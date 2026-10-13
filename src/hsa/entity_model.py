"""Entity Transformer with explicit card-instance binding and masked actions.

Independent format: never guesses compatibility with legacy flat checkpoints.
No dropout: collection and likelihood reevaluation must agree for later PPO.
"""
from __future__ import annotations

import hashlib
import math
import json

import torch
from torch import nn

from .encoding import ACTION_KINDS, CARD_SEMANTIC_FEATURE_SIZE
from .observer_view import SCHEMA, PLAYER_NUMERIC, CARD_NUMERIC, CARD_PRIVATE_NUMERIC

ARCHITECTURE = "hsa-entity-transformer-v1"
ZONES = ("padding", "global", "hero", "hero_power", "hand", "board", "secret",
         "location", "weapon", "graveyard", "quest", "known_starting_deck",
         "belief_expected_remaining", "choice", "history")
KINDS = ACTION_KINDS + ("RULE_CHOICE_PICK", "CATACLYSM_PICK", "EARTHEN_ROAR_PICK",
                        "DISCARD_PICK", "HAND_PICK")
NUMERIC = tuple(sorted(set(PLAYER_NUMERIC + CARD_NUMERIC + CARD_PRIVATE_NUMERIC + (
    "damaged_this_turn", "hand_count", "deck_count", "secret_count", "board_count",
    "damaged_character_count", "hero_damaged_this_turn", "used", "imbues", "cost_override",
    "durability", "cooldown", "next_refresh", "custom_tier", "ammunition", "count",
    "progress", "turns", "turn", "to_act", "candidate_count", "unresolved_hidden_slots",
    "has_candidate_support", "known_deck_provided", "selected",
))))
NUMERIC_INDEX = {name: index for index, name in enumerate(NUMERIC)}
ZONE_INDEX = {name: index for index, name in enumerate(ZONES)}
KIND_INDEX = {name: index for index, name in enumerate(KINDS)}
TAG_BUCKETS = 8192


def _tag_ids(tags):
    """Stable bounded vocabulary, preserving repeated gifts and field paths."""
    out = []

    def walk(value, path):
        if isinstance(value, dict):
            for key in sorted(value):
                walk(value[key], path + "/" + key)
        elif isinstance(value, (list, tuple)):
            for item in value:
                walk(item, path)
        elif value is not None:
            text = path + "=" + str(value)
            out.append(1 + int.from_bytes(hashlib.sha256(text.encode()).digest()[:4], "little") % (TAG_BUCKETS - 1))

    walk(tags, "")
    return out or [0]


def input_contract():
    return {"observation_schema": SCHEMA, "numeric_fields": list(NUMERIC),
            "zones": list(ZONES), "action_kinds": list(KINDS),
            "semantic_size": CARD_SEMANTIC_FEATURE_SIZE, "tag_buckets": TAG_BUCKETS}


def _nested_zeros(shape, value=0):
    if len(shape) == 1:
        return [value] * shape[0]
    return [_nested_zeros(shape[1:], value) for _ in range(shape[0])]


def collate_views(views, card_ids, device="cpu"):
    if not views:
        raise ValueError("empty batch")
    index = {card_id: i + 1 for i, card_id in enumerate(card_ids)}
    rows = []
    for view in views:
        if view["schema"] != SCHEMA:
            raise ValueError("observer schema mismatch")
        if not view["actions"]:
            raise ValueError("training/inference requires at least one legal action")
        global_numeric = {"turn": view["turn"], "to_act": view["to_act"],
                          "known_deck_provided": view["known_deck_provided"]}
        global_numeric.update(view.get("belief") or {})
        entities = [{"zone": "global", "owner": 0, "position": 0,
                     "numeric": global_numeric, "tags": {"choice_kind": (view.get("choice") or {}).get("kind")}}]
        entities += view["entities"]
        selected = set((view.get("choice") or {}).get("selected_entities", ()))
        if selected:
            entities = [dict(e, numeric=dict(e.get("numeric", {}), selected=i - 1 in selected))
                        for i, e in enumerate(entities)]
        for position, event in enumerate(view["history"]):
            entities.append({"zone": "history", "owner": event["owner"] or 0,
                             "position": position, "card_id": event["card_id"],
                             "numeric": {"turn": event["turn"]}, "tags": {"event": event["kind"]}})
        if len(entities) > 1024:
            raise ValueError("observation exceeds audited entity budget; no silent truncation")
        rows.append(entities)
    batch, length = len(rows), max(map(len, rows))
    action_count = max(len(v["actions"]) for v in views)
    tag_length = max(len(_tag_ids(e.get("tags", {}))) for row in rows for e in row)
    specs = {
        "cards": ((batch, length), torch.long),
        "zones": ((batch, length), torch.long),
        "owners": ((batch, length), torch.long),
        "positions": ((batch, length), torch.long),
        "numeric": ((batch, length, 2 * len(NUMERIC)), torch.float32),
        "semantic": ((batch, length, CARD_SEMANTIC_FEATURE_SIZE), torch.float32),
        "tags": ((batch, length, tag_length), torch.long),
        "entity_mask": ((batch, length), torch.bool),
        "kind": ((batch, action_count), torch.long),
        "source": ((batch, action_count), torch.long),
        "target": ((batch, action_count), torch.long),
        "literal": ((batch, action_count, 1), torch.float32),
        "action_mask": ((batch, action_count), torch.bool),
    }
    # Fill Python buffers and materialize each tensor once. Thousands of
    # individual torch scalar assignments were the dominant inference cost.
    result = {key: _nested_zeros(shape) for key, (shape, _) in specs.items()}
    for b, (view, row) in enumerate(zip(views, rows)):
        for n, entity in enumerate(row):
            result["entity_mask"][b][n] = True
            result["cards"][b][n] = index.get(entity.get("card_id"), 0)
            result["zones"][b][n] = ZONE_INDEX[entity["zone"]]
            result["owners"][b][n] = entity["owner"]
            result["positions"][b][n] = min(entity["position"], 127)
            # Entity numerics are sparse. Scanning every possible field for
            # every card used to dominate CPU collation during self-play.
            for name, value in entity.get("numeric", {}).items():
                j = NUMERIC_INDEX.get(name)
                if j is None or value is None:
                    continue
                if not isinstance(value, (int, float)) or not math.isfinite(value):
                    raise ValueError(f"non-finite/invalid numeric field {name}")
                result["numeric"][b][n][j] = math.copysign(math.log1p(abs(value)), value) / 5
                result["numeric"][b][n][len(NUMERIC) + j] = 1
            semantic = entity.get("semantic")
            if semantic is not None:
                if len(semantic) != CARD_SEMANTIC_FEATURE_SIZE:
                    raise ValueError("card semantic schema mismatch")
                result["semantic"][b][n] = semantic
            tags = _tag_ids(entity.get("tags", {}))
            result["tags"][b][n][:len(tags)] = tags
        for a, action in enumerate(view["actions"]):
            result["action_mask"][b][a] = True
            result["kind"][b][a] = KIND_INDEX[action["kind"]]
            for field in ("source", "target"):
                ref = action[field]
                if ref < -1 or ref >= len(view["entities"]):
                    raise ValueError("action entity reference outside observation")
                # Zero is global/no entity; observer entity indices start at one.
                result[field][b][a] = ref + 1
            result["literal"][b][a][0] = (action.get("literal") or 0) / 10
    return {key: torch.tensor(value, dtype=specs[key][1]).to(device)
            for key, value in result.items()}


class EntityAttentionBlock(nn.Module):
    """Explicit matmul attention: avoid NPU's unsupported fused CPU fallback."""

    def __init__(self, width, heads):
        super().__init__()
        self.heads = heads
        self.norm1 = nn.LayerNorm(width)
        self.qkv = nn.Linear(width, 3 * width)
        self.out = nn.Linear(width, width)
        self.norm2 = nn.LayerNorm(width)
        self.ff = nn.Sequential(nn.Linear(width, 4 * width), nn.GELU(), nn.Linear(4 * width, width))

    def forward(self, x, mask):
        batch, length, width = x.shape
        qkv = self.qkv(self.norm1(x)).reshape(batch, length, 3, self.heads, width // self.heads)
        q, k, v = qkv.permute(2, 0, 3, 1, 4).unbind(0)
        scores = (q @ k.transpose(-2, -1)) / math.sqrt(width // self.heads)
        scores = scores.masked_fill(~mask[:, None, None, :], -1e9)
        attention = (scores.softmax(-1) @ v).transpose(1, 2).reshape(batch, length, width)
        x = x + self.out(attention)
        return x + self.ff(self.norm2(x))


class EntityPolicyValueNet(nn.Module):
    def __init__(self, card_ids, d_model=256, layers=6, heads=8):
        super().__init__()
        if d_model % heads or layers < 1:
            raise ValueError("invalid Transformer width/depth")
        if len(card_ids) != len(set(card_ids)):
            raise ValueError("duplicate card vocabulary")
        self.card_ids = tuple(card_ids)
        self.config = {"d_model": d_model, "layers": layers, "heads": heads}
        self.card = nn.Embedding(len(card_ids) + 1, d_model, padding_idx=0)
        self.zone = nn.Embedding(len(ZONES), d_model, padding_idx=0)
        self.owner = nn.Embedding(2, d_model)
        self.position = nn.Embedding(128, d_model)
        self.tag = nn.Embedding(TAG_BUCKETS, d_model, padding_idx=0)
        self.numeric = nn.Linear(2 * len(NUMERIC), d_model)
        self.semantic = nn.Linear(CARD_SEMANTIC_FEATURE_SIZE, d_model)
        self.encoder = nn.ModuleList([EntityAttentionBlock(d_model, heads) for _ in range(layers)])
        self.norm = nn.LayerNorm(d_model)
        self.action = nn.Embedding(len(KINDS), d_model)
        self.policy = nn.Sequential(nn.Linear(4 * d_model + 1, d_model), nn.GELU(), nn.Linear(d_model, 1))
        self.value = nn.Sequential(nn.Linear(d_model, d_model), nn.GELU(), nn.Linear(d_model, 1), nn.Tanh())

    def forward(self, batch):
        x = (self.card(batch["cards"]) + self.zone(batch["zones"]) + self.owner(batch["owners"])
             + self.position(batch["positions"]) + self.numeric(batch["numeric"])
             + self.semantic(batch["semantic"]) + self.tag(batch["tags"]).sum(dim=2))
        for block in self.encoder:
            x = block(x, batch["entity_mask"])
        h = self.norm(x)
        global_h = h[:, 0]
        width = h.shape[-1]
        source = h.gather(1, batch["source"].unsqueeze(-1).expand(-1, -1, width))
        target = h.gather(1, batch["target"].unsqueeze(-1).expand(-1, -1, width))
        actor = global_h.unsqueeze(1).expand_as(source)
        joint = torch.cat((actor, source, target, self.action(batch["kind"]), batch["literal"]), dim=-1)
        logits = self.policy(joint).squeeze(-1).masked_fill(~batch["action_mask"], -1e9)
        return logits, self.value(global_h).squeeze(-1)

    def metadata(self):
        return {"architecture": ARCHITECTURE, "config": self.config,
                "card_ids": list(self.card_ids), "input_contract": input_contract(),
                "parameters": sum(p.numel() for p in self.parameters())}

    @classmethod
    def from_payload(cls, payload):
        meta = payload["entity_model"]
        if meta["architecture"] != ARCHITECTURE or meta["input_contract"] != input_contract():
            raise ValueError("entity checkpoint input contract mismatch")
        model = cls(meta["card_ids"], **meta["config"])
        model.load_state_dict(payload["model_state_dict"], strict=True)
        return model

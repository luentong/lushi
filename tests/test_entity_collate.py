from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

try:
    import torch
    from hsa import DragonMirrorGame
    from hsa.entity_model import (
        CARD_SEMANTIC_FEATURE_SIZE, KINDS, NUMERIC, ZONES,
        _tag_ids, collate_views,
    )
    from hsa.observer_view import observer_view, SCHEMA
    from hsa.policy import HeuristicPolicy
except ImportError:
    torch = None


def reference_collate(views, card_ids):
    """Independent scalar-assignment reference for the input tensor contract."""
    index = {card_id: i + 1 for i, card_id in enumerate(card_ids)}
    rows = []
    for view in views:
        if view["schema"] != SCHEMA or not view["actions"]:
            raise ValueError("invalid view")
        global_numeric = {"turn": view["turn"], "to_act": view["to_act"],
                          "known_deck_provided": view["known_deck_provided"]}
        global_numeric.update(view.get("belief") or {})
        entities = [{"zone": "global", "owner": 0, "position": 0,
                     "numeric": global_numeric,
                     "tags": {"choice_kind": (view.get("choice") or {}).get("kind")}}]
        entities += view["entities"]
        selected = set((view.get("choice") or {}).get("selected_entities", ()))
        if selected:
            entities = [dict(e, numeric=dict(e.get("numeric", {}),
                                             selected=i - 1 in selected))
                        for i, e in enumerate(entities)]
        for position, event in enumerate(view["history"]):
            entities.append({"zone": "history", "owner": event["owner"] or 0,
                             "position": position, "card_id": event["card_id"],
                             "numeric": {"turn": event["turn"]},
                             "tags": {"event": event["kind"]}})
        rows.append(entities)
    batch, length = len(rows), max(map(len, rows))
    action_count = max(len(view["actions"]) for view in views)
    tag_length = max(len(_tag_ids(entity.get("tags", {})))
                     for row in rows for entity in row)
    result = {
        "cards": torch.zeros(batch, length, dtype=torch.long),
        "zones": torch.zeros(batch, length, dtype=torch.long),
        "owners": torch.zeros(batch, length, dtype=torch.long),
        "positions": torch.zeros(batch, length, dtype=torch.long),
        "numeric": torch.zeros(batch, length, 2 * len(NUMERIC)),
        "semantic": torch.zeros(batch, length, CARD_SEMANTIC_FEATURE_SIZE),
        "tags": torch.zeros(batch, length, tag_length, dtype=torch.long),
        "entity_mask": torch.zeros(batch, length, dtype=torch.bool),
        "kind": torch.zeros(batch, action_count, dtype=torch.long),
        "source": torch.zeros(batch, action_count, dtype=torch.long),
        "target": torch.zeros(batch, action_count, dtype=torch.long),
        "literal": torch.zeros(batch, action_count, 1),
        "action_mask": torch.zeros(batch, action_count, dtype=torch.bool),
    }
    for b, (view, row) in enumerate(zip(views, rows)):
        for n, entity in enumerate(row):
            result["entity_mask"][b, n] = True
            result["cards"][b, n] = index.get(entity.get("card_id"), 0)
            result["zones"][b, n] = ZONES.index(entity["zone"])
            result["owners"][b, n] = entity["owner"]
            result["positions"][b, n] = min(entity["position"], 127)
            for j, name in enumerate(NUMERIC):
                value = entity.get("numeric", {}).get(name)
                if value is None:
                    continue
                if not isinstance(value, (int, float)) or not math.isfinite(value):
                    raise ValueError("invalid numeric")
                result["numeric"][b, n, j] = math.copysign(
                    math.log1p(abs(value)), value) / 5
                result["numeric"][b, n, len(NUMERIC) + j] = 1
            semantic = entity.get("semantic")
            if semantic is not None:
                result["semantic"][b, n] = torch.tensor(semantic)
            tags = _tag_ids(entity.get("tags", {}))
            result["tags"][b, n, :len(tags)] = torch.tensor(tags)
        for a, action in enumerate(view["actions"]):
            result["action_mask"][b, a] = True
            result["kind"][b, a] = KINDS.index(action["kind"])
            for field in ("source", "target"):
                ref = action[field]
                if ref < -1 or ref >= len(view["entities"]):
                    raise ValueError("invalid entity reference")
                result[field][b, a] = ref + 1
            result["literal"][b, a, 0] = (action.get("literal") or 0) / 10
    return result


@unittest.skipIf(torch is None, "torch not installed")
class EntityCollateParityTests(unittest.TestCase):
    def test_multiple_real_observations_match_reference_exactly(self):
        game = DragonMirrorGame(ROOT / "cards.251332.enUS.json", 42)
        policy = HeuristicPolicy()
        views = []
        for step in range(35):
            actions = game.legal_actions()
            if step in {0, 1, 4, 8, 16, 24, 32}:
                views.append(observer_view(
                    game, actions=actions,
                    known_deck=game.deck_counts[game.current]))
            game.step(policy.choose(game))
        card_ids = tuple(sorted(game.card_defs))
        expected = reference_collate(views, card_ids)
        actual = collate_views(views, card_ids, "cpu")
        self.assertEqual(expected.keys(), actual.keys())
        for key in expected:
            with self.subTest(tensor=key):
                self.assertTrue(torch.equal(expected[key], actual[key]))


if __name__ == "__main__":
    unittest.main()

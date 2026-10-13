#!/usr/bin/env python3
"""Direct policy/value training from columnar tensor shards."""
from __future__ import annotations

import argparse
import copy
import json
import random
import time
from pathlib import Path

import torch
import torch.nn.functional as F

from train_policy_value import choose_device
from hsa.encoding import compatible_feature_schema
from hsa.torch_model import StructuredResidualPolicyValueNet


def _is_held_out_deck_shard(path: Path, deck_ids: set[str]) -> bool:
    if not deck_ids:
        return False
    matchup = path.name.split(".jsonl", 1)[0]
    return any(deck_id in matchup.split("__") for deck_id in deck_ids)


def turn_band_sample_weights(states: torch.Tensor, weights: tuple[float, float, float]) -> torch.Tensor:
    """Return per-row weights for turns 1-3, 4-6, and 7+.

    The first encoded state feature is the normalized turn (turn / 100). Keep
    the default weights at 1 so existing training remains byte-for-byte
    equivalent in objective unless the experiment is explicitly enabled.
    """
    turns = (states[:, 0].clamp(0, 1) * 100).round()
    result = torch.full_like(turns, float(weights[2]))
    result = torch.where(turns <= 6, torch.full_like(result, float(weights[1])), result)
    result = torch.where(turns <= 3, torch.full_like(result, float(weights[0])), result)
    return result


def _load_checkpoint_weights(model, checkpoint, target_schema):
    """Load an exact checkpoint, or widen a structured schema-v4 state stem to v5.

    Schema v5 inserts one actor-deck histogram embedding before the dynamic
    features and appends two turn-damage counters.  All shared card embeddings,
    action layers and residual/value/policy layers remain shape-compatible.
    The new stem columns start at zero so the migrated model initially behaves
    exactly like the v4 checkpoint until the new features are learned.
    """
    previous = checkpoint.get("report", {}).get("feature_schema")
    state = checkpoint["model_state_dict"]
    def load_allowing_new_action_value_head(weights):
        result = model.load_state_dict(weights, strict=False)
        allowed = {
            key for key in result.missing_keys
            if key.startswith("action_value_head.")
        }
        if (set(result.missing_keys) != allowed or result.unexpected_keys):
            raise ValueError(
                "checkpoint tensor mismatch beyond the newly added action-value head: "
                f"missing={result.missing_keys}, unexpected={result.unexpected_keys}"
            )
        return bool(allowed)

    if previous is None or compatible_feature_schema(previous, target_schema):
        added_head = load_allowing_new_action_value_head(state)
        return "exact+new-action-value-head" if added_head else "exact"

    if (previous.get("schema_version") == 6
            and target_schema.get("schema_version") == 6
            and previous.get("card_vocab_sha256") == target_schema.get("card_vocab_sha256")
            and previous.get("card_vocab_size") == target_schema.get("card_vocab_size")
            and previous.get("action_kinds") == target_schema.get("action_kinds")):
        # Schema v6 is append-only for ID-independent semantic features. Keep
        # existing metadata projections and action weights intact, and zero
        # initialize only the appended text/effect dimensions.
        old_sem = int(previous.get("card_semantic_feature_size", 0))
        new_sem = int(target_schema.get("card_semantic_feature_size", 0))
        if not (0 < old_sem < new_sem):
            raise ValueError("v6 semantic widening requires a larger target feature vector")
        migrated = copy.deepcopy(state)
        semantic_key = "semantic_state_projection.0.weight"
        old_semantic = state.get(semantic_key)
        semantic_widths = (4 * old_sem, 4 * new_sem)
        if old_semantic is None or tuple(old_semantic.shape) != (
            int(model.card_embedding_size), semantic_widths[0]
        ):
            raise ValueError("v6 checkpoint semantic projection has an unexpected shape")
        new_semantic = model.semantic_state_projection[0].weight.detach().cpu().new_zeros(
            (int(model.card_embedding_size), semantic_widths[1])
        )
        new_semantic[:, :semantic_widths[0]] = old_semantic
        migrated[semantic_key] = new_semantic

        action_key = "action_tower.0.weight"
        old_action = state.get(action_key)
        old_action_width = 56 + 2 * int(model.card_embedding_size) + 2 * old_sem
        new_action_width = 56 + 2 * int(model.card_embedding_size) + 2 * new_sem
        if old_action is None or tuple(old_action.shape) != (
            int(model.action_hidden_size), old_action_width
        ):
            raise ValueError("v6 checkpoint action tower has an unexpected shape")
        new_action = model.action_tower[0].weight.detach().cpu().new_zeros(
            (int(model.action_hidden_size), new_action_width)
        )
        new_action[:, :old_action_width] = old_action
        migrated[action_key] = new_action
        added_head = load_allowing_new_action_value_head(migrated)
        return "v6-semantic-widening-zero-init-appended-text-effects" + (
            "+new-action-value-head" if added_head else ""
        )

    if (previous.get("schema_version") in (4, 5)
            and target_schema.get("schema_version") == 6):
        # Schema v6 adds ID-independent card metadata summaries to state and
        # action features. A v4 source also lacks the actor-deck histogram and
        # turn-damage progress added in v5; insert zero weights for those
        # columns while preserving the remaining feature-to-weight mapping.
        shared_fields = (
            "card_vocab_size", "card_vocab_mode", "card_vocab_sha256",
            "action_kinds", "action_player_encoding", "action_target_zone",
        )
        if any(previous.get(key) != target_schema.get(key) for key in shared_fields):
            raise ValueError("v5-to-v6 migration requires the same frozen card vocabulary")
        migrated = copy.deepcopy(state)
        source_version = int(previous["schema_version"])
        embed = int(model.card_embedding_size)
        hidden = int(model.hidden_size)
        old_histograms = 3 if source_version == 4 else 4
        old_dynamic = 350 if source_version == 4 else 352
        old_state_width = 24 + old_histograms * embed + old_dynamic
        new_state_width = old_state_width + embed
        if source_version == 4:
            new_state_width += embed + 2
        stem_key = "state_stem.0.weight"
        old_stem = state.get(stem_key)
        if old_stem is None or tuple(old_stem.shape) != (hidden, old_state_width):
            raise ValueError("v5 checkpoint state stem has an unexpected shape")
        new_stem = model.state_stem[0].weight.detach().cpu().new_zeros(
            (hidden, new_state_width)
        )
        old_hist_end = 24 + old_histograms * embed
        new_hist_end = 24 + 4 * embed
        new_stem[:, :24] = old_stem[:, :24]
        new_stem[:, 24:old_hist_end] = old_stem[:, 24:old_hist_end]
        new_dynamic_start = new_hist_end
        old_dynamic_start = old_hist_end
        if source_version == 5:
            new_stem[:, new_dynamic_start:new_dynamic_start + 352] = (
                old_stem[:, old_dynamic_start:old_dynamic_start + 352]
            )
        else:
            # The first 322 v4 dynamic columns are player/hand/board data;
            # two newly inserted damage-progress values precede 28 location
            # values at the end of that vector.
            new_stem[:, new_dynamic_start:new_dynamic_start + 322] = (
                old_stem[:, old_dynamic_start:old_dynamic_start + 322]
            )
            new_stem[:, new_dynamic_start + 324:new_dynamic_start + 352] = (
                old_stem[:, old_dynamic_start + 322:old_dynamic_start + 350]
            )
        migrated[stem_key] = new_stem

        action_key = "action_tower.0.weight"
        old_action = state.get(action_key)
        old_action_width = 56 + 2 * embed
        new_action_width = old_action_width + 2 * int(target_schema["card_semantic_feature_size"])
        if old_action is None or tuple(old_action.shape) != (
            int(model.action_hidden_size), old_action_width
        ):
            raise ValueError("v5 checkpoint action tower has an unexpected shape")
        new_action = model.action_tower[0].weight.detach().cpu().new_zeros(
            (int(model.action_hidden_size), new_action_width)
        )
        new_action[:, :old_action_width] = old_action
        migrated[action_key] = new_action
        result = model.load_state_dict(migrated, strict=False)
        allowed_missing = {
            key for key in result.missing_keys
            if key.startswith("semantic_state_projection.")
            or key.startswith("action_value_head.")
        }
        if set(result.missing_keys) != allowed_missing or result.unexpected_keys:
            raise ValueError(
                "v5-to-v6 checkpoint migration found unexpected tensor mismatch: "
                f"missing={result.missing_keys}, unexpected={result.unexpected_keys}"
            )
        added_q = any(key.startswith("action_value_head.") for key in allowed_missing)
        return f"v{source_version}-to-v6-zero-init-missing-semantic-and-runtime-columns" + (
            "+new-action-value-head" if added_q else ""
        )

    shared_fields = (
        "card_vocab_size", "card_vocab_mode", "card_vocab_sha256",
        "action_size", "action_kinds", "action_player_encoding",
        "action_target_zone",
    )
    if (previous.get("schema_version") != 4
            or target_schema.get("schema_version") != 5
            or any(previous.get(key) != target_schema.get(key) for key in shared_fields)):
        raise ValueError(
            "checkpoint feature schema differs from the input shards; "
            "only an exact match or compatible state-schema v4-to-v5 widening is supported"
        )

    vocab = int(target_schema["card_vocab_size"])
    embed = int(model.card_embedding_size)
    hidden = int(model.hidden_size)
    old_width = 24 + 3 * embed + 350
    new_width = 24 + 4 * embed + 352
    key = "state_stem.0.weight"
    old_weight = state.get(key)
    if old_weight is None or tuple(old_weight.shape) != (hidden, old_width):
        raise ValueError("v4 checkpoint state stem has an unexpected shape")
    migrated = copy.deepcopy(state)
    new_weight = model.state_stem[0].weight.detach().cpu().new_zeros((hidden, new_width))
    new_weight[:, :24] = old_weight[:, :24]
    old_hist_start = 24
    new_hist_start = 24
    new_dynamic_start = 24 + 4 * embed
    old_dynamic_start = 24 + 3 * embed
    new_weight[:, new_hist_start:new_hist_start + 3 * embed] = (
        old_weight[:, old_hist_start:old_hist_start + 3 * embed]
    )
    new_weight[:, new_dynamic_start:new_dynamic_start + 350] = (
        old_weight[:, old_dynamic_start:old_dynamic_start + 350]
    )
    migrated[key] = new_weight
    added_head = load_allowing_new_action_value_head(migrated)
    return (
        "v4-to-v5-zero-init-new-features+new-action-value-head"
        if added_head else "v4-to-v5-zero-init-new-features"
    )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data", nargs="+", type=Path, required=True)
    p.add_argument(
        "--priority-data", nargs="*", type=Path, default=(),
        help=("Optional higher-quality shards to mix into every epoch. "
              "They are repeated according to --priority-repeat rather than "
              "used as a post-hoc fine-tuning-only dataset."),
    )
    p.add_argument(
        "--priority-repeat", type=int, default=1,
        help="How many times each --priority-data shard appears per epoch (>= 1).",
    )
    p.add_argument("--tactical-data", nargs="*", type=Path, default=(),
                   help="Small covered multi-seed tactical correction shards.")
    p.add_argument("--tactical-repeat", type=int, default=1,
                   help="Repeat tactical correction shards per epoch independently of priority data.")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--init-checkpoint", type=Path,
                   help="Resume model weights from a compatible columnar checkpoint.")
    p.add_argument("--device", choices=("cpu", "npu"), default="npu")
    p.add_argument("--epochs", type=int, default=8)
    p.add_argument("--batch-size", type=int, default=256)
    p.add_argument("--hidden-size", type=int, default=1024)
    p.add_argument("--action-hidden-size", type=int, default=512)
    p.add_argument("--residual-blocks", type=int, default=8)
    p.add_argument("--card-embedding-size", type=int, default=256)
    p.add_argument("--learning-rate", type=float, default=2e-4)
    p.add_argument("--value-weight", type=float, default=.15)
    p.add_argument(
        "--opponent-value-weight", type=float, default=1.0,
        help="Relative value loss weight for the same position encoded from the other player's information view (0 disables it).",
    )
    p.add_argument("--action-value-weight", type=float, default=.10,
                   help="Auxiliary Huber loss against visited root action-Q estimates from the search teacher.")
    p.add_argument("--action-value-only", action="store_true",
                   help="Freeze policy/value/shared encoders and train only the action-Q head; requires visited Q targets.")
    p.add_argument("--conditional-policy-weight", type=float, default=2.0)
    p.add_argument(
        "--turn-band-weights", type=float, nargs=3, default=(1.0, 1.0, 1.0),
        metavar=("T1_3", "T4_6", "T7_PLUS"),
        help="Optional loss multipliers for turn bands 1-3, 4-6, and 7+.",
    )
    p.add_argument("--checkpoint-every", type=int, default=0,
                   help="Write an epoch checkpoint every N epochs (0 disables).")
    p.add_argument("--max-shards", type=int)
    p.add_argument("--exclude-deck-id", action="append", default=[],
                   help="Hold out every matchup shard containing this exact deck ID.")
    p.add_argument("--exclude-mod", type=int)
    p.add_argument("--exclude-rem", type=int, default=0)
    p.add_argument("--seed", type=int, default=1)
    args = p.parse_args()

    if args.priority_repeat < 1 or args.tactical_repeat < 1:
        p.error("priority and tactical repeat values must be at least 1")
    if args.conditional_policy_weight <= 0:
        p.error("--conditional-policy-weight must be positive")
    base_files = sorted(args.data)
    if args.max_shards is not None:
        base_files = base_files[:args.max_shards]
    priority_files = sorted(args.priority_data)
    tactical_files = sorted(args.tactical_data)
    held_out_deck_ids = set(args.exclude_deck_id)
    held_out_shards = [path for path in base_files + priority_files
                       if _is_held_out_deck_shard(path, held_out_deck_ids)]
    if held_out_deck_ids:
        base_files = [path for path in base_files
                      if not _is_held_out_deck_shard(path, held_out_deck_ids)]
        priority_files = [path for path in priority_files
                          if not _is_held_out_deck_shard(path, held_out_deck_ids)]
        if not base_files:
            p.error("deck holdout removed every base training shard")
    files = (base_files + priority_files * args.priority_repeat
             + tactical_files * args.tactical_repeat)
    if not files:
        p.error("at least one training shard is required")
    random.Random(args.seed).shuffle(files)
    # The base corpus owns the frozen vocabulary/schema. Never let a shuffled
    # correction shard silently define the network dimensions.
    first = torch.load(base_files[0], map_location="cpu", weights_only=False)
    schema = first["header"]["feature_schema"]
    model = StructuredResidualPolicyValueNet(
        int(schema["state_size"]), int(schema["action_size"]), args.hidden_size,
        args.action_hidden_size, args.residual_blocks,
        int(schema["card_vocab_size"]), args.card_embedding_size,
    )
    resumed_from = None
    checkpoint_migration = None
    if args.init_checkpoint is not None:
        checkpoint = torch.load(args.init_checkpoint, map_location="cpu", weights_only=False)
        checkpoint_migration = _load_checkpoint_weights(model, checkpoint, schema)
        resumed_from = str(args.init_checkpoint)
    if args.action_value_only:
        for name, parameter in model.named_parameters():
            parameter.requires_grad_(name.startswith("action_value_head."))
        if not any(parameter.requires_grad for parameter in model.parameters()):
            p.error("action-value head has no trainable parameters")
    device = choose_device(args.device)
    model.to(device)
    trainable_parameters = [parameter for parameter in model.parameters()
                            if parameter.requires_grad]
    opt = torch.optim.AdamW(trainable_parameters, lr=args.learning_rate, weight_decay=1e-2)
    started = time.perf_counter(); history = []; total_rows = 0
    action_q_supervision_seen = False
    opponent_value_supervision_seen = False
    opponent_value_rows = 0
    value_rows_seen = 0

    def checkpoint(path: Path, *, final: bool) -> None:
        report = {"records": total_rows, "epochs": len(history), "history": history,
                  "elapsed_seconds": time.perf_counter() - started, "device": str(device),
                  "feature_schema": schema, "model": model.metadata(),
                  "resumed_from": resumed_from, "final": final,
                  "checkpoint_migration": checkpoint_migration,
                  "base_shards": len(base_files), "priority_shards": len(priority_files),
                  "priority_repeat": args.priority_repeat,
                  "tactical_shards": len(tactical_files),
                  "tactical_repeat": args.tactical_repeat,
                  "excluded_deck_ids": sorted(held_out_deck_ids),
                  "excluded_deck_shards": [str(path) for path in held_out_shards],
                  "conditional_policy_weight": args.conditional_policy_weight,
                  "turn_band_weights": list(args.turn_band_weights),
                  "opponent_value_weight": args.opponent_value_weight,
                  "root_perspective_value_trained": (
                      not args.action_value_only
                      and opponent_value_supervision_seen
                      and args.opponent_value_weight > 0
                      and opponent_value_rows / max(1, value_rows_seen) >= 0.99
                  ),
                  "opponent_value_coverage": (
                      opponent_value_rows / max(1, value_rows_seen)
                  ),
                  "action_value_weight": args.action_value_weight,
                  "action_value_only": args.action_value_only,
                  "action_value_trained": action_q_supervision_seen}
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save({"model_state_dict": model.state_dict(), "report": report}, path)
        path.with_suffix(".json").write_text(json.dumps(report, indent=2) + "\n")

    for epoch in range(1, args.epochs + 1):
        model.train(); loss_sum = 0.; policy_sum = 0.; value_sum = 0.; opponent_value_sum = 0.; q_sum = 0.; batches = 0
        random.Random(args.seed + epoch).shuffle(files)
        for path in files:
            shard = torch.load(path, map_location="cpu", weights_only=False)
            shard_schema = shard.get("header", {}).get("feature_schema")
            if shard_schema is None or not compatible_feature_schema(shard_schema, schema):
                raise ValueError(
                    f"training shard schema/vocabulary mismatch: {path}; "
                    "reindex correction data to the base corpus vocabulary first"
                )
            n = int(shard["count"])
            eligible = torch.arange(n)
            if args.exclude_mod is not None:
                eligible = eligible[(shard["game_seed"].abs() % args.exclude_mod) != args.exclude_rem]
            if not len(eligible):
                continue
            total_rows += len(eligible) if epoch == 1 else 0
            order = eligible[torch.randperm(len(eligible))]
            for start in range(0, n, args.batch_size):
                ix = order[start:start + args.batch_size]
                states = shard["states"][ix].to(device)
                opponent_states = shard.get("opponent_value_states")
                if opponent_states is not None:
                    opponent_states = opponent_states[ix].to(device)
                    opponent_value_valid = shard.get(
                        "opponent_value_valid", torch.zeros(n, dtype=torch.bool)
                    )[ix].to(device)
                else:
                    opponent_value_valid = torch.zeros(len(ix), dtype=torch.bool, device=device)
                actions = shard["actions"][ix].to(device)
                mask = shard["mask"][ix].to(device)
                targets = shard["values"][ix].to(device)
                teacher_q = shard.get(
                    "action_values", torch.zeros_like(shard["policy_targets"])
                )[ix].to(device)
                teacher_q_visits = shard.get(
                    "action_value_visits",
                    torch.zeros_like(shard["policy_targets"], dtype=torch.int32),
                )[ix].to(device)
                teacher_q_mask = shard.get(
                    "action_value_mask", torch.zeros_like(shard["mask"])
                )[ix].to(device)
                policy_targets = shard["policy_targets"][ix].to(device)
                chosen = shard["chosen"][ix].to(device)
                value_valid = shard.get(
                    "value_valid", torch.ones(n, dtype=torch.bool)
                )[ix].to(device)
                conditional = shard.get(
                    "conditional", torch.zeros(n, dtype=torch.bool)
                )[ix].to(device)
                # Older decisions can contain shortened/zero policy targets.
                # Restore a one-hot teacher target and skip malformed empty
                # action rows so one record cannot poison the full run.
                valid = mask.any(dim=1)
                if not bool(valid.any().item()):
                    continue
                states, actions, mask = states[valid], actions[valid], mask[valid]
                targets, policy_targets, chosen = (
                    targets[valid], policy_targets[valid], chosen[valid]
                )
                teacher_q = teacher_q[valid]
                teacher_q_visits = teacher_q_visits[valid]
                teacher_q_mask = teacher_q_mask[valid] & mask
                value_valid = value_valid[valid]
                value_rows_seen += int(value_valid.sum().item())
                opponent_states = (
                    opponent_states[valid] if opponent_states is not None else None
                )
                opponent_value_valid = opponent_value_valid[valid] & value_valid
                conditional = conditional[valid]
                turn_weights = turn_band_sample_weights(
                    states, tuple(args.turn_band_weights)
                )
                policy_targets = torch.nan_to_num(policy_targets)
                sums = policy_targets.sum(dim=1, keepdim=True)
                missing = sums.squeeze(1) <= 0
                if bool(missing.any().item()):
                    policy_targets[missing] = 0
                    policy_targets[missing, chosen[missing]] = 1
                    sums = policy_targets.sum(dim=1, keepdim=True)
                policy_targets = policy_targets / sums.clamp_min(1e-12)
                logits, values, predicted_q = model.forward_with_action_values(
                    states, actions, mask
                )
                rows = -(policy_targets * F.log_softmax(logits, dim=1)).sum(dim=1)
                nontrivial = mask.sum(dim=1) > 1
                policy_weights = torch.where(
                    conditional,
                    torch.full_like(rows, args.conditional_policy_weight),
                    torch.ones_like(rows),
                ) * turn_weights
                policy = (
                    (rows[nontrivial] * policy_weights[nontrivial]).sum()
                    / policy_weights[nontrivial].sum().clamp_min(1e-12)
                    if bool(nontrivial.any()) else rows.sum() * 0
                )
                value_error = (values - targets).square()
                value = (
                    (value_error[value_valid] * turn_weights[value_valid]).sum()
                    / turn_weights[value_valid].sum().clamp_min(1e-12)
                    if bool(value_valid.any()) else values.sum() * 0
                )
                if (opponent_states is not None and args.opponent_value_weight > 0
                        and bool(opponent_value_valid.any())):
                    opponent_value_supervision_seen = True
                    opponent_value_rows += int(opponent_value_valid.sum().item())
                    opponent_encoded = model._encode_state(opponent_states)
                    opponent_values = model.value_head(opponent_encoded).squeeze(-1)
                    opponent_error = (
                        opponent_values + targets
                    ).square()
                    opponent_value = (
                        (opponent_error[opponent_value_valid]
                         * turn_weights[opponent_value_valid]).sum()
                        / turn_weights[opponent_value_valid].sum().clamp_min(1e-12)
                    )
                else:
                    opponent_value = values.sum() * 0
                q_mask = teacher_q_mask & (teacher_q_visits > 0)
                if bool(q_mask.any()):
                    action_q_supervision_seen = True
                    q_weights = teacher_q_visits.to(torch.float32).clamp_min(0).sqrt()
                    q_weights = q_weights * turn_weights.unsqueeze(1)
                    q_weights = q_weights * q_mask.to(torch.float32)
                    q_error = F.smooth_l1_loss(
                        predicted_q, teacher_q, reduction="none"
                    )
                    action_value = (
                        (q_error * q_weights).sum()
                        / q_weights.sum().clamp_min(1e-12)
                    )
                else:
                    action_value = predicted_q.sum() * 0
                loss = (
                    policy + args.value_weight * (
                        value + args.opponent_value_weight * opponent_value
                    )
                    + args.action_value_weight * action_value
                )
                if args.action_value_only:
                    if not bool(q_mask.any()):
                        continue
                    loss = action_value
                opt.zero_grad(set_to_none=True); loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                opt.step()
                loss_sum += float(loss.detach())
                policy_sum += float(policy.detach())
                value_sum += float(value.detach())
                opponent_value_sum += float(opponent_value.detach())
                q_sum += float(action_value.detach())
                batches += 1
        history.append({
            "epoch": epoch, "loss": loss_sum / max(1, batches),
            "policy_loss": policy_sum / max(1, batches),
            "value_loss": value_sum / max(1, batches),
            "opponent_value_loss": opponent_value_sum / max(1, batches),
            "action_value_loss": q_sum / max(1, batches),
        })
        print(json.dumps(history[-1]), flush=True)
        if args.action_value_only and not action_q_supervision_seen:
            raise RuntimeError("action-value-only training found no visited teacher Q targets")
        if args.checkpoint_every and epoch % args.checkpoint_every == 0:
            suffix = args.output.suffix
            checkpoint(args.output.with_name(f"{args.output.stem}.epoch{epoch}{suffix}"), final=False)
    if device.type == "npu": torch.npu.synchronize()
    checkpoint(args.output, final=True)

if __name__ == "__main__": main()

#!/usr/bin/env python3
"""Convert multi-seed neutral root audits into soft teacher shards.

Unlike a hard-negative shard, this keeps every action covered by multiple
seeds and uses the cross-seed visit-weighted Q means as a soft policy target.
It is intentionally compatible with the checkpoint feature schema.
"""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from hsa.encoding import configure_card_vocab, encode_action, encode_state
from replay_trace_state import replay_trace_state

def softmax(xs, temperature):
    m = max(xs)
    ws = [math.exp(max(-80.0, (x - m) / temperature)) for x in xs]
    z = sum(ws) or 1.0
    return [w / z for w in ws]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--audit", type=Path, required=True)
    p.add_argument("--deck-config", type=Path, required=True)
    p.add_argument("--checkpoint", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--temperature", type=float, default=.20)
    p.add_argument("--min-seeds", type=int, default=2)
    args = p.parse_args()
    ck = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    fs = ck["report"]["feature_schema"]
    configure_card_vocab(fs.get("card_vocab_mode", "legacy"), vocabulary=fs.get("card_vocab_ids"))
    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    trace = Path(audit["trace"])
    game = replay_trace_state(trace, int(audit["step"]), args.deck_config)
    legal = game.legal_actions()
    desc = [game.describe_action(a) for a in legal]
    rows = audit.get("rows", [])
    qsum = [0.0] * len(legal); visits = [0] * len(legal); seen = [set() for _ in legal]
    for row in rows:
        seed = int(row["seed"])
        for i, stat in enumerate(row.get("stats", [])):
            if i >= len(legal): break
            v = int(stat.get("visits", 0))
            if v > 0:
                qsum[i] += float(stat.get("mean_value", 0.0)) * v
                visits[i] += v
                seen[i].add(seed)
    valid = [visits[i] > 0 and len(seen[i]) >= args.min_seeds for i in range(len(legal))]
    if not any(valid):
        raise SystemExit("no actions covered by enough seeds")
    q = [qsum[i] / max(1, visits[i]) for i in range(len(legal))]
    probs0 = softmax([q[i] for i in range(len(legal)) if valid[i]], args.temperature)
    policy = [0.0] * len(legal); j = 0
    for i, ok in enumerate(valid):
        if ok:
            policy[i] = probs0[j]; j += 1
    chosen = max((i for i, ok in enumerate(valid) if ok), key=lambda i: q[i])
    state = list(encode_state(game, game.current, schema_version=int(fs["schema_version"])))
    actions = [list(encode_action(game, a, schema_version=int(fs["schema_version"]))) for a in legal]
    n, maxa, size = 1, len(actions), int(fs["action_size"])
    out = {"header": {"feature_schema": fs, "teacher": "neutral-cross-seed-soft-v1",
                       "source_audit": str(args.audit), "temperature": args.temperature,
                       "min_seeds": args.min_seeds},
           "states": torch.tensor([state], dtype=torch.float32),
           "actions": torch.tensor([actions], dtype=torch.float32),
           "mask": torch.ones((n, maxa), dtype=torch.bool),
           "chosen": torch.tensor([chosen]), "values": torch.tensor([sum(q[i] for i in range(len(q)) if valid[i]) / sum(valid)]),
           "actor": torch.tensor([game.current], dtype=torch.int8), "value_valid": torch.ones(n, dtype=torch.bool),
           "conditional": torch.ones(n, dtype=torch.bool), "game_seed": torch.tensor([int(audit["step"])]),
           "winner": torch.full((n,), -1, dtype=torch.int8),
           "action_values": torch.tensor([q], dtype=torch.float32),
           "action_value_visits": torch.tensor([visits], dtype=torch.int32),
           "action_value_mask": torch.tensor([valid], dtype=torch.bool),
           "policy_targets": torch.tensor([policy], dtype=torch.float32), "count": n}
    args.output.parent.mkdir(parents=True, exist_ok=True); torch.save(out, args.output)
    report = {"records": 1, "actions": len(actions), "covered_actions": sum(valid),
              "seeds": sorted({int(r["seed"]) for r in rows}), "selected_by_q": desc[chosen],
              "policy": {desc[i]: policy[i] for i in range(len(desc)) if valid[i]}}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))

if __name__ == "__main__":
    main()

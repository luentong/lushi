import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from replay_trace_state import replay_trace_state
from hsa.mcts import InformationSetMCTSPolicy


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", required=True)
    ap.add_argument("--deck", default="config/decks_20260924_flat.json")
    ap.add_argument("--step", type=int, required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--iterations", type=int, default=512)
    ap.add_argument("--seeds", type=int, nargs="+", default=[17, 41, 73, 113, 197, 271, 331, 401])
    args = ap.parse_args()
    trace = Path(args.trace)
    deck = Path(args.deck)
    if not trace.is_absolute():
        trace = ROOT / trace
    if not deck.is_absolute():
        deck = ROOT / deck
    game = replay_trace_state(trace, args.step, deck)
    rows = []
    for seed in args.seeds:
        p = InformationSetMCTSPolicy(
            samples=1,
            iterations_per_sample=args.iterations,
            tree_depth=8,
            rollout_depth=6,
            seed=seed,
            policy_value_model=None,
            use_model_value=False,
            force_uniform_expansion=True,
            min_simulations_per_root_action=2,
            max_total_iterations=args.iterations,
            tactical_precheck=True,
        )
        action = p.choose(game.clone())
        row = {
            "seed": seed,
            "selected": game.describe_action(action),
            "stats": p.last_search.get("root_action_stats", []),
        }
        rows.append(row)
        print(seed, row["selected"], flush=True)
    Path(args.output).write_text(
        json.dumps(
            {
                "trace": str(trace),
                "step": args.step,
                "iterations": args.iterations,
                "seeds": args.seeds,
                "rows": rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

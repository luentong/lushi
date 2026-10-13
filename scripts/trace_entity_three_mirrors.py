"""Generate three unfiltered mirror traces using the evaluated pure policy."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'scripts')]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--checkpoint', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--device', default='npu:3')
    p.add_argument('--seed', type=int, default=203001010001)
    p.add_argument('--label', default=None, help='Displayed checkpoint label; defaults to checkpoint filename')
    p.add_argument('--search-budget', type=int, default=0,
                   help='Optional public-belief root search simulations per decision')
    p.add_argument('--search-rollout-depth', type=int, default=8)
    args = p.parse_args()
    if args.search_budget < 0 or (args.search_budget and args.search_budget < 4) or args.search_rollout_depth < 0:
        p.error('search budget must be zero or at least four')
    import torch
    from benchmark_mcts import _decoded_decks
    from train_entity_selfplay import select_device, file_digest
    from evaluate_entity_policy import select_policy, play_job
    import build_hearthstone_board_replay as board
    torch.set_num_threads(2)
    args.cards = ROOT / 'cards.251332.enUS.json'
    args.deck_config = ROOT / 'config/decks_20260925_smoke8.json'
    if not args.deck_config.exists():
        # The live handoff branch may only carry the flattened standard deck
        # registry; keep the replay generator usable on that checkout too.
        args.deck_config = ROOT / 'config/decks_20260924_flat.json'
    args.max_actions = 400
    args.max_game_seconds = 180
    args.save_traces = True
    args.output.mkdir(parents=True, exist_ok=False)
    decks = _decoded_decks(args.deck_config)
    deck = next(k for k in decks if k.startswith('龙战'))
    policy = select_policy('entity', args.checkpoint, select_device(args.device),
                           search_budget=args.search_budget,
                           search_rollout_depth=args.search_rollout_depth)
    report = {'checkpoint': str(args.checkpoint), 'sha256': file_digest(args.checkpoint),
              'policy_mode': 'entity_root_search' if args.search_budget else 'greedy_without_search',
              'search_budget': args.search_budget,
              'search_rollout_depth': args.search_rollout_depth,
              'both_players_same_checkpoint': True,
              'mulligan': 'existing_engine_default_not_learned',
              'deck': deck, 'deck_counts': decks[deck][0],
              'audit_is_omniscient': True, 'model_observations_are_player_visible': True,
              'source_sha256': {str(f.relative_to(ROOT)): file_digest(f)
                                for f in (ROOT / 'src/hsa').rglob('*.py')}, 'games': []}
    for i in range(3):
        job = {'pair_id': i, 'seed': args.seed + i, 'candidate_deck': deck,
               'opponent_deck': deck, 'candidate_seat': 0}
        result = play_job(job, policy, policy, decks, args)
        report['games'].append(result)
        (args.output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({k: result.get(k) for k in ('seed', 'status', 'winner', 'steps', 'turns', 'invalid_actions', 'error')}, ensure_ascii=False), flush=True)
        if result['status'] != 'complete':
            raise RuntimeError('Trace failed; retained original seed and failure, no cherry-picking')
    sys.argv = ['build_hearthstone_board_replay.py', str(args.output / 'dragon-mirror-replay.html')] + [
        f'第{i+1}局 · {args.label or args.checkpoint.stem}={g["trace"]}' for i, g in enumerate(report['games'])]
    board.main()


if __name__ == '__main__':
    main()

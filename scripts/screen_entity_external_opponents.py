"""Bounded independent-opponent screen, with player-visible policy diagnostics."""
import argparse
import json
import math
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'scripts')]


def unknown_card_entities(view, vocab):
    # CLASS_POWER names are synthetic hero-power markers, not missing cards.
    return sum(bool(e.get('card_id')) and not e['card_id'].startswith('CLASS_POWER:')
               and e['card_id'] not in vocab for e in view['entities'])


def probe_policy(path, device):
    import torch
    from hsa.entity_model import EntityPolicyValueNet, collate_views
    from hsa.observer_view import observer_view
    model = EntityPolicyValueNet.from_payload(torch.load(path, map_location='cpu', weights_only=False)).to(device).eval()
    def choose(game, actions, counts):
        view = observer_view(game, actions=actions, known_deck=counts)
        with torch.no_grad():
            logits, values = model(collate_views([view], model.card_ids, device))
            probabilities = logits[0, :len(actions)].softmax(-1).cpu().tolist()
        if not all(math.isfinite(p) for p in probabilities):
            raise ValueError('nonfinite probabilities')
        index = max(range(len(actions)), key=probabilities.__getitem__)
        choose.last_value = float(values[0])
        if len(actions) > 1:
            entropy = -sum(p * math.log(max(p, 1e-30)) for p in probabilities)
            choose.probes.append({'turn': game.turn, 'legal': len(actions),
                'top_probability': probabilities[index], 'normalized_entropy': entropy / math.log(len(actions)),
                'chosen_kind': view['actions'][index]['kind'], 'value': choose.last_value,
                'unknown_entities': unknown_card_entities(view, vocab)})
        return actions[index]
    vocab = set(model.card_ids)
    choose.probes = []
    return choose


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--checkpoints', type=Path, nargs='+', required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--device', default='npu:3')
    p.add_argument('--seed', type=int, default=203401010000)
    args = p.parse_args()
    import torch
    from benchmark_mcts import _decoded_decks
    from train_entity_selfplay import select_device, file_digest
    from evaluate_entity_policy import play_job, make_schedule, summary, candidate_deck_summary, value_calibration_summary, select_policy
    from hsa.mcts import InformationSetMCTSPolicy
    torch.set_num_threads(2)
    args.cards = ROOT / 'cards.251332.enUS.json'
    args.deck_config = ROOT / 'config/decks_20260925_smoke8.json'
    args.max_actions = 400
    args.max_game_seconds = 300
    args.save_traces = False
    base = args.output
    base.mkdir(parents=True, exist_ok=False)
    decks = _decoded_decks(args.deck_config)
    names = sorted(decks)
    device = select_device(args.device)
    report = {'status': 'running', 'automatic_promotion': False,
        'note': 'heuristic: all 64 ordered matchups with seat swap; search: 8 fixed cross-deck matchups with seat swap; screening only',
        'source_sha256': {str(f.relative_to(ROOT)): file_digest(f) for f in (ROOT / 'src/hsa').rglob('*.py')},
        'checkpoints': []}
    for index, checkpoint in enumerate(args.checkpoints):
        policy = probe_policy(checkpoint, device)
        entry = {'checkpoint': str(checkpoint), 'sha256': file_digest(checkpoint), 'opponents': {}}
        report['checkpoints'].append(entry)
        for kind in ('heuristic', 'ismcts16'):
            args.output = base / f'model{index}-{kind}'
            args.output.mkdir()
            if kind == 'heuristic':
                jobs = make_schedule(names, 1, args.seed)
                opponent = select_policy('heuristic', None, device)
            else:
                jobs = [{'pair_id': i, 'candidate_deck': name, 'opponent_deck': names[(i+1) % len(names)],
                         'candidate_seat': seat, 'seed': args.seed + 10000 + i}
                        for i, name in enumerate(names) for seat in (0, 1)]
            results = []
            policy.probes.clear()
            for job in jobs:
                if kind == 'ismcts16':
                    search = InformationSetMCTSPolicy(samples=4, iterations_per_sample=4,
                        tree_depth=8, rollout_depth=8, seed=job['seed'], max_total_iterations=16)
                    opponent = lambda game, actions, counts: search.choose(game)
                results.append(play_job(job, policy, opponent, decks, args))
                entry['opponents'][kind] = {'planned': len(jobs), 'games': results,
                    'summary': summary(results), 'by_deck': candidate_deck_summary(results),
                    'value_calibration': value_calibration_summary(results)}
                probes = policy.probes
                entry['opponents'][kind]['policy_diagnostics'] = {
                    'nontrivial_decisions': len(probes),
                    'mean_normalized_entropy': statistics.mean(r['normalized_entropy'] for r in probes) if probes else None,
                    'mean_top_probability': statistics.mean(r['top_probability'] for r in probes) if probes else None,
                    'unknown_entity_decisions': sum(r['unknown_entities'] > 0 for r in probes)}
                temporary = base / 'screen.tmp'
                temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
                temporary.replace(base / 'screen.json')
                print(json.dumps({'model': index, 'opponent': kind, 'done': len(results), 'planned': len(jobs),
                                  'summary': summary(results)}), flush=True)
        del policy
    report['status'] = 'complete'
    (base / 'screen.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()

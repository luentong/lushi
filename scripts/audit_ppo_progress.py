"""Read-only round-level update audit; never interpret entropy alone as strength."""
import argparse
import json
import math
from pathlib import Path
import statistics


def summarize_round(report, batch_size, epochs):
    history = report['history'][-1]
    updates = history['updates']
    applied = [u for u in updates if u.get('update_applied', True)]
    planned = math.ceil(history['rows'] / batch_size) * epochs
    return {'round': history['round'], 'rows': history['rows'],
            'planned_updates': planned, 'applied_updates': len(applied),
            'update_fraction': len(applied) / planned,
            'kl_stopped': history['kl_early_stopped'],
            'trigger_kl': updates[-1]['approx_kl'] if history['kl_early_stopped'] else None,
            'mean_applied_kl': statistics.mean(u['approx_kl'] for u in applied) if applied else None,
            'mean_training_entropy': statistics.mean(u['entropy'] for u in applied) if applied else None,
            'mean_training_value_mse': statistics.mean(u['value_loss'] for u in applied) if applied else None,
            'opponent_versions': history['opponent_versions']}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--runs', nargs='+', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        p.error('output exists')
    result = {'limitations': ['training entropy is not normalized by legal action count',
                              'training value loss is not independent calibration',
                              'early stopping on a single minibatch may be noisy; this audit does not establish causality'],
              'runs': []}
    for directory in args.runs:
        pipeline = json.loads((directory / 'pipeline.json').read_text())
        cfg = pipeline['config']
        rows = []
        for entry in pipeline['rounds']:
            report = json.loads(Path(entry['report']).read_text())
            rows.append(summarize_round(report, cfg['batch_size'], cfg['epochs']))
        result['runs'].append({'directory': str(directory), 'rounds': rows,
            'kl_stopped_rounds': sum(r['kl_stopped'] for r in rows),
            'planned_updates': sum(r['planned_updates'] for r in rows),
            'applied_updates': sum(r['applied_updates'] for r in rows),
            'update_fraction': sum(r['applied_updates'] for r in rows) / sum(r['planned_updates'] for r in rows)})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps([{k: v for k, v in r.items() if k != 'rounds'} for r in result['runs']]))


if __name__ == '__main__':
    main()

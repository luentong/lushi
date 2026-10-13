"""Opt-in fixed game-balanced full-distribution KL guard for PPO experiments."""
from collections import defaultdict
import random


def select_probe_rows(rows, size, seed):
    if size < 1 or not rows:
        raise ValueError('positive probe size and nonempty rows required')
    games = defaultdict(list)
    for row in rows:
        games[row['game_seed']].append(row)
    rng = random.Random(seed)
    keys = sorted(games)
    rng.shuffle(keys)
    # Equal game weights: no oversampling of long games or duplicate positions.
    return [rng.choice(games[key]) for key in keys[:size]]


def categorical_kl(old_logp, new_logp):
    import torch
    if old_logp.shape != new_logp.shape:
        raise ValueError('policy distribution shape mismatch')
    values = (old_logp.exp() * (old_logp - new_logp)).sum(-1)
    if not torch.isfinite(values).all():
        raise ValueError('nonfinite full-policy KL')
    return values.clamp_min(0)


def build_probe(model, rows, size, seed, device, batch_size):
    import torch
    from hsa.entity_model import collate_views
    selected = select_probe_rows(rows, size, seed)
    probe = []
    with torch.no_grad():
        for start in range(0, len(selected), batch_size):
            chunk = selected[start:start + batch_size]
            batch = collate_views([r['view'] for r in chunk], model.card_ids)
            logits, _ = model({k: v.to(device) for k, v in batch.items()})
            probe.append((batch, logits.log_softmax(-1).cpu()))
    return probe


def measure_probe(model, probe, device):
    import torch
    values = []
    with torch.no_grad():
        for batch, old_logp in probe:
            logits, _ = model({k: v.to(device) for k, v in batch.items()})
            values.extend(categorical_kl(old_logp.to(device), logits.log_softmax(-1)).cpu().tolist())
    if not values:
        raise ValueError('empty KL probe')
    return {'mean': sum(values) / len(values), 'max': max(values), 'games': len(values)}

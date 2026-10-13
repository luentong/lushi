"""Bounded deck completion hypotheses for observed small list variations.

Variants constrain a starting list; they do not expose hidden cards or assign
calibrated probabilities. Special deckbuilding packages stay unchanged.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json


def _ordinary_card(card_id, metadata, player_class):
    card = metadata.get(card_id, {})
    classes = set(card.get('classes') or [card.get('cardClass')])
    text = str(card.get('text') or '').lower()
    return (card.get('collectible') is True
            and card.get('rarity') != 'LEGENDARY'
            and bool(classes & {'NEUTRAL', player_class})
            and not (set(card.get('mechanics', ())) & {'FABLED', 'RULEBREAKER'})
            and 'start of game' not in text)


def _removals(surplus, needed, index=0):
    if needed == 0:
        yield {}
        return
    if index >= len(surplus) or sum(n for _, n in surplus[index:]) < needed:
        return
    card, count = surplus[index]
    for amount in range(min(count, needed) + 1):
        for rest in _removals(surplus, needed - amount, index + 1):
            yield ({card: amount, **rest} if amount else rest)


def compatible_deck_variants(candidates, observed, player_class, metadata, *,
                             max_replacements=3, max_variants=64, starting_size=None):
    """Prefer compatible manifest lists, else enumerate a nearest small edit.

    Only unobserved surplus copies of ordinary cards may be removed. Anchors
    such as legendary/Fabled/Rulebreaker cards and noncollectible companions
    are retained. This deliberately covers ordinary flex-card substitutions;
    changing a deckbuilding package needs separate validation.
    """
    if max_replacements < 0 or max_variants < 1:
        raise ValueError('invalid variant bounds')
    observed = Counter(observed)
    if any(not isinstance(n, int) or isinstance(n, bool) or n < 1
           for n in observed.values()):
        raise ValueError('observed counts must be positive integers')
    same_class = [candidate for candidate in candidates if candidate['class'] == player_class
                  and (starting_size is None or sum(candidate['counts'].values()) == starting_size)]
    exact = [candidate for candidate in same_class
             if all(candidate['counts'].get(card, 0) >= n for card, n in observed.items())]
    if exact:
        return {'mode': 'manifest', 'candidates': exact, 'replacements': 0,
                'truncated': False}
    parents = []
    for candidate in same_class:
        base = Counter(candidate['counts'])
        additions = observed - base
        distance = sum(additions.values())
        if not 0 < distance <= max_replacements or sum(observed.values()) > sum(base.values()):
            continue
        if any(not _ordinary_card(card, metadata, player_class) or observed[card] > 2
               for card in additions):
            continue
        surplus = sorted((card, n) for card, n in (base - observed).items()
                         if _ordinary_card(card, metadata, player_class))
        if sum(n for _, n in surplus) >= distance:
            parents.append((distance, candidate, additions, surplus))
    if not parents:
        return {'mode': 'unresolved', 'candidates': [], 'replacements': None,
                'truncated': False}
    nearest = min(parent[0] for parent in parents)
    variants = []
    seen = set()
    for distance, candidate, additions, surplus in parents:
        if distance != nearest:
            continue
        for removed in _removals(surplus, distance):
            counts = dict(+(Counter(candidate['counts']) + additions - Counter(removed)))
            key = tuple(sorted(counts.items()))
            if key in seen:
                continue
            seen.add(key)
            if len(variants) == max_variants:
                return {'mode': 'synthetic_variants', 'candidates': variants,
                        'replacements': nearest, 'truncated': True}
            digest = hashlib.sha256(json.dumps(key).encode()).hexdigest()[:16]
            variants.append({'id': f'variant:{digest}', 'class': player_class,
                             'counts': counts, 'base_candidate_id': candidate['id'],
                             'added': dict(additions), 'removed': removed})
    return {'mode': 'synthetic_variants', 'candidates': variants,
            'replacements': nearest, 'truncated': False}

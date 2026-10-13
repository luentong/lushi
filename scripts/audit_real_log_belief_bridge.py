#!/usr/bin/env python3
"""Audit local action legality with a known own deck and causal opponent candidates.

Each action receives a freshly hydrated public snapshot, not a replay of
predicted effects. A passing action is therefore a legality check only.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'scripts'), str(ROOT / '.deps')]

from audit_real_log_action_bridge import action_matches, initial_public_classes
from export_live_deck_configs import decode_counts, get_deck_class
from hsa.deck_metadata import apply_deck_metadata_overrides
from hsa.deck_variants import compatible_deck_variants
from hsa.live_bridge import build_snapshot_hypothesis
from hsa.live_state import LiveGameState, _ordered_game_events
from hsa.real_log_deck_evidence import collect_deck_evidence


def audit_belief_bridge(game, *, cards_path, own_deck, candidates,
                        eligible_ids, local_controller, max_actions=100,
                        metadata=None, max_replacements=0, max_variants=64):
    if game.get('identity_timing') != 'causal_reveal_only':
        raise ValueError('causal import required')
    classes = initial_public_classes(game)
    if set(classes) != {1, 2}:
        raise ValueError('both opening hero classes must be observed')
    opponent = 3 - local_controller
    state = LiveGameState()
    rows = []
    pool_cache = {}
    for _, kind, item, parent in _ordered_game_events(game):
        if kind == 'block' and item.get('block_type') in {'PLAY', 'ATTACK', 'DECK_ACTION'}:
            source = state.entities.get(str(item.get('source_entity')))
            if source is not None and source.controller == local_controller:
                evidence = collect_deck_evidence(
                    game, eligible_ids, before_packet=int(item['packet_id']))
                if evidence.get('reset_boundary') is not None:
                    rows.append({'packet_id': item['packet_id'],
                                 'status': 'deck_provenance_stopped_at_reset'})
                    break
                observed = evidence['controllers'].get(str(opponent), {}).get('observed_counts', {})
                opening_size = evidence['controllers'].get(str(opponent), {}).get('opening_entities')
                origin_size = sum(
                    1 for entity in state.entities.values()
                    if entity.controller == opponent
                    and entity.zone_history
                    and entity.zone_history[0][1] == 'DECK'
                    and not any(entity.tags.get(tag) not in (None, 0, '0', '')
                                for tag in ('CREATOR', 'COPIED_FROM_ENTITY_ID'))
                )
                # A complete opening entity inventory is observable before
                # any plays. Partial/synthetic fragments don't constrain size.
                starting_size = (origin_size if origin_size in (30, 40)
                                 else opening_size if opening_size in (20, 30, 40)
                                 else None)
                pool_key = (starting_size, tuple(sorted(observed.items())))
                if pool_key not in pool_cache:
                    pool_cache[pool_key] = compatible_deck_variants(
                        candidates, observed, classes[opponent], metadata or {},
                        max_replacements=max_replacements, max_variants=max_variants,
                        starting_size=starting_size)
                pool = pool_cache[pool_key]
                viable = pool['candidates']
                checks = []
                for candidate in viable:
                    bridge = build_snapshot_hypothesis(
                        cards_path=cards_path, state=state, own_deck=own_deck,
                        opponent_deck=candidate['counts'],
                        player_classes=(classes[local_controller], classes[opponent]),
                        self_controller=local_controller, seed=1000 + len(rows),
                        setaside_policy='advisory')
                    checks.append({
                        'candidate_id': candidate['id'],
                        'variant': ({key: candidate[key] for key in
                                     ('base_candidate_id', 'counts', 'added', 'removed')}
                                    if 'base_candidate_id' in candidate else None),
                        'status': ('bridge_rejected' if not bridge.available else
                                   'legal_action_matched' if action_matches(item, bridge.game, state)
                                   else 'observed_action_not_legal'),
                        'reason': bridge.reason,
                        'deck_count_check': ([{
                            'controller': controller,
                            'log': sum(e.controller == controller and e.zone == 'DECK'
                                       for e in state.entities.values()),
                            'hypothesis': len(bridge.game.players[controller - 1].deck),
                        } for controller in (1, 2)]
                            if bridge.available and hasattr(bridge.game, 'players') else []),
                        'hypothesis_notes': getattr(bridge, 'hypothesis_notes', []),
                    })
                statuses = Counter(check['status'] for check in checks)
                row = {
                    'packet_id': item['packet_id'], 'turn': state.turn,
                    'source_card': source.card_id, 'kind': item['block_type'],
                    'observed_opponent_deck_counts': observed,
                    'candidate_count': len(viable),
                    'observed_starting_size': starting_size,
                    'candidate_mode': pool['mode'],
                    'candidate_replacements': pool['replacements'],
                    'candidate_enumeration_truncated': pool['truncated'],
                    'status': ('candidate_library_exhausted' if not viable else
                               'legal_under_all_candidates' if statuses['legal_action_matched'] == len(viable)
                               else 'requires_bridge_review'),
                    'status_counts': dict(statuses), 'checks': checks,
                }
                rows.append(row)
                if len(rows) >= max_actions:
                    break
        state._apply_ordered_event(kind, item, parent)
    return {'actions_examined': len(rows),
            'status_counts': dict(Counter(row['status'] for row in rows)),
            'bridge_reasons': dict(Counter(check['reason'] for row in rows
                                           for check in row.get('checks', ())
                                           if check['reason'])),
            'deck_count_mismatch_actions': sum(any(
                count['log'] != count['hypothesis']
                for check in row.get('checks', ()) for count in check.get('deck_count_check', ()))
                for row in rows),
            'rows': rows}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--log', type=Path, required=True)
    p.add_argument('--known', type=Path, required=True)
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--local-controller', type=int, choices=(1, 2), required=True)
    p.add_argument('--max-actions', type=int, default=100)
    p.add_argument('--max-replacements', type=int, default=0)
    p.add_argument('--max-variants', type=int, default=64)
    p.add_argument('--decisions', type=Path,
                   help='optional causal decision report; TURN_END records are merged as public-transition checks')
    p.add_argument('--cards', type=Path, default=ROOT / 'cards.251332.enUS.json')
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if (args.output.exists() or args.max_actions < 1
            or args.max_replacements < 0 or args.max_variants < 1):
        p.error('choose a new output path and a positive max-actions')
    payload = json.loads(args.log.read_text(encoding='utf-8'))
    game = payload['games'][-1] if payload.get('games') else payload
    own = json.loads(args.known.read_text(encoding='utf-8'))[str(args.local_controller)]
    cards = json.loads(args.cards.read_text(encoding='utf-8'))
    by_dbf = {int(card['dbfId']): card for card in cards if 'dbfId' in card}
    apply_deck_metadata_overrides(by_dbf)
    entries = json.loads(args.manifest.read_text(encoding='utf-8'))['decks']
    candidates = [{'id': entry['id'],
                   'class': get_deck_class(entry['deckstring'], by_dbf),
                   'counts': decode_counts(entry['deckstring'], by_dbf)} for entry in entries]
    eligible = {card['id'] for card in cards if card.get('collectible')}
    eligible.update(card for candidate in candidates for card in candidate['counts'])
    result = audit_belief_bridge(
        game, cards_path=args.cards, own_deck=own, candidates=candidates,
        eligible_ids=eligible, local_controller=args.local_controller,
        max_actions=args.max_actions, metadata={card['id']: card for card in by_dbf.values()},
        max_replacements=args.max_replacements, max_variants=args.max_variants)
    # TURN_END is represented by MAIN_END rather than a normal source block in
    # the normalized Power.log import, so it cannot be checked through the
    # action matcher above.  Merge the compact decision-level confirmation when
    # the causal decision export is available, without pretending this proves a
    # hidden-state or policy decision.
    if args.decisions:
        decision_payload = json.loads(args.decisions.read_text(encoding='utf-8'))
        turn_end_rows = []
        for record in decision_payload.get('records', ()):
            action = record.get('action', {})
            if action.get('kind') != 'TURN_END':
                continue
            before = record.get('pre_action_public_state', {})
            turn_end_rows.append({
                'packet_id': record.get('packet_id'),
                'turn': before.get('turn'),
                'kind': 'TURN_END',
                'actor_controller': record.get('actor_controller'),
                'active_player': before.get('active_player'),
                'game_phase': before.get('game_phase'),
                'client_option_confirmed': bool(record.get('client_option_confirmed')),
                'status': ('turn_end_public_transition_consistent'
                           if record.get('public_transition_audit', {}).get('status')
                           == 'public_transition_consistent'
                           else 'turn_end_requires_review'),
                'blockers': record.get('blockers', []),
            })
        result['turn_end_checks'] = turn_end_rows
        result['turn_end_status_counts'] = dict(Counter(row['status'] for row in turn_end_rows))
        result['actions_examined'] += len(turn_end_rows)
        result['status_counts'].update(result['turn_end_status_counts'])
        result['decision_report'] = str(args.decisions)
    result.update({'schema': 'real-log-causal-belief-bridge-v1',
                   'source_sha256': payload.get('source_sha256'),
                   'known_deck': str(args.known), 'manifest': str(args.manifest),
                   'max_replacements': args.max_replacements, 'max_variants': args.max_variants,
                       'training_authorized': False,
                   'limitations': [
                       'PLAY/ATTACK/TRADE are legality-checked; TURN_END is merged from causal public-transition records.',
                       'Each action starts from a hydrated log snapshot; post-action effect fidelity is not verified.',
                       'Hidden Trial recipes and Godfrey recovery order are sampled hypotheses, not observed truth.',
                       'Deck variants are bounded compatible completions, not calibrated opponent probabilities.',
                   ],
                   'scope': 'local PLAY/ATTACK legality under causal candidate lists; not predicted effect validation'})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: result[key] for key in
                      ('actions_examined', 'status_counts', 'bridge_reasons',
                       'deck_count_mismatch_actions')}, ensure_ascii=True))


if __name__ == '__main__':
    main()

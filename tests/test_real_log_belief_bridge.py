import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import audit_real_log_belief_bridge as audit


def test_candidates_use_only_reveals_before_each_action_and_exhaust_explicitly():
    opening = [{
        'kind': 'FullEntity', 'packet_id': entity, 'entity': entity,
        'tags': [{'tag': 'ZONE', 'value': 'DECK'},
                 {'tag': 'CONTROLLER', 'value': 2}],
    } for entity in (1, 2, 3)]
    opening.append({'kind': 'FullEntity', 'packet_id': 4, 'entity': 4,
                    'card_id': 'SELF', 'tags': [
                        {'tag': 'ZONE', 'value': 'HAND'},
                        {'tag': 'CONTROLLER', 'value': 1}]})
    def show(packet, entity):
        return {'kind': 'ShowEntity', 'packet_id': packet,
                'entity': entity, 'card_id': 'OPP'}
    game = {'identity_timing': 'causal_reveal_only', 'preamble': opening,
            'blocks': [
                {'packet_id': 10, 'block_type': 'PLAY', 'source_entity': 4,
                 'effects': [show(11, 1), show(12, 2)]},
                {'packet_id': 20, 'block_type': 'PLAY', 'source_entity': 4,
                 'effects': [show(21, 3)]},
                {'packet_id': 30, 'block_type': 'PLAY', 'source_entity': 4},
            ]}
    candidates = [
        {'id': 'a', 'class': 'WARLOCK', 'counts': {'OPP': 1}},
        {'id': 'b', 'class': 'WARLOCK', 'counts': {'OPP': 2}},
        {'id': 'wrong-class', 'class': 'MAGE', 'counts': {'OPP': 3}},
    ]
    with patch.object(audit, 'initial_public_classes', return_value={1: 'PRIEST', 2: 'WARLOCK'}), \
            patch.object(audit, 'build_snapshot_hypothesis', return_value=SimpleNamespace(
                available=True, game=None, reason=None)), \
            patch.object(audit, 'action_matches', return_value=True):
        result = audit.audit_belief_bridge(
            game, cards_path='unused', own_deck={'SELF': 30},
            candidates=candidates, eligible_ids={'OPP', 'SELF'}, local_controller=1)
    assert [row['candidate_count'] for row in result['rows']] == [2, 1, 0]
    assert [row['observed_opponent_deck_counts'] for row in result['rows']] == [
        {}, {'OPP': 2}, {'OPP': 3}]
    assert result['rows'][-1]['status'] == 'candidate_library_exhausted'

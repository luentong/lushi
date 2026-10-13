from types import SimpleNamespace

from scripts.audit_real_log_action_bridge import action_matches


class FakeAction:
    def __init__(self, kind, source=None):
        self.kind, self.source = kind, source
        self.target_player = self.target_entity = None


class FakeGame:
    def __init__(self, actions):
        self._actions = actions

    def legal_actions(self):
        return self._actions


class FakeState:
    entities = {}
    entity_registry = {}


def test_turn_end_matches_without_source_entity():
    assert action_matches({'block_type': 'TURN_END'}, FakeGame([FakeAction('END_TURN')]), FakeState())
    assert not action_matches({'block_type': 'TURN_END'}, FakeGame([FakeAction('PLAY')]), FakeState())


def test_trade_block_matches_trade_source():
    state = FakeState()
    state.entities = {'42': SimpleNamespace(card_type='SPELL', zone='HAND', controller=1,
                                             card_id='TRADEABLE')}
    assert action_matches({'block_type': 'DECK_ACTION', 'source_entity': 42},
                          FakeGame([FakeAction('TRADE', 42)]), state)
    assert not action_matches({'block_type': 'DECK_ACTION', 'source_entity': 42},
                              FakeGame([FakeAction('PLAY', 42)]), state)

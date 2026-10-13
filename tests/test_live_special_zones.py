from pathlib import Path

from hsa.live_bridge import build_snapshot_hypothesis, _visible_card_counts
from hsa.live_special_zones import (broxigar_reserves, godfrey_public_copies,
                                   generated_hidden_hand_card)
from hsa.live_state import EntityView, LiveGameState


def snapshot():
    state = LiveGameState(turn=5, active_player=1)
    for controller in (1, 2):
        key = str(controller)
        state.entities[key] = EntityView(key, card_id=f'HERO_{controller:02d}',
            controller=controller, zone='PLAY', card_type='HERO', health=30)
        key = str(controller + 2)
        state.entities[key] = EntityView(key, controller=controller, card_type='PLAYER',
                                        tags={'RESOURCES': 10, 'MAXRESOURCES': 10})
    return state


def bridge(state, *, own=None, opponent=None, seed=7):
    result = build_snapshot_hypothesis(
        cards_path=Path(__file__).parents[1] / 'cards.251332.enUS.json',
        state=state, own_deck=own or {'CORE_BT_035': 30},
        opponent_deck=opponent or {'CORE_BT_035': 30},
        player_classes=('DEMONHUNTER', 'WARLOCK'), seed=seed,
        setaside_policy='advisory')
    assert result.available, (result.reason, result.public_match)
    return result.game


def atlas_state():
    state = snapshot()
    state.entities['70'] = EntityView('70', card_id='JAIL_509e', controller=2,
        zone='PLAY', card_type='ENCHANTMENT', tags={'ATTACHED': 4})
    state.entities['88'] = EntityView('88', controller=2, zone='HAND',
        zone_history=[(10, 'SETASIDE'), (20, 'HAND')], tags={'ZONE_POSITION': 1})
    state.entities['89'] = EntityView('89', card_id='JAIL_515', controller=2,
        zone='SETASIDE', card_type='SPELL', cost=2,
        tags={'CREATOR': 70, 'COPIED_FROM_ENTITY_ID': 88})
    return state


def test_godfrey_inference_needs_public_proxy_and_never_mutates_hidden_state():
    state = atlas_state()
    assert godfrey_public_copies(state)['88'].cost == 1
    assert state.entities['88'].card_id is None
    state.entities['70'].card_id = 'UNRELATED_COPY_EFFECT'
    assert not godfrey_public_copies(state)
    state.entities['70'].card_id = 'JAIL_509e'
    state.entities['88'].identity_history = [(15, 'OTHER_CARD')]
    assert not godfrey_public_copies(state)
    state.entities['88'].identity_history.clear()
    state.entities.pop('89')
    assert not godfrey_public_copies(state)


def test_godfrey_hand_copy_does_not_consume_original_deck_and_preserves_order():
    state = atlas_state()
    state.entities['90'] = EntityView('90', controller=2, zone='HAND',
                                    tags={'ZONE_POSITION': 2})
    state.entities['91'] = EntityView('91', card_id='CORE_BT_035', controller=2,
        zone='HAND', card_type='MINION', tags={'ZONE_POSITION': 3})
    game = bridge(state)
    player = game.players[1]
    assert [c.entity_id for c in player.hand] == [88, 90, 91]
    assert player.hand[0].card_id == 'JAIL_515'
    assert player.hand[0].cost == 1
    assert len(player.deck) == 28


def test_godfrey_reserve_hydrated_separately_from_hand():
    state = atlas_state()
    state.entities['88'].zone = 'SETASIDE'
    state.entities['88'].zone_history = [(10, 'SETASIDE')]
    game = bridge(state, opponent={'JAIL_509': 1, 'CORE_BT_035': 29})
    assert not game.players[1].hand
    assert len(game.players[1].deck) == 30
    assert [(c.card_id, c.cost) for c in game.players[1].overdrawn_cards] == [('JAIL_515', 1)]


def test_broxigar_reserve_and_once_only_return_survive_bridge():
    state = snapshot()
    entity = EntityView('27', card_id='TIME_020', controller=1,
        zone='SETASIDE', card_type='MINION', zone_history=[(1, 'DECK'), (2, 'SETASIDE')])
    state.entities['27'] = entity
    own = {'TIME_020': 1, 'CORE_BT_035': 29}
    game = bridge(state, own=own)
    assert game.players[0].broxigar_removed_from_game
    assert not game.players[0].broxigar_return_used
    assert not any(c.card_id == 'TIME_020' for c in game.players[0].deck)
    entity.zone = 'HAND'
    entity.zone_history.append((3, 'HAND'))
    game = bridge(state, own=own)
    assert game.players[0].broxigar_return_used
    assert game.players[0].hand[0].card_id == 'TIME_020'
    entity.tags['CREATOR'] = 999
    assert not broxigar_reserves(state)


def test_explicit_hero_power_refresh_beats_earlier_use_but_not_exhaustion():
    state = snapshot()
    power = EntityView('86', card_id='JAIL_EVENT_101hp', controller=1,
        zone='PLAY', card_type='HERO_POWER', tags={'EXHAUSTED': 0, 'TAG_SCRIPT_DATA_NUM_1': 3})
    state.entities['86'] = power
    state.action_history = [{'turn': 5, 'kind': 'POWER', 'source_entity': 86, 'controller': 1}]
    game = bridge(state)
    assert not game.players[0].hero_power_used
    assert game.players[0].collapsing_star_damage == 3
    assert any(a.kind == 'HERO_POWER' for a in game.legal_actions())
    power.tags['EXHAUSTED'] = 1
    assert bridge(state).players[0].hero_power_used
    power.tags.pop('EXHAUSTED')
    assert bridge(state).players[0].hero_power_used


def test_original_hero_card_and_stolen_card_count_against_original_owner():
    state = snapshot()
    card = EntityView('48')
    card.apply({'packet_id': 1, 'card_id': 'CATA_190h', 'tags': [
        {'tag': 'CONTROLLER', 'value': 2}, {'tag': 'ZONE', 'value': 'DECK'},
        {'tag': 'CARDTYPE', 'value': 'HERO'}]})
    card.apply({'packet_id': 2, 'tag': 'ZONE', 'value': 'GRAVEYARD'})
    state.entities['48'] = card
    stolen = EntityView('17')
    stolen.apply({'packet_id': 3, 'card_id': 'CATA_526', 'tags': [
        {'tag': 'CONTROLLER', 'value': 1}, {'tag': 'ZONE', 'value': 'DECK'}]})
    stolen.apply({'packet_id': 4, 'tag': 'CONTROLLER', 'value': 2})
    stolen.apply({'packet_id': 5, 'tag': 'ZONE', 'value': 'HAND'})
    state.entities['17'] = stolen
    assert _visible_card_counts(state, 1) == {'CATA_526': 1}
    assert _visible_card_counts(state, 2) == {'CATA_190h': 1}


def test_known_deck_cards_are_not_sampled_into_hidden_hand():
    state = snapshot()
    state.entities['50'] = EntityView('50', card_id='CORE_UNG_205', controller=2,
        zone='DECK', card_type='MINION', zone_history=[(1, 'DECK')])
    state.entities['51'] = EntityView('51', controller=2, zone='HAND')
    state.entities['52'] = EntityView('52', card_id='TIME_025t', controller=2,
        zone='DECK', card_type='SPELL', tags={'CREATOR': 99})
    for seed in range(5):
        game = bridge(state, opponent={'CORE_UNG_205': 1, 'CORE_BT_035': 29}, seed=seed)
        player = game.players[1]
        assert player.hand[0].card_id == 'CORE_BT_035'
        assert len(player.deck) == 30
        assert {c.entity_id for c in player.deck if c.card_id in {'CORE_UNG_205', 'TIME_025t'}} == {50, 52}


def test_generated_trial_samples_legal_recipe_without_deducting_deck():
    state = snapshot()
    state.entities['216'] = EntityView('216', controller=2, zone='HAND',
        zone_history=[(1, 'SETASIDE'), (2, 'HAND')],
        creation_context={'source_card': 'CAP_405', 'block_type': 'POWER'})
    game = bridge(state)
    card = game.players[1].hand[0]
    assert card.card_id in {'CAP_405tb1', 'CAP_405tb2', 'CAP_405tb3'}
    assert len(set(card.sham_trial_effect_ids)) == 2
    assert len(game.players[1].deck) == 30
    assert state.entities['216'].card_id is None
    state.entities['216'].creation_context.clear()
    assert generated_hidden_hand_card(game, state.entities['216']) is None


def test_opening_coin_needs_witnessed_game_deal_not_arbitrary_hidden_hand():
    state = snapshot()
    coin = EntityView('68', controller=2, zone='HAND', zone_history=[(125, 'HAND')],
        creation_context={'source_type': 'GAME', 'block_type': 'TRIGGER',
                          'turn': 1, 'phase': None, 'opening_hand_count': 4})
    state.entities['68'] = coin
    game = bridge(state)
    assert game.players[1].hand[0].card_id == 'GAME_005'
    assert len(game.players[1].deck) == 30
    coin.creation_context['turn'] = 5
    assert generated_hidden_hand_card(game, coin) is None


def test_creation_context_uses_parent_at_creation_not_later_reveal():
    state = snapshot()
    state.entities['120'] = EntityView('120', controller=2, zone='PLAY',
                                       card_id='CAP_405', card_type='MINION')
    state.apply_block_delta({'block_type': 'POWER', 'source_entity': 120, 'effects': [
        {'kind': 'FullEntity', 'packet_id': 10, 'entity': 216, 'tags': [
            {'tag': 'ZONE', 'value': 'SETASIDE'}, {'tag': 'CONTROLLER', 'value': 2}]}]})
    entity = state.entities['216']
    assert entity.creation_context['source_card'] == 'CAP_405'
    assert entity.card_id is None
    state.apply_row({'kind': 'ShowEntity', 'packet_id': 20, 'entity': 216, 'card_id': 'CAP_405tb1'})
    assert entity.creation_context['source_card'] == 'CAP_405'

from pathlib import Path

from hsa.live_bridge import (_public_remaining_durability,
                             _retired_deathwing_hero_entities,
                             _retired_linked_hero_powers,
                             _unplayed_unlinked_setaside_heroes,
                             build_snapshot_hypothesis)
from hsa.live_state import EntityView, LiveGameState, reconstruct_game


def test_historical_setaside_links_do_not_block_but_live_links_do():
    state = LiveGameState()
    state.entities = {
        "54": EntityView("54", card_id="TIME_020", controller=2,
                         zone="SETASIDE", card_type="MINION"),
        "34": EntityView("34", card_id="TIME_020t2", controller=2,
                         zone="GRAVEYARD", card_type="MINION",
                         tags={"TAG_SCRIPT_DATA_NUM_1": 54}),
        "92": EntityView("92", controller=1, zone="SETASIDE"),
        "99": EntityView("99", card_id="TLC_100t1", controller=1,
                         zone="PLAY", card_type="MINION",
                         tags={"COPIED_FROM_ENTITY_ID": 92}),
    }
    projection = state.public_decision_projection()
    assert {"54", "92"} <= set(projection["inert_setaside"])
    state.entities["99"].tags["LINKED_ENTITY"] = 92
    assert "92" in state.public_decision_projection()["active_setaside"]


def test_replaced_hero_power_requires_active_successor_and_matching_owner():
    state = LiveGameState()
    state.entities = {
        "59": EntityView("59", card_id="HERO_09ajhp", controller=1,
                         zone="SETASIDE", card_type="HERO_POWER",
                         zone_history=[(1, "PLAY"), (2, "SETASIDE")]),
        "108": EntityView("108", card_id="EDR_449p", controller=1,
                          zone="PLAY", card_type="HERO_POWER",
                          tags={"LINKED_ENTITY": 59}),
    }
    assert _retired_linked_hero_powers(state) == {"59"}
    state.entities["108"].controller = 2
    assert not _retired_linked_hero_powers(state)
    state.entities["108"].controller = 1
    state.entities["59"].zone_history = [(2, "SETASIDE")]
    assert not _retired_linked_hero_powers(state)


def test_staged_hero_is_ignored_only_when_unplayed_unlinked_and_not_choice():
    state = LiveGameState()
    staged = EntityView("96", card_id="CATA_190h", controller=2,
                        zone="SETASIDE", card_type="HERO",
                        zone_history=[(1, "SETASIDE")])
    state.entities["96"] = staged
    assert _unplayed_unlinked_setaside_heroes(state, ()) == {"96"}
    assert not _unplayed_unlinked_setaside_heroes(state, (96,))
    state.entities["99"] = EntityView("99", card_id="SOURCE", controller=2,
                                      zone="PLAY", card_type="MINION",
                                      references={96})
    assert not _unplayed_unlinked_setaside_heroes(state, ())
    state.entities.pop("99")
    staged.zone_history.insert(0, (0, "PLAY"))
    assert not _unplayed_unlinked_setaside_heroes(state, ())


def test_weapon_health_minus_damage_is_public_remaining_durability():
    weapon = EntityView("85", card_id="CS2_082", controller=2, zone="PLAY",
                        card_type="WEAPON", attack=1, health=2, damage=1)
    assert _public_remaining_durability(weapon) == 1
    weapon.tags["DURABILITY"] = "2"
    assert _public_remaining_durability(weapon) == 2
    weapon.tags["DURABILITY"] = "invalid"
    assert _public_remaining_durability(weapon) is None
    weapon.tags.clear()
    weapon.health = None
    assert _public_remaining_durability(weapon) is None
    location = EntityView("56", card_id="CATA_527", controller=2,
                          zone="PLAY", card_type="LOCATION", health=5, damage=3)
    assert _public_remaining_durability(location) == 2


def test_visible_weapon_is_hydrated_as_equipment_not_board_minion():
    def full(entity_id, card_id, **tags):
        return {"kind": "FullEntity", "entity": entity_id, "card_id": card_id,
                "tags": [{"tag": name, "value": value} for name, value in tags.items()]}

    state = reconstruct_game({"preamble": [
        full(1, "HERO_01", CONTROLLER=1, ZONE="PLAY", CARDTYPE="HERO",
             HEALTH=30, DAMAGE=0),
        full(2, "HERO_03", CONTROLLER=2, ZONE="PLAY", CARDTYPE="HERO",
             HEALTH=30, DAMAGE=0),
        full(3, "GAME_005", CARDTYPE="GAME", TURN=3, CURRENT_PLAYER=1),
        full(4, "PLAYER_01", CONTROLLER=1, CARDTYPE="PLAYER",
             RESOURCES=3, MAXRESOURCES=3),
        full(5, "PLAYER_02", CONTROLLER=2, CARDTYPE="PLAYER",
             RESOURCES=3, MAXRESOURCES=3),
        full(85, "CS2_082", CONTROLLER=2, ZONE="PLAY", CARDTYPE="WEAPON",
             ATK=1, HEALTH=2, DAMAGE=1),
    ], "blocks": []})
    result = build_snapshot_hypothesis(
        cards_path=Path(__file__).parents[1] / "cards.251332.enUS.json",
        state=state, own_deck={"CORE_BT_035": 30},
        opponent_deck={"CORE_BT_035": 30},
        player_classes=("WARRIOR", "ROGUE"), self_controller=1,
        setaside_policy="advisory")
    assert result.available, (result.reason, result.public_match)
    assert result.game.players[1].weapon.durability == 1
    assert not result.game.players[1].board
    state.entities["55"] = EntityView(
        "55", card_id="CATA_584", controller=1, zone="PLAY",
        card_type="LOCATION", health=3, damage=1,
        tags={"EXHAUSTED": 1, "LOCATION_ACTION_COOLDOWN": 0})
    with_location = build_snapshot_hypothesis(
        cards_path=Path(__file__).parents[1] / "cards.251332.enUS.json",
        state=state, own_deck={"CORE_BT_035": 30},
        opponent_deck={"CORE_BT_035": 30},
        player_classes=("WARRIOR", "ROGUE"), self_controller=1,
        setaside_policy="advisory")
    assert with_location.available, (with_location.reason, with_location.public_match)
    assert with_location.game.players[0].locations[0].durability == 2
    assert with_location.game.players[0].locations[0].cooldown == 0
    assert not with_location.game.players[0].board
    state.entities["5"].tags["CORPSES"] = 12
    state.entities["191"] = EntityView(
        "191", card_id="TIME_618t", controller=2,
        zone="SETASIDE", card_type="SPELL")
    state.entities["192"] = EntityView(
        "192", card_id="TIME_618e", controller=2,
        zone="PLAY", card_type="ENCHANTMENT",
        tags={"ATTACHED": 5, "TAG_SCRIPT_DATA_NUM_1": 191})
    with_rebirth = build_snapshot_hypothesis(
        cards_path=Path(__file__).parents[1] / "cards.251332.enUS.json",
        state=state, own_deck={"CORE_BT_035": 30},
        opponent_deck={"CORE_BT_035": 30},
        player_classes=("WARRIOR", "ROGUE"), self_controller=1,
        setaside_policy="advisory")
    assert with_rebirth.available, (with_rebirth.reason, with_rebirth.public_match)
    assert with_rebirth.game.players[1].corpse_rebirth_pending
    assert with_rebirth.game.players[1].corpses == 12
    state.entities["5"].tags.pop("CORPSES")
    missing_corpses = build_snapshot_hypothesis(
        cards_path=Path(__file__).parents[1] / "cards.251332.enUS.json",
        state=state, own_deck={"CORE_BT_035": 30},
        opponent_deck={"CORE_BT_035": 30},
        player_classes=("WARRIOR", "ROGUE"), self_controller=1,
        setaside_policy="advisory")
    assert missing_corpses.reason == "unsupported live zone: SETASIDE"


def test_play_block_from_location_already_in_play_records_activation():
    state = LiveGameState()
    state.entities["47"] = EntityView("47", card_id="CORE_REV_990",
                                       controller=2, zone="PLAY", card_type="LOCATION")
    state._apply_block_metadata({"block_type": "PLAY", "source_entity": 47,
                                 "source_card": "CORE_REV_990", "target_entity": 72})
    assert state.action_history[-1]["kind"] == "LOCATION"
    state.entities["48"] = EntityView("48", card_id="CORE_REV_990",
                                       controller=2, zone="HAND", card_type="LOCATION")
    state._apply_block_metadata({"block_type": "PLAY", "source_entity": 48,
                                 "source_card": "CORE_REV_990"})
    assert state.action_history[-1]["kind"] == "PLAY"


def test_resolved_choice_rejects_unselected_setaside_weapon_options():
    state = LiveGameState()
    for entity_id in (178, 179, 180, 181):
        state.entities[str(entity_id)] = EntityView(
            str(entity_id), card_id=f"JAIL_458t{entity_id - 177}",
            controller=2, zone="SETASIDE", card_type="WEAPON")
    state.apply_row({"kind": "Choices", "id": 10,
                     "choices": [178, 179, 180, 181]})
    assert "178" in state.public_decision_projection()["active_setaside"]
    state.apply_row({"kind": "ChosenEntities", "id": 10, "choices": [181]})
    projection = state.public_decision_projection()
    assert {"178", "179", "180"} <= set(projection["inert_setaside"])
    assert "181" in projection["active_setaside"]
    # A later live reference still takes precedence over the resolved-choice
    # provenance; it cannot be silently discarded as historical debris.
    state.entities["200"] = EntityView(
        "200", controller=2, zone="PLAY", card_type="MINION",
        tags={"LINKED_ENTITY": 178})
    assert "178" in state.public_decision_projection()["active_setaside"]


def test_replaced_hero_uses_active_armor_and_archives_old_power():
    state = LiveGameState()
    state.entities = {
        "30": EntityView("30", card_id="CATA_190h", controller=1,
                         zone="PLAY", card_type="HERO", health=30,
                         damage=5, tags={"ARMOR": 12, "LINKED_ENTITY": 64}),
        "207": EntityView("207", card_id="CATA_190p", controller=1,
                          zone="PLAY", card_type="HERO_POWER",
                          tags={"CREATOR": 30}),
        # Old hero comes later in insertion order, as in the observed log.
        "64": EntityView("64", card_id="HERO_03cd", controller=1,
                         zone="SETASIDE", card_type="HERO", health=30,
                         tags={"ARMOR": 0},
                         zone_history=[(1, "PLAY"), (2, "SETASIDE")]),
        "65": EntityView("65", card_id="HERO_03dbp", controller=1,
                         zone="SETASIDE", card_type="HERO_POWER",
                         tags={"CREATOR": 64},
                         zone_history=[(1, "PLAY"), (2, "SETASIDE")]),
    }
    assert state.visible()["player_meta"]["1"]["armor"] == 12
    assert state.visible()["player_meta"]["1"]["health"] == 25
    class Game:
        card_defs = {"CATA_190p": object()}
    assert _retired_deathwing_hero_entities(state, Game()) == {"64", "65"}


def test_public_attack_counter_not_double_counted_from_history():
    state = LiveGameState()
    state.turn = 7
    state.active_player = 1
    state.entities = {
        "1": EntityView("1", card_id="HERO_01n", controller=1,
                        zone="PLAY", card_type="HERO", health=30, attack=3,
                        tags={"NUM_ATTACKS_THIS_TURN": 0}),
        "2": EntityView("2", card_id="HERO_03cd", controller=2,
                        zone="PLAY", card_type="HERO", health=30),
    }
    # A prior attack block may appear in the same log turn even when a card
    # effect has subsequently reset the public attack counter to zero.
    state.action_history.append({"kind": "ATTACK", "source_entity": 1,
                                 "controller": 1, "turn": 7})
    result = build_snapshot_hypothesis(
        cards_path=Path(__file__).parents[1] / "cards.251332.enUS.json",
        state=state, own_deck={"CORE_BT_035": 30},
        opponent_deck={"CORE_BT_035": 30},
        player_classes=("WARRIOR", "ROGUE"), self_controller=1,
        setaside_policy="advisory")
    assert result.available, (result.reason, result.public_match)
    assert result.game.players[0].hero_attacks_this_turn == 0
    assert any(action.kind == "HERO_ATTACK"
               for action in result.game.legal_actions())

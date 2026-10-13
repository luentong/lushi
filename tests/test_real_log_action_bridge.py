import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_real_log_action_bridge import (ordered_packets,
                                          initial_public_classes,
                                          target_publicly_resolved,
                                          target_resolved_for_action)
from hsa.live_state import EntityView


def test_opening_hero_class_comes_before_later_hero_transform():
    def hero(packet_id, card, controller, card_class):
        return {"kind": "FullEntity", "packet_id": packet_id, "card_id": card,
                "tags": [{"tag": "CARDTYPE", "value": "HERO"},
                         {"tag": "ZONE", "value": "PLAY"},
                         {"tag": "CONTROLLER", "value": controller},
                         {"tag": "CLASS", "value": card_class}]}
    game = {"preamble": [hero(100, "TRANSFORM", 1, "WARRIOR"),
                         hero(2, "START_2", 2, "DRUID"),
                         hero(1, "START_1", 1, "PRIEST")], "blocks": []}
    assert initial_public_classes(game) == {1: "PRIEST", 2: "DRUID"}


def test_completed_log_does_not_move_final_preamble_state_before_first_action():
    game = {"preamble": [
        {"packet_id": 1, "kind": "TagChange", "entity": 1, "tag": "STEP", "value": "MAIN_ACTION"},
        {"packet_id": 99, "kind": "TagChange", "entity": 1, "tag": "STEP", "value": "FINAL_GAMEOVER"},
    ], "blocks": [{"packet_id": 10, "block_type": "PLAY", "effects": [
        {"packet_id": 11, "kind": "TagChange", "entity": 2, "tag": "ZONE", "value": "PLAY"},
    ]}]}
    packets = ordered_packets(game)
    assert [item[0] for item in packets] == [1, 10, 11, 99]
    assert packets[1][2] == "block"


def test_sparse_target_is_unknown_not_a_proven_illegal_action():
    sparse = EntityView("105", card_id="CATA_525t")
    assert not target_publicly_resolved(sparse)
    resolved = EntityView("105", card_id="CATA_525t", controller=2,
                          zone="PLAY", card_type="MINION")
    assert target_publicly_resolved(resolved)


def test_location_target_still_in_deck_is_observation_gap():
    location = EntityView("47", card_id="CORE_REV_990", controller=2,
                          zone="PLAY", card_type="LOCATION")
    target = EntityView("72", card_id="JAIL_421", controller=2,
                        zone="DECK", card_type="MINION")
    assert target_publicly_resolved(target)
    assert not target_resolved_for_action("PLAY", location, target)
    assert not target_resolved_for_action("ATTACK", None, target)
    # Other card effects can legitimately target hand cards.
    target.zone = "HAND"
    assert target_resolved_for_action("PLAY", None, target)

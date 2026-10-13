from hsa.real_log_decisions import (audit_client_end_turn_options,
                                    audit_client_selected_options,
                                    extract_causal_decision_records,
                                    infer_observer_controller)


def _entity(packet_id, entity, card_id, controller, zone):
    return {"kind": "FullEntity", "packet_id": packet_id,
            "entity": entity, "card_id": card_id,
            "tags": [{"tag": "CONTROLLER", "value": controller},
                     {"tag": "ZONE", "value": zone},
                     {"tag": "CARDTYPE", "value": "MINION"}]}


def _public_opening():
    return [
        {"kind": "FullEntity", "packet_id": -4, "entity": 1,
         "tags": [{"tag": "CARDTYPE", "value": "GAME"},
                  {"tag": "TURN", "value": 1},
                  {"tag": "CURRENT_PLAYER", "value": 1}]},
        {"kind": "FullEntity", "packet_id": -3, "entity": 2,
         "tags": [{"tag": "CARDTYPE", "value": "PLAYER"},
                  {"tag": "CONTROLLER", "value": 1},
                  {"tag": "RESOURCES", "value": 1},
                  {"tag": "MAXRESOURCES", "value": 1}]},
        {"kind": "FullEntity", "packet_id": -2, "entity": 3,
         "tags": [{"tag": "CARDTYPE", "value": "PLAYER"},
                  {"tag": "CONTROLLER", "value": 2},
                  {"tag": "RESOURCES", "value": 1},
                  {"tag": "MAXRESOURCES", "value": 1}]},
        {"kind": "FullEntity", "packet_id": -1, "entity": 4,
         "card_id": "HERO_01", "tags": [
             {"tag": "CARDTYPE", "value": "HERO"},
             {"tag": "CONTROLLER", "value": 1},
             {"tag": "ZONE", "value": "PLAY"},
             {"tag": "HEALTH", "value": 30}]},
    ]


def test_hidden_opponent_card_never_enters_its_pre_action_snapshot():
    game = {"identity_timing": "causal_reveal_only", "preamble": _public_opening() + [
        _entity(1, 10, "KNOWN_OWN", 1, "HAND"),
        _entity(2, 20, None, 2, "HAND"),
    ], "blocks": [
        {"packet_id": 3, "block_type": "PLAY", "source_entity": 10,
         "source_card": "KNOWN_OWN", "effects": [
             {"packet_id": 4, "kind": "TagChange", "entity": 10,
              "tag": "ZONE", "value": "PLAY"}]},
        {"packet_id": 5, "block_type": "PLAY", "source_entity": 20,
         "source_card": None, "effects": [
             {"packet_id": 6, "kind": "ShowEntity", "entity": 20,
              "card_id": "LATER_REVEAL", "tags": [
                  {"tag": "CONTROLLER", "value": 2},
                  {"tag": "ZONE", "value": "PLAY"}]}]},
    ]}
    records = extract_causal_decision_records(game, local_controller=1)
    assert len(records) == 2
    assert records[0]["causal_observation_candidate"]
    assert records[0]["public_transition_audit"]["status"] == "public_transition_consistent"
    assert not records[0]["training_authorized"]
    assert records[0]["observed_until_next_decision"] == records[1]["pre_action_public_state"]
    assert records[1]["action"]["source_card_before_action"] is None
    assert "opponent_hidden_information" in records[1]["blockers"]
    assert "source_card_not_known_before_action" in records[1]["blockers"]
    assert "LATER_REVEAL" not in str(records[1]["pre_action_public_state"])
    assert "LATER_REVEAL" in str(records[1]["observed_until_next_decision"])


def test_legacy_import_cannot_be_promoted_to_causal_candidate():
    game = {"preamble": _public_opening() + [_entity(1, 10, "CARD_A", 1, "HAND")],
            "blocks": [{"packet_id": 2, "block_type": "PLAY",
                        "source_entity": 10, "source_card": "CARD_A"}]}
    records = extract_causal_decision_records(game, local_controller=1)
    assert records[0]["blockers"] == ["legacy_import_may_backfill_identity"]
    assert not records[0]["training_authorized"]


def test_power_effect_block_does_not_become_a_second_action():
    game = {"identity_timing": "causal_reveal_only",
            "preamble": _public_opening() + [_entity(1, 10, "CARD_A", 1, "HAND")],
            "blocks": [
                {"packet_id": 2, "block_type": "PLAY", "source_entity": 10,
                 "source_card": "CARD_A"},
                {"packet_id": 3, "block_type": "POWER", "source_entity": 10,
                 "source_card": "CARD_A"},
            ]}
    assert len(extract_causal_decision_records(game, local_controller=1)) == 1


def test_public_transition_flags_attack_source_outside_play():
    game = {"identity_timing": "causal_reveal_only",
            "preamble": _public_opening() + [_entity(1, 10, "CARD_A", 1, "HAND")],
            "blocks": [{"packet_id": 2, "block_type": "ATTACK",
                        "source_entity": 10, "source_card": "CARD_A"}]}
    record = extract_causal_decision_records(game, local_controller=1)[0]
    assert "attack_source_not_active_hero_or_minion" in (
        record["public_transition_audit"]["blockers"])
    assert not record["public_transition_audit"]["rule_legality_verified"]


def test_observer_inference_uses_only_preplay_hand_reveals():
    game = {"preamble": [
        _entity(1, 10, "OWN_A", 1, "HAND"),
        _entity(2, 11, "OWN_B", 1, "HAND"),
        _entity(3, 12, "OWN_C", 1, "HAND"),
        _entity(4, 20, None, 2, "HAND"),
        # This later reveal cannot be treated as opening-hand visibility.
        _entity(20, 20, "LATER", 2, "HAND"),
    ], "blocks": [{"packet_id": 10, "block_type": "PLAY"}]}
    evidence = infer_observer_controller(game)
    assert evidence["controller"] == 1
    assert evidence["known_opening_hand"] == {"1": 3, "2": 0}


def test_public_transition_detects_observed_unaffordable_play():
    game = {"identity_timing": "causal_reveal_only",
            "preamble": _public_opening() + [{
                **_entity(1, 10, "CARD_A", 1, "HAND"),
                "tags": _entity(1, 10, "CARD_A", 1, "HAND")["tags"]
                + [{"tag": "COST", "value": 3}],
            }],
            "blocks": [{"packet_id": 2, "block_type": "PLAY",
                        "source_entity": 10, "source_card": "CARD_A"}]}
    record = extract_causal_decision_records(game, local_controller=1)[0]
    audit = record["public_transition_audit"]
    assert audit["mana_cost_check"] == "observed_cost_exceeds_mana"
    assert "observed_cost_exceeds_available_mana" in audit["blockers"]


def test_client_confirmed_deck_action_is_trade_not_bookkeeping():
    game = {"identity_timing": "causal_reveal_only",
            "preamble": _public_opening() + [
                _entity(1, 10, "TRADEABLE_CARD", 1, "HAND"),
                {"packet_id": 2, "ts": "12:00:00.100", "kind": "Options",
                 "id": 7, "options": [{"id": 3, "entity": 10,
                                        "error": None}]},
                {"packet_id": 3, "ts": "12:00:00.200", "kind": "SendOption",
                 "option": 3, "target": 0},
            ], "blocks": [
                {"packet_id": 4, "block_type": "DECK_ACTION",
                 "source_entity": 10, "source_card": "TRADEABLE_CARD",
                 "effects": [{"packet_id": 5, "kind": "TagChange",
                              "entity": 10, "tag": "ZONE", "value": "DECK"}]},
            ]}
    options = audit_client_selected_options(game)
    assert len(options) == 1 and options[0]["client_option_legal"]
    records = extract_causal_decision_records(game, local_controller=1)
    assert len(records) == 1
    assert records[0]["action"]["kind"] == "TRADE"
    assert records[0]["client_option_confirmed"]
    assert records[0]["public_transition_audit"]["status"] == "public_transition_consistent"


def test_client_target_must_be_offered_and_legal_even_when_block_matches():
    game = {"preamble": [
        {"packet_id": 1, "ts": "12:00:00.100", "kind": "Options",
         "id": 7, "options": [{
             "id": 3, "entity": 10, "error": None,
             "options": [{"id": 0, "entity": 20, "error": None},
                         {"id": 1, "entity": 21, "error": "REQ_ENEMY_TARGET"}],
         }]},
        {"packet_id": 2, "ts": "12:00:00.200", "kind": "SendOption",
         "option": 3, "target": 20},
    ], "blocks": [{"packet_id": 3, "block_type": "PLAY",
                   "source_entity": 10, "target_entity": 20}]}
    assert audit_client_selected_options(game)[0]["client_option_legal"]

    game["preamble"][1]["target"] = 21
    game["blocks"][0]["target_entity"] = 21
    rejected = audit_client_selected_options(game)[0]
    assert not rejected["target_option_legal"]
    assert not rejected["client_option_legal"]
    assert rejected["reason"] == "target_not_confirmed_in_client_options"

    game["preamble"][1]["target"] = 22
    game["blocks"][0]["target_entity"] = 22
    assert not audit_client_selected_options(game)[0]["client_option_legal"]


def test_unconfirmed_deck_action_is_not_treated_as_player_decision():
    game = {"identity_timing": "causal_reveal_only",
            "preamble": _public_opening() + [_entity(1, 10, "CARD", 1, "HAND")],
            "blocks": [{"packet_id": 2, "block_type": "DECK_ACTION",
                        "source_entity": 10, "source_card": "CARD"}]}
    assert extract_causal_decision_records(game, local_controller=1) == []


def test_end_turn_requires_accepted_main_end_packet():
    game = {"identity_timing": "causal_reveal_only",
            "preamble": _public_opening() + [
                {"packet_id": 1, "kind": "SendOption", "option": 0,
                 "target": 0},
                {"packet_id": 2, "kind": "TagChange", "entity": 1,
                 "tag": "STEP", "value": "MAIN_END"},
            ], "blocks": []}
    assert 1 in audit_client_end_turn_options(game)
    records = extract_causal_decision_records(game, local_controller=1)
    assert len(records) == 1
    assert records[0]["action"]["kind"] == "TURN_END"
    assert records[0]["client_option_confirmed"]
    assert records[0]["causal_observation_candidate"]
    assert records[0]["public_transition_audit"]["status"] == "public_transition_consistent"
    game["preamble"].insert(-1, {"packet_id": 2, "kind": "TagChange",
                                  "entity": 1, "tag": 1196, "value": 0})
    game["preamble"][-1]["packet_id"] = 3
    assert 1 in audit_client_end_turn_options(game)
    game["preamble"][-1]["value"] = "MAIN_ACTION"
    assert not audit_client_end_turn_options(game)
    assert extract_causal_decision_records(game, local_controller=1) == []

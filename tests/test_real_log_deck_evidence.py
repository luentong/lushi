from hsa.real_log_deck_evidence import collect_deck_evidence


def opening(entity, owner=1):
    return {"kind": "FullEntity", "packet_id": entity, "entity": entity,
            "tags": [{"tag": "ZONE", "value": "DECK"},
                     {"tag": "CONTROLLER", "value": owner}]}


def reveal(packet, entity, card, **changes):
    return {"kind": "ShowEntity", "packet_id": packet, "entity": entity,
            "card_id": card, **changes}


def game(effects):
    return {"identity_timing": "causal_reveal_only",
            "preamble": [opening(1), opening(2), opening(3, 2)],
            "blocks": [{"packet_id": 10, "block_type": "TRIGGER", "effects": effects}]}


def test_original_entity_reveal_is_causal_and_only_counts_once():
    source = game([reveal(11, 1, "A"), reveal(12, 1, "A"), reveal(15, 2, "A")])
    before = collect_deck_evidence(source, {"A"}, before_packet=11)
    assert before["controllers"]["1"]["observed_counts"] == {}
    between = collect_deck_evidence(source, {"A"}, before_packet=15)
    assert between["controllers"]["1"]["observed_counts"] == {"A": 1}
    after = collect_deck_evidence(source, {"A"})
    assert after["controllers"]["1"]["observed_counts"] == {"A": 2}
    assert not after["complete_deck_identified"]


def test_generated_entities_and_transformed_hidden_slots_are_excluded():
    source = game([
        reveal(11, 1, "B", kind="ChangeEntity"),
        reveal(12, 1, "B"),
        reveal(13, 2, "A", tags=[{"tag": "CREATOR", "value": 90}]),
        reveal(14, 100, "A", kind="FullEntity"),
        reveal(15, 3, "HERO"),
    ])
    result = collect_deck_evidence(source, {"A", "B"})
    assert result["observations"] == []
    assert result["controllers"]["1"]["excluded_reasons"] == {
        "transformed_before_identity_reveal": 1,
        "created_or_copied_before_identity_reveal": 1,
    }


def test_later_transform_and_controller_change_preserve_original_evidence():
    source = game([
        reveal(11, 1, "A"),
        reveal(12, 1, "B", kind="ChangeEntity"),
        {"packet_id": 13, "entity": 3, "kind": "TagChange",
         "tag": "CONTROLLER", "value": 1},
        reveal(14, 3, "C"),
    ])
    result = collect_deck_evidence(source, {"A", "B", "C"})
    assert result["controllers"]["1"]["observed_counts"] == {"A": 1}
    assert result["controllers"]["2"]["observed_counts"] == {"C": 1}


def test_explicitly_eligible_companions_can_complete_the_opening_list():
    source = game([reveal(11, 1, "FABLED"), reveal(12, 2, "COMPANION")])
    result = collect_deck_evidence(source, {"FABLED", "COMPANION"})
    assert result["controllers"]["1"]["all_opening_slots_identified"]
    assert result["controllers"]["1"]["observed_counts"] == {
        "FABLED": 1, "COMPANION": 1}
    assert not result["controllers"]["2"]["all_opening_slots_identified"]


def test_reset_stops_new_evidence_and_legacy_import_is_rejected():
    source = game([reveal(11, 1, "A")])
    source["blocks"].append({"packet_id": 20, "block_type": "GAME_RESET",
                             "effects": [reveal(21, 2, "B")]})
    result = collect_deck_evidence(source, {"A", "B"})
    assert result["controllers"]["1"]["observed_counts"] == {"A": 1}
    assert result["reset_boundary"] == 20
    source.pop("identity_timing")
    try:
        collect_deck_evidence(source, {"A"})
    except ValueError:
        pass
    else:
        raise AssertionError("legacy imports must not provide deck evidence")

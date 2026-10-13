"""Top-level Power.log packets must not leak into earlier live actions."""

from hsa.live_state import LiveStateCursor, reconstruct_game, timeline_snapshots


def _game(include_late_row: bool):
    preamble = [
        {"kind": "FullEntity", "packet_id": 1, "entity": 1,
         "card_id": "GAME", "tags": [
             {"tag": "CARDTYPE", "value": "GAME"},
             {"tag": "TURN", "value": 1}]},
        {"kind": "FullEntity", "packet_id": 2, "entity": 7,
         "card_id": "CORE_BT_035", "tags": [
             {"tag": "CONTROLLER", "value": 1},
             {"tag": "ZONE", "value": "PLAY"},
             {"tag": "CARDTYPE", "value": "MINION"},
             {"tag": "HEALTH", "value": 4}]},
    ]
    if include_late_row:
        preamble.extend([
            {"kind": "TagChange", "packet_id": 30, "entity": 1,
             "tag": "TURN", "value": 2},
            {"kind": "TagChange", "packet_id": 31, "entity": 7,
             "tag": "DAMAGE", "value": 3},
        ])
    return {"preamble": preamble, "blocks": [{
        "packet_id": 20, "block_type": "PLAY", "source_entity": 7,
        "source_card": "CORE_BT_035", "effects": [
            {"kind": "TagChange", "packet_id": 21, "entity": 7,
             "tag": "DAMAGE", "value": 1},
        ]}]}


def test_reconstruction_preserves_action_turn_before_late_top_level_row():
    state = reconstruct_game(_game(True))
    assert state.turn == 2 and state.entities["7"].damage == 3
    assert state.action_history[0]["turn"] == 1


def test_incremental_cursor_applies_late_row_once():
    cursor = LiveStateCursor()
    first = cursor.apply_game(_game(False))
    assert first.turn == 1 and first.entities["7"].damage == 1
    assert len(first.action_history) == 1
    second = cursor.apply_game(_game(True))
    assert second.turn == 2 and second.entities["7"].damage == 3
    assert second.action_history[0]["turn"] == 1
    cursor.apply_game(_game(True))
    assert len(cursor.state.action_history) == 1


def test_block_snapshot_does_not_contain_future_top_level_damage():
    game = _game(True)
    game["blocks"][0]["effects"] = []
    snapshots = timeline_snapshots(game)
    assert snapshots[0]["players"]["1"]["PLAY"][0]["damage"] == 0


def test_total_mana_falls_back_to_observed_resources():
    game = {"preamble": [{"kind": "FullEntity", "packet_id": 1,
                          "entity": 2, "tags": [
                              {"tag": "CARDTYPE", "value": "PLAYER"},
                              {"tag": "CONTROLLER", "value": 1},
                              {"tag": "RESOURCES", "value": 4},
                              {"tag": "RESOURCES_USED", "value": 1},
                          ]}], "blocks": []}
    meta = reconstruct_game(game).visible()["player_meta"]["1"]
    assert meta["mana"] == 3
    assert meta["max_mana"] == 4

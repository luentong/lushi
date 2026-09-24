from __future__ import annotations

from pathlib import Path

from hsa.live_adapter import PowerLogStateAdapter
from hsa.live_state import EntityView, reconstruct_game, timeline_snapshots
from hsa.live_replay import (build_simulator_action_plan,
                              extract_replay_events, make_replay_cursor,
                              match_entity_candidates, action_from_plan)
from hsa.live_compare import compare_public_state
from hsa.live_executor import execute_plans
from hsa.live_session import check_initial_decks
from hsa.belief_state import build_beliefs, filter_candidates
from hsa.recommendation_gate import evaluate_gate
from hsa.belief_consensus import choose_consensus
from hsa.powerlog_watcher import PowerLogTailer
from hsa.live_bridge import build_snapshot_hypothesis
from hsa.live_recommendation import recommend_puct_state
from hsa.policy_value import HeuristicPolicyValueModel


def test_powerlog_tailer_handles_partial_line_and_append(tmp_path: Path):
    path = tmp_path / "Power.log"
    path.write_bytes(b"FULL_ENTITY - Creating ID=12 CardID=CS2_172\nTAG_CHANGE Entity=12 tag=ATK")
    tailer = PowerLogTailer(path, from_end=False)
    first = tailer.poll()
    assert [line.text for line in first] == ["FULL_ENTITY - Creating ID=12 CardID=CS2_172"]
    with path.open("ab") as handle:
        handle.write(b" value=3\n")
    second = tailer.poll()
    assert [line.text for line in second] == ["TAG_CHANGE Entity=12 tag=ATK value=3"]


def test_live_adapter_tracks_entities_tags_and_gate():
    adapter = PowerLogStateAdapter()
    adapter.consume("FULL_ENTITY - Creating ID=12 CardID=CS2_172")
    snapshot = adapter.consume("TAG_CHANGE Entity=12 tag=ATK value=3")
    assert snapshot.entities["12"] == "CS2_172"
    assert snapshot.tags["12"]["ATK"] == "3"
    assert snapshot.confidence == "amber"
    snapshot = adapter.consume("UNKNOWN_EFFECT card=NEW_CARD")
    assert snapshot.confidence == "red"


def test_live_state_reconstructs_public_zone_and_stats():
    state = reconstruct_game({
        "preamble": [{"kind": "FullEntity", "entity": 7, "card_id": "CORE_BT_035",
                       "tags": [{"tag": "CONTROLLER", "value": 1},
                                {"tag": "ZONE", "value": "PLAY"},
                                {"tag": "ATK", "value": 3},
                                {"tag": "HEALTH", "value": 4}]}],
        "blocks": [{"block_type": "PLAY", "source_entity": 7, "source_card": "CORE_BT_035",
                    "effects": [{"kind": "TagChange", "entity": 7,
                                 "tag": "DAMAGE", "value": 1}]}],
    })
    card = state.entities["7"]
    assert card.zone == "PLAY" and card.controller == 1
    assert card.attack == 3 and card.health == 4 and card.damage == 1
    assert state.visible()["players"]["1"]["PLAY"][0]["card_id"] == "CORE_BT_035"


def test_live_state_retains_action_timeline_and_fatigue():
    state = reconstruct_game({
        "preamble": [],
        "blocks": [
            {"block_type": "TURN_START", "turn": 3, "player": 1},
            {"block_type": "ATTACK", "controller": 1,
             "source_entity": 12, "source_card": "CS2_172",
             "target_entity": 1, "target_card": "HERO_01"},
            {"block_type": "POWER", "controller": 1,
             "effects": [{"tag": "FATIGUE_DAMAGE", "controller": 1, "value": 2}]},
        ],
    })
    view = state.visible()
    assert view["turn"] == 3 and view["active_player"] == 1
    assert view["action_history"][0]["kind"] == "ATTACK"
    assert view["fatigue"]["1"] == 2


def test_replay_events_require_explicit_choice_resolution():
    open_result = extract_replay_events({"blocks": [{
        "packet_id": 1, "block_type": "DISCOVER",
        "effects": [{"kind": "Choices", "choices": [10, 11, 12]}],
    }]})
    assert not open_result.replayable and open_result.unresolved_choices == 1
    closed = extract_replay_events({"blocks": [{
        "packet_id": 2, "block_type": "DISCOVER",
        "effects": [{"kind": "Choices", "choices": [10, 11, 12]},
                    {"kind": "ChosenEntities", "entities": [11]}],
    }]})
    assert closed.event_stream_closed and not closed.replayable
    assert closed.events[0].chosen == (11,)


def test_replay_extracts_deck_hand_and_generated_entities():
    result = extract_replay_events({
        "preamble": [
            {"kind": "FullEntity", "entity": 1, "card_id": "A",
             "tags": [{"tag": "ZONE", "value": "DECK"}, {"tag": "CONTROLLER", "value": 1}]},
            {"kind": "FullEntity", "entity": 2, "card_id": "B",
             "tags": [{"tag": "ZONE", "value": "HAND"}, {"tag": "CONTROLLER", "value": 1},
                      {"tag": "CREATOR", "value": 99}]},
            {"kind": "FullEntity", "entity": 3, "card_id": "",
             "tags": [{"tag": "ZONE", "value": "DECK"}, {"tag": "CONTROLLER", "value": 1}]},
        ], "blocks": []})
    assert result.deck_counts == {"1": {"A": 1}}
    assert result.unknown_deck_slots == {"1": 1}
    assert result.hand_entities["1"][0]["card_id"] == "B"
    assert result.generated_entities[0]["creator"] == 99


def test_replay_reports_first_unmatched_transition():
    result = extract_replay_events({"blocks": [{
        "packet_id": 9, "block_type": "ATTACK", "source_entity": 42,
        "target_entity": 1,
    }]})
    assert result.transition_errors[0]["reason"] == "entity_not_seen_before_action"


def test_replay_cursor_consumes_events_in_order():
    diagnostics, cursor = make_replay_cursor({"blocks": [
        {"packet_id": 1, "block_type": "PLAY", "source_entity": 7,
         "source_card": "CARD_A"},
        {"packet_id": 2, "block_type": "ATTACK", "source_entity": 7,
         "target_entity": 9, "target_card": "HERO"},
    ]})
    assert diagnostics.event_stream_closed
    assert cursor.step().packet_id == 1
    assert cursor.entities[7]["card_id"] == "CARD_A"
    assert cursor.run_until() == 1 and cursor.done


def test_simulator_plan_marks_hidden_source_as_unmappable():
    diagnostics = extract_replay_events({"blocks": [
        {"packet_id": 1, "block_type": "PLAY", "source_entity": 7},
        {"packet_id": 2, "block_type": "TURN_END"},
    ]})
    plan = build_simulator_action_plan(diagnostics)
    assert not plan[0].mappable and plan[0].reason == "source card hidden"
    assert plan[1].mappable


def test_entity_mapping_requires_unique_candidate():
    mapper, unresolved = match_entity_candidates(
        [{"entity": 10, "controller": 1, "card_id": "A", "zone": "HAND"}],
        [{"entity": 20, "controller": 1, "card_id": "A", "zone": "HAND"}],
    )
    assert mapper.resolve(10) == 20 and not unresolved
    _, unresolved = match_entity_candidates(
        [{"entity": 10, "controller": 1, "card_id": "A", "zone": "HAND"}],
        [{"entity": 20, "controller": 1, "card_id": "A", "zone": "HAND"},
         {"entity": 21, "controller": 1, "card_id": "A", "zone": "HAND"}],
    )
    assert unresolved[0]["candidate_count"] == 2


def test_action_plan_converts_after_entity_binding():
    diagnostics = extract_replay_events({"blocks": [{
        "packet_id": 1, "block_type": "PLAY", "source_entity": 10,
        "source_card": "CARD_A",
    }]})
    plan = build_simulator_action_plan(diagnostics)[0]
    mapper, _ = match_entity_candidates(
        [{"entity": 10, "controller": 1, "card_id": "CARD_A", "zone": "HAND"}],
        [{"entity": 20, "controller": 1, "card_id": "CARD_A", "zone": "HAND"}],
    )
    action, error = action_from_plan(plan, mapper)
    assert error is None and action.kind == "PLAY" and action.source == 20


def test_public_state_comparison_fails_closed_on_board_mismatch():
    class Card:
        card_id, attack, health, damage = "CARD_A", 2, 3, 0
    class Player:
        def __init__(self, board):
            self.board, self.hand = board, []
    class Engine:
        players = [Player([Card()]), Player([])]
    visible = {"players": {"1": {"PLAY": [{"card_id": "CARD_A", "attack": 2,
                                               "health": 3, "damage": 0}], "HAND": []},
                             "2": {"PLAY": [], "HAND": []}}}
    assert compare_public_state(Engine(), visible).matches
    visible["players"]["1"]["PLAY"][0]["health"] = 4
    assert not compare_public_state(Engine(), visible).matches


def test_executor_stops_when_action_is_not_legal():
    class Game:
        def legal_actions(self):
            from hsa.dragon_mirror import Action
            return [Action("END_TURN")]
        def step(self, action):
            raise AssertionError("must not execute")
    diagnostics = extract_replay_events({"blocks": [{
        "packet_id": 1, "block_type": "PLAY", "source_entity": 10,
        "source_card": "CARD_A",
    }]})
    plans = build_simulator_action_plan(diagnostics)
    mapper, _ = match_entity_candidates(
        [{"entity": 10, "controller": 1, "card_id": "CARD_A", "zone": "HAND"}],
        [{"entity": 20, "controller": 1, "card_id": "CARD_A", "zone": "HAND"}],
    )
    report = execute_plans(Game(), plans, mapper)
    assert report.executed == 0 and report.stopped_at == 0


def test_session_gate_requires_complete_initial_decks():
    gate = check_initial_decks({"1": {"A": 30}, "2": {"B": 12}})
    assert not gate.ready and gate.missing_slots["2"] == 18
    assert check_initial_decks({"1": {"A": 30}, "2": {"B": 30}}).ready


def test_timeline_snapshots_follow_block_order():
    snapshots = timeline_snapshots({"preamble": [], "blocks": [
        {"packet_id": 1, "block_type": "PLAY", "effects": []},
        {"packet_id": 2, "block_type": "ATTACK", "effects": []},
    ]})
    assert [x["packet_id"] for x in snapshots] == [1, 2]
    assert snapshots[-1]["blocks_seen"] == 2


def test_opponent_belief_tracks_known_and_unknown_cards():
    beliefs = build_beliefs({"2": {"A": 2}}, {"2": 28})
    beliefs["2"].observe_played("X")
    assert beliefs["2"].summary()["unknown_slots"] == 28
    assert beliefs["2"].compatible()


def test_belief_filters_candidates_after_observation():
    beliefs = build_beliefs({"2": {}}, {"2": 30}, candidate_decks={
        "2": [{"A": 2}, {"B": 2}],
    })
    beliefs["2"].observe_played("A")
    assert len(filter_candidates(beliefs["2"])) == 1
    assert beliefs["2"].candidate_decks[0]["A"] == 2


def test_recommendation_gate_stays_closed_until_all_checks_pass():
    gate = evaluate_gate(event_stream_closed=True, session_ready=True,
                         beliefs={"2": {"compatible": True, "candidate_decks": [{"A": 2}]}},
                         state_matches=False)
    assert not gate["available"] and "simulator_state_not_verified" in gate["reasons"]


def test_belief_gate_allows_unknown_opponent_only_with_candidates():
    gate = evaluate_gate(event_stream_closed=True, session_ready=True,
                         beliefs={"2": {"compatible": True,
                                        "candidate_decks": [{"A": 2}]}},
                         mode="belief")
    assert not gate["available"] and gate["belief_mode_ready"]
    assert "belief_action_consensus_not_verified" in gate["reasons"]


def test_belief_consensus_requires_support_threshold():
    a = {"kind": "PLAY", "source": 1}
    b = {"kind": "END_TURN"}
    assert choose_consensus([a, a, a, b]).available
    assert not choose_consensus([a, b], min_support=0.75).available


def test_snapshot_bridge_hydrates_public_state_for_local_turn():
    state = reconstruct_game({"preamble": [
        {"kind": "FullEntity", "entity": 1, "card_id": "HERO_01",
         "tags": [{"tag": "CONTROLLER", "value": 1}, {"tag": "ZONE", "value": "PLAY"},
                  {"tag": "CARDTYPE", "value": "HERO"}, {"tag": "HEALTH", "value": 30},
                  {"tag": "DAMAGE", "value": 0}]},
        {"kind": "FullEntity", "entity": 2, "card_id": "HERO_08",
         "tags": [{"tag": "CONTROLLER", "value": 2}, {"tag": "ZONE", "value": "PLAY"},
                  {"tag": "CARDTYPE", "value": "HERO"}, {"tag": "HEALTH", "value": 30},
                  {"tag": "DAMAGE", "value": 0}]},
        {"kind": "FullEntity", "entity": 10, "card_id": "CORE_BT_035",
         "tags": [{"tag": "CONTROLLER", "value": 1}, {"tag": "ZONE", "value": "HAND"},
                  {"tag": "CARDTYPE", "value": "MINION"}, {"tag": "COST", "value": 1}]},
        {"kind": "FullEntity", "entity": 20, "card_id": "GAME_005",
         "tags": [{"tag": "CARDTYPE", "value": "GAME"}, {"tag": "TURN", "value": 3},
                  {"tag": "CURRENT_PLAYER", "value": 1}]},
        {"kind": "FullEntity", "entity": 30, "card_id": "PLAYER_01",
         "tags": [{"tag": "CONTROLLER", "value": 1}, {"tag": "CARDTYPE", "value": "PLAYER"},
                  {"tag": "RESOURCES", "value": 3}, {"tag": "MAXRESOURCES", "value": 3}]},
        {"kind": "FullEntity", "entity": 31, "card_id": "PLAYER_02",
         "tags": [{"tag": "CONTROLLER", "value": 2}, {"tag": "CARDTYPE", "value": "PLAYER"},
                  {"tag": "RESOURCES", "value": 3}, {"tag": "MAXRESOURCES", "value": 3}]},
    ], "blocks": []})
    cards = Path(__file__).parents[1] / "cards.251332.enUS.json"
    result = build_snapshot_hypothesis(
        cards_path=cards, state=state, own_deck={"CORE_BT_035": 30},
        opponent_deck={"CORE_BT_035": 30}, player_classes=("WARRIOR", "MAGE"),
    )
    assert result.available, result.reason
    assert result.mapper.resolve(10) == 10
    assert result.game._live_replay_verified
    recommendation = recommend_puct_state(
        result.game, "unused.pt", model=HeuristicPolicyValueModel(), iterations=2,
    )
    assert recommendation.available and recommendation.action is not None
    state.entities["11"] = EntityView("11", card_id="CORE_BT_035", controller=1,
                                       zone="SETASIDE", card_type="MINION")
    choice = build_snapshot_hypothesis(
        cards_path=cards, state=state, own_deck={"CORE_BT_035": 30},
        opponent_deck={"CORE_BT_035": 30}, player_classes=("WARRIOR", "MAGE"),
        open_choice_kind="DISCOVER", open_choice_entities=(11,),
    )
    assert choice.available, choice.reason
    assert choice.game.pending_choice["kind"] == "DISCOVER"
    assert choice.game.legal_actions()[0].kind == "DISCOVER_PICK"

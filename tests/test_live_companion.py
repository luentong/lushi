from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from hsa.live_adapter import PowerLogStateAdapter
from hsa.live_state import EntityView, LiveStateCursor, reconstruct_game, timeline_snapshots
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
from hsa.live_bridge import _executable_card_id, build_snapshot_hypothesis
from hsa.live_recommendation import recommend_puct_state
from hsa.policy_value import HeuristicPolicyValueModel


def test_candidate_class_filter_keeps_matching_decks_and_has_safe_fallback():
    from importlib.util import module_from_spec, spec_from_file_location
    script = Path(__file__).parents[1] / "scripts" / "live_recommender.py"
    spec = spec_from_file_location("live_recommender", script)
    module = module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    cards = {"W": "WARRIOR", "P": "PRIEST", "N": "NEUTRAL"}
    decks = [{"W": 2, "N": 28}, {"P": 2, "N": 28}]
    assert module.filter_candidates_for_class(decks, cards, "PRIEST") == [decks[1]]
    assert module.filter_candidates_for_class(decks, cards, "MAGE") == decks
    assert module.class_matched_candidates(decks, cards, "PRIEST") == ([decks[1]], True)
    assert module.class_matched_candidates(decks, cards, "MAGE") == ([], False)
    assert module.filter_complete_candidates([{"A": 20}, {"A": 30}]) == [{"A": 30}]


def test_local_controller_is_inferred_from_hand_visibility():
    from importlib.util import module_from_spec, spec_from_file_location
    script = Path(__file__).parents[1] / "scripts" / "live_recommender.py"
    spec = spec_from_file_location("live_recommender", script)
    module = module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    state = SimpleNamespace(entities={
        "1": EntityView("1", controller=1, zone="HAND"),
        "2": EntityView("2", controller=1, zone="HAND"),
        "3": EntityView("3", card_id="CORE_EX1_409", controller=2, zone="HAND"),
        "4": EntityView("4", card_id="CORE_EX1_409", controller=2, zone="HAND"),
    })
    assert module.infer_local_controller(state) == 2
    state.entities["1"].card_id = "CORE_EX1_409"
    state.entities["2"].card_id = "CORE_EX1_409"
    assert module.infer_local_controller(state) is None
    heroes = SimpleNamespace(entities={
        "10": EntityView("10", card_id="HERO_01", controller=1, zone="PLAY", card_type="HERO"),
        "11": EntityView("11", card_id="HERO_09", controller=2, zone="PLAY", card_type="HERO"),
    })
    assert module.infer_player_classes(
        heroes, {"HERO_01": "WARRIOR", "HERO_09": "PRIEST"}
    ) == {1: "WARRIOR", 2: "PRIEST"}
    discover_event = SimpleNamespace(
        choice_type="GENERAL", kind="POWER", source_card="CAP_105", choices=(10, 11, 12),
    )
    discover_state = SimpleNamespace(entities={
        "10": EntityView("10", tags={"WAS_DISCOVER_OPTION": 1}),
    })
    assert module.normalise_open_choice_kind(
        discover_event, discover_state, {"CAP_105": "Discover a Pirate."}
    ) == "DISCOVER"
    banner = module.format_recommendation_banner(
        {"description": "Play Coin", "hypothesis_support": 1.0, "hypotheses": 7},
        {"turn": 2},
    )
    assert "Recommended action: Play Coin" in banner
    assert "Candidate agreement: 100% (7 hypotheses)" in banner


def test_belief_observes_only_non_generated_deck_plays():
    from importlib.util import module_from_spec, spec_from_file_location
    script = Path(__file__).parents[1] / "scripts" / "live_recommender.py"
    spec = spec_from_file_location("live_recommender", script)
    module = module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    state = SimpleNamespace(entities={
        "10": EntityView("10", card_id="CORE_BT_035", controller=1,
                           zone="PLAY", card_type="MINION"),
        "11": EntityView("11", card_id="GAME_005", controller=1,
                           zone="PLAY", card_type="SPELL", tags={"CREATOR": 1}),
        "12": EntityView("12", card_id="HERO_01bp", controller=1,
                           zone="PLAY", card_type="HERO_POWER"),
    }, entity_registry={})
    assert module.is_observable_deck_play({"kind": "PLAY", "source_entity": 10}, state)
    assert not module.is_observable_deck_play({"kind": "POWER", "source_entity": 10}, state)
    assert not module.is_observable_deck_play({"kind": "PLAY", "source_entity": 11}, state)
    assert not module.is_observable_deck_play({"kind": "PLAY", "source_entity": 12}, state)


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


def test_powerlog_tailer_can_start_at_latest_create_game(tmp_path: Path):
    path = tmp_path / "Power.log"
    path.write_bytes(
        b"old game\n"
        b"D 00:00:00.0000000 GameState.DebugPrintPower() - CREATE_GAME\n"
        b"current game\n"
    )
    tailer = PowerLogTailer(path, from_end=False, from_last_create_game=True)
    assert [line.text for line in tailer.poll()] == [
        "D 00:00:00.0000000 GameState.DebugPrintPower() - CREATE_GAME",
        "current game",
    ]


def test_live_adapter_tracks_entities_tags_and_gate():
    adapter = PowerLogStateAdapter()
    adapter.consume("FULL_ENTITY - Creating ID=12 CardID=CS2_172")
    snapshot = adapter.consume("TAG_CHANGE Entity=12 tag=ATK value=3")
    assert snapshot.entities["12"] == "CS2_172"
    assert snapshot.tags["12"]["ATK"] == "3"
    assert snapshot.confidence == "amber"
    snapshot = adapter.consume("UNKNOWN_EFFECT card=NEW_CARD")
    assert snapshot.confidence == "red"


def test_live_adapter_treats_open_choices_as_a_decision_boundary():
    adapter = PowerLogStateAdapter()
    snapshot = adapter.consume(
        "D 00:00:00.0000000 PowerTaskList.DebugPrintPower() - "
        "Choices - id=3 Player=1 ChoiceType=GENERAL"
    )
    assert snapshot.decision_boundary
    adapter.consume(
        "D 00:00:00.0000000 PowerTaskList.DebugPrintPower() - "
        "Choices - Source=[id=47 cardId=CAP_105 name=Hook]"
    )
    snapshot = adapter.consume(
        "D 00:00:00.0000000 PowerTaskList.DebugPrintPower() - "
        "Choices - Entities[3]=[id=89 cardId=CAP_107 name=A, "
        "id=90 cardId=CATA_556 name=B, id=91 cardId=EDR_457 name=C]"
    )
    assert snapshot.open_choice == {
        "id": 3,
        "choice_type": "GENERAL",
        "source_entity": 47,
        "source_card": "CAP_105",
        "options": [
            {"entity": 89, "card_id": "CAP_107"},
            {"entity": 90, "card_id": "CATA_556"},
            {"entity": 91, "card_id": "EDR_457"},
        ],
    }
    snapshot = adapter.consume(
        "D 00:00:00.0000000 PowerTaskList.DebugPrintPower() - "
        "ChosenEntities - id=3 Player=1 EntitiesCount=1"
    )
    assert snapshot.open_choice is None


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


def test_live_state_derives_action_controller_from_public_source_entity():
    state = reconstruct_game({
        "preamble": [{
            "kind": "FullEntity", "entity": 7, "card_id": "CORE_BT_035",
            "tags": [{"tag": "CONTROLLER", "value": 2},
                     {"tag": "ZONE", "value": "HAND"}],
        }],
        "blocks": [{
            "block_type": "PLAY", "source_entity": 7,
            "source_card": "CORE_BT_035", "target_entity": 0,
            "target_card": None, "effects": [],
        }],
    })
    assert state.action_history == [{
        "kind": "PLAY", "source_entity": 7, "source_card": "CORE_BT_035",
        "target_entity": 0, "target_card": None, "controller": 2, "turn": None,
    }]
    token = reconstruct_game({
        "preamble": [],
        "blocks": [{
            "block_type": "ATTACK", "source_entity": 8,
            "source_card": "CORE_BT_035", "target_entity": 0,
            "target_card": None,
            "effects": [{
                "kind": "FullEntity", "entity": 8, "card_id": "CORE_BT_035",
                "tags": [{"tag": "CONTROLLER", "value": 1},
                         {"tag": "ZONE", "value": "PLAY"}],
            }],
        }],
    })
    assert token.action_history[0]["controller"] == 1


def test_live_state_cursor_only_applies_new_open_block_effects():
    base = {
        "preamble": [{"kind": "FullEntity", "entity": 7, "card_id": "CORE_BT_035",
                      "tags": [{"tag": "CONTROLLER", "value": 1},
                               {"tag": "ZONE", "value": "PLAY"}]}],
        "blocks": [{"packet_id": 10, "block_type": "PLAY", "source_entity": 7,
                    "source_card": "CORE_BT_035", "effects": [
                        {"kind": "TagChange", "entity": 7, "tag": "DAMAGE", "value": 1},
                    ]}],
    }
    cursor = LiveStateCursor()
    first = cursor.apply_game(base)
    assert first.entities["7"].damage == 1 and len(first.action_history) == 1
    extended = {
        **base,
        "blocks": [{**base["blocks"][0], "effects": [
            *base["blocks"][0]["effects"],
            {"kind": "TagChange", "entity": 7, "tag": "DAMAGE", "value": 2},
        ]}],
    }
    second = cursor.apply_game(extended)
    assert second.entities["7"].damage == 2
    assert len(second.action_history) == 1


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


def test_game_reset_replaces_entities_and_current_turn_history():
    state = reconstruct_game({
        "preamble": [{"kind": "FullEntity", "entity": 10, "card_id": "OLD_CARD",
                      "tags": [{"tag": "CONTROLLER", "value": 1},
                               {"tag": "ZONE", "value": "PLAY"}]}],
        "blocks": [
            {"block_type": "PLAY", "controller": 1, "source_entity": 10,
             "source_card": "OLD_CARD"},
            {"block_type": "GAME_RESET", "effects": [
                {"kind": "ResetGame"},
                {"kind": "FullEntity", "entity": 20, "card_id": "NEW_CARD",
                 "tags": [{"tag": "CONTROLLER", "value": 1},
                          {"tag": "ZONE", "value": "HAND"}]},
                {"kind": "FullEntity", "entity": 30, "card_id": "PLAYER_01",
                 "tags": [{"tag": "CONTROLLER", "value": 1},
                          {"tag": "CARDTYPE", "value": "PLAYER"},
                          {"tag": "RESOURCES", "value": 2},
                          {"tag": "CURRENT_PLAYER", "value": 1}]},
            ]},
        ],
    })
    assert set(state.entities) == {"20", "30"}
    assert set(state.entity_registry) == {"10", "20", "30"}
    assert state.entity_registry["10"].card_id == "OLD_CARD"
    assert not state.action_history
    assert state.reset_count == 1
    assert state.visible()["player_meta"]["1"]["mana"] == 2
    assert state.active_player == 1


def test_live_state_marks_final_gameover_as_a_non_decision_phase():
    state = reconstruct_game({"preamble": [{
        "kind": "FullEntity", "entity": 1, "card_id": "GAME_005",
        "tags": [{"tag": "CARDTYPE", "value": "GAME"},
                 {"tag": "STEP", "value": "FINAL_GAMEOVER"}],
    }], "blocks": []})
    assert state.visible()["game_phase"] == "FINAL_GAMEOVER"


def test_live_state_recovers_current_player_from_untagged_player_entities():
    state = reconstruct_game({"preamble": [
        {"kind": "FullEntity", "entity": 2, "tags": [
            {"tag": "MULLIGAN_STATE", "value": "DONE"},
            {"tag": "CURRENT_PLAYER", "value": 1},
            {"tag": "RESOURCES", "value": 0},
            {"tag": "MAXRESOURCES", "value": 1},
        ]},
        {"kind": "FullEntity", "entity": 3, "tags": [
            {"tag": "MULLIGAN_STATE", "value": "DONE"},
            {"tag": "CURRENT_PLAYER", "value": 0},
            {"tag": "RESOURCES", "value": 2},
            {"tag": "MAXRESOURCES", "value": 2},
        ]},
    ], "blocks": []})
    assert state.active_player == 1
    assert state.visible()["player_meta"]["1"]["mana"] == 0
    assert state.visible()["player_meta"]["2"]["max_mana"] == 2


def test_live_state_refreshes_boolean_player_current_player_each_turn():
    state = reconstruct_game({"preamble": [
        {"kind": "FullEntity", "entity": 2, "tags": [
            {"tag": "MULLIGAN_STATE", "value": "DONE"},
            {"tag": "CURRENT_PLAYER", "value": 1},
        ]},
        {"kind": "FullEntity", "entity": 3, "tags": [
            {"tag": "MULLIGAN_STATE", "value": "DONE"},
            {"tag": "CURRENT_PLAYER", "value": 0},
        ]},
    ], "blocks": [
        {"block_type": "TRIGGER", "effects": [
            {"kind": "TagChange", "entity": 2,
             "tag": "CURRENT_PLAYER", "value": 0},
            {"kind": "TagChange", "entity": 3,
             "tag": "CURRENT_PLAYER", "value": 1},
        ]},
    ]})
    assert state.active_player == 2


def test_live_state_subtracts_resources_used_from_available_mana():
    state = reconstruct_game({"preamble": [
        {"kind": "FullEntity", "entity": 2, "tags": [
            {"tag": "MULLIGAN_STATE", "value": "DONE"},
            {"tag": "RESOURCES", "value": 3},
            {"tag": "RESOURCES_USED", "value": 2},
        ]},
        {"kind": "FullEntity", "entity": 3, "tags": [
            {"tag": "MULLIGAN_STATE", "value": "DONE"},
        ]},
    ], "blocks": []})
    assert state.visible()["player_meta"]["1"]["mana"] == 1


def test_replay_events_require_explicit_choice_resolution():
    open_result = extract_replay_events({"blocks": [{
        "packet_id": 1, "block_type": "DISCOVER",
        "effects": [{"kind": "Choices", "choices": [10, 11, 12]}],
    }]})
    assert not open_result.replayable and open_result.unresolved_choices == 1
    closed = extract_replay_events({"blocks": [{
        "packet_id": 2, "block_type": "DISCOVER",
        "effects": [{"kind": "Choices", "id": 3, "choices": [10, 11, 12]},
                    {"kind": "ChosenEntities", "id": 3, "entities": [11]}],
    }]})
    assert closed.event_stream_closed and not closed.replayable
    assert closed.events[0].chosen == (11,)


def test_deck_action_does_not_keep_live_event_stream_open():
    result = extract_replay_events({"blocks": [{
        "packet_id": 1, "block_type": "DECK_ACTION",
        "effects": [{"kind": "TagChange", "entity": 4,
                     "tag": "ZONE", "value": "DECK"}],
    }]})
    assert result.event_stream_closed
    assert not result.unsupported_blocks


def test_replay_resolves_choice_id_across_powerlog_blocks():
    result = extract_replay_events({"blocks": [
        {"packet_id": 1, "block_type": "POWER", "effects": [
            {"kind": "Choices", "id": 7, "tasklist": 9,
             "type": "DISCOVER", "choices": [10, 11, 12]},
        ]},
        {"packet_id": 2, "block_type": "META", "effects": [
            {"kind": "ChosenEntities", "id": 7, "entities": [11]},
        ]},
    ]})
    assert result.event_stream_closed
    assert result.unresolved_choices == 0
    event = result.events[0]
    assert event.choice_id == 7 and event.choice_type == "DISCOVER"
    assert event.task_list == 9 and event.chosen == (11,)


def test_replay_uses_last_game_reset_snapshot_as_its_baseline():
    result = extract_replay_events({
        "preamble": [{"kind": "FullEntity", "entity": 1, "card_id": "OLD",
                      "tags": [{"tag": "ZONE", "value": "DECK"},
                               {"tag": "CONTROLLER", "value": 1}]}],
        "blocks": [
            {"block_type": "PLAY", "source_entity": 1, "source_card": "OLD"},
            {"block_type": "GAME_RESET", "effects": [
                {"kind": "ResetGame"},
                {"kind": "FullEntity", "entity": 2, "card_id": "NEW",
                 "tags": [{"tag": "ZONE", "value": "DECK"},
                          {"tag": "CONTROLLER", "value": 1}]},
            ]},
            {"block_type": "TURN_END"},
        ],
    })
    assert result.reset_count == 1
    assert result.event_stream_closed
    assert result.deck_counts == {"1": {"NEW": 1}}
    assert [event.kind for event in result.events] == ["TURN_END"]


def test_replay_retains_pre_reset_entity_identity_without_replaying_old_actions():
    result = extract_replay_events({"blocks": [
        {"block_type": "POWER", "effects": [
            {"kind": "FullEntity", "entity": 7, "card_id": "PERSISTENT",
             "tags": [{"tag": "ZONE", "value": "HAND"}, {"tag": "CONTROLLER", "value": 1}]},
        ]},
        {"block_type": "GAME_RESET", "effects": [{"kind": "ResetGame"}]},
        {"block_type": "ATTACK", "source_entity": 7, "target_entity": 0},
    ]})
    assert result.retained_pre_reset_entities == {7}
    assert [event.kind for event in result.events] == ["ATTACK"]
    assert not result.transition_errors


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


def test_belief_gate_uses_the_runtime_opponent_controller():
    gate = evaluate_gate(event_stream_closed=True, session_ready=True,
                         beliefs={"1": {"compatible": True,
                                        "candidate_decks": [{"A": 2}]}},
                         state_matches=False, mode="belief",
                         belief_action_consensus=True,
                         opponent_controller="1")
    assert gate["available"]


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
    assert _executable_card_id(result.game, "VAC_COIN2") == "GAME_005"
    assert _executable_card_id(result.game, "TTN_COIN2") == "GAME_005"
    # A Hero's public ATK is authoritative even when a generated weapon is
    # not emitted as a normal CARDTYPE=WEAPON entity in the live snapshot.
    state.entities["1"].tags["ATK"] = 2
    state.entities["1"].attack = 2
    state.entities["44"] = EntityView("44", card_id="CORE_BT_035", controller=2,
                                       zone="PLAY", card_type="MINION", attack=1,
                                       health=1)
    hero_attack = build_snapshot_hypothesis(
        cards_path=cards, state=state, own_deck={"CORE_BT_035": 30},
        opponent_deck={"CORE_BT_035": 30}, player_classes=("WARRIOR", "MAGE"),
    )
    assert hero_attack.available, hero_attack.reason
    assert any(action.kind == "HERO_ATTACK" for action in hero_attack.game.legal_actions())
    state.entities["1"].tags.pop("ATK")
    state.entities["1"].attack = None
    del state.entities["44"]
    # A visible opponent Sapling has no text/effect beyond a 1/1 body. It is
    # outside the Dragon Warrior executable pool but must not block combat
    # projection or live recommendations.
    state.entities["41"] = EntityView("41", card_id="AT_037t", controller=2,
                                       zone="PLAY", card_type="MINION",
                                       attack=1, health=1)
    public_sapling = build_snapshot_hypothesis(
        cards_path=cards, state=state, own_deck={"CORE_BT_035": 30},
        opponent_deck={"CORE_BT_035": 30}, player_classes=("WARRIOR", "MAGE"),
    )
    assert public_sapling.available, public_sapling.reason
    assert any(card.card_id == "AT_037t" and card.attack == 1 and card.health == 1
               for card in public_sapling.game.players[1].board)
    assert "AT_037t" not in public_sapling.game.executable_card_ids
    del state.entities["41"]
    # A minion played in the current public turn must retain summoning
    # sickness when the snapshot bridge hydrates the board.
    state.entities["33"] = EntityView("33", card_id="CATA_111", controller=1,
                                       zone="PLAY", card_type="MINION")
    state.action_history.append({
        "kind": "PLAY", "source_entity": 33, "source_card": "CATA_111",
        "controller": 1, "turn": 3,
    })
    summoned_this_turn = build_snapshot_hypothesis(
        cards_path=cards, state=state, own_deck={"CORE_BT_035": 30},
        opponent_deck={"CORE_BT_035": 30}, player_classes=("WARRIOR", "MAGE"),
    )
    assert summoned_this_turn.available, summoned_this_turn.reason
    assert not any(action.kind == "ATTACK" and action.source == 33
                   for action in summoned_this_turn.game.legal_actions())
    del state.entities["33"]
    state.action_history.pop()
    state.entities["38"] = EntityView("38", card_id="VAC_COIN2", controller=1,
                                       zone="HAND", card_type="SPELL", cost=0)
    aliased_coin = build_snapshot_hypothesis(
        cards_path=cards, state=state, own_deck={"CORE_BT_035": 30},
        opponent_deck={"CORE_BT_035": 30}, player_classes=("WARRIOR", "MAGE"),
    )
    assert aliased_coin.available, aliased_coin.reason
    del state.entities["38"]
    state.entities["37"] = EntityView("37", card_id="JAIL_430e1", controller=1,
                                       zone="PLAY", card_type="ENCHANTMENT")
    attached_effect = build_snapshot_hypothesis(
        cards_path=cards, state=state, own_deck={"CORE_BT_035": 30},
        opponent_deck={"CORE_BT_035": 30}, player_classes=("WARRIOR", "MAGE"),
    )
    assert attached_effect.available, attached_effect.reason
    del state.entities["37"]
    # A local player's hand is public to their own client.  If the configured
    # local controller instead has anonymous hand entities while the other
    # side is identified, do not silently swap user-provided deck ownership.
    state.entities["39"] = EntityView("39", controller=2, zone="HAND")
    reversed_controller = build_snapshot_hypothesis(
        cards_path=cards, state=state, own_deck={"CORE_BT_035": 30},
        opponent_deck={"CORE_BT_035": 30}, player_classes=("WARRIOR", "MAGE"),
        self_controller=2,
    )
    assert reversed_controller.reason == (
        "self-controller likely reversed: configured local hand has hidden cards")
    del state.entities["39"]
    # Current clients can omit CARDTYPE=HERO_POWER for ordinary class powers.
    # It must not become an extra board minion or a missing executable card.
    state.entities["40"] = EntityView("40", card_id="HERO_01wbp", controller=1,
                                       zone="PLAY")
    implicit_power = build_snapshot_hypothesis(
        cards_path=cards, state=state, own_deck={"CORE_BT_035": 30},
        opponent_deck={"CORE_BT_035": 30}, player_classes=("WARRIOR", "MAGE"),
    )
    assert implicit_power.available, implicit_power.reason
    # Block packets from current clients may omit controller. The source
    # entity still proves that this player used their class Hero Power, so it
    # must not be offered a second time in the same turn.
    state.action_history.append({
        "kind": "POWER", "source_entity": 40, "source_card": "HERO_01wbp",
        "controller": None, "turn": 3,
    })
    spent_power = build_snapshot_hypothesis(
        cards_path=cards, state=state, own_deck={"CORE_BT_035": 30},
        opponent_deck={"CORE_BT_035": 30}, player_classes=("WARRIOR", "MAGE"),
    )
    assert spent_power.available, spent_power.reason
    assert not any(action.kind == "HERO_POWER" for action in spent_power.game.legal_actions())
    state.action_history.pop()
    # A completed effect can surface a zero-information implementation object
    # in PLAY. It has no card identity, type, stats, cost, or references, so
    # advisory mode may omit it while preserving an explicit risk flag.
    state.entities["102"] = EntityView("102", controller=2, zone="PLAY")
    state.entities["102"].zone_history = [(100, "SETASIDE"), (101, "PLAY")]
    opaque_strict = build_snapshot_hypothesis(
        cards_path=cards, state=state, own_deck={"CORE_BT_035": 30},
        opponent_deck={"CORE_BT_035": 30}, player_classes=("WARRIOR", "MAGE"),
    )
    assert opaque_strict.reason == "controller 2 has hidden public card identity"
    opaque_advisory = build_snapshot_hypothesis(
        cards_path=cards, state=state, own_deck={"CORE_BT_035": 30},
        opponent_deck={"CORE_BT_035": 30}, player_classes=("WARRIOR", "MAGE"),
        setaside_policy="advisory",
    )
    assert opaque_advisory.available, opaque_advisory.reason
    assert any("opaque PLAY artifacts" in note for note in opaque_advisory.hypothesis_notes)
    del state.entities["102"]
    recommendation = recommend_puct_state(
        result.game, "unused.pt", model=HeuristicPolicyValueModel(), iterations=2,
    )
    assert recommendation.available and recommendation.action is not None
    policy_only = recommend_puct_state(
        result.game, "unused.pt", model=HeuristicPolicyValueModel(), iterations=0,
    )
    assert policy_only.available and policy_only.action is not None

    # GAME_RESET snapshots can retain completed-effect entities in SETASIDE.
    # An unlinked ordinary entity is inert; a linked one remains fail-closed.
    state.entities["12"] = EntityView("12", card_id="CORE_BT_035", controller=1,
                                       zone="SETASIDE", card_type="MINION")
    strict = build_snapshot_hypothesis(
        cards_path=cards, state=state, own_deck={"CORE_BT_035": 30},
        opponent_deck={"CORE_BT_035": 30}, player_classes=("WARRIOR", "MAGE"),
    )
    assert strict.reason == "unsupported live zone: SETASIDE"
    inert = build_snapshot_hypothesis(
        cards_path=cards, state=state, own_deck={"CORE_BT_035": 30},
        opponent_deck={"CORE_BT_035": 30}, player_classes=("WARRIOR", "MAGE"),
        setaside_policy="advisory",
    )
    assert inert.available, inert.reason
    assert any("inert SETASIDE" in note for note in inert.hypothesis_notes)
    projection = state.public_decision_projection()
    assert "12" in projection["inert_setaside"]
    state.entities["13"] = EntityView("13", card_id="CORE_BT_035", controller=1,
                                       zone="PLAY", card_type="MINION",
                                       tags={"LINKED_ENTITY": 12})
    linked = build_snapshot_hypothesis(
        cards_path=cards, state=state, own_deck={"CORE_BT_035": 30},
        opponent_deck={"CORE_BT_035": 30}, player_classes=("WARRIOR", "MAGE"),
    )
    assert linked.reason == "unsupported live zone: SETASIDE"
    assert "12" in state.public_decision_projection()["active_setaside"]
    del state.entities["13"]
    # A known SECRET is hydrated directly. Its historical creator object is
    # not a pending action, so advisory projection can exclude the creator.
    state.entities["14"] = EntityView("14", card_id="KNOWN_SECRET", controller=1,
                                       zone="SECRET", card_type="SPELL",
                                       tags={"CREATOR": 12})
    assert "12" in state.public_decision_projection()["inert_setaside"]
    del state.entities["14"]
    state.entities["11"] = EntityView("11", card_id="CORE_BT_035", controller=1,
                                       zone="SETASIDE", card_type="MINION")
    choice = build_snapshot_hypothesis(
        cards_path=cards, state=state, own_deck={"CORE_BT_035": 30},
        opponent_deck={"CORE_BT_035": 30}, player_classes=("WARRIOR", "MAGE"),
        open_choice_kind="DISCOVER", open_choice_entities=(11,),
        setaside_policy="advisory",
    )
    assert choice.available, choice.reason
    assert choice.game.pending_choice["kind"] == "DISCOVER"
    assert choice.game.legal_actions()[0].kind == "DISCOVER_PICK"

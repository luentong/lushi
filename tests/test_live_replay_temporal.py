"""Opening-deck inference must not consume later Power.log packets."""

from hsa.live_replay import (
    EntityIdMapper,
    SimulatorActionPlan,
    action_from_plan,
    audit_post_action_source_reveals,
    build_simulator_action_plan,
    extract_replay_events,
)


def test_late_top_level_deck_entity_is_not_an_opening_deck_card():
    result = extract_replay_events({
        "preamble": [
            {"kind": "FullEntity", "packet_id": 2, "entity": 10,
             "card_id": "START", "tags": [
                 {"tag": "ZONE", "value": "DECK"},
                 {"tag": "CONTROLLER", "value": 1}]},
            # This is top-level but occurs after the first player action.
            {"kind": "FullEntity", "packet_id": 30, "entity": 11,
             "card_id": "GENERATED", "tags": [
                 {"tag": "ZONE", "value": "DECK"},
                 {"tag": "CONTROLLER", "value": 1},
                 {"tag": "CREATOR", "value": 99}]},
        ],
        "blocks": [{"packet_id": 20, "block_type": "PLAY",
                    "source_entity": 10, "source_card": "START"}],
    })
    assert result.deck_counts == {"1": {"START": 1}}
    assert any(row["card_id"] == "GENERATED" for row in result.generated_entities)


def test_opening_hidden_deck_slot_survives_later_zone_change():
    result = extract_replay_events({
        "preamble": [
            {"kind": "FullEntity", "packet_id": 2, "entity": 10,
             "card_id": "", "tags": [
                 {"tag": "ZONE", "value": "DECK"},
                 {"tag": "CONTROLLER", "value": 2}]},
            {"kind": "TagChange", "packet_id": 3, "entity": 10,
             "tag": "CONTROLLER", "value": 2},
            {"kind": "TagChange", "packet_id": 30, "entity": 10,
             "tag": "ZONE", "value": "HAND"},
        ],
        "blocks": [{"packet_id": 20, "block_type": "PLAY",
                    "source_entity": 99, "source_card": "OTHER"}],
    })
    assert result.unknown_deck_slots == {"2": 1}


def test_hidden_opponent_play_is_auditable_only_after_same_block_reveal():
    game = {"preamble": [], "blocks": [
        {"packet_id": 20, "block_type": "PLAY", "source_entity": 10,
         "source_card": None, "effects": [
             {"packet_id": 21, "kind": "ShowEntity", "entity": 10,
              "card_id": "CARD_A"}]},
    ]}
    diagnostics = extract_replay_events(game)
    assert diagnostics.events[0].source_card is None
    assert build_simulator_action_plan(diagnostics)[0].reason == "source card hidden"
    assert audit_post_action_source_reveals(game, diagnostics) == [{
        "event_index": 0, "action_packet_id": 20, "source_entity": 10,
        "revealed_card": "CARD_A", "reveal_packet_id": 21,
        "timing": "post_action_only",
    }]


def test_later_reveal_cannot_be_attributed_to_hidden_play():
    game = {"preamble": [], "blocks": [
        {"packet_id": 20, "block_type": "PLAY", "source_entity": 10,
         "source_card": None, "effects": []},
        {"packet_id": 30, "block_type": "TRIGGER", "source_entity": 10,
         "effects": [{"packet_id": 31, "kind": "ShowEntity", "entity": 10,
                      "card_id": "CARD_A"}]},
    ]}
    assert audit_post_action_source_reveals(game, extract_replay_events(game)) == []


def test_power_resolution_is_not_counted_as_player_decision():
    diagnostics = extract_replay_events({"blocks": [
        {"packet_id": 1, "block_type": "PLAY", "source_entity": 10,
         "source_card": "CARD_A"},
        {"packet_id": 2, "block_type": "POWER", "source_entity": 10,
         "source_card": "CARD_A"},
        {"packet_id": 3, "block_type": "TURN_START"},
        {"packet_id": 4, "block_type": "TURN_END"},
    ]})
    plans = build_simulator_action_plan(diagnostics)
    assert [plan.mappable for plan in plans] == [True, False, False, True]
    assert plans[1].reason == "effect resolution block; not a player decision"
    action, error = action_from_plan(plans[3], EntityIdMapper())
    assert error is None and action.kind == "END_TURN"


def test_targeted_action_requires_unique_legal_target_player():
    from hsa.dragon_mirror import Action
    mapper = EntityIdMapper()
    mapper.bind(10, 100)
    mapper.bind(20, 200)
    plan = SimulatorActionPlan(0, "ATTACK", "MINION_A", "MINION_B",
                               10, 20, (), True)
    assert action_from_plan(plan, mapper)[1] == (
        "target player cannot be inferred without legal actions")
    expected = Action("ATTACK", 100, 1, 200)
    action, error = action_from_plan(
        plan, mapper, legal_actions=[Action("ATTACK", 100, 1, None), expected])
    assert error is None and action == expected


def test_hero_attack_uses_no_source_entity_and_face_target():
    from hsa.dragon_mirror import Action
    plan = SimulatorActionPlan(0, "ATTACK", "HERO_01", "HERO_09",
                               10, 20, (), True)
    expected = Action("HERO_ATTACK", None, 1, None)
    action, error = action_from_plan(
        plan, EntityIdMapper(), legal_actions=[expected])
    assert error is None and action == expected


def test_play_block_for_class_hero_power_is_not_an_ordinary_card_play():
    from hsa.dragon_mirror import Action
    plan = SimulatorActionPlan(0, "PLAY", "HERO_10cbp", None,
                               10, None, (), True)
    expected = Action("HERO_POWER", None, None, None)
    action, error = action_from_plan(
        plan, EntityIdMapper(), legal_actions=[expected])
    assert error is None and action == expected


def test_ambiguous_hero_target_fails_closed():
    from hsa.dragon_mirror import Action
    mapper = EntityIdMapper()
    mapper.bind(10, 100)
    plan = SimulatorActionPlan(0, "PLAY", "HEAL", "HERO_09",
                               10, 20, (), True)
    actions = [Action("PLAY", 100, 0, None),
               Action("PLAY", 100, 1, None)]
    assert action_from_plan(plan, mapper, legal_actions=actions)[1] == (
        "observed action has no unique legal engine match")


def test_executor_applies_only_the_matched_targeted_action():
    from hsa.dragon_mirror import Action
    from hsa.live_executor import execute_plans

    class Game:
        def __init__(self):
            self.applied = []

        def legal_actions(self):
            return [Action("ATTACK", 100, 1, 200),
                    Action("ATTACK", 100, 1, 201)]

        def step(self, action):
            self.applied.append(action)

    mapper = EntityIdMapper()
    mapper.bind(10, 100)
    mapper.bind(20, 200)
    game = Game()
    plan = SimulatorActionPlan(0, "ATTACK", "MINION_A", "MINION_B",
                               10, 20, (), True)
    report = execute_plans(game, [plan], mapper)
    assert report.complete and report.executed == 1
    assert game.applied == [Action("ATTACK", 100, 1, 200)]

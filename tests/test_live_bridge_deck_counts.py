from hsa.live_bridge import _remaining_deck, _visible_card_counts
from hsa.live_state import EntityView, LiveGameState


def test_play_and_repeated_attacks_consume_one_deck_copy():
    state = LiveGameState(entities={
        "10": EntityView("10", card_id="MINION", controller=1,
                         zone="PLAY", card_type="MINION")},
        action_history=[{"kind": kind, "controller": 1, "source_card": "MINION",
                         "source_entity": 10} for kind in ("PLAY", "ATTACK", "ATTACK")])
    assert _visible_card_counts(state, 1) == {"MINION": 1}
    assert _remaining_deck({"MINION": 2}, _visible_card_counts(state, 1)) == ["MINION"]
    state.entities["10"].zone = "GRAVEYARD"
    assert _visible_card_counts(state, 1) == {"MINION": 1}
    state.entities["10"].zone = "DECK"
    assert not _visible_card_counts(state, 1)


def test_generated_copies_and_hero_powers_do_not_consume_deck_copies():
    state = LiveGameState(entities={
        "10": EntityView("10", card_id="MINION", controller=1,
                         zone="HAND", tags={"CREATOR": 99}),
        "11": EntityView("11", card_id="MINION", controller=1,
                         zone="GRAVEYARD", tags={"COPIED_FROM_ENTITY_ID": 20}),
        "12": EntityView("12", card_id="HERO_01wbp", controller=1, zone="PLAY"),
        "13": EntityView("13", card_id="MINION", controller=1,
                         zone="GRAVEYARD", tags={"CREATOR": 0}),
        "14": EntityView("14", card_id="MINION", controller=2, zone="PLAY"),
    })
    assert _visible_card_counts(state, 1) == {"MINION": 1}

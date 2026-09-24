from hsa.deck_metadata import apply_deck_metadata_overrides


def test_current_companion_hunter_call_of_the_wild_printing_maps_to_canonical_rule():
    cards = {}
    apply_deck_metadata_overrides(cards)
    assert cards[130677]["id"] == "CORE_OG_211"
    assert cards[130677]["name"] == "Call of the Wild"
    assert cards[130677]["cost"] == 8

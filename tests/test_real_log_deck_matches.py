import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_real_log_deck_matches import rank_decks


def test_no_visible_opening_deck_card_does_not_rank_all_decks_as_perfect():
    result = rank_decks({}, [{"id": "a", "deckstring": "not-needed"}], {}, set())
    assert result["status"] == "opening_deck_identities_not_visible"
    assert result["top_candidates"] == []
    assert result["equally_best_candidates"] == 0
    assert result["best_mismatch"] is None


def test_partial_evidence_filters_wrong_class_without_hiding_missing_cards():
    from types import SimpleNamespace
    from unittest.mock import patch
    fake = SimpleNamespace(
        decode_counts=lambda code, db: {"A": 2} if code == "wrong" else {"A": 1},
        get_deck_class=lambda code, db: "WARRIOR" if code == "wrong" else "PRIEST")
    entries = [{"id": "wrong", "deckstring": "wrong"},
               {"id": "right", "deckstring": "right"}]
    with patch.dict(sys.modules, {"export_live_deck_configs": fake}):
        result = rank_decks({"A": 2}, entries, {}, {"A"}, "PRIEST")
    assert len(result["top_candidates"]) == 1
    assert result["top_candidates"][0]["id"] == "right"
    assert result["best_mismatch"] == 1
    assert result["compatible_candidates"] == 0

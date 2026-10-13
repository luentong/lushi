from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from audit_broad_teacher_outcomes import choose_rows, paired_score


def test_choose_rows_balances_decks_and_ignores_model_agreement():
    rows = [
        {"deck": "a", "search_agree": True, "teacher_target": 1, "model_pick": 0},
        {"deck": "a", "search_agree": True, "teacher_target": 2, "model_pick": 0},
        {"deck": "a", "search_agree": True, "teacher_target": 0, "model_pick": 0},
        {"deck": "b", "search_agree": True, "teacher_target": 1, "model_pick": 0},
        {"deck": "b", "search_agree": False, "teacher_target": 1, "model_pick": 0},
    ]
    assert [row["deck"] for row in choose_rows(rows, 3)] == ["a", "b", "a"]


def test_paired_score_excludes_unfinished_without_breaking_alignment():
    results = [
        {"action_key": ["teacher"], "outcomes": [
            {"replicate": 0, "status": "wins"},
            {"replicate": 1, "status": "truncated"},
            {"replicate": 2, "status": "losses"}]},
        {"action_key": ["model"], "outcomes": [
            {"replicate": 0, "status": "losses"},
            {"replicate": 1, "status": "wins"},
            {"replicate": 2, "status": "losses"}]},
    ]
    assert paired_score(results, ["teacher"], ["model"]) == {
        "paired_decided": 2, "teacher_better": 1, "model_better": 0,
        "tied": 1, "score_delta": .5,
    }

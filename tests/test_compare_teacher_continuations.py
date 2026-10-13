import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from compare_teacher_continuations import compare_reports


def report(continuation, delta):
    return {"status": "complete", "source_audit": "same.jsonl.gz",
            "replicates": 8, "max_actions": 320,
            "continuation": continuation,
            "rows": [{"game_seed": 5, "step": 7, "deck": "deck",
                      "teacher_action": "attack", "model_action": "pass",
                      "comparison": {"paired_decided": 8,
                                     "teacher_better": 2 if delta > 0 else 0,
                                     "model_better": 2 if delta < 0 else 0,
                                     "tied": 6, "score_delta": delta}}]}


def test_agreement_is_diagnostic_not_training_authorization():
    result = compare_reports(report("heuristic", .25), report("entity-greedy", .25))
    assert result["both_favor_teacher"] == 1
    assert result["training_authorized"] is False


def test_opposite_outcomes_are_not_consensus():
    result = compare_reports(report("heuristic", .25), report("entity-greedy", -.25))
    assert result["opposite_directions"] == 1
    assert result["both_favor_teacher"] == 0


def test_misaligned_roots_fail_closed():
    other = report("entity-greedy", .25)
    other["rows"][0]["step"] = 8
    with pytest.raises(ValueError, match="identical roots"):
        compare_reports(report("heuristic", .25), other)

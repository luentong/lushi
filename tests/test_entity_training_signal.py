from __future__ import annotations

import gzip
import json
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_entity_training_signal import audit


def _write(path, rows):
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def _row(seed, action_count, kind, outcome, advantage):
    return {"view": {"actions": [{} for _ in range(action_count)]},
            "chosen": 0, "action_key": [kind], "return": outcome,
            "advantage": advantage, "terminated": True, "truncated": False,
            "deck_a": "a", "deck_b": "b", "actor": 0,
            "game_seed": seed, "logp": math.log(1 / action_count)}


def test_training_signal_audit_counts_choices_not_just_games(tmp_path):
    path = tmp_path / "rows.jsonl.gz"
    _write(path, [_row(1, 1, "END_TURN", 1.0, .4),
                  _row(1, 3, "PLAY", 1.0, .6),
                  _row(2, 2, "PLAY", -1.0, -.8)])
    result = audit([path])["by_file"][0]
    assert result["games"] == 2
    assert result["counts"]["single_legal_action"] == 1
    assert result["counts"]["end_turn"] == 1
    assert result["counts"]["positive_advantage_in_won_game"] == 2
    assert result["counts"]["negative_advantage_in_lost_game"] == 1
    assert result["mean_chosen_probability"] == pytest.approx((1 + 1 / 3 + .5) / 3)


def test_training_signal_refuses_truncated_label(tmp_path):
    path = tmp_path / "rows.jsonl.gz"
    row = _row(1, 2, "PLAY", -1.0, -.3)
    row["truncated"] = True
    _write(path, [row])
    with pytest.raises(ValueError, match="truncated"):
        audit([path])

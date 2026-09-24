"""Consensus over model actions from multiple hidden-state hypotheses."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class ConsensusResult:
    available: bool
    action: dict[str, Any] | None
    support: float
    hypotheses: int
    reason: str | None = None


def _key(action: dict[str, Any]) -> tuple[Any, ...]:
    return (action.get("kind"), action.get("source"),
            action.get("target_player"), action.get("target_entity"))


def choose_consensus(actions: Iterable[dict[str, Any]], *, min_support: float = 0.75) -> ConsensusResult:
    candidates = list(actions)
    if not candidates:
        return ConsensusResult(False, None, 0.0, 0, "no hypothesis produced an action")
    counts = Counter(_key(action) for action in candidates)
    key, count = counts.most_common(1)[0]
    support = count / len(candidates)
    selected = next(action for action in candidates if _key(action) == key)
    if support < min_support:
        return ConsensusResult(False, selected, support, len(candidates), "action support below threshold")
    return ConsensusResult(True, selected, support, len(candidates))

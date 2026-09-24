"""Fail-closed execution of mapped live actions in the simulator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .live_replay import EntityIdMapper, SimulatorActionPlan, action_from_plan


@dataclass
class ExecutionReport:
    executed: int = 0
    stopped_at: int | None = None
    reason: str | None = None
    actions: list[dict[str, Any]] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return self.stopped_at is None


def execute_plans(
    game: Any,
    plans: list[SimulatorActionPlan],
    mapper: EntityIdMapper,
    *,
    compare: Callable[[Any], bool] | None = None,
) -> ExecutionReport:
    """Apply only actions that are legal in the current simulator state."""
    report = ExecutionReport()
    for plan in plans:
        action, error = action_from_plan(plan, mapper)
        if error:
            report.stopped_at, report.reason = plan.index, error
            break
        legal = {candidate.key(): candidate for candidate in game.legal_actions()}
        if action.key() not in legal:
            report.stopped_at = plan.index
            report.reason = "mapped action is not legal in simulator state"
            break
        game.step(legal[action.key()])
        report.executed += 1
        report.actions.append({"index": plan.index, "kind": action.kind,
                               "source": action.source, "target": action.target_entity})
        if compare is not None and not compare(game):
            report.stopped_at, report.reason = plan.index, "state comparison failed"
            break
    return report

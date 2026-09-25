"""Fail-closed model recommendation boundary for the Windows companion.

The model is only called with a real :class:`DragonMirrorGame` that has been
replayed and consistency-checked.  A public Power.log snapshot alone is not a
simulator state (hidden hand/deck order and generated entities are missing),
so this module intentionally refuses such input rather than guessing.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .torch_model import TorchPolicyValueModel


@dataclass(frozen=True)
class Recommendation:
    available: bool
    action: dict[str, Any] | None = None
    probability: float | None = None
    value: float | None = None
    reason: str | None = None
    search: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def recommend_replayed_state(
    game: Any,
    checkpoint: str,
    *,
    device: str = "cpu",
    min_probability: float = 0.0,
    model: TorchPolicyValueModel | None = None,
) -> Recommendation:
    """Score legal actions after a verified log-to-simulator replay.

    ``game`` must expose ``legal_actions()``, and the caller must set
    ``_live_replay_verified`` after matching every observed transition.  This
    explicit marker prevents accidental use on a freshly initialised game.
    """
    if not getattr(game, "_live_replay_verified", False):
        return Recommendation(False, reason="live replay is not verified")
    if getattr(game, "finished", False):
        return Recommendation(False, reason="game is finished")
    actions = list(game.legal_actions())
    if not actions:
        return Recommendation(False, reason="no legal action")
    # A belief recommendation scores several candidate decks.  Loading a
    # 150MB checkpoint per candidate is needless latency on a live client, so
    # callers may retain a checked model for the whole watcher process.
    model = model or TorchPolicyValueModel.from_checkpoint(checkpoint, device=device)
    output = model.predict(game, actions)
    index = max(range(len(actions)), key=lambda i: output.priors[i])
    probability = float(output.priors[index])
    if probability < min_probability:
        return Recommendation(False, probability=probability,
                              value=float(output.value),
                              reason="model confidence below threshold")
    action = actions[index]
    return Recommendation(
        True,
        action={"kind": action.kind, "source": action.source,
                "target_player": action.target_player,
                "target_entity": action.target_entity},
        probability=probability,
        value=float(output.value),
    )


def recommend_replayed_states(
    games: list[Any],
    checkpoint: str,
    *,
    device: str = "cpu",
    min_probability: float = 0.0,
    model: TorchPolicyValueModel | None = None,
) -> list[Recommendation]:
    """Score several verified belief hypotheses in one model forward pass."""
    prepared: list[tuple[int, Any, list[Any]]] = []
    results = [Recommendation(False, reason="unprocessed hypothesis") for _ in games]
    for index, game in enumerate(games):
        if not getattr(game, "_live_replay_verified", False):
            results[index] = Recommendation(False, reason="live replay is not verified")
            continue
        if getattr(game, "finished", False):
            results[index] = Recommendation(False, reason="game is finished")
            continue
        actions = list(game.legal_actions())
        if not actions:
            results[index] = Recommendation(False, reason="no legal action")
            continue
        prepared.append((index, game, actions))
    if not prepared:
        return results
    model = model or TorchPolicyValueModel.from_checkpoint(checkpoint, device=device)
    outputs = model.predict_batch((game, actions) for _, game, actions in prepared)
    for (index, _game, actions), output in zip(prepared, outputs):
        action_index = max(range(len(actions)), key=lambda i: output.priors[i])
        probability = float(output.priors[action_index])
        if probability < min_probability:
            results[index] = Recommendation(
                False, probability=probability, value=float(output.value),
                reason="model confidence below threshold",
            )
            continue
        action = actions[action_index]
        results[index] = Recommendation(
            True,
            action={"kind": action.kind, "source": action.source,
                    "target_player": action.target_player,
                    "target_entity": action.target_entity},
            probability=probability,
            value=float(output.value),
        )
    return results


def recommend_puct_state(
    game: Any,
    checkpoint: str,
    *,
    device: str = "cpu",
    iterations: int = 8,
    tree_depth: int = 4,
    model: TorchPolicyValueModel | None = None,
) -> Recommendation:
    """Return a small, policy-prior ISMCTS recommendation for a verified state.

    The model provides priors; a bounded simulator search checks tactical
    consequences.  It is intentionally capped for an interactive companion,
    not the long offline teacher-data configuration.
    """
    if not getattr(game, "_live_replay_verified", False):
        return Recommendation(False, reason="live replay is not verified")
    if getattr(game, "finished", False):
        return Recommendation(False, reason="game is finished")
    if iterations < 1:
        return recommend_replayed_state(game, checkpoint, device=device, model=model)
    from .mcts import InformationSetMCTSPolicy
    network = model or TorchPolicyValueModel.from_checkpoint(checkpoint, device=device)
    search = InformationSetMCTSPolicy(
        samples=1, iterations_per_sample=iterations, tree_depth=tree_depth,
        rollout_depth=4, policy_value_model=network, use_model_value=False,
        force_uniform_expansion=False, max_total_iterations=iterations,
        neural_prior_depth=1,
    )
    try:
        action = search.choose(game)
    except Exception as exc:
        return Recommendation(False, reason=f"PUCT failed: {exc}")
    return Recommendation(
        True,
        action={"kind": action.kind, "source": action.source,
                "target_player": action.target_player,
                "target_entity": action.target_entity},
        search=dict(search.last_search),
    )

"""Small-budget MCTS baseline for the deterministic rules environment.

Version 0 intentionally searches the simulator's full deterministic state. It
is useful for validating tree mechanics but is not yet a fair hidden-information
Hearthstone agent; determinization/ISMCTS is the next algorithmic boundary.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .dragon_mirror import Action, DragonMirrorGame
from .policy import HeuristicPolicy, _card_value


def evaluate_state(game: DragonMirrorGame, player_index: int) -> float:
    if game.finished:
        if game.winner is None:
            return 0.0
        return 1.0 if game.winner == player_index else -1.0
    own = game.players[player_index]
    enemy = game.players[1 - player_index]
    own_board = sum(_card_value(card) for card in own.board)
    enemy_board = sum(_card_value(card) for card in enemy.board)
    own_weapon = 0.0 if own.weapon is None else own.weapon.attack * own.weapon.durability
    enemy_weapon = 0.0 if enemy.weapon is None else enemy.weapon.attack * enemy.weapon.durability
    # Opponent hand contents and deck order are deliberately not valued here.
    raw = (
        2.0 * ((own.health + own.armor) - (enemy.health + enemy.armor))
        + 1.2 * (own_board - enemy_board)
        + 0.8 * (own_weapon - enemy_weapon)
        + 0.7 * (len(own.hand) - len(enemy.hand))
    )
    return math.tanh(raw / 35.0)


@dataclass
class _Node:
    state: DragonMirrorGame
    parent: "_Node | None" = None
    action: Action | None = None
    children: list["_Node"] = field(default_factory=list)
    untried: list[Action] = field(default_factory=list)
    visits: int = 0
    value_sum: float = 0.0

    @property
    def mean_value(self) -> float:
        return self.value_sum / self.visits if self.visits else 0.0


class MCTSPolicy:
    name = "mcts-full-state-v0"
    information_mode = "debug_full_state"

    def __init__(
        self,
        iterations: int = 32,
        rollout_depth: int = 12,
        exploration: float = 1.25,
    ):
        if iterations < 1 or rollout_depth < 0:
            raise ValueError("iterations must be positive and rollout_depth non-negative")
        self.iterations = iterations
        self.rollout_depth = rollout_depth
        self.exploration = exploration
        self.rollout_policy = HeuristicPolicy()
        self.last_search: dict[str, object] = {}

    def choose(self, game: DragonMirrorGame) -> Action:
        legal = game.legal_actions()
        if not legal:
            raise RuntimeError("MCTS requested an action in a terminal state")
        if len(legal) == 1:
            self.last_search = {"iterations": 0, "root_actions": 1, "nodes": 1}
            return legal[0]
        root_player = game.current
        root = _Node(game.clone(), untried=self._ordered_actions(game, legal))
        nodes = 1
        for _ in range(self.iterations):
            node = root
            while not node.state.finished and not node.untried and node.children:
                node = self._select_child(node, root_player)
            if not node.state.finished and node.untried:
                action = node.untried.pop(0)
                child_state = node.state.branch(action)
                node = _Node(
                    child_state,
                    parent=node,
                    action=action,
                    untried=self._ordered_actions(child_state, child_state.legal_actions()),
                )
                node.parent.children.append(node)
                nodes += 1
            value = self._rollout(node.state, root_player)
            while node is not None:
                node.visits += 1
                node.value_sum += value
                node = node.parent
        best = max(
            root.children,
            key=lambda child: (child.visits, child.mean_value, child.action.key()),
        )
        self.last_search = {
            "iterations": self.iterations,
            "root_actions": len(legal),
            "nodes": nodes,
            "selected_visits": best.visits,
            "selected_value": best.mean_value,
        }
        return best.action

    def _ordered_actions(
        self, game: DragonMirrorGame, actions: list[Action]
    ) -> list[Action]:
        if not actions:
            return []
        if game.pending_choice:
            preferred = self.rollout_policy.choose(game)
            return sorted(actions, key=lambda action: action != preferred)
        return sorted(
            actions,
            key=lambda action: (-self.rollout_policy.score(game, action), action.key()),
        )

    def _select_child(self, node: _Node, root_player: int) -> _Node:
        direction = 1.0 if node.state.current == root_player else -1.0
        log_parent = math.log(max(1, node.visits))
        return max(
            node.children,
            key=lambda child: (
                direction * child.mean_value
                + self.exploration * math.sqrt(log_parent / child.visits),
                child.action.key(),
            ),
        )

    def _rollout(self, state: DragonMirrorGame, root_player: int) -> float:
        rollout = state.clone()
        for _ in range(self.rollout_depth):
            if rollout.finished:
                break
            rollout.step(self.rollout_policy.choose(rollout))
        return evaluate_state(rollout, root_player)


class DeterminizedMCTSPolicy:
    """Aggregate independent MCTS searches over sampled hidden-zone layouts."""

    name = "root-determinized-mcts-v3"
    information_mode = "public_dragon_mirror_v3"

    def __init__(
        self,
        samples: int = 4,
        iterations_per_sample: int = 8,
        rollout_depth: int = 8,
        seed: int = 20260909,
    ):
        if samples < 1:
            raise ValueError("samples must be positive")
        self.samples = samples
        self.iterations_per_sample = iterations_per_sample
        self.rollout_depth = rollout_depth
        self.seed = seed
        self.decision_index = 0
        self.last_search: dict[str, object] = {}

    def choose(self, game: DragonMirrorGame) -> Action:
        legal = game.legal_actions()
        if not legal:
            raise RuntimeError("MCTS requested an action in a terminal state")
        if len(legal) == 1:
            return legal[0]
        votes: dict[tuple, int] = {action.key(): 0 for action in legal}
        values: dict[tuple, float] = {action.key(): 0.0 for action in legal}
        nodes = 0
        for sample in range(self.samples):
            sample_seed = self.seed + self.decision_index * self.samples + sample
            # Import lazily to keep the engine/search module dependency acyclic.
            from .belief import PublicBelief

            belief = PublicBelief.from_game(game, game.current)
            state = belief.sample_determinization(game, seed=sample_seed)
            search = MCTSPolicy(
                iterations=self.iterations_per_sample,
                rollout_depth=self.rollout_depth,
            )
            selected = search.choose(state)
            key = selected.key()
            votes[key] += 1
            values[key] += float(search.last_search.get("selected_value", 0.0))
            nodes += int(search.last_search.get("nodes", 0))
        self.decision_index += 1
        by_key = {action.key(): action for action in legal}
        best_key = max(
            votes,
            key=lambda key: (votes[key], values[key], key),
        )
        self.last_search = {
            "information_mode": self.information_mode,
            "samples": self.samples,
            "iterations_per_sample": self.iterations_per_sample,
            "nodes": nodes,
            "votes": {str(key): value for key, value in votes.items() if value},
            "selected_votes": votes[best_key],
        }
        return by_key[best_key]


def _entity_descriptor(game: DragonMirrorGame, entity_id: int | None) -> tuple:
    """Describe an action entity without relying on cross-sample entity IDs."""
    if entity_id is None:
        return ("none",)
    for player in game.players:
        for zone_name in ("hand", "board"):
            zone = getattr(player, zone_name)
            for position, card in enumerate(zone):
                if card.entity_id == entity_id:
                    duplicate = sum(
                        other.card_id == card.card_id
                        for other in zone[:position]
                    )
                    return (
                        zone_name, player.index, card.card_id, duplicate,
                    )
        for position, location in enumerate(player.locations):
            if location.entity_id == entity_id:
                return ("location", player.index, location.card_id, position)
    if game.pending_choice:
        for position, option in enumerate(game.pending_choice.get("options", ())):
            if getattr(option, "entity_id", None) == entity_id:
                return (
                    "choice", game.current, option.card_id,
                    tuple(getattr(option, "gifts", ())), position,
                )
    return ("literal", entity_id)


def information_action_key(game: DragonMirrorGame, action: Action) -> tuple:
    """Stable action identity used to merge different determinizations."""
    if action.kind in {"AMMUNITION_PICK", "CORPSE_SPEND"}:
        source = ("choice_value", action.source)
    else:
        source = _entity_descriptor(game, action.source)
    if action.target_player is not None and action.target_entity is None:
        target = ("hero", action.target_player)
    else:
        target = _entity_descriptor(game, action.target_entity)
    return (action.kind, source, target)


@dataclass
class _InformationNode:
    action_key: tuple | None = None
    prior: float = 0.0
    children: dict[tuple, "_InformationNode"] = field(default_factory=dict)
    visits: int = 0
    availability: int = 0
    value_sum: float = 0.0

    @property
    def mean_value(self) -> float:
        return self.value_sum / self.visits if self.visits else 0.0


class InformationSetMCTSPolicy:
    """Single-observer ISMCTS with one tree shared by public determinizations."""

    name = "shared-tree-ismcts-v1"
    information_mode = "public_dragon_mirror_v3"

    def __init__(
        self,
        samples: int = 4,
        iterations_per_sample: int = 8,
        tree_depth: int = 8,
        rollout_depth: int = 8,
        exploration: float = 1.25,
        seed: int = 20260909,
        policy_value_model=None,
        use_model_value: bool = True,
        force_uniform_expansion: bool = True,
        min_simulations_per_root_action: int = 0,
        max_total_iterations: int | None = None,
    ):
        if samples < 1 or iterations_per_sample < 1:
            raise ValueError("samples and iterations_per_sample must be positive")
        if tree_depth < 1 or rollout_depth < 0:
            raise ValueError("tree_depth must be positive and rollout_depth non-negative")
        if min_simulations_per_root_action < 0:
            raise ValueError("min simulations per root action must be non-negative")
        if max_total_iterations is not None and max_total_iterations < 1:
            raise ValueError("max total iterations must be positive")
        self.samples = samples
        self.iterations_per_sample = iterations_per_sample
        self.tree_depth = tree_depth
        self.rollout_depth = rollout_depth
        self.exploration = exploration
        self.seed = seed
        self.policy_value_model = policy_value_model
        self.use_model_value = use_model_value
        self.force_uniform_expansion = force_uniform_expansion
        self.min_simulations_per_root_action = min_simulations_per_root_action
        self.max_total_iterations = max_total_iterations
        self.decision_index = 0
        self.rollout_policy = HeuristicPolicy()
        self.last_search: dict[str, object] = {}

    @staticmethod
    def _legal_map(game: DragonMirrorGame) -> dict[tuple, Action]:
        result: dict[tuple, Action] = {}
        for action in game.legal_actions():
            key = information_action_key(game, action)
            if key in result:
                raise RuntimeError(f"information action collision: {key}")
            result[key] = action
        return result

    def choose(self, game: DragonMirrorGame) -> Action:
        legal = game.legal_actions()
        if not legal:
            raise RuntimeError("ISMCTS requested an action in a terminal state")
        if len(legal) == 1:
            self.last_search = {
                "iterations": 0, "root_actions": 1, "nodes": 1,
                "information_mode": self.information_mode,
                "root_policy": [1.0],
            }
            return legal[0]

        from .belief import PublicBelief

        root_player = game.current
        belief = PublicBelief.from_game(game, root_player)
        root = _InformationNode()
        nodes = 1
        configured_iterations = self.samples * self.iterations_per_sample
        adaptive_floor = len(legal) * self.min_simulations_per_root_action
        total_iterations = max(configured_iterations, adaptive_floor)
        if self.max_total_iterations is not None:
            total_iterations = min(
                total_iterations,
                max(configured_iterations, self.max_total_iterations),
            )
        seed_stride = (
            max(configured_iterations, self.max_total_iterations or 4096)
            if self.min_simulations_per_root_action
            else configured_iterations
        )
        seed_base = self.seed + self.decision_index * seed_stride
        for iteration in range(total_iterations):
            state = belief.sample_determinization(
                game, seed=seed_base + iteration
            )
            node = root
            path = [root]
            for depth in range(self.tree_depth):
                if state.finished:
                    break
                legal_map = self._legal_map(state)
                if not legal_map:
                    break
                legal_items = list(legal_map.items())
                priors: dict[tuple, float] = {}
                if self.policy_value_model is not None:
                    prediction = self.policy_value_model.predict(
                        state, [action for _, action in legal_items]
                    )
                    priors = {
                        key: float(prior)
                        for (key, _), prior in zip(
                            legal_items, prediction.priors, strict=True
                        )
                    }
                available_children = [
                    child for key, child in node.children.items()
                    if key in legal_map
                ]
                for child in available_children:
                    child.availability += 1
                unexpanded = [
                    action for key, action in legal_map.items()
                    if key not in node.children
                ]
                if (
                    self.policy_value_model is not None
                    and not self.force_uniform_expansion
                ):
                    # PUCT must be allowed to revisit a high-prior action before
                    # every legal action has received one visit.  Forcing one
                    # visit per action makes low-budget searches nearly uniform
                    # whenever the branching factor approaches the simulation
                    # count, effectively discarding the learned prior.
                    for action in unexpanded:
                        key = information_action_key(state, action)
                        child = _InformationNode(
                            action_key=key, availability=1,
                            prior=priors.get(key, 0.0),
                        )
                        node.children[key] = child
                        available_children.append(child)
                        nodes += 1
                elif unexpanded:
                    if self.policy_value_model is not None:
                        ordered = sorted(
                            unexpanded,
                            key=lambda action: (
                                -priors[information_action_key(state, action)],
                                information_action_key(state, action),
                            ),
                        )
                    else:
                        ordered = sorted(
                            unexpanded,
                            key=lambda action: (
                                -self.rollout_policy.score(state, action),
                                information_action_key(state, action),
                            ),
                        )
                    action = ordered[0]
                    key = information_action_key(state, action)
                    child = _InformationNode(
                        action_key=key, availability=1,
                        prior=priors.get(key, 0.0),
                    )
                    node.children[key] = child
                    nodes += 1
                    state.step(action)
                    node = child
                    path.append(node)
                    break
                if depth == 0 and self.min_simulations_per_root_action:
                    minimum_visits = min(
                        child.visits for child in available_children
                    )
                    if minimum_visits < self.min_simulations_per_root_action:
                        undercovered = [
                            child for child in available_children
                            if child.visits == minimum_visits
                        ]
                        child = max(
                            undercovered,
                            key=lambda item: (
                                item.prior
                                if self.policy_value_model is not None
                                else self.rollout_policy.score(
                                    state, legal_map[item.action_key]
                                ),
                                item.action_key,
                            ),
                        )
                        state.step(legal_map[child.action_key])
                        node = child
                        path.append(node)
                        break
                direction = 1.0 if state.current == root_player else -1.0
                log_parent = math.log(max(1, node.visits))
                child = max(
                    available_children,
                    key=lambda item: (
                        direction * item.mean_value
                        + (
                            self.exploration * item.prior
                            * math.sqrt(max(1, node.visits))
                            / (1 + item.visits)
                            if self.policy_value_model is not None
                            else self.exploration * math.sqrt(
                                log_parent / max(1, item.availability)
                            )
                        ),
                        item.action_key,
                    ),
                )
                state.step(legal_map[child.action_key])
                node = child
                path.append(node)
                if child.visits == 0:
                    break
            if self.policy_value_model is not None and self.use_model_value:
                if state.finished:
                    value = evaluate_state(state, root_player)
                else:
                    leaf = self.policy_value_model.predict(
                        state, state.legal_actions()
                    ).value
                    value = leaf if state.current == root_player else -leaf
            else:
                rollout = state.clone()
                for _ in range(self.rollout_depth):
                    if rollout.finished:
                        break
                    rollout.step(self.rollout_policy.choose(rollout))
                value = evaluate_state(rollout, root_player)
            for visited in path:
                visited.visits += 1
                visited.value_sum += value

        root_map = self._legal_map(game)
        available_root = [
            child for key, child in root.children.items() if key in root_map
        ]
        best = max(
            available_root,
            key=lambda child: (
                child.visits, child.mean_value, child.action_key,
            ),
        )
        root_visits = [
            root.children.get(information_action_key(game, action), _InformationNode()).visits
            for action in legal
        ]
        visit_total = sum(root_visits)
        root_policy = [
            visits / visit_total if visit_total else 1.0 / len(legal)
            for visits in root_visits
        ]
        root_action_stats = []
        for action, visit_share in zip(legal, root_policy, strict=True):
            child = root.children.get(information_action_key(game, action))
            root_action_stats.append({
                "visits": 0 if child is None else child.visits,
                "availability": 0 if child is None else child.availability,
                "mean_value": 0.0 if child is None else child.mean_value,
                "prior": 0.0 if child is None else child.prior,
                "visit_share": visit_share,
                "selected": child is best,
            })
        self.decision_index += 1
        self.last_search = {
            "information_mode": self.information_mode,
            "iterations": total_iterations,
            "configured_iterations": configured_iterations,
            "adaptive_iterations": total_iterations - configured_iterations,
            "min_simulations_per_root_action": self.min_simulations_per_root_action,
            "minimum_root_action_visits_achieved": min(root_visits),
            "max_total_iterations": self.max_total_iterations,
            "determinizations": total_iterations,
            "root_actions": len(legal),
            "root_children": len(root.children),
            "nodes": nodes,
            "selected_visits": best.visits,
            "selected_value": best.mean_value,
            "root_policy": root_policy,
            "root_action_stats": root_action_stats,
            "policy_value_model": (
                getattr(self.policy_value_model, "name", None)
            ),
            "leaf_value_source": (
                "model" if self.policy_value_model is not None and self.use_model_value
                else "heuristic_rollout"
            ),
            "expansion_mode": (
                "force_unvisited"
                if self.policy_value_model is not None and self.force_uniform_expansion
                else "puct_prior"
                if self.policy_value_model is not None
                else "uct"
            ),
        }
        return root_map[best.action_key]

"""MCTS baselines and single-observer, public-belief ISMCTS/PUCT.

MCTSPolicy is a full-state debugging baseline. InformationSetMCTSPolicy samples
unknown order and future chance independently, and separates observed outcomes.
Neither the legacy baseline nor the partial public-belief model is a claim of
complete hidden-information support for every Standard mechanic.
"""

from __future__ import annotations

import math
import json
import random
import hashlib
from collections import Counter
from dataclasses import dataclass, field, fields, is_dataclass

from .dragon_mirror import Action, DragonMirrorGame
from .policy import HeuristicPolicy, _card_value
from .policy_value import PolicyValueOutput


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
        # Optional runtime-only branch states for an independent continuation
        # teacher. Keep game objects out of last_search, which is serializable
        # and consumed by diagnostics/live recommendation code.
        self.conditional_training_states: list[dict[str, object]] = []

    def choose(self, game: DragonMirrorGame) -> Action:
        legal = game.legal_actions()
        if not legal:
            raise RuntimeError("MCTS requested an action in a terminal state")
        if len(legal) == 1:
            self.last_search = {"iterations": 0, "root_actions": 1, "nodes": 1}
            return legal[0]
        root_player = game.current
        root = _Node(
            game.clone(record_events=False),
            untried=self._ordered_actions(game, legal),
        )
        nodes = 1
        for _ in range(self.iterations):
            node = root
            while not node.state.finished and not node.untried and node.children:
                node = self._select_child(node, root_player)
            if not node.state.finished and node.untried:
                action = node.untried.pop(0)
                try:
                    child_state = node.state.branch(action)
                except ValueError:
                    # The action generator intentionally stays broad, while
                    # card rules may reject a target at resolution time.
                    # Discard that branch and spend this iteration elsewhere.
                    continue
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
        if not root.children:
            return legal[0]
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
        # Rollouts are search-only branches.  Keep event recording disabled so
        # the clone stays on the compact copy path even if a caller supplied a
        # diagnostic state with event recording enabled.  Rollout history is
        # never part of the value target and only increases deepcopy cost.
        rollout = state.clone(record_events=False)
        for _ in range(self.rollout_depth):
            if rollout.finished:
                break
            try:
                rollout.step(self.rollout_policy.choose(rollout))
            except ValueError:
                # Some card-specific predicates are stricter than the broad
                # action generator (for example, a spell requiring a damaged
                # target).  Treat an invalid sampled branch as a truncated
                # rollout instead of aborting the entire search.
                break
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
            state = belief.sample_determinization(
                game, seed=sample_seed, record_event=False
            )
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
    prior_value: float = 0.0
    prior_value_weight: float = 0.0
    children: dict[tuple, "_InformationNode"] = field(default_factory=dict)
    outcomes: dict[str, "_InformationNode"] = field(default_factory=dict)
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

    @staticmethod
    def _uct_bonus(child: _InformationNode) -> float:
        # ISUCT: availability supplies the parent count; actual selections
        # supply the denominator. Using availability in the denominator
        # made unvisited/underexplored actions lose their exploration bonus.
        return math.sqrt(math.log(max(1, child.availability)) / max(1, child.visits))

    @staticmethod
    def _root_outcome_coverage(child: _InformationNode) -> int:
        # A terminal root action has no continuation observations. In that
        # case its actual samples, rather than a permanently missing branch,
        # supply coverage. Nonterminal actions acquire outcomes on revisits.
        return min((node.visits for node in child.outcomes.values()), default=child.visits)

    @staticmethod
    def _followup_diagnostics(child, root_player, root_turn):
        if child is None:
            return []
        result = []
        for observation, node in child.outcomes.items():
            view = json.loads(observation)
            # Never export the sampled enemy's private hand-action keys.
            if view["current"] != root_player or view["turn"] != root_turn:
                continue
            own_hand = view["players"][root_player]["hand"]
            candidates = sorted(node.children.values(),
                                key=lambda n: (n.visits, n.mean_value), reverse=True)
            result.append({
                "observation_sha256": hashlib.sha256(observation.encode()).hexdigest(),
                "visits": node.visits,
                # This is the acting player's visible hand; retaining the IDs
                # lets an offline audit see which random draw changed the
                # available continuation without exporting enemy-private data.
                "own_hand_card_ids": sorted(card["id"] for card in own_hand),
                "top_actions": [{"information_action_key": n.action_key,
                                 "visits": n.visits, "mean_value": n.mean_value,
                                 "prior": n.prior} for n in candidates[:5]],
            })
        return result

    @staticmethod
    def _observation_key(game: DragonMirrorGame, observer: int | None = None) -> str:
        """Separate continuations after different *observed* random outcomes.

        Action-only trees previously merged 'generated dragon A' and 'dragon
        B', including one immutable prior for their common follow-up actions.
        Never use the full game/RNG/deck state as a decision-node key.
        """
        observer = game.current if observer is None else observer
        view = game.observation(observer)
        # Snapshot contains some audit-only fields that are not public.
        allowed = {
            "player", "health", "max_health", "armor", "mana", "max_mana",
            "hand", "board", "locations", "weapon", "deck_count", "fatigue",
            "hero_attack", "hero_power_used", "corpses", "herald_count",
            "active_quests", "completed_quests", "overload_next_turn", "locked_mana",
            "cards_played_this_turn", "spell_damage", "hero_immune", "frozen",
        }
        players = [{key: value for key, value in p.items() if key in allowed}
                   for p in view["players"]]
        def strip_ids(value):
            if is_dataclass(value) and not isinstance(value, type):
                return {
                    item.name: strip_ids(getattr(value, item.name))
                    for item in fields(value)
                    if item.name not in {"entity_id", "colossal_parent_entity"}
                }
            if isinstance(value, dict):
                return {k: strip_ids(v) for k, v in value.items()
                        if k not in {"entity", "colossal_parent_entity"}}
            if isinstance(value, (list, tuple)):
                return [strip_ids(v) for v in value]
            if isinstance(value, (set, frozenset)):
                return sorted(
                    (strip_ids(v) for v in value), key=repr
                )
            return value
        return json.dumps(strip_ids({
            "turn": game.turn, "current": game.current, "players": players,
            "pending": view["pending_choice"],
        }), sort_keys=True, separators=(",", ":"))

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
        root_perspective_model_value: bool | None = None,
        force_uniform_expansion: bool = True,
        min_simulations_per_root_action: int = 0,
        max_total_iterations: int | None = None,
        neural_prior_depth: int | None = None,
        tactical_precheck: bool = True,
        model_rollout_depth: int = 0,
        use_action_value_estimates: bool = False,
        action_value_prior_weight: float = 2.0,
        prior_temperature: float = 1.0,
        prior_uniform_mix: float = 0.0,
        heuristic_prior_mix: float = 0.0,
        min_visits_per_root_outcome: int = 0,
        min_visits_per_observed_action: int = 0,
        collect_plan_diagnostics: bool = False,
        collect_conditional_training_examples: bool = False,
        conditional_training_min_visits: int = 8,
        conditional_training_max_branches: int = 2,
    ):
        if samples < 1 or iterations_per_sample < 1:
            raise ValueError("samples and iterations_per_sample must be positive")
        if tree_depth < 1 or rollout_depth < 0:
            raise ValueError("tree_depth must be positive and rollout_depth non-negative")
        if min_simulations_per_root_action < 0:
            raise ValueError("min simulations per root action must be non-negative")
        if max_total_iterations is not None and max_total_iterations < 1:
            raise ValueError("max total iterations must be positive")
        if neural_prior_depth is not None and neural_prior_depth < 1:
            raise ValueError("neural_prior_depth must be positive or None")
        if model_rollout_depth < 0:
            raise ValueError("model rollout depth must be non-negative")
        if not math.isfinite(action_value_prior_weight) or action_value_prior_weight < 0:
            raise ValueError("action-value prior weight must be finite and non-negative")
        if not math.isfinite(prior_temperature) or prior_temperature <= 0:
            raise ValueError("prior temperature must be finite and positive")
        if not math.isfinite(prior_uniform_mix) or not 0.0 <= prior_uniform_mix <= 1.0:
            raise ValueError("uniform prior mix must be finite and between zero and one")
        if not math.isfinite(heuristic_prior_mix) or not 0.0 <= heuristic_prior_mix <= 1.0:
            raise ValueError("heuristic prior mix must be finite and between zero and one")
        if min_visits_per_root_outcome < 0:
            raise ValueError("minimum root outcome visits must be non-negative")
        if min_visits_per_root_outcome and tree_depth < 2:
            raise ValueError("root outcome coverage requires tree depth >= 2")
        if min_visits_per_observed_action < 0:
            raise ValueError("minimum observed action visits must be non-negative")
        if conditional_training_min_visits < 1:
            raise ValueError("conditional training minimum visits must be positive")
        if conditional_training_max_branches < 1:
            raise ValueError("conditional training maximum branches must be positive")
        if min_visits_per_observed_action and tree_depth < 3:
            raise ValueError("observed action coverage requires tree depth >= 3")
        self.samples = samples
        self.iterations_per_sample = iterations_per_sample
        self.tree_depth = tree_depth
        self.rollout_depth = rollout_depth
        self.exploration = exploration
        self.seed = seed
        self.policy_value_model = policy_value_model
        self.use_model_value = use_model_value
        self.root_perspective_model_value = (
            bool(getattr(policy_value_model, "root_perspective_value", False))
            if root_perspective_model_value is None
            else root_perspective_model_value
        )
        self.force_uniform_expansion = force_uniform_expansion
        self.min_simulations_per_root_action = min_simulations_per_root_action
        self.max_total_iterations = max_total_iterations
        self.neural_prior_depth = neural_prior_depth
        self.tactical_precheck = tactical_precheck
        self.model_rollout_depth = model_rollout_depth
        self.use_action_value_estimates = use_action_value_estimates
        self.action_value_prior_weight = action_value_prior_weight
        self.prior_temperature = prior_temperature
        self.prior_uniform_mix = prior_uniform_mix
        self.heuristic_prior_mix = heuristic_prior_mix
        self.min_visits_per_root_outcome = min_visits_per_root_outcome
        self.min_visits_per_observed_action = min_visits_per_observed_action
        self.collect_plan_diagnostics = collect_plan_diagnostics
        self.collect_conditional_training_examples = collect_conditional_training_examples
        self.conditional_training_min_visits = conditional_training_min_visits
        self.conditional_training_max_branches = conditional_training_max_branches
        self.search_rules_version = (
            "chance_candidates_conditional_action_coverage_v8"
            if min_visits_per_observed_action else
            "chance_candidates_outcome_coverage_v6"
            if min_visits_per_root_outcome else "chance_candidates_terminal_v5"
        )
        self.decision_index = 0
        self.rollout_policy = HeuristicPolicy()
        self.last_search: dict[str, object] = {}

    def _calibrate_priors(self, priors) -> list[float]:
        """Flatten/sharpen network priors without changing the default policy."""
        values = [max(0.0, float(value)) for value in priors]
        if not values:
            return []
        if not all(math.isfinite(value) for value in values):
            raise ValueError("policy priors must be finite")
        if self.prior_temperature != 1.0:
            exponent = 1.0 / self.prior_temperature
            values = [value ** exponent for value in values]
        total = sum(values)
        if total <= 0:
            return [1.0 / len(values)] * len(values)
        normalized = [value / total for value in values]
        if self.prior_uniform_mix:
            uniform = 1.0 / len(normalized)
            normalized = [
                (1.0 - self.prior_uniform_mix) * value
                + self.prior_uniform_mix * uniform
                for value in normalized
            ]
        return normalized

    def _blend_heuristic_priors(self, game, legal_items, priors):
        """Blend a small, auditable heuristic correction into neural priors.

        The correction is deliberately opt-in.  It is useful for catching
        obviously harmful target choices (for example direct damage aimed at
        the friendly hero) while preserving the neural policy as the primary
        signal.  Scores are converted with a temperature-like scale instead
        of used as raw logits because the heuristic contains lethal bonuses.
        """
        mix = self.heuristic_prior_mix
        if not mix or not legal_items or len(priors) != len(legal_items):
            return priors
        scores = [self.rollout_policy.score(game, action) for _, action in legal_items]
        top = max(scores)
        weights = [math.exp(max(-60.0, (score - top) / 50.0)) for score in scores]
        total = sum(weights)
        if total <= 0.0 or not math.isfinite(total):
            return priors
        heuristic = [weight / total for weight in weights]
        return [
            (1.0 - mix) * prior + mix * correction
            for prior, correction in zip(priors, heuristic, strict=True)
        ]

    @staticmethod
    def _legal_map_from_actions(
        game: DragonMirrorGame, actions: list[Action] | tuple[Action, ...]
    ) -> dict[tuple, Action]:
        result: dict[tuple, Action] = {}
        for action in actions:
            base_key = information_action_key(game, action)
            key = base_key
            # A few generated/choice actions can be semantically identical
            # after hiding entity ids.  Identical duplicates do not represent
            # two choices and are safely collapsed; genuinely different
            # concrete actions retain a deterministic tie-breaker instead of
            # aborting the whole game.
            if key in result:
                if result[key].key() == action.key():
                    continue
                # Keep the first three fields identical to the normal key so
                # tuple ordering in PUCT tie-breaks remains well-defined.
                key = (*base_key, "concrete", action.key())
                suffix = 1
                while key in result:
                    key = (*base_key, "concrete", action.key(), suffix)
                    suffix += 1
            result[key] = action
        return result

    @classmethod
    def _legal_map(cls, game: DragonMirrorGame) -> dict[tuple, Action]:
        return cls._legal_map_from_actions(game, game.legal_actions())

    @staticmethod
    def _conditional_root_action_label(
        game: DragonMirrorGame,
        root_legal_map: dict[tuple, Action],
        path: list[_InformationNode],
    ) -> str:
        """Describe a root move without failing on determinization-only keys."""
        key = path[1].action_key if len(path) > 1 else None
        action = root_legal_map.get(key)
        if action is not None:
            return game.describe_action(action)
        # A sampled choice can expose a concrete action key absent from the
        # observed root map. Keep the conditional label and record the mismatch
        # rather than aborting an otherwise valid teacher game.
        return f"[unmapped root action] {key!r}"

    def choose(
        self,
        game: DragonMirrorGame,
        *,
        root_prediction: PolicyValueOutput | None = None,
        root_actions: tuple[Action, ...] | None = None,
    ) -> Action:
        self.conditional_training_states = []
        # A batched actor has already materialized these actions to encode its
        # root policy request. Reusing the exact tuple avoids a second target
        # enumeration (which can be expensive on wide boards) and guarantees
        # the injected prediction has the same action ordering.
        original_legal = list(root_actions) if root_actions is not None else game.legal_actions()
        root_legal_map = self._legal_map_from_actions(game, original_legal)
        legal = list(root_legal_map.values())
        if not legal:
            raise RuntimeError("ISMCTS requested an action in a terminal state")
        if len(legal) == 1:
            self.last_search = {
                "iterations": 0, "root_actions": 1, "nodes": 1,
                "information_mode": self.information_mode,
                "search_rules_version": self.search_rules_version,
                "selection_source": "single_legal_action",
                "root_action_keys": [action.key() for action in legal],
                "root_policy": [1.0],
            }
            return legal[0]

        from .belief import PublicBelief

        root_player = game.current
        belief = PublicBelief.from_game(game, root_player)
        if self.tactical_precheck:
            from .tactical_lethal import (
                find_face_attack_lethal, find_same_turn_lethal,
            )
            witness = find_face_attack_lethal(game, root_actions=legal)
            tactical_scope = "deterministic_public_face_attacks"
            if witness is None:
                tactical_state = belief.sample_determinization(
                    game, seed=self.seed + self.decision_index, record_event=False)
                witness = find_same_turn_lethal(tactical_state, root_actions=legal)
                tactical_scope = "primitive_spells_empty_board_public_face_attacks"
            if witness is not None:
                first = witness.actions[0]
                index = next(i for i, action in enumerate(legal) if action.key() == first.key())
                self.last_search = {
                    "information_mode": self.information_mode,
                    "search_rules_version": self.search_rules_version,
                    "iterations": 0, "root_actions": len(legal), "nodes": witness.nodes,
                    "root_action_keys": [action.key() for action in legal],
                    "selected_value": 1.0, "selected_visits": 0,
                    "root_policy": [float(i == index) for i in range(len(legal))],
                    "root_action_stats": [{"visits": 0, "availability": 0,
                        "mean_value": 1.0 if i == index else 0.0, "prior": 0.0,
                        "value_available": i == index,
                        "visit_share": float(i == index), "selected": i == index}
                        for i in range(len(legal))],
                    "selection_source": (
                        "bounded_face_attack_terminal"
                        if tactical_scope == "deterministic_public_face_attacks"
                        else "bounded_same_turn_terminal"
                    ),
                    "terminal_sequence": [dict(kind=a.kind, source=a.source,
                        target_player=a.target_player, target_entity=a.target_entity)
                        for a in witness.actions],
                    "tactical_scope": tactical_scope,
                    "tactical_precheck": True,
                }
                self.decision_index += 1
                return legal[index]
        root = _InformationNode()
        nodes = 1
        outcome_branches = 0
        tactical_leaf_hits = 0
        tactical_nodes = 0
        forced_root_samples = Counter()
        forced_observed_samples = Counter()
        forced_observed_root_samples = Counter()
        forced_root_policy_samples = Counter()
        root_leaf_diagnostics = {
            key: {name: Counter() for name in ("tree_depth_counts", "turn_delta_counts",
                                               "rollout_step_counts", "value_source_counts")}
            for key in root_legal_map
        }
        conditional_snapshots = {}
        invalid_determinization_actions = 0
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
        # At the root, the actor's visible state is identical across all
        # determinizations.  A root-only policy prior may therefore be safely
        # reused while the deeper tree remains heuristic/UCT guided.
        if root_prediction is not None and len(root_prediction.priors) == len(legal):
            calibrated_root_priors = self._calibrate_priors(root_prediction.priors)
            calibrated_root_priors = self._blend_heuristic_priors(
                game,
                list(root_legal_map.items()),
                calibrated_root_priors,
            )
            root_priors: dict[tuple, float] | None = {
                key: float(prior)
                for (key, _), prior in zip(
                    root_legal_map.items(), calibrated_root_priors, strict=True
                )
            }
        else:
            # Batched callers may have predicted before duplicate information
            # actions were collapsed.  Falling back to uniform/heuristic priors
            # is safer than rejecting an otherwise valid game.
            root_priors = None
        root_action_values: dict[tuple, float] = {}
        if (self.use_action_value_estimates and root_prediction is not None
                and len(root_prediction.action_values) == len(legal)):
            root_action_values = {
                key: float(value)
                for (key, _), value in zip(
                    root_legal_map.items(), root_prediction.action_values, strict=True
                )
            }
        for iteration in range(total_iterations):
            iteration_forced_coverage = False
            rollout_rng = random.Random(f"{seed_base + iteration}:policy-rollout")
            state = belief.sample_determinization(
                game, seed=seed_base + iteration, record_event=False
            )
            node = root
            path = [root]
            for depth in range(self.tree_depth):
                if state.finished:
                    break
                if depth:
                    observation_key = self._observation_key(state, root_player)
                    if observation_key not in node.outcomes:
                        node.outcomes[observation_key] = _InformationNode()
                        outcome_branches += 1
                        nodes += 1
                    node = node.outcomes[observation_key]
                    path.append(node)
                # Determinization normally only replaces the opponent's hidden
                # zones, so a non-choice root can reuse its already encoded
                # action map. Dynamic choice options are the exception: build
                # their map per sampled state and only reuse priors if keys
                # still match the visible root exactly.
                if depth == 0 and game.pending_choice is None:
                    legal_map = root_legal_map
                    root_actions_match = True
                else:
                    legal_map = self._legal_map(state)
                    root_actions_match = (
                        depth == 0
                        and legal_map.keys() == root_legal_map.keys()
                    )
                if not legal_map:
                    break
                legal_items = list(legal_map.items())
                action_key_by_concrete = {
                    action.key(): key for key, action in legal_items
                }
                # Capture a decision after any observed stochastic action in
                # the current turn, not only after the root action. ``path[-2]``
                # is the action node whose outcome branch we just entered;
                # keeping the full action path prevents merging states that
                # happen to have the same visible board after different lines.
                observed_outcome_branch = (
                    depth > 0 and len(path) >= 2 and len(path[-2].outcomes) > 1
                )
                if (
                    self.collect_conditional_training_examples
                    and observed_outcome_branch
                    and state.current == root_player
                    and state.turn == game.turn
                    and node.visits + 1 >= self.conditional_training_min_visits
                ):
                    from .encoding import encode_action, encode_state
                    action_path = tuple(
                        item.action_key for item in path if item.action_key is not None
                    )
                    snapshot_key = (action_path, observation_key)
                    if (
                        snapshot_key not in conditional_snapshots
                        and len(conditional_snapshots)
                        < self.conditional_training_max_branches
                    ):
                        conditional_snapshots[snapshot_key] = {
                            "state": list(encode_state(state, root_player)),
                            "actions": [
                                list(encode_action(state, action))
                                for _, action in legal_items
                            ],
                            "action_keys": [key for key, _ in legal_items],
                            "game": state.clone(record_events=False),
                            "branch": node,
                            "root_action": self._conditional_root_action_label(
                                game, root_legal_map, path,
                            ),
                            "trigger_depth": depth,
                            "observation_visits": node.visits + 1,
                        }

                def key_for_action(action: Action) -> tuple:
                    return action_key_by_concrete.get(
                        action.key(), information_action_key(state, action)
                    )
                conditional_coverage = (
                    self.min_visits_per_observed_action > 0
                    and observed_outcome_branch
                    and state.current == root_player
                    and state.turn == game.turn
                    and len(path) > 1
                )
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
                # A child's prior is immutable once it is expanded.  Re-running
                # the policy network on every revisit used to dominate NPU time
                # despite PUCT consuming only ``child.prior`` below.  A new
                # forward pass is needed only when a determinization exposes a
                # previously unseen legal action.
                priors: dict[tuple, float] = {}
                action_values: dict[tuple, float] = {}
                use_neural_prior = (
                    self.policy_value_model is not None
                    and (
                        self.neural_prior_depth is None
                        or depth < self.neural_prior_depth
                    )
                )
                if use_neural_prior and unexpanded:
                    if (
                        depth == 0
                        and root_actions_match
                        and root_priors is not None
                    ):
                        priors = root_priors
                    else:
                        prediction = self.policy_value_model.predict(
                            state, [action for _, action in legal_items]
                        )
                        priors = {
                            key: float(prior)
                            for (key, _), prior in zip(
                                legal_items,
                                self._calibrate_priors(prediction.priors),
                                strict=True,
                            )
                        }
                        calibrated = self._blend_heuristic_priors(
                            state,
                            legal_items,
                            [priors[key] for key, _ in legal_items],
                        )
                        priors = {
                            key: prior
                            for (key, _), prior in zip(
                                legal_items, calibrated, strict=True
                            )
                        }
                        if depth == 0 and root_actions_match:
                            root_priors = priors
                        if (self.use_action_value_estimates
                                and len(prediction.action_values) == len(legal_items)):
                            direction_to_root = (
                                1.0 if state.current == root_player else -1.0
                            )
                            action_values = {
                                key: direction_to_root * float(value)
                                for (key, _), value in zip(
                                    legal_items, prediction.action_values, strict=True
                                )
                            }
                            if depth == 0 and root_actions_match:
                                root_action_values = action_values
                if (depth == 0 and root_actions_match and root_action_values
                        and not action_values):
                    action_values = root_action_values
                if (
                    self.policy_value_model is not None
                    and not self.force_uniform_expansion
                ):
                    # PUCT must be allowed to revisit a high-prior action before
                    # every legal action has received one visit.  Forcing one
                    # visit per action makes low-budget searches nearly uniform
                    # whenever the branching factor approaches the simulation
                    # count, effectively discarding the learned prior.
                    for key, action in (
                        (key, action) for key, action in legal_items
                        if key not in node.children
                    ):
                        child = _InformationNode(
                            action_key=key, availability=1,
                            prior=(
                                priors.get(key, 0.0)
                                if use_neural_prior else 1.0 / len(legal_items)
                            ),
                            prior_value=action_values.get(key, 0.0),
                            prior_value_weight=(
                                self.action_value_prior_weight
                                if key in action_values else 0.0
                            ),
                        )
                        node.children[key] = child
                        available_children.append(child)
                        nodes += 1
                elif unexpanded:
                    if use_neural_prior:
                        action = min(
                            unexpanded,
                            key=lambda action: (
                                -priors.get(key_for_action(action), 0.0),
                                key_for_action(action),
                            ),
                        )
                    else:
                        action = min(
                            unexpanded,
                            key=lambda action: (
                                -self.rollout_policy.score(state, action),
                                key_for_action(action),
                            ),
                        )
                    key = key_for_action(action)
                    child = _InformationNode(
                        action_key=key, availability=1,
                        prior=(
                            priors.get(key, 0.0)
                            if use_neural_prior else 1.0 / len(legal_items)
                        ),
                        prior_value=action_values.get(key, 0.0),
                        prior_value_weight=(
                            self.action_value_prior_weight
                            if key in action_values else 0.0
                        ),
                    )
                    node.children[key] = child
                    nodes += 1
                    try:
                        state.step(action)
                    except ValueError:
                        # An information-set child can be legal in one
                        # determinization yet become unplayable in another
                        # after a hidden/random choice rewrites its concrete
                        # target.  It is not a simulator crash: discard this
                        # just-expanded child for the sampled branch.
                        node.children.pop(key, None)
                        invalid_determinization_actions += 1
                        break
                    node = child
                    path.append(node)
                    if conditional_coverage:
                        forced_observed_samples[(id(path[-2]), key)] += 1
                        forced_observed_root_samples[path[1].action_key] += 1
                        iteration_forced_coverage = True
                        continue
                    break
                if conditional_coverage:
                    undercovered_actions = []
                    for key, action in legal_items:
                        child = node.children.get(key)
                        selected_visits = 0 if child is None else child.visits
                        if selected_visits < self.min_visits_per_observed_action:
                            undercovered_actions.append((
                                selected_visits,
                                -(priors.get(key, child.prior if child else 0.0)),
                                key,
                                action,
                            ))
                    if undercovered_actions:
                        _, _, key, action = min(undercovered_actions)
                        child = node.children.get(key)
                        if child is None:
                            child = _InformationNode(
                                action_key=key,
                                prior=priors.get(key, 1.0 / len(legal_items)),
                            )
                            node.children[key] = child
                            available_children.append(child)
                            nodes += 1
                        try:
                            state.step(action)
                        except ValueError:
                            invalid_determinization_actions += 1
                            break
                        forced_observed_samples[(id(node), key)] += 1
                        forced_observed_root_samples[path[1].action_key] += 1
                        iteration_forced_coverage = True
                        node = child
                        path.append(node)
                        continue
                if depth == 0 and (self.min_simulations_per_root_action or self.min_visits_per_root_outcome):
                    undercovered = [child for child in available_children if (
                        child.visits < self.min_simulations_per_root_action
                        or self._root_outcome_coverage(child) < self.min_visits_per_root_outcome)]
                    if undercovered:
                        child = max(
                            undercovered,
                            key=lambda item: (
                                -(item.visits if item.visits < self.min_simulations_per_root_action
                                  else self._root_outcome_coverage(item)),
                                item.prior
                                if self.policy_value_model is not None
                                else self.rollout_policy.score(
                                    state, legal_map[item.action_key]
                                ),
                                item.action_key,
                            ),
                        )
                        try:
                            state.step(legal_map[child.action_key])
                        except ValueError:
                            child.availability = max(0, child.availability - 1)
                            invalid_determinization_actions += 1
                            break
                        node = child
                        path.append(node)
                        forced_root_samples[child.action_key] += 1
                        iteration_forced_coverage = True
                        # Coverage chooses the root action; it must not
                        # truncate every revisit immediately after that action.
                        # Continue into its observed outcome so forced samples
                        # can learn the next decision (including after reveals).
                        continue
                direction = 1.0 if state.current == root_player else -1.0
                noncoverage_root = depth == 0 and self.min_visits_per_root_outcome > 0
                if noncoverage_root:
                    selection_parent_visits = node.visits - sum(forced_root_policy_samples.values())
                elif conditional_coverage:
                    selection_parent_visits = node.visits - sum(
                        forced_observed_samples[(id(node), key)] for key in node.children
                    )
                else:
                    selection_parent_visits = node.visits

                def selection_count(item):
                    if noncoverage_root:
                        return item.visits - forced_root_policy_samples[item.action_key]
                    if conditional_coverage:
                        return item.visits - forced_observed_samples[(id(node), item.action_key)]
                    return item.visits

                def selection_value(item):
                    prior_weight = item.prior_value_weight
                    denominator = item.visits + prior_weight
                    return (
                        (item.value_sum + prior_weight * item.prior_value) / denominator
                        if denominator else 0.0
                    )

                child = max(
                    available_children,
                    key=lambda item: (
                        direction * selection_value(item)
                        + (
                            self.exploration * item.prior
                            * math.sqrt(max(1, selection_parent_visits))
                            / (1 + selection_count(item))
                            if self.policy_value_model is not None
                            else self.exploration * (
                                math.sqrt(math.log(max(1, item.availability)) / max(1, selection_count(item)))
                                if noncoverage_root else self._uct_bonus(item))
                        ),
                        item.action_key,
                    ),
                )
                try:
                    state.step(legal_map[child.action_key])
                except ValueError:
                    child.availability = max(0, child.availability - 1)
                    invalid_determinization_actions += 1
                    break
                node = child
                path.append(node)
                if child.visits == 0:
                    break
            leaf_witness = None
            tree_steps = sum(visited.action_key is not None for visited in path)
            rollout_steps = 0
            if self.tactical_precheck and not state.finished:
                from .tactical_lethal import find_same_turn_lethal
                leaf_witness = find_same_turn_lethal(state, max_nodes=32)
            if leaf_witness is not None:
                tactical_leaf_hits += 1
                tactical_nodes += leaf_witness.nodes
                value = 1.0 if state.current == root_player else -1.0
                value_source = "terminal_proof"
            elif self.policy_value_model is not None and self.use_model_value:
                # Optional policy rollout resolves newly observed choices and
                # same-turn continuations before asking the value head. Chance
                # outcomes stay sampled; this is not an information-first rule.
                rollout_actor, rollout_turn = state.current, state.turn
                for _ in range(self.model_rollout_depth):
                    if (state.finished or state.current != rollout_actor
                            or state.turn != rollout_turn):
                        break
                    rollout_actions = state.legal_actions()
                    prediction = self.policy_value_model.predict(state, rollout_actions)
                    weights = [max(0.0, float(p)) for p in prediction.priors]
                    if len(weights) != len(rollout_actions):
                        raise ValueError("model rollout priors must match legal actions")
                    if not all(math.isfinite(float(p)) for p in prediction.priors):
                        raise ValueError("model rollout priors must be finite")
                    if not any(weights):
                        weights = [1.0] * len(rollout_actions)
                    rollout_action = rollout_rng.choices(rollout_actions, weights=weights, k=1)[0]
                    state.step(rollout_action)
                    rollout_steps += 1
                if state.finished:
                    value = evaluate_state(state, root_player)
                    value_source = "terminal"
                else:
                    if self.root_perspective_model_value:
                        predict_value = getattr(
                            self.policy_value_model, "predict_value", None
                        )
                        if predict_value is None:
                            raise TypeError(
                                "root-perspective model values require predict_value(game, observer)"
                            )
                        value = float(predict_value(state, root_player))
                    else:
                        leaf = self.policy_value_model.predict(
                            state, state.legal_actions()
                        ).value
                        value = leaf if state.current == root_player else -leaf
                    value_source = "model"
            else:
                # ``state`` is a per-iteration determinization. Once tree
                # descent is complete, nothing below needs its pre-rollout
                # contents: backpropagation only consumes ``path`` and the
                # scalar result. Roll out in-place instead of paying for one
                # additional full GameState copy per simulation.
                rollout = state
                for _ in range(self.rollout_depth):
                    if rollout.finished:
                        break
                    try:
                        rollout.step(self.rollout_policy.choose(rollout))
                        rollout_steps += 1
                    except ValueError:
                        break
                value = evaluate_state(rollout, root_player)
                value_source = "terminal" if rollout.finished else "heuristic"
            if len(path) > 1 and path[1].action_key in root_leaf_diagnostics:
                diagnostic = root_leaf_diagnostics[path[1].action_key]
                diagnostic["tree_depth_counts"][tree_steps] += 1
                diagnostic["turn_delta_counts"][state.turn - game.turn] += 1
                diagnostic["rollout_step_counts"][rollout_steps] += 1
                diagnostic["value_source_counts"][value_source] += 1
            if iteration_forced_coverage and len(path) > 1:
                # A rollout may cover both a root action and its observed
                # continuation. Count it once when removing forced coverage
                # from root-policy selection visits.
                forced_root_policy_samples[path[1].action_key] += 1
            for visited in path:
                visited.visits += 1
                visited.value_sum += value

        root_map = root_legal_map
        available_root = [
            child for key, child in root.children.items() if key in root_map
        ]
        root_fallback = False
        if available_root:
            best = max(
                available_root,
                key=lambda child: (
                    child.visits - forced_root_policy_samples[child.action_key]
                    if (self.min_visits_per_root_outcome
                        or self.min_visits_per_observed_action) else child.visits,
                    child.mean_value, child.action_key,
                ),
            )
        else:
            # A determinization can legitimately rewrite a dynamic-choice
            # action (notably Corpse spend/Discover options) so that none of
            # the sampled root keys is concrete in the live state.  This is
            # not a terminal state and must never turn into max([]).  Choose
            # a current legal action using the live-root prior, then record a
            # zero-visit synthetic child so diagnostics expose the fallback.
            fallback_key = max(
                root_map,
                key=lambda key: (root_priors.get(key, 0.0) if root_priors else 0.0, key),
            )
            best = _InformationNode(
                action_key=fallback_key,
                availability=0,
                prior=(root_priors.get(fallback_key, 0.0) if root_priors else 0.0),
            )
            root.children[fallback_key] = best
            root_fallback = True
        root_key_by_concrete = {
            action.key(): key for key, action in root_map.items()
        }
        root_visits = [
            root.children.get(
                root_key_by_concrete.get(action.key(), information_action_key(game, action)),
                _InformationNode(),
            ).visits
            for action in legal
        ]
        policy_visits = [
            visits - forced_root_policy_samples[root_key_by_concrete[action.key()]]
            if (self.min_visits_per_root_outcome
                or self.min_visits_per_observed_action) else visits
            for action, visits in zip(legal, root_visits, strict=True)
        ]
        visit_total = sum(policy_visits)
        root_policy = [
            visits / visit_total if visit_total else 1.0 / len(legal)
            for visits in policy_visits
        ]
        root_action_stats = []
        for action, visit_share in zip(legal, root_policy, strict=True):
            key = root_key_by_concrete.get(action.key(), information_action_key(game, action))
            child = root.children.get(key)
            root_action_stats.append({
                "visits": 0 if child is None else child.visits,
                "availability": 0 if child is None else child.availability,
                "mean_value": 0.0 if child is None else child.mean_value,
                "prior_value": 0.0 if child is None else child.prior_value,
                "prior_value_weight": 0.0 if child is None else child.prior_value_weight,
                "prior": 0.0 if child is None else child.prior,
                "visit_share": visit_share,
                "selected": child is best,
                "coverage_forced_visits": forced_root_samples[key],
                "selection_visits": (0 if child is None else child.visits) - (
                    forced_root_policy_samples[key]
                    if (self.min_visits_per_root_outcome
                        or self.min_visits_per_observed_action) else 0),
                "conditional_coverage_forced_visits": forced_observed_root_samples[key],
                "observed_outcome_groups": 0 if child is None else len(child.outcomes),
                "observed_outcome_visit_counts": [] if child is None else sorted(n.visits for n in child.outcomes.values()),
                **{name: dict(counts) for name, counts in root_leaf_diagnostics[key].items()},
                **({"own_turn_followups": self._followup_diagnostics(child, root_player, game.turn)}
                   if self.collect_plan_diagnostics else {}),
            })
        conditional_training_examples = []
        conditional_training_states = []
        if self.collect_conditional_training_examples:
            for snapshot in conditional_snapshots.values():
                branch = snapshot["branch"]
                visits = [
                    max(
                        0,
                        branch.children.get(key, _InformationNode()).visits
                        - forced_observed_samples[(id(branch), key)],
                    )
                    for key in snapshot["action_keys"]
                ]
                total = sum(visits)
                if total < self.conditional_training_min_visits:
                    continue
                if len(snapshot["actions"]) != len(visits) or not visits:
                    continue
                conditional_training_examples.append({
                    "state": snapshot["state"],
                    "actions": snapshot["actions"],
                    "policy_target": [count / total for count in visits],
                    "teacher_action_values": [
                        branch.children.get(key, _InformationNode()).mean_value
                        for key in snapshot["action_keys"]
                    ],
                    "chosen_action": max(range(len(visits)), key=visits.__getitem__),
                    "conditional": True,
                    "conditional_root_action": snapshot["root_action"],
                    "conditional_trigger_depth": snapshot["trigger_depth"],
                    "conditional_observation_visits": branch.visits,
                    "conditional_policy_visits": total,
                    "value_target": None,
                    "value_target_valid": False,
                })
                conditional_training_states.append({
                    "game": snapshot["game"],
                    "root_action": snapshot["root_action"],
                    "trigger_depth": snapshot["trigger_depth"],
                    "observation_visits": branch.visits,
                    "policy_visits": total,
                })
        self.conditional_training_states = conditional_training_states
        self.decision_index += 1
        self.last_search = {
            "information_mode": self.information_mode,
            "iterations": total_iterations,
            "configured_iterations": configured_iterations,
            "adaptive_iterations": total_iterations - configured_iterations,
            "min_simulations_per_root_action": self.min_simulations_per_root_action,
            "min_visits_per_root_outcome": self.min_visits_per_root_outcome,
            "min_visits_per_observed_action": self.min_visits_per_observed_action,
            "root_outcome_coverage_complete": None if not self.min_visits_per_root_outcome else all(
                child is not None and self._root_outcome_coverage(child) >= self.min_visits_per_root_outcome
                for child in (root.children.get(key) for key in root_map)),
            "minimum_root_action_visits_achieved": min(root_visits),
            "max_total_iterations": self.max_total_iterations,
            "determinizations": total_iterations,
            "search_rules_version": self.search_rules_version,
            "tactical_precheck": self.tactical_precheck,
            "model_rollout_depth": self.model_rollout_depth,
            "tactical_leaf_hits": tactical_leaf_hits,
            "tactical_nodes": tactical_nodes,
            "outcome_branches": outcome_branches,
            "belief_candidate_count": len(belief.deck_hypotheses),
            "belief_unresolved_slots": belief.unresolved_hidden_slots,
            "root_actions": len(legal),
            "root_children": len(root.children),
            "root_action_keys": [action.key() for action in legal],
            "root_action_fallback": root_fallback,
            "invalid_determinization_actions": invalid_determinization_actions,
            "nodes": nodes,
            "selected_visits": best.visits,
            "selected_value": best.mean_value,
            "root_policy": root_policy,
            "root_policy_visit_basis": (
                "non_coverage_visits"
                if (self.min_visits_per_root_outcome or self.min_visits_per_observed_action)
                else "all_visits"
            ),
            "coverage_forced_iterations": sum(forced_root_samples.values()),
            "conditional_coverage_forced_iterations": sum(forced_observed_root_samples.values()),
            "collect_plan_diagnostics": self.collect_plan_diagnostics,
            "root_action_stats": root_action_stats,
            "conditional_training_examples": conditional_training_examples,
            "policy_value_model": (
                getattr(self.policy_value_model, "name", None)
            ),
            "leaf_value_source": (
                "model" if self.policy_value_model is not None and self.use_model_value
                else "heuristic_rollout"
            ),
            "value_perspective": (
                "fixed_root" if self.root_perspective_model_value
                else "acting_player_sign_flipped"
            ),
            "expansion_mode": (
                "force_unvisited"
                if self.policy_value_model is not None and self.force_uniform_expansion
                else "puct_prior"
                if self.policy_value_model is not None
                else "uct"
            ),
            "neural_prior_depth": self.neural_prior_depth,
            "prior_temperature": self.prior_temperature,
            "prior_uniform_mix": self.prior_uniform_mix,
        }
        return root_map[best.action_key]

"""Bounded deterministic same-turn terminal proofs for conservative tactics.

No card-ID preferences: attack witnesses use public, currently legal face
attacks; the broader spell grammar follows declared primitive effects and
requires a simpler board/secret/weapon/location scope. Random outcomes and
unresolved choices are never accepted as terminal witnesses.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from .rules import (Hook, DamageActionTarget, DamageHero, DamageEnemyHero,
                    DamageAllOtherMinions, GainHeroAttack, ResolveDeaths)

_EFFECTS = {DamageActionTarget, DamageHero, DamageEnemyHero,
            DamageAllOtherMinions, GainHeroAttack, ResolveDeaths}


@dataclass(frozen=True)
class LethalWitness:
    actions: tuple
    nodes: int


def find_face_attack_lethal(game, *, root_actions=None, max_depth=7, max_nodes=64):
    """Find a deterministic same-turn lethal using only legal face attacks.

    This narrow proof does not assume anything about card draws or generated
    cards. It is valid even with a board, weapon, or location present (which
    intentionally keeps the broader spell grammar below conservative). A
    cheap nominal-damage bound avoids cloning ordinary non-lethal positions.
    Unknown opponent Secrets and random attack outcomes are not proofs.
    """
    actor = game.current
    if game.finished or game.pending_choice or game.players[1 - actor].secrets:
        return None
    root_legal = list(root_actions) if root_actions is not None else game.legal_actions()
    attack_actions = [
        action for action in root_legal
        if action.kind in {"ATTACK", "HERO_ATTACK"}
        and action.target_player == 1 - actor
        and action.target_entity is None
    ]
    if not attack_actions:
        return None
    defender = game.players[1 - actor]
    if defender.hero_immune:
        return None
    # This is only a rejection bound. Every accepted candidate is subsequently
    # executed through the real rules engine, which checks modifiers, triggers,
    # armor, and terminal state exactly.
    nominal_damage = 0
    attacker = game.players[actor]
    for action in attack_actions:
        if action.kind == "ATTACK":
            source = next((m for m in attacker.board
                           if m.entity_id == action.source), None)
            nominal_damage += 0 if source is None else source.attack
        else:
            nominal_damage += (
                (0 if attacker.weapon is None else attacker.weapon.attack)
                + attacker.hero_attack_bonus
            )
    if nominal_damage < defender.health + defender.armor:
        return None

    # Depth-first search reaches an attack sequence quickly; breadth-first
    # expansion would spend a small node budget exploring every permutation
    # prefix before it ever reaches a seven-attacker lethal.
    frontier = [(game, ())]
    nodes = 0
    while frontier and nodes < max_nodes:
        state, path = frontier.pop()
        if len(path) >= max_depth:
            continue
        legal = root_legal if not path else state.legal_actions()
        # LIFO + reverse iteration preserves the engine's legal-action order
        # while descending one candidate line at a time.
        for action in reversed(legal):
            if nodes >= max_nodes:
                break
            if not (
                action.kind in {"ATTACK", "HERO_ATTACK"}
                and action.target_player == 1 - actor
                and action.target_entity is None
            ):
                continue
            child = state.clone(record_events=False)
            rng_before = child.rng.getstate()
            try:
                child.step(action)
            except ValueError:
                continue
            nodes += 1
            if child.rng.getstate() != rng_before or child.pending_choice is not None:
                continue
            sequence = (*path, action)
            if child.finished:
                if child.winner == actor:
                    return LethalWitness(sequence, nodes)
                continue
            frontier.append((child, sequence))
    return None


def _scope(game, actor):
    return (game.current == actor and not game.pending_choice
            and all(not (p.secrets or p.weapon or p.locations
                         or p.active_quests) for p in game.players))


def _eligible(game, action):
    if action.kind in {"ATTACK", "HERO_ATTACK"}:
        return action.target_entity is None and action.target_player == 1 - game.current
    if action.kind != "PLAY":
        return False
    if any(p.board for p in game.players):
        return False
    card = next((c for c in game.players[game.current].hand
                 if c.entity_id == action.source), None)
    if card is None or card.definition.card_type != "SPELL":
        return False
    rule = game.rule_registry.get(card.card_id)
    return (rule is not None and set(rule.hooks) == {Hook.SPELL}
            and bool(rule.hooks[Hook.SPELL])
            and all(type(effect) in _EFFECTS for effect in rule.hooks[Hook.SPELL]))


def find_same_turn_lethal(game, *, root_actions=None, max_depth=3, max_nodes=64):
    """Return a terminal witness within the restricted deterministic scope.

    Callers supply a public-belief determinization. Hidden hands/decks do not
    enter the eligible effects or ordering. All execution uses engine legality.
    Bounds limit work; exhausting a bound says nothing about absence of lethal.
    """
    actor = game.current
    if game.finished or not _scope(game, actor):
        return None
    queue = deque([(game, ())])
    nodes = 0
    while queue and nodes < max_nodes:
        state, path = queue.popleft()
        if len(path) >= max_depth:
            continue
        legal = root_actions if not path and root_actions is not None else state.legal_actions()
        for action in legal:
            if nodes >= max_nodes:
                break
            if not _eligible(state, action):
                continue
            child = state.clone(record_events=False)
            rng_before = child.rng.getstate()
            decks_before = tuple(tuple(c.entity_id for c in p.deck) for p in child.players)
            next_entity = child.next_entity_id
            try:
                child.step(action)
            except ValueError:
                continue
            nodes += 1
            # Reject hidden draws, random effects and generated entities even
            # when an ancillary engine trigger supplied one unexpectedly.
            if (child.rng.getstate() != rng_before
                    or child.next_entity_id != next_entity
                    or tuple(tuple(c.entity_id for c in p.deck) for p in child.players) != decks_before
                    or child.pending_choice is not None):
                continue
            sequence = (*path, action)
            if child.finished:
                if child.winner == actor:
                    return LethalWitness(sequence, nodes)
                continue
            if _scope(child, actor):
                queue.append((child, sequence))
    return None

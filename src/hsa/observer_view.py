"""Versioned, allowlisted observations for the new entity-policy training path.

Never serialize Game/Player.__dict__, deck order, RNG, or raw engine events.
This v1 covers the explicitly listed fields, not every Standard interaction.
It intentionally coexists with legacy encoding instead of resizing checkpoints.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json

from .encoding import card_semantic_features

SCHEMA = "hsa-observer-entities-v1"
PLAYER_NUMERIC = tuple("""
health max_health armor mana max_mana fatigue attack hero_attack_bonus
hero_attacks_this_turn hero_attacks_this_game hero_power_used hero_power_armor
hero_power_cost_override hero_power_cost_surcharge hero_power_imbues
collapsing_star_damage imbue_passive_triggered_this_turn herald_count
leyline_level leyline_upgrade leyline_extra_triggers leyline_cost_reduction
corpses locked_mana overload_next_turn overloaded_mana_this_game
cards_played_this_turn cards_drawn_this_turn spells_cast_this_turn
spells_cast_this_game hero_powers_used_this_game friendly_minions_died_this_turn
friendly_minions_died_this_game minion_played_this_turn minion_played_last_turn
hero_health_changed_this_turn hero_divine_shield hero_divine_shield_hits
hero_immune hero_immune_expiry_turn frozen_turn turns_taken skip_next_turn
next_spell_damage_bonus next_spell_cost_reduction next_minion_cost_reduction
next_demon_cost_reduction next_demon_free next_beast_cost_reduction
next_murloc_cost_reduction next_combo_cost_reduction next_temporary_cost_reduction
spell_cost_surcharge spell_cost_surcharge_turn minion_cost_fixed
void_soul_level broxigar_return_used broxigar_removed_from_game
animal_companion_cost_increase animal_companion_extra_count dragons_have_rush
recruit_attack_bonus recruit_health_bonus murloc_quest_buff gorishi_double_damage
kindred_triggers_twice end_turn_effect_repeat_turns reinforcement_aura_turns
spells_cast_twice_remaining restored_health_this_turn generated_cards_played
""".split())
CARD_NUMERIC = tuple("""
cost effective_cost attack health max_health damage cost_delta attack_delta health_delta
attacks_this_turn summoned_turn played_turn dormant_turns frozen_turn silenced
taunt rush charge lifesteal elusive stealth divine_shield divine_shield_hits
windfury mega_windfury reborn poisonous aura_poisonous cant_attack immune
immune_while_attacking cant_attack_heroes_turn cant_attack_turn
prepared prepared_turn prepare_granted playable_after_turn locked_until_card_played
battlecry_twice spell_casts_twice living_nightmare herald_power
spell_damage_bonus dynamic_spell_damage deathrattle_draw_cards
deathrattle_damage_enemy_hero deathrattle_damage_all_enemies
deathrattle_damage_all_minions deathrattle_summon_token_count
temporary temporary_immune_expiry_turn dies_at_end_of_turn destroy_at_turn_start
burning_turns burning_applied_turn avatar_form_pending
aura_attack_bonus aura_health_bonus weapon_attack_bonus pirate_aura_stats
shatter_combined smoldering_stage payload_attack payload_health payload_damage
sham_trial_due_owner_turn
""".split())
CARD_PRIVATE_NUMERIC = tuple("""
held_turns drawn_turn spells_cast_while_held mana_spent_while_held
minion_played_while_held higher_cost_card_played_while_held
opponent_card_copy_played_while_held stealthed_minion_attacked_while_held
""".split())
CARD_PUBLIC_TAGS = (
    "gifts", "deathrattle_summon_card_id",
    "deathrattle_summon_token_id", "sham_trial_effect_ids", "shatter_origin",
    "shatter_half", "temporary_attack_modifiers", "temporary_health_modifiers",
    "bonus_effect_active", "deathrattle_random_race", "titan_ability_id",
)
PLAYER_TAGS = (
    "card_class", "hero_power_id", "imbued_hero_power_id", "completed_quests",
    "played_races_this_turn", "played_races_last_turn", "played_races_this_game",
    "spell_schools_cast_this_turn", "ashalon_adaptations",
    "chronological_aura_turns", "delayed_self_damage", "delayed_mana_crystal_gains",
    "delayed_hero_attack", "last_played_card_id", "previous_played_card_id",
)
PUBLIC_EVENT_KINDS = frozenset({"play", "summon", "death", "hero_power", "attack",
                                "hero_attack", "turn_start", "turn_end"})
INDEX_CHOICES = frozenset({"RULE_CHOICE_PICK", "CATACLYSM_PICK"})


def _json_value(value):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return {str(k): _json_value(v) for k, v in sorted(value.items(), key=lambda x: str(x[0]))}
    if isinstance(value, (list, tuple)):
        return [_json_value(v) for v in value]
    if isinstance(value, (set, frozenset)):
        return sorted((_json_value(v) for v in value), key=str)
    raise TypeError(f"unreviewed observation payload: {type(value).__name__}")


def _numbers(obj, fields):
    return {name: getattr(obj, name, None) for name in fields}


def public_history(game, observer, limit=32):
    """Small public-event allowlist; never copy arbitrary event payloads."""
    result = []
    for event in reversed(game.events):
        kind = event.get("kind")
        if kind not in PUBLIC_EVENT_KINDS:
            continue
        card_id = event.get("card")
        definition = game.card_defs.get(card_id)
        if definition and "SECRET" in definition.mechanics:
            card_id = None
        player = event.get("player")
        result.append({"kind": kind, "card_id": card_id,
                       "owner": None if player not in (0, 1) else int(player != observer),
                       "turn": event.get("turn")})
        if len(result) >= limit:
            break
    return list(reversed(result))


def observer_view(game, observer=None, *, actions=None, known_deck=None, include_belief=True):
    """Build a detached JSON view; known_deck must be caller-known deck context.

    Own remaining deck identities are deliberately NOT read. They may cease to
    be known after hidden transformations. Opponent hand/secrets are count-only.
    Entity IDs are used internally for binding, never fed as numeric features.
    """
    observer = game.current if observer is None else observer
    if observer not in (0, 1):
        raise ValueError("observer must be 0 or 1")
    if actions is not None and observer != game.current:
        raise ValueError("only the acting observer may receive legal actions")
    entities, players, bindings = [], [], {}

    def add_entity(card_id, owner, zone, position, numbers=None, tags=None, entity_id=None):
        definition = game.card_defs.get(card_id)
        entity = {"card_id": card_id, "owner": owner, "zone": zone,
                  "position": position, "numeric": numbers or {}, "tags": tags or {},
                  "semantic": list(card_semantic_features(definition))}
        index = len(entities)
        entities.append(entity)
        if entity_id is not None:
            bindings[entity_id] = index
        return index

    def add_card(card, owner, zone, position):
        numbers = _numbers(card, CARD_NUMERIC)
        numbers["damaged_this_turn"] = (
            f"minion:{card.entity_id}" in game.players[game.current].damaged_characters_this_turn
        )
        tags = {name: _json_value(getattr(card, name, None)) for name in CARD_PUBLIC_TAGS}
        if owner == 0:
            numbers.update(_numbers(card, CARD_PRIVATE_NUMERIC))
            tags["embedded_spell_id"] = getattr(card, "embedded_spell_id", None)
            if zone == "hand":
                numbers["effective_cost"] = game._effective_cost(game.players[observer], card)
        return add_entity(card.card_id, owner, zone, position, numbers, tags, card.entity_id)

    for relative, index in enumerate((observer, 1 - observer)):
        player = game.players[index]
        numeric = _numbers(player, PLAYER_NUMERIC)
        numeric.update(hand_count=len(player.hand), deck_count=len(player.deck),
                       secret_count=len(player.secrets), board_count=len(player.board),
                       damaged_character_count=len(player.damaged_characters_this_turn)
                       if index == game.current else 0,
                       hero_damaged_this_turn=f"hero:{index}" in
                       game.players[game.current].damaged_characters_this_turn)
        tags = {name: _json_value(getattr(player, name, None)) for name in PLAYER_TAGS}
        if relative == 1:
            for field in ("last_played_card_id", "previous_played_card_id"):
                definition = game.card_defs.get(tags.get(field))
                if definition and "SECRET" in definition.mechanics:
                    tags[field] = "HIDDEN_SECRET"
        quests = {key: {field: _json_value(data[field]) for field in ("progress", "turns", "flags")
                        if field in data}
                  for key, data in sorted(player.active_quests.items())}
        players.append({"numeric": numeric, "tags": tags, "quests": quests})
        hero_index = add_entity(None, relative, "hero", 0, numeric, tags)
        bindings[("hero", index)] = hero_index
        hp = add_entity(player.hero_power_id or "CLASS_POWER:" + player.card_class,
                        relative, "hero_power", 0,
                        {"used": player.hero_power_used, "imbues": player.hero_power_imbues,
                         "cost_override": player.hero_power_cost_override})
        bindings[("hero_power", index)] = hp
        if relative == 0:
            for position, card in enumerate(player.hand):
                add_card(card, relative, "hand", position)
            for position, card in enumerate(player.secrets):
                add_card(card, relative, "secret", position)
        for position, card in enumerate(player.board):
            add_card(card, relative, "board", position)
        for position, location in enumerate(player.locations):
            add_entity(location.card_id, relative, "location", position,
                       _numbers(location, ("durability", "cooldown", "next_refresh", "custom_tier")),
                       {"custom_effects": list(location.custom_effects)}, location.entity_id)
        if player.weapon:
            add_entity(player.weapon.card_id, relative, "weapon", 0,
                       _numbers(player.weapon, ("attack", "durability", "ammunition")))
        # Identity counts are public. Do not retain historical private payloads.
        for position, (card_id, count) in enumerate(sorted(Counter(c.card_id for c in player.dead_minions).items())):
            add_entity(card_id, relative, "graveyard", position, {"count": count})
        for position, (card_id, progress) in enumerate(quests.items()):
            add_entity(card_id, relative, "quest", position,
                       {k: v for k, v in progress.items() if isinstance(v, (int, float))},
                       {"flags": progress.get("flags", [])})

    if known_deck is not None:
        for position, (card_id, count) in enumerate(sorted(known_deck.items())):
            if not isinstance(count, int) or count <= 0:
                raise ValueError("known deck counts must be positive integers")
            add_entity(card_id, 0, "known_starting_deck", position, {"count": count})

    pending = game.pending_choice
    choice_indices = {}
    choice = None
    if pending:
        own_choice = game.current == observer
        choice = {"kind": pending["kind"], "visible": own_choice}
        if own_choice:
            if hasattr(pending.get("card"), "card_id"):
                choice["source_card_id"] = pending["card"].card_id
            for position, option in enumerate(pending.get("options", ())):
                if hasattr(option, "card_id"):
                    choice_indices[position] = add_card(option, 0, "choice", position)
                elif pending["kind"] == "MULLIGAN" and isinstance(option, int) and option in bindings:
                    choice_indices[position] = bindings[option]
                elif pending["kind"] == "RULE_CHOICE" and isinstance(option, tuple) and isinstance(option[0], str):
                    # Labels are player-visible; effect objects are engine internals.
                    choice_indices[position] = add_entity(
                        None, 0, "choice", position, tags={"option": option[0],
                        "source_card": choice.get("source_card_id")})
                elif isinstance(option, (str, int, float, bool)):
                    choice_indices[position] = add_entity(
                        None, 0, "choice", position, tags={"option": option})
                else:
                    raise ValueError(f"unreviewed choice option in {pending['kind']}")
            selected = pending.get("selected", ())
            choice["selected_entities"] = [bindings[i] for i in selected if i in bindings]

    encoded_actions = []
    for action in actions or ():
        source = bindings.get(action.source, -1)
        if action.kind == "HERO_ATTACK":
            source = bindings[("hero", observer)]
        elif action.kind == "HERO_POWER":
            source = bindings[("hero_power", observer)]
        elif action.kind in INDEX_CHOICES:
            source = choice_indices.get(action.source, -1)
        elif action.kind in {"AMMUNITION_PICK", "CORPSE_SPEND"}:
            source = -1
        target = bindings.get(action.target_entity, -1)
        if action.target_entity is None and action.target_player in (0, 1):
            target = bindings[("hero", action.target_player)]
        encoded_actions.append({"kind": action.kind, "source": source, "target": target,
                                "literal": action.source if action.kind in
                                {"AMMUNITION_PICK", "CORPSE_SPEND"} else None})

    belief_summary = None
    if include_belief:
        from .belief import PublicBelief
        belief = PublicBelief.from_game(game, observer)
        total = sum(weight for weight, _ in belief.deck_hypotheses)
        expected = Counter()
        for weight, counts in belief.deck_hypotheses:
            for card_id, count in counts:
                expected[card_id] += weight * count / total
        belief_summary = {"candidate_count": len(belief.deck_hypotheses),
                          "unresolved_hidden_slots": belief.unresolved_hidden_slots,
                          "has_candidate_support": bool(total)}
        for position, (card_id, count) in enumerate(sorted(expected.items())):
            add_entity(card_id, 1, "belief_expected_remaining", position, {"count": count})

    view = {"schema": SCHEMA, "turn": game.turn, "to_act": int(game.current != observer),
            "players": players, "entities": entities, "actions": encoded_actions,
            "choice": choice, "belief": belief_summary,
            "history": public_history(game, observer),
            "known_deck_provided": known_deck is not None}
    # Every nested container above is constructed for this call, and observed
    # mutable game payloads pass through _json_value. A second recursive copy
    # only repeats the work without increasing snapshot isolation.
    return view


def observation_digest(view):
    return hashlib.sha256(json.dumps(view, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()

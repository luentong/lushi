"""Causal special-zone provenance; never infer identities from future packets."""
from dataclasses import replace


def broxigar_reserves(state):
    """Original Broxigar DECK -> SETASIDE, and whether it has returned once."""
    result = {}
    for entity in state.entities.values():
        zones = [zone for _, zone in entity.zone_history]
        if (entity.card_id != "TIME_020" or zones[:2] != ["DECK", "SETASIDE"]
                or entity.tags.get("CREATOR") not in (None, 0, "0", "")
                or entity.tags.get("COPIED_FROM_ENTITY_ID") not in (None, 0, "0", "")
                or entity.controller not in (1, 2)):
            continue
        result[entity.entity_id] = (entity.initial_controller or entity.controller,
                                    "HAND" in zones[2:])
    return result


def godfrey_public_copies(state):
    """Map returned/reserved entities to already-public Atlas copy proxies.

    Arbitrary copy links do not prove a hidden card's identity. Conflicting
    proxies, a changed identity, or a trip through another zone invalidate
    this narrow inference. The caller must label these inferred identities.
    """
    options = {}
    for proxy in state.entities.values():
        atlas = state.entities.get(str(proxy.tags.get("CREATOR")))
        source = state.entities.get(str(proxy.tags.get("COPIED_FROM_ENTITY_ID")))
        if (not proxy.card_id or proxy.zone != "SETASIDE" or atlas is None
                or atlas.card_id != "JAIL_509e" or atlas.zone != "PLAY"
                or source is None or source.zone not in {"HAND", "SETASIDE"}
                or source.controller != atlas.controller
                or proxy.controller != atlas.controller
                or not source.zone_history
                or source.zone_history[0][1] != "SETASIDE"
                or any(zone not in {"SETASIDE", "HAND"} for _, zone in source.zone_history)
                or (source.card_id and source.card_id != proxy.card_id)
                or any(card_id != proxy.card_id for _, card_id in source.identity_history)):
            continue
        options.setdefault(source.entity_id, []).append(proxy)
    result = {}
    for entity_id, proxies in options.items():
        if len({(p.card_id, p.cost) for p in proxies}) != 1:
            continue
        source, proxy = state.entities[entity_id], proxies[0]
        # Proxy stats precede the Atlas discount; explicit live COST wins.
        cost = source.cost if source.cost is not None else (
            max(0, proxy.cost - 1) if proxy.cost is not None else None)
        result[entity_id] = replace(
            source, card_id=proxy.card_id, card_type=proxy.card_type,
            cost=cost, attack=source.attack if source.attack is not None else proxy.attack,
            health=source.health if source.health is not None else proxy.health,
            tags={**source.tags, "CREATOR": proxy.tags["CREATOR"]})
    return result


def generated_hidden_hand_card(game, live):
    """Return a labelled hypothesis only for supported, witnessed generation.

    Unknown Kazakus selections remain unknown: a legal recipe is sampled,
    never asserted to be the opponent's actual choice.
    """
    context = live.creation_context
    zones = [zone for _, zone in live.zone_history]
    if (not live.card_id and zones == ["HAND"]
            and context.get("source_type") == "GAME"
            and context.get("block_type") == "TRIGGER"
            and context.get("turn") == 1
            and context.get("phase") in (None, "BEGIN_FIRST", "BEGIN_SHUFFLE", "BEGIN_DRAW")
            and context.get("opening_hand_count") == 4):
        return game._entity("GAME_005"), "inferred ordinary opening Coin from witnessed four-card deal"
    if (not live.card_id and zones == ["SETASIDE", "HAND"]
            and context.get("source_card") == "CAP_405"
            and context.get("block_type") == "POWER"):
        trial = game._entity(game.rng.choice(("CAP_405tb1", "CAP_405tb2", "CAP_405tb3")),
                             created_by="CAP_405")
        trial.sham_trial_effect_ids = tuple(game.rng.sample(
            [f"CAP_405t{n}" for n in range(1, 10)], 2))
        return trial, "sampled hidden Kazakus Trial recipe; actual delay and effects unknown"
    return None

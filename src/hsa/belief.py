"""Public-information belief tracking for the fixed Dragon Warrior mirror."""

from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass

from .dragon_mirror import (
    DRAGON_DECK_COUNTS,
    DRAGON_IDS,
    PIRATE_IDS,
    SPECIAL_TOKEN_IDS,
    SUPPORTED_IDS,
    WARRIOR_MINION_IDS,
    DragonMirrorGame,
)


@dataclass(frozen=True)
class GeneratedCardBelief:
    """One hidden generated card described only by public information."""

    source_card_id: str
    candidates: tuple[str, ...]
    destination: str
    void_soul_cost: int = 0

    def as_dict(self) -> dict[str, object]:
        return {
            "source_card_id": self.source_card_id,
            "candidates": list(self.candidates),
            "destination": self.destination,
            "void_soul_cost": self.void_soul_cost,
        }


@dataclass(frozen=True)
class HandModifierBelief:
    """Public aggregate for a hidden-hand modifier event."""

    source_card_id: str
    attack: int
    health: int
    card_types: tuple[str, ...]
    require_attribute: str | None
    affected_count: int
    burning_turns: int = 0

    def as_dict(self) -> dict[str, object]:
        return {
            "source_card_id": self.source_card_id,
            "attack": self.attack,
            "health": self.health,
            "card_types": list(self.card_types),
            "require_attribute": self.require_attribute,
            "affected_count": self.affected_count,
            "burning_turns": self.burning_turns,
        }


def _generation_candidates(source_card_id: str) -> tuple[str, ...]:
    """Return candidates for generation sources implemented by this slice."""
    pools = {
        # The current closed-pool Carrier Whelp rule adds another Carrier.
        # Expand this entry together with the card rule when its live pool lands.
        "CATA_556": ("CATA_556",),
        "CAP_107": ("CAP_107t",),
        "EDR_456": tuple(sorted(DRAGON_IDS)),
        "FIR_939": tuple(sorted(WARRIOR_MINION_IDS)),
        "CAP_105": ("CAP_107",),
        "CORE_DRG_024": tuple(sorted(PIRATE_IDS)),
        "TLC_820": ("TLC_813",),
        "CORE_DRG_107": ("CORE_EX1_277",),
        "CORE_EX1_014": ("EX1_014t",),
        "CATA_585": ("CATA_585",),
        "JAIL_730": ("JAIL_732",),
    }
    return pools.get(source_card_id, ())


@dataclass(frozen=True)
class PublicBelief:
    observer: int
    opponent: int
    starting_cards_remaining: dict[str, int]
    known_extra_cards: dict[str, int]
    opponent_hand_size: int
    opponent_deck_size: int
    known_coin_in_hand: bool
    generated_cards: tuple[GeneratedCardBelief, ...]
    hand_modifiers: tuple[HandModifierBelief, ...]
    unresolved_hidden_slots: int
    public_events_consumed: int

    def sample_determinization(
        self, game: DragonMirrorGame, *, seed: int
    ) -> DragonMirrorGame:
        """Rebuild opponent hidden zones without reading their true identities.

        The fixed deck remainder and public generation-source pools form the
        candidate bag.  If an unsupported hidden generator exists, its slot is
        sampled from the implemented closed pool and explicitly counted in the
        belief report. Public hand enchantments are reconstructed from aggregate
        source/filter/count facts, never from private affected-entity IDs.
        """
        if self.observer != game.current:
            raise ValueError("belief observer must be the player to act")
        sampled = game.clone()
        opponent = sampled.players[self.opponent]
        total_hidden = self.opponent_hand_size + self.opponent_deck_size
        rng = random.Random(seed)
        candidates: list[tuple[str, bool, str | None, int]] = []
        for card_id, count in self.starting_cards_remaining.items():
            candidates.extend((card_id, True, None, 0) for _ in range(count))
        for card_id, count in self.known_extra_cards.items():
            candidates.extend((card_id, False, "JAIL_384", 0) for _ in range(count))
        for slot in self.generated_cards:
            candidates.append(
                (
                    rng.choice(slot.candidates), False, slot.source_card_id,
                    slot.void_soul_cost,
                )
            )

        unknown_pool = tuple(sorted(
            (
                set(SUPPORTED_IDS) | DRAGON_IDS | WARRIOR_MINION_IDS | PIRATE_IDS
            ) - SPECIAL_TOKEN_IDS
        ))
        candidates.extend(
            (rng.choice(unknown_pool), False, "UNKNOWN_PUBLIC_GENERATOR", 0)
            for _ in range(self.unresolved_hidden_slots)
        )
        coin = ("GAME_005", False, "MULLIGAN", 0) if self.known_coin_in_hand else None
        non_coin_capacity = total_hidden - int(coin is not None)
        # Public destruction/discard bookkeeping is not complete yet.  If its
        # absence leaves too many candidates, choose a public-belief subset.
        rng.shuffle(candidates)
        candidates = candidates[:non_coin_capacity]
        while len(candidates) < non_coin_capacity:
            candidates.append(
                (rng.choice(unknown_pool), False, "UNKNOWN_PUBLIC_GENERATOR", 0)
            )
        rng.shuffle(candidates)
        hand_specs = candidates[:self.opponent_hand_size - int(coin is not None)]
        if coin is not None:
            hand_specs.append(coin)
        deck_specs = candidates[len(hand_specs) - int(coin is not None):]

        def make_card(spec: tuple[str, bool, str | None, int]):
            card_id, started_in_deck, created_by, void_soul_cost = spec
            card = sampled._entity(
                card_id, started_in_deck=started_in_deck, created_by=created_by
            )
            card.void_soul_cost = void_soul_cost
            return card

        opponent.hand = [make_card(spec) for spec in hand_specs]
        opponent.deck = [make_card(spec) for spec in deck_specs]
        for modifier in self.hand_modifiers:
            eligible = [
                card for card in opponent.hand
                if (
                    not modifier.card_types
                    or card.definition.card_type in modifier.card_types
                )
                and (
                    modifier.require_attribute is None
                    or bool(getattr(card, modifier.require_attribute, False))
                )
            ]
            rng.shuffle(eligible)
            for card in eligible[:modifier.affected_count]:
                card.attack_delta += modifier.attack
                card.health_delta += modifier.health
                if modifier.burning_turns:
                    card.burning_turns = max(
                        card.burning_turns, modifier.burning_turns
                    )
                    card.burning_applied_turn = sampled.turn
        sampled._event(
            "determinization", observer=self.observer,
            belief_model="public_dragon_mirror_v3", seed=seed,
            hidden_hand=len(opponent.hand), hidden_deck=len(opponent.deck),
            unresolved_hidden_slots=self.unresolved_hidden_slots,
        )
        return sampled

    @classmethod
    def from_game(cls, game: DragonMirrorGame, observer: int) -> "PublicBelief":
        if observer not in (0, 1):
            raise ValueError("observer must be player 0 or 1")
        opponent = 1 - observer
        remaining = Counter(DRAGON_DECK_COUNTS)
        extras: Counter[str] = Counter()
        generated: list[GeneratedCardBelief] = []
        modifiers: list[HandModifierBelief] = []
        consumed = 0

        def consume_public_card(event: dict[str, object]) -> None:
            card_id = str(event["card"])
            if event.get("started_in_deck"):
                if remaining[card_id] > 0:
                    remaining[card_id] -= 1
                    if remaining[card_id] == 0:
                        del remaining[card_id]
                return
            created_by = event.get("created_by")
            slot = next(
                (
                    item for item in generated
                    if item.source_card_id == created_by
                    and card_id in item.candidates
                ),
                None,
            )
            if slot is not None:
                generated.remove(slot)
            elif extras[card_id] > 0:
                extras[card_id] -= 1
                if extras[card_id] == 0:
                    del extras[card_id]
        # Deliberately ignore internal opening-deal, draw, mulligan and
        # Discover identities. Only whitelisted public events are consumed.
        for event in game.events:
            if event.get("player") != opponent:
                continue
            kind = event.get("kind")
            if kind == "start_of_game" and event.get("duplicated"):
                extras[event["duplicated"]] += 1
                consumed += 1
            elif kind == "play":
                consume_public_card(event)
                consumed += 1
            elif kind in {"burn", "discard"}:
                consume_public_card(event)
                consumed += 1
            elif kind in {
                "generated_to_hand", "generated_from_pool",
                "discover_pick", "discover_copy", "returned_to_hand",
                "void_soul_generated",
            }:
                source_card_id = event.get("source")
                destination = event.get("destination", "hand")
                candidates = _generation_candidates(source_card_id)
                if destination != "burned" and candidates:
                    generated.append(
                        GeneratedCardBelief(
                            source_card_id=source_card_id,
                            candidates=candidates,
                            destination=destination,
                            void_soul_cost=int(event.get("cost", 0)),
                        )
                    )
                consumed += 1
            elif (
                kind in {"zone_buff", "runthak_buff"}
                and event.get("zone") == "hand"
            ):
                modifiers.append(
                    HandModifierBelief(
                        source_card_id=str(event.get("source")),
                        attack=int(event.get("attack", 0)),
                        health=int(event.get("health", 0)),
                        card_types=tuple(event.get("card_types", ())),
                        require_attribute=event.get("require_attribute"),
                        affected_count=int(event.get("affected_count", 0)),
                        burning_turns=int(event.get("burning_turns", 0)),
                    )
                )
                consumed += 1
        view = game.observation(observer)
        opponent_view = view["players"][opponent]
        hand_size = len(opponent_view["hand"])
        deck_size = opponent_view["deck_count"]
        known_coin = (
            opponent == 1
            and any(
                event.get("kind") == "coin_given"
                and event.get("player") == opponent
                for event in game.events
            )
            and not any(
                event.get("kind") == "play"
                and event.get("player") == opponent
                and event.get("card") == "GAME_005"
                for event in game.events
            )
        )
        accounted = (
            sum(remaining.values()) + sum(extras.values())
            + len(generated) + int(known_coin)
        )
        return cls(
            observer=observer,
            opponent=opponent,
            starting_cards_remaining=dict(sorted(remaining.items())),
            known_extra_cards=dict(sorted(extras.items())),
            opponent_hand_size=hand_size,
            opponent_deck_size=deck_size,
            known_coin_in_hand=known_coin,
            generated_cards=tuple(generated),
            hand_modifiers=tuple(modifiers),
            unresolved_hidden_slots=max(0, hand_size + deck_size - accounted),
            public_events_consumed=consumed,
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": 3,
            "belief_model": "public_dragon_mirror_v3",
            "observer": self.observer + 1,
            "opponent": self.opponent + 1,
            "starting_cards_remaining": self.starting_cards_remaining,
            "known_extra_cards": self.known_extra_cards,
            "opponent_hand_size": self.opponent_hand_size,
            "opponent_deck_size": self.opponent_deck_size,
            "known_coin_in_hand": self.known_coin_in_hand,
            "generated_cards": [card.as_dict() for card in self.generated_cards],
            "hand_modifiers": [item.as_dict() for item in self.hand_modifiers],
            "unresolved_hidden_slots": self.unresolved_hidden_slots,
            "public_events_consumed": self.public_events_consumed,
        }

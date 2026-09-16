"""Composable card rules for the deterministic simulator.

The module deliberately depends on the game through a small duck-typed API.
That keeps card declarations separate from ``dragon_mirror.py`` and avoids a
circular import between the state model and the rule catalogue.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any, Protocol


class Hook(StrEnum):
    BATTLECRY = "battlecry"
    DEATHRATTLE = "deathrattle"
    SPELL = "spell"
    AFTER_DRAW = "after_draw"
    AFTER_PLAY = "after_play"
    AFTER_ATTACK = "after_attack"
    AFTER_HERO_ATTACK = "after_hero_attack"
    LOCATION = "location"
    HERO_POWER = "hero_power"
    START_TURN = "start_turn"
    END_TURN = "end_turn"
    SHATTER = "shatter"


class TargetKind(StrEnum):
    ANY_MINION = "any_minion"
    FRIENDLY_MINION = "friendly_minion"
    ENEMY_MINION = "enemy_minion"
    ANY_CHARACTER = "any_character"
    FRIENDLY_CHARACTER = "friendly_character"
    FRIENDLY_UNDEAD = "friendly_undead"
    ENEMY_CHARACTER = "enemy_character"


@dataclass(frozen=True)
class TargetSpec:
    kind: TargetKind
    optional: bool = False


# Base metadata for these generated entities comes from the pinned
# HearthstoneJSON snapshot. Declaring the dependency here lets ordinary rules
# refer only to card IDs instead of rebuilding CardDef objects in the engine.
DECLARATIVE_METADATA_IDS = {
    # Fyrakk stays outside executable generator pools until its full
    # 15-Mana Fire-spell closure is complete, but its target-side Fire
    # immunity is testable now.
    "FIR_959",
    "CORE_CS2_065",  # Voidwalker
    "EDR_492t",  # Duckling
    "EDR_260t",  # Illusion
    "EDR_810t",  # Bloated Leech
    "GAME_005",  # The Coin
    "JAIL_399t1",  # Grandmother Imp
    "TIME_713t",  # Timeless Chest
    "TLC_813",  # Purifying Vines
    "CAP_400t2t",  # Imp-formant
    "JAIL_511t",  # Shivarra Infiltrator
    "EDR_271t",  # Treant of Life
    "EX1_572",  # Ysera (for Ysera Awakens exclusion)
    "DREAM_01",  # Laughing Sister
    "DREAM_02",  # Ysera Awakens
    "DREAM_03",  # Emerald Drake
    "DREAM_04",  # Dream
    "DREAM_05",  # Nightmare
    "EDR_846t3",  # Corrupted Laughing Sister
    "EDR_846t5",  # Corrupted Drake
    "TIME_890t",  # Atiesh the Greatstaff
    "TIME_890t2",  # Karazhan the Sanctum
}

# Some Core printings retain the historical behavior ID while the pinned JSON
# snapshot only contains the original printing. Load its metadata under the
# runtime ID, but keep the alias explicit and auditable.
DECLARATIVE_METADATA_ALIASES = {
    "CORE_EX1_277": "EX1_277",  # Arcane Missiles
}

# New full-Standard rules are kept separate from the historical Dragon slice
# so adding cards does not mutate the vocabulary of existing neural models.
STANDARD_DECLARATIVE_IDS = {
    # Simple Core rule tranche: direct draw, heal, damage, and destroy.
    "CORE_AT_055",  # Flash Heal
    "CORE_CS2_023",  # Arcane Intellect
    "CORE_CS2_076",  # Assassinate
    "CORE_DS1_185",  # Arcane Shot
    "CORE_AT_064",  # Bash
    "CORE_CS1_130",  # Holy Smite
    "CORE_CS2_094",  # Hammer of Wrath
    "CORE_EX1_129",  # Fan of Knives
    "CORE_EX1_278",  # Shiv
    "CORE_TRL_307",  # Flash of Light
    "CORE_CS2_093",  # Consecration
    "CORE_BT_035",  # Chaos Strike
    "CORE_BT_292",  # Hand of A'dal
    "CORE_CS2_053",  # Far Sight
    "CORE_EX1_096",  # Loot Hoarder
    "CORE_CFM_604",  # Greater Healing Potion
    "CORE_BRM_013",  # Quick Shot
    "CORE_EX1_302",  # Mortal Coil
    "CORE_EX1_007",  # Acolyte of Pain
    "CORE_RLK_121",  # Acolyte of Death
    "RLK_511",  # Harbinger of Winter
    "RLK_709",  # Remorseless Winter
    "EDR_843a", "EDR_843b", "EDR_843t1", "CAP_405t4",
    "EDR_817", "CAP_102",
    "TIME_023", "EDR_251", "JAIL_377", "EDR_231", "JAIL_866", "CORE_CATA_007",
    "CORE_EX1_154", "CATA_526", "TLC_231", "TLC_236", "EDR_226",
    "RLK_024", "CATA_156",
    "CORE_AT_037",
    "CORE_CS2_024", "CORE_CS2_028", "CORE_RLK_063",
    "CORE_BAR_801",
    "CORE_EX1_391", "CORE_EX1_606", "CORE_GIL_622",
    "CORE_CS2_072", "CORE_CS2_108", "CORE_EX1_309", "CORE_EX1_312",
    "CORE_CS2_009", "CORE_EX1_238", "CORE_CS2_074", "CORE_RLK_567", "TIME_039", "JAIL_720", "TLC_515", "TLC_816", "CORE_YOP_001", "DINO_417", "JAIL_998", "DINO_411", "CATA_201", "TLC_902", "TLC_630t", "TLC_903t", "TLC_522", "CATA_785", "EDR_840", "CATA_158", "EDR_523", "CAP_001", "CAP_003", "CAP_000", "CAP_005", "CAP_002", "TIME_875t", "CORE_ULD_133", "MEND_504", "EDR_804", "GIL_553", "OG_195", "MEND_500", "LOOT_537",
    "CORE_CS1_112", "CORE_WON_337",
    "CORE_BT_072",
    "CORE_EX1_145",
    "CORE_EX1_619", "CORE_EX1_259",
    "CORE_EX1_246",
    "CORE_EX1_160",
    "CORE_DS1_184",
    "CATA_491",
    "CAP_801",
    "CATA_215",
    "CATA_582",
    "CATA_585",
    "CATA_203",
    "CATA_554",
    "CATA_557",
    "CATA_489",  # Arcane Flow (Shatter base card)
    "CATA_489t", "CATA_489t2",
    "CATA_479", "CATA_479t", "CATA_479t2",
    "CATA_820", "CATA_820t", "CATA_820t2",
    "CATA_134", "CATA_134t", "CATA_134t2",
    "CATA_306", "CATA_306t1", "CATA_306t2",
    "CATA_202",
    "TIME_101",
    "CORE_BOT_451",
    "CORE_KAR_077",
    "CORE_BAR_541",
    "CORE_BT_491",
    "CORE_BT_801",
    "CORE_CATA_009",
    "CORE_EDR_002",
    "YOD_012", "YOD_012ts",
    "CORE_BAR_311",
    "CORE_EX1_287",
    "CORE_EX1_289",
    "EDR_814",
    "CATA_485",
    "JAIL_441",
    "JAIL_891",
    "TLC_235",
    "RLK_025",
    "TIME_218", "CORE_BOT_222",
    "TLC_823",
    "MEND_043",
    "TIME_770", "JAIL_206",
    "JAIL_206",
    "EDR_416",  # Shepherd's Crook
    "EDR_416t",  # Sleepy Sheep token
    "CATA_302",  # Mend
    "CATA_308",  # Medivh's Triumph
    "JAIL_COIN1",  # The Coin
    "EDR_463",  # Twilight Influence
    "EDR_463a",  # Constricting Thorns choice
    "EDR_463b",  # Controlling Vines choice
    "CATA_131",
    "CATA_303",
    "CATA_138",
    "CATA_139",
    "CATA_140",
    "CATA_190p",
    # Deathwing, Worldbreaker and its four non-collectible Cataclysms.  The
    # sequencing is engine-owned because the Hero card makes one, two, or four
    # consecutive *distinct* choices based on Herald count.
    "CATA_190h",
    "CATA_190t10",
    "CATA_190t11",
    "CATA_190t12",
    "CATA_190t13",
    "CATA_190t14",
    "CATA_492",
    "CATA_496",
    "CATA_581",
    "CATA_725",
    "CORE_CS2_029",
    "CORE_CS2_032",
    "CORE_EX1_610",
    "CORE_EX1_611",
    "CORE_EX1_554",
    "CORE_EX1_130",
    "CORE_EX1_294",
    "CORE_FP1_020",
    "EX1_379",
    "EX1_136",
    "FP1_018",
    "EX1_594",
    "EX1_609",
    "CORE_KAR_004",
    "CORE_LOOT_101",
    "CAP_404",
    "CORE_CS2_004",
    "CORE_CS2_062",
    "CORE_EX1_169",
    "CORE_EX1_197",
    "CORE_ICC_055",
    "CORE_OG_047",
    "CORE_SW_072",
    "CORE_SW_108",
    "DINO_432",
    "DINO_431",
    "DINO_406",
    "EDR_449",
    "EDR_270",
    "EDR_271",
    "EDR_271t",
    "EDR_449p",
    "EDR_970",
    "EDR_846",
    "EDR_846t1",
    "EDR_846t2",
    "EDR_846t3",
    "EDR_846t4",
    "EDR_846t5",
    "EDR_852",
    "FIR_907",
    "FIR_906",
    "FIR_909",
    "FIR_910",
    "FIR_923",
    "FIR_954",
    "FIR_941",
    "EDR_476",
    "END_007",
    "END_011",
    "END_025",
    "END_024",
    "JAIL_201",
    "JAIL_200",
    "JAIL_307",
    "JAIL_801",
    "JAIL_801t",
    "JAIL_430",
    "JAIL_872",
    "JAIL_510",
    "JAIL_511",
    "JAIL_513",
    "JAIL_514",
    "JAIL_432",
    "JAIL_433",
    "JAIL_912",
    "JAIL_875",
    "JAIL_941",
    "JAIL_941t",
    "MEND_042",
    "TIME_702",
    "TIME_890",
    "TIME_890t",
    "TIME_890t2",
    "TIME_432",
    "TIME_701",
    "TLC_451",
    "TLC_227",
    "TLC_221",
    "TLC_222",
    "TLC_632",
    "TLC_632t",
    "TLC_632t2",
    "SW_108t",
    "TLC_COIN1",
}


@dataclass(frozen=True)
class RuleSource:
    kind: str
    reference: str
    upstream_card_id: str | None = None
    license: str | None = None
    verification: tuple[str, ...] = ()


@dataclass
class RuleContext:
    player: Any
    card: Any
    action: Any | None = None
    payload: dict[str, Any] = field(default_factory=dict)


class Effect(Protocol):
    def execute(self, game: Any, context: RuleContext) -> None: ...


class CostModifier(Protocol):
    def adjustment(self, game: Any, player: Any, card: Any) -> int: ...


@dataclass(frozen=True)
class CostIfOutcast:
    target_cost: int

    def adjustment(self, game: Any, player: Any, card: Any) -> int:
        active = getattr(card, "outcast_active", False)
        if not active:
            for index, held in enumerate(player.hand):
                if held.entity_id == card.entity_id:
                    active = index in {0, len(player.hand) - 1}
                    break
        if not active:
            return 0
        return self.target_cost - card.cost


def _recipient(game: Any, context: RuleContext, side: str) -> Any:
    if side == "controller":
        return context.player
    if side == "opponent":
        return game.players[1 - context.player.index]
    raise ValueError(f"unknown recipient side: {side}")


@dataclass(frozen=True)
class Draw:
    count: int = 1
    side: str = "controller"

    def execute(self, game: Any, context: RuleContext) -> None:
        player = _recipient(game, context, self.side)
        for _ in range(self.count):
            game._draw(player)


@dataclass(frozen=True)
class DrawIfOutcast:
    count: int = 1

    def execute(self, game: Any, context: RuleContext) -> None:
        if not getattr(context.card, "outcast_active", False):
            return
        for _ in range(self.count):
            game._draw(context.player)


@dataclass(frozen=True)
class DrawThenShuffleSource:
    """Draw a card, then shuffle the played source card back into its deck."""

    def execute(self, game: Any, context: RuleContext) -> None:
        game._draw(context.player)
        card = context.card
        if card in context.player.board:
            context.player.board.remove(card)
        card.damage = 0
        card.attack_delta = card.health_delta = 0
        card.playable_after_turn = -1
        context.player.deck.insert(game.rng.randrange(len(context.player.deck) + 1), card)
        game._event("shuffle_source_into_deck", player=context.player.index,
                    source=card.entity_id, card=card.card_id)


@dataclass(frozen=True)
class DrawIfUnspentMana:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.player.mana > 0:
            game._draw(context.player)


@dataclass(frozen=True)
class DrawAndDiscountDrawn:
    amount: int = 1

    def execute(self, game: Any, context: RuleContext) -> None:
        before = set(card.entity_id for card in context.player.hand)
        game._draw(context.player)
        drawn = [card for card in context.player.hand if card.entity_id not in before]
        if drawn:
            drawn[-1].cost_delta -= self.amount


@dataclass(frozen=True)
class DestroyFriendlyWispDraw:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player != context.player.index:
            raise ValueError("friendly Wisp target is required")
        target = game._find_minion(context.player.index, context.action.target_entity)
        if target.definition.name.casefold() != "wisp":
            raise ValueError("Divination requires a friendly Wisp")
        target.damage = target.max_health
        game._resolve_deaths()
        for _ in range(3):
            game._draw(context.player)


@dataclass(frozen=True)
class DamageRandomEnemyMinionExcess:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        enemy = game.players[1 - context.player.index]
        targets = [m for m in enemy.board if m.health > 0 and m.dormant_turns == 0]
        if not targets:
            return
        target = game.rng.choice(targets)
        before = max(0, target.health)
        amount = game._spell_effect_amount(context.player, context.card, self.amount)
        game._damage_minion(enemy.index, target, amount, context.card)
        excess = max(0, amount - before)
        if excess:
            game._damage_hero(enemy, excess, context.card)
        game._resolve_deaths()
        game._event("random_minion_excess_damage", player=context.player.index,
                    source=context.card.card_id, target=target.entity_id,
                    amount=amount, excess=excess)


@dataclass(frozen=True)
class DiscountCardsNotStartedInDeck:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        affected = []
        for card in context.player.hand:
            if card.started_in_deck:
                continue
            card.cost_delta -= self.amount
            affected.append(card.entity_id)
        game._event("leyline_manipulator_discount", player=context.player.index,
                    source=context.card.card_id, amount=self.amount,
                    affected=affected)


@dataclass(frozen=True)
class SummonWisps:
    count: int

    def execute(self, game: Any, context: RuleContext) -> None:
        Summon("CORE_CS2_231", self.count).execute(game, context)


@dataclass(frozen=True)
class SummonWispsEqualHand:
    def execute(self, game: Any, context: RuleContext) -> None:
        SummonWisps(len(context.player.hand)).execute(game, context)


@dataclass(frozen=True)
class DrawBottom:
    count: int = 1

    def execute(self, game: Any, context: RuleContext) -> None:
        for _ in range(self.count):
            if not context.player.deck:
                game._draw(context.player)
                continue
            card = context.player.deck.pop(0)
            game._refresh_scrappy(context.player)
            game._receive_drawn_card(context.player, card)


@dataclass(frozen=True)
class DrawThenDrawIfCostAtMost:
    maximum_cost: int

    def execute(self, game: Any, context: RuleContext) -> None:
        before = len(context.player.hand)
        game._draw(context.player)
        if len(context.player.hand) > before and context.player.hand[-1].cost <= self.maximum_cost:
            game._draw(context.player)


@dataclass(frozen=True)
class DrawMinionsAndBuffIfMana:
    count: int
    minimum_mana: int
    attack: int
    health: int

    def execute(self, game: Any, context: RuleContext) -> None:
        drawn: list[Any] = []
        for _ in range(self.count):
            card = game._draw_matching(
                context.player,
                lambda candidate: candidate.definition.card_type == "MINION",
            )
            if card is not None:
                drawn.append(card)
        if context.player.max_mana >= self.minimum_mana:
            for card in drawn:
                card.attack_delta += self.attack
                card.health_delta += self.health


@dataclass(frozen=True)
class ArmSecret:
    """Move a Secret spell from resolution into the controller's secret zone."""

    def execute(self, game: Any, context: RuleContext) -> None:
        game._arm_secret(context.player, context.card)


@dataclass(frozen=True)
class DrawMatching:
    count: int = 1
    card_type: str | None = None
    min_cost: int | None = None
    race: str | None = None
    spell_school: str | None = None
    started_in_deck: bool | None = None
    cost_delta: int = 0

    def execute(self, game: Any, context: RuleContext) -> None:
        def matches(card: Any) -> bool:
            return (
                (self.card_type is None or card.definition.card_type == self.card_type)
                and (self.min_cost is None or card.cost >= self.min_cost)
                and (self.race is None or card.has_race(self.race))
                and (self.spell_school is None or card.definition.spell_school == self.spell_school)
                and (self.started_in_deck is None or card.started_in_deck == self.started_in_deck)
            )

        for _ in range(self.count):
            if game._draw_matching(
                context.player, matches, cost_delta=self.cost_delta
            ) is None:
                break


@dataclass(frozen=True)
class OfferDeckCardDiscover:
    temporary: bool = False
    bottom_unchosen: bool = False

    def execute(self, game: Any, context: RuleContext) -> None:
        game._offer_deck_card_discover(
            context.player, temporary=self.temporary,
            bottom_unchosen=self.bottom_unchosen,
            source_card_id=context.card.card_id,
        )


@dataclass(frozen=True)
class OfferIntertwinedFate:
    def execute(self, game: Any, context: RuleContext) -> None:
        game._offer_intertwined_fate(
            context.player, source_card_id=context.card.card_id
        )


@dataclass(frozen=True)
class OfferClassDiscoverDiscountedByHeroAttack:
    card_class: str

    def execute(self, game: Any, context: RuleContext) -> None:
        attack = context.payload.get("hero_attack")
        if attack is None:
            attack = context.player.attack
        game._offer_class_discover(
            context.player, card_class=self.card_class,
            source_card_id=context.card.card_id, cost_delta=-attack,
        )


@dataclass(frozen=True)
class OfferSpellSchoolDiscover:
    spell_school: str
    cost_delta: int = 0

    def execute(self, game: Any, context: RuleContext) -> None:
        game._offer_spell_school_discover(
            context.player, spell_school=self.spell_school,
            source_card_id=context.card.card_id, cost_delta=self.cost_delta,
        )


@dataclass(frozen=True)
class OfferOutcastDiscover:
    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [
            card_id for card_id, definition in game.card_defs.items()
            if card_id in game.executable_card_ids
            and ("OUTCAST" in definition.mechanics or "Outcast" in definition.text)
        ]
        game._offer_discover(
            context.player, candidates, False,
            source_card_id=context.card.card_id,
        )
        context.player.next_spell_cost_reduction = max(
            context.player.next_spell_cost_reduction, 1
        )


@dataclass(frozen=True)
class OfferSpellDiscover:
    """Offer three executable spells from the Standard runtime pool."""

    def execute(self, game: Any, context: RuleContext) -> None:
        game._offer_spell_discover(
            context.player, source_card_id=context.card.card_id
        )


@dataclass(frozen=True)
class OfferStealthDiscover:
    """Offer three executable minions with Stealth in their printed text."""

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [
            card_id for card_id, definition in game.card_defs.items()
            if card_id in game.executable_card_ids
            and definition.card_type == "MINION"
            and ("STEALTH" in definition.mechanics or "Stealth" in definition.text)
        ]
        game._offer_discover(
            context.player, candidates, False,
            source_card_id=context.card.card_id,
        )


@dataclass(frozen=True)
class AddRandomExecutableClassCard:
    card_class: str

    def execute(self, game: Any, context: RuleContext) -> None:
        game._add_random_executable_class_card(
            context.player, card_class=self.card_class,
            source_card_id=context.card.card_id,
        )


@dataclass(frozen=True)
class SummonSpellCopyDeathrattleTreant:
    card_id: str

    def execute(self, game: Any, context: RuleContext) -> None:
        spell = context.payload.get("spell")
        if spell is None or spell.definition.spell_school != "NATURE":
            return
        player = context.player
        if len(player.board) + len(player.locations) >= 7:
            return
        treant = game._entity(self.card_id, created_by=context.card.card_id)
        treant.deathrattle_copy_card_id = spell.card_id
        treant.summoned_turn = game.turn
        game._summon(player, treant)
        game._event(
            "spell_copy_treant", player=player.index,
            source=context.card.card_id, entity=treant.entity_id,
            spell=spell.card_id,
        )


@dataclass(frozen=True)
class AddDeathrattleCopyToHand:
    def execute(self, game: Any, context: RuleContext) -> None:
        card_id = context.card.deathrattle_copy_card_id
        if card_id is None:
            return
        copy = game._entity(card_id, created_by=context.card.card_id)
        game._add_generated(context.player, copy)
        game._event(
            "deathrattle_spell_copy", player=context.player.index,
            source=context.card.card_id, card=copy.card_id,
            entity=copy.entity_id,
        )


@dataclass(frozen=True)
class CostMinusPerHandCard:
    def adjustment(self, game: Any, player: Any, card: Any) -> int:
        return -len(player.hand)


@dataclass(frozen=True)
class CostWhenSourceAttribute:
    attribute: str
    cost: int

    def adjustment(self, game: Any, player: Any, card: Any) -> int:
        return self.cost - card.cost if getattr(card, self.attribute) else 0


@dataclass(frozen=True)
class CostDiscountIfDeckAtLeast:
    minimum: int
    discount: int

    def adjustment(self, game: Any, player: Any, card: Any) -> int:
        return -self.discount if len(player.deck) >= self.minimum else 0


@dataclass(frozen=True)
class CostZeroIfControlling:
    card_id: str

    def adjustment(self, game: Any, player: Any, card: Any) -> int:
        controls = (
            any(minion.card_id == self.card_id for minion in player.board)
            or any(location.card_id == self.card_id for location in player.locations)
            or (player.weapon is not None and player.weapon.card_id == self.card_id)
        )
        return -card.cost if controls else 0


@dataclass(frozen=True)
class DamageHero:
    amount: int
    side: str = "controller"

    def execute(self, game: Any, context: RuleContext) -> None:
        amount = game._spell_effect_amount(context.player, context.card, self.amount)
        game._damage_hero(
            _recipient(game, context, self.side), amount, context.card
        )


@dataclass(frozen=True)
class AddCardCopiesToHand:
    card_id: str
    count: int = 1

    def execute(self, game: Any, context: RuleContext) -> None:
        for _ in range(self.count):
            card = game._entity(self.card_id, created_by=context.card.card_id)
            destination = game._add_generated(context.player, card)
            game._event(
                "generated_to_hand", player=context.player.index,
                card=card.card_id, entity=card.entity_id,
                source=context.card.card_id, destination=destination,
            )


@dataclass(frozen=True)
class SylvanasTriumphDamage:
    amount: int = 3

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.player.played_card_counts.get(context.card.card_id, 0) >= 2:
            DamageHero(self.amount, "opponent").execute(game, context)
            DamageBoard(self.amount, "opponent").execute(game, context)
        else:
            DamageHero(self.amount, "opponent").execute(game, context)


@dataclass(frozen=True)
class DamageBoard:
    amount: int
    side: str = "opponent"
    exclude_source: bool = False

    def execute(self, game: Any, context: RuleContext) -> None:
        player = _recipient(game, context, self.side)
        amount = game._spell_effect_amount(context.player, context.card, self.amount)
        for target in list(player.board):
            if self.exclude_source and target.entity_id == context.card.entity_id:
                continue
            game._damage_minion(player.index, target, amount, context.card)


@dataclass(frozen=True)
class ResolveDeaths:
    def execute(self, game: Any, context: RuleContext) -> None:
        game._resolve_deaths()


@dataclass(frozen=True)
class DamageActionTarget:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        amount = game._spell_effect_amount(context.player, context.card, self.amount)
        game._deal_to_target(
            context.player.index,
            (context.action.target_player, context.action.target_entity),
            amount,
            source=context.card,
        )


@dataclass(frozen=True)
class DamageActionTargetLifesteal:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        context.card.lifesteal = True
        game._deal_to_target(
            context.player.index,
            (context.action.target_player, context.action.target_entity),
            game._spell_effect_amount(context.player, context.card, self.amount),
            source=context.card,
        )


@dataclass(frozen=True)
class DamageActionTargetHealTargetOwnerIfKilled:
    amount: int
    heal: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        target = game._find_minion(
            context.action.target_player, context.action.target_entity
        )
        game._damage_minion(
            context.action.target_player, target,
            game._spell_effect_amount(context.player, context.card, self.amount),
            context.card,
        )
        killed = target.health <= 0
        game._resolve_deaths()
        if killed:
            owner = game.players[context.action.target_player]
            owner.health = min(owner.max_health, owner.health + self.heal)
        game._event(
            "damage_heal_if_killed", player=context.player.index,
            source=context.card.card_id, target=target.entity_id,
            killed=killed, heal=self.heal if killed else 0,
        )


@dataclass(frozen=True)
class DamageActionTargetThenDrawOwner:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        owner = game.players[context.action.target_player]
        target = game._find_minion(
            context.action.target_player, context.action.target_entity
        )
        game._damage_minion(
            owner.index, target,
            game._spell_effect_amount(context.player, context.card, self.amount),
            context.card,
        )
        game._draw(owner)
        game._resolve_deaths()
        game._event(
            "damage_target_owner_draw", player=context.player.index,
            source=context.card.card_id, target=target.entity_id,
            target_owner=owner.index,
        )


@dataclass(frozen=True)
class DamageActionTargetLifestealReturnOnKill:
    """Eternal Firebolt's exact minion-only damage/lifesteal/return sequence."""

    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        target = game._find_minion(
            context.action.target_player, context.action.target_entity
        )
        before = max(0, target.health)
        amount = game._spell_effect_amount(context.player, context.card, self.amount)
        game._damage_minion(
            context.action.target_player, target, amount, context.card
        )
        dealt = before - max(0, target.health)
        killed = target.health <= 0
        game._resolve_deaths()
        if killed:
            game._queue_end_turn_return(context.player, context.card)
        game._event(
            "lifesteal_damage_return_on_kill", player=context.player.index,
            source=context.card.card_id, target=target.entity_id,
            amount=amount, dealt=dealt, killed=killed,
        )


@dataclass(frozen=True)
class DamageRandomEnemyCharacters:
    amount: int
    count: int

    def execute(self, game: Any, context: RuleContext) -> None:
        targets = game._random_enemy_characters(context.player.index)
        chosen = game.rng.sample(targets, min(self.count, len(targets)))
        amount = game._spell_effect_amount(context.player, context.card, self.amount)
        for target in chosen:
            game._deal_to_target(context.player.index, target, amount, context.card)
        game._resolve_deaths()
        game._event(
            "random_enemy_damage", player=context.player.index,
            source=context.card.card_id, amount=amount, targets=chosen,
        )


@dataclass(frozen=True)
class DamageRandomSplitEnemyMinionsLifesteal:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        context.card.lifesteal = True
        enemy = game.players[1 - context.player.index]
        points = game._spell_effect_amount(context.player, context.card, self.amount)
        targets: list[int] = []
        for _ in range(points):
            living = [minion for minion in enemy.board if minion.health > 0]
            if not living:
                break


            target = game.rng.choice(living)
            game._damage_minion(enemy.index, target, 1, context.card)
            targets.append(target.entity_id)
        game._resolve_deaths()
        game._event(
            "random_split_enemy_minion_damage", player=context.player.index,
            source=context.card.card_id, amount=points, targets=targets,
        )


@dataclass(frozen=True)
class DrawZeroAttackMinion:
    def execute(self, game: Any, context: RuleContext) -> None:
        game._draw_matching(
            context.player,
            lambda card: (
                card.definition.card_type == "MINION" and card.attack == 0
            ),
        )


@dataclass(frozen=True)
class CastFanOfKnives:
    def execute(self, game: Any, context: RuleContext) -> None:
        repeats = 2 if context.card.card_id == "TLC_522" and getattr(context.card, "combo_active", False) else 1
        for _ in range(repeats):
            DamageBoard(1).execute(game, context)
            game._resolve_deaths()
            Draw().execute(game, context)


@dataclass(frozen=True)
class DamageActionTargetIfUndamaged:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        target = game._find_minion(context.action.target_player, context.action.target_entity)
        if target.damage == 0:
            game._damage_minion(context.action.target_player, target, self.amount, context.card)


@dataclass(frozen=True)
class DamageDamagedTargetWithExcessReturn:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        target = game._find_minion(context.action.target_player, context.action.target_entity)
        if target.damage <= 0:
            raise ValueError("target must already be damaged")
        remaining = max(0, target.health)
        excess = max(0, self.amount - remaining)
        game._damage_minion(
            context.action.target_player, target,
            game._spell_effect_amount(context.player, context.card, self.amount),
            context.card,
        )
        game._resolve_deaths()
        if excess and len(context.player.hand) < 10:
            returned = context.card.clone(game.next_entity_id)
            game.next_entity_id += 1
            context.player.hand.append(returned)
        game._event("damaged_target_excess_return", player=context.player.index,
                    source=context.card.card_id, target=target.entity_id,
                    excess=excess)


@dataclass(frozen=True)
class BuffActionTargetWithTaunt:
    attack: int
    health: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        target = game._find_minion(context.action.target_player, context.action.target_entity)
        target.attack_delta += self.attack
        target.health_delta += self.health
        target.taunt = True


@dataclass(frozen=True)
class BuffActionTargetWithRebornTaunt:
    attack: int
    health: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        target = game._find_minion(context.action.target_player, context.action.target_entity)
        target.attack_delta += self.attack
        target.health_delta += self.health
        target.taunt = True
        target.reborn = True


@dataclass(frozen=True)
class BuffAllFriendlyMinionsRushSacrifice:
    attack: int = 1

    def execute(self, game: Any, context: RuleContext) -> None:
        affected = []
        for minion in context.player.board:
            if minion.dormant_turns > 0 or minion.health <= 0:
                continue
            minion.attack_delta += self.attack
            minion.rush = True
            minion.dies_at_end_of_turn = True
            affected.append(minion.entity_id)
        game._event(
            "soulrest_ceremony", player=context.player.index,
            affected=affected,
        )


@dataclass(frozen=True)
class BuffActionTargetWithRush:
    attack: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        target = game._find_minion(context.action.target_player, context.action.target_entity)
        target.attack_delta += self.attack
        target.rush = True


@dataclass(frozen=True)
class Overload:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        game._overload(context.player, self.amount)


@dataclass(frozen=True)
class DiscountNextSpell:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.next_spell_cost_reduction += self.amount


@dataclass(frozen=True)
class BuffWeaponAttack:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.player.weapon is not None:
            context.player.weapon.attack += self.amount


@dataclass(frozen=True)
class DestroyActionTargetIfDamaged:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        target = game._find_minion(context.action.target_player, context.action.target_entity)
        if target.damage > 0:
            target.damage = target.max_health
            game._resolve_deaths()


@dataclass(frozen=True)
class DamageActionTargetThenAddToHandIfKilled:
    amount: int
    card_id: str

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        target = game._find_minion(
            context.action.target_player, context.action.target_entity
        )
        game._damage_minion(
            context.action.target_player, target,
            game._spell_effect_amount(context.player, context.card, self.amount),
            context.card,
        )
        killed = target.health <= 0
        game._resolve_deaths()
        if killed:
            game._draw(context.player)
        game._event(
            "damage_target_draw_if_killed", player=context.player.index,
            source=context.card.card_id, target=target.entity_id, killed=killed,
        )
        if killed:
            AddToHand(self.card_id).execute(game, context)
        game._event(
            "damage_target_add_if_killed", player=context.player.index,
            source=context.card.card_id, target=target.entity_id,
            killed=killed, generated=self.card_id if killed else None,
        )


@dataclass(frozen=True)
class DestroyActionTargetReplaceSameCost:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        owner = game.players[context.action.target_player]
        target = game._find_minion(owner.index, context.action.target_entity)
        cost = target.definition.cost
        target.damage = target.max_health
        game._resolve_deaths()
        # Resolve the replacement on the original owner's side, even when the
        # spell targeted an enemy minion.
        previous = context.player
        context.player = owner
        try:
            SummonRandomExecutableMinion(cost=cost).execute(game, context)
        finally:
            context.player = previous
        game._event(
            "destroy_replace_same_cost", player=previous.index,
            source=context.card.card_id, owner=owner.index, cost=cost,
        )


@dataclass(frozen=True)
class DamageActionTargetThenOfferRuneIfKilled:
    amount: int
    rune: str

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        target = game._find_minion(context.action.target_player, context.action.target_entity)
        game._damage_minion(
            context.action.target_player, target,
            game._spell_effect_amount(context.player, context.card, self.amount),
            context.card,
        )
        killed = target.health <= 0
        game._resolve_deaths()
        if killed:
            game._offer_rune_discover(context.player, rune=self.rune, source_card_id=context.card.card_id)


@dataclass(frozen=True)
class DamageRandomEnemyMinion:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        enemy = game.players[1 - context.player.index]
        targets = [m for m in enemy.board if m.dormant_turns == 0 and not m.stealth]
        if not targets:
            return
        target = game.rng.choice(targets)
        amount = game._spell_effect_amount(context.player, context.card, self.amount)
        game._damage_minion(enemy.index, target, amount, context.card)
        game._resolve_deaths()
        game._event(
            "random_enemy_minion_damage", player=context.player.index,
            source=context.card.card_id, amount=amount, target=target.entity_id,
        )


@dataclass(frozen=True)
class DamageRandomEnemyMinionWithHeldCost:
    amount: int
    upgraded_amount: int
    threshold: int

    def execute(self, game: Any, context: RuleContext) -> None:
        targets = [
            minion for minion in game.players[1 - context.player.index].board
            if minion.dormant_turns == 0 and not minion.stealth
        ]
        if not targets:
            return
        amount = (
            self.upgraded_amount
            if any(card.cost >= self.threshold for card in context.player.hand)
            else self.amount
        )
        target = game.rng.choice(targets)
        amount = game._spell_effect_amount(context.player, context.card, amount)
        game._damage_minion(1 - context.player.index, target, amount, context.card)
        game._resolve_deaths()
        game._event(
            "random_enemy_minion_damage", player=context.player.index,
            source=context.card.card_id, target=target.entity_id, amount=amount,
        )


@dataclass(frozen=True)
class DamageAllMinions:
    amount: int
    repeats: int = 1

    def execute(self, game: Any, context: RuleContext) -> None:
        amount = game._spell_effect_amount(context.player, context.card, self.amount)
        for _ in range(self.repeats):
            for player in game.players:
                for minion in list(player.board):
                    game._damage_minion(player.index, minion, amount, context.card)
            game._resolve_deaths()


@dataclass(frozen=True)
class DamageAllMinionsImprovedByBoardCount:
    """The printed base damage plus every minion present at resolution."""

    base_amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        minion_count = sum(len(player.board) for player in game.players)
        amount = game._spell_effect_amount(
            context.player, context.card, self.base_amount + minion_count
        )
        for player in game.players:
            for minion in list(player.board):
                game._damage_minion(player.index, minion, amount, context.card)
        game._resolve_deaths()
        game._event(
            "damage_all_minions_improved_by_board_count",
            player=context.player.index, source=context.card.card_id,
            minion_count=minion_count, amount=amount,
        )


@dataclass(frozen=True)
class DamageLowestHealthEnemyRepeated:
    amount: int
    repeats: int

    def execute(self, game: Any, context: RuleContext) -> None:
        amount = game._spell_effect_amount(context.player, context.card, self.amount)
        targets: list[tuple[int, int | None]] = []
        for _ in range(self.repeats):
            candidates = game._random_enemy_characters(context.player.index)
            if not candidates:
                break
            def health(target: tuple[int, int | None]) -> int:
                return (
                    game.players[target[0]].health
                    if target[1] is None
                    else game._find_minion(*target).health
                )
            lowest = min(health(target) for target in candidates)
            target = game.rng.choice([
                candidate for candidate in candidates if health(candidate) == lowest
            ])
            game._deal_to_target(context.player.index, target, amount, context.card)
            game._resolve_deaths()
            targets.append(target)
        game._event(
            "lowest_health_enemy_damage", player=context.player.index,
            source=context.card.card_id, amount=amount, targets=targets,
        )


@dataclass(frozen=True)
class BuffFriendlyMinionsDiscardRandomSpellSchool:
    attack: int
    health: int
    spell_school: str

    def execute(self, game: Any, context: RuleContext) -> None:
        player = context.player
        def buff() -> None:
            for minion in player.board:
                minion.attack_delta += self.attack
                minion.health_delta += self.health
        buff()
        candidates = [
            card for card in player.hand
            if card.definition.card_type == "SPELL"
            and card.definition.spell_school == self.spell_school
        ]
        discarded = None
        if candidates:
            discarded = game.rng.choice(candidates)
            player.hand.remove(discarded)
            game._event(
                "discard", player=player.index, card=discarded.card_id,
                entity=discarded.entity_id, source=context.card.card_id,
            )
            buff()
        game._event(
            "buff_discard_spell_school", player=player.index,
            source=context.card.card_id, spell_school=self.spell_school,
            discarded=None if discarded is None else discarded.card_id,
            attack=self.attack, health=self.health,
        )


@dataclass(frozen=True)
class DamageActionTargetDiscardRandomSpellSchool:
    amount: int
    spell_school: str

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        amount = game._spell_effect_amount(context.player, context.card, self.amount)
        target = (context.action.target_player, context.action.target_entity)
        game._deal_to_target(context.player.index, target, amount, context.card)
        candidates = [
            card for card in context.player.hand
            if card.definition.card_type == "SPELL"
            and card.definition.spell_school == self.spell_school
        ]
        discarded = None
        if candidates:
            discarded = game.rng.choice(candidates)
            context.player.hand.remove(discarded)
            game._event(
                "discard", player=context.player.index, card=discarded.card_id,
                entity=discarded.entity_id, source=context.card.card_id,
            )
            game._deal_to_target(context.player.index, target, amount, context.card)
        game._resolve_deaths()
        game._event(
            "damage_discard_spell_school", player=context.player.index,
            source=context.card.card_id, target=target,
            amount=amount, discarded=None if discarded is None else discarded.card_id,
        )


@dataclass(frozen=True)
class DamageActionTargetThenSummonByDamage:
    amount: int
    card_id: str
    attack: int
    health: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        amount = game._spell_effect_amount(context.player, context.card, self.amount)
        game._deal_to_target(
            context.player.index,
            (context.action.target_player, context.action.target_entity),
            amount, context.card,
        )
        game._resolve_deaths()
        summoned = []
        for _ in range(amount):
            if len(context.player.board) + len(context.player.locations) >= 7:
                break
            token = game._entity(self.card_id, created_by=context.card.card_id)
            token.attack_delta += self.attack - token.definition.attack
            token.health_delta += self.health - token.definition.health
            token.summoned_turn = game.turn
            game._summon(context.player, token)
            summoned.append(token.entity_id)
        game._event(
            "damage_then_summon", player=context.player.index,
            source=context.card.card_id, amount=amount,
            summoned=summoned,
        )


@dataclass(frozen=True)
class DamageActionTargetThenBuffFriendlyRace:
    """Resolve direct spell damage, then apply a permanent tribal buff."""

    amount: int
    race: str
    attack: int
    health: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        amount = game._spell_effect_amount(context.player, context.card, self.amount)
        target = (context.action.target_player, context.action.target_entity)
        game._deal_to_target(context.player.index, target, amount, context.card)
        game._resolve_deaths()
        buffed = []
        for minion in context.player.board:
            if minion.has_race(self.race):
                minion.attack_delta += self.attack
                minion.health_delta += self.health
                buffed.append(minion.entity_id)
        game._event(
            "damage_then_buff_friendly_race", player=context.player.index,
            source=context.card.card_id, target=target, amount=amount,
            race=self.race, buffed=buffed,
        )


@dataclass(frozen=True)
class DrawMinionThenSummonStatCopy:
    """Draw a minion and summon a fresh fixed-stat copy if board space exists."""

    attack: int
    health: int

    def execute(self, game: Any, context: RuleContext) -> None:
        drawn = game._draw_matching(
            context.player,
            lambda card: card.definition.card_type == "MINION",
        )
        summoned = None
        if drawn is not None and len(context.player.board) + len(context.player.locations) < 7:
            copy = drawn.clone(game.next_entity_id)
            game.next_entity_id += 1
            copy.started_in_deck = False
            copy.created_by = context.card.card_id
            copy.attack_delta += self.attack - copy.attack
            copy.health_delta += self.health - copy.max_health
            copy.damage = 0
            copy.divine_shield = True
            copy.divine_shield_hits = 1
            copy.summoned_turn = game.turn
            game._summon(context.player, copy)
            summoned = copy.entity_id
        game._event(
            "draw_minion_summon_stat_copy", player=context.player.index,
            source=context.card.card_id,
            drawn=None if drawn is None else drawn.card_id,
            summoned=summoned, attack=self.attack, health=self.health,
        )


@dataclass(frozen=True)
class DrawDifferentTribeMinionsAndBuff:
    """Draw up to two minions whose printed tribe sets do not overlap."""

    attack: int
    health: int

    @staticmethod
    def _tribes(card: Any) -> set[str]:
        tribes = {card.definition.race, *card.definition.races} - {""}
        return tribes or {"NONE"}

    def execute(self, game: Any, context: RuleContext) -> None:
        player = context.player
        drawn = []
        first = game._draw_matching(
            player, lambda card: card.definition.card_type == "MINION"
        )
        if first is not None:
            first.attack_delta += self.attack
            first.health_delta += self.health
            drawn.append(first)
            excluded = self._tribes(first)
            second = game._draw_matching(
                player,
                lambda card: (
                    card.definition.card_type == "MINION"
                    and self._tribes(card).isdisjoint(excluded)
                ),
            )
            if second is not None:
                second.attack_delta += self.attack
                second.health_delta += self.health
                drawn.append(second)
        game._event(
            "draw_different_tribe_minions", player=player.index,
            source=context.card.card_id, cards=[card.card_id for card in drawn],
            attack=self.attack, health=self.health,
        )


@dataclass(frozen=True)
class DamageAllCharacters:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        amount = game._spell_effect_amount(context.player, context.card, self.amount)
        for player in game.players:
            game._damage_hero(player, amount, context.card)
            for minion in list(player.board):
                game._damage_minion(
                    player.index, minion, amount, context.card
                )


@dataclass(frozen=True)
class DamageAllEnemies:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        enemy = game.players[1 - context.player.index]
        amount = game._spell_effect_amount(context.player, context.card, self.amount)
        game._damage_hero(enemy, amount, context.card)
        for minion in list(enemy.board):
            game._damage_minion(enemy.index, minion, amount, context.card)
        game._resolve_deaths()


@dataclass(frozen=True)
class DamageRandomEnemyMinionsThenDrawPerKill:
    amount: int
    count: int

    def execute(self, game: Any, context: RuleContext) -> None:
        enemy = game.players[1 - context.player.index]
        killed = 0
        for _ in range(self.count):
            if not enemy.board:
                break
            target = game.rng.choice(list(enemy.board))
            game._damage_minion(enemy.index, target, self.amount, context.card)
            if target.health <= 0:
                killed += 1
            game._resolve_deaths()
        for _ in range(killed):
            game._draw(context.player)


@dataclass(frozen=True)
class DamageAllMinionsThenDrawPerDeath:
    """Deal equal damage to every minion, then draw once per death."""

    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        before = sum(len(player.board) for player in game.players)
        amount = game._spell_effect_amount(context.player, context.card, self.amount)
        for player in game.players:
            for minion in list(player.board):
                game._damage_minion(player.index, minion, amount, context.card)
        game._resolve_deaths()
        after = sum(len(player.board) for player in game.players)
        for _ in range(max(0, before - after)):
            game._draw(context.player)
        game._event(
            "damage_all_minions_draw_per_death", player=context.player.index,
            source=context.card.card_id, amount=amount, deaths=max(0, before - after),
        )


@dataclass(frozen=True)
class FreezeActionTarget:
    """Freeze a targeted character for the current turn."""

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        target_player = game.players[context.action.target_player]
        if context.action.target_entity is None:
            target_player.frozen_turn = game.turn
        else:
            game._find_minion(
                context.action.target_player, context.action.target_entity
            ).frozen_turn = game.turn


@dataclass(frozen=True)
class FreezeAllEnemyMinions:
    def execute(self, game: Any, context: RuleContext) -> None:
        enemy = game.players[1 - context.player.index]
        for minion in enemy.board:
            minion.frozen_turn = game.turn


@dataclass(frozen=True)
class RefreshHeroPower:
    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.hero_power_used = False


@dataclass(frozen=True)
class DiscountNextBeast:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.next_beast_cost_reduction = max(
            context.player.next_beast_cost_reduction, self.amount
        )


@dataclass(frozen=True)
class DrawAndArmorRepeatIfNoMinionLastTurn:
    armor: int

    def execute(self, game: Any, context: RuleContext) -> None:
        repeats = 1 if context.player.minion_played_last_turn else 2
        for _ in range(repeats):
            game._draw(context.player)
            game._gain_armor(context.player, self.armor)


@dataclass(frozen=True)
class DiscountHeldCard:
    entity_id: int
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        for card in context.player.hand:
            if card.entity_id == self.entity_id:
                card.cost_delta -= self.amount
                game._event("discount_held_card", player=context.player.index,
                            source=context.card.card_id, entity=card.entity_id,
                            card=card.card_id, amount=self.amount)
                return


@dataclass(frozen=True)
class GiveHeldCardToOpponent:
    entity_id: int

    def execute(self, game: Any, context: RuleContext) -> None:
        opponent = game.players[1 - context.player.index]
        for index, card in enumerate(context.player.hand):
            if card.entity_id == self.entity_id:
                context.player.hand.pop(index)
                if len(opponent.hand) < 10:
                    opponent.hand.append(card)
                return


@dataclass(frozen=True)
class DrawThreeThenGiveOne:
    def execute(self, game: Any, context: RuleContext) -> None:
        drawn = []
        for _ in range(3):
            before = {card.entity_id for card in context.player.hand}
            game._draw(context.player)
            drawn.extend(card for card in context.player.hand if card.entity_id not in before)
        if drawn:
            game.pending_choice = {
                "kind": "RULE_CHOICE", "player": context.player.index,
                "card": context.card, "action": context.action,
                "options": tuple(
                    (f"give_{card.entity_id}_{card.card_id}", (GiveHeldCardToOpponent(card.entity_id),))
                    for card in drawn
                ),
            }


@dataclass(frozen=True)
class DrawTwoThenChooseDiscount:
    amount: int = 2

    def execute(self, game: Any, context: RuleContext) -> None:
        drawn = []
        for _ in range(2):
            before = {card.entity_id for card in context.player.hand}
            game._draw(context.player)
            drawn.extend(card for card in context.player.hand if card.entity_id not in before)
        if not drawn:
            return
        options = tuple(
            (f"discount_{card.entity_id}_{card.card_id}",
             (DiscountHeldCard(card.entity_id, self.amount),))
            for card in drawn
        )
        game.pending_choice = {
            "kind": "RULE_CHOICE", "player": context.player.index,
            "card": context.card, "action": context.action,
            "options": options,
        }


@dataclass(frozen=True)
class DrawMinionThenBuffIfAttack:
    """Draw a minion and conditionally buff it based on printed attack."""

    minimum_attack: int
    health: int
    armor: int

    def execute(self, game: Any, context: RuleContext) -> None:
        drawn = game._draw_matching(
            context.player,
            lambda card: card.definition.card_type == "MINION",
        )
        qualified = drawn is not None and drawn.definition.attack >= self.minimum_attack
        if qualified:
            drawn.health_delta += self.health
            game._gain_armor(context.player, self.armor)
        game._event(
            "draw_minion_conditional_buff", player=context.player.index,
            source=context.card.card_id,
            drawn=None if drawn is None else drawn.card_id,
            qualified=qualified,
        )


@dataclass(frozen=True)
class DrawMinionsByCosts:
    """Draw one minion at each listed printed cost; Kindred discounts them."""

    costs: tuple[int, ...]
    discount_if_kindred: int = 1

    def execute(self, game: Any, context: RuleContext) -> None:
        player = context.player
        races = set(player.played_races_last_turn)
        kindred = bool(races & set(context.card.definition.races))
        for cost in self.costs:
            drawn = game._draw_matching(
                player,
                lambda card, cost=cost: (
                    card.definition.card_type == "MINION"
                    and card.definition.cost == cost
                ),
            )
            if drawn is not None and kindred:
                drawn.cost_delta -= self.discount_if_kindred
        game._event(
            "draw_minions_by_cost", player=player.index,
            source=context.card.card_id, costs=list(self.costs), kindred=kindred,
        )
@dataclass(frozen=True)
class DestroyMinionsByAttack:
    minimum: int

    def execute(self, game: Any, context: RuleContext) -> None:
        for player in game.players:
            for minion in list(player.board):
                if minion.dormant_turns <= 0 and minion.attack >= self.minimum:
                    minion.damage = minion.max_health


@dataclass(frozen=True)
class DestroyEnemyWeapon:
    def execute(self, game: Any, context: RuleContext) -> None:
        enemy = game.players[1 - context.player.index]
        if enemy.weapon is not None:
            game._destroy_weapon(enemy)


@dataclass(frozen=True)
class DestroyAllMinions:
    def execute(self, game: Any, context: RuleContext) -> None:
        for player in game.players:
            for minion in player.board:
                minion.damage = minion.max_health


@dataclass(frozen=True)
class DestroyAllMinionsAndLocations:
    def execute(self, game: Any, context: RuleContext) -> None:
        DestroyAllMinions().execute(game, context)
        for player in game.players:
            player.locations.clear()
        game._resolve_deaths()


@dataclass(frozen=True)
class SetAllMinionHealth:
    health: int

    def execute(self, game: Any, context: RuleContext) -> None:
        for player in game.players:
            for minion in player.board:
                minion.health_delta += self.health - minion.max_health
                minion.damage = min(minion.damage, max(0, minion.max_health - self.health))


@dataclass(frozen=True)
class TransformActionTarget:
    card_id: str

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        owner = game.players[context.action.target_player]
        target = game._find_minion(owner.index, context.action.target_entity)
        replacement = game._entity(self.card_id, created_by=context.card.card_id)
        replacement.entity_id = target.entity_id
        owner.board[owner.board.index(target)] = replacement
        game._event("transform", player=context.player.index,
                    source=context.card.card_id, target=target.entity_id,
                    replacement=self.card_id)


@dataclass(frozen=True)
class BuffAllFriendlyMinions:
    attack: int
    health: int

    def execute(self, game: Any, context: RuleContext) -> None:
        for minion in context.player.board:
            minion.attack_delta += self.attack
            minion.health_delta += self.health


@dataclass(frozen=True)
class SilenceAndDestroyAllOtherMinions:
    def execute(self, game: Any, context: RuleContext) -> None:
        destroyed: list[int] = []
        for player in game.players:
            for minion in list(player.board):
                if minion.entity_id == context.card.entity_id:
                    continue
                game._silence_minion(minion)
                minion.damage = minion.max_health
                destroyed.append(minion.entity_id)
        game._resolve_deaths()
        game._event(
            "silence_destroy_all_other_minions", player=context.player.index,
            source=context.card.card_id, targets=destroyed,
        )


@dataclass(frozen=True)
class SummonMatchingFromBottomDeck:
    count: int
    race: str | None = None

    def execute(self, game: Any, context: RuleContext) -> None:
        player = context.player
        # The simulator stores the bottom at index 0 and draws from the end.
        candidates = list(player.deck[:self.count])
        for card in candidates:
            if self.race is not None and not card.has_race(self.race):
                continue
            if len(player.board) + len(player.locations) >= 7:
                break
            player.deck.remove(card)
            card.summoned_turn = game.turn
            game._summon(player, card)
            game._event(
                "summon_from_bottom_deck", player=player.index,
                card=card.card_id, entity=card.entity_id,
                source=context.card.card_id,
            )


@dataclass(frozen=True)
class HeraldRagnaros:
    def execute(self, game: Any, context: RuleContext) -> None:
        game._herald_ragnaros(context.player, source=context.card.card_id)


@dataclass(frozen=True)
class HeraldRagnarosCombo:
    """Herald once, then deal Combo damage to the selected enemy character."""

    def execute(self, game: Any, context: RuleContext) -> None:
        game._herald_ragnaros(context.player, source=context.card.card_id)
        if context.card.combo_active:
            DamageActionTarget(3).execute(game, context)


@dataclass(frozen=True)
class BuffSourceHealthPerHandCard:
    def execute(self, game: Any, context: RuleContext) -> None:
        context.card.health_delta += len(context.player.hand)


@dataclass(frozen=True)
class GainArmor:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        game._gain_armor(context.player, self.amount)


@dataclass(frozen=True)
class GainManaCrystals:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        gained = min(self.amount, 10 - context.player.max_mana)
        context.player.max_mana += gained
        context.player.mana += gained


@dataclass(frozen=True)
class GainMana:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.mana += self.amount


@dataclass(frozen=True)
class GrantStartTurnTemporaryMana:
    turns: int

    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.start_turn_temporary_mana_charges += self.turns


@dataclass(frozen=True)
class GainHeroAttack:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.hero_attack_bonus += self.amount


@dataclass(frozen=True)
class GrowWickerfangLeg:
    """The leg's own end-turn buff; the game syncs its Colossal parent."""

    def execute(self, game: Any, context: RuleContext) -> None:
        game._grow_wickerfang_leg(context.player, context.card)


@dataclass(frozen=True)
class SetHeroPower:
    card_id: str | None

    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.hero_power_id = self.card_id
        game._event(
            "hero_power_imbued", player=context.player.index,
            source=context.card.card_id, hero_power=self.card_id,
        )


@dataclass(frozen=True)
class ReduceEnemyMinionAttackUntilNextControllerTurn:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        enemy = game.players[1 - context.player.index]
        for minion in enemy.board:
            minion.attack_delta -= self.amount
            # Store the signed delta and the controller's next turn as the
            # expiry point.  The engine restores it before start-turn effects.
            minion.temporary_attack_modifiers.append(
                (-self.amount, context.player.index)
            )
        game._event(
            "temporary_enemy_attack_reduction", player=context.player.index,
            source=context.card.card_id, amount=self.amount,
            targets=[minion.entity_id for minion in enemy.board],
        )


@dataclass(frozen=True)
class OfferImbueHeroPowerOptions:
    def execute(self, game: Any, context: RuleContext) -> None:
        game._offer_imbue_options(
            context.player, source_card_id=context.card.card_id
        )


@dataclass(frozen=True)
class BuffActionTargetPerFriendlyMinion:
    attack: int = 0
    health: int = 0

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        target = game._find_minion(
            context.action.target_player, context.action.target_entity
        )
        count = len(context.player.board)
        target.attack_delta += self.attack * count
        target.health_delta += self.health * count


@dataclass(frozen=True)
class SetActionTargetStats:
    attack: int
    health: int
    stealth: bool = False

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        target = game._find_minion(
            context.action.target_player, context.action.target_entity
        )
        target.attack_delta += self.attack - target.attack
        target.health_delta += self.health - target.max_health
        if self.stealth:
            target.stealth = True


@dataclass(frozen=True)
class SetEnemyHealthOneWithDragonRepeat:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("enemy minion target is required")
        target = game._find_minion(context.action.target_player, context.action.target_entity)
        target.health_delta += 1 - target.max_health
        dragons = [card for card in context.player.hand if card.has_race("DRAGON")]
        if dragons:
            options = [m for m in game.players[1 - context.player.index].board if m.entity_id != target.entity_id]
            if options:
                game.pending_choice = {
                    "kind": "EARTHEN_ROAR_PICK", "player": context.player.index,
                    "options": options, "source_card_id": context.card.card_id,
                }


@dataclass(frozen=True)
class DestroyActionTarget:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        target = game._find_minion(
            context.action.target_player, context.action.target_entity
        )
        target.damage = target.max_health


@dataclass(frozen=True)
class DestroyActionTargetIfAttackAtMost:
    maximum_attack: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        target = game._find_minion(
            context.action.target_player, context.action.target_entity
        )
        if target.attack <= self.maximum_attack:
            target.damage = target.max_health
            game._resolve_deaths()


@dataclass(frozen=True)
class DamageActionTargetThenDrawIfKilled:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        owner = game.players[context.action.target_player]
        target = game._find_minion(
            context.action.target_player, context.action.target_entity
        )
        game._damage_minion(
            owner.index, target,
            game._spell_effect_amount(context.player, context.card, self.amount),
            context.card,
        )
        killed = target.health <= 0
        game._resolve_deaths()


@dataclass(frozen=True)
class DestroyLegendaryTarget:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        target = game._find_minion(context.action.target_player, context.action.target_entity)
        if target.definition.rarity != "LEGENDARY":
            raise ValueError("target must be legendary")
        target.damage = target.max_health
        game._resolve_deaths()


@dataclass(frozen=True)
class DamageActionTargetThenDrawIfSurvives:
    """Deal damage to a minion, then draw only when it remains alive."""

    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        owner = game.players[context.action.target_player]
        target = game._find_minion(
            context.action.target_player, context.action.target_entity
        )
        game._damage_minion(
            owner.index, target,
            game._spell_effect_amount(context.player, context.card, self.amount),
            context.card,
        )
        survives = target.health > 0
        game._resolve_deaths()
        if survives:
            game._draw(context.player)
        game._event(
            "damage_target_draw_if_survives", player=context.player.index,
            source=context.card.card_id, target=target.entity_id,
            survives=survives,
        )


@dataclass(frozen=True)
class DamageActionTargetThenDrawIfHandEmpty:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        target_player = context.action.target_player
        target = game.players[target_player] if context.action.target_entity is None else game._find_minion(target_player, context.action.target_entity)
        if context.action.target_entity is None:
            game._damage_hero(game.players[target_player], self.amount, context.card)
        else:
            game._damage_minion(target_player, target, self.amount, context.card)
            game._resolve_deaths()
        if not context.player.hand:
            game._draw(context.player)


@dataclass(frozen=True)
class ShuffleActionTargetIntoOwnerDeck:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        owner = game.players[context.action.target_player]
        target = game._find_minion(owner.index, context.action.target_entity)
        owner.board.remove(target)
        returned = game._entity(target.card_id, created_by=context.card.card_id)
        owner.deck.insert(game.rng.randrange(len(owner.deck) + 1), returned)
        game._refresh_continuous(owner)
        game._event(
            "shuffle_minion", player=owner.index, card=target.card_id,
            entity=target.entity_id, source=context.card.card_id,
        )


@dataclass(frozen=True)
class TakeControlActionTargetUntilEndOfOwnerTurn:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        owner = game.players[context.action.target_player]
        target = game._find_minion(owner.index, context.action.target_entity)
        owner.board.remove(target)
        context.player.board.append(target)
        target.return_control_to = owner.index
        target.return_control_at_end_of_turn = owner.index
        target.cant_attack_turn = game.turn
        game._refresh_continuous(owner)
        game._refresh_continuous(context.player)
        game._event(
            "temporary_control", player=context.player.index,
            target_player=owner.index, entity=target.entity_id,
            card=target.card_id, source=context.card.card_id,
        )


@dataclass(frozen=True)
class OfferEffectChoice:
    """Pause resolution until the controller selects one effect bundle."""

    options: tuple[tuple[str, tuple[Effect, ...]], ...]

    def execute(self, game: Any, context: RuleContext) -> None:
        game.pending_choice = {
            "kind": "RULE_CHOICE",
            "player": context.player.index,
            "card": context.card,
            "action": context.action,
            "options": self.options,
        }
        game._event(
            "rule_choice", player=context.player.index,
            card=context.card.card_id,
            options=[label for label, _ in self.options],
        )


@dataclass(frozen=True)
class IfSourceAttribute:
    attribute: str
    effects: tuple[Effect, ...]

    def execute(self, game: Any, context: RuleContext) -> None:
        if getattr(context.card, self.attribute):
            for effect in self.effects:
                effect.execute(game, context)


@dataclass(frozen=True)
class ManaCrystalByHeldSpend:
    threshold: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.card.mana_spent_while_held >= self.threshold:
            GainManaCrystals(1).execute(game, context)
        else:
            GainMana(1).execute(game, context)


@dataclass(frozen=True)
class BuffActionTarget:
    attack: int = 0
    health: int = 0
    event: str | None = None

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        target = game._find_minion(
            context.action.target_player, context.action.target_entity
        )
        target.attack_delta += self.attack
        target.health_delta += self.health
        if self.event:
            game._event(
                self.event, player=context.player.index,
                target_player=context.action.target_player,
                target=target.entity_id,
            )


@dataclass(frozen=True)
class SilentStrike:
    """Give a minion +3 Attack; stealth targets also fire their attack damage."""

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("minion target is required")
        target = game._find_minion(context.action.target_player, context.action.target_entity)
        target.attack_delta += 3
        game._event("silent_strike_buff", player=context.player.index,
                    target=target.entity_id, attack=3, stealth=target.stealth)
        if target.stealth:
            DamageRandomEnemyMinion(target.attack).execute(game, context)


@dataclass(frozen=True)
class BuffZone:
    zone: str
    attack: int = 0
    health: int = 0
    card_types: tuple[str, ...] = ()
    require_attribute: str | None = None
    exclude_source: bool = False

    def execute(self, game: Any, context: RuleContext) -> None:
        cards = getattr(context.player, self.zone)
        affected = []
        for card in cards:
            if self.exclude_source and card.entity_id == context.card.entity_id:
                continue
            if self.card_types and card.definition.card_type not in self.card_types:
                continue
            if self.require_attribute and not getattr(card, self.require_attribute):
                continue
            card.attack_delta += self.attack
            card.health_delta += self.health
            affected.append(card.entity_id)
        game._event(
            "zone_buff", player=context.player.index,
            source=context.card.card_id, zone=self.zone,
            attack=self.attack, health=self.health,
            card_types=list(self.card_types),
            require_attribute=self.require_attribute,
            affected_count=len(affected), affected=affected,
        )


@dataclass(frozen=True)
class BuffFriendlyMinionsAndShield:
    """Give friendly minions attack and Divine Shield."""

    attack: int

    def execute(self, game: Any, context: RuleContext) -> None:
        affected: list[int] = []
        for minion in context.player.board:
            minion.attack_delta += self.attack
            minion.divine_shield = True
            minion.divine_shield_hits = max(1, minion.divine_shield_hits)
            affected.append(minion.entity_id)
        game._event(
            "buff_friendly_minions_shield", player=context.player.index,
            source=context.card.card_id, attack=self.attack, affected=affected,
        )


@dataclass(frozen=True)
class GrantDeathrattleSummon:
    """Give friendly minions a simple summon-on-death effect."""

    card_id: str

    def execute(self, game: Any, context: RuleContext) -> None:
        affected: list[int] = []
        for minion in context.player.board:
            minion.deathrattle_summon_card_id = self.card_id
            affected.append(minion.entity_id)
        game._event(
            "grant_deathrattle_summon", player=context.player.index,
            source=context.card.card_id, summon=self.card_id, affected=affected,
        )


@dataclass(frozen=True)
class BuffActionTargetElusive:
    """Buff a friendly target and make it elusive to targeted spells."""

    attack: int
    health: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        target = game._find_minion(
            context.action.target_player, context.action.target_entity
        )
        target.attack_delta += self.attack
        target.health_delta += self.health
        target.elusive = True
        game._event(
            "buff_action_target_elusive", player=context.player.index,
            source=context.card.card_id, target=target.entity_id,
            attack=self.attack, health=self.health,
        )


@dataclass(frozen=True)
class GrantPoisonousActionTarget:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        target = game._find_minion(
            context.action.target_player, context.action.target_entity
        )
        if not target.has_race("UNDEAD"):
            raise ValueError("Poison Breath requires an Undead target")
        target.poisonous = True
        game._event(
            "grant_poisonous", player=context.player.index,
            source=context.card.card_id, target=target.entity_id,
        )


@dataclass(frozen=True)
class SummonActionTargetCopy:
    """Summon a copy of the friendly target's current state."""

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        owner = game.players[context.action.target_player]
        target = game._find_minion(owner.index, context.action.target_entity)
        if len(owner.board) + len(owner.locations) >= 7:
            return
        copy = target.clone(game.next_entity_id)
        game.next_entity_id += 1
        copy.created_by = context.card.card_id
        copy.damage = 0
        copy.summoned_turn = game.turn
        game._summon(owner, copy)
        game._event(
            "summon_action_target_copy", player=context.player.index,
            source=context.card.card_id, target=target.entity_id,
            copy=copy.entity_id,
        )


@dataclass(frozen=True)
class GenerateRandomCombinedShatter:
    """Add a random supported Shatter card from another class, combined."""

    card_ids: tuple[str, ...]

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [
            card_id for card_id in self.card_ids
            if card_id in game.card_defs
            and game.card_defs[card_id].card_class != context.player.card_class
        ]
        if not candidates:
            candidates = list(self.card_ids)
        if not candidates:
            return
        card_id = game.rng.choice(sorted(candidates))
        card = game._entity(card_id, created_by=context.card.card_id)
        card.shatter_combined = True
        destination = game._add_generated(context.player, card)
        game._event(
            "combined_shatter_generated", player=context.player.index,
            source=context.card.card_id, card=card_id, entity=card.entity_id,
            destination=destination,
        )


@dataclass(frozen=True)
class AddCurrentSourceStats:
    attack_multiplier: int = 0
    health_multiplier: int = 0

    def execute(self, game: Any, context: RuleContext) -> None:
        attack = context.card.attack
        health = context.card.max_health
        context.card.attack_delta += attack * self.attack_multiplier
        context.card.health_delta += health * self.health_multiplier


@dataclass(frozen=True)
class SetSourceAttributes:
    values: tuple[tuple[str, Any], ...]

    def execute(self, game: Any, context: RuleContext) -> None:
        for name, value in self.values:
            setattr(context.card, name, value)


@dataclass(frozen=True)
class Summon:
    card_id: str
    count: int = 1
    side: str = "controller"

    def execute(self, game: Any, context: RuleContext) -> None:
        player = _recipient(game, context, self.side)
        for _ in range(self.count):
            if len(player.board) + len(player.locations) >= 7:
                break
            minion = game._entity(self.card_id, created_by=context.card.card_id)
            minion.summoned_turn = game.turn
            game._summon(player, minion)


@dataclass(frozen=True)
class SummonWithTaunt:
    card_id: str
    count: int = 1

    def execute(self, game: Any, context: RuleContext) -> None:
        player = context.player
        for _ in range(self.count):
            if len(player.board) + len(player.locations) >= 7:
                break
            minion = game._entity(self.card_id, created_by=context.card.card_id)
            minion.taunt = True
            minion.summoned_turn = game.turn
            game._summon(player, minion)


@dataclass(frozen=True)
class AddTwinspellCopy:
    card_id: str

    def execute(self, game: Any, context: RuleContext) -> None:
        copy = game._entity(self.card_id, created_by=context.card.card_id)
        game._add_generated(context.player, copy)


@dataclass(frozen=True)
class SummonAndSpendManaBuff:
    card_id: str
    count: int
    attack_per_mana: int = 1
    health_per_mana: int = 1

    def execute(self, game: Any, context: RuleContext) -> None:
        player = context.player
        spent = max(0, player.mana)
        player.mana = 0
        for _ in range(self.count):
            if len(player.board) + len(player.locations) >= 7:
                break
            minion = game._entity(self.card_id, created_by=context.card.card_id)
            minion.summoned_turn = game.turn
            minion.attack_delta += spent * self.attack_per_mana
            minion.health_delta += spent * self.health_per_mana
            game._summon(player, minion)
        game._event("summon_spend_mana_buff", player=player.index,
                    source=context.card.card_id, spent=spent, count=self.count)


@dataclass(frozen=True)
class SummonDormant:
    """Summon a minion that cannot act until its fixed dormant countdown ends."""
    card_id: str
    dormant_turns: int
    count: int = 1
    side: str = "controller"

    def execute(self, game: Any, context: RuleContext) -> None:
        player = _recipient(game, context, self.side)
        for _ in range(self.count):
            if len(player.board) + len(player.locations) >= 7:
                break
            minion = game._entity(self.card_id, created_by=context.card.card_id)
            minion.summoned_turn = game.turn
            minion.dormant_turns = self.dormant_turns
            game._summon(player, minion)


@dataclass(frozen=True)
class SummonRandomDreadseed:
    """Summon one random Dormant Dreadseed from the current seed pool."""

    def execute(self, game: Any, context: RuleContext) -> None:
        # Hearthstone's Dreadseed pool has three distinct tokens with
        # different dormant durations and keywords.  Keep the pool explicit
        # so seeded simulations and audit reports remain reproducible.
        card_id = game.rng.choice(("EDR_840t", "EDR_840t1", "EDR_840t2"))
        dormant = {"EDR_840t": 2, "EDR_840t1": 1, "EDR_840t2": 3}[card_id]
        SummonDormant(card_id, dormant).execute(game, context)


@dataclass(frozen=True)
class BuffDamagedFriendlyMinions:
    attack: int
    health: int

    def execute(self, game: Any, context: RuleContext) -> None:
        for minion in context.player.board:
            if minion.damage > 0:
                minion.attack_delta += self.attack
                minion.health_delta += self.health


@dataclass(frozen=True)
class SummonRandomExecutableMinion:
    cost: int | None = None
    min_cost: int | None = None
    require_taunt: bool = False
    count: int = 1

    def execute(self, game: Any, context: RuleContext) -> None:
        for _ in range(self.count):
            game._summon_random_executable_minion(
                context.player, source_card_id=context.card.card_id,
                cost=self.cost, min_cost=self.min_cost,
                require_taunt=self.require_taunt,
            )


@dataclass(frozen=True)
class SummonStatsByHandThenAttackRandomEnemyMinion:
    card_id: str

    def execute(self, game: Any, context: RuleContext) -> None:
        player = context.player
        if len(player.board) + len(player.locations) >= 7:
            return
        stats = len(player.hand)
        minion = game._entity(self.card_id, created_by=context.card.card_id)
        minion.attack_delta += stats - minion.definition.attack
        minion.health_delta += stats - minion.definition.health
        minion.summoned_turn = game.turn
        game._summon(player, minion)
        enemy = game.players[1 - player.index]
        targets = [
            target for target in enemy.board
            if target.dormant_turns == 0 and not target.stealth
        ]
        if targets:
            target = game.rng.choice(targets)
            game._forced_minion_attack(player.index, minion, enemy.index, target)
        game._event(
            "hand_stat_summon", player=player.index,
            source=context.card.card_id, card=minion.card_id,
            entity=minion.entity_id, stats=stats,
        )


@dataclass(frozen=True)
class AddToHand:
    card_id: str
    count: int = 1
    side: str = "controller"

    def execute(self, game: Any, context: RuleContext) -> None:
        player = _recipient(game, context, self.side)
        for _ in range(self.count):
            card = game._entity(self.card_id, created_by=context.card.card_id)
            if len(player.hand) < 10:
                player.hand.append(card)
                game._event(
                    "generated_to_hand", player=player.index,
                    card=card.card_id, entity=card.entity_id,
                    source=context.card.card_id,
                )
            else:
                game._event(
                    "generated_burned", player=player.index,
                    card=card.card_id, source=context.card.card_id,
                )


@dataclass(frozen=True)
class AddShaladrassilDreamCards:
    """Get the fixed Dream set, using Corrupted versions only if earned."""

    def execute(self, game: Any, context: RuleContext) -> None:
        regular = ("DREAM_05", "DREAM_04", "DREAM_01", "DREAM_02", "DREAM_03")
        corrupted = (
            "EDR_846t1", "EDR_846t2", "EDR_846t3", "EDR_846t4", "EDR_846t5",
        )
        card_ids = corrupted if context.card.higher_cost_card_played_while_held else regular
        for card_id in card_ids:
            card = game._entity(card_id, created_by=context.card.card_id)
            if len(context.player.hand) < 10:
                context.player.hand.append(card)
                game._event(
                    "generated_to_hand", player=context.player.index,
                    card=card.card_id, entity=card.entity_id,
                    source=context.card.card_id,
                )
            else:
                game._event(
                    "generated_burned", player=context.player.index,
                    card=card.card_id, source=context.card.card_id,
                )


@dataclass(frozen=True)
class ReturnActionTargetToOwnerHand:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None or context.action.target_entity is None:
            raise ValueError("minion target is required")
        owner = game.players[context.action.target_player]
        target = game._find_minion(owner.index, context.action.target_entity)
        owner.board.remove(target)
        target.damage = 0
        target.attack_delta = target.health_delta = 0
        target.temporary_attack_modifiers.clear()
        target.temporary_health_modifiers.clear()
        target.temporary_immune_expiry_turn = -1
        target.destroy_at_turn_start = -1
        target.playable_after_turn = game.turn + 1
        if len(owner.hand) < 10:
            owner.hand.append(target)
            destination = "hand"
        else:
            destination = "burned"
        game._event(
            "return_to_hand", player=owner.index, entity=target.entity_id,
            card=target.card_id, source=context.card.card_id, destination=destination,
        )


@dataclass(frozen=True)
class ReturnFriendlyAndSummonSpider:
    """Return the selected friendly minion, then summon a 4/4 Stealth spider."""

    def execute(self, game: Any, context: RuleContext) -> None:
        ReturnActionTargetToOwnerHand().execute(game, context)
        Summon("EDR_523t").execute(game, context)


@dataclass(frozen=True)
class ReturnAllEnemyMinionsToHand:
    def execute(self, game: Any, context: RuleContext) -> None:
        enemy = game.players[1 - context.player.index]
        returned = []
        for target in list(enemy.board):
            enemy.board.remove(target)
            target.damage = 0
            target.attack_delta = target.health_delta = 0
            target.temporary_attack_modifiers.clear()
            target.temporary_health_modifiers.clear()
            target.playable_after_turn = game.turn + 1
            destination = game._add_generated(enemy, target)
            returned.append(target.entity_id)
            game._event(
                "return_to_hand", player=enemy.index,
                entity=target.entity_id, card=target.card_id,
                source=context.card.card_id, destination=destination,
            )
        game._event(
            "twilight_mistress_bounce", player=context.player.index,
            returned=returned,
        )


@dataclass(frozen=True)
class NightmareBuffThenDestroy:
    """Classic Dream Nightmare: +5/+5, then destroy at caster's next turn."""

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None or context.action.target_entity is None:
            raise ValueError("minion target is required")
        target = game._find_minion(context.action.target_player, context.action.target_entity)
        target.attack_delta += 5
        target.health_delta += 5
        target.destroy_at_turn_start = context.player.index
        game._event(
            "nightmare_buff", player=context.player.index, target=target.entity_id,
            source=context.card.card_id, destroy_at_turn_start=context.player.index,
        )


@dataclass(frozen=True)
class CorruptedNightmareBuff:
    """Corrupted Nightmare: +5/+5 and immune for only the current turn."""

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None or context.action.target_entity is None:
            raise ValueError("minion target is required")
        target = game._find_minion(context.action.target_player, context.action.target_entity)
        expiry = 1 - context.player.index
        target.attack_delta += 5
        target.health_delta += 5
        target.temporary_attack_modifiers.append((5, expiry))
        target.temporary_health_modifiers.append((5, expiry))
        target.immune = True
        target.temporary_immune_expiry_turn = expiry
        game._event(
            "corrupted_nightmare_buff", player=context.player.index,
            target=target.entity_id, source=context.card.card_id,
        )


@dataclass(frozen=True)
class DamageAllCharactersExceptYsera:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        amount = game._spell_effect_amount(context.player, context.card, self.amount)
        for player in game.players:
            game._damage_hero(player, amount, context.card)
            for minion in list(player.board):
                if minion.definition.name != "Ysera":
                    game._damage_minion(player.index, minion, amount, context.card)


@dataclass(frozen=True)
class AddToDeck:
    card_id: str
    count: int = 1
    position: str = "top"
    shuffle: bool = False
    side: str = "controller"
    attributes: tuple[tuple[str, Any], ...] = ()

    def execute(self, game: Any, context: RuleContext) -> None:
        player = _recipient(game, context, self.side)
        for _ in range(self.count):
            card = game._entity(self.card_id, created_by=context.card.card_id)
            for name, value in self.attributes:
                setattr(card, name, value)
            if self.position == "top":
                player.deck.append(card)
            elif self.position == "bottom":
                player.deck.insert(0, card)
            else:
                raise ValueError(f"unknown deck position: {self.position}")
        if self.shuffle:
            game.rng.shuffle(player.deck)


@dataclass(frozen=True)
class IncreaseOpponentMinionCostNextTurn:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        opponent = game.players[1 - context.player.index]
        opponent.minion_cost_increase_turn = game.turn + 1
        opponent.minion_cost_increase_amount += self.amount
        game._event(
            "next_turn_minion_cost_increase", player=opponent.index,
            source=context.card.card_id, amount=self.amount,
            active_turn=opponent.minion_cost_increase_turn,
        )


@dataclass(frozen=True)
class HealHero:
    amount: int
    side: str = "controller"

    def execute(self, game: Any, context: RuleContext) -> None:
        player = _recipient(game, context, self.side)
        amount = game._spell_effect_amount(context.player, context.card, self.amount)
        player.health = min(player.max_health, player.health + amount)


@dataclass(frozen=True)
class HealActionTarget:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        amount = game._spell_effect_amount(context.player, context.card, self.amount)
        if context.action.target_entity is None:
            target = game.players[context.action.target_player]
            target.health = min(target.max_health, target.health + amount)
        else:
            target = game._find_minion(
                context.action.target_player, context.action.target_entity
            )
            target.damage = max(0, target.damage - amount)


@dataclass(frozen=True)
class HealActionTargetToFull:
    """Restore a targeted minion to full Health."""

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        if context.action.target_entity is None:
            raise ValueError("minion target is required")
        target = game._find_minion(
            context.action.target_player, context.action.target_entity
        )
        target.damage = 0


@dataclass(frozen=True)
class HealFriendlyCharacters:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        player = context.player
        amount = game._spell_effect_amount(context.player, context.card, self.amount)
        player.health = min(player.max_health, player.health + amount)
        for minion in player.board:
            minion.damage = max(0, minion.damage - amount)


@dataclass(frozen=True)
class SetPlayerAttributes:
    values: tuple[tuple[str, Any], ...]
    event: str | None = None

    def execute(self, game: Any, context: RuleContext) -> None:
        for name, value in self.values:
            setattr(context.player, name, value)
        if self.event:
            game._event(
                self.event, player=context.player.index,
                source=context.card.card_id,
                values=dict(self.values),
            )


@dataclass(frozen=True)
class CardRule:
    card_id: str
    hooks: dict[Hook, tuple[Effect, ...]]
    source: RuleSource
    targeting: TargetSpec | None = None
    cost_modifier: CostModifier | None = None


class RuleRegistry:
    def __init__(self, rules: tuple[CardRule, ...] = ()):
        self._rules: dict[str, CardRule] = {}
        for rule in rules:
            self.register(rule)

    def register(self, rule: CardRule) -> None:
        if rule.card_id in self._rules:
            raise ValueError(f"duplicate card rule: {rule.card_id}")
        self._rules[rule.card_id] = rule

    def dispatch(
        self, hook: Hook, card_id: str, game: Any, context: RuleContext
    ) -> bool:
        rule = self._rules.get(card_id)
        if rule is None or hook not in rule.hooks:
            return False
        for effect in rule.hooks[hook]:
            effect.execute(game, context)
        return True

    def targeting(self, card_id: str) -> TargetSpec | None:
        rule = self._rules.get(card_id)
        return None if rule is None else rule.targeting

    def has_hook(self, hook: Hook, card_id: str) -> bool:
        rule = self._rules.get(card_id)
        return rule is not None and hook in rule.hooks

    def cost_adjustment(self, game: Any, player: Any, card: Any) -> int:
        rule = self._rules.get(card.card_id)
        if rule is None or rule.cost_modifier is None:
            return 0
        return rule.cost_modifier.adjustment(game, player, card)

    def manifest(self) -> list[dict[str, Any]]:
        rows = []
        for card_id in sorted(self._rules):
            rule = self._rules[card_id]
            rows.append({
                "card_id": card_id,
                "hooks": sorted(hook.value for hook in rule.hooks),
                "source": asdict(rule.source),
                "targeting": (
                    None if rule.targeting is None else asdict(rule.targeting)
                ),
                "effects": {
                    hook.value: [type(effect).__name__ for effect in effects]
                    for hook, effects in rule.hooks.items()
                },
                "cost_modifier": (
                    None if rule.cost_modifier is None
                    else type(rule.cost_modifier).__name__
                ),
            })
        return rows


def build_rule_registry() -> RuleRegistry:
    rosetta = "vendor/RosettaStone@e10749b5f0c08d3a6135bce317cb11d1738846ad"
    local = "HearthstoneJSON build 251332 + local rule tests"
    return RuleRegistry((
        CardRule(
            "GAME_005", {Hook.SPELL: (GainMana(1),)},
            RuleSource(
                "upstream_adapted", rosetta, "GAME_005", "AGPL-3.0",
                ("test_windpeak_wyrm_battlecry_and_coin_spell_rules",),
            ),
        ),
        CardRule(
            "CORE_EX1_169", {Hook.SPELL: (GainMana(1),)},
            RuleSource(
                "upstream_adapted", rosetta, "EX1_169", "AGPL-3.0",
                ("test_temporary_mana_spells",),
            ),
        ),
        CardRule(
            "CORE_OG_047",
            {Hook.SPELL: (OfferEffectChoice((
                ("hero_attack_4", (GainHeroAttack(4),)),
                ("armor_8", (GainArmor(8),)),
            )),)},
            RuleSource(
                "upstream_adapted", rosetta, "OG_047", "AGPL-3.0",
                ("test_feral_rage_choose_one",),
            ),
        ),
        CardRule(
            "TLC_COIN1", {Hook.SPELL: (GainMana(1),)},
            RuleSource(
                "powerlog_verified", "Power.log 61e3baf3 + HearthstoneJSON 251332",
                verification=("test_temporary_mana_spells",),
            ),
        ),
        CardRule(
            "CATA_138",
            {Hook.SPELL: (BuffActionTargetPerFriendlyMinion(1, 1),)},
            RuleSource(
                "powerlog_verified", "Power.log 61e3baf3 + HearthstoneJSON 251332",
                verification=("test_forest_gift_scales_with_friendly_board",),
            ),
            TargetSpec(TargetKind.FRIENDLY_MINION),
        ),
        CardRule(
            "CATA_131", {Hook.BATTLECRY: (ManaCrystalByHeldSpend(4),)},
            RuleSource(
                "powerlog_verified", "Power.log 61e3baf3 + HearthstoneJSON 251332",
                verification=("test_felwood_treant_tracks_mana_spent_while_held",),
            ),
        ),
        CardRule(
            "CATA_303",
            {Hook.SPELL: (DamageActionTargetHealTargetOwnerIfKilled(5, 5),)},
            RuleSource(
                "official_text_and_engine_verified",
                "HearthstoneJSON 251332",
                verification=("test_purifying_breath_heals_target_owner_on_kill",),
            ),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        *(
            CardRule(
                card_id, {Hook.END_TURN: (GrowWickerfangLeg(),)},
                RuleSource(
                    "official_text_and_engine_verified",
                    "HearthstoneJSON 251332; engine Colossal parent linkage",
                    "CATA_139t",
                    verification=(
                        "test_wickerfang_colossal_legs_grow_and_sync_their_stats",
                    ),
                ),
            )
            for card_id in ("CATA_139t", "CATA_139t2", "CATA_139t3", "CATA_139t4")
        ),
        CardRule(
            "CATA_492", {Hook.LOCATION: (HeraldRagnaros(), Draw())},
            RuleSource(
                "powerlog_verified", "Power.log 23282dea + HearthstoneJSON 251332",
                verification=("test_shrine_of_twilight_location_heralds_and_draws",),
            ),
        ),
        CardRule(
            "CATA_190p", {Hook.HERO_POWER: (GainHeroAttack(5),)},
            RuleSource(
                "powerlog_verified", "Power.log 23282dea + HearthstoneJSON 251332",
                verification=("test_ruthless_custom_hero_power",),
            ),
        ),
        CardRule(
            "CATA_496",
            {Hook.SPELL: (TakeControlActionTargetUntilEndOfOwnerTurn(),)},
            RuleSource(
                "powerlog_verified", "Power.log 23282dea + HearthstoneJSON 251332",
                verification=("test_cursed_chains_temporarily_controls_and_returns_minion",),
            ),
            TargetSpec(TargetKind.ENEMY_MINION),
        ),
        CardRule(
            "CATA_581",
            {Hook.SPELL: (DamageAllMinionsImprovedByBoardCount(1),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_decimation_scales_from_minions_present_at_resolution",),
            ),
        ),
        CardRule(
            "CATA_725",
            {Hook.BATTLECRY: (HeraldRagnaros(),), Hook.DEATHRATTLE: (HealHero(3),)},
            RuleSource(
                "powerlog_verified", "Power.log 23282dea + HearthstoneJSON 251332",
                verification=("test_shadowsworn_disciple_heralds_and_heals_on_death",),
            ),
        ),
        CardRule(
            "CAP_404", {Hook.SPELL: (
                IncreaseOpponentMinionCostNextTurn(2),
                AddToDeck("CAP_400t2t", count=2, shuffle=True, side="opponent"),
            )},
            RuleSource(
                "powerlog_verified",
                "Power.log 23282dea + HearthstoneJSON 251332",
                verification=("test_harsh_sentence_applies_next_turn_tax_and_imp_formants",),
            ),
        ),
        CardRule(
            "DINO_431", {
                Hook.DEATHRATTLE: (
                    SummonRandomExecutableMinion(min_cost=5, require_taunt=True),
                ),
            },
            RuleSource(
                "powerlog_verified",
                "Power.log 23282dea + HearthstoneJSON 251332",
                verification=("test_atlasaurus_deathrattle_summons_large_taunt",),
            ),
        ),
        CardRule(
            "DINO_432",
            {Hook.SPELL: (SetActionTargetStats(5, 4, stealth=True), Draw(2))},
            RuleSource(
                "powerlog_verified", "Power.log 61e3baf3 + HearthstoneJSON 251332",
                verification=("test_panther_mask_sets_stats_stealth_and_draws",),
            ),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "EDR_270", {
                Hook.SPELL: (OfferSpellSchoolDiscover("NATURE", cost_delta=-2),),
            },
            RuleSource(
                "powerlog_verified",
                "Power.log 61e3baf3 + HearthstoneJSON 251332",
                verification=("test_horn_of_plenty_discovers_discounted_nature_spell",),
            ),
        ),
        CardRule(
            "EDR_271", {
                Hook.AFTER_PLAY: (SummonSpellCopyDeathrattleTreant("EDR_271t"),),
            },
            RuleSource(
                "powerlog_verified",
                "Power.log 61e3baf3 + HearthstoneJSON 251332",
                verification=("test_grove_shaper_summons_treant_that_copies_nature_spell",),
            ),
        ),
        CardRule(
            "EDR_271t", {Hook.DEATHRATTLE: (AddDeathrattleCopyToHand(),)},
            RuleSource(
                "official_text_and_powerlog_verified",
                "HearthstoneJSON 251332 + Power.log 61e3baf3",
                verification=("test_grove_shaper_summons_treant_that_copies_nature_spell",),
            ),
        ),
        CardRule(
            "EDR_449", {Hook.BATTLECRY: (SetHeroPower("EDR_449p"),)},
            RuleSource(
                "powerlog_verified",
                "Power.log 23282dea + HearthstoneJSON 251332",
                verification=("test_lunarwing_messenger_imbues_hero_power",),
            ),
        ),
        CardRule(
            "EDR_852", {Hook.BATTLECRY: (SetHeroPower("EDR_449p"),)},
            RuleSource(
                "official_text_and_engine_pattern",
                "HearthstoneJSON 251332; Priest Imbue maps to Blessing of the Moon",
                verification=("test_bitterbloom_knight_imbues_priest_power",),
            ),
        ),
        CardRule(
            "EDR_449p", {Hook.HERO_POWER: (OfferImbueHeroPowerOptions(),)},
            RuleSource(
                "official_text_and_powerlog_verified",
                "Blizzard card library 114069 + Power.log 23282dea",
                verification=("test_blessing_of_the_moon_offers_discounted_temporary_cards",),
            ),
        ),
        CardRule(
            "EDR_970", {
                Hook.BATTLECRY: (
                    ReduceEnemyMinionAttackUntilNextControllerTurn(2),
                    SetHeroPower("EDR_449p"),
                ),
            },
            RuleSource(
                "powerlog_verified",
                "Power.log 23282dea + HearthstoneJSON 251332",
                verification=("test_kaldorei_priestess_reduces_then_restores_enemy_attack",),
            ),
        ),
        CardRule(
            "EDR_846", {Hook.SPELL: (AddShaladrassilDreamCards(),)},
            RuleSource(
                "official_text_and_powerlog_verified",
                "HearthstoneJSON 251332 + Power.log 61e3baf3",
                verification=("test_shaladrassil_generates_regular_or_corrupted_dream_set",),
            ),
        ),
        CardRule(
            "DREAM_05", {Hook.SPELL: (NightmareBuffThenDestroy(),)},
            RuleSource(
                "official_text", "HearthstoneJSON 251332",
                verification=("test_shaladrassil_generated_dream_spells_follow_their_rules",),
            ),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "DREAM_04", {Hook.SPELL: (ReturnActionTargetToOwnerHand(),)},
            RuleSource(
                "official_text", "HearthstoneJSON 251332",
                verification=("test_shaladrassil_generated_dream_spells_follow_their_rules",),
            ),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "DREAM_02", {Hook.SPELL: (DamageAllCharactersExceptYsera(5), ResolveDeaths())},
            RuleSource(
                "official_text", "HearthstoneJSON 251332",
                verification=("test_shaladrassil_generated_dream_spells_follow_their_rules",),
            ),
        ),
        CardRule(
            "EDR_846t1", {Hook.SPELL: (CorruptedNightmareBuff(),)},
            RuleSource(
                "official_text", "HearthstoneJSON 251332",
                verification=("test_shaladrassil_generated_dream_spells_follow_their_rules",),
            ),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "EDR_846t2",
            {Hook.SPELL: (ShuffleActionTargetIntoOwnerDeck(),)},
            RuleSource(
                "powerlog_verified", "Power.log 61e3baf3 + HearthstoneJSON 251332",
                verification=("test_corrupted_dream_shuffles_without_death",),
            ),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "EDR_846t4",
            {Hook.SPELL: (
                DamageHero(5, "opponent"), DamageBoard(5, "opponent"),
                ResolveDeaths(),
            )},
            RuleSource(
                "powerlog_verified", "Power.log 61e3baf3 + HearthstoneJSON 251332",
                verification=("test_corrupted_awakening_damages_only_enemies",),
            ),
        ),
        CardRule(
            "EDR_476",
            {Hook.SPELL: (
                DamageHero(4, "opponent"), DamageBoard(4, "opponent"),
                HealFriendlyCharacters(4), ResolveDeaths(),
            )},
            RuleSource(
                "powerlog_verified", "Power.log 23282dea/61e3baf3 + HearthstoneJSON 251332",
                verification=("test_moonwell_damages_enemies_and_heals_friends",),
            ),
        ),
        CardRule(
            "END_007",
            {Hook.SPELL: (
                DamageActionTarget(1), GainHeroAttack(1), Draw(), GainArmor(1),
                ResolveDeaths(),
            )},
            RuleSource(
                "powerlog_verified", "Power.log 61e3baf3 + HearthstoneJSON 251332",
                verification=("test_press_the_advantage_all_effects",),
            ),
            TargetSpec(TargetKind.ANY_CHARACTER),
        ),
        CardRule(
            "END_011", {Hook.SPELL: (GrantStartTurnTemporaryMana(3),)},
            RuleSource(
                "powerlog_verified", "Power.log 61e3baf3 + HearthstoneJSON 251332",
                verification=("test_acceleration_aura_grants_three_future_temporary_crystals",),
            ),
        ),
        CardRule(
            "JAIL_872", {Hook.AFTER_HERO_ATTACK: (Draw(),)},
            RuleSource(
                "powerlog_verified", "Power.log 61e3baf3 + HearthstoneJSON 251332",
                verification=("test_spider_rider_draws_after_hero_attack",),
            ),
        ),
        CardRule(
            "JAIL_201", {Hook.SPELL: (OfferEffectChoice((
                ("hero_attack_2", (GainHeroAttack(2),)),
                ("random_druid_card", (AddRandomExecutableClassCard("DRUID"),)),
            )),)},
            RuleSource(
                "powerlog_verified",
                "Power.log 61e3baf3 + HearthstoneJSON 251332",
                verification=("test_secret_ingredient_choose_one_attack_or_druid_card",),
            ),
        ),
        CardRule(
            "JAIL_875", {
                Hook.AFTER_HERO_ATTACK: (
                    OfferClassDiscoverDiscountedByHeroAttack("DRUID"),
                ),
            },
            RuleSource(
                "powerlog_verified",
                "Power.log 61e3baf3 + HearthstoneJSON 251332",
                verification=("test_staff_of_trickery_discovers_druid_card_discounted_by_attack",),
            ),
        ),
        CardRule(
            "JAIL_510",
            {Hook.SPELL: (
                DestroyAllMinions(), ResolveDeaths(),
                SummonMatchingFromBottomDeck(3, race="DEMON"),
            )},
            RuleSource(
                "powerlog_verified", "Power.log 23282dea + HearthstoneJSON 251332",
                verification=("test_annihilation_destroys_all_and_summons_bottom_demons",),
            ),
        ),
        CardRule(
            "JAIL_511", {
                Hook.LOCATION: (
                    SummonStatsByHandThenAttackRandomEnemyMinion("JAIL_511t"),
                ),
            },
            RuleSource(
                "powerlog_verified",
                "Power.log 23282dea + HearthstoneJSON 251332",
                verification=("test_spire_of_solitude_summons_hand_sized_demon_and_attacks",),
            ),
        ),
        CardRule(
            "JAIL_513", {Hook.BATTLECRY: (BuffSourceHealthPerHandCard(),)},
            RuleSource(
                "powerlog_verified", "Power.log 23282dea + HearthstoneJSON 251332",
                verification=("test_caged_cranium_counts_hand_after_play",),
            ),
        ),
        CardRule(
            "JAIL_432", {
                Hook.BATTLECRY: (
                    IfSourceAttribute(
                        "opponent_card_copy_played_while_held",
                        (DamageBoard(2, side="opponent"), ResolveDeaths()),
                    ),
                ),
            },
            RuleSource(
                "powerlog_verified",
                "Power.log 23282dea + HearthstoneJSON 251332",
                verification=("test_mind_sweeper_tracks_opponent_card_copy_while_held",),
            ),
        ),
        CardRule(
            "JAIL_433", {
                Hook.SPELL: (DestroyActionTarget(), ResolveDeaths()),
            },
            RuleSource(
                "powerlog_verified",
                "Power.log 61e3baf3 + HearthstoneJSON 251332",
                verification=("test_unshackle_soul_discounts_after_opponent_copy_and_destroys",),
            ),
            TargetSpec(TargetKind.ANY_MINION),
            cost_modifier=CostWhenSourceAttribute(
                "opponent_card_copy_played_while_held", 1
            ),
        ),
        CardRule(
            "JAIL_912", {
                Hook.DEATHRATTLE: (
                    HealHero(6), SummonRandomExecutableMinion(6),
                ),
            },
            RuleSource(
                "powerlog_verified",
                "Power.log 23282dea + HearthstoneJSON 251332",
                verification=("test_soothsayer_deathrattle_heals_and_summons_six_cost",),
            ),
        ),
        CardRule(
            "JAIL_941",
            {Hook.SPELL: (HealActionTarget(4), AddToHand("JAIL_941t"))},
            RuleSource(
                "powerlog_verified", "Power.log 23282dea + HearthstoneJSON 251332",
                verification=("test_holy_embrace_heals_and_generates_dark_embrace",),
            ),
            TargetSpec(TargetKind.ANY_CHARACTER),
        ),
        CardRule(
            "JAIL_941t", {Hook.SPELL: (DamageActionTarget(4), ResolveDeaths())},
            RuleSource(
                "powerlog_verified", "Power.log 23282dea + HearthstoneJSON 251332",
                verification=("test_dark_embrace_deals_damage",),
            ),
            TargetSpec(TargetKind.ANY_CHARACTER),
        ),
        CardRule(
            "MEND_042", {Hook.SPELL: (
                HealFriendlyCharacters(8),
                SummonRandomExecutableMinion(cost=8, count=2),
            )},
            RuleSource(
                "powerlog_verified",
                "Power.log 61e3baf3 + HearthstoneJSON 251332",
                verification=("test_lifebloom_heals_friendly_characters_and_summons_eight_costs",),
            ),
        ),
        CardRule(
            "TIME_890",
            {Hook.BATTLECRY: (SilenceAndDestroyAllOtherMinions(),)},
            RuleSource(
                "official_text_and_powerlog_verified",
                "HearthstoneJSON 251332 + Power.log 61e3baf3",
                verification=("test_medivh_battlecry_and_fabled_cost_reductions",),
            ),
            cost_modifier=CostZeroIfControlling("TIME_890t2"),
        ),
        CardRule(
            "TIME_890t",
            {},
            RuleSource(
                "official_text_and_powerlog_verified",
                "HearthstoneJSON 251332 + Power.log 61e3baf3",
                verification=("test_atiesh_doubles_generic_spell_damage_and_healing",),
            ),
            cost_modifier=CostZeroIfControlling("TIME_890"),
        ),
        CardRule(
            "TIME_890t2",
            {Hook.LOCATION: (SummonRandomExecutableMinion(8, count=2),)},
            RuleSource(
                "official_text", "HearthstoneJSON 251332",
                verification=("test_medivh_battlecry_and_fabled_cost_reductions",),
            ),
            cost_modifier=CostZeroIfControlling("TIME_890t"),
        ),
        CardRule(
            "TIME_432", {Hook.SPELL: (OfferIntertwinedFate(),)},
            RuleSource(
                "powerlog_verified",
                "Power.log 23282dea + HearthstoneJSON 251332",
                verification=("test_intertwined_fate_copies_one_card_from_each_deck",),
            ),
        ),
        CardRule(
            "TIME_702",
            {Hook.SPELL: (
                DamageActionTarget(3),
                IfSourceAttribute("minion_played_while_held", (GainArmor(5),)),
                ResolveDeaths(),
            )},
            RuleSource(
                "powerlog_verified", "Power.log 61e3baf3 + HearthstoneJSON 251332",
                verification=("test_ebb_and_flow_tracks_minion_played_while_held",),
            ),
            TargetSpec(TargetKind.ANY_CHARACTER),
        ),
        CardRule(
            "TIME_701", {Hook.SPELL: (OfferDeckCardDiscover(bottom_unchosen=True),)},
            RuleSource(
                "powerlog_verified", "Power.log 61e3baf3 + HearthstoneJSON 251332",
                verification=("test_waveshaping_discovers_from_deck_and_bottoms_others",),
            ),
        ),
        CardRule(
            "JAIL_514", {Hook.SPELL: (Draw(3),)},
            RuleSource(
                "powerlog_verified", "Power.log 23282dea + HearthstoneJSON 251332",
                verification=("test_unseen_atlas_costs_less_per_hand_card_and_draws",),
            ),
            cost_modifier=CostMinusPerHandCard(),
        ),
        CardRule(
            "TLC_451", {Hook.SPELL: (OfferDeckCardDiscover(temporary=True),)},
            RuleSource(
                "powerlog_verified", "Power.log 23282dea + HearthstoneJSON 251332",
                verification=("test_cursed_catacombs_discovers_temporary_deck_card",),
            ),
        ),
        CardRule(
            "CORE_CS2_004",
            {Hook.SPELL: (BuffActionTarget(health=2), Draw())},
            RuleSource(
                "upstream_adapted", rosetta, "CS2_004", "AGPL-3.0",
                ("test_power_word_shield",),
            ),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "CORE_CS2_062",
            {Hook.SPELL: (DamageAllCharacters(3), ResolveDeaths())},
            RuleSource(
                "upstream_adapted", rosetta, "CS2_062", "AGPL-3.0",
                ("test_hellfire_damages_all_characters",),
            ),
        ),
        CardRule(
            "CORE_CS2_029",
            {Hook.SPELL: (DamageActionTarget(6), ResolveDeaths())},
            RuleSource(
                "upstream_adapted", rosetta, "CS2_029", "AGPL-3.0",
                ("test_fireball_and_flamestrike",),
            ),
            TargetSpec(TargetKind.ENEMY_CHARACTER),
        ),
        CardRule(
            "CORE_CS2_032",
            {Hook.SPELL: (DamageBoard(5), ResolveDeaths())},
            RuleSource(
                "upstream_adapted", rosetta, "CS2_032", "AGPL-3.0",
                ("test_fireball_and_flamestrike",),
            ),
        ),
        CardRule(
            "CORE_EX1_610", {Hook.SPELL: (ArmSecret(),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_explosive_trap_triggers_after_hero_is_attacked",),
            ),
        ),
        CardRule(
            "CORE_EX1_611", {Hook.SPELL: (ArmSecret(),)},
            RuleSource(
                "upstream_adapted", rosetta, "EX1_611", "AGPL-3.0",
                ("test_freezing_trap",),
            ),
        ),
        CardRule(
            "CORE_EX1_554", {Hook.SPELL: (ArmSecret(),)},
            RuleSource(
                "upstream_adapted", rosetta, "EX1_554", "AGPL-3.0",
                ("test_snake_trap",),
            ),
        ),
        CardRule(
            "CORE_EX1_130", {Hook.SPELL: (ArmSecret(),)},
            RuleSource(
                "upstream_adapted", rosetta, "EX1_130", "AGPL-3.0",
                ("test_noble_sacrifice",),
            ),
        ),
        CardRule(
            "CORE_EX1_294", {Hook.SPELL: (ArmSecret(),)},
            RuleSource(
                "upstream_adapted", rosetta, "EX1_294", "AGPL-3.0",
                ("test_mirror_entity",),
            ),
        ),
        CardRule(
            "CORE_FP1_020", {Hook.SPELL: (ArmSecret(),)},
            RuleSource(
                "upstream_adapted", rosetta, "FP1_020", "AGPL-3.0",
                ("test_avenge",),
            ),
        ),
        CardRule(
            "CORE_RLK_567", {},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_shadow_of_demise_transform",),
            ),
        ),
        CardRule(
            "TIME_039", {},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_deja_vu_discover_opponent_hand",),
            ),
        ),
        CardRule(
            "JAIL_720", {},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_lotus_bookie_deathrattle_coin",),
            ),
        ),
        CardRule(
            "TLC_515", {},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_cultist_map_deck_discover",),
            ),
        ),
        CardRule(
            "TLC_816", {Hook.SPELL: (Draw(2),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_gravedawn_sunbloom_draws_two",),
            ),
        ),
        CardRule(
            "CORE_YOP_001", {Hook.SPELL: (OfferOutcastDiscover(),)},
            RuleSource(
                "upstream_adapted", rosetta, "YOP_001", "AGPL-3.0",
                ("test_illidari_studies",),
            ),
        ),
        CardRule(
            "DINO_417", {Hook.SPELL: (BuffAllFriendlyMinionsRushSacrifice(),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_soulrest_ceremony",),
            ),
        ),
        CardRule(
            "JAIL_998", {Hook.BATTLECRY: (BuffActionTargetWithRush(2),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_defias_smuggler_battlecry",),
            ),
            TargetSpec(TargetKind.FRIENDLY_MINION),
        ),
        CardRule(
            "DINO_411", {Hook.BATTLECRY: (DrawZeroAttackMinion(),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_holy_eggbearer_draws_zero_attack",),
            ),
        ),
        CardRule(
            "CATA_201", {Hook.BATTLECRY: (ReturnAllEnemyMinionsToHand(),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_twilight_mistress_returns_enemy_board",),
            ),
        ),
        CardRule(
            "TLC_902", {Hook.SPELL: (AddCardCopiesToHand("TLC_630t", 2),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_infestation_generates_stingers",),
            ),
        ),
        CardRule(
            "TLC_522", {
                Hook.BATTLECRY: (CastFanOfKnives(),),
                Hook.DEATHRATTLE: (CastFanOfKnives(),),
            },
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_opu_the_unseen_fan_of_knives",),
            ),
        ),
        CardRule(
            "CATA_785", {Hook.SPELL: (HeraldRagnarosCombo(),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_rite_of_twilight_herald",),
            ),
            TargetSpec(TargetKind.ENEMY_CHARACTER, optional=True),
        ),
        CardRule(
            "EDR_840", {Hook.SPELL: (Draw(1), SummonRandomDreadseed())},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_grim_harvest_draws_and_summons_dreadseed",),
            ),
        ),
        CardRule(
            "EDR_523", {Hook.SPELL: (ReturnFriendlyAndSummonSpider(),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_web_of_deception_returns_and_summons",),
            ),
            TargetSpec(TargetKind.FRIENDLY_MINION),
        ),
        CardRule(
            "CAP_001", {Hook.SPELL: (SilentStrike(),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_silent_strike_stealth_branch",),
            ),
            TargetSpec(TargetKind.FRIENDLY_MINION),
        ),
        CardRule(
            "CAP_002", {Hook.SPELL: (OfferStealthDiscover(),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_follow_the_footsteps_stealth_discover",),
            ),
        ),
        CardRule(
            "TIME_875t", {Hook.BATTLECRY: (DrawThenShuffleSource(),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_king_llane_draws_and_shuffles_back",),
            ),
        ),
        CardRule(
            "CORE_ULD_133", {Hook.END_TURN: (DrawIfUnspentMana(),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_crystal_merchant_draws_with_unspent_mana",),
            ),
        ),
        CardRule(
            "MEND_504", {Hook.SPELL: (DrawAndDiscountDrawn(),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_leyline_nexus_discounts_drawn_card",),
            ),
        ),
        CardRule(
            "EDR_804", {Hook.SPELL: (DestroyFriendlyWispDraw(),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_divination_sacrifices_wisp_and_draws",),
            ),
            TargetSpec(TargetKind.FRIENDLY_MINION),
        ),
        CardRule(
            "GIL_553", {Hook.SPELL: (SummonWispsEqualHand(),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_wispering_woods_summons_by_hand_size",),
            ),
        ),
        CardRule(
            "OG_195", {Hook.SPELL: (OfferEffectChoice((
                ("summon_seven_wisps", (SummonWisps(7),)),
                ("buff_friendly_minions", (BuffAllFriendlyMinions(2, 2),)),
            )),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_wisps_of_old_gods_offers_choice",),
            ),
        ),
        CardRule(
            "MEND_500", {Hook.SPELL: (DamageRandomEnemyMinionExcess(4),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_bursting_leyline_excess_damage",),
            ),
        ),
        CardRule(
            "LOOT_537", {Hook.BATTLECRY: (DiscountCardsNotStartedInDeck(2),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_leyline_manipulator_discounts_generated_cards",),
            ),
        ),
        CardRule(
            "CATA_158", {Hook.DEATHRATTLE: (HeraldRagnaros(),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_maniacal_follower_deathrattle_herald",),
            ),
        ),
        CardRule(
            "TLC_630t", {Hook.SPELL: (DamageRandomEnemyCharacters(2, 1), Summon("TLC_903t"),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332"),
        ),
        CardRule(
            "EX1_379", {Hook.SPELL: (ArmSecret(),)},
            RuleSource(
                "upstream_adapted", rosetta, "EX1_379", "AGPL-3.0",
                ("test_repentance",),
            ),
        ),
        CardRule(
            "EX1_136", {Hook.SPELL: (ArmSecret(),)},
            RuleSource(
                "upstream_adapted", rosetta, "EX1_136", "AGPL-3.0",
                ("test_redemption",),
            ),
        ),
        CardRule(
            "FP1_018", {Hook.SPELL: (ArmSecret(),)},
            RuleSource(
                "upstream_adapted", rosetta, "FP1_018", "AGPL-3.0",
                ("test_duplicate",),
            ),
        ),
        CardRule(
            "EX1_594", {Hook.SPELL: (ArmSecret(),)},
            RuleSource(
                "upstream_adapted", rosetta, "EX1_594", "AGPL-3.0",
                ("test_vaporize",),
            ),
        ),
        CardRule(
            "EX1_609", {Hook.SPELL: (ArmSecret(),)},
            RuleSource(
                "upstream_adapted", rosetta, "EX1_609", "AGPL-3.0",
                ("test_snipe",),
            ),
        ),
        CardRule(
            "CORE_KAR_004", {Hook.SPELL: (ArmSecret(),)},
            RuleSource(
                "upstream_adapted", rosetta, "KAR_004", "AGPL-3.0",
                ("test_cat_trick",),
            ),
        ),
        CardRule(
            "CORE_LOOT_101", {Hook.SPELL: (ArmSecret(),)},
            RuleSource(
                "upstream_adapted",
                "vendor/fireplace/cards/kobolds/mage.py; RosettaStone CoreCardsGenTests",
                "LOOT_101", "AGPL-3.0",
                ("test_explosive_runes_deals_excess_to_enemy_hero",),
            ),
        ),
        CardRule(
            "END_024", {Hook.SPELL: (ArmSecret(),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_flames_of_infinity_kills_highest_health_minion_at_enemy_end",),
            ),
        ),
        CardRule(
            "CORE_SW_108",
            {Hook.SPELL: (DamageActionTarget(2), AddToHand("SW_108t"), ResolveDeaths())},
            RuleSource(
                "upstream_adapted", rosetta, "SW_108", "AGPL-3.0",
                ("test_first_flame_generates_second_flame",),
            ),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "FIR_909",
            {Hook.SPELL: (DamageRandomEnemyCharacters(2, 3),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_bursting_shot_hits_distinct_random_enemies",),
            ),
        ),
        CardRule(
            "FIR_906",
            {Hook.SPELL: (BuffFriendlyMinionsDiscardRandomSpellSchool(1, 1, "NATURE"),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_overheat_discards_nature_spell_for_second_buff",),
            ),
        ),
        CardRule(
            "FIR_910",
            {Hook.SPELL: (DamageActionTargetDiscardRandomSpellSchool(3, "FIRE"),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_scorching_winds_discards_fire_spell_for_second_hit",),
            ),
            TargetSpec(TargetKind.ANY_CHARACTER),
        ),
        CardRule(
            "FIR_923",
            {Hook.SPELL: (DamageRandomEnemyMinionWithHeldCost(4, 8, 8),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_flames_of_the_firelord_uses_held_cost_threshold",),
            ),
        ),
        CardRule(
            "FIR_954",
            {Hook.SPELL: (DamageActionTargetThenDrawOwner(5),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_conflagrate_damages_and_target_owner_draws",),
            ),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "FIR_941",
            {Hook.SPELL: (DrawMinionThenSummonStatCopy(8, 8),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_searing_reflection_draws_and_summons_divine_shield_copy",),
            ),
        ),
        CardRule(
            "DINO_406",
            {Hook.SPELL: (DamageActionTargetThenBuffFriendlyRace(4, "ELEMENTAL", 1, 1),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_fire_breath_damages_and_buffs_friendly_elementals",),
            ),
            TargetSpec(TargetKind.ANY_CHARACTER),
        ),
        CardRule(
            "END_025",
            {Hook.SPELL: (DamageActionTargetLifestealReturnOnKill(3),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_eternal_firebolt_lifesteals_and_returns_at_end_turn_on_kill",),
            ),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "JAIL_307",
            {Hook.SPELL: (DamageAllMinions(2, repeats=2),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_crowd_control_damages_all_minions_twice",),
            ),
            cost_modifier=CostDiscountIfDeckAtLeast(25, 2),
        ),
        CardRule(
            "JAIL_801",
            {Hook.SPELL: (DamageActionTarget(4), ResolveDeaths())},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_molten_gold_transforms_after_three_spells_and_battlecries",),
            ),
            TargetSpec(TargetKind.ANY_CHARACTER),
        ),
        CardRule(
            "JAIL_801t",
            {Hook.BATTLECRY: (DamageActionTarget(4), ResolveDeaths())},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_molten_gold_transforms_after_three_spells_and_battlecries",),
            ),
            TargetSpec(TargetKind.ANY_CHARACTER),
        ),
        CardRule(
            "TLC_227",
            {Hook.SPELL: (DamageLowestHealthEnemyRepeated(2, 3),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_lava_flow_retargets_lowest_health_enemy",),
            ),
        ),
        CardRule(
            "TLC_221",
            {Hook.SPELL: (DamageActionTargetThenSummonByDamage(3, "TLC_249", 2, 1),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_sizzling_swarm_summons_one_cinder_per_damage",),
            ),
            TargetSpec(TargetKind.ANY_CHARACTER),
        ),
        CardRule(
            "TLC_222",
            {Hook.SPELL: (DrawDifferentTribeMinionsAndBuff(1, 1),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_flight_of_the_firehawk_draws_different_tribes_and_buffs",),
            ),
        ),
        CardRule(
            "TLC_632",
            {Hook.SPELL: (SetHeroPower("TLC_632t"),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_story_of_sulfuras_last_two_uses_then_restores_hero_power",),
            ),
        ),
        CardRule(
            "TLC_632t",
            {Hook.HERO_POWER: (DamageRandomEnemyCharacters(8, 1), SetHeroPower("TLC_632t2"))},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_story_of_sulfuras_last_two_uses_then_restores_hero_power",),
            ),
        ),
        CardRule(
            "TLC_632t2",
            {Hook.HERO_POWER: (DamageRandomEnemyCharacters(8, 1), SetHeroPower(None))},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_story_of_sulfuras_last_two_uses_then_restores_hero_power",),
            ),
        ),
        CardRule(
            "SW_108t",
            {Hook.SPELL: (DamageActionTarget(2), ResolveDeaths())},
            RuleSource(
                "upstream_adapted", rosetta, "SW_108t", "AGPL-3.0",
                ("test_first_flame_generates_second_flame",),
            ),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "CORE_EX1_197",
            {Hook.SPELL: (DestroyMinionsByAttack(5), ResolveDeaths())},
            RuleSource(
                "upstream_adapted", rosetta, "EX1_197", "AGPL-3.0",
                ("test_shadow_word_ruin_uses_current_attack",),
            ),
        ),
        CardRule(
            "CORE_ICC_055",
            {Hook.SPELL: (DamageActionTarget(3), ResolveDeaths())},
            RuleSource(
                "upstream_adapted", rosetta, "ICC_055", "AGPL-3.0",
                ("test_drain_soul_has_lifesteal_and_requires_a_minion",),
            ),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "CORE_SW_072",
            {Hook.BATTLECRY: (DestroyEnemyWeapon(),)},
            RuleSource(
                "upstream_adapted", rosetta, "SW_072", "AGPL-3.0",
                ("test_rustrot_viper_destroys_opposing_weapon",),
            ),
        ),
        CardRule(
            "EX1_014t",
            {Hook.SPELL: (BuffActionTarget(1, 1, event="banana"),)},
            RuleSource(
                "upstream_adapted", rosetta, "EX1_014t", "AGPL-3.0",
                ("test_thalnos_spell_damage_draw_and_mukla_bananas",),
            ),
        ),
        CardRule(
            "JAIL_882", {Hook.DEATHRATTLE: (Draw(),)},
            RuleSource(
                "local_spec", local,
                verification=(
                    "test_steamcleaner_pickpocket_and_ratcatcher_deck_rules",
                ),
            ),
        ),
        CardRule(
            "CORE_SW_068", {Hook.DEATHRATTLE: (GainArmor(8),)},
            RuleSource(
                "upstream_adapted", rosetta, "CORE_SW_068", "AGPL-3.0",
                ("test_eight_cost_demon_rules",),
            ),
        ),
        CardRule(
            "EDR_571",
            {Hook.DEATHRATTLE: (DrawMatching(card_type="SPELL", min_cost=5),)},
            RuleSource(
                "local_spec", local,
                verification=("test_deathrattle_filtered_draws",),
            ),
        ),
        CardRule(
            "EDR_572",
            {Hook.DEATHRATTLE: (DrawMatching(
                count=2, race="DRAGON", cost_delta=-1,
            ),)},
            RuleSource(
                "local_spec", local,
                verification=("test_deathrattle_filtered_draws",),
            ),
        ),
        CardRule(
            "JAIL_007",
            {Hook.DEATHRATTLE: (
                DamageHero(2, "opponent"), DamageBoard(2, "opponent"),
            )},
            RuleSource(
                "local_spec", local,
                verification=("test_six_cost_demon_deathrattles_damage_correct_sides",),
            ),
        ),
        CardRule(
            "JAIL_398",
            {Hook.DEATHRATTLE: (
                DamageHero(3), DamageBoard(3, "controller"),
                DamageHero(3, "opponent"), DamageBoard(3, "opponent"),
            )},
            RuleSource(
                "local_spec", local,
                verification=("test_six_cost_demon_deathrattles_damage_correct_sides",),
            ),
        ),
        CardRule(
            "EDR_459",
            {
                Hook.BATTLECRY: (
                    DamageBoard(3, "controller", exclude_source=True),
                    ResolveDeaths(),
                ),
                Hook.DEATHRATTLE: (DamageBoard(3, "opponent"),),
            },
            RuleSource(
                "local_spec", local,
                verification=("test_death_batch_chillmaw_and_afflicted_devastator",),
            ),
        ),
        CardRule(
            "CORE_LOOT_368",
            {Hook.DEATHRATTLE: (Summon("CORE_CS2_065", 3),)},
            RuleSource(
                "upstream_adapted", rosetta, "CORE_LOOT_368", "AGPL-3.0",
                ("test_voidlord_omen_and_moragg_deathrattles",),
            ),
        ),
        CardRule(
            "TLC_820", {Hook.DEATHRATTLE: (AddToHand("TLC_813"),)},
            RuleSource(
                "local_spec", local,
                verification=(
                    "test_glade_ecologist_generates_and_casts_purifying_vines",
                ),
            ),
        ),
        CardRule(
            "EDR_810", {Hook.BATTLECRY: (Summon("EDR_810t", 2),)},
            RuleSource(
                "local_spec", local,
                verification=(
                    "test_hideous_husk_summons_leeches_that_steal_health",
                ),
            ),
        ),
        CardRule(
            "EDR_260",
            {Hook.DEATHRATTLE: (AddToDeck(
                "EDR_260t", 2, shuffle=True,
                attributes=(("summoned_when_drawn", True),),
            ),)},
            RuleSource(
                "local_spec", local,
                verification=(
                    "test_illusory_greenwing_tokens_summon_when_drawn_and_replace_draw",
                ),
            ),
        ),
        CardRule(
            "JAIL_399",
            {Hook.DEATHRATTLE: (
                AddToDeck("JAIL_399t1", 2, position="bottom"),
            )},
            RuleSource(
                "local_spec", local,
                verification=(
                    "test_imp_gang_stooge_puts_two_grandmother_imps_on_deck_bottom",
                ),
            ),
        ),
        CardRule(
            "EDR_492", {Hook.BATTLECRY: (Summon("EDR_492t", 3),)},
            RuleSource(
                "local_spec", local,
                verification=("test_brood_keeper_and_mother_duck",),
            ),
        ),
        CardRule(
            "TIME_713",
            {Hook.BATTLECRY: (Summon("TIME_713t", side="opponent"),)},
            RuleSource(
                "local_spec", local,
                verification=("test_hooktail_chest_fills_original_players_hand_with_coins",),
            ),
        ),
        CardRule(
            "CORE_DRG_107",
            {Hook.DEATHRATTLE: (AddToHand("CORE_EX1_277"),)},
            RuleSource(
                "upstream_adapted", rosetta, "DRG_107", "AGPL-3.0",
                ("test_violet_spellwing_adds_playable_arcane_missiles",),
            ),
        ),
        CardRule(
            "TLC_600",
            {Hook.BATTLECRY: (DamageActionTarget(5), GainArmor(5))},
            RuleSource(
                "local_spec", local,
                verification=("test_windpeak_wyrm_battlecry_and_coin_spell_rules",),
            ),
        ),
        CardRule(
            "CORE_UNG_084", {Hook.BATTLECRY: (DamageActionTarget(3),)},
            RuleSource(
                "upstream_adapted", rosetta, "CORE_UNG_084", "AGPL-3.0",
                ("test_fire_plume_phoenix_has_explicit_battlecry_target",),
            ),
        ),
        CardRule(
            "CATA_556", {},
            RuleSource(
                "local_spec", local,
                verification=("test_hook_carrier_and_cannonmaster_generation",),
            ),
        ),
        CardRule(
            "CAP_107", {Hook.BATTLECRY: (AddToHand("CAP_107t"),)},
            RuleSource(
                "local_spec", local,
                verification=("test_generated_weapon_passives_and_deathrattle",),
            ),
        ),
        CardRule(
            "CATA_591",
            {Hook.BATTLECRY: (SetPlayerAttributes((("geddon_draw", True),)),)},
            RuleSource(
                "local_spec", local,
                verification=("test_commander_geddon_replaces_turn_draw_with_deck_choice",),
            ),
        ),
        CardRule(
            "CAP_106", {Hook.BATTLECRY: (Summon("CAP_107t", 2),)},
            RuleSource(
                "local_spec", local,
                verification=("test_captain_crowley_summons_cannoneers_and_adds_shots",),
            ),
        ),
        CardRule(
            "CORE_WW_329",
            {Hook.BATTLECRY: (BuffZone(
                "hand", 2, 2, require_attribute="taunt",
            ),)},
            RuleSource(
                "upstream_adapted", rosetta, "CORE_WW_329", "AGPL-3.0",
                ("test_detonation_juggernaut_buffs_taunts_in_hand",),
            ),
        ),
        CardRule(
            "END_004", {Hook.BATTLECRY: (Draw(2),)},
            RuleSource(
                "local_spec", local,
                verification=("test_remnant_costs_less_per_death_this_turn_and_draws_two",),
            ),
        ),
        CardRule(
            "JAIL_457",
            {Hook.BATTLECRY: (BuffZone(
                "board", 1, 1, card_types=("MINION",), exclude_source=True,
            ),)},
            RuleSource(
                "local_spec", local,
                verification=("test_hijacked_securitybot_buffs_other_friendly_minions",),
            ),
        ),
        CardRule(
            "EDR_000", {Hook.BATTLECRY: (GainManaCrystals(3),)},
            RuleSource(
                "local_spec", local,
                verification=("test_ysera_weaponsmith_and_cloud_serpent",),
            ),
        ),
        CardRule(
            "END_021",
            {Hook.BATTLECRY: (BuffZone(
                "hand", attack=2, card_types=("MINION", "WEAPON"),
            ),)},
            RuleSource(
                "local_spec", local,
                verification=("test_ysera_weaponsmith_and_cloud_serpent",),
            ),
        ),
        CardRule(
            "TIME_051",
            {Hook.BATTLECRY: (AddCurrentSourceStats(attack_multiplier=1),)},
            RuleSource(
                "local_spec", local,
                verification=("test_generated_dragon_stat_battlecries",),
            ),
        ),
        CardRule(
            "TIME_720",
            {Hook.BATTLECRY: (AddCurrentSourceStats(health_multiplier=1),)},
            RuleSource(
                "local_spec", local,
                verification=("test_generated_dragon_stat_battlecries",),
            ),
        ),
        CardRule(
            "TIME_024",
            {Hook.BATTLECRY: (SetSourceAttributes((
                ("infinite_attack_next_turn", True),
            )),)},
            RuleSource(
                "local_spec", local,
                verification=("test_murozond_becomes_infinite_at_next_owner_turn",),
            ),
        ),
        CardRule(
            "CORE_EX1_319", {Hook.BATTLECRY: (DamageHero(3),)},
            RuleSource(
                "upstream_adapted", rosetta, "CORE_EX1_319", "AGPL-3.0",
                ("test_basic_demon_battlecries_self_damage_freeze_and_discard",),
            ),
        ),
        CardRule(
            "CORE_LOOT_013", {Hook.BATTLECRY: (DamageHero(2),)},
            RuleSource(
                "upstream_adapted", rosetta, "CORE_LOOT_013", "AGPL-3.0",
                ("test_basic_demon_battlecries_self_damage_freeze_and_discard",),
            ),
        ),
        CardRule(
            "CAP_004", {Hook.DEATHRATTLE: (Draw(2, "opponent"),)},
            RuleSource(
                "local_spec", local,
                verification=("test_one_cost_simple_deathrattles",),
            ),
        ),
        CardRule(
            "EDR_485", {Hook.DEATHRATTLE: (DrawMatching(min_cost=7),)},
            RuleSource(
                "local_spec", local,
                verification=("test_one_cost_simple_deathrattles",),
            ),
        ),
        CardRule(
            "CORE_EX1_014",
            {Hook.BATTLECRY: (AddToHand("EX1_014t", 2, "opponent"),)},
            RuleSource(
                "upstream_adapted", rosetta, "EX1_014", "AGPL-3.0",
                ("test_thalnos_spell_damage_draw_and_mukla_bananas",),
            ),
        ),
        CardRule(
            "CORE_EX1_012", {Hook.DEATHRATTLE: (Draw(),)},
            RuleSource(
                "upstream_adapted", rosetta, "CORE_EX1_012", "AGPL-3.0",
                ("test_thalnos_spell_damage_draw_and_mukla_bananas",),
            ),
        ),
        CardRule(
            "CORE_EX1_110", {Hook.DEATHRATTLE: (Summon("EX1_110t"),)},
            RuleSource(
                "upstream_adapted", rosetta, "CORE_EX1_110", "AGPL-3.0",
                ("test_cairne_taelan_and_tindral_deathrattles",),
            ),
        ),
        CardRule(
            "RLK_708", {Hook.BATTLECRY: (Draw(),), Hook.DEATHRATTLE: (Draw(),)},
            RuleSource(
                "local_spec", local,
                verification=("test_chillfallen_baron_draws_on_battlecry_and_deathrattle",),
            ),
        ),
        CardRule(
            "TLC_225", {Hook.DEATHRATTLE: (Summon("TLC_249"),)},
            RuleSource(
                "local_spec", local,
                verification=("test_cinderfin_deathrattle_and_firegill_kindred",),
            ),
        ),
        CardRule(
            "TIME_015",
            {Hook.BATTLECRY: (
                HealHero(3),
                SetPlayerAttributes((("hero_divine_shield", True),)),
            )},
            RuleSource(
                "local_spec", local,
                verification=("test_hardlight_pmm_clockwork_and_quantum_states",),
            ),
        ),
        CardRule(
            "CATA_615t",
            {Hook.BATTLECRY: (SetPlayerAttributes((
                ("hero_power_cost_override", 1), ("hero_power_armor", 4),
            ), event="genn_hero_power_upgrade"),)},
            RuleSource(
                "local_spec", local,
                verification=(
                    "test_genn_transforms_reversibly_and_upgrades_warrior_hero_power",
                ),
            ),
        ),
        CardRule(
            "CORE_AT_055", {Hook.SPELL: (HealActionTarget(5),)},
            RuleSource(
                "upstream_adapted", rosetta, "AT_055", "AGPL-3.0",
                ("test_simple_core_spell_tranche",),
            ),
            TargetSpec(TargetKind.ANY_CHARACTER),
        ),
        CardRule(
            "CORE_CS2_023", {Hook.SPELL: (Draw(2),)},
            RuleSource(
                "upstream_adapted", rosetta, "CS2_023", "AGPL-3.0",
                ("test_simple_core_spell_tranche",),
            ),
        ),
        CardRule(
            "CORE_CS2_076", {Hook.SPELL: (DestroyActionTarget(),)},
            RuleSource(
                "upstream_adapted", rosetta, "CS2_076", "AGPL-3.0",
                ("test_simple_core_spell_tranche",),
            ),
            TargetSpec(TargetKind.ENEMY_MINION),
        ),
        CardRule(
            "CORE_DS1_185", {Hook.SPELL: (DamageActionTarget(2),)},
            RuleSource(
                "upstream_adapted", rosetta, "DS1_185", "AGPL-3.0",
                ("test_simple_core_spell_tranche",),
            ),
            TargetSpec(TargetKind.ANY_CHARACTER),
        ),
        CardRule(
            "CORE_AT_064", {Hook.SPELL: (DamageActionTarget(3), GainArmor(3))},
            RuleSource(
                "upstream_adapted", rosetta, "AT_064", "AGPL-3.0",
                ("test_second_core_spell_tranche",),
            ),
            TargetSpec(TargetKind.ANY_CHARACTER),
        ),
        CardRule(
            "CORE_CS1_130", {Hook.SPELL: (DamageActionTarget(3),)},
            RuleSource(
                "upstream_adapted", rosetta, "CS1_130", "AGPL-3.0",
                ("test_second_core_spell_tranche",),
            ),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "CORE_CS2_094", {Hook.SPELL: (DamageActionTarget(3), Draw())},
            RuleSource(
                "upstream_adapted", rosetta, "CS2_094", "AGPL-3.0",
                ("test_second_core_spell_tranche",),
            ),
            TargetSpec(TargetKind.ANY_CHARACTER),
        ),
        CardRule(
            "CORE_EX1_391",
            {Hook.SPELL: (DamageActionTargetThenDrawIfSurvives(2),)},
            RuleSource(
                "upstream_adapted", rosetta, "EX1_391", "AGPL-3.0",
                ("test_standard_basic_damage_draw",),
            ),
            TargetSpec(TargetKind.ENEMY_MINION),
        ),
        CardRule(
            "CORE_CS2_072", {Hook.SPELL: (DamageActionTargetIfUndamaged(2),)},
            RuleSource("upstream_adapted", rosetta, "CS2_072", "AGPL-3.0", ("test_standard_conditional_destroy",)),
            TargetSpec(TargetKind.ENEMY_MINION),
        ),
        CardRule(
            "CORE_CS2_009", {Hook.SPELL: (BuffActionTargetWithTaunt(2, 3),)},
            RuleSource("upstream_adapted", rosetta, "CS2_009", "AGPL-3.0", ("test_standard_buff_overload_weapon",)),
            TargetSpec(TargetKind.FRIENDLY_MINION),
        ),
        CardRule(
            "CATA_135", {Hook.SPELL: (SummonAndSpendManaBuff("CATA_135t", 2),)},
            RuleSource("upstream_adapted", rosetta, "CATA_135", "AGPL-3.0", ("test_standard_mossbinding",)),
        ),
        CardRule(
            "CATA_491",
            {Hook.SPELL: (
                DamageBoard(3), ResolveDeaths(),
                DamageBoard(2), ResolveDeaths(),
                DamageBoard(1), ResolveDeaths(),
            )},
            RuleSource("upstream_adapted", rosetta, "CATA_491", "AGPL-3.0", ("test_standard_eldritch_tentacles",)),
        ),
        CardRule(
            "CAP_801", {Hook.SPELL: (BuffActionTargetWithRebornTaunt(2, 3),)},
            RuleSource("upstream_adapted", rosetta, "CAP_801", "AGPL-3.0", ("test_standard_haunt",)),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "CATA_215", {Hook.SPELL: (ReturnActionTargetToOwnerHand(),)},
            RuleSource("upstream_adapted", rosetta, "CATA_215", "AGPL-3.0", ("test_standard_daze_bounce_lock",)),
            TargetSpec(TargetKind.ENEMY_MINION),
        ),
        CardRule(
            "CATA_582", {Hook.SPELL: (DamageBoard(1), GainHeroAttack(3))},
            RuleSource("upstream_adapted", rosetta, "CATA_582", "AGPL-3.0", ("test_standard_searing_fissure",)),
        ),
        CardRule(
            "CATA_585", {Hook.SPELL: (DamageDamagedTargetWithExcessReturn(8),)},
            RuleSource("upstream_adapted", rosetta, "CATA_585", "AGPL-3.0", ("test_standard_torch_excess_return",)),
            TargetSpec(TargetKind.ENEMY_MINION),
        ),
        CardRule(
            "CATA_203", {Hook.SPELL: (DestroyLegendaryTarget(),)},
            RuleSource("upstream_adapted", rosetta, "CATA_203", "AGPL-3.0", ("test_standard_garona_last_stand",)),
            TargetSpec(TargetKind.ENEMY_MINION),
        ),
        CardRule(
            "CATA_554", {Hook.SPELL: (SetEnemyHealthOneWithDragonRepeat(),)},
            RuleSource("upstream_adapted", rosetta, "CATA_554", "AGPL-3.0", ("test_standard_earthen_roar",)),
            TargetSpec(TargetKind.ENEMY_MINION),
        ),
        CardRule(
            "CATA_557", {Hook.SPELL: (SylvanasTriumphDamage(),)},
            RuleSource("upstream_adapted", rosetta, "CATA_557", "AGPL-3.0", ("test_standard_sylvanas_triumph_repeat",)),
        ),
        CardRule(
            "CATA_489", {Hook.SPELL: (DamageHero(4, "opponent"), DamageHero(2, "opponent"), DamageBoard(2, "opponent"))},
            RuleSource("upstream_adapted", rosetta, "CATA_489", "AGPL-3.0", ("test_arcane_flow_shatters_and_merges_at_hand_edges", "test_arcane_flow_halves_and_merged_spell_have_correct_effects")),
        ),
        CardRule(
            "CATA_489t", {Hook.SPELL: (DamageHero(4, "opponent"),)},
            RuleSource("upstream_adapted", rosetta, "CATA_489t", "AGPL-3.0", ("test_arcane_flow_halves_and_merged_spell_have_correct_effects",)),
        ),
        CardRule(
            "CATA_489t2", {Hook.SPELL: (DamageHero(2, "opponent"), DamageBoard(2, "opponent"))},
            RuleSource("upstream_adapted", rosetta, "CATA_489t2", "AGPL-3.0", ("test_arcane_flow_halves_and_merged_spell_have_correct_effects",)),
        ),
        CardRule(
            "CATA_479", {Hook.SPELL: (Summon("CATA_479t3", count=2), BuffFriendlyMinionsAndShield(1))},
            RuleSource("upstream_adapted", rosetta, "CATA_479", "AGPL-3.0", ("test_shatter_flight_maneuvers",)),
        ),
        CardRule(
            "CATA_479t", {Hook.SPELL: (Summon("CATA_479t3", count=2),)},
            RuleSource("upstream_adapted", rosetta, "CATA_479t", "AGPL-3.0", ("test_shatter_flight_maneuvers",)),
        ),
        CardRule(
            "CATA_479t2", {Hook.SPELL: (BuffFriendlyMinionsAndShield(1),)},
            RuleSource("upstream_adapted", rosetta, "CATA_479t2", "AGPL-3.0", ("test_shatter_flight_maneuvers",)),
        ),
        CardRule(
            "CATA_134", {Hook.SPELL: (Summon("CATA_134t3", count=2), GrantDeathrattleSummon("CATA_134t3"))},
            RuleSource("upstream_adapted", rosetta, "CATA_134", "AGPL-3.0", ("test_shatter_wildwood_circle",)),
        ),
        CardRule(
            "CATA_134t", {Hook.SPELL: (Summon("CATA_134t3", count=2),)},
            RuleSource("upstream_adapted", rosetta, "CATA_134t", "AGPL-3.0", ("test_shatter_wildwood_circle",)),
        ),
        CardRule(
            "CATA_134t2", {Hook.SPELL: (GrantDeathrattleSummon("CATA_134t3"),)},
            RuleSource("upstream_adapted", rosetta, "CATA_134t2", "AGPL-3.0", ("test_shatter_wildwood_circle",)),
        ),
        CardRule(
            "CATA_306", {Hook.SPELL: (BuffActionTargetElusive(2, 3), SummonActionTargetCopy())},
            RuleSource("upstream_adapted", rosetta, "CATA_306", "AGPL-3.0", ("test_shatter_schism",)),
            targeting=TargetSpec(TargetKind.FRIENDLY_MINION),
        ),
        CardRule(
            "CATA_306t1", {Hook.SPELL: (BuffActionTargetElusive(2, 3),)},
            RuleSource("upstream_adapted", rosetta, "CATA_306t1", "AGPL-3.0", ("test_shatter_schism",)),
            targeting=TargetSpec(TargetKind.FRIENDLY_MINION),
        ),
        CardRule(
            "CATA_306t2", {Hook.SPELL: (SummonActionTargetCopy(),)},
            RuleSource("upstream_adapted", rosetta, "CATA_306t2", "AGPL-3.0", ("test_shatter_schism",)),
            targeting=TargetSpec(TargetKind.FRIENDLY_MINION),
        ),
        CardRule(
            "CATA_202", {Hook.SPELL: (GenerateRandomCombinedShatter((
                "CATA_134", "CATA_306", "CATA_479", "CATA_489", "CATA_820",
            )),)},
            RuleSource("upstream_adapted", rosetta, "CATA_202", "AGPL-3.0", ("test_stolen_power_combined_shatter",)),
        ),
        CardRule(
            "TIME_101", {Hook.SHATTER: (DamageBoard(2, "opponent"),)},
            RuleSource("upstream_adapted", rosetta, "TIME_101", "AGPL-3.0", ("test_misplaced_pyromancer_shatter_trigger",)),
        ),
        CardRule(
            "CORE_BOT_451", {Hook.SPELL: (Summon("BOT_102t", count=2), Overload(1))},
            RuleSource("upstream_adapted", rosetta, "BOT_451", "AGPL-3.0", ("test_voltaic_burst",)),
        ),
        CardRule(
            "CORE_KAR_077", {Hook.SPELL: (BuffActionTarget(2, 2), SummonRandomExecutableMinion(cost=2))},
            RuleSource("upstream_adapted", rosetta, "KAR_077", "AGPL-3.0", ("test_silvermoon_portal",)),
            targeting=TargetSpec(TargetKind.FRIENDLY_MINION),
        ),
        CardRule(
            "CORE_BAR_541", {Hook.SPELL: (DamageActionTarget(2), OfferSpellDiscover())},
            RuleSource("upstream_adapted", rosetta, "BAR_541", "AGPL-3.0", ("test_runed_orb",)),
            targeting=TargetSpec(TargetKind.ANY_CHARACTER),
        ),
        CardRule(
            "CORE_BT_491", {Hook.SPELL: (Draw(), DrawIfOutcast())},
            RuleSource("upstream_adapted", rosetta, "BT_491", "AGPL-3.0", ("test_spectral_sight_outcast",)),
        ),
        CardRule(
            "CORE_BT_801", {Hook.SPELL: (DamageActionTargetLifesteal(3),)},
            RuleSource("upstream_adapted", rosetta, "BT_801", "AGPL-3.0", ("test_eye_beam_outcast_lifesteal",)),
            targeting=TargetSpec(TargetKind.ENEMY_MINION),
            cost_modifier=CostIfOutcast(1),
        ),
        CardRule(
            "CORE_CATA_009", {Hook.SPELL: (FreezeActionTarget(), OfferSpellDiscover())},
            RuleSource("upstream_adapted", rosetta, "CATA_009", "AGPL-3.0", ("test_deaths_advance",)),
            targeting=TargetSpec(TargetKind.ANY_CHARACTER),
        ),
        CardRule(
            "CORE_EDR_002", {Hook.SPELL: (GrantPoisonousActionTarget(),)},
            RuleSource("upstream_adapted", rosetta, "EDR_002", "AGPL-3.0", ("test_poison_breath",)),
            targeting=TargetSpec(TargetKind.FRIENDLY_UNDEAD),
        ),
        CardRule(
            "YOD_012", {Hook.SPELL: (SummonWithTaunt("CS2_101t", count=2), AddTwinspellCopy("YOD_012ts"))},
            RuleSource("upstream_adapted", rosetta, "YOD_012", "AGPL-3.0", ("test_air_raid",)),
        ),
        CardRule(
            "YOD_012ts", {Hook.SPELL: (SummonWithTaunt("CS2_101t", count=2),)},
            RuleSource("upstream_adapted", rosetta, "YOD_012ts", "AGPL-3.0", ("test_air_raid",)),
        ),
        CardRule(
            "CORE_BAR_311", {Hook.SPELL: (DamageRandomSplitEnemyMinionsLifesteal(4),)},
            RuleSource("upstream_adapted", rosetta, "BAR_311", "AGPL-3.0", ("test_devouring_plague_random_lifesteal",)),
        ),
        CardRule(
            "CORE_EX1_287", {Hook.SPELL: (ArmSecret(),)},
            RuleSource("upstream_adapted", rosetta, "EX1_287", "AGPL-3.0", ("test_counterspell",)),
        ),
        CardRule(
            "CORE_EX1_289", {Hook.SPELL: (ArmSecret(),)},
            RuleSource("upstream_adapted", rosetta, "EX1_289", "AGPL-3.0", ("test_ice_barrier",)),
        ),
        CardRule(
            "CATA_820", {Hook.SPELL: (DrawMatching(count=3, card_type="MINION"), BuffZone("hand", attack=2, health=2, card_types=("MINION",)))},
            RuleSource("upstream_adapted", rosetta, "CATA_820", "AGPL-3.0", ("test_shatter_supply_run",)),
        ),
        CardRule(
            "CATA_820t", {Hook.SPELL: (DrawMatching(count=3, card_type="MINION"),)},
            RuleSource("upstream_adapted", rosetta, "CATA_820t", "AGPL-3.0", ("test_shatter_supply_run",)),
        ),
        CardRule(
            "CATA_820t2", {Hook.SPELL: (BuffZone("hand", attack=2, health=2, card_types=("MINION",)),)},
            RuleSource("upstream_adapted", rosetta, "CATA_820t2", "AGPL-3.0", ("test_shatter_supply_run",)),
        ),
        CardRule(
            "CORE_CS1_112", {Hook.SPELL: (DamageBoard(2), HealFriendlyCharacters(2))},
            RuleSource("upstream_adapted", rosetta, "CS1_112", "AGPL-3.0", ("test_standard_holy_nova_portal",)),
        ),
        CardRule(
            "CORE_WON_337", {Hook.SPELL: (GainArmor(4), SummonRandomExecutableMinion(cost=4))},
            RuleSource("upstream_adapted", rosetta, "WON_337", "AGPL-3.0", ("test_standard_holy_nova_portal",)),
        ),
        CardRule(
            "CORE_BT_072", {Hook.SPELL: (FreezeActionTarget(), Summon("CORE_CS2_033", count=2))},
            RuleSource("upstream_adapted", rosetta, "BT_072", "AGPL-3.0", ("test_standard_deep_freeze",)),
            TargetSpec(TargetKind.ENEMY_CHARACTER),
        ),
        CardRule(
            "CORE_EX1_238", {Hook.SPELL: (DamageActionTarget(3), Overload(1))},
            RuleSource("upstream_adapted", rosetta, "EX1_238", "AGPL-3.0", ("test_standard_buff_overload_weapon",)),
            TargetSpec(TargetKind.ANY_CHARACTER),
        ),
        CardRule(
            "CORE_EX1_145", {Hook.SPELL: (DiscountNextSpell(2),)},
            RuleSource("upstream_adapted", rosetta, "EX1_145", "AGPL-3.0", ("test_standard_preparation_discount",)),
        ),
        CardRule(
            "CORE_CS2_074", {Hook.SPELL: (BuffWeaponAttack(2),)},
            RuleSource("upstream_adapted", rosetta, "CS2_074", "AGPL-3.0", ("test_standard_buff_overload_weapon",)),
        ),
        CardRule(
            "CORE_CS2_108", {Hook.SPELL: (DestroyActionTargetIfDamaged(),)},
            RuleSource("upstream_adapted", rosetta, "CS2_108", "AGPL-3.0", ("test_standard_conditional_destroy",)),
            TargetSpec(TargetKind.ENEMY_MINION),
        ),
        CardRule(
            "CORE_EX1_309", {Hook.SPELL: (DestroyActionTarget(), HealHero(3), ResolveDeaths())},
            RuleSource("upstream_adapted", rosetta, "EX1_309", "AGPL-3.0", ("test_standard_conditional_destroy",)),
            TargetSpec(TargetKind.ENEMY_MINION),
        ),
        CardRule(
            "CORE_EX1_312", {Hook.SPELL: (DestroyAllMinionsAndLocations(),)},
            RuleSource("upstream_adapted", rosetta, "EX1_312", "AGPL-3.0", ("test_standard_conditional_destroy",)),
        ),
        CardRule(
            "CORE_EX1_606", {Hook.SPELL: (GainArmor(5), Draw())},
            RuleSource(
                "upstream_adapted", rosetta, "EX1_606", "AGPL-3.0",
                ("test_standard_basic_damage_draw",),
            ),
        ),
        CardRule(
            "CORE_EX1_619", {Hook.SPELL: (SetAllMinionHealth(1),)},
            RuleSource("upstream_adapted", rosetta, "EX1_619", "AGPL-3.0", ("test_standard_equality_lightning_storm",)),
        ),
        CardRule(
            "CORE_EX1_259", {Hook.SPELL: (DamageBoard(3), Overload(1))},
            RuleSource("upstream_adapted", rosetta, "EX1_259", "AGPL-3.0", ("test_standard_equality_lightning_storm",)),
        ),
        CardRule(
            "CORE_GIL_622",
            {Hook.BATTLECRY: (DamageHero(3, "opponent"), HealHero(3))},
            RuleSource(
                "upstream_adapted", rosetta, "GIL_622", "AGPL-3.0",
                ("test_standard_basic_damage_draw",),
            ),
        ),
        CardRule(
            "CORE_EX1_246", {Hook.SPELL: (TransformActionTarget("hexfrog"),)},
            RuleSource("upstream_adapted", rosetta, "EX1_246", "AGPL-3.0", ("test_standard_hex_transform",)),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "CORE_EX1_160", {Hook.SPELL: (OfferEffectChoice((
                ("buff_friendly_minions", (BuffAllFriendlyMinions(1, 1),)),
                ("summon_panther", (Summon("EX1_160t"),)),
            )),)},
            RuleSource("upstream_adapted", rosetta, "EX1_160", "AGPL-3.0", ("test_standard_power_of_the_wild",)),
        ),
        CardRule(
            "CORE_DS1_184", {Hook.SPELL: (OfferDeckCardDiscover(),)},
            RuleSource("upstream_adapted", rosetta, "DS1_184", "AGPL-3.0", ("test_standard_tracking_discover",)),
        ),
        CardRule(
            "CORE_CS2_075", {Hook.SPELL: (DamageHero(3, "opponent"),)},
            RuleSource("upstream_adapted", rosetta, "CS2_075", "AGPL-3.0", ("test_standard_basic_direct_spells",)),
        ),
        CardRule(
            "CORE_CS2_077", {Hook.SPELL: (Draw(4),)},
            RuleSource("upstream_adapted", rosetta, "CS2_077", "AGPL-3.0", ("test_standard_basic_direct_spells",)),
        ),
        CardRule(
            "CORE_CS2_089", {Hook.SPELL: (HealHero(8),)},
            RuleSource("upstream_adapted", rosetta, "CS2_089", "AGPL-3.0", ("test_standard_basic_direct_spells",)),
        ),
        CardRule(
            "CORE_CS2_013", {Hook.SPELL: (GainManaCrystals(1),)},
            RuleSource("upstream_adapted", rosetta, "CS2_013", "AGPL-3.0", ("test_standard_mana_spells",)),
        ),
        CardRule(
            "CORE_EX1_164",
            {Hook.SPELL: (OfferEffectChoice((
                ("gain_mana_crystals", (GainManaCrystals(2),)),
                ("draw_three", (Draw(3),)),
            )),)},
            RuleSource("upstream_adapted", rosetta, "EX1_164", "AGPL-3.0", ("test_standard_mana_spells",)),
        ),
        CardRule(
            "CORE_EX1_284", {Hook.BATTLECRY: (Draw(),)},
            RuleSource("upstream_adapted", rosetta, "EX1_284", "AGPL-3.0", ("test_standard_azure_drake_draw",)),
        ),
        CardRule(
            "CORE_EX1_129", {Hook.SPELL: (DamageBoard(1), Draw())},
            RuleSource(
                "upstream_adapted", rosetta, "EX1_129", "AGPL-3.0",
                ("test_second_core_spell_tranche",),
            ),
        ),
        CardRule(
            "CORE_EX1_278", {Hook.SPELL: (DamageActionTarget(1), Draw())},
            RuleSource(
                "upstream_adapted", rosetta, "EX1_278", "AGPL-3.0",
                ("test_second_core_spell_tranche",),
            ),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "CORE_TRL_307", {Hook.SPELL: (HealActionTarget(4), Draw())},
            RuleSource(
                "upstream_adapted", rosetta, "TRL_307", "AGPL-3.0",
                ("test_second_core_spell_tranche",),
            ),
            TargetSpec(TargetKind.FRIENDLY_CHARACTER),
        ),
        CardRule(
            "CORE_CS2_093",
            {Hook.SPELL: (DamageHero(2, "opponent"), DamageBoard(2, "opponent"))},
            RuleSource(
                "upstream_adapted", rosetta, "CS2_093", "AGPL-3.0",
                ("test_second_core_spell_tranche",),
            ),
        ),
        CardRule(
            "CORE_BT_035", {Hook.SPELL: (GainHeroAttack(2), Draw())},
            RuleSource(
                "upstream_adapted", rosetta, "BT_035", "AGPL-3.0",
                ("test_a1_draw_and_discard_tranche",),
            ),
        ),
        CardRule(
            "CORE_CFM_604", {Hook.SPELL: (HealActionTarget(12), Draw())},
            RuleSource("upstream_adapted", rosetta, "CFM_604", "AGPL-3.0", ("test_a2_damage_heal_tranche",)),
            TargetSpec(TargetKind.FRIENDLY_CHARACTER),
        ),
        CardRule(
            "CORE_BRM_013", {Hook.SPELL: (DamageActionTargetThenDrawIfHandEmpty(3),)},
            RuleSource("upstream_adapted", rosetta, "BRM_013", "AGPL-3.0", ("test_a2_damage_heal_tranche",)),
            TargetSpec(TargetKind.ANY_CHARACTER),
        ),
        CardRule(
            "CORE_EX1_302", {Hook.SPELL: (DamageActionTargetThenDrawIfKilled(1),)},
            RuleSource("upstream_adapted", rosetta, "EX1_302", "AGPL-3.0", ("test_a2_damage_heal_tranche",)),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "CORE_BT_292", {Hook.SPELL: (BuffActionTarget(2, 1), Draw())},
            RuleSource(
                "upstream_adapted", rosetta, "BT_292", "AGPL-3.0",
                ("test_a1_draw_and_discard_tranche",),
            ),
            TargetSpec(TargetKind.FRIENDLY_MINION),
        ),
        CardRule(
            "CORE_CS2_053", {Hook.SPELL: (DrawMatching(cost_delta=-3),)},
            RuleSource(
                "upstream_adapted", rosetta, "CS2_053", "AGPL-3.0",
                ("test_a1_draw_and_discard_tranche",),
            ),
        ),
        CardRule(
            "CORE_EX1_096", {Hook.DEATHRATTLE: (Draw(),)},
            RuleSource(
                "upstream_adapted", rosetta, "EX1_096", "AGPL-3.0",
                ("test_a1_draw_and_discard_tranche",),
            ),
        ),
        CardRule(
            "RLK_511", {Hook.DEATHRATTLE: (DrawMatching(card_type="SPELL", spell_school="FROST"),)},
            RuleSource("upstream_adapted", rosetta, "RLK_511", "AGPL-3.0", ("test_a1_undead_and_frost_draw_tranche",)),
        ),
        CardRule(
            "RLK_709", {Hook.SPELL: (DamageAllEnemies(2), Draw())},
            RuleSource("upstream_adapted", rosetta, "RLK_709", "AGPL-3.0", ("test_a1_undead_and_frost_draw_tranche",)),
        ),
        CardRule(
            "EDR_843a", {Hook.SPELL: (DrawMatching(card_type="SPELL"),)},
            RuleSource("upstream_adapted", rosetta, "EDR_843a", "AGPL-3.0", ("test_type_draw_tranche",)),
        ),
        CardRule(
            "EDR_843b", {Hook.SPELL: (DrawMatching(card_type="MINION"),)},
            RuleSource("upstream_adapted", rosetta, "EDR_843b", "AGPL-3.0", ("test_type_draw_tranche",)),
        ),
        CardRule(
            "EDR_843t1", {Hook.SPELL: (DrawMatching(card_type="SPELL"), DrawMatching(card_type="MINION"))},
            RuleSource("upstream_adapted", rosetta, "EDR_843t1", "AGPL-3.0", ("test_type_draw_tranche",)),
        ),
        CardRule(
            "CAP_405t4", {Hook.SPELL: (Draw(3),)},
            RuleSource("upstream_adapted", rosetta, "CAP_405t4", "AGPL-3.0", ("test_type_draw_tranche",)),
        ),
        CardRule(
            "EDR_817", {Hook.SPELL: (Draw(2), Summon("EDR_810t", count=2))},
            RuleSource("upstream_adapted", rosetta, "EDR_817", "AGPL-3.0", ("test_draw_summon_tranche",)),
        ),
        CardRule(
            "CAP_102", {Hook.SPELL: (Draw(2), Summon("CAP_107t", count=2))},
            RuleSource("upstream_adapted", rosetta, "CAP_102", "AGPL-3.0", ("test_draw_summon_tranche",)),
        ),
        CardRule(
            "TIME_023", {Hook.SPELL: (DrawBottom(2),)},
            RuleSource("upstream_adapted", rosetta, "TIME_023", "AGPL-3.0", ("test_bottom_and_origin_draw_tranche",)),
        ),
        CardRule(
            "EDR_251", {Hook.SPELL: (
                DrawMatching(card_type="SPELL", started_in_deck=True),
                DrawMatching(card_type="SPELL", started_in_deck=False),
            )},
            RuleSource("upstream_adapted", rosetta, "EDR_251", "AGPL-3.0", ("test_bottom_and_origin_draw_tranche",)),
        ),
        CardRule(
            "EDR_416",
            {Hook.AFTER_HERO_ATTACK: (SummonDormant("EDR_416t", 2),)},
            RuleSource(
                "powerlog_verified", local, "EDR_416", "internal",
                ("test_powerlog_cards_and_triggers",),
            ),
        ),
        CardRule(
            "JAIL_377", {Hook.SPELL: (DrawThenDrawIfCostAtMost(2),)},
            RuleSource("upstream_adapted", rosetta, "JAIL_377", "AGPL-3.0", ("test_conditional_draw_tranche",)),
        ),
        CardRule(
            "EDR_231", {Hook.SPELL: (HealActionTarget(4), Draw(), OfferImbueHeroPowerOptions())},
            RuleSource("upstream_adapted", rosetta, "EDR_231", "AGPL-3.0", ("test_conditional_draw_tranche",)),
            TargetSpec(TargetKind.FRIENDLY_CHARACTER),
        ),
        CardRule(
            "JAIL_866", {Hook.SPELL: (DrawMinionsAndBuffIfMana(2, 10, 3, 3),)},
            RuleSource("upstream_adapted", rosetta, "JAIL_866", "AGPL-3.0", ("test_conditional_draw_tranche",)),
        ),
        CardRule(
            "CORE_CATA_007", {Hook.SPELL: (DamageRandomEnemyMinionsThenDrawPerKill(3, 2),)},
            RuleSource("upstream_adapted", rosetta, "CATA_007", "AGPL-3.0", ("test_conditional_draw_tranche",)),
        ),
        CardRule(
            "CATA_526", {Hook.SPELL: (DamageAllMinionsThenDrawPerDeath(1),)},
            RuleSource("upstream_adapted", rosetta, "CATA_526", "AGPL-3.0", ("test_batch_draw_damage_and_choose_one_cards",)),
        ),
        CardRule(
            "CATA_485", {Hook.SPELL: (DamageHero(2, "opponent"), DamageRandomEnemyMinion(1))},
            RuleSource("upstream_adapted", rosetta, "CATA_485", "AGPL-3.0", ("test_sleet_storm_fixed_and_random_damage",)),
        ),
        CardRule(
            "CORE_EX1_154", {Hook.SPELL: (OfferEffectChoice((
                ("damage_3", (DamageActionTarget(3),)),
                ("damage_1_draw", (DamageActionTarget(1), Draw())),
            )),)},
            RuleSource("upstream_adapted", rosetta, "EX1_154", "AGPL-3.0", ("test_batch_draw_damage_and_choose_one_cards",)),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "TLC_231", {Hook.SPELL: (DrawMinionThenBuffIfAttack(5, 5, 5),)},
            RuleSource("upstream_adapted", rosetta, "TLC_231", "AGPL-3.0", ("test_batch_conditional_and_costed_draw_cards",)),
        ),
        CardRule(
            "TLC_236", {Hook.SPELL: (DrawMinionsByCosts((1, 2, 3, 4)),)},
            RuleSource("upstream_adapted", rosetta, "TLC_236", "AGPL-3.0", ("test_batch_conditional_and_costed_draw_cards",)),
        ),
        CardRule(
            "EDR_226", {Hook.BATTLECRY: (DrawMatching(race="BEAST"), OfferImbueHeroPowerOptions())},
            RuleSource("upstream_adapted", rosetta, "EDR_226", "AGPL-3.0", ("test_batch_conditional_and_costed_draw_cards",)),
        ),
        CardRule(
            "CATA_302", {Hook.SPELL: (HealActionTargetToFull(), Draw())},
            RuleSource(
                "powerlog_verified", local, "CATA_302", "internal",
                ("test_latest_powerlog_simple_rules",),
            ),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "CATA_308", {Hook.SPELL: (DamageAllMinions(4), ResolveDeaths())},
            RuleSource(
                "powerlog_verified", local, "CATA_308", "internal",
                ("test_latest_powerlog_simple_rules",),
            ),
        ),
        CardRule(
            "JAIL_441", {Hook.SPELL: (DamageActionTarget(3), RefreshHeroPower())},
            RuleSource("upstream_adapted", rosetta, "JAIL_441", "AGPL-3.0", ("test_drink_blood_lifesteal_refresh",)),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "JAIL_891", {Hook.SPELL: (DamageActionTargetThenAddToHandIfKilled(3, "JAIL_732"),)},
            RuleSource("upstream_adapted", rosetta, "JAIL_891", "AGPL-3.0", ("test_void_blast_generates_void_soul",)),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "TLC_235", {Hook.SPELL: (DestroyActionTargetReplaceSameCost(),)},
            RuleSource("upstream_adapted", rosetta, "TLC_235", "AGPL-3.0", ("test_life_cycle_replaces_same_cost",)),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "RLK_025", {Hook.SPELL: (DamageActionTargetThenOfferRuneIfKilled(3, "frost"),)},
            RuleSource("upstream_adapted", rosetta, "RLK_025", "AGPL-3.0", ("test_frost_strike_rune_discover",)),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "TIME_218", {Hook.SPELL: (DamageActionTarget(1), GainHeroAttack(1))},
            RuleSource("upstream_adapted", rosetta, "TIME_218", "AGPL-3.0", ("test_static_shock_damage_attack",)),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "CORE_BOT_222", {Hook.SPELL: (DamageActionTarget(4), DamageHero(4))},
            RuleSource("upstream_adapted", rosetta, "BOT_222", "AGPL-3.0", ("test_spirit_bomb_self_damage",)),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "TLC_823", {Hook.SPELL: (DamageActionTarget(3), DiscountNextBeast(2))},
            RuleSource("upstream_adapted", rosetta, "TLC_823", "AGPL-3.0", ("test_cower_in_fear_beast_discount",)),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "MEND_043", {Hook.SPELL: (DrawAndArmorRepeatIfNoMinionLastTurn(3),)},
            RuleSource("upstream_adapted", rosetta, "MEND_043", "AGPL-3.0", ("test_heartroot_stones_repeat",)),
        ),
        CardRule(
            "RLK_024", {Hook.SPELL: (DamageActionTarget(6),)},
            RuleSource("upstream_adapted", rosetta, "RLK_024", "AGPL-3.0", ("test_batch_direct_damage_rules",)),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "CATA_156", {Hook.SPELL: (DamageAllEnemies(4),)},
            RuleSource("upstream_adapted", rosetta, "CATA_156", "AGPL-3.0", ("test_batch_direct_damage_rules",)),
        ),
        CardRule(
            "JAIL_COIN1", {Hook.SPELL: (GainMana(1),)},
            RuleSource(
                "powerlog_verified", local, "JAIL_COIN1", "internal",
                ("test_latest_powerlog_simple_rules",),
            ),
        ),
        CardRule(
            "TIME_770", {Hook.SPELL: (DrawTwoThenChooseDiscount(2),)},
            RuleSource("upstream_adapted", rosetta, "TIME_770", "AGPL-3.0", ("test_fast_forward_draw_choose_discount",)),
        ),
        CardRule(
            "JAIL_206", {Hook.SPELL: (DrawThreeThenGiveOne(),)},
            RuleSource("upstream_adapted", rosetta, "JAIL_206", "AGPL-3.0", ("test_dark_bribe_draw_give",)),
        ),
        CardRule(
            "CORE_AT_037", {Hook.SPELL: (OfferEffectChoice((
                ("damage_2", (DamageActionTarget(2),)),
                ("summon_saplings", (Summon("TTN_950t", count=2),)),
            )),)},
            RuleSource("upstream_adapted", rosetta, "AT_037", "AGPL-3.0", ("test_living_roots_choose_one",)),
            TargetSpec(TargetKind.ANY_CHARACTER, optional=True),
        ),
        CardRule(
            "CORE_CS2_024", {Hook.SPELL: (DamageActionTarget(3), FreezeActionTarget())},
            RuleSource("upstream_adapted", rosetta, "CS2_024", "AGPL-3.0", ("test_frostbolt_and_blizzard_freeze_targets",)),
            TargetSpec(TargetKind.ANY_CHARACTER),
        ),
        CardRule(
            "CORE_CS2_028", {Hook.SPELL: (DamageBoard(2), FreezeAllEnemyMinions())},
            RuleSource("upstream_adapted", rosetta, "CS2_028", "AGPL-3.0", ("test_frostbolt_and_blizzard_freeze_targets",)),
        ),
        CardRule(
            "CORE_RLK_063", {Hook.SPELL: (
                DamageActionTarget(5), FreezeAllEnemyMinions(), Summon("RLK_063t"),
            )},
            RuleSource("upstream_adapted", rosetta, "RLK_063", "AGPL-3.0", ("test_frostwyrms_fury_damage_freeze_summon",)),
            TargetSpec(TargetKind.ANY_CHARACTER),
        ),
        CardRule(
            "CORE_BAR_801", {Hook.SPELL: (DamageActionTarget(1), Summon("BAR_035t"))},
            RuleSource("upstream_adapted", rosetta, "BAR_801", "AGPL-3.0", ("test_wound_prey_damage_summon",)),
            TargetSpec(TargetKind.ANY_CHARACTER),
        ),
        CardRule(
            "EDR_814", {Hook.SPELL: (DamageActionTarget(2), Summon("EDR_810t"))},
            RuleSource("upstream_adapted", rosetta, "EDR_814", "AGPL-3.0", ("test_infested_breath_damage_summon",)),
            TargetSpec(TargetKind.ANY_CHARACTER),
        ),
        CardRule(
            "EDR_463",
            {Hook.SPELL: (OfferEffectChoice((
                ("destroy_low_attack", (DestroyActionTargetIfAttackAtMost(3),)),
                ("summon_random_two_cost", (SummonRandomExecutableMinion(cost=2),)),
            )),)},
            RuleSource(
                "powerlog_verified", local, "EDR_463", "internal",
                ("test_latest_powerlog_choice_rules",),
            ),
            # The current action encoding has one target slot for the whole
            # Choose One card.  Requiring a minion target keeps the destroy
            # branch legal; the summon branch simply ignores that target.
            TargetSpec(TargetKind.ANY_MINION),
        ),
    ))

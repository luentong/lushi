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


# Shared Leyline model.  Keeping the pool and progression helpers here makes
# every Leyline rule use the same state contract and prevents drift between
# individual card implementations.
LEYLINE_CARD_IDS = frozenset(("MEND_500", "MEND_502", "MEND_504"))


def _leyline_upgrade(player: Any) -> int:
    return max(0, int(getattr(player, "leyline_upgrade", 0)))


def _leyline_repeats(player: Any) -> int:
    return 1 + max(0, int(getattr(player, "leyline_extra_triggers", 0)))


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
    "CORE_EX1_189",  # Brightwing
    "CORE_GVG_114",  # Sneed's Old Shredder
    "TIME_609",  # Ranger General Sylvanas (Fabled)
    "TIME_609t1", "TIME_609t2",
    "TIME_850",  # Lo'Gosh, Blood Fighter (Fabled)
    "TIME_850t", "TIME_850t1",
    "TIME_852", "TIME_852t1",
    "TIME_852t3",
    "TIME_209",  # Muradin, High King (Fabled)
    "TIME_209t", "TIME_209t2",
    "TIME_875",  # Garona Halforcen (Fabled)
    "TIME_875t1", "TIME_009",  # Gelbin of Tomorrow (Fabled)
    "TIME_009t1", "TIME_009t2",
    "TIME_211",  # Lady Azshara (Fabled)
    "TIME_211a", "TIME_211b", "TIME_211t1", "TIME_211t1t",
    "TIME_211t2", "TIME_211t2t",
    "TIME_619", "TIME_619t2", "TIME_619t3", "TIME_619t4", "TIME_619t5",
    "TIME_619t",
    "TIME_020t1", "TIME_020t2", "TIME_020t3", "TIME_020t4", "TIME_020t5",
    "TIME_020t2t", "TIME_020t3t", "TIME_020t4t", "TIME_020t5t",
    "TIME_005",  # Timethief Rafaam (Fabled+)
    "TIME_005t1", "TIME_005t2", "TIME_005t3", "TIME_005t4", "TIME_005t5",
    "TIME_005t6", "TIME_005t7", "TIME_005t8", "TIME_005t9",
    "TIME_006t1", "TIME_870t", "TIME_873t",
    "TIME_713t",
    "TLC_366", "TLC_903",
    "TLC_440",
    "TLC_447",
    "TLC_226",
    "TLC_428",  # Hot Spring Glider (Kindred)
    "TLC_429", "TLC_429t",  # Steamfin Thief
    "TLC_519", "TLC_519t",  # Ambush Predators
    "TLC_815", "TLC_816",  # Gravedawn spells
    "TLC_454",  # Scalehide Kodo
    "TLC_463", "TLC_482", "TLC_825", "TLC_829",
    "TLC_251", "TLC_251e",
    "TLC_107", "END_015",
    "DINO_435",
    "DINO_138", "DINO_404", "DINO_413",
    "TLC_102", "TLC_223", "TLC_243", "TLC_432", "TLC_600",
    "CORE_GIL_836",
    "JAIL_460",
    "TLC_435", "TLC_442", "TLC_464", "TLC_515", "TLC_824", "TLC_900",
    # Classic League of Explorers map chain.
    "CORE_LOE_079", "LOE_019t", "LOE_019t2",
    "DINO_419", "DINO_421",
    # The Lost City of Un'Goro class Legendary Quests.
    "TLC_229", "TLC_239", "TLC_426", "TLC_433", "TLC_446",
    "TLC_460", "TLC_513", "TLC_602", "TLC_631", "TLC_817", "TLC_830",
    "TLC_229t14", "TLC_239t", "TLC_446t", "TLC_513t", "TLC_602t",
    "TLC_426t", "TLC_433t", "TLC_433t2", "TLC_460t", "TLC_631t",
    "TLC_817t3", "TLC_817t4", "TLC_817t5", "TLC_830t",
    "UNG_028t", "UNG_067t1", "UNG_116t", "UNG_829t1", "UNG_920t1",
    "UNG_934t1", "UNG_940t8", "UNG_942t", "UNG_954t1",
    "UNG_999t2t1",
    "TIME_005t1", "TIME_005t2", "TIME_005t4", "TIME_005t5", "TIME_005t6",
    "TIME_005t3", "TIME_005t7", "TIME_005t8",
    "CS2_tk1",
    "END_037",  # Endtime Murozond
    "CORE_EX1_096",  # Loot Hoarder
    "CORE_CFM_604",  # Greater Healing Potion
    "CORE_BRM_013",  # Quick Shot
    "CORE_SW_442",  # Void Shard
    "CORE_SCH_512",  # Initiation
    "CORE_LOOT_373",  # Healing Rain
    "TLC_439",  # Wave of Tar
    "CORE_EX1_302",  # Mortal Coil
    "CORE_EX1_007",  # Acolyte of Pain
    "CORE_RLK_121",  # Acolyte of Death
    "RLK_511",  # Harbinger of Winter
    "RLK_709",  # Remorseless Winter
    "EDR_843a", "EDR_843b", "EDR_843t1", "CAP_405t4",
    "EDR_817", "CAP_102", "EDR_860", "FIR_921", "EDR_227", "EDR_264", "EDR_451", "EDR_518", "EDR_519", "EDR_800", "EDR_871", "EDR_845", "EDR_888", "EDR_102", "EDR_811", "FIR_900", "EDR_488", "EDR_882", "FIR_920", "END_027", "FIR_901", "EDR_487", "EDR_654", "FIR_922", "EDR_528", "CORE_EDR_004", "CORE_EDR_004_2026", "EDR_456", "EDR_856", "FIR_924", "FIR_939", "FIR_956", "EDR_226", "EDR_231", "EDR_500", "END_000", "END_001", "END_003", "END_003p", "CORE_AT_003", "EDR_847p", "EDR_847pt2", "EDR_850p", "EDR_851p", "EDR_448p", "END_000p", "EDR_445p", "EDR_445pt3",
    "TIME_023", "EDR_251", "JAIL_377", "EDR_231", "JAIL_866", "CORE_CATA_007",
    "CORE_EX1_154", "CATA_526", "TLC_231", "TLC_236", "EDR_226",
    "RLK_024", "CATA_156",
    "CORE_AT_037",
    "CORE_CS2_024", "CORE_CS2_028", "CORE_RLK_063",
    "CORE_BAR_801",
    "CORE_EX1_391", "CORE_EX1_606", "CORE_GIL_622",
    "CORE_CS2_072", "CORE_CS2_108", "CORE_EX1_309", "CORE_EX1_312",
    "CORE_CS2_009", "CORE_EX1_238", "CORE_CS2_074", "CORE_RLK_567", "TIME_039", "JAIL_720", "TLC_515", "TLC_816", "CORE_YOP_001", "DINO_417", "JAIL_998", "DINO_411", "CATA_201", "TLC_902", "TLC_630t", "TLC_903t", "TLC_522", "CATA_785", "EDR_840", "CATA_158", "EDR_523", "CAP_001", "CAP_003", "CAP_000", "CAP_005", "CAP_002", "TIME_875t", "CORE_ULD_133", "MEND_504", "EDR_804", "GIL_553", "OG_195", "MEND_500", "LOOT_537", "MEND_501", "MEND_502", "EDR_940",
    "CORE_CS1_112", "CORE_WON_337", "EDR_871",
    "CORE_BT_072", "MEND_503", "MEND_506",
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


@dataclass(frozen=True)
class CostIfKindred:
    amount: int

    def adjustment(self, game: Any, player: Any, card: Any) -> int:
        races = set(card.definition.races)
        active = bool(races & player.played_races_last_turn) if races and "ALL" not in races else bool(
            player.played_races_last_turn
        )
        return -self.amount if active else 0


@dataclass(frozen=True)
class RafaamCostDiscount:
    """Dynamic discount for Giant Rafaam or the next Rafaam effect."""
    mode: str

    def adjustment(self, game: Any, player: Any, card: Any) -> int:
        if self.mode == "giant":
            count = sum(v for k, v in player.played_card_counts.items() if "TIME_005" in k)
            return -min(card.cost, count)
        if self.mode == "next":
            if getattr(player, "rafaam_next_discount", False) and "rafaam" in card.definition.name.casefold():
                return -min(card.cost, 3)
        return 0


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
class BuffRandomBeastInHand:
    """Give a random Beast in hand +1 Attack and reduce its cost by 1."""

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [card for card in context.player.hand if card.has_race("BEAST")]
        if not candidates:
            return
        card = game.rng.choice(candidates)
        card.attack_delta += 1
        card.cost_delta -= 1
        game._event("imbue_beast_buff", player=context.player.index,
                    source=context.card.card_id, target=card.entity_id,
                    attack=1, cost_reduction=1)


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
    scale_with_leyline: bool = False

    def execute(self, game: Any, context: RuleContext) -> None:
        repeats = _leyline_repeats(context.player) if self.scale_with_leyline else 1
        amount = self.amount + (_leyline_upgrade(context.player) if self.scale_with_leyline else 0)
        for _ in range(repeats):
            before = set(card.entity_id for card in context.player.hand)
            game._draw(context.player)
            drawn = [card for card in context.player.hand if card.entity_id not in before]
            if drawn:
                drawn[-1].cost_delta -= amount


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
    scale_with_leyline: bool = False

    def execute(self, game: Any, context: RuleContext) -> None:
        repeats = _leyline_repeats(context.player) if self.scale_with_leyline else 1
        for _ in range(repeats):
            enemy = game.players[1 - context.player.index]
            targets = [m for m in enemy.board if m.health > 0 and m.dormant_turns == 0]
            if not targets:
                return
            target = game.rng.choice(targets)
            before = max(0, target.health)
            base = self.amount + (_leyline_upgrade(context.player) if self.scale_with_leyline else 0)
            amount = game._spell_effect_amount(context.player, context.card, base)
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
class DiscountHeldLeylines:
    amount: int = 1

    def execute(self, game: Any, context: RuleContext) -> None:
        affected = []
        for card in context.player.hand:
            if card.card_id in LEYLINE_CARD_IDS:
                card.cost_delta -= self.amount
                affected.append(card.entity_id)
        game._event("ley_walker_discount", player=context.player.index,
                    source=context.card.card_id, amount=self.amount,
                    affected=affected)


@dataclass(frozen=True)
class AddRandomLeyline:
    def execute(self, game: Any, context: RuleContext) -> None:
        card_id = game.rng.choice(sorted(LEYLINE_CARD_IDS))
        card = game._entity(card_id, created_by=context.card.card_id)
        destination = game._add_generated(context.player, card)
        game._event("random_leyline_generated", player=context.player.index,
                    source=context.card.card_id, card=card_id,
                    destination=destination)


@dataclass(frozen=True)
class UpgradeLeylines:
    amount: int = 1

    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.leyline_upgrade = _leyline_upgrade(context.player) + max(0, self.amount)
        game._event("leyline_upgrade", player=context.player.index,
                    source=context.card.card_id, amount=self.amount,
                    level=_leyline_upgrade(context.player))


@dataclass(frozen=True)
class AddLeylineExtraTrigger:
    amount: int = 1

    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.leyline_extra_triggers = max(
            0, int(getattr(context.player, "leyline_extra_triggers", 0))
        ) + max(0, self.amount)
        game._event("leyline_extra_trigger", player=context.player.index,
                    source=context.card.card_id, amount=self.amount,
                    total=context.player.leyline_extra_triggers)


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
class TransformFriendlyMinionRandom:
    """Transform a random friendly minion into a random cheaper minion."""

    def execute(self, game: Any, context: RuleContext) -> None:
        if not context.player.board:
            return
        target = game.rng.choice(context.player.board)
        requested_cost = self.cost + int(getattr(context.card, "boon_summon_cost_bonus", 0))
        candidates = [
            card_id for card_id in game.executable_card_ids
            if card_id in game.card_defs
            and game.card_defs[card_id].card_type == "MINION"
            and game.card_defs[card_id].cost <= max(0, target.cost - 1)
        ]
        if not candidates:
            return
        replacement = game._entity(game.rng.choice(sorted(candidates)), created_by=context.card.card_id)
        replacement.entity_id = target.entity_id
        context.player.board[context.player.board.index(target)] = replacement
        game._event("imbue_transform", player=context.player.index,
                    source=context.card.card_id, target=target.entity_id,
                    replacement=replacement.card_id)


@dataclass(frozen=True)
class GainArmorPerWisp:
    base: int = 1

    def execute(self, game: Any, context: RuleContext) -> None:
        wisps = sum(card.definition.name.casefold() == "wisp" for card in context.player.board)
        GainArmor(self.base + wisps).execute(game, context)


@dataclass(frozen=True)
class SummonRandomLeylineMinion:
    def execute(self, game: Any, context: RuleContext) -> None:
        for _ in range(_leyline_repeats(context.player)):
            game._summon_random_executable_minion(
                context.player, source_card_id=context.card.card_id,
                cost=max(0, 5 + _leyline_upgrade(context.player)),
            )


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
    map_followup: bool = False

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
        if self.map_followup and game.pending_choice is not None:
            game.pending_choice["map_followup"] = True
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
class OfferLegendaryWildGodDiscover:
    """Discover from the executable Legendary minion Wild God proxy pool."""

    def execute(self, game: Any, context: RuleContext) -> None:
        game._offer_legendary_wild_god_discover(
            context.player, source_card_id=context.card.card_id,
            discount_if_imbued=context.player.hero_power_imbues >= 4,
        )


@dataclass(frozen=True)
class OfferMinionDarkGiftDiscover:
    rarity: str | None = None
    race: str | None = None
    mechanic: str | None = None
    mechanics: tuple[str, ...] = ()
    min_cost: int | None = None
    cost_delta: int = 0
    spend_corpses: int = 0

    def execute(self, game: Any, context: RuleContext) -> None:
        if self.spend_corpses:
            if context.player.corpses < self.spend_corpses:
                return
            context.player.corpses -= self.spend_corpses
        pool = [
            card_id for card_id, definition in game.card_defs.items()
            if card_id in game.executable_card_ids
            and definition.card_type == "MINION"
            and (self.rarity is None or definition.rarity == self.rarity)
            and (self.race is None or self.race in definition.races)
            and (
                self.mechanic is None
                or self.mechanic in definition.mechanics
                or self.mechanic.casefold() in definition.text.casefold()
            )
            and (
                not self.mechanics
                or any(
                    m in definition.mechanics
                    or m.casefold() in definition.text.casefold()
                    for m in self.mechanics
                )
            )
            and (self.min_cost is None or definition.cost >= self.min_cost)
        ]
        game._offer_discover(
            context.player, pool, dark_gift=True,
            source_card_id=context.card.card_id,
        )
        if game.pending_choice is not None:
            game.pending_choice["dark_gift_cost_delta"] = self.cost_delta


@dataclass(frozen=True)
class OfferRaptorHeraldDiscover:
    """Raptor Herald's Beast Dark Gift discover with Kindred discount."""

    def execute(self, game: Any, context: RuleContext) -> None:
        OfferMinionDarkGiftDiscover(race="BEAST").execute(game, context)
        if game.pending_choice is not None and game._kindred_repeats(context.player, context.card):
            game.pending_choice["dark_gift_cost_delta"] = -1


@dataclass(frozen=True)
class OfferBattlecryMinionDiscover:
    """Discover an executable minion with a printed Battlecry."""

    def execute(self, game: Any, context: RuleContext) -> None:
        pool = [
            card_id for card_id, definition in game.card_defs.items()
            if card_id in game.executable_card_ids
            and definition.card_type == "MINION"
            and "BATTLECRY" in definition.mechanics
        ]
        game._offer_discover(context.player, pool, dark_gift=False, source_card_id=context.card.card_id)
        if game.pending_choice is not None:
            for option in game.pending_choice["options"]:
                option.cost_delta -= 1


@dataclass(frozen=True)
class AddRandomWeapon:
    """Add one random executable Standard weapon to the controller's hand."""

    def execute(self, game: Any, context: RuleContext) -> None:
        pool = [
            card_id for card_id, definition in game.card_defs.items()
            if card_id in game.executable_card_ids
            and definition.card_type == "WEAPON"
        ]
        if not pool:
            return
        card = game._entity(game.rng.choice(sorted(pool)), created_by=context.card.card_id)
        destination = game._add_generated(context.player, card)
        game._event("random_weapon_added", player=context.player.index,
                    source=context.card.card_id, card=card.card_id,
                    destination=destination)


@dataclass(frozen=True)
class MapDiscover:
    """Shared Discover implementation for the current Map card family."""

    race: str | None = None
    spell_school: str | None = None
    rune: str | None = None
    odd_attack_beast: bool = False
    unplayed_race: bool = False

    def execute(self, game: Any, context: RuleContext) -> None:
        played = set(context.player.played_races_this_game)
        pool = []
        for card_id, definition in game.card_defs.items():
            if card_id not in game.executable_card_ids:
                continue
            if self.spell_school is not None:
                if definition.card_type != "SPELL" or definition.spell_school != self.spell_school:
                    continue
            elif definition.card_type != "MINION":
                continue
            if self.race is not None and self.race not in definition.races:
                continue
            if self.rune is not None and getattr(definition, "rune_cost", {}).get(self.rune, 0) <= 0:
                continue
            if self.odd_attack_beast and ("BEAST" not in definition.races or definition.attack % 2 != 1):
                continue
            if self.unplayed_race and set(definition.races) & played:
                continue
            pool.append(card_id)
        game._offer_discover(context.player, pool, dark_gift=False, source_card_id=context.card.card_id)
        if game.pending_choice is not None:
            game.pending_choice["map_followup"] = True


@dataclass(frozen=True)
class OfferOpponentDeckMinionDiscover:
    def execute(self, game: Any, context: RuleContext) -> None:
        game._offer_opponent_deck_minion_discover(
            context.player, source_card_id=context.card.card_id,
            dark_gift=context.card.combo_active,
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
class AddRandomClassMinion:
    """Add a random executable minion from another class, discounted by 1."""

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [
            card_id for card_id in game.executable_card_ids
            if card_id in game.card_defs
            and game.card_defs[card_id].card_type == "MINION"
            and game.card_defs[card_id].card_class not in {context.player.card_class, "NEUTRAL"}
        ]
        if not candidates:
            return
        card = game._entity(game.rng.choice(sorted(candidates)), created_by=context.card.card_id)
        card.cost_delta -= 1
        destination = game._add_generated(context.player, card)
        game._event("imbue_rewind_minion", player=context.player.index,
                    source=context.card.card_id, card=card.card_id,
                    entity=card.entity_id, destination=destination)


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
class DamageAllEnemyCharacters:
    """Deal fixed damage to the opposing hero and all awake minions."""

    amount: int
    repeat_for_cards: tuple[str, ...] = ()

    def execute(self, game: Any, context: RuleContext) -> None:
        amount = game._spell_effect_amount(context.player, context.card, self.amount)
        repeats = 1 + sum(
            context.player.played_card_counts.get(card_id, 0)
            for card_id in self.repeat_for_cards
        )
        targets = game._random_enemy_characters(context.player.index)
        for _ in range(repeats):
            for target in targets:
                game._deal_to_target(context.player.index, target, amount, context.card)
            game._resolve_deaths()
        game._event(
            "all_enemy_damage", player=context.player.index,
            source=context.card.card_id, amount=amount, repeats=repeats,
            targets=targets,
        )


@dataclass(frozen=True)
class DamageRandomSplitEnemyCharacters:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        targets = game._random_enemy_characters(context.player.index)
        if not targets:
            return
        amount = game._spell_effect_amount(context.player, context.card, self.amount)
        hits = [game.rng.choice(targets) for _ in range(amount)]
        for target in hits:
            game._deal_to_target(context.player.index, target, 1, context.card)
        game._resolve_deaths()
        game._event("random_split_enemy_damage", player=context.player.index,
                    source=context.card.card_id, amount=amount, targets=hits)


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
        # Random effects are allowed to hit Stealth; only Dormant removes a
        # minion from the character pool.
        targets = game._random_enemy_minions(context.player.index)
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
        targets = game._random_enemy_minions(context.player.index)
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
class DamageEnemyMinions:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        enemy = game.players[1 - context.player.index]
        amount = game._spell_effect_amount(context.player, context.card, self.amount)
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
            available = game._random_enemy_minions(context.player.index)
            if not available:
                break
            target = game.rng.choice(available)
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
class HotSpringGliderBattlecry:
    """Discount the next Murloc; Kindred also grants this minion Divine Shield."""

    def execute(self, game: Any, context: RuleContext) -> None:
        kindred = bool(game._kindred_repeats(context.player, context.card))
        context.player.next_murloc_cost_reduction += 1
        if kindred:
            context.card.divine_shield = True
            context.card.divine_shield_hits = max(1, context.card.divine_shield_hits)
        game._event(
            "hot_spring_glider_battlecry",
            player=context.player.index,
            source=context.card.card_id,
            kindred=kindred,
        )


@dataclass(frozen=True)
class PrimalfinChallengerBattlecry:
    """Make the next active Kindred effect resolve twice."""

    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.kindred_triggers_twice = 1
        game._event("kindred_trigger_primed", player=context.player.index,
                    source=context.card.card_id)


@dataclass(frozen=True)
class SteamfinThiefKindred:
    """Kindred: summon two 1/1 Rush Murlocs."""

    def execute(self, game: Any, context: RuleContext) -> None:
        repeats = game._kindred_repeats(context.player, context.card)
        if not repeats:
            return
        summoned = 0
        for _ in range(2 * repeats):
            if len(context.player.board) + len(context.player.locations) >= 7:
                break
            token = game._entity("TLC_429t", created_by=context.card.card_id)
            token.rush = True
            token.summoned_turn = game.turn
            game._summon(context.player, token)
            summoned += 1
        game._event("steamfin_thief_kindred", player=context.player.index,
                    source=context.card.card_id, summoned=summoned)


@dataclass(frozen=True)
class AmbushPredatorsKindred:
    """Summon stealth poisonous Spitters, with a second one under Kindred."""

    def execute(self, game: Any, context: RuleContext) -> None:
        repeats = game._kindred_repeats(context.player, context.card)
        count = 2 if repeats == 2 else 1
        summoned = 0
        for _ in range(count):
            if len(context.player.board) + len(context.player.locations) >= 7:
                break
            token = game._entity("TLC_519t", created_by=context.card.card_id)
            token.stealth = True
            token.poisonous = True
            token.summoned_turn = game.turn
            game._summon(context.player, token)
            summoned += 1
        game._event("ambush_predators", player=context.player.index,
                    source=context.card.card_id, summoned=summoned)


@dataclass(frozen=True)
class GravedawnVoidbulbKindred:
    """Summon one or two random 4-cost minions with Taunt."""

    def execute(self, game: Any, context: RuleContext) -> None:
        repeats = game._kindred_repeats(context.player, context.card)
        count = 2 if repeats == 2 else 1
        candidates = [
            card_id for card_id in game.executable_card_ids
            if card_id in game.card_defs
            and game.card_defs[card_id].card_type == "MINION"
            and game.card_defs[card_id].cost == 4
        ]
        summoned = 0
        for _ in range(count):
            if not candidates or len(context.player.board) + len(context.player.locations) >= 7:
                break
            minion = game._entity(game.rng.choice(sorted(candidates)), created_by=context.card.card_id)
            minion.taunt = True
            minion.summoned_turn = game.turn
            game._summon(context.player, minion)
            summoned += 1
        game._event("gravedawn_voidbulb", player=context.player.index,
                    source=context.card.card_id, summoned=summoned)


@dataclass(frozen=True)
class ScalehideKodoBattlecry:
    """Destroy the lowest Attack enemy minion, or highest Attack with Kindred."""

    def execute(self, game: Any, context: RuleContext) -> None:
        enemy = game.players[1 - context.player.index]
        candidates = [m for m in enemy.board if m.health > 0]
        if not candidates:
            return
        reverse = bool(game._kindred_repeats(context.player, context.card))
        target = (max if reverse else min)(candidates, key=lambda m: m.attack)
        target.damage = target.max_health
        game._resolve_deaths()
        game._event("scalehide_kodo_destroy", player=context.player.index,
                    source=context.card.card_id, target=target.entity_id,
                    highest=reverse)


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
class DiscountRandomHeldMinion:
    amount: int = 1

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [card for card in context.player.hand
                      if card.definition.card_type == "MINION"]
        if not candidates:
            return
        card = game.rng.choice(candidates)
        card.cost_delta -= self.amount
        game._event("discount_random_minion", player=context.player.index,
                    source=context.card.card_id, target=card.entity_id,
                    amount=self.amount)


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
        kindred = bool(races & set(context.card.definition.races)) if context.card.definition.races else bool(races)
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
class HeraldAndHeroLifesteal:
    """Herald once and grant the controller's hero lifesteal this turn."""

    def execute(self, game: Any, context: RuleContext) -> None:
        game._herald_ragnaros(context.player, source=context.card.card_id)
        context.player.hero_lifesteal_turn = game.turn
        game._event(
            "hero_lifesteal_granted", player=context.player.index,
            source=context.card.card_id, turn=game.turn,
        )


@dataclass(frozen=True)
class HeraldDestroyRightAndGrow:
    """Cho'gall Soldier: destroy the minion to the right and grow."""

    def execute(self, game: Any, context: RuleContext) -> None:
        player = context.player
        try:
            index = player.board.index(context.card)
        except ValueError:
            return
        if index + 1 >= len(player.board):
            return
        right = player.board[index + 1]
        if right.dormant_turns > 0 or right.health <= 0:
            return
        right.damage = right.max_health
        game._event(
            "herald_destroy_right", player=player.index,
            source=context.card.entity_id, target=right.entity_id,
        )
        game._resolve_deaths()
        if context.card in player.board:
            amount = context.card.herald_power
            context.card.attack_delta += amount
            context.card.health_delta += amount
            game._event(
                "herald_grow", player=player.index,
                source=context.card.entity_id, amount=amount,
            )


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
        context.player.imbued_hero_power_id = self.card_id
        context.player.hero_power_imbues += 1
        game._event(
            "hero_power_imbued", player=context.player.index,
            source=context.card.card_id, hero_power=self.card_id,
            count=context.player.hero_power_imbues,
        )


@dataclass(frozen=True)
class SetHeroPowerCostOverride:
    cost: int | None

    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.hero_power_cost_override = self.cost
        game._event(
            "hero_power_cost_override", player=context.player.index,
            source=context.card.card_id, cost=self.cost,
        )


IMBUE_HERO_POWER_BY_CLASS = {
    "DRUID": "EDR_847p",
    "HUNTER": "EDR_850p",
    "MAGE": "EDR_851p",
    "PALADIN": "EDR_445p",
    "PRIEST": "EDR_449p",
    "ROGUE": "END_000p",
    "SHAMAN": "EDR_448p",
    "DEATHKNIGHT": "END_003p",
}


def imbue_hero_power_id(card_class: str) -> str | None:
    return IMBUE_HERO_POWER_BY_CLASS.get(card_class)


@dataclass(frozen=True)
class ImbueHeroPowerByClass:
    """Apply the Imbue power belonging to the controller's current class."""

    def execute(self, game: Any, context: RuleContext) -> None:
        power_id = imbue_hero_power_id(context.player.card_class)
        if power_id is None or power_id not in game.card_defs:
            game._event(
                "hero_power_imbue_unavailable", player=context.player.index,
                source=context.card.card_id, card_class=context.player.card_class,
            )
            return
        SetHeroPower(power_id).execute(game, context)


@dataclass(frozen=True)
class TriggerHeroPowerFree:
    """Resolve the current hero power without spending mana or using it."""

    def execute(self, game: Any, context: RuleContext) -> None:
        hero_power_id = context.player.hero_power_id
        if hero_power_id is None or hero_power_id not in game.card_defs:
            return
        card = game._entity(hero_power_id, created_by=context.card.card_id)
        if not game.rule_registry.dispatch(
            Hook.HERO_POWER, hero_power_id, game,
            RuleContext(player=context.player, card=card),
        ):
            raise ValueError(f"hero power has no executable rule: {hero_power_id}")
        game._event("hero_power_triggered_free", player=context.player.index,
                    source=context.card.card_id, hero_power=hero_power_id)


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
class DamageActionTargetThenSummonCopyIfKilled:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        owner = game.players[context.action.target_player]
        target = game._find_minion(owner.index, context.action.target_entity)
        card_id = target.card_id
        game._damage_minion(
            owner.index, target,
            game._spell_effect_amount(context.player, context.card, self.amount),
            context.card,
        )
        killed = target.health <= 0
        game._resolve_deaths()
        if killed:
            Summon(card_id).execute(game, context)


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
class IfHeroPowerImbued:
    """Execute nested effects only after enough Imbue events."""

    minimum: int
    effects: tuple[Effect, ...]

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.player.hero_power_imbues >= self.minimum:
            for effect in self.effects:
                effect.execute(game, context)


@dataclass(frozen=True)
class IfHoldingDarkGift:
    effects: tuple[Effect, ...]

    def execute(self, game: Any, context: RuleContext) -> None:
        if any(card.definition.card_type == "MINION" and card.gifts for card in context.player.hand):
            for effect in self.effects:
                effect.execute(game, context)


@dataclass(frozen=True)
class BuffHeldDarkGiftMinions:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        affected = 0
        for card in context.player.hand:
            if card.definition.card_type == "MINION" and card.gifts:
                card.cost_delta -= self.amount
                affected += 1
        game._event(
            "dark_gift_minion_discount", player=context.player.index,
            source=context.card.card_id, amount=self.amount, affected=affected,
        )


@dataclass(frozen=True)
class BuffEquippedWeaponAttack:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.player.weapon is not None:
            context.player.weapon.attack += self.amount
            game._event(
                "weapon_attack_buff", player=context.player.index,
                source=context.card.card_id, amount=self.amount,
                weapon=context.player.weapon.card_id,
            )


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
class BuffFriendlyBeastWithRush:
    """Give a selected friendly Beast +2/+2 and Rush."""

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player != context.player.index:
            raise ValueError("friendly Beast target is required")
        target = game._find_minion(context.action.target_player, context.action.target_entity)
        if not target.has_race("BEAST"):
            raise ValueError("target must be a Beast")
        target.attack_delta += 2
        target.health_delta += 2
        target.rush = True
        game._event("herbivore_assistant_buff", player=context.player.index,
                    source=context.card.card_id, target=target.entity_id)


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
        targets = game._random_enemy_minions(player.index)
        if targets:
            target = game.rng.choice(targets)
            game._forced_minion_attack(player.index, minion, enemy.index, target)
        game._event(
            "hand_stat_summon", player=player.index,
            source=context.card.card_id, card=minion.card_id,
            entity=minion.entity_id, stats=stats,
        )


@dataclass(frozen=True)
class SummonBloodFighterFromHandThenAttack:
    """Summon a Blood Fighter from hand, buff it, then attack randomly."""

    def execute(self, game: Any, context: RuleContext) -> None:
        player = context.player
        candidates = [
            card for card in player.hand
            if "blood fighter" in card.definition.name.casefold()
        ]
        if not candidates or len(player.board) + len(player.locations) >= 7:
            return
        summoned = game.rng.choice(candidates)
        player.hand.remove(summoned)
        summoned.attack_delta += 5
        summoned.health_delta += 5
        summoned.summoned_turn = game.turn
        game._summon(player, summoned)
        targets = game._random_enemy_characters(player.index)
        if targets:
            target_player, target_entity = game.rng.choice(targets)
            if target_entity is not None:
                game._forced_minion_attack(
                    player.index, summoned, target_player,
                    game._find_minion(target_player, target_entity),
                )
            else:
                game._damage_hero(game.players[target_player], summoned.attack, summoned)
        game._event(
            "blood_fighter_summoned", player=player.index,
            source=context.card.card_id, card=summoned.card_id,
            entity=summoned.entity_id,
        )


@dataclass(frozen=True)
class SummonBloodFighterFromHandBuffed:
    """Broll/Valeera recursive Blood Fighter deathrattle."""
    keyword: str

    def execute(self, game: Any, context: RuleContext) -> None:
        player = context.player
        candidates = [card for card in player.hand if "blood fighter" in card.definition.name.casefold()]
        if not candidates or len(player.board) + len(player.locations) >= 7:
            return
        summoned = game.rng.choice(candidates)
        player.hand.remove(summoned)
        summoned.attack_delta += 5
        summoned.health_delta += 5
        if self.keyword == "TAUNT":
            summoned.taunt = True
        else:
            summoned.elusive = True
        summoned.summoned_turn = game.turn
        game._summon(player, summoned)
        game._event("blood_fighter_recursive_summon", player=player.index,
                    source=context.card.card_id, card=summoned.card_id,
                    entity=summoned.entity_id, keyword=self.keyword)


@dataclass(frozen=True)
class EquipHighKingsHammer:
    """Muradin's Fabled Battlecry: equip the High King's Hammer."""

    def execute(self, game: Any, context: RuleContext) -> None:
        from .dragon_mirror import Weapon
        deck_card = next((card for card in context.player.deck if card.card_id == "TIME_209t"), None)
        if deck_card is None:
            return
        context.player.deck.remove(deck_card)
        game._equip_weapon(context.player, Weapon("TIME_209t", "High King's Hammer", 3, 4))
        context.card.high_kings_hammer_claimed = True


@dataclass(frozen=True)
class ReturnHammerIfClaimed:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.card.high_kings_hammer_claimed and len(context.player.hand) < 10:
            game._add_generated(context.player, game._entity("TIME_209t", created_by=context.card.card_id))


@dataclass(frozen=True)
class SummonAurasFromDeck:
    """Gelbin's Fabled Battlecry: pull one of each Aura from the deck."""

    def execute(self, game: Any, context: RuleContext) -> None:
        player = context.player
        selected: list[CardInstance] = []
        seen: set[str] = set()
        for card in list(player.deck):
            if "AURA" not in card.definition.mechanics or card.card_id in seen:
                continue
            if len(player.board) + len(player.locations) + len(selected) >= 7:
                break
            seen.add(card.card_id)
            selected.append(card)
        for card in selected:
            player.deck.remove(card)
            card.summoned_turn = game.turn
            game._summon(player, card)


@dataclass(frozen=True)
class EndtimeMurozondBattlecry:
    """Fill the board with random Dragons, heal fully, and skip next turn."""

    def execute(self, game: Any, context: RuleContext) -> None:
        # Import locally: the rule catalogue is intentionally independent of
        # the state model at module import time.
        from .dragon_mirror import DRAGON_IDS

        player = context.player
        summoned: list[str] = []
        while len(player.board) + len(player.locations) < 7:
            candidates = sorted(card_id for card_id in DRAGON_IDS if card_id in game.card_defs)
            if not candidates:
                break
            dragon_id = game.rng.choice(candidates)
            dragon = game._entity(dragon_id, created_by=context.card.card_id)
            dragon.summoned_turn = game.turn
            game._summon(player, dragon)
            summoned.append(dragon_id)
        player.health = player.max_health
        player.skip_next_turn = True
        game._event(
            "endtime_murozond_battlecry", player=player.index,
            source=context.card.card_id, summoned=summoned,
            healed=True, skip_next_turn=True,
        )


@dataclass(frozen=True)
class EmpowerAzsharaLocation:
    """Apply Lady Azshara's mutually-exclusive location empowerment."""

    selected: str

    def execute(self, game: Any, context: RuleContext) -> None:
        player = context.player
        kept = "TIME_211t2" if self.selected == "zin" else "TIME_211t1"
        empowered = "TIME_211t2t" if self.selected == "zin" else "TIME_211t1t"
        opposite = {"TIME_211t1", "TIME_211t1t"} if self.selected == "zin" else {
            "TIME_211t2", "TIME_211t2t"
        }
        destroyed: list[int] = []
        upgraded: list[int] = []
        for location in list(player.locations):
            if location.card_id in opposite:
                player.locations.remove(location)
                destroyed.append(location.entity_id)
            elif location.card_id == kept:
                location.card_id = empowered
                upgraded.append(location.entity_id)
        # The opposing empowerment is destroyed regardless of zone.  This is
        # intentionally broader than removing a location from the battlefield:
        # copies waiting in hand or deck are also destroyed by the card text.
        for zone_name in ("hand", "deck"):
            zone = getattr(player, zone_name)
            survivors = []
            for card in zone:
                if card.card_id in opposite:
                    destroyed.append(card.entity_id)
                    game._event(
                        "azshara_destroyed", player=player.index,
                        source=context.card.card_id, card=card.card_id,
                        entity=card.entity_id, zone=zone_name,
                    )
                else:
                    survivors.append(card)
            setattr(player, zone_name, survivors)
        game._event(
            "azshara_empowerment", player=player.index,
            source=context.card.card_id, selected=self.selected,
            upgraded=upgraded, destroyed=destroyed,
        )


@dataclass(frozen=True)
class ApplyBwonsamdiBoon:
    entity_id: int
    boon: str

    def execute(self, game: Any, context: RuleContext) -> None:
        target = next(
            (card for card in context.player.hand + context.player.board
             if card.entity_id == self.entity_id),
            None,
        )
        if target is None:
            return
        if self.boon == "power":
            target.taunt = True
        elif self.boon == "longevity":
            target.lifesteal = True
        elif self.boon == "speed":
            target.rush = True
        if self.boon not in target.gifts:
            target.gifts.append(self.boon)
        game._event(
            "bwonsamdi_boon", player=context.player.index,
            source=context.card.card_id, entity=target.entity_id, boon=self.boon,
        )


@dataclass(frozen=True)
class ApplyBwonsamdiBoonSpell:
    """Resolve a generated Boon spell onto the controller's Bwonsamdi."""
    boon: str

    def execute(self, game: Any, context: RuleContext) -> None:
        target = next((m for m in context.player.board if m.card_id == "TIME_619t"), None)
        if target is None:
            return
        ApplyBwonsamdiBoon(target.entity_id, self.boon).execute(game, context)
        target.boon_summon_cost_bonus = getattr(target, "boon_summon_cost_bonus", 0) + 2


@dataclass(frozen=True)
class WhatBefellZandalar:
    """Damage all enemies, then offer a Boon for the active Bwonsamdi."""

    def execute(self, game: Any, context: RuleContext) -> None:
        enemy = game.players[1 - context.player.index]
        game._damage_hero(enemy, 2, context.card)
        for minion in list(enemy.board):
            game._damage_minion(enemy.index, minion, 2)
        game._resolve_deaths()
        target = next((m for m in context.player.board if m.card_id == "TIME_619t"), None)
        if target is None:
            return
        OfferEffectChoice((
                ("Boon of Power", (ApplyBwonsamdiBoon(target.entity_id, "power"),)),
                ("Boon of Longevity", (ApplyBwonsamdiBoon(target.entity_id, "longevity"),)),
                ("Boon of Speed", (ApplyBwonsamdiBoon(target.entity_id, "speed"),)),
            )).execute(game, context)


@dataclass(frozen=True)
class AvatarForm:
    """Give a friendly minion +2 Attack and a one-shot attack blast."""

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player != context.player.index:
            return
        if context.action.target_entity is None:
            context.player.avatar_form_hero_pending = True
            context.player.hero_attack_bonus += 2
            game._event("avatar_form", player=context.player.index, target="hero")
            return
        target = game._find_minion(context.player.index, context.action.target_entity)
        target.temporary_attack_modifiers.append((2, game.turn))
        target.avatar_form_pending = True
        game._event("avatar_form", player=context.player.index, target=target.entity_id)


@dataclass(frozen=True)
class GelbinAuraEndTurn:
    """Resolve one turn of Gelbin's temporary Aura and expire it after 3 turns."""
    kind: str

    def execute(self, game: Any, context: RuleContext) -> None:
        aura = context.card
        remaining = int(getattr(aura, "aura_remaining_turns", 3))
        if self.kind == "heal":
            context.player.health = min(context.player.max_health, context.player.health + 4)
            for minion in context.player.board:
                if minion is not aura and minion.health > 0:
                    minion.damage = max(0, minion.damage - 4)
        else:
            candidates = [
                m for m in context.player.board
                if m is not aura and m.health > 0
                and m.definition.card_type == "MINION"
            ]
            if candidates:
                target = game.rng.choice(candidates)
                target.attack_delta += 4
                target.health_delta += 4
                target.divine_shield = True
        remaining -= 1
        aura.aura_remaining_turns = remaining
        game._event("gelbin_aura_tick", player=context.player.index,
                    source=aura.card_id, remaining=max(0, remaining))
        if remaining <= 0 and aura in context.player.board:
            context.player.board.remove(aura)
            game._event("gelbin_aura_expired", player=context.player.index, source=aura.card_id)


@dataclass(frozen=True)
class AzureOathstone:
    """Summon friendly Dragons that died this game, up to board capacity."""

    def execute(self, game: Any, context: RuleContext) -> None:
        player = context.player
        summoned = 0
        for dead in list(player.dead_minions):
            if len(player.board) + len(player.locations) >= 7:
                break
            if not dead.has_race("DRAGON"):
                continue
            copy = dead.clone(game.next_entity_id)
            game.next_entity_id += 1
            copy.damage = 0
            copy.summoned_turn = game.turn
            copy.created_by = context.card.card_id
            game._summon(player, copy)
            summoned += 1
        game._event("azure_oathstone_summon", player=player.index, summoned=summoned)


@dataclass(frozen=True)
class KindredHeroAttack:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if game._kindred_repeats(context.player, context.card):
            context.player.hero_attack_bonus += self.amount
            game._event("kindred_hero_attack", player=context.player.index,
                        source=context.card.card_id, amount=self.amount)


@dataclass(frozen=True)
class CryosleepKindred:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            return
        target = (context.action.target_player, context.action.target_entity)
        game._deal_to_target(context.player.index, target, 4, source=context.card)
        Draw().execute(game, context)
        repeats = game._kindred_repeats(context.player, context.card)
        for _ in range(repeats):
            Draw().execute(game, context)


@dataclass(frozen=True)
class CausticFumesKindred:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None or context.action.target_entity is None:
            return
        target = game._find_minion(context.action.target_player, context.action.target_entity)
        target.damage = target.max_health
        game._resolve_deaths()
        repeats = game._kindred_repeats(context.player, context.card)
        for _ in range(repeats):
            DamageAllMinions(2).execute(game, context)
            game._resolve_deaths()


@dataclass(frozen=True)
class ConjuredBookkeeperDeathrattle:
    def execute(self, game: Any, context: RuleContext) -> None:
        game._draw_matching(
            context.player,
            lambda card: card.definition.card_type == "SPELL",
        )
        repeats = game._kindred_repeats(context.player, context.card)
        if not repeats:
            return
        for _ in range(repeats):
            if len(context.player.board) + len(context.player.locations) >= 7:
                break
            copy = context.card.clone(game.next_entity_id)
            game.next_entity_id += 1
            copy.damage = 0
            copy.summoned_turn = game.turn
            copy.created_by = context.card.card_id
            game._summon(context.player, copy)
            game._event("conjured_bookkeeper_copy", player=context.player.index,
                        source=context.card.card_id, entity=copy.entity_id)


@dataclass(frozen=True)
class TimelessChestDeathrattle:
    """Fill the opponent's hand with Coins, respecting the hand cap."""

    def execute(self, game: Any, context: RuleContext) -> None:
        opponent = game.players[1 - context.player.index]
        added = 0
        while len(opponent.hand) < 10:
            coin = game._entity("GAME_005", created_by=context.card.card_id)
            opponent.hand.append(coin)
            added += 1
        game._event("timeless_chest_coins", player=opponent.index,
                    source=context.card.card_id, added=added)




@dataclass(frozen=True)
class SummonCopyOfFriendlyTarget:
    doubled: bool = False

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player != context.player.index:
            raise ValueError("friendly minion target is required")
        if context.action.target_entity is None:
            raise ValueError("friendly minion target is required")
        if len(context.player.board) + len(context.player.locations) >= 7:
            return
        target = game._find_minion(context.player.index, context.action.target_entity)
        copy = game._instance_from_definition(target.definition, created_by=context.card.card_id)
        copy.attack_delta = target.attack_delta
        copy.health_delta = target.health_delta
        copy.taunt = target.taunt
        copy.rush = target.rush
        copy.lifesteal = target.lifesteal
        if self.doubled:
            copy.attack_delta += target.attack
            copy.health_delta += target.max_health
        copy.summoned_turn = game.turn
        game._summon(context.player, copy)
        game._event(
            "zin_azshari_copy_summoned", player=context.player.index,
            source=context.card.card_id, target=target.entity_id,
            entity=copy.entity_id, doubled=self.doubled,
        )


@dataclass(frozen=True)
class FillHandRandomTemporarySpells:
    """Fill the controller's hand with random temporary spells."""

    doubled: bool = False

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [
            card_id for card_id in game.executable_card_ids
            if card_id in game.card_defs
            and game.card_defs[card_id].card_type == "SPELL"
        ]
        added: list[str] = []
        while len(context.player.hand) < 10 and candidates:
            card = game._entity(game.rng.choice(sorted(candidates)), created_by=context.card.card_id)
            card.temporary = True
            card.spell_casts_twice = self.doubled
            context.player.hand.append(card)
            added.append(card.card_id)
        game._event(
            "well_of_eternity_fill", player=context.player.index,
            source=context.card.card_id, cards=added, temporary=True,
        )


@dataclass(frozen=True)
class SummonOpponentArgusDemon:
    token_id: str = "TIME_020t2t"

    def execute(self, game: Any, context: RuleContext) -> None:
        enemy = game.players[1 - context.player.index]
        if len(enemy.board) + len(enemy.locations) >= 7:
            return
        token = game._entity(self.token_id, created_by=context.card.card_id)
        token.summoned_turn = game.turn
        game._summon(enemy, token)
        game._event(
            "argus_portal_summon", player=context.player.index,
            source=context.card.card_id, target_player=enemy.index,
            card=token.card_id, entity=token.entity_id,
        )


@dataclass(frozen=True)
class ArgusPortalDeathrattle:
    next_portal: str | None = None
    return_broxigar: bool = False

    def execute(self, game: Any, context: RuleContext) -> None:
        recipient = game.players[1 - context.player.index]
        if self.return_broxigar:
            if not recipient.broxigar_removed_from_game:
                game._event("argus_broxigar_return_skipped", player=recipient.index, source=context.card.card_id, reason="broxigar_not_removed")
                return
            if recipient.broxigar_return_used:
                game._event("argus_broxigar_return_skipped", player=recipient.index, source=context.card.card_id, reason="once_per_game")
                return
            recipient.broxigar_return_used = True
            if len(recipient.hand) < 10:
                recipient.hand.append(game._entity("TIME_020", created_by=context.card.card_id))
            game._event("argus_broxigar_return", player=recipient.index, source=context.card.card_id)
            return
        game._draw(recipient)
        if self.next_portal is not None:
            recipient.deck.insert(game.rng.randrange(len(recipient.deck) + 1), game._entity(self.next_portal, started_in_deck=True, created_by=context.card.card_id))
        game._event("argus_portal_deathrattle", player=recipient.index, source=context.card.card_id, next_portal=self.next_portal)


@dataclass(frozen=True)
class DrawFirstArgusPortalOnHeroKill:
    def execute(self, game: Any, context: RuleContext) -> None:
        attacked = (context.payload or {}).get("attacked")
        if not attacked or attacked[1] is None:
            return
        try:
            target = game._find_minion(attacked[0], attacked[1])
        except ValueError:
            return
        if target.health > 0:
            return
        portals = [
            card for card in context.player.deck
            if card.card_id in {"TIME_020t2", "TIME_020t3", "TIME_020t4", "TIME_020t5"}
        ]
        if not portals:
            return
        portal = game.rng.choice(portals)
        context.player.deck.remove(portal)
        if len(context.player.hand) < 10:
            context.player.hand.append(portal)
            destination = "hand"
        else:
            destination = "burned"
        game._event("axe_of_cenarius_portal", player=context.player.index, portal=portal.card_id, destination=destination)


@dataclass(frozen=True)
class TalanjiBattlecry:
    """Draw or resurrect Bwonsamdi, then offer one of three Boons."""

    def execute(self, game: Any, context: RuleContext) -> None:
        player = context.player
        target = next((card for card in player.deck if card.card_id == "TIME_619t"), None)
        if target is not None and len(player.hand) < 10:
            player.deck.remove(target)
            player.hand.append(target)
            game._event("talanji_draw_bwonsamdi", player=player.index, entity=target.entity_id)
        else:
            dead = next((card for card in reversed(player.dead_minions) if card.card_id == "TIME_619t"), None)
            if dead is None or len(player.board) + len(player.locations) >= 7:
                return
            player.dead_minions.remove(dead)
            target = game._instance_from_definition(dead.definition, created_by=context.card.card_id)
            target.summoned_turn = game.turn
            game._summon(player, target)
            game._event("talanji_resurrect_bwonsamdi", player=player.index, entity=target.entity_id)
        game.pending_choice = {
            "kind": "RULE_CHOICE", "player": player.index, "card": context.card,
            "action": context.action, "options": (
                ("Boon of Power", (ApplyBwonsamdiBoon(target.entity_id, "power"),)),
                ("Boon of Longevity", (ApplyBwonsamdiBoon(target.entity_id, "longevity"),)),
                ("Boon of Speed", (ApplyBwonsamdiBoon(target.entity_id, "speed"),)),
            ),
        }
        game._event("talanji_boon_choice", player=player.index, entity=target.entity_id)


@dataclass(frozen=True)
class TimethiefRafaamBattlecry:
    """Destroy the enemy hero after the other Fabled minions were played."""

    def execute(self, game: Any, context: RuleContext) -> None:
        from .dragon_mirror import FABLED_MINION_IDS

        required = set(FABLED_MINION_IDS) - {context.card.card_id}
        played = context.player.played_card_counts
        if required and not all(played.get(card_id, 0) > 0 for card_id in required):
            game._event(
                "rafaam_not_ready", player=context.player.index,
                source=context.card.card_id,
                remaining=sorted(card_id for card_id in required if not played.get(card_id, 0)),
            )
            return
        enemy = game.players[1 - context.player.index]
        enemy.health = 0
        game._event(
            "rafaam_destroy_enemy_hero", player=context.player.index,
            source=context.card.card_id, target_player=enemy.index,
        )


@dataclass(frozen=True)
class RafaamTokenBattlecry:
    """Shared executable effects for Timethief Rafaam's derived minions."""

    def execute(self, game: Any, context: RuleContext) -> None:
        player = context.player
        card_id = context.card.card_id
        rafaams = lambda card: "rafaam" in card.definition.name.casefold()
        if card_id == "TIME_005t1":
            candidates = [card for card in player.deck if rafaams(card)]
            if candidates and len(player.hand) < 10:
                drawn = game.rng.choice(candidates)
                player.deck.remove(drawn)
                player.hand.append(drawn)
                game._event("rafaam_token_draw", player=player.index, source=card_id, card=drawn.card_id)
        elif card_id == "TIME_005t2":
            affected = 0
            for zone in (player.hand, player.board):
                for card in zone:
                    if card is not context.card and rafaams(card):
                        card.attack_delta += 2
                        card.health_delta += 2
                        affected += 1
            game._event("rafaam_token_buff", player=player.index, source=card_id, affected=affected)
        elif card_id == "TIME_005t3":
            pool = [card.card_id for card in player.deck if rafaams(card)]
            game._offer_discover(player, pool, False, source_card_id=card_id)
        elif card_id == "TIME_005t4":
            amount = 5 * (2 if any(rafaams(card) and card is not context.card for card in player.hand) else 1)
            game._gain_armor(player, amount)
            game._event("rafaam_token_armor", player=player.index, source=card_id, amount=amount)
        elif card_id == "TIME_005t5":
            if any(rafaams(card) and card is not context.card for card in player.hand) and len(player.board) + len(player.locations) < 7:
                copy = context.card.clone(game.next_entity_id)
                game.next_entity_id += 1
                copy.created_by = card_id
                copy.summoned_turn = game.turn
                game._summon(player, copy)
                game._event("rafaam_token_copy", player=player.index, source=card_id, card=copy.card_id)
        elif card_id == "TIME_005t6":
            damaged = 0
            for owner in game.players:
                for minion in owner.board:
                    if not rafaams(minion):
                        game._damage_minion(owner.index, minion, 6)
                        damaged += 1
            game._resolve_deaths()
            game._event("rafaam_token_calamitous_damage", player=player.index, source=card_id, damaged=damaged)
        elif card_id == "TIME_005t8":
            player.rafaam_next_discount = True
            game._event("rafaam_token_discount", player=player.index, source=card_id, amount=3)


@dataclass(frozen=True)
class ArchmageRafaamBattlecry:
    """Transform every non-Rafaam minion into a vanilla 1/1 Sheep."""

    def execute(self, game: Any, context: RuleContext) -> None:
        transformed = 0
        for owner in game.players:
            for index, target in list(enumerate(owner.board)):
                if "rafaam" in target.definition.name.casefold():
                    continue
                sheep = game._entity("CS2_tk1", created_by=context.card.card_id)
                sheep.entity_id = target.entity_id
                owner.board[index] = sheep
                transformed += 1
        game._event("rafaam_archmage_transform", player=context.player.index, transformed=transformed)


@dataclass(frozen=True)
class AlleriaDiscoverSpell:
    def execute(self, game: Any, context: RuleContext) -> None:
        pool = [
            card_id for card_id in game.executable_card_ids
            if card_id in game.card_defs and game.card_defs[card_id].card_type == "SPELL"
        ]
        repeats = 1 + context.player.played_card_counts.get("TIME_609", 0) + context.player.played_card_counts.get("TIME_609t2", 0)
        game._offer_discover(context.player, pool, False, repeats=repeats, source_card_id=context.card.card_id)


@dataclass(frozen=True)
class VereesaBuffDeckMinions:
    def execute(self, game: Any, context: RuleContext) -> None:
        repeats = 1 + context.player.played_card_counts.get("TIME_609", 0) + context.player.played_card_counts.get("TIME_609t1", 0)
        affected = 0
        for card in context.player.deck:
            if card.definition.card_type != "MINION":
                continue
            card.attack_delta += repeats
            card.health_delta += repeats
            affected += 1
        game._event("vereesa_deck_buff", player=context.player.index, repeats=repeats, affected=affected)


@dataclass(frozen=True)
class DestroyHeldCardAndHalveEnemyHealth:
    card_id: str

    def execute(self, game: Any, context: RuleContext) -> None:
        enemy = game.players[1 - context.player.index]
        held = next((card for card in enemy.hand if card.card_id == self.card_id), None)
        if held is None:
            return
        enemy.hand.remove(held)
        enemy.health = max(1, enemy.health // 2)
        game._event(
            "destroy_held_card_halve_health", player=context.player.index,
            source=context.card.card_id, target_card=self.card_id,
            target_player=enemy.index,
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
class AddRandomLegendaryMinion:
    """Add one collectible/executable Legendary minion to hand."""

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [
            card_id for card_id in game.executable_card_ids
            if card_id in game.card_defs
            and game.card_defs[card_id].card_type == "MINION"
            and game.card_defs[card_id].rarity == "LEGENDARY"
        ]
        if not candidates or len(context.player.hand) >= 10:
            return
        card_id = game.rng.choice(sorted(candidates))
        game._add_generated(
            context.player,
            game._entity(card_id, created_by=context.card.card_id),
        )


@dataclass(frozen=True)
class SummonRandomLegendaryMinion:
    """Summon one random executable Legendary minion if board space exists."""

    def execute(self, game: Any, context: RuleContext) -> None:
        if len(context.player.board) + len(context.player.locations) >= 7:
            return
        candidates = [
            card_id for card_id in game.executable_card_ids
            if card_id in game.card_defs
            and game.card_defs[card_id].card_type == "MINION"
            and game.card_defs[card_id].rarity == "LEGENDARY"
        ]
        if not candidates:
            return
        minion = game._entity(game.rng.choice(sorted(candidates)), created_by=context.card.card_id)
        minion.summoned_turn = game.turn
        game._summon(context.player, minion)


@dataclass(frozen=True)
class SummonRandomMinionWithCost:
    """Summon a random executable minion with the requested printed cost."""

    cost: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if len(context.player.board) + len(context.player.locations) >= 7:
            return
        candidates = [
            card_id for card_id in game.executable_card_ids
            if card_id in game.card_defs
            and game.card_defs[card_id].card_type == "MINION"
            and game.card_defs[card_id].cost == requested_cost
        ]
        if not candidates:
            return
        minion = game._entity(
            game.rng.choice(sorted(candidates)), created_by=context.card.card_id
        )
        # Bwonsamdi's Boons carry over to the minion summoned by its
        # deathrattle.  Copy the keyword flags and the auditable gift labels.
        if context.card.gifts:
            minion.gifts = list(context.card.gifts)
            minion.taunt = minion.taunt or context.card.taunt
            minion.lifesteal = minion.lifesteal or context.card.lifesteal
            minion.rush = minion.rush or context.card.rush
        minion.summoned_turn = game.turn
        game._summon(context.player, minion)
        game._event(
            "random_cost_minion_summoned", player=context.player.index,
            source=context.card.card_id, card=minion.card_id,
            entity=minion.entity_id, cost=requested_cost,
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
class HealRandomFriendlyCharacters:
    """Distribute healing one point at a time across friendly characters."""

    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        player = context.player
        targets: list[tuple[str, Any]] = [("hero", player)]
        targets.extend(("minion", minion) for minion in player.board)
        for _ in range(max(0, self.amount)):
            eligible = [target for target in targets
                        if (target[1].health < target[1].max_health
                            if target[0] == "hero"
                            else target[1].damage > 0)]
            if not eligible:
                break
            kind, target = game.rng.choice(eligible)
            if kind == "hero":
                target.health = min(target.max_health, target.health + 1)
            else:
                target.damage = max(0, target.damage - 1)
        game._event("random_friendly_heal", player=player.index,
                    source=context.card.card_id, amount=self.amount)


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
    """Indexed executable rules with a small read-only mapping interface.

    The engine only needs dispatch helpers, while audits and tooling need to
    inspect coverage.  Exposing these methods keeps callers from reaching
    into the private ``_rules`` dictionary and gives us one place to enforce
    registry invariants.
    """

    def __init__(self, rules: tuple[CardRule, ...] = ()):
        self._rules: dict[str, CardRule] = {}
        for rule in rules:
            self.register(rule)

    def __len__(self) -> int:
        return len(self._rules)

    def __contains__(self, card_id: str) -> bool:
        return card_id in self._rules

    def get(self, card_id: str) -> CardRule | None:
        """Return a rule without exposing the mutable backing dictionary."""
        return self._rules.get(card_id)

    def all_rules(self) -> tuple[CardRule, ...]:
        """Return rules in stable card-id order for audits and reports."""
        return tuple(self._rules[card_id] for card_id in sorted(self._rules))

    def register(self, rule: CardRule) -> None:
        if rule.card_id in self._rules:
            raise ValueError(f"duplicate card rule: {rule.card_id}")
        self._rules[rule.card_id] = rule

    def dispatch(
        self, hook: Hook, card_id: str, game: Any, context: RuleContext
    ) -> bool:
        rule = self.get(card_id)
        if rule is None or hook not in rule.hooks:
            return False
        for effect in rule.hooks[hook]:
            effect.execute(game, context)
        return True

    def targeting(self, card_id: str) -> TargetSpec | None:
        rule = self.get(card_id)
        return None if rule is None else rule.targeting

    def has_hook(self, hook: Hook, card_id: str) -> bool:
        rule = self.get(card_id)
        return rule is not None and hook in rule.hooks

    def cost_adjustment(self, game: Any, player: Any, card: Any) -> int:
        rule = self.get(card.card_id)
        if rule is None or rule.cost_modifier is None:
            return 0
        return rule.cost_modifier.adjustment(game, player, card)

    def manifest(self) -> list[dict[str, Any]]:
        rows = []
        for rule in self.all_rules():
            card_id = rule.card_id
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
            "CORE_EX1_189", {Hook.BATTLECRY: (AddRandomLegendaryMinion(),)},
            RuleSource(
                "official_text_and_engine_pattern", "HearthstoneJSON 251332",
                verification=("test_brightwing_adds_random_legendary",),
            ),
        ),
        CardRule(
            "CORE_GVG_114", {Hook.DEATHRATTLE: (SummonRandomLegendaryMinion(),)},
            RuleSource(
                "official_text_and_engine_pattern", "HearthstoneJSON 251332",
                verification=("test_sneed_summons_random_legendary",),
            ),
        ),
        CardRule(
            "TIME_609", {Hook.BATTLECRY: (
                DamageAllEnemyCharacters(2, repeat_for_cards=("TIME_609t1", "TIME_609t2")),
            )},
            RuleSource(
                "official_text_and_engine_pattern", "HearthstoneJSON 251332",
                verification=("test_ranger_general_sylvanas_hits_all_enemies",),
            ),
        ),
        CardRule("TIME_020", {}, RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule("TIME_852", {}, RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule("TIME_852t1", {}, RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule("TIME_852t3", {Hook.SPELL: (AzureOathstone(),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule("TIME_006t1", {}, RuleSource("official_text", "HearthstoneJSON 251332")),
        CardRule("TIME_870t", {}, RuleSource("official_text", "HearthstoneJSON 251332")),
        CardRule("TIME_873t", {}, RuleSource("official_text", "HearthstoneJSON 251332")),
        CardRule("TIME_713t", {Hook.DEATHRATTLE: (TimelessChestDeathrattle(),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule("TLC_366", {}, RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332"),
                 cost_modifier=CostIfKindred(2)),
        CardRule("TLC_903", {Hook.BATTLECRY: (KindredHeroAttack(5),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule("TLC_440", {Hook.SPELL: (CryosleepKindred(),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332"),
                 targeting=TargetSpec(TargetKind.ANY_CHARACTER)),
        CardRule("TLC_447", {Hook.SPELL: (CausticFumesKindred(),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332"),
                 targeting=TargetSpec(TargetKind.ENEMY_MINION)),
        CardRule("TLC_226", {Hook.DEATHRATTLE: (ConjuredBookkeeperDeathrattle(),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule("TLC_428", {Hook.BATTLECRY: (HotSpringGliderBattlecry(),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule("TLC_251", {Hook.BATTLECRY: (PrimalfinChallengerBattlecry(),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule("TLC_251e", {}, RuleSource("official_text", "HearthstoneJSON 251332")),
        CardRule("TLC_429", {Hook.BATTLECRY: (SteamfinThiefKindred(),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule("TLC_429t", {}, RuleSource("official_text", "HearthstoneJSON 251332")),
        CardRule("TLC_519", {Hook.SPELL: (AmbushPredatorsKindred(),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule("TLC_519t", {}, RuleSource("official_text", "HearthstoneJSON 251332")),
        CardRule("TLC_815", {Hook.SPELL: (GravedawnVoidbulbKindred(),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule("TLC_816", {Hook.SPELL: (Draw(2),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332"),
                 cost_modifier=CostIfKindred(2)),
        CardRule("TLC_454", {Hook.BATTLECRY: (ScalehideKodoBattlecry(),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule(
            "TIME_850", {Hook.DEATHRATTLE: (SummonBloodFighterFromHandThenAttack(),)},
            RuleSource(
                "official_text_and_engine_pattern", "HearthstoneJSON 251332",
                verification=("test_logosh_summons_blood_fighter_and_attacks",),
            ),
        ),
        CardRule("TIME_850t", {Hook.DEATHRATTLE: (SummonBloodFighterFromHandBuffed("TAUNT"),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule("TIME_850t1", {Hook.DEATHRATTLE: (SummonBloodFighterFromHandBuffed("ELUSIVE"),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule(
            "TIME_209",
            {Hook.BATTLECRY: (EquipHighKingsHammer(),), Hook.DEATHRATTLE: (ReturnHammerIfClaimed(),)},
            RuleSource(
                "official_text_and_engine_pattern", "HearthstoneJSON 251332",
                verification=("test_muradin_equips_and_returns_hammer",),
            ),
        ),
        CardRule("TIME_209t", {},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule(
            "END_037", {Hook.BATTLECRY: (EndtimeMurozondBattlecry(),)},
            RuleSource(
                "official_text_and_engine_pattern", "HearthstoneJSON 251332",
                verification=("test_endtime_murozond_fills_heals_and_skips_turn",),
            ),
        ),
        CardRule(
            "TIME_211", {Hook.BATTLECRY: (
                OfferEffectChoice(options=(
                    ("Empower Zin-Azshari", (EmpowerAzsharaLocation("zin"),)),
                    ("Empower the Well of Eternity", (EmpowerAzsharaLocation("well"),)),
                )),
            )},
            RuleSource(
                "official_text_and_engine_pattern", "HearthstoneJSON 251332",
                verification=("test_lady_azshara_choice_empowers_one_location",),
            ),
        ),
        CardRule("TIME_211a", {Hook.SPELL: (EmpowerAzsharaLocation("zin"),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule("TIME_211b", {Hook.SPELL: (EmpowerAzsharaLocation("well"),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule("TIME_209t2", {Hook.SPELL: (AvatarForm(),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332"),
                 targeting=TargetSpec(TargetKind.FRIENDLY_CHARACTER)),
        CardRule(
            "TIME_619", {Hook.BATTLECRY: (TalanjiBattlecry(),)},
            RuleSource(
                "official_text_and_engine_pattern", "HearthstoneJSON 251332",
                verification=("test_talanji_draws_or_resurrects_bwonsamdi_and_offers_boon",),
            ),
        ),
        CardRule(
            "TIME_005", {Hook.BATTLECRY: (TimethiefRafaamBattlecry(),)},
            RuleSource(
                "official_text_and_engine_pattern", "HearthstoneJSON 251332",
                verification=("test_timethief_rafaam_requires_other_fabled_cards",),
            ),
        ),
        CardRule("TIME_005t1", {Hook.BATTLECRY: (RafaamTokenBattlecry(),), Hook.DEATHRATTLE: (RafaamTokenBattlecry(),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule("TIME_005t2", {Hook.BATTLECRY: (RafaamTokenBattlecry(),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule("TIME_005t3", {Hook.BATTLECRY: (RafaamTokenBattlecry(),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule("TIME_005t4", {Hook.BATTLECRY: (RafaamTokenBattlecry(),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule("TIME_005t5", {Hook.BATTLECRY: (RafaamTokenBattlecry(),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule("TIME_005t6", {Hook.BATTLECRY: (RafaamTokenBattlecry(),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule("TIME_005t7", {},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332"),
                 cost_modifier=RafaamCostDiscount("giant")),
        CardRule("TIME_005t8", {Hook.BATTLECRY: (RafaamTokenBattlecry(),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule("TIME_005t9", {Hook.BATTLECRY: (ArchmageRafaamBattlecry(),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule("TIME_005t9t", {}, RuleSource("official_text", "HearthstoneJSON 251332")),
        CardRule(
            "TIME_609t1", {Hook.BATTLECRY: (AlleriaDiscoverSpell(),)},
            RuleSource("official_text", "HearthstoneJSON 251332", verification=("test_alleria_discovers_and_repeats",)),
        ),
        CardRule(
            "TIME_609t2", {Hook.BATTLECRY: (VereesaBuffDeckMinions(),)},
            RuleSource("official_text", "HearthstoneJSON 251332", verification=("test_vereesa_buffs_deck_minions_and_repeats",)),
        ),
        CardRule(
            "TIME_619t", {Hook.DEATHRATTLE: (SummonRandomMinionWithCost(4),)},
            RuleSource(
                "official_text_and_engine_pattern", "HearthstoneJSON 251332",
                verification=("test_bwonsamdi_deathrattle_summons_random_four_cost",),
            ),
        ),
        CardRule("TIME_619t3", {Hook.SPELL: (ApplyBwonsamdiBoonSpell("power"),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule("TIME_619t2", {Hook.SPELL: (WhatBefellZandalar(),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule("TIME_619t4", {Hook.SPELL: (ApplyBwonsamdiBoonSpell("longevity"),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule("TIME_619t5", {Hook.SPELL: (ApplyBwonsamdiBoonSpell("speed"),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule(
            "TIME_020t2", {Hook.SPELL: (SummonOpponentArgusDemon(),)},
            RuleSource("official_text", "HearthstoneJSON 251332", verification=("test_first_portal_summons_opponent_demon",)),
        ),
        CardRule(
            "TIME_211t2", {Hook.LOCATION: (SummonCopyOfFriendlyTarget(False),)},
            RuleSource("official_text", "HearthstoneJSON 251332", verification=("test_zin_azshari_copies_friendly_minion",)),
            TargetSpec(TargetKind.FRIENDLY_MINION),
        ),
        CardRule(
            "TIME_211t2t", {Hook.LOCATION: (SummonCopyOfFriendlyTarget(True),)},
            RuleSource("official_text", "HearthstoneJSON 251332", verification=("test_zin_azshari_copies_friendly_minion",)),
            TargetSpec(TargetKind.FRIENDLY_MINION),
        ),
        CardRule(
            "TIME_211t1", {Hook.LOCATION: (FillHandRandomTemporarySpells(),)},
            RuleSource("official_text", "HearthstoneJSON 251332", verification=("test_well_fills_hand_with_temporary_spells",)),
        ),
        CardRule(
            "TIME_211t1t", {Hook.LOCATION: (FillHandRandomTemporarySpells(True),)},
            RuleSource("official_text", "HearthstoneJSON 251332", verification=("test_well_fills_hand_with_temporary_spells",)),
        ),
        CardRule(
            "EDR_800", {Hook.BATTLECRY: (ImbueHeroPowerByClass(),)},
            RuleSource(
                "official_text_and_engine_pattern",
                "HearthstoneJSON 251332; neutral Imbue resolves by controller class",
                verification=("test_neutral_imbue_uses_controller_class",),
            ),
        ),
        CardRule("TIME_020t1", {Hook.AFTER_HERO_ATTACK: (DrawFirstArgusPortalOnHeroKill(),)}, RuleSource("official_text", "HearthstoneJSON 251332")),
        CardRule("TIME_020t3", {Hook.SPELL: (SummonOpponentArgusDemon("TIME_020t3t"),)}, RuleSource("official_text", "HearthstoneJSON 251332")),
        CardRule("TIME_020t4", {Hook.SPELL: (SummonOpponentArgusDemon("TIME_020t4t"),)}, RuleSource("official_text", "HearthstoneJSON 251332")),
        CardRule("TIME_020t5", {Hook.SPELL: (SummonOpponentArgusDemon("TIME_020t5t"),)}, RuleSource("official_text", "HearthstoneJSON 251332")),
        CardRule("TIME_020t2t", {Hook.DEATHRATTLE: (ArgusPortalDeathrattle("TIME_020t3"),)}, RuleSource("official_text", "HearthstoneJSON 251332")),
        CardRule("TIME_020t3t", {Hook.DEATHRATTLE: (ArgusPortalDeathrattle("TIME_020t4"),)}, RuleSource("official_text", "HearthstoneJSON 251332")),
        CardRule("TIME_020t4t", {Hook.DEATHRATTLE: (ArgusPortalDeathrattle("TIME_020t5"),)}, RuleSource("official_text", "HearthstoneJSON 251332")),
        CardRule("TIME_020t5t", {Hook.DEATHRATTLE: (ArgusPortalDeathrattle(return_broxigar=True),)}, RuleSource("official_text", "HearthstoneJSON 251332")),
        CardRule(
            "EDR_845", {},
            RuleSource(
                "official_text_and_engine_pattern",
                "HearthstoneJSON 251332; all-Nature deck Start of Game and 3-spell repeat",
                verification=("test_hamuul_start_of_game_and_spell_threshold",),
            ),
        ),
        CardRule(
            "EDR_888", {Hook.BATTLECRY: (OfferLegendaryWildGodDiscover(),)},
            RuleSource(
                "official_text_and_engine_pattern",
                "HearthstoneJSON 251332; Legendary Wild God discover with 4-Imbue discount",
                verification=("test_malorne_discovers_legendary_and_discount",),
            ),
        ),
        CardRule(
            "EDR_102", {Hook.BATTLECRY: (
                OfferMinionDarkGiftDiscover(rarity="LEGENDARY"),
            )},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332", ("test_treacherous_tormentor_dark_gift_discover",)),
        ),
        CardRule(
            "EDR_811", {Hook.SPELL: (
                OfferMinionDarkGiftDiscover(race="UNDEAD", spend_corpses=2),
            )},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332", ("test_rite_of_atrocity_spends_corpses",)),
        ),
        CardRule(
            "EDR_488", {Hook.SPELL: (
                OfferMinionDarkGiftDiscover(mechanic="DEATHRATTLE"),
            )},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332", ("test_avant_gardening_dark_gift_discover",)),
        ),
        CardRule(
            "EDR_882", {Hook.SPELL: (
                OfferMinionDarkGiftDiscover(race="DEMON", min_cost=5),
            )},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332", ("test_jumpscare_dark_gift_discover",)),
        ),
        CardRule(
            "FIR_920", {Hook.SPELL: (
                OfferMinionDarkGiftDiscover(mechanics=("COMBO", "BATTLECRY", "STEALTH")),
            )},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332", ("test_smoke_bomb_dark_gift_discover",)),
        ),
        CardRule(
            "END_027", {Hook.SPELL: (
                OfferMinionDarkGiftDiscover(race="DRAGON"),
            )},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332", ("test_wings_of_eternity_dark_gift_discover",)),
        ),
        CardRule(
            "FIR_900", {Hook.SPELL: (
                OfferMinionDarkGiftDiscover(cost_delta=-2),
            )},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332", ("test_cremate_dark_gift_discount",)),
        ),
        CardRule(
            "FIR_901", {Hook.BATTLECRY: (
                IfHoldingDarkGift((Summon("FIR_901t", count=2),)),
            )},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332", ("test_frostburn_matriarch_dark_gift_condition",)),
        ),
        CardRule(
            "EDR_654", {Hook.BATTLECRY: (BuffHeldDarkGiftMinions(2),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332", ("test_overgrown_horror_discounts_dark_gifts",)),
        ),
        CardRule(
            "EDR_487", {},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332; hidden Dark Gift copy", ("test_wallow_copies_dark_gifts",)),
        ),
        CardRule(
            "FIR_922", {Hook.BATTLECRY: (
                IfHoldingDarkGift((BuffEquippedWeaponAttack(3),)),
            )},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332", ("test_cindersword_buffs_with_dark_gift",)),
        ),
        CardRule(
            "EDR_528", {Hook.SPELL: (OfferOpponentDeckMinionDiscover(),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332; Combo adds Dark Gift", ("test_nightmare_fuel_opponent_deck_combo",)),
        ),
        CardRule(
            "CORE_EDR_004", {Hook.BATTLECRY: (OfferRaptorHeraldDiscover(),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332; Beast Dark Gift discover", ("test_raptor_herald_dark_gift_discover",)),
        ),
        CardRule(
            "CORE_GIL_836", {Hook.SPELL: (OfferBattlecryMinionDiscover(),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332"),
        ),
        CardRule(
            "JAIL_460", {Hook.DEATHRATTLE: (AddRandomWeapon(),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332"),
        ),
        CardRule("TLC_435", {Hook.SPELL: (MapDiscover(rune="frost"),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule("TLC_442", {Hook.SPELL: (MapDiscover(race="MURLOC"),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule("TLC_464", {Hook.SPELL: (MapDiscover(unplayed_race=True),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule("TLC_515", {Hook.SPELL: (OfferDeckCardDiscover(map_followup=True),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule("TLC_824", {Hook.SPELL: (MapDiscover(odd_attack_beast=True),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule("TLC_900", {Hook.SPELL: (MapDiscover(spell_school="FEL"),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule(
            "DINO_419", {Hook.BATTLECRY: (BuffFriendlyBeastWithRush(),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332"),
            targeting=TargetSpec(TargetKind.FRIENDLY_MINION),
        ),
        CardRule(
            "DINO_421", {Hook.DEATHRATTLE: (
                BuffZone("hand", attack=3, health=3, card_types=("MINION",)),
                BuffZone("deck", attack=3, health=3, card_types=("MINION",)),
            )},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332"),
        ),
        CardRule(
            "CORE_EDR_004_2026", {Hook.BATTLECRY: (OfferRaptorHeraldDiscover(),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332; versioned Raptor Herald entity", ("test_raptor_herald_dark_gift_discover",)),
        ),
        # These cards have additional engine-level resolution branches in
        # dragon_mirror.py; registering them here keeps the audit manifest
        # complete without duplicating those branches declaratively.
        CardRule("EDR_456", {}, RuleSource("engine_branch", "dragon_mirror.py")),
        CardRule("EDR_856", {}, RuleSource("engine_branch", "dragon_mirror.py")),
        CardRule("FIR_924", {}, RuleSource("engine_branch", "dragon_mirror.py")),
        CardRule("FIR_939", {}, RuleSource("engine_branch", "dragon_mirror.py")),
        CardRule("FIR_956", {}, RuleSource("engine_branch", "dragon_mirror.py")),
        CardRule(
            "EDR_500", {Hook.BATTLECRY: (
                ImbueHeroPowerByClass(), SetHeroPowerCostOverride(0),
            )},
            RuleSource(
                "official_text_and_engine_pattern",
                "HearthstoneJSON 251332; neutral Imbue and next Hero Power is free",
                verification=("test_fleeing_treant_makes_next_power_free",),
            ),
        ),
        CardRule(
            "END_000", {Hook.SPELL: (DamageHero(2, "opponent"), SetHeroPower("END_000p"))},
            RuleSource(
                "official_text_and_engine_pattern",
                "HearthstoneJSON 251332; Eventuality deals 2 and Imbues",
                verification=("test_eventuality_damages_and_imbues",),
            ),
        ),
        CardRule(
            "END_001", {Hook.BATTLECRY: (ImbueHeroPowerByClass(),)},
            RuleSource(
                "official_text_and_engine_pattern",
                "HearthstoneJSON 251332; neutral/dual-class Imbue resolves by controller class",
                verification=("test_neutral_imbue_weapon_uses_controller_class",),
            ),
        ),
        CardRule(
            "END_003", {Hook.SPELL: (DrawMatching(card_type="MINION", race="UNDEAD"), ImbueHeroPowerByClass(), ImbueHeroPowerByClass())},
            RuleSource(
                "official_text_and_engine_pattern",
                "HearthstoneJSON 251332; Finality draws an Undead and Imbues twice",
                verification=("test_finality_draws_undead_and_imbues_twice",),
            ),
        ),
        CardRule(
            "END_003p", {},
            RuleSource(
                "official_text_and_engine_pattern",
                "HearthstoneJSON 251332; passive first-Undead-per-turn trigger",
                verification=("test_deathknight_imbue_first_undead_each_turn",),
            ),
        ),
        CardRule(
            "EDR_852", {Hook.BATTLECRY: (ImbueHeroPowerByClass(),)},
            RuleSource(
                "official_text_and_engine_pattern",
                "HearthstoneJSON 251332; neutral Imbue resolves by controller class",
                verification=("test_bitterbloom_knight_uses_controller_class",),
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
            "TIME_875", {Hook.BATTLECRY: (DestroyHeldCardAndHalveEnemyHealth("TIME_875t"),)},
            RuleSource(
                "official_text_and_engine_pattern", "HearthstoneJSON 251332",
                verification=("test_garona_destroys_king_llane_and_halves_health",),
            ),
        ),
        CardRule("TIME_875t1", {},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule(
            "TIME_009", {Hook.BATTLECRY: (SummonAurasFromDeck(),)},
            RuleSource(
                "official_text_and_engine_pattern", "HearthstoneJSON 251332",
                verification=("test_gelbin_pulls_distinct_auras_from_deck",),
            ),
        ),
        CardRule("TIME_009t1", {Hook.END_TURN: (GelbinAuraEndTurn("heal"),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule("TIME_009t2", {Hook.END_TURN: (GelbinAuraEndTurn("buff"),)},
                 RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332")),
        CardRule(
            "CORE_ULD_133", {Hook.END_TURN: (DrawIfUnspentMana(),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_crystal_merchant_draws_with_unspent_mana",),
            ),
        ),
        CardRule(
            "MEND_504", {Hook.SPELL: (DrawAndDiscountDrawn(scale_with_leyline=True),)},
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
            "MEND_500", {Hook.SPELL: (DamageRandomEnemyMinionExcess(4, scale_with_leyline=True),)},
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
            "MEND_501", {
                Hook.BATTLECRY: (DiscountHeldLeylines(),),
                Hook.DEATHRATTLE: (AddRandomLeyline(),),
            },
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_ley_walker_discount_and_random_deathrattle",),
            ),
        ),
        CardRule(
            "MEND_502", {Hook.SPELL: (SummonRandomLeylineMinion(),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_crystallized_leyline_summons_five_cost",),
            ),
        ),
        CardRule(
            "MEND_503", {Hook.BATTLECRY: (AddLeylineExtraTrigger(),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_surge_needle_adds_leyline_trigger",),
            ),
        ),
        CardRule(
            "MEND_506", {Hook.BATTLECRY: (UpgradeLeylines(),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_mystic_runesaber_upgrades_leylines",),
            ),
        ),
        CardRule(
            "EDR_940", {Hook.END_TURN: (GainArmorPerWisp(),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_merry_moonkin_armor_scales_with_wisps",),
            ),
        ),
        CardRule(
            "EDR_871", {Hook.BATTLECRY: (
                AddToHand("CORE_CS2_231"), SetHeroPower("EDR_851p"),
            )},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_spirit_gatherer_gets_wisp_and_imbues",),
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
            cost_modifier=CostIfKindred(3),
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
            "EDR_231", {Hook.SPELL: (HealActionTarget(4), Draw(), SetHeroPower("EDR_448p"))},
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
            "EDR_226", {Hook.BATTLECRY: (DrawMatching(race="BEAST"), SetHeroPower("EDR_850p"))},
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
            "CATA_156", {Hook.SPELL: (HeraldRagnaros(), DamageAllEnemies(4),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332; Herald event model", ("test_experimental_animation_heralds_and_damages_enemy_minions",)),
        ),
        CardRule(
            "CATA_525", {Hook.BATTLECRY: (HeraldRagnaros(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332; Herald event model", ("test_armored_bloodletter_heralds",)),
        ),
        CardRule(
            "CATA_530", {Hook.SPELL: (HeraldAndHeroLifesteal(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332; turn-level hero lifesteal", ("test_fel_infusion_herald_and_hero_lifesteal",)),
        ),
        CardRule(
            "CATA_561", {Hook.SPELL: (HeraldRagnaros(), Summon("CATA_561t", count=2),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332; Herald event model", ("test_ritual_of_power_heralds_and_summons_rushing_elementals",)),
        ),
        CardRule(
            "CATA_565", {Hook.BATTLECRY: (HeraldRagnaros(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332; Herald event model", ("test_skywall_sentinel_heralds",)),
        ),
        CardRule(
            "CATA_580", {Hook.BATTLECRY: (HeraldRagnaros(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332; Herald event model", ("test_cataclysmic_war_axe_heralds",)),
        ),
        CardRule(
            "CATA_780", {Hook.BATTLECRY: (HeraldRagnaros(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332; Herald event model", ("test_obsessive_technician_heralds",)),
        ),
        CardRule(
            "JAIL_COIN1", {Hook.SPELL: (GainMana(1),)},
            RuleSource(
                "powerlog_verified", local, "JAIL_COIN1", "internal",
                ("test_latest_powerlog_simple_rules",),
            ),
        ),
        CardRule(
            "CATA_725t", {Hook.END_TURN: (HeraldDestroyRightAndGrow(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332; Herald Soldier token", ("test_herald_chogall_soldier_destroys_right_and_grows",)),
        ),
        CardRule(
            "CATA_726t", {Hook.END_TURN: (HeraldDestroyRightAndGrow(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332; Herald Soldier token", ("test_herald_chogall_soldier_destroys_right_and_grows",)),
        ),
        CardRule(
            "CATA_726t1", {Hook.END_TURN: (HeraldDestroyRightAndGrow(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332; Herald Soldier token", ("test_herald_chogall_soldier_destroys_right_and_grows",)),
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
        CardRule(
            "EDR_860",
            {Hook.BATTLECRY: (IfHeroPowerImbued(2, (DamageActionTarget(4),)),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332", ("test_imbue_threshold_cards",)),
            TargetSpec(TargetKind.ANY_MINION, optional=True),
        ),
        CardRule(
            "EDR_847p", {Hook.HERO_POWER: (Summon("EDR_847pt2"),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332", ("test_imbue_hero_power_druid",)),
        ),
        CardRule(
            "EDR_850p", {Hook.HERO_POWER: (BuffRandomBeastInHand(),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332", ("test_imbue_hero_power_hunter",)),
        ),
        CardRule(
            "EDR_851p", {Hook.HERO_POWER: (SummonWisps(1), DamageRandomSplitEnemyCharacters(1),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332", ("test_imbue_hero_power_mage",)),
        ),
        CardRule(
            "EDR_448p", {Hook.HERO_POWER: (TransformFriendlyMinionRandom(),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332", ("test_imbue_hero_power_shaman",)),
        ),
        CardRule(
            "EDR_445p", {Hook.HERO_POWER: (AddToDeck("EDR_445pt3", count=2, shuffle=True),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332", ("test_imbue_hero_power_paladin",)),
        ),
        CardRule(
            "EDR_227", {Hook.DEATHRATTLE: (SetHeroPower("EDR_850p"),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332", ("test_imbue_minion_batch",)),
        ),
        CardRule(
            "EDR_518", {Hook.BATTLECRY: (SetHeroPower("EDR_448p"), DiscountRandomHeldMinion())},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332", ("test_living_garden_imbue_discount",)),
        ),
        CardRule(
            "EDR_519", {Hook.BATTLECRY: (SetHeroPower("EDR_851p"), TriggerHeroPowerFree())},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332", ("test_wisprider_triggers_imbued_power",)),
        ),
        CardRule(
            "EDR_264", {Hook.SPELL: (
                SummonRandomExecutableMinion(cost=2, require_taunt=True),
                SetHeroPower("EDR_445p"),
            )},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332", ("test_imbue_paladin_card_batch",)),
        ),
        CardRule(
            "EDR_451", {Hook.BATTLECRY: (SetHeroPower("EDR_445p"),), Hook.DEATHRATTLE: (SetHeroPower("EDR_445p"),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332", ("test_imbue_minion_batch",)),
        ),
        CardRule(
            "END_000p", {Hook.HERO_POWER: (AddRandomClassMinion(),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332", ("test_imbue_hero_power_rogue",)),
        ),
        CardRule(
            "FIR_921",
            {Hook.BATTLECRY: (IfHeroPowerImbued(2, (Draw(2),)),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332", ("test_imbue_threshold_cards",)),
        ),
        CardRule(
            "CORE_SW_442",
            {Hook.SPELL: (DamageActionTargetLifesteal(4),)},
            RuleSource(
                "upstream_adapted", rosetta, "SW_442", "AGPL-3.0",
                ("test_void_shard_lifesteal",),
            ),
            TargetSpec(TargetKind.ANY_CHARACTER),
        ),
        CardRule(
            "CORE_SCH_512", {Hook.SPELL: (DamageActionTargetThenSummonCopyIfKilled(4),)},
            RuleSource("upstream_adapted", rosetta, "SCH_512", "AGPL-3.0", ("test_initiation_summons_copy",)),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "CORE_LOOT_373", {Hook.SPELL: (HealRandomFriendlyCharacters(12),)},
            RuleSource("upstream_adapted", rosetta, "LOOT_373", "AGPL-3.0", ("test_healing_rain_random_split",)),
        ),
        CardRule(
            "TLC_439", {Hook.SPELL: (DamageEnemyMinions(2), IncreaseOpponentMinionCostNextTurn(2))},
            RuleSource("upstream_adapted", rosetta, "TLC_439", "AGPL-3.0", ("test_wave_of_tar",)),
        ),
    ))

"""Composable card rules for the deterministic simulator.

The module deliberately depends on the game through a small duck-typed API.
That keeps card declarations separate from ``dragon_mirror.py`` and avoids a
circular import between the state model and the rule catalogue.
"""

from __future__ import annotations

import copy
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
    AFTER_HERO_POWER = "after_hero_power"
    OTHER_FRIENDLY_ATTACK = "other_friendly_attack"
    AFTER_HEAL_ENEMY = "after_heal_enemy"
    AFTER_SUMMON = "after_summon"
    AFTER_DISCARD = "after_discard"
    AFTER_DAMAGE = "after_damage"
    LOCATION = "location"
    HERO_POWER = "hero_power"
    START_TURN = "start_turn"
    END_TURN = "end_turn"
    SHATTER = "shatter"
    OVERHEAL = "overheal"


class TargetKind(StrEnum):
    ANY_MINION = "any_minion"
    DAMAGED_MINION = "damaged_minion"
    FRIENDLY_MINION = "friendly_minion"
    FRIENDLY_WISP = "friendly_wisp"
    ENEMY_MINION = "enemy_minion"
    ENEMY_TYPED_MINION = "enemy_typed_minion"
    ANY_CHARACTER = "any_character"
    FRIENDLY_CHARACTER = "friendly_character"
    FRIENDLY_UNDEAD = "friendly_undead"
    ENEMY_CHARACTER = "enemy_character"
    FRIENDLY_HAND_MINION = "friendly_hand_minion"
    FRIENDLY_HAND_CARD = "friendly_hand_card"
    FRIENDLY_DRAGON = "friendly_dragon"
    FRIENDLY_BEAST = "friendly_beast"
    FRIENDLY_MINION_OR_HAND = "friendly_minion_or_hand"
    FRIENDLY_LOCATION = "friendly_location"
    ENEMY_LOCATION = "enemy_location"


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
    # Generated entities used by the 50-card Standard tranche below.
    "CORE_EX1_506a", "CORE_CS2_065", "CS2_101t", "NEW1_032", "NEW1_033",
    "NEW1_034", "UNG_810", "AV_337t", "TSC_076t", "TSC_076t2", "TSC_076t3",
    "CS2_008", "EX1_173", "BAR_878t", "DRG_217t",
    # Standard tranche 50H generated / transformed dependencies.
    "GIL_577t", "JAIL_436t", "JAIL_436t2", "JAIL_447t", "JAIL_805t",
    "JAIL_879t", "JAIL_881t", "TLC_234t", "TLC_237t",
    # Lost City tranche 50I generated hand cards.  These remain generated
    # dependencies rather than deck-construction entries.
    "TLC_622t", "TLC_829t", "GILA_500p2t",
}

# Some Core printings retain the historical behavior ID while the pinned JSON
# snapshot only contains the original printing. Load its metadata under the
# runtime ID, but keep the alias explicit and auditable.
DECLARATIVE_METADATA_ALIASES = {
    "CORE_EX1_277": "EX1_277",  # Arcane Missiles
    "CORE_CS2_172": "CS2_172",  # Bloodfen Raptor legacy fixture
    "CORE_CFM_606t": "CFM_606t",  # Mana Geode Overheal token
    "CORE_SW_439t": "SW_439t",  # Acorn token used by Core Vibrant Squirrel
}

# New full-Standard rules are kept separate from the historical Dragon slice
# so adding cards does not mutate the vocabulary of existing neural models.
STANDARD_DECLARATIVE_IDS = {
    "BE_036",  # M.O.T.H.E.R.
    "CORE_BAR_812",  # Oasis Ally
    "CAP_407",  # Wanted Poster
    "JAIL_735",  # Code Violet
    "JAIL_909",  # Defias Wannabe
    "JAIL_321",  # Tricksy Improviser
    "JAIL_326",  # Judgment
    "JAIL_913",  # Hold Them Off!
    "JAIL_444",  # Sawbones
    "JAIL_395",  # Sewer Swimmer
    "JAIL_721",  # Tras'tath, Soul Parasite
    "JAIL_718",  # Black Market Auctioneer
    "JAIL_407",  # Vanessa the Ringleader
    "TLC_828",  # Supreme Dinomancy
    "TLC_835",  # Story of Amara
    "TLC_901",  # Fumigate
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
    "END_017", "END_017t",  # Battle at the End Time / Tick and Tock
    "TLC_987",  # Questing Assistant
    "CORE_RLK_083", "CORE_RLK_116", "RLK_223",  # DK rune cards
    "TIME_611", "TIME_612", "TIME_613",  # DK rune cards
    "TIME_617", "CORE_RLK_706",  # DK rune cards
    "JAIL_443", "JAIL_445", "JAIL_454",  # DK rune cards
    "TIME_615",  # DK rune card
    "CATA_161", "CATA_301", "CATA_477", "CATA_527", "CATA_569", "CATA_724", "CORE_AT_052", "CORE_EX1_250", "CORE_OG_044", "Core_LOE_115", "CORE_ONY_018", "CORE_TSC_650", "CS3_007", "EDR_233", "EDR_257", "EDR_263", "EDR_454", "EDR_490", "EDR_520", "EDR_525", "EDR_570", "EDR_843", "EDR_872", "END_010", "END_028", "JAIL_380", "JAIL_462", "JAIL_877", "JAIL_887", "MEND_044", "TIME_044", "TIME_436", "TIME_446", "TIME_601", "TIME_810", "TLC_227", "TLC_449",  # Standard mechanism tranche
    # Continuous-aura entities already handled by the engine refresh pass.
    "CORE_NEW1_027", "CORE_CS2_122", "CORE_CS2_222", "CORE_EX1_507",
    "CORE_EX1_162", "JAIL_459", "EDR_258", "CATA_153t", "CATA_153t1", "CATA_565t",
    "EDR_844", "TLC_241", "TLC_241t",
    "CORE_WON_351", "JAIL_202", "EDR_480", "TTN_844", "CATA_130",
    "CAP_104", "CAP_106", "CORE_BT_187", "CORE_CATA_001", "CORE_EDR_003", "EDR_810",
    "JAIL_890", "TIME_606",
    "CAP_000", "CAP_003", "CAP_005",
    "TIME_042", "TIME_042t",
    "TIME_617",
    "CATA_721",
    "CORE_RLK_087", "TIME_216", "FIR_929", "TIME_858", "TIME_037",
    "EDR_234", "TIME_750", "CATA_568", "CATA_570", "TIME_213",
    "TIME_715", "END_020", "CORE_WC_701", "TIME_031", "TIME_032",
    "TIME_614", "RLK_720", "FIR_902", "JAIL_440", "TLC_630",
    # Dark Gift option entities are non-collectible cards selected by a
    # Discover.  Register their actual effects as well as the parent-card
    # Discover flow, so replay/import callers do not need a parallel path.
    "EDR_100t", "EDR_100t1", "EDR_100t2", "EDR_100t3", "EDR_100t4",
    "EDR_100t5", "EDR_100t6", "EDR_100t7", "EDR_100t8", "EDR_100t9",
    "EDR_100t10", "EDR_100t13",
    "EDR_101t", "EDR_101t1", "EDR_101t2", "EDR_101t3", "EDR_101t4",
    "EDR_101t5", "EDR_101t6", "EDR_101t7", "EDR_101t8", "EDR_101t9",
    "EDR_101t10", "EDR_101t11", "EDR_101t12", "EDR_101t13", "EDR_101t14",
    # Past/Present/Future Location variants use one shared transition model.
    "TIME_044t1", "TIME_044t2", "TIME_436t1", "TIME_436t2",
    "TIME_810t1", "TIME_810t2",
    "END_010a", "END_010b", "TIME_000ta", "TIME_000tb", "TIME_036t",
    "TIME_038t1", "TIME_038t2", "TIME_038t3", "TIME_618t",
    # CAP_405 trial option cards and the two-sided detection tokens.
    "CAP_004a", "CAP_004b", "CAP_405t1", "CAP_405t2", "CAP_405t3",
    "CAP_405t5", "CAP_405t6", "CAP_405t7", "CAP_405t8", "CAP_405t9",
    "CAP_405tb1", "CAP_405tb1b", "CAP_405tb2", "CAP_405tb2b",
    "CAP_405tb3", "CAP_405tb3b",
    # Auxiliary choices and Casts When Drawn entities emitted by Escape from
    # Violet Hold cards.
    "JAIL_201a", "JAIL_201b", "JAIL_319t", "JAIL_386t", "JAIL_443t",
    "EDR_416t", "EDR_463a", "EDR_463b", "EDR_490t", "EDR_445pt3",
    "EDR_102t", "EDR_454t", "EDR_517A", "EDR_517B", "EDR_818t",
    "END_017t", "FIR_951t2", "FIR_951t3", "FIR_951t4",
    "JAIL_442a", "JAIL_442b", "JAIL_452a", "JAIL_452b", "JAIL_455a", "JAIL_455b",
    "JAIL_458t1", "JAIL_458t2", "JAIL_458t3", "JAIL_458t4", "JAIL_461a", "JAIL_461b",
    "JAIL_504t", "JAIL_504t2", "JAIL_504t3", "JAIL_504t3p", "JAIL_504t5",
    "JAIL_800hp1", "JAIL_800hp2", "JAIL_803t", "JAIL_887t2", "JAIL_EVENT_101hp",
    # Elise's generated Map locations and quest/treasure follow-up entities.
    "TLC_100t11", "TLC_100t12", "TLC_100t13", "TLC_100t14", "TLC_100t15",
    "TLC_100t16", "TLC_100t17", "TLC_100t21", "TLC_100t22", "TLC_100t23",
    "TLC_100t24", "TLC_100t25", "TLC_100t26", "TLC_100t27", "TLC_100t31",
    "TLC_100t32", "TLC_100t33", "TLC_100t34", "TLC_100t35", "TLC_100t36",
    "TLC_100t37", "TLC_229t14", "TLC_239t", "TLC_426t", "TLC_433t",
    "TLC_433t2", "TLC_446t1",
    # Titanographer Osk's generated ability entities.  Osk stores the
    # selected ability on the parent Titan and the engine resolves the
    # ability state; these IDs must still be executable for imported logs and
    # generated-card validation.
    "TLC_452t1", "TLC_452t2", "TLC_452t3", "TLC_452t4", "TLC_452t5",
    "TLC_452t6", "TLC_452t7", "TLC_452t13", "TLC_452t14", "TLC_452t15",
    "TLC_452t16", "TLC_452t17", "TLC_452t18", "TLC_452t19", "TLC_452t20",
    "TLC_452t21", "TLC_452t22", "TLC_452t23", "TLC_452t24", "TLC_452t26",
    "TLC_452t27", "TLC_452t28", "TLC_452t29", "TLC_452t30", "TLC_452t31",
    "TLC_452t32", "TLC_452t33", "TLC_452t34", "TLC_452t35",
    # Quest reward and engine-owned follow-up entities.
    "TLC_452t8", "TLC_452t9", "TLC_460t", "TLC_513hp", "TLC_513t",
    "TLC_602t", "TLC_631t", "TLC_817t", "TLC_817t2", "TLC_817t3",
    "TLC_817t4", "TLC_817t5", "TLC_830t", "TLC_841t",
    "EDR_259e1", "RLK_008t", "RLK_039t", "RLK_061t", "RLK_085t",
    "RLK_226t", "RLK_907t",
    # 50-card Standard coverage tranche (23 metadata-keyword cards + 27
    # composable Battlecry/Deathrattle/spell cards).
    "RLK_067", "CORE_BT_921", "EDR_272", "CATA_558", "CORE_CS2_179",
    "CORE_DRG_079", "CORE_EX1_010", "CORE_EX1_028", "CORE_GIL_558",
    "CORE_GVG_085", "CORE_LOOT_137", "CORE_NEW1_023", "CORE_ULD_723",
    "CS3_038", "Core_CS2_200", "EDR_486", "EDR_598", "TIME_045",
    "TIME_053", "TIME_056", "TLC_248", "CORE_ICC_038", "CORE_BT_701",
    "CORE_EX1_082", "CORE_ULD_271", "CORE_EX1_058", "CORE_EX1_103",
    "CORE_EX1_506", "CORE_LOOT_413", "CORE_REV_308", "CORE_SW_088",
    "CORE_CS2_042", "CORE_EX1_134", "CORE_GVG_059", "CORE_EX1_362",
    "CORE_CFM_753", "CORE_TSC_076", "CORE_UNG_952", "CORE_GVG_061",
    "CORE_BAR_310", "CORE_EX1_198", "CORE_ICC_214", "CORE_NEW1_031",
    "CORE_OG_211", "CORE_AV_337", "CORE_RLK_062", "CORE_ULD_178",
    "CORE_WON_141", "CORE_LOOT_309", "CORE_RLK_657",
    "CATA_527t2",
    "EDR_454t",
    "UNG_028t", "UNG_067t1", "UNG_116t", "UNG_829t1", "UNG_920t1",
    "UNG_934t1", "UNG_940t8", "UNG_942t", "UNG_954t1",
    "UNG_999t2t1", "HERO_11bpt", "UNG_999t2", "UNG_999t3", "UNG_999t8",
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
    "JAIL_COIN1", "ETC_COIN2", "MUDAN_COIN1", "GDB_COIN2",  # The Coin printings
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
    # Standard coverage tranche 50B.  These IDs are loaded from the pinned
    # HearthstoneJSON snapshot and become executable through the rules below.
    "CORE_RLK_121", "CORE_EX1_007", "EDR_253", "EDR_256", "CORE_TRL_240",
    "CORE_NEW1_020", "CORE_NEW1_021", "EDR_110", "TLC_633", "CORE_KAR_057",
    "EDR_255", "FIR_961", "JAIL_118", "TIME_018", "TIME_019", "CAP_803",
    "CATA_304", "FIR_777", "TIME_427", "TIME_431", "TIME_855", "END_014",
    "TIME_600", "EDR_941", "EDR_874", "TLC_220", "END_023", "CATA_209",
    "CORE_BAR_878", "JAIL_461", "CORE_RLK_706", "EDR_842", "FIR_904",
    "CATA_552", "EDR_262", "MEND_302", "TIME_856", "TLC_365", "TLC_605",
    "TLC_621", "TLC_829", "TLC_987", "CATA_494", "JAIL_803", "END_026",
    "EDR_979", "EDR_540", "JAIL_503", "TLC_466", "JAIL_719",
    # Standard coverage tranche 50C.  The first group is engine-owned
    # lifecycle behavior; the remaining declarations are composable rules.
    "TLC_817", "CATA_139", "TLC_513", "TLC_446", "TLC_433", "TLC_460",
    "TLC_239", "TLC_229", "TLC_631", "TLC_830", "TLC_602", "JAIL_450",
    "TLC_426", "JAIL_430", "TLC_833", "JAIL_458", "EDR_847",
    "CORE_RLK_086", "CORE_LOOT_044", "TLC_478", "TLC_107", "JAIL_730",
    "JAIL_376", "JAIL_329", "FIR_907", "END_016", "DINO_408",
    "CORE_OG_031", "CORE_DAL_720", "CORE_BT_781", "CATA_472",
    "CATA_467", "CAP_103", "CORE_DMF_067", "CORE_DRG_403",
    "CORE_EX1_059", "CORE_GIL_534", "CORE_GIL_623", "CORE_KAR_062",
    "CORE_SCH_713", "CORE_UNG_928", "EDR_254", "EDR_470", "EDR_861",
    "END_008", "TLC_101", "TLC_468", "TIME_443", "END_031", "TLC_242",
    # Standard coverage tranche 50D. It combines engine-owned lifecycle
    # entries with core cards expressed through the shared rule primitives.
    "CATA_140", "CATA_190h", "DINO_435", "END_015", "JAIL_200", "TLC_825",
    "CORE_BOT_576", "CORE_BT_321", "CORE_BT_416", "CORE_CATA_002",
    "CORE_CATA_004", "CORE_CFM_781", "CORE_CFM_790", "CORE_DMF_511",
    "CORE_EDR_001", "CORE_EX1_131", "CORE_EX1_383", "CORE_EX1_559",
    "CORE_GIL_531", "CORE_ICC_210", "CORE_ICC_407", "CORE_LOE_039",
    "CORE_ONY_022", "CORE_SCH_181", "CORE_TID_931", "CORE_TRL_111",
    "CORE_TRL_900", "CORE_ULD_280", "CORE_WON_096", "Core_UNG_072",
    "DINO_130", "DINO_131", "DINO_403", "DINO_405", "DINO_412",
    "DINO_422", "DINO_433", "DINO_434", "EDR_001", "EDR_060", "EDR_105",
    "EDR_230", "EDR_252", "EDR_273", "EDR_481", "EDR_531", "EDR_848",
    "EDR_890", "EDR_942", "EDR_978",
    # Standard coverage tranche 50E: Time Travel cards grouped around the
    # shared "from the past" pools, Shreds of Time and time-state effects.
    "TIME_006", "TIME_016", "TIME_025", "TIME_026", "TIME_027",
    "TIME_028", "TIME_029", "TIME_036", "TIME_040", "TIME_047",
    "TIME_049", "TIME_050", "TIME_052", "TIME_055", "TIME_057",
    "TIME_061", "TIME_062", "TIME_100", "TIME_102", "TIME_212",
    "TIME_214", "TIME_215", "TIME_217", "TIME_428", "TIME_429",
    "TIME_434", "TIME_435", "TIME_444", "TIME_447", "TIME_448",
    "TIME_449", "TIME_616", "TIME_620", "TIME_700", "TIME_703",
    "TIME_704", "TIME_705", "TIME_707", "TIME_710", "TIME_711",
    "TIME_712", "TIME_716", "TIME_730", "TIME_857", "TIME_859",
    "TIME_860", "TIME_861", "TIME_870", "TIME_872", "TIME_873",
    # 50E non-collectible dependencies.
    "TIME_025t", "TIME_434t", "TIME_700t", "TIME_704t", "TIME_870t",
    "TIME_873t", "TIME_218",
    # Standard coverage tranche 50F: Cataclysm's persistent card-state
    # mechanics plus the Mending at the Maelstrom animal/recruit package.
    "CATA_132", "CATA_136", "CATA_180", "CATA_186", "CATA_208",
    "CATA_216", "CATA_305", "CATA_452", "CATA_458", "CATA_471",
    "CATA_473", "CATA_474", "CATA_475", "CATA_478", "CATA_483",
    "CATA_487", "CATA_493", "CATA_498", "CATA_499", "CATA_528",
    "CATA_529", "CATA_551", "CATA_553", "CATA_560", "CATA_564",
    "CATA_566", "CATA_567", "CATA_610", "CATA_614", "CATA_616",
    "CATA_697", "CATA_699", "CATA_786", "CATA_897", "CATA_978",
    "CATA_979", "MEND_041", "MEND_045", "MEND_300", "MEND_301",
    "MEND_303", "MEND_304", "MEND_305", "MEND_800", "MEND_801",
    "MEND_802", "MEND_803", "MEND_804", "MEND_805", "MEND_900",
    # 50F generated dependencies and held-in-hand transformed forms.
    "CATA_132t", "CATA_186t", "CATA_528t", "CATA_551t", "CATA_553t",
    # Standard coverage tranche 50G: a coherent set of basic combat,
    # persistent-cost, Reborn, transform and generated-card effects.
    "CAP_006", "CAP_101", "CAP_400", "CAP_802", "CAP_804", "CAP_805",
    "CAP_806", "CATA_480", "CATA_563", "CORE_AT_062",
    "CORE_BAR_313", "CORE_BOT_256", "CORE_ETC_111", "CORE_ETC_523",
    "CORE_SCH_605", "CORE_SW_047", "CORE_WON_350", "DINO_137", "DINO_402",
    "DINO_415", "DINO_424", "DINO_426", "DINO_427", "DINO_428",
    "DINO_429", "DINO_430", "EDR_014", "EDR_460", "EDR_461", "EDR_464",
    "EDR_472", "EDR_477", "EDR_482", "EDR_483", "EDR_484", "EDR_495",
    "EDR_530", "EDR_853", "END_002", "END_006", "END_009", "END_012",
    "END_013", "END_018", "END_029", "END_032", "FIR_778", "FIR_913",
    "FIR_955", "FIR_960",
    # Standard coverage tranche 50H: Secrets, deck placement, Smoldering
    # cards and the remaining low-complexity Violet Hold/Lost City cards.
    "CAP_401", "CAP_402", "CAP_403", "CAP_406", "CORE_AV_107",
    "CORE_CATA_006", "CORE_GIL_577", "CORE_TRL_345", "CORE_ULD_152",
    "EDR_455", "FIR_911", "FIR_914", "FIR_916", "FIR_918", "FIR_927",
    "FIR_940", "FIR_952", "JAIL_030", "JAIL_123", "JAIL_125",
    "JAIL_204", "JAIL_225", "JAIL_312", "JAIL_327", "JAIL_387",
    "JAIL_436", "JAIL_447", "JAIL_448", "JAIL_474", "JAIL_507",
    "JAIL_515", "JAIL_516", "JAIL_706", "JAIL_733", "JAIL_734",
    "JAIL_805", "JAIL_806", "JAIL_876", "JAIL_878", "JAIL_879",
    "JAIL_881", "JAIL_883", "JAIL_940", "JAIL_974", "JAIL_986",
    "TLC_234", "TLC_237", "TLC_244", "TLC_245", "TLC_256",
    # Standard coverage tranche 50I: the remaining Lost City collectible
    # cards plus Tribute Dance, whose runtime behaviour belongs to the same
    # Un'Goro card family in the pinned client build.
    "DINO_414", "TLC_106", "TLC_109", "TLC_230", "TLC_232", "TLC_233",
    "TLC_247", "TLC_250", "TLC_252", "TLC_254", "TLC_257", "TLC_334",
    "TLC_364", "TLC_427", "TLC_430", "TLC_438", "TLC_441", "TLC_443",
    "TLC_444", "TLC_450", "TLC_452", "TLC_462", "TLC_465", "TLC_467",
    "TLC_469", "TLC_477", "TLC_479", "TLC_483", "TLC_516", "TLC_517",
    "TLC_518", "TLC_520", "TLC_521", "TLC_601", "TLC_620", "TLC_622",
    "TLC_810", "TLC_811", "TLC_814", "TLC_818", "TLC_819", "TLC_821",
    "TLC_822", "TLC_826", "TLC_827", "TLC_831", "TLC_836", "TLC_840",
    "TLC_841",
    # Final pinned-Standard collectible closure.  Generated entities remain
    # separate from this deck-construction set.
    "CAP_405", "CATA_213", "CATA_307", "CATA_470", "CATA_621",
    "CORE_CFM_670", "CORE_DAL_575", "CORE_WON_145",
    "EDR_031", "EDR_209", "EDR_232", "EDR_238", "EDR_259", "EDR_261",
    "EDR_430", "EDR_489", "EDR_491", "EDR_494", "EDR_517", "EDR_522",
    "EDR_526", "EDR_527", "EDR_781", "EDR_812", "EDR_819", "EDR_873",
    "EDR_895", "JAIL_101", "JAIL_122", "JAIL_205", "JAIL_303", "JAIL_313",
    "JAIL_315", "JAIL_330", "JAIL_434", "JAIL_470", "JAIL_500", "JAIL_802",
    "JAIL_861", "MEND_100", "MEND_307", "MEND_505", "TIME_030", "TIME_041",
    "TIME_064", "TIME_103", "TIME_706", "TTN_851",
    # Non-collectible Coin variants are separate client entities, not aliases
    # of GAME_005.  They share the same temporary-mana rule, but keeping each
    # ID executable matters when a current-standard effect creates its own
    # printing of The Coin.
    "CATA_COIN1", "CATA_COIN2", "CATA_COIN3", "CATA_COIN4", "CATA_COIN5", "CATA_COIN6",
    "DINO_COIN1", "DINO_COIN2", "EDR_COIN1", "EDR_COIN2", "TLC_COIN2",
    "TIME_COIN1", "TIME_COIN2", "TIME_COIN3", "TIME_COIN4", "TIME_EVENT_COIN",
    "JAIL_COIN2", "JAIL_COIN3", "JAIL_EVENT_COIN", "GDB_COIN2",
    # Current-standard generated cards that resolve through the same normal
    # spell/minion dispatcher as deck cards.
    "CATA_158t", "CATA_552t", "CATA_553t", "MEND_100t", "TTN_843t1",
    "MEND_505t", "MEND_505t2", "MEND_505t3",
    # Emerald Dream option cards.  The parent Choose One card creates these
    # exact entities in client traces, so each is independently executable.
    "EDR_209a", "EDR_209b", "EDR_233a", "EDR_233b", "EDR_257a", "EDR_257b",
    "EDR_263a", "EDR_263b", "EDR_460t", "EDR_461t", "EDR_490a", "EDR_490b",
    "EDR_525A", "EDR_525B", "EDR_570A", "EDR_570B", "EDR_813a", "EDR_813b",
    "EDR_820a", "EDR_820b", "EDR_872A", "EDR_872B", "FIR_918t", "EDR_490t",
}

# These non-collectible entities are emitted and resolved by explicit engine
# lifecycle code instead of a composable CardRule.  They are deliberately not
# called "vanilla": each has a tested source-side trigger (summon, spell cast,
# deathrattle, or custom Location state).  The audit imports this manifest so
# they cannot be mistaken for an unimplemented generated card merely because
# their behavior does not live in ``build_rule_registry``.
ENGINE_OWNED_AUXILIARY_IDS = frozenset({
    "JAIL_446hp",                # Vampyr's Kiss hero power replacement
    "CATA_158t",                 # Soldier of Sinestra on-summon trigger
    "CATA_150t", "CATA_150t1",  # Hand of Ragnaros Herald forms
    "CATA_151t1",                # Azshara's upgraded Tentacle
    "CATA_464t",                 # Blackwing Experiment's Dragon Breath
    "CATA_550t", "CATA_550t2", "CATA_550t3", "CATA_550t4",
    "CATA_550t5", "CATA_550t6",  # Magmaw body variants
    "CATA_580t",                 # Soldier of Ragnaros
    "CATA_186t",                 # hand-position Sabotage state
    "CATA_190t10", "CATA_190t11", "CATA_190t12", "CATA_190t13",
    # Deathwing Cataclysm modes (resolved by _unleash_deathwing_cataclysm)
    "TLC_100t1", "TLC_100t2", "TLC_100t3",  # Elise-created Maps
    "TLC_446t",                  # Underfel Rift activation
})


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
class CostIfQuickdraw:
    """Quickdraw is active only when the card was drawn this turn."""

    amount: int

    def adjustment(self, game: Any, player: Any, card: Any) -> int:
        return -self.amount if getattr(card, "drawn_turn", -1) == game.turn else 0


@dataclass(frozen=True)
class CostIfNoMinionsOnBattlefield:
    """Set a card's displayed cost when neither board has a minion."""

    target_cost: int

    def adjustment(self, game: Any, _player: Any, card: Any) -> int:
        if any(candidate.board for candidate in game.players):
            return 0
        return self.target_cost - card.cost


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
class DrawUntilHandSize:
    target_size: int

    def execute(self, game: Any, context: RuleContext) -> None:
        while len(context.player.hand) < self.target_size and context.player.deck:
            before = len(context.player.hand)
            game._draw(context.player)
            if len(context.player.hand) == before:
                break


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
class DiscardHandGetInfiniteBanana:
    """King Maluk: discard the whole hand, then create Infinite Banana."""

    def execute(self, game: Any, context: RuleContext) -> None:
        player = context.player
        discarded = list(player.hand)
        player.hand.clear()
        for card in discarded:
            game._event(
                "discard", player=player.index, card=card.card_id,
                entity=card.entity_id, source=context.card.card_id,
            )
        if len(player.hand) < 10:
            banana = game._entity("TIME_042t", created_by=context.card.card_id)
            player.hand.append(banana)
            game._event(
                "king_maluk_banana", player=player.index,
                entity=banana.entity_id, card=banana.card_id,
            )


@dataclass(frozen=True)
class FlashFloodOutcast:
    """Deal five to the enemy board's edges, repeating for Outcast.

    Edges are recomputed after each pass.  This matters when the first pass
    kills an edge minion and the next pass therefore reaches a new edge.
    """

    amount: int = 5

    def execute(self, game: Any, context: RuleContext) -> None:
        enemy = game.players[1 - context.player.index]
        passes = 2 if getattr(context.card, "outcast_active", False) else 1
        for _ in range(passes):
            targets = [m for m in enemy.board
                       if m.health > 0 and m.dormant_turns == 0]
            if not targets:
                break
            # With one minion it occupies both edges and receives both hits.
            edge_targets = [targets[0], targets[-1]]
            for target in edge_targets:
                if target in enemy.board and target.health > 0:
                    game._damage_minion(enemy.index, target,
                                        game._spell_effect_amount(
                                            context.player, context.card,
                                            self.amount), context.card)
            game._resolve_deaths()
        game._event("flash_flood", player=context.player.index,
                    source=context.card.card_id, passes=passes)


@dataclass(frozen=True)
class SummonOutcastImmuneRaptors:
    """Horn of Feasting's three Rush Raptors and temporary attack immunity."""

    card_id: str = "DINO_136t"

    def execute(self, game: Any, context: RuleContext) -> None:
        summoned = []
        for _ in range(3):
            if len(context.player.board) + len(context.player.locations) >= 7:
                break
            raptor = game._entity(self.card_id, created_by=context.card.card_id)
            raptor.summoned_turn = game.turn
            game._summon(context.player, raptor)
            summoned.append(raptor)
        if getattr(context.card, "outcast_active", False):
            expiry = 1 - context.player.index
            for raptor in summoned:
                # The printed effect is combat-only: spells and attacks made
                # against a resting Raptor can still damage it.
                raptor.immune_while_attacking = True
                raptor.temporary_immune_expiry_turn = expiry
        game._event("horn_of_feasting", player=context.player.index,
                    source=context.card.card_id, summoned=[m.entity_id for m in summoned],
                    outcast=bool(getattr(context.card, "outcast_active", False)))


@dataclass(frozen=True)
class BygoneEchoesOutcast:
    """Summon a four-cost minion, with corpse and Outcast extra copies."""

    def execute(self, game: Any, context: RuleContext) -> None:
        SummonRandomMinionWithCost(4).execute(game, context)
        if context.player.corpses >= 4:
            context.player.corpses -= 4
            game._event("spend_corpses", player=context.player.index,
                        amount=4, source=context.card.card_id)
            SummonRandomMinionWithCost(4).execute(game, context)
        if getattr(context.card, "outcast_active", False):
            SummonRandomMinionWithCost(4).execute(game, context)


@dataclass(frozen=True)
class CosmicManifestationsOutcast:
    """Deal damage and shuffle random Demon Hunter spells into the deck."""

    amount: int = 2

    def execute(self, game: Any, context: RuleContext) -> None:
        repetitions = 2 if getattr(context.card, "outcast_active", False) else 1
        candidates = sorted(
            card_id for card_id in game.executable_card_ids
            if card_id in game.card_defs
            and game.card_defs[card_id].card_type == "SPELL"
            and game.card_defs[card_id].card_class == "DEMONHUNTER"
            and card_id != "JAIL_732"
            and not card_id.endswith("t")
        )
        enemy = game.players[1 - context.player.index]
        owner = context.player
        for _ in range(repetitions):
            game._damage_hero(enemy, game._spell_effect_amount(
                context.player, context.card, self.amount), context.card)
            if candidates:
                card_id = game.rng.choice(candidates)
                generated = game._entity(card_id, created_by=context.card.card_id)
                owner.deck.append(generated)
                game.rng.shuffle(owner.deck)
                game._event("cosmic_manifestation_shuffle", player=owner.index,
                            source=context.card.card_id, card=card_id,
                            entity=generated.entity_id)
        game._event("cosmic_manifestations", player=context.player.index,
                    source=context.card.card_id, repetitions=repetitions)


@dataclass(frozen=True)
class HeroImmuneUntilNextTurnIfOutcast:
    """Doomsday Prepper's Outcast-only hero immunity."""

    def execute(self, game: Any, context: RuleContext) -> None:
        if not getattr(context.card, "outcast_active", False):
            return
        context.player.hero_immune = True
        context.player.hero_immune_expiry_turn = game.turn + 2
        game._event("hero_immune_until_next_turn", player=context.player.index,
                    source=context.card.card_id,
                    expiry_turn=context.player.hero_immune_expiry_turn)


@dataclass(frozen=True)
class GainCorpses:
    amount: int = 1

    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.corpses += self.amount
        game._event("gain_corpses", player=context.player.index,
                    source=context.card.card_id, amount=self.amount)


@dataclass(frozen=True)
class SpendCorpsesDiscoverRune:
    rune: str
    amount: int = 1

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.player.corpses < self.amount:
            return
        context.player.corpses -= self.amount
        game._event("spend_corpses", player=context.player.index,
                    source=context.card.card_id, amount=self.amount)
        game._offer_rune_discover(
            context.player, rune=self.rune, source_card_id=context.card.card_id,
        )


@dataclass(frozen=True)
class OfferUndeadDiscoverWithCorpseKeep:
    def execute(self, game: Any, context: RuleContext) -> None:
        pool = [card_id for card_id, definition in game.card_defs.items()
                if card_id in game.executable_card_ids
                and definition.card_type == "MINION"
                and "UNDEAD" in definition.races]
        game._offer_discover(context.player, pool, dark_gift=False,
                             after_pick="keep_all_undead",
                             source_card_id=context.card.card_id)


@dataclass(frozen=True)
class OfferFiveCostCorpseCopy:
    def execute(self, game: Any, context: RuleContext) -> None:
        pool = [card_id for card_id, definition in game.card_defs.items()
                if card_id in game.executable_card_ids
                and definition.card_type == "MINION"
                and definition.cost == 5]
        game._offer_discover(context.player, pool, dark_gift=False,
                             after_pick="corpse_copy_5",
                             source_card_id=context.card.card_id)


@dataclass(frozen=True)
class SpendCorpsesBuffHand:
    base_attack: int = 1
    base_health: int = 1
    spend: int = 0
    bonus_attack: int = 1
    bonus_health: int = 1

    def execute(self, game: Any, context: RuleContext) -> None:
        for card in context.player.hand:
            if card.entity_id != context.card.entity_id:
                card.attack_delta += self.base_attack
                card.health_delta += self.base_health
        if context.player.corpses >= self.spend:
            context.player.corpses -= self.spend
            for card in context.player.hand:
                if card.entity_id != context.card.entity_id:
                    card.attack_delta += self.bonus_attack
                    card.health_delta += self.bonus_health
            game._event("spend_corpses", player=context.player.index,
                        source=context.card.card_id, amount=self.spend)


@dataclass(frozen=True)
class SummonCorpseTokens:
    card_id: str
    count: int
    spend: int = 0
    taunt: bool = False
    reborn_if_spent: bool = False
    rush: bool = False

    def execute(self, game: Any, context: RuleContext) -> None:
        can_spend = context.player.corpses >= self.spend
        if can_spend and self.spend:
            context.player.corpses -= self.spend
            game._event("spend_corpses", player=context.player.index,
                        source=context.card.card_id, amount=self.spend)
        for _ in range(self.count):
            if len(context.player.board) + len(context.player.locations) >= 7:
                break
            token = game._entity(self.card_id, created_by=context.card.card_id)
            token.taunt = self.taunt or token.taunt
            token.rush = self.rush or token.rush
            token.reborn = self.reborn_if_spent and can_spend
            token.summoned_turn = game.turn
            game._summon(context.player, token)


@dataclass(frozen=True)
class SpendCorpsesRandomDamage:
    max_corpses: int
    amount_per_corpse: int

    def execute(self, game: Any, context: RuleContext) -> None:
        spent = min(context.player.corpses, self.max_corpses)
        if spent <= 0:
            return
        context.player.corpses -= spent
        game._event("spend_corpses", player=context.player.index,
                    source=context.card.card_id, amount=spent)
        for _ in range(spent):
            targets = game._random_enemy_characters(context.player.index)
            if not targets:
                break
            target = game.rng.choice(targets)
            game._deal_to_target(
                context.player.index, target,
                game._spell_effect_amount(context.player, context.card,
                                           self.amount_per_corpse),
                source=context.card,
            )


@dataclass(frozen=True)
class SpendCorpsesRandomMinion:
    max_corpses: int

    def execute(self, game: Any, context: RuleContext) -> None:
        spent = min(context.player.corpses, self.max_corpses)
        if spent <= 0:
            return
        context.player.corpses -= spent
        game._event("spend_corpses", player=context.player.index,
                    source=context.card.card_id, amount=spent)
        game._summon_random_executable_minion(
            context.player, source_card_id=context.card.card_id, cost=spent,
        )


@dataclass(frozen=True)
class SpendCorpseDamageActionTarget:
    spend: int
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("minion target is required")
        if context.player.corpses < self.spend:
            return
        target = game._find_minion(context.action.target_player,
                                   context.action.target_entity)
        context.player.corpses -= self.spend
        game._damage_minion(context.action.target_player, target,
                            game._spell_effect_amount(context.player,
                                                       context.card,
                                                       self.amount),
                            context.card)
        game._resolve_deaths()
        game._event("spend_corpses_target_damage", player=context.player.index,
                    source=context.card.card_id, target=target.entity_id,
                    amount=self.spend)


@dataclass(frozen=True)
class RaiseCorpseFootmen:
    max_count: int
    card_id: str
    attack_damage: int = 0
    health_damage: int = 0
    taunt: bool = True
    rush: bool = False

    def execute(self, game: Any, context: RuleContext) -> None:
        slots = max(0, 7 - len(context.player.board) - len(context.player.locations))
        count = min(context.player.corpses, self.max_count, slots)
        if count <= 0:
            return
        context.player.corpses -= count
        game._event("spend_corpses", player=context.player.index,
                    source=context.card.card_id, amount=count)
        for _ in range(count):
            if len(context.player.board) + len(context.player.locations) >= 7:
                break
            token = game._entity(self.card_id, created_by=context.card.card_id)
            token.taunt = self.taunt
            token.rush = self.rush
            token.summoned_turn = game.turn
            game._summon(context.player, token)


@dataclass(frozen=True)
class GraveStrength:
    base_attack: int = 1
    corpse_threshold: int = 5
    upgraded_attack: int = 3

    def execute(self, game: Any, context: RuleContext) -> None:
        attack = self.base_attack
        if context.player.corpses >= self.corpse_threshold:
            context.player.corpses -= self.corpse_threshold
            attack = self.upgraded_attack
            game._event("spend_corpses", player=context.player.index,
                        source=context.card.card_id, amount=self.corpse_threshold)
        for minion in context.player.board:
            minion.attack_delta += attack


@dataclass(frozen=True)
class ChowDown:
    def execute(self, game: Any, context: RuleContext) -> None:
        rush = context.player.corpses >= 8
        if rush:
            context.player.corpses -= 8
            game._event("spend_corpses", player=context.player.index,
                        source=context.card.card_id, amount=8)
        for _ in range(5):
            if len(context.player.board) + len(context.player.locations) >= 7:
                break
            drake = game._entity("CATA_465t", created_by=context.card.card_id)
            drake.rush = rush
            drake.summoned_turn = game.turn
            game._summon(context.player, drake)


@dataclass(frozen=True)
class MalignantHorrorEndTurn:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.player.corpses < 4:
            return
        if len(context.player.board) + len(context.player.locations) >= 7:
            return
        context.player.corpses -= 4
        game._event("spend_corpses", player=context.player.index,
                    source=context.card.card_id, amount=4)
        copy = context.card.clone(game.next_entity_id)
        game.next_entity_id += 1
        copy.created_by = context.card.card_id
        copy.damage = 0
        copy.summoned_turn = game.turn
        game._summon(context.player, copy)


@dataclass(frozen=True)
class RaiseOneCorpseEndTurn:
    def execute(self, game: Any, context: RuleContext) -> None:
        RaiseCorpseFootmen(1, "RLK_061t").execute(game, context)


@dataclass(frozen=True)
class ArmCorpseRebirth:
    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.corpse_rebirth_pending = True
        game._event("corpse_rebirth_armed", player=context.player.index,
                    source=context.card.card_id)


@dataclass(frozen=True)
class JaraxxusInferno:
    def execute(self, game: Any, context: RuleContext) -> None:
        if len(context.player.board) + len(context.player.locations) >= 7:
            return
        infernal = game._entity("EX1_tk34", created_by=context.card.card_id)
        infernal.summoned_turn = game.turn
        game._summon(context.player, infernal)
        game._event("jaraxxus_inferno", player=context.player.index,
                    entity=infernal.entity_id)


@dataclass(frozen=True)
class DestroyHighAttackMinion:
    threshold: int = 7

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_entity is None:
            raise ValueError("enemy minion target is required")
        target = game._find_minion(context.action.target_player,
                                   context.action.target_entity)
        if target.attack < self.threshold:
            raise ValueError("Big Game Hunter requires a 7+ Attack target")
        target.damage = target.max_health
        game._resolve_deaths()


@dataclass(frozen=True)
class DestroyHighestAttackEnemy:
    """Asphyxiate: destroy the highest-Attack enemy minion (random tie)."""

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [m for m in game.players[1 - context.player.index].board
                      if m.dormant_turns == 0 and m.health > 0]
        if not candidates:
            return
        highest = max(m.attack for m in candidates)
        target = game.rng.choice([m for m in candidates if m.attack == highest])
        target.damage = target.max_health
        game._resolve_deaths()


@dataclass(frozen=True)
class DamageThenDrawIfSurvives:
    amount: int
    draws: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("enemy minion target is required")
        target = game._find_minion(context.action.target_player,
                                   context.action.target_entity)
        game._damage_minion(
            context.action.target_player, target,
            game._spell_effect_amount(context.player, context.card, self.amount),
            context.card,
        )
        survives = target.health > 0
        game._resolve_deaths()
        if survives:
            for _ in range(self.draws):
                game._draw(context.player)


@dataclass(frozen=True)
class DamageThenDrawExcess:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("enemy minion target is required")
        target = game._find_minion(context.action.target_player,
                                   context.action.target_entity)
        before = max(0, target.health)
        damage = game._spell_effect_amount(context.player, context.card, self.amount)
        game._damage_minion(context.action.target_player, target, damage, context.card)
        excess = max(0, damage - before)
        game._resolve_deaths()
        for _ in range(excess):
            game._draw(context.player)


@dataclass(frozen=True)
class DrawMinionBuffHand:
    health: int

    def execute(self, game: Any, context: RuleContext) -> None:
        DrawMatching(card_type="MINION").execute(game, context)
        for card in context.player.hand:
            if card.definition.card_type == "MINION":
                card.health_delta += self.health


@dataclass(frozen=True)
class DrawAndLockForTurns:
    count: int
    turns: int

    def execute(self, game: Any, context: RuleContext) -> None:
        for _ in range(self.count):
            before = set(card.entity_id for card in context.player.hand)
            game._draw(context.player)
            for card in context.player.hand:
                if card.entity_id not in before:
                    card.playable_after_turn = game.turn + self.turns


@dataclass(frozen=True)
class DamageTargetThenConditionalMinionDraw:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        DamageActionTarget(self.amount).execute(game, context)
        if any(card.definition.card_type == "MINION" and card.cost >= 5
               for card in context.player.hand):
            DrawMatching(card_type="MINION").execute(game, context)


@dataclass(frozen=True)
class DrawTwoDiscountByHeroAttacks:
    def execute(self, game: Any, context: RuleContext) -> None:
        discount = context.player.hero_attacks_this_game
        for _ in range(2):
            before = set(card.entity_id for card in context.player.hand)
            game._draw(context.player)
            for card in context.player.hand:
                if card.entity_id not in before:
                    card.cost_delta -= discount


@dataclass(frozen=True)
class DrawCostRepeatExcess:
    discount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        remaining = self.discount
        while remaining > 0:
            before = set(card.entity_id for card in context.player.hand)
            game._draw(context.player)
            drawn = [card for card in context.player.hand if card.entity_id not in before]
            if not drawn:
                break
            card = drawn[-1]
            applied = min(remaining, card.cost)
            card.cost_delta -= remaining
            remaining -= applied
            if applied == 0:
                break


@dataclass(frozen=True)
class DamageThenDrawOrSummonOneCost:
    """Eternal Toil: damage a minion, then draw or summon on death."""

    amount: int = 1

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("minion target is required")
        target = game._find_minion(
            context.action.target_player, context.action.target_entity
        )
        game._damage_minion(
            context.action.target_player, target,
            game._spell_effect_amount(context.player, context.card, self.amount),
            context.card,
        )
        died = target.health <= 0
        game._resolve_deaths()
        if died:
            game._summon_random_executable_minion(
                context.player, source_card_id=context.card.card_id, cost=1,
            )
        else:
            game._draw(context.player)


@dataclass(frozen=True)
class DrawDifferentCosts:
    """Draw up to ``count`` cards with distinct printed costs."""

    count: int = 3

    def execute(self, game: Any, context: RuleContext) -> None:
        used_costs: set[int] = set()
        drawn: list[str] = []
        for _ in range(self.count):
            candidates = [
                card for card in context.player.deck
                if card.definition.cost not in used_costs
            ]
            if not candidates:
                break
            card = game.rng.choice(candidates)
            context.player.deck.remove(card)
            game._refresh_scrappy(context.player)
            used_costs.add(card.definition.cost)
            game._receive_drawn_card(context.player, card)
            drawn.append(card.card_id)
        game._event(
            "draw_different_costs", player=context.player.index,
            source=context.card.card_id, cards=drawn,
        )


@dataclass(frozen=True)
class ChronogorDrawHighestGiveLowest:
    """Draw two highest-cost cards and give two lowest-cost deck cards to enemy."""

    count: int = 2

    def execute(self, game: Any, context: RuleContext) -> None:
        player = context.player
        enemy = game.players[1 - player.index]
        highest: list[Any] = []
        remaining = list(player.deck)
        for _ in range(min(self.count, len(remaining))):
            cost = max(game._effective_cost(player, card) for card in remaining)
            choices = [card for card in remaining
                       if game._effective_cost(player, card) == cost]
            card = game.rng.choice(choices)
            remaining.remove(card)
            player.deck.remove(card)
            game._refresh_scrappy(player)
            game._receive_drawn_card(player, card)
            highest.append(card.card_id)
        lowest: list[str] = []
        for _ in range(min(self.count, len(player.deck))):
            cost = min(game._effective_cost(player, card) for card in player.deck)
            choices = [card for card in player.deck
                       if game._effective_cost(player, card) == cost]
            card = game.rng.choice(choices)
            player.deck.remove(card)
            if len(enemy.hand) < 10:
                enemy.hand.append(card)
                destination = "opponent_hand"
            else:
                destination = "burned"
            lowest.append(card.card_id)
            game._event(
                "chronogor_give_lowest", player=player.index,
                recipient=enemy.index, card=card.card_id, destination=destination,
            )
        game._event(
            "chronogor_draw", player=player.index,
            highest=highest, lowest=lowest,
        )


@dataclass(frozen=True)
class LiferenderIfHeroHealthChanged:
    amount: int = 6

    def execute(self, game: Any, context: RuleContext) -> None:
        if not getattr(context.player, "hero_health_changed_this_turn", False):
            return
        if context.action is None or context.action.target_player is None:
            return
        target = game._find_minion(
            context.action.target_player, context.action.target_entity
        )
        game._damage_minion(
            context.action.target_player, target,
            game._spell_effect_amount(context.player, context.card, self.amount),
            context.card,
        )
        game._resolve_deaths()


@dataclass(frozen=True)
class GnomeMuncherEndTurn:
    """Attack the lowest-health enemy character, including the enemy hero."""

    def execute(self, game: Any, context: RuleContext) -> None:
        enemy = game.players[1 - context.player.index]
        targets: list[tuple[int, int | None, int]] = [(enemy.index, None, enemy.health)]
        targets.extend((enemy.index, minion.entity_id, minion.health)
                       for minion in enemy.board
                       if minion.health > 0 and minion.dormant_turns == 0)
        if not targets or context.card.health <= 0:
            return
        lowest = min(health for _, _, health in targets)
        target_player, target_entity, _ = game.rng.choice(
            [target for target in targets if target[2] == lowest]
        )
        if target_entity is None:
            context.card.attacks_this_turn += 1
            context.card.stealth = False
            game._damage_hero(enemy, context.card.attack, context.card)
            game._after_minion_attack(
                context.player.index, context.card, attacked_minion=False,
            )
        else:
            target = game._find_minion(target_player, target_entity)
            game._forced_minion_attack(
                context.player.index, context.card, target_player, target,
            )
        game._event(
            "gnome_muncher_attack", player=context.player.index,
            source=context.card.entity_id, target_player=target_player,
            target_entity=target_entity,
        )


@dataclass(frozen=True)
class ArmSigilOfCinder:
    damage: int = 6

    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.sigil_of_cinder_turn = game.turn + 1
        context.player.sigil_of_cinder_damage = self.damage
        game._event(
            "sigil_of_cinder_armed", player=context.player.index,
            source=context.card.card_id, trigger_turn=game.turn + 1,
            damage=self.damage,
        )


@dataclass(frozen=True)
class SummonFrailGhoulsAfterDamage:
    count: int = 2

    def execute(self, game: Any, context: RuleContext) -> None:
        # Damage triggers resolve before the engine's death pass, so a lethal
        # hit still creates both tokens while the Tower occupies its board
        # slot.  The same ordering is used by Acolyte of Pain and other
        # "takes damage" effects.
        if context.card not in context.player.board:
            return
        summoned: list[int] = []
        for _ in range(self.count):
            if len(context.player.board) + len(context.player.locations) >= 7:
                break
            token = game._summon_frail_ghoul(
                context.player, source_card_id=context.card.card_id,
            )
            if token is not None:
                summoned.append(token.entity_id)
        game._event(
            "tower_of_ghouls", player=context.player.index,
            source=context.card.entity_id, summoned=summoned,
        )


@dataclass(frozen=True)
class GorishiStingerAfterDamage:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.card not in context.player.board:
            return
        stinger = game._entity("TLC_630t", created_by=context.card.card_id)
        destination = game._add_generated(context.player, stinger)
        game._event(
            "gorishi_stinger", player=context.player.index,
            source=context.card.entity_id, card=stinger.card_id,
            destination=destination,
        )


@dataclass(frozen=True)
class NatureHeldBuffDraw:
    def execute(self, game: Any, context: RuleContext) -> None:
        nature_held = any(
            card.definition.spell_school == "NATURE"
            for card in context.player.hand
        )
        if nature_held:
            context.card.attack_delta += 1
            context.card.health_delta += 1
            game._draw(context.player)


@dataclass(frozen=True)
class DestroyEnemyLocation:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_entity is None:
            raise ValueError("enemy location target is required")
        owner = game.players[context.action.target_player]
        location = next((loc for loc in owner.locations
                         if loc.entity_id == context.action.target_entity), None)
        if location is None:
            raise ValueError("location target is no longer present")
        owner.locations.remove(location)
        game._location_deathrattle(owner, location)
        game._event("destroy_enemy_location", player=context.player.index,
                    source=context.card.card_id, target=location.entity_id)


@dataclass(frozen=True)
class ReopenLocationWithRandomMinionDeathrattle:
    """Welcome Home!: reopen a friendly location and grant its Deathrattle."""

    cost: int = 3

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_entity is None:
            raise ValueError("friendly location target is required")
        location = next(
            (item for item in context.player.locations
             if item.entity_id == context.action.target_entity),
            None,
        )
        if location is None:
            raise ValueError("location target is no longer present")
        location.cooldown = 0
        location.random_minion_deathrattle_cost = self.cost
        game._event(
            "welcome_home_reopen", player=context.player.index,
            source=context.card.card_id, target=location.entity_id,
            summon_cost=self.cost,
        )


@dataclass(frozen=True)
class BestInShell:
    def execute(self, game: Any, context: RuleContext) -> None:
        SummonWithTaunt("SW_429t", count=2).execute(game, context)


@dataclass(frozen=True)
class CrystalTenderBattlecry:
    def execute(self, game: Any, context: RuleContext) -> None:
        opponent = game.players[1 - context.player.index]
        gained = max(0, opponent.max_mana - context.player.max_mana)
        gained = min(gained, 10 - context.player.max_mana)
        context.player.max_mana += gained
        context.player.mana += gained
        game._event("crystal_tender_mana", player=context.player.index,
                    source=context.card.card_id, amount=gained)


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
            # Legal-action generation only exposes friendly Wisps.  A stale
            # information-set branch can still retain a previous entity id;
            # it must fizzle rather than abort the entire simulation.
            game._event("divination_stale_target", player=context.player.index,
                        source=context.card.entity_id, target=None)
            return
        try:
            target = game._find_minion(context.player.index, context.action.target_entity)
        except ValueError:
            game._event("divination_stale_target", player=context.player.index,
                        source=context.card.entity_id,
                        target=context.action.target_entity)
            return
        if target.definition.name.casefold() != "wisp":
            game._event("divination_invalid_non_wisp_target", player=context.player.index,
                        source=context.card.entity_id, target=target.entity_id)
            return
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


def _advance_location(game: Any, context: RuleContext, next_card_id: str | None) -> None:
    """Transform the exact Location that supplied a staged time effect.

    The Location object persists across the transformation, retaining its
    durability and the normal two-turn cooldown applied by ``_use_location``.
    This deliberately happens before that common cooldown code so every Past
    -> Present -> Future chain obeys the ordinary Location timing rules.
    """

    if next_card_id is None or context.action is None:
        return
    location = next(
        (item for item in context.player.locations if item.entity_id == context.action.source),
        None,
    )
    if location is None:
        return
    previous = location.card_id
    location.card_id = next_card_id
    game._event(
        "location_advance", player=context.player.index, source=location.entity_id,
        previous=previous, current=next_card_id,
    )


@dataclass(frozen=True)
class BuffLocationTargetAndAdvance:
    attack: int
    health: int
    next_card_id: str | None = None
    divine_shield: bool = False
    deathrattle_damage_enemy_hero: int = 0

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player != context.player.index:
            raise ValueError("friendly minion target is required")
        target = game._find_minion(context.player.index, context.action.target_entity)
        target.attack_delta += self.attack
        target.health_delta += self.health
        if self.divine_shield:
            target.divine_shield = True
            target.divine_shield_hits = max(1, target.divine_shield_hits)
        target.deathrattle_damage_enemy_hero += self.deathrattle_damage_enemy_hero
        _advance_location(game, context, self.next_card_id)


@dataclass(frozen=True)
class SummonRandomDragonMinCostAndAdvance:
    min_cost: int
    next_card_id: str | None

    def execute(self, game: Any, context: RuleContext) -> None:
        SummonRandomDragonMinCost(self.min_cost).execute(game, context)
        _advance_location(game, context, self.next_card_id)


@dataclass(frozen=True)
class OfferDragonSummonLocation:
    """Discover a Dragon, summon it, then optionally advance/copy it."""

    min_cost: int
    next_card_id: str | None = None
    add_copy: bool = False

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = sorted(
            card_id for card_id, definition in game.card_defs.items()
            if card_id in game.executable_card_ids
            and definition.card_type == "MINION"
            and "DRAGON" in definition.races
            and definition.cost >= self.min_cost
        )
        if not candidates:
            return
        game._offer_discover(
            context.player, candidates, dark_gift=False,
            after_pick="time_location_dragon", source_card_id=context.card.card_id,
        )
        game.pending_choice["location_entity"] = context.action.source if context.action else None
        game.pending_choice["location_advance_to"] = self.next_card_id
        game.pending_choice["location_add_copy"] = self.add_copy


@dataclass(frozen=True)
class DamageLocationEnemyMinionAndAdvance:
    amount: int
    next_card_id: str | None = None
    excess_to_hero: bool = False
    lowest_health: bool = False

    def execute(self, game: Any, context: RuleContext) -> None:
        enemy = game.players[1 - context.player.index]
        candidates = [
            minion for minion in enemy.board
            if minion.health > 0 and minion.dormant_turns == 0
        ]
        if candidates:
            if self.lowest_health:
                minimum = min(minion.health for minion in candidates)
                candidates = [minion for minion in candidates if minion.health == minimum]
            target = game.rng.choice(candidates)
            before = target.health
            game._damage_minion(enemy.index, target, self.amount, context.card)
            excess = max(0, self.amount - before)
            if self.excess_to_hero and excess:
                game._damage_hero(enemy, excess, context.card)
            game._resolve_deaths()
            game._event(
                "time_location_damage", player=context.player.index,
                source=context.card.card_id, target=target.entity_id,
                amount=self.amount, excess=excess if self.excess_to_hero else 0,
                lowest_health=self.lowest_health,
            )
        _advance_location(game, context, self.next_card_id)


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
class IncreaseLeylinePower:
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
class ReduceLeylineCosts:
    """Apply a persistent discount only to the three Leyline cards."""

    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.leyline_cost_reduction = max(
            0, int(getattr(context.player, "leyline_cost_reduction", 0))
        ) + max(0, self.amount)
        game._event(
            "leyline_cost_reduction", player=context.player.index,
            source=context.card.card_id, amount=self.amount,
            total=context.player.leyline_cost_reduction,
        )


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
class OfferWatfinDiscover:
    """Discover a Standard minion and mark one option as suspicious.

    Watfin's “wrong printing” is a hidden per-offer property in the client.
    The simulator keeps that property on the offered CardInstance and in the
    pending choice, so replay/search branches cannot accidentally re-roll it
    when the player makes a selection.
    """

    def execute(self, game: Any, context: RuleContext) -> None:
        pool = game._standard_collectible_minion_ids()
        game._offer_discover(
            context.player, pool, False, repeats=1,
            after_pick="watfin", source_card_id=context.card.card_id,
            source_entity_id=context.card.entity_id,
        )
        pending = game.pending_choice
        if pending is None or not pending.get("options"):
            return
        suspicious = game.rng.choice(pending["options"])
        suspicious.watfin_suspicious = True
        pending["watfin_suspicious_entity"] = suspicious.entity_id
        game._event(
            "watfin_suspicious_option", player=context.player.index,
            source=context.card.card_id, entity=suspicious.entity_id,
            card=suspicious.card_id,
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
    map_followup: bool = False

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
class OfferIvoryKnightDiscover:
    """Ivory Knight's spell Discover with its chosen-cost heal callback."""

    def execute(self, game: Any, context: RuleContext) -> None:
        game._offer_spell_discover(
            context.player, source_card_id=context.card.card_id
        )
        if game.pending_choice is not None:
            game.pending_choice["ivory_heal"] = True


@dataclass(frozen=True)
class OfferTypeDiscover:
    """Discover three executable cards of one card type."""

    card_type: str

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [
            card_id for card_id, definition in game.card_defs.items()
            if card_id in game.executable_card_ids
            and definition.card_type == self.card_type
        ]
        game._offer_discover(
            context.player, candidates, False,
            source_card_id=context.card.card_id,
        )


@dataclass(frozen=True)
class OfferClassSpellDiscover:
    """Discover a spell belonging to the requested class."""

    card_class: str

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [
            card_id for card_id, definition in game.card_defs.items()
            if card_id in game.executable_card_ids
            and definition.card_type == "SPELL"
            and (
                definition.card_class == self.card_class
                or self.card_class in getattr(definition, "classes", ())
            )
        ]
        game._offer_discover(
            context.player, candidates, False,
            source_card_id=context.card.card_id,
        )


@dataclass(frozen=True)
class OfferSpellDiscoverHealthCost:
    """Blood Draw: discovered spells cost Health instead of Mana this turn."""

    def execute(self, game: Any, context: RuleContext) -> None:
        game._offer_spell_discover(
            context.player, source_card_id=context.card.card_id
        )
        if game.pending_choice is None:
            return
        for option in game.pending_choice["options"]:
            option.costs_health_expiry_turn = game.turn
        game._event(
            "health_cost_spell_discover", player=context.player.index,
            source=context.card.card_id,
            options=[option.card_id for option in game.pending_choice["options"]],
        )


@dataclass(frozen=True)
class OfferContrabandBeastDiscover:
    """Discover an executable Beast, including Beasts from other classes."""

    def execute(self, game: Any, context: RuleContext) -> None:
        pool = [
            card_id for card_id, definition in game.card_defs.items()
            if card_id in game.executable_card_ids
            and definition.card_type == "MINION"
            and "BEAST" in definition.races
        ]
        game._offer_discover(
            context.player, pool, dark_gift=False,
            source_card_id=context.card.card_id,
        )
        if game.pending_choice is not None:
            for option in game.pending_choice["options"]:
                option.cost_delta -= 3


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
    past: bool = False

    def execute(self, game: Any, context: RuleContext) -> None:
        if self.spend_corpses:
            if context.player.corpses < self.spend_corpses:
                return
            context.player.corpses -= self.spend_corpses
        candidate_ids = (
            _past_ids(game, card_type="MINION", race=self.race,
                      min_cost=self.min_cost, collectible_only=True)
            if self.past else list(game.card_defs)
        )
        pool = [
            card_id for card_id in candidate_ids
            if card_id in game.executable_card_ids
            and game.card_defs[card_id].card_type == "MINION"
            and (not self.past or game.card_defs[card_id].card_set != "TIME_TRAVEL")
            and (self.rarity is None or game.card_defs[card_id].rarity == self.rarity)
            and (self.race is None or self.race in game.card_defs[card_id].races)
            and (self.min_cost is None or game.card_defs[card_id].cost >= self.min_cost)
            and (
                self.mechanic is None
                or self.mechanic in game.card_defs[card_id].mechanics
                or self.mechanic.casefold() in game.card_defs[card_id].text.casefold()
            )
            and (
                not self.mechanics
                or any(
                    m in game.card_defs[card_id].mechanics
                    or m.casefold() in game.card_defs[card_id].text.casefold()
                    for m in self.mechanics
                )
            )
        ]
        game._offer_discover(
            context.player, pool, dark_gift=True,
            source_card_id=context.card.card_id,
        )
        if game.pending_choice is not None:
            game.pending_choice["dark_gift_cost_delta"] = self.cost_delta


@dataclass(frozen=True)
class OfferDemonDiscoverMinCost:
    """Discover an executable Demon with at least the requested cost."""

    min_cost: int

    def execute(self, game: Any, context: RuleContext) -> None:
        pool = [
            card_id for card_id, definition in game.card_defs.items()
            if card_id in game.executable_card_ids
            and definition.card_type == "MINION"
            and "DEMON" in definition.races
            and definition.cost >= self.min_cost
        ]
        game._offer_discover(
            context.player, pool, dark_gift=False,
            source_card_id=context.card.card_id,
        )
        if not any(
            card.definition.card_type == "MINION"
            for card in context.player.deck
        ):
            context.player.next_minion_cost_reduction = 99
            game._event(
                "eternal_hold_discount_armed", player=context.player.index,
                source=context.card.card_id,
            )


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
    require_no_neutral: bool = False
    cost_delta: int = 0

    def execute(self, game: Any, context: RuleContext) -> None:
        if self.require_no_neutral and any(
            card.definition.card_class == "NEUTRAL"
            for card in context.player.deck
        ):
            return
        game._add_random_executable_class_card(
            context.player, card_class=self.card_class,
            source_card_id=context.card.card_id, cost_delta=self.cost_delta,
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
class CostMinusEnemyMinions:
    """Dynamic spell cost reduction from the opponent's live board."""

    def adjustment(self, game: Any, player: Any, card: Any) -> int:
        opponent = game.players[1 - player.index]
        return -len(opponent.board)


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
class AddMinionsMatchingSourceAttack:
    """Al'Akir: add two minions whose printed cost equals this minion's attack."""

    count: int = 2

    def execute(self, game: Any, context: RuleContext) -> None:
        cost = context.card.attack
        candidates = [
            card_id for card_id, definition in game.card_defs.items()
            if card_id in game.executable_card_ids
            and definition.card_type == "MINION"
            and definition.cost == cost
        ]
        for _ in range(self.count):
            if not candidates:
                break
            card = game._entity(
                game.rng.choice(sorted(candidates)),
                created_by=context.card.card_id,
            )
            card.cost_delta = 1 - card.definition.cost
            game._add_generated(context.player, card)


@dataclass(frozen=True)
class DrawTwoGainChargeIfMinions:
    def execute(self, game: Any, context: RuleContext) -> None:
        drawn: list[Any] = []
        for _ in range(2):
            before = len(context.player.hand)
            game._draw(context.player)
            if len(context.player.hand) > before:
                drawn.append(context.player.hand[-1])
        if len(drawn) == 2 and all(card.definition.card_type == "MINION" for card in drawn):
            context.card.charge = True
            game._event(
                "getaway_hogdriver_charge", player=context.player.index,
                source=context.card.card_id,
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
class DamageAllOtherMinions:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        amount = game._spell_effect_amount(context.player, context.card, self.amount)
        for owner in game.players:
            for target in list(owner.board):
                if target.entity_id != context.card.entity_id:
                    game._damage_minion(owner.index, target, amount, context.card)
        game._resolve_deaths()


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
class DeathchillerAfterSpell:
    """Deathchiller: after a spell, ping two random enemy characters."""

    def execute(self, game: Any, context: RuleContext) -> None:
        DamageRandomEnemyCharacters(1, 2).execute(game, context)


@dataclass(frozen=True)
class DiscoverUnholyIfUndeadDied:
    """Necrotic Mortician's conditional Unholy Rune Discover."""

    def execute(self, game: Any, context: RuleContext) -> None:
        if getattr(context.player, "undead_died_after_last_turn", False):
            game._offer_rune_discover(
                context.player, rune="unholy", source_card_id=context.card.card_id
            )
            game._event(
                "necrotic_mortician_discover", player=context.player.index,
                source=context.card.entity_id, rune="unholy",
            )


@dataclass(frozen=True)
class ThassarianRandomEnemyDamage:
    """Thassarian's Battlecry and Deathrattle share one random ping."""

    def execute(self, game: Any, context: RuleContext) -> None:
        DamageRandomEnemyCharacters(2, 1).execute(game, context)


@dataclass(frozen=True)
class TimestopEffect:
    """Timestop: damage the opposing hero and freeze two random minions."""

    def execute(self, game: Any, context: RuleContext) -> None:
        game._damage_hero(game.players[1 - context.player.index], 3, context.card)
        candidates = game._random_enemy_minions(context.player.index)
        chosen = game.rng.sample(candidates, min(2, len(candidates)))
        for minion in chosen:
            minion.frozen_turn = game.turn
        game._event(
            "timestop", player=context.player.index,
            source=context.card.card_id, frozen=[m.entity_id for m in chosen],
        )


@dataclass(frozen=True)
class BoneFlurryEffect:
    """Bone Flurry gains a second volley after a friendly death this turn."""

    def execute(self, game: Any, context: RuleContext) -> None:
        amount = 3 + (3 if getattr(context.player, "friendly_minions_died_this_turn", 0) else 0)
        DamageRandomSplitEnemyCharacters(amount).execute(game, context)


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
        resolved_targets = []
        for _ in range(repeats):
            # Each volley is a distinct damage resolution.  A minion killed
            # by an earlier volley has left the board and is not a legal
            # target for the following one.
            targets = game._random_enemy_characters(context.player.index)
            for target in targets:
                game._deal_to_target(context.player.index, target, amount, context.card)
                resolved_targets.append(target)
            game._resolve_deaths()
        game._event(
            "all_enemy_damage", player=context.player.index,
            source=context.card.card_id, amount=amount, repeats=repeats,
            targets=resolved_targets,
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
class SummonNecronursesAttackTarget:
    """Emergency Surgery: summon four Lifesteal attackers into one target."""

    count: int = 4

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("enemy minion target is required")
        target_player = context.action.target_player
        target_entity = context.action.target_entity
        target = game._find_minion(target_player, target_entity)
        summoned = []
        for _ in range(self.count):
            if len(context.player.board) + len(context.player.locations) >= 7:
                break
            nurse = game._entity("JAIL_454t", created_by=context.card.card_id)
            nurse.summoned_turn = game.turn
            game._summon(context.player, nurse)
            summoned.append(nurse.entity_id)
            if target not in game.players[target_player].board or target.health <= 0:
                break
            game._forced_minion_attack(
                context.player.index, nurse, target_player, target
            )
        game._event(
            "necronurse_surgery", player=context.player.index,
            source=context.card.card_id, target=target_entity, summoned=summoned,
        )


@dataclass(frozen=True)
class RevealSpellThenSplitEnemyMinions:
    threshold: int
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        spells = [
            card for card in context.player.deck
            if card.definition.card_type == "SPELL"
        ]
        if not spells:
            game._event(
                "reveal_spell", player=context.player.index,
                source=context.card.card_id, card=None, triggered=False,
            )
            return
        revealed = game.rng.choice(spells)
        triggered = revealed.definition.cost >= self.threshold
        game._event(
            "reveal_spell", player=context.player.index,
            source=context.card.card_id, card=revealed.card_id,
            cost=revealed.definition.cost, triggered=triggered,
        )
        if not triggered:
            return
        enemy = game.players[1 - context.player.index]
        targets = []
        for _ in range(self.amount):
            living = [minion for minion in enemy.board if minion.health > 0]
            if not living:
                break
            target = game.rng.choice(living)
            game._damage_minion(enemy.index, target, 1, context.card)
            targets.append(target.entity_id)
        game._resolve_deaths()
        game._event(
            "reveal_spell_split_damage", player=context.player.index,
            source=context.card.card_id, amount=self.amount, targets=targets,
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
            # Returning the spell is a zone move, not creation of a new
            # entity.  Preserve the original instance so trackers and
            # generated-card identity remain stable across the round trip.
            context.player.hand.append(context.card)
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
class UnlockOverloadedMana:
    def execute(self, game: Any, context: RuleContext) -> None:
        unlocked = context.player.locked_mana
        context.player.locked_mana = 0
        context.player.mana = min(context.player.max_mana, context.player.mana + unlocked)
        game._event("overload_unlocked", player=context.player.index,
                    source=context.card.card_id, amount=unlocked)


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
class SetCoinReplacement:
    coin_id: str

    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.coin_replacement_id = self.coin_id
        game._event(
            "aya_coin_choice", player=context.player.index,
            source=context.card.card_id, coin=self.coin_id,
        )


@dataclass(frozen=True)
class AyaCoinChoice:
    def execute(self, game: Any, context: RuleContext) -> None:
        game.pending_choice = {
            "kind": "RULE_CHOICE", "player": context.player.index,
            "card": context.card, "action": context.action,
            "options": (
                ("Jade Coin", (SetCoinReplacement("JAIL_504t"),)),
                ("Grimy Coin", (SetCoinReplacement("JAIL_504t2"),)),
                ("Kabal Coin", (SetCoinReplacement("JAIL_504t3"),)),
            ),
        }


@dataclass(frozen=True)
class HolmesInspect:
    card_id: str

    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.holmes_target_card_id = self.card_id
        context.player.holmes_watch_turn = game.turn + 1
        game._event(
            "holmes_investigate", player=context.player.index,
            source=context.card.card_id, inspected=self.card_id,
            watch_turn=context.player.holmes_watch_turn,
        )


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
class DestroyMinionsByAttackAtMost:
    maximum: int

    def execute(self, game: Any, context: RuleContext) -> None:
        for player in game.players:
            for minion in list(player.board):
                if minion.dormant_turns <= 0 and minion.attack <= self.maximum:
                    minion.damage = minion.max_health
        game._resolve_deaths()


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
                # Dormant minions are not valid targets for destroy effects;
                # keep the same immunity used by targeted destroy rules.
                if minion.dormant_turns <= 0:
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
class SetOtherMinionsStat:
    """Set one stat on every minion except the resolving source minion."""

    stat: str
    value: int

    def execute(self, game: Any, context: RuleContext) -> None:
        for player in game.players:
            for minion in player.board:
                if minion.entity_id == context.card.entity_id:
                    continue
                if self.stat == "attack":
                    minion.attack_delta += self.value - minion.attack
                elif self.stat == "health":
                    minion.health_delta += self.value - minion.max_health
                    minion.damage = min(minion.damage, max(0, minion.max_health - self.value))
                else:
                    raise ValueError(f"unsupported minion stat: {self.stat}")
        if self.stat == "health":
            game._resolve_deaths()


@dataclass(frozen=True)
class GiveHeroPoisonousThisTurn:
    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.hero_poisonous_until_turn = game.turn


@dataclass(frozen=True)
class SetDeathrattleDamageAllEnemies:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        context.card.deathrattle_damage_all_enemies = self.amount


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
        # Cho'gall's Arms/Soldiers replace the adjacent destruction with a
        # random minion destroyed from the enemy deck while Cho'gall lives.
        # The parent link prevents another copy's Arm from changing targets.
        cho_gall = next(
            (
                minion for minion in player.board
                if minion.card_id == "CATA_726"
                and not minion.silenced
                and minion.dormant_turns == 0
                and minion.health > 0
                and context.card.colossal_parent_entity == minion.entity_id
            ),
            None,
        )
        if cho_gall is not None:
            enemy = game.players[1 - player.index]
            candidates = [
                card for card in enemy.deck
                if card.definition.card_type == "MINION"
            ]
            if candidates:
                destroyed = game.rng.choice(candidates)
                enemy.deck.remove(destroyed)
                game._event(
                    "chogall_deck_destroy", player=player.index,
                    source=context.card.entity_id, card=destroyed.card_id,
                )
                context.card.attack_delta += context.card.herald_power
                context.card.health_delta += context.card.herald_power
            return
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
class SetHeroPowerDirect:
    """Swap the active Hero Power without marking it as an Imbue power."""

    card_id: str | None

    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.hero_power_id = self.card_id
        game._event(
            "hero_power_swap", player=context.player.index,
            source=context.card.card_id, hero_power=self.card_id,
        )


@dataclass(frozen=True)
class SoulImmolationSpell:
    """Install or upgrade the Demon Hunter Collapsing Star Hero Power."""

    hero_power_id: str = "JAIL_EVENT_101hp"

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.player.hero_power_id == self.hero_power_id:
            context.player.collapsing_star_damage = max(
                2, int(getattr(context.player, "collapsing_star_damage", 2))
            ) + 1
            upgraded = True
        else:
            context.player.collapsing_star_damage = 2
            upgraded = False
        context.player.hero_power_id = self.hero_power_id
        # Soul Immolation is a direct replacement, not an Imbue effect.  Do
        # not leave an older temporary/imbued power scheduled for restoration.
        context.player.imbued_hero_power_id = None
        game._event(
            "soul_immolation", player=context.player.index,
            source=context.card.card_id, hero_power=self.hero_power_id,
            damage=context.player.collapsing_star_damage, upgraded=upgraded,
        )


@dataclass(frozen=True)
class CollapsingStarHeroPower:
    """Deal upgraded damage to one random enemy character."""

    def execute(self, game: Any, context: RuleContext) -> None:
        amount = max(2, int(getattr(context.player, "collapsing_star_damage", 2)))
        DamageRandomEnemyCharacters(amount, 1).execute(game, context)


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
class DeadlyBribeSpell:
    """Destroy a chosen enemy minion and pay the printed Coin costs.

    The normal play path has already populated ``combo_active`` before the
    spell hook is dispatched.  Resolving the death before generating Coins
    also preserves the ordinary Hearthstone ordering for deathrattles.
    """

    def execute(self, game: Any, context: RuleContext) -> None:
        DestroyActionTarget().execute(game, context)
        game._resolve_deaths()
        AddToHand("GAME_005", side="opponent").execute(game, context)
        if context.card.combo_active:
            AddToHand("GAME_005").execute(game, context)
        game._event(
            "deadly_bribe", player=context.player.index,
            source=context.card.card_id, combo=context.card.combo_active,
        )


@dataclass(frozen=True)
class DesperateBribeSpell:
    """Resolve Desperate Bribe without treating transformations as summons.

    The two summons for each side happen first.  The caster's resulting board
    (including its newly summoned minions) is then transformed slot by slot
    into random minions with exactly one higher *printed* cost.  A transform
    retains entity identity and summoning sickness, but not the old minion's
    stats, enchantments, Battlecry, or Deathrattle.
    """

    def execute(self, game: Any, context: RuleContext) -> None:
        for player in game.players:
            for _ in range(2):
                game._summon_random_executable_minion(
                    player, source_card_id=context.card.card_id, cost=2,
                    collectible_standard=True,
                )

        transformed: list[dict[str, Any]] = []
        for target in list(context.player.board):
            cost = target.definition.cost + 1
            candidates = sorted(
                card_id for card_id, definition in game.card_defs.items()
                if card_id in game.executable_card_ids
                and definition.card_type == "MINION"
                and definition.cost == cost
                and game._is_standard_collectible(definition)
            )
            if not candidates:
                continue
            replacement = game._entity(
                game.rng.choice(candidates), created_by=context.card.card_id
            )
            replacement.entity_id = target.entity_id
            replacement.summoned_turn = target.summoned_turn
            replacement.attacks_this_turn = target.attacks_this_turn
            context.player.board[context.player.board.index(target)] = replacement
            transformed.append({
                "entity": target.entity_id,
                "previous": target.card_id,
                "replacement": replacement.card_id,
                "cost": cost,
            })
        game._event(
            "desperate_bribe", player=context.player.index,
            source=context.card.card_id, transformed=transformed,
        )


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
        fandral_active = any(
            minion.card_id == "CORE_OG_044"
            and not minion.silenced
            and minion.dormant_turns == 0
            for minion in context.player.board
        )
        if fandral_active:
            for _label, effects in self.options:
                for effect in effects:
                    effect.execute(game, context)
            game._event(
                "choose_one_combined", player=context.player.index,
                card=context.card.card_id,
                options=[label for label, _effects in self.options],
            )
            return
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
class IfQuickdraw:
    """Run the nested effects when the source card was drawn this turn."""

    effects: tuple[Effect, ...]

    def execute(self, game: Any, context: RuleContext) -> None:
        if getattr(context.card, "drawn_turn", -1) == game.turn:
            for effect in self.effects:
                effect.execute(game, context)


@dataclass(frozen=True)
class SetDormantActionTarget:
    turns: int = 2
    buff_friendly_demon: bool = False

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        target = game._find_minion(context.action.target_player,
                                   context.action.target_entity)
        if (self.buff_friendly_demon and
                context.action.target_player == context.player.index and
                target.has_race("DEMON")):
            target.attack_delta += 3
            target.health_delta += 3
        else:
            target.dormant_turns = self.turns
        game._event("set_dormant", player=context.player.index,
                    source=context.card.card_id, target=target.entity_id,
                    turns=(0 if target.dormant_turns == 0 else self.turns))


@dataclass(frozen=True)
class GrantTemporaryImmune:
    """Grant immunity through the current turn."""

    def execute(self, game: Any, context: RuleContext) -> None:
        context.card.immune = True
        context.card.temporary_immune_expiry_turn = game.turn + 1
        game._event("quickdraw_immune", player=context.player.index,
                    source=context.card.card_id, entity=context.card.entity_id)


@dataclass(frozen=True)
class RefreshMana:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        before = context.player.mana
        context.player.mana = min(context.player.max_mana,
                                  context.player.mana + self.amount)
        game._event("refresh_mana", player=context.player.index,
                    source=context.card.card_id,
                    amount=context.player.mana - before)


@dataclass(frozen=True)
class QuickdrawCopyBattlecry:
    """Azerite Chain Gang: copy once for Battlecry and once more for Quickdraw."""

    def execute(self, game: Any, context: RuleContext) -> None:
        count = 2 if getattr(context.card, "drawn_turn", -1) == game.turn else 1
        for _ in range(count):
            if len(context.player.board) + len(context.player.locations) >= 7:
                break
            copy = context.card.clone(game.next_entity_id)
            game.next_entity_id += 1
            copy.damage = 0
            copy.summoned_turn = game.turn
            copy.created_by = context.card.card_id
            game._summon(context.player, copy)
        game._event("quickdraw_copy_battlecry", player=context.player.index,
                    source=context.card.card_id, count=count)


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
class BuffActionTargetIfDamaged:
    """Apply a buff only to a minion that already has damage."""

    attack: int = 0
    health: int = 0

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("damaged minion target is required")
        target = game._find_minion(
            context.action.target_player, context.action.target_entity
        )
        if target.damage <= 0:
            raise ValueError("target must already be damaged")
        target.attack_delta += self.attack
        target.health_delta += self.health


@dataclass(frozen=True)
class BuffActionTargetWithLifesteal:
    attack: int = 0
    health: int = 0

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("friendly minion target is required")
        target = game._find_minion(
            context.action.target_player, context.action.target_entity
        )
        target.attack_delta += self.attack
        target.health_delta += self.health
        target.lifesteal = True


@dataclass(frozen=True)
class SetAllMinionStatsLikeTarget:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player != context.player.index:
            raise ValueError("friendly minion target is required")
        target = game._find_minion(context.player.index, context.action.target_entity)
        for player in game.players:
            for minion in player.board:
                minion.attack_delta += target.attack - minion.attack
                minion.health_delta += target.max_health - minion.max_health
                minion.damage = min(minion.damage, max(0, minion.max_health))
        game._event("judgment_set_stats", player=context.player.index,
                    source=context.card.card_id, target=target.entity_id,
                    attack=target.attack, health=target.max_health)


@dataclass(frozen=True)
class DestroyOtherMinionsDrawAndRefresh:
    def execute(self, game: Any, context: RuleContext) -> None:
        player = context.player
        victims = [m for m in player.board if m.entity_id != context.card.entity_id]
        for minion in victims:
            minion.damage = minion.max_health
        game._resolve_deaths()
        destroyed = sum(
            corpse.entity_id in {m.entity_id for m in victims}
            for corpse in player.dead_minions
        )
        for _ in range(destroyed):
            game._draw(player)
            player.mana = min(player.max_mana, player.mana + 1)
        game._event("sawbones_destroyed_others", player=player.index,
                    source=context.card.card_id, destroyed=destroyed)


@dataclass(frozen=True)
class TriggerFriendlyDeathrattle:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player != context.player.index:
            raise ValueError("friendly minion target is required")
        target = game._find_minion(context.player.index, context.action.target_entity)
        if target.silenced or "DEATHRATTLE" not in target.definition.mechanics:
            raise ValueError("target must have a Deathrattle")
        game._deathrattle(context.player, target)
        game._event("trigger_friendly_deathrattle", player=context.player.index,
                    source=context.card.card_id, target=target.entity_id)


@dataclass(frozen=True)
class CastRandomMageSecretsIfSpellCast:
    count: int = 2

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.player.spells_cast_this_turn <= 0:
            return
        candidates = [
            card_id for card_id in game.executable_card_ids
            if card_id in game.card_defs
            and game.card_defs[card_id].card_type == "SPELL"
            and game.card_defs[card_id].card_class == "MAGE"
            and "SECRET" in game.card_defs[card_id].mechanics
        ]
        for _ in range(self.count):
            if not candidates or len(context.player.secrets) >= 7:
                break
            secret = game._entity(
                game.rng.choice(sorted(candidates)),
                created_by=context.card.card_id,
            )
            game._arm_secret(context.player, secret)
        game._event("tricksy_improviser_secrets", player=context.player.index,
                    source=context.card.card_id, count=self.count)


@dataclass(frozen=True)
class CodeVioletSummon:
    def execute(self, game: Any, context: RuleContext) -> None:
        # The spell itself is already included in the counter, hence three
        # other spells means at least four total spells this turn.
        count = 2 if context.player.spells_cast_this_turn >= 4 else 1
        SummonRandomExecutableMinion(cost=8, count=count).execute(game, context)
        game._event("code_violet_summon", player=context.player.index,
                    source=context.card.card_id, count=count)


@dataclass(frozen=True)
class WantedPosterDiscover:
    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [
            card_id for card_id in game.executable_card_ids
            if card_id in game.card_defs
            and game.card_defs[card_id].card_type == "MINION"
            and game.card_defs[card_id].cost >= 5
        ]
        game._offer_discover(
            context.player, candidates, dark_gift=False,
            source_card_id=context.card.card_id,
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
class BuffBeastsEverywhere:
    attack: int
    health: int

    def execute(self, game: Any, context: RuleContext) -> None:
        affected: list[int] = []
        for zone_name in ("hand", "deck", "board"):
            for card in getattr(context.player, zone_name):
                if card.definition.card_type == "MINION" and card.has_race("BEAST"):
                    card.attack_delta += self.attack
                    card.health_delta += self.health
                    affected.append(card.entity_id)
        game._event("buff_beasts_everywhere", player=context.player.index,
                    source=context.card.card_id, affected=affected)


@dataclass(frozen=True)
class SetHeroHealth:
    health: int

    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.max_health = max(context.player.max_health, self.health)
        context.player.health = self.health
        game._event("set_hero_health", player=context.player.index,
                    source=context.card.card_id, health=self.health)


@dataclass(frozen=True)
class DamageMinionAndSameRace:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("minion target is required")
        target = game._find_minion(context.action.target_player, context.action.target_entity)
        race = target.definition.race or (target.definition.races[0] if target.definition.races else "")
        enemy = game.players[context.action.target_player]
        targets = [m for m in enemy.board if m.health > 0 and m.dormant_turns == 0
                   and (m is target or (race and m.has_race(race)))]
        for minion in targets:
            game._damage_minion(enemy.index, minion, self.amount, context.card)
        game._resolve_deaths()


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
class BuffFriendlyMinionsAndElusive:
    """Anti-Magic Shell: +1/+1 and targeted-spell immunity to all allies."""

    attack: int = 1

    def execute(self, game: Any, context: RuleContext) -> None:
        affected = []
        for minion in context.player.board:
            minion.attack_delta += self.attack
            minion.health_delta += self.attack
            minion.elusive = True
            affected.append(minion.entity_id)
        game._event("anti_magic_shell", player=context.player.index,
                    source=context.card.card_id, affected=affected)


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
class GrantKeyword:
    """Grant one printed keyword to the card that caused this trigger."""

    keyword: str

    def execute(self, game: Any, context: RuleContext) -> None:
        setattr(context.card, self.keyword, True)
        if self.keyword == "divine_shield":
            context.card.divine_shield_hits = max(1, context.card.divine_shield_hits)
        game._event("grant_keyword", player=context.player.index,
                    source=context.card.card_id, keyword=self.keyword,
                    entity=context.card.entity_id)


@dataclass(frozen=True)
class FlitterwingEndTurn:
    """Iridescent Flitterwing buffs every other friendly minion."""

    def execute(self, game: Any, context: RuleContext) -> None:
        affected = []
        for minion in context.player.board:
            if minion.entity_id == context.card.entity_id or minion.dormant_turns > 0:
                continue
            minion.attack_delta += 1
            minion.health_delta += 1
            affected.append(minion.entity_id)
        game._event("flitterwing_end_turn", player=context.player.index,
                    source=context.card.entity_id, affected=affected)


@dataclass(frozen=True)
class AddRandomDragon:
    """Add an executable Standard Dragon to hand."""

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = sorted(
            card_id for card_id, definition in game.card_defs.items()
            if card_id in game.executable_card_ids
            and definition.card_type == "MINION"
            and "DRAGON" in definition.races
        )
        if not candidates:
            return
        card = game._entity(game.rng.choice(candidates), created_by=context.card.card_id)
        destination = game._add_generated(context.player, card)
        game._event("random_dragon", player=context.player.index,
                    source=context.card.card_id, card=card.card_id,
                    destination=destination)


@dataclass(frozen=True)
class SummonRandomDragonMinCost:
    """Summon a random executable Dragon at or above a printed cost."""

    min_cost: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if len(context.player.board) + len(context.player.locations) >= 7:
            return
        candidates = sorted(
            card_id for card_id, definition in game.card_defs.items()
            if card_id in game.executable_card_ids
            and definition.card_type == "MINION"
            and "DRAGON" in definition.races
            and definition.cost >= self.min_cost
        )
        if not candidates:
            return
        minion = game._entity(
            game.rng.choice(candidates), created_by=context.card.card_id
        )
        minion.summoned_turn = game.turn
        game._summon(context.player, minion)
        game._event(
            "random_dragon_summoned", player=context.player.index,
            source=context.card.card_id, card=minion.card_id,
            entity=minion.entity_id, min_cost=self.min_cost,
        )


@dataclass(frozen=True)
class DiscoverNatureSpell:
    """Farseer Wo's post-cast Discover from the historical Nature pool."""

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = _past_ids(
            game, card_type="SPELL", spell_school="NATURE",
            collectible_only=True,
        )
        if candidates:
            game._offer_discover(context.player, candidates, dark_gift=False,
                                 source_card_id=context.card.card_id)


@dataclass(frozen=True)
class DiscoverQuickdrawOtherClass:
    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = sorted(
            card_id for card_id, definition in game.card_defs.items()
            if card_id in game.executable_card_ids
            and definition.card_type == "SPELL"
            and definition.card_class != context.player.card_class
            and "QUICKDRAW" in definition.mechanics
        )
        if candidates:
            game._offer_discover(context.player, candidates, dark_gift=False,
                                 source_card_id=context.card.card_id)


@dataclass(frozen=True)
class TwistedMonstrosityRotate:
    """Choose two bonus effects once, then alternate them while held."""

    def execute(self, game: Any, context: RuleContext) -> None:
        effects = ("divine_shield", "lifesteal", "poisonous", "rush",
                   "taunt", "windfury", "elusive")
        if context.card.bonus_effect_options is None:
            context.card.bonus_effect_options = tuple(game.rng.sample(effects, 2))
        options = context.card.bonus_effect_options
        active = options[0] if context.card.bonus_effect_active != options[0] else options[1]
        for keyword in effects:
            if keyword == active:
                continue
            setattr(context.card, keyword, False)
        setattr(context.card, active, True)
        context.card.bonus_effect_active = active
        game._event("twisted_monstrosity_bonus", player=context.player.index,
                    source=context.card.entity_id, effect=active,
                    options=list(options))


@dataclass(frozen=True)
class LivingParadoxBattlecry:
    """Summon two 2/1 Elusive paradoxes without replaying a Battlecry."""

    def execute(self, game: Any, context: RuleContext) -> None:
        for _ in range(2):
            if len(context.player.board) + len(context.player.locations) >= 7:
                break
            token = context.card.clone(game.next_entity_id)
            game.next_entity_id += 1
            token.attack_delta = 2 - token.definition.attack
            token.health_delta = 1 - token.definition.health
            token.damage = 0
            token.summoned_turn = game.turn
            token.created_by = context.card.card_id
            token.elusive = True
            game._summon(context.player, token)
        game._event("living_paradox_battlecry", player=context.player.index,
                    source=context.card.card_id)


@dataclass(frozen=True)
class EpochStalkerBattlecry:
    """Summon a copy of Epoch Stalker; summoned copies do not replay Battlecry."""

    def execute(self, game: Any, context: RuleContext) -> None:
        if len(context.player.board) + len(context.player.locations) >= 7:
            return
        copy = context.card.clone(game.next_entity_id)
        game.next_entity_id += 1
        copy.damage = 0
        copy.summoned_turn = game.turn
        copy.created_by = context.card.card_id
        game._summon(context.player, copy)
        game._event("epoch_stalker_copy", player=context.player.index,
                    source=context.card.card_id, entity=copy.entity_id)


@dataclass(frozen=True)
class FacelessReplicatorDeathrattle:
    """Transform the minion that dealt the lethal combat blow."""

    def execute(self, game: Any, context: RuleContext) -> None:
        killer_id = getattr(context.card, "killed_by_entity", None)
        if killer_id is None:
            return
        killer = next(
            (minion for player in game.players for minion in player.board
             if minion.entity_id == killer_id),
            None,
        )
        if killer is None:
            return
        killer.definition = game.card_defs.get("CATA_185", killer.definition)
        killer.attack_delta = 0
        killer.health_delta = 0
        killer.damage = 0
        killer.elusive = True
        killer.silenced = False
        game._event("faceless_replicator_transform", player=context.player.index,
                    source=context.card.card_id, target=killer.entity_id)


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
        dynamic = [
            card_id for card_id, definition in game.card_defs.items()
            if card_id in game.executable_card_ids
            and definition.card_type == "SPELL"
            and "shatter" in (definition.text or "").casefold()
            and not card_id.endswith("t")
        ]
        candidates = [
            card_id for card_id in self.card_ids
            if card_id in game.card_defs
            and game.card_defs[card_id].card_class != context.player.card_class
        ]
        if dynamic:
            candidates = [
                card_id for card_id in dynamic
                if game.card_defs[card_id].card_class != context.player.card_class
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
        # Khadgar's wording applies to every source which *summons* rather
        # than to played minions.  Keeping the multiplier in both standard
        # and Dormant summon primitives covers every declarative token path.
        khadgar_multiplier = 2 ** sum(
            minion.card_id == "CORE_DAL_575"
            and not minion.silenced
            and minion.dormant_turns == 0
            and minion.health > 0
            for minion in player.board
        )
        for _ in range(self.count * khadgar_multiplier):
            if len(player.board) + len(player.locations) >= 7:
                break
            minion = game._entity(self.card_id, created_by=context.card.card_id)
            minion.summoned_turn = game.turn
            game._summon(player, minion)


@dataclass(frozen=True)
class SummonIfDeckHasNoNeutral:
    card_id: str
    count: int = 1

    def execute(self, game: Any, context: RuleContext) -> None:
        if any(
            card.definition.card_class == "NEUTRAL"
            for card in context.player.deck
        ):
            return
        Summon(self.card_id, self.count).execute(game, context)


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
        # Khadgar's wording applies to every source which *summons* rather
        # than to played minions.  Keeping it here covers declarative token
        # effects without duplicating that check in every individual card.
        khadgar_multiplier = 2 ** sum(
            minion.card_id == "CORE_DAL_575"
            and not minion.silenced
            and minion.dormant_turns == 0
            and minion.health > 0
            for minion in player.board
        )
        for _ in range(self.count * khadgar_multiplier):
            if len(player.board) + len(player.locations) >= 7:
                break
            minion = game._entity(self.card_id, created_by=context.card.card_id)
            minion.summoned_turn = game.turn
            minion.dormant_turns = self.dormant_turns
            game._summon(player, minion)


@dataclass(frozen=True)
class SummonRandomDreadseed:
    """Summon one random Dormant Dreadseed from the current seed pool."""

    count: int = 1

    def execute(self, game: Any, context: RuleContext) -> None:
        # Hearthstone's Dreadseed pool has three distinct tokens with
        # different dormant durations and keywords.  Keep the pool explicit
        # so seeded simulations and audit reports remain reproducible.
        for _ in range(self.count):
            card_id = game.rng.choice(("EDR_840t", "EDR_840t1", "EDR_840t2"))
            dormant = {"EDR_840t": 2, "EDR_840t1": 1, "EDR_840t2": 3}[card_id]
            SummonDormant(card_id, dormant).execute(game, context)


@dataclass(frozen=True)
class IsorathDevour:
    def execute(self, game: Any, context: RuleContext) -> None:
        opponent = game.players[1 - context.player.index]
        context.card.devoured_cards = []
        for card in game.rng.sample(opponent.hand, min(2, len(opponent.hand))):
            opponent.hand.remove(card)
            context.card.devoured_cards.append(card)
        context.card.dormant_turns = 2
        game._event("isorath_devour", player=context.player.index,
                    source=context.card.entity_id,
                    cards=[card.card_id for card in context.card.devoured_cards])


@dataclass(frozen=True)
class IsorathReturn:
    def execute(self, game: Any, context: RuleContext) -> None:
        returned = []
        for card in list(context.card.devoured_cards):
            if len(context.player.hand) >= 10:
                break
            context.player.hand.append(card)
            returned.append(card.card_id)
        context.card.devoured_cards.clear()
        game._event("isorath_return", player=context.player.index,
                    source=context.card.entity_id, cards=returned)


@dataclass(frozen=True)
class TimewayImprison:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("enemy minion target is required")
        target = game._find_minion(context.action.target_player,
                                   context.action.target_entity)
        target.dormant_turns = 10_000
        context.card.imprisoned_entity_id = target.entity_id
        game._event("timeway_imprison", player=context.player.index,
                    source=context.card.entity_id, target=target.entity_id)


@dataclass(frozen=True)
class TimewayAwaken:
    def execute(self, game: Any, context: RuleContext) -> None:
        target_id = context.card.imprisoned_entity_id
        if target_id is None:
            return
        target = next((minion for player in game.players for minion in player.board
                       if minion.entity_id == target_id), None)
        if target is not None:
            target.dormant_turns = 0
            game._event("timeway_awaken", player=context.player.index,
                        source=context.card.entity_id, target=target.entity_id)


@dataclass(frozen=True)
class SummonRandomDormantCost:
    cost: int = 2

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [card_id for card_id, definition in game.card_defs.items()
                      if card_id in game.executable_card_ids
                      and definition.card_type == "MINION"
                      and definition.cost == self.cost
                      and ("DORMANT" in definition.mechanics or card_id.startswith("EDR_840t"))]
        if not candidates or len(context.player.board) + len(context.player.locations) >= 7:
            return
        minion = game._entity(game.rng.choice(sorted(candidates)), created_by=context.card.card_id)
        minion.summoned_turn = game.turn
        minion.dormant_turns = 2
        game._summon(context.player, minion)


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
            if card.card_id == "JAIL_732":
                # Void Blast can add the generated Void Soul directly to hand;
                # preserve the controller's current tier just like the
                # Stardust Scythe generation path does.
                card.void_soul_cost = max(1, player.void_soul_level)
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
class AddRandomLegendaryMinionDiscounted:
    """Cryofrozen Champion: add a random Legendary at one less Cost."""

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [
            card_id for card_id in game.executable_card_ids
            if card_id in game.card_defs
            and game.card_defs[card_id].card_type == "MINION"
            and game.card_defs[card_id].rarity == "LEGENDARY"
        ]
        if not candidates:
            return
        card = game._entity(game.rng.choice(sorted(candidates)), created_by=context.card.card_id)
        card.cost_delta -= 1
        game._add_generated(context.player, card)


@dataclass(frozen=True)
class FillHandRandomUndeadHealthCost:
    """Forgotten Millennium fills the hand with Undead costing Health."""

    def execute(self, game: Any, context: RuleContext) -> None:
        pool = [
            card_id for card_id, definition in game.card_defs.items()
            if card_id in game.executable_card_ids
            and definition.card_type == "MINION"
            and "UNDEAD" in definition.races
        ]
        added = []
        while len(context.player.hand) < 10 and pool:
            card = game._entity(game.rng.choice(sorted(pool)), created_by=context.card.card_id)
            card.costs_health_expiry_turn = game.turn
            context.player.hand.append(card)
            added.append(card.card_id)
        game._event(
            "forgotten_millennium_fill", player=context.player.index,
            source=context.card.card_id, cards=added,
        )


@dataclass(frozen=True)
class SummonLocationRat:
    def execute(self, game: Any, context: RuleContext) -> None:
        if len(context.player.board) + len(context.player.locations) >= 7:
            return
        rat = game._entity("JAIL_877t", created_by=context.card.card_id)
        rat.summoned_turn = game.turn
        game._summon(context.player, rat)


@dataclass(frozen=True)
class AddRandomShamanMinionLocked:
    """Add a random executable Shaman minion locked until another card is played."""

    def execute(self, game: Any, context: RuleContext) -> None:
        pool = sorted(
            card_id for card_id, definition in game.card_defs.items()
            if card_id in game.executable_card_ids
            and definition.card_type == "MINION"
            and definition.card_class == "SHAMAN"
        )
        if not pool or len(context.player.hand) >= 10:
            return
        card = game._entity(game.rng.choice(pool), created_by=context.card.card_id)
        card.locked_until_card_played = True
        destination = game._add_generated(context.player, card)
        game._event(
            "locked_shaman_minion_added", player=context.player.index,
            source=context.card.card_id, card=card.card_id,
            destination=destination,
        )


@dataclass(frozen=True)
class SpendManaCastRandomSpell:
    """Spend all current mana and cast a random spell of that cost."""

    def execute(self, game: Any, context: RuleContext) -> None:
        spent = max(0, context.player.mana)
        context.player.mana = 0
        if spent <= 0:
            return
        pool = sorted(
            card_id for card_id, definition in game.card_defs.items()
            if card_id in game.executable_card_ids
            and definition.card_type == "SPELL"
            and definition.cost == spent
        )
        if not pool:
            game._event(
                "forbidden_shrine_no_spell", player=context.player.index,
                source=context.card.card_id, spent=spent,
            )
            return
        spell = game._entity(game.rng.choice(pool), created_by=context.card.card_id)
        action_type = type(context.action) if context.action is not None else None
        if action_type is None:
            return
        try:
            game._cast_spell(context.player, spell, action_type("PLAY", spell.entity_id))
        except ValueError:
            for target_player, target_entity, _ in game._random_spell_target_candidates(
                context.player.index, spell
            ):
                try:
                    game._cast_spell(
                        context.player, spell,
                        action_type("PLAY", spell.entity_id, target_player, target_entity),
                    )
                    break
                except ValueError:
                    continue
        game._event(
            "forbidden_shrine_cast", player=context.player.index,
            source=context.card.card_id, spell=spell.card_id, spent=spent,
        )


@dataclass(frozen=True)
class ArmRubySanctum:
    """Convert the controller's next healing effect this turn into damage."""

    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.ruby_sanctum_turn = game.turn
        game._event(
            "ruby_sanctum_armed", player=context.player.index,
            source=context.card.card_id, turn=game.turn,
        )


@dataclass(frozen=True)
class StartZuramatPrison:
    """Ask the controller to discard a chosen card and summon the Prison token."""

    def execute(self, game: Any, context: RuleContext) -> None:
        if not context.player.hand:
            return
        game.pending_choice = {
            "kind": "HAND_DISCARD",
            "player": context.player.index,
            "source": context.card.card_id,
            "options": list(context.player.hand),
        }


@dataclass(frozen=True)
class NespirahUnshackledAfterFel:
    """After a Fel spell, add a random non-Colossal Naga at 1 cost."""

    def execute(self, game: Any, context: RuleContext) -> None:
        spell = (context.payload or {}).get("spell")
        if spell is None or spell.definition.spell_school != "FEL":
            return
        pool = sorted(
            card_id for card_id, definition in game.card_defs.items()
            if card_id in game.executable_card_ids
            and definition.card_type == "MINION"
            and "NAGA" in definition.races
            and "COLOSSAL" not in definition.mechanics
        )
        if not pool or len(context.player.hand) >= 10:
            return
        card = game._entity(game.rng.choice(pool), created_by=context.card.card_id)
        card.cost_delta = 1 - card.definition.cost
        destination = game._add_generated(context.player, card)
        game._event(
            "nespirah_naga_generated", player=context.player.index,
            source=context.card.card_id, spell=spell.card_id,
            card=card.card_id, destination=destination,
        )


@dataclass(frozen=True)
class BuffFriendlyMinionOrHandAttack:
    """Set a friendly battlefield/hand minion's attack to source attack."""

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player != context.player.index:
            raise ValueError("friendly minion target is required")
        target = next(
            (minion for minion in context.player.board
             if minion.entity_id == context.action.target_entity),
            None,
        )
        if target is None:
            target = next(
                (card for card in context.player.hand
                 if card.entity_id == context.action.target_entity),
                None,
            )
        if target is None or target.definition.card_type != "MINION":
            raise ValueError("friendly minion target is required")
        amount = max(0, context.card.attack - target.attack)
        target.attack_delta += amount
        game._event(
            "gruesome_nightmare_attack", player=context.player.index,
            source=context.card.card_id, target=target.entity_id, amount=amount,
        )


@dataclass(frozen=True)
class BuffSelfAttackShield:
    def execute(self, game: Any, context: RuleContext) -> None:
        context.card.attack_delta += 3
        context.card.divine_shield = True
        context.card.divine_shield_hits = max(1, context.card.divine_shield_hits)


@dataclass(frozen=True)
class BuffSelfHealthLifesteal:
    def execute(self, game: Any, context: RuleContext) -> None:
        context.card.health_delta += 3
        context.card.lifesteal = True


@dataclass(frozen=True)
class DamageEnemyHero:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        game._damage_hero(game.players[1 - context.player.index], self.amount, context.card)


@dataclass(frozen=True)
class SummonCustomRushWolf:
    count: int = 1

    def execute(self, game: Any, context: RuleContext) -> None:
        for _ in range(self.count):
            if len(context.player.board) + len(context.player.locations) >= 7:
                break
            token = game._entity("DRG_217t", created_by=context.card.card_id)
            token.attack_delta += 1
            token.health_delta -= 1
            token.taunt = False
            token.rush = True
            token.summoned_turn = game.turn
            game._summon(context.player, token)


@dataclass(frozen=True)
class BuffLocationTargetAndSleep:
    attack: int
    health: int
    dormant_turns: int = 2

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("friendly minion target is required")
        target = game._find_minion(context.action.target_player, context.action.target_entity)
        if context.action.target_player != context.player.index:
            raise ValueError("location target must be friendly")
        target.attack_delta += self.attack
        target.health_delta += self.health
        target.taunt = True
        target.dormant_turns = max(target.dormant_turns, self.dormant_turns)
        game._event(
            "location_buff_sleep", player=context.player.index,
            source=context.card.card_id, target=target.entity_id,
        )


@dataclass(frozen=True)
class BuffFriendlyHandMinion:
    attack: int
    health: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player != context.player.index:
            raise ValueError("friendly hand minion target is required")
        target = next(
            (card for card in context.player.hand
             if card.entity_id == context.action.target_entity),
            None,
        )
        if target is None or target.definition.card_type != "MINION":
            raise ValueError("friendly hand minion target is required")
        target.attack_delta += self.attack
        target.health_delta += self.health
        game._event(
            "location_hand_buff", player=context.player.index,
            source=context.card.card_id, target=target.entity_id,
            attack=self.attack, health=self.health,
        )


@dataclass(frozen=True)
class SummonEggCopyingTargetDragon:
    """Summon a 0/2 egg whose deathrattle copies the chosen Dragon."""

    egg_id: str

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player != context.player.index:
            raise ValueError("friendly Dragon target is required")
        target = game._find_minion(context.player.index, context.action.target_entity)
        if not target.has_race("DRAGON"):
            raise ValueError("friendly Dragon target is required")
        if len(context.player.board) + len(context.player.locations) >= 7:
            return
        egg = game._entity(self.egg_id, created_by=context.card.card_id)
        egg.deathrattle_copy_card_id = target.card_id
        egg.summoned_turn = game.turn
        game._summon(context.player, egg)
        game._event(
            "dragon_copy_egg_summoned", player=context.player.index,
            source=context.card.card_id, egg=egg.entity_id,
            copied=target.card_id,
        )


@dataclass(frozen=True)
class DiscoverTemporaryOneCostMinion:
    def execute(self, game: Any, context: RuleContext) -> None:
        pool = [
            card_id for card_id, definition in game.card_defs.items()
            if card_id in game.executable_card_ids
            and definition.card_type == "MINION" and definition.cost == 1
        ]
        game._offer_discover(context.player, pool, dark_gift=False,
                             source_card_id=context.card.card_id)
        if game.pending_choice is not None:
            for option in game.pending_choice["options"]:
                option.temporary = True


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
    count: int = 1

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [
            card_id for card_id in game.executable_card_ids
            if card_id in game.card_defs
            and game.card_defs[card_id].card_type == "MINION"
            and game.card_defs[card_id].cost == self.cost
        ]
        if not candidates:
            return
        for _ in range(self.count):
            if len(context.player.board) + len(context.player.locations) >= 7:
                break
            minion = game._entity(
                game.rng.choice(sorted(candidates)), created_by=context.card.card_id
            )
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
                entity=minion.entity_id, cost=self.cost,
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
            game._on_enter_hand_from_battlefield(
                owner, target, source=context.card.card_id,
            )
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
class OverhealGainAttack:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        context.card.attack_delta += self.amount
        game._event(
            "overheal_trigger", player=context.player.index,
            source=context.card.card_id, effect="attack",
            amount=self.amount,
        )


@dataclass(frozen=True)
class OverhealDraw:
    def execute(self, game: Any, context: RuleContext) -> None:
        Draw().execute(game, context)


@dataclass(frozen=True)
class OverhealSummonCrystal:
    def execute(self, game: Any, context: RuleContext) -> None:
        if len(context.player.board) + len(context.player.locations) >= 7:
            return
        crystal = game._entity("CORE_CFM_606t", created_by=context.card.card_id)
        crystal.summoned_turn = game.turn
        game._summon(context.player, crystal)
        game._event(
            "overheal_trigger", player=context.player.index,
            source=context.card.card_id, effect="summon_crystal",
            entity=crystal.entity_id,
        )


@dataclass(frozen=True)
class HealHero:
    amount: int
    side: str = "controller"

    def execute(self, game: Any, context: RuleContext) -> None:
        player = _recipient(game, context, self.side)
        amount = game._spell_effect_amount(context.player, context.card, self.amount)
        game._apply_heal(player, player, amount, source=context.card)


@dataclass(frozen=True)
class HealActionTarget:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        amount = game._spell_effect_amount(context.player, context.card, self.amount)
        if context.action.target_entity is None:
            target = game.players[context.action.target_player]
            owner = target
            game._apply_heal(owner, target, amount, source=context.card)
        else:
            owner = game.players[context.action.target_player]
            target = game._find_minion(
                context.action.target_player, context.action.target_entity
            )
            game._apply_heal(owner, target, amount, source=context.card)


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
        owner = game.players[context.action.target_player]
        game._apply_heal(owner, target, target.damage, source=context.card)


@dataclass(frozen=True)
class HealFriendlyCharacters:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        player = context.player
        amount = game._spell_effect_amount(context.player, context.card, self.amount)
        restored = game._apply_heal(
            player, player, amount, source=context.card,
            trigger_black_blood=False,
        )
        for minion in player.board:
            restored += game._apply_heal(
                player, minion, amount, source=context.card,
                trigger_black_blood=False,
            )
        if restored:
            game._black_blood_after_restore(player, source=context.card)


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
            game._apply_heal(player, target, 1, source=context.card)
        game._event("random_friendly_heal", player=player.index,
                    source=context.card.card_id, amount=self.amount)


@dataclass(frozen=True)
class DamageRandomOtherCharacters:
    """Mad Bomber-style random split damage to every other character."""

    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        # Select and resolve one hit at a time.  Sampling the whole list with
        # replacement and resolving deaths between hits can leave a dead
        # minion entity in the remaining sample, which makes replay fail with
        # ``minion not found``.  The live game re-evaluates random characters
        # after each damage event, so this also matches the intended semantics.
        hits: list[tuple[int, int | None]] = []
        for _ in range(max(0, self.amount)):
            targets: list[tuple[int, int | None]] = []
            for player in game.players:
                targets.append((player.index, None))
                targets.extend(
                    (player.index, minion.entity_id)
                    for minion in player.board
                    if minion.dormant_turns == 0 and minion.health > 0
                )
            targets = [target for target in targets if not (
                target[0] == context.player.index
                and target[1] == context.card.entity_id
            )]
            if not targets:
                break
            target = game.rng.choice(targets)
            hits.append(target)
            game._deal_to_target(context.player.index, target, 1, context.card)
            game._resolve_deaths()
        game._event("random_other_character_damage", player=context.player.index,
                    source=context.card.card_id, hits=hits)


@dataclass(frozen=True)
class DamageSelf:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        game._damage_minion(context.player.index, context.card, self.amount, context.card)
        game._resolve_deaths()


@dataclass(frozen=True)
class GrantAdjacentTaunt:
    def execute(self, game: Any, context: RuleContext) -> None:
        try:
            index = context.player.board.index(context.card)
        except ValueError:
            return
        affected = []
        for neighbor in (index - 1, index + 1):
            if 0 <= neighbor < len(context.player.board):
                target = context.player.board[neighbor]
                if target.dormant_turns == 0 and not target.silenced:
                    target.taunt = True
                    affected.append(target.entity_id)
        game._event("adjacent_taunt", player=context.player.index,
                    source=context.card.card_id, affected=affected)


@dataclass(frozen=True)
class BuffOtherMurlocsHealth:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        affected = []
        for minion in context.player.board:
            if minion is not context.card and minion.has_race("MURLOC"):
                minion.health_delta += self.amount
                affected.append(minion.entity_id)
        game._event("buff_other_murlocs_health", player=context.player.index,
                    source=context.card.card_id, affected=affected, amount=self.amount)


@dataclass(frozen=True)
class GiveRandomFriendlyDivineShieldTaunt:
    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [m for m in context.player.board
                      if m.health > 0 and m.dormant_turns == 0]
        if not candidates:
            return
        target = game.rng.choice(candidates)
        target.divine_shield = True
        target.divine_shield_hits = max(1, target.divine_shield_hits)
        target.taunt = True
        game._event("random_friendly_shield_taunt", player=context.player.index,
                    source=context.card.card_id, target=target.entity_id)


@dataclass(frozen=True)
class GiveActionTargetDivineShield:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player != context.player.index:
            raise ValueError("friendly minion target is required")
        target = game._find_minion(context.player.index, context.action.target_entity)
        target.divine_shield = True
        target.divine_shield_hits = max(1, target.divine_shield_hits)
        game._event("friendly_divine_shield", player=context.player.index,
                    source=context.card.card_id, target=target.entity_id)


@dataclass(frozen=True)
class BuffAllMinionsInHand:
    attack: int
    health: int

    def execute(self, game: Any, context: RuleContext) -> None:
        affected = []
        for card in context.player.hand:
            if card.definition.card_type == "MINION":
                card.attack_delta += self.attack
                card.health_delta += self.health
                affected.append(card.entity_id)
        game._event("buff_minions_in_hand", player=context.player.index,
                    source=context.card.card_id, affected=affected,
                    attack=self.attack, health=self.health)


@dataclass(frozen=True)
class ForceEachMinionToAttackAnother:
    """Force every living minion to fight a random other living minion."""

    def execute(self, game: Any, context: RuleContext) -> None:
        all_minions = [
            (player.index, minion)
            for player in game.players
            for minion in player.board
            if minion.health > 0 and minion.dormant_turns == 0
        ]
        pairs = []
        for owner_index, attacker in list(all_minions):
            candidates = [
                (target_owner, target)
                for target_owner, target in all_minions
                if target.entity_id != attacker.entity_id and target.health > 0
            ]
            if not candidates or attacker.health <= 0:
                continue
            target_owner, target = game.rng.choice(candidates)
            pairs.append((owner_index, attacker, target_owner, target))
        for owner_index, attacker, target_owner, target in pairs:
            if attacker.health <= 0 or target.health <= 0:
                continue
            game._damage_minion(target_owner, target, attacker.attack, attacker)
            if target.health > 0 and attacker.health > 0:
                game._damage_minion(owner_index, attacker, target.attack, target)
            game._resolve_deaths()
        game._event("force_minions_attack", player=context.player.index,
                    source=context.card.card_id, pair_count=len(pairs))


@dataclass(frozen=True)
class TakeRandomEnemyMinion:
    """Take control of a random enemy minion permanently."""

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [m for m in game.players[1 - context.player.index].board
                      if m.health > 0 and m.dormant_turns == 0]
        if not candidates or len(context.player.board) + len(context.player.locations) >= 7:
            return
        target = game.rng.choice(candidates)
        enemy = game.players[1 - context.player.index]
        enemy.board.remove(target)
        context.player.board.append(target)
        target.return_control_to = None
        target.return_control_at_end_of_turn = None
        target.cant_attack_turn = game.turn
        game._refresh_continuous(enemy)
        game._refresh_continuous(context.player)
        game._event("random_minion_control", player=context.player.index,
                    source=context.card.card_id, target=target.entity_id,
                    card=target.card_id)


@dataclass(frozen=True)
class StealEnemyHandCards:
    count: int

    def execute(self, game: Any, context: RuleContext) -> None:
        enemy = game.players[1 - context.player.index]
        chosen = list(enemy.hand)
        game.rng.shuffle(chosen)
        stolen = []
        for card in chosen[:self.count]:
            if card not in enemy.hand:
                continue
            enemy.hand.remove(card)
            if len(context.player.hand) < 10:
                card.created_by = context.card.card_id
                card.copied_from_opponent = True
                context.player.hand.append(card)
                stolen.append(card.card_id)
            else:
                game._event("generated_burned", player=context.player.index,
                            card=card.card_id, source=context.card.card_id)
        game._event("steal_enemy_hand", player=context.player.index,
                    source=context.card.card_id, cards=stolen)


@dataclass(frozen=True)
class BuffMinionsInHandAndBoard:
    attack: int
    health: int

    def execute(self, game: Any, context: RuleContext) -> None:
        affected = []
        for card in context.player.hand:
            if card.definition.card_type == "MINION":
                card.attack_delta += self.attack
                card.health_delta += self.health
                affected.append(card.entity_id)
        for minion in context.player.board:
            if minion.health > 0:
                minion.attack_delta += self.attack
                minion.health_delta += self.health
                affected.append(minion.entity_id)
        game._event("buff_minions_hand_and_board", player=context.player.index,
                    source=context.card.card_id, affected=affected,
                    attack=self.attack, health=self.health)


@dataclass(frozen=True)
class ReduceHandMinionCosts:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        affected = []
        for card in context.player.hand:
            if card.definition.card_type == "MINION":
                card.cost_delta -= self.amount
                affected.append(card.entity_id)
        game._event("reduce_hand_minion_costs", player=context.player.index,
                    source=context.card.card_id, affected=affected,
                    amount=self.amount)


@dataclass(frozen=True)
class SummonNamedMinion:
    card_id: str

    def execute(self, game: Any, context: RuleContext) -> None:
        if len(context.player.board) + len(context.player.locations) >= 7:
            return
        if self.card_id not in game.card_defs or self.card_id not in game.executable_card_ids:
            return
        minion = game._entity(self.card_id, created_by=context.card.card_id)
        minion.summoned_turn = game.turn
        game._summon(context.player, minion)
        game._event("summon_named_minion", player=context.player.index,
                    source=context.card.card_id, card=self.card_id,
                    entity=minion.entity_id)


@dataclass(frozen=True)
class GrantTargetDeathrattleSummon:
    card_id: str

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player != context.player.index:
            raise ValueError("friendly minion target is required")
        target = game._find_minion(context.player.index, context.action.target_entity)
        target.attack_delta += 2
        target.health_delta += 6
        target.taunt = True
        target.deathrattle_summon_card_id = self.card_id
        game._event("target_deathrattle_summon", player=context.player.index,
                    source=context.card.card_id, target=target.entity_id,
                    summon=self.card_id)


@dataclass(frozen=True)
class DestroyTargetGainHealth:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("minion target is required")
        owner = game.players[context.action.target_player]
        target = game._find_minion(owner.index, context.action.target_entity)
        gained = max(0, target.max_health)
        target.damage = target.max_health
        game._resolve_deaths()
        context.player.health = min(context.player.max_health, context.player.health + gained)
        game._event("destroy_target_gain_health", player=context.player.index,
                    source=context.card.card_id, target=target.entity_id, gained=gained)


@dataclass(frozen=True)
class DestroyRandomEnemyMinion:
    def execute(self, game: Any, context: RuleContext) -> None:
        targets = game._random_enemy_minions(context.player.index)
        if not targets:
            return
        target = game.rng.choice(targets)
        target.damage = target.max_health
        game._resolve_deaths()
        game._event("destroy_random_enemy_minion", player=context.player.index,
                    source=context.card.card_id, target=target.entity_id)


@dataclass(frozen=True)
class SummonAnimalCompanion:
    def execute(self, game: Any, context: RuleContext) -> None:
        # MEND_300/303 replace every later Animal Companion with a random
        # Beast of the upgraded cost; MEND_304 adds one further companion.
        upgrade = max(0, context.player.animal_companion_cost_increase)
        if upgrade:
            candidates = _filtered_executable_ids(
                game, card_type="MINION", race="BEAST", cost=3 + upgrade,
            )
        else:
            candidates = [card_id for card_id in ("NEW1_032", "NEW1_033", "NEW1_034")
                          if card_id in game.card_defs]
        count = 1 + max(0, context.player.animal_companion_extra_count)
        for _ in range(count):
            if not candidates or len(context.player.board) + len(context.player.locations) >= 7:
                break
            minion = game._entity(game.rng.choice(candidates), created_by=context.card.card_id)
            minion.summoned_turn = game.turn
            game._summon(context.player, minion)


@dataclass(frozen=True)
class SummonSelectedAnimalCompanion:
    """Resolve a specifically selected companion through global replacement.

    Spiritspeaker retains the meaningful Huffer/Leokk/Misha selection before
    an upgrade.  Once a replacement effect is active, that selected companion
    is replaced by the same random-Beast companion event as every other
    source.
    """

    companion_id: str

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.player.animal_companion_cost_increase:
            SummonAnimalCompanion().execute(game, context)
            return
        if len(context.player.board) + len(context.player.locations) >= 7:
            return
        if self.companion_id not in game.card_defs:
            return
        minion = game._entity(self.companion_id, created_by=context.card.card_id)
        minion.summoned_turn = game.turn
        game._summon(context.player, minion)


@dataclass(frozen=True)
class SummonAllAnimalCompanions:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.player.animal_companion_cost_increase:
            # The replacement is global, so a card that would summon all
            # three companions instead performs three upgraded companion
            # summons. Each invocation observes the extra-copy rule.
            for _ in range(3):
                SummonAnimalCompanion().execute(game, context)
            return
        for card_id in ("NEW1_032", "NEW1_033", "NEW1_034"):
            if len(context.player.board) + len(context.player.locations) >= 7:
                break
            if card_id not in game.card_defs:
                continue
            minion = game._entity(card_id, created_by=context.card.card_id)
            minion.summoned_turn = game.turn
            game._summon(context.player, minion)


@dataclass(frozen=True)
class SummonFromDeckAtMostCost:
    max_cost: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if len(context.player.board) + len(context.player.locations) >= 7:
            return
        candidates = [card for card in context.player.deck
                      if card.definition.card_type == "MINION"
                      and card.definition.cost <= self.max_cost]
        if not candidates:
            return
        card = game.rng.choice(candidates)
        context.player.deck.remove(card)
        card.summoned_turn = game.turn
        game._summon(context.player, card)
        game._event("summon_from_deck_cost", player=context.player.index,
                    source=context.card.card_id, card=card.card_id,
                    entity=card.entity_id, max_cost=self.max_cost)


@dataclass(frozen=True)
class BuffDifferentTribeMinions:
    amount: int = 1

    def execute(self, game: Any, context: RuleContext) -> None:
        groups: dict[str, list[Any]] = {}
        for minion in context.player.board:
            tribes = set(minion.definition.races) or {minion.definition.race or "NONE"}
            for tribe in tribes:
                groups.setdefault(tribe, []).append(minion)
        chosen = []
        for tribe in game.rng.sample(list(groups), min(len(groups), 3)):
            chosen.append(game.rng.choice(groups[tribe]))
        for minion in chosen:
            minion.attack_delta += self.amount
            minion.health_delta += self.amount
        game._event("buff_different_tribe_minions", player=context.player.index,
                    source=context.card.card_id, targets=[m.entity_id for m in chosen])


@dataclass(frozen=True)
class EquipGeneratedWeapon:
    card_id: str
    name: str
    attack: int
    durability: int

    def execute(self, game: Any, context: RuleContext) -> None:
        from .dragon_mirror import Weapon
        game._equip_weapon(context.player,
                           Weapon(self.card_id, self.name, self.attack, self.durability))


@dataclass(frozen=True)
class SummonRecruitsAndEquip:
    count: int = 3

    def execute(self, game: Any, context: RuleContext) -> None:
        Summon("CS2_101t", self.count).execute(game, context)
        EquipGeneratedWeapon("CS2_091", "Light's Justice", 1, 4).execute(game, context)


# ---- Standard tranche 50I -------------------------------------------------
# The last Lost City collection has a dense group of cards that manufacture
# small tokens or read a persistent game counter.  Keep those mechanics here
# rather than teaching each card a bespoke engine branch.  ``_lost_city_token``
# intentionally creates a non-collectible instance: it is never admitted to a
# Constructed deck or a random generator pool, but carries normal minion
# combat/death state once it enters a zone.


def _lost_city_token(
    game: Any, card_id: str, name: str, *, cost: int, attack: int,
    health: int, race: str = "", mechanics: tuple[str, ...] = (),
    card_class: str = "NEUTRAL",
) -> Any:
    from .dragon_mirror import CardDef

    definition = CardDef(
        card_id, name, "MINION", cost, attack, health, race, mechanics,
        card_class, (race,) if race else (), "THE_LOST_CITY",
    )
    return game._instance_from_definition(definition)


@dataclass(frozen=True)
class OfferTransformIntoDifferentMinion:
    """Tribute Dance: target first, then explicitly choose a new minion."""

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("minion target is required")
        target = game._find_minion(
            context.action.target_player, context.action.target_entity
        )
        pool = [
            card_id for card_id, definition in game.card_defs.items()
            if card_id in game.executable_card_ids
            and definition.card_type == "MINION"
            and card_id != target.card_id
        ]
        if not pool:
            return
        game.rng.shuffle(pool)
        options = tuple(
            (f"Transform into {game.card_defs[card_id].name}",
             (TransformActionTarget(card_id),))
            for card_id in pool[:3]
        )
        game.pending_choice = {
            "kind": "RULE_CHOICE", "player": context.player.index,
            "card": context.card, "action": context.action,
            "options": options,
        }
        game._event("tribute_dance_offer", player=context.player.index,
                    source=context.card.card_id, target=target.entity_id,
                    options=pool[:3])


@dataclass(frozen=True)
class TriggerRandomFriendlyDeadDeathrattles:
    count: int

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [
            minion for minion in context.player.dead_minions
            if "DEATHRATTLE" in minion.definition.mechanics and not minion.silenced
        ]
        game.rng.shuffle(candidates)
        triggered: list[int] = []
        for minion in candidates[:self.count]:
            game._deathrattle(context.player, copy.deepcopy(minion))
            game._resolve_deaths()
            triggered.append(minion.entity_id)
        game._event("trigger_dead_deathrattles", player=context.player.index,
                    source=context.card.card_id, triggered=triggered)


@dataclass(frozen=True)
class DestroyTopDeckDiscoverSameRarity:
    def execute(self, game: Any, context: RuleContext) -> None:
        deck = context.player.deck
        if not deck:
            return
        destroyed = deck.pop()
        pool = [
            card_id for card_id, definition in game.card_defs.items()
            if card_id in game.executable_card_ids
            and definition.rarity == destroyed.definition.rarity
        ]
        game._event("relic_miner_destroy", player=context.player.index,
                    source=context.card.card_id, destroyed=destroyed.card_id,
                    rarity=destroyed.definition.rarity)
        if pool:
            game._offer_discover(context.player, pool, False,
                                 source_card_id=context.card.card_id)


@dataclass(frozen=True)
class SummonTokensAttackActionTarget:
    card_id: str
    count: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("minion target is required")
        target_owner = context.action.target_player
        target_id = context.action.target_entity
        summoned: list[int] = []
        for _ in range(self.count):
            if len(context.player.board) + len(context.player.locations) >= 7:
                break
            try:
                target = game._find_minion(target_owner, target_id)
            except ValueError:
                break
            token = game._entity(self.card_id, created_by=context.card.card_id)
            token.rush = True
            token.summoned_turn = game.turn
            game._summon(context.player, token)
            game._forced_minion_attack(context.player.index, token,
                                       target_owner, target)
            summoned.append(token.entity_id)
        game._event("summon_attack_target", player=context.player.index,
                    source=context.card.card_id, summoned=summoned,
                    target=target_id)


@dataclass(frozen=True)
class QueueStartTurnTokenSummon:
    card_id: str
    count: int

    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.delayed_token_summons.append(
            (context.player.turns_taken, self.card_id, self.count,
             context.card.card_id)
        )
        game._event("delayed_token_summon", player=context.player.index,
                    source=context.card.card_id, card=self.card_id,
                    count=self.count)


@dataclass(frozen=True)
class BuffOtherLowAttackMinionsTaunt:
    attack: int
    health: int
    maximum_attack: int

    def execute(self, game: Any, context: RuleContext) -> None:
        affected = []
        for minion in context.player.board:
            if minion.entity_id == context.card.entity_id or minion.attack > self.maximum_attack:
                continue
            minion.attack_delta += self.attack
            minion.health_delta += self.health
            minion.taunt = True
            affected.append(minion.entity_id)
        game._event("low_attack_minion_buff", player=context.player.index,
                    source=context.card.card_id, affected=affected)


@dataclass(frozen=True)
class CopyKilledMinionToHand:
    def execute(self, game: Any, context: RuleContext) -> None:
        enemy = game.players[1 - context.player.index]
        killed = [
            minion for minion in enemy.dead_minions
            if minion.killed_by_entity == context.card.entity_id
        ]
        if not killed:
            return
        copy_card = killed[-1].clone(game.next_entity_id)
        game.next_entity_id += 1
        copy_card.created_by = context.card.card_id
        game._add_generated(context.player, copy_card)
        game._event("sabretooth_copy", player=context.player.index,
                    source=context.card.entity_id, card=copy_card.card_id)


@dataclass(frozen=True)
class BlockEnemyHeroHealing:
    def execute(self, game: Any, context: RuleContext) -> None:
        enemy = game.players[1 - context.player.index]
        # The global turn advances once at each player's start.  A value one
        # turn ahead therefore covers the opponent's coming turn and expires
        # before this minion's controller starts another one.
        enemy.hero_heal_blocked_until_enemy_turn = game.turn + 1
        enemy.hero_heal_blocked_by = context.player.index
        game._event("hero_healing_blocked", player=enemy.index,
                    source=context.card.card_id)


@dataclass(frozen=True)
class DestroyFriendlyMakeBones:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player != context.player.index:
            raise ValueError("friendly minion target is required")
        # A repeated Battlecry can reuse the original target action. If the
        # first copy already destroyed that minion, the second copy fizzles.
        target = next(
            (minion for minion in context.player.board
             if minion.entity_id == context.action.target_entity),
            None,
        )
        if target is None:
            return
        attack, health = target.attack, target.max_health
        target.damage = target.max_health
        game._resolve_deaths()
        if len(context.player.hand) < 10:
            bones = game._entity("TLC_829t", created_by=context.card.card_id)
            bones.payload_attack = attack
            bones.payload_health = health
            context.player.hand.append(bones)
        game._event("dissolving_ooze_bones", player=context.player.index,
                    source=context.card.card_id, attack=attack, health=health)


@dataclass(frozen=True)
class BuffTargetFromPayload:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("minion target is required")
        target = game._find_minion(context.action.target_player, context.action.target_entity)
        target.attack_delta += int(getattr(context.card, "payload_attack", 0))
        target.health_delta += int(getattr(context.card, "payload_health", 0))
        game._event("bones_buff", player=context.player.index,
                    source=context.card.card_id, target=target.entity_id,
                    attack=getattr(context.card, "payload_attack", 0),
                    health=getattr(context.card, "payload_health", 0))


@dataclass(frozen=True)
class BuffEachDifferentTribe:
    def execute(self, game: Any, context: RuleContext) -> None:
        seen: set[str] = set()
        affected = []
        for minion in context.player.board:
            tribes = tuple(sorted(set(minion.definition.races) or {minion.definition.race or "NONE"}))
            tribe = next((race for race in tribes if race not in seen), None)
            if tribe is None:
                continue
            seen.add(tribe)
            minion.attack_delta += 1
            minion.health_delta += 1
            affected.append(minion.entity_id)
        game._event("storyteller_tribe_buff", player=context.player.index,
                    source=context.card.card_id, affected=affected)


@dataclass(frozen=True)
class SetMinionCostForGame:
    cost: int

    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.minion_cost_fixed = self.cost
        game._event("minion_cost_fixed", player=context.player.index,
                    source=context.card.card_id, cost=self.cost)


@dataclass(frozen=True)
class OfferHighCostSpellDiscounted:
    min_cost: int
    target_cost: int

    def execute(self, game: Any, context: RuleContext) -> None:
        pool = _filtered_executable_ids(game, card_type="SPELL", min_cost=self.min_cost)
        game._offer_discover(context.player, pool, False,
                             source_card_id=context.card.card_id)
        if game.pending_choice is not None:
            for option in game.pending_choice["options"]:
                option.cost_delta += self.target_cost - option.definition.cost


@dataclass(frozen=True)
class DiscountNonStartingHandCards:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        affected = []
        for held in context.player.hand:
            if held.started_in_deck:
                continue
            held.cost_delta -= self.amount
            affected.append(held.entity_id)
        game._event("nonstarting_hand_discount", player=context.player.index,
                    source=context.card.card_id, affected=affected, amount=self.amount)


@dataclass(frozen=True)
class AddSmallRock:
    def execute(self, game: Any, context: RuleContext) -> None:
        rock = game._entity("GILA_500p2t", created_by=context.card.card_id)
        rock.cost_delta += 1
        rock.payload_damage = 3
        game._add_generated(context.player, rock)


@dataclass(frozen=True)
class DamageTargetFromPayload:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("target is required")
        amount = int(getattr(context.card, "payload_damage", 1))
        game._deal_to_target(context.player.index,
                             (context.action.target_player, context.action.target_entity),
                             amount, context.card)
        game._resolve_deaths()


@dataclass(frozen=True)
class ReplayRandomSchoolSpellThisTurn:
    school: str

    def execute(self, game: Any, context: RuleContext) -> None:
        # Rules deliberately do not import the simulator at module import
        # time: it imports this registry.  The local import avoids that cycle.
        from .dragon_mirror import Action
        spells = [
            spell for spell in context.player.spells_this_turn_for_replay
            if spell.definition.spell_school == self.school
        ]
        if not spells:
            return
        spell = copy.deepcopy(game.rng.choice(spells))
        spell.created_by = context.card.card_id
        try:
            game._cast_spell(context.player, spell, Action("PLAY", spell.entity_id,
                                                            context.player.index,
                                                            context.card.entity_id))
        except ValueError:
            for target_player, target_entity, _ in game._random_spell_target_candidates(
                context.player.index, spell
            ):
                try:
                    game._cast_spell(context.player, spell,
                                     Action("PLAY", spell.entity_id, target_player, target_entity))
                    break
                except ValueError:
                    continue
        game._event("recast_random_school_spell", player=context.player.index,
                    source=context.card.entity_id, spell=spell.card_id, school=self.school)


@dataclass(frozen=True)
class CastRandomDeckSpellAtSource:
    maximum_cost: int

    def execute(self, game: Any, context: RuleContext) -> None:
        from .dragon_mirror import Action
        candidates = [
            card for card in context.player.deck
            if card.definition.card_type == "SPELL" and card.cost <= self.maximum_cost
        ]
        if not candidates:
            return
        spell = game.rng.choice(candidates)
        context.player.deck.remove(spell)
        try:
            game._cast_spell(context.player, spell,
                             Action("PLAY", spell.entity_id, context.player.index,
                                    context.card.entity_id))
        except ValueError:
            for target_player, target_entity, _ in game._random_spell_target_candidates(
                context.player.index, spell
            ):
                try:
                    game._cast_spell(context.player, spell,
                                     Action("PLAY", spell.entity_id, target_player, target_entity))
                    break
                except ValueError:
                    continue
        game._event("deck_spell_cast", player=context.player.index,
                    source=context.card.entity_id, spell=spell.card_id)


@dataclass(frozen=True)
class BuffTargetAndSameTribe:
    attack: int
    health: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player != context.player.index:
            raise ValueError("friendly minion target is required")
        target = game._find_minion(context.player.index, context.action.target_entity)
        races = set(target.definition.races) or {target.definition.race}
        for minion in context.player.board:
            if minion is target or races & (set(minion.definition.races) | {minion.definition.race}):
                minion.attack_delta += self.attack
                minion.health_delta += self.health


@dataclass(frozen=True)
class GrantRandomBonusEffects:
    count: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player != context.player.index:
            raise ValueError("friendly minion target is required")
        target = game._find_minion(context.player.index, context.action.target_entity)
        granted = []
        for _ in range(self.count):
            effect = game._grant_bonus_effect(context.player, target,
                                              source=context.card.card_id)
            if effect is None:
                break
            granted.append(effect)
        game._event("random_bonus_effects", player=context.player.index,
                    source=context.card.card_id, target=target.entity_id,
                    effects=granted)


@dataclass(frozen=True)
class SetNextTemporaryDiscount:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.next_temporary_cost_reduction += self.amount
        game._event("temporary_discount_armed", player=context.player.index,
                    source=context.card.card_id, amount=self.amount)


@dataclass(frozen=True)
class TitanographerAbility:
    """Record a rotating Titan ability without widening the public action space.

    Actual Titan abilities are selected from the executable Titan ability pool
    once their generated closures are available; until then this is an
    auditable held-card state, not a fake spell cast.
    """

    def execute(self, game: Any, context: RuleContext) -> None:
        pool = [
            card_id for card_id, definition in game.card_defs.items()
            if card_id in game.executable_card_ids
            and "TITAN" in definition.text.upper()
            and definition.card_type in {"SPELL", "HERO_POWER"}
        ]
        context.card.titan_ability_id = game.rng.choice(pool) if pool else None
        game._event("titanographer_ability", player=context.player.index,
                    source=context.card.entity_id, ability=context.card.titan_ability_id)


@dataclass(frozen=True)
class SummonRandomMinionByDiscoverState:
    def execute(self, game: Any, context: RuleContext) -> None:
        cost = 4 if context.player.discovers_this_turn else 2
        game._summon_random_executable_minion(context.player,
                                               source_card_id=context.card.card_id,
                                               cost=cost)


@dataclass(frozen=True)
class PropagateRandomBonusDeathrattle:
    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [minion for minion in context.player.board
                      if minion.dormant_turns == 0 and minion.health > 0]
        if not candidates:
            return
        target = game.rng.choice(candidates)
        game._grant_bonus_effect(context.player, target, source=context.card.card_id)
        target.propagate_bonus_deathrattle = True
        game._event("propagate_bonus_deathrattle", player=context.player.index,
                    source=context.card.card_id, target=target.entity_id)


@dataclass(frozen=True)
class AddRandomSpellsCostHealth:
    count: int
    school: str

    def execute(self, game: Any, context: RuleContext) -> None:
        pool = _filtered_executable_ids(game, card_type="SPELL", spell_school=self.school)
        for _ in range(self.count):
            if not pool:
                break
            spell = game._entity(game.rng.choice(pool), created_by=context.card.card_id)
            spell.costs_health_expiry_turn = 1 - context.player.index
            game._add_generated(context.player, spell)


@dataclass(frozen=True)
class AddTemporaryRandomMinions:
    count: int
    cost: int

    def execute(self, game: Any, context: RuleContext) -> None:
        pool = _filtered_executable_ids(game, card_type="MINION", cost=self.cost)
        for _ in range(self.count):
            if not pool:
                break
            minion = game._entity(game.rng.choice(pool), created_by=context.card.card_id)
            minion.temporary = True
            game._add_generated(context.player, minion)


@dataclass(frozen=True)
class SummonRandomFelBeast:
    def execute(self, game: Any, context: RuleContext) -> None:
        pool = _filtered_executable_ids(game, card_type="MINION", race="BEAST")
        if pool:
            minion = game._entity(game.rng.choice(pool), created_by=context.card.card_id)
            minion.summoned_turn = game.turn
            game._summon(context.player, minion)


@dataclass(frozen=True)
class OfferOtherClassWeapon:
    def execute(self, game: Any, context: RuleContext) -> None:
        pool = [
            card_id for card_id, definition in game.card_defs.items()
            if card_id in game.executable_card_ids
            and definition.card_type == "WEAPON"
            and definition.card_class not in {"", "NEUTRAL", context.player.card_class}
        ]
        if not pool:
            return
        weapon = game._entity(game.rng.choice(pool), created_by=context.card.card_id)
        if context.card.combo_active:
            # Weapon is an ordinary CardInstance until equipped, so mutate
            # its instance attack modifier rather than a nonexistent weapon
            # object field.
            weapon.attack_delta += 2
        game._add_generated(context.player, weapon)


@dataclass(frozen=True)
class DamagePerShuffle:
    base: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("enemy minion target is required")
        amount = self.base + context.player.cards_shuffled_into_deck
        game._deal_to_target(context.player.index,
                             (context.action.target_player, context.action.target_entity),
                             amount, context.card)
        game._resolve_deaths()


@dataclass(frozen=True)
class ShuffleNinjas:
    count: int

    def execute(self, game: Any, context: RuleContext) -> None:
        for _ in range(self.count):
            ninja = _lost_city_token(game, "TLC_518t", "Ninja", cost=3,
                                      attack=3, health=3, mechanics=("STEALTH",))
            ninja.stealth = True
            ninja.summoned_when_drawn = True
            context.player.deck.insert(game.rng.randrange(len(context.player.deck) + 1), ninja)
        context.player.cards_shuffled_into_deck += self.count
        game._event("ninjas_shuffled", player=context.player.index,
                    source=context.card.card_id, count=self.count)


@dataclass(frozen=True)
class CostMinusShuffledCards:
    def adjustment(self, _game: Any, player: Any, _card: Any) -> int:
        return -player.cards_shuffled_into_deck


@dataclass(frozen=True)
class OfferEnemyDeckCardTop:
    def execute(self, game: Any, context: RuleContext) -> None:
        enemy = game.players[1 - context.player.index]
        options = game.rng.sample(enemy.deck, min(3, len(enemy.deck)))
        if not options:
            return
        context.player.discovers_this_turn = True
        game.pending_choice = {
            "kind": "ENEMY_DECK_TOP_DISCOVER", "player": context.player.index,
            "enemy": enemy.index, "source_card_id": context.card.card_id,
            "options": options,
        }
        game._event("enemy_deck_top_offer", player=context.player.index,
                    source=context.card.card_id,
                    options=[card.card_id for card in options])


@dataclass(frozen=True)
class SpendArmorDamageAllMinions:
    maximum: int

    def execute(self, game: Any, context: RuleContext) -> None:
        spent = min(self.maximum, context.player.armor)
        context.player.armor -= spent
        for owner in game.players:
            for minion in list(owner.board):
                game._damage_minion(owner.index, minion, spent, context.card)
        game._resolve_deaths()
        game._event("shellnado", player=context.player.index,
                    source=context.card.card_id, armor_spent=spent)


@dataclass(frozen=True)
class GainArmorDamageTarget:
    armor: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("enemy minion target is required")
        game._gain_armor(context.player, self.armor)
        game._deal_to_target(context.player.index,
                             (context.action.target_player, context.action.target_entity),
                             context.player.armor, context.card)
        game._resolve_deaths()


@dataclass(frozen=True)
class SummonSecurity:
    count: int

    def execute(self, game: Any, context: RuleContext) -> None:
        Summon("TLC_622t", self.count).execute(game, context)


@dataclass(frozen=True)
class GainAttackAfterDamage:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.payload.get("amount", 0) > 0:
            context.card.attack_delta += self.amount


@dataclass(frozen=True)
class SummonDeckDeathrattlesAndFight:
    count: int

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [card for card in context.player.deck
                      if card.definition.card_type == "MINION"
                      and "DEATHRATTLE" in card.definition.mechanics]
        game.rng.shuffle(candidates)
        summoned = []
        for card in candidates[:self.count]:
            if len(context.player.board) + len(context.player.locations) >= 7:
                break
            context.player.deck.remove(card)
            card.summoned_turn = game.turn
            game._summon(context.player, card)
            summoned.append(card)
        if len(summoned) == 2:
            game._forced_minion_attack(context.player.index, summoned[0],
                                       context.player.index, summoned[1])
        game._event("herenn_deathrattle_fight", player=context.player.index,
                    source=context.card.card_id, summoned=[card.entity_id for card in summoned])


@dataclass(frozen=True)
class SetAttackerHealthToSource:
    def execute(self, game: Any, context: RuleContext) -> None:
        attacker = context.payload.get("attacker")
        if attacker is None or attacker.entity_id == context.card.entity_id:
            return
        attacker.health_delta += context.card.max_health - attacker.max_health
        attacker.damage = min(attacker.damage, max(0, attacker.max_health - context.card.max_health))


@dataclass(frozen=True)
class AddRandomSchoolSpells:
    schools: tuple[str, ...]

    def execute(self, game: Any, context: RuleContext) -> None:
        for school in self.schools:
            pool = _filtered_executable_ids(game, card_type="SPELL", spell_school=school)
            if pool:
                game._add_generated(context.player,
                                    game._entity(game.rng.choice(pool), created_by=context.card.card_id))


@dataclass(frozen=True)
class ResurrectCostsWithReborn:
    costs: tuple[int, ...]

    def execute(self, game: Any, context: RuleContext) -> None:
        for cost in self.costs:
            if len(context.player.board) + len(context.player.locations) >= 7:
                break
            candidates = [card for card in context.player.dead_minions
                          if card.definition.cost == cost]
            if not candidates:
                continue
            revived = copy.deepcopy(game.rng.choice(candidates)).clone(game.next_entity_id)
            game.next_entity_id += 1
            revived.reborn = True
            revived.damage = 0
            revived.summoned_turn = game.turn
            game._summon(context.player, revived)


@dataclass(frozen=True)
class CostIfHolyAndShadowThisTurn:
    target_cost: int

    def adjustment(self, _game: Any, player: Any, card: Any) -> int:
        if {"HOLY", "SHADOW"} <= player.spell_schools_cast_this_turn:
            return self.target_cost - card.cost
        return 0


@dataclass(frozen=True)
class AttackEnemyHealedTarget:
    def execute(self, game: Any, context: RuleContext) -> None:
        target = context.payload.get("target")
        owner_index = context.payload.get("target_owner")
        if target is None or owner_index is None:
            return
        if target is game.players[owner_index]:
            game._damage_hero(target, context.card.attack, context.card)
            return
        if target in game.players[owner_index].board:
            game._forced_minion_attack(context.player.index, context.card,
                                       owner_index, target)


@dataclass(frozen=True)
class DiscountRandomHandRaceEndTurn:
    race: str
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [card for card in context.player.hand if card.has_race(self.race)]
        if candidates:
            game.rng.choice(candidates).cost_delta -= self.amount


@dataclass(frozen=True)
class ShuffleRaptors:
    count: int

    def execute(self, game: Any, context: RuleContext) -> None:
        for _ in range(self.count):
            raptor = _lost_city_token(game, "TLC_826t", "Raptor", cost=1,
                                       attack=3, health=2, race="BEAST")
            raptor.summoned_when_drawn = True
            raptor.draw_on_summon = True
            context.player.deck.insert(game.rng.randrange(len(context.player.deck) + 1), raptor)
        context.player.cards_shuffled_into_deck += self.count
        game._event("raptors_shuffled", player=context.player.index,
                    source=context.card.card_id, count=self.count)


@dataclass(frozen=True)
class GrowSelfEverywhere:
    attack: int

    def execute(self, game: Any, context: RuleContext) -> None:
        for zone in (context.player.board, context.player.hand, context.player.deck):
            for card in zone:
                if card.card_id == context.card.card_id:
                    card.attack_delta += self.attack


@dataclass(frozen=True)
class SummonPterrordaxAndStealHealth:
    def execute(self, game: Any, context: RuleContext) -> None:
        if len(context.player.board) + len(context.player.locations) >= 7:
            return
        pterrordax = game._entity("TLC_831t", created_by=context.card.card_id)
        pterrordax.summoned_turn = game.turn
        game._summon(context.player, pterrordax)
        for owner in game.players:
            for minion in list(owner.board):
                if minion.entity_id == pterrordax.entity_id:
                    continue
                game._steal_health(context.player, (owner.index, minion.entity_id), 1)
        game._resolve_deaths()


@dataclass(frozen=True)
class DoubleOneCostPlays:
    def execute(self, game: Any, context: RuleContext) -> None:
        played = context.payload.get("played")
        if played is None or played.entity_id == context.card.entity_id:
            return
        if played.definition.cost == 1 and played.definition.card_type == "MINION":
            played.attack_delta += played.attack
            played.health_delta += played.max_health


@dataclass(frozen=True)
class DealEnemyHeroAfterAttack:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        game._damage_hero(game.players[1 - context.player.index], self.amount,
                          context.card)


@dataclass(frozen=True)
class JarHandMinions:
    def execute(self, game: Any, context: RuleContext) -> None:
        from .dragon_mirror import CardDef
        jar_def = CardDef("TLC_841t", "Specimen Jar", "MINION", 1, 0, 1,
                          "", ("DEATHRATTLE",), "DEMONHUNTER", (), "THE_LOST_CITY")
        jarred = []
        for held in list(context.player.hand):
            if held.definition.card_type != "MINION":
                continue
            original = copy.deepcopy(held)
            held.definition = jar_def
            held.attack_delta = held.health_delta = held.damage = 0
            held.taunt = held.rush = held.charge = held.lifesteal = False
            held.elusive = held.divine_shield = held.windfury = held.reborn = False
            held.stealth = held.poisonous = held.immune = False
            held.jarred_minion = original
            jarred.append(original.card_id)
        game._event("jar_hand_minions", player=context.player.index,
                    source=context.card.card_id, cards=jarred)


# ---- Final pinned-Standard closure ----------------------------------------
# These are deliberately small composable effects.  They share the regular
# zone, target and generated-card machinery so the final 48 cards stay valid
# under clone/undo and do not become metadata-only placeholders.


@dataclass(frozen=True)
class ArmShamTrial:
    def execute(self, game: Any, context: RuleContext) -> None:
        # The client flow is not a single duration flag: pick a Trial form,
        # pick two distinct verdict effects, then put the resulting spell in
        # hand. The engine owns the later owner-turn countdown.
        variants = (
            ("CAP_405tb1", 0),  # Rushed: resolves immediately when played.
            ("CAP_405tb2", 1),  # Grueling: start of next own turn.
            ("CAP_405tb3", 4),  # Unending: start of fourth own turn later.
        )
        game.pending_choice = {
            "kind": "RULE_CHOICE", "stage": "SHAM_TRIAL_LENGTH",
            "player": context.player.index, "card": context.card,
            "action": context.action, "trial_variants": variants,
            "options": tuple((game.card_defs[trial_id].name, ())
                             for trial_id, _delay in variants),
        }
        game._event("sham_trial_offer", player=context.player.index,
                    source=context.card.card_id,
                    trials=[trial_id for trial_id, _delay in variants])


@dataclass(frozen=True)
class SplitHundredStatsIfStartingCosts:
    def execute(self, game: Any, context: RuleContext) -> None:
        minions = [card for card in context.player.hand + context.player.deck
                   if card.started_in_deck and card.definition.card_type == "MINION"]
        if sum(card.definition.cost for card in minions) != 100 or not minions:
            return
        for _ in range(100):
            chosen = game.rng.choice(minions)
            if game.rng.randrange(2):
                chosen.attack_delta += 1
            else:
                chosen.health_delta += 1
        game._event("vyranoth_split_stats", player=context.player.index,
                    source=context.card.card_id, recipients=len(minions), total=100)


@dataclass(frozen=True)
class SetHealthAndArmFullHealDamage:
    health: int
    damage: int

    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.health = min(context.player.max_health, self.health)
        context.player.alex_full_heal_damage = self.damage
        game._event("alexstrasza_health_set", player=context.player.index,
                    source=context.card.card_id, health=context.player.health,
                    full_heal_damage=self.damage)


@dataclass(frozen=True)
class CraftUndeadDragon:
    def execute(self, game: Any, context: RuleContext) -> None:
        dragon = _lost_city_token(game, "CATA_470t", "Undead Dragon Creation",
                                  cost=6, attack=5, health=5, race="DRAGON",
                                  mechanics=("DEATHRATTLE",), card_class="DEATHKNIGHT")
        dragon.definition = type(dragon.definition)(
            dragon.definition.card_id, dragon.definition.name, dragon.definition.card_type,
            dragon.definition.cost, dragon.definition.attack, dragon.definition.health,
            "DRAGON", dragon.definition.mechanics, dragon.definition.card_class,
            ("DRAGON", "UNDEAD"), dragon.definition.card_set,
        )
        if game._holding_dragon(context.player):
            dragon.cost_delta -= 3
        game._grant_bonus_effect(context.player, dragon, source=context.card.card_id)
        game._add_generated(context.player, dragon)


@dataclass(frozen=True)
class AddRandomPaladinAura:
    def execute(self, game: Any, context: RuleContext) -> None:
        pool = [card_id for card_id, definition in game.card_defs.items()
                if card_id in game.executable_card_ids and definition.card_type == "SPELL"
                and definition.card_class == "PALADIN" and "aura" in definition.text.casefold()]
        if not pool:
            return
        aura = game._entity(game.rng.choice(sorted(pool)), created_by=context.card.card_id)
        aura.aura_duration_bonus = getattr(aura, "aura_duration_bonus", 0) + 1
        game._add_generated(context.player, aura)
        game._event("paladin_aura_generated", player=context.player.index,
                    source=context.card.card_id, card=aura.card_id, extra_turn=1)


@dataclass(frozen=True)
class PlayTopDeckCards:
    count: int

    def execute(self, game: Any, context: RuleContext) -> None:
        from .dragon_mirror import Action
        played: list[str] = []
        for _ in range(self.count):
            if not context.player.deck:
                break
            card = context.player.deck.pop()
            card.created_by = context.card.card_id
            if card.definition.card_type == "MINION":
                if len(context.player.board) + len(context.player.locations) >= 7:
                    context.player.deck.insert(0, card)
                    break
                card.summoned_turn = game.turn
                game._summon(context.player, card)
                # A top-decked minion is *played* without a UI target picker.
                # When its battlecry is targeted, select only from the rule's
                # legal target pool; with no legal target the battlecry simply
                # fizzles.  Passing `None` through to a targeted implementation
                # used to crash long self-play games on e.g. EDR_031.
                targeting = game.rule_registry.targeting(card.card_id)
                if targeting is None:
                    game._battlecry(context.player, card, Action("PLAY", card.entity_id))
                else:
                    candidates = game._rule_targets(
                        context.player, card, targeting.kind,
                    )
                    if candidates:
                        target_player, target_entity = game.rng.choice(candidates)
                        game._battlecry(
                            context.player, card,
                            Action("PLAY", card.entity_id, target_player, target_entity),
                        )
                    else:
                        game._event(
                            "topdeck_battlecry_no_legal_target",
                            player=context.player.index, card=card.card_id,
                        )
            elif card.definition.card_type == "SPELL":
                candidates = game._random_spell_target_candidates(context.player.index, card)
                action = Action("PLAY", card.entity_id, *candidates[0][:2]) if candidates else Action("PLAY", card.entity_id)
                try:
                    game._cast_spell(context.player, card, action)
                except ValueError:
                    game._event("topdeck_play_target_unavailable", player=context.player.index,
                                card=card.card_id)
            else:
                game._add_generated(context.player, card)
                continue
            played.append(card.card_id)
        game._event("topdeck_cards_played", player=context.player.index,
                    source=context.card.card_id, cards=played)


@dataclass(frozen=True)
class ChooseThriceCenarius:
    def execute(self, game: Any, context: RuleContext) -> None:
        # The client presents three sequential picks.  A seeded random choice
        # is used here only for the unobserved automatic simulation policy;
        # each resulting effect is the real card effect.
        picks = []
        for _ in range(3):
            if game.rng.randrange(2) == 0:
                for minion in context.player.board:
                    if minion.entity_id != context.card.entity_id:
                        minion.attack_delta += 1
                        minion.health_delta += 3
                picks.append("buff")
            elif len(context.player.board) + len(context.player.locations) < 7:
                ancient = _lost_city_token(game, "EDR_209t", "Ancient", cost=5,
                                            attack=5, health=5, mechanics=("TAUNT",),
                                            card_class="DRUID")
                ancient.taunt = True
                ancient.summoned_turn = game.turn
                game._summon(context.player, ancient)
                picks.append("summon")
        game._event("cenarius_choose_thrice", player=context.player.index,
                    source=context.card.card_id, picks=picks)


@dataclass(frozen=True)
class SummonCenariusAncient:
    """Create the 5/5 Taunt token used by the standalone Cenarius option."""

    def execute(self, game: Any, context: RuleContext) -> None:
        if len(context.player.board) + len(context.player.locations) >= 7:
            return
        ancient = _lost_city_token(
            game, "EDR_209t", "Ancient", cost=5, attack=5, health=5,
            mechanics=("TAUNT",), card_class="DRUID",
        )
        ancient.taunt = True
        ancient.summoned_turn = game.turn
        game._summon(context.player, ancient)
        game._event(
            "cenarius_ancient_summoned", player=context.player.index,
            source=context.card.card_id, entity=ancient.entity_id,
        )


@dataclass(frozen=True)
class ShuffleAllMinionsRandomly:
    def execute(self, game: Any, context: RuleContext) -> None:
        moved = []
        for owner in game.players:
            for minion in list(owner.board):
                owner.board.remove(minion)
                destination = game.rng.choice(game.players)
                minion.damage = 0
                minion.summoned_turn = -1
                destination.deck.insert(game.rng.randrange(len(destination.deck) + 1), minion)
                moved.append((minion.card_id, destination.index))
        game._event("typhoon_shuffle_minions", player=context.player.index,
                    source=context.card.card_id, moved=moved)


@dataclass(frozen=True)
class ResurrectDistinctHighCost:
    def execute(self, game: Any, context: RuleContext) -> None:
        seen: set[str] = set()
        summoned = []
        for dead in context.player.dead_minions:
            if dead.definition.cost < 8 or dead.card_id in seen:
                continue
            if len(context.player.board) + len(context.player.locations) >= 7:
                break
            seen.add(dead.card_id)
            revived = dead.clone(game.next_entity_id)
            game.next_entity_id += 1
            revived.damage = 0
            revived.summoned_turn = game.turn
            game._summon(context.player, revived)
            summoned.append(revived.card_id)
        game._event("merithra_resurrect", player=context.player.index,
                    source=context.card.card_id, cards=summoned)


@dataclass(frozen=True)
class CastHighestHandSpellAsAura:
    def execute(self, game: Any, context: RuleContext) -> None:
        from .dragon_mirror import Action
        spells = [card for card in context.player.hand if card.definition.card_type == "SPELL"]
        if not spells:
            return
        spell = max(spells, key=lambda card: (card.cost, card.entity_id))
        context.player.hand.remove(spell)
        spell.aura_remaining_turns = 3
        context.card.stored_spell = copy.deepcopy(spell)
        context.card.aura_remaining_turns = 3
        candidates = game._random_spell_target_candidates(context.player.index, spell)
        action = Action("PLAY", spell.entity_id, *candidates[0][:2]) if candidates else Action("PLAY", spell.entity_id)
        try:
            game._cast_spell(context.player, spell, action)
        except ValueError:
            pass
        game._event("ursol_aura_cast", player=context.player.index,
                    source=context.card.card_id, spell=spell.card_id, turns=3)


@dataclass(frozen=True)
class ArmOpponentHealthCost:
    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.next_card_uses_opponent_health = True
        game._event("opponent_health_cost_armed", player=context.player.index,
                    source=context.card.card_id, cap=10)


@dataclass(frozen=True)
class GainDeadDeathrattleMarkers:
    def execute(self, game: Any, context: RuleContext) -> None:
        inherited = [dead.card_id for dead in context.player.dead_minions
                     if dead.died_turn == game.turn and "DEATHRATTLE" in dead.definition.mechanics]
        context.card.inherited_deathrattles = tuple(inherited)
        game._event("archdruid_inherit_deathrattles", player=context.player.index,
                    source=context.card.card_id, cards=inherited)


@dataclass(frozen=True)
class EatDeckMinionGainStats:
    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [card for card in context.player.deck if card.definition.card_type == "MINION"]
        if not candidates:
            return
        eaten = game.rng.choice(candidates)
        context.player.deck.remove(eaten)
        context.card.attack_delta += eaten.attack
        context.card.health_delta += eaten.max_health
        context.card.eaten_deck_minion = copy.deepcopy(eaten)
        game._event("hungering_ancient_eat", player=context.player.index,
                    source=context.card.entity_id, card=eaten.card_id)


@dataclass(frozen=True)
class DiscoverSpellKeepOrTopdeckEnemy:
    def execute(self, game: Any, context: RuleContext) -> None:
        pool = _filtered_executable_ids(game, card_type="SPELL")
        game._offer_discover(context.player, pool, False,
                             source_card_id=context.card.card_id)


@dataclass(frozen=True)
class OpponentDrawCopies:
    count: int

    def execute(self, game: Any, context: RuleContext) -> None:
        enemy = game.players[1 - context.player.index]
        for _ in range(self.count):
            if not enemy.deck:
                game._draw(enemy)
                continue
            card = enemy.deck[-1]
            copy_card = card.clone(game.next_entity_id)
            game.next_entity_id += 1
            copy_card.copied_from_opponent = True
            copy_card.created_by = context.card.card_id
            game._draw(enemy)
            game._add_generated(context.player, copy_card)


@dataclass(frozen=True)
class TrapRandomEnemyHandCard:
    def execute(self, game: Any, context: RuleContext) -> None:
        enemy = game.players[1 - context.player.index]
        if not enemy.hand:
            return
        target = game.rng.choice(enemy.hand)
        target.locked_until_card_played = True
        target.trapped_until_turn = game.turn + 2
        game._event("renferal_trap", player=context.player.index,
                    source=context.card.card_id, target=target.entity_id)


@dataclass(frozen=True)
class FillHandEnemyDeckCopies:
    def execute(self, game: Any, context: RuleContext) -> None:
        enemy = game.players[1 - context.player.index]
        for card in list(enemy.deck):
            if len(context.player.hand) >= 10:
                break
            copied = card.clone(game.next_entity_id)
            game.next_entity_id += 1
            copied.copied_from_opponent = True
            copied.cost_delta -= 3
            copied.created_by = context.card.card_id
            context.player.hand.append(copied)


@dataclass(frozen=True)
class TransformNeutralDeckToDruid:
    def execute(self, game: Any, context: RuleContext) -> None:
        pool = [card_id for card_id, definition in game.card_defs.items()
                if card_id in game.executable_card_ids and definition.card_class == "DRUID"]
        if not pool:
            return
        transformed = 0
        for index, card in enumerate(list(context.player.deck)):
            if card.definition.card_class != "NEUTRAL":
                continue
            replacement = game._entity(game.rng.choice(pool), created_by=context.card.card_id)
            replacement.started_in_deck = card.started_in_deck
            context.player.deck[index] = replacement
            transformed += 1
        game._event("envoy_transform_deck", player=context.player.index,
                    source=context.card.card_id, count=transformed)


@dataclass(frozen=True)
class StartLunarCycle:
    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.lunar_cycle_turns = 3
        game._event("lunar_cycle_started", player=context.player.index,
                    source=context.card.card_id, turns=3)


@dataclass(frozen=True)
class StealBonusEffects:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("enemy minion target is required")
        target = game._find_minion(context.action.target_player, context.action.target_entity)
        effects = list(target.gifts)
        target.gifts.clear()
        for effect in effects:
            game._apply_dark_gift(context.card, effect, owner=context.player)
        context.card.attack_delta += len(effects)
        context.card.health_delta += len(effects)


@dataclass(frozen=True)
class ApplyDarkGiftToActionTarget:
    """Apply one concrete Dark Gift option to a friendly minion.

    Dark Gifts normally resolve as the second half of a Discover, where the
    game calls ``_apply_dark_gift`` directly.  The option entities also occur
    in replay data, however, so they need the same authoritative path when
    dispatched as cards rather than a hand-written approximation.
    """

    gift: str

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player != context.player.index:
            raise ValueError("friendly minion target is required for a Dark Gift")
        target = game._find_minion(context.player.index, context.action.target_entity)
        if self.gift not in game._eligible_dark_gifts(target):
            # A copied spell resolves its second cast against the *current*
            # board.  If its original target just received an exclusive
            # keyword Gift, that target is no longer legal and this cast
            # fizzles rather than throwing or double-granting the Gift.
            game._event(
                "dark_gift_no_longer_eligible", player=context.player.index,
                source=context.card.card_id, target=target.entity_id, gift=self.gift,
            )
            return
        game._apply_dark_gift(target, self.gift, owner=context.player)
        game._event(
            "dark_gift_option", player=context.player.index,
            source=context.card.card_id, target=target.entity_id, gift=self.gift,
        )


@dataclass(frozen=True)
class ApplyKeywordPackageToActionTarget:
    """Apply a Blinding Carapace keyword pair to a friendly minion.

    The 15 token IDs encode every unordered pair from the five keyword pool.
    Applying through a tuple makes the combinations auditable and guarantees
    that a shield created by the option gets its regular single-hit counter.
    """

    keywords: tuple[str, str]

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player != context.player.index:
            raise ValueError("friendly minion target is required for Blinding Carapace")
        target = game._find_minion(context.player.index, context.action.target_entity)
        for keyword in self.keywords:
            if keyword == "DIVINE_SHIELD":
                target.divine_shield = True
                target.divine_shield_hits = max(1, target.divine_shield_hits)
            elif keyword == "RUSH":
                target.rush = True
            elif keyword == "LIFESTEAL":
                target.lifesteal = True
            elif keyword == "REBORN":
                target.reborn = True
            elif keyword == "TAUNT":
                target.taunt = True
            elif keyword == "POISONOUS":
                target.poisonous = True
            else:
                raise ValueError(f"unsupported Blinding Carapace keyword: {keyword}")
        game._event(
            "blinding_carapace", player=context.player.index,
            source=context.card.card_id, target=target.entity_id,
            keywords=list(self.keywords),
        )


@dataclass(frozen=True)
class OfferEnemyHandDiscardOnDeath:
    def execute(self, game: Any, context: RuleContext) -> None:
        enemy = game.players[1 - context.player.index]
        options = game.rng.sample(enemy.hand, min(3, len(enemy.hand)))
        context.card.trapped_enemy_entity = game.rng.choice(options).entity_id if options else None
        game._event("ancient_augur_mark", player=context.player.index,
                    source=context.card.entity_id, target=context.card.trapped_enemy_entity)


@dataclass(frozen=True)
class TransformHandCardToCostPlusSpell:
    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [card for card in context.player.hand if card.entity_id != context.card.entity_id]
        if not candidates:
            return
        held = game.rng.choice(candidates)
        pool = _filtered_executable_ids(game, card_type="SPELL", cost=held.cost + 5)
        if not pool:
            return
        replacement = game._entity(game.rng.choice(pool), created_by=context.card.card_id)
        replacement.entity_id = held.entity_id
        replacement.cost_delta += held.cost - replacement.cost
        context.player.hand[context.player.hand.index(held)] = replacement


@dataclass(frozen=True)
class ShootRandomEnemy:
    def execute(self, game: Any, context: RuleContext) -> None:
        shots = 1 + 2 * context.player.played_card_counts.get(context.card.card_id, 0)
        for _ in range(shots):
            targets = game._random_enemy_characters(context.player.index)
            if not targets:
                break
            game._deal_to_target(context.player.index, game.rng.choice(targets), 1, context.card)
        game._resolve_deaths()


@dataclass(frozen=True)
class GrantAllLeylinesAndUpgrade:
    def execute(self, game: Any, context: RuleContext) -> None:
        for card_id in ("MEND_500", "MEND_502", "MEND_504"):
            game._add_generated(context.player, game._entity(card_id, created_by=context.card.card_id))
        context.player.leyline_upgrade += 1
        game._event("arcanomicon_leylines", player=context.player.index,
                    source=context.card.card_id, upgrade=context.player.leyline_upgrade)


@dataclass(frozen=True)
class SplitRandomHandMinion:
    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [card for card in context.player.hand if card.definition.card_type == "MINION"]
        if not candidates or len(context.player.hand) >= 10:
            return
        original = game.rng.choice(candidates)
        clone = original.clone(game.next_entity_id)
        game.next_entity_id += 1
        original.attack_delta -= original.attack // 2
        clone.attack_delta -= clone.attack - original.attack
        original.health_delta -= original.max_health // 2
        clone.health_delta -= clone.max_health - original.max_health
        clone.created_by = context.card.card_id
        context.player.hand.append(clone)


@dataclass(frozen=True)
class GuessEnemyHandGainHealth:
    def execute(self, game: Any, context: RuleContext) -> None:
        enemy_ids = {card.card_id for card in game.players[1 - context.player.index].hand}
        options = game.rng.sample(list(context.player.hand + context.player.deck),
                                  min(3, len(context.player.hand + context.player.deck)))
        if any(card.card_id in enemy_ids for card in options):
            context.card.health_delta += 4


@dataclass(frozen=True)
class RestoreStartingHandUntilEndTurn:
    def execute(self, game: Any, context: RuleContext) -> None:
        current = list(context.player.hand)
        context.player.hand = [card.clone(game.next_entity_id + i)
                               for i, card in enumerate(context.player.starting_hand_snapshot)]
        game.next_entity_id += len(context.player.hand)
        # The replacement survives if Fins is removed before the end step.
        context.player.fins_restore_hand = current
        game._event("fins_replace_hand", player=context.player.index,
                    source=context.card.card_id, cards=[card.card_id for card in context.player.hand])


@dataclass(frozen=True)
class DealTwentyIfFriendlyDeaths:
    def execute(self, game: Any, context: RuleContext) -> None:
        if len(context.player.dead_minions) < 20:
            return
        targets = game._random_enemy_characters(context.player.index)
        for _ in range(20):
            if not targets:
                break
            game._deal_to_target(context.player.index, game.rng.choice(targets), 1, context.card)
        game._resolve_deaths()


@dataclass(frozen=True)
class AttackAllOtherMinions:
    def execute(self, game: Any, context: RuleContext) -> None:
        killed = []
        for owner in game.players:
            for target in list(owner.board):
                if target.entity_id == context.card.entity_id or context.card.health <= 0:
                    continue
                before = target.health
                game._forced_minion_attack(context.player.index, context.card, owner.index, target)
                if before > 0 and target.health <= 0:
                    killed.append(copy.deepcopy(target))
        context.card.killed_by_ursoc = killed
        game._resolve_deaths()


@dataclass(frozen=True)
class ReplayOtherSpellsAndEndTurn:
    def execute(self, game: Any, context: RuleContext) -> None:
        from .dragon_mirror import Action
        for spell in list(context.player.spells_this_turn_for_replay):
            replay = copy.deepcopy(spell)
            candidates = game._random_spell_target_candidates(context.player.index, replay)
            action = Action("PLAY", replay.entity_id, *candidates[0][:2]) if candidates else Action("PLAY", replay.entity_id)
            try:
                game._cast_spell(context.player, replay, action)
            except ValueError:
                continue
        context.player.force_end_turn = True
        game._event("slice_and_dice_replay", player=context.player.index,
                    source=context.card.card_id)


@dataclass(frozen=True)
class OfferChooseOneAndCopyEnemy:
    def execute(self, game: Any, context: RuleContext) -> None:
        pool = [card_id for card_id, definition in game.card_defs.items()
                if card_id in game.executable_card_ids and "choose one" in definition.text.casefold()]
        game._offer_discover(context.player, pool, False, source_card_id=context.card.card_id)
        if game.pending_choice is not None:
            game.pending_choice["copy_choice_to_enemy"] = True


@dataclass(frozen=True)
class AddBulb:
    def execute(self, game: Any, context: RuleContext) -> None:
        bulb = _lost_city_token(game, "MEND_100t", "Prismatic Bulb", cost=3,
                                attack=0, health=1, card_class="NEUTRAL")
        bulb.bulb_spell_count = 3
        bulb.bulb_upgrade = 0
        game._add_generated(context.player, bulb)


@dataclass(frozen=True)
class DrawPlayedCardCopy:
    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [card for card in context.player.deck
                      if context.player.played_card_counts.get(card.card_id, 0)]
        if candidates:
            game._draw_matching(context.player, lambda card: card in candidates)


@dataclass(frozen=True)
class ArmSpellSurchargeTwoEnemyTurns:
    def execute(self, game: Any, context: RuleContext) -> None:
        opponent = game.players[1 - context.player.index]
        opponent.spell_cost_surcharge = max(opponent.spell_cost_surcharge, 1)
        opponent.spell_cost_surcharge_turn = game.turn + 3
        game._event("resistance_aura", player=context.player.index,
                    opponent=opponent.index, turns=2)


@dataclass(frozen=True)
class OpenStandardPackAndPlay:
    """Open a bounded Standard pack and play its cards immediately.

    The live game has a collectible-pack generator.  The simulator keeps the
    same observable rule (five independently generated Standard cards are
    played) while drawing from its executable Standard closure, so it never
    manufactures a metadata-only card during search.
    """
    count: int = 5

    def execute(self, game: Any, context: RuleContext) -> None:
        from .dragon_mirror import Action, Weapon
        pool = [card_id for card_id in game.executable_card_ids
                if card_id in game.card_defs
                and game.card_defs[card_id].card_set != "GENERATED"]
        game.rng.shuffle(pool)
        played: list[str] = []
        for card_id in pool[:self.count]:
            card = game._entity(card_id, created_by=context.card.card_id)
            if card.definition.card_type == "MINION":
                if len(context.player.board) + len(context.player.locations) >= 7:
                    break
                target_spec = game.rule_registry.targeting(card.card_id)
                targets = (
                    game._rule_targets(context.player, card, target_spec.kind)
                    if target_spec is not None else []
                )
                if target_spec is not None and not targets and not target_spec.optional:
                    # A generated battlecry that needs a target cannot be
                    # played when the random pack did not also provide one.
                    continue
                target = targets[0] if targets else (None, None)
                card.summoned_turn = game.turn
                game._summon(context.player, card)
                game._battlecry(
                    context.player, card,
                    Action("PLAY", card.entity_id, target[0], target[1]),
                )
            elif card.definition.card_type == "SPELL":
                candidates = game._random_spell_target_candidates(context.player.index, card)
                action = Action("PLAY", card.entity_id, *candidates[0][:2]) if candidates else Action("PLAY", card.entity_id)
                try:
                    game._cast_spell(context.player, card, action)
                except ValueError:
                    continue
            elif card.definition.card_type == "WEAPON":
                game._equip_weapon(
                    context.player,
                    Weapon(card.card_id, card.definition.name, card.definition.attack,
                           max(1, card.definition.health)),
                )
            else:
                continue
            played.append(card.card_id)
        game._event("standard_pack_opened", player=context.player.index,
                    source=context.card.card_id, cards=played)


@dataclass(frozen=True)
class GrantDeathrattleBuffAllFriendly:
    attack: int
    health: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player != context.player.index:
            raise ValueError("friendly minion target is required")
        target = game._find_minion(context.player.index, context.action.target_entity)
        target.deathrattle_friendly_buff = (self.attack, self.health)
        game._event("amphibian_spirit_blessing", player=context.player.index,
                    source=context.card.entity_id, target=target.entity_id,
                    attack=self.attack, health=self.health)


@dataclass(frozen=True)
class SummonRandomMinionMatchingSpellCost:
    def execute(self, game: Any, context: RuleContext) -> None:
        spell = context.payload.get("spell")
        if spell is None:
            return
        game._summon_random_executable_minion(
            context.player, source_card_id=context.card.card_id, cost=spell.cost,
        )


@dataclass(frozen=True)
class BuffPlayedBattlecryMinion:
    attack: int = 1
    health: int = 1

    def execute(self, game: Any, context: RuleContext) -> None:
        played = context.payload.get("played")
        if (
            played is None
            or played.definition.card_type != "MINION"
            or "BATTLECRY" not in played.definition.mechanics
            or played.health <= 0
        ):
            return
        played.attack_delta += self.attack
        played.health_delta += self.health
        game._event("gallagio_goon_buff", player=context.player.index,
                    source=context.card.entity_id, target=played.entity_id,
                    attack=self.attack, health=self.health)


@dataclass(frozen=True)
class EquipRunebladeBonus:
    """Resolve Grotesque Runeblade from the previous card's rune metadata."""
    def execute(self, game: Any, context: RuleContext) -> None:
        prior = getattr(context.player, "previous_played_card_id", None)
        if not prior or prior not in game.card_defs or context.player.weapon is None:
            return
        definition = game.card_defs[prior]
        text = definition.text.casefold()
        # JSON exposes rune requirements in the printed text for this
        # snapshot; recognises all three rune words, with unholy only adding
        # attack and blood only adding durability as specified.
        if "unholy" in text:
            context.player.weapon.attack += 1
        if "blood" in text:
            context.player.weapon.durability += 1
        game._event("grotesque_runeblade_bonus", player=context.player.index,
                    source=context.card.card_id, prior=prior,
                    attack=context.player.weapon.attack,
                    durability=context.player.weapon.durability)


@dataclass(frozen=True)
class StealEnemyHandCardsEnteredThisTurn:
    def execute(self, game: Any, context: RuleContext) -> None:
        enemy = game.players[1 - context.player.index]
        stolen: list[str] = []
        for card in list(enemy.hand):
            if getattr(card, "entered_hand_turn", -1) != game.turn:
                continue
            enemy.hand.remove(card)
            if len(context.player.hand) < 10:
                context.player.hand.append(card)
                stolen.append(card.card_id)
            else:
                game._event("burn", player=context.player.index,
                            card=card.card_id, entity=card.entity_id,
                            source=context.card.card_id)
        game._event("rat_burglar_steal", player=context.player.index,
                    source=context.card.entity_id, cards=stolen)


_FINAL_48_SOURCE = RuleSource(
    "official_text_and_engine_pattern", "HearthstoneJSON 251332",
    verification=(
        "FinalStandardClosureTests.test_final_48_registry_and_smoke",
        "FinalStandardClosureTests.test_final_48_stateful_effects",
    ),
)

_AUXILIARY_TOKEN_SOURCE = RuleSource(
    "official_text_and_engine_pattern", "HearthstoneJSON 251332",
    verification=(
        "AuxiliaryEntityCoverageTests.test_every_coin_variant_grants_temporary_mana",
        "AuxiliaryEntityCoverageTests.test_engine_owned_auxiliaries_are_executable",
    ),
)

_EVENT_BLOCKER_SOURCE = RuleSource(
    "official_text_and_engine_pattern", "HearthstoneJSON 251332",
    verification=("EventCardRegressionTests.test_event_blockers",),
)


_BATCH_50_SOURCE = RuleSource(
    "official_text_and_engine_pattern", "HearthstoneJSON 251332",
    verification=("test_standard_batch_50_registry_and_smoke",),
)

_BATCH_50B_SOURCE = RuleSource(
    "official_text_and_engine_pattern", "HearthstoneJSON 251332",
    verification=(
        "SecondStandardCardBatchTests.test_batch_has_exactly_fifty_registered_cards",
        "SecondStandardCardBatchTests.test_tar_tyrant_attack_bonus_tracks_opponent_turn",
        "SecondStandardCardBatchTests.test_maloriak_and_story_of_lakkari_cross_turn_hooks",
    ),
)

_BATCH_50C_SOURCE = RuleSource(
    "official_text_and_engine_pattern", "HearthstoneJSON 251332",
    verification=(
        "ThirdStandardCardBatchTests.test_batch_has_exactly_fifty_registered_cards",
        "ThirdStandardCardBatchTests.test_cost_windows_and_hero_power_triggers",
        "ThirdStandardCardBatchTests.test_blob_hounds_and_conditional_attack",
    ),
)


_BATCH_50D_SOURCE = RuleSource(
    "official_text_and_engine_pattern", "HearthstoneJSON 251332",
    verification=(
        "FourthStandardCardBatchTests.test_batch_has_exactly_fifty_registered_cards",
        "FourthStandardCardBatchTests.test_cost_reductions_and_generated_cards",
        "FourthStandardCardBatchTests.test_deathrattle_and_delayed_windows",
    ),
)


_BATCH_50E_SOURCE = RuleSource(
    "official_text_and_engine_pattern", "HearthstoneJSON 251332",
    verification=(
        "FifthStandardCardBatchTests.test_batch_has_exactly_fifty_registered_cards",
        "FifthStandardCardBatchTests.test_shreds_and_time_summons",
        "FifthStandardCardBatchTests.test_past_discover_and_time_state",
    ),
)


_BATCH_50F_SOURCE = RuleSource(
    "official_text_and_engine_pattern", "HearthstoneJSON 251332",
    verification=(
        "SixthStandardCardBatchTests.test_batch_has_exactly_fifty_registered_cards",
        "SixthStandardCardBatchTests.test_cataclysm_persistent_state_and_tokens",
        "SixthStandardCardBatchTests.test_animal_companion_and_recruit_package",
    ),
)


_BATCH_50G_SOURCE = RuleSource(
    "official_text_and_engine_pattern", "HearthstoneJSON 251332",
    verification=(
        "SeventhStandardCardBatchTests.test_batch_has_exactly_fifty_registered_cards",
        "SeventhStandardCardBatchTests.test_masks_and_druid_state_rules",
        "SeventhStandardCardBatchTests.test_resurrect_transform_and_cost_rules",
    ),
)


_BATCH_50H_SOURCE = RuleSource(
    "official_text_and_engine_pattern", "HearthstoneJSON 251332",
    verification=(
        "EighthStandardCardBatchTests.test_batch_has_exactly_fifty_registered_cards",
        "EighthStandardCardBatchTests.test_deck_secret_and_discover_rules",
        "EighthStandardCardBatchTests.test_damage_deathrattle_and_hand_rules",
    ),
)


_BATCH_50I_SOURCE = RuleSource(
    "official_text_and_engine_pattern", "HearthstoneJSON 251332",
    verification=(
        "NinthStandardCardBatchTests.test_batch_has_exactly_fifty_registered_cards",
        "NinthStandardCardBatchTests.test_lost_city_token_and_deck_rules",
        "NinthStandardCardBatchTests.test_lost_city_combat_and_persistent_rules",
    ),
)

_FINAL_STANDARD_SOURCE = RuleSource(
    "official_text_and_engine_pattern", "HearthstoneJSON 251332",
    verification=(
        "FinalStandardClosureTests.test_all_final_collectibles_registered",
        "FinalStandardClosureTests.test_cross_turn_and_zone_effects",
    ),
)


# ---- Standard tranche 50D -------------------------------------------------
# These helpers intentionally express card text in terms of the shared engine
# primitives.  The random pools are derived from the executable card catalogue
# rather than a hand-maintained list, so a later verified card migration joins
# Discover/random-generation pools automatically.


def _filtered_executable_ids(
    game: Any,
    *,
    card_type: str | None = None,
    cost: int | None = None,
    min_cost: int | None = None,
    race: str | None = None,
    spell_school: str | None = None,
    card_class: str | None = None,
    other_class_for: Any | None = None,
    mechanic: str | None = None,
    exclude_card_set: str | None = None,
    collectible_only: bool = False,
) -> list[str]:
    """Return a stable, runtime-safe random/Discover pool.

    This keeps all batch-50D pools inside the simulator's executable closure;
    metadata-only cards cannot be created merely because their JSON exists.
    """
    result: list[str] = []
    for card_id, definition in game.card_defs.items():
        if card_id not in game.executable_card_ids:
            continue
        if collectible_only and not definition.collectible:
            continue
        if card_type is not None and definition.card_type != card_type:
            continue
        if cost is not None and definition.cost != cost:
            continue
        if min_cost is not None and definition.cost < min_cost:
            continue
        if race is not None and race not in definition.races and definition.race != race:
            continue
        if spell_school is not None and definition.spell_school != spell_school:
            continue
        if card_class is not None and definition.card_class != card_class:
            continue
        if other_class_for is not None and (
            definition.card_class in {"", "NEUTRAL", other_class_for.card_class}
        ):
            continue
        if mechanic is not None:
            # The printed word can occur in another card's text (for example
            # a Battlecry that triggers a token's Deathrattle).  For a
            # Discover filter that is not the card's own mechanic, that is a
            # false positive; prefer the structured mechanic tag for the
            # Deathrattle pool and retain the text fallback for legacy tags.
            if mechanic == "DEATHRATTLE":
                if mechanic not in definition.mechanics:
                    continue
            elif (
                mechanic not in definition.mechanics
                and mechanic.casefold() not in definition.text.casefold()
            ):
                continue
        if exclude_card_set is not None and definition.card_set == exclude_card_set:
            continue
        result.append(card_id)
    return sorted(result)


@dataclass(frozen=True)
class OfferFilteredDiscover:
    card_type: str | None = None
    cost: int | None = None
    race: str | None = None
    spell_school: str | None = None
    mechanic: str | None = None
    other_class: bool = False
    dark_gift: bool = False

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = _filtered_executable_ids(
            game,
            card_type=self.card_type,
            cost=self.cost,
            race=self.race,
            spell_school=self.spell_school,
            mechanic=self.mechanic,
            other_class_for=context.player if self.other_class else None,
        )
        if candidates:
            game._offer_discover(
                context.player, candidates, self.dark_gift,
                source_card_id=context.card.card_id,
            )


@dataclass(frozen=True)
class AddRandomFilteredCards:
    count: int = 1
    card_type: str | None = None
    cost: int | None = None
    race: str | None = None
    spell_school: str | None = None
    card_class: str | None = None
    other_class: bool = False
    mechanic: str | None = None

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = _filtered_executable_ids(
            game,
            card_type=self.card_type,
            cost=self.cost,
            race=self.race,
            spell_school=self.spell_school,
            card_class=self.card_class,
            other_class_for=context.player if self.other_class else None,
            mechanic=self.mechanic,
        )
        for _ in range(self.count):
            if not candidates:
                break
            generated = game._entity(
                game.rng.choice(candidates), created_by=context.card.card_id,
            )
            game._add_generated(context.player, generated)


@dataclass(frozen=True)
class AddRandomOtherClassSpellDiscount:
    """Soldier of Sinestra's on-summon random off-class spell."""

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = _filtered_executable_ids(
            game, card_type="SPELL", other_class_for=context.player,
        )
        if not candidates:
            return
        generated = game._entity(
            game.rng.choice(candidates), created_by=context.card.card_id,
        )
        discount = max(0, int(getattr(context.card, "herald_power", 1)))
        generated.cost_delta -= discount
        destination = game._add_generated(context.player, generated)
        game._event(
            "sinestra_soldier_spell", player=context.player.index,
            source=context.card.entity_id, card=generated.card_id,
            discount=discount, destination=destination,
        )


@dataclass(frozen=True)
class CastRandomExecutableSpells:
    """Cast a bounded number of random executable spells without mana cost."""

    count: int
    cost: int

    def execute(self, game: Any, context: RuleContext) -> None:
        from .dragon_mirror import Action

        pool = _filtered_executable_ids(
            game, card_type="SPELL", cost=self.cost,
        )
        cast: list[str] = []
        for _ in range(self.count):
            if not pool:
                break
            spell = game._entity(
                game.rng.choice(pool), created_by=context.card.card_id,
            )
            # A generated spell must obey the same target contract as a card
            # played from hand.  Do not attempt a target-free resolution for
            # a required-target spell: some legacy fallback resolvers index
            # the target immediately, and that used to turn a valid random
            # cast (for example Torch) into a TypeError.
            target_spec = game.rule_registry.targeting(spell.card_id)
            if target_spec is not None and not target_spec.optional:
                candidates = game._random_spell_target_candidates(
                    context.player.index, spell
                )
                if not candidates:
                    continue
                target_player, target_entity, _ = candidates[0]
                try:
                    game._cast_spell(
                        context.player, spell,
                        Action("PLAY", spell.entity_id, target_player, target_entity),
                    )
                except ValueError:
                    continue
                cast.append(spell.card_id)
                continue
            # For target-free and optional-target spells, retain a no-target
            # attempt first.  If it is illegal, choose from current legal
            # candidates rather than fabricating an entity.
            try:
                game._cast_spell(context.player, spell, Action("PLAY", spell.entity_id))
            except ValueError:
                for target_player, target_entity, _ in game._random_spell_target_candidates(
                    context.player.index, spell
                ):
                    try:
                        game._cast_spell(
                            context.player, spell,
                            Action("PLAY", spell.entity_id, target_player, target_entity),
                        )
                        break
                    except ValueError:
                        continue
                else:
                    continue
            cast.append(spell.card_id)
        game._event(
            "random_spells_cast", player=context.player.index,
            source=context.card.card_id, cost=self.cost, cards=cast,
        )


@dataclass(frozen=True)
class CastRandomFireSpellsMana:
    """Cast random Fire spells until the printed-mana budget is exhausted."""

    budget: int = 15

    def execute(self, game: Any, context: RuleContext) -> None:
        from .dragon_mirror import Action

        pool = [
            card_id for card_id, definition in game.card_defs.items()
            if card_id in game.executable_card_ids
            and definition.card_type == "SPELL"
            and definition.spell_school == "FIRE"
            and definition.cost > 0
            and definition.cost <= self.budget
        ]
        remaining = self.budget
        cast: list[str] = []
        attempts = 0
        while pool and remaining > 0 and attempts < self.budget * 3:
            attempts += 1
            eligible = [
                card_id for card_id in pool
                if game.card_defs[card_id].cost <= remaining
            ]
            if not eligible:
                break
            card_id = game.rng.choice(sorted(eligible))
            spell = game._entity(card_id, created_by=context.card.card_id)
            resolved = False
            try:
                game._cast_spell(context.player, spell, Action("PLAY", spell.entity_id))
                resolved = True
            except ValueError:
                candidates = [
                    (target_player, target_entity)
                    for target_player, target_entity, _ in
                    game._random_spell_target_candidates(context.player.index, spell)
                    if target_player != context.player.index
                ]
                game.rng.shuffle(candidates)
                for target_player, target_entity in candidates:
                    try:
                        game._cast_spell(
                            context.player, spell,
                            Action("PLAY", spell.entity_id,
                                   target_player, target_entity),
                        )
                        resolved = True
                        break
                    except ValueError:
                        continue
            if resolved:
                cast.append(card_id)
                remaining -= game.card_defs[card_id].cost
            else:
                pool.remove(card_id)
        game._event(
            "fyrakk_fire_barrage", player=context.player.index,
            source=context.card.entity_id, budget=self.budget,
            spent=self.budget - remaining, cards=cast,
        )


# ---- Standard tranche 50E -------------------------------------------------
# Taverns of Time repeatedly refers to cards "from the past".  This is not a
# hard-coded expansion list: the pool is every executable card outside the
# current TIME_TRAVEL set, so verified migrations automatically become legal
# future candidates without changing any individual Time card.


def _past_ids(game: Any, **filters: Any) -> list[str]:
    # "From the past" refers to historical cards, not generated tokens or
    # engine-only entities whose metadata happens to predate TIME_TRAVEL.
    # Keep this default centralized so a newly added past effect cannot
    # accidentally reintroduce token candidates; callers may explicitly
    # override it if a future card text requires a broader pool.
    filters.setdefault("collectible_only", True)
    return _filtered_executable_ids(
        game, exclude_card_set="TIME_TRAVEL", **filters,
    )


@dataclass(frozen=True)
class ShuffleShredsOfTime:
    count: int = 2

    def execute(self, game: Any, context: RuleContext) -> None:
        for _ in range(self.count):
            shred = game._entity("TIME_025t", created_by=context.card.card_id)
            shred.started_in_deck = False
            context.player.deck.insert(
                game.rng.randrange(len(context.player.deck) + 1), shred,
            )
        game._event(
            "shred_of_time_shuffled", player=context.player.index,
            source=context.card.card_id, count=self.count,
        )


@dataclass(frozen=True)
class CastShredFromDeck:
    gain_source_stats: tuple[int, int] = ()
    summon_source_copy: bool = False

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [card for card in context.player.deck if card.card_id == "TIME_025t"]
        if not candidates:
            game._event("shred_of_time_unavailable", player=context.player.index,
                        source=context.card.card_id)
            return
        shred = game.rng.choice(candidates)
        context.player.deck.remove(shred)
        game._damage_hero(context.player, 3, shred)
        if self.gain_source_stats:
            attack, health = self.gain_source_stats
            context.card.attack_delta += attack
            context.card.health_delta += health
        if self.summon_source_copy and len(context.player.board) + len(context.player.locations) < 7:
            copy_card = context.card.clone(game.next_entity_id)
            game.next_entity_id += 1
            copy_card.created_by = context.card.card_id
            copy_card.summoned_turn = game.turn
            game._summon(context.player, copy_card)
        game._event(
            "shred_of_time_cast", player=context.player.index,
            source=context.card.entity_id, shred=shred.entity_id,
            gain=list(self.gain_source_stats), copied=self.summon_source_copy,
        )


@dataclass(frozen=True)
class OfferPastDiscover:
    card_type: str | None = None
    cost: int | None = None
    min_cost: int | None = None
    race: str | None = None
    spell_school: str | None = None
    card_class: str | None = None
    repeats: int = 1
    after_pick: str | None = None

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = _past_ids(
            game, card_type=self.card_type, cost=self.cost,
            min_cost=self.min_cost, race=self.race,
            spell_school=self.spell_school, card_class=self.card_class,
            collectible_only=True,
        )
        if candidates:
            game._offer_discover(
                context.player, candidates, dark_gift=False,
                repeats=self.repeats, after_pick=self.after_pick,
                source_card_id=context.card.card_id,
            )


@dataclass(frozen=True)
class AddRandomPast:
    card_type: str | None = None
    cost: int | None = None
    race: str | None = None
    count: int = 1

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = _past_ids(
            game, card_type=self.card_type, cost=self.cost, race=self.race,
            collectible_only=True,
        )
        for _ in range(self.count):
            if not candidates:
                return
            generated = game._entity(game.rng.choice(candidates), created_by=context.card.card_id)
            game._add_generated(context.player, generated)


@dataclass(frozen=True)
class SummonRandomPast:
    cost: int | None = None
    count: int = 1

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = _past_ids(
            game, card_type="MINION", cost=self.cost, collectible_only=True,
        )
        for _ in range(self.count):
            if not candidates or len(context.player.board) + len(context.player.locations) >= 7:
                break
            minion = game._entity(game.rng.choice(candidates), created_by=context.card.card_id)
            minion.summoned_turn = game.turn
            game._summon(context.player, minion)


@dataclass(frozen=True)
class ShuffleShredsAfter:
    effects: tuple[Effect, ...]

    def execute(self, game: Any, context: RuleContext) -> None:
        for effect in self.effects:
            effect.execute(game, context)
        ShuffleShredsOfTime().execute(game, context)


@dataclass(frozen=True)
class RoyalInformantBattlecry:
    def execute(self, game: Any, context: RuleContext) -> None:
        opponent = game.players[1 - context.player.index]
        if not opponent.hand:
            return
        target = opponent.hand[-1]
        game.pending_choice = {
            "kind": "RULE_CHOICE", "stage": "ROYAL_INFORMANT",
            "player": context.player.index, "card": context.card,
            "target_entity": target.entity_id,
            "options": (("Copy it", ()), ("Increase its Cost by (2)", ())),
        }
        game._event(
            "royal_informant_offer", player=context.player.index,
            source=context.card.entity_id, target=target.entity_id,
            card=target.card_id,
        )


@dataclass(frozen=True)
class IncreaseRightmostOpponentCardCost:
    """Resolve Royal Informant's explicit cost-increase option."""

    amount: int = 2

    def execute(self, game: Any, context: RuleContext) -> None:
        opponent = game.players[1 - context.player.index]
        if not opponent.hand:
            return
        target = opponent.hand[-1]
        target.cost_delta += self.amount
        game._event(
            "royal_informant_cost_increase", player=context.player.index,
            source=context.card.card_id, target=target.entity_id,
            card=target.card_id, amount=self.amount,
        )


@dataclass(frozen=True)
class TransformSourceIntoRandomPast:
    cost: int

    def execute(self, game: Any, context: RuleContext) -> None:
        source = context.card
        owner = context.player
        if source not in owner.board or source.health <= 0:
            return
        candidates = _past_ids(
            game, card_type="MINION", cost=self.cost, collectible_only=True,
        )
        if not candidates:
            return
        replacement = game._entity(game.rng.choice(candidates), created_by=source.card_id)
        replacement.entity_id = source.entity_id
        replacement.summoned_turn = source.summoned_turn
        owner.board[owner.board.index(source)] = replacement
        game._event(
            "time_transform", player=owner.index, source=source.card_id,
            entity=source.entity_id, replacement=replacement.card_id,
        )


@dataclass(frozen=True)
class SwapSourceStatsAfterDamage:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.card.health <= 0:
            return
        attack, health = context.card.attack, context.card.max_health
        context.card.attack_delta += health - attack
        context.card.health_delta += attack - health
        game._event("sentient_hourglass_swap", player=context.player.index,
                    entity=context.card.entity_id, attack=context.card.attack,
                    health=context.card.max_health)


@dataclass(frozen=True)
class ResetAllHandCosts:
    def execute(self, game: Any, context: RuleContext) -> None:
        affected: list[int] = []
        for player in game.players:
            for held in player.hand:
                if held.cost_delta:
                    held.cost_delta = 0
                    affected.append(held.entity_id)
        game._event("reset_hand_costs", player=context.player.index,
                    source=context.card.card_id, affected=affected)


@dataclass(frozen=True)
class ReverseOwnDeck:
    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.deck.reverse()
        game._event("deck_reversed", player=context.player.index,
                    source=context.card.card_id)


@dataclass(frozen=True)
class ChronicleKeeperBattlecry:
    def execute(self, game: Any, context: RuleContext) -> None:
        if any(held.has_race("DRAGON") for held in context.player.hand):
            context.card.taunt = True
            context.card.divine_shield = True
            context.card.divine_shield_hits = max(1, context.card.divine_shield_hits)


@dataclass(frozen=True)
class IfHoldingDragon:
    effects: tuple[Effect, ...]

    def execute(self, game: Any, context: RuleContext) -> None:
        if any(held.has_race("DRAGON") for held in context.player.hand):
            for effect in self.effects:
                effect.execute(game, context)


@dataclass(frozen=True)
class CircadiamancerBattlecry:
    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = _past_ids(
            game, card_type="MINION", cost=8, collectible_only=True,
        )
        if not candidates:
            return
        generated = game._entity(game.rng.choice(candidates), created_by=context.card.card_id)
        generated.circadiamancer_discount = True
        game._add_generated(context.player, generated)


@dataclass(frozen=True)
class LightningRod:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player != context.player.index:
            raise ValueError("friendly minion target is required")
        target = game._find_minion(context.player.index, context.action.target_entity)
        game._damage_minion(context.player.index, target,
                            game._spell_effect_amount(context.player, context.card, 2), context.card)
        enemies = game._random_enemy_minions(context.player.index)
        if enemies:
            game._damage_minion(1 - context.player.index, game.rng.choice(enemies),
                                game._spell_effect_amount(context.player, context.card, 4), context.card)
        game._resolve_deaths()


@dataclass(frozen=True)
class Thunderquake:
    def execute(self, game: Any, context: RuleContext) -> None:
        for owner in game.players:
            for minion in list(owner.board):
                game._damage_minion(owner.index, minion,
                                    game._spell_effect_amount(context.player, context.card, 1), context.card)
        game._resolve_deaths()
        static_shock = game._entity("TIME_218", created_by=context.card.card_id)
        game._add_generated(context.player, static_shock)


@dataclass(frozen=True)
class DivineAugurBattlecry:
    def execute(self, game: Any, context: RuleContext) -> None:
        for held in context.player.hand:
            if held.definition.card_type != "MINION":
                continue
            value = max(held.attack, held.max_health)
            held.attack_delta += value - held.attack
            held.health_delta += value - held.max_health


@dataclass(frozen=True)
class TemporalShadowDeathrattle:
    def execute(self, game: Any, context: RuleContext) -> None:
        if len(context.player.board) + len(context.player.locations) >= 7:
            return
        shadow = game._entity("TIME_434t", created_by=context.card.card_id)
        shadow.summoned_turn = game.turn
        game._summon(context.player, shadow)
        targets = game._random_enemy_minions(context.player.index)
        if targets:
            game._forced_minion_attack(context.player.index, shadow,
                                        1 - context.player.index, game.rng.choice(targets))


@dataclass(frozen=True)
class EternusBattlecry:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player == context.player.index:
            raise ValueError("enemy minion target is required")
        target = game._find_minion(context.action.target_player, context.action.target_entity)
        if target.health > context.card.max_health:
            raise ValueError("target has too much Health for Eternus")
        previous = game.players[context.action.target_player]
        previous.board.remove(target)
        context.player.board.append(target)
        target.attacks_this_turn = 0
        game._event("eternus_control", player=context.player.index,
                    source=context.card.entity_id, target=target.entity_id)


@dataclass(frozen=True)
class PowerWordBarrier:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("character target is required")
        if context.action.target_entity is None:
            target_player = game.players[context.action.target_player]
            target_player.hero_divine_shield = True
            target_player.hero_divine_shield_hits = max(1, target_player.hero_divine_shield_hits)
        else:
            target = game._find_minion(context.action.target_player, context.action.target_entity)
            target.divine_shield = True
            target.divine_shield_hits = max(1, target.divine_shield_hits)
        for held in context.player.hand:
            if held.definition.card_type == "MINION":
                held.health_delta += 2


@dataclass(frozen=True)
class LastingLegacy:
    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.hero_attack_bonus += 4
        if not any(held.definition.card_type == "MINION" for held in context.player.deck):
            candidates = [held for held in context.player.hand if held.definition.card_type == "MINION"]
            if candidates:
                target = game.rng.choice(candidates)
                target.attack_delta += 4


@dataclass(frozen=True)
class ChronologicalAura:
    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.chronological_aura_turns.append(3)
        game._event("chronological_aura", player=context.player.index,
                    source=context.card.card_id, turns=3)


@dataclass(frozen=True)
class EndangeredDodoBattlecry:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.player.health > 10:
            return
        context.card.attack_delta += 5
        context.card.health_delta += 5
        if len(context.player.board) + len(context.player.locations) < 7:
            copy_card = context.card.clone(game.next_entity_id)
            game.next_entity_id += 1
            copy_card.summoned_turn = game.turn
            copy_card.created_by = context.card.card_id
            game._summon(context.player, copy_card)


@dataclass(frozen=True)
class HighborneMentorBattlecry:
    def execute(self, game: Any, context: RuleContext) -> None:
        pupil = game._entity("TIME_704t", created_by=context.card.card_id)
        game._add_generated(context.player, pupil)
        OfferPastDiscover(card_type="SPELL", min_cost=7,
                          after_pick="highborne_mentor").execute(game, context)


@dataclass(frozen=True)
class KronaBattlecry:
    def execute(self, game: Any, context: RuleContext) -> None:
        for held in context.player.deck[:5]:
            held.cost_delta += 1 - held.cost
        game._event("krona_bottom_discount", player=context.player.index,
                    source=context.card.entity_id, count=min(5, len(context.player.deck)))


@dataclass(frozen=True)
class AlternateReality:
    def execute(self, game: Any, context: RuleContext) -> None:
        pool = _past_ids(game, mechanic="CHOOSE_ONE", collectible_only=True)
        if not pool:
            return
        for zone_name in ("hand", "deck"):
            zone = getattr(context.player, zone_name)
            original = list(zone)
            zone.clear()
            for held in original:
                replacement = game._entity(game.rng.choice(pool), created_by=context.card.card_id)
                replacement.cost_delta += -1
                replacement.started_in_deck = held.started_in_deck
                zone.append(replacement)
        game._event("alternate_reality_replace", player=context.player.index,
                    source=context.card.card_id)


@dataclass(frozen=True)
class TroubledDoubleCombo:
    def execute(self, game: Any, context: RuleContext) -> None:
        if not context.card.combo_active or len(context.player.board) + len(context.player.locations) >= 7:
            return
        copy_card = context.card.clone(game.next_entity_id)
        game.next_entity_id += 1
        copy_card.summoned_turn = game.turn
        copy_card.created_by = context.card.card_id
        game._summon(context.player, copy_card)


@dataclass(frozen=True)
class Flashback:
    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = _past_ids(
            game, card_type="MINION", cost=1, collectible_only=True,
        )
        for _ in range(2):
            if not candidates or len(context.player.board) + len(context.player.locations) >= 7:
                break
            minion = game._entity(game.rng.choice(candidates), created_by=context.card.card_id)
            if context.card.combo_active:
                minion.attack_delta += 1
            minion.summoned_turn = game.turn
            game._summon(context.player, minion)


@dataclass(frozen=True)
class Dethrone:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("minion target is required")
        target = game._find_minion(context.action.target_player, context.action.target_entity)
        target.damage = target.max_health
        game._resolve_deaths()
        if context.card.combo_active:
            SummonRandomPast(cost=8).execute(game, context)


@dataclass(frozen=True)
class SlowMotion:
    def execute(self, game: Any, context: RuleContext) -> None:
        opponent = game.players[1 - context.player.index]
        opponent.all_card_cost_surcharge = getattr(opponent, "all_card_cost_surcharge", 0) + 1
        opponent.all_card_cost_surcharge_turn = game.turn + 1
        game._event("slow_motion", player=context.player.index,
                    target_player=opponent.index, active_turn=game.turn + 1)


@dataclass(frozen=True)
class Anomalize:
    def execute(self, game: Any, context: RuleContext) -> None:
        for cost in (10, 1):
            candidates = _past_ids(
                game, card_type="MINION", cost=cost, collectible_only=True,
            )
            if not candidates or len(context.player.board) + len(context.player.locations) >= 7:
                continue
            minion = game._entity(game.rng.choice(candidates), created_by=context.card.card_id)
            minion.attack_delta += minion.max_health - minion.attack
            minion.health_delta += minion.attack - minion.max_health
            minion.summoned_turn = game.turn
            game._summon(context.player, minion)


@dataclass(frozen=True)
class FacelessEnigmaBattlecry:
    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [
            card_id for card_id in _past_ids(
                game, card_type="SPELL", collectible_only=True,
            )
            if "SECRET" in game.card_defs[card_id].mechanics
        ]
        game.rng.shuffle(candidates)
        options = [game._entity(card_id, created_by=context.card.card_id) for card_id in candidates[:2]]
        if len(options) < 2:
            return
        game.pending_choice = {
            "kind": "DISCOVER", "player": context.player.index,
            "pool": tuple(candidates), "dark_gift": False,
            "repeats_left": 0, "after_pick": "time_enigma",
            "source_card_id": context.card.card_id, "options": options,
        }
        game._event("faceless_enigma_offer", player=context.player.index,
                    source=context.card.entity_id, options=[card.card_id for card in options])


@dataclass(frozen=True)
class TimelooperTokiBattlecry:
    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = _past_ids(
            game, card_type="SPELL", collectible_only=True,
        )
        if not candidates:
            return
        generated_count = 0
        for _ in range(3):
            generated = game._entity(game.rng.choice(candidates), created_by=context.card.card_id)
            generated.timelooper_origin = context.card.entity_id
            if game._add_generated(context.player, generated) == "hand":
                generated_count += 1
        if generated_count:
            context.player.timelooper_remaining[context.card.entity_id] = generated_count
        game._event("timelooper_cards", player=context.player.index,
                    source=context.card.entity_id, count=generated_count)


@dataclass(frozen=True)
class GladiatorialCombat:
    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [held for held in context.player.deck if held.definition.card_type == "MINION"]
        if candidates and len(context.player.board) + len(context.player.locations) < 7:
            minion = game.rng.choice(candidates)
            context.player.deck.remove(minion)
            minion.summoned_turn = game.turn
            game._summon(context.player, minion)
        Summon("TIME_870t", side="opponent").execute(game, context)


@dataclass(frozen=True)
class UndefeatedChampionBattlecry:
    def execute(self, game: Any, context: RuleContext) -> None:
        opponent = game.players[1 - context.player.index]
        candidates = _filtered_executable_ids(game, card_type="MINION", cost=1)
        while candidates and len(opponent.board) + len(opponent.locations) < 7:
            minion = game._entity(game.rng.choice(candidates), created_by=context.card.card_id)
            minion.summoned_turn = game.turn
            game._summon(opponent, minion)


@dataclass(frozen=True)
class UnleashCrocolisks:
    def execute(self, game: Any, context: RuleContext) -> None:
        GainArmor(10).execute(game, context)
        Summon("TIME_873t", count=2, side="opponent").execute(game, context)


# ---- Standard tranche 50F -------------------------------------------------
# Cataclysm has a cluster of effects whose state lives on a player, a held
# card, or a future generated token.  These helpers use explicit engine state
# rather than mutating frozen card definitions, which keeps MCTS branches
# independent and makes each persistent effect auditable.


@dataclass(frozen=True)
class CostByPlayerAttribute:
    attribute: str

    def adjustment(self, game: Any, player: Any, card: Any) -> int:
        return -max(0, int(getattr(player, self.attribute, 0)))


@dataclass(frozen=True)
class BroodwatcherBattlecry:
    def execute(self, game: Any, context: RuleContext) -> None:
        ready = context.card.mana_spent_while_held >= 8
        destinations: list[str] = []
        for _ in range(2):
            whelp = game._entity("CATA_132t", created_by=context.card.card_id)
            if ready and len(context.player.board) + len(context.player.locations) < 7:
                whelp.summoned_turn = game.turn
                game._summon(context.player, whelp)
                destinations.append("board")
            else:
                destinations.append(game._add_generated(context.player, whelp))
        game._event("broodwatcher_whelps", player=context.player.index,
                    source=context.card.entity_id, ready=ready,
                    destinations=destinations)


@dataclass(frozen=True)
class ShuffleLargeMinionsDoubled:
    count: int = 5

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = _filtered_executable_ids(game, card_type="MINION", min_cost=8)
        added: list[str] = []
        for _ in range(self.count):
            if not candidates:
                break
            card = game._entity(game.rng.choice(candidates), created_by=context.card.card_id)
            card.attack_delta += card.definition.attack
            card.health_delta += card.definition.health
            context.player.deck.insert(game.rng.randrange(len(context.player.deck) + 1), card)
            added.append(card.card_id)
        game._event("azsharas_triumph", player=context.player.index,
                    source=context.card.card_id, cards=added)


@dataclass(frozen=True)
class SetNextMurlocHealthCost:
    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.next_murloc_costs_health = True
        game._event("next_murloc_costs_health", player=context.player.index,
                    source=context.card.card_id)


@dataclass(frozen=True)
class GrantHealingBonus:
    amount: int = 2

    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.healing_bonus += self.amount
        game._event("healing_bonus", player=context.player.index,
                    source=context.card.card_id, amount=self.amount,
                    total=context.player.healing_bonus)


@dataclass(frozen=True)
class EndTurnFullHealthGain:
    health: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.card.damage == 0:
            context.card.health_delta += self.health
            game._event("full_health_end_turn_gain", player=context.player.index,
                        source=context.card.entity_id, health=self.health)


@dataclass(frozen=True)
class SummonFixedDragon:
    attack: int
    health: int
    card_id: str
    name: str

    def execute(self, game: Any, context: RuleContext) -> None:
        if len(context.player.board) + len(context.player.locations) >= 7:
            return
        from .dragon_mirror import CardDef
        dragon = game._instance_from_definition(CardDef(
            self.card_id, self.name, "MINION", 0, self.attack, self.health,
            "DRAGON", (), context.player.card_class, ("DRAGON",), "CATACLYSM",
        ), created_by=context.card.card_id)
        dragon.summoned_turn = game.turn
        game._summon(context.player, dragon)
        game._event("summon_fixed_dragon", player=context.player.index,
                    source=context.card.card_id, entity=dragon.entity_id,
                    attack=self.attack, health=self.health)


@dataclass(frozen=True)
class GrantHeldAndDeckSpellDamage:
    amount: int = 1

    def execute(self, game: Any, context: RuleContext) -> None:
        affected = []
        for card in context.player.hand + context.player.deck:
            if card.definition.card_type == "SPELL":
                card.spell_damage_bonus += self.amount
                affected.append(card.entity_id)
        game._event("grant_spell_damage_to_spells", player=context.player.index,
                    source=context.card.card_id, amount=self.amount, affected=affected)


@dataclass(frozen=True)
class GrantRandomCostDeathrattle:
    cost: int

    def execute(self, game: Any, context: RuleContext) -> None:
        for minion in context.player.board:
            minion.deathrattle_summon_random_cost = self.cost
        game._event("grant_random_cost_deathrattle", player=context.player.index,
                    source=context.card.card_id, cost=self.cost,
                    targets=[minion.entity_id for minion in context.player.board])


@dataclass(frozen=True)
class NozdormuBronzeAspectEndTurn:
    def execute(self, game: Any, context: RuleContext) -> None:
        shielded, buffed = [], []
        for minion in context.player.board:
            if minion is context.card or minion.health <= 0 or minion.dormant_turns:
                continue
            if minion.divine_shield:
                minion.attack_delta += 3
                minion.health_delta += 3
                buffed.append(minion.entity_id)
            else:
                minion.divine_shield = True
                minion.divine_shield_hits = max(1, minion.divine_shield_hits)
                shielded.append(minion.entity_id)
        game._event("nozdormu_bronze_aspect", player=context.player.index,
                    source=context.card.entity_id, shielded=shielded, buffed=buffed)


@dataclass(frozen=True)
class BronzeRedeemerEndTurn:
    def execute(self, game: Any, context: RuleContext) -> None:
        SummonFixedDragon(context.card.attack, context.card.max_health,
                          "CATA_478t", "Bronze Redeemer's Dragon").execute(game, context)


@dataclass(frozen=True)
class SummonSourceCopyIfSpellDamage:
    def execute(self, game: Any, context: RuleContext) -> None:
        if not context.player.spell_damage_dealt_this_turn:
            return
        if len(context.player.board) + len(context.player.locations) >= 7:
            return
        copy_card = context.card.clone(game.next_entity_id)
        game.next_entity_id += 1
        copy_card.created_by = context.card.card_id
        copy_card.summoned_turn = game.turn
        game._summon(context.player, copy_card)
        game._event("unstable_spellcaster_copy", player=context.player.index,
                    source=context.card.entity_id, copy=copy_card.entity_id)


@dataclass(frozen=True)
class DukeOfBelowBattlecry:
    def execute(self, game: Any, context: RuleContext) -> None:
        amount = 2 * max(0, context.player.discarded_this_game)
        context.card.attack_delta += amount
        context.card.health_delta += amount
        game._event("duke_of_below_stats", player=context.player.index,
                    source=context.card.entity_id,
                    discarded=context.player.discarded_this_game, amount=amount)


@dataclass(frozen=True)
class RafaamsLastStand:
    def execute(self, game: Any, context: RuleContext) -> None:
        amount = 2 + max(0, context.card.held_turns)
        targets = list(game._random_enemy_minions(context.player.index))
        game.rng.shuffle(targets)
        for target in targets[:2]:
            game._damage_minion(1 - context.player.index, target,
                                game._spell_effect_amount(context.player, context.card, amount),
                                context.card)
        game._resolve_deaths()
        game._event("rafaams_last_stand", player=context.player.index,
                    source=context.card.card_id, amount=amount,
                    targets=[target.entity_id for target in targets[:2]])


@dataclass(frozen=True)
class ArmSigilOfSeas:
    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.sigil_of_seas_trigger_turn = game.turn + 2
        game._event("sigil_of_seas_armed", player=context.player.index,
                    source=context.card.card_id, trigger_turn=game.turn + 2)


@dataclass(frozen=True)
class SetAnimalCompanionUpgrade:
    cost_increase: int = 0
    extra_count: int = 0

    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.animal_companion_cost_increase += self.cost_increase
        context.player.animal_companion_extra_count += self.extra_count
        game._event("animal_companion_upgrade", player=context.player.index,
                    source=context.card.card_id,
                    cost_increase=context.player.animal_companion_cost_increase,
                    extra_count=context.player.animal_companion_extra_count)


@dataclass(frozen=True)
class NurturingNature:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player != context.player.index:
            raise ValueError("friendly Beast target is required")
        target = game._find_minion(context.player.index, context.action.target_entity)
        if not target.has_race("BEAST"):
            raise ValueError("Nurturing Nature requires a friendly Beast")
        target.attack_delta += 2
        target.health_delta += 2
        held = [card for card in context.player.hand if card.has_race("BEAST")]
        chosen = game.rng.choice(held) if held else None
        if chosen is not None:
            chosen.attack_delta += 2
            chosen.health_delta += 2
        game._event("nurturing_nature", player=context.player.index,
                    source=context.card.card_id, target=target.entity_id,
                    held=None if chosen is None else chosen.entity_id)


@dataclass(frozen=True)
class SummonRecruit:
    count: int
    divine_shield: bool = False
    add_to_hand: bool = False

    def execute(self, game: Any, context: RuleContext) -> None:
        summoned, generated = [], []
        for _ in range(self.count):
            if len(context.player.board) + len(context.player.locations) < 7:
                recruit = game._entity("CS2_101t", created_by=context.card.card_id)
                recruit.divine_shield = self.divine_shield or recruit.divine_shield
                recruit.divine_shield_hits = max(1, recruit.divine_shield_hits) if recruit.divine_shield else 0
                recruit.summoned_turn = game.turn
                game._summon(context.player, recruit)
                summoned.append(recruit.entity_id)
            if self.add_to_hand:
                card = game._entity("CS2_101t", created_by=context.card.card_id)
                generated.append((card.entity_id, game._add_generated(context.player, card)))
        game._event("summon_recruits", player=context.player.index,
                    source=context.card.card_id, summoned=summoned, generated=generated,
                    divine_shield=self.divine_shield)


@dataclass(frozen=True)
class AddRecruitStats:
    attack: int = 0
    health: int = 0

    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.recruit_attack_bonus += self.attack
        context.player.recruit_health_bonus += self.health
        for minion in context.player.board:
            if minion.card_id == "CS2_101t":
                minion.attack_delta += self.attack
                minion.health_delta += self.health
        game._event("recruit_stats", player=context.player.index,
                    source=context.card.card_id, attack=self.attack, health=self.health)


@dataclass(frozen=True)
class AratorBattlecry:
    def execute(self, game: Any, context: RuleContext) -> None:
        affected = []
        for minion in context.player.board:
            if minion.card_id != "CS2_101t":
                continue
            minion.attack_delta += minion.attack
            minion.health_delta += minion.max_health
            minion.taunt = True
            affected.append(minion.entity_id)
        game._event("arator_redeemer", player=context.player.index,
                    source=context.card.entity_id, affected=affected)


@dataclass(frozen=True)
class RefreshManaIfNoMinionLastTurn:
    amount: int = 3

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.player.minion_played_last_turn:
            return
        before = context.player.mana
        context.player.mana = min(context.player.max_mana, context.player.mana + self.amount)
        game._event("wildspeaker_refresh", player=context.player.index,
                    source=context.card.entity_id, amount=context.player.mana - before)


@dataclass(frozen=True)
class AddRandomDragonDiscount:
    amount: int = 2

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = _filtered_executable_ids(game, card_type="MINION", race="DRAGON")
        if not candidates:
            return
        card = game._entity(game.rng.choice(candidates), created_by=context.card.card_id)
        card.cost_delta -= self.amount
        destination = game._add_generated(context.player, card)
        game._event("random_dragon_discount", player=context.player.index,
                    source=context.card.card_id, card=card.card_id,
                    destination=destination, amount=self.amount)


@dataclass(frozen=True)
class AddRandomSpellSchoolDiscount:
    spell_school: str
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = _filtered_executable_ids(
            game, card_type="SPELL", spell_school=self.spell_school,
        )
        if not candidates:
            return
        card = game._entity(game.rng.choice(candidates), created_by=context.card.card_id)
        card.cost_delta -= self.amount
        destination = game._add_generated(context.player, card)
        game._event(
            "random_spell_school_discount", player=context.player.index,
            source=context.card.card_id, card=card.card_id,
            spell_school=self.spell_school, amount=self.amount,
            destination=destination,
        )


@dataclass(frozen=True)
class GrantDragonsRush:
    """Grant a controller-level Dragon Rush enchantment for the game."""

    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.dragons_have_rush = True
        affected: list[int] = []
        for minion in context.player.board:
            if minion.has_race("DRAGON"):
                minion.rush = True
                affected.append(minion.entity_id)
        game._event("dragons_gain_rush", player=context.player.index,
                    source=context.card.entity_id, affected=affected)


@dataclass(frozen=True)
class CopyFriendlyDeathsThisTurn:
    attack: int = 0
    health: int = 0

    def execute(self, game: Any, context: RuleContext) -> None:
        copied: list[int] = []
        for dead in context.player.minions_died_this_turn_cards:
            copy_card = dead.clone(game.next_entity_id)
            game.next_entity_id += 1
            copy_card.created_by = context.card.card_id
            copy_card.attack_delta += self.attack
            copy_card.health_delta += self.health
            if game._add_generated(context.player, copy_card) == "hand":
                copied.append(copy_card.entity_id)
        game._event("copy_friendly_deaths_this_turn", player=context.player.index,
                    source=context.card.entity_id, copies=copied,
                    attack=self.attack, health=self.health)


@dataclass(frozen=True)
class SummonOneCostMinionsPlayed:
    def execute(self, game: Any, context: RuleContext) -> None:
        summoned = []
        for card_id, count in sorted(context.player.played_card_counts.items()):
            definition = game.card_defs.get(card_id)
            if definition is None or definition.card_type != "MINION" or definition.cost != 1:
                continue
            for _ in range(count):
                if len(context.player.board) + len(context.player.locations) >= 7:
                    break
                minion = game._entity(card_id, created_by=context.card.card_id)
                minion.summoned_turn = game.turn
                game._summon(context.player, minion)
                summoned.append(minion.entity_id)
        game._event("confront_tolvir", player=context.player.index,
                    source=context.card.card_id, summoned=summoned)


@dataclass(frozen=True)
class AirSupportBattlecry:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player != context.player.index:
            raise ValueError("friendly minion target is required")
        target = game._find_minion(context.player.index, context.action.target_entity)
        target.mega_windfury = True
        target.cant_attack_heroes_turn = game.turn
        game._event("air_support", player=context.player.index,
                    source=context.card.entity_id, target=target.entity_id)


@dataclass(frozen=True)
class OfferHandSelection:
    mode: str
    predicate: str = "any"

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [card for card in context.player.hand if card.entity_id != context.card.entity_id]
        if self.predicate == "spell":
            candidates = [card for card in candidates if card.definition.card_type == "SPELL"]
        elif self.predicate == "spell_le4":
            candidates = [card for card in candidates if card.definition.card_type == "SPELL" and card.cost <= 4]
        elif self.predicate == "fel_spell":
            candidates = [card for card in candidates if card.definition.card_type == "SPELL" and card.definition.spell_school == "FEL"]
        if not candidates:
            return
        game.pending_choice = {
            "kind": "HAND_SELECT", "player": context.player.index,
            "source": context.card, "mode": self.mode, "options": tuple(candidates),
        }
        game._event("hand_selection_offer", player=context.player.index,
                    source=context.card.card_id, mode=self.mode,
                    options=[card.entity_id for card in candidates])


@dataclass(frozen=True)
class Ascendance:
    def execute(self, game: Any, context: RuleContext) -> None:
        transformed = []
        for original in list(context.player.board):
            candidates = _filtered_executable_ids(
                game, card_type="MINION", cost=original.definition.cost + 1,
            )
            if not candidates:
                continue
            replacement = game._entity(game.rng.choice(candidates), created_by=context.card.card_id)
            replacement.entity_id = original.entity_id
            replacement.summoned_turn = original.summoned_turn
            replacement.played_turn = original.played_turn
            replacement.deathrattle_summon_card_id = original.card_id
            context.player.board[context.player.board.index(original)] = replacement
            transformed.append((original.card_id, replacement.card_id, replacement.entity_id))
        game._refresh_continuous(context.player)
        game._event("ascendance", player=context.player.index,
                    source=context.card.card_id, transformed=transformed)


@dataclass(frozen=True)
class SetHandMinionDeathrattle:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_entity is None:
            raise ValueError("minion target is required")
        target = game._find_minion(context.action.target_player, context.action.target_entity)
        target.deathrattle_summon_hand_minion = True
        game._event("deathrattle_summon_hand_minion", player=context.player.index,
                    source=context.card.card_id, target=target.entity_id)


@dataclass(frozen=True)
class ShadowedInformantBattlecry:
    def execute(self, game: Any, context: RuleContext) -> None:
        card_class = context.card.shadowed_class or context.player.card_class
        # This is a class-spell Discover, not an arbitrary executable spell
        # filter.  Delegate to the engine's collectible Standard pool so
        # generated tokens and historical auxiliary entities cannot leak into
        # the offer; dual-class spells remain eligible through CardDef.classes.
        game._offer_class_discover(
            context.player, card_class=card_class,
            source_card_id=context.card.card_id,
            card_type="SPELL",
        )


@dataclass(frozen=True)
class ShadowedInformantStartTurn:
    def execute(self, game: Any, context: RuleContext) -> None:
        classes = (
            "DEMONHUNTER", "DRUID", "HUNTER", "MAGE", "PALADIN", "PRIEST",
            "ROGUE", "SHAMAN", "WARLOCK", "WARRIOR", "DEATHKNIGHT",
        )
        current = context.card.shadowed_class or context.player.card_class
        try:
            context.card.shadowed_class = classes[(classes.index(current) + 1) % len(classes)]
        except ValueError:
            context.card.shadowed_class = classes[0]
        game._event("shadowed_informant_class", player=context.player.index,
                    source=context.card.entity_id, card_class=context.card.shadowed_class)


@dataclass(frozen=True)
class DreadLeviathanBattlecry:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player == context.player.index:
            raise ValueError("enemy minion target is required")
        target = game._find_minion(context.action.target_player, context.action.target_entity)
        stolen = 0
        for _ in range(3):
            if target.health <= 0:
                break
            amount = min(3, max(0, target.health))
            game._damage_minion(context.action.target_player, target, 3, context.card)
            context.card.damage = max(0, context.card.damage - amount)
            stolen += amount
        game._resolve_deaths()
        game._event("dread_leviathan_steal", player=context.player.index,
                    source=context.card.entity_id, target=target.entity_id, amount=stolen)


@dataclass(frozen=True)
class ChaosSupplicantAfterSpell:
    def execute(self, game: Any, context: RuleContext) -> None:
        spell = context.payload.get("spell")
        if spell is None or getattr(spell, "chaos_supplicant_depth", 0) >= 8:
            return
        candidates = _filtered_executable_ids(
            game, card_type="SPELL", cost=spell.cost, other_class_for=context.player,
        )
        candidates = [card_id for card_id in candidates if "DISCOVER" not in game.card_defs[card_id].mechanics]
        if not candidates:
            return
        from .dragon_mirror import Action, UnsupportedGeneratedCard
        generated = game._entity(game.rng.choice(candidates), created_by=context.card.card_id)
        generated.chaos_supplicant_depth = getattr(spell, "chaos_supplicant_depth", 0) + 1
        action = Action("PLAY", generated.entity_id)
        targeting = game.rule_registry.targeting(generated.card_id)
        if targeting is not None:
            targets = game._rule_targets(context.player, generated, targeting.kind)
            if not targets:
                return
            target_player, target_entity = game.rng.choice(targets)
            action = Action("PLAY", generated.entity_id, target_player, target_entity)
        try:
            game._cast_spell(context.player, generated, action)
        except (ValueError, UnsupportedGeneratedCard):
            game._event("chaos_supplicant_skip", player=context.player.index,
                        source=context.card.entity_id, spell=generated.card_id)
            return
        game._event("chaos_supplicant_cast", player=context.player.index,
                    source=context.card.entity_id, spell=generated.card_id,
                    depth=generated.chaos_supplicant_depth)


@dataclass(frozen=True)
class ReturnGemstoneDiscard:
    def execute(self, game: Any, context: RuleContext) -> None:
        card = context.card.stored_discarded_card
        if card is None:
            return
        context.card.stored_discarded_card = None
        card.cost_delta -= 1
        destination = game._add_generated(context.player, card)
        game._event("gemstone_return", player=context.player.index,
                    source=context.card.entity_id, card=card.card_id, destination=destination)


@dataclass(frozen=True)
class SindragosasTriumph:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_entity is None:
            raise ValueError("minion target is required")
        target = game._find_minion(context.action.target_player, context.action.target_entity)
        before = max(0, target.health)
        amount = 8
        game._damage_minion(context.action.target_player, target, amount, context.card)
        excess = max(0, amount - before)
        game._resolve_deaths()
        chosen = game.rng.choice(context.player.hand) if excess and context.player.hand else None
        if chosen is not None:
            chosen.cost_delta -= excess
        game._event("sindragosas_triumph", player=context.player.index,
                    source=context.card.card_id, target=target.entity_id,
                    excess=excess, discounted=None if chosen is None else chosen.entity_id)


# ---- Standard tranche 50G -------------------------------------------------
# These cards deliberately use the same generated-entity and player-state
# primitives as the earlier batches.  In particular, a generated token keeps
# its behaviour on the *instance* rather than becoming a metadata-only card.


def _dynamic_minion(
    game: Any, source: Any, card_id: str, name: str, attack: int, health: int,
    *, race: str = "", mechanics: tuple[str, ...] = (), card_class: str = "NEUTRAL",
) -> Any:
    from .dragon_mirror import CardDef
    minion = game._instance_from_definition(CardDef(
        card_id, name, "MINION", 0, attack, health, race, mechanics,
        card_class, (() if not race else (race,)), "GENERATED",
    ), created_by=source.card_id)
    minion.summoned_turn = game.turn
    return minion


@dataclass(frozen=True)
class DealRandomEnemy:
    amount: int
    count: int = 1

    def execute(self, game: Any, context: RuleContext) -> None:
        hits = []
        for _ in range(self.count):
            targets = game._random_enemy_characters(context.player.index)
            if not targets:
                break
            target = game.rng.choice(targets)
            game._deal_to_target(context.player.index, target, self.amount, context.card)
            hits.append(target)
            game._resolve_deaths()
        game._event("random_enemy_damage", player=context.player.index,
                    source=context.card.card_id, amount=self.amount, hits=hits)


@dataclass(frozen=True)
class PassTemporaryPlayEffect:
    effect: str
    predicate: str = "any"

    def execute(self, game: Any, context: RuleContext) -> None:
        choices = [card for card in context.player.hand if card.entity_id != context.card.entity_id]
        if self.predicate == "pirate":
            choices = [card for card in choices if card.has_race("PIRATE")]
        # "playable" means it can actually be paid now, not merely that it
        # has a type which could be played in some future turn.
        choices = [card for card in choices if game._effective_cost(context.player, card) <= context.player.mana]
        if not choices:
            return
        chosen = game.rng.choice(choices)
        chosen.temporary_play_effect = self.effect
        chosen.temporary_play_effect_expiry_turn = game.turn + 2
        game._event("temporary_play_effect", player=context.player.index,
                    source=context.card.card_id, target=chosen.entity_id,
                    effect=self.effect)


@dataclass(frozen=True)
class ShuffleImpFormants:
    count: int = 2

    def execute(self, game: Any, context: RuleContext) -> None:
        opponent = game.players[1 - context.player.index]
        cards = []
        for _ in range(self.count):
            imp = _imp_formant(game, context.card, context.player.index)
            opponent.deck.insert(game.rng.randrange(len(opponent.deck) + 1), imp)
            cards.append(imp.entity_id)
        game._event("imp_formants_shuffled", player=context.player.index,
                    opponent=opponent.index, cards=cards)


@dataclass(frozen=True)
class SummonGhostAndPassEffect:
    def execute(self, game: Any, context: RuleContext) -> None:
        if len(context.player.board) + len(context.player.locations) < 7:
            ghost = _dynamic_minion(game, context.card, "CAP_802t", "Ghost", 2, 1,
                                    mechanics=("REBORN",))
            ghost.reborn = True
            game._summon(context.player, ghost)
        PassTemporaryPlayEffect("CAP_802").execute(game, context)


@dataclass(frozen=True)
class GrantRebornOrCopy:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player != context.player.index:
            raise ValueError("friendly minion target is required")
        target = game._find_minion(context.player.index, context.action.target_entity)
        if not target.reborn:
            target.reborn = True
            game._event("grant_reborn", player=context.player.index,
                        source=context.card.entity_id, target=target.entity_id)
            return
        if len(context.player.board) + len(context.player.locations) >= 7:
            return
        copy_card = target.clone(game.next_entity_id)
        game.next_entity_id += 1
        copy_card.created_by = context.card.card_id
        copy_card.summoned_turn = game.turn
        game._summon(context.player, copy_card)
        game._event("reborn_copy", player=context.player.index,
                    source=context.card.entity_id, target=target.entity_id,
                    copy=copy_card.entity_id)


@dataclass(frozen=True)
class SlimeEm:
    def execute(self, game: Any, context: RuleContext) -> None:
        for player in game.players:
            player.slime_resummon = [copy.deepcopy(minion) for minion in player.board]
            for minion in player.board:
                minion.damage = minion.max_health
        game._resolve_deaths()
        from .dragon_mirror import CardDef
        for player in game.players:
            spell = game._instance_from_definition(CardDef(
                "CAP_805t", "Slime 'em!", "SPELL", 3, 0, 0, "", (),
                "NEUTRAL", (), "GENERATED",
            ), created_by=context.card.card_id)
            game._add_generated(player, spell)
        game._event("slime_em_destroy", player=context.player.index)


@dataclass(frozen=True)
class ResummonSlime:
    def execute(self, game: Any, context: RuleContext) -> None:
        summoned = []
        for original in list(context.player.slime_resummon):
            if len(context.player.board) + len(context.player.locations) >= 7:
                break
            minion = original.clone(game.next_entity_id)
            game.next_entity_id += 1
            minion.damage = 0
            minion.reborn = original.reborn
            minion.summoned_turn = game.turn
            game._summon(context.player, minion)
            summoned.append(minion.entity_id)
        context.player.slime_resummon.clear()
        game._event("slime_em_resummon", player=context.player.index, summoned=summoned)


@dataclass(frozen=True)
class ResurrectRebornAndFight:
    def execute(self, game: Any, context: RuleContext) -> None:
        resurrected = []
        for dead in list(context.player.dead_minions):
            if not dead.reborn or len(context.player.board) + len(context.player.locations) >= 7:
                continue
            minion = dead.clone(game.next_entity_id)
            game.next_entity_id += 1
            minion.damage = 0
            minion.reborn = False
            minion.summoned_turn = game.turn
            game._summon(context.player, minion)
            resurrected.append(minion)
        for minion in resurrected:
            targets = game._random_enemy_minions(context.player.index)
            if targets and minion.health > 0:
                game._forced_minion_attack(context.player.index, minion,
                                            1 - context.player.index,
                                            game.rng.choice(targets))
        game._resolve_deaths()
        game._event("raith_van_geist", player=context.player.index,
                    resurrected=[minion.entity_id for minion in resurrected])


@dataclass(frozen=True)
class SetEndTurnEffectsTwice:
    turns: int = 3

    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.end_turn_effect_repeat_turns += self.turns
        game._event("end_turn_effects_twice", player=context.player.index,
                    source=context.card.card_id, turns=self.turns)


@dataclass(frozen=True)
class AbsorbSpell:
    def execute(self, game: Any, context: RuleContext) -> None:
        OfferHandSelection("absorb_spell", "spell_le4").execute(game, context)


@dataclass(frozen=True)
class SummonWebspinners:
    def execute(self, game: Any, context: RuleContext) -> None:
        for _ in range(3):
            if len(context.player.board) + len(context.player.locations) >= 7:
                break
            spider = _dynamic_minion(game, context.card, "CORE_AT_062t", "Webspinner", 1, 1,
                                     race="BEAST", mechanics=("DEATHRATTLE",))
            spider.deathrattle_random_race = "BEAST"
            game._summon(context.player, spider)


@dataclass(frozen=True)
class PriestOfAnshe:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.player.restored_health_this_turn:
            context.card.attack_delta += 3
            context.card.health_delta += 3
            game._event("priest_of_anshe", player=context.player.index,
                        source=context.card.entity_id)


@dataclass(frozen=True)
class SummonRandomByHandSize:
    def execute(self, game: Any, context: RuleContext) -> None:
        game._summon_random_executable_minion(
            context.player, source_card_id=context.card.card_id,
            cost=len(context.player.hand),
        )


@dataclass(frozen=True)
class TopdeckRandomSpellForOpponent:
    def execute(self, game: Any, context: RuleContext) -> None:
        opponent = game.players[1 - context.player.index]
        candidates = _filtered_executable_ids(game, card_type="SPELL")
        if not candidates:
            return
        spell = game._entity(game.rng.choice(candidates), created_by=context.card.card_id)
        opponent.deck.append(spell)
        game._event("merch_seller_topdeck", player=context.player.index,
                    opponent=opponent.index, card=spell.card_id)


@dataclass(frozen=True)
class DiscountAdjacentHandCards:
    amount: int = 1

    def execute(self, game: Any, context: RuleContext) -> None:
        # The Battlecry source has already left the hand. Its old neighbours
        # are now the two cards adjacent to that vacated position.
        index = min(getattr(context.card, "played_hand_index", len(context.player.hand)), len(context.player.hand))
        targets = context.player.hand[max(0, index - 1):index + 1]
        for target in targets:
            target.cost_delta -= self.amount
        game._event("adjacent_hand_discount", player=context.player.index,
                    source=context.card.entity_id,
                    targets=[target.entity_id for target in targets], amount=self.amount)


@dataclass(frozen=True)
class SetFriendlyOneOneAndFillCopies:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player != context.player.index:
            raise ValueError("friendly minion target is required")
        target = game._find_minion(context.player.index, context.action.target_entity)
        target.attack_delta += 1 - target.attack
        target.health_delta += 1 - target.max_health
        target.damage = min(target.damage, target.max_health - 1)
        while len(context.player.board) + len(context.player.locations) < 7:
            copy_card = target.clone(game.next_entity_id)
            game.next_entity_id += 1
            copy_card.damage = 0
            copy_card.summoned_turn = game.turn
            copy_card.created_by = context.card.card_id
            game._summon(context.player, copy_card)
        game._event("bat_mask", player=context.player.index,
                    source=context.card.card_id, target=target.entity_id)


@dataclass(frozen=True)
class DiscoverAndSummon:
    card_type: str = "MINION"
    cost: int | None = None
    min_cost: int | None = None
    race: str | None = None
    mechanic: str | None = None
    legendary: bool = False
    after_pick: str = "summon_discover"

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = _filtered_executable_ids(
            game, card_type=self.card_type, cost=self.cost,
            min_cost=self.min_cost, race=self.race, mechanic=self.mechanic,
        )
        if self.legendary:
            candidates = [card_id for card_id in candidates
                          if game.card_defs[card_id].rarity == "LEGENDARY"]
        if candidates:
            game._offer_discover(context.player, candidates, False,
                                 source_card_id=context.card.card_id,
                                 after_pick=self.after_pick)


@dataclass(frozen=True)
class RandomMaskOtherClass:
    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [
            card_id for card_id, definition in game.card_defs.items()
            if card_id in game.executable_card_ids
            and "mask" in definition.name.casefold()
            and definition.card_class not in {"", "NEUTRAL", context.player.card_class}
        ]
        if not candidates:
            return
        card = game._entity(game.rng.choice(candidates), created_by=context.card.card_id)
        if context.card.combo_active:
            card.cost_delta -= 2
        game._add_generated(context.player, card)
        game._event("costume_merchant", player=context.player.index,
                    source=context.card.entity_id, card=card.card_id,
                    combo=context.card.combo_active)


@dataclass(frozen=True)
class BehemothMask:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_entity is None:
            raise ValueError("minion target is required")
        target = game._find_minion(context.action.target_player, context.action.target_entity)
        target.attack_delta += 8 - target.attack
        target.health_delta += 10 - target.max_health
        target.damage = min(target.damage, target.max_health - 1)
        target.lifesteal = True
        enemies = game._random_enemy_minions(context.player.index)
        if enemies:
            attacker = game.rng.choice(enemies)
            game._forced_minion_attack(1 - context.player.index, attacker,
                                        context.player.index, target)
        game._event("behemoth_mask", player=context.player.index,
                    source=context.card.card_id, target=target.entity_id)


@dataclass(frozen=True)
class SheepMask:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_entity is None:
            raise ValueError("minion target is required")
        target = game._find_minion(context.action.target_player, context.action.target_entity)
        target.attack_delta += 1 - target.attack
        target.health_delta += 1 - target.max_health
        target.damage = min(target.damage, target.max_health - 1)
        target.deathrattle_damage_all_minions = 2
        game._event("sheep_mask", player=context.player.index,
                    source=context.card.card_id, target=target.entity_id)


@dataclass(frozen=True)
class BeastSpeakerTaka:
    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = _filtered_executable_ids(game, card_type="MINION", race="BEAST")
        candidates = [card_id for card_id in candidates
                      if game.card_defs[card_id].rarity == "LEGENDARY"]
        if candidates:
            game._offer_discover(
                context.player, candidates, False,
                source_card_id=context.card.card_id,
                source_entity_id=context.card.entity_id,
                after_pick="taka_stats_deathrattle",
            )


@dataclass(frozen=True)
class AttackRandomEnemyMinionsIfCheap:
    count: int = 2

    def execute(self, game: Any, context: RuleContext) -> None:
        if (
            context.card.paid_cost
            if context.card.paid_cost is not None
            else context.card.cost
        ) > 3:
            return
        targets = list(game._random_enemy_minions(context.player.index))
        game.rng.shuffle(targets)
        for target in targets[:self.count]:
            if context.card in context.player.board and context.card.health > 0:
                game._forced_minion_attack(context.player.index, context.card,
                                            1 - context.player.index, target)
        game._resolve_deaths()


@dataclass(frozen=True)
class NewMoonDamage:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_entity is None:
            raise ValueError("minion target is required")
        target = game._find_minion(context.action.target_player, context.action.target_entity)
        context.card.lifesteal = context.player.spells_cast_this_game >= 3
        game._damage_minion(context.action.target_player, target,
                            game._spell_effect_amount(context.player, context.card, 6), context.card)
        game._resolve_deaths()


@dataclass(frozen=True)
class RitualNewMoon:
    def execute(self, game: Any, context: RuleContext) -> None:
        cost = 6 if context.player.spells_cast_this_game >= 3 else 3
        for _ in range(2):
            game._summon_random_executable_minion(context.player,
                                                   source_card_id=context.card.card_id,
                                                   cost=cost)


@dataclass(frozen=True)
class SetNextThreeSpellsTwice:
    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.spells_cast_twice_remaining += 3
        game._event("next_spells_twice", player=context.player.index,
                    source=context.card.entity_id,
                    remaining=context.player.spells_cast_twice_remaining)


@dataclass(frozen=True)
class WeaverOfCycle:
    def execute(self, game: Any, context: RuleContext) -> None:
        if any(card.definition.card_type == "SPELL" and card.cost >= 5
               for card in context.player.hand):
            game._damage_hero(game.players[1 - context.player.index], 3, context.card)
            game._event("weaver_of_cycle", player=context.player.index,
                        source=context.card.entity_id, amount=3)


@dataclass(frozen=True)
class RottenApple:
    def execute(self, game: Any, context: RuleContext) -> None:
        game._apply_heal(context.player, context.player, 12, source=context.card)
        context.player.delayed_self_damage.extend(((game.turn + 2, 3), (game.turn + 4, 3)))
        game._event("rotten_apple", player=context.player.index,
                    source=context.card.card_id)


@dataclass(frozen=True)
class FracturedPower:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.player.max_mana:
            context.player.max_mana -= 1
            context.player.mana = min(context.player.mana, context.player.max_mana)
        context.player.delayed_mana_crystal_gains.append((game.turn + 4, 2))
        game._event("fractured_power", player=context.player.index,
                    source=context.card.card_id)


@dataclass(frozen=True)
class RandomHandMinionAttackReduction:
    amount: int = 2

    def execute(self, game: Any, context: RuleContext) -> None:
        affected = []
        for player in game.players:
            candidates = [card for card in player.hand if card.definition.card_type == "MINION"]
            if candidates:
                card = game.rng.choice(candidates)
                card.attack_delta -= self.amount
                affected.append(card.entity_id)
        game._event("twisted_treant", player=context.player.index,
                    source=context.card.entity_id, affected=affected)


@dataclass(frozen=True)
class RandomSchoolSpell:
    school: str

    def execute(self, game: Any, context: RuleContext) -> None:
        AddRandomFilteredCards(card_type="SPELL", spell_school=self.school).execute(game, context)


@dataclass(frozen=True)
class DaggerOrWeaponBuff:
    def execute(self, game: Any, context: RuleContext) -> None:
        from .dragon_mirror import Weapon
        if context.player.weapon is None:
            context.player.weapon = Weapon("END_002t", "Dagger", 1, 2)
            game._event("wicked_blightspawn_dagger", player=context.player.index)
        else:
            context.player.weapon.attack += 2
            game._event("wicked_blightspawn_weapon_buff", player=context.player.index,
                        attack=context.player.weapon.attack)


@dataclass(frozen=True)
class ChronikarBattlecry:
    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.hero_attack_bonus += 3
        context.player.delayed_hero_attack.extend(((game.turn + 2, 3), (game.turn + 4, 3)))
        game._event("chronikar_attack", player=context.player.index,
                    source=context.card.entity_id)


@dataclass(frozen=True)
class SplinteredReality:
    def execute(self, game: Any, context: RuleContext) -> None:
        treant_deaths = sum(card.card_id == "END_009t" for card in context.player.dead_minions)
        for _ in range(2):
            if len(context.player.board) + len(context.player.locations) >= 7:
                break
            treant = _dynamic_minion(game, context.card, "END_009t", "Splintered Treant", 2, 2, race="TREANT")
            treant.attack_delta += treant_deaths
            treant.health_delta += treant_deaths
            game._summon(context.player, treant)


@dataclass(frozen=True)
class InfinityWeaponBattlecry:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.player.weapon is not None:
            context.player.weapon.attack = 2_147_483_647
            context.player.weapon_attack_reset_turn = game.turn + 2
            game._event("hand_of_infinity", player=context.player.index,
                        source=context.card.entity_id)


@dataclass(frozen=True)
class InfiniteAcolyte:
    def execute(self, game: Any, context: RuleContext) -> None:
        if not context.player.hand:
            return
        card = game.rng.choice(context.player.hand)
        card.original_cost_delta = card.cost_delta
        card.cost_delta += 2_147_483_647
        context.card.stored_discarded_card = card
        game._event("acolyte_of_infinity", player=context.player.index,
                    source=context.card.entity_id, target=card.entity_id)


@dataclass(frozen=True)
class WingedAberrationCombo:
    def execute(self, game: Any, context: RuleContext) -> None:
        if not context.card.combo_active:
            return
        context.player.overload_next_turn += 2
        context.card.immune = True
        context.card.temporary_immune_expiry_turn = game.current
        context.card.windfury = True
        game._event("winged_aberration_combo", player=context.player.index,
                    source=context.card.entity_id)


@dataclass(frozen=True)
class CopyLowestCostBeast:
    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [card for card in context.player.hand if card.has_race("BEAST")]
        if not candidates:
            return
        lowest = min(card.cost for card in candidates)
        chosen = game.rng.choice([card for card in candidates if card.cost == lowest])
        copy_card = chosen.clone(game.next_entity_id)
        game.next_entity_id += 1
        copy_card.created_by = context.card.card_id
        game._add_generated(context.player, copy_card)


@dataclass(frozen=True)
class TricksOfTheTrade:
    def execute(self, game: Any, context: RuleContext) -> None:
        DamageActionTarget(
            3 if context.card.stealthed_minion_attacked_while_held else 1
        ).execute(game, context)


@dataclass(frozen=True)
class OfferTauntDiscoverBuff:
    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = _filtered_executable_ids(game, card_type="MINION", mechanic="TAUNT")
        if candidates:
            game._offer_discover(context.player, candidates, False,
                                 source_card_id=context.card.card_id,
                                 after_pick="taunt_buff")


@dataclass(frozen=True)
class SetDeathrattleAllEnemies:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        context.card.deathrattle_damage_all_enemies = self.amount


@dataclass(frozen=True)
class InfernoHeraldAfterSpell:
    def execute(self, game: Any, context: RuleContext) -> None:
        spell = context.payload.get("spell")
        if spell is None or spell.definition.spell_school != "FIRE":
            return
        candidates = _filtered_executable_ids(game, card_type="MINION", race="ELEMENTAL")
        if not candidates:
            return
        elemental = game._entity(game.rng.choice(candidates), created_by=context.card.card_id)
        elemental.cost_delta -= 3
        game._add_generated(context.player, elemental)
        game._event("inferno_herald", player=context.player.index,
                    source=context.card.entity_id, card=elemental.card_id)


# ---- Standard tranche 50H -------------------------------------------------
# This tranche deliberately keeps deck, hand and generated-card state on the
# engine entities.  It avoids a second, card-specific shadow game state, which
# is important because an ISMCTS clone must retain exactly the same pending
# effect and deck order as its parent branch.


def _imp_formant(game: Any, source: Any, controller: int) -> Any:
    """Create the printed Imp-formant token used by the Violet Hold cards."""
    card_id = "CAP_400t2t" if "CAP_400t2t" in game.card_defs else "CAP_400t"
    imp = game._entity(card_id, created_by=source.card_id)
    imp.summoned_when_drawn = True
    imp.summon_when_drawn_for = controller
    return imp


@dataclass(frozen=True)
class MoveImpFormantToEnemyTop:
    def execute(self, game: Any, context: RuleContext) -> None:
        enemy = game.players[1 - context.player.index]
        candidates = [card for card in enemy.deck if card.card_id in {"CAP_400t2t", "CAP_400t"}]
        if not candidates:
            return
        chosen = game.rng.choice(candidates)
        enemy.deck.remove(chosen)
        chosen.attack_delta += 2
        chosen.health_delta += 2
        enemy.deck.append(chosen)
        game._event("corrupt_constable", player=context.player.index,
                    source=context.card.entity_id, target=chosen.entity_id)


@dataclass(frozen=True)
class FollowEvidence:
    def execute(self, game: Any, context: RuleContext) -> None:
        enemy = game.players[1 - context.player.index]
        enemy.deck.insert(game.rng.randrange(len(enemy.deck) + 1),
                          _imp_formant(game, context.card, context.player.index))
        PassTemporaryPlayEffect("CAP_402").execute(game, context)


@dataclass(frozen=True)
class FrameJob:
    def execute(self, game: Any, context: RuleContext) -> None:
        enemy = game.players[1 - context.player.index]
        victims = list(enemy.board)
        game.rng.shuffle(victims)
        for victim in victims[:2]:
            victim.damage = victim.max_health
        game._resolve_deaths()
        game._offer_enemy_deck_top_discover(
            context.player, enemy, source_card_id=context.card.card_id,
        )


@dataclass(frozen=True)
class OtherMinionsGainCostDeathrattle:
    def execute(self, game: Any, context: RuleContext) -> None:
        for minion in context.player.board:
            if minion.entity_id != context.card.entity_id:
                minion.deathrattle_summon_random_cost = minion.definition.cost
        game._event("ulfar_deathrattles", player=context.player.index,
                    source=context.card.entity_id)


@dataclass(frozen=True)
class DiscoverSummonFreeze:
    cost: int

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = _filtered_executable_ids(game, card_type="MINION", cost=self.cost)
        if candidates:
            game._offer_discover(context.player, candidates, False,
                                 source_card_id=context.card.card_id,
                                 after_pick="summon_freeze")


@dataclass(frozen=True)
class DiscoverDeadDragonAndResummon:
    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [minion.card_id for minion in context.player.dead_minions
                      if minion.has_race("DRAGON")]
        if candidates:
            game._offer_discover(context.player, candidates, False,
                                 source_card_id=context.card.card_id,
                                 after_pick="resummon_discover")


@dataclass(frozen=True)
class SmolderingDraw:
    def execute(self, game: Any, context: RuleContext) -> None:
        for _ in range(1 + getattr(context.card, "smoldering_stage", 0)):
            game._draw(context.player)


@dataclass(frozen=True)
class SmolderingBuff:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player != context.player.index:
            raise ValueError("friendly minion target is required")
        target = game._find_minion(context.player.index, context.action.target_entity)
        amount = 1 + getattr(context.card, "smoldering_stage", 0)
        target.attack_delta += amount
        target.health_delta += amount


@dataclass(frozen=True)
class SmolderingEnemyBoardDamage:
    def execute(self, game: Any, context: RuleContext) -> None:
        amount = game._spell_effect_amount(
            context.player, context.card, 1 + getattr(context.card, "smoldering_stage", 0),
        )
        enemy = game.players[1 - context.player.index]
        for minion in list(enemy.board):
            game._damage_minion(enemy.index, minion, amount, context.card)
        game._resolve_deaths()


@dataclass(frozen=True)
class LightNewMoon:
    def execute(self, game: Any, context: RuleContext) -> None:
        BuffActionTarget(3, 3).execute(game, context)
        if context.card.spells_cast_while_held >= 3 and len(context.player.hand) < 10:
            context.player.hand.append(context.card)
            game._event("light_new_moon_return", player=context.player.index,
                        source=context.card.entity_id)


@dataclass(frozen=True)
class DiscoverFiveCostAndTemporaryMana:
    def execute(self, game: Any, context: RuleContext) -> None:
        OfferFilteredDiscover(card_type=None, cost=5).execute(game, context)
        context.player.start_turn_temporary_mana_charges += 1


@dataclass(frozen=True)
class DiscountHandIfUniqueCosts:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        costs = [card.cost for card in context.player.hand]
        if len(costs) != len(set(costs)):
            return
        for card in context.player.hand:
            card.cost_delta -= self.amount


@dataclass(frozen=True)
class DiscoverFelAndDiscountHand:
    def execute(self, game: Any, context: RuleContext) -> None:
        for card in context.player.hand:
            if card.definition.card_type == "SPELL" and card.definition.spell_school == "FEL":
                card.cost_delta -= 1
        OfferFilteredDiscover(card_type="SPELL", spell_school="FEL").execute(game, context)


@dataclass(frozen=True)
class GetThreeArcaneMissiles:
    def execute(self, game: Any, context: RuleContext) -> None:
        for _ in range(3):
            game._add_generated(context.player, game._entity("CORE_EX1_277", created_by=context.card.card_id))


@dataclass(frozen=True)
class DamageTargetShuffleTwoCostCopyIfKilled:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_entity is None:
            raise ValueError("minion target is required")
        target = game._find_minion(context.action.target_player, context.action.target_entity)
        game._damage_minion(context.action.target_player, target, self.amount, context.card)
        killed = target.health <= 0
        game._resolve_deaths()
        if killed:
            copied = target.clone(game.next_entity_id)
            game.next_entity_id += 1
            copied.cost_delta += 2 - copied.cost
            copied.created_by = context.card.card_id
            context.player.deck.insert(game.rng.randrange(len(context.player.deck) + 1), copied)


@dataclass(frozen=True)
class ShadowRounds:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_entity is None:
            raise ValueError("enemy minion target is required")
        target = game._find_minion(context.action.target_player, context.action.target_entity)
        game._damage_minion(context.action.target_player, target, 2, context.card)
        killed = target.health <= 0
        game._resolve_deaths()
        # "Cast this on another random enemy minion" can enter a self-feeding
        # deathrattle/summon chain in a simulator (for example when every
        # victim immediately produces another killable body).  The live game
        # has effect-resolution safeguards; impose an explicit branch-local
        # budget here so a single rollout cannot run forever.  Thirty-two is
        # far above an ordinary seven-slot board clear and the cap is emitted
        # for audit rather than silently treated as a natural termination.
        chained_casts = 0
        max_chained_casts = 32
        while killed and chained_casts < max_chained_casts:
            enemy = game.players[1 - context.player.index]
            candidates = [
                minion for minion in enemy.board
                if minion.dormant_turns == 0 and minion.health > 0
            ]
            if not candidates:
                return
            target = game.rng.choice(candidates)
            game._damage_minion(enemy.index, target, 2, context.card)
            killed = target.health <= 0
            game._resolve_deaths()
            chained_casts += 1
        if killed:
            game._event(
                "effect_resolution_capped",
                source=context.card.card_id,
                player=context.player.index,
                effect="shadow_rounds",
                chained_casts=chained_casts,
                limit=max_chained_casts,
            )


@dataclass(frozen=True)
class SetReinforcementAura:
    turns: int = 3

    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.reinforcement_aura_turns += self.turns


@dataclass(frozen=True)
class BuffHandMinionsWithLegendaryBonus:
    def execute(self, game: Any, context: RuleContext) -> None:
        for card in context.player.hand:
            if card.definition.card_type != "MINION":
                continue
            card.attack_delta += 1
            card.health_delta += 1
            if card.definition.rarity == "LEGENDARY":
                card.attack_delta += 2
                card.health_delta += 1


@dataclass(frozen=True)
class DiscountOpponentCopies:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        for card in context.player.hand:
            if card.copied_from_opponent:
                card.cost_delta -= self.amount


@dataclass(frozen=True)
class AddDetectiveClothes:
    def execute(self, game: Any, context: RuleContext) -> None:
        game._add_generated(context.player, game._entity("JAIL_447t", created_by=context.card.card_id))


@dataclass(frozen=True)
class AddLegendaryOneOneCopies:
    count: int = 3

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [card_id for card_id in game.executable_card_ids
                      if card_id in game.card_defs
                      and game.card_defs[card_id].card_type == "MINION"
                      and game.card_defs[card_id].rarity == "LEGENDARY"]
        for _ in range(self.count):
            if not candidates:
                return
            card = game._entity(game.rng.choice(sorted(candidates)), created_by=context.card.card_id)
            card.cost_delta += 1 - card.cost
            card.attack_delta += 1 - card.attack
            card.health_delta += 1 - card.max_health
            game._add_generated(context.player, card)


@dataclass(frozen=True)
class AddRandomEightCostMinionsDiscountByTwoCostPlays:
    count: int = 2

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = _filtered_executable_ids(game, card_type="MINION", cost=8)
        for _ in range(self.count):
            if not candidates:
                return
            card = game._entity(game.rng.choice(candidates), created_by=context.card.card_id)
            card.cost_delta -= context.player.two_cost_cards_played_this_game
            game._add_generated(context.player, card)


@dataclass(frozen=True)
class SummonDeckMinionsWithRush:
    max_cost: int
    count: int

    def execute(self, game: Any, context: RuleContext) -> None:
        for _ in range(self.count):
            if len(context.player.board) + len(context.player.locations) >= 7:
                return
            candidates = [card for card in context.player.deck
                          if card.definition.card_type == "MINION" and card.cost <= self.max_cost]
            if not candidates:
                return
            card = game.rng.choice(candidates)
            context.player.deck.remove(card)
            card.rush = True
            card.summoned_turn = game.turn
            game._summon(context.player, card)


@dataclass(frozen=True)
class AddRandomSpellsDiscounted:
    cost: int
    count: int
    discount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = _filtered_executable_ids(game, card_type="SPELL", cost=self.cost)
        for _ in range(self.count):
            if not candidates:
                return
            card = game._entity(game.rng.choice(candidates), created_by=context.card.card_id)
            card.cost_delta -= self.discount
            game._add_generated(context.player, card)


@dataclass(frozen=True)
class DiscoverDeckCardOrGainStats:
    def execute(self, game: Any, context: RuleContext) -> None:
        if not context.player.deck:
            context.card.attack_delta += 4
            context.card.health_delta += 4
            return
        game._offer_deck_card_discover(context.player, source_card_id=context.card.card_id)


@dataclass(frozen=True)
class Stormfury:
    def execute(self, game: Any, context: RuleContext) -> None:
        enemy = game.players[1 - context.player.index]
        context.card.lifesteal = True
        for minion in list(enemy.board):
            game._damage_minion(enemy.index, minion,
                                game._spell_effect_amount(context.player, context.card, 2), context.card)
        game._resolve_deaths()


@dataclass(frozen=True)
class AddRandomHighCostSpell:
    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = _filtered_executable_ids(game, card_type="SPELL", min_cost=5)
        if candidates:
            card = game._entity(game.rng.choice(candidates), created_by=context.card.card_id)
            if not context.player.deck_started_with_spells:
                card.cost_delta -= 5
            game._add_generated(context.player, card)


@dataclass(frozen=True)
class AddVoidSoul:
    def execute(self, game: Any, context: RuleContext) -> None:
        from .dragon_mirror import VOID_SOUL_DEMON_IDS_BY_COST
        cost = min(10, max(1, context.player.void_soul_level))
        candidates = sorted(VOID_SOUL_DEMON_IDS_BY_COST.get(cost, ()))
        if candidates:
            soul = game._entity("JAIL_732", created_by=context.card.card_id)
            soul.void_soul_cost = cost
            game._add_generated(context.player, soul)


@dataclass(frozen=True)
class TriggerDeathrattleOfRandomDead:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.player.dead_minions:
            game._deathrattle(context.player, game.rng.choice(context.player.dead_minions))


@dataclass(frozen=True)
class RandomPlayableTemporarySpell:
    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [card_id for card_id in game.executable_card_ids
                      if card_id in game.card_defs
                      and game.card_defs[card_id].card_type == "SPELL"
                      and game.card_defs[card_id].cost <= context.player.mana]
        if candidates:
            card = game._entity(game.rng.choice(sorted(candidates)), created_by=context.card.card_id)
            card.temporary = True
            game._add_generated(context.player, card)


@dataclass(frozen=True)
class SummonTokenDeathrattle:
    card_id: str
    count: int = 1

    def execute(self, game: Any, context: RuleContext) -> None:
        Summon(self.card_id, self.count).execute(game, context)


@dataclass(frozen=True)
class DiscountRandomOpponentHandMinion:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        enemy = game.players[1 - context.player.index]
        candidates = [card for card in enemy.hand if card.definition.card_type == "MINION"]
        if candidates:
            game.rng.choice(candidates).cost_delta -= self.amount


@dataclass(frozen=True)
class AncientRaptorChoice:
    def execute(self, game: Any, context: RuleContext) -> None:
        OfferEffectChoice((
            ("Attack", (SetSourceAttributes((("attack_delta", context.card.attack_delta + 3),)),)),
            ("Divine Shield", (SetSourceAttributes((("divine_shield", True), ("divine_shield_hits", 1))),)),
            ("Plants", (SetSourceAttributes((("deathrattle_summon_token_id", "__ancient_raptor_plant"), ("deathrattle_summon_token_count", 2))),)),
        )).execute(game, context)


@dataclass(frozen=True)
class ThresherAfterSpell:
    def execute(self, game: Any, context: RuleContext) -> None:
        context.card.divine_shield = True
        context.card.divine_shield_hits = max(1, context.card.divine_shield_hits)


@dataclass(frozen=True)
class ReturnLastTurnSpells:
    def execute(self, game: Any, context: RuleContext) -> None:
        returned: list[int] = []
        for spell in context.player.spells_last_turn_for_replay:
            if len(context.player.hand) >= 10:
                break
            replay = spell.clone(game.next_entity_id)
            game.next_entity_id += 1
            replay.created_by = context.card.card_id
            replay.spell_casts_twice = False
            replay.temporary = False
            context.player.hand.append(replay)
            returned.append(replay.entity_id)
        game._event("kragwa_return_spells", player=context.player.index,
                    source=context.card.entity_id, returned=returned)


@dataclass(frozen=True)
class EscapeAfterAttack:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.card not in context.player.board or context.card.health <= 0:
            return
        game._draw(context.player)
        if context.card in context.player.board:
            context.player.board.remove(context.card)
            game._event("escape_artist", player=context.player.index,
                        source=context.card.entity_id, escaped=True)


@dataclass(frozen=True)
class BuffActionTargetAndRush:
    attack: int
    health: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("minion target is required")
        target = game._find_minion(context.action.target_player, context.action.target_entity)
        target.attack_delta += self.attack
        target.health_delta += self.health
        target.rush = True


@dataclass(frozen=True)
class GrantDeathrattleRandomMinion:
    cost: int
    count: int = 1
    mechanic: str | None = None

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player != context.player.index:
            raise ValueError("friendly minion target is required")
        target = game._find_minion(context.player.index, context.action.target_entity)
        target.deathrattle_summon_random_cost = self.cost
        target.deathrattle_summon_token_count = self.count
        target.deathrattle_summon_mechanic = self.mechanic


@dataclass(frozen=True)
class GainRebornAtEndTurn:
    def execute(self, _game: Any, context: RuleContext) -> None:
        context.card.reborn = True


@dataclass(frozen=True)
class CapturedArchmageDeathrattle:
    def execute(self, game: Any, context: RuleContext) -> None:
        count = sum(card.card_id == "JAIL_974" for card in context.player.dead_minions)
        # The just-dead source is already in dead_minions, hence five total.
        if count < 5:
            return
        targets = game._random_enemy_characters(context.player.index)
        if targets:
            game._deal_to_target(context.player.index, game.rng.choice(targets), 6, context.card)
            game._resolve_deaths()


@dataclass(frozen=True)
class WidowBite:
    attack: int
    armor: int
    followup: str | None = None

    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.hero_attack_bonus += self.attack
        game._gain_armor(context.player, self.armor)
        if self.followup is not None:
            game._add_generated(context.player, game._entity(self.followup, created_by=context.card.card_id))


@dataclass(frozen=True)
class SummonRandomBeast:
    cost: int

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = _filtered_executable_ids(game, card_type="MINION", cost=self.cost, race="BEAST")
        if not candidates or len(context.player.board) + len(context.player.locations) >= 7:
            return
        card = game._entity(game.rng.choice(candidates), created_by=context.card.card_id)
        card.summoned_turn = game.turn
        game._summon(context.player, card)


@dataclass(frozen=True)
class SummonRandomMinionMatching:
    cost: int
    mechanic: str | None = None

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = _filtered_executable_ids(
            game, card_type="MINION", cost=self.cost, mechanic=self.mechanic,
        )
        if not candidates or len(context.player.board) + len(context.player.locations) >= 7:
            return
        card = game._entity(game.rng.choice(candidates), created_by=context.card.card_id)
        card.summoned_turn = game.turn
        game._summon(context.player, card)


@dataclass(frozen=True)
class SpitefulChef:
    def execute(self, game: Any, context: RuleContext) -> None:
        cost = 6 if context.player.max_mana >= 10 else 2
        candidates = _filtered_executable_ids(game, card_type="MINION", cost=cost, mechanic="TAUNT")
        if candidates and len(context.player.board) + len(context.player.locations) < 7:
            card = game._entity(game.rng.choice(candidates), created_by=context.card.card_id)
            card.summoned_turn = game.turn
            game._summon(context.player, card)


@dataclass(frozen=True)
class ArcaneTripwireDamage:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        enemy = game.players[1 - context.player.index]
        targets: list[tuple[int, int | None]] = [(enemy.index, None)] + [
            (enemy.index, minion.entity_id)
            for minion in enemy.board if minion.dormant_turns == 0
        ]
        if not targets:
            return
        base, remainder = divmod(self.amount, len(targets))
        for index, target in enumerate(targets):
            game._deal_to_target(context.player.index, target, base + (1 if index < remainder else 0), context.card)
        game._resolve_deaths()


@dataclass(frozen=True)
class Tripwire:
    kind: str

    def execute(self, game: Any, context: RuleContext) -> None:
        if self.kind == "beast":
            SummonRandomBeast(5).execute(game, context)
            token_id = "JAIL_879t"
        else:
            ArcaneTripwireDamage(4).execute(game, context)
            token_id = "JAIL_881t"
        for _ in range(2):
            token = game._entity(token_id, created_by=context.card.card_id)
            context.player.deck.insert(game.rng.randrange(len(context.player.deck) + 1), token)
        game._event("tripwire_shuffled", player=context.player.index,
                    source=context.card.entity_id, card=token_id, count=2)


@dataclass(frozen=True)
class OfferHighCostSpellThatCastsTwice:
    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = _filtered_executable_ids(game, card_type="SPELL", min_cost=5)
        if candidates:
            game._offer_discover(context.player, candidates, False,
                                 source_card_id=context.card.card_id,
                                 after_pick="spell_twice")



@dataclass(frozen=True)
class CostEnemyHeroDamageThisTurn:
    def adjustment(self, game: Any, player: Any, card: Any) -> int:
        return -max(0, int(getattr(player, "enemy_hero_damage_this_turn", 0)))


@dataclass(frozen=True)
class BuffAllOtherFriendlyMinions:
    attack: int = 0
    health: int = 0

    def execute(self, game: Any, context: RuleContext) -> None:
        affected: list[int] = []
        for minion in context.player.board:
            if minion.entity_id == context.card.entity_id or minion.dormant_turns > 0:
                continue
            minion.attack_delta += self.attack
            minion.health_delta += self.health
            affected.append(minion.entity_id)
        game._event("time_other_minion_buff", player=context.player.index,
                    source=context.card.entity_id, affected=affected,
                    attack=self.attack, health=self.health)


@dataclass(frozen=True)
class ResurrectHighestCostUndead:
    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [card for card in context.player.dead_minions if card.has_race("UNDEAD")]
        if not candidates or len(context.player.board) + len(context.player.locations) >= 7:
            return
        highest = max(card.definition.cost for card in candidates)
        chosen = game.rng.choice([card for card in candidates if card.definition.cost == highest])
        minion = game._entity(chosen.card_id, created_by=context.card.card_id)
        minion.summoned_turn = game.turn
        game._summon(context.player, minion)
        game._event("memoriam_manifest", player=context.player.index,
                    source=context.card.card_id, entity=minion.entity_id,
                    card=minion.card_id, cost=highest)


@dataclass(frozen=True)
class AddRandomDreamCard:
    """Hopeful Dryad uses the fixed Dream-card family, not a text search."""

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [
            card_id for card_id in ("DREAM_01", "DREAM_02", "DREAM_03", "DREAM_04", "DREAM_05")
            if card_id in game.card_defs and card_id in game.executable_card_ids
        ]
        if candidates:
            game._add_generated(context.player, game._entity(
                game.rng.choice(candidates), created_by=context.card.card_id,
            ))


@dataclass(frozen=True)
class OptionalBuffActionTarget:
    attack: int = 0
    health: int = 0

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_entity is None:
            return
        BuffActionTarget(self.attack, self.health).execute(game, context)


@dataclass(frozen=True)
class SetNextRaceCostReduction:
    race: str
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        attribute = {
            "DEMON": "next_demon_cost_reduction",
            "BEAST": "next_beast_cost_reduction",
            "MURLOC": "next_murloc_cost_reduction",
        }.get(self.race)
        if attribute is None:
            raise ValueError(f"unsupported race cost reducer: {self.race}")
        setattr(context.player, attribute, max(0, getattr(context.player, attribute) + self.amount))
        game._event(
            "next_race_cost_reduction", player=context.player.index,
            source=context.card.card_id, race=self.race, amount=self.amount,
        )


@dataclass(frozen=True)
class SetNextComboCostReduction:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.next_combo_cost_reduction = max(
            context.player.next_combo_cost_reduction, self.amount,
        )
        game._event(
            "next_combo_cost_reduction", player=context.player.index,
            source=context.card.card_id, amount=self.amount,
        )


@dataclass(frozen=True)
class ResurrectHighestCostFriendly:
    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [card for card in context.player.dead_minions if card.definition.card_type == "MINION"]
        if not candidates or len(context.player.board) + len(context.player.locations) >= 7:
            return
        highest = max(card.definition.cost for card in candidates)
        chosen = game.rng.choice([card for card in candidates if card.definition.cost == highest])
        resurrected = game._entity(chosen.card_id, created_by=context.card.card_id)
        resurrected.summoned_turn = game.turn
        game._summon(context.player, resurrected)
        game._event(
            "resurrect_highest_cost", player=context.player.index,
            source=context.card.card_id, card=resurrected.card_id,
            entity=resurrected.entity_id, cost=highest,
        )


@dataclass(frozen=True)
class SummonOpponentRandomHandMinion:
    def execute(self, game: Any, context: RuleContext) -> None:
        opponent = game.players[1 - context.player.index]
        candidates = [card for card in opponent.hand if card.definition.card_type == "MINION"]
        if not candidates or len(opponent.board) + len(opponent.locations) >= 7:
            return
        minion = game.rng.choice(candidates)
        opponent.hand.remove(minion)
        minion.summoned_turn = game.turn
        game._summon(opponent, minion)
        game._event(
            "opponent_hand_minion_summoned", player=context.player.index,
            source=context.card.card_id, target_player=opponent.index,
            card=minion.card_id, entity=minion.entity_id,
        )


@dataclass(frozen=True)
class SummonRaceFromHandAndDeck:
    race: str

    def execute(self, game: Any, context: RuleContext) -> None:
        player = context.player
        for zone_name in ("hand", "deck"):
            if len(player.board) + len(player.locations) >= 7:
                break
            zone = getattr(player, zone_name)
            candidates = [card for card in zone if card.has_race(self.race)]
            if not candidates:
                continue
            minion = game.rng.choice(candidates)
            zone.remove(minion)
            minion.summoned_turn = game.turn
            game._summon(player, minion)
            game._event(
                "summon_race_from_zone", player=player.index,
                source=context.card.card_id, zone=zone_name,
                race=self.race, card=minion.card_id, entity=minion.entity_id,
            )


@dataclass(frozen=True)
class EquipFixedWeapon:
    card_id: str
    name: str
    attack: int
    durability: int

    def execute(self, game: Any, context: RuleContext) -> None:
        from .dragon_mirror import Weapon
        game._equip_weapon(
            context.player, Weapon(self.card_id, self.name, self.attack, self.durability),
        )


@dataclass(frozen=True)
class EndTurnBuffRandomOther:
    attack: int
    health: int

    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [
            minion for minion in context.player.board
            if minion.entity_id != context.card.entity_id
            and minion.dormant_turns == 0 and minion.health > 0
        ]
        if not candidates:
            return
        target = game.rng.choice(candidates)
        target.attack_delta += self.attack
        target.health_delta += self.health
        game._event(
            "end_turn_random_buff", player=context.player.index,
            source=context.card.entity_id, target=target.entity_id,
            attack=self.attack, health=self.health,
        )


@dataclass(frozen=True)
class RemoveTopOpponentDeckCard:
    def execute(self, game: Any, context: RuleContext) -> None:
        opponent = game.players[1 - context.player.index]
        if not opponent.deck:
            return
        removed = opponent.deck.pop()
        game._event(
            "remove_top_opponent_deck_card", player=context.player.index,
            source=context.card.card_id, target_player=opponent.index,
            card=removed.card_id, entity=removed.entity_id,
        )


def _return_minion_to_hand(game: Any, owner: Any, target: Any, source: str) -> str:
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
        game._on_enter_hand_from_battlefield(owner, target, source=source)
        destination = "hand"
    else:
        destination = "burned"
    game._event(
        "return_to_hand", player=owner.index, entity=target.entity_id,
        card=target.card_id, source=source, destination=destination,
    )
    return destination


@dataclass(frozen=True)
class ReturnRandomEnemyMinion:
    def execute(self, game: Any, context: RuleContext) -> None:
        enemy = game.players[1 - context.player.index]
        candidates = game._random_enemy_minions(context.player.index)
        if candidates:
            _return_minion_to_hand(game, enemy, game.rng.choice(candidates), context.card.card_id)


@dataclass(frozen=True)
class SummonLongneckAndBuff:
    def execute(self, game: Any, context: RuleContext) -> None:
        Summon("DINO_130t").execute(game, context)
        for minion in context.player.board:
            if minion.dormant_turns == 0:
                minion.attack_delta += 1
                minion.health_delta += 1
        game._event("longneck_egg_hatched", player=context.player.index,
                    source=context.card.card_id)


@dataclass(frozen=True)
class SummonRandomDeckRaceWithLifesteal:
    race: str

    def execute(self, game: Any, context: RuleContext) -> None:
        player = context.player
        if len(player.board) + len(player.locations) >= 7:
            return
        candidates = [card for card in player.deck if card.has_race(self.race)]
        if not candidates:
            return
        minion = game.rng.choice(candidates)
        player.deck.remove(minion)
        minion.lifesteal = True
        minion.summoned_turn = game.turn
        game._summon(player, minion)
        game._event("summon_deck_race_lifesteal", player=player.index,
                    source=context.card.card_id, card=minion.card_id,
                    entity=minion.entity_id, race=self.race)


@dataclass(frozen=True)
class SetActionTargetStatsAndKeyword:
    attack: int
    health: int
    keyword: str

    def execute(self, game: Any, context: RuleContext) -> None:
        SetActionTargetStats(self.attack, self.health).execute(game, context)
        target = game._find_minion(context.action.target_player, context.action.target_entity)
        setattr(target, self.keyword, True)
        game._event("set_target_keyword", player=context.player.index,
                    source=context.card.card_id, target=target.entity_id,
                    keyword=self.keyword)


@dataclass(frozen=True)
class ScheduleHatchingCeremony:
    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.hatching_ceremony_trigger_turn = context.player.turns_taken + 1
        game._event("hatching_ceremony_scheduled", player=context.player.index,
                    source=context.card.card_id,
                    trigger_turn=context.player.hatching_ceremony_trigger_turn)


@dataclass(frozen=True)
class AddRandomMultiRaceMinion:
    def execute(self, game: Any, context: RuleContext) -> None:
        candidates = [
            card_id for card_id in _filtered_executable_ids(game, card_type="MINION")
            if len(set(game.card_defs[card_id].races) | ({game.card_defs[card_id].race} if game.card_defs[card_id].race else set())) >= 2
        ]
        if candidates:
            game._add_generated(context.player, game._entity(
                game.rng.choice(candidates), created_by=context.card.card_id,
            ))


@dataclass(frozen=True)
class AnkylodonDeathrattle:
    def execute(self, game: Any, context: RuleContext) -> None:
        player = context.player
        for _ in range(2):
            if len(player.board) + len(player.locations) >= 7:
                break
            candidates = [
                card_id for card_id in _filtered_executable_ids(
                    game, card_type="MINION", cost=3, race="BEAST",
                )
            ]
            if not candidates:
                break
            minion = game._entity(game.rng.choice(candidates), created_by=context.card.card_id)
            minion.summoned_turn = game.turn
            game._summon(player, minion)
            targets = game._random_enemy_characters(player.index)
            if not targets:
                continue
            target_player, target_entity = game.rng.choice(targets)
            if target_entity is None:
                game._damage_hero(game.players[target_player], minion.attack, minion)
            else:
                target = game._find_minion(target_player, target_entity)
                game._forced_minion_attack(player.index, minion, target_player, target)
            game._resolve_deaths()


@dataclass(frozen=True)
class SummonRandomTauntCosts:
    costs: tuple[int, ...]

    def execute(self, game: Any, context: RuleContext) -> None:
        for cost in self.costs:
            SummonRandomExecutableMinion(cost=cost, require_taunt=True).execute(game, context)


@dataclass(frozen=True)
class SummonRandomCostWithTaunt:
    cost: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if len(context.player.board) + len(context.player.locations) >= 7:
            return
        candidates = _filtered_executable_ids(game, card_type="MINION", cost=self.cost)
        if not candidates:
            return
        minion = game._entity(game.rng.choice(candidates), created_by=context.card.card_id)
        minion.taunt = True
        minion.summoned_turn = game.turn
        game._summon(context.player, minion)


@dataclass(frozen=True)
class BuffTopDeckMinions:
    count: int
    attack: int
    health: int

    def execute(self, game: Any, context: RuleContext) -> None:
        affected = []
        for card in reversed(context.player.deck):
            if card.definition.card_type != "MINION":
                continue
            card.attack_delta += self.attack
            card.health_delta += self.health
            affected.append(card.entity_id)
            if len(affected) >= self.count:
                break
        game._event("buff_top_deck_minions", player=context.player.index,
                    source=context.card.card_id, affected=affected,
                    attack=self.attack, health=self.health)


@dataclass(frozen=True)
class SetTargetStatsByAllegiance:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("minion target is required")
        target = game._find_minion(context.action.target_player, context.action.target_entity)
        if context.action.target_player == context.player.index:
            target.attack_delta += 3
            target.health_delta += 3
            mode = "friendly_buff"
        else:
            target.attack_delta += 1 - target.attack
            target.health_delta += 1 - target.max_health
            mode = "enemy_set_one"
        game._event("mark_of_ursol", player=context.player.index,
                    source=context.card.card_id, target=target.entity_id, mode=mode)


@dataclass(frozen=True)
class SummonCopyIfSourceAttackAtLeast:
    attack: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.card.attack < self.attack or len(context.player.board) + len(context.player.locations) >= 7:
            return
        copied = context.card.clone(game.next_entity_id)
        game.next_entity_id += 1
        copied.created_by = context.card.card_id
        copied.summoned_turn = game.turn
        game._summon(context.player, copied)
        game._event("summon_source_copy", player=context.player.index,
                    source=context.card.entity_id, entity=copied.entity_id)


@dataclass(frozen=True)
class DestroyFriendlyMinionGainArmor:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player != context.player.index:
            raise ValueError("friendly minion target is required")
        target = game._find_minion(context.player.index, context.action.target_entity)
        target.damage = target.max_health
        game._resolve_deaths()
        game._gain_armor(context.player, self.amount)


@dataclass(frozen=True)
class GrantHeroDivineShield:
    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.hero_divine_shield = True
        context.player.hero_divine_shield_hits = max(1, context.player.hero_divine_shield_hits)
        game._event("hero_divine_shield", player=context.player.index,
                    source=context.card.card_id)


@dataclass(frozen=True)
class DiscountRightmostHeldCard:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if not context.player.hand:
            return
        target = context.player.hand[-1]
        target.cost_delta -= self.amount
        game._event(
            "discount_rightmost_hand_card", player=context.player.index,
            source=context.card.card_id, target=target.entity_id,
            card=target.card_id, amount=self.amount,
        )


@dataclass(frozen=True)
class ShuffleDiscountedSourceAtBottom:
    cost: int

    def execute(self, game: Any, context: RuleContext) -> None:
        copy = game._entity(context.card.card_id, created_by=context.card.card_id)
        copy.cost_delta += self.cost - copy.definition.cost
        context.player.deck.insert(0, copy)
        game._event("shuffle_source_bottom", player=context.player.index,
                    source=context.card.card_id, entity=copy.entity_id, cost=copy.cost)


@dataclass(frozen=True)
class OfferMechIfControllingAnother:
    def execute(self, game: Any, context: RuleContext) -> None:
        controls_other_mech = any(
            minion.entity_id != context.card.entity_id and minion.has_race("MECH")
            for minion in context.player.board
        )
        if controls_other_mech:
            OfferFilteredDiscover(card_type="MINION", race="MECH").execute(game, context)


@dataclass(frozen=True)
class BuffCurrentWeaponDurabilityIfBeast:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.player.weapon is None:
            return
        if any(minion.has_race("BEAST") for minion in context.player.board):
            context.player.weapon.durability += 1
            game._event("weapon_durability_buff", player=context.player.index,
                        source=context.card.card_id, amount=1,
                        weapon=context.player.weapon.card_id)


@dataclass(frozen=True)
class FillHandWithToken:
    card_id: str

    def execute(self, game: Any, context: RuleContext) -> None:
        while len(context.player.hand) < 10:
            context.player.hand.append(game._entity(self.card_id, created_by=context.card.card_id))
        game._event("fill_hand_tokens", player=context.player.index,
                    source=context.card.card_id, token=self.card_id)


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


# ---- Standard tranche 50C -------------------------------------------------
# This tranche is deliberately grouped around shared state transitions:
# temporary cost windows, post-Hero-Power triggers, conditional turn stats,
# generated tokens, and small Discover pools.  That keeps the declarations
# below readable and avoids scattering card-id checks through the engine.


@dataclass(frozen=True)
class EachPlayerDraw:
    def execute(self, game: Any, context: RuleContext) -> None:
        for player in game.players:
            game._draw(player)


@dataclass(frozen=True)
class ApplyHeroPowerSurcharge:
    amount: int = 2

    def execute(self, game: Any, context: RuleContext) -> None:
        opponent = game.players[1 - context.player.index]
        opponent.hero_power_cost_surcharge += self.amount
        # The next call to _start_turn belongs to the opponent.  The engine's
        # global turn increments at that boundary, so this is a one-turn
        # window rather than an unbounded "next power" discount.
        opponent.hero_power_cost_surcharge_expiry_turn = game.turn + 1
        game._event(
            "hero_power_surcharge", player=opponent.index,
            source=context.card.card_id, amount=self.amount,
            expiry_turn=opponent.hero_power_cost_surcharge_expiry_turn,
        )


@dataclass(frozen=True)
class SwapActionTargetAttackHealth:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("minion target is required")
        target = game._find_minion(
            context.action.target_player, context.action.target_entity
        )
        attack, health = target.attack, target.max_health
        target.attack_delta += health - attack
        target.health_delta += attack - health
        game._event(
            "swap_attack_health", player=context.player.index,
            source=context.card.card_id, target=target.entity_id,
            attack=target.attack, health=target.max_health,
        )
        game._resolve_deaths()


@dataclass(frozen=True)
class HenchClanThugAfterHeroAttack:
    def execute(self, game: Any, context: RuleContext) -> None:
        context.card.attack_delta += 1
        context.card.health_delta += 1
        game._event(
            "hench_clan_thug_buff", player=context.player.index,
            entity=context.card.entity_id,
        )


@dataclass(frozen=True)
class WitchwoodGrizzlyBattlecry:
    def execute(self, game: Any, context: RuleContext) -> None:
        lost_health = len(game.players[1 - context.player.index].hand)
        context.card.health_delta -= lost_health
        game._event(
            "witchwood_grizzly_health", player=context.player.index,
            entity=context.card.entity_id, lost=lost_health,
        )
        game._resolve_deaths()


@dataclass(frozen=True)
class OfferDragonDiscoverIfHolding:
    def execute(self, game: Any, context: RuleContext) -> None:
        if not game._holding_dragon(context.player):
            return
        pool = [
            card_id for card_id, definition in game.card_defs.items()
            if card_id in game.executable_card_ids
            and definition.card_type == "MINION"
            and (definition.race == "DRAGON" or "DRAGON" in definition.races)
        ]
        game._offer_discover(
            context.player, pool, False, source_card_id=context.card.card_id
        )


@dataclass(frozen=True)
class ApplyOpponentSpellSurchargeNextTurn:
    amount: int = 1

    def execute(self, game: Any, context: RuleContext) -> None:
        opponent = game.players[1 - context.player.index]
        expiry_turn = game.turn + 1
        if opponent.spell_cost_surcharge_turn == expiry_turn:
            opponent.spell_cost_surcharge += self.amount
        else:
            opponent.spell_cost_surcharge = self.amount
            opponent.spell_cost_surcharge_turn = expiry_turn
        game._event(
            "spell_cost_surcharge", player=opponent.index,
            source=context.card.card_id, amount=opponent.spell_cost_surcharge,
            expiry_turn=expiry_turn,
        )


@dataclass(frozen=True)
class AnimatedMoonwellAfterSpell:
    def execute(self, game: Any, context: RuleContext) -> None:
        spell = context.payload.get("spell")
        if spell is None:
            return
        amount = max(0, int(context.payload.get("paid_cost", spell.cost)))
        context.card.attack_delta += amount
        game._event(
            "animated_moonwell_attack", player=context.player.index,
            entity=context.card.entity_id, spell=spell.card_id, amount=amount,
        )


@dataclass(frozen=True)
class GainSourceHealth:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        context.card.health_delta += self.amount
        game._event(
            "source_health_gain", player=context.player.index,
            entity=context.card.entity_id, amount=self.amount,
        )


@dataclass(frozen=True)
class GainEmptyManaForBothPlayers:
    amount: int = 1

    def execute(self, game: Any, context: RuleContext) -> None:
        gained: dict[int, int] = {}
        for player in game.players:
            before = player.max_mana
            player.max_mana = min(10, player.max_mana + self.amount)
            gained[player.index] = player.max_mana - before
        game._event(
            "gain_empty_mana_both", player=context.player.index,
            source=context.card.card_id, gained=gained,
        )


@dataclass(frozen=True)
class RefreshManaAfterHeroPower:
    amount: int = 2

    def execute(self, game: Any, context: RuleContext) -> None:
        restored = min(
            self.amount, max(0, context.player.max_mana - context.player.mana)
        )
        context.player.mana += restored
        game._event(
            "refresh_mana_after_hero_power", player=context.player.index,
            entity=context.card.entity_id, amount=restored,
        )


@dataclass(frozen=True)
class BlobOfTarDeathrattle:
    def execute(self, game: Any, context: RuleContext) -> None:
        Summon("TLC_468t1").execute(game, context)
        Summon("TLC_468t2").execute(game, context)


@dataclass(frozen=True)
class HoundsOfFurySpell:
    """Summon the two printed Demon tokens then force their attacks."""

    def execute(self, game: Any, context: RuleContext) -> None:
        player = context.player
        hounds = []
        for card_id in ("TIME_443t", "TIME_443t2"):
            if len(player.board) + len(player.locations) >= 7:
                break
            hound = game._entity(card_id, created_by=context.card.card_id)
            hound.summoned_turn = game.turn
            game._summon(player, hound)
            hounds.append(hound)
        if any(card.definition.card_type == "MINION" for card in player.deck):
            return
        for hound in hounds:
            if hound not in player.board or hound.health <= 0:
                continue
            candidates = game._enemy_characters(player.index)
            if not candidates:
                break

            def health_of(candidate: tuple[int, int | None]) -> int:
                owner, entity = candidate
                return (
                    game.players[owner].health
                    if entity is None
                    else game._find_minion(owner, entity).health
                )

            lowest = min(health_of(candidate) for candidate in candidates)
            targets = [
                candidate for candidate in candidates
                if health_of(candidate) == lowest
            ]
            target_owner, target_entity = game.rng.choice(targets)
            if target_entity is None:
                # A forced minion attack on a hero has no return damage.
                hound.attacks_this_turn += 1
                game._deal_to_target(
                    player.index, (target_owner, None), hound.attack, source=hound
                )
            else:
                game._forced_minion_attack(
                    player.index, hound, target_owner,
                    game._find_minion(target_owner, target_entity),
                )
            game._event(
                "hounds_of_fury_attack", player=player.index,
                source=context.card.card_id, hound=hound.entity_id,
                target_player=target_owner, target_entity=target_entity,
            )


@dataclass(frozen=True)
class GainSourceStats:
    attack: int
    health: int

    def execute(self, game: Any, context: RuleContext) -> None:
        context.card.attack_delta += self.attack
        context.card.health_delta += self.health
        game._event(
            "source_stats_gain", player=context.player.index,
            entity=context.card.entity_id, attack=self.attack, health=self.health,
        )


# ---- Standard tranche 50B -------------------------------------------------
# These effects are intentionally small and composable.  They describe the
# printed card behavior while delegating targeting, damage, draw, death and
# hand-cap semantics to the simulator's existing primitives.


@dataclass(frozen=True)
class DreamwardenBattlecry:
    def execute(self, game: Any, context: RuleContext) -> None:
        game._draw_matching(
            context.player, lambda held: not held.started_in_deck
        )
        context.card.attack_delta += 2
        context.card.health_delta += 2


@dataclass(frozen=True)
class SavageStrikerBattlecry:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_entity is None:
            raise ValueError("enemy minion target is required")
        target = next(
            (
                minion for minion in game.players[context.action.target_player].board
                if minion.entity_id == context.action.target_entity
            ),
            None,
        )
        # A copied/doubled Battlecry keeps the original target.  If its first
        # resolution killed that minion, subsequent resolutions fizzle rather
        # than dereferencing an entity that has left the board.
        if target is None:
            game._event("battlecry_target_absent", player=context.player.index,
                        source=context.card.card_id,
                        target=context.action.target_entity)
            return
        amount = max(0, context.player.attack)
        game._damage_minion(
            context.action.target_player, target, amount, context.card
        )
        game._resolve_deaths()


@dataclass(frozen=True)
class BugsquasherBattlecry:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_entity is None:
            raise ValueError("enemy minion target is required")
        target = next(
            (
                minion for minion in game.players[context.action.target_player].board
                if minion.entity_id == context.action.target_entity
            ),
            None,
        )
        if target is None:
            game._event("battlecry_target_absent", player=context.player.index,
                        source=context.card.card_id,
                        target=context.action.target_entity)
            return
        if not target.definition.races and not target.definition.race:
            raise ValueError("Bugsquasher requires a minion with a type")
        game._damage_minion(
            context.action.target_player, target,
            game._spell_effect_amount(context.player, context.card, 6),
            context.card,
        )
        game._resolve_deaths()


@dataclass(frozen=True)
class AshleafPixieBattlecry:
    def execute(self, game: Any, context: RuleContext) -> None:
        if any(held.definition.card_type == "SPELL" and held.cost >= 5
               for held in context.player.hand):
            context.card.divine_shield = True
            context.card.divine_shield_hits = max(1, context.card.divine_shield_hits)
            context.card.lifesteal = True


@dataclass(frozen=True)
class DestroyNonPaladinMinions:
    def execute(self, game: Any, context: RuleContext) -> None:
        for owner in game.players:
            for minion in list(owner.board):
                if minion.definition.card_class != "PALADIN" and minion.dormant_turns == 0:
                    minion.damage = minion.max_health
        game._resolve_deaths()


@dataclass(frozen=True)
class ManifestedTimewaysBattlecry:
    def execute(self, game: Any, context: RuleContext) -> None:
        has_aura = any(
            not minion.silenced and minion.dormant_turns == 0
            and ("AURA" in minion.definition.mechanics
                 or minion.aura_attack_bonus or minion.aura_health_bonus)
            for minion in context.player.board
        )
        if has_aura:
            DamageAllEnemies(3).execute(game, context)


@dataclass(frozen=True)
class SpiritKaldoreiBattlecry:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.player.hero_power_used:
            context.card.attack_delta += 3
            context.card.health_delta += 3


@dataclass(frozen=True)
class CleansingLightspawnBattlecry:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_entity is None:
            raise ValueError("enemy minion target is required")
        target = game._find_minion(
            context.action.target_player, context.action.target_entity
        )
        game._damage_minion(
            context.action.target_player, target,
            game._spell_effect_amount(context.player, context.card, context.card.max_health),
            context.card,
        )
        game._resolve_deaths()


@dataclass(frozen=True)
class AmberPriestessBattlecry:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("character target is required")
        amount = context.card.max_health
        if context.action.target_entity is None:
            target = game.players[context.action.target_player]
            game._apply_heal(target, target, amount, source=context.card)
        else:
            owner = game.players[context.action.target_player]
            target = game._find_minion(owner.index, context.action.target_entity)
            game._apply_heal(owner, target, amount, source=context.card)


@dataclass(frozen=True)
class ArcaneBarrageEffect:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("enemy target is required")
        primary = (context.action.target_player, context.action.target_entity)
        game._deal_to_target(
            context.player.index, primary,
            game._spell_effect_amount(context.player, context.card, 3),
            source=context.card,
        )
        others = [candidate for candidate in game._random_enemy_characters(context.player.index)
                  if candidate != primary]
        if others:
            for _ in range(2):
                game._deal_to_target(
                    context.player.index, game.rng.choice(others),
                    game._spell_effect_amount(context.player, context.card, 2),
                    source=context.card,
                )
        game._resolve_deaths()


@dataclass(frozen=True)
class SynchronizedSparkEffect:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_entity is None:
            raise ValueError("enemy minion target is required")
        target = game._find_minion(
            context.action.target_player, context.action.target_entity
        )
        game._damage_minion(
            context.action.target_player, target,
            game._spell_effect_amount(context.player, context.card, 3),
            context.card,
        )
        killed = target.health <= 0
        game._resolve_deaths()
        if killed:
            candidates = [minion for minion in context.player.board if minion.health > 0]
            if candidates:
                chosen = game.rng.choice(candidates)
                chosen.attack_delta += 3
                chosen.health_delta += 3


@dataclass(frozen=True)
class PreciseShotEffect:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("enemy target is required")
        try:
            position = next(
                index for index, held in enumerate(context.player.hand)
                if held.entity_id == context.card.entity_id
            )
        except StopIteration:
            position = -1
        exactly_center = len(context.player.hand) % 2 == 1 and position == len(context.player.hand) // 2
        amount = 5 if exactly_center else 3
        game._deal_to_target(
            context.player.index,
            (context.action.target_player, context.action.target_entity),
            game._spell_effect_amount(context.player, context.card, amount),
            source=context.card,
        )
        game._resolve_deaths()


@dataclass(frozen=True)
class StarsurgeEffect:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_entity is None:
            raise ValueError("minion target is required")
        target = game._find_minion(
            context.action.target_player, context.action.target_entity
        )
        amount = 1 + max(0, context.player.friendly_minions_died_this_game)
        game._damage_minion(
            context.action.target_player, target,
            game._spell_effect_amount(context.player, context.card, amount),
            context.card,
        )
        game._resolve_deaths()


@dataclass(frozen=True)
class StellarBalanceEffect:
    def execute(self, game: Any, context: RuleContext) -> None:
        for card_id in ("CS2_008", "EX1_173"):
            generated = game._entity(card_id, created_by=context.card.card_id)
            generated.spell_damage_bonus += 1
            game._add_generated(context.player, generated)


@dataclass(frozen=True)
class BitterEndEffect:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_entity is None:
            raise ValueError("minion target is required")
        owner = game.players[context.action.target_player]
        target = game._find_minion(owner.index, context.action.target_entity)
        index = owner.board.index(target)
        affected = owner.board[max(0, index - 1): index + 2]
        for minion in affected:
            minion.frozen_turn = game.turn
        for minion in list(affected):
            if minion.damage > 0:
                minion.damage = minion.max_health
        game._resolve_deaths()


@dataclass(frozen=True)
class BattlefieldBlasterBattlecry:
    def execute(self, game: Any, context: RuleContext) -> None:
        spells = [held for held in context.player.hand
                  if held.definition.card_type == "SPELL"]
        if spells:
            game.rng.choice(spells).spell_damage_bonus += 1


@dataclass(frozen=True)
class VeteranWarmedicAfterHoly:
    def execute(self, game: Any, context: RuleContext) -> None:
        spell = context.payload.get("spell")
        if spell is None or spell.definition.spell_school != "HOLY":
            return
        if len(context.player.board) + len(context.player.locations) >= 7:
            return
        medic = game._entity("BAR_878t", created_by=context.card.card_id)
        medic.lifesteal = True
        medic.summoned_turn = game.turn
        game._summon(context.player, medic)


@dataclass(frozen=True)
class DefiledSpearAfterHeroAttack:
    def execute(self, game: Any, context: RuleContext) -> None:
        attacked = context.payload.get("attacked")
        candidates = [target for target in game._random_enemy_characters(context.player.index)
                      if target != attacked]
        if not candidates:
            return
        amount = max(0, int(context.payload.get("hero_attack") or context.player.attack))
        game._deal_to_target(context.player.index, game.rng.choice(candidates), amount, context.card)
        game._resolve_deaths()


@dataclass(frozen=True)
class FelfireBlazeAfterFel:
    def execute(self, game: Any, context: RuleContext) -> None:
        spell = context.payload.get("spell")
        if spell is None or spell.definition.spell_school != "FEL":
            return
        if context.card in context.player.board:
            context.card.damage = context.card.max_health
        DamageAllEnemies(2).execute(game, context)
        game._resolve_deaths()


@dataclass(frozen=True)
class EbonscaleScoutBattlecry:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_entity is None:
            raise ValueError("enemy minion target is required")
        target = game._find_minion(context.action.target_player, context.action.target_entity)
        game._damage_minion(
            context.action.target_player, target,
            game._spell_effect_amount(context.player, context.card, context.card.attack),
            context.card,
        )
        game._resolve_deaths()


@dataclass(frozen=True)
class SpiritBondEffect:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_entity is None:
            raise ValueError("minion target is required")
        target = game._find_minion(context.action.target_player, context.action.target_entity)
        game._damage_minion(
            context.action.target_player, target,
            game._spell_effect_amount(context.player, context.card, 3),
            context.card,
        )
        killed = target.health <= 0
        game._resolve_deaths()
        if killed and "DRG_217t" in game.card_defs:
            Summon("DRG_217t").execute(game, context)


@dataclass(frozen=True)
class WastelandVanguardEffect:
    def execute(self, game: Any, context: RuleContext) -> None:
        enemy = game.players[1 - context.player.index]
        before = {m.entity_id for m in enemy.board}
        for _ in range(3):
            targets = game._random_enemy_characters(context.player.index)
            if not targets:
                break
            game._deal_to_target(context.player.index, game.rng.choice(targets), 1, context.card)
        game._resolve_deaths()
        killed = len(before - {m.entity_id for m in enemy.board})
        if killed:
            for _ in range(3):
                targets = game._random_enemy_characters(context.player.index)
                if not targets:
                    break
                game._deal_to_target(context.player.index, game.rng.choice(targets), 1, context.card)
            game._resolve_deaths()


@dataclass(frozen=True)
class AfterSummonElementalDamage:
    def execute(self, game: Any, context: RuleContext) -> None:
        summoned = context.payload.get("summoned")
        if summoned is None or not summoned.has_race("ELEMENTAL"):
            return
        targets = game._random_enemy_characters(context.player.index)
        if targets:
            game._deal_to_target(context.player.index, game.rng.choice(targets), 3, context.card)
            game._resolve_deaths()


@dataclass(frozen=True)
class WillfulWatcherDeathrattle:
    def execute(self, game: Any, context: RuleContext) -> None:
        destroyed = []
        for _ in range(min(3, len(context.player.deck))):
            card = context.player.deck.pop()
            destroyed.append(card.card_id)
        game._event("destroy_top_deck", player=context.player.index,
                    source=context.card.card_id, cards=destroyed)


@dataclass(frozen=True)
class RavenousDevilsaurBattlecry:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_entity is None:
            raise ValueError("minion target is required")
        target = game._find_minion(context.action.target_player, context.action.target_entity)
        attack, health = target.attack, target.max_health
        target.damage = target.max_health
        game._resolve_deaths()
        if game._kindred_active(context.player, context.card):
            context.card.attack_delta += attack
            context.card.health_delta += health


@dataclass(frozen=True)
class TwistedWebweaverAfterSummon:
    def execute(self, game: Any, context: RuleContext) -> None:
        summoned = context.payload.get("summoned")
        if summoned is None or summoned.entity_id == context.card.entity_id:
            return
        if context.player.played_card_counts.get(summoned.card_id, 0) > 1:
            game._draw(context.player)


@dataclass(frozen=True)
class BlackpawsWhipDeathrattle:
    def execute(self, game: Any, context: RuleContext) -> None:
        Draw().execute(game, context)


@dataclass(frozen=True)
class MaloriakAfterDiscard:
    def execute(self, game: Any, context: RuleContext) -> None:
        discarded = context.payload.get("discarded")
        if discarded is None or discarded.definition.card_type != "MINION":
            return
        if len(context.player.board) + len(context.player.locations) >= 7:
            return
        copy_card = discarded.clone(game.next_entity_id)
        game.next_entity_id += 1
        copy_card.created_by = context.card.card_id
        copy_card.damage = 0
        copy_card.summoned_turn = game.turn
        game._summon(context.player, copy_card)


@dataclass(frozen=True)
class FragmentOfNothingAfterSpell:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.payload.get("target_entity") is not None:
            game._draw(context.player)


@dataclass(frozen=True)
class StoryOfLakkariSpell:
    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.lakkari_turns = 3
        game._event("story_of_lakkari_started", player=context.player.index, turns=3)


@dataclass(frozen=True)
class InjuredAttendantBattlecry:
    def execute(self, game: Any, context: RuleContext) -> None:
        DamageSelf(4).execute(game, context)


@dataclass(frozen=True)
class MotherHandDiscount:
    """Discount a selected hand card and its neighbors.

    M.O.T.H.E.R. applies 5 points to the selected card, then 4/3/2/1 to
    cards at increasing distance on both sides in the current hand order.
    The played M.O.T.H.E.R. is already on the board when this hook runs, so
    the entity IDs in the action refer only to the remaining hand.
    """

    center_discount: int = 5

    def execute(self, game: Any, context: RuleContext) -> None:
        action = context.action
        hand = context.player.hand
        if action is None or action.target_entity is None:
            # M.O.T.H.E.R. can also be played by an effect such as a
            # top-deck replay.  Those effects cannot open an interactive
            # target choice; resolve the Battlecry against a random eligible
            # minion, and correctly fizzle when the hand has none.  The
            # ordinary PLAY path still supplies an explicit target through
            # legal_actions.
            candidates = [card for card in hand
                          if card.definition.card_type == "MINION"]
            if not candidates:
                game._event("mother_no_hand_minion", player=context.player.index,
                            source=context.card.card_id)
                return
            target_entity = game.rng.choice(candidates).entity_id
        else:
            target_entity = action.target_entity
        try:
            center = next(
                index for index, card in enumerate(hand)
                if card.entity_id == target_entity
            )
        except StopIteration as exc:
            raise ValueError("M.O.T.H.E.R. target is not in hand") from exc

        affected: list[dict[str, int]] = []
        for distance in range(self.center_discount):
            discount = self.center_discount - distance
            for index in (center - distance if distance else center,
                          center + distance if distance else None):
                if index is None or not 0 <= index < len(hand):
                    continue
                target = hand[index]
                target.cost_delta -= discount
                affected.append({
                    "entity": target.entity_id,
                    "card": target.card_id,
                    "discount": discount,
                    "distance": distance,
                })
        game._event(
            "mother_hand_discount", player=context.player.index,
            source=context.card.entity_id, target=action.target_entity,
            affected=affected,
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
        # Blackwing Experiment's generated Dragon Breath is a targeted spell.
        # Registering its target contract is required when a spell-copy effect
        # repeats it; otherwise the repeat-retarget helper would manufacture a
        # no-target PLAY action and resolution would receive player=None.
        CardRule(
            "CATA_464t", {},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332"),
            TargetSpec(TargetKind.ANY_CHARACTER),
        ),
        CardRule(
            "TLC_813", {},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332"),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "TIME_EVENT_997", {Hook.SPELL: (ReopenLocationWithRandomMinionDeathrattle(),)},
            RuleSource("official_text", "HearthstoneJSON 251332"),
            TargetSpec(TargetKind.FRIENDLY_LOCATION),
        ),
        CardRule(
            "BE_036", {Hook.BATTLECRY: (MotherHandDiscount(),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON latest",
                       verification=("test_mother_left_right_hand_discount",)),
            TargetSpec(TargetKind.FRIENDLY_HAND_CARD),
        ),
        CardRule(
            "CATA_133", {Hook.END_TURN: (FlitterwingEndTurn(),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332",
                       verification=("test_elusive_flitterwing_end_turn_buff",)),
        ),
        CardRule(
            "JAIL_997", {Hook.SPELL: (SetDormantActionTarget(2, True),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332"),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "WW_325", {Hook.SPELL: (DamageActionTargetLifesteal(4),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332",
                       verification=("test_dehydrate_quickdraw_damage_and_cost",)),
            TargetSpec(TargetKind.ENEMY_MINION), cost_modifier=CostIfQuickdraw(1),
        ),
        CardRule(
            "WW_360", {Hook.BATTLECRY: (QuickdrawCopyBattlecry(),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332",
                       verification=("test_azerite_chain_gang_quickdraw_copy",)),
        ),
        CardRule(
            "WW_434", {Hook.BATTLECRY: (IfQuickdraw((DamageRandomEnemyCharacters(6, 1),)),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332",
                       verification=("test_sunspot_dragon_quickdraw",)),
        ),
        CardRule(
            "WW_808", {Hook.BATTLECRY: (IfQuickdraw((GrantTemporaryImmune(),)),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332",
                       verification=("test_silver_serpent_quickdraw_immune",)),
        ),
        CardRule(
            "WW_823", {Hook.SPELL: (HealHero(7), IfQuickdraw((RefreshMana(2),)))},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332",
                       verification=("test_rehydrate_quickdraw_refresh",)),
        ),
        CardRule(
            "DED_506", {Hook.SPELL: (Draw(3),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332",
                       verification=("test_need_for_greed_quickdraw_cost",)),
            cost_modifier=CostIfQuickdraw(3),
        ),
        CardRule(
            "TTN_841", {Hook.SPELL: (GainHeroAttack(4),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332",
                       verification=("test_momentum_scales_with_draws",)),
        ),
        CardRule(
            "TOY_519", {Hook.SPELL: (SummonRandomMinionWithCost(4, count=2),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332",
                       verification=("test_everything_must_go_scales_with_draws",)),
        ),
        CardRule(
            "WW_403", {Hook.SPELL: (DamageHero(3),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332",
                       verification=("test_pocket_sand_quickdraw",)),
        ),
        CardRule(
            "CATA_185", {Hook.DEATHRATTLE: (FacelessReplicatorDeathrattle(),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332",
                       verification=("test_faceless_replicator_transforms_lethal_killer",)),
        ),
        CardRule(
            "CATA_206", {Hook.START_TURN: (TwistedMonstrosityRotate(),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332",
                       verification=("test_twisted_monstrosity_rotates_hand_bonus",)),
        ),
        CardRule(
            "EDR_462", {Hook.END_TURN: (AddRandomDragon(),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332",
                       verification=("test_selenic_drake_adds_random_dragon",)),
        ),
        CardRule(
            "TIME_013", {Hook.AFTER_PLAY: (DiscoverNatureSpell(),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332",
                       verification=("test_farseer_wo_discovers_after_spell",)),
        ),
        CardRule(
            "TIME_059", {Hook.BATTLECRY: (LivingParadoxBattlecry(),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332",
                       verification=("test_living_paradox_summons_two_elusive_tokens",)),
        ),
        CardRule(
            "TIME_605", {Hook.BATTLECRY: (EpochStalkerBattlecry(),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332",
                       verification=("test_epoch_stalker_summons_copy",)),
        ),
        CardRule(
            "RLK_048", {Hook.SPELL: (BuffFriendlyMinionsAndElusive(1),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332",
                       verification=("test_anti_magic_shell_grants_elusive",)),
        ),
        CardRule(
            "TLC_246", {Hook.BATTLECRY: (OfferEffectChoice((
                ("stealth", (GrantKeyword("stealth"),)),
                ("elusive", (GrantKeyword("elusive"),)),
                ("windfury", (GrantKeyword("windfury"),)),
            )),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332",
                       verification=("test_ancient_pterrordax_keyword_choice",)),
        ),
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
            "JAIL_877", {Hook.LOCATION: (SummonLocationRat(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ()),
        ),
        CardRule(
            "JAIL_887", {Hook.LOCATION: (StartZuramatPrison(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ()),
        ),
        CardRule(
            "CATA_477", {Hook.LOCATION: (BuffFriendlyHandMinion(2, 2),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ()),
            TargetSpec(TargetKind.FRIENDLY_HAND_MINION),
        ),
        CardRule(
            "CATA_301", {Hook.LOCATION: (ArmRubySanctum(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ()),
        ),
        CardRule(
            "CATA_161", {Hook.BATTLECRY: (BuffFriendlyMinionOrHandAttack(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ()),
            TargetSpec(TargetKind.FRIENDLY_MINION_OR_HAND),
        ),
        CardRule(
            "CATA_527", {Hook.LOCATION: (DamageRandomEnemyCharacters(1, 1),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ()),
        ),
        CardRule(
            "EDR_233", {Hook.SPELL: (OfferEffectChoice((
                ("summon_wolves", (Summon("DRG_217t", count=3),)),
                ("summon_falcons", (Summon("EDR_233t2", count=2),)),
            )),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ()),
        ),
        CardRule(
            "EDR_257", {Hook.BATTLECRY: (OfferEffectChoice((
                ("attack_divine_shield", (BuffSelfAttackShield(),)),
                ("health_lifesteal", (BuffSelfHealthLifesteal(),)),
            )),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ()),
        ),
        CardRule(
            "EDR_263", {Hook.SPELL: (OfferEffectChoice((
                ("damage_enemy_hero", (DamageEnemyHero(4),)),
                ("summon_rush_wolves", (SummonCustomRushWolf(2),)),
            )),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ()),
        ),
        CardRule(
            "CATA_527t2", {Hook.AFTER_PLAY: (NespirahUnshackledAfterFel(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ()),
        ),
        CardRule(
            "EDR_520", {Hook.LOCATION: (SpendManaCastRandomSpell(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ()),
        ),
        CardRule(
            "EDR_454", {Hook.LOCATION: (SummonEggCopyingTargetDragon("EDR_454t"),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ()),
            TargetSpec(TargetKind.FRIENDLY_DRAGON),
        ),
        CardRule(
            "JAIL_987", {Hook.LOCATION: (AddRandomShamanMinionLocked(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ()),
        ),
        CardRule(
            "MEND_044", {Hook.LOCATION: (BuffLocationTargetAndSleep(2, 2),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ()),
            TargetSpec(TargetKind.FRIENDLY_WISP),
        ),
        CardRule(
            "TIME_044", {Hook.LOCATION: (BuffLocationTargetAndAdvance(2, 1, "TIME_044t1"),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ()),
            TargetSpec(TargetKind.FRIENDLY_MINION),
        ),
        CardRule(
            "TIME_044t1", {Hook.LOCATION: (
                BuffLocationTargetAndAdvance(2, 1, "TIME_044t2", deathrattle_damage_enemy_hero=2),
            )},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_time_location_progression",)),
            TargetSpec(TargetKind.FRIENDLY_MINION),
        ),
        CardRule(
            "TIME_044t2", {Hook.LOCATION: (
                BuffLocationTargetAndAdvance(2, 1, divine_shield=True, deathrattle_damage_enemy_hero=2),
            )},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_time_location_progression",)),
            TargetSpec(TargetKind.FRIENDLY_MINION),
        ),
        CardRule(
            "TIME_436", {Hook.LOCATION: (SummonRandomDragonMinCostAndAdvance(5, "TIME_436t1"),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ()),
        ),
        CardRule(
            "TIME_436t1", {Hook.LOCATION: (OfferDragonSummonLocation(5, "TIME_436t2"),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_time_location_progression",)),
        ),
        CardRule(
            "TIME_436t2", {Hook.LOCATION: (OfferDragonSummonLocation(5, add_copy=True),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_time_location_progression",)),
        ),
        CardRule(
            "TIME_446", {Hook.LOCATION: (OfferDemonDiscoverMinCost(5),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ()),
        ),
        CardRule(
            "TIME_810", {Hook.LOCATION: (DamageLocationEnemyMinionAndAdvance(5, "TIME_810t1"),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ()),
        ),
        CardRule(
            "TIME_810t1", {Hook.LOCATION: (DamageLocationEnemyMinionAndAdvance(5, "TIME_810t2", excess_to_hero=True),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_time_location_progression",)),
        ),
        CardRule(
            "TIME_810t2", {Hook.LOCATION: (DamageLocationEnemyMinionAndAdvance(5, excess_to_hero=True, lowest_health=True),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_time_location_progression",)),
        ),
        CardRule(
            "TLC_449", {Hook.LOCATION: (DiscoverTemporaryOneCostMinion(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ()),
        ),
        CardRule(
            "WW_365", {Hook.SPELL: (SetActionTargetStats(1, 1),
                                      IfQuickdraw((DamageActionTarget(1),)))},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332"),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "WW_363", {Hook.BATTLECRY: (IfQuickdraw((AddToHand("JAIL_COIN1"),)),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332"),
        ),
        CardRule(
            "WW_411", {Hook.SPELL: (DiscoverQuickdrawOtherClass(),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332"),
        ),
        CardRule(
            "CORE_EX1_189", {Hook.BATTLECRY: (AddRandomLegendaryMinion(),)},
            RuleSource(
                "official_text_and_engine_pattern", "HearthstoneJSON 251332",
                verification=("test_brightwing_adds_random_legendary",),
            ),
        ),
        CardRule(
            "FIR_959", {Hook.BATTLECRY: (CastRandomFireSpellsMana(15),)},
            RuleSource(
                "official_text_and_engine_pattern", "HearthstoneJSON 251332",
                verification=("test_fyrakk_is_immune_to_fire_spell_damage_only",),
            ),
        ),
        CardRule(
            "CATA_723", {Hook.DEATHRATTLE: (SummonRandomMinionWithCost(4, count=2),)},
            RuleSource(
                "official_text_and_engine_pattern", "HearthstoneJSON 251332",
                verification=("test_drakeadon_mongrel_summons_random_four_cost",),
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
        CardRule(
            "JAIL_446hp", {Hook.HERO_POWER: (BuffActionTarget(3, 0),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332"),
            targeting=TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "JAIL_504", {Hook.BATTLECRY: (AyaCoinChoice(),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332"),
        ),
        CardRule(
            "JAIL_319", {Hook.SPELL: (OfferSpellDiscover(),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332"),
        ),
        CardRule(
            "JAIL_882", {Hook.DEATHRATTLE: (Draw(),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332"),
        ),
        CardRule(
            "JAIL_831", {Hook.BATTLECRY: (OfferContrabandBeastDiscover(),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332"),
        ),
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
        # Dark Gift option cards.  These are normally chosen inside a
        # Discover, but Power.log/replay inputs can expose their individual
        # entity IDs.  Keep the option rules explicit so both routes apply
        # the same instance-level Gift state.
        CardRule("EDR_100t", {Hook.SPELL: (ApplyDarkGiftToActionTarget("waking_terror"),)},
                 RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_dark_gift_option_entities",)), TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("EDR_100t1", {Hook.SPELL: (ApplyDarkGiftToActionTarget("well_rested"),)},
                 RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_dark_gift_option_entities",)), TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("EDR_100t2", {Hook.SPELL: (ApplyDarkGiftToActionTarget("short_claws"),)},
                 RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_dark_gift_option_entities",)), TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("EDR_100t3", {Hook.SPELL: (ApplyDarkGiftToActionTarget("bundled_up"),)},
                 RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_dark_gift_option_entities",)), TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("EDR_100t4", {Hook.SPELL: (ApplyDarkGiftToActionTarget("inner_demons"),)},
                 RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_dark_gift_option_entities",)), TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("EDR_100t5", {Hook.SPELL: (ApplyDarkGiftToActionTarget("living_nightmare"),)},
                 RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_dark_gift_option_entities",)), TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("EDR_100t6", {Hook.SPELL: (ApplyDarkGiftToActionTarget("sleepwalker"),)},
                 RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_dark_gift_option_entities",)), TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("EDR_100t7", {Hook.SPELL: (ApplyDarkGiftToActionTarget("rude_awakening"),)},
                 RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_dark_gift_option_entities",)), TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("EDR_100t8", {Hook.SPELL: (ApplyDarkGiftToActionTarget("sweet_dreams"),)},
                 RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_dark_gift_option_entities",)), TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("EDR_100t9", {Hook.SPELL: (ApplyDarkGiftToActionTarget("persisting_horror"),)},
                 RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_dark_gift_option_entities",)), TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("EDR_100t10", {Hook.SPELL: (ApplyDarkGiftToActionTarget("nightmare_scales"),)},
                 RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_dark_gift_option_entities",)), TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("EDR_100t13", {Hook.SPELL: (ApplyDarkGiftToActionTarget("harpys_talons"),)},
                 RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_dark_gift_option_entities",)), TargetSpec(TargetKind.FRIENDLY_MINION)),
        # Blinding Carapace: each option is one pair from Divine Shield,
        # Rush, Lifesteal, Reborn, Taunt and Poisonous.
        CardRule("EDR_101t", {Hook.SPELL: (ApplyKeywordPackageToActionTarget(("DIVINE_SHIELD", "RUSH")),)}, RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_blinding_carapace_options",)), TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("EDR_101t1", {Hook.SPELL: (ApplyKeywordPackageToActionTarget(("DIVINE_SHIELD", "LIFESTEAL")),)}, RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_blinding_carapace_options",)), TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("EDR_101t2", {Hook.SPELL: (ApplyKeywordPackageToActionTarget(("DIVINE_SHIELD", "REBORN")),)}, RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_blinding_carapace_options",)), TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("EDR_101t3", {Hook.SPELL: (ApplyKeywordPackageToActionTarget(("DIVINE_SHIELD", "TAUNT")),)}, RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_blinding_carapace_options",)), TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("EDR_101t4", {Hook.SPELL: (ApplyKeywordPackageToActionTarget(("DIVINE_SHIELD", "POISONOUS")),)}, RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_blinding_carapace_options",)), TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("EDR_101t5", {Hook.SPELL: (ApplyKeywordPackageToActionTarget(("RUSH", "LIFESTEAL")),)}, RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_blinding_carapace_options",)), TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("EDR_101t6", {Hook.SPELL: (ApplyKeywordPackageToActionTarget(("RUSH", "REBORN")),)}, RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_blinding_carapace_options",)), TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("EDR_101t7", {Hook.SPELL: (ApplyKeywordPackageToActionTarget(("RUSH", "TAUNT")),)}, RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_blinding_carapace_options",)), TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("EDR_101t8", {Hook.SPELL: (ApplyKeywordPackageToActionTarget(("RUSH", "POISONOUS")),)}, RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_blinding_carapace_options",)), TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("EDR_101t9", {Hook.SPELL: (ApplyKeywordPackageToActionTarget(("LIFESTEAL", "REBORN")),)}, RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_blinding_carapace_options",)), TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("EDR_101t10", {Hook.SPELL: (ApplyKeywordPackageToActionTarget(("LIFESTEAL", "TAUNT")),)}, RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_blinding_carapace_options",)), TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("EDR_101t11", {Hook.SPELL: (ApplyKeywordPackageToActionTarget(("LIFESTEAL", "POISONOUS")),)}, RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_blinding_carapace_options",)), TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("EDR_101t12", {Hook.SPELL: (ApplyKeywordPackageToActionTarget(("REBORN", "TAUNT")),)}, RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_blinding_carapace_options",)), TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("EDR_101t13", {Hook.SPELL: (ApplyKeywordPackageToActionTarget(("REBORN", "POISONOUS")),)}, RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_blinding_carapace_options",)), TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("EDR_101t14", {Hook.SPELL: (ApplyKeywordPackageToActionTarget(("TAUNT", "POISONOUS")),)}, RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_blinding_carapace_options",)), TargetSpec(TargetKind.FRIENDLY_MINION)),
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
                OfferMinionDarkGiftDiscover(race="DRAGON", past=True),
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
            targeting=TargetSpec(TargetKind.FRIENDLY_BEAST),
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
            "CATA_481", {Hook.BATTLECRY: (IsorathDevour(),),
                         Hook.DEATHRATTLE: (IsorathReturn(),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332"),
        ),
        CardRule(
            "EDR_841", {Hook.BATTLECRY: (SummonRandomDreadseed(),),
                         Hook.DEATHRATTLE: (SummonRandomDreadseed(),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332"),
        ),
        CardRule(
            "EDR_820", {Hook.SPELL: (OfferEffectChoice((
                ("dreadseeds", (SummonRandomDreadseed(count=2),)),
                ("damage_all", (DamageAllMinions(2),)),
            )),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332"),
        ),
        CardRule(
            "TIME_058", {Hook.DEATHRATTLE: (SummonRandomDormantCost(2),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332"),
        ),
        CardRule(
            "TIME_442", {Hook.BATTLECRY: (TimewayImprison(),),
                          Hook.DEATHRATTLE: (TimewayAwaken(),)},
            RuleSource("official_text_and_engine_pattern", "HearthstoneJSON 251332"),
            TargetSpec(TargetKind.ENEMY_MINION),
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
            "MEND_506", {Hook.BATTLECRY: (IncreaseLeylinePower(),)},
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
            "JAIL_386", {Hook.SPELL: (
                GainArmor(2),
                AddToDeck(
                    "JAIL_386t", count=5, shuffle=True,
                    attributes=(("casts_when_drawn_armor", 2),),
                ),
            )},
            RuleSource(
                "official_text_and_engine_pattern", "HearthstoneJSON 251332",
                verification=("test_scramble_for_gear_gains_armor_and_shuffles_gear",),
            ),
        ),
        CardRule(
            "JAIL_379", {Hook.BATTLECRY: (
                RevealSpellThenSplitEnemyMinions(threshold=5, amount=5),
            )},
            RuleSource(
                "official_text_and_engine_pattern", "HearthstoneJSON 251332",
                verification=("test_spire_security_reveals_and_splits_damage",),
            ),
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
            {Hook.SPELL: (DamageLowestHealthEnemyRepeated(2, 3), Overload(1))},
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
            {Hook.SPELL: (SetHeroPowerDirect("TLC_632t"),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_story_of_sulfuras_last_two_uses_then_restores_hero_power",),
            ),
        ),
        CardRule(
            "TLC_632t",
            {Hook.HERO_POWER: (DamageRandomEnemyCharacters(8, 1), SetHeroPowerDirect("TLC_632t2"))},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_story_of_sulfuras_last_two_uses_then_restores_hero_power",),
            ),
        ),
        CardRule(
            "TLC_632t2",
            {Hook.HERO_POWER: (DamageRandomEnemyCharacters(8, 1), SetHeroPowerDirect(None))},
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
            "JAIL_851", {},
            RuleSource(
                "local_spec", local,
                verification=(
                    "test_holmes_investigation_is_an_explicit_hand_guess",
                ),
            ),
        ),
        CardRule(
            "TLC_100", {},
            RuleSource(
                "local_spec", local,
                verification=("test_elise_navigator_location_choices",),
            ),
        ),
        CardRule(
            "MEND_046", {},
            RuleSource(
                "local_spec", local,
                verification=("test_bashana_carves_nature_spells",),
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
            "JAIL_035", {Hook.BATTLECRY: (
                SummonIfDeckHasNoNeutral("JAIL_035", count=2),
            )},
            RuleSource(
                "official_text_and_engine_pattern", "HearthstoneJSON 251332",
                verification=("test_vigilant_sentry_no_neutral_summons_two",),
            ),
        ),
        CardRule(
            "JAIL_328", {Hook.DEATHRATTLE: (
                AddRandomExecutableClassCard(
                    "PALADIN", require_no_neutral=True, cost_delta=-2,
                ),
            )},
            RuleSource(
                "official_text_and_engine_pattern", "HearthstoneJSON 251332",
                verification=("test_scarlet_bruiser_no_neutral_adds_discounted_paladin",),
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
            "CATA_582", {Hook.SPELL: (DamageAllOtherMinions(1), GainHeroAttack(3))},
            RuleSource("upstream_adapted", rosetta, "CATA_582", "AGPL-3.0", ("test_standard_searing_fissure",)),
        ),
        CardRule(
            "CATA_585", {Hook.SPELL: (DamageDamagedTargetWithExcessReturn(8),)},
            RuleSource("upstream_adapted", rosetta, "CATA_585", "AGPL-3.0", ("test_standard_torch_excess_return",)),
            # The spell text requires a minion that is already damaged.  Keep
            # the legality predicate aligned with the effect implementation;
            # otherwise ISMCTS can select an undamaged target and fail during
            # action replay.
            TargetSpec(TargetKind.DAMAGED_MINION),
        ),
        CardRule(
            "CATA_203", {Hook.SPELL: (DestroyLegendaryTarget(),)},
            RuleSource("upstream_adapted", rosetta, "CATA_203", "AGPL-3.0", ("test_standard_garona_last_stand",)),
            TargetSpec(TargetKind.ENEMY_MINION),
        ),
        CardRule(
            "CORE_EX1_005", {Hook.BATTLECRY: (DestroyHighAttackMinion(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_big_game_hunter_tradeable_battlecry",)),
            TargetSpec(TargetKind.ENEMY_MINION),
        ),
        CardRule(
            "CORE_REV_023", {Hook.BATTLECRY: (DestroyEnemyLocation(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_demolition_renovator_tradeable_battlecry",)),
            TargetSpec(TargetKind.ENEMY_LOCATION),
        ),
        CardRule(
            "CORE_SW_429", {Hook.SPELL: (BestInShell(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_best_in_shell_tradeable_spell",)),
        ),
        CardRule(
            "TLC_255", {Hook.BATTLECRY: (CrystalTenderBattlecry(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_crystal_tender_matches_mana",)),
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
            "CORE_BT_480", {Hook.BATTLECRY: (DrawIfOutcast(),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_crimson_sigil_runner_outcast_draw",),
            ),
        ),
        CardRule(
            "CATA_533", {Hook.SPELL: (FlashFloodOutcast(),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_flash_flood_outcast_repeats_edges",),
            ),
        ),
        CardRule(
            "DINO_136", {Hook.SPELL: (SummonOutcastImmuneRaptors(),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_horn_of_feasting_outcast_raptors",),
            ),
        ),
        CardRule(
            "END_005", {Hook.SPELL: (BygoneEchoesOutcast(),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_bygone_echoes_corpses_and_outcast",),
            ),
        ),
        CardRule(
            "JAIL_892", {Hook.SPELL: (CosmicManifestationsOutcast(),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_cosmic_manifestations_outcast",),
            ),
        ),
        CardRule(
            "TIME_021", {Hook.BATTLECRY: (HeroImmuneUntilNextTurnIfOutcast(),)},
            RuleSource(
                "official_text_and_engine_verified", "HearthstoneJSON 251332",
                verification=("test_doomsday_prepper_outcast_hero_immunity",),
            ),
        ),
        CardRule(
            "RLK_503", {Hook.BATTLECRY: (GainCorpses(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_body_bagger_gains_corpse",)),
        ),
        CardRule(
            "CORE_RLK_066", {Hook.BATTLECRY: (
                SpendCorpsesDiscoverRune("blood"),
            )},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_hematurge_spends_corpse",)),
        ),
        CardRule(
            "CORE_RLK_118", {Hook.SPELL: (
                SummonCorpseTokens("RLK_118t3", 2, spend=4,
                                   taunt=True, reborn_if_spent=True),
            )},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_tomb_guardians_corpse_upgrade",)),
        ),
        CardRule(
            "CORE_RLK_505", {Hook.BATTLECRY: (SpendCorpsesRandomDamage(5, 2),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_marrow_manipulator_spends_corpses",)),
        ),
        CardRule(
            "CORE_RLK_506", {Hook.BATTLECRY: (
                RaiseCorpseFootmen(6, "RLK_506t"),
            )},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_boneguard_commander_raises_corpses",)),
        ),
        CardRule(
            "CORE_RLK_712", {Hook.SPELL: (SpendCorpsesBuffHand(1, 1, 2, 1, 1),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_blood_tap_corpse_upgrade",)),
        ),
        CardRule(
            "CORE_WW_374", {Hook.SPELL: (SpendCorpsesRandomMinion(8),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_corpse_farm_cost_pool",)),
        ),
        CardRule(
            "RLK_060", {Hook.SPELL: (RaiseCorpseFootmen(5, "RLK_008t", rush=True),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_army_of_the_dead_raises_ghouls",)),
        ),
        CardRule(
            "RLK_707", {Hook.SPELL: (GraveStrength(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_grave_strength_corpse_upgrade",)),
        ),
        CardRule(
            "CATA_465", {Hook.SPELL: (ChowDown(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_chow_down_corpse_rush",)),
        ),
        CardRule(
            "CORE_RLK_745", {Hook.END_TURN: (MalignantHorrorEndTurn(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_malignant_horror_end_turn_copy",)),
        ),
        CardRule(
            "RLK_061", {Hook.END_TURN: (RaiseOneCorpseEndTurn(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_battlefield_necromancer_raises_footman",)),
        ),
        CardRule(
            "JAIL_451", {Hook.SPELL: (OfferFiveCostCorpseCopy(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_blood_clone_corpse_copy",)),
        ),
        CardRule(
            "TLC_434", {Hook.SPELL: (OfferUndeadDiscoverWithCorpseKeep(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_paleomancy_keeps_undead_options",)),
        ),
        CardRule(
            "EDR_813", {Hook.SPELL: (OfferEffectChoice((
                ("summon_ants", (Summon("EDR_813at", count=2),)),
                ("corpse_damage", (SpendCorpseDamageActionTarget(2, 4),)),
            )),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_morbid_swarm_choose_one",)),
            TargetSpec(TargetKind.ANY_MINION, optional=True),
        ),
        CardRule(
            "Core_LOE_115", {Hook.SPELL: (OfferEffectChoice((
                ("discover_minion", (OfferTypeDiscover("MINION"),)),
                ("discover_spell", (OfferTypeDiscover("SPELL"),)),
            )),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_raven_idol_choose_one_discover",)),
        ),
        CardRule(
            "EDR_872", {Hook.SPELL: (OfferEffectChoice((
                ("discover_mage_spell", (OfferClassSpellDiscover("MAGE"),)),
                ("discover_druid_spell", (OfferClassSpellDiscover("DRUID"),)),
            )),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_spark_of_life_choose_one_class_discover",)),
        ),
        CardRule(
            "EDR_843", {Hook.SPELL: (OfferEffectChoice((
                ("draw_spell", (DrawMatching(card_type="SPELL"),)),
                ("draw_minion", (DrawMatching(card_type="MINION"),)),
            )),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_reforestation_choose_one_draw_type",)),
        ),
        CardRule(
            "END_010", {Hook.BATTLECRY: (OfferEffectChoice((
                ("set_other_attack_one", (SetOtherMinionsStat("attack", 1),)),
                ("set_other_health_one", (SetOtherMinionsStat("health", 1),)),
            )),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_twilight_timereaver_choose_one_stats",)),
        ),
        CardRule(
            "END_010a", {Hook.SPELL: (SetOtherMinionsStat("attack", 1),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332; parent Choose One", ("test_time_auxiliary_entities",)),
        ),
        CardRule(
            "END_010b", {Hook.SPELL: (SetOtherMinionsStat("health", 1),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332; parent Choose One", ("test_time_auxiliary_entities",)),
        ),
        CardRule(
            "TIME_000ta", {},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332; Rewind keep branch", ("test_time_auxiliary_entities",)),
        ),
        CardRule(
            "TIME_000tb", {},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332; Rewind retry branch", ("test_time_auxiliary_entities",)),
        ),
        CardRule(
            "TIME_036t", {Hook.SPELL: (IncreaseRightmostOpponentCardCost(2),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332; Royal Informant choice", ("test_time_auxiliary_entities",)),
        ),
        CardRule(
            "TIME_038t1", {Hook.BATTLECRY: (
                SummonRandomLegendaryMinion(), SummonRandomLegendaryMinion(),
            )},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332; Rewind x2", ("test_time_auxiliary_entities",)),
        ),
        CardRule(
            "TIME_038t2", {Hook.BATTLECRY: (
                SummonRandomLegendaryMinion(), SummonRandomLegendaryMinion(),
            )},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332; Rewind x1", ("test_time_auxiliary_entities",)),
        ),
        CardRule(
            "TIME_038t3", {Hook.BATTLECRY: (
                SummonRandomLegendaryMinion(), SummonRandomLegendaryMinion(),
            )},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332; no Rewind", ("test_time_auxiliary_entities",)),
        ),
        CardRule(
            "TIME_618t", {Hook.SPELL: (ArmCorpseRebirth(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332; Husk hero Deathrattle", ("test_time_auxiliary_entities",)),
        ),
        CardRule(
            "CORE_AT_052", {Hook.AFTER_PLAY: (Overload(1),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_totem_golem_overload",)),
        ),
        CardRule(
            "CATA_569", {Hook.SPELL: (
                SummonRandomExecutableMinion(cost=3),
                SummonRandomExecutableMinion(cost=2),
                SummonRandomExecutableMinion(cost=1),
                Overload(1),
            )},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_ceremonial_clash_summons_costs_and_overload",)),
        ),
        CardRule(
            "END_028", {Hook.SPELL: (DestroyMinionsByAttackAtMost(4), Overload(2))},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_for_all_time_attack_filter_and_overload",)),
        ),
        CardRule(
            "CORE_EX1_250", {Hook.AFTER_PLAY: (Overload(2),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_earth_elemental_overload",)),
        ),
        CardRule(
            "CS3_007", {Hook.AFTER_PLAY: (Overload(1),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_novice_zapper_overload",)),
        ),
        CardRule(
            "JAIL_452", {},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332 + placement engine",
                       verification=("test_disguised_detective_overloads_receiving_side",)),
        ),
        CardRule(
            "TIME_014", {},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332 + rewind engine",
                       verification=("test_instant_multiverse_overload",)),
        ),
        CardRule(
            "CATA_898", {},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332 + continuous aura engine",
                       verification=("test_scaled_lancer_aura_adds_enemy_taunt",)),
        ),
        CardRule(
            "CATA_613", {},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332 + continuous aura engine",
                       verification=("test_survivalist_no_other_minions_immune",)),
        ),
        CardRule(
            "TLC_228", {},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332 + continuous aura engine",
                       verification=("test_bralma_elemental_damage_aura",)),
        ),
        # These are audit markers rather than duplicate play hooks.  Their
        # static effects are recalculated by Game._refresh_continuous so the
        # same implementation covers silence, death, dormancy and summon
        # ordering without adding one-off registry actions.
        CardRule("CORE_NEW1_027", {},
                 RuleSource("official_text_and_engine_verified", "continuous aura engine",
                            verification=("test_raid_leader_aura_buffs_other_minions_only",))),
        CardRule("CORE_CS2_122", {},
                 RuleSource("official_text_and_engine_verified", "continuous aura engine",
                            verification=("test_raid_leader_aura_buffs_other_minions_only",))),
        CardRule("CORE_CS2_222", {},
                 RuleSource("official_text_and_engine_verified", "continuous aura engine",
                            verification=("test_raid_leader_aura_buffs_other_minions_only",))),
        CardRule("CORE_EX1_507", {},
                 RuleSource("official_text_and_engine_verified", "continuous aura engine",
                            verification=("test_raid_leader_aura_buffs_other_minions_only",))),
        CardRule("CORE_EX1_162", {},
                 RuleSource("official_text_and_engine_verified", "continuous aura engine",
                            verification=("test_raid_leader_aura_buffs_other_minions_only",))),
        CardRule("JAIL_459", {},
                 RuleSource("official_text_and_engine_verified", "continuous aura engine",
                            verification=("test_arachnathid_aura_grants_poisonous",))),
        CardRule("EDR_258", {},
                 RuleSource("official_text_and_engine_verified", "continuous aura engine",
                            verification=("test_toreth_aura_expands_divine_shield",))),
        CardRule("CATA_153t", {},
                 RuleSource("official_text_and_engine_verified", "continuous aura engine",
                            verification=("test_herald_neighbor_attack_aura",))),
        CardRule("CATA_153t1", {},
                 RuleSource("official_text_and_engine_verified", "continuous aura engine",
                            verification=("test_herald_neighbor_attack_aura",))),
        CardRule("CATA_565t", {},
                 RuleSource("official_text_and_engine_verified", "continuous aura engine",
                            verification=("test_herald_neighbor_attack_aura",))),
        CardRule("EDR_844", {},
                 RuleSource("official_text_and_engine_verified", "continuous aura engine",
                            verification=("test_naralex_first_dragon_discount",))),
        CardRule("TLC_241", {},
                 RuleSource("official_text_and_engine_verified", "continuous aura engine",
                            verification=("test_ido_spell_lifecycle",))),
        CardRule("TLC_241t", {},
                 RuleSource("official_text_and_engine_verified", "continuous aura engine",
                            verification=("test_ido_spell_lifecycle",))),
        CardRule("CORE_WON_351", {},
                 RuleSource("official_text_and_engine_verified", "continuous aura engine",
                            verification=("test_weapon_aura_bonus",))),
        CardRule("JAIL_202", {},
                 RuleSource("official_text_and_engine_verified", "continuous aura engine",
                            verification=("test_spiderling_hero_attack_aura",))),
        CardRule("EDR_480", {},
                 RuleSource("official_text_and_engine_verified", "continuous aura engine",
                            verification=("test_goldrinn_beast_damage_aura",))),
        CardRule("TTN_844", {},
                 RuleSource("official_text_and_engine_verified", "continuous aura engine",
                            verification=("test_drawn_minion_attack_aura",))),
        CardRule("CATA_130", {},
                 RuleSource("official_text_and_engine_verified", "continuous aura engine",
                            verification=("test_last_mana_spent_aura",))),
        CardRule("CAP_104", {},
                 RuleSource("official_text_and_engine_verified", "continuous aura engine",
                            verification=("test_blastpowder_pirate_damage_aura",))),
        CardRule("CORE_BT_187", {},
                 RuleSource("official_text_and_engine_verified", "continuous aura engine",
                            verification=("test_kayn_ignores_taunt",))),
        CardRule("CORE_CATA_001", {},
                 RuleSource("official_text_and_engine_verified", "continuous aura engine",
                            verification=("test_tichondrius_hero_immunity",))),
        CardRule("CORE_EDR_003", {},
                 RuleSource("official_text_and_engine_verified", "continuous aura engine",
                            verification=("test_falric_doubles_corpses",))),
        CardRule("JAIL_890", {},
                 RuleSource("official_text_and_engine_verified", "continuous aura engine",
                            verification=("test_captive_nathrezim_global_cost_aura",))),
        CardRule("TIME_606", {},
                 RuleSource("official_text_and_engine_verified", "continuous aura engine",
                            verification=("test_quel_dorei_fletcher_hero_power_aura",))),
        CardRule("CAP_000", {},
                 RuleSource("official_text_and_engine_verified", "attack-trigger engine",
                            verification=("test_si7_slayer_buffs_stealthed_attacker",))),
        CardRule("CAP_003", {},
                 RuleSource("official_text_and_engine_verified", "attack-trigger engine",
                            verification=("test_si7_supplier_draws_after_attack",))),
        CardRule("CAP_005", {},
                 RuleSource("official_text_and_engine_verified", "attack-trigger engine",
                            verification=("test_mathias_shaw_discounts_after_stealth_attack",))),
        CardRule("TIME_042", {Hook.BATTLECRY: (DiscardHandGetInfiniteBanana(),)},
                 RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                            verification=("test_king_maluk_discards_hand_for_infinite_banana",))),
        CardRule("TIME_042t", {Hook.SPELL: (BuffActionTarget(1, 1, event="infinite_banana"),)},
                 RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                            verification=("test_king_maluk_discards_hand_for_infinite_banana",)),
                 TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("TIME_617", {},
                 RuleSource("official_text_and_engine_verified", "start-turn draw engine",
                            verification=("test_chronochiller_skips_start_turn_draw",))),
        CardRule("CATA_721", {},
                 RuleSource("official_text_and_engine_verified", "hand choice and shuffle engine",
                            verification=("test_sheltered_survivor_shuffles_selected_hand_card",))),
        CardRule("CORE_RLK_087", {Hook.SPELL: (DestroyHighestAttackEnemy(),)},
                 RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                            verification=("test_asphyxiate_destroys_highest_attack_enemy",))),
        CardRule("TIME_216", {Hook.SPELL: (DamageThenDrawIfSurvives(5, 2),)},
                 RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                            verification=("test_nascent_bolt_draws_two_if_survives",)),
                 targeting=TargetSpec(TargetKind.ENEMY_MINION)),
        CardRule("FIR_929", {Hook.DEATHRATTLE: (DrawMatching(card_type="SPELL", spell_school="FIRE"),)},
                 RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                            verification=("test_living_flame_draws_fire_spell",))),
        CardRule("TIME_858", {Hook.BATTLECRY: (DamageThenDrawExcess(5),)},
                 RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                            verification=("test_temporal_construct_draws_excess",)),
                 targeting=TargetSpec(TargetKind.ENEMY_MINION)),
        CardRule("TIME_037", {Hook.BATTLECRY: (DrawMinionBuffHand(2),)},
                 RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                            verification=("test_disciple_of_the_dove_draws_and_buffs_hand",))),
        CardRule("EDR_234", {Hook.SPELL: (DrawAndLockForTurns(2, 2),)},
                 RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                            verification=("test_emerald_bounty_locks_drawn_cards",))),
        CardRule("TIME_750", {Hook.SPELL: (DamageTargetThenConditionalMinionDraw(3),)},
                 RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                            verification=("test_precursory_strike_conditional_minion_draw",)),
                 targeting=TargetSpec(TargetKind.ANY_CHARACTER)),
        CardRule("CATA_568", {Hook.SPELL: (DrawTwoDiscountByHeroAttacks(),)},
                 RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                            verification=("test_muradins_last_stand_scales_with_attacks",))),
        CardRule("CATA_570", {Hook.BATTLECRY: (DrawCostRepeatExcess(10),)},
                 RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                            verification=("test_morchok_draws_with_excess_discount",))),
        CardRule("TIME_213", {Hook.BATTLECRY: (NatureHeldBuffDraw(),)},
                 RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                            verification=("test_primordial_overseer_nature_condition",))),
        CardRule(
            "CATA_724", {
                Hook.AFTER_PLAY: (Overload(3),),
                Hook.DEATHRATTLE: (UnlockOverloadedMana(),),
            },
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_stormbinder_unlocks_overload",)),
        ),
        CardRule(
            "EDR_525", {Hook.BATTLECRY: (OfferEffectChoice((
                ("hero_poisonous", (GiveHeroPoisonousThisTurn(),)),
                ("enemy_deathrattle", (SetDeathrattleDamageAllEnemies(2),)),
            )),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_barbed_thorn_choose_one",)),
        ),
        CardRule(
            "CORE_ONY_018", {Hook.BATTLECRY: (OfferEffectChoice((
                ("restore_hero", (HealHero(8),)),
                ("deal_damage", (DamageHero(4, "opponent"),)),
            )),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_boomkin_choose_one",)),
        ),
        CardRule(
            "CORE_TSC_650", {Hook.SPELL: (OfferEffectChoice((
                ("summon_orca", (Summon("TSC_650t"),)),
                ("summon_otters", (Summon("TSC_650t4", count=6),)),
            )),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_flipper_friends_choose_one",)),
        ),
        CardRule(
            "EDR_490", {Hook.SPELL: (OfferEffectChoice((
                ("summon_night_terrors", (Summon("EDR_490t", count=2),)),
                ("destroy_enemy_minion", (DestroyActionTarget(),)),
            )),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_sleep_paralysis_choose_one",)),
            # The summon branch needs no target; the destroy branch needs an
            # enemy minion.  Optional targeting exposes both legal forms.
            TargetSpec(TargetKind.ENEMY_MINION, optional=True),
        ),
        CardRule(
            "EDR_570", {Hook.SPELL: (OfferEffectChoice((
                ("damage_all_minions", (DamageAllMinions(1),)),
                ("buff_damaged_minion", (BuffActionTargetIfDamaged(2, 2),)),
            )),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_ominous_nightmares_choose_one",)),
            TargetSpec(TargetKind.DAMAGED_MINION, optional=True),
        ),
        CardRule(
            "EDR_815", {},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_corpse_flower_triggers_on_opponent_summon",)),
        ),
        CardRule(
            "TIME_618", {Hook.BATTLECRY: (ArmCorpseRebirth(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_husk_arms_corpse_rebirth",)),
        ),
        CardRule(
            "EX1_tk33", {Hook.HERO_POWER: (JaraxxusInferno(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_jaraxxus_inferno_hero_power",)),
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
            "CORE_AT_011", {Hook.OVERHEAL: (OverhealGainAttack(2),)},
            RuleSource(
                "official_text_and_engine_pattern", "HearthstoneJSON 251332",
                verification=("test_overheal_core_minions",),
            ),
        ),
        CardRule(
            "CORE_CFM_606", {Hook.OVERHEAL: (OverhealSummonCrystal(),)},
            RuleSource(
                "official_text_and_engine_pattern", "HearthstoneJSON 251332",
                verification=("test_overheal_core_minions",),
            ),
        ),
        CardRule(
            "CORE_CS3_014", {Hook.OVERHEAL: (OverhealDraw(),)},
            RuleSource(
                "official_text_and_engine_pattern", "HearthstoneJSON 251332",
                verification=("test_overheal_core_minions",),
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
            "CORE_RLK_083", {Hook.AFTER_PLAY: (DeathchillerAfterSpell(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ()),
        ),
        CardRule(
            "CORE_RLK_116", {Hook.BATTLECRY: (DiscoverUnholyIfUndeadDied(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ()),
        ),
        CardRule(
            "RLK_223", {
                Hook.BATTLECRY: (ThassarianRandomEnemyDamage(),),
                Hook.DEATHRATTLE: (ThassarianRandomEnemyDamage(),),
            },
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ()),
        ),
        CardRule(
            "TIME_611", {Hook.SPELL: (TimestopEffect(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ()),
        ),
        CardRule(
            "TIME_612", {Hook.SPELL: (OfferSpellDiscoverHealthCost(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ()),
        ),
        CardRule(
            "TIME_613", {Hook.DEATHRATTLE: (AddRandomLegendaryMinionDiscounted(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ()),
        ),
        CardRule(
            "JAIL_445", {Hook.SPELL: (BoneFlurryEffect(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ()),
        ),
        CardRule(
            "JAIL_454", {Hook.SPELL: (SummonNecronursesAttackTarget(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ()),
            TargetSpec(TargetKind.ENEMY_MINION),
        ),
        CardRule(
            "TIME_615", {Hook.SPELL: (FillHandRandomUndeadHealthCost(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ()),
        ),
        CardRule(
            "CATA_156", {Hook.SPELL: (HeraldRagnaros(), DamageEnemyMinions(4),)},
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
            "ETC_COIN2", {Hook.SPELL: (GainMana(1),)},
            RuleSource(
                "official_text_and_powerlog_verified", "HearthstoneJSON 251332 + real Power.log",
                "ETC_COIN2", "internal",
                ("test_every_coin_variant_grants_temporary_mana",),
            ),
        ),
        CardRule(
            "CATA_153", {Hook.BATTLECRY: (AddMinionsMatchingSourceAttack(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332; Colossal appendage model", ("test_alakir_colossal_and_cost_matching_minions",)),
        ),
        CardRule(
            "CATA_154", {},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332; Colossal appendage model", ("test_sinestra_colossal_doubles_other_class_spells",)),
        ),
        CardRule(
            "CATA_488", {Hook.END_TURN: (DamageAllOtherMinions(3),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332; Colossal appendage model", ("test_vulcanos_colossal_and_end_turn_damage",)),
        ),
        CardRule(
            "CATA_300", {},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332; Colossal appendage model", ("test_black_blood_colossal_bodies",)),
        ),
        CardRule(
            "CATA_432", {},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332; Colossal appendage model", ("test_chromatus_heads_remove_keywords",)),
        ),
        CardRule(
            "CATA_726", {},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332; Colossal appendage model", ("test_chogall_colossal_arms",)),
        ),
        CardRule(
            "TLC_828", {Hook.SPELL: (BuffBeastsEverywhere(2, 2),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_supreme_dinomancy_buffs_all_beast_zones",)),
        ),
        CardRule(
            "TLC_835", {Hook.SPELL: (SetHeroHealth(40),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_story_of_amara_sets_hero_health",)),
        ),
        CardRule(
            "TLC_901", {Hook.SPELL: (DamageMinionAndSameRace(3),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_fumigate_hits_same_race",)),
            TargetSpec(TargetKind.ENEMY_MINION),
        ),
        CardRule(
            "JAIL_326", {Hook.SPELL: (SetAllMinionStatsLikeTarget(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_judgment_sets_all_minion_stats",)),
            TargetSpec(TargetKind.FRIENDLY_MINION),
        ),
        CardRule(
            "JAIL_913", {Hook.SPELL: (BuffActionTargetWithLifesteal(5, 5),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_hold_them_off_buffs_lifesteal",)),
            TargetSpec(TargetKind.FRIENDLY_MINION),
        ),
        CardRule(
            "JAIL_444", {Hook.BATTLECRY: (DestroyOtherMinionsDrawAndRefresh(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_sawbones_destroys_other_minions_and_refreshes",)),
        ),
        CardRule(
            "JAIL_462", {Hook.BATTLECRY: (DrawTwoGainChargeIfMinions(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       ("test_getaway_hogdriver_draw_two_minions_charge",)),
        ),
        CardRule(
            "JAIL_380", {Hook.DEATHRATTLE: (
                DrawMatching(card_type="SPELL", started_in_deck=False),
            )},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       verification=("test_smuggled_shovel_draws_generated_spell",)),
        ),
        CardRule(
            "TIME_601", {Hook.BATTLECRY: (DrawUntilHandSize(3),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332",
                       ("test_arrow_retriever_draw_until_three",)),
        ),
        CardRule(
            "JAIL_395", {Hook.BATTLECRY: (TriggerFriendlyDeathrattle(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332", ("test_sewer_swimmer_triggers_friendly_deathrattle",)),
            TargetSpec(TargetKind.FRIENDLY_MINION),
        ),
        CardRule(
            "JAIL_721", {},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332; summon event model", ("test_tras_tath_gains_summoned_demon_stats",)),
        ),
        CardRule(
            "JAIL_718", {},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332; spell-play event model", ("test_black_market_auctioneer_draws_after_spell",)),
        ),
        CardRule(
            "JAIL_407", {},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332; card-play event model", ("test_vanessa_generates_discounted_battlecry_minion",)),
        ),
        CardRule(
            "JAIL_321", {Hook.BATTLECRY: (CastRandomMageSecretsIfSpellCast(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332; spell-count event model", ("test_tricksy_improviser_prepared_secrets",)),
        ),
        CardRule(
            "JAIL_909", {},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332; combo play event model", ("test_defias_wannabe_prepare_combo",)),
        ),
        CardRule(
            "JAIL_735", {Hook.SPELL: (CodeVioletSummon(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332; spell-count event model", ("test_code_violet_repeats_after_three_other_spells",)),
        ),
        CardRule(
            "CAP_407", {Hook.SPELL: (WantedPosterDiscover(),)},
            RuleSource("official_text_and_engine_verified", "HearthstoneJSON 251332; Discover + Prepare state", ("test_wanted_poster_grants_prepare",)),
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
            # The target belongs to the destroy choice only. The engine
            # exposes it after the player has selected that branch.
            TargetSpec(TargetKind.ANY_MINION, optional=True),
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
        CardRule(
            "TIME_715", {Hook.SPELL: (Draw(2),)},
            RuleSource(
                "official_text_and_engine_pattern", "HearthstoneJSON 251332",
                verification=("test_for_glory_costs_less_per_enemy_minion",),
            ),
            cost_modifier=CostMinusEnemyMinions(),
        ),
        CardRule(
            "END_020", {Hook.SPELL: (DamageThenDrawOrSummonOneCost(),)},
            RuleSource(
                "official_text_and_engine_pattern", "HearthstoneJSON 251332",
                verification=("test_eternal_toil_draw_or_summon",),
            ),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "CORE_WC_701", {
                Hook.DEATHRATTLE: (SetDeathrattleDamageAllEnemies(1),),
            },
            RuleSource(
                "official_text_and_engine_pattern", "HearthstoneJSON 251332",
                verification=("test_felrattler_deathrattle_damages_enemy_minions",),
            ),
        ),
        CardRule(
            "TIME_031", {Hook.SPELL: (DrawDifferentCosts(3),)},
            RuleSource(
                "official_text_and_engine_pattern", "HearthstoneJSON 251332",
                verification=("test_rafaam_ladder_draws_different_costs",),
            ),
        ),
        CardRule(
            "TIME_032", {Hook.BATTLECRY: (ChronogorDrawHighestGiveLowest(2),)},
            RuleSource(
                "official_text_and_engine_pattern", "HearthstoneJSON 251332",
                verification=("test_chronogor_draws_highest_and_gives_lowest",),
            ),
        ),
        CardRule(
            "TIME_614", {Hook.BATTLECRY: (LiferenderIfHeroHealthChanged(6),)},
            RuleSource(
                "official_text_and_engine_pattern", "HearthstoneJSON 251332",
                verification=("test_liferender_requires_hero_health_change",),
            ),
            TargetSpec(TargetKind.ENEMY_MINION, optional=True),
        ),
        CardRule(
            "RLK_720", {Hook.END_TURN: (GnomeMuncherEndTurn(),)},
            RuleSource(
                "official_text_and_engine_pattern", "HearthstoneJSON 251332",
                verification=("test_gnome_muncher_attacks_lowest_health_enemy",),
            ),
        ),
        CardRule(
            "FIR_902", {Hook.SPELL: (ArmSigilOfCinder(),)},
            RuleSource(
                "official_text_and_engine_pattern", "HearthstoneJSON 251332",
                verification=("test_sigil_of_cinder_triggers_next_turn",),
            ),
        ),
        CardRule(
            "JAIL_440", {Hook.AFTER_DAMAGE: (SummonFrailGhoulsAfterDamage(),)},
            RuleSource(
                "official_text_and_engine_pattern", "HearthstoneJSON 251332",
                verification=("test_tower_of_ghouls_summons_after_damage",),
            ),
        ),
        CardRule(
            "TLC_630", {Hook.AFTER_DAMAGE: (GorishiStingerAfterDamage(),)},
            RuleSource(
                "official_text_and_engine_pattern", "HearthstoneJSON 251332",
                verification=("test_gorishi_wasp_generates_stinger_after_damage",),
            ),
        ),
        # ---- 50-card Standard tranche ---------------------------------
        # These keyword-only cards use the canonical metadata keyword
        # initialization in dragon_mirror.py; an empty rule is intentional
        # and keeps them auditable without duplicating metadata behavior.
        *tuple(CardRule(card_id, {}, _BATCH_50_SOURCE) for card_id in (
            "RLK_067", "CORE_BT_921", "EDR_272", "CATA_558",
            "CORE_CS2_179", "CORE_DRG_079", "CORE_EX1_010", "CORE_EX1_028",
            "CORE_GIL_558", "CORE_GVG_085", "CORE_LOOT_137", "CORE_NEW1_023",
            "CORE_ULD_723", "CS3_038", "Core_CS2_200", "EDR_486", "EDR_598",
            "TIME_045", "TIME_053", "TIME_056", "TLC_248", "CORE_ICC_038",
            "CORE_BT_701",
        )),
        CardRule("CORE_EX1_082", {Hook.BATTLECRY: (DamageRandomOtherCharacters(3),)},
                 _BATCH_50_SOURCE),
        CardRule("CORE_ULD_271", {Hook.BATTLECRY: (DamageSelf(3),)},
                 _BATCH_50_SOURCE),
        CardRule("CORE_EX1_058", {Hook.BATTLECRY: (GrantAdjacentTaunt(),)},
                 _BATCH_50_SOURCE),
        CardRule("CORE_EX1_103", {Hook.BATTLECRY: (BuffOtherMurlocsHealth(2),)},
                 _BATCH_50_SOURCE),
        CardRule("CORE_EX1_506", {Hook.BATTLECRY: (Summon("CORE_EX1_506a"),)},
                 _BATCH_50_SOURCE),
        CardRule("CORE_LOOT_413", {Hook.DEATHRATTLE: (GainArmor(3),)},
                 _BATCH_50_SOURCE),
        CardRule("CORE_REV_308", {Hook.BATTLECRY: (SummonRandomMinionWithCost(2),)},
                 _BATCH_50_SOURCE),
        CardRule("CORE_SW_088", {Hook.SPELL: (DamageEnemyHero(3), SummonWithTaunt("CORE_CS2_065", 2))},
                 _BATCH_50_SOURCE),
        # The legacy engine owns the silence effect, while the rule registry
        # owns target metadata so generated play effects can construct a
        # legal action for Ironbeak Owl.
        CardRule("CORE_SW_066", {}, _BATCH_50_SOURCE,
                 TargetSpec(TargetKind.ANY_MINION)),
        CardRule("CORE_CS2_042", {Hook.BATTLECRY: (DamageActionTarget(4),)},
                 _BATCH_50_SOURCE, TargetSpec(TargetKind.ENEMY_CHARACTER)),
        CardRule("CORE_EX1_134", {Hook.BATTLECRY: (IfSourceAttribute("combo_active", (DamageActionTarget(3),)),)},
                 _BATCH_50_SOURCE, TargetSpec(TargetKind.ENEMY_CHARACTER, optional=True)),
        CardRule("CORE_GVG_059", {Hook.BATTLECRY: (GiveRandomFriendlyDivineShieldTaunt(),)},
                 _BATCH_50_SOURCE),
        CardRule("CORE_EX1_362", {Hook.BATTLECRY: (GiveActionTargetDivineShield(),)},
                 _BATCH_50_SOURCE, TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("CORE_CFM_753", {Hook.BATTLECRY: (BuffAllMinionsInHand(1, 1),)},
                 _BATCH_50_SOURCE),
        CardRule("CORE_TSC_076", {Hook.SPELL: (SummonWithTaunt("TSC_076t3"), SummonWithTaunt("TSC_076t2"), SummonWithTaunt("TSC_076t"))},
                 _BATCH_50_SOURCE),
        CardRule("CORE_UNG_952", {Hook.SPELL: (GrantTargetDeathrattleSummon("UNG_810"),)},
                 _BATCH_50_SOURCE, TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("CORE_GVG_061", {Hook.SPELL: (SummonRecruitsAndEquip(),)},
                 _BATCH_50_SOURCE),
        CardRule("CORE_BAR_310", {Hook.DEATHRATTLE: (HealFriendlyCharacters(8),)},
                 _BATCH_50_SOURCE),
        CardRule("CORE_EX1_198", {Hook.BATTLECRY: (DestroyTargetGainHealth(),)},
                 _BATCH_50_SOURCE, TargetSpec(TargetKind.ANY_MINION)),
        CardRule("CORE_ICC_214", {Hook.DEATHRATTLE: (DestroyRandomEnemyMinion(),)},
                 _BATCH_50_SOURCE),
        CardRule("CORE_NEW1_031", {Hook.SPELL: (SummonAnimalCompanion(),)},
                 _BATCH_50_SOURCE),
        CardRule("CORE_OG_211", {Hook.SPELL: (SummonAllAnimalCompanions(),)},
                 _BATCH_50_SOURCE),
        CardRule("CORE_AV_337", {Hook.DEATHRATTLE: (SummonWithTaunt("AV_337t", 2),)},
                 _BATCH_50_SOURCE),
        CardRule("CORE_RLK_062", {Hook.BATTLECRY: (Summon("CORE_RLK_062", 2),)},
                 _BATCH_50_SOURCE),
        CardRule("CORE_ULD_178", {Hook.BATTLECRY: (OfferEffectChoice((
            ("rush_taunt", (GrantKeyword("rush"), GrantKeyword("taunt"))),
            ("rush_shield", (GrantKeyword("rush"), GrantKeyword("divine_shield"))),
            ("rush_windfury", (GrantKeyword("rush"), GrantKeyword("windfury"))),
            ("taunt_shield", (GrantKeyword("taunt"), GrantKeyword("divine_shield"))),
            ("taunt_windfury", (GrantKeyword("taunt"), GrantKeyword("windfury"))),
            ("shield_windfury", (GrantKeyword("divine_shield"), GrantKeyword("windfury"))),
        )),)}, _BATCH_50_SOURCE),
        CardRule("CORE_WON_141", {Hook.BATTLECRY: (BuffDifferentTribeMinions(),)},
                 _BATCH_50_SOURCE),
        CardRule("CORE_LOOT_309", {Hook.SPELL: (GainArmor(6), SummonFromDeckAtMostCost(4))},
                 _BATCH_50_SOURCE),
        CardRule("CORE_RLK_657", {Hook.BATTLECRY: (GainArmor(6),), Hook.DEATHRATTLE: (GainArmor(6),)},
                 _BATCH_50_SOURCE),
        # ---- 50-card Standard tranche 50B -----------------------------
        # Engine-owned triggers are registered with an empty hook map when
        # dragon_mirror.py already owns their complete lifecycle (or when the
        # card is a metadata-only conditional).  This keeps coverage audits
        # honest without duplicating state transitions here.
        *tuple(CardRule(card_id, {}, _BATCH_50B_SOURCE) for card_id in (
            "CORE_RLK_121", "CORE_EX1_007", "JAIL_461", "CORE_RLK_706",
            "TLC_987", "EDR_979", "JAIL_719", "TIME_856", "TLC_605",
        )),
        CardRule("EDR_253", {Hook.AFTER_HERO_ATTACK: (Draw(),)}, _BATCH_50B_SOURCE),
        CardRule("EDR_256", {Hook.BATTLECRY: (DreamwardenBattlecry(),)}, _BATCH_50B_SOURCE),
        CardRule("CORE_TRL_240", {Hook.BATTLECRY: (SavageStrikerBattlecry(),)},
                 _BATCH_50B_SOURCE, TargetSpec(TargetKind.ENEMY_MINION)),
        CardRule("CORE_NEW1_020", {Hook.AFTER_PLAY: (DamageAllMinions(1),)}, _BATCH_50B_SOURCE),
        CardRule("CORE_NEW1_021", {Hook.START_TURN: (DamageAllMinions(99),)}, _BATCH_50B_SOURCE),
        CardRule("EDR_110", {Hook.DEATHRATTLE: (DamageRandomEnemyMinion(1),)}, _BATCH_50B_SOURCE),
        CardRule("TLC_633", {Hook.BATTLECRY: (BugsquasherBattlecry(),)},
                 _BATCH_50B_SOURCE, TargetSpec(TargetKind.ENEMY_TYPED_MINION)),
        CardRule("CORE_KAR_057", {Hook.BATTLECRY: (OfferIvoryKnightDiscover(),)}, _BATCH_50B_SOURCE),
        CardRule("EDR_255", {Hook.SPELL: (DamageLowestHealthEnemyRepeated(5, 2),)}, _BATCH_50B_SOURCE),
        CardRule("FIR_961", {Hook.BATTLECRY: (AshleafPixieBattlecry(),)}, _BATCH_50B_SOURCE),
        CardRule("JAIL_118", {Hook.BATTLECRY: (DestroyNonPaladinMinions(),)}, _BATCH_50B_SOURCE),
        # Mend the Timeline is resolved by the engine's Rewind dispatcher;
        # keeping the registry entry empty prevents a generic Discover from
        # bypassing its two-random-Holy-spells + healing semantics.
        CardRule("TIME_018", {}, _BATCH_50B_SOURCE),
        CardRule("TIME_019", {Hook.BATTLECRY: (ManifestedTimewaysBattlecry(),)}, _BATCH_50B_SOURCE),
        CardRule("CAP_803", {Hook.DEATHRATTLE: (HealHero(3),)}, _BATCH_50B_SOURCE),
        CardRule("CATA_304", {Hook.BATTLECRY: (InjuredAttendantBattlecry(),)}, _BATCH_50B_SOURCE),
        CardRule("FIR_777", {Hook.BATTLECRY: (SpiritKaldoreiBattlecry(),)}, _BATCH_50B_SOURCE),
        CardRule("TIME_427", {Hook.BATTLECRY: (CleansingLightspawnBattlecry(),)},
                 _BATCH_50B_SOURCE, TargetSpec(TargetKind.ENEMY_MINION)),
        CardRule("TIME_431", {Hook.BATTLECRY: (AmberPriestessBattlecry(),)},
                 _BATCH_50B_SOURCE, TargetSpec(TargetKind.ANY_CHARACTER)),
        CardRule("TIME_855", {Hook.SPELL: (ArcaneBarrageEffect(),)},
                 _BATCH_50B_SOURCE, TargetSpec(TargetKind.ENEMY_CHARACTER)),
        CardRule("END_014", {Hook.SPELL: (SynchronizedSparkEffect(),)},
                 _BATCH_50B_SOURCE, TargetSpec(TargetKind.ENEMY_MINION)),
        CardRule("TIME_600", {Hook.SPELL: (PreciseShotEffect(),)},
                 _BATCH_50B_SOURCE, TargetSpec(TargetKind.ENEMY_CHARACTER)),
        CardRule("EDR_941", {Hook.SPELL: (StarsurgeEffect(),)},
                 _BATCH_50B_SOURCE, TargetSpec(TargetKind.ANY_MINION)),
        CardRule("EDR_874", {Hook.SPELL: (StellarBalanceEffect(),)}, _BATCH_50B_SOURCE),
        CardRule("TLC_220", {Hook.AFTER_SUMMON: (AfterSummonElementalDamage(),)}, _BATCH_50B_SOURCE),
        CardRule("END_023", {Hook.SPELL: (BitterEndEffect(),)},
                 _BATCH_50B_SOURCE, TargetSpec(TargetKind.ANY_MINION)),
        CardRule("CATA_209", {Hook.BATTLECRY: (BattlefieldBlasterBattlecry(),)}, _BATCH_50B_SOURCE),
        CardRule("CORE_BAR_878", {Hook.AFTER_PLAY: (VeteranWarmedicAfterHoly(),)}, _BATCH_50B_SOURCE),
        CardRule("EDR_842", {Hook.AFTER_HERO_ATTACK: (DefiledSpearAfterHeroAttack(),)}, _BATCH_50B_SOURCE),
        CardRule("FIR_904", {Hook.AFTER_PLAY: (FelfireBlazeAfterFel(),)}, _BATCH_50B_SOURCE),
        CardRule("CATA_552", {Hook.BATTLECRY: (EbonscaleScoutBattlecry(),)},
                 _BATCH_50B_SOURCE, TargetSpec(TargetKind.ENEMY_MINION)),
        CardRule("EDR_262", {Hook.SPELL: (SpiritBondEffect(),)},
                 _BATCH_50B_SOURCE, TargetSpec(TargetKind.ANY_MINION)),
        CardRule("MEND_302", {Hook.BATTLECRY: (WastelandVanguardEffect(),)}, _BATCH_50B_SOURCE),
        CardRule("TLC_365", {Hook.SPELL: (DamageActionTarget(3),)},
                 _BATCH_50B_SOURCE, TargetSpec(TargetKind.ANY_MINION)),
        CardRule("TLC_621", {Hook.DEATHRATTLE: (WillfulWatcherDeathrattle(),)}, _BATCH_50B_SOURCE),
        CardRule("TLC_829", {Hook.BATTLECRY: (RavenousDevilsaurBattlecry(),)},
                 _BATCH_50B_SOURCE, TargetSpec(TargetKind.ANY_MINION)),
        CardRule("CATA_494", {Hook.AFTER_DISCARD: (MaloriakAfterDiscard(),)}, _BATCH_50B_SOURCE),
        CardRule("JAIL_803", {Hook.SPELL: (FreezeActionTarget(), Draw(2),)},
                 _BATCH_50B_SOURCE, TargetSpec(TargetKind.ENEMY_CHARACTER)),
        CardRule("END_026", {Hook.AFTER_PLAY: (FragmentOfNothingAfterSpell(),)}, _BATCH_50B_SOURCE),
        CardRule("EDR_540", {Hook.AFTER_SUMMON: (TwistedWebweaverAfterSummon(),)}, _BATCH_50B_SOURCE),
        CardRule("JAIL_503", {Hook.DEATHRATTLE: (BlackpawsWhipDeathrattle(),)}, _BATCH_50B_SOURCE),
        CardRule("TLC_466", {Hook.SPELL: (StoryOfLakkariSpell(),)}, _BATCH_50B_SOURCE),
        # ---- 50-card Standard tranche 50C -----------------------------
        # These cards already have an engine-owned lifecycle (pre-game deck
        # setup, generated card handling, keywords, weapons, locations, or
        # conditional metadata).  A registry row makes that ownership
        # auditable without replaying the lifecycle as a second card script.
        *tuple(CardRule(card_id, {}, _BATCH_50C_SOURCE) for card_id in (
            "TLC_817", "CATA_139", "TLC_513", "TLC_446", "TLC_433",
            "TLC_460", "TLC_239", "TLC_229", "TLC_631", "TLC_830",
            "TLC_602", "JAIL_450", "TLC_426", "JAIL_430", "TLC_833",
            "JAIL_458", "EDR_847", "CORE_RLK_086", "CORE_LOOT_044",
            "TLC_478", "TLC_107", "JAIL_730", "JAIL_376", "JAIL_329",
            "FIR_907", "END_016", "DINO_408", "CORE_OG_031",
            "CORE_DAL_720", "CORE_BT_781", "CATA_472", "CATA_467",
            "CAP_103", "CORE_UNG_928", "TLC_101", "END_031",
        )),
        CardRule(
            "CORE_DMF_067",
            {Hook.BATTLECRY: (EachPlayerDraw(),), Hook.DEATHRATTLE: (EachPlayerDraw(),)},
            _BATCH_50C_SOURCE,
        ),
        CardRule("CORE_DRG_403", {Hook.BATTLECRY: (ApplyHeroPowerSurcharge(),)},
                 _BATCH_50C_SOURCE),
        CardRule("CORE_EX1_059", {Hook.BATTLECRY: (SwapActionTargetAttackHealth(),)},
                 _BATCH_50C_SOURCE, TargetSpec(TargetKind.ANY_MINION)),
        CardRule("CORE_GIL_534", {Hook.AFTER_HERO_ATTACK: (HenchClanThugAfterHeroAttack(),)},
                 _BATCH_50C_SOURCE),
        CardRule("CORE_GIL_623", {Hook.BATTLECRY: (WitchwoodGrizzlyBattlecry(),)},
                 _BATCH_50C_SOURCE),
        CardRule("CORE_KAR_062", {Hook.BATTLECRY: (OfferDragonDiscoverIfHolding(),)},
                 _BATCH_50C_SOURCE),
        CardRule("CORE_SCH_713", {Hook.BATTLECRY: (ApplyOpponentSpellSurchargeNextTurn(),)},
                 _BATCH_50C_SOURCE),
        CardRule("EDR_254", {Hook.AFTER_PLAY: (AnimatedMoonwellAfterSpell(),)},
                 _BATCH_50C_SOURCE),
        CardRule("EDR_470", {Hook.AFTER_HERO_POWER: (GainSourceHealth(2),)},
                 _BATCH_50C_SOURCE),
        CardRule("EDR_861", {Hook.DEATHRATTLE: (GainEmptyManaForBothPlayers(),)},
                 _BATCH_50C_SOURCE),
        CardRule("END_008", {Hook.AFTER_HERO_POWER: (RefreshManaAfterHeroPower(),)},
                 _BATCH_50C_SOURCE),
        CardRule("TLC_468", {Hook.DEATHRATTLE: (BlobOfTarDeathrattle(),)},
                 _BATCH_50C_SOURCE),
        CardRule("TIME_443", {Hook.SPELL: (HoundsOfFurySpell(),)},
                 _BATCH_50C_SOURCE),
        CardRule(
            "TLC_242",
            {Hook.BATTLECRY: (OfferEffectChoice((
                ("taunt", (GrantKeyword("taunt"),)),
                ("poisonous", (GrantKeyword("poisonous"),)),
                ("stats", (GainSourceStats(1, 1),)),
            )),)},
            _BATCH_50C_SOURCE,
        ),
        # ---- 50-card Standard tranche 50D -----------------------------
        # These six cards have a complete engine-owned lifecycle.  Register
        # them explicitly so the Standard coverage report distinguishes
        # audited ownership from a missing implementation.
        *tuple(CardRule(card_id, {}, _BATCH_50D_SOURCE) for card_id in (
            "CATA_140", "CATA_190h", "DINO_435", "END_015", "JAIL_200", "TLC_825",
        )),
        CardRule(
            "CORE_BOT_576",
            {Hook.BATTLECRY: (IfSourceAttribute(
                "combo_active", (OptionalBuffActionTarget(4, 0),),
            ),)},
            _BATCH_50D_SOURCE, TargetSpec(TargetKind.FRIENDLY_MINION, optional=True),
        ),
        CardRule("CORE_BT_321", {Hook.BATTLECRY: (
            OfferFilteredDiscover(card_type="MINION", race="DEMON"),
        )}, _BATCH_50D_SOURCE),
        CardRule("CORE_BT_416", {Hook.BATTLECRY: (
            SetNextRaceCostReduction("DEMON", 2),
        )}, _BATCH_50D_SOURCE),
        CardRule("CORE_CATA_002", {Hook.BATTLECRY: (
            ResurrectHighestCostFriendly(),
        )}, _BATCH_50D_SOURCE),
        # Rehgar's post-attack observer needs the combat outcome and is
        # therefore dispatched by ``Game._after_minion_attack``.
        CardRule("CORE_CATA_004", {}, _BATCH_50D_SOURCE),
        CardRule("CORE_CFM_781", {Hook.AFTER_ATTACK: (
            AddRandomFilteredCards(other_class=True),
        )}, _BATCH_50D_SOURCE),
        CardRule("CORE_CFM_790", {Hook.BATTLECRY: (
            SummonOpponentRandomHandMinion(),
        )}, _BATCH_50D_SOURCE),
        CardRule("CORE_DMF_511", {Hook.BATTLECRY: (
            SetNextComboCostReduction(2),
        )}, _BATCH_50D_SOURCE),
        CardRule("CORE_EDR_001", {Hook.BATTLECRY: (
            AddRandomFilteredCards(count=2, card_type="SPELL", card_class="MAGE"),
        )}, _BATCH_50D_SOURCE),
        CardRule("CORE_EX1_131", {Hook.BATTLECRY: (
            IfSourceAttribute("combo_active", (Summon("EX1_131t"),)),
        )}, _BATCH_50D_SOURCE),
        CardRule("CORE_EX1_383", {Hook.DEATHRATTLE: (
            EquipFixedWeapon("EX1_383t", "Ashbringer", 5, 3),
        )}, _BATCH_50D_SOURCE),
        CardRule("CORE_EX1_559", {Hook.AFTER_PLAY: (
            AddToHand("CORE_CS2_029"),
        )}, _BATCH_50D_SOURCE),
        CardRule("CORE_GIL_531", {Hook.BATTLECRY: (
            AddRandomFilteredCards(card_type="SPELL", card_class="SHAMAN"),
        )}, _BATCH_50D_SOURCE),
        CardRule("CORE_ICC_210", {Hook.END_TURN: (
            EndTurnBuffRandomOther(1, 1),
        )}, _BATCH_50D_SOURCE),
        CardRule("CORE_ICC_407", {Hook.BATTLECRY: (
            RemoveTopOpponentDeckCard(),
        )}, _BATCH_50D_SOURCE),
        CardRule("CORE_LOE_039", {Hook.BATTLECRY: (
            OfferMechIfControllingAnother(),
        )}, _BATCH_50D_SOURCE),
        CardRule("CORE_ONY_022", {Hook.BATTLECRY: (
            OfferFilteredDiscover(card_type="SPELL", spell_school="HOLY"),
        )}, _BATCH_50D_SOURCE),
        CardRule("CORE_SCH_181", {Hook.BATTLECRY: (
            SummonRaceFromHandAndDeck("DEMON"),
        )}, _BATCH_50D_SOURCE),
        CardRule("CORE_TID_931", {Hook.SPELL: (
            AddRandomFilteredCards(count=2, card_type="SPELL", other_class=True),
        )}, _BATCH_50D_SOURCE),
        CardRule("CORE_TRL_111", {Hook.BATTLECRY: (
            BuffCurrentWeaponDurabilityIfBeast(),
        )}, _BATCH_50D_SOURCE),
        CardRule("CORE_TRL_900", {Hook.BATTLECRY: (
            FillHandWithToken("TRL_348t"),
        )}, _BATCH_50D_SOURCE),
        CardRule("CORE_ULD_280", {Hook.DEATHRATTLE: (
            ReturnRandomEnemyMinion(),
        )}, _BATCH_50D_SOURCE),
        CardRule("CORE_WON_096", {Hook.BATTLECRY: (
            OfferFilteredDiscover(cost=1),
        )}, _BATCH_50D_SOURCE),
        CardRule("Core_UNG_072", {Hook.BATTLECRY: (
            OfferFilteredDiscover(card_type="MINION", mechanic="TAUNT"),
        )}, _BATCH_50D_SOURCE),
        CardRule("DINO_130", {Hook.DEATHRATTLE: (
            SummonLongneckAndBuff(),
        )}, _BATCH_50D_SOURCE),
        CardRule("DINO_131", {Hook.DEATHRATTLE: (
            SummonRandomDeckRaceWithLifesteal("BEAST"),
        )}, _BATCH_50D_SOURCE),
        CardRule("DINO_403", {Hook.SPELL: (
            SetActionTargetStatsAndKeyword(8, 8, "charge"),
        )}, _BATCH_50D_SOURCE, TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("DINO_405", {Hook.SPELL: (
            ScheduleHatchingCeremony(),
        )}, _BATCH_50D_SOURCE),
        CardRule("DINO_412", {Hook.END_TURN: (
            AddRandomMultiRaceMinion(),
        )}, _BATCH_50D_SOURCE),
        CardRule("DINO_422", {Hook.DEATHRATTLE: (
            AnkylodonDeathrattle(),
        )}, _BATCH_50D_SOURCE),
        CardRule("DINO_433", {Hook.SPELL: (
            SummonRandomTauntCosts((6, 4, 2)),
        )}, _BATCH_50D_SOURCE),
        CardRule(
            "DINO_434",
            {
                Hook.BATTLECRY: (AddRandomFilteredCards(card_type="MINION", cost=1),),
                Hook.DEATHRATTLE: (AddRandomFilteredCards(card_type="SPELL", cost=1),),
            },
            _BATCH_50D_SOURCE,
        ),
        CardRule("EDR_001", {Hook.BATTLECRY: (AddRandomDreamCard(),)}, _BATCH_50D_SOURCE),
        CardRule("EDR_060", {Hook.SPELL: (
            GainArmor(5), SummonRandomCostWithTaunt(5),
        )}, _BATCH_50D_SOURCE),
        CardRule("EDR_105", {Hook.BATTLECRY: (
            OfferFilteredDiscover(card_type="MINION", cost=3, dark_gift=True),
        )}, _BATCH_50D_SOURCE),
        CardRule("EDR_230", {Hook.BATTLECRY: (
            BuffTopDeckMinions(3, 4, 4),
        )}, _BATCH_50D_SOURCE),
        CardRule("EDR_252", {Hook.SPELL: (
            SetTargetStatsByAllegiance(),
        )}, _BATCH_50D_SOURCE, TargetSpec(TargetKind.ANY_MINION)),
        CardRule("EDR_273", {Hook.SPELL: (
            OfferFilteredDiscover(mechanic="CHOOSE_ONE", other_class=True),
        )}, _BATCH_50D_SOURCE),
        CardRule("EDR_481", {Hook.BATTLECRY: (
            SummonCopyIfSourceAttackAtLeast(4),
        )}, _BATCH_50D_SOURCE),
        CardRule("EDR_531", {Hook.SPELL: (
            DestroyFriendlyMinionGainArmor(8),
        )}, _BATCH_50D_SOURCE, TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("EDR_848", {Hook.SPELL: (
            HealHero(6), AddRandomFilteredCards(count=3, card_type="SPELL", card_class="DRUID"),
        )}, _BATCH_50D_SOURCE),
        CardRule("EDR_890", {Hook.DEATHRATTLE: (
            DiscountRightmostHeldCard(2),
        )}, _BATCH_50D_SOURCE),
        CardRule("EDR_942", {Hook.END_TURN: (
            GrantHeroDivineShield(),
        )}, _BATCH_50D_SOURCE),
        CardRule("EDR_978", {Hook.DEATHRATTLE: (
            ShuffleDiscountedSourceAtBottom(1),
        )}, _BATCH_50D_SOURCE),
        # ---- 50-card Standard tranche 50E -----------------------------
        # Time Travel.  All "from the past" generators deliberately consume
        # the shared executable non-Time pool defined above.
        CardRule("TIME_006", {Hook.SPELL: (
            Summon("TIME_006t1"),
            IfHoldingDragon((Summon("TIME_006t1"),)),
        )}, _BATCH_50E_SOURCE),
        CardRule("TIME_016", {Hook.SPELL: (
            # A class Discover pool includes neutral cards playable by that
            # class.  This runtime's safe historical Mech closure therefore
            # uses the Mechanical tribe rather than incorrectly requiring a
            # non-existent literal PALADIN/MECH metadata combination.
            OfferPastDiscover(card_type="MINION", race="MECHANICAL",
                              after_pick="neon_innovation"),
        )}, _BATCH_50E_SOURCE),
        CardRule("TIME_025", {Hook.BATTLECRY: (ShuffleShredsOfTime(),)}, _BATCH_50E_SOURCE),
        CardRule("TIME_026", {Hook.SPELL: (
            BuffAllFriendlyMinions(1, 1), ShuffleShredsOfTime(),
        )}, _BATCH_50E_SOURCE),
        CardRule("TIME_027", {Hook.SPELL: (
            DamageRandomSplitEnemyCharacters(6), ShuffleShredsOfTime(),
        )}, _BATCH_50E_SOURCE),
        CardRule("TIME_028", {Hook.BATTLECRY: (
            CastShredFromDeck((3, 3)),
        )}, _BATCH_50E_SOURCE),
        CardRule("TIME_029", {Hook.BATTLECRY: (
            CastShredFromDeck(summon_source_copy=True),
        )}, _BATCH_50E_SOURCE),
        CardRule("TIME_036", {Hook.BATTLECRY: (RoyalInformantBattlecry(),)}, _BATCH_50E_SOURCE),
        CardRule("TIME_040", {Hook.DEATHRATTLE: (
            AddRandomPast(card_type="MINION", cost=5),
        )}, _BATCH_50E_SOURCE),
        CardRule("TIME_047", {}, _BATCH_50E_SOURCE,
                 cost_modifier=CostEnemyHeroDamageThisTurn()),
        CardRule("TIME_049", {Hook.START_TURN: (
            TransformSourceIntoRandomPast(5),
        )}, _BATCH_50E_SOURCE),
        CardRule("TIME_050", {Hook.AFTER_DAMAGE: (
            SwapSourceStatsAfterDamage(),
        )}, _BATCH_50E_SOURCE),
        CardRule("TIME_052", {Hook.DEATHRATTLE: (
            SummonRandomPast(),
        )}, _BATCH_50E_SOURCE),
        CardRule("TIME_055", {Hook.AFTER_DAMAGE: (
            TransformSourceIntoRandomPast(7),
        )}, _BATCH_50E_SOURCE),
        CardRule("TIME_057", {Hook.BATTLECRY: (ResetAllHandCosts(),)}, _BATCH_50E_SOURCE),
        CardRule("TIME_061", {Hook.BATTLECRY: (ReverseOwnDeck(),)}, _BATCH_50E_SOURCE),
        CardRule("TIME_062", {Hook.BATTLECRY: (ChronicleKeeperBattlecry(),)}, _BATCH_50E_SOURCE),
        CardRule("TIME_100", {Hook.END_TURN: (
            BuffZone("hand", attack=1, health=1, card_types=("MINION",)),
        )}, _BATCH_50E_SOURCE),
        CardRule("TIME_102", {Hook.BATTLECRY: (CircadiamancerBattlecry(),)}, _BATCH_50E_SOURCE),
        CardRule("TIME_212", {Hook.SPELL: (LightningRod(),)}, _BATCH_50E_SOURCE,
                 TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("TIME_214", {}, _BATCH_50E_SOURCE),
        CardRule("TIME_215", {Hook.SPELL: (Thunderquake(),)}, _BATCH_50E_SOURCE),
        CardRule("TIME_217", {}, _BATCH_50E_SOURCE),
        CardRule("TIME_428", {Hook.END_TURN: (
            BuffAllOtherFriendlyMinions(health=1),
        )}, _BATCH_50E_SOURCE),
        CardRule("TIME_429", {Hook.BATTLECRY: (DivineAugurBattlecry(),)}, _BATCH_50E_SOURCE),
        CardRule("TIME_434", {Hook.DEATHRATTLE: (TemporalShadowDeathrattle(),)}, _BATCH_50E_SOURCE),
        CardRule("TIME_435", {Hook.BATTLECRY: (EternusBattlecry(),)}, _BATCH_50E_SOURCE,
                 TargetSpec(TargetKind.ENEMY_MINION)),
        CardRule("TIME_444", {Hook.DEATHRATTLE: (
            AddRandomPast(card_type="MINION", race="DEMON"),
        )}, _BATCH_50E_SOURCE),
        CardRule("TIME_447", {Hook.SPELL: (PowerWordBarrier(),)}, _BATCH_50E_SOURCE,
                 TargetSpec(TargetKind.ANY_CHARACTER)),
        CardRule("TIME_448", {Hook.SPELL: (
            OfferPastDiscover(card_type="MINION", repeats=2, after_pick="solitude"),
        )}, _BATCH_50E_SOURCE),
        CardRule("TIME_449", {Hook.SPELL: (LastingLegacy(),)}, _BATCH_50E_SOURCE),
        CardRule("TIME_616", {Hook.SPELL: (ResurrectHighestCostUndead(),)}, _BATCH_50E_SOURCE),
        CardRule("TIME_620", {}, _BATCH_50E_SOURCE),
        CardRule("TIME_700", {Hook.SPELL: (ChronologicalAura(),)}, _BATCH_50E_SOURCE),
        CardRule("TIME_703", {Hook.BATTLECRY: (EndangeredDodoBattlecry(),)}, _BATCH_50E_SOURCE),
        CardRule("TIME_704", {Hook.BATTLECRY: (HighborneMentorBattlecry(),)}, _BATCH_50E_SOURCE),
        CardRule("TIME_705", {Hook.BATTLECRY: (KronaBattlecry(),)}, _BATCH_50E_SOURCE),
        CardRule("TIME_707", {Hook.SPELL: (AlternateReality(),)}, _BATCH_50E_SOURCE),
        CardRule("TIME_710", {Hook.BATTLECRY: (TroubledDoubleCombo(),)}, _BATCH_50E_SOURCE),
        CardRule("TIME_711", {Hook.SPELL: (Flashback(),)}, _BATCH_50E_SOURCE),
        CardRule("TIME_712", {Hook.SPELL: (Dethrone(),)}, _BATCH_50E_SOURCE,
                 TargetSpec(TargetKind.ANY_MINION)),
        CardRule("TIME_716", {Hook.SPELL: (SlowMotion(),)}, _BATCH_50E_SOURCE),
        CardRule("TIME_730", {Hook.BATTLECRY: (
            OfferPastDiscover(card_type="MINION", race="BEAST", repeats=2,
                              after_pick="kaldorei_cultivator"),
        )}, _BATCH_50E_SOURCE),
        CardRule("TIME_857", {Hook.SPELL: (
            OfferPastDiscover(card_type="SPELL", spell_school="ARCANE", repeats=2,
                              after_pick="alter_time"),
        )}, _BATCH_50E_SOURCE),
        CardRule("TIME_859", {Hook.SPELL: (Anomalize(),)}, _BATCH_50E_SOURCE),
        CardRule("TIME_860", {Hook.BATTLECRY: (FacelessEnigmaBattlecry(),)}, _BATCH_50E_SOURCE),
        CardRule("TIME_861", {Hook.BATTLECRY: (TimelooperTokiBattlecry(),)}, _BATCH_50E_SOURCE),
        CardRule("TIME_870", {Hook.SPELL: (GladiatorialCombat(),)}, _BATCH_50E_SOURCE),
        CardRule("TIME_872", {Hook.BATTLECRY: (UndefeatedChampionBattlecry(),)}, _BATCH_50E_SOURCE),
        CardRule("TIME_873", {Hook.SPELL: (UnleashCrocolisks(),)}, _BATCH_50E_SOURCE),
        # ---- 50-card Standard tranche 50F -----------------------------
        # Cataclysm persistent/held-card effects and the Mending companion
        # and Silver Hand Recruit packages.  Engine-owned state is used for
        # effects that survive the source leaving play.
        CardRule("CATA_132", {Hook.BATTLECRY: (BroodwatcherBattlecry(),)}, _BATCH_50F_SOURCE),
        CardRule("CATA_136", {Hook.SPELL: (ShuffleLargeMinionsDoubled(),)}, _BATCH_50F_SOURCE),
        CardRule("CATA_180", {Hook.BATTLECRY: (SetNextMurlocHealthCost(),)}, _BATCH_50F_SOURCE),
        CardRule("CATA_186", {Hook.BATTLECRY: (AddToHand("CATA_186t", side="opponent"),)}, _BATCH_50F_SOURCE),
        CardRule("CATA_208", {}, _BATCH_50F_SOURCE),
        CardRule("CATA_216", {Hook.BATTLECRY: (GrantHealingBonus(),)}, _BATCH_50F_SOURCE),
        CardRule("CATA_305", {Hook.END_TURN: (EndTurnFullHealthGain(3),)}, _BATCH_50F_SOURCE),
        CardRule("CATA_452", {Hook.SPELL: (
            SummonFixedDragon(6, 6, "CATA_452t", "Spellweaver Dragon"),
        )}, _BATCH_50F_SOURCE, cost_modifier=CostByPlayerAttribute("spell_damage_dealt_this_turn")),
        CardRule("CATA_458", {Hook.BATTLECRY: (GrantHeldAndDeckSpellDamage(),)}, _BATCH_50F_SOURCE),
        CardRule("CATA_471", {Hook.SPELL: (GrantRandomCostDeathrattle(4),)}, _BATCH_50F_SOURCE),
        CardRule("CATA_473", {Hook.END_TURN: (NozdormuBronzeAspectEndTurn(),)}, _BATCH_50F_SOURCE),
        CardRule("CATA_474", {Hook.END_TURN: (
            AddRandomSpellSchoolDiscount("HOLY", 3),
        )}, _BATCH_50F_SOURCE),
        CardRule("CATA_475", {Hook.END_TURN: (DamageAllEnemies(2),)}, _BATCH_50F_SOURCE),
        CardRule("CATA_478", {Hook.END_TURN: (BronzeRedeemerEndTurn(),)}, _BATCH_50F_SOURCE),
        CardRule("CATA_483", {Hook.BATTLECRY: (SummonSourceCopyIfSpellDamage(),)}, _BATCH_50F_SOURCE),
        CardRule("CATA_487", {}, _BATCH_50F_SOURCE),
        CardRule("CATA_493", {Hook.BATTLECRY: (DukeOfBelowBattlecry(),)}, _BATCH_50F_SOURCE),
        CardRule("CATA_498", {Hook.SPELL: (RafaamsLastStand(),)}, _BATCH_50F_SOURCE),
        CardRule("CATA_499", {Hook.SPELL: (
            SummonRandomMinionWithCost(1), SummonRandomMinionWithCost(1),
        )}, _BATCH_50F_SOURCE),
        CardRule("CATA_528", {Hook.SPELL: (ArmSigilOfSeas(),)}, _BATCH_50F_SOURCE),
        CardRule("CATA_529", {}, _BATCH_50F_SOURCE,
                 cost_modifier=CostByPlayerAttribute("fel_spells_cast_this_game")),
        CardRule("CATA_551", {}, _BATCH_50F_SOURCE),
        CardRule("CATA_553", {Hook.BATTLECRY: (GrantDragonsRush(),)}, _BATCH_50F_SOURCE),
        CardRule("CATA_560", {Hook.SPELL: (SummonOneCostMinionsPlayed(),)}, _BATCH_50F_SOURCE),
        CardRule("CATA_564", {Hook.BATTLECRY: (AirSupportBattlecry(),)}, _BATCH_50F_SOURCE,
                 TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("CATA_566", {Hook.BATTLECRY: (
            OfferHandSelection("tolvir_discount"),
        )}, _BATCH_50F_SOURCE),
        CardRule("CATA_567", {Hook.SPELL: (Ascendance(),)}, _BATCH_50F_SOURCE),
        CardRule("CATA_610", {Hook.SPELL: (SetHandMinionDeathrattle(),)}, _BATCH_50F_SOURCE,
                 TargetSpec(TargetKind.ANY_MINION)),
        CardRule("CATA_614", {
            Hook.BATTLECRY: (ShadowedInformantBattlecry(),),
            Hook.START_TURN: (ShadowedInformantStartTurn(),),
        }, _BATCH_50F_SOURCE),
        CardRule("CATA_616", {}, _BATCH_50F_SOURCE,
                 cost_modifier=CostByPlayerAttribute("last_played_card_cost")),
        CardRule("CATA_697", {Hook.BATTLECRY: (
            OfferHandSelection("fel_copy", "fel_spell"),
        )}, _BATCH_50F_SOURCE),
        CardRule("CATA_699", {Hook.BATTLECRY: (DreadLeviathanBattlecry(),)}, _BATCH_50F_SOURCE,
                 TargetSpec(TargetKind.ENEMY_MINION)),
        CardRule("CATA_786", {Hook.AFTER_PLAY: (ChaosSupplicantAfterSpell(),)}, _BATCH_50F_SOURCE),
        CardRule("CATA_897", {
            Hook.BATTLECRY: (OfferHandSelection("gemstone_discard"),),
            Hook.DEATHRATTLE: (ReturnGemstoneDiscard(),),
        }, _BATCH_50F_SOURCE),
        CardRule("CATA_978", {Hook.SPELL: (SindragosasTriumph(),)}, _BATCH_50F_SOURCE,
                 TargetSpec(TargetKind.ANY_MINION)),
        CardRule("CATA_979", {Hook.BATTLECRY: (
            OfferHandSelection("split_spell", "spell"),
        )}, _BATCH_50F_SOURCE),
        CardRule("MEND_041", {Hook.BATTLECRY: (RefreshManaIfNoMinionLastTurn(),)}, _BATCH_50F_SOURCE),
        CardRule("MEND_045", {Hook.DEATHRATTLE: (AddRandomDragonDiscount(),)}, _BATCH_50F_SOURCE),
        CardRule("MEND_300", {Hook.SPELL: (
            SetAnimalCompanionUpgrade(cost_increase=1), Draw(),
        )}, _BATCH_50F_SOURCE),
        CardRule("MEND_301", {Hook.BATTLECRY: (
            OfferEffectChoice((
                # These labels are the three pre-replacement companions.
                # The result must nevertheless go through the canonical
                # companion event: Tame Pet / Migrating Elekk / Roam Free
                # replace *future Animal Companions* globally, including a
                # companion selected through Spiritspeaker.
                ("Huffer", (SummonSelectedAnimalCompanion("NEW1_032"),)),
                ("Leokk", (SummonSelectedAnimalCompanion("NEW1_033"),)),
                ("Misha", (SummonSelectedAnimalCompanion("NEW1_034"),)),
            )),
        )}, _BATCH_50F_SOURCE),
        CardRule("MEND_303", {Hook.BATTLECRY: (SetAnimalCompanionUpgrade(cost_increase=1),)}, _BATCH_50F_SOURCE),
        CardRule("MEND_304", {Hook.BATTLECRY: (SetAnimalCompanionUpgrade(extra_count=1),)}, _BATCH_50F_SOURCE),
        CardRule("MEND_305", {Hook.SPELL: (NurturingNature(),)}, _BATCH_50F_SOURCE,
                 TargetSpec(TargetKind.FRIENDLY_BEAST)),
        CardRule("MEND_800", {Hook.DEATHRATTLE: (AddRecruitStats(attack=1),)}, _BATCH_50F_SOURCE),
        CardRule("MEND_801", {}, _BATCH_50F_SOURCE),
        CardRule("MEND_802", {Hook.SPELL: (SummonRecruit(2, divine_shield=True),)}, _BATCH_50F_SOURCE),
        CardRule("MEND_803", {Hook.BATTLECRY: (AddRecruitStats(attack=1, health=1),)}, _BATCH_50F_SOURCE),
        CardRule("MEND_804", {Hook.BATTLECRY: (AratorBattlecry(),)}, _BATCH_50F_SOURCE),
        CardRule("MEND_805", {Hook.SPELL: (
            CopyFriendlyDeathsThisTurn(attack=3, health=3),
        )}, _BATCH_50F_SOURCE),
        CardRule("MEND_900", {Hook.SPELL: (SummonRecruit(4, add_to_hand=True),)}, _BATCH_50F_SOURCE),
        # ---- 50-card Standard tranche 50G -----------------------------
        CardRule("CAP_006", {Hook.SPELL: (TricksOfTheTrade(),)}, _BATCH_50G_SOURCE,
                 TargetSpec(TargetKind.ANY_CHARACTER)),
        CardRule("CAP_101", {Hook.SPELL: (
            DealRandomEnemy(2), PassTemporaryPlayEffect("CAP_101", "pirate"),
        )}, _BATCH_50G_SOURCE),
        CardRule("CAP_400", {Hook.DEATHRATTLE: (ShuffleImpFormants(),)}, _BATCH_50G_SOURCE),
        CardRule("CAP_802", {Hook.SPELL: (SummonGhostAndPassEffect(),)}, _BATCH_50G_SOURCE),
        CardRule("CAP_804", {Hook.BATTLECRY: (GrantRebornOrCopy(),)}, _BATCH_50G_SOURCE,
                 TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("CAP_805", {Hook.SPELL: (SlimeEm(),)}, _BATCH_50G_SOURCE),
        CardRule("CAP_805t", {Hook.SPELL: (ResummonSlime(),)}, _BATCH_50G_SOURCE),
        CardRule("CAP_806", {Hook.BATTLECRY: (ResurrectRebornAndFight(),)}, _BATCH_50G_SOURCE),
        CardRule("CATA_480", {Hook.SPELL: (SetEndTurnEffectsTwice(),)}, _BATCH_50G_SOURCE),
        CardRule("CATA_563", {
            Hook.BATTLECRY: (AbsorbSpell(),),
        }, _BATCH_50G_SOURCE),
        CardRule("CORE_AT_062", {Hook.SPELL: (SummonWebspinners(),)}, _BATCH_50G_SOURCE),
        CardRule("CORE_BAR_313", {Hook.BATTLECRY: (PriestOfAnshe(),)}, _BATCH_50G_SOURCE),
        CardRule("CORE_BOT_256", {Hook.BATTLECRY: (SummonRandomByHandSize(),)}, _BATCH_50G_SOURCE),
        CardRule("CORE_ETC_111", {Hook.END_TURN: (TopdeckRandomSpellForOpponent(),)}, _BATCH_50G_SOURCE),
        CardRule("CORE_ETC_523", {}, _BATCH_50G_SOURCE),
        CardRule("CORE_SCH_605", {}, _BATCH_50G_SOURCE),
        CardRule("CORE_SW_047", {}, _BATCH_50G_SOURCE),
        CardRule("CORE_WON_350", {Hook.SPELL: (OfferTauntDiscoverBuff(),)}, _BATCH_50G_SOURCE),
        CardRule("DINO_137", {Hook.BATTLECRY: (DiscountAdjacentHandCards(),)}, _BATCH_50G_SOURCE),
        CardRule("DINO_402", {Hook.SPELL: (SetFriendlyOneOneAndFillCopies(),)}, _BATCH_50G_SOURCE,
                 TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("DINO_415", {Hook.SPELL: (
            DiscoverAndSummon(min_cost=5, mechanic="DEATHRATTLE", after_pick="summon_discover"),
        )}, _BATCH_50G_SOURCE),
        CardRule("DINO_424", {Hook.SPELL: (
            DiscoverAndSummon(legendary=True, after_pick="legendary_ten"),
        )}, _BATCH_50G_SOURCE),
        CardRule("DINO_426", {Hook.SPELL: (
            DiscoverAndSummon(cost=3, after_pick="copy_two_three"),
        )}, _BATCH_50G_SOURCE),
        CardRule("DINO_427", {Hook.BATTLECRY: (RandomMaskOtherClass(),)}, _BATCH_50G_SOURCE),
        CardRule("DINO_428", {Hook.SPELL: (BehemothMask(),)}, _BATCH_50G_SOURCE,
                 TargetSpec(TargetKind.ANY_MINION)),
        CardRule("DINO_429", {Hook.SPELL: (SheepMask(),)}, _BATCH_50G_SOURCE,
                 TargetSpec(TargetKind.ANY_MINION)),
        CardRule("DINO_430", {Hook.BATTLECRY: (BeastSpeakerTaka(),)}, _BATCH_50G_SOURCE),
        CardRule("EDR_014", {Hook.BATTLECRY: (AttackRandomEnemyMinionsIfCheap(),)}, _BATCH_50G_SOURCE),
        CardRule("EDR_460", {Hook.SPELL: (NewMoonDamage(),)}, _BATCH_50G_SOURCE,
                 TargetSpec(TargetKind.ANY_MINION)),
        CardRule("EDR_461", {Hook.SPELL: (RitualNewMoon(),)}, _BATCH_50G_SOURCE),
        CardRule("EDR_464", {Hook.BATTLECRY: (SetNextThreeSpellsTwice(),)}, _BATCH_50G_SOURCE),
        CardRule("EDR_472", {Hook.BATTLECRY: (WeaverOfCycle(),)}, _BATCH_50G_SOURCE),
        CardRule("EDR_477", {}, _BATCH_50G_SOURCE,
                 cost_modifier=CostByPlayerAttribute("hero_powers_used_this_game")),
        CardRule("EDR_482", {Hook.SPELL: (RottenApple(),)}, _BATCH_50G_SOURCE),
        CardRule("EDR_483", {Hook.SPELL: (FracturedPower(),)}, _BATCH_50G_SOURCE),
        CardRule("EDR_484", {}, _BATCH_50G_SOURCE),
        CardRule("EDR_495", {Hook.DEATHRATTLE: (RandomHandMinionAttackReduction(),)}, _BATCH_50G_SOURCE),
        CardRule("EDR_530", {Hook.END_TURN: (RandomSchoolSpell("NATURE"),)}, _BATCH_50G_SOURCE),
        CardRule("EDR_853", {Hook.AFTER_PLAY: (SummonAnimalCompanion(),)}, _BATCH_50G_SOURCE),
        CardRule("END_002", {Hook.DEATHRATTLE: (DaggerOrWeaponBuff(),)}, _BATCH_50G_SOURCE),
        CardRule("END_006", {Hook.BATTLECRY: (ChronikarBattlecry(),)}, _BATCH_50G_SOURCE),
        CardRule("END_009", {Hook.SPELL: (SplinteredReality(),)}, _BATCH_50G_SOURCE),
        CardRule("END_012", {Hook.BATTLECRY: (InfinityWeaponBattlecry(),)}, _BATCH_50G_SOURCE),
        CardRule("END_013", {Hook.BATTLECRY: (
            OfferFilteredDiscover(card_type="MINION", cost=1, dark_gift=True),
        )}, _BATCH_50G_SOURCE),
        CardRule("END_018", {
            Hook.BATTLECRY: (InfiniteAcolyte(),),
        }, _BATCH_50G_SOURCE),
        CardRule("END_029", {Hook.END_TURN: (RandomSchoolSpell("SHADOW"),)}, _BATCH_50G_SOURCE),
        CardRule("END_032", {Hook.BATTLECRY: (WingedAberrationCombo(),)}, _BATCH_50G_SOURCE),
        CardRule("FIR_778", {Hook.DEATHRATTLE: (SetDeathrattleAllEnemies(9),)}, _BATCH_50G_SOURCE),
        CardRule("FIR_913", {Hook.AFTER_PLAY: (InfernoHeraldAfterSpell(),)}, _BATCH_50G_SOURCE),
        CardRule("FIR_955", {}, _BATCH_50G_SOURCE),
        # ---- 50-card Standard tranche 50H -----------------------------
        CardRule("CAP_401", {Hook.BATTLECRY: (MoveImpFormantToEnemyTop(),)}, _BATCH_50H_SOURCE),
        CardRule("CAP_402", {Hook.SPELL: (FollowEvidence(),)}, _BATCH_50H_SOURCE),
        CardRule("CAP_403", {Hook.SPELL: (FrameJob(),)}, _BATCH_50H_SOURCE),
        CardRule("CAP_406", {Hook.BATTLECRY: (OtherMinionsGainCostDeathrattle(),)}, _BATCH_50H_SOURCE),
        CardRule("CORE_AV_107", {Hook.SPELL: (DiscoverSummonFreeze(8),)}, _BATCH_50H_SOURCE),
        CardRule("CORE_CATA_006", {Hook.BATTLECRY: (OtherMinionsGainCostDeathrattle(),)}, _BATCH_50H_SOURCE),
        CardRule("CORE_GIL_577", {}, _BATCH_50H_SOURCE),
        CardRule("CORE_TRL_345", {Hook.BATTLECRY: (ReturnLastTurnSpells(),)}, _BATCH_50H_SOURCE),
        CardRule("CORE_ULD_152", {}, _BATCH_50H_SOURCE),
        CardRule("EDR_455", {Hook.SPELL: (DiscoverDeadDragonAndResummon(),)}, _BATCH_50H_SOURCE),
        CardRule("FIR_911", {Hook.SPELL: (SmolderingDraw(),)}, _BATCH_50H_SOURCE),
        CardRule("FIR_914", {Hook.SPELL: (SmolderingBuff(),)}, _BATCH_50H_SOURCE,
                 TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("FIR_916", {Hook.SPELL: (SmolderingEnemyBoardDamage(),)}, _BATCH_50H_SOURCE),
        CardRule("FIR_918", {Hook.SPELL: (LightNewMoon(),)}, _BATCH_50H_SOURCE,
                 TargetSpec(TargetKind.ANY_MINION)),
        CardRule("FIR_927", {Hook.BATTLECRY: (DiscoverFiveCostAndTemporaryMana(),)}, _BATCH_50H_SOURCE),
        CardRule("FIR_940", {Hook.BATTLECRY: (DiscountHandIfUniqueCosts(2),)}, _BATCH_50H_SOURCE),
        CardRule("FIR_952", {Hook.BATTLECRY: (DiscoverFelAndDiscountHand(),)}, _BATCH_50H_SOURCE),
        CardRule("JAIL_030", {Hook.AFTER_ATTACK: (EscapeAfterAttack(),)}, _BATCH_50H_SOURCE),
        CardRule("JAIL_123", {Hook.BATTLECRY: (OfferHighCostSpellThatCastsTwice(),)}, _BATCH_50H_SOURCE),
        CardRule("JAIL_125", {Hook.SPELL: (FreezeActionTarget(), AddRandomFilteredCards(1, card_type="SPELL", spell_school="FROST"))}, _BATCH_50H_SOURCE,
                 TargetSpec(TargetKind.ENEMY_CHARACTER)),
        CardRule("JAIL_204", {}, _BATCH_50H_SOURCE, cost_modifier=CostIfNoMinionsOnBattlefield(2)),
        CardRule("JAIL_225", {Hook.SPELL: (DamageTargetShuffleTwoCostCopyIfKilled(3),)}, _BATCH_50H_SOURCE,
                 TargetSpec(TargetKind.ENEMY_MINION)),
        CardRule("JAIL_312", {Hook.SPELL: (GetThreeArcaneMissiles(),)}, _BATCH_50H_SOURCE),
        CardRule("JAIL_327", {Hook.SPELL: (SetReinforcementAura(),)}, _BATCH_50H_SOURCE),
        CardRule("JAIL_387", {Hook.SPELL: (BuffHandMinionsWithLegendaryBonus(),)}, _BATCH_50H_SOURCE),
        CardRule("JAIL_436", {Hook.SPELL: (WidowBite(1, 1, "JAIL_436t"),)}, _BATCH_50H_SOURCE),
        CardRule("JAIL_436t", {Hook.SPELL: (WidowBite(2, 2, "JAIL_436t2"),)}, _BATCH_50H_SOURCE),
        CardRule("JAIL_436t2", {Hook.SPELL: (WidowBite(4, 4),)}, _BATCH_50H_SOURCE),
        CardRule("JAIL_447", {Hook.DEATHRATTLE: (AddDetectiveClothes(),)}, _BATCH_50H_SOURCE),
        CardRule("JAIL_447t", {Hook.SPELL: (BuffActionTargetAndRush(4, 4),)}, _BATCH_50H_SOURCE,
                 TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("JAIL_448", {Hook.DEATHRATTLE: (AddLegendaryOneOneCopies(),)}, _BATCH_50H_SOURCE),
        CardRule("JAIL_474", {Hook.BATTLECRY: (AddRandomEightCostMinionsDiscountByTwoCostPlays(),)}, _BATCH_50H_SOURCE),
        CardRule("JAIL_507", {Hook.BATTLECRY: (SpitefulChef(),)}, _BATCH_50H_SOURCE),
        CardRule("JAIL_515", {Hook.SPELL: (ShadowRounds(),)}, _BATCH_50H_SOURCE,
                 TargetSpec(TargetKind.ENEMY_MINION)),
        CardRule("JAIL_516", {Hook.BATTLECRY: (SummonDeckMinionsWithRush(2, 2),)}, _BATCH_50H_SOURCE),
        CardRule("JAIL_706", {Hook.SPELL: (AddRandomSpellsDiscounted(4, 2, 2),)}, _BATCH_50H_SOURCE),
        CardRule("JAIL_733", {Hook.DEATHRATTLE: (AddVoidSoul(),)}, _BATCH_50H_SOURCE),
        CardRule("JAIL_734", {Hook.BATTLECRY: (DiscoverDeckCardOrGainStats(),)}, _BATCH_50H_SOURCE),
        CardRule("JAIL_805", {Hook.SPELL: (Stormfury(),)}, _BATCH_50H_SOURCE),
        CardRule("JAIL_805t", {Hook.BATTLECRY: (Stormfury(),)}, _BATCH_50H_SOURCE),
        CardRule("JAIL_806", {Hook.BATTLECRY: (AddRandomHighCostSpell(),)}, _BATCH_50H_SOURCE),
        CardRule("JAIL_876", {Hook.SPELL: (GrantDeathrattleRandomMinion(4, 2),)}, _BATCH_50H_SOURCE,
                 TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("JAIL_878", {Hook.DEATHRATTLE: (SummonRandomMinionMatching(1, "DEATHRATTLE"),)}, _BATCH_50H_SOURCE),
        CardRule("JAIL_879", {Hook.SPELL: (Tripwire("beast"),)}, _BATCH_50H_SOURCE),
        CardRule("JAIL_879t", {Hook.SPELL: (SummonRandomBeast(5),)}, _BATCH_50H_SOURCE),
        CardRule("JAIL_881", {Hook.SPELL: (Tripwire("arcane"),)}, _BATCH_50H_SOURCE),
        CardRule("JAIL_881t", {Hook.SPELL: (ArcaneTripwireDamage(4),)}, _BATCH_50H_SOURCE),
        CardRule("JAIL_883", {Hook.END_TURN: (GainRebornAtEndTurn(),)}, _BATCH_50H_SOURCE),
        CardRule("JAIL_940", {Hook.SPELL: (TriggerDeathrattleOfRandomDead(),)}, _BATCH_50H_SOURCE),
        CardRule("JAIL_974", {Hook.DEATHRATTLE: (CapturedArchmageDeathrattle(),)}, _BATCH_50H_SOURCE),
        CardRule("JAIL_986", {Hook.BATTLECRY: (RandomPlayableTemporarySpell(),)}, _BATCH_50H_SOURCE),
        CardRule("TLC_234", {Hook.DEATHRATTLE: (SummonTokenDeathrattle("TLC_234t"),)}, _BATCH_50H_SOURCE),
        CardRule("TLC_234t", {Hook.DEATHRATTLE: (SummonTokenDeathrattle("TLC_234"),)}, _BATCH_50H_SOURCE),
        CardRule("TLC_237", {Hook.DEATHRATTLE: (SummonTokenDeathrattle("TLC_237t", 4),)}, _BATCH_50H_SOURCE),
        CardRule("TLC_244", {Hook.DEATHRATTLE: (DiscountRandomOpponentHandMinion(2),)}, _BATCH_50H_SOURCE),
        CardRule("TLC_245", {Hook.BATTLECRY: (AncientRaptorChoice(),)}, _BATCH_50H_SOURCE),
        CardRule("TLC_256", {Hook.AFTER_PLAY: (ThresherAfterSpell(),)}, _BATCH_50H_SOURCE),
        # ---- 50-card Standard tranche 50I -----------------------------
        CardRule("CORE_BAR_812", {}, _BATCH_50I_SOURCE),
        CardRule("DINO_414", {Hook.SPELL: (OfferTransformIntoDifferentMinion(),)}, _BATCH_50I_SOURCE,
                 TargetSpec(TargetKind.ANY_MINION)),
        CardRule("TLC_106", {Hook.BATTLECRY: (TriggerRandomFriendlyDeadDeathrattles(5),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_109", {Hook.BATTLECRY: (DestroyTopDeckDiscoverSameRarity(),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_230", {Hook.SPELL: (SummonTokensAttackActionTarget("TLC_230t", 4),)}, _BATCH_50I_SOURCE,
                 TargetSpec(TargetKind.ANY_MINION)),
        CardRule("TLC_232", {Hook.SPELL: (QueueStartTurnTokenSummon("TLC_237t", 3),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_233", {Hook.BATTLECRY: (BuffOtherLowAttackMinionsTaunt(1, 1, 2),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_247", {Hook.AFTER_ATTACK: (CopyKilledMinionToHand(),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_250", {Hook.BATTLECRY: (BlockEnemyHeroHealing(),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_252", {Hook.BATTLECRY: (DestroyFriendlyMakeBones(),)}, _BATCH_50I_SOURCE,
                 TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("TLC_254", {Hook.END_TURN: (BuffEachDifferentTribe(),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_257", {Hook.BATTLECRY: (SetMinionCostForGame(5),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_334", {Hook.SPELL: (OfferHighCostSpellDiscounted(8, 1),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_364", {Hook.SPELL: (DiscountNonStartingHandCards(1),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_427", {Hook.BATTLECRY: (AddSmallRock(),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_430", {Hook.END_TURN: (ReplayRandomSchoolSpellThisTurn("HOLY"),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_438", {Hook.BATTLECRY: (CastRandomDeckSpellAtSource(2),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_441", {Hook.SPELL: (BuffTargetAndSameTribe(1, 2),)}, _BATCH_50I_SOURCE,
                 TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("TLC_443", {Hook.DEATHRATTLE: (Summon("TLC_443t"),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_444", {Hook.SPELL: (GrantRandomBonusEffects(3),)}, _BATCH_50I_SOURCE,
                 TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("TLC_450", {Hook.BATTLECRY: (SetNextTemporaryDiscount(2),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_452", {Hook.START_TURN: (TitanographerAbility(),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_462", {Hook.SPELL: (SummonRandomMinionByDiscoverState(),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_465", {Hook.DEATHRATTLE: (PropagateRandomBonusDeathrattle(),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_467", {Hook.DEATHRATTLE: (AddRandomSpellsCostHealth(2, "FEL"),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_469", {Hook.DEATHRATTLE: (AddTemporaryRandomMinions(2, 2),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_477", {Hook.SPELL: (BuffActionTarget(4, 4), GrantDeathrattleRandomMinion(4, 1))}, _BATCH_50I_SOURCE,
                 TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("TLC_479", {Hook.DEATHRATTLE: (SummonRandomFelBeast(),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_483", {}, _BATCH_50I_SOURCE),
        CardRule("TLC_516", {Hook.BATTLECRY: (OfferOtherClassWeapon(),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_517", {Hook.SPELL: (DamagePerShuffle(1),)}, _BATCH_50I_SOURCE,
                 TargetSpec(TargetKind.ENEMY_MINION)),
        CardRule("TLC_518", {Hook.SPELL: (ShuffleNinjas(3),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_520", {}, _BATCH_50I_SOURCE, cost_modifier=CostMinusShuffledCards()),
        CardRule("TLC_521", {Hook.BATTLECRY: (OfferEnemyDeckCardTop(),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_601", {Hook.SPELL: (SpendArmorDamageAllMinions(5),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_620", {Hook.SPELL: (GainArmorDamageTarget(3),)}, _BATCH_50I_SOURCE,
                 TargetSpec(TargetKind.ENEMY_MINION)),
        CardRule("TLC_622", {Hook.SPELL: (SummonSecurity(2),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_622t", {Hook.AFTER_DAMAGE: (GainAttackAfterDamage(1),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_810", {Hook.BATTLECRY: (SummonDeckDeathrattlesAndFight(2),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_811", {Hook.OTHER_FRIENDLY_ATTACK: (SetAttackerHealthToSource(),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_814", {Hook.DEATHRATTLE: (AddRandomSchoolSpells(("HOLY", "SHADOW")),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_818", {Hook.SPELL: (ResurrectCostsWithReborn((1, 2, 3)),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_819", {}, _BATCH_50I_SOURCE, cost_modifier=CostIfHolyAndShadowThisTurn(1)),
        CardRule("TLC_821", {Hook.AFTER_HEAL_ENEMY: (AttackEnemyHealedTarget(),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_822", {Hook.END_TURN: (DiscountRandomHandRaceEndTurn("BEAST", 1),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_826", {Hook.SPELL: (ShuffleRaptors(10),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_827", {Hook.END_TURN: (GrowSelfEverywhere(1),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_831", {Hook.DEATHRATTLE: (SummonPterrordaxAndStealHealth(),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_836", {Hook.AFTER_PLAY: (DoubleOneCostPlays(),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_840", {Hook.AFTER_ATTACK: (DealEnemyHeroAfterAttack(2),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_841", {Hook.BATTLECRY: (JarHandMinions(),)}, _BATCH_50I_SOURCE),
        CardRule("TLC_829t", {Hook.SPELL: (BuffTargetFromPayload(),)}, _BATCH_50I_SOURCE,
                 TargetSpec(TargetKind.ANY_MINION)),
        CardRule("GILA_500p2t", {Hook.SPELL: (DamageTargetFromPayload(),)}, _BATCH_50I_SOURCE,
                 TargetSpec(TargetKind.ANY_CHARACTER)),
        CardRule("FIR_960", {Hook.BATTLECRY: (CopyLowestCostBeast(),)}, _BATCH_50G_SOURCE),
        # Final 48 collectible Standard cards.  Each card is declared here
        # (rather than only admitted to the card vocabulary) so it follows
        # normal target validation, cloning and rule-source auditing.
        CardRule("CAP_405", {Hook.BATTLECRY: (ArmShamTrial(),)}, _FINAL_48_SOURCE),
        CardRule("CAP_004a", {}, _AUXILIARY_TOKEN_SOURCE),
        CardRule("CAP_004b", {}, _AUXILIARY_TOKEN_SOURCE),
        CardRule("CAP_405t1", {Hook.SPELL: (ForceEachMinionToAttackAnother(),)},
                 _AUXILIARY_TOKEN_SOURCE),
        CardRule("CAP_405t2", {Hook.SPELL: (TakeRandomEnemyMinion(),)},
                 _AUXILIARY_TOKEN_SOURCE),
        CardRule("CAP_405t3", {Hook.SPELL: (StealEnemyHandCards(2),)},
                 _AUXILIARY_TOKEN_SOURCE),
        CardRule("CAP_405t5", {Hook.SPELL: (BuffMinionsInHandAndBoard(3, 3),)},
                 _AUXILIARY_TOKEN_SOURCE),
        CardRule("CAP_405t6", {Hook.SPELL: (SummonRandomMinionWithCost(3, count=3),)},
                 _AUXILIARY_TOKEN_SOURCE),
        CardRule("CAP_405t7", {Hook.SPELL: (ReduceHandMinionCosts(2),)},
                 _AUXILIARY_TOKEN_SOURCE),
        CardRule("CAP_405t8", {Hook.SPELL: (HealHero(12),)},
                 _AUXILIARY_TOKEN_SOURCE),
        CardRule("CAP_405t9", {Hook.SPELL: (SummonNamedMinion("CORE_LOOT_368"),)},
                 _AUXILIARY_TOKEN_SOURCE),
        # The three trial labels are surfaced as selectable entities by the
        # client. Their actual progression is stored on CAP_405's trial state.
        *tuple(CardRule(card_id, {}, _AUXILIARY_TOKEN_SOURCE) for card_id in (
            "CAP_405tb1", "CAP_405tb1b", "CAP_405tb2", "CAP_405tb2b",
            "CAP_405tb3", "CAP_405tb3b",
        )),
        CardRule("JAIL_201a", {Hook.SPELL: (GainHeroAttack(2),)}, _AUXILIARY_TOKEN_SOURCE),
        CardRule("JAIL_201b", {Hook.SPELL: (AddRandomExecutableClassCard("DRUID"),)},
                 _AUXILIARY_TOKEN_SOURCE),
        CardRule("JAIL_319t", {}, _AUXILIARY_TOKEN_SOURCE),
        CardRule("JAIL_386t", {}, _AUXILIARY_TOKEN_SOURCE),
        CardRule("JAIL_443t", {}, _AUXILIARY_TOKEN_SOURCE),
        CardRule("EDR_416t", {}, _AUXILIARY_TOKEN_SOURCE),
        CardRule("EDR_463a", {Hook.SPELL: (DestroyActionTargetIfAttackAtMost(3),)},
                 _AUXILIARY_TOKEN_SOURCE, TargetSpec(TargetKind.ENEMY_MINION)),
        CardRule("EDR_463b", {Hook.SPELL: (SummonRandomExecutableMinion(cost=2),)},
                 _AUXILIARY_TOKEN_SOURCE),
        CardRule("EDR_490t", {}, _AUXILIARY_TOKEN_SOURCE),
        CardRule("EDR_445pt3", {}, _AUXILIARY_TOKEN_SOURCE),
        CardRule("JAIL_504t2", {Hook.SPELL: (GainMana(1), DamageRandomEnemyMinion(2),)},
                 _AUXILIARY_TOKEN_SOURCE),
        CardRule("JAIL_803t", {Hook.BATTLECRY: (FreezeActionTarget(), Draw(2),)},
                 _AUXILIARY_TOKEN_SOURCE, TargetSpec(TargetKind.ENEMY_MINION)),
        CardRule("JAIL_EVENT_100", {Hook.BATTLECRY: (OfferWatfinDiscover(),)},
                 _EVENT_BLOCKER_SOURCE),
        CardRule("TLC_EVENT_402", {Hook.DEATHRATTLE: (DestroyAllMinions(), ResolveDeaths(),)},
                 _EVENT_BLOCKER_SOURCE),
        CardRule("JAIL_EVENT_101", {Hook.SPELL: (SoulImmolationSpell(),)},
                 _EVENT_BLOCKER_SOURCE),
        CardRule("JAIL_EVENT_102", {Hook.SPELL: (DesperateBribeSpell(),)},
                 _EVENT_BLOCKER_SOURCE),
        CardRule("CATA_EVENT_402", {Hook.SPELL: (DeadlyBribeSpell(),)},
                 _EVENT_BLOCKER_SOURCE, TargetSpec(TargetKind.ENEMY_MINION)),
        CardRule("JAIL_EVENT_101hp", {Hook.HERO_POWER: (CollapsingStarHeroPower(),)},
                 _AUXILIARY_TOKEN_SOURCE),
        *tuple(CardRule(card_id, {}, _AUXILIARY_TOKEN_SOURCE) for card_id in (
            "EDR_102t", "EDR_454t", "EDR_517A", "EDR_517B", "EDR_818t",
            "END_017t", "FIR_951t2", "FIR_951t3", "FIR_951t4",
            "JAIL_442a", "JAIL_442b", "JAIL_452a", "JAIL_452b", "JAIL_455a", "JAIL_455b",
            "JAIL_458t1", "JAIL_458t2", "JAIL_458t3", "JAIL_458t4", "JAIL_461a", "JAIL_461b",
            "JAIL_504t", "JAIL_504t3", "JAIL_504t3p", "JAIL_504t5",
            "JAIL_800hp1", "JAIL_800hp2", "JAIL_887t2",
        )),
        # These generated entities are resolved by the engine-owned Map and
        # quest lifecycles (custom location effects, quest counters and
        # deathrattle follow-ups); an empty rule map prevents a second,
        # conflicting generic script from firing.
        *tuple(CardRule(card_id, {}, _AUXILIARY_TOKEN_SOURCE) for card_id in (
            "TLC_100t11", "TLC_100t12", "TLC_100t13", "TLC_100t14", "TLC_100t15",
            "TLC_100t16", "TLC_100t17", "TLC_100t21", "TLC_100t22", "TLC_100t23",
            "TLC_100t24", "TLC_100t25", "TLC_100t26", "TLC_100t27", "TLC_100t31",
            "TLC_100t32", "TLC_100t33", "TLC_100t34", "TLC_100t35", "TLC_100t36",
            "TLC_100t37", "TLC_229t14", "TLC_239t", "TLC_426t", "TLC_433t",
            "TLC_433t2", "TLC_446t1",
        )),
        *tuple(CardRule(card_id, {}, _AUXILIARY_TOKEN_SOURCE) for card_id in (
            "TLC_452t1", "TLC_452t2", "TLC_452t3", "TLC_452t4", "TLC_452t5",
            "TLC_452t6", "TLC_452t7", "TLC_452t13", "TLC_452t14", "TLC_452t15",
            "TLC_452t16", "TLC_452t17", "TLC_452t18", "TLC_452t19", "TLC_452t20",
            "TLC_452t21", "TLC_452t22", "TLC_452t23", "TLC_452t24", "TLC_452t26",
            "TLC_452t27", "TLC_452t28", "TLC_452t29", "TLC_452t30", "TLC_452t31",
            "TLC_452t32", "TLC_452t33", "TLC_452t34", "TLC_452t35",
        )),
        *tuple(CardRule(card_id, {}, _AUXILIARY_TOKEN_SOURCE) for card_id in (
            "TLC_452t8", "TLC_452t9", "TLC_460t", "TLC_513hp", "TLC_513t",
            "TLC_602t", "TLC_631t", "TLC_817t", "TLC_817t2", "TLC_817t3",
            "TLC_817t4", "TLC_817t5", "TLC_830t", "TLC_841t",
        )),
        CardRule("RLK_907t", {Hook.DEATHRATTLE: (DamageRandomEnemyCharacters(2, 1),)},
                 _AUXILIARY_TOKEN_SOURCE),
        *tuple(CardRule(card_id, {}, _AUXILIARY_TOKEN_SOURCE) for card_id in (
            "EDR_259e1", "RLK_008t", "RLK_039t", "RLK_061t", "RLK_085t", "RLK_226t",
        )),
        CardRule("CATA_213", {Hook.BATTLECRY: (SplitHundredStatsIfStartingCosts(),)}, _FINAL_48_SOURCE),
        CardRule("CATA_307", {Hook.BATTLECRY: (SetHealthAndArmFullHealDamage(15, 15),)}, _FINAL_48_SOURCE),
        CardRule("CATA_470", {Hook.BATTLECRY: (CraftUndeadDragon(),)}, _FINAL_48_SOURCE),
        CardRule("CATA_621", {Hook.BATTLECRY: (AddRandomPaladinAura(),)}, _FINAL_48_SOURCE),
        CardRule("CORE_CFM_670", {}, _FINAL_48_SOURCE),
        CardRule("CORE_DAL_575", {}, _FINAL_48_SOURCE),
        CardRule("CORE_WON_145", {Hook.BATTLECRY: (OpenStandardPackAndPlay(),)}, _FINAL_48_SOURCE),
        CardRule("EDR_031", {Hook.END_TURN: (PlayTopDeckCards(3),)}, _FINAL_48_SOURCE),
        CardRule("EDR_209", {Hook.BATTLECRY: (ChooseThriceCenarius(),)}, _FINAL_48_SOURCE),
        CardRule("EDR_232", {Hook.SPELL: (ShuffleAllMinionsRandomly(),)}, _FINAL_48_SOURCE),
        CardRule("EDR_238", {Hook.BATTLECRY: (ResurrectDistinctHighCost(),)}, _FINAL_48_SOURCE),
        CardRule("EDR_259", {Hook.BATTLECRY: (CastHighestHandSpellAsAura(),)}, _FINAL_48_SOURCE),
        CardRule("EDR_261", {Hook.SPELL: (BuffActionTarget(2, 2), GrantDeathrattleBuffAllFriendly(2, 2))}, _FINAL_48_SOURCE,
                 TargetSpec(TargetKind.FRIENDLY_MINION)),
        CardRule("EDR_430", {Hook.BATTLECRY: (DealTwentyIfFriendlyDeaths(),)}, _FINAL_48_SOURCE),
        CardRule("EDR_489", {Hook.BATTLECRY: (ArmOpponentHealthCost(),)}, _FINAL_48_SOURCE),
        CardRule("EDR_491", {Hook.BATTLECRY: (GainDeadDeathrattleMarkers(),)}, _FINAL_48_SOURCE),
        CardRule("EDR_494", {Hook.END_TURN: (EatDeckMinionGainStats(),)}, _FINAL_48_SOURCE),
        CardRule("EDR_517", {Hook.BATTLECRY: (DiscoverSpellKeepOrTopdeckEnemy(),)}, _FINAL_48_SOURCE),
        CardRule("EDR_522", {Hook.SPELL: (OpponentDrawCopies(2),)}, _FINAL_48_SOURCE),
        CardRule("EDR_526", {Hook.BATTLECRY: (TrapRandomEnemyHandCard(),)}, _FINAL_48_SOURCE),
        CardRule("EDR_527", {Hook.BATTLECRY: (FillHandEnemyDeckCopies(),)}, _FINAL_48_SOURCE),
        CardRule("EDR_781", {}, _FINAL_48_SOURCE),
        CardRule("EDR_812", {Hook.BATTLECRY: (EquipRunebladeBonus(),)}, _FINAL_48_SOURCE),
        CardRule("EDR_819", {Hook.BATTLECRY: (AttackAllOtherMinions(),)}, _FINAL_48_SOURCE),
        CardRule("EDR_873", {Hook.BATTLECRY: (TransformNeutralDeckToDruid(),)}, _FINAL_48_SOURCE),
        CardRule("EDR_895", {Hook.BATTLECRY: (StartLunarCycle(),)}, _FINAL_48_SOURCE),
        CardRule("JAIL_101", {Hook.BATTLECRY: (StealBonusEffects(),)}, _FINAL_48_SOURCE,
                 TargetSpec(TargetKind.ENEMY_MINION)),
        CardRule("JAIL_122", {Hook.AFTER_PLAY: (SummonRandomMinionMatchingSpellCost(),)}, _FINAL_48_SOURCE),
        CardRule("JAIL_205", {Hook.END_TURN: (StealEnemyHandCardsEnteredThisTurn(),)}, _FINAL_48_SOURCE),
        CardRule("JAIL_303", {Hook.BATTLECRY: (OfferEnemyHandDiscardOnDeath(),)}, _FINAL_48_SOURCE),
        CardRule("JAIL_313", {Hook.BATTLECRY: (TransformHandCardToCostPlusSpell(),)}, _FINAL_48_SOURCE),
        CardRule("JAIL_315", {}, _FINAL_48_SOURCE),
        CardRule("JAIL_330", {}, _FINAL_48_SOURCE),
        CardRule("JAIL_434", {Hook.DEATHRATTLE: (DiscountOpponentCopies(1),)}, _FINAL_48_SOURCE),
        CardRule("JAIL_470", {Hook.BATTLECRY: (ShootRandomEnemy(),)}, _FINAL_48_SOURCE),
        CardRule("JAIL_500", {Hook.SPELL: (ReplayOtherSpellsAndEndTurn(),)}, _FINAL_48_SOURCE),
        CardRule("JAIL_802", {Hook.AFTER_PLAY: (BuffPlayedBattlecryMinion(),)}, _FINAL_48_SOURCE),
        CardRule("JAIL_861", {Hook.SPELL: (OfferChooseOneAndCopyEnemy(),)}, _FINAL_48_SOURCE),
        CardRule("MEND_100", {Hook.BATTLECRY: (AddBulb(),)}, _FINAL_48_SOURCE),
        CardRule("MEND_307", {Hook.SPELL: (SetAnimalCompanionUpgrade(2), SummonAnimalCompanion())}, _FINAL_48_SOURCE),
        CardRule("MEND_505", {Hook.SPELL: (GrantAllLeylinesAndUpgrade(),)}, _FINAL_48_SOURCE),
        CardRule("TIME_030", {Hook.SPELL: (SplitRandomHandMinion(),)}, _FINAL_48_SOURCE),
        CardRule("TIME_041", {Hook.BATTLECRY: (GuessEnemyHandGainHealth(),)}, _FINAL_48_SOURCE),
        CardRule("TIME_064", {}, _FINAL_48_SOURCE),
        CardRule("TIME_103", {Hook.DEATHRATTLE: (DrawPlayedCardCopy(),)}, _FINAL_48_SOURCE),
        CardRule("TIME_706", {Hook.BATTLECRY: (RestoreStartingHandUntilEndTurn(),)}, _FINAL_48_SOURCE),
        CardRule("TTN_851", {Hook.SPELL: (ArmSpellSurchargeTwoEnemyTurns(),)}, _FINAL_48_SOURCE),
        # Every current-standard generated Coin remains a distinct entity in
        # Power.log.  Their effect is intentionally shared, not inferred from
        # the display name, so future non-Coin cards named "Coin" cannot gain
        # mana accidentally.
        *tuple(
            CardRule(card_id, {Hook.SPELL: (GainMana(1),)}, _AUXILIARY_TOKEN_SOURCE)
            for card_id in (
                "CATA_COIN1", "CATA_COIN2", "CATA_COIN3", "CATA_COIN4", "CATA_COIN5", "CATA_COIN6",
                "DINO_COIN1", "DINO_COIN2", "EDR_COIN1", "EDR_COIN2", "TLC_COIN2",
                "TIME_COIN1", "TIME_COIN2", "TIME_COIN3", "TIME_COIN4", "TIME_EVENT_COIN",
                "JAIL_COIN2", "JAIL_COIN3", "JAIL_EVENT_COIN", "MUDAN_COIN1", "GDB_COIN2",
            )
        ),
        # Cataclysm and Mending generated forms.  These are real hand/board
        # entities in the client, not presentation-only option labels.
        CardRule("CATA_552t", {Hook.BATTLECRY: (EbonscaleScoutBattlecry(),)},
                 _AUXILIARY_TOKEN_SOURCE, TargetSpec(TargetKind.ENEMY_MINION)),
        CardRule("CATA_553t", {Hook.BATTLECRY: (GrantDragonsRush(),)},
                 _AUXILIARY_TOKEN_SOURCE),
        CardRule("MEND_100t", {Hook.SPELL: (CastRandomExecutableSpells(3, 1),)},
                 _AUXILIARY_TOKEN_SOURCE),
        CardRule("MEND_505t", {Hook.SPELL: (AddLeylineExtraTrigger(),)},
                 _AUXILIARY_TOKEN_SOURCE),
        CardRule("MEND_505t2", {Hook.SPELL: (ReduceLeylineCosts(2),)},
                 _AUXILIARY_TOKEN_SOURCE),
        CardRule("MEND_505t3", {Hook.SPELL: (IncreaseLeylinePower(2),)},
                 _AUXILIARY_TOKEN_SOURCE),
        # Eredar Deceptor emits this exact 1/1 Rush token in current logs;
        # its attack behavior is carried by the entity metadata.
        CardRule("TTN_843t1", {}, _AUXILIARY_TOKEN_SOURCE),
        CardRule("HERO_11bpt", {}, _AUXILIARY_TOKEN_SOURCE),
        CardRule("UNG_999t2t1", {}, _AUXILIARY_TOKEN_SOURCE),
        *tuple(CardRule(card_id, {}, _AUXILIARY_TOKEN_SOURCE) for card_id in (
            "UNG_999t2", "UNG_999t3", "UNG_999t8",
        )),
        # Emerald Dream's Choose One options are emitted as concrete spell
        # entities in Power.log.  Declare the option surface explicitly so a
        # replay can resolve either the parent card or the selected entity.
        CardRule("EDR_209a", {Hook.SPELL: (BuffAllOtherFriendlyMinions(1, 3),)},
                 _AUXILIARY_TOKEN_SOURCE),
        CardRule("EDR_209b", {Hook.SPELL: (SummonCenariusAncient(),)},
                 _AUXILIARY_TOKEN_SOURCE),
        CardRule("EDR_233a", {Hook.SPELL: (Summon("DRG_217t", count=3),)},
                 _AUXILIARY_TOKEN_SOURCE),
        CardRule("EDR_233b", {Hook.SPELL: (Summon("EDR_233t2", count=2),)},
                 _AUXILIARY_TOKEN_SOURCE),
        CardRule("EDR_257a", {Hook.SPELL: (BuffSelfAttackShield(),)},
                 _AUXILIARY_TOKEN_SOURCE),
        CardRule("EDR_257b", {Hook.SPELL: (BuffSelfHealthLifesteal(),)},
                 _AUXILIARY_TOKEN_SOURCE),
        CardRule("EDR_263a", {Hook.SPELL: (DamageEnemyHero(4),)},
                 _AUXILIARY_TOKEN_SOURCE),
        CardRule("EDR_263b", {Hook.SPELL: (SummonCustomRushWolf(2),)},
                 _AUXILIARY_TOKEN_SOURCE),
        CardRule("EDR_460t", {Hook.SPELL: (NewMoonDamage(),)},
                 _AUXILIARY_TOKEN_SOURCE, TargetSpec(TargetKind.ENEMY_MINION)),
        CardRule("EDR_461t", {Hook.SPELL: (RitualNewMoon(),)},
                 _AUXILIARY_TOKEN_SOURCE),
        CardRule("EDR_490a", {Hook.SPELL: (Summon("EDR_490t", count=2),)},
                 _AUXILIARY_TOKEN_SOURCE),
        CardRule("EDR_490b", {Hook.SPELL: (DestroyActionTarget(),)},
                 _AUXILIARY_TOKEN_SOURCE, TargetSpec(TargetKind.ENEMY_MINION)),
        CardRule("EDR_525A", {Hook.SPELL: (GiveHeroPoisonousThisTurn(),)},
                 _AUXILIARY_TOKEN_SOURCE),
        CardRule("EDR_525B", {Hook.SPELL: (SetDeathrattleDamageAllEnemies(2),)},
                 _AUXILIARY_TOKEN_SOURCE),
        CardRule("EDR_570A", {Hook.SPELL: (DamageAllMinions(1),)},
                 _AUXILIARY_TOKEN_SOURCE),
        CardRule("EDR_570B", {Hook.SPELL: (BuffActionTargetIfDamaged(2, 2),)},
                 _AUXILIARY_TOKEN_SOURCE, TargetSpec(TargetKind.DAMAGED_MINION)),
        CardRule("EDR_813a", {Hook.SPELL: (Summon("EDR_813at", count=2),)},
                 _AUXILIARY_TOKEN_SOURCE),
        CardRule("EDR_813b", {Hook.SPELL: (SpendCorpseDamageActionTarget(2, 4),)},
                 _AUXILIARY_TOKEN_SOURCE, TargetSpec(TargetKind.ANY_MINION)),
        CardRule("EDR_820a", {Hook.SPELL: (SummonRandomDreadseed(count=2),)},
                 _AUXILIARY_TOKEN_SOURCE),
        CardRule("EDR_820b", {Hook.SPELL: (DamageAllMinions(2),)},
                 _AUXILIARY_TOKEN_SOURCE),
        CardRule("EDR_872A", {Hook.SPELL: (OfferClassSpellDiscover("MAGE"),)},
                 _AUXILIARY_TOKEN_SOURCE),
        CardRule("EDR_872B", {Hook.SPELL: (OfferClassSpellDiscover("DRUID"),)},
                 _AUXILIARY_TOKEN_SOURCE),
        CardRule("FIR_918t", {Hook.SPELL: (LightNewMoon(),)},
                 _AUXILIARY_TOKEN_SOURCE, TargetSpec(TargetKind.ANY_MINION)),
    ))

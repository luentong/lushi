"""Rules-first Dragon Warrior mirror vertical slice.

The simulator deliberately supports only the supplied Dragon Warrior deck and a
closed generation pool. Unsupported generated cards are errors, never vanilla
minions. This makes incomplete coverage visible in benchmark output.
"""

from __future__ import annotations

import copy
import hashlib
import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .rules import (
    DECLARATIVE_METADATA_ALIASES,
    DECLARATIVE_METADATA_IDS,
    Hook,
    RuleContext,
    STANDARD_DECLARATIVE_IDS,
    TargetKind,
    build_rule_registry,
)


DRAGON_DECKSTRING = (
    "AAECAQcEzp4G4+YG69YHstgHDar8Bqv8BqWFB+iHB9KXB7etB+yyB7XAB5XCB5vCB5zCB6ngB/vgBwAA"
)
RULESET = "dragon-warrior-closed-v4"

DIRECT_IDS = {
    "CORE_SW_066",
    "CORE_REV_990",
    "EDR_456",
    "EDR_457",
    "EDR_492",
    "FIR_939",
    "TLC_600",
    "TIME_034",
    "END_033",
    "CATA_556",
    "CATA_582",
    "CATA_584",
    "CATA_585",
    "JAIL_421",
    "JAIL_384",
    "CAP_105",
    "CAP_107",
}

GENERATED_DRAGON_IDS = {
    "CATA_111",  # Darkscale Broodmother
    "CATA_160",  # Scorching Ravager
    "CATA_476",  # Bronze Keeper
    "CATA_497",  # Ultraxion
    "CATA_898",  # Scaled Lancer
    "CATA_999",  # Earthen Drake
    "CORE_AT_123",  # Chillmaw
    "CORE_DRG_079",  # Evasive Wyrm
    "CORE_EX1_043",  # Twilight Drake
    "CORE_LOOT_137",  # Sleepy Dragon
    "CORE_NEW1_023",  # Faerie Dragon
    "CORE_UNG_848",  # Primordial Drake
    "CORE_YOP_034",  # Runaway Blackwing
    "CS3_035",  # Nozdormu the Eternal
    "DINO_401",  # The Great Dracorex
    "EDR_000",  # Ysera, Emerald Aspect
    "EDR_260",  # Illusory Greenwing
    "EDR_453",  # Briarspawn Drake
    "EDR_459",  # Afflicted Devastator
    "EDR_465",  # Ysondre
    "EDR_571",  # Fae Trickster
    "EDR_572",  # Tormented Dreadwing
    "EDR_889",  # Petal Peddler
    "END_021",  # Dimensional Weaponsmith
    "END_022",  # Time-Twisted Seer
    "END_034",  # Crumblecrusher
    "END_035",  # Omen of the End
    "FIR_956",  # Dragon Turtle
    "TIME_003",  # Portal Vanguard
    "TIME_004",  # Conflux Crasher
    "TIME_045",  # Whelp of the Infinite
    "TIME_051",  # Soldier of the Infinite
    "TIME_056",  # Whelp of the Bronze
    "TIME_024",  # Murozond, Unbounded
    "TIME_063",  # Timelord Nozdormu
    "TIME_714",  # Chrono-Lord Epoch
    "TIME_720",  # Soldier of the Bronze
    "TIME_871",  # Heir of Hereafter
    "TLC_243",  # Whirling Stormdrake
    "TLC_888",  # Cloud Serpent
}

GENERATED_WARRIOR_MINION_IDS = {
    "CORE_DRG_024",  # Sky Raider
    "CAP_104",  # Blastpowder Engineer
    "CAP_106",  # Captain Crowley
    "CATA_586",  # Destructive Blaze
    "CATA_591",  # Commander Geddon
    "CATA_150",  # Ragnaros, the Great Fire
    "CATA_722",  # Envoy of the End
    "CORE_BT_120",  # Warmaul Challenger
    "CORE_EX1_414",  # Grommash Hellscream
    "CORE_EX1_604",  # Frothing Berserker
    "CORE_OG_149",  # Ravaging Ghoul
    "CORE_OG_218",  # Bloodhoof Brave
    "CORE_WW_329",  # Detonation Juggernaut
    "CORE_NX2_028",  # Hookfist-3000
    "DINO_400",  # Barricade Basher
    "EDR_468",  # Eggbasher
    "EDR_471",  # Tortolla
    "EDR_465",  # Ysondre
    "END_019",  # Endtime Survivor
    "FIR_928",  # Keeper of Flame
    "JAIL_029",  # Rioter
    "JAIL_311",  # Scrappy Defender
    "JAIL_435",  # Rampaging Hound
    "JAIL_455",  # Disguised Watchman
    "TLC_606",  # Latorvian Armorer
    "TLC_623",  # Stonecarver
    "TLC_624",  # Nablya, the Watcher
}

GENERATED_PIRATE_IDS = {
    "CORE_DRG_024",  # Sky Raider
    "CORE_NEW1_018",  # Bloodsail Raider
    "CORE_NEW1_022",  # Dread Corsair
    "CORE_NEW1_027",  # Southsea Captain
    "CORE_WON_351",  # Small-Time Buccaneer
    "CS3_022",  # Fogsail Freebooter
    "TIME_054",  # Time Skipper
}

GENERATED_MINION_IDS = (
    GENERATED_DRAGON_IDS | GENERATED_WARRIOR_MINION_IDS | GENERATED_PIRATE_IDS
)

# First generally playable tranche from Tortotem's random multi-type-minion
# dependency. Tortotem itself remains excluded until every member of that pool
# has full play-from-hand behavior.
ADDITIONAL_GENERATED_MINION_IDS = {
    "CAP_800",  # Sinful Steed
    "CATA_464",  # Blackwing Experiment
    "CATA_469",  # Chromatic Broodmother
    "CORE_BT_201",  # Augmented Porcupine
    "CORE_DRG_107",  # Violet Spellwing
    "CORE_SW_068",  # Mo'arg Forgefiend
    "CORE_TTN_866",  # Mythical Terror
    "CORE_ULD_723",  # Murmy
    "CORE_UNG_084",  # Fire Plume Phoenix
    "DINO_404",  # Firegill
    "DINO_413",  # Chillspine Stegodon
    "DINO_409",  # Techysaurus
    "DINO_416",  # Hollow Direhorn
    "CATA_550",  # Magmaw
    "DINO_407",  # Mirrex, the Crystalline
    "DINO_132",  # Asphyxiodon
    "DINO_138",  # Diabolus Rex
    "FIR_919",  # Everburning Phoenix
    "FIR_953",  # Magma Hound
    "FIR_951",  # Volcoross
    "EDR_421",  # Omen
    "EDR_810",  # Hideous Husk
    "EDR_818",  # Nythendra
    "END_030",  # Haywire Hornswog
    "JAIL_942",  # Specter of Despair
    "RLK_708",  # Chillfallen Baron
    "TIME_046",  # Cyborg Patriarch
    "TIME_053",  # Sandmaw
    "TIME_713",  # Time Adm'ral Hooktail
    "JAIL_457",  # Hijacked Securitybot
    "TLC_225",  # Cinderfin
    "TLC_224",  # Mechanized Magma
    "TLC_401",  # Bonechill Stegodon
    "TLC_240",  # Tyrannogill
    "TLC_432",  # Dread Raptor
    "TLC_482",  # Slagclaw
    "TLC_436",  # Reanimated Pterrordax
    "TLC_102",  # Torga
    "TLC_223",  # Volcanic Thrasher
    "TLC_463",  # Razidir
    "END_004",  # Remnant of Rage
}

ADDITIONAL_PLAYABLE_MINION_IDS = {
    "CATA_151",  # Azshara, Ocean Lord
    "CATA_720",  # Warmaster Blackhorn
    "CATA_613",  # Survivalist
    "CATA_615",  # Genn, Cursed King
    "CORE_CFM_344",  # Finja, the Flying Star
    "CORE_BT_187",  # Kayn Sunfury
    "CORE_CATA_001",  # Tichondrius
    "CORE_CS2_122",  # Raid Leader
    "CORE_CS2_222",  # Stormwind Champion
    "CORE_DRG_256",  # Dragonbane
    "CORE_EX1_162",  # Dire Wolf Alpha
    "CORE_EX1_507",  # Murloc Warleader
    "CORE_EX1_002",  # The Black Knight
    "CORE_EX1_012",  # Bloodmage Thalnos
    "CORE_EX1_014",  # King Mukla
    "CORE_EX1_100",  # Lorewalker Cho
    "CORE_EX1_110",  # Cairne Bloodhoof
    "CORE_SCH_717",  # Keymaster Alabaster
    "EDR_480",  # Goldrinn
    "DINO_410",  # The Egg of Khelos
    "EDR_258",  # Toreth the Unbreaking
    "EDR_844",  # Naralex, Herald of the Flights
    "CORE_EDR_003",  # Falric
    "CORE_GVG_085",  # Annoy-o-Tron
    "CORE_GVG_103",  # Micro Machine
    "CORE_KAR_061",  # The Curator
    "CORE_REV_946",  # Steamcleaner
    "JAIL_456",  # P1CK-P0K3T
    "JAIL_502",  # Alarm-o-Matic
    "JAIL_850",  # Warden Maiev
    "JAIL_852",  # Togwaggle, Smuggler King
    "JAIL_882",  # R4T-C4TCH3R
    "JAIL_202",  # Spiderling
    "JAIL_459",  # Arachnathid
    "JAIL_890",  # Captive Nathrezim
    "TIME_015",  # Hardlight Protector
    "TIME_017",  # Tankgineer
    "TIME_043",  # PMM Infinitizer
    "TIME_048",  # Clockwork Rager
    "TIME_060",  # Quantum Destabilizer
    "TIME_606",  # Quel'dorei Fletcher
    "TIME_852",  # Azure Queen Sindragosa
    "TIME_603",  # Ticking Timebomb
    "TLC_228",  # Bralma Searstone
    "TLC_241",  # Ido of the Threshfleet
    "TLC_110",  # City Chief Esho
    "CS3_024",  # Taelan Fordring
    "CS3_025",  # Overlord Runthak
    "FIR_958",  # Tindral Sageswift
    "TLC_480",  # Krog, Crater King
}

# Closed Rewind cards whose random outcomes can be played from hand without
# opening another generated-card pool.
ADDITIONAL_PLAYABLE_CARD_IDS = {
    "TIME_001",  # Chrono Daggers
    "TIME_008",  # Bygone Doomspeaker
    "TIME_433",  # Cease to Exist
    "TIME_441",  # Aeon Rend
    "TIME_610",  # Shadows of Yesterday
}

SPECIAL_TOKEN_IDS = {
    "CAP_107t",  # Cannoneer
    "CATA_615t",  # Genn, Worgen King
    "CATA_151t",  # Azshara's Tentacle
    "DINO_410t",  # Khelos
    "DINO_410t2",  # Slightly cracked Egg
    "DINO_410t3",  # More cracked Egg
    "DINO_410t4",  # Very cracked Egg
    "DINO_410t5",  # Most cracked Egg
    "EX1_014t",  # Bananas
    "EX1_110t",  # Baine Bloodhoof
    "TLC_241t",  # Call the Threshfleet!
    "JAIL_732",  # Void Soul
}

# These legacy/basic entities are runtime dependencies of current hero powers,
# not cards that can start in a Standard deck. Keeping them separate preserves
# the frozen rules-v3/v4 policy model vocabulary.
BASIC_AUXILIARY_IDS = {
    "CS2_101t",  # Silver Hand Recruit
    "CS2_082",  # Wicked Knife
    "CS2_050",  # Searing Totem
    "CS2_051",  # Stoneclaw Totem
    "CS2_052",  # Wrath of Air Totem
    "NEW1_009",  # Healing Totem
    "HERO_11bpt",  # Frail Ghoul
}

BASIC_TOTEM_IDS = ("CS2_050", "CS2_051", "CS2_052", "NEW1_009")

# Their outer rule is implemented, but they remain unreachable from random
# runtime pools until every transitive generation dependency is closed.
BLOCKED_GENERATOR_IDS = {
    "EDR_493",  # Alara'shi -> Demon play-from-hand pool
    "FIR_924",  # Shadowflame Stalker -> Demon play-from-hand pool
}

# The first three upgrades of Void Soul are closed in summon context. Its
# generated Demons do not execute Battlecries, but persistent keywords,
# Dormant, triggers, and Deathrattles remain active.
VOID_SOUL_DEMON_IDS_BY_COST = {
    1: {
        "CATA_200", "CORE_BT_351", "CORE_EX1_319", "CORE_YOD_026",
        "EDR_456",
    },
    2: {"CATA_612", "CORE_BT_156", "CORE_LOOT_013"},
    3: {"CATA_490", "EDR_521", "EDR_780", "JAIL_399"},
    4: {"CORE_TTN_843", "EDR_102", "EDR_524", "EDR_856", "TLC_463"},
    5: {"CORE_BT_510", "CORE_EX1_310", "EDR_493", "EDR_891"},
    6: {"CORE_ULD_165", "DINO_138", "JAIL_007", "JAIL_398"},
    7: {"CORE_BT_493", "CORE_TTN_866", "EDR_892", "END_004"},
    8: {"CORE_SW_068", "CS3_020", "DINO_132"},
    9: {"CORE_CATA_001", "CORE_LOOT_368", "EDR_486", "JAIL_906"},
    10: {"EDR_421", "JAIL_890"},
}
SUPPORTED_VOID_SOUL_DEMON_IDS = set().union(
    *VOID_SOUL_DEMON_IDS_BY_COST.values()
)

# Alara'shi and Shadowflame Stalker create Demons that can later be played
# from hand. This is stricter than Void Soul's summon-only closure.
UNSUPPORTED_DEMON_PLAY_IDS = {"EDR_102", "EDR_493"}
SUPPORTED_DEMON_PLAY_IDS = (
    SUPPORTED_VOID_SOUL_DEMON_IDS - UNSUPPORTED_DEMON_PLAY_IDS
)

# Undefeated Champion summons rather than plays these minions, so Battlecries,
# Outcast, and similar from-hand effects do not need to execute. Keep this set
# contextual instead of claiming those cards are generally supported by every
# generator.
SUPPORTED_ONE_COST_SUMMON_IDS = {
    "CAP_004",
    "CAP_107",
    "CATA_200",
    "CATA_130",
    "CATA_210",
    "CATA_484",
    "CATA_556",
    "CATA_558",
    "CORE_BT_351",
    "CORE_BT_480",
    "CORE_BT_701",
    "CORE_CS2_188",
    "CORE_CS2_189",
    "CORE_DRG_024",
    "CORE_DRG_107",
    "CORE_EX1_010",
    "CORE_EX1_011",
    "CORE_EX1_193",
    "CORE_EX1_319",
    "CORE_EX1_509",
    "CORE_GIL_558",
    "CORE_ICC_038",
    "CORE_KAR_069",
    "CORE_RLK_814",
    "CORE_SW_439",
    "CORE_ULD_191",
    "CORE_ULD_723",
    "CORE_UNG_205",
    "CORE_UNG_809",
    "CORE_UNG_912",
    "CORE_WON_351",
    "CORE_WC_042",
    "CORE_YOD_026",
    "CS3_007",
    "EDR_456",
    "EDR_469",
    "EDR_485",
    "EDR_529",
    "EDR_816",
    "EDR_849",
    "EDR_971",
    "EDR_999",
    "END_022",
    "FIR_908",
    "JAIL_202",
    "JAIL_442",
    "JAIL_452",
    "JAIL_501",
    "JAIL_703",
    "JAIL_880",
    "RLK_503",
    "RLK_958",
    "MEND_040",
    "TIME_606",
    "TIME_876",
    "TLC_249",
    "TLC_461",
    "TLC_514",
    "TLC_603",
    "TLC_820",
}

BONUS_EFFECTS = (
    "divine_shield",
    "elusive",
    "lifesteal",
    "poisonous",
    "reborn",
    "rush",
    "taunt",
    "windfury",
)

SUPPORTED_IDS = (
    DIRECT_IDS | GENERATED_MINION_IDS | SUPPORTED_ONE_COST_SUMMON_IDS
    | SUPPORTED_VOID_SOUL_DEMON_IDS | ADDITIONAL_GENERATED_MINION_IDS
    | ADDITIONAL_PLAYABLE_MINION_IDS | ADDITIONAL_PLAYABLE_CARD_IDS
    | SPECIAL_TOKEN_IDS | BLOCKED_GENERATOR_IDS | DECLARATIVE_METADATA_IDS
    | DECLARATIVE_METADATA_ALIASES.keys()
)
EXECUTABLE_CARD_IDS = SUPPORTED_IDS | STANDARD_DECLARATIVE_IDS

# The fixed Dragon Warrior deck starts with no Herald-related or Fabled card.
# Constructed generation therefore excludes these cards even though they are
# collectible class/tribe matches in the raw Standard catalog.
DISCOVER_BANNED_IDS = {
    "CATA_150", "CATA_160", "CATA_497", "CATA_722", "TIME_850",
}

DRAGON_IDS = {
    "TLC_600", "TIME_034", "END_033", "CATA_556",
    *GENERATED_DRAGON_IDS,
} - DISCOVER_BANNED_IDS
# Standard dragons in the supported generation closure whose printed cost is
# at most three.  Keep this explicit: card definitions are loaded per game,
# while public-belief sampling needs the pool at module import time.
LOW_COST_DRAGON_IDS = {
    "CATA_111", "CATA_556", "CORE_NEW1_023", "EDR_571", "EDR_889",
    "END_021", "END_022", "TIME_003", "TIME_045", "TIME_056",
    "TIME_063", "TLC_888",
} & DRAGON_IDS
WARRIOR_MINION_IDS = {
    "CORE_DRG_024",
    "CATA_160",
    "CATA_497",
    "CATA_586",
    "CATA_591",
    "CATA_150",
    "CATA_722",
    "CAP_104",
    "CAP_106",
    "DINO_401",
    "DINO_400",
    "EDR_456",
    "EDR_457",
    "EDR_459",
    "EDR_468",
    "EDR_471",
    "EDR_465",
    "END_021",
    "END_022",
    "END_019",
    "FIR_956",
    "FIR_928",
    "TLC_600",
    "TLC_606",
    "TLC_623",
    "TIME_034",
    "TIME_714",
    "TIME_871",
    "JAIL_421",
    "JAIL_384",
    "CAP_107",
    "CORE_OG_149",
    "CORE_OG_218",
    "CORE_WW_329",
    "CORE_EX1_414",
    "CORE_EX1_604",
    "CORE_BT_120",
    "CORE_NX2_028",
    "JAIL_029",
    "JAIL_311",
    "JAIL_435",
    "JAIL_455",
    "TLC_624",
} - DISCOVER_BANNED_IDS
PIRATE_IDS = {
    "CAP_104", "CAP_106", "CAP_107", "CORE_NX2_028",
    *GENERATED_PIRATE_IDS,
}
LEGENDARY_IDS = {"JAIL_421", "JAIL_384"}

SUPPORTED_STADIUM_WEAPONS = {
    "CAP_103": ("Hand Cannon", 3, 2),
    "CATA_467": ("Command Claw", 2, 2),
    "CATA_472": ("Inspiring Maul", 2, 2),
    "CATA_580": ("Cataclysmic War Axe", 3, 2),
    "CORE_BT_781": ("Bulwark of Azzinoth", 1, 4),
    "CORE_BT_921": ("Aldrachi Warblades", 2, 2),
    "CORE_DAL_720": ("Waggle Pick", 4, 2),
    "CORE_GVG_059": ("Coghammer", 2, 3),
    "CORE_LOOT_044": ("Bladed Gauntlet", 0, 2),
    "CORE_OG_031": ("Hammer of Twilight", 4, 2),
    "CORE_RLK_086": ("Frostmourne", 4, 3),
    "CORE_TRL_111": ("Headhunter's Hatchet", 2, 2),
    "DINO_408": ("Crystal Tusk", 2, 2),
    "EDR_253": ("Ursine Maul", 4, 2),
    "EDR_416": ("Shepherd's Crook", 3, 2),
    "EDR_525": ("Barbed Thorn", 1, 3),
    "EDR_812": ("Grotesque Runeblade", 2, 2),
    "EDR_842": ("Defiled Spear", 2, 3),
    "END_001": ("Jagged Edge of Time", 3, 2),
    "END_012": ("Hand of Infinity", 4, 2),
    "END_016": ("Chronoclaws", 4, 3),
    "FIR_922": ("Cindersword", 1, 2),
    "JAIL_376": ("Ball and Chain", 1, 2),
    "JAIL_329": ("Truth Seeker", 3, 3),
    "JAIL_380": ("Smuggled Shovel", 1, 2),
    "JAIL_450": ("Corpse Cannon", 1, 3),
    "JAIL_503": ("Blackpaw's Whip", 3, 2),
    "JAIL_730": ("Stardust Scythe", 3, 3),
    "MEND_803": ("Emboldening Blade", 3, 2),
    "RLK_067": ("Corrupted Ashbringer", 5, 2),
    "TLC_478": ("Axe of the Forefathers", 2, 2),
    "TLC_833": ("Insect Claw", 2, 2),
}
GENERATION_PROFILE = "closed_generation_pools"

DRAGON_DECK_COUNTS = {
    "CORE_SW_066": 1, "CORE_REV_990": 1, "EDR_456": 2,
    "EDR_457": 2, "EDR_492": 2, "FIR_939": 2, "TLC_600": 2,
    "TIME_034": 2, "END_033": 2, "CATA_556": 2, "CATA_582": 2,
    "CATA_584": 2, "CATA_585": 2, "JAIL_421": 1, "JAIL_384": 1,
    "CAP_105": 2, "CAP_107": 2,
}


class UnsupportedGeneratedCard(RuntimeError):
    pass


@dataclass(frozen=True)
class CardDef:
    card_id: str
    name: str
    card_type: str
    cost: int
    attack: int = 0
    health: int = 0
    race: str = ""
    mechanics: tuple[str, ...] = ()
    card_class: str = ""
    races: tuple[str, ...] = ()
    card_set: str = ""
    text: str = ""
    spell_school: str = ""
    spell_damage: int = 0

    def __deepcopy__(self, memo: dict[int, Any]) -> "CardDef":
        # Definitions are immutable and shared by every search branch.
        return self


@dataclass
class CardInstance:
    entity_id: int
    definition: CardDef
    cost_delta: int = 0
    attack_delta: int = 0
    health_delta: int = 0
    gifts: list[str] = field(default_factory=list)
    taunt: bool = False
    rush: bool = False
    charge: bool = False
    lifesteal: bool = False
    elusive: bool = False
    stealth: bool = False
    divine_shield: bool = False
    divine_shield_hits: int = 0
    divine_shield_toreth: bool = False
    windfury: bool = False
    reborn: bool = False
    poisonous: bool = False
    aura_poisonous: bool = False
    battlecry_twice: bool = False
    living_nightmare: bool = False
    summoned_turn: int = -1
    played_turn: int = -1
    attacks_this_turn: int = 0
    damage: int = 0
    silenced: bool = False
    started_in_deck: bool = False
    created_by: str | None = None
    dormant_turns: int = 0
    summoned_when_drawn: bool = False
    immune: bool = False
    infinite_attack_next_turn: bool = False
    herald_power: int = 1
    deck_threshold_attack: int = 0
    pirate_aura_stats: int = 0
    aura_attack_bonus: int = 0
    aura_health_bonus: int = 0
    weapon_attack_bonus: int = 0
    burning_turns: int = 0
    burning_applied_turn: int = -1
    twilight_whelp_bonus: int = 0
    casts_when_drawn_damage: int = 0
    void_soul_cost: int = 0
    omen_damage: int = 1
    summon_moragg_on_death: bool = False
    frozen_turn: int = -1
    cant_attack: bool = False
    mirrex_tracker: bool = False
    spell_damage_bonus: int = 0
    prepared_turn: int = -1
    dynamic_spell_damage: int = 0
    illusion_fake: bool = False
    cant_attack_heroes_turn: int = -1
    dies_at_end_of_turn: bool = False
    mana_spent_while_held: int = 0
    minion_played_while_held: bool = False
    opponent_card_copy_played_while_held: bool = False
    copied_from_opponent: bool = False
    temporary: bool = False
    return_control_to: int | None = None
    return_control_at_end_of_turn: int | None = None
    cant_attack_turn: int = -1
    temporary_attack_modifiers: list[tuple[int, int]] = field(default_factory=list)

    @property
    def card_id(self) -> str:
        return self.definition.card_id

    @property
    def attack(self) -> int:
        enraged = 0
        if self.damage > 0 and not self.silenced:
            if self.card_id == "CORE_EX1_414":
                enraged = 6
            elif self.card_id == "CORE_OG_218":
                enraged = 3
        threshold = 0 if self.silenced else self.deck_threshold_attack
        # External auras continue to affect a silenced recipient. Self-owned
        # conditional bonuses are zeroed by _refresh_continuous when the source
        # minion itself is silenced.
        continuous = (
            self.pirate_aura_stats + self.aura_attack_bonus
            + self.weapon_attack_bonus
        )
        return max(
            0,
            self.definition.attack + self.attack_delta + enraged + threshold
            + continuous,
        )

    @property
    def max_health(self) -> int:
        aura = self.pirate_aura_stats + self.aura_health_bonus
        # Health-reduction enchantments can reduce maximum Health to zero and
        # destroy a minion; clamping at one incorrectly kept those minions alive.
        return max(0, self.definition.health + self.health_delta + aura)

    @property
    def health(self) -> int:
        return self.max_health - self.damage

    @property
    def cost(self) -> int:
        return max(0, self.definition.cost + self.cost_delta)

    def has_race(self, race: str) -> bool:
        return race == self.definition.race or race in self.definition.races

    def clone(self, entity_id: int) -> "CardInstance":
        result = copy.deepcopy(self)
        result.entity_id = entity_id
        result.damage = 0
        result.attacks_this_turn = 0
        result.played_turn = -1
        result.infinite_attack_next_turn = False
        result.frozen_turn = -1
        return result


@dataclass
class Weapon:
    card_id: str
    name: str
    attack: int
    durability: int
    killed_minions: list[CardDef] = field(default_factory=list)
    ammunition: int | None = None


@dataclass
class Location:
    entity_id: int
    card_id: str
    durability: int
    cooldown: int = 1


@dataclass
class Player:
    index: int
    card_class: str = "WARRIOR"
    deck: list[CardInstance] = field(default_factory=list)
    hand: list[CardInstance] = field(default_factory=list)
    board: list[CardInstance] = field(default_factory=list)
    dead_minions: list[CardInstance] = field(default_factory=list)
    locations: list[Location] = field(default_factory=list)
    health: int = 30
    max_health: int = 30
    armor: int = 0
    mana: int = 0
    max_mana: int = 0
    fatigue: int = 0
    weapon: Weapon | None = None
    hero_attack_bonus: int = 0
    hero_attacks_this_turn: int = 0
    void_soul_level: int = 1
    hero_power_used: bool = False
    hero_power_cost_override: int | None = None
    hero_power_armor: int = 2
    hero_power_id: str | None = None
    fire_spell_played: bool = False
    played_races_this_turn: set[str] = field(default_factory=set)
    played_races_last_turn: set[str] = field(default_factory=set)
    damaged_characters_this_turn: set[str] = field(default_factory=set)
    herald_count: int = 0
    geddon_draw: bool = False
    ysondre_deaths: int = 0
    hero_board_attack_bonus: int = 0
    frozen_turn: int = -1
    cards_played_this_turn: int = 0
    generated_cards_played: int = 0
    pending_phoenixes: int = 0
    corpses: int = 0
    pending_magmaw_bodies: int = 0
    magmaw_entity: int | None = None
    overloaded_mana_this_game: int = 0
    overload_next_turn: int = 0
    locked_mana: int = 0
    next_demon_free: bool = False
    hero_divine_shield: bool = False
    hero_divine_shield_hits: int = 0
    hero_divine_shield_toreth: bool = False
    turns_taken: int = 0
    dragons_played_this_turn: int = 0
    start_turn_temporary_mana_charges: int = 0
    minion_cost_increase_turn: int = -1
    minion_cost_increase_amount: int = 0

    @property
    def attack(self) -> int:
        weapon_attack = 0
        if self.weapon:
            weapon_attack = (
                self.armor if self.weapon.card_id == "CORE_LOOT_044"
                else self.weapon.attack
            )
        return self.hero_attack_bonus + weapon_attack + self.hero_board_attack_bonus


@dataclass(frozen=True)
class Action:
    kind: str
    source: int | None = None
    target_player: int | None = None
    target_entity: int | None = None

    def key(self) -> tuple:
        return (
            self.kind,
            -1 if self.source is None else self.source,
            -1 if self.target_player is None else self.target_player,
            -1 if self.target_entity is None else self.target_entity,
        )


def _clean_text(value: str) -> str:
    return value or ""


class DragonMirrorGame:
    """A deterministic, closed-pool simulator for the supplied Dragon deck."""

    def __init__(
        self,
        cards_path: str | Path,
        seed: int = 1,
        *,
        manual_mulligan: bool = False,
        deck_counts: tuple[dict[str, int], dict[str, int]] | None = None,
        player_classes: tuple[str, str] = ("WARRIOR", "WARRIOR"),
    ):
        self.rng = random.Random(seed)
        self.seed = seed
        self.turn = 0
        self.current = 0
        self.next_entity_id = 1
        self.invalid_actions = 0
        self.events: list[dict[str, Any]] = []
        self.finished = False
        self.winner: int | None = None
        self.pending_choice: dict[str, Any] | None = None
        self.minions_died_this_turn = 0
        self.deck_counts = deck_counts or (DRAGON_DECK_COUNTS, DRAGON_DECK_COUNTS)
        requested_ids = set(self.deck_counts[0]) | set(self.deck_counts[1])
        unsupported = requested_ids - EXECUTABLE_CARD_IDS
        if unsupported:
            raise UnsupportedGeneratedCard(
                "deck contains cards without executable rules: "
                + ", ".join(sorted(unsupported))
            )
        self.card_defs = self._load_defs(Path(cards_path))
        self.rule_registry = build_rule_registry()
        missing = (
            EXECUTABLE_CARD_IDS | BASIC_AUXILIARY_IDS
        ) - self.card_defs.keys()
        if missing:
            raise ValueError(f"missing card metadata: {sorted(missing)}")
        self.players = [
            Player(0, card_class=player_classes[0]),
            Player(1, card_class=player_classes[1]),
        ]
        for player in self.players:
            player.deck = self._new_deck(player.index)
            self.rng.shuffle(player.deck)
        self._initial_draw()
        if manual_mulligan:
            self._begin_mulligan(0)
        else:
            for player in self.players:
                selected = {
                    card.entity_id for card in player.hand
                    if card.definition.cost >= 4
                }
                self._resolve_mulligan_for_player(player, selected)
            self._finish_mulligan()

    def _load_defs(self, path: Path) -> dict[str, CardDef]:
        cards = json.loads(path.read_text(encoding="utf-8"))
        result = {}
        aliases_by_source: dict[str, list[str]] = {}
        for target_id, source_id in DECLARATIVE_METADATA_ALIASES.items():
            aliases_by_source.setdefault(source_id, []).append(target_id)
        for card in cards:
            card_id = card.get("id")
            target_ids = list(aliases_by_source.get(card_id, ()))
            if card_id in EXECUTABLE_CARD_IDS | BASIC_AUXILIARY_IDS:
                target_ids.append(card_id)
            if not target_ids:
                continue
            for target_id in target_ids:
                result[target_id] = CardDef(
                    card_id=target_id,
                    name=_clean_text(card.get("name")),
                    card_type=card.get("type", ""),
                    cost=int(card.get("cost", 0)),
                    attack=int(card.get("attack", 0)),
                    health=int(card.get("health", 0)),
                    race=card.get("race", "") or "",
                    mechanics=tuple(card.get("mechanics", ())),
                    card_class=card.get("cardClass", "") or "",
                    races=tuple(card.get("races", ())),
                    card_set=card.get("set", "") or "",
                    text=card.get("text", "") or "",
                    spell_school=card.get("spellSchool", "") or "",
                    spell_damage=int(card.get("spellDamage", 0)),
                )
        return result

    def _entity(
        self,
        card_id: str,
        *,
        started_in_deck: bool = False,
        created_by: str | None = None,
    ) -> CardInstance:
        if card_id not in self.card_defs:
            raise UnsupportedGeneratedCard(card_id)
        result = self._instance_from_definition(
            self.card_defs[card_id],
            started_in_deck=started_in_deck,
            created_by=created_by,
        )
        return result

    def _instance_from_definition(
        self,
        definition: CardDef,
        *,
        started_in_deck: bool = False,
        created_by: str | None = None,
    ) -> CardInstance:
        result = CardInstance(
            self.next_entity_id,
            definition,
            started_in_deck=started_in_deck,
            created_by=created_by,
        )
        self.next_entity_id += 1
        result.taunt = "TAUNT" in result.definition.mechanics
        result.rush = "RUSH" in result.definition.mechanics
        result.charge = "CHARGE" in result.definition.mechanics
        result.lifesteal = "LIFESTEAL" in result.definition.mechanics
        result.elusive = "ELUSIVE" in result.definition.mechanics
        result.stealth = "STEALTH" in result.definition.mechanics
        result.divine_shield = "DIVINE_SHIELD" in result.definition.mechanics
        result.divine_shield_hits = 1 if result.divine_shield else 0
        result.windfury = "WINDFURY" in result.definition.mechanics
        result.reborn = "REBORN" in result.definition.mechanics
        result.poisonous = "POISONOUS" in result.definition.mechanics
        result.spell_damage_bonus = result.definition.spell_damage
        result.mirrex_tracker = result.card_id == "DINO_407"
        if result.card_id in {"EDR_469", "MEND_040"}:
            # These use condition-based Dormant rather than a fixed countdown.
            result.dormant_turns = 2_147_483_647
        elif result.card_id == "CORE_BT_156":
            result.dormant_turns = 2
        elif result.card_id == "TIME_046":
            result.dormant_turns = 3
        if result.card_id == "JAIL_942":
            result.cant_attack = True
        if result.card_id == "HERO_11bpt":
            result.dies_at_end_of_turn = True
        return result

    def _update_mirrex_trackers(
        self, opponent: Player, played: CardInstance
    ) -> None:
        for tracker in opponent.hand:
            if not tracker.mirrex_tracker:
                continue
            tracker.definition = copy.deepcopy(played.definition)
            tracker.attack_delta = 3 - tracker.definition.attack
            tracker.health_delta = 4 - tracker.definition.health
            tracker.damage = 0
            tracker.taunt = "TAUNT" in tracker.definition.mechanics
            tracker.rush = "RUSH" in tracker.definition.mechanics
            tracker.charge = "CHARGE" in tracker.definition.mechanics
            tracker.lifesteal = "LIFESTEAL" in tracker.definition.mechanics
            tracker.elusive = "ELUSIVE" in tracker.definition.mechanics
            tracker.stealth = "STEALTH" in tracker.definition.mechanics
            tracker.divine_shield = "DIVINE_SHIELD" in tracker.definition.mechanics
            tracker.windfury = "WINDFURY" in tracker.definition.mechanics
            tracker.reborn = "REBORN" in tracker.definition.mechanics
            tracker.poisonous = "POISONOUS" in tracker.definition.mechanics
            tracker.cant_attack = "CANT_ATTACK" in tracker.definition.mechanics
            tracker.dormant_turns = 3 if tracker.card_id == "TIME_046" else 0
            self._event(
                "mirrex_update", player=opponent.index,
                entity=tracker.entity_id, copied=tracker.card_id,
            )

    def _new_deck(self, player_index: int = 0) -> list[CardInstance]:
        return [
            self._entity(card_id, started_in_deck=True)
            for card_id, count in self.deck_counts[player_index].items()
            for _ in range(count)
        ]

    def _initial_draw(self) -> None:
        for _ in range(3):
            self._deal_opening_card(self.players[0])
        for _ in range(4):
            self._deal_opening_card(self.players[1])

    def _deal_opening_card(self, player: Player) -> CardInstance:
        card = player.deck.pop()
        player.hand.append(card)
        self._event(
            "opening_deal", player=player.index, card=card.card_id,
            entity=card.entity_id,
        )
        return card

    def _begin_mulligan(self, player_index: int) -> None:
        self.current = player_index
        options = tuple(card.entity_id for card in self.players[player_index].hand)
        self.pending_choice = {
            "kind": "MULLIGAN",
            "player": player_index,
            "options": options,
            "selected": set(),
        }
        self._event(
            "mulligan_offer", player=player_index,
            cards=[card.card_id for card in self.players[player_index].hand],
            entities=list(options),
        )

    def _toggle_mulligan(self, entity_id: int | None) -> None:
        selected: set[int] = self.pending_choice["selected"]
        if entity_id in selected:
            selected.remove(entity_id)
            replace = False
        else:
            selected.add(entity_id)
            replace = True
        self._event(
            "mulligan_toggle", player=self.current, entity=entity_id,
            replace=replace,
        )

    def _resolve_mulligan_for_player(
        self, player: Player, selected: set[int]
    ) -> None:
        original = list(player.hand)
        rejected = [card for card in original if card.entity_id in selected]
        kept = [card for card in original if card.entity_id not in selected]
        replacements = [player.deck.pop() for _ in rejected]
        player.hand = kept + replacements
        # Rejected cards return only after replacements are drawn, so a player
        # cannot immediately redraw a card they just mulliganed away.
        player.deck.extend(rejected)
        self.rng.shuffle(player.deck)
        self._event(
            "mulligan_result", player=player.index,
            kept=[card.card_id for card in kept],
            replaced=[card.card_id for card in rejected],
            replacements=[card.card_id for card in replacements],
        )

    def _confirm_mulligan(self) -> None:
        player_index = self.pending_choice["player"]
        selected = set(self.pending_choice["selected"])
        self._resolve_mulligan_for_player(self.players[player_index], selected)
        self.pending_choice = None
        if player_index == 0:
            self._begin_mulligan(1)
        else:
            self._finish_mulligan()

    def _finish_mulligan(self) -> None:
        self.pending_choice = None
        self.current = 0
        self._give_coin(self.players[1], source="MULLIGAN")
        self._start_of_game()
        self._start_turn(0)

    def _start_of_game(self) -> None:
        # Start-of-game happens after initial hands. Hogger duplicates every other
        # Legendary still represented by the deck list; here that is Warptooth.
        for player in self.players:
            if any(c.card_id == "JAIL_384" for c in player.hand + player.deck):
                player.deck.append(self._entity("JAIL_421"))
                self.rng.shuffle(player.deck)
                self._event("start_of_game", player=player.index, card="JAIL_384", duplicated="JAIL_421")

    def _event(self, kind: str, **payload: Any) -> None:
        self.events.append({"turn": self.turn, "kind": kind, **payload})

    def clone(self, *, include_history: bool = False) -> "DragonMirrorGame":
        """Return an independent search state with the exact same RNG stream.

        Immutable card metadata and the read-only rule registry are shared;
        players, entities, pending decisions and RNG state are copied. Search
        normally drops historical events because they are not part of game
        semantics and become increasingly expensive to copy at deep nodes.
        """
        memo: dict[int, Any] = {
            id(self.card_defs): self.card_defs,
            id(self.rule_registry): self.rule_registry,
        }
        if not include_history:
            memo[id(self.events)] = []
        return copy.deepcopy(self, memo)

    def branch(
        self, action: Action, *, include_history: bool = False
    ) -> "DragonMirrorGame":
        """Clone this state and apply one legal action to the child only."""
        child = self.clone(include_history=include_history)
        child.step(action)
        return child

    def determinize_hidden(
        self, observer: int, *, seed: int
    ) -> "DragonMirrorGame":
        """Sample opponent hand/deck placement without touching game RNG.

        This first belief model knows the combined hidden-zone multiset from the
        simulator and randomizes only placement and deck order. The Coin is kept
        in hand because its ownership is public. Unknown generated-card identity
        distributions are not reconstructed yet, so callers must label results
        as ``shuffle_hidden_zones_v0`` rather than full client-fidelity ISMCTS.
        """
        if observer not in (0, 1):
            raise ValueError("observer must be player 0 or 1")
        sampled = self.clone()
        opponent = sampled.players[1 - observer]
        hand_size = len(opponent.hand)
        known_hand = [card for card in opponent.hand if card.card_id == "GAME_005"]
        unknown = [
            card for card in opponent.hand + opponent.deck
            if card not in known_hand
        ]
        sampler = random.Random(seed)
        sampler.shuffle(unknown)
        unknown_hand_size = hand_size - len(known_hand)
        opponent.hand = known_hand + unknown[:unknown_hand_size]
        opponent.deck = unknown[unknown_hand_size:]
        sampled._event(
            "determinization", observer=observer,
            belief_model="shuffle_hidden_zones_v0", seed=seed,
            hidden_hand=hand_size, hidden_deck=len(opponent.deck),
        )
        return sampled

    def observation(self, observer: int) -> dict[str, Any]:
        """Return a snapshot with the opponent's private choices masked."""
        if observer not in (0, 1):
            raise ValueError("observer must be player 0 or 1")
        result = self.snapshot()
        opponent = result["players"][1 - observer]
        opponent["hand"] = [
            {"hidden": True, "slot": slot}
            for slot in range(len(opponent["hand"]))
        ]
        pending = result["pending_choice"]
        if pending and self.current != observer:
            pending["options"] = [
                {"hidden": True, "slot": slot}
                for slot in range(len(pending.get("options", ())))
            ]
        result["observer"] = observer + 1
        result["information_mode"] = "player_observation_v1"
        return result

    def _summon(
        self, player: Player, minion: CardInstance, *, position: int | None = None
    ) -> None:
        if minion.divine_shield and minion.divine_shield_hits <= 0:
            minion.divine_shield_hits = 1
        tidecallers = [
            other for other in player.board
            if other.card_id == "CORE_EX1_509"
            and not other.silenced
            and other.dormant_turns == 0
        ]
        if position is None:
            player.board.append(minion)
        else:
            player.board.insert(position, minion)
        if minion.has_race("MURLOC"):
            for tidecaller in tidecallers:
                tidecaller.attack_delta += 1
                self._event(
                    "murloc_tidecaller_trigger", player=player.index,
                    entity=tidecaller.entity_id, summoned=minion.card_id,
                )
        self._refresh_continuous(player)
        if minion.card_id == "CATA_151t":
            amount = self._herald_power(player.herald_count)
            player.hero_attack_bonus += amount
            self._event(
                "azshara_tentacle", player=player.index,
                entity=minion.entity_id, attack=amount,
            )
        elif minion.card_id == "CATA_151":
            self._summon_azshara_tentacles(player, minion)

    def _summon_azshara_tentacles(
        self, player: Player, azshara: CardInstance
    ) -> None:
        for side in ("left", "right"):
            if len(player.board) + len(player.locations) >= 7:
                break
            main_index = player.board.index(azshara)
            position = main_index if side == "left" else main_index + 1
            tentacle = self._entity("CATA_151t", created_by=azshara.card_id)
            tentacle.summoned_turn = self.turn
            self._summon(player, tentacle, position=position)
            self._event(
                "colossal_appendage", player=player.index,
                source=azshara.entity_id, entity=tentacle.entity_id, side=side,
            )

    def _draw(self, player: Player) -> None:
        if not player.deck:
            player.fatigue += 1
            self._damage_hero(player, player.fatigue)
            return
        card = player.deck.pop()
        self._refresh_scrappy(player)
        self._receive_drawn_card(player, card)

    def _receive_drawn_card(self, player: Player, card: CardInstance) -> None:
        if card.casts_when_drawn_damage:
            self._event(
                "casts_when_drawn", player=player.index, card=card.card_id,
                damage=card.casts_when_drawn_damage,
            )
            self._damage_hero(player, card.casts_when_drawn_damage)
            self._after_card_draw(player, card)
            self._draw(player)
            return
        if card.summoned_when_drawn:
            if len(player.board) + len(player.locations) < 7:
                card.summoned_turn = self.turn
                self._summon(player, card)
                self._event(
                    "summoned_when_drawn", player=player.index,
                    card=card.card_id, entity=card.entity_id,
                )
            else:
                self._event(
                    "summoned_when_drawn_failed", player=player.index,
                    card=card.card_id,
                )
            self._after_card_draw(player, card)
            # Cast/Summoned When Drawn cards replace themselves with a normal
            # draw, including fatigue if the deck is now empty.
            self._draw(player)
            return
        if len(player.hand) >= 10:
            self._event(
                "burn", player=player.index, card=card.card_id,
                entity=card.entity_id, started_in_deck=card.started_in_deck,
                created_by=card.created_by,
            )
        else:
            player.hand.append(card)
            self._event("draw", player=player.index, card=card.card_id)
        self._after_card_draw(player, card)

    def _after_card_draw(self, player: Player, card: CardInstance) -> None:
        opponent = self.players[1 - player.index]
        for keymaster in list(opponent.board):
            if (
                keymaster.card_id != "CORE_SCH_717"
                or keymaster.silenced
                or keymaster.dormant_turns > 0
            ):
                continue
            copied = card.clone(self.next_entity_id)
            self.next_entity_id += 1
            copied.cost_delta = 1 - copied.definition.cost
            copied.created_by = keymaster.card_id
            copied.copied_from_opponent = True
            if len(opponent.hand) < 10:
                opponent.hand.append(copied)
                self._event(
                    "keymaster_copy", player=opponent.index,
                    source=keymaster.entity_id, drawn=card.card_id,
                    copied=copied.entity_id,
                )
            else:
                self._event(
                    "generated_burned", player=opponent.index,
                    card=copied.card_id, source=keymaster.card_id,
                )
        for deceptor in list(player.board):
            if (
                deceptor.card_id != "CORE_TTN_843"
                or deceptor.silenced
                or deceptor.dormant_turns > 0
            ):
                continue
            if len(player.board) + len(player.locations) >= 7:
                break
            demon = CardInstance(
                self.next_entity_id,
                CardDef(
                    "CORE_TTN_843t", "Fel Interloper", "MINION", 1,
                    1, 1, "DEMON", ("RUSH",), "DEMONHUNTER",
                    ("DEMON",), "CORE",
                ),
                rush=True,
                summoned_turn=self.turn,
                created_by=deceptor.card_id,
            )
            self.next_entity_id += 1
            self._summon(player, demon)
            self._event(
                "eredar_deceptor_trigger", player=player.index,
                source=deceptor.entity_id, drawn=card.card_id,
                summoned=demon.entity_id,
            )

    def _draw_matching(
        self,
        player: Player,
        predicate,
        *,
        cost_delta: int = 0,
    ) -> CardInstance | None:
        candidates = [card for card in player.deck if predicate(card)]
        if not candidates:
            return None
        card = self.rng.choice(candidates)
        player.deck.remove(card)
        self._refresh_scrappy(player)
        card.cost_delta += cost_delta
        self._receive_drawn_card(player, card)
        return card

    def _start_turn(self, index: int) -> None:
        self.current = index
        self.turn += 1
        self.minions_died_this_turn = 0
        player = self.players[index]
        for owner in self.players:
            for minion in owner.board:
                expired = [
                    modifier for modifier in minion.temporary_attack_modifiers
                    if modifier[1] == index
                ]
                for amount, expiry in expired:
                    minion.attack_delta -= amount
                    minion.temporary_attack_modifiers.remove((amount, expiry))
                    self._event(
                        "temporary_attack_expire", player=owner.index,
                        entity=minion.entity_id, amount=amount,
                    )
        player.turns_taken += 1
        for owner in self.players:
            for minion in owner.board:
                if (
                    minion.card_id == "CORE_GVG_103"
                    and not minion.silenced
                    and minion.dormant_turns == 0
                ):
                    minion.attack_delta += 1
                    self._event(
                        "micro_machine", player=owner.index,
                        entity=minion.entity_id,
                    )
        opponent = self.players[1 - index]
        for alarm in list(player.board):
            candidates = [
                card for card in opponent.hand
                if card.definition.card_type == "MINION"
            ]
            if (
                alarm.card_id != "JAIL_502"
                or alarm.silenced
                or alarm.dormant_turns > 0
                or not candidates
            ):
                continue
            incoming = self.rng.choice(candidates)
            opponent.hand.remove(incoming)
            player.board.remove(alarm)
            opponent.hand.append(alarm)
            incoming.summoned_turn = self.turn
            self._summon(player, incoming)
            self._event(
                "alarm_swap", player=player.index,
                outgoing=alarm.entity_id, incoming=incoming.entity_id,
            )
        player.max_mana = min(10, player.max_mana + 1)
        player.locked_mana = min(player.max_mana, player.overload_next_turn)
        player.overload_next_turn = 0
        player.mana = player.max_mana - player.locked_mana
        if player.start_turn_temporary_mana_charges:
            player.mana += 1
            player.start_turn_temporary_mana_charges -= 1
            self._event(
                "start_turn_temporary_mana", player=player.index,
                remaining=player.start_turn_temporary_mana_charges,
            )
        player.hero_attack_bonus = 0
        player.hero_attacks_this_turn = 0
        player.hero_power_used = False
        player.fire_spell_played = False
        player.cards_played_this_turn = 0
        player.dragons_played_this_turn = 0
        player.damaged_characters_this_turn.clear()
        self._reform_nythendra(player)
        for minion in player.board:
            minion.attacks_this_turn = 0
            if (
                minion.card_id == "CATA_210"
                and not minion.silenced
                and minion.dormant_turns == 0
            ):
                minion.twilight_whelp_bonus += 1
                self._event(
                    "twilight_egg_upgrade", player=player.index,
                    entity=minion.entity_id,
                    bonus=minion.twilight_whelp_bonus,
                )
            if minion.infinite_attack_next_turn and not minion.silenced:
                minion.attack_delta = 2_147_483_647 - minion.definition.attack
                minion.infinite_attack_next_turn = False
                self._event(
                    "infinite_attack", player=index, card=minion.card_id,
                    entity=minion.entity_id,
                )
            if minion.dormant_turns > 0:
                minion.dormant_turns -= 1
                if minion.dormant_turns == 0:
                    self._event("awaken", player=index, card=minion.card_id, entity=minion.entity_id)
        for location in player.locations:
            location.cooldown = max(0, location.cooldown - 1)
        if player.geddon_draw:
            self._offer_geddon_draw(player)
        else:
            self._draw(player)
        self._event("turn_start", player=index)

    def _end_turn(self) -> None:
        player = self.players[self.current]
        for minion in list(player.board):
            if (
                minion not in player.board
                or minion.health <= 0
                or minion.dormant_turns > 0
            ):
                continue
            if minion.dies_at_end_of_turn and not minion.silenced:
                minion.damage = minion.max_health
                self._event(
                    "end_turn_destroy", player=player.index,
                    card=minion.card_id, entity=minion.entity_id,
                )
                self._resolve_deaths()
            elif minion.card_id == "CAP_107t" and not minion.silenced:
                self._fire_cannoneer(player, minion, reason="end_turn")
            elif minion.card_id == "NEW1_009" and not minion.silenced:
                healed = []
                for target in player.board:
                    if target.health > 0 and target.damage > 0:
                        amount = min(1, target.damage)
                        target.damage -= amount
                        healed.append((target.entity_id, amount))
                self._event(
                    "healing_totem", player=player.index,
                    entity=minion.entity_id, healed=healed,
                )
            elif minion.card_id == "JAIL_450t" and not minion.silenced:
                minion.damage = minion.max_health
            elif minion.card_id == "CATA_999" and not minion.silenced:
                self._damage_hero(self.players[1 - player.index], 4, minion)
            elif minion.card_id == "EDR_889" and not minion.silenced:
                dragons = [
                    other for other in player.board
                    if other.entity_id != minion.entity_id
                    and other.has_race("DRAGON")
                ]
                if dragons:
                    target = self.rng.choice(dragons)
                    target.attack_delta += 1
                    target.health_delta += 1
            elif minion.card_id == "CATA_476" and not minion.silenced:
                if len(player.board) + len(player.locations) < 7:
                    token = CardInstance(
                        self.next_entity_id,
                        CardDef(
                            "CATA_476t", "Sandscale Dragon", "MINION", 6, 6, 6,
                            "DRAGON", ("DIVINE_SHIELD",), "NEUTRAL",
                            ("ELEMENTAL", "DRAGON"),
                        ),
                        created_by=minion.card_id,
                    )
                    self.next_entity_id += 1
                    token.divine_shield = True
                    token.summoned_turn = self.turn
                    self._summon(player, token)
            elif minion.card_id == "CORE_BT_493" and not minion.silenced:
                for _ in range(6):
                    targets = self._random_enemy_characters(player.index)
                    if not targets:
                        break
                    self._deal_to_target(
                        player.index, self.rng.choice(targets), 1,
                        source=minion,
                    )
                    self._resolve_deaths()
            elif minion.card_id == "CORE_TTN_866" and not minion.silenced:
                enemy = self.players[1 - player.index]
                for attacker in list(enemy.board):
                    if minion not in player.board:
                        break
                    if attacker in enemy.board and attacker.dormant_turns == 0:
                        self._forced_minion_attack(
                            enemy.index, attacker, player.index, minion
                        )
            elif minion.card_id == "DINO_132" and not minion.silenced:
                enemy = self.players[1 - player.index]
                candidates = [
                    target for target in enemy.board
                    if target.dormant_turns == 0
                ]
                if candidates:
                    self._damage_minion(
                        enemy.index, self.rng.choice(candidates), 5, minion
                    )
                    self._resolve_deaths()
            elif minion.card_id == "EDR_810t" and not minion.silenced:
                enemy = self.players[1 - player.index]
                targets = self._random_enemy_characters(player.index)
                if targets:
                    def current_health(target: tuple[int, int | None]) -> int:
                        return (
                            self.players[target[0]].health
                            if target[1] is None
                            else self._find_minion(*target).health
                        )
                    lowest = min(current_health(target) for target in targets)
                    candidates = [
                        target for target in targets
                        if current_health(target) == lowest
                    ]
                    amount = 1 + sum(
                        husk.card_id == "EDR_810"
                        and not husk.silenced
                        and husk.dormant_turns == 0
                        for husk in player.board
                    )
                    self._steal_health(
                        player, self.rng.choice(candidates), amount
                    )
                    self._resolve_deaths()
            elif minion.card_id == "CORE_YOP_034" and not minion.silenced:
                targets = [
                    target for target in self.players[1 - player.index].board
                    if target.dormant_turns == 0
                ]
                if targets:
                    self._damage_minion(
                        1 - player.index, self.rng.choice(targets), 10, minion
                    )
            elif minion.card_id == "EDR_453" and not minion.silenced:
                enemy = self.players[1 - player.index]
                targets = [m for m in enemy.board if m.dormant_turns == 0]
                if targets:
                    target = self.rng.choice(targets)
                    excess = (
                        0 if target.divine_shield
                        else max(0, minion.attack - target.health)
                    )
                    self._damage_minion(enemy.index, target, minion.attack, minion)
                    self._damage_minion(player.index, minion, target.attack, target)
                    if excess:
                        self._damage_hero(enemy, excess, minion)
            elif minion.card_id == "CATA_150" and not minion.silenced:
                deathrattles = [
                    target for target in player.board
                    if target.entity_id != minion.entity_id
                    and not target.silenced
                    and "DEATHRATTLE" in target.definition.mechanics
                ]
                for target in deathrattles:
                    if target in player.board:
                        self._deathrattle(player, target)
                        self._resolve_deaths()
            elif minion.card_id == "TLC_623" and not minion.silenced:
                candidates = [
                    other for other in player.board
                    if other.entity_id != minion.entity_id
                    and other.damage > 0
                    and other.health > 0
                    and other.dormant_turns == 0
                ]
                if candidates:
                    target = self.rng.choice(candidates)
                    target.attack_delta += 2
                    target.health_delta += 2
                    self._event(
                        "stonecarver_buff", player=player.index,
                        source=minion.entity_id, target=target.entity_id,
                    )
            elif minion.card_id == "EDR_816" and not minion.silenced:
                for other in player.board:
                    if other.entity_id != minion.entity_id:
                        other.attack_delta += 1
            elif minion.card_id == "EDR_971" and not minion.silenced:
                for hero in self.players:
                    hero.health = min(hero.max_health, hero.health + 3)
            elif minion.card_id == "TLC_480" and not minion.silenced:
                enemy = self.players[1 - player.index]
                affected = []
                for target in enemy.board:
                    if target.dormant_turns > 0:
                        continue
                    target.attack_delta = 1 - target.definition.attack
                    target.health_delta = 1 - target.definition.health
                    target.damage = 0
                    affected.append(target.entity_id)
                self._event(
                    "krog_set_stats", player=player.index, affected=affected
                )
        self._resolve_deaths()
        # Time Skipper observes every player's end step, regardless of which
        # side controls it. Each surviving copy gives the active player a Coin.
        skippers = [
            minion
            for owner in self.players
            for minion in owner.board
            if minion.card_id == "TIME_054"
            and not minion.silenced
            and minion.dormant_turns == 0
        ]
        for skipper in skippers:
            self._give_coin(player, source=skipper.card_id)
        self._tick_burning_minions(player)
        for owner in self.players:
            while owner.pending_phoenixes > 0:
                owner.pending_phoenixes -= 1
                phoenix = self._entity("FIR_919", created_by="FIR_919")
                if len(owner.hand) < 10:
                    owner.hand.append(phoenix)
                    self._event(
                        "phoenix_return", player=owner.index,
                        entity=phoenix.entity_id,
                    )
                else:
                    self._event(
                        "generated_burned", player=owner.index,
                        card=phoenix.card_id, source="FIR_919",
                    )
        for minion in player.board:
            minion.immune = False
            # A character frozen before this turn has now missed its attack
            # opportunity and thaws. A character frozen during this same turn
            # must remain frozen through its next turn instead.
            if minion.frozen_turn >= 0 and minion.frozen_turn < self.turn:
                minion.frozen_turn = -1
        if player.frozen_turn >= 0 and player.frozen_turn < self.turn:
            player.frozen_turn = -1
        player.played_races_last_turn = set(player.played_races_this_turn)
        player.played_races_this_turn.clear()
        for card in list(player.hand):
            if card.temporary:
                player.hand.remove(card)
                self._event(
                    "temporary_expire", player=player.index,
                    card=card.card_id, entity=card.entity_id,
                )
        for controller in self.players:
            for minion in list(controller.board):
                if minion.return_control_at_end_of_turn != player.index:
                    continue
                owner = self.players[minion.return_control_to]
                controller.board.remove(minion)
                minion.return_control_to = None
                minion.return_control_at_end_of_turn = None
                if len(owner.board) + len(owner.locations) < 7:
                    owner.board.append(minion)
                    self._refresh_continuous(controller)
                    self._refresh_continuous(owner)
                    self._event(
                        "control_return", player=owner.index,
                        card=minion.card_id, entity=minion.entity_id,
                    )
                else:
                    minion.damage = minion.max_health
                    controller.board.append(minion)
                    self._event(
                        "control_return_failed", player=owner.index,
                        card=minion.card_id, entity=minion.entity_id,
                    )
                    self._resolve_deaths()
        self._event("turn_end", player=self.current)
        self._start_turn(1 - self.current)

    def _fire_cannoneer(
        self, player: Player, minion: CardInstance, *, reason: str
    ) -> None:
        extra_shots = sum(
            captain.card_id == "CAP_106"
            and not captain.silenced
            and captain.dormant_turns == 0
            and captain.health > 0
            for captain in player.board
        )
        for _ in range(1 + extra_shots):
            targets = self._random_enemy_characters(player.index)
            if not targets:
                break
            target = self.rng.choice(targets)
            target_card = (
                None if target[1] is None
                else self._find_minion(*target).card_id
            )
            self._event(
                "cannoneer_shot", player=player.index,
                card=minion.card_id, entity=minion.entity_id,
                target_player=target[0], target_entity=target[1],
                target_card=target_card, amount=1, reason=reason,
            )
            self._deal_to_target(player.index, target, 1, source=minion)
            self._resolve_deaths()

    def _effective_cost(self, player: Player, card: CardInstance) -> int:
        cost = card.cost
        cost += self.rule_registry.cost_adjustment(self, player, card)
        if (
            card.definition.card_type == "MINION"
            and player.minion_cost_increase_turn == self.turn
        ):
            cost += player.minion_cost_increase_amount
        if card.definition.card_type == "MINION":
            cost += 2 * sum(
                minion.card_id == "JAIL_890"
                and not minion.silenced
                and minion.dormant_turns == 0
                for owner in self.players for minion in owner.board
            )
        if card.card_id == "TLC_600" and "DRAGON" in player.played_races_last_turn:
            cost -= 3
        if card.card_id == "END_033" and any(
            other.entity_id != card.entity_id and other.has_race("DRAGON")
            for other in player.hand
        ):
            cost -= 3
        if card.card_id == "CORE_NEW1_022" and player.weapon:
            cost -= player.weapon.attack
        if card.card_id == "DINO_409":
            cost -= player.generated_cards_played
        if card.card_id == "FIR_919":
            cost -= player.cards_played_this_turn
        if card.card_id == "END_004":
            cost -= self.minions_died_this_turn
        if card.card_id == "END_030":
            cost -= player.overloaded_mana_this_game
        if (
            card.has_race("DRAGON")
            and player.dragons_played_this_turn == 0
            and any(
                minion.card_id == "EDR_844"
                and not minion.silenced
                and minion.dormant_turns == 0
                for minion in player.board
            )
        ):
            cost = 1
        if (
            card.definition.card_type == "SPELL"
            and card.definition.spell_school == "ARCANE"
            and any(
                minion.card_id == "TIME_852"
                and not minion.silenced
                and minion.dormant_turns == 0
                and any(
                    other.entity_id != minion.entity_id
                    and other.has_race("DRAGON")
                    and other.dormant_turns == 0
                    for other in player.board
                )
                for minion in player.board
            )
        ):
            cost -= 2
        if card.has_race("DEMON") and player.next_demon_free:
            cost = 0
        return max(0, cost)

    def _overload(self, player: Player, amount: int) -> None:
        if amount <= 0:
            return
        player.overload_next_turn += amount
        player.overloaded_mana_this_game += amount
        self._event(
            "overload", player=player.index, amount=amount,
            total=player.overloaded_mana_this_game,
        )

    def _reform_nythendra(self, player: Player) -> None:
        beetles = [m for m in player.board if m.card_id == "EDR_818t"]
        if not beetles or not any(not beetle.silenced for beetle in beetles):
            return
        for beetle in beetles:
            player.board.remove(beetle)
        count = len(beetles)
        nythendra = self._entity("EDR_818", created_by="EDR_818t")
        nythendra.attack_delta = count - nythendra.definition.attack
        nythendra.health_delta = count - nythendra.definition.health
        nythendra.summoned_turn = self.turn
        self._summon(player, nythendra)
        self._event(
            "nythendra_reform", player=player.index,
            entity=nythendra.entity_id, beetles=count,
        )

    def _refresh_scrappy(self, player: Player) -> None:
        bonus = 5 if len(player.deck) >= 25 else 0
        for minion in player.board:
            if minion.card_id == "JAIL_311":
                minion.deck_threshold_attack = bonus

    def _refresh_continuous(self, player: Player) -> None:
        self._refresh_scrappy(player)
        player.hero_board_attack_bonus = sum(
            minion.card_id == "JAIL_202"
            and not minion.silenced
            and minion.dormant_turns == 0
            for minion in player.board
        ) if player.index == self.current else 0
        captains = sum(
            minion.card_id == "CORE_NEW1_027"
            and not minion.silenced
            and minion.dormant_turns == 0
            and minion.health > 0
            for minion in player.board
        )
        active = [
            minion for minion in player.board
            if not minion.silenced
            and minion.dormant_turns == 0
            and minion.health > 0
        ]
        raid_leaders = sum(m.card_id == "CORE_CS2_122" for m in active)
        champions = sum(m.card_id == "CORE_CS2_222" for m in active)
        warleaders = sum(m.card_id == "CORE_EX1_507" for m in active)
        arachnathids = sum(m.card_id == "JAIL_459" for m in active)
        toreth_active = any(m.card_id == "EDR_258" for m in active)
        dire_wolf_neighbors: dict[int, int] = {}
        for index, source in enumerate(player.board):
            if source not in active or source.card_id != "CORE_EX1_162":
                continue
            for neighbor_index in (index - 1, index + 1):
                if 0 <= neighbor_index < len(player.board):
                    neighbor = player.board[neighbor_index]
                    if neighbor.dormant_turns > 0 or neighbor.health <= 0:
                        continue
                    dire_wolf_neighbors[neighbor.entity_id] = (
                        dire_wolf_neighbors.get(neighbor.entity_id, 0) + 1
                    )
        for minion in player.board:
            minion.pirate_aura_stats = (
                captains
                - int(minion.card_id == "CORE_NEW1_027" and not minion.silenced)
                if minion.has_race("PIRATE")
                else 0
            )
            minion.weapon_attack_bonus = (
                2
                if minion.card_id == "CORE_WON_351"
                and not minion.silenced
                and player.weapon is not None
                else 0
            )
            if minion.dormant_turns == 0 and minion.health > 0:
                minion.aura_attack_bonus = (
                    raid_leaders
                    - int(minion.card_id == "CORE_CS2_122" and minion in active)
                    + champions
                    - int(minion.card_id == "CORE_CS2_222" and minion in active)
                    + (
                        2 * (
                            warleaders
                            - int(minion.card_id == "CORE_EX1_507" and minion in active)
                        )
                        if minion.has_race("MURLOC") else 0
                    )
                    + dire_wolf_neighbors.get(minion.entity_id, 0)
                )
                minion.aura_health_bonus = (
                    champions
                    - int(minion.card_id == "CORE_CS2_222" and minion in active)
                )
            else:
                minion.aura_attack_bonus = 0
                minion.aura_health_bonus = 0
            minion.aura_poisonous = bool(
                arachnathids
                and minion.dormant_turns == 0
                and minion.health > 0
            )
            if minion.card_id == "CATA_613":
                minion.immune = (
                    minion in active
                    and not any(
                        other.entity_id != minion.entity_id
                        and other.dormant_turns == 0
                        and other.health > 0
                        for other in player.board
                    )
                )
            if minion.divine_shield:
                if toreth_active and not minion.divine_shield_toreth:
                    minion.divine_shield_hits = 3
                    minion.divine_shield_toreth = True
                elif not toreth_active and minion.divine_shield_toreth:
                    minion.divine_shield_hits = min(1, minion.divine_shield_hits)
                    minion.divine_shield_toreth = False
                elif minion.divine_shield_hits <= 0:
                    minion.divine_shield_hits = 1
            else:
                minion.divine_shield_hits = 0
                minion.divine_shield_toreth = False
        if player.hero_divine_shield:
            if toreth_active and not player.hero_divine_shield_toreth:
                player.hero_divine_shield_hits = 3
                player.hero_divine_shield_toreth = True
            elif not toreth_active and player.hero_divine_shield_toreth:
                player.hero_divine_shield_hits = min(
                    1, player.hero_divine_shield_hits
                )
                player.hero_divine_shield_toreth = False
            elif player.hero_divine_shield_hits <= 0:
                player.hero_divine_shield_hits = 1
        else:
            player.hero_divine_shield_hits = 0
            player.hero_divine_shield_toreth = False

        active_ido = any(minion.card_id == "TLC_241" for minion in active)
        ido_spells = [card for card in player.hand if card.card_id == "TLC_241t"]
        if active_ido and not ido_spells and len(player.hand) < 10:
            spell = self._entity("TLC_241t", created_by="TLC_241")
            player.hand.append(spell)
            self._event(
                "ido_spell_available", player=player.index, entity=spell.entity_id
            )
        elif not active_ido and ido_spells:
            player.hand[:] = [
                card for card in player.hand if card.card_id != "TLC_241t"
            ]
            self._event("ido_spell_removed", player=player.index)
        if len(player.board) + len(player.locations) >= 7:
            for minion in player.board:
                if minion.card_id == "MEND_040" and minion.dormant_turns > 0:
                    minion.dormant_turns = 0
                    self._event(
                        "awaken", player=player.index, card=minion.card_id,
                        entity=minion.entity_id,
                    )

    def _spend_mana(self, player: Player, amount: int) -> None:
        before = player.mana
        player.mana -= amount
        if amount > 0:
            for held in player.hand:
                held.mana_spent_while_held += amount
        if amount <= 0 or before <= 0 or player.mana != 0:
            return
        for cub in player.board:
            if (
                cub.card_id == "CATA_130"
                and not cub.silenced
                and cub.dormant_turns == 0
            ):
                cub.attack_delta += 1
                cub.health_delta += 1
                self._event(
                    "last_mana_spent", player=player.index,
                    entity=cub.entity_id,
                )

    def _give_coin(self, player: Player, *, source: str) -> None:
        if len(player.hand) >= 10:
            self._event("generated_burned", player=player.index, card="GAME_005", source=source)
            return
        coin = self._entity("GAME_005", created_by=source)
        player.hand.append(coin)
        self._event("coin_given", player=player.index, source=source, entity=coin.entity_id)

    def _tick_burning_minions(self, player: Player) -> None:
        for card in list(player.hand):
            if card.burning_turns and card.burning_applied_turn < self.turn:
                card.burning_turns -= 1
                if card.burning_turns == 0:
                    player.hand.remove(card)
                    self._event(
                        "burning_destroyed", player=player.index,
                        card=card.card_id, zone="hand",
                    )
        for minion in list(player.board):
            if minion.burning_turns and minion.burning_applied_turn < self.turn:
                minion.burning_turns -= 1
                if minion.burning_turns == 0:
                    minion.damage = minion.max_health
                    self._event(
                        "burning_destroyed", player=player.index,
                        card=minion.card_id, zone="board",
                    )
        self._resolve_deaths()

    def _friendly_characters(self, player_index: int) -> list[tuple[int, int | None]]:
        player = self.players[player_index]
        return [(player_index, None)] + [
            (player_index, m.entity_id) for m in player.board if m.dormant_turns == 0
        ]

    def _enemy_characters(self, player_index: int) -> list[tuple[int, int | None]]:
        enemy = self.players[1 - player_index]
        return [(enemy.index, None)] + [
            (enemy.index, minion.entity_id)
            for minion in enemy.board
            if minion.dormant_turns == 0 and not minion.stealth
        ]

    def _random_enemy_characters(
        self, player_index: int
    ) -> list[tuple[int, int | None]]:
        """Random effects can hit Stealth enemies; Dormant is not a character."""
        enemy = self.players[1 - player_index]
        return [(enemy.index, None)] + [
            (enemy.index, minion.entity_id)
            for minion in enemy.board
            if minion.dormant_turns == 0
        ]

    def _has_taunt(self, owner_index: int, minion: CardInstance) -> bool:
        if minion.taunt:
            return True
        opponent = self.players[1 - owner_index]
        return any(
            aura.card_id == "CATA_898"
            and not aura.silenced
            and aura.dormant_turns == 0
            for aura in opponent.board
        )

    @staticmethod
    def _ignores_taunt(player: Player) -> bool:
        return any(
            minion.card_id == "CORE_BT_187"
            and not minion.silenced
            and minion.dormant_turns == 0
            and minion.health > 0
            for minion in player.board
        )

    def _spell_damage(self, player: Player) -> int:
        dynamic_seer_damage = sum(
            2 for minion in player.board
            if minion.card_id == "END_022"
            and minion.damage > 0
            and not minion.silenced
            and minion.dormant_turns == 0
        )
        generic_damage = sum(
            minion.spell_damage_bonus
            for minion in player.board
            if not minion.silenced and minion.dormant_turns == 0
        )
        return dynamic_seer_damage + generic_damage

    def _hero_power_cost(self, player: Player) -> int:
        if player.hero_power_id is not None:
            return self.card_defs[player.hero_power_id].cost
        free = any(
            minion.card_id == "TIME_606"
            and not minion.silenced
            and minion.dormant_turns == 0
            for minion in player.board
        ) and len(player.hand) <= 3
        if free:
            return 0
        if player.hero_power_cost_override is not None:
            return player.hero_power_cost_override
        return 1 if player.card_class == "DEMONHUNTER" else 2

    def _hero_power_actions(self, player: Player) -> list[Action]:
        if player.hero_power_id is not None:
            target_spec = self.rule_registry.targeting(player.hero_power_id)
            if target_spec is None:
                return [Action("HERO_POWER")]
            card = CardInstance(-1, self.card_defs[player.hero_power_id])
            return [
                Action("HERO_POWER", target_player=owner, target_entity=entity)
                for owner, entity in self._rule_targets(player, card, target_spec.kind)
            ]
        card_class = player.card_class
        if card_class in {"MAGE", "PRIEST"}:
            targets = self._friendly_characters(player.index)
            targets.extend(self._enemy_characters(player.index))
            return [Action("HERO_POWER", target_player=p, target_entity=e)
                    for p, e in targets]
        if card_class == "PALADIN":
            return ([Action("HERO_POWER")]
                    if len(player.board) + len(player.locations) < 7 else [])
        if card_class == "SHAMAN":
            controlled = {m.card_id for m in player.board}
            available = set(BASIC_TOTEM_IDS) - controlled
            return ([Action("HERO_POWER")]
                    if available and len(player.board) + len(player.locations) < 7
                    else [])
        if card_class == "DEATHKNIGHT":
            return ([Action("HERO_POWER")]
                    if len(player.board) + len(player.locations) < 7 else [])
        return [Action("HERO_POWER")]

    def _use_hero_power(self, action: Action) -> None:
        player = self.players[self.current]
        self._spend_mana(player, self._hero_power_cost(player))
        player.hero_power_used = True
        if player.hero_power_id is not None:
            card = CardInstance(-1, self.card_defs[player.hero_power_id])
            if not self.rule_registry.dispatch(
                Hook.HERO_POWER, card.card_id, self,
                RuleContext(player=player, card=card, action=action),
            ):
                raise UnsupportedGeneratedCard(
                    f"hero power has no executable rule: {card.card_id}"
                )
            self._event(
                "hero_power", player=player.index, card_id=card.card_id,
                target_player=action.target_player,
                target_entity=action.target_entity,
            )
            return
        card_class = player.card_class
        if card_class == "WARRIOR":
            self._gain_armor(player, player.hero_power_armor)
        elif card_class == "MAGE":
            self._deal_to_target(
                player.index,
                (action.target_player, action.target_entity),
                1,
            )
        elif card_class == "PRIEST":
            if action.target_entity is None:
                target = self.players[action.target_player]
                target.health = min(target.max_health, target.health + 2)
            else:
                target = self._find_minion(
                    action.target_player, action.target_entity
                )
                target.damage = max(0, target.damage - 2)
        elif card_class == "HUNTER":
            self._damage_hero(self.players[1 - player.index], 2)
        elif card_class == "PALADIN":
            recruit = self._entity("CS2_101t", created_by="HERO_04bp")
            recruit.summoned_turn = self.turn
            self._summon(player, recruit)
        elif card_class == "ROGUE":
            self._equip_weapon(player, Weapon("CS2_082", "Wicked Knife", 1, 2))
        elif card_class == "DRUID":
            player.hero_attack_bonus += 1
            self._gain_armor(player, 1)
        elif card_class == "SHAMAN":
            controlled = {m.card_id for m in player.board}
            choices = [card_id for card_id in BASIC_TOTEM_IDS
                       if card_id not in controlled]
            totem = self._entity(self.rng.choice(choices), created_by="HERO_02bp")
            totem.summoned_turn = self.turn
            self._summon(player, totem)
        elif card_class == "WARLOCK":
            self._draw(player)
            self._damage_hero(player, 2)
        elif card_class == "DEMONHUNTER":
            player.hero_attack_bonus += 1
        elif card_class == "DEATHKNIGHT":
            ghoul = self._entity("HERO_11bpt", created_by="HERO_11bp")
            ghoul.summoned_turn = self.turn
            self._summon(player, ghoul)
        else:
            raise ValueError(f"unsupported hero class: {card_class}")
        self._event(
            "hero_power", player=player.index, card_class=card_class,
            target_player=action.target_player,
            target_entity=action.target_entity,
        )
        for minion in player.board:
            if minion.card_id == "EDR_469" and minion.dormant_turns > 0:
                minion.dormant_turns = 0
                self._event(
                    "awaken", player=player.index, card=minion.card_id,
                    entity=minion.entity_id,
                )
        for dragonbane in list(player.board):
            if (
                dragonbane.card_id == "CORE_DRG_256"
                and not dragonbane.silenced
                and dragonbane.dormant_turns == 0
            ):
                targets = self._random_enemy_characters(player.index)
                if targets:
                    self._deal_to_target(
                        player.index, self.rng.choice(targets), 5,
                        source=dragonbane,
                    )
                    self._event(
                        "dragonbane", player=player.index,
                        entity=dragonbane.entity_id,
                    )

    def _refresh_genn(self, player: Player) -> None:
        for held in player.hand:
            if held.card_id not in {"CATA_615", "CATA_615t"}:
                continue
            others = [card for card in player.hand if card.entity_id != held.entity_id]
            all_even = all(card.cost % 2 == 0 for card in others)
            all_odd = all(card.cost % 2 == 1 for card in others)
            wanted = "CATA_615t" if all_even or all_odd else "CATA_615"
            if held.card_id != wanted:
                held.definition = self.card_defs[wanted]
                self._event(
                    "genn_transform", player=player.index,
                    entity=held.entity_id, card=wanted,
                )

    @staticmethod
    def _hero_max_attacks(player: Player) -> int:
        windfury = any(
            minion.card_id == "CATA_151"
            and not minion.silenced
            and minion.dormant_turns == 0
            and minion.health > 0
            for minion in player.board
        )
        return 2 if windfury else 1

    def _all_minions(self) -> list[tuple[int, int]]:
        return [
            (p.index, m.entity_id)
            for p in self.players for m in p.board
            if m.dormant_turns == 0
        ]

    def _find_minion(self, player_index: int, entity_id: int) -> CardInstance:
        for minion in self.players[player_index].board:
            if minion.entity_id == entity_id:
                return minion
        raise ValueError("minion not found")

    def _rule_targets(
        self, player: Player, card: CardInstance, target_kind: TargetKind
    ) -> list[tuple[int, int | None]]:
        friendly_minions = [
            (player.index, minion.entity_id)
            for minion in player.board if minion.dormant_turns == 0
        ]
        enemy = self.players[1 - player.index]
        enemy_minions = [
            (enemy.index, minion.entity_id)
            for minion in enemy.board
            if minion.dormant_turns == 0
            and not minion.stealth
            and not (
                card.definition.card_type == "SPELL" and minion.elusive
            )
        ]
        if target_kind == TargetKind.FRIENDLY_MINION:
            return friendly_minions
        if target_kind == TargetKind.ENEMY_MINION:
            return enemy_minions
        if target_kind == TargetKind.ANY_MINION:
            return friendly_minions + enemy_minions
        if target_kind == TargetKind.FRIENDLY_CHARACTER:
            return [(player.index, None)] + friendly_minions
        if target_kind == TargetKind.ENEMY_CHARACTER:
            return [(enemy.index, None)] + enemy_minions
        if target_kind == TargetKind.ANY_CHARACTER:
            return (
                [(player.index, None)] + friendly_minions
                + [(enemy.index, None)] + enemy_minions
            )
        raise ValueError(f"unsupported target kind: {target_kind}")

    def legal_actions(self) -> list[Action]:
        if self.finished:
            return []
        if self.pending_choice:
            if self.pending_choice["kind"] == "MULLIGAN":
                return [
                    Action("MULLIGAN_TOGGLE", entity_id)
                    for entity_id in self.pending_choice["options"]
                ] + [Action("MULLIGAN_CONFIRM")]
            if self.pending_choice["kind"] in {
                "DISCOVER", "GEDDON_DRAW", "DECK_DISCOVER", "DECK_CARD_DISCOVER",
                "IMBUE_PICK",
            }:
                return [
                    Action("DISCOVER_PICK", option.entity_id)
                    for option in self.pending_choice["options"]
                ]
            if self.pending_choice["kind"] == "REWIND":
                return [Action("REWIND_KEEP"), Action("REWIND_RETRY")]
            if self.pending_choice["kind"] == "AMMUNITION":
                return [
                    Action("AMMUNITION_PICK", option)
                    for option in self.pending_choice["options"]
                ]
            if self.pending_choice["kind"] == "CORPSE_SPEND":
                return [
                    Action("CORPSE_SPEND", option)
                    for option in self.pending_choice["options"]
                ]
            if self.pending_choice["kind"] == "RULE_CHOICE":
                return [
                    Action("RULE_CHOICE_PICK", index)
                    for index in range(len(self.pending_choice["options"]))
                ]
        player = self.players[self.current]
        self._refresh_genn(player)
        for candidate in self.players:
            self._refresh_continuous(candidate)
        actions = [Action("END_TURN")]
        for card in player.hand:
            if "Prepare" in card.definition.text and card.prepared_turn != self.turn:
                actions.append(Action("PREPARE", card.entity_id))
            if card.prepared_turn == self.turn:
                continue
            effective_cost = self._effective_cost(player, card)
            if card.card_id == "TLC_436":
                if effective_cost > player.corpses:
                    continue
            elif effective_cost > player.mana:
                continue
            if (
                card.definition.card_type in {"MINION", "LOCATION"}
                and len(player.board) + len(player.locations) >= 7
                and card.card_id != "JAIL_455"
            ):
                continue
            targets: list[tuple[int, int | None]] | None = None
            target_spec = self.rule_registry.targeting(card.card_id)
            if target_spec is not None:
                targets = self._rule_targets(player, card, target_spec.kind)
                if target_spec.optional:
                    targets = [(None, None), *targets]
            elif card.card_id == "CORE_SW_066":
                targets = [
                    target for target in self._all_minions()
                    if target[0] == self.current
                    or not self._find_minion(*target).stealth
                ]
            elif card.card_id in {"CATA_200", "CATA_490"}:
                targets = [
                    (self.current, held.entity_id) for held in player.hand
                    if held.entity_id != card.entity_id
                ] or [(None, None)]
            elif card.card_id == "CORE_ULD_165":
                targets = [
                    target for target in self._all_minions()
                    if target[0] == self.current
                    or not self._find_minion(*target).stealth
                ] or [(None, None)]
            elif card.card_id == "TIME_043":
                targets = [
                    (self.current, minion.entity_id)
                    for minion in player.board
                    if minion.dormant_turns == 0
                ] or [(None, None)]
            elif card.card_id in {"FIR_939", "TLC_600", "CATA_464t"}:
                targets = self._friendly_characters(self.current) + self._enemy_characters(self.current)
                if card.card_id in {"FIR_939", "CATA_464t"}:
                    targets = [
                        target for target in targets
                        if target[1] is None
                        or target[0] == self.current
                        or not self._find_minion(*target).elusive
                    ]
            elif card.card_id == "CORE_UNG_084":
                targets = [
                    target for target in (
                    self._friendly_characters(self.current)
                    + self._enemy_characters(self.current)
                    )
                    if target[1] is None
                    or target[0] == self.current
                    or not self._find_minion(*target).stealth
                ]
            elif card.card_id == "CATA_585":
                targets = [
                    (p.index, m.entity_id)
                    for p in self.players for m in p.board
                    if m.damage > 0 and m.dormant_turns == 0
                    and (
                        p.index == self.current
                        or (not m.elusive and not m.stealth)
                    )
                ]
            elif card.card_id == "TLC_813":
                targets = [
                    target for target in self._all_minions()
                    if target[0] == self.current
                    or not self._find_minion(*target).stealth
                ]
            elif card.card_id == "TLC_241t":
                targets = [
                    target for target in self._all_minions()
                    if target[0] == self.current
                    or (
                        not self._find_minion(*target).elusive
                        and not self._find_minion(*target).stealth
                    )
                ]
            elif card.card_id == "CORE_EX1_002":
                targets = [
                    (1 - self.current, minion.entity_id)
                    for minion in self.players[1 - self.current].board
                    if minion.dormant_turns == 0
                    and not minion.stealth
                    and self._has_taunt(1 - self.current, minion)
                ] or [(None, None)]
            elif card.card_id == "EX1_014t":
                targets = [
                    target for target in self._all_minions()
                    if target[0] == self.current
                    or (
                        not self._find_minion(*target).elusive
                        and not self._find_minion(*target).stealth
                    )
                ]
            elif card.card_id == "EDR_468":
                targets = [
                    target for target in self._all_minions()
                    if target[0] == self.current
                    or not self._find_minion(*target).stealth
                ] or [(None, None)]
            elif card.card_id == "TLC_606":
                targets = [
                    (1 - self.current, minion.entity_id)
                    for minion in self.players[1 - self.current].board
                    if minion.dormant_turns == 0 and not minion.stealth
                ] or [(None, None)]
            elif card.card_id == "CORE_BT_120":
                targets = [
                    (1 - self.current, minion.entity_id)
                    for minion in self.players[1 - self.current].board
                    if minion.dormant_turns == 0 and not minion.stealth
                ] or [(None, None)]
            elif card.card_id == "JAIL_455":
                targets = [
                    (candidate.index, None)
                    for candidate in self.players
                    if len(candidate.board) + len(candidate.locations) < 7
                ]
            elif card.card_id == "CS3_022" and player.weapon is not None:
                targets = (
                    self._friendly_characters(self.current)
                    + self._enemy_characters(self.current)
                )
            if targets is None:
                actions.append(Action("PLAY", card.entity_id))
            else:
                actions.extend(Action("PLAY", card.entity_id, p, e) for p, e in targets)
            if "TRADEABLE" in card.definition.mechanics and player.mana >= 1 and player.deck:
                actions.append(Action("TRADE", card.entity_id))
        for minion in player.board:
            if minion.dormant_turns > 0:
                continue
            max_attacks = 2 if minion.windfury else 1
            ready = minion.summoned_turn < self.turn or minion.charge or minion.rush
            if (
                not ready
                or minion.attacks_this_turn >= max_attacks
                or minion.attack <= 0
                or minion.frozen_turn >= 0
                or minion.cant_attack
                or minion.cant_attack_turn == self.turn
            ):
                continue
            enemy = self.players[1 - self.current]
            awake_enemy = [
                m for m in enemy.board
                if m.dormant_turns == 0 and not m.stealth
            ]
            taunts = [m for m in awake_enemy if self._has_taunt(enemy.index, m)]
            ignore_taunt = self._ignores_taunt(player)
            target_minions = awake_enemy if ignore_taunt else (taunts or awake_enemy)
            actions.extend(Action("ATTACK", minion.entity_id, enemy.index, m.entity_id) for m in target_minions)
            if (
                (not taunts or ignore_taunt)
                and (minion.summoned_turn < self.turn or minion.charge)
                and minion.cant_attack_heroes_turn != self.turn
            ):
                actions.append(Action("ATTACK", minion.entity_id, enemy.index, None))
        if (
            player.attack > 0
            and player.hero_attacks_this_turn < self._hero_max_attacks(player)
            and player.frozen_turn < 0
        ):
            enemy = self.players[1 - self.current]
            awake_enemy = [
                m for m in enemy.board
                if m.dormant_turns == 0 and not m.stealth
            ]
            taunts = [m for m in awake_enemy if self._has_taunt(enemy.index, m)]
            if taunts and not self._ignores_taunt(player):
                actions.extend(Action("HERO_ATTACK", None, enemy.index, m.entity_id) for m in taunts)
            else:
                if not player.weapon or player.weapon.card_id not in {
                    "CORE_LOOT_044", "END_012",
                }:
                    actions.append(Action("HERO_ATTACK", None, enemy.index, None))
                actions.extend(Action("HERO_ATTACK", None, enemy.index, m.entity_id) for m in awake_enemy)
        if player.mana >= self._hero_power_cost(player) and not player.hero_power_used:
            actions.extend(self._hero_power_actions(player))
        for location in player.locations:
            if location.cooldown == 0 and location.durability > 0:
                if location.card_id == "CORE_REV_990":
                    targets = [
                        target for target in self._all_minions()
                        if target[0] == self.current
                        or not self._find_minion(*target).stealth
                    ]
                    actions.extend(
                        Action("LOCATION", location.entity_id, p, e)
                        for p, e in targets
                    )
                elif location.card_id == "CATA_584":
                    actions.append(Action("LOCATION", location.entity_id))
                elif self.rule_registry.has_hook(Hook.LOCATION, location.card_id):
                    actions.append(Action("LOCATION", location.entity_id))
        return sorted(actions, key=Action.key)

    def step(self, action: Action) -> None:
        legal = {a.key(): a for a in self.legal_actions()}
        if action.key() not in legal:
            self.invalid_actions += 1
            raise ValueError(f"illegal action: {action}")
        action = legal[action.key()]
        if action.kind == "END_TURN":
            self._end_turn()
        elif action.kind == "MULLIGAN_TOGGLE":
            self._toggle_mulligan(action.source)
        elif action.kind == "MULLIGAN_CONFIRM":
            self._confirm_mulligan()
        elif action.kind == "TRADE":
            self._trade(action.source)
        elif action.kind == "PLAY":
            self._play(action)
        elif action.kind == "PREPARE":
            self._prepare(action.source)
        elif action.kind == "ATTACK":
            self._attack(action)
        elif action.kind == "HERO_ATTACK":
            self._hero_attack(action)
        elif action.kind == "LOCATION":
            self._use_location(action)
        elif action.kind == "HERO_POWER":
            self._use_hero_power(action)
        elif action.kind == "DISCOVER_PICK":
            self._resolve_discover(action.source)
        elif action.kind == "REWIND_KEEP":
            self._resolve_rewind(False)
        elif action.kind == "REWIND_RETRY":
            self._resolve_rewind(True)
        elif action.kind == "AMMUNITION_PICK":
            self._resolve_ammunition(action.source)
        elif action.kind == "CORPSE_SPEND":
            self._resolve_corpse_spend(action.source)
        elif action.kind == "RULE_CHOICE_PICK":
            self._resolve_rule_choice(action.source)
        self._resolve_deaths()
        self._check_winner()

    def _resolve_rule_choice(self, option_index: int | None) -> None:
        pending = self.pending_choice
        if pending is None or pending["kind"] != "RULE_CHOICE":
            raise ValueError("no rule choice is pending")
        if option_index is None or not 0 <= option_index < len(pending["options"]):
            raise ValueError("invalid rule choice")
        label, effects = pending["options"][option_index]
        player = self.players[pending["player"]]
        card = pending["card"]
        self.pending_choice = None
        context = RuleContext(player=player, card=card)
        for effect in effects:
            effect.execute(self, context)
        self._event(
            "rule_choice_pick", player=player.index, card=card.card_id,
            option=label,
        )

    def _prepare(self, entity_id: int | None) -> None:
        player = self.players[self.current]
        card = next(card for card in player.hand if card.entity_id == entity_id)
        spent = player.mana
        player.mana = 0
        card.cost_delta -= spent + 1
        card.prepared_turn = self.turn
        self._event(
            "prepare", player=player.index, card=card.card_id,
            entity=card.entity_id, spent=spent, discount=spent + 1,
        )

    def _pop_hand(self, player: Player, entity_id: int) -> CardInstance:
        for i, card in enumerate(player.hand):
            if card.entity_id == entity_id:
                return player.hand.pop(i)
        raise ValueError("card not in hand")

    def _trade(self, entity_id: int) -> None:
        player = self.players[self.current]
        card = self._pop_hand(player, entity_id)
        self._spend_mana(player, 1)
        player.deck.insert(self.rng.randrange(len(player.deck) + 1), card)
        self._draw(player)
        self._event("trade", player=player.index, card=card.card_id)

    def _play(self, action: Action) -> None:
        player = self.players[self.current]
        self._refresh_genn(player)
        # Dynamic costs are evaluated while the card is still in hand.  This
        # matters for effects such as "costs (1) less for each card in your
        # hand", where the card itself is counted by the live client.
        held = next(card for card in player.hand if card.entity_id == action.source)
        effective_cost = self._effective_cost(player, held)
        card = self._pop_hand(player, action.source)
        if card.card_id == "TLC_436":
            player.corpses -= effective_cost
            self._event(
                "spend_corpses", player=player.index,
                card=card.card_id, amount=effective_cost,
            )
        else:
            self._spend_mana(player, effective_cost)
        if card.has_race("DEMON") and player.next_demon_free:
            player.next_demon_free = False
            self._event(
                "demon_discount_consumed", player=player.index,
                card=card.card_id,
            )
        controller = (
            self.players[action.target_player]
            if card.card_id == "JAIL_455" and action.target_player is not None
            else player
        )
        self._event(
            "play", player=player.index, card=card.card_id,
            controller=controller.index, entity=card.entity_id,
            started_in_deck=card.started_in_deck,
            created_by=card.created_by,
        )
        player.cards_played_this_turn += 1
        if not card.started_in_deck:
            player.generated_cards_played += 1
        if card.copied_from_opponent:
            for held in player.hand:
                held.opponent_card_copy_played_while_held = True
            self._event(
                "opponent_card_copy_played", player=player.index,
                card=card.card_id, entity=card.entity_id,
            )
        if card.definition.card_type == "MINION":
            for held in player.hand:
                held.minion_played_while_held = True
            maievs = [
                minion for minion in player.board
                if minion.card_id == "JAIL_850"
                and not minion.silenced
                and minion.dormant_turns == 0
            ]
            card.summoned_turn = self.turn
            card.played_turn = self.turn
            card.mirrex_tracker = False
            if card.card_id == "TIME_063":
                card.dormant_turns = 5
            self._summon(controller, card)
            self._update_mirrex_trackers(self.players[1 - player.index], card)
            if "DEATHRATTLE" in card.definition.mechanics and any(
                minion.entity_id != card.entity_id
                and minion.card_id == "JAIL_880"
                and not minion.silenced
                and minion.dormant_turns == 0
                for minion in controller.board
            ):
                card.rush = True
                self._event(
                    "black_market_rush", player=controller.index,
                    entity=card.entity_id,
                )
            player.played_races_this_turn.update(card.definition.races)
            if card.definition.race:
                player.played_races_this_turn.add(card.definition.race)
            if card.has_race("DRAGON"):
                player.dragons_played_this_turn += 1
            if card.card_id == "CATA_150":
                self._summon_ragnaros_hands(controller, source=card.card_id)
            if card.card_id == "CATA_550":
                controller.pending_magmaw_bodies += 99
                controller.magmaw_entity = card.entity_id
                self._summon_magmaw_bodies(controller)
            self._battlecry(controller, card, action)
            if card.living_nightmare and len(controller.board) + len(controller.locations) < 7:
                token = card.clone(self.next_entity_id)
                self.next_entity_id += 1
                token.attack_delta = 2 - token.definition.attack
                token.health_delta = 2 - token.definition.health
                token.summoned_turn = self.turn
                self._summon(controller, token)
            if card.has_race("ELEMENTAL"):
                for vapor in controller.board:
                    if (
                        vapor.entity_id != card.entity_id
                        and vapor.card_id == "CORE_WC_042"
                        and not vapor.silenced
                        and vapor.dormant_turns == 0
                    ):
                        vapor.attack_delta += 1
                        self._event(
                            "wailing_vapor_trigger", player=controller.index,
                            entity=vapor.entity_id, played=card.card_id,
                        )
            # "After you play" triggers resolve after the played minion's
            # Battlecry. The newly played Raptor does not trigger itself, and
            # Raptors removed during Battlecry resolution cannot trigger.
            if card in controller.board:
                raptors = [
                    minion for minion in controller.board
                    if minion.entity_id != card.entity_id
                    and minion.card_id == "EDR_849"
                    and not minion.silenced
                    and minion.dormant_turns == 0
                ]
                for raptor in raptors:
                    self._grant_bonus_effect(
                        controller, card, source=raptor.card_id
                    )
                for maiev in maievs:
                    if maiev not in player.board:
                        continue
                    card.attack_delta += 3
                    card.health_delta += 3
                    card.dormant_turns = max(card.dormant_turns, 1)
                    self._event(
                        "warden_maiev_trigger", player=controller.index,
                        source=maiev.entity_id, target=card.entity_id,
                    )
            self._refresh_continuous(controller)
        elif card.definition.card_type == "LOCATION":
            player.locations.append(Location(card.entity_id, card.card_id, card.definition.health, 1))
        else:
            lorewalkers = []
            if card.definition.card_type == "SPELL":
                lorewalkers = [
                    minion for owner in self.players for minion in owner.board
                    if minion.card_id == "CORE_EX1_100"
                    and not minion.silenced
                    and minion.dormant_turns == 0
                ]
            self._cast_spell(player, card, action)
            recipient = self.players[1 - player.index]
            for lorewalker in lorewalkers:
                copied = card.clone(self.next_entity_id)
                self.next_entity_id += 1
                copied.created_by = lorewalker.card_id
                if len(recipient.hand) < 10:
                    recipient.hand.append(copied)
                    self._event(
                        "lorewalker_copy", player=recipient.index,
                        source=lorewalker.entity_id, spell=card.card_id,
                        copied=copied.entity_id,
                    )
                else:
                    self._event(
                        "generated_burned", player=recipient.index,
                        card=copied.card_id, source=lorewalker.card_id,
                    )
        if card.definition.card_set == "TIME_TRAVEL":
            self._accelerate_timelords(
                player,
                exclude_entity=card.entity_id if card.card_id == "TIME_063" else None,
            )

    def _accelerate_timelords(
        self, player: Player, *, exclude_entity: int | None = None
    ) -> None:
        for minion in player.board:
            if (
                minion.card_id != "TIME_063"
                or minion.entity_id == exclude_entity
                or minion.dormant_turns <= 0
            ):
                continue
            minion.dormant_turns -= 1
            self._event(
                "dormant_accelerated", player=player.index,
                card=minion.card_id, entity=minion.entity_id,
                remaining=minion.dormant_turns,
            )
            if minion.dormant_turns == 0:
                self._event(
                    "awaken", player=player.index, card=minion.card_id,
                    entity=minion.entity_id,
                )

    def _battlecry(self, player: Player, card: CardInstance, action: Action) -> None:
        times = 2 if card.battlecry_twice else 1
        if card.card_id == "CATA_556":
            for _ in range(times):
                generated = self._entity(
                    self.rng.choice(sorted(LOW_COST_DRAGON_IDS)),
                    created_by=card.card_id,
                )
                destination = self._add_generated(player, generated)
                self._event(
                    "generated_from_pool", player=player.index,
                    card=generated.card_id, entity=generated.entity_id,
                    source=card.card_id, destination=destination,
                )
            return
        if card.card_id == "TIME_034":
            self._offer_rewind(
                player, "stadium_weapons", remaining_battlecries=times - 1
            )
            return
        if card.card_id == "TIME_003":
            self._offer_rewind(
                player, "portal_vanguard", remaining_battlecries=times - 1
            )
            return
        if card.card_id == "TIME_004":
            self._offer_rewind(
                player, "conflux_crasher", remaining_battlecries=times - 1
            )
            return
        if card.card_id == "TIME_008":
            self._offer_rewind(
                player, "bygone_doomspeaker", remaining_battlecries=times - 1
            )
            return
        if card.card_id == "EDR_456" and self._holding_dragon(player):
            self._offer_discover(
                player, DRAGON_IDS, dark_gift=True, repeats=times,
                source_card_id=card.card_id,
            )
            return
        if card.card_id == "EDR_856":
            self._offer_deck_minion_discover(player, repeats=times)
            return
        if card.card_id == "FIR_924":
            self._offer_discover(
                player, SUPPORTED_VOID_SOUL_DEMON_IDS, dark_gift=True,
                repeats=times, after_pick="copy_each_discovered",
                source_card_id=card.card_id,
            )
            return
        for _ in range(times):
            if self.rule_registry.dispatch(
                Hook.BATTLECRY, card.card_id, self,
                RuleContext(player=player, card=card, action=action),
            ):
                continue
            if card.card_id == "CORE_SW_066":
                target = self._find_minion(action.target_player, action.target_entity)
                target.attack_delta = 0
                target.health_delta = 0
                target.taunt = target.rush = target.charge = target.lifesteal = False
                target.elusive = target.divine_shield = target.windfury = target.reborn = False
                target.stealth = False
                target.poisonous = False
                target.immune = False
                target.infinite_attack_next_turn = False
                target.silenced = True
            elif card.card_id == "CATA_200":
                target = next(
                    (held for held in player.hand if held.entity_id == action.target_entity),
                    None,
                )
                if target is not None:
                    target.definition = self.card_defs["GAME_005"]
                    target.cost_delta = target.attack_delta = target.health_delta = 0
                    target.gifts.clear()
                    target.created_by = card.card_id
                    self._event(
                        "transform_to_coin", player=player.index,
                        entity=target.entity_id, source=card.card_id,
                    )
            elif card.card_id == "CATA_612":
                card.frozen_turn = self.turn
            elif card.card_id == "CATA_490":
                target = next(
                    (held for held in player.hand if held.entity_id == action.target_entity),
                    None,
                )
                if target is not None:
                    player.hand.remove(target)
                    self._event(
                        "discard", player=player.index, card=target.card_id,
                        source=card.card_id, entity=target.entity_id,
                        started_in_deck=target.started_in_deck,
                        created_by=target.created_by,
                    )
            elif card.card_id == "EDR_521":
                opponent = self.players[1 - player.index]
                if opponent.hand and len(player.hand) < 10:
                    lowest = min(
                        self._effective_cost(opponent, held) for held in opponent.hand
                    )
                    candidates = [
                        held for held in opponent.hand
                        if self._effective_cost(opponent, held) == lowest
                    ]
                    copied = self.rng.choice(candidates).clone(self.next_entity_id)
                    self.next_entity_id += 1
                    copied.created_by = card.card_id
                    player.hand.append(copied)
            elif card.card_id == "EDR_780":
                if len(player.board) + len(player.locations) < 7:
                    copied = card.clone(self.next_entity_id)
                    self.next_entity_id += 1
                    copied.created_by = card.card_id
                    copied.summoned_turn = self.turn
                    fake = self.rng.choice([card, copied])
                    fake.illusion_fake = True
                    self._summon(player, copied)
                    self._event(
                        "illusion_pair", player=player.index,
                        original=card.entity_id, copy=copied.entity_id,
                        fake=fake.entity_id,
                    )
            elif card.card_id == "EDR_493":
                self._transform_hand_minions_to_demons(player, card.card_id)
            elif card.card_id == "EDR_524":
                opponent = self.players[1 - player.index]
                shared = sorted(
                    {held.card_id for held in player.hand}
                    & {held.card_id for held in opponent.hand}
                )
                if shared:
                    chosen_id = self.rng.choice(shared)
                    target = next(
                        held for held in opponent.hand if held.card_id == chosen_id
                    )
                    opponent.hand.remove(target)
                    opponent.deck.insert(
                        self.rng.randrange(len(opponent.deck) + 1), target
                    )
                    self._event(
                        "shuffle_from_hand", player=opponent.index,
                        card=target.card_id, source=card.card_id,
                    )
            elif card.card_id == "CORE_EX1_310":
                for _ in range(min(2, len(player.hand))):
                    discarded = self.rng.choice(player.hand)
                    player.hand.remove(discarded)
                    self._event(
                        "discard", player=player.index,
                        card=discarded.card_id, source=card.card_id,
                        entity=discarded.entity_id,
                        started_in_deck=discarded.started_in_deck,
                        created_by=discarded.created_by,
                    )
            elif card.card_id == "CORE_ULD_165" and action.target_entity is not None:
                target = self._find_minion(action.target_player, action.target_entity)
                health = target.health
                target.damage = target.max_health
                self._resolve_deaths()
                self._damage_hero(player, health, card)
            elif card.card_id == "CORE_CATA_001":
                player.next_demon_free = True
                self._event("next_demon_free", player=player.index)
            elif card.card_id == "CORE_KAR_061":
                for race in ("BEAST", "DRAGON", "MURLOC"):
                    self._draw_matching(player, lambda held, race=race: held.has_race(race))
            elif card.card_id == "CATA_720":
                for owner in self.players:
                    destroyed = [
                        held for held in owner.deck
                        if self._effective_cost(owner, held) <= 2
                    ]
                    owner.deck[:] = [
                        held for held in owner.deck if held not in destroyed
                    ]
                    self._refresh_scrappy(owner)
                    self._event(
                        "warmaster_destroy", player=owner.index,
                        cards=[held.card_id for held in destroyed],
                    )
            elif card.card_id == "JAIL_852":
                first_count = len(self.players[0].hand)
                combined = self.players[0].hand + self.players[1].hand
                self.rng.shuffle(combined)
                self.players[0].hand = combined[:first_count]
                self.players[1].hand = combined[first_count:]
                self._event(
                    "togwaggle_shuffle", player=player.index,
                    first_count=first_count,
                    second_count=len(combined) - first_count,
                )
            elif card.card_id == "TLC_110":
                deck_minions = [
                    held for held in player.deck
                    if held.definition.card_type == "MINION"
                ]
                shared_types: set[str] = set()
                if deck_minions:
                    first = deck_minions[0]
                    shared_types = set(first.definition.races)
                    if first.definition.race:
                        shared_types.add(first.definition.race)
                    for held in deck_minions[1:]:
                        races = set(held.definition.races)
                        if held.definition.race:
                            races.add(held.definition.race)
                        shared_types &= races
                if shared_types:
                    affected: list[int] = []
                    for held in player.board + player.hand + player.deck:
                        if (
                            held.definition.card_type != "MINION"
                            or held.entity_id == card.entity_id
                        ):
                            continue
                        held.attack_delta += 2
                        held.health_delta += 2
                        affected.append(held.entity_id)
                    self._event(
                        "city_chief_esho_buff", player=player.index,
                        shared_types=sorted(shared_types), affected=affected,
                    )
            elif card.card_id == "CORE_EX1_002" and action.target_entity is not None:
                enemy = self.players[action.target_player]
                target = next(
                    (m for m in enemy.board if m.entity_id == action.target_entity),
                    None,
                )
                if target is not None and self._has_taunt(enemy.index, target):
                    target.damage = target.max_health
                    self._event(
                        "black_knight_destroy", player=player.index,
                        target=target.entity_id,
                    )
                    self._resolve_deaths()
            elif card.card_id == "CORE_EDR_003":
                self._draw_matching(
                    player,
                    lambda held: (
                        "<b>Corpses</b>" in held.definition.text
                        and (
                            "Spend" in held.definition.text
                            or "Costs <b>Corpses</b>" in held.definition.text
                        )
                    ),
                )
            elif card.card_id == "CORE_REV_946":
                for owner in self.players:
                    removed = [held for held in owner.deck if not held.started_in_deck]
                    owner.deck[:] = [held for held in owner.deck if held.started_in_deck]
                    self._refresh_scrappy(owner)
                    self._event(
                        "steamcleaner", player=owner.index,
                        destroyed=[held.card_id for held in removed],
                    )
            elif card.card_id == "JAIL_456":
                if len(player.deck) >= 25:
                    self._draw(player)
            elif card.card_id == "JAIL_882":
                copies = []
                for held in list(player.deck):
                    if held.definition.card_type != "SPELL":
                        continue
                    copied = held.clone(self.next_entity_id)
                    self.next_entity_id += 1
                    copied.started_in_deck = False
                    copied.created_by = card.card_id
                    copies.append(copied)
                player.deck.extend(copies)
                self.rng.shuffle(player.deck)
                self._event(
                    "deck_spell_copies", player=player.index,
                    count=len(copies), source=card.card_id,
                )
            elif card.card_id == "TIME_043" and action.target_entity is not None:
                target = self._find_minion(player.index, action.target_entity)
                target.attack_delta = 8 - target.definition.attack
                target.health_delta = 8 - target.definition.health
                target.damage = 0
                target.cant_attack_heroes_turn = self.turn
            elif card.card_id == "TIME_048":
                card.health_delta += player.turns_taken
            elif card.card_id == "EDR_457" and self._holding_dragon(player):
                self._equip_weapon(player, Weapon("EDR_457t", "Brood Keeper's Sword", 2, 2))
            elif card.card_id == "CORE_DRG_024":
                pirate_id = self.rng.choice(sorted(PIRATE_IDS))
                generated = self._entity(pirate_id, created_by=card.card_id)
                destination = self._add_generated(
                    player, generated
                )
                self._event(
                    "generated_from_pool", player=player.index,
                    card=generated.card_id, entity=generated.entity_id,
                    source=card.card_id, destination=destination,
                )
            elif card.card_id == "CORE_NEW1_018" and player.weapon:
                card.attack_delta += player.weapon.attack
            elif card.card_id == "CS3_022" and player.weapon is not None:
                self._deal_to_target(
                    player.index,
                    (action.target_player, action.target_entity),
                    2,
                    source=card,
                )
            elif card.card_id == "CATA_111" and self._holding_dragon(player):
                player.mana = min(player.max_mana, player.mana + 2)
            elif card.card_id == "CATA_160":
                self._herald_ragnaros(player, source=card.card_id, rush=True)
            elif card.card_id == "CATA_497":
                self._herald_ragnaros(player, source=card.card_id)
                discount = self._herald_power(player.herald_count)
                discounted = self._discount_deathwings(player, discount)
                self._event(
                    "deathwing_discount", player=player.index,
                    source=card.card_id, amount=discount,
                    affected=discounted,
                )
            elif card.card_id == "CATA_722":
                self._herald_ragnaros(player, source=card.card_id)
            elif card.card_id == "CORE_BT_120" and action.target_entity is not None:
                enemy = self.players[1 - player.index]
                target = next(
                    (m for m in enemy.board if m.entity_id == action.target_entity),
                    None,
                )
                while target is not None and card.health > 0 and target.health > 0:
                    card_attack = card.attack
                    target_attack = target.attack
                    self._damage_minion(enemy.index, target, card_attack, card)
                    self._damage_minion(player.index, card, target_attack, target)
                    self._resolve_deaths()
                    if card not in player.board or target not in enemy.board:
                        break
            elif card.card_id == "CORE_OG_149":
                for owner, entity in list(self._all_minions()):
                    if entity != card.entity_id:
                        self._damage_minion(
                            owner, self._find_minion(owner, entity), 1, card
                        )
                self._resolve_deaths()
            elif card.card_id == "EDR_468" and action.target_entity is not None:
                targets = self.players[action.target_player].board
                target = next(
                    (m for m in targets if m.entity_id == action.target_entity),
                    None,
                )
                if target is not None:
                    self._damage_minion(action.target_player, target, 1, card)
                    target.attack_delta += 4
            elif card.card_id == "END_019" and (
                f"hero:{player.index}" in player.damaged_characters_this_turn
            ):
                card.attack_delta += 3
                card.health_delta += 3
            elif card.card_id == "FIR_928":
                affected = []
                for held in player.hand:
                    if held.definition.card_type != "MINION":
                        continue
                    held.attack_delta += 3
                    held.health_delta += 3
                    if held.burning_turns == 0:
                        held.burning_turns = 3
                        held.burning_applied_turn = self.turn
                    affected.append(held.entity_id)
                self._event(
                    "zone_buff", player=player.index, source=card.card_id,
                    zone="hand", attack=3, health=3,
                    card_types=["MINION"], require_attribute=None,
                    burning_turns=3, affected_count=len(affected),
                    affected=affected,
                )
            elif card.card_id == "TLC_606" and action.target_entity is not None:
                enemy = self.players[1 - player.index]
                target = next(
                    (m for m in enemy.board if m.entity_id == action.target_entity),
                    None,
                )
                if target is not None:
                    self._damage_minion(enemy.index, target, 2, card)
                    killed = target.health <= 0
                    self._resolve_deaths()
                    if killed:
                        self._gain_armor(player, 5)
            elif card.card_id == "JAIL_435":
                enemy = self.players[1 - player.index]
                attackers = [
                    minion for minion in enemy.board
                    if minion.dormant_turns == 0
                ]
                for attacker in attackers:
                    if card not in player.board:
                        break
                    if attacker in enemy.board:
                        self._forced_minion_attack(
                            enemy.index, attacker, player.index, card
                        )
            elif card.card_id == "JAIL_455":
                for _ in range(2):
                    for target in list(player.board):
                        if target.entity_id != card.entity_id:
                            self._damage_minion(player.index, target, 1, card)
                    self._resolve_deaths()
            elif card.card_id == "TLC_624":
                originals = [
                    minion for minion in player.board
                    if minion.entity_id != card.entity_id
                    and minion.damage > 0
                    and minion.health > 0
                    and minion.dormant_turns == 0
                ]
                for original in originals:
                    if len(player.board) + len(player.locations) >= 7:
                        break
                    copied = original.clone(self.next_entity_id)
                    self.next_entity_id += 1
                    copied.created_by = card.card_id
                    copied.rush = True
                    copied.summoned_turn = self.turn
                    self._summon(player, copied)
            elif card.card_id == "CORE_EX1_043":
                card.health_delta += len(player.hand)
            elif card.card_id == "CORE_UNG_848":
                for owner, entity in list(self._all_minions()):
                    if entity != card.entity_id:
                        self._damage_minion(owner, self._find_minion(owner, entity), 2)
                self._resolve_deaths()
            elif card.card_id == "FIR_956" and any(
                held.gifts and held.definition.card_type == "MINION"
                for held in player.hand
            ):
                player.hero_attack_bonus += 3
                self._gain_armor(player, 6)
            elif card.card_id == "TIME_871":
                damaged = sum(
                    minion.damage > 0
                    for other in self.players
                    for minion in other.board
                )
                card.attack_delta += 2 * damaged
                card.health_delta += 2 * damaged
            elif card.card_id == "TIME_714":
                enemy = self.players[1 - player.index]
                for minion in list(enemy.board):
                    if minion.played_turn == self.turn - 1:
                        minion.damage = minion.max_health
                self._resolve_deaths()
            elif card.card_id == "TLC_243" and (
                set(card.definition.races) & player.played_races_last_turn
            ):
                card.immune = True
            elif card.card_id == "DINO_404" and (
                set(card.definition.races) & player.played_races_last_turn
            ):
                for other in player.board:
                    if other.entity_id != card.entity_id:
                        other.rush = True
            elif card.card_id == "DINO_413":
                enemy = self.players[1 - player.index]
                targets = [
                    minion for minion in enemy.board
                    if minion.dormant_turns == 0
                ]
                for target in self.rng.sample(targets, min(2, len(targets))):
                    self._damage_minion(enemy.index, target, 2, card)
                    if set(card.definition.races) & player.played_races_last_turn:
                        target.frozen_turn = self.turn
                        self._event(
                            "freeze", player=enemy.index,
                            entity=target.entity_id, source=card.card_id,
                        )
                self._resolve_deaths()
            elif card.card_id == "DINO_138" and (
                set(card.definition.races) & player.played_races_last_turn
            ):
                enemy = self.players[1 - player.index]
                targets = [m for m in enemy.board if m.dormant_turns == 0]
                edge_targets = targets[:1] + targets[-1:]
                seen: set[int] = set()
                for target in edge_targets:
                    if target.entity_id in seen:
                        continue
                    seen.add(target.entity_id)
                    self._damage_minion(enemy.index, target, 6, card)
                self._resolve_deaths()
            elif card.card_id == "TLC_432":
                drawn = self._draw_matching(
                    player,
                    lambda held: (
                        held.definition.cost <= 3
                        and "DEATHRATTLE" in held.definition.mechanics
                    ),
                )
                if (
                    drawn is not None
                    and set(card.definition.races) & player.played_races_last_turn
                ):
                    drawn.cost_delta -= drawn.cost
            elif card.card_id == "TLC_482":
                for _ in range(2):
                    if len(player.board) + len(player.locations) >= 7:
                        break
                    cinder = self._entity("TLC_249", created_by=card.card_id)
                    cinder.summoned_turn = self.turn
                    self._summon(player, cinder)
                if set(card.definition.races) & player.played_races_last_turn:
                    for cinder in list(player.board):
                        if cinder.card_id == "TLC_249" and not cinder.silenced:
                            self._deathrattle(player, cinder)
            elif card.card_id == "TLC_102":
                kindred = self._draw_matching(
                    player, lambda held: "Kindred" in held.definition.text
                )
                if kindred is not None:
                    races = set(kindred.definition.races)
                    if kindred.definition.race:
                        races.add(kindred.definition.race)
                    self._draw_matching(
                        player,
                        lambda held: bool(races & (
                            set(held.definition.races)
                            | ({held.definition.race} if held.definition.race else set())
                        )),
                    )
            elif card.card_id == "TLC_223":
                drawn = self._draw_matching(
                    player, lambda held: held.definition.spell_school == "FIRE"
                )
                if (
                    drawn is not None
                    and set(card.definition.races) & player.played_races_last_turn
                ):
                    drawn.spell_damage_bonus += 2
            elif card.card_id == "FIR_951":
                options = [amount for amount in (10, 20, 30) if amount <= player.corpses]
                if options:
                    self.pending_choice = {
                        "kind": "CORPSE_SPEND",
                        "player": player.index,
                        "entity": card.entity_id,
                        "options": options,
                    }
                    self._event(
                        "corpse_spend_offer", player=player.index,
                        entity=card.entity_id, options=options,
                    )
            elif card.card_id == "END_034":
                enemy = self.players[1 - player.index]
                minions = [m for m in enemy.board if m.dormant_turns == 0]
                if minions:
                    destroyed_minion = self.rng.choice(minions)
                    destroyed_minion.damage = destroyed_minion.max_health
                if enemy.locations:
                    enemy.locations.remove(self.rng.choice(enemy.locations))
                if enemy.weapon:
                    self._destroy_weapon(enemy)
                self._resolve_deaths()
            elif card.card_id == "END_035" and not player.deck:
                enemy = self.players[1 - player.index]
                for _ in range(min(5, len(enemy.deck))):
                    destroyed = enemy.deck.pop()
                    self._event(
                        "deck_destroy", player=enemy.index, card=destroyed.card_id,
                        source=card.card_id,
                    )
                self._refresh_scrappy(enemy)
            elif card.card_id == "TLC_888":
                candidates = [
                    held for held in player.hand
                    if held.has_race("ELEMENTAL") or held.has_race("DRAGON")
                ]
                if candidates and len(player.hand) < 10:
                    copied = self.rng.choice(candidates).clone(self.next_entity_id)
                    self.next_entity_id += 1
                    copied.created_by = card.card_id
                    player.hand.append(copied)

    def _cast_spell(self, player: Player, card: CardInstance, action: Action) -> None:
        prior_fire = player.fire_spell_played
        spell_damage = self._spell_damage(player) + card.spell_damage_bonus
        if self.rule_registry.dispatch(
            Hook.SPELL, card.card_id, self,
            RuleContext(player=player, card=card, action=action),
        ):
            return
        if card.card_id == "TIME_001":
            self._offer_rewind(player, "chrono_daggers")
        elif card.card_id == "TIME_433":
            self._offer_rewind(player, "cease_to_exist")
        elif card.card_id == "TIME_441":
            self._offer_rewind(player, "aeon_rend")
        elif card.card_id == "TIME_610":
            self._offer_rewind(player, "shadows_of_yesterday")
        elif card.card_id == "FIR_939":
            self._deal_to_target(
                player.index, (action.target_player, action.target_entity),
                2 + spell_damage,
            )
            self._offer_discover(
                player, WARRIOR_MINION_IDS, dark_gift=True,
                source_card_id=card.card_id,
            )
        elif card.card_id == "CATA_582":
            for p, entity in list(self._all_minions()):
                self._damage_minion(
                    p, self._find_minion(p, entity), 1 + spell_damage
                )
            player.hero_attack_bonus += 3
        elif card.card_id == "CATA_584":
            for _ in range(6 if prior_fire else 3):
                targets = self._random_enemy_characters(player.index)
                if not targets:
                    break
                self._deal_to_target(player.index, self.rng.choice(targets), 1)
                self._resolve_deaths()
        elif card.card_id == "CATA_585":
            target = self._find_minion(action.target_player, action.target_entity)
            amount = 8 + spell_damage
            excess = max(0, amount - target.health)
            self._damage_minion(action.target_player, target, amount)
            if excess and len(player.hand) < 10:
                card.started_in_deck = False
                card.created_by = card.card_id
                player.hand.append(card)
                self._event(
                    "returned_to_hand", player=player.index,
                    card=card.card_id, entity=card.entity_id,
                    source=card.card_id, destination="hand",
                )
        elif card.card_id == "CAP_105":
            self._offer_discover(
                player, PIRATE_IDS, dark_gift=False,
                after_pick="summon_cannoneers",
                source_card_id=card.card_id,
            )
        elif card.card_id == "CORE_EX1_277":
            for _ in range(3 + spell_damage):
                targets = self._random_enemy_characters(player.index)
                if not targets:
                    break
                self._deal_to_target(
                    player.index, self.rng.choice(targets), 1
                )
                self._resolve_deaths()
        elif card.card_id == "CATA_464t":
            self._deal_to_target(
                player.index, (action.target_player, action.target_entity),
                card.dynamic_spell_damage + spell_damage,
            )
            self._resolve_deaths()
        elif card.card_id == "TLC_813":
            target = self._find_minion(
                action.target_player, action.target_entity
            )
            target.health_delta += 2 if action.target_player == player.index else -2
            self._event(
                "purifying_vines", player=player.index,
                target_player=action.target_player,
                target=target.entity_id,
                health_delta=(2 if action.target_player == player.index else -2),
            )
            self._resolve_deaths()
        elif card.card_id == "TLC_241t":
            target = self._find_minion(
                action.target_player, action.target_entity
            )
            target.attack_delta += 2
            target.health_delta += 2
            target.divine_shield = True
            target.divine_shield_hits = 1
            target.divine_shield_toreth = False
            self._refresh_continuous(self.players[action.target_player])
            self._event(
                "call_threshfleet", player=player.index,
                target_player=action.target_player, target=target.entity_id,
            )
        elif card.card_id == "JAIL_732":
            pool = VOID_SOUL_DEMON_IDS_BY_COST.get(card.void_soul_cost)
            if not pool:
                raise UnsupportedGeneratedCard(
                    f"Void Soul cost {card.void_soul_cost}"
                )
            if len(player.board) + len(player.locations) < 7:
                demon_id = self.rng.choice(sorted(pool))
                demon = self._entity(demon_id, created_by=card.card_id)
                demon.summoned_turn = self.turn
                self._summon(player, demon)
                self._event(
                    "void_soul_summon", player=player.index,
                    cost=card.void_soul_cost, card=demon_id,
                )
            player.void_soul_level = min(10, player.void_soul_level + 1)
        if card.card_id in {"FIR_939", "CATA_582", "CATA_585"}:
            player.fire_spell_played = True
            spell_cost = self._effective_cost(player, card)
            for magma in player.board:
                if (
                    magma.card_id == "TLC_224"
                    and not magma.silenced
                    and magma.dormant_turns == 0
                ):
                    magma.attack_delta += spell_cost
                    magma.health_delta += spell_cost
                    self._event(
                        "mechanized_magma_buff", player=player.index,
                        entity=magma.entity_id, amount=spell_cost,
                    )

    def _holding_dragon(self, player: Player) -> bool:
        return any(card.has_race("DRAGON") for card in player.hand)

    @staticmethod
    def _silence_minion(target: CardInstance) -> None:
        """Remove enchantments, keywords, and text-driven state from a minion."""
        target.attack_delta = 0
        target.health_delta = 0
        target.taunt = target.rush = target.charge = target.lifesteal = False
        target.elusive = target.divine_shield = target.windfury = target.reborn = False
        target.stealth = target.poisonous = target.immune = False
        target.infinite_attack_next_turn = False
        target.silenced = True

    def _grant_bonus_effect(
        self, player: Player, target: CardInstance, *, source: str
    ) -> str | None:
        eligible = [
            effect for effect in BONUS_EFFECTS
            if not getattr(target, effect)
            and not (
                effect == "rush"
                and (
                    target.charge
                    or target.attacks_this_turn > 0
                    or self.current != player.index
                )
            )
        ]
        if not eligible:
            return None
        effect = self.rng.choice(eligible)
        setattr(target, effect, True)
        if effect == "divine_shield":
            target.divine_shield_hits = 1
            target.divine_shield_toreth = False
        self._event(
            "bonus_effect", player=player.index, source=source,
            target=target.entity_id, effect=effect,
        )
        return effect

    @staticmethod
    def _herald_power(herald_count: int) -> int:
        if herald_count >= 4:
            return 4
        if herald_count >= 2:
            return 2
        return 1

    def _herald_ragnaros(
        self, player: Player, *, source: str, rush: bool = False
    ) -> CardInstance | None:
        # Herald summons the current Soldier first, then advances the tracker.
        # Consequently the first two Soldiers are base, the next two are x2,
        # and later Soldiers are x4.
        power = self._herald_power(player.herald_count)
        soldier = None
        if len(player.board) + len(player.locations) < 7:
            soldier = CardInstance(
                self.next_entity_id,
                CardDef(
                    "CATA_580t", "Soldier of Ragnaros", "MINION", 1,
                    2, 1, "ELEMENTAL", ("DEATHRATTLE",), "WARRIOR",
                    ("ELEMENTAL",), "CATACLYSM",
                ),
                rush=rush,
                summoned_turn=self.turn,
                created_by=source,
                herald_power=power,
            )
            self.next_entity_id += 1
            soldier.attack_delta = 2 * power - soldier.definition.attack
            soldier.health_delta = power - soldier.definition.health
            self._summon(player, soldier)
        player.herald_count += 1
        self._event(
            "herald", player=player.index, source=source,
            count=player.herald_count, power=power,
            soldier=None if soldier is None else soldier.entity_id,
            rush=rush,
        )
        return soldier

    def _summon_ragnaros_hands(self, player: Player, *, source: str) -> None:
        power = self._herald_power(player.herald_count)
        for _ in range(2):
            if len(player.board) + len(player.locations) >= 7:
                break
            hand = CardInstance(
                self.next_entity_id,
                CardDef(
                    "CATA_150t", "Hand of Ragnaros", "MINION", 1,
                    2, 1, "ELEMENTAL", ("DEATHRATTLE",), "WARRIOR",
                    ("ELEMENTAL",), "CATACLYSM",
                ),
                summoned_turn=self.turn,
                created_by=source,
                herald_power=power,
            )
            self.next_entity_id += 1
            hand.attack_delta = 2 * power - hand.definition.attack
            hand.health_delta = power - hand.definition.health
            self._summon(player, hand)

    def _forced_minion_attack(
        self, attacker_owner: int, attacker: CardInstance,
        defender_owner: int, defender: CardInstance,
    ) -> None:
        if attacker.health <= 0 or defender.health <= 0:
            return
        attacker.attacks_this_turn += 1
        attacker.stealth = False
        attacker_damage = attacker.attack
        defender_damage = defender.attack
        self._damage_minion(defender_owner, defender, attacker_damage, attacker)
        self._damage_minion(attacker_owner, attacker, defender_damage, defender)
        self._finja_kill(attacker_owner, attacker, defender)
        self._after_minion_attacked(defender_owner, defender)
        self._after_minion_attack(attacker_owner, attacker, attacked_minion=True)
        self._resolve_deaths()

    def _finja_kill(
        self, attacker_owner: int, attacker: CardInstance,
        defender: CardInstance,
    ) -> None:
        if (
            attacker.card_id != "CORE_CFM_344"
            or attacker.silenced
            or defender.health > 0
        ):
            return
        player = self.players[attacker_owner]
        summoned: list[int] = []
        for _ in range(2):
            candidates = [held for held in player.deck if held.has_race("MURLOC")]
            if not candidates or len(player.board) + len(player.locations) >= 7:
                break
            chosen = self.rng.choice(candidates)
            player.deck.remove(chosen)
            chosen.summoned_turn = self.turn
            self._summon(player, chosen)
            summoned.append(chosen.entity_id)
        self._refresh_scrappy(player)
        self._event(
            "finja_trigger", player=attacker_owner,
            source=attacker.entity_id, killed=defender.entity_id,
            summoned=summoned,
        )

    def _after_minion_attack(
        self, attacker_owner: int, attacker: CardInstance,
        *, attacked_minion: bool = False,
    ) -> None:
        if attacker.card_id == "EDR_421" and not attacker.silenced:
            attacker.omen_damage += 1
            self._event(
                "omen_upgrade", player=attacker_owner,
                entity=attacker.entity_id, damage=attacker.omen_damage,
            )
        elif attacker.card_id == "CATA_469" and not attacker.silenced:
            player = self.players[attacker_owner]
            refreshed = min(attacker.attack, player.max_mana - player.mana)
            player.mana += refreshed
            self._event(
                "mana_refreshed", player=attacker_owner,
                entity=attacker.entity_id, amount=refreshed,
            )
        elif (
            attacker.card_id == "FIR_953"
            and not attacker.silenced
            and attacked_minion
            and attacker.health > 0
            and attacker in self.players[attacker_owner].board
        ):
            for _ in range(attacker.attack):
                targets = self._random_enemy_characters(attacker_owner)
                if not targets:
                    break
                self._deal_to_target(
                    attacker_owner, self.rng.choice(targets), 1,
                    source=attacker,
                )
                self._resolve_deaths()
        elif attacker.card_id == "CS3_025" and not attacker.silenced:
            player = self.players[attacker_owner]
            affected = []
            for held in player.hand:
                if held.definition.card_type != "MINION":
                    continue
                held.attack_delta += 1
                held.health_delta += 1
                affected.append(held.entity_id)
            self._event(
                "runthak_buff", player=attacker_owner,
                entity=attacker.entity_id, source=attacker.card_id,
                zone="hand", attack=1, health=1,
                card_types=["MINION"], require_attribute=None,
                affected_count=len(affected), affected=affected,
            )

    def _after_minion_attacked(
        self, defender_owner: int, defender: CardInstance
    ) -> None:
        if (
            defender.card_id != "CORE_BT_510"
            or defender.silenced
            or defender.health <= 0
            or defender not in self.players[defender_owner].board
        ):
            return
        enemy = self.players[1 - defender_owner]
        self._damage_hero(enemy, 1, defender)
        for minion in list(enemy.board):
            self._damage_minion(enemy.index, minion, 1, defender)
        self._event(
            "wrathspike_brute_trigger", player=defender_owner,
            entity=defender.entity_id,
        )

    def _discount_deathwings(self, player: Player, amount: int) -> int:
        affected = 0
        for card in player.hand + player.deck:
            if "deathwing" in card.definition.name.casefold():
                card.cost_delta -= amount
                affected += 1
        return affected

    def _offer_discover(
        self,
        player: Player,
        pool: Iterable[str],
        dark_gift: bool,
        repeats: int = 1,
        after_pick: str | None = None,
        source_card_id: str | None = None,
    ) -> None:
        card_ids = sorted(set(pool))
        self.rng.shuffle(card_ids)
        options = [
            self._entity(card_id, created_by=source_card_id)
            for card_id in card_ids[:3]
        ]
        if dark_gift:
            used_gifts: set[str] = set()
            for option in options:
                eligible = sorted(self._eligible_dark_gifts(option) - used_gifts)
                if not eligible:
                    eligible = sorted(self._eligible_dark_gifts(option))
                gift = self.rng.choice(eligible)
                used_gifts.add(gift)
                self._apply_dark_gift(option, gift)
        self.pending_choice = {
            "kind": "DISCOVER",
            "player": player.index,
            "pool": tuple(sorted(set(pool))),
            "dark_gift": dark_gift,
            "repeats_left": repeats - 1,
            "after_pick": after_pick,
            "source_card_id": source_card_id,
            "options": options,
        }
        self._event(
            "discover_offer",
            player=player.index,
            options=[{"entity": c.entity_id, "card": c.card_id, "gifts": list(c.gifts)} for c in options],
            profile="closed_pool",
        )

    def _transform_hand_minions_to_demons(
        self, player: Player, source_card_id: str
    ) -> None:
        demon_ids = sorted(SUPPORTED_VOID_SOUL_DEMON_IDS)
        for index, original in list(enumerate(player.hand)):
            if original.definition.card_type != "MINION":
                continue
            original_cost = original.cost
            original_attack = original.attack
            original_health = original.max_health
            transformed = self._entity(
                self.rng.choice(demon_ids), created_by=source_card_id
            )
            generated_entity = transformed.entity_id
            transformed.entity_id = original.entity_id
            transformed.started_in_deck = original.started_in_deck
            transformed.cost_delta = original_cost - transformed.definition.cost
            transformed.attack_delta = original_attack - transformed.definition.attack
            transformed.health_delta = original_health - transformed.definition.health
            player.hand[index] = transformed
            self._event(
                "hand_transform", player=player.index,
                entity=transformed.entity_id, from_card=original.card_id,
                to_card=transformed.card_id, source=source_card_id,
                discarded_entity=generated_entity,
                kept_cost=original_cost, kept_attack=original_attack,
                kept_health=original_health,
            )

    def _offer_geddon_draw(self, player: Player) -> None:
        if not player.deck:
            player.fatigue += 1
            self._damage_hero(player, player.fatigue)
            self._event(
                "geddon_fatigue", player=player.index, amount=player.fatigue
            )
            return
        options = self.rng.sample(player.deck, min(3, len(player.deck)))
        for option in options:
            player.deck.remove(option)
        self._refresh_scrappy(player)
        self.pending_choice = {
            "kind": "GEDDON_DRAW",
            "player": player.index,
            "options": options,
        }
        self._event(
            "geddon_offer",
            player=player.index,
            options=[
                {"entity": card.entity_id, "card": card.card_id}
                for card in options
            ],
        )

    def _offer_deck_minion_discover(
        self, player: Player, *, repeats: int = 1
    ) -> None:
        candidates = [
            card for card in player.deck
            if card.definition.card_type == "MINION"
        ]
        if not candidates:
            return
        originals = self.rng.sample(candidates, min(3, len(candidates)))
        options: list[CardInstance] = []
        original_entities: dict[int, int] = {}
        used_gifts: set[str] = set()
        for original in originals:
            option = original.clone(self.next_entity_id)
            self.next_entity_id += 1
            eligible = sorted(self._eligible_dark_gifts(option) - used_gifts)
            if not eligible:
                eligible = sorted(self._eligible_dark_gifts(option))
            gift = self.rng.choice(eligible)
            used_gifts.add(gift)
            self._apply_dark_gift(option, gift)
            options.append(option)
            original_entities[option.entity_id] = original.entity_id
        self.pending_choice = {
            "kind": "DECK_DISCOVER",
            "player": player.index,
            "options": options,
            "original_entities": original_entities,
            "repeats_left": repeats - 1,
        }
        self._event(
            "deck_discover_offer", player=player.index,
            options=[
                {"entity": card.entity_id, "card": card.card_id,
                 "gifts": list(card.gifts)}
                for card in options
            ],
        )

    def _offer_deck_card_discover(
        self, player: Player, *, temporary: bool = False,
        bottom_unchosen: bool = False, source_card_id: str | None = None,
    ) -> None:
        if not player.deck:
            return
        options = self.rng.sample(player.deck, min(3, len(player.deck)))
        self.pending_choice = {
            "kind": "DECK_CARD_DISCOVER",
            "player": player.index,
            "options": options,
            "temporary": temporary,
            "bottom_unchosen": bottom_unchosen,
            "source_card_id": source_card_id,
        }
        self._event(
            "deck_card_discover_offer", player=player.index,
            source=source_card_id, temporary=temporary,
            bottom_unchosen=bottom_unchosen,
            options=[{"entity": card.entity_id, "card": card.card_id} for card in options],
        )

    def _offer_imbue_options(self, player: Player, *, source_card_id: str) -> None:
        """Offer one playable Priest minion and spell for Blessing of the Moon.

        The production game can create from its complete card database.  This
        simulator deliberately limits the offer to its *executable* closed
        pool: creating an unsupported card as a vanilla placeholder would
        silently produce an invalid game.  The pool expands as rules are
        implemented, while the choice shape and temporary/cost semantics stay
        faithful to the card text.
        """
        candidates: dict[str, list[str]] = {"MINION": [], "SPELL": []}
        for card_id, definition in self.card_defs.items():
            if (
                card_id not in EXECUTABLE_CARD_IDS
                or definition.card_class != "PRIEST"
                or definition.card_type not in candidates
                or max(0, definition.cost - 1) > player.mana
            ):
                continue
            candidates[definition.card_type].append(card_id)
        if not candidates["MINION"] or not candidates["SPELL"]:
            self._event(
                "imbue_offer_unavailable", player=player.index,
                source=source_card_id,
            )
            return
        options: list[CardInstance] = []
        for card_type in ("MINION", "SPELL"):
            option = self._entity(
                self.rng.choice(sorted(candidates[card_type])),
                created_by=source_card_id,
            )
            option.cost_delta -= 1
            option.temporary = True
            options.append(option)
        self.pending_choice = {
            "kind": "IMBUE_PICK",
            "player": player.index,
            "source_card_id": source_card_id,
            "options": options,
        }
        self._event(
            "imbue_offer", player=player.index, source=source_card_id,
            profile="executable_standard_pool_v1",
            options=[{"entity": card.entity_id, "card": card.card_id}
                     for card in options],
        )

    def _summon_random_executable_minion(
        self, player: Player, *, source_card_id: str,
        cost: int | None = None, min_cost: int | None = None,
        require_taunt: bool = False,
    ) -> None:
        """Summon from the verified runtime pool without inventing a stub card."""
        if len(player.board) + len(player.locations) >= 7:
            return
        candidates = sorted(
            card_id for card_id, definition in self.card_defs.items()
            if card_id in EXECUTABLE_CARD_IDS
            and definition.card_type == "MINION"
            and (cost is None or definition.cost == cost)
            and (min_cost is None or definition.cost >= min_cost)
            and (not require_taunt or "TAUNT" in definition.mechanics)
        )
        if not candidates:
            self._event(
                "random_summon_unavailable", player=player.index,
                source=source_card_id, cost=cost, min_cost=min_cost,
                require_taunt=require_taunt,
            )
            return
        minion = self._entity(
            self.rng.choice(candidates), created_by=source_card_id
        )
        minion.summoned_turn = self.turn
        self._summon(player, minion)
        self._event(
            "random_summon", player=player.index, source=source_card_id,
            card=minion.card_id, entity=minion.entity_id, cost=cost,
            min_cost=min_cost, require_taunt=require_taunt,
            profile="executable_standard_pool_v1",
        )

    def _resolve_discover(self, entity_id: int) -> None:
        pending = self.pending_choice
        option = next(card for card in pending["options"] if card.entity_id == entity_id)
        player = self.players[pending["player"]]
        self.pending_choice = None
        if pending["kind"] == "GEDDON_DRAW":
            option.cost_delta -= 3
            destroyed = [
                card for card in pending["options"]
                if card.entity_id != entity_id
            ]
            if len(player.hand) < 10:
                player.hand.append(option)
                outcome = "hand"
            else:
                outcome = "burned"
            self._event(
                "geddon_pick", player=player.index, card=option.card_id,
                entity=option.entity_id, outcome=outcome,
                destroyed=[card.card_id for card in destroyed],
            )
            return
        if pending["kind"] == "DECK_CARD_DISCOVER":
            player.deck.remove(option)
            if pending["bottom_unchosen"]:
                unchosen = [
                    card for card in pending["options"]
                    if card.entity_id != entity_id and card in player.deck
                ]
                for card in unchosen:
                    player.deck.remove(card)
                player.deck[0:0] = unchosen
            option.temporary = pending["temporary"]
            if len(player.hand) < 10:
                player.hand.append(option)
                destination = "hand"
            else:
                destination = "burned"
            self._event(
                "deck_card_discover_pick", player=player.index,
                card=option.card_id, entity=option.entity_id,
                source=pending["source_card_id"], temporary=option.temporary,
                destination=destination,
            )
            return
        if pending["kind"] == "DECK_DISCOVER":
            original_entity = pending["original_entities"][entity_id]
            original = next(
                card for card in player.deck if card.entity_id == original_entity
            )
            player.deck.remove(original)
            option.started_in_deck = original.started_in_deck
            option.created_by = original.created_by
            self._add_generated(player, option)
            self._event(
                "deck_discover_pick", player=player.index,
                card=option.card_id, entity=option.entity_id,
                gifts=list(option.gifts),
            )
            if pending["repeats_left"]:
                self._offer_deck_minion_discover(
                    player, repeats=pending["repeats_left"]
                )
            return
        if pending["kind"] == "IMBUE_PICK":
            destination = self._add_generated(player, option)
            self._event(
                "imbue_pick", player=player.index,
                source=pending["source_card_id"], card=option.card_id,
                entity=option.entity_id, cost=option.cost,
                temporary=option.temporary, destination=destination,
            )
            return
        destination = self._add_generated(player, option)
        self._event(
            "discover_pick", player=player.index, card=option.card_id,
            gifts=list(option.gifts), entity=option.entity_id,
            source=pending["source_card_id"], destination=destination,
        )
        if pending["after_pick"] == "copy_each_discovered":
            copied = option.clone(self.next_entity_id)
            self.next_entity_id += 1
            copied.created_by = pending["source_card_id"]
            copy_destination = self._add_generated(player, copied)
            self._event(
                "discover_copy", player=player.index,
                card=copied.card_id, entity=copied.entity_id,
                gifts=list(copied.gifts), source=pending["source_card_id"],
                destination=copy_destination,
            )
        repeats_left = pending["repeats_left"]
        if repeats_left:
            self._offer_discover(
                player, pending["pool"], pending["dark_gift"],
                repeats=repeats_left, after_pick=pending["after_pick"],
                source_card_id=pending["source_card_id"],
            )
        elif pending["after_pick"] == "summon_cannoneers":
            self._summon_cannoneers(player)

    def _summon_cannoneers(self, player: Player) -> None:
        for _ in range(2):
            if len(player.board) + len(player.locations) >= 7:
                break
            token = self._entity("CAP_107t", created_by="CAP_105")
            token.summoned_turn = self.turn
            self._summon(player, token)

    def _eligible_dark_gifts(self, card: CardInstance) -> set[str]:
        gifts = {"living_nightmare", "sweet_dreams"}
        if not card.lifesteal:
            gifts.add("waking_terror")
        if not card.taunt:
            gifts.add("bundled_up")
        if not card.elusive:
            gifts.add("well_rested")
        if card.attack > 0 and not card.charge:
            gifts.add("sleepwalker")
        if not card.divine_shield and not card.windfury:
            gifts.add("harpys_talons")
        if not card.reborn:
            gifts.add("persisting_horror")
        if card.attack >= 3:
            gifts.add("short_claws")
        if "BATTLECRY" in card.definition.mechanics:
            gifts.add("rude_awakening")
        return gifts

    def _apply_dark_gift(self, card: CardInstance, gift: str) -> None:
        if gift not in self._eligible_dark_gifts(card):
            raise ValueError(f"ineligible Dark Gift {gift} for {card.card_id}")
        card.gifts.append(gift)
        if gift == "waking_terror": card.attack_delta += 3; card.lifesteal = True
        elif gift == "bundled_up": card.health_delta += 4; card.taunt = True
        elif gift == "well_rested": card.attack_delta += 2; card.health_delta += 2; card.elusive = True
        elif gift == "sleepwalker": card.charge = True
        elif gift == "harpys_talons": card.divine_shield = True; card.windfury = True
        elif gift == "persisting_horror": card.reborn = True
        elif gift == "short_claws": card.cost_delta -= 2; card.attack_delta -= 2
        elif gift == "rude_awakening": card.battlecry_twice = True
        elif gift == "living_nightmare": card.living_nightmare = True
        elif gift == "sweet_dreams": card.attack_delta += 4; card.health_delta += 5

    def _add_generated(self, player: Player, card: CardInstance) -> str:
        if "sweet_dreams" in card.gifts:
            player.deck.append(card)
            return "deck"
        elif len(player.hand) < 10:
            player.hand.append(card)
            return "hand"
        return "burned"

    def _stadium_weapons(self, player: Player) -> None:
        for p in self.players:
            card_id = self.rng.choice(sorted(SUPPORTED_STADIUM_WEAPONS))
            name, attack, durability = SUPPORTED_STADIUM_WEAPONS[card_id]
            self._equip_weapon(p, Weapon(card_id, name, attack, durability))
        player.weapon.attack += 1
        player.weapon.durability += 1

    def _equip_weapon(self, player: Player, weapon: Weapon) -> None:
        if player.weapon:
            self._destroy_weapon(player)
        player.weapon = weapon
        self._refresh_continuous(player)
        self._event(
            "equip_weapon", player=player.index, card=weapon.card_id,
            attack=weapon.attack, durability=weapon.durability,
        )

    def _destroy_weapon(self, player: Player) -> None:
        weapon = player.weapon
        if weapon is None:
            return
        player.weapon = None
        self._refresh_continuous(player)
        self._event("weapon_destroyed", player=player.index, card=weapon.card_id)
        if weapon.card_id == "JAIL_376":
            for minion in player.board:
                if minion.damage > 0:
                    minion.attack_delta += 1
                    minion.health_delta += 2
        elif weapon.card_id == "CATA_472":
            end_turn_minions = [m for m in player.board if m.card_id == "CAP_107t" and not m.silenced]
            if end_turn_minions:
                self._fire_cannoneer(
                    player, self.rng.choice(end_turn_minions),
                    reason="copied_end_turn",
                )
        elif weapon.card_id == "CORE_DAL_720" and player.board and len(player.hand) < 10:
            minion = self.rng.choice(player.board)
            player.board.remove(minion)
            minion.cost_delta -= 2
            minion.damage = 0
            player.hand.append(minion)
        elif weapon.card_id == "CORE_OG_031" and len(player.board) + len(player.locations) < 7:
            token = CardInstance(
                self.next_entity_id,
                CardDef("OG_031a", "Twilight Elemental", "MINION", 4, 4, 2, "ELEMENTAL"),
            )
            self.next_entity_id += 1
            token.summoned_turn = self.turn
            self._summon(player, token)
        elif weapon.card_id == "CORE_RLK_086":
            for definition in weapon.killed_minions:
                if len(player.board) + len(player.locations) >= 7:
                    break
                minion = self._instance_from_definition(
                    definition, created_by=weapon.card_id
                )
                minion.summoned_turn = self.turn
                self._summon(player, minion)
        elif weapon.card_id == "DINO_408":
            self._draw(player)
            self._draw(player)
        elif weapon.card_id == "JAIL_380":
            candidates = [
                card for card in player.deck
                if card.definition.card_type == "SPELL" and not card.started_in_deck
            ]
            if candidates:
                card = self.rng.choice(candidates)
                player.deck.remove(card)
                if len(player.hand) < 10:
                    player.hand.append(card)
                    self._event("draw", player=player.index, card=card.card_id)
                else:
                    self._event("burn", player=player.index, card=card.card_id)
        elif weapon.card_id == "JAIL_503":
            self._draw(player)

    def _after_hero_attack(
        self,
        player: Player,
        weapon: Weapon | None,
        attacked: tuple[int, int | None],
        attack_amount: int,
    ) -> None:
        if weapon is None:
            self._dispatch_after_hero_attack(player)
            return
        if weapon.card_id == "CAP_103":
            cannoneers = [
                minion for minion in player.board
                if minion.card_id == "CAP_107t" and not minion.silenced
            ]
            for cannoneer in cannoneers:
                if cannoneer not in player.board or cannoneer.health <= 0:
                    continue
                self._fire_cannoneer(
                    player, cannoneer, reason="hero_attack"
                )
        elif weapon.card_id == "TLC_478":
            for owner, entity in list(self._all_minions()):
                self._damage_minion(owner, self._find_minion(owner, entity), 1)
            self._resolve_deaths()
        elif weapon.card_id == "CATA_467" and player.board:
            self.rng.choice(player.board).attack_delta += 2
        elif weapon.card_id == "EDR_253":
            self._draw(player)
        elif weapon.card_id == "EDR_842":
            targets = [
                target for target in self._random_enemy_characters(player.index)
                if target != attacked
            ]
            if targets:
                self._deal_to_target(player.index, self.rng.choice(targets), attack_amount)
                self._resolve_deaths()
        elif weapon.card_id == "EDR_416" and len(player.board) + len(player.locations) < 7:
            sheep = CardInstance(
                self.next_entity_id,
                CardDef("EDR_416t", "Sleepy Sheep", "MINION", 2, 3, 3, "BEAST", (), "HUNTER"),
                created_by=weapon.card_id,
                dormant_turns=2,
            )
            self.next_entity_id += 1
            sheep.summoned_turn = self.turn
            self._summon(player, sheep)
        elif weapon.card_id == "END_016" and player.hand:
            highest = max(self._effective_cost(player, card) for card in player.hand)
            candidates = [
                card for card in player.hand
                if self._effective_cost(player, card) == highest
            ]
            discarded = self.rng.choice(candidates)
            player.hand.remove(discarded)
            self._event("discard", player=player.index, card=discarded.card_id)
        elif weapon.card_id == "JAIL_450" and len(player.board) + len(player.locations) < 7:
            token = CardInstance(
                self.next_entity_id,
                CardDef("JAIL_450t", "Frail Ghoul", "MINION", 1, 1, 1, "UNDEAD", ("CHARGE",)),
            )
            self.next_entity_id += 1
            token.charge = True
            token.summoned_turn = self.turn
            self._summon(player, token)
        elif weapon.card_id == "JAIL_329":
            for minion in player.board:
                if minion.definition.card_class == "PALADIN" and minion.dormant_turns == 0:
                    minion.attack_delta += 2
                    minion.health_delta += 2
        elif weapon.card_id == "TLC_833" and len(player.board) + len(player.locations) < 7:
            token = CardInstance(
                self.next_entity_id,
                CardDef("TLC_833t", "Grub", "MINION", 1, 2, 1, "BEAST", ("RUSH",)),
            )
            self.next_entity_id += 1
            token.rush = True
            token.summoned_turn = self.turn
            self._summon(player, token)
        elif weapon.card_id == "JAIL_730":
            soul = CardInstance(
                self.next_entity_id,
                CardDef(
                    "JAIL_732", "Void Soul", "SPELL", 1,
                    card_class="DEMONHUNTER",
                    card_set="ESCAPEFROM_VIOLET_HOLD",
                ),
                created_by=weapon.card_id,
                void_soul_cost=player.void_soul_level,
            )
            self.next_entity_id += 1
            if len(player.hand) < 10:
                player.hand.append(soul)
                self._event(
                    "void_soul_generated", player=player.index,
                    card=soul.card_id, entity=soul.entity_id,
                    source=weapon.card_id, destination="hand",
                    cost=soul.void_soul_cost,
                )
            else:
                self._event(
                    "generated_burned", player=player.index,
                    card=soul.card_id, source=weapon.card_id,
                )
        elif weapon.card_id == "JAIL_458" and weapon.ammunition is not None:
            self._fire_tiny_pal_ammunition(player, weapon, attacked)
        self._dispatch_after_hero_attack(player)

    def _dispatch_after_hero_attack(self, player: Player) -> None:
        """Run friendly-minion triggers after every hero attack.

        The hook is independent of weapons: Spider Rider must draw after an
        unarmed hero attack as well as after an armed one.
        """
        for minion in list(player.board):
            if (
                minion not in player.board
                or minion.silenced
                or minion.dormant_turns > 0
                or minion.health <= 0
            ):
                continue
            self.rule_registry.dispatch(
                Hook.AFTER_HERO_ATTACK, minion.card_id, self,
                RuleContext(player=player, card=minion),
            )

    def _offer_ammunition(
        self, player: Player, *, exclude: int | None = None
    ) -> None:
        options = [mode for mode in range(1, 5) if mode != exclude]
        self.pending_choice = {
            "kind": "AMMUNITION",
            "player": player.index,
            "options": options,
        }
        self._event(
            "ammunition_offer", player=player.index,
            options=options, excluded=exclude,
        )

    def _resolve_ammunition(self, mode: int | None) -> None:
        pending = self.pending_choice
        if pending is None or pending["kind"] != "AMMUNITION":
            raise ValueError("no ammunition decision is pending")
        if mode not in pending["options"]:
            raise ValueError(f"invalid ammunition mode: {mode}")
        player = self.players[pending["player"]]
        if player.weapon is None or player.weapon.card_id != "JAIL_458":
            raise ValueError("Tiny Pal is no longer equipped")
        player.weapon.ammunition = mode
        self.pending_choice = None
        self._event("ammunition_pick", player=player.index, mode=mode)

    def _resolve_corpse_spend(self, amount: int | None) -> None:
        pending = self.pending_choice
        if pending is None or pending["kind"] != "CORPSE_SPEND":
            raise ValueError("no Corpse-spend decision is pending")
        if amount not in pending["options"]:
            raise ValueError(f"invalid Corpse-spend amount: {amount}")
        player = self.players[pending["player"]]
        minion = self._find_minion(player.index, pending["entity"])
        player.corpses -= amount
        minion.attack_delta += amount
        minion.health_delta += amount
        self.pending_choice = None
        self._event(
            "corpse_spend_pick", player=player.index,
            entity=minion.entity_id, amount=amount,
        )

    def _steal_health(
        self, beneficiary: Player, target: tuple[int, int | None], amount: int
    ) -> None:
        """Transfer maximum and current Health without treating it as damage/healing."""
        target_player, target_entity = target
        if target_entity is None:
            victim = self.players[target_player]
            stolen = min(amount, max(0, victim.max_health))
            victim.max_health -= stolen
            victim.health = min(victim.health, victim.max_health)
        else:
            victim_minion = self._find_minion(target_player, target_entity)
            stolen = min(amount, max(0, victim_minion.max_health))
            victim_minion.health_delta -= stolen
        beneficiary.max_health += stolen
        beneficiary.health += stolen
        self._event(
            "health_stolen", player=beneficiary.index,
            target_player=target_player, target_entity=target_entity,
            amount=stolen,
        )

    def _fire_tiny_pal_ammunition(
        self,
        player: Player,
        weapon: Weapon,
        attacked: tuple[int, int | None],
    ) -> None:
        mode = weapon.ammunition
        enemy = self.players[1 - player.index]
        if mode == 1:
            candidates = [
                target for target in self._random_enemy_characters(player.index)
                if target != attacked
            ]
            for target in self.rng.sample(candidates, min(2, len(candidates))):
                if target[1] is None:
                    self.players[target[0]].frozen_turn = self.turn
                else:
                    self._find_minion(*target).frozen_turn = self.turn
                self._event(
                    "freeze", player=target[0], entity=target[1],
                    source=weapon.card_id,
                )
        elif mode == 2:
            self._damage_hero(enemy, 1)
            for minion in list(enemy.board):
                if minion.dormant_turns == 0:
                    self._damage_minion(enemy.index, minion, 1)
            self._resolve_deaths()
        else:
            raise UnsupportedGeneratedCard(
                f"Tiny Pal ammunition mode {mode} opens an unclosed card pool"
            )
        self._event("ammunition_fired", player=player.index, mode=mode)
        # A weapon at zero Durability was already destroyed by _hero_attack;
        # only a surviving Tiny Pal can receive another ammunition choice.
        if player.weapon is not None and player.weapon.card_id == "JAIL_458":
            self._offer_ammunition(player, exclude=mode)

    def _offer_rewind(
        self,
        player: Player,
        effect: str,
        remaining_battlecries: int = 0,
    ) -> None:
        """Resolve a random effect once, then expose Rewind as a decision.

        Rewind restores only the random card effect before rolling it one final
        time. Playing the card and paying its cost are not undone.
        """
        before_players = copy.deepcopy(self.players)
        outcome = self._run_rewind_effect(player, effect)
        self.pending_choice = {
            "kind": "REWIND",
            "player": player.index,
            "before_players": before_players,
            "effect": effect,
            "outcome": outcome,
            "remaining_battlecries": remaining_battlecries,
        }
        self._event(
            "rewind_offer",
            player=player.index,
            effect=effect,
            restorable=True,
            outcome=outcome,
        )

    def _run_rewind_effect(self, player: Player, effect: str) -> Any:
        if effect == "stadium_weapons":
            self._stadium_weapons(player)
            return self._weapon_outcome()
        if effect == "portal_vanguard":
            drawn = self._draw_matching(
                player, lambda card: card.definition.card_type == "MINION"
            )
            if drawn is not None:
                drawn.attack_delta += 2
                drawn.health_delta += 2
            return None if drawn is None else {
                "card": drawn.card_id, "entity": drawn.entity_id,
            }
        if effect == "conflux_crasher":
            targets = self._random_enemy_characters(player.index)
            if not targets:
                return None
            target = self.rng.choice(targets)
            self._deal_to_target(player.index, target, 7)
            self._resolve_deaths()
            return {"player": target[0], "entity": target[1], "damage": 7}
        if effect == "bygone_doomspeaker":
            discarded = []
            for owner in self.players:
                if not owner.hand:
                    discarded.append(None)
                    continue
                card = self.rng.choice(owner.hand)
                owner.hand.remove(card)
                discarded.append({"card": card.card_id, "entity": card.entity_id})
                self._event(
                    "discard", player=owner.index, card=card.card_id,
                    entity=card.entity_id, source="TIME_008",
                )
            return discarded
        if effect == "chrono_daggers":
            hits = []
            damage = 2 + self._spell_damage(player)
            for _ in range(3):
                targets = self._random_enemy_characters(player.index)
                if not targets:
                    break
                target = self.rng.choice(targets)
                self._deal_to_target(player.index, target, damage)
                hits.append({"player": target[0], "entity": target[1], "damage": damage})
                self._resolve_deaths()
            return hits
        if effect == "cease_to_exist":
            enemy = self.players[1 - player.index]
            targets = [
                minion for minion in enemy.board
                if minion.dormant_turns == 0 and not minion.stealth
            ]
            if not targets:
                return None
            target = self.rng.choice(targets)
            self._silence_minion(target)
            target.damage = target.max_health
            self._resolve_deaths()
            return {"player": enemy.index, "entity": target.entity_id}
        if effect == "aeon_rend":
            targets = self._random_enemy_characters(player.index)
            chosen = self.rng.sample(targets, min(2, len(targets)))
            damage = 4 + self._spell_damage(player)
            hits = []
            for target in chosen:
                self._deal_to_target(player.index, target, damage)
                hits.append({"player": target[0], "entity": target[1], "damage": damage})
            self._resolve_deaths()
            return hits
        if effect == "shadows_of_yesterday":
            summoned = []
            for _ in range(4):
                if len(player.board) + len(player.locations) >= 7:
                    break
                shade = CardInstance(
                    self.next_entity_id,
                    CardDef(
                        "TIME_610t2", "Anomalous Shade", "MINION", 2, 3, 2
                    ),
                    summoned_turn=self.turn,
                    created_by="TIME_610",
                )
                self.next_entity_id += 1
                effects = [
                    self._grant_bonus_effect(player, shade, source="TIME_610"),
                    self._grant_bonus_effect(player, shade, source="TIME_610"),
                ]
                self._summon(player, shade)
                summoned.append({"entity": shade.entity_id, "effects": effects})
            return summoned
        raise ValueError(f"unknown Rewind effect: {effect}")

    def _resolve_rewind(self, retry: bool) -> None:
        pending = self.pending_choice
        if pending is None or pending["kind"] != "REWIND":
            raise ValueError("no Rewind decision is pending")
        player = self.players[pending["player"]]
        self.pending_choice = None
        if retry:
            self.players = copy.deepcopy(pending["before_players"])
            player = self.players[pending["player"]]
            outcome = self._run_rewind_effect(player, pending["effect"])
        else:
            outcome = pending["outcome"]
        self._event(
            "rewind_pick",
            player=player.index,
            effect=pending["effect"],
            decision="retry" if retry else "keep",
            outcome=outcome,
        )
        remaining = pending["remaining_battlecries"]
        if remaining:
            self._offer_rewind(
                player, pending["effect"],
                remaining_battlecries=remaining - 1,
            )

    def _weapon_outcome(self) -> list[dict[str, Any] | None]:
        return [
            None if p.weapon is None else {
                "name": p.weapon.name,
                "card": p.weapon.card_id,
                "attack": p.weapon.attack,
                "durability": p.weapon.durability,
            }
            for p in self.players
        ]

    def _use_location(self, action: Action) -> None:
        player = self.players[self.current]
        location = next(x for x in player.locations if x.entity_id == action.source)
        context_card = CardInstance(location.entity_id, self.card_defs[location.card_id])
        if self.rule_registry.dispatch(
            Hook.LOCATION, location.card_id, self,
            RuleContext(player=player, card=context_card, action=action),
        ):
            pass
        elif location.card_id == "CORE_REV_990":
            target = self._find_minion(action.target_player, action.target_entity)
            self._damage_minion(action.target_player, target, 1)
            if target.health > 0:
                target.attack_delta += 2
        elif location.card_id == "CATA_584":
            missiles = 6 if player.fire_spell_played else 3
            for _ in range(missiles):
                targets = self._random_enemy_characters(player.index)
                if not targets:
                    break
                self._deal_to_target(player.index, self.rng.choice(targets), 1)
                self._resolve_deaths()
        location.durability -= 1
        location.cooldown = 1
        if location.durability <= 0:
            player.locations.remove(location)

    def _attack(self, action: Action) -> None:
        attacker = self._find_minion(self.current, action.source)
        attacker.attacks_this_turn += 1
        attacker.stealth = False
        if action.target_entity is None:
            self._damage_hero(self.players[action.target_player], attacker.attack, attacker)
        else:
            defender = self._find_minion(action.target_player, action.target_entity)
            self._damage_minion(action.target_player, defender, attacker.attack, attacker)
            self._damage_minion(self.current, attacker, defender.attack, defender)
            self._finja_kill(self.current, attacker, defender)
            self._after_minion_attacked(action.target_player, defender)
            if attacker.card_id == "DINO_401" and not attacker.silenced:
                enemy = self.players[action.target_player]
                for other in list(enemy.board):
                    if (
                        other.entity_id != defender.entity_id
                        and other.dormant_turns == 0
                    ):
                        self._damage_minion(
                            enemy.index, other, attacker.attack, attacker
                        )
        self._after_minion_attack(
            self.current, attacker,
            attacked_minion=action.target_entity is not None,
        )

    def _hero_attack(self, action: Action) -> None:
        player = self.players[self.current]
        attacked_weapon = copy.deepcopy(player.weapon)
        attack_amount = player.attack
        player.hero_attacks_this_turn += 1
        if action.target_entity is None:
            enemy = self.players[action.target_player]
            before = enemy.health + enemy.armor
            self._damage_hero(self.players[action.target_player], player.attack)
            dealt = before - (enemy.health + enemy.armor)
            self._weapon_lifesteal(player, attacked_weapon, dealt)
        else:
            defender = self._find_minion(action.target_player, action.target_entity)
            before = max(0, defender.health)
            self._damage_minion(action.target_player, defender, player.attack)
            if (
                defender.health <= 0
                and player.weapon
                and player.weapon.card_id == "CORE_RLK_086"
            ):
                player.weapon.killed_minions.append(copy.deepcopy(defender.definition))
            dealt = before - max(0, defender.health)
            self._weapon_lifesteal(player, attacked_weapon, dealt)
            self._damage_hero(player, defender.attack)
            self._after_minion_attacked(action.target_player, defender)
        if player.weapon:
            player.weapon.durability -= 1
            if player.weapon.durability <= 0:
                self._destroy_weapon(player)
        self._after_hero_attack(
            player,
            attacked_weapon,
            (action.target_player, action.target_entity),
            attack_amount,
        )
        for inquisitor in list(player.board):
            if (
                inquisitor.card_id != "CS3_020"
                or inquisitor.silenced
                or inquisitor.dormant_turns > 0
                or inquisitor.health <= 0
            ):
                continue
            if action.target_entity is None:
                self._damage_hero(
                    self.players[action.target_player], inquisitor.attack,
                    inquisitor,
                )
                inquisitor.attacks_this_turn += 1
                self._after_minion_attack(player.index, inquisitor)
            else:
                target = next(
                    (m for m in self.players[action.target_player].board
                     if m.entity_id == action.target_entity and m.health > 0),
                    None,
                )
                if target is not None:
                    self._forced_minion_attack(
                        player.index, inquisitor,
                        action.target_player, target,
                    )
            self._event(
                "illidari_inquisitor_attack", player=player.index,
                entity=inquisitor.entity_id,
                target_player=action.target_player,
                target=action.target_entity,
            )
        for hookfist in list(player.board):
            if (
                hookfist.card_id == "CORE_NX2_028"
                and not hookfist.silenced
                and hookfist.dormant_turns == 0
            ):
                self._gain_armor(player, 4)
                self._draw(player)
                self._event(
                    "hookfist_trigger", player=player.index,
                    entity=hookfist.entity_id,
                )
        for battlefiend in player.board:
            if (
                battlefiend.card_id == "CORE_BT_351"
                and not battlefiend.silenced
                and battlefiend.dormant_turns == 0
            ):
                battlefiend.attack_delta += 1
                self._event(
                    "battlefiend_trigger", player=player.index,
                    entity=battlefiend.entity_id,
                )

    def _weapon_lifesteal(self, player: Player, weapon: Weapon | None, dealt: int) -> None:
        if weapon and weapon.card_id in {"CORE_BT_921", "RLK_067"} and dealt > 0:
            player.health = min(player.max_health, player.health + dealt)

    def _deal_to_target(
        self, source_player: int, target: tuple[int, int | None], amount: int,
        source: CardInstance | None = None,
    ) -> None:
        player_index, entity_id = target
        if entity_id is None:
            self._damage_hero(self.players[player_index], amount, source)
        else:
            self._damage_minion(
                player_index, self._find_minion(player_index, entity_id),
                amount, source,
            )

    def _pirate_damage_bonus(self, source: CardInstance | None) -> int:
        if source is None or not source.has_race("PIRATE"):
            return 0
        player = self.players[self.current]
        if source not in player.board:
            return 0
        return sum(
            minion.card_id == "CAP_104"
            and not minion.silenced
            and minion.dormant_turns == 0
            for minion in player.board
        )

    def _source_controller(self, source: CardInstance) -> Player:
        for player in self.players:
            if any(
                minion.entity_id == source.entity_id
                for minion in player.board + player.dead_minions
            ):
                return player
        return self.players[self.current]

    def _modified_damage(
        self, amount: int, source: CardInstance | None
    ) -> int:
        amount += self._pirate_damage_bonus(source)
        if source is None:
            return amount
        owner = self._source_controller(source)
        active = [
            minion for minion in owner.board
            if not minion.silenced
            and minion.dormant_turns == 0
            and minion.health > 0
        ]
        if source.has_race("ELEMENTAL"):
            amount += sum(m.card_id == "TLC_228" for m in active)
        if source.has_race("BEAST") and any(
            minion.card_id == "EDR_480" for minion in active
        ):
            amount *= 2
        return amount

    def _gain_armor(self, player: Player, amount: int) -> None:
        if amount <= 0:
            return
        player.armor += amount
        self._event("gain_armor", player=player.index, amount=amount)
        bashers = [
            minion for minion in player.board
            if minion.card_id == "DINO_400"
            and not minion.silenced
            and minion.dormant_turns == 0
        ]
        for basher in bashers:
            if basher not in player.board:
                continue
            basher.attack_delta += 2
            basher.health_delta += 2
            enemy = self.players[1 - player.index]
            targets = [
                minion for minion in enemy.board
                if minion.dormant_turns == 0
            ]
            if targets:
                self._forced_minion_attack(
                    player.index, basher, enemy.index,
                    self.rng.choice(targets),
                )

    def _damage_hero(self, player: Player, amount: int, source: CardInstance | None = None) -> None:
        amount = self._modified_damage(amount, source)
        if amount <= 0:
            return
        if any(
            minion.card_id == "CORE_CATA_001"
            and not minion.silenced
            and minion.dormant_turns == 0
            for minion in player.board
        ):
            self._event("hero_immune", player=player.index, amount=amount)
            return
        if player.hero_divine_shield:
            player.hero_divine_shield_hits = max(
                1, player.hero_divine_shield_hits
            ) - 1
            if player.hero_divine_shield_hits == 0:
                player.hero_divine_shield = False
                player.hero_divine_shield_toreth = False
            self._event(
                "hero_divine_shield", player=player.index, amount=amount,
                remaining_hits=player.hero_divine_shield_hits,
            )
            return
        if player.weapon and player.weapon.card_id == "CORE_BT_781":
            player.weapon.durability -= 1
            self._event("bulwark_absorb", player=player.index, amount=amount)
            if player.weapon.durability <= 0:
                self._destroy_weapon(player)
            return
        absorbed = min(player.armor, amount)
        player.armor -= absorbed
        player.health -= amount - absorbed
        self.players[player.index].damaged_characters_this_turn.add(f"hero:{player.index}")
        if source and source.lifesteal:
            owner = self.players[1 - player.index]
            owner.health = min(owner.max_health, owner.health + amount)
        self._check_warptooth(player.index)

    def _damage_minion(self, player_index: int, minion: CardInstance, amount: int,
                       source: CardInstance | None = None) -> None:
        amount = self._modified_damage(amount, source)
        if minion.card_id == "TIME_060" and not minion.silenced:
            amount *= 2
        if amount <= 0:
            return
        if minion.immune:
            return
        if minion.divine_shield:
            minion.divine_shield_hits = max(1, minion.divine_shield_hits) - 1
            if minion.divine_shield_hits == 0:
                minion.divine_shield = False
                minion.divine_shield_toreth = False
            return
        minion.damage += amount
        if minion.illusion_fake and not minion.silenced:
            minion.damage = max(minion.damage, minion.max_health)
            self._event(
                "illusion_revealed", player=player_index,
                entity=minion.entity_id,
            )
        if source and (source.poisonous or source.aura_poisonous):
            minion.damage = max(minion.damage, minion.max_health)
        self.players[player_index].damaged_characters_this_turn.add(f"minion:{minion.entity_id}")

        # Damage triggers happen after damage is marked but before the next
        # death-processing pass. This lets effects that explicitly require a
        # survivor inspect health while global "takes damage" triggers still
        # observe lethal damage events.
        if minion.card_id == "EDR_471" and not minion.silenced:
            minion.attack_delta += 1
            self._gain_armor(self.players[player_index], 1)
            self._event(
                "tortolla_damaged", player=player_index,
                entity=minion.entity_id,
            )
        for owner in self.players:
            for berserker in owner.board:
                if (
                    berserker.card_id == "CORE_EX1_604"
                    and not berserker.silenced
                    and berserker.dormant_turns == 0
                ):
                    berserker.attack_delta += 1
        if minion in self.players[player_index].board and minion.health > 0:
            for rioter in self.players[player_index].board:
                if (
                    rioter.card_id == "JAIL_029"
                    and not rioter.silenced
                    and rioter.dormant_turns == 0
                ):
                    minion.attack_delta += 1
            if (
                minion.card_id == "CATA_586"
                and not minion.silenced
                and len(self.players[player_index].board)
                    + len(self.players[player_index].locations) < 7
            ):
                copy_minion = self._entity(
                    "CATA_586", created_by=minion.card_id
                )
                copy_minion.summoned_turn = self.turn
                self._summon(self.players[player_index], copy_minion)
                self._event(
                    "destructive_blaze_summon", player=player_index,
                    source=minion.entity_id, entity=copy_minion.entity_id,
                )
        if source and source.lifesteal:
            owner = self.players[1 - player_index]
            owner.health = min(owner.max_health, owner.health + amount)
        self._check_warptooth(player_index)

    def _check_warptooth(self, damaged_owner: int) -> None:
        # Only damage during that player's own turn advances their condition.
        if damaged_owner != self.current:
            return
        player = self.players[damaged_owner]
        if len(player.damaged_characters_this_turn) < 4:
            return
        while len(player.board) + len(player.locations) < 7:
            found = None
            for zone in (player.hand, player.deck):
                for i, card in enumerate(zone):
                    if card.card_id == "JAIL_421":
                        found = zone.pop(i)
                        break
                if found:
                    break
            if not found:
                return
            found.summoned_turn = self.turn
            self._summon(player, found)
            self._event("summon_from_zone", player=player.index, card="JAIL_421")

    def _resolve_deaths(self) -> None:
        while True:
            for candidate in self.players:
                self._refresh_continuous(candidate)
            dead = [
                (player, minion)
                for player in self.players
                for minion in player.board
                if minion.health <= 0
            ]
            if not dead:
                return

            corpse_multipliers = {
                player.index: 2 ** sum(
                    minion.card_id == "CORE_EDR_003"
                    and not minion.silenced
                    and minion.dormant_turns == 0
                    and minion.health > 0
                    for minion in player.board
                )
                for player in self.players
            }

            # Remove the entire death batch before any Deathrattle runs. This
            # prevents an early trigger from targeting a minion that has
            # already taken lethal damage in the same event.
            for player, minion in dead:
                player.board.remove(minion)
                player.dead_minions.append(copy.deepcopy(minion))
                self._event(
                    "minion_died", player=player.index, card=minion.card_id,
                    entity=minion.entity_id,
                )
                gained = corpse_multipliers[player.index]
                player.corpses += gained
                if gained > 1:
                    self._event(
                        "corpse_multiplier", player=player.index,
                        entity=minion.entity_id, gained=gained,
                    )
            self.minions_died_this_turn += len(dead)

            for owner in self.players:
                if not any(player is owner for player, _ in dead):
                    continue
                for direhorn in owner.board:
                    if (
                        direhorn.card_id == "DINO_416"
                        and not direhorn.silenced
                        and direhorn.dormant_turns == 0
                        and not direhorn.reborn
                        and owner.corpses >= 3
                    ):
                        owner.corpses -= 3
                        direhorn.reborn = True
                        self._event(
                            "direhorn_reborn", player=owner.index,
                            entity=direhorn.entity_id, spent=3,
                        )

            for player, minion in dead:
                if minion.card_id == "EDR_465":
                    player.ysondre_deaths += 1
                    self._event(
                        "ysondre_death_count", player=player.index,
                        count=player.ysondre_deaths,
                    )

            # Aura loss may make another damaged minion lethal; recompute
            # before Deathrattles can create or damage further entities.
            for candidate in self.players:
                self._refresh_continuous(candidate)

            for player, minion in dead:
                if not minion.silenced:
                    self._deathrattle(player, minion)
                if minion.reborn and len(player.board) + len(player.locations) < 7:
                    reborn = minion.clone(self.next_entity_id)
                    self.next_entity_id += 1
                    reborn.reborn = False
                    reborn.damage = (
                        0 if minion.card_id == "CAP_800"
                        else reborn.max_health - 1
                    )
                    reborn.summoned_turn = self.turn
                    self._summon(player, reborn)
                    self._event(
                        "reborn", player=player.index, card=reborn.card_id,
                        entity=reborn.entity_id,
                    )

            for player in self.players:
                self._summon_magmaw_bodies(player)

    def _summon_magmaw_bodies(self, player: Player) -> None:
        source = next(
            (
                minion for minion in player.board
                if minion.entity_id == player.magmaw_entity
                and minion.card_id == "CATA_550"
                and not minion.silenced
            ),
            None,
        )
        if source is None:
            player.pending_magmaw_bodies = 0
            player.magmaw_entity = None
            return
        while (
            player.pending_magmaw_bodies > 0
            and len(player.board) + len(player.locations) < 7
        ):
            body = self._instance_from_definition(
                CardDef(
                    "CATA_550t", "Magmaw's Body", "MINION", 1,
                    2, 1, "BEAST", ("DEATHRATTLE",), "HUNTER",
                    ("BEAST", "MECHANICAL"), "CATACLYSM",
                ),
                created_by=source.card_id,
            )
            body.summoned_turn = self.turn
            self._summon(player, body)
            player.pending_magmaw_bodies -= 1
            self._event(
                "magmaw_body", player=player.index,
                entity=body.entity_id, remaining=player.pending_magmaw_bodies,
            )

    def _deathrattle(self, player: Player, minion: CardInstance) -> None:
        self.rule_registry.dispatch(
            Hook.DEATHRATTLE, minion.card_id, self,
            RuleContext(player=player, card=minion),
        )
        if minion.card_id in {
            "DINO_410", "DINO_410t2", "DINO_410t3", "DINO_410t4",
            "DINO_410t5",
        }:
            next_stage = {
                "DINO_410": "DINO_410t2",
                "DINO_410t2": "DINO_410t3",
                "DINO_410t3": "DINO_410t4",
                "DINO_410t4": "DINO_410t5",
                "DINO_410t5": "DINO_410t",
            }[minion.card_id]
            if len(player.board) + len(player.locations) < 7:
                hatch = self._entity(next_stage, created_by="DINO_410")
                hatch.summoned_turn = self.turn
                self._summon(player, hatch)
                self._event(
                    "khelos_egg_stage", player=player.index,
                    source=minion.entity_id, summoned=hatch.entity_id,
                    stage=next_stage,
                )
        elif minion.card_id == "CS3_024":
            candidates = [
                card for card in player.deck
                if card.definition.card_type == "MINION"
            ]
            if candidates:
                highest = max(self._effective_cost(player, card) for card in candidates)
                self._draw_matching(
                    player,
                    lambda card: (
                        card.definition.card_type == "MINION"
                        and self._effective_cost(player, card) == highest
                    ),
                )
        elif minion.card_id == "FIR_958":
            enemy = self.players[1 - player.index]
            amount = 4 if self.current != player.index else 1
            self._damage_hero(enemy, amount, minion)
            for target in list(enemy.board):
                self._damage_minion(enemy.index, target, amount, minion)
        elif minion.card_id == "CORE_BT_201":
            for _ in range(minion.attack):
                targets = self._random_enemy_characters(player.index)
                if not targets:
                    break
                self._deal_to_target(
                    player.index, self.rng.choice(targets), 1, source=minion
                )
                self._resolve_deaths()
        elif minion.card_id == "TLC_401":
            targets = self._random_enemy_characters(player.index)
            for target in self.rng.sample(targets, min(3, len(targets))):
                self._deal_to_target(player.index, target, 6, source=minion)
            self._resolve_deaths()
        elif minion.card_id == "FIR_919":
            player.pending_phoenixes += 1
            self._event(
                "phoenix_return_scheduled", player=player.index,
                pending=player.pending_phoenixes,
            )
        elif minion.card_id == "TLC_240":
            for _ in range(3):
                if len(player.board) + len(player.locations) >= 7:
                    break
                murloc = CardInstance(
                    self.next_entity_id,
                    CardDef(
                        "TLC_240t", "Tyrannogill Spawn", "MINION", 1,
                        2, 1, "MURLOC", (), "NEUTRAL", ("MURLOC",),
                        "THE_LOST_CITY",
                    ),
                    summoned_turn=self.turn,
                    created_by=minion.card_id,
                )
                self.next_entity_id += 1
                self._summon(player, murloc)
                effect = self.rng.choice(BONUS_EFFECTS)
                setattr(murloc, effect, True)
                self._event(
                    "bonus_effect", player=player.index,
                    source=minion.card_id, target=murloc.entity_id,
                    effect=effect,
                )
        elif minion.card_id == "CATA_550t":
            candidates = [other for other in player.board if other.health > 0]
            if candidates:
                target = self.rng.choice(candidates)
                target.attack_delta += 2
                self._event(
                    "magmaw_body_buff", player=player.index,
                    source=minion.entity_id, target=target.entity_id,
                )
        elif minion.card_id == "EDR_818":
            for _ in range(minion.attack):
                if len(player.board) + len(player.locations) >= 7:
                    break
                beetle = self._instance_from_definition(
                    CardDef(
                        "EDR_818t", "Nythendric Beetle", "MINION", 1,
                        1, 1, "BEAST", ("TRIGGER_VISUAL",), "DEATHKNIGHT",
                        ("BEAST", "UNDEAD"), "EMERALD_DREAM",
                    ),
                    created_by=minion.card_id,
                )
                beetle.summoned_turn = self.turn
                self._summon(player, beetle)
        elif minion.card_id == "CATA_464":
            breath = self._instance_from_definition(
                CardDef(
                    "CATA_464t", "Dragon Breath", "SPELL", 2,
                    card_class="DEATHKNIGHT", card_set="CATACLYSM",
                    text=f"Deal {minion.attack} damage.",
                ),
                created_by=minion.card_id,
            )
            breath.dynamic_spell_damage = minion.attack
            if len(player.hand) < 10:
                player.hand.append(breath)
                self._event(
                    "generated", player=player.index, card=breath.card_id,
                    source=minion.card_id, damage=breath.dynamic_spell_damage,
                )
            else:
                self._event(
                    "generated_burned", player=player.index,
                    card=breath.card_id, source=minion.card_id,
                )
        elif minion.card_id == "TIME_017":
            if len(player.board) + len(player.locations) < 7:
                tank = self._instance_from_definition(
                    CardDef(
                        "TIME_017t", "Tank", "MINION", 7, 7, 7,
                        "MECHANICAL", ("DIVINE_SHIELD",), "NEUTRAL",
                        ("MECHANICAL",), "TIME_TRAVEL",
                    ),
                    created_by=minion.card_id,
                )
                tank.divine_shield = True
                tank.summoned_turn = self.turn
                self._summon(player, tank)
        elif minion.card_id == "TIME_603":
            enemy = self.players[1 - player.index]
            targets = [m for m in enemy.board if m.health > 0]
            if targets:
                target = self.rng.choice(targets)
                target.damage = target.max_health
                self._event(
                    "timebomb", player=player.index,
                    target=target.entity_id,
                )
        elif minion.card_id == "TIME_713t":
            beneficiary = self.players[1 - player.index]
            while len(beneficiary.hand) < 10:
                coin = self._entity("GAME_005", created_by=minion.card_id)
                beneficiary.hand.append(coin)
            self._event(
                "chest_coins", player=beneficiary.index,
                hand_size=len(beneficiary.hand),
            )
        elif minion.card_id == "CATA_210":
            if len(player.board) + len(player.locations) < 7:
                bonus = minion.twilight_whelp_bonus
                whelp = CardInstance(
                    self.next_entity_id,
                    CardDef(
                        "CATA_210t", "Accelerated Whelp", "MINION", 2,
                        2 + bonus, 1 + bonus, "DRAGON", (), "NEUTRAL",
                        ("DRAGON",), "CATACLYSM",
                    ),
                    summoned_turn=self.turn,
                    created_by=minion.card_id,
                )
                self.next_entity_id += 1
                self._summon(player, whelp)
        elif minion.card_id == "CORE_SW_439":
            for _ in range(4):
                acorn = CardInstance(
                    self.next_entity_id,
                    CardDef(
                        "CORE_SW_439t", "Squirrel", "MINION", 1, 2, 1,
                        "BEAST", (), "DRUID", ("BEAST",), "CORE",
                    ),
                    created_by=minion.card_id,
                    summoned_when_drawn=True,
                )
                self.next_entity_id += 1
                player.deck.append(acorn)
            self.rng.shuffle(player.deck)
        elif minion.card_id == "JAIL_442":
            for _ in range(4):
                blight = CardInstance(
                    self.next_entity_id,
                    CardDef(
                        "JAIL_442t", "Blight", "SPELL", 1,
                        card_class="DEATHKNIGHT",
                        card_set="ESCAPEFROM_VIOLET_HOLD",
                    ),
                    created_by=minion.card_id,
                    casts_when_drawn_damage=2,
                )
                self.next_entity_id += 1
                player.deck.append(blight)
            self.rng.shuffle(player.deck)
        elif minion.card_id == "EDR_891":
            candidates = [
                dead for dead in player.dead_minions
                if dead.entity_id != minion.entity_id
                and dead.definition.cost <= 4
                and "DEATHRATTLE" in dead.definition.mechanics
            ]
            if candidates:
                chosen = self.rng.choice(candidates)
                summoned: list[int] = []
                for _ in range(2):
                    if len(player.board) + len(player.locations) >= 7:
                        break
                    restored = self._instance_from_definition(
                        chosen.definition, created_by=minion.card_id
                    )
                    restored.summoned_turn = self.turn
                    self._summon(player, restored)
                    summoned.append(restored.entity_id)
                self._event(
                    "ravenous_felhunter_resurrect", player=player.index,
                    card=chosen.card_id, summoned=summoned,
                )
        elif minion.card_id == "EDR_892":
            candidates = [
                dead for dead in player.dead_minions
                if dead.entity_id != minion.entity_id
                and dead.card_id != minion.card_id
                and dead.definition.cost >= 5
                and "DEATHRATTLE" in dead.definition.mechanics
            ]
            if candidates:
                chosen = self.rng.choice(candidates)
                summoned: list[int] = []
                for _ in range(2):
                    if len(player.board) + len(player.locations) >= 7:
                        break
                    restored = self._instance_from_definition(
                        chosen.definition, created_by=minion.card_id
                    )
                    restored.summoned_turn = self.turn
                    self._summon(player, restored)
                    summoned.append(restored.entity_id)
                self._event(
                    "ferocious_felbat_resurrect", player=player.index,
                    card=chosen.card_id, summoned=summoned,
                )
        elif minion.card_id == "JAIL_906":
            candidates = [card for card in player.deck if card.has_race("DEMON")]
            if candidates and len(player.board) + len(player.locations) < 7:
                demon = self.rng.choice(candidates)
                player.deck.remove(demon)
                demon.summoned_turn = self.turn
                demon.summon_moragg_on_death = True
                self._summon(player, demon)
                self._event(
                    "moragg_summon", player=player.index,
                    card=demon.card_id, entity=demon.entity_id,
                )
        elif minion.card_id == "EDR_421":
            enemy = self.players[1 - player.index]
            self._damage_hero(enemy, minion.omen_damage, minion)
            for target in list(enemy.board):
                self._damage_minion(
                    enemy.index, target, minion.omen_damage, minion
                )

        elif minion.card_id == "CORE_YOD_026":
            candidates = [
                target for target in player.board
                if target.dormant_turns == 0 and target.health > 0
            ]
            if candidates:
                target = self.rng.choice(candidates)
                target.attack_delta += minion.attack
                self._event(
                    "fiendish_attack_gift", player=player.index,
                    target=target.entity_id, amount=minion.attack,
                )
        elif minion.card_id == "TLC_249":
            for _ in range(2):
                targets = self._random_enemy_characters(player.index)
                if not targets:
                    break
                self._deal_to_target(
                    player.index, self.rng.choice(targets), 1, source=minion
                )
                self._resolve_deaths()
        elif minion.card_id == "CORE_AT_123" and self._holding_dragon(player):
            for owner, entity in list(self._all_minions()):
                self._damage_minion(owner, self._find_minion(owner, entity), 3)
        elif minion.card_id == "EDR_465":
            summoned: list[str] = []
            for _ in range(player.ysondre_deaths):
                if len(player.board) + len(player.locations) >= 7:
                    break
                dragon_id = self.rng.choice(sorted(DRAGON_IDS))
                dragon = self._entity(dragon_id, created_by=minion.card_id)
                dragon.summoned_turn = self.turn
                self._summon(player, dragon)
                summoned.append(dragon_id)
            self._event(
                "ysondre_summon", player=player.index,
                death_count=player.ysondre_deaths, cards=summoned,
                profile="closed_pool",
            )
        elif minion.card_id in {"CATA_580t", "CATA_150t"}:
            targets = self._random_enemy_characters(player.index)
            if targets:
                self._deal_to_target(
                    player.index, self.rng.choice(targets),
                    2 * minion.herald_power,
                )
        elif minion.card_id == "CATA_586":
            targets = self._random_enemy_characters(player.index)
            if targets:
                self._deal_to_target(
                    player.index, self.rng.choice(targets), 2,
                    source=minion,
                )

        if minion.summon_moragg_on_death:
            definition = self.card_defs["JAIL_906"]
            if len(player.board) + len(player.locations) < 7:
                moragg = self._instance_from_definition(
                    definition, created_by=minion.card_id
                )
                moragg.summoned_turn = self.turn
                self._summon(player, moragg)
                self._event(
                    "moragg_return", player=player.index,
                    source=minion.entity_id, entity=moragg.entity_id,
                )

    def _check_winner(self) -> None:
        dead = [p.index for p in self.players if p.health <= 0]
        if dead:
            self.finished = True
            self.winner = None if len(dead) == 2 else 1 - dead[0]

    def _card_label(self, card: CardInstance) -> str:
        gifts = f" gift={','.join(card.gifts)}" if card.gifts else ""
        return (
            f"{card.definition.name}[{card.card_id}]#{card.entity_id} "
            f"{card.attack}/{card.health} cost={self._effective_cost(self.players[self.current], card)}{gifts}"
        )

    def _target_label(self, player_index: int | None, entity_id: int | None) -> str:
        if player_index is None:
            return "-"
        if entity_id is None:
            return f"P{player_index + 1} hero"
        try:
            minion = self._find_minion(player_index, entity_id)
            return f"P{player_index + 1} {minion.definition.name}#{entity_id}"
        except ValueError:
            return f"P{player_index + 1} entity#{entity_id}"

    def describe_action(self, action: Action) -> str:
        player = self.players[self.current]
        if action.kind == "MULLIGAN_TOGGLE":
            card = next(c for c in player.hand if c.entity_id == action.source)
            selected = action.source in self.pending_choice["selected"]
            verb = "KEEP" if selected else "REPLACE"
            return (
                f"P{self.current + 1} MULLIGAN_{verb} "
                f"{card.definition.name}[{card.card_id}]"
            )
        if action.kind == "MULLIGAN_CONFIRM":
            return f"P{self.current + 1} MULLIGAN_CONFIRM"
        if action.kind == "DISCOVER_PICK":
            option = next(
                card for card in self.pending_choice["options"]
                if card.entity_id == action.source
            )
            gift = f" + {option.gifts[0]}" if option.gifts else ""
            choice_kind = self.pending_choice["kind"]
            return (
                f"P{self.current + 1} {choice_kind}_PICK "
                f"{option.definition.name}[{option.card_id}]{gift}"
            )
        if action.kind == "REWIND_KEEP":
            return f"P{self.current + 1} REWIND_KEEP"
        if action.kind == "REWIND_RETRY":
            return f"P{self.current + 1} REWIND_RETRY"
        if action.kind == "PREPARE":
            card = next(c for c in player.hand if c.entity_id == action.source)
            return f"P{self.current + 1} PREPARE {card.definition.name}[{card.card_id}]"
        if action.kind == "AMMUNITION_PICK":
            return f"P{self.current + 1} AMMUNITION_PICK mode={action.source}"
        if action.kind == "CORPSE_SPEND":
            return f"P{self.current + 1} CORPSE_SPEND amount={action.source}"
        if action.kind == "RULE_CHOICE_PICK":
            label = self.pending_choice["options"][action.source][0]
            return f"P{self.current + 1} CHOOSE_ONE {label}"
        source_card = next(
            (c for c in player.hand + player.board if c.entity_id == action.source),
            None,
        )
        if action.kind == "PLAY":
            return f"P{self.current + 1} PLAY {source_card.definition.name}[{source_card.card_id}] -> {self._target_label(action.target_player, action.target_entity)}"
        if action.kind == "TRADE":
            return f"P{self.current + 1} TRADE {source_card.definition.name}[{source_card.card_id}]"
        if action.kind == "ATTACK":
            return f"P{self.current + 1} ATTACK {source_card.definition.name}#{source_card.entity_id} -> {self._target_label(action.target_player, action.target_entity)}"
        if action.kind == "HERO_ATTACK":
            return f"P{self.current + 1} HERO_ATTACK -> {self._target_label(action.target_player, action.target_entity)}"
        if action.kind == "LOCATION":
            location = next(x for x in player.locations if x.entity_id == action.source)
            return f"P{self.current + 1} LOCATION {location.card_id}#{location.entity_id} -> {self._target_label(action.target_player, action.target_entity)}"
        if action.kind == "HERO_POWER":
            return f"P{self.current + 1} HERO_POWER {player.hero_power_id or player.card_class}"
        return f"P{self.current + 1} END_TURN"

    def snapshot(self) -> dict[str, Any]:
        for player in self.players:
            self._refresh_continuous(player)

        def card_state(card: CardInstance, owner: Player) -> dict[str, Any]:
            return {
                "entity": card.entity_id,
                "id": card.card_id,
                "name": card.definition.name,
                "card_class": card.definition.card_class,
                "card_set": card.definition.card_set,
                "races": list(card.definition.races),
                "cost": self._effective_cost(owner, card),
                "attack": card.attack,
                "health": card.health,
                "max_health": card.max_health,
                "damage": card.damage,
                "gifts": list(card.gifts),
                "started_in_deck": card.started_in_deck,
                "created_by": card.created_by,
                "dormant_turns": card.dormant_turns,
                "played_turn": card.played_turn,
                "summoned_when_drawn": card.summoned_when_drawn,
                "infinite_attack_next_turn": card.infinite_attack_next_turn,
                "herald_power": card.herald_power,
                "burning_turns": card.burning_turns,
                "twilight_whelp_bonus": card.twilight_whelp_bonus,
                "void_soul_cost": card.void_soul_cost,
                "omen_damage": card.omen_damage,
                "summon_moragg_on_death": card.summon_moragg_on_death,
                "frozen": card.frozen_turn >= 0,
                "cant_attack": card.cant_attack,
                "mirrex_tracker": card.mirrex_tracker,
                "spell_damage_bonus": card.spell_damage_bonus,
                "prepared_turn": card.prepared_turn,
                "dynamic_spell_damage": card.dynamic_spell_damage,
                "illusion_fake": card.illusion_fake,
                "cant_attack_heroes_turn": card.cant_attack_heroes_turn,
                "divine_shield_hits": card.divine_shield_hits,
                "keywords": [
                    name for name, enabled in (
                        ("taunt", self._has_taunt(owner.index, card)), ("rush", card.rush),
                        ("charge", card.charge), ("lifesteal", card.lifesteal),
                        ("elusive", card.elusive), ("stealth", card.stealth),
                        ("divine_shield", card.divine_shield),
                        ("windfury", card.windfury), ("reborn", card.reborn),
                        ("poisonous", card.poisonous or card.aura_poisonous),
                        ("immune", card.immune),
                    ) if enabled
                ],
            }

        players = []
        for player in self.players:
            players.append({
                "player": player.index + 1,
                "health": player.health,
                "max_health": player.max_health,
                "armor": player.armor,
                "mana": player.mana,
                "max_mana": player.max_mana,
                "hero_attack": player.attack,
                "hero_power_cost": self._hero_power_cost(player),
                "hero_power_id": player.hero_power_id,
                "hero_power_armor": player.hero_power_armor,
                "spell_damage": self._spell_damage(player),
                "herald_count": player.herald_count,
                "geddon_draw": player.geddon_draw,
                "ysondre_deaths": player.ysondre_deaths,
                "void_soul_level": player.void_soul_level,
                "frozen": player.frozen_turn >= 0,
                "cards_played_this_turn": player.cards_played_this_turn,
                "dragons_played_this_turn": player.dragons_played_this_turn,
                "generated_cards_played": player.generated_cards_played,
                "pending_phoenixes": player.pending_phoenixes,
                "corpses": player.corpses,
                "pending_magmaw_bodies": player.pending_magmaw_bodies,
                "overloaded_mana_this_game": player.overloaded_mana_this_game,
                "overload_next_turn": player.overload_next_turn,
                "locked_mana": player.locked_mana,
                "next_demon_free": player.next_demon_free,
                "hero_divine_shield": player.hero_divine_shield,
                "hero_divine_shield_hits": player.hero_divine_shield_hits,
                "turns_taken": player.turns_taken,
                "weapon": None if player.weapon is None else {
                    "card": player.weapon.card_id,
                    "name": player.weapon.name,
                    "attack": player.weapon.attack,
                    "durability": player.weapon.durability,
                    "kills": [card.card_id for card in player.weapon.killed_minions],
                    "ammunition": player.weapon.ammunition,
                },
                "hand": [card_state(card, player) for card in player.hand],
                "deck_count": len(player.deck),
                "dead_minions": [card.card_id for card in player.dead_minions],
                "board": [card_state(card, player) for card in player.board],
                "locations": [
                    {"entity": x.entity_id, "id": x.card_id,
                     "durability": x.durability, "cooldown": x.cooldown}
                    for x in player.locations
                ],
                "fatigue": player.fatigue,
            })
        pending = None
        if self.pending_choice:
            pending = {"kind": self.pending_choice["kind"]}
            if self.pending_choice["kind"] == "MULLIGAN":
                owner = self.players[self.pending_choice["player"]]
                selected = self.pending_choice["selected"]
                pending["player"] = self.pending_choice["player"] + 1
                pending["options"] = [
                    {
                        **card_state(card, owner),
                        "replace": card.entity_id in selected,
                    }
                    for card in owner.hand
                    if card.entity_id in self.pending_choice["options"]
                ]
            elif self.pending_choice["kind"] in {
                "DISCOVER", "GEDDON_DRAW", "DECK_CARD_DISCOVER", "IMBUE_PICK"
            }:
                pending["options"] = [
                    card_state(card, self.players[self.current])
                    for card in self.pending_choice["options"]
                ]
            elif self.pending_choice["kind"] == "REWIND":
                pending["options"] = ["REWIND_KEEP", "REWIND_RETRY"]
            elif self.pending_choice["kind"] == "RULE_CHOICE":
                pending["options"] = [
                    label for label, _ in self.pending_choice["options"]
                ]
            else:
                pending["options"] = list(self.pending_choice["options"])
        return {
            "turn": self.turn,
            "active_player": self.current + 1,
            "finished": self.finished,
            "winner": None if self.winner is None else self.winner + 1,
            "pending_choice": pending,
            "minions_died_this_turn": self.minions_died_this_turn,
            "players": players,
        }

    def choose_random_action(self) -> Action:
        legal = self.legal_actions()
        if self.pending_choice and self.pending_choice["kind"] == "MULLIGAN":
            player = self.players[self.current]
            desired = {
                card.entity_id for card in player.hand
                if card.entity_id in self.pending_choice["options"]
                and card.definition.cost >= 4
            }
            selected = self.pending_choice["selected"]
            mismatch = sorted(desired ^ selected)
            return (
                Action("MULLIGAN_TOGGLE", mismatch[0])
                if mismatch else Action("MULLIGAN_CONFIRM")
            )
        if self.pending_choice:
            return self.rng.choice(legal)
        non_end = [action for action in legal if action.kind != "END_TURN"]
        return (
            self.rng.choice(non_end)
            if non_end and self.rng.random() < 0.78
            else Action("END_TURN")
        )

    def run_random(self, max_actions: int = 5000) -> dict[str, Any]:
        actions = 0
        while not self.finished and actions < max_actions:
            choice = self.choose_random_action()
            self.step(choice)
            actions += 1
        digest = hashlib.sha256(
            json.dumps(self.events, ensure_ascii=True, sort_keys=True).encode()
        ).hexdigest()
        return {
            "seed": self.seed,
            "winner": self.winner,
            "turn": self.turn,
            "actions": actions,
            "invalid_actions": self.invalid_actions,
            "finished": self.finished,
            "event_sha256": digest,
            "generation_profile": GENERATION_PROFILE,
        }

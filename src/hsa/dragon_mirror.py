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

from .config import DRAGON_DECKSTRING, RULESET
from .rules import (
    DECLARATIVE_METADATA_ALIASES,
    DECLARATIVE_METADATA_IDS,
    Hook,
    HolmesInspect,
    RuleContext,
    STANDARD_DECLARATIVE_IDS,
    TargetKind,
    imbue_hero_power_id,
    build_rule_registry,
)


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
    "CATA_161", "CATA_301", "CATA_477", "CATA_527", "CATA_569", "CATA_724", "CORE_AT_052", "CORE_EX1_250", "CORE_OG_044", "Core_LOE_115", "CORE_ONY_018", "CORE_TSC_650", "CS3_007", "EDR_233", "EDR_257", "EDR_263", "EDR_454", "EDR_490", "EDR_520", "EDR_525", "EDR_570", "EDR_843", "EDR_872", "END_010", "END_028", "JAIL_380", "JAIL_462", "JAIL_877", "JAIL_887", "JAIL_987", "MEND_044", "TIME_044", "TIME_601", "TLC_227", "TLC_449",
    "TIME_436", "TIME_446", "TIME_810",
}

GENERATED_DRAGON_IDS = {
    "CATA_111",  # Darkscale Broodmother
    "CATA_160",  # Scorching Ravager
    "CATA_476",  # Bronze Keeper
    "CATA_497",  # Ultraxion
    "CATA_898",  # Scaled Lancer
    "CATA_999",  # Earthen Drake
    "CATA_723",  # Drakeadon Mongrel
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
    "CORE_CS2_033",  # Water Elemental
    "hexfrog",  # Hex transformation token
    "EX1_160t",  # Power of the Wild Panther token
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
    # Standard Dormant cards.
    "CATA_481", "EDR_469", "EDR_841", "EDR_979", "TIME_022", "TIME_058",
    "TIME_442", "TLC_253",
    # Standard Quickdraw minions.
    # Standard Elusive cards with explicit rules below.
    "CATA_133", "CATA_185", "CATA_206", "EDR_462", "RLK_048", "TLC_246",
    "TLC_100",  # Elise the Navigator
    "MEND_046",  # Bashana Runetotem
    "JAIL_860",  # Chef Neth'rek
    "JAIL_719",  # Irida Sinseeker
    "JAIL_446",  # Blood Doctor Thal'ena
    "JAIL_800",  # Mug'Zee
    "JAIL_504",  # Aya, Lotus Kingpin
    "JAIL_397",  # Commander Beatrix
    "JAIL_882",  # R4T-C4TCH3R
    "JAIL_831",  # King of the Underbelly
    "JAIL_851",  # Inspector Murloc Holmes
    "TLC_226",  # Conjured Bookkeeper
    "TLC_251",  # Primalfin Challenger
    "TLC_366",  # Pterrorwing Ravager
    "TLC_428",  # Hot Spring Glider
    "TLC_429",  # Steamfin Thief
    "TLC_454",  # Scalehide Kodo
    "TLC_903",  # Silithid Queen
    "JAIL_906",  # Moragg
    "JAIL_998",  # Defias Smuggler
    "JAIL_912",  # Soothsayer
    "JAIL_453",  # Jailbird
    "JAIL_909",  # Defias Wannabe
    "JAIL_321",  # Tricksy Improviser
    "JAIL_407",  # Vanessa the Ringleader
    "JAIL_718",  # Black Market Auctioneer
    "JAIL_721",  # Tras'tath, Soul Parasite
    "JAIL_395",  # Sewer Swimmer
    "JAIL_444",  # Sawbones
    "CATA_300",  # The Black Blood
    "CATA_432",  # Chromatus
    "CATA_726",  # Cho'gall, Mastermind
    "CATA_153",  # Al'Akir, Lord of Storms
    "CATA_154",  # Sinestra
    "CATA_488",  # Vulcanos
    "CATA_525",  # Armored Bloodletter
    "CATA_565",  # Skywall Sentinel
    "CATA_780",  # Obsessive Technician
    "CORE_EX1_284",  # Azure Drake (legacy/Core-hidden compatibility)
    "CATA_155",  # Arisen Onyxia
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
    "JAIL_035",  # Vigilant Sentry
    "JAIL_328",  # Scarlet Bruiser
    "JAIL_386",  # Scramble for Gear
    "JAIL_379",  # Spire Security
    "CORE_AT_011",  # Holy Champion
    "CORE_CFM_606",  # Mana Geode
    "CORE_CS3_014",  # Crimson Clergy
    "CORE_BT_480",  # Crimson Sigil Runner
    "CAP_004",  # Disguised Operator
    "JAIL_442",  # Disguised Doctor
    "JAIL_452",  # Disguised Detective
    "JAIL_461",  # Disguised Executioner
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
    "TIME_850",  # Lo'Gosh, Blood Fighter
    "TIME_209",  # Muradin, High King
    "TIME_875",  # Garona Halforcen
    "TIME_009",  # Gelbin of Tomorrow
    "END_037",  # Endtime Murozond
    "TIME_619",  # Talanji of the Graves
    "TIME_619t",  # Bwonsamdi token
    "TIME_020",  # Broxigar
    "TIME_020t1", "TIME_020t2", "TIME_020t3", "TIME_020t4", "TIME_020t5",
    "TIME_020t2t", "TIME_020t3t", "TIME_020t4t", "TIME_020t5t",
    "TIME_005",  # Timethief Rafaam
    "TIME_603",  # Ticking Timebomb
    "TIME_609t1", "TIME_609t2",  # Sylvanas sister tokens
    "TLC_228",  # Bralma Searstone
    "TLC_241",  # Ido of the Threshfleet
    "TLC_110",  # City Chief Esho
    "CS3_024",  # Taelan Fordring
    "CS3_025",  # Overlord Runthak
    "FIR_958",  # Tindral Sageswift
    "JAIL_509",  # Godfrey the Betrayer
    "TLC_987",  # Questing Assistant
    "CORE_RLK_083",  # Deathchiller
    "CORE_RLK_116",  # Necrotic Mortician
    "RLK_223",  # Thassarian
    "TIME_613",  # Cryofrozen Champion
    "TIME_617",  # Chronochiller
    "CORE_RLK_706",  # Alexandros Mograine
    "JAIL_443",  # The Living Plague
    "TLC_480",  # Krog, Crater King
    "CORE_EX1_005",  # Big Game Hunter
    "CORE_REV_023",  # Demolition Renovator
    "TLC_255",  # Crystal Tender
    "TIME_021",  # Doomsday Prepper
    "CORE_EDR_003",  # Falric
    "CORE_RLK_066",  # Hematurge
    "CORE_RLK_505",  # Marrow Manipulator
    "CORE_RLK_506",  # Boneguard Commander
    "DINO_416",  # Hollow Direhorn
    "EDR_815",  # Corpse Flower
    "FIR_951",  # Volcoross
    "RLK_061",  # Battlefield Necromancer
    "RLK_503",  # Body Bagger
    "CORE_RLK_745",  # Malignant Horror
    "TIME_618",  # Husk, Eternal Reaper
}

# Closed Rewind cards whose random outcomes can be played from hand without
# opening another generated-card pool.
ADDITIONAL_PLAYABLE_CARD_IDS = {
    "CORE_EX1_323",  # Lord Jaraxxus Hero card
    "TIME_000",  # Semi-Stable Portal
    "TIME_001",  # Chrono Daggers
    "TIME_002",  # Aeon Wizard
    "TIME_008",  # Bygone Doomspeaker
    "TIME_014",  # Instant Multiverse
    "TIME_018",  # Mend the Timeline
    "TIME_035",  # Time Machine
    "TIME_602",  # Wormhole
    "TIME_038",  # Mister Clocksworth
    "TOT_056",  # Wildlands Adventurer
    "TIME_033",  # Druid of Regrowth
    "END_036",  # Morchie
    "TOT_332",  # Murozond
    "TIME_EVENT_999",  # Sands of Time
    "TIME_433",  # Cease to Exist
    "TIME_441",  # Aeon Rend
    "TIME_610",  # Shadows of Yesterday
    "CATA_580",  # Cataclysmic War Axe
}

# Rulebreaker minions explicitly ignore the normal friendly-board placement
# restriction.  Keep this as data so legal-action generation and resolution
# use the same side-placement contract.
PLAYABLE_ON_EITHER_SIDE_IDS = frozenset({
    "CAP_004",   # Disguised Operator
    "JAIL_442",  # Disguised Doctor
    "JAIL_452",  # Disguised Detective
    "JAIL_455",  # Disguised Watchman
    "JAIL_461",  # Disguised Executioner
})

# Individually closed spells used by generated-spell mechanics. Keep these
# separate from the Rewind tranche: the generation audit relies on the latter
# being exactly the Rewind cards, while this set will grow by school/pool.
ADDITIONAL_PLAYABLE_SPELL_IDS = {
    "EDR_820", "JAIL_997",
    # Standard Quickdraw spells.
    "RLK_048",  # Anti-Magic Shell
    "CAP_001",  # Silent Strike
    "CORE_BAR_541",  # Runed Orb
    "TLC_435",  # Crypt Map
    "TLC_440",  # Cryosleep
    "TLC_442",  # Submerged Map
    "TLC_447",  # Caustic Fumes
    "TLC_464",  # Mountain Map
    "TLC_519",  # Ambush Predators
    "TLC_815",  # Gravedawn Voidbulb
    "TLC_816",  # Gravedawn Sunbloom
    "TLC_824",  # Odd Map
    "TLC_900",  # Hive Map
    "JAIL_319",  # The Skeleton Key
    "CAP_407",  # Wanted Poster
    "JAIL_735",  # Code Violet
    "CORE_CS2_013", "CORE_EX1_164", "CORE_CS2_075",
    "CORE_CS2_077", "CORE_CS2_089",
    "CATA_135",  # Mossbinding
    "CATA_303",  # Purifying Breath
    "CORE_CS2_029",  # Fireball
    "CORE_CS2_032",  # Flamestrike
    "CORE_SW_108",  # First Flame
    "FIR_909",  # Bursting Shot
    "FIR_906",  # Overheat
    "FIR_910",  # Scorching Winds
    "FIR_923",  # Flames of the Firelord
    "FIR_954",  # Conflagrate
    "JAIL_307",  # Crowd Control
    "SW_108t",  # Second Flame
    "TLC_227",  # Lava Flow
    "TLC_221",  # Sizzling Swarm
    "DINO_406",  # Fire Breath
    "FIR_941",  # Searing Reflection
    "TLC_222",  # Flight of the Firehawk
    "TLC_632",  # Story of Sulfuras
    "CATA_581",  # Decimation
    "CATA_533",  # Flash Flood
    "DINO_136",  # Horn of Feasting
    "END_005",  # Bygone Echoes
    "JAIL_892",  # Cosmic Manifestations
    "CORE_RLK_118",  # Tomb Guardians
    "CORE_RLK_712",  # Blood Tap
    "CORE_WW_374",  # Corpse Farm
    "RLK_060",  # Army of the Dead
    "RLK_707",  # Grave Strength
    "JAIL_451",  # Blood Clone
    "TLC_434",  # Paleomancy
    "EDR_813",  # Morbid Swarm
    "CATA_465",  # Chow Down
    "CORE_SW_429",  # Best in Shell
    "END_025",  # Eternal Firebolt
    "JAIL_801",  # Molten Gold
    "CORE_EX1_610",  # Explosive Trap
    "END_024",  # Flames of Infinity
    "CORE_LOOT_101",  # Explosive Runes
    "CATA_156",  # Experimental Animation
    "CATA_530",  # Fel Infusion
    "CATA_561",  # Ritual of Power
    "END_017",  # Battle at the End Time
    "TIME_612",  # Blood Draw
    "TIME_611",  # Timestop
    "JAIL_445",  # Bone Flurry
    "JAIL_454",  # Emergency Surgery
    "TIME_615",  # Forgotten Millennium
}

# Rotated Quickdraw cards retained for an optional Wild/historical ruleset.
# They are deliberately not included in SUPPORTED_IDS for the current pinned
# Standard environment.
WILD_QUICKDRAW_IDS = frozenset({
    "WW_003", "WW_325", "WW_348", "WW_358", "WW_360", "WW_363",
    "WW_365", "WW_377", "WW_379", "WW_384", "WW_403", "WW_411",
    "WW_417", "WW_434", "WW_436", "WW_808", "WW_823", "WW_900",
    "DED_506", "SW_037", "TTN_841", "TTN_844", "TOY_519", "YOG_402",
})

SPECIAL_TOKEN_IDS = {
    "EX1_131t",  # Defias Bandit
    "EX1_383t",  # Ashbringer
    "TRL_348t",  # Lynx
    "MEND_046t",  # Bashana Runetotem's carved-spell Treant
    "CATA_300t1", "CATA_300t2", "CATA_300t3",
    "CATA_432t1", "CATA_432t2", "CATA_432t3", "CATA_432t4",
    "CATA_561t",  # Breezling
    "CATA_153t", "CATA_153t1",  # Charged Hand of Al'Akir
    "CATA_154t", "CATA_154t1",  # Sinestra's Wing
    "CATA_525t", "CATA_565t", "CATA_725t", "CATA_726t", "CATA_726t1",
    "CATA_780t",
    "CATA_488t", "CATA_488t2",
    "BOT_102t",  # Spark
    "CAP_107t",  # Cannoneer
    "CATA_155t",  # Onyxia's Wing
    "CATA_155t1",  # Onyxia's Wing
    "CATA_615t",  # Genn, Worgen King
    "CATA_151t",  # Azshara's Tentacle
    "CATA_139t",  # Wickerfang's Leg
    "CATA_139t2",  # Wickerfang's Leg
    "CATA_139t3",  # Wickerfang's Leg
    "CATA_139t4",  # Wickerfang's Leg
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

# Metadata-only Standard cards with no printed text or hidden triggers. They
# use the engine's ordinary minion lifecycle (summon, attack, damage, death)
# and are intentionally kept separate from generated pools until a focused
# regression test promotes them there.
STANDARD_VANILLA_IDS = {
    # Keyword-only A0 tranche (no Battlecry/Deathrattle/random text).
    "RLK_067", "CORE_BT_921", "EDR_272", "CORE_CS2_179",
    # Standard keyword-only Elusive minions.  Elusive itself is enforced by
    # target legality below; these IDs make the cards available to normal
    # deck construction and generated pools.
    "CATA_558", "CORE_DRG_079", "CORE_NEW1_023", "EDR_598",
    "END_033", "END_030", "MEND_506", "TIME_013", "TIME_059",
    "TIME_605",
    "CORE_EX1_028", "CS3_038", "EDR_598", "FIR_901t", "JAIL_454t",
    "RLK_077t", "RLK_705t", "TLC_443t", "CATA_528t", "DINO_136t",
    "TLC_903t", "CATA_132t", "EDR_209t5", "CATA_551t", "EDR_850pe",
    "TIME_006t1", "EDR_840t", "EDR_840t1", "EDR_840t2", "EDR_523t",
    "RLK_Prologue_RLK_705t", "EDR_100t6e", "CATA_476t", "EDR_100t6",
    "JAIL_887t3", "Story_09_StormwatcherPuzzle", "TLC_101t", "TLC_429t",
    "TLC_468t1", "TLC_468t2", "TIME_700t", "CAP_802t", "EDR_523t",
    "TLC_513t2", "TLC_519t", "CATA_561t", "EDR_233t2", "TLC_446t2",
    "TLC_446t3", "TLC_446t4",
    "CORE_EDR_002e", "CATA_151e", "TLC_631e", "TIME_861e2",
    "CATA_530e", "CATA_553e2", "JAIL_500e", "JAIL_516e",
    "MEND_044e3", "JAIL_877t", "NEW_4183_Copy", "CAP_805e", "TLC_446e",
    "CAP_105t", "TIME_870t",
    "CATA_134t3", "CATA_135t", "CATA_190t14", "CATA_210t",
    "CATA_452t", "CATA_465t", "CATA_470t1", "CATA_478t", "CATA_479t3",
    "Core_CS2_200",  # Boulderfist Ogre
    "CORE_EX1_506a", "CORE_GIL_191t", "CS3_002t", "Core_CS2_200",
    "DINO_130t", "EDR_457t", "EDR_813at", "EDR_846t5",
    "EDR_847pt2", "EDR_847pt3", "EDR_847pt4", "EDR_851t", "END_009t",
    "JAIL_504tt01", "JAIL_504tt04", "JAIL_504tt07", "JAIL_504tt20",
    "JAIL_511t", "JAIL_EVENT_100t", "Story_09_Imp", "TIME_005t9t",
    "TIME_053", "TIME_434t", "TIME_443t", "TIME_443t2", "TIME_610t2",
    "TIME_873t", "TLC_230t", "TLC_237t", "TLC_240t", "TLC_240t2",
    "TLC_240t3", "TLC_248", "TLC_831t",
    "TIME_850t", "TIME_850t1",
    "TIME_209t",
    # Core vanilla minions used as stable fixtures and valid neutral pool
    # members for the declarative draw rules.
    "CORE_CS2_231", "CORE_CS2_120", "CORE_GVG_044", "CORE_CS2_182",
    "TTN_950t", "RLK_063t", "BAR_035t",
    "TTN_081t", "TTN_710", "TTN_727t", "TTN_801t1", "TTN_812t",
    "TTN_950t2", "TTN_960t5", "TTN_960t6", "YOG_506t",
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
    | ADDITIONAL_PLAYABLE_SPELL_IDS
    | SPECIAL_TOKEN_IDS | BLOCKED_GENERATOR_IDS | STANDARD_VANILLA_IDS
    | DECLARATIVE_METADATA_IDS
    | DECLARATIVE_METADATA_ALIASES.keys()
)
EXECUTABLE_CARD_IDS = SUPPORTED_IDS | STANDARD_DECLARATIVE_IDS

# Current Standard collectible cards carrying the Herald keyword.  Keeping
# this manifest separate from generated Soldier entities lets the generation
# audit detect a newly added Herald card that is missing from the executable
# surface.
HERALD_COLLECTIBLE_IDS = frozenset({
    "CATA_156", "CATA_158", "CATA_160", "CATA_190h", "CATA_492",
    "CATA_497", "CATA_525", "CATA_530", "CATA_561", "CATA_565",
    "CATA_580", "CATA_722", "CATA_725", "CATA_780", "CATA_785",
})

# The fixed Dragon Warrior deck starts with no Herald-related or Fabled card.
# Constructed generation therefore excludes these cards even though they are
# collectible class/tribe matches in the raw Standard catalog.
DISCOVER_BANNED_IDS = {
    "CATA_150", "CATA_160", "CATA_497", "CATA_722", "TIME_850",
}

# Fabled is a standalone keyword in Taverns of Time.  It is not equivalent
# to Legendary rarity: some Fabled cards can have any rarity, and Legendary
# cards without the keyword must never enter this pool.
FABLED_MINION_IDS = frozenset({
    "TIME_005", "TIME_009", "TIME_020", "TIME_209", "TIME_211",
    "TIME_609", "TIME_619", "TIME_850", "TIME_852", "TIME_875", "TIME_890",
})

# Current Lost City class quest cards.  They live in a dedicated state zone
# once played; treating them as ordinary spells would silently consume them
# without retaining their progress.
LOST_CITY_QUEST_IDS = frozenset({
    "END_017",
    "TLC_229", "TLC_239", "TLC_426", "TLC_433", "TLC_446",
    "TLC_460", "TLC_513", "TLC_602", "TLC_631", "TLC_817", "TLC_830",
})
LOST_CITY_QUEST_REWARDS = {
    "END_017": "END_017t",
    "TLC_229": "TLC_229t14", "TLC_239": "TLC_239t", "TLC_446": "TLC_446t",
    "TLC_433": "TLC_433t", "TLC_460": "TLC_460t", "TLC_513": "TLC_513t",
    "TLC_602": "TLC_602t", "TLC_631": "TLC_631t",
    "TLC_830": "TLC_830t",
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
    # Death Knight rune requirements are part of the printed card metadata;
    # Map cards use them when building the Frost Rune Discover pool.
    rune_cost: dict[str, int] = field(default_factory=dict)
    rarity: str = ""
    collectible: bool = False
    armor: int = 0

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
    playable_after_turn: int = -1
    locked_until_card_played: bool = False
    summoned_when_drawn: bool = False
    immune: bool = False
    immune_while_attacking: bool = False
    attacking_now: bool = False
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
    casts_when_drawn_armor: int = 0
    void_soul_cost: int = 0
    omen_damage: int = 1
    summon_moragg_on_death: bool = False
    frozen_turn: int = -1
    cant_attack: bool = False
    mirrex_tracker: bool = False
    spell_damage_bonus: int = 0
    embedded_spell_id: str | None = None
    prepared_turn: int = -1
    # Prepare is a one-time state on the card, not a per-turn activation.
    prepared: bool = False
    prepare_granted: bool = False
    shatter_origin: str | None = None
    shatter_half: str | None = None
    shatter_combined: bool = False
    outcast_active: bool = False
    dynamic_spell_damage: int = 0
    spells_cast_while_held: int = 0
    illusion_fake: bool = False
    cant_attack_heroes_turn: int = -1
    dies_at_end_of_turn: bool = False
    combo_active: bool = False
    mana_spent_while_held: int = 0
    minion_played_while_held: bool = False
    higher_cost_card_played_while_held: bool = False
    opponent_card_copy_played_while_held: bool = False
    held_turns: int = 0
    copied_from_opponent: bool = False
    deathrattle_copy_card_id: str | None = None
    deathrattle_summon_card_id: str | None = None
    deathrattle_damage_all_enemies: int = 0
    killed_by_entity: int | None = None
    devoured_cards: list[CardInstance] = field(default_factory=list)
    imprisoned_entity_id: int | None = None
    high_kings_hammer_claimed: bool = False
    temporary: bool = False
    spell_casts_twice: bool = False
    return_control_to: int | None = None
    return_control_at_end_of_turn: int | None = None
    cant_attack_turn: int = -1
    temporary_attack_modifiers: list[tuple[int, int]] = field(default_factory=list)
    avatar_form_pending: bool = False
    temporary_health_modifiers: list[tuple[int, int]] = field(default_factory=list)
    temporary_immune_expiry_turn: int = -1
    drawn_turn: int = -1
    bonus_effect_options: tuple[str, str] | None = None
    bonus_effect_active: str | None = None
    destroy_at_turn_start: int = -1
    costs_health_expiry_turn: int = -1
    # Colossal appendages retain their parent entity rather than merely their
    # source card id: several copies of the same Colossal can coexist.  These
    # fields are used by Wickerfang, whose text copies permanent stat gains
    # from each of its Legs onto the body.
    colossal_parent_entity: int | None = None
    wickerfang_inherited_attack: int = 0
    wickerfang_inherited_health: int = 0
    # Conditional "during your opponent's turn" attack is represented as a
    # state flag rather than mutating attack_delta. This keeps printed stats
    # intact, makes silence immediately remove the effective bonus, and is
    # naturally branch-safe for MCTS cloning.
    opponent_turn_attack_bonus_active: bool = False

    @property
    def card_id(self) -> str:
        return self.definition.card_id

    @property
    def attack(self) -> int:
        enraged = 0
        if self.damage > 0 and not self.silenced:
            if self.card_id == "CORE_EX1_414":
                enraged = 6
            elif self.card_id in {"CORE_OG_218", "TLC_101"}:
                enraged = 3
        threshold = 0 if self.silenced else self.deck_threshold_attack
        # External auras continue to affect a silenced recipient. Self-owned
        # conditional bonuses are zeroed by _refresh_continuous when the source
        # minion itself is silenced.
        continuous = (
            self.pirate_aura_stats + self.aura_attack_bonus
            + self.weapon_attack_bonus
        )
        conditional = (
            {"TLC_605": 6, "CORE_UNG_928": 2}.get(self.card_id, 0)
            if self.opponent_turn_attack_bonus_active and not self.silenced
            else 0
        )
        return max(
            0,
            self.definition.attack + self.attack_delta + enraged + threshold
            + conditional
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

    def __deepcopy__(self, memo: dict[int, Any]) -> "CardInstance":
        """Copy mutable instance state without recursively walking CardDef.

        Card definitions are frozen and shared across all search branches.  A
        generic dataclass deepcopy nevertheless spends substantial time
        reconstructing the instance dictionary for every card in every MCTS
        branch.  Most instance fields are scalars; only these three lists need
        their own containers in a child state.
        """
        result = copy.copy(self)
        memo[id(self)] = result
        result.gifts = list(self.gifts)
        result.temporary_attack_modifiers = list(self.temporary_attack_modifiers)
        result.temporary_health_modifiers = list(self.temporary_health_modifiers)
        return result

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

    def __deepcopy__(self, memo: dict[int, Any]) -> "Weapon":
        result = copy.copy(self)
        memo[id(self)] = result
        # CardDef is immutable, but the kill list itself is branch-local.
        result.killed_minions = list(self.killed_minions)
        return result


@dataclass
class Location:
    entity_id: int
    card_id: str
    durability: int
    # A location enters play and becomes dormant for one full turn.
    cooldown: int = 2
    next_refresh: int = 1
    # Custom locations (for example Elise's crafted location) retain the
    # selected effect ids and tier as engine state.  Ordinary locations leave
    # these fields empty, so their existing behavior is unchanged.
    custom_effects: tuple[str, ...] = ()
    custom_tier: int = 0

    def __deepcopy__(self, memo: dict[int, Any]) -> "Location":
        result = copy.copy(self)
        memo[id(self)] = result
        return result


@dataclass
class Player:
    index: int
    card_class: str = "WARRIOR"
    # Death Knight deck-building rune slots.  Non-DK players keep all slots
    # at zero; the mapping is copied with the game state for search branches.
    rune_counts: dict[str, int] = field(
        default_factory=lambda: {"blood": 0, "frost": 0, "unholy": 0}
    )
    deck: list[CardInstance] = field(default_factory=list)
    # Cards removed by Irida Sinseeker.  They are not a second deck: they can
    # only return through Irida's start-of-turn effect.
    void_cards: list[CardInstance] = field(default_factory=list)
    hand: list[CardInstance] = field(default_factory=list)
    board: list[CardInstance] = field(default_factory=list)
    dead_minions: list[CardInstance] = field(default_factory=list)
    locations: list[Location] = field(default_factory=list)
    secrets: list[CardInstance] = field(default_factory=list)
    health: int = 30
    max_health: int = 30
    armor: int = 0
    mana: int = 0
    max_mana: int = 0
    fatigue: int = 0
    weapon: Weapon | None = None
    hero_attack_bonus: int = 0
    next_spell_damage_bonus: int = 0
    # Set by Fel Infusion/Herald and valid only for the current turn.
    hero_lifesteal_turn: int = -1
    hero_attacks_this_turn: int = 0
    hero_attacks_this_game: int = 0
    hero_poisonous_until_turn: int = -1
    avatar_form_hero_pending: bool = False
    void_soul_level: int = 1
    # Shared Leyline progression.  Crystallized Leyline reads this value;
    # upgrade cards will increment it rather than carrying local constants.
    leyline_level: int = 5
    leyline_upgrade: int = 0
    leyline_extra_triggers: int = 0
    hero_power_used: bool = False
    hero_power_cost_override: int | None = None
    # One-shot surcharge used by Blowtorch Saboteur.  Its expiry is recorded
    # in the global turn counter so it cannot leak past the opponent's next
    # turn when that player elects not to use their Hero Power.
    hero_power_cost_surcharge: int = 0
    hero_power_cost_surcharge_expiry_turn: int = -1
    # Cult Neophyte applies only through the target player's next turn.
    spell_cost_surcharge: int = 0
    spell_cost_surcharge_turn: int = -1
    hero_power_armor: int = 2
    hero_power_id: str | None = None
    hero_power_imbues: int = 0
    undead_died_after_last_turn: bool = False
    mograine_active: bool = False
    friendly_minions_died_this_turn: int = 0
    friendly_minions_died_this_game: int = 0
    # Endtime Murozond skips the controller's next turn.  This is a turn-level
    # flag rather than a card-local effect so it survives state cloning and
    # resolves before start-of-turn draws/mana refresh.
    skip_next_turn: bool = False
    broxigar_return_used: bool = False
    broxigar_removed_from_game: bool = False
    imbued_hero_power_id: str | None = None
    imbue_passive_triggered_this_turn: bool = False
    hamuul_active: bool = False
    hamuul_spells_cast: int = 0
    fire_spell_played: bool = False
    played_races_this_turn: set[str] = field(default_factory=set)
    played_races_last_turn: set[str] = field(default_factory=set)
    played_races_this_game: set[str] = field(default_factory=set)
    minion_played_this_turn: bool = False
    minion_played_last_turn: bool = False
    damaged_characters_this_turn: set[str] = field(default_factory=set)
    hero_health_changed_this_turn: bool = False
    sigil_of_cinder_turn: int = -1
    sigil_of_cinder_damage: int = 0
    herald_count: int = 0
    geddon_draw: bool = False
    ysondre_deaths: int = 0
    hero_board_attack_bonus: int = 0
    frozen_turn: int = -1
    cards_played_this_turn: int = 0
    cards_drawn_this_turn: int = 0
    spells_cast_this_turn: int = 0
    generated_cards_played: int = 0
    played_card_counts: dict[str, int] = field(default_factory=dict)
    pending_phoenixes: int = 0
    corpses: int = 0
    pending_magmaw_bodies: int = 0
    magmaw_entity: int | None = None
    overloaded_mana_this_game: int = 0
    overload_next_turn: int = 0
    next_spell_cost_reduction: int = 0
    next_demon_cost_reduction: int = 0
    # Foxy Fraud applies only during the current turn and only once a later
    # card actually satisfies Combo.
    next_combo_cost_reduction: int = 0
    locked_mana: int = 0
    next_demon_free: bool = False
    next_beast_cost_reduction: int = 0
    next_murloc_cost_reduction: int = 0
    next_minion_cost_reduction: int = 0
    # Hatching Ceremony is resolved at the end of the controller's following
    # turn; ``turns_taken`` gives that delayed window a branch-safe identity.
    hatching_ceremony_trigger_turn: int = -1
    ruby_sanctum_turn: int = -1
    kindred_triggers_twice: int = 0
    map_followup_options: list[str] = field(default_factory=list)
    map_followup_entity: int | None = None
    map_followup_turn: int = -1
    hero_divine_shield: bool = False
    hero_divine_shield_hits: int = 0
    hero_divine_shield_toreth: bool = False
    # Temporary immunity granted by Outcast cards such as Doomsday Prepper.
    # The expiry is the owner's next turn, not the opponent's intervening turn.
    hero_immune: bool = False
    hero_immune_expiry_turn: int = -1
    corpse_rebirth_pending: bool = False
    turns_taken: int = 0
    dragons_played_this_turn: int = 0
    start_turn_temporary_mana_charges: int = 0
    # Chef Neth'rek's Start of Game condition.  A value of -1 means the
    # restriction was not satisfied; otherwise it counts down the owner's
    # turns and grants ten mana when it reaches zero.
    chef_nethrek_turns_remaining: int = -1
    irida_active: bool = False
    coin_replacement_id: str | None = None
    holmes_target_card_id: str | None = None
    holmes_watch_turn: int = -1
    mug_magic_active: bool = False
    mug_magic_used_this_turn: bool = False
    zee_might_active: bool = False
    zee_might_minions_played: int = 0
    minion_cost_increase_turn: int = -1
    minion_cost_increase_amount: int = 0
    recover_overdrawn_cards: bool = False
    overdrawn_cards: list[CardInstance] = field(default_factory=list)
    pending_end_turn_returns: list[CardInstance] = field(default_factory=list)
    zuramat_discarded_card: CardInstance | None = None
    active_quests: dict[str, dict[str, Any]] = field(default_factory=dict)
    completed_quests: set[str] = field(default_factory=set)
    murloc_quest_buff: bool = False
    gorishi_double_damage: bool = False
    ninja_shuffle_active: bool = False
    ashalon_adaptations: list[str] = field(default_factory=list)
    underfel_rift_used_turn: int = -1
    origin_stone_triggering: bool = False

    def __deepcopy__(self, memo: dict[int, Any]) -> "Player":
        """Fast branch copy for the mutable player state used by MCTS."""
        result = copy.copy(self)
        memo[id(self)] = result
        for name in (
            "deck", "hand", "board", "dead_minions", "locations", "secrets",
            "overdrawn_cards", "pending_end_turn_returns",
        ):
            zone = getattr(self, name)
            # ``clone(skip_hidden_zones_of=...)`` supplies branch-local empty
            # zones through ``memo``. This is used only by public-belief
            # determinizations, which replace the opponent's private hand and
            # deck immediately after cloning. Avoiding a copy of cards that
            # will be discarded materially reduces ISMCTS branch cost.
            copied_zone = memo.get(id(zone))
            if copied_zone is None:
                copied_zone = copy.deepcopy(zone, memo)
            setattr(result, name, copied_zone)
        result.weapon = copy.deepcopy(self.weapon, memo)
        result.played_races_this_turn = set(self.played_races_this_turn)
        result.played_races_last_turn = set(self.played_races_last_turn)
        result.played_races_this_game = set(self.played_races_this_game)
        result.damaged_characters_this_turn = set(self.damaged_characters_this_turn)
        result.played_card_counts = dict(self.played_card_counts)
        result.map_followup_options = list(self.map_followup_options)
        result.ashalon_adaptations = list(self.ashalon_adaptations)
        result.active_quests = copy.deepcopy(self.active_quests, memo)
        result.completed_quests = set(self.completed_quests)
        result.zuramat_discarded_card = copy.deepcopy(self.zuramat_discarded_card, memo)
        return result

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


def _discard_search_event(*_args: Any, **_payload: Any) -> None:
    """No-op event sink installed on event-free search branches."""


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
        beatrix_choices: tuple[str | None, str | None] | None = None,
        rune_configs: tuple[dict[str, int] | None, dict[str, int] | None] | None = None,
    ):
        self.rng = random.Random(seed)
        self.seed = seed
        self.turn = 0
        self.current = 0
        self.first_player = 0
        self.next_entity_id = 1
        self.invalid_actions = 0
        self.events: list[dict[str, Any]] = []
        # Production games retain a full event trace. Search branches can turn
        # this off because events are audit data, not rule-engine state.
        self.record_events = True
        self.finished = False
        self.winner: int | None = None
        self.pending_choice: dict[str, Any] | None = None
        self.minions_died_this_turn = 0
        self.deck_counts = deck_counts or (DRAGON_DECK_COUNTS, DRAGON_DECK_COUNTS)
        self.beatrix_choices = beatrix_choices or (None, None)
        requested_ids = set(self.deck_counts[0]) | set(self.deck_counts[1])
        unsupported = requested_ids - EXECUTABLE_CARD_IDS
        if unsupported:
            raise UnsupportedGeneratedCard(
                "deck contains cards without executable rules: "
                + ", ".join(sorted(unsupported))
            )
        self.card_defs = self._load_defs(Path(cards_path))
        self.rune_configs = self._resolve_rune_configs(rune_configs, player_classes)
        self.executable_card_ids = EXECUTABLE_CARD_IDS
        self.rule_registry = build_rule_registry()
        missing = (
            EXECUTABLE_CARD_IDS | BASIC_AUXILIARY_IDS
        ) - self.card_defs.keys()
        if missing:
            raise ValueError(f"missing card metadata: {sorted(missing)}")
        self.players = [
            Player(0, card_class=player_classes[0], rune_counts=dict(self.rune_configs[0])),
            Player(1, card_class=player_classes[1], rune_counts=dict(self.rune_configs[1])),
        ]
        for player in self.players:
            player.deck = self._new_deck(player.index)
        self._apply_pre_game_deck_rules()
        for player in self.players:
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
                    rune_cost=dict(card.get("runeCost", {}) or {}),
                    rarity=card.get("rarity", "") or "",
                    collectible=bool(card.get("collectible", False)),
                    armor=int(card.get("armor", 0)),
                )
        return result

    def _resolve_rune_configs(
        self,
        requested: tuple[dict[str, int] | None, dict[str, int] | None] | None,
        player_classes: tuple[str, str],
    ) -> tuple[dict[str, int], dict[str, int]]:
        """Resolve and validate Death Knight rune slots at deck construction.

        A DK has three rune slots total.  If no explicit configuration is
        supplied, infer the minimum slots needed by the supplied deck; this
        keeps existing simulations compatible while rejecting decks whose
        cards cannot share one legal rune configuration.  Explicit configs are
        useful for mulligan/search experiments and are validated strictly.
        """
        raw = requested or (None, None)
        if len(raw) != 2:
            raise ValueError("rune_configs must contain one config per player")
        colors = ("blood", "frost", "unholy")
        resolved: list[dict[str, int]] = []
        for index, card_class in enumerate(player_classes):
            supplied = raw[index]
            if supplied is None:
                config = {color: 0 for color in colors}
                if card_class == "DEATHKNIGHT":
                    for card_id in self.deck_counts[index]:
                        definition = self.card_defs.get(card_id)
                        if definition is None:
                            continue
                        for color in colors:
                            config[color] = max(
                                config[color],
                                int(definition.rune_cost.get(color, 0)),
                            )
            else:
                unknown = set(supplied) - set(colors)
                if unknown:
                    raise ValueError(f"unknown rune colors: {sorted(unknown)}")
                config = {color: int(supplied.get(color, 0)) for color in colors}
            if any(value < 0 or value > 3 for value in config.values()):
                raise ValueError("each rune color must be between 0 and 3")
            if sum(config.values()) > 3:
                raise ValueError("a Death Knight can have at most three rune slots")
            if card_class != "DEATHKNIGHT" and any(config.values()):
                raise ValueError("only Death Knight decks may use rune slots")
            if card_class == "DEATHKNIGHT":
                for card_id in self.deck_counts[index]:
                    definition = self.card_defs.get(card_id)
                    if definition is None:
                        continue
                    for color in colors:
                        required = int(definition.rune_cost.get(color, 0))
                        if required > config[color]:
                            raise ValueError(
                                f"{card_id} requires {required} {color} rune(s), "
                                f"but player {index} has {config[color]}"
                            )
            resolved.append(config)
        return resolved[0], resolved[1]

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
        if result.card_id in {"EDR_469", "MEND_040", "EDR_979", "TLC_253"}:
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

    def _apply_pre_game_deck_rules(self) -> None:
        """Apply Start of Game rules before opening hands are dealt.

        This is deliberately separate from ``_start_of_game``: effects that
        modify deck composition or starting health must be complete before
        shuffling, the opening draw, and the mulligan.  In particular,
        Azalina's copied cards are real initial-deck cards rather than
        generated cards added after the game begins.
        """
        original_definitions = [
            [card.definition for card in player.deck] for player in self.players
        ]
        for player in self.players:
            if any(card.card_id == "JAIL_397" for card in player.deck):
                candidates = [
                    card for card in player.deck
                    if card.card_id != "JAIL_397"
                    and card.definition.card_type == "MINION"
                    and card.definition.cost == 2
                ]
                requested = self.beatrix_choices[player.index]
                requested_candidate = next(
                    (card for card in candidates if card.card_id == requested), None
                )
                if requested_candidate is not None or candidates:
                    chosen_id = (
                        requested_candidate.card_id
                        if requested_candidate is not None else candidates[0].card_id
                    )
                    for _ in range(10):
                        player.deck.append(
                            self._entity(chosen_id, started_in_deck=True,
                                         created_by="JAIL_397")
                        )
                    self._event(
                        "beatrix_deck_choice", player=player.index,
                        card="JAIL_397", chosen=chosen_id, copies=10,
                        choice_source="explicit" if requested_candidate is not None else "fallback",
                    )
            if not any(card.card_id == "JAIL_430" for card in player.deck):
                continue
            enemy_definitions = original_definitions[1 - player.index]
            own = self.rng.sample(player.deck, min(20, len(player.deck)))
            copied_definitions = self.rng.sample(
                enemy_definitions, min(20, len(enemy_definitions))
            )
            copies = [
                self._instance_from_definition(
                    definition, started_in_deck=True, created_by="JAIL_430"
                )
                for definition in copied_definitions
            ]
            for copied in copies:
                copied.copied_from_opponent = True
            # The normal game shuffle below mixes retained and copied cards.
            player.deck = own + copies
            player.max_health = 40
            player.health = 40
            self._event(
                "start_of_game_deck_rebuild", player=player.index,
                card="JAIL_430", own_cards=len(own), copied_cards=len(copies),
                total_cards=len(player.deck), starting_health=40,
            )

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
        aya_players = [
            player.index for player in self.players
            if any(card.card_id == "JAIL_504" for card in player.hand + player.deck)
        ]
        if len(aya_players) == 2:
            # Two Aya effects cancel the deterministic rule; use the game's
            # seeded RNG so cloned/search states remain reproducible.
            self.first_player = self.rng.choice([0, 1])
            self._event(
                "aya_first_player_randomized", candidates=[0, 1],
                first_player=self.first_player,
            )
        elif aya_players:
            self.first_player = 1 - aya_players[0]
        else:
            self.first_player = 0
        self.current = self.first_player
        self._give_coin(self.players[1 - self.first_player], source="MULLIGAN")
        self._start_of_game()
        self._start_turn(self.first_player)

    def _start_of_game(self) -> None:
        # Start-of-game happens after initial hands. Hogger duplicates every other
        # Legendary still represented by the deck list; here that is Warptooth.
        for player in self.players:
            # Broxigar's Fabled Start of Game text removes him until the Argus
            # portal chain completes. Keep the flag on Player so cloned search
            # states preserve the one-time return condition.
            for zone_name in ("hand", "deck"):
                zone = getattr(player, zone_name)
                removed = next((card for card in zone if card.card_id == "TIME_020"), None)
                if removed is not None:
                    zone.remove(removed)
                    player.broxigar_removed_from_game = True
                    self._event("broxigar_disappear", player=player.index, zone=zone_name, entity=removed.entity_id)
                    break
            # Hamuul Runetotem: if every spell that started in the deck is
            # Nature, Imbue once at game start and repeat after each three
            # spells cast.  This is tracked as state rather than a one-off
            # card branch so generated/copy spells do not reset the counter.
            hamuul = next(
                (c for c in player.hand + player.deck if c.card_id == "EDR_845"),
                None,
            )
            deck_spells = [
                c for c in player.deck
                if c.definition.card_type == "SPELL" and c.started_in_deck
            ]
            if hamuul is not None and all(
                getattr(c.definition, "spell_school", None) == "NATURE" for c in deck_spells
            ):
                player.hamuul_active = True
                player.hamuul_spells_cast = 0
                power_id = imbue_hero_power_id(player.card_class)
                if power_id in self.card_defs:
                    player.hero_power_id = power_id
                    player.imbued_hero_power_id = power_id
                    player.hero_power_imbues += 1
                    self._event(
                        "hero_power_imbued", player=player.index,
                        source="EDR_845", hero_power=power_id,
                        count=player.hero_power_imbues,
                    )
                self._event(
                    "hamuul_start_of_game", player=player.index,
                    active=True, spells=len(deck_spells),
                )
            if any(c.card_id == "JAIL_384" for c in player.hand + player.deck):
                player.deck.append(self._entity("JAIL_421"))
                self.rng.shuffle(player.deck)
                self._event("start_of_game", player=player.index, card="JAIL_384", duplicated="JAIL_421")
            # Chef Neth'rek: the deck-building restriction is evaluated from
            # the complete starting deck, including cards already moved to the
            # opening hand.  The bonus is granted after five of this player's
            # turns, not five global turns.
            if any(c.card_id == "JAIL_860" for c in player.hand + player.deck):
                starting_cards = [
                    c for c in player.hand + player.deck
                    if c.card_id != "JAIL_860"
                ]
                if starting_cards and all(c.definition.cost <= 3 for c in starting_cards):
                    player.chef_nethrek_turns_remaining = 5
                    self._event(
                        "start_of_game", player=player.index,
                        card="JAIL_860", effect="ten_mana_after_five_turns",
                    )
            if any(c.card_id == "JAIL_800" for c in player.hand + player.deck):
                starting_cards = [
                    c for c in player.hand + player.deck
                    if c.card_id != "JAIL_800"
                ]
                if not any(c.definition.card_type == "MINION" for c in starting_cards):
                    player.mug_magic_active = True
                if not any(c.definition.card_type == "SPELL" for c in starting_cards):
                    player.zee_might_active = True
                if player.mug_magic_active or player.zee_might_active:
                    self._event(
                        "start_of_game", player=player.index,
                        card="JAIL_800", mug=player.mug_magic_active,
                        zee=player.zee_might_active,
                    )
            if any(c.card_id == "JAIL_509" for c in player.hand + player.deck):
                player.recover_overdrawn_cards = True
                self._event("start_of_game", player=player.index, card="JAIL_509", effect="recover_overdrawn")

    def _event(self, kind: str, **payload: Any) -> None:
        self._observe_lost_city_quests(kind, payload)
        if not self.record_events:
            return
        self.events.append({"turn": self.turn, "kind": kind, **payload})

    def _observe_lost_city_quests(self, kind: str, payload: dict[str, Any]) -> None:
        """Advance the compact progress model for active Lost City quests."""
        owner = payload.get("player")
        if not isinstance(owner, int) or owner not in (0, 1):
            return
        player = self.players[owner]
        card_id = payload.get("card")
        for quest_id, state in list(player.active_quests.items()):
            if kind == "play" and card_id in self.card_defs:
                definition = self.card_defs[card_id]
                if quest_id == "TLC_229" and definition.card_type == "MINION":
                    types = set(definition.races) or ({definition.race} if definition.race else set())
                    state["flags"].update(types)
                    state["progress"] = len(state["flags"])
                elif quest_id == "TLC_830" and definition.card_type == "MINION" and "BEAST" in definition.races:
                    state["flags"].add(definition.attack)
                    state["progress"] = len(state["flags"] & {1, 3, 5, 7})
                elif quest_id == "TLC_817" and definition.card_type == "SPELL":
                    school = definition.spell_school.upper()
                    if school == "HOLY":
                        state["holy"] = state.get("holy", 0) + 1
                    elif school == "SHADOW":
                        state["shadow"] = state.get("shadow", 0) + 1
            if quest_id == "END_017":
                # Battle at the End Time is sequential: first fill the hand,
                # then empty it.  Checking after every event also covers
                # generated cards, draws, trades, and cards played from hand.
                if len(player.hand) >= 10:
                    state["filled"] = True
                elif state.get("filled") and len(player.hand) == 0:
                    self._complete_lost_city_quest(player, quest_id)
                    continue
            if quest_id == "TLC_460" and kind in {
                "discover_pick", "deck_card_discover_pick", "deck_discover_pick",
                "intertwined_fate_pick", "rewind_discover_pick",
            }:
                state["progress"] += 1
            elif quest_id == "TLC_513" and "shuffle" in kind:
                state["progress"] += 1
            elif quest_id == "TLC_433" and kind == "spend_corpses":
                state["progress"] += int(payload.get("amount", 0))
            elif quest_id == "TLC_602" and kind == "turn_end":
                state["progress"] += 1
            elif quest_id == "TLC_239" and kind == "turn_end":
                if len(player.board) + len(player.locations) >= 7:
                    state["progress"] += 1
            elif quest_id == "TLC_631" and kind in {"damage_minion", "damage_hero"}:
                if int(payload.get("amount", 0)) == 2:
                    state["progress"] += 1
            elif quest_id == "TLC_426" and kind == "summon":
                summoned = self.card_defs.get(card_id)
                if summoned is not None and "MURLOC" in summoned.races:
                    state["progress"] += 1
            elif quest_id == "TLC_446" and kind == "play" and not payload.get("started_in_deck", True):
                state["progress"] += 1
            thresholds = {
                "TLC_229": 6, "TLC_239": 3, "TLC_446": 6, "TLC_460": 8,
                "TLC_513": 5, "TLC_602": 10, "TLC_631": 12, "TLC_830": 4,
            }
            if quest_id in thresholds and state["progress"] >= thresholds[quest_id]:
                self._complete_lost_city_quest(player, quest_id)
            elif quest_id == "TLC_817" and state.get("holy", 0) >= 4 and state.get("shadow", 0) >= 4:
                self._complete_lost_city_quest(player, quest_id)
            elif quest_id == "TLC_426" and state["progress"] >= 6:
                self._complete_lost_city_quest(player, quest_id)

    def _complete_lost_city_quest(self, player: Player, quest_id: str) -> None:
        state = player.active_quests.pop(quest_id, None)
        if state is None:
            return
        if quest_id == "TLC_426":
            # Repeatable Quest: the progress starts over, while the reward
            # aura remains active for all later Murlocs.
            player.active_quests[quest_id] = {"progress": 0, "turns": 0, "flags": set()}
            player.murloc_quest_buff = True
            self._event("quest_completed", player=player.index, card=quest_id, repeatable=True)
            return
        player.completed_quests.add(quest_id)
        if quest_id == "TLC_817":
            for reward_id in ("TLC_817t3", "TLC_817t4"):
                if reward_id in self.card_defs and len(player.hand) < 10:
                    self._add_generated(player, self._entity(reward_id, created_by=quest_id))
            self._combine_soletos(player)
            self._event("quest_completed", player=player.index, card=quest_id,
                        reward=["TLC_817t3", "TLC_817t4"])
            return
        if quest_id == "TLC_239":
            self._equip_weapon(player, Weapon("TLC_239t", "The Everbloom", 2, 5))
            self._event("quest_completed", player=player.index, card=quest_id,
                        reward="TLC_239t")
            return
        reward_id = LOST_CITY_QUEST_REWARDS.get(quest_id)
        if reward_id in self.card_defs and len(player.hand) < 10:
            self._add_generated(player, self._entity(reward_id, created_by=quest_id))
        self._event("quest_completed", player=player.index, card=quest_id, reward=reward_id)

    def _combine_soletos(self, player: Player) -> None:
        """Combine both Reach Equilibrium rewards when they are held together."""
        life = next((c for c in player.hand if c.card_id == "TLC_817t3"), None)
        touch = next((c for c in player.hand if c.card_id == "TLC_817t4"), None)
        if life is None or touch is None or "TLC_817t5" not in self.card_defs:
            return
        player.hand.remove(life)
        player.hand.remove(touch)
        combined = self._entity("TLC_817t5", created_by="TLC_817")
        player.hand.append(combined)
        self._event(
            "soletos_combined", player=player.index,
            source=[life.entity_id, touch.entity_id], entity=combined.entity_id,
        )

    def _activate_lost_city_quest(self, player: Player, card: CardInstance) -> None:
        """Move a Lost City quest from hand into the quest state zone."""
        if card.card_id not in LOST_CITY_QUEST_IDS:
            return
        if card.card_id in player.active_quests or card.card_id in player.completed_quests:
            return
        player.active_quests[card.card_id] = {"progress": 0, "turns": 0, "flags": set()}
        self._event(
            "quest_activated", player=player.index, card=card.card_id,
            entity=card.entity_id,
        )

    def clone(
        self,
        *,
        include_history: bool = False,
        skip_hidden_zones_of: int | None = None,
        record_events: bool | None = None,
    ) -> "DragonMirrorGame":
        """Return an independent search state with the exact same RNG stream.

        Immutable card metadata and the read-only rule registry are shared;
        players, entities, pending decisions and RNG state are copied. Search
        normally drops historical events because they are not part of game
        semantics and become increasingly expensive to copy at deep nodes.
        A public-belief determinization may also omit one player's private
        hand/deck, provided it replaces both zones before the cloned state is
        observed or stepped. Search callers can also disable event recording;
        event history is observability data and does not affect rule execution.
        """
        # Search creates millions of short-lived branches. Generic deepcopy
        # repeatedly reflects over the GameState object even though its static
        # card metadata and rule registry are shared. Use an explicit copy for
        # event-free search states; the ordinary deepcopy path remains for
        # history-bearing diagnostics and compatibility callers.
        use_search_clone = (
            not include_history
            and (record_events is False or (record_events is None and not self.record_events))
        )
        if use_search_clone:
            return self._clone_for_search(skip_hidden_zones_of=skip_hidden_zones_of)
        memo: dict[int, Any] = {
            id(self.card_defs): self.card_defs,
            id(self.rule_registry): self.rule_registry,
            # Deck definitions are constructor input and never mutated by a
            # game; sharing avoids rebuilding the nested count dictionaries in
            # every search branch.
            id(self.deck_counts): self.deck_counts,
        }
        if not include_history:
            memo[id(self.events)] = []
        if skip_hidden_zones_of is not None:
            if skip_hidden_zones_of not in (0, 1):
                raise ValueError("skip_hidden_zones_of must be player 0 or 1")
            skipped = self.players[skip_hidden_zones_of]
            memo[id(skipped.hand)] = []
            memo[id(skipped.deck)] = []
        result = copy.deepcopy(self, memo)
        if record_events is not None:
            result.record_events = record_events
        return result

    def _clone_for_search(
        self, *, skip_hidden_zones_of: int | None = None,
    ) -> "DragonMirrorGame":
        """Copy only mutable rule state for an event-free search branch."""
        if skip_hidden_zones_of is not None and skip_hidden_zones_of not in (0, 1):
            raise ValueError("skip_hidden_zones_of must be player 0 or 1")
        memo: dict[int, Any] = {
            id(self.card_defs): self.card_defs,
            id(self.rule_registry): self.rule_registry,
            id(self.deck_counts): self.deck_counts,
        }
        if skip_hidden_zones_of is not None:
            skipped = self.players[skip_hidden_zones_of]
            memo[id(skipped.hand)] = []
            memo[id(skipped.deck)] = []

        result = object.__new__(type(self))
        memo[id(self)] = result
        result.rng = copy.deepcopy(self.rng, memo)
        result.seed = self.seed
        result.turn = self.turn
        result.current = self.current
        result.first_player = self.first_player
        result.next_entity_id = self.next_entity_id
        result.invalid_actions = self.invalid_actions
        result.events = []
        result.record_events = False
        # Shadow the bound method for this branch. This removes a method call,
        # branch and dictionary allocation from every simulated card trigger.
        result._event = _discard_search_event
        result.finished = self.finished
        result.winner = self.winner
        result.minions_died_this_turn = self.minions_died_this_turn
        result.deck_counts = self.deck_counts
        result.rune_configs = self.rune_configs
        result.beatrix_choices = self.beatrix_choices
        result.card_defs = self.card_defs
        result.rule_registry = self.rule_registry
        result.players = copy.deepcopy(self.players, memo)
        # Copy after player zones so pending-choice options that reference a
        # held card retain the same cloned identity as that player's hand.
        result.pending_choice = copy.deepcopy(self.pending_choice, memo)
        return result

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

    def _summon_frail_ghoul(
        self, player: Player, *, source_card_id: str
    ) -> CardInstance | None:
        """Create the Frail Ghoul token used by Tower of Ghouls.

        The token is a generated entity and is intentionally not part of the
        collectible card metadata JSON.  Keeping its definition here avoids
        making generated-only tokens look like playable Standard cards.
        """
        if len(player.board) + len(player.locations) >= 7:
            return None
        token = CardInstance(
            self.next_entity_id,
            CardDef(
                "JAIL_450t", "Frail Ghoul", "MINION", 1, 1, 1,
                "UNDEAD", ("CHARGE",), "DEATHKNIGHT", ("UNDEAD",),
                "ESCAPE_FROM_VIOLET_HOLD",
            ),
            created_by=source_card_id,
            charge=True,
            summoned_turn=self.turn,
        )
        self.next_entity_id += 1
        self._summon(player, token)
        return token

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
        if (
            minion.card_id in {"TLC_605", "CORE_UNG_928"}
            and player.index != self.current
            and not minion.silenced
            and minion.dormant_turns == 0
        ):
            minion.opponent_turn_attack_bonus_active = True
            self._event(
                "opponent_turn_attack_toggle", player=player.index,
                entity=minion.entity_id, card=minion.card_id,
                active=True,
                attack_bonus={"TLC_605": 6, "CORE_UNG_928": 2}[minion.card_id],
            )
        if minion.has_race("MURLOC") and player.murloc_quest_buff:
            minion.attack_delta += 1
            minion.health_delta += 1
        self._event(
            "summon", player=player.index, card=minion.card_id,
            entity=minion.entity_id,
        )
        if minion.has_race("DEMON"):
            parasites = [
                candidate for candidate in player.board
                if candidate.card_id == "JAIL_721"
                and candidate.entity_id != minion.entity_id
                and not candidate.silenced
                and candidate.dormant_turns == 0
                and candidate.health > 0
            ]
            for parasite in parasites:
                parasite.attack_delta += minion.attack
                parasite.health_delta += minion.max_health
                self._event(
                    "tras_tath_gain_stats", player=player.index,
                    source=parasite.entity_id, summoned=minion.entity_id,
                    attack=minion.attack, health=minion.max_health,
                )
        if minion.card_id in {"TIME_009t1", "TIME_009t2"}:
            minion.aura_remaining_turns = 3
        if minion.has_race("MURLOC"):
            for tidecaller in tidecallers:
                tidecaller.attack_delta += 1
                self._event(
                    "murloc_tidecaller_trigger", player=player.index,
                    entity=tidecaller.entity_id, summoned=minion.card_id,
                )
        if (
            minion.card_id in {
                "CATA_525t", "CATA_565t", "CATA_725t", "CATA_726t",
                "CATA_726t1", "CATA_780t", "CATA_153t", "CATA_153t1",
                "CATA_154t", "CATA_154t1",
            }
            and minion.herald_power == 1
        ):
            minion.herald_power = self._herald_power(player.herald_count)
        self._refresh_continuous(player)
        if minion.card_id == "CATA_151t":
            amount = self._herald_power(player.herald_count)
            player.hero_attack_bonus += amount
            self._event(
                "azshara_tentacle", player=player.index,
                entity=minion.entity_id, attack=amount,
            )
        elif minion.card_id in {"CATA_154t", "CATA_154t1"}:
            # The Wing token's generated spell is discounted by the current
            # Herald tier.  Keep the class pool explicit and executable-only,
            # as with the other random-generation effects.
            candidates = sorted(
                card_id for card_id, definition in self.card_defs.items()
                if card_id in EXECUTABLE_CARD_IDS
                and definition.card_type == "SPELL"
                and definition.card_class in {
                    "DEMONHUNTER", "DRUID", "HUNTER", "MAGE", "PALADIN",
                    "PRIEST", "ROGUE", "SHAMAN", "WARLOCK", "WARRIOR",
                    "DEATHKNIGHT",
                }
                and definition.card_class != player.card_class
            )
            if candidates:
                generated = self._entity(
                    self.rng.choice(candidates), created_by=minion.card_id
                )
                generated.cost_delta -= minion.herald_power
                self._add_generated(player, generated)
                self._event(
                    "sinestra_wing_spell", player=player.index,
                    source=minion.entity_id, card=generated.card_id,
                    discount=minion.herald_power,
                )
        elif minion.card_id == "CATA_525t":
            amount = minion.herald_power
            player.hero_attack_bonus += amount
            self._event(
                "herald_azshara_soldier", player=player.index,
                entity=minion.entity_id, attack=amount,
            )
        elif minion.card_id == "CATA_780t":
            self._get_onyxia_wing_minion(player, minion, power=minion.herald_power)
        elif minion.card_id == "CATA_153":
            self._summon_colossal_appendages(player, minion, "CATA_153t", 2)
        elif minion.card_id == "CATA_154":
            self._summon_colossal_appendages(player, minion, "CATA_154t", 2)
        elif minion.card_id == "CATA_488":
            self._summon_colossal_appendages(player, minion, "CATA_488t", 2)
        elif minion.card_id == "CATA_300":
            self._summon_colossal_appendages(
                player, minion, "CATA_300t1", 3,
            )
        elif minion.card_id == "CATA_432":
            self._summon_chromatus_heads(player, minion)
        elif minion.card_id == "CATA_726":
            self._summon_colossal_appendages(player, minion, "CATA_726t", 2)
        elif minion.card_id == "CATA_151":
            self._summon_azshara_tentacles(player, minion)
        elif minion.card_id == "CATA_155":
            self._summon_onyxia_wings(player, minion)
        elif minion.card_id == "CATA_139":
            self._summon_wickerfang_legs(player, minion)
        elif minion.card_id in {"CATA_155t", "CATA_155t1"}:
            self._get_onyxia_wing_minion(player, minion)
        # Corpse Flower watches the opponent's completed summons.  Resolve
        # this after summon-side effects so the summoned minion is a legal
        # target, while still allowing the trigger to kill it immediately.
        opponent = self.players[1 - player.index]
        flowers = [m for m in opponent.board
                   if m.card_id == "EDR_815" and not m.silenced
                   and m.dormant_turns == 0 and m.health > 0]
        if flowers and player.index != opponent.index and opponent.corpses >= 2:
            for flower in flowers:
                if opponent.corpses < 2 or minion not in player.board:
                    break
                opponent.corpses -= 2
                self._damage_minion(player.index, minion, 3, flower)
                self._event("corpse_flower_trigger", player=opponent.index,
                            source=flower.entity_id, target=minion.entity_id)
                self._resolve_deaths()
        # Generic summon window used by Elemental and repeated-play cards.
        # It runs after token/Colossal side effects, so the payload represents
        # the final summoned entity and board position.
        for watcher in list(player.board):
            if (
                watcher not in player.board
                or watcher.silenced
                or watcher.dormant_turns > 0
                or watcher.health <= 0
            ):
                continue
            self.rule_registry.dispatch(
                Hook.AFTER_SUMMON, watcher.card_id, self,
                RuleContext(player=player, card=watcher,
                            payload={"summoned": minion}),
            )

    def _summon_colossal_appendages(
        self, player: Player, parent: CardInstance, card_id: str, count: int
    ) -> None:
        """Summon named Colossal appendages immediately beside their parent."""
        for offset in range(count):
            if len(player.board) + len(player.locations) >= 7:
                break
            index = player.board.index(parent)
            position = index if offset % 2 == 0 else index + 1
            appendage = self._entity(card_id, created_by=parent.card_id)
            appendage.colossal_parent_entity = parent.entity_id
            appendage.summoned_turn = self.turn
            self._summon(player, appendage, position=position)
            self._event(
                "colossal_appendage", player=player.index,
                source=parent.entity_id, entity=appendage.entity_id,
                side="left" if offset % 2 == 0 else "right",
            )

    def _summon_chromatus_heads(
        self, player: Player, chromatus: CardInstance
    ) -> None:
        """Summon Chromatus's four heads in printed order around its body."""
        for offset, card_id in enumerate(
            ("CATA_432t1", "CATA_432t2", "CATA_432t3", "CATA_432t4")
        ):
            if len(player.board) + len(player.locations) >= 7:
                break
            index = player.board.index(chromatus)
            position = index if offset % 2 == 0 else index + 1
            head = self._entity(card_id, created_by=chromatus.card_id)
            head.colossal_parent_entity = chromatus.entity_id
            head.summoned_turn = self.turn
            self._summon(player, head, position=position)
            self._event(
                "colossal_appendage", player=player.index,
                source=chromatus.entity_id, entity=head.entity_id,
                side="left" if offset % 2 == 0 else "right",
            )

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

    def _summon_onyxia_wings(
        self, player: Player, onyxia: CardInstance
    ) -> None:
        """Summon the two Colossal wings immediately beside Arisen Onyxia."""
        for side, card_id in (("left", "CATA_155t"), ("right", "CATA_155t1")):
            if len(player.board) + len(player.locations) >= 7:
                break
            main_index = player.board.index(onyxia)
            position = main_index if side == "left" else main_index + 1
            wing = self._entity(card_id, created_by=onyxia.card_id)
            wing.summoned_turn = self.turn
            self._summon(player, wing, position=position)
            self._event(
                "colossal_appendage", player=player.index,
                source=onyxia.entity_id, entity=wing.entity_id, side=side,
            )

    def _summon_wickerfang_legs(
        self, player: Player, wickerfang: CardInstance
    ) -> None:
        """Resolve Wickerfang's Colossal +4 as four adjacent named Legs.

        The four token IDs are distinct in HearthstoneJSON even though their
        display name is identical. Keeping that identity makes replay traces
        auditable and avoids accidentally manufacturing a fifth leg.
        """
        for side, card_id in (
            ("left_1", "CATA_139t"),
            ("left_2", "CATA_139t2"),
            ("right_1", "CATA_139t3"),
            ("right_2", "CATA_139t4"),
        ):
            if len(player.board) + len(player.locations) >= 7:
                break
            main_index = player.board.index(wickerfang)
            position = main_index if side.startswith("left") else main_index + 1
            leg = self._entity(card_id, created_by=wickerfang.card_id)
            leg.colossal_parent_entity = wickerfang.entity_id
            leg.summoned_turn = self.turn
            self._summon(player, leg, position=position)
            self._event(
                "colossal_appendage", player=player.index,
                source=wickerfang.entity_id, entity=leg.entity_id, side=side,
            )

    def _get_onyxia_wing_minion(
        self, player: Player, wing: CardInstance, *, power: int | None = None
    ) -> None:
        """Get a Herald-scaled minion that costs Health only this turn."""
        cost = power if power is not None else self._herald_power(player.herald_count)
        candidates = [
            definition for card_id, definition in self.card_defs.items()
            if card_id in EXECUTABLE_CARD_IDS
            and definition.card_type == "MINION"
            and definition.cost == cost
        ]
        if not candidates:
            return
        generated = CardInstance(
            self.next_entity_id, self.rng.choice(candidates),
            created_by=wing.card_id,
        )
        self.next_entity_id += 1
        generated.costs_health_expiry_turn = 1 - player.index
        if len(player.hand) < 10:
            player.hand.append(generated)
            destination = "hand"
        else:
            destination = "burned"
        self._event(
            "onyxia_wing_generated", player=player.index, source=wing.entity_id,
            card=generated.card_id, entity=generated.entity_id, cost=cost,
            destination=destination,
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
        card.drawn_turn = self.turn
        player.cards_drawn_this_turn += 1
        for minion in player.board:
            if minion.card_id == "TTN_844" and not minion.silenced:
                minion.attack_delta += 1
        if (card.card_id in {"CATA_134", "CATA_306", "CATA_479", "CATA_489", "CATA_820"}
                and not card.shatter_combined):
            self._split_shatter_card(player, card)
            self._after_card_draw(player, card)
            return
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
            if player.recover_overdrawn_cards:
                card.cost_delta -= 1
                player.overdrawn_cards.append(card)
                self._event(
                    "overdraw_queued", player=player.index, card=card.card_id,
                    entity=card.entity_id, discounted_cost=card.cost,
                )
        else:
            player.hand.append(card)
            self._event("draw", player=player.index, card=card.card_id)
        self._after_card_draw(player, card)

    def _restore_overdrawn_cards(self, player: Player) -> None:
        """Return Godfrey-tracked burns in original burn order when space opens."""
        while player.overdrawn_cards and len(player.hand) < 10:
            card = player.overdrawn_cards.pop(0)
            player.hand.append(card)
            self._event(
                "overdraw_return", player=player.index, card=card.card_id,
                entity=card.entity_id, cost=card.cost,
            )

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

    def _queue_end_turn_return(self, player: Player, card: CardInstance) -> None:
        """Keep an already-played card out of zones until its owner's end step."""
        player.pending_end_turn_returns.append(card)
        self._event(
            "return_queued_end_turn", player=player.index,
            card=card.card_id, entity=card.entity_id,
        )

    def _arm_secret(self, player: Player, card: CardInstance) -> None:
        """Arm a Secret, enforcing the live seven-secret capacity."""
        if len(player.secrets) >= 7:
            self._event(
                "secret_burned", player=player.index,
                card=card.card_id, entity=card.entity_id, reason="secret_cap",
            )
            return
        if any(secret.card_id == card.card_id for secret in player.secrets):
            self._event(
                "secret_burned", player=player.index,
                card=card.card_id, entity=card.entity_id, reason="duplicate",
            )
            return
        player.secrets.append(card)
        self._event(
            "secret_armed", player=player.index,
            card=card.card_id, entity=card.entity_id,
        )

    def _consume_secret(self, player: Player, secret: CardInstance) -> None:
        player.secrets.remove(secret)
        self._event(
            "secret_trigger", player=player.index,
            card=secret.card_id, entity=secret.entity_id,
        )

    def _trigger_secrets_after_hero_attacked(self, defender: Player) -> None:
        """Resolve implemented secrets after combat damage reaches a hero."""
        for secret in list(defender.secrets):
            if secret.card_id == "CORE_EX1_289":
                self._consume_secret(defender, secret)
                self._gain_armor(defender, 8)
                self._event(
                    "ice_barrier", player=defender.index,
                    source=secret.entity_id, armor=8,
                )
                continue
            if secret.card_id != "CORE_EX1_610":
                continue
            self._consume_secret(defender, secret)
            attacker = self.players[1 - defender.index]
            self._damage_hero(attacker, 2, secret)
            for minion in list(attacker.board):
                self._damage_minion(attacker.index, minion, 2, secret)
        self._resolve_deaths()

    def _trigger_freezing_trap(self, attacker: CardInstance, defender: Player) -> bool:
        for secret in list(defender.secrets):
            if secret.card_id != "CORE_EX1_611":
                continue
            self._consume_secret(defender, secret)
            owner = self.players[self.current]
            if attacker in owner.board:
                owner.board.remove(attacker)
            if len(owner.hand) < 10:
                attacker.cost_delta += 2
                owner.hand.append(attacker)
                destination = "hand"
            else:
                destination = "burned"
            self._event(
                "freezing_trap", player=defender.index,
                source=secret.entity_id, attacker=attacker.entity_id,
                destination=destination,
            )
            return True
        return False

    def _trigger_vaporize(self, attacker: CardInstance, defender: Player) -> bool:
        for secret in list(defender.secrets):
            if secret.card_id != "EX1_594":
                continue
            self._consume_secret(defender, secret)
            attacker.damage = attacker.max_health
            self._resolve_deaths()
            self._event(
                "vaporize", player=defender.index,
                source=secret.entity_id, attacker=attacker.entity_id,
            )
            return True
        return False

    def _trigger_snake_trap(self, defender: Player) -> bool:
        for secret in list(defender.secrets):
            if secret.card_id != "CORE_EX1_554":
                continue
            self._consume_secret(defender, secret)
            summoned = 0
            while len(defender.board) + len(defender.locations) < 7 and summoned < 3:
                snake = self._instance_from_definition(
                    CardDef(
                        "EX1_554t", "Snake", "MINION", 1, 1, 1,
                        "BEAST", (), "HUNTER", ("BEAST",), "EXPERT1",
                    ),
                    created_by=secret.card_id,
                )
                snake.summoned_turn = self.turn
                self._summon(defender, snake)
                summoned += 1
            self._event(
                "snake_trap", player=defender.index,
                source=secret.entity_id, summoned=summoned,
            )
            return True
        return False

    def _trigger_noble_sacrifice(self, defender: Player) -> CardInstance | None:
        for secret in list(defender.secrets):
            if secret.card_id != "CORE_EX1_130":
                continue
            self._consume_secret(defender, secret)
            if len(defender.board) + len(defender.locations) >= 7:
                self._event("noble_sacrifice", player=defender.index, summoned=False)
                return None
            token = self._instance_from_definition(
                CardDef(
                    "EX1_130a", "Defender", "MINION", 1, 2, 1,
                    "DRAENEI", (), "PALADIN", ("DRAENEI",), "EXPERT1",
                ),
                created_by=secret.card_id,
            )
            token.summoned_turn = self.turn
            self._summon(defender, token)
            self._event(
                "noble_sacrifice", player=defender.index,
                source=secret.entity_id, summoned=token.entity_id,
            )
            return token
        return None

    def _trigger_end_turn_secrets(self, ending_player: Player) -> None:
        """Resolve enemy Secrets whose condition is the active player's end step."""
        owner = self.players[1 - ending_player.index]
        for secret in list(owner.secrets):
            if secret.card_id != "END_024":
                continue
            candidates = [
                minion for minion in ending_player.board
                if minion.dormant_turns == 0 and minion.health > 0
            ]
            if not candidates:
                continue
            highest = max(minion.health for minion in candidates)
            target = self.rng.choice([
                minion for minion in candidates if minion.health == highest
            ])
            self._consume_secret(owner, secret)
            target.damage = target.max_health
            self._event(
                "flames_of_infinity", player=owner.index,
                target_player=ending_player.index, target=target.entity_id,
            )
            self._resolve_deaths()

    def _trigger_secrets_after_enemy_minion_play(
        self, player: Player, minion: CardInstance
    ) -> None:
        """Resolve implemented opponent-minion-play Secrets after Battlecry."""
        owner = self.players[1 - player.index]
        for secret in list(owner.secrets):
            if secret.card_id == "EX1_609":
                self._consume_secret(owner, secret)
                self._damage_minion(player.index, minion, 6, secret)
                self._resolve_deaths()
                self._event(
                    "snipe", player=owner.index,
                    source=secret.entity_id, target=minion.entity_id,
                )
                continue
            if secret.card_id == "EX1_379":
                self._consume_secret(owner, secret)
                minion.damage = max(0, minion.max_health - 1)
                self._event(
                    "repentance", player=owner.index,
                    source=secret.entity_id, target=minion.entity_id,
                )
                self._resolve_deaths()
                continue
            if secret.card_id == "CORE_EX1_294":
                self._consume_secret(owner, secret)
                if len(owner.board) + len(owner.locations) < 7:
                    copy_card = minion.clone(self.next_entity_id)
                    self.next_entity_id += 1
                    copy_card.created_by = secret.card_id
                    copy_card.summoned_turn = self.turn
                    self._summon(owner, copy_card)
                    self._event(
                        "mirror_entity", player=owner.index,
                        source=secret.entity_id, copied=minion.entity_id,
                        summoned=copy_card.entity_id,
                    )
                continue
            if secret.card_id != "CORE_LOOT_101":
                continue
            before = max(0, minion.health)
            had_shield = minion.divine_shield
            self._consume_secret(owner, secret)
            self._damage_minion(player.index, minion, 6, secret)
            dealt = before - max(0, minion.health)
            excess = 0
            if not had_shield and dealt == before:
                excess = max(0, 6 - before)
            if excess:
                self._damage_hero(player, excess, secret)
            self._resolve_deaths()
            self._event(
                "explosive_runes", player=owner.index,
                target_player=player.index, target=minion.entity_id,
                dealt=dealt, excess=excess,
            )

    def _trigger_secrets_after_enemy_spell_cast(self, player: Player) -> None:
        owner = self.players[1 - player.index]
        for secret in list(owner.secrets):
            if secret.card_id != "CORE_KAR_004":
                continue
            self._consume_secret(owner, secret)
            if len(owner.board) + len(owner.locations) >= 7:
                self._event("cat_trick", player=owner.index, summoned=False)
                continue
            panther = self._instance_from_definition(
                CardDef(
                    "KAR_004a", "Cat in a Hat", "MINION", 3, 4, 2,
                    "BEAST", ("STEALTH",), "HUNTER", ("BEAST",), "KARA",
                ),
                created_by=secret.card_id,
            )
            panther.summoned_turn = self.turn
            self._summon(owner, panther)
            self._event(
                "cat_trick", player=owner.index,
                source=secret.entity_id, summoned=panther.entity_id,
            )

    def _start_turn(self, index: int) -> None:
        self.current = index
        self.turn += 1
        self.minions_died_this_turn = 0
        player = self.players[index]
        if (
            player.hero_power_cost_surcharge
            and player.hero_power_cost_surcharge_expiry_turn < self.turn
        ):
            self._event(
                "hero_power_surcharge_expired", player=player.index,
                amount=player.hero_power_cost_surcharge,
            )
            player.hero_power_cost_surcharge = 0
            player.hero_power_cost_surcharge_expiry_turn = -1
        if player.sigil_of_cinder_turn == self.turn:
            amount = max(0, player.sigil_of_cinder_damage)
            player.sigil_of_cinder_turn = -1
            player.sigil_of_cinder_damage = 0
            hits = 0
            for _ in range(amount):
                targets = self._random_enemy_characters(player.index)
                if not targets:
                    break
                self._deal_to_target(
                    player.index, self.rng.choice(targets), 1,
                )
                hits += 1
                self._resolve_deaths()
            self._event(
                "sigil_of_cinder_trigger", player=player.index,
                amount=amount, hits=hits,
            )
        player.friendly_minions_died_this_turn = 0
        if player.hero_immune_expiry_turn == self.turn:
            player.hero_immune = False
            player.hero_immune_expiry_turn = -1
            self._event("hero_immune_expire", player=index)
        if player.holmes_watch_turn >= 0 and player.holmes_watch_turn < self.turn:
            self._event(
                "holmes_expire", player=player.index,
                target=player.holmes_target_card_id,
            )
            player.holmes_target_card_id = None
            player.holmes_watch_turn = -1
        if player.skip_next_turn:
            player.skip_next_turn = False
            self._event("turn_skipped", player=index, source="END_037")
            self._event("turn_start", player=index, skipped=True)
            self._event("turn_end", player=index, skipped=True)
            self._start_turn(1 - index)
            return
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
                expired_health = [
                    modifier for modifier in minion.temporary_health_modifiers
                    if modifier[1] == index
                ]
                for amount, expiry in expired_health:
                    minion.health_delta -= amount
                    minion.temporary_health_modifiers.remove((amount, expiry))
                    self._event(
                        "temporary_health_expire", player=owner.index,
                        entity=minion.entity_id, amount=amount,
                    )
                if minion.temporary_immune_expiry_turn == index:
                    minion.immune = False
                    minion.immune_while_attacking = False
                    minion.temporary_immune_expiry_turn = -1
                    self._event(
                        "temporary_immune_expire", player=owner.index,
                        entity=minion.entity_id,
                    )
                if minion.destroy_at_turn_start == index:
                    minion.damage = minion.max_health
                    minion.destroy_at_turn_start = -1
                    self._event(
                        "delayed_destroy", player=owner.index,
                        entity=minion.entity_id,
                    )
            for card in owner.hand:
                if card.costs_health_expiry_turn == index:
                    card.costs_health_expiry_turn = -1
                if card.card_id == "EDR_843":
                    card.held_turns += 1
                    if card.held_turns >= 3 and "EDR_843t1" in self.card_defs:
                        card.definition = self.card_defs["EDR_843t1"]
                        self._event(
                            "reforestation_upgraded", player=owner.index,
                            entity=card.entity_id, card=card.card_id,
                        )
                    self._event(
                        "health_cost_expire", player=owner.index,
                        card=card.card_id, entity=card.entity_id,
                    )
        self._resolve_deaths()
        player.turns_taken += 1
        # Tar Creeper/Tar Tyrant have conditional attack while their controller
        # waits through the opponent's turn. Toggle a flag at the turn boundary
        # instead of permanently changing attack_delta; this is deterministic
        # in cloned MCTS states and naturally disappears on the owner's turn.
        for owner in self.players:
            for minion in owner.board:
                if minion.card_id not in {"TLC_605", "CORE_UNG_928"}:
                    continue
                active = (
                    owner.index != index
                    and not minion.silenced
                    and minion.dormant_turns == 0
                    and minion.health > 0
                )
                if minion.opponent_turn_attack_bonus_active == active:
                    continue
                minion.opponent_turn_attack_bonus_active = active
                self._event(
                    "opponent_turn_attack_toggle", player=owner.index,
                    entity=minion.entity_id, active=active,
                    card=minion.card_id,
                    attack_bonus=(
                        {"TLC_605": 6, "CORE_UNG_928": 2}[minion.card_id]
                        if active else 0
                    ),
                )
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
        if player.chef_nethrek_turns_remaining > 0:
            player.chef_nethrek_turns_remaining -= 1
            if player.chef_nethrek_turns_remaining == 0:
                player.max_mana = 10
                player.locked_mana = 0
                player.mana = 10
                self._event(
                    "rulebreaker_trigger", player=index,
                    card="JAIL_860", effect="set_mana_to_ten",
                )
        if player.irida_active and player.void_cards:
            returned: list[str] = []
            for _ in range(2):
                if not player.void_cards:
                    break
                card_from_void = player.void_cards.pop(0)
                if len(player.hand) < 10:
                    player.hand.append(card_from_void)
                    returned.append(card_from_void.card_id)
                else:
                    # A full hand burns the card rather than putting it back
                    # into the normal deck, matching ordinary draw handling.
                    returned.append(f"burned:{card_from_void.card_id}")
            self._event(
                "irida_void_draw", player=index,
                cards=returned, remaining=len(player.void_cards),
            )
        if player.start_turn_temporary_mana_charges:
            player.mana += 1
            player.start_turn_temporary_mana_charges -= 1
            self._event(
                "start_turn_temporary_mana", player=player.index,
                remaining=player.start_turn_temporary_mana_charges,
            )
        player.hero_attack_bonus = 0
        if player.hero_lifesteal_turn != -1:
            player.hero_lifesteal_turn = -1
        player.hero_attacks_this_turn = 0
        player.hero_power_used = False
        player.imbue_passive_triggered_this_turn = False
        player.next_beast_cost_reduction = 0
        player.next_murloc_cost_reduction = 0
        if player.map_followup_turn != self.turn:
            player.map_followup_options.clear()
            player.map_followup_entity = None
            player.map_followup_turn = -1
        player.fire_spell_played = False
        player.cards_played_this_turn = 0
        player.cards_drawn_this_turn = 0
        player.spells_cast_this_turn = 0
        player.mug_magic_used_this_turn = False
        player.dragons_played_this_turn = 0
        player.damaged_characters_this_turn.clear()
        player.hero_health_changed_this_turn = False
        self._reform_nythendra(player)
        for minion in player.board:
            if minion.card_id == "TLC_253" and minion.dormant_turns > 0 and not minion.silenced:
                minion.attack_delta += 2
                minion.health_delta += 2
                if self.rng.random() < 0.5:
                    minion.dormant_turns = 0
                    self._event("petrified_ogre_awaken", player=player.index,
                                entity=minion.entity_id)
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
                    if minion.card_id == "EDR_840t":
                        player.hero_attack_bonus += 3
                        self._event("hound_dreadseed_awaken", player=index,
                                    entity=minion.entity_id, attack=3)
        # Rotate hand-held bonus effects before the draw for cards such as
        # Twisted Monstrosity.
        for minion in list(player.board):
            if (
                minion not in player.board
                or minion.silenced
                or minion.dormant_turns > 0
                or minion.health <= 0
            ):
                continue
            self.rule_registry.dispatch(
                Hook.START_TURN, minion.card_id, self,
                RuleContext(player=player, card=minion),
            )
            self._resolve_deaths()
        for held in list(player.hand):
            self.rule_registry.dispatch(
                Hook.START_TURN, held.card_id, self,
                RuleContext(player=player, card=held),
            )
        for location in player.locations:
            location.cooldown = max(0, location.cooldown - 1)
        if player.geddon_draw:
            self._offer_geddon_draw(player)
        elif any(
            minion.card_id == "TIME_617"
            and not minion.silenced
            and minion.dormant_turns == 0
            for minion in player.board
        ):
            self._event("chronochiller_skip_draw", player=index)
        else:
            self._draw(player)
        self._event("turn_start", player=index)

    def _end_turn(self) -> None:
        player = self.players[self.current]
        # Foxy Fraud's discount cannot carry into a later turn, even when its
        # controller chose not to play another Combo card this turn.
        player.next_combo_cost_reduction = 0
        if player.hatching_ceremony_trigger_turn == player.turns_taken:
            affected = []
            for minion in player.board:
                if minion.dormant_turns > 0:
                    continue
                minion.attack_delta += 2
                minion.health_delta += 2
                affected.append(minion.entity_id)
            player.hatching_ceremony_trigger_turn = -1
            self._event(
                "hatching_ceremony", player=player.index, affected=affected,
            )
        lakkari_turns = max(0, int(getattr(player, "lakkari_turns", 0)))
        if lakkari_turns:
            if player.hand:
                discarded = self.rng.choice(player.hand)
                player.hand.remove(discarded)
                self._event(
                    "discard", player=player.index, card=discarded.card_id,
                    source="TLC_466", entity=discarded.entity_id,
                )
                self._dispatch_after_discard(player, discarded)
            while len(player.board) + len(player.locations) < 7:
                if "Story_09_Imp" not in self.card_defs:
                    break
                imp = self._entity("Story_09_Imp", created_by="TLC_466")
                imp.attack_delta += 2
                imp.health_delta += 1
                imp.summoned_turn = self.turn
                self._summon(player, imp)
            player.lakkari_turns = lakkari_turns - 1
            self._event(
                "story_of_lakkari_tick", player=player.index,
                remaining=player.lakkari_turns,
            )
        # Start the new observation window before end-of-turn triggers. Any
        # Undead dying in those triggers belongs to the next opponent turn.
        player.undead_died_after_last_turn = False
        for minion in list(player.board):
            if minion.card_id == "EDR_979" and minion.dormant_turns > 0 and not minion.silenced:
                self._gain_armor(player, 3)
                self._draw(player)
                continue
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
            elif minion.card_id in {"CATA_300t1", "CATA_300t2", "CATA_300t3"} and not minion.silenced:
                damaged = [m for m in player.board if m.health > 0 and m.damage > 0]
                if player.health < player.max_health:
                    damaged.append(None)
                if damaged:
                    target = self.rng.choice(damaged)
                    if target is None:
                        player.health = min(player.max_health, player.health + 3)
                        restored = "hero"
                    else:
                        amount = min(3, target.damage)
                        target.damage -= amount
                        restored = target.entity_id
                    self._event("black_blood_restore", player=player.index,
                                source=minion.entity_id, restored=restored)
                    self._black_blood_after_restore(player, source=minion)
            elif not minion.silenced and self.rule_registry.dispatch(
                Hook.END_TURN, minion.card_id, self,
                RuleContext(player=player, card=minion),
            ):
                # Declarative end-turn triggers resolve in board order, just
                # like the engine-owned triggers in this loop.
                pass
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
            elif minion.card_id == "JAIL_887t2" and not minion.silenced:
                discarded = player.zuramat_discarded_card
                player.zuramat_discarded_card = None
                if discarded is not None:
                    discarded.created_by = minion.card_id
                    if discarded.definition.card_type == "MINION":
                        if len(player.board) + len(player.locations) < 7:
                            discarded.summoned_turn = self.turn
                            self._summon(player, discarded)
                            self._battlecry(
                                player, discarded,
                                Action("PLAY", discarded.entity_id),
                            )
                    elif discarded.definition.card_type == "SPELL":
                        try:
                            self._cast_spell(
                                player, discarded,
                                Action("PLAY", discarded.entity_id),
                            )
                        except ValueError:
                            for target_player, target_entity, _ in self._random_spell_target_candidates(
                                player.index, discarded
                            ):
                                try:
                                    self._cast_spell(
                                        player, discarded,
                                        Action("PLAY", discarded.entity_id, target_player, target_entity),
                                    )
                                    break
                                except ValueError:
                                    continue
                    self._event(
                        "zuramat_play_discarded", player=player.index,
                        source=minion.entity_id, card=discarded.card_id,
                    )
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
                candidates = self._random_enemy_minions(player.index)
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
                targets = self._random_enemy_minions(player.index)
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
        self._trigger_end_turn_secrets(player)
        if player.mograine_active:
            self._damage_hero(self.players[1 - player.index], 3)
            self._event("mograine_end_turn_damage", player=player.index, amount=3)
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
        while player.pending_end_turn_returns:
            card = player.pending_end_turn_returns.pop(0)
            if len(player.hand) < 10:
                player.hand.append(card)
                self._event(
                    "returned_to_hand", player=player.index,
                    card=card.card_id, entity=card.entity_id,
                    source=card.card_id, destination="hand",
                )
            else:
                self._event(
                    "burn", player=player.index, card=card.card_id,
                    entity=card.entity_id, source="end_turn_return",
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
        player.minion_played_last_turn = player.minion_played_this_turn
        player.minion_played_this_turn = False
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
        if card.definition.card_type == "SPELL":
            cost -= player.next_spell_cost_reduction
            if player.spell_cost_surcharge_turn == self.turn:
                cost += player.spell_cost_surcharge
        cost += self.rule_registry.cost_adjustment(self, player, card)
        if (
            card.definition.card_type == "MINION"
            and player.minion_cost_increase_turn == self.turn
        ):
            cost += player.minion_cost_increase_amount
        if card.definition.card_type == "MINION":
            cost -= player.next_minion_cost_reduction
            cost += 2 * sum(
                minion.card_id == "JAIL_890"
                and not minion.silenced
                and minion.dormant_turns == 0
                for owner in self.players for minion in owner.board
            )
            if (
                player.mug_magic_active
                and self.turn >= 3
                and not player.mug_magic_used_this_turn
            ):
                cost -= 2
        if card.card_id == "TOY_519":
            cost -= player.cards_drawn_this_turn
        if card.card_id == "TTN_841":
            cost -= player.cards_drawn_this_turn
        if card.card_id == "SW_037":
            cost -= player.cards_drawn_this_turn
        if card.has_race("BEAST"):
            cost -= player.next_beast_cost_reduction
        if card.has_race("MURLOC"):
            cost -= player.next_murloc_cost_reduction
        if card.has_race("DEMON"):
            cost -= player.next_demon_cost_reduction
        if (
            player.next_combo_cost_reduction
            and player.cards_played_this_turn > 0
            and "combo" in card.definition.text.casefold()
        ):
            cost -= player.next_combo_cost_reduction
        if card.card_id == "TLC_600" and "DRAGON" in player.played_races_last_turn:
            cost -= 3
        if card.card_id == "CATA_568":
            cost -= player.hero_attacks_this_game
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
        if card.card_id == "TIME_022" and any(
            minion.dormant_turns > 0 and minion.health > 0
            for owner in self.players for minion in owner.board
        ):
            cost -= 4
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
        if (
            card.definition.card_type == "MINION"
            and player.next_minion_cost_reduction == 99
        ):
            cost = 1
        return max(0, cost)

    @staticmethod
    def _kindred_active(player: Player, card: CardInstance) -> bool:
        """Whether a card's tribe was played during the previous turn."""
        races = set(card.definition.races)
        # Race-less spells use the generic Kindred condition: any friendly
        # minion tribe played during the previous turn activates them.
        return bool(races & player.played_races_last_turn) if races and "ALL" not in races else bool(
            player.played_races_last_turn
        )

    def _kindred_repeats(self, player: Player, card: CardInstance) -> int:
        """Return Kindred repeat count and consume the one-shot multiplier."""
        if not self._kindred_active(player, card):
            return 0
        repeats = 2 if player.kindred_triggers_twice else 1
        player.kindred_triggers_twice = 0
        return repeats

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

    def _refresh_wickerfang(
        self, player: Player, *, parent_entity: int | None = None
    ) -> None:
        """Synchronize Wickerfang with permanent stat gains on its own Legs.

        ``attack_delta``/``health_delta`` describe persistent enchantments in
        this engine. Auras deliberately do not enter this calculation: their
        source may disappear without a new stat-gain event. Subtracting the
        previously inherited amount preserves buffs applied directly to the
        Wickerfang body.
        """
        parents = [
            minion for minion in player.board
            if minion.card_id == "CATA_139"
            and (parent_entity is None or minion.entity_id == parent_entity)
        ]
        for parent in parents:
            # A Silence removes the accumulated copied enchantments and the
            # body has no text left to observe later leg buffs.  Silenced is
            # irreversible for a minion instance in Hearthstone, so clearing
            # the bookkeeping here cannot accidentally restore those stats.
            if parent.silenced:
                parent.wickerfang_inherited_attack = 0
                parent.wickerfang_inherited_health = 0
                continue
            legs = [
                minion for minion in player.board
                if minion.colossal_parent_entity == parent.entity_id
                and minion.card_id in {"CATA_139t", "CATA_139t2", "CATA_139t3", "CATA_139t4"}
            ]
            inherited_attack = sum(leg.attack_delta for leg in legs)
            inherited_health = sum(leg.health_delta for leg in legs)
            parent.attack_delta += inherited_attack - parent.wickerfang_inherited_attack
            parent.health_delta += inherited_health - parent.wickerfang_inherited_health
            parent.wickerfang_inherited_attack = inherited_attack
            parent.wickerfang_inherited_health = inherited_health

    def _grow_wickerfang_leg(
        self, player: Player, leg: CardInstance
    ) -> None:
        """Engine primitive used by the declarative Wickerfang Leg rule."""
        leg.attack_delta += 1
        leg.health_delta += 1
        self._refresh_wickerfang(
            player, parent_entity=leg.colossal_parent_entity,
        )
        self._event(
            "wickerfang_leg_grow", player=player.index,
            entity=leg.entity_id, parent=leg.colossal_parent_entity,
            attack=leg.attack, health=leg.max_health,
        )

    def _refresh_continuous(self, player: Player) -> None:
        self._refresh_scrappy(player)
        self._refresh_wickerfang(player)
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
        charged_hand_neighbors: dict[int, int] = {}
        for index, source in enumerate(player.board):
            if source.card_id not in {"CATA_153t", "CATA_153t1", "CATA_565t"} or source not in active:
                continue
            bonus = max(1, source.herald_power)
            for neighbor_index in (index - 1, index + 1):
                if 0 <= neighbor_index < len(player.board):
                    neighbor = player.board[neighbor_index]
                    if neighbor in active:
                        charged_hand_neighbors[neighbor.entity_id] = (
                            charged_hand_neighbors.get(neighbor.entity_id, 0)
                            + bonus
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
                    + charged_hand_neighbors.get(minion.entity_id, 0)
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
        coin_id = player.coin_replacement_id or "GAME_005"
        coin = self._entity(coin_id, created_by=source)
        player.hand.append(coin)
        self._event(
            "coin_given", player=player.index, source=source,
            card=coin_id, entity=coin.entity_id,
        )

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

    def _random_enemy_minions(
        self, player_index: int, *, alive_only: bool = True
    ) -> list[CardInstance]:
        """Return enemy minions eligible for a random effect.

        Stealth does not protect a minion from random effects; Dormant does.
        Most damage/destruction effects also ignore already-dead minions, so
        that is the default here.
        """
        enemy = self.players[1 - player_index]
        return [
            minion for minion in enemy.board
            if minion.dormant_turns == 0
            and (not alive_only or minion.health > 0)
        ]

    def _random_spell_target_candidates(
        self, player_index: int, spell: CardInstance
    ) -> list[tuple[int, int | None, str]]:
        """Return a randomized, text-constrained target pool for a spell.

        The spell resolver still performs the final legality check.  This
        helper only applies the broad faction constraint from card text and
        randomizes candidates uniformly before that check.
        """
        text = spell.definition.text.casefold()
        enemy_only = "enemy" in text and "friendly" not in text
        friendly_only = "friendly" in text and "enemy" not in text
        enemy_minion_only = "enemy minion" in text
        friendly_minion_only = "friendly minion" in text
        # "character" explicitly includes the hero.  For minion wording,
        # do not silently add a hero to the random pool.
        enemy_character = "enemy character" in text
        friendly_character = "friendly character" in text
        enemy_priority = any(
            token in text
            for token in ("prefer enemy", "enemy first", "prioritize enemy", "enemy targets first")
        )
        friendly_priority = any(
            token in text
            for token in ("prefer friendly", "friendly first", "prioritize friendly", "friendly targets first")
        )
        enemy_candidates: list[tuple[int, int | None, str]] = []
        friendly_candidates: list[tuple[int, int | None, str]] = []
        if not friendly_only:
            if not enemy_minion_only and (
                enemy_character or "enemy" in text
                or ("enemy" not in text and "friendly" not in text)
            ):
                enemy_candidates.append((1 - player_index, None, "enemy_hero"))
            enemy_candidates.extend(
                (1 - player_index, minion.entity_id, "enemy_minion")
                for minion in self.players[1 - player_index].board
                if minion.dormant_turns == 0
            )
        if not enemy_only:
            if not friendly_minion_only and (
                friendly_character or "friendly" in text
                or ("enemy" not in text and "friendly" not in text)
            ):
                friendly_candidates.append((player_index, None, "friendly_hero"))
            friendly_candidates.extend(
                (player_index, minion.entity_id, "friendly_minion")
                for minion in self.players[player_index].board
                if minion.dormant_turns == 0
            )
        # Shuffle each faction independently.  Priority means “try this
        # faction first, then fall back to the other faction if it has no
        # legal target”; it must not be undone by a final global shuffle.
        self.rng.shuffle(enemy_candidates)
        self.rng.shuffle(friendly_candidates)
        if enemy_priority and enemy_candidates and friendly_candidates:
            return enemy_candidates + friendly_candidates
        if friendly_priority and enemy_candidates and friendly_candidates:
            return friendly_candidates + enemy_candidates
        candidates = enemy_candidates + friendly_candidates
        self.rng.shuffle(candidates)
        return candidates

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
        algethar_instructor = sum(
            2 for minion in player.board
            if minion.card_id == "TIME_856"
            and not minion.silenced
            and minion.dormant_turns == 0
            and minion.health > 0
        )
        return (
            dynamic_seer_damage + generic_damage + algethar_instructor
            + player.next_spell_damage_bonus
        )

    def _spell_effect_amount(self, player: Player, card: CardInstance, amount: int) -> int:
        """Apply shared spell-damage and spell-doubling replacement effects.

        This is intentionally the one entry point used by declarative damage
        and healing effects.  A weapon such as Atiesh doubles the final spell
        effect (base amount plus Spell Damage), not merely the Spell Damage.
        """
        if card.definition.card_type != "SPELL":
            return amount
        amount += self._spell_damage(player)
        if player.weapon is not None and player.weapon.card_id == "TIME_890t":
            amount *= 2
        return amount

    def _hero_power_cost(self, player: Player) -> int:
        if player.hero_power_cost_override is not None:
            base_cost = player.hero_power_cost_override
        elif player.hero_power_id is not None:
            base_cost = self.card_defs[player.hero_power_id].cost
        else:
            free = any(
                minion.card_id == "TIME_606"
                and not minion.silenced
                and minion.dormant_turns == 0
                for minion in player.board
            ) and len(player.hand) <= 3
            base_cost = 0 if free else (1 if player.card_class == "DEMONHUNTER" else 2)
        surcharge = (
            player.hero_power_cost_surcharge
            if player.hero_power_cost_surcharge_expiry_turn == self.turn
            else 0
        )
        return max(0, base_cost + surcharge)

    def _hero_power_actions(self, player: Player) -> list[Action]:
        if player.hero_power_id == "END_003p":
            return []
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
        if player.hero_power_id == "JAIL_446hp":
            if player.corpses < 3:
                raise ValueError("Vampyr's Kiss requires 3 corpses")
            player.corpses -= 3
            self._event(
                "spend_corpses", player=player.index, amount=3,
                source="JAIL_446hp",
            )
        else:
            self._spend_mana(player, self._hero_power_cost(player))
        if (
            player.hero_power_cost_surcharge
            and player.hero_power_cost_surcharge_expiry_turn == self.turn
        ):
            surcharge = player.hero_power_cost_surcharge
            player.hero_power_cost_surcharge = 0
            player.hero_power_cost_surcharge_expiry_turn = -1
            self._event(
                "hero_power_surcharge_consumed", player=player.index,
                amount=surcharge,
            )
        # Effects such as Fleeing Treant make exactly the next Hero Power
        # free; consume the override at resolution time.
        if player.hero_power_cost_override is not None:
            player.hero_power_cost_override = None
        player.hero_power_used = True
        if player.hero_power_id is not None:
            imbued_power = player.imbued_hero_power_id
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
            self._dispatch_after_hero_power(player)
            # Some Imbue cards temporarily transform the hero power while it
            # is used.  Restore the imbued power afterward without resetting
            # its cumulative progress.
            if imbued_power is not None:
                player.hero_power_id = imbued_power
            return
        card_class = player.card_class
        if card_class == "WARRIOR":
            self._gain_armor(player, player.hero_power_armor)
        elif card_class == "MAGE":
            bonus = sum(
                minion.card_id == "CORE_AT_003"
                and not minion.silenced
                and minion.dormant_turns == 0
                and minion.health > 0
                for minion in player.board
            )
            self._deal_to_target(
                player.index,
                (action.target_player, action.target_entity),
                1 + bonus,
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
        self._dispatch_after_hero_power(player)
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

    def _dispatch_after_hero_power(self, player: Player) -> None:
        """Run friendly minion triggers after a fully resolved Hero Power."""
        for minion in list(player.board):
            if (
                minion not in player.board
                or minion.silenced
                or minion.dormant_turns > 0
                or minion.health <= 0
            ):
                continue
            self.rule_registry.dispatch(
                Hook.AFTER_HERO_POWER, minion.card_id, self,
                RuleContext(player=player, card=minion),
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

    def _hero_elusive(self, player_index: int) -> bool:
        """Return whether a live, unsilenced aura protects this hero."""
        return any(
            minion.card_id == "EDR_846t3"
            and not minion.silenced
            and minion.dormant_turns == 0
            and minion.health > 0
            for minion in self.players[player_index].board
        )

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
        enemy_hero = [] if (
            card.definition.card_type == "SPELL" and self._hero_elusive(enemy.index)
        ) else [(enemy.index, None)]
        if target_kind == TargetKind.FRIENDLY_MINION:
            return friendly_minions
        if target_kind == TargetKind.FRIENDLY_HAND_MINION:
            return [
                (player.index, card.entity_id)
                for card in player.hand
                if card.definition.card_type == "MINION"
            ]
        if target_kind == TargetKind.FRIENDLY_DRAGON:
            return [
                (player.index, minion.entity_id)
                for minion in player.board
                if minion.dormant_turns == 0 and minion.has_race("DRAGON")
            ]
        if target_kind == TargetKind.FRIENDLY_MINION_OR_HAND:
            return [
                (player.index, minion.entity_id)
                for minion in player.board
                if minion.dormant_turns == 0
            ] + [
                (player.index, card.entity_id)
                for card in player.hand
                if card.definition.card_type == "MINION"
            ]
        if target_kind == TargetKind.FRIENDLY_UNDEAD:
            return [
                (player.index, minion.entity_id)
                for minion in player.board
                if minion.dormant_turns == 0 and minion.has_race("UNDEAD")
            ]
        if target_kind == TargetKind.ENEMY_MINION:
            return enemy_minions
        if target_kind == TargetKind.DAMAGED_MINION:
            return [
                (owner.index, minion.entity_id)
                for owner in self.players
                for minion in owner.board
                if minion.dormant_turns == 0
                and minion.damage > 0
                and not minion.stealth
                and not (
                    card.definition.card_type == "SPELL" and minion.elusive
                )
            ]
        if target_kind == TargetKind.ANY_MINION:
            return friendly_minions + enemy_minions
        if target_kind == TargetKind.FRIENDLY_CHARACTER:
            return [(player.index, None)] + friendly_minions
        if target_kind == TargetKind.ENEMY_CHARACTER:
            return enemy_hero + enemy_minions
        if target_kind == TargetKind.ANY_CHARACTER:
            return (
                [(player.index, None)] + friendly_minions
                + enemy_hero + enemy_minions
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
            if self.pending_choice["kind"] == "HAND_DISCARD":
                return [
                    Action("DISCARD_PICK", card.entity_id)
                    for card in self.pending_choice["options"]
                ]
            if self.pending_choice["kind"] in {
                "DISCOVER", "GEDDON_DRAW", "DECK_DISCOVER", "DECK_CARD_DISCOVER",
                "IMBUE_PICK", "INTERTWINED_FATE", "INTERTWINED_FATE_OPPONENT",
                "SKELETON_KEY",
            }:
                actions = [
                    Action("DISCOVER_PICK", option.entity_id)
                    for option in self.pending_choice["options"]
                ]
                if self.pending_choice["kind"] == "SKELETON_KEY":
                    actions.append(Action("RULE_CHOICE_PICK", -1))
                return actions
            if self.pending_choice["kind"] == "ASHALON_ADAPT":
                return [
                    Action("RULE_CHOICE_PICK", index)
                    for index in range(len(self.pending_choice["options"]))
                ]
            if self.pending_choice["kind"] == "EARTHEN_ROAR_PICK":
                return [Action("EARTHEN_ROAR_PICK", option.entity_id) for option in self.pending_choice["options"]]
            if self.pending_choice["kind"] == "REWIND":
                return [Action("REWIND_KEEP"), Action("REWIND_RETRY")]
            if self.pending_choice["kind"] == "REWIND_DISCOVER":
                return [
                    *(Action("DISCOVER_PICK", option.entity_id)
                      for option in self.pending_choice["options"]),
                    Action("REWIND_RETRY"),
                ]
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
            if self.pending_choice["kind"] == "DEATHWING_CATACLYSM":
                return [
                    Action("CATACLYSM_PICK", index)
                    for index in range(len(self.pending_choice["options"]))
                ]
        player = self.players[self.current]
        self._refresh_genn(player)
        for candidate in self.players:
            self._refresh_continuous(candidate)
        actions = [Action("END_TURN")]
        for card in player.hand:
            if ("Prepare" in card.definition.text or card.prepare_granted) and not card.prepared:
                actions.append(Action("PREPARE", card.entity_id))
            if card.prepared_turn == self.turn:
                continue
            if self.turn <= card.playable_after_turn:
                continue
            if card.locked_until_card_played:
                continue
            if card.card_id == "TLC_446t" and player.underfel_rift_used_turn == self.turn:
                continue
            effective_cost = self._effective_cost(player, card)
            if card.card_id == "TLC_436":
                if effective_cost > player.corpses:
                    continue
            elif card.costs_health_expiry_turn == self.turn:
                # Health costs cannot reduce the hero to zero.
                if effective_cost >= player.health:
                    continue
            elif effective_cost > player.mana:
                continue
            if (
                card.definition.card_type in {"MINION", "LOCATION"}
                and len(player.board) + len(player.locations) >= 7
                and card.card_id not in PLAYABLE_ON_EITHER_SIDE_IDS
            ):
                continue
            targets: list[tuple[int, int | None]] | None = None
            target_spec = self.rule_registry.targeting(card.card_id)
            if target_spec is not None:
                targets = self._rule_targets(player, card, target_spec.kind)
                if card.card_id == "CORE_EX1_005":
                    targets = [
                        target for target in targets
                        if self._find_minion(*target).attack >= 7
                    ]
                if target_spec.optional:
                    targets = [(None, None), *targets]
            elif card.card_id == "CORE_REV_023":
                targets = [
                    (1 - self.current, location.entity_id)
                    for location in self.players[1 - self.current].locations
                    if location.durability > 0
                ]
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
            elif card.card_id in PLAYABLE_ON_EITHER_SIDE_IDS:
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
        hero_power_ready = (
            player.corpses >= 3
            if player.hero_power_id == "JAIL_446hp"
            else player.mana >= self._hero_power_cost(player)
        )
        if hero_power_ready and not player.hero_power_used:
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
                elif location.card_id in {"CATA_584", "FIR_907"}:
                    actions.append(Action("LOCATION", location.entity_id))
                elif location.card_id == "TLC_433t2":
                    # Terror's Grave is a targeted location: deal 4 damage to
                    # an enemy character, then its durability is consumed.
                    actions.extend(
                        Action("LOCATION", location.entity_id, p, e)
                        for p, e in self._enemy_characters(player.index)
                    )
                elif location.custom_effects:
                    actions.append(Action("LOCATION", location.entity_id))
                elif self.rule_registry.has_hook(Hook.LOCATION, location.card_id):
                    target_spec = self.rule_registry.targeting(location.card_id)
                    if target_spec is None:
                        actions.append(Action("LOCATION", location.entity_id))
                    else:
                        location_card = CardInstance(
                            location.entity_id, self.card_defs[location.card_id]
                        )
                        targets = self._rule_targets(player, location_card, target_spec.kind)
                        if target_spec.optional:
                            targets = [(None, None), *targets]
                        actions.extend(
                            Action("LOCATION", location.entity_id, p, e)
                            for p, e in targets
                        )
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
            if self.pending_choice and self.pending_choice["kind"] == "REWIND_DISCOVER":
                self._resolve_rewind_discover(action)
            else:
                self._resolve_discover(action.source)
        elif action.kind == "EARTHEN_ROAR_PICK":
            self._resolve_earthen_roar_pick(action.source)
        elif action.kind == "REWIND_KEEP":
            self._resolve_rewind(False)
        elif action.kind == "REWIND_RETRY":
            if self.pending_choice and self.pending_choice["kind"] == "REWIND_DISCOVER":
                self._resolve_rewind_discover(action)
            else:
                self._resolve_rewind(True)
        elif action.kind == "AMMUNITION_PICK":
            self._resolve_ammunition(action.source)
        elif action.kind == "CORPSE_SPEND":
            self._resolve_corpse_spend(action.source)
        elif action.kind == "RULE_CHOICE_PICK":
            if (
                self.pending_choice
                and self.pending_choice.get("kind") == "SKELETON_KEY"
                and action.source == -1
            ):
                self._refresh_skeleton_key()
            else:
                self._resolve_rule_choice(action.source)
        elif action.kind == "CATACLYSM_PICK":
            self._resolve_deathwing_cataclysm(action.source)
        elif action.kind == "DISCARD_PICK":
            self._resolve_hand_discard(action.source)
        for owner in self.players:
            self._normalize_shattered_hand(owner)
        self._resolve_deaths()
        self._check_winner()

    def _resolve_hand_discard(self, entity_id: int | None) -> None:
        pending = self.pending_choice
        if pending is None or pending.get("kind") != "HAND_DISCARD":
            raise ValueError("no hand discard is pending")
        player = self.players[pending["player"]]
        card = next((item for item in player.hand if item.entity_id == entity_id), None)
        if card is None:
            raise ValueError("invalid discard choice")
        player.hand.remove(card)
        if pending.get("mode") == "shuffle_hand_card":
            card.started_in_deck = False
            card.created_by = pending["source"]
            player.deck.insert(self.rng.randrange(len(player.deck) + 1), card)
            self.pending_choice = None
            self._draw(player)
            self._event(
                "sheltered_survivor_shuffle", player=player.index,
                source=pending["source"], card=card.card_id,
            )
            return
        player.zuramat_discarded_card = card
        self.pending_choice = None
        if len(player.board) + len(player.locations) < 7:
            token = self._entity("JAIL_887t3", created_by=pending["source"])
            token.taunt = True
            token.summoned_turn = self.turn
            self._summon(player, token)
        self._event(
            "zuramat_prison_discard", player=player.index,
            source=pending["source"], discarded=card.card_id,
        )
        self._dispatch_after_discard(player, card)

    def _resolve_rule_choice(self, option_index: int | None) -> None:
        pending = self.pending_choice
        if pending is None or pending["kind"] not in {"RULE_CHOICE", "ASHALON_ADAPT"}:
            raise ValueError("no rule choice is pending")
        if option_index is None or not 0 <= option_index < len(pending["options"]):
            raise ValueError("invalid rule choice")
        player = self.players[pending["player"]]
        if pending.get("stage") == "ELISE_COST":
            cost = pending["costs"][option_index]
            effect_ids = (
                "bursting_geyser", "shining_moonlight", "runic_inscriptions",
                "snapping_plants", "nesting_grounds", "lava_stream",
                "radiant_crystals",
            )
            if cost == 1:
                effect_ids = tuple(
                    effect for effect in effect_ids
                    if effect != "radiant_crystals"
                )
            self.pending_choice = {
                "kind": "RULE_CHOICE", "stage": "ELISE_EFFECTS",
                "player": player.index, "card": pending["card"],
                "action": pending.get("action"), "cost": cost,
                "selected_effects": [],
                "options": tuple(
                    (effect.replace("_", " ").title(), ())
                    for effect in effect_ids
                ),
            }
            self._event(
                "elise_location_cost_pick", player=player.index,
                source=pending["card"].card_id, cost=cost,
            )
            return
        if pending.get("stage") == "ELISE_EFFECTS":
            selected = list(pending["selected_effects"])
            effect_id = pending["options"][option_index][0].lower().replace(" ", "_")
            selected.append(effect_id)
            if len(selected) < 2:
                self.pending_choice = {
                    **pending,
                    "selected_effects": selected,
                    "options": tuple(
                        option for option in pending["options"]
                        if option[0].lower().replace(" ", "_") not in selected
                    ),
                }
                self._event(
                    "elise_location_effect_pick", player=player.index,
                    source=pending["card"].card_id, effect=effect_id,
                    remaining=1,
                )
                return
            location_id = {
                1: "TLC_100t1", 5: "TLC_100t2", 10: "TLC_100t3",
            }[pending["cost"]]
            location = Location(
                self.next_entity_id, location_id, 2,
                custom_effects=tuple(selected), custom_tier=pending["cost"],
            )
            self.next_entity_id += 1
            player.locations.append(location)
            self.pending_choice = None
            self._event(
                "elise_location_created", player=player.index,
                source=pending["card"].card_id, location=location_id,
                cost=pending["cost"], effects=selected,
            )
            return
        self.pending_choice = None
        if pending["kind"] == "ASHALON_ADAPT":
            adaptation = pending["options"][option_index]
            player.ashalon_adaptations.append(adaptation)
            self._event(
                "ashalon_adaptation_pick", player=player.index,
                adaptation=adaptation, picks=len(player.ashalon_adaptations),
            )
            if pending["remaining"] > 1:
                self._offer_ashalon_adapt(player, remaining=pending["remaining"] - 1)
            return
        label, effects = pending["options"][option_index]
        card = pending["card"]
        context = RuleContext(
            player=player, card=card, action=pending.get("action")
        )
        for effect in effects:
            effect.execute(self, context)
        self._event(
            "rule_choice_pick", player=player.index, card=card.card_id,
            option=label,
        )

    def _play_hero_card(self, player: Player, card: CardInstance) -> None:
        """Resolve hero transformation cards that have engine-level choices.

        A Hero card replaces the hero power and adds its printed Armor; it does
        not heal the player.  Deathwing's Cataclysms are selected one at a time
        from the four different modes, so a later choice sees the board/deck
        mutations made by the earlier one.
        """
        player.max_health = card.definition.health or player.max_health
        player.health = min(player.health, player.max_health)
        player.armor += card.definition.armor
        if card.card_id == "CATA_190h":
            player.hero_power_id = "CATA_190p"
            choices = self._herald_power(player.herald_count)
            self.pending_choice = {
                "kind": "DEATHWING_CATACLYSM",
                "player": player.index,
                "card": card,
                "remaining": choices,
                "options": [
                    "CATA_190t10", "CATA_190t11", "CATA_190t12", "CATA_190t13",
                ],
                "chosen": [],
            }
            self._event(
                "deathwing_transform", player=player.index, card=card.card_id,
                armor=card.definition.armor, cataclysms=choices,
            )
        elif card.card_id == "CORE_EX1_323":
            player.hero_power_id = "EX1_tk33"
            self._equip_weapon(
                player,
                Weapon("EX1_323w", "Blood Fury", 3, 8),
            )
            self._event(
                "jaraxxus_transform", player=player.index,
                armor=card.definition.armor, hero_power="EX1_tk33",
            )
        elif card.card_id == "TLC_513t":
            player.ninja_shuffle_active = True
            for _ in range(2):
                if len(player.board) + len(player.locations) >= 7:
                    break
                ninja = self._entity("TLC_513t2", created_by=card.card_id)
                ninja.summoned_turn = self.turn
                self._summon(player, ninja)
            self._event("master_dusk_battlecry", player=player.index, ninjas=2)
        else:
            self._event("hero_transform", player=player.index, card=card.card_id)

    def _resolve_deathwing_cataclysm(self, option_index: int | None) -> None:
        pending = self.pending_choice
        if pending is None or pending["kind"] != "DEATHWING_CATACLYSM":
            raise ValueError("no Deathwing Cataclysm is pending")
        options = pending["options"]
        if option_index is None or not 0 <= option_index < len(options):
            raise ValueError("invalid Deathwing Cataclysm")
        card_id = options.pop(option_index)
        player = self.players[pending["player"]]
        pending["chosen"].append(card_id)
        self._unleash_deathwing_cataclysm(player, card_id)
        pending["remaining"] -= 1
        self._event(
            "deathwing_cataclysm", player=player.index, card=card_id,
            remaining=pending["remaining"], choices=list(pending["chosen"]),
        )
        # The official Herald text says 1 / 2 / 4 Cataclysms, while there are
        # exactly four modes.  Remove a chosen mode, rather than allowing the
        # same Cataclysm to be picked twice in one transformation.
        if pending["remaining"] > 0 and options:
            return
        self.pending_choice = None

    def _unleash_deathwing_cataclysm(self, player: Player, card_id: str) -> None:
        enemy = self.players[1 - player.index]
        if card_id == "CATA_190t10":
            if len(player.board) + len(player.locations) < 7:
                minion = self._entity(card_id="CATA_190t14", created_by=card_id)
                minion.summoned_turn = self.turn
                self._summon(player, minion)
            return
        if card_id == "CATA_190t11":
            candidates = self._random_enemy_minions(player.index)
            if candidates:
                highest_health = max(minion.health for minion in candidates)
                target = self.rng.choice([
                    minion for minion in candidates
                    if minion.health == highest_health
                ])
                target.damage = max(target.damage, target.max_health)
                self._event(
                    "deathwing_topple", player=player.index,
                    target_player=enemy.index, target=target.entity_id,
                )
            return
        if card_id == "CATA_190t12":
            for minion in list(enemy.board):
                if minion.dormant_turns == 0:
                    # Raze specifies a fixed 4; it is not modified by the
                    # controller's spell damage.
                    self._damage_minion(enemy.index, minion, 4)
            return
        if card_id == "CATA_190t13":
            pool = self._executable_legendary_dragons()
            for _ in range(5):
                if not pool:
                    break
                generated = self._entity(self.rng.choice(pool), created_by=card_id)
                generated.cost_delta = 1 - generated.definition.cost
                generated.started_in_deck = False
                player.deck.insert(self.rng.randrange(len(player.deck) + 1), generated)
                self._event(
                    "deathwing_enthrall", player=player.index,
                    card=generated.card_id, entity=generated.entity_id,
                    cost=generated.cost,
                )
            return
        raise UnsupportedGeneratedCard(f"Deathwing Cataclysm {card_id}")

    def _executable_legendary_dragons(self) -> list[str]:
        """Return the closed, playable subset of Standard Legendary Dragons.

        The live game can generate from the complete Standard pool.  This
        simulator deliberately excludes cards without executable behavior;
        keeping that boundary explicit prevents an unsupported card silently
        becoming a vanilla minion when it is later drawn and played.
        """
        return sorted(
            card_id for card_id, definition in self.card_defs.items()
            if card_id in EXECUTABLE_CARD_IDS
            and definition.card_type == "MINION"
            and definition.rarity == "LEGENDARY"
            and (definition.race == "DRAGON" or "DRAGON" in definition.races)
        )

    def _prepare(self, entity_id: int | None) -> None:
        player = self.players[self.current]
        card = next(card for card in player.hand if card.entity_id == entity_id)
        if card.prepared:
            raise ValueError("card can only be prepared once")
        spent = player.mana
        player.mana = 0
        card.cost_delta -= spent + 1
        card.prepared_turn = self.turn
        card.prepared = True
        jailbirds = [
            held for held in player.hand
            if held.card_id == "JAIL_453" and held.entity_id != card.entity_id
        ]
        for jailbird in jailbirds:
            jailbird.cost_delta -= spent + 1
            self._event(
                "prepare_jailbird_discount", player=player.index,
                source=card.card_id, entity=jailbird.entity_id,
                discount=spent + 1,
            )
        self._event(
            "prepare", player=player.index, card=card.card_id,
            entity=card.entity_id, spent=spent, discount=spent + 1,
        )

    def _pop_hand(self, player: Player, entity_id: int) -> CardInstance:
        for i, card in enumerate(player.hand):
            if card.entity_id == entity_id:
                popped = player.hand.pop(i)
                self._restore_overdrawn_cards(player)
                return popped
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
        held_index = next(
            index for index, card in enumerate(player.hand)
            if card.entity_id == action.source
        )
        held = player.hand[held_index]
        held.outcast_active = held_index in {0, len(player.hand) - 1}
        effective_cost = self._effective_cost(player, held)
        if (
            held.definition.card_type == "MINION"
            and player.mug_magic_active
            and self.turn >= 3
            and not player.mug_magic_used_this_turn
        ):
            player.mug_magic_used_this_turn = True
        if held.definition.card_type == "MINION" and player.zee_might_active:
            player.zee_might_minions_played += 1
            held.battlecry_twice = player.zee_might_minions_played % 5 == 0
        card = self._pop_hand(player, action.source)
        for held_card in player.hand:
            if held_card.locked_until_card_played:
                held_card.locked_until_card_played = False
        watcher = self.players[1 - player.index]
        if (
            watcher.holmes_target_card_id == card.card_id
            and watcher.holmes_watch_turn == self.turn
        ):
            for _ in range(3):
                self._give_coin(watcher, source="JAIL_851")
            self._event(
                "holmes_match", player=watcher.index,
                source="JAIL_851", matched=card.card_id,
                coins=3,
            )
            watcher.holmes_target_card_id = None
            watcher.holmes_watch_turn = -1
        # "While holding this" uses the card's displayed Cost.  Capture it
        # before resolving play effects that could mutate the remaining hand.
        for other in player.hand:
            if card.cost > other.cost:
                other.higher_cost_card_played_while_held = True
        if card.card_id == "TLC_436":
            player.corpses -= effective_cost
            self._event(
                "spend_corpses", player=player.index,
                card=card.card_id, amount=effective_cost,
            )
        elif card.costs_health_expiry_turn == self.turn:
            self._damage_hero(player, effective_cost, card)
            self._event(
                "health_cost_paid", player=player.index,
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
        if card.has_race("BEAST") and player.next_beast_cost_reduction:
            player.next_beast_cost_reduction = 0
        if card.has_race("MURLOC") and player.next_murloc_cost_reduction:
            player.next_murloc_cost_reduction = 0
        if card.has_race("DEMON") and player.next_demon_cost_reduction:
            player.next_demon_cost_reduction = 0
        if (
            player.next_combo_cost_reduction
            and player.cards_played_this_turn > 0
            and "combo" in card.definition.text.casefold()
        ):
            player.next_combo_cost_reduction = 0
        if card.definition.card_type == "MINION" and player.next_minion_cost_reduction:
            player.next_minion_cost_reduction = 0
        if card.definition.card_type == "SPELL" and player.next_spell_cost_reduction:
            player.next_spell_cost_reduction = 0
        controller = (
            self.players[action.target_player]
            if card.card_id in PLAYABLE_ON_EITHER_SIDE_IDS
            and action.target_player is not None
            else player
        )
        self._event(
            "play", player=player.index, card=card.card_id,
            controller=controller.index, entity=card.entity_id,
            started_in_deck=card.started_in_deck,
            created_by=card.created_by,
        )
        player.cards_played_this_turn += 1
        if card.definition.card_type == "SPELL":
            player.spells_cast_this_turn += 1
        player.played_card_counts[card.card_id] = player.played_card_counts.get(card.card_id, 0) + 1
        if card.card_id != "JAIL_407":
            vanessas = [
                minion for minion in player.board
                if minion.card_id == "JAIL_407"
                and minion.prepared
                and not minion.silenced
                and minion.dormant_turns == 0
                and minion.health > 0
            ]
            for vanessa in vanessas:
                candidates = [
                    card_id for card_id in self.executable_card_ids
                    if card_id in self.card_defs
                    and self.card_defs[card_id].card_type == "MINION"
                    and "BATTLECRY" in self.card_defs[card_id].mechanics
                ]
                if candidates:
                    generated = self._entity(
                        self.rng.choice(sorted(candidates)),
                        created_by=vanessa.card_id,
                    )
                    generated.cost_delta -= 2
                    self._add_generated(player, generated)
                    self._event(
                        "vanessa_battlecry_minion", player=player.index,
                        source=vanessa.entity_id, card=generated.card_id,
                        discount=2,
                    )
        if card.definition.card_type == "SPELL":
            auctioneers = [
                minion for minion in player.board
                if minion.card_id == "JAIL_718"
                and minion.prepared
                and not minion.silenced
                and minion.dormant_turns == 0
                and minion.health > 0
            ]
            for auctioneer in auctioneers:
                self._draw(player)
                self._event(
                    "black_market_auctioneer_draw", player=player.index,
                    source=auctioneer.entity_id, spell=card.card_id,
                )
        if getattr(player, "rafaam_next_discount", False) and "rafaam" in card.definition.name.casefold():
            player.rafaam_next_discount = False
            self._event("rafaam_discount_consumed", player=player.index, card=card.card_id)
        card.combo_active = player.cards_played_this_turn > 1
        if card.card_id == "JAIL_909" and card.combo_active:
            amount = player.cards_played_this_turn - 1
            card.attack_delta += amount
            card.health_delta += amount
            self._event(
                "defias_wannabe_combo", player=player.index,
                source=card.entity_id, amount=amount,
            )
        if not card.started_in_deck:
            player.generated_cards_played += 1
        if card.card_id in LOST_CITY_QUEST_IDS:
            self._activate_lost_city_quest(player, card)
            return
        if card.copied_from_opponent:
            for held in player.hand:
                held.opponent_card_copy_played_while_held = True
            self._event(
                "opponent_card_copy_played", player=player.index,
                card=card.card_id, entity=card.entity_id,
            )
        if card.definition.card_type == "MINION":
            player.minion_played_this_turn = True
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
            if controller.ashalon_adaptations and card.card_id != "TLC_229t14":
                self._apply_ashalon_adaptations(controller, card)
            if card.card_id == "TLC_107" and self._kindred_repeats(controller, card):
                card.rush = True
            if card.card_id == "DINO_435" and self._kindred_repeats(controller, card):
                if len(controller.board) + len(controller.locations) < 7:
                    copy = card.clone(self.next_entity_id)
                    self.next_entity_id += 1
                    copy.damage = 0
                    copy.summoned_turn = self.turn
                    copy.created_by = card.card_id
                    self._summon(controller, copy)
                    self._event("crater_experiment_kindred", player=controller.index,
                                source=card.entity_id, copy=copy.entity_id)
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
            player.played_races_this_game.update(card.definition.races)
            if card.definition.race:
                player.played_races_this_turn.add(card.definition.race)
                player.played_races_this_game.add(card.definition.race)
            if card.has_race("DRAGON"):
                player.dragons_played_this_turn += 1
            if card.card_id == "CATA_150":
                self._summon_ragnaros_hands(controller, source=card.card_id)
            if card.card_id == "CATA_550":
                controller.pending_magmaw_bodies += 99
                controller.magmaw_entity = card.entity_id
                self._summon_magmaw_bodies(controller)
            self._battlecry(controller, card, action)
            self._trigger_imbue_passive(controller, card)
            if card in controller.board:
                self._trigger_secrets_after_enemy_minion_play(controller, card)
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
            player.locations.append(Location(card.entity_id, card.card_id, card.definition.health, 2))
        elif card.definition.card_type == "WEAPON":
            durability = (
                card.definition.health
                if card.card_id == "TLC_460t"
                else getattr(card.definition, "durability", 0)
                or card.definition.health or 2
            )
            self._equip_weapon(
                player,
                Weapon(card.card_id, card.definition.name, card.definition.attack, durability),
            )
            self._battlecry(player, card, action)
        elif card.definition.card_type == "HERO":
            self._play_hero_card(player, card)
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
            malygos_active = (
                card.definition.spell_school == "ARCANE"
                and any(m.card_id == "TIME_852t1" and not m.silenced and m.dormant_turns == 0
                        for m in player.board)
                and any(m.has_race("DRAGON") and m.card_id != "TIME_852t1"
                        and not m.silenced and m.dormant_turns == 0 for m in player.board)
            )
            sinestra_active = any(
                m.card_id == "CATA_154"
                and not m.silenced and m.dormant_turns == 0
                and card.definition.card_class not in {"", "NEUTRAL", player.card_class}
                for m in player.board
            )
            if (card.spell_casts_twice or malygos_active or sinestra_active) and self.pending_choice is None:
                self._cast_spell(player, card, action)
            if player.hamuul_active:
                player.hamuul_spells_cast += 1
                if player.hamuul_spells_cast % 3 == 0:
                    power_id = imbue_hero_power_id(player.card_class)
                    if power_id in self.card_defs:
                        player.hero_power_id = power_id
                        player.imbued_hero_power_id = power_id
                        player.hero_power_imbues += 1
                        self._event(
                            "hero_power_imbued", player=player.index,
                            source="EDR_845", hero_power=power_id,
                            count=player.hero_power_imbues,
                        )
                    self._event(
                        "hamuul_spell_threshold", player=player.index,
                        spells=player.hamuul_spells_cast,
                    )
            self._dispatch_after_spell_cast(
                player, card, action, paid_cost=effective_cost
            )
            self._trigger_secrets_after_enemy_spell_cast(player)
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
            if card.card_id == "TIME_042t" and len(player.hand) < 10:
                banana = self._entity("TIME_042t", created_by="TIME_042t")
                player.hand.append(banana)
                self._event(
                    "infinite_banana_returned", player=player.index,
                    entity=banana.entity_id,
                )
        if (
            player.map_followup_entity == card.entity_id
            and player.map_followup_turn == self.turn
            and player.map_followup_options
            and self.pending_choice is None
        ):
            options = list(player.map_followup_options)
            player.map_followup_options.clear()
            player.map_followup_entity = None
            player.map_followup_turn = -1
            self._offer_discover(player, options, dark_gift=False, source_card_id=card.card_id)
            self._event("map_followup_offer", player=player.index,
                        source=card.card_id, options=options)
        if card.definition.card_set == "TIME_TRAVEL":
            self._accelerate_timelords(
                player,
                exclude_entity=card.entity_id if card.card_id == "TIME_063" else None,
            )

    def _trigger_imbue_passive(self, player: Player, card: CardInstance) -> None:
        """Resolve passive Imbue effects after a minion's Battlecry."""
        if (
            card.definition.card_type != "MINION"
            or not card.has_race("UNDEAD")
            or player.hero_power_id != "END_003p"
            or player.imbue_passive_triggered_this_turn
        ):
            return
        player.imbue_passive_triggered_this_turn = True
        # Blessing of the Infinite grants attack only in the pinned print.
        card.attack_delta += 1
        self._event(
            "imbue_first_undead", player=player.index,
            card=card.card_id, entity=card.entity_id, attack=1,
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
        if card.card_id == "CORE_RLK_706":
            player.mograine_active = True
            self._event(
                "mograine_active", player=player.index,
                source=card.entity_id, damage=3,
            )
            return
        if card.card_id == "END_017t":
            # Tick and Tock draws only while there is room in hand.  If the
            # deck is empty, stop rather than repeatedly applying fatigue.
            while len(player.hand) < 10 and player.deck:
                self._draw(player)
            self._event(
                "tick_and_tock_battlecry", player=player.index,
                source=card.entity_id, hand_size=len(player.hand),
            )
            return
        if card.card_id == "TLC_987":
            if player.active_quests or player.completed_quests:
                targets = self._random_enemy_minions(player.index)
                if targets:
                    target = self.rng.choice(targets)
                    target_ref = (1 - player.index, target.entity_id)
                    self._deal_to_target(player.index, target_ref, 3, source=card)
                    self._event(
                        "questing_assistant_battlecry", player=player.index,
                        source=card.entity_id, target=target.entity_id, damage=3,
                    )
            return
        if card.card_id == "JAIL_452":
            # Overload belongs to the side that received the minion.  This is
            # observable when the Detective is deliberately played onto the
            # opponent's board.
            player.overload_next_turn += 2
            self._event(
                "rulebreaker_overload", player=player.index,
                source=card.card_id, amount=2,
            )
            return
        if card.card_id == "CATA_721":
            if player.hand:
                self.pending_choice = {
                    "kind": "HAND_DISCARD", "mode": "shuffle_hand_card",
                    "player": player.index, "source": card.card_id,
                    "options": tuple(player.hand),
                }
                self._event(
                    "sheltered_survivor_offer", player=player.index,
                    source=card.entity_id,
                    options=[held.card_id for held in player.hand],
                )
            else:
                self._draw(player)
            return
        if card.card_id == "JAIL_461":
            if card in player.board:
                index = player.board.index(card)
                adjacent = [
                    minion for minion in (
                        player.board[max(0, index - 1):index]
                        + player.board[index + 1:index + 2]
                    )
                    if minion.dormant_turns == 0
                ]
                if adjacent:
                    target = self.rng.choice(adjacent)
                    target.damage = target.max_health
                    self._event(
                        "rulebreaker_adjacent_destroy", player=player.index,
                        source=card.card_id, target=target.entity_id,
                    )
                    self._resolve_deaths()
            return
        if card.card_id == "TLC_229t14":
            self._offer_ashalon_adapt(player, remaining=2)
            return
        if card.card_id == "TLC_817t5":
            if len(player.board) + len(player.locations) < 7:
                copy_card = card.clone(self.next_entity_id)
                self.next_entity_id += 1
                copy_card.created_by = card.card_id
                copy_card.summoned_turn = self.turn
                self._summon(player, copy_card)
            return
        if card.card_id == "TLC_631t":
            player.gorishi_double_damage = True
            self._event("gorishi_colossus_active", player=player.index,
                        source=card.card_id)
            return

        if card.card_id == "TLC_830t":
            pool = [
                card_id for card_id, definition in self.card_defs.items()
                if card_id in EXECUTABLE_CARD_IDS
                and definition.card_type == "MINION"
                and "BEAST" in definition.races
                and definition.attack in {4, 6, 8}
            ]
            self._offer_discover(
                player, pool, dark_gift=False, source_card_id=card.card_id,
            )
            if self.pending_choice is not None:
                for option in self.pending_choice["options"]:
                    option.cost_delta = 2 - option.definition.cost
            return
        if card.card_id == "TLC_602t":
            reward_pool = [
                "UNG_028t", "UNG_067t1", "UNG_116t", "UNG_829t1",
                "UNG_920t1", "UNG_934t1", "UNG_940t8", "UNG_942t", "UNG_954t1",
            ]
            reward_pool = [reward_id for reward_id in reward_pool if reward_id in self.card_defs]
            self.rng.shuffle(reward_pool)
            chosen, remainder = reward_pool[:2], reward_pool[2:]
            for reward_id in chosen:
                self._add_generated(player, self._entity(reward_id, created_by=card.card_id))
            for reward_id in remainder:
                player.deck.insert(self.rng.randrange(len(player.deck) + 1),
                                   self._entity(reward_id, started_in_deck=True,
                                                created_by=card.card_id))
            self._event("latorvius_quest_rewards", player=player.index,
                        chosen=chosen, shuffled=remainder)
            return
        if card.card_id == "CORE_LOE_079":
            # Elise's map is a real deck card and is shuffled immediately;
            # this is intentionally not a hand generation shortcut.
            map_card = self._entity("LOE_019t", created_by=card.card_id)
            player.deck.insert(self.rng.randrange(len(player.deck) + 1), map_card)
            self._event(
                "elise_map_shuffled", player=player.index,
                source=card.card_id, card=map_card.card_id,
                entity=map_card.entity_id,
            )
            return
        if card.card_id == "LOE_019t2":
            # Golden Monkey preserves zone sizes while replacing each card
            # with a random executable Legendary minion.  The played Monkey
            # itself remains on board and is therefore not reinserted.
            pool = [
                card_id for card_id, definition in self.card_defs.items()
                if card_id in EXECUTABLE_CARD_IDS
                and definition.card_type == "MINION"
                and definition.rarity == "LEGENDARY"
                and card_id != "LOE_019t2"
            ]
            if pool:
                hand_count, deck_count = len(player.hand), len(player.deck)
                player.hand = [
                    self._entity(self.rng.choice(pool), created_by=card.card_id)
                    for _ in range(hand_count)
                ]
                player.deck = [
                    self._entity(self.rng.choice(pool), started_in_deck=True,
                                 created_by=card.card_id)
                    for _ in range(deck_count)
                ]
                self._event(
                    "golden_monkey_replace", player=player.index,
                    source=card.card_id, hand_count=hand_count,
                    deck_count=deck_count, pool_size=len(pool),
                )
            return
        if card.card_id == "JAIL_446":
            player.hero_power_id = "JAIL_446hp"
            self._event(
                "rulebreaker_hero_power", player=player.index,
                source=card.card_id, hero_power="JAIL_446hp",
            )
            return
        if card.card_id == "TLC_100":
            started_costs = {
                held.definition.cost for held in player.deck
                if held.started_in_deck
            }
            if len(started_costs) >= 10 and len(player.locations) < 7:
                self.pending_choice = {
                    "kind": "RULE_CHOICE", "stage": "ELISE_COST",
                    "player": player.index, "card": card, "action": action,
                    "costs": (1, 5, 10),
                    "options": tuple(
                        (f"Craft {cost} Mana Location", ())
                        for cost in (1, 5, 10)
                    ),
                }
                self._event(
                    "elise_location_cost_offer", player=player.index,
                    source=card.card_id, costs=[1, 5, 10],
                )
            return
        if card.card_id == "MEND_046":
            nature_by_cost: dict[int, list[str]] = {}
            for card_id, definition in self.card_defs.items():
                if (
                    card_id in EXECUTABLE_CARD_IDS
                    and definition.card_type == "SPELL"
                    and definition.spell_school == "NATURE"
                    and 0 <= definition.cost <= 10
                ):
                    nature_by_cost.setdefault(definition.cost, []).append(card_id)
            costs = sorted(nature_by_cost)
            cost_triples = [
                (a, b, c)
                for a in costs for b in costs if b >= a
                for c in costs if c >= b and a + b + c == 12
            ]
            exact = bool(cost_triples)
            if not cost_triples:
                fallback = [
                    (a, b, c)
                    for a in costs for b in costs if b >= a
                    for c in costs if c >= b and a + b + c <= 12
                ]
                if fallback:
                    best_total = max(sum(item) for item in fallback)
                    cost_triples = [
                        item for item in fallback if sum(item) == best_total
                    ]
            chosen = None
            if cost_triples:
                chosen_costs = self.rng.choice(cost_triples)
                chosen = tuple(
                    self.rng.choice(nature_by_cost[cost])
                    for cost in chosen_costs
                )
            for index in range(3):
                if len(player.board) + len(player.locations) >= 7:
                    break
                token = self._entity("MEND_046t", created_by=card.card_id)
                token.embedded_spell_id = chosen[index] if chosen else None
                token.summoned_turn = self.turn
                self._summon(player, token)
            self._event(
                "bashana_runetotem", player=player.index,
                source=card.card_id,
                spells=list(chosen) if chosen else [],
                total_cost=(
                    sum(self.card_defs[spell_id].cost for spell_id in chosen)
                    if chosen else 0
                ),
                exact_total=exact,
            )
            return
        if card.card_id == "MEND_046t" and card.embedded_spell_id:
            spell = self._entity(card.embedded_spell_id, created_by=card.card_id)
            try:
                self._cast_spell(player, spell, Action("PLAY", spell.entity_id))
            except ValueError:
                for target_player, target_entity, _ in self._random_spell_target_candidates(
                    player.index, spell
                ):
                    try:
                        self._cast_spell(
                            player, spell,
                            Action("PLAY", spell.entity_id, target_player, target_entity),
                        )
                        break
                    except ValueError:
                        continue
            self._event(
                "bashana_treant_cast", player=player.index,
                source=card.entity_id, spell=spell.card_id,
            )
            return
        if card.card_id == "JAIL_851":
            opponent = self.players[1 - player.index]
            if opponent.hand:
                # Holmes is an explicit guess, not a random inspection.  Keep
                # one option per hand entity so duplicate cards remain
                # individually selectable in replay/training traces.
                options = tuple(
                    (
                        f"Guess {held.definition.name}"
                        f" [entity {held.entity_id}]",
                        (HolmesInspect(held.card_id),),
                    )
                    for held in opponent.hand
                )
                self.pending_choice = {
                    "kind": "RULE_CHOICE", "player": player.index,
                    "card": card, "action": action,
                    "options": options,
                    "option_metadata": tuple(
                        {"entity": held.entity_id, "card_id": held.card_id}
                        for held in opponent.hand
                    ),
                }
                self._event(
                    "holmes_investigate_offer", player=player.index,
                    source=card.card_id,
                    options=[held.card_id for held in opponent.hand],
                )
            return
        if card.card_id == "JAIL_882":
            spell_ids = [
                held.card_id for held in player.deck
                if held.definition.card_type == "SPELL"
            ]
            generated = []
            for spell_id in spell_ids:
                copy_card = self._entity(spell_id, created_by=card.card_id)
                if len(player.hand) >= 10:
                    break
                player.hand.append(copy_card)
                generated.append(copy_card.card_id)
            self._event(
                "r4t4tcher_copy_spells", player=player.index,
                source=card.card_id, copied=generated,
            )
            return
        if card.card_id == "JAIL_719":
            # Irida leaves exactly one random card in the normal deck and
            # moves every other card into the Void.  Void cards retain their
            # entities and accumulated cost changes; they are drawn back only
            # by Irida's start-of-turn effect.
            if player.deck:
                original_deck = list(player.deck)
                keep = self.rng.choice(original_deck)
                player.deck = [keep]
                player.void_cards.extend(
                    card_in_void for card_in_void in original_deck
                    if card_in_void is not keep
                )
            player.irida_active = True
            self._event(
                "irida_send_deck_to_void", player=player.index,
                kept=len(player.deck), void=len(player.void_cards),
            )
            return
        if card.card_id == "JAIL_430":
            # This Battlecry is distinct from the card's pre-game deck rebuild:
            # draw repeatedly only after Azalina itself has occupied a board
            # slot, stopping naturally at the hand-size cap.
            drawn = 0
            while len(player.hand) < 10 and player.deck:
                self._draw(player)
                drawn += 1
            self._event(
                "azalina_draw_to_full", player=player.index,
                source=card.entity_id, drawn=drawn, hand_size=len(player.hand),
            )
            return
        if card.card_id == "CATA_140":
            # Merithra's generated cards use the Dragon closure, rather than
            # all metadata rows, so a later play cannot degrade into an
            # unsupported vanilla card.  The held-mana counter is accumulated
            # by _spend_mana while the card remains in hand.
            discounted = card.mana_spent_while_held >= 25
            generated_ids: list[str] = []
            while len(player.hand) < 10:
                generated = self._entity(
                    self.rng.choice(sorted(DRAGON_IDS)), created_by=card.card_id,
                )
                if discounted:
                    generated.cost_delta = 1 - generated.definition.cost
                destination = self._add_generated(player, generated)
                generated_ids.append(generated.card_id)
                if destination != "hand":
                    break
            self._event(
                "merithra_fill_hand", player=player.index, source=card.entity_id,
                discounted=discounted, generated=generated_ids,
            )
            return
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
        if card.card_id == "TIME_002":
            self._offer_rewind(
                player, "aeon_wizard", remaining_battlecries=times - 1
            )
            return
        if card.card_id == "TIME_033":
            self._offer_rewind(
                player, "druid_of_regrowth", remaining_battlecries=times - 1
            )
            return
        if card.card_id == "TIME_038":
            self._offer_rewind(
                player, "mister_clocksworth", remaining_battlecries=2
            )
            return
        if card.card_id == "TOT_056":
            expansion_cards = [
                card_id for card_id, definition in self.card_defs.items()
                if definition.card_set == "TIME_TRAVEL"
            ]
            candidates = [
                card_id for card_id, definition in self.card_defs.items()
                if card_id in EXECUTABLE_CARD_IDS
                and definition.card_set == "TIME_TRAVEL"
            ]
            self._event(
                "rewind_taverns_pool", player=player.index,
                source=card.entity_id, expansion="TIME_TRAVEL",
                total_cards=len(expansion_cards),
                executable_cards=len(candidates),
                unsupported_cards=len(expansion_cards) - len(candidates),
            )
            if candidates:
                generated = self._entity(
                    self.rng.choice(sorted(candidates)), created_by=card.card_id
                )
                destination = self._add_generated(player, generated)
                self._event(
                    "rewind_taverns_card", player=player.index,
                    source=card.entity_id, card=generated.card_id,
                    destination=destination,
                )
            return
        if card.card_id == "END_036":
            self._offer_discover(
                player, sorted(ADDITIONAL_PLAYABLE_CARD_IDS),
                dark_gift=False, source_card_id=card.card_id,
            )
            return
        if card.card_id == "TOT_332":
            fabled_pool = [
                card_id for card_id, definition in self.card_defs.items()
                if card_id in FABLED_MINION_IDS
                and definition.card_type == "MINION"
            ]
            if fabled_pool:
                generated = self._entity(
                    self.rng.choice(sorted(fabled_pool)), created_by=card.card_id
                )
                destination = self._add_generated(player, generated)
                self._event(
                    "fabled_minion_generated", player=player.index,
                    source=card.entity_id, card=generated.card_id,
                    destination=destination,
                    bundled_cards_resolved=False,
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
            dragon_pool = [
                card_id for card_id, definition in self.card_defs.items()
                if card_id in EXECUTABLE_CARD_IDS
                and definition.card_type == "MINION"
                and "DRAGON" in definition.races
            ]
            self._offer_discover(
                player, dragon_pool, dark_gift=True, repeats=times,
                source_card_id=card.card_id,
            )
            return
        if card.card_id == "EDR_856":
            self._offer_deck_minion_discover(player, repeats=times)
            return
        if card.card_id == "FIR_924":
            demon_pool = [
                card_id for card_id, definition in self.card_defs.items()
                if card_id in EXECUTABLE_CARD_IDS
                and definition.card_type == "MINION"
                and "DEMON" in definition.races
            ]
            self._offer_discover(
                player, demon_pool, dark_gift=True,
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
                    self._dispatch_after_discard(player, target)
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
                    self._dispatch_after_discard(player, discarded)
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
            elif card.card_id == "TLC_243" and self._kindred_repeats(player, card):
                card.immune = True
            elif card.card_id == "DINO_404" and self._kindred_repeats(player, card):
                for other in player.board:
                    if other.entity_id != card.entity_id:
                        other.rush = True
            elif card.card_id == "DINO_413":
                enemy = self.players[1 - player.index]
                targets = [
                    minion for minion in enemy.board
                    if minion.dormant_turns == 0
                ]
                kindred = bool(self._kindred_repeats(player, card))
                for target in self.rng.sample(targets, min(2, len(targets))):
                    self._damage_minion(enemy.index, target, 2, card)
                    if kindred:
                        target.frozen_turn = self.turn
                        self._event(
                            "freeze", player=enemy.index,
                            entity=target.entity_id, source=card.card_id,
                        )
                self._resolve_deaths()
            elif card.card_id == "DINO_138" and (repeats := self._kindred_repeats(player, card)):
                enemy = self.players[1 - player.index]
                targets = [m for m in enemy.board if m.dormant_turns == 0]
                edge_targets = targets[:1] + targets[-1:]
                for _ in range(repeats):
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
                if drawn is not None and self._kindred_repeats(player, card):
                    drawn.cost_delta -= drawn.cost
            elif card.card_id == "TLC_463":
                # Razidir discards from its controller normally; Kindred
                # redirects the random discard to the opponent's hand.
                recipient = self.players[1 - player.index] if self._kindred_repeats(player, card) else player
                if recipient.hand:
                    discarded = self.rng.choice(recipient.hand)
                    recipient.hand.remove(discarded)
                    self._event("discard", player=recipient.index,
                                card=discarded.card_id, entity=discarded.entity_id,
                                source=card.card_id)
                    self._dispatch_after_discard(recipient, discarded)
            elif card.card_id == "TLC_825" and (repeats := self._kindred_repeats(player, card)):
                if action.target_player is not None and action.target_entity is not None:
                    target = self._find_minion(action.target_player, action.target_entity)
                    for _ in range(repeats):
                        self._damage_minion(action.target_player, target, card.attack, card)
                    self._resolve_deaths()
            elif card.card_id == "TLC_829":
                if action.target_player is not None and action.target_entity is not None:
                    target = self._find_minion(action.target_player, action.target_entity)
                    attack, health = target.attack, target.max_health
                    target.damage = target.max_health
                    self._resolve_deaths()
                    if self._kindred_repeats(player, card):
                        card.attack_delta += attack - card.definition.attack
                        card.health_delta += health - card.definition.health
                        self._event("ravenous_devilsaur_gain_stats", player=player.index,
                                    source=card.card_id, attack=attack, health=health)
            elif card.card_id == "TLC_482":
                for _ in range(2):
                    if len(player.board) + len(player.locations) >= 7:
                        break
                    cinder = self._entity("TLC_249", created_by=card.card_id)
                    cinder.summoned_turn = self.turn
                    self._summon(player, cinder)
                repeats = self._kindred_repeats(player, card)
                for _ in range(repeats):
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
                repeats = self._kindred_repeats(player, card)
                if drawn is not None and repeats:
                    drawn.spell_damage_bonus += 2 * repeats
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
                minions = self._random_enemy_minions(player.index)
                if minions:
                    destroyed_minion = self.rng.choice(minions)
                    destroyed_minion.damage = destroyed_minion.max_health
                if enemy.locations:
                    removed_location = self.rng.choice(enemy.locations)
                    enemy.locations.remove(removed_location)
                    self._location_deathrattle(enemy, removed_location)
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

    def _offer_ashalon_adapt(self, player: Player, *, remaining: int) -> None:
        """Offer one of three Adaptations, preserving the two-pick chain."""
        pool = [
            "attack_health", "attack", "health", "divine_shield", "taunt",
            "windfury", "poisonous", "stealth", "elusive", "plants",
        ]
        self.rng.shuffle(pool)
        self.pending_choice = {
            "kind": "ASHALON_ADAPT", "player": player.index,
            "options": pool[:3], "remaining": remaining,
        }
        self._event(
            "ashalon_adaptation_offer", player=player.index,
            options=pool[:3], remaining=remaining,
        )

    def _apply_ashalon_adaptations(self, player: Player, minion: CardInstance) -> None:
        for adaptation in player.ashalon_adaptations:
            if adaptation == "attack_health":
                minion.attack_delta += 1
                minion.health_delta += 1
            elif adaptation == "attack":
                minion.attack_delta += 3
            elif adaptation == "health":
                minion.health_delta += 3
            elif adaptation == "divine_shield":
                minion.divine_shield = True
                minion.divine_shield_hits = max(1, minion.divine_shield_hits)
            elif adaptation == "taunt":
                minion.taunt = True
            elif adaptation == "windfury":
                minion.windfury = True
            elif adaptation == "poisonous":
                minion.poisonous = True
            elif adaptation == "stealth":
                minion.stealth = True
            elif adaptation == "elusive":
                minion.elusive = True
            elif adaptation == "plants":
                for _ in range(2):
                    if len(player.board) + len(player.locations) >= 7:
                        break
                    plant = self._entity("UNG_999t2t1", created_by="TLC_229t14")
                    plant.summoned_turn = self.turn
                    self._summon(player, plant)
        if player.ashalon_adaptations:
            self._event(
                "ashalon_adaptations_applied", player=player.index,
                entity=minion.entity_id,
                adaptations=list(player.ashalon_adaptations),
            )

    def _cast_spell(self, player: Player, card: CardInstance, action: Action) -> None:
        opponent = self.players[1 - player.index]
        counterspell = next(
            (secret for secret in opponent.secrets
             if secret.card_id == "CORE_EX1_287"),
            None,
        )
        if counterspell is not None:
            self._consume_secret(opponent, counterspell)
            self._event(
                "counterspell", player=opponent.index,
                source=counterspell.entity_id, canceled=card.card_id,
            )
            return
        if card.card_id == "TIME_039":
            opponent = self.players[1 - player.index]
            if opponent.hand:
                self._offer_discover(
                    player,
                    [held.card_id for held in opponent.hand],
                    False,
                    source_card_id=card.card_id,
                )
                return
        if card.card_id == "TLC_515":
            self._offer_deck_card_discover(player, source_card_id=card.card_id)
            return
        prior_fire = player.fire_spell_played
        spell_damage = self._spell_damage(player) + card.spell_damage_bonus
        if self.rule_registry.dispatch(
            Hook.SPELL, card.card_id, self,
            RuleContext(player=player, card=card, action=action),
        ):
            return
        if card.card_id == "LOE_019t":
            # The map shuffles the Monkey first, then draws.  In particular,
            # the draw can burn the card if the hand was already full.
            monkey = self._entity("LOE_019t2", created_by=card.card_id)
            player.deck.insert(self.rng.randrange(len(player.deck) + 1), monkey)
            self._event(
                "golden_monkey_shuffled", player=player.index,
                source=card.card_id, card=monkey.card_id,
                entity=monkey.entity_id,
            )
            self._draw(player)
            return
        if card.casts_when_drawn_armor:
            self._gain_armor(player, card.casts_when_drawn_armor)
            self._event(
                "casts_when_drawn", player=player.index, card=card.card_id,
                armor=card.casts_when_drawn_armor,
            )
            self._after_card_draw(player, card)
            self._draw(player)
            return
        if card.card_id == "TLC_446t":
            player.underfel_rift_used_turn = self.turn
            if player.hand:
                thrown = next(
                    (held for held in player.hand if held.entity_id == action.target_entity),
                    None,
                ) or self.rng.choice(player.hand)
                player.hand.remove(thrown)
                # “Throw into the Rift” consumes the selected hand card; it
                # is not a discard and therefore must not trigger discard
                # reactions or be counted as a discard quest event.
                self._event("underfel_rift_throw", player=player.index,
                            card=thrown.card_id, source=card.card_id)
            pool = [
                card_id for card_id, definition in self.card_defs.items()
                if card_id in EXECUTABLE_CARD_IDS
                and definition.card_type == "MINION"
                and "DEMON" in definition.races
            ]
            for _ in range(2):
                if len(player.board) + len(player.locations) >= 7 or not pool:
                    break
                minion = self._entity(self.rng.choice(pool), created_by=card.card_id)
                minion.summoned_turn = self.turn
                self._summon(player, minion)
            return
        if card.card_id == "JAIL_200":
            # Sanitized Power.log observed 3 prior hero attacks producing two
            # 6-Cost minions and 7 prior attacks producing two 10-Cost
            # minions. The printed 3-Cost baseline upgrades by one per hero
            # attack, capped at ten.
            cost = min(10, 3 + player.hero_attacks_this_game)
            for _ in range(2):
                self._summon_random_executable_minion(
                    player, source_card_id=card.card_id, cost=cost,
                )
            self._event(
                "infest_scullery", player=player.index, source=card.entity_id,
                hero_attacks=player.hero_attacks_this_game, summoned_cost=cost,
            )
        elif card.card_id == "TIME_001":
            self._offer_rewind(player, "chrono_daggers")
        elif card.card_id == "TIME_433":
            self._offer_rewind(player, "cease_to_exist")
        elif card.card_id == "TIME_441":
            self._offer_rewind(player, "aeon_rend")
        elif card.card_id == "TIME_610":
            self._offer_rewind(player, "shadows_of_yesterday")
        elif card.card_id == "TIME_000":
            self._offer_rewind(player, "semi_stable_portal")
        elif card.card_id == "TIME_002":
            self._offer_rewind(player, "aeon_wizard")
        elif card.card_id == "TIME_014":
            self._offer_rewind(player, "instant_multiverse")
        elif card.card_id == "TIME_018":
            self._offer_rewind(player, "mend_the_timeline")
        elif card.card_id == "TIME_602":
            self._offer_rewind(player, "wormhole")
        elif card.card_id == "TIME_EVENT_999":
            self._offer_rewind_discover(player)
        elif card.card_id == "FIR_939":
            self._deal_to_target(
                player.index, (action.target_player, action.target_entity),
                2 + spell_damage,
            )
            warrior_pool = [
                card_id for card_id, definition in self.card_defs.items()
                if card_id in EXECUTABLE_CARD_IDS
                and definition.card_type == "MINION"
                and definition.card_class == "WARRIOR"
            ]
            self._offer_discover(
                player, warrior_pool, dark_gift=True,
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

    def _dispatch_after_spell_cast(
        self, player: Player, spell: CardInstance,
        action: Action | None = None,
        *, paid_cost: int | None = None,
    ) -> None:
        """Dispatch controller-owned 'After you cast a spell' rules."""
        if spell.definition.spell_school == "FEL":
            for location in player.locations:
                if location.card_id == "CATA_527" and location.durability > 0:
                    location.cooldown = 0
                    self._event(
                        "nespirah_reopened", player=player.index,
                        source=location.entity_id, spell=spell.card_id,
                    )
        for minion in list(player.board):
            if (
                minion not in player.board
                or minion.silenced
                or minion.dormant_turns > 0
                or minion.health <= 0
            ):
                continue
            self.rule_registry.dispatch(
                Hook.AFTER_PLAY, minion.card_id, self,
                RuleContext(
                    player=player, card=minion,
                    payload={
                        "spell": spell,
                        "paid_cost": spell.cost if paid_cost is None else paid_cost,
                        "target_player": None if action is None else action.target_player,
                        "target_entity": None if action is None else action.target_entity,
                    },
                ),
            )
        for held in list(player.hand):
            if held.card_id != "CORE_RLK_567":
                continue
            held.definition = spell.definition
            held.cost_delta = 0
        if player.next_spell_damage_bonus:
            self._event(
                "elise_shining_moonlight_consume", player=player.index,
                amount=player.next_spell_damage_bonus, spell=spell.card_id,
            )
            player.next_spell_damage_bonus = 0
            held.created_by = "CORE_RLK_567"
            self._event(
                "shadow_of_demise_transform", player=player.index,
                entity=held.entity_id, copied=spell.card_id,
            )
        for held in list(player.hand):
            if held.card_id != "JAIL_801":
                continue
            held.spells_cast_while_held += 1
            if held.spells_cast_while_held >= 3:
                held.definition = self.card_defs["JAIL_801t"]
            self._event(
                "molten_gold_transform", player=player.index,
                entity=held.entity_id, spells=held.spells_cast_while_held,
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
        was_stealthed = self._break_stealth_for_attack(attacker)
        attacker_damage = attacker.attack
        defender_damage = defender.attack
        attacker.attacking_now = True
        self._damage_minion(defender_owner, defender, attacker_damage, attacker)
        attacker.attacking_now = False
        if defender.health <= 0:
            defender.killed_by_entity = attacker.entity_id
        self._damage_minion(attacker_owner, attacker, defender_damage, defender)
        self._finja_kill(attacker_owner, attacker, defender)
        self._after_minion_attacked(defender_owner, defender)
        self._after_minion_attack(attacker_owner, attacker, attacked_minion=True, was_stealthed=was_stealthed)
        self._resolve_deaths()

    def _black_blood_after_restore(self, player: Player, source: CardInstance | None = None) -> None:
        """Resolve The Black Blood's trigger after a real Health restore."""
        bodies = [
            minion for minion in player.board
            if minion.card_id == "CATA_300"
            and not minion.silenced and minion.dormant_turns == 0
            and minion.health > 0
        ]
        for body in bodies:
            targets = self._random_enemy_minions(player.index)
            if not targets:
                continue
            target = self.rng.choice(targets)
            self._event("black_blood_attack", player=player.index,
                        source=body.entity_id, target=target.entity_id,
                        restore_source=getattr(source, "card_id", None))
            self._forced_minion_attack(
                player.index, body, 1 - player.index, target,
            )

    def _apply_heal(
        self, owner: Player, target: Any, amount: int,
        *, source: CardInstance | None = None,
        trigger_black_blood: bool = True,
    ) -> int:
        """Apply healing and dispatch Overheal only for actual excess."""
        amount = max(0, int(amount))
        if owner.ruby_sanctum_turn == self.turn and amount:
            owner.ruby_sanctum_turn = -1
            if isinstance(target, Player):
                self._damage_hero(owner, amount, source)
            else:
                self._damage_minion(owner.index, target, amount, source)
                self._resolve_deaths()
            self._event(
                "ruby_sanctum_replaced_heal", player=owner.index,
                source=None if source is None else source.card_id,
                amount=amount,
            )
            return 0
        missing = (
            max(0, target.max_health - target.health)
            if isinstance(target, Player) else max(0, target.damage)
        )
        restored = min(amount, missing)
        if isinstance(target, Player):
            target.health += restored
            if restored > 0:
                target.hero_health_changed_this_turn = True
        else:
            target.damage = max(0, target.damage - restored)
        if restored and trigger_black_blood:
            self._black_blood_after_restore(owner, source=source)
        excess = amount - restored
        if excess and source is not None:
            for minion in list(owner.board):
                if minion.silenced or minion.dormant_turns > 0 or minion.health <= 0:
                    continue
                self.rule_registry.dispatch(
                    Hook.OVERHEAL, minion.card_id, self,
                    RuleContext(
                        player=owner, card=minion,
                        payload={"amount": excess, "target": target, "source": source},
                    ),
                )
            self._event(
                "overheal", player=owner.index, source=source.card_id,
                target=(None if isinstance(target, Player) else target.entity_id),
                amount=excess,
            )
        return restored

    def _dispatch_after_discard(self, player: Player, discarded: CardInstance) -> None:
        """Notify board minions that a card was discarded by their controller."""
        for minion in list(player.board):
            if (
                minion not in player.board
                or minion.silenced
                or minion.dormant_turns > 0
                or minion.health <= 0
            ):
                continue
            self.rule_registry.dispatch(
                Hook.AFTER_DISCARD, minion.card_id, self,
                RuleContext(player=player, card=minion,
                            payload={"discarded": discarded}),
            )

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
        *, attacked_minion: bool = False, was_stealthed: bool = False,
    ) -> None:
        player = self.players[attacker_owner]
        if getattr(attacker, "avatar_form_pending", False) and not attacker.silenced:
            attacker.avatar_form_pending = False
            enemy = self.players[1 - attacker_owner]
            self._damage_hero(enemy, 2, attacker)
            for minion in list(enemy.board):
                self._damage_minion(enemy.index, minion, 2)
            self._resolve_deaths()
            self._event("avatar_form_blast", player=attacker_owner,
                        source=attacker.entity_id, amount=2)
        if was_stealthed and not attacker.silenced:
            for trigger in list(player.board):
                if trigger.silenced or trigger.dormant_turns > 0:
                    continue
                if trigger.card_id == "CAP_000":
                    attacker.attack_delta += 2
                    attacker.health_delta += 2
                    self._event("si7_slayer_buff", player=attacker_owner,
                                source=trigger.entity_id, target=attacker.entity_id)
                elif trigger.card_id == "CAP_005":
                    candidates = [card for card in player.hand if card.entity_id != attacker.entity_id]
                    if candidates:
                        chosen = self.rng.choice(candidates)
                        chosen.cost_delta -= 3
                        self._event("mathias_shaw_discount", player=attacker_owner,
                                    source=trigger.entity_id, target=chosen.entity_id, amount=3)
        if attacker.card_id == "CAP_003" and not attacker.silenced and attacker.health > 0 and attacker in player.board:
            self._draw(player)
            self._event("si7_supplier_draw", player=attacker_owner, entity=attacker.entity_id)
        elif attacker.card_id == "EDR_421" and not attacker.silenced:
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

        # Declarative "Whenever this attacks" effects resolve only while the
        # attacker remains a live, unsilenced board entity after combat.
        if (
            attacker in player.board
            and attacker.health > 0
            and attacker.dormant_turns == 0
            and not attacker.silenced
        ):
            self.rule_registry.dispatch(
                Hook.AFTER_ATTACK, attacker.card_id, self,
                RuleContext(
                    player=player, card=attacker,
                    payload={"attacked_minion": attacked_minion},
                ),
            )

        # Rehgar observes its own and its surviving adjacent minions' attacks.
        # The board may have changed during combat, so recompute adjacency
        # after deaths have resolved rather than retaining stale positions.
        for rehgar in list(player.board):
            if (
                rehgar.card_id != "CORE_CATA_004"
                or rehgar.silenced
                or rehgar.dormant_turns > 0
                or rehgar.health <= 0
            ):
                continue
            index = player.board.index(rehgar)
            adjacent = player.board[max(0, index - 1):index] + player.board[index + 1:index + 2]
            if attacker.entity_id != rehgar.entity_id and all(
                attacker.entity_id != minion.entity_id for minion in adjacent
            ):
                continue
            bolt = self._entity("CORE_EX1_238", created_by=rehgar.card_id)
            destination = self._add_generated(player, bolt)
            self._event(
                "rehgar_lightning_bolt", player=player.index,
                source=rehgar.entity_id, attacker=attacker.entity_id,
                card=bolt.card_id, destination=destination,
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
        if not options:
            self.pending_choice = None
            self._event(
                "discover_unavailable", player=player.index,
                source=source_card_id, dark_gift=dark_gift,
            )
            return
        if dark_gift:
            # The three Discover choices are paired with distinct gifts when
            # the candidate sets permit it.  Solve the tiny assignment problem
            # instead of greedily falling back to a duplicate for an unlucky
            # option ordering.
            eligible_sets = [set(self._eligible_dark_gifts(option)) for option in options]
            assignment: list[str] | None = None

            def assign(index: int, used: set[str], picked: list[str]) -> bool:
                nonlocal assignment
                if index == len(eligible_sets):
                    assignment = list(picked)
                    return True
                choices = sorted(eligible_sets[index] - used)
                self.rng.shuffle(choices)
                for gift in choices:
                    if assign(index + 1, used | {gift}, picked + [gift]):
                        return True
                return False

            if not assign(0, set(), []):
                # A pathological/fully constrained pool can make uniqueness
                # impossible; preserve playability by allowing a duplicate.
                assignment = [self.rng.choice(sorted(gifts)) for gifts in eligible_sets]
            for option, gift in zip(options, assignment):
                self._apply_dark_gift(option, gift, owner=player)
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
            self._apply_dark_gift(option, gift, owner=player)
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

    def _offer_intertwined_fate(
        self, player: Player, *, source_card_id: str
    ) -> None:
        """Discover one copied card from each deck, in two explicit picks.

        Hearthstone's UI presents the two source pools as one compound choice.
        The simulator represents the same required outcome as two pending
        selections, which keeps action encoding fixed while retaining card
        provenance for downstream copy-synergy cards.
        """
        opponent = self.players[1 - player.index]

        def copied_options(owner: Player, *, from_opponent: bool) -> list[CardInstance]:
            originals = self.rng.sample(owner.deck, min(3, len(owner.deck)))
            options: list[CardInstance] = []
            for original in originals:
                option = original.clone(self.next_entity_id)
                self.next_entity_id += 1
                option.started_in_deck = False
                option.created_by = source_card_id
                option.copied_from_opponent = from_opponent
                options.append(option)
            return options

        own_options = copied_options(player, from_opponent=False)
        opponent_options = copied_options(opponent, from_opponent=True)
        if not own_options or not opponent_options:
            self._event(
                "intertwined_fate_unavailable", player=player.index,
                source=source_card_id, own_options=len(own_options),
                opponent_options=len(opponent_options),
            )
            return
        self.pending_choice = {
            "kind": "INTERTWINED_FATE",
            "player": player.index,
            "source_card_id": source_card_id,
            "options": own_options,
            "opponent_options": opponent_options,
        }
        self._event(
            "intertwined_fate_offer", player=player.index, source=source_card_id,
            own_options=[{"entity": card.entity_id, "card": card.card_id}
                         for card in own_options],
            opponent_options=[{"entity": card.entity_id, "card": card.card_id}
                              for card in opponent_options],
        )

    def _offer_class_discover(
        self, player: Player, *, card_class: str, source_card_id: str,
        cost_delta: int = 0,
    ) -> None:
        candidates = sorted(
            card_id for card_id, definition in self.card_defs.items()
            if card_id in EXECUTABLE_CARD_IDS
            and definition.card_class == card_class
        )
        self.rng.shuffle(candidates)
        options = [
            self._entity(card_id, created_by=source_card_id)
            for card_id in candidates[:3]
        ]
        for option in options:
            option.cost_delta += cost_delta
        self.pending_choice = {
            "kind": "DISCOVER", "player": player.index,
            "pool": tuple(candidates), "dark_gift": False,
            "repeats_left": 0, "after_pick": None,
            "source_card_id": source_card_id, "options": options,
        }
        self._event(
            "class_discover_offer", player=player.index, source=source_card_id,
            card_class=card_class, cost_delta=cost_delta,
            profile="executable_standard_pool_v1",
            options=[{"entity": card.entity_id, "card": card.card_id}
                     for card in options],
        )

    def _refresh_skeleton_key(self) -> None:
        pending = self.pending_choice
        if pending is None or pending.get("kind") != "SKELETON_KEY":
            raise ValueError("no Skeleton Key choice is pending")
        player = self.players[pending["player"]]
        if self.rng.random() < 0.20:
            self._damage_hero(player, 5)
            self._event(
                "skeleton_key_refresh_damage", player=player.index,
                amount=5, refreshes=pending["refreshes"] + 1,
            )
        candidates = list(pending["pool"])
        self.rng.shuffle(candidates)
        self.pending_choice["options"] = [
            self._entity(card_id, created_by="JAIL_319")
            for card_id in candidates[:3]
        ]
        self.pending_choice["refreshes"] += 1
        self._event(
            "skeleton_key_refresh", player=player.index,
            refreshes=self.pending_choice["refreshes"],
            options=[card.card_id for card in self.pending_choice["options"]],
        )

    def _offer_spell_school_discover(
        self, player: Player, *, spell_school: str, source_card_id: str,
        cost_delta: int = 0,
    ) -> None:
        candidates = sorted(
            card_id for card_id, definition in self.card_defs.items()
            if card_id in EXECUTABLE_CARD_IDS
            and definition.card_type == "SPELL"
            and definition.spell_school == spell_school
        )
        self.rng.shuffle(candidates)
        options = [
            self._entity(card_id, created_by=source_card_id)
            for card_id in candidates[:3]
        ]
        for option in options:
            option.cost_delta += cost_delta
        self.pending_choice = {
            "kind": "DISCOVER",
            "player": player.index,
            "pool": tuple(candidates), "dark_gift": False,
            "repeats_left": 0, "after_pick": None,
            "source_card_id": source_card_id, "options": options,
        }
        self._event(
            "spell_school_discover_offer", player=player.index,
            source=source_card_id, spell_school=spell_school,
            cost_delta=cost_delta, profile="executable_standard_pool_v1",
            options=[{"entity": card.entity_id, "card": card.card_id}
                     for card in options],
        )

    def _offer_spell_discover(
        self, player: Player, *, source_card_id: str, discount: int = 0,
    ) -> None:
        candidates = sorted(
            card_id for card_id, definition in self.card_defs.items()
            if card_id in EXECUTABLE_CARD_IDS
            and definition.card_type == "SPELL"
        )
        self.rng.shuffle(candidates)
        options = [
            self._entity(card_id, created_by=source_card_id)
            for card_id in candidates[:3]
        ]
        self.pending_choice = {
            "kind": "SKELETON_KEY" if source_card_id == "JAIL_319" else "DISCOVER",
            "player": player.index,
            "pool": tuple(candidates), "dark_gift": False,
            "repeats_left": 0, "after_pick": None,
            "source_card_id": source_card_id, "options": options,
            "refreshes": 0, "custom_discount": discount,
        }
        self._event(
            "spell_discover_offer", player=player.index,
            source=source_card_id,
            options=[{"entity": card.entity_id, "card": card.card_id}
                     for card in options],
        )

    def _offer_legendary_wild_god_discover(
        self, player: Player, *, source_card_id: str,
        discount_if_imbued: bool = False,
    ) -> None:
        candidates = sorted(
            card_id for card_id, definition in self.card_defs.items()
            if card_id in EXECUTABLE_CARD_IDS
            and definition.card_type == "MINION"
            and getattr(definition, "rarity", "") == "LEGENDARY"
        )

    def _offer_opponent_deck_minion_discover(
        self, player: Player, *, source_card_id: str, dark_gift: bool = False,
    ) -> None:
        opponent = self.players[1 - player.index]
        originals = [c for c in opponent.deck if c.definition.card_type == "MINION"]
        self.rng.shuffle(originals)
        options = []
        for original in originals[:3]:
            option = original.clone(self.next_entity_id)
            self.next_entity_id += 1
            option.created_by = source_card_id
            if dark_gift:
                eligible = sorted(self._eligible_dark_gifts(option))
                if eligible:
                    self._apply_dark_gift(option, self.rng.choice(eligible), owner=player)
            options.append(option)
        if not options:
            self.pending_choice = None
            self._event(
                "discover_unavailable", player=player.index,
                source=source_card_id, dark_gift=dark_gift,
            )
            return
        self.pending_choice = {
            "kind": "DISCOVER", "player": player.index,
            "pool": tuple(c.card_id for c in options), "dark_gift": dark_gift,
            "repeats_left": 0, "after_pick": None,
            "source_card_id": source_card_id, "options": options,
        }
        self._event(
            "opponent_deck_minion_discover_offer", player=player.index,
            source=source_card_id, dark_gift=dark_gift,
            options=[{"entity": c.entity_id, "card": c.card_id, "gifts": list(c.gifts)} for c in options],
        )
        self.rng.shuffle(candidates)
        options = [self._entity(i, created_by=source_card_id) for i in candidates[:3]]
        self.pending_choice = {
            "kind": "DISCOVER", "player": player.index,
            "pool": tuple(candidates), "dark_gift": False,
            "repeats_left": 0, "after_pick": None,
            "source_card_id": source_card_id, "options": options,
            "malorne_discount": discount_if_imbued,
        }
        self._event(
            "legendary_wild_god_discover_offer", player=player.index,
            source=source_card_id, discount_if_imbued=discount_if_imbued,
            options=[{"entity": c.entity_id, "card": c.card_id} for c in options],
        )

    def _offer_rune_discover(self, player: Player, *, rune: str, source_card_id: str) -> None:
        candidates = sorted(
            card_id for card_id, definition in self.card_defs.items()
            if card_id in EXECUTABLE_CARD_IDS
            and definition.card_class == "DEATHKNIGHT"
            and getattr(definition, "rune_cost", None)
            and definition.rune_cost.get(rune.casefold(), 0) > 0
        )
        self.rng.shuffle(candidates)
        options = [self._entity(card_id, created_by=source_card_id) for card_id in candidates[:3]]
        self.pending_choice = {
            "kind": "DISCOVER", "player": player.index,
            "pool": tuple(candidates), "dark_gift": False,
            "repeats_left": 0, "after_pick": None,
            "source_card_id": source_card_id, "options": options,
        }
        self._event("rune_discover_offer", player=player.index, rune=rune,
                    source=source_card_id, options=[c.card_id for c in options])

    def _add_random_executable_class_card(
        self, player: Player, *, card_class: str, source_card_id: str,
        cost_delta: int = 0,
    ) -> None:
        candidates = sorted(
            card_id for card_id, definition in self.card_defs.items()
            if card_id in EXECUTABLE_CARD_IDS
            and definition.card_class == card_class
        )
        if not candidates:
            self._event(
                "random_class_card_unavailable", player=player.index,
                source=source_card_id, card_class=card_class,
            )
            return
        card = self._entity(
            self.rng.choice(candidates), created_by=source_card_id
        )
        card.cost_delta += cost_delta
        destination = self._add_generated(player, card)
        self._event(
            "random_class_card", player=player.index, source=source_card_id,
            card_class=card_class, card=card.card_id, entity=card.entity_id,
            destination=destination, cost_delta=cost_delta,
            profile="executable_standard_pool_v1",
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
        if pending["kind"] == "INTERTWINED_FATE":
            destination = self._add_generated(player, option)
            self.pending_choice = {
                "kind": "INTERTWINED_FATE_OPPONENT",
                "player": player.index,
                "source_card_id": pending["source_card_id"],
                "options": pending["opponent_options"],
            }
            self._event(
                "intertwined_fate_pick", player=player.index,
                source=pending["source_card_id"], pool="own",
                card=option.card_id, entity=option.entity_id,
                destination=destination,
            )
            return
        if pending["kind"] == "INTERTWINED_FATE_OPPONENT":
            destination = self._add_generated(player, option)
            self._event(
                "intertwined_fate_pick", player=player.index,
                source=pending["source_card_id"], pool="opponent",
                card=option.card_id, entity=option.entity_id,
                destination=destination,
            )
            return
        if pending.get("malorne_discount"):
            option.cost_delta = 1 - option.definition.cost
        if pending.get("dark_gift_cost_delta"):
            option.cost_delta += pending["dark_gift_cost_delta"]
        if pending.get("source_card_id") == "TLC_100_CUSTOM":
            option.cost_delta -= pending.get("custom_discount", 0)
        if pending.get("source_card_id") == "CAP_407":
            option.prepare_granted = True
        destination = self._add_generated(player, option)
        if pending.get("ivory_heal"):
            healed = option.definition.cost
            player.health = min(player.max_health, player.health + healed)
            self._event(
                "ivory_knight_heal", player=player.index,
                source=pending.get("source_card_id"), amount=healed,
                chosen_spell=option.card_id,
            )
        if pending.get("map_followup") and destination == "hand":
            player.map_followup_options = [
                other.card_id for other in pending["options"]
                if other.card_id != option.card_id
            ]
            player.map_followup_entity = option.entity_id
            player.map_followup_turn = self.turn
        if (
            player.weapon is not None
            and player.weapon.card_id == "TLC_460t"
            and player.weapon.durability > 0
            and not player.origin_stone_triggering
        ):
            self._origin_stone_play_unchosen(player, pending["options"], option.entity_id)
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
        elif pending["after_pick"] == "keep_all_undead":
            if player.corpses >= 5:
                player.corpses -= 5
                for other in pending["options"]:
                    if other.entity_id == option.entity_id:
                        continue
                    copy = other.clone(self.next_entity_id)
                    self.next_entity_id += 1
                    copy.created_by = pending["source_card_id"]
                    self._add_generated(player, copy)
                self._event("paleomancy_keep_all", player=player.index,
                            source=pending["source_card_id"], amount=5)
        elif pending["after_pick"] == "corpse_copy_5":
            if player.corpses >= 5 and len(player.board) + len(player.locations) < 7:
                player.corpses -= 5
                copy = option.clone(self.next_entity_id)
                self.next_entity_id += 1
                copy.created_by = pending["source_card_id"]
                copy.damage = 0
                copy.summoned_turn = self.turn
                self._summon(player, copy)
                self._event("blood_clone_summon", player=player.index,
                            source=pending["source_card_id"], card=copy.card_id)
        repeats_left = pending["repeats_left"]
        if repeats_left:
            self._offer_discover(
                player, pending["pool"], pending["dark_gift"],
                repeats=repeats_left, after_pick=pending["after_pick"],
                source_card_id=pending["source_card_id"],
            )
        elif pending["after_pick"] == "summon_cannoneers":
            self._summon_cannoneers(player)

    def _origin_stone_play_unchosen(
        self, player: Player, options: list[CardInstance], chosen_entity: int,
    ) -> None:
        """Resolve Origin Stone's remaining Discover options as free plays."""
        player.origin_stone_triggering = True
        try:
            for option in options:
                if option.entity_id == chosen_entity:
                    continue
                player.cards_played_this_turn += 1
                player.played_card_counts[option.card_id] = (
                    player.played_card_counts.get(option.card_id, 0) + 1
                )
                option.combo_active = player.cards_played_this_turn > 1
                if not option.started_in_deck:
                    player.generated_cards_played += 1
                self._event(
                    "play", player=player.index, card=option.card_id,
                    controller=player.index, entity=option.entity_id,
                    started_in_deck=option.started_in_deck,
                    created_by=option.created_by, origin_stone=True,
                )
                if option.definition.card_type == "MINION":
                    player.minion_played_this_turn = True
                    player.played_races_this_turn.update(option.definition.races)
                    player.played_races_this_game.update(option.definition.races)
                    if option.definition.race:
                        player.played_races_this_turn.add(option.definition.race)
                        player.played_races_this_game.add(option.definition.race)
                    if option.has_race("DRAGON"):
                        player.dragons_played_this_turn += 1
                action = Action("PLAY", option.entity_id)
                target_spec = self.rule_registry.targeting(option.card_id)
                if target_spec is not None:
                    targets = self._rule_targets(player, option, target_spec.kind)
                    if not targets:
                        self._event(
                            "origin_stone_option_skipped", player=player.index,
                            card=option.card_id, reason="no_target",
                        )
                        continue
                    target_player, target_entity = self.rng.choice(targets)
                    action = Action("PLAY", option.entity_id, target_player, target_entity)
                if option.definition.card_type == "MINION":
                    if len(player.board) + len(player.locations) >= 7:
                        continue
                    option.summoned_turn = self.turn
                    option.played_turn = self.turn
                    self._summon(player, option)
                    self._battlecry(player, option, action)
                elif option.definition.card_type == "SPELL":
                    self._cast_spell(player, option, action)
                    if player.hamuul_active:
                        player.hamuul_spells_cast += 1
                        if player.hamuul_spells_cast % 3 == 0:
                            power_id = imbue_hero_power_id(player.card_class)
                            if power_id in self.card_defs:
                                player.hero_power_id = power_id
                                player.imbued_hero_power_id = power_id
                                player.hero_power_imbues += 1
                                self._event(
                                    "hero_power_imbued", player=player.index,
                                    source="EDR_845", hero_power=power_id,
                                    count=player.hero_power_imbues,
                                )
                    self._dispatch_after_spell_cast(player, option)
                elif option.definition.card_type == "WEAPON":
                    durability = (
                        option.definition.health
                        if option.card_id == "TLC_460t"
                        else getattr(option.definition, "durability", 0)
                        or option.definition.health or 2
                    )
                    self._equip_weapon(
                        player, Weapon(option.card_id, option.definition.name,
                                       option.definition.attack, durability),
                    )
                    self._battlecry(player, option, action)
                self._event(
                    "origin_stone_option_played", player=player.index,
                    card=option.card_id,
                )
        finally:
            player.origin_stone_triggering = False
        if player.weapon is not None and player.weapon.card_id == "TLC_460t":
            player.weapon.durability -= 1
            self._event(
                "origin_stone_durability", player=player.index,
                remaining=player.weapon.durability,
            )
            if player.weapon.durability <= 0:
                self._destroy_weapon(player)

    def _resolve_earthen_roar_pick(self, entity_id: int) -> None:
        pending = self.pending_choice
        target = next(m for m in pending["options"] if m.entity_id == entity_id)
        target.health_delta += 1 - target.max_health
        self.pending_choice = None
        self._event("earthen_roar_second_pick", player=pending["player"], target=entity_id)

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

    def _apply_dark_gift(self, card: CardInstance, gift: str, *, propagate: bool = True, owner: Player | None = None) -> None:
        if gift not in self._eligible_dark_gifts(card):
            raise ValueError(f"ineligible Dark Gift {gift} for {card.card_id}")
        # A Dark Gift is an enchantment event, not a set membership flag.
        # Keyword gifts become ineligible after the first application because
        # _eligible_dark_gifts observes the newly granted keyword.  Gifts
        # without such a keyword restriction (for example Sweet Dreams and
        # Living Nightmare) may be granted again by a later Discover.  Keep
        # each application in the list so Wallow can copy every event.
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
        if propagate:
            # Wallow copies gifts granted to friendly minions while hidden in
            # hand/deck.  Do not recurse when applying the copied gift.
            owner = owner or next(
                (
                    p for p in self.players
                    if card in p.board or card in p.hand or card in p.deck
                ),
                None,
            )
            if owner is not None:
                for hidden in owner.hand + owner.deck:
                    if hidden.card_id == "EDR_487":
                        self._apply_dark_gift(hidden, gift, propagate=False)

    def _add_generated(self, player: Player, card: CardInstance) -> str:
        if (card.card_id in {"CATA_134", "CATA_306", "CATA_479", "CATA_489", "CATA_820"}
                and not card.shatter_combined):
            return "hand" if self._split_shatter_card(player, card) else "burned"
        if "sweet_dreams" in card.gifts:
            # Sweet Dreams places the gifted minion on top of the deck, so the
            # next draw must return this exact card.
            player.deck.insert(0, card)
            self._event(
                "dark_gift_topdeck", player=player.index,
                card=card.card_id, entity=card.entity_id, gift="sweet_dreams",
            )
            return "deck"
        elif len(player.hand) < 10:
            player.hand.append(card)
            if card.card_id in {"TLC_817t3", "TLC_817t4"}:
                self._combine_soletos(player)
            return "hand"
        return "burned"

    def _split_shatter_card(self, player: Player, card: CardInstance) -> bool:
        """Replace a Shatter card entering hand with its two half-cards.

        The two pieces are placed at opposite ends of the hand.  Hand-size
        limits are applied independently, so a partially full hand can keep
        one half while burning the other instead of exceeding ten cards.
        """
        available = max(0, 10 - len(player.hand))
        if available == 0:
            self._event("shatter_burn", player=player.index, card=card.card_id,
                        halves=2)
            return False
        shatter_halves = {
            "CATA_134": ("CATA_134t", "CATA_134t2"),
            "CATA_306": ("CATA_306t1", "CATA_306t2"),
            "CATA_489": ("CATA_489t", "CATA_489t2"),
            "CATA_479": ("CATA_479t", "CATA_479t2"),
            "CATA_820": ("CATA_820t", "CATA_820t2"),
        }
        half_ids = shatter_halves.get(card.card_id)
        if half_ids is None:
            raise UnsupportedGeneratedCard(f"Shatter card {card.card_id}")
        left = card.clone(self.next_entity_id)
        self.next_entity_id += 1
        right = card.clone(self.next_entity_id)
        self.next_entity_id += 1
        left.definition = self.card_defs[half_ids[0]]
        right.definition = self.card_defs[half_ids[1]]
        left.shatter_origin = right.shatter_origin = card.card_id
        left.shatter_half, right.shatter_half = "left", "right"
        if available >= 2:
            player.hand.insert(0, left)
            player.hand.append(right)
            burned = 0
        else:
            # With one slot remaining, Hearthstone keeps the left-hand
            # Shattered piece; the right-hand piece is burned.
            player.hand.insert(0, left)
            burned = 1
        self._event("shatter_split", player=player.index, source=card.card_id,
                    halves=[left.entity_id, right.entity_id], burned=burned)
        for source in list(player.board):
            if source.dormant_turns == 0 and not source.silenced:
                self.rule_registry.dispatch(
                    Hook.SHATTER, source.card_id, self,
                    RuleContext(player=player, card=source),
                )
        return True

    def _normalize_shattered_hand(self, player: Player) -> None:
        for index in range(len(player.hand) - 1):
            left, right = player.hand[index], player.hand[index + 1]
            if left.shatter_origin != right.shatter_origin or left.shatter_origin is None:
                continue
            if {left.shatter_half, right.shatter_half} != {"left", "right"}:
                continue
            merged = self._entity(left.shatter_origin, created_by="SHATTER_MERGE")
            merged.cost_delta = left.cost_delta
            player.hand[index:index + 2] = [merged]
            self._event("shatter_merge", player=player.index,
                        source=merged.card_id, halves=[left.entity_id, right.entity_id])
            return

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
        elif weapon.card_id == "TIME_209t":
            # High King's Hammer's deathrattle shuffles itself back with
            # permanently increased attack.  The equipped instance is not
            # reused; create a fresh deck entity carrying the attack gain.
            hammer = self._entity("TIME_209t", started_in_deck=True)
            hammer.attack_delta = weapon.attack - hammer.definition.attack + 2
            player.deck.insert(self.rng.randrange(len(player.deck) + 1), hammer)
            self._event("high_kings_hammer_reshuffled", player=player.index,
                        attack=hammer.attack, card=hammer.card_id)
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
        if player.avatar_form_hero_pending:
            player.avatar_form_hero_pending = False
            enemy = self.players[1 - player.index]
            self._damage_hero(enemy, 2)
            for minion in list(enemy.board):
                self._damage_minion(enemy.index, minion, 2)
            self._resolve_deaths()
            self._event("avatar_form_blast", player=player.index,
                        source="hero", amount=2)
        if weapon is None:
            self._dispatch_after_hero_attack(
                player, attack_amount=attack_amount, weapon=None, attacked=attacked
            )
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
        elif weapon.card_id == "TLC_239t":
            for minion in player.board:
                if minion.dormant_turns == 0 and not minion.silenced:
                    minion.attack_delta += 2
                    minion.health_delta += 2
        elif weapon.card_id == "CATA_467" and player.board:
            self.rng.choice(player.board).attack_delta += 2
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
            self._dispatch_after_discard(player, discarded)
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
        elif weapon.card_id == "TIME_875t1":
            for owner in self.players:
                candidates = [
                    card for card in owner.deck
                    if card.definition.card_type == "MINION"
                    and card.definition.rarity == "LEGENDARY"
                ]
                if not candidates:
                    continue
                drawn = self.rng.choice(candidates)
                owner.deck.remove(drawn)
                destination = "hand" if len(owner.hand) < 10 else "burned"
                if destination == "hand":
                    owner.hand.append(drawn)
                self._event("kingslayers_draw", player=owner.index,
                            card=drawn.card_id, destination=destination)
        elif weapon.card_id == "JAIL_458" and weapon.ammunition is not None:
            self._fire_tiny_pal_ammunition(player, weapon, attacked)
        self._dispatch_after_hero_attack(
            player, attack_amount=attack_amount, weapon=weapon, attacked=attacked
        )

    def _dispatch_after_hero_attack(
        self, player: Player, *, attack_amount: int | None = None,
        weapon: Weapon | None = None,
        attacked: tuple[int, int | None] | None = None,
    ) -> None:
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
                RuleContext(
                    player=player, card=minion,
                    payload={"hero_attack": attack_amount, "attacked": attacked},
                ),
            )
        if weapon is not None and weapon.card_id == "JAIL_730":
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
        if weapon is not None and self.rule_registry.has_hook(
            Hook.AFTER_HERO_ATTACK, weapon.card_id
        ):
            card = CardInstance(-1, self.card_defs[weapon.card_id])
            self.rule_registry.dispatch(
                Hook.AFTER_HERO_ATTACK, weapon.card_id, self,
                RuleContext(
                    player=player, card=card,
                    payload={"hero_attack": attack_amount, "attacked": attacked},
                ),
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
        morchie_active = any(
            minion.card_id == "END_036" and not minion.silenced
            for minion in player.board
        )
        if morchie_active:
            # Morchie removes the keep/retry prompt: both potential outcomes
            # are retained.  Re-run from the first outcome so additive effects
            # (damage, summons, draws) accumulate naturally.
            second = self._run_rewind_effect(player, effect)
            self._event(
                "rewind_both_outcomes", player=player.index,
                effect=effect, first=outcome, second=second,
            )
            if remaining_battlecries:
                self._offer_rewind(
                    player, effect, remaining_battlecries=remaining_battlecries - 1
                )
            return
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

    def _offer_rewind_discover(self, player: Player, *, class_only: bool = False,
                               before_players: list[Player] | None = None) -> None:
        pool = [
            card_id for card_id, definition in self.card_defs.items()
            if card_id in EXECUTABLE_CARD_IDS and definition.card_type == "SPELL"
            and (not class_only or definition.card_class == player.card_class)
        ]
        shuffled = sorted(pool)
        self.rng.shuffle(shuffled)
        options = [self._entity(card_id, created_by="TIME_EVENT_999")
                   for card_id in shuffled[:3]]
        if not options:
            self.pending_choice = None
            self._event("rewind_discover_unavailable", player=player.index,
                        source="TIME_EVENT_999", class_only=class_only)
            return
        self.pending_choice = {
            "kind": "REWIND_DISCOVER", "player": player.index,
            "before_players": copy.deepcopy(self.players) if before_players is None else before_players,
            "class_only": class_only,
            "morchie_second": (not class_only and any(
                m.card_id == "END_036" and not m.silenced for m in player.board
            )),
            "pool": tuple(sorted(pool)), "options": options,
        }
        self._event("rewind_discover_offer", player=player.index,
                    options=[c.card_id for c in options])

    def _resolve_rewind_discover(self, action: Action) -> None:
        pending = self.pending_choice
        if pending is None or pending["kind"] != "REWIND_DISCOVER":
            raise ValueError("no Rewind Discover is pending")
        if action.kind == "REWIND_RETRY":
            before = copy.deepcopy(pending["before_players"])
            self.players = before
            self.pending_choice = None
            self._offer_rewind_discover(
                self.players[pending["player"]], class_only=True,
                before_players=before,
            )
            return
        option = next((c for c in pending["options"] if c.entity_id == action.source), None)
        if option is None:
            raise ValueError("invalid Rewind Discover option")
        player = self.players[pending["player"]]
        self.pending_choice = None
        self._add_generated(player, option)
        self._event("rewind_discover_pick", player=player.index, card=option.card_id)
        if pending.get("morchie_second"):
            # Morchie keeps both Sands of Time outcomes: after the first
            # (any-class) Discover, immediately offer the post-Rewind,
            # own-class Discover without restoring away the first pick.
            self._offer_rewind_discover(player, class_only=True,
                                        before_players=pending["before_players"])

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
                self._dispatch_after_discard(owner, card)
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
        if effect == "semi_stable_portal":
            candidates = [
                card_id for card_id, definition in self.card_defs.items()
                if card_id in EXECUTABLE_CARD_IDS
                and definition.card_type == "MINION"
            ]
            if not candidates:
                return None
            generated = self._entity(self.rng.choice(sorted(candidates)), created_by="TIME_000")
            generated.cost_delta -= 3
            destination = self._add_generated(player, generated)
            return {"card": generated.card_id, "entity": generated.entity_id,
                    "destination": destination, "cost_delta": -3}
        if effect == "aeon_wizard":
            candidates = [
                card_id for card_id, definition in self.card_defs.items()
                if card_id in EXECUTABLE_CARD_IDS
                and definition.card_type == "SPELL"
                and definition.card_class == player.card_class
            ]
            generated = []
            for _ in range(2):
                if not candidates:
                    break
                card = self._entity(self.rng.choice(sorted(candidates)), created_by="TIME_002")
                destination = self._add_generated(player, card)
                generated.append({"card": card.card_id, "entity": card.entity_id,
                                  "destination": destination})
            return generated
        if effect == "instant_multiverse":
            remaining = 12
            summoned = []
            while remaining > 0 and len(player.board) + len(player.locations) < 7:
                candidates = [
                    card_id for card_id, definition in self.card_defs.items()
                    if card_id in EXECUTABLE_CARD_IDS
                    and definition.card_type == "MINION"
                    and 1 <= definition.cost <= remaining
                ]
                if not candidates:
                    break
                chosen = self.rng.choice(candidates)
                cost = self.card_defs[chosen].cost
                summoned_card = self._entity(chosen, created_by="TIME_014")
                summoned_card.summoned_turn = self.turn
                self._summon(player, summoned_card)
                summoned.append({"card": chosen, "cost": cost})
                remaining -= cost
            # Instant Multiverse has Overload (3), applied after the rewind
            # effect just like a normally played overload spell.
            self._overload(player, 3)
            return summoned
        if effect == "mend_the_timeline":
            candidates = [
                card_id for card_id, definition in self.card_defs.items()
                if card_id in EXECUTABLE_CARD_IDS
                and definition.card_type == "SPELL"
                and definition.spell_school == "HOLY"
            ]
            generated = []
            total_cost = 0
            for _ in range(2):
                if not candidates:
                    break
                card = self._entity(self.rng.choice(sorted(candidates)), created_by="TIME_018")
                total_cost += card.definition.cost
                destination = self._add_generated(player, card)
                generated.append({"card": card.card_id, "entity": card.entity_id,
                                  "destination": destination})
            player.health = min(player.max_health, player.health + total_cost)
            return {"cards": generated, "healed": total_cost}
        if effect == "wormhole":
            candidates = [
                card_id for card_id, definition in self.card_defs.items()
                if card_id in EXECUTABLE_CARD_IDS
                and definition.card_type == "MINION"
                and definition.cost == 3
                and "BEAST" in definition.races
            ]
            if not candidates or len(player.board) + len(player.locations) >= 7:
                return None
            summoned = self._entity(self.rng.choice(sorted(candidates)), created_by="TIME_602")
            summoned.summoned_turn = self.turn
            self._summon(player, summoned)
            enemies = self._random_enemy_characters(player.index)
            target = self.rng.choice(enemies) if enemies else None
            if target is not None:
                if target[1] is None:
                    self._damage_hero(self.players[target[0]], summoned.attack, summoned)
                else:
                    defender = self._find_minion(target[0], target[1])
                    self._damage_minion(target[0], defender, summoned.attack, summoned)
                    self._damage_minion(player.index, summoned, defender.attack, defender)
                    self._resolve_deaths()
            return {"card": summoned.card_id, "entity": summoned.entity_id,
                    "target": target}
        if effect == "mister_clocksworth":
            candidates = [
                card_id for card_id, definition in self.card_defs.items()
                if card_id in EXECUTABLE_CARD_IDS
                and definition.card_type == "MINION"
                and definition.rarity == "LEGENDARY"
            ]
            summoned = []
            for _ in range(2):
                if len(player.board) + len(player.locations) >= 7 or not candidates:
                    break
                card_id = self.rng.choice(sorted(candidates))
                minion = self._entity(card_id, created_by="TIME_038")
                minion.summoned_turn = self.turn
                self._summon(player, minion)
                summoned.append({"card": card_id, "entity": minion.entity_id})
            return summoned
        if effect == "druid_of_regrowth":
            # Prefer targetless Nature spells, then resolve targeted spells
            # through the same faction/priority-aware candidate pool.  The
            # normal spell dispatcher remains the final legality authority.
            candidates = [
                card_id for card_id, definition in self.card_defs.items()
                if card_id in EXECUTABLE_CARD_IDS
                and definition.card_type == "SPELL"
                and definition.spell_school == "NATURE"
            ]
            cast = []
            for _ in range(2):
                if not candidates:
                    break
                spell = self._entity(self.rng.choice(sorted(candidates)), created_by="TIME_033")
                try:
                    self._cast_spell(player, spell, Action("PLAY", spell.entity_id))
                    cast.append({"card": spell.card_id, "entity": spell.entity_id})
                except ValueError as exc:
                    targeted = self._random_spell_target_candidates(player.index, spell)
                    for target_player, target_entity, target_name in targeted:
                        try:
                            self._cast_spell(
                                player, spell,
                                Action("PLAY", spell.entity_id,
                                       target_player, target_entity),
                            )
                            cast.append({"card": spell.card_id, "entity": spell.entity_id,
                                         "target": target_name})
                            break
                        except ValueError:
                            continue
                    else:
                        self._event(
                            "rewind_spell_unavailable", player=player.index,
                            source="TIME_033", card=spell.card_id, reason=str(exc),
                        )
            return cast
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
        if location.custom_effects:
            self._activate_custom_location(player, location, context_card)
        elif self.rule_registry.dispatch(
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
        elif location.card_id == "FIR_907":
            # Verified from sanitized Power.log: the first activation's
            # script counter advances 1 -> 2.  The number of refreshed Mana
            # Crystals therefore increases by one after each activation.
            self._summon_random_executable_minion(
                player, source_card_id=location.card_id, cost=1,
            )
            self._gain_armor(player, 1)
            self._draw(player)
            refreshed = min(location.next_refresh, player.max_mana - player.mana)
            player.mana += refreshed
            self._event(
                "amirdrassil_activate", player=player.index,
                source=location.entity_id, summoned_cost=1,
                armor=1, drew=1, refreshed=refreshed,
                next_refresh=location.next_refresh + 1,
            )
            location.next_refresh += 1
        elif location.card_id == "TLC_433t2":
            target = (action.target_player, action.target_entity)
            self._deal_to_target(player.index, target, 4, source=context_card)
        location.durability -= 1
        # Locations are dormant for the entire following turn; the next
        # refresh at turn start reduces 2 -> 1, and the subsequent one 1 -> 0.
        location.cooldown = 2
        if location.durability <= 0:
            player.locations.remove(location)
            self._location_deathrattle(player, location)

    def _activate_custom_location(
        self, player: Player, location: Location, source: CardInstance,
    ) -> None:
        """Resolve the currently supported effects of an Elise location."""
        tier = location.custom_tier
        geyser_damage = {1: 1, 5: 3, 10: 5}[tier]
        armor = {1: 3, 5: 6, 10: 12}[tier]
        attack = {1: 1, 5: 2, 10: 4}[tier]
        for effect in location.custom_effects:
            if effect == "bursting_geyser":
                # Bursting Geyser is the location's Deathrattle; it resolves
                # when the location is removed, not on every activation.
                continue
            elif effect == "lava_stream":
                self._gain_armor(player, armor)
            elif effect == "snapping_plants":
                player.hero_attack_bonus += attack
                for minion in player.board:
                    if minion.dormant_turns == 0:
                        minion.attack_delta += attack
                        minion.temporary_attack_modifiers.append((attack, player.index))
            elif effect == "nesting_grounds":
                count = {1: 1, 5: 2, 10: 4}[tier]
                for _ in range(count):
                    if len(player.board) + len(player.locations) >= 7:
                        break
                    raptor = self._entity("TLC_101t", created_by=source.card_id)
                    raptor.summoned_turn = self.turn
                    self._summon(player, raptor)
            elif effect == "radiant_crystals":
                candidates = [m for m in player.board if m.entity_id != source.entity_id]
                if candidates and len(player.board) + len(player.locations) < 7:
                    target = self.rng.choice(candidates)
                    copy = target.clone(self.next_entity_id)
                    self.next_entity_id += 1
                    copy.attack_delta = {1: 1, 5: 3, 10: 5}[tier] - copy.definition.attack
                    copy.health_delta = {1: 1, 5: 3, 10: 5}[tier] - copy.definition.health
                    copy.damage = 0
                    copy.created_by = source.card_id
                    copy.summoned_turn = self.turn
                    self._summon(player, copy)
            elif effect == "runic_inscriptions":
                self._offer_spell_discover(
                    player, source_card_id="TLC_100_CUSTOM",
                    discount={1: 1, 5: 4, 10: 7}[tier],
                )
            elif effect == "shining_moonlight":
                player.next_spell_damage_bonus += {1: 1, 5: 2, 10: 4}[tier]
        self._event(
            "elise_location_activate", player=player.index,
            source=location.entity_id, tier=tier,
            effects=list(location.custom_effects),
        )

    def _location_deathrattle(self, player: Player, location: Location) -> None:
        """Resolve location deathrattles when durability or an effect destroys it."""
        if "bursting_geyser" in location.custom_effects:
            damage = {1: 1, 5: 3, 10: 5}[location.custom_tier]
            source = CardInstance(location.entity_id, self.card_defs[location.card_id])
            for target in self._random_enemy_characters(player.index):
                self._deal_to_target(player.index, target, damage, source=source)
            self._resolve_deaths()
            self._event(
                "elise_bursting_geyser_deathrattle", player=player.index,
                source=location.entity_id, amount=damage,
            )
            return
        if location.card_id == "CATA_527":
            if len(player.board) + len(player.locations) < 7:
                summoned = self._entity("CATA_527t2", created_by=location.card_id)
                summoned.summoned_turn = self.turn
                self._summon(player, summoned)
                self._event(
                    "nespirah_unshackled_summoned", player=player.index,
                    source=location.entity_id, entity=summoned.entity_id,
                )
            return
        if location.card_id == "JAIL_887":
            if len(player.board) + len(player.locations) < 7:
                zuramat = self._entity("JAIL_887t2", created_by=location.card_id)
                zuramat.summoned_turn = self.turn
                self._summon(player, zuramat)
                self._event(
                    "zuramat_freed", player=player.index,
                    source=location.entity_id, entity=zuramat.entity_id,
                )
            return
        if location.card_id != "TLC_433t2":
            return
        if len(player.board) + len(player.locations) >= 7:
            self._event(
                "terror_grave_resummon_blocked", player=player.index,
                source=location.entity_id,
            )
            return
        tyrax = self._entity("TLC_433t", created_by=location.card_id)
        tyrax.summoned_turn = self.turn
        self._summon(player, tyrax)
        self._event(
            "terror_grave_resummon", player=player.index,
            source=location.entity_id, entity=tyrax.entity_id,
        )

    @staticmethod
    def _break_stealth_for_attack(attacker: CardInstance) -> bool:
        """Reveal an attacker and return whether it was stealthed."""
        was_stealthed = attacker.stealth
        attacker.stealth = False
        return was_stealthed

    def _attack(self, action: Action) -> None:
        attacker = self._find_minion(self.current, action.source)
        attacker.attacks_this_turn += 1
        was_stealthed = self._break_stealth_for_attack(attacker)
        if attacker.card_id == "TLC_107" and not attacker.silenced:
            # Stormbrewer hits the declared target before normal combat.
            if action.target_entity is None:
                self._damage_hero(self.players[action.target_player], 3, attacker)
            else:
                target = self._find_minion(action.target_player, action.target_entity)
                self._damage_minion(action.target_player, target, 3, attacker)
                self._resolve_deaths()
        if self._trigger_freezing_trap(
            attacker, self.players[action.target_player]
        ):
            return
        if action.target_entity is None and self._trigger_vaporize(
            attacker, self.players[action.target_player]
        ):
            return
        if action.target_entity is not None:
            defender_player = self.players[action.target_player]
            sacrifice = self._trigger_noble_sacrifice(defender_player)
            target_entity = sacrifice.entity_id if sacrifice is not None else action.target_entity
            self._trigger_snake_trap(defender_player)
        else:
            sacrifice = self._trigger_noble_sacrifice(self.players[action.target_player])
            target_entity = sacrifice.entity_id if sacrifice is not None else None
        if target_entity is None:
            if attacker.card_id == "JAIL_443" and not attacker.silenced:
                enemy = self.players[action.target_player]
                for _ in range(max(0, attacker.attack)):
                    blight = CardInstance(
                        self.next_entity_id,
                        CardDef(
                            "JAIL_442t", "Blight", "SPELL", 1,
                            card_class="DEATHKNIGHT",
                            card_set="ESCAPEFROM_VIOLET_HOLD",
                        ),
                        created_by=attacker.card_id,
                        casts_when_drawn_damage=2,
                    )
                    self.next_entity_id += 1
                    enemy.deck.append(blight)
                self.rng.shuffle(enemy.deck)
                self._event(
                    "living_plague_attack", player=self.current,
                    source=attacker.entity_id, target_player=enemy.index,
                    blights=max(0, attacker.attack),
                )
                self._trigger_secrets_after_hero_attacked(enemy)
                self._after_minion_attack(
                    self.current, attacker,
                    attacked_minion=False, was_stealthed=was_stealthed,
                )
                return
            self._damage_hero(self.players[action.target_player], attacker.attack, attacker)
            self._trigger_secrets_after_hero_attacked(
                self.players[action.target_player]
            )
        else:
            defender = self._find_minion(action.target_player, target_entity)
            attacker.attacking_now = True
            self._damage_minion(action.target_player, defender, attacker.attack, attacker)
            attacker.attacking_now = False
            if defender.health <= 0:
                defender.killed_by_entity = attacker.entity_id
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
            attacked_minion=target_entity is not None,
            was_stealthed=was_stealthed,
        )

    def _hero_attack(self, action: Action) -> None:
        player = self.players[self.current]
        attacked_weapon = copy.deepcopy(player.weapon)
        attack_amount = player.attack
        player.hero_attacks_this_turn += 1
        player.hero_attacks_this_game += 1
        target_entity = action.target_entity
        sacrifice = self._trigger_noble_sacrifice(self.players[action.target_player])
        if sacrifice is not None:
            target_entity = sacrifice.entity_id
        if target_entity is None:
            enemy = self.players[action.target_player]
            before = enemy.health + enemy.armor
            self._damage_hero(self.players[action.target_player], player.attack)
            self._trigger_secrets_after_hero_attacked(
                self.players[action.target_player]
            )
            dealt = before - (enemy.health + enemy.armor)
            self._weapon_lifesteal(player, attacked_weapon, dealt)
            if player.hero_lifesteal_turn == self.turn and dealt > 0:
                player.health = min(player.max_health, player.health + dealt)
                self._event(
                    "hero_lifesteal", player=player.index,
                    amount=dealt,
                )
        else:
            defender = self._find_minion(action.target_player, target_entity)
            before = max(0, defender.health)
            self._damage_minion(action.target_player, defender, player.attack)
            if (
                player.hero_poisonous_until_turn == self.turn
                and defender.health > 0
            ):
                defender.damage = defender.max_health
                self._resolve_deaths()
            if (
                defender.health <= 0
                and player.weapon
                and player.weapon.card_id == "CORE_RLK_086"
            ):
                player.weapon.killed_minions.append(copy.deepcopy(defender.definition))
            dealt = before - max(0, defender.health)
            self._weapon_lifesteal(player, attacked_weapon, dealt)
            if player.hero_lifesteal_turn == self.turn and dealt > 0:
                player.health = min(player.max_health, player.health + dealt)
                self._event(
                    "hero_lifesteal", player=player.index,
                    amount=dealt,
                )
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
            targets = self._random_enemy_minions(player.index)
            if targets:
                self._forced_minion_attack(
                    player.index, basher, enemy.index,
                    self.rng.choice(targets),
                )

    def _damage_hero(self, player: Player, amount: int, source: CardInstance | None = None) -> None:
        attacker = self.players[1 - player.index]
        if amount == 2 and attacker.gorishi_double_damage and self.current == attacker.index:
            amount = 4
        amount = self._modified_damage(amount, source)
        if amount <= 0:
            return
        if player.hero_immune:
            self._event("hero_immune", player=player.index, amount=amount)
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
        health_loss = amount - absorbed
        if (
            health_loss > 0
            and self.current == player.index
            and any(
                minion.card_id == "CATA_155"
                and not minion.silenced
                and minion.dormant_turns == 0
                and minion.health > 0
                for minion in player.board
            )
        ):
            player.max_health += health_loss
            self._event(
                "arisen_onyxia_health_replaced", player=player.index,
                amount=health_loss, source=None if source is None else source.card_id,
            )
            return
        player.health -= health_loss
        if health_loss > 0:
            player.hero_health_changed_this_turn = True
        if player.health <= 0 and player.corpse_rebirth_pending:
            amount = min(20, player.corpses)
            if amount > 0:
                player.corpses -= amount
                player.health = min(player.max_health, amount)
                player.corpse_rebirth_pending = False
                self._event("corpse_rebirth", player=player.index,
                            amount=amount, source=getattr(source, "card_id", None))
        self.players[player.index].damaged_characters_this_turn.add(f"hero:{player.index}")
        if source and source.lifesteal:
            owner = self.players[1 - player.index]
            owner.health = min(owner.max_health, owner.health + amount)
        self._check_warptooth(player.index)

    def _damage_minion(self, player_index: int, minion: CardInstance, amount: int,
                       source: CardInstance | None = None) -> None:
        attacker = self.players[1 - player_index]
        if amount == 2 and attacker.gorishi_double_damage and self.current == attacker.index:
            amount = 4
        # Fyrakk's printed immunity is specifically to damage originating from
        # a Fire *spell*, not to combat or to Fire-named minions.  Do this
        # before damage modifiers and shields so the trace records the real
        # prevention rather than an apparent zero-damage hit.
        if (
            minion.card_id == "FIR_959"
            and source is not None
            and source.definition.card_type == "SPELL"
            and source.definition.spell_school == "FIRE"
        ):
            self._event(
                "fire_spell_immune", player=player_index,
                entity=minion.entity_id, source=source.card_id, amount=amount,
            )
            return
        amount = self._modified_damage(amount, source)
        if minion.card_id == "TIME_060" and not minion.silenced:
            amount *= 2
        if amount <= 0:
            return
        if minion.immune or (minion.immune_while_attacking and minion.attacking_now):
            return
        if minion.divine_shield:
            minion.divine_shield_hits = max(1, minion.divine_shield_hits) - 1
            if minion.divine_shield_hits == 0:
                minion.divine_shield = False
                minion.divine_shield_toreth = False
            return
        health_before_damage = max(0, minion.health)
        minion.damage += amount
        if minion.health <= 0 and source is not None:
            # Preserve the lethal minion for deathrattles such as Faceless
            # Replicator, including non-combat damage caused by a minion.
            minion.killed_by_entity = source.entity_id
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
        if (
            minion.card_id in {"CATA_488t", "CATA_488t2"}
            and not minion.silenced
        ):
            fire_spells = [
                card_id for card_id, definition in self.card_defs.items()
                if card_id in EXECUTABLE_CARD_IDS
                and definition.card_type == "SPELL"
                and definition.spell_school == "FIRE"
            ]
            if fire_spells:
                generated = self._entity(
                    self.rng.choice(sorted(fire_spells)),
                    created_by=minion.card_id,
                )
                generated.cost_delta -= 3
                destination = self._add_generated(
                    self.players[player_index], generated
                )
                self._event(
                    "vulcanos_plume_damaged", player=player_index,
                    source=minion.entity_id, card=generated.card_id,
                    destination=destination,
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
            # Lifesteal uses damage actually dealt, not the printed amount.
            # This matters for overkill and applies correctly when a spell can
            # target either side: a spell source is not on board, so resolve
            # its controller through the regular source-controller helper.
            dealt = health_before_damage - max(0, minion.health)
            owner = self._source_controller(source)
            owner.health = min(owner.max_health, owner.health + dealt)
        # Acolyte of Pain draws after damage is applied, before death
        # processing removes a lethal copy from the board.
        if (
            minion.card_id == "CORE_EX1_007"
            and not minion.silenced
            and minion in self.players[player_index].board
        ):
            self._draw(self.players[player_index])
            self._event(
                "acolyte_of_pain_draw", player=player_index,
                entity=minion.entity_id,
            )
        if minion in self.players[player_index].board:
            self.rule_registry.dispatch(
                Hook.AFTER_DAMAGE, minion.card_id, self,
                RuleContext(
                    player=self.players[player_index], card=minion,
                    payload={"amount": amount, "source": source},
                ),
            )
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
                if minion.has_race("UNDEAD") and player.index != self.current:
                    player.undead_died_after_last_turn = True
                if player.index == self.current:
                    player.friendly_minions_died_this_turn += 1
                player.friendly_minions_died_this_game += 1
                gained = corpse_multipliers[player.index]
                player.corpses += gained
                if gained > 1:
                    self._event(
                        "corpse_multiplier", player=player.index,
                        entity=minion.entity_id, gained=gained,
                    )
                self.minions_died_this_turn += len(dead)

            # Duplicate copies the first friendly corpse twice into hand.
            for owner in self.players:
                corpses = [minion for dead_owner, minion in dead if dead_owner is owner]
                if not corpses:
                    continue
                for secret in list(owner.secrets):
                    if secret.card_id != "FP1_018":
                        continue
                    self._consume_secret(owner, secret)
                    added = 0
                    for _ in range(2):
                        if len(owner.hand) >= 10:
                            break
                        duplicate = corpses[0].clone(self.next_entity_id)
                        self.next_entity_id += 1
                        duplicate.created_by = secret.card_id
                        owner.hand.append(duplicate)
                        added += 1
                    self._event(
                        "duplicate", player=owner.index,
                        source=secret.entity_id, added=added,
                    )

            # Redemption returns the first friendly corpse from this death
            # batch before Deathrattles resolve. The revived copy keeps buffs
            # and keywords but enters with exactly one Health.
            for owner in self.players:
                corpses = [minion for dead_owner, minion in dead if dead_owner is owner]
                if not corpses:
                    continue
                for secret in list(owner.secrets):
                    if secret.card_id != "EX1_136":
                        continue
                    self._consume_secret(owner, secret)
                    if len(owner.board) + len(owner.locations) >= 7:
                        self._event("redemption", player=owner.index, summoned=False)
                        continue
                    revived = corpses[0].clone(self.next_entity_id)
                    self.next_entity_id += 1
                    revived.damage = max(0, revived.max_health - 1)
                    revived.summoned_turn = self.turn
                    revived.created_by = secret.card_id
                    self._summon(owner, revived)
                    self._event(
                        "redemption", player=owner.index,
                        source=secret.entity_id, revived=revived.entity_id,
                    )
                    break

            # Paladin's Avenge resolves once per friendly death batch, before
            # deathrattles, choosing a random surviving friendly minion.
            for owner in self.players:
                if not any(dead_owner is owner for dead_owner, _ in dead):
                    continue
                for secret in list(owner.secrets):
                    if secret.card_id != "CORE_FP1_020":
                        continue
                    self._consume_secret(owner, secret)
                    candidates = [
                        minion for minion in owner.board
                        if minion.dormant_turns == 0 and minion.health > 0
                    ]
                    if not candidates:
                        continue
                    target = self.rng.choice(candidates)
                    target.attack_delta += 3
                    target.health_delta += 2
                    self._event(
                        "avenge", player=owner.index,
                        source=secret.entity_id, target=target.entity_id,
                    )

            # Acolyte of Death observes the completed death batch. Each
            # friendly Undead death produces one draw before deathrattles.
            undead_deaths = {
                player.index: sum(minion.has_race("UNDEAD") for owner, minion in dead if owner.index == player.index)
                for player in self.players
            }
            for player in self.players:
                count = undead_deaths[player.index]
                if not count:
                    continue
                sources = [m for m in player.board if m.card_id == "CORE_RLK_121" and not m.silenced and m.dormant_turns == 0]
                for source in sources:
                    for _ in range(count):
                        self._draw(player)
                        self._event("acolyte_of_death_draw", player=player.index, entity=source.entity_id)

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
                    # Persisting Horror's Dark Gift explicitly reborns with
                    # full health and all enchantments; ordinary Reborn keeps
                    # the engine's standard one-health behavior.
                    reborn.damage = (
                        0
                        if minion.card_id == "CAP_800"
                        or "persisting_horror" in minion.gifts
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
        if minion.deathrattle_damage_all_enemies:
            amount = minion.deathrattle_damage_all_enemies
            opponent = self.players[1 - player.index]
            self._damage_hero(opponent, amount, minion)
            for target in list(opponent.board):
                self._damage_minion(opponent.index, target, amount, minion)
            self._resolve_deaths()
            self._event(
                "deathrattle_damage_all_enemies", player=player.index,
                source=minion.entity_id, amount=amount,
            )
        if minion.card_id == "END_017t":
            opponent = self.players[1 - player.index]
            removed = len(opponent.hand)
            opponent.hand.clear()
            self._event(
                "tick_and_tock_deathrattle", player=player.index,
                source=minion.entity_id, opponent=opponent.index,
                cards_removed=removed,
            )
        if minion.card_id == "JAIL_877t":
            self._draw(player)
            self._event(
                "snoot_hoarder_deathrattle", player=player.index,
                source=minion.entity_id,
            )
        if minion.deathrattle_copy_card_id and len(player.board) + len(player.locations) < 7:
            copied = self._entity(
                minion.deathrattle_copy_card_id, created_by=minion.card_id,
            )
            copied.summoned_turn = self.turn
            self._summon(player, copied)
            self._event(
                "deathrattle_copy_summon", player=player.index,
                source=minion.entity_id, summoned=copied.entity_id,
                card=copied.card_id,
            )
        # Chromatus heads remove exactly their own keyword from the surviving
        # parent.  The parent entity link matters when multiple Chromatuses
        # are present; looking only at the card ID would mutate the wrong one.
        chromatus_keyword = {
            "CATA_432t1": "taunt",
            "CATA_432t2": "lifesteal",
            "CATA_432t3": "elusive",
            "CATA_432t4": "divine_shield",
        }.get(minion.card_id)
        if chromatus_keyword and minion.colossal_parent_entity is not None:
            parent = next(
                (
                    candidate for candidate in player.board
                    if candidate.entity_id == minion.colossal_parent_entity
                    and candidate.card_id == "CATA_432"
                ),
                None,
            )
            if parent is not None:
                setattr(parent, chromatus_keyword, False)
                if chromatus_keyword == "divine_shield":
                    parent.divine_shield_hits = 0
                self._event(
                    "chromatus_head_removed_keyword", player=player.index,
                    source=minion.entity_id, parent=parent.entity_id,
                    keyword=chromatus_keyword,
                )
        if minion.card_id == "TLC_513t2" and player.ninja_shuffle_active:
            returned = self._entity("TLC_513t2", started_in_deck=True,
                                    created_by="TLC_513t")
            player.deck.insert(self.rng.randrange(len(player.deck) + 1), returned)
            self._event("master_dusk_ninja_reshuffled", player=player.index,
                        card=returned.card_id)
        if minion.card_id == "TLC_433t":
            # Tyrax opens Terror's Grave when it dies.  The location occupies
            # a board slot just like every other location and can therefore
            # fail to appear when the controller's board is full.
            if len(player.board) + len(player.locations) < 7:
                grave = self._entity("TLC_433t2", created_by=minion.card_id)
                player.locations.append(
                    Location(grave.entity_id, grave.card_id, grave.definition.health, 2)
                )
                self._event(
                    "terror_grave_opened", player=player.index,
                    source=minion.entity_id, entity=grave.entity_id,
                )
            else:
                self._event(
                    "terror_grave_blocked", player=player.index,
                    source=minion.entity_id,
                )
        if minion.card_id == "TLC_817t5":
            targets = self._random_enemy_characters(player.index)
            if targets:
                self._deal_to_target(
                    player.index, self.rng.choice(targets), 5, source=minion
                )
                self._event(
                    "soletos_deathrattle", player=player.index,
                    source=minion.entity_id, damage=5,
                )
        if minion.card_id == "JAIL_720":
            coin = self._entity("JAIL_COIN1", created_by=minion.card_id)
            destination = self._add_generated(player, coin)
            self._event(
                "lotus_bookie_coin", player=player.index,
                source=minion.entity_id, card=coin.card_id,
                destination=destination,
            )
        if minion.card_id == "END_015" and self._kindred_repeats(player, minion):
            candidates = [
                card_id for card_id in self.executable_card_ids
                if card_id in self.card_defs
                and self.card_defs[card_id].card_type == "MINION"
                and "DEATHRATTLE" in self.card_defs[card_id].mechanics
            ]
            if candidates:
                card = self._entity(self.rng.choice(sorted(candidates)), created_by=minion.card_id)
                card.cost_delta -= 2
                destination = self._add_generated(player, card)
                self._event("triennium_rex_kindred", player=player.index,
                            source=minion.entity_id, card=card.card_id,
                            destination=destination)
        if minion.card_id == "TIME_035":
            rewind_pool = sorted(ADDITIONAL_PLAYABLE_CARD_IDS)
            if rewind_pool:
                card = self._entity(self.rng.choice(rewind_pool), created_by=minion.card_id)
                destination = self._add_generated(player, card)
                self._event(
                    "rewind_card_generated", player=player.index,
                    source=minion.entity_id, card=card.card_id,
                    destination=destination,
                )
        if minion.deathrattle_summon_card_id and len(player.board) + len(player.locations) < 7:
            token = self._entity(
                minion.deathrattle_summon_card_id,
                created_by=minion.card_id,
            )
            token.summoned_turn = self.turn
            self._summon(player, token)
            self._event(
                "deathrattle_summon", player=player.index,
                source=minion.entity_id, summoned=token.entity_id,
                card=token.card_id,
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
            targets = self._random_enemy_minions(player.index)
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
        if action.kind == "DISCARD_PICK":
            option = next(
                card for card in self.pending_choice["options"]
                if card.entity_id == action.source
            )
            return (
                f"P{self.current + 1} DISCARD_PICK "
                f"{option.definition.name}[{option.card_id}]"
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
        if action.kind == "CATACLYSM_PICK":
            card_id = self.pending_choice["options"][action.source]
            return (
                f"P{self.current + 1} CATACLYSM_PICK "
                f"{self.card_defs[card_id].name}[{card_id}]"
            )
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
                "colossal_parent_entity": card.colossal_parent_entity,
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
                "embedded_spell_id": card.embedded_spell_id,
                "prepared_turn": card.prepared_turn,
                "prepared": card.prepared,
                "prepare_granted": card.prepare_granted,
                "dynamic_spell_damage": card.dynamic_spell_damage,
                "spells_cast_while_held": card.spells_cast_while_held,
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
                        ("immune_while_attacking", card.immune_while_attacking),
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
                "next_spell_damage_bonus": player.next_spell_damage_bonus,
                "hero_attacks_this_game": player.hero_attacks_this_game,
                "hero_lifesteal_turn": player.hero_lifesteal_turn,
                "hero_power_cost": self._hero_power_cost(player),
                "hero_power_id": player.hero_power_id,
                "hero_power_armor": player.hero_power_armor,
                "rune_counts": dict(player.rune_counts),
                "undead_died_after_last_turn": player.undead_died_after_last_turn,
                "mograine_active": player.mograine_active,
                "friendly_minions_died_this_turn": player.friendly_minions_died_this_turn,
                "friendly_minions_died_this_game": player.friendly_minions_died_this_game,
                "secrets": [card.card_id for card in player.secrets],
                "pending_end_turn_returns": [
                    card.card_id for card in player.pending_end_turn_returns
                ],
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
                "corpse_rebirth_pending": player.corpse_rebirth_pending,
                "pending_magmaw_bodies": player.pending_magmaw_bodies,
                "overloaded_mana_this_game": player.overloaded_mana_this_game,
                "overload_next_turn": player.overload_next_turn,
                "locked_mana": player.locked_mana,
                "chef_nethrek_turns_remaining": player.chef_nethrek_turns_remaining,
                "next_demon_free": player.next_demon_free,
                "hero_divine_shield": player.hero_divine_shield,
                "hero_divine_shield_hits": player.hero_divine_shield_hits,
                "hero_immune": player.hero_immune,
                "hero_immune_expiry_turn": player.hero_immune_expiry_turn,
                "turns_taken": player.turns_taken,
                "active_quests": {
                    quest_id: {
                        key: (sorted(value) if isinstance(value, set) else value)
                        for key, value in state.items()
                    }
                    for quest_id, state in player.active_quests.items()
                },
                "completed_quests": sorted(player.completed_quests),
                "murloc_quest_buff": player.murloc_quest_buff,
                "gorishi_double_damage": player.gorishi_double_damage,
                "ninja_shuffle_active": player.ninja_shuffle_active,
                "ashalon_adaptations": list(player.ashalon_adaptations),
                "underfel_rift_used_turn": player.underfel_rift_used_turn,
                "origin_stone_triggering": player.origin_stone_triggering,
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
                "void_count": len(player.void_cards),
                "irida_active": player.irida_active,
                "coin_replacement_id": player.coin_replacement_id,
                "holmes_target_card_id": player.holmes_target_card_id,
                "holmes_watch_turn": player.holmes_watch_turn,
                "mug_magic_active": player.mug_magic_active,
                "zee_might_active": player.zee_might_active,
                "zee_might_minions_played": player.zee_might_minions_played,
                "dead_minions": [card.card_id for card in player.dead_minions],
                "board": [card_state(card, player) for card in player.board],
                "locations": [
                    {"entity": x.entity_id, "id": x.card_id,
                     "durability": x.durability, "cooldown": x.cooldown,
                     "next_refresh": x.next_refresh,
                     "custom_effects": list(x.custom_effects),
                     "custom_tier": x.custom_tier}
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
                "DISCOVER", "GEDDON_DRAW", "DECK_CARD_DISCOVER", "IMBUE_PICK",
                "INTERTWINED_FATE", "INTERTWINED_FATE_OPPONENT",
            }:
                pending["options"] = [
                    card_state(card, self.players[self.current])
                    for card in self.pending_choice["options"]
                ]
            elif self.pending_choice["kind"] == "REWIND":
                pending["options"] = ["REWIND_KEEP", "REWIND_RETRY"]
            elif self.pending_choice["kind"] == "RULE_CHOICE":
                pending["player"] = self.pending_choice["player"] + 1
                pending["source_card"] = self.pending_choice["card"].card_id
                pending["options"] = [
                    label for label, _ in self.pending_choice["options"]
                ]
                if "option_metadata" in self.pending_choice:
                    pending["option_metadata"] = list(
                        self.pending_choice["option_metadata"]
                    )
            elif self.pending_choice["kind"] == "DEATHWING_CATACLYSM":
                pending["remaining"] = self.pending_choice["remaining"]
                pending["options"] = [
                    {
                        "id": card_id,
                        "name": self.card_defs[card_id].name,
                    }
                    for card_id in self.pending_choice["options"]
                ]
            else:
                pending["options"] = list(self.pending_choice["options"])
        return {
            "turn": self.turn,
            "active_player": self.current + 1,
            "first_player": self.first_player + 1,
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

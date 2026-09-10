# Dragon Warrior mirror trace

- Seed: `202609080001`
- Profile: `closed_generation_pools`
- Winner: `P2`
- Actions: `151`
- Illegal actions: `0`

## Step 1 — turn 0

`P1 MULLIGAN_REPLACE Windpeak Wyrm[TLC_600]`

Legal choices before action: 4

Events:

- `{"entity": 12, "kind": "mulligan_toggle", "player": 0, "replace": true, "turn": 0}`

- P1: HP=30 Armor=0 Mana=0/0 Deck=27; Weapon=none; Board=empty; Locations=none; Hand=Windpeak Wyrm(8), Hook n' Heave(2), Carrier Whelp(1)
- P2: HP=30 Armor=0 Mana=0/0 Deck=26; Weapon=none; Board=empty; Locations=none; Hand=Carrier Whelp(1), Sanguine Depths(1), Prescient Slitherdrake(4), Prescient Slitherdrake(4)
- Pending decision: `{"kind": "MULLIGAN", "options": [{"attack": 6, "burning_turns": 0, "cant_attack": false, "cant_attack_heroes_turn": -1, "card_class": "WARRIOR", "card_set": "THE_LOST_CITY", "cost": 8, "created_by": null, "damage": 0, "divine_shield_hits": 0, "dormant_turns": 0, "dynamic_spell_damage": 0, "entity": 12, "frozen": false, "gifts": [], "health": 6, "herald_power": 1, "id": "TLC_600", "illusion_fake": false, "infinite_attack_next_turn": false, "keywords": [], "max_health": 6, "mirrex_tracker": false, "name": "Windpeak Wyrm", "omen_damage": 1, "played_turn": -1, "prepared_turn": -1, "races": ["DRAGON"], "replace": true, "spell_damage_bonus": 0, "started_in_deck": true, "summon_moragg_on_death": false, "summoned_when_drawn": false, "twilight_whelp_bonus": 0, "void_soul_cost": 0}, {"attack": 0, "burning_turns": 0, "cant_attack": false, "cant_attack_heroes_turn": -1, "card_class": "WARRIOR", "card_set": "ESCAPEFROM_VIOLET_HOLD", "cost": 2, "created_by": null, "damage": 0, "divine_shield_hits": 0, "dormant_turns": 0, "dynamic_spell_damage": 0, "entity": 27, "frozen": false, "gifts": [], "health": 0, "herald_power": 1, "id": "CAP_105", "illusion_fake": false, "infinite_attack_next_turn": false, "keywords": [], "max_health": 0, "mirrex_tracker": false, "name": "Hook n' Heave", "omen_damage": 1, "played_turn": -1, "prepared_turn": -1, "races": [], "replace": false, "spell_damage_bonus": 0, "started_in_deck": true, "summon_moragg_on_death": false, "summoned_when_drawn": false, "twilight_whelp_bonus": 0, "void_soul_cost": 0}, {"attack": 1, "burning_turns": 0, "cant_attack": false, "cant_attack_heroes_turn": -1, "card_class": "NEUTRAL", "card_set": "CATACLYSM", "cost": 1, "created_by": null, "damage": 0, "divine_shield_hits": 0, "dormant_turns": 0, "dynamic_spell_damage": 0, "entity": 17, "frozen": false, "gifts": [], "health": 2, "herald_power": 1, "id": "CATA_556", "illusion_fake": false, "infinite_attack_next_turn": false, "keywords": [], "max_health": 2, "mirrex_tracker": false, "name": "Carrier Whelp", "omen_damage": 1, "played_turn": -1, "prepared_turn": -1, "races": ["DRAGON"], "replace": false, "spell_damage_bonus": 0, "started_in_deck": true, "summon_moragg_on_death": false, "summoned_when_drawn": false, "twilight_whelp_bonus": 0, "void_soul_cost": 0}], "player": 1}`

## Step 2 — turn 0

`P1 MULLIGAN_CONFIRM`

Legal choices before action: 4

Events:

- `{"kept": ["CAP_105", "CATA_556"], "kind": "mulligan_result", "player": 0, "replaced": ["TLC_600"], "replacements": ["EDR_457"], "turn": 0}`
- `{"cards": ["CATA_556", "CORE_REV_990", "END_033", "END_033"], "entities": [47, 32, 45, 46], "kind": "mulligan_offer", "player": 1, "turn": 0}`

- P1: HP=30 Armor=0 Mana=0/0 Deck=27; Weapon=none; Board=empty; Locations=none; Hand=Hook n' Heave(2), Carrier Whelp(1), Brood Keeper(2)
- P2: HP=30 Armor=0 Mana=0/0 Deck=26; Weapon=none; Board=empty; Locations=none; Hand=Carrier Whelp(1), Sanguine Depths(1), Prescient Slitherdrake(4), Prescient Slitherdrake(4)
- Pending decision: `{"kind": "MULLIGAN", "options": [{"attack": 1, "burning_turns": 0, "cant_attack": false, "cant_attack_heroes_turn": -1, "card_class": "NEUTRAL", "card_set": "CATACLYSM", "cost": 1, "created_by": null, "damage": 0, "divine_shield_hits": 0, "dormant_turns": 0, "dynamic_spell_damage": 0, "entity": 47, "frozen": false, "gifts": [], "health": 2, "herald_power": 1, "id": "CATA_556", "illusion_fake": false, "infinite_attack_next_turn": false, "keywords": [], "max_health": 2, "mirrex_tracker": false, "name": "Carrier Whelp", "omen_damage": 1, "played_turn": -1, "prepared_turn": -1, "races": ["DRAGON"], "replace": false, "spell_damage_bonus": 0, "started_in_deck": true, "summon_moragg_on_death": false, "summoned_when_drawn": false, "twilight_whelp_bonus": 0, "void_soul_cost": 0}, {"attack": 0, "burning_turns": 0, "cant_attack": false, "cant_attack_heroes_turn": -1, "card_class": "WARRIOR", "card_set": "CORE", "cost": 1, "created_by": null, "damage": 0, "divine_shield_hits": 0, "dormant_turns": 0, "dynamic_spell_damage": 0, "entity": 32, "frozen": false, "gifts": [], "health": 3, "herald_power": 1, "id": "CORE_REV_990", "illusion_fake": false, "infinite_attack_next_turn": false, "keywords": [], "max_health": 3, "mirrex_tracker": false, "name": "Sanguine Depths", "omen_damage": 1, "played_turn": -1, "prepared_turn": -1, "races": [], "replace": false, "spell_damage_bonus": 0, "started_in_deck": true, "summon_moragg_on_death": false, "summoned_when_drawn": false, "twilight_whelp_bonus": 0, "void_soul_cost": 0}, {"attack": 5, "burning_turns": 0, "cant_attack": false, "cant_attack_heroes_turn": -1, "card_class": "NEUTRAL", "card_set": "TIME_TRAVEL", "cost": 4, "created_by": null, "damage": 0, "divine_shield_hits": 0, "dormant_turns": 0, "dynamic_spell_damage": 0, "entity": 45, "frozen": false, "gifts": [], "health": 8, "herald_power": 1, "id": "END_033", "illusion_fake": false, "infinite_attack_next_turn": false, "keywords": ["elusive"], "max_health": 8, "mirrex_tracker": false, "name": "Prescient Slitherdrake", "omen_damage": 1, "played_turn": -1, "prepared_turn": -1, "races": ["DRAGON"], "replace": false, "spell_damage_bonus": 0, "started_in_deck": true, "summon_moragg_on_death": false, "summoned_when_drawn": false, "twilight_whelp_bonus": 0, "void_soul_cost": 0}, {"attack": 5, "burning_turns": 0, "cant_attack": false, "cant_attack_heroes_turn": -1, "card_class": "NEUTRAL", "card_set": "TIME_TRAVEL", "cost": 4, "created_by": null, "damage": 0, "divine_shield_hits": 0, "dormant_turns": 0, "dynamic_spell_damage": 0, "entity": 46, "frozen": false, "gifts": [], "health": 8, "herald_power": 1, "id": "END_033", "illusion_fake": false, "infinite_attack_next_turn": false, "keywords": ["elusive"], "max_health": 8, "mirrex_tracker": false, "name": "Prescient Slitherdrake", "omen_damage": 1, "played_turn": -1, "prepared_turn": -1, "races": ["DRAGON"], "replace": false, "spell_damage_bonus": 0, "started_in_deck": true, "summon_moragg_on_death": false, "summoned_when_drawn": false, "twilight_whelp_bonus": 0, "void_soul_cost": 0}], "player": 2}`

## Step 3 — turn 0

`P2 MULLIGAN_REPLACE Prescient Slitherdrake[END_033]`

Legal choices before action: 5

Events:

- `{"entity": 45, "kind": "mulligan_toggle", "player": 1, "replace": true, "turn": 0}`

- P1: HP=30 Armor=0 Mana=0/0 Deck=27; Weapon=none; Board=empty; Locations=none; Hand=Hook n' Heave(2), Carrier Whelp(1), Brood Keeper(2)
- P2: HP=30 Armor=0 Mana=0/0 Deck=26; Weapon=none; Board=empty; Locations=none; Hand=Carrier Whelp(1), Sanguine Depths(1), Prescient Slitherdrake(4), Prescient Slitherdrake(4)
- Pending decision: `{"kind": "MULLIGAN", "options": [{"attack": 1, "burning_turns": 0, "cant_attack": false, "cant_attack_heroes_turn": -1, "card_class": "NEUTRAL", "card_set": "CATACLYSM", "cost": 1, "created_by": null, "damage": 0, "divine_shield_hits": 0, "dormant_turns": 0, "dynamic_spell_damage": 0, "entity": 47, "frozen": false, "gifts": [], "health": 2, "herald_power": 1, "id": "CATA_556", "illusion_fake": false, "infinite_attack_next_turn": false, "keywords": [], "max_health": 2, "mirrex_tracker": false, "name": "Carrier Whelp", "omen_damage": 1, "played_turn": -1, "prepared_turn": -1, "races": ["DRAGON"], "replace": false, "spell_damage_bonus": 0, "started_in_deck": true, "summon_moragg_on_death": false, "summoned_when_drawn": false, "twilight_whelp_bonus": 0, "void_soul_cost": 0}, {"attack": 0, "burning_turns": 0, "cant_attack": false, "cant_attack_heroes_turn": -1, "card_class": "WARRIOR", "card_set": "CORE", "cost": 1, "created_by": null, "damage": 0, "divine_shield_hits": 0, "dormant_turns": 0, "dynamic_spell_damage": 0, "entity": 32, "frozen": false, "gifts": [], "health": 3, "herald_power": 1, "id": "CORE_REV_990", "illusion_fake": false, "infinite_attack_next_turn": false, "keywords": [], "max_health": 3, "mirrex_tracker": false, "name": "Sanguine Depths", "omen_damage": 1, "played_turn": -1, "prepared_turn": -1, "races": [], "replace": false, "spell_damage_bonus": 0, "started_in_deck": true, "summon_moragg_on_death": false, "summoned_when_drawn": false, "twilight_whelp_bonus": 0, "void_soul_cost": 0}, {"attack": 5, "burning_turns": 0, "cant_attack": false, "cant_attack_heroes_turn": -1, "card_class": "NEUTRAL", "card_set": "TIME_TRAVEL", "cost": 4, "created_by": null, "damage": 0, "divine_shield_hits": 0, "dormant_turns": 0, "dynamic_spell_damage": 0, "entity": 45, "frozen": false, "gifts": [], "health": 8, "herald_power": 1, "id": "END_033", "illusion_fake": false, "infinite_attack_next_turn": false, "keywords": ["elusive"], "max_health": 8, "mirrex_tracker": false, "name": "Prescient Slitherdrake", "omen_damage": 1, "played_turn": -1, "prepared_turn": -1, "races": ["DRAGON"], "replace": true, "spell_damage_bonus": 0, "started_in_deck": true, "summon_moragg_on_death": false, "summoned_when_drawn": false, "twilight_whelp_bonus": 0, "void_soul_cost": 0}, {"attack": 5, "burning_turns": 0, "cant_attack": false, "cant_attack_heroes_turn": -1, "card_class": "NEUTRAL", "card_set": "TIME_TRAVEL", "cost": 4, "created_by": null, "damage": 0, "divine_shield_hits": 0, "dormant_turns": 0, "dynamic_spell_damage": 0, "entity": 46, "frozen": false, "gifts": [], "health": 8, "herald_power": 1, "id": "END_033", "illusion_fake": false, "infinite_attack_next_turn": false, "keywords": ["elusive"], "max_health": 8, "mirrex_tracker": false, "name": "Prescient Slitherdrake", "omen_damage": 1, "played_turn": -1, "prepared_turn": -1, "races": ["DRAGON"], "replace": false, "spell_damage_bonus": 0, "started_in_deck": true, "summon_moragg_on_death": false, "summoned_when_drawn": false, "twilight_whelp_bonus": 0, "void_soul_cost": 0}], "player": 2}`

## Step 4 — turn 0

`P2 MULLIGAN_REPLACE Prescient Slitherdrake[END_033]`

Legal choices before action: 5

Events:

- `{"entity": 46, "kind": "mulligan_toggle", "player": 1, "replace": true, "turn": 0}`

- P1: HP=30 Armor=0 Mana=0/0 Deck=27; Weapon=none; Board=empty; Locations=none; Hand=Hook n' Heave(2), Carrier Whelp(1), Brood Keeper(2)
- P2: HP=30 Armor=0 Mana=0/0 Deck=26; Weapon=none; Board=empty; Locations=none; Hand=Carrier Whelp(1), Sanguine Depths(1), Prescient Slitherdrake(4), Prescient Slitherdrake(4)
- Pending decision: `{"kind": "MULLIGAN", "options": [{"attack": 1, "burning_turns": 0, "cant_attack": false, "cant_attack_heroes_turn": -1, "card_class": "NEUTRAL", "card_set": "CATACLYSM", "cost": 1, "created_by": null, "damage": 0, "divine_shield_hits": 0, "dormant_turns": 0, "dynamic_spell_damage": 0, "entity": 47, "frozen": false, "gifts": [], "health": 2, "herald_power": 1, "id": "CATA_556", "illusion_fake": false, "infinite_attack_next_turn": false, "keywords": [], "max_health": 2, "mirrex_tracker": false, "name": "Carrier Whelp", "omen_damage": 1, "played_turn": -1, "prepared_turn": -1, "races": ["DRAGON"], "replace": false, "spell_damage_bonus": 0, "started_in_deck": true, "summon_moragg_on_death": false, "summoned_when_drawn": false, "twilight_whelp_bonus": 0, "void_soul_cost": 0}, {"attack": 0, "burning_turns": 0, "cant_attack": false, "cant_attack_heroes_turn": -1, "card_class": "WARRIOR", "card_set": "CORE", "cost": 1, "created_by": null, "damage": 0, "divine_shield_hits": 0, "dormant_turns": 0, "dynamic_spell_damage": 0, "entity": 32, "frozen": false, "gifts": [], "health": 3, "herald_power": 1, "id": "CORE_REV_990", "illusion_fake": false, "infinite_attack_next_turn": false, "keywords": [], "max_health": 3, "mirrex_tracker": false, "name": "Sanguine Depths", "omen_damage": 1, "played_turn": -1, "prepared_turn": -1, "races": [], "replace": false, "spell_damage_bonus": 0, "started_in_deck": true, "summon_moragg_on_death": false, "summoned_when_drawn": false, "twilight_whelp_bonus": 0, "void_soul_cost": 0}, {"attack": 5, "burning_turns": 0, "cant_attack": false, "cant_attack_heroes_turn": -1, "card_class": "NEUTRAL", "card_set": "TIME_TRAVEL", "cost": 4, "created_by": null, "damage": 0, "divine_shield_hits": 0, "dormant_turns": 0, "dynamic_spell_damage": 0, "entity": 45, "frozen": false, "gifts": [], "health": 8, "herald_power": 1, "id": "END_033", "illusion_fake": false, "infinite_attack_next_turn": false, "keywords": ["elusive"], "max_health": 8, "mirrex_tracker": false, "name": "Prescient Slitherdrake", "omen_damage": 1, "played_turn": -1, "prepared_turn": -1, "races": ["DRAGON"], "replace": true, "spell_damage_bonus": 0, "started_in_deck": true, "summon_moragg_on_death": false, "summoned_when_drawn": false, "twilight_whelp_bonus": 0, "void_soul_cost": 0}, {"attack": 5, "burning_turns": 0, "cant_attack": false, "cant_attack_heroes_turn": -1, "card_class": "NEUTRAL", "card_set": "TIME_TRAVEL", "cost": 4, "created_by": null, "damage": 0, "divine_shield_hits": 0, "dormant_turns": 0, "dynamic_spell_damage": 0, "entity": 46, "frozen": false, "gifts": [], "health": 8, "herald_power": 1, "id": "END_033", "illusion_fake": false, "infinite_attack_next_turn": false, "keywords": ["elusive"], "max_health": 8, "mirrex_tracker": false, "name": "Prescient Slitherdrake", "omen_damage": 1, "played_turn": -1, "prepared_turn": -1, "races": ["DRAGON"], "replace": true, "spell_damage_bonus": 0, "started_in_deck": true, "summon_moragg_on_death": false, "summoned_when_drawn": false, "twilight_whelp_bonus": 0, "void_soul_cost": 0}], "player": 2}`

## Step 5 — turn 1

`P2 MULLIGAN_CONFIRM`

Legal choices before action: 5

Events:

- `{"kept": ["CATA_556", "CORE_REV_990"], "kind": "mulligan_result", "player": 1, "replaced": ["END_033", "END_033"], "replacements": ["EDR_492", "CATA_584"], "turn": 0}`
- `{"entity": 61, "kind": "coin_given", "player": 1, "source": "MULLIGAN", "turn": 0}`
- `{"card": "JAIL_384", "duplicated": "JAIL_421", "kind": "start_of_game", "player": 0, "turn": 0}`
- `{"card": "JAIL_384", "duplicated": "JAIL_421", "kind": "start_of_game", "player": 1, "turn": 0}`
- `{"card": "EDR_492", "kind": "draw", "player": 0, "turn": 1}`
- `{"kind": "turn_start", "player": 0, "turn": 1}`

- P1: HP=30 Armor=0 Mana=1/1 Deck=27; Weapon=none; Board=empty; Locations=none; Hand=Hook n' Heave(2), Carrier Whelp(1), Brood Keeper(2), Mother Duck(4)
- P2: HP=30 Armor=0 Mana=0/0 Deck=27; Weapon=none; Board=empty; Locations=none; Hand=Carrier Whelp(1), Sanguine Depths(1), Mother Duck(4), Erupting Volcano(3), The Coin(0)

## Step 6 — turn 1

`P1 PLAY Carrier Whelp[CATA_556] -> -`

Legal choices before action: 2

Events:

- `{"card": "CATA_556", "controller": 0, "kind": "play", "player": 0, "turn": 1}`
- `{"card": "CATA_556", "entity": 64, "kind": "generated_to_hand", "player": 0, "source": "CATA_556", "turn": 1}`

- P1: HP=30 Armor=0 Mana=0/1 Deck=27; Weapon=none; Board=Carrier Whelp#17 1/2; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Carrier Whelp(1)
- P2: HP=30 Armor=0 Mana=0/0 Deck=27; Weapon=none; Board=empty; Locations=none; Hand=Carrier Whelp(1), Sanguine Depths(1), Mother Duck(4), Erupting Volcano(3), The Coin(0)

## Step 7 — turn 2

`P1 END_TURN`

Legal choices before action: 1

Events:

- `{"kind": "turn_end", "player": 0, "turn": 1}`
- `{"card": "TLC_600", "kind": "draw", "player": 1, "turn": 2}`
- `{"kind": "turn_start", "player": 1, "turn": 2}`

- P1: HP=30 Armor=0 Mana=0/1 Deck=27; Weapon=none; Board=Carrier Whelp#17 1/2; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Carrier Whelp(1)
- P2: HP=30 Armor=0 Mana=1/1 Deck=26; Weapon=none; Board=empty; Locations=none; Hand=Carrier Whelp(1), Sanguine Depths(1), Mother Duck(4), Erupting Volcano(3), The Coin(0), Windpeak Wyrm(8)

## Step 8 — turn 2

`P2 PLAY Carrier Whelp[CATA_556] -> -`

Legal choices before action: 4

Events:

- `{"card": "CATA_556", "controller": 1, "kind": "play", "player": 1, "turn": 2}`
- `{"card": "CATA_556", "entity": 65, "kind": "generated_to_hand", "player": 1, "source": "CATA_556", "turn": 2}`

- P1: HP=30 Armor=0 Mana=0/1 Deck=27; Weapon=none; Board=Carrier Whelp#17 1/2; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Carrier Whelp(1)
- P2: HP=30 Armor=0 Mana=0/1 Deck=26; Weapon=none; Board=Carrier Whelp#47 1/2; Locations=none; Hand=Sanguine Depths(1), Mother Duck(4), Erupting Volcano(3), The Coin(0), Windpeak Wyrm(8), Carrier Whelp(1)

## Step 9 — turn 2

`P2 PLAY The Coin[GAME_005] -> -`

Legal choices before action: 2

Events:

- `{"card": "GAME_005", "controller": 1, "kind": "play", "player": 1, "turn": 2}`

- P1: HP=30 Armor=0 Mana=0/1 Deck=27; Weapon=none; Board=Carrier Whelp#17 1/2; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Carrier Whelp(1)
- P2: HP=30 Armor=0 Mana=1/1 Deck=26; Weapon=none; Board=Carrier Whelp#47 1/2; Locations=none; Hand=Sanguine Depths(1), Mother Duck(4), Erupting Volcano(3), Windpeak Wyrm(8), Carrier Whelp(1)

## Step 10 — turn 3

`P2 END_TURN`

Legal choices before action: 3

Events:

- `{"kind": "turn_end", "player": 1, "turn": 2}`
- `{"card": "JAIL_421", "kind": "draw", "player": 0, "turn": 3}`
- `{"kind": "turn_start", "player": 0, "turn": 3}`

- P1: HP=30 Armor=0 Mana=2/2 Deck=26; Weapon=none; Board=Carrier Whelp#17 1/2; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Carrier Whelp(1), Warptooth(4)
- P2: HP=30 Armor=0 Mana=1/1 Deck=26; Weapon=none; Board=Carrier Whelp#47 1/2; Locations=none; Hand=Sanguine Depths(1), Mother Duck(4), Erupting Volcano(3), Windpeak Wyrm(5), Carrier Whelp(1)

## Step 11 — turn 3

`P1 PLAY Carrier Whelp[CATA_556] -> -`

Legal choices before action: 7

Events:

- `{"card": "CATA_556", "controller": 0, "kind": "play", "player": 0, "turn": 3}`
- `{"card": "CATA_556", "entity": 66, "kind": "generated_to_hand", "player": 0, "source": "CATA_556", "turn": 3}`

- P1: HP=30 Armor=0 Mana=1/2 Deck=26; Weapon=none; Board=Carrier Whelp#17 1/2, Carrier Whelp#64 1/2; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Warptooth(4), Carrier Whelp(1)
- P2: HP=30 Armor=0 Mana=1/1 Deck=26; Weapon=none; Board=Carrier Whelp#47 1/2; Locations=none; Hand=Sanguine Depths(1), Mother Duck(4), Erupting Volcano(3), Windpeak Wyrm(5), Carrier Whelp(1)

## Step 12 — turn 3

`P1 PLAY Carrier Whelp[CATA_556] -> -`

Legal choices before action: 4

Events:

- `{"card": "CATA_556", "controller": 0, "kind": "play", "player": 0, "turn": 3}`
- `{"card": "CATA_556", "entity": 67, "kind": "generated_to_hand", "player": 0, "source": "CATA_556", "turn": 3}`

- P1: HP=30 Armor=0 Mana=0/2 Deck=26; Weapon=none; Board=Carrier Whelp#17 1/2, Carrier Whelp#64 1/2, Carrier Whelp#66 1/2; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Warptooth(4), Carrier Whelp(1)
- P2: HP=30 Armor=0 Mana=1/1 Deck=26; Weapon=none; Board=Carrier Whelp#47 1/2; Locations=none; Hand=Sanguine Depths(1), Mother Duck(4), Erupting Volcano(3), Windpeak Wyrm(5), Carrier Whelp(1)

## Step 13 — turn 3

`P1 ATTACK Carrier Whelp#17 -> P2 Carrier Whelp#47`

Legal choices before action: 3

- P1: HP=30 Armor=0 Mana=0/2 Deck=26; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/2; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Warptooth(4), Carrier Whelp(1)
- P2: HP=30 Armor=0 Mana=1/1 Deck=26; Weapon=none; Board=Carrier Whelp#47 1/1; Locations=none; Hand=Sanguine Depths(1), Mother Duck(4), Erupting Volcano(3), Windpeak Wyrm(5), Carrier Whelp(1)

## Step 14 — turn 4

`P1 END_TURN`

Legal choices before action: 1

Events:

- `{"kind": "turn_end", "player": 0, "turn": 3}`
- `{"card": "FIR_939", "kind": "draw", "player": 1, "turn": 4}`
- `{"kind": "turn_start", "player": 1, "turn": 4}`

- P1: HP=30 Armor=0 Mana=0/2 Deck=26; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/2; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Warptooth(4), Carrier Whelp(1)
- P2: HP=30 Armor=0 Mana=2/2 Deck=25; Weapon=none; Board=Carrier Whelp#47 1/1; Locations=none; Hand=Sanguine Depths(1), Mother Duck(4), Erupting Volcano(3), Windpeak Wyrm(5), Carrier Whelp(1), Shadowflame Suffusion(2)

## Step 15 — turn 4

`P2 ATTACK Carrier Whelp#47 -> P1 Carrier Whelp#66`

Legal choices before action: 14

Events:

- `{"card": "CATA_556", "entity": 47, "kind": "minion_died", "player": 1, "turn": 4}`

- P1: HP=30 Armor=0 Mana=0/2 Deck=26; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Warptooth(4), Carrier Whelp(1)
- P2: HP=30 Armor=0 Mana=2/2 Deck=25; Weapon=none; Board=empty; Locations=none; Hand=Sanguine Depths(1), Mother Duck(4), Erupting Volcano(3), Windpeak Wyrm(5), Carrier Whelp(1), Shadowflame Suffusion(2)

## Step 16 — turn 4

`P2 PLAY Shadowflame Suffusion[FIR_939] -> P1 hero`

Legal choices before action: 9

Events:

- `{"card": "FIR_939", "controller": 1, "kind": "play", "player": 1, "turn": 4}`
- `{"kind": "discover_offer", "options": [{"card": "EDR_468", "entity": 68, "gifts": ["living_nightmare"]}, {"card": "DINO_400", "entity": 69, "gifts": ["persisting_horror"]}, {"card": "DINO_401", "entity": 70, "gifts": ["harpys_talons"]}], "player": 1, "profile": "closed_pool", "turn": 4}`

- P1: HP=28 Armor=0 Mana=0/2 Deck=26; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Warptooth(4), Carrier Whelp(1)
- P2: HP=30 Armor=0 Mana=0/2 Deck=25; Weapon=none; Board=empty; Locations=none; Hand=Sanguine Depths(1), Mother Duck(4), Erupting Volcano(3), Windpeak Wyrm(5), Carrier Whelp(1)
- Pending decision: `{"kind": "DISCOVER", "options": [{"attack": 3, "burning_turns": 0, "cant_attack": false, "cant_attack_heroes_turn": -1, "card_class": "WARRIOR", "card_set": "EMERALD_DREAM", "cost": 4, "created_by": "FIR_939", "damage": 0, "divine_shield_hits": 0, "dormant_turns": 0, "dynamic_spell_damage": 0, "entity": 68, "frozen": false, "gifts": ["living_nightmare"], "health": 5, "herald_power": 1, "id": "EDR_468", "illusion_fake": false, "infinite_attack_next_turn": false, "keywords": [], "max_health": 5, "mirrex_tracker": false, "name": "Eggbasher", "omen_damage": 1, "played_turn": -1, "prepared_turn": -1, "races": [], "spell_damage_bonus": 0, "started_in_deck": false, "summon_moragg_on_death": false, "summoned_when_drawn": false, "twilight_whelp_bonus": 0, "void_soul_cost": 0}, {"attack": 4, "burning_turns": 0, "cant_attack": false, "cant_attack_heroes_turn": -1, "card_class": "WARRIOR", "card_set": "THE_LOST_CITY", "cost": 3, "created_by": "FIR_939", "damage": 0, "divine_shield_hits": 0, "dormant_turns": 0, "dynamic_spell_damage": 0, "entity": 69, "frozen": false, "gifts": ["persisting_horror"], "health": 3, "herald_power": 1, "id": "DINO_400", "illusion_fake": false, "infinite_attack_next_turn": false, "keywords": ["reborn"], "max_health": 3, "mirrex_tracker": false, "name": "Barricade Basher", "omen_damage": 1, "played_turn": -1, "prepared_turn": -1, "races": ["BEAST"], "spell_damage_bonus": 0, "started_in_deck": false, "summon_moragg_on_death": false, "summoned_when_drawn": false, "twilight_whelp_bonus": 0, "void_soul_cost": 0}, {"attack": 5, "burning_turns": 0, "cant_attack": false, "cant_attack_heroes_turn": -1, "card_class": "WARRIOR", "card_set": "THE_LOST_CITY", "cost": 8, "created_by": "FIR_939", "damage": 0, "divine_shield_hits": 0, "dormant_turns": 0, "dynamic_spell_damage": 0, "entity": 70, "frozen": false, "gifts": ["harpys_talons"], "health": 12, "herald_power": 1, "id": "DINO_401", "illusion_fake": false, "infinite_attack_next_turn": false, "keywords": ["rush", "divine_shield", "windfury"], "max_health": 12, "mirrex_tracker": false, "name": "The Great Dracorex", "omen_damage": 1, "played_turn": -1, "prepared_turn": -1, "races": ["BEAST", "DRAGON"], "spell_damage_bonus": 0, "started_in_deck": false, "summon_moragg_on_death": false, "summoned_when_drawn": false, "twilight_whelp_bonus": 0, "void_soul_cost": 0}]}`

## Step 17 — turn 4

`P2 DISCOVER_PICK The Great Dracorex[DINO_401] + harpys_talons`

Legal choices before action: 3

Events:

- `{"card": "DINO_401", "entity": 70, "gifts": ["harpys_talons"], "kind": "discover_pick", "player": 1, "turn": 4}`

- P1: HP=28 Armor=0 Mana=0/2 Deck=26; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Warptooth(4), Carrier Whelp(1)
- P2: HP=30 Armor=0 Mana=0/2 Deck=25; Weapon=none; Board=empty; Locations=none; Hand=Sanguine Depths(1), Mother Duck(4), Erupting Volcano(3), Windpeak Wyrm(5), Carrier Whelp(1), The Great Dracorex(8)

## Step 18 — turn 5

`P2 END_TURN`

Legal choices before action: 1

Events:

- `{"kind": "turn_end", "player": 1, "turn": 4}`
- `{"card": "CATA_585", "kind": "draw", "player": 0, "turn": 5}`
- `{"kind": "turn_start", "player": 0, "turn": 5}`

- P1: HP=28 Armor=0 Mana=3/3 Deck=25; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Warptooth(4), Carrier Whelp(1), Torch(1)
- P2: HP=30 Armor=0 Mana=0/2 Deck=25; Weapon=none; Board=empty; Locations=none; Hand=Sanguine Depths(1), Mother Duck(4), Erupting Volcano(3), Windpeak Wyrm(8), Carrier Whelp(1), The Great Dracorex(8)

## Step 19 — turn 5

`P1 ATTACK Carrier Whelp#17 -> P2 hero`

Legal choices before action: 10

- P1: HP=28 Armor=0 Mana=3/3 Deck=25; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Warptooth(4), Carrier Whelp(1), Torch(1)
- P2: HP=29 Armor=0 Mana=0/2 Deck=25; Weapon=none; Board=empty; Locations=none; Hand=Sanguine Depths(1), Mother Duck(4), Erupting Volcano(3), Windpeak Wyrm(8), Carrier Whelp(1), The Great Dracorex(8)

## Step 20 — turn 5

`P1 HERO_POWER Armor Up`

Legal choices before action: 9

Events:

- `{"amount": 2, "kind": "gain_armor", "player": 0, "turn": 5}`
- `{"kind": "hero_power", "player": 0, "turn": 5}`

- P1: HP=28 Armor=2 Mana=1/3 Deck=25; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Warptooth(4), Carrier Whelp(1), Torch(1)
- P2: HP=29 Armor=0 Mana=0/2 Deck=25; Weapon=none; Board=empty; Locations=none; Hand=Sanguine Depths(1), Mother Duck(4), Erupting Volcano(3), Windpeak Wyrm(8), Carrier Whelp(1), The Great Dracorex(8)

## Step 21 — turn 6

`P1 END_TURN`

Legal choices before action: 6

Events:

- `{"kind": "turn_end", "player": 0, "turn": 5}`
- `{"card": "EDR_492", "kind": "draw", "player": 1, "turn": 6}`
- `{"kind": "turn_start", "player": 1, "turn": 6}`

- P1: HP=28 Armor=2 Mana=1/3 Deck=25; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Warptooth(4), Carrier Whelp(1), Torch(1)
- P2: HP=29 Armor=0 Mana=3/3 Deck=24; Weapon=none; Board=empty; Locations=none; Hand=Sanguine Depths(1), Mother Duck(4), Erupting Volcano(3), Windpeak Wyrm(8), Carrier Whelp(1), The Great Dracorex(8), Mother Duck(4)

## Step 22 — turn 7

`P2 END_TURN`

Legal choices before action: 5

Events:

- `{"kind": "turn_end", "player": 1, "turn": 6}`
- `{"card": "END_033", "kind": "draw", "player": 0, "turn": 7}`
- `{"kind": "turn_start", "player": 0, "turn": 7}`

- P1: HP=28 Armor=2 Mana=4/4 Deck=24; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Warptooth(4), Carrier Whelp(1), Torch(1), Prescient Slitherdrake(4)
- P2: HP=29 Armor=0 Mana=3/3 Deck=24; Weapon=none; Board=empty; Locations=none; Hand=Sanguine Depths(1), Mother Duck(4), Erupting Volcano(3), Windpeak Wyrm(8), Carrier Whelp(1), The Great Dracorex(8), Mother Duck(4)

## Step 23 — turn 8

`P1 END_TURN`

Legal choices before action: 13

Events:

- `{"kind": "turn_end", "player": 0, "turn": 7}`
- `{"card": "EDR_457", "kind": "draw", "player": 1, "turn": 8}`
- `{"kind": "turn_start", "player": 1, "turn": 8}`

- P1: HP=28 Armor=2 Mana=4/4 Deck=24; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Warptooth(4), Carrier Whelp(1), Torch(1), Prescient Slitherdrake(4)
- P2: HP=29 Armor=0 Mana=4/4 Deck=23; Weapon=none; Board=empty; Locations=none; Hand=Sanguine Depths(1), Mother Duck(4), Erupting Volcano(3), Windpeak Wyrm(8), Carrier Whelp(1), The Great Dracorex(8), Mother Duck(4), Brood Keeper(2)

## Step 24 — turn 8

`P2 PLAY Erupting Volcano[CATA_584] -> -`

Legal choices before action: 8

Events:

- `{"card": "CATA_584", "controller": 1, "kind": "play", "player": 1, "turn": 8}`

- P1: HP=28 Armor=2 Mana=4/4 Deck=24; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Warptooth(4), Carrier Whelp(1), Torch(1), Prescient Slitherdrake(4)
- P2: HP=29 Armor=0 Mana=1/4 Deck=23; Weapon=none; Board=empty; Locations=CATA_584#51 durability=3 cooldown=1; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), Carrier Whelp(1), The Great Dracorex(8), Mother Duck(4), Brood Keeper(2)

## Step 25 — turn 8

`P2 PLAY Carrier Whelp[CATA_556] -> -`

Legal choices before action: 3

Events:

- `{"card": "CATA_556", "controller": 1, "kind": "play", "player": 1, "turn": 8}`
- `{"card": "CATA_556", "entity": 71, "kind": "generated_to_hand", "player": 1, "source": "CATA_556", "turn": 8}`

- P1: HP=28 Armor=2 Mana=4/4 Deck=24; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Warptooth(4), Carrier Whelp(1), Torch(1), Prescient Slitherdrake(4)
- P2: HP=29 Armor=0 Mana=0/4 Deck=23; Weapon=none; Board=Carrier Whelp#65 1/2; Locations=CATA_584#51 durability=3 cooldown=1; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Mother Duck(4), Brood Keeper(2), Carrier Whelp(1)

## Step 26 — turn 9

`P2 END_TURN`

Legal choices before action: 1

Events:

- `{"kind": "turn_end", "player": 1, "turn": 8}`
- `{"card": "EDR_456", "kind": "draw", "player": 0, "turn": 9}`
- `{"kind": "turn_start", "player": 0, "turn": 9}`

- P1: HP=28 Armor=2 Mana=5/5 Deck=23; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Warptooth(4), Carrier Whelp(1), Torch(1), Prescient Slitherdrake(4), Darkrider(1)
- P2: HP=29 Armor=0 Mana=0/4 Deck=23; Weapon=none; Board=Carrier Whelp#65 1/2; Locations=CATA_584#51 durability=3 cooldown=1; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(5), The Great Dracorex(8), Mother Duck(4), Brood Keeper(2), Carrier Whelp(1)

## Step 27 — turn 9

`P1 PLAY Carrier Whelp[CATA_556] -> -`

Legal choices before action: 17

Events:

- `{"card": "CATA_556", "controller": 0, "kind": "play", "player": 0, "turn": 9}`
- `{"card": "CATA_556", "entity": 72, "kind": "generated_to_hand", "player": 0, "source": "CATA_556", "turn": 9}`

- P1: HP=28 Armor=2 Mana=4/5 Deck=23; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1, Carrier Whelp#67 1/2; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Warptooth(4), Torch(1), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1)
- P2: HP=29 Armor=0 Mana=0/4 Deck=23; Weapon=none; Board=Carrier Whelp#65 1/2; Locations=CATA_584#51 durability=3 cooldown=1; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(5), The Great Dracorex(8), Mother Duck(4), Brood Keeper(2), Carrier Whelp(1)

## Step 28 — turn 9

`P1 ATTACK Carrier Whelp#66 -> P2 hero`

Legal choices before action: 17

- P1: HP=28 Armor=2 Mana=4/5 Deck=23; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1, Carrier Whelp#67 1/2; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Warptooth(4), Torch(1), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1)
- P2: HP=28 Armor=0 Mana=0/4 Deck=23; Weapon=none; Board=Carrier Whelp#65 1/2; Locations=CATA_584#51 durability=3 cooldown=1; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(5), The Great Dracorex(8), Mother Duck(4), Brood Keeper(2), Carrier Whelp(1)

## Step 29 — turn 9

`P1 HERO_POWER Armor Up`

Legal choices before action: 15

Events:

- `{"amount": 2, "kind": "gain_armor", "player": 0, "turn": 9}`
- `{"kind": "hero_power", "player": 0, "turn": 9}`

- P1: HP=28 Armor=4 Mana=2/5 Deck=23; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1, Carrier Whelp#67 1/2; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Warptooth(4), Torch(1), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1)
- P2: HP=28 Armor=0 Mana=0/4 Deck=23; Weapon=none; Board=Carrier Whelp#65 1/2; Locations=CATA_584#51 durability=3 cooldown=1; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(5), The Great Dracorex(8), Mother Duck(4), Brood Keeper(2), Carrier Whelp(1)

## Step 30 — turn 9

`P1 PLAY Carrier Whelp[CATA_556] -> -`

Legal choices before action: 11

Events:

- `{"card": "CATA_556", "controller": 0, "kind": "play", "player": 0, "turn": 9}`
- `{"card": "CATA_556", "entity": 73, "kind": "generated_to_hand", "player": 0, "source": "CATA_556", "turn": 9}`

- P1: HP=28 Armor=4 Mana=1/5 Deck=23; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1, Carrier Whelp#67 1/2, Carrier Whelp#72 1/2; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Warptooth(4), Torch(1), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1)
- P2: HP=28 Armor=0 Mana=0/4 Deck=23; Weapon=none; Board=Carrier Whelp#65 1/2; Locations=CATA_584#51 durability=3 cooldown=1; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(5), The Great Dracorex(8), Mother Duck(4), Brood Keeper(2), Carrier Whelp(1)

## Step 31 — turn 10

`P1 END_TURN`

Legal choices before action: 9

Events:

- `{"kind": "turn_end", "player": 0, "turn": 9}`
- `{"card": "JAIL_421", "kind": "draw", "player": 1, "turn": 10}`
- `{"kind": "turn_start", "player": 1, "turn": 10}`

- P1: HP=28 Armor=4 Mana=1/5 Deck=23; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1, Carrier Whelp#67 1/2, Carrier Whelp#72 1/2; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Warptooth(4), Torch(1), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1)
- P2: HP=28 Armor=0 Mana=5/5 Deck=22; Weapon=none; Board=Carrier Whelp#65 1/2; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(5), The Great Dracorex(8), Mother Duck(4), Brood Keeper(2), Carrier Whelp(1), Warptooth(4)

## Step 32 — turn 10

`P2 ATTACK Carrier Whelp#65 -> P1 Carrier Whelp#67`

Legal choices before action: 23

- P1: HP=28 Armor=4 Mana=1/5 Deck=23; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1, Carrier Whelp#67 1/1, Carrier Whelp#72 1/2; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Warptooth(4), Torch(1), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1)
- P2: HP=28 Armor=0 Mana=5/5 Deck=22; Weapon=none; Board=Carrier Whelp#65 1/1; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(5), The Great Dracorex(8), Mother Duck(4), Brood Keeper(2), Carrier Whelp(1), Warptooth(4)

## Step 33 — turn 11

`P2 END_TURN`

Legal choices before action: 17

Events:

- `{"kind": "turn_end", "player": 1, "turn": 10}`
- `{"card": "JAIL_384", "kind": "draw", "player": 0, "turn": 11}`
- `{"kind": "turn_start", "player": 0, "turn": 11}`

- P1: HP=28 Armor=4 Mana=6/6 Deck=22; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1, Carrier Whelp#67 1/1, Carrier Whelp#72 1/2; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Warptooth(4), Torch(1), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1), Chainbreaker Hogger(8)
- P2: HP=28 Armor=0 Mana=5/5 Deck=22; Weapon=none; Board=Carrier Whelp#65 1/1; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Mother Duck(4), Brood Keeper(2), Carrier Whelp(1), Warptooth(4)

## Step 34 — turn 11

`P1 ATTACK Carrier Whelp#67 -> P2 Carrier Whelp#65`

Legal choices before action: 23

Events:

- `{"card": "CATA_556", "entity": 67, "kind": "minion_died", "player": 0, "turn": 11}`
- `{"card": "CATA_556", "entity": 65, "kind": "minion_died", "player": 1, "turn": 11}`

- P1: HP=28 Armor=4 Mana=6/6 Deck=22; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1, Carrier Whelp#72 1/2; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Warptooth(4), Torch(1), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1), Chainbreaker Hogger(8)
- P2: HP=28 Armor=0 Mana=5/5 Deck=22; Weapon=none; Board=empty; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Mother Duck(4), Brood Keeper(2), Carrier Whelp(1), Warptooth(4)

## Step 35 — turn 11

`P1 HERO_POWER Armor Up`

Legal choices before action: 15

Events:

- `{"amount": 2, "kind": "gain_armor", "player": 0, "turn": 11}`
- `{"kind": "hero_power", "player": 0, "turn": 11}`

- P1: HP=28 Armor=6 Mana=4/6 Deck=22; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1, Carrier Whelp#72 1/2; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Warptooth(4), Torch(1), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1), Chainbreaker Hogger(8)
- P2: HP=28 Armor=0 Mana=5/5 Deck=22; Weapon=none; Board=empty; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Mother Duck(4), Brood Keeper(2), Carrier Whelp(1), Warptooth(4)

## Step 36 — turn 11

`P1 ATTACK Carrier Whelp#17 -> P2 hero`

Legal choices before action: 14

- P1: HP=28 Armor=6 Mana=4/6 Deck=22; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1, Carrier Whelp#72 1/2; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Warptooth(4), Torch(1), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1), Chainbreaker Hogger(8)
- P2: HP=27 Armor=0 Mana=5/5 Deck=22; Weapon=none; Board=empty; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Mother Duck(4), Brood Keeper(2), Carrier Whelp(1), Warptooth(4)

## Step 37 — turn 11

`P1 PLAY Warptooth[JAIL_421] -> -`

Legal choices before action: 13

Events:

- `{"card": "JAIL_421", "controller": 0, "kind": "play", "player": 0, "turn": 11}`

- P1: HP=28 Armor=6 Mana=0/6 Deck=22; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1, Carrier Whelp#72 1/2, Warptooth#25 3/3; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Torch(1), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1), Chainbreaker Hogger(8)
- P2: HP=27 Armor=0 Mana=5/5 Deck=22; Weapon=none; Board=empty; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Mother Duck(4), Brood Keeper(2), Carrier Whelp(1), Warptooth(4)

## Step 38 — turn 11

`P1 ATTACK Warptooth#25 -> P2 hero`

Legal choices before action: 5

- P1: HP=28 Armor=6 Mana=0/6 Deck=22; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1, Carrier Whelp#72 1/2, Warptooth#25 3/3; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Torch(1), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1), Chainbreaker Hogger(8)
- P2: HP=24 Armor=0 Mana=5/5 Deck=22; Weapon=none; Board=empty; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Mother Duck(4), Brood Keeper(2), Carrier Whelp(1), Warptooth(4)

## Step 39 — turn 11

`P1 ATTACK Carrier Whelp#72 -> P2 hero`

Legal choices before action: 4

- P1: HP=28 Armor=6 Mana=0/6 Deck=22; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1, Carrier Whelp#72 1/2, Warptooth#25 3/3; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Torch(1), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1), Chainbreaker Hogger(8)
- P2: HP=23 Armor=0 Mana=5/5 Deck=22; Weapon=none; Board=empty; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Mother Duck(4), Brood Keeper(2), Carrier Whelp(1), Warptooth(4)

## Step 40 — turn 11

`P1 ATTACK Carrier Whelp#64 -> P2 hero`

Legal choices before action: 3

- P1: HP=28 Armor=6 Mana=0/6 Deck=22; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1, Carrier Whelp#72 1/2, Warptooth#25 3/3; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Torch(1), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1), Chainbreaker Hogger(8)
- P2: HP=22 Armor=0 Mana=5/5 Deck=22; Weapon=none; Board=empty; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Mother Duck(4), Brood Keeper(2), Carrier Whelp(1), Warptooth(4)

## Step 41 — turn 11

`P1 ATTACK Carrier Whelp#66 -> P2 hero`

Legal choices before action: 2

- P1: HP=28 Armor=6 Mana=0/6 Deck=22; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1, Carrier Whelp#72 1/2, Warptooth#25 3/3; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Torch(1), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1), Chainbreaker Hogger(8)
- P2: HP=21 Armor=0 Mana=5/5 Deck=22; Weapon=none; Board=empty; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Mother Duck(4), Brood Keeper(2), Carrier Whelp(1), Warptooth(4)

## Step 42 — turn 12

`P1 END_TURN`

Legal choices before action: 1

Events:

- `{"kind": "turn_end", "player": 0, "turn": 11}`
- `{"card": "CAP_105", "kind": "draw", "player": 1, "turn": 12}`
- `{"kind": "turn_start", "player": 1, "turn": 12}`

- P1: HP=28 Armor=6 Mana=0/6 Deck=22; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1, Carrier Whelp#72 1/2, Warptooth#25 3/3; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Torch(1), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1), Chainbreaker Hogger(8)
- P2: HP=21 Armor=0 Mana=6/6 Deck=21; Weapon=none; Board=empty; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Mother Duck(4), Brood Keeper(2), Carrier Whelp(1), Warptooth(4), Hook n' Heave(2)

## Step 43 — turn 12

`P2 PLAY Mother Duck[EDR_492] -> -`

Legal choices before action: 10

Events:

- `{"card": "EDR_492", "controller": 1, "kind": "play", "player": 1, "turn": 12}`

- P1: HP=28 Armor=6 Mana=0/6 Deck=22; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1, Carrier Whelp#72 1/2, Warptooth#25 3/3; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Torch(1), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1), Chainbreaker Hogger(8)
- P2: HP=21 Armor=0 Mana=2/6 Deck=21; Weapon=none; Board=Mother Duck#38 2/3, Duckling#74 1/1, Duckling#75 1/1, Duckling#76 1/1; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Brood Keeper(2), Carrier Whelp(1), Warptooth(4), Hook n' Heave(2)

## Step 44 — turn 13

`P2 END_TURN`

Legal choices before action: 22

Events:

- `{"kind": "turn_end", "player": 1, "turn": 12}`
- `{"card": "CATA_585", "kind": "draw", "player": 0, "turn": 13}`
- `{"kind": "turn_start", "player": 0, "turn": 13}`

- P1: HP=28 Armor=6 Mana=7/7 Deck=21; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1, Carrier Whelp#72 1/2, Warptooth#25 3/3; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Torch(1), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1), Chainbreaker Hogger(8), Torch(1)
- P2: HP=21 Armor=0 Mana=2/6 Deck=21; Weapon=none; Board=Mother Duck#38 2/3, Duckling#74 1/1, Duckling#75 1/1, Duckling#76 1/1; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Brood Keeper(2), Carrier Whelp(1), Warptooth(4), Hook n' Heave(2)

## Step 45 — turn 14

`P1 END_TURN`

Legal choices before action: 37

Events:

- `{"kind": "turn_end", "player": 0, "turn": 13}`
- `{"card": "END_033", "kind": "draw", "player": 1, "turn": 14}`
- `{"kind": "turn_start", "player": 1, "turn": 14}`

- P1: HP=28 Armor=6 Mana=7/7 Deck=21; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1, Carrier Whelp#72 1/2, Warptooth#25 3/3; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Torch(1), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1), Chainbreaker Hogger(8), Torch(1)
- P2: HP=21 Armor=0 Mana=7/7 Deck=20; Weapon=none; Board=Mother Duck#38 2/3, Duckling#74 1/1, Duckling#75 1/1, Duckling#76 1/1; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Brood Keeper(2), Carrier Whelp(1), Warptooth(4), Hook n' Heave(2), Prescient Slitherdrake(4)

## Step 46 — turn 14

`P2 PLAY Hook n' Heave[CAP_105] -> -`

Legal choices before action: 34

Events:

- `{"card": "CAP_105", "controller": 1, "kind": "play", "player": 1, "turn": 14}`
- `{"kind": "discover_offer", "options": [{"card": "CAP_107", "entity": 77, "gifts": []}], "player": 1, "profile": "closed_pool", "turn": 14}`

- P1: HP=28 Armor=6 Mana=7/7 Deck=21; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1, Carrier Whelp#72 1/2, Warptooth#25 3/3; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Torch(1), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1), Chainbreaker Hogger(8), Torch(1)
- P2: HP=21 Armor=0 Mana=5/7 Deck=20; Weapon=none; Board=Mother Duck#38 2/3, Duckling#74 1/1, Duckling#75 1/1, Duckling#76 1/1; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Brood Keeper(2), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4)
- Pending decision: `{"kind": "DISCOVER", "options": [{"attack": 3, "burning_turns": 0, "cant_attack": false, "cant_attack_heroes_turn": -1, "card_class": "WARRIOR", "card_set": "ESCAPEFROM_VIOLET_HOLD", "cost": 1, "created_by": "CAP_105", "damage": 0, "divine_shield_hits": 0, "dormant_turns": 0, "dynamic_spell_damage": 0, "entity": 77, "frozen": false, "gifts": [], "health": 1, "herald_power": 1, "id": "CAP_107", "illusion_fake": false, "infinite_attack_next_turn": false, "keywords": [], "max_health": 1, "mirrex_tracker": false, "name": "Cannonmaster", "omen_damage": 1, "played_turn": -1, "prepared_turn": -1, "races": ["PIRATE", "DRAENEI"], "spell_damage_bonus": 0, "started_in_deck": false, "summon_moragg_on_death": false, "summoned_when_drawn": false, "twilight_whelp_bonus": 0, "void_soul_cost": 0}]}`

## Step 47 — turn 14

`P2 DISCOVER_PICK Cannonmaster[CAP_107]`

Legal choices before action: 1

Events:

- `{"card": "CAP_107", "entity": 77, "gifts": [], "kind": "discover_pick", "player": 1, "turn": 14}`

- P1: HP=28 Armor=6 Mana=7/7 Deck=21; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1, Carrier Whelp#72 1/2, Warptooth#25 3/3; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Torch(1), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1), Chainbreaker Hogger(8), Torch(1)
- P2: HP=21 Armor=0 Mana=5/7 Deck=20; Weapon=none; Board=Mother Duck#38 2/3, Duckling#74 1/1, Duckling#75 1/1, Duckling#76 1/1, Cutlass Cutthroat#78 1/1, Cutlass Cutthroat#79 1/1; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Brood Keeper(2), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1)

## Step 48 — turn 15

`P2 END_TURN`

Legal choices before action: 37

Events:

- `{"kind": "turn_end", "player": 1, "turn": 14}`
- `{"card": "CORE_REV_990", "kind": "draw", "player": 0, "turn": 15}`
- `{"kind": "turn_start", "player": 0, "turn": 15}`

- P1: HP=28 Armor=6 Mana=8/8 Deck=20; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1, Carrier Whelp#72 1/2, Warptooth#25 3/3; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Torch(1), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1), Chainbreaker Hogger(8), Torch(1), Sanguine Depths(1)
- P2: HP=21 Armor=0 Mana=5/7 Deck=20; Weapon=none; Board=Mother Duck#38 2/3, Duckling#74 1/1, Duckling#75 1/1, Duckling#76 1/1, Cutlass Cutthroat#78 1/1, Cutlass Cutthroat#79 1/1; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Brood Keeper(2), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1)

## Step 49 — turn 16

`P1 END_TURN`

Legal choices before action: 49

Events:

- `{"kind": "turn_end", "player": 0, "turn": 15}`
- `{"card": "JAIL_421", "kind": "draw", "player": 1, "turn": 16}`
- `{"kind": "turn_start", "player": 1, "turn": 16}`

- P1: HP=28 Armor=6 Mana=8/8 Deck=20; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1, Carrier Whelp#72 1/2, Warptooth#25 3/3; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Torch(1), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1), Chainbreaker Hogger(8), Torch(1), Sanguine Depths(1)
- P2: HP=21 Armor=0 Mana=8/8 Deck=19; Weapon=none; Board=Mother Duck#38 2/3, Duckling#74 1/1, Duckling#75 1/1, Duckling#76 1/1, Cutlass Cutthroat#78 1/1, Cutlass Cutthroat#79 1/1; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Brood Keeper(2), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4)

## Step 50 — turn 17

`P2 END_TURN`

Legal choices before action: 39

Events:

- `{"kind": "turn_end", "player": 1, "turn": 16}`
- `{"card": "CATA_582", "kind": "burn", "player": 0, "turn": 17}`
- `{"kind": "turn_start", "player": 0, "turn": 17}`

- P1: HP=28 Armor=6 Mana=9/9 Deck=19; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1, Carrier Whelp#72 1/2, Warptooth#25 3/3; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Torch(1), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1), Chainbreaker Hogger(8), Torch(1), Sanguine Depths(1)
- P2: HP=21 Armor=0 Mana=8/8 Deck=19; Weapon=none; Board=Mother Duck#38 2/3, Duckling#74 1/1, Duckling#75 1/1, Duckling#76 1/1, Cutlass Cutthroat#78 1/1, Cutlass Cutthroat#79 1/1; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Brood Keeper(2), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4)

## Step 51 — turn 17

`P1 ATTACK Warptooth#25 -> P2 hero`

Legal choices before action: 49

- P1: HP=28 Armor=6 Mana=9/9 Deck=19; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#66 1/1, Carrier Whelp#72 1/2, Warptooth#25 3/3; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Torch(1), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1), Chainbreaker Hogger(8), Torch(1), Sanguine Depths(1)
- P2: HP=18 Armor=0 Mana=8/8 Deck=19; Weapon=none; Board=Mother Duck#38 2/3, Duckling#74 1/1, Duckling#75 1/1, Duckling#76 1/1, Cutlass Cutthroat#78 1/1, Cutlass Cutthroat#79 1/1; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Brood Keeper(2), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4)

## Step 52 — turn 17

`P1 PLAY Torch[CATA_585] -> P1 Carrier Whelp#66`

Legal choices before action: 42

Events:

- `{"card": "CATA_585", "controller": 0, "kind": "play", "player": 0, "turn": 17}`
- `{"card": "CATA_556", "entity": 66, "kind": "minion_died", "player": 0, "turn": 17}`

- P1: HP=28 Armor=6 Mana=8/9 Deck=19; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#72 1/2, Warptooth#25 3/3; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Torch(1), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1), Chainbreaker Hogger(8), Sanguine Depths(1), Torch(1)
- P2: HP=18 Armor=0 Mana=8/8 Deck=19; Weapon=none; Board=Mother Duck#38 2/3, Duckling#74 1/1, Duckling#75 1/1, Duckling#76 1/1, Cutlass Cutthroat#78 1/1, Cutlass Cutthroat#79 1/1; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Brood Keeper(2), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4)

## Step 53 — turn 17

`P1 PLAY Chainbreaker Hogger[JAIL_384] -> -`

Legal choices before action: 33

Events:

- `{"card": "JAIL_384", "controller": 0, "kind": "play", "player": 0, "turn": 17}`

- P1: HP=28 Armor=6 Mana=0/9 Deck=19; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#72 1/2, Warptooth#25 3/3, Chainbreaker Hogger#26 10/10; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Torch(1), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1), Sanguine Depths(1), Torch(1)
- P2: HP=18 Armor=0 Mana=8/8 Deck=19; Weapon=none; Board=Mother Duck#38 2/3, Duckling#74 1/1, Duckling#75 1/1, Duckling#76 1/1, Cutlass Cutthroat#78 1/1, Cutlass Cutthroat#79 1/1; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Brood Keeper(2), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4)

## Step 54 — turn 17

`P1 ATTACK Carrier Whelp#72 -> P2 Duckling#76`

Legal choices before action: 22

Events:

- `{"card": "EDR_492t", "entity": 76, "kind": "minion_died", "player": 1, "turn": 17}`

- P1: HP=28 Armor=6 Mana=0/9 Deck=19; Weapon=none; Board=Carrier Whelp#17 1/1, Carrier Whelp#64 1/2, Carrier Whelp#72 1/1, Warptooth#25 3/3, Chainbreaker Hogger#26 10/10; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Torch(1), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1), Sanguine Depths(1), Torch(1)
- P2: HP=18 Armor=0 Mana=8/8 Deck=19; Weapon=none; Board=Mother Duck#38 2/3, Duckling#74 1/1, Duckling#75 1/1, Cutlass Cutthroat#78 1/1, Cutlass Cutthroat#79 1/1; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Brood Keeper(2), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4)

## Step 55 — turn 17

`P1 ATTACK Carrier Whelp#17 -> P2 Cutlass Cutthroat#78`

Legal choices before action: 13

Events:

- `{"card": "CATA_556", "entity": 17, "kind": "minion_died", "player": 0, "turn": 17}`
- `{"card": "CAP_105t", "entity": 78, "kind": "minion_died", "player": 1, "turn": 17}`

- P1: HP=28 Armor=6 Mana=0/9 Deck=19; Weapon=none; Board=Carrier Whelp#64 1/2, Carrier Whelp#72 1/1, Warptooth#25 3/3, Chainbreaker Hogger#26 10/10; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Torch(1), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1), Sanguine Depths(1), Torch(1)
- P2: HP=18 Armor=0 Mana=8/8 Deck=19; Weapon=none; Board=Mother Duck#38 2/3, Duckling#74 1/1, Duckling#75 1/1, Cutlass Cutthroat#79 1/1; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Brood Keeper(2), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4)

## Step 56 — turn 17

`P1 ATTACK Carrier Whelp#64 -> P2 Mother Duck#38`

Legal choices before action: 6

Events:

- `{"card": "JAIL_421", "kind": "summon_from_zone", "player": 0, "turn": 17}`
- `{"card": "CATA_556", "entity": 64, "kind": "minion_died", "player": 0, "turn": 17}`

- P1: HP=28 Armor=6 Mana=0/9 Deck=18; Weapon=none; Board=Carrier Whelp#72 1/1, Warptooth#25 3/3, Chainbreaker Hogger#26 10/10, Warptooth#62 3/3; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Torch(1), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1), Sanguine Depths(1), Torch(1)
- P2: HP=18 Armor=0 Mana=8/8 Deck=19; Weapon=none; Board=Mother Duck#38 2/2, Duckling#74 1/1, Duckling#75 1/1, Cutlass Cutthroat#79 1/1; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Brood Keeper(2), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4)

## Step 57 — turn 17

`P1 ATTACK Warptooth#62 -> P2 Mother Duck#38`

Legal choices before action: 6

Events:

- `{"card": "EDR_492", "entity": 38, "kind": "minion_died", "player": 1, "turn": 17}`

- P1: HP=28 Armor=6 Mana=0/9 Deck=18; Weapon=none; Board=Carrier Whelp#72 1/1, Warptooth#25 3/3, Chainbreaker Hogger#26 10/10, Warptooth#62 3/1; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Torch(1), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1), Sanguine Depths(1), Torch(1)
- P2: HP=18 Armor=0 Mana=8/8 Deck=19; Weapon=none; Board=Duckling#74 1/1, Duckling#75 1/1, Cutlass Cutthroat#79 1/1; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Brood Keeper(2), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4)

## Step 58 — turn 18

`P1 END_TURN`

Legal choices before action: 1

Events:

- `{"kind": "turn_end", "player": 0, "turn": 17}`
- `{"card": "END_033", "kind": "burn", "player": 1, "turn": 18}`
- `{"kind": "turn_start", "player": 1, "turn": 18}`

- P1: HP=28 Armor=6 Mana=0/9 Deck=18; Weapon=none; Board=Carrier Whelp#72 1/1, Warptooth#25 3/3, Chainbreaker Hogger#26 10/10, Warptooth#62 3/1; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Torch(1), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1), Sanguine Depths(1), Torch(1)
- P2: HP=18 Armor=0 Mana=9/9 Deck=18; Weapon=none; Board=Duckling#74 1/1, Duckling#75 1/1, Cutlass Cutthroat#79 1/1; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Brood Keeper(2), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4)

## Step 59 — turn 19

`P2 END_TURN`

Legal choices before action: 24

Events:

- `{"kind": "turn_end", "player": 1, "turn": 18}`
- `{"card": "EDR_457", "kind": "draw", "player": 0, "turn": 19}`
- `{"kind": "turn_start", "player": 0, "turn": 19}`

- P1: HP=28 Armor=6 Mana=10/10 Deck=17; Weapon=none; Board=Carrier Whelp#72 1/1, Warptooth#25 3/3, Chainbreaker Hogger#26 10/10, Warptooth#62 3/1; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Torch(1), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1), Sanguine Depths(1), Torch(1), Brood Keeper(2)
- P2: HP=18 Armor=0 Mana=9/9 Deck=18; Weapon=none; Board=Duckling#74 1/1, Duckling#75 1/1, Cutlass Cutthroat#79 1/1; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Brood Keeper(2), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4)

## Step 60 — turn 19

`P1 PLAY Torch[CATA_585] -> P1 Warptooth#62`

Legal choices before action: 30

Events:

- `{"card": "CATA_585", "controller": 0, "kind": "play", "player": 0, "turn": 19}`
- `{"card": "JAIL_421", "entity": 62, "kind": "minion_died", "player": 0, "turn": 19}`

- P1: HP=28 Armor=6 Mana=9/10 Deck=17; Weapon=none; Board=Carrier Whelp#72 1/1, Warptooth#25 3/3, Chainbreaker Hogger#26 10/10; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1), Sanguine Depths(1), Torch(1), Brood Keeper(2), Torch(1)
- P2: HP=18 Armor=0 Mana=9/9 Deck=18; Weapon=none; Board=Duckling#74 1/1, Duckling#75 1/1, Cutlass Cutthroat#79 1/1; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Brood Keeper(2), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4)

## Step 61 — turn 19

`P1 PLAY Brood Keeper[EDR_457] -> -`

Legal choices before action: 24

Events:

- `{"card": "EDR_457", "controller": 0, "kind": "play", "player": 0, "turn": 19}`
- `{"attack": 2, "card": "EDR_457t", "durability": 2, "kind": "equip_weapon", "player": 0, "turn": 19}`

- P1: HP=28 Armor=6 Mana=7/10 Deck=17; Weapon=Brood Keeper's Sword 2/2; Board=Carrier Whelp#72 1/1, Warptooth#25 3/3, Chainbreaker Hogger#26 10/10, Brood Keeper#6 2/3; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1), Sanguine Depths(1), Torch(1), Torch(1)
- P2: HP=18 Armor=0 Mana=9/9 Deck=18; Weapon=none; Board=Duckling#74 1/1, Duckling#75 1/1, Cutlass Cutthroat#79 1/1; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Brood Keeper(2), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4)

## Step 62 — turn 19

`P1 HERO_ATTACK -> P2 hero`

Legal choices before action: 27

- P1: HP=28 Armor=6 Mana=7/10 Deck=17; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#72 1/1, Warptooth#25 3/3, Chainbreaker Hogger#26 10/10, Brood Keeper#6 2/3; Locations=none; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1), Sanguine Depths(1), Torch(1), Torch(1)
- P2: HP=16 Armor=0 Mana=9/9 Deck=18; Weapon=none; Board=Duckling#74 1/1, Duckling#75 1/1, Cutlass Cutthroat#79 1/1; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Brood Keeper(2), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4)

## Step 63 — turn 19

`P1 PLAY Sanguine Depths[CORE_REV_990] -> -`

Legal choices before action: 23

Events:

- `{"card": "CORE_REV_990", "controller": 0, "kind": "play", "player": 0, "turn": 19}`

- P1: HP=28 Armor=6 Mana=6/10 Deck=17; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#72 1/1, Warptooth#25 3/3, Chainbreaker Hogger#26 10/10, Brood Keeper#6 2/3; Locations=CORE_REV_990#2 durability=3 cooldown=1; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1), Torch(1), Torch(1)
- P2: HP=16 Armor=0 Mana=9/9 Deck=18; Weapon=none; Board=Duckling#74 1/1, Duckling#75 1/1, Cutlass Cutthroat#79 1/1; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Brood Keeper(2), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4)

## Step 64 — turn 19

`P1 ATTACK Chainbreaker Hogger#26 -> P2 Duckling#75`

Legal choices before action: 22

Events:

- `{"card": "EDR_492t", "entity": 75, "kind": "minion_died", "player": 1, "turn": 19}`

- P1: HP=28 Armor=6 Mana=6/10 Deck=17; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#72 1/1, Warptooth#25 3/3, Chainbreaker Hogger#26 10/9, Brood Keeper#6 2/3; Locations=CORE_REV_990#2 durability=3 cooldown=1; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Darkrider(1), Carrier Whelp(1), Torch(1), Torch(1)
- P2: HP=16 Armor=0 Mana=9/9 Deck=18; Weapon=none; Board=Duckling#74 1/1, Cutlass Cutthroat#79 1/1; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Brood Keeper(2), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4)

## Step 65 — turn 19

`P1 PLAY Carrier Whelp[CATA_556] -> -`

Legal choices before action: 18

Events:

- `{"card": "CATA_556", "controller": 0, "kind": "play", "player": 0, "turn": 19}`
- `{"card": "CATA_556", "entity": 80, "kind": "generated_to_hand", "player": 0, "source": "CATA_556", "turn": 19}`

- P1: HP=28 Armor=6 Mana=5/10 Deck=17; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#72 1/1, Warptooth#25 3/3, Chainbreaker Hogger#26 10/9, Brood Keeper#6 2/3, Carrier Whelp#73 1/2; Locations=CORE_REV_990#2 durability=3 cooldown=1; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Darkrider(1), Torch(1), Torch(1), Carrier Whelp(1)
- P2: HP=16 Armor=0 Mana=9/9 Deck=18; Weapon=none; Board=Duckling#74 1/1, Cutlass Cutthroat#79 1/1; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Brood Keeper(2), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4)

## Step 66 — turn 19

`P1 ATTACK Warptooth#25 -> P2 Cutlass Cutthroat#79`

Legal choices before action: 18

Events:

- `{"card": "CAP_105t", "entity": 79, "kind": "minion_died", "player": 1, "turn": 19}`

- P1: HP=28 Armor=6 Mana=5/10 Deck=17; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#72 1/1, Warptooth#25 3/2, Chainbreaker Hogger#26 10/9, Brood Keeper#6 2/3, Carrier Whelp#73 1/2; Locations=CORE_REV_990#2 durability=3 cooldown=1; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Darkrider(1), Torch(1), Torch(1), Carrier Whelp(1)
- P2: HP=16 Armor=0 Mana=9/9 Deck=18; Weapon=none; Board=Duckling#74 1/1; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Brood Keeper(2), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4)

## Step 67 — turn 19

`P1 HERO_POWER Armor Up`

Legal choices before action: 16

Events:

- `{"amount": 2, "kind": "gain_armor", "player": 0, "turn": 19}`
- `{"kind": "hero_power", "player": 0, "turn": 19}`

- P1: HP=28 Armor=8 Mana=3/10 Deck=17; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#72 1/1, Warptooth#25 3/2, Chainbreaker Hogger#26 10/9, Brood Keeper#6 2/3, Carrier Whelp#73 1/2; Locations=CORE_REV_990#2 durability=3 cooldown=1; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Darkrider(1), Torch(1), Torch(1), Carrier Whelp(1)
- P2: HP=16 Armor=0 Mana=9/9 Deck=18; Weapon=none; Board=Duckling#74 1/1; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Brood Keeper(2), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4)

## Step 68 — turn 19

`P1 PLAY Darkrider[EDR_456] -> -`

Legal choices before action: 13

Events:

- `{"card": "EDR_456", "controller": 0, "kind": "play", "player": 0, "turn": 19}`
- `{"kind": "discover_offer", "options": [{"card": "EDR_000", "entity": 81, "gifts": ["persisting_horror"]}, {"card": "CS3_035", "entity": 82, "gifts": ["harpys_talons"]}, {"card": "CORE_DRG_079", "entity": 83, "gifts": ["sleepwalker"]}], "player": 0, "profile": "closed_pool", "turn": 19}`

- P1: HP=28 Armor=8 Mana=2/10 Deck=17; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#72 1/1, Warptooth#25 3/2, Chainbreaker Hogger#26 10/9, Brood Keeper#6 2/3, Carrier Whelp#73 1/2, Darkrider#3 1/1; Locations=CORE_REV_990#2 durability=3 cooldown=1; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Torch(1), Torch(1), Carrier Whelp(1)
- P2: HP=16 Armor=0 Mana=9/9 Deck=18; Weapon=none; Board=Duckling#74 1/1; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Brood Keeper(2), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4)
- Pending decision: `{"kind": "DISCOVER", "options": [{"attack": 4, "burning_turns": 0, "cant_attack": false, "cant_attack_heroes_turn": -1, "card_class": "NEUTRAL", "card_set": "EMERALD_DREAM", "cost": 9, "created_by": "EDR_456", "damage": 0, "divine_shield_hits": 0, "dormant_turns": 0, "dynamic_spell_damage": 0, "entity": 81, "frozen": false, "gifts": ["persisting_horror"], "health": 12, "herald_power": 1, "id": "EDR_000", "illusion_fake": false, "infinite_attack_next_turn": false, "keywords": ["reborn"], "max_health": 12, "mirrex_tracker": false, "name": "Ysera, Emerald Aspect", "omen_damage": 1, "played_turn": -1, "prepared_turn": -1, "races": ["DRAGON"], "spell_damage_bonus": 0, "started_in_deck": false, "summon_moragg_on_death": false, "summoned_when_drawn": false, "twilight_whelp_bonus": 0, "void_soul_cost": 0}, {"attack": 8, "burning_turns": 0, "cant_attack": false, "cant_attack_heroes_turn": -1, "card_class": "NEUTRAL", "card_set": "CORE", "cost": 7, "created_by": "EDR_456", "damage": 0, "divine_shield_hits": 0, "dormant_turns": 0, "dynamic_spell_damage": 0, "entity": 82, "frozen": false, "gifts": ["harpys_talons"], "health": 8, "herald_power": 1, "id": "CS3_035", "illusion_fake": false, "infinite_attack_next_turn": false, "keywords": ["divine_shield", "windfury"], "max_health": 8, "mirrex_tracker": false, "name": "Nozdormu the Eternal", "omen_damage": 1, "played_turn": -1, "prepared_turn": -1, "races": ["DRAGON"], "spell_damage_bonus": 0, "started_in_deck": false, "summon_moragg_on_death": false, "summoned_when_drawn": false, "twilight_whelp_bonus": 0, "void_soul_cost": 0}, {"attack": 5, "burning_turns": 0, "cant_attack": false, "cant_attack_heroes_turn": -1, "card_class": "NEUTRAL", "card_set": "CORE", "cost": 6, "created_by": "EDR_456", "damage": 0, "divine_shield_hits": 1, "dormant_turns": 0, "dynamic_spell_damage": 0, "entity": 83, "frozen": false, "gifts": ["sleepwalker"], "health": 4, "herald_power": 1, "id": "CORE_DRG_079", "illusion_fake": false, "infinite_attack_next_turn": false, "keywords": ["rush", "charge", "elusive", "divine_shield"], "max_health": 4, "mirrex_tracker": false, "name": "Evasive Wyrm", "omen_damage": 1, "played_turn": -1, "prepared_turn": -1, "races": ["DRAGON"], "spell_damage_bonus": 0, "started_in_deck": false, "summon_moragg_on_death": false, "summoned_when_drawn": false, "twilight_whelp_bonus": 0, "void_soul_cost": 0}]}`

## Step 69 — turn 19

`P1 DISCOVER_PICK Evasive Wyrm[CORE_DRG_079] + sleepwalker`

Legal choices before action: 3

Events:

- `{"card": "CORE_DRG_079", "entity": 83, "gifts": ["sleepwalker"], "kind": "discover_pick", "player": 0, "turn": 19}`

- P1: HP=28 Armor=8 Mana=2/10 Deck=17; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#72 1/1, Warptooth#25 3/2, Chainbreaker Hogger#26 10/9, Brood Keeper#6 2/3, Carrier Whelp#73 1/2, Darkrider#3 1/1; Locations=CORE_REV_990#2 durability=3 cooldown=1; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Torch(1), Torch(1), Carrier Whelp(1), Evasive Wyrm(6)
- P2: HP=16 Armor=0 Mana=9/9 Deck=18; Weapon=none; Board=Duckling#74 1/1; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Brood Keeper(2), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4)

## Step 70 — turn 19

`P1 PLAY Torch[CATA_585] -> P1 Chainbreaker Hogger#26`

Legal choices before action: 10

Events:

- `{"card": "CATA_585", "controller": 0, "kind": "play", "player": 0, "turn": 19}`

- P1: HP=28 Armor=8 Mana=1/10 Deck=17; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#72 1/1, Warptooth#25 3/2, Chainbreaker Hogger#26 10/1, Brood Keeper#6 2/3, Carrier Whelp#73 1/2, Darkrider#3 1/1; Locations=CORE_REV_990#2 durability=3 cooldown=1; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Torch(1), Carrier Whelp(1), Evasive Wyrm(6)
- P2: HP=16 Armor=0 Mana=9/9 Deck=18; Weapon=none; Board=Duckling#74 1/1; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Brood Keeper(2), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4)

## Step 71 — turn 19

`P1 PLAY Torch[CATA_585] -> P1 Chainbreaker Hogger#26`

Legal choices before action: 6

Events:

- `{"card": "CATA_585", "controller": 0, "kind": "play", "player": 0, "turn": 19}`
- `{"card": "JAIL_384", "entity": 26, "kind": "minion_died", "player": 0, "turn": 19}`

- P1: HP=28 Armor=8 Mana=0/10 Deck=17; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#72 1/1, Warptooth#25 3/2, Brood Keeper#6 2/3, Carrier Whelp#73 1/2, Darkrider#3 1/1; Locations=CORE_REV_990#2 durability=3 cooldown=1; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Carrier Whelp(1), Evasive Wyrm(6), Torch(1)
- P2: HP=16 Armor=0 Mana=9/9 Deck=18; Weapon=none; Board=Duckling#74 1/1; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Brood Keeper(2), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4)

## Step 72 — turn 19

`P1 ATTACK Carrier Whelp#72 -> P2 Duckling#74`

Legal choices before action: 3

Events:

- `{"card": "CATA_556", "entity": 72, "kind": "minion_died", "player": 0, "turn": 19}`
- `{"card": "EDR_492t", "entity": 74, "kind": "minion_died", "player": 1, "turn": 19}`

- P1: HP=28 Armor=8 Mana=0/10 Deck=17; Weapon=Brood Keeper's Sword 2/1; Board=Warptooth#25 3/2, Brood Keeper#6 2/3, Carrier Whelp#73 1/2, Darkrider#3 1/1; Locations=CORE_REV_990#2 durability=3 cooldown=1; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Carrier Whelp(1), Evasive Wyrm(6), Torch(1)
- P2: HP=16 Armor=0 Mana=9/9 Deck=18; Weapon=none; Board=empty; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Brood Keeper(2), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4)

## Step 73 — turn 20

`P1 END_TURN`

Legal choices before action: 1

Events:

- `{"kind": "turn_end", "player": 0, "turn": 19}`
- `{"card": "CATA_582", "kind": "burn", "player": 1, "turn": 20}`
- `{"kind": "turn_start", "player": 1, "turn": 20}`

- P1: HP=28 Armor=8 Mana=0/10 Deck=17; Weapon=Brood Keeper's Sword 2/1; Board=Warptooth#25 3/2, Brood Keeper#6 2/3, Carrier Whelp#73 1/2, Darkrider#3 1/1; Locations=CORE_REV_990#2 durability=3 cooldown=1; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Carrier Whelp(1), Evasive Wyrm(6), Torch(1)
- P2: HP=16 Armor=0 Mana=10/10 Deck=17; Weapon=none; Board=empty; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Brood Keeper(2), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4)

## Step 74 — turn 20

`P2 PLAY Brood Keeper[EDR_457] -> -`

Legal choices before action: 18

Events:

- `{"card": "EDR_457", "controller": 1, "kind": "play", "player": 1, "turn": 20}`
- `{"attack": 2, "card": "EDR_457t", "durability": 2, "kind": "equip_weapon", "player": 1, "turn": 20}`

- P1: HP=28 Armor=8 Mana=0/10 Deck=17; Weapon=Brood Keeper's Sword 2/1; Board=Warptooth#25 3/2, Brood Keeper#6 2/3, Carrier Whelp#73 1/2, Darkrider#3 1/1; Locations=CORE_REV_990#2 durability=3 cooldown=1; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Carrier Whelp(1), Evasive Wyrm(6), Torch(1)
- P2: HP=16 Armor=0 Mana=8/10 Deck=17; Weapon=Brood Keeper's Sword 2/2; Board=Brood Keeper#35 2/3; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4)

## Step 75 — turn 21

`P2 END_TURN`

Legal choices before action: 23

Events:

- `{"kind": "turn_end", "player": 1, "turn": 20}`
- `{"card": "CATA_584", "kind": "draw", "player": 0, "turn": 21}`
- `{"kind": "turn_start", "player": 0, "turn": 21}`

- P1: HP=28 Armor=8 Mana=10/10 Deck=16; Weapon=Brood Keeper's Sword 2/1; Board=Warptooth#25 3/2, Brood Keeper#6 2/3, Carrier Whelp#73 1/2, Darkrider#3 1/1; Locations=CORE_REV_990#2 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Carrier Whelp(1), Evasive Wyrm(6), Torch(1), Erupting Volcano(3)
- P2: HP=16 Armor=0 Mana=8/10 Deck=17; Weapon=Brood Keeper's Sword 2/2; Board=Brood Keeper#35 2/3; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4)

## Step 76 — turn 21

`P1 ATTACK Warptooth#25 -> P2 hero`

Legal choices before action: 25

- P1: HP=28 Armor=8 Mana=10/10 Deck=16; Weapon=Brood Keeper's Sword 2/1; Board=Warptooth#25 3/2, Brood Keeper#6 2/3, Carrier Whelp#73 1/2, Darkrider#3 1/1; Locations=CORE_REV_990#2 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Carrier Whelp(1), Evasive Wyrm(6), Torch(1), Erupting Volcano(3)
- P2: HP=13 Armor=0 Mana=8/10 Deck=17; Weapon=Brood Keeper's Sword 2/2; Board=Brood Keeper#35 2/3; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4)

## Step 77 — turn 22

`P1 END_TURN`

Legal choices before action: 23

Events:

- `{"kind": "turn_end", "player": 0, "turn": 21}`
- `{"card": "CATA_585", "kind": "draw", "player": 1, "turn": 22}`
- `{"kind": "turn_start", "player": 1, "turn": 22}`

- P1: HP=28 Armor=8 Mana=10/10 Deck=16; Weapon=Brood Keeper's Sword 2/1; Board=Warptooth#25 3/2, Brood Keeper#6 2/3, Carrier Whelp#73 1/2, Darkrider#3 1/1; Locations=CORE_REV_990#2 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Carrier Whelp(1), Evasive Wyrm(6), Torch(1), Erupting Volcano(3)
- P2: HP=13 Armor=0 Mana=10/10 Deck=16; Weapon=Brood Keeper's Sword 2/2; Board=Brood Keeper#35 2/3; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4), Torch(1)

## Step 78 — turn 22

`P2 ATTACK Brood Keeper#35 -> P1 Brood Keeper#6`

Legal choices before action: 29

- P1: HP=28 Armor=8 Mana=10/10 Deck=16; Weapon=Brood Keeper's Sword 2/1; Board=Warptooth#25 3/2, Brood Keeper#6 2/1, Carrier Whelp#73 1/2, Darkrider#3 1/1; Locations=CORE_REV_990#2 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Carrier Whelp(1), Evasive Wyrm(6), Torch(1), Erupting Volcano(3)
- P2: HP=13 Armor=0 Mana=10/10 Deck=16; Weapon=Brood Keeper's Sword 2/2; Board=Brood Keeper#35 2/1; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4), Torch(1)

## Step 79 — turn 22

`P2 HERO_POWER Armor Up`

Legal choices before action: 26

Events:

- `{"amount": 2, "kind": "gain_armor", "player": 1, "turn": 22}`
- `{"kind": "hero_power", "player": 1, "turn": 22}`

- P1: HP=28 Armor=8 Mana=10/10 Deck=16; Weapon=Brood Keeper's Sword 2/1; Board=Warptooth#25 3/2, Brood Keeper#6 2/1, Carrier Whelp#73 1/2, Darkrider#3 1/1; Locations=CORE_REV_990#2 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Carrier Whelp(1), Evasive Wyrm(6), Torch(1), Erupting Volcano(3)
- P2: HP=13 Armor=2 Mana=8/10 Deck=16; Weapon=Brood Keeper's Sword 2/2; Board=Brood Keeper#35 2/1; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4), Torch(1)

## Step 80 — turn 23

`P2 END_TURN`

Legal choices before action: 25

Events:

- `{"kind": "turn_end", "player": 1, "turn": 22}`
- `{"card": "CORE_SW_066", "kind": "draw", "player": 0, "turn": 23}`
- `{"kind": "turn_start", "player": 0, "turn": 23}`

- P1: HP=28 Armor=8 Mana=10/10 Deck=15; Weapon=Brood Keeper's Sword 2/1; Board=Warptooth#25 3/2, Brood Keeper#6 2/1, Carrier Whelp#73 1/2, Darkrider#3 1/1; Locations=CORE_REV_990#2 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Carrier Whelp(1), Evasive Wyrm(6), Torch(1), Erupting Volcano(3), Royal Librarian(4)
- P2: HP=13 Armor=2 Mana=8/10 Deck=16; Weapon=Brood Keeper's Sword 2/2; Board=Brood Keeper#35 2/1; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4), Torch(1)

## Step 81 — turn 24

`P1 END_TURN`

Legal choices before action: 33

Events:

- `{"kind": "turn_end", "player": 0, "turn": 23}`
- `{"card": "CAP_107", "kind": "burn", "player": 1, "turn": 24}`
- `{"kind": "turn_start", "player": 1, "turn": 24}`

- P1: HP=28 Armor=8 Mana=10/10 Deck=15; Weapon=Brood Keeper's Sword 2/1; Board=Warptooth#25 3/2, Brood Keeper#6 2/1, Carrier Whelp#73 1/2, Darkrider#3 1/1; Locations=CORE_REV_990#2 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Carrier Whelp(1), Evasive Wyrm(6), Torch(1), Erupting Volcano(3), Royal Librarian(4)
- P2: HP=13 Armor=2 Mana=10/10 Deck=15; Weapon=Brood Keeper's Sword 2/2; Board=Brood Keeper#35 2/1; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4), Torch(1)

## Step 82 — turn 24

`P2 PLAY Torch[CATA_585] -> P2 Brood Keeper#35`

Legal choices before action: 31

Events:

- `{"card": "CATA_585", "controller": 1, "kind": "play", "player": 1, "turn": 24}`
- `{"card": "EDR_457", "entity": 35, "kind": "minion_died", "player": 1, "turn": 24}`

- P1: HP=28 Armor=8 Mana=10/10 Deck=15; Weapon=Brood Keeper's Sword 2/1; Board=Warptooth#25 3/2, Brood Keeper#6 2/1, Carrier Whelp#73 1/2, Darkrider#3 1/1; Locations=CORE_REV_990#2 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Carrier Whelp(1), Evasive Wyrm(6), Torch(1), Erupting Volcano(3), Royal Librarian(4)
- P2: HP=13 Armor=2 Mana=9/10 Deck=15; Weapon=Brood Keeper's Sword 2/2; Board=empty; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4), Torch(1)

## Step 83 — turn 25

`P2 END_TURN`

Legal choices before action: 24

Events:

- `{"kind": "turn_end", "player": 1, "turn": 24}`
- `{"card": "CAP_107", "kind": "draw", "player": 0, "turn": 25}`
- `{"kind": "turn_start", "player": 0, "turn": 25}`

- P1: HP=28 Armor=8 Mana=10/10 Deck=14; Weapon=Brood Keeper's Sword 2/1; Board=Warptooth#25 3/2, Brood Keeper#6 2/1, Carrier Whelp#73 1/2, Darkrider#3 1/1; Locations=CORE_REV_990#2 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Carrier Whelp(1), Evasive Wyrm(6), Torch(1), Erupting Volcano(3), Royal Librarian(4), Cannonmaster(1)
- P2: HP=13 Armor=2 Mana=9/10 Deck=15; Weapon=Brood Keeper's Sword 2/2; Board=empty; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4), Torch(1)

## Step 84 — turn 25

`P1 HERO_POWER Armor Up`

Legal choices before action: 26

Events:

- `{"amount": 2, "kind": "gain_armor", "player": 0, "turn": 25}`
- `{"kind": "hero_power", "player": 0, "turn": 25}`

- P1: HP=28 Armor=10 Mana=8/10 Deck=14; Weapon=Brood Keeper's Sword 2/1; Board=Warptooth#25 3/2, Brood Keeper#6 2/1, Carrier Whelp#73 1/2, Darkrider#3 1/1; Locations=CORE_REV_990#2 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Carrier Whelp(1), Evasive Wyrm(6), Torch(1), Erupting Volcano(3), Royal Librarian(4), Cannonmaster(1)
- P2: HP=13 Armor=2 Mana=9/10 Deck=15; Weapon=Brood Keeper's Sword 2/2; Board=empty; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4), Torch(1)

## Step 85 — turn 25

`P1 PLAY Erupting Volcano[CATA_584] -> -`

Legal choices before action: 25

Events:

- `{"card": "CATA_584", "controller": 0, "kind": "play", "player": 0, "turn": 25}`

- P1: HP=28 Armor=10 Mana=5/10 Deck=14; Weapon=Brood Keeper's Sword 2/1; Board=Warptooth#25 3/2, Brood Keeper#6 2/1, Carrier Whelp#73 1/2, Darkrider#3 1/1; Locations=CORE_REV_990#2 durability=3 cooldown=0, CATA_584#21 durability=3 cooldown=1; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Carrier Whelp(1), Evasive Wyrm(6), Torch(1), Royal Librarian(4), Cannonmaster(1)
- P2: HP=13 Armor=2 Mana=9/10 Deck=15; Weapon=Brood Keeper's Sword 2/2; Board=empty; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4), Torch(1)

## Step 86 — turn 25

`P1 ATTACK Carrier Whelp#73 -> P2 hero`

Legal choices before action: 23

- P1: HP=28 Armor=10 Mana=5/10 Deck=14; Weapon=Brood Keeper's Sword 2/1; Board=Warptooth#25 3/2, Brood Keeper#6 2/1, Carrier Whelp#73 1/2, Darkrider#3 1/1; Locations=CORE_REV_990#2 durability=3 cooldown=0, CATA_584#21 durability=3 cooldown=1; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Carrier Whelp(1), Evasive Wyrm(6), Torch(1), Royal Librarian(4), Cannonmaster(1)
- P2: HP=13 Armor=1 Mana=9/10 Deck=15; Weapon=Brood Keeper's Sword 2/2; Board=empty; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4), Torch(1)

## Step 87 — turn 25

`P1 HERO_ATTACK -> P2 hero`

Legal choices before action: 22

Events:

- `{"card": "EDR_457t", "kind": "weapon_destroyed", "player": 0, "turn": 25}`

- P1: HP=28 Armor=10 Mana=5/10 Deck=14; Weapon=none; Board=Warptooth#25 3/2, Brood Keeper#6 2/1, Carrier Whelp#73 1/2, Darkrider#3 1/1; Locations=CORE_REV_990#2 durability=3 cooldown=0, CATA_584#21 durability=3 cooldown=1; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Carrier Whelp(1), Evasive Wyrm(6), Torch(1), Royal Librarian(4), Cannonmaster(1)
- P2: HP=12 Armor=0 Mana=9/10 Deck=15; Weapon=Brood Keeper's Sword 2/2; Board=empty; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4), Torch(1)

## Step 88 — turn 26

`P1 END_TURN`

Legal choices before action: 21

Events:

- `{"kind": "turn_end", "player": 0, "turn": 25}`
- `{"card": "CORE_SW_066", "kind": "burn", "player": 1, "turn": 26}`
- `{"kind": "turn_start", "player": 1, "turn": 26}`

- P1: HP=28 Armor=10 Mana=5/10 Deck=14; Weapon=none; Board=Warptooth#25 3/2, Brood Keeper#6 2/1, Carrier Whelp#73 1/2, Darkrider#3 1/1; Locations=CORE_REV_990#2 durability=3 cooldown=0, CATA_584#21 durability=3 cooldown=1; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Carrier Whelp(1), Evasive Wyrm(6), Torch(1), Royal Librarian(4), Cannonmaster(1)
- P2: HP=12 Armor=0 Mana=10/10 Deck=14; Weapon=Brood Keeper's Sword 2/2; Board=empty; Locations=CATA_584#51 durability=3 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4), Torch(1)

## Step 89 — turn 26

`P2 LOCATION CATA_584#51 -> -`

Legal choices before action: 24

Events:

- `{"card": "EDR_457", "entity": 6, "kind": "minion_died", "player": 0, "turn": 26}`

- P1: HP=28 Armor=9 Mana=5/10 Deck=14; Weapon=none; Board=Warptooth#25 3/1, Carrier Whelp#73 1/2, Darkrider#3 1/1; Locations=CORE_REV_990#2 durability=3 cooldown=0, CATA_584#21 durability=3 cooldown=1; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Carrier Whelp(1), Evasive Wyrm(6), Torch(1), Royal Librarian(4), Cannonmaster(1)
- P2: HP=12 Armor=0 Mana=10/10 Deck=14; Weapon=Brood Keeper's Sword 2/2; Board=empty; Locations=CATA_584#51 durability=2 cooldown=1; Hand=Sanguine Depths(1), Mother Duck(4), Windpeak Wyrm(8), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4), Torch(1)

## Step 90 — turn 26

`P2 PLAY Windpeak Wyrm[TLC_600] -> P1 Darkrider#3`

Legal choices before action: 20

Events:

- `{"card": "TLC_600", "controller": 1, "kind": "play", "player": 1, "turn": 26}`
- `{"amount": 5, "kind": "gain_armor", "player": 1, "turn": 26}`
- `{"card": "EDR_456", "entity": 3, "kind": "minion_died", "player": 0, "turn": 26}`

- P1: HP=28 Armor=9 Mana=5/10 Deck=14; Weapon=none; Board=Warptooth#25 3/1, Carrier Whelp#73 1/2; Locations=CORE_REV_990#2 durability=3 cooldown=0, CATA_584#21 durability=3 cooldown=1; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Carrier Whelp(1), Evasive Wyrm(6), Torch(1), Royal Librarian(4), Cannonmaster(1)
- P2: HP=12 Armor=5 Mana=2/10 Deck=14; Weapon=Brood Keeper's Sword 2/2; Board=Windpeak Wyrm#41 6/6; Locations=CATA_584#51 durability=2 cooldown=1; Hand=Sanguine Depths(1), Mother Duck(4), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4), Torch(1)

## Step 91 — turn 26

`P2 PLAY Torch[CATA_585] -> P1 Warptooth#25`

Legal choices before action: 9

Events:

- `{"card": "CATA_585", "controller": 1, "kind": "play", "player": 1, "turn": 26}`
- `{"card": "JAIL_421", "entity": 25, "kind": "minion_died", "player": 0, "turn": 26}`

- P1: HP=28 Armor=9 Mana=5/10 Deck=14; Weapon=none; Board=Carrier Whelp#73 1/2; Locations=CORE_REV_990#2 durability=3 cooldown=0, CATA_584#21 durability=3 cooldown=1; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Carrier Whelp(1), Evasive Wyrm(6), Torch(1), Royal Librarian(4), Cannonmaster(1)
- P2: HP=12 Armor=5 Mana=1/10 Deck=14; Weapon=Brood Keeper's Sword 2/2; Board=Windpeak Wyrm#41 6/6; Locations=CATA_584#51 durability=2 cooldown=1; Hand=Sanguine Depths(1), Mother Duck(4), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4), Torch(1)

## Step 92 — turn 27

`P2 END_TURN`

Legal choices before action: 6

Events:

- `{"kind": "turn_end", "player": 1, "turn": 26}`
- `{"card": "END_033", "kind": "draw", "player": 0, "turn": 27}`
- `{"kind": "turn_start", "player": 0, "turn": 27}`

- P1: HP=28 Armor=9 Mana=10/10 Deck=13; Weapon=none; Board=Carrier Whelp#73 1/2; Locations=CORE_REV_990#2 durability=3 cooldown=0, CATA_584#21 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Carrier Whelp(1), Evasive Wyrm(6), Torch(1), Royal Librarian(4), Cannonmaster(1), Prescient Slitherdrake(4)
- P2: HP=12 Armor=5 Mana=1/10 Deck=14; Weapon=Brood Keeper's Sword 2/2; Board=Windpeak Wyrm#41 6/6; Locations=CATA_584#51 durability=2 cooldown=1; Hand=Sanguine Depths(1), Mother Duck(4), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4), Torch(1)

## Step 93 — turn 27

`P1 LOCATION CORE_REV_990#2 -> P2 Windpeak Wyrm#41`

Legal choices before action: 18

- P1: HP=28 Armor=9 Mana=10/10 Deck=13; Weapon=none; Board=Carrier Whelp#73 1/2; Locations=CORE_REV_990#2 durability=2 cooldown=1, CATA_584#21 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Carrier Whelp(1), Evasive Wyrm(6), Torch(1), Royal Librarian(4), Cannonmaster(1), Prescient Slitherdrake(4)
- P2: HP=12 Armor=5 Mana=1/10 Deck=14; Weapon=Brood Keeper's Sword 2/2; Board=Windpeak Wyrm#41 8/5; Locations=CATA_584#51 durability=2 cooldown=1; Hand=Sanguine Depths(1), Mother Duck(4), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4), Torch(1)

## Step 94 — turn 27

`P1 PLAY Evasive Wyrm[CORE_DRG_079] -> -`

Legal choices before action: 17

Events:

- `{"card": "CORE_DRG_079", "controller": 0, "kind": "play", "player": 0, "turn": 27}`

- P1: HP=28 Armor=9 Mana=4/10 Deck=13; Weapon=none; Board=Carrier Whelp#73 1/2, Evasive Wyrm#83 5/4; Locations=CORE_REV_990#2 durability=2 cooldown=1, CATA_584#21 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Carrier Whelp(1), Torch(1), Royal Librarian(4), Cannonmaster(1), Prescient Slitherdrake(4)
- P2: HP=12 Armor=5 Mana=1/10 Deck=14; Weapon=Brood Keeper's Sword 2/2; Board=Windpeak Wyrm#41 8/5; Locations=CATA_584#51 durability=2 cooldown=1; Hand=Sanguine Depths(1), Mother Duck(4), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4), Torch(1)

## Step 95 — turn 27

`P1 ATTACK Carrier Whelp#73 -> P2 Windpeak Wyrm#41`

Legal choices before action: 19

Events:

- `{"card": "CATA_556", "entity": 73, "kind": "minion_died", "player": 0, "turn": 27}`

- P1: HP=28 Armor=9 Mana=4/10 Deck=13; Weapon=none; Board=Evasive Wyrm#83 5/4; Locations=CORE_REV_990#2 durability=2 cooldown=1, CATA_584#21 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Carrier Whelp(1), Torch(1), Royal Librarian(4), Cannonmaster(1), Prescient Slitherdrake(4)
- P2: HP=12 Armor=5 Mana=1/10 Deck=14; Weapon=Brood Keeper's Sword 2/2; Board=Windpeak Wyrm#41 8/4; Locations=CATA_584#51 durability=2 cooldown=1; Hand=Sanguine Depths(1), Mother Duck(4), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4), Torch(1)

## Step 96 — turn 28

`P1 END_TURN`

Legal choices before action: 16

Events:

- `{"kind": "turn_end", "player": 0, "turn": 27}`
- `{"card": "CAP_105", "kind": "draw", "player": 1, "turn": 28}`
- `{"kind": "turn_start", "player": 1, "turn": 28}`

- P1: HP=28 Armor=9 Mana=4/10 Deck=13; Weapon=none; Board=Evasive Wyrm#83 5/4; Locations=CORE_REV_990#2 durability=2 cooldown=1, CATA_584#21 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Carrier Whelp(1), Torch(1), Royal Librarian(4), Cannonmaster(1), Prescient Slitherdrake(4)
- P2: HP=12 Armor=5 Mana=10/10 Deck=13; Weapon=Brood Keeper's Sword 2/2; Board=Windpeak Wyrm#41 8/4; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4), Torch(1), Hook n' Heave(2)

## Step 97 — turn 28

`P2 PLAY Hook n' Heave[CAP_105] -> -`

Legal choices before action: 17

Events:

- `{"card": "CAP_105", "controller": 1, "kind": "play", "player": 1, "turn": 28}`
- `{"kind": "discover_offer", "options": [{"card": "CAP_107", "entity": 84, "gifts": []}], "player": 1, "profile": "closed_pool", "turn": 28}`

- P1: HP=28 Armor=9 Mana=4/10 Deck=13; Weapon=none; Board=Evasive Wyrm#83 5/4; Locations=CORE_REV_990#2 durability=2 cooldown=1, CATA_584#21 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Carrier Whelp(1), Torch(1), Royal Librarian(4), Cannonmaster(1), Prescient Slitherdrake(4)
- P2: HP=12 Armor=5 Mana=8/10 Deck=13; Weapon=Brood Keeper's Sword 2/2; Board=Windpeak Wyrm#41 8/4; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4), Torch(1)
- Pending decision: `{"kind": "DISCOVER", "options": [{"attack": 3, "burning_turns": 0, "cant_attack": false, "cant_attack_heroes_turn": -1, "card_class": "WARRIOR", "card_set": "ESCAPEFROM_VIOLET_HOLD", "cost": 1, "created_by": "CAP_105", "damage": 0, "divine_shield_hits": 0, "dormant_turns": 0, "dynamic_spell_damage": 0, "entity": 84, "frozen": false, "gifts": [], "health": 1, "herald_power": 1, "id": "CAP_107", "illusion_fake": false, "infinite_attack_next_turn": false, "keywords": [], "max_health": 1, "mirrex_tracker": false, "name": "Cannonmaster", "omen_damage": 1, "played_turn": -1, "prepared_turn": -1, "races": ["PIRATE", "DRAENEI"], "spell_damage_bonus": 0, "started_in_deck": false, "summon_moragg_on_death": false, "summoned_when_drawn": false, "twilight_whelp_bonus": 0, "void_soul_cost": 0}]}`

## Step 98 — turn 28

`P2 DISCOVER_PICK Cannonmaster[CAP_107]`

Legal choices before action: 1

Events:

- `{"card": "CAP_107", "entity": 84, "gifts": [], "kind": "discover_pick", "player": 1, "turn": 28}`

- P1: HP=28 Armor=9 Mana=4/10 Deck=13; Weapon=none; Board=Evasive Wyrm#83 5/4; Locations=CORE_REV_990#2 durability=2 cooldown=1, CATA_584#21 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Carrier Whelp(1), Torch(1), Royal Librarian(4), Cannonmaster(1), Prescient Slitherdrake(4)
- P2: HP=12 Armor=5 Mana=8/10 Deck=13; Weapon=Brood Keeper's Sword 2/2; Board=Windpeak Wyrm#41 8/4, Cutlass Cutthroat#85 1/1, Cutlass Cutthroat#86 1/1; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4), Torch(1), Cannonmaster(1)

## Step 99 — turn 28

`P2 PLAY Cannonmaster[CAP_107] -> -`

Legal choices before action: 19

Events:

- `{"card": "CAP_107", "controller": 1, "kind": "play", "player": 1, "turn": 28}`
- `{"card": "CAP_107t", "entity": 87, "kind": "generated_to_hand", "player": 1, "source": "CAP_107", "turn": 28}`

- P1: HP=28 Armor=9 Mana=4/10 Deck=13; Weapon=none; Board=Evasive Wyrm#83 5/4; Locations=CORE_REV_990#2 durability=2 cooldown=1, CATA_584#21 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Carrier Whelp(1), Torch(1), Royal Librarian(4), Cannonmaster(1), Prescient Slitherdrake(4)
- P2: HP=12 Armor=5 Mana=7/10 Deck=13; Weapon=Brood Keeper's Sword 2/2; Board=Windpeak Wyrm#41 8/4, Cutlass Cutthroat#85 1/1, Cutlass Cutthroat#86 1/1, Cannonmaster#84 3/1; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4), Torch(1), Cannoneer(1)

## Step 100 — turn 28

`P2 PLAY Torch[CATA_585] -> P2 Windpeak Wyrm#41`

Legal choices before action: 18

Events:

- `{"card": "CATA_585", "controller": 1, "kind": "play", "player": 1, "turn": 28}`
- `{"card": "TLC_600", "entity": 41, "kind": "minion_died", "player": 1, "turn": 28}`

- P1: HP=28 Armor=9 Mana=4/10 Deck=13; Weapon=none; Board=Evasive Wyrm#83 5/4; Locations=CORE_REV_990#2 durability=2 cooldown=1, CATA_584#21 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Carrier Whelp(1), Torch(1), Royal Librarian(4), Cannonmaster(1), Prescient Slitherdrake(4)
- P2: HP=12 Armor=5 Mana=6/10 Deck=13; Weapon=Brood Keeper's Sword 2/2; Board=Cutlass Cutthroat#85 1/1, Cutlass Cutthroat#86 1/1, Cannonmaster#84 3/1; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Prescient Slitherdrake(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1)

## Step 101 — turn 28

`P2 PLAY Prescient Slitherdrake[END_033] -> -`

Legal choices before action: 15

Events:

- `{"card": "END_033", "controller": 1, "kind": "play", "player": 1, "turn": 28}`

- P1: HP=28 Armor=9 Mana=4/10 Deck=13; Weapon=none; Board=Evasive Wyrm#83 5/4; Locations=CORE_REV_990#2 durability=2 cooldown=1, CATA_584#21 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Carrier Whelp(1), Torch(1), Royal Librarian(4), Cannonmaster(1), Prescient Slitherdrake(4)
- P2: HP=12 Armor=5 Mana=2/10 Deck=13; Weapon=Brood Keeper's Sword 2/2; Board=Cutlass Cutthroat#85 1/1, Cutlass Cutthroat#86 1/1, Cannonmaster#84 3/1, Prescient Slitherdrake#46 5/8; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1)

## Step 102 — turn 29

`P2 END_TURN`

Legal choices before action: 11

Events:

- `{"kind": "turn_end", "player": 1, "turn": 28}`
- `{"card": "FIR_939", "kind": "draw", "player": 0, "turn": 29}`
- `{"kind": "turn_start", "player": 0, "turn": 29}`

- P1: HP=28 Armor=9 Mana=10/10 Deck=12; Weapon=none; Board=Evasive Wyrm#83 5/4; Locations=CORE_REV_990#2 durability=2 cooldown=0, CATA_584#21 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Carrier Whelp(1), Torch(1), Royal Librarian(4), Cannonmaster(1), Prescient Slitherdrake(4), Shadowflame Suffusion(2)
- P2: HP=12 Armor=5 Mana=2/10 Deck=13; Weapon=Brood Keeper's Sword 2/2; Board=Cutlass Cutthroat#85 1/1, Cutlass Cutthroat#86 1/1, Cannonmaster#84 3/1, Prescient Slitherdrake#46 5/8; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1)

## Step 103 — turn 29

`P1 ATTACK Evasive Wyrm#83 -> P2 Cutlass Cutthroat#85`

Legal choices before action: 32

Events:

- `{"card": "CAP_105t", "entity": 85, "kind": "minion_died", "player": 1, "turn": 29}`

- P1: HP=28 Armor=9 Mana=10/10 Deck=12; Weapon=none; Board=Evasive Wyrm#83 5/4; Locations=CORE_REV_990#2 durability=2 cooldown=0, CATA_584#21 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Carrier Whelp(1), Torch(1), Royal Librarian(4), Cannonmaster(1), Prescient Slitherdrake(4), Shadowflame Suffusion(2)
- P2: HP=12 Armor=5 Mana=2/10 Deck=13; Weapon=Brood Keeper's Sword 2/2; Board=Cutlass Cutthroat#86 1/1, Cannonmaster#84 3/1, Prescient Slitherdrake#46 5/8; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1)

## Step 104 — turn 29

`P1 PLAY Shadowflame Suffusion[FIR_939] -> P1 hero`

Legal choices before action: 24

Events:

- `{"card": "FIR_939", "controller": 0, "kind": "play", "player": 0, "turn": 29}`
- `{"kind": "discover_offer", "options": [{"card": "JAIL_029", "entity": 88, "gifts": ["well_rested"]}, {"card": "JAIL_435", "entity": 89, "gifts": ["sweet_dreams"]}, {"card": "DINO_400", "entity": 90, "gifts": ["persisting_horror"]}], "player": 0, "profile": "closed_pool", "turn": 29}`

- P1: HP=28 Armor=7 Mana=8/10 Deck=12; Weapon=none; Board=Evasive Wyrm#83 5/4; Locations=CORE_REV_990#2 durability=2 cooldown=0, CATA_584#21 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Carrier Whelp(1), Torch(1), Royal Librarian(4), Cannonmaster(1), Prescient Slitherdrake(4)
- P2: HP=12 Armor=5 Mana=2/10 Deck=13; Weapon=Brood Keeper's Sword 2/2; Board=Cutlass Cutthroat#86 1/1, Cannonmaster#84 3/1, Prescient Slitherdrake#46 5/8; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1)
- Pending decision: `{"kind": "DISCOVER", "options": [{"attack": 3, "burning_turns": 0, "cant_attack": false, "cant_attack_heroes_turn": -1, "card_class": "WARRIOR", "card_set": "ESCAPEFROM_VIOLET_HOLD", "cost": 3, "created_by": "FIR_939", "damage": 0, "divine_shield_hits": 0, "dormant_turns": 0, "dynamic_spell_damage": 0, "entity": 88, "frozen": false, "gifts": ["well_rested"], "health": 8, "herald_power": 1, "id": "JAIL_029", "illusion_fake": false, "infinite_attack_next_turn": false, "keywords": ["elusive"], "max_health": 8, "mirrex_tracker": false, "name": "Rioter", "omen_damage": 1, "played_turn": -1, "prepared_turn": -1, "races": [], "spell_damage_bonus": 0, "started_in_deck": false, "summon_moragg_on_death": false, "summoned_when_drawn": false, "twilight_whelp_bonus": 0, "void_soul_cost": 0}, {"attack": 8, "burning_turns": 0, "cant_attack": false, "cant_attack_heroes_turn": -1, "card_class": "WARRIOR", "card_set": "ESCAPEFROM_VIOLET_HOLD", "cost": 7, "created_by": "FIR_939", "damage": 0, "divine_shield_hits": 0, "dormant_turns": 0, "dynamic_spell_damage": 0, "entity": 89, "frozen": false, "gifts": ["sweet_dreams"], "health": 17, "herald_power": 1, "id": "JAIL_435", "illusion_fake": false, "infinite_attack_next_turn": false, "keywords": [], "max_health": 17, "mirrex_tracker": false, "name": "Rampaging Hound", "omen_damage": 1, "played_turn": -1, "prepared_turn": -1, "races": ["ELEMENTAL", "BEAST"], "spell_damage_bonus": 0, "started_in_deck": false, "summon_moragg_on_death": false, "summoned_when_drawn": false, "twilight_whelp_bonus": 0, "void_soul_cost": 0}, {"attack": 4, "burning_turns": 0, "cant_attack": false, "cant_attack_heroes_turn": -1, "card_class": "WARRIOR", "card_set": "THE_LOST_CITY", "cost": 3, "created_by": "FIR_939", "damage": 0, "divine_shield_hits": 0, "dormant_turns": 0, "dynamic_spell_damage": 0, "entity": 90, "frozen": false, "gifts": ["persisting_horror"], "health": 3, "herald_power": 1, "id": "DINO_400", "illusion_fake": false, "infinite_attack_next_turn": false, "keywords": ["reborn"], "max_health": 3, "mirrex_tracker": false, "name": "Barricade Basher", "omen_damage": 1, "played_turn": -1, "prepared_turn": -1, "races": ["BEAST"], "spell_damage_bonus": 0, "started_in_deck": false, "summon_moragg_on_death": false, "summoned_when_drawn": false, "twilight_whelp_bonus": 0, "void_soul_cost": 0}]}`

## Step 105 — turn 29

`P1 DISCOVER_PICK Barricade Basher[DINO_400] + persisting_horror`

Legal choices before action: 3

Events:

- `{"card": "DINO_400", "entity": 90, "gifts": ["persisting_horror"], "kind": "discover_pick", "player": 0, "turn": 29}`

- P1: HP=28 Armor=7 Mana=8/10 Deck=12; Weapon=none; Board=Evasive Wyrm#83 5/4; Locations=CORE_REV_990#2 durability=2 cooldown=0, CATA_584#21 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Prescient Slitherdrake(4), Carrier Whelp(1), Torch(1), Royal Librarian(4), Cannonmaster(1), Prescient Slitherdrake(4), Barricade Basher(3)
- P2: HP=12 Armor=5 Mana=2/10 Deck=13; Weapon=Brood Keeper's Sword 2/2; Board=Cutlass Cutthroat#86 1/1, Cannonmaster#84 3/1, Prescient Slitherdrake#46 5/8; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1)

## Step 106 — turn 29

`P1 PLAY Prescient Slitherdrake[END_033] -> -`

Legal choices before action: 20

Events:

- `{"card": "END_033", "controller": 0, "kind": "play", "player": 0, "turn": 29}`

- P1: HP=28 Armor=7 Mana=4/10 Deck=12; Weapon=none; Board=Evasive Wyrm#83 5/4, Prescient Slitherdrake#16 5/8; Locations=CORE_REV_990#2 durability=2 cooldown=0, CATA_584#21 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Mother Duck(4), Carrier Whelp(1), Torch(1), Royal Librarian(4), Cannonmaster(1), Prescient Slitherdrake(4), Barricade Basher(3)
- P2: HP=12 Armor=5 Mana=2/10 Deck=13; Weapon=Brood Keeper's Sword 2/2; Board=Cutlass Cutthroat#86 1/1, Cannonmaster#84 3/1, Prescient Slitherdrake#46 5/8; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1)

## Step 107 — turn 29

`P1 PLAY Mother Duck[EDR_492] -> -`

Legal choices before action: 21

Events:

- `{"card": "EDR_492", "controller": 0, "kind": "play", "player": 0, "turn": 29}`

- P1: HP=28 Armor=7 Mana=0/10 Deck=12; Weapon=none; Board=Evasive Wyrm#83 5/4, Prescient Slitherdrake#16 5/8, Mother Duck#7 2/3, Duckling#91 1/1, Duckling#92 1/1; Locations=CORE_REV_990#2 durability=2 cooldown=0, CATA_584#21 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Carrier Whelp(1), Torch(1), Royal Librarian(4), Cannonmaster(1), Prescient Slitherdrake(4), Barricade Basher(3)
- P2: HP=12 Armor=5 Mana=2/10 Deck=13; Weapon=Brood Keeper's Sword 2/2; Board=Cutlass Cutthroat#86 1/1, Cannonmaster#84 3/1, Prescient Slitherdrake#46 5/8; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1)

## Step 108 — turn 30

`P1 END_TURN`

Legal choices before action: 16

Events:

- `{"kind": "turn_end", "player": 0, "turn": 29}`
- `{"card": "EDR_457", "kind": "draw", "player": 1, "turn": 30}`
- `{"kind": "turn_start", "player": 1, "turn": 30}`

- P1: HP=28 Armor=7 Mana=0/10 Deck=12; Weapon=none; Board=Evasive Wyrm#83 5/4, Prescient Slitherdrake#16 5/8, Mother Duck#7 2/3, Duckling#91 1/1, Duckling#92 1/1; Locations=CORE_REV_990#2 durability=2 cooldown=0, CATA_584#21 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Carrier Whelp(1), Torch(1), Royal Librarian(4), Cannonmaster(1), Prescient Slitherdrake(4), Barricade Basher(3)
- P2: HP=12 Armor=5 Mana=10/10 Deck=12; Weapon=Brood Keeper's Sword 2/2; Board=Cutlass Cutthroat#86 1/1, Cannonmaster#84 3/1, Prescient Slitherdrake#46 5/8; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2)

## Step 109 — turn 30

`P2 ATTACK Cutlass Cutthroat#86 -> P1 Prescient Slitherdrake#16`

Legal choices before action: 36

Events:

- `{"card": "CAP_105t", "entity": 86, "kind": "minion_died", "player": 1, "turn": 30}`

- P1: HP=28 Armor=7 Mana=0/10 Deck=12; Weapon=none; Board=Evasive Wyrm#83 5/4, Prescient Slitherdrake#16 5/7, Mother Duck#7 2/3, Duckling#91 1/1, Duckling#92 1/1; Locations=CORE_REV_990#2 durability=2 cooldown=0, CATA_584#21 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Carrier Whelp(1), Torch(1), Royal Librarian(4), Cannonmaster(1), Prescient Slitherdrake(4), Barricade Basher(3)
- P2: HP=12 Armor=5 Mana=10/10 Deck=12; Weapon=Brood Keeper's Sword 2/2; Board=Cannonmaster#84 3/1, Prescient Slitherdrake#46 5/8; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2)

## Step 110 — turn 30

`P2 HERO_ATTACK -> P1 hero`

Legal choices before action: 30

- P1: HP=28 Armor=5 Mana=0/10 Deck=12; Weapon=none; Board=Evasive Wyrm#83 5/4, Prescient Slitherdrake#16 5/7, Mother Duck#7 2/3, Duckling#91 1/1, Duckling#92 1/1; Locations=CORE_REV_990#2 durability=2 cooldown=0, CATA_584#21 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Carrier Whelp(1), Torch(1), Royal Librarian(4), Cannonmaster(1), Prescient Slitherdrake(4), Barricade Basher(3)
- P2: HP=12 Armor=5 Mana=10/10 Deck=12; Weapon=Brood Keeper's Sword 2/1; Board=Cannonmaster#84 3/1, Prescient Slitherdrake#46 5/8; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), The Great Dracorex(8), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2)

## Step 111 — turn 30

`P2 PLAY The Great Dracorex[DINO_401] -> -`

Legal choices before action: 24

Events:

- `{"card": "DINO_401", "controller": 1, "kind": "play", "player": 1, "turn": 30}`

- P1: HP=28 Armor=5 Mana=0/10 Deck=12; Weapon=none; Board=Evasive Wyrm#83 5/4, Prescient Slitherdrake#16 5/7, Mother Duck#7 2/3, Duckling#91 1/1, Duckling#92 1/1; Locations=CORE_REV_990#2 durability=2 cooldown=0, CATA_584#21 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Carrier Whelp(1), Torch(1), Royal Librarian(4), Cannonmaster(1), Prescient Slitherdrake(4), Barricade Basher(3)
- P2: HP=12 Armor=5 Mana=2/10 Deck=12; Weapon=Brood Keeper's Sword 2/1; Board=Cannonmaster#84 3/1, Prescient Slitherdrake#46 5/8, The Great Dracorex#70 5/12; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2)

## Step 112 — turn 30

`P2 ATTACK Cannonmaster#84 -> P1 Prescient Slitherdrake#16`

Legal choices before action: 25

Events:

- `{"card": "CAP_107", "entity": 84, "kind": "minion_died", "player": 1, "turn": 30}`

- P1: HP=28 Armor=5 Mana=0/10 Deck=12; Weapon=none; Board=Evasive Wyrm#83 5/4, Prescient Slitherdrake#16 5/4, Mother Duck#7 2/3, Duckling#91 1/1, Duckling#92 1/1; Locations=CORE_REV_990#2 durability=2 cooldown=0, CATA_584#21 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Carrier Whelp(1), Torch(1), Royal Librarian(4), Cannonmaster(1), Prescient Slitherdrake(4), Barricade Basher(3)
- P2: HP=12 Armor=5 Mana=2/10 Deck=12; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 5/8, The Great Dracorex#70 5/12; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2)

## Step 113 — turn 30

`P2 ATTACK Prescient Slitherdrake#46 -> P1 hero`

Legal choices before action: 19

- P1: HP=28 Armor=0 Mana=0/10 Deck=12; Weapon=none; Board=Evasive Wyrm#83 5/4, Prescient Slitherdrake#16 5/4, Mother Duck#7 2/3, Duckling#91 1/1, Duckling#92 1/1; Locations=CORE_REV_990#2 durability=2 cooldown=0, CATA_584#21 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Carrier Whelp(1), Torch(1), Royal Librarian(4), Cannonmaster(1), Prescient Slitherdrake(4), Barricade Basher(3)
- P2: HP=12 Armor=5 Mana=2/10 Deck=12; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 5/8, The Great Dracorex#70 5/12; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2)

## Step 114 — turn 30

`P2 ATTACK The Great Dracorex#70 -> P1 Evasive Wyrm#83`

Legal choices before action: 13

Events:

- `{"card": "CORE_DRG_079", "entity": 83, "kind": "minion_died", "player": 0, "turn": 30}`
- `{"card": "END_033", "entity": 16, "kind": "minion_died", "player": 0, "turn": 30}`
- `{"card": "EDR_492", "entity": 7, "kind": "minion_died", "player": 0, "turn": 30}`
- `{"card": "EDR_492t", "entity": 91, "kind": "minion_died", "player": 0, "turn": 30}`
- `{"card": "EDR_492t", "entity": 92, "kind": "minion_died", "player": 0, "turn": 30}`

- P1: HP=28 Armor=0 Mana=0/10 Deck=12; Weapon=none; Board=empty; Locations=CORE_REV_990#2 durability=2 cooldown=0, CATA_584#21 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Carrier Whelp(1), Torch(1), Royal Librarian(4), Cannonmaster(1), Prescient Slitherdrake(4), Barricade Basher(3)
- P2: HP=12 Armor=5 Mana=2/10 Deck=12; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 5/8, The Great Dracorex#70 5/12; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2)

## Step 115 — turn 31

`P2 END_TURN`

Legal choices before action: 8

Events:

- `{"kind": "turn_end", "player": 1, "turn": 30}`
- `{"card": "EDR_492", "kind": "draw", "player": 0, "turn": 31}`
- `{"kind": "turn_start", "player": 0, "turn": 31}`

- P1: HP=28 Armor=0 Mana=10/10 Deck=11; Weapon=none; Board=empty; Locations=CORE_REV_990#2 durability=2 cooldown=0, CATA_584#21 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Carrier Whelp(1), Torch(1), Royal Librarian(4), Cannonmaster(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4)
- P2: HP=12 Armor=5 Mana=2/10 Deck=12; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 5/8, The Great Dracorex#70 5/12; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2)

## Step 116 — turn 31

`P1 PLAY Carrier Whelp[CATA_556] -> -`

Legal choices before action: 15

Events:

- `{"card": "CATA_556", "controller": 0, "kind": "play", "player": 0, "turn": 31}`
- `{"card": "CATA_556", "entity": 93, "kind": "generated_to_hand", "player": 0, "source": "CATA_556", "turn": 31}`

- P1: HP=28 Armor=0 Mana=9/10 Deck=11; Weapon=none; Board=Carrier Whelp#80 1/2; Locations=CORE_REV_990#2 durability=2 cooldown=0, CATA_584#21 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Torch(1), Royal Librarian(4), Cannonmaster(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1)
- P2: HP=12 Armor=5 Mana=2/10 Deck=12; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 5/8, The Great Dracorex#70 5/12; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2)

## Step 117 — turn 31

`P1 HERO_POWER Armor Up`

Legal choices before action: 17

Events:

- `{"amount": 2, "kind": "gain_armor", "player": 0, "turn": 31}`
- `{"kind": "hero_power", "player": 0, "turn": 31}`

- P1: HP=28 Armor=2 Mana=7/10 Deck=11; Weapon=none; Board=Carrier Whelp#80 1/2; Locations=CORE_REV_990#2 durability=2 cooldown=0, CATA_584#21 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Torch(1), Royal Librarian(4), Cannonmaster(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1)
- P2: HP=12 Armor=5 Mana=2/10 Deck=12; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 5/8, The Great Dracorex#70 5/12; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2)

## Step 118 — turn 31

`P1 PLAY Royal Librarian[CORE_SW_066] -> P1 Carrier Whelp#80`

Legal choices before action: 16

Events:

- `{"card": "CORE_SW_066", "controller": 0, "kind": "play", "player": 0, "turn": 31}`

- P1: HP=28 Armor=2 Mana=3/10 Deck=11; Weapon=none; Board=Carrier Whelp#80 1/2, Royal Librarian#1 4/4; Locations=CORE_REV_990#2 durability=2 cooldown=0, CATA_584#21 durability=3 cooldown=0; Hand=Hook n' Heave(2), Brood Keeper(2), Torch(1), Cannonmaster(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1)
- P2: HP=12 Armor=5 Mana=2/10 Deck=12; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 5/8, The Great Dracorex#70 5/12; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2)

## Step 119 — turn 31

`P1 PLAY Brood Keeper[EDR_457] -> -`

Legal choices before action: 11

Events:

- `{"card": "EDR_457", "controller": 0, "kind": "play", "player": 0, "turn": 31}`
- `{"attack": 2, "card": "EDR_457t", "durability": 2, "kind": "equip_weapon", "player": 0, "turn": 31}`

- P1: HP=28 Armor=2 Mana=1/10 Deck=11; Weapon=Brood Keeper's Sword 2/2; Board=Carrier Whelp#80 1/2, Royal Librarian#1 4/4, Brood Keeper#5 2/3; Locations=CORE_REV_990#2 durability=2 cooldown=0, CATA_584#21 durability=3 cooldown=0; Hand=Hook n' Heave(2), Torch(1), Cannonmaster(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1)
- P2: HP=12 Armor=5 Mana=2/10 Deck=12; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 5/8, The Great Dracorex#70 5/12; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2)

## Step 120 — turn 31

`P1 PLAY Cannonmaster[CAP_107] -> -`

Legal choices before action: 12

Events:

- `{"card": "CAP_107", "controller": 0, "kind": "play", "player": 0, "turn": 31}`
- `{"card": "CAP_107t", "entity": 94, "kind": "generated_to_hand", "player": 0, "source": "CAP_107", "turn": 31}`

- P1: HP=28 Armor=2 Mana=0/10 Deck=11; Weapon=Brood Keeper's Sword 2/2; Board=Carrier Whelp#80 1/2, Royal Librarian#1 4/4, Brood Keeper#5 2/3, Cannonmaster#29 3/1; Locations=CORE_REV_990#2 durability=2 cooldown=0, CATA_584#21 durability=3 cooldown=0; Hand=Hook n' Heave(2), Torch(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1), Cannoneer(1)
- P2: HP=12 Armor=5 Mana=2/10 Deck=12; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 5/8, The Great Dracorex#70 5/12; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2)

## Step 121 — turn 31

`P1 LOCATION CORE_REV_990#2 -> P1 Cannonmaster#29`

Legal choices before action: 11

Events:

- `{"card": "CAP_107", "entity": 29, "kind": "minion_died", "player": 0, "turn": 31}`

- P1: HP=28 Armor=2 Mana=0/10 Deck=11; Weapon=Brood Keeper's Sword 2/2; Board=Carrier Whelp#80 1/2, Royal Librarian#1 4/4, Brood Keeper#5 2/3; Locations=CORE_REV_990#2 durability=1 cooldown=1, CATA_584#21 durability=3 cooldown=0; Hand=Hook n' Heave(2), Torch(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1), Cannoneer(1)
- P2: HP=12 Armor=5 Mana=2/10 Deck=12; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 5/8, The Great Dracorex#70 5/12; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2)

## Step 122 — turn 31

`P1 HERO_ATTACK -> P2 The Great Dracorex#70`

Legal choices before action: 5

- P1: HP=25 Armor=0 Mana=0/10 Deck=11; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#80 1/2, Royal Librarian#1 4/4, Brood Keeper#5 2/3; Locations=CORE_REV_990#2 durability=1 cooldown=1, CATA_584#21 durability=3 cooldown=0; Hand=Hook n' Heave(2), Torch(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1), Cannoneer(1)
- P2: HP=12 Armor=5 Mana=2/10 Deck=12; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 5/8, The Great Dracorex#70 5/10; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2)

## Step 123 — turn 31

`P1 LOCATION CATA_584#21 -> -`

Legal choices before action: 2

- P1: HP=25 Armor=0 Mana=0/10 Deck=11; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#80 1/2, Royal Librarian#1 4/4, Brood Keeper#5 2/3; Locations=CORE_REV_990#2 durability=1 cooldown=1, CATA_584#21 durability=2 cooldown=1; Hand=Hook n' Heave(2), Torch(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1), Cannoneer(1)
- P2: HP=12 Armor=4 Mana=2/10 Deck=12; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 5/8, The Great Dracorex#70 5/8; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2)

## Step 124 — turn 32

`P1 END_TURN`

Legal choices before action: 1

Events:

- `{"kind": "turn_end", "player": 0, "turn": 31}`
- `{"card": "CATA_556", "kind": "draw", "player": 1, "turn": 32}`
- `{"kind": "turn_start", "player": 1, "turn": 32}`

- P1: HP=25 Armor=0 Mana=0/10 Deck=11; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#80 1/2, Royal Librarian#1 4/4, Brood Keeper#5 2/3; Locations=CORE_REV_990#2 durability=1 cooldown=1, CATA_584#21 durability=2 cooldown=1; Hand=Hook n' Heave(2), Torch(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1), Cannoneer(1)
- P2: HP=12 Armor=4 Mana=10/10 Deck=11; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 5/8, The Great Dracorex#70 5/8; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2), Carrier Whelp(1)

## Step 125 — turn 32

`P2 ATTACK Prescient Slitherdrake#46 -> P1 hero`

Legal choices before action: 25

- P1: HP=20 Armor=0 Mana=0/10 Deck=11; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#80 1/2, Royal Librarian#1 4/4, Brood Keeper#5 2/3; Locations=CORE_REV_990#2 durability=1 cooldown=1, CATA_584#21 durability=2 cooldown=1; Hand=Hook n' Heave(2), Torch(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1), Cannoneer(1)
- P2: HP=12 Armor=4 Mana=10/10 Deck=11; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 5/8, The Great Dracorex#70 5/8; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2), Carrier Whelp(1)

## Step 126 — turn 33

`P2 END_TURN`

Legal choices before action: 21

Events:

- `{"kind": "turn_end", "player": 1, "turn": 32}`
- `{"card": "CATA_556", "kind": "draw", "player": 0, "turn": 33}`
- `{"kind": "turn_start", "player": 0, "turn": 33}`

- P1: HP=20 Armor=0 Mana=10/10 Deck=10; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#80 1/2, Royal Librarian#1 4/4, Brood Keeper#5 2/3; Locations=CORE_REV_990#2 durability=1 cooldown=0, CATA_584#21 durability=2 cooldown=0; Hand=Hook n' Heave(2), Torch(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1), Cannoneer(1), Carrier Whelp(1)
- P2: HP=12 Armor=4 Mana=10/10 Deck=11; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 5/8, The Great Dracorex#70 5/8; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2), Carrier Whelp(1)

## Step 127 — turn 33

`P1 PLAY Carrier Whelp[CATA_556] -> -`

Legal choices before action: 28

Events:

- `{"card": "CATA_556", "controller": 0, "kind": "play", "player": 0, "turn": 33}`
- `{"card": "CATA_556", "entity": 95, "kind": "generated_to_hand", "player": 0, "source": "CATA_556", "turn": 33}`

- P1: HP=20 Armor=0 Mana=9/10 Deck=10; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#80 1/2, Royal Librarian#1 4/4, Brood Keeper#5 2/3, Carrier Whelp#18 1/2; Locations=CORE_REV_990#2 durability=1 cooldown=0, CATA_584#21 durability=2 cooldown=0; Hand=Hook n' Heave(2), Torch(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1), Cannoneer(1), Carrier Whelp(1)
- P2: HP=12 Armor=4 Mana=10/10 Deck=11; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 5/8, The Great Dracorex#70 5/8; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2), Carrier Whelp(1)

## Step 128 — turn 34

`P1 END_TURN`

Legal choices before action: 29

Events:

- `{"kind": "turn_end", "player": 0, "turn": 33}`
- `{"card": "JAIL_384", "kind": "burn", "player": 1, "turn": 34}`
- `{"kind": "turn_start", "player": 1, "turn": 34}`

- P1: HP=20 Armor=0 Mana=9/10 Deck=10; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#80 1/2, Royal Librarian#1 4/4, Brood Keeper#5 2/3, Carrier Whelp#18 1/2; Locations=CORE_REV_990#2 durability=1 cooldown=0, CATA_584#21 durability=2 cooldown=0; Hand=Hook n' Heave(2), Torch(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1), Cannoneer(1), Carrier Whelp(1)
- P2: HP=12 Armor=4 Mana=10/10 Deck=10; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 5/8, The Great Dracorex#70 5/8; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2), Carrier Whelp(1)

## Step 129 — turn 34

`P2 ATTACK The Great Dracorex#70 -> P1 hero`

Legal choices before action: 28

- P1: HP=15 Armor=0 Mana=9/10 Deck=10; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#80 1/2, Royal Librarian#1 4/4, Brood Keeper#5 2/3, Carrier Whelp#18 1/2; Locations=CORE_REV_990#2 durability=1 cooldown=0, CATA_584#21 durability=2 cooldown=0; Hand=Hook n' Heave(2), Torch(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1), Cannoneer(1), Carrier Whelp(1)
- P2: HP=12 Armor=4 Mana=10/10 Deck=10; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 5/8, The Great Dracorex#70 5/8; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Mother Duck(4), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2), Carrier Whelp(1)

## Step 130 — turn 34

`P2 PLAY Mother Duck[EDR_492] -> -`

Legal choices before action: 28

Events:

- `{"card": "EDR_492", "controller": 1, "kind": "play", "player": 1, "turn": 34}`

- P1: HP=15 Armor=0 Mana=9/10 Deck=10; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#80 1/2, Royal Librarian#1 4/4, Brood Keeper#5 2/3, Carrier Whelp#18 1/2; Locations=CORE_REV_990#2 durability=1 cooldown=0, CATA_584#21 durability=2 cooldown=0; Hand=Hook n' Heave(2), Torch(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1), Cannoneer(1), Carrier Whelp(1)
- P2: HP=12 Armor=4 Mana=6/10 Deck=10; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 5/8, The Great Dracorex#70 5/8, Mother Duck#37 2/3, Duckling#96 1/1, Duckling#97 1/1, Duckling#98 1/1; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2), Carrier Whelp(1)

## Step 131 — turn 34

`P2 ATTACK Duckling#96 -> P1 Brood Keeper#5`

Legal choices before action: 31

Events:

- `{"card": "EDR_492t", "entity": 96, "kind": "minion_died", "player": 1, "turn": 34}`

- P1: HP=15 Armor=0 Mana=9/10 Deck=10; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#80 1/2, Royal Librarian#1 4/4, Brood Keeper#5 2/2, Carrier Whelp#18 1/2; Locations=CORE_REV_990#2 durability=1 cooldown=0, CATA_584#21 durability=2 cooldown=0; Hand=Hook n' Heave(2), Torch(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1), Cannoneer(1), Carrier Whelp(1)
- P2: HP=12 Armor=4 Mana=6/10 Deck=10; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 5/8, The Great Dracorex#70 5/8, Mother Duck#37 2/3, Duckling#97 1/1, Duckling#98 1/1; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2), Carrier Whelp(1)

## Step 132 — turn 34

`P2 ATTACK Duckling#98 -> P1 Carrier Whelp#80`

Legal choices before action: 36

Events:

- `{"card": "EDR_492t", "entity": 98, "kind": "minion_died", "player": 1, "turn": 34}`

- P1: HP=15 Armor=0 Mana=9/10 Deck=10; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#80 1/1, Royal Librarian#1 4/4, Brood Keeper#5 2/2, Carrier Whelp#18 1/2; Locations=CORE_REV_990#2 durability=1 cooldown=0, CATA_584#21 durability=2 cooldown=0; Hand=Hook n' Heave(2), Torch(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1), Cannoneer(1), Carrier Whelp(1)
- P2: HP=12 Armor=4 Mana=6/10 Deck=10; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 5/8, The Great Dracorex#70 5/8, Mother Duck#37 2/3, Duckling#97 1/1; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2), Carrier Whelp(1)

## Step 133 — turn 35

`P2 END_TURN`

Legal choices before action: 33

Events:

- `{"kind": "turn_end", "player": 1, "turn": 34}`
- `{"card": "CAP_105", "kind": "draw", "player": 0, "turn": 35}`
- `{"kind": "turn_start", "player": 0, "turn": 35}`

- P1: HP=15 Armor=0 Mana=10/10 Deck=9; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#80 1/1, Royal Librarian#1 4/4, Brood Keeper#5 2/2, Carrier Whelp#18 1/2; Locations=CORE_REV_990#2 durability=1 cooldown=0, CATA_584#21 durability=2 cooldown=0; Hand=Hook n' Heave(2), Torch(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1), Cannoneer(1), Carrier Whelp(1), Hook n' Heave(2)
- P2: HP=12 Armor=4 Mana=6/10 Deck=10; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 5/8, The Great Dracorex#70 5/8, Mother Duck#37 2/3, Duckling#97 1/1; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2), Carrier Whelp(1)

## Step 134 — turn 35

`P1 ATTACK Carrier Whelp#18 -> P2 Prescient Slitherdrake#46`

Legal choices before action: 47

Events:

- `{"card": "CATA_556", "entity": 18, "kind": "minion_died", "player": 0, "turn": 35}`

- P1: HP=15 Armor=0 Mana=10/10 Deck=9; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#80 1/1, Royal Librarian#1 4/4, Brood Keeper#5 2/2; Locations=CORE_REV_990#2 durability=1 cooldown=0, CATA_584#21 durability=2 cooldown=0; Hand=Hook n' Heave(2), Torch(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1), Cannoneer(1), Carrier Whelp(1), Hook n' Heave(2)
- P2: HP=12 Armor=4 Mana=6/10 Deck=10; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 5/7, The Great Dracorex#70 5/8, Mother Duck#37 2/3, Duckling#97 1/1; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2), Carrier Whelp(1)

## Step 135 — turn 35

`P1 HERO_ATTACK -> P2 hero`

Legal choices before action: 41

Events:

- `{"card": "EDR_457t", "kind": "weapon_destroyed", "player": 0, "turn": 35}`

- P1: HP=15 Armor=0 Mana=10/10 Deck=9; Weapon=none; Board=Carrier Whelp#80 1/1, Royal Librarian#1 4/4, Brood Keeper#5 2/2; Locations=CORE_REV_990#2 durability=1 cooldown=0, CATA_584#21 durability=2 cooldown=0; Hand=Hook n' Heave(2), Torch(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1), Cannoneer(1), Carrier Whelp(1), Hook n' Heave(2)
- P2: HP=12 Armor=2 Mana=6/10 Deck=10; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 5/7, The Great Dracorex#70 5/8, Mother Duck#37 2/3, Duckling#97 1/1; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2), Carrier Whelp(1)

## Step 136 — turn 35

`P1 LOCATION CORE_REV_990#2 -> P2 Prescient Slitherdrake#46`

Legal choices before action: 36

- P1: HP=15 Armor=0 Mana=10/10 Deck=9; Weapon=none; Board=Carrier Whelp#80 1/1, Royal Librarian#1 4/4, Brood Keeper#5 2/2; Locations=CATA_584#21 durability=2 cooldown=0; Hand=Hook n' Heave(2), Torch(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1), Cannoneer(1), Carrier Whelp(1), Hook n' Heave(2)
- P2: HP=12 Armor=2 Mana=6/10 Deck=10; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 7/6, The Great Dracorex#70 5/8, Mother Duck#37 2/3, Duckling#97 1/1; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2), Carrier Whelp(1)

## Step 137 — turn 35

`P1 PLAY Cannoneer[CAP_107t] -> -`

Legal choices before action: 29

Events:

- `{"card": "CAP_107t", "controller": 0, "kind": "play", "player": 0, "turn": 35}`

- P1: HP=15 Armor=0 Mana=9/10 Deck=9; Weapon=none; Board=Carrier Whelp#80 1/1, Royal Librarian#1 4/4, Brood Keeper#5 2/2, Cannoneer#94 1/1; Locations=CATA_584#21 durability=2 cooldown=0; Hand=Hook n' Heave(2), Torch(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1), Carrier Whelp(1), Hook n' Heave(2)
- P2: HP=12 Armor=2 Mana=6/10 Deck=10; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 7/6, The Great Dracorex#70 5/8, Mother Duck#37 2/3, Duckling#97 1/1; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2), Carrier Whelp(1)

## Step 138 — turn 35

`P1 ATTACK Brood Keeper#5 -> P2 Mother Duck#37`

Legal choices before action: 28

Events:

- `{"card": "EDR_457", "entity": 5, "kind": "minion_died", "player": 0, "turn": 35}`

- P1: HP=15 Armor=0 Mana=9/10 Deck=9; Weapon=none; Board=Carrier Whelp#80 1/1, Royal Librarian#1 4/4, Cannoneer#94 1/1; Locations=CATA_584#21 durability=2 cooldown=0; Hand=Hook n' Heave(2), Torch(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1), Carrier Whelp(1), Hook n' Heave(2)
- P2: HP=12 Armor=2 Mana=6/10 Deck=10; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 7/6, The Great Dracorex#70 5/8, Mother Duck#37 2/1, Duckling#97 1/1; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2), Carrier Whelp(1)

## Step 139 — turn 35

`P1 ATTACK Royal Librarian#1 -> P2 hero`

Legal choices before action: 23

- P1: HP=15 Armor=0 Mana=9/10 Deck=9; Weapon=none; Board=Carrier Whelp#80 1/1, Royal Librarian#1 4/4, Cannoneer#94 1/1; Locations=CATA_584#21 durability=2 cooldown=0; Hand=Hook n' Heave(2), Torch(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1), Carrier Whelp(1), Hook n' Heave(2)
- P2: HP=10 Armor=0 Mana=6/10 Deck=10; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 7/6, The Great Dracorex#70 5/8, Mother Duck#37 2/1, Duckling#97 1/1; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2), Carrier Whelp(1)

## Step 140 — turn 36

`P1 END_TURN`

Legal choices before action: 18

Events:

- `{"card": "EDR_492", "entity": 37, "kind": "minion_died", "player": 1, "turn": 35}`
- `{"kind": "turn_end", "player": 0, "turn": 35}`
- `{"card": "TIME_034", "kind": "draw", "player": 1, "turn": 36}`
- `{"kind": "turn_start", "player": 1, "turn": 36}`

- P1: HP=15 Armor=0 Mana=9/10 Deck=9; Weapon=none; Board=Carrier Whelp#80 1/1, Royal Librarian#1 4/4, Cannoneer#94 1/1; Locations=CATA_584#21 durability=2 cooldown=0; Hand=Hook n' Heave(2), Torch(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1), Carrier Whelp(1), Hook n' Heave(2)
- P2: HP=10 Armor=0 Mana=10/10 Deck=9; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 7/6, The Great Dracorex#70 5/8, Duckling#97 1/1; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2), Carrier Whelp(1), Stadium Announcer(4)

## Step 141 — turn 36

`P2 HERO_POWER Armor Up`

Legal choices before action: 31

Events:

- `{"amount": 2, "kind": "gain_armor", "player": 1, "turn": 36}`
- `{"kind": "hero_power", "player": 1, "turn": 36}`

- P1: HP=15 Armor=0 Mana=9/10 Deck=9; Weapon=none; Board=Carrier Whelp#80 1/1, Royal Librarian#1 4/4, Cannoneer#94 1/1; Locations=CATA_584#21 durability=2 cooldown=0; Hand=Hook n' Heave(2), Torch(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1), Carrier Whelp(1), Hook n' Heave(2)
- P2: HP=10 Armor=2 Mana=8/10 Deck=9; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 7/6, The Great Dracorex#70 5/8, Duckling#97 1/1; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Carrier Whelp(1), Warptooth(4), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2), Carrier Whelp(1), Stadium Announcer(4)

## Step 142 — turn 36

`P2 PLAY Warptooth[JAIL_421] -> -`

Legal choices before action: 30

Events:

- `{"card": "JAIL_421", "controller": 1, "kind": "play", "player": 1, "turn": 36}`

- P1: HP=15 Armor=0 Mana=9/10 Deck=9; Weapon=none; Board=Carrier Whelp#80 1/1, Royal Librarian#1 4/4, Cannoneer#94 1/1; Locations=CATA_584#21 durability=2 cooldown=0; Hand=Hook n' Heave(2), Torch(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1), Carrier Whelp(1), Hook n' Heave(2)
- P2: HP=10 Armor=2 Mana=4/10 Deck=9; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 7/6, The Great Dracorex#70 5/8, Duckling#97 1/1, Warptooth#63 3/3; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Carrier Whelp(1), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2), Carrier Whelp(1), Stadium Announcer(4)

## Step 143 — turn 36

`P2 ATTACK Warptooth#63 -> P1 Cannoneer#94`

Legal choices before action: 33

Events:

- `{"card": "CAP_107t", "entity": 94, "kind": "minion_died", "player": 0, "turn": 36}`

- P1: HP=15 Armor=0 Mana=9/10 Deck=9; Weapon=none; Board=Carrier Whelp#80 1/1, Royal Librarian#1 4/4; Locations=CATA_584#21 durability=2 cooldown=0; Hand=Hook n' Heave(2), Torch(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1), Carrier Whelp(1), Hook n' Heave(2)
- P2: HP=10 Armor=2 Mana=4/10 Deck=9; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 7/6, The Great Dracorex#70 5/8, Duckling#97 1/1, Warptooth#63 3/2; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Carrier Whelp(1), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2), Carrier Whelp(1), Stadium Announcer(4)

## Step 144 — turn 36

`P2 PLAY Carrier Whelp[CATA_556] -> -`

Legal choices before action: 26

Events:

- `{"card": "CATA_556", "controller": 1, "kind": "play", "player": 1, "turn": 36}`
- `{"card": "CATA_556", "entity": 99, "kind": "generated_to_hand", "player": 1, "source": "CATA_556", "turn": 36}`

- P1: HP=15 Armor=0 Mana=9/10 Deck=9; Weapon=none; Board=Carrier Whelp#80 1/1, Royal Librarian#1 4/4; Locations=CATA_584#21 durability=2 cooldown=0; Hand=Hook n' Heave(2), Torch(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1), Carrier Whelp(1), Hook n' Heave(2)
- P2: HP=10 Armor=2 Mana=3/10 Deck=9; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 7/6, The Great Dracorex#70 5/8, Duckling#97 1/1, Warptooth#63 3/2, Carrier Whelp#48 1/2; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Carrier Whelp(1), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2), Stadium Announcer(4), Carrier Whelp(1)

## Step 145 — turn 36

`P2 ATTACK The Great Dracorex#70 -> P1 Royal Librarian#1`

Legal choices before action: 24

Events:

- `{"card": "CATA_556", "entity": 80, "kind": "minion_died", "player": 0, "turn": 36}`
- `{"card": "CORE_SW_066", "entity": 1, "kind": "minion_died", "player": 0, "turn": 36}`

- P1: HP=15 Armor=0 Mana=9/10 Deck=9; Weapon=none; Board=empty; Locations=CATA_584#21 durability=2 cooldown=0; Hand=Hook n' Heave(2), Torch(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1), Carrier Whelp(1), Hook n' Heave(2)
- P2: HP=10 Armor=2 Mana=3/10 Deck=9; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 7/6, The Great Dracorex#70 5/4, Duckling#97 1/1, Warptooth#63 3/2, Carrier Whelp#48 1/2; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Carrier Whelp(1), Cannonmaster(1), Warptooth(4), Cannoneer(1), Torch(1), Brood Keeper(2), Stadium Announcer(4), Carrier Whelp(1)

## Step 146 — turn 36

`P2 PLAY Torch[CATA_585] -> P2 The Great Dracorex#70`

Legal choices before action: 15

Events:

- `{"card": "CATA_585", "controller": 1, "kind": "play", "player": 1, "turn": 36}`
- `{"card": "DINO_401", "entity": 70, "kind": "minion_died", "player": 1, "turn": 36}`

- P1: HP=15 Armor=0 Mana=9/10 Deck=9; Weapon=none; Board=empty; Locations=CATA_584#21 durability=2 cooldown=0; Hand=Hook n' Heave(2), Torch(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1), Carrier Whelp(1), Hook n' Heave(2)
- P2: HP=10 Armor=2 Mana=2/10 Deck=9; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 7/6, Duckling#97 1/1, Warptooth#63 3/2, Carrier Whelp#48 1/2; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Carrier Whelp(1), Cannonmaster(1), Warptooth(4), Cannoneer(1), Brood Keeper(2), Stadium Announcer(4), Carrier Whelp(1), Torch(1)

## Step 147 — turn 36

`P2 PLAY Cannonmaster[CAP_107] -> -`

Legal choices before action: 13

Events:

- `{"card": "CAP_107", "controller": 1, "kind": "play", "player": 1, "turn": 36}`
- `{"card": "CAP_107t", "entity": 100, "kind": "generated_to_hand", "player": 1, "source": "CAP_107", "turn": 36}`

- P1: HP=15 Armor=0 Mana=9/10 Deck=9; Weapon=none; Board=empty; Locations=CATA_584#21 durability=2 cooldown=0; Hand=Hook n' Heave(2), Torch(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1), Carrier Whelp(1), Hook n' Heave(2)
- P2: HP=10 Armor=2 Mana=1/10 Deck=9; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 7/6, Duckling#97 1/1, Warptooth#63 3/2, Carrier Whelp#48 1/2, Cannonmaster#77 3/1; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Carrier Whelp(1), Warptooth(4), Cannoneer(1), Brood Keeper(2), Stadium Announcer(4), Carrier Whelp(1), Torch(1), Cannoneer(1)

## Step 148 — turn 36

`P2 PLAY Cannoneer[CAP_107t] -> -`

Legal choices before action: 12

Events:

- `{"card": "CAP_107t", "controller": 1, "kind": "play", "player": 1, "turn": 36}`

- P1: HP=15 Armor=0 Mana=9/10 Deck=9; Weapon=none; Board=empty; Locations=CATA_584#21 durability=2 cooldown=0; Hand=Hook n' Heave(2), Torch(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1), Carrier Whelp(1), Hook n' Heave(2)
- P2: HP=10 Armor=2 Mana=0/10 Deck=9; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 7/6, Duckling#97 1/1, Warptooth#63 3/2, Carrier Whelp#48 1/2, Cannonmaster#77 3/1, Cannoneer#100 1/1; Locations=CATA_584#51 durability=2 cooldown=0; Hand=Sanguine Depths(1), Carrier Whelp(1), Warptooth(4), Cannoneer(1), Brood Keeper(2), Stadium Announcer(4), Carrier Whelp(1), Torch(1)

## Step 149 — turn 36

`P2 LOCATION CATA_584#51 -> -`

Legal choices before action: 5

- P1: HP=9 Armor=0 Mana=9/10 Deck=9; Weapon=none; Board=empty; Locations=CATA_584#21 durability=2 cooldown=0; Hand=Hook n' Heave(2), Torch(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1), Carrier Whelp(1), Hook n' Heave(2)
- P2: HP=10 Armor=2 Mana=0/10 Deck=9; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 7/6, Duckling#97 1/1, Warptooth#63 3/2, Carrier Whelp#48 1/2, Cannonmaster#77 3/1, Cannoneer#100 1/1; Locations=CATA_584#51 durability=1 cooldown=1; Hand=Sanguine Depths(1), Carrier Whelp(1), Warptooth(4), Cannoneer(1), Brood Keeper(2), Stadium Announcer(4), Carrier Whelp(1), Torch(1)

## Step 150 — turn 36

`P2 ATTACK Prescient Slitherdrake#46 -> P1 hero`

Legal choices before action: 4

- P1: HP=2 Armor=0 Mana=9/10 Deck=9; Weapon=none; Board=empty; Locations=CATA_584#21 durability=2 cooldown=0; Hand=Hook n' Heave(2), Torch(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1), Carrier Whelp(1), Hook n' Heave(2)
- P2: HP=10 Armor=2 Mana=0/10 Deck=9; Weapon=Brood Keeper's Sword 2/1; Board=Prescient Slitherdrake#46 7/6, Duckling#97 1/1, Warptooth#63 3/2, Carrier Whelp#48 1/2, Cannonmaster#77 3/1, Cannoneer#100 1/1; Locations=CATA_584#51 durability=1 cooldown=1; Hand=Sanguine Depths(1), Carrier Whelp(1), Warptooth(4), Cannoneer(1), Brood Keeper(2), Stadium Announcer(4), Carrier Whelp(1), Torch(1)

## Step 151 — turn 36

`P2 HERO_ATTACK -> P1 hero`

Legal choices before action: 3

Events:

- `{"card": "EDR_457t", "kind": "weapon_destroyed", "player": 1, "turn": 36}`

- P1: HP=0 Armor=0 Mana=9/10 Deck=9; Weapon=none; Board=empty; Locations=CATA_584#21 durability=2 cooldown=0; Hand=Hook n' Heave(2), Torch(1), Prescient Slitherdrake(4), Barricade Basher(3), Mother Duck(4), Carrier Whelp(1), Carrier Whelp(1), Hook n' Heave(2)
- P2: HP=10 Armor=2 Mana=0/10 Deck=9; Weapon=none; Board=Prescient Slitherdrake#46 7/6, Duckling#97 1/1, Warptooth#63 3/2, Carrier Whelp#48 1/2, Cannonmaster#77 3/1, Cannoneer#100 1/1; Locations=CATA_584#51 durability=1 cooldown=1; Hand=Sanguine Depths(1), Carrier Whelp(1), Warptooth(4), Cannoneer(1), Brood Keeper(2), Stadium Announcer(4), Carrier Whelp(1), Torch(1)

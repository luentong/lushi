# Policy-prior PUCT vs ISMCTS detailed trace

- Seed: `202609100039`
- Candidate: `P1`
- Winner: `P1`
- Candidate win: `True`
- Actions: `38`
- Illegal actions: `0`

## Turn 2

### Step 1: policy-prior-puct-v1

**P1 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P1 END_TURN

Resolved events:

- `{"kind": "turn_end", "player": 0, "turn": 1}`
- `{"card": "END_033", "kind": "draw", "player": 1, "turn": 2}`
- `{"kind": "turn_start", "player": 1, "turn": 2}`

- P1: HP=30 Armor=0 Mana=1/1 Deck=27; Weapon=none; Board=empty; Hand=Searing Fissure(2), Torch(1), Windpeak Wyrm(8), Searing Fissure(2)
- P2: HP=30 Armor=0 Mana=1/1 Deck=26; Weapon=none; Board=empty; Hand=Darkrider(1), Darkrider(1), Shadowflame Suffusion(2), Warptooth(4), The Coin(0), Prescient Slitherdrake(7)

### Step 2: shared-tree-ismcts-v1

**P2 PLAY Darkrider[EDR_456] -> -**

Legal actions: 4; Searched nodes: 5; Selected value: 0.2420

Top choices by root visit share:

- `0.250` — P2 END_TURN
- `0.250` — P2 PLAY Darkrider[EDR_456] -> -
- `0.250` — P2 PLAY Darkrider[EDR_456] -> -
- `0.250` — P2 PLAY The Coin[GAME_005] -> -

Resolved events:

- `{"card": "EDR_456", "controller": 1, "created_by": null, "entity": 34, "kind": "play", "player": 1, "started_in_deck": true, "turn": 2}`
- `{"kind": "discover_offer", "options": [{"card": "FIR_956", "entity": 64, "gifts": ["rude_awakening"]}, {"card": "TIME_871", "entity": 65, "gifts": ["persisting_horror"]}, {"card": "TIME_714", "entity": 66, "gifts": ["well_rested"]}], "player": 1, "profile": "closed_pool", "turn": 2}`

- P1: HP=30 Armor=0 Mana=1/1 Deck=27; Weapon=none; Board=empty; Hand=Searing Fissure(2), Torch(1), Windpeak Wyrm(8), Searing Fissure(2)
- P2: HP=30 Armor=0 Mana=0/1 Deck=26; Weapon=none; Board=Darkrider#34 1/1; Hand=Darkrider(1), Shadowflame Suffusion(2), Warptooth(4), The Coin(0), Prescient Slitherdrake(7)

### Step 3: shared-tree-ismcts-v1

**P2 DISCOVER_PICK Heir of Hereafter[TIME_871] + persisting_horror**

Legal actions: 3; Searched nodes: 5; Selected value: 0.2513

Top choices by root visit share:

- `0.500` — P2 DISCOVER_PICK Heir of Hereafter[TIME_871] + persisting_horror
- `0.250` — P2 DISCOVER_PICK Dragon Turtle[FIR_956] + rude_awakening
- `0.250` — P2 DISCOVER_PICK Chrono-Lord Epoch[TIME_714] + well_rested

Resolved events:

- `{"card": "TIME_871", "destination": "hand", "entity": 65, "gifts": ["persisting_horror"], "kind": "discover_pick", "player": 1, "source": "EDR_456", "turn": 2}`

- P1: HP=30 Armor=0 Mana=1/1 Deck=27; Weapon=none; Board=empty; Hand=Searing Fissure(2), Torch(1), Windpeak Wyrm(8), Searing Fissure(2)
- P2: HP=30 Armor=0 Mana=0/1 Deck=26; Weapon=none; Board=Darkrider#34 1/1; Hand=Darkrider(1), Shadowflame Suffusion(2), Warptooth(4), The Coin(0), Prescient Slitherdrake(4), Heir of Hereafter(5)

### Step 4: shared-tree-ismcts-v1

**P2 PLAY The Coin[GAME_005] -> -**

Legal actions: 2; Searched nodes: 5; Selected value: 0.0529

Top choices by root visit share:

- `0.750` — P2 PLAY The Coin[GAME_005] -> -
- `0.250` — P2 END_TURN

Resolved events:

- `{"card": "GAME_005", "controller": 1, "created_by": "MULLIGAN", "entity": 61, "kind": "play", "player": 1, "started_in_deck": false, "turn": 2}`

- P1: HP=30 Armor=0 Mana=1/1 Deck=27; Weapon=none; Board=empty; Hand=Searing Fissure(2), Torch(1), Windpeak Wyrm(8), Searing Fissure(2)
- P2: HP=30 Armor=0 Mana=1/1 Deck=26; Weapon=none; Board=Darkrider#34 1/1; Hand=Darkrider(1), Shadowflame Suffusion(2), Warptooth(4), Prescient Slitherdrake(4), Heir of Hereafter(5)

### Step 5: shared-tree-ismcts-v1

**P2 PLAY Darkrider[EDR_456] -> -**

Legal actions: 2; Searched nodes: 5; Selected value: 0.0903

Top choices by root visit share:

- `0.750` — P2 PLAY Darkrider[EDR_456] -> -
- `0.250` — P2 END_TURN

Resolved events:

- `{"card": "EDR_456", "controller": 1, "created_by": null, "entity": 33, "kind": "play", "player": 1, "started_in_deck": true, "turn": 2}`
- `{"kind": "discover_offer", "options": [{"card": "TIME_045", "entity": 67, "gifts": ["sleepwalker"]}, {"card": "TIME_004", "entity": 68, "gifts": ["waking_terror"]}, {"card": "DINO_401", "entity": 69, "gifts": ["well_rested"]}], "player": 1, "profile": "closed_pool", "turn": 2}`

- P1: HP=30 Armor=0 Mana=1/1 Deck=27; Weapon=none; Board=empty; Hand=Searing Fissure(2), Torch(1), Windpeak Wyrm(8), Searing Fissure(2)
- P2: HP=30 Armor=0 Mana=0/1 Deck=26; Weapon=none; Board=Darkrider#34 1/1, Darkrider#33 1/1; Hand=Shadowflame Suffusion(2), Warptooth(4), Prescient Slitherdrake(4), Heir of Hereafter(5)

### Step 6: shared-tree-ismcts-v1

**P2 DISCOVER_PICK Whelp of the Infinite[TIME_045] + sleepwalker**

Legal actions: 3; Searched nodes: 5; Selected value: -0.1405

Top choices by root visit share:

- `0.500` — P2 DISCOVER_PICK Whelp of the Infinite[TIME_045] + sleepwalker
- `0.250` — P2 DISCOVER_PICK Conflux Crasher[TIME_004] + waking_terror
- `0.250` — P2 DISCOVER_PICK The Great Dracorex[DINO_401] + well_rested

Resolved events:

- `{"card": "TIME_045", "destination": "hand", "entity": 67, "gifts": ["sleepwalker"], "kind": "discover_pick", "player": 1, "source": "EDR_456", "turn": 2}`

- P1: HP=30 Armor=0 Mana=1/1 Deck=27; Weapon=none; Board=empty; Hand=Searing Fissure(2), Torch(1), Windpeak Wyrm(8), Searing Fissure(2)
- P2: HP=30 Armor=0 Mana=0/1 Deck=26; Weapon=none; Board=Darkrider#34 1/1, Darkrider#33 1/1; Hand=Shadowflame Suffusion(2), Warptooth(4), Prescient Slitherdrake(4), Heir of Hereafter(5), Whelp of the Infinite(3)

## Turn 3

### Step 7: shared-tree-ismcts-v1

**P2 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P2 END_TURN

Resolved events:

- `{"kind": "turn_end", "player": 1, "turn": 2}`
- `{"card": "JAIL_421", "kind": "draw", "player": 0, "turn": 3}`
- `{"kind": "turn_start", "player": 0, "turn": 3}`

- P1: HP=30 Armor=0 Mana=2/2 Deck=26; Weapon=none; Board=empty; Hand=Searing Fissure(2), Torch(1), Windpeak Wyrm(8), Searing Fissure(2), Warptooth(4)
- P2: HP=30 Armor=0 Mana=0/1 Deck=26; Weapon=none; Board=Darkrider#34 1/1, Darkrider#33 1/1; Hand=Shadowflame Suffusion(2), Warptooth(4), Prescient Slitherdrake(4), Heir of Hereafter(5), Whelp of the Infinite(3)

### Step 8: policy-prior-puct-v1

**P1 PLAY Searing Fissure[CATA_582] -> -**

Legal actions: 4; Searched nodes: 5; Selected value: 0.0371

Top choices by root visit share:

- `0.250` — P1 END_TURN
- `0.250` — P1 HERO_POWER Armor Up
- `0.250` — P1 PLAY Searing Fissure[CATA_582] -> -
- `0.250` — P1 PLAY Searing Fissure[CATA_582] -> -

Resolved events:

- `{"card": "CATA_582", "controller": 0, "created_by": null, "entity": 20, "kind": "play", "player": 0, "started_in_deck": true, "turn": 3}`
- `{"card": "EDR_456", "entity": 34, "kind": "minion_died", "player": 1, "turn": 3}`
- `{"card": "EDR_456", "entity": 33, "kind": "minion_died", "player": 1, "turn": 3}`

- P1: HP=30 Armor=0 Mana=0/2 Deck=26; Weapon=none; Board=empty; Hand=Searing Fissure(2), Torch(1), Windpeak Wyrm(8), Warptooth(4)
- P2: HP=30 Armor=0 Mana=0/1 Deck=26; Weapon=none; Board=empty; Hand=Shadowflame Suffusion(2), Warptooth(4), Prescient Slitherdrake(4), Heir of Hereafter(5), Whelp of the Infinite(3)

### Step 9: policy-prior-puct-v1

**P1 HERO_ATTACK -> P2 hero**

Legal actions: 2; Searched nodes: 5; Selected value: 0.0271

Top choices by root visit share:

- `0.500` — P1 END_TURN
- `0.500` — P1 HERO_ATTACK -> P2 hero

- P1: HP=30 Armor=0 Mana=0/2 Deck=26; Weapon=none; Board=empty; Hand=Searing Fissure(2), Torch(1), Windpeak Wyrm(8), Warptooth(4)
- P2: HP=27 Armor=0 Mana=0/1 Deck=26; Weapon=none; Board=empty; Hand=Shadowflame Suffusion(2), Warptooth(4), Prescient Slitherdrake(4), Heir of Hereafter(5), Whelp of the Infinite(3)

## Turn 4

### Step 10: policy-prior-puct-v1

**P1 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P1 END_TURN

Resolved events:

- `{"kind": "turn_end", "player": 0, "turn": 3}`
- `{"card": "CATA_582", "kind": "draw", "player": 1, "turn": 4}`
- `{"kind": "turn_start", "player": 1, "turn": 4}`

- P1: HP=30 Armor=0 Mana=0/2 Deck=26; Weapon=none; Board=empty; Hand=Searing Fissure(2), Torch(1), Windpeak Wyrm(8), Warptooth(4)
- P2: HP=27 Armor=0 Mana=2/2 Deck=25; Weapon=none; Board=empty; Hand=Shadowflame Suffusion(2), Warptooth(4), Prescient Slitherdrake(4), Heir of Hereafter(5), Whelp of the Infinite(3), Searing Fissure(2)

### Step 11: shared-tree-ismcts-v1

**P2 HERO_POWER Armor Up**

Legal actions: 5; Searched nodes: 5; Selected value: -0.1503

Top choices by root visit share:

- `0.250` — P2 HERO_POWER Armor Up
- `0.250` — P2 PLAY Shadowflame Suffusion[FIR_939] -> P1 hero
- `0.250` — P2 PLAY Shadowflame Suffusion[FIR_939] -> P2 hero
- `0.250` — P2 PLAY Searing Fissure[CATA_582] -> -
- `0.000` — P2 END_TURN

Resolved events:

- `{"amount": 2, "kind": "gain_armor", "player": 1, "turn": 4}`
- `{"kind": "hero_power", "player": 1, "turn": 4}`

- P1: HP=30 Armor=0 Mana=0/2 Deck=26; Weapon=none; Board=empty; Hand=Searing Fissure(2), Torch(1), Windpeak Wyrm(8), Warptooth(4)
- P2: HP=27 Armor=2 Mana=0/2 Deck=25; Weapon=none; Board=empty; Hand=Shadowflame Suffusion(2), Warptooth(4), Prescient Slitherdrake(4), Heir of Hereafter(5), Whelp of the Infinite(3), Searing Fissure(2)

## Turn 5

### Step 12: shared-tree-ismcts-v1

**P2 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P2 END_TURN

Resolved events:

- `{"kind": "turn_end", "player": 1, "turn": 4}`
- `{"card": "END_033", "kind": "draw", "player": 0, "turn": 5}`
- `{"kind": "turn_start", "player": 0, "turn": 5}`

- P1: HP=30 Armor=0 Mana=3/3 Deck=25; Weapon=none; Board=empty; Hand=Searing Fissure(2), Torch(1), Windpeak Wyrm(8), Warptooth(4), Prescient Slitherdrake(4)
- P2: HP=27 Armor=2 Mana=0/2 Deck=25; Weapon=none; Board=empty; Hand=Shadowflame Suffusion(2), Warptooth(4), Prescient Slitherdrake(4), Heir of Hereafter(5), Whelp of the Infinite(3), Searing Fissure(2)

### Step 13: policy-prior-puct-v1

**P1 PLAY Searing Fissure[CATA_582] -> -**

Legal actions: 3; Searched nodes: 5; Selected value: -0.2827

Top choices by root visit share:

- `0.500` — P1 PLAY Searing Fissure[CATA_582] -> -
- `0.250` — P1 END_TURN
- `0.250` — P1 HERO_POWER Armor Up

Resolved events:

- `{"card": "CATA_582", "controller": 0, "created_by": null, "entity": 19, "kind": "play", "player": 0, "started_in_deck": true, "turn": 5}`

- P1: HP=30 Armor=0 Mana=1/3 Deck=25; Weapon=none; Board=empty; Hand=Torch(1), Windpeak Wyrm(8), Warptooth(4), Prescient Slitherdrake(4)
- P2: HP=27 Armor=2 Mana=0/2 Deck=25; Weapon=none; Board=empty; Hand=Shadowflame Suffusion(2), Warptooth(4), Prescient Slitherdrake(4), Heir of Hereafter(5), Whelp of the Infinite(3), Searing Fissure(2)

### Step 14: policy-prior-puct-v1

**P1 HERO_ATTACK -> P2 hero**

Legal actions: 2; Searched nodes: 5; Selected value: -0.1861

Top choices by root visit share:

- `0.500` — P1 END_TURN
- `0.500` — P1 HERO_ATTACK -> P2 hero

- P1: HP=30 Armor=0 Mana=1/3 Deck=25; Weapon=none; Board=empty; Hand=Torch(1), Windpeak Wyrm(8), Warptooth(4), Prescient Slitherdrake(4)
- P2: HP=26 Armor=0 Mana=0/2 Deck=25; Weapon=none; Board=empty; Hand=Shadowflame Suffusion(2), Warptooth(4), Prescient Slitherdrake(4), Heir of Hereafter(5), Whelp of the Infinite(3), Searing Fissure(2)

## Turn 6

### Step 15: policy-prior-puct-v1

**P1 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P1 END_TURN

Resolved events:

- `{"kind": "turn_end", "player": 0, "turn": 5}`
- `{"card": "CATA_582", "kind": "draw", "player": 1, "turn": 6}`
- `{"kind": "turn_start", "player": 1, "turn": 6}`

- P1: HP=30 Armor=0 Mana=1/3 Deck=25; Weapon=none; Board=empty; Hand=Torch(1), Windpeak Wyrm(8), Warptooth(4), Prescient Slitherdrake(4)
- P2: HP=26 Armor=0 Mana=3/3 Deck=24; Weapon=none; Board=empty; Hand=Shadowflame Suffusion(2), Warptooth(4), Prescient Slitherdrake(4), Heir of Hereafter(5), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2)

### Step 16: shared-tree-ismcts-v1

**P2 PLAY Shadowflame Suffusion[FIR_939] -> P1 hero**

Legal actions: 7; Searched nodes: 5; Selected value: -0.1670

Top choices by root visit share:

- `0.250` — P2 PLAY Shadowflame Suffusion[FIR_939] -> P1 hero
- `0.250` — P2 PLAY Searing Fissure[CATA_582] -> -
- `0.250` — P2 PLAY Searing Fissure[CATA_582] -> -
- `0.250` — P2 PLAY Whelp of the Infinite[TIME_045] -> -
- `0.000` — P2 END_TURN

Resolved events:

- `{"card": "FIR_939", "controller": 1, "created_by": null, "entity": 39, "kind": "play", "player": 1, "started_in_deck": true, "turn": 6}`
- `{"kind": "discover_offer", "options": [{"card": "CATA_591", "entity": 70, "gifts": ["rude_awakening"]}, {"card": "JAIL_421", "entity": 71, "gifts": ["bundled_up"]}, {"card": "TIME_714", "entity": 72, "gifts": ["sleepwalker"]}], "player": 1, "profile": "closed_pool", "turn": 6}`

- P1: HP=28 Armor=0 Mana=1/3 Deck=25; Weapon=none; Board=empty; Hand=Torch(1), Windpeak Wyrm(8), Warptooth(4), Prescient Slitherdrake(4)
- P2: HP=26 Armor=0 Mana=1/3 Deck=24; Weapon=none; Board=empty; Hand=Warptooth(4), Prescient Slitherdrake(4), Heir of Hereafter(5), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2)

### Step 17: shared-tree-ismcts-v1

**P2 DISCOVER_PICK Chrono-Lord Epoch[TIME_714] + sleepwalker**

Legal actions: 3; Searched nodes: 5; Selected value: -0.3557

Top choices by root visit share:

- `0.500` — P2 DISCOVER_PICK Chrono-Lord Epoch[TIME_714] + sleepwalker
- `0.250` — P2 DISCOVER_PICK Commander Geddon[CATA_591] + rude_awakening
- `0.250` — P2 DISCOVER_PICK Warptooth[JAIL_421] + bundled_up

Resolved events:

- `{"card": "TIME_714", "destination": "hand", "entity": 72, "gifts": ["sleepwalker"], "kind": "discover_pick", "player": 1, "source": "FIR_939", "turn": 6}`

- P1: HP=28 Armor=0 Mana=1/3 Deck=25; Weapon=none; Board=empty; Hand=Torch(1), Windpeak Wyrm(8), Warptooth(4), Prescient Slitherdrake(4)
- P2: HP=26 Armor=0 Mana=1/3 Deck=24; Weapon=none; Board=empty; Hand=Warptooth(4), Prescient Slitherdrake(4), Heir of Hereafter(5), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6)

## Turn 7

### Step 18: shared-tree-ismcts-v1

**P2 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P2 END_TURN

Resolved events:

- `{"kind": "turn_end", "player": 1, "turn": 6}`
- `{"card": "TIME_034", "kind": "draw", "player": 0, "turn": 7}`
- `{"kind": "turn_start", "player": 0, "turn": 7}`

- P1: HP=28 Armor=0 Mana=4/4 Deck=24; Weapon=none; Board=empty; Hand=Torch(1), Windpeak Wyrm(8), Warptooth(4), Prescient Slitherdrake(4), Stadium Announcer(4)
- P2: HP=26 Armor=0 Mana=1/3 Deck=24; Weapon=none; Board=empty; Hand=Warptooth(4), Prescient Slitherdrake(4), Heir of Hereafter(5), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6)

### Step 19: policy-prior-puct-v1

**P1 PLAY Stadium Announcer[TIME_034] -> -**

Legal actions: 5; Searched nodes: 5; Selected value: 0.7815

Top choices by root visit share:

- `0.250` — P1 HERO_POWER Armor Up
- `0.250` — P1 PLAY Stadium Announcer[TIME_034] -> -
- `0.250` — P1 PLAY Prescient Slitherdrake[END_033] -> -
- `0.250` — P1 PLAY Warptooth[JAIL_421] -> -
- `0.000` — P1 END_TURN

Resolved events:

- `{"card": "TIME_034", "controller": 0, "created_by": null, "entity": 13, "kind": "play", "player": 0, "started_in_deck": true, "turn": 7}`
- `{"attack": 3, "card": "EDR_416", "durability": 2, "kind": "equip_weapon", "player": 0, "turn": 7}`
- `{"attack": 2, "card": "EDR_842", "durability": 3, "kind": "equip_weapon", "player": 1, "turn": 7}`
- `{"effect": "stadium_weapons", "kind": "rewind_offer", "outcome": [{"attack": 4, "card": "EDR_416", "durability": 3, "name": "Shepherd's Crook"}, {"attack": 2, "card": "EDR_842", "durability": 3, "name": "Defiled Spear"}], "player": 0, "restorable": true, "turn": 7}`

- P1: HP=28 Armor=0 Mana=0/4 Deck=24; Weapon=Shepherd's Crook 4/3; Board=Stadium Announcer#13 3/3; Hand=Torch(1), Windpeak Wyrm(8), Warptooth(4), Prescient Slitherdrake(4)
- P2: HP=26 Armor=0 Mana=1/3 Deck=24; Weapon=Defiled Spear 2/3; Board=empty; Hand=Warptooth(4), Prescient Slitherdrake(4), Heir of Hereafter(5), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6)

### Step 20: policy-prior-puct-v1

**P1 REWIND_KEEP**

Legal actions: 2; Searched nodes: 5; Selected value: 0.6692

Top choices by root visit share:

- `0.500` — P1 REWIND_KEEP
- `0.500` — P1 REWIND_RETRY

Resolved events:

- `{"decision": "keep", "effect": "stadium_weapons", "kind": "rewind_pick", "outcome": [{"attack": 4, "card": "EDR_416", "durability": 3, "name": "Shepherd's Crook"}, {"attack": 2, "card": "EDR_842", "durability": 3, "name": "Defiled Spear"}], "player": 0, "turn": 7}`

- P1: HP=28 Armor=0 Mana=0/4 Deck=24; Weapon=Shepherd's Crook 4/3; Board=Stadium Announcer#13 3/3; Hand=Torch(1), Windpeak Wyrm(8), Warptooth(4), Prescient Slitherdrake(4)
- P2: HP=26 Armor=0 Mana=1/3 Deck=24; Weapon=Defiled Spear 2/3; Board=empty; Hand=Warptooth(4), Prescient Slitherdrake(4), Heir of Hereafter(5), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6)

### Step 21: policy-prior-puct-v1

**P1 HERO_ATTACK -> P2 hero**

Legal actions: 2; Searched nodes: 5; Selected value: 0.5831

Top choices by root visit share:

- `0.750` — P1 HERO_ATTACK -> P2 hero
- `0.250` — P1 END_TURN

- P1: HP=28 Armor=0 Mana=0/4 Deck=24; Weapon=Shepherd's Crook 4/2; Board=Stadium Announcer#13 3/3, Sleepy Sheep#73 3/3; Hand=Torch(1), Windpeak Wyrm(8), Warptooth(4), Prescient Slitherdrake(4)
- P2: HP=22 Armor=0 Mana=1/3 Deck=24; Weapon=Defiled Spear 2/3; Board=empty; Hand=Warptooth(4), Prescient Slitherdrake(4), Heir of Hereafter(5), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6)

## Turn 8

### Step 22: policy-prior-puct-v1

**P1 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P1 END_TURN

Resolved events:

- `{"kind": "turn_end", "player": 0, "turn": 7}`
- `{"card": "CATA_584", "kind": "draw", "player": 1, "turn": 8}`
- `{"kind": "turn_start", "player": 1, "turn": 8}`

- P1: HP=28 Armor=0 Mana=0/4 Deck=24; Weapon=Shepherd's Crook 4/2; Board=Stadium Announcer#13 3/3, Sleepy Sheep#73 3/3; Hand=Torch(1), Windpeak Wyrm(5), Warptooth(4), Prescient Slitherdrake(4)
- P2: HP=22 Armor=0 Mana=4/4 Deck=23; Weapon=Defiled Spear 2/3; Board=empty; Hand=Warptooth(4), Prescient Slitherdrake(4), Heir of Hereafter(5), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6), Erupting Volcano(3)

### Step 23: shared-tree-ismcts-v1

**P2 HERO_ATTACK -> P1 hero**

Legal actions: 10; Searched nodes: 5; Selected value: -0.2538

Top choices by root visit share:

- `0.250` — P2 HERO_ATTACK -> P1 hero
- `0.250` — P2 HERO_ATTACK -> P1 Stadium Announcer#13
- `0.250` — P2 PLAY Prescient Slitherdrake[END_033] -> -
- `0.250` — P2 PLAY Warptooth[JAIL_421] -> -
- `0.000` — P2 END_TURN

- P1: HP=26 Armor=0 Mana=0/4 Deck=24; Weapon=Shepherd's Crook 4/2; Board=Stadium Announcer#13 3/1, Sleepy Sheep#73 3/3; Hand=Torch(1), Windpeak Wyrm(5), Warptooth(4), Prescient Slitherdrake(4)
- P2: HP=22 Armor=0 Mana=4/4 Deck=23; Weapon=Defiled Spear 2/2; Board=empty; Hand=Warptooth(4), Prescient Slitherdrake(4), Heir of Hereafter(5), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6), Erupting Volcano(3)

### Step 24: shared-tree-ismcts-v1

**P2 PLAY Prescient Slitherdrake[END_033] -> -**

Legal actions: 8; Searched nodes: 5; Selected value: -0.0263

Top choices by root visit share:

- `0.250` — P2 PLAY Prescient Slitherdrake[END_033] -> -
- `0.250` — P2 PLAY Erupting Volcano[CATA_584] -> -
- `0.250` — P2 PLAY Warptooth[JAIL_421] -> -
- `0.250` — P2 PLAY Whelp of the Infinite[TIME_045] -> -
- `0.000` — P2 END_TURN

Resolved events:

- `{"card": "END_033", "controller": 1, "created_by": null, "entity": 45, "kind": "play", "player": 1, "started_in_deck": true, "turn": 8}`

- P1: HP=26 Armor=0 Mana=0/4 Deck=24; Weapon=Shepherd's Crook 4/2; Board=Stadium Announcer#13 3/1, Sleepy Sheep#73 3/3; Hand=Torch(1), Windpeak Wyrm(5), Warptooth(4), Prescient Slitherdrake(4)
- P2: HP=22 Armor=0 Mana=0/4 Deck=23; Weapon=Defiled Spear 2/2; Board=Prescient Slitherdrake#45 5/8; Hand=Warptooth(4), Heir of Hereafter(5), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6), Erupting Volcano(3)

## Turn 9

### Step 25: shared-tree-ismcts-v1

**P2 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P2 END_TURN

Resolved events:

- `{"kind": "turn_end", "player": 1, "turn": 8}`
- `{"card": "CORE_REV_990", "kind": "draw", "player": 0, "turn": 9}`
- `{"kind": "turn_start", "player": 0, "turn": 9}`

- P1: HP=26 Armor=0 Mana=5/5 Deck=23; Weapon=Shepherd's Crook 4/2; Board=Stadium Announcer#13 3/1, Sleepy Sheep#73 3/3; Hand=Torch(1), Windpeak Wyrm(5), Warptooth(4), Prescient Slitherdrake(4), Sanguine Depths(1)
- P2: HP=22 Armor=0 Mana=0/4 Deck=23; Weapon=Defiled Spear 2/2; Board=Prescient Slitherdrake#45 5/8; Hand=Warptooth(4), Heir of Hereafter(5), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6), Erupting Volcano(3)

### Step 26: policy-prior-puct-v1

**P1 PLAY Windpeak Wyrm[TLC_600] -> P2 hero**

Legal actions: 14; Searched nodes: 5; Selected value: 0.8780

Top choices by root visit share:

- `0.250` — P1 HERO_POWER Armor Up
- `0.250` — P1 PLAY Windpeak Wyrm[TLC_600] -> P2 hero
- `0.250` — P1 PLAY Prescient Slitherdrake[END_033] -> -
- `0.250` — P1 PLAY Warptooth[JAIL_421] -> -
- `0.000` — P1 ATTACK Stadium Announcer#13 -> P2 hero

Resolved events:

- `{"card": "TLC_600", "controller": 0, "created_by": null, "entity": 11, "kind": "play", "player": 0, "started_in_deck": true, "turn": 9}`
- `{"amount": 5, "kind": "gain_armor", "player": 0, "turn": 9}`

- P1: HP=26 Armor=5 Mana=0/5 Deck=23; Weapon=Shepherd's Crook 4/2; Board=Stadium Announcer#13 3/1, Sleepy Sheep#73 3/3, Windpeak Wyrm#11 6/6; Hand=Torch(1), Warptooth(4), Prescient Slitherdrake(7), Sanguine Depths(1)
- P2: HP=17 Armor=0 Mana=0/4 Deck=23; Weapon=Defiled Spear 2/2; Board=Prescient Slitherdrake#45 5/8; Hand=Warptooth(4), Heir of Hereafter(5), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6), Erupting Volcano(3)

### Step 27: policy-prior-puct-v1

**P1 HERO_ATTACK -> P2 hero**

Legal actions: 5; Searched nodes: 5; Selected value: 0.9603

Top choices by root visit share:

- `0.250` — P1 ATTACK Stadium Announcer#13 -> P2 hero
- `0.250` — P1 END_TURN
- `0.250` — P1 HERO_ATTACK -> P2 hero
- `0.250` — P1 HERO_ATTACK -> P2 Prescient Slitherdrake#45
- `0.000` — P1 ATTACK Stadium Announcer#13 -> P2 Prescient Slitherdrake#45

- P1: HP=26 Armor=5 Mana=0/5 Deck=23; Weapon=Shepherd's Crook 4/1; Board=Stadium Announcer#13 3/1, Sleepy Sheep#73 3/3, Windpeak Wyrm#11 6/6, Sleepy Sheep#74 3/3; Hand=Torch(1), Warptooth(4), Prescient Slitherdrake(7), Sanguine Depths(1)
- P2: HP=13 Armor=0 Mana=0/4 Deck=23; Weapon=Defiled Spear 2/2; Board=Prescient Slitherdrake#45 5/8; Hand=Warptooth(4), Heir of Hereafter(5), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6), Erupting Volcano(3)

### Step 28: policy-prior-puct-v1

**P1 ATTACK Stadium Announcer#13 -> P2 hero**

Legal actions: 3; Searched nodes: 5; Selected value: 0.8803

Top choices by root visit share:

- `0.500` — P1 ATTACK Stadium Announcer#13 -> P2 hero
- `0.250` — P1 ATTACK Stadium Announcer#13 -> P2 Prescient Slitherdrake#45
- `0.250` — P1 END_TURN

- P1: HP=26 Armor=5 Mana=0/5 Deck=23; Weapon=Shepherd's Crook 4/1; Board=Stadium Announcer#13 3/1, Sleepy Sheep#73 3/3, Windpeak Wyrm#11 6/6, Sleepy Sheep#74 3/3; Hand=Torch(1), Warptooth(4), Prescient Slitherdrake(7), Sanguine Depths(1)
- P2: HP=10 Armor=0 Mana=0/4 Deck=23; Weapon=Defiled Spear 2/2; Board=Prescient Slitherdrake#45 5/8; Hand=Warptooth(4), Heir of Hereafter(5), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6), Erupting Volcano(3)

## Turn 10

### Step 29: policy-prior-puct-v1

**P1 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P1 END_TURN

Resolved events:

- `{"kind": "turn_end", "player": 0, "turn": 9}`
- `{"card": "END_033", "kind": "draw", "player": 1, "turn": 10}`
- `{"kind": "turn_start", "player": 1, "turn": 10}`

- P1: HP=26 Armor=5 Mana=0/5 Deck=23; Weapon=Shepherd's Crook 4/1; Board=Stadium Announcer#13 3/1, Sleepy Sheep#73 3/3, Windpeak Wyrm#11 6/6, Sleepy Sheep#74 3/3; Hand=Torch(1), Warptooth(4), Prescient Slitherdrake(7), Sanguine Depths(1)
- P2: HP=10 Armor=0 Mana=5/5 Deck=22; Weapon=Defiled Spear 2/2; Board=Prescient Slitherdrake#45 5/8; Hand=Warptooth(4), Heir of Hereafter(5), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6), Erupting Volcano(3), Prescient Slitherdrake(4)

### Step 30: shared-tree-ismcts-v1

**P2 HERO_ATTACK -> P1 Stadium Announcer#13**

Legal actions: 15; Searched nodes: 5; Selected value: -0.5900

Top choices by root visit share:

- `0.250` — P2 ATTACK Prescient Slitherdrake#45 -> P1 Windpeak Wyrm#11
- `0.250` — P2 ATTACK Prescient Slitherdrake#45 -> P1 Stadium Announcer#13
- `0.250` — P2 HERO_ATTACK -> P1 Windpeak Wyrm#11
- `0.250` — P2 HERO_ATTACK -> P1 Stadium Announcer#13
- `0.000` — P2 ATTACK Prescient Slitherdrake#45 -> P1 hero

Resolved events:

- `{"card": "TIME_034", "entity": 13, "kind": "minion_died", "player": 0, "turn": 10}`

- P1: HP=26 Armor=5 Mana=0/5 Deck=23; Weapon=Shepherd's Crook 4/1; Board=Sleepy Sheep#73 3/3, Windpeak Wyrm#11 6/4, Sleepy Sheep#74 3/3; Hand=Torch(1), Warptooth(4), Prescient Slitherdrake(7), Sanguine Depths(1)
- P2: HP=7 Armor=0 Mana=5/5 Deck=22; Weapon=Defiled Spear 2/1; Board=Prescient Slitherdrake#45 5/8; Hand=Warptooth(4), Heir of Hereafter(5), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6), Erupting Volcano(3), Prescient Slitherdrake(4)

### Step 31: shared-tree-ismcts-v1

**P2 PLAY Heir of Hereafter[TIME_871] -> -**

Legal actions: 11; Searched nodes: 5; Selected value: -0.7006

Top choices by root visit share:

- `0.250` — P2 ATTACK Prescient Slitherdrake#45 -> P1 hero
- `0.250` — P2 ATTACK Prescient Slitherdrake#45 -> P1 Windpeak Wyrm#11
- `0.250` — P2 PLAY Prescient Slitherdrake[END_033] -> -
- `0.250` — P2 PLAY Heir of Hereafter[TIME_871] -> -
- `0.000` — P2 END_TURN

Resolved events:

- `{"card": "TIME_871", "controller": 1, "created_by": "EDR_456", "entity": 65, "kind": "play", "player": 1, "started_in_deck": false, "turn": 10}`

- P1: HP=26 Armor=5 Mana=0/5 Deck=23; Weapon=Shepherd's Crook 4/1; Board=Sleepy Sheep#73 3/3, Windpeak Wyrm#11 6/4, Sleepy Sheep#74 3/3; Hand=Torch(1), Warptooth(4), Prescient Slitherdrake(7), Sanguine Depths(1)
- P2: HP=7 Armor=0 Mana=0/5 Deck=22; Weapon=Defiled Spear 2/1; Board=Prescient Slitherdrake#45 5/8, Heir of Hereafter#65 4/8; Hand=Warptooth(4), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6), Erupting Volcano(3), Prescient Slitherdrake(4)

### Step 32: shared-tree-ismcts-v1

**P2 ATTACK Prescient Slitherdrake#45 -> P1 hero**

Legal actions: 3; Searched nodes: 5; Selected value: -0.5241

Top choices by root visit share:

- `0.500` — P2 ATTACK Prescient Slitherdrake#45 -> P1 hero
- `0.250` — P2 ATTACK Prescient Slitherdrake#45 -> P1 Windpeak Wyrm#11
- `0.250` — P2 END_TURN

- P1: HP=26 Armor=0 Mana=0/5 Deck=23; Weapon=Shepherd's Crook 4/1; Board=Sleepy Sheep#73 3/3, Windpeak Wyrm#11 6/4, Sleepy Sheep#74 3/3; Hand=Torch(1), Warptooth(4), Prescient Slitherdrake(7), Sanguine Depths(1)
- P2: HP=7 Armor=0 Mana=0/5 Deck=22; Weapon=Defiled Spear 2/1; Board=Prescient Slitherdrake#45 5/8, Heir of Hereafter#65 4/8; Hand=Warptooth(4), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6), Erupting Volcano(3), Prescient Slitherdrake(4)

## Turn 11

### Step 33: shared-tree-ismcts-v1

**P2 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P2 END_TURN

Resolved events:

- `{"kind": "turn_end", "player": 1, "turn": 10}`
- `{"card": "EDR_416t", "entity": 73, "kind": "awaken", "player": 0, "turn": 11}`
- `{"card": "TLC_600", "kind": "draw", "player": 0, "turn": 11}`
- `{"kind": "turn_start", "player": 0, "turn": 11}`

- P1: HP=26 Armor=0 Mana=6/6 Deck=22; Weapon=Shepherd's Crook 4/1; Board=Sleepy Sheep#73 3/3, Windpeak Wyrm#11 6/4, Sleepy Sheep#74 3/3; Hand=Torch(1), Warptooth(4), Prescient Slitherdrake(4), Sanguine Depths(1), Windpeak Wyrm(5)
- P2: HP=7 Armor=0 Mana=0/5 Deck=22; Weapon=Defiled Spear 2/1; Board=Prescient Slitherdrake#45 5/8, Heir of Hereafter#65 4/8; Hand=Warptooth(4), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6), Erupting Volcano(3), Prescient Slitherdrake(4)

### Step 34: policy-prior-puct-v1

**P1 PLAY Windpeak Wyrm[TLC_600] -> P2 hero**

Legal actions: 15; Searched nodes: 5; Selected value: 0.9651

Top choices by root visit share:

- `0.250` — P1 PLAY Windpeak Wyrm[TLC_600] -> P2 hero
- `0.250` — P1 PLAY Windpeak Wyrm[TLC_600] -> P2 Heir of Hereafter#65
- `0.250` — P1 PLAY Prescient Slitherdrake[END_033] -> -
- `0.250` — P1 PLAY Warptooth[JAIL_421] -> -
- `0.000` — P1 ATTACK Windpeak Wyrm#11 -> P2 Heir of Hereafter#65

Resolved events:

- `{"card": "TLC_600", "controller": 0, "created_by": null, "entity": 12, "kind": "play", "player": 0, "started_in_deck": true, "turn": 11}`
- `{"amount": 5, "kind": "gain_armor", "player": 0, "turn": 11}`

- P1: HP=26 Armor=5 Mana=1/6 Deck=22; Weapon=Shepherd's Crook 4/1; Board=Sleepy Sheep#73 3/3, Windpeak Wyrm#11 6/4, Sleepy Sheep#74 3/3, Windpeak Wyrm#12 6/6; Hand=Torch(1), Warptooth(4), Prescient Slitherdrake(7), Sanguine Depths(1)
- P2: HP=2 Armor=0 Mana=0/5 Deck=22; Weapon=Defiled Spear 2/1; Board=Prescient Slitherdrake#45 5/8, Heir of Hereafter#65 4/8; Hand=Warptooth(4), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6), Erupting Volcano(3), Prescient Slitherdrake(4)

### Step 35: policy-prior-puct-v1

**P1 PLAY Sanguine Depths[CORE_REV_990] -> -**

Legal actions: 6; Searched nodes: 5; Selected value: 0.9637

Top choices by root visit share:

- `0.250` — P1 ATTACK Windpeak Wyrm#11 -> P2 Heir of Hereafter#65
- `0.250` — P1 HERO_ATTACK -> P2 Heir of Hereafter#65
- `0.250` — P1 PLAY Sanguine Depths[CORE_REV_990] -> -
- `0.250` — P1 PLAY Torch[CATA_585] -> P1 Windpeak Wyrm#11
- `0.000` — P1 ATTACK Sleepy Sheep#73 -> P2 Heir of Hereafter#65

Resolved events:

- `{"card": "CORE_REV_990", "controller": 0, "created_by": null, "entity": 2, "kind": "play", "player": 0, "started_in_deck": true, "turn": 11}`

- P1: HP=26 Armor=5 Mana=0/6 Deck=22; Weapon=Shepherd's Crook 4/1; Board=Sleepy Sheep#73 3/3, Windpeak Wyrm#11 6/4, Sleepy Sheep#74 3/3, Windpeak Wyrm#12 6/6; Hand=Torch(1), Warptooth(4), Prescient Slitherdrake(7)
- P2: HP=2 Armor=0 Mana=0/5 Deck=22; Weapon=Defiled Spear 2/1; Board=Prescient Slitherdrake#45 5/8, Heir of Hereafter#65 4/8; Hand=Warptooth(4), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6), Erupting Volcano(3), Prescient Slitherdrake(4)

## Turn 12

### Step 36: policy-prior-puct-v1

**P1 END_TURN**

Legal actions: 4; Searched nodes: 5; Selected value: 1.0000

Top choices by root visit share:

- `0.250` — P1 ATTACK Windpeak Wyrm#11 -> P2 Heir of Hereafter#65
- `0.250` — P1 ATTACK Sleepy Sheep#73 -> P2 Heir of Hereafter#65
- `0.250` — P1 END_TURN
- `0.250` — P1 HERO_ATTACK -> P2 Heir of Hereafter#65

Resolved events:

- `{"kind": "turn_end", "player": 0, "turn": 11}`
- `{"card": "JAIL_421", "kind": "draw", "player": 1, "turn": 12}`
- `{"kind": "turn_start", "player": 1, "turn": 12}`

- P1: HP=26 Armor=5 Mana=0/6 Deck=22; Weapon=Shepherd's Crook 4/1; Board=Sleepy Sheep#73 3/3, Windpeak Wyrm#11 6/4, Sleepy Sheep#74 3/3, Windpeak Wyrm#12 6/6; Hand=Torch(1), Warptooth(4), Prescient Slitherdrake(7)
- P2: HP=2 Armor=0 Mana=6/6 Deck=21; Weapon=Defiled Spear 2/1; Board=Prescient Slitherdrake#45 5/8, Heir of Hereafter#65 4/8; Hand=Warptooth(4), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6), Erupting Volcano(3), Prescient Slitherdrake(4), Warptooth(4)

### Step 37: shared-tree-ismcts-v1

**P2 ATTACK Heir of Hereafter#65 -> P1 Windpeak Wyrm#11**

Legal actions: 22; Searched nodes: 5; Selected value: -1.0000

Top choices by root visit share:

- `0.250` — P2 ATTACK Prescient Slitherdrake#45 -> P1 Windpeak Wyrm#11
- `0.250` — P2 ATTACK Prescient Slitherdrake#45 -> P1 Sleepy Sheep#73
- `0.250` — P2 ATTACK Heir of Hereafter#65 -> P1 Windpeak Wyrm#11
- `0.250` — P2 ATTACK Heir of Hereafter#65 -> P1 Sleepy Sheep#73
- `0.000` — P2 ATTACK Prescient Slitherdrake#45 -> P1 hero

Resolved events:

- `{"card": "TLC_600", "entity": 11, "kind": "minion_died", "player": 0, "turn": 12}`

- P1: HP=26 Armor=5 Mana=0/6 Deck=22; Weapon=Shepherd's Crook 4/1; Board=Sleepy Sheep#73 3/3, Sleepy Sheep#74 3/3, Windpeak Wyrm#12 6/6; Hand=Torch(1), Warptooth(4), Prescient Slitherdrake(7)
- P2: HP=2 Armor=0 Mana=6/6 Deck=21; Weapon=Defiled Spear 2/1; Board=Prescient Slitherdrake#45 5/8, Heir of Hereafter#65 4/2; Hand=Warptooth(4), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6), Erupting Volcano(3), Prescient Slitherdrake(4), Warptooth(4)

### Step 38: shared-tree-ismcts-v1

**P2 HERO_ATTACK -> P1 Windpeak Wyrm#12**

Legal actions: 16; Searched nodes: 5; Selected value: -1.0000

Top choices by root visit share:

- `0.250` — P2 ATTACK Prescient Slitherdrake#45 -> P1 Windpeak Wyrm#12
- `0.250` — P2 ATTACK Prescient Slitherdrake#45 -> P1 Sleepy Sheep#73
- `0.250` — P2 HERO_ATTACK -> P1 Windpeak Wyrm#12
- `0.250` — P2 HERO_ATTACK -> P1 Sleepy Sheep#73
- `0.000` — P2 ATTACK Prescient Slitherdrake#45 -> P1 hero

Resolved events:

- `{"card": "EDR_842", "kind": "weapon_destroyed", "player": 1, "turn": 12}`

- P1: HP=26 Armor=5 Mana=0/6 Deck=22; Weapon=Shepherd's Crook 4/1; Board=Sleepy Sheep#73 3/1, Sleepy Sheep#74 3/3, Windpeak Wyrm#12 6/4; Hand=Torch(1), Warptooth(4), Prescient Slitherdrake(7)
- P2: HP=-4 Armor=0 Mana=6/6 Deck=21; Weapon=none; Board=Prescient Slitherdrake#45 5/8, Heir of Hereafter#65 4/2; Hand=Warptooth(4), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6), Erupting Volcano(3), Prescient Slitherdrake(4), Warptooth(4)


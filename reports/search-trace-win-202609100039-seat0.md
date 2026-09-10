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

- `1.000` — P1 END_TURN; Q=0.0000; prior=0.0000

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

- `0.250` — P2 PLAY Darkrider[EDR_456] -> - [SELECTED]; Q=0.2420; prior=0.0000
- `0.250` — P2 PLAY Darkrider[EDR_456] -> -; Q=0.2420; prior=0.0000
- `0.250` — P2 PLAY The Coin[GAME_005] -> -; Q=0.0940; prior=0.0000
- `0.250` — P2 END_TURN; Q=-0.2687; prior=0.0000

Resolved events:

- `{"card": "EDR_456", "controller": 1, "created_by": null, "entity": 34, "kind": "play", "player": 1, "started_in_deck": true, "turn": 2}`
- `{"kind": "discover_offer", "options": [{"card": "FIR_956", "entity": 64, "gifts": ["rude_awakening"]}, {"card": "TIME_871", "entity": 65, "gifts": ["persisting_horror"]}, {"card": "TIME_714", "entity": 66, "gifts": ["well_rested"]}], "player": 1, "profile": "closed_pool", "turn": 2}`

- P1: HP=30 Armor=0 Mana=1/1 Deck=27; Weapon=none; Board=empty; Hand=Searing Fissure(2), Torch(1), Windpeak Wyrm(8), Searing Fissure(2)
- P2: HP=30 Armor=0 Mana=0/1 Deck=26; Weapon=none; Board=Darkrider#34 1/1; Hand=Darkrider(1), Shadowflame Suffusion(2), Warptooth(4), The Coin(0), Prescient Slitherdrake(7)

### Step 3: shared-tree-ismcts-v1

**P2 DISCOVER_PICK Heir of Hereafter[TIME_871] + persisting_horror**

Legal actions: 3; Searched nodes: 5; Selected value: 0.2513

Top choices by root visit share:

- `0.500` — P2 DISCOVER_PICK Heir of Hereafter[TIME_871] + persisting_horror [SELECTED]; Q=0.2513; prior=0.0000
- `0.250` — P2 DISCOVER_PICK Dragon Turtle[FIR_956] + rude_awakening; Q=0.2607; prior=0.0000
- `0.250` — P2 DISCOVER_PICK Chrono-Lord Epoch[TIME_714] + well_rested; Q=0.2607; prior=0.0000

Resolved events:

- `{"card": "TIME_871", "destination": "hand", "entity": 65, "gifts": ["persisting_horror"], "kind": "discover_pick", "player": 1, "source": "EDR_456", "turn": 2}`

- P1: HP=30 Armor=0 Mana=1/1 Deck=27; Weapon=none; Board=empty; Hand=Searing Fissure(2), Torch(1), Windpeak Wyrm(8), Searing Fissure(2)
- P2: HP=30 Armor=0 Mana=0/1 Deck=26; Weapon=none; Board=Darkrider#34 1/1; Hand=Darkrider(1), Shadowflame Suffusion(2), Warptooth(4), The Coin(0), Prescient Slitherdrake(4), Heir of Hereafter(5)

### Step 4: shared-tree-ismcts-v1

**P2 PLAY The Coin[GAME_005] -> -**

Legal actions: 2; Searched nodes: 5; Selected value: 0.0529

Top choices by root visit share:

- `0.750` — P2 PLAY The Coin[GAME_005] -> - [SELECTED]; Q=0.0529; prior=0.0000
- `0.250` — P2 END_TURN; Q=0.0599; prior=0.0000

Resolved events:

- `{"card": "GAME_005", "controller": 1, "created_by": "MULLIGAN", "entity": 61, "kind": "play", "player": 1, "started_in_deck": false, "turn": 2}`

- P1: HP=30 Armor=0 Mana=1/1 Deck=27; Weapon=none; Board=empty; Hand=Searing Fissure(2), Torch(1), Windpeak Wyrm(8), Searing Fissure(2)
- P2: HP=30 Armor=0 Mana=1/1 Deck=26; Weapon=none; Board=Darkrider#34 1/1; Hand=Darkrider(1), Shadowflame Suffusion(2), Warptooth(4), Prescient Slitherdrake(4), Heir of Hereafter(5)

### Step 5: shared-tree-ismcts-v1

**P2 PLAY Darkrider[EDR_456] -> -**

Legal actions: 2; Searched nodes: 5; Selected value: 0.0903

Top choices by root visit share:

- `0.750` — P2 PLAY Darkrider[EDR_456] -> - [SELECTED]; Q=0.0903; prior=0.0000
- `0.250` — P2 END_TURN; Q=-0.3121; prior=0.0000

Resolved events:

- `{"card": "EDR_456", "controller": 1, "created_by": null, "entity": 33, "kind": "play", "player": 1, "started_in_deck": true, "turn": 2}`
- `{"kind": "discover_offer", "options": [{"card": "TIME_045", "entity": 67, "gifts": ["sleepwalker"]}, {"card": "TIME_004", "entity": 68, "gifts": ["waking_terror"]}, {"card": "DINO_401", "entity": 69, "gifts": ["well_rested"]}], "player": 1, "profile": "closed_pool", "turn": 2}`

- P1: HP=30 Armor=0 Mana=1/1 Deck=27; Weapon=none; Board=empty; Hand=Searing Fissure(2), Torch(1), Windpeak Wyrm(8), Searing Fissure(2)
- P2: HP=30 Armor=0 Mana=0/1 Deck=26; Weapon=none; Board=Darkrider#34 1/1, Darkrider#33 1/1; Hand=Shadowflame Suffusion(2), Warptooth(4), Prescient Slitherdrake(4), Heir of Hereafter(5)

### Step 6: shared-tree-ismcts-v1

**P2 DISCOVER_PICK Whelp of the Infinite[TIME_045] + sleepwalker**

Legal actions: 3; Searched nodes: 5; Selected value: -0.1405

Top choices by root visit share:

- `0.500` — P2 DISCOVER_PICK Whelp of the Infinite[TIME_045] + sleepwalker [SELECTED]; Q=-0.1405; prior=0.0000
- `0.250` — P2 DISCOVER_PICK The Great Dracorex[DINO_401] + well_rested; Q=-0.1025; prior=0.0000
- `0.250` — P2 DISCOVER_PICK Conflux Crasher[TIME_004] + waking_terror; Q=-0.1503; prior=0.0000

Resolved events:

- `{"card": "TIME_045", "destination": "hand", "entity": 67, "gifts": ["sleepwalker"], "kind": "discover_pick", "player": 1, "source": "EDR_456", "turn": 2}`

- P1: HP=30 Armor=0 Mana=1/1 Deck=27; Weapon=none; Board=empty; Hand=Searing Fissure(2), Torch(1), Windpeak Wyrm(8), Searing Fissure(2)
- P2: HP=30 Armor=0 Mana=0/1 Deck=26; Weapon=none; Board=Darkrider#34 1/1, Darkrider#33 1/1; Hand=Shadowflame Suffusion(2), Warptooth(4), Prescient Slitherdrake(4), Heir of Hereafter(5), Whelp of the Infinite(3)

## Turn 3

### Step 7: shared-tree-ismcts-v1

**P2 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P2 END_TURN; Q=0.0000; prior=0.0000

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

- `0.250` — P1 PLAY Searing Fissure[CATA_582] -> - [SELECTED]; Q=0.0371; prior=0.3001
- `0.250` — P1 PLAY Searing Fissure[CATA_582] -> -; Q=-0.1492; prior=0.3089
- `0.250` — P1 HERO_POWER Armor Up; Q=-0.2607; prior=0.2750
- `0.250` — P1 END_TURN; Q=-0.6253; prior=0.1161

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

- `0.500` — P1 HERO_ATTACK -> P2 hero [SELECTED]; Q=0.0271; prior=0.5074
- `0.500` — P1 END_TURN; Q=-0.1052; prior=0.4926

- P1: HP=30 Armor=0 Mana=0/2 Deck=26; Weapon=none; Board=empty; Hand=Searing Fissure(2), Torch(1), Windpeak Wyrm(8), Warptooth(4)
- P2: HP=27 Armor=0 Mana=0/1 Deck=26; Weapon=none; Board=empty; Hand=Shadowflame Suffusion(2), Warptooth(4), Prescient Slitherdrake(4), Heir of Hereafter(5), Whelp of the Infinite(3)

## Turn 4

### Step 10: policy-prior-puct-v1

**P1 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P1 END_TURN; Q=0.0000; prior=0.0000

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

- `0.250` — P2 HERO_POWER Armor Up [SELECTED]; Q=-0.1503; prior=0.0000
- `0.250` — P2 PLAY Shadowflame Suffusion[FIR_939] -> P1 hero; Q=-0.1924; prior=0.0000
- `0.250` — P2 PLAY Searing Fissure[CATA_582] -> -; Q=-0.2290; prior=0.0000
- `0.250` — P2 PLAY Shadowflame Suffusion[FIR_939] -> P2 hero; Q=-0.3452; prior=0.0000
- `0.000` — P2 END_TURN; Q=0.0000; prior=0.0000

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

- `1.000` — P2 END_TURN; Q=0.0000; prior=0.0000

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

- `0.500` — P1 PLAY Searing Fissure[CATA_582] -> - [SELECTED]; Q=-0.2827; prior=0.4134
- `0.250` — P1 HERO_POWER Armor Up; Q=-0.2819; prior=0.4143
- `0.250` — P1 END_TURN; Q=-0.5092; prior=0.1724

Resolved events:

- `{"card": "CATA_582", "controller": 0, "created_by": null, "entity": 19, "kind": "play", "player": 0, "started_in_deck": true, "turn": 5}`

- P1: HP=30 Armor=0 Mana=1/3 Deck=25; Weapon=none; Board=empty; Hand=Torch(1), Windpeak Wyrm(8), Warptooth(4), Prescient Slitherdrake(4)
- P2: HP=27 Armor=2 Mana=0/2 Deck=25; Weapon=none; Board=empty; Hand=Shadowflame Suffusion(2), Warptooth(4), Prescient Slitherdrake(4), Heir of Hereafter(5), Whelp of the Infinite(3), Searing Fissure(2)

### Step 14: policy-prior-puct-v1

**P1 HERO_ATTACK -> P2 hero**

Legal actions: 2; Searched nodes: 5; Selected value: -0.1861

Top choices by root visit share:

- `0.500` — P1 HERO_ATTACK -> P2 hero [SELECTED]; Q=-0.1861; prior=0.4679
- `0.500` — P1 END_TURN; Q=-0.3045; prior=0.5321

- P1: HP=30 Armor=0 Mana=1/3 Deck=25; Weapon=none; Board=empty; Hand=Torch(1), Windpeak Wyrm(8), Warptooth(4), Prescient Slitherdrake(4)
- P2: HP=26 Armor=0 Mana=0/2 Deck=25; Weapon=none; Board=empty; Hand=Shadowflame Suffusion(2), Warptooth(4), Prescient Slitherdrake(4), Heir of Hereafter(5), Whelp of the Infinite(3), Searing Fissure(2)

## Turn 6

### Step 15: policy-prior-puct-v1

**P1 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P1 END_TURN; Q=0.0000; prior=0.0000

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

- `0.250` — P2 PLAY Shadowflame Suffusion[FIR_939] -> P1 hero [SELECTED]; Q=-0.1670; prior=0.0000
- `0.250` — P2 PLAY Whelp of the Infinite[TIME_045] -> -; Q=-0.5088; prior=0.0000
- `0.250` — P2 PLAY Searing Fissure[CATA_582] -> -; Q=-0.6672; prior=0.0000
- `0.250` — P2 PLAY Searing Fissure[CATA_582] -> -; Q=-0.6697; prior=0.0000
- `0.000` — P2 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "FIR_939", "controller": 1, "created_by": null, "entity": 39, "kind": "play", "player": 1, "started_in_deck": true, "turn": 6}`
- `{"kind": "discover_offer", "options": [{"card": "CATA_591", "entity": 70, "gifts": ["rude_awakening"]}, {"card": "JAIL_421", "entity": 71, "gifts": ["bundled_up"]}, {"card": "TIME_714", "entity": 72, "gifts": ["sleepwalker"]}], "player": 1, "profile": "closed_pool", "turn": 6}`

- P1: HP=28 Armor=0 Mana=1/3 Deck=25; Weapon=none; Board=empty; Hand=Torch(1), Windpeak Wyrm(8), Warptooth(4), Prescient Slitherdrake(4)
- P2: HP=26 Armor=0 Mana=1/3 Deck=24; Weapon=none; Board=empty; Hand=Warptooth(4), Prescient Slitherdrake(4), Heir of Hereafter(5), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2)

### Step 17: shared-tree-ismcts-v1

**P2 DISCOVER_PICK Chrono-Lord Epoch[TIME_714] + sleepwalker**

Legal actions: 3; Searched nodes: 5; Selected value: -0.3557

Top choices by root visit share:

- `0.500` — P2 DISCOVER_PICK Chrono-Lord Epoch[TIME_714] + sleepwalker [SELECTED]; Q=-0.3557; prior=0.0000
- `0.250` — P2 DISCOVER_PICK Commander Geddon[CATA_591] + rude_awakening; Q=-0.3054; prior=0.0000
- `0.250` — P2 DISCOVER_PICK Warptooth[JAIL_421] + bundled_up; Q=-0.5342; prior=0.0000

Resolved events:

- `{"card": "TIME_714", "destination": "hand", "entity": 72, "gifts": ["sleepwalker"], "kind": "discover_pick", "player": 1, "source": "FIR_939", "turn": 6}`

- P1: HP=28 Armor=0 Mana=1/3 Deck=25; Weapon=none; Board=empty; Hand=Torch(1), Windpeak Wyrm(8), Warptooth(4), Prescient Slitherdrake(4)
- P2: HP=26 Armor=0 Mana=1/3 Deck=24; Weapon=none; Board=empty; Hand=Warptooth(4), Prescient Slitherdrake(4), Heir of Hereafter(5), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6)

## Turn 7

### Step 18: shared-tree-ismcts-v1

**P2 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P2 END_TURN; Q=0.0000; prior=0.0000

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

- `0.250` — P1 PLAY Stadium Announcer[TIME_034] -> - [SELECTED]; Q=0.7815; prior=0.2920
- `0.250` — P1 PLAY Prescient Slitherdrake[END_033] -> -; Q=0.3532; prior=0.2547
- `0.250` — P1 PLAY Warptooth[JAIL_421] -> -; Q=-0.1570; prior=0.2045
- `0.250` — P1 HERO_POWER Armor Up; Q=-0.2903; prior=0.1474
- `0.000` — P1 END_TURN; Q=0.0000; prior=0.0000

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

- `0.500` — P1 REWIND_KEEP [SELECTED]; Q=0.6692; prior=0.5299
- `0.500` — P1 REWIND_RETRY; Q=0.6403; prior=0.4701

Resolved events:

- `{"decision": "keep", "effect": "stadium_weapons", "kind": "rewind_pick", "outcome": [{"attack": 4, "card": "EDR_416", "durability": 3, "name": "Shepherd's Crook"}, {"attack": 2, "card": "EDR_842", "durability": 3, "name": "Defiled Spear"}], "player": 0, "turn": 7}`

- P1: HP=28 Armor=0 Mana=0/4 Deck=24; Weapon=Shepherd's Crook 4/3; Board=Stadium Announcer#13 3/3; Hand=Torch(1), Windpeak Wyrm(8), Warptooth(4), Prescient Slitherdrake(4)
- P2: HP=26 Armor=0 Mana=1/3 Deck=24; Weapon=Defiled Spear 2/3; Board=empty; Hand=Warptooth(4), Prescient Slitherdrake(4), Heir of Hereafter(5), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6)

### Step 21: policy-prior-puct-v1

**P1 HERO_ATTACK -> P2 hero**

Legal actions: 2; Searched nodes: 5; Selected value: 0.5831

Top choices by root visit share:

- `0.750` — P1 HERO_ATTACK -> P2 hero [SELECTED]; Q=0.5831; prior=0.6430
- `0.250` — P1 END_TURN; Q=0.1553; prior=0.3570

- P1: HP=28 Armor=0 Mana=0/4 Deck=24; Weapon=Shepherd's Crook 4/2; Board=Stadium Announcer#13 3/3, Sleepy Sheep#73 3/3; Hand=Torch(1), Windpeak Wyrm(8), Warptooth(4), Prescient Slitherdrake(4)
- P2: HP=22 Armor=0 Mana=1/3 Deck=24; Weapon=Defiled Spear 2/3; Board=empty; Hand=Warptooth(4), Prescient Slitherdrake(4), Heir of Hereafter(5), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6)

## Turn 8

### Step 22: policy-prior-puct-v1

**P1 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P1 END_TURN; Q=0.0000; prior=0.0000

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

- `0.250` — P2 HERO_ATTACK -> P1 hero [SELECTED]; Q=-0.2538; prior=0.0000
- `0.250` — P2 HERO_ATTACK -> P1 Stadium Announcer#13; Q=-0.4060; prior=0.0000
- `0.250` — P2 PLAY Prescient Slitherdrake[END_033] -> -; Q=-0.4060; prior=0.0000
- `0.250` — P2 PLAY Warptooth[JAIL_421] -> -; Q=-0.5483; prior=0.0000
- `0.000` — P2 END_TURN; Q=0.0000; prior=0.0000

- P1: HP=26 Armor=0 Mana=0/4 Deck=24; Weapon=Shepherd's Crook 4/2; Board=Stadium Announcer#13 3/1, Sleepy Sheep#73 3/3; Hand=Torch(1), Windpeak Wyrm(5), Warptooth(4), Prescient Slitherdrake(4)
- P2: HP=22 Armor=0 Mana=4/4 Deck=23; Weapon=Defiled Spear 2/2; Board=empty; Hand=Warptooth(4), Prescient Slitherdrake(4), Heir of Hereafter(5), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6), Erupting Volcano(3)

### Step 24: shared-tree-ismcts-v1

**P2 PLAY Prescient Slitherdrake[END_033] -> -**

Legal actions: 8; Searched nodes: 5; Selected value: -0.0263

Top choices by root visit share:

- `0.250` — P2 PLAY Prescient Slitherdrake[END_033] -> - [SELECTED]; Q=-0.0263; prior=0.0000
- `0.250` — P2 PLAY Whelp of the Infinite[TIME_045] -> -; Q=-0.5206; prior=0.0000
- `0.250` — P2 PLAY Warptooth[JAIL_421] -> -; Q=-0.7966; prior=0.0000
- `0.250` — P2 PLAY Erupting Volcano[CATA_584] -> -; Q=-0.9212; prior=0.0000
- `0.000` — P2 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "END_033", "controller": 1, "created_by": null, "entity": 45, "kind": "play", "player": 1, "started_in_deck": true, "turn": 8}`

- P1: HP=26 Armor=0 Mana=0/4 Deck=24; Weapon=Shepherd's Crook 4/2; Board=Stadium Announcer#13 3/1, Sleepy Sheep#73 3/3; Hand=Torch(1), Windpeak Wyrm(5), Warptooth(4), Prescient Slitherdrake(4)
- P2: HP=22 Armor=0 Mana=0/4 Deck=23; Weapon=Defiled Spear 2/2; Board=Prescient Slitherdrake#45 5/8; Hand=Warptooth(4), Heir of Hereafter(5), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6), Erupting Volcano(3)

## Turn 9

### Step 25: shared-tree-ismcts-v1

**P2 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P2 END_TURN; Q=0.0000; prior=0.0000

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

- `0.250` — P1 PLAY Windpeak Wyrm[TLC_600] -> P2 hero [SELECTED]; Q=0.8780; prior=0.1285
- `0.250` — P1 PLAY Prescient Slitherdrake[END_033] -> -; Q=0.6497; prior=0.1029
- `0.250` — P1 PLAY Warptooth[JAIL_421] -> -; Q=0.5042; prior=0.0925
- `0.250` — P1 HERO_POWER Armor Up; Q=0.1200; prior=0.1151
- `0.000` — P1 ATTACK Stadium Announcer#13 -> P2 hero; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "TLC_600", "controller": 0, "created_by": null, "entity": 11, "kind": "play", "player": 0, "started_in_deck": true, "turn": 9}`
- `{"amount": 5, "kind": "gain_armor", "player": 0, "turn": 9}`

- P1: HP=26 Armor=5 Mana=0/5 Deck=23; Weapon=Shepherd's Crook 4/2; Board=Stadium Announcer#13 3/1, Sleepy Sheep#73 3/3, Windpeak Wyrm#11 6/6; Hand=Torch(1), Warptooth(4), Prescient Slitherdrake(7), Sanguine Depths(1)
- P2: HP=17 Armor=0 Mana=0/4 Deck=23; Weapon=Defiled Spear 2/2; Board=Prescient Slitherdrake#45 5/8; Hand=Warptooth(4), Heir of Hereafter(5), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6), Erupting Volcano(3)

### Step 27: policy-prior-puct-v1

**P1 HERO_ATTACK -> P2 hero**

Legal actions: 5; Searched nodes: 5; Selected value: 0.9603

Top choices by root visit share:

- `0.250` — P1 HERO_ATTACK -> P2 hero [SELECTED]; Q=0.9603; prior=0.3068
- `0.250` — P1 ATTACK Stadium Announcer#13 -> P2 hero; Q=0.9192; prior=0.2730
- `0.250` — P1 HERO_ATTACK -> P2 Prescient Slitherdrake#45; Q=0.9174; prior=0.1515
- `0.250` — P1 END_TURN; Q=-0.5218; prior=0.1344
- `0.000` — P1 ATTACK Stadium Announcer#13 -> P2 Prescient Slitherdrake#45; Q=0.0000; prior=0.0000

- P1: HP=26 Armor=5 Mana=0/5 Deck=23; Weapon=Shepherd's Crook 4/1; Board=Stadium Announcer#13 3/1, Sleepy Sheep#73 3/3, Windpeak Wyrm#11 6/6, Sleepy Sheep#74 3/3; Hand=Torch(1), Warptooth(4), Prescient Slitherdrake(7), Sanguine Depths(1)
- P2: HP=13 Armor=0 Mana=0/4 Deck=23; Weapon=Defiled Spear 2/2; Board=Prescient Slitherdrake#45 5/8; Hand=Warptooth(4), Heir of Hereafter(5), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6), Erupting Volcano(3)

### Step 28: policy-prior-puct-v1

**P1 ATTACK Stadium Announcer#13 -> P2 hero**

Legal actions: 3; Searched nodes: 5; Selected value: 0.8803

Top choices by root visit share:

- `0.500` — P1 ATTACK Stadium Announcer#13 -> P2 hero [SELECTED]; Q=0.8803; prior=0.4924
- `0.250` — P1 ATTACK Stadium Announcer#13 -> P2 Prescient Slitherdrake#45; Q=0.9558; prior=0.2383
- `0.250` — P1 END_TURN; Q=-0.1053; prior=0.2694

- P1: HP=26 Armor=5 Mana=0/5 Deck=23; Weapon=Shepherd's Crook 4/1; Board=Stadium Announcer#13 3/1, Sleepy Sheep#73 3/3, Windpeak Wyrm#11 6/6, Sleepy Sheep#74 3/3; Hand=Torch(1), Warptooth(4), Prescient Slitherdrake(7), Sanguine Depths(1)
- P2: HP=10 Armor=0 Mana=0/4 Deck=23; Weapon=Defiled Spear 2/2; Board=Prescient Slitherdrake#45 5/8; Hand=Warptooth(4), Heir of Hereafter(5), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6), Erupting Volcano(3)

## Turn 10

### Step 29: policy-prior-puct-v1

**P1 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P1 END_TURN; Q=0.0000; prior=0.0000

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

- `0.250` — P2 HERO_ATTACK -> P1 Stadium Announcer#13 [SELECTED]; Q=-0.5900; prior=0.0000
- `0.250` — P2 ATTACK Prescient Slitherdrake#45 -> P1 Windpeak Wyrm#11; Q=-0.6906; prior=0.0000
- `0.250` — P2 HERO_ATTACK -> P1 Windpeak Wyrm#11; Q=-0.6906; prior=0.0000
- `0.250` — P2 ATTACK Prescient Slitherdrake#45 -> P1 Stadium Announcer#13; Q=-0.8793; prior=0.0000
- `0.000` — P2 ATTACK Prescient Slitherdrake#45 -> P1 hero; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "TIME_034", "entity": 13, "kind": "minion_died", "player": 0, "turn": 10}`

- P1: HP=26 Armor=5 Mana=0/5 Deck=23; Weapon=Shepherd's Crook 4/1; Board=Sleepy Sheep#73 3/3, Windpeak Wyrm#11 6/4, Sleepy Sheep#74 3/3; Hand=Torch(1), Warptooth(4), Prescient Slitherdrake(7), Sanguine Depths(1)
- P2: HP=7 Armor=0 Mana=5/5 Deck=22; Weapon=Defiled Spear 2/1; Board=Prescient Slitherdrake#45 5/8; Hand=Warptooth(4), Heir of Hereafter(5), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6), Erupting Volcano(3), Prescient Slitherdrake(4)

### Step 31: shared-tree-ismcts-v1

**P2 PLAY Heir of Hereafter[TIME_871] -> -**

Legal actions: 11; Searched nodes: 5; Selected value: -0.7006

Top choices by root visit share:

- `0.250` — P2 PLAY Heir of Hereafter[TIME_871] -> - [SELECTED]; Q=-0.7006; prior=0.0000
- `0.250` — P2 ATTACK Prescient Slitherdrake#45 -> P1 hero; Q=-0.7710; prior=0.0000
- `0.250` — P2 ATTACK Prescient Slitherdrake#45 -> P1 Windpeak Wyrm#11; Q=-0.8395; prior=0.0000
- `0.250` — P2 PLAY Prescient Slitherdrake[END_033] -> -; Q=-0.8395; prior=0.0000
- `0.000` — P2 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "TIME_871", "controller": 1, "created_by": "EDR_456", "entity": 65, "kind": "play", "player": 1, "started_in_deck": false, "turn": 10}`

- P1: HP=26 Armor=5 Mana=0/5 Deck=23; Weapon=Shepherd's Crook 4/1; Board=Sleepy Sheep#73 3/3, Windpeak Wyrm#11 6/4, Sleepy Sheep#74 3/3; Hand=Torch(1), Warptooth(4), Prescient Slitherdrake(7), Sanguine Depths(1)
- P2: HP=7 Armor=0 Mana=0/5 Deck=22; Weapon=Defiled Spear 2/1; Board=Prescient Slitherdrake#45 5/8, Heir of Hereafter#65 4/8; Hand=Warptooth(4), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6), Erupting Volcano(3), Prescient Slitherdrake(4)

### Step 32: shared-tree-ismcts-v1

**P2 ATTACK Prescient Slitherdrake#45 -> P1 hero**

Legal actions: 3; Searched nodes: 5; Selected value: -0.5241

Top choices by root visit share:

- `0.500` — P2 ATTACK Prescient Slitherdrake#45 -> P1 hero [SELECTED]; Q=-0.5241; prior=0.0000
- `0.250` — P2 ATTACK Prescient Slitherdrake#45 -> P1 Windpeak Wyrm#11; Q=-0.5618; prior=0.0000
- `0.250` — P2 END_TURN; Q=-0.7355; prior=0.0000

- P1: HP=26 Armor=0 Mana=0/5 Deck=23; Weapon=Shepherd's Crook 4/1; Board=Sleepy Sheep#73 3/3, Windpeak Wyrm#11 6/4, Sleepy Sheep#74 3/3; Hand=Torch(1), Warptooth(4), Prescient Slitherdrake(7), Sanguine Depths(1)
- P2: HP=7 Armor=0 Mana=0/5 Deck=22; Weapon=Defiled Spear 2/1; Board=Prescient Slitherdrake#45 5/8, Heir of Hereafter#65 4/8; Hand=Warptooth(4), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6), Erupting Volcano(3), Prescient Slitherdrake(4)

## Turn 11

### Step 33: shared-tree-ismcts-v1

**P2 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P2 END_TURN; Q=0.0000; prior=0.0000

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

- `0.250` — P1 PLAY Windpeak Wyrm[TLC_600] -> P2 hero [SELECTED]; Q=0.9651; prior=0.0865
- `0.250` — P1 PLAY Windpeak Wyrm[TLC_600] -> P2 Heir of Hereafter#65; Q=0.9592; prior=0.1202
- `0.250` — P1 PLAY Prescient Slitherdrake[END_033] -> -; Q=0.8903; prior=0.1610
- `0.250` — P1 PLAY Warptooth[JAIL_421] -> -; Q=0.7777; prior=0.0725
- `0.000` — P1 ATTACK Windpeak Wyrm#11 -> P2 Heir of Hereafter#65; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "TLC_600", "controller": 0, "created_by": null, "entity": 12, "kind": "play", "player": 0, "started_in_deck": true, "turn": 11}`
- `{"amount": 5, "kind": "gain_armor", "player": 0, "turn": 11}`

- P1: HP=26 Armor=5 Mana=1/6 Deck=22; Weapon=Shepherd's Crook 4/1; Board=Sleepy Sheep#73 3/3, Windpeak Wyrm#11 6/4, Sleepy Sheep#74 3/3, Windpeak Wyrm#12 6/6; Hand=Torch(1), Warptooth(4), Prescient Slitherdrake(7), Sanguine Depths(1)
- P2: HP=2 Armor=0 Mana=0/5 Deck=22; Weapon=Defiled Spear 2/1; Board=Prescient Slitherdrake#45 5/8, Heir of Hereafter#65 4/8; Hand=Warptooth(4), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6), Erupting Volcano(3), Prescient Slitherdrake(4)

### Step 35: policy-prior-puct-v1

**P1 PLAY Sanguine Depths[CORE_REV_990] -> -**

Legal actions: 6; Searched nodes: 5; Selected value: 0.9637

Top choices by root visit share:

- `0.250` — P1 PLAY Sanguine Depths[CORE_REV_990] -> - [SELECTED]; Q=0.9637; prior=0.2513
- `0.250` — P1 ATTACK Windpeak Wyrm#11 -> P2 Heir of Hereafter#65; Q=0.9637; prior=0.1820
- `0.250` — P1 HERO_ATTACK -> P2 Heir of Hereafter#65; Q=0.9637; prior=0.1617
- `0.250` — P1 PLAY Torch[CATA_585] -> P1 Windpeak Wyrm#11; Q=0.9023; prior=0.1654
- `0.000` — P1 ATTACK Sleepy Sheep#73 -> P2 Heir of Hereafter#65; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "CORE_REV_990", "controller": 0, "created_by": null, "entity": 2, "kind": "play", "player": 0, "started_in_deck": true, "turn": 11}`

- P1: HP=26 Armor=5 Mana=0/6 Deck=22; Weapon=Shepherd's Crook 4/1; Board=Sleepy Sheep#73 3/3, Windpeak Wyrm#11 6/4, Sleepy Sheep#74 3/3, Windpeak Wyrm#12 6/6; Hand=Torch(1), Warptooth(4), Prescient Slitherdrake(7)
- P2: HP=2 Armor=0 Mana=0/5 Deck=22; Weapon=Defiled Spear 2/1; Board=Prescient Slitherdrake#45 5/8, Heir of Hereafter#65 4/8; Hand=Warptooth(4), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6), Erupting Volcano(3), Prescient Slitherdrake(4)

## Turn 12

### Step 36: policy-prior-puct-v1

**P1 END_TURN**

Legal actions: 4; Searched nodes: 5; Selected value: 1.0000

Top choices by root visit share:

- `0.250` — P1 END_TURN [SELECTED]; Q=1.0000; prior=0.1633
- `0.250` — P1 ATTACK Windpeak Wyrm#11 -> P2 Heir of Hereafter#65; Q=0.9622; prior=0.3100
- `0.250` — P1 ATTACK Sleepy Sheep#73 -> P2 Heir of Hereafter#65; Q=0.9622; prior=0.2572
- `0.250` — P1 HERO_ATTACK -> P2 Heir of Hereafter#65; Q=0.9622; prior=0.2696

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

- `0.250` — P2 ATTACK Heir of Hereafter#65 -> P1 Windpeak Wyrm#11 [SELECTED]; Q=-1.0000; prior=0.0000
- `0.250` — P2 ATTACK Prescient Slitherdrake#45 -> P1 Windpeak Wyrm#11; Q=-1.0000; prior=0.0000
- `0.250` — P2 ATTACK Prescient Slitherdrake#45 -> P1 Sleepy Sheep#73; Q=-1.0000; prior=0.0000
- `0.250` — P2 ATTACK Heir of Hereafter#65 -> P1 Sleepy Sheep#73; Q=-1.0000; prior=0.0000
- `0.000` — P2 ATTACK Prescient Slitherdrake#45 -> P1 hero; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "TLC_600", "entity": 11, "kind": "minion_died", "player": 0, "turn": 12}`

- P1: HP=26 Armor=5 Mana=0/6 Deck=22; Weapon=Shepherd's Crook 4/1; Board=Sleepy Sheep#73 3/3, Sleepy Sheep#74 3/3, Windpeak Wyrm#12 6/6; Hand=Torch(1), Warptooth(4), Prescient Slitherdrake(7)
- P2: HP=2 Armor=0 Mana=6/6 Deck=21; Weapon=Defiled Spear 2/1; Board=Prescient Slitherdrake#45 5/8, Heir of Hereafter#65 4/2; Hand=Warptooth(4), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6), Erupting Volcano(3), Prescient Slitherdrake(4), Warptooth(4)

### Step 38: shared-tree-ismcts-v1

**P2 HERO_ATTACK -> P1 Windpeak Wyrm#12**

Legal actions: 16; Searched nodes: 5; Selected value: -1.0000

Top choices by root visit share:

- `0.250` — P2 HERO_ATTACK -> P1 Windpeak Wyrm#12 [SELECTED]; Q=-1.0000; prior=0.0000
- `0.250` — P2 ATTACK Prescient Slitherdrake#45 -> P1 Windpeak Wyrm#12; Q=-1.0000; prior=0.0000
- `0.250` — P2 ATTACK Prescient Slitherdrake#45 -> P1 Sleepy Sheep#73; Q=-1.0000; prior=0.0000
- `0.250` — P2 HERO_ATTACK -> P1 Sleepy Sheep#73; Q=-1.0000; prior=0.0000
- `0.000` — P2 ATTACK Prescient Slitherdrake#45 -> P1 hero; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "EDR_842", "kind": "weapon_destroyed", "player": 1, "turn": 12}`

- P1: HP=26 Armor=5 Mana=0/6 Deck=22; Weapon=Shepherd's Crook 4/1; Board=Sleepy Sheep#73 3/1, Sleepy Sheep#74 3/3, Windpeak Wyrm#12 6/4; Hand=Torch(1), Warptooth(4), Prescient Slitherdrake(7)
- P2: HP=-4 Armor=0 Mana=6/6 Deck=21; Weapon=none; Board=Prescient Slitherdrake#45 5/8, Heir of Hereafter#65 4/2; Hand=Warptooth(4), Whelp of the Infinite(3), Searing Fissure(2), Searing Fissure(2), Chrono-Lord Epoch(6), Erupting Volcano(3), Prescient Slitherdrake(4), Warptooth(4)


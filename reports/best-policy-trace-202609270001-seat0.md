# Policy-prior PUCT vs ISMCTS detailed trace

- Seed: `202609270001`
- Candidate: `P1`
- Winner: `P1`
- Candidate win: `True`
- Actions: `67`
- Illegal actions: `0`

## Turn 1

### Step 1: policy-prior-puct-v1

**P1 PLAY Cannonmaster[CAP_107] -> -**

Legal actions: 3; Searched nodes: 7; Selected value: -0.0907

Top choices by root visit share:

- `0.500` — P1 PLAY Cannonmaster[CAP_107] -> - [SELECTED]; Q=-0.0907; prior=0.5797
- `0.333` — P1 PLAY Darkrider[EDR_456] -> -; Q=-0.0425; prior=0.2841
- `0.167` — P1 END_TURN; Q=-0.3537; prior=0.1362

Resolved events:

- `{"card": "CAP_107", "controller": 0, "created_by": null, "entity": 29, "kind": "play", "player": 0, "started_in_deck": true, "turn": 1}`
- `{"card": "CAP_107t", "entity": 64, "kind": "generated_to_hand", "player": 0, "source": "CAP_107", "turn": 1}`

- P1: HP=30 Armor=0 Mana=0/1 Deck=27; Weapon=none; Board=Cannonmaster#29 3/1; Hand=Brood Keeper(2), Darkrider(1), Royal Librarian(4), Cannoneer(1)
- P2: HP=30 Armor=0 Mana=0/0 Deck=27; Weapon=none; Board=empty; Hand=Hook n' Heave(2), Darkrider(1), Stadium Announcer(4), Searing Fissure(2), The Coin(0)

## Turn 2

### Step 2: policy-prior-puct-v1

**P1 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P1 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 0, "turn": 1}`
- `{"card": "CAP_105", "kind": "draw", "player": 1, "turn": 2}`
- `{"kind": "turn_start", "player": 1, "turn": 2}`

- P1: HP=30 Armor=0 Mana=0/1 Deck=27; Weapon=none; Board=Cannonmaster#29 3/1; Hand=Brood Keeper(2), Darkrider(1), Royal Librarian(4), Cannoneer(1)
- P2: HP=30 Armor=0 Mana=1/1 Deck=26; Weapon=none; Board=empty; Hand=Hook n' Heave(2), Darkrider(1), Stadium Announcer(4), Searing Fissure(2), The Coin(0), Hook n' Heave(2)

### Step 3: shared-tree-ismcts-v1

**P2 PLAY The Coin[GAME_005] -> -**

Legal actions: 3; Searched nodes: 5; Selected value: 0.1828

Top choices by root visit share:

- `0.500` — P2 PLAY The Coin[GAME_005] -> - [SELECTED]; Q=0.1828; prior=0.0000
- `0.250` — P2 PLAY Darkrider[EDR_456] -> -; Q=-0.1093; prior=0.0000
- `0.250` — P2 END_TURN; Q=-0.2939; prior=0.0000

Resolved events:

- `{"card": "GAME_005", "controller": 1, "created_by": "MULLIGAN", "entity": 61, "kind": "play", "player": 1, "started_in_deck": false, "turn": 2}`

- P1: HP=30 Armor=0 Mana=0/1 Deck=27; Weapon=none; Board=Cannonmaster#29 3/1; Hand=Brood Keeper(2), Darkrider(1), Royal Librarian(4), Cannoneer(1)
- P2: HP=30 Armor=0 Mana=2/1 Deck=26; Weapon=none; Board=empty; Hand=Hook n' Heave(2), Darkrider(1), Stadium Announcer(4), Searing Fissure(2), Hook n' Heave(2)

### Step 4: shared-tree-ismcts-v1

**P2 PLAY Hook n' Heave[CAP_105] -> -**

Legal actions: 6; Searched nodes: 5; Selected value: 0.1731

Top choices by root visit share:

- `0.250` — P2 PLAY Hook n' Heave[CAP_105] -> - [SELECTED]; Q=0.1731; prior=0.0000
- `0.250` — P2 PLAY Hook n' Heave[CAP_105] -> -; Q=0.1731; prior=0.0000
- `0.250` — P2 PLAY Darkrider[EDR_456] -> -; Q=0.0000; prior=0.0000
- `0.250` — P2 PLAY Searing Fissure[CATA_582] -> -; Q=-0.1093; prior=0.0000
- `0.000` — P2 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "CAP_105", "controller": 1, "created_by": null, "entity": 57, "kind": "play", "player": 1, "started_in_deck": true, "turn": 2}`
- `{"kind": "discover_offer", "options": [{"card": "CAP_107", "entity": 65, "gifts": []}], "player": 1, "profile": "closed_pool", "turn": 2}`

- P1: HP=30 Armor=0 Mana=0/1 Deck=27; Weapon=none; Board=Cannonmaster#29 3/1; Hand=Brood Keeper(2), Darkrider(1), Royal Librarian(4), Cannoneer(1)
- P2: HP=30 Armor=0 Mana=0/1 Deck=26; Weapon=none; Board=empty; Hand=Hook n' Heave(2), Darkrider(1), Stadium Announcer(4), Searing Fissure(2)

### Step 5: shared-tree-ismcts-v1

**P2 DISCOVER_PICK Cannonmaster[CAP_107]**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P2 DISCOVER_PICK Cannonmaster[CAP_107]; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "CAP_107", "destination": "hand", "entity": 65, "gifts": [], "kind": "discover_pick", "player": 1, "source": "CAP_105", "turn": 2}`

- P1: HP=30 Armor=0 Mana=0/1 Deck=27; Weapon=none; Board=Cannonmaster#29 3/1; Hand=Brood Keeper(2), Darkrider(1), Royal Librarian(4), Cannoneer(1)
- P2: HP=30 Armor=0 Mana=0/1 Deck=26; Weapon=none; Board=Cutlass Cutthroat#66 1/1, Cutlass Cutthroat#67 1/1; Hand=Hook n' Heave(2), Darkrider(1), Stadium Announcer(4), Searing Fissure(2), Cannonmaster(1)

### Step 6: shared-tree-ismcts-v1

**P2 ATTACK Cutlass Cutthroat#66 -> P1 Cannonmaster#29**

Legal actions: 3; Searched nodes: 5; Selected value: -0.0482

Top choices by root visit share:

- `0.500` — P2 ATTACK Cutlass Cutthroat#66 -> P1 Cannonmaster#29 [SELECTED]; Q=-0.0482; prior=0.0000
- `0.250` — P2 ATTACK Cutlass Cutthroat#67 -> P1 Cannonmaster#29; Q=-0.1503; prior=0.0000
- `0.250` — P2 END_TURN; Q=-0.2447; prior=0.0000

Resolved events:

- `{"card": "CAP_107", "entity": 29, "kind": "minion_died", "player": 0, "turn": 2}`
- `{"card": "CAP_105t", "entity": 66, "kind": "minion_died", "player": 1, "turn": 2}`

- P1: HP=30 Armor=0 Mana=0/1 Deck=27; Weapon=none; Board=empty; Hand=Brood Keeper(2), Darkrider(1), Royal Librarian(4), Cannoneer(1)
- P2: HP=30 Armor=0 Mana=0/1 Deck=26; Weapon=none; Board=Cutlass Cutthroat#67 1/1; Hand=Hook n' Heave(2), Darkrider(1), Stadium Announcer(4), Searing Fissure(2), Cannonmaster(1)

## Turn 3

### Step 7: shared-tree-ismcts-v1

**P2 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P2 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 1, "turn": 2}`
- `{"card": "CATA_556", "kind": "draw", "player": 0, "turn": 3}`
- `{"kind": "turn_start", "player": 0, "turn": 3}`

- P1: HP=30 Armor=0 Mana=2/2 Deck=26; Weapon=none; Board=empty; Hand=Brood Keeper(2), Darkrider(1), Royal Librarian(4), Cannoneer(1), Carrier Whelp(1)
- P2: HP=30 Armor=0 Mana=0/1 Deck=26; Weapon=none; Board=Cutlass Cutthroat#67 1/1; Hand=Hook n' Heave(2), Darkrider(1), Stadium Announcer(4), Searing Fissure(2), Cannonmaster(1)

### Step 8: policy-prior-puct-v1

**P1 PLAY Brood Keeper[EDR_457] -> -**

Legal actions: 6; Searched nodes: 13; Selected value: -0.0023

Top choices by root visit share:

- `0.333` — P1 PLAY Brood Keeper[EDR_457] -> - [SELECTED]; Q=-0.0023; prior=0.4802
- `0.250` — P1 PLAY Carrier Whelp[CATA_556] -> -; Q=0.0786; prior=0.2828
- `0.167` — P1 PLAY Cannoneer[CAP_107t] -> -; Q=-0.0014; prior=0.1177
- `0.083` — P1 PLAY Darkrider[EDR_456] -> -; Q=0.0861; prior=0.0634
- `0.083` — P1 HERO_POWER Armor Up; Q=-0.2279; prior=0.0346

Resolved events:

- `{"card": "EDR_457", "controller": 0, "created_by": null, "entity": 6, "kind": "play", "player": 0, "started_in_deck": true, "turn": 3}`
- `{"attack": 2, "card": "EDR_457t", "durability": 2, "kind": "equip_weapon", "player": 0, "turn": 3}`

- P1: HP=30 Armor=0 Mana=0/2 Deck=26; Weapon=Brood Keeper's Sword 2/2; Board=Brood Keeper#6 2/3; Hand=Darkrider(1), Royal Librarian(4), Cannoneer(1), Carrier Whelp(1)
- P2: HP=30 Armor=0 Mana=0/1 Deck=26; Weapon=none; Board=Cutlass Cutthroat#67 1/1; Hand=Hook n' Heave(2), Darkrider(1), Stadium Announcer(4), Searing Fissure(2), Cannonmaster(1)

### Step 9: policy-prior-puct-v1

**P1 HERO_ATTACK -> P2 hero**

Legal actions: 3; Searched nodes: 7; Selected value: 0.0551

Top choices by root visit share:

- `0.667` — P1 HERO_ATTACK -> P2 hero [SELECTED]; Q=0.0551; prior=0.7013
- `0.167` — P1 HERO_ATTACK -> P2 Cutlass Cutthroat#67; Q=-0.0314; prior=0.1719
- `0.167` — P1 END_TURN; Q=-0.0520; prior=0.1269

- P1: HP=30 Armor=0 Mana=0/2 Deck=26; Weapon=Brood Keeper's Sword 2/1; Board=Brood Keeper#6 2/3; Hand=Darkrider(1), Royal Librarian(4), Cannoneer(1), Carrier Whelp(1)
- P2: HP=28 Armor=0 Mana=0/1 Deck=26; Weapon=none; Board=Cutlass Cutthroat#67 1/1; Hand=Hook n' Heave(2), Darkrider(1), Stadium Announcer(4), Searing Fissure(2), Cannonmaster(1)

## Turn 4

### Step 10: policy-prior-puct-v1

**P1 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P1 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 0, "turn": 3}`
- `{"card": "CORE_SW_066", "kind": "draw", "player": 1, "turn": 4}`
- `{"kind": "turn_start", "player": 1, "turn": 4}`

- P1: HP=30 Armor=0 Mana=0/2 Deck=26; Weapon=Brood Keeper's Sword 2/1; Board=Brood Keeper#6 2/3; Hand=Darkrider(1), Royal Librarian(4), Cannoneer(1), Carrier Whelp(1)
- P2: HP=28 Armor=0 Mana=2/2 Deck=25; Weapon=none; Board=Cutlass Cutthroat#67 1/1; Hand=Hook n' Heave(2), Darkrider(1), Stadium Announcer(4), Searing Fissure(2), Cannonmaster(1), Royal Librarian(4)

### Step 11: shared-tree-ismcts-v1

**P2 ATTACK Cutlass Cutthroat#67 -> P1 hero**

Legal actions: 8; Searched nodes: 5; Selected value: 0.2018

Top choices by root visit share:

- `0.250` — P2 ATTACK Cutlass Cutthroat#67 -> P1 hero [SELECTED]; Q=0.2018; prior=0.0000
- `0.250` — P2 ATTACK Cutlass Cutthroat#67 -> P1 Brood Keeper#6; Q=0.0069; prior=0.0000
- `0.250` — P2 PLAY Cannonmaster[CAP_107] -> -; Q=0.0069; prior=0.0000
- `0.250` — P2 PLAY Hook n' Heave[CAP_105] -> -; Q=-0.1564; prior=0.0000
- `0.000` — P2 END_TURN; Q=0.0000; prior=0.0000

- P1: HP=29 Armor=0 Mana=0/2 Deck=26; Weapon=Brood Keeper's Sword 2/1; Board=Brood Keeper#6 2/3; Hand=Darkrider(1), Royal Librarian(4), Cannoneer(1), Carrier Whelp(1)
- P2: HP=28 Armor=0 Mana=2/2 Deck=25; Weapon=none; Board=Cutlass Cutthroat#67 1/1; Hand=Hook n' Heave(2), Darkrider(1), Stadium Announcer(4), Searing Fissure(2), Cannonmaster(1), Royal Librarian(4)

### Step 12: shared-tree-ismcts-v1

**P2 PLAY Cannonmaster[CAP_107] -> -**

Legal actions: 6; Searched nodes: 5; Selected value: 0.1864

Top choices by root visit share:

- `0.250` — P2 PLAY Cannonmaster[CAP_107] -> - [SELECTED]; Q=0.1864; prior=0.0000
- `0.250` — P2 PLAY Darkrider[EDR_456] -> -; Q=0.1659; prior=0.0000
- `0.250` — P2 PLAY Hook n' Heave[CAP_105] -> -; Q=-0.1002; prior=0.0000
- `0.250` — P2 PLAY Searing Fissure[CATA_582] -> -; Q=-0.2782; prior=0.0000
- `0.000` — P2 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "CAP_107", "controller": 1, "created_by": "CAP_105", "entity": 65, "kind": "play", "player": 1, "started_in_deck": false, "turn": 4}`
- `{"card": "CAP_107t", "entity": 68, "kind": "generated_to_hand", "player": 1, "source": "CAP_107", "turn": 4}`

- P1: HP=29 Armor=0 Mana=0/2 Deck=26; Weapon=Brood Keeper's Sword 2/1; Board=Brood Keeper#6 2/3; Hand=Darkrider(1), Royal Librarian(4), Cannoneer(1), Carrier Whelp(1)
- P2: HP=28 Armor=0 Mana=1/2 Deck=25; Weapon=none; Board=Cutlass Cutthroat#67 1/1, Cannonmaster#65 3/1; Hand=Hook n' Heave(2), Darkrider(1), Stadium Announcer(4), Searing Fissure(2), Royal Librarian(4), Cannoneer(1)

### Step 13: shared-tree-ismcts-v1

**P2 PLAY Darkrider[EDR_456] -> -**

Legal actions: 3; Searched nodes: 5; Selected value: 0.0706

Top choices by root visit share:

- `0.500` — P2 PLAY Darkrider[EDR_456] -> - [SELECTED]; Q=0.0706; prior=0.0000
- `0.250` — P2 PLAY Cannoneer[CAP_107t] -> -; Q=0.0991; prior=0.0000
- `0.250` — P2 END_TURN; Q=-0.0923; prior=0.0000

Resolved events:

- `{"card": "EDR_456", "controller": 1, "created_by": null, "entity": 33, "kind": "play", "player": 1, "started_in_deck": true, "turn": 4}`
- `{"kind": "discover_offer", "options": [{"card": "FIR_956", "entity": 69, "gifts": ["living_nightmare"]}, {"card": "TIME_714", "entity": 70, "gifts": ["well_rested"]}, {"card": "EDR_571", "entity": 71, "gifts": ["sweet_dreams"]}], "player": 1, "profile": "closed_pool", "turn": 4}`

- P1: HP=29 Armor=0 Mana=0/2 Deck=26; Weapon=Brood Keeper's Sword 2/1; Board=Brood Keeper#6 2/3; Hand=Darkrider(1), Royal Librarian(4), Cannoneer(1), Carrier Whelp(1)
- P2: HP=28 Armor=0 Mana=0/2 Deck=25; Weapon=none; Board=Cutlass Cutthroat#67 1/1, Cannonmaster#65 3/1, Darkrider#33 1/1; Hand=Hook n' Heave(2), Stadium Announcer(4), Searing Fissure(2), Royal Librarian(4), Cannoneer(1)

### Step 14: shared-tree-ismcts-v1

**P2 DISCOVER_PICK Chrono-Lord Epoch[TIME_714] + well_rested**

Legal actions: 3; Searched nodes: 5; Selected value: -0.0407

Top choices by root visit share:

- `0.500` — P2 DISCOVER_PICK Chrono-Lord Epoch[TIME_714] + well_rested [SELECTED]; Q=-0.0407; prior=0.0000
- `0.250` — P2 DISCOVER_PICK Dragon Turtle[FIR_956] + living_nightmare; Q=0.0109; prior=0.0000
- `0.250` — P2 DISCOVER_PICK Fae Trickster[EDR_571] + sweet_dreams; Q=-0.0091; prior=0.0000

Resolved events:

- `{"card": "TIME_714", "destination": "hand", "entity": 70, "gifts": ["well_rested"], "kind": "discover_pick", "player": 1, "source": "EDR_456", "turn": 4}`

- P1: HP=29 Armor=0 Mana=0/2 Deck=26; Weapon=Brood Keeper's Sword 2/1; Board=Brood Keeper#6 2/3; Hand=Darkrider(1), Royal Librarian(4), Cannoneer(1), Carrier Whelp(1)
- P2: HP=28 Armor=0 Mana=0/2 Deck=25; Weapon=none; Board=Cutlass Cutthroat#67 1/1, Cannonmaster#65 3/1, Darkrider#33 1/1; Hand=Hook n' Heave(2), Stadium Announcer(4), Searing Fissure(2), Royal Librarian(4), Cannoneer(1), Chrono-Lord Epoch(6)

## Turn 5

### Step 15: shared-tree-ismcts-v1

**P2 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P2 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 1, "turn": 4}`
- `{"card": "CAP_105", "kind": "draw", "player": 0, "turn": 5}`
- `{"kind": "turn_start", "player": 0, "turn": 5}`

- P1: HP=29 Armor=0 Mana=3/3 Deck=25; Weapon=Brood Keeper's Sword 2/1; Board=Brood Keeper#6 2/3; Hand=Darkrider(1), Royal Librarian(4), Cannoneer(1), Carrier Whelp(1), Hook n' Heave(2)
- P2: HP=28 Armor=0 Mana=0/2 Deck=25; Weapon=none; Board=Cutlass Cutthroat#67 1/1, Cannonmaster#65 3/1, Darkrider#33 1/1; Hand=Hook n' Heave(2), Stadium Announcer(4), Searing Fissure(2), Royal Librarian(4), Cannoneer(1), Chrono-Lord Epoch(6)

### Step 16: policy-prior-puct-v1

**P1 PLAY Hook n' Heave[CAP_105] -> -**

Legal actions: 14; Searched nodes: 17; Selected value: 0.3414

Top choices by root visit share:

- `0.188` — P1 PLAY Hook n' Heave[CAP_105] -> - [SELECTED]; Q=0.3414; prior=0.2800
- `0.062` — P1 ATTACK Brood Keeper#6 -> P2 Cutlass Cutthroat#67; Q=0.3265; prior=0.0199
- `0.062` — P1 HERO_ATTACK -> P2 Cannonmaster#65; Q=0.3265; prior=0.0147
- `0.062` — P1 ATTACK Brood Keeper#6 -> P2 hero; Q=0.3028; prior=0.0535
- `0.062` — P1 ATTACK Brood Keeper#6 -> P2 Darkrider#33; Q=0.2798; prior=0.0177

Resolved events:

- `{"card": "CAP_105", "controller": 0, "created_by": null, "entity": 28, "kind": "play", "player": 0, "started_in_deck": true, "turn": 5}`
- `{"kind": "discover_offer", "options": [{"card": "CAP_107", "entity": 72, "gifts": []}], "player": 0, "profile": "closed_pool", "turn": 5}`

- P1: HP=29 Armor=0 Mana=1/3 Deck=25; Weapon=Brood Keeper's Sword 2/1; Board=Brood Keeper#6 2/3; Hand=Darkrider(1), Royal Librarian(4), Cannoneer(1), Carrier Whelp(1)
- P2: HP=28 Armor=0 Mana=0/2 Deck=25; Weapon=none; Board=Cutlass Cutthroat#67 1/1, Cannonmaster#65 3/1, Darkrider#33 1/1; Hand=Hook n' Heave(2), Stadium Announcer(4), Searing Fissure(2), Royal Librarian(4), Cannoneer(1), Chrono-Lord Epoch(6)

### Step 17: policy-prior-puct-v1

**P1 DISCOVER_PICK Cannonmaster[CAP_107]**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P1 DISCOVER_PICK Cannonmaster[CAP_107]; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "CAP_107", "destination": "hand", "entity": 72, "gifts": [], "kind": "discover_pick", "player": 0, "source": "CAP_105", "turn": 5}`

- P1: HP=29 Armor=0 Mana=1/3 Deck=25; Weapon=Brood Keeper's Sword 2/1; Board=Brood Keeper#6 2/3, Cutlass Cutthroat#73 1/1, Cutlass Cutthroat#74 1/1; Hand=Darkrider(1), Royal Librarian(4), Cannoneer(1), Carrier Whelp(1), Cannonmaster(1)
- P2: HP=28 Armor=0 Mana=0/2 Deck=25; Weapon=none; Board=Cutlass Cutthroat#67 1/1, Cannonmaster#65 3/1, Darkrider#33 1/1; Hand=Hook n' Heave(2), Stadium Announcer(4), Searing Fissure(2), Royal Librarian(4), Cannoneer(1), Chrono-Lord Epoch(6)

### Step 18: policy-prior-puct-v1

**P1 HERO_ATTACK -> P2 Darkrider#33**

Legal actions: 19; Searched nodes: 17; Selected value: 0.5614

Top choices by root visit share:

- `0.062` — P1 HERO_ATTACK -> P2 Darkrider#33 [SELECTED]; Q=0.5614; prior=0.0230
- `0.062` — P1 ATTACK Cutlass Cutthroat#73 -> P2 Cannonmaster#65; Q=0.5614; prior=0.0172
- `0.062` — P1 ATTACK Cutlass Cutthroat#74 -> P2 Cannonmaster#65; Q=0.5614; prior=0.0165
- `0.062` — P1 HERO_ATTACK -> P2 Cutlass Cutthroat#67; Q=0.5614; prior=0.0236
- `0.062` — P1 ATTACK Brood Keeper#6 -> P2 Darkrider#33; Q=0.4781; prior=0.0181

Resolved events:

- `{"card": "EDR_457t", "kind": "weapon_destroyed", "player": 0, "turn": 5}`
- `{"card": "EDR_456", "entity": 33, "kind": "minion_died", "player": 1, "turn": 5}`

- P1: HP=28 Armor=0 Mana=1/3 Deck=25; Weapon=none; Board=Brood Keeper#6 2/3, Cutlass Cutthroat#73 1/1, Cutlass Cutthroat#74 1/1; Hand=Darkrider(1), Royal Librarian(4), Cannoneer(1), Carrier Whelp(1), Cannonmaster(1)
- P2: HP=28 Armor=0 Mana=0/2 Deck=25; Weapon=none; Board=Cutlass Cutthroat#67 1/1, Cannonmaster#65 3/1; Hand=Hook n' Heave(2), Stadium Announcer(4), Searing Fissure(2), Royal Librarian(4), Cannoneer(1), Chrono-Lord Epoch(6)

### Step 19: policy-prior-puct-v1

**P1 PLAY Carrier Whelp[CATA_556] -> -**

Legal actions: 12; Searched nodes: 17; Selected value: 0.3017

Top choices by root visit share:

- `0.188` — P1 PLAY Carrier Whelp[CATA_556] -> - [SELECTED]; Q=0.3017; prior=0.2341
- `0.125` — P1 PLAY Cannonmaster[CAP_107] -> -; Q=0.5382; prior=0.1737
- `0.125` — P1 PLAY Cannoneer[CAP_107t] -> -; Q=0.4847; prior=0.1429
- `0.062` — P1 ATTACK Brood Keeper#6 -> P2 Cutlass Cutthroat#67; Q=0.5475; prior=0.0364
- `0.062` — P1 ATTACK Cutlass Cutthroat#73 -> P2 Cannonmaster#65; Q=0.5475; prior=0.0313

Resolved events:

- `{"card": "CATA_556", "controller": 0, "created_by": null, "entity": 17, "kind": "play", "player": 0, "started_in_deck": true, "turn": 5}`
- `{"card": "CATA_556", "entity": 75, "kind": "generated_to_hand", "player": 0, "source": "CATA_556", "turn": 5}`

- P1: HP=28 Armor=0 Mana=0/3 Deck=25; Weapon=none; Board=Brood Keeper#6 2/3, Cutlass Cutthroat#73 1/1, Cutlass Cutthroat#74 1/1, Carrier Whelp#17 1/2; Hand=Darkrider(1), Royal Librarian(4), Cannoneer(1), Cannonmaster(1), Carrier Whelp(1)
- P2: HP=28 Armor=0 Mana=0/2 Deck=25; Weapon=none; Board=Cutlass Cutthroat#67 1/1, Cannonmaster#65 3/1; Hand=Hook n' Heave(2), Stadium Announcer(4), Searing Fissure(2), Royal Librarian(4), Cannoneer(1), Chrono-Lord Epoch(6)

### Step 20: policy-prior-puct-v1

**P1 ATTACK Brood Keeper#6 -> P2 hero**

Legal actions: 8; Searched nodes: 17; Selected value: 0.2902

Top choices by root visit share:

- `0.375` — P1 ATTACK Brood Keeper#6 -> P2 hero [SELECTED]; Q=0.2902; prior=0.4138
- `0.188` — P1 ATTACK Cutlass Cutthroat#73 -> P2 Cutlass Cutthroat#67; Q=0.3411; prior=0.0825
- `0.125` — P1 ATTACK Cutlass Cutthroat#74 -> P2 Cutlass Cutthroat#67; Q=0.3596; prior=0.0801
- `0.062` — P1 ATTACK Brood Keeper#6 -> P2 Cutlass Cutthroat#67; Q=0.3028; prior=0.0994
- `0.062` — P1 ATTACK Cutlass Cutthroat#74 -> P2 Cannonmaster#65; Q=0.3028; prior=0.0731

- P1: HP=28 Armor=0 Mana=0/3 Deck=25; Weapon=none; Board=Brood Keeper#6 2/3, Cutlass Cutthroat#73 1/1, Cutlass Cutthroat#74 1/1, Carrier Whelp#17 1/2; Hand=Darkrider(1), Royal Librarian(4), Cannoneer(1), Cannonmaster(1), Carrier Whelp(1)
- P2: HP=26 Armor=0 Mana=0/2 Deck=25; Weapon=none; Board=Cutlass Cutthroat#67 1/1, Cannonmaster#65 3/1; Hand=Hook n' Heave(2), Stadium Announcer(4), Searing Fissure(2), Royal Librarian(4), Cannoneer(1), Chrono-Lord Epoch(6)

### Step 21: policy-prior-puct-v1

**P1 ATTACK Cutlass Cutthroat#73 -> P2 Cannonmaster#65**

Legal actions: 5; Searched nodes: 11; Selected value: 0.4229

Top choices by root visit share:

- `0.300` — P1 ATTACK Cutlass Cutthroat#73 -> P2 Cannonmaster#65 [SELECTED]; Q=0.4229; prior=0.1786
- `0.300` — P1 ATTACK Cutlass Cutthroat#73 -> P2 Cutlass Cutthroat#67; Q=0.3777; prior=0.1915
- `0.200` — P1 ATTACK Cutlass Cutthroat#74 -> P2 Cutlass Cutthroat#67; Q=0.2846; prior=0.1856
- `0.100` — P1 ATTACK Cutlass Cutthroat#74 -> P2 Cannonmaster#65; Q=0.1592; prior=0.1687
- `0.100` — P1 END_TURN; Q=0.0542; prior=0.2757

Resolved events:

- `{"card": "CAP_105t", "entity": 73, "kind": "minion_died", "player": 0, "turn": 5}`
- `{"card": "CAP_107", "entity": 65, "kind": "minion_died", "player": 1, "turn": 5}`

- P1: HP=28 Armor=0 Mana=0/3 Deck=25; Weapon=none; Board=Brood Keeper#6 2/3, Cutlass Cutthroat#74 1/1, Carrier Whelp#17 1/2; Hand=Darkrider(1), Royal Librarian(4), Cannoneer(1), Cannonmaster(1), Carrier Whelp(1)
- P2: HP=26 Armor=0 Mana=0/2 Deck=25; Weapon=none; Board=Cutlass Cutthroat#67 1/1; Hand=Hook n' Heave(2), Stadium Announcer(4), Searing Fissure(2), Royal Librarian(4), Cannoneer(1), Chrono-Lord Epoch(6)

### Step 22: policy-prior-puct-v1

**P1 ATTACK Cutlass Cutthroat#74 -> P2 Cutlass Cutthroat#67**

Legal actions: 2; Searched nodes: 5; Selected value: 0.2712

Top choices by root visit share:

- `0.500` — P1 ATTACK Cutlass Cutthroat#74 -> P2 Cutlass Cutthroat#67 [SELECTED]; Q=0.2712; prior=0.3450
- `0.500` — P1 END_TURN; Q=0.1453; prior=0.6550

Resolved events:

- `{"card": "CAP_105t", "entity": 74, "kind": "minion_died", "player": 0, "turn": 5}`
- `{"card": "CAP_105t", "entity": 67, "kind": "minion_died", "player": 1, "turn": 5}`

- P1: HP=28 Armor=0 Mana=0/3 Deck=25; Weapon=none; Board=Brood Keeper#6 2/3, Carrier Whelp#17 1/2; Hand=Darkrider(1), Royal Librarian(4), Cannoneer(1), Cannonmaster(1), Carrier Whelp(1)
- P2: HP=26 Armor=0 Mana=0/2 Deck=25; Weapon=none; Board=empty; Hand=Hook n' Heave(2), Stadium Announcer(4), Searing Fissure(2), Royal Librarian(4), Cannoneer(1), Chrono-Lord Epoch(6)

## Turn 6

### Step 23: policy-prior-puct-v1

**P1 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P1 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 0, "turn": 5}`
- `{"card": "CATA_584", "kind": "draw", "player": 1, "turn": 6}`
- `{"kind": "turn_start", "player": 1, "turn": 6}`

- P1: HP=28 Armor=0 Mana=0/3 Deck=25; Weapon=none; Board=Brood Keeper#6 2/3, Carrier Whelp#17 1/2; Hand=Darkrider(1), Royal Librarian(4), Cannoneer(1), Cannonmaster(1), Carrier Whelp(1)
- P2: HP=26 Armor=0 Mana=3/3 Deck=24; Weapon=none; Board=empty; Hand=Hook n' Heave(2), Stadium Announcer(4), Searing Fissure(2), Royal Librarian(4), Cannoneer(1), Chrono-Lord Epoch(6), Erupting Volcano(3)

### Step 24: shared-tree-ismcts-v1

**P2 PLAY Searing Fissure[CATA_582] -> -**

Legal actions: 6; Searched nodes: 5; Selected value: -0.1245

Top choices by root visit share:

- `0.250` — P2 PLAY Searing Fissure[CATA_582] -> - [SELECTED]; Q=-0.1245; prior=0.0000
- `0.250` — P2 PLAY Cannoneer[CAP_107t] -> -; Q=-0.1979; prior=0.0000
- `0.250` — P2 PLAY Hook n' Heave[CAP_105] -> -; Q=-0.4174; prior=0.0000
- `0.250` — P2 PLAY Erupting Volcano[CATA_584] -> -; Q=-0.6197; prior=0.0000
- `0.000` — P2 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "CATA_582", "controller": 1, "created_by": null, "entity": 49, "kind": "play", "player": 1, "started_in_deck": true, "turn": 6}`

- P1: HP=28 Armor=0 Mana=0/3 Deck=25; Weapon=none; Board=Brood Keeper#6 2/2, Carrier Whelp#17 1/1; Hand=Darkrider(1), Royal Librarian(4), Cannoneer(1), Cannonmaster(1), Carrier Whelp(1)
- P2: HP=26 Armor=0 Mana=1/3 Deck=24; Weapon=none; Board=empty; Hand=Hook n' Heave(2), Stadium Announcer(4), Royal Librarian(4), Cannoneer(1), Chrono-Lord Epoch(6), Erupting Volcano(3)

### Step 25: shared-tree-ismcts-v1

**P2 HERO_ATTACK -> P1 hero**

Legal actions: 5; Searched nodes: 5; Selected value: -0.1737

Top choices by root visit share:

- `0.250` — P2 HERO_ATTACK -> P1 hero [SELECTED]; Q=-0.1737; prior=0.0000
- `0.250` — P2 HERO_ATTACK -> P1 Carrier Whelp#17; Q=-0.1891; prior=0.0000
- `0.250` — P2 HERO_ATTACK -> P1 Brood Keeper#6; Q=-0.4697; prior=0.0000
- `0.250` — P2 PLAY Cannoneer[CAP_107t] -> -; Q=-0.5362; prior=0.0000
- `0.000` — P2 END_TURN; Q=0.0000; prior=0.0000

- P1: HP=25 Armor=0 Mana=0/3 Deck=25; Weapon=none; Board=Brood Keeper#6 2/2, Carrier Whelp#17 1/1; Hand=Darkrider(1), Royal Librarian(4), Cannoneer(1), Cannonmaster(1), Carrier Whelp(1)
- P2: HP=26 Armor=0 Mana=1/3 Deck=24; Weapon=none; Board=empty; Hand=Hook n' Heave(2), Stadium Announcer(4), Royal Librarian(4), Cannoneer(1), Chrono-Lord Epoch(6), Erupting Volcano(3)

### Step 26: shared-tree-ismcts-v1

**P2 PLAY Cannoneer[CAP_107t] -> -**

Legal actions: 2; Searched nodes: 5; Selected value: -0.5852

Top choices by root visit share:

- `0.750` — P2 PLAY Cannoneer[CAP_107t] -> - [SELECTED]; Q=-0.5852; prior=0.0000
- `0.250` — P2 END_TURN; Q=-0.8492; prior=0.0000

Resolved events:

- `{"card": "CAP_107t", "controller": 1, "created_by": "CAP_107", "entity": 68, "kind": "play", "player": 1, "started_in_deck": false, "turn": 6}`

- P1: HP=25 Armor=0 Mana=0/3 Deck=25; Weapon=none; Board=Brood Keeper#6 2/2, Carrier Whelp#17 1/1; Hand=Darkrider(1), Royal Librarian(4), Cannoneer(1), Cannonmaster(1), Carrier Whelp(1)
- P2: HP=26 Armor=0 Mana=0/3 Deck=24; Weapon=none; Board=Cannoneer#68 1/1; Hand=Hook n' Heave(2), Stadium Announcer(4), Royal Librarian(4), Chrono-Lord Epoch(6), Erupting Volcano(3)

## Turn 7

### Step 27: shared-tree-ismcts-v1

**P2 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P2 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 1, "turn": 6}`
- `{"card": "EDR_492", "kind": "draw", "player": 0, "turn": 7}`
- `{"kind": "turn_start", "player": 0, "turn": 7}`

- P1: HP=25 Armor=0 Mana=4/4 Deck=24; Weapon=none; Board=Brood Keeper#6 2/1, Carrier Whelp#17 1/1; Hand=Darkrider(1), Royal Librarian(4), Cannoneer(1), Cannonmaster(1), Carrier Whelp(1), Mother Duck(4)
- P2: HP=26 Armor=0 Mana=0/3 Deck=24; Weapon=none; Board=Cannoneer#68 1/1; Hand=Hook n' Heave(2), Stadium Announcer(4), Royal Librarian(4), Chrono-Lord Epoch(6), Erupting Volcano(3)

### Step 28: policy-prior-puct-v1

**P1 PLAY Mother Duck[EDR_492] -> -**

Legal actions: 15; Searched nodes: 17; Selected value: 0.8143

Top choices by root visit share:

- `0.125` — P1 PLAY Mother Duck[EDR_492] -> - [SELECTED]; Q=0.8143; prior=0.2902
- `0.062` — P1 ATTACK Brood Keeper#6 -> P2 hero; Q=0.8090; prior=0.0709
- `0.062` — P1 ATTACK Carrier Whelp#17 -> P2 Cannoneer#68; Q=0.8090; prior=0.0212
- `0.062` — P1 ATTACK Brood Keeper#6 -> P2 Cannoneer#68; Q=0.7521; prior=0.0194
- `0.062` — P1 ATTACK Carrier Whelp#17 -> P2 hero; Q=0.7521; prior=0.0623

Resolved events:

- `{"card": "EDR_492", "controller": 0, "created_by": null, "entity": 7, "kind": "play", "player": 0, "started_in_deck": true, "turn": 7}`

- P1: HP=25 Armor=0 Mana=0/4 Deck=24; Weapon=none; Board=Brood Keeper#6 2/1, Carrier Whelp#17 1/1, Mother Duck#7 2/3, Duckling#76 1/1, Duckling#77 1/1, Duckling#78 1/1; Hand=Darkrider(1), Royal Librarian(4), Cannoneer(1), Cannonmaster(1), Carrier Whelp(1)
- P2: HP=26 Armor=0 Mana=0/3 Deck=24; Weapon=none; Board=Cannoneer#68 1/1; Hand=Hook n' Heave(2), Stadium Announcer(4), Royal Librarian(4), Chrono-Lord Epoch(6), Erupting Volcano(3)

### Step 29: policy-prior-puct-v1

**P1 ATTACK Carrier Whelp#17 -> P2 hero**

Legal actions: 8; Searched nodes: 17; Selected value: 0.6372

Top choices by root visit share:

- `0.250` — P1 ATTACK Carrier Whelp#17 -> P2 hero [SELECTED]; Q=0.6372; prior=0.2830
- `0.188` — P1 ATTACK Brood Keeper#6 -> P2 hero; Q=0.6194; prior=0.2763
- `0.125` — P1 ATTACK Duckling#77 -> P2 Cannoneer#68; Q=0.7677; prior=0.0657
- `0.125` — P1 ATTACK Duckling#78 -> P2 Cannoneer#68; Q=0.7677; prior=0.0791
- `0.125` — P1 ATTACK Carrier Whelp#17 -> P2 Cannoneer#68; Q=0.6709; prior=0.0757

- P1: HP=25 Armor=0 Mana=0/4 Deck=24; Weapon=none; Board=Brood Keeper#6 2/1, Carrier Whelp#17 1/1, Mother Duck#7 2/3, Duckling#76 1/1, Duckling#77 1/1, Duckling#78 1/1; Hand=Darkrider(1), Royal Librarian(4), Cannoneer(1), Cannonmaster(1), Carrier Whelp(1)
- P2: HP=25 Armor=0 Mana=0/3 Deck=24; Weapon=none; Board=Cannoneer#68 1/1; Hand=Hook n' Heave(2), Stadium Announcer(4), Royal Librarian(4), Chrono-Lord Epoch(6), Erupting Volcano(3)

### Step 30: policy-prior-puct-v1

**P1 ATTACK Brood Keeper#6 -> P2 hero**

Legal actions: 6; Searched nodes: 13; Selected value: 0.5734

Top choices by root visit share:

- `0.333` — P1 ATTACK Brood Keeper#6 -> P2 hero [SELECTED]; Q=0.5734; prior=0.3852
- `0.250` — P1 ATTACK Duckling#77 -> P2 Cannoneer#68; Q=0.5710; prior=0.1130
- `0.167` — P1 ATTACK Duckling#78 -> P2 Cannoneer#68; Q=0.4789; prior=0.1313
- `0.083` — P1 ATTACK Duckling#76 -> P2 Cannoneer#68; Q=0.7245; prior=0.1048
- `0.083` — P1 END_TURN; Q=0.5519; prior=0.1520

- P1: HP=25 Armor=0 Mana=0/4 Deck=24; Weapon=none; Board=Brood Keeper#6 2/1, Carrier Whelp#17 1/1, Mother Duck#7 2/3, Duckling#76 1/1, Duckling#77 1/1, Duckling#78 1/1; Hand=Darkrider(1), Royal Librarian(4), Cannoneer(1), Cannonmaster(1), Carrier Whelp(1)
- P2: HP=23 Armor=0 Mana=0/3 Deck=24; Weapon=none; Board=Cannoneer#68 1/1; Hand=Hook n' Heave(2), Stadium Announcer(4), Royal Librarian(4), Chrono-Lord Epoch(6), Erupting Volcano(3)

### Step 31: policy-prior-puct-v1

**P1 ATTACK Duckling#77 -> P2 Cannoneer#68**

Legal actions: 4; Searched nodes: 9; Selected value: 0.6678

Top choices by root visit share:

- `0.250` — P1 ATTACK Duckling#77 -> P2 Cannoneer#68 [SELECTED]; Q=0.6678; prior=0.2319
- `0.250` — P1 END_TURN; Q=0.5190; prior=0.2948
- `0.250` — P1 ATTACK Duckling#78 -> P2 Cannoneer#68; Q=0.4881; prior=0.2581
- `0.250` — P1 ATTACK Duckling#76 -> P2 Cannoneer#68; Q=0.4483; prior=0.2152

Resolved events:

- `{"card": "EDR_492t", "entity": 77, "kind": "minion_died", "player": 0, "turn": 7}`
- `{"card": "CAP_107t", "entity": 68, "kind": "minion_died", "player": 1, "turn": 7}`

- P1: HP=25 Armor=0 Mana=0/4 Deck=24; Weapon=none; Board=Brood Keeper#6 2/1, Carrier Whelp#17 1/1, Mother Duck#7 2/3, Duckling#76 1/1, Duckling#78 1/1; Hand=Darkrider(1), Royal Librarian(4), Cannoneer(1), Cannonmaster(1), Carrier Whelp(1)
- P2: HP=23 Armor=0 Mana=0/3 Deck=24; Weapon=none; Board=empty; Hand=Hook n' Heave(2), Stadium Announcer(4), Royal Librarian(4), Chrono-Lord Epoch(6), Erupting Volcano(3)

## Turn 8

### Step 32: policy-prior-puct-v1

**P1 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P1 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 0, "turn": 7}`
- `{"card": "END_033", "kind": "draw", "player": 1, "turn": 8}`
- `{"kind": "turn_start", "player": 1, "turn": 8}`

- P1: HP=25 Armor=0 Mana=0/4 Deck=24; Weapon=none; Board=Brood Keeper#6 2/1, Carrier Whelp#17 1/1, Mother Duck#7 2/3, Duckling#76 1/1, Duckling#78 1/1; Hand=Darkrider(1), Royal Librarian(4), Cannoneer(1), Cannonmaster(1), Carrier Whelp(1)
- P2: HP=23 Armor=0 Mana=4/4 Deck=23; Weapon=none; Board=empty; Hand=Hook n' Heave(2), Stadium Announcer(4), Royal Librarian(4), Chrono-Lord Epoch(6), Erupting Volcano(3), Prescient Slitherdrake(4)

### Step 33: shared-tree-ismcts-v1

**P2 PLAY Royal Librarian[CORE_SW_066] -> P1 Duckling#76**

Legal actions: 12; Searched nodes: 5; Selected value: -0.3755

Top choices by root visit share:

- `0.250` — P2 PLAY Royal Librarian[CORE_SW_066] -> P1 Duckling#76 [SELECTED]; Q=-0.3755; prior=0.0000
- `0.250` — P2 PLAY Royal Librarian[CORE_SW_066] -> P1 Brood Keeper#6; Q=-0.3755; prior=0.0000
- `0.250` — P2 PLAY Royal Librarian[CORE_SW_066] -> P1 Mother Duck#7; Q=-0.3755; prior=0.0000
- `0.250` — P2 PLAY Royal Librarian[CORE_SW_066] -> P1 Carrier Whelp#17; Q=-0.3755; prior=0.0000
- `0.000` — P2 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "CORE_SW_066", "controller": 1, "created_by": null, "entity": 31, "kind": "play", "player": 1, "started_in_deck": true, "turn": 8}`

- P1: HP=25 Armor=0 Mana=0/4 Deck=24; Weapon=none; Board=Brood Keeper#6 2/1, Carrier Whelp#17 1/1, Mother Duck#7 2/3, Duckling#76 1/1, Duckling#78 1/1; Hand=Darkrider(1), Royal Librarian(4), Cannoneer(1), Cannonmaster(1), Carrier Whelp(1)
- P2: HP=23 Armor=0 Mana=0/4 Deck=23; Weapon=none; Board=Royal Librarian#31 4/4; Hand=Hook n' Heave(2), Stadium Announcer(4), Chrono-Lord Epoch(6), Erupting Volcano(3), Prescient Slitherdrake(4)

## Turn 9

### Step 34: shared-tree-ismcts-v1

**P2 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P2 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 1, "turn": 8}`
- `{"card": "FIR_939", "kind": "draw", "player": 0, "turn": 9}`
- `{"kind": "turn_start", "player": 0, "turn": 9}`

- P1: HP=25 Armor=0 Mana=5/5 Deck=23; Weapon=none; Board=Brood Keeper#6 2/1, Carrier Whelp#17 1/1, Mother Duck#7 2/3, Duckling#76 1/1, Duckling#78 1/1; Hand=Darkrider(1), Royal Librarian(4), Cannoneer(1), Cannonmaster(1), Carrier Whelp(1), Shadowflame Suffusion(2)
- P2: HP=23 Armor=0 Mana=0/4 Deck=23; Weapon=none; Board=Royal Librarian#31 4/4; Hand=Hook n' Heave(2), Stadium Announcer(4), Chrono-Lord Epoch(6), Erupting Volcano(3), Prescient Slitherdrake(4)

### Step 35: policy-prior-puct-v1

**P1 PLAY Royal Librarian[CORE_SW_066] -> P2 Royal Librarian#31**

Legal actions: 31; Searched nodes: 17; Selected value: 0.7936

Top choices by root visit share:

- `0.062` — P1 PLAY Royal Librarian[CORE_SW_066] -> P2 Royal Librarian#31 [SELECTED]; Q=0.7936; prior=0.0567
- `0.062` — P1 PLAY Royal Librarian[CORE_SW_066] -> P1 Brood Keeper#6; Q=0.7936; prior=0.0611
- `0.062` — P1 PLAY Royal Librarian[CORE_SW_066] -> P1 Mother Duck#7; Q=0.7936; prior=0.0873
- `0.062` — P1 PLAY Royal Librarian[CORE_SW_066] -> P1 Carrier Whelp#17; Q=0.7936; prior=0.0501
- `0.062` — P1 PLAY Royal Librarian[CORE_SW_066] -> P1 Duckling#76; Q=0.7936; prior=0.0350

Resolved events:

- `{"card": "CORE_SW_066", "controller": 0, "created_by": null, "entity": 1, "kind": "play", "player": 0, "started_in_deck": true, "turn": 9}`

- P1: HP=25 Armor=0 Mana=1/5 Deck=23; Weapon=none; Board=Brood Keeper#6 2/1, Carrier Whelp#17 1/1, Mother Duck#7 2/3, Duckling#76 1/1, Duckling#78 1/1, Royal Librarian#1 4/4; Hand=Darkrider(1), Cannoneer(1), Cannonmaster(1), Carrier Whelp(1), Shadowflame Suffusion(2)
- P2: HP=23 Armor=0 Mana=0/4 Deck=23; Weapon=none; Board=Royal Librarian#31 4/4; Hand=Hook n' Heave(2), Stadium Announcer(4), Chrono-Lord Epoch(6), Erupting Volcano(3), Prescient Slitherdrake(4)

### Step 36: policy-prior-puct-v1

**P1 PLAY Cannonmaster[CAP_107] -> -**

Legal actions: 15; Searched nodes: 17; Selected value: 0.8722

Top choices by root visit share:

- `0.125` — P1 PLAY Cannonmaster[CAP_107] -> - [SELECTED]; Q=0.8722; prior=0.1366
- `0.062` — P1 PLAY Carrier Whelp[CATA_556] -> -; Q=0.8451; prior=0.1161
- `0.062` — P1 ATTACK Mother Duck#7 -> P2 hero; Q=0.8323; prior=0.0540
- `0.062` — P1 ATTACK Carrier Whelp#17 -> P2 Royal Librarian#31; Q=0.8323; prior=0.0347
- `0.062` — P1 ATTACK Duckling#76 -> P2 Royal Librarian#31; Q=0.8323; prior=0.0398

Resolved events:

- `{"card": "CAP_107", "controller": 0, "created_by": "CAP_105", "entity": 72, "kind": "play", "player": 0, "started_in_deck": false, "turn": 9}`
- `{"card": "CAP_107t", "entity": 79, "kind": "generated_to_hand", "player": 0, "source": "CAP_107", "turn": 9}`

- P1: HP=25 Armor=0 Mana=0/5 Deck=23; Weapon=none; Board=Brood Keeper#6 2/1, Carrier Whelp#17 1/1, Mother Duck#7 2/3, Duckling#76 1/1, Duckling#78 1/1, Royal Librarian#1 4/4, Cannonmaster#72 3/1; Hand=Darkrider(1), Cannoneer(1), Carrier Whelp(1), Shadowflame Suffusion(2), Cannoneer(1)
- P2: HP=23 Armor=0 Mana=0/4 Deck=23; Weapon=none; Board=Royal Librarian#31 4/4; Hand=Hook n' Heave(2), Stadium Announcer(4), Chrono-Lord Epoch(6), Erupting Volcano(3), Prescient Slitherdrake(4)

### Step 37: policy-prior-puct-v1

**P1 ATTACK Duckling#78 -> P2 hero**

Legal actions: 11; Searched nodes: 17; Selected value: 0.8750

Top choices by root visit share:

- `0.188` — P1 ATTACK Duckling#78 -> P2 hero [SELECTED]; Q=0.8750; prior=0.1774
- `0.188` — P1 ATTACK Duckling#76 -> P2 hero; Q=0.8674; prior=0.1899
- `0.125` — P1 ATTACK Mother Duck#7 -> P2 hero; Q=0.8970; prior=0.1113
- `0.062` — P1 ATTACK Carrier Whelp#17 -> P2 Royal Librarian#31; Q=0.8914; prior=0.0488
- `0.062` — P1 ATTACK Duckling#76 -> P2 Royal Librarian#31; Q=0.8914; prior=0.0511

- P1: HP=25 Armor=0 Mana=0/5 Deck=23; Weapon=none; Board=Brood Keeper#6 2/1, Carrier Whelp#17 1/1, Mother Duck#7 2/3, Duckling#76 1/1, Duckling#78 1/1, Royal Librarian#1 4/4, Cannonmaster#72 3/1; Hand=Darkrider(1), Cannoneer(1), Carrier Whelp(1), Shadowflame Suffusion(2), Cannoneer(1)
- P2: HP=22 Armor=0 Mana=0/4 Deck=23; Weapon=none; Board=Royal Librarian#31 4/4; Hand=Hook n' Heave(2), Stadium Announcer(4), Chrono-Lord Epoch(6), Erupting Volcano(3), Prescient Slitherdrake(4)

### Step 38: policy-prior-puct-v1

**P1 ATTACK Duckling#76 -> P2 hero**

Legal actions: 9; Searched nodes: 17; Selected value: 0.8563

Top choices by root visit share:

- `0.250` — P1 ATTACK Duckling#76 -> P2 hero [SELECTED]; Q=0.8563; prior=0.2537
- `0.188` — P1 ATTACK Mother Duck#7 -> P2 hero; Q=0.8882; prior=0.1475
- `0.125` — P1 ATTACK Carrier Whelp#17 -> P2 hero; Q=0.8689; prior=0.1356
- `0.125` — P1 ATTACK Brood Keeper#6 -> P2 hero; Q=0.8548; prior=0.1653
- `0.062` — P1 ATTACK Carrier Whelp#17 -> P2 Royal Librarian#31; Q=0.9116; prior=0.0623

- P1: HP=25 Armor=0 Mana=0/5 Deck=23; Weapon=none; Board=Brood Keeper#6 2/1, Carrier Whelp#17 1/1, Mother Duck#7 2/3, Duckling#76 1/1, Duckling#78 1/1, Royal Librarian#1 4/4, Cannonmaster#72 3/1; Hand=Darkrider(1), Cannoneer(1), Carrier Whelp(1), Shadowflame Suffusion(2), Cannoneer(1)
- P2: HP=21 Armor=0 Mana=0/4 Deck=23; Weapon=none; Board=Royal Librarian#31 4/4; Hand=Hook n' Heave(2), Stadium Announcer(4), Chrono-Lord Epoch(6), Erupting Volcano(3), Prescient Slitherdrake(4)

### Step 39: policy-prior-puct-v1

**P1 ATTACK Brood Keeper#6 -> P2 hero**

Legal actions: 7; Searched nodes: 15; Selected value: 0.8426

Top choices by root visit share:

- `0.286` — P1 ATTACK Brood Keeper#6 -> P2 hero [SELECTED]; Q=0.8426; prior=0.2505
- `0.214` — P1 ATTACK Mother Duck#7 -> P2 hero; Q=0.8853; prior=0.2157
- `0.214` — P1 ATTACK Carrier Whelp#17 -> P2 hero; Q=0.8726; prior=0.2010
- `0.071` — P1 ATTACK Brood Keeper#6 -> P2 Royal Librarian#31; Q=0.8884; prior=0.0942
- `0.071` — P1 ATTACK Mother Duck#7 -> P2 Royal Librarian#31; Q=0.8884; prior=0.0812

- P1: HP=25 Armor=0 Mana=0/5 Deck=23; Weapon=none; Board=Brood Keeper#6 2/1, Carrier Whelp#17 1/1, Mother Duck#7 2/3, Duckling#76 1/1, Duckling#78 1/1, Royal Librarian#1 4/4, Cannonmaster#72 3/1; Hand=Darkrider(1), Cannoneer(1), Carrier Whelp(1), Shadowflame Suffusion(2), Cannoneer(1)
- P2: HP=19 Armor=0 Mana=0/4 Deck=23; Weapon=none; Board=Royal Librarian#31 4/4; Hand=Hook n' Heave(2), Stadium Announcer(4), Chrono-Lord Epoch(6), Erupting Volcano(3), Prescient Slitherdrake(4)

### Step 40: policy-prior-puct-v1

**P1 ATTACK Mother Duck#7 -> P2 hero**

Legal actions: 5; Searched nodes: 11; Selected value: 0.8518

Top choices by root visit share:

- `0.400` — P1 ATTACK Mother Duck#7 -> P2 hero [SELECTED]; Q=0.8518; prior=0.3305
- `0.300` — P1 ATTACK Carrier Whelp#17 -> P2 hero; Q=0.8306; prior=0.3185
- `0.100` — P1 ATTACK Mother Duck#7 -> P2 Royal Librarian#31; Q=0.7883; prior=0.1200
- `0.100` — P1 ATTACK Carrier Whelp#17 -> P2 Royal Librarian#31; Q=0.7883; prior=0.1405
- `0.100` — P1 END_TURN; Q=0.5467; prior=0.0904

- P1: HP=25 Armor=0 Mana=0/5 Deck=23; Weapon=none; Board=Brood Keeper#6 2/1, Carrier Whelp#17 1/1, Mother Duck#7 2/3, Duckling#76 1/1, Duckling#78 1/1, Royal Librarian#1 4/4, Cannonmaster#72 3/1; Hand=Darkrider(1), Cannoneer(1), Carrier Whelp(1), Shadowflame Suffusion(2), Cannoneer(1)
- P2: HP=17 Armor=0 Mana=0/4 Deck=23; Weapon=none; Board=Royal Librarian#31 4/4; Hand=Hook n' Heave(2), Stadium Announcer(4), Chrono-Lord Epoch(6), Erupting Volcano(3), Prescient Slitherdrake(4)

### Step 41: policy-prior-puct-v1

**P1 ATTACK Carrier Whelp#17 -> P2 hero**

Legal actions: 3; Searched nodes: 7; Selected value: 0.7325

Top choices by root visit share:

- `0.500` — P1 ATTACK Carrier Whelp#17 -> P2 hero [SELECTED]; Q=0.7325; prior=0.5588
- `0.333` — P1 ATTACK Carrier Whelp#17 -> P2 Royal Librarian#31; Q=0.8343; prior=0.2996
- `0.167` — P1 END_TURN; Q=0.7568; prior=0.1416

- P1: HP=25 Armor=0 Mana=0/5 Deck=23; Weapon=none; Board=Brood Keeper#6 2/1, Carrier Whelp#17 1/1, Mother Duck#7 2/3, Duckling#76 1/1, Duckling#78 1/1, Royal Librarian#1 4/4, Cannonmaster#72 3/1; Hand=Darkrider(1), Cannoneer(1), Carrier Whelp(1), Shadowflame Suffusion(2), Cannoneer(1)
- P2: HP=16 Armor=0 Mana=0/4 Deck=23; Weapon=none; Board=Royal Librarian#31 4/4; Hand=Hook n' Heave(2), Stadium Announcer(4), Chrono-Lord Epoch(6), Erupting Volcano(3), Prescient Slitherdrake(4)

## Turn 10

### Step 42: policy-prior-puct-v1

**P1 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P1 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 0, "turn": 9}`
- `{"card": "EDR_457", "kind": "draw", "player": 1, "turn": 10}`
- `{"kind": "turn_start", "player": 1, "turn": 10}`

- P1: HP=25 Armor=0 Mana=0/5 Deck=23; Weapon=none; Board=Brood Keeper#6 2/1, Carrier Whelp#17 1/1, Mother Duck#7 2/3, Duckling#76 1/1, Duckling#78 1/1, Royal Librarian#1 4/4, Cannonmaster#72 3/1; Hand=Darkrider(1), Cannoneer(1), Carrier Whelp(1), Shadowflame Suffusion(2), Cannoneer(1)
- P2: HP=16 Armor=0 Mana=5/5 Deck=22; Weapon=none; Board=Royal Librarian#31 4/4; Hand=Hook n' Heave(2), Stadium Announcer(4), Chrono-Lord Epoch(6), Erupting Volcano(3), Prescient Slitherdrake(4), Brood Keeper(2)

### Step 43: shared-tree-ismcts-v1

**P2 ATTACK Royal Librarian#31 -> P1 Royal Librarian#1**

Legal actions: 15; Searched nodes: 5; Selected value: -0.6763

Top choices by root visit share:

- `0.250` — P2 ATTACK Royal Librarian#31 -> P1 Royal Librarian#1 [SELECTED]; Q=-0.6763; prior=0.0000
- `0.250` — P2 ATTACK Royal Librarian#31 -> P1 Mother Duck#7; Q=-0.7033; prior=0.0000
- `0.250` — P2 ATTACK Royal Librarian#31 -> P1 Brood Keeper#6; Q=-0.7661; prior=0.0000
- `0.250` — P2 ATTACK Royal Librarian#31 -> P1 Cannonmaster#72; Q=-0.7813; prior=0.0000
- `0.000` — P2 ATTACK Royal Librarian#31 -> P1 hero; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "CORE_SW_066", "entity": 1, "kind": "minion_died", "player": 0, "turn": 10}`
- `{"card": "CORE_SW_066", "entity": 31, "kind": "minion_died", "player": 1, "turn": 10}`

- P1: HP=25 Armor=0 Mana=0/5 Deck=23; Weapon=none; Board=Brood Keeper#6 2/1, Carrier Whelp#17 1/1, Mother Duck#7 2/3, Duckling#76 1/1, Duckling#78 1/1, Cannonmaster#72 3/1; Hand=Darkrider(1), Cannoneer(1), Carrier Whelp(1), Shadowflame Suffusion(2), Cannoneer(1)
- P2: HP=16 Armor=0 Mana=5/5 Deck=22; Weapon=none; Board=empty; Hand=Hook n' Heave(2), Stadium Announcer(4), Chrono-Lord Epoch(6), Erupting Volcano(3), Prescient Slitherdrake(4), Brood Keeper(2)

### Step 44: shared-tree-ismcts-v1

**P2 PLAY Prescient Slitherdrake[END_033] -> -**

Legal actions: 7; Searched nodes: 5; Selected value: -0.6250

Top choices by root visit share:

- `0.250` — P2 PLAY Prescient Slitherdrake[END_033] -> - [SELECTED]; Q=-0.6250; prior=0.0000
- `0.250` — P2 PLAY Stadium Announcer[TIME_034] -> -; Q=-0.7299; prior=0.0000
- `0.250` — P2 PLAY Brood Keeper[EDR_457] -> -; Q=-0.8816; prior=0.0000
- `0.250` — P2 PLAY Erupting Volcano[CATA_584] -> -; Q=-0.8816; prior=0.0000
- `0.000` — P2 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "END_033", "controller": 1, "created_by": null, "entity": 46, "kind": "play", "player": 1, "started_in_deck": true, "turn": 10}`

- P1: HP=25 Armor=0 Mana=0/5 Deck=23; Weapon=none; Board=Brood Keeper#6 2/1, Carrier Whelp#17 1/1, Mother Duck#7 2/3, Duckling#76 1/1, Duckling#78 1/1, Cannonmaster#72 3/1; Hand=Darkrider(1), Cannoneer(1), Carrier Whelp(1), Shadowflame Suffusion(2), Cannoneer(1)
- P2: HP=16 Armor=0 Mana=1/5 Deck=22; Weapon=none; Board=Prescient Slitherdrake#46 5/8; Hand=Hook n' Heave(2), Stadium Announcer(4), Chrono-Lord Epoch(6), Erupting Volcano(3), Brood Keeper(2)

## Turn 11

### Step 45: shared-tree-ismcts-v1

**P2 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P2 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 1, "turn": 10}`
- `{"card": "EDR_457", "kind": "draw", "player": 0, "turn": 11}`
- `{"kind": "turn_start", "player": 0, "turn": 11}`

- P1: HP=25 Armor=0 Mana=6/6 Deck=22; Weapon=none; Board=Brood Keeper#6 2/1, Carrier Whelp#17 1/1, Mother Duck#7 2/3, Duckling#76 1/1, Duckling#78 1/1, Cannonmaster#72 3/1; Hand=Darkrider(1), Cannoneer(1), Carrier Whelp(1), Shadowflame Suffusion(2), Cannoneer(1), Brood Keeper(2)
- P2: HP=16 Armor=0 Mana=1/5 Deck=22; Weapon=none; Board=Prescient Slitherdrake#46 5/8; Hand=Hook n' Heave(2), Stadium Announcer(4), Chrono-Lord Epoch(6), Erupting Volcano(3), Brood Keeper(2)

### Step 46: policy-prior-puct-v1

**P1 ATTACK Duckling#76 -> P2 Prescient Slitherdrake#46**

Legal actions: 27; Searched nodes: 17; Selected value: 0.8675

Top choices by root visit share:

- `0.062` — P1 ATTACK Duckling#76 -> P2 Prescient Slitherdrake#46 [SELECTED]; Q=0.8675; prior=0.0226
- `0.062` — P1 PLAY Darkrider[EDR_456] -> -; Q=0.6945; prior=0.0462
- `0.062` — P1 PLAY Shadowflame Suffusion[FIR_939] -> P2 hero; Q=0.6791; prior=0.0272
- `0.062` — P1 PLAY Brood Keeper[EDR_457] -> -; Q=0.6766; prior=0.0859
- `0.062` — P1 ATTACK Cannonmaster#72 -> P2 hero; Q=0.6726; prior=0.0353

Resolved events:

- `{"card": "EDR_492t", "entity": 76, "kind": "minion_died", "player": 0, "turn": 11}`

- P1: HP=25 Armor=0 Mana=6/6 Deck=22; Weapon=none; Board=Brood Keeper#6 2/1, Carrier Whelp#17 1/1, Mother Duck#7 2/3, Duckling#78 1/1, Cannonmaster#72 3/1; Hand=Darkrider(1), Cannoneer(1), Carrier Whelp(1), Shadowflame Suffusion(2), Cannoneer(1), Brood Keeper(2)
- P2: HP=16 Armor=0 Mana=1/5 Deck=22; Weapon=none; Board=Prescient Slitherdrake#46 5/7; Hand=Hook n' Heave(2), Stadium Announcer(4), Chrono-Lord Epoch(6), Erupting Volcano(3), Brood Keeper(2)

### Step 47: policy-prior-puct-v1

**P1 ATTACK Duckling#78 -> P2 Prescient Slitherdrake#46**

Legal actions: 24; Searched nodes: 17; Selected value: 0.9345

Top choices by root visit share:

- `0.062` — P1 ATTACK Duckling#78 -> P2 Prescient Slitherdrake#46 [SELECTED]; Q=0.9345; prior=0.0255
- `0.062` — P1 ATTACK Mother Duck#7 -> P2 Prescient Slitherdrake#46; Q=0.9148; prior=0.0224
- `0.062` — P1 PLAY Brood Keeper[EDR_457] -> -; Q=0.9055; prior=0.0974
- `0.062` — P1 ATTACK Cannonmaster#72 -> P2 hero; Q=0.9016; prior=0.0381
- `0.062` — P1 PLAY Carrier Whelp[CATA_556] -> -; Q=0.9016; prior=0.0480

Resolved events:

- `{"card": "EDR_492t", "entity": 78, "kind": "minion_died", "player": 0, "turn": 11}`

- P1: HP=25 Armor=0 Mana=6/6 Deck=22; Weapon=none; Board=Brood Keeper#6 2/1, Carrier Whelp#17 1/1, Mother Duck#7 2/3, Cannonmaster#72 3/1; Hand=Darkrider(1), Cannoneer(1), Carrier Whelp(1), Shadowflame Suffusion(2), Cannoneer(1), Brood Keeper(2)
- P2: HP=16 Armor=0 Mana=1/5 Deck=22; Weapon=none; Board=Prescient Slitherdrake#46 5/6; Hand=Hook n' Heave(2), Stadium Announcer(4), Chrono-Lord Epoch(6), Erupting Volcano(3), Brood Keeper(2)

### Step 48: policy-prior-puct-v1

**P1 PLAY Brood Keeper[EDR_457] -> -**

Legal actions: 21; Searched nodes: 17; Selected value: 0.9585

Top choices by root visit share:

- `0.062` — P1 PLAY Brood Keeper[EDR_457] -> - [SELECTED]; Q=0.9585; prior=0.1036
- `0.062` — P1 ATTACK Cannonmaster#72 -> P2 Prescient Slitherdrake#46; Q=0.9531; prior=0.0280
- `0.062` — P1 PLAY Carrier Whelp[CATA_556] -> -; Q=0.9518; prior=0.0494
- `0.062` — P1 ATTACK Mother Duck#7 -> P2 hero; Q=0.9476; prior=0.0407
- `0.062` — P1 HERO_POWER Armor Up; Q=0.9476; prior=0.2159

Resolved events:

- `{"card": "EDR_457", "controller": 0, "created_by": null, "entity": 5, "kind": "play", "player": 0, "started_in_deck": true, "turn": 11}`
- `{"attack": 2, "card": "EDR_457t", "durability": 2, "kind": "equip_weapon", "player": 0, "turn": 11}`

- P1: HP=25 Armor=0 Mana=4/6 Deck=22; Weapon=Brood Keeper's Sword 2/2; Board=Brood Keeper#6 2/1, Carrier Whelp#17 1/1, Mother Duck#7 2/3, Cannonmaster#72 3/1, Brood Keeper#5 2/3; Hand=Darkrider(1), Cannoneer(1), Carrier Whelp(1), Shadowflame Suffusion(2), Cannoneer(1)
- P2: HP=16 Armor=0 Mana=1/5 Deck=22; Weapon=none; Board=Prescient Slitherdrake#46 5/6; Hand=Hook n' Heave(2), Stadium Announcer(4), Chrono-Lord Epoch(6), Erupting Volcano(3), Brood Keeper(2)

### Step 49: policy-prior-puct-v1

**P1 HERO_ATTACK -> P2 hero**

Legal actions: 23; Searched nodes: 17; Selected value: 0.9713

Top choices by root visit share:

- `0.062` — P1 HERO_ATTACK -> P2 hero [SELECTED]; Q=0.9713; prior=0.0492
- `0.062` — P1 ATTACK Cannonmaster#72 -> P2 Prescient Slitherdrake#46; Q=0.9704; prior=0.0261
- `0.062` — P1 PLAY Carrier Whelp[CATA_556] -> -; Q=0.9695; prior=0.0600
- `0.062` — P1 ATTACK Brood Keeper#6 -> P2 hero; Q=0.9668; prior=0.0287
- `0.062` — P1 ATTACK Mother Duck#7 -> P2 hero; Q=0.9668; prior=0.0375

- P1: HP=25 Armor=0 Mana=4/6 Deck=22; Weapon=Brood Keeper's Sword 2/1; Board=Brood Keeper#6 2/1, Carrier Whelp#17 1/1, Mother Duck#7 2/3, Cannonmaster#72 3/1, Brood Keeper#5 2/3; Hand=Darkrider(1), Cannoneer(1), Carrier Whelp(1), Shadowflame Suffusion(2), Cannoneer(1)
- P2: HP=14 Armor=0 Mana=1/5 Deck=22; Weapon=none; Board=Prescient Slitherdrake#46 5/6; Hand=Hook n' Heave(2), Stadium Announcer(4), Chrono-Lord Epoch(6), Erupting Volcano(3), Brood Keeper(2)

### Step 50: policy-prior-puct-v1

**P1 ATTACK Cannonmaster#72 -> P2 Prescient Slitherdrake#46**

Legal actions: 21; Searched nodes: 17; Selected value: 0.9795

Top choices by root visit share:

- `0.062` — P1 ATTACK Cannonmaster#72 -> P2 Prescient Slitherdrake#46 [SELECTED]; Q=0.9795; prior=0.0287
- `0.062` — P1 PLAY Carrier Whelp[CATA_556] -> -; Q=0.9790; prior=0.0631
- `0.062` — P1 ATTACK Mother Duck#7 -> P2 hero; Q=0.9771; prior=0.0417
- `0.062` — P1 HERO_POWER Armor Up; Q=0.9771; prior=0.2429
- `0.062` — P1 PLAY Cannoneer[CAP_107t] -> -; Q=0.9766; prior=0.0639

Resolved events:

- `{"card": "CAP_107", "entity": 72, "kind": "minion_died", "player": 0, "turn": 11}`

- P1: HP=25 Armor=0 Mana=4/6 Deck=22; Weapon=Brood Keeper's Sword 2/1; Board=Brood Keeper#6 2/1, Carrier Whelp#17 1/1, Mother Duck#7 2/3, Brood Keeper#5 2/3; Hand=Darkrider(1), Cannoneer(1), Carrier Whelp(1), Shadowflame Suffusion(2), Cannoneer(1)
- P2: HP=14 Armor=0 Mana=1/5 Deck=22; Weapon=none; Board=Prescient Slitherdrake#46 5/3; Hand=Hook n' Heave(2), Stadium Announcer(4), Chrono-Lord Epoch(6), Erupting Volcano(3), Brood Keeper(2)

### Step 51: policy-prior-puct-v1

**P1 ATTACK Brood Keeper#6 -> P2 Prescient Slitherdrake#46**

Legal actions: 18; Searched nodes: 17; Selected value: 0.9854

Top choices by root visit share:

- `0.062` — P1 ATTACK Brood Keeper#6 -> P2 Prescient Slitherdrake#46 [SELECTED]; Q=0.9854; prior=0.0368
- `0.062` — P1 ATTACK Carrier Whelp#17 -> P2 Prescient Slitherdrake#46; Q=0.9854; prior=0.0342
- `0.062` — P1 PLAY Carrier Whelp[CATA_556] -> -; Q=0.9850; prior=0.0660
- `0.062` — P1 ATTACK Mother Duck#7 -> P2 hero; Q=0.9837; prior=0.0641
- `0.062` — P1 HERO_POWER Armor Up; Q=0.9837; prior=0.2234

Resolved events:

- `{"card": "JAIL_421", "kind": "summon_from_zone", "player": 0, "turn": 11}`
- `{"card": "JAIL_421", "kind": "summon_from_zone", "player": 0, "turn": 11}`
- `{"card": "EDR_457", "entity": 6, "kind": "minion_died", "player": 0, "turn": 11}`

- P1: HP=25 Armor=0 Mana=4/6 Deck=20; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#17 1/1, Mother Duck#7 2/3, Brood Keeper#5 2/3, Warptooth#62 3/3, Warptooth#25 3/3; Hand=Darkrider(1), Cannoneer(1), Carrier Whelp(1), Shadowflame Suffusion(2), Cannoneer(1)
- P2: HP=14 Armor=0 Mana=1/5 Deck=22; Weapon=none; Board=Prescient Slitherdrake#46 5/1; Hand=Hook n' Heave(2), Stadium Announcer(4), Chrono-Lord Epoch(6), Erupting Volcano(3), Brood Keeper(2)

### Step 52: policy-prior-puct-v1

**P1 PLAY Carrier Whelp[CATA_556] -> -**

Legal actions: 21; Searched nodes: 17; Selected value: 0.9893

Top choices by root visit share:

- `0.062` — P1 PLAY Carrier Whelp[CATA_556] -> - [SELECTED]; Q=0.9893; prior=0.0580
- `0.062` — P1 ATTACK Mother Duck#7 -> P2 hero; Q=0.9884; prior=0.0626
- `0.062` — P1 ATTACK Warptooth#25 -> P2 hero; Q=0.9884; prior=0.0656
- `0.062` — P1 ATTACK Warptooth#62 -> P2 hero; Q=0.9884; prior=0.0726
- `0.062` — P1 HERO_POWER Armor Up; Q=0.9884; prior=0.1820

Resolved events:

- `{"card": "CATA_556", "controller": 0, "created_by": "CATA_556", "entity": 75, "kind": "play", "player": 0, "started_in_deck": false, "turn": 11}`
- `{"card": "CATA_556", "entity": 80, "kind": "generated_to_hand", "player": 0, "source": "CATA_556", "turn": 11}`

- P1: HP=25 Armor=0 Mana=3/6 Deck=20; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#17 1/1, Mother Duck#7 2/3, Brood Keeper#5 2/3, Warptooth#62 3/3, Warptooth#25 3/3, Carrier Whelp#75 1/2; Hand=Darkrider(1), Cannoneer(1), Shadowflame Suffusion(2), Cannoneer(1), Carrier Whelp(1)
- P2: HP=14 Armor=0 Mana=1/5 Deck=22; Weapon=none; Board=Prescient Slitherdrake#46 5/1; Hand=Hook n' Heave(2), Stadium Announcer(4), Chrono-Lord Epoch(6), Erupting Volcano(3), Brood Keeper(2)

### Step 53: policy-prior-puct-v1

**P1 PLAY Carrier Whelp[CATA_556] -> -**

Legal actions: 22; Searched nodes: 17; Selected value: 0.9922

Top choices by root visit share:

- `0.062` — P1 PLAY Carrier Whelp[CATA_556] -> - [SELECTED]; Q=0.9922; prior=0.0648
- `0.062` — P1 ATTACK Mother Duck#7 -> P2 hero; Q=0.9915; prior=0.0654
- `0.062` — P1 ATTACK Carrier Whelp#17 -> P2 Prescient Slitherdrake#46; Q=0.9915; prior=0.0258
- `0.062` — P1 ATTACK Warptooth#25 -> P2 hero; Q=0.9915; prior=0.0648
- `0.062` — P1 ATTACK Warptooth#62 -> P2 hero; Q=0.9915; prior=0.0717

Resolved events:

- `{"card": "CATA_556", "controller": 0, "created_by": "CATA_556", "entity": 80, "kind": "play", "player": 0, "started_in_deck": false, "turn": 11}`
- `{"card": "CATA_556", "entity": 81, "kind": "generated_to_hand", "player": 0, "source": "CATA_556", "turn": 11}`

- P1: HP=25 Armor=0 Mana=2/6 Deck=20; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#17 1/1, Mother Duck#7 2/3, Brood Keeper#5 2/3, Warptooth#62 3/3, Warptooth#25 3/3, Carrier Whelp#75 1/2, Carrier Whelp#80 1/2; Hand=Darkrider(1), Cannoneer(1), Shadowflame Suffusion(2), Cannoneer(1), Carrier Whelp(1)
- P2: HP=14 Armor=0 Mana=1/5 Deck=22; Weapon=none; Board=Prescient Slitherdrake#46 5/1; Hand=Hook n' Heave(2), Stadium Announcer(4), Chrono-Lord Epoch(6), Erupting Volcano(3), Brood Keeper(2)

### Step 54: policy-prior-puct-v1

**P1 HERO_POWER Armor Up**

Legal actions: 19; Searched nodes: 17; Selected value: 0.9938

Top choices by root visit share:

- `0.062` — P1 HERO_POWER Armor Up [SELECTED]; Q=0.9938; prior=0.2107
- `0.062` — P1 ATTACK Mother Duck#7 -> P2 hero; Q=0.9938; prior=0.0992
- `0.062` — P1 ATTACK Carrier Whelp#17 -> P2 Prescient Slitherdrake#46; Q=0.9938; prior=0.0301
- `0.062` — P1 ATTACK Warptooth#25 -> P2 hero; Q=0.9938; prior=0.0912
- `0.062` — P1 ATTACK Warptooth#62 -> P2 hero; Q=0.9938; prior=0.1019

Resolved events:

- `{"amount": 2, "kind": "gain_armor", "player": 0, "turn": 11}`
- `{"kind": "hero_power", "player": 0, "turn": 11}`

- P1: HP=25 Armor=2 Mana=0/6 Deck=20; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#17 1/1, Mother Duck#7 2/3, Brood Keeper#5 2/3, Warptooth#62 3/3, Warptooth#25 3/3, Carrier Whelp#75 1/2, Carrier Whelp#80 1/2; Hand=Darkrider(1), Cannoneer(1), Shadowflame Suffusion(2), Cannoneer(1), Carrier Whelp(1)
- P2: HP=14 Armor=0 Mana=1/5 Deck=22; Weapon=none; Board=Prescient Slitherdrake#46 5/1; Hand=Hook n' Heave(2), Stadium Announcer(4), Chrono-Lord Epoch(6), Erupting Volcano(3), Brood Keeper(2)

### Step 55: policy-prior-puct-v1

**P1 ATTACK Warptooth#25 -> P2 hero**

Legal actions: 9; Searched nodes: 17; Selected value: 0.9949

Top choices by root visit share:

- `0.188` — P1 ATTACK Warptooth#25 -> P2 hero [SELECTED]; Q=0.9949; prior=0.1620
- `0.188` — P1 ATTACK Mother Duck#7 -> P2 hero; Q=0.9949; prior=0.1877
- `0.188` — P1 ATTACK Warptooth#62 -> P2 hero; Q=0.9949; prior=0.1947
- `0.125` — P1 ATTACK Carrier Whelp#17 -> P2 hero; Q=0.9889; prior=0.1615
- `0.062` — P1 ATTACK Carrier Whelp#17 -> P2 Prescient Slitherdrake#46; Q=0.9951; prior=0.0678

- P1: HP=25 Armor=2 Mana=0/6 Deck=20; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#17 1/1, Mother Duck#7 2/3, Brood Keeper#5 2/3, Warptooth#62 3/3, Warptooth#25 3/3, Carrier Whelp#75 1/2, Carrier Whelp#80 1/2; Hand=Darkrider(1), Cannoneer(1), Shadowflame Suffusion(2), Cannoneer(1), Carrier Whelp(1)
- P2: HP=11 Armor=0 Mana=1/5 Deck=22; Weapon=none; Board=Prescient Slitherdrake#46 5/1; Hand=Hook n' Heave(2), Stadium Announcer(4), Chrono-Lord Epoch(6), Erupting Volcano(3), Brood Keeper(2)

### Step 56: policy-prior-puct-v1

**P1 ATTACK Mother Duck#7 -> P2 hero**

Legal actions: 7; Searched nodes: 15; Selected value: 0.9909

Top choices by root visit share:

- `0.286` — P1 ATTACK Mother Duck#7 -> P2 hero [SELECTED]; Q=0.9909; prior=0.2482
- `0.214` — P1 ATTACK Carrier Whelp#17 -> P2 hero; Q=0.9876; prior=0.2139
- `0.214` — P1 ATTACK Warptooth#62 -> P2 hero; Q=0.9635; prior=0.2541
- `0.071` — P1 ATTACK Carrier Whelp#17 -> P2 Prescient Slitherdrake#46; Q=0.9949; prior=0.0839
- `0.071` — P1 ATTACK Mother Duck#7 -> P2 Prescient Slitherdrake#46; Q=0.9910; prior=0.0787

- P1: HP=25 Armor=2 Mana=0/6 Deck=20; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#17 1/1, Mother Duck#7 2/3, Brood Keeper#5 2/3, Warptooth#62 3/3, Warptooth#25 3/3, Carrier Whelp#75 1/2, Carrier Whelp#80 1/2; Hand=Darkrider(1), Cannoneer(1), Shadowflame Suffusion(2), Cannoneer(1), Carrier Whelp(1)
- P2: HP=9 Armor=0 Mana=1/5 Deck=22; Weapon=none; Board=Prescient Slitherdrake#46 5/1; Hand=Hook n' Heave(2), Stadium Announcer(4), Chrono-Lord Epoch(6), Erupting Volcano(3), Brood Keeper(2)

### Step 57: policy-prior-puct-v1

**P1 ATTACK Warptooth#62 -> P2 hero**

Legal actions: 5; Searched nodes: 11; Selected value: 0.9762

Top choices by root visit share:

- `0.400` — P1 ATTACK Warptooth#62 -> P2 hero [SELECTED]; Q=0.9762; prior=0.3739
- `0.300` — P1 ATTACK Carrier Whelp#17 -> P2 hero; Q=0.9881; prior=0.2993
- `0.100` — P1 ATTACK Warptooth#62 -> P2 Prescient Slitherdrake#46; Q=0.9856; prior=0.1132
- `0.100` — P1 ATTACK Carrier Whelp#17 -> P2 Prescient Slitherdrake#46; Q=0.9792; prior=0.1308
- `0.100` — P1 END_TURN; Q=0.9529; prior=0.0829

- P1: HP=25 Armor=2 Mana=0/6 Deck=20; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#17 1/1, Mother Duck#7 2/3, Brood Keeper#5 2/3, Warptooth#62 3/3, Warptooth#25 3/3, Carrier Whelp#75 1/2, Carrier Whelp#80 1/2; Hand=Darkrider(1), Cannoneer(1), Shadowflame Suffusion(2), Cannoneer(1), Carrier Whelp(1)
- P2: HP=6 Armor=0 Mana=1/5 Deck=22; Weapon=none; Board=Prescient Slitherdrake#46 5/1; Hand=Hook n' Heave(2), Stadium Announcer(4), Chrono-Lord Epoch(6), Erupting Volcano(3), Brood Keeper(2)

### Step 58: policy-prior-puct-v1

**P1 ATTACK Carrier Whelp#17 -> P2 hero**

Legal actions: 3; Searched nodes: 7; Selected value: 0.9346

Top choices by root visit share:

- `0.667` — P1 ATTACK Carrier Whelp#17 -> P2 hero [SELECTED]; Q=0.9346; prior=0.5885
- `0.167` — P1 END_TURN; Q=0.9381; prior=0.1698
- `0.167` — P1 ATTACK Carrier Whelp#17 -> P2 Prescient Slitherdrake#46; Q=0.8534; prior=0.2417

- P1: HP=25 Armor=2 Mana=0/6 Deck=20; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#17 1/1, Mother Duck#7 2/3, Brood Keeper#5 2/3, Warptooth#62 3/3, Warptooth#25 3/3, Carrier Whelp#75 1/2, Carrier Whelp#80 1/2; Hand=Darkrider(1), Cannoneer(1), Shadowflame Suffusion(2), Cannoneer(1), Carrier Whelp(1)
- P2: HP=5 Armor=0 Mana=1/5 Deck=22; Weapon=none; Board=Prescient Slitherdrake#46 5/1; Hand=Hook n' Heave(2), Stadium Announcer(4), Chrono-Lord Epoch(6), Erupting Volcano(3), Brood Keeper(2)

## Turn 12

### Step 59: policy-prior-puct-v1

**P1 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P1 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 0, "turn": 11}`
- `{"card": "CATA_582", "kind": "draw", "player": 1, "turn": 12}`
- `{"kind": "turn_start", "player": 1, "turn": 12}`

- P1: HP=25 Armor=2 Mana=0/6 Deck=20; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#17 1/1, Mother Duck#7 2/3, Brood Keeper#5 2/3, Warptooth#62 3/3, Warptooth#25 3/3, Carrier Whelp#75 1/2, Carrier Whelp#80 1/2; Hand=Darkrider(1), Cannoneer(1), Shadowflame Suffusion(2), Cannoneer(1), Carrier Whelp(1)
- P2: HP=5 Armor=0 Mana=6/6 Deck=21; Weapon=none; Board=Prescient Slitherdrake#46 5/1; Hand=Hook n' Heave(2), Stadium Announcer(4), Chrono-Lord Epoch(6), Erupting Volcano(3), Brood Keeper(2), Searing Fissure(2)

### Step 60: shared-tree-ismcts-v1

**P2 ATTACK Prescient Slitherdrake#46 -> P1 Warptooth#25**

Legal actions: 16; Searched nodes: 5; Selected value: -0.6468

Top choices by root visit share:

- `0.250` — P2 ATTACK Prescient Slitherdrake#46 -> P1 Warptooth#25 [SELECTED]; Q=-0.6468; prior=0.0000
- `0.250` — P2 ATTACK Prescient Slitherdrake#46 -> P1 Warptooth#62; Q=-0.6468; prior=0.0000
- `0.250` — P2 ATTACK Prescient Slitherdrake#46 -> P1 Mother Duck#7; Q=-0.6776; prior=0.0000
- `0.250` — P2 ATTACK Prescient Slitherdrake#46 -> P1 Brood Keeper#5; Q=-0.8256; prior=0.0000
- `0.000` — P2 ATTACK Prescient Slitherdrake#46 -> P1 hero; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "JAIL_421", "entity": 25, "kind": "minion_died", "player": 0, "turn": 12}`
- `{"card": "END_033", "entity": 46, "kind": "minion_died", "player": 1, "turn": 12}`

- P1: HP=25 Armor=2 Mana=0/6 Deck=20; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#17 1/1, Mother Duck#7 2/3, Brood Keeper#5 2/3, Warptooth#62 3/3, Carrier Whelp#75 1/2, Carrier Whelp#80 1/2; Hand=Darkrider(1), Cannoneer(1), Shadowflame Suffusion(2), Cannoneer(1), Carrier Whelp(1)
- P2: HP=5 Armor=0 Mana=6/6 Deck=21; Weapon=none; Board=empty; Hand=Hook n' Heave(2), Stadium Announcer(4), Chrono-Lord Epoch(6), Erupting Volcano(3), Brood Keeper(2), Searing Fissure(2)

### Step 61: shared-tree-ismcts-v1

**P2 PLAY Chrono-Lord Epoch[TIME_714] -> -**

Legal actions: 8; Searched nodes: 5; Selected value: -0.5919

Top choices by root visit share:

- `0.250` — P2 PLAY Chrono-Lord Epoch[TIME_714] -> - [SELECTED]; Q=-0.5919; prior=0.0000
- `0.250` — P2 PLAY Brood Keeper[EDR_457] -> -; Q=-0.9343; prior=0.0000
- `0.250` — P2 PLAY Stadium Announcer[TIME_034] -> -; Q=-0.9501; prior=0.0000
- `0.250` — P2 PLAY Erupting Volcano[CATA_584] -> -; Q=-0.9833; prior=0.0000
- `0.000` — P2 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "TIME_714", "controller": 1, "created_by": "EDR_456", "entity": 70, "kind": "play", "player": 1, "started_in_deck": false, "turn": 12}`
- `{"card": "EDR_457", "entity": 5, "kind": "minion_died", "player": 0, "turn": 12}`
- `{"card": "CATA_556", "entity": 75, "kind": "minion_died", "player": 0, "turn": 12}`
- `{"card": "CATA_556", "entity": 80, "kind": "minion_died", "player": 0, "turn": 12}`

- P1: HP=25 Armor=2 Mana=0/6 Deck=20; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#17 1/1, Mother Duck#7 2/3, Warptooth#62 3/3; Hand=Darkrider(1), Cannoneer(1), Shadowflame Suffusion(2), Cannoneer(1), Carrier Whelp(1)
- P2: HP=5 Armor=0 Mana=0/6 Deck=21; Weapon=none; Board=Chrono-Lord Epoch#70 9/7; Hand=Hook n' Heave(2), Stadium Announcer(4), Erupting Volcano(3), Brood Keeper(2), Searing Fissure(2)

## Turn 13

### Step 62: shared-tree-ismcts-v1

**P2 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P2 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 1, "turn": 12}`
- `{"card": "CATA_584", "kind": "draw", "player": 0, "turn": 13}`
- `{"kind": "turn_start", "player": 0, "turn": 13}`

- P1: HP=25 Armor=2 Mana=7/7 Deck=19; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#17 1/1, Mother Duck#7 2/3, Warptooth#62 3/3; Hand=Darkrider(1), Cannoneer(1), Shadowflame Suffusion(2), Cannoneer(1), Carrier Whelp(1), Erupting Volcano(3)
- P2: HP=5 Armor=0 Mana=0/6 Deck=21; Weapon=none; Board=Chrono-Lord Epoch#70 9/7; Hand=Hook n' Heave(2), Stadium Announcer(4), Erupting Volcano(3), Brood Keeper(2), Searing Fissure(2)

### Step 63: policy-prior-puct-v1

**P1 PLAY Shadowflame Suffusion[FIR_939] -> P2 hero**

Legal actions: 20; Searched nodes: 17; Selected value: 1.0000

Top choices by root visit share:

- `0.062` — P1 PLAY Shadowflame Suffusion[FIR_939] -> P2 hero [SELECTED]; Q=1.0000; prior=0.0398
- `0.062` — P1 ATTACK Mother Duck#7 -> P2 hero; Q=1.0000; prior=0.0558
- `0.062` — P1 ATTACK Warptooth#62 -> P2 hero; Q=1.0000; prior=0.0441
- `0.062` — P1 HERO_ATTACK -> P2 hero; Q=1.0000; prior=0.0687
- `0.062` — P1 ATTACK Mother Duck#7 -> P2 Chrono-Lord Epoch#70; Q=0.7368; prior=0.0269

Resolved events:

- `{"card": "FIR_939", "controller": 0, "created_by": null, "entity": 10, "kind": "play", "player": 0, "started_in_deck": true, "turn": 13}`
- `{"kind": "discover_offer", "options": [{"card": "CATA_591", "entity": 82, "gifts": ["sweet_dreams"]}, {"card": "JAIL_435", "entity": 83, "gifts": ["harpys_talons"]}, {"card": "TIME_034", "entity": 84, "gifts": ["rude_awakening"]}], "player": 0, "profile": "closed_pool", "turn": 13}`

- P1: HP=25 Armor=2 Mana=5/7 Deck=19; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#17 1/1, Mother Duck#7 2/3, Warptooth#62 3/3; Hand=Darkrider(1), Cannoneer(1), Cannoneer(1), Carrier Whelp(1), Erupting Volcano(3)
- P2: HP=3 Armor=0 Mana=0/6 Deck=21; Weapon=none; Board=Chrono-Lord Epoch#70 9/7; Hand=Hook n' Heave(2), Stadium Announcer(4), Erupting Volcano(3), Brood Keeper(2), Searing Fissure(2)

### Step 64: policy-prior-puct-v1

**P1 DISCOVER_PICK Rampaging Hound[JAIL_435] + harpys_talons**

Legal actions: 3; Searched nodes: 7; Selected value: 1.0000

Top choices by root visit share:

- `0.500` — P1 DISCOVER_PICK Rampaging Hound[JAIL_435] + harpys_talons [SELECTED]; Q=1.0000; prior=0.5715
- `0.333` — P1 DISCOVER_PICK Stadium Announcer[TIME_034] + rude_awakening; Q=1.0000; prior=0.3453
- `0.167` — P1 DISCOVER_PICK Commander Geddon[CATA_591] + sweet_dreams; Q=1.0000; prior=0.0832

Resolved events:

- `{"card": "JAIL_435", "destination": "hand", "entity": 83, "gifts": ["harpys_talons"], "kind": "discover_pick", "player": 0, "source": "FIR_939", "turn": 13}`

- P1: HP=25 Armor=2 Mana=5/7 Deck=19; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#17 1/1, Mother Duck#7 2/3, Warptooth#62 3/3; Hand=Darkrider(1), Cannoneer(1), Cannoneer(1), Carrier Whelp(1), Erupting Volcano(3), Rampaging Hound(7)
- P2: HP=3 Armor=0 Mana=0/6 Deck=21; Weapon=none; Board=Chrono-Lord Epoch#70 9/7; Hand=Hook n' Heave(2), Stadium Announcer(4), Erupting Volcano(3), Brood Keeper(2), Searing Fissure(2)

### Step 65: policy-prior-puct-v1

**P1 PREPARE Rampaging Hound[JAIL_435]**

Legal actions: 16; Searched nodes: 17; Selected value: 1.0000

Top choices by root visit share:

- `0.062` — P1 PREPARE Rampaging Hound[JAIL_435] [SELECTED]; Q=1.0000; prior=0.0634
- `0.062` — P1 ATTACK Mother Duck#7 -> P2 hero; Q=1.0000; prior=0.0655
- `0.062` — P1 ATTACK Mother Duck#7 -> P2 Chrono-Lord Epoch#70; Q=1.0000; prior=0.0261
- `0.062` — P1 ATTACK Carrier Whelp#17 -> P2 hero; Q=1.0000; prior=0.0332
- `0.062` — P1 ATTACK Carrier Whelp#17 -> P2 Chrono-Lord Epoch#70; Q=1.0000; prior=0.0175

Resolved events:

- `{"card": "JAIL_435", "discount": 6, "entity": 83, "kind": "prepare", "player": 0, "spent": 5, "turn": 13}`

- P1: HP=25 Armor=2 Mana=0/7 Deck=19; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#17 1/1, Mother Duck#7 2/3, Warptooth#62 3/3; Hand=Darkrider(1), Cannoneer(1), Cannoneer(1), Carrier Whelp(1), Erupting Volcano(3), Rampaging Hound(1)
- P2: HP=3 Armor=0 Mana=0/6 Deck=21; Weapon=none; Board=Chrono-Lord Epoch#70 9/7; Hand=Hook n' Heave(2), Stadium Announcer(4), Erupting Volcano(3), Brood Keeper(2), Searing Fissure(2)

### Step 66: policy-prior-puct-v1

**P1 HERO_ATTACK -> P2 hero**

Legal actions: 9; Searched nodes: 16; Selected value: 1.0000

Top choices by root visit share:

- `0.250` — P1 HERO_ATTACK -> P2 hero [SELECTED]; Q=1.0000; prior=0.2136
- `0.250` — P1 ATTACK Mother Duck#7 -> P2 hero; Q=1.0000; prior=0.2140
- `0.125` — P1 ATTACK Warptooth#62 -> P2 hero; Q=1.0000; prior=0.1575
- `0.062` — P1 ATTACK Mother Duck#7 -> P2 Chrono-Lord Epoch#70; Q=1.0000; prior=0.0809
- `0.062` — P1 ATTACK Carrier Whelp#17 -> P2 hero; Q=1.0000; prior=0.1050

Resolved events:

- `{"card": "EDR_457t", "kind": "weapon_destroyed", "player": 0, "turn": 13}`

- P1: HP=25 Armor=2 Mana=0/7 Deck=19; Weapon=none; Board=Carrier Whelp#17 1/1, Mother Duck#7 2/3, Warptooth#62 3/3; Hand=Darkrider(1), Cannoneer(1), Cannoneer(1), Carrier Whelp(1), Erupting Volcano(3), Rampaging Hound(1)
- P2: HP=1 Armor=0 Mana=0/6 Deck=21; Weapon=none; Board=Chrono-Lord Epoch#70 9/7; Hand=Hook n' Heave(2), Stadium Announcer(4), Erupting Volcano(3), Brood Keeper(2), Searing Fissure(2)

### Step 67: policy-prior-puct-v1

**P1 ATTACK Mother Duck#7 -> P2 hero**

Legal actions: 7; Searched nodes: 8; Selected value: 1.0000

Top choices by root visit share:

- `0.357` — P1 ATTACK Mother Duck#7 -> P2 hero [SELECTED]; Q=1.0000; prior=0.3031
- `0.214` — P1 ATTACK Warptooth#62 -> P2 hero; Q=1.0000; prior=0.2263
- `0.143` — P1 ATTACK Carrier Whelp#17 -> P2 hero; Q=1.0000; prior=0.1575
- `0.071` — P1 ATTACK Mother Duck#7 -> P2 Chrono-Lord Epoch#70; Q=1.0000; prior=0.1023
- `0.071` — P1 ATTACK Carrier Whelp#17 -> P2 Chrono-Lord Epoch#70; Q=1.0000; prior=0.0757

- P1: HP=25 Armor=2 Mana=0/7 Deck=19; Weapon=none; Board=Carrier Whelp#17 1/1, Mother Duck#7 2/3, Warptooth#62 3/3; Hand=Darkrider(1), Cannoneer(1), Cannoneer(1), Carrier Whelp(1), Erupting Volcano(3), Rampaging Hound(1)
- P2: HP=-1 Armor=0 Mana=0/6 Deck=21; Weapon=none; Board=Chrono-Lord Epoch#70 9/7; Hand=Hook n' Heave(2), Stadium Announcer(4), Erupting Volcano(3), Brood Keeper(2), Searing Fissure(2)


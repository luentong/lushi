# Policy-prior PUCT vs ISMCTS detailed trace

- Seed: `202609100010`
- Candidate: `P2`
- Winner: `P1`
- Candidate win: `False`
- Actions: `52`
- Illegal actions: `0`

## Turn 1

### Step 1: shared-tree-ismcts-v1

**P1 PLAY Cannonmaster[CAP_107] -> -**

Legal actions: 2; Searched nodes: 5; Selected value: -0.0337

Top choices by root visit share:

- `0.500` — P1 PLAY Cannonmaster[CAP_107] -> - [SELECTED]; Q=-0.0337; prior=0.0000
- `0.500` — P1 END_TURN; Q=-0.1427; prior=0.0000

Resolved events:

- `{"card": "CAP_107", "controller": 0, "created_by": null, "entity": 30, "kind": "play", "player": 0, "started_in_deck": true, "turn": 1}`
- `{"card": "CAP_107t", "entity": 64, "kind": "generated_to_hand", "player": 0, "source": "CAP_107", "turn": 1}`

- P1: HP=30 Armor=0 Mana=0/1 Deck=27; Weapon=none; Board=Cannonmaster#30 3/1; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(8), Cannoneer(1)
- P2: HP=30 Armor=0 Mana=0/0 Deck=27; Weapon=none; Board=empty; Hand=Sanguine Depths(1), Hook n' Heave(2), Torch(1), Torch(1), The Coin(0)

## Turn 2

### Step 2: shared-tree-ismcts-v1

**P1 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P1 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 0, "turn": 1}`
- `{"card": "CATA_584", "kind": "draw", "player": 1, "turn": 2}`
- `{"kind": "turn_start", "player": 1, "turn": 2}`

- P1: HP=30 Armor=0 Mana=0/1 Deck=27; Weapon=none; Board=Cannonmaster#30 3/1; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(8), Cannoneer(1)
- P2: HP=30 Armor=0 Mana=1/1 Deck=26; Weapon=none; Board=empty; Hand=Sanguine Depths(1), Hook n' Heave(2), Torch(1), Torch(1), The Coin(0), Erupting Volcano(3)

### Step 3: policy-prior-puct-v1

**P2 PLAY The Coin[GAME_005] -> -**

Legal actions: 3; Searched nodes: 5; Selected value: 0.1828

Top choices by root visit share:

- `0.500` — P2 PLAY The Coin[GAME_005] -> - [SELECTED]; Q=0.1828; prior=0.6212
- `0.250` — P2 PLAY Sanguine Depths[CORE_REV_990] -> -; Q=-0.4008; prior=0.2033
- `0.250` — P2 END_TURN; Q=-0.4612; prior=0.1755

Resolved events:

- `{"card": "GAME_005", "controller": 1, "created_by": "MULLIGAN", "entity": 61, "kind": "play", "player": 1, "started_in_deck": false, "turn": 2}`

- P1: HP=30 Armor=0 Mana=0/1 Deck=27; Weapon=none; Board=Cannonmaster#30 3/1; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(8), Cannoneer(1)
- P2: HP=30 Armor=0 Mana=2/1 Deck=26; Weapon=none; Board=empty; Hand=Sanguine Depths(1), Hook n' Heave(2), Torch(1), Torch(1), Erupting Volcano(3)

### Step 4: policy-prior-puct-v1

**P2 PLAY Hook n' Heave[CAP_105] -> -**

Legal actions: 4; Searched nodes: 5; Selected value: 0.1731

Top choices by root visit share:

- `0.250` — P2 PLAY Hook n' Heave[CAP_105] -> - [SELECTED]; Q=0.1731; prior=0.3167
- `0.250` — P2 PLAY Sanguine Depths[CORE_REV_990] -> -; Q=-0.1698; prior=0.1554
- `0.250` — P2 HERO_POWER Armor Up; Q=-0.5668; prior=0.2233
- `0.250` — P2 END_TURN; Q=-0.6377; prior=0.3046

Resolved events:

- `{"card": "CAP_105", "controller": 1, "created_by": null, "entity": 57, "kind": "play", "player": 1, "started_in_deck": true, "turn": 2}`
- `{"kind": "discover_offer", "options": [{"card": "CAP_107", "entity": 65, "gifts": []}], "player": 1, "profile": "closed_pool", "turn": 2}`

- P1: HP=30 Armor=0 Mana=0/1 Deck=27; Weapon=none; Board=Cannonmaster#30 3/1; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(8), Cannoneer(1)
- P2: HP=30 Armor=0 Mana=0/1 Deck=26; Weapon=none; Board=empty; Hand=Sanguine Depths(1), Torch(1), Torch(1), Erupting Volcano(3)

### Step 5: policy-prior-puct-v1

**P2 DISCOVER_PICK Cannonmaster[CAP_107]**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P2 DISCOVER_PICK Cannonmaster[CAP_107]; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "CAP_107", "destination": "hand", "entity": 65, "gifts": [], "kind": "discover_pick", "player": 1, "source": "CAP_105", "turn": 2}`

- P1: HP=30 Armor=0 Mana=0/1 Deck=27; Weapon=none; Board=Cannonmaster#30 3/1; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(8), Cannoneer(1)
- P2: HP=30 Armor=0 Mana=0/1 Deck=26; Weapon=none; Board=Cutlass Cutthroat#66 1/1, Cutlass Cutthroat#67 1/1; Hand=Sanguine Depths(1), Torch(1), Torch(1), Erupting Volcano(3), Cannonmaster(1)

## Turn 3

### Step 6: policy-prior-puct-v1

**P2 END_TURN**

Legal actions: 3; Searched nodes: 5; Selected value: -0.0198

Top choices by root visit share:

- `0.500` — P2 END_TURN [SELECTED]; Q=-0.0198; prior=0.6641
- `0.250` — P2 ATTACK Cutlass Cutthroat#67 -> P1 Cannonmaster#30; Q=-0.1503; prior=0.1743
- `0.250` — P2 ATTACK Cutlass Cutthroat#66 -> P1 Cannonmaster#30; Q=-0.2447; prior=0.1617

Resolved events:

- `{"kind": "turn_end", "player": 1, "turn": 2}`
- `{"card": "CAP_105", "kind": "draw", "player": 0, "turn": 3}`
- `{"kind": "turn_start", "player": 0, "turn": 3}`

- P1: HP=30 Armor=0 Mana=2/2 Deck=26; Weapon=none; Board=Cannonmaster#30 3/1; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(8), Cannoneer(1), Hook n' Heave(2)
- P2: HP=30 Armor=0 Mana=0/1 Deck=26; Weapon=none; Board=Cutlass Cutthroat#66 1/1, Cutlass Cutthroat#67 1/1; Hand=Sanguine Depths(1), Torch(1), Torch(1), Erupting Volcano(3), Cannonmaster(1)

### Step 7: shared-tree-ismcts-v1

**P1 ATTACK Cannonmaster#30 -> P2 hero**

Legal actions: 7; Searched nodes: 5; Selected value: 0.3839

Top choices by root visit share:

- `0.250` — P1 ATTACK Cannonmaster#30 -> P2 hero [SELECTED]; Q=0.3839; prior=0.0000
- `0.250` — P1 PLAY Hook n' Heave[CAP_105] -> -; Q=0.2290; prior=0.0000
- `0.250` — P1 ATTACK Cannonmaster#30 -> P2 Cutlass Cutthroat#66; Q=0.1731; prior=0.0000
- `0.250` — P1 ATTACK Cannonmaster#30 -> P2 Cutlass Cutthroat#67; Q=0.1731; prior=0.0000
- `0.000` — P1 END_TURN; Q=0.0000; prior=0.0000

- P1: HP=30 Armor=0 Mana=2/2 Deck=26; Weapon=none; Board=Cannonmaster#30 3/1; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(8), Cannoneer(1), Hook n' Heave(2)
- P2: HP=27 Armor=0 Mana=0/1 Deck=26; Weapon=none; Board=Cutlass Cutthroat#66 1/1, Cutlass Cutthroat#67 1/1; Hand=Sanguine Depths(1), Torch(1), Torch(1), Erupting Volcano(3), Cannonmaster(1)

### Step 8: shared-tree-ismcts-v1

**P1 PLAY Hook n' Heave[CAP_105] -> -**

Legal actions: 4; Searched nodes: 5; Selected value: 0.3839

Top choices by root visit share:

- `0.250` — P1 PLAY Hook n' Heave[CAP_105] -> - [SELECTED]; Q=0.3839; prior=0.0000
- `0.250` — P1 PLAY Cannoneer[CAP_107t] -> -; Q=0.0968; prior=0.0000
- `0.250` — P1 HERO_POWER Armor Up; Q=0.0337; prior=0.0000
- `0.250` — P1 END_TURN; Q=-0.4079; prior=0.0000

Resolved events:

- `{"card": "CAP_105", "controller": 0, "created_by": null, "entity": 27, "kind": "play", "player": 0, "started_in_deck": true, "turn": 3}`
- `{"kind": "discover_offer", "options": [{"card": "CAP_107", "entity": 68, "gifts": []}], "player": 0, "profile": "closed_pool", "turn": 3}`

- P1: HP=30 Armor=0 Mana=0/2 Deck=26; Weapon=none; Board=Cannonmaster#30 3/1; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(8), Cannoneer(1)
- P2: HP=27 Armor=0 Mana=0/1 Deck=26; Weapon=none; Board=Cutlass Cutthroat#66 1/1, Cutlass Cutthroat#67 1/1; Hand=Sanguine Depths(1), Torch(1), Torch(1), Erupting Volcano(3), Cannonmaster(1)

### Step 9: shared-tree-ismcts-v1

**P1 DISCOVER_PICK Cannonmaster[CAP_107]**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P1 DISCOVER_PICK Cannonmaster[CAP_107]; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "CAP_107", "destination": "hand", "entity": 68, "gifts": [], "kind": "discover_pick", "player": 0, "source": "CAP_105", "turn": 3}`

- P1: HP=30 Armor=0 Mana=0/2 Deck=26; Weapon=none; Board=Cannonmaster#30 3/1, Cutlass Cutthroat#69 1/1, Cutlass Cutthroat#70 1/1; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(8), Cannoneer(1), Cannonmaster(1)
- P2: HP=27 Armor=0 Mana=0/1 Deck=26; Weapon=none; Board=Cutlass Cutthroat#66 1/1, Cutlass Cutthroat#67 1/1; Hand=Sanguine Depths(1), Torch(1), Torch(1), Erupting Volcano(3), Cannonmaster(1)

### Step 10: shared-tree-ismcts-v1

**P1 ATTACK Cutlass Cutthroat#69 -> P2 Cutlass Cutthroat#66**

Legal actions: 5; Searched nodes: 5; Selected value: 0.2230

Top choices by root visit share:

- `0.250` — P1 ATTACK Cutlass Cutthroat#69 -> P2 Cutlass Cutthroat#66 [SELECTED]; Q=0.2230; prior=0.0000
- `0.250` — P1 ATTACK Cutlass Cutthroat#70 -> P2 Cutlass Cutthroat#67; Q=0.1503; prior=0.0000
- `0.250` — P1 ATTACK Cutlass Cutthroat#69 -> P2 Cutlass Cutthroat#67; Q=0.0320; prior=0.0000
- `0.250` — P1 ATTACK Cutlass Cutthroat#70 -> P2 Cutlass Cutthroat#66; Q=0.0320; prior=0.0000
- `0.000` — P1 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "CAP_105t", "entity": 69, "kind": "minion_died", "player": 0, "turn": 3}`
- `{"card": "CAP_105t", "entity": 66, "kind": "minion_died", "player": 1, "turn": 3}`

- P1: HP=30 Armor=0 Mana=0/2 Deck=26; Weapon=none; Board=Cannonmaster#30 3/1, Cutlass Cutthroat#70 1/1; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(8), Cannoneer(1), Cannonmaster(1)
- P2: HP=27 Armor=0 Mana=0/1 Deck=26; Weapon=none; Board=Cutlass Cutthroat#67 1/1; Hand=Sanguine Depths(1), Torch(1), Torch(1), Erupting Volcano(3), Cannonmaster(1)

### Step 11: shared-tree-ismcts-v1

**P1 ATTACK Cutlass Cutthroat#70 -> P2 Cutlass Cutthroat#67**

Legal actions: 2; Searched nodes: 5; Selected value: 0.1106

Top choices by root visit share:

- `0.750` — P1 ATTACK Cutlass Cutthroat#70 -> P2 Cutlass Cutthroat#67 [SELECTED]; Q=0.1106; prior=0.0000
- `0.250` — P1 END_TURN; Q=-0.1391; prior=0.0000

Resolved events:

- `{"card": "CAP_105t", "entity": 70, "kind": "minion_died", "player": 0, "turn": 3}`
- `{"card": "CAP_105t", "entity": 67, "kind": "minion_died", "player": 1, "turn": 3}`

- P1: HP=30 Armor=0 Mana=0/2 Deck=26; Weapon=none; Board=Cannonmaster#30 3/1; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(8), Cannoneer(1), Cannonmaster(1)
- P2: HP=27 Armor=0 Mana=0/1 Deck=26; Weapon=none; Board=empty; Hand=Sanguine Depths(1), Torch(1), Torch(1), Erupting Volcano(3), Cannonmaster(1)

## Turn 4

### Step 12: shared-tree-ismcts-v1

**P1 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P1 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 0, "turn": 3}`
- `{"card": "CATA_582", "kind": "draw", "player": 1, "turn": 4}`
- `{"kind": "turn_start", "player": 1, "turn": 4}`

- P1: HP=30 Armor=0 Mana=0/2 Deck=26; Weapon=none; Board=Cannonmaster#30 3/1; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(8), Cannoneer(1), Cannonmaster(1)
- P2: HP=27 Armor=0 Mana=2/2 Deck=25; Weapon=none; Board=empty; Hand=Sanguine Depths(1), Torch(1), Torch(1), Erupting Volcano(3), Cannonmaster(1), Searing Fissure(2)

### Step 13: policy-prior-puct-v1

**P2 PLAY Cannonmaster[CAP_107] -> -**

Legal actions: 5; Searched nodes: 5; Selected value: -0.0109

Top choices by root visit share:

- `0.250` — P2 PLAY Cannonmaster[CAP_107] -> - [SELECTED]; Q=-0.0109; prior=0.2178
- `0.250` — P2 PLAY Searing Fissure[CATA_582] -> -; Q=-0.2479; prior=0.1871
- `0.250` — P2 END_TURN; Q=-0.5982; prior=0.2553
- `0.250` — P2 HERO_POWER Armor Up; Q=-0.6719; prior=0.2251
- `0.000` — P2 PLAY Sanguine Depths[CORE_REV_990] -> -; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "CAP_107", "controller": 1, "created_by": "CAP_105", "entity": 65, "kind": "play", "player": 1, "started_in_deck": false, "turn": 4}`
- `{"card": "CAP_107t", "entity": 71, "kind": "generated_to_hand", "player": 1, "source": "CAP_107", "turn": 4}`

- P1: HP=30 Armor=0 Mana=0/2 Deck=26; Weapon=none; Board=Cannonmaster#30 3/1; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(8), Cannoneer(1), Cannonmaster(1)
- P2: HP=27 Armor=0 Mana=1/2 Deck=25; Weapon=none; Board=Cannonmaster#65 3/1; Hand=Sanguine Depths(1), Torch(1), Torch(1), Erupting Volcano(3), Searing Fissure(2), Cannoneer(1)

### Step 14: policy-prior-puct-v1

**P2 PLAY Cannoneer[CAP_107t] -> -**

Legal actions: 3; Searched nodes: 5; Selected value: -0.0523

Top choices by root visit share:

- `0.500` — P2 PLAY Cannoneer[CAP_107t] -> - [SELECTED]; Q=-0.0523; prior=0.5150
- `0.250` — P2 PLAY Sanguine Depths[CORE_REV_990] -> -; Q=-0.4960; prior=0.2452
- `0.250` — P2 END_TURN; Q=-0.5317; prior=0.2398

Resolved events:

- `{"card": "CAP_107t", "controller": 1, "created_by": "CAP_107", "entity": 71, "kind": "play", "player": 1, "started_in_deck": false, "turn": 4}`

- P1: HP=30 Armor=0 Mana=0/2 Deck=26; Weapon=none; Board=Cannonmaster#30 3/1; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(8), Cannoneer(1), Cannonmaster(1)
- P2: HP=27 Armor=0 Mana=0/2 Deck=25; Weapon=none; Board=Cannonmaster#65 3/1, Cannoneer#71 1/1; Hand=Sanguine Depths(1), Torch(1), Torch(1), Erupting Volcano(3), Searing Fissure(2)

## Turn 5

### Step 15: policy-prior-puct-v1

**P2 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P2 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 1, "turn": 4}`
- `{"card": "TIME_034", "kind": "draw", "player": 0, "turn": 5}`
- `{"kind": "turn_start", "player": 0, "turn": 5}`

- P1: HP=29 Armor=0 Mana=3/3 Deck=25; Weapon=none; Board=Cannonmaster#30 3/1; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(8), Cannoneer(1), Cannonmaster(1), Stadium Announcer(4)
- P2: HP=27 Armor=0 Mana=0/2 Deck=25; Weapon=none; Board=Cannonmaster#65 3/1, Cannoneer#71 1/1; Hand=Sanguine Depths(1), Torch(1), Torch(1), Erupting Volcano(3), Searing Fissure(2)

### Step 16: shared-tree-ismcts-v1

**P1 ATTACK Cannonmaster#30 -> P2 hero**

Legal actions: 7; Searched nodes: 5; Selected value: 0.5527

Top choices by root visit share:

- `0.250` — P1 ATTACK Cannonmaster#30 -> P2 hero [SELECTED]; Q=0.5527; prior=0.0000
- `0.250` — P1 ATTACK Cannonmaster#30 -> P2 Cannonmaster#65; Q=0.4226; prior=0.0000
- `0.250` — P1 PLAY Cannonmaster[CAP_107] -> -; Q=0.4226; prior=0.0000
- `0.250` — P1 ATTACK Cannonmaster#30 -> P2 Cannoneer#71; Q=0.3285; prior=0.0000
- `0.000` — P1 END_TURN; Q=0.0000; prior=0.0000

- P1: HP=29 Armor=0 Mana=3/3 Deck=25; Weapon=none; Board=Cannonmaster#30 3/1; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(8), Cannoneer(1), Cannonmaster(1), Stadium Announcer(4)
- P2: HP=24 Armor=0 Mana=0/2 Deck=25; Weapon=none; Board=Cannonmaster#65 3/1, Cannoneer#71 1/1; Hand=Sanguine Depths(1), Torch(1), Torch(1), Erupting Volcano(3), Searing Fissure(2)

### Step 17: shared-tree-ismcts-v1

**P1 PLAY Cannoneer[CAP_107t] -> -**

Legal actions: 4; Searched nodes: 5; Selected value: 0.6148

Top choices by root visit share:

- `0.250` — P1 PLAY Cannoneer[CAP_107t] -> - [SELECTED]; Q=0.6148; prior=0.0000
- `0.250` — P1 PLAY Cannonmaster[CAP_107] -> -; Q=0.6148; prior=0.0000
- `0.250` — P1 HERO_POWER Armor Up; Q=0.3799; prior=0.0000
- `0.250` — P1 END_TURN; Q=-0.0985; prior=0.0000

Resolved events:

- `{"card": "CAP_107t", "controller": 0, "created_by": "CAP_107", "entity": 64, "kind": "play", "player": 0, "started_in_deck": false, "turn": 5}`

- P1: HP=29 Armor=0 Mana=2/3 Deck=25; Weapon=none; Board=Cannonmaster#30 3/1, Cannoneer#64 1/1; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(8), Cannonmaster(1), Stadium Announcer(4)
- P2: HP=24 Armor=0 Mana=0/2 Deck=25; Weapon=none; Board=Cannonmaster#65 3/1, Cannoneer#71 1/1; Hand=Sanguine Depths(1), Torch(1), Torch(1), Erupting Volcano(3), Searing Fissure(2)

### Step 18: shared-tree-ismcts-v1

**P1 PLAY Cannonmaster[CAP_107] -> -**

Legal actions: 3; Searched nodes: 5; Selected value: 0.5419

Top choices by root visit share:

- `0.500` — P1 PLAY Cannonmaster[CAP_107] -> - [SELECTED]; Q=0.5419; prior=0.0000
- `0.250` — P1 HERO_POWER Armor Up; Q=0.4113; prior=0.0000
- `0.250` — P1 END_TURN; Q=0.2247; prior=0.0000

Resolved events:

- `{"card": "CAP_107", "controller": 0, "created_by": "CAP_105", "entity": 68, "kind": "play", "player": 0, "started_in_deck": false, "turn": 5}`
- `{"card": "CAP_107t", "entity": 72, "kind": "generated_to_hand", "player": 0, "source": "CAP_107", "turn": 5}`

- P1: HP=29 Armor=0 Mana=1/3 Deck=25; Weapon=none; Board=Cannonmaster#30 3/1, Cannoneer#64 1/1, Cannonmaster#68 3/1; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(8), Stadium Announcer(4), Cannoneer(1)
- P2: HP=24 Armor=0 Mana=0/2 Deck=25; Weapon=none; Board=Cannonmaster#65 3/1, Cannoneer#71 1/1; Hand=Sanguine Depths(1), Torch(1), Torch(1), Erupting Volcano(3), Searing Fissure(2)

### Step 19: shared-tree-ismcts-v1

**P1 PLAY Cannoneer[CAP_107t] -> -**

Legal actions: 2; Searched nodes: 5; Selected value: 0.3954

Top choices by root visit share:

- `0.500` — P1 PLAY Cannoneer[CAP_107t] -> - [SELECTED]; Q=0.3954; prior=0.0000
- `0.500` — P1 END_TURN; Q=0.2015; prior=0.0000

Resolved events:

- `{"card": "CAP_107t", "controller": 0, "created_by": "CAP_107", "entity": 72, "kind": "play", "player": 0, "started_in_deck": false, "turn": 5}`

- P1: HP=29 Armor=0 Mana=0/3 Deck=25; Weapon=none; Board=Cannonmaster#30 3/1, Cannoneer#64 1/1, Cannonmaster#68 3/1, Cannoneer#72 1/1; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(8), Stadium Announcer(4)
- P2: HP=24 Armor=0 Mana=0/2 Deck=25; Weapon=none; Board=Cannonmaster#65 3/1, Cannoneer#71 1/1; Hand=Sanguine Depths(1), Torch(1), Torch(1), Erupting Volcano(3), Searing Fissure(2)

## Turn 6

### Step 20: shared-tree-ismcts-v1

**P1 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P1 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 0, "turn": 5}`
- `{"card": "END_033", "kind": "draw", "player": 1, "turn": 6}`
- `{"kind": "turn_start", "player": 1, "turn": 6}`

- P1: HP=29 Armor=0 Mana=0/3 Deck=25; Weapon=none; Board=Cannonmaster#30 3/1, Cannoneer#64 1/1, Cannonmaster#68 3/1, Cannoneer#72 1/1; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(8), Stadium Announcer(4)
- P2: HP=22 Armor=0 Mana=3/3 Deck=24; Weapon=none; Board=Cannonmaster#65 3/1, Cannoneer#71 1/1; Hand=Sanguine Depths(1), Torch(1), Torch(1), Erupting Volcano(3), Searing Fissure(2), Prescient Slitherdrake(7)

### Step 21: policy-prior-puct-v1

**P2 PLAY Searing Fissure[CATA_582] -> -**

Legal actions: 15; Searched nodes: 5; Selected value: -0.2436

Top choices by root visit share:

- `0.250` — P2 PLAY Searing Fissure[CATA_582] -> - [SELECTED]; Q=-0.2436; prior=0.0727
- `0.250` — P2 ATTACK Cannonmaster#65 -> P1 hero; Q=-0.4426; prior=0.0988
- `0.250` — P2 ATTACK Cannoneer#71 -> P1 hero; Q=-0.5198; prior=0.0757
- `0.250` — P2 ATTACK Cannonmaster#65 -> P1 Cannoneer#72; Q=-0.6391; prior=0.0736
- `0.000` — P2 ATTACK Cannonmaster#65 -> P1 Cannonmaster#30; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "CATA_582", "controller": 1, "created_by": null, "entity": 50, "kind": "play", "player": 1, "started_in_deck": true, "turn": 6}`
- `{"card": "CAP_107", "entity": 30, "kind": "minion_died", "player": 0, "turn": 6}`
- `{"card": "CAP_107t", "entity": 64, "kind": "minion_died", "player": 0, "turn": 6}`
- `{"card": "CAP_107", "entity": 68, "kind": "minion_died", "player": 0, "turn": 6}`
- `{"card": "CAP_107t", "entity": 72, "kind": "minion_died", "player": 0, "turn": 6}`
- `{"card": "CAP_107", "entity": 65, "kind": "minion_died", "player": 1, "turn": 6}`
- `{"card": "CAP_107t", "entity": 71, "kind": "minion_died", "player": 1, "turn": 6}`

- P1: HP=29 Armor=0 Mana=0/3 Deck=25; Weapon=none; Board=empty; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(8), Stadium Announcer(4)
- P2: HP=22 Armor=0 Mana=1/3 Deck=24; Weapon=none; Board=empty; Hand=Sanguine Depths(1), Torch(1), Torch(1), Erupting Volcano(3), Prescient Slitherdrake(7)

### Step 22: policy-prior-puct-v1

**P2 HERO_ATTACK -> P1 hero**

Legal actions: 3; Searched nodes: 5; Selected value: -0.2678

Top choices by root visit share:

- `0.500` — P2 HERO_ATTACK -> P1 hero [SELECTED]; Q=-0.2678; prior=0.2794
- `0.250` — P2 PLAY Sanguine Depths[CORE_REV_990] -> -; Q=-0.5379; prior=0.2090
- `0.250` — P2 END_TURN; Q=-0.7334; prior=0.5117

- P1: HP=26 Armor=0 Mana=0/3 Deck=25; Weapon=none; Board=empty; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(8), Stadium Announcer(4)
- P2: HP=22 Armor=0 Mana=1/3 Deck=24; Weapon=none; Board=empty; Hand=Sanguine Depths(1), Torch(1), Torch(1), Erupting Volcano(3), Prescient Slitherdrake(7)

## Turn 7

### Step 23: policy-prior-puct-v1

**P2 END_TURN**

Legal actions: 2; Searched nodes: 5; Selected value: -0.4338

Top choices by root visit share:

- `0.750` — P2 END_TURN [SELECTED]; Q=-0.4338; prior=0.7072
- `0.250` — P2 PLAY Sanguine Depths[CORE_REV_990] -> -; Q=-0.7604; prior=0.2928

Resolved events:

- `{"kind": "turn_end", "player": 1, "turn": 6}`
- `{"card": "EDR_492", "kind": "draw", "player": 0, "turn": 7}`
- `{"kind": "turn_start", "player": 0, "turn": 7}`

- P1: HP=26 Armor=0 Mana=4/4 Deck=24; Weapon=none; Board=empty; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(8), Stadium Announcer(4), Mother Duck(4)
- P2: HP=22 Armor=0 Mana=1/3 Deck=24; Weapon=none; Board=empty; Hand=Sanguine Depths(1), Torch(1), Torch(1), Erupting Volcano(3), Prescient Slitherdrake(7)

### Step 24: shared-tree-ismcts-v1

**P1 PLAY Stadium Announcer[TIME_034] -> -**

Legal actions: 4; Searched nodes: 5; Selected value: 0.6697

Top choices by root visit share:

- `0.250` — P1 PLAY Stadium Announcer[TIME_034] -> - [SELECTED]; Q=0.6697; prior=0.0000
- `0.250` — P1 PLAY Mother Duck[EDR_492] -> -; Q=0.5063; prior=0.0000
- `0.250` — P1 END_TURN; Q=-0.3162; prior=0.0000
- `0.250` — P1 HERO_POWER Armor Up; Q=-0.4017; prior=0.0000

Resolved events:

- `{"card": "TIME_034", "controller": 0, "created_by": null, "entity": 13, "kind": "play", "player": 0, "started_in_deck": true, "turn": 7}`
- `{"attack": 2, "card": "EDR_812", "durability": 2, "kind": "equip_weapon", "player": 0, "turn": 7}`
- `{"attack": 2, "card": "DINO_408", "durability": 2, "kind": "equip_weapon", "player": 1, "turn": 7}`
- `{"effect": "stadium_weapons", "kind": "rewind_offer", "outcome": [{"attack": 3, "card": "EDR_812", "durability": 3, "name": "Grotesque Runeblade"}, {"attack": 2, "card": "DINO_408", "durability": 2, "name": "Crystal Tusk"}], "player": 0, "restorable": true, "turn": 7}`

- P1: HP=26 Armor=0 Mana=0/4 Deck=24; Weapon=Grotesque Runeblade 3/3; Board=Stadium Announcer#13 3/3; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(8), Mother Duck(4)
- P2: HP=22 Armor=0 Mana=1/3 Deck=24; Weapon=Crystal Tusk 2/2; Board=empty; Hand=Sanguine Depths(1), Torch(1), Torch(1), Erupting Volcano(3), Prescient Slitherdrake(7)

### Step 25: shared-tree-ismcts-v1

**P1 REWIND_RETRY**

Legal actions: 2; Searched nodes: 5; Selected value: 0.6148

Top choices by root visit share:

- `0.750` — P1 REWIND_RETRY [SELECTED]; Q=0.6148; prior=0.0000
- `0.250` — P1 REWIND_KEEP; Q=0.7438; prior=0.0000

Resolved events:

- `{"attack": 4, "card": "EDR_253", "durability": 2, "kind": "equip_weapon", "player": 0, "turn": 7}`
- `{"attack": 2, "card": "EDR_842", "durability": 3, "kind": "equip_weapon", "player": 1, "turn": 7}`
- `{"decision": "retry", "effect": "stadium_weapons", "kind": "rewind_pick", "outcome": [{"attack": 5, "card": "EDR_253", "durability": 3, "name": "Ursine Maul"}, {"attack": 2, "card": "EDR_842", "durability": 3, "name": "Defiled Spear"}], "player": 0, "turn": 7}`

- P1: HP=26 Armor=0 Mana=0/4 Deck=24; Weapon=Ursine Maul 5/3; Board=Stadium Announcer#13 3/3; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(8), Mother Duck(4)
- P2: HP=22 Armor=0 Mana=1/3 Deck=24; Weapon=Defiled Spear 2/3; Board=empty; Hand=Sanguine Depths(1), Torch(1), Torch(1), Erupting Volcano(3), Prescient Slitherdrake(7)

### Step 26: shared-tree-ismcts-v1

**P1 HERO_ATTACK -> P2 hero**

Legal actions: 2; Searched nodes: 5; Selected value: 0.5709

Top choices by root visit share:

- `0.750` — P1 HERO_ATTACK -> P2 hero [SELECTED]; Q=0.5709; prior=0.0000
- `0.250` — P1 END_TURN; Q=0.3824; prior=0.0000

Resolved events:

- `{"card": "CATA_556", "kind": "draw", "player": 0, "turn": 7}`

- P1: HP=26 Armor=0 Mana=0/4 Deck=23; Weapon=Ursine Maul 5/2; Board=Stadium Announcer#13 3/3; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(8), Mother Duck(4), Carrier Whelp(1)
- P2: HP=17 Armor=0 Mana=1/3 Deck=24; Weapon=Defiled Spear 2/3; Board=empty; Hand=Sanguine Depths(1), Torch(1), Torch(1), Erupting Volcano(3), Prescient Slitherdrake(7)

## Turn 8

### Step 27: shared-tree-ismcts-v1

**P1 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P1 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 0, "turn": 7}`
- `{"card": "CATA_556", "kind": "draw", "player": 1, "turn": 8}`
- `{"kind": "turn_start", "player": 1, "turn": 8}`

- P1: HP=26 Armor=0 Mana=0/4 Deck=23; Weapon=Ursine Maul 5/2; Board=Stadium Announcer#13 3/3; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(5), Mother Duck(4), Carrier Whelp(1)
- P2: HP=17 Armor=0 Mana=4/4 Deck=23; Weapon=Defiled Spear 2/3; Board=empty; Hand=Sanguine Depths(1), Torch(1), Torch(1), Erupting Volcano(3), Prescient Slitherdrake(4), Carrier Whelp(1)

### Step 28: policy-prior-puct-v1

**P2 PLAY Prescient Slitherdrake[END_033] -> -**

Legal actions: 8; Searched nodes: 5; Selected value: -0.0673

Top choices by root visit share:

- `0.250` — P2 PLAY Prescient Slitherdrake[END_033] -> - [SELECTED]; Q=-0.0673; prior=0.1226
- `0.250` — P2 PLAY Carrier Whelp[CATA_556] -> -; Q=-0.3567; prior=0.1730
- `0.250` — P2 HERO_POWER Armor Up; Q=-0.3940; prior=0.2123
- `0.250` — P2 END_TURN; Q=-0.9770; prior=0.1876
- `0.000` — P2 HERO_ATTACK -> P1 hero; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "END_033", "controller": 1, "created_by": null, "entity": 46, "kind": "play", "player": 1, "started_in_deck": true, "turn": 8}`

- P1: HP=26 Armor=0 Mana=0/4 Deck=23; Weapon=Ursine Maul 5/2; Board=Stadium Announcer#13 3/3; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(5), Mother Duck(4), Carrier Whelp(1)
- P2: HP=17 Armor=0 Mana=0/4 Deck=23; Weapon=Defiled Spear 2/3; Board=Prescient Slitherdrake#46 5/8; Hand=Sanguine Depths(1), Torch(1), Torch(1), Erupting Volcano(3), Carrier Whelp(1)

## Turn 9

### Step 29: policy-prior-puct-v1

**P2 END_TURN**

Legal actions: 3; Searched nodes: 5; Selected value: -0.6235

Top choices by root visit share:

- `0.500` — P2 END_TURN [SELECTED]; Q=-0.6235; prior=0.4791
- `0.250` — P2 HERO_ATTACK -> P1 hero; Q=-0.1753; prior=0.3220
- `0.250` — P2 HERO_ATTACK -> P1 Stadium Announcer#13; Q=-0.3351; prior=0.1990

Resolved events:

- `{"kind": "turn_end", "player": 1, "turn": 8}`
- `{"card": "TLC_600", "kind": "draw", "player": 0, "turn": 9}`
- `{"kind": "turn_start", "player": 0, "turn": 9}`

- P1: HP=26 Armor=0 Mana=5/5 Deck=22; Weapon=Ursine Maul 5/2; Board=Stadium Announcer#13 3/3; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(5), Mother Duck(4), Carrier Whelp(1), Windpeak Wyrm(5)
- P2: HP=17 Armor=0 Mana=0/4 Deck=23; Weapon=Defiled Spear 2/3; Board=Prescient Slitherdrake#46 5/8; Hand=Sanguine Depths(1), Torch(1), Torch(1), Erupting Volcano(3), Carrier Whelp(1)

### Step 30: shared-tree-ismcts-v1

**P1 ATTACK Stadium Announcer#13 -> P2 hero**

Legal actions: 16; Searched nodes: 5; Selected value: 0.9542

Top choices by root visit share:

- `0.250` — P1 ATTACK Stadium Announcer#13 -> P2 hero [SELECTED]; Q=0.9542; prior=0.0000
- `0.250` — P1 HERO_ATTACK -> P2 hero; Q=0.9538; prior=0.0000
- `0.250` — P1 ATTACK Stadium Announcer#13 -> P2 Prescient Slitherdrake#46; Q=0.9196; prior=0.0000
- `0.250` — P1 HERO_ATTACK -> P2 Prescient Slitherdrake#46; Q=0.9196; prior=0.0000
- `0.000` — P1 END_TURN; Q=0.0000; prior=0.0000

- P1: HP=26 Armor=0 Mana=5/5 Deck=22; Weapon=Ursine Maul 5/2; Board=Stadium Announcer#13 3/3; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(5), Mother Duck(4), Carrier Whelp(1), Windpeak Wyrm(5)
- P2: HP=14 Armor=0 Mana=0/4 Deck=23; Weapon=Defiled Spear 2/3; Board=Prescient Slitherdrake#46 5/8; Hand=Sanguine Depths(1), Torch(1), Torch(1), Erupting Volcano(3), Carrier Whelp(1)

### Step 31: shared-tree-ismcts-v1

**P1 PLAY Windpeak Wyrm[TLC_600] -> P2 Prescient Slitherdrake#46**

Legal actions: 14; Searched nodes: 5; Selected value: 0.9694

Top choices by root visit share:

- `0.250` — P1 PLAY Windpeak Wyrm[TLC_600] -> P2 Prescient Slitherdrake#46 [SELECTED]; Q=0.9694; prior=0.0000
- `0.250` — P1 HERO_ATTACK -> P2 Prescient Slitherdrake#46; Q=0.9694; prior=0.0000
- `0.250` — P1 PLAY Windpeak Wyrm[TLC_600] -> P2 Prescient Slitherdrake#46; Q=0.9694; prior=0.0000
- `0.250` — P1 HERO_ATTACK -> P2 hero; Q=0.9670; prior=0.0000
- `0.000` — P1 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "TLC_600", "controller": 0, "created_by": null, "entity": 11, "kind": "play", "player": 0, "started_in_deck": true, "turn": 9}`
- `{"amount": 5, "kind": "gain_armor", "player": 0, "turn": 9}`

- P1: HP=26 Armor=5 Mana=0/5 Deck=22; Weapon=Ursine Maul 5/2; Board=Stadium Announcer#13 3/3, Windpeak Wyrm#11 6/6; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(5), Mother Duck(4), Carrier Whelp(1)
- P2: HP=14 Armor=0 Mana=0/4 Deck=23; Weapon=Defiled Spear 2/3; Board=Prescient Slitherdrake#46 5/3; Hand=Sanguine Depths(1), Torch(1), Torch(1), Erupting Volcano(3), Carrier Whelp(1)

## Turn 10

### Step 32: shared-tree-ismcts-v1

**P1 END_TURN**

Legal actions: 3; Searched nodes: 5; Selected value: 0.8482

Top choices by root visit share:

- `0.500` — P1 END_TURN [SELECTED]; Q=0.8482; prior=0.0000
- `0.250` — P1 HERO_ATTACK -> P2 hero; Q=0.9780; prior=0.0000
- `0.250` — P1 HERO_ATTACK -> P2 Prescient Slitherdrake#46; Q=0.8721; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 0, "turn": 9}`
- `{"card": "EDR_456", "kind": "draw", "player": 1, "turn": 10}`
- `{"kind": "turn_start", "player": 1, "turn": 10}`

- P1: HP=26 Armor=5 Mana=0/5 Deck=22; Weapon=Ursine Maul 5/2; Board=Stadium Announcer#13 3/3, Windpeak Wyrm#11 6/6; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(5), Mother Duck(4), Carrier Whelp(1)
- P2: HP=14 Armor=0 Mana=5/5 Deck=22; Weapon=Defiled Spear 2/3; Board=Prescient Slitherdrake#46 5/3; Hand=Sanguine Depths(1), Torch(1), Torch(1), Erupting Volcano(3), Carrier Whelp(1), Darkrider(1)

### Step 33: policy-prior-puct-v1

**P2 PLAY Carrier Whelp[CATA_556] -> -**

Legal actions: 14; Searched nodes: 5; Selected value: -0.8209

Top choices by root visit share:

- `0.250` — P2 PLAY Carrier Whelp[CATA_556] -> - [SELECTED]; Q=-0.8209; prior=0.0849
- `0.250` — P2 HERO_POWER Armor Up; Q=-0.8345; prior=0.1140
- `0.250` — P2 PLAY Darkrider[EDR_456] -> -; Q=-0.9591; prior=0.1096
- `0.250` — P2 END_TURN; Q=-0.9840; prior=0.1180
- `0.000` — P2 ATTACK Prescient Slitherdrake#46 -> P1 hero; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "CATA_556", "controller": 1, "created_by": null, "entity": 48, "kind": "play", "player": 1, "started_in_deck": true, "turn": 10}`
- `{"card": "CATA_556", "entity": 73, "kind": "generated_to_hand", "player": 1, "source": "CATA_556", "turn": 10}`

- P1: HP=26 Armor=5 Mana=0/5 Deck=22; Weapon=Ursine Maul 5/2; Board=Stadium Announcer#13 3/3, Windpeak Wyrm#11 6/6; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(5), Mother Duck(4), Carrier Whelp(1)
- P2: HP=14 Armor=0 Mana=4/5 Deck=22; Weapon=Defiled Spear 2/3; Board=Prescient Slitherdrake#46 5/3, Carrier Whelp#48 1/2; Hand=Sanguine Depths(1), Torch(1), Torch(1), Erupting Volcano(3), Darkrider(1), Carrier Whelp(1)

### Step 34: policy-prior-puct-v1

**P2 HERO_POWER Armor Up**

Legal actions: 14; Searched nodes: 5; Selected value: -0.7799

Top choices by root visit share:

- `0.250` — P2 HERO_POWER Armor Up [SELECTED]; Q=-0.7799; prior=0.0918
- `0.250` — P2 HERO_ATTACK -> P1 Windpeak Wyrm#11; Q=-0.8909; prior=0.0945
- `0.250` — P2 HERO_ATTACK -> P1 hero; Q=-0.9030; prior=0.0831
- `0.250` — P2 END_TURN; Q=-0.9760; prior=0.1086
- `0.000` — P2 ATTACK Prescient Slitherdrake#46 -> P1 hero; Q=0.0000; prior=0.0000

Resolved events:

- `{"amount": 2, "kind": "gain_armor", "player": 1, "turn": 10}`
- `{"kind": "hero_power", "player": 1, "turn": 10}`

- P1: HP=26 Armor=5 Mana=0/5 Deck=22; Weapon=Ursine Maul 5/2; Board=Stadium Announcer#13 3/3, Windpeak Wyrm#11 6/6; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(5), Mother Duck(4), Carrier Whelp(1)
- P2: HP=14 Armor=2 Mana=2/5 Deck=22; Weapon=Defiled Spear 2/3; Board=Prescient Slitherdrake#46 5/3, Carrier Whelp#48 1/2; Hand=Sanguine Depths(1), Torch(1), Torch(1), Erupting Volcano(3), Darkrider(1), Carrier Whelp(1)

### Step 35: policy-prior-puct-v1

**P2 PLAY Carrier Whelp[CATA_556] -> -**

Legal actions: 12; Searched nodes: 5; Selected value: -0.7101

Top choices by root visit share:

- `0.250` — P2 PLAY Carrier Whelp[CATA_556] -> - [SELECTED]; Q=-0.7101; prior=0.1528
- `0.250` — P2 HERO_ATTACK -> P1 Windpeak Wyrm#11; Q=-0.8125; prior=0.0873
- `0.250` — P2 PLAY Darkrider[EDR_456] -> -; Q=-0.9305; prior=0.1419
- `0.250` — P2 END_TURN; Q=-0.9699; prior=0.0839
- `0.000` — P2 ATTACK Prescient Slitherdrake#46 -> P1 hero; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "CATA_556", "controller": 1, "created_by": "CATA_556", "entity": 73, "kind": "play", "player": 1, "started_in_deck": false, "turn": 10}`
- `{"card": "CATA_556", "entity": 74, "kind": "generated_to_hand", "player": 1, "source": "CATA_556", "turn": 10}`

- P1: HP=26 Armor=5 Mana=0/5 Deck=22; Weapon=Ursine Maul 5/2; Board=Stadium Announcer#13 3/3, Windpeak Wyrm#11 6/6; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(5), Mother Duck(4), Carrier Whelp(1)
- P2: HP=14 Armor=2 Mana=1/5 Deck=22; Weapon=Defiled Spear 2/3; Board=Prescient Slitherdrake#46 5/3, Carrier Whelp#48 1/2, Carrier Whelp#73 1/2; Hand=Sanguine Depths(1), Torch(1), Torch(1), Erupting Volcano(3), Darkrider(1), Carrier Whelp(1)

### Step 36: policy-prior-puct-v1

**P2 ATTACK Prescient Slitherdrake#46 -> P1 hero**

Legal actions: 12; Searched nodes: 5; Selected value: -0.3877

Top choices by root visit share:

- `0.250` — P2 ATTACK Prescient Slitherdrake#46 -> P1 hero [SELECTED]; Q=-0.3877; prior=0.0848
- `0.250` — P2 HERO_ATTACK -> P1 Windpeak Wyrm#11; Q=-0.8192; prior=0.0907
- `0.250` — P2 PLAY Carrier Whelp[CATA_556] -> -; Q=-0.9034; prior=0.1459
- `0.250` — P2 PLAY Darkrider[EDR_456] -> -; Q=-0.9060; prior=0.1350
- `0.000` — P2 ATTACK Prescient Slitherdrake#46 -> P1 Windpeak Wyrm#11; Q=0.0000; prior=0.0000

- P1: HP=26 Armor=0 Mana=0/5 Deck=22; Weapon=Ursine Maul 5/2; Board=Stadium Announcer#13 3/3, Windpeak Wyrm#11 6/6; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(5), Mother Duck(4), Carrier Whelp(1)
- P2: HP=14 Armor=2 Mana=1/5 Deck=22; Weapon=Defiled Spear 2/3; Board=Prescient Slitherdrake#46 5/3, Carrier Whelp#48 1/2, Carrier Whelp#73 1/2; Hand=Sanguine Depths(1), Torch(1), Torch(1), Erupting Volcano(3), Darkrider(1), Carrier Whelp(1)

### Step 37: policy-prior-puct-v1

**P2 HERO_ATTACK -> P1 Windpeak Wyrm#11**

Legal actions: 9; Searched nodes: 5; Selected value: -0.5692

Top choices by root visit share:

- `0.250` — P2 HERO_ATTACK -> P1 Windpeak Wyrm#11 [SELECTED]; Q=-0.5692; prior=0.1083
- `0.250` — P2 HERO_ATTACK -> P1 hero; Q=-0.6094; prior=0.1037
- `0.250` — P2 PLAY Darkrider[EDR_456] -> -; Q=-0.7724; prior=0.1754
- `0.250` — P2 PLAY Carrier Whelp[CATA_556] -> -; Q=-0.8423; prior=0.1914
- `0.000` — P2 END_TURN; Q=0.0000; prior=0.0000

- P1: HP=24 Armor=0 Mana=0/5 Deck=22; Weapon=Ursine Maul 5/2; Board=Stadium Announcer#13 3/3, Windpeak Wyrm#11 6/4; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(5), Mother Duck(4), Carrier Whelp(1)
- P2: HP=10 Armor=0 Mana=1/5 Deck=22; Weapon=Defiled Spear 2/2; Board=Prescient Slitherdrake#46 5/3, Carrier Whelp#48 1/2, Carrier Whelp#73 1/2; Hand=Sanguine Depths(1), Torch(1), Torch(1), Erupting Volcano(3), Darkrider(1), Carrier Whelp(1)

### Step 38: policy-prior-puct-v1

**P2 PLAY Torch[CATA_585] -> P1 Windpeak Wyrm#11**

Legal actions: 8; Searched nodes: 5; Selected value: -0.6468

Top choices by root visit share:

- `0.250` — P2 PLAY Torch[CATA_585] -> P1 Windpeak Wyrm#11 [SELECTED]; Q=-0.6468; prior=0.2352
- `0.250` — P2 PLAY Torch[CATA_585] -> P1 Windpeak Wyrm#11; Q=-0.6468; prior=0.1386
- `0.250` — P2 PLAY Darkrider[EDR_456] -> -; Q=-0.8574; prior=0.1514
- `0.250` — P2 PLAY Carrier Whelp[CATA_556] -> -; Q=-0.8747; prior=0.1645
- `0.000` — P2 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "CATA_585", "controller": 1, "created_by": null, "entity": 53, "kind": "play", "player": 1, "started_in_deck": true, "turn": 10}`
- `{"card": "CATA_585", "destination": "hand", "entity": 53, "kind": "returned_to_hand", "player": 1, "source": "CATA_585", "turn": 10}`
- `{"card": "TLC_600", "entity": 11, "kind": "minion_died", "player": 0, "turn": 10}`

- P1: HP=24 Armor=0 Mana=0/5 Deck=22; Weapon=Ursine Maul 5/2; Board=Stadium Announcer#13 3/3; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(5), Mother Duck(4), Carrier Whelp(1)
- P2: HP=10 Armor=0 Mana=0/5 Deck=22; Weapon=Defiled Spear 2/2; Board=Prescient Slitherdrake#46 5/3, Carrier Whelp#48 1/2, Carrier Whelp#73 1/2; Hand=Sanguine Depths(1), Torch(1), Erupting Volcano(3), Darkrider(1), Carrier Whelp(1), Torch(1)

## Turn 11

### Step 39: policy-prior-puct-v1

**P2 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P2 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 1, "turn": 10}`
- `{"card": "CORE_SW_066", "kind": "draw", "player": 0, "turn": 11}`
- `{"kind": "turn_start", "player": 0, "turn": 11}`

- P1: HP=24 Armor=0 Mana=6/6 Deck=21; Weapon=Ursine Maul 5/2; Board=Stadium Announcer#13 3/3; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(5), Mother Duck(4), Carrier Whelp(1), Royal Librarian(4)
- P2: HP=10 Armor=0 Mana=0/5 Deck=22; Weapon=Defiled Spear 2/2; Board=Prescient Slitherdrake#46 5/3, Carrier Whelp#48 1/2, Carrier Whelp#73 1/2; Hand=Sanguine Depths(1), Torch(1), Erupting Volcano(3), Darkrider(1), Carrier Whelp(1), Torch(1)

### Step 40: shared-tree-ismcts-v1

**P1 HERO_ATTACK -> P2 Prescient Slitherdrake#46**

Legal actions: 23; Searched nodes: 5; Selected value: 0.9737

Top choices by root visit share:

- `0.250` — P1 HERO_ATTACK -> P2 Prescient Slitherdrake#46 [SELECTED]; Q=0.9737; prior=0.0000
- `0.250` — P1 ATTACK Stadium Announcer#13 -> P2 Carrier Whelp#48; Q=0.9737; prior=0.0000
- `0.250` — P1 ATTACK Stadium Announcer#13 -> P2 Carrier Whelp#73; Q=0.9737; prior=0.0000
- `0.250` — P1 ATTACK Stadium Announcer#13 -> P2 Prescient Slitherdrake#46; Q=0.9653; prior=0.0000
- `0.000` — P1 ATTACK Stadium Announcer#13 -> P2 hero; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "CATA_584", "kind": "draw", "player": 0, "turn": 11}`
- `{"card": "END_033", "entity": 46, "kind": "minion_died", "player": 1, "turn": 11}`

- P1: HP=19 Armor=0 Mana=6/6 Deck=20; Weapon=Ursine Maul 5/1; Board=Stadium Announcer#13 3/3; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(5), Mother Duck(4), Carrier Whelp(1), Royal Librarian(4), Erupting Volcano(3)
- P2: HP=10 Armor=0 Mana=0/5 Deck=22; Weapon=Defiled Spear 2/2; Board=Carrier Whelp#48 1/2, Carrier Whelp#73 1/2; Hand=Sanguine Depths(1), Torch(1), Erupting Volcano(3), Darkrider(1), Carrier Whelp(1), Torch(1)

### Step 41: shared-tree-ismcts-v1

**P1 ATTACK Stadium Announcer#13 -> P2 hero**

Legal actions: 17; Searched nodes: 5; Selected value: 0.9752

Top choices by root visit share:

- `0.250` — P1 ATTACK Stadium Announcer#13 -> P2 hero [SELECTED]; Q=0.9752; prior=0.0000
- `0.250` — P1 ATTACK Stadium Announcer#13 -> P2 Carrier Whelp#48; Q=0.9727; prior=0.0000
- `0.250` — P1 ATTACK Stadium Announcer#13 -> P2 Carrier Whelp#73; Q=0.9727; prior=0.0000
- `0.250` — P1 PLAY Windpeak Wyrm[TLC_600] -> P2 Carrier Whelp#48; Q=0.9727; prior=0.0000
- `0.000` — P1 END_TURN; Q=0.0000; prior=0.0000

- P1: HP=19 Armor=0 Mana=6/6 Deck=20; Weapon=Ursine Maul 5/1; Board=Stadium Announcer#13 3/3; Hand=Torch(1), Chainbreaker Hogger(8), Windpeak Wyrm(5), Mother Duck(4), Carrier Whelp(1), Royal Librarian(4), Erupting Volcano(3)
- P2: HP=7 Armor=0 Mana=0/5 Deck=22; Weapon=Defiled Spear 2/2; Board=Carrier Whelp#48 1/2, Carrier Whelp#73 1/2; Hand=Sanguine Depths(1), Torch(1), Erupting Volcano(3), Darkrider(1), Carrier Whelp(1), Torch(1)

### Step 42: shared-tree-ismcts-v1

**P1 PLAY Windpeak Wyrm[TLC_600] -> P2 hero**

Legal actions: 14; Searched nodes: 5; Selected value: 0.9731

Top choices by root visit share:

- `0.250` — P1 PLAY Windpeak Wyrm[TLC_600] -> P2 hero [SELECTED]; Q=0.9731; prior=0.0000
- `0.250` — P1 PLAY Windpeak Wyrm[TLC_600] -> P2 Carrier Whelp#48; Q=0.9653; prior=0.0000
- `0.250` — P1 PLAY Windpeak Wyrm[TLC_600] -> P2 Carrier Whelp#73; Q=0.9653; prior=0.0000
- `0.250` — P1 PLAY Royal Librarian[CORE_SW_066] -> P2 Carrier Whelp#48; Q=0.9197; prior=0.0000
- `0.000` — P1 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "TLC_600", "controller": 0, "created_by": null, "entity": 12, "kind": "play", "player": 0, "started_in_deck": true, "turn": 11}`
- `{"amount": 5, "kind": "gain_armor", "player": 0, "turn": 11}`

- P1: HP=19 Armor=5 Mana=1/6 Deck=20; Weapon=Ursine Maul 5/1; Board=Stadium Announcer#13 3/3, Windpeak Wyrm#12 6/6; Hand=Torch(1), Chainbreaker Hogger(8), Mother Duck(4), Carrier Whelp(1), Royal Librarian(4), Erupting Volcano(3)
- P2: HP=2 Armor=0 Mana=0/5 Deck=22; Weapon=Defiled Spear 2/2; Board=Carrier Whelp#48 1/2, Carrier Whelp#73 1/2; Hand=Sanguine Depths(1), Torch(1), Erupting Volcano(3), Darkrider(1), Carrier Whelp(1), Torch(1)

## Turn 12

### Step 43: shared-tree-ismcts-v1

**P1 END_TURN**

Legal actions: 2; Searched nodes: 5; Selected value: 1.0000

Top choices by root visit share:

- `0.750` — P1 END_TURN [SELECTED]; Q=1.0000; prior=0.0000
- `0.250` — P1 PLAY Carrier Whelp[CATA_556] -> -; Q=0.9789; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 0, "turn": 11}`
- `{"card": "EDR_492", "kind": "draw", "player": 1, "turn": 12}`
- `{"kind": "turn_start", "player": 1, "turn": 12}`

- P1: HP=19 Armor=5 Mana=1/6 Deck=20; Weapon=Ursine Maul 5/1; Board=Stadium Announcer#13 3/3, Windpeak Wyrm#12 6/6; Hand=Torch(1), Chainbreaker Hogger(8), Mother Duck(4), Carrier Whelp(1), Royal Librarian(4), Erupting Volcano(3)
- P2: HP=2 Armor=0 Mana=6/6 Deck=21; Weapon=Defiled Spear 2/2; Board=Carrier Whelp#48 1/2, Carrier Whelp#73 1/2; Hand=Sanguine Depths(1), Torch(1), Erupting Volcano(3), Darkrider(1), Carrier Whelp(1), Torch(1), Mother Duck(4)

### Step 44: policy-prior-puct-v1

**P2 HERO_ATTACK -> P1 hero**

Legal actions: 16; Searched nodes: 5; Selected value: -0.8310

Top choices by root visit share:

- `0.250` — P2 HERO_ATTACK -> P1 hero [SELECTED]; Q=-0.8310; prior=0.0796
- `0.250` — P2 ATTACK Carrier Whelp#73 -> P1 Windpeak Wyrm#12; Q=-1.0000; prior=0.0800
- `0.250` — P2 HERO_ATTACK -> P1 Windpeak Wyrm#12; Q=-1.0000; prior=0.1055
- `0.250` — P2 HERO_ATTACK -> P1 Stadium Announcer#13; Q=-1.0000; prior=0.0756
- `0.000` — P2 ATTACK Carrier Whelp#48 -> P1 hero; Q=0.0000; prior=0.0000

- P1: HP=19 Armor=3 Mana=1/6 Deck=20; Weapon=Ursine Maul 5/1; Board=Stadium Announcer#13 3/1, Windpeak Wyrm#12 6/6; Hand=Torch(1), Chainbreaker Hogger(8), Mother Duck(4), Carrier Whelp(1), Royal Librarian(4), Erupting Volcano(3)
- P2: HP=2 Armor=0 Mana=6/6 Deck=21; Weapon=Defiled Spear 2/1; Board=Carrier Whelp#48 1/2, Carrier Whelp#73 1/2; Hand=Sanguine Depths(1), Torch(1), Erupting Volcano(3), Darkrider(1), Carrier Whelp(1), Torch(1), Mother Duck(4)

### Step 45: policy-prior-puct-v1

**P2 ATTACK Carrier Whelp#73 -> P1 Windpeak Wyrm#12**

Legal actions: 15; Searched nodes: 5; Selected value: -0.3249

Top choices by root visit share:

- `0.250` — P2 ATTACK Carrier Whelp#73 -> P1 Windpeak Wyrm#12 [SELECTED]; Q=-0.3249; prior=0.0809
- `0.250` — P2 ATTACK Carrier Whelp#73 -> P1 hero; Q=-0.7902; prior=0.0737
- `0.250` — P2 HERO_POWER Armor Up; Q=-0.7921; prior=0.0842
- `0.250` — P2 PLAY Torch[CATA_585] -> P1 Stadium Announcer#13; Q=-0.8310; prior=0.0975
- `0.000` — P2 ATTACK Carrier Whelp#48 -> P1 hero; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "CATA_556", "entity": 73, "kind": "minion_died", "player": 1, "turn": 12}`

- P1: HP=19 Armor=3 Mana=1/6 Deck=20; Weapon=Ursine Maul 5/1; Board=Stadium Announcer#13 3/1, Windpeak Wyrm#12 6/5; Hand=Torch(1), Chainbreaker Hogger(8), Mother Duck(4), Carrier Whelp(1), Royal Librarian(4), Erupting Volcano(3)
- P2: HP=2 Armor=0 Mana=6/6 Deck=21; Weapon=Defiled Spear 2/1; Board=Carrier Whelp#48 1/2; Hand=Sanguine Depths(1), Torch(1), Erupting Volcano(3), Darkrider(1), Carrier Whelp(1), Torch(1), Mother Duck(4)

### Step 46: policy-prior-puct-v1

**P2 PLAY Torch[CATA_585] -> P1 Windpeak Wyrm#12**

Legal actions: 14; Searched nodes: 5; Selected value: -0.1775

Top choices by root visit share:

- `0.250` — P2 PLAY Torch[CATA_585] -> P1 Windpeak Wyrm#12 [SELECTED]; Q=-0.1775; prior=0.0976
- `0.250` — P2 PLAY Torch[CATA_585] -> P1 Stadium Announcer#13; Q=-0.3249; prior=0.1004
- `0.250` — P2 HERO_POWER Armor Up; Q=-0.7995; prior=0.1348
- `0.250` — P2 END_TURN; Q=-1.0000; prior=0.0994
- `0.000` — P2 ATTACK Carrier Whelp#48 -> P1 hero; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "CATA_585", "controller": 1, "created_by": "CATA_585", "entity": 53, "kind": "play", "player": 1, "started_in_deck": false, "turn": 12}`
- `{"card": "CATA_585", "destination": "hand", "entity": 53, "kind": "returned_to_hand", "player": 1, "source": "CATA_585", "turn": 12}`
- `{"card": "TLC_600", "entity": 12, "kind": "minion_died", "player": 0, "turn": 12}`

- P1: HP=19 Armor=3 Mana=1/6 Deck=20; Weapon=Ursine Maul 5/1; Board=Stadium Announcer#13 3/1; Hand=Torch(1), Chainbreaker Hogger(8), Mother Duck(4), Carrier Whelp(1), Royal Librarian(4), Erupting Volcano(3)
- P2: HP=2 Armor=0 Mana=5/6 Deck=21; Weapon=Defiled Spear 2/1; Board=Carrier Whelp#48 1/2; Hand=Sanguine Depths(1), Torch(1), Erupting Volcano(3), Darkrider(1), Carrier Whelp(1), Mother Duck(4), Torch(1)

### Step 47: policy-prior-puct-v1

**P2 PLAY Mother Duck[EDR_492] -> -**

Legal actions: 11; Searched nodes: 5; Selected value: -0.1385

Top choices by root visit share:

- `0.250` — P2 PLAY Mother Duck[EDR_492] -> - [SELECTED]; Q=-0.1385; prior=0.0855
- `0.250` — P2 PLAY Carrier Whelp[CATA_556] -> -; Q=-0.1968; prior=0.0961
- `0.250` — P2 HERO_POWER Armor Up; Q=-0.8066; prior=0.1947
- `0.250` — P2 END_TURN; Q=-1.0000; prior=0.1451
- `0.000` — P2 ATTACK Carrier Whelp#48 -> P1 hero; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "EDR_492", "controller": 1, "created_by": null, "entity": 38, "kind": "play", "player": 1, "started_in_deck": true, "turn": 12}`

- P1: HP=19 Armor=3 Mana=1/6 Deck=20; Weapon=Ursine Maul 5/1; Board=Stadium Announcer#13 3/1; Hand=Torch(1), Chainbreaker Hogger(8), Mother Duck(4), Carrier Whelp(1), Royal Librarian(4), Erupting Volcano(3)
- P2: HP=2 Armor=0 Mana=1/6 Deck=21; Weapon=Defiled Spear 2/1; Board=Carrier Whelp#48 1/2, Mother Duck#38 2/3, Duckling#75 1/1, Duckling#76 1/1, Duckling#77 1/1; Hand=Sanguine Depths(1), Torch(1), Erupting Volcano(3), Darkrider(1), Carrier Whelp(1), Torch(1)

### Step 48: policy-prior-puct-v1

**P2 PLAY Carrier Whelp[CATA_556] -> -**

Legal actions: 11; Searched nodes: 5; Selected value: -0.1581

Top choices by root visit share:

- `0.250` — P2 PLAY Carrier Whelp[CATA_556] -> - [SELECTED]; Q=-0.1581; prior=0.1098
- `0.250` — P2 ATTACK Carrier Whelp#48 -> P1 hero; Q=-0.1581; prior=0.1160
- `0.250` — P2 PLAY Darkrider[EDR_456] -> -; Q=-0.1913; prior=0.0946
- `0.250` — P2 PLAY Torch[CATA_585] -> P1 Stadium Announcer#13; Q=-1.0000; prior=0.1341
- `0.000` — P2 ATTACK Carrier Whelp#48 -> P1 Stadium Announcer#13; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "CATA_556", "controller": 1, "created_by": "CATA_556", "entity": 74, "kind": "play", "player": 1, "started_in_deck": false, "turn": 12}`
- `{"card": "CATA_556", "entity": 78, "kind": "generated_to_hand", "player": 1, "source": "CATA_556", "turn": 12}`

- P1: HP=19 Armor=3 Mana=1/6 Deck=20; Weapon=Ursine Maul 5/1; Board=Stadium Announcer#13 3/1; Hand=Torch(1), Chainbreaker Hogger(8), Mother Duck(4), Carrier Whelp(1), Royal Librarian(4), Erupting Volcano(3)
- P2: HP=2 Armor=0 Mana=0/6 Deck=21; Weapon=Defiled Spear 2/1; Board=Carrier Whelp#48 1/2, Mother Duck#38 2/3, Duckling#75 1/1, Duckling#76 1/1, Duckling#77 1/1, Carrier Whelp#74 1/2; Hand=Sanguine Depths(1), Torch(1), Erupting Volcano(3), Darkrider(1), Torch(1), Carrier Whelp(1)

### Step 49: policy-prior-puct-v1

**P2 ATTACK Duckling#76 -> P1 Stadium Announcer#13**

Legal actions: 6; Searched nodes: 5; Selected value: -1.0000

Top choices by root visit share:

- `0.250` — P2 ATTACK Duckling#76 -> P1 Stadium Announcer#13 [SELECTED]; Q=-1.0000; prior=0.1700
- `0.250` — P2 ATTACK Carrier Whelp#48 -> P1 hero; Q=-1.0000; prior=0.2513
- `0.250` — P2 ATTACK Carrier Whelp#48 -> P1 Stadium Announcer#13; Q=-1.0000; prior=0.1705
- `0.250` — P2 ATTACK Duckling#75 -> P1 Stadium Announcer#13; Q=-1.0000; prior=0.1655
- `0.000` — P2 ATTACK Duckling#77 -> P1 Stadium Announcer#13; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "TIME_034", "entity": 13, "kind": "minion_died", "player": 0, "turn": 12}`
- `{"card": "EDR_492t", "entity": 76, "kind": "minion_died", "player": 1, "turn": 12}`

- P1: HP=19 Armor=3 Mana=1/6 Deck=20; Weapon=Ursine Maul 5/1; Board=empty; Hand=Torch(1), Chainbreaker Hogger(8), Mother Duck(4), Carrier Whelp(1), Royal Librarian(4), Erupting Volcano(3)
- P2: HP=2 Armor=0 Mana=0/6 Deck=21; Weapon=Defiled Spear 2/1; Board=Carrier Whelp#48 1/2, Mother Duck#38 2/3, Duckling#75 1/1, Duckling#77 1/1, Carrier Whelp#74 1/2; Hand=Sanguine Depths(1), Torch(1), Erupting Volcano(3), Darkrider(1), Torch(1), Carrier Whelp(1)

### Step 50: policy-prior-puct-v1

**P2 ATTACK Carrier Whelp#48 -> P1 hero**

Legal actions: 2; Searched nodes: 5; Selected value: -0.8836

Top choices by root visit share:

- `0.750` — P2 ATTACK Carrier Whelp#48 -> P1 hero [SELECTED]; Q=-0.8836; prior=0.6389
- `0.250` — P2 END_TURN; Q=-1.0000; prior=0.3611

- P1: HP=19 Armor=2 Mana=1/6 Deck=20; Weapon=Ursine Maul 5/1; Board=empty; Hand=Torch(1), Chainbreaker Hogger(8), Mother Duck(4), Carrier Whelp(1), Royal Librarian(4), Erupting Volcano(3)
- P2: HP=2 Armor=0 Mana=0/6 Deck=21; Weapon=Defiled Spear 2/1; Board=Carrier Whelp#48 1/2, Mother Duck#38 2/3, Duckling#75 1/1, Duckling#77 1/1, Carrier Whelp#74 1/2; Hand=Sanguine Depths(1), Torch(1), Erupting Volcano(3), Darkrider(1), Torch(1), Carrier Whelp(1)

## Turn 13

### Step 51: policy-prior-puct-v1

**P2 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P2 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 1, "turn": 12}`
- `{"card": "EDR_457", "kind": "draw", "player": 0, "turn": 13}`
- `{"kind": "turn_start", "player": 0, "turn": 13}`

- P1: HP=19 Armor=2 Mana=7/7 Deck=19; Weapon=Ursine Maul 5/1; Board=empty; Hand=Torch(1), Chainbreaker Hogger(8), Mother Duck(4), Carrier Whelp(1), Royal Librarian(4), Erupting Volcano(3), Brood Keeper(2)
- P2: HP=2 Armor=0 Mana=0/6 Deck=21; Weapon=Defiled Spear 2/1; Board=Carrier Whelp#48 1/2, Mother Duck#38 2/3, Duckling#75 1/1, Duckling#77 1/1, Carrier Whelp#74 1/2; Hand=Sanguine Depths(1), Torch(1), Erupting Volcano(3), Darkrider(1), Torch(1), Carrier Whelp(1)

### Step 52: shared-tree-ismcts-v1

**P1 HERO_ATTACK -> P2 hero**

Legal actions: 18; Searched nodes: 5; Selected value: 1.0000

Top choices by root visit share:

- `0.250` — P1 HERO_ATTACK -> P2 hero [SELECTED]; Q=1.0000; prior=0.0000
- `0.250` — P1 HERO_ATTACK -> P2 Mother Duck#38; Q=0.8878; prior=0.0000
- `0.250` — P1 HERO_ATTACK -> P2 Carrier Whelp#48; Q=0.8556; prior=0.0000
- `0.250` — P1 HERO_ATTACK -> P2 Carrier Whelp#74; Q=0.8556; prior=0.0000
- `0.000` — P1 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "EDR_253", "kind": "weapon_destroyed", "player": 0, "turn": 13}`
- `{"card": "CAP_107", "kind": "draw", "player": 0, "turn": 13}`

- P1: HP=19 Armor=2 Mana=7/7 Deck=18; Weapon=none; Board=empty; Hand=Torch(1), Chainbreaker Hogger(8), Mother Duck(4), Carrier Whelp(1), Royal Librarian(4), Erupting Volcano(3), Brood Keeper(2), Cannonmaster(1)
- P2: HP=-3 Armor=0 Mana=0/6 Deck=21; Weapon=Defiled Spear 2/1; Board=Carrier Whelp#48 1/2, Mother Duck#38 2/3, Duckling#75 1/1, Duckling#77 1/1, Carrier Whelp#74 1/2; Hand=Sanguine Depths(1), Torch(1), Erupting Volcano(3), Darkrider(1), Torch(1), Carrier Whelp(1)


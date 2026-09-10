# Policy-prior PUCT vs ISMCTS detailed trace

- Seed: `202609270002`
- Candidate: `P2`
- Winner: `P2`
- Candidate win: `True`
- Actions: `86`
- Illegal actions: `0`

## Turn 1

### Step 1: shared-tree-ismcts-v1

**P1 PLAY Cannonmaster[CAP_107] -> -**

Legal actions: 3; Searched nodes: 5; Selected value: 0.1737

Top choices by root visit share:

- `0.500` — P1 PLAY Cannonmaster[CAP_107] -> - [SELECTED]; Q=0.1737; prior=0.0000
- `0.250` — P1 PLAY Darkrider[EDR_456] -> -; Q=-0.0741; prior=0.0000
- `0.250` — P1 END_TURN; Q=-0.1425; prior=0.0000

Resolved events:

- `{"card": "CAP_107", "controller": 0, "created_by": null, "entity": 30, "kind": "play", "player": 0, "started_in_deck": true, "turn": 1}`
- `{"card": "CAP_107t", "entity": 64, "kind": "generated_to_hand", "player": 0, "source": "CAP_107", "turn": 1}`

- P1: HP=30 Armor=0 Mana=0/1 Deck=27; Weapon=none; Board=Cannonmaster#30 3/1; Hand=Darkrider(1), Mother Duck(4), Erupting Volcano(3), Cannoneer(1)
- P2: HP=30 Armor=0 Mana=0/0 Deck=27; Weapon=none; Board=empty; Hand=Sanguine Depths(1), Carrier Whelp(1), Windpeak Wyrm(8), Torch(1), The Coin(0)

## Turn 2

### Step 2: shared-tree-ismcts-v1

**P1 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P1 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 0, "turn": 1}`
- `{"card": "CORE_SW_066", "kind": "draw", "player": 1, "turn": 2}`
- `{"kind": "turn_start", "player": 1, "turn": 2}`

- P1: HP=30 Armor=0 Mana=0/1 Deck=27; Weapon=none; Board=Cannonmaster#30 3/1; Hand=Darkrider(1), Mother Duck(4), Erupting Volcano(3), Cannoneer(1)
- P2: HP=30 Armor=0 Mana=1/1 Deck=26; Weapon=none; Board=empty; Hand=Sanguine Depths(1), Carrier Whelp(1), Windpeak Wyrm(8), Torch(1), The Coin(0), Royal Librarian(4)

### Step 3: policy-prior-puct-v1

**P2 PLAY Carrier Whelp[CATA_556] -> -**

Legal actions: 4; Searched nodes: 9; Selected value: 0.0157

Top choices by root visit share:

- `0.500` — P2 PLAY Carrier Whelp[CATA_556] -> - [SELECTED]; Q=0.0157; prior=0.6285
- `0.250` — P2 PLAY The Coin[GAME_005] -> -; Q=0.1193; prior=0.2730
- `0.125` — P2 PLAY Sanguine Depths[CORE_REV_990] -> -; Q=-0.0951; prior=0.0551
- `0.125` — P2 END_TURN; Q=-0.4453; prior=0.0434

Resolved events:

- `{"card": "CATA_556", "controller": 1, "created_by": null, "entity": 47, "kind": "play", "player": 1, "started_in_deck": true, "turn": 2}`
- `{"card": "CATA_556", "entity": 65, "kind": "generated_to_hand", "player": 1, "source": "CATA_556", "turn": 2}`

- P1: HP=30 Armor=0 Mana=0/1 Deck=27; Weapon=none; Board=Cannonmaster#30 3/1; Hand=Darkrider(1), Mother Duck(4), Erupting Volcano(3), Cannoneer(1)
- P2: HP=30 Armor=0 Mana=0/1 Deck=26; Weapon=none; Board=Carrier Whelp#47 1/2; Hand=Sanguine Depths(1), Windpeak Wyrm(8), Torch(1), The Coin(0), Royal Librarian(4), Carrier Whelp(1)

### Step 4: policy-prior-puct-v1

**P2 PLAY The Coin[GAME_005] -> -**

Legal actions: 2; Searched nodes: 5; Selected value: -0.1056

Top choices by root visit share:

- `0.750` — P2 PLAY The Coin[GAME_005] -> - [SELECTED]; Q=-0.1056; prior=0.9004
- `0.250` — P2 END_TURN; Q=-0.3809; prior=0.0996

Resolved events:

- `{"card": "GAME_005", "controller": 1, "created_by": "MULLIGAN", "entity": 61, "kind": "play", "player": 1, "started_in_deck": false, "turn": 2}`

- P1: HP=30 Armor=0 Mana=0/1 Deck=27; Weapon=none; Board=Cannonmaster#30 3/1; Hand=Darkrider(1), Mother Duck(4), Erupting Volcano(3), Cannoneer(1)
- P2: HP=30 Armor=0 Mana=1/1 Deck=26; Weapon=none; Board=Carrier Whelp#47 1/2; Hand=Sanguine Depths(1), Windpeak Wyrm(8), Torch(1), Royal Librarian(4), Carrier Whelp(1)

### Step 5: policy-prior-puct-v1

**P2 PLAY Carrier Whelp[CATA_556] -> -**

Legal actions: 3; Searched nodes: 7; Selected value: -0.0668

Top choices by root visit share:

- `0.667` — P2 PLAY Carrier Whelp[CATA_556] -> - [SELECTED]; Q=-0.0668; prior=0.8567
- `0.167` — P2 END_TURN; Q=-0.0940; prior=0.1011
- `0.167` — P2 PLAY Sanguine Depths[CORE_REV_990] -> -; Q=-0.3562; prior=0.0422

Resolved events:

- `{"card": "CATA_556", "controller": 1, "created_by": "CATA_556", "entity": 65, "kind": "play", "player": 1, "started_in_deck": false, "turn": 2}`
- `{"card": "CATA_556", "entity": 66, "kind": "generated_to_hand", "player": 1, "source": "CATA_556", "turn": 2}`

- P1: HP=30 Armor=0 Mana=0/1 Deck=27; Weapon=none; Board=Cannonmaster#30 3/1; Hand=Darkrider(1), Mother Duck(4), Erupting Volcano(3), Cannoneer(1)
- P2: HP=30 Armor=0 Mana=0/1 Deck=26; Weapon=none; Board=Carrier Whelp#47 1/2, Carrier Whelp#65 1/2; Hand=Sanguine Depths(1), Windpeak Wyrm(8), Torch(1), Royal Librarian(4), Carrier Whelp(1)

## Turn 3

### Step 6: policy-prior-puct-v1

**P2 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P2 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 1, "turn": 2}`
- `{"card": "JAIL_421", "kind": "draw", "player": 0, "turn": 3}`
- `{"kind": "turn_start", "player": 0, "turn": 3}`

- P1: HP=30 Armor=0 Mana=2/2 Deck=26; Weapon=none; Board=Cannonmaster#30 3/1; Hand=Darkrider(1), Mother Duck(4), Erupting Volcano(3), Cannoneer(1), Warptooth(4)
- P2: HP=30 Armor=0 Mana=0/1 Deck=26; Weapon=none; Board=Carrier Whelp#47 1/2, Carrier Whelp#65 1/2; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Torch(1), Royal Librarian(4), Carrier Whelp(1)

### Step 7: shared-tree-ismcts-v1

**P1 ATTACK Cannonmaster#30 -> P2 hero**

Legal actions: 7; Searched nodes: 5; Selected value: 0.3007

Top choices by root visit share:

- `0.250` — P1 ATTACK Cannonmaster#30 -> P2 hero [SELECTED]; Q=0.3007; prior=0.0000
- `0.250` — P1 ATTACK Cannonmaster#30 -> P2 Carrier Whelp#47; Q=0.0633; prior=0.0000
- `0.250` — P1 ATTACK Cannonmaster#30 -> P2 Carrier Whelp#65; Q=0.0633; prior=0.0000
- `0.250` — P1 PLAY Cannoneer[CAP_107t] -> -; Q=0.0633; prior=0.0000
- `0.000` — P1 END_TURN; Q=0.0000; prior=0.0000

- P1: HP=30 Armor=0 Mana=2/2 Deck=26; Weapon=none; Board=Cannonmaster#30 3/1; Hand=Darkrider(1), Mother Duck(4), Erupting Volcano(3), Cannoneer(1), Warptooth(4)
- P2: HP=27 Armor=0 Mana=0/1 Deck=26; Weapon=none; Board=Carrier Whelp#47 1/2, Carrier Whelp#65 1/2; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Torch(1), Royal Librarian(4), Carrier Whelp(1)

### Step 8: shared-tree-ismcts-v1

**P1 PLAY Darkrider[EDR_456] -> -**

Legal actions: 4; Searched nodes: 5; Selected value: 0.1979

Top choices by root visit share:

- `0.250` — P1 PLAY Darkrider[EDR_456] -> - [SELECTED]; Q=0.1979; prior=0.0000
- `0.250` — P1 PLAY Cannoneer[CAP_107t] -> -; Q=0.1979; prior=0.0000
- `0.250` — P1 HERO_POWER Armor Up; Q=0.0508; prior=0.0000
- `0.250` — P1 END_TURN; Q=-0.3936; prior=0.0000

Resolved events:

- `{"card": "EDR_456", "controller": 0, "created_by": null, "entity": 4, "kind": "play", "player": 0, "started_in_deck": true, "turn": 3}`

- P1: HP=30 Armor=0 Mana=1/2 Deck=26; Weapon=none; Board=Cannonmaster#30 3/1, Darkrider#4 1/1; Hand=Mother Duck(4), Erupting Volcano(3), Cannoneer(1), Warptooth(4)
- P2: HP=27 Armor=0 Mana=0/1 Deck=26; Weapon=none; Board=Carrier Whelp#47 1/2, Carrier Whelp#65 1/2; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Torch(1), Royal Librarian(4), Carrier Whelp(1)

### Step 9: shared-tree-ismcts-v1

**P1 PLAY Cannoneer[CAP_107t] -> -**

Legal actions: 2; Searched nodes: 5; Selected value: 0.0026

Top choices by root visit share:

- `0.750` — P1 PLAY Cannoneer[CAP_107t] -> - [SELECTED]; Q=0.0026; prior=0.0000
- `0.250` — P1 END_TURN; Q=-0.2214; prior=0.0000

Resolved events:

- `{"card": "CAP_107t", "controller": 0, "created_by": "CAP_107", "entity": 64, "kind": "play", "player": 0, "started_in_deck": false, "turn": 3}`

- P1: HP=30 Armor=0 Mana=0/2 Deck=26; Weapon=none; Board=Cannonmaster#30 3/1, Darkrider#4 1/1, Cannoneer#64 1/1; Hand=Mother Duck(4), Erupting Volcano(3), Warptooth(4)
- P2: HP=27 Armor=0 Mana=0/1 Deck=26; Weapon=none; Board=Carrier Whelp#47 1/2, Carrier Whelp#65 1/2; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Torch(1), Royal Librarian(4), Carrier Whelp(1)

## Turn 4

### Step 10: shared-tree-ismcts-v1

**P1 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P1 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 0, "turn": 3}`
- `{"card": "EDR_457", "kind": "draw", "player": 1, "turn": 4}`
- `{"kind": "turn_start", "player": 1, "turn": 4}`

- P1: HP=30 Armor=0 Mana=0/2 Deck=26; Weapon=none; Board=Cannonmaster#30 3/1, Darkrider#4 1/1, Cannoneer#64 1/1; Hand=Mother Duck(4), Erupting Volcano(3), Warptooth(4)
- P2: HP=27 Armor=0 Mana=2/2 Deck=25; Weapon=none; Board=Carrier Whelp#47 1/1, Carrier Whelp#65 1/2; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Torch(1), Royal Librarian(4), Carrier Whelp(1), Brood Keeper(2)

### Step 11: policy-prior-puct-v1

**P2 PLAY Carrier Whelp[CATA_556] -> -**

Legal actions: 14; Searched nodes: 17; Selected value: 0.1916

Top choices by root visit share:

- `0.125` — P2 PLAY Carrier Whelp[CATA_556] -> - [SELECTED]; Q=0.1916; prior=0.2761
- `0.125` — P2 PLAY Brood Keeper[EDR_457] -> -; Q=0.1208; prior=0.2677
- `0.062` — P2 ATTACK Carrier Whelp#47 -> P1 Cannonmaster#30; Q=0.2559; prior=0.0252
- `0.062` — P2 ATTACK Carrier Whelp#65 -> P1 Darkrider#4; Q=0.2559; prior=0.0276
- `0.062` — P2 ATTACK Carrier Whelp#65 -> P1 Cannoneer#64; Q=0.2559; prior=0.0320

Resolved events:

- `{"card": "CATA_556", "controller": 1, "created_by": "CATA_556", "entity": 66, "kind": "play", "player": 1, "started_in_deck": false, "turn": 4}`
- `{"card": "CATA_556", "entity": 67, "kind": "generated_to_hand", "player": 1, "source": "CATA_556", "turn": 4}`

- P1: HP=30 Armor=0 Mana=0/2 Deck=26; Weapon=none; Board=Cannonmaster#30 3/1, Darkrider#4 1/1, Cannoneer#64 1/1; Hand=Mother Duck(4), Erupting Volcano(3), Warptooth(4)
- P2: HP=27 Armor=0 Mana=1/2 Deck=25; Weapon=none; Board=Carrier Whelp#47 1/1, Carrier Whelp#65 1/2, Carrier Whelp#66 1/2; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Torch(1), Royal Librarian(4), Brood Keeper(2), Carrier Whelp(1)

### Step 12: policy-prior-puct-v1

**P2 PLAY Carrier Whelp[CATA_556] -> -**

Legal actions: 12; Searched nodes: 17; Selected value: 0.1733

Top choices by root visit share:

- `0.312` — P2 PLAY Carrier Whelp[CATA_556] -> - [SELECTED]; Q=0.1733; prior=0.3676
- `0.062` — P2 ATTACK Carrier Whelp#47 -> P1 Cannonmaster#30; Q=0.1820; prior=0.0524
- `0.062` — P2 ATTACK Carrier Whelp#65 -> P1 Darkrider#4; Q=0.1820; prior=0.0496
- `0.062` — P2 ATTACK Carrier Whelp#65 -> P1 Cannoneer#64; Q=0.1820; prior=0.0580
- `0.062` — P2 ATTACK Carrier Whelp#65 -> P1 hero; Q=0.1508; prior=0.1118

Resolved events:

- `{"card": "CATA_556", "controller": 1, "created_by": "CATA_556", "entity": 67, "kind": "play", "player": 1, "started_in_deck": false, "turn": 4}`
- `{"card": "CATA_556", "entity": 68, "kind": "generated_to_hand", "player": 1, "source": "CATA_556", "turn": 4}`

- P1: HP=30 Armor=0 Mana=0/2 Deck=26; Weapon=none; Board=Cannonmaster#30 3/1, Darkrider#4 1/1, Cannoneer#64 1/1; Hand=Mother Duck(4), Erupting Volcano(3), Warptooth(4)
- P2: HP=27 Armor=0 Mana=0/2 Deck=25; Weapon=none; Board=Carrier Whelp#47 1/1, Carrier Whelp#65 1/2, Carrier Whelp#66 1/2, Carrier Whelp#67 1/2; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Torch(1), Royal Librarian(4), Brood Keeper(2), Carrier Whelp(1)

### Step 13: policy-prior-puct-v1

**P2 ATTACK Carrier Whelp#65 -> P1 hero**

Legal actions: 9; Searched nodes: 17; Selected value: 0.2108

Top choices by root visit share:

- `0.312` — P2 ATTACK Carrier Whelp#65 -> P1 hero [SELECTED]; Q=0.2108; prior=0.2345
- `0.188` — P2 ATTACK Carrier Whelp#47 -> P1 hero; Q=0.1647; prior=0.1888
- `0.125` — P2 ATTACK Carrier Whelp#65 -> P1 Cannonmaster#30; Q=0.1763; prior=0.1163
- `0.062` — P2 ATTACK Carrier Whelp#47 -> P1 Cannonmaster#30; Q=0.1820; prior=0.0922
- `0.062` — P2 ATTACK Carrier Whelp#65 -> P1 Darkrider#4; Q=0.1820; prior=0.0804

- P1: HP=29 Armor=0 Mana=0/2 Deck=26; Weapon=none; Board=Cannonmaster#30 3/1, Darkrider#4 1/1, Cannoneer#64 1/1; Hand=Mother Duck(4), Erupting Volcano(3), Warptooth(4)
- P2: HP=27 Armor=0 Mana=0/2 Deck=25; Weapon=none; Board=Carrier Whelp#47 1/1, Carrier Whelp#65 1/2, Carrier Whelp#66 1/2, Carrier Whelp#67 1/2; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Torch(1), Royal Librarian(4), Brood Keeper(2), Carrier Whelp(1)

### Step 14: policy-prior-puct-v1

**P2 ATTACK Carrier Whelp#47 -> P1 hero**

Legal actions: 5; Searched nodes: 11; Selected value: 0.1150

Top choices by root visit share:

- `0.300` — P2 ATTACK Carrier Whelp#47 -> P1 hero [SELECTED]; Q=0.1150; prior=0.3803
- `0.200` — P2 ATTACK Carrier Whelp#47 -> P1 Cannonmaster#30; Q=0.1698; prior=0.2029
- `0.200` — P2 ATTACK Carrier Whelp#47 -> P1 Cannoneer#64; Q=0.1535; prior=0.1831
- `0.200` — P2 ATTACK Carrier Whelp#47 -> P1 Darkrider#4; Q=0.1265; prior=0.1485
- `0.100` — P2 END_TURN; Q=0.2040; prior=0.0852

- P1: HP=28 Armor=0 Mana=0/2 Deck=26; Weapon=none; Board=Cannonmaster#30 3/1, Darkrider#4 1/1, Cannoneer#64 1/1; Hand=Mother Duck(4), Erupting Volcano(3), Warptooth(4)
- P2: HP=27 Armor=0 Mana=0/2 Deck=25; Weapon=none; Board=Carrier Whelp#47 1/1, Carrier Whelp#65 1/2, Carrier Whelp#66 1/2, Carrier Whelp#67 1/2; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Torch(1), Royal Librarian(4), Brood Keeper(2), Carrier Whelp(1)

## Turn 5

### Step 15: policy-prior-puct-v1

**P2 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P2 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 1, "turn": 4}`
- `{"card": "EDR_457", "kind": "draw", "player": 0, "turn": 5}`
- `{"kind": "turn_start", "player": 0, "turn": 5}`

- P1: HP=28 Armor=0 Mana=3/3 Deck=25; Weapon=none; Board=Cannonmaster#30 3/1, Darkrider#4 1/1, Cannoneer#64 1/1; Hand=Mother Duck(4), Erupting Volcano(3), Warptooth(4), Brood Keeper(2)
- P2: HP=27 Armor=0 Mana=0/2 Deck=25; Weapon=none; Board=Carrier Whelp#47 1/1, Carrier Whelp#65 1/2, Carrier Whelp#66 1/2, Carrier Whelp#67 1/2; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Torch(1), Royal Librarian(4), Brood Keeper(2), Carrier Whelp(1)

### Step 16: shared-tree-ismcts-v1

**P1 ATTACK Cannonmaster#30 -> P2 Carrier Whelp#67**

Legal actions: 19; Searched nodes: 5; Selected value: -0.0029

Top choices by root visit share:

- `0.250` — P1 ATTACK Cannonmaster#30 -> P2 Carrier Whelp#67 [SELECTED]; Q=-0.0029; prior=0.0000
- `0.250` — P1 ATTACK Cannonmaster#30 -> P2 Carrier Whelp#65; Q=-0.0029; prior=0.0000
- `0.250` — P1 ATTACK Cannonmaster#30 -> P2 Carrier Whelp#66; Q=-0.0029; prior=0.0000
- `0.250` — P1 ATTACK Cannonmaster#30 -> P2 Carrier Whelp#47; Q=-0.0371; prior=0.0000
- `0.000` — P1 ATTACK Darkrider#4 -> P2 hero; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "CAP_107", "entity": 30, "kind": "minion_died", "player": 0, "turn": 5}`
- `{"card": "CATA_556", "entity": 67, "kind": "minion_died", "player": 1, "turn": 5}`

- P1: HP=28 Armor=0 Mana=3/3 Deck=25; Weapon=none; Board=Darkrider#4 1/1, Cannoneer#64 1/1; Hand=Mother Duck(4), Erupting Volcano(3), Warptooth(4), Brood Keeper(2)
- P2: HP=27 Armor=0 Mana=0/2 Deck=25; Weapon=none; Board=Carrier Whelp#47 1/1, Carrier Whelp#65 1/2, Carrier Whelp#66 1/2; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Torch(1), Royal Librarian(4), Brood Keeper(2), Carrier Whelp(1)

### Step 17: shared-tree-ismcts-v1

**P1 ATTACK Darkrider#4 -> P2 Carrier Whelp#47**

Legal actions: 12; Searched nodes: 5; Selected value: -0.0229

Top choices by root visit share:

- `0.250` — P1 ATTACK Darkrider#4 -> P2 Carrier Whelp#47 [SELECTED]; Q=-0.0229; prior=0.0000
- `0.250` — P1 ATTACK Cannoneer#64 -> P2 Carrier Whelp#47; Q=-0.0229; prior=0.0000
- `0.250` — P1 ATTACK Cannoneer#64 -> P2 Carrier Whelp#65; Q=-0.0229; prior=0.0000
- `0.250` — P1 ATTACK Cannoneer#64 -> P2 Carrier Whelp#66; Q=-0.0229; prior=0.0000
- `0.000` — P1 ATTACK Darkrider#4 -> P2 hero; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "EDR_456", "entity": 4, "kind": "minion_died", "player": 0, "turn": 5}`
- `{"card": "CATA_556", "entity": 47, "kind": "minion_died", "player": 1, "turn": 5}`

- P1: HP=28 Armor=0 Mana=3/3 Deck=25; Weapon=none; Board=Cannoneer#64 1/1; Hand=Mother Duck(4), Erupting Volcano(3), Warptooth(4), Brood Keeper(2)
- P2: HP=27 Armor=0 Mana=0/2 Deck=25; Weapon=none; Board=Carrier Whelp#65 1/2, Carrier Whelp#66 1/2; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Torch(1), Royal Librarian(4), Brood Keeper(2), Carrier Whelp(1)

### Step 18: shared-tree-ismcts-v1

**P1 ATTACK Cannoneer#64 -> P2 hero**

Legal actions: 7; Searched nodes: 5; Selected value: 0.0685

Top choices by root visit share:

- `0.250` — P1 ATTACK Cannoneer#64 -> P2 hero [SELECTED]; Q=0.0685; prior=0.0000
- `0.250` — P1 ATTACK Cannoneer#64 -> P2 Carrier Whelp#65; Q=0.0662; prior=0.0000
- `0.250` — P1 ATTACK Cannoneer#64 -> P2 Carrier Whelp#66; Q=0.0662; prior=0.0000
- `0.250` — P1 PLAY Brood Keeper[EDR_457] -> -; Q=0.0662; prior=0.0000
- `0.000` — P1 END_TURN; Q=0.0000; prior=0.0000

- P1: HP=28 Armor=0 Mana=3/3 Deck=25; Weapon=none; Board=Cannoneer#64 1/1; Hand=Mother Duck(4), Erupting Volcano(3), Warptooth(4), Brood Keeper(2)
- P2: HP=26 Armor=0 Mana=0/2 Deck=25; Weapon=none; Board=Carrier Whelp#65 1/2, Carrier Whelp#66 1/2; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Torch(1), Royal Librarian(4), Brood Keeper(2), Carrier Whelp(1)

### Step 19: shared-tree-ismcts-v1

**P1 PLAY Brood Keeper[EDR_457] -> -**

Legal actions: 4; Searched nodes: 5; Selected value: 0.1564

Top choices by root visit share:

- `0.250` — P1 PLAY Brood Keeper[EDR_457] -> - [SELECTED]; Q=0.1564; prior=0.0000
- `0.250` — P1 HERO_POWER Armor Up; Q=-0.1346; prior=0.0000
- `0.250` — P1 PLAY Erupting Volcano[CATA_584] -> -; Q=-0.2634; prior=0.0000
- `0.250` — P1 END_TURN; Q=-0.5387; prior=0.0000

Resolved events:

- `{"card": "EDR_457", "controller": 0, "created_by": null, "entity": 5, "kind": "play", "player": 0, "started_in_deck": true, "turn": 5}`

- P1: HP=28 Armor=0 Mana=1/3 Deck=25; Weapon=none; Board=Cannoneer#64 1/1, Brood Keeper#5 2/3; Hand=Mother Duck(4), Erupting Volcano(3), Warptooth(4)
- P2: HP=26 Armor=0 Mana=0/2 Deck=25; Weapon=none; Board=Carrier Whelp#65 1/2, Carrier Whelp#66 1/2; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Torch(1), Royal Librarian(4), Brood Keeper(2), Carrier Whelp(1)

## Turn 6

### Step 20: shared-tree-ismcts-v1

**P1 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P1 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 0, "turn": 5}`
- `{"card": "CAP_107", "kind": "draw", "player": 1, "turn": 6}`
- `{"kind": "turn_start", "player": 1, "turn": 6}`

- P1: HP=28 Armor=0 Mana=1/3 Deck=25; Weapon=none; Board=Cannoneer#64 1/1, Brood Keeper#5 2/3; Hand=Mother Duck(4), Erupting Volcano(3), Warptooth(4)
- P2: HP=26 Armor=0 Mana=3/3 Deck=24; Weapon=none; Board=Carrier Whelp#65 1/1, Carrier Whelp#66 1/2; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Torch(1), Royal Librarian(4), Brood Keeper(2), Carrier Whelp(1), Cannonmaster(1)

### Step 21: policy-prior-puct-v1

**P2 PLAY Cannonmaster[CAP_107] -> -**

Legal actions: 13; Searched nodes: 17; Selected value: 0.3298

Top choices by root visit share:

- `0.188` — P2 PLAY Cannonmaster[CAP_107] -> - [SELECTED]; Q=0.3298; prior=0.2054
- `0.125` — P2 PLAY Carrier Whelp[CATA_556] -> -; Q=0.3441; prior=0.1596
- `0.062` — P2 ATTACK Carrier Whelp#65 -> P1 Brood Keeper#5; Q=0.4151; prior=0.0284
- `0.062` — P2 ATTACK Carrier Whelp#66 -> P1 Cannoneer#64; Q=0.4151; prior=0.0477
- `0.062` — P2 ATTACK Carrier Whelp#65 -> P1 Cannoneer#64; Q=0.3080; prior=0.0378

Resolved events:

- `{"card": "CAP_107", "controller": 1, "created_by": null, "entity": 59, "kind": "play", "player": 1, "started_in_deck": true, "turn": 6}`
- `{"card": "CAP_107t", "entity": 69, "kind": "generated_to_hand", "player": 1, "source": "CAP_107", "turn": 6}`

- P1: HP=28 Armor=0 Mana=1/3 Deck=25; Weapon=none; Board=Cannoneer#64 1/1, Brood Keeper#5 2/3; Hand=Mother Duck(4), Erupting Volcano(3), Warptooth(4)
- P2: HP=26 Armor=0 Mana=2/3 Deck=24; Weapon=none; Board=Carrier Whelp#65 1/1, Carrier Whelp#66 1/2, Cannonmaster#59 3/1; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Torch(1), Royal Librarian(4), Brood Keeper(2), Carrier Whelp(1), Cannoneer(1)

### Step 22: policy-prior-puct-v1

**P2 PLAY Carrier Whelp[CATA_556] -> -**

Legal actions: 13; Searched nodes: 17; Selected value: 0.3861

Top choices by root visit share:

- `0.188` — P2 PLAY Carrier Whelp[CATA_556] -> - [SELECTED]; Q=0.3861; prior=0.2012
- `0.125` — P2 PLAY Brood Keeper[EDR_457] -> -; Q=0.3376; prior=0.2343
- `0.062` — P2 ATTACK Carrier Whelp#65 -> P1 hero; Q=0.4485; prior=0.0659
- `0.062` — P2 ATTACK Carrier Whelp#65 -> P1 Brood Keeper#5; Q=0.4462; prior=0.0287
- `0.062` — P2 ATTACK Carrier Whelp#66 -> P1 Cannoneer#64; Q=0.4462; prior=0.0465

Resolved events:

- `{"card": "CATA_556", "controller": 1, "created_by": "CATA_556", "entity": 68, "kind": "play", "player": 1, "started_in_deck": false, "turn": 6}`
- `{"card": "CATA_556", "entity": 70, "kind": "generated_to_hand", "player": 1, "source": "CATA_556", "turn": 6}`

- P1: HP=28 Armor=0 Mana=1/3 Deck=25; Weapon=none; Board=Cannoneer#64 1/1, Brood Keeper#5 2/3; Hand=Mother Duck(4), Erupting Volcano(3), Warptooth(4)
- P2: HP=26 Armor=0 Mana=1/3 Deck=24; Weapon=none; Board=Carrier Whelp#65 1/1, Carrier Whelp#66 1/2, Cannonmaster#59 3/1, Carrier Whelp#68 1/2; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Torch(1), Royal Librarian(4), Brood Keeper(2), Cannoneer(1), Carrier Whelp(1)

### Step 23: policy-prior-puct-v1

**P2 PLAY Carrier Whelp[CATA_556] -> -**

Legal actions: 11; Searched nodes: 17; Selected value: 0.3416

Top choices by root visit share:

- `0.188` — P2 PLAY Carrier Whelp[CATA_556] -> - [SELECTED]; Q=0.3416; prior=0.2469
- `0.125` — P2 ATTACK Carrier Whelp#65 -> P1 hero; Q=0.4250; prior=0.0978
- `0.125` — P2 ATTACK Carrier Whelp#66 -> P1 hero; Q=0.3496; prior=0.1304
- `0.125` — P2 PLAY Cannoneer[CAP_107t] -> -; Q=0.3277; prior=0.2166
- `0.062` — P2 ATTACK Carrier Whelp#65 -> P1 Brood Keeper#5; Q=0.4301; prior=0.0387

Resolved events:

- `{"card": "CATA_556", "controller": 1, "created_by": "CATA_556", "entity": 70, "kind": "play", "player": 1, "started_in_deck": false, "turn": 6}`
- `{"card": "CATA_556", "entity": 71, "kind": "generated_to_hand", "player": 1, "source": "CATA_556", "turn": 6}`

- P1: HP=28 Armor=0 Mana=1/3 Deck=25; Weapon=none; Board=Cannoneer#64 1/1, Brood Keeper#5 2/3; Hand=Mother Duck(4), Erupting Volcano(3), Warptooth(4)
- P2: HP=26 Armor=0 Mana=0/3 Deck=24; Weapon=none; Board=Carrier Whelp#65 1/1, Carrier Whelp#66 1/2, Cannonmaster#59 3/1, Carrier Whelp#68 1/2, Carrier Whelp#70 1/2; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Torch(1), Royal Librarian(4), Brood Keeper(2), Cannoneer(1), Carrier Whelp(1)

### Step 24: policy-prior-puct-v1

**P2 ATTACK Carrier Whelp#65 -> P1 hero**

Legal actions: 7; Searched nodes: 15; Selected value: 0.2178

Top choices by root visit share:

- `0.286` — P2 ATTACK Carrier Whelp#65 -> P1 hero [SELECTED]; Q=0.2178; prior=0.2313
- `0.214` — P2 ATTACK Carrier Whelp#66 -> P1 hero; Q=0.1316; prior=0.2945
- `0.143` — P2 ATTACK Carrier Whelp#66 -> P1 Cannoneer#64; Q=0.2727; prior=0.1201
- `0.143` — P2 ATTACK Carrier Whelp#65 -> P1 Brood Keeper#5; Q=0.2360; prior=0.0753
- `0.071` — P2 ATTACK Carrier Whelp#65 -> P1 Cannoneer#64; Q=0.2554; prior=0.1043

- P1: HP=27 Armor=0 Mana=1/3 Deck=25; Weapon=none; Board=Cannoneer#64 1/1, Brood Keeper#5 2/3; Hand=Mother Duck(4), Erupting Volcano(3), Warptooth(4)
- P2: HP=26 Armor=0 Mana=0/3 Deck=24; Weapon=none; Board=Carrier Whelp#65 1/1, Carrier Whelp#66 1/2, Cannonmaster#59 3/1, Carrier Whelp#68 1/2, Carrier Whelp#70 1/2; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Torch(1), Royal Librarian(4), Brood Keeper(2), Cannoneer(1), Carrier Whelp(1)

### Step 25: policy-prior-puct-v1

**P2 ATTACK Carrier Whelp#66 -> P1 Cannoneer#64**

Legal actions: 4; Searched nodes: 9; Selected value: 0.1299

Top choices by root visit share:

- `0.375` — P2 ATTACK Carrier Whelp#66 -> P1 Cannoneer#64 [SELECTED]; Q=0.1299; prior=0.1940
- `0.375` — P2 ATTACK Carrier Whelp#66 -> P1 hero; Q=-0.0337; prior=0.5110
- `0.125` — P2 ATTACK Carrier Whelp#66 -> P1 Brood Keeper#5; Q=0.0713; prior=0.1457
- `0.125` — P2 END_TURN; Q=0.0713; prior=0.1492

Resolved events:

- `{"card": "CAP_107t", "entity": 64, "kind": "minion_died", "player": 0, "turn": 6}`

- P1: HP=27 Armor=0 Mana=1/3 Deck=25; Weapon=none; Board=Brood Keeper#5 2/3; Hand=Mother Duck(4), Erupting Volcano(3), Warptooth(4)
- P2: HP=26 Armor=0 Mana=0/3 Deck=24; Weapon=none; Board=Carrier Whelp#65 1/1, Carrier Whelp#66 1/1, Cannonmaster#59 3/1, Carrier Whelp#68 1/2, Carrier Whelp#70 1/2; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Torch(1), Royal Librarian(4), Brood Keeper(2), Cannoneer(1), Carrier Whelp(1)

## Turn 7

### Step 26: policy-prior-puct-v1

**P2 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P2 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 1, "turn": 6}`
- `{"card": "EDR_492", "kind": "draw", "player": 0, "turn": 7}`
- `{"kind": "turn_start", "player": 0, "turn": 7}`

- P1: HP=27 Armor=0 Mana=4/4 Deck=24; Weapon=none; Board=Brood Keeper#5 2/3; Hand=Mother Duck(4), Erupting Volcano(3), Warptooth(4), Mother Duck(4)
- P2: HP=26 Armor=0 Mana=0/3 Deck=24; Weapon=none; Board=Carrier Whelp#65 1/1, Carrier Whelp#66 1/1, Cannonmaster#59 3/1, Carrier Whelp#68 1/2, Carrier Whelp#70 1/2; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Torch(1), Royal Librarian(4), Brood Keeper(2), Cannoneer(1), Carrier Whelp(1)

### Step 27: shared-tree-ismcts-v1

**P1 ATTACK Brood Keeper#5 -> P2 Carrier Whelp#70**

Legal actions: 12; Searched nodes: 5; Selected value: 0.0940

Top choices by root visit share:

- `0.250` — P1 ATTACK Brood Keeper#5 -> P2 Carrier Whelp#70 [SELECTED]; Q=0.0940; prior=0.0000
- `0.250` — P1 ATTACK Brood Keeper#5 -> P2 Carrier Whelp#68; Q=0.0940; prior=0.0000
- `0.250` — P1 ATTACK Brood Keeper#5 -> P2 Carrier Whelp#65; Q=0.0599; prior=0.0000
- `0.250` — P1 ATTACK Brood Keeper#5 -> P2 Cannonmaster#59; Q=-0.0770; prior=0.0000
- `0.000` — P1 ATTACK Brood Keeper#5 -> P2 hero; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "CATA_556", "entity": 70, "kind": "minion_died", "player": 1, "turn": 7}`

- P1: HP=27 Armor=0 Mana=4/4 Deck=24; Weapon=none; Board=Brood Keeper#5 2/2; Hand=Mother Duck(4), Erupting Volcano(3), Warptooth(4), Mother Duck(4)
- P2: HP=26 Armor=0 Mana=0/3 Deck=24; Weapon=none; Board=Carrier Whelp#65 1/1, Carrier Whelp#66 1/1, Cannonmaster#59 3/1, Carrier Whelp#68 1/2; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Torch(1), Royal Librarian(4), Brood Keeper(2), Cannoneer(1), Carrier Whelp(1)

### Step 28: shared-tree-ismcts-v1

**P1 PLAY Mother Duck[EDR_492] -> -**

Legal actions: 6; Searched nodes: 5; Selected value: 0.8352

Top choices by root visit share:

- `0.250` — P1 PLAY Mother Duck[EDR_492] -> - [SELECTED]; Q=0.8352; prior=0.0000
- `0.250` — P1 PLAY Mother Duck[EDR_492] -> -; Q=0.8352; prior=0.0000
- `0.250` — P1 PLAY Warptooth[JAIL_421] -> -; Q=-0.0428; prior=0.0000
- `0.250` — P1 PLAY Erupting Volcano[CATA_584] -> -; Q=-0.4657; prior=0.0000
- `0.000` — P1 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "EDR_492", "controller": 0, "created_by": null, "entity": 7, "kind": "play", "player": 0, "started_in_deck": true, "turn": 7}`

- P1: HP=27 Armor=0 Mana=0/4 Deck=24; Weapon=none; Board=Brood Keeper#5 2/2, Mother Duck#7 2/3, Duckling#72 1/1, Duckling#73 1/1, Duckling#74 1/1; Hand=Mother Duck(4), Erupting Volcano(3), Warptooth(4)
- P2: HP=26 Armor=0 Mana=0/3 Deck=24; Weapon=none; Board=Carrier Whelp#65 1/1, Carrier Whelp#66 1/1, Cannonmaster#59 3/1, Carrier Whelp#68 1/2; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Torch(1), Royal Librarian(4), Brood Keeper(2), Cannoneer(1), Carrier Whelp(1)

### Step 29: shared-tree-ismcts-v1

**P1 ATTACK Duckling#74 -> P2 Cannonmaster#59**

Legal actions: 13; Searched nodes: 5; Selected value: 0.8689

Top choices by root visit share:

- `0.250` — P1 ATTACK Duckling#74 -> P2 Cannonmaster#59 [SELECTED]; Q=0.8689; prior=0.0000
- `0.250` — P1 ATTACK Duckling#72 -> P2 Cannonmaster#59; Q=0.8689; prior=0.0000
- `0.250` — P1 ATTACK Duckling#72 -> P2 Carrier Whelp#65; Q=0.8689; prior=0.0000
- `0.250` — P1 ATTACK Duckling#73 -> P2 Cannonmaster#59; Q=0.8689; prior=0.0000
- `0.000` — P1 ATTACK Duckling#72 -> P2 Carrier Whelp#66; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "EDR_492t", "entity": 74, "kind": "minion_died", "player": 0, "turn": 7}`
- `{"card": "CAP_107", "entity": 59, "kind": "minion_died", "player": 1, "turn": 7}`

- P1: HP=27 Armor=0 Mana=0/4 Deck=24; Weapon=none; Board=Brood Keeper#5 2/2, Mother Duck#7 2/3, Duckling#72 1/1, Duckling#73 1/1; Hand=Mother Duck(4), Erupting Volcano(3), Warptooth(4)
- P2: HP=26 Armor=0 Mana=0/3 Deck=24; Weapon=none; Board=Carrier Whelp#65 1/1, Carrier Whelp#66 1/1, Carrier Whelp#68 1/2; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Torch(1), Royal Librarian(4), Brood Keeper(2), Cannoneer(1), Carrier Whelp(1)

### Step 30: shared-tree-ismcts-v1

**P1 ATTACK Duckling#73 -> P2 Carrier Whelp#66**

Legal actions: 7; Searched nodes: 5; Selected value: 0.9051

Top choices by root visit share:

- `0.250` — P1 ATTACK Duckling#73 -> P2 Carrier Whelp#66 [SELECTED]; Q=0.9051; prior=0.0000
- `0.250` — P1 ATTACK Duckling#72 -> P2 Carrier Whelp#65; Q=0.9051; prior=0.0000
- `0.250` — P1 ATTACK Duckling#72 -> P2 Carrier Whelp#66; Q=0.9051; prior=0.0000
- `0.250` — P1 ATTACK Duckling#73 -> P2 Carrier Whelp#65; Q=0.9051; prior=0.0000
- `0.000` — P1 ATTACK Duckling#72 -> P2 Carrier Whelp#68; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "EDR_492t", "entity": 73, "kind": "minion_died", "player": 0, "turn": 7}`
- `{"card": "CATA_556", "entity": 66, "kind": "minion_died", "player": 1, "turn": 7}`

- P1: HP=27 Armor=0 Mana=0/4 Deck=24; Weapon=none; Board=Brood Keeper#5 2/2, Mother Duck#7 2/3, Duckling#72 1/1; Hand=Mother Duck(4), Erupting Volcano(3), Warptooth(4)
- P2: HP=26 Armor=0 Mana=0/3 Deck=24; Weapon=none; Board=Carrier Whelp#65 1/1, Carrier Whelp#68 1/2; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Torch(1), Royal Librarian(4), Brood Keeper(2), Cannoneer(1), Carrier Whelp(1)

### Step 31: shared-tree-ismcts-v1

**P1 ATTACK Duckling#72 -> P2 Carrier Whelp#68**

Legal actions: 3; Searched nodes: 5; Selected value: 0.6608

Top choices by root visit share:

- `0.500` — P1 ATTACK Duckling#72 -> P2 Carrier Whelp#68 [SELECTED]; Q=0.6608; prior=0.0000
- `0.250` — P1 ATTACK Duckling#72 -> P2 Carrier Whelp#65; Q=0.9015; prior=0.0000
- `0.250` — P1 END_TURN; Q=0.0804; prior=0.0000

Resolved events:

- `{"card": "JAIL_421", "kind": "summon_from_zone", "player": 0, "turn": 7}`
- `{"card": "JAIL_421", "kind": "summon_from_zone", "player": 0, "turn": 7}`
- `{"card": "EDR_492t", "entity": 72, "kind": "minion_died", "player": 0, "turn": 7}`

- P1: HP=27 Armor=0 Mana=0/4 Deck=23; Weapon=none; Board=Brood Keeper#5 2/2, Mother Duck#7 2/3, Warptooth#25 3/3, Warptooth#62 3/3; Hand=Mother Duck(4), Erupting Volcano(3)
- P2: HP=26 Armor=0 Mana=0/3 Deck=24; Weapon=none; Board=Carrier Whelp#65 1/1, Carrier Whelp#68 1/1; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Torch(1), Royal Librarian(4), Brood Keeper(2), Cannoneer(1), Carrier Whelp(1)

### Step 32: shared-tree-ismcts-v1

**P1 ATTACK Warptooth#62 -> P2 Carrier Whelp#68**

Legal actions: 7; Searched nodes: 5; Selected value: 0.7182

Top choices by root visit share:

- `0.250` — P1 ATTACK Warptooth#62 -> P2 Carrier Whelp#68 [SELECTED]; Q=0.7182; prior=0.0000
- `0.250` — P1 ATTACK Warptooth#25 -> P2 Carrier Whelp#65; Q=0.7182; prior=0.0000
- `0.250` — P1 ATTACK Warptooth#25 -> P2 Carrier Whelp#68; Q=0.7182; prior=0.0000
- `0.250` — P1 ATTACK Warptooth#62 -> P2 Carrier Whelp#65; Q=0.7182; prior=0.0000
- `0.000` — P1 ATTACK Warptooth#25 -> P2 hero; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "CATA_556", "entity": 68, "kind": "minion_died", "player": 1, "turn": 7}`

- P1: HP=27 Armor=0 Mana=0/4 Deck=23; Weapon=none; Board=Brood Keeper#5 2/2, Mother Duck#7 2/3, Warptooth#25 3/3, Warptooth#62 3/2; Hand=Mother Duck(4), Erupting Volcano(3)
- P2: HP=26 Armor=0 Mana=0/3 Deck=24; Weapon=none; Board=Carrier Whelp#65 1/1; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Torch(1), Royal Librarian(4), Brood Keeper(2), Cannoneer(1), Carrier Whelp(1)

## Turn 8

### Step 33: shared-tree-ismcts-v1

**P1 END_TURN**

Legal actions: 3; Searched nodes: 5; Selected value: 0.6809

Top choices by root visit share:

- `0.500` — P1 END_TURN [SELECTED]; Q=0.6809; prior=0.0000
- `0.250` — P1 ATTACK Warptooth#25 -> P2 hero; Q=0.7496; prior=0.0000
- `0.250` — P1 ATTACK Warptooth#25 -> P2 Carrier Whelp#65; Q=0.4882; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 0, "turn": 7}`
- `{"card": "TIME_034", "kind": "draw", "player": 1, "turn": 8}`
- `{"kind": "turn_start", "player": 1, "turn": 8}`

- P1: HP=27 Armor=0 Mana=0/4 Deck=23; Weapon=none; Board=Brood Keeper#5 2/2, Mother Duck#7 2/3, Warptooth#25 3/3, Warptooth#62 3/2; Hand=Mother Duck(4), Erupting Volcano(3)
- P2: HP=26 Armor=0 Mana=4/4 Deck=23; Weapon=none; Board=Carrier Whelp#65 1/1; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Torch(1), Royal Librarian(4), Brood Keeper(2), Cannoneer(1), Carrier Whelp(1), Stadium Announcer(4)

### Step 34: policy-prior-puct-v1

**P2 ATTACK Carrier Whelp#65 -> P1 hero**

Legal actions: 21; Searched nodes: 17; Selected value: -0.1570

Top choices by root visit share:

- `0.062` — P2 ATTACK Carrier Whelp#65 -> P1 hero [SELECTED]; Q=-0.1570; prior=0.0278
- `0.062` — P2 PLAY Torch[CATA_585] -> P1 Brood Keeper#5; Q=-0.2792; prior=0.0549
- `0.062` — P2 PLAY Torch[CATA_585] -> P1 Warptooth#62; Q=-0.2792; prior=0.0540
- `0.062` — P2 PLAY Carrier Whelp[CATA_556] -> -; Q=-0.3592; prior=0.0602
- `0.062` — P2 PLAY Brood Keeper[EDR_457] -> -; Q=-0.3785; prior=0.0797

- P1: HP=26 Armor=0 Mana=0/4 Deck=23; Weapon=none; Board=Brood Keeper#5 2/2, Mother Duck#7 2/3, Warptooth#25 3/3, Warptooth#62 3/2; Hand=Mother Duck(4), Erupting Volcano(3)
- P2: HP=26 Armor=0 Mana=4/4 Deck=23; Weapon=none; Board=Carrier Whelp#65 1/1; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Torch(1), Royal Librarian(4), Brood Keeper(2), Cannoneer(1), Carrier Whelp(1), Stadium Announcer(4)

### Step 35: policy-prior-puct-v1

**P2 PLAY Carrier Whelp[CATA_556] -> -**

Legal actions: 16; Searched nodes: 17; Selected value: -0.1930

Top choices by root visit share:

- `0.062` — P2 PLAY Carrier Whelp[CATA_556] -> - [SELECTED]; Q=-0.1930; prior=0.0691
- `0.062` — P2 PLAY Brood Keeper[EDR_457] -> -; Q=-0.2143; prior=0.0911
- `0.062` — P2 PLAY Cannoneer[CAP_107t] -> -; Q=-0.2447; prior=0.0443
- `0.062` — P2 PLAY Torch[CATA_585] -> P1 Brood Keeper#5; Q=-0.2976; prior=0.0615
- `0.062` — P2 PLAY Torch[CATA_585] -> P1 Warptooth#62; Q=-0.2976; prior=0.0646

Resolved events:

- `{"card": "CATA_556", "controller": 1, "created_by": "CATA_556", "entity": 71, "kind": "play", "player": 1, "started_in_deck": false, "turn": 8}`
- `{"card": "CATA_556", "entity": 75, "kind": "generated_to_hand", "player": 1, "source": "CATA_556", "turn": 8}`

- P1: HP=26 Armor=0 Mana=0/4 Deck=23; Weapon=none; Board=Brood Keeper#5 2/2, Mother Duck#7 2/3, Warptooth#25 3/3, Warptooth#62 3/2; Hand=Mother Duck(4), Erupting Volcano(3)
- P2: HP=26 Armor=0 Mana=3/4 Deck=23; Weapon=none; Board=Carrier Whelp#65 1/1, Carrier Whelp#71 1/2; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Torch(1), Royal Librarian(4), Brood Keeper(2), Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1)

### Step 36: policy-prior-puct-v1

**P2 PLAY Torch[CATA_585] -> P1 Warptooth#62**

Legal actions: 9; Searched nodes: 17; Selected value: -0.3042

Top choices by root visit share:

- `0.188` — P2 PLAY Torch[CATA_585] -> P1 Warptooth#62 [SELECTED]; Q=-0.3042; prior=0.1945
- `0.188` — P2 PLAY Carrier Whelp[CATA_556] -> -; Q=-0.3141; prior=0.1912
- `0.125` — P2 PLAY Cannoneer[CAP_107t] -> -; Q=-0.3148; prior=0.1042
- `0.125` — P2 PLAY Torch[CATA_585] -> P1 Brood Keeper#5; Q=-0.3171; prior=0.1626
- `0.125` — P2 PLAY Brood Keeper[EDR_457] -> -; Q=-0.3629; prior=0.1666

Resolved events:

- `{"card": "CATA_585", "controller": 1, "created_by": null, "entity": 54, "kind": "play", "player": 1, "started_in_deck": true, "turn": 8}`
- `{"card": "CATA_585", "destination": "hand", "entity": 54, "kind": "returned_to_hand", "player": 1, "source": "CATA_585", "turn": 8}`
- `{"card": "JAIL_421", "entity": 62, "kind": "minion_died", "player": 0, "turn": 8}`

- P1: HP=26 Armor=0 Mana=0/4 Deck=23; Weapon=none; Board=Brood Keeper#5 2/2, Mother Duck#7 2/3, Warptooth#25 3/3; Hand=Mother Duck(4), Erupting Volcano(3)
- P2: HP=26 Armor=0 Mana=2/4 Deck=23; Weapon=none; Board=Carrier Whelp#65 1/1, Carrier Whelp#71 1/2; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Royal Librarian(4), Brood Keeper(2), Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1), Torch(1)

### Step 37: policy-prior-puct-v1

**P2 PLAY Brood Keeper[EDR_457] -> -**

Legal actions: 8; Searched nodes: 17; Selected value: -0.4785

Top choices by root visit share:

- `0.250` — P2 PLAY Brood Keeper[EDR_457] -> - [SELECTED]; Q=-0.4785; prior=0.2832
- `0.188` — P2 PLAY Torch[CATA_585] -> P1 Brood Keeper#5; Q=-0.3866; prior=0.2058
- `0.188` — P2 PLAY Carrier Whelp[CATA_556] -> -; Q=-0.4200; prior=0.1925
- `0.125` — P2 PLAY Cannoneer[CAP_107t] -> -; Q=-0.4202; prior=0.1339
- `0.062` — P2 PLAY Sanguine Depths[CORE_REV_990] -> -; Q=-0.4750; prior=0.0339

Resolved events:

- `{"card": "EDR_457", "controller": 1, "created_by": null, "entity": 36, "kind": "play", "player": 1, "started_in_deck": true, "turn": 8}`
- `{"attack": 2, "card": "EDR_457t", "durability": 2, "kind": "equip_weapon", "player": 1, "turn": 8}`

- P1: HP=26 Armor=0 Mana=0/4 Deck=23; Weapon=none; Board=Brood Keeper#5 2/2, Mother Duck#7 2/3, Warptooth#25 3/3; Hand=Mother Duck(4), Erupting Volcano(3)
- P2: HP=26 Armor=0 Mana=0/4 Deck=23; Weapon=Brood Keeper's Sword 2/2; Board=Carrier Whelp#65 1/1, Carrier Whelp#71 1/2, Brood Keeper#36 2/3; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Royal Librarian(4), Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1), Torch(1)

### Step 38: policy-prior-puct-v1

**P2 HERO_ATTACK -> P1 Warptooth#25**

Legal actions: 5; Searched nodes: 11; Selected value: -0.5216

Top choices by root visit share:

- `0.300` — P2 HERO_ATTACK -> P1 Warptooth#25 [SELECTED]; Q=-0.5216; prior=0.2261
- `0.300` — P2 HERO_ATTACK -> P1 hero; Q=-0.6480; prior=0.3106
- `0.200` — P2 HERO_ATTACK -> P1 Brood Keeper#5; Q=-0.6163; prior=0.2030
- `0.100` — P2 END_TURN; Q=-0.5996; prior=0.0571
- `0.100` — P2 HERO_ATTACK -> P1 Mother Duck#7; Q=-0.6011; prior=0.2032

- P1: HP=26 Armor=0 Mana=0/4 Deck=23; Weapon=none; Board=Brood Keeper#5 2/2, Mother Duck#7 2/3, Warptooth#25 3/1; Hand=Mother Duck(4), Erupting Volcano(3)
- P2: HP=23 Armor=0 Mana=0/4 Deck=23; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#65 1/1, Carrier Whelp#71 1/2, Brood Keeper#36 2/3; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Royal Librarian(4), Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1), Torch(1)

## Turn 9

### Step 39: policy-prior-puct-v1

**P2 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P2 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 1, "turn": 8}`
- `{"card": "CATA_584", "kind": "draw", "player": 0, "turn": 9}`
- `{"kind": "turn_start", "player": 0, "turn": 9}`

- P1: HP=26 Armor=0 Mana=5/5 Deck=22; Weapon=none; Board=Brood Keeper#5 2/2, Mother Duck#7 2/3, Warptooth#25 3/1; Hand=Mother Duck(4), Erupting Volcano(3), Erupting Volcano(3)
- P2: HP=23 Armor=0 Mana=0/4 Deck=23; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#65 1/1, Carrier Whelp#71 1/2, Brood Keeper#36 2/3; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Royal Librarian(4), Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1), Torch(1)

### Step 40: shared-tree-ismcts-v1

**P1 ATTACK Warptooth#25 -> P2 Brood Keeper#36**

Legal actions: 17; Searched nodes: 5; Selected value: 0.8913

Top choices by root visit share:

- `0.250` — P1 ATTACK Warptooth#25 -> P2 Brood Keeper#36 [SELECTED]; Q=0.8913; prior=0.0000
- `0.250` — P1 ATTACK Brood Keeper#5 -> P2 Carrier Whelp#71; Q=0.8913; prior=0.0000
- `0.250` — P1 ATTACK Mother Duck#7 -> P2 Carrier Whelp#71; Q=0.8913; prior=0.0000
- `0.250` — P1 ATTACK Warptooth#25 -> P2 Carrier Whelp#71; Q=0.7628; prior=0.0000
- `0.000` — P1 ATTACK Brood Keeper#5 -> P2 hero; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "JAIL_421", "entity": 25, "kind": "minion_died", "player": 0, "turn": 9}`
- `{"card": "EDR_457", "entity": 36, "kind": "minion_died", "player": 1, "turn": 9}`

- P1: HP=26 Armor=0 Mana=5/5 Deck=22; Weapon=none; Board=Brood Keeper#5 2/2, Mother Duck#7 2/3; Hand=Mother Duck(4), Erupting Volcano(3), Erupting Volcano(3)
- P2: HP=23 Armor=0 Mana=0/4 Deck=23; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#65 1/1, Carrier Whelp#71 1/2; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Royal Librarian(4), Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1), Torch(1)

### Step 41: shared-tree-ismcts-v1

**P1 ATTACK Mother Duck#7 -> P2 Carrier Whelp#71**

Legal actions: 11; Searched nodes: 5; Selected value: 0.8871

Top choices by root visit share:

- `0.250` — P1 ATTACK Mother Duck#7 -> P2 Carrier Whelp#71 [SELECTED]; Q=0.8871; prior=0.0000
- `0.250` — P1 ATTACK Brood Keeper#5 -> P2 Carrier Whelp#65; Q=0.8871; prior=0.0000
- `0.250` — P1 ATTACK Brood Keeper#5 -> P2 Carrier Whelp#71; Q=0.8871; prior=0.0000
- `0.250` — P1 ATTACK Mother Duck#7 -> P2 Carrier Whelp#65; Q=0.8871; prior=0.0000
- `0.000` — P1 ATTACK Brood Keeper#5 -> P2 hero; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "CATA_556", "entity": 71, "kind": "minion_died", "player": 1, "turn": 9}`

- P1: HP=26 Armor=0 Mana=5/5 Deck=22; Weapon=none; Board=Brood Keeper#5 2/2, Mother Duck#7 2/2; Hand=Mother Duck(4), Erupting Volcano(3), Erupting Volcano(3)
- P2: HP=23 Armor=0 Mana=0/4 Deck=23; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#65 1/1; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Royal Librarian(4), Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1), Torch(1)

### Step 42: shared-tree-ismcts-v1

**P1 ATTACK Brood Keeper#5 -> P2 hero**

Legal actions: 7; Searched nodes: 5; Selected value: 0.8813

Top choices by root visit share:

- `0.250` — P1 ATTACK Brood Keeper#5 -> P2 hero [SELECTED]; Q=0.8813; prior=0.0000
- `0.250` — P1 ATTACK Brood Keeper#5 -> P2 Carrier Whelp#65; Q=0.8490; prior=0.0000
- `0.250` — P1 PLAY Mother Duck[EDR_492] -> -; Q=0.8490; prior=0.0000
- `0.250` — P1 PLAY Erupting Volcano[CATA_584] -> -; Q=0.5703; prior=0.0000
- `0.000` — P1 END_TURN; Q=0.0000; prior=0.0000

- P1: HP=26 Armor=0 Mana=5/5 Deck=22; Weapon=none; Board=Brood Keeper#5 2/2, Mother Duck#7 2/2; Hand=Mother Duck(4), Erupting Volcano(3), Erupting Volcano(3)
- P2: HP=21 Armor=0 Mana=0/4 Deck=23; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#65 1/1; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Royal Librarian(4), Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1), Torch(1)

### Step 43: shared-tree-ismcts-v1

**P1 PLAY Mother Duck[EDR_492] -> -**

Legal actions: 5; Searched nodes: 5; Selected value: 0.8415

Top choices by root visit share:

- `0.250` — P1 PLAY Mother Duck[EDR_492] -> - [SELECTED]; Q=0.8415; prior=0.0000
- `0.250` — P1 HERO_POWER Armor Up; Q=0.4759; prior=0.0000
- `0.250` — P1 PLAY Erupting Volcano[CATA_584] -> -; Q=0.4759; prior=0.0000
- `0.250` — P1 PLAY Erupting Volcano[CATA_584] -> -; Q=0.4759; prior=0.0000
- `0.000` — P1 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "EDR_492", "controller": 0, "created_by": null, "entity": 8, "kind": "play", "player": 0, "started_in_deck": true, "turn": 9}`

- P1: HP=26 Armor=0 Mana=1/5 Deck=22; Weapon=none; Board=Brood Keeper#5 2/2, Mother Duck#7 2/2, Mother Duck#8 2/3, Duckling#76 1/1, Duckling#77 1/1, Duckling#78 1/1; Hand=Erupting Volcano(3), Erupting Volcano(3)
- P2: HP=21 Armor=0 Mana=0/4 Deck=23; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#65 1/1; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Royal Librarian(4), Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1), Torch(1)

## Turn 10

### Step 44: shared-tree-ismcts-v1

**P1 END_TURN**

Legal actions: 4; Searched nodes: 5; Selected value: 0.8267

Top choices by root visit share:

- `0.250` — P1 END_TURN [SELECTED]; Q=0.8267; prior=0.0000
- `0.250` — P1 ATTACK Duckling#76 -> P2 Carrier Whelp#65; Q=0.7528; prior=0.0000
- `0.250` — P1 ATTACK Duckling#77 -> P2 Carrier Whelp#65; Q=0.7528; prior=0.0000
- `0.250` — P1 ATTACK Duckling#78 -> P2 Carrier Whelp#65; Q=0.6051; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 0, "turn": 9}`
- `{"card": "CATA_585", "kind": "draw", "player": 1, "turn": 10}`
- `{"kind": "turn_start", "player": 1, "turn": 10}`

- P1: HP=26 Armor=0 Mana=1/5 Deck=22; Weapon=none; Board=Brood Keeper#5 2/2, Mother Duck#7 2/2, Mother Duck#8 2/3, Duckling#76 1/1, Duckling#77 1/1, Duckling#78 1/1; Hand=Erupting Volcano(3), Erupting Volcano(3)
- P2: HP=21 Armor=0 Mana=5/5 Deck=22; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#65 1/1; Hand=Sanguine Depths(1), Windpeak Wyrm(5), Royal Librarian(4), Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1), Torch(1), Torch(1)

### Step 45: policy-prior-puct-v1

**P2 PLAY Windpeak Wyrm[TLC_600] -> P1 Mother Duck#8**

Legal actions: 43; Searched nodes: 17; Selected value: 0.1764

Top choices by root visit share:

- `0.062` — P2 PLAY Windpeak Wyrm[TLC_600] -> P1 Mother Duck#8 [SELECTED]; Q=0.1764; prior=0.0661
- `0.062` — P2 PLAY Windpeak Wyrm[TLC_600] -> P1 hero; Q=0.1138; prior=0.0608
- `0.062` — P2 PLAY Windpeak Wyrm[TLC_600] -> P1 Brood Keeper#5; Q=0.0753; prior=0.0519
- `0.062` — P2 PLAY Windpeak Wyrm[TLC_600] -> P1 Mother Duck#7; Q=0.0753; prior=0.0609
- `0.062` — P2 PLAY Windpeak Wyrm[TLC_600] -> P1 Duckling#76; Q=0.0034; prior=0.0360

Resolved events:

- `{"card": "TLC_600", "controller": 1, "created_by": null, "entity": 42, "kind": "play", "player": 1, "started_in_deck": true, "turn": 10}`
- `{"amount": 5, "kind": "gain_armor", "player": 1, "turn": 10}`
- `{"card": "EDR_492", "entity": 8, "kind": "minion_died", "player": 0, "turn": 10}`

- P1: HP=26 Armor=0 Mana=1/5 Deck=22; Weapon=none; Board=Brood Keeper#5 2/2, Mother Duck#7 2/2, Duckling#76 1/1, Duckling#77 1/1, Duckling#78 1/1; Hand=Erupting Volcano(3), Erupting Volcano(3)
- P2: HP=21 Armor=5 Mana=0/5 Deck=22; Weapon=Brood Keeper's Sword 2/1; Board=Carrier Whelp#65 1/1, Windpeak Wyrm#42 6/6; Hand=Sanguine Depths(1), Royal Librarian(4), Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1), Torch(1), Torch(1)

### Step 46: policy-prior-puct-v1

**P2 ATTACK Carrier Whelp#65 -> P1 Duckling#78**

Legal actions: 13; Searched nodes: 17; Selected value: 0.3324

Top choices by root visit share:

- `0.125` — P2 ATTACK Carrier Whelp#65 -> P1 Duckling#78 [SELECTED]; Q=0.3324; prior=0.0739
- `0.125` — P2 HERO_ATTACK -> P1 Mother Duck#7; Q=0.2698; prior=0.0981
- `0.125` — P2 HERO_ATTACK -> P1 Duckling#78; Q=0.1910; prior=0.1053
- `0.062` — P2 ATTACK Carrier Whelp#65 -> P1 Duckling#76; Q=0.3085; prior=0.0661
- `0.062` — P2 ATTACK Carrier Whelp#65 -> P1 Duckling#77; Q=0.3085; prior=0.0672

Resolved events:

- `{"card": "EDR_492t", "entity": 78, "kind": "minion_died", "player": 0, "turn": 10}`
- `{"card": "CATA_556", "entity": 65, "kind": "minion_died", "player": 1, "turn": 10}`

- P1: HP=26 Armor=0 Mana=1/5 Deck=22; Weapon=none; Board=Brood Keeper#5 2/2, Mother Duck#7 2/2, Duckling#76 1/1, Duckling#77 1/1; Hand=Erupting Volcano(3), Erupting Volcano(3)
- P2: HP=21 Armor=5 Mana=0/5 Deck=22; Weapon=Brood Keeper's Sword 2/1; Board=Windpeak Wyrm#42 6/6; Hand=Sanguine Depths(1), Royal Librarian(4), Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1), Torch(1), Torch(1)

### Step 47: policy-prior-puct-v1

**P2 HERO_ATTACK -> P1 Mother Duck#7**

Legal actions: 6; Searched nodes: 13; Selected value: 0.4136

Top choices by root visit share:

- `0.250` — P2 HERO_ATTACK -> P1 Mother Duck#7 [SELECTED]; Q=0.4136; prior=0.1833
- `0.250` — P2 HERO_ATTACK -> P1 hero; Q=0.1149; prior=0.2601
- `0.167` — P2 HERO_ATTACK -> P1 Duckling#76; Q=0.5134; prior=0.1685
- `0.167` — P2 HERO_ATTACK -> P1 Duckling#77; Q=0.5134; prior=0.1624
- `0.083` — P2 END_TURN; Q=0.5012; prior=0.0563

Resolved events:

- `{"card": "EDR_457t", "kind": "weapon_destroyed", "player": 1, "turn": 10}`
- `{"card": "EDR_492", "entity": 7, "kind": "minion_died", "player": 0, "turn": 10}`

- P1: HP=26 Armor=0 Mana=1/5 Deck=22; Weapon=none; Board=Brood Keeper#5 2/2, Duckling#76 1/1, Duckling#77 1/1; Hand=Erupting Volcano(3), Erupting Volcano(3)
- P2: HP=21 Armor=3 Mana=0/5 Deck=22; Weapon=none; Board=Windpeak Wyrm#42 6/6; Hand=Sanguine Depths(1), Royal Librarian(4), Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1), Torch(1), Torch(1)

## Turn 11

### Step 48: policy-prior-puct-v1

**P2 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P2 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 1, "turn": 10}`
- `{"card": "END_033", "kind": "draw", "player": 0, "turn": 11}`
- `{"kind": "turn_start", "player": 0, "turn": 11}`

- P1: HP=26 Armor=0 Mana=6/6 Deck=21; Weapon=none; Board=Brood Keeper#5 2/2, Duckling#76 1/1, Duckling#77 1/1; Hand=Erupting Volcano(3), Erupting Volcano(3), Prescient Slitherdrake(7)
- P2: HP=21 Armor=3 Mana=0/5 Deck=22; Weapon=none; Board=Windpeak Wyrm#42 6/6; Hand=Sanguine Depths(1), Royal Librarian(4), Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1), Torch(1), Torch(1)

### Step 49: shared-tree-ismcts-v1

**P1 ATTACK Brood Keeper#5 -> P2 hero**

Legal actions: 10; Searched nodes: 5; Selected value: -0.3497

Top choices by root visit share:

- `0.250` — P1 ATTACK Brood Keeper#5 -> P2 hero [SELECTED]; Q=-0.3497; prior=0.0000
- `0.250` — P1 ATTACK Brood Keeper#5 -> P2 Windpeak Wyrm#42; Q=-0.5768; prior=0.0000
- `0.250` — P1 ATTACK Duckling#76 -> P2 Windpeak Wyrm#42; Q=-0.5768; prior=0.0000
- `0.250` — P1 ATTACK Duckling#77 -> P2 Windpeak Wyrm#42; Q=-0.5768; prior=0.0000
- `0.000` — P1 ATTACK Duckling#76 -> P2 hero; Q=0.0000; prior=0.0000

- P1: HP=26 Armor=0 Mana=6/6 Deck=21; Weapon=none; Board=Brood Keeper#5 2/2, Duckling#76 1/1, Duckling#77 1/1; Hand=Erupting Volcano(3), Erupting Volcano(3), Prescient Slitherdrake(7)
- P2: HP=21 Armor=1 Mana=0/5 Deck=22; Weapon=none; Board=Windpeak Wyrm#42 6/6; Hand=Sanguine Depths(1), Royal Librarian(4), Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1), Torch(1), Torch(1)

### Step 50: shared-tree-ismcts-v1

**P1 ATTACK Duckling#77 -> P2 hero**

Legal actions: 8; Searched nodes: 5; Selected value: -0.1853

Top choices by root visit share:

- `0.250` — P1 ATTACK Duckling#77 -> P2 hero [SELECTED]; Q=-0.1853; prior=0.0000
- `0.250` — P1 ATTACK Duckling#76 -> P2 hero; Q=-0.1853; prior=0.0000
- `0.250` — P1 ATTACK Duckling#76 -> P2 Windpeak Wyrm#42; Q=-0.3672; prior=0.0000
- `0.250` — P1 ATTACK Duckling#77 -> P2 Windpeak Wyrm#42; Q=-0.3672; prior=0.0000
- `0.000` — P1 END_TURN; Q=0.0000; prior=0.0000

- P1: HP=26 Armor=0 Mana=6/6 Deck=21; Weapon=none; Board=Brood Keeper#5 2/2, Duckling#76 1/1, Duckling#77 1/1; Hand=Erupting Volcano(3), Erupting Volcano(3), Prescient Slitherdrake(7)
- P2: HP=21 Armor=0 Mana=0/5 Deck=22; Weapon=none; Board=Windpeak Wyrm#42 6/6; Hand=Sanguine Depths(1), Royal Librarian(4), Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1), Torch(1), Torch(1)

### Step 51: shared-tree-ismcts-v1

**P1 ATTACK Duckling#76 -> P2 hero**

Legal actions: 6; Searched nodes: 5; Selected value: -0.0097

Top choices by root visit share:

- `0.250` — P1 ATTACK Duckling#76 -> P2 hero [SELECTED]; Q=-0.0097; prior=0.0000
- `0.250` — P1 ATTACK Duckling#76 -> P2 Windpeak Wyrm#42; Q=-0.2045; prior=0.0000
- `0.250` — P1 PLAY Erupting Volcano[CATA_584] -> -; Q=-0.2045; prior=0.0000
- `0.250` — P1 PLAY Erupting Volcano[CATA_584] -> -; Q=-0.2045; prior=0.0000
- `0.000` — P1 END_TURN; Q=0.0000; prior=0.0000

- P1: HP=26 Armor=0 Mana=6/6 Deck=21; Weapon=none; Board=Brood Keeper#5 2/2, Duckling#76 1/1, Duckling#77 1/1; Hand=Erupting Volcano(3), Erupting Volcano(3), Prescient Slitherdrake(7)
- P2: HP=20 Armor=0 Mana=0/5 Deck=22; Weapon=none; Board=Windpeak Wyrm#42 6/6; Hand=Sanguine Depths(1), Royal Librarian(4), Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1), Torch(1), Torch(1)

### Step 52: shared-tree-ismcts-v1

**P1 HERO_POWER Armor Up**

Legal actions: 4; Searched nodes: 5; Selected value: -0.0537

Top choices by root visit share:

- `0.250` — P1 HERO_POWER Armor Up [SELECTED]; Q=-0.0537; prior=0.0000
- `0.250` — P1 PLAY Erupting Volcano[CATA_584] -> -; Q=-0.1858; prior=0.0000
- `0.250` — P1 PLAY Erupting Volcano[CATA_584] -> -; Q=-0.1858; prior=0.0000
- `0.250` — P1 END_TURN; Q=-0.7078; prior=0.0000

Resolved events:

- `{"amount": 2, "kind": "gain_armor", "player": 0, "turn": 11}`
- `{"kind": "hero_power", "player": 0, "turn": 11}`

- P1: HP=26 Armor=2 Mana=4/6 Deck=21; Weapon=none; Board=Brood Keeper#5 2/2, Duckling#76 1/1, Duckling#77 1/1; Hand=Erupting Volcano(3), Erupting Volcano(3), Prescient Slitherdrake(7)
- P2: HP=20 Armor=0 Mana=0/5 Deck=22; Weapon=none; Board=Windpeak Wyrm#42 6/6; Hand=Sanguine Depths(1), Royal Librarian(4), Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1), Torch(1), Torch(1)

## Turn 12

### Step 53: shared-tree-ismcts-v1

**P1 END_TURN**

Legal actions: 3; Searched nodes: 5; Selected value: -0.6693

Top choices by root visit share:

- `0.500` — P1 END_TURN [SELECTED]; Q=-0.6693; prior=0.0000
- `0.250` — P1 PLAY Erupting Volcano[CATA_584] -> -; Q=-0.4675; prior=0.0000
- `0.250` — P1 PLAY Erupting Volcano[CATA_584] -> -; Q=-0.8626; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 0, "turn": 11}`
- `{"card": "CAP_107", "kind": "draw", "player": 1, "turn": 12}`
- `{"kind": "turn_start", "player": 1, "turn": 12}`

- P1: HP=26 Armor=2 Mana=4/6 Deck=21; Weapon=none; Board=Brood Keeper#5 2/2, Duckling#76 1/1, Duckling#77 1/1; Hand=Erupting Volcano(3), Erupting Volcano(3), Prescient Slitherdrake(7)
- P2: HP=20 Armor=0 Mana=6/6 Deck=21; Weapon=none; Board=Windpeak Wyrm#42 6/6; Hand=Sanguine Depths(1), Royal Librarian(4), Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1), Torch(1), Torch(1), Cannonmaster(1)

### Step 54: policy-prior-puct-v1

**P2 ATTACK Windpeak Wyrm#42 -> P1 hero**

Legal actions: 18; Searched nodes: 17; Selected value: 0.8347

Top choices by root visit share:

- `0.062` — P2 ATTACK Windpeak Wyrm#42 -> P1 hero [SELECTED]; Q=0.8347; prior=0.1212
- `0.062` — P2 ATTACK Windpeak Wyrm#42 -> P1 Duckling#76; Q=0.7621; prior=0.0266
- `0.062` — P2 ATTACK Windpeak Wyrm#42 -> P1 Duckling#77; Q=0.7621; prior=0.0318
- `0.062` — P2 PLAY Torch[CATA_585] -> P1 Brood Keeper#5; Q=0.7621; prior=0.0389
- `0.062` — P2 PLAY Torch[CATA_585] -> P1 Brood Keeper#5; Q=0.7621; prior=0.0518

- P1: HP=22 Armor=0 Mana=4/6 Deck=21; Weapon=none; Board=Brood Keeper#5 2/2, Duckling#76 1/1, Duckling#77 1/1; Hand=Erupting Volcano(3), Erupting Volcano(3), Prescient Slitherdrake(7)
- P2: HP=20 Armor=0 Mana=6/6 Deck=21; Weapon=none; Board=Windpeak Wyrm#42 6/6; Hand=Sanguine Depths(1), Royal Librarian(4), Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1), Torch(1), Torch(1), Cannonmaster(1)

### Step 55: policy-prior-puct-v1

**P2 PLAY Royal Librarian[CORE_SW_066] -> P2 Windpeak Wyrm#42**

Legal actions: 14; Searched nodes: 17; Selected value: 0.7963

Top choices by root visit share:

- `0.125` — P2 PLAY Royal Librarian[CORE_SW_066] -> P2 Windpeak Wyrm#42 [SELECTED]; Q=0.7963; prior=0.1062
- `0.125` — P2 HERO_POWER Armor Up; Q=0.7169; prior=0.1727
- `0.062` — P2 PLAY Royal Librarian[CORE_SW_066] -> P1 Duckling#76; Q=0.8285; prior=0.0297
- `0.062` — P2 PLAY Royal Librarian[CORE_SW_066] -> P1 Duckling#77; Q=0.8285; prior=0.0329
- `0.062` — P2 PLAY Torch[CATA_585] -> P1 Brood Keeper#5; Q=0.8285; prior=0.0487

Resolved events:

- `{"card": "CORE_SW_066", "controller": 1, "created_by": null, "entity": 31, "kind": "play", "player": 1, "started_in_deck": true, "turn": 12}`

- P1: HP=22 Armor=0 Mana=4/6 Deck=21; Weapon=none; Board=Brood Keeper#5 2/2, Duckling#76 1/1, Duckling#77 1/1; Hand=Erupting Volcano(3), Erupting Volcano(3), Prescient Slitherdrake(7)
- P2: HP=20 Armor=0 Mana=2/6 Deck=21; Weapon=none; Board=Windpeak Wyrm#42 6/6, Royal Librarian#31 4/4; Hand=Sanguine Depths(1), Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1), Torch(1), Torch(1), Cannonmaster(1)

### Step 56: policy-prior-puct-v1

**P2 HERO_POWER Armor Up**

Legal actions: 8; Searched nodes: 17; Selected value: 0.6841

Top choices by root visit share:

- `0.250` — P2 HERO_POWER Armor Up [SELECTED]; Q=0.6841; prior=0.2441
- `0.125` — P2 PLAY Torch[CATA_585] -> P1 Brood Keeper#5; Q=0.8310; prior=0.1185
- `0.125` — P2 PLAY Cannoneer[CAP_107t] -> -; Q=0.8265; prior=0.1039
- `0.125` — P2 PLAY Carrier Whelp[CATA_556] -> -; Q=0.7939; prior=0.1348
- `0.125` — P2 PLAY Cannonmaster[CAP_107] -> -; Q=0.7439; prior=0.1504

Resolved events:

- `{"amount": 2, "kind": "gain_armor", "player": 1, "turn": 12}`
- `{"kind": "hero_power", "player": 1, "turn": 12}`

- P1: HP=22 Armor=0 Mana=4/6 Deck=21; Weapon=none; Board=Brood Keeper#5 2/2, Duckling#76 1/1, Duckling#77 1/1; Hand=Erupting Volcano(3), Erupting Volcano(3), Prescient Slitherdrake(7)
- P2: HP=20 Armor=2 Mana=0/6 Deck=21; Weapon=none; Board=Windpeak Wyrm#42 6/6, Royal Librarian#31 4/4; Hand=Sanguine Depths(1), Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1), Torch(1), Torch(1), Cannonmaster(1)

## Turn 13

### Step 57: policy-prior-puct-v1

**P2 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P2 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 1, "turn": 12}`
- `{"card": "FIR_939", "kind": "draw", "player": 0, "turn": 13}`
- `{"kind": "turn_start", "player": 0, "turn": 13}`

- P1: HP=22 Armor=0 Mana=7/7 Deck=20; Weapon=none; Board=Brood Keeper#5 2/2, Duckling#76 1/1, Duckling#77 1/1; Hand=Erupting Volcano(3), Erupting Volcano(3), Prescient Slitherdrake(7), Shadowflame Suffusion(2)
- P2: HP=20 Armor=2 Mana=0/6 Deck=21; Weapon=none; Board=Windpeak Wyrm#42 6/6, Royal Librarian#31 4/4; Hand=Sanguine Depths(1), Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1), Torch(1), Torch(1), Cannonmaster(1)

### Step 58: shared-tree-ismcts-v1

**P1 ATTACK Duckling#77 -> P2 Windpeak Wyrm#42**

Legal actions: 21; Searched nodes: 5; Selected value: -0.4278

Top choices by root visit share:

- `0.250` — P1 ATTACK Duckling#77 -> P2 Windpeak Wyrm#42 [SELECTED]; Q=-0.4278; prior=0.0000
- `0.250` — P1 ATTACK Brood Keeper#5 -> P2 Windpeak Wyrm#42; Q=-0.4278; prior=0.0000
- `0.250` — P1 ATTACK Duckling#76 -> P2 Royal Librarian#31; Q=-0.4278; prior=0.0000
- `0.250` — P1 ATTACK Duckling#76 -> P2 Windpeak Wyrm#42; Q=-0.4278; prior=0.0000
- `0.000` — P1 ATTACK Brood Keeper#5 -> P2 hero; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "EDR_492t", "entity": 77, "kind": "minion_died", "player": 0, "turn": 13}`

- P1: HP=22 Armor=0 Mana=7/7 Deck=20; Weapon=none; Board=Brood Keeper#5 2/2, Duckling#76 1/1; Hand=Erupting Volcano(3), Erupting Volcano(3), Prescient Slitherdrake(7), Shadowflame Suffusion(2)
- P2: HP=20 Armor=2 Mana=0/6 Deck=21; Weapon=none; Board=Windpeak Wyrm#42 6/5, Royal Librarian#31 4/4; Hand=Sanguine Depths(1), Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1), Torch(1), Torch(1), Cannonmaster(1)

### Step 59: shared-tree-ismcts-v1

**P1 ATTACK Duckling#76 -> P2 Windpeak Wyrm#42**

Legal actions: 17; Searched nodes: 5; Selected value: -0.4440

Top choices by root visit share:

- `0.250` — P1 ATTACK Duckling#76 -> P2 Windpeak Wyrm#42 [SELECTED]; Q=-0.4440; prior=0.0000
- `0.250` — P1 ATTACK Brood Keeper#5 -> P2 Royal Librarian#31; Q=-0.4440; prior=0.0000
- `0.250` — P1 ATTACK Brood Keeper#5 -> P2 Windpeak Wyrm#42; Q=-0.4440; prior=0.0000
- `0.250` — P1 ATTACK Duckling#76 -> P2 Royal Librarian#31; Q=-0.4440; prior=0.0000
- `0.000` — P1 ATTACK Brood Keeper#5 -> P2 hero; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "EDR_492t", "entity": 76, "kind": "minion_died", "player": 0, "turn": 13}`

- P1: HP=22 Armor=0 Mana=7/7 Deck=20; Weapon=none; Board=Brood Keeper#5 2/2; Hand=Erupting Volcano(3), Erupting Volcano(3), Prescient Slitherdrake(7), Shadowflame Suffusion(2)
- P2: HP=20 Armor=2 Mana=0/6 Deck=21; Weapon=none; Board=Windpeak Wyrm#42 6/4, Royal Librarian#31 4/4; Hand=Sanguine Depths(1), Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1), Torch(1), Torch(1), Cannonmaster(1)

### Step 60: shared-tree-ismcts-v1

**P1 PLAY Prescient Slitherdrake[END_033] -> -**

Legal actions: 13; Searched nodes: 5; Selected value: -0.0109

Top choices by root visit share:

- `0.250` — P1 PLAY Prescient Slitherdrake[END_033] -> - [SELECTED]; Q=-0.0109; prior=0.0000
- `0.250` — P1 ATTACK Brood Keeper#5 -> P2 Windpeak Wyrm#42; Q=-0.0109; prior=0.0000
- `0.250` — P1 ATTACK Brood Keeper#5 -> P2 Royal Librarian#31; Q=-0.1869; prior=0.0000
- `0.250` — P1 ATTACK Brood Keeper#5 -> P2 hero; Q=-0.3477; prior=0.0000
- `0.000` — P1 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "END_033", "controller": 0, "created_by": null, "entity": 15, "kind": "play", "player": 0, "started_in_deck": true, "turn": 13}`

- P1: HP=22 Armor=0 Mana=0/7 Deck=20; Weapon=none; Board=Brood Keeper#5 2/2, Prescient Slitherdrake#15 5/8; Hand=Erupting Volcano(3), Erupting Volcano(3), Shadowflame Suffusion(2)
- P2: HP=20 Armor=2 Mana=0/6 Deck=21; Weapon=none; Board=Windpeak Wyrm#42 6/4, Royal Librarian#31 4/4; Hand=Sanguine Depths(1), Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1), Torch(1), Torch(1), Cannonmaster(1)

### Step 61: shared-tree-ismcts-v1

**P1 ATTACK Brood Keeper#5 -> P2 hero**

Legal actions: 4; Searched nodes: 5; Selected value: -0.0063

Top choices by root visit share:

- `0.250` — P1 ATTACK Brood Keeper#5 -> P2 hero [SELECTED]; Q=-0.0063; prior=0.0000
- `0.250` — P1 ATTACK Brood Keeper#5 -> P2 Royal Librarian#31; Q=-0.0997; prior=0.0000
- `0.250` — P1 ATTACK Brood Keeper#5 -> P2 Windpeak Wyrm#42; Q=-0.0997; prior=0.0000
- `0.250` — P1 END_TURN; Q=-0.4662; prior=0.0000

- P1: HP=22 Armor=0 Mana=0/7 Deck=20; Weapon=none; Board=Brood Keeper#5 2/2, Prescient Slitherdrake#15 5/8; Hand=Erupting Volcano(3), Erupting Volcano(3), Shadowflame Suffusion(2)
- P2: HP=20 Armor=0 Mana=0/6 Deck=21; Weapon=none; Board=Windpeak Wyrm#42 6/4, Royal Librarian#31 4/4; Hand=Sanguine Depths(1), Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1), Torch(1), Torch(1), Cannonmaster(1)

## Turn 14

### Step 62: shared-tree-ismcts-v1

**P1 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P1 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 0, "turn": 13}`
- `{"card": "EDR_456", "kind": "draw", "player": 1, "turn": 14}`
- `{"kind": "turn_start", "player": 1, "turn": 14}`

- P1: HP=22 Armor=0 Mana=0/7 Deck=20; Weapon=none; Board=Brood Keeper#5 2/2, Prescient Slitherdrake#15 5/8; Hand=Erupting Volcano(3), Erupting Volcano(3), Shadowflame Suffusion(2)
- P2: HP=20 Armor=0 Mana=7/7 Deck=20; Weapon=none; Board=Windpeak Wyrm#42 6/4, Royal Librarian#31 4/4; Hand=Sanguine Depths(1), Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1), Torch(1), Torch(1), Cannonmaster(1), Darkrider(1)

### Step 63: policy-prior-puct-v1

**P2 ATTACK Windpeak Wyrm#42 -> P1 hero**

Legal actions: 18; Searched nodes: 17; Selected value: 0.8207

Top choices by root visit share:

- `0.062` — P2 ATTACK Windpeak Wyrm#42 -> P1 hero [SELECTED]; Q=0.8207; prior=0.2107
- `0.062` — P2 ATTACK Royal Librarian#31 -> P1 hero; Q=0.7797; prior=0.1151
- `0.062` — P2 PLAY Cannonmaster[CAP_107] -> -; Q=0.5996; prior=0.0663
- `0.062` — P2 PLAY Carrier Whelp[CATA_556] -> -; Q=0.5491; prior=0.0412
- `0.062` — P2 HERO_POWER Armor Up; Q=0.5181; prior=0.0974

- P1: HP=16 Armor=0 Mana=0/7 Deck=20; Weapon=none; Board=Brood Keeper#5 2/2, Prescient Slitherdrake#15 5/8; Hand=Erupting Volcano(3), Erupting Volcano(3), Shadowflame Suffusion(2)
- P2: HP=20 Armor=0 Mana=7/7 Deck=20; Weapon=none; Board=Windpeak Wyrm#42 6/4, Royal Librarian#31 4/4; Hand=Sanguine Depths(1), Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1), Torch(1), Torch(1), Cannonmaster(1), Darkrider(1)

### Step 64: policy-prior-puct-v1

**P2 ATTACK Royal Librarian#31 -> P1 hero**

Legal actions: 15; Searched nodes: 17; Selected value: 0.9070

Top choices by root visit share:

- `0.125` — P2 ATTACK Royal Librarian#31 -> P1 hero [SELECTED]; Q=0.9070; prior=0.1813
- `0.062` — P2 PLAY Darkrider[EDR_456] -> -; Q=0.8846; prior=0.0656
- `0.062` — P2 ATTACK Royal Librarian#31 -> P1 Brood Keeper#5; Q=0.8836; prior=0.0414
- `0.062` — P2 PLAY Stadium Announcer[TIME_034] -> -; Q=0.8836; prior=0.0695
- `0.062` — P2 PLAY Cannonmaster[CAP_107] -> -; Q=0.8836; prior=0.0884

- P1: HP=12 Armor=0 Mana=0/7 Deck=20; Weapon=none; Board=Brood Keeper#5 2/2, Prescient Slitherdrake#15 5/8; Hand=Erupting Volcano(3), Erupting Volcano(3), Shadowflame Suffusion(2)
- P2: HP=20 Armor=0 Mana=7/7 Deck=20; Weapon=none; Board=Windpeak Wyrm#42 6/4, Royal Librarian#31 4/4; Hand=Sanguine Depths(1), Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1), Torch(1), Torch(1), Cannonmaster(1), Darkrider(1)

### Step 65: policy-prior-puct-v1

**P2 HERO_POWER Armor Up**

Legal actions: 12; Searched nodes: 17; Selected value: 0.9161

Top choices by root visit share:

- `0.188` — P2 HERO_POWER Armor Up [SELECTED]; Q=0.9161; prior=0.1784
- `0.125` — P2 PLAY Cannonmaster[CAP_107] -> -; Q=0.9325; prior=0.1132
- `0.125` — P2 PLAY Torch[CATA_585] -> P1 Brood Keeper#5; Q=0.9017; prior=0.0943
- `0.062` — P2 PLAY Darkrider[EDR_456] -> -; Q=0.9346; prior=0.0899
- `0.062` — P2 PLAY Stadium Announcer[TIME_034] -> -; Q=0.9340; prior=0.0883

Resolved events:

- `{"amount": 2, "kind": "gain_armor", "player": 1, "turn": 14}`
- `{"kind": "hero_power", "player": 1, "turn": 14}`

- P1: HP=12 Armor=0 Mana=0/7 Deck=20; Weapon=none; Board=Brood Keeper#5 2/2, Prescient Slitherdrake#15 5/8; Hand=Erupting Volcano(3), Erupting Volcano(3), Shadowflame Suffusion(2)
- P2: HP=20 Armor=2 Mana=5/7 Deck=20; Weapon=none; Board=Windpeak Wyrm#42 6/4, Royal Librarian#31 4/4; Hand=Sanguine Depths(1), Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1), Torch(1), Torch(1), Cannonmaster(1), Darkrider(1)

### Step 66: policy-prior-puct-v1

**P2 PLAY Cannonmaster[CAP_107] -> -**

Legal actions: 11; Searched nodes: 17; Selected value: 0.9343

Top choices by root visit share:

- `0.188` — P2 PLAY Cannonmaster[CAP_107] -> - [SELECTED]; Q=0.9343; prior=0.1391
- `0.125` — P2 PLAY Carrier Whelp[CATA_556] -> -; Q=0.9401; prior=0.1168
- `0.125` — P2 PLAY Stadium Announcer[TIME_034] -> -; Q=0.9228; prior=0.1201
- `0.125` — P2 PLAY Darkrider[EDR_456] -> -; Q=0.9133; prior=0.1325
- `0.062` — P2 PLAY Cannoneer[CAP_107t] -> -; Q=0.9234; prior=0.0975

Resolved events:

- `{"card": "CAP_107", "controller": 1, "created_by": null, "entity": 60, "kind": "play", "player": 1, "started_in_deck": true, "turn": 14}`
- `{"card": "CAP_107t", "entity": 79, "kind": "generated_to_hand", "player": 1, "source": "CAP_107", "turn": 14}`

- P1: HP=12 Armor=0 Mana=0/7 Deck=20; Weapon=none; Board=Brood Keeper#5 2/2, Prescient Slitherdrake#15 5/8; Hand=Erupting Volcano(3), Erupting Volcano(3), Shadowflame Suffusion(2)
- P2: HP=20 Armor=2 Mana=4/7 Deck=20; Weapon=none; Board=Windpeak Wyrm#42 6/4, Royal Librarian#31 4/4, Cannonmaster#60 3/1; Hand=Sanguine Depths(1), Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1), Torch(1), Torch(1), Darkrider(1), Cannoneer(1)

### Step 67: policy-prior-puct-v1

**P2 PLAY Torch[CATA_585] -> P1 Brood Keeper#5**

Legal actions: 11; Searched nodes: 17; Selected value: 0.9474

Top choices by root visit share:

- `0.125` — P2 PLAY Torch[CATA_585] -> P1 Brood Keeper#5 [SELECTED]; Q=0.9474; prior=0.1089
- `0.125` — P2 PLAY Carrier Whelp[CATA_556] -> -; Q=0.9474; prior=0.1085
- `0.125` — P2 PLAY Cannoneer[CAP_107t] -> -; Q=0.9416; prior=0.1394
- `0.125` — P2 PLAY Darkrider[EDR_456] -> -; Q=0.9360; prior=0.1248
- `0.125` — P2 PLAY Stadium Announcer[TIME_034] -> -; Q=0.8491; prior=0.1391

Resolved events:

- `{"card": "CATA_585", "controller": 1, "created_by": null, "entity": 53, "kind": "play", "player": 1, "started_in_deck": true, "turn": 14}`
- `{"card": "CATA_585", "destination": "hand", "entity": 53, "kind": "returned_to_hand", "player": 1, "source": "CATA_585", "turn": 14}`
- `{"card": "EDR_457", "entity": 5, "kind": "minion_died", "player": 0, "turn": 14}`

- P1: HP=12 Armor=0 Mana=0/7 Deck=20; Weapon=none; Board=Prescient Slitherdrake#15 5/8; Hand=Erupting Volcano(3), Erupting Volcano(3), Shadowflame Suffusion(2)
- P2: HP=20 Armor=2 Mana=3/7 Deck=20; Weapon=none; Board=Windpeak Wyrm#42 6/4, Royal Librarian#31 4/4, Cannonmaster#60 3/1; Hand=Sanguine Depths(1), Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1), Torch(1), Darkrider(1), Cannoneer(1), Torch(1)

### Step 68: policy-prior-puct-v1

**P2 PLAY Darkrider[EDR_456] -> -**

Legal actions: 8; Searched nodes: 17; Selected value: 0.9482

Top choices by root visit share:

- `0.250` — P2 PLAY Darkrider[EDR_456] -> - [SELECTED]; Q=0.9482; prior=0.2207
- `0.188` — P2 PLAY Cannoneer[CAP_107t] -> -; Q=0.9152; prior=0.1741
- `0.188` — P2 PLAY Carrier Whelp[CATA_556] -> -; Q=0.8849; prior=0.1746
- `0.125` — P2 PLAY Cannoneer[CAP_107t] -> -; Q=0.9012; prior=0.1542
- `0.062` — P2 PLAY Sanguine Depths[CORE_REV_990] -> -; Q=0.9254; prior=0.0489

Resolved events:

- `{"card": "EDR_456", "controller": 1, "created_by": null, "entity": 34, "kind": "play", "player": 1, "started_in_deck": true, "turn": 14}`
- `{"kind": "discover_offer", "options": [{"card": "CORE_UNG_848", "entity": 80, "gifts": ["harpys_talons"]}, {"card": "EDR_260", "entity": 81, "gifts": ["sleepwalker"]}, {"card": "CATA_556", "entity": 82, "gifts": ["well_rested"]}], "player": 1, "profile": "closed_pool", "turn": 14}`

- P1: HP=12 Armor=0 Mana=0/7 Deck=20; Weapon=none; Board=Prescient Slitherdrake#15 5/8; Hand=Erupting Volcano(3), Erupting Volcano(3), Shadowflame Suffusion(2)
- P2: HP=20 Armor=2 Mana=2/7 Deck=20; Weapon=none; Board=Windpeak Wyrm#42 6/4, Royal Librarian#31 4/4, Cannonmaster#60 3/1, Darkrider#34 1/1; Hand=Sanguine Depths(1), Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1), Torch(1), Cannoneer(1), Torch(1)

### Step 69: policy-prior-puct-v1

**P2 DISCOVER_PICK Illusory Greenwing[EDR_260] + sleepwalker**

Legal actions: 3; Searched nodes: 7; Selected value: 0.8773

Top choices by root visit share:

- `0.500` — P2 DISCOVER_PICK Illusory Greenwing[EDR_260] + sleepwalker [SELECTED]; Q=0.8773; prior=0.5553
- `0.333` — P2 DISCOVER_PICK Primordial Drake[CORE_UNG_848] + harpys_talons; Q=0.8941; prior=0.2663
- `0.167` — P2 DISCOVER_PICK Carrier Whelp[CATA_556] + well_rested; Q=0.9601; prior=0.1784

Resolved events:

- `{"card": "EDR_260", "destination": "hand", "entity": 81, "gifts": ["sleepwalker"], "kind": "discover_pick", "player": 1, "source": "EDR_456", "turn": 14}`

- P1: HP=12 Armor=0 Mana=0/7 Deck=20; Weapon=none; Board=Prescient Slitherdrake#15 5/8; Hand=Erupting Volcano(3), Erupting Volcano(3), Shadowflame Suffusion(2)
- P2: HP=20 Armor=2 Mana=2/7 Deck=20; Weapon=none; Board=Windpeak Wyrm#42 6/4, Royal Librarian#31 4/4, Cannonmaster#60 3/1, Darkrider#34 1/1; Hand=Sanguine Depths(1), Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1), Torch(1), Cannoneer(1), Torch(1), Illusory Greenwing(4)

### Step 70: policy-prior-puct-v1

**P2 PLAY Sanguine Depths[CORE_REV_990] -> -**

Legal actions: 7; Searched nodes: 15; Selected value: 0.3506

Top choices by root visit share:

- `0.286` — P2 PLAY Sanguine Depths[CORE_REV_990] -> - [SELECTED]; Q=0.3506; prior=0.0596
- `0.214` — P2 PLAY Cannoneer[CAP_107t] -> -; Q=0.4525; prior=0.2119
- `0.143` — P2 PLAY Cannoneer[CAP_107t] -> -; Q=0.2624; prior=0.1856
- `0.143` — P2 PLAY Carrier Whelp[CATA_556] -> -; Q=0.2607; prior=0.2086
- `0.071` — P2 PLAY Torch[CATA_585] -> P2 Windpeak Wyrm#42; Q=0.4733; prior=0.0750

Resolved events:

- `{"card": "CORE_REV_990", "controller": 1, "created_by": null, "entity": 32, "kind": "play", "player": 1, "started_in_deck": true, "turn": 14}`

- P1: HP=12 Armor=0 Mana=0/7 Deck=20; Weapon=none; Board=Prescient Slitherdrake#15 5/8; Hand=Erupting Volcano(3), Erupting Volcano(3), Shadowflame Suffusion(2)
- P2: HP=20 Armor=2 Mana=1/7 Deck=20; Weapon=none; Board=Windpeak Wyrm#42 6/4, Royal Librarian#31 4/4, Cannonmaster#60 3/1, Darkrider#34 1/1; Hand=Cannoneer(1), Stadium Announcer(4), Carrier Whelp(1), Torch(1), Cannoneer(1), Torch(1), Illusory Greenwing(4)

### Step 71: policy-prior-puct-v1

**P2 PLAY Cannoneer[CAP_107t] -> -**

Legal actions: 6; Searched nodes: 13; Selected value: 0.5690

Top choices by root visit share:

- `0.333` — P2 PLAY Cannoneer[CAP_107t] -> - [SELECTED]; Q=0.5690; prior=0.1758
- `0.250` — P2 PLAY Cannoneer[CAP_107t] -> -; Q=0.3371; prior=0.2222
- `0.167` — P2 PLAY Carrier Whelp[CATA_556] -> -; Q=0.5741; prior=0.2075
- `0.083` — P2 PLAY Torch[CATA_585] -> P2 Windpeak Wyrm#42; Q=-0.1160; prior=0.0967
- `0.083` — P2 END_TURN; Q=-0.2713; prior=0.2005

Resolved events:

- `{"card": "CAP_107t", "controller": 1, "created_by": "CAP_107", "entity": 69, "kind": "play", "player": 1, "started_in_deck": false, "turn": 14}`

- P1: HP=12 Armor=0 Mana=0/7 Deck=20; Weapon=none; Board=Prescient Slitherdrake#15 5/8; Hand=Erupting Volcano(3), Erupting Volcano(3), Shadowflame Suffusion(2)
- P2: HP=20 Armor=2 Mana=0/7 Deck=20; Weapon=none; Board=Windpeak Wyrm#42 6/4, Royal Librarian#31 4/4, Cannonmaster#60 3/1, Darkrider#34 1/1, Cannoneer#69 1/1; Hand=Stadium Announcer(4), Carrier Whelp(1), Torch(1), Cannoneer(1), Torch(1), Illusory Greenwing(4)

## Turn 15

### Step 72: policy-prior-puct-v1

**P2 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P2 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 1, "turn": 14}`
- `{"card": "CAP_105", "kind": "draw", "player": 0, "turn": 15}`
- `{"kind": "turn_start", "player": 0, "turn": 15}`

- P1: HP=11 Armor=0 Mana=8/8 Deck=19; Weapon=none; Board=Prescient Slitherdrake#15 5/8; Hand=Erupting Volcano(3), Erupting Volcano(3), Shadowflame Suffusion(2), Hook n' Heave(2)
- P2: HP=20 Armor=2 Mana=0/7 Deck=20; Weapon=none; Board=Windpeak Wyrm#42 6/4, Royal Librarian#31 4/4, Cannonmaster#60 3/1, Darkrider#34 1/1, Cannoneer#69 1/1; Hand=Stadium Announcer(4), Carrier Whelp(1), Torch(1), Cannoneer(1), Torch(1), Illusory Greenwing(4)

### Step 73: shared-tree-ismcts-v1

**P1 ATTACK Prescient Slitherdrake#15 -> P2 Windpeak Wyrm#42**

Legal actions: 19; Searched nodes: 5; Selected value: -0.3417

Top choices by root visit share:

- `0.250` — P1 ATTACK Prescient Slitherdrake#15 -> P2 Windpeak Wyrm#42 [SELECTED]; Q=-0.3417; prior=0.0000
- `0.250` — P1 ATTACK Prescient Slitherdrake#15 -> P2 Royal Librarian#31; Q=-0.4887; prior=0.0000
- `0.250` — P1 ATTACK Prescient Slitherdrake#15 -> P2 Cannonmaster#60; Q=-0.6414; prior=0.0000
- `0.250` — P1 ATTACK Prescient Slitherdrake#15 -> P2 Cannoneer#69; Q=-0.6650; prior=0.0000
- `0.000` — P1 ATTACK Prescient Slitherdrake#15 -> P2 hero; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "TLC_600", "entity": 42, "kind": "minion_died", "player": 1, "turn": 15}`

- P1: HP=11 Armor=0 Mana=8/8 Deck=19; Weapon=none; Board=Prescient Slitherdrake#15 5/2; Hand=Erupting Volcano(3), Erupting Volcano(3), Shadowflame Suffusion(2), Hook n' Heave(2)
- P2: HP=20 Armor=2 Mana=0/7 Deck=20; Weapon=none; Board=Royal Librarian#31 4/4, Cannonmaster#60 3/1, Darkrider#34 1/1, Cannoneer#69 1/1; Hand=Stadium Announcer(4), Carrier Whelp(1), Torch(1), Cannoneer(1), Torch(1), Illusory Greenwing(4)

### Step 74: shared-tree-ismcts-v1

**P1 PLAY Shadowflame Suffusion[FIR_939] -> P2 Cannonmaster#60**

Legal actions: 12; Searched nodes: 5; Selected value: -0.2083

Top choices by root visit share:

- `0.250` — P1 PLAY Shadowflame Suffusion[FIR_939] -> P2 Cannonmaster#60 [SELECTED]; Q=-0.2083; prior=0.0000
- `0.250` — P1 PLAY Shadowflame Suffusion[FIR_939] -> P2 Darkrider#34; Q=-0.3105; prior=0.0000
- `0.250` — P1 PLAY Shadowflame Suffusion[FIR_939] -> P2 Cannoneer#69; Q=-0.3105; prior=0.0000
- `0.250` — P1 PLAY Shadowflame Suffusion[FIR_939] -> P2 Royal Librarian#31; Q=-0.3592; prior=0.0000
- `0.000` — P1 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "FIR_939", "controller": 0, "created_by": null, "entity": 9, "kind": "play", "player": 0, "started_in_deck": true, "turn": 15}`
- `{"kind": "discover_offer", "options": [{"card": "FIR_956", "entity": 83, "gifts": ["short_claws"]}, {"card": "CATA_586", "entity": 84, "gifts": ["waking_terror"]}, {"card": "EDR_457", "entity": 85, "gifts": ["bundled_up"]}], "player": 0, "profile": "closed_pool", "turn": 15}`
- `{"card": "CAP_107", "entity": 60, "kind": "minion_died", "player": 1, "turn": 15}`

- P1: HP=11 Armor=0 Mana=6/8 Deck=19; Weapon=none; Board=Prescient Slitherdrake#15 5/2; Hand=Erupting Volcano(3), Erupting Volcano(3), Hook n' Heave(2)
- P2: HP=20 Armor=2 Mana=0/7 Deck=20; Weapon=none; Board=Royal Librarian#31 4/4, Darkrider#34 1/1, Cannoneer#69 1/1; Hand=Stadium Announcer(4), Carrier Whelp(1), Torch(1), Cannoneer(1), Torch(1), Illusory Greenwing(4)

### Step 75: shared-tree-ismcts-v1

**P1 DISCOVER_PICK Destructive Blaze[CATA_586] + waking_terror**

Legal actions: 3; Searched nodes: 5; Selected value: 0.2469

Top choices by root visit share:

- `0.500` — P1 DISCOVER_PICK Destructive Blaze[CATA_586] + waking_terror [SELECTED]; Q=0.2469; prior=0.0000
- `0.250` — P1 DISCOVER_PICK Brood Keeper[EDR_457] + bundled_up; Q=-0.3940; prior=0.0000
- `0.250` — P1 DISCOVER_PICK Dragon Turtle[FIR_956] + short_claws; Q=-0.4531; prior=0.0000

Resolved events:

- `{"card": "CATA_586", "destination": "hand", "entity": 84, "gifts": ["waking_terror"], "kind": "discover_pick", "player": 0, "source": "FIR_939", "turn": 15}`

- P1: HP=11 Armor=0 Mana=6/8 Deck=19; Weapon=none; Board=Prescient Slitherdrake#15 5/2; Hand=Erupting Volcano(3), Erupting Volcano(3), Hook n' Heave(2), Destructive Blaze(5)
- P2: HP=20 Armor=2 Mana=0/7 Deck=20; Weapon=none; Board=Royal Librarian#31 4/4, Darkrider#34 1/1, Cannoneer#69 1/1; Hand=Stadium Announcer(4), Carrier Whelp(1), Torch(1), Cannoneer(1), Torch(1), Illusory Greenwing(4)

### Step 76: shared-tree-ismcts-v1

**P1 PLAY Destructive Blaze[CATA_586] -> -**

Legal actions: 6; Searched nodes: 5; Selected value: 0.2887

Top choices by root visit share:

- `0.250` — P1 PLAY Destructive Blaze[CATA_586] -> - [SELECTED]; Q=0.2887; prior=0.0000
- `0.250` — P1 PLAY Hook n' Heave[CAP_105] -> -; Q=-0.5222; prior=0.0000
- `0.250` — P1 PLAY Erupting Volcano[CATA_584] -> -; Q=-0.7511; prior=0.0000
- `0.250` — P1 PLAY Erupting Volcano[CATA_584] -> -; Q=-0.7511; prior=0.0000
- `0.000` — P1 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"card": "CATA_586", "controller": 0, "created_by": "FIR_939", "entity": 84, "kind": "play", "player": 0, "started_in_deck": false, "turn": 15}`

- P1: HP=11 Armor=0 Mana=1/8 Deck=19; Weapon=none; Board=Prescient Slitherdrake#15 5/2, Destructive Blaze#84 6/3; Hand=Erupting Volcano(3), Erupting Volcano(3), Hook n' Heave(2)
- P2: HP=20 Armor=2 Mana=0/7 Deck=20; Weapon=none; Board=Royal Librarian#31 4/4, Darkrider#34 1/1, Cannoneer#69 1/1; Hand=Stadium Announcer(4), Carrier Whelp(1), Torch(1), Cannoneer(1), Torch(1), Illusory Greenwing(4)

## Turn 16

### Step 77: shared-tree-ismcts-v1

**P1 END_TURN**

Legal actions: 1; Searched nodes: 1; Selected value: 0.0000

Top choices by root visit share:

- `1.000` — P1 END_TURN; Q=0.0000; prior=0.0000

Resolved events:

- `{"kind": "turn_end", "player": 0, "turn": 15}`
- `{"card": "FIR_939", "kind": "draw", "player": 1, "turn": 16}`
- `{"kind": "turn_start", "player": 1, "turn": 16}`

- P1: HP=11 Armor=0 Mana=1/8 Deck=19; Weapon=none; Board=Prescient Slitherdrake#15 5/2, Destructive Blaze#84 6/3; Hand=Erupting Volcano(3), Erupting Volcano(3), Hook n' Heave(2)
- P2: HP=20 Armor=2 Mana=8/8 Deck=19; Weapon=none; Board=Royal Librarian#31 4/4, Darkrider#34 1/1, Cannoneer#69 1/1; Hand=Stadium Announcer(4), Carrier Whelp(1), Torch(1), Cannoneer(1), Torch(1), Illusory Greenwing(4), Shadowflame Suffusion(2)

### Step 78: policy-prior-puct-v1

**P2 PLAY Stadium Announcer[TIME_034] -> -**

Legal actions: 26; Searched nodes: 17; Selected value: 0.8163

Top choices by root visit share:

- `0.062` — P2 PLAY Stadium Announcer[TIME_034] -> - [SELECTED]; Q=0.8163; prior=0.0381
- `0.062` — P2 ATTACK Royal Librarian#31 -> P1 Destructive Blaze#84; Q=0.6701; prior=0.0309
- `0.062` — P2 LOCATION CORE_REV_990#32 -> P2 Darkrider#34; Q=0.4943; prior=0.0455
- `0.062` — P2 LOCATION CORE_REV_990#32 -> P2 Cannoneer#69; Q=0.4943; prior=0.0422
- `0.062` — P2 ATTACK Darkrider#34 -> P1 hero; Q=0.3902; prior=0.0373

Resolved events:

- `{"card": "TIME_034", "controller": 1, "created_by": null, "entity": 44, "kind": "play", "player": 1, "started_in_deck": true, "turn": 16}`
- `{"attack": 4, "card": "CORE_OG_031", "durability": 2, "kind": "equip_weapon", "player": 0, "turn": 16}`
- `{"attack": 5, "card": "RLK_067", "durability": 2, "kind": "equip_weapon", "player": 1, "turn": 16}`
- `{"effect": "stadium_weapons", "kind": "rewind_offer", "outcome": [{"attack": 4, "card": "CORE_OG_031", "durability": 2, "name": "Hammer of Twilight"}, {"attack": 6, "card": "RLK_067", "durability": 3, "name": "Corrupted Ashbringer"}], "player": 1, "restorable": true, "turn": 16}`

- P1: HP=11 Armor=0 Mana=1/8 Deck=19; Weapon=Hammer of Twilight 4/2; Board=Prescient Slitherdrake#15 5/2, Destructive Blaze#84 6/3; Hand=Erupting Volcano(3), Erupting Volcano(3), Hook n' Heave(2)
- P2: HP=20 Armor=2 Mana=4/8 Deck=19; Weapon=Corrupted Ashbringer 6/3; Board=Royal Librarian#31 4/4, Darkrider#34 1/1, Cannoneer#69 1/1, Stadium Announcer#44 3/3; Hand=Carrier Whelp(1), Torch(1), Cannoneer(1), Torch(1), Illusory Greenwing(4), Shadowflame Suffusion(2)

### Step 79: policy-prior-puct-v1

**P2 REWIND_KEEP**

Legal actions: 2; Searched nodes: 5; Selected value: 0.8503

Top choices by root visit share:

- `0.500` — P2 REWIND_KEEP [SELECTED]; Q=0.8503; prior=0.3585
- `0.500` — P2 REWIND_RETRY; Q=0.6951; prior=0.6415

Resolved events:

- `{"decision": "keep", "effect": "stadium_weapons", "kind": "rewind_pick", "outcome": [{"attack": 4, "card": "CORE_OG_031", "durability": 2, "name": "Hammer of Twilight"}, {"attack": 6, "card": "RLK_067", "durability": 3, "name": "Corrupted Ashbringer"}], "player": 1, "turn": 16}`

- P1: HP=11 Armor=0 Mana=1/8 Deck=19; Weapon=Hammer of Twilight 4/2; Board=Prescient Slitherdrake#15 5/2, Destructive Blaze#84 6/3; Hand=Erupting Volcano(3), Erupting Volcano(3), Hook n' Heave(2)
- P2: HP=20 Armor=2 Mana=4/8 Deck=19; Weapon=Corrupted Ashbringer 6/3; Board=Royal Librarian#31 4/4, Darkrider#34 1/1, Cannoneer#69 1/1, Stadium Announcer#44 3/3; Hand=Carrier Whelp(1), Torch(1), Cannoneer(1), Torch(1), Illusory Greenwing(4), Shadowflame Suffusion(2)

### Step 80: policy-prior-puct-v1

**P2 ATTACK Royal Librarian#31 -> P1 hero**

Legal actions: 30; Searched nodes: 17; Selected value: 0.9824

Top choices by root visit share:

- `0.062` — P2 ATTACK Royal Librarian#31 -> P1 hero [SELECTED]; Q=0.9824; prior=0.0322
- `0.062` — P2 PLAY Illusory Greenwing[EDR_260] -> -; Q=0.9590; prior=0.0866
- `0.062` — P2 HERO_ATTACK -> P1 hero; Q=0.8882; prior=0.0432
- `0.062` — P2 PLAY Carrier Whelp[CATA_556] -> -; Q=0.8765; prior=0.0309
- `0.062` — P2 HERO_POWER Armor Up; Q=0.8661; prior=0.1809

- P1: HP=7 Armor=0 Mana=1/8 Deck=19; Weapon=Hammer of Twilight 4/2; Board=Prescient Slitherdrake#15 5/2, Destructive Blaze#84 6/3; Hand=Erupting Volcano(3), Erupting Volcano(3), Hook n' Heave(2)
- P2: HP=20 Armor=2 Mana=4/8 Deck=19; Weapon=Corrupted Ashbringer 6/3; Board=Royal Librarian#31 4/4, Darkrider#34 1/1, Cannoneer#69 1/1, Stadium Announcer#44 3/3; Hand=Carrier Whelp(1), Torch(1), Cannoneer(1), Torch(1), Illusory Greenwing(4), Shadowflame Suffusion(2)

### Step 81: policy-prior-puct-v1

**P2 PLAY Shadowflame Suffusion[FIR_939] -> P1 hero**

Legal actions: 27; Searched nodes: 17; Selected value: 1.0000

Top choices by root visit share:

- `0.062` — P2 PLAY Shadowflame Suffusion[FIR_939] -> P1 hero [SELECTED]; Q=1.0000; prior=0.0337
- `0.062` — P2 ATTACK Darkrider#34 -> P1 hero; Q=1.0000; prior=0.0302
- `0.062` — P2 ATTACK Cannoneer#69 -> P1 hero; Q=1.0000; prior=0.0267
- `0.062` — P2 HERO_ATTACK -> P1 hero; Q=1.0000; prior=0.0618
- `0.062` — P2 PLAY Carrier Whelp[CATA_556] -> -; Q=0.9871; prior=0.0311

Resolved events:

- `{"card": "FIR_939", "controller": 1, "created_by": null, "entity": 39, "kind": "play", "player": 1, "started_in_deck": true, "turn": 16}`
- `{"kind": "discover_offer", "options": [{"card": "JAIL_384", "entity": 86, "gifts": ["well_rested"]}, {"card": "END_021", "entity": 87, "gifts": ["rude_awakening"]}, {"card": "EDR_465", "entity": 88, "gifts": ["persisting_horror"]}], "player": 1, "profile": "closed_pool", "turn": 16}`

- P1: HP=5 Armor=0 Mana=1/8 Deck=19; Weapon=Hammer of Twilight 4/2; Board=Prescient Slitherdrake#15 5/2, Destructive Blaze#84 6/3; Hand=Erupting Volcano(3), Erupting Volcano(3), Hook n' Heave(2)
- P2: HP=20 Armor=2 Mana=2/8 Deck=19; Weapon=Corrupted Ashbringer 6/3; Board=Royal Librarian#31 4/4, Darkrider#34 1/1, Cannoneer#69 1/1, Stadium Announcer#44 3/3; Hand=Carrier Whelp(1), Torch(1), Cannoneer(1), Torch(1), Illusory Greenwing(4)

### Step 82: policy-prior-puct-v1

**P2 DISCOVER_PICK Chainbreaker Hogger[JAIL_384] + well_rested**

Legal actions: 3; Searched nodes: 7; Selected value: 1.0000

Top choices by root visit share:

- `0.333` — P2 DISCOVER_PICK Chainbreaker Hogger[JAIL_384] + well_rested [SELECTED]; Q=1.0000; prior=0.3890
- `0.333` — P2 DISCOVER_PICK Dimensional Weaponsmith[END_021] + rude_awakening; Q=1.0000; prior=0.2811
- `0.333` — P2 DISCOVER_PICK Ysondre[EDR_465] + persisting_horror; Q=1.0000; prior=0.3300

Resolved events:

- `{"card": "JAIL_384", "destination": "hand", "entity": 86, "gifts": ["well_rested"], "kind": "discover_pick", "player": 1, "source": "FIR_939", "turn": 16}`

- P1: HP=5 Armor=0 Mana=1/8 Deck=19; Weapon=Hammer of Twilight 4/2; Board=Prescient Slitherdrake#15 5/2, Destructive Blaze#84 6/3; Hand=Erupting Volcano(3), Erupting Volcano(3), Hook n' Heave(2)
- P2: HP=20 Armor=2 Mana=2/8 Deck=19; Weapon=Corrupted Ashbringer 6/3; Board=Royal Librarian#31 4/4, Darkrider#34 1/1, Cannoneer#69 1/1, Stadium Announcer#44 3/3; Hand=Carrier Whelp(1), Torch(1), Cannoneer(1), Torch(1), Illusory Greenwing(4), Chainbreaker Hogger(8)

### Step 83: policy-prior-puct-v1

**P2 PLAY Carrier Whelp[CATA_556] -> -**

Legal actions: 19; Searched nodes: 17; Selected value: 1.0000

Top choices by root visit share:

- `0.062` — P2 PLAY Carrier Whelp[CATA_556] -> - [SELECTED]; Q=1.0000; prior=0.0364
- `0.062` — P2 ATTACK Darkrider#34 -> P1 hero; Q=1.0000; prior=0.0468
- `0.062` — P2 ATTACK Darkrider#34 -> P1 Prescient Slitherdrake#15; Q=1.0000; prior=0.0370
- `0.062` — P2 ATTACK Cannoneer#69 -> P1 hero; Q=1.0000; prior=0.0418
- `0.062` — P2 HERO_ATTACK -> P1 hero; Q=1.0000; prior=0.0952

Resolved events:

- `{"card": "CATA_556", "controller": 1, "created_by": "CATA_556", "entity": 75, "kind": "play", "player": 1, "started_in_deck": false, "turn": 16}`
- `{"card": "CATA_556", "entity": 89, "kind": "generated_to_hand", "player": 1, "source": "CATA_556", "turn": 16}`

- P1: HP=5 Armor=0 Mana=1/8 Deck=19; Weapon=Hammer of Twilight 4/2; Board=Prescient Slitherdrake#15 5/2, Destructive Blaze#84 6/3; Hand=Erupting Volcano(3), Erupting Volcano(3), Hook n' Heave(2)
- P2: HP=20 Armor=2 Mana=1/8 Deck=19; Weapon=Corrupted Ashbringer 6/3; Board=Royal Librarian#31 4/4, Darkrider#34 1/1, Cannoneer#69 1/1, Stadium Announcer#44 3/3, Carrier Whelp#75 1/2; Hand=Torch(1), Cannoneer(1), Torch(1), Illusory Greenwing(4), Chainbreaker Hogger(8), Carrier Whelp(1)

### Step 84: policy-prior-puct-v1

**P2 PLAY Carrier Whelp[CATA_556] -> -**

Legal actions: 19; Searched nodes: 17; Selected value: 1.0000

Top choices by root visit share:

- `0.062` — P2 PLAY Carrier Whelp[CATA_556] -> - [SELECTED]; Q=1.0000; prior=0.0835
- `0.062` — P2 ATTACK Darkrider#34 -> P1 hero; Q=1.0000; prior=0.0468
- `0.062` — P2 ATTACK Darkrider#34 -> P1 Prescient Slitherdrake#15; Q=1.0000; prior=0.0399
- `0.062` — P2 ATTACK Cannoneer#69 -> P1 hero; Q=1.0000; prior=0.0424
- `0.062` — P2 HERO_ATTACK -> P1 hero; Q=1.0000; prior=0.0935

Resolved events:

- `{"card": "CATA_556", "controller": 1, "created_by": "CATA_556", "entity": 89, "kind": "play", "player": 1, "started_in_deck": false, "turn": 16}`
- `{"card": "CATA_556", "entity": 90, "kind": "generated_to_hand", "player": 1, "source": "CATA_556", "turn": 16}`

- P1: HP=5 Armor=0 Mana=1/8 Deck=19; Weapon=Hammer of Twilight 4/2; Board=Prescient Slitherdrake#15 5/2, Destructive Blaze#84 6/3; Hand=Erupting Volcano(3), Erupting Volcano(3), Hook n' Heave(2)
- P2: HP=20 Armor=2 Mana=0/8 Deck=19; Weapon=Corrupted Ashbringer 6/3; Board=Royal Librarian#31 4/4, Darkrider#34 1/1, Cannoneer#69 1/1, Stadium Announcer#44 3/3, Carrier Whelp#75 1/2, Carrier Whelp#89 1/2; Hand=Torch(1), Cannoneer(1), Torch(1), Illusory Greenwing(4), Chainbreaker Hogger(8), Carrier Whelp(1)

### Step 85: policy-prior-puct-v1

**P2 LOCATION CORE_REV_990#32 -> P2 Stadium Announcer#44**

Legal actions: 18; Searched nodes: 17; Selected value: 1.0000

Top choices by root visit share:

- `0.062` — P2 LOCATION CORE_REV_990#32 -> P2 Stadium Announcer#44 [SELECTED]; Q=1.0000; prior=0.0658
- `0.062` — P2 ATTACK Darkrider#34 -> P1 hero; Q=1.0000; prior=0.0493
- `0.062` — P2 ATTACK Darkrider#34 -> P1 Prescient Slitherdrake#15; Q=1.0000; prior=0.0440
- `0.062` — P2 ATTACK Cannoneer#69 -> P1 hero; Q=1.0000; prior=0.0464
- `0.062` — P2 HERO_ATTACK -> P1 hero; Q=1.0000; prior=0.0887

- P1: HP=5 Armor=0 Mana=1/8 Deck=19; Weapon=Hammer of Twilight 4/2; Board=Prescient Slitherdrake#15 5/2, Destructive Blaze#84 6/3; Hand=Erupting Volcano(3), Erupting Volcano(3), Hook n' Heave(2)
- P2: HP=20 Armor=2 Mana=0/8 Deck=19; Weapon=Corrupted Ashbringer 6/3; Board=Royal Librarian#31 4/4, Darkrider#34 1/1, Cannoneer#69 1/1, Stadium Announcer#44 5/2, Carrier Whelp#75 1/2, Carrier Whelp#89 1/2; Hand=Torch(1), Cannoneer(1), Torch(1), Illusory Greenwing(4), Chainbreaker Hogger(8), Carrier Whelp(1)

### Step 86: policy-prior-puct-v1

**P2 HERO_ATTACK -> P1 hero**

Legal actions: 10; Searched nodes: 14; Selected value: 1.0000

Top choices by root visit share:

- `0.250` — P2 HERO_ATTACK -> P1 hero [SELECTED]; Q=1.0000; prior=0.1853
- `0.125` — P2 ATTACK Darkrider#34 -> P1 hero; Q=1.0000; prior=0.1031
- `0.125` — P2 ATTACK Darkrider#34 -> P1 Prescient Slitherdrake#15; Q=1.0000; prior=0.0940
- `0.125` — P2 ATTACK Cannoneer#69 -> P1 hero; Q=1.0000; prior=0.0980
- `0.062` — P2 ATTACK Cannoneer#69 -> P1 Prescient Slitherdrake#15; Q=1.0000; prior=0.0783

- P1: HP=-1 Armor=0 Mana=1/8 Deck=19; Weapon=Hammer of Twilight 4/2; Board=Prescient Slitherdrake#15 5/2, Destructive Blaze#84 6/3; Hand=Erupting Volcano(3), Erupting Volcano(3), Hook n' Heave(2)
- P2: HP=26 Armor=2 Mana=0/8 Deck=19; Weapon=Corrupted Ashbringer 6/2; Board=Royal Librarian#31 4/4, Darkrider#34 1/1, Cannoneer#69 1/1, Stadium Announcer#44 5/2, Carrier Whelp#75 1/2, Carrier Whelp#89 1/2; Hand=Torch(1), Cannoneer(1), Torch(1), Illusory Greenwing(4), Chainbreaker Hogger(8), Carrier Whelp(1)


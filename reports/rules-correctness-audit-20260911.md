# Rules correctness audit — 2026-09-11

## Scope and evidence

This audit compares the pinned HearthstoneJSON build 251332 card text with the
Dragon Warrior vertical-slice implementation and its reachable generation
pools. HearthstoneJSON supplies card metadata and localized text; it is not an
executable source of game rules. RosettaStone and Fireplace are useful
references for older cards, but neither contains the current 2025-2026 card set
needed by this deck.

## Cannoneer finding

`CAP_107t` is a normal 1/1 minion. It has two independent behaviours:

1. after summoning sickness it may take one ordinary minion attack each turn;
2. at the end of its controller's turn it fires one triggered shot that deals
   1 damage to a random enemy.

The simulator already exposed the first behaviour through the generic `ATTACK`
action and resolved the second in the end-turn trigger queue. The trace omitted
an explicit damage event, making the shot invisible and easy to misread as an
attack. Ruleset v4 records every shot as `cannoneer_shot`, including source,
target, reason, and damage, and the Chinese renderer explicitly labels it as a
trigger rather than a minion attack.

Captain Crowley (`CAP_106`) says Cannoneers fire an additional shot. The old
implementation applied this at natural end of turn but not when Hand Cannon
(`CAP_103`) caused Cannoneers to fire. Ruleset v4 routes both firing sources
through one helper and applies the additional shot consistently.

## Confirmed cross-card bug fixed

The old engine used the same enemy-character function for manual targeting and
random selection. That incorrectly excluded Stealth minions from random damage.
Ruleset v4 separates:

- `_enemy_characters`: legal manually targetable enemies, excluding Stealth;
- `_random_enemy_characters`: random-effect population, including Stealth and
  excluding Dormant entities.

All implemented automatic random-enemy damage and selection paths now use the
second population.

## Remaining confidence limits

The current runtime recognizes 281 entities, but recognition is not equivalent
to complete semantic validation:

- 41 entries have executable declarative effects;
- 1 entry is a focused legacy special case recorded in the rule catalogue;
- 239 are still legacy compatibility implementations;
- only 78 have a matching reference in the pinned RosettaStone or Fireplace
  snapshots;
- the direct Dragon Warrior deck has focused coverage for all 17 unique cards,
  but generated-card closure is intentionally incomplete.

The current generation audit still reports these high-priority omissions:

- 5 eligible Dragons;
- 1 eligible Warrior minion;
- 3 eligible weapons;
- deeper transitive pools, including 5-Cost, 2-Cost, 4-Cost, Legendary,
  historical, and class-card generation, remain substantially incomplete.

Consequently the engine must still be described as a closed Dragon Warrior
vertical slice, not a complete Standard simulator. Discover and random
generation are restricted to supported closed pools, so they do not yet match
the full live-client candidate population.

One known partial mechanic remains: Inspiring Maul (`CATA_472`) can trigger a
Cannoneer's end-turn effect, but the generic catalogue and dispatcher for every
eligible friendly end-turn effect is not complete. This must be closed before
claiming full correctness for random Stadium weapon outcomes.

## Model validity

The structured v5 checkpoint was trained and evaluated under ruleset v3. Since
v4 changes reachable outcomes, its 75/104 result against ordinary ISMCTS remains
a historical baseline. A new v4 dataset and checkpoint are required before a
neural policy is promoted again.

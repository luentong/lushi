# Card rule architecture

## Data and behavior boundaries

HearthstoneJSON build 251332 is the pinned source for names, costs, stats,
types, races, keywords, targeting metadata, and linked token IDs. It is not an
executable specification. Runtime behavior is split into three layers:

1. `hsa.rules`: composable hooks and effects for ordinary cards;
2. `hsa.dragon_mirror`: game state, event ordering, legal actions, and a
   compatibility layer for cards not migrated yet;
3. explicit special handlers for effects that cannot be expressed safely by
   the current effect vocabulary.

Declarative rules are registered by card ID and hook:

```python
CardRule(
    "CORE_EX1_110",
    {Hook.DEATHRATTLE: (Summon("EX1_110t"),)},
    RuleSource(...),
)
```

Fixed generated entities are listed in `DECLARATIVE_METADATA_IDS`; their base
stats, tribes, card type, spell school, and keywords are loaded from the same
pinned HearthstoneJSON snapshot as constructed cards. Historical/Core ID
differences use the explicit `DECLARATIVE_METADATA_ALIASES` mapping. Handwritten
`CardDef` objects are reserved for entities absent from that snapshot.

Every rule carries provenance and one or more verification tests. The runtime
does not execute upstream code. RosettaStone and Fireplace are reference-only
AGPL-3.0 sources used to locate historical implementations and verify timing
semantics; adaptations are expressed independently using this project's effect
API.

## Migration rules

- Do not add a new branch to `_battlecry` or `_deathrattle` when existing
  effects can express the behavior.
- Add a reusable effect when at least two cards share the operation and its
  timing is unambiguous.
- Keep selectors explicit (`controller`, `opponent`, zone, type, race, cost).
- Keep random choice inside the deterministic game RNG.
- Preserve entity IDs, hand and board limits, generated-card attribution, and
  event logging in every effect.
- A card moves out of the compatibility layer only after its existing focused
  tests and the full mirror regression suite pass unchanged.
- New or changed Standard cards require a pinned HearthstoneJSON build and, if
  available, a real Power.log trace for differential verification.

## Upstream audit

Run:

```bash
python scripts/audit_card_rules.py
```

The scanner searches exact IDs and historical aliases such as
`CORE_EX1_100 -> EX1_100` in the pinned RosettaStone and Fireplace trees. It
writes:

- `reports/card_rule_manifest.json`: full provenance and exact source matches;
- `reports/card_rule_manifest.csv`: compact planning view.

The audit also parses `tests/test_*.py` and fails if any declarative rule names
a verification test that does not exist. This keeps provenance from silently
degrading into an unchecked label.

An upstream match is evidence and a migration lead, not proof that the current
Standard printing behaves identically. Stats, text, linked entities, and timing
must still be checked against build 251332 and focused tests.

## Planned extraction order

1. Complete simple `Draw`, `Summon`, `Damage`, `Heal`, `Buff`, and generated
   hand-card rules.
2. Extract target selectors and conditional predicates.
3. Extract continuous auras and cost modifiers.
4. Extract attack, draw, play, turn-start, and turn-end triggers.
5. Move Discover, Rewind, transformation, and delayed-event state machines.
6. Leave only genuinely unique cards in special handlers.

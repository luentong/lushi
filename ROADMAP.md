# Delivery gates

## Gate 0: immutable inputs (done)

- Four deckstrings, CN Standard, snapshot date 2026-09-08.
- HearthstoneJSON build 251332 and source commits pinned in `SOURCES.lock`.
- Deck decode and RosettaStone card coverage reports reproducible.

## Gate 1: rules vertical slice

Implement the 17 unique Dragon Warrior entities first and run deterministic
Dragon Warrior mirror games. This is the smallest ordinary 30-card slice.

Acceptance:

- legal-action generator produces no illegal actions;
- a fixed seed reproduces the same event trace and winner;
- each card has a focused rules test;
- replay trace records state hash before and after every action.

Then add Aggro Druid, Stealth Rogue, and Dirty Priest in that order. Dirty Priest
is last despite its smaller list because its 20-card construction rule and copying
effects require deeper engine/state support.

## Gate 2: non-learning baselines

- random legal policy;
- deterministic hand-written heuristic policy;
- Beam Search, followed by information-set MCTS if Beam Search is insufficient;
- seeded match matrix and confidence intervals.

## Gate 3: replay data

Use `python-hslog` to convert supplied `Power.log` files into normalized replay
records. Validate public/hidden information boundaries before producing policy or
value labels.

## Gate 4: learned policy/value and optional LLM

Train small policy/value models first. Add the LLM only as an independently
switchable high-level feature and keep exact rules, legality, and search outside
the LLM.

## Inputs still needed

1. Exact Hearthstone client build number, to verify it matches metadata build
   251332.
2. Several complete `Power.log` files for each deck, including at least one win
   and one loss. Logs are not required for Gate 1 but are required for Gate 3.

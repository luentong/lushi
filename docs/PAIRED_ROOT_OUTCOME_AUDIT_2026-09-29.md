# Paired root-outcome audit (2026-09-29)

The current search teacher supplies visit-count policy labels. A visit count is
not an observed win rate, so this audit replays a recorded decision and forces
each legal first action into the **same sampled hidden world and future random
stream** before continuing both players with a fixed policy. A new sample uses
an independent chance stream. The script is
`scripts/audit_paired_root_outcomes.py`. It rejects state drift and ambiguous
selected-action descriptions, records incomplete games separately, and compares
only paired replicates that reached a result for both actions.

Example (local heuristic continuation):

```powershell
python scripts/audit_paired_root_outcomes.py `
  --trace reports/decision-quality-loop-20260928/three-traces/game-02.json `
  --step 4 --deck-config config/decision_quality_pair_decks_20260928.json `
  --replicates 64 --max-actions 240 `
  --output reports/entity-conditional-v1-20260929/paired-root-game02-step04-64.json
```

At game 02, step 4, the old neural search used 16 simulations and selected
`END_TURN` (8 visits; mean value +0.26). It assigned 2 visits each to `ATTACK
Carrier Whelp` and `PLAY Brood Keeper` (search mean values -0.62 and -0.86).
In 64 paired hidden-world continuations with the *heuristic* policy:

| Forced first action | Wins / completed | Paired better / worse vs END_TURN |
| --- | ---: | ---: |
| END_TURN | 23 / 64 | baseline |
| ATTACK Carrier Whelp -> hero | 43 / 64 | 23 / 3 |
| PLAY Brood Keeper | 43 / 64 | 23 / 3 |
| HERO_POWER | 26 / 64 | 3 / 0 |

At game 03, step 5, the same audit was less clear: `END_TURN`, `ATTACK
Carrier Whelp`, and `PLAY Sanguine Depths` each won 31 of 64. `HERO_POWER`
won 35 of 64. This root does not provide strong evidence for a correction.
Other sampled roots favored the teacher's choice. This is evidence that some
labels merit review, **not** an estimate of the optimal policy or a new model
win rate. The heuristic continuation strongly favors spending all available
actions and can erase first-action ordering differences. Hidden-world sampling
also does not fully model a real ladder opponent.

The audit additionally supports `--continuation entity-greedy --checkpoint
<entity checkpoint> --device <device>` and legacy `model-greedy`, to test
whether a suspected error persists with a different continuation policy.
On 910B, the current entity PPO checkpoint was tried on the same game 02 root
with two paired future-random samples. `END_TURN` won 1/2; attacking won 2/2,
while playing Brood Keeper won 1/2. This is a smoke check only: two samples
cannot validate or overturn the 64-sample heuristic result. This neural
continuation took about a minute for only two replicates, so scaling it to
thousands of roots without batching/caching would be impractical.
An exact-observer-view inference cache was added for repeated continuations;
in a one-replicate smoke run it avoided 61 of 363 potential model calls. This
does not fix the underlying per-step inference cost.
The six forced branches can now advance together with padded batched entity
inference. A two-replicate parity run returned the same outcomes as sequential
inference and used 161 batched forward passes, but wall time remained roughly
a minute. The bottleneck is not simply the number of NPU launches; observation
construction, collation, model batch cost, and game simulation still need
profiling before large neural continuation audits.

Profiling one paired replicate on 910B isolated the cost: of 27.2 seconds of
audit time, observer-view construction used 9.7 seconds, CPU collation 15.5
seconds, host-to-NPU transfer 0.07 seconds, and model forward 1.4 seconds.
`collate_views` now fills Python buffers and creates one tensor per field,
instead of thousands of torch scalar assignments. On the same six-view batch,
median CPU collation fell from **183 ms to 39 ms** (4.7×); all 12 tensor
checksums matched the old path. In the same one-replicate NPU audit, total
audit time fell from **27.2 to 11.7 seconds** and collation from 15.5 to 2.6
seconds; outputs were unchanged. A separate seven-observation parity test and
the 34 entity-related tests passed on the remote Python/torch environment.
The model weights and decision policy were not changed by this refactor.

A subsequent profile showed that rebuilding the same static card-text semantic
features and deep-copying a freshly constructed observation were also costly.
Semantic vectors are now cached by their complete feature-bearing fields (not
by card ID), so distinct runtime variants cannot silently share stale
features. Observation construction returns its already-detached JSON tree
without a second recursive copy. Mutation-isolation and semantic-cache
invalidation tests pass. On the same one-replicate 910B paired audit, time
fell again from **11.7 to 7.2 seconds**; observer-view time fell from 7.2 to
2.3 seconds. The actor action and all six forced-action outcomes stayed the
same. This is a performance improvement to the audit, not evidence that the
checkpoint has learned better play.

Neither continuation should automatically overwrite teacher labels. Before
using these examples for corrective training, require agreement across
multiple continuation policies, more independent roots/deck families, and a
held-out paired-match benchmark. The current candidate checkpoint has **not**
been promoted.

## From teacher shards to cross-matchup audits

`scripts/audit_teacher_shard_roots.py` now reads the actual teacher manifest
and compressed per-game shards. It verifies each shard hash and the deck
configuration hash, restores the **frozen vocabulary in that shard's header**,
then replays every recorded ordinary decision. At each step it checks actor,
encoded state, ordered concrete legal actions, and the full acting-observer
view. It also verifies terminal winner and each ordinary row's value target.
The ruleset fingerprint must match the shard header.
Any drift rejects that complete game. Conditional branch rows are counted but
not falsely replayed as committed actions.

The audit samples both `END_TURN` and other selected actions across ordered
matchups, avoiding duplicate games when possible. Its output explicitly says
that a sampled-root discrepancy is not a dataset-wide error rate. This is a
tool for finding teacher-label failures before making new corrective data,
not itself a replacement teacher.

In the 32-game conditional-teacher shard set, all 32 games passed replay; eight
roots sampled from eight distinct games across all four ordered Dragon Warrior
/ Aggro Druid matchups were audited with 16 heuristic continuations each.
Most alternatives tied the teacher choice. The largest sampled advantage was
3 paired wins versus 0 losses (13 ties), too little to relabel automatically.
This result is compatible with a sparse set of conspicuous failures such as
the separate game-02 step-4 `END_TURN` case (23 better / 3 worse for attacking
or playing Brood Keeper in 64 paired heuristic continuations).

## Independent neural continuation of the game-02 root

Two nonoverlapping seed blocks (16 and 32; 48 total) were run on the 910B
with the same entity PPO checkpoint as a greedy continuation policy. The
`scripts/aggregate_paired_root_audits.py` verifier rejects duplicate future
seeds and mismatched roots/checkpoints, then recomputes *paired* counts.
Every forced branch finished; there were no invalid or truncated games.

| Forced root action | Wins / 48 | Better / worse / tied than recorded END_TURN |
| --- | ---: | ---: |
| END_TURN (recorded teacher action) | 15 | — |
| PLAY Brood Keeper | 39 | **27 / 3 / 18** |
| PLAY Sanguine Depths | 29 | 19 / 5 / 24 |
| ATTACK Carrier Whelp → opposing hero | 25 | 15 / 5 / 28 |

For Brood Keeper versus END_TURN, the exploratory two-sided paired sign-test
value is about `8.4e-6`. The independent neural block and earlier heuristic
continuations point in the same direction: the 16-simulation teacher probably
undervalued this line. This is **not** an optimal-action proof or a ladder
win-rate estimate. The model continuation can share systematic weaknesses
with the teacher; five alternative actions were inspected; and the root was
chosen because it already looked suspicious. Its proper use is a prioritized
teacher-review case, not an automatically relabeled training sample.

Local artifacts: `reports/game02-step04-entity16-fastview.json`,
`reports/game02-step04-entity32-independent.json`, and
`reports/game02-step04-entity48-aggregate.json`.

## Broader teacher-shard screen and engine follow-up

A second exact-replay screen used all 32 teacher games and selected 32 distinct
roots, balanced eight per ordered Dragon Warrior / Aggro Druid matchup. It
inspected 130 forced alternatives with 16 paired heuristic continuations per
root. No alternative survived Holm correction over the inspected family.
The largest exploratory advantage was 5 better, 1 worse, 10 tied, so the
screen does not justify bulk relabeling. Results are in
`reports/entity-conditional-v1-20260929/shards-diverse32-seed20260930.json`
and its `-summary.json` companion.

The semantic-feature memoization changed the source-file-based ruleset
fingerprint despite preserving the feature values. The shard audit therefore
continues to reject a mismatch by default. A dedicated
`--allow-fingerprint-drift-if-exact-replay` audit-only switch records both
fingerprints and still requires exact equality of every replayed encoded
state, legal-action list, acting-observer view, actor, and terminal/value
outcome. All 32 games passed under that explicit check. This only verifies
visited states; it does not certify arbitrary unvisited interactions or
authorize training on a drifted shard.

A targeted 64-replicate follow-up at game 8, ply 13 uncovered an unrelated
engine error in a *counterfactual* branch. An Ebonscale Scout with a doubled
Battlecry killed its selected minion on the first trigger; the second trigger
then tried to dereference that removed minion and aborted the simulation.
The second trigger now fizzles, matching the existing targeted double-
Battlecry handling. The original failing seed reproduces without an invalid
action after the fix; the `test_standard_cards.py` tests pass, including a
new regression for this interaction. Previous audit counts that contained
the invalid branch must be treated as pre-fix diagnostics, not final evidence.

After this repair, the same focused 64-sample game-8 root had zero invalid
branches. Its best sampled alternative, Hook n' Heave, was only 16 better / 11
worse / 37 tied versus the teacher's END_TURN. The apparent 4/0 lead for a
different action in the original 16-sample screen was therefore too fragile
to justify a label change.

Reviewing the wider screen also surfaced a second, separate invalid branch in
game 23. Corrupted Dream attempted to shuffle a generated Ancient (`EDR_209t`)
into its owner's deck. That token carried a complete runtime CardDef but was
not registered in global `card_defs`, so reconstruction by card ID raised
`UnsupportedGeneratedCard`. The shuffle now creates a fresh unbuffed card
from the targeted minion's immutable definition. The exact failing seed
reaches a terminal result for all forced root actions after the repair. A
regression test covers the unregistered runtime token. Both local and 910B
`test_standard_cards.py` suites pass **471/471**. Existing teacher shards
still need careful provenance handling: exact replay of their *committed*
games does not prove every counterfactual branch searched by the old teacher
was free of these latent bugs.

The 32-root screen was repeated after both repairs with the same root and
future-random seeds. All 32 recorded games again replayed exactly; the 130
alternative actions yielded **zero invalid** continuations (six reached the
240-action audit cap and were excluded from paired scoring). No alternative
survived Holm correction. The clean artifact is
`reports/entity-conditional-v1-20260929/shards-diverse32-seed20260930-fixed.json`
with a `-summary.json` companion. This does not certify the old teacher
labels: the original data was generated by a ruleset that contained the two
counterfactual branch bugs. Regenerate teacher data from the repaired
ruleset before claiming a new checkpoint improves play.

The teacher chose the most-visited root action even when its recorded sampled
Q was not the largest at **20 of 32** screened roots. This is normal for a
visit-count policy under exploration and unequal sample counts; it is a
diagnostic of possible prior/sample imbalance, not proof that choosing max-Q
would be better. At game 15, ply 21, END_TURN received 34/64 visits although
several alternatives had slightly higher sampled Q. In 64 independent paired
*heuristic* continuations, Press the Advantage on the opposing Rustrot Viper
was 16 better / 4 worse / 44 tied than END_TURN. However, 32 independent
*entity-model* continuations gave 3 better / 4 worse / 25 tied for the same
action. Because the continuation policies disagree, this root is **not**
eligible for corrective relabeling. The focused artifacts are
`reports/entity-conditional-v1-20260929/focus-game15-ply21-r64-fixed.json`
and `focus-game15-ply21-entity32.json`.

The final regression pass on the isolated 910B workspace completed **876/876**
tests. This also caught a test-configuration failure in conditional sample
generation: an absent optional `export_observer_view` setting is now treated
as disabled. The fix was separately covered by the 24 search-information
tests. Neither this test pass nor the paired root audits establishes that the
current checkpoint has professional-level play; the next training experiment
needs freshly generated, provenance-matched teacher data and an independent
direct-play evaluation.

## Repaired-rules teacher pilot (2026-09-30)

The first launch of the high-budget driver mistakenly passed the **entity PPO**
checkpoint to the **older structured-model** teacher loader. All four jobs
failed at checkpoint loading (`KeyError: 'model'`), before any game data was
written. Those files are excluded. The driver now checks checkpoint-loader
compatibility before creating its output directory; the mismatched entity
checkpoint was rejected in preflight, while the intended structured
checkpoint passed. The driver was rerun from a new directory
with the compatible frozen structured checkpoint used by the earlier entity
bootstrap; its manifest now hashes all `src/hsa/*.py` sources, not only MCTS
and the data generator.

For future runs, the driver also records the card-database digest and hashes
the belief-configuration and audit scripts. The completed pilot manifest is
left unchanged as a point-in-time record; this later provenance addition does
not retroactively alter its generated data.

The clean pilot used Dragon Warrior and Aggro Druid in all four ordered
matchups, one game each, `1 × 64` search simulations per decision, rollout
depth 4, on 910B NPU 2/3. **4/4 games reached a winner** in about 415 s;
there were 393 ordinary decisions and 2,617 recorded legal actions. The
structural dataset audit passed with zero errors, and 71.6% of search-eligible
root actions received at least one visit. That coverage is not an action-
quality metric. No conditional branch training rows were collected by this
driver, so these four shards do not address the unresolved replanning-label
problem.

All four committed games replayed exactly against the repaired rules. A small
screen of four roots compared 16 forced alternatives with 16 paired heuristic
continuations each: zero invalid results, zero audit-cap truncations, and
zero alternatives surviving Holm correction. This is a **data-integrity
pilot**, not evidence that the teacher is stronger or that a student should
be trained on it. Artifacts, including the hashed manifest, dataset audit,
root audit, summary, and four game shards, are in
`reports/repaired-teacher-pilot4b-20260930/`. A larger independent paired
search-strength evaluation, with budget and runtime controlled, remains the
gate before scaling teacher generation or promoting a checkpoint.

## Same-budget search comparison and long-game diagnosis

On the repaired rules, `1 × 64` and `2 × 32` used the same frozen structured
policy prior, tree depth 8, heuristic rollout depth 4, and prior-first PUCT
expansion. Dragon Warrior / Aggro Druid was run both ways round, with the
candidate search in both seats for each arrangement (four games total).
Each search configuration won **2/4**. All four games ended normally with
zero invalid actions, effect caps, or action-limit exclusions. Four games
are far too few to establish equal strength; the stronger teacher is still
unproven. The two result files are
`reports/repaired-teacher-pilot4b-20260930/search-strength-*.json`.

The deck-swapped pair took about 603 s in aggregate, versus 188 s for the
other pair. Its games each lasted 16 turns and 90 actions; the faster pair
lasted 11 turns and 53 actions each. To check the possibility of a stuck
engine, one slow game (seed `202609301720`, candidate seat 1) was rerun with
durable per-action timing. It again finished after 90 actions, with the same
winner and no invalid action. All actions advanced. The trace totals 326.9 s
of action time: median 1.82 s, 95th percentile 11.03 s, maximum 11.75 s.
The first 45 actions used 72.2 s; the last 45 used 254.7 s, with up to 61
legal root actions as the board became more complex. Turns 12 and 14 each
consumed about 81–84 s across 10 and 9 distinct actions; no turn repeated
an action indefinitely. This evidence does
**not** indicate an infinite loop or one pathological stalled action. It
does not prove the rules are correct, and it does not yet identify the exact
CPU hotspot inside search/branch simulation.

`benchmark_mcts.py` now has an optional `--progress-dir` that writes a
before/after record for each action and a per-game result sidecar, so a
future long-game timeout does not erase all diagnostic progress. A one-action
smoke verified both files; the full 910B regression suite still passes
**876/876**. The diagnostic rerun and trace are in
`reports/repaired-teacher-pilot4b-20260930/diag-swapped-seat1.json` and
`seed-202609301720-seat-1-swap-1.jsonl`.

## Search volume versus decision quality (2026-09-30)

The slow rerun above completed normally; its later turns simply had more
actions and much wider roots. At the user's request, no speed optimization is
being pursued on this evidence alone. Further work is on decision quality.

A wider paired-outcome probe verified all four teacher games and inspected
22 alternatives at seven selected roots with 32 paired continuations. It
found no invalid/truncated continuation and no alternative surviving Holm
correction. These are small, continuation-policy-dependent audits, **not**
proof of strong teacher play. The summary is in
`reports/repaired-teacher-pilot4b-20260930/diverse20-r32-summary.json`.

The fixed tactical suite initially appeared to score 22/24 at 64 total
simulations (`1 x 64` and `2 x 32` produced the same score), with the two
"misses" both attributed to playing Cannonmaster before Carrier Whelp.
Raising the budget to 128/256 did not consistently produce Whelp-first.
However, this test is **not a sound quality label**: the fixture has exactly
two mana, both cards cost one, and every Dragon in Carrier Whelp's candidate
pool costs at least one. Once both cards are played, none of the revealed
cards can be played this turn. The observed order is therefore a preference,
not a demonstrated regret or tactical failure in this fixture. The audit now
records the order without adding it to pass/fail counts, and a regression
test checks the resource precondition in both orders. The seven independently
checkable tactical cases passed 21/21 across three seeds. This does not
resolve the user's **real-game** information-order concern; that needs an
equal-world counterfactual with an actionable revealed outcome and a payoff
measured after replanning, not a rule hardcoding Whelp-first.

After loading the server's CANN environment, the updated full regression
suite passed **877/877** tests. A one-case audit smoke also confirmed that a
reverse observed order is recorded but `passed` stays null, rather than
becoming a false failure.

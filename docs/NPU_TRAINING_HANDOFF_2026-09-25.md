# NPU Retraining Handoff: Standard Live Advisor

## Goal

Train a replacement for the legacy live checkpoint
`models/standard91-generalized-columnar-v1.best.pt`. The replacement must be
useful in real Standard games, rather than merely score well on a small,
randomly split self-play dataset.

The live program is advisory only. It can read a local `Power.log` and write
a local suggestion. It must never upload logs or control Hearthstone. Do not
commit raw logs, player names, account identifiers, or local current-match deck
files. Reviewed sanitized public-state fixtures are acceptable.

## Current Repository State

The current working tree includes the following live-advisor work.

| Area | Files | What it now does |
| --- | --- | --- |
| Incremental intake | `src/hsa/incremental_powerlog.py`, `src/hsa/powerlog_watcher.py` | Avoids reparsing the entire growing log on each update. |
| Entity registry / projection | `src/hsa/live_state.py`, `src/hsa/live_adapter.py`, `src/hsa/live_replay.py` | Keeps entity lineage, but puts only public decision state into the simulator. |
| Reset, setaside, choices | `src/hsa/live_state.py`, `src/hsa/live_replay.py` | Rebuilds `GAME_RESET` snapshots, handles safe opaque `SETASIDE` artifacts in advisory mode, and exposes pending Discover choices early. |
| Legal-state reconstruction | `src/hsa/live_bridge.py` | Reconstructs mana, weapon/hero attack, attacks used, summoning sickness, Hero Power use, and public static minions. |
| Candidate belief | `scripts/live_recommender.py`, `src/hsa/live_compare.py` | Counts real deck-card `PLAY` events as evidence; generated effects and `POWER` records no longer double-count cards. |
| Recommendation guard | `src/hsa/recommendation_gate.py`, `src/hsa/live_recommendation.py` | Refuses advice if the state/action phase/candidate belief is not trustworthy. |

This fixed live-framework errors observed during testing: reversed controllers,
advice during the opponent turn, duplicate Hero Power suggestions, attacks by a
just-summoned minion, delayed Discover options, and stale post-event advice.
It does **not** turn the old policy into a strong strategic model.

## What Was Learned

### Model and data limitations

1. **The current checkpoint is legacy.**
   It needs `--allow-legacy-checkpoint` to load. It is a compatibility and
   integration artifact, not an approved model line to scale up blindly.

2. **Fast live mode currently uses `--search-iterations 0`.**
   This was necessary to reduce event-to-advice latency. The answer is therefore
   almost a single policy ranking and has limited look-ahead for face-versus-
   trade attacks, ordering, resource conservation, and Discover value.

3. **The corpus is too small and narrow.**
   README already documents value overfitting for small independent-game sets.
   More epochs on the same data will not produce general play strength.

4. **The highest-value decision types need deliberate coverage.**
   Discover/Choose, targets, attack target choice, play/attack/Hero Power
   ordering, weapons, locations, generated cards, temporary attack, and board
   clears must be common in teacher data.

5. **Opponent candidate coverage is not fixed by neural training.**
   A real Warrior-versus-Death-Knight match had valid public opponent cards but
   zero compatible configured candidate decks. The tool correctly stopped
   instead of inventing hidden information. The Standard candidate library must
   cover supported archetypes and preserve an explicit uncertainty fallback.

### Framework and rules limitations

Do not classify these as neural-model failures:

- A public card whose rule is missing from `src/hsa/dragon_mirror.py` makes
  the simulated future strategically wrong even if the suggested action is
  legal.
- `Power.log` cannot reveal opponent hand/deck identities or every internal
  object. Use public belief/determinization, never hidden truth.
- Some enchantments show changed stats but not enough semantics to recreate all
  future effects. Add rules or mark the snapshot uncertain before treating it
  as a teacher/evaluation state.
- Do not weaken a candidate-deck or snapshot gate merely to increase advice
  frequency.

## Recommended Model And Data Plan

Use `structured-v5` / `StructuredResidualPolicyValueNet` as the default.
It has separate state and action representations and is already supported by
the multi-deck generator. Preserve feature-schema and vocabulary metadata in
every checkpoint. A schema or vocabulary change requires a new model line, not
an unchecked resume.

Build a dated Standard deck manifest with:

- every executable, supported Standard archetype across all classes;
- multiple archetype variants where the game plan changes;
- both ordered seats for every matchup;
- frequency weights for common ladder decks, with a nonzero floor for rare
  archetypes and decision-rich classes;
- labels for Discover, random generation, weapons, locations, targets,
  board clears, and temporary combat;
- an explicit list of incomplete cards/rules excluded from the corpus.

For a serious run, generate **tens of thousands of independent complete games**.
Increasing the ISMCTS teacher from 32 to roughly 64--128 iterations and varying
seeds is more valuable than doubling epochs over a shallow corpus. Keep a
priority shard of difficult Dragon Warrior and relevant-opponent positions, but
mix it in every epoch rather than doing a narrow final fine-tune that erases
generalization.

Teacher targets should be fair-information ISMCTS root visit distributions.
Keep soft policy targets instead of only a selected action, retain final
outcome/value targets, and report value calibration separately. Oversample
non-forced decisions. Use sanitized live games mainly as bridge and legality
regressions; do not blindly imitate human log actions as a teacher.

## NPU Execution Order

The existing NPU-oriented runner is
`scripts/run_standard_multideck_training_910b.sh`. It is an integration
baseline, not the final data scale.

The NPU notebook may not have outbound GitHub access.  If `git clone` stalls,
do not change model code on the notebook to work around networking.  On an
approved connected machine, archive the exact reviewed commit with
`git archive`, transfer that archive through the approved SSH path, extract it
into a new dated `/workspace/hearthstone-agent-live-advisory-*` directory, and
record the commit SHA beside the run outputs.  Keep the notebook deployment
separate from any existing colleague checkout.

`config/decks_20260925_standard127.json` combines the reviewed 91-variant
library with 30 non-duplicate variants from the prior 40-deck survey,
then six new user-supplied current-ladder variants, including the previously
missing Hunter and Paladin coverage.  A 33,000-game
first corpus can cover every ordered pair at least twice
(127 x 127 x 2 = 32,258) and leave the remaining games for frequency
weighting.  Do **not** claim a minimum of eight games per pair at this scale:
that would require at least 129,032 games before weighted sampling.  Use the
same manifest for the live candidate library and for training.

```bash
cd /workspace/hearthstone-agent
source /usr/local/Ascend/cann-9.0.0/set_env.sh
export PYTHONPATH="$PWD/src:${PYTHONPATH:-}"
PY=/usr/local/python3.11.14/bin/python3

RUN_TAG=20260925_r1
RUN_DIR="reports/standard_live_${RUN_TAG}"
DECK_CONFIG=config/decks_20260925_standard127.json
mkdir -p "$RUN_DIR"

$PY scripts/preflight_multideck.py \
  --cards cards.251332.enUS.json \
  --deck-config "$DECK_CONFIG" \
  --iterations 8 \
  --output "$RUN_DIR/preflight.json" \
  > "$RUN_DIR/preflight.log" 2>&1

$PY scripts/generate_multideck_policy_value_data.py \
  --config "$DECK_CONFIG" \
  --cards cards.251332.enUS.json \
  --output-dir "$RUN_DIR/data" \
  --manifest "$RUN_DIR/manifest.json" \
  --total-games 33000 \
  --min-games-per-pair 2 \
  --seed 202609250000 \
  --teacher-samples 4 \
  --teacher-iterations 96 \
  --rollout-depth 4 \
  --workers 8 \
  --parallel-jobs 4 \
  --job-timeout-seconds 1800 \
  --ruleset-label standard-live-20260925-r1 \
  --card-vocab expanded-executable \
  --continue-on-error \
  > "$RUN_DIR/generation.log" 2>&1
```

Inspect `manifest.json` before training. Every planned matchup must either
complete or be explicitly failed for a concrete rule-engine reason. Repair
rules and regenerate the affected pairs; do not silently train around broad
failures.

Train the generated JSONL corpus with the existing structured-v5 trainer:

```bash
$PY scripts/train_policy_value.py \
  --device npu \
  --data "$RUN_DIR"/data/*.jsonl.gz \
  --output "$RUN_DIR/policy-value-standard-live-r1.pt" \
  --architecture structured-v5 \
  --hidden-size 1024 \
  --action-hidden-size 512 \
  --residual-blocks 8 \
  --card-embedding-size 256 \
  --epochs 20 \
  --batch-size 512 \
  --learning-rate 2e-4 \
  --weight-decay 1e-2 \
  --value-weight 0.15 \
  --policy-weight 1.0 \
  --validation-ratio 0.2 \
  --early-stopping-patience 4 \
  --early-stopping-metric joint \
  --policy-target visits \
  --seed 2026092501 \
  > "$RUN_DIR/training.log" 2>&1
```

For packed columnar `.pt` shards, use
`scripts/train_columnar_policy_value.py` and
`scripts/evaluate_columnar_policy_value.py` instead. The columnar trainer can
mix a high-quality priority shard with `--priority-data` and
`--priority-repeat`. Do not mix artifact formats accidentally: retain the
matching schema report and generator manifest.

## Promotion Gates

Promotion requires all of the following, retained under the same run directory.

1. **Schema:** checkpoint metadata matches the corpus schema and frozen
   vocabulary. A promoted checkpoint must load without a legacy override.
2. **Leak-free validation:** split by complete game and additionally hold out
   whole archetypes/matchup pairs. A random decision split leaks near-identical
   states.
3. **Imitation and calibration:** record policy top-1, soft-target
   cross-entropy/KL, value MAE/Brier, value-sign accuracy, and comparison with a
   constant value baseline.
4. **Legality:** zero invalid actions in large seat-swapped tests, including
   Discover, target selection, weapons, locations, attacks, Hero Power,
   generated cards, and summoning-sickness cases.
5. **Strength:** compare policy-only PUCT and policy-plus-value PUCT to the
   current ISMCTS/heuristic baselines on held-out pairs. If value harms search,
   keep it disabled.
6. **Live replay fixtures:** assert no action during opponent turns, no repeated
   Hero Power, no out-of-mana play, no exhausted attack, and a result for every
   stable supported Discover decision.
7. **Latency:** benchmark the target RTX 4070 Ti Super separately. Measure from
   stable log event to advice for explicit policy-only and short-search modes.
   Do not hide a multi-second search behind a live recommendation.

Suggested acceptance targets are zero illegal recommendations in the fixture
suite, broad Standard candidate-library coverage, and sub-second policy-only
refresh on the Windows target. Strength claims require a predefined held-out
tournament and confidence intervals, not one successful ladder game.

## Deployment

1. Copy only the approved checkpoint and its JSON report to Windows.
2. Verify it with `scripts/verify_cuda_policy.py --checkpoint ... --device cuda`
   without `--allow-legacy-checkpoint`.
3. Start policy-only live mode first. Compare a small root-search budget offline
   before enabling it in a match.
4. Preserve strict recommendation gates for incompatible candidate decks,
   unsupported rules, unresolved choices, and incomplete action phases.
5. Version every checkpoint by Git SHA, ruleset label/fingerprint, vocabulary
   hash, generator manifest, and evaluation reports.

## NPU Agent Checklist

1. Audit the multi-deck manifest and live candidate-deck library for missing
   Standard archetypes, especially all classes appearing in real matches.
2. Run the preflight. Repair or explicitly exclude failed rules and record why.
3. Generate a 64--128-game smoke corpus at the proposed teacher budget. Check
   NPU memory/time, shard headers, soft-target entropy, and matchup completion.
4. Launch the resumable full corpus. Preserve the manifest and failed-job list.
5. Train structured-v5 and evaluate seed-held-out plus archetype-held-out data.
6. Run seat-swapped tournaments and sanitized live bridge/legality fixtures.
7. Report exact commands, Git SHA, vocabulary hash, ruleset fingerprint, data
   counts, failed matchups, metrics, tournament results, latency, and an
   explicit promote/do-not-promote decision.

> Work from this revision of `luentong/lushi` and follow this document.
> Train a replacement for the legacy live checkpoint using fair-information,
> multi-deck ISMCTS soft targets. Never upload raw Power.log and never weaken
> safety gates just to make the tool emit more advice.

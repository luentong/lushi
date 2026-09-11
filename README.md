# Hearthstone agent baseline

This directory freezes the four CN Standard deckstrings supplied on 2026-09-08
and audits them before simulator/search development starts.

## Component boundaries

- `python-hearthstone`: deckstring decoding, enums, and card-data loading.
- `python-hslog`: importing `Power.log` into replay/training records.
- `RosettaStone`: deterministic rules engine and legal-action authority.
- This project: state schema, action schema, policies, search, replay datasets,
  evaluation, and later optional LLM guidance.

The game client is not automated. The intended target is an offline simulator and
an analysis/advice system.

## Reproduce the audit

The metadata is pinned to HearthstoneJSON build `251332` rather than silently
following `latest`.

```bash
python -m pip install hearthstone==9.20.12
python scripts/audit_decks.py
```

Outputs are written to `reports/deck_audit.json`, `reports/deck_summary.csv`, and
`reports/card_coverage.csv`.

The deck audit keeps three coverage notions separate: reference implementations
found in RosettaStone, entities known by this runtime, and cards validated for
normal constructed-deck play. Only the last column determines `deck_ready`;
context-limited random-summon support cannot accidentally mark another deck as
playable. Dragon Warrior is currently 17/17 unique cards and 30/30 copies in
that validated column.

## Current gate

RosettaStone commit `e10749b5f0c08d3a6135bce317cb11d1738846ad` contains metadata
for only four of the 71 unique encoded entities used by these decks. Those four
Core cards are implemented; the 2025-2026 sets used by the decks are absent.
Therefore RosettaStone can be reused as an engine framework, but it cannot yet
run trustworthy games with these decklists. Building MCTS, policy/value models,
or an LLM decision layer before closing this card/mechanic gap would produce an
invalid benchmark.

The Dragon Warrior mirror vertical slice is now implemented and suitable for
search and learning experiments under ruleset `dragon-warrior-closed-v5`.
This result does not yet generalize to the other supplied decks or to full
Standard. Cross-match expansion remains gated on implementing and validating
their cards and reachable generated-card closure. Every added card needs a
focused rules test and at least one deterministic replay fixture.

## Dragon Warrior vertical slice

`src/hsa/dragon_mirror.py` implements the 17 directly encoded Dragon Warrior
entities plus the Coin and generated tokens needed by their direct effects. It
includes legal-action enumeration, combat, mana, fatigue, Armor Up, locations,
Tradeable, conditional costs, Fire-spell tracking, Dark Gifts, Rewind decision
points, Start-of-Game duplication, and deterministic random events.
Discover offers and Rewind keep/retry prompts are explicit player actions: the
engine pauses at each decision and exposes no unrelated legal action until it is
resolved. Dark Gift offers also filter incompatible keywords and keep the three
offered Gifts distinct when the closed pool has three candidates.

Run its focused rules tests and seeded mirror smoke test:

```bash
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/run_dragon_mirror.py --games 100 --seed 202609080001
```

Generate a complete, single-game action trace in both JSON and Markdown:

```bash
.venv/bin/python scripts/trace_dragon_mirror.py --seed 202609080001
```

The readable report is `reports/dragon_mirror_trace.md`. The JSON report records
the selected action, number of legal alternatives, new events, and complete
before/after state for both players at every step.

To replay one policy-prior PUCT versus plain ISMCTS benchmark game with the
same search seeds and parameters, run:

```bash
python scripts/trace_search_match.py \
  --seed 202610050003 --candidate-seat 0 \
  --checkpoint reports/policy-value-rules-v3-structured-v5-2048.pt \
  --device npu:0 \
  --samples 4 --iterations 4 --tree-depth 8 --rollout-depth 3 \
  --min-simulations-per-root-action 1 --max-total-iterations 32
```

The strongest ruleset-v3 strategy was the structured residual v5 checkpoint
used as a **policy prior only**. In 104 seat-swapped games it defeated ordinary ISMCTS
75-29 (72.12%, Wilson 95% CI 62.83%-79.83%). Enabling the same checkpoint's
value head won only 32/104 against policy-only PUCT, so model leaf values are
disabled. Because the simulator is now ruleset v4, these measurements are a
historical baseline and no v4 neural checkpoint is promoted yet. See
`reports/current-best-policy.md` for the exact artifact hash, experiment design,
and reproducible report paths.

Its Markdown trace shows every chosen action, the five leading alternatives by
root visits, each branch's mean value and neural prior, the final selection,
resolved engine events, and both players' state after the action. The compact
JSON trace retains all ranked alternatives for analysis.
Use the bundled HearthstoneJSON Chinese card data to render a complete Chinese
version without rerunning the match:

```bash
python scripts/localize_search_trace_zhcn.py \
  reports/search-trace-202609100039-seat0.json
```

Opening hands now use an explicit mulligan phase. Each player may independently
toggle any offered card between keep/replace and confirm the whole selection;
replacement cards are drawn before rejected cards return to the shuffled deck,
so an immediately rejected entity cannot be redrawn. The second player's Coin,
Start-of-Game effects, and turn-one draw occur only after both confirmations.
Normal batch games apply the deterministic curve baseline (replace cards costing
4 or more), while the trace command exposes every toggle and confirmation as a
separate step.

Run the first policy baseline as a seat-swapped paired experiment:

```bash
.venv/bin/python scripts/benchmark_policies.py --pairs 100
```

Each seed is played twice with the heuristic and random policies exchanging
seats. The report includes first/second-player results and a Wilson 95% confidence
interval, and is pinned to the current ruleset so it is not confused with
future full-generation-pool results. `HeuristicPolicy` reads the acting player's
hand and public board state only; it does not inspect hidden opposing cards or
deck order.

Ruleset v3 corrects Carrier Whelp's random low-cost Dragon generation and Hooked
on a Feeling's Pirate Discover plus two Cannoneer summons.  Checkpoints and
datasets tagged v2 remain historical artifacts and must not be promoted as a v3
strategy result.

Ruleset v4 separates targetable enemies from random-enemy pools (random effects
can hit Stealth), records Cannoneer shots independently from minion attacks, and
applies Captain Crowley's additional shot to every Cannoneer firing source.
Ruleset-v3/v4 checkpoints remain historical until retrained or explicitly
revalidated under v5.

Ruleset v5 adds the current declarative-rule tranche and attaches an immutable
source fingerprint to every newly generated dataset and checkpoint. Generate
`reports/ruleset-manifest.json` before a run; do not mix JSONL.GZ inputs whose
`ruleset_fingerprint` differs, even if their friendly ruleset labels match.

## Real Power.log shadow mode

The project can inspect a real game **without sending clicks, keystrokes, or
commands to the client**. First sanitize the raw log so account identifiers and
player names never enter a shared report, then create an advisory-only report:

```bash
python scripts/import_power_log.py /path/to/Power.log \
  --output reports/live.sanitized.json
python scripts/shadow_power_log.py reports/live.sanitized.json \
  --output reports/live.shadow.json \
  --backlog reports/live.shadow.backlog.jsonl
```

`live.shadow.json` has one confidence gate per game. A red task means a played
card, trigger source, or observed generated entity cannot be faithfully replayed
by the current rules; it is automatically written to the JSONL engineering
backlog with the card ID, printed metadata, first packet, and occurrence count.
Amber means the revealed effects are covered but arbitrary Standard state replay
is still not implemented. No action recommendation is emitted until the matchup
deck and reachable generated-card closure are both complete; this is deliberate
fail-closed behavior, not a weak recommendation. The current Dragon Warrior
policy/value model is valid only for its closed mirror simulator.

## Windows local companion (RTX GPU)

For a Hearthstone PC that cannot reach FusionOne, run the companion entirely on
that PC. It reads the local `Power.log`, writes only local sanitized reports,
and never automates the client. An RTX 4070 Ti Super is more than sufficient
for the current 22 MB Dragon Warrior policy checkpoint; the search itself is
still limited by Python game simulation, so begin with the validated 16
simulation budget.

Clone this repository, install a CUDA-enabled PyTorch build appropriate for
your installed NVIDIA driver, then install the remaining pinned dependencies:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
# Install the CUDA-enabled command selected for this PC by pytorch.org/get-started.
# Do not install a CPU-only wheel.
python -m pip install -r requirements-live.txt
```

Manually copy `policy-value-v5-structured-256.pt` into `models\`; model files
are deliberately ignored by Git. Verify both CUDA and exact source/checkpoint
identity before using it:

```powershell
python scripts\verify_cuda_policy.py `
  --checkpoint models\policy-value-v5-structured-256.pt --device cuda
```

Start local-only shadow mode against the default client log path:

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\start_local_shadow.ps1 `
  -Python .\.venv\Scripts\python.exe
```

The report is written to `%LOCALAPPDATA%\LushiAgent\shadow\live.shadow.json`
and the automatically deduplicated rule backlog to
`live.shadow.backlog.jsonl`. The raw log never leaves the gaming PC. Current
mode is coverage/engineering shadow analysis, not real-time move automation;
the latter remains gated by complete live-state reconstruction and matchup
coverage.

Dataset generation streams each completed game into a compressed temporary
spool and keeps at most `2 * workers` parallel game results in memory. The final
JSONL.GZ header and aggregate statistics remain compatible with existing
training commands, while large runs no longer retain every encoded decision in
RAM during generation.

Search code can use `game.clone()` or `game.branch(action)`. Mutable game state
and the RNG stream are copied independently, while immutable card definitions
and the read-only rule registry are shared. Historical event logs are omitted by
default to keep deep search nodes small; pass `include_history=True` for debugging
or exact trace reproduction.

`MCTSPolicy` is the first small-budget tree-search baseline. It uses UCT,
heuristic action ordering and depth-limited heuristic rollouts. It is explicitly
labeled `mcts-full-state-v0` / `debug_full_state`: the tree mechanics are valid,
but the opponent hand is still present in simulator branches. Do not report it
as a fair Hearthstone agent until observation masking plus determinization or
ISMCTS replaces this debug information model.

`game.observation(player)` masks the opposing hand. The legacy debugging helper
`game.determinize_hidden(player, seed=...)` still shuffles the simulator's true
combined hidden-zone multiset and must not be used for fair evaluation.

`PublicBelief.from_game(game, observer)` is the non-oracle belief input.
It consumes the pinned deck list plus whitelisted public events, removes publicly
played starting cards, records public Start-of-Game additions, and represents
generated cards by their public source pool. It deliberately ignores identities
embedded in internal opening-deal, draw, mulligan and Discover events.
`PublicBelief.sample_determinization(...)` rebuilds the opponent hand and deck
from those public candidates without reading the true hidden cards.
`DeterminizedMCTSPolicy` now votes over these samples and is labeled
`root-determinized-mcts-v3` / `public_dragon_mirror_v3`. Public hand buffs are
reconstructed from their source, filter, magnitude, and affected count without
reading private entity IDs. Because exact historical hand membership is hidden,
the affected current candidates are sampled rather than asserted. Unknown
generators use an explicitly counted closed-pool fallback; shared-tree ISMCTS
is available as `InformationSetMCTSPolicy`. It maps entity-based engine actions
to stable semantic keys (zone, card, duplicate ordinal, and target), resamples a
public determinization per iteration, and updates one availability-aware tree.
The older `DeterminizedMCTSPolicy` remains as an independent-tree voting
baseline. `shared-tree-ismcts-v1` is still an engineering baseline rather than
a trained policy/value agent.

Use `python scripts/benchmark_mcts.py --mode ismcts` for a seat-swapped run.
The pinned smoke report completed six games with zero invalid actions and four
wins against `heuristic-tempo-v1`; six games are a correctness signal, not a
statistically meaningful strength claim.

Policy/value inputs are frozen in `hsa.encoding` as framework-neutral tuples.
Schema v2 has a 281-card vocabulary, 1,217 state features, and 612 action
features. It extends the legacy 867-feature schema with public dynamic combat
state: temporary hero Attack, attacks used, hero status, current hand costs,
ordered board stats and keywords, and location durability/cooldown. Opponent
hidden identities remain excluded by construction. Checkpoints record their
schema and the inference adapter continues to encode old v1 checkpoints with
the legacy representation. The
`PolicyValueModel` protocol and `HeuristicPolicyValueModel` provide the model
boundary before adding a trainable implementation. Generate compressed training
records with `python scripts/generate_policy_value_data.py`; every decision
stores the state, all legal action vectors, selected action index, and final
win/loss value target. This plain numeric contract can be loaded by
PyTorch/torch-npu on Ascend 910C without coupling the rules engine to a training
framework.

`hsa.torch_model.PolicyValueNet` is the first trainable network. Its state and
action towers use only Linear, LayerNorm, GELU, masked logits, and Tanh. Train it
with `scripts/train_policy_value.py`. A real Ascend 910C smoke run using
torch 2.10.0 plus torch-npu 2.10.0.post2 completed forward, backward, and AdamW
updates on `npu:0`: 64 records for 5 epochs reduced training loss from 1.7923 to
0.9154 in 1.66 seconds. The resulting 79.7% policy accuracy is an intentional
tiny-set overfit check, not held-out playing strength. The command was:

```
source /usr/local/Ascend/cann-9.0.1/set_env.sh
/workspace/let/minimax-h3-venv/bin/python scripts/train_policy_value.py \
  --device npu --epochs 5 --batch-size 16 --max-records 64 \
  --output reports/policy-value-npu-smoke.pt
```

`TorchPolicyValueModel.from_checkpoint(...)` loads that checkpoint behind the
same framework-neutral inference contract. Passing it to
`InformationSetMCTSPolicy` switches expansion/selection to policy-prior PUCT and
uses the network value at leaves instead of heuristic rollout. The benchmark
shortcut is `python scripts/benchmark_mcts.py --mode puct --checkpoint MODEL \
--device npu:0`. The first 910C end-to-end smoke completed two games and 51
searches with zero invalid actions. Its 0/2 score is expected to be meaningless
because the checkpoint only overfits 64 decisions from one game.

ISMCTS teachers now export their normalized root-visit distribution as a soft
policy target (dataset schema v2), rather than only the selected move. Training
splits are grouped by complete `game_seed`, so decisions from one game cannot
appear in both training and validation. The first four-game diagnostic contains
411 decisions (three train games, one validation game). On 910C, 20 epochs took
24.16 seconds: policy top-1 was 36.2% train / 37.0% validation, while value MAE
was 0.011 train / 0.810 validation. This exposes severe value overfitting and is
the reason to scale independent games before tuning architecture or epochs.

The next independent-teacher tranche contains 32 games and 3,361 decisions.
Generation took 108.5 seconds with four ISMCTS simulations per decision. A
26-game/6-game grouped split trained for 25 epochs on 910C in 115.5 seconds:
policy top-1 was 48.1% train / 38.0% validation and value MAE was 0.005 train /
0.484 validation. More independent games materially improve value
generalization, but the remaining train/validation gap is still large. A
four-game, seat-swapped, four-simulation PUCT smoke then scored 1/4 against the
heuristic baseline with zero invalid actions. Therefore this checkpoint remains
an integration artifact, not a promoted playing policy. The next data tranche
should use a stronger search budget and a less noisy value target before model
capacity or epoch count is increased.

Void Soul is represented as a first-class generated token in the public belief
sampler. Its publicly announced upgrade cost is carried into every sampled
determinization; otherwise a hidden upgraded Soul could be reconstructed as an
invalid zero-tier spell during long ISMCTS data runs.

A teacher-budget ablation showed that four simulations per decision are too
sparse. Raising the budget to 16 increased the mean number of root actions with
visits from 3.43 to 9.72. The resulting 32-game dataset has 3,318 decisions;
after excluding forced one-action states, its mean policy entropy is 1.905 and
no target is one-hot. Four independent worker processes generated it in 119.7
seconds. Search RNG streams are deterministic but distinct per game.

Training and evaluation exclude forced actions from policy loss and policy
metrics while retaining those states for value learning. Reports include soft
policy cross-entropy, target entropy, KL divergence, value MSE/Brier, and
winner-stratified whole-game splits. The 32-game value target still does not
generalize: even a three-epoch checkpoint has validation Brier above the 0.25
constant-probability baseline. Neural leaf values therefore remain disabled for
promotion. `benchmark_mcts.py --mode puct --policy-only` uses learned policy
priors with the existing heuristic rollout value instead.

On the same 20 seat-swapped games and four simulations per decision, plain
ISMCTS scored 12/20 against `heuristic-tempo-v1`; policy-prior PUCT scored
18/20 with zero invalid actions. The paired outcomes were 11 both-win, 7
prior-only wins, 1 plain-only win, and 1 both-loss. This is promising but still
small (exact paired p=0.0703), so it is an engineering candidate rather than a
strength claim. Long strong-teacher generation also exposed and fixed heuristic
scoring for CATA_200/CATA_490: both target cards in hand rather than board
minions.

The follow-up uses 50 entirely new seed pairs. Against the heuristic baseline,
both policy-prior PUCT and plain ISMCTS scored 80/100 (Wilson 95% interval
71.1%-86.7%); their paired discordant outcomes were exactly 13 versus 13. This
shows that the earlier 18/20 difference was sampling noise and that low-budget
ISMCTS itself, not the learned prior, explains the gain over the heuristic.
However, a direct 20-pair match between the two search agents produced 30/40
for policy-prior PUCT: ten seed pairs were swept and ten split, with no pair
lost. This is evidence that the prior changes relative search strength even
though the heuristic benchmark is saturated, but it still needs a larger direct
match and an independent checkpoint before promotion.

An independent replication then generated 64 new strong-teacher games (6,511
decisions) from a disjoint seed range. Its winner balance was 35:29, mean
non-forced policy entropy was 1.937, and each target visited 9.96 actions on
average. A second checkpoint trained with `value_weight=0` reached validation
policy KL 0.226. On a third disjoint seed range it beat plain ISMCTS 60/100 in
direct play (Wilson 95% interval 50.2%-69.1%) with zero invalid actions. Across
the 50 seat-swapped pairs it swept 18, split 24, and lost 8; the two-sided paired
sign test is p=0.0755. The effect therefore replicated directionally but is
smaller than the first 30/40 result and is not yet statistically decisive.
Policy-prior search remains experimental pending more independent training
runs or a pooled hierarchical analysis.

A third checkpoint was trained from another 64-game teacher set (6,849
decisions) and evaluated on another disjoint 50-pair range. It also won 60/100
against plain ISMCTS, sweeping 18 pairs, splitting 24, and losing 8 (paired
p=0.0755). The two 100-game replications used different training data,
evaluation seeds, and checkpoint hashes. Across all three direct matches the
policy-prior agents won 150/240 games (62.5%, descriptive Wilson 95% interval
56.2%-68.4%); the pooled pair counts were 46 swept, 58 split, and 16 lost
(descriptive paired p=0.00018). Pooling games is not a substitute for more
independent checkpoints, but the repeated 60% result makes the direction more
credible and revises the likely effect down from the initial 75% estimate.
`aggregate_policy_prior_runs.py` reproduces these statistics and validates
that every seed has both seat assignments.

Policy-only checkpoints now record `value_trained=false`. The benchmark rejects
using their untrained value head unless `--policy-only` is supplied, preventing
an accidentally random leaf-value comparison.

An inference-budget pilot used the same ten seat-swapped seeds and equal
simulation budgets for policy-prior PUCT and plain ISMCTS. At 4/8/16/32
simulations the v1 policy prior won 14/13/12/16 of 20 games, with wall times of
49.7/81.0/115.2/179.4 seconds. The non-monotonic small-sample result does not
establish an optimum, but confirms that the four-simulation setting was an
evaluation budget rather than an engine limit. Thirty-two simulations is the
next production candidate; it still requires a larger paired run.

A 64-simulation teacher explored more root actions than the 16-simulation
teacher (11.86 versus 9.66) while producing a lower-entropy, more decisive
target (mean maximum probability 0.516 versus 0.339). However, a 64-game v1
student overfit the sharper targets (validation KL 0.523) and scored only 12/20
at both 4 and 32 inference simulations. More teacher compute alone therefore
does not solve missing observation features.

A strict schema-v3/schema-v4 paired experiment reused the same 11,490 teacher
decisions, action ordering, visit targets, game split, optimizer seed, and
architecture. Schema v4 only retained the six target-zone dimensions that were
removed for the paired v3 input. The v4 validation top-1 was 40.95% versus
40.74% for v3, while its KL was slightly worse (0.4641 versus 0.4615). Target
zone is still a correctness fix because it prevents hand/board aliasing, but
this dataset does not demonstrate a strength improvement attributable to it.

The low-budget PUCT expansion rule was also isolated. Standard prior-first
expansion was tested against the existing force-unvisited rule with the same
checkpoint, four simulations, four 910C workers, and 52 seat-swapped seed
pairs. Prior-first expansion won only 23/104 games (22.1%, Wilson 95% interval
15.2%-31.0%); it swept one pair, split 21, and lost 30 (paired sign-test
p=2.98e-8). The learned prior is therefore not calibrated strongly enough to
control first visits. Force-unvisited remains the safe default, while
`benchmark_mcts.py --prior-first-expansion` retains the alternative for future
calibration experiments. This result rules out a tempting code-only shortcut:
raising teacher/search quality still requires better policy targets or a
stronger model, not simply trusting the current prior earlier.

Adaptive root budgeting is now available through
`--min-simulations-per-root-action` and `--max-total-iterations`. With a base
budget of four, a floor of two simulations per legal root action, and a cap of
16, it beat fixed-four PUCT 29/40 (72.5%); nine seat-swapped pairs were swept
and none lost (paired p=0.0039). It averaged about 10.4 simulations per
non-forced search. Against a fixed-ten baseline it scored 22/40 (55%, paired
p=0.6875), so the pilot supports comparable strength at comparable nominal
compute, not a free algorithmic gain. Dataset generation records the actual
teacher and adaptive simulation counts per decision so future distillation
experiments can audit compute rather than relying on the base-budget label.

An independent 128-game adaptive-teacher tranche contains 14,331 decisions and
took 214.5 seconds with eight CPU workers. Its non-forced decisions averaged
13.30 simulations; 94.4% triggered adaptive compute. The target remained quite
diffuse (mean entropy 2.009 and mean maximum probability 0.295). A v4 student
reached validation KL 0.177 and top-1 34.34%, but won only 10/40 against the v4
fixed-64-teacher student at equal four-simulation inference (25%, paired
p=0.00635). It is not a promotion candidate: cheaper adaptive search is useful
online, but its visit distribution is not yet a strong distillation teacher.

Training can now apply `--policy-target-temperature`. Temperature 0.5 reduced
adaptive-target validation entropy from 2.053 to 1.703 and increased top-1 from
34.34% to 37.40%. In a direct same-data match it scored exactly 20/40 against
temperature 1.0 (paired p=1.0), so sharpening alone did not improve playing
strength. More aggressive hard labels had already failed in the fixed-teacher
ablation; the next teacher experiment should improve target information (for
example value-aware action targets), rather than merely rescale visit counts.

Dataset generation now also records each legal root action's visit count and
search mean value. `train_policy_value.py --policy-target
value-weighted-visits --policy-value-temperature T` can distil a normalized
`visit_share * exp((Q - max(Q)) / T)` target. On an exactly regenerated copy of
the 128-game adaptive tranche, visited root actions had a mean Q range of
0.523. At T=0.5, the student scored 21/40 against the ordinary visit-target
student, providing no evidence of improvement. T=0.2 scored 26/40 in a pilot
and then 64/104 on independent seeds (61.5%, Wilson 95% interval 51.9%-70.3%);
it swept 16 seat-swapped pairs and lost four (paired sign-test p=0.0118).
This confirms that teacher Q values recover useful information discarded by
visit counts. The model still scored only 14/40 against the stronger fixed-64
teacher student, however, so this is a useful experimental target rather than
a new default checkpoint. The next training iteration should apply the same
target to fixed-64 teacher data instead of spending more compute tuning the
weaker adaptive-teacher student.

That fixed-64 control has now been completed. Replaying the original 128 seeds
with the current exporter reproduced all 11,490 decisions, the 81:47 winner
split, every validation metric, and all 18 tensors of the ordinary visit-target
checkpoint exactly. The additional Q audit measured a 0.519 mean visited-action
value range. Value weighting at T=0.2 reduced validation target entropy from
1.515 to 1.288, while T=0.5 reduced it to 1.399. Both students scored exactly
20/40 against the reproduced ordinary student at equal four-simulation
inference (three swept and three lost seat-swapped pairs, paired p=1.0).
Therefore value-aware targets help the noisier adaptive teacher but add no
measurable strength to the fixed-64 teacher. The fixed-64 ordinary visit-target
checkpoint remains the default; further work should improve model capacity or
train a calibrated value head rather than tune more Q temperatures.

The trace audit found the concrete omission: schema v1 encoded weapon Attack
but not temporary hero Attack. At the reported Searing Fissure decision, the
v1 model therefore could not observe the three points of temporary Attack. The
v2 encoder fixes this and other analogous dynamic-state gaps. A first 64-game
v2 student reduced validation KL to 0.241 and raised policy top-1 from 28.1% to
31.5%. On the audited action its attack prior rose from 0.507 to 0.630 and root
visits changed from 2:2 to 3:1 in favor of attacking. Its same-seed pilot scored
14/20 at four simulations and 17/20 at 32, with zero invalid actions. These are
engineering signals only; the v2 training tranche was seat-imbalanced 43:21
and needs another balanced tranche plus a larger paired evaluation before
promotion.

Benchmarks can now load one checkpoint per worker, run independent games in
parallel, report wall-clock time, and emit a Wilson interval. Multi-process NPU
inference was verified with four workers on Ascend 910C. Special generated
tokens are excluded from unresolved hidden-card fallback sampling; otherwise a
source-less zero-tier Void Soul could enter a determinization. Known generated
tokens remain represented by their source-specific public belief slots.

The next budget-controlled study separated search strength from distillation.
On 20 fresh seat-swapped games, plain 64-simulation ISMCTS beat otherwise
identical 16-simulation ISMCTS 18/20, and beat 32-simulation ISMCTS 18/20.
Thus four simulations was only a smoke-test budget and 64 simulations is the
current strength setting; 32 remains a lower-latency candidate, not an
equivalent-strength replacement. `benchmark_mcts.py` accepts independent
`--baseline-samples`, `--baseline-iterations`, `--baseline-tree-depth`, and
`--baseline-rollout-depth` values so unequal-budget controls are explicit in
the report.

Two independent schema-v2 64-simulation teacher tranches contain 128 games and
11,262 decisions. Their root targets consistently visit about 12--13 actions,
with mean maximum probability about 0.506 and entropy 1.55--1.58. A policy-only
student trained from those stronger targets did not beat the 16-simulation
student at an equal 32-simulation inference budget (10/20). Mixing 32 strong
teacher games into the old 128-game set scored 11/20. Replacing visit-share
targets with the teacher's final hard action was worse, losing 7/20 to the
soft-target student. The promoted training target therefore remains root visit
shares; stronger teachers are demonstrably useful search agents but their full
advantage has not yet been distilled by this small MLP.

An explicit state/action-product head also failed its controlled offline test
(validation policy KL 0.270 versus 0.245 for the additive head). It remains an
optional experiment rather than the default architecture. Training now records
the split seed and validation game seeds, supports multiple input datasets,
and can early-stop on validation policy KL while restoring the best epoch.
A 256-game policy/value attempt still overfit its value head: train Brier was
0.029 but validation Brier was 0.351, worse than the 0.25 constant baseline.
Neural leaf values therefore remain disabled.

Feature schema v3 fixes an observer-frame mismatch: states were encoded as
own/enemy while action source and target players were encoded as absolute seat
0/1. New checkpoints use relative action players; v1/v2 checkpoints retain
their original encoder. A 128-game v3 high-budget student scored 56/100 against
an independently trained v2 high-budget student at equal 32-simulation search
(Wilson 95% interval 46.2%-65.3%, paired sign p=0.210). This is a correctness
fix with only directional, non-significant strength evidence.

A first DAgger-style tranche executes a 16-simulation behavior policy while a
64-simulation teacher labels every reached state. The agents disagreed on
58.8% of non-forced decisions, confirming meaningful deployment-distribution
shift. Adding 32 such games to the 128 teacher-self-play games scored 13/24
against the base v3 student, so one tranche is insufficient evidence of gain.
The data generator records both `chosen_action` and `executed_action`, behavior
configuration, and disagreement rate.

Feature schema v4 additionally records the target zone. Schema v3 could not
distinguish an otherwise identical target in hand from one on board. The v4
student improved offline validation top-1 from 38.4% to 40.9% and policy KL
from 0.489 to 0.464 across independent splits, but scored only 9/24 against the
v3 student. The information fix remains, while the v4 checkpoint is not a
promoted strength model. A constrained bilinear policy head also failed its
offline gate (validation KL 0.498 versus 0.489 for additive v1) and was not sent
to direct play. Long benchmarks now print progress after every completed game,
including out-of-order worker completions.

For an equal simulation-budget comparison, run
`python scripts/compare_search.py --pairs 10 --samples 2 --iterations 8`.
The small pinned smoke run uses 16 simulations per decision and exists only to
verify measurement parity; larger paired runs are required for strength claims.

Run `python scripts/audit_belief.py --games 50` to audit the bookkeeping over
complete mirrors. The pinned report covers 50 finished games and 10,158 decision
points with zero unresolved hidden slots. Public plays, discards, burns, returned
spells, Discover results, fixed generators, random Pirate generation, and Void
Soul generation all update the same candidate ledger.

The result is intentionally labeled `generation_profile=closed_generation_pools`.
Stadium Announcer now uses a 32-weapon supported subset, including their
relevant passive, attack-trigger, replacement, and Deathrattle behavior. Its
actual Standard pool is class-unrestricted and contains 35 weapons in the pinned
snapshot, so 3 transitive-generation weapon rules remain before that pool is
complete. Card instances now retain class, `started_in_deck`, `created_by`, and
Dormant/Frozen state; weapons retain their kill ledger for effects such as Frostmourne.
Dragon discovery has 42/47 candidates eligible for this fixed deck. Two
otherwise collectible Dragons are excluded because the starting deck does not
activate Herald generation. The Pirate generation pool is now complete at
11/11, so Sky Raider can use its full pinned-Standard pool. The eligible
Warrior-minion pool currently has 39/40 supported candidates; the remaining 5
eligible Dragons and 1 Warrior minion stay restricted until their transitive
rules are implemented. Runtime pools are asserted against the audit so a new
rule cannot be reported as covered while remaining unreachable from its
generator. This profile validates engine invariants and direct card behavior; it is not yet a
ladder-strength or game-client-fidelity win-rate benchmark.

The final Warrior minion, Undefeated Champion, opens a separate pool of 65
collectible Standard 1-Cost minions. Coverage is tracked in summon context:
Battlecries and other from-hand effects do not execute, while keywords,
auras, end-turn triggers, and Deathrattles still must be modeled. The current
contextual closure is 60/65; Champion remains excluded until it reaches 65/65.
The first Tortotem dependency tranche is now explicit in the audit: its random
multi-type-minion pool contains 55 cards, 50 are generally playable in the
current runtime, and 5 still need rules. The closed tranches add
Firegill, Specter of Despair, Chillfallen Baron, Cyborg Patriarch, Sandmaw, and
Cinderfin, including Dormant, can't-attack, Kindred, draw, and Deathrattle
behavior; plus Sinful Steed, Chromatic Broodmother, Augmented Porcupine,
Chillspine Stegodon, Mechanized Magma, and Bonechill Stegodon, including
full-Health Reborn, attack-triggered Mana refresh, random-split damage, Freeze,
Fire-spell growth, and multi-target Deathrattles.
The third tranche adds Techysaurus, Everburning Phoenix, Magma Hound,
Tyrannogill, Dread Raptor, Slagclaw, and Fire Plume Phoenix. This also adds
per-game/per-turn play counters, delayed end-of-turn returns, attack-survival
triggers, targeted Battlecries, filtered draws, and explicit Bonus Effects.
The fourth tranche promotes six already-complete persistent/Deathrattle cards
into general play support and adds Mirrex, Time Adm'ral Hooktail, Torga, and
Volcanic Thrasher. It introduces dynamic in-hand copying, opponent-side token
ownership, hand-filling Chest Deathrattles, Kindred-aware paired draws, spell
school metadata, and per-card Spell Damage bonuses.
The fifth through seventh tranches raise the closed total to 50/55. They add Prepare,
per-turn death counts, Corpses and Corpse payment/choices, conditional Reborn,
maximum-Health stealing, edge-target Kindred damage, and Magmaw's persistent
Colossal appendage queue. They also cover Nythendra's split/reform lifecycle,
lifetime Overload discounts, and Blackwing Experiment's attack-snapshot damage
spell. The remaining five cards are kept out because they open broader
Mech/Demon/5-Cost or variable-Cost minion pools.

Those secondary pools are now exported separately instead of being hidden
behind the five outer cards. The Demon play-from-hand pool is 36/38 complete;
the remaining rules are Alara'shi itself and Treacherous Tormentor's much larger
Legendary Discover dependency. The audit also reports the Mech, 5-Cost, 2-Cost,
and 4-Cost minion pools. This tranche adds explicit hand targeting, self-damage,
discard, Freeze, copying/shuffling, Riftcleaver destruction, Tichondrius's next-
Demon discount, Bloodthistle's secret false copy, and Xavius's deck-backed Dark
Gift Discover.

Alara'shi's hand transformation and Shadowflame Stalker's doubled Dark-Gift
Discover are implemented but deliberately marked blocked rather than generally
supported. Their Demon dependency is still 36/38 because Treacherous Tormentor
opens a Warrior/Neutral Legendary pool with 54 candidates, of which 35
currently have complete play rules. Automated tests assert that staged outer
generators cannot leak into Tortotem's live pool before this closure is complete.

The first Mech play tranche closes 14 more cards and raises that dependency to
23/29. It covers Hero-Power and every-turn triggers, tribe-filtered draws,
generated-deck cleanup, conditional draw, start-of-turn hand swapping, deck
spell copying, hero Divine Shield, stat replacement with a temporary face-
attack restriction, turn-count scaling, double damage, and deterministic
Deathrattle tokens/destruction. The final six Mechs are secondary generators:
their dependencies are now measured as 32/35 weapons, 8/18 Rewind cards,
35/54 Warrior/Neutral Legendary minions, and 24/29 Aura cards.

The first closed Rewind tranche adds Chrono Daggers, Bygone Doomspeaker,
Cease to Exist, Aeon Rend, and Shadows of Yesterday. Rewind snapshots both
players immediately before the random effect, so retrying replaces rather than
stacks damage, discards, destruction, or summoned Shades. The remaining ten
Rewind cards all open another random Beast, spell, minion, Legendary, or
recursive Rewind pool and stay excluded until those dependencies are closed.

The first Aura play-from-hand tranche promotes four rules that were already
complete in narrower summon contexts (Tichondrius, Spiderling, Captive
Nathrezim, and Quel'dorei Fletcher), and adds Survivalist, Raid Leader,
Stormwind Champion, Dire Wolf Alpha, and Murloc Warleader. Continuous stat
auras stack, follow board adjacency, survive Silence on the recipient, and are
removed immediately when their source is silenced or leaves play.

The second Aura tranche adds Kayn Sunfury, Goldrinn, Naralex, Arachnathid,
Azure Queen Sindragosa, and Bralma Searstone. Combat legality now supports
friendly Taunt bypass, damage calculation applies additive Elemental bonuses
before Beast doubling, Poisonous can come from a removable external aura, and
the cost engine tracks both the first Dragon played each turn and conditional
Arcane-spell discounts. These counters and effective keywords are included in
snapshots so traces remain auditable.

The third Aura tranche adds Falric, Toreth the Unbreaking, and Ido of the
Threshfleet. Corpse gain now supports multiplicative living Falric auras and
Falric's filtered draw includes cards whose Mana cost is replaced by Corpses.
Toreth tracks three-hit Divine Shields independently on minions and heroes,
including aura removal. Ido dynamically supplies exactly one reusable Holy
spell while active and removes it when silenced or gone.

Azshara, Ocean Lord is the first fully closed Colossal Aura. It places up to
two Tentacles beside the main body, respects the seven-slot board limit, grants
1/2/4 temporary hero Attack per Tentacle from the current Herald tier, and
raises the hero attack limit to two while an unsilenced Azshara remains alive.
Fandral is intentionally not counted yet: it is inert in the current Dragon
mirror closure, but will need real Choose One composition when the Druid deck
is admitted rather than being mislabeled as globally complete.

The first general Legendary tranche closes Warmaster Blackhorn, The Black
Knight, Bloodmage Thalnos, King Mukla, Cairne Bloodhoof, Taelan Fordring,
Overlord Runthak, Tindral Sageswift, and Krog. This adds two-deck filtering,
targeted Taunt destruction, board Spell Damage, Banana spells, deterministic
Deathrattle summons and filtered draws, attack-triggered hand buffs,
turn-sensitive enemy-wide Deathrattle damage, and end-turn stat replacement.
Together with Naralex from the Aura work, the Warrior/Neutral Legendary pool is
now 27/54 complete.

The second general Legendary tranche adds Finja, Lorewalker Cho, Keymaster
Alabaster, Warden Maiev, Togwaggle, and City Chief Esho. It closes
attack-and-kill deck summons (including forced attacks), spell-copy trigger
timing, opponent-draw copying at fixed Cost (1), post-Battlecry Dormant buffs,
two-hand redistribution, and shared-tribe buffs across board, hand, and deck.
The Warrior/Neutral Legendary pool is now 33/54 complete.

Genn, Cursed King and The Egg of Khelos form the next deterministic closure.
Genn now transforms reversibly as hand parity changes and upgrades Warrior's
Hero Power to four Armor for one Mana when played as Worgen King. Khelos uses
all four intermediate Egg tokens before hatching the final 20/20 Taunt Beast.
This raises the pool to 35/54.

Stardust Scythe and its player-bound Void Soul upgrade state are implemented
through the capped tenth tier. The Standard 1- through 10-Cost Demon summon
pools are closed (38/38 total), so Stardust Scythe is admitted to Stadium
Announcer's fully supported random-weapon pool.

Tiny Pal's explicit ammunition decision and its Frost and Fire modes are also
implemented, including post-attack reselection and Frozen-duration handling.

## Rule architecture migration

Card behavior is being migrated from the original single-file compatibility
handlers into the composable registry in `src/hsa/rules.py`. The first 42 rules
now use typed Battlecry, Deathrattle, and Spell hooks with reusable Draw,
filtered Draw (including cost adjustment), Summon, generated-hand-card,
targeted/board damage, targeted and zone buffs, armor/mana, hero damage/healing,
death-resolution barriers, and state-update effects.
Fixed generated tokens used by these rules now load their base metadata from
HearthstoneJSON; explicit aliases cover Core IDs whose snapshot entry retains
the historical ID.
Existing special handlers remain active until their focused tests pass through
the new layer, so the migration does not invalidate the deterministic baseline.

`scripts/audit_card_rules.py` scans exact card IDs and historical aliases in
the pinned RosettaStone and Fireplace source trees. The current audit covers
280 closed-pool entities and finds upstream references for 78; every row records
its metadata source, implementation layer, upstream location and license, and
verification status. See `docs/RULE_ARCHITECTURE.md` for the migration policy
and `reports/card_rule_manifest.json` for the machine-readable manifest.
Tiny Pal remains outside the closed random-weapon pool until its two
card-generating modes (a random 3-Cost minion and a discounted random Battlecry
minion) have complete transitive rule coverage.

Audit the remaining generation closure with:

```bash
.venv/bin/python scripts/audit_generation_pools.py
```

The summary is `reports/generation_pool_audit.json`; it now includes a structured
`weapon_closure_backlog` explaining why each of the final three weapons is blocked
and which secondary card pools must close first. The per-card rule backlog is
`reports/generation_pool_cards.csv`.

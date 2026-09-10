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

The first implementation milestone is a vertical slice of two decks, followed by
cross-match expansion. Every added card needs a focused rules test and at least
one deterministic replay fixture.

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
interval, and is pinned to `dragon-warrior-closed-v2` so it is not confused with
future full-generation-pool results. `HeuristicPolicy` reads the acting player's
hand and public board state only; it does not inspect hidden opposing cards or
deck order.

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
Schema v1 has a 281-card vocabulary, 867 state features, and 612 action
features. Opponent hidden identities are excluded by construction. The
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

Benchmarks can now load one checkpoint per worker, run independent games in
parallel, report wall-clock time, and emit a Wilson interval. Multi-process NPU
inference was verified with four workers on Ascend 910C. Special generated
tokens are excluded from unresolved hidden-card fallback sampling; otherwise a
source-less zero-tier Void Soul could enter a determinization. Known generated
tokens remain represented by their source-specific public belief slots.

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

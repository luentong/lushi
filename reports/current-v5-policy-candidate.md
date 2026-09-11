# Current Dragon Warrior v5 policy candidate

This document identifies the current **closed Dragon Warrior mirror** policy
candidate. It is not a claim about full Standard Hearthstone, arbitrary
opponents, live-client automation, or a complete value model.

## Artifact identity

- Ruleset: `dragon-warrior-closed-v5`
- Ruleset source fingerprint:
  `af31f09933b967304bac09a01999d8de0c165445d30ce10545f0284b48a2858e`
- Checkpoint: `reports/policy-value-v5-structured-256.pt`
- Server artifact:
  `/workspace/let/hearthstone-agent/reports/policy-value-v5-structured-256.pt`
- Checkpoint SHA-256:
  `ed49bf8f5b41576c0a81db48cf3fd934b0d69c9b15a5cbe9587fef0ac6a7217c`
- Architecture: structured residual v5; state 1217, action 618, hidden 512,
  action hidden 256, 4 residual blocks, card embedding 128.

## Training

The dataset is `policy-value-v5-teacher16-256.jsonl.gz`: 256 independent
Dragon Warrior mirror games and 22,227 decisions. The teacher used four public
belief samples × four ISMCTS iterations, with at least one simulation for every
root action and a cap of 16 total iterations. Training ran on Ascend 910C for
eight epochs (best checkpoint epoch 5), with a grouped-by-game validation split.

Held-out policy top-1 accuracy was 34.47%. Held-out value MAE was 0.7454; that
value head is therefore not used for search. The candidate is a **policy prior
only** and keeps heuristic rollouts as leaf evaluation.

## Independent confirmation

The four independent seat-swapped benchmark shards are aggregated in
`reports/policy-value-v5-vs-ismcts-104games-npu.json`.

- Candidate: policy-prior PUCT using the v5 checkpoint.
- Baseline: ordinary shared-tree ISMCTS.
- Both: 4 samples × 4 iterations, tree depth 8, rollout depth 3; candidate cap
  16 total iterations and one initial simulation per root action.
- Result: 79 / 104 wins (75.96%), Wilson 95% CI 66.92%–83.15%.
- Seat-swapped pairs: 29 sweeps, 21 splits, 2 full losses; exact two-sided sign
  test across 31 decisive pairs: `4.63e-7`.
- Invalid actions: 0 / 104.

This is enough to use it as the current v5 mirror **candidate** in further
algorithm work. A second independently generated training dataset/checkpoint
must reproduce the result before it replaces the historical v3 result as the
strongest general research conclusion. No checkpoint is eligible for real-time
advice against a non-mirror Standard deck until that matchup's direct card list
and generated-card closure are complete.

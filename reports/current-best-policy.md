# Current best Dragon Warrior mirror policy

This file records the promoted strategy for the closed Dragon Warrior mirror
ruleset. It is not a claim about full Standard Hearthstone strength.

## Runtime configuration

- Ruleset: `dragon-warrior-closed-v3`
- Agent: structured residual v5 neural policy prior + PUCT
- Value head: **disabled**
- Checkpoint: `reports/policy-value-rules-v3-structured-v5-2048.pt`
- Server artifact: `/workspace/let/hearthstone-agent/reports/policy-value-rules-v3-structured-v5-2048.pt`
- SHA-256: `d0733ac05350d4f65f3bec9423e32a5982cd8d574183c3071d8116e8cba3d0c1`
- Belief samples: 4
- Iterations per sample: 4
- Tree depth: 8
- Heuristic rollout depth: 3
- Minimum simulations per root action: 1
- Maximum total iterations: 32

The architecture shares learned card embeddings across the acting player's
hand, both boards, action source card, and action target card. The operators are
portable PyTorch layers validated for forward, backward, and checkpoint reload
on Ascend 910C with `torch_npu`.

## Promotion result

Against ordinary ISMCTS at the same search budget, four independent 26-game
shards produced 75 wins in 104 games:

- Win rate: 72.115%
- Wilson 95% confidence interval: 62.827%-79.828%
- 52 seat-swapped seed pairs: 24 sweeps, 27 splits, 1 lost pair
- Exact two-sided sign-test p-value over decisive pairs: 0.00000155
- Aggregate report: `reports/v5-policyonly-vs-ismcts-104games.json`

This is strong evidence that the learned policy prior improves search within
the current ruleset and budget. Generalization still needs independent training
checkpoints and additional deck matchups.

## Rejected value-head configuration

Using the checkpoint's value head for leaf evaluation won only 32 of 104 games
against the same checkpoint used policy-only:

- Win rate: 30.769%
- Wilson 95% confidence interval: 22.716%-40.192%
- 52 seat-swapped seed pairs: 2 sweeps, 28 splits, 22 lost pairs
- Exact two-sided sign-test p-value over decisive pairs: 0.0000359
- Aggregate report: `reports/v5-value-vs-policyonly-104games.json`

The value head is therefore research-only. Do not enable model leaf values in
the promoted runtime until value targets, calibration, and independent match
validation improve.

## Auditable Chinese traces

- Candidate in seat 1, win: `reports/best-v5-policy-trace-202610050003-seat0.zhCN.md`
- Candidate in seat 2, win: `reports/best-v5-policy-trace-202610050000-seat1.zhCN.md`

Both traces use the promoted policy-only configuration and record every action,
legal-action count, root visits, neural prior, resolved event, and resulting
public game state.

# Explicit mulligan pipeline

The in-game policy/value checkpoint is unchanged. Mulligan uses a separate
four-card, 16-mask classifier and the engine's `MULLIGAN_TOGGLE` /
`MULLIGAN_CONFIRM` actions. Traces show these actions at turn 0.

Generate openings from the configured multi-deck pool:

```bash
python scripts/generate_mulligan_data.py \
  --games 8192 --output reports/mulligan-v3/openings-8192.jsonl
python scripts/train_mulligan.py \
  --data reports/mulligan-v3/openings-8192.jsonl \
  --output reports/mulligan-v3/mulligan-head.best.pt \
  --epochs 30 --batch-size 256 --device npu:2
```

The game seed, not individual player record, determines the train/validation
split. The input contains the offered cards' public attributes, the declared
own deck's cost curve, opponent class, and seat. It contains no opponent hand
or hidden deck order. Card IDs and deck IDs in the JSONL are for auditing, not
network inputs. The target is a sampled opening-curve proxy, **not** a win-rate
oracle or a professional player's mulligan.

Use `--mulligan-mode model --mulligan-checkpoint PATH` with
`generate_policy_value_data.py`, `generate_multideck_policy_value_data.py`, or
`trace_search_match.py`. `--mulligan-mode teacher` explicitly executes the
opening-curve teacher without loading a model; the default `automatic` preserves
older data-generation behavior. The model has a per-decision safety fallback:
if its chosen mask scores below the legacy automatic mask under the same
opening-curve proxy, the legacy mask is used. This does **not** guarantee a
better real-game decision.

Run an independent, seat-swapped gameplay check:

```bash
python scripts/evaluate_mulligan.py \
  --checkpoint reports/mulligan-v3/mulligan-head.best.pt \
  --pairs 50 --deck-id 龙战_01 --deck-id 快攻德_01 \
  --deck-id 脏牧_01 --deck-id 先驱术_01 \
  --output reports/mulligan-v3/paired-eval-guarded-100games.json
```

Both seats use the same in-game `HeuristicPolicy` in this check; it isolates
the opening choice, but is not an evaluation of the JEV in-game checkpoint or
ranked-ladder strength. Any future mulligan checkpoint must keep its feature
schema and teacher version aligned, and should be validated by paired games
against a stable in-game policy before replacing the incumbent.

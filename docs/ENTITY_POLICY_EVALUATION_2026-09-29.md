# Entity v1：数据检查与独立对战基线

更新：32 局 bootstrap 后发现价值头过拟合，原自动 PPO 串联已停止，checkpoint 全部保留。新的校准审计、128 局扩样和验证关卡见 [ENTITY_VALUE_RECOVERY_2026-09-29.md](ENTITY_VALUE_RECOVERY_2026-09-29.md)。下文 smoke 基线为历史实测，不代表当前最新训练阶段。

## 当前进展与解释边界

上一轮 8 局冷启动、4 局 PPO 的模型仅用于工程验证。本轮为它补齐了对战基线，供 32 局教师 + 后续 64 局 PPO 候选比较。不是宣称 8 局训练可以得到优秀策略。

固定开发评测种子从 `202609299000` 起；不在本轮 32 局教师或 PPO 的种子范围内。两套卡组四种有序配对，每组 2 个 seed，交换 candidate 所在座位，共 16 局。模型均使用纯策略 argmax，不加 MCTS/PUCT；起手替换仍使用现有引擎默认，不是模型学会的留牌策略。

| 对手 | 胜 / 负 | 初筛胜率 | 未终局 / 非法动作 |
| --- | --- | --- | --- |
| 冷启动模型 `entity-bootstrap-smoke.pt` | 7 / 9 | 43.75% | 0 / 0 |
| 启发式 | 8 / 8 | 50.00% | 0 / 0 |
| 旧模型 `closed-loop-v2.epoch2.pt` 的纯策略 | 6 / 10 | 37.50% | 0 / 0 |

这组结果没有证明小样本 PPO 已经提高强度，样本也不足以断言必然退步。旧最佳模型不替换。尤其不能把这组纯策略胜率直接与历史带 PUCT 搜索的胜率作比较。

## 新增工具

### `scripts/evaluate_entity_policy.py`

- 支持 entity checkpoint、legacy checkpoint、启发式三种对手。
- 四种有序 matchup、同 seed 交换座位，报告总体、先后手、分配对结果。
- 截断/异常单列，不标成平局或失败胜负；配对统计只纳入两局都有效的完整配对。
- 不把一对种子的两局当成独立样本；按 seed-pair 均分，给出保守 Hoeffding 95% 区间。
- 保留每局动作。`--save-traces` 额外输出场面/手牌，兼容现有 HTML 回放生成器的 JSON 结构。
- 全知回放仅用于离线审计，模型看不到对手手牌快照。
- 输出 checkpoint、代码和卡组配置哈希，不执行训练，不自动晋级。

```bash
python scripts/evaluate_entity_policy.py \
  --candidate reports/entity-pilot32-v1/entity-ppo.pt \
  --opponent-kind legacy \
  --opponent /workspace/hs_decision_quality_verify_20260928/reports/strategy-loop-v2/closed-loop-v2.epoch2.pt \
  --device npu:1 --pairs-per-matchup 2 --seed 202609299000 \
  --split development --save-traces --output reports/entity-pilot-vs-legacy-dev
```

使用者应先确认设备空闲，且输出目录不存在。跨多个 checkpoint 做选择使用开发集；选定后必须冻结候选，在另一批未使用种子上做更大规模 `confirmation` 评测。脚本的 `split` 是明确标签，不会自动保证外部训练数据与种子没有交叉。

### `scripts/audit_entity_dataset.py`

流式检查动作/标签对齐、终局收益玩家视角、费用字段、实体索引、私有区域和有限数值。

```bash
python scripts/audit_entity_dataset.py \
  --manifest reports/entity-pilot32-v1/pipeline.json \
  --output reports/entity-pilot-final-audit.json
```

必须通过 manifest 选择已经成功提交的分片。对运行中的目录直接 `teacher-*.jsonl.gz` 会扫到临时 `.records.jsonl.gz`；这些不是完成的数据，不能据此诊断训练样本缺失 header。

教师动作访问覆盖率按选择来源拆分：单一合法动作和已证明的限界斩杀可能没有树访问；等价动作合并也影响逐实体计数。覆盖率不是“正确决策比例”，结构检查通过也不证明教师最优或模拟器所有规则正确。

## 服务器产物

工作目录：`/workspace/hs_observer_entity_20260929`。

```text
reports/entity-eval-smoke-vs-bootstrap/evaluation.json
reports/entity-eval-smoke-vs-heuristic/evaluation.json
reports/entity-eval-smoke-vs-legacy/evaluation.json
reports/entity-pilot-audit-committed-v1.json
reports/entity-pilot32-v1/pipeline.json
```

本轮相关回归累计 90 项通过。下一阶段关注新候选是否在固定预算下稳定改善，而不是只追求训练 loss 下降或教师 accuracy 上升。

## 本轮交接时训练状态

- 32/32 局新教师数据全部完成，没有失败；四种有序配对各 8 局。
- 共 2380 条决策，完整数据结构检查通过。
- 按整局种子划分：1845 条训练、535 条验证；没有按同一局内的步骤随机拆分。
- 已进入 NPU 7 上的 6 个 epoch 冷启动续训，之后由既有一次性管线接续 8 轮 PPO。
- 最终完整数据检查：`reports/entity-pilot-audit-final32.json`。
- 这只是两个卡组的受控试训，尚未扩展到全卡组，也未完成新候选的强度验收。

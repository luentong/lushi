# Standard 卡牌迁移工作流

当前快照固定为 HearthstoneJSON build `251332`。迁移队列由
`scripts/build_standard_migration_queue.py` 生成，不能手工修改报告中的实现状态。

## 分工边界

每张卡只能有一个负责人；负责人提交规则、针对性测试和来源说明。其他人可以审查，
但不要同时编辑同一个规则声明或同一个测试函数。跨卡公共机制（事件队列、目标选择、
随机池、复制/变形）单独开 PR，并先补机制测试，再迁移卡牌。

推荐按批次分工：

| 批次 | 内容 | 验收重点 |
|---|---|---|
| A0 | 无文本随从、武器、地点和显式关键词 | 费用、身材、关键词、攻击限制 |
| A1 | 抽牌、弃牌、疲劳、手牌上限 | 牌库不足、爆牌、触发顺序 |
| A2 | 伤害、治疗、摧毁 | 目标合法性、护甲、吸血、死亡结算 |
| A3 | 召唤、增益、减益 | 位置、光环、临时效果、衍生牌 |
| B1 | Discover、随机、Choose One、Rewind | 随机种子、候选池闭包、选择状态 |
| B2 | Battlecry、Deathrattle、Aura、Quest | 事件顺序、沉默、复制和跨卡交互 |
| C | 无法组合的特殊脚本 | 必须有 Power.log 或官方行为证据 |

## PR 闸门

```powershell
python scripts/audit_standard_rules.py
python scripts/audit_card_rules.py
python scripts/build_standard_migration_queue.py
python scripts/validate_migration_queue.py
```

上游 RosettaStone/Fireplace 命中只是参考来源，不会自动提升
`playable_ready`。只有规则实现、针对性测试和回归测试都通过，才允许标记为
`verified`。发现未知卡牌或未知生成池时，运行时必须保持 fail-closed。

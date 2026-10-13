# 多卡组 PPO 信用分配对照（2026-09-30）

## 问题

原 actor 优势为 `终局胜负 - 当前 value`。在非平局中，同一局所有决策的优势符号相同：胜局里的错误动作也得到正向更新，败局里的正确动作也得到负向更新。改动只新增可选的 GAE(λ) actor 优势；critic 仍以真实终局胜负训练，不把估计回报冒充终局标签。默认参数仍保留原来的 `terminal` 模式。

## 离线审计

`scripts/audit_ppo_credit.py` 对前一次 3×256 局轨迹审计：768 局、30,151 个 learner 决策。`λ=0.95` 的 GAE 相比旧终局优势有 4,626 个决策（15.3%）符号相反；其中败局的 1,996 个动作得到正优势、胜局的 2,627 个动作得到负优势。这只能证明标签不同，不能证明 GAE 判定的好坏正确；value 估计仍有噪声。结果：`reports/entity-gamebalanced768-credit-audit.json`。

另用 `scripts/audit_entity_rollouts.py` 对账：八套牌各 96 局，决策行数每套约 3,152–4,271；按完整游戏等权避免长局多占梯度。历史对手版本依实际可用轮次分别出现 bootstrap 471 局、round1 211 局、round2 86 局；不是三个版本等份，因为首轮只有 bootstrap，第二轮没有 round2。value 的每局宏平均 Brier 为 0.180（常数 0.5 基线约 0.250），但首个决策 Brier 为 0.222；龙猎与光铸骑开局分别约 0.260/0.270，甚至劣于常数 0.5。故用价值差分给早期动作打 GAE 标签尤其可能引入噪声。完整审计：`reports/entity-gamebalanced768-rollout-audit.json`。这些是采集轨迹自身的校准统计，不是独立强度评测。

## 严格配对训练

从相同的 `reports/entity-pilot128-v2-repaired/entity-ppo.pt` 初始化，保持八套卡组、种子 `202609301700`、256 局、batch 16、2 个训练 epoch、学习率 `5e-6` 不变，唯一训练目标差异是 actor 优势。两个 rollout 的 10,073 条决策在 observer view、合法动作、选中动作、旧价值及游戏元数据上逐条完全相同；`scripts/compare_ppo_rollouts.py` 只忽略训练标签字段。GAE 版 256/256 终局、0 失败、1,260 次更新、无 KL 提前停止。实验权重（仅研究）：910B `reports/entity-multideck-ppo-20260930-gae95-r1.round1.pt`。

## 直接对战

双方模型都是相同初始化、相同 256 局训练数据的第一轮 checkpoint。评测覆盖八套牌的全部有序 matchup，并交换模型座位；无搜索的贪心 entity policy，不能外推为真实 PUCT 强度。

| 数据集 | GAE 胜-平-负 | GAE 得分率 | 失败/截断 |
| --- | ---: | ---: | ---: |
| 开发集，新种子，每 matchup 1 对 | 60-1-67 / 128 | 47.3% | 0 |
| 独立确认，新种子，每 matchup 2 对 | 132-0-124 / 256 | 51.6% | 0 |

确认集的座位配对 Hoeffding 95% 区间为 39.6%–63.6%。两组结果没有可靠证明 GAE 更强，因此不晋级、不部署、不继续盲目增加 PPO 轮数。报告：`reports/entity-gae95-r1-vs-terminal-r1-dev.json` 和 `reports/entity-gae95-r1-vs-terminal-r1-confirm.json`。这里的单一卡组原始胜率同时含卡组固有强弱，不能不经同卡组基线校正就称为模型在该卡组上的净改善。

## 为下一轮动作级对照补的基础设施

训练报告现在为每局保存双方完整 `action_trace`，`scripts/replay_entity_rollout.py` 可验证整局胜负并停在任意动作前的可复现局面；回放前强制核对卡牌库、卡组配置及引擎源码 SHA-256，错误卡组配置会被拒绝。实际烟测：龙战对穆格萨 54 个动作完整重放，终局胜者一致；停在第 12 步能够重建 Discover 选择根及三个合法选项。回放发现旧报告 `steps` 在终局后多计一次循环，已修为真实 `len(action_trace)`；旧报告的步骤计数有时会比实际动作数多 1，但本轮胜负、PPO 样本和梯度不受该计数错误影响。烟测报告在 910B：`reports/entity-trace-capture-smoke-fixed.report.json`。

`scripts/audit_entity_rollout_root.py` 复用现有公共 belief 配对后续模拟，可直接审计保存的 learner 动作。对上述 Discover 根、16 个配对随机样本、heuristic 延续：两个替代选项分别相对实际选择 `1 好/1 差/14 平` 与 `0/0/16`，**没有**可据此改标签的证据。烟测结果在 910B：`reports/entity-trace-root12-heuristic16-verified.json`。这只是管线验证，不是对 Discover 策略质量的证明。

下一步应从多卡组可复现根局面抽样，用同一 belief 样本、配对未来随机流、多个延续策略比较候选动作，再将高一致性且分差足够的对照转为 actor 训练目标；要先做小规模胜率 A/B，不能把单一 heuristic rollout 或低预算搜索访问次数直接当最优动作标签。现有 `scripts/audit_paired_root_outcomes.py` 可复用，但尚未形成可靠的大规模教师。

远程最新完整回归：894 项通过。

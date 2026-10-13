# 实体观察与真实自博弈：第一阶段实现

本分支落实 `PRO_LEVEL_TRAINING_AUDIT_2026-09-29.md` 中 A/B 阶段的最小训练闭环。
**这是工程验收，不是新模型强度验收，更不是职业级能力证明。**

后续状态：32 局 bootstrap 出现明显价值过拟合，已停止自动接入末轮权重。现增加最佳轮次选择、校准关卡和扩大独立对局数，详见 [价值恢复实验](ENTITY_VALUE_RECOVERY_2026-09-29.md)。

## 与旧训练的区别

| 环节 | 本次新增 |
| --- | --- |
| 观察 | 独立 `hsa-observer-entities-v1`，逐卡绑定身份、动态属性、区域和位置；加入英雄技能、Herald/Imbue/Leyline、任务进度、伤害对象等 |
| 隐藏信息 | 不读取真实未知牌库顺序；对手手牌/奥秘只有数量；候选套牌由外部配置提供，不取真实对手卡表作为唯一答案 |
| 网络 | `hsa-entity-transformer-v1`，实体间注意力；源/目标实体绑定的完整合法动作评分；独立 value head |
| 历史 | 最近 32 个白名单公共事件作为历史 token，长期计数另存；尚不是完整 recurrent 状态 |
| 旧模型利用 | 作为 ISMCTS 策略先验，生成带真实 ObserverView 的冷启动样本；**不是把不兼容的旧 MLP 权重直接加载到 Transformer** |
| RL | 更新后的策略重新生成对局，以终局胜负更新 PPO，不把重复训练静态教师数据称为自博弈 RL |
| 对手 | 有界历史 checkpoint 池，记录每轮所选对手版本 |
| 数据 | 保存行为 log-prob、动作掩码、玩家视角、终局/截断状态、策略版本、套牌和种子 |
| 失败 | 未终局样本不伪标平局；保留失败种子、动作轨迹和异常栈，成功对局不连带作废 |
| 兼容 | 旧 schema/词表不变；新实体 checkpoint 自带冻结词表、输入契约；未知实体使用未知 ID 加语义特征，不静默扩维 |

## 文件

- `src/hsa/observer_view.py`：模型观察边界与显式字段白名单。
- `src/hsa/entity_model.py`：实体 Transformer、动态 padding 和合法动作 mask。
- `scripts/generate_policy_value_data.py`：新增 `--teacher-checkpoint`、`--teacher-device`、`--teacher-value-mode`、`--export-observer-view`。
- `scripts/generate_multideck_policy_value_data.py`：向子任务传递上述参数。
- `scripts/train_entity_selfplay.py`：冷启动训练及同步 on-policy PPO 参考实现。
- `tests/test_observer_view.py`、`tests/test_entity_training.py`：新输入和训练契约测试。

任何影响字段语义或可见性的后续修改必须升级观察版本，不能仅因为 Tensor 形状没变就声称兼容。checkpoint/report 另保存源代码、卡库、卡组配置、数据及初始化模型 SHA256。

## 安全与信息边界

1. 同一玩家可连续执行多个动作，终局收益按该玩家计算，不按动作奇偶翻转正负。
2. 动作上限只是截断，不是游戏规则中的平局。截断局写问题库，不加入 Monte Carlo 胜负训练。
3. 对手 Discover 选项、私有抽牌事件、嵌入的未知法术不进入观察。
4. 修复 PublicBelief 根据对手秘密打出的奥秘真实 ID 排除候选套牌的问题；尚未揭示时保持宽候选。尚未完整建模“哪些奥秘未触发”提供的负证据。
5. 己方手牌同时保留固有费用与当前有效费用，避免条件减费只进入合法动作生成、却不进入网络观察。
6. PPO 使用同步冻结版本采样，无 dropout；测试单独/混合 padding batch 的动作概率一致性。每轮只训练当前 learner 的行为数据。
7. 旧教师使用 `prior-only`，不默认信任历史未充分校准的 value head；不能把这称作纯神经叶节点估值。

## 本次服务器位置

- 训练环境：FusionOne 内网的 **910B3**，不是 910C；具体连接信息保存在私有配置中。
- 隔离源码：`/workspace/hs_observer_entity_20260929`。
- 主验证设备：`npu:7`；数值探针临时使用 `npu:6`，完成后退出。
- 不修改原 `/workspace/hearthstone-agent` 的源码，也不停止其已有教师数据任务。
- 卡库与 `.deps` 通过只读使用的链接复用，不向链接目标写入。

主要产物：

```text
reports/neural-teacher-smoke.jsonl.gz
reports/entity-npu-probe.json
reports/entity-bootstrap-smoke.pt
reports/entity-bootstrap-smoke.report.json
reports/entity-ppo-smoke.pt
reports/entity-ppo-smoke.report.json
reports/entity-ppo-smoke.round1.jsonl.gz
reports/entity-ppo-smoke.round2.jsonl.gz
```

第一批教师样本只用于链路检查，含 8 局、559 个决策，不能作为正式泛化训练集。它生成于本次输入补充期间，部分可选字段缺失由 presence mask 表达；正式扩量应冻结当前代码后重新导出，不能将旧平面 Tensor 数据伪造升级为实体观察。

### 已完成的工程验收

- 服务器相关测试：79 项通过；本机无 PyTorch，非 Torch 测试正常，Torch 测试转到服务器执行。
- 新注意力实现的 CPU/NPU 最大输出差异约 `3.1e-5`，梯度全部有限；未再出现默认 Transformer 快路径的 CPU 回退警告。
- 6 层、256 维、8 个注意力头，实际 **7,784,706 参数**。
- 冷启动：475 条训练决策、84 条整局留出决策，2 个 epoch，约 60.7 秒。
- PPO：2 轮，共 4 局终局、154 条 learner 决策，约 43.8 秒；0 失败局。
- 覆盖快攻德对龙战、龙战镜像和快攻德镜像。对手均为历史 bootstrap 版本。
- 最大记录近似 KL 约 `0.00975`。这只检查更新是否数值稳定，不代表打牌强度。

旧模型没有被替换，新模型暂定为 smoke checkpoint。验证集和对局样本都过少，不公布所谓“新模型更强”的胜率结论。

### 已启动的下一轮受控试训

一次性管线 `scripts/run_entity_pilot.py` 已在同一隔离目录启动；不是定时任务。

- 目录：`reports/entity-pilot32-v1/`。
- 状态：`reports/entity-pilot32-v1/pipeline.json`；总日志：`reports/entity-pilot32-v1.driver.log`。
- 教师数据：龙战/快攻德四种有序配对，每种 8 局，共 32 局；每决策 2 个采样 × 32 次迭代，使用旧模型策略先验。
- 分配：NPU 4/5/6/7 各一个教师进程，单局独立分片；单局超过 900 秒记为工程超时，不伪造胜负。
- 进入训练条件：至少半数对局成功，且四种配对都有成功对局。其余失败记录和日志保留，不删除成功分片。
- 冷启动续训：从 `entity-ppo-smoke.pt` 初始化，在新数据上训练 6 个 epoch，学习率 `5e-5`，NPU 7。
- 随后自博弈：8 轮 × 每轮目标 8 个有效终局，每轮 2 个 PPO 更新 epoch，学习率 `2e-5`。每轮最多尝试目标局数的三倍，未终局样本隔离，不算作平局。
- 此规模仍是受控试训，不是职业级训练量，也没有替代独立胜率评测。

管线有完成/失败状态；若中断需检查日志并使用新输出路径重启，不把已有目录当作可覆盖临时目录。

## 复现命令

先确认所选 NPU 没被他人使用。以下从隔离目录执行，输出路径须选择未使用的新名称，避免覆盖已有模型。

```bash
source /usr/local/Ascend/cann-8.5.0/set_env.sh
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2
PY=/usr/local/python3.11.14/bin/python3.11

$PY scripts/train_entity_selfplay.py \
  --mode bootstrap --data reports/neural-teacher-smoke.jsonl.gz \
  --output reports/entity-bootstrap-next.pt --device npu:7 \
  --d-model 256 --layers 6 --heads 8 --epochs 2 --batch-size 8

$PY scripts/train_entity_selfplay.py \
  --mode ppo --init-checkpoint reports/entity-bootstrap-next.pt \
  --output reports/entity-ppo-next.pt --device npu:7 \
  --rounds 2 --games-per-round 2 --epochs 2 --batch-size 8 \
  --learning-rate 2e-5 --max-actions 400
```

`--init-checkpoint` 是权重 warm-start，会新建优化器；不是完整恢复中断的训练运行。数据按 game seed 划分训练/验证，当前小样本划分仅用于工程验收，不能代替卡表 hash/卡组族留出。

## 当前明确没有完成的部分

- 尚未证明新模型强于旧模型；不得上线替换当前最佳策略。
- 尚未覆盖标准模式所有可见/隐含机制状态，不能把白名单 v1 说成完整状态。
- 类别 tag 使用有界哈希嵌入，存在碰撞；历史为有限窗口，尚未加入长期 recurrent 记忆。
- 未知己方牌库的复杂变换、公开顶牌信息、秘密触发负证据等需进一步精确编码。
- 此次对手奥秘修复针对观察和候选推断；旧 ISMCTS 的所有隐藏区域重采样仍需完整审计，不能推广为搜索完全无信息泄露。当前小批教师使用不含奥秘的龙战镜像。
- PPO 是同步、小批单步推理参考实现，尚未做多 actor 合批推理、异步参数滞后修正、大规模 league 或高吞吐列式轨迹。
- 新实体网络尚未接入旧平面输入的 PUCT 接口；不能用旧 `--checkpoint` 参数直接加载。
- 尚未完成战术通过率、卡组族留出和独立配对对战晋级评测。

下一关卡是冻结观察协议、扩展多卡组冷启动和真实自博弈，加入独立强度对照，再决定是否扩到 384/512 宽度、8–12 层及更大数据量；不是仅靠增加 epoch 宣称变强。

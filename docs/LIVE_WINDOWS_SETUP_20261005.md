# Windows 实时建议部署

把以下文件放入项目目录：

- `config/live_known_decks.json`
- `config/live_candidate_decks.json`
- `models/standard91-generalized-expanded18-v1.epoch4.pt`（模型文件名可按实际 checkpoint 修改）

先校验配置：

```powershell
python scripts/validate_live_configs.py `
  --known config/live_known_decks.json `
  --candidates config/live_candidate_decks.json
```

在 4070 Ti Super 上启动只读建议：

```powershell
python scripts/live_recommender.py `
  --power-log "C:\Program Files (x86)\Hearthstone\Logs" `
  --checkpoint "models\standard91-generalized-expanded18-v1.epoch4.pt" `
  --known-decks config/live_known_decks.json `
  --candidate-decks config/live_candidate_decks.json `
  --mode belief `
  --self-class WARRIOR `
  --opponent-class WARRIOR `
  --device cuda `
  --search-iterations 8 `
  --tree-depth 4 `
  --setaside-policy advisory
```

`--opponent-class WARRIOR` 只是英雄职业尚未从日志识别前的临时回退值；识别到对手英雄后会使用日志中的真实职业。程序只输出建议，不会控制炉石客户端。

候选文件中允许 20 张特殊卡组（当前为脏牧），实时过滤器会保留 20、30、40 张合法列表。

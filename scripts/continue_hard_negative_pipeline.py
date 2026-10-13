#!/usr/bin/env python3
"""Wait for full-trace audits, then build and train the next correction model."""
import json, subprocess, time
from pathlib import Path

ROOT=Path('/workspace/hearthstone-agent')
out=ROOT/'reports/standard91_generalized_20260924/hard_negative_v2'
names=['game01-all.json','game02-all.json','game03-all.json']
while True:
    ready=True
    for name in names:
        try: ready = ready and bool(json.loads((out/name).read_text()).get('complete'))
        except Exception: ready=False
    if ready: break
    time.sleep(30)
cmd=['/usr/local/python3.11.14/bin/python3','scripts/build_trace_hard_negative_shard.py',
 '--audit',*(str(out/n) for n in names),'--deck-config','config/decks_20260924_flat.json',
 '--checkpoint','reports/standard91_generalized_20260924/hard_negative_v1/standard91-hard-negative-v1.epoch4.pt',
 '--output',str(out/'trace-hard-negative-v2.pt'),'--report',str(out/'trace-hard-negative-v2.json')]
subprocess.run(cmd,cwd=ROOT,check=True)
train=out/'train'; train.mkdir(exist_ok=True)
cmd=['/usr/local/python3.11.14/bin/python3','scripts/train_columnar_policy_value.py',
 '--data',*map(str,sorted((ROOT/'reports/standard91_generalized_20260924/columnar_train_v3').glob('*.pt'))),
 '--tactical-data',str(out/'trace-hard-negative-v2.pt'),'--tactical-repeat','8',
 '--init-checkpoint','reports/standard91_generalized_20260924/hard_negative_v1/standard91-hard-negative-v1.epoch4.pt',
 '--output',str(train/'standard91-hard-negative-v2.pt'),'--device','npu','--epochs','4','--batch-size','256',
 '--learning-rate','1e-5','--value-weight','.25','--action-value-weight','.35','--conditional-policy-weight','3.0','--checkpoint-every','1','--seed','20261006']
subprocess.run(cmd,cwd=ROOT,check=True)

#!/usr/bin/env python3
"""Turn trace search A/B audits into a schema-compatible hard-negative shard.

Neutral high-budget counterfactual roots provide soft policy and action-Q
targets; the recorded model action is retained as metadata so regret can be
audited without pretending that one search seed is infallible.
"""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from hsa.encoding import configure_card_vocab, encode_action, encode_state, feature_schema
from replay_trace_state import replay_trace_state

def softmax(xs, temperature=0.2):
    m=max(xs); ws=[math.exp(max(-80.,(x-m)/temperature)) for x in xs]
    z=sum(ws) or 1.; return [w/z for w in ws]

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--audit", nargs="+", type=Path, required=True)
    p.add_argument("--deck-config", type=Path, required=True)
    p.add_argument("--checkpoint", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--temperature", type=float, default=.20)
    p.add_argument("--min-neutral-seeds", type=int, default=2)
    p.add_argument("--teacher-mode", choices=("neutral", "rollout"), default="neutral",
                   help="Search mode used as the teacher target.")
    args=p.parse_args()
    ck=torch.load(args.checkpoint,map_location="cpu",weights_only=False)
    fs=ck["report"]["feature_schema"]
    configure_card_vocab(fs.get("card_vocab_mode","legacy"), vocabulary=fs.get("card_vocab_ids"))
    rows=[]
    for audit_path in args.audit:
        audit=json.loads(audit_path.read_text(encoding="utf-8"))
        trace=Path(audit["trace"])
        # remote absolute paths are valid on the training host; local callers
        # may pass a copied audit only for report inspection.
        grouped={}
        for r in audit.get("rows",[]):
            if r.get("mode")!=args.teacher_mode: continue
            key=(int(r["step"]),int(r["budget"]),int(r.get("root_min_visits",0)))
            grouped.setdefault(key,[]).append(r)
        for (step,budget,minimum), rs in sorted(grouped.items()):
            if len({int(r["seed"]) for r in rs}) < args.min_neutral_seeds: continue
            game=replay_trace_state(trace, step, args.deck_config)
            actions=game.legal_actions(); desc=[game.describe_action(a) for a in actions]
            qsum=[0.]*len(actions); visits=[0]*len(actions); seen=[set() for _ in actions]
            for r in rs:
                for a in r.get("alternatives",[]):
                    try: i=desc.index(a["action"])
                    except ValueError: continue
                    v=int(a.get("visits",0))
                    if v>0:
                        qsum[i]+=float(a.get("mean_value",0.))*v; visits[i]+=v; seen[i].add(int(r["seed"]))
            valid=[visits[i]>0 and len(seen[i])>=args.min_neutral_seeds for i in range(len(actions))]
            if not any(valid): continue
            q=[qsum[i]/max(1,visits[i]) for i in range(len(actions))]
            target=softmax([q[i] for i in range(len(actions)) if valid[i]],args.temperature)
            policy=[0.]*len(actions); j=0
            for i in range(len(actions)):
                if valid[i]: policy[i]=target[j]; j+=1
            best=max((i for i in range(len(actions)) if valid[i]),key=lambda i:q[i])
            model_actions=[r.get("chosen") for r in rs if r.get("mode")=="model"]
            model_action=model_actions[0] if model_actions else None
            selected=[float(r.get("search",{}).get("selected_value",0.)) for r in rs]
            rows.append({
                "state":list(encode_state(game,game.current,schema_version=int(fs["schema_version"]))),
                "actions":[list(encode_action(game,a,schema_version=int(fs["schema_version"]))) for a in actions],
                "policy":policy,"q":q,"visits":visits,"valid":valid,
                "chosen":best,"actor":game.current,"game_seed":step,
                "value":sum(selected)/len(selected) if selected else 0.,
                "model_action":model_action,"model_action_matches_teacher":model_action==desc[best],
                "trace":str(trace),"step":step,"budget":budget,"teacher_mode":args.teacher_mode,
                "neutral_seeds":sorted({int(r["seed"]) for r in rs}),
            })
    if not rows: raise SystemExit("no usable neutral roots")
    maxa=max(len(r["actions"]) for r in rows); n=len(rows); size=int(fs["action_size"])
    states=torch.tensor([r["state"] for r in rows],dtype=torch.float32)
    actions=torch.zeros((n,maxa,size)); mask=torch.zeros((n,maxa),dtype=torch.bool)
    pol=torch.zeros((n,maxa)); qv=torch.zeros((n,maxa)); qvis=torch.zeros((n,maxa),dtype=torch.int32); qmask=torch.zeros((n,maxa),dtype=torch.bool)
    chosen=torch.zeros(n,dtype=torch.long); values=torch.zeros(n); actors=torch.zeros(n,dtype=torch.int8); seeds=torch.zeros(n,dtype=torch.int64); winners=torch.full((n,),-1,dtype=torch.int8); conditional=torch.ones(n,dtype=torch.bool)
    for k,r in enumerate(rows):
        m=len(r["actions"]); actions[k,:m]=torch.tensor(r["actions"]); mask[k,:m]=True; pol[k,:m]=torch.tensor(r["policy"]); qv[k,:m]=torch.tensor(r["q"]); qvis[k,:m]=torch.tensor(r["visits"]); qmask[k,:m]=torch.tensor(r["valid"]); chosen[k]=r["chosen"]; values[k]=r["value"]; actors[k]=r["actor"]; seeds[k]=r["game_seed"]
    out={"header":{"feature_schema":fs,"teacher":"trace-hard-negative-counterfactual-q-v1",
                    "teacher_mode":args.teacher_mode,"source_audits":[str(x) for x in args.audit],"temperature":args.temperature},"states":states,"actions":actions,"mask":mask,"chosen":chosen,"values":values,"actor":actors,"value_valid":torch.ones(n,dtype=torch.bool),"conditional":conditional,"game_seed":seeds,"winner":winners,"action_values":qv,"action_value_visits":qvis,"action_value_mask":qmask,"policy_targets":pol,"count":n}
    args.output.parent.mkdir(parents=True,exist_ok=True); torch.save(out,args.output)
    report={"records":n,"max_actions":maxa,"mismatches":sum(not r["model_action_matches_teacher"] for r in rows),"rows":[{k:r[k] for k in ("trace","step","budget","neutral_seeds","model_action","model_action_matches_teacher")} for r in rows]}
    args.report.parent.mkdir(parents=True,exist_ok=True); args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"records":n,"mismatches":report["mismatches"],"output":str(args.output)}))
if __name__=="__main__": main()

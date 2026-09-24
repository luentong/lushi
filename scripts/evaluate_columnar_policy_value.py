#!/usr/bin/env python3
"""Evaluate a columnar policy/value checkpoint on a deterministic seed split."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import torch
import torch.nn.functional as F
from train_policy_value import choose_device
from hsa.torch_model import StructuredResidualPolicyValueNet

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--checkpoint", type=Path, required=True)
    p.add_argument("--data", type=Path, nargs="+", required=True)
    p.add_argument("--device", choices=("cpu","npu"), default="npu")
    p.add_argument("--batch-size", type=int, default=256)
    p.add_argument("--validation-mod", type=int, default=5)
    p.add_argument("--validation-rem", type=int, default=0)
    args=p.parse_args(); device=choose_device(args.device)
    ckpt=torch.load(args.checkpoint,map_location="cpu",weights_only=False)
    meta=ckpt["report"]["model"]; schema=ckpt["report"]["feature_schema"]
    model=StructuredResidualPolicyValueNet(meta["state_size"],meta["action_size"],meta["hidden_size"],meta["action_hidden_size"],meta["residual_blocks"],meta["card_vocab_size"],meta["card_embedding_size"]).to(device)
    model.load_state_dict(ckpt["model_state_dict"]); model.eval()
    stat={"records":0,"policy_decisions":0,"correct":0,"abs":0.,"sq":0.,"target_sq":0.,
          "target_sum":0.,"value_sign_correct":0,"ce":0.,"entropy":0.}
    with torch.no_grad():
      for path in args.data:
        shard=torch.load(path,map_location="cpu",weights_only=False)
        ix=(shard["game_seed"].abs()%args.validation_mod==args.validation_rem).nonzero().flatten()
        for start in range(0,len(ix),args.batch_size):
          rows=ix[start:start+args.batch_size]
          if not len(rows): continue
          s=shard["states"][rows].to(device); a=shard["actions"][rows].to(device); m=shard["mask"][rows].to(device)
          y=shard["values"][rows].to(device); target=shard["policy_targets"][rows].to(device); chosen=shard["chosen"][rows].to(device)
          logits,val=model(s,a,m); logp=F.log_softmax(logits,1); nt=m.sum(1)>1
          stat["records"]+=len(rows); stat["policy_decisions"]+=int(nt.sum()); stat["correct"]+=int(((logits.argmax(1)==chosen)&nt).sum())
          stat["abs"]+=float((val-y).abs().sum()); stat["sq"]+=float(((val-y)**2).sum())
          stat["target_sq"]+=float((y**2).sum()); stat["target_sum"]+=float(y.sum())
          stat["value_sign_correct"]+=int(((val >= 0) == (y >= 0)).sum())
          stat["ce"]+=float((-(target*logp).sum(1))[nt].sum())
          tlog=torch.where(target>0,torch.log(target.clamp_min(1e-12)),torch.zeros_like(target))
          stat["entropy"]+=float((-(target*tlog).sum(1))[nt].sum())
    n=max(1,stat["records"]); q=max(1,stat["policy_decisions"])
    result={"records":stat["records"],"policy_decisions":stat["policy_decisions"],"policy_accuracy":stat["correct"]/q,"policy_cross_entropy":stat["ce"]/q,"policy_kl":max(0.,(stat["ce"]-stat["entropy"])/q),"value_mae":stat["abs"]/n,"value_mse":stat["sq"]/n,"value_brier":stat["sq"]/n/4,"value_sign_accuracy":stat["value_sign_correct"]/n,"target_mean":stat["target_sum"]/n,"neutral_value_mse":stat["target_sq"]/n,"neutral_value_brier":stat["target_sq"]/n/4,"split":{"mod":args.validation_mod,"remainder":args.validation_rem}}
    print(json.dumps(result,indent=2))
if __name__=="__main__": main()

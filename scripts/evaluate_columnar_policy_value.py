#!/usr/bin/env python3
"""Evaluate a columnar policy/value checkpoint on a deterministic seed split."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import torch
import torch.nn.functional as F
from train_policy_value import choose_device
from train_columnar_policy_value import _load_checkpoint_weights
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
    if not args.data:
        p.error("at least one columnar shard is required")
    first_shard=torch.load(args.data[0],map_location="cpu",weights_only=False)
    schema=first_shard["header"]["feature_schema"]
    ckpt=torch.load(args.checkpoint,map_location="cpu",weights_only=False)
    meta=ckpt["report"]["model"]
    model=StructuredResidualPolicyValueNet(schema["state_size"],schema["action_size"],meta["hidden_size"],meta["action_hidden_size"],meta["residual_blocks"],schema["card_vocab_size"],meta["card_embedding_size"])
    migration=_load_checkpoint_weights(model,ckpt,schema)
    model=model.to(device); model.eval()
    stat={"records":0,"value_records":0,"policy_decisions":0,"correct":0,"abs":0.,"sq":0.,"target_sq":0.,
          "opponent_value_records":0,"opponent_abs":0.,"opponent_sq":0.,"opponent_sign_correct":0,
          "q_records":0,"q_abs":0.,"q_sq":0.,"q_weighted_abs":0.,"q_weight_sum":0.,
          "target_sum":0.,"value_sign_correct":0,"ce":0.,"entropy":0.}
    turn_stat={name:{"n":0,"abs":0.,"sq":0.,"sign":0,"target_sq":0.} for name in ("turn_1_3","turn_4_6","turn_7_plus")}
    with torch.no_grad():
      for path in args.data:
        shard=torch.load(path,map_location="cpu",weights_only=False)
        ix=(shard["game_seed"].abs()%args.validation_mod==args.validation_rem).nonzero().flatten()
        for start in range(0,len(ix),args.batch_size):
          rows=ix[start:start+args.batch_size]
          if not len(rows): continue
          s=shard["states"][rows].to(device); a=shard["actions"][rows].to(device); m=shard["mask"][rows].to(device)
          y=shard["values"][rows].to(device); target=shard["policy_targets"][rows].to(device); chosen=shard["chosen"][rows].to(device)
          q_target=shard.get("action_values",torch.zeros_like(shard["policy_targets"]))[rows].to(device)
          q_visits=shard.get("action_value_visits",torch.zeros_like(shard["policy_targets"],dtype=torch.int32))[rows].to(device)
          q_mask=shard.get("action_value_mask",torch.zeros_like(shard["mask"]))[rows].to(device)&m&(q_visits>0)
          value_valid=shard.get("value_valid",torch.ones(shard["count"],dtype=torch.bool))[rows].to(device)
          # Score the actual auxiliary action-value head. Calling the regular
          # two-head forward path here and substituting zeros silently made
          # every reported action-Q MAE/RMSE a target-magnitude statistic,
          # not an evaluation of the checkpoint.
          logits,val,q_pred=model.forward_with_action_values(s,a,m)
          opponent_states=shard.get("opponent_value_states")
          opponent_valid=shard.get("opponent_value_valid")
          if opponent_states is not None and opponent_valid is not None:
            os=opponent_states[rows].to(device)
            ov=opponent_valid[rows].to(device)&value_valid
            if bool(ov.any()):
              ov_pred=model.value_head(model._encode_state(os)).squeeze(-1)
              ov_target=-y
              ov_error=ov_pred[ov]-ov_target[ov]
              stat["opponent_value_records"]+=int(ov.sum())
              stat["opponent_abs"]+=float(ov_error.abs().sum())
              stat["opponent_sq"]+=float(ov_error.square().sum())
              stat["opponent_sign_correct"]+=int(((ov_pred[ov]>=0)==(ov_target[ov]>=0)).sum())
          logp=F.log_softmax(logits,1); nt=m.sum(1)>1
          if bool(q_mask.any()):
            q_error=(q_pred-q_target)[q_mask]
            q_w=q_visits[q_mask].float().sqrt()
            stat["q_records"]+=int(q_mask.sum())
            stat["q_abs"]+=float(q_error.abs().sum())
            stat["q_sq"]+=float(q_error.square().sum())
            stat["q_weighted_abs"]+=float((q_error.abs()*q_w).sum())
            stat["q_weight_sum"]+=float(q_w.sum())
          stat["records"]+=len(rows); stat["policy_decisions"]+=int(nt.sum()); stat["correct"]+=int(((logits.argmax(1)==chosen)&nt).sum())
          stat["value_records"]+=int(value_valid.sum())
          stat["abs"]+=float((val[value_valid]-y[value_valid]).abs().sum()); stat["sq"]+=float(((val[value_valid]-y[value_valid])**2).sum())
          stat["target_sq"]+=float((y[value_valid]**2).sum()); stat["target_sum"]+=float(y[value_valid].sum())
          stat["value_sign_correct"]+=int(((val[value_valid] >= 0) == (y[value_valid] >= 0)).sum())
          # State feature 0 is min(game.turn, 100) / 100 (hsa.encoding).
          turns=(s[:,0]*100.0).round().long()
          for name,turn_mask in (("turn_1_3",(turns>=1)&(turns<=3)),
                                 ("turn_4_6",(turns>=4)&(turns<=6)),
                                 ("turn_7_plus",turns>=7)):
            valid=value_valid&turn_mask
            if bool(valid.any()):
              err=val[valid]-y[valid]
              turn_stat[name]["n"]+=int(valid.sum())
              turn_stat[name]["abs"]+=float(err.abs().sum())
              turn_stat[name]["sq"]+=float(err.square().sum())
              turn_stat[name]["target_sq"]+=float(y[valid].square().sum())
              turn_stat[name]["sign"]+=int(((val[valid]>=0)==(y[valid]>=0)).sum())
          stat["ce"]+=float((-(target*logp).sum(1))[nt].sum())
          tlog=torch.where(target>0,torch.log(target.clamp_min(1e-12)),torch.zeros_like(target))
          stat["entropy"]+=float((-(target*tlog).sum(1))[nt].sum())
    n=max(1,stat["value_records"]); q=max(1,stat["policy_decisions"])
    result={"checkpoint":str(args.checkpoint),"checkpoint_migration":migration,"records":stat["records"],"value_records":stat["value_records"],"policy_decisions":stat["policy_decisions"],"policy_accuracy":stat["correct"]/q,"policy_cross_entropy":stat["ce"]/q,"policy_kl":max(0.,(stat["ce"]-stat["entropy"])/q),"value_mae":stat["abs"]/n,"value_mse":stat["sq"]/n,"value_brier":stat["sq"]/n/4,"value_sign_accuracy":stat["value_sign_correct"]/n,"target_mean":stat["target_sum"]/n,"neutral_value_mse":stat["target_sq"]/n,"neutral_value_brier":stat["target_sq"]/n/4,"action_q_records":stat["q_records"],"action_q_mae":stat["q_abs"]/max(1,stat["q_records"]),"action_q_rmse":(stat["q_sq"]/max(1,stat["q_records"]))**.5,"action_q_visit_weighted_mae":stat["q_weighted_abs"]/max(1e-12,stat["q_weight_sum"]),"split":{"mod":args.validation_mod,"remainder":args.validation_rem}}
    result["root_perspective_value_trained"] = bool(
        ckpt.get("report", {}).get("root_perspective_value_trained", False)
    )
    result["opponent_view_value"]={"records":stat["opponent_value_records"],"mae":stat["opponent_abs"]/max(1,stat["opponent_value_records"]),"brier":stat["opponent_sq"]/max(1,stat["opponent_value_records"])/4,"sign_accuracy":stat["opponent_sign_correct"]/max(1,stat["opponent_value_records"])}
    result["value_by_turn"]={name:{"records":v["n"],"mae":v["abs"]/max(1,v["n"]),"brier":v["sq"]/max(1,v["n"])/4,"sign_accuracy":v["sign"]/max(1,v["n"]),"neutral_brier":v["target_sq"]/max(1,v["n"])/4} for name,v in turn_stat.items()}
    print(json.dumps(result,indent=2))
if __name__=="__main__": main()

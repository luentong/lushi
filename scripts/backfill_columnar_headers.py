from pathlib import Path
import torch

src = Path(__file__).resolve().parents[1] / "reports/standard_multideck_20260921_retry6/pt_shards"
dst = Path(__file__).resolve().parents[1] / "reports/standard_multideck_20260921_retry6/columnar"
for out in sorted(dst.glob("*.pt")):
    if out.name.endswith(".tmp.pt"):
        continue
    if "header" in torch.load(out, map_location="cpu", weights_only=False):
        continue
    packed = src / out.name
    payload = torch.load(out, map_location="cpu", weights_only=False)
    original = torch.load(packed, map_location="cpu", weights_only=False)
    payload["header"] = original.get("header", {})
    tmp = out.with_suffix(".tmp.pt")
    torch.save(payload, tmp)
    tmp.replace(out)
    print(out.name, flush=True)

"""Retry missing matchup shards from a multideck manifest with bounded jobs."""
from __future__ import annotations

import json
import gzip
import subprocess
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    manifest_path = root / "reports/standard40_teacher_20260923_v2/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    missing = [
        job for job in manifest["jobs"]
        if not (root / job["output"]).is_file()
    ]
    print(f"missing={len(missing)}", flush=True)
    for job in missing:
        command = list(job["command"])
        # The original command's --workers=4 amplified pathological games.
        command[command.index("--workers") + 1] = "1"
        command[command.index("--games") + 1] = "1"
        command[command.index("--max-actions") + 1] = "200"
        output = root / job["output"]
        output.unlink(missing_ok=True)
        print(f"retry {job['deck_a']} vs {job['deck_b']}", flush=True)
        try:
            subprocess.run(command, cwd=root, check=True, timeout=150)
        except Exception as exc:
            print(f"failed {job['deck_a']} vs {job['deck_b']}: {exc}", flush=True)
            output.unlink(missing_ok=True)
        else:
            job["status"] = "complete"
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

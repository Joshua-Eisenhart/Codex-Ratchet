#!/usr/bin/env python3
"""Run claimgate.py over every system_v8 receipt.json and write a summary."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAIMGATE = Path(__file__).resolve().parent / "claimgate.py"
OUT = Path(__file__).resolve().parent / "results" / "first_sweep.json"


def main():
    receipts = sorted((ROOT / "system_v8").rglob("receipt.json"))
    results = []
    admit = 0
    reject = 0
    for r in receipts:
        rel = str(r.relative_to(ROOT))
        proc = subprocess.run(
            [sys.executable, str(CLAIMGATE), str(r)],
            capture_output=True, text=True,
        )
        if proc.returncode == 0:
            admit += 1
            results.append({"path": rel, "verdict": "admit", "reasons": []})
        else:
            reject += 1
            try:
                payload = json.loads(proc.stdout)
                reasons = payload.get("reasons", [])
            except Exception:
                reasons = [{"code": "claimgate_error", "detail": proc.stdout + proc.stderr}]
            results.append({"path": rel, "verdict": "reject", "reasons": reasons})

    summary = {
        "total": len(receipts),
        "admit": admit,
        "reject": reject,
        "results": results,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, indent=2))
    print(f"total={len(receipts)} admit={admit} reject={reject}")
    print(f"written to {OUT}")


if __name__ == "__main__":
    main()

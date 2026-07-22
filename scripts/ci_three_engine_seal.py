#!/usr/bin/env python3
"""CI enforcement — run the three-engine seal (metadata-only) over EVERY ratcheting
receipt. Fails (exit 1) if ANY receipt contains numpy or lacks >=2 agreeing
authoritative engines. This runs on GitHub CI (no sim env needed for the numpy /
engine-count / agreement checks), so a numpy sim cannot pass un-noticed regardless
of what any commit message claims. The jax re-derive is done locally by the
pre-commit hook + Stop hook; CI catches the numpy bullshit un-bypassably.
"""
import glob
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEAL = os.path.join(REPO, "claimgate_plugin", "three_engine_seal.py")
GLOBS = [
    "ratchet_contract/ratchetings/results/*.json",
    "system_v8/*/results/*.json",
]


def main():
    receipts = []
    for g in GLOBS:
        receipts += glob.glob(os.path.join(REPO, g))
    receipts = sorted(r for r in receipts if not r.endswith("_nvidia_referee.json"))
    env = dict(os.environ, SEAL_METADATA_ONLY="1")
    failures = []
    checked = 0
    for r in receipts:
        proc = subprocess.run([sys.executable, SEAL, r], capture_output=True, text=True, env=env)
        line = (proc.stderr or proc.stdout).strip().splitlines()[-1] if (proc.stderr or proc.stdout).strip() else ""
        rel = os.path.relpath(r, REPO)
        if proc.returncode == 1:
            failures.append((rel, line))
        elif proc.returncode == 0:
            checked += 1
        # exit 2 (usage) is not a contract verdict — ignore
    print(f"three-engine CI seal: {checked} receipt(s) pass, {len(failures)} REJECTED", file=sys.stderr)
    for rel, line in failures:
        print(f"  FAIL {rel}: {line}", file=sys.stderr)
    if failures:
        print("\nCI FAILED — the above receipts contain numpy or lack real engine evidence. "
              "Rework them numpy-free (jax base + Julia authoritative) or declare exemption.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

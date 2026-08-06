#!/usr/bin/env python3
"""CI enforcement — run the three-engine seal (metadata-only) over EVERY ratcheting
receipt. Fails (exit 1) if ANY receipt labels numpy load_bearing or lacks >=2 agreeing
authoritative engines.

NUMPY IS CONTAINED, NOT BANNED (owner, 2026-07-22). This docstring used to read
"fails if ANY receipt CONTAINS numpy", which was never what the seal it delegates to
enforced and is not the rule now. numpy in a downstream-satellite role — consuming
what an authoritative engine produced, computing no observable of its own — is
ALLOWED. numpy labelled load_bearing is REJECTED by three_engine_seal.py R1, and a
numeric receipt must still show >=2 authoritative engines agreeing on the same metric
ID, which is what stops numpy being the workhorse in disguise. Proven in both
directions by claimgate_plugin/run_numpy_containment_regression.py.

This runs on GitHub CI (no sim env needed for the label / engine-count / agreement
checks), so a receipt that promotes numpy cannot pass un-noticed regardless of what
any commit message claims. The jax re-derive is done locally by the pre-commit hook
+ Stop hook.
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
        print("\nCI FAILED — the above receipts promote numpy to load_bearing or lack real "
              "engine evidence. The fix is NOT to strip numpy: keep it in its contained "
              "downstream-satellite role and move the load-bearing work onto authoritative "
              "engines (jax base + Julia/PyTorch authoritative), or declare exemption.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

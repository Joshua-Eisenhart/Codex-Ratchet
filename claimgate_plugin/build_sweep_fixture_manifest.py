#!/usr/bin/env python3
"""Build claimgate_plugin/fixtures/sweep_fixture_manifest.json — the digest-pinned
registry of poison-by-design regression inputs.

WHY. ci_receipt_sweep.py used to skip anything under a fixture path PREFIX. That
was the cheapest bypass in the enforcement layer and required no edit to any
checker: park a poisoned real receipt under claimgate_plugin/fixtures/ and it was
never swept. A prefix cannot tell "poison we wrote on purpose" from "poison
someone left here". A digest can.

Each entry pins: path, sha256, and the exit code each lean-tier checker returns.
The sweep then RUNS these fixtures and asserts the recorded exit, so they are
regression inputs rather than blind spots.

THIS IS A CONSCIOUS BASELINE, and re-running it is a re-baseline, not a fix. If a
checker later returns a different exit for a pinned fixture, the sweep fails and
the answer is to fix the CHECKER. Re-pinning to whatever it now returns erases
the finding — the same mistake as raising a ratchet ceiling to make CI green.

Usage:  python3 claimgate_plugin/build_sweep_fixture_manifest.py [--write]
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "claimgate_plugin" / "fixtures" / "sweep_fixture_manifest.json"
FIXTURE_ROOTS = ("claimgate_plugin/fixtures", "claimgate_plugin/rf_fixtures",
                 "system_v8/harness_patch/results/fixtures", "claimgate_plugin/stress")
CHECKERS = ("intake_supervisor", "recompute_veto")
SKIP_PARTS = {".git", "__pycache__", "node_modules"}


def run_checker(mod: str, target: Path) -> int:
    """Same isolated-module trampoline ci_receipt_sweep uses, so the recorded exit
    is the exit the sweep will actually observe."""
    code = ("import sys, runpy\n"
            f"sys.path.append({str(REPO)!r})\n"
            f"sys.argv = ['{mod}.py', sys.argv[1]]\n"
            f"runpy.run_module('claimgate_plugin.{mod}', run_name='__main__', alter_sys=False)\n")
    return subprocess.run([sys.executable, "-I", "-c", code, str(target)],
                          capture_output=True, text=True, cwd=str(REPO)).returncode


def claim_bearing(path: Path) -> bool:
    try:
        raw = path.read_bytes()
    except OSError:
        return False
    low = raw.lower()
    if ("receipt" in path.name.lower() or b'"claim_under_test"' in low
            or b'"claim_ceiling"' in low or (b'"schema"' in low and b"receipt" in low)):
        return True
    try:
        obj = json.loads(raw)
    except Exception:  # noqa: BLE001
        # Match ci_receipt_sweep.claim_bearing: unparseable JSON is claim-bearing,
        # so a deliberately malformed fixture gets PINNED rather than left
        # permanently unpinned and permanently failing the sweep.
        return True
    return isinstance(obj, dict) and "classification" in obj


def main(argv):
    write = "--write" in argv
    entries = []
    for root in FIXTURE_ROOTS:
        base = REPO / root
        if not base.exists():
            continue
        for p in sorted(base.rglob("*.json")):
            if not p.is_file() or SKIP_PARTS & set(p.parts):
                continue
            if not claim_bearing(p):
                continue
            rel = p.relative_to(REPO).as_posix()
            exits = {c: run_checker(c, p) for c in CHECKERS}
            entries.append({
                "path": rel,
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                "expect_exit": exits,
            })
    doc = {
        "_what": "Poison-by-design regression inputs, pinned by DIGEST and by the exit "
                 "each lean-tier checker must return. Replaces the path-prefix exclusion "
                 "list, which let anyone hide a poisoned receipt by parking it under a "
                 "fixture directory.",
        "_rule": "If the sweep reports a mismatch, FIX THE CHECKER. Re-running this "
                 "generator re-pins to current behaviour and erases the finding — the same "
                 "mistake as raising a ratchet ceiling to make CI green.",
        "_baseline_note": "Exits below are MEASURED, not aspirational. Some are 0 because "
                          "the checker genuinely has nothing to say about that fixture (a "
                          "control receipt, or poison outside that checker's remit). A 0 "
                          "here is a recorded fact about today, not an endorsement.",
        "_regenerate": "python3 claimgate_plugin/build_sweep_fixture_manifest.py --write",
        "_checkers": list(CHECKERS),
        "fixtures": entries,
    }
    dist = {}
    for e in entries:
        for c, code in e["expect_exit"].items():
            dist[f"{c}={code}"] = dist.get(f"{c}={code}", 0) + 1
    print(f"pinned {len(entries)} claim-bearing fixture(s) under {len(FIXTURE_ROOTS)} roots")
    for k in sorted(dist):
        print(f"  {k}: {dist[k]}")
    if write:
        OUT.write_text(json.dumps(doc, indent=1) + "\n")
        print(f"wrote {OUT.relative_to(REPO)}")
    else:
        print("(dry run — pass --write to emit)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

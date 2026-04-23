#!/usr/bin/env python3
"""Seed Lane A (capability probes) and Lane B (classical baselines).

Lane B: files under system_v4/probes with classification="classical_baseline"
        (excludes runners like classical_sweep_runner.py).
Lane A: system_v4/probes/sim_*_capability.py (12 tool-capability probes).
"""
from __future__ import annotations

import re
from pathlib import Path

from queue_claim import ROOT, enqueue, counts

PROBES = ROOT / "system_v4" / "probes"
CLASSICAL_PAT = re.compile(r"""classification\s*=\s*["']classical_baseline["']""")


def lane_b_sims() -> list[Path]:
    hits = []
    for p in sorted(PROBES.glob("sim_*_classical*.py")):
        try:
            text = p.read_text(errors="ignore")
        except OSError:
            continue
        if CLASSICAL_PAT.search(text):
            hits.append(p)
    # also include non-"sim_" classical-tagged files missed by prefix?
    for p in sorted(PROBES.glob("*_classical*.py")):
        if p in hits:
            continue
        if p.name.startswith("sim_"):
            continue
        # skip runners / non-sim utilities
        if "runner" in p.name or "report" in p.name:
            continue
        text = p.read_text(errors="ignore")
        if CLASSICAL_PAT.search(text):
            hits.append(p)
    return hits


def lane_a_sims() -> list[Path]:
    return sorted(PROBES.glob("sim_*_capability.py"))


def main() -> None:
    b = lane_b_sims()
    a = lane_a_sims()
    print(f"Lane B candidates: {len(b)}")
    print(f"Lane A candidates: {len(a)}")
    for p in b:
        enqueue("lane_B", str(p))
    for p in a:
        enqueue("lane_A", str(p))
    print("counts:", counts())


if __name__ == "__main__":
    main()

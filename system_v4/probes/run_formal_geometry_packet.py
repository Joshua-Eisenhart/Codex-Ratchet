#!/usr/bin/env python3
"""
run_formal_geometry_packet.py
============================

Refresh the formal geometry witness packet from existing executable probes.

Scope:
  - exact Hopf / connection geometry truth
  - Weyl ambient rung
  - ambient-vs-engine overlay separation
  - live engine-family chirality split
  - dual Weyl cycle stability
  - torus-structure negative control
  - no-chirality negative control

This runner intentionally does not invoke sidecar scripts that write markdown.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RESULTS_PATH = ROOT / "a2_state" / "sim_results" / "formal_geometry_packet_run_results.json"
SPEC_GRAPH_PYTHON = ROOT.parent.parent / ".venv_spec_graph" / "bin" / "python3"


def choose_python(require_spec_graph: bool) -> str:
    if require_spec_graph and SPEC_GRAPH_PYTHON.exists():
        return str(SPEC_GRAPH_PYTHON)
    return sys.executable


def run_step(label: str, script_name: str, require_spec_graph: bool = False) -> dict:
    script_path = ROOT / script_name
    python_bin = choose_python(require_spec_graph=require_spec_graph)
    cmd = [python_bin, str(script_path)]
    started = time.time()
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    elapsed = time.time() - started
    return {
        "label": label,
        "script": str(script_path),
        "python": python_bin,
        "returncode": int(proc.returncode),
        "elapsed_sec": float(elapsed),
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
        "ok": proc.returncode == 0,
    }


def main() -> int:
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)

    steps = [
        ("geometry_truth", "sim_geometry_truth.py", True),
        ("weyl_geometry_ladder", "sim_weyl_geometry_ladder_audit.py", False),
        ("weyl_ambient_overlay", "sim_weyl_ambient_vs_engine_overlay.py", False),
        ("engine_chirality", "sim_L4_engine_chirality.py", False),
        ("dual_weyl_cycle", "dual_weyl_spinor_engine_sim.py", False),
        ("neg_torus_scrambled", "sim_neg_torus_scrambled.py", False),
        ("neg_no_chirality", "sim_neg_no_chirality.py", False),
        ("neg_loop_law_swap", "sim_neg_loop_law_swap.py", False),
    ]

    step_results = [run_step(label, script_name, require_spec_graph) for label, script_name, require_spec_graph in steps]
    all_ok = all(step["ok"] for step in step_results)

    payload = {
        "name": "formal_geometry_packet_run",
        "timestamp": datetime.now(UTC).isoformat(),
        "all_ok": all_ok,
        "steps": step_results,
    }

    with open(RESULTS_PATH, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)

    print("=" * 72)
    print("FORMAL GEOMETRY PACKET RUN")
    print("=" * 72)
    for step in step_results:
        status = "PASS" if step["ok"] else "FAIL"
        print(f"{status:>4}  {step['label']:<24} rc={step['returncode']}  t={step['elapsed_sec']:.2f}s")
    print(f"\nrun_results: {RESULTS_PATH}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

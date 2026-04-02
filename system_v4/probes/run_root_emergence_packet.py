#!/usr/bin/env python3
"""
run_root_emergence_packet.py
===========================

Refresh the executable root-emergence witness packet from the current lower
layer probes.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RESULTS_PATH = ROOT / "a2_state" / "sim_results" / "root_emergence_packet_run_results.json"
SPEC_GRAPH_PYTHON = ROOT.parent.parent / ".venv_spec_graph" / "bin" / "python3"


def choose_python(require_spec_graph: bool) -> str:
    if require_spec_graph and SPEC_GRAPH_PYTHON.exists():
        return str(SPEC_GRAPH_PYTHON)
    return sys.executable


def run_step(label: str, script_name: str, require_spec_graph: bool = False, extra_args: list[str] | None = None) -> dict:
    script_path = ROOT / script_name
    python_bin = choose_python(require_spec_graph=require_spec_graph)
    cmd = [python_bin, str(script_path), *(extra_args or [])]
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
        ("nonclassical_guard", "sim_nonclassical_guard_probe.py", False, []),
        ("ec3_identity", "sim_ec3_identity_principle.py", False, []),
        ("missing_axis_search", "sim_missing_axis_search.py", False, []),
        ("bridge_search", "sim_axis0_bridge_search.py", False, []),
        ("carrier_rank", "sim_root_constraint_carrier_rank.py", False, []),
        ("history_mispair_counterfeit", "sim_history_mispair_counterfeit.py", False, []),
        ("coarising_stress", "sim_axis0_coarising_stress_test.py", False, []),
        ("orbit_phase_alignment", "sim_axis0_orbit_phase_alignment.py", True, ["--packet-witness"]),
        ("attractor_basin_boundary", "sim_axis0_attractor_basin_boundary.py", False, []),
    ]
    step_results = [
        run_step(label, script_name, require_spec_graph, extra_args)
        for label, script_name, require_spec_graph, extra_args in steps
    ]
    all_ok = all(step["ok"] for step in step_results)

    payload = {
        "name": "root_emergence_packet_run",
        "timestamp": datetime.now(UTC).isoformat(),
        "all_ok": all_ok,
        "steps": step_results,
    }
    RESULTS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("=" * 72)
    print("ROOT EMERGENCE PACKET RUN")
    print("=" * 72)
    for step in step_results:
        status = "PASS" if step["ok"] else "FAIL"
        print(f"{status:>4}  {step['label']:<24} rc={step['returncode']}  t={step['elapsed_sec']:.2f}s")
    print(f"\nrun_results: {RESULTS_PATH}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
run_entropy_readout_packet.py
=============================

Refresh the executable entropy-readout packet from the current live probes.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RESULTS_PATH = ROOT / "a2_state" / "sim_results" / "entropy_readout_packet_run_results.json"


def run_step(label: str, script_name: str) -> dict:
    script_path = ROOT / script_name
    cmd = [sys.executable, str(script_path)]
    started = time.time()
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    elapsed = time.time() - started
    return {
        "label": label,
        "script": str(script_path),
        "returncode": int(proc.returncode),
        "elapsed_sec": float(elapsed),
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
        "ok": proc.returncode == 0,
    }


def main() -> int:
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    steps = [
        ("entropy_negative_battery", "entropy_form_negative_battery.py"),
        ("axis0_full_spectrum", "axis0_full_spectrum_sim.py"),
        ("axis0_fep_compression", "sim_axis0_fep_compression_framing.py"),
    ]
    step_results = [run_step(label, script_name) for label, script_name in steps]
    all_ok = all(step["ok"] for step in step_results)

    payload = {
        "name": "entropy_readout_packet_run",
        "timestamp": datetime.now(UTC).isoformat(),
        "all_ok": all_ok,
        "steps": step_results,
    }
    RESULTS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("=" * 72)
    print("ENTROPY READOUT PACKET RUN")
    print("=" * 72)
    for step in step_results:
        status = "PASS" if step["ok"] else "FAIL"
        print(f"{status:>4}  {step['label']:<28} rc={step['returncode']}  t={step['elapsed_sec']:.2f}s")
    print(f"\nrun_results: {RESULTS_PATH}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

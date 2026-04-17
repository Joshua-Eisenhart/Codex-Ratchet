#!/usr/bin/env python3
"""
run_axis0_stack_packet.py
=========================

Refresh the full executable Axis 0 ladder by running each packet runner.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from axis0_constraint_types import build_constraint_family_profile
from axis0_xi_law_fingerprint import runner_law_fingerprints_consistent


ROOT = Path(__file__).resolve().parent
RESULTS_PATH = ROOT / "a2_state" / "sim_results" / "axis0_stack_packet_run_results.json"


def _mean_profile(*profiles: dict[str, float]) -> dict[str, float]:
    keys = (
        "observational",
        "admissible",
        "stable",
        "entropy_conditioned",
        "topology_conditioned",
    )
    present = [profile for profile in profiles if profile]
    if not present:
        return build_constraint_family_profile()
    return build_constraint_family_profile(
        **{
            key: sum(float(profile.get(key, 0.0)) for profile in present) / len(present)
            for key in keys
        }
    )


def _load_constraint_profile_results(results_dir: Path) -> dict[str, dict[str, float]]:
    constraint_profile_paths = {
        "formal_geometry": "formal_geometry_packet_validation.json",
        "root_emergence": "root_emergence_packet_validation.json",
        "carrier_selection": "carrier_selection_packet_validation.json",
        "pre_entropy": "pre_entropy_packet_validation.json",
        "c1_bridge_object": "c1_bridge_object_packet_validation.json",
        "matched_marginal": "matched_marginal_packet_validation.json",
        "entropy_readout": "entropy_readout_packet_validation.json",
    }
    constraint_profile_results = {}
    for label, result_name in constraint_profile_paths.items():
        path = results_dir / result_name
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        profile = payload.get("constraint_family_profile")
        if profile:
            constraint_profile_results[label] = profile
    return constraint_profile_results


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
        ("formal_geometry", "run_formal_geometry_packet.py"),
        ("root_emergence", "run_root_emergence_packet.py"),
        ("carrier_selection", "run_carrier_selection_packet.py"),
        ("pre_entropy", "run_pre_entropy_packet.py"),
        ("c1_bridge_object", "validate_c1_bridge_object_packet.py"),
        ("matched_marginal", "run_matched_marginal_packet.py"),
        ("entropy_readout", "run_entropy_readout_packet.py"),
    ]
    step_results = [run_step(label, script_name) for label, script_name in steps]
    all_ok = all(step["ok"] for step in step_results)
    constraint_profile_results = _load_constraint_profile_results(RESULTS_PATH.parent)
    xi_hist_law_fingerprints = {}
    for label, result_name in (
        ("carrier_selection", "carrier_selection_packet_run_results.json"),
        ("pre_entropy", "pre_entropy_packet_run_results.json"),
    ):
        path = RESULTS_PATH.parent / result_name
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        fingerprint = payload.get("xi_hist_strict_law_fingerprint")
        if fingerprint is not None:
            xi_hist_law_fingerprints[label] = fingerprint

    payload = {
        "name": "axis0_stack_packet_run",
        "timestamp": datetime.now(UTC).isoformat(),
        "all_ok": all_ok,
        "steps": step_results,
        "xi_hist_law_fingerprints": xi_hist_law_fingerprints,
        "constraint_family_profiles": constraint_profile_results,
        "constraint_family_profile": _mean_profile(*constraint_profile_results.values()),
        "xi_hist_law_fingerprints_consistent": runner_law_fingerprints_consistent(
            {"xi_hist_law_fingerprints": xi_hist_law_fingerprints}
        ) if xi_hist_law_fingerprints else False,
    }
    RESULTS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("=" * 72)
    print("AXIS0 STACK PACKET RUN")
    print("=" * 72)
    for step in step_results:
        status = "PASS" if step["ok"] else "FAIL"
        print(f"{status:>4}  {step['label']:<20} rc={step['returncode']}  t={step['elapsed_sec']:.2f}s")
    print(f"\nrun_results: {RESULTS_PATH}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

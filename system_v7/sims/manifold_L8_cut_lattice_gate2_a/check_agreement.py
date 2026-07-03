#!/usr/bin/env python3
"""Agreement checker for manifold_L8_cut_lattice_gate2_a.

This is an adjudicator only: it reads the NumPy and Julia receipts and checks
that the independently computed L8 invariants agree within 1e-9.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "load-bearing readback of NumPy and Julia receipts and agreement result emission"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source/result digesting"},
}
TOOL_INTEGRATION_DEPTH = {"json": "load_bearing", "hashlib": "supportive"}

SIM_ID = "manifold_L8_cut_lattice_gate2_a"
HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
PARITY_ABS_TOL = 1e-9


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def scalar_diff(a: float, b: float) -> float:
    return abs(float(a) - float(b))


def main() -> int:
    numpy_path = RESULTS / f"{SIM_ID}_numpy_results.json"
    julia_path = RESULTS / f"{SIM_ID}_julia_results.json"
    numpy_result = load_json(numpy_path)
    julia_result = load_json(julia_path)
    failures: list[str] = []

    for name, row in (("numpy", numpy_result), ("julia", julia_result)):
        if row.get("reads_peer_result") is not False:
            failures.append(f"{name}: reads_peer_result is not false")
        if row.get("classification") != "scratch_diagnostic":
            failures.append(f"{name}: classification drifted")
        if row.get("promotion_allowed") is not False or row.get("formal_admission_allowed") is not False:
            failures.append(f"{name}: promotion/formal admission fence drifted")
        if row.get("all_pass") is not True:
            failures.append(f"{name}: all_pass is not true")

    comparable_count_keys = [
        "finite_gate1_roster_states",
        "gate1_full_quotient_classes_consumed",
        "full_recomputed_quotient_classes",
        "coarse_z_recomputed_quotient_classes",
        "cut_count_unordered_bipartitions",
        "nonempty_subset_lattice_nodes",
        "per_cut_side_marginal_records",
        "compatibility_checks",
    ]
    count_deltas = {}
    for key in comparable_count_keys:
        left = int(numpy_result["enumeration_counts"][key])
        right = int(julia_result["enumeration_counts"][key])
        count_deltas[key] = abs(left - right)
        if left != right:
            failures.append(f"count mismatch {key}: numpy={left} julia={right}")

    cut_deltas = []
    for ncut, jcut in zip(numpy_result["cuts"], julia_result["cuts"], strict=True):
        if ncut["cut_id"] != jcut["cut_id"]:
            failures.append(f"cut id mismatch: {ncut['cut_id']} vs {jcut['cut_id']}")
            continue
        for key in ("left_stratum_count", "right_stratum_count"):
            if int(ncut[key]) != int(jcut[key]):
                failures.append(f"{ncut['cut_id']} {key} mismatch: numpy={ncut[key]} julia={jcut[key]}")
        for key in ("negativity_min", "negativity_max"):
            delta = scalar_diff(ncut[key], jcut[key])
            cut_deltas.append(delta)
            if delta > PARITY_ABS_TOL:
                failures.append(f"{ncut['cut_id']} {key} delta {delta} exceeds {PARITY_ABS_TOL}")

    control_deltas = []
    n_controls = numpy_result["negative_controls"]
    j_controls = julia_result["negative_controls"]
    shared_controls = sorted(set(n_controls) & set(j_controls))
    for key in shared_controls:
        if n_controls[key].get("pass") != j_controls[key].get("pass"):
            failures.append(f"control verdict mismatch: {key}")
    if "entangled_finite_roster_nonzero_negativity" in shared_controls:
        delta = scalar_diff(
            n_controls["entangled_finite_roster_nonzero_negativity"]["negativity"],
            j_controls["entangled_finite_roster_nonzero_negativity"]["negativity"],
        )
        control_deltas.append(delta)
        if delta > PARITY_ABS_TOL:
            failures.append(f"entangled roster negativity delta {delta} exceeds {PARITY_ABS_TOL}")

    parity_max_abs_diff = max([0.0] + [float(v) for v in count_deltas.values()] + cut_deltas + control_deltas)
    parity_pass = not failures and parity_max_abs_diff <= PARITY_ABS_TOL
    report = {
        "schema": "codex_ratchet.manifold_L8_cut_lattice_gate2_a.agreement.v1",
        "sim_id": SIM_ID,
        "engine": "agreement_controller",
        "source_path": str(Path(__file__).resolve()),
        "source_sha256": sha256_file(Path(__file__)),
        "written_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "QUARANTINE_EXPLORATORY": True,
        "scratch_diagnostic": True,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "inputs": {
            "numpy_result_path": str(numpy_path),
            "numpy_result_sha256": sha256_file(numpy_path),
            "julia_result_path": str(julia_path),
            "julia_result_sha256": sha256_file(julia_path),
        },
        "parity_abs_tol": PARITY_ABS_TOL,
        "parity_max_abs_diff": parity_max_abs_diff,
        "parity_pass": parity_pass,
        "count_deltas": count_deltas,
        "cut_numeric_deltas": cut_deltas,
        "control_numeric_deltas": control_deltas,
        "all_pass": parity_pass,
        "failures": failures,
        "summary": {
            "cut_formula": numpy_result["cut_count_resolution"]["chosen_formula"],
            "cut_count": numpy_result["enumeration_counts"]["cut_count_unordered_bipartitions"],
            "finite_roster_states": numpy_result["enumeration_counts"]["finite_gate1_roster_states"],
            "full_quotient_classes": numpy_result["enumeration_counts"]["full_recomputed_quotient_classes"],
            "coarse_z_quotient_classes": numpy_result["enumeration_counts"]["coarse_z_recomputed_quotient_classes"],
            "compatibility_checks": numpy_result["enumeration_counts"]["compatibility_checks"],
            "per_cut_side_marginal_records": numpy_result["enumeration_counts"]["per_cut_side_marginal_records"],
        },
    }
    out = RESULTS / f"{SIM_ID}_agreement_results.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "sim_id": SIM_ID,
        "all_pass": report["all_pass"],
        "parity_pass": parity_pass,
        "parity_max_abs_diff": parity_max_abs_diff,
        "failures": failures,
        "result_path": str(out),
    }, indent=2))
    return 0 if parity_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

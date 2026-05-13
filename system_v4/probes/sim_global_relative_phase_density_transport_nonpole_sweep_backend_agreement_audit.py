#!/usr/bin/env python3
"""Audit QuTiP/Qiskit agreement on non-pole global-vs-relative phase sweeps."""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

from receipt_boundary import apply_default_receipt_boundary


NAME = "global_relative_phase_density_transport_nonpole_sweep_backend_agreement_audit"
CLASSIFICATION = "audit"
classification = CLASSIFICATION

PROBE_DIR = pathlib.Path(__file__).resolve().parent
ROOT = PROBE_DIR.parents[1]
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
QUTIP_RESULT = RESULT_DIR / "qutip_global_relative_phase_density_transport_nonpole_sweep_results.json"
QISKIT_RESULT = RESULT_DIR / "qiskit_global_relative_phase_density_transport_nonpole_sweep_results.json"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

TOOL_MANIFEST = {
    "qutip": {
        "tried": False,
        "used": False,
        "reason": "not executed here; this audit reads the prior QuTiP non-pole sweep receipt",
    },
    "qiskit": {
        "tried": False,
        "used": False,
        "reason": "not executed here; this audit reads the prior Qiskit non-pole sweep receipt",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "loads existing sweep receipts and compares recorded sweep and graveyard metrics",
    },
}
TOOL_INTEGRATION_DEPTH = {"qutip": None, "qiskit": None, "python_json": "supportive"}

CLAIM_CEILING = (
    "backend-agreement audit only: compares existing QuTiP and Qiskit non-pole global-phase density-invariance "
    "and relative-phase density-transport sweep receipts; no fresh backend execution, no full Hopf bundle, no "
    "physical loop independence, no flux, no QIT, GStack, axis, bridge, engine, target-system, or nonclassical "
    "admission"
)


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def nearly_equal(left: float, right: float, *, tolerance: float = 1e-9) -> bool:
    return math.isclose(left, right, abs_tol=tolerance, rel_tol=tolerance)


def sweep_rows(qutip_data: dict[str, Any], qiskit_data: dict[str, Any]) -> list[dict[str, Any]]:
    qutip_rows = qutip_data["positive"]["sweep"]
    qiskit_rows = qiskit_data["positive"]["sweep"]
    rows: list[dict[str, Any]] = []
    for index, (qutip_row, qiskit_row) in enumerate(zip(qutip_rows, qiskit_rows)):
        metric_pairs = [
            ("global_density_displacement", qutip_row["global_phase_transport"]["density_displacement_from_start"], qiskit_row["global_phase_transport"]["density_displacement_from_start"]),
            ("global_bloch_path_length", qutip_row["global_phase_transport"]["bloch_path_length"], qiskit_row["global_phase_transport"]["bloch_path_length"]),
            ("relative_density_displacement", qutip_row["relative_phase_transport"]["density_displacement_from_start"], qiskit_row["relative_phase_transport"]["density_displacement_from_start"]),
            ("relative_bloch_displacement", qutip_row["relative_phase_transport"]["bloch_displacement_from_start"], qiskit_row["relative_phase_transport"]["bloch_displacement_from_start"]),
            ("relative_bloch_path_length", qutip_row["relative_phase_transport"]["bloch_path_length"], qiskit_row["relative_phase_transport"]["bloch_path_length"]),
            ("relative_purity_min", qutip_row["relative_phase_transport"]["purity_min"], qiskit_row["relative_phase_transport"]["purity_min"]),
            ("relative_trace_min", qutip_row["relative_phase_transport"]["trace_min"], qiskit_row["relative_phase_transport"]["trace_min"]),
        ]
        metric_agreement = [
            {
                "metric": metric,
                "qutip_value": float(qutip_value),
                "qiskit_value": float(qiskit_value),
                "absolute_delta": abs(float(qutip_value) - float(qiskit_value)),
                "passed": nearly_equal(float(qutip_value), float(qiskit_value)),
            }
            for metric, qutip_value, qiskit_value in metric_pairs
        ]
        rows.append(
            {
                "case_index": index,
                "theta": float(qutip_row["theta"]),
                "sample_count": int(qutip_row["sample_count"]),
                "same_case": bool(
                    nearly_equal(float(qutip_row["theta"]), float(qiskit_row["theta"]))
                    and int(qutip_row["sample_count"]) == int(qiskit_row["sample_count"])
                ),
                "qutip_passed": bool(qutip_row["passed"]),
                "qiskit_passed": bool(qiskit_row["passed"]),
                "metric_agreement": metric_agreement,
                "passed": bool(
                    qutip_row["passed"]
                    and qiskit_row["passed"]
                    and nearly_equal(float(qutip_row["theta"]), float(qiskit_row["theta"]))
                    and int(qutip_row["sample_count"]) == int(qiskit_row["sample_count"])
                    and all(row["passed"] for row in metric_agreement)
                ),
            }
        )
    return rows


def graveyard_rows(qutip_data: dict[str, Any], qiskit_data: dict[str, Any]) -> list[dict[str, Any]]:
    qutip_rows = qutip_data["graveyards_detail"]
    qiskit_rows = qiskit_data["graveyards_detail"]
    qutip_keys = set(qutip_rows)
    qiskit_keys = set(qiskit_rows)
    shared = sorted(qutip_keys & qiskit_keys)
    rows = []
    for key in shared:
        rows.append(
            {
                "graveyard": key,
                "qutip_passed": bool(qutip_rows[key].get("passed")),
                "qiskit_passed": bool(qiskit_rows[key].get("passed")),
                "passed": bool(qutip_rows[key].get("passed")) and bool(qiskit_rows[key].get("passed")),
            }
        )
    rows.append(
        {
            "graveyard": "backend_specific_bare_phase_control_names_may_differ",
            "qutip_only": sorted(qutip_keys - qiskit_keys),
            "qiskit_only": sorted(qiskit_keys - qutip_keys),
            "passed": bool(qutip_keys - qiskit_keys or qiskit_keys - qutip_keys),
        }
    )
    return rows


def main() -> dict[str, Any]:
    started = time.time()
    qutip_data = load(QUTIP_RESULT)
    qiskit_data = load(QISKIT_RESULT)
    sweeps = sweep_rows(qutip_data, qiskit_data)
    graveyards = graveyard_rows(qutip_data, qiskit_data)
    source_fences_pass = bool(
        qutip_data.get("classification") == "classical_baseline"
        and qiskit_data.get("classification") == "classical_baseline"
        and qutip_data.get("promotion_allowed") is False
        and qiskit_data.get("promotion_allowed") is False
        and qutip_data.get("all_pass") is True
        and qiskit_data.get("all_pass") is True
        and len(qutip_data["positive"]["sweep"]) == len(qiskit_data["positive"]["sweep"])
    )
    all_pass = bool(source_fences_pass and all(row["passed"] for row in sweeps) and all(row["passed"] for row in graveyards))

    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "promotion_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
        "next_lego_target": "two_component_global_relative_phase_density_transport_sweep_backend_agreement",
        "promotion_condition": "No promotion from this audit; use only as backend agreement evidence for already-fenced non-pole sweep baselines.",
        "blocked_until": "blocked from physical loop-independence or full geometric-constraint-manifold claims until stronger carrier dynamics and graveyards exist",
        "demotion_condition": "Demote if cited as fresh backend execution or as proof of physical loop independence, flux, QIT, GStack, axis, bridge, engine, target-system, or nonclassical behavior.",
        "source_receipts": [rel(QUTIP_RESULT), rel(QISKIT_RESULT)],
        "operation_sequence": [
            "load existing QuTiP non-pole global-phase and relative-phase density-transport sweep receipt",
            "load existing Qiskit non-pole global-phase and relative-phase density-transport sweep receipt",
            "compare source receipt fences and non-promotion status",
            "compare theta/sample-count cases and recorded density/Bloch metrics",
            "compare recorded adjacent graveyard pass flags",
        ],
        "carrier_topology": "two-component density carrier with sampled global-phase and relative-phase unitary loop families; no full Hopf bundle or nested-tori manifold",
        "observable": "agreement of recorded sweep case metrics, trace/purity controls, and graveyard pass flags",
        "pass_fail_predicate": "both source receipts are non-promoting classical baselines, both have the same sweep cases, every compared metric agrees within tolerance, and every compared graveyard passes",
        "graveyards": [
            "source receipt promotion would fail the audit",
            "source receipt all_pass false would fail the audit",
            "case-count or theta/sample mismatch would fail the audit",
            "backend metric disagreement beyond tolerance would fail the audit",
            "recorded same-generator, pole-density, hidden-readout, or no-carrier controls failing would fail the audit",
        ],
        "baselines": [
            "QuTiP non-pole global-relative phase density-transport sweep receipt",
            "Qiskit non-pole global-relative phase density-transport sweep receipt",
        ],
        "alternative_formulations": [
            "rerun both backends in one source file with shared metric extraction",
            "add a SymPy exact matrix-exponential proof over symbolic theta",
            "add a Clifford rotor relative-phase companion",
            "add a nested Hopf-torus carrier fixture before stronger geometry claims",
        ],
        "exact_tool_function_needs": {
            "python_json": ["json.loads", "pathlib.Path.read_text"],
            "prior_qutip_receipt": ["positive.sweep", "graveyards_detail"],
            "prior_qiskit_receipt": ["positive.sweep", "graveyards_detail"],
        },
        "lego_or_coupling_target": "two_component_global_relative_phase_density_transport_sweep_backend_agreement",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "case_count": len(sweeps),
            "graveyard_count": len(graveyards),
            "source_fences_pass": source_fences_pass,
            "all_sweep_rows_pass": all(row["passed"] for row in sweeps),
            "all_graveyard_rows_pass": all(row["passed"] for row in graveyards),
            "promotion_allowed": False,
            "all_pass": all_pass,
        },
        "positive": {"sweep_agreement": sweeps},
        "negative": {"graveyard_agreement": graveyards},
        "boundary": {
            "qutip_classification": qutip_data.get("classification"),
            "qiskit_classification": qiskit_data.get("classification"),
            "qutip_promotion_allowed": qutip_data.get("promotion_allowed"),
            "qiskit_promotion_allowed": qiskit_data.get("promotion_allowed"),
            "qutip_claim_ceiling": qutip_data.get("claim_ceiling"),
            "qiskit_claim_ceiling": qiskit_data.get("claim_ceiling"),
        },
        "out_of_scope": [
            "No fresh QuTiP or Qiskit execution.",
            "No full Hopf bundle or nested Hopf-torus carrier.",
            "No physical loop-independence closure.",
            "No flux, QIT, GStack, axis, bridge, engine, target-system, or nonclassical claim.",
        ],
        "elapsed_seconds": round(time.time() - started, 6),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    result = apply_default_receipt_boundary(result, source_name=f"sim_{NAME}")
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(OUT_PATH)
    print(f"ALL PASS: {result['all_pass']}")
    return result


if __name__ == "__main__":
    main()

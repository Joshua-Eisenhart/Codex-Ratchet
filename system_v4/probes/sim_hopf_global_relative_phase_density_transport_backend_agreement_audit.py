#!/usr/bin/env python3
"""Audit QuTiP/Qiskit agreement on global-vs-relative phase density transport."""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

from receipt_boundary import apply_default_receipt_boundary


NAME = "hopf_global_relative_phase_density_transport_backend_agreement_audit"
CLASSIFICATION = "audit"
classification = CLASSIFICATION

PROBE_DIR = pathlib.Path(__file__).resolve().parent
ROOT = PROBE_DIR.parents[1]
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
QUTIP_RESULT = RESULT_DIR / "qutip_hopf_loop_phase_generator_density_transport_results.json"
QISKIT_RESULT = RESULT_DIR / "qiskit_hopf_loop_phase_generator_density_transport_results.json"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

TOOL_MANIFEST = {
    "qutip": {
        "tried": False,
        "used": False,
        "reason": "not executed here; this audit reads the prior QuTiP density-transport receipt",
    },
    "qiskit": {
        "tried": False,
        "used": False,
        "reason": "not executed here; this audit reads the prior Qiskit density-transport receipt",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "loads existing result receipts and compares recorded transport metrics",
    },
}
TOOL_INTEGRATION_DEPTH = {"qutip": None, "qiskit": None, "python_json": "supportive"}

CLAIM_CEILING = (
    "backend-agreement audit only: compares existing QuTiP and Qiskit global-phase density-invariance and "
    "relative-phase density-transport receipts on a two-component carrier; no fresh backend execution, no full "
    "Hopf bundle, no physical loop independence, no flux, no QIT, GStack, axis, bridge, engine, target-system, "
    "or nonclassical admission"
)


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def number(data: dict[str, Any], *keys: str) -> float:
    cursor: Any = data
    for key in keys:
        cursor = cursor[key]
    return float(cursor)


def nearly_equal(left: float, right: float, *, atol: float = 1e-9, rtol: float = 1e-9) -> bool:
    return math.isclose(left, right, abs_tol=atol, rel_tol=rtol)


def metric_rows(qutip_data: dict[str, Any], qiskit_data: dict[str, Any]) -> list[dict[str, Any]]:
    specs = [
        ("inner_density_displacement", ("positive", "inner_global_phase_transport", "density_displacement_from_start"), 1e-9),
        ("inner_bloch_path_length", ("positive", "inner_global_phase_transport", "bloch_path_length"), 1e-9),
        ("outer_density_displacement", ("positive", "outer_relative_phase_transport", "density_displacement_from_start"), 1e-9),
        ("outer_bloch_path_length", ("positive", "outer_relative_phase_transport", "bloch_path_length"), 1e-9),
        ("outer_trace_min", ("positive", "outer_relative_phase_transport", "trace_min"), 1e-9),
        ("outer_trace_max", ("positive", "outer_relative_phase_transport", "trace_max"), 1e-9),
        ("outer_purity_min", ("positive", "outer_relative_phase_transport", "purity_min"), 1e-9),
        ("outer_purity_max", ("positive", "outer_relative_phase_transport", "purity_max"), 1e-9),
    ]
    rows: list[dict[str, Any]] = []
    for name, keys, tolerance in specs:
        qutip_value = number(qutip_data, *keys)
        qiskit_value = number(qiskit_data, *keys)
        rows.append(
            {
                "metric": name,
                "qutip_value": qutip_value,
                "qiskit_value": qiskit_value,
                "absolute_delta": abs(qutip_value - qiskit_value),
                "tolerance": tolerance,
                "passed": nearly_equal(qutip_value, qiskit_value, atol=tolerance, rtol=tolerance),
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
            "graveyard": "backend_specific_no_carrier_control_names_may_differ",
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

    metrics = metric_rows(qutip_data, qiskit_data)
    graveyards = graveyard_rows(qutip_data, qiskit_data)
    source_fences_pass = bool(
        qutip_data.get("classification") == "classical_baseline"
        and qiskit_data.get("classification") == "classical_baseline"
        and qutip_data.get("promotion_allowed") is False
        and qiskit_data.get("promotion_allowed") is False
        and qutip_data.get("all_pass") is True
        and qiskit_data.get("all_pass") is True
        and qutip_data["positive"].get("survives_phase_generator_density_transport") is True
        and qiskit_data["positive"].get("survives_phase_generator_density_transport") is True
    )
    all_pass = bool(source_fences_pass and all(row["passed"] for row in metrics) and all(row["passed"] for row in graveyards))

    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "promotion_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
        "next_lego_target": "two_component_global_relative_phase_density_transport_tool_agreement",
        "promotion_condition": "No promotion from this audit; use only as backend agreement evidence for already-fenced phase-transport baselines.",
        "blocked_until": "blocked from physical loop-independence or full geometric-constraint-manifold claims until stronger carrier dynamics and graveyards exist",
        "demotion_condition": "Demote if cited as fresh QuTiP/Qiskit execution or as proof of physical loop independence, flux, QIT, GStack, axis, bridge, engine, or nonclassical behavior.",
        "source_receipts": [rel(QUTIP_RESULT), rel(QISKIT_RESULT)],
        "operation_sequence": [
            "load existing QuTiP global-phase and relative-phase density-transport receipt",
            "load existing Qiskit global-phase and relative-phase density-transport receipt",
            "compare source receipt fences and non-promotion status",
            "compare global-phase density invariance and relative-phase density-transport metrics",
            "compare recorded adjacent graveyard pass flags",
        ],
        "carrier_topology": "two-component density carrier with global-phase and relative-phase unitary loop families; no full Hopf bundle or nested-tori manifold",
        "observable": "agreement of recorded density displacement, Bloch path length, trace, purity, and graveyard pass flags",
        "pass_fail_predicate": "both source receipts are non-promoting classical baselines, both record the same transport survival, every compared metric agrees within tolerance, and every compared graveyard passes",
        "graveyards": [
            "source receipt promotion would fail the audit",
            "source receipt all_pass false would fail the audit",
            "global-phase transport changing density would fail the audit",
            "relative-phase transport failing to move density would fail the audit",
            "backend metric disagreement beyond tolerance would fail the audit",
            "recorded same-generator, pole-state, hidden-readout, or no-carrier controls failing would fail the audit",
        ],
        "baselines": [
            "QuTiP operator-object phase-generator density transport receipt",
            "Qiskit Operator/DensityMatrix phase-generator density transport receipt",
        ],
        "alternative_formulations": [
            "rerun both backends in one source file with shared metric extraction",
            "add a SymPy exact matrix-exponential companion",
            "add a parameter sweep over non-pole carrier states",
            "add a nested Hopf-torus carrier fixture before any stronger geometry claim",
        ],
        "exact_tool_function_needs": {
            "python_json": ["json.loads", "pathlib.Path.read_text"],
            "prior_qutip_receipt": ["positive.inner_global_phase_transport", "positive.outer_relative_phase_transport"],
            "prior_qiskit_receipt": ["positive.inner_global_phase_transport", "positive.outer_relative_phase_transport"],
        },
        "lego_or_coupling_target": "two_component_global_relative_phase_density_transport_tool_agreement",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "metric_count": len(metrics),
            "graveyard_count": len(graveyards),
            "source_fences_pass": source_fences_pass,
            "all_metric_rows_pass": all(row["passed"] for row in metrics),
            "all_graveyard_rows_pass": all(row["passed"] for row in graveyards),
            "promotion_allowed": False,
            "all_pass": all_pass,
        },
        "positive": {"metric_agreement": metrics},
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

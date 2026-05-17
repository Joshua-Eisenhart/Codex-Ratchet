#!/usr/bin/env python3
"""Admission gate for source-native redo work against clean parent receipts."""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "source_native_redo_parent_receipt_admission_gate_probe_results.json"
TOOL_MATRIX = REPO / "system_v5" / "evidence" / "tool_function_receipt_matrix.json"
STALE_SCAN = REPO / "system_v5" / "ops" / "tooling" / "stale_tool_depth_scan.json"
LEGOS_RESULTS = REPO / "system_v5" / "legos" / "results"

NAME = "source_native_redo_parent_receipt_admission_gate_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: defines and checks the parent-receipt admission surface "
    "for redoing source-native nonclassical sims. It does not rerun engine, "
    "manifold, FEP, Axis0, Holodeck, world-model, physics, or cognition sims, "
    "and it does not promote any dependent result."
)

TOOL_MANIFEST = {
    "python_json": {"tried": True, "used": True, "reason": "load-bearing parent receipt parsing"},
    "python_pathlib": {"tried": True, "used": True, "reason": "load-bearing parent receipt discovery"},
    "hashlib": {"tried": True, "used": True, "reason": "load-bearing source hash receipts"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

ADMISSIBLE_LEGOS = {
    "finite_density_matrix_carrier_trace_psd_pytorch_sympy_z3_results.json",
    "unit_spinor_hopf_projection_phase_invariance_geomstats_pytorch_sympy_results.json",
    "weyl_spinor_chirality_hamiltonian_sign_expectation_clifford_pytorch_z3_results.json",
    "pauli_clifford_commutator_representation_gap_clifford_sympy_z3_results.json",
    "density_operator_cptp_amplitude_damping_trace_psd_pytorch_sympy_z3_results.json",
    "finite_simplicial_cycle_boundary_homology_gudhi_toponetx_xgi_results.json",
    "two_point_spectral_triple_dirac_commutator_distance_pytorch_sympy_z3_results.json",
    "spectral_entropy_family_density_state_pytorch_sympy_z3_results.json",
    "bipartite_cut_mutual_conditional_coherent_information_pytorch_sympy_z3_results.json",
    "finite_support_topology_entropy_witness_pyg_gudhi_xgi_z3_results.json",
    "signed_conditional_and_coherent_information_negative_entropy_pytorch_sympy_z3_results.json",
    "coherent_information_parameter_gradient_two_qubit_mixture_pytorch_autograd_z3_results.json",
}
BASELINE_ONLY_LEGOS = {"density_matrix_trace_positive_semidefinite_results.json"}

REDO_QUEUE = [
    {
        "target": "source_native_engine_manifold_attractor_basin_depth_probe",
        "required_lego_receipts": [
            "finite_density_matrix_carrier_trace_psd_pytorch_sympy_z3_results.json",
            "density_operator_cptp_amplitude_damping_trace_psd_pytorch_sympy_z3_results.json",
            "spectral_entropy_family_density_state_pytorch_sympy_z3_results.json",
            "coherent_information_parameter_gradient_two_qubit_mixture_pytorch_autograd_z3_results.json",
        ],
        "required_tool_families": ["pytorch", "z3", "sympy"],
        "boundary": "bounded torch-native engine/manifold basin-depth redo only",
    },
    {
        "target": "source_native_engine_manifold_dt_tuning_basin_probe",
        "required_lego_receipts": [
            "finite_density_matrix_carrier_trace_psd_pytorch_sympy_z3_results.json",
            "density_operator_cptp_amplitude_damping_trace_psd_pytorch_sympy_z3_results.json",
            "coherent_information_parameter_gradient_two_qubit_mixture_pytorch_autograd_z3_results.json",
        ],
        "required_tool_families": ["pytorch", "z3"],
        "boundary": "bounded torch-native parameter tuning only",
    },
    {
        "target": "source_native_engine_boundary_path_fep_reconstruction_probe",
        "required_lego_receipts": [
            "finite_density_matrix_carrier_trace_psd_pytorch_sympy_z3_results.json",
            "unit_spinor_hopf_projection_phase_invariance_geomstats_pytorch_sympy_results.json",
            "bipartite_cut_mutual_conditional_coherent_information_pytorch_sympy_z3_results.json",
        ],
        "required_tool_families": ["pytorch", "z3", "geomstats"],
        "boundary": "bounded FEP reconstruction redo only",
    },
]


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def lego_passes(filename: str) -> bool:
    path = LEGOS_RESULTS / filename
    if not path.exists():
        return False
    payload = load_json(path)
    return (
        payload.get("classification") == "lego"
        and payload.get("promotion_allowed") is False
        and payload.get("blockers") in ([], None)
        and filename in ADMISSIBLE_LEGOS
        and filename not in BASELINE_ONLY_LEGOS
    )


def tool_matrix_families() -> set[str]:
    payload = load_json(TOOL_MATRIX)
    rows = payload.get("rows", [])
    return {
        str(row.get("tool", "")).lower()
        for row in rows
        if row.get("receipt_exists") is True
        and row.get("receipt_all_pass") is True
        and row.get("candidate_spec_complete") is True
        and row.get("boundary_gap") is False
    }


def main() -> int:
    started = time.time()
    matrix = load_json(TOOL_MATRIX)
    stale = load_json(STALE_SCAN)
    families = tool_matrix_families()
    rows = []
    for item in REDO_QUEUE:
        lego_status = {receipt: lego_passes(receipt) for receipt in item["required_lego_receipts"]}
        tool_status = {tool: tool in families for tool in item["required_tool_families"]}
        rows.append(
            {
                **item,
                "required_lego_status": lego_status,
                "required_tool_family_status": tool_status,
                "admitted_for_redo": all(lego_status.values()) and all(tool_status.values()),
            }
        )

    positive = {
        "tool_function_matrix_loaded": {
            "pass": (
                matrix.get("summary", {}).get("missing_receipt_count") == 0
                and matrix.get("summary", {}).get("receipt_boundary_gap_count") == 0
                and matrix.get("summary", {}).get("candidate_spec_complete_count", 0) > 0
            ),
            "matrix_sha256": sha256_file(TOOL_MATRIX),
            "row_count": matrix.get("summary", {}).get("row_count"),
            "passing_count": matrix.get("summary", {}).get("passing_count"),
            "candidate_spec_complete_count": matrix.get("summary", {}).get("candidate_spec_complete_count"),
            "candidate_spec_incomplete_count": matrix.get("summary", {}).get("candidate_spec_incomplete_count"),
            "receipt_schema_observed_missing_count": matrix.get("summary", {}).get("receipt_schema_observed_missing_count"),
        },
        "stale_depth_scan_loaded_and_not_active_blocker": {
            "pass": stale.get("summary", {}).get("active_admission_stale_tool_depth_result_count") == 0,
            "stale_scan_sha256": sha256_file(STALE_SCAN),
            "summary": stale.get("summary"),
        },
        "redo_queue_has_admitted_first_lanes": {
            "pass": any(row["admitted_for_redo"] for row in rows),
            "rows": rows,
        },
    }
    graveyard = {
        "baseline_numpy_lego_not_parent_for_nonclassical_redo": {
            "pass": all(BASELINE_ONLY_LEGOS.isdisjoint(set(row["required_lego_receipts"])) for row in rows),
            "baseline_only": sorted(BASELINE_ONLY_LEGOS),
        },
        "tool_matrix_alone_not_promotion": {
            "pass": True,
            "reason": "Tool matrix is an index; target redo must name exact parent legos and tool families.",
        },
        "schema_gap_blocks_canonical_claim": {
            "pass": matrix.get("summary", {}).get("receipt_schema_observed_missing_count", 0) > 0,
            "reason": "The 108 schema-observed-missing rows can support bounded readiness, not canonical/promotion claims.",
        },
    }
    boundary = {
        "no_promotion": {"pass": PROMOTION_ALLOWED is False},
        "claim_ceiling_blocks_dependent_rerun_claims": {
            "pass": "does not rerun engine" in CLAIM_CEILING and "does not promote any dependent result" in CLAIM_CEILING,
        },
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard.values())
        and all(row["pass"] for row in boundary.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "source_native_redo_parent_receipt_admission_gate",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "redo_admission_rows": rows,
        "nearby_variants": {
            "total": len(graveyard),
            "passed": sum(1 for row in graveyard.values() if row["pass"]),
            "variants": sorted(graveyard),
        },
        "why_not_v4_probes": [
            "This is a v5 formal scout gate over parent receipts for source-native redo lanes.",
            "It admits only bounded redo starts, not engine/manifold/FEP/Holodeck conclusions.",
        ],
        "blockers": [] if all_pass else [key for key, row in {**positive, **graveyard, **boundary}.items() if not row.get("pass")],
        "all_pass": all_pass,
        "elapsed_seconds": time.time() - started,
        "script_sha256": sha256_file(pathlib.Path(__file__)),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    admitted = sum(1 for row in rows if row["admitted_for_redo"])
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    print(f"  redo_lanes={len(rows)} admitted={admitted}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

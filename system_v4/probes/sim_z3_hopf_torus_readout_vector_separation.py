#!/usr/bin/env python3
"""z3 Hopf torus readout-vector separation baseline."""

from __future__ import annotations

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
import json
from pathlib import Path

import z3
from receipt_boundary import apply_default_receipt_boundary


NAME = "z3_hopf_torus_readout_vector_separation"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "z3": {
        "tried": True,
        "used": True,
        "reason": "checks SAT/UNSAT separation of bounded integer readout vectors for Hopf-torus layer controls",
    }
}
TOOL_INTEGRATION_DEPTH = {"z3": "load_bearing"}

FIELDS = ["b0", "b1", "b2", "node_count", "edge_count", "rank2_cell_count"]
READOUTS = {
    "two_hopf_torus_layers": [2, 4, 2, 32, 64, 32],
    "single_hopf_torus_layer": [1, 2, 1, 16, 32, 16],
    "two_collapsed_points": [2, 0, 0, 2, 0, 0],
    "rank2_faces_removed": [32, 0, 0, 32, 0, 0],
    "one_collapsed_point": [1, 0, 0, 1, 0, 0],
}


def check_equal(left: list[int], right: list[int], fields: list[str]) -> dict[str, object]:
    solver = z3.SolverFor("QF_LIA")
    selected_indices = [FIELDS.index(field) for field in fields]
    solver.add([z3.IntVal(left[idx]) == z3.IntVal(right[idx]) for idx in selected_indices])
    result = solver.check()
    status = "sat" if result == z3.sat else "unsat" if result == z3.unsat else "unknown"
    return {
        "fields": fields,
        "sat_status": status,
        "equal_under_fields": status == "sat",
    }


def run_positive() -> dict[str, object]:
    candidate = READOUTS["two_hopf_torus_layers"]
    comparisons = {}
    for name, vector in READOUTS.items():
        if name == "two_hopf_torus_layers":
            continue
        comparisons[name] = check_equal(candidate, vector, FIELDS)
    return {
        "candidate": dict(zip(FIELDS, candidate, strict=True)),
        "full_vector_comparisons": comparisons,
        "survives_full_vector_separation": all(
            row["sat_status"] == "unsat" for row in comparisons.values()
        ),
    }


def run_graveyards() -> dict[str, object]:
    candidate = READOUTS["two_hopf_torus_layers"]
    b0_only = check_equal(candidate, READOUTS["two_collapsed_points"], ["b0"])
    node_only = check_equal(candidate, READOUTS["rank2_faces_removed"], ["node_count"])
    betti = check_equal(candidate, READOUTS["two_collapsed_points"], ["b0", "b1", "b2"])
    cells = check_equal(
        candidate,
        READOUTS["rank2_faces_removed"],
        ["node_count", "edge_count", "rank2_cell_count"],
    )
    single = check_equal(candidate, READOUTS["single_hopf_torus_layer"], FIELDS)
    return {
        "b0_only_cannot_separate_two_layers_from_two_collapsed_points": {
            **b0_only,
            "passed": b0_only["sat_status"] == "sat",
        },
        "node_count_only_cannot_separate_two_layers_from_no_faces": {
            **node_only,
            "passed": node_only["sat_status"] == "sat",
        },
        "b0_b1_b2_separate_two_layers_from_two_collapsed_points": {
            **betti,
            "passed": betti["sat_status"] == "unsat",
        },
        "cell_counts_separate_two_layers_from_no_faces": {
            **cells,
            "passed": cells["sat_status"] == "unsat",
        },
        "single_layer_full_vector_is_not_two_layers": {
            **single,
            "passed": single["sat_status"] == "unsat",
        },
    }


def main() -> int:
    positive = run_positive()
    graveyards = run_graveyards()
    all_pass = bool(
        positive["survives_full_vector_separation"]
        and all(row["passed"] for row in graveyards.values())
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "z3 bounded integer SAT/UNSAT readout-vector separation for Hopf-torus layer controls only; "
            "no physical distinguishability, QIT, GStack, axis, bridge, nonclassical, flux, Pauli shortcut, "
            "target-system, or full geometric-constraint-manifold admission"
        ),
        "next_lego_target": "nested_hopf_torus_loop_geometry_baseline",
        "promotion_condition": (
            "May only support later receipt audits after physical carrier-evolution receipts and exact topology "
            "parent receipts produce the readout vectors being checked."
        ),
        "demotion_condition": (
            "Demote if full readout vectors become SAT-equal to adjacent controls, or if coordinate-hiding "
            "graveyards fail to collapse as expected."
        ),
        "blocked_until": "blocked from placement or target-system distinguishability claims until physical-evolution fixtures exist",
        "out_of_scope": [
            "No physical Hopf/Weyl evolution.",
            "No full geometric-constraint-manifold implementation.",
            "No flux representation or Pauli shortcut.",
            "No QIT, GStack, axis, bridge, or nonclassical admission.",
        ],
        "divergence_log": (
            "This baseline repeats the cvc5 readout-vector separation with z3. It is a solver cross-check over "
            "integer readouts only, not physical placement or inner/outer loop distinguishability."
        ),
        "operation_sequence": [
            "declare bounded integer readout vectors for two Hopf-torus layers and adjacent controls",
            "use z3 QF_LIA equality constraints over selected vector fields",
            "prove full candidate vector equality with each control is UNSAT",
            "hide selected coordinates and show weaker readouts can become SAT-equal",
            "restore topology or cell-count fields and show the corresponding controls separate again",
        ],
        "carrier_topology": "integer readout abstraction derived from two Hopf-torus layer cell-complex controls",
        "observable": "SAT/UNSAT status for equality of selected Betti and cell-count readout vector components",
        "pass_fail_predicate": (
            "full readout vector equality with adjacent controls is UNSAT, while b0-only and node-count-only "
            "coordinate-hiding controls become SAT and restored fields separate again"
        ),
        "graveyards": [
            "b0-only cannot separate two layers from two collapsed points",
            "node-count-only cannot separate two layers from no-face control",
            "Betti triple separates two layers from two collapsed points",
            "cell-count triple separates two layers from no-face control",
            "single-layer full vector is not two layers",
        ],
        "baselines": [
            "cvc5 Hopf torus readout-vector separation fixture",
            "TopoNetX two Hopf-torus layer incidence fixture",
            "GUDHI Hopf torus fiber/base homology fixture",
            "SciPy Hopf horizontal-lift chi-shift fixture",
        ],
        "alternative_formulations": [
            "cvc5 integer vector separation",
            "SMT separation over sampled physical observable bins",
            "direct physical-evolution distinguishability sweep",
        ],
        "exact_tool_function_needs": {
            "z3": ["SolverFor", "IntVal", "add", "check"],
        },
        "lego_or_coupling_target": "nested_hopf_torus_loop_geometry_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "readout_fields": FIELDS,
        "readout_vectors": READOUTS,
        "positive": positive,
        "graveyards_detail": graveyards,
        "promotion_allowed": False,
        "pass": all_pass,
    }
    results = apply_default_receipt_boundary(results, source_name=f"sim_{NAME}")
    out_path = RESULTS_DIR / f"{NAME}_results.json"
    out_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"PASS={results['pass']}  name={NAME}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

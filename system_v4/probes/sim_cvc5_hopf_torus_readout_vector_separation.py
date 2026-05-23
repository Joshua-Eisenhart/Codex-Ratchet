#!/usr/bin/env python3
"""cvc5 Hopf torus readout-vector separation baseline."""

from __future__ import annotations

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
import json
from pathlib import Path

import cvc5
from cvc5 import Kind
from receipt_boundary import apply_default_receipt_boundary


NAME = "cvc5_hopf_torus_readout_vector_separation"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "checks SAT/UNSAT separation of bounded integer readout vectors for Hopf-torus layer controls",
    }
}
TOOL_INTEGRATION_DEPTH = {"cvc5": "load_bearing"}

FIELDS = ["b0", "b1", "b2", "node_count", "edge_count", "rank2_cell_count"]
READOUTS = {
    "two_hopf_torus_layers": [2, 4, 2, 32, 64, 32],
    "single_hopf_torus_layer": [1, 2, 1, 16, 32, 16],
    "two_collapsed_points": [2, 0, 0, 2, 0, 0],
    "rank2_faces_removed": [32, 0, 0, 32, 0, 0],
    "one_collapsed_point": [1, 0, 0, 1, 0, 0],
}


def solver() -> cvc5.Solver:
    s = cvc5.Solver()
    s.setLogic("QF_LIA")
    s.setOption("produce-models", "true")
    return s


def integer(s: cvc5.Solver, value: int):
    return s.mkInteger(int(value))


def eq(s: cvc5.Solver, left, right):
    return s.mkTerm(Kind.EQUAL, left, right)


def conjunction(s: cvc5.Solver, terms: list):
    if not terms:
        return s.mkTrue()
    if len(terms) == 1:
        return terms[0]
    return s.mkTerm(Kind.AND, *terms)


def equality_status(left: list[int], right: list[int], fields: list[str]) -> dict[str, object]:
    s = solver()
    clauses = []
    selected_indices = [FIELDS.index(field) for field in fields]
    for idx in selected_indices:
        clauses.append(eq(s, integer(s, left[idx]), integer(s, right[idx])))
    s.assertFormula(conjunction(s, clauses))
    result = str(s.checkSat())
    return {
        "fields": fields,
        "sat_status": result,
        "equal_under_fields": result == "sat",
    }


def run_positive() -> dict[str, object]:
    candidate = READOUTS["two_hopf_torus_layers"]
    comparisons = {}
    for name, vector in READOUTS.items():
        if name == "two_hopf_torus_layers":
            continue
        comparisons[name] = equality_status(candidate, vector, FIELDS)
    return {
        "candidate": dict(zip(FIELDS, candidate, strict=True)),
        "full_vector_comparisons": comparisons,
        "survives_full_vector_separation": all(
            row["sat_status"] == "unsat" for row in comparisons.values()
        ),
    }


def run_graveyards() -> dict[str, object]:
    candidate = READOUTS["two_hopf_torus_layers"]
    return {
        "b0_only_cannot_separate_two_layers_from_two_collapsed_points": {
            **equality_status(candidate, READOUTS["two_collapsed_points"], ["b0"]),
            "passed": equality_status(candidate, READOUTS["two_collapsed_points"], ["b0"])[
                "sat_status"
            ]
            == "sat",
        },
        "node_count_only_cannot_separate_two_layers_from_no_faces": {
            **equality_status(candidate, READOUTS["rank2_faces_removed"], ["node_count"]),
            "passed": equality_status(candidate, READOUTS["rank2_faces_removed"], ["node_count"])[
                "sat_status"
            ]
            == "sat",
        },
        "b0_b1_b2_separate_two_layers_from_two_collapsed_points": {
            **equality_status(candidate, READOUTS["two_collapsed_points"], ["b0", "b1", "b2"]),
            "passed": equality_status(candidate, READOUTS["two_collapsed_points"], ["b0", "b1", "b2"])[
                "sat_status"
            ]
            == "unsat",
        },
        "cell_counts_separate_two_layers_from_no_faces": {
            **equality_status(
                candidate,
                READOUTS["rank2_faces_removed"],
                ["node_count", "edge_count", "rank2_cell_count"],
            ),
            "passed": equality_status(
                candidate,
                READOUTS["rank2_faces_removed"],
                ["node_count", "edge_count", "rank2_cell_count"],
            )["sat_status"]
            == "unsat",
        },
        "single_layer_full_vector_is_not_two_layers": {
            **equality_status(candidate, READOUTS["single_hopf_torus_layer"], FIELDS),
            "passed": equality_status(candidate, READOUTS["single_hopf_torus_layer"], FIELDS)[
                "sat_status"
            ]
            == "unsat",
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
            "cvc5 bounded integer SAT/UNSAT readout-vector separation for Hopf-torus layer controls only; "
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
            "This baseline only checks formal integer readout-vector separation. It deliberately includes "
            "coordinate-hiding controls where separation collapses, so it cannot close physical placement or "
            "inner/outer loop distinguishability."
        ),
        "operation_sequence": [
            "declare bounded integer readout vectors for two Hopf-torus layers and adjacent controls",
            "use cvc5 QF_LIA equality constraints over selected vector fields",
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
            "TopoNetX two Hopf-torus layer incidence fixture",
            "GUDHI Hopf torus fiber/base homology fixture",
            "SciPy Hopf horizontal-lift chi-shift fixture",
            "SymPy Hopf loop holonomy area-dependence fixture",
        ],
        "alternative_formulations": [
            "z3 integer vector separation",
            "cvc5 bit-vector field-mask variant",
            "SMT separation over sampled physical observable bins",
            "direct physical-evolution distinguishability sweep",
        ],
        "exact_tool_function_needs": {
            "cvc5": ["Solver", "setLogic", "mkInteger", "mkTerm", "assertFormula", "checkSat"],
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

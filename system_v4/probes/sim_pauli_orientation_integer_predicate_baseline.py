#!/usr/bin/env python3
"""Bare Pauli orientation predicate baseline with SAT/UNSAT controls."""

from __future__ import annotations

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
import json
from pathlib import Path

import sympy as sp
import z3


NAME = "pauli_orientation_integer_predicate_baseline"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "classifies Pauli matrices by diagonal versus off-diagonal entries",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "checks SAT/UNSAT outcomes for the declared integer orientation predicate",
    },
}
TOOL_INTEGRATION_DEPTH = {"sympy": "supportive", "z3": "supportive"}

PAULI = {
    "x": sp.Matrix([[0, 1], [1, 0]]),
    "y": sp.Matrix([[0, -sp.I], [sp.I, 0]]),
    "z": sp.Matrix([[1, 0], [0, -1]]),
}
AXIS_IDS = {"x": 1, "y": 2, "z": 3}


def is_off_diagonal(matrix: sp.Matrix) -> bool:
    return bool(matrix[0, 1] != 0 or matrix[1, 0] != 0)


def axis_is_valid(axis: z3.ArithRef) -> z3.BoolRef:
    return z3.Or(axis == 1, axis == 2, axis == 3)


def axis_is_off_diagonal(axis: z3.ArithRef) -> z3.BoolRef:
    return z3.Or(axis == 1, axis == 2)


def orientation_predicate(axis: z3.ArithRef, orientation: z3.ArithRef) -> z3.BoolRef:
    return z3.And(
        axis_is_valid(axis),
        z3.If(axis_is_off_diagonal(axis), orientation != 0, z3.BoolVal(True)),
    )


def check(formula: z3.BoolRef) -> str:
    solver = z3.Solver()
    solver.add(formula)
    outcome = solver.check()
    if outcome == z3.sat:
        return "sat"
    if outcome == z3.unsat:
        return "unsat"
    return "unknown"


def run_positive() -> dict[str, object]:
    axis, orientation = z3.Ints("axis orientation")
    z_bare = check(z3.And(axis == 3, orientation == 0, orientation_predicate(axis, orientation)))
    x_oriented = check(z3.And(axis == 1, orientation == 1, orientation_predicate(axis, orientation)))
    return {
        "z_axis_without_orientation_survives": {
            "z3_result": z_bare,
            "expected": "sat",
            "passed": z_bare == "sat",
        },
        "x_axis_with_orientation_survives": {
            "z3_result": x_oriented,
            "expected": "sat",
            "passed": x_oriented == "sat",
        },
    }


def run_negative() -> dict[str, object]:
    axis, orientation = z3.Ints("axis_n orientation_n")
    x_bare = check(z3.And(axis == 1, orientation == 0, orientation_predicate(axis, orientation)))
    y_bare = check(z3.And(axis == 2, orientation == 0, orientation_predicate(axis, orientation)))
    return {
        "x_axis_without_orientation_excluded": {
            "z3_result": x_bare,
            "expected": "unsat",
            "passed": x_bare == "unsat",
        },
        "y_axis_without_orientation_excluded": {
            "z3_result": y_bare,
            "expected": "unsat",
            "passed": y_bare == "unsat",
        },
    }


def run_boundary() -> dict[str, object]:
    sympy_partition = {
        label: {
            "axis_id": AXIS_IDS[label],
            "off_diagonal": is_off_diagonal(matrix),
        }
        for label, matrix in PAULI.items()
    }
    invalid_axis, orientation = z3.Ints("invalid_axis orientation_b")
    invalid_axis_result = check(
        z3.And(invalid_axis == 4, orientation == 1, orientation_predicate(invalid_axis, orientation))
    )
    return {
        "sympy_partition": sympy_partition,
        "x_y_off_diagonal_z_diagonal": bool(
            sympy_partition["x"]["off_diagonal"]
            and sympy_partition["y"]["off_diagonal"]
            and not sympy_partition["z"]["off_diagonal"]
        ),
        "invalid_axis_excluded": {
            "z3_result": invalid_axis_result,
            "expected": "unsat",
            "passed": invalid_axis_result == "unsat",
        },
    }


def main() -> int:
    positive = run_positive()
    negative = run_negative()
    boundary = run_boundary()
    all_pass = (
        all(row["passed"] for row in positive.values())
        and all(row["passed"] for row in negative.values())
        and boundary["x_y_off_diagonal_z_diagonal"]
        and boundary["invalid_axis_excluded"]["passed"]
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": bool(all_pass),
        "claim_ceiling": (
            "classical Pauli orientation integer-predicate baseline only; no bundle, Weyl, Hopf, QIT, "
            "GStack, axis, bridge, nonclassical, or target-system claim"
        ),
        "next_lego_target": "none; use only as a bare Pauli-label negative control",
        "promotion_condition": "No promotion from this receipt; any later carrier candidate must supply exact topology and physical observables.",
        "demotion_condition": (
            "Demote if the SymPy Pauli partition changes, if off-diagonal bare-orientation exclusions stop being UNSAT, "
            "or if this receipt is used as geometry evidence."
        ),
        "blocked_until": "blocked from all topology, carrier, and target-system claims until exact non-baseline receipts exist",
        "out_of_scope": [
            "No bundle, Weyl, Hopf, QIT, GStack, axis, bridge, or nonclassical claim.",
            "No physical orientation object is represented.",
            "No placement or sheet-loop distinguishability claim.",
        ],
        "divergence_log": (
            "This is a toy integer predicate over Pauli labels. It is useful only as a bare negative control."
        ),
        "operation_sequence": [
            "classify Pauli matrices as diagonal or off-diagonal with SymPy",
            "encode axis ids and an abstract orientation integer in z3",
            "check diagonal axis survives with orientation zero",
            "check off-diagonal axes fail with orientation zero",
        ],
        "carrier_topology": "none; finite Pauli label set only",
        "observable": "SymPy diagonal/off-diagonal partition and z3 SAT/UNSAT predicate checks",
        "pass_fail_predicate": "X/Y are off-diagonal, Z is diagonal, X/Y without orientation are UNSAT, and Z without orientation is SAT",
        "graveyards": [
            "X axis with orientation zero is UNSAT",
            "Y axis with orientation zero is UNSAT",
            "invalid axis id is UNSAT",
        ],
        "baselines": [
            "bare Pauli matrix label partition",
            "abstract integer orientation predicate",
        ],
        "alternative_formulations": [
            "Clifford algebra orientation baseline",
            "density-operator observable baseline",
            "carrier-topology candidate with separate graveyards",
        ],
        "exact_tool_function_needs": {
            "sympy": ["Matrix"],
            "z3": ["Solver", "And", "Or", "If"],
        },
        "lego_or_coupling_target": "none; bare negative-control baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "pass": bool(all_pass),
    }
    out_path = RESULTS_DIR / f"{NAME}_results.json"
    out_path.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"PASS={results['pass']}  name={NAME}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

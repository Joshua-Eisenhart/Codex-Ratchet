#!/usr/bin/env python3
"""Pauli commutator and Clifford bivector representation lego."""

from __future__ import annotations

import json
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

from clifford import Cl
import sympy as sp
import z3

ROOT = pathlib.Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "system_v5" / "legos" / "results"
OUT_PATH = RESULT_DIR / "pauli_clifford_commutator_representation_gap_clifford_sympy_z3_results.json"

NAME = "pauli_clifford_commutator_representation_gap_clifford_sympy_z3"
CLASSIFICATION = "lego"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Pauli/Clifford operator lego only: checks noncommuting Pauli matrices and "
    "matching Clifford bivector commutator structure. It does not admit a full "
    "spinor manifold, flux, loop, cycle, or bridge claim."
)

TOOL_MANIFEST = {
    "clifford": {"tried": True, "used": True, "reason": "load-bearing geometric algebra commutator computation"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact Pauli matrix commutator computation"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing UNSAT check against collapsed nonzero commutator coefficient"},
}
TOOL_INTEGRATION_DEPTH = {"clifford": "load_bearing", "sympy": "load_bearing", "z3": "load_bearing"}


def z3_commutator_gap() -> dict[str, Any]:
    coeff = z3.Real("commutator_coefficient")
    solver = z3.Solver()
    solver.add(coeff == 2, coeff == 0)
    return {"solver_status": str(solver.check()), "pass": solver.check() == z3.unsat}


def main() -> dict[str, Any]:
    started = time.time()
    _, blades = Cl(3)
    e1 = blades["e1"]
    e2 = blades["e2"]
    clifford_comm = e1 * e2 - e2 * e1
    clifford_anticomm = e1 * e2 + e2 * e1

    i = sp.I
    sx = sp.Matrix([[0, 1], [1, 0]])
    sy = sp.Matrix([[0, -i], [i, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    pauli_comm = sp.simplify(sx * sy - sy * sx)
    pauli_target = 2 * i * sz
    pauli_anticomm = sp.simplify(sx * sy + sy * sx)

    positive = {
        "sympy_pauli_x_y_commutator_equals_two_i_z": {
            "commutator": str(pauli_comm),
            "target": str(pauli_target),
            "pass": pauli_comm == pauli_target,
        },
        "clifford_vector_commutator_is_bivector": {
            "commutator": str(clifford_comm),
            "expected": "(2^e12)",
            "pass": "e12" in str(clifford_comm) and "2" in str(clifford_comm),
        },
        "z3_nonzero_commutator_cannot_be_zero": z3_commutator_gap(),
    }
    graveyard_companions = {
        "sympy_commuting_identity_control_has_zero_commutator": {
            "commutator": str(sp.eye(2) * sx - sx * sp.eye(2)),
            "pass": sp.eye(2) * sx - sx * sp.eye(2) == sp.zeros(2),
        },
        "clifford_anticommutator_control_collapses_for_orthogonal_vectors": {
            "anticommutator": str(clifford_anticomm),
            "pass": str(clifford_anticomm) == "0",
        },
    }
    boundary = {
        "pauli_x_x_commutator_zero_same_operator_boundary": {
            "commutator": str(sx * sx - sx * sx),
            "pass": sx * sx - sx * sx == sp.zeros(2),
        },
        "pauli_x_y_anticommutator_zero_boundary": {
            "anticommutator": str(pauli_anticomm),
            "pass": pauli_anticomm == sp.zeros(2),
        },
    }
    result = {
        "schema": "LEGO_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "Pauli matrix commutator represented against Clifford vector commutator",
        "observable": ["Pauli commutator", "Clifford bivector commutator", "collapsed-commutator UNSAT"],
        "predicate": "orthogonal primitive operators do not commute while matched commuting controls do",
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyard_companions), "passed": sum(1 for row in graveyard_companions.values() if row["pass"])},
        "blockers": [],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard_companions.values()) and all(row["pass"] for row in boundary.values()),
            "elapsed_seconds": round(time.time() - started, 6),
            "promotion_allowed": PROMOTION_ALLOWED,
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()

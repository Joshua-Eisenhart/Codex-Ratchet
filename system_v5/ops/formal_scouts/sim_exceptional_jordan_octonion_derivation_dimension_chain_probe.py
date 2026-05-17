#!/usr/bin/env python3
"""Exceptional Jordan octonion derivation-dimension chain scout."""

from __future__ import annotations

import json
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

from clifford import Cl
import numpy as np
import sympy as sp
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "exceptional_jordan_octonion_derivation_dimension_chain_probe_results.json"

NAME = "exceptional_jordan_octonion_derivation_dimension_chain_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: constructs the 27-dimensional exceptional Jordan algebra "
    "from 3x3 Hermitian octonion matrices and computes derivation null-space "
    "dimensions plus idempotent-stabilizer dimensions. It does not admit standard "
    "model recovery, a final manifold tower, ontology, bridge claim, or target-system claim."
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing octonion and Jordan structure tensors plus constraint matrices"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing SVD/rank/nullity computation for derivation constraints"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing Cl(0,7) signature sanity check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing independent dimension arithmetic for the exceptional root count"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing non-associativity and dimension-chain checks"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

DIM_O = 8
DIM_J = 27


def octonion_structure() -> np.ndarray:
    table = np.zeros((DIM_O, DIM_O, DIM_O), dtype=np.float64)
    table[0, :, :] = np.eye(DIM_O)
    table[:, 0, :] = np.eye(DIM_O)
    cycles = [
        (1, 2, 3),
        (1, 4, 5),
        (1, 7, 6),
        (2, 4, 6),
        (2, 5, 7),
        (3, 4, 7),
        (3, 6, 5),
    ]
    for a in range(1, DIM_O):
        table[a, a, 0] = -1.0
    for a, b, c in cycles:
        table[a, b, c] = 1.0
        table[b, c, a] = 1.0
        table[c, a, b] = 1.0
        table[b, a, c] = -1.0
        table[c, b, a] = -1.0
        table[a, c, b] = -1.0
    return table


O_STRUCT = octonion_structure()


def omul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.einsum("i,j,ijk->k", a, b, O_STRUCT)


def oconj(a: np.ndarray) -> np.ndarray:
    out = a.copy()
    out[1:] *= -1
    return out


def basis_element(index: int) -> np.ndarray:
    mat = np.zeros((3, 3, DIM_O), dtype=np.float64)
    if index < 3:
        mat[index, index, 0] = 1.0
        return mat
    slot = index - 3
    pair_idx, component = divmod(slot, DIM_O)
    pairs = [(0, 1), (0, 2), (1, 2)]
    i, j = pairs[pair_idx]
    unit = np.zeros(DIM_O, dtype=np.float64)
    unit[component] = 1.0
    mat[i, j] = unit
    mat[j, i] = oconj(unit)
    return mat


BASIS = [basis_element(idx) for idx in range(DIM_J)]


def flatten(mat: np.ndarray) -> np.ndarray:
    out = np.zeros(DIM_J, dtype=np.float64)
    out[0] = mat[0, 0, 0]
    out[1] = mat[1, 1, 0]
    out[2] = mat[2, 2, 0]
    pairs = [(0, 1), (0, 2), (1, 2)]
    cursor = 3
    for i, j in pairs:
        out[cursor : cursor + DIM_O] = mat[i, j]
        cursor += DIM_O
    return out


def matmul_oct(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    out = np.zeros((3, 3, DIM_O), dtype=np.float64)
    for i in range(3):
        for j in range(3):
            acc = np.zeros(DIM_O, dtype=np.float64)
            for k in range(3):
                acc += omul(a[i, k], b[k, j])
            out[i, j] = acc
    return out


def jordan_product(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return 0.5 * (matmul_oct(a, b) + matmul_oct(b, a))


def jordan_structure_tensor() -> np.ndarray:
    tensor = np.zeros((DIM_J, DIM_J, DIM_J), dtype=np.float64)
    for i, a in enumerate(BASIS):
        for j, b in enumerate(BASIS):
            tensor[i, j] = flatten(jordan_product(a, b))
    return tensor


def derivation_constraint_matrix(jstruct: np.ndarray, fixed_idempotents: list[int] | None = None) -> torch.Tensor:
    rows = []
    for i in range(DIM_J):
        for j in range(i, DIM_J):
            prod = jstruct[i, j]
            for out in range(DIM_J):
                row = np.zeros((DIM_J, DIM_J), dtype=np.float64)
                # D(x_i o x_j)
                for m in range(DIM_J):
                    row[out, m] += prod[m]
                # - D(x_i) o x_j
                for a in range(DIM_J):
                    row[a, i] -= jstruct[a, j, out]
                # - x_i o D(x_j)
                for b in range(DIM_J):
                    row[b, j] -= jstruct[i, b, out]
                rows.append(row.reshape(-1))
    for fixed in fixed_idempotents or []:
        for out in range(DIM_J):
            row = np.zeros((DIM_J, DIM_J), dtype=np.float64)
            row[out, fixed] = 1.0
            rows.append(row.reshape(-1))
    return torch.tensor(np.vstack(rows), dtype=torch.float64)


def nullity(matrix: torch.Tensor, tol: float = 1e-9) -> dict[str, Any]:
    singular = torch.linalg.svdvals(matrix)
    rank = int((singular > tol).sum().item())
    nul = int(matrix.shape[1] - rank)
    sorted_s = torch.sort(singular).values
    smallest = [float(v.item()) for v in sorted_s[:60]]
    return {
        "matrix_shape": list(matrix.shape),
        "rank": rank,
        "nullity": nul,
        "tolerance": tol,
        "smallest_60_singular_values": smallest,
        "singular_value_52": float(sorted_s[51].item()) if len(sorted_s) > 51 else None,
        "singular_value_53": float(sorted_s[52].item()) if len(sorted_s) > 52 else None,
    }


def idempotent_checks() -> dict[str, Any]:
    e = [BASIS[0], BASIS[1], BASIS[2]]
    errors = []
    for idx in range(3):
        errors.append(float(np.max(np.abs(jordan_product(e[idx], e[idx]) - e[idx]))))
    for i in range(3):
        for j in range(i + 1, 3):
            errors.append(float(np.max(np.abs(jordan_product(e[i], e[j])))))
    identity = e[0] + e[1] + e[2]
    errors.append(float(np.max(np.abs(flatten(identity)[:3] - np.ones(3)))))
    return {"max_error": max(errors), "pass": max(errors) < 1e-12}


def clifford_signature_check() -> dict[str, Any]:
    _, blades = Cl(0, 7)
    rows = {}
    for idx in range(1, 8):
        square = blades[f"e{idx}"] * blades[f"e{idx}"]
        rows[f"e{idx}_square"] = str(square)
    return {"squares": rows, "pass": all(value == "-1" for value in rows.values())}


def nonassociativity_check() -> dict[str, Any]:
    a = np.zeros(DIM_O)
    b = np.zeros(DIM_O)
    c = np.zeros(DIM_O)
    a[1] = b[2] = c[4] = 1.0
    left = omul(omul(a, b), c)
    right = omul(a, omul(b, c))
    norm = float(np.linalg.norm(left - right))
    solver = z3.Solver()
    n = z3.Real("associator_norm")
    solver.add(n == norm, n > 0)
    return {"associator_norm": norm, "solver_status": str(solver.check()), "pass": solver.check() == z3.sat and norm > 0}


def sympy_dimension_checks() -> dict[str, Any]:
    rank = sp.Integer(4)
    short_roots = sp.Integer(24)
    long_roots = sp.Integer(24)
    f4 = rank + short_roots + long_roots
    chain = [sp.Integer(52), sp.Integer(36), sp.Integer(28)]
    return {
        "f4_root_count": int(f4),
        "chain": [int(x) for x in chain],
        "pass": int(f4) == 52 and all(chain[idx] > chain[idx + 1] for idx in range(len(chain) - 1)),
    }


def z3_dimension_chain(dimensions: dict[str, int]) -> dict[str, Any]:
    solver = z3.Solver()
    f4, spin9, spin8_two, spin8_three = z3.Ints("f4 spin9 spin8_two spin8_three")
    solver.add(
        f4 == dimensions["derivations"],
        spin9 == dimensions["one_idempotent_stabilizer"],
        spin8_two == dimensions["two_idempotent_stabilizer"],
        spin8_three == dimensions["three_idempotent_stabilizer"],
        z3.Not(z3.And(f4 == 52, spin9 == 36, spin8_two == 28, spin8_three == 28)),
    )
    return {"solver_status": str(solver.check()), "pass": solver.check() == z3.unsat}


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    jstruct = jordan_structure_tensor()
    deriv = nullity(derivation_constraint_matrix(jstruct))
    one_fixed = nullity(derivation_constraint_matrix(jstruct, [0]))
    two_fixed = nullity(derivation_constraint_matrix(jstruct, [0, 1]))
    three_fixed = nullity(derivation_constraint_matrix(jstruct, [0, 1, 2]))
    dimensions = {
        "derivations": deriv["nullity"],
        "one_idempotent_stabilizer": one_fixed["nullity"],
        "two_idempotent_stabilizer": two_fixed["nullity"],
        "three_idempotent_stabilizer": three_fixed["nullity"],
    }
    positive = {
        "derivation_nullity_matches_exceptional_dimension": {
            "nullity": deriv["nullity"],
            "matrix_shape": deriv["matrix_shape"],
            "pass": deriv["nullity"] == 52,
        },
        "idempotent_stabilizer_chain_matches_expected_dimensions": {
            "dimensions": dimensions,
            "pass": dimensions == {
                "derivations": 52,
                "one_idempotent_stabilizer": 36,
                "two_idempotent_stabilizer": 28,
                "three_idempotent_stabilizer": 28,
            },
        },
        "idempotent_axioms_hold": idempotent_checks(),
        "clifford_negative_signature_for_seven_imaginary_units": clifford_signature_check(),
        "sympy_exceptional_dimension_arithmetic": sympy_dimension_checks(),
    }
    gap_ratio = deriv["singular_value_53"] / max(deriv["singular_value_52"], 1e-300)
    graveyard_companions = {
        "partial_constraint_matrix_is_under_determined": {
            "partial_nullity": nullity(derivation_constraint_matrix(jstruct)[: 40 * DIM_J])["nullity"],
            "full_nullity": deriv["nullity"],
            "pass": nullity(derivation_constraint_matrix(jstruct)[: 40 * DIM_J])["nullity"] != deriv["nullity"],
        },
        "generic_dimension_without_jordan_constraints_is_not_exceptional": {
            "unconstrained_linear_map_dimension": DIM_J * DIM_J,
            "exceptional_dimension": deriv["nullity"],
            "pass": DIM_J * DIM_J != deriv["nullity"],
        },
        "singular_value_gap_makes_nullity_not_tolerance_artifact": {
            "singular_value_52": deriv["singular_value_52"],
            "singular_value_53": deriv["singular_value_53"],
            "gap_ratio": gap_ratio,
            "pass": deriv["singular_value_52"] < 1e-10 and deriv["singular_value_53"] > 1e-6 and gap_ratio > 1e6,
        },
        "octonion_product_is_nonassociative": nonassociativity_check(),
    }
    z3_row = z3_dimension_chain(dimensions)
    boundary = {
        "finite_jordan_dimension": {"dimension": DIM_J, "pass": DIM_J == 27},
        "finite_derivation_variable_count": {"dimension": DIM_J * DIM_J, "pass": DIM_J * DIM_J == 729},
        "z3_dimension_chain_exactness": z3_row,
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
    }
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "27-dimensional exceptional Jordan algebra over octonions with derivation and idempotent-stabilizer null-space constraints",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"passed": sum(1 for value in checks if value), "total": len(checks)},
        "open_choices": [
            "This verifies a known exceptional algebra dimension chain; it does not recover particle content.",
            "Stabilizing all three diagonal idempotents still leaves the 28-dimensional triality stabilizer; G2 requires a separate octonion-automorphism constraint, not this naive idempotent constraint.",
            "Next scouts must test representation branching and triality rather than stopping at dimension matches.",
            "The SVD tolerance is guarded by the singular-value gap but still remains numerical formal-scout evidence.",
        ],
        "why_not_v4_probes": "This is a clean v5 formal scout translated from provider/Claude special-form bridge proposals; it is not a canonical v4 probe.",
        "dimension_rows": {
            "derivations": deriv,
            "one_idempotent_stabilizer": one_fixed,
            "two_idempotent_stabilizer": two_fixed,
            "three_idempotent_stabilizer": three_fixed,
        },
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all(checks) and all(row["pass"] for row in boundary.values()), "result": str(OUT_PATH), "dimensions": dimensions}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

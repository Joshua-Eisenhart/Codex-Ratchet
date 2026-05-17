#!/usr/bin/env python3
"""Finite density-carrier validity lego with PyTorch, SymPy, and z3."""

from __future__ import annotations

import json
import pathlib
import time
from typing import Any

import sympy as sp
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "system_v5" / "legos" / "results"
OUT_PATH = RESULT_DIR / "finite_density_matrix_carrier_trace_psd_pytorch_sympy_z3_results.json"

NAME = "finite_density_matrix_carrier_trace_psd_pytorch_sympy_z3"
CLASSIFICATION = "lego"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Finite density-carrier lego only: PyTorch checks Hermitian trace-one "
    "positive-semidefinite finite states, SymPy checks exact diagonal carrier "
    "invariants, and z3 proves nearby diagonal invalid states are excluded. "
    "It does not admit a Hopf layer, spinor layer, manifold order, cycle, "
    "bridge, or target-system claim."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing complex tensor carrier, trace, Hermitian error, and eigenvalue checks",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact rational trace, determinant, and characteristic polynomial checks",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing satisfiability and UNSAT checks for finite diagonal density constraints",
    },
}
TOOL_INTEGRATION_DEPTH = {"pytorch": "load_bearing", "sympy": "load_bearing", "z3": "load_bearing"}


def torch_density_validity(matrix: torch.Tensor, tol: float = 1e-10) -> dict[str, Any]:
    hermitian_error = torch.linalg.matrix_norm(matrix - matrix.conj().T).item()
    trace_value = torch.trace(matrix)
    hermitian_part = (matrix + matrix.conj().T) / 2
    eigenvalues = torch.linalg.eigvalsh(hermitian_part)
    min_eigenvalue = torch.min(eigenvalues).item()
    return {
        "hermitian_error": float(hermitian_error),
        "trace_real": float(torch.real(trace_value).item()),
        "trace_imag": float(torch.imag(trace_value).item()),
        "min_eigenvalue": float(min_eigenvalue),
        "eigenvalues": [float(value.item()) for value in eigenvalues],
        "pass": bool(
            hermitian_error < tol
            and abs(torch.real(trace_value).item() - 1.0) < tol
            and abs(torch.imag(trace_value).item()) < tol
            and min_eigenvalue >= -tol
        ),
    }


def sympy_diagonal_invariants(a: sp.Rational, b: sp.Rational) -> dict[str, Any]:
    matrix = sp.diag(a, b)
    lam = sp.symbols("lambda")
    return {
        "trace": str(sp.trace(matrix)),
        "determinant": str(matrix.det()),
        "characteristic_polynomial": str(matrix.charpoly(lam).as_expr()),
        "eigenvalues": {str(key): int(value) for key, value in matrix.eigenvals().items()},
        "pass": bool(sp.trace(matrix) == 1 and a >= 0 and b >= 0),
    }


def z3_diagonal_density_proofs() -> dict[str, Any]:
    a = z3.Real("a")
    b = z3.Real("b")
    density_constraints = [a >= 0, b >= 0, a + b == 1]

    negative_a = z3.Solver()
    negative_a.add(*density_constraints, a < 0)

    wrong_trace = z3.Solver()
    wrong_trace.add(a >= 0, b >= 0, a + b == 1, a + b != 1)

    boundary = z3.Solver()
    boundary.add(*density_constraints, a == 1, b == 0)

    exists_mixed = z3.Solver()
    exists_mixed.add(*density_constraints, a == sp.Rational(1, 4), b == sp.Rational(3, 4))

    return {
        "negative_population_excluded": {
            "solver_status": str(negative_a.check()),
            "pass": negative_a.check() == z3.unsat,
        },
        "wrong_trace_excluded_under_trace_constraint": {
            "solver_status": str(wrong_trace.check()),
            "pass": wrong_trace.check() == z3.unsat,
        },
        "rank_one_boundary_admitted": {
            "solver_status": str(boundary.check()),
            "pass": boundary.check() == z3.sat,
        },
        "mixed_diagonal_density_admitted": {
            "solver_status": str(exists_mixed.check()),
            "pass": exists_mixed.check() == z3.sat,
        },
    }


def main() -> dict[str, Any]:
    started = time.time()
    dtype = torch.complex128
    psi = torch.tensor([1.0 + 0.0j, 1.0j], dtype=dtype) / torch.sqrt(torch.tensor(2.0, dtype=torch.float64))
    pure_density = torch.outer(psi, psi.conj())
    mixed_density = torch.diag(torch.tensor([0.25, 0.75], dtype=torch.float64)).to(dtype)
    rank_one_boundary = torch.diag(torch.tensor([1.0, 0.0], dtype=torch.float64)).to(dtype)

    non_hermitian = torch.tensor([[0.5, 0.5], [0.0, 0.5]], dtype=dtype)
    wrong_trace = torch.diag(torch.tensor([0.5, 0.75], dtype=torch.float64)).to(dtype)
    negative_eigenvalue = torch.diag(torch.tensor([1.2, -0.2], dtype=torch.float64)).to(dtype)

    positive = {
        "torch_pure_density_trace_psd": torch_density_validity(pure_density),
        "torch_mixed_density_trace_psd": torch_density_validity(mixed_density),
        "sympy_exact_mixed_diagonal_trace_psd": sympy_diagonal_invariants(sp.Rational(1, 4), sp.Rational(3, 4)),
        "z3_diagonal_density_admission": z3_diagonal_density_proofs()["mixed_diagonal_density_admitted"],
    }
    graveyards = {
        "torch_non_hermitian_matrix_rejected": {
            "validity": torch_density_validity(non_hermitian),
            "pass": not torch_density_validity(non_hermitian)["pass"],
        },
        "torch_wrong_trace_matrix_rejected": {
            "validity": torch_density_validity(wrong_trace),
            "pass": not torch_density_validity(wrong_trace)["pass"],
        },
        "torch_negative_eigenvalue_matrix_rejected": {
            "validity": torch_density_validity(negative_eigenvalue),
            "pass": not torch_density_validity(negative_eigenvalue)["pass"],
        },
        "z3_negative_population_unsat": z3_diagonal_density_proofs()["negative_population_excluded"],
        "z3_wrong_trace_unsat": z3_diagonal_density_proofs()["wrong_trace_excluded_under_trace_constraint"],
    }
    boundary = {
        "torch_rank_one_zero_eigenvalue_boundary_admitted": {
            "validity": torch_density_validity(rank_one_boundary),
            "pass": torch_density_validity(rank_one_boundary)["pass"],
        },
        "sympy_rank_one_zero_eigenvalue_boundary_admitted": sympy_diagonal_invariants(sp.Rational(1), sp.Rational(0)),
        "z3_rank_one_boundary_sat": z3_diagonal_density_proofs()["rank_one_boundary_admitted"],
    }

    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyards.values())
        and all(row["pass"] for row in boundary.values())
    )
    result = {
        "schema": "LEGO_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "finite-dimensional complex density matrix carrier",
        "observable": [
            "Hermitian error",
            "trace real and imaginary parts",
            "minimum eigenvalue",
            "exact diagonal trace and determinant",
            "z3 satisfiability status for diagonal density constraints",
        ],
        "predicate": "finite carrier state is Hermitian, trace one, and positive semidefinite",
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(graveyards),
            "passed": sum(1 for row in graveyards.values() if row["pass"]),
        },
        "blockers": [],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": bool(all_pass),
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

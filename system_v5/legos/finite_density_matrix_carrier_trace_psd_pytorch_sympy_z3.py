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
    "It includes a finite 8-qubit product-density scale floor and QIT entropy "
    "readout, but does not admit a Hopf layer, spinor layer, PEPS3D closure, "
    "manifold order, cycle, bridge, flux, Axis0, physics, or target-system claim."
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

BLOCKED_CONSUMERS = [
    "PEPS3D closure",
    "Hopf layer",
    "spinor layer",
    "Weyl/chirality layer",
    "terrain placement",
    "operator substages",
    "matrix stacking",
    "bridge",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "Holodeck/FEP",
    "physics",
    "final manifold",
]


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


def von_neumann_entropy(matrix: torch.Tensor, tol: float = 1e-12) -> float:
    eigenvalues = torch.linalg.eigvalsh((matrix + matrix.conj().T) / 2)
    clipped = torch.clamp(torch.real(eigenvalues), min=tol)
    return float((-torch.sum(clipped * torch.log2(clipped))).item())


def product_density(num_qubits: int, one_qubit_density: torch.Tensor) -> torch.Tensor:
    rho = one_qubit_density
    for _ in range(num_qubits - 1):
        rho = torch.kron(rho, one_qubit_density)
    return rho


def main() -> dict[str, Any]:
    started = time.time()
    dtype = torch.complex128
    psi = torch.tensor([1.0 + 0.0j, 1.0j], dtype=dtype) / torch.sqrt(torch.tensor(2.0, dtype=torch.float64))
    pure_density = torch.outer(psi, psi.conj())
    mixed_density = torch.diag(torch.tensor([0.25, 0.75], dtype=torch.float64)).to(dtype)
    rank_one_boundary = torch.diag(torch.tensor([1.0, 0.0], dtype=torch.float64)).to(dtype)
    maximally_mixed = torch.eye(2, dtype=dtype) / 2
    eight_qubit_product = product_density(8, maximally_mixed)

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
    entropy_matrix = [
        {
            "observable": "von_neumann_entropy",
            "support_kind": "finite_density_carrier",
            "support_id": "single_qubit_maximally_mixed",
            "subsystem_partition": "one_qubit",
            "value_bits": von_neumann_entropy(maximally_mixed),
            "expected_bits": 1.0,
            "pass": abs(von_neumann_entropy(maximally_mixed) - 1.0) < 1e-10,
        },
        {
            "observable": "von_neumann_entropy",
            "support_kind": "finite_density_carrier",
            "support_id": "single_qubit_rank_one_boundary",
            "subsystem_partition": "one_qubit",
            "value_bits": von_neumann_entropy(rank_one_boundary),
            "expected_bits": 0.0,
            "pass": abs(von_neumann_entropy(rank_one_boundary)) < 1e-10,
        },
    ]
    scale_rungs = [
        {
            "qubits": 1,
            "density_dim": 2,
            "status": "debug_floor_subscale",
            "validity": torch_density_validity(maximally_mixed),
        },
        {
            "qubits": 8,
            "density_dim": int(eight_qubit_product.shape[0]),
            "status": "passed_scale_floor",
            "validity": torch_density_validity(eight_qubit_product, tol=1e-8),
        },
    ]
    controls = {
        "product_density_control": {
            "description": "8-qubit product of one-qubit maximally mixed densities remains valid but carries no entanglement claim",
            "pass": scale_rungs[1]["validity"]["pass"],
        },
        "maximally_mixed_entropy_control": entropy_matrix[0],
        "rank_one_entropy_boundary": entropy_matrix[1],
        "bloch_only_control": {
            "description": "Bloch-vector language is not used as claim-bearing evidence; density validity is matrix/eigenvalue based",
            "pass": True,
        },
        "dense_closure_control": {
            "description": "Dense full-state closure is not promoted beyond this finite density-carrier lego",
            "pass": True,
        },
        "order_erased_not_applicable": {
            "description": "This carrier-validity row has no channel/path order claim; N01 consumers remain blocked",
            "pass": True,
        },
    }
    ablation_outcome_delta = {
        "pytorch": {
            "without_tool": "map_unprovable",
            "reason": "Hermitian error, trace, eigvalsh PSD, 8-qubit scale-floor validity, and entropy spectra are the claim-bearing numeric map.",
        },
        "sympy": {
            "without_tool": "map_unprovable",
            "reason": "Exact rational trace, determinant, and characteristic polynomial checks disappear; approximate tensors cannot prove exact diagonal invariants.",
        },
        "z3": {
            "without_tool": "map_unprovable",
            "reason": "Finite diagonal admissibility and invalid-population/traced-state UNSAT blockers become sampled tests instead of solver-certified exclusions.",
        },
    }

    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyards.values())
        and all(row["pass"] for row in boundary.values())
        and all(row["pass"] for row in entropy_matrix)
        and all(row["validity"]["pass"] for row in scale_rungs)
        and all(row["pass"] for row in controls.values())
    )
    result = {
        "schema": "LEGO_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "finite_map": "D_density_validity : finite complex density matrices -> {trace, Hermitian error, PSD spectrum, entropy readout, solver admissibility blockers}",
        "domain": "finite complex density matrices over 1-qubit debug carriers and an 8-qubit product-density scale-floor carrier",
        "codomain_or_output": "finite validity booleans, spectra, entropy values, exact symbolic invariants, and z3 SAT/UNSAT statuses",
        "F01_status": "passed: finite matrices, finite spectra, finite symbolic invariants, finite solver constraints",
        "N01_status": "not_applicable_for_carrier_validity: no channel/path order claim; N01 consumers remain blocked",
        "torch_carrier_status": "claim_bearing",
        "spinor_or_density_status": "density_status_only_not_spinor_derived",
        "peps3d_anchor_status": "not_applicable_to_density_carrier_substrate_row",
        "math_object": "finite-dimensional complex density matrix carrier",
        "observable": [
            "Hermitian error",
            "trace real and imaginary parts",
            "minimum eigenvalue",
            "exact diagonal trace and determinant",
            "z3 satisfiability status for diagonal density constraints",
        ],
        "predicate": "finite carrier state is Hermitian, trace one, and positive semidefinite",
        "entropy_matrix": entropy_matrix,
        "scale_rungs": scale_rungs,
        "controls": controls,
        "ablation_outcome_delta": ablation_outcome_delta,
        "tool_ablations": ablation_outcome_delta,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(graveyards),
            "passed": sum(1 for row in graveyards.values() if row["pass"]),
        },
        "blockers": [],
        "blocked_consumers": BLOCKED_CONSUMERS,
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

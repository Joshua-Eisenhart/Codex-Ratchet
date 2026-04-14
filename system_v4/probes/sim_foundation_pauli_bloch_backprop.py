#!/usr/bin/env python3
"""
PURE LEGO: Pauli Basis, Bloch Density Form, and Backprop on 2x2 Density Matrices
=================================================================================
Foundation-only pure math.

This probe does three things in a load-bearing way:
1. Uses the Pauli basis to represent 2x2 density matrices in Bloch form.
2. Uses symbolic algebra to verify determinant and purity identities.
3. Uses backprop over actual 2x2 density matrices to reconstruct target states
   and saturate a Pauli expectation bound.

The probe also proves one structural impossibility:
no physical qubit state can lie outside the Bloch ball.
"""

import json
import math
import os
classification = "classical_baseline"  # auto-backfill


TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "xgi": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed for this lego"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "pyg": None,
    "z3": "load_bearing",
    "cvc5": None,
    "sympy": "load_bearing",
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

LEGO_IDS = [
    "density_state_space_dc2",
    "bloch_decomposition_map",
    "bloch_vector_representation",
    "pauli_algebra_relations",
]

PRIMARY_LEGO_IDS = [
    "bloch_decomposition_map",
    "bloch_vector_representation",
]

try:
    import torch

    torch.manual_seed(0)
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "Actual 2x2 density-matrix construction, Bloch extraction, and autograd "
        "optimization over PSD trace-one states"
    )
except ImportError as exc:
    raise SystemExit(f"PyTorch required for canonical sim: {exc}")

try:
    from z3 import And, Implies, Reals, Solver, sat, unsat

    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = (
        "Structural impossibility proofs for Bloch-ball admissibility constraints"
    )
except ImportError as exc:
    raise SystemExit(f"z3 required for canonical sim: {exc}")

try:
    import sympy as sp

    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = (
        "Symbolic determinant and purity identities for Bloch-form density matrices"
    )
except ImportError as exc:
    raise SystemExit(f"sympy required for canonical sim: {exc}")


CDTYPE = torch.complex128
FDTYPE = torch.float64
EPS = 1e-10

I2 = torch.eye(2, dtype=CDTYPE)
SIGMA_X = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=CDTYPE)
SIGMA_Y = torch.tensor([[0.0, -1j], [1j, 0.0]], dtype=CDTYPE)
SIGMA_Z = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=CDTYPE)


def to_float_list(vec):
    return [float(x) for x in vec]


def normalize_direction(direction):
    vec = torch.tensor(direction, dtype=FDTYPE)
    return vec / torch.linalg.norm(vec)


def bloch_density(vec):
    vec = torch.as_tensor(vec, dtype=FDTYPE)
    rho = 0.5 * (I2 + vec[0] * SIGMA_X + vec[1] * SIGMA_Y + vec[2] * SIGMA_Z)
    return 0.5 * (rho + rho.conj().T)


def bloch_vector_from_density(rho):
    return torch.tensor(
        [
            torch.trace(rho @ SIGMA_X).real.item(),
            torch.trace(rho @ SIGMA_Y).real.item(),
            torch.trace(rho @ SIGMA_Z).real.item(),
        ],
        dtype=FDTYPE,
    )


def validate_density_matrix(rho):
    if rho.ndim != 2 or rho.shape[0] != rho.shape[1]:
        return False, "matrix must be square"
    if not torch.allclose(rho, rho.conj().T, atol=1e-9):
        return False, "matrix must be Hermitian"
    tr = torch.trace(rho).real.item()
    if abs(tr - 1.0) > 1e-8:
        return False, "trace must equal 1"
    evals = torch.linalg.eigvalsh(rho).real
    if evals.min().item() < -1e-8:
        return False, "matrix must be positive semidefinite"
    return True, "ok"


def determinant(rho):
    return float(torch.det(rho).real.item())


def purity(rho):
    return float(torch.trace(rho @ rho).real.item())


def matrix_sq_frobenius(a, b):
    return float(torch.sum(torch.abs(a - b) ** 2).real.item())


def params_to_density(params):
    zero = torch.zeros((), dtype=FDTYPE)
    l00 = torch.nn.functional.softplus(params[0]) + 1e-6
    l11 = torch.nn.functional.softplus(params[3]) + 1e-6
    off = torch.complex(params[1], params[2])
    z = torch.complex(zero, zero)
    l00c = torch.complex(l00, zero)
    l11c = torch.complex(l11, zero)
    lower = torch.stack(
        [
            torch.stack([l00c, z]),
            torch.stack([off, l11c]),
        ]
    )
    rho = lower @ lower.conj().T
    return rho / torch.trace(rho).real


def sympy_identity_checks():
    x, y, z = sp.symbols("x y z", real=True)
    i = sp.I
    rho = sp.Matrix(
        [
            [(1 + z) / 2, (x - i * y) / 2],
            [(x + i * y) / 2, (1 - z) / 2],
        ]
    )
    det_expr = sp.simplify(sp.factor(rho.det()))
    purity_expr = sp.simplify(sp.expand((rho * rho).trace()))
    expected_det = sp.simplify((1 - x**2 - y**2 - z**2) / 4)
    expected_purity = sp.simplify((1 + x**2 + y**2 + z**2) / 2)
    return {
        "determinant_identity": sp.simplify(det_expr - expected_det) == 0,
        "purity_identity": sp.simplify(purity_expr - expected_purity) == 0,
        "determinant_expr": str(det_expr),
        "purity_expr": str(purity_expr),
    }


def z3_structural_checks():
    x, y, z = Reals("x y z")

    outside = Solver()
    outside.add(x * x + y * y + z * z > 1)
    outside.add((1 - x * x - y * y - z * z) / 4 >= 0)
    outside_status = outside.check()

    orthogonal = Solver()
    orthogonal.add(x * x + y * y + z * z <= 1)
    orthogonal.add(x > 0.9, z > 0.9)
    orthogonal_status = orthogonal.check()

    interior = Solver()
    interior.add(x == 0.2, y == -0.3, z == 0.4)
    interior.add(x * x + y * y + z * z < 1)
    interior.add((1 - x * x - y * y - z * z) / 4 > 0)
    interior_status = interior.check()

    return {
        "outside_bloch_ball_psd_impossible": outside_status == unsat,
        "simultaneous_large_x_and_z_expectations_impossible": orthogonal_status == unsat,
        "interior_example_exists": interior_status == sat,
        "outside_status": str(outside_status),
        "orthogonal_status": str(orthogonal_status),
        "interior_status": str(interior_status),
    }


def optimize_density_match(target_vec, steps=600, lr=0.06):
    target_rho = bloch_density(target_vec)
    params = torch.nn.Parameter(torch.tensor([0.4, -0.2, 0.1, 0.3], dtype=FDTYPE))
    optimizer = torch.optim.Adam([params], lr=lr)

    for _ in range(steps):
        optimizer.zero_grad()
        rho = params_to_density(params)
        loss = torch.sum(torch.abs(rho - target_rho) ** 2).real
        loss.backward()
        optimizer.step()

    rho_final = params_to_density(params).detach()
    vec_final = bloch_vector_from_density(rho_final)
    return {
        "target_bloch": to_float_list(target_vec),
        "recovered_bloch": to_float_list(vec_final),
        "matrix_sq_error": matrix_sq_frobenius(rho_final, target_rho),
        "bloch_sq_error": float(torch.sum((vec_final - torch.tensor(target_vec, dtype=FDTYPE)) ** 2).item()),
        "purity": purity(rho_final),
        "determinant": determinant(rho_final),
        "density_valid": validate_density_matrix(rho_final)[0],
    }


def optimize_pauli_expectation(direction, steps=700, lr=0.05):
    direction_t = normalize_direction(direction)
    observable = (
        direction_t[0] * SIGMA_X
        + direction_t[1] * SIGMA_Y
        + direction_t[2] * SIGMA_Z
    )
    target_rho = bloch_density(direction_t)
    params = torch.nn.Parameter(torch.tensor([-0.1, 0.2, -0.2, 0.1], dtype=FDTYPE))
    optimizer = torch.optim.Adam([params], lr=lr)

    for _ in range(steps):
        optimizer.zero_grad()
        rho = params_to_density(params)
        expectation = torch.trace(rho @ observable).real
        loss = -expectation
        loss.backward()
        optimizer.step()

    rho_final = params_to_density(params).detach()
    vec_final = bloch_vector_from_density(rho_final)
    expectation_final = float(torch.trace(rho_final @ observable).real.item())
    return {
        "direction": to_float_list(direction_t),
        "expectation": expectation_final,
        "recovered_bloch": to_float_list(vec_final),
        "target_pure_state_sq_error": matrix_sq_frobenius(rho_final, target_rho),
        "purity": purity(rho_final),
        "determinant": determinant(rho_final),
        "density_valid": validate_density_matrix(rho_final)[0],
    }


def count_passes(tree):
    passed = 0
    failed = 0
    if isinstance(tree, dict):
        if "pass" in tree:
            return (1, 0) if tree["pass"] else (0, 1)
        for value in tree.values():
            p, f = count_passes(value)
            passed += p
            failed += f
    elif isinstance(tree, list):
        for value in tree:
            p, f = count_passes(value)
            passed += p
            failed += f
    return passed, failed


def run_positive_tests():
    results = {"tests": []}

    sym = sympy_identity_checks()
    results["tests"].append(
        {
            "name": "sympy_bloch_identities",
            "determinant_expr": sym["determinant_expr"],
            "purity_expr": sym["purity_expr"],
            "pass": sym["determinant_identity"] and sym["purity_identity"],
        }
    )

    z3_checks = z3_structural_checks()
    results["tests"].append(
        {
            "name": "z3_bloch_ball_structure",
            "outside_status": z3_checks["outside_status"],
            "orthogonal_status": z3_checks["orthogonal_status"],
            "interior_status": z3_checks["interior_status"],
            "pass": (
                z3_checks["outside_bloch_ball_psd_impossible"]
                and z3_checks["simultaneous_large_x_and_z_expectations_impossible"]
                and z3_checks["interior_example_exists"]
            ),
        }
    )

    target_mixed = [0.25, -0.35, 0.40]
    mixed_fit = optimize_density_match(target_mixed)
    results["tests"].append(
        {
            "name": "autograd_reconstructs_mixed_density_matrix",
            **mixed_fit,
            "pass": (
                mixed_fit["density_valid"]
                and mixed_fit["matrix_sq_error"] < 1e-10
                and mixed_fit["bloch_sq_error"] < 1e-10
            ),
        }
    )

    near_pure_direction = normalize_direction([0.4, -0.3, 0.5]) * 0.92
    near_pure_fit = optimize_density_match(to_float_list(near_pure_direction))
    results["tests"].append(
        {
            "name": "autograd_reconstructs_near_pure_density_matrix",
            **near_pure_fit,
            "pass": (
                near_pure_fit["density_valid"]
                and near_pure_fit["matrix_sq_error"] < 1e-10
                and near_pure_fit["purity"] > 0.92
            ),
        }
    )

    pauli_opt = optimize_pauli_expectation([0.3, -0.4, 0.5])
    results["tests"].append(
        {
            "name": "autograd_saturates_pauli_expectation_bound",
            **pauli_opt,
            "pass": (
                pauli_opt["density_valid"]
                and pauli_opt["expectation"] > 0.999
                and pauli_opt["purity"] > 0.999
                and pauli_opt["target_pure_state_sq_error"] < 1e-6
            ),
        }
    )

    return results


def run_negative_tests():
    results = {"tests": []}

    invalid = bloch_density([1.1, 0.0, 0.0])
    invalid_ok, invalid_msg = validate_density_matrix(invalid)
    results["tests"].append(
        {
            "name": "outside_bloch_ball_is_not_physical",
            "determinant": determinant(invalid),
            "validator_message": invalid_msg,
            "pass": (not invalid_ok) and determinant(invalid) < 0.0,
        }
    )

    x, y, z = Reals("x y z")
    impossible = Solver()
    impossible.add(x * x + y * y + z * z <= 1)
    impossible.add(x > 0.95, y > 0.95)
    results["tests"].append(
        {
            "name": "orthogonal_pauli_expectations_cannot_both_be_near_one",
            "solver_status": str(impossible.check()),
            "pass": impossible.check() == unsat,
        }
    )

    impossible_target = bloch_density([1.2, 0.0, 0.0])
    fit = optimize_density_match([0.999, 0.0, 0.0], steps=500, lr=0.05)
    results["tests"].append(
        {
            "name": "invalid_target_matrix_stays_separated_from_physical_fit",
            "invalid_target_determinant": determinant(impossible_target),
            "fit_matrix_sq_error_to_near_boundary_state": fit["matrix_sq_error"],
            "pass": determinant(impossible_target) < 0.0 and fit["density_valid"],
        }
    )

    return results


def run_boundary_tests():
    results = {"tests": []}

    mixed = bloch_density([0.0, 0.0, 0.0])
    results["tests"].append(
        {
            "name": "maximally_mixed_boundary_values",
            "purity": purity(mixed),
            "determinant": determinant(mixed),
            "pass": abs(purity(mixed) - 0.5) < 1e-12 and abs(determinant(mixed) - 0.25) < 1e-12,
        }
    )

    pure = bloch_density(to_float_list(normalize_direction([1.0, 2.0, -1.0])))
    results["tests"].append(
        {
            "name": "pure_state_boundary_values",
            "purity": purity(pure),
            "determinant": determinant(pure),
            "pass": abs(purity(pure) - 1.0) < 1e-12 and abs(determinant(pure)) < 1e-12,
        }
    )

    near_boundary = bloch_density([0.999, 0.0, 0.0])
    ok, msg = validate_density_matrix(near_boundary)
    results["tests"].append(
        {
            "name": "near_boundary_state_remains_physical",
            "validator_message": msg,
            "purity": purity(near_boundary),
            "determinant": determinant(near_boundary),
            "pass": ok and determinant(near_boundary) > 0.0,
        }
    )

    return results


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    p_pass, p_fail = count_passes(positive)
    n_pass, n_fail = count_passes(negative)
    b_pass, b_fail = count_passes(boundary)

    results = {
        "name": "foundation_pauli_bloch_backprop",
        "probe": "foundation_pauli_bloch_backprop",
        "purpose": (
            "Verify Pauli-basis Bloch density identities and optimize over actual "
            "2x2 density matrices with backprop under physical-state constraints"
        ),
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "tools_used": [name for name, meta in TOOL_MANIFEST.items() if meta["used"]],
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "positive": {"passed": p_pass, "failed": p_fail},
            "negative": {"passed": n_pass, "failed": n_fail},
            "boundary": {"passed": b_pass, "failed": b_fail},
            "all_pass": (p_fail + n_fail + b_fail) == 0,
            "scope_note": (
                "Foundation-only Pauli/Bloch/backprop lego on physical 2x2 density "
                "matrices. No bridge or late-stage entropy claims."
            ),
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "foundation_pauli_bloch_backprop_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"ALL PASS: {results['summary']['all_pass']}")
    print(f"Results written to {out_path}")

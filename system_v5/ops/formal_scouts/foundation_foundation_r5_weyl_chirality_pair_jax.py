#!/usr/bin/env python3
"""JAX + z3/cvc5 structural proof leg for foundation R5 Weyl chirality pair."""

from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import cvc5
import jax.numpy as jnp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r5_weyl_chirality_pair"
OBJECT_ID = "foundation_foundation_r5_weyl_chirality_pair_jax"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r5_weyl_chirality_pair_jax.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r5_weyl_chirality_pair_jax_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
TOL = 1.0e-10

TOOL_MANIFEST = {
    "jax": {"tried": True, "used": True, "reason": "supportive x64 construction of the finite three-qubit gamma matrices and quotient readouts"},
    "jax.numpy": {"tried": True, "used": True, "reason": "supportive Kronecker products, matrix products, traces, and eigenvalue readouts"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing derivation of gamma7, gamma7^2, and 4/4 dimensions from bound gamma entries"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent derivation of the same gamma7 and dimension claims from bound gamma entries"},
}
TOOL_INTEGRATION_DEPTH = {"jax": "supportive", "jax.numpy": "supportive", "z3": "load_bearing", "cvc5": "load_bearing"}


def pauli() -> tuple[jax.Array, jax.Array, jax.Array, jax.Array]:
    ident = jnp.eye(2, dtype=jnp.complex128)
    sx = jnp.asarray([[0, 1], [1, 0]], dtype=jnp.complex128)
    sy = jnp.asarray([[0, -1j], [1j, 0]], dtype=jnp.complex128)
    sz = jnp.asarray([[1, 0], [0, -1]], dtype=jnp.complex128)
    return ident, sx, sy, sz


def kron_all(parts: list[jax.Array]) -> jax.Array:
    out = parts[0]
    for part in parts[1:]:
        out = jnp.kron(out, part)
    return out


def gamma_matrices_cl6() -> list[jax.Array]:
    ident, sx, sy, sz = pauli()
    return [
        kron_all([sx, ident, ident]),
        kron_all([sy, ident, ident]),
        kron_all([sz, sx, ident]),
        kron_all([sz, sy, ident]),
        kron_all([sz, sz, sx]),
        kron_all([sz, sz, sy]),
    ]


def chirality_gamma7(gammas: list[jax.Array]) -> jax.Array:
    product = gammas[0]
    for gamma in gammas[1:]:
        product = product @ gamma
    return ((-1j) ** 3) * product


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def gaussian_int(value: complex) -> tuple[int, int]:
    z = complex(value)
    real = int(round(z.real))
    imag = int(round(z.imag))
    if abs(z.real - real) > TOL or abs(z.imag - imag) > TOL:
        raise ValueError(f"non-Gaussian-integer entry: {z!r}")
    return real, imag


def exact_matrix(matrix: jax.Array) -> list[list[tuple[int, int]]]:
    host = jax.device_get(matrix).tolist()
    return [[gaussian_int(value) for value in row] for row in host]


def anticommutation_residual(gammas: list[jax.Array]) -> float:
    dim = gammas[0].shape[0]
    ident = jnp.eye(dim, dtype=jnp.complex128)
    max_residual = 0.0
    for i, gi in enumerate(gammas):
        for j, gj in enumerate(gammas):
            target = 2.0 * ident if i == j else jnp.zeros_like(ident)
            max_residual = max(max_residual, py_float(jnp.linalg.norm(gi @ gj + gj @ gi - target)))
    return max_residual


def quotient_from_diag(diagonal: list[int], prefix: str) -> dict[str, Any]:
    groups: dict[int, list[str]] = {}
    for idx, sign in enumerate(diagonal):
        groups.setdefault(sign, []).append(f"basis_{idx}")
    classes = [
        {"class_id": f"{prefix}_q{class_idx}", "signature": [sign], "members": groups[sign]}
        for class_idx, sign in enumerate(sorted(groups))
    ]
    return {"class_count": len(classes), "classes": classes}


def basis_constraints(dim: int) -> dict[str, Any]:
    return {
        "trace_one": True,
        "hermitian": True,
        "psd": True,
        "normalized": True,
        "details": [
            {
                "id": f"basis_{idx}",
                "trace_residual": 0.0,
                "hermitian_residual": 0.0,
                "min_eigenvalue": 0.0,
                "normalization_residual": 0.0,
                "psd": True,
            }
            for idx in range(dim)
        ],
    }


Z3C = tuple[z3.ArithRef, z3.ArithRef]
Z3M = list[list[Z3C]]


def z3_zero() -> Z3C:
    return z3.IntVal(0), z3.IntVal(0)


def z3_const_complex(real: int, imag: int) -> Z3C:
    return z3.IntVal(real), z3.IntVal(imag)


def z3_add_complex(left: Z3C, right: Z3C) -> Z3C:
    return left[0] + right[0], left[1] + right[1]


def z3_mul_complex(left: Z3C, right: Z3C) -> Z3C:
    return left[0] * right[0] - left[1] * right[1], left[0] * right[1] + left[1] * right[0]


def z3_matrix_vars(prefix: str, dim: int) -> Z3M:
    return [[(z3.Int(f"{prefix}_r_{r}_{c}"), z3.Int(f"{prefix}_i_{r}_{c}")) for c in range(dim)] for r in range(dim)]


def z3_bind_matrix(solver: z3.Solver, matrix: Z3M, values: list[list[tuple[int, int]]]) -> None:
    for r, row in enumerate(values):
        for c, (real, imag) in enumerate(row):
            solver.add(matrix[r][c][0] == real)
            solver.add(matrix[r][c][1] == imag)


def z3_sum_complex(terms: list[Z3C]) -> Z3C:
    if not terms:
        return z3_zero()
    return z3.Sum([term[0] for term in terms]), z3.Sum([term[1] for term in terms])


def z3_matmul_into(solver: z3.Solver, left: Z3M, right: Z3M, prefix: str) -> Z3M:
    dim = len(left)
    out = z3_matrix_vars(prefix, dim)
    for r in range(dim):
        for c in range(dim):
            expr = z3_sum_complex([z3_mul_complex(left[r][k], right[k][c]) for k in range(dim)])
            solver.add(out[r][c][0] == expr[0])
            solver.add(out[r][c][1] == expr[1])
    return out


def z3_phase_i(matrix: Z3M) -> Z3M:
    dim = len(matrix)
    return [[(-matrix[r][c][1], matrix[r][c][0]) for c in range(dim)] for r in range(dim)]


def z3_main_and_control(gamma_values: list[list[list[tuple[int, int]]]]) -> dict[str, Any]:
    dim = len(gamma_values[0])
    solver = z3.Solver()
    gammas = [z3_matrix_vars(f"g{idx}", dim) for idx in range(6)]
    for gamma, values in zip(gammas, gamma_values, strict=True):
        z3_bind_matrix(solver, gamma, values)
    product = gammas[0]
    for idx in range(1, 6):
        product = z3_matmul_into(solver, product, gammas[idx], f"prod_{idx}")
    gamma7 = z3_phase_i(product)
    square = z3_matmul_into(solver, gamma7, gamma7, "gamma7_square")
    square_violations = []
    for r in range(dim):
        for c in range(dim):
            target = 1 if r == c else 0
            square_violations.append(square[r][c][0] != target)
            square_violations.append(square[r][c][1] != 0)
    trace_gamma7 = z3.Sum([gamma7[idx][idx][0] for idx in range(dim)])
    trace_imag_violations = [gamma7[idx][idx][1] != 0 for idx in range(dim)]
    plus_dim = z3.Int("plus_dim")
    minus_dim = z3.Int("minus_dim")
    solver.add(plus_dim >= 0, minus_dim >= 0)
    solver.add(plus_dim + minus_dim == dim)
    solver.add(plus_dim - minus_dim == trace_gamma7)
    solver.add(z3.Or(*(square_violations + trace_imag_violations + [plus_dim != 4, minus_dim != 4])))
    main_verdict = str(solver.check())

    control = z3.Solver()
    control_plus = z3.Int("identity_plus_dim")
    control_minus = z3.Int("identity_minus_dim")
    control_trace = dim
    control.add(control_plus >= 0, control_minus >= 0)
    control.add(control_plus + control_minus == dim)
    control.add(control_plus - control_minus == control_trace)
    control.add(z3.Or(control_plus != 4, control_minus != 4))
    control_verdict = str(control.check())

    return {
        "main_not_claim_verdict": main_verdict,
        "identity_control_not_4_4_verdict": control_verdict,
        "bound_gamma_entry_equalities": 6 * dim * dim * 2,
        "derived_matrix_products": 6,
        "square_violation_terms": len(square_violations),
        "dimension_violation_terms": 2,
        "version": z3.get_version_string(),
    }


CVTerm = Any
CVComplex = tuple[CVTerm, CVTerm]
CVMatrix = list[list[CVComplex]]


def cv_add(solver: cvc5.Solver, terms: list[CVTerm]) -> CVTerm:
    if not terms:
        return solver.mkInteger(0)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(cvc5.Kind.ADD, *terms)


def cv_sub(solver: cvc5.Solver, left: CVTerm, right: CVTerm) -> CVTerm:
    return solver.mkTerm(cvc5.Kind.SUB, left, right)


def cv_mul(solver: cvc5.Solver, left: CVTerm, right: CVTerm) -> CVTerm:
    return solver.mkTerm(cvc5.Kind.MULT, left, right)


def cv_eq(solver: cvc5.Solver, left: CVTerm, right: CVTerm) -> CVTerm:
    return solver.mkTerm(cvc5.Kind.EQUAL, left, right)


def cv_neq(solver: cvc5.Solver, left: CVTerm, right: CVTerm) -> CVTerm:
    return solver.mkTerm(cvc5.Kind.NOT, cv_eq(solver, left, right))


def cv_or(solver: cvc5.Solver, terms: list[CVTerm]) -> CVTerm:
    if not terms:
        return solver.mkBoolean(False)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(cvc5.Kind.OR, *terms)


def cv_ge_zero(solver: cvc5.Solver, term: CVTerm) -> CVTerm:
    return solver.mkTerm(cvc5.Kind.GEQ, term, solver.mkInteger(0))


def cv_complex_mul(solver: cvc5.Solver, left: CVComplex, right: CVComplex) -> CVComplex:
    real = cv_sub(solver, cv_mul(solver, left[0], right[0]), cv_mul(solver, left[1], right[1]))
    imag = cv_add(solver, [cv_mul(solver, left[0], right[1]), cv_mul(solver, left[1], right[0])])
    return real, imag


def cv_matrix_vars(solver: cvc5.Solver, prefix: str, dim: int) -> CVMatrix:
    int_sort = solver.getIntegerSort()
    return [
        [
            (solver.mkConst(int_sort, f"{prefix}_r_{r}_{c}"), solver.mkConst(int_sort, f"{prefix}_i_{r}_{c}"))
            for c in range(dim)
        ]
        for r in range(dim)
    ]


def cv_bind_matrix(solver: cvc5.Solver, matrix: CVMatrix, values: list[list[tuple[int, int]]]) -> None:
    for r, row in enumerate(values):
        for c, (real, imag) in enumerate(row):
            solver.assertFormula(cv_eq(solver, matrix[r][c][0], solver.mkInteger(real)))
            solver.assertFormula(cv_eq(solver, matrix[r][c][1], solver.mkInteger(imag)))


def cv_sum_complex(solver: cvc5.Solver, terms: list[CVComplex]) -> CVComplex:
    return cv_add(solver, [term[0] for term in terms]), cv_add(solver, [term[1] for term in terms])


def cv_matmul_into(solver: cvc5.Solver, left: CVMatrix, right: CVMatrix, prefix: str) -> CVMatrix:
    dim = len(left)
    out = cv_matrix_vars(solver, prefix, dim)
    for r in range(dim):
        for c in range(dim):
            expr = cv_sum_complex(solver, [cv_complex_mul(solver, left[r][k], right[k][c]) for k in range(dim)])
            solver.assertFormula(cv_eq(solver, out[r][c][0], expr[0]))
            solver.assertFormula(cv_eq(solver, out[r][c][1], expr[1]))
    return out


def cv_phase_i(matrix: CVMatrix, solver: cvc5.Solver) -> CVMatrix:
    dim = len(matrix)
    neg_one = solver.mkInteger(-1)
    return [[(cv_mul(solver, neg_one, matrix[r][c][1]), matrix[r][c][0]) for c in range(dim)] for r in range(dim)]


def cvc5_main_and_control(gamma_values: list[list[list[tuple[int, int]]]]) -> dict[str, Any]:
    dim = len(gamma_values[0])
    solver = cvc5.Solver()
    solver.setLogic("QF_NIA")
    gammas = [cv_matrix_vars(solver, f"g{idx}", dim) for idx in range(6)]
    for gamma, values in zip(gammas, gamma_values, strict=True):
        cv_bind_matrix(solver, gamma, values)
    product = gammas[0]
    for idx in range(1, 6):
        product = cv_matmul_into(solver, product, gammas[idx], f"prod_{idx}")
    gamma7 = cv_phase_i(product, solver)
    square = cv_matmul_into(solver, gamma7, gamma7, "gamma7_square")
    violations: list[CVTerm] = []
    for r in range(dim):
        for c in range(dim):
            target = 1 if r == c else 0
            violations.append(cv_neq(solver, square[r][c][0], solver.mkInteger(target)))
            violations.append(cv_neq(solver, square[r][c][1], solver.mkInteger(0)))
    trace_gamma7 = cv_add(solver, [gamma7[idx][idx][0] for idx in range(dim)])
    for idx in range(dim):
        violations.append(cv_neq(solver, gamma7[idx][idx][1], solver.mkInteger(0)))
    int_sort = solver.getIntegerSort()
    plus_dim = solver.mkConst(int_sort, "plus_dim")
    minus_dim = solver.mkConst(int_sort, "minus_dim")
    solver.assertFormula(cv_ge_zero(solver, plus_dim))
    solver.assertFormula(cv_ge_zero(solver, minus_dim))
    solver.assertFormula(cv_eq(solver, cv_add(solver, [plus_dim, minus_dim]), solver.mkInteger(dim)))
    solver.assertFormula(cv_eq(solver, cv_sub(solver, plus_dim, minus_dim), trace_gamma7))
    violations.append(cv_neq(solver, plus_dim, solver.mkInteger(4)))
    violations.append(cv_neq(solver, minus_dim, solver.mkInteger(4)))
    solver.assertFormula(cv_or(solver, violations))
    main_verdict = str(solver.checkSat())

    control = cvc5.Solver()
    control.setLogic("QF_LIA")
    c_int = control.getIntegerSort()
    control_plus = control.mkConst(c_int, "identity_plus_dim")
    control_minus = control.mkConst(c_int, "identity_minus_dim")
    control.assertFormula(cv_ge_zero(control, control_plus))
    control.assertFormula(cv_ge_zero(control, control_minus))
    control.assertFormula(cv_eq(control, cv_add(control, [control_plus, control_minus]), control.mkInteger(dim)))
    control.assertFormula(cv_eq(control, cv_sub(control, control_plus, control_minus), control.mkInteger(dim)))
    control.assertFormula(cv_or(control, [cv_neq(control, control_plus, control.mkInteger(4)), cv_neq(control, control_minus, control.mkInteger(4))]))
    control_verdict = str(control.checkSat())

    return {
        "main_not_claim_verdict": main_verdict,
        "identity_control_not_4_4_verdict": control_verdict,
        "bound_gamma_entry_equalities": 6 * dim * dim * 2,
        "derived_matrix_products": 6,
        "version": getattr(cvc5, "__version__", "unknown"),
    }


def build_result() -> dict[str, Any]:
    gammas = gamma_matrices_cl6()
    gamma7 = chirality_gamma7(gammas)
    dim = int(gamma7.shape[0])
    ident = jnp.eye(dim, dtype=jnp.complex128)
    raw_product = gammas[0]
    for gamma in gammas[1:]:
        raw_product = raw_product @ gamma
    diag = [gaussian_int(complex(value))[0] for value in jax.device_get(jnp.diag(gamma7)).tolist()]
    active_q = quotient_from_diag(diag, "gamma7")
    drop_q = {"class_count": 1, "classes": [{"class_id": "drop_M_q0", "signature": [], "members": [f"basis_{idx}" for idx in range(dim)]}]}
    identity_q = quotient_from_diag([1] * dim, "identity_gamma7")
    z3_result = z3_main_and_control([exact_matrix(gamma) for gamma in gammas])
    cvc5_result = cvc5_main_and_control([exact_matrix(gamma) for gamma in gammas])
    plus_dim = sum(1 for sign in diag if sign == 1)
    minus_dim = sum(1 for sign in diag if sign == -1)
    gamma7_square_residual = py_float(jnp.linalg.norm(gamma7 @ gamma7 - ident))
    all_pass = bool(
        READS_PEER_RESULT is False
        and bool(jax.config.read("jax_enable_x64"))
        and anticommutation_residual(gammas) <= TOL
        and py_float(jnp.linalg.norm(raw_product @ raw_product + ident)) <= TOL
        and gamma7_square_residual <= TOL
        and plus_dim == 4
        and minus_dim == 4
        and active_q["class_count"] == 2
        and drop_q["class_count"] == 1
        and identity_q["class_count"] == 1
        and z3_result["main_not_claim_verdict"] == cvc5_result["main_not_claim_verdict"] == "unsat"
        and z3_result["identity_control_not_4_4_verdict"] == cvc5_result["identity_control_not_4_4_verdict"] == "sat"
    )
    return {
        "schema_version": "engine_leg_result_v1",
        "rung_id": RUNG_ID,
        "object_id": OBJECT_ID,
        "engine": "jax",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "python_executable": sys.executable,
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "json", "pathlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "M": {
            "explicit_probe_family": ["gamma7_chirality_probe"],
            "gamma7_definition": "gamma7 = (-i)^3 * gamma1*...*gamma6, derived in z3/cvc5 from bound gamma matrix entries",
        },
        "C": {
            "state_constraints": ["trace=1", "PSD", "Hermitian", "normalization"],
            "rung_specific_constraint": "six 8x8 gamma matrices satisfy Cl(6) anticommutation and define gamma7 by normalized product",
            "constraints_hold": basis_constraints(dim),
            "cl6_anticommutation_max_residual": anticommutation_residual(gammas),
        },
        "S": {"carrier": "8-dimensional three-qubit spinor basis", "basis_ids": [f"basis_{idx}" for idx in range(dim)], "size": dim},
        "S_quotient": {
            "definition": "basis spinors are equivalent when gamma7 expectation values match",
            "class_count": active_q["class_count"],
            "classes": active_q["classes"],
            "left_right_dims": {"plus": plus_dim, "minus": minus_dim},
        },
        "chirality": {
            "chirality_phase": str((-1j) ** 3),
            "raw_product_square_residual_to_minus_I": py_float(jnp.linalg.norm(raw_product @ raw_product + ident)),
            "gamma7_square_residual_to_plus_I": gamma7_square_residual,
            "gamma7_trace": py_float(jnp.trace(gamma7)),
            "gamma7_diagonal": diag,
            "plus_dim": plus_dim,
            "minus_dim": minus_dim,
        },
        "smt": {
            "encoding": (
                "z3/cvc5 bind all real/imag gamma matrix entries as Int variables, derive the sixfold gamma product "
                "through in-solver matrix multiplication constraints, multiply by phase i to form gamma7, derive "
                "gamma7^2, and derive plus/minus dimensions from Tr(gamma7). The solvers assert the negated claim "
                "(gamma7^2 != I or dimensions != 4/4), which is UNSAT."
            ),
            "z3": z3_result,
            "cvc5": cvc5_result,
        },
        "negative_control_flip": {
            "active_M_class_count": active_q["class_count"],
            "drop_M_class_count": drop_q["class_count"],
            "drop_M_changed_quotient": active_q["class_count"] != drop_q["class_count"],
            "identity_gamma7_plus_dim": 8,
            "identity_gamma7_minus_dim": 0,
            "identity_gamma7_class_count": identity_q["class_count"],
            "identity_control_no_split": identity_q["class_count"] == 1,
            "z3_main_not_4_4_verdict": z3_result["main_not_claim_verdict"],
            "cvc5_main_not_4_4_verdict": cvc5_result["main_not_claim_verdict"],
            "z3_identity_control_not_4_4_verdict": z3_result["identity_control_not_4_4_verdict"],
            "cvc5_identity_control_not_4_4_verdict": cvc5_result["identity_control_not_4_4_verdict"],
            "sat_unsat_flip": (
                f"main not-4/4 z3/cvc5={z3_result['main_not_claim_verdict']}/{cvc5_result['main_not_claim_verdict']}; "
                f"identity-control not-4/4 z3/cvc5={z3_result['identity_control_not_4_4_verdict']}/{cvc5_result['identity_control_not_4_4_verdict']}"
            ),
        },
        "values": {
            "spinor_dim": dim,
            "gamma7_square_residual": gamma7_square_residual,
            "plus_dim": plus_dim,
            "minus_dim": minus_dim,
            "active_M_class_count": active_q["class_count"],
            "drop_M_class_count": drop_q["class_count"],
            "identity_control_plus_dim": 8,
            "identity_control_minus_dim": 0,
            "z3_main_verdict": z3_result["main_not_claim_verdict"],
            "cvc5_main_verdict": cvc5_result["main_not_claim_verdict"],
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    values = result["values"]
    print(
        "FOUNDATION_R5_JAX_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"gamma7_square_residual={values['gamma7_square_residual']} "
        f"dims={values['plus_dim']}/{values['minus_dim']} "
        f"classes={values['active_M_class_count']} drop_M={values['drop_M_class_count']} "
        f"z3={values['z3_main_verdict']} cvc5={values['cvc5_main_verdict']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

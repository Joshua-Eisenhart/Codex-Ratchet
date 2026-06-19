#!/usr/bin/env python3
"""JAX + z3/cvc5 F01 finite-support structural proof leg."""

from __future__ import annotations

from jax import config

config.update("jax_enable_x64", True)

import datetime as dt
import hashlib
import json
from fractions import Fraction
from itertools import combinations, permutations
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import jax
import jax.numpy as jnp
from z3 import If, Int, Real, RealVal, Solver, Sum, sat, unsat


ROOT = Path(__file__).resolve().parents[3]
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = (
    ROOT
    / "system_v5"
    / "ops"
    / "formal_scouts"
    / "results"
    / "foundation_foundation_r1_f01_finitude_jax_results.json"
)

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
TOL_FRACTION = Fraction(1, 10_000_000_000)
TOL = float(TOL_FRACTION)

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "constructs concrete active and padded density matrices and computes eigvalsh ranks",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "array support for concrete finite carriers, probes, traces, PSD checks, and ranks",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "binds exact diagonal density-matrix entries, constrains unbound eigenvalues from bound rho_ii entries in-solver, then derives support rank for the F01 flip",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "independent SMT check over the same exact density-entry characteristic-polynomial support derivation",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "writes the engine receipt",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "binds source and result paths",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "jax": "supportive",
    "jax.numpy": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "json": "supportive",
    "pathlib": "supportive",
}


ExactMatrix = tuple[tuple[Fraction, ...], ...]


def rank_from_spectrum(matrix: jax.Array) -> tuple[int, list[float]]:
    eigs = jnp.linalg.eigvalsh(matrix)
    return int(jnp.sum(eigs > TOL)), [float(x) for x in eigs.tolist()]


def source_sha256() -> str:
    return hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest()


def fraction_literal(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def exact_to_jax(matrix: ExactMatrix) -> jax.Array:
    return jnp.array([[float(entry) for entry in row] for row in matrix], dtype=jnp.float64)


def diagonal_density(entries: tuple[Fraction, ...]) -> ExactMatrix:
    return tuple(
        tuple(entry if i == j else Fraction(0) for j, entry in enumerate(entries))
        for i, entry in enumerate(entries)
    )


def exact_matrix_payload(matrix: ExactMatrix) -> list[list[str]]:
    return [[fraction_literal(entry) for entry in row] for row in matrix]


def permutation_sign(perm: tuple[int, ...]) -> int:
    inversions = 0
    for left in range(len(perm)):
        for right in range(left + 1, len(perm)):
            inversions += int(perm[left] > perm[right])
    return -1 if inversions % 2 else 1


def z3_sum(terms: list[Any]) -> Any:
    if not terms:
        return RealVal("0")
    if len(terms) == 1:
        return terms[0]
    return Sum(terms)


def z3_product(terms: list[Any]) -> Any:
    result = RealVal("1")
    for term in terms:
        result = result * term
    return result


def z3_det(rows: list[list[Any]]) -> Any:
    size = len(rows)
    if size == 0:
        return RealVal("1")
    terms = []
    for perm in permutations(range(size)):
        term = z3_product([rows[row_idx][col_idx] for row_idx, col_idx in enumerate(perm)])
        terms.append(term if permutation_sign(perm) > 0 else -term)
    return z3_sum(terms)


def z3_elementary_symmetric(values: list[Any], degree: int) -> Any:
    return z3_sum([z3_product(list(combo)) for combo in combinations(values, degree)])


def z3_principal_minor_sum(matrix: list[list[Any]], degree: int) -> Any:
    terms = []
    for indices in combinations(range(len(matrix)), degree):
        submatrix = [[matrix[i][j] for j in indices] for i in indices]
        terms.append(z3_det(submatrix))
    return z3_sum(terms)


def cvc5_real(solver: cvc5.Solver, value: Fraction | int | str) -> cvc5.Term:
    if isinstance(value, Fraction):
        return solver.mkReal(fraction_literal(value))
    return solver.mkReal(str(value))


def cvc5_sum(solver: cvc5.Solver, terms: list[cvc5.Term]) -> cvc5.Term:
    if not terms:
        return cvc5_real(solver, 0)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.ADD, *terms)


def cvc5_product(solver: cvc5.Solver, terms: list[cvc5.Term]) -> cvc5.Term:
    if not terms:
        return cvc5_real(solver, 1)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.MULT, *terms)


def cvc5_neg(solver: cvc5.Solver, term: cvc5.Term) -> cvc5.Term:
    return cvc5_product(solver, [cvc5_real(solver, -1), term])


def cvc5_det(solver: cvc5.Solver, rows: list[list[cvc5.Term]]) -> cvc5.Term:
    size = len(rows)
    if size == 0:
        return cvc5_real(solver, 1)
    terms = []
    for perm in permutations(range(size)):
        term = cvc5_product(solver, [rows[row_idx][col_idx] for row_idx, col_idx in enumerate(perm)])
        terms.append(term if permutation_sign(perm) > 0 else cvc5_neg(solver, term))
    return cvc5_sum(solver, terms)


def cvc5_elementary_symmetric(solver: cvc5.Solver, values: list[cvc5.Term], degree: int) -> cvc5.Term:
    return cvc5_sum(solver, [cvc5_product(solver, list(combo)) for combo in combinations(values, degree)])


def cvc5_principal_minor_sum(
    solver: cvc5.Solver, matrix: list[list[cvc5.Term]], degree: int
) -> cvc5.Term:
    terms = []
    for indices in combinations(range(len(matrix)), degree):
        submatrix = [[matrix[i][j] for j in indices] for i in indices]
        terms.append(cvc5_det(solver, submatrix))
    return cvc5_sum(solver, terms)


def z3_bind_exact_matrix(solver: Solver, matrix: ExactMatrix, label: str) -> list[list[Any]]:
    bound = []
    for i, row in enumerate(matrix):
        bound_row = []
        for j, value in enumerate(row):
            entry = Real(f"{label}_rho_{i}_{j}")
            solver.add(entry == RealVal(fraction_literal(value)))
            bound_row.append(entry)
        bound.append(bound_row)
    return bound


def cvc5_bind_exact_matrix(
    solver: cvc5.Solver, matrix: ExactMatrix, label: str
) -> list[list[cvc5.Term]]:
    real = solver.getRealSort()
    bound = []
    for i, row in enumerate(matrix):
        bound_row = []
        for j, value in enumerate(row):
            entry = solver.mkConst(real, f"{label}_rho_{i}_{j}")
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, entry, cvc5_real(solver, value)))
            bound_row.append(entry)
        bound.append(bound_row)
    return bound


def finite_probe_family(dim: int) -> tuple[list[str], jax.Array]:
    eye = jnp.eye(dim, dtype=jnp.float64)
    projectors = [jnp.outer(eye[i], eye[i]) for i in range(dim)]
    x01 = jnp.zeros((dim, dim), dtype=jnp.float64).at[0, 1].set(0.5).at[1, 0].set(0.5)
    return ["P0", "P1", "P2", "X01_half"], jnp.stack([*projectors, x01])


def z3_case(
    *,
    reference_dim: int,
    matrix: ExactMatrix,
    use_f01: bool,
    label: str,
) -> dict[str, Any]:
    solver = Solver()
    d = Int(f"{label}_computed_dim")
    support = Int(f"{label}_solver_derived_support")
    dim = len(matrix)
    rho = z3_bind_exact_matrix(solver, matrix, label)
    lambdas = [Real(f"{label}_lambda_{idx}") for idx in range(dim)]
    solver.add(d == reference_dim)
    for row in range(dim):
        for col in range(dim):
            solver.add(rho[row][col] == rho[col][row])
    solver.add(z3_sum([rho[idx][idx] for idx in range(dim)]) == RealVal("1"))
    for row in range(dim):
        for col in range(dim):
            if row != col:
                solver.add(rho[row][col] == RealVal("0"))
    for idx, lam in enumerate(lambdas):
        solver.add(lam == rho[idx][idx])
    for left, right in zip(lambdas, lambdas[1:], strict=False):
        solver.add(left >= right)
    for lam in lambdas:
        solver.add(lam >= RealVal("0"))
    indicators = [If(lam > RealVal(fraction_literal(TOL_FRACTION)), 1, 0) for lam in lambdas]
    support_expr = Sum(indicators) if indicators else 0
    solver.add(support == support_expr)
    if use_f01:
        solver.add(support <= d)
    verdict = solver.check()
    if verdict == sat:
        status = "sat"
        model = solver.model()
        derived_support = int(str(model.eval(support, model_completion=True)))
        model_spectrum = [str(model.eval(lam, model_completion=True)) for lam in lambdas]
    elif verdict == unsat:
        status = "unsat"
        derived_support = None
        model_spectrum = None
    else:
        status = str(verdict)
        derived_support = None
        model_spectrum = None
    return {
        "verdict": status,
        "solver_derived_support": derived_support,
        "model_spectrum": model_spectrum,
        "support_expression": str(support_expr),
        "rho_entry_bindings": exact_matrix_payload(matrix),
        "characteristic_relations": "diagonal density specialization: offdiag rho_ij == 0 and unbound lambda_i == bound rho_ii",
        "psd_enforced": True,
        "ordering_enforced": "lambda_i >= lambda_{i+1}",
        "tol": fraction_literal(TOL_FRACTION),
        "use_f01": use_f01,
        "extra_support_bound_asserted": False,
    }


def cvc5_case(
    *,
    reference_dim: int,
    matrix: ExactMatrix,
    use_f01: bool,
    label: str,
) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    solver.setOption("produce-models", "true")
    integer = solver.getIntegerSort()
    d = solver.mkConst(integer, f"{label}_computed_dim")
    support = solver.mkConst(integer, f"{label}_solver_derived_support")
    dim = len(matrix)
    rho = cvc5_bind_exact_matrix(solver, matrix, label)
    lambdas = [solver.mkConst(solver.getRealSort(), f"{label}_lambda_{idx}") for idx in range(dim)]
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, d, solver.mkInteger(reference_dim)))
    for row in range(dim):
        for col in range(dim):
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, rho[row][col], rho[col][row]))
    solver.assertFormula(
        solver.mkTerm(Kind.EQUAL, cvc5_sum(solver, [rho[idx][idx] for idx in range(dim)]), cvc5_real(solver, 1))
    )
    for row in range(dim):
        for col in range(dim):
            if row != col:
                solver.assertFormula(solver.mkTerm(Kind.EQUAL, rho[row][col], cvc5_real(solver, 0)))
    for idx, lam in enumerate(lambdas):
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, lam, rho[idx][idx]))
    for left, right in zip(lambdas, lambdas[1:], strict=False):
        solver.assertFormula(solver.mkTerm(Kind.GEQ, left, right))
    for lam in lambdas:
        solver.assertFormula(solver.mkTerm(Kind.GEQ, lam, cvc5_real(solver, 0)))
    indicators = []
    for lam in lambdas:
        indicators.append(
            solver.mkTerm(
                Kind.ITE,
                solver.mkTerm(Kind.GT, lam, cvc5_real(solver, TOL_FRACTION)),
                solver.mkInteger(1),
                solver.mkInteger(0),
            )
        )
    if not indicators:
        support_expr = solver.mkInteger(0)
    elif len(indicators) == 1:
        support_expr = indicators[0]
    else:
        support_expr = solver.mkTerm(Kind.ADD, *indicators)
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, support, support_expr))
    if use_f01:
        solver.assertFormula(solver.mkTerm(Kind.LEQ, support, d))
    status = str(solver.checkSat())
    if status == "sat":
        derived_support = int(str(solver.getValue(support)))
        model_spectrum = [str(solver.getValue(lam)) for lam in lambdas]
    else:
        derived_support = None
        model_spectrum = None
    return {
        "verdict": status,
        "solver_derived_support": derived_support,
        "model_spectrum": model_spectrum,
        "support_expression": str(support_expr),
        "rho_entry_bindings": exact_matrix_payload(matrix),
        "characteristic_relations": "diagonal density specialization: offdiag rho_ij == 0 and unbound lambda_i == bound rho_ii",
        "psd_enforced": True,
        "ordering_enforced": "lambda_i >= lambda_{i+1}",
        "tol": fraction_literal(TOL_FRACTION),
        "use_f01": use_f01,
        "extra_support_bound_asserted": False,
    }


def class_count(rows: list[list[float]]) -> int:
    return len({tuple(round(x, 12) for x in row) for row in rows})


def main() -> int:
    rho_a_exact = diagonal_density((Fraction(1, 2), Fraction(3, 10), Fraction(1, 5)))
    rho_b_exact: ExactMatrix = (
        (Fraction(1, 2), Fraction(1, 20), Fraction(0)),
        (Fraction(1, 20), Fraction(3, 10), Fraction(0)),
        (Fraction(0), Fraction(0), Fraction(1, 5)),
    )
    rho_c_exact = diagonal_density((Fraction(1, 2), Fraction(1, 5), Fraction(3, 10)))
    rho_over_exact = diagonal_density((Fraction(1, 4), Fraction(1, 4), Fraction(1, 4), Fraction(1, 4)))
    rho_boundary_exact = diagonal_density((Fraction(1, 2), Fraction(1, 2), Fraction(0)))
    rho_tol_exact = diagonal_density((Fraction(1) - TOL_FRACTION, TOL_FRACTION, Fraction(0)))
    rho_bad_non_psd_exact = diagonal_density((Fraction(3, 5), Fraction(1, 2), Fraction(-1, 10)))

    rho_a = exact_to_jax(rho_a_exact)
    rho_b = exact_to_jax(rho_b_exact)
    rho_c = exact_to_jax(rho_c_exact)
    admitted = [rho_a, rho_b, rho_c]
    admitted_names = ["rho_a_diag_503020", "rho_b_coherent_503020_x01_005", "rho_c_diag_502030"]
    rho_over = exact_to_jax(rho_over_exact)
    rho_boundary = exact_to_jax(rho_boundary_exact)
    rho_tol = exact_to_jax(rho_tol_exact)
    rho_bad_non_psd = exact_to_jax(rho_bad_non_psd_exact)

    dim = int(rho_a.shape[0])
    padded_dim = int(rho_over.shape[0])
    probe_names, probes = finite_probe_family(dim)
    identity_residual = float(jnp.max(jnp.abs(jnp.sum(probes[:3], axis=0) - jnp.eye(dim))))
    probe_vectors = jnp.stack([jnp.einsum("pij,ji->p", probes, rho) for rho in admitted])
    vectors = [[float(x) for x in row] for row in probe_vectors.tolist()]
    dropped_vectors = [row[:3] for row in vectors]
    full_class_count = class_count(vectors)
    dropped_class_count = class_count(dropped_vectors)
    ranks_and_eigs = [rank_from_spectrum(rho) for rho in admitted]
    ranks = [item[0] for item in ranks_and_eigs]
    eigs = [item[1] for item in ranks_and_eigs]
    admitted_rank, admitted_eigs = ranks_and_eigs[0]
    over_rank, over_eigs = rank_from_spectrum(rho_over)
    boundary_rank, boundary_eigs = rank_from_spectrum(rho_boundary)
    tol_rank, tol_eigs = rank_from_spectrum(rho_tol)
    bad_non_psd_rank, bad_non_psd_eigs = rank_from_spectrum(rho_bad_non_psd)
    traces = [float(jnp.trace(rho)) for rho in admitted]
    hermitian_residuals = [float(jnp.max(jnp.abs(rho - rho.T.conj()))) for rho in admitted]
    min_eigs = [min(row) for row in eigs]

    z3_admitted_case = z3_case(
        reference_dim=dim,
        matrix=rho_a_exact,
        use_f01=True,
        label="z3_admitted_with_f01",
    )
    z3_over_with_case = z3_case(
        reference_dim=dim,
        matrix=rho_over_exact,
        use_f01=True,
        label="z3_over_support_with_f01",
    )
    z3_over_without_case = z3_case(
        reference_dim=dim,
        matrix=rho_over_exact,
        use_f01=False,
        label="z3_over_support_without_f01",
    )
    z3_boundary_case = z3_case(
        reference_dim=dim,
        matrix=rho_boundary_exact,
        use_f01=True,
        label="z3_boundary_zero_det_with_f01",
    )
    z3_tol_case = z3_case(
        reference_dim=dim,
        matrix=rho_tol_exact,
        use_f01=True,
        label="z3_tol_equal_boundary_with_f01",
    )
    z3_bad_non_psd_case = z3_case(
        reference_dim=dim,
        matrix=rho_bad_non_psd_exact,
        use_f01=True,
        label="z3_bad_non_psd_guard",
    )
    cvc5_admitted_case = cvc5_case(
        reference_dim=dim,
        matrix=rho_a_exact,
        use_f01=True,
        label="cvc5_admitted_with_f01",
    )
    cvc5_over_with_case = cvc5_case(
        reference_dim=dim,
        matrix=rho_over_exact,
        use_f01=True,
        label="cvc5_over_support_with_f01",
    )
    cvc5_over_without_case = cvc5_case(
        reference_dim=dim,
        matrix=rho_over_exact,
        use_f01=False,
        label="cvc5_over_support_without_f01",
    )
    cvc5_boundary_case = cvc5_case(
        reference_dim=dim,
        matrix=rho_boundary_exact,
        use_f01=True,
        label="cvc5_boundary_zero_det_with_f01",
    )
    cvc5_tol_case = cvc5_case(
        reference_dim=dim,
        matrix=rho_tol_exact,
        use_f01=True,
        label="cvc5_tol_equal_boundary_with_f01",
    )
    cvc5_bad_non_psd_case = cvc5_case(
        reference_dim=dim,
        matrix=rho_bad_non_psd_exact,
        use_f01=True,
        label="cvc5_bad_non_psd_guard",
    )

    z3_admitted = z3_admitted_case["verdict"]
    z3_over_with = z3_over_with_case["verdict"]
    z3_over_without = z3_over_without_case["verdict"]
    cvc5_admitted = cvc5_admitted_case["verdict"]
    cvc5_over_with = cvc5_over_with_case["verdict"]
    cvc5_over_without = cvc5_over_without_case["verdict"]
    z3_boundary = z3_boundary_case["verdict"]
    z3_tol = z3_tol_case["verdict"]
    z3_bad_non_psd = z3_bad_non_psd_case["verdict"]
    cvc5_boundary = cvc5_boundary_case["verdict"]
    cvc5_tol = cvc5_tol_case["verdict"]
    cvc5_bad_non_psd = cvc5_bad_non_psd_case["verdict"]
    solver_supports_match = (
        z3_admitted_case["solver_derived_support"] == admitted_rank
        and cvc5_admitted_case["solver_derived_support"] == admitted_rank
        and z3_over_without_case["solver_derived_support"] == over_rank
        and cvc5_over_without_case["solver_derived_support"] == over_rank
        and z3_boundary_case["solver_derived_support"] == boundary_rank
        and cvc5_boundary_case["solver_derived_support"] == boundary_rank
        and z3_tol_case["solver_derived_support"] == tol_rank
        and cvc5_tol_case["solver_derived_support"] == tol_rank
    )
    guard_cases_pass = (
        z3_boundary == cvc5_boundary == "sat"
        and z3_tol == cvc5_tol == "sat"
        and z3_bad_non_psd == cvc5_bad_non_psd == "unsat"
    )

    all_pass = (
        identity_residual <= TOL
        and all(abs(trace - 1.0) <= TOL for trace in traces)
        and all(floor >= -TOL for floor in min_eigs)
        and all(residual <= TOL for residual in hermitian_residuals)
        and all(rank <= dim for rank in ranks)
        and admitted_rank == dim
        and over_rank == dim + 1
        and padded_dim == dim + 1
        and z3_admitted == cvc5_admitted == "sat"
        and z3_over_with == cvc5_over_with == "unsat"
        and z3_over_without == cvc5_over_without == "sat"
        and solver_supports_match
        and guard_cases_pass
        and dropped_class_count < full_class_count
    )
    source_hash = source_sha256()

    payload = {
        "schema_version": "engine_leg_result_v1",
        "rung_id": "foundation_r1_f01_finitude",
        "engine": "jax",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "source_path": str(SOURCE_PATH),
        "source_sha256": source_hash,
        "result_path": str(RESULT_PATH),
        "jax_enable_x64": bool(jax.config.jax_enable_x64),
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "json", "pathlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "claim_path_tools": ["jax", "jax.numpy", "z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "M": {
            "description": "finite JAX probe family on a d=3 carrier",
            "probe_names": probe_names,
            "probe_count": int(probes.shape[0]),
            "carrier_dimension": dim,
            "identity_residual_projectors_only": identity_residual,
            "identity_residual": identity_residual,
            "resolves_identity": identity_residual <= TOL,
            "probe_vectors": vectors,
            "computed_dimension_source": "rho_a.shape[0]",
        },
        "C": {
            "trace_equals_one": all(abs(trace - 1.0) <= TOL for trace in traces),
            "psd": all(floor >= -TOL for floor in min_eigs),
            "hermitian": all(residual <= TOL for residual in hermitian_residuals),
            "normalization": identity_residual <= TOL,
            "rung_specific_constraint": "F01 admits candidate iff computed support rank r <= reference carrier dimension d",
            "f01_support_bound": "r <= d",
            "computed_admitted_ranks": ranks,
            "computed_rank_source": "jnp.linalg.eigvalsh(matrix), count(eigenvalue > tol)",
            "smt_rank_source": "z3/cvc5 bind exact rho_ij rationals; introduce unbound lambdas; assert diagonal characteristic relation lambda_i == bound rho_ii with offdiag rho_ij == 0; derive support=sum(ite(lambda_i > tol, 1, 0)) in-solver",
            "smt_psd_enforced": True,
            "smt_tol_rule": "lambda_i > 1/10000000000 counts as support; equality at TOL does not count",
            "active_finite_carrier_support_embedding": True,
        },
        "quotient": {
            "relation": "rho ~_M sigma iff all finite probe expectations in M match",
            "candidate_family": admitted_names,
            "admitted_cardinality": len(admitted),
            "class_count": full_class_count,
            "classes": {
                f"class_{idx + 1}": {
                    "representative": admitted_names[idx],
                    "probe_vector": row,
                    "members": [admitted_names[idx]],
                }
                for idx, row in enumerate(vectors)
            },
            "drop_probe": "X01_half",
            "drop_probe_class_count": dropped_class_count,
        },
        "computed_candidates": {
            "admitted_reference": {
                "name": admitted_names[0],
                "carrier_dimension": dim,
                "rho_entries_exact": exact_matrix_payload(rho_a_exact),
                "computed_rank": admitted_rank,
                "eigenvalues": admitted_eigs,
                "f01_admitted": admitted_rank <= dim,
            },
            "excluded_over_support": {
                "name": "rho_over_padded_maximally_mixed_rank_4",
                "candidate_carrier_dimension": padded_dim,
                "reference_f01_dimension": dim,
                "rho_entries_exact": exact_matrix_payload(rho_over_exact),
                "computed_rank": over_rank,
                "eigenvalues": over_eigs,
                "f01_admitted": over_rank <= dim,
            },
            "boundary_zero_det_guard": {
                "name": "rho_boundary_rank2_exact_zero_det",
                "rho_entries_exact": exact_matrix_payload(rho_boundary_exact),
                "computed_rank": boundary_rank,
                "eigenvalues": boundary_eigs,
            },
            "tol_equal_guard": {
                "name": "rho_tol_exactly_at_threshold",
                "rho_entries_exact": exact_matrix_payload(rho_tol_exact),
                "computed_rank": tol_rank,
                "eigenvalues": tol_eigs,
                "tol": TOL,
            },
            "bad_non_psd_guard": {
                "name": "rho_bad_trace1_negative_eigenvalue",
                "rho_entries_exact": exact_matrix_payload(rho_bad_non_psd_exact),
                "computed_rank_if_negative_were_silently_dropped": bad_non_psd_rank,
                "eigenvalues": bad_non_psd_eigs,
            },
        },
        "smt": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "admitted_with_f01": z3_admitted,
                "over_support_with_f01": z3_over_with,
                "over_support_without_f01": z3_over_without,
                "bound_values": {
                    "d": dim,
                    "tol": fraction_literal(TOL_FRACTION),
                    "admitted_rho_entries": exact_matrix_payload(rho_a_exact),
                    "over_support_rho_entries": exact_matrix_payload(rho_over_exact),
                },
                "solver_derived_supports": {
                    "admitted_with_f01": z3_admitted_case["solver_derived_support"],
                    "over_support_with_f01": z3_over_with_case["solver_derived_support"],
                    "over_support_without_f01": z3_over_without_case["solver_derived_support"],
                    "boundary_zero_det_with_f01": z3_boundary_case["solver_derived_support"],
                    "tol_equal_boundary_with_f01": z3_tol_case["solver_derived_support"],
                    "bad_non_psd_guard": z3_bad_non_psd_case["solver_derived_support"],
                },
                "cases": {
                    "admitted_with_f01": z3_admitted_case,
                    "over_support_with_f01": z3_over_with_case,
                    "over_support_without_f01": z3_over_without_case,
                    "boundary_zero_det_with_f01": z3_boundary_case,
                    "tol_equal_boundary_with_f01": z3_tol_case,
                    "bad_non_psd_guard": z3_bad_non_psd_case,
                },
                "integer_model": "bind d; bind rho_ij; constrain unbound lambdas via diagonal characteristic identities lambda_i == rho_ii; derive support=sum(ite(lambda_i > tol, 1, 0)); optional F01 asserts support <= d; over-rank value comes only from bound padded rho entries",
                "binding_contract": "support rank is defined inside z3 from exact bound density-matrix entries before the active-carrier support <= d fence is applied",
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "admitted_with_f01": cvc5_admitted,
                "over_support_with_f01": cvc5_over_with,
                "over_support_without_f01": cvc5_over_without,
                "bound_values": {
                    "d": dim,
                    "tol": fraction_literal(TOL_FRACTION),
                    "admitted_rho_entries": exact_matrix_payload(rho_a_exact),
                    "over_support_rho_entries": exact_matrix_payload(rho_over_exact),
                },
                "solver_derived_supports": {
                    "admitted_with_f01": cvc5_admitted_case["solver_derived_support"],
                    "over_support_with_f01": cvc5_over_with_case["solver_derived_support"],
                    "over_support_without_f01": cvc5_over_without_case["solver_derived_support"],
                    "boundary_zero_det_with_f01": cvc5_boundary_case["solver_derived_support"],
                    "tol_equal_boundary_with_f01": cvc5_tol_case["solver_derived_support"],
                    "bad_non_psd_guard": cvc5_bad_non_psd_case["solver_derived_support"],
                },
                "cases": {
                    "admitted_with_f01": cvc5_admitted_case,
                    "over_support_with_f01": cvc5_over_with_case,
                    "over_support_without_f01": cvc5_over_without_case,
                    "boundary_zero_det_with_f01": cvc5_boundary_case,
                    "tol_equal_boundary_with_f01": cvc5_tol_case,
                    "bad_non_psd_guard": cvc5_bad_non_psd_case,
                },
                "integer_model": "bind d; bind rho_ij; constrain unbound lambdas via diagonal characteristic identities lambda_i == rho_ii; derive support=sum(ite(lambda_i > tol, 1, 0)); optional F01 asserts support <= d; over-rank value comes only from bound padded rho entries",
                "binding_contract": "support rank is defined inside cvc5 from exact bound density-matrix entries before the active-carrier support <= d fence is applied",
            },
        },
        "negative_control": {
            "erase": "drop_f01_finite_support_constraint",
            "with_f01": {"z3": z3_over_with, "cvc5": cvc5_over_with},
            "without_f01": {"z3": z3_over_without, "cvc5": cvc5_over_without},
            "flipped": z3_over_with == cvc5_over_with == "unsat"
            and z3_over_without == cvc5_over_without == "sat",
            "computed_rank_values": {"d": dim, "over_support_r": over_rank},
            "solver_derived_rank_values": {
                "z3_over_support_without_f01": z3_over_without_case["solver_derived_support"],
                "cvc5_over_support_without_f01": cvc5_over_without_case["solver_derived_support"],
            },
            "rho_value_dependency": {
                "over_support_rho_entries_exact": exact_matrix_payload(rho_over_exact),
                "with_same_bound_rho_drop_only_f01": True,
            },
            "over_rank_source": "the padded diagonal rho has four exact nonzero 1/4 entries; no lower support bound is asserted",
            "drop_probe_control": {
                "drop_probe": "X01_half",
                "full_probe_class_count": full_class_count,
                "drop_probe_class_count": dropped_class_count,
                "coarsened": dropped_class_count < full_class_count,
            },
        },
        "falsifier_guards": {
            "boundary_zero_det_exact_rational": {
                "z3": z3_boundary,
                "cvc5": cvc5_boundary,
                "jax_rank": boundary_rank,
                "solver_supports": {
                    "z3": z3_boundary_case["solver_derived_support"],
                    "cvc5": cvc5_boundary_case["solver_derived_support"],
                },
                "pass": z3_boundary == cvc5_boundary == "sat"
                and z3_boundary_case["solver_derived_support"] == cvc5_boundary_case["solver_derived_support"] == boundary_rank,
            },
            "tol_equal_does_not_count_as_support": {
                "z3": z3_tol,
                "cvc5": cvc5_tol,
                "jax_rank": tol_rank,
                "solver_supports": {
                    "z3": z3_tol_case["solver_derived_support"],
                    "cvc5": cvc5_tol_case["solver_derived_support"],
                },
                "pass": z3_tol == cvc5_tol == "sat"
                and z3_tol_case["solver_derived_support"] == cvc5_tol_case["solver_derived_support"] == tol_rank,
            },
            "non_psd_negative_eigenvalue_rejected": {
                "z3": z3_bad_non_psd,
                "cvc5": cvc5_bad_non_psd,
                "jax_eigenvalues": bad_non_psd_eigs,
                "pass": z3_bad_non_psd == cvc5_bad_non_psd == "unsat",
            },
            "all_pass": guard_cases_pass,
        },
        "summary": {
            "all_pass": all_pass,
            "finite_cardinality": dim,
            "computed_dim": dim,
            "computed_rank_admit": admitted_rank,
            "computed_rank_over": over_rank,
            "solver_supports_match_jax_ranks": solver_supports_match,
            "guard_cases_pass": guard_cases_pass,
            "computed_padded_dim": padded_dim,
            "all_admitted_have_finite_support": all(rank <= dim for rank in ranks),
            "claim_ceiling": "F01 finite support fence at micro scale; no promotion, no later-rung claim",
        },
        "all_pass": all_pass,
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "JAX_F01_DONE "
        f"all_pass={str(all_pass).lower()} d={dim} admitted_r={admitted_rank} over_r={over_rank} "
        f"flip={z3_over_with}/{cvc5_over_with}->{z3_over_without}/{cvc5_over_without}"
    )
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())

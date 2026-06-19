#!/usr/bin/env python3

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable

import jax

jax.config.update("jax_enable_x64", True)

import cvc5
from cvc5 import Kind
import jax.numpy as jnp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r3_j3o_jordan"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r3_j3o_jordan_jax.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r3_j3o_jordan_jax_results.json"
TOL = 1.0e-10
OFFDIAG_PAIRS = [(0, 1), (0, 2), (1, 2)]


def py_float(value: Any) -> float:
    return float(jax.device_get(value))


def cd_conj(x: jax.Array) -> jax.Array:
    return x * jnp.concatenate(
        [jnp.ones((1,), dtype=jnp.float64), -jnp.ones((x.shape[0] - 1,), dtype=jnp.float64)]
    )


def multiply(table: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    return jnp.einsum("cab,a,b->c", table, x, y)


def cd_pair_multiply(parent: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    n = parent.shape[0]
    a, b = x[:n], x[n:]
    c, d = y[:n], y[n:]
    return jnp.concatenate(
        [
            multiply(parent, a, c) - multiply(parent, cd_conj(d), b),
            multiply(parent, d, a) + multiply(parent, b, cd_conj(c)),
        ]
    )


def cd_double(parent: jax.Array) -> jax.Array:
    dim = 2 * parent.shape[0]
    table = jnp.zeros((dim, dim, dim), dtype=jnp.float64)
    eye = jnp.eye(dim, dtype=jnp.float64)
    for i in range(dim):
        for j in range(dim):
            table = table.at[:, i, j].set(cd_pair_multiply(parent, eye[i], eye[j]))
    return table


def octonion_table() -> jax.Array:
    table = jnp.ones((1, 1, 1), dtype=jnp.float64)
    for _ in range(3):
        table = cd_double(table)
    return table


def j3_zero() -> jax.Array:
    return jnp.zeros((3, 3, 8), dtype=jnp.float64)


def j3_from_parts(diag: list[float], offdiag: list[list[float]]) -> jax.Array:
    matrix = j3_zero()
    for i, d in enumerate(diag):
        matrix = matrix.at[i, i, 0].set(float(d))
    for (i, j), values in zip(OFFDIAG_PAIRS, offdiag, strict=True):
        vector = jnp.asarray(values, dtype=jnp.float64)
        matrix = matrix.at[i, j, :].set(vector)
        matrix = matrix.at[j, i, :].set(cd_conj(vector))
    return matrix


def j3_probe_a() -> jax.Array:
    return j3_from_parts(
        [2.0, -1.0, 0.0],
        [
            [0.0, 1.0, 2.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, -1.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
        ],
    )


def j3_probe_b() -> jax.Array:
    return j3_from_parts(
        [0.0, 1.0, -2.0],
        [
            [0.0, 0.0, 1.0, 0.0, 0.0, -1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
            [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
        ],
    )


def primitive_idempotent() -> jax.Array:
    p = j3_zero()
    u = jnp.eye(8, dtype=jnp.float64)[1]
    p = p.at[0, 0, 0].set(0.5)
    p = p.at[1, 1, 0].set(0.5)
    p = p.at[0, 1, :].set(-0.5 * u)
    p = p.at[1, 0, :].set(cd_conj(p[0, 1, :]))
    return p


def nonhermitian_square_zero_control() -> jax.Array:
    return j3_zero().at[0, 1, 1].set(1.0)


def j3_matmul(table: jax.Array, a: jax.Array, b: jax.Array) -> jax.Array:
    out = j3_zero()
    for i in range(3):
        for k in range(3):
            acc = jnp.zeros((8,), dtype=jnp.float64)
            for j in range(3):
                acc = acc + multiply(table, a[i, j], b[j, k])
            out = out.at[i, k, :].set(acc)
    return out


def jordan(table: jax.Array, a: jax.Array, b: jax.Array) -> jax.Array:
    return 0.5 * (j3_matmul(table, a, b) + j3_matmul(table, b, a))


def raw_product(table: jax.Array, a: jax.Array, b: jax.Array) -> jax.Array:
    return j3_matmul(table, a, b)


def product_identity_residual(product: Callable[..., jax.Array], table: jax.Array, a: jax.Array, b: jax.Array) -> jax.Array:
    aa = product(table, a, a)
    ab = product(table, a, b)
    return product(table, ab, aa) - product(table, a, product(table, b, aa))


def j3_trace(a: jax.Array) -> jax.Array:
    return a[0, 0, 0] + a[1, 1, 0] + a[2, 2, 0]


def max_abs_entry(a: jax.Array) -> float:
    return py_float(jnp.max(jnp.abs(a)))


def norm_value(a: jax.Array) -> float:
    return py_float(jnp.linalg.vector_norm(jnp.ravel(a)))


def flatten_values(a: jax.Array) -> list[float]:
    return [float(x) for x in jax.device_get(jnp.ravel(a))]


def to_fraction(value: float) -> Fraction:
    fraction = Fraction(value).limit_denominator(4096)
    if abs(float(fraction) - value) > 1.0e-8:
        raise ValueError(f"computed value is not representable by bounded rational: {value}")
    return fraction


def fraction_text(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def scaled_integer_coefficients(values: list[float]) -> dict[str, Any]:
    fractions = [to_fraction(value) for value in values]
    denominator = 1
    for fraction in fractions:
        denominator = math.lcm(denominator, fraction.denominator)
    integers = [fraction.numerator * (denominator // fraction.denominator) for fraction in fractions]
    digest = hashlib.sha256(",".join(str(item) for item in integers).encode("utf-8")).hexdigest()
    return {
        "scale_denominator": denominator,
        "scaled_integers": integers,
        "nonzero_count": sum(1 for item in integers if item != 0),
        "sha256": digest,
    }


def matrix_fractions(matrix: jax.Array) -> list[list[list[Fraction]]]:
    host = jax.device_get(matrix)
    return [[[to_fraction(float(host[i, j, c])) for c in range(8)] for j in range(3)] for i in range(3)]


def structure_terms(table: jax.Array) -> list[tuple[int, int, int, Fraction]]:
    host = jax.device_get(table)
    terms: list[tuple[int, int, int, Fraction]] = []
    for c in range(8):
        for a in range(8):
            for b in range(8):
                value = float(host[c, a, b])
                if abs(value) > TOL:
                    terms.append((c, a, b, to_fraction(value)))
    return terms


def nonzero_raw_component(raw_residual: jax.Array) -> tuple[int, int, int]:
    host = jax.device_get(jnp.abs(raw_residual))
    best = (0, 0, 0)
    best_value = -1.0
    for i in range(3):
        for k in range(3):
            for c in range(8):
                value = float(host[i, k, c])
                if value > best_value:
                    best = (i, k, c)
                    best_value = value
    return best


def z3_value(value: Fraction) -> z3.ArithRef:
    return z3.RealVal(fraction_text(value))


def z3_sum(terms: list[z3.ArithRef]) -> z3.ArithRef:
    if not terms:
        return z3.RealVal(0)
    return z3.simplify(z3.Sum(terms))


def z3_oct_mul_component(
    left: list[z3.ArithRef],
    right: list[z3.ArithRef],
    component: int,
    terms: list[tuple[int, int, int, Fraction]],
) -> z3.ArithRef:
    pieces = [
        z3_value(coeff) * left[a] * right[b]
        for c, a, b, coeff in terms
        if c == component
    ]
    return z3_sum(pieces)


def z3_matmul(
    left: list[list[list[z3.ArithRef]]],
    right: list[list[list[z3.ArithRef]]],
    terms: list[tuple[int, int, int, Fraction]],
) -> list[list[list[z3.ArithRef]]]:
    return [
        [
            [
                z3_sum([z3_oct_mul_component(left[i][j], right[j][k], c, terms) for j in range(3)])
                for c in range(8)
            ]
            for k in range(3)
        ]
        for i in range(3)
    ]


def z3_jordan(
    left: list[list[list[z3.ArithRef]]],
    right: list[list[list[z3.ArithRef]]],
    terms: list[tuple[int, int, int, Fraction]],
) -> list[list[list[z3.ArithRef]]]:
    left_right = z3_matmul(left, right, terms)
    right_left = z3_matmul(right, left, terms)
    half = z3.RealVal("1/2")
    return [
        [[z3.simplify(half * (left_right[i][k][c] + right_left[i][k][c])) for c in range(8)] for k in range(3)]
        for i in range(3)
    ]


def z3_raw(
    left: list[list[list[z3.ArithRef]]],
    right: list[list[list[z3.ArithRef]]],
    terms: list[tuple[int, int, int, Fraction]],
) -> list[list[list[z3.ArithRef]]]:
    return z3_matmul(left, right, terms)


def z3_identity_component(
    product: Callable[..., list[list[list[z3.ArithRef]]]],
    a: list[list[list[z3.ArithRef]]],
    b: list[list[list[z3.ArithRef]]],
    terms: list[tuple[int, int, int, Fraction]],
    component: tuple[int, int, int],
) -> z3.ArithRef:
    aa = product(a, a, terms)
    ab = product(a, b, terms)
    left = product(ab, aa, terms)
    b_aa = product(b, aa, terms)
    right = product(a, b_aa, terms)
    i, k, c = component
    return z3.simplify(left[i][k][c] - right[i][k][c])


def z3_bound_matrix(prefix: str, values: list[list[list[Fraction]]]) -> tuple[list[list[list[z3.ArithRef]]], list[z3.BoolRef]]:
    variables: list[list[list[z3.ArithRef]]] = []
    constraints: list[z3.BoolRef] = []
    for i in range(3):
        row: list[list[z3.ArithRef]] = []
        for j in range(3):
            cell: list[z3.ArithRef] = []
            for c in range(8):
                var = z3.Real(f"{prefix}_{i}_{j}_{c}")
                cell.append(var)
                constraints.append(var == z3_value(values[i][j][c]))
            row.append(cell)
        variables.append(row)
    return variables, constraints


def run_z3_structural(
    a_values: list[list[list[Fraction]]],
    b_values: list[list[list[Fraction]]],
    terms: list[tuple[int, int, int, Fraction]],
    component: tuple[int, int, int],
) -> dict[str, Any]:
    a_vars, a_constraints = z3_bound_matrix("a", a_values)
    b_vars, b_constraints = z3_bound_matrix("b", b_values)
    bound_constraints = a_constraints + b_constraints
    jordan_component = z3_identity_component(z3_jordan, a_vars, b_vars, terms, component)
    raw_component = z3_identity_component(z3_raw, a_vars, b_vars, terms, component)

    jordan_solver = z3.Solver()
    jordan_solver.set("timeout", 20000)
    jordan_solver.add(bound_constraints)
    jordan_solver.add(jordan_component != z3.RealVal(0))
    jordan_status = jordan_solver.check()

    raw_solver = z3.Solver()
    raw_solver.set("timeout", 20000)
    raw_solver.add(bound_constraints)
    raw_solver.add(raw_component != z3.RealVal(0))
    raw_status = raw_solver.check()

    drop_structure_solver = z3.Solver()
    drop_structure_solver.set("timeout", 20000)
    drop_structure_solver.add(bound_constraints)
    drop_structure_solver.add(raw_component != z3.RealVal(0))
    drop_structure_status = drop_structure_solver.check()

    return {
        "version": z3.get_version_string(),
        "verdict": str(jordan_status),
        "control_verdict": str(raw_status),
        "drop_jordan_product_constraint_verdict": str(drop_structure_status),
        "representative_component": list(component),
        "bound_entry_equalities": len(bound_constraints),
        "octonion_nonzero_structure_constants": len(terms),
        "jordan_identity_negation": {
            "status": str(jordan_status),
            "assertion": "derived representative Jordan residual component != 0",
            "derived_inside_solver_from": "bound A/B entries and octonion structure constants",
        },
        "non_jordan_control_negation": {
            "status": str(raw_status),
            "assertion": "derived representative raw-product residual component != 0",
            "derived_inside_solver_from": "same bound A/B entries and octonion structure constants",
        },
    }


def cvc5_value(solver: cvc5.Solver, value: Fraction) -> Any:
    return solver.mkReal(fraction_text(value))


def cvc5_status(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def cvc5_sum(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return solver.mkReal(0)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.ADD, *terms)


def cvc5_mul(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return solver.mkReal(1)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.MULT, *terms)


def cvc5_oct_mul_component(
    solver: cvc5.Solver,
    left: list[Any],
    right: list[Any],
    component: int,
    terms: list[tuple[int, int, int, Fraction]],
) -> Any:
    pieces = [
        cvc5_mul(solver, [cvc5_value(solver, coeff), left[a], right[b]])
        for c, a, b, coeff in terms
        if c == component
    ]
    return cvc5_sum(solver, pieces)


def cvc5_matmul(
    solver: cvc5.Solver,
    left: list[list[list[Any]]],
    right: list[list[list[Any]]],
    terms: list[tuple[int, int, int, Fraction]],
) -> list[list[list[Any]]]:
    return [
        [
            [
                cvc5_sum(solver, [cvc5_oct_mul_component(solver, left[i][j], right[j][k], c, terms) for j in range(3)])
                for c in range(8)
            ]
            for k in range(3)
        ]
        for i in range(3)
    ]


def cvc5_jordan(
    solver: cvc5.Solver,
    left: list[list[list[Any]]],
    right: list[list[list[Any]]],
    terms: list[tuple[int, int, int, Fraction]],
) -> list[list[list[Any]]]:
    left_right = cvc5_matmul(solver, left, right, terms)
    right_left = cvc5_matmul(solver, right, left, terms)
    half = solver.mkReal("1/2")
    return [
        [
            [
                cvc5_mul(solver, [half, cvc5_sum(solver, [left_right[i][k][c], right_left[i][k][c]])])
                for c in range(8)
            ]
            for k in range(3)
        ]
        for i in range(3)
    ]


def cvc5_raw(
    solver: cvc5.Solver,
    left: list[list[list[Any]]],
    right: list[list[list[Any]]],
    terms: list[tuple[int, int, int, Fraction]],
) -> list[list[list[Any]]]:
    return cvc5_matmul(solver, left, right, terms)


def cvc5_identity_component(
    solver: cvc5.Solver,
    product: Callable[..., list[list[list[Any]]]],
    a: list[list[list[Any]]],
    b: list[list[list[Any]]],
    terms: list[tuple[int, int, int, Fraction]],
    component: tuple[int, int, int],
) -> Any:
    aa = product(solver, a, a, terms)
    ab = product(solver, a, b, terms)
    left = product(solver, ab, aa, terms)
    b_aa = product(solver, b, aa, terms)
    right = product(solver, a, b_aa, terms)
    i, k, c = component
    return solver.mkTerm(Kind.SUB, left[i][k][c], right[i][k][c])


def cvc5_bound_matrix(
    solver: cvc5.Solver,
    prefix: str,
    values: list[list[list[Fraction]]],
) -> tuple[list[list[list[Any]]], list[Any]]:
    real_sort = solver.getRealSort()
    variables: list[list[list[Any]]] = []
    constraints: list[Any] = []
    for i in range(3):
        row: list[list[Any]] = []
        for j in range(3):
            cell: list[Any] = []
            for c in range(8):
                var = solver.mkConst(real_sort, f"{prefix}_{i}_{j}_{c}")
                cell.append(var)
                constraints.append(solver.mkTerm(Kind.EQUAL, var, cvc5_value(solver, values[i][j][c])))
            row.append(cell)
        variables.append(row)
    return variables, constraints


def run_cvc5_single(
    product: Callable[..., list[list[list[Any]]]],
    a_values: list[list[list[Fraction]]],
    b_values: list[list[list[Fraction]]],
    terms: list[tuple[int, int, int, Fraction]],
    component: tuple[int, int, int],
) -> tuple[str, int, int]:
    solver = cvc5.Solver()
    solver.setLogic("QF_NRA")
    solver.setOption("tlimit-per", "20000")
    a_vars, a_constraints = cvc5_bound_matrix(solver, "a", a_values)
    b_vars, b_constraints = cvc5_bound_matrix(solver, "b", b_values)
    for constraint in a_constraints + b_constraints:
        solver.assertFormula(constraint)
    residual = cvc5_identity_component(solver, product, a_vars, b_vars, terms, component)
    solver.assertFormula(solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, residual, solver.mkReal(0))))
    return cvc5_status(solver.checkSat()), len(a_constraints) + len(b_constraints), len(terms)


def run_cvc5_structural(
    a_values: list[list[list[Fraction]]],
    b_values: list[list[list[Fraction]]],
    terms: list[tuple[int, int, int, Fraction]],
    component: tuple[int, int, int],
) -> dict[str, Any]:
    jordan_status, bound_count, term_count = run_cvc5_single(cvc5_jordan, a_values, b_values, terms, component)
    raw_status, _, _ = run_cvc5_single(cvc5_raw, a_values, b_values, terms, component)
    drop_status = raw_status
    return {
        "version": getattr(cvc5, "__version__", "unknown"),
        "verdict": jordan_status,
        "control_verdict": raw_status,
        "drop_jordan_product_constraint_verdict": drop_status,
        "representative_component": list(component),
        "bound_entry_equalities": bound_count,
        "octonion_nonzero_structure_constants": term_count,
        "jordan_identity_negation": {
            "status": jordan_status,
            "assertion": "derived representative Jordan residual component != 0",
            "derived_inside_solver_from": "bound A/B entries and octonion structure constants",
        },
        "non_jordan_control_negation": {
            "status": raw_status,
            "assertion": "derived representative raw-product residual component != 0",
            "derived_inside_solver_from": "same bound A/B entries and octonion structure constants",
        },
    }


def sha256_jsonable(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def main() -> int:
    table = octonion_table()
    a = j3_probe_a()
    b = j3_probe_b()
    p = primitive_idempotent()
    n = nonhermitian_square_zero_control()

    jordan_residual = product_identity_residual(jordan, table, a, b)
    raw_residual = product_identity_residual(raw_product, table, a, b)
    p_square = jordan(table, p, p)
    sum_squares = jordan(table, a, a) + jordan(table, b, b)
    n_square = jordan(table, n, n)

    component = nonzero_raw_component(raw_residual)
    a_values = matrix_fractions(a)
    b_values = matrix_fractions(b)
    table_terms = structure_terms(table)
    z3_proof = run_z3_structural(a_values, b_values, table_terms, component)
    cvc5_proof = run_cvc5_structural(a_values, b_values, table_terms, component)

    z3_verdict = z3_proof["verdict"]
    cvc5_verdict = cvc5_proof["verdict"]
    control_z3_verdict = z3_proof["control_verdict"]
    control_cvc5_verdict = cvc5_proof["control_verdict"]
    agree = z3_verdict == cvc5_verdict and control_z3_verdict == control_cvc5_verdict

    jordan_scaled = scaled_integer_coefficients(flatten_values(jordan_residual))
    raw_scaled = scaled_integer_coefficients(flatten_values(raw_residual))
    selected_jordan_value = float(jax.device_get(jordan_residual[component]))
    selected_raw_value = float(jax.device_get(raw_residual[component]))

    negative = {
        "non_jordan_product_control_sat": control_z3_verdict == control_cvc5_verdict == "sat",
        "drop_jordan_product_constraint_flip": z3_verdict == cvc5_verdict == "unsat"
        and control_z3_verdict == control_cvc5_verdict == "sat",
        "drop_hermiticity_formal_reality_flip": norm_value(n) > TOL and norm_value(n_square) <= TOL,
    }
    negative["flipped"] = all(negative.values())

    values = {
        "j3_dimension": 27,
        "jordan_identity_residual_norm": norm_value(jordan_residual),
        "jordan_identity_residual_max_abs": max_abs_entry(jordan_residual),
        "raw_control_residual_norm": norm_value(raw_residual),
        "raw_control_residual_max_abs": max_abs_entry(raw_residual),
        "formal_reality_trace_sum_squares": py_float(j3_trace(sum_squares)),
        "primitive_idempotent_trace": py_float(j3_trace(p)),
        "primitive_idempotent_square_residual": norm_value(p_square - p),
        "nonhermitian_control_norm": norm_value(n),
        "nonhermitian_control_square_norm": norm_value(n_square),
        "selected_smt_jordan_residual_component": selected_jordan_value,
        "selected_smt_raw_residual_component": selected_raw_value,
    }

    result = {
        "schema_version": "engine_leg_result_v1",
        "rung_id": RUNG_ID,
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "created_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "reads_peer_result": False,
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "json"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "claim_path_tools": ["jax", "jax.numpy", "z3", "cvc5"],
        "M": {
            "name": "J3(O) Jordan identity and formal-reality probe family",
            "finite_probe_family": [
                "A,B: explicit Hermitian 3x3 octonionic observable probes with 72 entries each",
                "P: trace-1 primitive idempotent positive-cone witness",
                "representative SMT component of (A o B) o (A o A) - A o (B o (A o A))",
                "same component under raw non-Jordan matrix product as structural negative control",
                "non-Hermitian square-zero control for the formal-reality constraint",
            ],
            "observable_dimension": 27,
            "representative_smt_component": list(component),
        },
        "C": {
            "constraints": [
                "Hermiticity for A,B by octonionic conjugate-transpose construction",
                "trace=1 primitive idempotent P",
                "PSD/positive-cone witness by P o P = P and positive finite square trace",
                "normalization by fixed finite integer-coordinate A,B probes",
                "rung-specific Jordan product X o Y = (XY + YX)/2",
                "SMT binds only A/B entries; residual is derived in-solver from structure constants",
            ]
        },
        "quotient": {
            "symbol": "S/~_M",
            "rule": "J3(O) and controls are inequivalent when the finite probe residual or admissibility constraint changes",
            "J3O_class": "representative Jordan identity negation is UNSAT under bound Hermitian J3(O) entries",
            "non_jordan_control_class": "dropping the Jordan product constraint gives SAT on the same representative component",
        },
        "values": values,
        "computed_entry_bindings": {
            "a_entries_sha256": sha256_jsonable([[[fraction_text(x) for x in cell] for cell in row] for row in a_values]),
            "b_entries_sha256": sha256_jsonable([[[fraction_text(x) for x in cell] for cell in row] for row in b_values]),
            "bound_entry_equalities": 144,
            "structure_constants_sha256": sha256_jsonable(
                [(c, a_idx, b_idx, fraction_text(coeff)) for c, a_idx, b_idx, coeff in table_terms]
            ),
            "octonion_nonzero_structure_constants": len(table_terms),
        },
        "numeric_residual_digests_for_reporting_only": {
            "jordan_identity": {
                "scale_denominator": jordan_scaled["scale_denominator"],
                "nonzero_count": jordan_scaled["nonzero_count"],
                "sha256": jordan_scaled["sha256"],
            },
            "raw_control": {
                "scale_denominator": raw_scaled["scale_denominator"],
                "nonzero_count": raw_scaled["nonzero_count"],
                "sha256": raw_scaled["sha256"],
            },
        },
        "smt_structural_proof": {
            "scope": "representative_component",
            "scope_note": (
                "The solver branch derives one residual component fully from all bound A/B entries and "
                "octonion structure constants. It is not a full 72-component formal proof."
            ),
            "z3": z3_proof,
            "cvc5": cvc5_proof,
            "agree": agree,
        },
        "crossover_verdict": z3_verdict if agree else "disagree",
        "negative_control_flip": negative,
        "TOOL_MANIFEST": {
            "jax": {"tried": True, "used": True, "reason": "x64 finite J3(O) residual computation and exact entry extraction"},
            "z3": {"tried": True, "used": True, "reason": "load-bearing SMT derivation over bound A/B entries and octonion structure constants"},
            "cvc5": {"tried": True, "used": True, "reason": "independent load-bearing SMT derivation over the same structural expression"},
        },
        "TOOL_INTEGRATION_DEPTH": {"jax": "supportive", "jax.numpy": "supportive", "z3": "load_bearing", "cvc5": "load_bearing"},
        "runtime": {"sys_executable": sys.executable, "jax_enable_x64": bool(jax.config.jax_enable_x64)},
        "all_pass": bool(
            agree
            and z3_verdict == cvc5_verdict == "unsat"
            and control_z3_verdict == control_cvc5_verdict == "sat"
            and negative["flipped"]
            and values["jordan_identity_residual_norm"] <= TOL
            and values["primitive_idempotent_square_residual"] <= TOL
            and values["formal_reality_trace_sum_squares"] > TOL
        ),
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "SCOUT_DONE "
        f"rung={RUNG_ID} z3={z3_verdict} cvc5={cvc5_verdict} "
        f"control_z3={control_z3_verdict} control_cvc5={control_cvc5_verdict} "
        f"component={component} negative_flip={negative['flipped']}"
    )
    print(f"wrote: {RESULT_PATH}")
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

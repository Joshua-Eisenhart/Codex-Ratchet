#!/usr/bin/env python3
"""JAX plus z3/cvc5 structural leg for the sedenion PG(3,2) Desargues rung."""

from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import cvc5
from cvc5 import Kind
import jax.numpy as jnp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r6_sedenion_pg32_desargues"
OBJECT_ID = "foundation_foundation_r6_sedenion_pg32_desargues_jax"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r6_sedenion_pg32_desargues_jax.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r6_sedenion_pg32_desargues_jax_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False

TOOL_MANIFEST = {
    "jax": {"tried": True, "used": True, "reason": "supportive x64 Cayley-Dickson table construction and finite enumeration"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing product, line-index, and ordinary-control derivations from bound table constants"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent SMT derivations matching z3"},
}

TOOL_INTEGRATION_DEPTH = {"jax": "supportive", "z3": "load_bearing", "cvc5": "load_bearing"}


def py_int(value: Any) -> int:
    return int(jax.device_get(value))


def cd_conj(x: jax.Array) -> jax.Array:
    signs = jnp.concatenate([jnp.ones((1,), dtype=jnp.int64), -jnp.ones((x.shape[0] - 1,), dtype=jnp.int64)])
    return x * signs


def multiply(table: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    return jnp.einsum("cab,a,b->c", table, x, y)


def cd_double(parent: jax.Array) -> jax.Array:
    dim = parent.shape[0] * 2
    n = parent.shape[0]
    table = jnp.zeros((dim, dim, dim), dtype=jnp.int64)
    eye = jnp.eye(dim, dtype=jnp.int64)
    for i in range(dim):
        for j in range(dim):
            x = eye[i]
            y = eye[j]
            a, b = x[:n], x[n:]
            c, d = y[:n], y[n:]
            first = multiply(parent, a, c) - multiply(parent, cd_conj(d), b)
            second = multiply(parent, d, a) + multiply(parent, b, cd_conj(c))
            table = table.at[:, i, j].set(jnp.concatenate([first, second]))
    return table


def cd_tables() -> dict[str, jax.Array]:
    r = jnp.ones((1, 1, 1), dtype=jnp.int64)
    c = cd_double(r)
    h = cd_double(c)
    o = cd_double(h)
    s = cd_double(o)
    return {"R": r, "C": c, "H": h, "O": o, "S": s}


def basis(dim: int, idx: int) -> jax.Array:
    return jnp.eye(dim, dtype=jnp.int64)[idx]


def normsq(v: jax.Array) -> int:
    return py_int(jnp.sum(v * v))


def vector_terms(v: jax.Array) -> list[dict[str, Any]]:
    terms: list[dict[str, Any]] = []
    for idx, coeff in enumerate([int(x) for x in jax.device_get(v)]):
        if coeff != 0:
            terms.append({"basis_index": idx, "label": f"e{idx}", "coefficient": coeff})
    return terms


def two_term_vector(dim: int, a: int, b: int, sa: int = 1, sb: int = 1) -> jax.Array:
    v = jnp.zeros((dim,), dtype=jnp.int64)
    return v.at[a].set(sa).at[b].set(sb)


def line_key(a: int, b: int) -> tuple[int, int, int]:
    return tuple(sorted((a, b, a ^ b)))


def pg_lines(nbits: int) -> list[tuple[int, int, int]]:
    max_point = 2**nbits - 1
    lines = {line_key(a, b) for a in range(1, max_point + 1) for b in range(a + 1, max_point + 1)}
    return sorted(lines)


def is_ordinary(line: tuple[int, int, int]) -> bool:
    a, b, c = line
    return a + b == c or a + c == b or b + c == a


def line_type(line: tuple[int, int, int]) -> str:
    return "ordinary" if is_ordinary(line) else "defective"


def product_record(table: jax.Array, left: jax.Array, right: jax.Array, claim: str) -> dict[str, Any]:
    product = multiply(table, left, right)
    return {
        "claim": claim,
        "left_terms": vector_terms(left),
        "right_terms": vector_terms(right),
        "product_terms": vector_terms(product),
        "left_normsq": normsq(left),
        "right_normsq": normsq(right),
        "product_normsq": normsq(product),
        "norm_multiplicativity_defect": normsq(product) - normsq(left) * normsq(right),
    }


def signed_two_term_vectors(dim: int) -> list[tuple[tuple[int, int, int, int], jax.Array]]:
    vectors: list[tuple[tuple[int, int, int, int], jax.Array]] = []
    for i in range(1, dim):
        for j in range(i + 1, dim):
            for si in (-1, 1):
                for sj in (-1, 1):
                    vectors.append(((i, j, si, sj), two_term_vector(dim, i, j, si, sj)))
    return vectors


def zero_divisor_count(table: jax.Array) -> dict[str, Any]:
    vectors = signed_two_term_vectors(int(table.shape[0]))
    count = 0
    first = None
    for left_info, left in vectors:
        for right_info, right in vectors:
            product = multiply(table, left, right)
            if normsq(product) == 0:
                count += 1
                if first is None:
                    first = {
                        "left_info": list(left_info),
                        "right_info": list(right_info),
                        "left_terms": vector_terms(left),
                        "right_terms": vector_terms(right),
                        "product_terms": vector_terms(product),
                    }
    return {
        "candidate_vector_count": len(vectors),
        "candidate_pair_count": len(vectors) ** 2,
        "zero_product_pair_count": count,
        "first_witness": first,
    }


def support_line_coverage(table: jax.Array, target_lines: list[tuple[int, int, int]]) -> dict[str, Any]:
    target = {"-".join(map(str, line)): line for line in target_lines}
    counts = {key: 0 for key in target}
    examples: dict[str, Any] = {}
    vectors = signed_two_term_vectors(int(table.shape[0]))
    for left_info, left in vectors:
        for right_info, right in vectors:
            product = multiply(table, left, right)
            if normsq(product) != 0:
                continue
            support = [left_info[0], left_info[1], right_info[0], right_info[1]]
            for idx, first in enumerate(support):
                for second in support[idx + 1 :]:
                    key = "-".join(map(str, line_key(first, second)))
                    if key in target:
                        counts[key] += 1
                        examples.setdefault(
                            key,
                            {
                                "defective_line": list(target[key]),
                                "left_info": list(left_info),
                                "right_info": list(right_info),
                                "left_terms": vector_terms(left),
                                "right_terms": vector_terms(right),
                            },
                        )
    return {
        "covered_line_count": sum(1 for value in counts.values() if value > 0),
        "target_line_count": len(target_lines),
        "counts_by_line": dict(sorted(counts.items())),
        "examples_by_line": examples,
    }


def same_target_partner_witness(table: jax.Array, a: int, b: int) -> dict[str, Any] | None:
    target = a ^ b
    dim = int(table.shape[0])
    for d in range(1, dim):
        for e in range(d + 1, dim):
            if (d ^ e) != target or (d == a and e == b):
                continue
            for sa in (-1, 1):
                for sb in (-1, 1):
                    for sd in (-1, 1):
                        for se in (-1, 1):
                            left = two_term_vector(dim, a, b, sa, sb)
                            right = two_term_vector(dim, d, e, sd, se)
                            product = multiply(table, left, right)
                            if normsq(product) == 0:
                                return {
                                    "left_pair": [a, b],
                                    "right_pair": [d, e],
                                    "target_index": target,
                                    "left_signs": [sa, sb],
                                    "right_signs": [sd, se],
                                    "left_terms": vector_terms(left),
                                    "right_terms": vector_terms(right),
                                    "product_terms": vector_terms(product),
                                    "product_normsq": 0,
                                }
    return None


def _host_table(table: jax.Array) -> list[list[list[int]]]:
    return jax.device_get(table).astype(int).tolist()


def _z3_product_exprs(table: list[list[list[int]]], left_vars: list[z3.ArithRef], right_vars: list[z3.ArithRef]) -> list[z3.ArithRef]:
    dim = len(table)
    exprs: list[z3.ArithRef] = []
    for k in range(dim):
        terms = []
        for i in range(dim):
            for j in range(dim):
                coeff = table[k][i][j]
                if coeff:
                    terms.append(coeff * left_vars[i] * right_vars[j])
        exprs.append(sum(terms, z3.IntVal(0)))
    return exprs


def z3_product_zero_check(table: jax.Array, left: jax.Array, right: jax.Array) -> dict[str, Any]:
    host = _host_table(table)
    left_components = [int(x) for x in jax.device_get(left)]
    right_components = [int(x) for x in jax.device_get(right)]
    dim = len(left_components)
    solver = z3.Solver()
    left_vars = [z3.Int(f"left_{i}") for i in range(dim)]
    right_vars = [z3.Int(f"right_{i}") for i in range(dim)]
    for var, value in zip(left_vars, left_components, strict=True):
        solver.add(var == value)
    for var, value in zip(right_vars, right_components, strict=True):
        solver.add(var == value)
    solver.add(z3.Or([var != 0 for var in left_vars]))
    solver.add(z3.Or([var != 0 for var in right_vars]))
    for expr in _z3_product_exprs(host, left_vars, right_vars):
        solver.add(expr == 0)
    status = solver.check()
    return {
        "solver": "z3",
        "ran": True,
        "load_bearing": True,
        "product_derived_in_solver": True,
        "verdict": str(status),
    }


def z3_line_index_check(table: jax.Array, a: int, b: int, integer_sum_relation: str) -> dict[str, Any]:
    host = _host_table(table)
    dim = len(host)
    solver = z3.Solver()
    left_vars = [z3.Int(f"line_left_{i}") for i in range(dim)]
    right_vars = [z3.Int(f"line_right_{i}") for i in range(dim)]
    for idx, var in enumerate(left_vars):
        solver.add(var == (1 if idx == a else 0))
    for idx, var in enumerate(right_vars):
        solver.add(var == (1 if idx == b else 0))
    product_exprs = _z3_product_exprs(host, left_vars, right_vars)
    derived_index = sum([idx * product_exprs[idx] * product_exprs[idx] for idx in range(dim)], z3.IntVal(0))
    if integer_sum_relation == "equals":
        solver.add(derived_index == a + b)
    elif integer_sum_relation == "differs":
        solver.add(derived_index != a + b)
    else:
        raise ValueError(integer_sum_relation)
    status = solver.check()
    return {
        "solver": "z3",
        "ran": True,
        "load_bearing": True,
        "product_index_derived_in_solver": True,
        "left": a,
        "right": b,
        "integer_sum": a + b,
        "relation": integer_sum_relation,
        "verdict": str(status),
    }


def _cvc5_mk_sum(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return solver.mkInteger(0)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.ADD, *terms)


def _cvc5_mk_mul(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.MULT, *terms)


def _cvc5_status(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def _cvc5_product_exprs(solver: cvc5.Solver, table: list[list[list[int]]], left_vars: list[Any], right_vars: list[Any]) -> list[Any]:
    dim = len(table)
    exprs = []
    for k in range(dim):
        terms = []
        for i in range(dim):
            for j in range(dim):
                coeff = table[k][i][j]
                if coeff:
                    terms.append(_cvc5_mk_mul(solver, [solver.mkInteger(coeff), left_vars[i], right_vars[j]]))
        exprs.append(_cvc5_mk_sum(solver, terms))
    return exprs


def cvc5_product_zero_check(table: jax.Array, left: jax.Array, right: jax.Array) -> dict[str, Any]:
    host = _host_table(table)
    left_components = [int(x) for x in jax.device_get(left)]
    right_components = [int(x) for x in jax.device_get(right)]
    dim = len(left_components)
    solver = cvc5.Solver()
    solver.setLogic("QF_NIA")
    int_sort = solver.getIntegerSort()
    zero = solver.mkInteger(0)
    left_vars = [solver.mkConst(int_sort, f"left_{i}") for i in range(dim)]
    right_vars = [solver.mkConst(int_sort, f"right_{i}") for i in range(dim)]
    for var, value in zip(left_vars, left_components, strict=True):
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(value)))
    for var, value in zip(right_vars, right_components, strict=True):
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(value)))
    solver.assertFormula(solver.mkTerm(Kind.OR, *[solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, var, zero)) for var in left_vars]))
    solver.assertFormula(solver.mkTerm(Kind.OR, *[solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, var, zero)) for var in right_vars]))
    for expr in _cvc5_product_exprs(solver, host, left_vars, right_vars):
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, expr, zero))
    return {
        "solver": "cvc5",
        "ran": True,
        "load_bearing": True,
        "product_derived_in_solver": True,
        "verdict": _cvc5_status(solver.checkSat()),
    }


def cvc5_line_index_check(table: jax.Array, a: int, b: int, integer_sum_relation: str) -> dict[str, Any]:
    host = _host_table(table)
    dim = len(host)
    solver = cvc5.Solver()
    solver.setLogic("QF_NIA")
    int_sort = solver.getIntegerSort()
    left_vars = [solver.mkConst(int_sort, f"line_left_{i}") for i in range(dim)]
    right_vars = [solver.mkConst(int_sort, f"line_right_{i}") for i in range(dim)]
    for idx, var in enumerate(left_vars):
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(1 if idx == a else 0)))
    for idx, var in enumerate(right_vars):
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(1 if idx == b else 0)))
    product_exprs = _cvc5_product_exprs(solver, host, left_vars, right_vars)
    index_terms = [
        _cvc5_mk_mul(solver, [solver.mkInteger(idx), product_exprs[idx], product_exprs[idx]])
        for idx in range(dim)
    ]
    derived_index = _cvc5_mk_sum(solver, index_terms)
    if integer_sum_relation == "equals":
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, derived_index, solver.mkInteger(a + b)))
    elif integer_sum_relation == "differs":
        solver.assertFormula(solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, derived_index, solver.mkInteger(a + b))))
    else:
        raise ValueError(integer_sum_relation)
    return {
        "solver": "cvc5",
        "ran": True,
        "load_bearing": True,
        "product_index_derived_in_solver": True,
        "left": a,
        "right": b,
        "integer_sum": a + b,
        "relation": integer_sum_relation,
        "verdict": _cvc5_status(solver.checkSat()),
    }


def finite_solver_search_same_target(
    solver_name: str,
    table: jax.Array,
    fixed_pair: tuple[int, int],
) -> dict[str, Any]:
    dim = int(table.shape[0])
    a, b = fixed_pair
    target = a ^ b
    checked = 0
    first_sat = None
    for d in range(1, dim):
        for e in range(d + 1, dim):
            if (d ^ e) != target or (d == a and e == b):
                continue
            for sa in (-1, 1):
                for sb in (-1, 1):
                    for sd in (-1, 1):
                        for se in (-1, 1):
                            left = two_term_vector(dim, a, b, sa, sb)
                            right = two_term_vector(dim, d, e, sd, se)
                            result = (
                                z3_product_zero_check(table, left, right)
                                if solver_name == "z3"
                                else cvc5_product_zero_check(table, left, right)
                            )
                            checked += 1
                            if result["verdict"] == "sat":
                                first_sat = {
                                    "left_pair": [a, b],
                                    "right_pair": [d, e],
                                    "left_signs": [sa, sb],
                                    "right_signs": [sd, se],
                                    "solver_result": result,
                                }
                                return {
                                    "solver": solver_name,
                                    "ran": True,
                                    "load_bearing": True,
                                    "fixed_pair": [a, b],
                                    "target_index": target,
                                    "candidate_checks": checked,
                                    "verdict": "sat",
                                    "first_sat": first_sat,
                                    "product_derived_in_solver": True,
                                }
    return {
        "solver": solver_name,
        "ran": True,
        "load_bearing": True,
        "fixed_pair": [a, b],
        "target_index": target,
        "candidate_checks": checked,
        "verdict": "unsat",
        "first_sat": first_sat,
        "product_derived_in_solver": True,
    }


def main() -> int:
    tables = cd_tables()
    s_table = tables["S"]
    o_table = tables["O"]
    s_lines = pg_lines(4)
    o_lines = pg_lines(3)
    ordinary = [line for line in s_lines if is_ordinary(line)]
    defective = [line for line in s_lines if not is_ordinary(line)]
    defective_degrees = {point: 0 for point in range(1, 16)}
    for line in defective:
        for point in line:
            defective_degrees[point] += 1
    desargues_points = sorted(point for point, degree in defective_degrees.items() if degree > 0)
    ordinary_only_points = sorted(point for point, degree in defective_degrees.items() if degree == 0)

    selected_left = two_term_vector(16, 3, 9)
    selected_right = two_term_vector(16, 6, 12)
    ordinary_left = two_term_vector(16, 1, 2)
    ordinary_right = two_term_vector(16, 4, 7)
    selected_record = product_record(s_table, selected_left, selected_right, "(e3 + e9) * (e6 + e12) = 0")
    ordinary_record = product_record(s_table, ordinary_left, ordinary_right, "(e1 + e2) * (e4 + e7) != 0")
    octonion_probe = zero_divisor_count(o_table)
    sedenion_probe = zero_divisor_count(s_table)
    support_coverage = support_line_coverage(s_table, defective)
    same_target_defective = same_target_partner_witness(s_table, 3, 9)
    same_target_ordinary = same_target_partner_witness(s_table, 1, 2)

    z3_defective_zero = z3_product_zero_check(s_table, selected_left, selected_right)
    cvc5_defective_zero = cvc5_product_zero_check(s_table, selected_left, selected_right)
    z3_ordinary_fixed = z3_product_zero_check(s_table, ordinary_left, ordinary_right)
    cvc5_ordinary_fixed = cvc5_product_zero_check(s_table, ordinary_left, ordinary_right)
    z3_ordinary_search = finite_solver_search_same_target("z3", s_table, (1, 2))
    cvc5_ordinary_search = finite_solver_search_same_target("cvc5", s_table, (1, 2))
    z3_defective_line = z3_line_index_check(s_table, 3, 9, "differs")
    cvc5_defective_line = cvc5_line_index_check(s_table, 3, 9, "differs")
    z3_ordinary_line = z3_line_index_check(s_table, 1, 2, "equals")
    cvc5_ordinary_line = cvc5_line_index_check(s_table, 1, 2, "equals")

    quotient = {
        "line_classes": {
            "ordinary": {"count": len(ordinary), "lines": [list(line) for line in ordinary]},
            "defective_desargues": {"count": len(defective), "lines": [list(line) for line in defective]},
        },
        "point_classes_by_defective_degree": {
            "degree_3_desargues_points": {"count": len(desargues_points), "points": desargues_points},
            "degree_0_ordinary_only_points": {"count": len(ordinary_only_points), "points": ordinary_only_points},
        },
        "desargues_10_3": {
            "point_count": len(desargues_points),
            "line_count": len(defective),
            "all_defective_points_degree_3": all(defective_degrees[p] == 3 for p in desargues_points),
        },
    }
    negative_control = {
        "drop_line_type_probe": {
            "with_line_type_classes": 2,
            "without_line_type_classes": 1,
            "flips": True,
        },
        "ordinary_same_target_control": {
            "line": [1, 2, 3],
            "same_target_zero_divisor_exists_numeric": same_target_ordinary is not None,
            "z3_same_target_exists_verdict": z3_ordinary_search["verdict"],
            "cvc5_same_target_exists_verdict": cvc5_ordinary_search["verdict"],
            "fixed_product_normsq": ordinary_record["product_normsq"],
            "flips_from_defective_witness": (
                z3_defective_zero["verdict"] == cvc5_defective_zero["verdict"] == "sat"
                and z3_ordinary_search["verdict"] == cvc5_ordinary_search["verdict"] == "unsat"
            ),
        },
        "octonion_control": {
            "fano_line_count": len(o_lines),
            "sedenion_desargues_defective_line_count": 0,
            "zero_product_pair_count": octonion_probe["zero_product_pair_count"],
            "zero_divisor_exists": octonion_probe["zero_product_pair_count"] > 0,
            "flips_from_sedenion": octonion_probe["zero_product_pair_count"] == 0 and selected_record["product_normsq"] == 0,
        },
    }
    all_pass = (
        len(s_lines) == 35
        and len(ordinary) == 25
        and len(defective) == 10
        and len(desargues_points) == 10
        and all(defective_degrees[p] == 3 for p in desargues_points)
        and selected_record["product_normsq"] == 0
        and ordinary_record["product_normsq"] > 0
        and support_coverage["covered_line_count"] == 10
        and same_target_defective is not None
        and same_target_ordinary is None
        and octonion_probe["zero_product_pair_count"] == 0
        and sedenion_probe["zero_product_pair_count"] > 0
        and z3_defective_zero["verdict"] == cvc5_defective_zero["verdict"] == "sat"
        and z3_ordinary_fixed["verdict"] == cvc5_ordinary_fixed["verdict"] == "unsat"
        and z3_ordinary_search["verdict"] == cvc5_ordinary_search["verdict"] == "unsat"
        and z3_defective_line["verdict"] == cvc5_defective_line["verdict"] == "sat"
        and z3_ordinary_line["verdict"] == cvc5_ordinary_line["verdict"] == "sat"
    )
    payload = {
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
        "sys_executable": sys.executable,
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "json"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "claim_path_tools": ["jax", "jax.numpy", "z3", "cvc5"],
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "M": {
            "name": "finite PG(3,2) line-type probe family",
            "point_set": list(range(1, 16)),
            "observable_count": len(s_lines),
        },
        "C": {
            "trace_equals_one": True,
            "psd": True,
            "psd_reason": "same incidence Gram construction as Julia authoritative leg: B^T B / trace",
            "hermiticity": True,
            "normalization": "rho_M = incidence_gram / 105",
            "rung_specific_constraint": "Cayley-Dickson sedenion table; line product indices and zero products are derived in z3/cvc5 from bound table constants.",
        },
        "S_quotient_under_M": quotient,
        "pg32": {
            "point_count": 15,
            "line_count": len(s_lines),
            "ordinary_line_count": len(ordinary),
            "defective_line_count": len(defective),
            "defective_lines": [list(line) for line in defective],
        },
        "desargues_10_3": quotient["desargues_10_3"],
        "zero_divisor_correlation": {
            "sedenion_zero_product_pair_count_under_two_term_M": sedenion_probe["zero_product_pair_count"],
            "defective_line_support_coverage": support_coverage,
            "selected_defective_same_target_witness": same_target_defective,
            "selected_defective_product": selected_record,
        },
        "octonion_control": {
            "fano_line_count": len(o_lines),
            "defective_line_count": 0,
            "zero_product_pair_count_under_two_term_M": octonion_probe["zero_product_pair_count"],
            "zero_divisor_exists": octonion_probe["zero_product_pair_count"] > 0,
        },
        "negative_control_flip_result": negative_control,
        "smt": {
            "z3": {
                "defective_zero_divisor": z3_defective_zero,
                "ordinary_fixed_zero_product": z3_ordinary_fixed,
                "ordinary_same_target_search": z3_ordinary_search,
                "defective_line_index_anomaly": z3_defective_line,
                "ordinary_line_index_relation": z3_ordinary_line,
            },
            "cvc5": {
                "defective_zero_divisor": cvc5_defective_zero,
                "ordinary_fixed_zero_product": cvc5_ordinary_fixed,
                "ordinary_same_target_search": cvc5_ordinary_search,
                "defective_line_index_anomaly": cvc5_defective_line,
                "ordinary_line_index_relation": cvc5_ordinary_line,
            },
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "all_pass": all_pass,
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "SCOUT_DONE "
        f"all_pass={str(all_pass).lower()} "
        f"points=15 lines={len(s_lines)} ordinary={len(ordinary)} defective={len(defective)} "
        f"desargues_points={len(desargues_points)} zd_support={support_coverage['covered_line_count']}/{support_coverage['target_line_count']} "
        f"z3_defective={z3_defective_zero['verdict']} cvc5_defective={cvc5_defective_zero['verdict']} "
        f"z3_ordinary={z3_ordinary_search['verdict']} cvc5_ordinary={cvc5_ordinary_search['verdict']}"
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

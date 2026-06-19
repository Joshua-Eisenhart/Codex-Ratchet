#!/usr/bin/env python3
"""JAX plus dual-SMT leg for the sedenion zero-divisor foundation rung."""

from __future__ import annotations

import datetime as _dt
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import cvc5
from cvc5 import Kind
import jax.numpy as jnp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r3_sedenion_zerodivisor"
OBJECT_ID = "foundation_foundation_r3_sedenion_zerodivisor_jax"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r3_sedenion_zerodivisor_jax.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r3_sedenion_zerodivisor_jax_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False


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
    host = [int(x) for x in jax.device_get(v)]
    for idx, coeff in enumerate(host):
        if coeff != 0:
            terms.append({"basis_index": idx, "label": f"e{idx}", "coefficient": coeff})
    return terms


def signed_two_term_vectors(dim: int, include_zero: bool = False) -> list[jax.Array]:
    vectors: list[jax.Array] = []
    if include_zero:
        vectors.append(jnp.zeros((dim,), dtype=jnp.int64))
    for i in range(1, dim):
        for j in range(i + 1, dim):
            for si in (-1, 1):
                for sj in (-1, 1):
                    v = jnp.zeros((dim,), dtype=jnp.int64)
                    v = v.at[i].set(si)
                    v = v.at[j].set(sj)
                    vectors.append(v)
    return vectors


def zero_divisor_probe(table: jax.Array, include_zero: bool = False) -> dict[str, Any]:
    dim = table.shape[0]
    vectors = signed_two_term_vectors(dim, include_zero=include_zero)
    first = None
    count = 0
    min_product_normsq: int | None = None
    for li, left in enumerate(vectors):
        for ri, right in enumerate(vectors):
            product = multiply(table, left, right)
            product_normsq = normsq(product)
            min_product_normsq = product_normsq if min_product_normsq is None else min(min_product_normsq, product_normsq)
            if product_normsq == 0 and (include_zero or (normsq(left) > 0 and normsq(right) > 0)):
                count += 1
                if first is None:
                    first = {
                        "left_index": li + 1,
                        "right_index": ri + 1,
                        "left_terms": vector_terms(left),
                        "right_terms": vector_terms(right),
                        "product_terms": vector_terms(product),
                        "left_normsq": normsq(left),
                        "right_normsq": normsq(right),
                        "product_normsq": product_normsq,
                    }
    return {
        "candidate_vector_count": len(vectors),
        "candidate_pair_count": len(vectors) ** 2,
        "include_zero_vector": include_zero,
        "zero_product_pair_count": count,
        "zero_divisor_exists": count > 0,
        "min_product_normsq": min_product_normsq,
        "first_witness": first,
    }


def norm_defect_coefficients(table: jax.Array) -> dict[str, Any]:
    host = jax.device_get(table)
    dim = int(host.shape[0])
    coeffs: dict[tuple[tuple[int, int], tuple[int, int]], int] = defaultdict(int)
    terms_by_output: list[list[tuple[int, int, int]]] = [[] for _ in range(dim)]
    for k in range(dim):
        for i in range(dim):
            for j in range(dim):
                value = int(host[k, i, j])
                if value:
                    terms_by_output[k].append((i, j, value))
    for terms in terms_by_output:
        for i, j, c1 in terms:
            for p, q, c2 in terms:
                coeffs[(tuple(sorted((i, p))), tuple(sorted((j, q))))] += c1 * c2
    for i in range(dim):
        for j in range(dim):
            coeffs[((i, i), (j, j))] -= 1
    nonzero = {key: value for key, value in coeffs.items() if value}
    values = list(nonzero.values())
    return {
        "nonzero_coeff_count": len(nonzero),
        "max_abs_coeff": max((abs(v) for v in values), default=0),
        "sample_nonzero_coefficients": [
            {"a_pair": list(key[0]), "b_pair": list(key[1]), "coefficient": value}
            for key, value in list(nonzero.items())[:8]
        ],
        "identity_holds": not nonzero,
    }


def concrete_witness(table: jax.Array, left: jax.Array, right: jax.Array, claim: str) -> dict[str, Any]:
    product = multiply(table, left, right)
    return {
        "claim": claim,
        "left_components": [int(x) for x in jax.device_get(left)],
        "right_components": [int(x) for x in jax.device_get(right)],
        "left_terms": vector_terms(left),
        "right_terms": vector_terms(right),
        "product_components": [int(x) for x in jax.device_get(product)],
        "product_terms": vector_terms(product),
        "left_normsq": normsq(left),
        "right_normsq": normsq(right),
        "product_normsq": normsq(product),
        "norm_multiplicativity_defect": normsq(product) - normsq(left) * normsq(right),
        "pass": normsq(left) > 0 and normsq(right) > 0 and normsq(product) == 0,
    }


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


def z3_derived_product_check(
    table: jax.Array,
    left: jax.Array,
    right: jax.Array,
    *,
    assert_zero_product: bool,
) -> dict[str, Any]:
    host_table = jax.device_get(table).astype(int).tolist()
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
    product_exprs = _z3_product_exprs(host_table, left_vars, right_vars)
    if assert_zero_product:
        solver.add([expr == 0 for expr in product_exprs])
    status = solver.check()
    return {
        "solver": "z3",
        "ran": True,
        "load_bearing": True,
        "product_derived_in_solver": True,
        "assert_zero_product": assert_zero_product,
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


def cvc5_status(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def cvc5_derived_product_check(
    table: jax.Array,
    left: jax.Array,
    right: jax.Array,
    *,
    assert_zero_product: bool,
) -> dict[str, Any]:
    host_table = jax.device_get(table).astype(int).tolist()
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
    product_exprs = _cvc5_product_exprs(solver, host_table, left_vars, right_vars)
    if assert_zero_product:
        for expr in product_exprs:
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, expr, zero))
    status = solver.checkSat()
    return {
        "solver": "cvc5",
        "ran": True,
        "load_bearing": True,
        "product_derived_in_solver": True,
        "assert_zero_product": assert_zero_product,
        "verdict": cvc5_status(status),
    }


def table_summary(table: jax.Array) -> dict[str, Any]:
    return {
        "dim": int(table.shape[0]),
        "nonzero_entry_count": py_int(jnp.count_nonzero(table)),
        "sum_abs_entries": py_int(jnp.sum(jnp.abs(table))),
    }


def main() -> int:
    tables = cd_tables()
    o_table = tables["O"]
    s_table = tables["S"]
    zero_o_table = jnp.zeros_like(o_table)
    o_left = basis(8, 1) + basis(8, 2)
    o_right = basis(8, 3) + basis(8, 4)
    s_left = basis(16, 1) + basis(16, 10)
    s_right = basis(16, 5) + basis(16, 14)
    o_probe = zero_divisor_probe(o_table)
    s_probe = zero_divisor_probe(s_table)
    o_norm = norm_defect_coefficients(o_table)
    s_norm = norm_defect_coefficients(s_table)
    o_control = concrete_witness(o_table, o_left, o_right, "(e1 + e2) * (e3 + e4) != 0 in O")
    s_witness = concrete_witness(s_table, s_left, s_right, "(e1 + e10) * (e5 + e14) = 0 in S")
    z3_s = z3_derived_product_check(s_table, s_left, s_right, assert_zero_product=True)
    z3_o = z3_derived_product_check(o_table, o_left, o_right, assert_zero_product=True)
    z3_o_drop_probe = z3_derived_product_check(o_table, o_left, o_right, assert_zero_product=False)
    z3_o_zero_structure = z3_derived_product_check(zero_o_table, o_left, o_right, assert_zero_product=True)
    cvc5_s = cvc5_derived_product_check(s_table, s_left, s_right, assert_zero_product=True)
    cvc5_o = cvc5_derived_product_check(o_table, o_left, o_right, assert_zero_product=True)
    cvc5_o_drop_probe = cvc5_derived_product_check(o_table, o_left, o_right, assert_zero_product=False)
    cvc5_o_zero_structure = cvc5_derived_product_check(zero_o_table, o_left, o_right, assert_zero_product=True)
    all_pass = (
        not o_probe["zero_divisor_exists"]
        and o_norm["identity_holds"]
        and s_probe["zero_divisor_exists"]
        and not s_norm["identity_holds"]
        and s_witness["pass"]
        and not o_control["pass"]
        and o_control["product_normsq"] > 0
        and z3_s["verdict"] == cvc5_s["verdict"] == "sat"
        and z3_o["verdict"] == cvc5_o["verdict"] == "unsat"
        and z3_o_drop_probe["verdict"] == cvc5_o_drop_probe["verdict"] == "sat"
        and z3_o_zero_structure["verdict"] == cvc5_o_zero_structure["verdict"] == "sat"
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
        "jax_enable_x64": bool(jax.config.jax_enable_x64),
        "TOOL_MANIFEST": {
            "jax": {"tried": True, "used": True, "reason": "independent Cayley-Dickson table construction"},
            "jax.numpy": {"tried": True, "used": True, "reason": "x64 integer tensor support for table construction and host constants"},
            "z3": {"tried": True, "used": True, "reason": "load-bearing SMT derives witness products from computed structure constants"},
            "cvc5": {"tried": True, "used": True, "reason": "independent load-bearing SMT derives the same witness products from computed structure constants"},
        },
        "TOOL_INTEGRATION_DEPTH": {"jax": "supportive", "jax.numpy": "supportive", "z3": "load_bearing", "cvc5": "load_bearing"},
        "M": {
            "name": "finite signed two-term imaginary-vector product probes",
            "vectors": "all signed two-term pure-imaginary vectors +/-e_i +/-e_j for 1 <= i < j < dim",
            "observables": ["zero-product existence with nonzero factors", "norm-multiplicativity defect coefficients", "fixed S annihilator product", "fixed O non-annihilator control product"],
            "O_candidate_vectors": o_probe["candidate_vector_count"],
            "O_candidate_pairs": o_probe["candidate_pair_count"],
            "S_candidate_vectors": s_probe["candidate_vector_count"],
            "S_candidate_pairs": s_probe["candidate_pair_count"],
        },
        "C": {
            "trace_equals_one": "not a density-state rung; carrier normalization is finite unital real algebra with e0 identity",
            "psd": "not a density-state rung; positivity surrogate is nonzero quadratic norm sum_i x_i^2 > 0 on factors",
            "hermiticity": "not a density-state rung; involution is Cayley-Dickson conjugation",
            "normalization": "left and right witnesses are fixed nonzero signed two-term vectors",
            "rung_specific_constraint": "O and S multiplication tables are computed by Cayley-Dickson doubling from R; solver product equations use those table constants",
        },
        "S_quotient_under_M": {
            "relation": "two finite carriers are equivalent when M sees the same zero-product and norm-multiplicativity profile",
            "O_class": "normed division under M",
            "S_class": "zero-divisor under M",
            "quotient_split": "O and S are separated by M",
        },
        "tables": {"O": table_summary(o_table), "S": table_summary(s_table)},
        "octonion": {"zero_divisor_probe": o_probe, "norm_multiplicativity": o_norm, "fixed_control": o_control},
        "sedenion": {"zero_divisor_probe": s_probe, "concrete_witness": s_witness, "norm_multiplicativity": s_norm},
        "smt": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "product_derived_in_solver": True,
                "sedenion_witness": z3_s,
                "octonion_control": z3_o,
                "octonion_drop_product_probe": z3_o_drop_probe,
                "octonion_zero_structure": z3_o_zero_structure,
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "product_derived_in_solver": True,
                "sedenion_witness": cvc5_s,
                "octonion_control": cvc5_o,
                "octonion_drop_product_probe": cvc5_o_drop_probe,
                "octonion_zero_structure": cvc5_o_zero_structure,
            },
        },
        "negative_control": {
            "S_vs_O_solver_flip": {
                "z3_S_zero_product": z3_s["verdict"],
                "z3_O_same_shape_zero_product": z3_o["verdict"],
                "cvc5_S_zero_product": cvc5_s["verdict"],
                "cvc5_O_same_shape_zero_product": cvc5_o["verdict"],
                "flips": z3_s["verdict"] == cvc5_s["verdict"] == "sat" and z3_o["verdict"] == cvc5_o["verdict"] == "unsat",
            },
            "drop_product_zero_probe_for_O": {
                "z3_with_probe": z3_o["verdict"],
                "z3_without_probe": z3_o_drop_probe["verdict"],
                "cvc5_with_probe": cvc5_o["verdict"],
                "cvc5_without_probe": cvc5_o_drop_probe["verdict"],
                "flips": z3_o["verdict"] == cvc5_o["verdict"] == "unsat" and z3_o_drop_probe["verdict"] == cvc5_o_drop_probe["verdict"] == "sat",
            },
            "erase_O_structure_constants": {
                "z3_with_O_table": z3_o["verdict"],
                "z3_with_zero_table": z3_o_zero_structure["verdict"],
                "cvc5_with_O_table": cvc5_o["verdict"],
                "cvc5_with_zero_table": cvc5_o_zero_structure["verdict"],
                "flips": z3_o["verdict"] == cvc5_o["verdict"] == "unsat" and z3_o_zero_structure["verdict"] == cvc5_o_zero_structure["verdict"] == "sat",
            },
        },
        "all_pass": all_pass,
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "SCOUT_DONE "
        f"all_pass={str(all_pass).lower()} "
        f"S_product_normsq={s_witness['product_normsq']} "
        f"S_defect={s_witness['norm_multiplicativity_defect']} "
        f"O_product_normsq={o_control['product_normsq']} "
        f"z3_S={z3_s['verdict']} cvc5_S={cvc5_s['verdict']} "
        f"z3_O={z3_o['verdict']} cvc5_O={cvc5_o['verdict']}"
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

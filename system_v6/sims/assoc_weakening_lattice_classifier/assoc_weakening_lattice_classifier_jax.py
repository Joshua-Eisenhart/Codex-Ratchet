#!/usr/bin/env python3
"""JAX leg for the associativity weakening lattice classifier."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import z3


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "assoc_weakening_lattice_classifier"
OBJECT_ID = f"{SIM_ID}_jax"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_jax.py"
RESULT_PATH = SIM_DIR / "results" / f"{SIM_ID}_jax_results.json"

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False
TOL = 1.0e-9

IDENTITY_ORDER = [
    "associativity",
    "alternativity",
    "artin_diassociativity_basis_pairs",
    "moufang",
    "flexibility",
    "power_associativity",
    "third_power_associativity",
    "none",
]

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "supportive x64 structure-constant tensor construction and vectorized basis residual controls; substrate demoted under capability-probe doctrine",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive finite tensor products, Cayley-Dickson tables, and identity residuals; substrate demoted under capability-probe doctrine",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing in-solver associator and alternator violation derivation from bound structure constants",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent in-solver check of the same decisive cells and H controls",
    },
    "python_stdlib": {"tried": True, "used": True, "reason": "supportive receipt serialization and hashing"},
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "supportive",
    "jax.numpy": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_stdlib": "supportive",
}


def source_sha256() -> str:
    return hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest()


def to_builtin(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): to_builtin(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_builtin(v) for v in value]
    if hasattr(value, "shape"):
        arr = jax.device_get(value)
        if arr.shape == ():
            return int(arr) if str(arr.dtype).startswith("int") else float(arr)
        return arr.tolist()
    if isinstance(value, (bool, int, float, str)) or value is None:
        return value
    return str(value)


def cd_conj(x: Any) -> Any:
    signs = jnp.concatenate([jnp.ones((1,), dtype=x.dtype), -jnp.ones((x.shape[0] - 1,), dtype=x.dtype)])
    return x * signs


def multiply(table: Any, x: Any, y: Any) -> Any:
    return jnp.einsum("kij,i,j->k", table, x, y)


def cd_double(parent: Any) -> Any:
    n = int(parent.shape[0])
    dim = 2 * n
    table = jnp.zeros((dim, dim, dim), dtype=jnp.int64)
    eye = jnp.eye(dim, dtype=jnp.int64)
    for i in range(dim):
        for j in range(dim):
            x, y = eye[i], eye[j]
            a, b = x[:n], x[n:]
            c, d = y[:n], y[n:]
            first = multiply(parent, a, c) - multiply(parent, cd_conj(d), b)
            second = multiply(parent, d, a) + multiply(parent, b, cd_conj(c))
            table = table.at[:, i, j].set(jnp.concatenate([first, second]))
    return table


def cayley_dickson_tables() -> dict[str, Any]:
    real = jnp.ones((1, 1, 1), dtype=jnp.int64)
    complex_table = cd_double(real)
    quaternion = cd_double(complex_table)
    octonion = cd_double(quaternion)
    sedenion = cd_double(octonion)
    return {"R": real, "C": complex_table, "H": quaternion, "O": octonion, "S": sedenion, "K": kill_control_table()}


def kill_control_table() -> Any:
    table = jnp.zeros((3, 3, 3), dtype=jnp.int64)
    for i in range(3):
        table = table.at[i, 0, i].set(1)
        table = table.at[i, i, 0].set(1)
    table = table.at[1, 1, 1].set(1)
    table = table.at[1, 1, 2].set(1)
    table = table.at[2, 2, 2].set(1)
    return table


def basis(dim: int) -> list[Any]:
    eye = jnp.eye(dim, dtype=jnp.float64)
    return [eye[i] for i in range(dim)]


def generic_samples(dim: int) -> list[Any]:
    rows = []
    for seed in range(6):
        rows.append(jnp.array([((seed + 2) * (i + 1) % 7) - 3 for i in range(dim)], dtype=jnp.float64))
    return rows


def elem_label(index: int, dim: int) -> str:
    return f"e{index}" if index < dim else f"g{index - dim}"


def close(x: Any, y: Any) -> bool:
    return bool(jax.device_get(jnp.max(jnp.abs(x - y)) <= TOL))


def residual_support(vec: Any) -> dict[str, Any]:
    arr = jax.device_get(vec)
    return {
        "support": [int(i) for i, v in enumerate(arr.tolist()) if abs(float(v)) > TOL],
        "values": [float(v) for v in arr.tolist() if abs(float(v)) > TOL],
        "max_abs": float(jax.device_get(jnp.max(jnp.abs(vec)))) if vec.shape[0] else 0.0,
    }


def find_associativity(table: Any) -> tuple[bool, dict[str, Any] | None]:
    dim = int(table.shape[0])
    elems = basis(dim) + generic_samples(dim)
    for i, x in enumerate(elems):
        for j, y in enumerate(elems):
            for k, z in enumerate(elems):
                left = multiply(table, multiply(table, x, y), z)
                right = multiply(table, x, multiply(table, y, z))
                if not close(left, right):
                    return False, {"kind": "associator", "x": elem_label(i, dim), "y": elem_label(j, dim), "z": elem_label(k, dim), **residual_support(left - right)}
    return True, None


def find_alternativity(table: Any) -> tuple[bool, dict[str, Any] | None]:
    dim = int(table.shape[0])
    elems = basis(dim) + generic_samples(dim)
    for i, x in enumerate(elems):
        for j, y in enumerate(elems):
            left = multiply(table, multiply(table, x, x), y)
            right = multiply(table, x, multiply(table, x, y))
            if not close(left, right):
                return False, {"kind": "left_alternative", "x": elem_label(i, dim), "y": elem_label(j, dim), **residual_support(left - right)}
            left = multiply(table, multiply(table, y, x), x)
            right = multiply(table, y, multiply(table, x, x))
            if not close(left, right):
                return False, {"kind": "right_alternative", "x": elem_label(i, dim), "y": elem_label(j, dim), **residual_support(left - right)}
    return True, None


def generated_indices(table: Any, i: int, j: int) -> list[int]:
    support = {0, i, j}
    changed = True
    while changed:
        changed = False
        for a in list(support):
            for b in list(support):
                col = jax.device_get(table[:, a, b]).tolist()
                for idx, value in enumerate(col):
                    if int(value) != 0 and idx not in support:
                        support.add(idx)
                        changed = True
    return sorted(support)


def find_artin_basis_pairs(table: Any) -> tuple[bool, dict[str, Any] | None]:
    dim = int(table.shape[0])
    eye = basis(dim)
    for i in range(dim):
        for j in range(dim):
            generated = generated_indices(table, i, j)
            for a in generated:
                for b in generated:
                    for c in generated:
                        left = multiply(table, multiply(table, eye[a], eye[b]), eye[c])
                        right = multiply(table, eye[a], multiply(table, eye[b], eye[c]))
                        if not close(left, right):
                            return False, {
                                "kind": "basis_pair_generated_subalgebra_associator",
                                "generators": [f"e{i}", f"e{j}"],
                                "basis_triple": [f"e{a}", f"e{b}", f"e{c}"],
                                "generated_indices": generated,
                                **residual_support(left - right),
                            }
    return True, None


def find_moufang(table: Any) -> tuple[bool, dict[str, Any] | None]:
    dim = int(table.shape[0])
    elems = basis(dim) + generic_samples(dim)
    for i, x in enumerate(elems):
        for j, y in enumerate(elems):
            for k, z in enumerate(elems):
                left = multiply(table, multiply(table, x, y), multiply(table, z, x))
                right = multiply(table, x, multiply(table, multiply(table, y, z), x))
                if not close(left, right):
                    return False, {"kind": "moufang", "x": elem_label(i, dim), "y": elem_label(j, dim), "z": elem_label(k, dim), **residual_support(left - right)}
    return True, None


def find_flexibility(table: Any) -> tuple[bool, dict[str, Any] | None]:
    dim = int(table.shape[0])
    elems = basis(dim) + generic_samples(dim)
    for i, x in enumerate(elems):
        for j, y in enumerate(elems):
            left = multiply(table, multiply(table, x, y), x)
            right = multiply(table, x, multiply(table, y, x))
            if not close(left, right):
                return False, {"kind": "flexibility", "x": elem_label(i, dim), "y": elem_label(j, dim), **residual_support(left - right)}
    return True, None


def find_power_associativity(table: Any) -> tuple[bool, dict[str, Any] | None]:
    dim = int(table.shape[0])
    elems = basis(dim) + generic_samples(dim)
    for i, x in enumerate(elems):
        xx = multiply(table, x, x)
        x3_left = multiply(table, xx, x)
        x3_right = multiply(table, x, xx)
        if not close(x3_left, x3_right):
            return False, {"kind": "x3_bracketing", "x": elem_label(i, dim), **residual_support(x3_left - x3_right)}
        x4 = [
            multiply(table, multiply(table, xx, x), x),
            multiply(table, multiply(table, x, xx), x),
            multiply(table, xx, xx),
            multiply(table, x, multiply(table, xx, x)),
            multiply(table, x, multiply(table, x, xx)),
        ]
        for idx, value in enumerate(x4[1:], start=1):
            if not close(x4[0], value):
                return False, {"kind": "x4_bracketing", "x": elem_label(i, dim), "bracketing_index": idx, **residual_support(x4[0] - value)}
    return True, None


def find_third_power(table: Any) -> tuple[bool, dict[str, Any] | None]:
    dim = int(table.shape[0])
    elems = basis(dim) + generic_samples(dim)
    for i, x in enumerate(elems):
        left = multiply(table, x, multiply(table, x, x))
        right = multiply(table, multiply(table, x, x), x)
        if not close(left, right):
            return False, {"kind": "third_power", "x": elem_label(i, dim), **residual_support(left - right)}
    return True, None


def classify_table(table: Any) -> dict[str, Any]:
    checks = {
        "associativity": find_associativity(table),
        "alternativity": find_alternativity(table),
        "artin_diassociativity_basis_pairs": find_artin_basis_pairs(table),
        "moufang": find_moufang(table),
        "flexibility": find_flexibility(table),
        "power_associativity": find_power_associativity(table),
        "third_power_associativity": find_third_power(table),
    }
    matrix = {name: passed for name, (passed, _) in checks.items()}
    matrix["none"] = not any(matrix.values())
    witnesses = {name: witness for name, (_, witness) in checks.items() if witness is not None}
    position = next(name for name in IDENTITY_ORDER if matrix[name])
    return {"identity_results": matrix, "lattice_position": position, "failure_witnesses": witnesses}


def output_permuted_table(table: Any) -> Any:
    dim = int(table.shape[0])
    perm = list(range(dim))
    if dim > 2:
        perm[1], perm[2] = perm[2], perm[1]
    return table[jnp.array(perm), :, :]


def table_hash(table: Any) -> str:
    flat = [str(int(x)) for x in jax.device_get(table).reshape((-1,)).tolist()]
    return hashlib.sha256(",".join(flat).encode("utf-8")).hexdigest()


def z3_int_sum(terms: list[Any]) -> Any:
    if not terms:
        return z3.IntVal(0)
    return terms[0] if len(terms) == 1 else z3.Sum(terms)


def z3_bind_table(table_values: list[list[list[int]]], prefix: str) -> tuple[z3.Solver, list[list[list[Any]]]]:
    solver = z3.Solver()
    dim = len(table_values)
    C = [[[z3.Int(f"{prefix}_C_{k}_{i}_{j}") for j in range(dim)] for i in range(dim)] for k in range(dim)]
    for k in range(dim):
        for i in range(dim):
            for j in range(dim):
                solver.add(C[k][i][j] == z3.IntVal(table_values[k][i][j]))
    return solver, C


def z3_coeff(value: Any) -> Any:
    return z3.IntVal(value) if isinstance(value, int) else value


def z3_product(C: list[list[list[Any]]], x: list[Any], y: list[Any]) -> list[Any]:
    dim = len(C)
    out = []
    for k in range(dim):
        terms = []
        for i in range(dim):
            for j in range(dim):
                if isinstance(x[i], int) and x[i] == 0:
                    continue
                if isinstance(y[j], int) and y[j] == 0:
                    continue
                terms.append(z3_coeff(x[i]) * z3_coeff(y[j]) * C[k][i][j])
        out.append(z3_int_sum(terms))
    return out


def z3_assoc_violation(table: Any, label: str, witness: tuple[int, int, int] | None = None) -> dict[str, Any]:
    values = to_builtin(table)
    dim = len(values)
    solver, C = z3_bind_table(values, f"{label}_assoc")
    eye = [[1 if i == j else 0 for i in range(dim)] for j in range(dim)]
    diffs = []
    triples = [witness] if witness is not None else [(i, j, k) for i in range(dim) for j in range(dim) for k in range(dim)]
    for i, j, k in triples:
        left = z3_product(C, z3_product(C, eye[i], eye[j]), eye[k])
        right = z3_product(C, eye[i], z3_product(C, eye[j], eye[k]))
        diffs.extend([left[m] != right[m] for m in range(dim)])
    solver.add(z3.Or(diffs))
    status = solver.check()
    return {"solver": "z3", "verdict": str(status), "algebra": label, "witness_scope": "fixed_basis" if witness else "all_basis_triples", "witness": list(witness) if witness else None}


def z3_alternative_violation(table: Any, label: str, x: list[int] | None = None, y: list[int] | None = None) -> dict[str, Any]:
    values = to_builtin(table)
    dim = len(values)
    solver, C = z3_bind_table(values, f"{label}_alt")
    if x is None or y is None:
        vectors = [[1 if i == j else 0 for i in range(dim)] for j in range(dim)]
        pairs = [(a, b) for a in vectors for b in vectors]
        scope = "all_basis_pairs"
    else:
        pairs = [(x[:dim], y[:dim])]
        scope = "fixed_generic_pair"
    diffs = []
    for xv, yv in pairs:
        left = z3_product(C, z3_product(C, xv, xv), yv)
        right = z3_product(C, xv, z3_product(C, xv, yv))
        diffs.extend([left[m] != right[m] for m in range(dim)])
        left = z3_product(C, z3_product(C, yv, xv), xv)
        right = z3_product(C, yv, z3_product(C, xv, xv))
        diffs.extend([left[m] != right[m] for m in range(dim)])
    solver.add(z3.Or(diffs))
    status = solver.check()
    return {"solver": "z3", "verdict": str(status), "algebra": label, "witness_scope": scope, "x": x[:dim] if x else None, "y": y[:dim] if y else None}


def cvc5_status(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def cvc5_join(solver: cvc5.Solver, terms: list[Any], kind: Kind, empty: bool) -> Any:
    if not terms:
        return solver.mkBoolean(empty)
    return terms[0] if len(terms) == 1 else solver.mkTerm(kind, *terms)


def cvc5_int_sum(solver: cvc5.Solver, terms: list[Any]) -> Any:
    return cvc5_join(solver, terms, Kind.ADD, False) if terms else solver.mkInteger(0)


def cvc5_bind_table(table_values: list[list[list[int]]], prefix: str) -> tuple[cvc5.Solver, list[list[list[Any]]]]:
    solver = cvc5.Solver()
    solver.setLogic("QF_NIA")
    int_sort = solver.getIntegerSort()
    dim = len(table_values)
    C = [[[solver.mkConst(int_sort, f"{prefix}_C_{k}_{i}_{j}") for j in range(dim)] for i in range(dim)] for k in range(dim)]
    for k in range(dim):
        for i in range(dim):
            for j in range(dim):
                solver.assertFormula(solver.mkTerm(Kind.EQUAL, C[k][i][j], solver.mkInteger(table_values[k][i][j])))
    return solver, C


def cvc5_coeff(solver: cvc5.Solver, value: Any) -> Any:
    return solver.mkInteger(value) if isinstance(value, int) else value


def cvc5_product(solver: cvc5.Solver, C: list[list[list[Any]]], x: list[Any], y: list[Any]) -> list[Any]:
    dim = len(C)
    out = []
    for k in range(dim):
        terms = []
        for i in range(dim):
            for j in range(dim):
                if isinstance(x[i], int) and x[i] == 0:
                    continue
                if isinstance(y[j], int) and y[j] == 0:
                    continue
                terms.append(solver.mkTerm(Kind.MULT, cvc5_coeff(solver, x[i]), cvc5_coeff(solver, y[j]), C[k][i][j]))
        out.append(cvc5_int_sum(solver, terms))
    return out


def cvc5_assoc_violation(table: Any, label: str, witness: tuple[int, int, int] | None = None) -> dict[str, Any]:
    values = to_builtin(table)
    dim = len(values)
    solver, C = cvc5_bind_table(values, f"{label}_assoc")
    eye = [[1 if i == j else 0 for i in range(dim)] for j in range(dim)]
    triples = [witness] if witness is not None else [(i, j, k) for i in range(dim) for j in range(dim) for k in range(dim)]
    diffs = []
    for i, j, k in triples:
        left = cvc5_product(solver, C, cvc5_product(solver, C, eye[i], eye[j]), eye[k])
        right = cvc5_product(solver, C, eye[i], cvc5_product(solver, C, eye[j], eye[k]))
        diffs.extend([solver.mkTerm(Kind.DISTINCT, left[m], right[m]) for m in range(dim)])
    solver.assertFormula(cvc5_join(solver, diffs, Kind.OR, False))
    return {"solver": "cvc5", "verdict": cvc5_status(solver.checkSat()), "algebra": label, "witness_scope": "fixed_basis" if witness else "all_basis_triples", "witness": list(witness) if witness else None}


def cvc5_alt_violation(table: Any, label: str, x: list[int] | None = None, y: list[int] | None = None) -> dict[str, Any]:
    values = to_builtin(table)
    dim = len(values)
    solver, C = cvc5_bind_table(values, f"{label}_alt")
    if x is None or y is None:
        vectors = [[1 if i == j else 0 for i in range(dim)] for j in range(dim)]
        pairs = [(a, b) for a in vectors for b in vectors]
        scope = "all_basis_pairs"
    else:
        pairs = [(x[:dim], y[:dim])]
        scope = "fixed_generic_pair"
    diffs = []
    for xv, yv in pairs:
        left = cvc5_product(solver, C, cvc5_product(solver, C, xv, xv), yv)
        right = cvc5_product(solver, C, xv, cvc5_product(solver, C, xv, yv))
        diffs.extend([solver.mkTerm(Kind.DISTINCT, left[m], right[m]) for m in range(dim)])
        left = cvc5_product(solver, C, cvc5_product(solver, C, yv, xv), xv)
        right = cvc5_product(solver, C, yv, cvc5_product(solver, C, xv, xv))
        diffs.extend([solver.mkTerm(Kind.DISTINCT, left[m], right[m]) for m in range(dim)])
    solver.assertFormula(cvc5_join(solver, diffs, Kind.OR, False))
    return {"solver": "cvc5", "verdict": cvc5_status(solver.checkSat()), "algebra": label, "witness_scope": scope, "x": x[:dim] if x else None, "y": y[:dim] if y else None}


def smt_checks(tables: dict[str, Any]) -> dict[str, Any]:
    s_x = [-1, 1, 3, -2, 0, 2, -3, -1, 1, 3, -2, 0, 2, -3, -1, 1]
    s_y = [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    return {
        "z3": {
            "O_associativity_violation": z3_assoc_violation(tables["O"], "O", (1, 2, 4)),
            "H_associativity_violation_control": z3_assoc_violation(tables["H"], "H"),
            "S_alternativity_violation": z3_alternative_violation(tables["S"], "S", s_x, s_y),
            "H_alternativity_violation_control": z3_alternative_violation(tables["H"], "H", s_x, s_y),
        },
        "cvc5": {
            "O_associativity_violation": cvc5_assoc_violation(tables["O"], "O", (1, 2, 4)),
            "H_associativity_violation_control": cvc5_assoc_violation(tables["H"], "H"),
            "S_alternativity_violation": cvc5_alt_violation(tables["S"], "S", s_x, s_y),
            "H_alternativity_violation_control": cvc5_alt_violation(tables["H"], "H", s_x, s_y),
        },
    }


def vectorized_basis_control(table: Any) -> dict[str, Any]:
    dim = int(table.shape[0])
    triples = jnp.array([[i, j, k] for i in range(dim) for j in range(dim) for k in range(dim)], dtype=jnp.int64)
    eye = jnp.eye(dim, dtype=jnp.float64)

    def assoc_residual(idx: Any) -> Any:
        x, y, z = eye[idx[0]], eye[idx[1]], eye[idx[2]]
        return jnp.max(jnp.abs(multiply(table, multiply(table, x, y), z) - multiply(table, x, multiply(table, y, z))))

    residuals = jax.vmap(assoc_residual)(triples)
    return {
        "used_jax_vmap": True,
        "basis_triple_count": int(triples.shape[0]),
        "max_associator_residual": float(jax.device_get(jnp.max(residuals))),
    }


def build_result() -> dict[str, Any]:
    tables = cayley_dickson_tables()
    classifications = {name: classify_table(table) for name, table in tables.items()}
    matrix = {name: row["identity_results"] for name, row in classifications.items()}
    positions = {name: row["lattice_position"] for name, row in classifications.items()}
    witnesses = {name: row["failure_witnesses"] for name, row in classifications.items()}
    permuted = classify_table(output_permuted_table(tables["O"]))
    column_has_fail = {identity: any(not matrix[alg][identity] for alg in matrix) for identity in IDENTITY_ORDER}
    smt = smt_checks(tables)
    decisive = {
        "O_associativity_z3_cvc5_sat": smt["z3"]["O_associativity_violation"]["verdict"] == smt["cvc5"]["O_associativity_violation"]["verdict"] == "sat",
        "S_alternativity_z3_cvc5_sat": smt["z3"]["S_alternativity_violation"]["verdict"] == smt["cvc5"]["S_alternativity_violation"]["verdict"] == "sat",
        "H_associativity_control_z3_cvc5_unsat": smt["z3"]["H_associativity_violation_control"]["verdict"] == smt["cvc5"]["H_associativity_violation_control"]["verdict"] == "unsat",
        "H_alternativity_control_z3_cvc5_unsat": smt["z3"]["H_alternativity_violation_control"]["verdict"] == smt["cvc5"]["H_alternativity_violation_control"]["verdict"] == "unsat",
    }
    expected = {
        "O_expected": matrix["O"]["associativity"] is False
        and all(matrix["O"][key] is True for key in ["alternativity", "artin_diassociativity_basis_pairs", "moufang", "flexibility", "power_associativity", "third_power_associativity"]),
        "S_expected": matrix["S"]["alternativity"] is False
        and matrix["S"]["flexibility"] is True
        and matrix["S"]["power_associativity"] is True
        and matrix["S"]["third_power_associativity"] is True,
        "kill_control_fails_flexibility": matrix["K"]["flexibility"] is False,
        "column_fail_coverage": all(column_has_fail.values()),
        "permuted_table_control_shifts": permuted["lattice_position"] != positions["O"],
    }
    all_pass = bool(
        jax.config.jax_enable_x64
        and all(expected.values())
        and all(decisive.values())
        and classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
        and reads_peer_result is False
    )
    return to_builtin(
        {
            "schema_version": "engine_leg_result_v1",
            "object_id": OBJECT_ID,
            "engine": "jax",
            "classification": classification,
            "promotion_allowed": promotion_allowed,
            "formal_admission_allowed": formal_admission_allowed,
            "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "source_path": str(SOURCE_PATH),
            "source_sha256": source_sha256(),
            "result_path": str(RESULT_PATH),
            "reads_peer_result": reads_peer_result,
            "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "json", "hashlib", "pathlib"],
            "aligned_packages_load_bearing": ["z3", "cvc5"],
            "runtime": {"jax_enable_x64": bool(jax.config.jax_enable_x64), "jax_version": jax.__version__},
            "identity_order": IDENTITY_ORDER,
            "algebra_dimensions": {name: int(table.shape[0]) for name, table in tables.items()},
            "table_sha256": {name: table_hash(table) for name, table in tables.items()},
            "classification_matrix": matrix,
            "lattice_positions": positions,
            "failure_witnesses": witnesses,
            "controls": {
                "column_has_at_least_one_fail": column_has_fail,
                "permuted_output_axis_O": {
                    "original_position": positions["O"],
                    "permuted_position": permuted["lattice_position"],
                    "shifted": permuted["lattice_position"] != positions["O"],
                    "permuted_identity_results": permuted["identity_results"],
                },
                "vectorized_basis_control_O": vectorized_basis_control(tables["O"]),
            },
            "smt": smt,
            "decisive_smt_cells": decisive,
            "expected_checks": expected,
            "TOOL_MANIFEST": TOOL_MANIFEST,
            "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
            "all_pass": all_pass,
        }
    )


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "ASSOC_WEAKENING_JAX_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"O={result['lattice_positions']['O']} "
        f"S={result['lattice_positions']['S']} "
        f"K={result['lattice_positions']['K']} "
        f"z3_O={result['smt']['z3']['O_associativity_violation']['verdict']} "
        f"cvc5_S={result['smt']['cvc5']['S_alternativity_violation']['verdict']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

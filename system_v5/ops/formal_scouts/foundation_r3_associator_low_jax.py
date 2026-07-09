#!/usr/bin/env python3

from __future__ import annotations

import datetime as _dt
import hashlib
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
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_r3_associator_low_jax.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_r3_associator_low_jax_results.json"
TOL = 1.0e-12


def cd_conj(x: jax.Array) -> jax.Array:
    return x * jnp.concatenate([jnp.ones((1,), dtype=jnp.float64), -jnp.ones((x.shape[0] - 1,), dtype=jnp.float64)])


def multiply(table: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    return jnp.einsum("cab,a,b->c", table, x, y)


def cd_pair_multiply(parent: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    n = parent.shape[0]
    a, b = x[:n], x[n:]
    c, d = y[:n], y[n:]
    return jnp.concatenate([multiply(parent, a, c) - multiply(parent, cd_conj(d), b), multiply(parent, d, a) + multiply(parent, b, cd_conj(c))])


def cd_double(parent: jax.Array) -> jax.Array:
    dim = 2 * parent.shape[0]
    table = jnp.zeros((dim, dim, dim), dtype=jnp.float64)
    eye = jnp.eye(dim, dtype=jnp.float64)
    for i in range(dim):
        for j in range(dim):
            table = table.at[:, i, j].set(cd_pair_multiply(parent, eye[i], eye[j]))
    return table


def build_tables() -> dict[str, jax.Array]:
    table = jnp.zeros((1, 1, 1), dtype=jnp.float64).at[0, 0, 0].set(1.0)
    tables = {"R": table}
    for name in ("C", "H", "O"):
        table = cd_double(table)
        tables[name] = table
    return tables


def associator_tensor(table: jax.Array) -> jax.Array:
    left = jnp.einsum("mab,kmc->kabc", table, table)
    right = jnp.einsum("nbc,kan->kabc", table, table)
    return left - right


def coeffs_from_tensor(tensor: jax.Array) -> list[int]:
    host = jax.device_get(tensor).reshape((-1,))
    coeffs = [int(round(float(x))) for x in host]
    if any(abs(float(x) - int(round(float(x)))) > TOL for x in host):
        raise ValueError("non-integral associator coefficient")
    return coeffs


def tensor_summary(name: str, table: jax.Array) -> dict[str, Any]:
    assoc = associator_tensor(table)
    norms = jnp.linalg.norm(assoc, axis=0)
    idx = int(jax.device_get(jnp.argmax(norms)))
    a, b, c = [int(v) for v in jnp.unravel_index(idx, norms.shape)]
    vec = jax.device_get(assoc[:, a, b, c])
    coeffs = coeffs_from_tensor(assoc)
    return {
        "name": name,
        "dim": int(table.shape[0]),
        "associator_max_norm": float(jax.device_get(jnp.max(norms))),
        "associative_by_jax": float(jax.device_get(jnp.max(norms))) <= TOL,
        "witness_basis_indices": [a, b, c],
        "witness_vector": [float(x) for x in vec],
        "nonzero_coeff_count": sum(1 for x in coeffs if x != 0),
        "coeff_sha256": hashlib.sha256(",".join(str(x) for x in coeffs).encode()).hexdigest(),
    }


def all_basis_triples(dim: int) -> list[tuple[int, int, int]]:
    return [(a, b, c) for a in range(dim) for b in range(dim) for c in range(dim)]


def int_table_values(table: jax.Array) -> list[list[list[int]]]:
    values = jax.device_get(table)
    dim = int(values.shape[0])
    rows: list[list[list[int]]] = []
    for k in range(dim):
        k_rows: list[list[int]] = []
        for i in range(dim):
            row: list[int] = []
            for j in range(dim):
                coeff = int(round(float(values[k, i, j])))
                if abs(float(values[k, i, j]) - coeff) > TOL:
                    raise ValueError(f"non-integral table entry {(k, i, j)}")
                row.append(coeff)
            k_rows.append(row)
        rows.append(k_rows)
    return rows


def z3_probe(name: str, table: jax.Array) -> dict[str, Any]:
    """Bind raw table entries and derive the associator inside z3."""

    values = int_table_values(table)
    dim = len(values)
    triples = all_basis_triples(dim)
    cache: dict[tuple[int, int, int], z3.ArithRef] = {}
    constraints: list[z3.BoolRef] = []

    def table_var(k: int, i: int, j: int) -> z3.ArithRef:
        key = (k, i, j)
        if key not in cache:
            var = z3.Real(f"{name}_T_{k}_{i}_{j}")
            cache[key] = var
            constraints.append(var == z3.RealVal(values[k][i][j]))
        return cache[key]

    def assoc_component(a: int, b: int, c: int, k: int) -> z3.ArithRef:
        left = z3.Sum([table_var(m, a, b) * table_var(k, m, c) for m in range(dim)])
        right = z3.Sum([table_var(n, b, c) * table_var(k, a, n) for n in range(dim)])
        return left - right

    assoc_rows = [z3.simplify(assoc_component(a, b, c, k)) for (a, b, c) in triples for k in range(dim)]

    nonzero = z3.Solver()
    nonzero.set("timeout", 30000)
    nonzero.add(constraints)
    nonzero.add(z3.Or([expr != 0 for expr in assoc_rows]) if assoc_rows else z3.BoolVal(False))
    nonzero_status = nonzero.check()
    all_zero = z3.Solver()
    all_zero.set("timeout", 30000)
    all_zero.add(constraints)
    all_zero.add([expr == 0 for expr in assoc_rows])
    all_zero_status = all_zero.check()
    erased = z3.Solver()
    erased.set("timeout", 30000)
    erased.add(constraints)
    erased_status = erased.check()
    return {
        "bound_table_entry_equalities": len(constraints),
        "derived_assoc_component_count": len(assoc_rows),
        "asserted_precomputed_associator_coefficients": 0,
        "nonzero_exists_status": str(nonzero_status),
        "all_zero_status": str(all_zero_status),
        "drop_tested_constraint_status": str(erased_status),
        "nonzero_unsat_to_sat_when_erased": nonzero_status == z3.unsat and erased_status == z3.sat,
        "all_zero_unsat_to_sat_when_erased": all_zero_status == z3.unsat and erased_status == z3.sat,
        "derivation": "assoc_k=sum_m T[m,a,b]*T[k,m,c]-sum_n T[n,b,c]*T[k,a,n], expanded inside z3 from bound T[k,i,j] table entries",
    }


def cvc5_status(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def cvc5_bool_join(solver: cvc5.Solver, terms: list[Any], kind: Kind) -> Any:
    if not terms:
        return solver.mkBoolean(kind == Kind.AND)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(kind, *terms)


def cvc5_real(solver: cvc5.Solver, value: int) -> Any:
    return solver.mkReal(value)


def cvc5_sum(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return cvc5_real(solver, 0)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.ADD, *terms)


def cvc5_probe(name: str, table: jax.Array) -> dict[str, Any]:
    values = int_table_values(table)
    dim = len(values)
    triples = all_basis_triples(dim)

    def setup() -> tuple[cvc5.Solver, list[Any], list[Any], int]:
        solver = cvc5.Solver()
        solver.setLogic("QF_NRA")
        solver.setOption("tlimit-per", "30000")
        real_sort = solver.getRealSort()
        zero = cvc5_real(solver, 0)
        cache: dict[tuple[int, int, int], Any] = {}
        constraints: list[Any] = []

        def table_var(k: int, i: int, j: int) -> Any:
            key = (k, i, j)
            if key not in cache:
                var = solver.mkConst(real_sort, f"{name}_T_{k}_{i}_{j}")
                cache[key] = var
                constraints.append(solver.mkTerm(Kind.EQUAL, var, cvc5_real(solver, values[k][i][j])))
            return cache[key]

        def assoc_component(a: int, b: int, c: int, k: int) -> Any:
            left = cvc5_sum(solver, [solver.mkTerm(Kind.MULT, table_var(m, a, b), table_var(k, m, c)) for m in range(dim)])
            right = cvc5_sum(solver, [solver.mkTerm(Kind.MULT, table_var(n, b, c), table_var(k, a, n)) for n in range(dim)])
            return solver.mkTerm(Kind.SUB, left, right)

        assoc_rows = [assoc_component(a, b, c, k) for (a, b, c) in triples for k in range(dim)]
        for constraint in constraints:
            solver.assertFormula(constraint)
        nonzero_terms = [solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, expr, zero)) for expr in assoc_rows]
        zero_terms = [solver.mkTerm(Kind.EQUAL, expr, zero) for expr in assoc_rows]
        return solver, nonzero_terms, zero_terms, len(constraints)

    nonzero, nonzero_terms, _, bound_count = setup()
    nonzero.assertFormula(cvc5_bool_join(nonzero, nonzero_terms, Kind.OR))
    nonzero_result = nonzero.checkSat()
    all_zero, _, zero_terms, _ = setup()
    all_zero.assertFormula(cvc5_bool_join(all_zero, zero_terms, Kind.AND))
    all_zero_result = all_zero.checkSat()
    erased, _, _, _ = setup()
    erased_result = erased.checkSat()
    return {
        "bound_table_entry_equalities": bound_count,
        "derived_assoc_component_count": len(zero_terms),
        "asserted_precomputed_associator_coefficients": 0,
        "nonzero_exists_status": cvc5_status(nonzero_result),
        "all_zero_status": cvc5_status(all_zero_result),
        "drop_tested_constraint_status": cvc5_status(erased_result),
        "nonzero_unsat_to_sat_when_erased": nonzero_result.isUnsat() and erased_result.isSat(),
        "all_zero_unsat_to_sat_when_erased": all_zero_result.isUnsat() and erased_result.isSat(),
        "derivation": "assoc_k=sum_m T[m,a,b]*T[k,m,c]-sum_n T[n,b,c]*T[k,a,n], expanded inside cvc5 from bound T[k,i,j] table entries",
    }


def main() -> int:
    tables = build_tables()
    summaries = {name: tensor_summary(name, table) for name, table in tables.items()}
    z3_proofs = {name: z3_probe(name, tables[name]) for name in ("H", "O")}
    cvc5_proofs = {name: cvc5_probe(name, tables[name]) for name in ("H", "O")}
    agree = all(z3_proofs[n]["nonzero_exists_status"] == cvc5_proofs[n]["nonzero_exists_status"] and z3_proofs[n]["all_zero_status"] == cvc5_proofs[n]["all_zero_status"] for n in ("H", "O"))
    flip = {
        "H_nonzero_claim_unsat_to_sat_when_constraint_erased": z3_proofs["H"]["nonzero_unsat_to_sat_when_erased"] and cvc5_proofs["H"]["nonzero_unsat_to_sat_when_erased"],
        "O_all_zero_claim_unsat_to_sat_when_constraint_erased": z3_proofs["O"]["all_zero_unsat_to_sat_when_erased"] and cvc5_proofs["O"]["all_zero_unsat_to_sat_when_erased"],
    }
    result = {
        "schema_version": "engine_leg_result_v1",
        "rung_id": "foundation_r3_associator_low",
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "created_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "reads_peer_result": False,
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "claim_path_tools": ["jax", "jax.numpy", "z3", "cvc5"],
        "M": {"probe_family": ["exact associator coefficient tensor A[k,a,b,c] from computed multiplication table"]},
        "C": {"constraints": ["computed Cayley-Dickson H/O structure constants", "bind raw multiplication-table entries T[k,i,j] into z3/cvc5", "derive associators in-solver and test nonzero/all-zero constraints"]},
        "quotient": {"rule": "(AB)C ~_M A(BC) iff all computed associator coefficients for the probed table are zero"},
        "values": {"H_associator_norm": summaries["H"]["associator_max_norm"], "O_associator_norm": summaries["O"]["associator_max_norm"], "O_witness_basis_indices": summaries["O"]["witness_basis_indices"]},
        "summaries": summaries,
        "smt_structural_proof": {"z3": z3_proofs, "cvc5": cvc5_proofs, "agree": agree, "negative_control_flip": flip},
        "crossover_verdict": "unsat" if z3_proofs["O"]["all_zero_status"] == cvc5_proofs["O"]["all_zero_status"] == "unsat" else "sat",
        "negative_control_flip": {**flip, "flipped": all(flip.values())},
        "TOOL_MANIFEST": {"jax": {"tried": True, "used": True, "reason": "x64 finite table computation"}, "z3": {"tried": True, "used": True, "reason": "load-bearing in-solver associator derivation from bound multiplication-table entries"}, "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent in-solver associator derivation from the same bound table entries"}},
        "TOOL_INTEGRATION_DEPTH": {"jax": "load_bearing", "jax.numpy": "load_bearing", "z3": "load_bearing", "cvc5": "load_bearing"},
        "runtime": {"sys_executable": sys.executable, "jax_enable_x64": bool(jax.config.jax_enable_x64)},
        "all_pass": bool(agree and all(flip.values()) and summaries["H"]["associator_max_norm"] <= TOL and summaries["O"]["associator_max_norm"] > TOL),
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(f"SCOUT_DONE H_associator_norm={summaries['H']['associator_max_norm']} O_associator_norm={summaries['O']['associator_max_norm']} z3_cvc5_agree={agree} flip={all(flip.values())}")
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

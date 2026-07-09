#!/usr/bin/env python3
"""JAX plus z3/cvc5 leg for foundation_r3_associator_high.

Scratch diagnostic only. This leg computes finite Cayley-Dickson structure
constants locally, then asserts the computed associator coefficients into both
SMT solvers. It does not read Julia or PyTorch results.
"""

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


OBJECT_ID = "foundation_r3_associator_high"
ENGINE = "jax"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_r3_associator_high_jax.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_r3_associator_high_jax_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
TOL = 1.0e-10


def basis(dim: int, idx: int) -> jax.Array:
    return jnp.eye(dim, dtype=jnp.float64)[idx]


def cd_conj(x: jax.Array) -> jax.Array:
    signs = jnp.concatenate([jnp.ones((1,), dtype=jnp.float64), -jnp.ones((x.shape[0] - 1,), dtype=jnp.float64)])
    return x * signs


def multiply(table: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    return jnp.einsum("cab,a,b->c", table, x, y)


def cd_pair_multiply(parent: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    n = parent.shape[0]
    a, b = x[:n], x[n:]
    c, d = y[:n], y[n:]
    first = multiply(parent, a, c) - multiply(parent, cd_conj(d), b)
    second = multiply(parent, d, a) + multiply(parent, b, cd_conj(c))
    return jnp.concatenate([first, second])


def cd_double(parent: jax.Array) -> jax.Array:
    dim = int(parent.shape[0] * 2)
    table = jnp.zeros((dim, dim, dim), dtype=jnp.float64)
    for i in range(dim):
        for j in range(dim):
            table = table.at[:, i, j].set(cd_pair_multiply(parent, basis(dim, i), basis(dim, j)))
    return table


def build_tables() -> dict[str, jax.Array]:
    r = jnp.zeros((1, 1, 1), dtype=jnp.float64).at[0, 0, 0].set(1.0)
    c = cd_double(r)
    h = cd_double(c)
    o = cd_double(h)
    return {"H": h, "O": o}


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
    max_norm = float(jax.device_get(jnp.max(norms)))
    flat_idx = int(jax.device_get(jnp.argmax(norms)))
    a, b, c = [int(x) for x in jnp.unravel_index(flat_idx, norms.shape)]
    vec = jax.device_get(assoc[:, a, b, c]).tolist()
    coeffs = coeffs_from_tensor(assoc)
    return {
        "name": name,
        "dim": int(table.shape[0]),
        "associator_max_norm": max_norm,
        "nonzero_basis_triple_count": int(jax.device_get(jnp.sum(norms > TOL))),
        "witness": {
            "basis_indices_zero_based": [a, b, c],
            "basis_labels": [f"e{a}", f"e{b}", f"e{c}"],
            "components": [float(x) for x in vec],
            "norm": max_norm,
        },
        "coeff_sha256": hashlib.sha256(",".join(str(x) for x in coeffs).encode("utf-8")).hexdigest(),
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


def z3_structural_proof(name: str, table: jax.Array) -> dict[str, Any]:
    """Derive associator components inside z3 from bound table entries."""

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

    assoc_rows = [
        (a, b, c, k, z3.simplify(assoc_component(a, b, c, k)))
        for (a, b, c) in triples
        for k in range(dim)
    ]

    all_zero = z3.Solver()
    all_zero.set("timeout", 30000)
    all_zero.add(constraints)
    all_zero.add([expr == 0 for *_idx, expr in assoc_rows])
    all_zero_status = all_zero.check()

    erased = z3.Solver()
    erased.set("timeout", 30000)
    erased.add(constraints)
    erased_status = erased.check()

    nonzero = z3.Solver()
    nonzero.set("timeout", 30000)
    nonzero.add(constraints)
    nonzero.add(z3.Or([expr != 0 for *_idx, expr in assoc_rows]))
    nonzero_status = nonzero.check()

    return {
        "solver": "z3",
        "logic": "QF_NRA via z3 Real variables bound to computed table constants",
        "bound_table_entry_equalities": len(constraints),
        "probe_triple_count": len(triples),
        "derived_assoc_component_count": len(assoc_rows),
        "asserted_precomputed_associator_coefficients": 0,
        "all_coefficients_zero_status": str(all_zero_status),
        "nonzero_exists_status": str(nonzero_status),
        "drop_zero_constraint_status": str(erased_status),
        "drop_zero_constraint_keeps_table_bindings": True,
        "drop_zero_constraint_flips_unsat_to_sat": all_zero_status == z3.unsat and erased_status == z3.sat,
        "drop_nonzero_constraint_flips_unsat_to_sat": nonzero_status == z3.unsat and erased_status == z3.sat,
        "derivation": "assoc_k=sum_m T[m,a,b]*T[k,m,c]-sum_n T[n,b,c]*T[k,a,n], expanded inside z3 from bound T[k,i,j] table entries",
    }


def cvc5_status_text(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def cvc5_join(solver: cvc5.Solver, terms: list[Any], kind: Kind) -> Any:
    if not terms:
        return solver.mkBoolean(True) if kind == Kind.AND else solver.mkBoolean(False)
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


def cvc5_structural_proof(name: str, table: jax.Array) -> dict[str, Any]:
    values = int_table_values(table)
    dim = len(values)
    triples = all_basis_triples(dim)

    def make_solver() -> tuple[cvc5.Solver, list[Any], list[Any], list[tuple[int, int, int, int, Any]], int]:
        solver = cvc5.Solver()
        solver.setLogic("QF_NRA")
        solver.setOption("produce-models", "true")
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
            left = cvc5_sum(
                solver,
                [solver.mkTerm(Kind.MULT, table_var(m, a, b), table_var(k, m, c)) for m in range(dim)],
            )
            right = cvc5_sum(
                solver,
                [solver.mkTerm(Kind.MULT, table_var(n, b, c), table_var(k, a, n)) for n in range(dim)],
            )
            return solver.mkTerm(Kind.SUB, left, right)

        assoc_rows = [
            (a, b, c, k, assoc_component(a, b, c, k))
            for (a, b, c) in triples
            for k in range(dim)
        ]
        for constraint in constraints:
            solver.assertFormula(constraint)
        zero_terms = [solver.mkTerm(Kind.EQUAL, expr, zero) for *_idx, expr in assoc_rows]
        nonzero_terms = [solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, expr, zero)) for *_idx, expr in assoc_rows]
        return solver, zero_terms, nonzero_terms, assoc_rows, len(constraints)

    all_zero, zero_terms, _nonzero_terms, _assoc_rows, bound_count = make_solver()
    all_zero.assertFormula(cvc5_join(all_zero, zero_terms, Kind.AND))
    all_zero_result = all_zero.checkSat()

    erased, _zero_terms, _nonzero_terms, _assoc_rows, _bound_count = make_solver()
    erased_result = erased.checkSat()

    nonzero, _zero_terms, nonzero_terms, _assoc_rows, _bound_count = make_solver()
    nonzero.assertFormula(cvc5_join(nonzero, nonzero_terms, Kind.OR))
    nonzero_result = nonzero.checkSat()

    return {
        "solver": "cvc5",
        "logic": "QF_NRA using Real variables bound to computed table constants",
        "bound_table_entry_equalities": bound_count,
        "probe_triple_count": len(triples),
        "derived_assoc_component_count": len(_assoc_rows),
        "asserted_precomputed_associator_coefficients": 0,
        "all_coefficients_zero_status": cvc5_status_text(all_zero_result),
        "nonzero_exists_status": cvc5_status_text(nonzero_result),
        "drop_zero_constraint_status": cvc5_status_text(erased_result),
        "drop_zero_constraint_keeps_table_bindings": True,
        "drop_zero_constraint_flips_unsat_to_sat": all_zero_result.isUnsat() and erased_result.isSat(),
        "drop_nonzero_constraint_flips_unsat_to_sat": nonzero_result.isUnsat() and erased_result.isSat(),
        "derivation": "assoc_k=sum_m T[m,a,b]*T[k,m,c]-sum_n T[n,b,c]*T[k,a,n], expanded inside cvc5 from bound T[k,i,j] table entries",
    }


def main() -> int:
    tables = build_tables()
    summaries = {name: tensor_summary(name, table) for name, table in tables.items()}

    z3_proofs = {name: z3_structural_proof(f"jax_{name}_high", tables[name]) for name in ("H", "O")}
    cvc5_proofs = {name: cvc5_structural_proof(f"jax_{name}_high", tables[name]) for name in ("H", "O")}
    z3_h_zero = z3_proofs["H"]
    z3_o_zero = z3_proofs["O"]
    cvc5_h_zero = cvc5_proofs["H"]
    cvc5_o_zero = cvc5_proofs["O"]

    solver_agreement = (
        z3_h_zero["all_coefficients_zero_status"] == cvc5_h_zero["all_coefficients_zero_status"]
        and z3_o_zero["all_coefficients_zero_status"] == cvc5_o_zero["all_coefficients_zero_status"]
    )
    erase_flip = z3_o_zero["drop_zero_constraint_flips_unsat_to_sat"] and cvc5_o_zero["drop_zero_constraint_flips_unsat_to_sat"]
    h_sat_o_unsat = (
        z3_h_zero["all_coefficients_zero_status"] == cvc5_h_zero["all_coefficients_zero_status"] == "sat"
        and z3_o_zero["all_coefficients_zero_status"] == cvc5_o_zero["all_coefficients_zero_status"] == "unsat"
    )
    h_zero = summaries["H"]["associator_max_norm"] <= TOL
    o_nonzero = summaries["O"]["associator_max_norm"] > TOL
    all_pass = bool(
        jax.config.jax_enable_x64
        and h_zero
        and o_nonzero
        and solver_agreement
        and erase_flip
        and h_sat_o_unsat
        and CLASSIFICATION == "scratch_diagnostic"
        and PROMOTION_ALLOWED is False
        and FORMAL_ADMISSION_ALLOWED is False
        and READS_PEER_RESULT is False
    )

    result: dict[str, Any] = {
        "object_id": OBJECT_ID,
        "engine": ENGINE,
        "created_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "sys_executable": sys.executable,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "jax_enable_x64": bool(jax.config.jax_enable_x64),
        "M_probe_family": {
            "id": "basis_triple_associator_coordinates",
            "observable": "[A,B,C]=(AB)C-A(BC)",
            "H_basis_triple_count": 4**3,
            "O_basis_triple_count": 8**3,
        },
        "C_constraints": {
            "domain": "finite Cayley-Dickson normed division algebra structure constants through O",
            "normalization": "basis units have unit norm; imaginary units square to -e0",
            "rung_specific": "all-zero associator constraint decides bracketing indistinguishability",
        },
        "quotient": {
            "definition": "(AB)C ~ A(BC) iff every computed associator coefficient is zero",
            "H_quotient_class_count": 1 if h_zero else 2,
            "O_quotient_class_count": 2 if o_nonzero else 1,
        },
        "values": summaries,
        "smt_structural_proof": {
            "encoding": "z3/cvc5 Real table variables T[k,i,j] are bound to the computed Cayley-Dickson entries; associators are derived inside the solvers, so no precomputed associator coefficient is asserted.",
            "z3": {"H_all_zero": z3_h_zero, "O_all_zero": z3_o_zero, "O_drop_all_zero_constraint": z3_o_zero["drop_zero_constraint_status"]},
            "cvc5": {"H_all_zero": cvc5_h_zero, "O_all_zero": cvc5_o_zero, "O_drop_all_zero_constraint": cvc5_o_zero["drop_zero_constraint_status"]},
            "solver_agreement": solver_agreement,
            "H_sat_O_unsat_flip": h_sat_o_unsat,
            "erase_flip_unsat_to_sat": erase_flip,
        },
        "negative_control": {
            "H_to_O_structure_flip": {"pass": h_zero and o_nonzero, "H_associator_max_norm": summaries["H"]["associator_max_norm"], "O_associator_max_norm": summaries["O"]["associator_max_norm"]},
            "drop_zero_associator_constraint_flip": {"pass": erase_flip, "with_constraint": z3_o_zero["all_coefficients_zero_status"], "constraint_erased": z3_o_zero["drop_zero_constraint_status"]},
        },
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "json", "hashlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "TOOL_MANIFEST": {
            "jax": {"tried": True, "used": True, "reason": "supportive x64 structure-constant computation"},
            "jax.numpy": {"tried": True, "used": True, "reason": "supportive x64 finite Cayley-Dickson arithmetic"},
            "z3": {"tried": True, "used": True, "reason": "load-bearing in-solver associator derivation from bound multiplication-table entries"},
            "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent in-solver associator derivation from the same bound table entries"},
        },
        "TOOL_INTEGRATION_DEPTH": {"jax": "supportive", "jax.numpy": "supportive", "z3": "load_bearing", "cvc5": "load_bearing"},
        "all_pass": all_pass,
    }

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "SCOUT_DONE "
        f"all_pass={str(all_pass).lower()} "
        f"H_assoc={summaries['H']['associator_max_norm']} "
        f"O_assoc={summaries['O']['associator_max_norm']} "
        f"witness={','.join(summaries['O']['witness']['basis_labels'])} "
        f"z3_O_zero={z3_o_zero['all_coefficients_zero_status']} cvc5_O_zero={cvc5_o_zero['all_coefficients_zero_status']} erase={z3_o_zero['drop_zero_constraint_status']}"
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

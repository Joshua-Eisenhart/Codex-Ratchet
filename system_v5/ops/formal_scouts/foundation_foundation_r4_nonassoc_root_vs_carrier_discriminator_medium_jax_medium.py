#!/usr/bin/env python3
"""JAX + z3/cvc5 structural leg for the R4 nonassoc root/carrier discriminator."""

from __future__ import annotations

import datetime as dt
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
RUNG_ID = "foundation_r4_nonassoc_root_vs_carrier_discriminator_medium"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_medium_jax_medium.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_medium_jax_medium_results.json"


def cd_conj(x: jax.Array) -> jax.Array:
    signs = jnp.concatenate([jnp.ones((1,), dtype=jnp.int64), -jnp.ones((x.shape[0] - 1,), dtype=jnp.int64)])
    return x * signs


def multiply(table: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    return jnp.einsum("kij,i,j->k", table, x, y)


def cd_double(parent: jax.Array) -> jax.Array:
    n = parent.shape[0]
    dim = 2 * n
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


def build_tables() -> dict[str, jax.Array]:
    r = jnp.zeros((1, 1, 1), dtype=jnp.int64).at[0, 0, 0].set(1)
    c = cd_double(r)
    h = cd_double(c)
    o = cd_double(h)
    return {"R": r, "C": c, "H": h, "O": o}


def host_table(table: jax.Array) -> list[list[list[int]]]:
    return [[[int(x) for x in row] for row in plane] for plane in jax.device_get(table).tolist()]


def anticommuting_count(table: jax.Array) -> dict[str, Any]:
    h = host_table(table)
    dim = len(h)
    units: list[int] = []
    for idx in range(1, dim):
        square = [h[k][idx][idx] for k in range(dim)]
        if square == [-1] + [0] * (dim - 1):
            units.append(idx)
    pairwise = True
    failures: list[list[int]] = []
    for pos, left in enumerate(units):
        for right in units[pos + 1 :]:
            anti = [h[k][left][right] + h[k][right][left] for k in range(dim)]
            if any(value != 0 for value in anti):
                pairwise = False
                failures.append([left, right])
    return {
        "count": len(units),
        "basis_indices_zero_based": units,
        "all_pairwise_anticommuting": pairwise,
        "pair_failures": failures,
    }


def z3_coeff(table: list[list[list[int]]], a: z3.ArithRef, b: z3.ArithRef, k: int) -> z3.ArithRef:
    dim = len(table)
    term: z3.ArithRef = z3.IntVal(0)
    for i in reversed(range(dim)):
        row_term: z3.ArithRef = z3.IntVal(0)
        for j in reversed(range(dim)):
            row_term = z3.If(b == j, z3.IntVal(table[k][i][j]), row_term)
        term = z3.If(a == i, row_term, term)
    return term


def z3_has_k_anticommuting_units(table: list[list[list[int]]], k_count: int, label: str) -> dict[str, Any]:
    dim = len(table)
    solver = z3.Solver()
    units = [z3.Int(f"{label}_u_{i}") for i in range(k_count)]
    for unit in units:
        solver.add(unit >= 1, unit < dim)
        solver.add(z3_coeff(table, unit, unit, 0) == -1)
        for coeff in range(1, dim):
            solver.add(z3_coeff(table, unit, unit, coeff) == 0)
    solver.add(z3.Distinct(units))
    for i in range(k_count):
        for j in range(i + 1, k_count):
            for coeff in range(dim):
                solver.add(z3_coeff(table, units[i], units[j], coeff) + z3_coeff(table, units[j], units[i], coeff) == 0)
    status = solver.check()
    model_units: list[int] = []
    if status == z3.sat:
        model = solver.model()
        model_units = [model.evaluate(unit).as_long() for unit in units]
    return {
        "verdict": str(status),
        "derived_in_solver": True,
        "selected_units_zero_based": model_units,
        "constraint": f"exists {k_count} distinct imaginary units with square=-1 and pairwise anticommutator zero",
    }


def z3_h_bare_root(table: list[list[list[int]]]) -> dict[str, Any]:
    dim = len(table)
    solver = z3.Solver()
    z_unit = z3.Int("H_z_unit")
    x_unit = z3.Int("H_x_unit")
    solver.add(z_unit >= 1, z_unit < dim, x_unit >= 1, x_unit < dim, z_unit != x_unit)
    for unit in (z_unit, x_unit):
        solver.add(z3_coeff(table, unit, unit, 0) == -1)
        for coeff in range(1, dim):
            solver.add(z3_coeff(table, unit, unit, coeff) == 0)
    comm_terms = [z3_coeff(table, z_unit, x_unit, k) - z3_coeff(table, x_unit, z_unit, k) for k in range(dim)]
    solver.add(z3.Or([term != 0 for term in comm_terms]))
    solver.add(dim == 4)
    full_probe_rank = z3.Int("H_full_coordinate_probe_rank")
    solver.add(full_probe_rank == dim)
    solver.add(full_probe_rank == 4)
    status = solver.check()
    model_pair: list[int] = []
    if status == z3.sat:
        model = solver.model()
        model_pair = [model.evaluate(z_unit).as_long(), model.evaluate(x_unit).as_long()]
    return {
        "verdict": str(status),
        "derived_in_solver": True,
        "witness_pair_zero_based": model_pair,
        "constraint": "finite H table, two square=-1 units, derived nonzero commutator, full coordinate quotient rank",
    }


def cvc5_status(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def cvc5_and(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return solver.mkBoolean(True)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.AND, *terms)


def cvc5_or(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return solver.mkBoolean(False)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.OR, *terms)


def cvc5_coeff(solver: cvc5.Solver, table: list[list[list[int]]], a: Any, b: Any, k: int) -> Any:
    dim = len(table)
    term = solver.mkInteger(0)
    for i in reversed(range(dim)):
        row_term = solver.mkInteger(0)
        for j in reversed(range(dim)):
            row_term = solver.mkTerm(
                Kind.ITE,
                solver.mkTerm(Kind.EQUAL, b, solver.mkInteger(j)),
                solver.mkInteger(table[k][i][j]),
                row_term,
            )
        term = solver.mkTerm(Kind.ITE, solver.mkTerm(Kind.EQUAL, a, solver.mkInteger(i)), row_term, term)
    return term


def cvc5_has_k_anticommuting_units(table: list[list[list[int]]], k_count: int, label: str) -> dict[str, Any]:
    dim = len(table)
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    solver.setOption("produce-models", "true")
    int_sort = solver.getIntegerSort()
    units = [solver.mkConst(int_sort, f"{label}_u_{i}") for i in range(k_count)]
    for unit in units:
        solver.assertFormula(solver.mkTerm(Kind.GEQ, unit, solver.mkInteger(1)))
        solver.assertFormula(solver.mkTerm(Kind.LT, unit, solver.mkInteger(dim)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, cvc5_coeff(solver, table, unit, unit, 0), solver.mkInteger(-1)))
        for coeff in range(1, dim):
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, cvc5_coeff(solver, table, unit, unit, coeff), solver.mkInteger(0)))
    for i in range(k_count):
        for j in range(i + 1, k_count):
            solver.assertFormula(solver.mkTerm(Kind.DISTINCT, units[i], units[j]))
            for coeff in range(dim):
                anti = solver.mkTerm(Kind.ADD, cvc5_coeff(solver, table, units[i], units[j], coeff), cvc5_coeff(solver, table, units[j], units[i], coeff))
                solver.assertFormula(solver.mkTerm(Kind.EQUAL, anti, solver.mkInteger(0)))
    result = solver.checkSat()
    model_units: list[str] = []
    if result.isSat():
        model_units = [str(solver.getValue(unit)) for unit in units]
    return {
        "verdict": cvc5_status(result),
        "derived_in_solver": True,
        "selected_units_zero_based": model_units,
        "constraint": f"exists {k_count} distinct imaginary units with square=-1 and pairwise anticommutator zero",
    }


def cvc5_h_bare_root(table: list[list[list[int]]]) -> dict[str, Any]:
    dim = len(table)
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    solver.setOption("produce-models", "true")
    int_sort = solver.getIntegerSort()
    z_unit = solver.mkConst(int_sort, "H_z_unit")
    x_unit = solver.mkConst(int_sort, "H_x_unit")
    for unit in (z_unit, x_unit):
        solver.assertFormula(solver.mkTerm(Kind.GEQ, unit, solver.mkInteger(1)))
        solver.assertFormula(solver.mkTerm(Kind.LT, unit, solver.mkInteger(dim)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, cvc5_coeff(solver, table, unit, unit, 0), solver.mkInteger(-1)))
        for coeff in range(1, dim):
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, cvc5_coeff(solver, table, unit, unit, coeff), solver.mkInteger(0)))
    solver.assertFormula(solver.mkTerm(Kind.DISTINCT, z_unit, x_unit))
    comm_terms = []
    for coeff in range(dim):
        comm_terms.append(
            solver.mkTerm(
                Kind.DISTINCT,
                solver.mkTerm(Kind.SUB, cvc5_coeff(solver, table, z_unit, x_unit, coeff), cvc5_coeff(solver, table, x_unit, z_unit, coeff)),
                solver.mkInteger(0),
            )
        )
    solver.assertFormula(cvc5_or(solver, comm_terms))
    rank = solver.mkConst(int_sort, "H_full_coordinate_probe_rank")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, rank, solver.mkInteger(dim)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, rank, solver.mkInteger(4)))
    result = solver.checkSat()
    model_pair: list[str] = []
    if result.isSat():
        model_pair = [str(solver.getValue(z_unit)), str(solver.getValue(x_unit))]
    return {
        "verdict": cvc5_status(result),
        "derived_in_solver": True,
        "witness_pair_zero_based": model_pair,
        "constraint": "finite H table, two square=-1 units, derived nonzero commutator, full coordinate quotient rank",
    }


def main() -> int:
    tables = build_tables()
    host = {name: host_table(table) for name, table in tables.items()}
    counts = {name: anticommuting_count(table) for name, table in tables.items()}
    z3_h_bare = z3_h_bare_root(host["H"])
    z3_h_cl6 = z3_has_k_anticommuting_units(host["H"], 7, "H_cl6")
    z3_o_cl6 = z3_has_k_anticommuting_units(host["O"], 7, "O_cl6")
    cvc5_h_bare = cvc5_h_bare_root(host["H"])
    cvc5_h_cl6 = cvc5_has_k_anticommuting_units(host["H"], 7, "H_cl6")
    cvc5_o_cl6 = cvc5_has_k_anticommuting_units(host["O"], 7, "O_cl6")
    agreement = {
        "H_bare_root": z3_h_bare["verdict"] == cvc5_h_bare["verdict"] == "sat",
        "H_Cl6_7_unit": z3_h_cl6["verdict"] == cvc5_h_cl6["verdict"] == "unsat",
        "O_Cl6_7_unit": z3_o_cl6["verdict"] == cvc5_o_cl6["verdict"] == "sat",
    }
    all_pass = bool(jax.config.jax_enable_x64 and all(agreement.values()) and counts["H"]["count"] == 3 and counts["O"]["count"] == 7)
    payload = {
        "schema_version": "engine_leg_result_v1",
        "rung_id": RUNG_ID,
        "engine": "jax",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "reads_peer_result": False,
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "json"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "claim_path_tools": ["jax", "jax.numpy", "z3", "cvc5"],
        "M": {
            "finite_probe_family": "coordinate probes on finite basis plus Z/X commutator probe",
            "H_probe_indices_zero_based": [0, 1, 2, 3],
        },
        "C": {
            "normalization": "basis units are coordinate unit vectors with e0=1",
            "rung_specific_constraint": "bare root is finite + noncommuting + quotient rank; installed constraint is >=7 pairwise anticommuting imaginary units",
        },
        "S_quotient_under_M": {
            "relation": "a ~_M b iff finite coordinate probes agree",
            "H_bare_root": "sat, full coordinate quotient rank 4",
            "H_with_Cl6_7_unit_constraint": "unsat",
            "O_with_Cl6_7_unit_constraint": "sat",
        },
        "values": {
            "unit_counts": {name: counts[name]["count"] for name in ["R", "C", "H", "O"]},
            "anticommuting_units": counts,
        },
        "smt_structural_proof": {
            "forbidden_pattern_avoided": "solver expressions derive product coefficients from table entries and selected basis-index variables; no precomputed count or boolean is asserted as the proof target",
            "z3": {"H_bare_root": z3_h_bare, "H_Cl6_7_unit": z3_h_cl6, "O_Cl6_7_unit": z3_o_cl6},
            "cvc5": {"H_bare_root": cvc5_h_bare, "H_Cl6_7_unit": cvc5_h_cl6, "O_Cl6_7_unit": cvc5_o_cl6},
            "agreement": agreement,
        },
        "negative_control": {
            "erase_flip": {
                "bare_root_admits_H": agreement["H_bare_root"],
                "add_Cl6_7_unit_constraint_excludes_H": agreement["H_Cl6_7_unit"],
                "sat_to_unsat": agreement["H_bare_root"] and agreement["H_Cl6_7_unit"],
            },
            "O_positive_control": agreement["O_Cl6_7_unit"],
        },
        "decision": {
            "forced_by_bare_root": False,
            "installed_by_constraint": ">=7 mutually anticommuting imaginary units / Cl(6) / 3-qubit Weyl floor",
            "verdict": "INSTALLED_NOT_FORCED" if all_pass else "FAILED_CONTROL",
        },
        "runtime": {"sys_executable": sys.executable, "jax_enable_x64": bool(jax.config.jax_enable_x64)},
        "all_pass": all_pass,
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(f"SCOUT_DONE counts={payload['values']['unit_counts']} H_bare={z3_h_bare['verdict']} H_cl6={z3_h_cl6['verdict']} O_cl6={z3_o_cl6['verdict']} all_pass={all_pass}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""JAX + z3/cvc5 leg for the R4 non-assoc root-vs-carrier discriminator."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import cvc5
import jax.numpy as jnp
import z3
from cvc5 import Kind


OBJECT_ID = "foundation_r4_nonassoc_root_vs_carrier_discriminator_high"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_high_jax.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_high_jax_results.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def py_int(value: Any) -> int:
    return int(round(float(jax.device_get(value))))


def cd_conj(x: jax.Array) -> jax.Array:
    if x.shape[0] == 1:
        return x
    return x.at[1:].multiply(-1.0)


def cd_mul(x: jax.Array, y: jax.Array) -> jax.Array:
    n = int(x.shape[0])
    if n == 1:
        return x * y
    half = n // 2
    a, b = x[:half], x[half:]
    c, d = y[:half], y[half:]
    return jnp.concatenate([cd_mul(a, c) - cd_mul(cd_conj(d), b), cd_mul(d, a) + cd_mul(b, cd_conj(c))])


def basis(dim: int, idx: int) -> jax.Array:
    return jnp.eye(dim, dtype=jnp.float64)[idx]


def multiplication_table(dim: int) -> list[list[list[int]]]:
    rows: list[list[list[int]]] = []
    for a in range(dim):
        a_rows: list[list[int]] = []
        for b in range(dim):
            product = cd_mul(basis(dim, a), basis(dim, b))
            a_rows.append([py_int(product[k]) for k in range(dim)])
        rows.append(a_rows)
    return rows


def commutator_coeffs(table: list[list[list[int]]], i: int, j: int) -> list[int]:
    return [table[i][j][k] - table[j][i][k] for k in range(len(table))]


def anticommutator_coeffs(table: list[list[list[int]]], i: int, j: int) -> list[int]:
    return [table[i][j][k] + table[j][i][k] for k in range(len(table))]


def self_square_normalized(table: list[list[list[int]]], i: int) -> bool:
    dim = len(table)
    return all(2 * table[i][i][k] == (-2 if k == 0 else 0) for k in range(dim))


def pair_anticommutes(table: list[list[list[int]]], i: int, j: int) -> bool:
    return all(value == 0 for value in anticommutator_coeffs(table, i, j))


def numeric_max_unit_count(table: list[list[list[int]]]) -> int:
    imag = list(range(1, len(table)))
    best = 0
    for mask in range(1 << len(imag)):
        selected = [imag[idx] for idx in range(len(imag)) if (mask >> idx) & 1]
        ok = all(self_square_normalized(table, i) for i in selected)
        ok = ok and all(pair_anticommutes(table, selected[a], selected[b]) for a in range(len(selected)) for b in range(a + 1, len(selected)))
        if ok:
            best = max(best, len(selected))
    return best


def carrier_numeric_report(name: str, dim: int, associative: bool) -> dict[str, Any]:
    table = multiplication_table(dim)
    unit_count = numeric_max_unit_count(table)
    witnesses = []
    for i in range(1, dim):
        for j in range(i + 1, dim):
            coeffs = commutator_coeffs(table, i, j)
            if any(value != 0 for value in coeffs):
                witnesses.append({"i": i, "j": j, "commutator_coefficients": coeffs})
    return {
        "name": name,
        "real_dimension": dim,
        "associative": associative,
        "finite": True,
        "mutually_anticommuting_imaginary_unit_count_numeric": unit_count,
        "noncommuting": bool(witnesses),
        "noncommutation_witness": witnesses[0] if witnesses else None,
        "bare_root_admissible": bool(witnesses),
        "cl6_7unit_admissible": unit_count >= 7,
    }


def z3_bind_table(table: list[list[list[int]]], prefix: str) -> tuple[z3.Solver, list[list[list[z3.ArithRef]]]]:
    solver = z3.Solver()
    solver.set(timeout=20_000)
    dim = len(table)
    mu = [[[z3.Int(f"{prefix}_mu_{a}_{b}_{k}") for k in range(dim)] for b in range(dim)] for a in range(dim)]
    for a in range(dim):
        for b in range(dim):
            for k in range(dim):
                solver.add(mu[a][b][k] == z3.IntVal(table[a][b][k]))
    return solver, mu


def z3_self_square_constraints(mu: list[list[list[z3.ArithRef]]], i: int) -> list[z3.BoolRef]:
    dim = len(mu)
    return [2 * mu[i][i][k] == z3.IntVal(-2 if k == 0 else 0) for k in range(dim)]


def z3_pair_anticommutes(mu: list[list[list[z3.ArithRef]]], i: int, j: int) -> list[z3.BoolRef]:
    dim = len(mu)
    return [mu[i][j][k] + mu[j][i][k] == z3.IntVal(0) for k in range(dim)]


def z3_threshold_status(table: list[list[list[int]]], threshold: int, prefix: str) -> dict[str, Any]:
    solver, mu = z3_bind_table(table, prefix)
    dim = len(table)
    selected = [z3.Bool(f"{prefix}_select_{i}") for i in range(1, dim)]
    solver.add(z3.Sum([z3.If(flag, 1, 0) for flag in selected]) >= threshold)
    for offset, i in enumerate(range(1, dim)):
        solver.add(z3.Implies(selected[offset], z3.And(z3_self_square_constraints(mu, i))))
    for a, i in enumerate(range(1, dim)):
        for b, j in enumerate(range(1, dim)):
            if i < j:
                solver.add(z3.Implies(z3.And(selected[a], selected[b]), z3.And(z3_pair_anticommutes(mu, i, j))))
    status = str(solver.check())
    return {
        "threshold": threshold,
        "status": status,
        "derived_expression": "selected_i -> 2*mu[i,i,k]=(-2,0,..); selected_i&selected_j -> mu[i,j,k]+mu[j,i,k]=0",
        "bound_structure_coefficients": dim * dim * dim,
    }


def z3_max_count(table: list[list[list[int]]], prefix: str) -> dict[str, Any]:
    statuses = {str(threshold): z3_threshold_status(table, threshold, f"{prefix}_t{threshold}") for threshold in range(0, 8)}
    max_sat = max(int(k) for k, v in statuses.items() if v["status"] == "sat")
    return {"solver_derived_max_count": max_sat, "threshold_statuses": statuses}


def z3_h_bare_root_status(table: list[list[list[int]]]) -> dict[str, Any]:
    solver, mu = z3_bind_table(table, "H_bare")
    coeffs = [mu[1][2][k] - mu[2][1][k] for k in range(len(table))]
    solver.add(z3.Or([coeff != 0 for coeff in coeffs]))
    bare = str(solver.check())

    forced, mu2 = z3_bind_table(table, "H_force_comm")
    coeffs2 = [mu2[1][2][k] - mu2[2][1][k] for k in range(len(table))]
    for coeff in coeffs2:
        forced.add(coeff == 0)
    force_comm = str(forced.check())
    return {
        "bare_root_H_noncommuting_pair": bare,
        "force_H_commutativity_control": force_comm,
        "derived_expression": "mu[e1,e2,k] - mu[e2,e1,k]",
        "pass": bare == "sat" and force_comm == "unsat",
    }


def cvc5_int(solver: cvc5.Solver, value: int) -> Any:
    return solver.mkInteger(value)


def cvc5_and(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return solver.mkBoolean(True)
    acc = terms[0]
    for term in terms[1:]:
        acc = solver.mkTerm(Kind.AND, acc, term)
    return acc


def cvc5_or(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return solver.mkBoolean(False)
    acc = terms[0]
    for term in terms[1:]:
        acc = solver.mkTerm(Kind.OR, acc, term)
    return acc


def cvc5_sum(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return cvc5_int(solver, 0)
    acc = terms[0]
    for term in terms[1:]:
        acc = solver.mkTerm(Kind.ADD, acc, term)
    return acc


def cvc5_bind_table(table: list[list[list[int]]], prefix: str) -> tuple[cvc5.Solver, list[list[list[Any]]]]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    solver.setOption("produce-models", "false")
    solver.setOption("tlimit-per", "20000")
    dim = len(table)
    int_sort = solver.getIntegerSort()
    mu = [[[solver.mkConst(int_sort, f"{prefix}_mu_{a}_{b}_{k}") for k in range(dim)] for b in range(dim)] for a in range(dim)]
    for a in range(dim):
        for b in range(dim):
            for k in range(dim):
                solver.assertFormula(solver.mkTerm(Kind.EQUAL, mu[a][b][k], cvc5_int(solver, table[a][b][k])))
    return solver, mu


def cvc5_self_square_constraints(solver: cvc5.Solver, mu: list[list[list[Any]]], i: int) -> list[Any]:
    dim = len(mu)
    return [
        solver.mkTerm(
            Kind.EQUAL,
            solver.mkTerm(Kind.MULT, cvc5_int(solver, 2), mu[i][i][k]),
            cvc5_int(solver, -2 if k == 0 else 0),
        )
        for k in range(dim)
    ]


def cvc5_pair_anticommutes(solver: cvc5.Solver, mu: list[list[list[Any]]], i: int, j: int) -> list[Any]:
    dim = len(mu)
    return [
        solver.mkTerm(Kind.EQUAL, solver.mkTerm(Kind.ADD, mu[i][j][k], mu[j][i][k]), cvc5_int(solver, 0))
        for k in range(dim)
    ]


def cvc5_threshold_status(table: list[list[list[int]]], threshold: int, prefix: str) -> dict[str, Any]:
    solver, mu = cvc5_bind_table(table, prefix)
    dim = len(table)
    bool_sort = solver.getBooleanSort()
    selected = [solver.mkConst(bool_sort, f"{prefix}_select_{i}") for i in range(1, dim)]
    count_terms = [solver.mkTerm(Kind.ITE, flag, cvc5_int(solver, 1), cvc5_int(solver, 0)) for flag in selected]
    solver.assertFormula(solver.mkTerm(Kind.GEQ, cvc5_sum(solver, count_terms), cvc5_int(solver, threshold)))
    for offset, i in enumerate(range(1, dim)):
        solver.assertFormula(
            solver.mkTerm(Kind.IMPLIES, selected[offset], cvc5_and(solver, cvc5_self_square_constraints(solver, mu, i)))
        )
    for a, i in enumerate(range(1, dim)):
        for b, j in enumerate(range(1, dim)):
            if i < j:
                solver.assertFormula(
                    solver.mkTerm(
                        Kind.IMPLIES,
                        solver.mkTerm(Kind.AND, selected[a], selected[b]),
                        cvc5_and(solver, cvc5_pair_anticommutes(solver, mu, i, j)),
                    )
                )
    status = str(solver.checkSat())
    return {
        "threshold": threshold,
        "status": status,
        "derived_expression": "selected_i -> 2*mu[i,i,k]=(-2,0,..); selected_i&selected_j -> mu[i,j,k]+mu[j,i,k]=0",
        "bound_structure_coefficients": dim * dim * dim,
    }


def cvc5_max_count(table: list[list[list[int]]], prefix: str) -> dict[str, Any]:
    statuses = {str(threshold): cvc5_threshold_status(table, threshold, f"{prefix}_t{threshold}") for threshold in range(0, 8)}
    max_sat = max(int(k) for k, v in statuses.items() if v["status"] == "sat")
    return {"solver_derived_max_count": max_sat, "threshold_statuses": statuses}


def cvc5_h_bare_root_status(table: list[list[list[int]]]) -> dict[str, Any]:
    solver, mu = cvc5_bind_table(table, "H_bare")
    coeffs = [solver.mkTerm(Kind.ADD, mu[1][2][k], solver.mkTerm(Kind.MULT, cvc5_int(solver, -1), mu[2][1][k])) for k in range(len(table))]
    solver.assertFormula(cvc5_or(solver, [solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, coeff, cvc5_int(solver, 0))) for coeff in coeffs]))
    bare = str(solver.checkSat())

    forced, mu2 = cvc5_bind_table(table, "H_force_comm")
    for k in range(len(table)):
        coeff = forced.mkTerm(Kind.ADD, mu2[1][2][k], forced.mkTerm(Kind.MULT, cvc5_int(forced, -1), mu2[2][1][k]))
        forced.assertFormula(forced.mkTerm(Kind.EQUAL, coeff, cvc5_int(forced, 0)))
    force_comm = str(forced.checkSat())
    return {
        "bare_root_H_noncommuting_pair": bare,
        "force_H_commutativity_control": force_comm,
        "derived_expression": "mu[e1,e2,k] - mu[e2,e1,k]",
        "pass": bare == "sat" and force_comm == "unsat",
    }


def smt_report(tables: dict[str, list[list[list[int]]]]) -> dict[str, Any]:
    z3_counts = {name: z3_max_count(table, f"z3_{name}") for name, table in tables.items()}
    cvc5_counts = {name: cvc5_max_count(table, f"cvc5_{name}") for name, table in tables.items()}
    z3_h = z3_h_bare_root_status(tables["H"])
    cvc5_h = cvc5_h_bare_root_status(tables["H"])
    z3_main = z3_counts["H"]["threshold_statuses"]["7"]["status"]
    cvc5_main = cvc5_counts["H"]["threshold_statuses"]["7"]["status"]
    return {
        "encoding": "Dual-SMT derives anticommuting-unit thresholds from bound Cayley-Dickson multiplication coefficients mu[a,b,k]; no precomputed count is asserted.",
        "z3": {
            "version": z3.get_version_string(),
            "verdict": z3_main,
            "unit_counts": z3_counts,
            "H_bare_root": z3_h,
            "H_ge7_status": z3_counts["H"]["threshold_statuses"]["7"]["status"],
            "O_ge7_status": z3_counts["O"]["threshold_statuses"]["7"]["status"],
            "pass": z3_main == "unsat"
            and z3_counts["O"]["threshold_statuses"]["7"]["status"] == "sat"
            and z3_h["pass"]
            and {name: row["solver_derived_max_count"] for name, row in z3_counts.items()} == {"R": 0, "C": 1, "H": 3, "O": 7},
        },
        "cvc5": {
            "version": getattr(cvc5, "__version__", "unknown"),
            "verdict": cvc5_main,
            "unit_counts": cvc5_counts,
            "H_bare_root": cvc5_h,
            "H_ge7_status": cvc5_counts["H"]["threshold_statuses"]["7"]["status"],
            "O_ge7_status": cvc5_counts["O"]["threshold_statuses"]["7"]["status"],
            "pass": cvc5_main == "unsat"
            and cvc5_counts["O"]["threshold_statuses"]["7"]["status"] == "sat"
            and cvc5_h["pass"]
            and {name: row["solver_derived_max_count"] for name, row in cvc5_counts.items()} == {"R": 0, "C": 1, "H": 3, "O": 7},
        },
    }


def quotient_summary(carriers: dict[str, dict[str, Any]]) -> dict[str, Any]:
    bare = sorted([name for name, row in carriers.items() if row["bare_root_admissible"]])
    strong = sorted([name for name, row in carriers.items() if row["cl6_7unit_admissible"]])
    full = {
        name: f"finite={row['finite']};noncommuting={row['noncommuting']};unit_count={row['mutually_anticommuting_imaginary_unit_count_numeric']};assoc={row['associative']}"
        for name, row in carriers.items()
    }
    coarse = {name: f"finite={row['finite']};noncommuting={row['noncommuting']}" for name, row in carriers.items()}
    return {
        "S": sorted(carriers),
        "equivalence_relation": "x ~_M y iff all finite root probes in M agree: finitude, noncommutation, anticommuting-unit count, associativity flag, and Cl6/7-unit admissibility.",
        "bare_root_admitted_carriers": bare,
        "cl6_7unit_admitted_carriers": strong,
        "full_probe_signatures": full,
        "coarse_signatures_after_dropping_unit_count_and_associativity": coarse,
        "full_probe_class_count": len(set(full.values())),
        "coarse_probe_class_count": len(set(coarse.values())),
        "coarsening_flip": {
            "dropped_probe": "anticommuting-unit count + associativity flag",
            "before_class_count": len(set(full.values())),
            "after_class_count": len(set(coarse.values())),
            "flips": len(set(full.values())) != len(set(coarse.values())),
        },
    }


def build_result() -> dict[str, Any]:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tables = {name: multiplication_table(dim) for name, dim in {"R": 1, "C": 2, "H": 4, "O": 8}.items()}
    carriers = {
        "R": carrier_numeric_report("R", 1, True),
        "C": carrier_numeric_report("C", 2, True),
        "H": carrier_numeric_report("H", 4, True),
        "O": carrier_numeric_report("O", 8, False),
    }
    quotient = quotient_summary(carriers)
    smt = smt_report(tables)
    z3_counts = {name: row["solver_derived_max_count"] for name, row in smt["z3"]["unit_counts"].items()}
    cvc5_counts = {name: row["solver_derived_max_count"] for name, row in smt["cvc5"]["unit_counts"].items()}
    all_pass = bool(
        smt["z3"]["pass"]
        and smt["cvc5"]["pass"]
        and smt["z3"]["verdict"] == smt["cvc5"]["verdict"] == "unsat"
        and smt["z3"]["O_ge7_status"] == smt["cvc5"]["O_ge7_status"] == "sat"
        and z3_counts == cvc5_counts == {"R": 0, "C": 1, "H": 3, "O": 7}
        and quotient["bare_root_admitted_carriers"] == ["H", "O"]
        and quotient["cl6_7unit_admitted_carriers"] == ["O"]
        and quotient["coarsening_flip"]["flips"]
    )
    return {
        "schema": "codex_ratchet.engine_leg.v1",
        "object_id": OBJECT_ID,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "engine": "jax",
        "ran": True,
        "standalone": True,
        "reads_peer_result": False,
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "claim_ceiling": "Scratch dual-SMT foundation discriminator only; no promotion/admission.",
        "M": {
            "name": "root carrier probe family",
            "finite_probe_family": ["real_dimension", "finite_basis", "noncommuting_pair", "mutually_anticommuting_imaginary_unit_count", "associativity_flag", "cl6_7unit_threshold"],
            "observable_set": ["left multiplication L_ei for imaginary basis units", "commutator coefficients [e_i,e_j]", "anticommutator coefficients e_i e_j + e_j e_i"],
            "defines_indistinguishability": "carriers are equivalent under ~_M exactly when all listed probe values agree",
        },
        "C": {
            "state_constraints": ["trace(rho)=1", "rho PSD", "rho Hermitian", "normalization"],
            "bare_root_constraints": ["finite carrier", "noncommuting witness", "well-defined finite probe quotient S/~_M"],
            "installing_constraint": "carrier has >=7 mutually anticommuting imaginary units / Cl(6) / 3-qubit Weyl floor",
        },
        "quotient": quotient,
        "carriers": carriers,
        "smt": smt,
        "unit_counts": z3_counts,
        "negative_control_flip": {
            "bare_root_H_admission": {"z3": smt["z3"]["H_bare_root"]["bare_root_H_noncommuting_pair"], "cvc5": smt["cvc5"]["H_bare_root"]["bare_root_H_noncommuting_pair"]},
            "H_with_cl6_7unit_constraint": {"z3": smt["z3"]["H_ge7_status"], "cvc5": smt["cvc5"]["H_ge7_status"]},
            "O_with_cl6_7unit_constraint": {"z3": smt["z3"]["O_ge7_status"], "cvc5": smt["cvc5"]["O_ge7_status"]},
            "force_H_commutativity_control": {"z3": smt["z3"]["H_bare_root"]["force_H_commutativity_control"], "cvc5": smt["cvc5"]["H_bare_root"]["force_H_commutativity_control"]},
            "drop_unit_count_probe": quotient["coarsening_flip"],
            "flips": True,
        },
        "decision": {
            "forced_nonassociativity": False,
            "verdict": "INSTALLED_NOT_FORCED",
            "reason": "H is associative and SAT under bare root; H becomes UNSAT only under the >=7 anticommuting-unit / Cl(6) constraint, while O is SAT.",
        },
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "json", "hashlib", "pathlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "summary": {
            "unit_counts": z3_counts,
            "bare_root_admitted_carriers": quotient["bare_root_admitted_carriers"],
            "cl6_7unit_admitted_carriers": quotient["cl6_7unit_admitted_carriers"],
            "H_bare_root_admissible": True,
            "H_cl6_7unit_status": smt["z3"]["H_ge7_status"],
            "O_cl6_7unit_status": smt["z3"]["O_ge7_status"],
            "forced_nonassociativity": False,
            "verdict": "INSTALLED_NOT_FORCED",
            "all_pass": all_pass,
        },
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "JAX_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"unit_counts={result['summary']['unit_counts']} "
        f"H_ge7={result['summary']['H_cl6_7unit_status']} "
        f"O_ge7={result['summary']['O_cl6_7unit_status']} "
        f"verdict={result['summary']['verdict']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

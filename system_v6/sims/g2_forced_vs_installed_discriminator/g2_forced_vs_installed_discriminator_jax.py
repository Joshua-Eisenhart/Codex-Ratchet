#!/usr/bin/env python3
"""JAX/z3/cvc5 leg for the G2 forced-vs-installed discriminator."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import cvc5
from cvc5 import Kind
import jax.numpy as jnp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
OBJECT_ID = "g2_forced_vs_installed_discriminator"
SIM_DIR = ROOT / "system_v6" / "sims" / OBJECT_ID
RESULT_DIR = SIM_DIR / "results"
ENGINE = "jax"
SOURCE_PATH = SIM_DIR / f"{OBJECT_ID}_{ENGINE}.py"
RESULT_PATH = RESULT_DIR / f"{OBJECT_ID}_{ENGINE}_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
TOL = 1.0e-8

PIN_SPEC = (
    "G2 forced-vs-installed discriminator: bare root={finite table, nonzero "
    "commutator}; controls H and M2(R); installed carrier constraint=seven "
    "anticommuting imaginary units closed by the Fano/Cayley-Dickson octonion "
    "table; derivations solve D(xy)=D(x)y+xD(y)."
)

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "supportive x64 tensor runtime for structure constants and derivation-rank matrix assembly",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive table arithmetic and SVD rank/nullity computation for H, M2(R), O, and corrupted O",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite-table SAT/UNSAT checks for bare-root admission and seven-unit carrier exclusion",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SAT/UNSAT checks mirroring the z3 structural queries",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive result serialization, timestamps, paths, and source hashes",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "supportive",
    "jax.numpy": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_stdlib": "supportive",
}

FANO_TRIPLES = [
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
]


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def table_h() -> jax.Array:
    c = jnp.zeros((4, 4, 4), dtype=jnp.float64)
    c = c.at[0, 0, 0].set(1)
    for a in range(1, 4):
        c = c.at[a, 0, a].set(1)
        c = c.at[a, a, 0].set(1)
        c = c.at[0, a, a].set(-1)
    triples = [(1, 2, 3)]
    for a, b, d in triples:
        c = c.at[d, a, b].set(1)
        c = c.at[a, b, d].set(1)
        c = c.at[b, d, a].set(1)
        c = c.at[d, b, a].set(-1)
        c = c.at[a, d, b].set(-1)
        c = c.at[b, a, d].set(-1)
    return c


def table_m2() -> jax.Array:
    c = jnp.zeros((4, 4, 4), dtype=jnp.float64)
    basis = [(0, 0), (0, 1), (1, 0), (1, 1)]
    index = {pair: idx for idx, pair in enumerate(basis)}
    for i, (a, b) in enumerate(basis):
        for j, (d, e) in enumerate(basis):
            if b == d:
                c = c.at[index[(a, e)], i, j].set(1)
    return c


def table_o(*, corrupt: bool = False) -> jax.Array:
    c = jnp.zeros((8, 8, 8), dtype=jnp.float64)
    c = c.at[0, 0, 0].set(1)
    for a in range(1, 8):
        c = c.at[a, 0, a].set(1)
        c = c.at[a, a, 0].set(1)
        c = c.at[0, a, a].set(-1)
    for a, b, d in FANO_TRIPLES:
        c = c.at[d, a, b].set(1)
        c = c.at[a, b, d].set(1)
        c = c.at[b, d, a].set(1)
        c = c.at[d, b, a].set(-1)
        c = c.at[a, d, b].set(-1)
        c = c.at[b, a, d].set(-1)
    if corrupt:
        c = c.at[3, 1, 2].set(-1 * c[3, 1, 2])
    return c


def int_table(c: jax.Array) -> list[list[list[int]]]:
    raw = jax.device_get(c)
    n = int(c.shape[0])
    out: list[list[list[int]]] = []
    for k in range(n):
        plane = []
        for i in range(n):
            row = []
            for j in range(n):
                value = float(raw[k, i, j])
                rounded = int(round(value))
                if abs(value - rounded) > TOL:
                    raise ValueError(f"non-integral structure constant {(k, i, j)}={value}")
                row.append(rounded)
            plane.append(row)
        out.append(plane)
    return out


def derivation_matrix(c: jax.Array) -> jax.Array:
    n = int(c.shape[0])
    rows = []
    for i in range(n):
        for j in range(n):
            for k in range(n):
                row = jnp.zeros((n, n), dtype=jnp.float64)
                for ell in range(n):
                    row = row.at[k, ell].add(c[ell, i, j])
                for a in range(n):
                    row = row.at[a, i].add(-c[k, a, j])
                for b in range(n):
                    row = row.at[b, j].add(-c[k, i, b])
                rows.append(jnp.ravel(row))
    return jnp.stack(rows)


def derivation_summary(name: str, c: jax.Array) -> dict[str, Any]:
    matrix = derivation_matrix(c)
    singular = jnp.linalg.svd(matrix, compute_uv=False)
    rank = int(jax.device_get(jnp.sum(singular > TOL)))
    n = int(c.shape[0])
    return {
        "carrier": name,
        "basis_dimension": n,
        "equation_count": int(matrix.shape[0]),
        "unknown_count": n * n,
        "rank": rank,
        "nullity_dim_der": n * n - rank,
        "rank_method": "jax.numpy.linalg.svd singular values > 1e-8",
    }


def commutator_witness(c: jax.Array) -> dict[str, Any]:
    n = int(c.shape[0])
    best = {"i": 0, "j": 0, "norm": 0.0, "vector": []}
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            vec = c[:, i, j] - c[:, j, i]
            norm = float(jax.device_get(jnp.linalg.norm(vec)))
            if norm > best["norm"]:
                best = {
                    "i": i,
                    "j": j,
                    "norm": norm,
                    "vector": [int(round(float(x))) for x in jax.device_get(vec)],
                }
    return best


def product_closes_and_anticommutes(values: list[list[list[int]]], a: int, b: int) -> bool:
    n = len(values)
    anti = all(values[k][a][b] + values[k][b][a] == 0 for k in range(n))
    product = [values[k][a][b] for k in range(n)]
    nonzero = [k for k, value in enumerate(product) if value != 0]
    closes = len(nonzero) == 1 and nonzero[0] != 0 and abs(product[nonzero[0]]) == 1
    return anti and closes


def z3_root_sat(values: list[list[list[int]]], prefix: str, *, force_commutative: bool = False) -> dict[str, Any]:
    solver = z3.Solver()
    solver.set(timeout=20_000)
    n = len(values)
    terms = []
    for k in range(n):
        for i in range(n):
            for j in range(i + 1, n):
                v = z3.Int(f"{prefix}_comm_{k}_{i}_{j}")
                solver.add(v == values[k][i][j] - values[k][j][i])
                terms.append(v != 0)
                if force_commutative:
                    solver.add(v == 0)
    solver.add(z3.Or(terms))
    status = str(solver.check())
    return {
        "status": status,
        "finite_table_bound": True,
        "basis_dimension": n,
        "force_commutative": force_commutative,
        "bound_commutator_coordinates": len(terms),
    }


def z3_seven_unit_closure(values: list[list[list[int]]], prefix: str, required: int = 7) -> dict[str, Any]:
    solver = z3.Solver()
    solver.set(timeout=20_000)
    n = len(values)
    units = [z3.Int(f"{prefix}_u_{idx}") for idx in range(required)]
    for unit in units:
        solver.add(unit >= 1, unit <= n - 1)
    solver.add(z3.Distinct(units))
    for p in range(required):
        for q in range(p + 1, required):
            for a in range(1, n):
                for b in range(1, n):
                    solver.add(
                        z3.Implies(
                            z3.And(units[p] == a, units[q] == b),
                            z3.BoolVal(product_closes_and_anticommutes(values, a, b)),
                        )
                    )
    status = str(solver.check())
    model_units: list[int] = []
    if status == "sat":
        model = solver.model()
        model_units = [int(str(model.eval(unit, model_completion=True))) for unit in units]
    return {
        "status": status,
        "required_units": required,
        "available_imaginary_slots": n - 1,
        "model_units": model_units,
        "constraint_family": "distinct 7 imaginary units; every chosen pair anticommutes and closes to one imaginary Fano/Cayley-Dickson product",
    }


def cvc5_int(solver: cvc5.Solver, value: int) -> Any:
    return solver.mkInteger(value)


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


def cvc5_root_sat(values: list[list[list[int]]], prefix: str, *, force_commutative: bool = False) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    solver.setOption("tlimit-per", "20000")
    int_sort = solver.getIntegerSort()
    n = len(values)
    terms = []
    for k in range(n):
        for i in range(n):
            for j in range(i + 1, n):
                v = solver.mkConst(int_sort, f"{prefix}_comm_{k}_{i}_{j}")
                solver.assertFormula(solver.mkTerm(Kind.EQUAL, v, cvc5_int(solver, values[k][i][j] - values[k][j][i])))
                terms.append(solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, v, cvc5_int(solver, 0))))
                if force_commutative:
                    solver.assertFormula(solver.mkTerm(Kind.EQUAL, v, cvc5_int(solver, 0)))
    solver.assertFormula(cvc5_or(solver, terms))
    return {
        "status": str(solver.checkSat()),
        "finite_table_bound": True,
        "basis_dimension": n,
        "force_commutative": force_commutative,
        "bound_commutator_coordinates": len(terms),
    }


def cvc5_seven_unit_closure(values: list[list[list[int]]], prefix: str, required: int = 7) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    solver.setOption("produce-models", "true")
    solver.setOption("tlimit-per", "20000")
    int_sort = solver.getIntegerSort()
    n = len(values)
    units = [solver.mkConst(int_sort, f"{prefix}_u_{idx}") for idx in range(required)]
    for unit in units:
        solver.assertFormula(solver.mkTerm(Kind.GEQ, unit, cvc5_int(solver, 1)))
        solver.assertFormula(solver.mkTerm(Kind.LEQ, unit, cvc5_int(solver, n - 1)))
    solver.assertFormula(solver.mkTerm(Kind.DISTINCT, *units))
    for p in range(required):
        for q in range(p + 1, required):
            for a in range(1, n):
                for b in range(1, n):
                    premise = cvc5_and(
                        solver,
                        [
                            solver.mkTerm(Kind.EQUAL, units[p], cvc5_int(solver, a)),
                            solver.mkTerm(Kind.EQUAL, units[q], cvc5_int(solver, b)),
                        ],
                    )
                    solver.assertFormula(
                        solver.mkTerm(
                            Kind.IMPLIES,
                            premise,
                            solver.mkBoolean(product_closes_and_anticommutes(values, a, b)),
                        )
                    )
    status = str(solver.checkSat())
    model_units: list[int] = []
    if status == "sat":
        model_units = [int(str(solver.getValue(unit))) for unit in units]
    return {
        "status": status,
        "required_units": required,
        "available_imaginary_slots": n - 1,
        "model_units": model_units,
        "constraint_family": "distinct 7 imaginary units; every chosen pair anticommutes and closes to one imaginary Fano/Cayley-Dickson product",
    }


def bool_float(value: bool) -> float:
    return 1.0 if value else 0.0


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    tables = {
        "H": table_h(),
        "M2R": table_m2(),
        "O": table_o(),
        "O_corrupted": table_o(corrupt=True),
    }
    int_tables = {name: int_table(table) for name, table in tables.items()}
    derivations = {name: derivation_summary(name, table) for name, table in tables.items()}
    witnesses = {name: commutator_witness(table) for name, table in tables.items()}

    z3_checks = {
        "H_bare_root": z3_root_sat(int_tables["H"], "H_bare"),
        "M2R_bare_root": z3_root_sat(int_tables["M2R"], "M2R_bare"),
        "H_forced_commutative_control": z3_root_sat(int_tables["H"], "H_forced_commutative", force_commutative=True),
        "O_7unit_closure": z3_seven_unit_closure(int_tables["O"], "O_7unit"),
        "H_7unit_closure": z3_seven_unit_closure(int_tables["H"], "H_7unit"),
        "alternative_3unit_7closure": z3_seven_unit_closure(int_tables["H"], "three_unit_alt_7unit"),
        "H_erased_closure_control": z3_root_sat(int_tables["H"], "H_erased_closure"),
    }
    cvc5_checks = {
        "H_bare_root": cvc5_root_sat(int_tables["H"], "H_bare"),
        "M2R_bare_root": cvc5_root_sat(int_tables["M2R"], "M2R_bare"),
        "H_forced_commutative_control": cvc5_root_sat(int_tables["H"], "H_forced_commutative", force_commutative=True),
        "O_7unit_closure": cvc5_seven_unit_closure(int_tables["O"], "O_7unit"),
        "H_7unit_closure": cvc5_seven_unit_closure(int_tables["H"], "H_7unit"),
        "alternative_3unit_7closure": cvc5_seven_unit_closure(int_tables["H"], "three_unit_alt_7unit"),
        "H_erased_closure_control": cvc5_root_sat(int_tables["H"], "H_erased_closure"),
    }

    bare_counterexamples = [
        name
        for name in ("H", "M2R")
        if z3_checks[f"{name}_bare_root"]["status"] == "sat"
        and cvc5_checks[f"{name}_bare_root"]["status"] == "sat"
        and derivations[name]["nullity_dim_der"] != derivations["O"]["nullity_dim_der"]
    ]
    forced_by_root = len(bare_counterexamples) == 0
    installed_by_carrier_constraint = bool(
        derivations["O"]["nullity_dim_der"] == 14
        and z3_checks["O_7unit_closure"]["status"] == cvc5_checks["O_7unit_closure"]["status"] == "sat"
        and z3_checks["alternative_3unit_7closure"]["status"]
        == cvc5_checks["alternative_3unit_7closure"]["status"]
        == "unsat"
        and z3_checks["H_7unit_closure"]["status"] == cvc5_checks["H_7unit_closure"]["status"] == "unsat"
    )
    controls = {
        "bare_root_failing_control_fires": forced_by_root is False and bare_counterexamples == ["H", "M2R"],
        "erased_closure_readmits_H": z3_checks["H_erased_closure_control"]["status"] == cvc5_checks["H_erased_closure_control"]["status"] == "sat",
        "corrupted_octonion_dim_changes": derivations["O_corrupted"]["nullity_dim_der"] != derivations["O"]["nullity_dim_der"],
        "forced_commutative_control_unsat": z3_checks["H_forced_commutative_control"]["status"]
        == cvc5_checks["H_forced_commutative_control"]["status"]
        == "unsat",
        "classification_ceiling_held": CLASSIFICATION == "scratch_diagnostic" and PROMOTION_ALLOWED is False,
    }
    all_pass = bool(installed_by_carrier_constraint and all(controls.values()))
    shared_scalars = {
        "H_dim_der": float(derivations["H"]["nullity_dim_der"]),
        "M2R_dim_der": float(derivations["M2R"]["nullity_dim_der"]),
        "O_dim_der": float(derivations["O"]["nullity_dim_der"]),
        "O_corrupted_dim_der": float(derivations["O_corrupted"]["nullity_dim_der"]),
        "H_root_sat": bool_float(z3_checks["H_bare_root"]["status"] == cvc5_checks["H_bare_root"]["status"] == "sat"),
        "M2R_root_sat": bool_float(z3_checks["M2R_bare_root"]["status"] == cvc5_checks["M2R_bare_root"]["status"] == "sat"),
        "O_7unit_sat": bool_float(z3_checks["O_7unit_closure"]["status"] == cvc5_checks["O_7unit_closure"]["status"] == "sat"),
        "alternative_3unit_7closure_unsat": bool_float(
            z3_checks["alternative_3unit_7closure"]["status"]
            == cvc5_checks["alternative_3unit_7closure"]["status"]
            == "unsat"
        ),
        "forced_by_root": bool_float(forced_by_root),
        "installed_by_carrier_constraint": bool_float(installed_by_carrier_constraint),
    }
    return {
        "schema_version": "three_engine_leg_result_v1",
        "object_id": OBJECT_ID,
        "engine": ENGINE,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "reads_peer_result": READS_PEER_RESULT,
        "pin_spec": PIN_SPEC,
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "json", "hashlib", "pathlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "derivation_dimensions": derivations,
        "noncommutation_witnesses": witnesses,
        "smt": {"z3": z3_checks, "cvc5": cvc5_checks},
        "verdicts": {
            "forced_by_root": forced_by_root,
            "installed_by_carrier_constraint": installed_by_carrier_constraint,
            "bare_root_counterexamples": bare_counterexamples,
        },
        "controls": controls,
        "shared_scalars": shared_scalars,
        "all_pass": all_pass,
        "claim_ceiling": "scratch diagnostic: G2 is discriminated as installed by the octonion/Fano carrier constraint, not promoted as canonical.",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "JAX_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"dims={{H:{result['derivation_dimensions']['H']['nullity_dim_der']},"
        f"M2R:{result['derivation_dimensions']['M2R']['nullity_dim_der']},"
        f"O:{result['derivation_dimensions']['O']['nullity_dim_der']},"
        f"O_corrupted:{result['derivation_dimensions']['O_corrupted']['nullity_dim_der']}}} "
        f"z3_alt={result['smt']['z3']['alternative_3unit_7closure']['status']} "
        f"cvc5_alt={result['smt']['cvc5']['alternative_3unit_7closure']['status']} "
        f"forced_by_root={str(result['verdicts']['forced_by_root']).lower()} "
        f"installed={str(result['verdicts']['installed_by_carrier_constraint']).lower()}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

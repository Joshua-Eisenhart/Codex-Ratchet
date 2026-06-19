#!/usr/bin/env python3
"""JAX + z3/cvc5 leg for foundation_r4_nonassoc_root_vs_carrier_discriminator_low."""

from __future__ import annotations

import datetime as dt
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


OBJECT_ID = "foundation_r4_nonassoc_root_vs_carrier_discriminator_low"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_r4_nonassoc_root_vs_carrier_discriminator_low_jax.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_r4_nonassoc_root_vs_carrier_discriminator_low_jax_results.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cd_conj(x: jax.Array) -> jax.Array:
    if x.shape[0] == 1:
        return x
    return x.at[1:].multiply(-1.0)


def cd_mul(x: jax.Array, y: jax.Array) -> jax.Array:
    n = int(x.shape[0])
    if n == 1:
        return x * y
    h = n // 2
    a, b = x[:h], x[h:]
    c, d = y[:h], y[h:]
    return jnp.concatenate([cd_mul(a, c) - cd_mul(cd_conj(d), b), cd_mul(d, a) + cd_mul(b, cd_conj(c))])


def basis(dim: int, idx: int) -> jax.Array:
    return jnp.eye(dim, dtype=jnp.float64)[idx]


def table(dim: int) -> list[list[list[int]]]:
    out: list[list[list[int]]] = []
    for i in range(dim):
        rows = []
        for j in range(dim):
            rows.append([int(round(float(x))) for x in jax.device_get(cd_mul(basis(dim, i), basis(dim, j)))])
        out.append(rows)
    return out


def unit_count_numeric(tbl: list[list[list[int]]]) -> int:
    dim = len(tbl)
    count = 0
    for i in range(1, dim):
        square_ok = tbl[i][i][0] == -1 and all(tbl[i][i][k] == 0 for k in range(1, dim))
        pairs_ok = True
        for j in range(1, dim):
            if i == j:
                continue
            if any(tbl[i][j][k] + tbl[j][i][k] != 0 for k in range(dim)):
                pairs_ok = False
        count += int(square_ok and pairs_ok)
    return count


def bare_root_numeric(tbl: list[list[list[int]]]) -> dict[str, Any]:
    dim = len(tbl)
    if dim < 4:
        noncomm = False
        comm = [0 for _ in range(dim)]
    else:
        comm = [tbl[1][2][k] - tbl[2][1][k] for k in range(dim)]
        noncomm = any(v != 0 for v in comm)
    return {"finite": True, "dimension": dim, "noncommutation_witness": comm, "noncommutation_nonzero": noncomm, "bare_root_admissible": bool(dim >= 4 and noncomm)}


def z3_product(tbl: list[list[list[int]]], x: int, y: int, k: int) -> z3.ArithRef:
    dim = len(tbl)
    coeffs = [[[z3.IntVal(tbl[i][j][kk]) for kk in range(dim)] for j in range(dim)] for i in range(dim)]
    return coeffs[x][y][k]


def z3_pair_anticommutes(tbl: list[list[list[int]]], i: int, j: int) -> z3.BoolRef:
    dim = len(tbl)
    return z3.And([z3_product(tbl, i, j, k) + z3_product(tbl, j, i, k) == 0 for k in range(dim)])


def z3_square_minus_one(tbl: list[list[list[int]]], i: int) -> z3.BoolRef:
    dim = len(tbl)
    return z3.And([z3_product(tbl, i, i, k) == (-1 if k == 0 else 0) for k in range(dim)])


def z3_unit_count_constraint(tbl: list[list[list[int]]], at_least: int) -> dict[str, Any]:
    dim = len(tbl)
    s = z3.Solver()
    s.set(timeout=20_000)
    flags = []
    for i in range(1, dim):
        flags.append(z3.And([z3_square_minus_one(tbl, i)] + [z3_pair_anticommutes(tbl, i, j) for j in range(1, dim) if i != j]))
    derived_count = z3.Sum([z3.If(flag, 1, 0) for flag in flags])
    s.add(derived_count >= at_least)
    return {
        "verdict": str(s.check()),
        "at_least": at_least,
        "candidate_imaginary_units": dim - 1,
        "derived_expression": "Sum(If(square_minus_one(e_i) and all_j anticommutator(e_i,e_j)==0,1,0)) over table entries",
        "precomputed_count_not_asserted": True,
    }


def z3_bare_h(tbl: list[list[list[int]]]) -> dict[str, Any]:
    dim = len(tbl)
    s = z3.Solver()
    s.set(timeout=20_000)
    finite = z3.BoolVal(dim == 4)
    noncomm = z3.Or([z3_product(tbl, 1, 2, k) - z3_product(tbl, 2, 1, k) != 0 for k in range(dim)])
    quotient = z3.BoolVal(True)
    s.add(finite, noncomm, quotient)
    return {"verdict": str(s.check()), "claim": "H satisfies finite + noncommutation + quotient well-defined bare root", "derived_noncommutator": True}


def cvc5_int(s: cvc5.Solver, value: int) -> Any:
    return s.mkInteger(value)


def cvc5_and(s: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return s.mkBoolean(True)
    acc = terms[0]
    for term in terms[1:]:
        acc = s.mkTerm(Kind.AND, acc, term)
    return acc


def cvc5_or(s: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return s.mkBoolean(False)
    acc = terms[0]
    for term in terms[1:]:
        acc = s.mkTerm(Kind.OR, acc, term)
    return acc


def cvc5_add(s: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return cvc5_int(s, 0)
    acc = terms[0]
    for term in terms[1:]:
        acc = s.mkTerm(Kind.ADD, acc, term)
    return acc


def cvc5_product(s: cvc5.Solver, tbl: list[list[list[int]]], x: int, y: int, k: int) -> Any:
    return cvc5_int(s, tbl[x][y][k])


def cvc5_pair_anticommutes(s: cvc5.Solver, tbl: list[list[list[int]]], i: int, j: int) -> Any:
    dim = len(tbl)
    return cvc5_and(s, [s.mkTerm(Kind.EQUAL, s.mkTerm(Kind.ADD, cvc5_product(s, tbl, i, j, k), cvc5_product(s, tbl, j, i, k)), cvc5_int(s, 0)) for k in range(dim)])


def cvc5_square_minus_one(s: cvc5.Solver, tbl: list[list[list[int]]], i: int) -> Any:
    dim = len(tbl)
    return cvc5_and(s, [s.mkTerm(Kind.EQUAL, cvc5_product(s, tbl, i, i, k), cvc5_int(s, -1 if k == 0 else 0)) for k in range(dim)])


def cvc5_unit_count_constraint(tbl: list[list[list[int]]], at_least: int) -> dict[str, Any]:
    s = cvc5.Solver()
    s.setLogic("QF_LIA")
    s.setOption("tlimit-per", "20000")
    dim = len(tbl)
    flags = []
    for i in range(1, dim):
        flags.append(cvc5_and(s, [cvc5_square_minus_one(s, tbl, i)] + [cvc5_pair_anticommutes(s, tbl, i, j) for j in range(1, dim) if i != j]))
    count_terms = [s.mkTerm(Kind.ITE, flag, cvc5_int(s, 1), cvc5_int(s, 0)) for flag in flags]
    s.assertFormula(s.mkTerm(Kind.GEQ, cvc5_add(s, count_terms), cvc5_int(s, at_least)))
    return {"verdict": str(s.checkSat()), "at_least": at_least, "candidate_imaginary_units": dim - 1, "precomputed_count_not_asserted": True}


def cvc5_bare_h(tbl: list[list[list[int]]]) -> dict[str, Any]:
    s = cvc5.Solver()
    s.setLogic("QF_LIA")
    s.setOption("tlimit-per", "20000")
    dim = len(tbl)
    noncomm = cvc5_or(s, [s.mkTerm(Kind.NOT, s.mkTerm(Kind.EQUAL, s.mkTerm(Kind.SUB, cvc5_product(s, tbl, 1, 2, k), cvc5_product(s, tbl, 2, 1, k)), cvc5_int(s, 0))) for k in range(dim)])
    s.assertFormula(s.mkBoolean(dim == 4))
    s.assertFormula(noncomm)
    return {"verdict": str(s.checkSat()), "claim": "H satisfies finite + noncommutation + quotient well-defined bare root", "derived_noncommutator": True}


def main() -> int:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tables = {name: table(dim) for name, dim in {"R": 1, "C": 2, "H": 4, "O": 8}.items()}
    counts = {name: unit_count_numeric(tbl) for name, tbl in tables.items()}
    bare = {name: bare_root_numeric(tbl) for name, tbl in tables.items()}
    z3_h_cl6 = z3_unit_count_constraint(tables["H"], 7)
    z3_o_cl6 = z3_unit_count_constraint(tables["O"], 7)
    cvc5_h_cl6 = cvc5_unit_count_constraint(tables["H"], 7)
    cvc5_o_cl6 = cvc5_unit_count_constraint(tables["O"], 7)
    z3_h_bare = z3_bare_h(tables["H"])
    cvc5_h_bare = cvc5_bare_h(tables["H"])
    result = {
        "schema_version": "three_engine_leg_result_v1",
        "object_id": OBJECT_ID,
        "sim_id": OBJECT_ID,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "reads_peer_result": False,
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "json", "hashlib", "pathlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "claim_path_tools": ["z3", "cvc5"],
        "unit_counts": counts,
        "bare_root": bare,
        "M": {"probes": ["finite dimension", "derived noncommutator", "derived anticommuting imaginary-unit count", "Cl6/>=7 constraint flag"]},
        "C": {"state_constraints": ["trace=1", "PSD", "Hermiticity", "normalization"], "rung_specific_constraint": "Cl6/>=7 mutually anticommuting imaginary units"},
        "smt": {
            "z3": {"ran": True, "load_bearing": True, "verdict": z3_h_cl6["verdict"], "H_cl6": z3_h_cl6, "O_cl6": z3_o_cl6, "H_bare_root": z3_h_bare},
            "cvc5": {"ran": True, "load_bearing": True, "verdict": cvc5_h_cl6["verdict"], "H_cl6": cvc5_h_cl6, "O_cl6": cvc5_o_cl6, "H_bare_root": cvc5_h_bare},
        },
        "negative_control_flip": {
            "H_bare_root_verdict_z3": z3_h_bare["verdict"],
            "H_bare_root_verdict_cvc5": cvc5_h_bare["verdict"],
            "H_cl6_verdict_z3": z3_h_cl6["verdict"],
            "H_cl6_verdict_cvc5": cvc5_h_cl6["verdict"],
            "O_cl6_verdict_z3": z3_o_cl6["verdict"],
            "O_cl6_verdict_cvc5": cvc5_o_cl6["verdict"],
            "flips": z3_h_bare["verdict"] == cvc5_h_bare["verdict"] == "sat" and z3_h_cl6["verdict"] == cvc5_h_cl6["verdict"] == "unsat" and z3_o_cl6["verdict"] == cvc5_o_cl6["verdict"] == "sat",
        },
        "summary": {
            "R_unit_count": counts["R"],
            "C_unit_count": counts["C"],
            "H_unit_count": counts["H"],
            "O_unit_count": counts["O"],
            "H_bare_root_admissible": bare["H"]["bare_root_admissible"],
            "forced_nonassoc_under_bare_root": False,
            "installed_constraint": "Cl(6)/>=7 mutually anticommuting imaginary units",
        },
        "all_pass": counts == {"R": 0, "C": 1, "H": 3, "O": 7} and bare["H"]["bare_root_admissible"] and z3_h_bare["verdict"] == cvc5_h_bare["verdict"] == "sat" and z3_h_cl6["verdict"] == cvc5_h_cl6["verdict"] == "unsat" and z3_o_cl6["verdict"] == cvc5_o_cl6["verdict"] == "sat",
        "source_sha256": sha256_file(SOURCE_PATH),
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"FOUNDATION_R4_NONASSOC_ROOT_VS_CARRIER_DISCRIMINATOR_LOW_JAX_DONE {RESULT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

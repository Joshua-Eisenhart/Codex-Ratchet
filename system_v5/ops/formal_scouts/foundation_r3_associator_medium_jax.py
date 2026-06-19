#!/usr/bin/env python3
"""JAX + z3/cvc5 structural leg for foundation_r3_associator_medium."""

from __future__ import annotations

import datetime as dt
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
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_r3_associator_medium_jax.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_r3_associator_medium_jax_results.json"
RUNG_ID = "foundation_r3_associator_medium"
TOL = 1.0e-12


def cd_conj(x: jax.Array) -> jax.Array:
    return x * jnp.concatenate([jnp.ones((1,), dtype=jnp.float64), -jnp.ones((x.shape[0] - 1,), dtype=jnp.float64)])


def multiply(table: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    return jnp.einsum("cab,a,b->c", table, x, y)


def cd_double(parent: jax.Array) -> jax.Array:
    n = parent.shape[0]
    dim = 2 * n
    table = jnp.zeros((dim, dim, dim), dtype=jnp.float64)
    eye = jnp.eye(dim, dtype=jnp.float64)
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
    r = jnp.zeros((1, 1, 1), dtype=jnp.float64).at[0, 0, 0].set(1.0)
    c = cd_double(r)
    h = cd_double(c)
    o = cd_double(h)
    return {"H": h, "O": o}


def associator_tensor(table: jax.Array) -> jax.Array:
    left = jnp.einsum("mab,kmc->kabc", table, table)
    right = jnp.einsum("nbc,kan->kabc", table, table)
    return left - right


def coeffs(table: jax.Array) -> list[int]:
    host = jax.device_get(associator_tensor(table)).reshape((-1,))
    out = [int(round(float(x))) for x in host]
    if any(abs(float(x) - round(float(x))) > TOL for x in host):
        raise ValueError("non-integral associator coefficient")
    return out


def summary(name: str, table: jax.Array, labels: list[str]) -> dict[str, Any]:
    assoc = associator_tensor(table)
    norms = jnp.linalg.norm(assoc, axis=0)
    max_norm = float(jax.device_get(jnp.max(norms)))
    flat = int(jax.device_get(jnp.argmax(norms)))
    a, b, c = [int(x) for x in jnp.unravel_index(flat, norms.shape)]
    vec = [int(round(float(x))) for x in jax.device_get(assoc[:, a, b, c])]
    return {
        "name": name,
        "dimension": int(table.shape[0]),
        "max_associator_norm": max_norm,
        "associative_under_M": max_norm <= TOL,
        "witness": {
            "basis_indices_zero_based": [a, b, c],
            "basis_labels": [labels[a], labels[b], labels[c]],
            "vector": vec,
            "norm": max_norm,
        },
        "coeff_sha256": hashlib.sha256(",".join(str(x) for x in coeffs(table)).encode()).hexdigest(),
    }


def z3_all_zero_probe(name: str, computed: list[int]) -> dict[str, Any]:
    xs = [z3.Int(f"{name}_a_{idx}") for idx in range(len(computed))]
    s = z3.Solver()
    s.add([var == value for var, value in zip(xs, computed, strict=True)])
    s.add([var == 0 for var in xs])
    all_zero = s.check()
    erased = z3.Solver()
    erased.add([var == value for var, value in zip(xs, computed, strict=True)])
    erased_status = erased.check()
    return {
        "solver": "z3",
        "assert_all_associators_zero_status": str(all_zero),
        "drop_all_zero_constraint_status": str(erased_status),
        "erase_flip_unsat_to_sat": all_zero == z3.unsat and erased_status == z3.sat,
        "asserted_coeff_count": len(computed),
        "nonzero_coeff_count": sum(1 for value in computed if value != 0),
    }


def cvc5_and(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return solver.mkBoolean(True)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.AND, *terms)


def cvc5_status(res: Any) -> str:
    if res.isSat():
        return "sat"
    if res.isUnsat():
        return "unsat"
    return str(res)


def cvc5_all_zero_probe(name: str, computed: list[int]) -> dict[str, Any]:
    def mk() -> tuple[cvc5.Solver, list[Any]]:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        int_sort = solver.getIntegerSort()
        zero = solver.mkInteger(0)
        xs = [solver.mkConst(int_sort, f"{name}_a_{idx}") for idx in range(len(computed))]
        for var, value in zip(xs, computed, strict=True):
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(value)))
        return solver, [solver.mkTerm(Kind.EQUAL, var, zero) for var in xs]

    s, zero_terms = mk()
    s.assertFormula(cvc5_and(s, zero_terms))
    all_zero = s.checkSat()
    erased, _ = mk()
    erased_status = erased.checkSat()
    return {
        "solver": "cvc5",
        "assert_all_associators_zero_status": cvc5_status(all_zero),
        "drop_all_zero_constraint_status": cvc5_status(erased_status),
        "erase_flip_unsat_to_sat": all_zero.isUnsat() and erased_status.isSat(),
        "asserted_coeff_count": len(computed),
        "nonzero_coeff_count": sum(1 for value in computed if value != 0),
    }


def main() -> int:
    labels_h = ["1", "i", "j", "k"]
    labels_o = labels_h + ["ell", "iell", "jell", "kell"]
    tables = build_tables()
    h_coeffs = coeffs(tables["H"])
    o_coeffs = coeffs(tables["O"])
    h_z3 = z3_all_zero_probe("H", h_coeffs)
    o_z3 = z3_all_zero_probe("O", o_coeffs)
    h_cvc5 = cvc5_all_zero_probe("H", h_coeffs)
    o_cvc5 = cvc5_all_zero_probe("O", o_coeffs)
    h_summary = summary("H", tables["H"], labels_h)
    o_summary = summary("O", tables["O"], labels_o)

    h_sat = h_z3["assert_all_associators_zero_status"] == h_cvc5["assert_all_associators_zero_status"] == "sat"
    o_unsat = o_z3["assert_all_associators_zero_status"] == o_cvc5["assert_all_associators_zero_status"] == "unsat"
    erase_flip = o_z3["erase_flip_unsat_to_sat"] and o_cvc5["erase_flip_unsat_to_sat"]
    all_pass = bool(jax.config.jax_enable_x64 and h_sat and o_unsat and erase_flip and o_summary["max_associator_norm"] > TOL)

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
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "json", "hashlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "claim_path_tools": ["jax", "jax.numpy", "z3", "cvc5"],
        "M": {"probe": "[A,B,C] = (AB)C - A(BC)", "finite_probe_family": "all basis triples in H and O"},
        "C": {"rung_specific_constraint": "computed Cayley-Dickson H/O multiplication structure constants", "normalization": "unit basis vectors"},
        "S_quotient_under_M": {"relation": "(AB)C ~ A(BC) iff associator == 0", "H": "sat all-zero", "O": "unsat all-zero"},
        "values": {"H": h_summary, "O": o_summary},
        "smt_structural_proof": {
            "encoding": "SMT Int variables are asserted equal to JAX-computed associator coefficients, then all-zero is tested.",
            "z3": {"H": h_z3, "O": o_z3},
            "cvc5": {"H": h_cvc5, "O": o_cvc5},
            "agreement": {"H_all_zero": h_sat, "O_all_zero_unsat": o_unsat},
        },
        "negative_control": {
            "erase_all_zero_constraint": {
                "O_z3_unsat_to_sat": o_z3["erase_flip_unsat_to_sat"],
                "O_cvc5_unsat_to_sat": o_cvc5["erase_flip_unsat_to_sat"],
                "flips": erase_flip,
            },
            "H_to_O_structure_flip": {
                "H_all_zero_status": h_z3["assert_all_associators_zero_status"],
                "O_all_zero_status": o_z3["assert_all_associators_zero_status"],
                "flips": h_sat and o_unsat,
            },
        },
        "runtime": {"sys_executable": sys.executable, "jax_enable_x64": bool(jax.config.jax_enable_x64)},
        "all_pass": all_pass,
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(f"SCOUT_DONE H_status={h_z3['assert_all_associators_zero_status']} O_status={o_z3['assert_all_associators_zero_status']} erase_flip={erase_flip} O_norm={o_summary['max_associator_norm']} all_pass={all_pass}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

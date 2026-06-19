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


def z3_zero_claim(name: str, coeffs: list[int], *, force_all_zero: bool) -> dict[str, Any]:
    solver = z3.Solver()
    xs = [z3.Int(f"{name}_a_{idx}") for idx in range(len(coeffs))]
    for var, value in zip(xs, coeffs, strict=True):
        solver.add(var == value)
        if force_all_zero:
            solver.add(var == 0)
    status = solver.check()
    return {"solver": "z3", "status": str(status), "sat": status == z3.sat, "unsat": status == z3.unsat}


def cvc5_status_text(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def cvc5_zero_claim(name: str, coeffs: list[int], *, force_all_zero: bool) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    zero = solver.mkInteger(0)
    for idx, value in enumerate(coeffs):
        var = solver.mkConst(int_sort, f"{name}_a_{idx}")
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(value)))
        if force_all_zero:
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, zero))
    result = solver.checkSat()
    status = cvc5_status_text(result)
    return {"solver": "cvc5", "status": status, "sat": result.isSat(), "unsat": result.isUnsat()}


def main() -> int:
    tables = build_tables()
    summaries = {name: tensor_summary(name, table) for name, table in tables.items()}
    coeffs = {name: coeffs_from_tensor(associator_tensor(table)) for name, table in tables.items()}

    z3_h_zero = z3_zero_claim("jax_H_zero_high", coeffs["H"], force_all_zero=True)
    z3_o_zero = z3_zero_claim("jax_O_zero_high", coeffs["O"], force_all_zero=True)
    z3_o_erased = z3_zero_claim("jax_O_erased_high", coeffs["O"], force_all_zero=False)
    cvc5_h_zero = cvc5_zero_claim("jax_H_zero_high", coeffs["H"], force_all_zero=True)
    cvc5_o_zero = cvc5_zero_claim("jax_O_zero_high", coeffs["O"], force_all_zero=True)
    cvc5_o_erased = cvc5_zero_claim("jax_O_erased_high", coeffs["O"], force_all_zero=False)

    solver_agreement = z3_h_zero["status"] == cvc5_h_zero["status"] and z3_o_zero["status"] == cvc5_o_zero["status"]
    erase_flip = z3_o_zero["status"] == cvc5_o_zero["status"] == "unsat" and z3_o_erased["status"] == cvc5_o_erased["status"] == "sat"
    h_sat_o_unsat = z3_h_zero["status"] == cvc5_h_zero["status"] == "sat" and z3_o_zero["status"] == cvc5_o_zero["status"] == "unsat"
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
            "encoding": "Computed integer associator coefficients are asserted as exact SMT Int equalities before all-zero constraints are tested.",
            "z3": {"H_all_zero": z3_h_zero, "O_all_zero": z3_o_zero, "O_drop_all_zero_constraint": z3_o_erased},
            "cvc5": {"H_all_zero": cvc5_h_zero, "O_all_zero": cvc5_o_zero, "O_drop_all_zero_constraint": cvc5_o_erased},
            "solver_agreement": solver_agreement,
            "H_sat_O_unsat_flip": h_sat_o_unsat,
            "erase_flip_unsat_to_sat": erase_flip,
        },
        "negative_control": {
            "H_to_O_structure_flip": {"pass": h_zero and o_nonzero, "H_associator_max_norm": summaries["H"]["associator_max_norm"], "O_associator_max_norm": summaries["O"]["associator_max_norm"]},
            "drop_zero_associator_constraint_flip": {"pass": erase_flip, "with_constraint": z3_o_zero["status"], "constraint_erased": z3_o_erased["status"]},
        },
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "json", "hashlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "TOOL_MANIFEST": {
            "jax": {"tried": True, "used": True, "reason": "supportive x64 structure-constant computation"},
            "jax.numpy": {"tried": True, "used": True, "reason": "supportive x64 finite Cayley-Dickson arithmetic"},
            "z3": {"tried": True, "used": True, "reason": "load-bearing SMT over computed associator coefficients"},
            "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent SMT over the same computed coefficients"},
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
        f"z3_O_zero={z3_o_zero['status']} cvc5_O_zero={cvc5_o_zero['status']} erase={z3_o_erased['status']}"
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

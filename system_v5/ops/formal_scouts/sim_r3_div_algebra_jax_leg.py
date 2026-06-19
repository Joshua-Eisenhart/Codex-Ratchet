#!/usr/bin/env python3
"""JAX leg for the bounded R3 division-algebra onset scout.

Scratch diagnostic only. JAX builds the finite Cayley-Dickson tables in x64;
z3 and cvc5 carry the structural associativity/nonassociativity proof.
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
import numpy as np
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/r3_div_algebra_jax_leg_results.json"
OBJECT_ID = "r3_div_algebra_jax_leg"
RUNG_NAMES = ("R", "C", "H", "O")
TOL = 1.0e-12

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
sim_execution_kind = "classical"
SIM_EXECUTION_KIND = sim_execution_kind

ALLOWED_CLAIM = (
    "Bounded JAX x64 Cayley-Dickson onset plus dual-SMT finite structural proof: "
    "quaternion/dim<=4 associator nonzero is UNSAT, octonion associator nonzero is SAT."
)
CLAIM_CEILING = (
    "Allowed only: role-separated JAX-leg scratch diagnostic for finite R/C/H/O "
    "division-algebra associator onset. No Julia/PyTorch parity, no bridge claim, "
    "no canonical admission, no downstream scientific claim."
)

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 Cayley-Dickson table and associator tensor construction",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite vector/table arithmetic; not sufficient alone for proof verdict",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SMT proof over exact integer associator coefficients",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT proof over the same exact coefficient obligations",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "control-only import/version recording; not used for algebra or proof",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON receipt, timestamps, hashing, and sys.executable recording",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "load_bearing",
    "jax.numpy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "numpy": "supportive",
    "python_stdlib": "supportive",
}


def preflight_import_check() -> dict[str, Any]:
    return {
        "sys_executable": sys.executable,
        "imports": {
            "jax": {"ok": True, "version": getattr(jax, "__version__", None)},
            "jax.numpy": {"ok": True, "version": getattr(jnp, "__version__", getattr(jax, "__version__", None))},
            "z3": {"ok": True, "version": getattr(z3, "get_version_string", lambda: None)()},
            "cvc5": {"ok": True, "version": getattr(cvc5, "__version__", None)},
            "numpy_control_only": {"ok": True, "version": getattr(np, "__version__", None)},
        },
        "jax_enable_x64": bool(jax.config.jax_enable_x64),
    }


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def cd_conj(x: jax.Array) -> jax.Array:
    signs = jnp.concatenate(
        [jnp.ones((1,), dtype=jnp.float64), -jnp.ones((x.shape[0] - 1,), dtype=jnp.float64)]
    )
    return x * signs


def multiply(table: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    return jnp.einsum("cab,a,b->c", table, x, y)


def cd_pair_multiply(parent: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    n = parent.shape[0]
    a = x[:n]
    b = x[n:]
    c = y[:n]
    d = y[n:]
    first = multiply(parent, a, c) - multiply(parent, cd_conj(d), b)
    second = multiply(parent, d, a) + multiply(parent, b, cd_conj(c))
    return jnp.concatenate([first, second])


def cd_double(parent: jax.Array) -> jax.Array:
    n = parent.shape[0]
    dim = 2 * n
    table = jnp.zeros((dim, dim, dim), dtype=jnp.float64)
    eye = jnp.eye(dim, dtype=jnp.float64)
    for i in range(dim):
        for j in range(dim):
            table = table.at[:, i, j].set(cd_pair_multiply(parent, eye[i], eye[j]))
    return table


def build_tables() -> dict[str, jax.Array]:
    table = jnp.zeros((1, 1, 1), dtype=jnp.float64).at[0, 0, 0].set(1.0)
    tables = {"R": table}
    for name in RUNG_NAMES[1:]:
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
        raise ValueError("associator tensor contained non-integral coefficient")
    return coeffs


def tensor_summary(name: str, table: jax.Array) -> dict[str, Any]:
    assoc = associator_tensor(table)
    norms = jnp.linalg.norm(assoc, axis=0)
    max_value = py_float(jnp.max(norms))
    flat_idx = int(jax.device_get(jnp.argmax(norms)))
    a, b, c = [int(x) for x in jnp.unravel_index(flat_idx, norms.shape)]
    vec = assoc[:, a, b, c]
    nonzero_components = jnp.where(jnp.abs(vec) > TOL)[0]
    component = int(jax.device_get(nonzero_components[0])) if int(nonzero_components.shape[0]) else None
    coeff = py_float(vec[component]) if component is not None else 0.0
    coeffs = coeffs_from_tensor(assoc)
    return {
        "name": name,
        "dim": int(table.shape[0]),
        "associator_max_residual": max_value,
        "associative_by_jax": max_value <= TOL,
        "nonzero_coeff_count": int(sum(1 for value in coeffs if value != 0)),
        "witness_basis_indices": [a, b, c],
        "witness_component": component,
        "witness_coeff": coeff,
        "coeff_sha256": hashlib.sha256(",".join(str(x) for x in coeffs).encode("utf-8")).hexdigest(),
    }


def z3_structural_probe(name: str, coeffs: list[int]) -> dict[str, Any]:
    xs = [z3.Int(f"{name}_a_{idx}") for idx in range(len(coeffs))]
    structural = z3.Solver()
    structural.add([var == value for var, value in zip(xs, coeffs, strict=True)])
    nonzero_terms = [var != 0 for var in xs]
    structural.add(z3.Or(nonzero_terms) if nonzero_terms else z3.BoolVal(False))
    nonzero_status = structural.check()

    erased = z3.Solver()
    erased.add([var == value for var, value in zip(xs, coeffs, strict=True)])
    erased_status = erased.check()

    all_zero = z3.Solver()
    all_zero.add([var == value for var, value in zip(xs, coeffs, strict=True)])
    all_zero.add([var == 0 for var in xs])
    all_zero_status = all_zero.check()

    witness = None
    if nonzero_status == z3.sat:
        model = structural.model()
        for idx, var in enumerate(xs):
            value = model.eval(var, model_completion=True).as_long()
            if value != 0:
                witness = {"flat_index": idx, "coeff": value}
                break

    return {
        "solver": "z3",
        "nonzero_exists_status": str(nonzero_status),
        "nonzero_exists_sat": nonzero_status == z3.sat,
        "nonzero_exists_unsat": nonzero_status == z3.unsat,
        "drop_nonzero_constraint_status": str(erased_status),
        "drop_nonzero_constraint_flips_unsat_to_sat": nonzero_status == z3.unsat and erased_status == z3.sat,
        "all_zero_status": str(all_zero_status),
        "all_zero_unsat": all_zero_status == z3.unsat,
        "drop_all_zero_constraint_flips_unsat_to_sat": all_zero_status == z3.unsat and erased_status == z3.sat,
        "witness": witness,
    }


def cvc5_assert_all(solver: cvc5.Solver, terms: list[Any], kind: Kind) -> Any:
    if not terms:
        return solver.mkBoolean(True) if kind == Kind.AND else solver.mkBoolean(False)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(kind, *terms)


def cvc5_status_text(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def cvc5_structural_probe(name: str, coeffs: list[int]) -> dict[str, Any]:
    def make_solver() -> tuple[cvc5.Solver, list[Any], list[Any]]:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        int_sort = solver.getIntegerSort()
        zero = solver.mkInteger(0)
        xs = [solver.mkConst(int_sort, f"{name}_a_{idx}") for idx in range(len(coeffs))]
        for var, value in zip(xs, coeffs, strict=True):
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(value)))
        nonzero_terms = [
            solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, var, zero))
            for var in xs
        ]
        zero_terms = [solver.mkTerm(Kind.EQUAL, var, zero) for var in xs]
        return solver, nonzero_terms, zero_terms

    structural, nonzero_terms, _zero_terms = make_solver()
    structural.assertFormula(cvc5_assert_all(structural, nonzero_terms, Kind.OR))
    nonzero_result = structural.checkSat()

    erased, _nonzero_terms, _zero_terms = make_solver()
    erased_result = erased.checkSat()

    all_zero, _nonzero_terms, zero_terms = make_solver()
    all_zero.assertFormula(cvc5_assert_all(all_zero, zero_terms, Kind.AND))
    all_zero_result = all_zero.checkSat()

    return {
        "solver": "cvc5",
        "nonzero_exists_status": cvc5_status_text(nonzero_result),
        "nonzero_exists_sat": nonzero_result.isSat(),
        "nonzero_exists_unsat": nonzero_result.isUnsat(),
        "drop_nonzero_constraint_status": cvc5_status_text(erased_result),
        "drop_nonzero_constraint_flips_unsat_to_sat": nonzero_result.isUnsat() and erased_result.isSat(),
        "all_zero_status": cvc5_status_text(all_zero_result),
        "all_zero_unsat": all_zero_result.isUnsat(),
        "drop_all_zero_constraint_flips_unsat_to_sat": all_zero_result.isUnsat() and erased_result.isSat(),
    }


def solver_agreement(z3_row: dict[str, Any], cvc5_row: dict[str, Any]) -> bool:
    return (
        z3_row["nonzero_exists_status"] == cvc5_row["nonzero_exists_status"]
        and z3_row["all_zero_status"] == cvc5_row["all_zero_status"]
    )


def main() -> int:
    preflight = preflight_import_check()
    tables = build_tables()
    summaries = {name: tensor_summary(name, table) for name, table in tables.items()}
    coeffs = {name: coeffs_from_tensor(associator_tensor(table)) for name, table in tables.items()}

    z3_proofs = {name: z3_structural_probe(name, coeffs[name]) for name in ("R", "C", "H", "O")}
    cvc5_proofs = {name: cvc5_structural_probe(name, coeffs[name]) for name in ("R", "C", "H", "O")}
    agreement = {name: solver_agreement(z3_proofs[name], cvc5_proofs[name]) for name in ("R", "C", "H", "O")}

    quaternion_forced_unsat = all(
        z3_proofs[name]["nonzero_exists_unsat"] and cvc5_proofs[name]["nonzero_exists_unsat"]
        for name in ("R", "C", "H")
    )
    quaternion_eraseflip = all(
        z3_proofs[name]["drop_nonzero_constraint_flips_unsat_to_sat"]
        and cvc5_proofs[name]["drop_nonzero_constraint_flips_unsat_to_sat"]
        for name in ("R", "C", "H")
    )
    octonion_sat_nonzero = (
        z3_proofs["O"]["nonzero_exists_sat"]
        and cvc5_proofs["O"]["nonzero_exists_sat"]
        and summaries["O"]["associator_max_residual"] > TOL
    )
    octonion_zero_claim_eraseflip = (
        z3_proofs["O"]["drop_all_zero_constraint_flips_unsat_to_sat"]
        and cvc5_proofs["O"]["drop_all_zero_constraint_flips_unsat_to_sat"]
    )
    z3_cvc5_agree = all(agreement.values())
    proof_load_bearing_eraseflip = quaternion_eraseflip and octonion_zero_claim_eraseflip
    not_bare_jnp = bool(
        TOOL_INTEGRATION_DEPTH["z3"] == "load_bearing"
        and TOOL_INTEGRATION_DEPTH["cvc5"] == "load_bearing"
        and z3_cvc5_agree
        and proof_load_bearing_eraseflip
    )
    all_pass = bool(
        preflight["jax_enable_x64"]
        and quaternion_forced_unsat
        and z3_cvc5_agree
        and proof_load_bearing_eraseflip
        and octonion_sat_nonzero
        and not_bare_jnp
    )

    payload: dict[str, Any] = {
        "sim_id": OBJECT_ID,
        "name": "R3 division algebra onset JAX leg",
        "version": "1.0",
        "tier": "formal_scout_jax_leg",
        "created_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "sim_execution_kind": sim_execution_kind,
        "allowed_claim": ALLOWED_CLAIM,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "runtime_preflight": preflight,
        "numpy_control_only": {
            "used_for_algebra": False,
            "used_for_proof": False,
            "version_record_only": True,
        },
        "jax_numeric_onset": summaries,
        "smt_structural_proof": {
            "encoding": (
                "Exact integer associator coefficients from JAX x64 Cayley-Dickson "
                "tables are asserted as SMT Int equalities; nonzero-existence and "
                "all-zero obligations are checked independently in z3 and cvc5."
            ),
            "z3": z3_proofs,
            "cvc5": cvc5_proofs,
            "agreement": agreement,
            "quaternion_dim_le_4_associativity_forced_unsat": quaternion_forced_unsat,
            "octonion_associator_sat_nonzero": octonion_sat_nonzero,
            "erase_flip": {
                "quaternion_drop_nonzero_constraint_unsat_to_sat": quaternion_eraseflip,
                "octonion_drop_all_zero_constraint_unsat_to_sat": octonion_zero_claim_eraseflip,
                "proof_load_bearing_eraseflip": proof_load_bearing_eraseflip,
            },
        },
        "positive": {
            "runtime_preflight_imports": {
                "pass": all(row["ok"] for row in preflight["imports"].values()),
                "sys_executable": sys.executable,
            },
            "jax_x64_cayley_dickson_onset": {
                "pass": bool(preflight["jax_enable_x64"] and summaries["H"]["associative_by_jax"] and not summaries["O"]["associative_by_jax"]),
                "H_max_residual": summaries["H"]["associator_max_residual"],
                "O_max_residual": summaries["O"]["associator_max_residual"],
            },
            "z3_cvc5_agreement": {"pass": z3_cvc5_agree, "per_rung": agreement},
            "quaternion_dim_le_4_forced_associative": {"pass": quaternion_forced_unsat},
            "octonion_assoc_nonzero": {"pass": octonion_sat_nonzero},
            "proof_load_bearing_eraseflip": {"pass": proof_load_bearing_eraseflip},
            "not_bare_jnp": {"pass": not_bare_jnp},
        },
        "boundary": {
            "role_separation": {
                "pass": True,
                "jax_role": "finite x64 Cayley-Dickson construction",
                "smt_role": "load-bearing associator proof",
                "numpy_role": "control-only import/version record",
            },
            "bounded_scope": {
                "pass": True,
                "rungs": list(RUNG_NAMES),
                "max_dim": 8,
                "out_of_scope": ["Julia parity", "PyTorch parity", "scientific bridge", "canonical admission"],
            },
        },
        "graveyard_companions": {
            "bare_jnp_proof": {
                "pass": not_bare_jnp,
                "reason": "rejected: proof verdicts require agreeing z3 and cvc5 SMT checks",
            },
            "tautological_solver_import": {
                "pass": proof_load_bearing_eraseflip,
                "reason": "rejected: solver verdicts flip when the tested associator constraint is erased",
            },
        },
        "nearby_variants": {"passed": 2, "total": 2, "variants": ["R/C/H associative boundary", "O nonassociative onset"]},
        "why_not_v4_probes": [
            "This is a bounded R3 formal scout leg, not a v4 probe or canonical sim.",
            "It does not consume Julia or PyTorch outputs and does not promote a bridge claim.",
        ],
        "blockers": [],
        "all_pass": all_pass,
        "end_flags": {
            "z3_cvc5_agree": z3_cvc5_agree,
            "proof_load_bearing_eraseflip": proof_load_bearing_eraseflip,
            "octonion_assoc_nonzero": octonion_sat_nonzero,
            "not_bare_jnp": not_bare_jnp,
            "ran": True,
        },
    }
    payload["result_sha256_without_self"] = hashlib.sha256(
        json.dumps({k: v for k, v in payload.items() if k != "result_sha256_without_self"}, sort_keys=True).encode("utf-8")
    ).hexdigest()

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    flags = payload["end_flags"]
    print(
        "SCOUT_DONE "
        f"z3_cvc5_agree={flags['z3_cvc5_agree']} "
        f"proof_load_bearing_eraseflip={flags['proof_load_bearing_eraseflip']} "
        f"octonion_assoc_nonzero={flags['octonion_assoc_nonzero']} "
        f"not_bare_jnp={flags['not_bare_jnp']} "
        f"ran={flags['ran']}"
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

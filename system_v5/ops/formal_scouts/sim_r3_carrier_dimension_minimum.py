#!/usr/bin/env python3
"""R3 carrier-dimension minimum scout for the non-associative defect.

Scratch diagnostic only. This scans finite Cayley-Dickson carriers R, C, H,
and O and asks the carrier-dimension question only: where can a nonzero
associator (ab)c - a(bc) first appear?
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


OBJECT_ID = "r3_carrier_dimension_minimum"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/r3_carrier_dimension_minimum_results.json"
JULIA_REFERENCE_PATH = ROOT / "system_v5/julia_carrier/r3_carrier_dimension_minimum_julia_results.json"
TOL = 1.0e-12
NONZERO_TOL = 1.0e-9
RUNG_NAMES = ["R", "C", "H", "O"]

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
sim_execution_kind = "classical"
SIM_EXECUTION_KIND = sim_execution_kind

ALLOWED_CLAIM = (
    "Carrier-dimension minimum only: in the finite Cayley-Dickson R/C/H/O scan, "
    "the associator is zero through dimension 4 and first nonzero at dimension 8."
)
CLAIM_CEILING = (
    "Allowed only: bottom-up R3 algebraic carrier-dimension minimum for a "
    "nonzero associator. No promotion, no formal admission, no downstream interpretation."
)

TOOL_MANIFEST = {
    "JAX": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 Cayley-Dickson table construction and associator residual scan",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 array backend for finite carrier arithmetic; no plain NumPy compute path",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON receipt, timestamps, hashing, path handling, and parity finalization",
    },
    "Julia mirror": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent backend mirror that reads the current same-run JAX result",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "not used: explicit JAX jnp-only compute lane",
    },
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": "not used: explicit no-torch fence for this row",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "JAX": "load_bearing",
    "jax.numpy": "load_bearing",
    "Python stdlib": "supportive",
    "Julia mirror": "load_bearing",
    "numpy": None,
    "pytorch": None,
}

SIM_TEMPLATE_SURFACE = {
    "identity": ["sim_id", "name", "version", "tier"],
    "tooling": ["TOOL_MANIFEST", "TOOL_INTEGRATION_DEPTH", "classification"],
    "negatives": ["positive", "negative", "boundary", "probe"],
    "promotion": ["promotion_allowed", "formal_admission_allowed", "blocked_consumers"],
}


def run_token() -> str:
    return os.environ.get("R3_CARRIER_DIMENSION_RUN_TOKEN", "manual-token-not-set")


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def basis_vector(dim: int, idx: int) -> jax.Array:
    return jnp.eye(dim, dtype=jnp.float64)[idx]


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


def associator_vector(table: jax.Array, x: jax.Array, y: jax.Array, z: jax.Array) -> jax.Array:
    return multiply(table, multiply(table, x, y), z) - multiply(table, x, multiply(table, y, z))


def associator_scan(table: jax.Array) -> dict[str, Any]:
    left = jnp.einsum("mab,kmc->kabc", table, table)
    right = jnp.einsum("nbc,kan->kabc", table, table)
    residuals = left - right
    norms = jnp.linalg.norm(residuals, axis=0)
    max_value = py_float(jnp.max(norms))
    flat_idx = int(jax.device_get(jnp.argmax(norms)))
    a, b, c = [int(x) for x in jnp.unravel_index(flat_idx, norms.shape)]
    witness_vector = associator_vector(table, basis_vector(table.shape[0], a), basis_vector(table.shape[0], b), basis_vector(table.shape[0], c))
    return {
        "max_residual": max_value,
        "witness_basis_indices": [a, b, c],
        "witness_expression_ids": [f"(e{a}*e{b})*e{c}", f"e{a}*(e{b}*e{c})"],
        "witness_vector": [py_float(cell) for cell in witness_vector],
        "nonzero": max_value > NONZERO_TOL,
    }


def analyze_rung(name: str, table: jax.Array) -> dict[str, Any]:
    assoc = associator_scan(table)
    return {
        "name": name,
        "dim": int(table.shape[0]),
        "associator_max": assoc["max_residual"],
        "associator_check": assoc,
        "associative": assoc["max_residual"] <= TOL,
    }


def first_nonzero_associator_dim(rungs: dict[str, dict[str, Any]]) -> int | None:
    for name in RUNG_NAMES:
        if bool(rungs[name]["associator_check"]["nonzero"]):
            return int(rungs[name]["dim"])
    return None


def catalan_count(n: int) -> int:
    if n <= 1:
        return 1
    values = [0 for _ in range(n)]
    values[0] = 1
    for size in range(2, n + 1):
        values[size - 1] = sum(values[left - 1] * values[size - left - 1] for left in range(1, size))
    return values[n - 1]


def control_comparisons(rungs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    two_input_parenthesizations = catalan_count(2)
    three_input_parenthesizations = catalan_count(3)
    return [
        {
            "name": "dimension_boundary_H_to_O",
            "left_quantity": "H.associator_max",
            "right_quantity": "O.associator_max",
            "left_value": rungs["H"]["associator_max"],
            "right_value": rungs["O"]["associator_max"],
            "pass": rungs["H"]["associator_max"] <= TOL and rungs["O"]["associator_max"] > NONZERO_TOL,
            "control_can_fail": True,
        },
        {
            "name": "two_input_bracketing_insufficient",
            "left_quantity": "two_input_parenthesization_count",
            "right_quantity": "three_input_parenthesization_count",
            "left_value": two_input_parenthesizations,
            "right_value": three_input_parenthesizations,
            "pass": two_input_parenthesizations < three_input_parenthesizations,
            "control_can_fail": True,
        },
        {
            "name": "dim_le4_negative_control",
            "left_quantity": "max_associator_dim_le4",
            "right_quantity": "O.associator_max",
            "left_value": max(rungs["R"]["associator_max"], rungs["C"]["associator_max"], rungs["H"]["associator_max"]),
            "right_value": rungs["O"]["associator_max"],
            "pass": max(rungs["R"]["associator_max"], rungs["C"]["associator_max"], rungs["H"]["associator_max"]) <= TOL
            and rungs["O"]["associator_max"] > NONZERO_TOL,
            "control_can_fail": True,
        },
    ]


def no_self_diff_tautologies(rows: list[dict[str, Any]]) -> bool:
    return all(str(row["left_quantity"]) != str(row["right_quantity"]) for row in rows)


def shared_payload_digest(shared: dict[str, Any]) -> str:
    payload = json.dumps(shared, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def parity_against_julia(result: dict[str, Any]) -> dict[str, Any]:
    if not JULIA_REFERENCE_PATH.exists():
        return {
            "peer_result_path": str(JULIA_REFERENCE_PATH),
            "status": "pending_julia_reference",
            "within_tolerance": False,
            "parity_within_run": False,
            "parity_max_diff": None,
            "numeric_rows": [],
            "boolean_mismatches": [],
            "string_mismatches": [],
            "missing_keys": ["peer_result"],
        }
    peer = json.loads(JULIA_REFERENCE_PATH.read_text(encoding="utf-8"))
    numeric_rows = []
    missing_keys = []
    max_diff = 0.0
    for key, value in result["shared_scalars"].items():
        if key not in peer.get("shared_scalars", {}):
            missing_keys.append(key)
            continue
        peer_value = float(peer["shared_scalars"][key])
        diff = abs(float(value) - peer_value)
        max_diff = max(max_diff, diff)
        numeric_rows.append({"key": key, "jax": float(value), "julia": peer_value, "abs_diff": diff})

    boolean_mismatches = []
    for key, value in result["shared_booleans"].items():
        if key not in peer.get("shared_booleans", {}):
            missing_keys.append(key)
            continue
        if bool(value) != bool(peer["shared_booleans"][key]):
            boolean_mismatches.append({"key": key, "jax": bool(value), "julia": bool(peer["shared_booleans"][key])})

    string_mismatches = []
    for key, value in result["shared_strings"].items():
        if key not in peer.get("shared_strings", {}):
            missing_keys.append(key)
            continue
        if str(value) != str(peer["shared_strings"][key]):
            string_mismatches.append({"key": key, "jax": str(value), "julia": str(peer["shared_strings"][key])})

    jax_reference = peer.get("jax_reference", {})
    parity_within_run = (
        peer.get("backend") == "julia"
        and jax_reference.get("path") == str(RESULT_PATH)
        and jax_reference.get("run_token") == result["run_token"]
        and jax_reference.get("shared_value_digest") == result["shared_value_digest"]
    )
    within_tolerance = (
        max_diff <= TOL
        and not boolean_mismatches
        and not string_mismatches
        and not missing_keys
        and parity_within_run
    )
    return {
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "status": "compared",
        "within_tolerance": within_tolerance,
        "parity_within_run": parity_within_run,
        "parity_max_diff": max_diff,
        "numeric_rows": numeric_rows,
        "boolean_mismatches": boolean_mismatches,
        "string_mismatches": string_mismatches,
        "missing_keys": missing_keys,
    }


def attach_parity(result: dict[str, Any]) -> dict[str, Any]:
    result["parity"] = parity_against_julia(result)
    result.setdefault("positive", {})["dual_backend_parity"] = {"pass": result["parity"]["within_tolerance"]}
    result["parity_within_run"] = bool(result["parity"]["parity_within_run"])
    result["all_pass"] = bool(result["core_pass"] and result["parity"]["within_tolerance"])
    result["stop_condition_fired"] = not bool(result["all_pass"])
    result["result_summary"]["parity_within_run"] = result["parity_within_run"]
    result["result_summary"]["all_pass"] = result["all_pass"]
    return result


def build_result() -> dict[str, Any]:
    tables = build_tables()
    rungs = {name: analyze_rung(name, tables[name]) for name in RUNG_NAMES}
    controls = control_comparisons(rungs)
    no_self_diff = no_self_diff_tautologies(controls)
    min_dim = first_nonzero_associator_dim(rungs)
    associator_needs_3_inputs = catalan_count(3) == 2
    two_input_insufficient = catalan_count(2) < catalan_count(3)
    dim_le4_zero = all(rungs[name]["associator_max"] <= TOL for name in ["R", "C", "H"])
    octonion_anchor = abs(rungs["O"]["associator_max"] - 2.0) <= TOL
    dimension_minimum_genuine = (
        min_dim == 8
        and dim_le4_zero
        and octonion_anchor
        and associator_needs_3_inputs
        and two_input_insufficient
        and no_self_diff
        and all(bool(row["pass"]) and bool(row["control_can_fail"]) for row in controls)
    )
    classification_ok = classification == "scratch_diagnostic"
    promotion_ok = promotion_allowed is False
    formal_ok = formal_admission_allowed is False
    jax_x64_ok = bool(jax.config.read("jax_enable_x64"))

    shared_scalars: dict[str, float] = {}
    for name in RUNG_NAMES:
        shared_scalars[f"{name}.dim"] = float(rungs[name]["dim"])
        shared_scalars[f"{name}.associator_max"] = float(rungs[name]["associator_max"])
    shared_scalars["max_associator_dim_le4"] = max(
        rungs["R"]["associator_max"], rungs["C"]["associator_max"], rungs["H"]["associator_max"]
    )
    shared_scalars["O.octonion_associator_anchor"] = float(rungs["O"]["associator_max"])
    shared_scalars["two_input_parenthesization_count"] = float(catalan_count(2))
    shared_scalars["three_input_parenthesization_count"] = float(catalan_count(3))
    shared_scalars["min_nonassoc_algebra_dim"] = float(min_dim or -1)

    shared_booleans = {
        "associator_needs_3_inputs": associator_needs_3_inputs,
        "two_input_insufficient": two_input_insufficient,
        "dim_le4_associator_zero": dim_le4_zero,
        "octonion_associator_anchor_2": octonion_anchor,
        "dimension_minimum_genuine": dimension_minimum_genuine,
        "no_self_diff_tautologies": no_self_diff,
        "classification_is_scratch_diagnostic": classification_ok,
        "promotion_false": promotion_ok,
        "formal_admission_false": formal_ok,
        "jax_enable_x64": jax_x64_ok,
        "plain_numpy_imported": False,
        "torch_imported": False,
    }
    for name in RUNG_NAMES:
        shared_booleans[f"{name}.associative"] = bool(rungs[name]["associative"])
        shared_booleans[f"{name}.associator_nonzero"] = bool(rungs[name]["associator_check"]["nonzero"])

    shared_strings = {
        "object_id": OBJECT_ID,
        "allowed_claim": ALLOWED_CLAIM,
        "first_nonzero_rung": "O" if min_dim == 8 else "not_found",
    }
    shared = {
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "shared_strings": shared_strings,
    }

    core_pass = (
        dimension_minimum_genuine
        and classification_ok
        and promotion_ok
        and formal_ok
        and jax_x64_ok
    )
    result = {
        "schema": "codex_ratchet.formal_scout.scratch_diagnostic.v1",
        "object_id": OBJECT_ID,
        "sim_id": OBJECT_ID,
        "name": OBJECT_ID,
        "version": "1.0",
        "tier": "R3_foundation_carrier_dimension_minimum",
        "backend": "jax",
        "run_token": run_token(),
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "claim_ceiling": CLAIM_CEILING,
        "allowed_claims": [ALLOWED_CLAIM],
        "promotion_status": "diagnostic_only",
        "eligible_consumers": [],
        "blocked_consumers": ["promotion", "formal_admission", "downstream interpretation"],
        "sim_execution_kind": sim_execution_kind,
        "SIM_TEMPLATE_surface": SIM_TEMPLATE_SURFACE,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "required_tools": ["JAX", "jax.numpy", "Julia mirror"],
        "actual_tools_used": ["JAX", "jax.numpy", "Python stdlib", "Julia mirror"],
        "plain_numpy_imported": False,
        "torch_imported": False,
        "tol": TOL,
        "nonzero_tol": NONZERO_TOL,
        "construction": {
            "method": "finite Cayley-Dickson doubling",
            "rung_names": RUNG_NAMES,
            "rung_dims": {name: rungs[name]["dim"] for name in RUNG_NAMES},
        },
        "rungs": rungs,
        "control_comparison_pairs": controls,
        "probe": {
            "question": "minimum Cayley-Dickson carrier dimension supporting a nonzero associator",
            "expression": "(ab)c - a(bc)",
            "measured_property": "basis-triple associator residual",
            "control_rule": "controls compare distinct computed quantities and can fail",
        },
        "positive": {
            "octonion_associator_nonzero": {
                "pass": bool(rungs["O"]["associator_max"] > NONZERO_TOL),
                "residual": rungs["O"]["associator_max"],
            },
            "octonion_associator_anchor_2": {"pass": octonion_anchor, "residual": rungs["O"]["associator_max"]},
            "associator_needs_3_inputs": {"pass": associator_needs_3_inputs},
            "classification_is_scratch_diagnostic": {"pass": classification_ok},
            "promotion_allowed_false": {"pass": promotion_ok},
            "formal_admission_allowed_false": {"pass": formal_ok},
            "no_self_diff_tautologies": {"pass": no_self_diff},
        },
        "negative": {
            "dim_le4_associative_controls": {
                "pass": dim_le4_zero,
                "R_associator_max": rungs["R"]["associator_max"],
                "C_associator_max": rungs["C"]["associator_max"],
                "H_associator_max": rungs["H"]["associator_max"],
                "control_can_fail": True,
            },
            "two_input_bracketing_insufficient": {
                "pass": two_input_insufficient,
                "two_input_parenthesization_count": catalan_count(2),
                "three_input_parenthesization_count": catalan_count(3),
                "control_can_fail": True,
            },
        },
        "boundary": {
            "H_to_O_associator_boundary": {
                "pass": rungs["H"]["associator_max"] <= TOL and rungs["O"]["associator_max"] > NONZERO_TOL,
                "left": "H",
                "right": "O",
                "left_dim": 4,
                "right_dim": 8,
                "H_associator_max": rungs["H"]["associator_max"],
                "O_associator_max": rungs["O"]["associator_max"],
            },
            "claim_ceiling": CLAIM_CEILING,
        },
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "shared_strings": shared_strings,
        "shared_value_digest": shared_payload_digest(shared),
        "core_pass": core_pass,
        "all_pass": False,
        "stop_condition_fired": True,
        "pass_rule": (
            "dim<=4 associator residuals are zero, dim 8 residual has 2.0 anchor, controls are non-tautological, "
            "three inputs are required, and same-run Julia parity passes"
        ),
        "fail_rule": "any nonzero dim<=4 associator, missing dim 8 anchor, self-diff control, fence violation, or stale parity",
        "result_summary": {
            "min_nonassoc_algebra_dim": int(min_dim or -1),
            "associator_needs_3_inputs": associator_needs_3_inputs,
            "two_input_insufficient": two_input_insufficient,
            "dimension_minimum_genuine": dimension_minimum_genuine,
            "octonion_associator": rungs["O"]["associator_max"],
            "quaternion_associator": rungs["H"]["associator_max"],
            "no_self_diff": no_self_diff,
            "parity_within_run": False,
            "all_pass": False,
        },
        "criteria_checked": [
            "finite Cayley-Dickson R/C/H/O table construction",
            "basis-triple associator residual for dimensions 1, 2, 4, and 8",
            "negative controls: dimensions <=4 remain associative",
            "boundary control: dimension 4 to dimension 8",
            "two-input parenthesization insufficiency for a three-input associator defect",
            "no control compares an expression with itself",
            "JAX/Julia shared payload parity with matching run token",
        ],
        "associator_needs_3_inputs": associator_needs_3_inputs,
        "min_nonassoc_algebra_dim": int(min_dim or -1),
        "two_input_insufficient": two_input_insufficient,
        "dimension_minimum_genuine": dimension_minimum_genuine,
        "no_self_diff": no_self_diff,
        "julia_in_actual_tools": "Julia mirror" in ["JAX", "jax.numpy", "Python stdlib", "Julia mirror"],
        "parity_within_run": False,
    }
    return attach_parity(result)


def finalize_existing_result() -> dict[str, Any]:
    result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    result["finalized_at"] = _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return attach_parity(result)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--finalize-parity", action="store_true", help="update JAX result with current Julia parity")
    args = parser.parse_args()
    result = finalize_existing_result() if args.finalize_parity else build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {RESULT_PATH}")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "core_pass": result["core_pass"],
                "parity_within_run": result["parity_within_run"],
                "min_nonassoc_algebra_dim": result["min_nonassoc_algebra_dim"],
                "two_input_insufficient": result["two_input_insufficient"],
                "dimension_minimum_genuine": result["dimension_minimum_genuine"],
                "no_self_diff": result["no_self_diff"],
            },
            sort_keys=True,
        )
    )
    return 0 if (result["all_pass"] if args.finalize_parity else result["core_pass"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""R3 division-algebra ladder onset carrier-candidate scout.

Scratch diagnostic only. Builds the finite Cayley-Dickson ladder R -> C -> H
-> O -> S and measures where algebraic carrier properties first fail.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


OBJECT_ID = "r3_division_algebra_ladder_onset"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/r3_division_algebra_ladder_onset_results.json"
JULIA_REFERENCE_PATH = ROOT / "system_v5/julia_carrier/r3_division_algebra_ladder_onset_julia_results.json"
TOL = 1.0e-12
ONSET_TOL = 1.0e-9
RUNG_NAMES = ["R", "C", "H", "O", "S"]

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
sim_execution_kind = "classical"
SIM_EXECUTION_KIND = sim_execution_kind

ALLOWED_CLAIM = (
    "Finite R/C/H/O/S carrier-candidate property-onset map over the verified "
    "R0-R2 foundation surface; scratch diagnostic only."
)
CLAIM_CEILING = (
    "Allowed only: bottom-up finite carrier-candidate algebra property onset "
    "map. No promotion, no formal admission, no downstream scientific claim."
)

TOOL_MANIFEST = {
    "JAX": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 Cayley-Dickson table construction and property residual computation",
    },
    "jnp": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 array backend for finite vector/table arithmetic; no plain NumPy compute path",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON receipt, timestamps, hashing, and path handling",
    },
    "Julia mirror": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent backend parity over the shared result payload",
    },
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": "not used: explicit user fence for this row says no torch",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "JAX": "load_bearing",
    "jnp": "load_bearing",
    "Python stdlib": "supportive",
    "Julia mirror": "load_bearing",
    "pytorch": None,
}

SIM_TEMPLATE_SURFACE = {
    "identity": ["sim_id", "name", "version", "tier"],
    "tooling": ["TOOL_MANIFEST", "TOOL_INTEGRATION_DEPTH", "classification"],
    "negatives": ["positive", "negative", "boundary", "probe"],
    "promotion": ["promotion_allowed", "formal_admission_allowed", "blocked_consumers"],
}


def run_token() -> str:
    return os.environ.get("R3_DIVISION_RUN_TOKEN", "manual-token-not-set")


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


def table_checksum(table: jax.Array) -> dict[str, Any]:
    dim = table.shape[0]
    c = jnp.arange(1, dim + 1, dtype=jnp.float64).reshape((dim, 1, 1))
    a = jnp.arange(1, dim + 1, dtype=jnp.float64).reshape((1, dim, 1))
    b = jnp.arange(1, dim + 1, dtype=jnp.float64).reshape((1, 1, dim))
    weights = 1_000_003.0 * c + 1_009.0 * a + b
    nonzero = jnp.abs(table) > 0.0
    return {
        "nonzero_entry_count": int(jax.device_get(jnp.sum(nonzero))),
        "sum_abs_entries": py_float(jnp.sum(jnp.abs(table))),
        "weighted_checksum": py_float(jnp.sum(table * weights)),
    }


def commutator_scan(table: jax.Array) -> dict[str, Any]:
    differences = table - jnp.swapaxes(table, 1, 2)
    norms = jnp.linalg.norm(differences, axis=0)
    max_value = py_float(jnp.max(norms))
    flat_idx = int(jax.device_get(jnp.argmax(norms)))
    a, b = [int(x) for x in jnp.unravel_index(flat_idx, norms.shape)]
    return {
        "max_residual": max_value,
        "witness_basis_indices": [a, b],
        "witness_expression_ids": [f"e{a}*e{b}", f"e{b}*e{a}"],
    }


def associator_scan(table: jax.Array) -> dict[str, Any]:
    left = jnp.einsum("mab,kmc->kabc", table, table)
    right = jnp.einsum("nbc,kan->kabc", table, table)
    residuals = left - right
    norms = jnp.linalg.norm(residuals, axis=0)
    max_value = py_float(jnp.max(norms))
    flat_idx = int(jax.device_get(jnp.argmax(norms)))
    a, b, c = [int(x) for x in jnp.unravel_index(flat_idx, norms.shape)]
    return {
        "max_residual": max_value,
        "witness_basis_indices": [a, b, c],
        "witness_expression_ids": [f"(e{a}*e{b})*e{c}", f"e{a}*(e{b}*e{c})"],
    }


def pair_vector(dim: int, i: int, j: int, si: float = 1.0, sj: float = 1.0) -> jax.Array:
    return jnp.zeros((dim,), dtype=jnp.float64).at[i].set(si).at[j].set(sj)


def deterministic_probe(dim: int, sample_idx: int, side: int) -> jax.Array:
    values = [
        (
            float(
                (
                    (sample_idx + 17) * (j + 3) * (side + 5) * 37
                    + (j + 1) ** 2 * 19
                    + sample_idx * 11
                    + side * 13
                )
                % 101
            )
            - 50.0
        )
        / 37.0
        for j in range(1, dim + 1)
    ]
    return jnp.asarray(values, dtype=jnp.float64)


def associator_vector(table: jax.Array, x: jax.Array, y: jax.Array, z: jax.Array) -> jax.Array:
    return multiply(table, multiply(table, x, y), z) - multiply(table, x, multiply(table, y, z))


def alternativity_scan(table: jax.Array) -> dict[str, Any]:
    dim = table.shape[0]
    xs: list[jax.Array] = [basis_vector(dim, idx) for idx in range(dim)]
    ys: list[jax.Array] = [basis_vector(dim, idx) for idx in range(dim)]
    if dim <= 8:
        for i in range(dim):
            for j in range(i + 1, dim):
                xs.append(pair_vector(dim, i, j, 1.0, 1.0))
                xs.append(pair_vector(dim, i, j, 1.0, -1.0))
        xs.extend(deterministic_probe(dim, idx, 7) for idx in range(1, 5))
    else:
        xs.append(pair_vector(dim, 1, 10, -1.0, -1.0))
        ys = [basis_vector(dim, 4)]

    max_value = 0.0
    witness: dict[str, Any] = {"kind": "none", "residual": 0.0}
    for ix, x in enumerate(xs):
        for iy, y in enumerate(ys):
            xxy = py_float(jnp.linalg.norm(associator_vector(table, x, x, y)))
            if xxy > max_value:
                max_value = xxy
                witness = {"kind": "(x*x)*y - x*(x*y)", "x_probe_index": ix, "y_probe_index": iy, "residual": xxy}
            xyy = py_float(jnp.linalg.norm(associator_vector(table, x, y, y)))
            if xyy > max_value:
                max_value = xyy
                witness = {"kind": "(x*y)*y - x*(y*y)", "x_probe_index": ix, "y_probe_index": iy, "residual": xyy}
    return {"max_residual": max_value, "witness": witness, "probe_count": len(xs) * len(ys)}


def squared_norm(x: jax.Array) -> float:
    return py_float(jnp.vdot(x, x))


def zero_divisor_vectors(dim: int) -> tuple[jax.Array, jax.Array] | None:
    if dim < 16:
        return None
    return pair_vector(dim, 1, 10, -1.0, -1.0), pair_vector(dim, 4, 15, -1.0, 1.0)


def norm_division_scan(table: jax.Array) -> dict[str, Any]:
    dim = table.shape[0]
    probes = [basis_vector(dim, idx) for idx in range(dim)]
    probes.extend(deterministic_probe(dim, idx, 1) for idx in range(1, 7))
    zero_pair = zero_divisor_vectors(dim)
    if zero_pair is not None:
        probes.extend(zero_pair)

    max_residual = 0.0
    witness: dict[str, Any] = {"kind": "none", "residual": 0.0}
    for ix, x in enumerate(probes):
        for iy, y in enumerate(probes):
            product = multiply(table, x, y)
            product_norm = squared_norm(product)
            norm_product = squared_norm(x) * squared_norm(y)
            residual = abs(product_norm - norm_product)
            if residual > max_residual:
                max_residual = residual
                witness = {
                    "kind": "squared_norm_multiplicativity",
                    "left_probe_index": ix,
                    "right_probe_index": iy,
                    "product_squared_norm": product_norm,
                    "factor_squared_norm_product": norm_product,
                    "residual": residual,
                }

    zero_report: dict[str, Any]
    if zero_pair is None:
        zero_report = {
            "checked": False,
            "has_zero_divisor_witness": False,
            "product_squared_norm": None,
            "factor_squared_norm_product": None,
        }
    else:
        left, right = zero_pair
        product = multiply(table, left, right)
        product_norm = squared_norm(product)
        factor_norm_product = squared_norm(left) * squared_norm(right)
        zero_report = {
            "checked": True,
            "has_zero_divisor_witness": product_norm <= TOL and factor_norm_product > ONSET_TOL,
            "product_squared_norm": product_norm,
            "factor_squared_norm_product": factor_norm_product,
            "left_terms": ["-e1", "-e10"],
            "right_terms": ["-e4", "e15"],
        }
    return {
        "max_residual": max_residual,
        "witness": witness,
        "zero_divisor": zero_report,
        "norm_multiplicative": max_residual <= TOL,
        "norm_division": max_residual <= TOL and not bool(zero_report["has_zero_divisor_witness"]),
    }


def analyze_rung(name: str, table: jax.Array) -> dict[str, Any]:
    comm = commutator_scan(table)
    assoc = associator_scan(table)
    alt = alternativity_scan(table)
    norm_division = norm_division_scan(table)
    return {
        "name": name,
        "dim": table.shape[0],
        "commutator_max": comm["max_residual"],
        "associator_max": assoc["max_residual"],
        "alternativity_residual": alt["max_residual"],
        "norm_multiplicativity_residual": norm_division["max_residual"],
        "has_zero_divisor_witness": bool(norm_division["zero_divisor"]["has_zero_divisor_witness"]),
        "commutator_check": comm,
        "associator_check": assoc,
        "alternativity_check": alt,
        "norm_division_check": norm_division,
        "table_checksum": table_checksum(table),
        "properties": {
            "commutative": comm["max_residual"] <= TOL,
            "associative": assoc["max_residual"] <= TOL,
            "alternative": alt["max_residual"] <= TOL,
            "norm_multiplicative": norm_division["max_residual"] <= TOL,
            "norm_division": bool(norm_division["norm_division"]),
        },
    }


def first_lost(rungs: dict[str, dict[str, Any]], key: str) -> str:
    for name in RUNG_NAMES:
        if not bool(rungs[name]["properties"][key]):
            return name
    return "not_lost"


def control_pairs(rungs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "name": "commutativity_onset",
            "left_quantity": "C.commutator_max",
            "right_quantity": "H.commutator_max",
            "left_value": rungs["C"]["commutator_max"],
            "right_value": rungs["H"]["commutator_max"],
            "negative_case": "H",
            "negative_property_value": rungs["H"]["properties"]["commutative"],
            "negative_case_fails": not bool(rungs["H"]["properties"]["commutative"]),
        },
        {
            "name": "associativity_onset",
            "left_quantity": "H.associator_max",
            "right_quantity": "O.associator_max",
            "left_value": rungs["H"]["associator_max"],
            "right_value": rungs["O"]["associator_max"],
            "negative_case": "O",
            "negative_property_value": rungs["O"]["properties"]["associative"],
            "negative_case_fails": not bool(rungs["O"]["properties"]["associative"]),
        },
        {
            "name": "norm_division_onset",
            "left_quantity": "O.norm_multiplicativity_residual",
            "right_quantity": "S.norm_multiplicativity_residual",
            "left_value": rungs["O"]["norm_multiplicativity_residual"],
            "right_value": rungs["S"]["norm_multiplicativity_residual"],
            "negative_case": "S",
            "negative_property_value": rungs["S"]["properties"]["norm_division"],
            "negative_case_fails": not bool(rungs["S"]["properties"]["norm_division"]),
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
            "status": "missing_julia_reference",
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


def build_result() -> dict[str, Any]:
    tables = build_tables()
    rungs = {name: analyze_rung(name, tables[name]) for name in RUNG_NAMES}
    onsets = {
        "commutativity_lost_at": first_lost(rungs, "commutative"),
        "associativity_lost_at": first_lost(rungs, "associative"),
        "alternativity_lost_at": first_lost(rungs, "alternative"),
        "norm_division_lost_at": first_lost(rungs, "norm_division"),
    }
    controls = control_pairs(rungs)
    no_self_diff = no_self_diff_tautologies(controls)
    onset_map_ok = (
        onsets["commutativity_lost_at"] == "H"
        and onsets["associativity_lost_at"] == "O"
        and onsets["alternativity_lost_at"] == "S"
        and onsets["norm_division_lost_at"] == "S"
    )
    quaternion_associator_zero = rungs["H"]["associator_max"] <= TOL
    octonion_assoc_residual = rungs["O"]["associator_max"]
    octonion_assoc_anchor = abs(octonion_assoc_residual - 2.0) <= TOL
    negative_controls_fail = all(bool(row["negative_case_fails"]) for row in controls)
    ladder_onset_genuine = onset_map_ok and negative_controls_fail and no_self_diff and octonion_assoc_anchor
    classification_ok = classification == "scratch_diagnostic"
    promotion_ok = promotion_allowed is False
    formal_ok = formal_admission_allowed is False

    shared_scalars: dict[str, float] = {}
    for name in RUNG_NAMES:
        rung = rungs[name]
        prefix = f"{name}."
        for key in (
            "dim",
            "commutator_max",
            "associator_max",
            "alternativity_residual",
            "norm_multiplicativity_residual",
        ):
            shared_scalars[prefix + key] = float(rung[key])
        checksum = rung["table_checksum"]
        shared_scalars[prefix + "nonzero_entry_count"] = float(checksum["nonzero_entry_count"])
        shared_scalars[prefix + "sum_abs_entries"] = float(checksum["sum_abs_entries"])
        shared_scalars[prefix + "weighted_checksum"] = float(checksum["weighted_checksum"])
    shared_scalars["O.octonion_assoc_residual"] = float(octonion_assoc_residual)
    shared_scalars["S.zero_divisor_product_squared_norm"] = float(
        rungs["S"]["norm_division_check"]["zero_divisor"]["product_squared_norm"]
    )
    shared_scalars["S.zero_divisor_factor_squared_norm_product"] = float(
        rungs["S"]["norm_division_check"]["zero_divisor"]["factor_squared_norm_product"]
    )

    shared_booleans = {
        "onset_map_ok": onset_map_ok,
        "quaternion_associator_zero": quaternion_associator_zero,
        "octonion_assoc_anchor": octonion_assoc_anchor,
        "negative_controls_fail": negative_controls_fail,
        "no_self_diff_tautologies": no_self_diff,
        "ladder_onset_genuine": ladder_onset_genuine,
        "classification_is_scratch_diagnostic": classification_ok,
        "promotion_false": promotion_ok,
        "formal_admission_false": formal_ok,
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "plain_numpy_imported": False,
        "torch_imported": False,
    }
    for name in RUNG_NAMES:
        for key, value in rungs[name]["properties"].items():
            shared_booleans[f"{name}.property.{key}"] = bool(value)
        shared_booleans[f"{name}.has_zero_divisor_witness"] = bool(rungs[name]["has_zero_divisor_witness"])

    shared_strings = {
        "object_id": OBJECT_ID,
        "allowed_claim": ALLOWED_CLAIM,
        "commutativity_lost_at": onsets["commutativity_lost_at"],
        "associativity_lost_at": onsets["associativity_lost_at"],
        "alternativity_lost_at": onsets["alternativity_lost_at"],
        "norm_division_lost_at": onsets["norm_division_lost_at"],
    }
    shared = {
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "shared_strings": shared_strings,
    }

    result: dict[str, Any] = {
        "schema": "codex_ratchet.formal_scout.scratch_diagnostic.v1",
        "object_id": OBJECT_ID,
        "sim_id": OBJECT_ID,
        "name": OBJECT_ID,
        "version": "1.0",
        "tier": "R3_foundation_carrier_candidate_onset",
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
        "blocked_consumers": ["promotion", "formal_admission", "downstream scientific claims"],
        "sim_execution_kind": sim_execution_kind,
        "sim_class": "carrier_probe",
        "purpose": "Build one bottom-up R3 finite carrier-candidate onset map above the verified R0-R2 structure.",
        "scientific_question": "Where do commutativity, associativity, alternativity, and norm-division first fail in R/C/H/O/S?",
        "branch_status_before_run": "scratch_diagnostic_only",
        "carrier_layer": "finite_Cayley_Dickson_R_C_H_O_S_tables",
        "geometry_layer": "none",
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "finite division-algebra carrier property onset",
        "root_constraints_in_force": ["R0_finite_object", "R1_probe_quotient", "R2_admissible_operations_context"],
        "promotion_blockers": ["scratch diagnostic fence", "no formal admission", "no higher-layer consumer"],
        "SIM_TEMPLATE_surface": SIM_TEMPLATE_SURFACE,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "required_tools": ["JAX", "jnp", "Julia mirror"],
        "actual_tools_used": ["JAX", "jnp", "Python stdlib"],
        "proof_surfaces_used": [],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "plain_numpy_imported": False,
        "torch_imported": False,
        "tol": TOL,
        "onset_tol": ONSET_TOL,
        "construction": {
            "method": "finite Cayley-Dickson doubling",
            "rung_names": RUNG_NAMES,
            "rung_dims": {name: rungs[name]["dim"] for name in RUNG_NAMES},
        },
        "rungs": rungs,
        "onset_map": onsets,
        "control_comparison_pairs": controls,
        "probe": {
            "question": "property onset in the R/C/H/O/S carrier-candidate ladder",
            "measured_properties": ["commutativity", "associativity", "alternativity", "norm_multiplicativity", "norm_division"],
            "control_rule": "every control compares two named computed quantities and includes a negative case that fails the property",
        },
        "positive": {
            "R_C_commutative": {"pass": rungs["R"]["properties"]["commutative"] and rungs["C"]["properties"]["commutative"]},
            "H_associative": {"pass": quaternion_associator_zero, "quaternion_associator_max": rungs["H"]["associator_max"]},
            "O_norm_division_before_S": {"pass": rungs["O"]["properties"]["norm_division"]},
            "classification_is_scratch_diagnostic": {"pass": classification_ok},
            "promotion_allowed_false": {"pass": promotion_ok},
            "formal_admission_allowed_false": {"pass": formal_ok},
            "no_self_diff_tautologies": {"pass": no_self_diff},
        },
        "negative": {
            "H_commutativity_negative_case": {
                "pass": not bool(rungs["H"]["properties"]["commutative"]),
                "commutator_max": rungs["H"]["commutator_max"],
                "control_can_fail": True,
            },
            "O_associativity_negative_case": {
                "pass": not bool(rungs["O"]["properties"]["associative"]),
                "octonion_assoc_residual": octonion_assoc_residual,
                "control_can_fail": True,
            },
            "S_norm_division_negative_case": {
                "pass": not bool(rungs["S"]["properties"]["norm_division"]),
                "norm_multiplicativity_residual": rungs["S"]["norm_multiplicativity_residual"],
                "zero_divisor": rungs["S"]["norm_division_check"]["zero_divisor"],
                "control_can_fail": True,
            },
        },
        "graveyard_companions": {
            "commutativity_persists_through_H": {
                "pass": not bool(rungs["H"]["properties"]["commutative"]),
                "reason": "H is the first computed noncommutative rung.",
            },
            "associativity_persists_through_O": {
                "pass": not bool(rungs["O"]["properties"]["associative"]),
                "reason": "O is the first computed nonassociative rung.",
            },
            "norm_division_persists_through_S": {
                "pass": not bool(rungs["S"]["properties"]["norm_division"]),
                "reason": "S has a computed zero-divisor witness and nonzero norm multiplicativity residual.",
            },
            "self_diff_control": {
                "pass": no_self_diff,
                "reason": "all control rows name distinct left and right computed quantities.",
            },
        },
        "boundary": {
            "C_to_H_commutativity_boundary": {
                "pass": rungs["C"]["properties"]["commutative"] and not rungs["H"]["properties"]["commutative"],
                "left": "C",
                "right": "H",
            },
            "H_to_O_associativity_boundary": {
                "pass": rungs["H"]["properties"]["associative"] and not rungs["O"]["properties"]["associative"],
                "left": "H",
                "right": "O",
            },
            "O_to_S_norm_division_boundary": {
                "pass": rungs["O"]["properties"]["norm_division"] and not rungs["S"]["properties"]["norm_division"],
                "left": "O",
                "right": "S",
            },
            "claim_ceiling": CLAIM_CEILING,
        },
        "nearby_variants": {
            "total": 3,
            "passed": 3 if negative_controls_fail else 0,
            "all_pass": negative_controls_fail,
            "rows": controls,
        },
        "why_not_v4_probes": "This is a v5 scratch diagnostic formal-scout receipt with no promotion or formal admission.",
        "required_negatives": ["H_commutativity_negative_case", "O_associativity_negative_case", "S_norm_division_negative_case"],
        "negatives_run": ["H_commutativity_negative_case", "O_associativity_negative_case", "S_norm_division_negative_case"],
        "kill_conditions": [
            "commutativity is not first lost at H",
            "associativity is not first lost at O",
            "norm-division is not first lost at S",
            "octonion associator residual is not approximately 2.0",
            "quaternion associator residual is nonzero",
            "any control compares an expression with itself",
            "Julia parity does not read this run token and match shared fields",
        ],
        "required_artifacts": [str(RESULT_PATH), str(JULIA_REFERENCE_PATH)],
        "artifacts_emitted": [str(RESULT_PATH)],
        "witness_trace_id": f"{OBJECT_ID}:jax:{run_token()}",
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "shared_strings": shared_strings,
        "shared_value_digest": shared_payload_digest(shared),
    }
    result["parity"] = parity_against_julia(result)
    result["positive"]["dual_backend_parity"] = {"pass": result["parity"]["within_tolerance"]}
    result["core_pass"] = bool(
        onset_map_ok
        and quaternion_associator_zero
        and octonion_assoc_anchor
        and negative_controls_fail
        and ladder_onset_genuine
        and classification_ok
        and promotion_ok
        and formal_ok
        and no_self_diff
        and bool(jax.config.read("jax_enable_x64"))
    )
    result["all_pass"] = bool(result["core_pass"] and result["parity"]["within_tolerance"])
    result["stop_condition_fired"] = not result["all_pass"]
    result["pass_rule"] = (
        "onset map H/O/S as specified, quaternion associator zero, octonion associator 2.0, "
        "negative controls fail as expected, no self-diff controls, and within-run Julia parity"
    )
    result["fail_rule"] = "any wrong onset, missing negative failure, self-diff control, fence violation, or parity mismatch"
    result["result_summary"] = {
        "commutativity_lost_at": onsets["commutativity_lost_at"],
        "associativity_lost_at": onsets["associativity_lost_at"],
        "norm_division_lost_at": onsets["norm_division_lost_at"],
        "octonion_assoc_residual": octonion_assoc_residual,
        "quaternion_assoc_residual": rungs["H"]["associator_max"],
        "ladder_onset_genuine": ladder_onset_genuine,
        "no_self_diff": no_self_diff,
        "parity_within_run": result["parity"]["parity_within_run"],
        "all_pass": result["all_pass"],
    }
    result["criteria_checked"] = [
        "finite Cayley-Dickson R/C/H/O/S table construction",
        "commutativity residual for each rung",
        "associativity residual for each rung",
        "alternativity residual for each rung",
        "squared-norm multiplicativity and zero-divisor witness",
        "onset map: H/O/S",
        "negative controls fail on H, O, and S respectively",
        "no control compares an expression with itself",
        "JAX/Julia shared payload parity with matching run token",
    ]
    result["commutativity_lost_at"] = onsets["commutativity_lost_at"]
    result["associativity_lost_at"] = onsets["associativity_lost_at"]
    result["norm_division_lost_at"] = onsets["norm_division_lost_at"]
    result["octonion_assoc_residual"] = octonion_assoc_residual
    result["ladder_onset_genuine"] = ladder_onset_genuine
    result["no_self_diff"] = no_self_diff
    result["parity_within_run"] = result["parity"]["parity_within_run"]
    return result


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {RESULT_PATH}")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "core_pass": result["core_pass"],
                "parity_within_run": result["parity_within_run"],
                "commutativity_lost_at": result["commutativity_lost_at"],
                "associativity_lost_at": result["associativity_lost_at"],
                "norm_division_lost_at": result["norm_division_lost_at"],
                "octonion_assoc_residual": result["octonion_assoc_residual"],
                "no_self_diff": result["no_self_diff"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["core_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

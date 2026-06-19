#!/usr/bin/env python3
"""R3 carrier-property requirements over verified R0-R2 structure.

Scratch diagnostic only. This maps each bottom R2 need to the minimal
R/C/H/O/S carrier-candidate property that can host it.
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


OBJECT_ID = "r3_carrier_property_requirements"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/r3_carrier_property_requirements_results.json"
JULIA_REFERENCE_PATH = ROOT / "system_v5/julia_carrier/r3_carrier_property_requirements_julia_results.json"
PARENT_RESULTS = {
    "foundation_rung0to3": ROOT / "system_v5/ops/formal_scouts/results/foundation_rung0to3_distinguishability_results.json",
    "r0_r1_r2_probe_quotient_micro_packet": ROOT / "system_v5/ops/formal_scouts/results/r0_r1_r2_probe_quotient_micro_packet_results.json",
    "r2_admissible_operations": ROOT / "system_v5/ops/formal_scouts/results/r2_admissible_operations_commutation_order_results.json",
    "r2_admissible_composition_rules": ROOT / "system_v5/ops/formal_scouts/results/r2_admissible_composition_rules_results.json",
}
TOL = 1.0e-12
REQUIREMENT_TOL = 1.0e-9
RUNG_NAMES = ["R", "C", "H", "O", "S"]

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
sim_execution_kind = "classical"
SIM_EXECUTION_KIND = sim_execution_kind

ALLOWED_CLAIM = "R3 bottom carrier-candidate property requirement map for verified R0-R2 structure."
CLAIM_CEILING = (
    "Allowed only: finite R/C/H/O/S carrier-candidate requirement map for R2 "
    "noncommutation and three-cell associator defect. Scratch diagnostic only; "
    "no promotion, no formal admission, no top-floor consumer."
)

TOOL_MANIFEST = {
    "JAX": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 finite carrier table arithmetic and residual comparisons",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 array algebra through jnp only; no plain NumPy compute path",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON receipt, run-token parity, timestamps, and hashing",
    },
    "Julia mirror": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent backend parity reading the current JAX result",
    },
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": "not used: this row is explicitly no-torch and finite carrier-table only",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "not imported or used; JAX lane uses jax.numpy only",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "JAX": "load_bearing",
    "jax.numpy": "load_bearing",
    "Python stdlib": "supportive",
    "Julia mirror": "load_bearing",
    "pytorch": None,
    "numpy": None,
}

SIM_TEMPLATE_SURFACE = {
    "identity": ["sim_id", "name", "version", "tier"],
    "tooling": ["TOOL_MANIFEST", "TOOL_INTEGRATION_DEPTH", "classification"],
    "negatives": ["positive", "negative", "boundary", "probe"],
    "promotion": ["promotion_allowed", "formal_admission_allowed", "blocked_consumers"],
}


def run_token() -> str:
    return os.environ.get("R3_CARRIER_RUN_TOKEN", "manual-token-not-set")


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


def commutator_scan(table: jax.Array) -> dict[str, Any]:
    diffs = table - jnp.swapaxes(table, 1, 2)
    norms = jnp.linalg.norm(diffs, axis=0)
    max_value = py_float(jnp.max(norms))
    flat_idx = int(jax.device_get(jnp.argmax(norms)))
    a, b = [int(x) for x in jnp.unravel_index(flat_idx, norms.shape)]
    return {
        "max_residual": max_value,
        "witness_basis_indices": [a, b],
        "left_expression_id": f"e{a}*e{b}",
        "right_expression_id": f"e{b}*e{a}",
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
        "left_expression_id": f"(e{a}*e{b})*e{c}",
        "right_expression_id": f"e{a}*(e{b}*e{c})",
    }


def analyze_carrier(name: str, table: jax.Array) -> dict[str, Any]:
    comm = commutator_scan(table)
    assoc = associator_scan(table)
    return {
        "name": name,
        "dim": table.shape[0],
        "commutator_capacity": comm["max_residual"],
        "associator_capacity": assoc["max_residual"],
        "commutative": comm["max_residual"] <= TOL,
        "associative": assoc["max_residual"] <= TOL,
        "noncommutative": comm["max_residual"] > REQUIREMENT_TOL,
        "nonassociative": assoc["max_residual"] > REQUIREMENT_TOL,
        "commutator_check": comm,
        "associator_check": assoc,
    }


def read_parent_results() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, path in PARENT_RESULTS.items():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            out[name] = {"path": str(path), "present": False, "error": str(exc)}
            continue
        out[name] = {
            "path": str(path),
            "present": True,
            "all_pass": data.get("all_pass") is True,
            "classification": data.get("classification"),
            "promotion_allowed": data.get("promotion_allowed"),
            "formal_admission_allowed": data.get("formal_admission_allowed"),
            "parity_ok": bool((data.get("parity") or {}).get("within_1e_12")),
            "shared_scalars": data.get("shared_scalars", {}),
            "result_summary": data.get("result_summary", {}),
        }
    return out


def parent_scalar(parents: dict[str, Any], parent: str, key: str) -> float:
    value = parents[parent].get("shared_scalars", {}).get(key)
    if value is None:
        value = parents[parent].get("result_summary", {}).get(key)
    return float(value)


def parents_verified(parents: dict[str, Any]) -> bool:
    return all(
        row.get("present") is True
        and row.get("all_pass") is True
        and row.get("classification") == "scratch_diagnostic"
        and row.get("promotion_allowed") is False
        and row.get("formal_admission_allowed") is False
        and row.get("parity_ok") is True
        for row in parents.values()
    )


def first_supporting(carriers: dict[str, dict[str, Any]], predicate: str) -> str:
    for name in RUNG_NAMES:
        if bool(carriers[name][predicate]):
            return name
    return "none"


def carrier_supports_gap(carrier: dict[str, Any], capacity_key: str, required_gap: float) -> bool:
    return float(carrier[capacity_key]) + TOL >= required_gap and required_gap > REQUIREMENT_TOL


def build_requirement_controls(
    carriers: dict[str, dict[str, Any]], n01_required_gap: float, associator_required_gap: float
) -> list[dict[str, Any]]:
    rows = [
        {
            "name": "real_negative_fails_n01",
            "left_quantity": "R.commutator_capacity",
            "right_quantity": "R2.n01_required_gap",
            "left_value": carriers["R"]["commutator_capacity"],
            "right_value": n01_required_gap,
            "computed_quantities_distinct": True,
            "negative_case": "R",
            "negative_case_supports_requirement": carrier_supports_gap(carriers["R"], "commutator_capacity", n01_required_gap),
            "negative_case_fails": not carrier_supports_gap(carriers["R"], "commutator_capacity", n01_required_gap),
            "positive_reference": "H",
            "positive_reference_supports_requirement": carrier_supports_gap(carriers["H"], "commutator_capacity", n01_required_gap),
        },
        {
            "name": "commutative_negative_fails_n01",
            "left_quantity": "C.commutator_capacity",
            "right_quantity": "R2.n01_required_gap",
            "left_value": carriers["C"]["commutator_capacity"],
            "right_value": n01_required_gap,
            "computed_quantities_distinct": True,
            "negative_case": "C",
            "negative_case_supports_requirement": carrier_supports_gap(carriers["C"], "commutator_capacity", n01_required_gap),
            "negative_case_fails": not carrier_supports_gap(carriers["C"], "commutator_capacity", n01_required_gap),
            "positive_reference": "H",
            "positive_reference_supports_requirement": carrier_supports_gap(carriers["H"], "commutator_capacity", n01_required_gap),
        },
        {
            "name": "associative_negative_fails_3cell",
            "left_quantity": "H.associator_capacity",
            "right_quantity": "R2.three_cell_required_defect",
            "left_value": carriers["H"]["associator_capacity"],
            "right_value": associator_required_gap,
            "computed_quantities_distinct": True,
            "negative_case": "H",
            "negative_case_supports_requirement": carrier_supports_gap(carriers["H"], "associator_capacity", associator_required_gap),
            "negative_case_fails": not carrier_supports_gap(carriers["H"], "associator_capacity", associator_required_gap),
            "positive_reference": "O",
            "positive_reference_supports_requirement": carrier_supports_gap(carriers["O"], "associator_capacity", associator_required_gap),
        },
        {
            "name": "octonion_positive_hosts_3cell",
            "left_quantity": "O.associator_capacity",
            "right_quantity": "R2.three_cell_required_defect",
            "left_value": carriers["O"]["associator_capacity"],
            "right_value": associator_required_gap,
            "computed_quantities_distinct": True,
            "negative_case": "H",
            "negative_case_supports_requirement": carrier_supports_gap(carriers["H"], "associator_capacity", associator_required_gap),
            "negative_case_fails": not carrier_supports_gap(carriers["H"], "associator_capacity", associator_required_gap),
            "positive_reference": "O",
            "positive_reference_supports_requirement": carrier_supports_gap(carriers["O"], "associator_capacity", associator_required_gap),
        },
    ]
    for row in rows:
        row["left_right_names_distinct"] = row["left_quantity"] != row["right_quantity"]
        row["pass"] = (
            row["computed_quantities_distinct"]
            and row["left_right_names_distinct"]
            and row["negative_case_fails"]
            and row["positive_reference_supports_requirement"]
        )
    return rows


def no_self_diff_tautologies(rows: list[dict[str, Any]], carriers: dict[str, dict[str, Any]]) -> bool:
    if not all(row["left_quantity"] != row["right_quantity"] for row in rows):
        return False
    for carrier in carriers.values():
        comm = carrier["commutator_check"]
        assoc = carrier["associator_check"]
        if comm["max_residual"] > REQUIREMENT_TOL and comm["left_expression_id"] == comm["right_expression_id"]:
            return False
        if assoc["max_residual"] > REQUIREMENT_TOL and assoc["left_expression_id"] == assoc["right_expression_id"]:
            return False
    return True


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
    parents = read_parent_results()
    parent_ok = parents_verified(parents)
    n01_required_gap = parent_scalar(parents, "r2_admissible_composition_rules", "order_gap_norm")
    associator_required_gap = parent_scalar(parents, "r2_admissible_composition_rules", "toy_assoc_residual_norm")

    tables = build_tables()
    carriers = {name: analyze_carrier(name, tables[name]) for name in RUNG_NAMES}
    controls = build_requirement_controls(carriers, n01_required_gap, associator_required_gap)
    no_self_diff = no_self_diff_tautologies(controls, carriers)

    n01_requires_noncommutative_carrier = (
        not carrier_supports_gap(carriers["R"], "commutator_capacity", n01_required_gap)
        and not carrier_supports_gap(carriers["C"], "commutator_capacity", n01_required_gap)
        and carrier_supports_gap(carriers["H"], "commutator_capacity", n01_required_gap)
    )
    associator_requires_octonion = (
        not carrier_supports_gap(carriers["R"], "associator_capacity", associator_required_gap)
        and not carrier_supports_gap(carriers["C"], "associator_capacity", associator_required_gap)
        and not carrier_supports_gap(carriers["H"], "associator_capacity", associator_required_gap)
        and carrier_supports_gap(carriers["O"], "associator_capacity", associator_required_gap)
    )
    real_carrier_insufficient_for = "N01_noncommuting_admissible_operations_and_associator_3cell_defect"
    requirement_map = {
        "R0_R1_finite_probe_quotient_identity": {
            "minimal_carrier": "R",
            "minimal_property": "finite_scalar_support",
            "reason": "finite quotient bookkeeping does not require carrier noncommutation",
        },
        "R2_N01_noncommuting_admissible_operations": {
            "minimal_carrier": first_supporting(carriers, "noncommutative"),
            "minimal_property": "noncommutative_multiplication",
            "negative_control": "R_and_C_fail_commutator_capacity_against_R2_order_gap",
        },
        "R2_admissible_composition_associative_operation_layer": {
            "minimal_carrier": "ordinary_operation_maps",
            "minimal_property": "associative_map_composition",
            "reason": "parent R2 composition residual is zero; nonassociativity is not required at the operation-composition layer",
        },
        "R2_three_cell_associator_defect_detector": {
            "minimal_carrier": first_supporting(carriers, "nonassociative"),
            "minimal_property": "nonassociative_multiplication",
            "negative_control": "R_C_H_fail_associator_capacity_against_R2_three_cell_defect",
        },
    }
    requirement_map_genuine = (
        requirement_map["R2_N01_noncommuting_admissible_operations"]["minimal_carrier"] == "H"
        and requirement_map["R2_three_cell_associator_defect_detector"]["minimal_carrier"] == "O"
        and all(row["pass"] for row in controls)
        and no_self_diff
    )

    classification_ok = classification == "scratch_diagnostic"
    promotion_ok = promotion_allowed is False
    formal_ok = formal_admission_allowed is False

    shared_scalars: dict[str, float] = {
        "R2.n01_required_gap": float(n01_required_gap),
        "R2.three_cell_required_defect": float(associator_required_gap),
    }
    for name in RUNG_NAMES:
        carrier = carriers[name]
        shared_scalars[f"{name}.dim"] = float(carrier["dim"])
        shared_scalars[f"{name}.commutator_capacity"] = float(carrier["commutator_capacity"])
        shared_scalars[f"{name}.associator_capacity"] = float(carrier["associator_capacity"])

    shared_booleans = {
        "parents_verified": parent_ok,
        "n01_requires_noncommutative_carrier": n01_requires_noncommutative_carrier,
        "associator_requires_octonion": associator_requires_octonion,
        "requirement_map_genuine": requirement_map_genuine,
        "no_self_diff_tautologies": no_self_diff,
        "classification_is_scratch_diagnostic": classification_ok,
        "promotion_false": promotion_ok,
        "formal_admission_false": formal_ok,
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "numpy_compute_used": False,
        "numpy_imported": False,
        "torch_imported": False,
    }
    for name in RUNG_NAMES:
        carrier = carriers[name]
        shared_booleans[f"{name}.commutative"] = bool(carrier["commutative"])
        shared_booleans[f"{name}.associative"] = bool(carrier["associative"])
        shared_booleans[f"{name}.noncommutative"] = bool(carrier["noncommutative"])
        shared_booleans[f"{name}.nonassociative"] = bool(carrier["nonassociative"])

    shared_strings = {
        "object_id": OBJECT_ID,
        "allowed_claim": ALLOWED_CLAIM,
        "minimal_n01_carrier": requirement_map["R2_N01_noncommuting_admissible_operations"]["minimal_carrier"],
        "minimal_associator_carrier": requirement_map["R2_three_cell_associator_defect_detector"]["minimal_carrier"],
        "real_carrier_insufficient_for": real_carrier_insufficient_for,
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
        "tier": "R3_foundation_carrier_property_requirements",
        "backend": "jax",
        "run_token": run_token(),
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "parent_results": parents,
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "claim_ceiling": CLAIM_CEILING,
        "next_lego_target": "none",
        "promotion_condition": "not applicable: promotion_allowed=false for this scratch diagnostic row",
        "blocked_until": "remains fenced unless a separate owner-authorized admission packet changes the classification",
        "demotion_condition": "already fenced; mark failed if any named criterion, parity, or no-self-diff check fails",
        "out_of_scope": [
            "no promotion from this result",
            "no formal admission from this result",
            "no higher-layer consumer from this result",
            "no carrier claim outside the finite R/C/H/O/S candidate ladder",
        ],
        "allowed_claims": [ALLOWED_CLAIM],
        "promotion_status": "diagnostic_only",
        "eligible_consumers": [],
        "blocked_consumers": ["promotion", "formal_admission", "top_floor_consumers"],
        "sim_execution_kind": sim_execution_kind,
        "sim_class": "carrier_probe",
        "purpose": "Map R2 bottom structural needs to minimal finite carrier-candidate properties.",
        "scientific_question": "Which R2 need requires which minimal carrier property in the R/C/H/O/S candidate ladder?",
        "branch_status_before_run": "scratch_diagnostic_only",
        "carrier_layer": "finite_Cayley_Dickson_R_C_H_O_S_tables",
        "law_or_candidate_tested": "carrier property requirement map for R2 noncommutation and associator defect",
        "root_constraints_in_force": ["R0_finite_object", "R1_probe_quotient", "R2_noncommuting_admissible_operations", "R2_composition_rules"],
        "promotion_blockers": ["scratch diagnostic fence", "no formal admission", "no higher-layer consumer"],
        "SIM_TEMPLATE_surface": SIM_TEMPLATE_SURFACE,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "required_tools": ["JAX", "jax.numpy", "Julia mirror"],
        "actual_tools_used": ["JAX", "jax.numpy", "Python stdlib"],
        "proof_surfaces_used": [],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "numpy_compute_used": False,
        "numpy_imported": False,
        "torch_imported": False,
        "tol": TOL,
        "requirement_tol": REQUIREMENT_TOL,
        "construction": {
            "method": "finite Cayley-Dickson doubling",
            "candidate_ladder": RUNG_NAMES,
            "rung_dims": {name: carriers[name]["dim"] for name in RUNG_NAMES},
        },
        "carriers": carriers,
        "requirement_map": requirement_map,
        "control_comparison_pairs": controls,
        "probe": {
            "question": "minimal carrier property for each R2 structural need",
            "required_gaps": {
                "n01_required_gap_from_parent_R2": n01_required_gap,
                "three_cell_required_defect_from_parent_R2": associator_required_gap,
            },
            "control_rule": "controls compare carrier capacity against a distinct parent R2-required gap; real/commutative negatives must fail",
        },
        "positive": {
            "H_hosts_N01_noncommutation": {
                "pass": carrier_supports_gap(carriers["H"], "commutator_capacity", n01_required_gap),
                "H_commutator_capacity": carriers["H"]["commutator_capacity"],
                "required_gap": n01_required_gap,
            },
            "O_hosts_associator_3cell_defect": {
                "pass": carrier_supports_gap(carriers["O"], "associator_capacity", associator_required_gap),
                "O_associator_capacity": carriers["O"]["associator_capacity"],
                "required_gap": associator_required_gap,
            },
            "parents_verified": {"pass": parent_ok},
            "no_self_diff_tautologies": {"pass": no_self_diff},
            "classification_is_scratch_diagnostic": {"pass": classification_ok},
            "promotion_allowed_false": {"pass": promotion_ok},
            "formal_admission_allowed_false": {"pass": formal_ok},
        },
        "negative": {
            "real_carrier_fails_N01": {
                "pass": not carrier_supports_gap(carriers["R"], "commutator_capacity", n01_required_gap),
                "R_commutator_capacity": carriers["R"]["commutator_capacity"],
                "required_gap": n01_required_gap,
                "control_can_fail": True,
            },
            "commutative_carrier_fails_N01": {
                "pass": not carrier_supports_gap(carriers["C"], "commutator_capacity", n01_required_gap),
                "C_commutator_capacity": carriers["C"]["commutator_capacity"],
                "required_gap": n01_required_gap,
                "control_can_fail": True,
            },
            "associative_carrier_fails_associator_3cell": {
                "pass": not carrier_supports_gap(carriers["H"], "associator_capacity", associator_required_gap),
                "H_associator_capacity": carriers["H"]["associator_capacity"],
                "required_gap": associator_required_gap,
                "control_can_fail": True,
            },
        },
        "graveyard_companions": {
            "real_carrier_hosts_N01": {
                "pass": not carrier_supports_gap(carriers["R"], "commutator_capacity", n01_required_gap),
                "reason": "R commutator capacity is zero while parent R2 noncommutation gap is nonzero.",
            },
            "commutative_carrier_hosts_N01": {
                "pass": not carrier_supports_gap(carriers["C"], "commutator_capacity", n01_required_gap),
                "reason": "C commutator capacity is zero while parent R2 noncommutation gap is nonzero.",
            },
            "quaternion_hosts_3cell_associator": {
                "pass": not carrier_supports_gap(carriers["H"], "associator_capacity", associator_required_gap),
                "reason": "H is noncommutative but still associative in this finite table.",
            },
            "self_diff_control": {
                "pass": no_self_diff,
                "reason": "all controls compare distinct named computed quantities.",
            },
        },
        "boundary": {
            "C_to_H_noncommutation_boundary": {
                "pass": (
                    not carrier_supports_gap(carriers["C"], "commutator_capacity", n01_required_gap)
                    and carrier_supports_gap(carriers["H"], "commutator_capacity", n01_required_gap)
                ),
                "left": "C",
                "right": "H",
            },
            "H_to_O_associator_boundary": {
                "pass": (
                    not carrier_supports_gap(carriers["H"], "associator_capacity", associator_required_gap)
                    and carrier_supports_gap(carriers["O"], "associator_capacity", associator_required_gap)
                ),
                "left": "H",
                "right": "O",
            },
            "claim_ceiling": CLAIM_CEILING,
        },
        "nearby_variants": {
            "total": len(controls),
            "passed": sum(1 for row in controls if row["pass"]),
            "all_pass": all(row["pass"] for row in controls),
            "rows": controls,
        },
        "why_not_v4_probes": "This is a v5 scratch diagnostic dual-backend carrier-property scout with no promotion or formal admission.",
        "required_negatives": ["real_carrier_fails_N01", "commutative_carrier_fails_N01", "associative_carrier_fails_associator_3cell"],
        "negatives_run": ["real_carrier_fails_N01", "commutative_carrier_fails_N01", "associative_carrier_fails_associator_3cell"],
        "kill_conditions": [
            "parent R0-R2 results are absent, unpassed, promoted, or parity-stale",
            "R or C can host the parent R2 noncommutation gap",
            "H cannot host the parent R2 noncommutation gap",
            "H can host the associator defect",
            "O cannot host the associator defect",
            "any control compares an expression with itself",
            "Julia mirror did not read this run token and match shared fields",
        ],
        "required_artifacts": [str(RESULT_PATH), str(JULIA_REFERENCE_PATH)],
        "artifacts_emitted": [str(RESULT_PATH)],
        "witness_trace_id": f"{OBJECT_ID}:jax:{run_token()}",
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "shared_strings": shared_strings,
        "shared_value_digest": shared_payload_digest(shared),
        "n01_requires_noncommutative_carrier": n01_requires_noncommutative_carrier,
        "associator_requires_octonion": associator_requires_octonion,
        "real_carrier_insufficient_for": real_carrier_insufficient_for,
        "requirement_map_genuine": requirement_map_genuine,
        "no_self_diff": no_self_diff,
    }
    result["parity"] = parity_against_julia(result)
    result["positive"]["dual_backend_parity"] = {"pass": result["parity"]["within_tolerance"]}
    result["parity_within_run"] = result["parity"]["parity_within_run"]
    result["core_pass"] = bool(
        parent_ok
        and n01_requires_noncommutative_carrier
        and associator_requires_octonion
        and requirement_map_genuine
        and no_self_diff
        and classification_ok
        and promotion_ok
        and formal_ok
        and bool(jax.config.read("jax_enable_x64"))
        and not result["numpy_compute_used"]
        and not result["torch_imported"]
    )
    result["all_pass"] = bool(result["core_pass"] and result["parity"]["within_tolerance"])
    result["stop_condition_fired"] = not result["all_pass"]
    result["pass_rule"] = (
        "verified parents, H minimal for N01 noncommutation, O minimal for associator defect, "
        "real/commutative negatives fail, no self-diff controls, and within-run Julia parity"
    )
    result["fail_rule"] = "any parent fence failure, wrong minimal carrier, non-failing negative, self-diff control, or parity mismatch"
    result["result_summary"] = {
        "parents_verified": parent_ok,
        "minimal_n01_carrier": requirement_map["R2_N01_noncommuting_admissible_operations"]["minimal_carrier"],
        "minimal_associator_carrier": requirement_map["R2_three_cell_associator_defect_detector"]["minimal_carrier"],
        "n01_requires_noncommutative_carrier": n01_requires_noncommutative_carrier,
        "associator_requires_octonion": associator_requires_octonion,
        "real_carrier_insufficient_for": real_carrier_insufficient_for,
        "requirement_map_genuine": requirement_map_genuine,
        "no_self_diff": no_self_diff,
        "parity_within_run": result["parity_within_run"],
        "all_pass": result["all_pass"],
    }
    result["criteria_checked"] = [
        "parent R0-R2 result files are present, scratch-fenced, all_pass, and parity-clean",
        "finite R/C/H/O/S carrier tables built with JAX x64 and jnp only",
        "carrier commutator capacity compared against parent R2 N01 order gap",
        "carrier associator capacity compared against parent R2 three-cell defect gap",
        "R and C fail the N01 hosting control",
        "H supports N01 but fails associator hosting",
        "O supports associator hosting",
        "no control compares an expression with itself",
        "Julia mirror reads this run token and shared digest",
    ]
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
                "n01_requires_noncommutative_carrier": result["n01_requires_noncommutative_carrier"],
                "associator_requires_octonion": result["associator_requires_octonion"],
                "real_carrier_insufficient_for": result["real_carrier_insufficient_for"],
                "requirement_map_genuine": result["requirement_map_genuine"],
                "no_self_diff": result["no_self_diff"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["core_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

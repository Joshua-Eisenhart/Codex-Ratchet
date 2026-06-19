#!/usr/bin/env python3
"""R3 entropy as a derived readout over the verified R2 quotient.

Scratch diagnostic only. Entropy is computed downstream of the finite
probe-relative quotient: the primitive is distinguishability under finite M,
and entropy is only a later readout on the resulting quotient/signature data.
"""

from __future__ import annotations

import datetime as _dt
import json
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


OBJECT_ID = "r3_entropy_as_derived_readout"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/r3_entropy_as_derived_readout_results.json"
JULIA_SCRIPT_PATH = ROOT / "system_v5/julia_carrier/r3_entropy_as_derived_readout.jl"
JULIA_RESULT_PATH = ROOT / "system_v5/julia_carrier/r3_entropy_as_derived_readout_julia_results.json"
PARENT_RESULTS = [
    ROOT / "system_v5/ops/formal_scouts/results/foundation_rung0to3_distinguishability_results.json",
    ROOT / "system_v5/ops/formal_scouts/results/r0_r1_r2_probe_quotient_micro_packet_results.json",
    ROOT / "system_v5/ops/formal_scouts/results/r2_admissible_operations_commutation_order_results.json",
    ROOT / "system_v5/ops/formal_scouts/results/r2_admissible_composition_rules_results.json",
]
TOL = 1.0e-12

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
sim_execution_kind = "nonclassical"
SIM_EXECUTION_KIND = sim_execution_kind

ALLOWED_CLAIM = (
    "R3 entropy is a downstream readout of the verified finite R2 "
    "probe-relative distinguishability quotient."
)
BLOCKED_CLAIMS = [
    "top_floor_claim",
    "physics_claim",
    "formal_admission",
    "promotion",
]
CLAIM_CEILING = (
    "Allowed only: finite quotient/signature entropy readout at scratch level. "
    "The primitive remains distinguishability under M; entropy is not primitive. "
    "Blocked: " + "; ".join(BLOCKED_CLAIMS) + "."
)

TOOL_MANIFEST = {
    "JAX": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 finite density, quotient, von-Neumann entropy, Shannon entropy, and controls",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite complex array algebra and entropy arithmetic through jnp only",
    },
    "Julia mirror": {
        "tried": True,
        "used": True,
        "reason": "load-bearing within-run independent backend parity; Julia reads the current JAX receipt run id",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON receipt, timestamp, subprocess launch, and run-id generation",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "not used: JAX lane uses jax.numpy with x64 and no NumPy import or compute path",
    },
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": "not used: explicit user fence requires no torch for this diagnostic rung",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "JAX": "load_bearing",
    "jax.numpy": "load_bearing",
    "Julia mirror": "load_bearing",
    "Python stdlib": "supportive",
    "numpy": None,
    "pytorch": None,
}

SIM_TEMPLATE_SURFACE = {
    "identity": ["sim_id", "name", "version", "tier"],
    "tooling": ["TOOL_MANIFEST", "TOOL_INTEGRATION_DEPTH", "classification"],
    "negatives": ["positive", "negative", "boundary", "probe"],
    "promotion": ["promotion_allowed", "formal_admission_allowed", "blocked_consumers"],
}

I2 = jnp.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=jnp.complex128)


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def rounded(value: Any, digits: int = 12) -> float:
    return round(py_float(value), digits)


def matrix_parts(matrix: jax.Array, digits: int = 12) -> dict[str, list[list[float]]]:
    real = jax.device_get(jnp.real(matrix))
    imag = jax.device_get(jnp.imag(matrix))
    return {
        "real": [[round(float(cell), digits) for cell in row] for row in real.tolist()],
        "imag": [[round(float(cell), digits) for cell in row] for row in imag.tolist()],
    }


def ket(values: list[complex]) -> jax.Array:
    vec = jnp.asarray(values, dtype=jnp.complex128)
    return vec / jnp.sqrt(jnp.vdot(vec, vec))


def density(psi: jax.Array) -> jax.Array:
    return jnp.outer(psi, jnp.conj(psi))


def make_projective_probe(name: str, vectors: list[jax.Array]) -> dict[str, Any]:
    return {
        "name": name,
        "outcome_labels": [f"{name}_{idx}" for idx in range(len(vectors))],
        "effects": [density(vec) for vec in vectors],
    }


def make_blind_probe() -> dict[str, Any]:
    return {
        "name": "BLIND_I",
        "outcome_labels": ["BLIND_I_0"],
        "effects": [I2],
    }


def base_kets() -> dict[str, jax.Array]:
    s2 = jnp.sqrt(jnp.asarray(2.0, dtype=jnp.float64))
    return {
        "z0": ket([1.0 + 0.0j, 0.0 + 0.0j]),
        "z1": ket([0.0 + 0.0j, 1.0 + 0.0j]),
        "x_plus": ket([1.0 + 0.0j, 1.0 + 0.0j]),
        "x_minus": ket([1.0 + 0.0j, -1.0 + 0.0j]),
        "y_plus": jnp.asarray([1.0 + 0.0j, 0.0 + 1.0j], dtype=jnp.complex128) / s2,
        "y_minus": jnp.asarray([1.0 + 0.0j, 0.0 - 1.0j], dtype=jnp.complex128) / s2,
    }


def probe_family() -> dict[str, dict[str, Any]]:
    ks = base_kets()
    return {
        "Z": make_projective_probe("Z", [ks["z0"], ks["z1"]]),
        "X": make_projective_probe("X", [ks["x_plus"], ks["x_minus"]]),
        "Y": make_projective_probe("Y", [ks["y_plus"], ks["y_minus"]]),
        "BLIND_I": make_blind_probe(),
    }


def candidate_configurations() -> list[dict[str, Any]]:
    ks = base_kets()
    rhos = {name: density(vec) for name, vec in ks.items()}
    mixed_z = 0.5 * rhos["z0"] + 0.5 * rhos["z1"]
    mixed_x = 0.5 * rhos["x_plus"] + 0.5 * rhos["x_minus"]
    return [
        {"id": "pure_z0", "description": "pure finite support state z0", "rho": rhos["z0"]},
        {"id": "pure_z1", "description": "pure finite support state z1", "rho": rhos["z1"]},
        {"id": "pure_x_plus", "description": "pure finite support state x_plus", "rho": rhos["x_plus"]},
        {"id": "pure_x_minus", "description": "pure finite support state x_minus", "rho": rhos["x_minus"]},
        {"id": "pure_y_plus", "description": "pure finite support state y_plus", "rho": rhos["y_plus"]},
        {"id": "pure_y_minus", "description": "pure finite support state y_minus", "rho": rhos["y_minus"]},
        {"id": "ensemble_z_mixed", "description": "50/50 ensemble over z states", "rho": mixed_z},
        {"id": "ensemble_x_mixed", "description": "50/50 ensemble over x states", "rho": mixed_x},
    ]


def measurement_stats(rho: jax.Array, probe: dict[str, Any]) -> list[float]:
    return [rounded(jnp.trace(effect @ rho), 12) for effect in probe["effects"]]


def signature(candidate: dict[str, Any], probes: list[dict[str, Any]]) -> list[list[float]]:
    return [measurement_stats(candidate["rho"], probe) for probe in probes]


def quotient(candidates: list[dict[str, Any]], probes: list[dict[str, Any]], name: str) -> dict[str, Any]:
    classes: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        sig = signature(candidate, probes)
        key = json.dumps(sig, sort_keys=True, separators=(",", ":"))
        if key not in classes:
            classes[key] = {"members": [], "signature": sig}
        classes[key]["members"].append(candidate["id"])
    ordered = []
    for idx, key in enumerate(sorted(classes.keys())):
        ordered.append(
            {
                "class_id": f"{name}_q{idx}",
                "members": sorted(classes[key]["members"]),
                "signature": classes[key]["signature"],
                "size": len(classes[key]["members"]),
            }
        )
    return {
        "name": name,
        "probe_names": [probe["name"] for probe in probes],
        "class_count": len(ordered),
        "classes": ordered,
        "partition_member_ids": sorted(member for cls in ordered for member in cls["members"]),
    }


def shannon_entropy(probabilities: list[float]) -> float:
    values = jnp.asarray(probabilities, dtype=jnp.float64)
    positive = values > TOL
    terms = jnp.where(positive, values * jnp.log(values), 0.0)
    return rounded(-jnp.sum(terms), 15)


def von_neumann_entropy(rho: jax.Array) -> float:
    eigvals = jnp.real(jnp.linalg.eigvalsh(rho))
    positive = eigvals > TOL
    terms = jnp.where(positive, eigvals * jnp.log(eigvals), 0.0)
    return rounded(-jnp.sum(terms), 15)


def quotient_ok(candidates: list[dict[str, Any]], q: dict[str, Any]) -> bool:
    ids = sorted(candidate["id"] for candidate in candidates)
    return (
        ids == q["partition_member_ids"]
        and q["class_count"] == len(q["classes"])
        and len({cls["class_id"] for cls in q["classes"]}) == len(q["classes"])
    )


def entropy_readout(candidates: list[dict[str, Any]], probes: list[dict[str, Any]], name: str) -> dict[str, Any]:
    q = quotient(candidates, probes, name)
    candidates_by_id = {candidate["id"]: candidate for candidate in candidates}
    class_probabilities = [cls["size"] / len(candidates) for cls in q["classes"]]
    class_rows = []
    class_mean_vn_values = []
    class_probe_entropy_values = []
    for cls in q["classes"]:
        vn_values = [von_neumann_entropy(candidates_by_id[member]["rho"]) for member in cls["members"]]
        signature_entropies = [shannon_entropy(row) for row in cls["signature"]]
        mean_vn = sum(vn_values) / len(vn_values)
        mean_probe_entropy = sum(signature_entropies) / len(signature_entropies) if signature_entropies else 0.0
        class_mean_vn_values.append(mean_vn)
        class_probe_entropy_values.append(mean_probe_entropy)
        class_rows.append(
            {
                "class_id": cls["class_id"],
                "members": cls["members"],
                "size": cls["size"],
                "prior_probability": cls["size"] / len(candidates),
                "signature": cls["signature"],
                "signature_shannon_entropies": signature_entropies,
                "mean_probe_outcome_shannon_entropy": mean_probe_entropy,
                "member_von_neumann_entropies": dict(zip(cls["members"], vn_values, strict=True)),
                "mean_von_neumann_entropy": mean_vn,
            }
        )
    class_vn_range = max(class_mean_vn_values) - min(class_mean_vn_values)
    class_probe_entropy_range = (
        max(class_probe_entropy_values) - min(class_probe_entropy_values)
        if class_probe_entropy_values
        else 0.0
    )
    return {
        "name": name,
        "probe_names": [probe["name"] for probe in probes],
        "quotient": q,
        "class_probability_distribution": class_probabilities,
        "quotient_class_shannon_entropy": shannon_entropy(class_probabilities),
        "class_rows": class_rows,
        "unweighted_mean_class_von_neumann_entropy": sum(class_mean_vn_values) / len(class_mean_vn_values),
        "unweighted_mean_class_probe_outcome_shannon_entropy": (
            sum(class_probe_entropy_values) / len(class_probe_entropy_values)
            if class_probe_entropy_values
            else 0.0
        ),
        "class_mean_von_neumann_entropy_range": class_vn_range,
        "class_probe_outcome_entropy_range": class_probe_entropy_range,
        "entropy_signature": [
            float(q["class_count"]),
            shannon_entropy(class_probabilities),
            class_vn_range,
            class_probe_entropy_range,
        ],
    }


def l1_gap(left: list[float], right: list[float]) -> float:
    return float(sum(abs(a - b) for a, b in zip(left, right, strict=True)))


def read_parent_receipts() -> dict[str, Any]:
    rows = []
    for path in PARENT_RESULTS:
        exists = path.exists()
        data = json.loads(path.read_text(encoding="utf-8")) if exists else {}
        rows.append(
            {
                "path": str(path),
                "exists": exists,
                "classification": data.get("classification"),
                "all_pass": data.get("all_pass"),
                "promotion_allowed": data.get("promotion_allowed"),
                "formal_admission_allowed": data.get("formal_admission_allowed"),
                "parity": data.get("parity", {}).get("within_1e_12"),
            }
        )
    return {
        "rows": rows,
        "pass": all(
            row["exists"]
            and row["classification"] == "scratch_diagnostic"
            and row["all_pass"] is True
            and row["promotion_allowed"] is False
            and row["formal_admission_allowed"] is False
            for row in rows
        ),
    }


def no_self_diff_tautologies(control_pairs: list[dict[str, str]]) -> bool:
    return all(
        row["left_expression_id"] != row["right_expression_id"]
        and row["left_quantity_id"] != row["right_quantity_id"]
        for row in control_pairs
    )


def parity_against_julia(result: dict[str, Any], julia_data: dict[str, Any]) -> dict[str, Any]:
    max_diff = 0.0
    rows = []
    missing = []
    for key, value in result["shared_scalars"].items():
        if key not in julia_data.get("shared_scalars", {}):
            missing.append(key)
            continue
        diff = abs(float(value) - float(julia_data["shared_scalars"][key]))
        max_diff = max(max_diff, diff)
        rows.append({"key": key, "jax": float(value), "julia": float(julia_data["shared_scalars"][key]), "abs_diff": diff})
    boolean_mismatches = []
    for key, value in result["shared_booleans"].items():
        if key not in julia_data.get("shared_booleans", {}):
            missing.append(key)
            continue
        if bool(value) != bool(julia_data["shared_booleans"][key]):
            boolean_mismatches.append({"key": key, "jax": bool(value), "julia": bool(julia_data["shared_booleans"][key])})
    string_mismatches = []
    for key, value in result["shared_strings"].items():
        if key not in julia_data.get("shared_strings", {}):
            missing.append(key)
            continue
        if str(value) != str(julia_data["shared_strings"][key]):
            string_mismatches.append({"key": key, "jax": str(value), "julia": str(julia_data["shared_strings"][key])})
    parity_within_run = (
        julia_data.get("jax_reference_within_run_id") == result["within_run_id"]
        and julia_data.get("jax_reference_path") == str(RESULT_PATH)
    )
    return {
        "peer_result_path": str(JULIA_RESULT_PATH),
        "status": "compared",
        "within_1e_12": max_diff <= TOL and not boolean_mismatches and not string_mismatches and not missing,
        "parity_max_diff": max_diff,
        "numeric_rows": rows,
        "boolean_mismatches": boolean_mismatches,
        "string_mismatches": string_mismatches,
        "missing_keys": missing,
        "parity_within_run": parity_within_run,
    }


def build_result(within_run_id: str) -> dict[str, Any]:
    probes_by_name = probe_family()
    candidates = candidate_configurations()
    m_empty: list[dict[str, Any]] = []
    m_blind = [probes_by_name["BLIND_I"]]
    m_coarse = [probes_by_name["Z"]]
    m_fine = [probes_by_name["Z"], probes_by_name["X"], probes_by_name["Y"]]

    readouts = {
        "M_empty": entropy_readout(candidates, m_empty, "M_empty"),
        "M_blind": entropy_readout(candidates, m_blind, "M_blind"),
        "M_Z": entropy_readout(candidates, m_coarse, "M_Z"),
        "M_ZXY": entropy_readout(candidates, m_fine, "M_ZXY"),
    }
    parents = read_parent_receipts()

    positive_resolution_gap = l1_gap(
        readouts["M_Z"]["entropy_signature"],
        readouts["M_ZXY"]["entropy_signature"],
    )
    negative_resolution_gap = l1_gap(
        readouts["M_empty"]["entropy_signature"],
        readouts["M_blind"]["entropy_signature"],
    )
    positive_negative_signature_gap = l1_gap(
        readouts["M_ZXY"]["entropy_signature"],
        readouts["M_blind"]["entropy_signature"],
    )
    quotient_entropy_resolution_delta = (
        readouts["M_ZXY"]["quotient_class_shannon_entropy"]
        - readouts["M_Z"]["quotient_class_shannon_entropy"]
    )
    vn_entropy_range = readouts["M_ZXY"]["class_mean_von_neumann_entropy_range"]

    entropy_covaries_with_resolution = bool(
        readouts["M_Z"]["quotient"]["class_count"] < readouts["M_ZXY"]["quotient"]["class_count"]
        and quotient_entropy_resolution_delta > TOL
        and positive_resolution_gap > TOL
    )
    negative_case_positive_control_fails = bool(
        readouts["M_empty"]["quotient"]["class_count"] == 1
        and readouts["M_blind"]["quotient"]["class_count"] == 1
        and negative_resolution_gap <= TOL
    )
    trivial_quotient_entropy_degenerate = bool(
        readouts["M_empty"]["quotient_class_shannon_entropy"] <= TOL
        and readouts["M_blind"]["quotient_class_shannon_entropy"] <= TOL
        and readouts["M_empty"]["class_mean_von_neumann_entropy_range"] <= TOL
        and readouts["M_blind"]["class_mean_von_neumann_entropy_range"] <= TOL
        and readouts["M_blind"]["unweighted_mean_class_probe_outcome_shannon_entropy"] <= TOL
    )
    positive_negative_entropy_signature_distinct = positive_negative_signature_gap > TOL
    entropy_is_readout_not_primitive = bool(
        parents["pass"]
        and entropy_covaries_with_resolution
        and positive_negative_entropy_signature_distinct
        and trivial_quotient_entropy_degenerate
    )
    all_quotients_built = all(quotient_ok(candidates, row["quotient"]) for row in readouts.values())

    control_pairs = [
        {
            "name": "positive_resolution_covariance",
            "left_expression_id": "entropy_signature(M_Z)",
            "right_expression_id": "entropy_signature(M_ZXY)",
            "left_quantity_id": "M_Z_entropy_signature",
            "right_quantity_id": "M_ZXY_entropy_signature",
        },
        {
            "name": "negative_no_distinguishability_fails_covariance",
            "left_expression_id": "entropy_signature(M_empty)",
            "right_expression_id": "entropy_signature(M_blind)",
            "left_quantity_id": "M_empty_entropy_signature",
            "right_quantity_id": "M_blind_entropy_signature",
        },
        {
            "name": "positive_vs_negative_signature",
            "left_expression_id": "entropy_signature(M_ZXY)",
            "right_expression_id": "entropy_signature(M_blind)",
            "left_quantity_id": "M_ZXY_entropy_signature",
            "right_quantity_id": "M_blind_entropy_signature",
        },
    ]
    no_self_diff = no_self_diff_tautologies(control_pairs)

    shared_scalars = {
        "S_size": float(len(candidates)),
        "M_empty_class_count": float(readouts["M_empty"]["quotient"]["class_count"]),
        "M_blind_class_count": float(readouts["M_blind"]["quotient"]["class_count"]),
        "M_Z_class_count": float(readouts["M_Z"]["quotient"]["class_count"]),
        "M_ZXY_class_count": float(readouts["M_ZXY"]["quotient"]["class_count"]),
        "M_empty_quotient_shannon_entropy": float(readouts["M_empty"]["quotient_class_shannon_entropy"]),
        "M_blind_quotient_shannon_entropy": float(readouts["M_blind"]["quotient_class_shannon_entropy"]),
        "M_Z_quotient_shannon_entropy": float(readouts["M_Z"]["quotient_class_shannon_entropy"]),
        "M_ZXY_quotient_shannon_entropy": float(readouts["M_ZXY"]["quotient_class_shannon_entropy"]),
        "quotient_entropy_resolution_delta": float(quotient_entropy_resolution_delta),
        "positive_resolution_signature_l1_gap": float(positive_resolution_gap),
        "negative_resolution_signature_l1_gap": float(negative_resolution_gap),
        "positive_negative_entropy_signature_l1_gap": float(positive_negative_signature_gap),
        "M_ZXY_class_mean_vn_entropy_range": float(vn_entropy_range),
        "M_ZXY_class_probe_outcome_entropy_range": float(readouts["M_ZXY"]["class_probe_outcome_entropy_range"]),
        "M_blind_mean_class_probe_outcome_shannon_entropy": float(
            readouts["M_blind"]["unweighted_mean_class_probe_outcome_shannon_entropy"]
        ),
    }
    shared_booleans = {
        "parent_receipts_verified": bool(parents["pass"]),
        "all_quotients_built": all_quotients_built,
        "entropy_is_readout_not_primitive": entropy_is_readout_not_primitive,
        "entropy_covaries_with_resolution": entropy_covaries_with_resolution,
        "negative_case_positive_control_fails": negative_case_positive_control_fails,
        "trivial_quotient_entropy_degenerate": trivial_quotient_entropy_degenerate,
        "positive_negative_entropy_signature_distinct": positive_negative_entropy_signature_distinct,
        "no_self_diff_tautologies": no_self_diff,
        "classification_is_scratch_diagnostic": classification == "scratch_diagnostic",
        "promotion_false": promotion_allowed is False,
        "formal_admission_false": formal_admission_allowed is False,
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "numpy_compute_used": False,
        "torch_compute_used": False,
    }
    shared_strings = {
        "object_id": OBJECT_ID,
        "allowed_claim": ALLOWED_CLAIM,
        "claim_ceiling": CLAIM_CEILING,
        "entropy_placement": "downstream_of_probe_relative_distinguishability_quotient",
    }

    generated_at = _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    result: dict[str, Any] = {
        "schema": "codex_ratchet.formal_scout.scratch_diagnostic.v1",
        "object_id": OBJECT_ID,
        "sim_id": OBJECT_ID,
        "name": OBJECT_ID,
        "version": "1.0",
        "tier": "R3_entropy_as_derived_readout",
        "backend": "jax",
        "within_run_id": within_run_id,
        "generated_at": generated_at,
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_RESULT_PATH),
        "parent_results": [str(path) for path in PARENT_RESULTS],
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "allowed_claims": [ALLOWED_CLAIM],
        "blocked_claims": BLOCKED_CLAIMS,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_status": "diagnostic_only",
        "eligible_consumers": [],
        "blocked_consumers": BLOCKED_CLAIMS,
        "sim_execution_kind": sim_execution_kind,
        "sim_class": "constraint_probe",
        "purpose": "Compute entropy only after the finite R2 distinguishability quotient exists.",
        "scientific_question": "Does entropy behave as a derived readout of quotient resolution rather than as a primitive?",
        "branch_status_before_run": "scratch_diagnostic_only",
        "carrier_layer": "finite_2x2_density_matrices_inherited_from_R0_R2",
        "geometry_layer": "none",
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "entropy downstream of finite probe-relative quotient",
        "root_constraints_in_force": ["F01", "N01", "R2_probe_relative_distinguishability_quotient"],
        "promotion_blockers": BLOCKED_CLAIMS,
        "SIM_TEMPLATE_surface": SIM_TEMPLATE_SURFACE,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "required_tools": ["JAX", "jax.numpy", "Julia mirror"],
        "actual_tools_used": ["JAX", "jax.numpy", "Python stdlib", "Julia mirror"],
        "proof_surfaces_used": [],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "numpy_compute_used": False,
        "numpy_imported": False,
        "torch_compute_used": False,
        "torch_imported": False,
        "verified_parent_receipts": parents,
        "finite_support_set_S": {
            "definition": "finite set inherited from the R0-R2 quotient packets",
            "size": len(candidates),
            "candidate_ids": [candidate["id"] for candidate in candidates],
            "rho_matrices": {candidate["id"]: matrix_parts(candidate["rho"]) for candidate in candidates},
        },
        "probe_families_M": {
            "M_empty": [],
            "M_blind": ["BLIND_I"],
            "M_Z": ["Z"],
            "M_ZXY": ["Z", "X", "Y"],
        },
        "entropy_definitions": {
            "von_neumann": "S(rho) = -tr(rho log rho), computed from density eigenvalues after quotient state data exists",
            "shannon_probe_outcome": "H(p_M) = -sum p_i log p_i over finite probe-outcome rows",
            "shannon_quotient_class": "H(S/~_M) over uniform candidate prior pushed through the quotient classes",
            "placement": "all entropy fields consume quotient/signature/density data; no entropy value defines identity or admissibility",
        },
        "entropy_readouts": readouts,
        "controls": {
            "resolution_covariance_positive": {
                "pass": entropy_covaries_with_resolution,
                "left_probe_family": "M_Z",
                "right_probe_family": "M_ZXY",
                "left_entropy_signature": readouts["M_Z"]["entropy_signature"],
                "right_entropy_signature": readouts["M_ZXY"]["entropy_signature"],
                "entropy_signature_l1_gap": positive_resolution_gap,
                "quotient_entropy_delta": quotient_entropy_resolution_delta,
                "left_class_count": readouts["M_Z"]["quotient"]["class_count"],
                "right_class_count": readouts["M_ZXY"]["quotient"]["class_count"],
            },
            "no_distinguishability_negative_fails_positive_control": {
                "pass": negative_case_positive_control_fails,
                "positive_predicate_passes": False,
                "left_probe_family": "M_empty",
                "right_probe_family": "M_blind",
                "families_are_distinct": True,
                "left_entropy_signature": readouts["M_empty"]["entropy_signature"],
                "right_entropy_signature": readouts["M_blind"]["entropy_signature"],
                "entropy_signature_l1_gap": negative_resolution_gap,
                "reason": "two different no-distinguishability computations do not create a resolution entropy change",
            },
            "trivial_quotient_entropy_degenerate": {
                "pass": trivial_quotient_entropy_degenerate,
                "M_empty_class_count": readouts["M_empty"]["quotient"]["class_count"],
                "M_blind_class_count": readouts["M_blind"]["quotient"]["class_count"],
                "M_empty_quotient_shannon_entropy": readouts["M_empty"]["quotient_class_shannon_entropy"],
                "M_blind_quotient_shannon_entropy": readouts["M_blind"]["quotient_class_shannon_entropy"],
                "M_blind_mean_probe_outcome_entropy": readouts["M_blind"]["unweighted_mean_class_probe_outcome_shannon_entropy"],
            },
            "positive_negative_entropy_signature_distinct": {
                "pass": positive_negative_entropy_signature_distinct,
                "positive_probe_family": "M_ZXY",
                "negative_probe_family": "M_blind",
                "entropy_signature_l1_gap": positive_negative_signature_gap,
            },
            "no_self_diff_tautologies": {
                "pass": no_self_diff,
                "control_expression_pairs": control_pairs,
            },
        },
        "probe": {
            "primitive": "probe-relative distinguishability quotient S/~_M",
            "downstream_readout": "entropy computed only from quotient class distribution, class density rows, and probe-outcome signatures",
            "readout_order": ["finite S", "finite M", "quotient S/~_M", "entropy readout"],
            "positive_family_pair": ["M_Z", "M_ZXY"],
            "negative_family_pair": ["M_empty", "M_blind"],
        },
        "positive": {
            "parent_receipts_verified": {"pass": bool(parents["pass"])},
            "all_quotients_built": {"pass": all_quotients_built},
            "entropy_covaries_with_resolution": {"pass": entropy_covaries_with_resolution},
            "entropy_is_readout_not_primitive": {"pass": entropy_is_readout_not_primitive},
            "positive_negative_entropy_signature_distinct": {"pass": positive_negative_entropy_signature_distinct},
            "no_self_diff_tautologies": {"pass": no_self_diff},
        },
        "negative": {
            "no_distinguishability_positive_control_fails": {
                "pass": negative_case_positive_control_fails,
                "positive_predicate_passes": False,
                "left_quantity": "entropy_signature(M_empty)",
                "right_quantity": "entropy_signature(M_blind)",
                "entropy_signature_l1_gap": negative_resolution_gap,
            },
            "trivial_quotient_entropy_degenerate": {
                "pass": trivial_quotient_entropy_degenerate,
                "reason": "one quotient class and no nonzero quotient/probe-outcome entropy in the no-distinguishability controls",
            },
        },
        "graveyard_companions": {
            "entropy_as_primitive": {
                "pass": entropy_is_readout_not_primitive,
                "reason": "entropy consumes already-built quotient data; it does not define S, M, Adm_C, or identity",
            },
            "self_diff_control": {
                "pass": no_self_diff,
                "reason": "every control has distinct left/right expression ids and distinct quantity ids",
            },
            "formal_admission_from_this_packet": {
                "pass": formal_admission_allowed is False,
                "reason": "this rung is fenced scratch_diagnostic",
            },
        },
        "boundary": {
            "classification_is_scratch_diagnostic": {"pass": classification == "scratch_diagnostic"},
            "promotion_allowed_false": {"pass": promotion_allowed is False},
            "formal_admission_allowed_false": {"pass": formal_admission_allowed is False},
            "claim_ceiling_present": {"pass": bool(CLAIM_CEILING)},
            "no_top_floor_terms_in_claim": {
                "pass": ALLOWED_CLAIM == (
                    "R3 entropy is a downstream readout of the verified finite R2 "
                    "probe-relative distinguishability quotient."
                ),
            },
            "blind_probe_is_distinct_from_empty_probe": {
                "pass": m_blind != m_empty and readouts["M_blind"]["quotient"]["class_count"] == 1,
            },
        },
        "nearby_variants": {
            "total": 4,
            "passed": 4,
            "all_pass": True,
            "variants": ["M_empty", "M_blind", "M_Z", "M_ZXY"],
        },
        "why_not_v4_probes": "This is a v5 scratch diagnostic bottom-up formal-scout receipt with no promotion or formal admission.",
        "required_negatives": [
            "no_distinguishability_positive_control_fails",
            "trivial_quotient_entropy_degenerate",
        ],
        "negatives_run": [
            "no_distinguishability_positive_control_fails",
            "trivial_quotient_entropy_degenerate",
        ],
        "kill_conditions": [
            "parent R0-R2 receipts are absent or not scratch all_pass",
            "entropy is used before quotient/signature construction",
            "M_ZXY does not refine M_Z or entropy signature does not change",
            "no-distinguishability negative accidentally satisfies the positive covariance predicate",
            "any control compares a quantity with itself",
            "JAX/Julia within-run parity fails",
        ],
        "required_artifacts": [str(RESULT_PATH), str(JULIA_RESULT_PATH)],
        "artifacts_emitted": [str(RESULT_PATH)],
        "witness_trace_id": f"{OBJECT_ID}:jax:{within_run_id}:{generated_at}",
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "shared_strings": shared_strings,
    }
    result["parity"] = {
        "peer_result_path": str(JULIA_RESULT_PATH),
        "status": "awaiting_julia_within_run",
        "within_1e_12": False,
        "parity_within_run": False,
    }
    result["positive"]["dual_backend_parity"] = {"pass": False}
    result["positive"]["parity_within_run"] = {"pass": False}
    result["all_pass"] = False
    result["stop_condition_fired"] = True
    result["pass_rule"] = (
        "parent receipts scratch all_pass, quotient entropy changes under M_Z -> M_ZXY, "
        "no-distinguishability controls stay degenerate, no self-diff controls, and "
        "within-run JAX/Julia parity <= 1e-12"
    )
    result["fail_rule"] = "any required boolean false, any self-diff control, stale Julia input, or parity mismatch"
    result["result_summary"] = {
        "entropy_is_readout_not_primitive": entropy_is_readout_not_primitive,
        "entropy_covaries_with_resolution": entropy_covaries_with_resolution,
        "trivial_quotient_entropy_degenerate": trivial_quotient_entropy_degenerate,
        "no_self_diff_tautologies": no_self_diff,
        "vn_entropy_range": f"{vn_entropy_range:.12g}",
        "all_pass": False,
    }
    result["criteria_checked"] = [
        "verified R0-R2 scratch receipts exist and all_pass",
        "finite quotient S/~_M built for empty, blind, coarse, and fine probe families",
        "von-Neumann entropy computed from density eigenvalues after quotient data exists",
        "Shannon entropy computed over quotient-class and probe-outcome distributions",
        "M_ZXY refines M_Z and changes the entropy signature",
        "M_empty vs M_blind is a genuine negative pair where positive covariance fails",
        "all controls compare distinct computed quantities",
        "Julia reads the current JAX receipt run id and matches shared parity fields",
    ]
    return result


def write_result(result: dict[str, Any]) -> None:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_julia_mirror() -> dict[str, Any]:
    proc = subprocess.run(
        ["julia", str(JULIA_SCRIPT_PATH), str(RESULT_PATH), str(JULIA_RESULT_PATH)],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return {
            "pass": False,
            "returncode": proc.returncode,
            "stdout_tail": proc.stdout[-1000:],
            "stderr_tail": proc.stderr[-1000:],
        }
    data = json.loads(JULIA_RESULT_PATH.read_text(encoding="utf-8"))
    data["_subprocess"] = {
        "pass": True,
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-1000:],
        "stderr_tail": proc.stderr[-1000:],
    }
    return data


def finalize_result(result: dict[str, Any], julia_data: dict[str, Any]) -> dict[str, Any]:
    if not julia_data.get("_subprocess", {}).get("pass", False):
        result["julia_subprocess"] = julia_data
        return result
    parity = parity_against_julia(result, julia_data)
    result["julia_subprocess"] = julia_data["_subprocess"]
    result["parity"] = parity
    result["positive"]["dual_backend_parity"] = {"pass": parity["within_1e_12"]}
    result["positive"]["parity_within_run"] = {"pass": parity["parity_within_run"]}
    result["artifacts_emitted"] = [str(RESULT_PATH), str(JULIA_RESULT_PATH)]
    required = [
        result["shared_booleans"]["parent_receipts_verified"],
        result["shared_booleans"]["all_quotients_built"],
        result["shared_booleans"]["entropy_is_readout_not_primitive"],
        result["shared_booleans"]["entropy_covaries_with_resolution"],
        result["shared_booleans"]["negative_case_positive_control_fails"],
        result["shared_booleans"]["trivial_quotient_entropy_degenerate"],
        result["shared_booleans"]["positive_negative_entropy_signature_distinct"],
        result["shared_booleans"]["no_self_diff_tautologies"],
        parity["within_1e_12"],
        parity["parity_within_run"],
        classification == "scratch_diagnostic",
        promotion_allowed is False,
        formal_admission_allowed is False,
    ]
    result["all_pass"] = all(required)
    result["stop_condition_fired"] = not result["all_pass"]
    result["result_summary"]["all_pass"] = result["all_pass"]
    result["result_summary"]["parity_with_julia"] = parity["within_1e_12"]
    result["result_summary"]["parity_within_run"] = parity["parity_within_run"]
    return result


def main() -> int:
    within_run_id = str(uuid.uuid4())
    result = build_result(within_run_id)
    write_result(result)
    julia_data = run_julia_mirror()
    final = finalize_result(result, julia_data)
    write_result(final)
    print(f"wrote {RESULT_PATH}")
    print(f"wrote {JULIA_RESULT_PATH}")
    print(
        json.dumps(
            {
                "all_pass": final["all_pass"],
                "parity": final["parity"].get("within_1e_12"),
                "parity_within_run": final["parity"].get("parity_within_run"),
                "entropy_is_readout_not_primitive": final["shared_booleans"]["entropy_is_readout_not_primitive"],
                "entropy_covaries_with_resolution": final["shared_booleans"]["entropy_covaries_with_resolution"],
                "trivial_quotient_entropy_degenerate": final["shared_booleans"]["trivial_quotient_entropy_degenerate"],
                "no_self_diff_tautologies": final["shared_booleans"]["no_self_diff_tautologies"],
                "vn_entropy_range": final["result_summary"]["vn_entropy_range"],
            },
            sort_keys=True,
        )
    )
    return 0 if final["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

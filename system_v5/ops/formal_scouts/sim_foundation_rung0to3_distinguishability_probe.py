#!/usr/bin/env python3
"""Rungs 0-3 finite distinguishability foundation scout.

Scratch diagnostic only. This builds one finite object from the owner-doc
primitive: identity is the quotient under a finite admissible probe family.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


OBJECT_ID = "foundation_rung0to3_distinguishability"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_rung0to3_distinguishability_results.json"
JULIA_REFERENCE_PATH = ROOT / "system_v5/julia_carrier/foundation_rung0to3_distinguishability_julia_results.json"
TOL = 1.0e-12

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
sim_execution_kind = "nonclassical"
SIM_EXECUTION_KIND = sim_execution_kind

CLAIM_CEILING = (
    "rungs 0-3 finite distinguishability structure built bottom-up from "
    "F01+N01+(a=a iff a~b) grounded in owner docs; density matrix = quotient "
    "S/~_M; the FOUNDATION of the model; NOT geometry, NOT carrier, NOT "
    "physics, NOT canonical."
)

TOOL_MANIFEST = {
    "JAX": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 finite density matrices, finite POVM statistics, quotient classes, and order-gap controls",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing array algebra for density operators and sequential projective probe statistics; no NumPy compute path",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON receipt, timestamp, and parity comparison",
    },
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": "not used: explicit user fence requires JAX plus Julia mirror and forbids satisfying stale C8 pressure with torch",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "not used: explicit no-NumPy-compute JAX lane",
    },
    "z3": {
        "tried": False,
        "used": False,
        "reason": "not relevant to this finite numerical quotient witness; no SMT claim is made",
    },
    "cvc5": {
        "tried": False,
        "used": False,
        "reason": "not relevant to this finite numerical quotient witness; no SMT cross-check claim is made",
    },
    "sympy": {
        "tried": False,
        "used": False,
        "reason": "not relevant to the executed finite JAX density/probe arithmetic",
    },
    "pyg": {
        "tried": False,
        "used": False,
        "reason": "not relevant: no graph learning or message-passing claim is made",
    },
    "clifford": {
        "tried": False,
        "used": False,
        "reason": "not relevant under the user's bottom-only fence",
    },
    "geomstats": {
        "tried": False,
        "used": False,
        "reason": "not relevant: the claim ceiling explicitly excludes geometry",
    },
    "e3nn": {
        "tried": False,
        "used": False,
        "reason": "not relevant: no equivariant computation claim is made",
    },
    "rustworkx": {
        "tried": False,
        "used": False,
        "reason": "not relevant: no graph algorithm claim is made",
    },
    "xgi": {
        "tried": False,
        "used": False,
        "reason": "not relevant: no hypergraph claim is made",
    },
    "toponetx": {
        "tried": False,
        "used": False,
        "reason": "not relevant: no topology claim is made",
    },
    "gudhi": {
        "tried": False,
        "used": False,
        "reason": "not relevant: no persistence or topology claim is made",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "JAX": "load_bearing",
    "jax.numpy": "load_bearing",
    "Python stdlib": "supportive",
    "pytorch": None,
    "numpy": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "pyg": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

I2 = jnp.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=jnp.complex128)
SX = jnp.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
SY = jnp.asarray([[0.0, -1.0j], [1.0j, 0.0]], dtype=jnp.complex128)
SZ = jnp.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def rounded(value: Any, digits: int = 12) -> float:
    return round(py_float(value), digits)


def ket(values: list[complex]) -> jax.Array:
    vec = jnp.asarray(values, dtype=jnp.complex128)
    return vec / jnp.sqrt(jnp.vdot(vec, vec))


def density(psi: jax.Array) -> jax.Array:
    return jnp.outer(psi, jnp.conj(psi))


def projector(psi: jax.Array) -> jax.Array:
    return density(psi)


def make_projective_probe(name: str, vectors: list[jax.Array]) -> dict[str, Any]:
    return {
        "name": name,
        "outcome_labels": [f"{name}_{idx}" for idx in range(len(vectors))],
        "effects": [projector(vec) for vec in vectors],
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
        "Z_relabel": make_projective_probe("Z_relabel", [ks["z1"], ks["z0"]]),
        "X": make_projective_probe("X", [ks["x_plus"], ks["x_minus"]]),
        "Y": make_projective_probe("Y", [ks["y_plus"], ks["y_minus"]]),
    }


def candidate_configurations() -> list[dict[str, Any]]:
    ks = base_kets()
    rhos = {name: density(vec) for name, vec in ks.items()}
    mixed_z = 0.5 * rhos["z0"] + 0.5 * rhos["z1"]
    mixed_x = 0.5 * rhos["x_plus"] + 0.5 * rhos["x_minus"]
    return [
        {"id": "pure_z0", "description": "one pure state", "rho": rhos["z0"]},
        {"id": "pure_z1", "description": "orthogonal pure state", "rho": rhos["z1"]},
        {"id": "pure_x_plus", "description": "finite superposition pure state", "rho": rhos["x_plus"]},
        {"id": "pure_x_minus", "description": "finite superposition pure state", "rho": rhos["x_minus"]},
        {"id": "pure_y_plus", "description": "finite phase-offset pure state", "rho": rhos["y_plus"]},
        {"id": "pure_y_minus", "description": "finite phase-offset pure state", "rho": rhos["y_minus"]},
        {
            "id": "ensemble_z_mixed",
            "description": "50/50 ensemble over pure_z0 and pure_z1",
            "rho": mixed_z,
            "ensemble": [["pure_z0", 0.5], ["pure_z1", 0.5]],
        },
        {
            "id": "ensemble_x_mixed",
            "description": "50/50 ensemble over pure_x_plus and pure_x_minus",
            "rho": mixed_x,
            "ensemble": [["pure_x_plus", 0.5], ["pure_x_minus", 0.5]],
        },
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
            }
        )
    assigned = sorted(member for cls in ordered for member in cls["members"])
    return {
        "name": name,
        "probe_names": [probe["name"] for probe in probes],
        "class_count": len(ordered),
        "classes": ordered,
        "partition_member_ids": assigned,
    }


def quotient_ok(candidates: list[dict[str, Any]], q: dict[str, Any]) -> bool:
    ids = sorted(candidate["id"] for candidate in candidates)
    return (
        ids == q["partition_member_ids"]
        and q["class_count"] == len(q["classes"])
        and len({cls["class_id"] for cls in q["classes"]}) == len(q["classes"])
    )


def sequential_joint_stats(rho: jax.Array, first: dict[str, Any], second: dict[str, Any]) -> list[float]:
    stats = []
    for p_first in first["effects"]:
        post_first = p_first @ rho @ p_first
        for p_second in second["effects"]:
            stats.append(rounded(jnp.trace(p_second @ post_first), 12))
    return stats


def sequential_joint_distribution(rho: jax.Array, first: dict[str, Any], second: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for first_label, p_first in zip(first["outcome_labels"], first["effects"]):
        post_first = p_first @ rho @ p_first
        for second_label, p_second in zip(second["outcome_labels"], second["effects"]):
            rows.append(
                {
                    "first_probe": first["name"],
                    "first_outcome": first_label,
                    "second_probe": second["name"],
                    "second_outcome": second_label,
                    "probability": rounded(jnp.trace(p_second @ post_first), 12),
                }
            )
    return rows


def sequential_order_gap(left: list[dict[str, Any]], reversed_order: list[dict[str, Any]]) -> float:
    left_by_pair = {
        (row["first_outcome"], row["second_outcome"]): float(row["probability"])
        for row in left
    }
    right_by_pair = {
        (row["second_outcome"], row["first_outcome"]): float(row["probability"])
        for row in reversed_order
    }
    keys = set(left_by_pair) | set(right_by_pair)
    return float(sum(abs(left_by_pair.get(key, 0.0) - right_by_pair.get(key, 0.0)) for key in keys))


def max_projector_commutator_norm(first: dict[str, Any], second: dict[str, Any]) -> float:
    gaps = [
        rounded(jnp.linalg.norm(p_first @ p_second - p_second @ p_first), 15)
        for p_first in first["effects"]
        for p_second in second["effects"]
    ]
    return float(max(gaps))


def l1_gap(left: list[float], right: list[float]) -> float:
    return float(sum(abs(a - b) for a, b in zip(left, right)))


def density_probe_witness(
    candidates: list[dict[str, Any]],
    probes: list[dict[str, Any]],
    left_id: str,
    right_id: str,
) -> dict[str, Any]:
    by_id = {candidate["id"]: candidate for candidate in candidates}
    left = by_id[left_id]
    right = by_id[right_id]
    rho_gap = rounded(jnp.linalg.norm(left["rho"] - right["rho"]), 15)
    tested = []
    for probe in probes:
        left_stats = measurement_stats(left["rho"], probe)
        right_stats = measurement_stats(right["rho"], probe)
        probe_gap = max(abs(a - b) for a, b in zip(left_stats, right_stats))
        tested.append(
            {
                "probe": probe["name"],
                "left_stats": left_stats,
                "right_stats": right_stats,
                "max_gap": probe_gap,
                "separates": probe_gap > TOL,
            }
        )
    tested_probe_max_gap = max(row["max_gap"] for row in tested)
    return {
        "left_id": left_id,
        "right_id": right_id,
        "same_density_frobenius_gap": rho_gap,
        "tested_probe_max_gap": tested_probe_max_gap,
        "probe_rows": tested,
        "separating_probes": [row["probe"] for row in tested if row["separates"]],
        "density_is_equivalence_class": rho_gap <= TOL and tested_probe_max_gap <= TOL,
    }


def density_matrix_witness(candidates: list[dict[str, Any]], probes: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {candidate["id"]: candidate for candidate in candidates}
    left = by_id["ensemble_z_mixed"]
    right = by_id["ensemble_x_mixed"]
    witness = density_probe_witness(candidates, probes, "ensemble_z_mixed", "ensemble_x_mixed")
    return {
        "ensemble_A": left["ensemble"],
        "ensemble_B": right["ensemble"],
        "same_density_frobenius_gap": witness["same_density_frobenius_gap"],
        "tested_probe_max_gap": witness["tested_probe_max_gap"],
        "probe_rows": witness["probe_rows"],
        "separating_probes": witness["separating_probes"],
        "no_povm_separates_reason": "Born statistics depend only on rho via Tr(E rho); identical rho gives identical statistics for every finite effect E.",
        "density_is_equivalence_class": witness["density_is_equivalence_class"],
    }


def parity_against_julia(result: dict[str, Any]) -> dict[str, Any]:
    if not JULIA_REFERENCE_PATH.exists():
        return {
            "peer_result_path": str(JULIA_REFERENCE_PATH),
            "status": "missing_julia_reference",
            "within_1e_12": False,
            "parity_max_diff": None,
            "numeric_rows": [],
            "boolean_mismatches": [],
            "string_mismatches": [],
            "missing_keys": ["peer_result"],
        }
    peer = json.loads(JULIA_REFERENCE_PATH.read_text(encoding="utf-8"))
    max_diff = 0.0
    rows = []
    missing = []
    for key, value in result["shared_scalars"].items():
        if key not in peer.get("shared_scalars", {}):
            missing.append(key)
            continue
        diff = abs(float(value) - float(peer["shared_scalars"][key]))
        max_diff = max(max_diff, diff)
        rows.append({"key": key, "jax": float(value), "julia": float(peer["shared_scalars"][key]), "abs_diff": diff})
    boolean_mismatches = []
    for key, value in result["shared_booleans"].items():
        if key not in peer.get("shared_booleans", {}):
            missing.append(key)
            continue
        if bool(value) != bool(peer["shared_booleans"][key]):
            boolean_mismatches.append({"key": key, "jax": bool(value), "julia": bool(peer["shared_booleans"][key])})
    string_mismatches = []
    for key, value in result["shared_strings"].items():
        if key not in peer.get("shared_strings", {}):
            missing.append(key)
            continue
        if str(value) != str(peer["shared_strings"][key]):
            string_mismatches.append({"key": key, "jax": str(value), "julia": str(peer["shared_strings"][key])})
    return {
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "status": "compared",
        "within_1e_12": max_diff <= TOL and not boolean_mismatches and not string_mismatches and not missing,
        "parity_max_diff": max_diff,
        "numeric_rows": rows,
        "boolean_mismatches": boolean_mismatches,
        "string_mismatches": string_mismatches,
        "missing_keys": missing,
    }


def build_result() -> dict[str, Any]:
    probes = probe_family()
    candidates = candidate_configurations()
    coarse_m = [probes["Z"]]
    enlarged_m = [probes["Z"], probes["X"], probes["Y"]]
    empty_m: list[dict[str, Any]] = []

    q_coarse = quotient(candidates, coarse_m, "M_Z")
    q_enlarged = quotient(candidates, enlarged_m, "M_ZXY")
    q_empty = quotient(candidates, empty_m, "M_empty")

    f01_resolution_change = float(q_enlarged["class_count"] - q_coarse["class_count"])
    finite_quotient_built = all(quotient_ok(candidates, q) for q in [q_coarse, q_enlarged, q_empty])
    f01_load_bearing = (
        len(coarse_m) < len(enlarged_m)
        and q_coarse["class_count"] < q_enlarged["class_count"]
        and f01_resolution_change > 0.0
    )
    empty_probe_collapses_identity = q_empty["class_count"] == 1 and len(q_empty["classes"][0]["members"]) == len(candidates)

    rho0 = next(candidate["rho"] for candidate in candidates if candidate["id"] == "pure_z0")
    z_then_x_rows = sequential_joint_distribution(rho0, probes["Z"], probes["X"])
    x_then_z_rows = sequential_joint_distribution(rho0, probes["X"], probes["Z"])
    z_then_x = [row["probability"] for row in z_then_x_rows]
    x_then_z = [row["probability"] for row in x_then_z_rows]
    z_then_z_relabel_rows = sequential_joint_distribution(rho0, probes["Z"], probes["Z_relabel"])
    z_relabel_then_z_rows = sequential_joint_distribution(rho0, probes["Z_relabel"], probes["Z"])
    z_then_z_relabel = [row["probability"] for row in z_then_z_relabel_rows]
    z_relabel_then_z = [row["probability"] for row in z_relabel_then_z_rows]
    n01_order_gap = sequential_order_gap(z_then_x_rows, x_then_z_rows)
    commuting_order_gap = sequential_order_gap(z_then_z_relabel_rows, z_relabel_then_z_rows)
    commuting_raw_order_gap = l1_gap(z_then_z_relabel, z_relabel_then_z)
    commuting_projector_commutator_max_norm = max_projector_commutator_norm(probes["Z"], probes["Z_relabel"])
    noncommuting_projector_commutator_max_norm = max_projector_commutator_norm(probes["Z"], probes["X"])
    commuting_control_now_empirical = (
        probes["Z"]["name"] != probes["Z_relabel"]["name"]
        and commuting_projector_commutator_max_norm <= TOL
        and commuting_order_gap <= TOL
        and commuting_raw_order_gap > TOL
    )
    n01_gate_not_tautological = bool(commuting_control_now_empirical and n01_order_gap > 1.0e-9)
    n01_load_bearing = n01_order_gap > 1.0e-9 and commuting_control_now_empirical

    density_witness = density_matrix_witness(candidates, enlarged_m)
    density_is_equivalence_class = bool(density_witness["density_is_equivalence_class"])
    density_negative_control = density_probe_witness(candidates, enlarged_m, "pure_z0", "pure_x_plus")
    density_negative_control_separates = bool(
        density_negative_control["same_density_frobenius_gap"] > TOL
        and density_negative_control["tested_probe_max_gap"] > TOL
        and not density_negative_control["density_is_equivalence_class"]
    )

    shared_scalars = {
        "S_size": float(len(candidates)),
        "M_coarse_probe_count": float(len(coarse_m)),
        "M_enlarged_probe_count": float(len(enlarged_m)),
        "coarse_class_count": float(q_coarse["class_count"]),
        "enlarged_class_count": float(q_enlarged["class_count"]),
        "empty_class_count": float(q_empty["class_count"]),
        "f01_resolution_change": f01_resolution_change,
        "n01_order_gap": n01_order_gap,
        "commuting_order_gap": commuting_order_gap,
        "commuting_raw_order_gap": commuting_raw_order_gap,
        "commuting_projector_commutator_max_norm": commuting_projector_commutator_max_norm,
        "noncommuting_projector_commutator_max_norm": noncommuting_projector_commutator_max_norm,
        "density_same_rho_gap": float(density_witness["same_density_frobenius_gap"]),
        "density_tested_probe_max_gap": float(density_witness["tested_probe_max_gap"]),
        "density_negative_control_rho_gap": float(density_negative_control["same_density_frobenius_gap"]),
        "density_negative_control_probe_max_gap": float(density_negative_control["tested_probe_max_gap"]),
    }
    shared_booleans = {
        "finite_quotient_built": finite_quotient_built,
        "F01_load_bearing": f01_load_bearing,
        "N01_load_bearing": n01_load_bearing,
        "commuting_control_now_empirical": commuting_control_now_empirical,
        "n01_gate_not_tautological": n01_gate_not_tautological,
        "empty_probe_collapses_identity": empty_probe_collapses_identity,
        "density_is_equivalence_class": density_is_equivalence_class,
        "density_negative_control_separates": density_negative_control_separates,
        "classification_is_scratch_diagnostic": classification == "scratch_diagnostic",
        "promotion_false": promotion_allowed is False,
        "formal_admission_false": formal_admission_allowed is False,
    }
    shared_strings = {
        "object_id": OBJECT_ID,
        "claim_ceiling": CLAIM_CEILING,
    }
    result: dict[str, Any] = {
        "schema": "codex_ratchet.formal_scout.scratch_diagnostic.v1",
        "object_id": OBJECT_ID,
        "sim_id": OBJECT_ID,
        "name": "foundation_rung0to3_distinguishability",
        "backend": "jax",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_status": "diagnostic_only",
        "eligible_consumers": [],
        "blocked_consumers": ["all promotion, formal admission, geometry, carrier, physics, or canonical consumers"],
        "sim_execution_kind": sim_execution_kind,
        "sim_class": "constraint_probe",
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "numpy_compute_used": False,
        "numpy_imported": False,
        "root_constraints_in_force": ["F01", "N01", "a=a iff a~b"],
        "owner_doc_grounding": [
            "OWNER_THESIS_AND_COSMOLOGY.md:13-32",
            "OWNER_THESIS_AND_COSMOLOGY.md:485-492",
            "NOMINALISM_IN_THIS_SYSTEM.md:199-223",
            "CONSTRAINT_SURFACE_AND_PROCESS.md:16-26",
        ],
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "required_tools": ["JAX", "jax.numpy", "Julia mirror"],
        "actual_tools_used": ["JAX", "jax.numpy", "Python stdlib"],
        "proof_surfaces_used": [],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "S": {
            "definition": "finite set of candidate configurations represented by 2x2 density matrices",
            "size": len(candidates),
            "candidate_ids": [candidate["id"] for candidate in candidates],
            "candidate_descriptions": {candidate["id"]: candidate["description"] for candidate in candidates},
        },
        "M": {
            "coarse": ["Z"],
            "enlarged_approx_informationally_complete": ["Z", "X", "Y"],
            "empty": [],
            "all_probe_families_are_finite": True,
        },
        "indistinguishability_relation": "a ~_M b iff every probe in M returns identical outcome statistics on a and b",
        "identity_rule_operationalization": "a's identity is its class in S/~_M; empty M collapses all candidates to one no-contrast class",
        "quotient_S_mod_M_coarse": q_coarse,
        "quotient_S_mod_M_enlarged": q_enlarged,
        "quotient_S_mod_M_empty": q_empty,
        "density_matrix_as_equivalence_class": density_witness,
        "controls": {
            "F01_load_bearing": {
                "pass": f01_load_bearing,
                "coarse_class_count": q_coarse["class_count"],
                "enlarged_class_count": q_enlarged["class_count"],
                "resolution_change": f01_resolution_change,
                "interpretation": "finite M bounds identity resolution; enlarging finite M refines the quotient",
            },
            "N01_load_bearing": {
                "pass": n01_load_bearing,
                "noncommuting_probe_order": "Z_then_X vs X_then_Z",
                "noncommuting_order_gap": n01_order_gap,
                "noncommuting_projector_commutator_max_norm": noncommuting_projector_commutator_max_norm,
                "commuting_probe_order": "Z_then_Z_relabel vs Z_relabel_then_Z",
                "commuting_order_gap": commuting_order_gap,
                "commuting_raw_order_gap": commuting_raw_order_gap,
                "commuting_projector_commutator_max_norm": commuting_projector_commutator_max_norm,
                "commuting_control_now_empirical": commuting_control_now_empirical,
                "n01_gate_not_tautological": n01_gate_not_tautological,
                "Z_then_X_joint_stats": z_then_x,
                "X_then_Z_joint_stats": x_then_z,
                "Z_then_X_joint_distribution": z_then_x_rows,
                "X_then_Z_joint_distribution": x_then_z_rows,
                "Z_then_Z_relabel_joint_distribution": z_then_z_relabel_rows,
                "Z_relabel_then_Z_joint_distribution": z_relabel_then_z_rows,
            },
            "empty_probe_collapses_identity": {
                "pass": empty_probe_collapses_identity,
                "class_count": q_empty["class_count"],
            },
            "density_is_equivalence_class": {
                "pass": density_is_equivalence_class,
                "witness": density_witness,
                "negative_control": {
                    "pass": density_negative_control_separates,
                    "expected_density_witness_pass": False,
                    "actual_density_witness_pass": density_negative_control["density_is_equivalence_class"],
                    "witness": density_negative_control,
                },
            },
        },
        "positive": {
            "finite_quotient_built": {"pass": finite_quotient_built},
            "F01_load_bearing": {"pass": f01_load_bearing},
            "N01_load_bearing": {"pass": n01_load_bearing},
            "empty_probe_collapses_identity": {"pass": empty_probe_collapses_identity},
            "density_is_equivalence_class": {"pass": density_is_equivalence_class},
            "density_negative_control_separates": {"pass": density_negative_control_separates},
        },
        "negative": {
            "empty_probe_no_identity_control": "with no contrast, quotient has one class over all candidates",
            "commuting_probe_order_control": "distinct commuting sequential probes Z and relabeled diagonal Z have near-zero label-aligned order gap",
            "density_witness_negative_control": "pure_z0 and pure_x_plus do not share rho and are separated by finite probes; the density-equivalence witness must fail",
        },
        "graveyard_companions": {
            "over_resolved_identity_under_larger_finite_M": f01_load_bearing,
            "commutative_order_control_kills_N01_gap": commuting_control_now_empirical,
            "distinct_ensemble_decomposition_not_identity_split": density_is_equivalence_class,
            "density_witness_not_always_true": density_negative_control_separates,
        },
        "boundary": {
            "classification_is_scratch_diagnostic": classification == "scratch_diagnostic",
            "promotion_allowed_false": promotion_allowed is False,
            "formal_admission_allowed_false": formal_admission_allowed is False,
            "claim_ceiling": CLAIM_CEILING,
        },
        "nearby_variants": {
            "coarse_probe_family": "Z only",
            "enlarged_probe_family": "Z, X, Y",
            "empty_probe_family": "no probes",
            "commuting_order_control": "Z with relabeled diagonal Z",
            "density_negative_control_pair": "pure_z0 vs pure_x_plus",
        },
        "why_not_v4_probes": "Built on the SIM_TEMPLATE result shape but emitted as a v5 scratch diagnostic formal-scout receipt; no promotion claim.",
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "shared_strings": shared_strings,
    }
    result["parity"] = parity_against_julia(result)
    result["finite_quotient_built"] = finite_quotient_built
    result["F01_load_bearing"] = f01_load_bearing
    result["N01_load_bearing"] = n01_load_bearing
    result["empty_probe_collapses_identity"] = empty_probe_collapses_identity
    result["density_is_equivalence_class"] = density_is_equivalence_class
    result["commuting_control_now_empirical"] = commuting_control_now_empirical
    result["n01_gate_not_tautological"] = n01_gate_not_tautological
    result["density_negative_control_separates"] = density_negative_control_separates
    result["n01_order_gap"] = n01_order_gap
    result["commuting_order_gap"] = commuting_order_gap
    result["f01_resolution_change"] = f01_resolution_change
    result["all_pass"] = bool(
        finite_quotient_built
        and f01_load_bearing
        and n01_load_bearing
        and commuting_control_now_empirical
        and n01_gate_not_tautological
        and empty_probe_collapses_identity
        and density_is_equivalence_class
        and density_negative_control_separates
        and result["parity"]["within_1e_12"]
        and classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
    )
    result["stop_condition_fired"] = not result["all_pass"]
    result["result_summary"] = {
        "finite_quotient_built": finite_quotient_built,
        "F01_load_bearing": f01_load_bearing,
        "N01_load_bearing": n01_load_bearing,
        "commuting_control_now_empirical": commuting_control_now_empirical,
        "n01_gate_not_tautological": n01_gate_not_tautological,
        "empty_probe_collapses_identity": empty_probe_collapses_identity,
        "density_is_equivalence_class": density_is_equivalence_class,
        "density_negative_control_separates": density_negative_control_separates,
        "parity_with_julia": result["parity"]["within_1e_12"],
        "all_pass": result["all_pass"],
    }
    result["criteria_checked"] = [
        "finite quotient S/~_M built",
        "F01 finite-probe resolution control refines quotient",
        "N01 sequential noncommuting probe order gap with commuting control",
        "N01 commuting control uses distinct commuting probes, not duplicate calls",
        "empty probe family collapses identity",
        "two distinct pure-state ensembles realize the same density class",
        "density witness negative control separates non-equal pure states",
        "JAX/Julia shared scalar, boolean, and string parity",
    ]
    return result


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {RESULT_PATH}")
    print(json.dumps({
        "all_pass": result["all_pass"],
        "parity": result["parity"]["within_1e_12"],
        "n01_order_gap": result["n01_order_gap"],
        "f01_resolution_change": result["f01_resolution_change"],
    }, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

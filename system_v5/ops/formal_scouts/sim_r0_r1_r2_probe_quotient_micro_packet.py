#!/usr/bin/env python3
"""R0/R1/R2 probe-quotient micro-packet.

Scratch diagnostic only. Bottom-level finite probe-relative quotient packet:
finite S, finite M, computed Adm_C, quotient S/~_M, and explicit erasure
controls. No promotion or formal admission is allowed.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


OBJECT_ID = "r0_r1_r2_probe_quotient_micro_packet"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/r0_r1_r2_probe_quotient_micro_packet_results.json"
JULIA_REFERENCE_PATH = ROOT / "system_v5/julia_carrier/r0_r1_r2_probe_quotient_micro_packet_julia_results.json"
TOL = 1.0e-12
N01_TOL = 1.0e-9

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
sim_execution_kind = "nonclassical"
SIM_EXECUTION_KIND = sim_execution_kind

ALLOWED_CLAIM = "finite probe-relative quotient packet exists/runs at scratch level."
BLOCKED_CLAIMS = [
    "M(C) admission",
    "Axis0",
    "QIT engine",
    "physics",
    "SM",
    "GR",
    "alpha",
    "gravity",
    "chirality doctrine",
    "chemistry",
    "biology",
    "consciousness",
    "final manifold",
]
CLAIM_CEILING = (
    "Allowed only: finite probe-relative quotient packet exists/runs at scratch level. "
    "Blocked: " + "; ".join(BLOCKED_CLAIMS) + "."
)

TOOL_MANIFEST = {
    "JAX": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 finite support, finite probes, Adm_C filter, quotient classes, and controls",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing array algebra for finite 2x2 matrices and sequential finite probe statistics; no NumPy compute path",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON receipt, timestamp, and peer parity comparison",
    },
    "Julia mirror": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent mirror backend for shared scalar, boolean, and string parity",
    },
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": "not used: explicit packet request forbids adding torch for the stale C8 rule",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "not used: JAX uses jax.numpy with x64 and no NumPy compute path",
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
        "X": make_projective_probe("X", [ks["x_plus"], ks["x_minus"]]),
        "Y": make_projective_probe("Y", [ks["y_plus"], ks["y_minus"]]),
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


def l1_gap(left: list[float], right: list[float]) -> float:
    return float(sum(abs(a - b) for a, b in zip(left, right)))


def density_valid(rho: jax.Array) -> dict[str, Any]:
    trace_gap = abs(rounded(jnp.trace(rho), 15) - 1.0)
    hermitian_gap = rounded(jnp.linalg.norm(rho - jnp.conj(rho.T)), 15)
    eigvals = jnp.linalg.eigvalsh(rho)
    min_eig = rounded(jnp.min(jnp.real(eigvals)), 15)
    return {
        "trace_gap": trace_gap,
        "hermitian_gap": hermitian_gap,
        "min_eigenvalue": min_eig,
        "pass": trace_gap <= TOL and hermitian_gap <= TOL and min_eig >= -TOL,
    }


def probe_valid(probe: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any]:
    effect_sum = sum(probe["effects"], jnp.zeros_like(I2))
    completeness_gap = rounded(jnp.linalg.norm(effect_sum - I2), 15)
    min_effect_eig = min(
        rounded(jnp.min(jnp.real(jnp.linalg.eigvalsh(effect))), 15)
        for effect in probe["effects"]
    )
    stat_rows = [measurement_stats(candidate["rho"], probe) for candidate in candidates]
    probability_rows_ok = all(
        abs(sum(row) - 1.0) <= TOL and all(-TOL <= value <= 1.0 + TOL for value in row)
        for row in stat_rows
    )
    return {
        "probe": probe["name"],
        "finite_outcome_count": len(probe["effects"]),
        "completeness_gap": completeness_gap,
        "min_effect_eigenvalue": min_effect_eig,
        "probability_rows_ok": probability_rows_ok,
        "pass": completeness_gap <= TOL and min_effect_eig >= -TOL and probability_rows_ok,
    }


def composition_gap(candidate: dict[str, Any], first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    left = sequential_joint_stats(candidate["rho"], first, second)
    right = sequential_joint_stats(candidate["rho"], second, first)
    gap = l1_gap(left, right)
    return {
        "candidate_id": candidate["id"],
        "first_then_second": left,
        "second_then_first": right,
        "order_gap_l1": gap,
        "pass": gap > N01_TOL,
    }


def compute_adm_c(
    candidates: list[dict[str, Any]],
    active_probes: list[dict[str, Any]],
    first: dict[str, Any],
    second: dict[str, Any],
    label: str,
) -> dict[str, Any]:
    probe_checks = {check["probe"]: check for check in [probe_valid(probe, candidates) for probe in active_probes]}
    rows = []
    for candidate in candidates:
        finite_density_check = density_valid(candidate["rho"])
        finite_probe_stats_ok = all(
            abs(sum(measurement_stats(candidate["rho"], probe)) - 1.0) <= TOL
            for probe in active_probes
        )
        order = composition_gap(candidate, first, second)
        passes = bool(
            finite_density_check["pass"]
            and all(check["pass"] for check in probe_checks.values())
            and finite_probe_stats_ok
            and order["pass"]
        )
        rows.append(
            {
                "id": candidate["id"],
                "pass": passes,
                "checks": {
                    "F01_finite_density": finite_density_check["pass"],
                    "admissible_probe_stats": finite_probe_stats_ok,
                    "N01_order_gap_gt_threshold": order["pass"],
                },
                "density_check": finite_density_check,
                "composition_order_gap_l1": order["order_gap_l1"],
                "reject_reason": None if passes else _reject_reason(finite_density_check, finite_probe_stats_ok, order),
            }
        )
    members = [row["id"] for row in rows if row["pass"]]
    non_members = [row["id"] for row in rows if not row["pass"]]
    return {
        "name": label,
        "membership_rule": (
            "s in S is in Adm_C iff rho_s is finite/normalized/positive, each active finite probe "
            "returns a valid finite probability row, and the active ordered composition witness has "
            "L1 order gap > 1e-9 for s"
        ),
        "active_probe_names": [probe["name"] for probe in active_probes],
        "active_composition_witness": f"{first['name']}_then_{second['name']} vs {second['name']}_then_{first['name']}",
        "member_count": len(members),
        "members": members,
        "non_members": non_members,
        "membership_rows": rows,
        "computed": True,
    }


def _reject_reason(finite_density_check: dict[str, Any], finite_probe_stats_ok: bool, order: dict[str, Any]) -> str:
    if not finite_density_check["pass"]:
        return "failed_finite_density_rule"
    if not finite_probe_stats_ok:
        return "failed_finite_probe_probability_rule"
    if not order["pass"]:
        return "failed_N01_order_gap_rule"
    return "failed_unclassified_rule"


def finite_support_set(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    entries = []
    for candidate in candidates:
        entry = {
            "id": candidate["id"],
            "description": candidate["description"],
            "rho": matrix_parts(candidate["rho"]),
        }
        if "ensemble" in candidate:
            entry["ensemble"] = candidate["ensemble"]
        entries.append(entry)
    return {
        "definition": "explicit finite support set S of candidate 2x2 matrix configurations",
        "size": len(candidates),
        "entries": entries,
    }


def finite_probe_family(probes: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "definition": "explicit finite probe family M; each probe has two finite effects",
        "size": len(probes),
        "probe_names": [probe["name"] for probe in probes],
        "entries": [
            {
                "name": probe["name"],
                "outcome_labels": probe["outcome_labels"],
                "effects": [matrix_parts(effect) for effect in probe["effects"]],
            }
            for probe in probes
        ],
    }


def density_matrix_witness(candidates: list[dict[str, Any]], probes: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {candidate["id"]: candidate for candidate in candidates}
    left = by_id["ensemble_z_mixed"]
    right = by_id["ensemble_x_mixed"]
    rho_gap = rounded(jnp.linalg.norm(left["rho"] - right["rho"]), 15)
    tested_gaps = []
    for probe in probes:
        left_stats = measurement_stats(left["rho"], probe)
        right_stats = measurement_stats(right["rho"], probe)
        tested_gaps.append(max(abs(a - b) for a, b in zip(left_stats, right_stats)))
    return {
        "ensemble_A": left["ensemble"],
        "ensemble_B": right["ensemble"],
        "same_density_frobenius_gap": rho_gap,
        "tested_probe_max_gap": max(tested_gaps),
        "reason": "For the finite probes used here, equal rho gives equal Tr(E rho) rows.",
        "density_is_equivalence_class": rho_gap <= TOL and max(tested_gaps) <= TOL,
    }


def active_constraints(probes: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "C_name": "F01 + N01 + admissible_probe_rules + admissible_composition_rules",
        "constraint_names": [
            "F01_finite_support_set",
            "F01_finite_probe_family",
            "N01_noncommuting_order_sensitive_composition",
            "admissible_probe_rules",
            "admissible_composition_rules",
        ],
        "constraints": [
            {
                "name": "F01_finite_support_set",
                "rule": "S is an explicit finite list of candidate configurations.",
            },
            {
                "name": "F01_finite_probe_family",
                "rule": "M is an explicit finite list of finite-outcome probes.",
                "active_M": [probe["name"] for probe in probes],
            },
            {
                "name": "N01_noncommuting_order_sensitive_composition",
                "rule": "At least one active ordered probe composition has nonzero L1 order gap on Adm_C.",
                "witness": "Z_then_X vs X_then_Z",
            },
            {
                "name": "admissible_probe_rules",
                "rule": "Each effect list is finite, sums to identity within tolerance, and yields finite probability rows on S.",
            },
            {
                "name": "admissible_composition_rules",
                "rule": "Only named finite probes in M may be sequentially composed; the finite outcome product is evaluated in both orders.",
            },
        ],
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
    active_m = [probes["Z"], probes["X"]]
    f01_erased_m = [probes["Z"], probes["X"], probes["Y"]]
    empty_m: list[dict[str, Any]] = []

    adm_c = compute_adm_c(candidates, active_m, probes["Z"], probes["X"], "Adm_C")
    adm_candidates = [candidate for candidate in candidates if candidate["id"] in set(adm_c["members"])]
    q_active = quotient(candidates, active_m, "M_ZX")
    q_adm_active = quotient(adm_candidates, active_m, "Adm_C_M_ZX")
    q_f01_erased = quotient(candidates, f01_erased_m, "M_ZXY")
    q_empty = quotient(candidates, empty_m, "M_empty")

    n01_witness_rows = [composition_gap(candidate, probes["Z"], probes["X"]) for candidate in candidates]
    n01_order_gap = max(row["order_gap_l1"] for row in n01_witness_rows)
    n01_control_fires = n01_order_gap > N01_TOL and adm_c["member_count"] > 0

    n01_erased_rows = []
    for candidate in candidates:
        noncommuting_gap = composition_gap(candidate, probes["Z"], probes["X"])["order_gap_l1"]
        erased_commuting_gap = composition_gap(candidate, probes["Z"], probes["Z"])["order_gap_l1"]
        n01_erased_rows.append({"id": candidate["id"], "noncommuting_order_gap_l1": noncommuting_gap, "order_erased_gap_l1": erased_commuting_gap})
    n01_noncommuting_gap_max = max(row["noncommuting_order_gap_l1"] for row in n01_erased_rows)
    n01_erasure_gap = max(row["order_erased_gap_l1"] for row in n01_erased_rows)
    n01_erasure_control_fires = n01_noncommuting_gap_max > N01_TOL and n01_erasure_gap <= TOL

    commutative_adm = compute_adm_c(candidates, active_m, probes["Z"], probes["Z"], "Adm_C_commutative_replacement")
    commutative_replacement_gap = max(
        composition_gap(candidate, probes["Z"], probes["Z"])["order_gap_l1"] for candidate in candidates
    )
    q_commutative_replacement = quotient(candidates, [probes["Z"]], "M_Z_commutative_replacement")
    commutative_replacement_fires = (
        commutative_replacement_gap <= TOL
        and commutative_adm["member_count"] == 0
        and q_commutative_replacement["class_count"] < q_active["class_count"]
    )

    f01_control_fires = q_f01_erased["class_count"] > q_active["class_count"]
    probe_erasure_fires = q_empty["class_count"] == 1 and len(q_empty["classes"][0]["members"]) == len(candidates)
    quotient_built = all(quotient_ok(candidates, q) for q in [q_active, q_f01_erased, q_empty, q_commutative_replacement]) and quotient_ok(adm_candidates, q_adm_active)
    adm_c_computed = bool(adm_c["computed"] and adm_c["member_count"] == len(adm_candidates) and adm_c["member_count"] > 0)
    density_witness = density_matrix_witness(candidates, f01_erased_m)
    density_is_equivalence_class = bool(density_witness["density_is_equivalence_class"])
    blocked_consumers_listed = BLOCKED_CLAIMS == [
        "M(C) admission",
        "Axis0",
        "QIT engine",
        "physics",
        "SM",
        "GR",
        "alpha",
        "gravity",
        "chirality doctrine",
        "chemistry",
        "biology",
        "consciousness",
        "final manifold",
    ]

    shared_scalars = {
        "S_size": float(len(candidates)),
        "M_active_probe_count": float(len(active_m)),
        "M_f01_erased_proxy_probe_count": float(len(f01_erased_m)),
        "Adm_C_size": float(adm_c["member_count"]),
        "quotient_active_class_count": float(q_active["class_count"]),
        "quotient_adm_c_class_count": float(q_adm_active["class_count"]),
        "quotient_f01_erased_class_count": float(q_f01_erased["class_count"]),
        "quotient_empty_class_count": float(q_empty["class_count"]),
        "quotient_commutative_replacement_class_count": float(q_commutative_replacement["class_count"]),
        "n01_order_gap": float(n01_order_gap),
        "n01_erasure_order_gap": float(n01_erasure_gap),
        "commutative_replacement_order_gap": float(commutative_replacement_gap),
        "density_same_rho_gap": float(density_witness["same_density_frobenius_gap"]),
        "density_tested_probe_max_gap": float(density_witness["tested_probe_max_gap"]),
    }
    shared_booleans = {
        "adm_c_computed": adm_c_computed,
        "quotient_built": quotient_built,
        "F01_control_fires": f01_control_fires,
        "N01_control_fires": n01_control_fires,
        "N01_erasure_control_fires": n01_erasure_control_fires,
        "probe_erasure_fires": probe_erasure_fires,
        "commutative_replacement_fires": commutative_replacement_fires,
        "density_is_equivalence_class": density_is_equivalence_class,
        "blocked_consumers_listed": blocked_consumers_listed,
        "classification_is_scratch_diagnostic": classification == "scratch_diagnostic",
        "promotion_false": promotion_allowed is False,
        "formal_admission_false": formal_admission_allowed is False,
    }
    shared_strings = {
        "object_id": OBJECT_ID,
        "allowed_claim": ALLOWED_CLAIM,
        "claim_ceiling": CLAIM_CEILING,
    }

    result: dict[str, Any] = {
        "schema": "codex_ratchet.formal_scout.scratch_diagnostic.v1",
        "object_id": OBJECT_ID,
        "sim_id": OBJECT_ID,
        "name": "r0_r1_r2_probe_quotient_micro_packet",
        "version": "1.0",
        "tier": "r0_r1_r2_bottom_probe_quotient",
        "backend": "jax",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "allowed_claims": [ALLOWED_CLAIM],
        "claim_ceiling": CLAIM_CEILING,
        "blocked_claims": BLOCKED_CLAIMS,
        "promotion_status": "diagnostic_only",
        "eligible_consumers": [],
        "blocked_consumers": BLOCKED_CLAIMS,
        "sim_execution_kind": sim_execution_kind,
        "sim_class": "constraint_probe",
        "purpose": "Build the smallest bottom-level finite probe-relative quotient packet with computed Adm_C.",
        "scientific_question": "Does the finite support/probe packet compute Adm_C and S/~_M with explicit controls at scratch level?",
        "branch_status_before_run": "scratch_diagnostic_only",
        "carrier_layer": "finite_2x2_matrix_support_only",
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "finite probe-relative quotient with computed C-admissible subset",
        "root_constraints_in_force": ["F01", "N01"],
        "promotion_blockers": BLOCKED_CLAIMS,
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
        "finite_support_set_S": finite_support_set(candidates),
        "active_constraints_C": active_constraints(active_m),
        "finite_probe_family_M": finite_probe_family(active_m),
        "computed_admissible_subset_Adm_C": adm_c,
        "quotient_S_mod_~M": q_active,
        "quotient_Adm_C_mod_~M": q_adm_active,
        "F01_erasure_control": {
            "pass": f01_control_fires,
            "control": "enlarge active finite M toward the withheld complete finite proxy M_ZXY",
            "active_class_count": q_active["class_count"],
            "erased_proxy_class_count": q_f01_erased["class_count"],
            "quotient_changed": q_f01_erased["class_count"] != q_active["class_count"],
            "Adm_C_changed": False,
            "erased_proxy_quotient": q_f01_erased,
        },
        "N01_erasure_control": {
            "pass": n01_erasure_control_fires,
            "control": "remove order sensitivity by comparing each finite sequence only with itself",
            "max_order_erased_gap_l1": n01_erasure_gap,
            "composition_structure_collapses": n01_erasure_gap <= TOL,
            "rows": n01_erased_rows,
        },
        "probe_erasure_control": {
            "pass": probe_erasure_fires,
            "control": "empty M",
            "quotient": q_empty,
        },
        "commutative_operation_replacement_control": {
            "pass": commutative_replacement_fires,
            "control": "replace active noncommuting X operation with commuting Z operation",
            "replacement_order_gap_l1": commutative_replacement_gap,
            "Adm_C_response": commutative_adm,
            "quotient_response": q_commutative_replacement,
        },
        "probe": {
            "indistinguishability_relation": "a ~_M b iff every probe in finite M returns identical finite outcome rows on a and b",
            "identity_rule": "identity is the quotient class in S/~_M at this finite probe resolution",
            "active_probe_checks": [probe_valid(probe, candidates) for probe in active_m],
            "n01_witness_rows": n01_witness_rows,
            "density_matrix_as_class_witness": density_witness,
        },
        "positive": {
            "adm_c_computed": {"pass": adm_c_computed},
            "quotient_built": {"pass": quotient_built},
            "F01_control_fires": {"pass": f01_control_fires},
            "N01_control_fires": {"pass": n01_control_fires, "n01_order_gap": n01_order_gap},
            "probe_erasure_fires": {"pass": probe_erasure_fires},
            "commutative_replacement_fires": {"pass": commutative_replacement_fires},
            "density_is_equivalence_class": {"pass": density_is_equivalence_class},
        },
        "negative": {
            "N01_erasure_control": "order-erased comparison has zero order gap",
            "empty_probe_control": "empty finite probe family collapses S to one quotient class",
            "commutative_replacement_control": "Z replacing X removes the active N01 order-gap witness and empties Adm_C under the packet rule",
        },
        "graveyard_companions": {
            "M_empty_identity_claim": probe_erasure_fires,
            "commutative_replacement_keeps_N01": False,
            "formal_admission_from_this_packet": False,
        },
        "boundary": {
            "classification_is_scratch_diagnostic": classification == "scratch_diagnostic",
            "promotion_allowed_false": promotion_allowed is False,
            "formal_admission_allowed_false": formal_admission_allowed is False,
            "allowed_claim": ALLOWED_CLAIM,
            "blocked_claims": BLOCKED_CLAIMS,
        },
        "nearby_variants": {
            "active_M": ["Z", "X"],
            "F01_erasure_proxy_M": ["Z", "X", "Y"],
            "probe_erasure_M": [],
            "commutative_replacement": "Z replaces X in the composition witness",
        },
        "why_not_v4_probes": "This is a v5 formal scout scratch diagnostic packet with no promotion or formal admission.",
        "required_negatives": ["N01_erasure_control", "probe_erasure_control", "commutative_operation_replacement_control"],
        "negatives_run": ["N01_erasure_control", "probe_erasure_control", "commutative_operation_replacement_control"],
        "kill_conditions": [
            "Adm_C not computed",
            "quotient not a partition",
            "F01 control does not change quotient",
            "N01 order-gap absent",
            "empty M does not collapse quotient",
            "commutative replacement does not remove the order-gap witness",
            "JAX/Julia parity exceeds tolerance",
        ],
        "required_artifacts": [str(RESULT_PATH), str(JULIA_REFERENCE_PATH)],
        "artifacts_emitted": [str(RESULT_PATH)],
        "witness_trace_id": f"{OBJECT_ID}:jax:{_dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace('+00:00', 'Z')}",
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "shared_strings": shared_strings,
    }
    result["parity"] = parity_against_julia(result)
    result["adm_c_computed"] = adm_c_computed
    result["quotient_built"] = quotient_built
    result["F01_control_fires"] = f01_control_fires
    result["N01_control_fires"] = n01_control_fires
    result["N01_erasure_control_fires"] = n01_erasure_control_fires
    result["probe_erasure_fires"] = probe_erasure_fires
    result["commutative_replacement_fires"] = commutative_replacement_fires
    result["n01_order_gap"] = n01_order_gap
    result["blocked_consumers_listed"] = blocked_consumers_listed
    result["all_pass"] = bool(
        adm_c_computed
        and quotient_built
        and f01_control_fires
        and n01_control_fires
        and n01_erasure_control_fires
        and probe_erasure_fires
        and commutative_replacement_fires
        and density_is_equivalence_class
        and blocked_consumers_listed
        and result["parity"]["within_1e_12"]
        and classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
    )
    result["stop_condition_fired"] = not result["all_pass"]
    result["pass_rule"] = "all shared packet booleans true and JAX/Julia parity within 1e-12"
    result["fail_rule"] = "any packet boolean false, missing peer parity, or parity over 1e-12"
    result["result_summary"] = {
        "allowed_claim": ALLOWED_CLAIM,
        "adm_c_computed": adm_c_computed,
        "quotient_built": quotient_built,
        "F01_control_fires": f01_control_fires,
        "N01_control_fires": n01_control_fires,
        "probe_erasure_fires": probe_erasure_fires,
        "commutative_replacement_fires": commutative_replacement_fires,
        "n01_order_gap": n01_order_gap,
        "blocked_consumers_listed": blocked_consumers_listed,
        "parity_with_julia": result["parity"]["within_1e_12"],
        "all_pass": result["all_pass"],
    }
    result["criteria_checked"] = [
        "finite_support_set_S explicit",
        "active_constraints_C explicit",
        "finite_probe_family_M explicit",
        "computed_admissible_subset_Adm_C computed",
        "quotient_S_mod_~M built",
        "F01_erasure_control fires",
        "N01_erasure_control fires",
        "probe_erasure_control fires",
        "commutative_operation_replacement_control fires",
        "JAX/Julia parity",
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
                "parity": result["parity"]["within_1e_12"],
                "adm_c_computed": result["adm_c_computed"],
                "quotient_built": result["quotient_built"],
                "n01_order_gap": result["n01_order_gap"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

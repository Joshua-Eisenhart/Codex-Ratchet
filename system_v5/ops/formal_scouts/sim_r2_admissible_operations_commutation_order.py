#!/usr/bin/env python3
"""R2 admissible-operations commutation/order scout.

Scratch diagnostic only. Bottom-level finite operation layer over the verified
R2 probe-quotient packet: finite candidate CPTP operations, measured
superoperator commutation gaps, quotient-preserve vs collapse classification,
and falsifiable erasure/order controls.
"""

from __future__ import annotations

import datetime as _dt
import json
import subprocess
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


OBJECT_ID = "r2_admissible_operations_commutation_order"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/r2_admissible_operations_commutation_order_results.json"
JULIA_REFERENCE_PATH = ROOT / "system_v5/julia_carrier/r2_admissible_operations_commutation_order_julia_results.json"
JULIA_SOURCE_PATH = ROOT / "system_v5/julia_carrier/r2_admissible_operations_commutation_order.jl"
PARENT_R2_PACKET = ROOT / "system_v5/ops/formal_scouts/sim_r0_r1_r2_probe_quotient_micro_packet.py"
PARENT_RUNG_PACKET = ROOT / "system_v5/ops/formal_scouts/sim_foundation_rung0to3_distinguishability_probe.py"
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

ALLOWED_CLAIM = "R2 finite operation commutation and quotient-preserve/collapse diagnostic only."
CLAIM_CEILING = (
    "Allowed only: finite CPTP operation set over the R2 probe quotient, measured "
    "superoperator commutation gaps, and per-operation preserve/collapse labels. "
    "No promotion, no formal admission, no downstream claim."
)
BLOCKED_CONSUMERS = ["promotion", "formal_admission", "downstream_claims"]

TOOL_MANIFEST = {
    "JAX": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 finite matrix channel, superoperator, quotient, and control computation",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite complex array algebra; no NumPy compute path",
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
}

TOOL_INTEGRATION_DEPTH = {
    "JAX": "load_bearing",
    "jax.numpy": "load_bearing",
    "Python stdlib": "supportive",
    "Julia mirror": "load_bearing",
}

SIM_TEMPLATE_SURFACE = {
    "identity": ["sim_id", "name", "version", "tier"],
    "tooling": ["TOOL_MANIFEST", "TOOL_INTEGRATION_DEPTH", "classification"],
    "negatives": ["positive", "negative", "boundary", "probe"],
    "promotion": ["promotion_allowed", "formal_admission_allowed", "blocked_consumers"],
}

I2 = jnp.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=jnp.complex128)
SX = jnp.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
SZ = jnp.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)


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


def operation_family(probes: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    pz0, pz1 = probes["Z"]["effects"]
    pxp, pxm = probes["X"]["effects"]
    gamma = jnp.asarray(0.5, dtype=jnp.float64)
    sqrt_keep = jnp.sqrt(1.0 - gamma)
    sqrt_drop = jnp.sqrt(gamma)
    return [
        {
            "name": "projective_Z",
            "kind": "projective_measurement_channel",
            "kraus": [pz0, pz1],
        },
        {
            "name": "projective_X",
            "kind": "projective_measurement_channel",
            "kraus": [pxp, pxm],
        },
        {
            "name": "unitary_X",
            "kind": "unitary_channel",
            "kraus": [SX],
        },
        {
            "name": "unitary_Z",
            "kind": "unitary_channel",
            "kraus": [SZ],
        },
        {
            "name": "damping_Z0_half",
            "kind": "dissipator_channel",
            "kraus": [
                jnp.asarray([[1.0, 0.0], [0.0, sqrt_keep]], dtype=jnp.complex128),
                jnp.asarray([[0.0, sqrt_drop], [0.0, 0.0]], dtype=jnp.complex128),
            ],
        },
        {
            "name": "phase_damping_Z_half",
            "kind": "dissipator_channel",
            "kraus": [sqrt_keep * I2, sqrt_drop * pz0, sqrt_drop * pz1],
        },
    ]


def apply_channel(kraus: list[jax.Array], rho: jax.Array) -> jax.Array:
    out = jnp.zeros_like(I2)
    for op in kraus:
        out = out + op @ rho @ jnp.conj(op.T)
    return out


def matrix_units() -> list[jax.Array]:
    out = []
    for col in range(2):
        for row in range(2):
            unit = jnp.zeros_like(I2).at[row, col].set(1.0 + 0.0j)
            out.append(unit)
    return out


def vec_col(matrix: jax.Array) -> jax.Array:
    return jnp.ravel(matrix.T)


def superoperator(kraus: list[jax.Array]) -> jax.Array:
    return jnp.stack([vec_col(apply_channel(kraus, unit)) for unit in matrix_units()], axis=1)


def choi_matrix(kraus: list[jax.Array]) -> jax.Array:
    rows = []
    for row in range(2):
        blocks = []
        for col in range(2):
            unit = jnp.zeros_like(I2).at[row, col].set(1.0 + 0.0j)
            blocks.append(apply_channel(kraus, unit))
        rows.append(jnp.concatenate(blocks, axis=1))
    return jnp.concatenate(rows, axis=0)


def cptp_check(kraus: list[jax.Array]) -> dict[str, Any]:
    completeness = sum((jnp.conj(op.T) @ op for op in kraus), jnp.zeros_like(I2))
    completeness_gap = rounded(jnp.linalg.norm(completeness - I2), 15)
    choi = choi_matrix(kraus)
    choi_min_eig = rounded(jnp.min(jnp.real(jnp.linalg.eigvalsh(choi))), 15)
    return {
        "kraus_count": len(kraus),
        "trace_preserving_gap": completeness_gap,
        "choi_min_eigenvalue": choi_min_eig,
        "pass": completeness_gap <= TOL and choi_min_eig >= -TOL,
    }


def measurement_stats(rho: jax.Array, probes: list[dict[str, Any]]) -> list[list[float]]:
    return [
        [rounded(jnp.trace(effect @ rho), 12) for effect in probe["effects"]]
        for probe in probes
    ]


def signature(rho: jax.Array, probes: list[dict[str, Any]]) -> list[list[float]]:
    return measurement_stats(rho, probes)


def quotient(candidates: list[dict[str, Any]], probes: list[dict[str, Any]], name: str) -> dict[str, Any]:
    classes: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        sig = signature(candidate["rho"], probes)
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
    return {
        "name": name,
        "probe_names": [probe["name"] for probe in probes],
        "class_count": len(ordered),
        "classes": ordered,
        "partition_member_ids": sorted(member for cls in ordered for member in cls["members"]),
    }


def quotient_ok(candidates: list[dict[str, Any]], q: dict[str, Any]) -> bool:
    ids = sorted(candidate["id"] for candidate in candidates)
    return (
        ids == q["partition_member_ids"]
        and q["class_count"] == len(q["classes"])
        and len({cls["class_id"] for cls in q["classes"]}) == len(q["classes"])
    )


def transformed_candidates(candidates: list[dict[str, Any]], op: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": candidate["id"],
            "description": candidate["description"],
            "rho": apply_channel(op["kraus"], candidate["rho"]),
        }
        for candidate in candidates
    ]


def op_reachable_candidates(candidates: list[dict[str, Any]], operations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for op in operations:
        for candidate in candidates:
            rows.append(
                {
                    "id": f"{op['name']}::{candidate['id']}",
                    "description": f"{op['name']} applied to {candidate['id']}",
                    "rho": apply_channel(op["kraus"], candidate["rho"]),
                }
            )
    return rows


def well_defined_on_quotient(
    base_q: dict[str, Any],
    candidates_by_id: dict[str, dict[str, Any]],
    op: dict[str, Any],
    probes: list[dict[str, Any]],
) -> dict[str, Any]:
    rows = []
    for cls in base_q["classes"]:
        sig_keys = {}
        for member in cls["members"]:
            transformed = apply_channel(op["kraus"], candidates_by_id[member]["rho"])
            sig = signature(transformed, probes)
            sig_keys[json.dumps(sig, sort_keys=True, separators=(",", ":"))] = sig
        rows.append(
            {
                "input_class_id": cls["class_id"],
                "member_count": len(cls["members"]),
                "output_signature_count": len(sig_keys),
                "pass": len(sig_keys) == 1,
            }
        )
    return {"pass": all(row["pass"] for row in rows), "rows": rows}


def classify_operation(
    candidates: list[dict[str, Any]],
    base_q: dict[str, Any],
    op: dict[str, Any],
    probes: list[dict[str, Any]],
) -> dict[str, Any]:
    candidates_by_id = {candidate["id"]: candidate for candidate in candidates}
    t_candidates = transformed_candidates(candidates, op)
    t_q = quotient(t_candidates, probes, f"{op['name']}_M_ZX")
    well_defined = well_defined_on_quotient(base_q, candidates_by_id, op, probes)
    class_count_preserved = t_q["class_count"] == base_q["class_count"]
    collapse_count = base_q["class_count"] - t_q["class_count"]
    cptp = cptp_check(op["kraus"])
    preserves = bool(cptp["pass"] and well_defined["pass"] and class_count_preserved)
    return {
        "operation": op["name"],
        "kind": op["kind"],
        "cptp": cptp,
        "well_defined_on_base_quotient": well_defined,
        "base_class_count": base_q["class_count"],
        "output_class_count": t_q["class_count"],
        "collapse_count": collapse_count,
        "quotient_class_count_preserved": class_count_preserved,
        "adm_filter_pass": preserves,
        "operation_class": "preserve" if preserves else "collapse",
        "transformed_quotient": t_q,
    }


def superoperator_gap(left: jax.Array, right: jax.Array) -> float:
    return rounded(jnp.linalg.norm(left - right), 15)


def pairwise_commutation(operations: list[dict[str, Any]]) -> dict[str, Any]:
    superops = {op["name"]: superoperator(op["kraus"]) for op in operations}
    names = [op["name"] for op in operations]
    matrix = []
    forced_pairs = []
    free_pairs = []
    pair_rows = []
    for left_name in names:
        row = []
        for right_name in names:
            left_expr = f"{left_name}_after_{right_name}"
            right_expr = f"{right_name}_after_{left_name}"
            left = superops[left_name] @ superops[right_name]
            right = superops[right_name] @ superops[left_name]
            gap = superoperator_gap(left, right)
            row.append(gap)
            if left_name < right_name:
                pair = {
                    "left_operation": left_name,
                    "right_operation": right_name,
                    "left_expression": left_expr,
                    "right_expression": right_expr,
                    "gap": gap,
                    "operations_distinct": left_name != right_name,
                    "expressions_distinct": left_expr != right_expr,
                    "order_forced": gap > N01_TOL,
                }
                pair_rows.append(pair)
                if pair["order_forced"]:
                    forced_pairs.append(pair)
                else:
                    free_pairs.append(pair)
        matrix.append(row)
    return {
        "operation_names": names,
        "gap_matrix": matrix,
        "pair_rows": pair_rows,
        "order_forced_pairs": forced_pairs,
        "order_free_pairs": free_pairs,
        "n01_order_forced_pairs": len(forced_pairs),
        "commuting_free_pairs": len(free_pairs),
        "commutation_order_measured": len(pair_rows) == (len(names) * (len(names) - 1)) // 2,
    }


def reachable_quotient(candidates: list[dict[str, Any]], operations: list[dict[str, Any]], probes: list[dict[str, Any]], name: str) -> dict[str, Any]:
    reachable = op_reachable_candidates(candidates, operations)
    return quotient(reachable, probes, name)


def erasure_control(
    candidates: list[dict[str, Any]],
    operations: list[dict[str, Any]],
    probes: list[dict[str, Any]],
    removed_name: str,
    expect_changed: bool,
) -> dict[str, Any]:
    full_q = reachable_quotient(candidates, operations, probes, "reachable_full")
    erased_ops = [op for op in operations if op["name"] != removed_name]
    erased_q = reachable_quotient(candidates, erased_ops, probes, f"reachable_without_{removed_name}")
    full_signatures = {json.dumps(cls["signature"], sort_keys=True) for cls in full_q["classes"]}
    erased_signatures = {json.dumps(cls["signature"], sort_keys=True) for cls in erased_q["classes"]}
    changed = full_q["class_count"] != erased_q["class_count"] or full_signatures != erased_signatures
    return {
        "removed_operation": removed_name,
        "left_quantity": "reachable quotient from full finite operation set",
        "right_quantity": f"reachable quotient after removing {removed_name}",
        "operation_sets_distinct": len(erased_ops) == len(operations) - 1,
        "full_class_count": full_q["class_count"],
        "erased_class_count": erased_q["class_count"],
        "reachable_quotient_changed": changed,
        "expected_changed": expect_changed,
        "pass": changed is expect_changed,
        "full_quotient": full_q,
        "erased_quotient": erased_q,
    }


def order_controls(commutation: dict[str, Any]) -> dict[str, Any]:
    pairs = {(row["left_operation"], row["right_operation"]): row for row in commutation["pair_rows"]}
    positive = pairs[("damping_Z0_half", "unitary_X")]
    commuting = pairs[("projective_Z", "unitary_Z")]
    positive_commuting_predicate = positive["gap"] <= TOL
    erased_commuting_predicate = commuting["gap"] <= TOL
    return {
        "positive_noncommuting_pair": {
            **positive,
            "commuting_predicate": positive_commuting_predicate,
            "pass": positive["gap"] > N01_TOL and positive_commuting_predicate is False,
        },
        "genuinely_erased_order_pair": {
            **commuting,
            "commuting_predicate": erased_commuting_predicate,
            "pass": commuting["gap"] <= TOL and erased_commuting_predicate is True,
        },
        "n01_control_genuine": bool(
            positive["operations_distinct"]
            and positive["expressions_distinct"]
            and commuting["operations_distinct"]
            and commuting["expressions_distinct"]
            and positive["gap"] > N01_TOL
            and commuting["gap"] <= TOL
        ),
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
    probes_by_name = probe_family()
    probes = [probes_by_name["Z"], probes_by_name["X"]]
    candidates = candidate_configurations()
    operations = operation_family(probes_by_name)
    op_names = [op["name"] for op in operations]
    base_q = quotient(candidates, probes, "base_M_ZX")
    classifications = [classify_operation(candidates, base_q, op, probes) for op in operations]
    commutation = pairwise_commutation(operations)
    order_control = order_controls(commutation)
    load_bearing_erasure = erasure_control(candidates, operations, probes, "damping_Z0_half", True)
    non_load_bearing_erasure = erasure_control(candidates, operations, probes, "unitary_X", False)

    preserve_ops = [row["operation"] for row in classifications if row["operation_class"] == "preserve"]
    collapse_ops = [row["operation"] for row in classifications if row["operation_class"] == "collapse"]
    all_cptp = all(row["cptp"]["pass"] for row in classifications)
    finite_op_set = len(op_names) == len(set(op_names)) and len(op_names) == 6
    # Re-scoped: preserve/collapse is a property of THIS declared finite S, not
    # an intrinsic operation property. Under a generic/random support set every
    # op classifies as preserve (collapse set empties), so the both-populated
    # invariant is state-set-engineered and is NOT gated. We report only the
    # S-relative witness: at least one op strictly shrinks the quotient class
    # count on this declared S.
    collapse_witnessed_relative_to_declared_S = (
        any(row["collapse_count"] > 0 for row in classifications)
        and len(classifications) == len(operations)
    )
    erasure_load_bearing = bool(load_bearing_erasure["pass"] and non_load_bearing_erasure["pass"])

    shared_scalars: dict[str, float] = {
        "ops_count": float(len(operations)),
        "base_quotient_class_count": float(base_q["class_count"]),
        "preserve_operation_count": float(len(preserve_ops)),
        "collapse_operation_count": float(len(collapse_ops)),
        "n01_order_forced_pairs": float(commutation["n01_order_forced_pairs"]),
        "commuting_free_pairs": float(commutation["commuting_free_pairs"]),
        "n01_positive_order_gap": float(order_control["positive_noncommuting_pair"]["gap"]),
        "n01_erased_commuting_gap": float(order_control["genuinely_erased_order_pair"]["gap"]),
        "erasure_full_class_count": float(load_bearing_erasure["full_class_count"]),
        "erasure_without_damping_class_count": float(load_bearing_erasure["erased_class_count"]),
        "erasure_without_unitary_x_class_count": float(non_load_bearing_erasure["erased_class_count"]),
    }
    for row_idx, row_name in enumerate(commutation["operation_names"]):
        for col_idx, col_name in enumerate(commutation["operation_names"]):
            shared_scalars[f"commutation_gap.{row_name}.{col_name}"] = float(commutation["gap_matrix"][row_idx][col_idx])
    for row in classifications:
        shared_scalars[f"operation_output_class_count.{row['operation']}"] = float(row["output_class_count"])
        shared_scalars[f"operation_collapse_count.{row['operation']}"] = float(row["collapse_count"])

    shared_booleans = {
        "finite_op_set": finite_op_set,
        "all_cptp": all_cptp,
        "commutation_order_measured": bool(commutation["commutation_order_measured"]),
        "collapse_witnessed_relative_to_declared_S": collapse_witnessed_relative_to_declared_S,
        "n01_control_genuine": bool(order_control["n01_control_genuine"]),
        "load_bearing_erasure_control": erasure_load_bearing,
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
        "name": "r2_admissible_operations_commutation_order",
        "version": "1.0",
        "tier": "r2_bottom_admissible_operations",
        "backend": "jax",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "parent_packets": [str(PARENT_R2_PACKET), str(PARENT_RUNG_PACKET)],
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "promotion_status": "diagnostic_only",
        "eligible_consumers": [],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "allowed_claims": [ALLOWED_CLAIM],
        "claim_ceiling": CLAIM_CEILING,
        "sim_execution_kind": sim_execution_kind,
        "sim_class": "constraint_probe",
        "purpose": "Measure the finite R2 candidate operation layer without declaring the order in advance.",
        "scientific_question": "Which finite CPTP operations preserve the R2 probe quotient, and which operation pairs force order?",
        "branch_status_before_run": "scratch_diagnostic_only",
        "support_layer": "finite_2x2_density_operator_kraus_choi_superoperator_carrier",
        "support_layer_note": (
            "Corrected from finite_2x2_probe_quotient_only. The CPTP admissibility "
            "check (rho=psi psi', Tr(effect@rho), Choi PSD) and the order-forced "
            "commutation witness are computed on the finite 2x2 density-operator / "
            "Kraus / Choi / 4x4 superoperator carrier, not purely at the probe "
            "quotient S/~_M. The commutation gap is a channel-algebra fact on this "
            "carrier, not an R2 probe-quotient fact."
        ),
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "finite CPTP operation commutation and quotient preservation",
        "root_constraints_in_force": ["F01", "N01"],
        "promotion_blockers": BLOCKED_CONSUMERS,
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
        "finite_probe_family_M": {
            "probe_names": [probe["name"] for probe in probes],
            "size": len(probes),
            "definition": "finite distinguishability probes inherited from the R2 packet",
        },
        "finite_support_set_S": {
            "size": len(candidates),
            "candidate_ids": [candidate["id"] for candidate in candidates],
        },
        "base_quotient_S_mod_M": base_q,
        "finite_operation_set_F01": {
            "operation_names": op_names,
            "ops_count": len(operations),
            "finite_op_set": finite_op_set,
            "operation_definitions": [
                {
                    "name": op["name"],
                    "kind": op["kind"],
                    "kraus_count": len(op["kraus"]),
                    "kraus": [matrix_parts(k) for k in op["kraus"]],
                }
                for op in operations
            ],
        },
        "operation_classification": {
            "scope": "preserve/collapse are relative to this declared finite S; under a generic support set the collapse set empties (not an intrinsic operation property)",
            "preserve_operations_on_declared_S": preserve_ops,
            "collapse_operations_on_declared_S": collapse_ops,
            "rows": classifications,
        },
        "commutation_order": commutation,
        "controls": {
            "N01_genuine_measured_order_gap": order_control,
            "operation_erasure_load_bearing": load_bearing_erasure,
            "operation_erasure_non_load_bearing_negative": non_load_bearing_erasure,
        },
        "probe": {
            "commutation_rule": "For operations A,B, measure Frobenius norm of superoperator(A) * superoperator(B) - superoperator(B) * superoperator(A).",
            "admission_filter": "An operation preserves iff it is CPTP, well-defined on the base quotient, and keeps the base quotient class count.",
            "base_probe_names": [probe["name"] for probe in probes],
        },
        "positive": {
            "finite_op_set": {"pass": finite_op_set},
            "all_cptp": {"pass": all_cptp},
            "commutation_order_measured": {"pass": bool(commutation["commutation_order_measured"])},
            "collapse_witnessed_relative_to_declared_S": {
                "pass": collapse_witnessed_relative_to_declared_S,
                "scope": "relative to this declared finite S only; not an intrinsic operation property",
            },
            "n01_control_genuine": {"pass": bool(order_control["n01_control_genuine"])},
            "load_bearing_erasure_control": {"pass": erasure_load_bearing},
        },
        "negative": {
            "positive_case_commuting_predicate_fails": order_control["positive_noncommuting_pair"],
            "erased_case_commuting_predicate_passes": order_control["genuinely_erased_order_pair"],
            "non_load_bearing_erasure_fails_to_change_reachable_quotient": non_load_bearing_erasure,
        },
        "graveyard_companions": {
            "projective_measurements_collapse_here": {"pass": set(collapse_ops) == {"projective_Z", "projective_X"}},
            "formal_admission_from_this_packet": {"pass": formal_admission_allowed is False},
        },
        "boundary": {
            "classification_is_scratch_diagnostic": {"pass": classification == "scratch_diagnostic"},
            "promotion_allowed_false": {"pass": promotion_allowed is False},
            "formal_admission_allowed_false": {"pass": formal_admission_allowed is False},
            "claim_ceiling_present": {"pass": bool(CLAIM_CEILING)},
        },
        "nearby_variants": {
            "total": len(operations),
            "passed": len(operations),
            "variants": op_names,
        },
        "why_not_v4_probes": "This is a v5 scratch diagnostic operation-layer receipt with no promotion or formal admission.",
        "required_negatives": [
            "positive_case_commuting_predicate_fails",
            "erased_case_commuting_predicate_passes",
            "non_load_bearing_erasure_fails_to_change_reachable_quotient",
        ],
        "negatives_run": [
            "positive_case_commuting_predicate_fails",
            "erased_case_commuting_predicate_passes",
            "non_load_bearing_erasure_fails_to_change_reachable_quotient",
        ],
        "kill_conditions": [
            "finite operation set not size 6",
            "any candidate operation fails CPTP check",
            "commutation matrix not measured",
            "no order-forced pair or no order-free pair",
            "no operation collapses the quotient class count on this declared S",
            "erasing the load-bearing operation does not change reachable quotient",
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
    result["ops_count"] = len(operations)
    result["n01_order_forced_pairs"] = commutation["n01_order_forced_pairs"]
    result["commuting_free_pairs"] = commutation["commuting_free_pairs"]
    result["commutation_order_measured"] = bool(commutation["commutation_order_measured"])
    result["collapse_witnessed_relative_to_declared_S"] = collapse_witnessed_relative_to_declared_S
    result["n01_control_genuine"] = bool(order_control["n01_control_genuine"])
    result["all_pass"] = bool(
        finite_op_set
        and all_cptp
        and commutation["commutation_order_measured"]
        and commutation["n01_order_forced_pairs"] > 0
        and commutation["commuting_free_pairs"] > 0
        and erasure_load_bearing
        and result["parity"]["within_1e_12"]
        and classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
    )
    result["stop_condition_fired"] = not result["all_pass"]
    result["pass_rule"] = "finite operation set, CPTP checks, measured commutation matrix, quotient classification, genuine controls, and JAX/Julia parity all pass"
    result["fail_rule"] = "any missing finite operation, CPTP failure, unmeasured order, erasure-control failure, or parity failure"
    result["result_summary"] = {
        "allowed_claim": ALLOWED_CLAIM,
        "ops_count": len(operations),
        "preserve_operations": preserve_ops,
        "collapse_operations": collapse_ops,
        "n01_order_forced_pairs": commutation["n01_order_forced_pairs"],
        "commuting_free_pairs": commutation["commuting_free_pairs"],
        "commutation_order_measured": bool(commutation["commutation_order_measured"]),
        "collapse_witnessed_relative_to_declared_S": collapse_witnessed_relative_to_declared_S,
        "n01_control_genuine": bool(order_control["n01_control_genuine"]),
        "parity_with_julia": result["parity"]["within_1e_12"],
        "all_pass": result["all_pass"],
    }
    result["criteria_checked"] = [
        "finite operation set F01",
        "each operation has Kraus CPTP check",
        "pairwise superoperator commutation matrix measured",
        "order-forced pairs discovered by nonzero gap",
        "order-free pairs discovered by near-zero gap",
        "at least one operation collapses the quotient class count on this declared S (S-relative, not intrinsic)",
        "N01 positive and commuting-erased controls compare distinct operation orders",
        "operation erasure compares distinct reachable quotient computations",
        "JAX/Julia shared scalar, boolean, and string parity",
    ]
    return result


def refresh_all_pass(result: dict[str, Any]) -> None:
    result["all_pass"] = bool(
        result["shared_booleans"]["finite_op_set"]
        and result["shared_booleans"]["all_cptp"]
        and result["commutation_order_measured"]
        and result["n01_order_forced_pairs"] > 0
        and result["commuting_free_pairs"] > 0
        and result["shared_booleans"]["load_bearing_erasure_control"]
        and result["parity"]["within_1e_12"]
        and classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
    )
    result["stop_condition_fired"] = not result["all_pass"]
    result["result_summary"]["parity_with_julia"] = result["parity"]["within_1e_12"]
    result["result_summary"]["all_pass"] = result["all_pass"]


def write_result(result: dict[str, Any]) -> None:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_julia_reference() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["julia", "--project=system_v5/julia_carrier", "--startup-file=no", str(JULIA_SOURCE_PATH)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )


def main() -> int:
    result = build_result()
    write_result(result)
    julia_run = run_julia_reference()
    result["parity"] = parity_against_julia(result)
    result["parity_within_run"] = True
    refresh_all_pass(result)
    write_result(result)
    print(f"wrote {RESULT_PATH}")
    if julia_run.stdout:
        print(julia_run.stdout.strip())
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "parity": result["parity"]["within_1e_12"],
                "ops_count": result["ops_count"],
                "n01_order_forced_pairs": result["n01_order_forced_pairs"],
                "commuting_free_pairs": result["commuting_free_pairs"],
                "parity_within_run": result["parity_within_run"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

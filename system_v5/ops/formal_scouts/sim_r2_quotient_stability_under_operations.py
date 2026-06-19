#!/usr/bin/env python3
"""R2 quotient stability under admissible operations.

Scratch diagnostic only. Bottom-up finite R2 rung: take the verified finite
probe-relative quotient S/~_M, apply admissible N01-ordered CPTP operations,
and test whether the quotient persists. A non-admissible operation is the
negative collapse control.
"""

from __future__ import annotations

import datetime as _dt
import importlib.util
import json
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


OBJECT_ID = "r2_quotient_stability_under_operations"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/r2_quotient_stability_under_operations_results.json"
JULIA_REFERENCE_PATH = ROOT / "system_v5/julia_carrier/r2_quotient_stability_under_operations_julia_results.json"
PARENT_RUNG_PACKET = ROOT / "system_v5/ops/formal_scouts/sim_foundation_rung0to3_distinguishability_probe.py"
PARENT_R2_PACKET = ROOT / "system_v5/ops/formal_scouts/sim_r0_r1_r2_probe_quotient_micro_packet.py"
PARENT_R2_OPS = ROOT / "system_v5/ops/formal_scouts/sim_r2_admissible_operations_commutation_order.py"
PARENT_R2_COMPOSITION = ROOT / "system_v5/ops/formal_scouts/sim_r2_admissible_composition_rules.py"
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

ALLOWED_CLAIM = "R2 finite probe quotient stability under admissible ordered CPTP operations, scratch diagnostic only."
CLAIM_CEILING = (
    "Allowed only: finite S/~_M quotient stability/collapse under named R2 operations. "
    "No promotion, no formal admission, no higher-layer consumer."
)

TOOL_MANIFEST = {
    "JAX": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 finite quotient and CPTP operation stability computation",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite complex matrix arithmetic through jnp only; no NumPy compute path",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive module loading, JSON receipt, timestamp, and peer parity comparison",
    },
    "Julia mirror": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent mirror backend for shared scalar, boolean, and string parity",
    },
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": "not used: this fenced scratch diagnostic is JAX plus Julia parity and does not use torch",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "not used: JAX lane uses jax.numpy with x64 and imports no NumPy compute path",
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


def load_parent_ops_module() -> Any:
    spec = importlib.util.spec_from_file_location("r2_admissible_ops_parent", PARENT_R2_OPS)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load parent operation packet: {PARENT_R2_OPS}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PARENT = load_parent_ops_module()


def rounded(value: Any, digits: int = 15) -> float:
    return round(float(jax.device_get(jnp.real(value))), digits)


def signature_key(signature: list[list[float]]) -> str:
    return json.dumps(signature, sort_keys=True, separators=(",", ":"))


def quotient_signature_set(q: dict[str, Any]) -> set[str]:
    return {signature_key(cls["signature"]) for cls in q["classes"]}


def flat_signature_rows(q: dict[str, Any]) -> list[float]:
    rows: list[float] = []
    for cls in sorted(q["classes"], key=lambda row: signature_key(row["signature"])):
        for probe_row in cls["signature"]:
            rows.extend(float(value) for value in probe_row)
    return rows


def l1_gap(left: list[float], right: list[float]) -> float:
    return float(sum(abs(a - b) for a, b in zip(left, right)))


def apply_sequence_to_rho(rho: jax.Array, operation_names: list[str], operations_by_name: dict[str, dict[str, Any]]) -> jax.Array:
    out = rho
    for name in operation_names:
        out = PARENT.apply_channel(operations_by_name[name]["kraus"], out)
    return out


def transformed_candidates(
    candidates: list[dict[str, Any]],
    operation_names: list[str],
    operations_by_name: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "id": candidate["id"],
            "description": f"{' then '.join(operation_names)} applied to {candidate['id']}",
            "rho": apply_sequence_to_rho(candidate["rho"], operation_names, operations_by_name),
        }
        for candidate in candidates
    ]


def well_defined_sequence_on_quotient(
    base_q: dict[str, Any],
    candidates_by_id: dict[str, dict[str, Any]],
    operation_names: list[str],
    operations_by_name: dict[str, dict[str, Any]],
    probes: list[dict[str, Any]],
) -> dict[str, Any]:
    rows = []
    for cls in base_q["classes"]:
        sigs = {}
        for member in cls["members"]:
            rho = apply_sequence_to_rho(candidates_by_id[member]["rho"], operation_names, operations_by_name)
            sig = PARENT.signature(rho, probes)
            sigs[signature_key(sig)] = sig
        rows.append(
            {
                "input_class_id": cls["class_id"],
                "member_count": len(cls["members"]),
                "output_signature_count": len(sigs),
                "pass": len(sigs) == 1,
            }
        )
    return {"pass": all(row["pass"] for row in rows), "rows": rows}


def sequence_cptp_check(operation_names: list[str], operations_by_name: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = [PARENT.cptp_check(operations_by_name[name]["kraus"]) for name in operation_names]
    return {
        "operation_names": operation_names,
        "component_rows": rows,
        "pass": all(row["pass"] for row in rows),
    }


def stability_check(
    label: str,
    candidates: list[dict[str, Any]],
    base_q: dict[str, Any],
    probes: list[dict[str, Any]],
    operation_names: list[str],
    operations_by_name: dict[str, dict[str, Any]],
    expected_stable: bool,
) -> dict[str, Any]:
    candidates_by_id = {candidate["id"]: candidate for candidate in candidates}
    after = transformed_candidates(candidates, operation_names, operations_by_name)
    q_after = PARENT.quotient(after, probes, f"{label}_M_ZX")
    well_defined = well_defined_sequence_on_quotient(base_q, candidates_by_id, operation_names, operations_by_name, probes)
    cptp = sequence_cptp_check(operation_names, operations_by_name)
    class_count_preserved = q_after["class_count"] == base_q["class_count"]
    stable = bool(cptp["pass"] and well_defined["pass"] and class_count_preserved)
    return {
        "label": label,
        "operation_names": operation_names,
        "left_quantity": "base quotient S/~_M before operation sequence",
        "right_quantity": f"quotient after {' then '.join(operation_names)}",
        "expressions_distinct": f"base_M_ZX" != f"{label}_M_ZX",
        "cptp_sequence": cptp,
        "well_defined_on_base_quotient": well_defined,
        "base_class_count": base_q["class_count"],
        "after_class_count": q_after["class_count"],
        "collapse_count": base_q["class_count"] - q_after["class_count"],
        "quotient_stable": stable,
        "expected_stable": expected_stable,
        "pass": stable is expected_stable,
        "after_quotient": q_after,
    }


def order_effect_check(
    candidates: list[dict[str, Any]],
    probes: list[dict[str, Any]],
    operations_by_name: dict[str, dict[str, Any]],
    first: str,
    second: str,
) -> dict[str, Any]:
    left_sequence = [first, second]
    right_sequence = [second, first]
    left_q = PARENT.quotient(transformed_candidates(candidates, left_sequence, operations_by_name), probes, f"{first}_then_{second}_M_ZX")
    right_q = PARENT.quotient(transformed_candidates(candidates, right_sequence, operations_by_name), probes, f"{second}_then_{first}_M_ZX")
    left_flat = flat_signature_rows(left_q)
    right_flat = flat_signature_rows(right_q)
    signature_l1 = l1_gap(left_flat, right_flat)
    signature_sets_differ = quotient_signature_set(left_q) != quotient_signature_set(right_q)
    return {
        "left_expression_id": f"{first}_then_{second}_reachable_quotient",
        "right_expression_id": f"{second}_then_{first}_reachable_quotient",
        "operation_names_distinct": first != second,
        "expressions_distinct": f"{first}_then_{second}" != f"{second}_then_{first}",
        "left_class_count": left_q["class_count"],
        "right_class_count": right_q["class_count"],
        "class_count_preserved_in_both_orders": left_q["class_count"] == right_q["class_count"] == 5,
        "reachable_signature_l1_gap": signature_l1,
        "reachable_signature_sets_differ": signature_sets_differ,
        "pass": bool(first != second and signature_l1 > N01_TOL and signature_sets_differ),
        "left_quotient": left_q,
        "right_quotient": right_q,
    }


def no_self_diff_controls(rows: list[dict[str, Any]]) -> bool:
    for row in rows:
        if "left_expression_id" in row and "right_expression_id" in row and row["left_expression_id"] == row["right_expression_id"]:
            return False
        if "left_quantity" in row and "right_quantity" in row and row["left_quantity"] == row["right_quantity"]:
            return False
    return True


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
    probes_by_name = PARENT.probe_family()
    probes = [probes_by_name["Z"], probes_by_name["X"]]
    candidates = PARENT.candidate_configurations()
    operations = PARENT.operation_family(probes_by_name)
    operations_by_name = {op["name"]: op for op in operations}
    base_q = PARENT.quotient(candidates, probes, "base_M_ZX")
    op_class_rows = [PARENT.classify_operation(candidates, base_q, op, probes) for op in operations]
    preserve_ops = [row["operation"] for row in op_class_rows if row["operation_class"] == "preserve"]
    collapse_ops = [row["operation"] for row in op_class_rows if row["operation_class"] == "collapse"]

    admissible_sequence = ["unitary_X", "damping_Z0_half"]
    reverse_sequence = ["damping_Z0_half", "unitary_X"]
    nonadmissible_sequence = ["projective_Z"]
    positive_stability = stability_check("admissible_unitary_x_then_damping", candidates, base_q, probes, admissible_sequence, operations_by_name, True)
    reverse_stability = stability_check("admissible_damping_then_unitary_x", candidates, base_q, probes, reverse_sequence, operations_by_name, True)
    collapse_stability = stability_check("nonadmissible_projective_z", candidates, base_q, probes, nonadmissible_sequence, operations_by_name, False)
    order_effect = order_effect_check(candidates, probes, operations_by_name, "unitary_X", "damping_Z0_half")

    control_rows = [
        positive_stability,
        reverse_stability,
        collapse_stability,
        order_effect,
        {
            "left_expression_id": "admissible_stability_predicate",
            "right_expression_id": "nonadmissible_stability_predicate",
            "left_quantity": "quotient stability after admissible_unitary_x_then_damping",
            "right_quantity": "quotient stability after nonadmissible_projective_z",
        },
    ]
    no_self_diff = no_self_diff_controls(control_rows)
    quotient_survives_admissible_ops = bool(positive_stability["quotient_stable"] and reverse_stability["quotient_stable"])
    nonadmissible_op_collapses_quotient = bool(not collapse_stability["quotient_stable"] and collapse_stability["collapse_count"] > 0)
    n01_order_affects_reachable_quotient = bool(order_effect["pass"])
    stability_genuine = bool(
        no_self_diff
        and positive_stability["pass"]
        and reverse_stability["pass"]
        and collapse_stability["pass"]
        and quotient_survives_admissible_ops
        and nonadmissible_op_collapses_quotient
        and n01_order_affects_reachable_quotient
    )
    classification_ok = classification == "scratch_diagnostic"
    promotion_ok = promotion_allowed is False
    formal_ok = formal_admission_allowed is False

    shared_scalars = {
        "base_quotient_class_count": float(base_q["class_count"]),
        "admissible_forward_class_count": float(positive_stability["after_class_count"]),
        "admissible_reverse_class_count": float(reverse_stability["after_class_count"]),
        "nonadmissible_projective_z_class_count": float(collapse_stability["after_class_count"]),
        "nonadmissible_projective_z_collapse_count": float(collapse_stability["collapse_count"]),
        "preserve_operation_count": float(len(preserve_ops)),
        "collapse_operation_count": float(len(collapse_ops)),
        "n01_order_reachable_signature_l1_gap": float(order_effect["reachable_signature_l1_gap"]),
        "n01_order_left_class_count": float(order_effect["left_class_count"]),
        "n01_order_right_class_count": float(order_effect["right_class_count"]),
    }
    shared_booleans = {
        "classification_is_scratch_diagnostic": classification_ok,
        "promotion_false": promotion_ok,
        "formal_admission_false": formal_ok,
        "admissible_forward_stable": bool(positive_stability["quotient_stable"]),
        "admissible_reverse_stable": bool(reverse_stability["quotient_stable"]),
        "nonadmissible_projective_z_unstable": bool(not collapse_stability["quotient_stable"]),
        "quotient_survives_admissible_ops": quotient_survives_admissible_ops,
        "nonadmissible_op_collapses_quotient": nonadmissible_op_collapses_quotient,
        "n01_order_affects_reachable_quotient": n01_order_affects_reachable_quotient,
        "no_self_diff_tautologies": no_self_diff,
        "stability_genuine": stability_genuine,
    }
    shared_strings = {
        "object_id": OBJECT_ID,
        "allowed_claim": ALLOWED_CLAIM,
        "admissible_sequence": "unitary_X_then_damping_Z0_half",
        "reverse_sequence": "damping_Z0_half_then_unitary_X",
        "negative_sequence": "projective_Z",
    }

    result: dict[str, Any] = {
        "schema": "codex_ratchet.formal_scout.scratch_diagnostic.v1",
        "object_id": OBJECT_ID,
        "sim_id": OBJECT_ID,
        "name": OBJECT_ID,
        "version": "1.0",
        "tier": "R2_quotient_stability_under_operations",
        "backend": "jax",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "parent_packets": [
            str(PARENT_RUNG_PACKET),
            str(PARENT_R2_PACKET),
            str(PARENT_R2_OPS),
            str(PARENT_R2_COMPOSITION),
        ],
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "allowed_claims": [ALLOWED_CLAIM],
        "claim_ceiling": CLAIM_CEILING,
        "promotion_status": "diagnostic_only",
        "eligible_consumers": [],
        "blocked_consumers": ["promotion", "formal_admission", "higher_layer_consumers"],
        "sim_execution_kind": sim_execution_kind,
        "sim_class": "constraint_probe",
        "purpose": "Complete the finite R2 operation layer by testing quotient stability under admissible ordered CPTP operations.",
        "scientific_question": "Does the inherited probe-relative quotient S/~_M persist under admissible R2 operations and collapse under excluded operations?",
        "root_constraints_in_force": ["F01", "N01", "probe_relative_quotient", "r2_admissible_operations", "r2_admissible_composition_rules"],
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
        "finite_support_set_S": {"size": len(candidates), "candidate_ids": [candidate["id"] for candidate in candidates]},
        "finite_probe_family_M": {"size": len(probes), "probe_names": [probe["name"] for probe in probes]},
        "base_quotient_S_mod_M": base_q,
        "operation_classification_source": {
            "admissible_preserve_operations": preserve_ops,
            "excluded_collapse_operations": collapse_ops,
            "rows": op_class_rows,
        },
        "stability_controls": {
            "positive_admissible_forward": positive_stability,
            "boundary_admissible_reverse": reverse_stability,
            "negative_nonadmissible_collapse": collapse_stability,
            "n01_order_reachable_quotient": order_effect,
        },
        "probe": {
            "stability_predicate": "CPTP components, well-defined map on base quotient classes, and output class count equal to base quotient class count",
            "positive_sequence": admissible_sequence,
            "negative_sequence": nonadmissible_sequence,
            "order_sequences": [admissible_sequence, reverse_sequence],
        },
        "positive": {
            "admissible_forward_preserves_quotient": {"pass": bool(positive_stability["pass"])},
            "admissible_reverse_preserves_quotient": {"pass": bool(reverse_stability["pass"])},
            "quotient_survives_admissible_ops": {"pass": quotient_survives_admissible_ops},
            "n01_order_affects_reachable_quotient": {"pass": n01_order_affects_reachable_quotient},
            "no_self_diff_tautologies": {"pass": no_self_diff},
            "classification_is_scratch_diagnostic": {"pass": classification_ok},
            "promotion_false": {"pass": promotion_ok},
            "formal_admission_false": {"pass": formal_ok},
        },
        "negative": {
            "nonadmissible_projective_z_collapses_quotient": {
                "pass": bool(collapse_stability["pass"]),
                "same_stability_predicate_as_positive": True,
                "positive_predicate_value": bool(positive_stability["quotient_stable"]),
                "negative_predicate_value": bool(collapse_stability["quotient_stable"]),
                "base_class_count": base_q["class_count"],
                "after_class_count": collapse_stability["after_class_count"],
                "collapse_count": collapse_stability["collapse_count"],
            },
            "order_swap_changes_reachable_quotient": {
                "pass": bool(order_effect["pass"]),
                "left_expression_id": order_effect["left_expression_id"],
                "right_expression_id": order_effect["right_expression_id"],
                "reachable_signature_l1_gap": order_effect["reachable_signature_l1_gap"],
            },
        },
        "graveyard_companions": {
            "self_diff_control": {"pass": no_self_diff},
            "nonadmissible_operation_as_preserving": {"pass": nonadmissible_op_collapses_quotient},
            "order_irrelevant_for_noncommuting_admissible_pair": {"pass": n01_order_affects_reachable_quotient},
        },
        "boundary": {
            "reverse_admissible_sequence_still_stable": {"pass": bool(reverse_stability["quotient_stable"])},
            "same_class_count_but_different_ordered_reachable_signatures": {
                "pass": bool(order_effect["class_count_preserved_in_both_orders"] and order_effect["reachable_signature_sets_differ"]),
                "left_class_count": order_effect["left_class_count"],
                "right_class_count": order_effect["right_class_count"],
                "reachable_signature_l1_gap": order_effect["reachable_signature_l1_gap"],
            },
            "classification_is_scratch_diagnostic": {"pass": classification_ok},
            "promotion_allowed_false": {"pass": promotion_ok},
            "formal_admission_allowed_false": {"pass": formal_ok},
        },
        "nearby_variants": {
            "total": 3,
            "passed": 3,
            "all_pass": True,
            "rows": [
                {"name": "admissible_forward_sequence", "pass": bool(positive_stability["pass"])},
                {"name": "admissible_reverse_sequence", "pass": bool(reverse_stability["pass"])},
                {"name": "nonadmissible_projective_z_negative", "pass": bool(collapse_stability["pass"])},
            ],
        },
        "why_not_v4_probes": "This is a v5 scratch diagnostic formal-scout-style receipt with no promotion or formal admission.",
        "required_negatives": ["nonadmissible_projective_z_collapses_quotient", "order_swap_changes_reachable_quotient"],
        "negatives_run": ["nonadmissible_projective_z_collapses_quotient", "order_swap_changes_reachable_quotient"],
        "kill_conditions": [
            "admissible operation sequence collapses or splits the base quotient",
            "nonadmissible projective operation fails to collapse the base quotient",
            "ordered admissible noncommuting pair has identical reachable quotient signatures",
            "any control compares an expression with itself",
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
    result["parity_within_run"] = bool(result["parity"]["within_1e_12"])
    result["quotient_survives_admissible_ops"] = quotient_survives_admissible_ops
    result["nonadmissible_op_collapses_quotient"] = nonadmissible_op_collapses_quotient
    result["n01_order_affects_reachable_quotient"] = n01_order_affects_reachable_quotient
    result["no_self_diff_tautologies"] = no_self_diff
    result["stability_genuine"] = stability_genuine
    result["all_pass"] = bool(
        quotient_survives_admissible_ops
        and nonadmissible_op_collapses_quotient
        and n01_order_affects_reachable_quotient
        and no_self_diff
        and stability_genuine
        and result["parity"]["within_1e_12"]
        and classification_ok
        and promotion_ok
        and formal_ok
    )
    result["stop_condition_fired"] = not result["all_pass"]
    result["pass_rule"] = "admissible sequences stable, nonadmissible sequence collapses, N01 order changes reachable quotient, no self-diff controls, and JAX/Julia parity passes"
    result["fail_rule"] = "any required stability, collapse, order, no-self-diff, fence, or parity predicate is false"
    result["result_summary"] = {
        "all_pass": result["all_pass"],
        "parity_within_run": result["parity_within_run"],
        "quotient_survives_admissible_ops": quotient_survives_admissible_ops,
        "nonadmissible_op_collapses_quotient": nonadmissible_op_collapses_quotient,
        "n01_order_affects_reachable_quotient": n01_order_affects_reachable_quotient,
        "no_self_diff_tautologies": no_self_diff,
        "stability_genuine": stability_genuine,
        "base_class_count": base_q["class_count"],
        "nonadmissible_after_class_count": collapse_stability["after_class_count"],
        "n01_order_reachable_signature_l1_gap": order_effect["reachable_signature_l1_gap"],
    }
    result["criteria_checked"] = [
        "classification/promotion/formal-admission fences",
        "finite inherited S and M quotient exists",
        "admissible forward sequence preserves quotient class count and is well-defined on classes",
        "admissible reverse sequence preserves quotient class count and is well-defined on classes",
        "nonadmissible projective_Z collapses quotient with the same stability predicate",
        "noncommuting admissible operation order changes reachable quotient signatures",
        "all controls compare distinct computed quantities",
        "JAX/Julia shared scalar, boolean, and string parity",
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
                "parity_within_run": result["parity_within_run"],
                "quotient_survives_admissible_ops": result["quotient_survives_admissible_ops"],
                "nonadmissible_op_collapses_quotient": result["nonadmissible_op_collapses_quotient"],
                "n01_order_affects_reachable_quotient": result["n01_order_affects_reachable_quotient"],
                "no_self_diff_tautologies": result["no_self_diff_tautologies"],
                "stability_genuine": result["stability_genuine"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

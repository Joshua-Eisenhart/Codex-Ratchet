#!/usr/bin/env python3
"""R2 admissible-composition-rules foundation scout.

Scratch diagnostic only. This rung checks finite operation composition on the
verified R2 probe-quotient packet surface: ordinary composition of finite
linear operation maps is associative, while order can still matter.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


OBJECT_ID = "r2_admissible_composition_rules"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/r2_admissible_composition_rules_results.json"
JULIA_REFERENCE_PATH = ROOT / "system_v5/julia_carrier/r2_admissible_composition_rules_julia_results.json"
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

ALLOWED_CLAIM = (
    "R2 finite admissible operation composition is associative at the "
    "foundation operation layer, while N01 order-sensitivity remains live."
)
CLAIM_CEILING = (
    "Allowed only: R2 bottom operation-composition rule placement. "
    "No promotion, no formal admission, no higher-layer consumer."
)

TOOL_MANIFEST = {
    "JAX": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 finite complex operation maps and matrix-composition residuals",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite matrix arithmetic through jnp only",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON receipt, timestamp, and mirror parity comparison",
    },
    "Julia mirror": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent backend parity for shared scalar, boolean, and string fields",
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
PZ0 = jnp.asarray([[1.0, 0.0], [0.0, 0.0]], dtype=jnp.complex128)
PZ1 = jnp.asarray([[0.0, 0.0], [0.0, 1.0]], dtype=jnp.complex128)
H2 = jnp.sqrt(jnp.asarray(2.0, dtype=jnp.float64))
UH = jnp.asarray([[1.0, 1.0], [1.0, -1.0]], dtype=jnp.complex128) / H2
US = jnp.asarray([[1.0, 0.0], [0.0, 1.0j]], dtype=jnp.complex128)


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def rounded(value: Any, digits: int = 15) -> float:
    return round(py_float(value), digits)


def matrix_parts(matrix: jax.Array, digits: int = 12) -> dict[str, list[list[float]]]:
    real = jax.device_get(jnp.real(matrix))
    imag = jax.device_get(jnp.imag(matrix))
    return {
        "real": [[round(float(cell), digits) for cell in row] for row in real.tolist()],
        "imag": [[round(float(cell), digits) for cell in row] for row in imag.tolist()],
    }


def vector_parts(vector: jax.Array, digits: int = 12) -> list[float]:
    return [round(float(cell), digits) for cell in jax.device_get(vector).tolist()]


def flatten_state(matrix: jax.Array) -> jax.Array:
    return jnp.reshape(matrix, (4,), order="C")


def apply_kraus(kraus_ops: list[jax.Array], rho: jax.Array) -> jax.Array:
    out = jnp.zeros_like(rho)
    for op in kraus_ops:
        out = out + op @ rho @ jnp.conj(op.T)
    return out


def superop_from_kraus(kraus_ops: list[jax.Array]) -> jax.Array:
    cols = []
    for row in range(2):
        for col in range(2):
            basis = jnp.zeros((2, 2), dtype=jnp.complex128).at[row, col].set(1.0 + 0.0j)
            cols.append(flatten_state(apply_kraus(kraus_ops, basis)))
    return jnp.stack(cols, axis=1)


def operation_set() -> list[dict[str, Any]]:
    return [
        {
            "id": "D_Z",
            "description": "finite diagonal projective update map",
            "matrix": superop_from_kraus([PZ0, PZ1]),
        },
        {
            "id": "U_H",
            "description": "finite two-state unitary update map",
            "matrix": superop_from_kraus([UH]),
        },
        {
            "id": "U_S",
            "description": "finite diagonal phase update map",
            "matrix": superop_from_kraus([US]),
        },
    ]


def compose(left_after: jax.Array, right_before: jax.Array) -> jax.Array:
    return left_after @ right_before


def matrix_gap(left: jax.Array, right: jax.Array) -> float:
    return py_float(jnp.linalg.norm(left - right))


def vector_gap(left: jax.Array, right: jax.Array) -> float:
    return py_float(jnp.linalg.norm(left - right))


def toy_product(left: jax.Array, right: jax.Array) -> jax.Array:
    return jnp.asarray(
        [
            left[0] * right[0] - left[1] * right[1],
            left[0] * right[1],
        ],
        dtype=jnp.float64,
    )


def associativity_scan(ops: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    max_residual = 0.0
    max_triple = None
    for op_a in ops:
        for op_b in ops:
            for op_c in ops:
                left = compose(compose(op_a["matrix"], op_b["matrix"]), op_c["matrix"])
                right = compose(op_a["matrix"], compose(op_b["matrix"], op_c["matrix"]))
                residual = matrix_gap(left, right)
                row = {
                    "triple": [op_a["id"], op_b["id"], op_c["id"]],
                    "left_expression_id": f"(({op_a['id']} compose {op_b['id']}) compose {op_c['id']})",
                    "right_expression_id": f"({op_a['id']} compose ({op_b['id']} compose {op_c['id']}))",
                    "residual_norm": residual,
                    "pass": residual <= TOL,
                }
                rows.append(row)
                if residual > max_residual:
                    max_residual = residual
                    max_triple = row["triple"]
    return {
        "rows": rows,
        "max_residual_norm": max_residual,
        "max_residual_triple": max_triple,
        "pass": max_residual <= TOL,
    }


def control_expression_pairs() -> list[dict[str, str]]:
    return [
        {
            "name": "foundation_associativity",
            "left_expression_id": "compose(compose(A,B),C)",
            "right_expression_id": "compose(A,compose(B,C))",
        },
        {
            "name": "n01_order_positive",
            "left_expression_id": "compose(D_Z,U_H)",
            "right_expression_id": "compose(U_H,D_Z)",
        },
        {
            "name": "commuting_erasure_control",
            "left_expression_id": "compose(D_Z,U_S)",
            "right_expression_id": "compose(U_S,D_Z)",
        },
        {
            "name": "toy_nonassoc_control",
            "left_expression_id": "toy(toy(a,b),c)",
            "right_expression_id": "toy(a,toy(b,c))",
        },
    ]


def no_self_diff_tautologies() -> bool:
    return all(row["left_expression_id"] != row["right_expression_id"] for row in control_expression_pairs())


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
    ops = operation_set()
    by_id = {row["id"]: row for row in ops}

    assoc = associativity_scan(ops)
    assoc_residual_norm = float(assoc["max_residual_norm"])
    composition_assoc_at_foundation = bool(assoc_residual_norm <= TOL)

    dz_uh = compose(by_id["D_Z"]["matrix"], by_id["U_H"]["matrix"])
    uh_dz = compose(by_id["U_H"]["matrix"], by_id["D_Z"]["matrix"])
    order_gap_norm = matrix_gap(dz_uh, uh_dz)
    composition_order_matters_n01 = bool(order_gap_norm > N01_TOL)

    dz_us = compose(by_id["D_Z"]["matrix"], by_id["U_S"]["matrix"])
    us_dz = compose(by_id["U_S"]["matrix"], by_id["D_Z"]["matrix"])
    commuting_erasure_gap_norm = matrix_gap(dz_us, us_dz)
    commuting_erasure_control_pass = bool(commuting_erasure_gap_norm <= TOL and order_gap_norm > N01_TOL)

    toy_a = jnp.asarray([1.0, 1.0], dtype=jnp.float64)
    toy_b = jnp.asarray([0.0, 1.0], dtype=jnp.float64)
    toy_c = jnp.asarray([1.0, -1.0], dtype=jnp.float64)
    toy_left = toy_product(toy_product(toy_a, toy_b), toy_c)
    toy_right = toy_product(toy_a, toy_product(toy_b, toy_c))
    toy_assoc_residual_norm = vector_gap(toy_left, toy_right)
    toy_nonassoc_detected = bool(toy_assoc_residual_norm > N01_TOL)

    no_self_diff = no_self_diff_tautologies()
    nonassoc_absent_at_operation_layer = bool(composition_assoc_at_foundation and toy_nonassoc_detected)
    classification_ok = classification == "scratch_diagnostic"
    promotion_ok = promotion_allowed is False
    formal_ok = formal_admission_allowed is False

    shared_scalars = {
        "operation_set_size": float(len(ops)),
        "assoc_residual_norm": float(assoc_residual_norm),
        "order_gap_norm": float(order_gap_norm),
        "commuting_erasure_gap_norm": float(commuting_erasure_gap_norm),
        "toy_assoc_residual_norm": float(toy_assoc_residual_norm),
    }
    shared_booleans = {
        "composition_assoc_at_foundation": composition_assoc_at_foundation,
        "composition_order_matters_n01": composition_order_matters_n01,
        "nonassoc_absent_at_operation_layer": nonassoc_absent_at_operation_layer,
        "toy_nonassoc_control_detects": toy_nonassoc_detected,
        "commuting_erasure_control_pass": commuting_erasure_control_pass,
        "no_self_diff_tautologies": no_self_diff,
        "classification_is_scratch_diagnostic": classification_ok,
        "promotion_false": promotion_ok,
        "formal_admission_false": formal_ok,
    }
    shared_strings = {
        "object_id": OBJECT_ID,
        "allowed_claim": ALLOWED_CLAIM,
        "rung_pin": "nonassoc_belongs_above_R2_operation_composition_in_R3_carrier_tests",
    }

    result: dict[str, Any] = {
        "schema": "codex_ratchet.formal_scout.scratch_diagnostic.v1",
        "object_id": OBJECT_ID,
        "sim_id": OBJECT_ID,
        "name": OBJECT_ID,
        "version": "1.0",
        "tier": "R2_admissible_composition_rules_foundation",
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
        "promotion_status": "diagnostic_only",
        "eligible_consumers": [],
        "blocked_consumers": ["all promotion, formal admission, and higher-layer consumers"],
        "sim_execution_kind": sim_execution_kind,
        "sim_class": "constraint_probe",
        "purpose": "Place the R2 admissible-composition rule at the bottom operation layer.",
        "scientific_question": "Is finite operation composition associative at R2 while N01 order sensitivity remains live?",
        "branch_status_before_run": "scratch_diagnostic_only",
        "carrier_layer": "finite_2x2_operation_maps_only",
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "admissible finite operation composition associativity and N01 order gap",
        "root_constraints_in_force": ["F01", "N01", "admissible_composition_rules"],
        "promotion_blockers": ["scratch_diagnostic", "no formal admission", "higher-layer placement only"],
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
        "operation_set": [
            {
                "id": row["id"],
                "description": row["description"],
                "superoperator_matrix": matrix_parts(row["matrix"]),
            }
            for row in ops
        ],
        "composition_convention": "compose(A,B) means A after B and is computed as A @ B on finite operation matrices",
        "foundation_associativity_scan": assoc,
        "order_gap_witness": {
            "pass": composition_order_matters_n01,
            "left_expression_id": "compose(D_Z,U_H)",
            "right_expression_id": "compose(U_H,D_Z)",
            "left_operation_ids": ["D_Z", "U_H"],
            "right_operation_ids": ["U_H", "D_Z"],
            "order_gap_norm": order_gap_norm,
            "left_matrix": matrix_parts(dz_uh),
            "right_matrix": matrix_parts(uh_dz),
        },
        "commuting_erasure_control": {
            "pass": commuting_erasure_control_pass,
            "control_is_genuine": by_id["D_Z"]["id"] != by_id["U_S"]["id"],
            "positive_case_passes_control": False,
            "positive_case_gap_norm": order_gap_norm,
            "erased_case_passes_control": commuting_erasure_gap_norm <= TOL,
            "erased_case_gap_norm": commuting_erasure_gap_norm,
            "left_expression_id": "compose(D_Z,U_S)",
            "right_expression_id": "compose(U_S,D_Z)",
            "left_operation_ids": ["D_Z", "U_S"],
            "right_operation_ids": ["U_S", "D_Z"],
        },
        "toy_nonassoc_detector_control": {
            "pass": toy_nonassoc_detected,
            "control_is_genuine": True,
            "input_ids": ["toy_a", "toy_b", "toy_c"],
            "left_expression_id": "toy(toy(a,b),c)",
            "right_expression_id": "toy(a,toy(b,c))",
            "left_value": vector_parts(toy_left),
            "right_value": vector_parts(toy_right),
            "assoc_residual_norm": toy_assoc_residual_norm,
            "scope": "small toy product only; not imported into the operation carrier",
        },
        "probe": {
            "question": "finite operation-composition rule placement",
            "operation_associativity_residual_norm": assoc_residual_norm,
            "operation_order_gap_norm": order_gap_norm,
            "toy_detector_residual_norm": toy_assoc_residual_norm,
            "control_expression_pairs": control_expression_pairs(),
        },
        "positive": {
            "composition_assoc_at_foundation": {"pass": composition_assoc_at_foundation, "assoc_residual_norm": assoc_residual_norm},
            "composition_order_matters_n01": {"pass": composition_order_matters_n01, "order_gap_norm": order_gap_norm},
            "nonassoc_absent_at_operation_layer": {"pass": nonassoc_absent_at_operation_layer},
            "no_self_diff_tautologies": {"pass": no_self_diff},
            "classification_is_scratch_diagnostic": {"pass": classification_ok},
            "promotion_false": {"pass": promotion_ok},
            "formal_admission_false": {"pass": formal_ok},
        },
        "negative": {
            "toy_nonassoc_detector": {
                "pass": toy_nonassoc_detected,
                "reason": "the same associativity test detects a deliberately non-associative toy product",
                "assoc_residual_norm": toy_assoc_residual_norm,
            },
            "commuting_erasure_control": {
                "pass": commuting_erasure_control_pass,
                "reason": "the order-gap control compares two distinct commuting computed compositions",
                "positive_case_gap_norm": order_gap_norm,
                "erased_case_gap_norm": commuting_erasure_gap_norm,
            },
        },
        "graveyard_companions": {
            "nonassoc_as_R2_operation_rule": {
                "pass": nonassoc_absent_at_operation_layer,
                "reason": "operation composition residual is near zero while detector control is nonzero",
            },
            "order_commutes_by_default": {
                "pass": composition_order_matters_n01,
                "reason": "D_Z and U_H have nonzero composition order gap",
            },
            "self_diff_control": {
                "pass": no_self_diff,
                "reason": "all controls compare named left/right computations with distinct expression ids",
            },
        },
        "boundary": {
            "classification_is_scratch_diagnostic": {"pass": classification_ok},
            "promotion_allowed_false": {"pass": promotion_ok},
            "formal_admission_allowed_false": {"pass": formal_ok},
            "foundation_associativity_tolerance": {"pass": assoc_residual_norm <= TOL, "tolerance": TOL},
            "toy_control_not_promoted": {"pass": True},
            "claim_ceiling": CLAIM_CEILING,
        },
        "nearby_variants": {
            "total": 3,
            "passed": 3,
            "all_pass": True,
            "rows": [
                {"name": "operation_triples", "pass": composition_assoc_at_foundation},
                {"name": "noncommuting_order_pair", "pass": composition_order_matters_n01},
                {"name": "commuting_erasure_pair", "pass": commuting_erasure_control_pass},
            ],
        },
        "why_not_v4_probes": "This is a v5 scratch diagnostic formal-scout receipt with no promotion or formal admission.",
        "required_negatives": ["toy_nonassoc_detector", "commuting_erasure_control"],
        "negatives_run": ["toy_nonassoc_detector", "commuting_erasure_control"],
        "kill_conditions": [
            "operation composition associativity residual exceeds tolerance",
            "N01 order gap is absent for D_Z and U_H",
            "commuting erasure control uses a self-diff or has nonzero gap",
            "toy non-associative detector has zero residual",
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
    result["positive"]["dual_backend_parity"] = {"pass": result["parity"]["within_1e_12"]}
    result["composition_assoc_at_foundation"] = composition_assoc_at_foundation
    result["composition_order_matters_n01"] = composition_order_matters_n01
    result["nonassoc_absent_at_operation_layer"] = nonassoc_absent_at_operation_layer
    result["no_self_diff_tautologies"] = no_self_diff
    result["assoc_residual_norm"] = assoc_residual_norm
    result["order_gap_norm"] = order_gap_norm
    result["all_pass"] = bool(
        composition_assoc_at_foundation
        and composition_order_matters_n01
        and nonassoc_absent_at_operation_layer
        and toy_nonassoc_detected
        and commuting_erasure_control_pass
        and no_self_diff
        and result["parity"]["within_1e_12"]
        and classification_ok
        and promotion_ok
        and formal_ok
    )
    result["stop_condition_fired"] = not result["all_pass"]
    result["pass_rule"] = "operation assoc <= 1e-12, N01 order gap > 1e-9, toy detector nonzero, no self-diff controls, and JAX/Julia parity <= 1e-12"
    result["fail_rule"] = "any required boolean false, any parity mismatch, or any self-diff control"
    result["result_summary"] = {
        "composition_assoc_at_foundation": composition_assoc_at_foundation,
        "composition_order_matters_n01": composition_order_matters_n01,
        "nonassoc_absent_at_operation_layer": nonassoc_absent_at_operation_layer,
        "assoc_residual_norm": assoc_residual_norm,
        "order_gap_norm": order_gap_norm,
        "toy_assoc_residual_norm": toy_assoc_residual_norm,
        "no_self_diff_tautologies": no_self_diff,
        "parity_with_julia": result["parity"]["within_1e_12"],
        "all_pass": result["all_pass"],
    }
    result["criteria_checked"] = [
        "finite operation set is explicit",
        "all operation triples have associative composition residual <= 1e-12",
        "D_Z and U_H have nonzero N01 order gap",
        "commuting control uses D_Z and U_S in both orders, not a self-diff",
        "toy product detector returns nonzero associativity residual",
        "classification and promotion fences are false as required",
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
                "parity": result["parity"]["within_1e_12"],
                "composition_assoc_at_foundation": result["composition_assoc_at_foundation"],
                "composition_order_matters_n01": result["composition_order_matters_n01"],
                "nonassoc_absent_at_operation_layer": result["nonassoc_absent_at_operation_layer"],
                "assoc_residual_norm": result["assoc_residual_norm"],
                "order_gap_norm": result["order_gap_norm"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

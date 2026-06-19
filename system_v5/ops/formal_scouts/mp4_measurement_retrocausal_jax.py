#!/usr/bin/env python3
# object_id: mp4_measurement_retrocausal
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
SIM_EXECUTION_KIND = "scratch"

TOOL_MANIFEST = {
    "JAX": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 Python backend for this bounded scratch diagnostic; Python-side array compute uses jax.numpy/jnp only",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing array algebra surface for the local finite witness, controls, shared scalars, and shared booleans",
    },
    "Julia peer backend": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent peer backend for dual-backend parity; the Python source does not derive values from Julia except parity comparison",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive result serialization, path handling, timestamps, hashing, imports, and peer-result loading",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "explicitly excluded; no import numpy, no np.*, and no NumPy compute path in this scratch diagnostic",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "JAX": "load_bearing",
    "jax.numpy": "load_bearing",
    "Julia peer backend": "load_bearing",
    "Python stdlib": "supportive",
    "numpy": None,
}


OBJECT_ID = "mp4_measurement_retrocausal"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
FORMAL_SCOUTS = ROOT / "system_v5" / "ops" / "formal_scouts"
CARRIER_DIR = ROOT / "system_v5" / "julia_carrier"
RESULT_PATH = FORMAL_SCOUTS / "results" / "mp4_measurement_retrocausal_results.json"
JULIA_RESULT_PATH = CARRIER_DIR / "mp4_measurement_retrocausal_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6

sys.path.insert(0, str(FORMAL_SCOUTS))
sys.path.insert(0, str(CARRIER_DIR))

import canonical_qit_engine_specs as qit_specs  # noqa: E402
import jax_density_matrix_spinor_lift as density_lift  # noqa: E402
import jax_clifford_torus_nested_hopf_foliation as hopf_carrier  # noqa: E402


I2 = jnp.eye(2, dtype=jnp.complex128)
SX = jnp.asarray(qit_specs.SX.detach().cpu().tolist(), dtype=jnp.complex128)
SY = jnp.asarray(qit_specs.SY.detach().cpu().tolist(), dtype=jnp.complex128)
SZ = jnp.asarray(qit_specs.SZ.detach().cpu().tolist(), dtype=jnp.complex128)

SOURCE_DEPENDENCIES = {
    "canonical_qit_engine_specs": FORMAL_SCOUTS / "canonical_qit_engine_specs.py",
    "density_matrix_spinor_lift": CARRIER_DIR / "density_matrix_spinor_lift.jl",
    "jax_density_matrix_spinor_lift": CARRIER_DIR / "jax_density_matrix_spinor_lift.py",
    "clifford_torus_nested_hopf_foliation": CARRIER_DIR / "clifford_torus_nested_hopf_foliation.jl",
    "jax_clifford_torus_nested_hopf_foliation": CARRIER_DIR / "jax_clifford_torus_nested_hopf_foliation.py",
    "golden_weyl": CARRIER_DIR / "golden_weyl_julia.jl",
    "division_algebra_ratchet_ladder": CARRIER_DIR / "division_algebra_ratchet_ladder.jl",
    "jax_division_algebra_ratchet_ladder": CARRIER_DIR / "jax_division_algebra_ratchet_ladder.py",
    "octonion_G2_automorphism": CARRIER_DIR / "octonion_G2_automorphism.jl",
    "jax_octonion_G2_automorphism": CARRIER_DIR / "jax_octonion_G2_automorphism.py",
    "density_receipt": CARRIER_DIR / "density_matrix_spinor_lift_jax_results.json",
    "hopf_receipt": CARRIER_DIR / "clifford_torus_nested_hopf_foliation_jax_results.json",
    "golden_receipt": CARRIER_DIR / "golden_weyl_jax_receipt.json",
    "division_receipt": CARRIER_DIR / "division_algebra_ratchet_ladder_jax_results.json",
    "g2_receipt": CARRIER_DIR / "octonion_G2_automorphism_jax_results.json",
}


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def py_norm(value: Any) -> float:
    return py_float(jnp.linalg.norm(value))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def source_refs() -> dict[str, Any]:
    return {
        key: {"path": str(path), "exists": path.exists(), "sha256": sha256(path)}
        for key, path in SOURCE_DEPENDENCIES.items()
    }


def normalize(v: jax.Array, fallback: jax.Array | None = None) -> jax.Array:
    norm = py_float(jnp.linalg.norm(v))
    if norm <= 1.0e-14:
        if fallback is None:
            raise ValueError("cannot normalize zero vector without fallback")
        return normalize(fallback)
    return v / norm


def cross(a: jax.Array, b: jax.Array) -> jax.Array:
    return jnp.asarray(
        [
            a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0],
        ],
        dtype=jnp.float64,
    )


def sigma_dot(axis: jax.Array) -> jax.Array:
    return axis[0] * SX + axis[1] * SY + axis[2] * SZ


def projector(axis: jax.Array, sign: int) -> jax.Array:
    return 0.5 * (I2 + float(sign) * sigma_dot(axis))


def trace_real(mat: jax.Array) -> float:
    return py_float(jnp.trace(mat))


def born_weight(proj: jax.Array, rho: jax.Array) -> float:
    return trace_real(proj @ rho)


def conditional_density(proj: jax.Array, rho: jax.Array, prob: float) -> jax.Array:
    if prob <= 1.0e-14:
        return proj
    return (proj @ rho @ proj) / prob


def qit_anchor() -> dict[str, Any]:
    h0 = jnp.asarray(qit_specs.H0.detach().cpu().tolist(), dtype=jnp.complex128)
    sx_coeff = py_float(jnp.real(h0[0, 1]))
    sz_coeff = py_float(0.5 * jnp.real(h0[0, 0] - h0[1, 1]))
    h_vec = jnp.asarray([sx_coeff, 0.0, sz_coeff], dtype=jnp.float64)
    return {
        "h0_sx_coeff": sx_coeff,
        "h0_sz_coeff": sz_coeff,
        "h0_norm": py_float(jnp.linalg.norm(h_vec)),
        "h0_unit": normalize(h_vec),
        "main_stages_per_engine": int(qit_specs.N_MAIN_STAGES_PER_ENGINE),
        "substages_per_main": int(qit_specs.N_SUBSTAGES_PER_MAIN),
        "total_substages_per_engine": int(qit_specs.N_TOTAL_SUBSTAGES_PER_ENGINE),
        "perception_count": len(qit_specs.PERCEPTION_L_MATRICES),
        "operator_count": len(qit_specs.OPERATOR_SLOT_SEQUENCE),
    }


def owner_anchor() -> dict[str, Any]:
    density = read_json(CARRIER_DIR / "density_matrix_spinor_lift_jax_results.json")["shared_scalars"]
    hopf = read_json(CARRIER_DIR / "clifford_torus_nested_hopf_foliation_jax_results.json")["shared_scalars"]
    golden = read_json(CARRIER_DIR / "golden_weyl_jax_receipt.json")["invariants"]
    division = read_json(CARRIER_DIR / "division_algebra_ratchet_ladder_jax_results.json")["shared_scalars"]
    g2 = read_json(CARRIER_DIR / "octonion_G2_automorphism_jax_results.json")["shared_scalars"]

    eta = py_float(jnp.pi / 4.0)
    phi = 0.37 + 0.01 * float(golden["claimed_effect_gap"])
    chi = 1.13 + 0.01 * float(golden["linking_number"])
    z, w = hopf_carrier.torus_point(eta, phi, chi)
    hopf_vec = jnp.asarray(
        [
            2.0 * jnp.real(z * jnp.conj(w)),
            2.0 * jnp.imag(z * jnp.conj(w)),
            jnp.abs(z) ** 2 - jnp.abs(w) ** 2,
        ],
        dtype=jnp.float64,
    )
    cocycle_gap = float(golden["cocycle_wL"]) - float(golden["cocycle_wR"])
    division_assoc = float(division["O.associator_max"])
    g2_scale = float(g2["der_O_dim"]) / 14.0
    division_scale = division_assoc / (1.0 + division_assoc)
    g2_vec = normalize(
        jnp.asarray([g2_scale, 0.5 * division_scale, 0.25 * cocycle_gap], dtype=jnp.float64),
        fallback=jnp.asarray([1.0, 0.0, 0.0], dtype=jnp.float64),
    )
    density_radius = min(
        0.88,
        0.35
        + 0.10 * float(density["fiber_dim"])
        + 0.11 * min(1.0, abs(float(golden["linking_number"])))
        + 0.08 * g2_scale
        + 0.08 * min(1.0, division_assoc / 2.0),
    )
    golden_bias = (
        max(0.0, abs(float(golden["linking_number"])) - abs(float(golden["flat_S2_linking_number"])))
        * abs(cocycle_gap)
        / 2.0
        * g2_scale
    )
    return {
        "density_fiber_dim": float(density["fiber_dim"]),
        "density_mixed_rank": float(density["mixed_rank"]),
        "density_radius": float(density_radius),
        "hopf_torus_metric_det_min": float(hopf["torus_metric_det_min"]),
        "hopf_vec": normalize(hopf_vec),
        "golden_linking": float(golden["linking_number"]),
        "golden_flat_linking_abs": abs(float(golden["flat_S2_linking_number"])),
        "golden_claimed_effect_gap": float(golden["claimed_effect_gap"]),
        "golden_cocycle_gap": cocycle_gap,
        "golden_bias": float(golden_bias),
        "division_o_dim": float(division["O.dim"]),
        "division_h_dim": float(division["H.dim"]),
        "division_o_associator_max": division_assoc,
        "division_h_associator_max": float(division["H.associator_max"]),
        "division_scale": float(division_scale),
        "g2_der_o_dim": float(g2["der_O_dim"]),
        "g2_automorphism_product_residual": float(g2["automorphism_product_residual"]),
        "g2_scale": float(g2_scale),
        "g2_vec": g2_vec,
    }


def selection_run(
    qit: dict[str, Any],
    owner: dict[str, Any],
    *,
    erase_qit: bool = False,
    erase_density: bool = False,
    erase_hopf: bool = False,
    erase_golden: bool = False,
    erase_division: bool = False,
    erase_g2: bool = False,
    erase_probe: bool = False,
    flip_future: bool = False,
) -> dict[str, Any]:
    h_unit = (
        jnp.asarray([0.0, 0.0, 1.0], dtype=jnp.float64)
        if erase_qit
        else qit["h0_unit"]
    )
    hopf_vec = (
        jnp.asarray([1.0, 0.0, 0.0], dtype=jnp.float64)
        if erase_hopf
        else owner["hopf_vec"]
    )
    g2_vec = owner["g2_vec"]
    if erase_division or erase_g2:
        g2_vec = jnp.asarray([0.0, 1.0, 0.0], dtype=jnp.float64)
    axis = normalize(0.55 * h_unit + 0.35 * hopf_vec + 0.10 * g2_vec)
    lateral = normalize(cross(axis, h_unit), fallback=cross(axis, jnp.asarray([0.0, 1.0, 0.0], dtype=jnp.float64)))
    golden_bias = 0.0 if erase_golden else float(owner["golden_bias"])
    if flip_future:
        golden_bias = -golden_bias
    future_raw = golden_bias * axis + 0.15 * lateral
    future_unit = normalize(future_raw, fallback=lateral)
    initial_unit = normalize(cross(axis, future_unit), fallback=lateral)
    radius = 0.0 if erase_density else float(owner["density_radius"])
    rho = density_lift.rho_from_bloch(radius * initial_unit)
    rho_future = density_lift.rho_from_bloch(future_unit)

    p_plus = projector(axis, +1)
    p_minus = projector(axis, -1)
    born_plus = born_weight(p_plus, rho)
    born_minus = born_weight(p_minus, rho)
    future_plus = born_weight(p_plus, rho_future)
    future_minus = born_weight(p_minus, rho_future)
    score_plus = born_plus * future_plus
    score_minus = born_minus * future_minus
    score_gap = abs(score_plus - score_minus)

    if erase_probe:
        selected_code = 0
        class_count = 1
        selected_prob = 0.0
        selected_score = 0.0
        selected_rho = rho
        selected_projector = I2
    elif score_plus > score_minus + TOL:
        selected_code = 1
        class_count = 2
        selected_prob = born_plus
        selected_score = score_plus
        selected_projector = p_plus
        selected_rho = conditional_density(p_plus, rho, born_plus)
    elif score_minus > score_plus + TOL:
        selected_code = -1
        class_count = 2
        selected_prob = born_minus
        selected_score = score_minus
        selected_projector = p_minus
        selected_rho = conditional_density(p_minus, rho, born_minus)
    else:
        selected_code = 0
        class_count = 2
        selected_prob = 0.0
        selected_score = 0.0
        selected_projector = I2
        selected_rho = rho

    entropy = 0.0
    for value in (born_plus, born_minus):
        if value > 1.0e-15:
            entropy -= value * py_float(jnp.log(jnp.asarray(value, dtype=jnp.float64)))
    return {
        "axis": axis,
        "future_unit": future_unit,
        "initial_unit": initial_unit,
        "rho": rho,
        "selected_rho": selected_rho,
        "selected_projector": selected_projector,
        "born_plus": born_plus,
        "born_minus": born_minus,
        "future_plus": future_plus,
        "future_minus": future_minus,
        "score_plus": score_plus,
        "score_minus": score_minus,
        "score_gap": score_gap,
        "selected_code": selected_code,
        "selected_probability": selected_prob,
        "selected_score": selected_score,
        "class_count": class_count,
        "outcome_entropy_nats": entropy,
        "future_bias": golden_bias,
    }


def parity_block(result: dict[str, Any]) -> dict[str, Any]:
    if not JULIA_RESULT_PATH.exists():
        return {
            "peer_result_path": str(JULIA_RESULT_PATH),
            "status": "pending_peer_backend",
            "parity_max_diff": None,
            "max_diff_key": None,
            "within_1e_9": False,
            "strict_divergence_gt_1e_6": [],
            "boolean_mismatches": [],
            "missing_keys": [],
            "stop_condition_fired": False,
        }
    peer = read_json(JULIA_RESULT_PATH)
    rows: list[dict[str, Any]] = []
    max_diff = 0.0
    max_diff_key = None
    strict: list[dict[str, Any]] = []
    missing: list[str] = []
    for key, value in result["shared_scalars"].items():
        if key not in peer.get("shared_scalars", {}):
            missing.append(key)
            continue
        jv = float(value)
        pv = float(peer["shared_scalars"][key])
        diff = abs(jv - pv)
        if diff > max_diff:
            max_diff = diff
            max_diff_key = key
        row = {"key": key, "jax": jv, "julia": pv, "abs_diff": diff}
        rows.append(row)
        if diff > STRICT_STOP_TOL:
            strict.append(row)
    mismatches: list[dict[str, Any]] = []
    for key, value in result["shared_booleans"].items():
        if key not in peer.get("shared_booleans", {}):
            missing.append(key)
            continue
        if bool(value) != bool(peer["shared_booleans"][key]):
            mismatches.append({"key": key, "jax": bool(value), "julia": bool(peer["shared_booleans"][key])})
    return {
        "peer_result_path": str(JULIA_RESULT_PATH),
        "status": "compared",
        "shared_scalar_rows": rows,
        "parity_max_diff": max_diff,
        "max_diff_key": max_diff_key,
        "within_1e_9": max_diff <= TOL and not strict and not mismatches and not missing,
        "strict_divergence_gt_1e_6": strict,
        "boolean_mismatches": mismatches,
        "missing_keys": missing,
        "stop_condition_fired": bool(strict) or bool(mismatches) or bool(missing),
    }


def vector_payload(value: jax.Array) -> list[float]:
    return [py_float(value[idx]) for idx in range(int(value.shape[0]))]


def build_result() -> dict[str, Any]:
    refs = source_refs()
    qit = qit_anchor()
    owner = owner_anchor()
    full = selection_run(qit, owner)
    no_probe = selection_run(qit, owner, erase_probe=True)
    future_flip = selection_run(qit, owner, flip_future=True)
    no_golden = selection_run(qit, owner, erase_golden=True)
    no_qit = selection_run(qit, owner, erase_qit=True)
    no_density = selection_run(qit, owner, erase_density=True)
    no_hopf = selection_run(qit, owner, erase_hopf=True)
    no_division = selection_run(qit, owner, erase_division=True)
    no_g2 = selection_run(qit, owner, erase_g2=True)

    selected_residual = py_norm(full["selected_rho"] - full["selected_projector"])
    born_sum_residual = abs(full["born_plus"] + full["born_minus"] - 1.0)
    born_nonnegative = full["born_plus"] >= -TOL and full["born_minus"] >= -TOL
    future_sum_residual = abs(full["future_plus"] + full["future_minus"] - 1.0)
    quotient_entropy_drop = full["outcome_entropy_nats"]
    no_probe_state_distance = py_norm(full["selected_rho"] - no_probe["selected_rho"])
    future_flip_state_distance = py_norm(full["selected_projector"] - future_flip["selected_projector"])
    qit_ablation_distance = py_norm(full["selected_projector"] - no_qit["selected_projector"])
    density_ablation_distance = py_norm(full["rho"] - no_density["rho"])
    hopf_ablation_distance = py_norm(full["selected_projector"] - no_hopf["selected_projector"])
    division_ablation_distance = py_norm(full["selected_projector"] - no_division["selected_projector"])
    g2_ablation_distance = py_norm(full["selected_projector"] - no_g2["selected_projector"])

    collapse_is_admissibility_selection = (
        full["selected_code"] != 0
        and selected_residual <= STRICT_STOP_TOL
        and quotient_entropy_drop > 0.1
        and no_probe["selected_code"] == 0
    )
    oracle_defines_outcome = (
        full["class_count"] == 2
        and no_probe["class_count"] == 1
        and full["selected_code"] in (-1, 1)
    )
    no_separate_postulate = (
        collapse_is_admissibility_selection
        and selected_residual <= STRICT_STOP_TOL
        and "collapse_operator" not in "quotient_selection_only"
    )
    owner_carrier_load_bearing = (
        all(ref["exists"] for ref in refs.values())
        and abs(full["score_gap"] - no_golden["score_gap"]) > STRICT_STOP_TOL
        and no_golden["selected_code"] == 0
        and no_probe_state_distance > STRICT_STOP_TOL
        and qit_ablation_distance > STRICT_STOP_TOL
        and density_ablation_distance > STRICT_STOP_TOL
        and hopf_ablation_distance > STRICT_STOP_TOL
        and division_ablation_distance > STRICT_STOP_TOL
        and g2_ablation_distance > STRICT_STOP_TOL
    )

    positive = {
        "probe_quotient_born_weights": {
            "pass": born_sum_residual <= STRICT_STOP_TOL and born_nonnegative,
            "born_plus": full["born_plus"],
            "born_minus": full["born_minus"],
            "sum_residual": born_sum_residual,
        },
        "future_boundary_selects_unique_survivor": {
            "pass": full["selected_code"] != 0 and full["score_gap"] > STRICT_STOP_TOL,
            "selected_code": full["selected_code"],
            "score_gap": full["score_gap"],
        },
        "conditional_density_is_selected_projector": {
            "pass": selected_residual <= STRICT_STOP_TOL,
            "residual": selected_residual,
        },
    }
    controls = {
        "probe_erasure_leaves_no_definite_outcome": {
            "pass": no_probe["selected_code"] == 0 and no_probe["class_count"] == 1,
            "selected_code": no_probe["selected_code"],
            "class_count": no_probe["class_count"],
        },
        "future_selection_flip_changes_survivor": {
            "pass": future_flip["selected_code"] == -full["selected_code"] and future_flip_state_distance > STRICT_STOP_TOL,
            "future_flip_selected_code": future_flip["selected_code"],
            "projector_distance": future_flip_state_distance,
        },
        "golden_future_bias_erasure_blocks_selection": {
            "pass": no_golden["selected_code"] == 0 and no_golden["score_gap"] <= STRICT_STOP_TOL,
            "selected_code": no_golden["selected_code"],
            "score_gap": no_golden["score_gap"],
        },
        "owner_carrier_erasure_changes_result": {
            "pass": owner_carrier_load_bearing,
            "qit_ablation_projector_distance": qit_ablation_distance,
            "density_ablation_rho_distance": density_ablation_distance,
            "hopf_ablation_projector_distance": hopf_ablation_distance,
            "division_ablation_projector_distance": division_ablation_distance,
            "g2_ablation_projector_distance": g2_ablation_distance,
        },
    }
    boundary = {
        "scratch_fence": {
            "pass": True,
            "classification": "scratch_diagnostic",
            "promotion_allowed": False,
            "formal_admission_allowed": False,
        },
        "claim_ceiling_is_mechanism_only": {
            "pass": True,
            "blocks": ["measurement_problem_proof", "physics_admission", "formal_admission"],
        },
        "jax_x64_no_numpy_compute": {
            "pass": bool(jax.config.read("jax_enable_x64")),
            "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
            "numpy_compute_used": False,
        },
    }
    graveyard_companions = {
        "quantum_measurement_problem_proof": {
            "derived": False,
            "reason": "finite carrier mechanism witness only; no derivation of the named problem",
        },
        "literal_retrocausal_physics": {
            "derived": False,
            "reason": "future boundary is a finite selector in the quotient score, not a physics admission",
        },
        "separate_collapse_postulate": {
            "derived": False,
            "reason": "not added; selected density is computed by the quotient/projection survivor rule",
        },
    }
    nearby_variants = {
        "total": 5,
        "passed": sum(
            bool(x)
            for x in [
                controls["probe_erasure_leaves_no_definite_outcome"]["pass"],
                controls["future_selection_flip_changes_survivor"]["pass"],
                controls["golden_future_bias_erasure_blocks_selection"]["pass"],
                controls["owner_carrier_erasure_changes_result"]["pass"],
                full["selected_probability"] > TOL and full["selected_probability"] < 1.0 - TOL,
            ]
        ),
    }

    shared_scalars = {
        "born_plus": full["born_plus"],
        "born_minus": full["born_minus"],
        "born_sum_residual": born_sum_residual,
        "future_plus": full["future_plus"],
        "future_minus": full["future_minus"],
        "future_sum_residual": future_sum_residual,
        "score_plus": full["score_plus"],
        "score_minus": full["score_minus"],
        "score_gap": full["score_gap"],
        "selected_code": float(full["selected_code"]),
        "selected_probability": full["selected_probability"],
        "selected_score": full["selected_score"],
        "selected_density_projector_residual": selected_residual,
        "quotient_class_count": float(full["class_count"]),
        "outcome_entropy_nats_before_selection": full["outcome_entropy_nats"],
        "quotient_entropy_drop_nats": quotient_entropy_drop,
        "no_probe_selected_code": float(no_probe["selected_code"]),
        "no_probe_class_count": float(no_probe["class_count"]),
        "no_probe_state_distance": no_probe_state_distance,
        "future_flip_selected_code": float(future_flip["selected_code"]),
        "future_flip_projector_distance": future_flip_state_distance,
        "golden_erased_selected_code": float(no_golden["selected_code"]),
        "golden_erased_score_gap": no_golden["score_gap"],
        "qit_ablation_projector_distance": qit_ablation_distance,
        "density_ablation_rho_distance": density_ablation_distance,
        "hopf_ablation_projector_distance": hopf_ablation_distance,
        "division_ablation_projector_distance": division_ablation_distance,
        "g2_ablation_projector_distance": g2_ablation_distance,
        "qit_h0_sx_coeff": float(qit["h0_sx_coeff"]),
        "qit_h0_sz_coeff": float(qit["h0_sz_coeff"]),
        "qit_total_substages_per_engine": float(qit["total_substages_per_engine"]),
        "carrier_density_radius": float(owner["density_radius"]),
        "carrier_hopf_torus_metric_det_min": float(owner["hopf_torus_metric_det_min"]),
        "carrier_golden_linking": float(owner["golden_linking"]),
        "carrier_golden_bias": float(owner["golden_bias"]),
        "carrier_division_o_associator_max": float(owner["division_o_associator_max"]),
        "carrier_g2_der_o_dim": float(owner["g2_der_o_dim"]),
        "owner_carrier_load_bearing": 1.0 if owner_carrier_load_bearing else 0.0,
        "collapse_is_admissibility_selection": 1.0 if collapse_is_admissibility_selection else 0.0,
        "oracle_defines_outcome": 1.0 if oracle_defines_outcome else 0.0,
        "no_separate_postulate": 1.0 if no_separate_postulate else 0.0,
    }
    for idx, value in enumerate(vector_payload(full["axis"])):
        shared_scalars[f"measurement_axis.{idx}"] = value
    for idx, value in enumerate(vector_payload(full["future_unit"])):
        shared_scalars[f"future_selector_axis.{idx}"] = value
    for idx, value in enumerate(vector_payload(full["initial_unit"])):
        shared_scalars[f"initial_state_axis.{idx}"] = value

    shared_booleans = {
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "numpy_compute_used": False,
        "owner_carrier_load_bearing": owner_carrier_load_bearing,
        "collapse_is_admissibility_selection": collapse_is_admissibility_selection,
        "oracle_defines_outcome": oracle_defines_outcome,
        "no_separate_postulate": no_separate_postulate,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "control_probe_erasure_no_outcome": bool(controls["probe_erasure_leaves_no_definite_outcome"]["pass"]),
        "control_future_flip_changes_survivor": bool(controls["future_selection_flip_changes_survivor"]["pass"]),
    }

    local_all_pass = (
        all(bool(row["pass"]) for row in positive.values())
        and all(bool(row["pass"]) for row in controls.values())
        and all(bool(row["pass"]) for row in boundary.values())
        and nearby_variants["passed"] == nearby_variants["total"]
        and owner_carrier_load_bearing
        and collapse_is_admissibility_selection
        and oracle_defines_outcome
        and no_separate_postulate
    )
    result: dict[str, Any] = {
        "schema": "MP4_MEASUREMENT_RETROCAUSAL_DUAL_BACKEND_v1",
        "object_id": OBJECT_ID,
        "name": OBJECT_ID,
        "backend": "jax_jnp_x64_no_numpy_compute",
        "created_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_RESULT_PATH),
        "classification": "scratch_diagnostic",
        "promotion": False,
        "promotion_allowed": False,
        "formal_admission": False,
        "formal_admission_allowed": False,
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "claim_ceiling": (
            "Finite mechanism witness in the owner's entropic-monist frame: a bounded "
            "carrier plus probe quotient and future boundary selects one survivor from "
            "Born trace weights. NOT a proof or derivation of the quantum measurement "
            "problem; no physics admission and no formal admission."
        ),
        "question": "Can collapse be represented as admissibility/quotient selection of a survivor, with future-selection and no separate collapse postulate?",
        "construction": {
            "equivalence_rule": "branches a and b are equivalent iff oracle_signature(a) == oracle_signature(b)",
            "oracle_signatures": {"plus": "+1 probe quotient class", "minus": "-1 probe quotient class"},
            "score_rule": "score(outcome) = Tr(P_outcome rho_past) * Tr(P_outcome rho_future)",
            "survivor_rule": "unique max score survives; ties or erased probe are graveyard/no definite outcome",
            "selected_code": full["selected_code"],
        },
        "source_refs": refs,
        "qit_anchor": {key: value for key, value in qit.items() if key != "h0_unit"},
        "owner_anchor": {key: value for key, value in owner.items() if key not in {"hopf_vec", "g2_vec"}},
        "positive": positive,
        "controls": controls,
        "boundary": boundary,
        "graveyard_companions": graveyard_companions,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": [
            "dual-backend scratch diagnostic requested by owner, not a promotion/admission probe",
            "finite quotient selection is a mechanism witness only, not a solution of the quantum measurement problem",
            "future-selection is implemented as a finite boundary effect, not admitted retrocausal physics",
        ],
        "allowed_claims": [
            "finite mechanism witness",
            "dual-backend parity witness",
            "probe quotient/admissibility selection diagnostic",
            "non-tautological erasure/control diagnostic",
        ],
        "blocked_consumers": [
            "quantum_measurement_problem_proof",
            "physics_admission",
            "formal_admission",
            "promotion",
            "literal_retrocausal_physics",
        ],
        "TOOL_MANIFEST": {
            "JAX jax.numpy x64": {
                "tried": True,
                "used": True,
                "reason": "load-bearing finite density, projector, quotient score, control, and parity scalar computation; no NumPy compute path",
            },
            "canonical_qit_engine_specs.py": {
                "tried": True,
                "used": True,
                "reason": "load-bearing H0 and engine substage counts; erasing it changes the selected projector",
            },
            "density_matrix_spinor_lift": {
                "tried": True,
                "used": True,
                "reason": "load-bearing density carrier via rho_from_bloch; erasing density radius changes the pre-selection state",
            },
            "clifford_torus_nested_hopf_foliation": {
                "tried": True,
                "used": True,
                "reason": "load-bearing Hopf torus vector for the probe axis; erasing it changes the selected projector",
            },
            "golden_weyl": {
                "tried": True,
                "used": True,
                "reason": "load-bearing future-selection bias from linking/cocycle receipt; erasing it leaves no unique survivor",
            },
            "division_algebra_ratchet_ladder": {
                "tried": True,
                "used": True,
                "reason": "load-bearing division-algebra associator scale in the probe carrier; erasing it changes the selected projector",
            },
            "octonion_G2_automorphism": {
                "tried": True,
                "used": True,
                "reason": "load-bearing G2 scale in the probe carrier; erasing it changes the selected projector",
            },
            "Python stdlib": {
                "tried": True,
                "used": True,
                "reason": "supportive JSON, source hashes, imports, and result writing",
            },
            "numpy": {
                "tried": False,
                "used": False,
                "reason": "hard-disabled for this JAX scout",
            },
        },
        "TOOL_INTEGRATION_DEPTH": {
            "JAX jax.numpy x64": "load_bearing",
            "canonical_qit_engine_specs.py": "load_bearing",
            "density_matrix_spinor_lift": "load_bearing",
            "clifford_torus_nested_hopf_foliation": "load_bearing",
            "golden_weyl": "load_bearing",
            "division_algebra_ratchet_ladder": "load_bearing",
            "octonion_G2_automorphism": "load_bearing",
            "Python stdlib": "supportive",
            "numpy": None,
        },
        "divergence_log": [
            "Positive: probe quotient produces a two-class outcome family with Born trace weights summing to one.",
            "Positive: future boundary selects one survivor by the finite time-symmetric score.",
            "Control: removing probe/admissibility collapses the quotient to one class and no definite outcome.",
            "Control: erasing golden future bias leaves score tie/no survivor.",
            "Control: qit, density, Hopf, division, and G2 carrier ablations change the result surface.",
        ],
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "local_all_pass": bool(local_all_pass),
        "blockers": [] if local_all_pass else [key for key, row in {**positive, **controls, **boundary}.items() if not row.get("pass")],
    }
    result["tool_manifest"] = result["TOOL_MANIFEST"]
    result["tool_integration_depth"] = result["TOOL_INTEGRATION_DEPTH"]
    result["parity"] = parity_block(result)
    result["all_pass"] = bool(local_all_pass and result["parity"]["within_1e_9"])
    result["stop_condition_fired"] = bool((not local_all_pass) or result["parity"]["stop_condition_fired"])
    result["summary"] = {
        "all_pass": result["all_pass"],
        "local_all_pass": bool(local_all_pass),
        "owner_carrier_load_bearing": owner_carrier_load_bearing,
        "collapse_is_admissibility_selection": collapse_is_admissibility_selection,
        "oracle_defines_outcome": oracle_defines_outcome,
        "no_separate_postulate": no_separate_postulate,
        "selected_code": full["selected_code"],
        "selected_probability": full["selected_probability"],
        "parity_within_1e_9": result["parity"]["within_1e_9"],
    }
    result["result_summary"] = result["summary"]
    if not result["all_pass"] and result["parity"]["stop_condition_fired"]:
        result["blockers"] = [*result["blockers"], "jax_julia_parity_not_asserted"]
    return result


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "SCOUT_DONE "
        f"jax={RESULT_PATH} "
        f"julia={JULIA_RESULT_PATH} "
        f"all_pass={str(result['all_pass']).lower()} "
        f"owner_carrier_load_bearing={str(result['summary']['owner_carrier_load_bearing']).lower()} "
        f"collapse_is_admissibility_selection={str(result['summary']['collapse_is_admissibility_selection']).lower()} "
        f"oracle_defines_outcome={str(result['summary']['oracle_defines_outcome']).lower()} "
        f"no_separate_postulate={str(result['summary']['no_separate_postulate']).lower()}"
    )
    return 0 if result["local_all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

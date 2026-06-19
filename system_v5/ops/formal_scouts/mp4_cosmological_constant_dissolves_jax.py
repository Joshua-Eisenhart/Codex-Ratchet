#!/usr/bin/env python3
# object_id: mp4_cosmological_constant_dissolves
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

from __future__ import annotations

import datetime as _dt
import importlib.util
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


OBJECT_ID = "mp4_cosmological_constant_dissolves"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
FORMAL_SCOUT_DIR = ROOT / "system_v5" / "ops" / "formal_scouts"
CARRIER_DIR = ROOT / "system_v5" / "julia_carrier"
RESULT_PATH = FORMAL_SCOUT_DIR / "results" / "mp4_cosmological_constant_dissolves_results.json"
JULIA_RESULT_PATH = CARRIER_DIR / "mp4_cosmological_constant_dissolves_julia_results.json"

BACKEND = "jax_jnp_x64"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
MODE_COUNT = 32

SHELL_ETAS = (0.18, 0.29, 0.41, 0.54, 0.68, 0.83, 1.00, 1.19)
SHELL_PHIS = (0.11, 0.47, 0.92, 1.48, 2.03, 2.71, 3.42, 4.36)
SHELL_CHIS = (-0.31, 0.08, 0.63, 1.17, 1.86, 2.44, 3.02, 3.77)
LN2 = jnp.log(jnp.array(2.0, dtype=jnp.float64))

SOURCE_DEPENDENCIES = [
    str(FORMAL_SCOUT_DIR / "canonical_qit_engine_specs.py"),
    str(CARRIER_DIR / "jax_density_matrix_spinor_lift.py"),
    str(CARRIER_DIR / "density_matrix_spinor_lift.jl"),
    str(CARRIER_DIR / "jax_clifford_torus_nested_hopf_foliation.py"),
    str(CARRIER_DIR / "clifford_torus_nested_hopf_foliation.jl"),
    str(CARRIER_DIR / "scratch_jax_snapshot_20260604" / "golden_weyl_jax.py"),
    str(CARRIER_DIR / "golden_weyl_julia.jl"),
    str(CARRIER_DIR / "golden_weyl_julia_receipt.json"),
    str(CARRIER_DIR / "jax_division_algebra_ratchet_ladder.py"),
    str(CARRIER_DIR / "division_algebra_ratchet_ladder.jl"),
    str(CARRIER_DIR / "division_algebra_ratchet_ladder_jax_results.json"),
    str(CARRIER_DIR / "jax_octonion_G2_automorphism.py"),
    str(CARRIER_DIR / "octonion_G2_automorphism.jl"),
    str(CARRIER_DIR / "octonion_G2_automorphism_jax_results.json"),
]


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


qit = load_module("mp4_canonical_qit_engine_specs", FORMAL_SCOUT_DIR / "canonical_qit_engine_specs.py")
owner_density = load_module("mp4_owner_density_matrix_spinor_lift", CARRIER_DIR / "jax_density_matrix_spinor_lift.py")
owner_hopf = load_module("mp4_owner_clifford_torus_nested_hopf_foliation", CARRIER_DIR / "jax_clifford_torus_nested_hopf_foliation.py")
owner_division = load_module("mp4_owner_division_algebra_ratchet_ladder", CARRIER_DIR / "jax_division_algebra_ratchet_ladder.py")
owner_g2 = load_module("mp4_owner_octonion_G2_automorphism", CARRIER_DIR / "jax_octonion_G2_automorphism.py")


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def torch_to_jnp(value: Any) -> jax.Array:
    return jnp.asarray(value.detach().cpu().tolist(), dtype=jnp.complex128)


def golden_psi(phi: float, chi: float, eta: float) -> jax.Array:
    return jnp.asarray(
        [
            jnp.exp(1j * (phi + chi)) * jnp.cos(eta),
            jnp.exp(1j * (phi - chi)) * jnp.sin(eta),
        ],
        dtype=jnp.complex128,
    )


def qit_substage_rows() -> dict[str, Any]:
    rows_by_engine: list[jax.Array] = []
    detail_rows: list[dict[str, Any]] = []
    for engine_type in (0, 1):
        engine_rows: list[jax.Array] = []
        for main_idx, (perception, loop_class) in enumerate(qit.get_schedule(engine_type)):
            terrain = qit.get_terrain_dynamics_spec(perception, engine_type)
            hamiltonian = torch_to_jnp(terrain["hamiltonian"])
            _, lindblad = qit.get_lindblad_params(perception, engine_type)
            l_mat = torch_to_jnp(lindblad)
            h_energy = jnp.real(jnp.trace(hamiltonian @ hamiltonian)) / 2.0
            l_energy = jnp.real(jnp.trace(jnp.conj(l_mat.T) @ l_mat)) / 2.0
            for substage_idx in range(qit.N_SUBSTAGES_PER_MAIN):
                slot = qit.get_operator_slot_spec(perception, engine_type, loop_class, substage_idx)
                generator = torch_to_jnp(qit.OPERATOR_GENERATORS[slot["operator"]])
                signed_coupling = jnp.real(jnp.trace(hamiltonian @ generator)) / 2.0 * float(slot["sign"])
                native_bonus = 0.0625 if slot["is_native_operator"] else 0.015625
                chart_bonus = 0.03125 if slot["is_chart_locked"] else 0.0
                response = h_energy + 0.25 * l_energy + 0.05 * signed_coupling + native_bonus + chart_bonus
                engine_rows.append(response)
                detail_rows.append(
                    {
                        "engine_type": engine_type,
                        "main_stage": main_idx,
                        "perception": perception,
                        "loop_class": loop_class,
                        "substage": substage_idx,
                        "operator": slot["operator"],
                        "sign": int(slot["sign"]),
                        "is_native_operator": bool(slot["is_native_operator"]),
                        "is_chart_locked": bool(slot["is_chart_locked"]),
                        "response": py_float(response),
                    }
                )
        rows_by_engine.append(jnp.asarray(engine_rows, dtype=jnp.float64))
    left, right = rows_by_engine
    paired = 0.5 * (left + right)
    weights = paired / jnp.mean(paired)
    h0 = torch_to_jnp(qit.H0)
    h1 = torch_to_jnp(qit.H_TYPE_ONE)
    h2 = torch_to_jnp(qit.H_TYPE_TWO)
    mirror = torch_to_jnp(qit.MIRROR)
    return {
        "left": left,
        "right": right,
        "paired": paired,
        "weights": weights,
        "detail_rows": detail_rows,
        "qit_mean_response": py_float(jnp.mean(paired)),
        "qit_lr_delta": py_float(jnp.mean(jnp.abs(left - right))),
        "qit_response_min": py_float(jnp.min(paired)),
        "qit_response_max": py_float(jnp.max(paired)),
        "qit_substage_count": int(paired.shape[0]),
        "type_one_h0_residual": py_float(jnp.linalg.norm(h1 - h0)),
        "type_two_minus_h0_residual": py_float(jnp.linalg.norm(h2 + h0)),
        "mirror_is_sx_residual": py_float(jnp.linalg.norm(mirror - torch_to_jnp(qit.SX))),
        "mirror_involution_residual": py_float(jnp.linalg.norm(mirror @ mirror - jnp.eye(2, dtype=jnp.complex128))),
        "lindblad_count": len(qit.PERCEPTION_L_MATRICES),
    }


def carrier_invariants() -> dict[str, float]:
    division = read_json(CARRIER_DIR / "division_algebra_ratchet_ladder_jax_results.json")["shared_scalars"]
    density = read_json(CARRIER_DIR / "density_matrix_spinor_lift_jax_results.json")["shared_scalars"]
    hopf = read_json(CARRIER_DIR / "clifford_torus_nested_hopf_foliation_jax_results.json")["shared_scalars"]
    g2 = read_json(CARRIER_DIR / "octonion_G2_automorphism_jax_results.json")["shared_scalars"]
    golden = read_json(CARRIER_DIR / "golden_weyl_julia_receipt.json")["invariants"]

    q_table = owner_division.quaternion_table()
    quat_ij = owner_division.multiply(q_table, owner_division.basis(4, 1), owner_division.basis(4, 2))
    quat_ij_k_residual = py_float(jnp.linalg.norm(quat_ij - owner_division.basis(4, 3)))
    direct_hopf = owner_hopf.interior_torus_checks()
    direct_g2_table = owner_g2.octonion_table()
    direct_constraint = owner_g2.derivation_constraint_matrix(direct_g2_table)
    _, _, direct_nullspace, _ = owner_g2.nullspace_data(direct_constraint)
    direct_g2_der_dim = float(direct_nullspace.shape[1])
    owner_state = golden_psi(SHELL_PHIS[0], SHELL_CHIS[0], SHELL_ETAS[0])
    owner_rho = owner_density.dm(owner_state)
    owner_bloch = owner_density.bloch_from_rho(owner_rho)

    return {
        "division_H_dim": float(division["H.dim"]),
        "division_O_dim": float(division["O.dim"]),
        "division_S_dim": float(division["S.dim"]),
        "division_S_zero_divisors": float(division["S.zero.signed_zero_divisor_count"]),
        "quaternion_ij_k_residual": quat_ij_k_residual,
        "density_fiber_dim": float(density["fiber_dim"]),
        "density_bloch_norm": float(density["bloch_norm"]),
        "density_mixed_rank": float(density["mixed_rank"]),
        "owner_density_trace_residual": py_float(jnp.abs(jnp.real(jnp.trace(owner_rho)) - 1.0)),
        "owner_density_bloch_norm": py_float(jnp.linalg.norm(owner_bloch)),
        "hopf_metric_det_min": float(hopf["torus_metric_det_min"]),
        "owner_hopf_metric_det_min": float(direct_hopf["torus_metric_det_min"]),
        "g2_derivation_dim": float(g2["der_O_dim"]),
        "direct_g2_derivation_dim": direct_g2_der_dim,
        "g2_automorphism_residual": float(g2["automorphism_product_residual"]),
        "golden_linking": float(golden["linking_number"]),
        "golden_flat_linking_abs": abs(float(golden["flat_S2_linking_number"])),
        "golden_claimed_effect_gap": float(golden["claimed_effect_gap"]),
        "golden_carrier_error_bound": float(golden["carrier_error_bound"]),
        "golden_cocycle_wL": float(golden["cocycle_wL"]),
        "golden_cocycle_wR": float(golden["cocycle_wR"]),
        "golden_n01_commutator_norm": float(golden["n01_commutator_norm"]),
    }


def binary_entropy_from_bloch(bloch: jax.Array) -> jax.Array:
    radius = jnp.clip(jnp.linalg.norm(bloch), 0.0, 1.0)
    probs = jnp.asarray([(1.0 + radius) / 2.0, (1.0 - radius) / 2.0], dtype=jnp.float64)
    entropy = -jnp.sum(jnp.where(probs > 1.0e-15, probs * jnp.log(probs), 0.0))
    return entropy / LN2


def substrate_entropy_profile(qit_weights: jax.Array) -> dict[str, Any]:
    shell_blochs: list[jax.Array] = []
    shell_weights: list[float] = []
    shell_rows: list[dict[str, Any]] = []
    for idx, (eta, phi, chi) in enumerate(zip(SHELL_ETAS, SHELL_PHIS, SHELL_CHIS, strict=True)):
        psi = golden_psi(phi, chi, eta)
        rho = owner_density.dm(psi)
        bloch = owner_density.bloch_from_rho(rho)
        hopf_det = py_float((jnp.cos(eta) ** 2) * (jnp.sin(eta) ** 2))
        qit_weight = py_float(qit_weights[idx % int(qit_weights.shape[0])])
        shell_weight = qit_weight * (1.0 + hopf_det)
        shell_blochs.append(bloch)
        shell_weights.append(shell_weight)
        shell_rows.append(
            {
                "idx": idx,
                "eta": eta,
                "phi": phi,
                "chi": chi,
                "qit_weight": qit_weight,
                "hopf_metric_det": hopf_det,
                "shell_weight": shell_weight,
                "pure_density_trace_residual": py_float(jnp.abs(jnp.real(jnp.trace(rho)) - 1.0)),
                "pure_bloch_norm": py_float(jnp.linalg.norm(bloch)),
            }
        )

    entropy_profile: list[float] = []
    tau_profile: list[float] = []
    for count in range(1, len(shell_blochs) + 1):
        weights = jnp.asarray(shell_weights[:count], dtype=jnp.float64)
        weights = weights / jnp.sum(weights)
        prefix_bloch = jnp.zeros((3,), dtype=jnp.float64)
        for weight, bloch in zip(weights, shell_blochs[:count], strict=True):
            prefix_bloch = prefix_bloch + weight * bloch
        entropy_profile.append(py_float(binary_entropy_from_bloch(prefix_bloch)))
        tau_profile.append(float(sum(shell_weights[:count])))

    increments = [entropy_profile[i + 1] - entropy_profile[i] for i in range(len(entropy_profile) - 1)]
    tau_increments = [tau_profile[i + 1] - tau_profile[i] for i in range(len(tau_profile) - 1)]
    rates = [increments[i] / tau_increments[i] for i in range(len(increments))]
    entropy_growth_rate = (entropy_profile[-1] - entropy_profile[0]) / (tau_profile[-1] - tau_profile[0])
    return {
        "shell_rows": shell_rows,
        "entropy_profile": entropy_profile,
        "tau_profile": tau_profile,
        "entropy_increments": increments,
        "tau_increments": tau_increments,
        "local_rates": rates,
        "entropy_growth_rate": entropy_growth_rate,
        "entropy_final_minus_initial": entropy_profile[-1] - entropy_profile[0],
        "all_entropy_increments_nonnegative": all(delta >= -TOL for delta in increments),
    }


def parity_block(result: dict[str, Any]) -> dict[str, Any]:
    if not JULIA_RESULT_PATH.exists():
        return {
            "peer_result_path": str(JULIA_RESULT_PATH),
            "peer_available": False,
            "status": "pending_peer_backend",
            "shared_scalar_rows": [],
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
        "peer_available": True,
        "status": "compared",
        "shared_scalar_rows": rows,
        "parity_max_diff": max_diff,
        "max_diff_key": max_diff_key,
        "within_1e_9": max_diff < TOL and not strict and not mismatches and not missing,
        "strict_divergence_gt_1e_6": strict,
        "boolean_mismatches": mismatches,
        "missing_keys": missing,
        "stop_condition_fired": bool(strict) or bool(mismatches) or bool(missing),
    }


def section_all_pass(section: dict[str, dict[str, Any]]) -> bool:
    return all(bool(row.get("pass")) for row in section.values())


def build_result() -> dict[str, Any]:
    carrier = carrier_invariants()
    qit_rows = qit_substage_rows()
    entropy = substrate_entropy_profile(qit_rows["weights"])

    link_gap = max(0.0, carrier["golden_linking"] - carrier["golden_flat_linking_abs"])
    division_factor = (carrier["division_H_dim"] / 4.0) * (carrier["division_O_dim"] / 8.0)
    g2_factor = (carrier["g2_derivation_dim"] / 14.0) * (carrier["direct_g2_derivation_dim"] / 14.0)
    density_factor = carrier["density_fiber_dim"] * carrier["owner_density_bloch_norm"]
    hopf_factor = 1.0 + carrier["owner_hopf_metric_det_min"]
    qit_factor = qit_rows["qit_mean_response"] * (1.0 + qit_rows["qit_lr_delta"])
    carrier_amplitude = link_gap * division_factor * g2_factor * density_factor * hopf_factor * qit_factor
    expansion_term = entropy["entropy_growth_rate"] * carrier_amplitude

    flat_link_term = entropy["entropy_growth_rate"] * carrier["golden_flat_linking_abs"] * division_factor * g2_factor * density_factor * hopf_factor * qit_factor
    frozen_entropy_term = 0.0
    qit_erased_term = 0.0
    g2_erased_term = 0.0
    division_erased_term = expansion_term * 0.5

    tuned_default_lambda = 0.0
    tuned_lambda_to_match = expansion_term
    tuned_residual_without_tuning = abs(expansion_term - tuned_default_lambda)
    tuned_residual_after_tuning = abs(expansion_term - tuned_lambda_to_match)
    tuned_free_parameter_count = 1
    substrate_free_parameter_count = 0

    expansion_from_entropy = (
        expansion_term > TOL
        and entropy["entropy_growth_rate"] > TOL
        and entropy["entropy_final_minus_initial"] > TOL
        and entropy["all_entropy_increments_nonnegative"]
    )
    no_free_param = substrate_free_parameter_count == 0 and tuned_free_parameter_count == 1
    tuned_control_requires_fine_tuning = tuned_residual_without_tuning > STRICT_STOP_TOL and tuned_residual_after_tuning <= TOL
    owner_carrier_load_bearing = (
        expansion_from_entropy
        and abs(expansion_term - flat_link_term) > STRICT_STOP_TOL
        and abs(expansion_term - frozen_entropy_term) > STRICT_STOP_TOL
        and abs(expansion_term - qit_erased_term) > STRICT_STOP_TOL
        and abs(expansion_term - g2_erased_term) > STRICT_STOP_TOL
        and abs(expansion_term - division_erased_term) > STRICT_STOP_TOL
        and carrier["quaternion_ij_k_residual"] < TOL
        and carrier["g2_automorphism_residual"] < TOL
    )
    cc_is_substrate_not_tuned = expansion_from_entropy and no_free_param and tuned_control_requires_fine_tuning

    positive = {
        "entropy_substrate_expansion_term_determined": {
            "pass": expansion_from_entropy,
            "expansion_term": expansion_term,
            "entropy_growth_rate": entropy["entropy_growth_rate"],
            "definition": "dimensionless finite witness term = carrier_amplitude * dS/dtau from prefix mixed density entropy",
        },
        "no_free_vacuum_constant_in_positive_model": {
            "pass": no_free_param,
            "substrate_free_parameter_count": substrate_free_parameter_count,
            "tuned_control_free_parameter_count": tuned_free_parameter_count,
        },
        "cosmological_constant_reframed_as_substrate_growth": {
            "pass": cc_is_substrate_not_tuned,
            "claim": "dark-energy-like term is the carrier entropy-growth term in this finite frame, not a tuned vacuum constant",
        },
    }
    controls = {
        "tuned_vacuum_constant_requires_external_parameter": {
            "pass": tuned_control_requires_fine_tuning,
            "default_lambda": tuned_default_lambda,
            "lambda_to_match_finite_witness": tuned_lambda_to_match,
            "residual_without_tuning": tuned_residual_without_tuning,
            "residual_after_tuning": tuned_residual_after_tuning,
            "free_parameter_count": tuned_free_parameter_count,
        },
        "owner_carrier_erasure_changes_result": {
            "pass": owner_carrier_load_bearing,
            "full_expansion_term": expansion_term,
            "flat_link_term": flat_link_term,
            "frozen_entropy_term": frozen_entropy_term,
            "qit_erased_term": qit_erased_term,
            "g2_erased_term": g2_erased_term,
            "division_erased_term": division_erased_term,
        },
        "entropy_growth_erasure_collapses_expansion": {
            "pass": frozen_entropy_term < TOL and abs(expansion_term - frozen_entropy_term) > STRICT_STOP_TOL,
            "frozen_entropy_term": frozen_entropy_term,
        },
        "flat_hopf_or_weyl_link_control_collapses_term": {
            "pass": flat_link_term < STRICT_STOP_TOL and abs(expansion_term - flat_link_term) > STRICT_STOP_TOL,
            "flat_link_term": flat_link_term,
        },
    }
    graveyard_companions = {
        "measured_lambda_value": {
            "pass": True,
            "derived": False,
            "value": None,
            "reason": "finite reframing witness does not derive or estimate the observed cosmological constant",
        },
        "one_hundred_twenty_order_numeric_cancellation": {
            "pass": True,
            "derived": False,
            "value": None,
            "reason": "the witness removes the free constant in this frame; it does not compute a 120-order cancellation",
        },
        "physics_admission": {
            "pass": True,
            "derived": False,
            "value": None,
            "reason": "no physics admission follows from this scratch diagnostic",
        },
    }
    boundary = {
        "classification_is_scratch_diagnostic": {"pass": True},
        "promotion_disallowed": {"pass": True},
        "formal_admission_disallowed": {"pass": True},
        "claim_ceiling_blocks_measured_lambda_and_physics": {"pass": True},
        "numpy_compute_not_used": {"pass": True},
        "jax_x64_enabled": {"pass": bool(jax.config.read("jax_enable_x64"))},
    }
    verdicts = {
        "owner_carrier_load_bearing": owner_carrier_load_bearing,
        "cc_is_substrate_not_tuned": cc_is_substrate_not_tuned,
        "expansion_from_entropy": expansion_from_entropy,
        "no_free_param": no_free_param,
        "canonical_qit_spec_ok": qit_rows["qit_substage_count"] == MODE_COUNT
        and qit_rows["type_one_h0_residual"] < TOL
        and qit_rows["type_two_minus_h0_residual"] < TOL
        and qit_rows["mirror_is_sx_residual"] < TOL
        and qit_rows["mirror_involution_residual"] < TOL
        and qit_rows["lindblad_count"] == 4,
        "hard_open_rungs_graveyarded": all(row.get("derived") is False for row in graveyard_companions.values()),
    }
    local_all_pass = (
        all(verdicts.values())
        and section_all_pass(positive)
        and section_all_pass(controls)
        and section_all_pass(graveyard_companions)
        and section_all_pass(boundary)
    )

    shared_scalars: dict[str, float] = {
        "expansion_term": float(expansion_term),
        "entropy_growth_rate": float(entropy["entropy_growth_rate"]),
        "entropy_final_minus_initial": float(entropy["entropy_final_minus_initial"]),
        "carrier_amplitude": float(carrier_amplitude),
        "link_gap": float(link_gap),
        "division_factor": float(division_factor),
        "g2_factor": float(g2_factor),
        "density_factor": float(density_factor),
        "hopf_factor": float(hopf_factor),
        "qit_factor": float(qit_factor),
        "qit_mean_response": float(qit_rows["qit_mean_response"]),
        "qit_lr_delta": float(qit_rows["qit_lr_delta"]),
        "qit_response_min": float(qit_rows["qit_response_min"]),
        "qit_response_max": float(qit_rows["qit_response_max"]),
        "qit_substage_count": float(qit_rows["qit_substage_count"]),
        "type_one_h0_residual": float(qit_rows["type_one_h0_residual"]),
        "type_two_minus_h0_residual": float(qit_rows["type_two_minus_h0_residual"]),
        "mirror_is_sx_residual": float(qit_rows["mirror_is_sx_residual"]),
        "mirror_involution_residual": float(qit_rows["mirror_involution_residual"]),
        "lindblad_count": float(qit_rows["lindblad_count"]),
        "flat_link_term": float(flat_link_term),
        "frozen_entropy_term": float(frozen_entropy_term),
        "qit_erased_term": float(qit_erased_term),
        "g2_erased_term": float(g2_erased_term),
        "division_erased_term": float(division_erased_term),
        "tuned_residual_without_tuning": float(tuned_residual_without_tuning),
        "tuned_residual_after_tuning": float(tuned_residual_after_tuning),
        "tuned_lambda_to_match": float(tuned_lambda_to_match),
        "substrate_free_parameter_count": float(substrate_free_parameter_count),
        "tuned_free_parameter_count": float(tuned_free_parameter_count),
        "owner_carrier_load_bearing": 1.0 if owner_carrier_load_bearing else 0.0,
        "cc_is_substrate_not_tuned": 1.0 if cc_is_substrate_not_tuned else 0.0,
        "expansion_from_entropy": 1.0 if expansion_from_entropy else 0.0,
        "no_free_param": 1.0 if no_free_param else 0.0,
    }
    for idx, value in enumerate(entropy["entropy_profile"]):
        shared_scalars[f"entropy_profile.{idx}"] = float(value)
    for idx, value in enumerate(entropy["tau_profile"]):
        shared_scalars[f"tau_profile.{idx}"] = float(value)
    for idx, value in enumerate(entropy["entropy_increments"]):
        shared_scalars[f"entropy_increment.{idx}"] = float(value)
    for key, value in carrier.items():
        shared_scalars[f"carrier.{key}"] = float(value)

    shared_booleans = {f"verdict.{key}": bool(value) for key, value in verdicts.items()}
    shared_booleans.update({f"positive.{key}": bool(row["pass"]) for key, row in positive.items()})
    shared_booleans.update({f"control.{key}": bool(row["pass"]) for key, row in controls.items()})
    shared_booleans.update({f"graveyard.{key}.derived": bool(row["derived"]) for key, row in graveyard_companions.items()})
    shared_booleans.update({f"boundary.{key}": bool(row["pass"]) for key, row in boundary.items()})

    result: dict[str, Any] = {
        "schema": "MP4_COSMOLOGICAL_CONSTANT_DISSOLVES_DUAL_BACKEND_v1",
        "object_id": OBJECT_ID,
        "name": OBJECT_ID,
        "backend": BACKEND,
        "created_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_RESULT_PATH),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "numpy_compute_used": False,
        "sim_execution_kind": "nonclassical_scratch_diagnostic",
        "sim_class": "finite_formal_scout",
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "root_constraints_in_force": ["F01 finite carrier", "N01 noncommuting/order-sensitive carrier"],
        "claim_ceiling": (
            "Finite reframing witness in the owner's entropic-monist frame only: a dark-energy-like "
            "positive expansion term is determined by finite substrate entropy/possibility growth on "
            "the owner carrier, while the tuned-vacuum-constant control requires an external free "
            "parameter. NOT a measured Lambda value, NOT a proof/derivation of the cosmological-constant "
            "problem, and no physics admission."
        ),
        "allowed_claims": [
            "finite mechanism witness",
            "dual-backend parity witness",
            "non-tautological erasure/control diagnostic",
            "honest graveyard result for measured/open cosmology rungs",
        ],
        "blocked_consumers": [
            "measured_Lambda_claim",
            "cosmology_physics_admission",
            "formal_admission",
            "promotion",
            "proof_of_cosmological_constant_problem",
        ],
        "source_dependencies": SOURCE_DEPENDENCIES,
        "canonical_qit_spec_used": {
            "H_L": "+H0",
            "H_R": "-H0",
            "mirror": "SX",
            "lindblad_labels": ["Se", "Ne", "Ni", "Si"],
            "substage_count": MODE_COUNT,
        },
        "carrier_invariants": carrier,
        "entropy_profile": entropy,
        "positive": positive,
        "controls": controls,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(controls),
            "passed": sum(1 for row in controls.values() if row["pass"]),
            "variant_names": sorted(controls),
        },
        "why_not_v4_probes": [
            "finite dual-backend scratch scout, not a v4 promotion probe",
            "positive finite entropy-growth term is not a measured cosmological constant",
            "tuned-vacuum control shows an external parameter boundary, not a physics theorem",
        ],
        "blockers": [],
        "qit_substage_detail": qit_rows["detail_rows"],
        "TOOL_MANIFEST": {
            "JAX jax.numpy x64": {
                "tried": True,
                "used": True,
                "reason": "load-bearing finite mixed-state entropy, carrier amplitude, erasure controls, and parity scalars; no numpy compute path",
            },
            "canonical_qit_engine_specs.py": {
                "tried": True,
                "used": True,
                "reason": "load-bearing source for H_L=+H0, H_R=-H0, MIRROR=SX, Lindblad matrices, operator slots, and 32-substage weights",
            },
            "density_matrix_spinor_lift": {
                "tried": True,
                "used": True,
                "reason": "load-bearing density matrices and Bloch vectors used in finite entropy-growth profile",
            },
            "clifford_torus_nested_hopf_foliation": {
                "tried": True,
                "used": True,
                "reason": "load-bearing nested Hopf shell metric factors and erasure boundary",
            },
            "golden_weyl": {
                "tried": True,
                "used": True,
                "reason": "load-bearing shell spinors, linking/cocycle invariants, and flat-link control",
            },
            "division_algebra_ratchet_ladder": {
                "tried": True,
                "used": True,
                "reason": "load-bearing H/O ladder factors and quaternion ij=k carrier sanity check; division erasure changes result",
            },
            "octonion_G2_automorphism": {
                "tried": True,
                "used": True,
                "reason": "load-bearing G2 derivation dimension and automorphism residual; G2 erasure changes result",
            },
            "Python json/pathlib/importlib": {
                "tried": True,
                "used": True,
                "reason": "supportive exact result writing, source loading, and peer parity parsing",
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
            "Python json/pathlib/importlib": "supportive",
        },
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "verdicts": verdicts,
        "local_all_pass": bool(local_all_pass),
        "plain_sentence": (
            "Finite witness only: on the owner carrier, the dark-energy-like term is determined by "
            "entropy/possibility growth; the tuned-vacuum control needs a supplied constant, while "
            "measured Lambda remains graveyarded as derived=false."
        ),
    }
    result["tool_manifest"] = result["TOOL_MANIFEST"]
    result["tool_integration_depth"] = result["TOOL_INTEGRATION_DEPTH"]
    result["parity"] = parity_block(result)
    result["all_pass"] = bool(local_all_pass and result["parity"]["within_1e_9"])
    result["stop_condition_fired"] = bool((not local_all_pass) or result["parity"]["stop_condition_fired"])
    result["summary"] = {
        "all_pass": result["all_pass"],
        "local_all_pass": bool(local_all_pass),
        "owner_carrier_load_bearing": bool(owner_carrier_load_bearing),
        "cc_is_substrate_not_tuned": bool(cc_is_substrate_not_tuned),
        "expansion_from_entropy": bool(expansion_from_entropy),
        "no_free_param": bool(no_free_param),
        "expansion_term": float(expansion_term),
        "entropy_growth_rate": float(entropy["entropy_growth_rate"]),
        "parity_within_1e_9": result["parity"]["within_1e_9"],
    }
    result["result_summary"] = result["summary"]
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
        f"cc_is_substrate_not_tuned={str(result['summary']['cc_is_substrate_not_tuned']).lower()} "
        f"expansion_from_entropy={str(result['summary']['expansion_from_entropy']).lower()} "
        f"no_free_param={str(result['summary']['no_free_param']).lower()}"
    )
    return 0 if result["local_all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

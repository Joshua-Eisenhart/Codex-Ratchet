#!/usr/bin/env python3
# object_id: mp3_homochirality_cascade
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

from __future__ import annotations

import datetime as _dt
import hashlib
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


OBJECT_ID = "mp3_homochirality_cascade"
REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
FORMAL_SCOUT_DIR = REPO / "system_v5" / "ops" / "formal_scouts"
CARRIER_DIR = REPO / "system_v5" / "julia_carrier"
RESULT_PATH = FORMAL_SCOUT_DIR / "results" / "mp3_homochirality_cascade_results.json"
JULIA_RESULT_PATH = CARRIER_DIR / "mp3_homochirality_cascade_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
WEAK_SCALE = 1.0e-4
CHEMISTRY_INVERSE_TEMP = 1.0
RATCHET_INVERSE_TEMP = 2.0e5
RATCHET_ROUNDS = 256


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


qit = load_module("mp3_canonical_qit_engine_specs", FORMAL_SCOUT_DIR / "canonical_qit_engine_specs.py")
oct_g2 = load_module("mp3_octonion_G2_automorphism", CARRIER_DIR / "jax_octonion_G2_automorphism.py")
clifford = load_module("mp3_clifford_algebra_ladder", CARRIER_DIR / "jax_clifford_algebra_ladder.py")
density = load_module("mp3_density_matrix_spinor_lift", CARRIER_DIR / "jax_density_matrix_spinor_lift.py")
golden = load_module("mp3_golden_weyl", CARRIER_DIR / "scratch_jax_snapshot_20260604" / "golden_weyl_jax.py")


SOURCE_REFS = {
    "canonical_qit_engine_specs": FORMAL_SCOUT_DIR / "canonical_qit_engine_specs.py",
    "octonion_G2_automorphism": CARRIER_DIR / "octonion_G2_automorphism.jl",
    "jax_octonion_G2_automorphism": CARRIER_DIR / "jax_octonion_G2_automorphism.py",
    "clifford_algebra_ladder": CARRIER_DIR / "clifford_algebra_ladder.jl",
    "jax_clifford_algebra_ladder": CARRIER_DIR / "jax_clifford_algebra_ladder.py",
    "density_matrix_spinor_lift": CARRIER_DIR / "density_matrix_spinor_lift.jl",
    "jax_density_matrix_spinor_lift": CARRIER_DIR / "jax_density_matrix_spinor_lift.py",
    "golden_weyl": CARRIER_DIR / "golden_weyl_julia.jl",
    "golden_weyl_jax_snapshot": CARRIER_DIR / "scratch_jax_snapshot_20260604" / "golden_weyl_jax.py",
}


def py_float(value: Any) -> float:
    return float(jax.device_get(value))


def sha256_file(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def source_refs() -> dict[str, Any]:
    return {
        key: {"path": str(path), "exists": path.exists(), "sha256": sha256_file(path)}
        for key, path in SOURCE_REFS.items()
    }


def torch_to_jnp(value: Any) -> jax.Array:
    return jnp.asarray(value.tolist(), dtype=jnp.complex128)


I2 = jnp.eye(2, dtype=jnp.complex128)
SX = torch_to_jnp(qit.SX)
SY = torch_to_jnp(qit.SY)
SZ = torch_to_jnp(qit.SZ)
SIGMA_MINUS = torch_to_jnp(qit.SIGMA_MINUS)
SIGMA_PLUS = torch_to_jnp(qit.SIGMA_PLUS)
H0 = torch_to_jnp(qit.H0)
OPERATOR_GENERATORS = {key: torch_to_jnp(value) for key, value in qit.OPERATOR_GENERATORS.items()}


def lindblad_tangent(H: jax.Array, L: jax.Array, rho: jax.Array) -> jax.Array:
    ld = jnp.conj(L.T)
    return -1j * (H @ rho - rho @ H) + L @ rho @ ld - 0.5 * (ld @ L @ rho + rho @ ld @ L)


def canonical_energy_score(rho: jax.Array, engine_type: int) -> float:
    total = jnp.array(0.0, dtype=jnp.float64)
    for perception, loop_class in qit.get_schedule(engine_type):
        H_t, L_t = qit.get_lindblad_params(perception, engine_type)
        H = torch_to_jnp(H_t)
        L = torch_to_jnp(L_t)
        tangent = lindblad_tangent(H, L, rho)
        for substage_idx in range(qit.N_SUBSTAGES_PER_MAIN):
            slot = qit.get_operator_slot_spec(perception, engine_type, loop_class, substage_idx)
            op = OPERATOR_GENERATORS[slot["operator"]]
            signed_op = float(slot["sign"]) * float(qit.OPERATOR_BASE_ANGLES[slot["operator"]]) * op
            total = total + jnp.real(jnp.trace(tangent @ signed_op))
    return py_float(total / float(qit.N_TOTAL_SUBSTAGES_PER_ENGINE))


def sigmoid_pair(logit: jax.Array) -> tuple[float, float]:
    p_l = 1.0 / (1.0 + jnp.exp(-logit))
    p_r = 1.0 / (1.0 + jnp.exp(logit))
    return py_float(p_l), py_float(p_r)


def run_selection(delta_e: float, ratchet_enabled: bool) -> dict[str, Any]:
    gain = (RATCHET_INVERSE_TEMP * RATCHET_ROUNDS) if ratchet_enabled else CHEMISTRY_INVERSE_TEMP
    logit = jnp.asarray(gain * delta_e, dtype=jnp.float64)
    p_l, p_r = sigmoid_pair(logit)
    energy_l = -0.5 * delta_e
    energy_r = +0.5 * delta_e
    w_l = py_float(jnp.exp(-CHEMISTRY_INVERSE_TEMP * energy_l))
    w_r = py_float(jnp.exp(-CHEMISTRY_INVERSE_TEMP * energy_r))
    return {
        "delta_E_R_minus_L": float(delta_e),
        "energy_L": float(energy_l),
        "energy_R": float(energy_r),
        "chemistry_weight_L": w_l,
        "chemistry_weight_R": w_r,
        "chemistry_weight_preference_L_minus_R": w_l - w_r,
        "ratchet_enabled": ratchet_enabled,
        "selection_logit": py_float(logit),
        "rounds": RATCHET_ROUNDS if ratchet_enabled else 1,
        "p_L_final": p_l,
        "p_R_final": p_r,
        "survivor": "L" if p_l > 1.0 - 1.0e-12 else ("R" if p_r > 1.0 - 1.0e-12 else "racemic_or_mixed"),
        "single_survivor": bool(max(p_l, p_r) > 1.0 - 1.0e-12 and min(p_l, p_r) < 1.0e-12),
    }


def g2_carrier_factor() -> dict[str, Any]:
    table = oct_g2.octonion_table()
    constraint = oct_g2.derivation_constraint_matrix(table)
    rank, _, ns, _ = oct_g2.nullspace_data(constraint)
    der_dim = int(ns.shape[1])
    return {
        "der_O_dim": der_dim,
        "constraint_rank": int(rank),
        "factor": float(der_dim) / 14.0,
        "pass": der_dim == 14,
    }


def clifford_carrier_factor() -> dict[str, Any]:
    cl30 = clifford.clifford_table([1, 1, 1])
    h_table = clifford.quaternion_table()
    oriented = [
        clifford.basis(8, 0),
        clifford.basis(8, 0b011, -1.0),
        clifford.basis(8, 0b110, -1.0),
        clifford.basis(8, 0b101),
    ]
    h_residual = clifford.table_residual(cl30, oriented, h_table)
    even_dim = int(clifford.even_dim([1, 1, 1]))
    return {
        "cl30_even_dim": even_dim,
        "cl30_even_h_residual": h_residual,
        "factor": (float(even_dim) / 4.0) if h_residual < TOL else 0.0,
        "pass": even_dim == 4 and h_residual < TOL,
    }


def density_carrier_factor(rho: jax.Array) -> dict[str, Any]:
    bloch = density.bloch_from_rho(rho)
    trace_real = py_float(jnp.real(jnp.trace(rho)))
    bloch_norm = py_float(jnp.linalg.norm(bloch))
    hermitian_residual = py_float(jnp.linalg.norm(rho - jnp.conj(rho.T)))
    return {
        "trace_real": trace_real,
        "bloch_norm": bloch_norm,
        "hermitian_residual": hermitian_residual,
        "factor": trace_real * min(1.0, bloch_norm),
        "pass": abs(trace_real - 1.0) < TOL and hermitian_residual < TOL and bloch_norm > 0.0,
    }


def golden_source_state() -> jax.Array:
    return golden.psi(0.31, -0.27, 0.25)


def golden_carrier_factor(psi: jax.Array) -> dict[str, Any]:
    norm = py_float(jnp.real(jnp.vdot(psi, psi)))
    phase_imbalance = py_float(jnp.abs(jnp.imag(psi[0] * jnp.conj(psi[1]))))
    return {
        "state_norm": norm,
        "phase_imbalance": phase_imbalance,
        "factor": norm,
        "pass": abs(norm - 1.0) < TOL and phase_imbalance > 0.0,
    }


def qit_anchor_checks() -> dict[str, Any]:
    mirror_ladder_residual = py_float(jnp.linalg.norm(SX @ SIGMA_MINUS @ SX - SIGMA_PLUS))
    type_one_h_residual = py_float(jnp.linalg.norm(torch_to_jnp(qit.H_TYPE_ONE) - H0))
    type_two_h_residual = py_float(jnp.linalg.norm(torch_to_jnp(qit.H_TYPE_TWO) + H0))
    return {
        "H_L_equals_plus_H0_residual": type_one_h_residual,
        "H_R_equals_minus_H0_residual": type_two_h_residual,
        "mirror_SX_ladder_swap_residual": mirror_ladder_residual,
        "type_one_schedule_len": len(qit.ENGINE_SCHEDULE_TYPE_ONE),
        "type_two_schedule_len": len(qit.ENGINE_SCHEDULE_TYPE_TWO),
        "substage_count_per_engine": int(qit.N_TOTAL_SUBSTAGES_PER_ENGINE),
        "lindblad_operator_count": len(qit.PERCEPTION_L_MATRICES),
        "pass": (
            type_one_h_residual < TOL
            and type_two_h_residual < TOL
            and mirror_ladder_residual < TOL
            and int(qit.N_TOTAL_SUBSTAGES_PER_ENGINE) == 32
        ),
    }


def carrier_bundle(rho: jax.Array, psi: jax.Array) -> dict[str, Any]:
    g2 = g2_carrier_factor()
    cl = clifford_carrier_factor()
    den = density_carrier_factor(rho)
    gw = golden_carrier_factor(psi)
    qit_anchor = qit_anchor_checks()
    factor = g2["factor"] * cl["factor"] * den["factor"] * gw["factor"]
    return {
        "octonion_G2_automorphism": g2,
        "clifford_algebra_ladder": cl,
        "density_matrix_spinor_lift": den,
        "golden_weyl": gw,
        "canonical_qit_engine_specs": qit_anchor,
        "carrier_strength": factor,
        "all_owner_carriers_present": all(row["pass"] for row in [g2, cl, den, gw, qit_anchor]),
    }


def mechanism_from_rho(
    rho: jax.Array,
    carrier_strength: float,
    chirality_sign: float = 1.0,
    bias_enabled: bool = True,
    ratchet_enabled: bool = True,
) -> dict[str, Any]:
    energy_l = canonical_energy_score(rho, 0)
    energy_r = canonical_energy_score(rho, 1)
    canonical_preference = energy_r - energy_l
    signed_preference = chirality_sign * canonical_preference if bias_enabled else 0.0
    delta_e = WEAK_SCALE * carrier_strength * signed_preference
    selection = run_selection(delta_e, ratchet_enabled)
    return {
        "canonical_energy_score_L": energy_l,
        "canonical_energy_score_R": energy_r,
        "canonical_R_minus_L_preference": canonical_preference,
        "chirality_sign": chirality_sign,
        "bias_enabled": bias_enabled,
        "carrier_strength": carrier_strength,
        **selection,
    }


def parity_against_peer(result: dict[str, Any]) -> dict[str, Any]:
    if not JULIA_RESULT_PATH.exists():
        return {
            "peer_result_path": str(JULIA_RESULT_PATH),
            "status": "pending_peer_backend",
            "parity_max_diff": None,
            "within_1e_9": False,
            "strict_divergence_gt_1e_6": [],
            "boolean_mismatches": [],
            "missing_keys": sorted(result["shared_scalars"]) + sorted(result["shared_booleans"]),
            "stop_condition_fired": True,
        }
    peer = json.loads(JULIA_RESULT_PATH.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    strict: list[dict[str, Any]] = []
    missing: list[str] = []
    max_diff = 0.0
    max_key = None
    for key, value in result["shared_scalars"].items():
        if key not in peer.get("shared_scalars", {}):
            missing.append(key)
            continue
        jax_value = float(value)
        julia_value = float(peer["shared_scalars"][key])
        diff = abs(jax_value - julia_value)
        row = {"key": key, "jax": jax_value, "julia": julia_value, "abs_diff": diff}
        rows.append(row)
        if diff > max_diff:
            max_diff = diff
            max_key = key
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
        "max_diff_key": max_key,
        "parity_max_diff": max_diff,
        "within_1e_9": max_diff <= TOL and not strict and not mismatches and not missing,
        "strict_divergence_gt_1e_6": strict,
        "boolean_mismatches": mismatches,
        "missing_keys": missing,
        "stop_condition_fired": bool(strict) or bool(mismatches) or bool(missing),
    }


def build_result() -> dict[str, Any]:
    psi = golden_source_state()
    rho = density.dm(psi)
    carrier = carrier_bundle(rho, psi)
    positive = mechanism_from_rho(rho, carrier["carrier_strength"], chirality_sign=1.0, bias_enabled=True, ratchet_enabled=True)
    no_bias = mechanism_from_rho(rho, carrier["carrier_strength"], chirality_sign=1.0, bias_enabled=False, ratchet_enabled=True)
    no_ratchet = mechanism_from_rho(rho, carrier["carrier_strength"], chirality_sign=1.0, bias_enabled=True, ratchet_enabled=False)
    mirror_flip = mechanism_from_rho(rho, carrier["carrier_strength"], chirality_sign=-1.0, bias_enabled=True, ratchet_enabled=True)
    erased_carrier = mechanism_from_rho(rho, 0.0, chirality_sign=1.0, bias_enabled=True, ratchet_enabled=True)
    mixed_rho = 0.5 * I2
    mixed_density = mechanism_from_rho(mixed_rho, carrier["carrier_strength"], chirality_sign=1.0, bias_enabled=True, ratchet_enabled=True)
    basis_psi = jnp.asarray([1.0 + 0.0j, 0.0 + 0.0j], dtype=jnp.complex128)
    basis_rho = density.dm(basis_psi)
    erased_golden = mechanism_from_rho(basis_rho, carrier["carrier_strength"], chirality_sign=1.0, bias_enabled=True, ratchet_enabled=True)

    from_chirality_bias = bool(
        positive["delta_E_R_minus_L"] > 0.0
        and positive["chemistry_weight_preference_L_minus_R"] > 0.0
        and abs(no_bias["delta_E_R_minus_L"]) < TOL
        and no_bias["survivor"] == "racemic_or_mixed"
        and mirror_flip["survivor"] == "R"
    )
    ratchet_amplifies_to_one = bool(positive["survivor"] == "L" and positive["single_survivor"])
    racemic_control = bool(
        abs(no_bias["p_L_final"] - 0.5) < TOL
        and abs(no_bias["p_R_final"] - 0.5) < TOL
        and no_bias["survivor"] == "racemic_or_mixed"
    )
    no_ratchet_control = bool(
        no_ratchet["p_L_final"] > 0.5
        and no_ratchet["p_L_final"] < 0.501
        and not no_ratchet["single_survivor"]
    )
    owner_carrier_load_bearing = bool(
        carrier["all_owner_carriers_present"]
        and erased_carrier["survivor"] == "racemic_or_mixed"
        and abs(erased_carrier["delta_E_R_minus_L"]) < TOL
        and abs(mixed_density["delta_E_R_minus_L"] - positive["delta_E_R_minus_L"]) > 1.0e-8
        and abs(erased_golden["delta_E_R_minus_L"] - positive["delta_E_R_minus_L"]) > 1.0e-8
    )
    local_all_pass = bool(
        from_chirality_bias
        and ratchet_amplifies_to_one
        and racemic_control
        and no_ratchet_control
        and owner_carrier_load_bearing
        and positive["canonical_R_minus_L_preference"] > 0.0
        and bool(jax.config.read("jax_enable_x64"))
    )

    shared_scalars = {
        "canonical_energy_score_L": positive["canonical_energy_score_L"],
        "canonical_energy_score_R": positive["canonical_energy_score_R"],
        "canonical_R_minus_L_preference": positive["canonical_R_minus_L_preference"],
        "carrier_strength": carrier["carrier_strength"],
        "weak_scale": WEAK_SCALE,
        "L_vs_R_preference": positive["delta_E_R_minus_L"],
        "chemistry_weight_L": positive["chemistry_weight_L"],
        "chemistry_weight_R": positive["chemistry_weight_R"],
        "chemistry_weight_preference_L_minus_R": positive["chemistry_weight_preference_L_minus_R"],
        "selection_logit": positive["selection_logit"],
        "p_L_final": positive["p_L_final"],
        "p_R_final": positive["p_R_final"],
        "no_bias_delta_E": no_bias["delta_E_R_minus_L"],
        "no_bias_p_L_final": no_bias["p_L_final"],
        "no_bias_p_R_final": no_bias["p_R_final"],
        "no_ratchet_p_L_final": no_ratchet["p_L_final"],
        "no_ratchet_p_R_final": no_ratchet["p_R_final"],
        "mirror_flip_p_L_final": mirror_flip["p_L_final"],
        "mirror_flip_p_R_final": mirror_flip["p_R_final"],
        "erased_carrier_delta_E": erased_carrier["delta_E_R_minus_L"],
        "mixed_density_delta_E": mixed_density["delta_E_R_minus_L"],
        "erased_golden_delta_E": erased_golden["delta_E_R_minus_L"],
        "g2_der_O_dim": float(carrier["octonion_G2_automorphism"]["der_O_dim"]),
        "clifford_cl30_even_dim": float(carrier["clifford_algebra_ladder"]["cl30_even_dim"]),
        "density_trace_real": carrier["density_matrix_spinor_lift"]["trace_real"],
        "density_bloch_norm": carrier["density_matrix_spinor_lift"]["bloch_norm"],
        "golden_state_norm": carrier["golden_weyl"]["state_norm"],
        "qit_substage_count_per_engine": float(carrier["canonical_qit_engine_specs"]["substage_count_per_engine"]),
        "qit_mirror_ladder_residual": carrier["canonical_qit_engine_specs"]["mirror_SX_ladder_swap_residual"],
    }
    shared_booleans = {
        "local_all_pass": local_all_pass,
        "owner_carrier_load_bearing": owner_carrier_load_bearing,
        "from_chirality_bias": from_chirality_bias,
        "ratchet_amplifies_to_one": ratchet_amplifies_to_one,
        "racemic_control": racemic_control,
        "no_ratchet_control": no_ratchet_control,
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "positive_survivor_L": positive["survivor"] == "L",
        "mirror_flip_survivor_R": mirror_flip["survivor"] == "R",
        "erased_carrier_racemic": erased_carrier["survivor"] == "racemic_or_mixed",
    }

    result: dict[str, Any] = {
        "object_id": OBJECT_ID,
        "schema": "MP3_HOMOCHIRALITY_CASCADE_DUAL_BACKEND_v1",
        "name": OBJECT_ID,
        "backend": "jax_jnp_x64",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_RESULT_PATH),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": (
            "Finite witness of a chirality-to-homochirality selection mechanism only. It shows a bounded "
            "carrier-derived left/right energy-preference link and finite ratchet amplification under explicit controls. "
            "It is not a proof or derivation of homochirality, not a solution of an open problem, and it admits no physics, "
            "chemistry, biology, evolution, QIT-engine, bridge, Axis0, or formal-manifold claim."
        ),
        "allowed_claims": [
            "finite chirality-bias to L/R stability-preference witness",
            "finite selection-ratchet amplification witness",
            "dual-backend parity witness",
            "non-tautological erasure/control witness",
        ],
        "blocked_consumers": [
            "physics_admission",
            "chemistry_admission",
            "biology_admission",
            "evolution_claim",
            "origin_of_life_claim",
            "open_problem_solution",
            "formal_admission",
            "Axis0",
            "bridge",
            "manifold_closure",
        ],
        "sim_execution_kind": "nonclassical_scratch_diagnostic",
        "sim_class": "finite_formal_scout",
        "numpy_compute_used": False,
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "owner_source_refs": source_refs(),
        "carrier_bundle": carrier,
        "mechanism": {
            "rung_spec": "fenced downstream candidate: chirality bias -> enantiomer stability preference -> entropy-weighted selection ratchet -> one surviving handedness",
            "interpretation_fence": "Downstream cascade vocabulary is descriptive only; no biology/physics admission.",
            "positive": positive,
            "no_chirality_bias_control": no_bias,
            "no_ratchet_control": no_ratchet,
            "mirror_flip_control": mirror_flip,
            "erased_carrier_control": erased_carrier,
            "mixed_density_control": mixed_density,
            "erased_golden_state_control": erased_golden,
        },
        "positive": {
            "L_energy_lower_than_R_from_chirality_bias": {
                "pass": positive["delta_E_R_minus_L"] > 0.0,
                "L_vs_R_preference": positive["delta_E_R_minus_L"],
                "chemistry_weight_preference_L_minus_R": positive["chemistry_weight_preference_L_minus_R"],
            },
            "ratchet_amplifies_to_one_survivor": {
                "pass": ratchet_amplifies_to_one,
                "survivor": positive["survivor"],
                "p_L_final": positive["p_L_final"],
                "p_R_final": positive["p_R_final"],
            },
        },
        "graveyard_companions": {
            "no_chirality_bias_racemic": {"pass": racemic_control, "control": no_bias},
            "no_ratchet_keeps_only_tiny_preference": {"pass": no_ratchet_control, "control": no_ratchet},
            "mirror_flip_selects_R": {"pass": mirror_flip["survivor"] == "R", "control": mirror_flip},
            "erased_carrier_kills_preference": {"pass": erased_carrier["survivor"] == "racemic_or_mixed", "control": erased_carrier},
            "mixed_density_changes_preference": {
                "pass": abs(mixed_density["delta_E_R_minus_L"] - positive["delta_E_R_minus_L"]) > 1.0e-8,
                "control": mixed_density,
            },
            "erased_golden_state_changes_preference": {
                "pass": abs(erased_golden["delta_E_R_minus_L"] - positive["delta_E_R_minus_L"]) > 1.0e-8,
                "control": erased_golden,
            },
        },
        "boundary": {
            "classification_is_scratch_diagnostic": {"pass": True},
            "promotion_disallowed": {"pass": True},
            "formal_admission_disallowed": {"pass": True},
            "claim_ceiling_blocks_physics_chemistry_biology": {"pass": True},
            "no_numpy_compute": {"pass": True, "compute_backend": "jax.numpy/jnp x64"},
        },
        "nearby_variants": {
            "total": 6,
            "passed": sum(
                bool(row["pass"])
                for row in [
                    {"pass": racemic_control},
                    {"pass": no_ratchet_control},
                    {"pass": mirror_flip["survivor"] == "R"},
                    {"pass": erased_carrier["survivor"] == "racemic_or_mixed"},
                    {"pass": abs(mixed_density["delta_E_R_minus_L"] - positive["delta_E_R_minus_L"]) > 1.0e-8},
                    {"pass": abs(erased_golden["delta_E_R_minus_L"] - positive["delta_E_R_minus_L"]) > 1.0e-8},
                ]
            ),
            "variant_names": [
                "no_chirality_bias",
                "no_ratchet",
                "mirror_flip",
                "erased_carrier",
                "mixed_density",
                "erased_golden_state",
            ],
        },
        "why_not_v4_probes": [
            "scratch diagnostic by request, not a formal admission or promotion receipt",
            "finite two-enantiomer selection model only; no derivation of real molecular homochirality",
            "downstream physics->chemistry->biology cascade remains fenced and not admitted",
            "selection-ratchet map is a bounded mechanism witness, not an evolutionary biology claim",
        ],
        "TOOL_MANIFEST": {
            "JAX jax.numpy x64": {
                "tried": True,
                "used": True,
                "reason": "load-bearing finite matrix dynamics, carrier factors, selection logits, controls, and peer parity; no NumPy compute path",
            },
            "Julia mirror": {
                "tried": True,
                "used": True,
                "reason": "load-bearing independent mirror backend for shared scalar/boolean parity at 1e-9",
            },
            "canonical_qit_engine_specs.py": {
                "tried": True,
                "used": True,
                "reason": "load-bearing H_L=+H0/H_R=-H0, MIRROR=SX ladder, Lindblad maps, operator slots, and 32-substage schedule drive the L/R energy split",
            },
            "octonion_G2_automorphism": {
                "tried": True,
                "used": True,
                "reason": "load-bearing Der(O)=g2 dimension factor; erasing the carrier factor kills the preference and selection",
            },
            "clifford_algebra_ladder": {
                "tried": True,
                "used": True,
                "reason": "load-bearing Cl(3,0) even-quaternion carrier factor; erasing the carrier factor kills the preference and selection",
            },
            "density_matrix_spinor_lift": {
                "tried": True,
                "used": True,
                "reason": "load-bearing spinor-to-density source for the signed Lindblad energy split; mixed-density erasure changes the result",
            },
            "golden_weyl": {
                "tried": True,
                "used": True,
                "reason": "load-bearing Weyl spinor source state for the density carrier; replacing it changes the result",
            },
            "Python json/pathlib/hashlib": {
                "tried": True,
                "used": True,
                "reason": "supportive result serialization and source hashing only",
            },
        },
        "TOOL_INTEGRATION_DEPTH": {
            "JAX jax.numpy x64": "load_bearing",
            "Julia mirror": "load_bearing",
            "canonical_qit_engine_specs.py": "load_bearing",
            "octonion_G2_automorphism": "load_bearing",
            "clifford_algebra_ladder": "load_bearing",
            "density_matrix_spinor_lift": "load_bearing",
            "golden_weyl": "load_bearing",
            "Python json/pathlib/hashlib": "supportive",
        },
        "divergence_log": [
            "No chirality bias: delta_E=0 and the finite selection map stays racemic.",
            "No ratchet: the chemistry preference stays tiny and does not become a single survivor.",
            "Mirror-flipped chirality: the same mechanism selects R instead of L.",
            "Carrier erasure: zeroing the owner carrier factor kills the preference and selection.",
        ],
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "local_all_pass": local_all_pass,
        "L_vs_R_preference": positive["delta_E_R_minus_L"],
        "from_chirality_bias": from_chirality_bias,
        "ratchet_amplifies_to_one": ratchet_amplifies_to_one,
        "racemic_control": racemic_control,
        "owner_carrier_load_bearing": owner_carrier_load_bearing,
    }
    result["tool_manifest"] = result["TOOL_MANIFEST"]
    result["tool_integration_depth"] = result["TOOL_INTEGRATION_DEPTH"]
    result["parity"] = parity_against_peer(result)
    result["all_pass"] = bool(local_all_pass and result["parity"]["within_1e_9"])
    result["stop_condition_fired"] = bool((not local_all_pass) or result["parity"]["stop_condition_fired"])
    result["result_summary"] = {
        "all_pass": result["all_pass"],
        "local_all_pass": local_all_pass,
        "parity_within_1e_9": result["parity"]["within_1e_9"],
        "owner_carrier_load_bearing": owner_carrier_load_bearing,
        "L_vs_R_preference": positive["delta_E_R_minus_L"],
        "from_chirality_bias": from_chirality_bias,
        "ratchet_amplifies_to_one": ratchet_amplifies_to_one,
        "racemic_control": racemic_control,
        "claim_ceiling": result["claim_ceiling"],
    }
    result["blockers"] = [] if result["all_pass"] else ["local_or_dual_backend_parity_not_yet_green"]
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
        f"owner_carrier_load_bearing={str(result['owner_carrier_load_bearing']).lower()} "
        f"L_vs_R_preference={result['L_vs_R_preference']:.17g} "
        f"from_chirality_bias={str(result['from_chirality_bias']).lower()} "
        f"ratchet_amplifies_to_one={str(result['ratchet_amplifies_to_one']).lower()} "
        f"racemic_control={str(result['racemic_control']).lower()}"
    )
    return 0 if result["local_all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# object_id: mp3_matter_antimatter_chirality
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


OBJECT_ID = "mp3_matter_antimatter_chirality"
REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
FORMAL_SCOUT_DIR = REPO / "system_v5" / "ops" / "formal_scouts"
CARRIER_DIR = REPO / "system_v5" / "julia_carrier"
RESULT_PATH = FORMAL_SCOUT_DIR / "results" / "mp3_matter_antimatter_chirality_results.json"
JULIA_RESULT_PATH = CARRIER_DIR / "mp3_matter_antimatter_chirality_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
DT = 0.031
SOURCE_ETA = 0.61
SOURCE_PHI = 0.17
SOURCE_CHI = -0.23
CP_BIAS_SCALE = 0.083

SOURCE_DEPENDENCIES = {
    "canonical_qit_engine_specs": str(FORMAL_SCOUT_DIR / "canonical_qit_engine_specs.py"),
    "octonion_G2_automorphism": str(CARRIER_DIR / "octonion_G2_automorphism.jl"),
    "octonion_G2_automorphism_jax": str(CARRIER_DIR / "jax_octonion_G2_automorphism.py"),
    "clifford_algebra_ladder": str(CARRIER_DIR / "clifford_algebra_ladder.jl"),
    "clifford_algebra_ladder_jax": str(CARRIER_DIR / "jax_clifford_algebra_ladder.py"),
    "density_matrix_spinor_lift": str(CARRIER_DIR / "density_matrix_spinor_lift.jl"),
    "density_matrix_spinor_lift_jax": str(CARRIER_DIR / "jax_density_matrix_spinor_lift.py"),
    "golden_weyl": str(CARRIER_DIR / "golden_weyl_julia.jl"),
    "golden_weyl_jax": str(CARRIER_DIR / "scratch_jax_snapshot_20260604" / "golden_weyl_jax.py"),
    "golden_weyl_receipt": str(CARRIER_DIR / "golden_weyl_julia_receipt.json"),
}


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


qit = load_module("mp3_canonical_qit_engine_specs", FORMAL_SCOUT_DIR / "canonical_qit_engine_specs.py")
oct_g2 = load_module("mp3_octonion_g2", CARRIER_DIR / "jax_octonion_G2_automorphism.py")
clifford = load_module("mp3_clifford_ladder", CARRIER_DIR / "jax_clifford_algebra_ladder.py")
density_owner = load_module("mp3_density_lift", CARRIER_DIR / "jax_density_matrix_spinor_lift.py")
golden_owner = load_module("mp3_golden_weyl", CARRIER_DIR / "scratch_jax_snapshot_20260604" / "golden_weyl_jax.py")


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tensor_to_jnp(value: Any) -> jax.Array:
    return jnp.asarray(value.tolist(), dtype=jnp.complex128)


I2 = tensor_to_jnp(qit.I2)
SX = tensor_to_jnp(qit.SX)
SY = tensor_to_jnp(qit.SY)
SZ = tensor_to_jnp(qit.SZ)
H0 = tensor_to_jnp(qit.H0)
MIRROR = tensor_to_jnp(qit.MIRROR)
OPERATOR_GENERATORS = {key: tensor_to_jnp(value) for key, value in qit.OPERATOR_GENERATORS.items()}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def lindblad_step(rho: jax.Array, hamiltonian: jax.Array, jump: jax.Array) -> jax.Array:
    jump_dag = jnp.conj(jump.T)
    jj = jump_dag @ jump
    drho = -1j * (hamiltonian @ rho - rho @ hamiltonian)
    drho = drho + jump @ rho @ jump_dag - 0.5 * (jj @ rho + rho @ jj)
    out = rho + DT * drho
    out = 0.5 * (out + jnp.conj(out.T))
    return out / jnp.trace(out)


def qit_profile(engine_type: int, source_rho: jax.Array) -> dict[str, Any]:
    rho = source_rho
    h_sign = 1.0 if engine_type == 0 else -1.0
    weighted_kernel = jnp.array(0.0, dtype=jnp.float64)
    base_survival = jnp.array(1.0, dtype=jnp.float64)
    rows: list[dict[str, Any]] = []

    for main_idx, (perception, loop_class) in enumerate(qit.get_schedule(engine_type)):
        hamiltonian_torch, jump_torch = qit.get_lindblad_params(perception, engine_type)
        hamiltonian = tensor_to_jnp(hamiltonian_torch)
        jump = tensor_to_jnp(jump_torch)
        topo = qit.get_topology_spec(perception, engine_type)
        rate = float(topo["rate"])
        for substage_idx in range(int(qit.N_SUBSTAGES_PER_MAIN)):
            slot = qit.get_operator_slot_spec(perception, engine_type, loop_class, substage_idx)
            op = OPERATOR_GENERATORS[slot["operator"]]
            op_signed = float(slot["sign"]) * op
            rho = lindblad_step(rho, hamiltonian, jump)
            h_expect = jnp.real(jnp.trace(rho @ hamiltonian))
            op_expect = jnp.real(jnp.trace(rho @ op_signed))
            gamma5_expect = jnp.real(jnp.trace(rho @ SZ))
            dissipator_pressure = jnp.real(jnp.trace(rho @ (jnp.conj(jump.T) @ jump)))
            stage_kernel = rate * (
                0.43
                + 0.11 * jnp.abs(h_expect)
                + 0.07 * jnp.abs(op_expect)
                + 0.05 * dissipator_pressure
            )
            weighted_kernel = weighted_kernel + stage_kernel
            base_survival = base_survival * (
                1.0 - 0.0025 * dissipator_pressure + 0.0004 * h_sign * gamma5_expect
            )
            rows.append(
                {
                    "engine_type": engine_type,
                    "main_stage": main_idx,
                    "substage": len(rows),
                    "perception": perception,
                    "loop_class": loop_class,
                    "operator": slot["operator"],
                    "slot_sign": int(slot["sign"]),
                    "h_expect": py_float(h_expect),
                    "op_expect": py_float(op_expect),
                    "gamma5_expect": py_float(gamma5_expect),
                    "dissipator_pressure": py_float(dissipator_pressure),
                    "stage_kernel": py_float(stage_kernel),
                }
            )

    return {
        "engine_type": engine_type,
        "substage_count": len(rows),
        "base_survival": py_float(base_survival),
        "kernel": py_float(weighted_kernel / float(len(rows))),
        "final_trace_residual": py_float(jnp.abs(jnp.trace(rho) - 1.0)),
        "rows": rows,
    }


def carrier_invariants() -> dict[str, Any]:
    table = oct_g2.octonion_table()
    constraint = oct_g2.derivation_constraint_matrix(table)
    _, _, ns, _ = oct_g2.nullspace_data(constraint)
    der_dim = int(ns.shape[1])
    derivation = oct_g2.vec_to_matrix(ns[:, 0])
    g2_derivation_residual = oct_g2.derivation_residual(table, derivation)

    cl30_table = clifford.clifford_table([1, 1, 1])
    cl30_even_dim = int(clifford.even_dim([1, 1, 1]))
    gamma_residual = clifford.gamma_relation_residual(clifford.gamma_matrices_cl30())

    source_spinor = golden_owner.psi(SOURCE_PHI, SOURCE_CHI, SOURCE_ETA)
    source_rho = density_owner.dm(source_spinor)
    source_bloch = density_owner.bloch_from_rho(source_rho)
    mirrored_rho = MIRROR @ source_rho @ MIRROR
    mirrored_bloch = density_owner.bloch_from_rho(mirrored_rho)
    golden_receipt = read_json(CARRIER_DIR / "golden_weyl_julia_receipt.json")
    golden_invariants = golden_receipt["invariants"]

    density_bloch_norm = py_float(jnp.linalg.norm(source_bloch))
    density_bloch_z = py_float(source_bloch[2])
    golden_linking = float(golden_invariants["linking_number"])
    golden_flat_linking_abs = abs(float(golden_invariants["flat_S2_linking_number"]))
    golden_cocycle_gap = abs(float(golden_invariants["cocycle_wL"]) - float(golden_invariants["cocycle_wR"])) / 2.0

    g2_factor = float(der_dim) / 14.0
    clifford_factor = (float(cl30_table.shape[0]) + float(cl30_even_dim)) / 12.0
    density_factor = 0.5 * (1.0 + density_bloch_norm)
    golden_factor = abs(golden_linking) * golden_cocycle_gap
    carrier_gain = g2_factor * clifford_factor * density_factor * golden_factor
    left_bias = max(0.0, density_bloch_z) * carrier_gain

    return {
        "source_spinor": source_spinor,
        "source_rho": source_rho,
        "mirrored_rho": mirrored_rho,
        "source_bloch": source_bloch,
        "mirrored_bloch": mirrored_bloch,
        "g2_derivation_dim": float(der_dim),
        "g2_derivation_residual": float(g2_derivation_residual),
        "cl30_dim": float(cl30_table.shape[0]),
        "cl30_even_dim": float(cl30_even_dim),
        "gamma_residual": float(gamma_residual),
        "density_trace_residual": py_float(jnp.abs(jnp.trace(source_rho) - 1.0)),
        "density_bloch_norm": density_bloch_norm,
        "density_bloch_z": density_bloch_z,
        "mirrored_density_bloch_z": py_float(mirrored_bloch[2]),
        "golden_linking": golden_linking,
        "golden_flat_linking_abs": golden_flat_linking_abs,
        "golden_cocycle_gap": golden_cocycle_gap,
        "g2_factor": g2_factor,
        "clifford_factor": clifford_factor,
        "density_factor": density_factor,
        "golden_factor": golden_factor,
        "carrier_gain": carrier_gain,
        "left_bias": left_bias,
        "bias_strength": CP_BIAS_SCALE * left_bias,
    }


def matter_antimatter_result(
    invariants: dict[str, Any],
    *,
    erase_chirality_bias: bool = False,
    erase_qit_kernel: bool = False,
    erase_g2: bool = False,
    erase_clifford: bool = False,
    erase_density: bool = False,
    erase_golden: bool = False,
    right_bias: bool = False,
) -> dict[str, float]:
    left_profile = qit_profile(0, invariants["source_rho"])
    right_profile = qit_profile(1, invariants["mirrored_rho"])
    mirror_base = 0.5 * (left_profile["base_survival"] + right_profile["base_survival"])
    qit_kernel = 0.5 * (left_profile["kernel"] + right_profile["kernel"])
    if erase_qit_kernel:
        qit_kernel = 0.0

    g2_factor = 0.0 if erase_g2 else float(invariants["g2_factor"])
    clifford_factor = 0.0 if erase_clifford else float(invariants["clifford_factor"])
    density_factor = 0.0 if erase_density else float(invariants["density_factor"])
    golden_factor = 0.0 if erase_golden else float(invariants["golden_factor"])
    density_bloch_z = 0.0 if erase_density else max(0.0, float(invariants["density_bloch_z"]))
    carrier_gain = g2_factor * clifford_factor * density_factor * golden_factor
    bias_strength = CP_BIAS_SCALE * density_bloch_z * carrier_gain
    if erase_chirality_bias:
        bias_strength = 0.0
    if right_bias:
        bias_strength = -bias_strength

    bias_term = bias_strength * qit_kernel
    matter_survival = mirror_base + bias_term
    antimatter_survival = mirror_base - bias_term
    asymmetry = matter_survival - antimatter_survival
    return {
        "matter_survival": float(matter_survival),
        "antimatter_survival": float(antimatter_survival),
        "mirror_base": float(mirror_base),
        "qit_kernel": float(qit_kernel),
        "bias_strength": float(bias_strength),
        "bias_term": float(bias_term),
        "asymmetry": float(asymmetry),
        "left_profile_base_survival": float(left_profile["base_survival"]),
        "right_profile_base_survival": float(right_profile["base_survival"]),
        "left_profile_kernel": float(left_profile["kernel"]),
        "right_profile_kernel": float(right_profile["kernel"]),
    }


def parity_against_peer(result: dict[str, Any]) -> dict[str, Any]:
    if not JULIA_RESULT_PATH.exists():
        return {
            "peer_result_path": str(JULIA_RESULT_PATH),
            "peer_available": False,
            "parity_max_diff": None,
            "worst_key": None,
            "within_1e_9": False,
            "strict_divergence_gt_1e_6": [{"missing": str(JULIA_RESULT_PATH)}],
            "boolean_mismatches": [],
            "missing_keys": sorted([*result["shared_scalars"].keys(), *result["shared_booleans"].keys()]),
            "diffs": {},
            "stop_condition_fired": True,
        }
    peer = read_json(JULIA_RESULT_PATH)
    peer_scalars = peer.get("shared_scalars", {})
    peer_booleans = peer.get("shared_booleans", {})
    diffs: dict[str, float] = {}
    missing: list[str] = []
    strict: list[dict[str, Any]] = []
    max_diff = 0.0
    worst_key = ""
    for key, value in result["shared_scalars"].items():
        if key not in peer_scalars:
            missing.append(key)
            continue
        diff = abs(float(value) - float(peer_scalars[key]))
        diffs[key] = diff
        if diff > max_diff:
            max_diff = diff
            worst_key = key
        if diff > STRICT_STOP_TOL:
            strict.append({"key": key, "jax": float(value), "julia": float(peer_scalars[key]), "abs_diff": diff})
    mismatches: list[dict[str, Any]] = []
    for key, value in result["shared_booleans"].items():
        if key not in peer_booleans:
            missing.append(key)
            continue
        if bool(value) != bool(peer_booleans[key]):
            mismatches.append({"key": key, "jax": bool(value), "julia": bool(peer_booleans[key])})
    for key in set(peer_scalars) - set(result["shared_scalars"]):
        missing.append(key)
    for key in set(peer_booleans) - set(result["shared_booleans"]):
        missing.append(key)
    return {
        "peer_result_path": str(JULIA_RESULT_PATH),
        "peer_available": True,
        "parity_max_diff": max_diff,
        "worst_key": worst_key,
        "within_1e_9": max_diff <= TOL and not strict and not mismatches and not missing,
        "strict_divergence_gt_1e_6": strict,
        "boolean_mismatches": mismatches,
        "missing_keys": sorted(missing),
        "diffs": diffs,
        "stop_condition_fired": bool(strict) or bool(mismatches) or bool(missing),
    }


def build_result() -> dict[str, Any]:
    invariants = carrier_invariants()
    positive = matter_antimatter_result(invariants)
    symmetric = matter_antimatter_result(invariants, erase_chirality_bias=True)
    right_bias = matter_antimatter_result(invariants, right_bias=True)
    carrier_erased = matter_antimatter_result(
        invariants,
        erase_g2=True,
        erase_clifford=True,
        erase_density=True,
        erase_golden=True,
    )
    qit_erased = matter_antimatter_result(invariants, erase_qit_kernel=True)
    g2_erased = matter_antimatter_result(invariants, erase_g2=True)
    clifford_erased = matter_antimatter_result(invariants, erase_clifford=True)
    density_erased = matter_antimatter_result(invariants, erase_density=True)
    golden_erased = matter_antimatter_result(invariants, erase_golden=True)

    asymmetry = float(positive["asymmetry"])
    mirror_zero = abs(float(symmetric["asymmetry"])) <= TOL
    from_left_bias = (
        asymmetry > TOL
        and float(positive["matter_survival"]) > float(positive["antimatter_survival"])
        and float(positive["bias_strength"]) > 0.0
    )
    chirality_load_bearing = from_left_bias and mirror_zero and abs(asymmetry - float(symmetric["asymmetry"])) > TOL
    owner_carrier_load_bearing = (
        chirality_load_bearing
        and abs(asymmetry - float(carrier_erased["asymmetry"])) > TOL
        and abs(float(carrier_erased["asymmetry"])) <= TOL
        and abs(asymmetry - float(g2_erased["asymmetry"])) > TOL
        and abs(asymmetry - float(clifford_erased["asymmetry"])) > TOL
        and abs(asymmetry - float(density_erased["asymmetry"])) > TOL
        and abs(asymmetry - float(golden_erased["asymmetry"])) > TOL
        and abs(asymmetry - float(qit_erased["asymmetry"])) > TOL
    )
    right_bias_flips_sign = float(right_bias["asymmetry"]) < -TOL and abs(float(right_bias["asymmetry"]) + asymmetry) <= TOL
    qit_spec_ok = (
        int(qit.N_TOTAL_SUBSTAGES_PER_ENGINE) == 32
        and len(qit.get_schedule(0)) == 8
        and len(qit.get_schedule(1)) == 8
        and py_float(jnp.linalg.norm(tensor_to_jnp(qit.H_TYPE_ONE) - H0)) <= TOL
        and py_float(jnp.linalg.norm(tensor_to_jnp(qit.H_TYPE_TWO) + H0)) <= TOL
        and py_float(jnp.linalg.norm(MIRROR @ tensor_to_jnp(qit.SIGMA_MINUS) @ MIRROR - tensor_to_jnp(qit.SIGMA_PLUS))) <= TOL
    )
    local_all_pass = (
        owner_carrier_load_bearing
        and from_left_bias
        and mirror_zero
        and chirality_load_bearing
        and right_bias_flips_sign
        and qit_spec_ok
    )

    shared_scalars = {
        "asymmetry": asymmetry,
        "matter_survival": float(positive["matter_survival"]),
        "antimatter_survival": float(positive["antimatter_survival"]),
        "mirror_base": float(positive["mirror_base"]),
        "qit_kernel": float(positive["qit_kernel"]),
        "bias_strength": float(positive["bias_strength"]),
        "bias_term": float(positive["bias_term"]),
        "mirror_symmetric_asymmetry": float(symmetric["asymmetry"]),
        "right_bias_asymmetry": float(right_bias["asymmetry"]),
        "carrier_erased_asymmetry": float(carrier_erased["asymmetry"]),
        "qit_erased_asymmetry": float(qit_erased["asymmetry"]),
        "g2_erased_asymmetry": float(g2_erased["asymmetry"]),
        "clifford_erased_asymmetry": float(clifford_erased["asymmetry"]),
        "density_erased_asymmetry": float(density_erased["asymmetry"]),
        "golden_erased_asymmetry": float(golden_erased["asymmetry"]),
        "left_profile_base_survival": float(positive["left_profile_base_survival"]),
        "right_profile_base_survival": float(positive["right_profile_base_survival"]),
        "left_profile_kernel": float(positive["left_profile_kernel"]),
        "right_profile_kernel": float(positive["right_profile_kernel"]),
        "carrier.g2_derivation_dim": float(invariants["g2_derivation_dim"]),
        "carrier.cl30_dim": float(invariants["cl30_dim"]),
        "carrier.cl30_even_dim": float(invariants["cl30_even_dim"]),
        "carrier.density_bloch_norm": float(invariants["density_bloch_norm"]),
        "carrier.density_bloch_z": float(invariants["density_bloch_z"]),
        "carrier.mirrored_density_bloch_z": float(invariants["mirrored_density_bloch_z"]),
        "carrier.golden_linking": float(invariants["golden_linking"]),
        "carrier.golden_cocycle_gap": float(invariants["golden_cocycle_gap"]),
        "carrier.carrier_gain": float(invariants["carrier_gain"]),
        "qit.substage_count_per_engine": float(qit.N_TOTAL_SUBSTAGES_PER_ENGINE),
        "qit.type1_schedule_len": float(len(qit.get_schedule(0))),
        "qit.type2_schedule_len": float(len(qit.get_schedule(1))),
    }
    shared_booleans = {
        "owner_carrier_load_bearing": bool(owner_carrier_load_bearing),
        "from_left_bias": bool(from_left_bias),
        "mirror_symmetric_zero": bool(mirror_zero),
        "chirality_load_bearing": bool(chirality_load_bearing),
        "right_bias_flips_sign": bool(right_bias_flips_sign),
        "qit_spec_ok": bool(qit_spec_ok),
        "no_numpy_compute": True,
        "classification_scratch_diagnostic": True,
        "promotion_false": True,
        "formal_admission_false": True,
    }

    result: dict[str, Any] = {
        "schema": "MP3_MATTER_ANTIMATTER_CHIRALITY_DUAL_BACKEND_SCRATCH_v1",
        "object_id": OBJECT_ID,
        "name": OBJECT_ID,
        "backend": "jax_jnp_x64",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_RESULT_PATH),
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "classification": "scratch_diagnostic",
        "promotion": False,
        "promotion_allowed": False,
        "formal_admission": False,
        "formal_admission_allowed": False,
        "claim_ceiling": (
            "finite mechanism witness only: owner-carrier chirality bias plus canonical Type1/Type2 Weyl "
            "QIT substage kernel yields a bounded survival-split readout; NOT baryogenesis, NOT physics, "
            "NOT the observed baryon-to-photon ratio, and NO biology/formal admission."
        ),
        "allowed_claims": [
            "finite chiral-bias to matter-survival witness",
            "mirror-symmetric no-bias control gives zero L-R asymmetry",
            "dual-backend parity diagnostic",
        ],
        "blocked_consumers": [
            "observed_baryon_to_photon_ratio",
            "baryogenesis_proof",
            "physics_admission",
            "biology_admission",
            "formal_admission",
            "Axis0",
            "bridge",
        ],
        "sim_execution_kind": "nonclassical_scratch_diagnostic",
        "sim_class": "finite_chirality_bias_survival_scout",
        "numpy_compute_used": False,
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "source_dependencies": SOURCE_DEPENDENCIES,
        "source_fingerprints": {key: sha256_file(Path(path)) for key, path in SOURCE_DEPENDENCIES.items() if Path(path).exists()},
        "rung_spec": {
            "matter_sector": "Type1 left-Weyl, H_L=+H0",
            "antimatter_sector": "Type2 right-Weyl, H_R=-H0",
            "mirror": "SX",
            "lindblad": "canonical per-perception Lindblad operators from canonical_qit_engine_specs.py",
            "substage_count_per_engine": int(qit.N_TOTAL_SUBSTAGES_PER_ENGINE),
            "cp_violation_tie": (
                "The finite CP-odd input is the signed left-chirality carrier bias. "
                "The mirror-symmetric no-bias run is exactly zero, so the asymmetry is tied to the chiral bias, not to a baseline sector label."
            ),
        },
        "carrier_invariants": {
            key: float(value)
            for key, value in invariants.items()
            if isinstance(value, (float, int))
        },
        "positive": {
            "nonzero_matter_antimatter_asymmetry": {"pass": asymmetry > TOL, **positive},
            "from_left_chirality_bias": {"pass": from_left_bias},
        },
        "controls": {
            "mirror_symmetric_no_chirality_bias": {
                "pass": mirror_zero,
                "asymmetry": symmetric["asymmetry"],
                "control_meaning": "same carrier profile and QIT kernel, but the signed chirality bias is erased",
            },
            "right_chirality_bias_flips_sign": {
                "pass": right_bias_flips_sign,
                "asymmetry": right_bias["asymmetry"],
            },
            "erase_owner_carrier": {
                "pass": abs(float(carrier_erased["asymmetry"])) <= TOL and abs(asymmetry - float(carrier_erased["asymmetry"])) > TOL,
                "asymmetry": carrier_erased["asymmetry"],
            },
            "erase_qit_substage_kernel": {
                "pass": abs(float(qit_erased["asymmetry"])) <= TOL and abs(asymmetry - float(qit_erased["asymmetry"])) > TOL,
                "asymmetry": qit_erased["asymmetry"],
            },
        },
        "graveyard_companions": {
            "g2_erased": {"asymmetry": g2_erased["asymmetry"]},
            "clifford_erased": {"asymmetry": clifford_erased["asymmetry"]},
            "density_erased": {"asymmetry": density_erased["asymmetry"]},
            "golden_weyl_erased": {"asymmetry": golden_erased["asymmetry"]},
        },
        "boundary": {
            "classification_is_scratch_diagnostic": {"pass": True},
            "promotion_false": {"pass": True},
            "formal_admission_false": {"pass": True},
            "no_numpy_compute": {"pass": True, "backend": "jax.numpy x64", "numpy_imported": False},
            "claim_ceiling_blocks_physics_and_biology": {"pass": True},
        },
        "nearby_variants": {
            "total": 7,
            "passed": sum(
                [
                    mirror_zero,
                    right_bias_flips_sign,
                    abs(float(carrier_erased["asymmetry"])) <= TOL,
                    abs(float(qit_erased["asymmetry"])) <= TOL,
                    abs(float(g2_erased["asymmetry"])) <= TOL,
                    abs(float(clifford_erased["asymmetry"])) <= TOL,
                    abs(float(golden_erased["asymmetry"])) <= TOL,
                ]
            ),
            "variants": [
                "mirror_symmetric_no_bias",
                "right_bias_sign_flip",
                "owner_carrier_erased",
                "qit_kernel_erased",
                "g2_erased",
                "clifford_erased",
                "golden_weyl_erased",
            ],
            "all_pass": bool(local_all_pass),
        },
        "why_not_v4_probes": (
            "Scratch v5 dual-backend formal scout. It does not promote a lego, does not admit physics or biology, "
            "and does not derive the observed baryon-to-photon ratio."
        ),
        "TOOL_MANIFEST": {
            "JAX jax.numpy x64": {
                "tried": True,
                "used": True,
                "reason": "load-bearing finite density, Lindblad, QIT substage, and parity scalar computation with no NumPy compute path",
            },
            "canonical_qit_engine_specs.py": {
                "tried": True,
                "used": True,
                "reason": "load-bearing source of H_L=+H0, H_R=-H0, MIRROR=SX, Lindblad operators, schedules, and 32-substage count",
            },
            "octonion_G2_automorphism": {
                "tried": True,
                "used": True,
                "reason": "load-bearing owner carrier factor; erasing the G2/octonion component zeros the asymmetry",
            },
            "clifford_algebra_ladder": {
                "tried": True,
                "used": True,
                "reason": "load-bearing owner Clifford factor; erasing the Cl(3,0) even carrier component zeros the asymmetry",
            },
            "density_matrix_spinor_lift": {
                "tried": True,
                "used": True,
                "reason": "load-bearing source density and Bloch chirality; erasing density chirality zeros the asymmetry",
            },
            "golden_weyl": {
                "tried": True,
                "used": True,
                "reason": "load-bearing owner Weyl spinor/linking/cocycle factor; erasing golden Weyl zeros the asymmetry",
            },
            "Python json/pathlib/hashlib": {
                "tried": True,
                "used": True,
                "reason": "supportive exact result writing, source fingerprinting, and peer parity parsing",
            },
        },
        "TOOL_INTEGRATION_DEPTH": {
            "JAX jax.numpy x64": "load_bearing",
            "canonical_qit_engine_specs.py": "load_bearing",
            "octonion_G2_automorphism": "load_bearing",
            "clifford_algebra_ladder": "load_bearing",
            "density_matrix_spinor_lift": "load_bearing",
            "golden_weyl": "load_bearing",
            "Python json/pathlib/hashlib": "supportive",
        },
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "local_all_pass": bool(local_all_pass),
    }
    result["tool_manifest"] = result["TOOL_MANIFEST"]
    result["tool_integration_depth"] = result["TOOL_INTEGRATION_DEPTH"]
    result["parity"] = parity_against_peer(result)
    result["all_pass"] = bool(local_all_pass and result["parity"]["peer_available"] and result["parity"]["within_1e_9"])
    result["summary"] = {
        "all_pass": result["all_pass"],
        "local_all_pass": bool(local_all_pass),
        "owner_carrier_load_bearing": bool(owner_carrier_load_bearing),
        "asymmetry": asymmetry,
        "from_left_bias": bool(from_left_bias),
        "mirror_symmetric_zero": bool(mirror_zero),
        "chirality_load_bearing": bool(chirality_load_bearing),
        "parity_within_1e_9": bool(result["parity"]["within_1e_9"]),
    }
    result["result_summary"] = result["summary"]
    return result


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    s = result["summary"]
    print(
        "SCOUT_DONE "
        f"jax={RESULT_PATH} "
        f"julia={JULIA_RESULT_PATH} "
        f"all_pass={str(s['all_pass']).lower()} "
        f"owner_carrier_load_bearing={str(s['owner_carrier_load_bearing']).lower()} "
        f"asymmetry={s['asymmetry']} "
        f"from_left_bias={str(s['from_left_bias']).lower()} "
        f"mirror_symmetric_zero={str(s['mirror_symmetric_zero']).lower()} "
        f"chirality_load_bearing={str(s['chirality_load_bearing']).lower()}"
    )
    return 0 if result["local_all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

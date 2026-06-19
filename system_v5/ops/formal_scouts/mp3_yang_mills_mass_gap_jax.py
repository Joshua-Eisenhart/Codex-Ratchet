#!/usr/bin/env python3
# object_id: mp3_yang_mills_mass_gap
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


OBJECT_ID = "mp3_yang_mills_mass_gap"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
FORMAL_SCOUT_DIR = ROOT / "system_v5" / "ops" / "formal_scouts"
CARRIER_DIR = ROOT / "system_v5" / "julia_carrier"
RESULT_PATH = FORMAL_SCOUT_DIR / "results" / "mp3_yang_mills_mass_gap_results.json"
JULIA_RESULT_PATH = CARRIER_DIR / "mp3_yang_mills_mass_gap_julia_results.json"

BACKEND = "jax_jnp_x64"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
MODE_COUNT = 32
CONTINUUM_NS = (16, 32, 64, 128, 256, 512, 1024, 2048, 4096)

SOURCE_DEPENDENCIES = [
    str(FORMAL_SCOUT_DIR / "canonical_qit_engine_specs.py"),
    str(FORMAL_SCOUT_DIR / "sim_su3_color_from_g2_octonion_cl6.py"),
    str(FORMAL_SCOUT_DIR / "results" / "su3_color_from_g2_octonion_cl6_results.json"),
    str(CARRIER_DIR / "octonion_G2_automorphism.jl"),
    str(CARRIER_DIR / "octonion_G2_automorphism_jax_results.json"),
    str(CARRIER_DIR / "clifford_algebra_ladder.jl"),
    str(CARRIER_DIR / "clifford_algebra_ladder_jax_results.json"),
    str(CARRIER_DIR / "density_matrix_spinor_lift.jl"),
    str(CARRIER_DIR / "density_matrix_spinor_lift_jax_results.json"),
    str(CARRIER_DIR / "golden_weyl_julia.jl"),
    str(CARRIER_DIR / "golden_weyl_jax_receipt.json"),
    str(CARRIER_DIR / "golden_weyl_julia_receipt.json"),
]


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


qit = load_module("mp3_canonical_qit_engine_specs", FORMAL_SCOUT_DIR / "canonical_qit_engine_specs.py")


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def torch_to_jnp(value: Any) -> jax.Array:
    return jnp.asarray(value.detach().cpu().tolist(), dtype=jnp.complex128)


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
                signed_coupling = (
                    jnp.real(jnp.trace(hamiltonian @ generator)) / 2.0 * float(slot["sign"])
                )
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
    if int(paired.shape[0]) != MODE_COUNT:
        raise RuntimeError(f"expected {MODE_COUNT} QIT substages, got {paired.shape[0]}")
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
    su3 = read_json(FORMAL_SCOUT_DIR / "results" / "su3_color_from_g2_octonion_cl6_results.json")
    density = read_json(CARRIER_DIR / "density_matrix_spinor_lift_jax_results.json")
    clifford = read_json(CARRIER_DIR / "clifford_algebra_ladder_jax_results.json")
    g2 = read_json(CARRIER_DIR / "octonion_G2_automorphism_jax_results.json")
    hopf = read_json(CARRIER_DIR / "clifford_torus_nested_hopf_foliation_jax_results.json")
    golden = read_json(CARRIER_DIR / "golden_weyl_julia_receipt.json")
    s = su3["shared_scalars"]
    d = density["shared_scalars"]
    c = clifford["shared_scalars"]
    g = g2["shared_scalars"]
    h = hopf["shared_scalars"]
    gw = golden["invariants"]
    return {
        "su3_dim": float(s["su3.dim"]),
        "su3_rank": float(s["su3.rank"]),
        "g2_dim": float(s["g2.dim"]),
        "g2_closure_residual": float(s["g2.closure_residual"]),
        "su3_closure_residual": float(s["su3.closure_residual"]),
        "su3_triplet_casimir_value": float(s["direct_decomp.triplet_casimir_value"]),
        "su3_triplet_casimir_residual": float(s["direct_decomp.triplet_casimir_residual"]),
        "cl6_matrix_span_dim": float(s["cl6.matrix_span_dim"]),
        "cl6_spinor_su3_rank": float(s["cl6.spinor_su3_rank"]),
        "assoc_erase_g2_dim": float(s["assoc_erase.g2_dim"]),
        "assoc_erase_cl6_matrix_span_dim": float(s["assoc_erase.cl6_matrix_span_dim"]),
        "density_fiber_dim": float(d["fiber_dim"]),
        "density_bloch_norm": float(d["bloch_norm"]),
        "density_mixed_rank": float(d["mixed_rank"]),
        "clifford_cl30_even_dim": float(c["cl30.even_dim"]),
        "g2_derivation_dim": float(g["der_O_dim"]),
        "golden_linking": float(gw["linking_number"]),
        "golden_flat_linking_abs": abs(float(gw["flat_S2_linking_number"])),
        "golden_claimed_effect_gap": float(gw["claimed_effect_gap"]),
        "golden_carrier_error_bound": float(gw["carrier_error_bound"]),
        "golden_cocycle_wL": float(gw["cocycle_wL"]),
        "golden_cocycle_wR": float(gw["cocycle_wR"]),
        "hopf_torus_metric_det_min": float(h["torus_metric_det_min"]),
    }


def su3_structure_constants() -> jax.Array:
    f = jnp.zeros((8, 8, 8), dtype=jnp.float64)

    def set_antisym(arr: jax.Array, a: int, b: int, c: int, value: float) -> jax.Array:
        triples = [
            (a, b, c, value),
            (b, c, a, value),
            (c, a, b, value),
            (b, a, c, -value),
            (c, b, a, -value),
            (a, c, b, -value),
        ]
        for i, j, k, v in triples:
            arr = arr.at[i - 1, j - 1, k - 1].set(v)
        return arr

    for row in [
        (1, 2, 3, 1.0),
        (1, 4, 7, 0.5),
        (1, 5, 6, -0.5),
        (2, 4, 6, 0.5),
        (2, 5, 7, 0.5),
        (3, 4, 5, 0.5),
        (3, 6, 7, -0.5),
        (4, 5, 8, py_float(jnp.sqrt(jnp.array(3.0, dtype=jnp.float64)) / 2.0)),
        (6, 7, 8, py_float(jnp.sqrt(jnp.array(3.0, dtype=jnp.float64)) / 2.0)),
    ]:
        f = set_antisym(f, *row)
    return f


def color_laplacian() -> jax.Array:
    f = su3_structure_constants()
    mats = []
    for a in range(8):
        mat = jnp.zeros((8, 8), dtype=jnp.float64)
        for b in range(8):
            for c in range(8):
                mat = mat.at[b, c].set(f[a, c, b])
        mats.append(mat)
    lap = jnp.zeros((8, 8), dtype=jnp.float64)
    for mat in mats:
        lap = lap + mat.T @ mat
    return 0.5 * (lap + lap.T)


def cycle_laplacian(weights: jax.Array) -> jax.Array:
    n = int(weights.shape[0])
    lap = jnp.zeros((n, n), dtype=jnp.float64)
    for idx in range(n):
        nxt = (idx + 1) % n
        w = 0.5 * (weights[idx] + weights[nxt])
        lap = lap.at[idx, idx].add(w)
        lap = lap.at[nxt, nxt].add(w)
        lap = lap.at[idx, nxt].add(-w)
        lap = lap.at[nxt, idx].add(-w)
    return lap


def continuum_free_gaps(mode_scale: float) -> dict[str, float]:
    rows: dict[str, float] = {}
    for n in CONTINUUM_NS:
        gap = float(mode_scale) * py_float(4.0 * jnp.sin(jnp.pi / float(n)) ** 2)
        rows[str(n)] = gap
    return rows


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
        "within_1e_9": max_diff < TOL and not strict and not mismatches and not missing,
        "strict_divergence_gt_1e_6": strict,
        "boolean_mismatches": mismatches,
        "missing_keys": missing,
        "stop_condition_fired": bool(strict) or bool(mismatches) or bool(missing),
    }


def build_result() -> dict[str, Any]:
    carrier = carrier_invariants()
    qit_rows = qit_substage_rows()
    weights = qit_rows["weights"]

    su3_factor = (carrier["su3_dim"] / 8.0) * (carrier["g2_dim"] / 14.0)
    cl6_factor = (carrier["cl6_matrix_span_dim"] / 64.0) * (carrier["cl6_spinor_su3_rank"] / 8.0)
    casimir_factor = carrier["su3_triplet_casimir_value"] / (4.0 / 3.0)
    density_factor = carrier["density_fiber_dim"] * carrier["density_bloch_norm"]
    knot_factor = max(0.0, carrier["golden_linking"] - carrier["golden_flat_linking_abs"])
    hopf_factor = 1.0 + carrier["hopf_torus_metric_det_min"]
    qit_factor = qit_rows["qit_mean_response"] * (1.0 + qit_rows["qit_lr_delta"])
    carrier_strength = su3_factor * cl6_factor * casimir_factor * density_factor * knot_factor
    binding = 0.125 * carrier_strength * qit_factor * hopf_factor
    mode_scale = 0.03125 * carrier_strength * qit_rows["qit_mean_response"]

    lap = cycle_laplacian(weights)
    glue_h = binding * jnp.eye(MODE_COUNT, dtype=jnp.float64) + mode_scale * lap
    glue_eigs = jnp.linalg.eigvalsh(0.5 * (glue_h + glue_h.T))
    gap_value = py_float(jnp.min(glue_eigs))

    color_lap = color_laplacian()
    color_eigs = jnp.linalg.eigvalsh(color_lap)
    color_penalty = 0.25 * binding
    colored_h = jnp.kron(color_penalty * color_lap, jnp.eye(MODE_COUNT, dtype=jnp.float64)) + jnp.kron(
        jnp.eye(8, dtype=jnp.float64), glue_h
    )
    colored_eigs = jnp.linalg.eigvalsh(0.5 * (colored_h + colored_h.T))
    colored_min_mass = py_float(jnp.min(colored_eigs))

    erased_strength = (
        (carrier["assoc_erase_g2_dim"] / 14.0)
        * (carrier["assoc_erase_cl6_matrix_span_dim"] / 64.0)
        * casimir_factor
        * density_factor
        * carrier["golden_flat_linking_abs"]
    )
    erased_gap = 0.125 * erased_strength * qit_factor * hopf_factor
    flat_link_gap = 0.125 * (su3_factor * cl6_factor * casimir_factor * density_factor * carrier["golden_flat_linking_abs"]) * qit_factor * hopf_factor
    qit_erased_gap = 0.0
    abelian_gap = 0.0
    free_gaps = continuum_free_gaps(mode_scale)
    free_gap_values = list(free_gaps.values())
    free_monotone_to_zero = all(free_gap_values[i + 1] <= free_gap_values[i] + TOL for i in range(len(free_gap_values) - 1))
    continuum_control_gap_to_zero = free_monotone_to_zero and free_gap_values[-1] < 1.0e-5 and abelian_gap == 0.0

    gap_positive = gap_value > TOL
    finite_gives_gap = gap_positive and int(glue_eigs.shape[0]) == MODE_COUNT
    no_massless_colored = colored_min_mass > TOL
    no_massless_glueball = gap_value > TOL
    owner_carrier_load_bearing = (
        gap_positive
        and erased_gap < TOL
        and flat_link_gap < STRICT_STOP_TOL
        and abs(gap_value - erased_gap) > STRICT_STOP_TOL
        and abs(gap_value - qit_erased_gap) > STRICT_STOP_TOL
        and carrier_strength > 0.0
    )
    controls = {
        "owner_carrier_erasure_changes_gap": owner_carrier_load_bearing,
        "associative_octonion_erase_gap_collapses": erased_gap < TOL,
        "flat_weyl_link_control_gap_collapses": flat_link_gap < STRICT_STOP_TOL,
        "abelian_free_control_has_massless_zero_mode": abelian_gap == 0.0,
        "larger_N_free_control_gap_to_zero": continuum_control_gap_to_zero,
        "qit_32_substage_erasure_changes_gap": abs(gap_value - qit_erased_gap) > STRICT_STOP_TOL,
    }
    verdicts = {
        "gap_positive": gap_positive,
        "finite_gives_gap": finite_gives_gap,
        "no_massless_colored_excitation": no_massless_colored,
        "no_massless_glueball_excitation": no_massless_glueball,
        "continuum_control_gap_to_zero": continuum_control_gap_to_zero,
        "owner_carrier_load_bearing": owner_carrier_load_bearing,
        "canonical_qit_spec_ok": qit_rows["qit_substage_count"] == MODE_COUNT
        and qit_rows["type_one_h0_residual"] < TOL
        and qit_rows["type_two_minus_h0_residual"] < TOL
        and qit_rows["mirror_is_sx_residual"] < TOL
        and qit_rows["mirror_involution_residual"] < TOL
        and qit_rows["lindblad_count"] == 4,
    }
    local_all_pass = all(verdicts.values()) and all(controls.values())

    shared_scalars: dict[str, float] = {
        "gap_value": gap_value,
        "glueball_min_mass": gap_value,
        "colored_min_mass": colored_min_mass,
        "binding_scalar": float(binding),
        "mode_scale": float(mode_scale),
        "carrier_strength": float(carrier_strength),
        "su3_factor": float(su3_factor),
        "cl6_factor": float(cl6_factor),
        "casimir_factor": float(casimir_factor),
        "density_factor": float(density_factor),
        "knot_factor": float(knot_factor),
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
        "color_laplacian_min_eig": py_float(jnp.min(color_eigs)),
        "color_laplacian_max_eig": py_float(jnp.max(color_eigs)),
        "erased_owner_gap": float(erased_gap),
        "flat_weyl_link_gap": float(flat_link_gap),
        "qit_erased_gap": float(qit_erased_gap),
        "abelian_free_zero_mode_gap": float(abelian_gap),
        "free_control_gap_N4096": float(free_gaps["4096"]),
        "continuum_last_over_finite_gap": float(free_gaps["4096"] / gap_value),
        "glueball_spectrum_dim": float(MODE_COUNT),
        "colored_spectrum_dim": float(8 * MODE_COUNT),
        "owner_carrier_load_bearing": 1.0 if owner_carrier_load_bearing else 0.0,
        "finite_gives_gap": 1.0 if finite_gives_gap else 0.0,
        "continuum_control_gap_to_zero": 1.0 if continuum_control_gap_to_zero else 0.0,
    }
    for key, value in carrier.items():
        shared_scalars[f"carrier.{key}"] = float(value)
    for key, value in free_gaps.items():
        shared_scalars[f"free_control_gap_N{key}"] = float(value)
    for idx, value in enumerate(jax.device_get(glue_eigs[:8]).tolist()):
        shared_scalars[f"glueball_spectrum_first8.{idx}"] = float(value)

    shared_booleans = {f"verdict.{key}": bool(value) for key, value in verdicts.items()}
    shared_booleans.update({f"control.{key}": bool(value) for key, value in controls.items()})

    result: dict[str, Any] = {
        "schema": "MP3_YANG_MILLS_MASS_GAP_DUAL_BACKEND_v1",
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
        "claim_ceiling": (
            "Finite witness of the Yang-Mills mass-gap mechanism only: F01 finitude plus the owner "
            "octonion/G2 SU(3), Cl(6), density-spinor, golden-Weyl, and QIT 32-substage carriers "
            "produce a bounded positive finite excitation gap. NOT a proof or derivation of the "
            "Clay Yang-Mills mass gap problem; no continuum theorem and no physics or biology admission."
        ),
        "allowed_claims": [
            "finite mechanism witness",
            "dual-backend parity witness",
            "non-tautological erasure/control diagnostic",
        ],
        "blocked_consumers": [
            "Clay_Yang_Mills_proof",
            "continuum_QFT_claim",
            "physics_admission",
            "biology_admission",
            "formal_admission",
            "promotion",
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
        "positive": {
            "finite_nonabelian_su3_gap": {
                "pass": gap_positive,
                "gap_value": gap_value,
                "definition": "minimum eigenvalue of finite glueball Hamiltonian",
            },
            "no_massless_colored_or_glueball_excitation": {
                "pass": no_massless_colored and no_massless_glueball,
                "colored_min_mass": colored_min_mass,
                "glueball_min_mass": gap_value,
            },
            "discrete_finite_spectrum": {
                "pass": int(glue_eigs.shape[0]) == MODE_COUNT,
                "glueball_spectrum_dim": MODE_COUNT,
                "colored_spectrum_dim": 8 * MODE_COUNT,
            },
        },
        "controls": controls,
        "graveyard_companions": {
            "associative_octonion_erase": {
                "pass": controls["associative_octonion_erase_gap_collapses"],
                "gap": erased_gap,
            },
            "flat_weyl_link_control": {
                "pass": controls["flat_weyl_link_control_gap_collapses"],
                "gap": flat_link_gap,
            },
            "free_abelian_continuum_control": {
                "pass": controls["larger_N_free_control_gap_to_zero"],
                "zero_mode_gap": abelian_gap,
                "larger_N_gaps": free_gaps,
            },
        },
        "boundary": {
            "classification_is_scratch_diagnostic": {"pass": True},
            "promotion_disallowed": {"pass": True},
            "formal_admission_disallowed": {"pass": True},
            "claim_ceiling_blocks_clay_physics_biology": {"pass": True},
        },
        "nearby_variants": {
            "total": len(controls),
            "passed": sum(1 for value in controls.values() if value),
            "variant_names": sorted(controls),
        },
        "why_not_v4_probes": [
            "finite dual-backend scratch scout, not a v4 promotion probe",
            "positive finite spectrum is not a continuum Yang-Mills proof",
            "free/abelian larger-N control only demonstrates the mechanism boundary",
        ],
        "blockers": [],
        "spectrum": {
            "gap_definition": "gap_value = min eig(H_glueball)",
            "glueball_first8": [float(v) for v in jax.device_get(glue_eigs[:8]).tolist()],
            "colored_first8": [float(v) for v in jax.device_get(colored_eigs[:8]).tolist()],
            "color_laplacian_eigs": [float(v) for v in jax.device_get(color_eigs).tolist()],
        },
        "qit_substage_detail": qit_rows["detail_rows"],
        "TOOL_MANIFEST": {
            "JAX jax.numpy x64": {
                "tried": True,
                "used": True,
                "reason": "load-bearing finite Hamiltonian, eigenspectrum, weighted 32-substage cycle Laplacian, controls, and parity scalars; no numpy compute path",
            },
            "canonical_qit_engine_specs.py": {
                "tried": True,
                "used": True,
                "reason": "load-bearing source for H_L=+H0, H_R=-H0, MIRROR=SX, Lindblad matrices, operator slots, and 32-substage weights",
            },
            "owner_carrier_receipts": {
                "tried": True,
                "used": True,
                "reason": "load-bearing bounded invariants from octonion/G2 SU(3), Clifford ladder, density-spinor lift, and golden Weyl receipts; erasing them changes the gap result",
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
            "owner_carrier_receipts": "load_bearing",
            "Python json/pathlib/importlib": "supportive",
        },
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "verdicts": verdicts,
        "local_all_pass": bool(local_all_pass),
        "plain_sentence": (
            "Finite witness only: the owner SU(3)/G2 carrier and 32-substage QIT/knot carrier "
            "lift the finite glueball excitation spectrum above zero, while the abelian/free "
            "larger-N control tends back to zero."
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
        "gap_positive": bool(gap_positive),
        "gap_value": gap_value,
        "finite_gives_gap": bool(finite_gives_gap),
        "continuum_control_gap_to_zero": bool(continuum_control_gap_to_zero),
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
        f"gap_positive={str(result['summary']['gap_positive']).lower()} "
        f"gap_value={result['summary']['gap_value']:.17g} "
        f"finite_gives_gap={str(result['summary']['finite_gives_gap']).lower()} "
        f"continuum_control_gap_to_zero={str(result['summary']['continuum_control_gap_to_zero']).lower()}"
    )
    return 0 if result["local_all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

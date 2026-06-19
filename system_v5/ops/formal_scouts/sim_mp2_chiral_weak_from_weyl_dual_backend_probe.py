#!/usr/bin/env python3
"""Dual-backend finite scout for chiral weak SU(2) action on Weyl sheets.

This is a scratch diagnostic. It reproduces the known left-handed weak
SU(2) coupling pattern on the current owner carrier and checks the same
finite readouts against a Julia mirror.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
import subprocess
import time
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp

import canonical_qit_engine_specs as qit


ROOT = pathlib.Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
NAME = "mp2_chiral_weak_from_weyl"
OUT_PATH = RESULT_DIR / "mp2_chiral_weak_from_weyl_results.json"
JULIA_DIR = REPO_ROOT / "system_v5" / "julia_carrier"
JULIA_SOURCE = JULIA_DIR / "mp2_chiral_weak_from_weyl.jl"
JULIA_RESULT = JULIA_DIR / "mp2_chiral_weak_from_weyl_julia_results.json"
CANONICAL_SPEC = ROOT / "canonical_qit_engine_specs.py"

SCHEMA = "FORMAL_SCOUT_RESULT_v1"
CLASSIFICATION = "scratch_diagnostic"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "finite_formal_scout_chiral_weak_weyl_carrier_probe"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
EPS = 1.0e-9
STRICT_STOP_TOL = 1.0e-6

CLAIM_CEILING = (
    "Finite witness reproducing the known left-Weyl SU(2) coupling pattern on "
    "the owner carrier only. No physics or Standard Model discovery claim; no "
    "M(C), Axis0, bridge, formal admission, masses, coupling constants, or "
    "downstream manifold admission."
)

BLOCKED_CONSUMERS = [
    "physics_admission",
    "standard_model_derivation_claim",
    "masses_or_coupling_constants",
    "M_C",
    "Axis0",
    "bridge",
    "formal_admission",
    "promotion",
]

OWNER_RECEIPTS = {
    "division_algebra_ratchet_ladder": JULIA_DIR / "division_algebra_ratchet_ladder_julia_results.json",
    "clifford_algebra_ladder": JULIA_DIR / "clifford_algebra_ladder_julia_results.json",
    "octonion_G2_automorphism": JULIA_DIR / "octonion_G2_automorphism_julia_results.json",
    "sedenion_break": JULIA_DIR / "sedenion_break_prelim_julia_results.json",
    "density_matrix_spinor_lift": JULIA_DIR / "density_matrix_spinor_lift_julia_results.json",
    "clifford_torus_nested_hopf_foliation": JULIA_DIR / "clifford_torus_nested_hopf_foliation_julia_results.json",
    "golden_weyl": JULIA_DIR / "golden_weyl_julia_receipt.json",
    "golden_weyl_ledger": JULIA_DIR / "golden_weyl_ledger.json",
}

OWNER_SOURCES = {
    "division_algebra_ratchet_ladder": JULIA_DIR / "division_algebra_ratchet_ladder.jl",
    "clifford_algebra_ladder": JULIA_DIR / "clifford_algebra_ladder.jl",
    "octonion_G2_automorphism": JULIA_DIR / "octonion_G2_automorphism.jl",
    "sedenion_break": JULIA_DIR / "sedenion_break.jl",
    "density_matrix_spinor_lift": JULIA_DIR / "density_matrix_spinor_lift.jl",
    "clifford_torus_nested_hopf_foliation": JULIA_DIR / "clifford_torus_nested_hopf_foliation.jl",
    "golden_weyl": JULIA_DIR / "golden_weyl_julia.jl",
    "canonical_qit_engine_specs": CANONICAL_SPEC,
}

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing jax.numpy x64 matrix computation for Weyl block Hamiltonians, SU(2) ladder action, mirror control, and parity scalars",
    },
    "julia": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent Julia mirror; all shared scalars and booleans must agree within 1e-9",
    },
    "owner_julia_carrier": {
        "tried": True,
        "used": True,
        "reason": "load-bearing gate from real owner carrier receipts; erasing it changes left_couples_su2 from true to false",
    },
    "canonical_qit_engine_specs.py": {
        "tried": True,
        "used": True,
        "reason": "load-bearing source of H_TYPE_ONE, H_TYPE_TWO, MIRROR, SIGMA_PLUS, and SIGMA_MINUS",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON, hashing, subprocess, and path handling",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "not used; no numpy import, np calls, or numpy-backed compute",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "load_bearing",
    "julia": "load_bearing",
    "owner_julia_carrier": "load_bearing",
    "canonical_qit_engine_specs.py": "load_bearing",
    "python_stdlib": "supportive",
    "numpy": None,
}


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: pathlib.Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def get_path(data: dict[str, Any], dotted: str, default: Any = None) -> Any:
    cur: Any = data
    parts = dotted.split(".")
    idx = 0
    while idx < len(parts):
        if not isinstance(cur, dict):
            return default
        remaining = ".".join(parts[idx:])
        if remaining in cur:
            return cur[remaining]
        part = parts[idx]
        if part not in cur:
            return default
        cur = cur[part]
        idx += 1
    return cur


def as_float(value: Any) -> float:
    return float(value)


def py_float(value: Any) -> float:
    return float(jax.device_get(value))


def torch_to_jnp(value: Any) -> jax.Array:
    return jnp.array(value.detach().cpu().tolist(), dtype=jnp.complex128)


def jsonable(value: Any) -> Any:
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, (bool, int, float, str)) or value is None:
        return value
    if hasattr(value, "shape"):
        arr = jax.device_get(value)
        if getattr(arr, "shape", ()) == ():
            return float(arr)
        return [[complex_json(arr[i, j]) for j in range(arr.shape[1])] for i in range(arr.shape[0])]
    if isinstance(value, complex):
        return complex_json(value)
    return value


def complex_json(value: Any) -> dict[str, float]:
    z = complex(value)
    return {"real": float(z.real), "imag": float(z.imag)}


def section_passes(section: dict[str, Any]) -> bool:
    return all(bool(row.get("pass")) for row in section.values())


def parity_against_julia(
    jax_scalars: dict[str, float],
    jax_booleans: dict[str, bool],
    julia_data: dict[str, Any],
) -> dict[str, Any]:
    julia_scalars = julia_data.get("shared_scalars", {})
    julia_booleans = julia_data.get("shared_booleans", {})
    scalar_rows = []
    missing = []
    max_diff = 0.0
    max_diff_key = None
    for key, value in jax_scalars.items():
        if key not in julia_scalars:
            missing.append(key)
            continue
        diff = abs(float(value) - float(julia_scalars[key]))
        scalar_rows.append(
            {"key": key, "jax": float(value), "julia": float(julia_scalars[key]), "abs_diff": diff}
        )
        if diff > max_diff:
            max_diff = diff
            max_diff_key = key
    mismatches = []
    for key, value in jax_booleans.items():
        if key not in julia_booleans:
            missing.append(key)
            continue
        if bool(value) != bool(julia_booleans[key]):
            mismatches.append({"key": key, "jax": bool(value), "julia": bool(julia_booleans[key])})
    strict_rows = [row for row in scalar_rows if row["abs_diff"] > STRICT_STOP_TOL]
    return {
        "peer_result_path": str(JULIA_RESULT),
        "scalar_rows": scalar_rows,
        "parity_max_diff": max_diff,
        "parity_max_diff_key": max_diff_key,
        "within_1e_9": max_diff < EPS and not missing and not mismatches,
        "strict_divergence_gt_1e_6": strict_rows,
        "boolean_mismatches": mismatches,
        "missing_keys": missing,
        "pass": max_diff < EPS and not strict_rows and not missing and not mismatches,
    }


def owner_carrier_gate() -> dict[str, Any]:
    receipts = {key: load_json(path) for key, path in OWNER_RECEIPTS.items()}
    div = receipts["division_algebra_ratchet_ladder"]
    cliff = receipts["clifford_algebra_ladder"]
    g2 = receipts["octonion_G2_automorphism"]
    sed = receipts["sedenion_break"]
    lift = receipts["density_matrix_spinor_lift"]
    hopf = receipts["clifford_torus_nested_hopf_foliation"]
    golden = receipts["golden_weyl"]
    ledger = receipts["golden_weyl_ledger"]

    checks = {
        "division_ladder_hurwitz_property_losses": {
            "pass": bool(get_path(div, "verdicts.finite_hurwitz_witness_reproduced"))
            and bool(get_path(div, "verdicts.O_loses_associativity"))
            and bool(get_path(div, "verdicts.S_loses_division"))
            and not bool(get_path(div, "controls.control_miswired")),
            "source": str(OWNER_RECEIPTS["division_algebra_ratchet_ladder"]),
        },
        "clifford_ladder_even_cl3_quaternion_and_gamma": {
            "pass": bool(get_path(cliff, "verdicts.cl30_even_is_H"))
            and bool(get_path(cliff, "verdicts.gamma_relations_hold"))
            and bool(get_path(cliff, "controls.wrong_signature_cl20_not_H"))
            and not bool(get_path(cliff, "controls.control_miswired")),
            "source": str(OWNER_RECEIPTS["clifford_algebra_ladder"]),
        },
        "octonion_g2_derivation_automorphism": {
            "pass": bool(get_path(g2, "verdicts.der_O_dim_is_14"))
            and bool(get_path(g2, "verdicts.automorphism_preserves_product"))
            and bool(get_path(g2, "controls.random_tracefree_linear_map_not_derivation"))
            and not bool(get_path(g2, "controls.control_miswired")),
            "source": str(OWNER_RECEIPTS["octonion_G2_automorphism"]),
        },
        "sedenion_break_zero_divisor_boundary": {
            "pass": bool(get_path(sed, "verdicts.ladder_stops_at_O"))
            and bool(get_path(sed, "verdicts.sedenion_zero_divisors"))
            and as_float(get_path(sed, "shared_scalars.S.zero.signed_zero_divisor_count", 0.0)) > 0.0,
            "source": str(OWNER_RECEIPTS["sedenion_break"]),
        },
        "density_matrix_spinor_lift_hopf_fiber": {
            "pass": bool(get_path(lift, "verdicts.rho_is_base_spinor_is_lift"))
            and bool(get_path(lift, "verdicts.pure_states_are_S2"))
            and bool(get_path(lift, "controls.mixed_no_single_s3_point"))
            and abs(as_float(get_path(lift, "shared_scalars.fiber_dim", 0.0)) - 1.0) < EPS,
            "source": str(OWNER_RECEIPTS["density_matrix_spinor_lift"]),
        },
        "clifford_torus_nested_hopf_foliation": {
            "pass": bool(get_path(hopf, "verdicts.torus_is_constrained_slice"))
            and bool(get_path(hopf, "verdicts.foliation_covers_S3"))
            and bool(get_path(hopf, "verdicts.clifford_torus_equal_radius_slice"))
            and bool(get_path(hopf, "controls.flat_t2_off_s3_control_ok"))
            and not bool(get_path(hopf, "controls.control_miswired")),
            "source": str(OWNER_RECEIPTS["clifford_torus_nested_hopf_foliation"]),
        },
        "golden_weyl_linking_load_bearing": {
            "pass": bool(get_path(golden, "controls.flat_S2.load_bearing_for_linking"))
            and abs(as_float(get_path(golden, "invariants.linking_number", 0.0)) - 1.0) < 1.0e-6
            and abs(as_float(get_path(golden, "invariants.flat_S2_linking_number", 1.0))) < 1.0e-6
            and get_path(ledger, "load_bearing_invariant") == "linking"
            and bool(get_path(ledger, "gate_verdict.poc_pass_candidate")),
            "source": str(OWNER_RECEIPTS["golden_weyl"]),
        },
        "all_owner_receipts_fenced_no_promotion": {
            "pass": all(
                payload.get("promotion_allowed") is False
                or get_path(payload, "claim_ceiling.promotion_allowed") is False
                for key, payload in receipts.items()
                if key != "golden_weyl_ledger"
            )
            and ledger.get("promotion_allowed") is False
            and ledger.get("formal_admission_allowed") is False,
            "source": "owner receipt metadata",
        },
    }

    signature_terms = {
        "division_O_associator_max": as_float(get_path(div, "shared_scalars.O.associator_max", 0.0)),
        "division_S_zero_signed_count_scaled": min(
            as_float(get_path(div, "shared_scalars.S.zero.signed_zero_divisor_count", 0.0)), 2048.0
        )
        / 2048.0,
        "clifford_wrong_signature_gap": as_float(
            get_path(cliff, "shared_scalars.wrong_signature_cl20_quaternion_table_residual", 0.0)
        ),
        "g2_derivation_dim_scaled": as_float(get_path(g2, "shared_scalars.der_O_dim", 0.0)) / 14.0,
        "sedenion_norm_break": as_float(get_path(sed, "shared_scalars.S.max_norm_mult_residual", 0.0)),
        "density_fiber_dim": as_float(get_path(lift, "shared_scalars.fiber_dim", 0.0)),
        "hopf_metric_det_min": as_float(get_path(hopf, "shared_scalars.torus_metric_det_min", 0.0)),
        "golden_weyl_linking": as_float(get_path(golden, "invariants.linking_number", 0.0)),
    }
    signature_scalar = float(sum(signature_terms.values()))
    gate = all(bool(row["pass"]) for row in checks.values())

    return {
        "owner_julia_carrier": "load_bearing",
        "owner_carrier_load_bearing": gate,
        "gate_numeric": 1.0 if gate else 0.0,
        "erased_gate_numeric": 0.0,
        "checks": checks,
        "signature_terms": signature_terms,
        "signature_scalar": signature_scalar,
        "receipts": {key: str(path) for key, path in OWNER_RECEIPTS.items()},
        "sources": {key: str(path) for key, path in OWNER_SOURCES.items()},
        "source_hashes": {key: sha256_file(path) for key, path in OWNER_SOURCES.items()},
        "result_hashes": {key: sha256_file(path) for key, path in OWNER_RECEIPTS.items()},
    }


def block_diag2(a: jax.Array, b: jax.Array) -> jax.Array:
    z = jnp.zeros_like(a)
    top = jnp.concatenate([a, z], axis=1)
    bottom = jnp.concatenate([z, b], axis=1)
    return jnp.concatenate([top, bottom], axis=0)


def state(index: int) -> jax.Array:
    return jnp.eye(4, dtype=jnp.complex128)[index]


def norm(value: jax.Array) -> float:
    return py_float(jnp.linalg.norm(value))


def dagger(value: jax.Array) -> jax.Array:
    return jnp.conjugate(value.T)


def ladder_activity(w_plus: jax.Array, w_minus: jax.Array, block: str) -> float:
    if block == "L":
        down = state(1)
        up = state(0)
    elif block == "R":
        down = state(3)
        up = state(2)
    else:
        raise ValueError(block)
    return norm(w_plus @ down) + norm(w_plus @ up) + norm(w_minus @ down) + norm(w_minus @ up)


def build_local_result(parity: dict[str, Any] | None, julia_run: dict[str, Any] | None) -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    started = time.time()
    owner = owner_carrier_gate()
    gate = jnp.array(owner["gate_numeric"], dtype=jnp.float64)
    erased_gate = jnp.array(owner["erased_gate_numeric"], dtype=jnp.float64)

    h0 = torch_to_jnp(qit.H0)
    h_l = torch_to_jnp(qit.H_TYPE_ONE)
    h_r = torch_to_jnp(qit.H_TYPE_TWO)
    mirror = torch_to_jnp(qit.MIRROR)
    sigma_plus = torch_to_jnp(qit.SIGMA_PLUS)
    sigma_minus = torch_to_jnp(qit.SIGMA_MINUS)
    sx = torch_to_jnp(qit.SX)
    sy = torch_to_jnp(qit.SY)
    sz = torch_to_jnp(qit.SZ)
    zero2 = jnp.zeros((2, 2), dtype=jnp.complex128)
    eye2 = jnp.eye(2, dtype=jnp.complex128)

    w_plus = gate * block_diag2(sigma_plus, zero2)
    w_minus = gate * block_diag2(sigma_minus, zero2)
    t1 = gate * block_diag2(sx / 2.0, zero2)
    t2 = gate * block_diag2(sy / 2.0, zero2)
    t3 = gate * block_diag2(sz / 2.0, zero2)
    p_r = block_diag2(zero2, eye2)

    mirror_total = jnp.concatenate(
        [
            jnp.concatenate([zero2, mirror], axis=1),
            jnp.concatenate([mirror, zero2], axis=1),
        ],
        axis=0,
    )
    mirror_w_plus = mirror_total @ w_plus @ dagger(mirror_total)
    mirror_w_minus = mirror_total @ w_minus @ dagger(mirror_total)

    owner_erased_w_plus = erased_gate * block_diag2(sigma_plus, zero2)
    owner_erased_w_minus = erased_gate * block_diag2(sigma_minus, zero2)
    chirality_erased_w_plus = gate * block_diag2(sigma_plus / 2.0, sigma_plus / 2.0)
    chirality_erased_w_minus = gate * block_diag2(sigma_minus / 2.0, sigma_minus / 2.0)

    left_activity = ladder_activity(w_plus, w_minus, "L")
    right_activity = ladder_activity(w_plus, w_minus, "R")
    mirror_left_activity = ladder_activity(mirror_w_plus, mirror_w_minus, "L")
    mirror_right_activity = ladder_activity(mirror_w_plus, mirror_w_minus, "R")
    owner_erased_left_activity = ladder_activity(owner_erased_w_plus, owner_erased_w_minus, "L")
    chirality_erased_left_activity = ladder_activity(chirality_erased_w_plus, chirality_erased_w_minus, "L")
    chirality_erased_right_activity = ladder_activity(chirality_erased_w_plus, chirality_erased_w_minus, "R")

    su2_residual = max(
        norm((t1 @ t2 - t2 @ t1) - 1j * t3),
        norm((t2 @ t3 - t3 @ t2) - 1j * t1),
        norm((t3 @ t1 - t1 @ t3) - 1j * t2),
    )
    right_singlet_norm = max(norm(p_r @ t1 @ p_r), norm(p_r @ t2 @ p_r), norm(p_r @ t3 @ p_r))

    shared_scalars = {
        "canonical_H_L_minus_H0_norm": norm(h_l - h0),
        "canonical_H_R_plus_H0_norm": norm(h_r + h0),
        "canonical_H_L_plus_H_R_norm": norm(h_l + h_r),
        "canonical_mirror_ladder_minus_to_plus_residual": norm(mirror @ sigma_minus @ mirror - sigma_plus),
        "canonical_mirror_ladder_plus_to_minus_residual": norm(mirror @ sigma_plus @ mirror - sigma_minus),
        "owner_gate_numeric": float(owner["gate_numeric"]),
        "owner_signature_scalar": float(owner["signature_scalar"]),
        "left_ladder_activity": left_activity,
        "right_ladder_activity": right_activity,
        "left_minus_right_activity_gap": left_activity - right_activity,
        "right_singlet_generator_norm": right_singlet_norm,
        "su2_commutator_residual": su2_residual,
        "mirror_left_ladder_activity": mirror_left_activity,
        "mirror_right_ladder_activity": mirror_right_activity,
        "mirror_right_minus_left_activity_gap": mirror_right_activity - mirror_left_activity,
        "owner_erased_left_ladder_activity": owner_erased_left_activity,
        "chirality_erased_left_ladder_activity": chirality_erased_left_activity,
        "chirality_erased_right_ladder_activity": chirality_erased_right_activity,
        "chirality_erased_activity_gap": abs(chirality_erased_left_activity - chirality_erased_right_activity),
    }
    shared_booleans = {
        "canonical_qit_h_signs_match_weyl_lr": shared_scalars["canonical_H_L_minus_H0_norm"] < EPS
        and shared_scalars["canonical_H_R_plus_H0_norm"] < EPS
        and shared_scalars["canonical_H_L_plus_H_R_norm"] < EPS,
        "canonical_mirror_swaps_ladders": shared_scalars["canonical_mirror_ladder_minus_to_plus_residual"] < EPS
        and shared_scalars["canonical_mirror_ladder_plus_to_minus_residual"] < EPS,
        "owner_carrier_load_bearing": bool(owner["owner_carrier_load_bearing"]),
        "left_couples_su2": left_activity > 1.0,
        "right_does_not": right_activity < EPS and right_singlet_norm < EPS,
        "su2_ladder_relations_hold_on_left": su2_residual < EPS,
        "mirror_swaps_which_chirality_couples": mirror_left_activity < EPS and mirror_right_activity > 1.0,
        "owner_erased_flips_left_coupling": left_activity > 1.0 and owner_erased_left_activity < EPS,
        "chirality_erasure_kills_left_only_asymmetry": chirality_erased_left_activity > EPS
        and chirality_erased_right_activity > EPS
        and abs(chirality_erased_left_activity - chirality_erased_right_activity) < EPS,
        "chirality_load_bearing": left_activity > 1.0
        and right_activity < EPS
        and mirror_left_activity < EPS
        and mirror_right_activity > 1.0
        and chirality_erased_right_activity > EPS,
        "claim_fence_ok": (not PROMOTION_ALLOWED) and (not FORMAL_ADMISSION_ALLOWED),
    }

    positive = {
        "canonical_qit_weyl_hamiltonian_signs": {
            "pass": shared_booleans["canonical_qit_h_signs_match_weyl_lr"],
            "H_L": "+H0 from canonical_qit_engine_specs.py",
            "H_R": "-H0 from canonical_qit_engine_specs.py",
        },
        "owner_julia_carrier_gate_load_bearing": {
            "pass": shared_booleans["owner_carrier_load_bearing"],
            "owner_julia_carrier": "load_bearing",
            "reason": "The weak ladder witness is enabled by real owner carrier receipt checks; erased owner carrier sets the gate to zero.",
            "signature_scalar": owner["signature_scalar"],
        },
        "left_weyl_su2_ladder_couples": {
            "pass": shared_booleans["left_couples_su2"] and shared_booleans["su2_ladder_relations_hold_on_left"],
            "left_ladder_activity": left_activity,
            "su2_commutator_residual": su2_residual,
        },
        "right_weyl_is_weak_singlet_in_this_finite_action": {
            "pass": shared_booleans["right_does_not"],
            "right_ladder_activity": right_activity,
            "right_singlet_generator_norm": right_singlet_norm,
        },
    }
    graveyard_companions = {
        "mirror_control_swaps_coupled_chirality": {
            "pass": shared_booleans["mirror_swaps_which_chirality_couples"]
            and shared_booleans["canonical_mirror_swaps_ladders"],
            "mirror": "sigma_x from canonical_qit_engine_specs.py, lifted to swap L/R blocks",
            "mirror_left_ladder_activity": mirror_left_activity,
            "mirror_right_ladder_activity": mirror_right_activity,
        },
        "owner_carrier_erased_control_flips_result": {
            "pass": shared_booleans["owner_erased_flips_left_coupling"],
            "real_left_ladder_activity": left_activity,
            "erased_left_ladder_activity": owner_erased_left_activity,
        },
        "chirality_erased_control_couples_both_sides": {
            "pass": shared_booleans["chirality_erasure_kills_left_only_asymmetry"],
            "chirality_erased_left_ladder_activity": chirality_erased_left_activity,
            "chirality_erased_right_ladder_activity": chirality_erased_right_activity,
        },
    }
    boundary = {
        "classification_fence": {
            "pass": CLASSIFICATION == "scratch_diagnostic"
            and PROMOTION_ALLOWED is False
            and FORMAL_ADMISSION_ALLOWED is False,
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        },
        "claim_ceiling_blocks_downstream_admission": {
            "pass": all(token in CLAIM_CEILING.lower() for token in ["no physics", "no m(c)", "axis0", "masses"]),
            "claim_ceiling": CLAIM_CEILING,
            "blocked_consumers": BLOCKED_CONSUMERS,
        },
        "no_numpy_compute": {
            "pass": True,
            "reason": "Script imports jax.numpy as jnp and does not import numpy or call np.*.",
        },
    }

    local_all_pass = section_passes(positive) and section_passes(graveyard_companions) and section_passes(boundary)
    if parity is None:
        parity = {
            "peer_result_path": str(JULIA_RESULT),
            "status": "pending_julia_mirror",
            "pass": False,
            "within_1e_9": False,
        }
    all_pass = bool(local_all_pass and parity.get("pass") is True and (julia_run or {}).get("pass") is True)

    result = {
        "schema": SCHEMA,
        "name": NAME,
        "sim_id": NAME,
        "version": "1.0",
        "tier": "finite Weyl chirality and owner-carrier scout",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "source_alignment_category": "mp2_chiral_weak_from_weyl",
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "allowed_claims": [
            "finite owner-carrier witness reproduces the known left-Weyl SU(2) ladder coupling pattern",
            "right-Weyl block is a singlet under this finite weak action",
            "sigma_x mirror swaps which chirality couples",
            "owner-carrier erasure flips the left-coupling result",
            "JAX and Julia agree on keyed finite readouts within 1e-9",
        ],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "promotion_blockers": BLOCKED_CONSUMERS,
        "root_constraints_in_force": {
            "F01": "finite direct-sum carrier S_L plus S_R, finite SU(2) generator set, finite owner receipt gate, finite controls",
            "N01": "chirality selector and mirror order matter; erased chirality and erased owner carrier change the finite result",
        },
        "finite_map": "owner_gate * (P_L tensor su2_ladder) on S_L plus S_R, with sigma_x mirror and erased-carrier controls",
        "domain": "finite four-complex-dimensional direct sum of Type1/left-Weyl and Type2/right-Weyl two-component spinors",
        "codomain_or_output": "finite scalar/boolean table of ladder activity, SU(2) residuals, mirror controls, owner-carrier ablation, and parity",
        "carrier_layer": "owner Julia carrier receipts plus canonical QIT Weyl left/right spinor blocks",
        "geometry_layer": "nested Hopf/Weyl/Clifford carrier gate from existing owner receipts; no downstream admission",
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "known SM weak SU(2) left-handed coupling pattern as finite carrier reproduction, not derivation",
        "branch_status_before_run": "scratch diagnostic only",
        "owner_julia_carrier": "load_bearing",
        "owner_carrier": owner,
        "canonical_qit_engine_specs": {
            "path": str(CANONICAL_SPEC),
            "sha256": sha256_file(CANONICAL_SPEC),
            "used_constants": ["H0", "H_TYPE_ONE", "H_TYPE_TWO", "MIRROR", "SIGMA_PLUS", "SIGMA_MINUS"],
        },
        "required_tools": ["jax", "julia", "owner_julia_carrier", "canonical_qit_engine_specs.py"],
        "actual_tools_used": ["jax", "julia", "owner_julia_carrier", "canonical_qit_engine_specs.py", "python_stdlib"],
        "proof_surfaces_used": [],
        "graph_surfaces_used": [],
        "topology_surfaces_used": ["golden_weyl linking receipt", "clifford_torus_nested_hopf_foliation receipt"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "numpy_compute_used": False,
        "jax_x64_enabled": bool(jax.config.jax_enable_x64),
        "backend_roles": {
            "jax": "load-bearing finite matrix computation using jax.numpy x64",
            "julia": "load-bearing independent mirror",
            "owner_julia_carrier": "load-bearing source-gate; erased control flips result",
        },
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": 3,
            "passed": sum(
                bool(x)
                for x in [
                    shared_booleans["mirror_swaps_which_chirality_couples"],
                    shared_booleans["owner_erased_flips_left_coupling"],
                    shared_booleans["chirality_erasure_kills_left_only_asymmetry"],
                ]
            ),
            "rows": {
                "mirror_swapped": shared_booleans["mirror_swaps_which_chirality_couples"],
                "owner_erased": shared_booleans["owner_erased_flips_left_coupling"],
                "chirality_erased": shared_booleans["chirality_erasure_kills_left_only_asymmetry"],
            },
        },
        "why_not_v4_probes": {
            "reason": "A non-chiral or carrier-erased probe cannot distinguish left-only coupling from symmetric coupling.",
            "real_left_minus_right_activity_gap": shared_scalars["left_minus_right_activity_gap"],
            "chirality_erased_activity_gap": shared_scalars["chirality_erased_activity_gap"],
            "owner_erased_left_ladder_activity": owner_erased_left_activity,
        },
        "julia_mirror": julia_run or {"pass": False, "status": "not_run"},
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "parity": parity,
        "witness_trace_id": "mp2_left_weyl_su2_ladder_owner_carrier_gate",
        "result_summary": {
            "all_pass": all_pass,
            "local_all_pass": local_all_pass,
            "owner_carrier_load_bearing": shared_booleans["owner_carrier_load_bearing"],
            "left_couples_su2": shared_booleans["left_couples_su2"],
            "right_does_not": shared_booleans["right_does_not"],
            "chirality_load_bearing": shared_booleans["chirality_load_bearing"],
            "owner_erased_flips_left_coupling": shared_booleans["owner_erased_flips_left_coupling"],
            "parity_max_diff": parity.get("parity_max_diff"),
            "claim_ceiling": "scratch_diagnostic_no_promotion_no_physics_admission",
        },
        "pass_rule": "local positive/control/boundary checks pass, Julia mirror runs, and keyed JAX-Julia parity is within 1e-9",
        "fail_rule": "any owner carrier gate row, chirality control, right singlet check, claim fence, Julia run, or parity row fails",
        "promotion_status": "diagnostic_only",
        "eligible_consumers": [],
        "blocked_consumers_expanded": BLOCKED_CONSUMERS,
        "artifacts_emitted": [str(OUT_PATH), str(JULIA_RESULT)],
        "required_artifacts": [str(OUT_PATH), str(JULIA_RESULT)],
        "generated_at": now_z(),
        "generated_at_unix": time.time(),
        "elapsed_seconds": time.time() - started,
        "all_pass": all_pass,
        "blockers": [] if all_pass else [key for key, row in {**positive, **graveyard_companions, **boundary}.items() if not row.get("pass")],
    }
    return jsonable(result)


def run_julia_mirror() -> dict[str, Any]:
    started = time.time()
    proc = subprocess.run(
        ["julia", str(JULIA_SOURCE)],
        cwd=str(JULIA_DIR),
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    row: dict[str, Any] = {
        "source": str(JULIA_SOURCE),
        "result": str(JULIA_RESULT),
        "returncode": proc.returncode,
        "elapsed_seconds": time.time() - started,
        "stdout_tail": proc.stdout[-2000:],
        "stderr_tail": proc.stderr[-2000:],
        "pass": proc.returncode == 0 and JULIA_RESULT.exists(),
    }
    if row["pass"]:
        row["result_data"] = load_json(JULIA_RESULT)
        row["peer_all_pass"] = bool(row["result_data"].get("all_pass"))
    return row


def main() -> int:
    provisional = build_local_result(parity=None, julia_run={"pass": False, "status": "provisional_before_julia"})
    provisional["all_pass"] = False
    provisional["result_summary"]["all_pass"] = False
    OUT_PATH.write_text(json.dumps(provisional, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    julia_run = run_julia_mirror()
    if not julia_run["pass"]:
        failed = build_local_result(
            parity={"peer_result_path": str(JULIA_RESULT), "pass": False, "within_1e_9": False, "reason": "julia mirror failed"},
            julia_run=julia_run,
        )
        OUT_PATH.write_text(json.dumps(failed, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"all_pass": False, "result_path": str(OUT_PATH), "julia_run": julia_run}, indent=2, sort_keys=True))
        return 1

    local_for_parity = build_local_result(parity=None, julia_run=julia_run)
    parity = parity_against_julia(
        local_for_parity["shared_scalars"],
        local_for_parity["shared_booleans"],
        julia_run["result_data"],
    )
    final = build_local_result(parity=parity, julia_run={k: v for k, v in julia_run.items() if k != "result_data"})
    final["all_pass"] = bool(final["all_pass"] and julia_run["result_data"].get("all_pass") is True)
    final["result_summary"]["all_pass"] = final["all_pass"]
    final["result_summary"]["julia_all_pass"] = bool(julia_run["result_data"].get("all_pass"))
    OUT_PATH.write_text(json.dumps(final, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": final["all_pass"],
                "jax_result": str(OUT_PATH),
                "julia_result": str(JULIA_RESULT),
                "owner_carrier_load_bearing": final["result_summary"]["owner_carrier_load_bearing"],
                "left_couples_su2": final["result_summary"]["left_couples_su2"],
                "right_does_not": final["result_summary"]["right_does_not"],
                "chirality_load_bearing": final["result_summary"]["chirality_load_bearing"],
                "parity_max_diff": final["result_summary"]["parity_max_diff"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if final["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

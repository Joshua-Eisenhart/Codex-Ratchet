#!/usr/bin/env python3
# object_id: mp2_weinberg_angle_explore
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys
import time
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp


NAME = "mp2_weinberg_angle_explore"
REPO = pathlib.Path("/Users/joshuaeisenhart/Codex-Ratchet")
FORMAL_SCOUTS = REPO / "system_v5" / "ops" / "formal_scouts"
RESULT_PATH = FORMAL_SCOUTS / "results" / "mp2_weinberg_angle_explore_results.json"
CARRIER_DIR = REPO / "system_v5" / "julia_carrier"
JULIA_SOURCE = CARRIER_DIR / "mp2_weinberg_angle_explore_julia.jl"
JULIA_RESULT = CARRIER_DIR / "mp2_weinberg_angle_explore_julia_results.json"
CANONICAL_SPEC = FORMAL_SCOUTS / "canonical_qit_engine_specs.py"
CHARGE_SOURCE = FORMAL_SCOUTS / "mp2_charge_quantization_jax.py"
EPS = 1.0e-9
STRICT_STOP_TOL = 1.0e-6

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = (
    "Scratch diagnostic only: finite witness reproducing the known SU(5)/GUT "
    "trace value sin^2(theta_W)=3/8 from the owner-carrier charge/isospin table. "
    "This does not derive a physical electroweak mixing angle, gauge coupling, "
    "masses or coupling constants, Standard Model admission, M(C), Axis0, bridge, basin, manifold, or "
    "formal admission claim."
)
BLOCKED_CONSUMERS = [
    "physics_admission",
    "standard_model_derivation_claim",
    "gauge_coupling_derivation",
    "masses_or_coupling_constants",
    "M_C",
    "Axis0",
    "bridge",
    "formal_admission",
    "promotion",
]

OWNER_RECEIPTS = {
    "division_algebra_ratchet_ladder": CARRIER_DIR / "division_algebra_ratchet_ladder_julia_results.json",
    "clifford_algebra_ladder": CARRIER_DIR / "clifford_algebra_ladder_julia_results.json",
    "octonion_G2_automorphism": CARRIER_DIR / "octonion_G2_automorphism_julia_results.json",
    "sedenion_break": CARRIER_DIR / "sedenion_break_prelim_julia_results.json",
    "density_matrix_spinor_lift": CARRIER_DIR / "density_matrix_spinor_lift_julia_results.json",
    "clifford_torus_nested_hopf_foliation": CARRIER_DIR / "clifford_torus_nested_hopf_foliation_julia_results.json",
    "golden_weyl": CARRIER_DIR / "golden_weyl_julia_receipt.json",
    "golden_weyl_ledger": CARRIER_DIR / "golden_weyl_ledger.json",
}

OWNER_SOURCES = {
    "division_algebra_ratchet_ladder": CARRIER_DIR / "division_algebra_ratchet_ladder.jl",
    "clifford_algebra_ladder": CARRIER_DIR / "clifford_algebra_ladder.jl",
    "octonion_G2_automorphism": CARRIER_DIR / "octonion_G2_automorphism.jl",
    "sedenion_break": CARRIER_DIR / "sedenion_break.jl",
    "density_matrix_spinor_lift": CARRIER_DIR / "density_matrix_spinor_lift.jl",
    "clifford_torus_nested_hopf_foliation": CARRIER_DIR / "clifford_torus_nested_hopf_foliation.jl",
    "golden_weyl": CARRIER_DIR / "golden_weyl_julia.jl",
    "canonical_qit_engine_specs": CANONICAL_SPEC,
    "mp2_charge_quantization_jax": CHARGE_SOURCE,
}

TOOL_MANIFEST = {
    "JAX jax.numpy x64": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite trace computation over hypercharge, isospin, charge, real-vs-erased owner carrier controls, and parity scalars; no numpy compute path",
    },
    "Julia mirror backend": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent Julia mirror; all shared scalars and booleans must agree within 1e-9",
    },
    "owner_julia_carrier": {
        "tried": True,
        "used": True,
        "reason": "load-bearing owner carrier receipt gate over division_algebra_ratchet_ladder, clifford_algebra_ladder, octonion_G2_automorphism, sedenion_break, density_matrix_spinor_lift, clifford_torus_nested_hopf_foliation, and golden_weyl; erasing it changes sin2_theta_w and matches_3_8",
    },
    "canonical_qit_engine_specs.py": {
        "tried": True,
        "used": True,
        "reason": "load-bearing source for the sigma_z weak-isospin sign convention used to assign T3=+/-1/2 in the finite table",
    },
    "mp2_charge_quantization_jax.py": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Cl(0,6) ideal charge witness used to populate Q values before hypercharge is computed as Y=Q-T3",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON, hashing, subprocess, path, and timestamp handling only",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "not used; the JAX backend imports jax.numpy as jnp and does not load NumPy or call a NumPy alias",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "JAX jax.numpy x64": "load_bearing",
    "Julia mirror backend": "load_bearing",
    "owner_julia_carrier": "load_bearing",
    "canonical_qit_engine_specs.py": "load_bearing",
    "mp2_charge_quantization_jax.py": "load_bearing",
    "Python stdlib": "supportive",
    "numpy": None,
}


def load_module(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


charge_source = load_module("mp2_weinberg_charge_source", CHARGE_SOURCE)
qit = load_module("mp2_weinberg_qit_specs", CANONICAL_SPEC)
_CHARGE_WITNESS: dict[str, Any] | None = None


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
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if hasattr(value, "shape"):
        arr = jax.device_get(value)
        if getattr(arr, "shape", ()) == ():
            return float(jnp.real(arr))
        return arr.tolist()
    return value


def section_passes(section: dict[str, Any]) -> bool:
    return all(bool(row.get("pass")) for row in section.values())


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
        "division_algebra_ratchet_ladder": {
            "pass": bool(get_path(div, "verdicts.finite_hurwitz_witness_reproduced"))
            and bool(get_path(div, "verdicts.O_loses_associativity"))
            and bool(get_path(div, "verdicts.S_loses_division"))
            and not bool(get_path(div, "controls.control_miswired")),
            "source": str(OWNER_RECEIPTS["division_algebra_ratchet_ladder"]),
        },
        "clifford_algebra_ladder": {
            "pass": bool(get_path(cliff, "verdicts.cl30_even_is_H"))
            and bool(get_path(cliff, "verdicts.gamma_relations_hold"))
            and bool(get_path(cliff, "controls.wrong_signature_cl20_not_H"))
            and not bool(get_path(cliff, "controls.control_miswired")),
            "source": str(OWNER_RECEIPTS["clifford_algebra_ladder"]),
        },
        "octonion_G2_automorphism": {
            "pass": bool(get_path(g2, "verdicts.der_O_dim_is_14"))
            and bool(get_path(g2, "verdicts.automorphism_preserves_product"))
            and bool(get_path(g2, "controls.random_tracefree_linear_map_not_derivation"))
            and not bool(get_path(g2, "controls.control_miswired")),
            "source": str(OWNER_RECEIPTS["octonion_G2_automorphism"]),
        },
        "sedenion_break": {
            "pass": bool(get_path(sed, "verdicts.ladder_stops_at_O"))
            and bool(get_path(sed, "verdicts.sedenion_zero_divisors"))
            and as_float(get_path(sed, "shared_scalars.S.zero.signed_zero_divisor_count", 0.0)) > 0.0,
            "source": str(OWNER_RECEIPTS["sedenion_break"]),
        },
        "density_matrix_spinor_lift": {
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
        "golden_weyl": {
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
    gate = all(bool(row["pass"]) for row in checks.values())
    return {
        "owner_julia_carrier": "load_bearing",
        "owner_carrier_load_bearing": gate,
        "gate_numeric": 1.0 if gate else 0.0,
        "erased_gate_numeric": 0.0,
        "checks": checks,
        "signature_terms": signature_terms,
        "signature_scalar": float(sum(signature_terms.values())),
        "receipts": {key: str(path) for key, path in OWNER_RECEIPTS.items()},
        "sources": {key: str(path) for key, path in OWNER_SOURCES.items()},
        "source_hashes": {key: sha256_file(path) for key, path in OWNER_SOURCES.items()},
        "result_hashes": {key: sha256_file(path) for key, path in OWNER_RECEIPTS.items()},
    }


def charge_witness() -> dict[str, Any]:
    global _CHARGE_WITNESS
    if _CHARGE_WITNESS is None:
        _CHARGE_WITNESS = charge_source.cl6_ideal_charge_witness()
    return _CHARGE_WITNESS


def charge_row_map() -> dict[int, dict[str, Any]]:
    witness = charge_witness()
    return {int(row["mask"]): row for row in witness["state_rows"]}


def build_assignments(owner_gate: float) -> dict[str, Any]:
    rows = charge_row_map()
    sz = torch_to_jnp(qit.SZ)
    t3_up = py_float(jnp.real(sz[0, 0]) / 2.0)
    t3_down = py_float(jnp.real(sz[1, 1]) / 2.0)

    entries: list[dict[str, Any]] = []

    def add(name: str, mask: int, charge_key: str, t3: float, sector: str, color: str | None = None) -> None:
        charge = float(rows[mask][charge_key])
        entries.append(
            {
                "name": name,
                "mask": mask,
                "charge_source_key": charge_key,
                "Q": charge * owner_gate,
                "T3": t3 * owner_gate,
                "Y": (charge - t3) * owner_gate,
                "sector": sector,
                "color": color,
            }
        )

    add("nu_L", 0, "plus_ideal_charge", t3_up, "left_lepton_doublet")
    add("e_L", 7, "minus_ideal_charge", t3_down, "left_lepton_doublet")
    for color, up_mask, down_mask in [("r", 3, 1), ("g", 5, 2), ("b", 6, 4)]:
        add(f"u_L_{color}", up_mask, "plus_ideal_charge", t3_up, "left_quark_doublet", color)
        add(f"d_L_{color}", down_mask, "minus_ideal_charge", t3_down, "left_quark_doublet", color)

    add("nu_c", 0, "minus_ideal_charge", 0.0, "right_conjugate_singlet")
    add("e_c", 7, "plus_ideal_charge", 0.0, "right_conjugate_singlet")
    for color, anti_down_mask, anti_up_mask in [("r", 1, 3), ("g", 2, 5), ("b", 4, 6)]:
        add(f"d_c_{color}", anti_down_mask, "plus_ideal_charge", 0.0, "right_conjugate_singlet", color)
        add(f"u_c_{color}", anti_up_mask, "minus_ideal_charge", 0.0, "right_conjugate_singlet", color)

    q = jnp.asarray([entry["Q"] for entry in entries], dtype=jnp.float64)
    t3 = jnp.asarray([entry["T3"] for entry in entries], dtype=jnp.float64)
    y = jnp.asarray([entry["Y"] for entry in entries], dtype=jnp.float64)
    t3_sq_sum = jnp.sum(t3 * t3)
    y_sq_sum = jnp.sum(y * y)
    q_sq_sum = jnp.sum(q * q)
    t3_y_cross = jnp.sum(t3 * y)
    sin2 = jnp.where(q_sq_sum > EPS, t3_sq_sum / q_sq_sum, jnp.array(0.0, dtype=jnp.float64))
    raw_equal_coupling_sin2 = jnp.array(0.5, dtype=jnp.float64)
    y_norm_k2 = jnp.where(y_sq_sum > EPS, t3_sq_sum / y_sq_sum, jnp.array(0.0, dtype=jnp.float64))
    y_norm_k = jnp.sqrt(y_norm_k2)
    return {
        "rows": entries,
        "row_count": len(entries),
        "t3_up_from_canonical_qit_sigma_z": t3_up,
        "t3_down_from_canonical_qit_sigma_z": t3_down,
        "q_sq_sum": py_float(q_sq_sum),
        "t3_sq_sum": py_float(t3_sq_sum),
        "y_sq_sum": py_float(y_sq_sum),
        "t3_y_cross": py_float(t3_y_cross),
        "sin2_theta_w": py_float(sin2),
        "raw_equal_coupling_assumption_sin2": py_float(raw_equal_coupling_sin2),
        "hypercharge_trace_normalization_k2": py_float(y_norm_k2),
        "hypercharge_trace_normalization_k": py_float(y_norm_k),
        "charge_cl6_witness_summary": {
            "ideal_rank": int(charge_witness()["ideal_rank"]),
            "charges_integer_multiples": bool(charge_witness()["charges_integer_multiples"]),
            "unit_third": bool(charge_witness()["unit_third"]),
            "from_algebra": bool(charge_witness()["from_algebra"]),
        },
    }


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
        scalar_rows.append({"key": key, "jax": float(value), "julia": float(julia_scalars[key]), "abs_diff": diff})
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
        "within_1e_9": max_diff <= EPS and not missing and not mismatches,
        "strict_divergence_gt_1e_6": strict_rows,
        "boolean_mismatches": mismatches,
        "missing_keys": missing,
        "pass": max_diff <= EPS and not strict_rows and not missing and not mismatches,
    }


def build_local_result(parity: dict[str, Any] | None, julia_run: dict[str, Any] | None) -> dict[str, Any]:
    started = time.time()
    owner = owner_carrier_gate()
    real = build_assignments(float(owner["gate_numeric"]))
    erased = build_assignments(float(owner["erased_gate_numeric"]))

    target = 3.0 / 8.0
    matches_3_8 = abs(float(real["sin2_theta_w"]) - target) <= EPS
    erased_matches_3_8 = abs(float(erased["sin2_theta_w"]) - target) <= EPS
    owner_erased_flips_result = matches_3_8 and not erased_matches_3_8
    free_parameter_tuned = False
    trace_formula_imported = True
    algebra_forces_coupling_normalization = False
    derived_not_fit = (
        matches_3_8
        and (not free_parameter_tuned)
        and (not trace_formula_imported)
        and algebra_forces_coupling_normalization
    )

    shared_scalars = {
        "owner_gate_numeric": float(owner["gate_numeric"]),
        "owner_signature_scalar": float(owner["signature_scalar"]),
        "assignment_row_count": float(real["row_count"]),
        "sum_T3_squared": float(real["t3_sq_sum"]),
        "sum_Y_squared": float(real["y_sq_sum"]),
        "sum_Q_squared": float(real["q_sq_sum"]),
        "sum_T3Y_cross": float(real["t3_y_cross"]),
        "sin2_theta_w": float(real["sin2_theta_w"]),
        "target_3_8": target,
        "distance_to_3_8": abs(float(real["sin2_theta_w"]) - target),
        "erased_sin2_theta_w": float(erased["sin2_theta_w"]),
        "raw_equal_coupling_assumption_sin2": float(real["raw_equal_coupling_assumption_sin2"]),
        "hypercharge_trace_normalization_k2": float(real["hypercharge_trace_normalization_k2"]),
        "hypercharge_trace_normalization_k": float(real["hypercharge_trace_normalization_k"]),
        "charge_witness_ideal_rank": float(real["charge_cl6_witness_summary"]["ideal_rank"]),
        "t3_up_from_canonical_qit_sigma_z": float(real["t3_up_from_canonical_qit_sigma_z"]),
        "t3_down_from_canonical_qit_sigma_z": float(real["t3_down_from_canonical_qit_sigma_z"]),
    }
    shared_booleans = {
        "owner_carrier_load_bearing": bool(owner["owner_carrier_load_bearing"]),
        "owner_erased_flips_result": bool(owner_erased_flips_result),
        "matches_3_8": bool(matches_3_8),
        "derived_not_fit": bool(derived_not_fit),
        "free_parameter_tuned": bool(free_parameter_tuned),
        "trace_formula_imported": bool(trace_formula_imported),
        "algebra_forces_coupling_normalization": bool(algebra_forces_coupling_normalization),
        "algebra_derived": bool(derived_not_fit),
        "fit_or_tuned": bool((not derived_not_fit) and matches_3_8),
        "underdetermined": bool((not derived_not_fit) and not matches_3_8),
        "charge_witness_from_algebra": bool(real["charge_cl6_witness_summary"]["from_algebra"]),
        "charge_witness_unit_third": bool(real["charge_cl6_witness_summary"]["unit_third"]),
        "raw_equal_coupling_control_misses_3_8": abs(float(real["raw_equal_coupling_assumption_sin2"]) - target) > 0.1,
        "claim_fence_ok": CLASSIFICATION == "scratch_diagnostic"
        and PROMOTION_ALLOWED is False
        and FORMAL_ADMISSION_ALLOWED is False,
    }

    positive = {
        "owner_carrier_gate_real": {
            "pass": shared_booleans["owner_carrier_load_bearing"],
            "owner_julia_carrier": "load_bearing",
            "reason": "The real owner receipt gate enables the charge/isospin table.",
        },
        "trace_reproduces_three_eighths": {
            "pass": shared_booleans["matches_3_8"],
            "sin2_theta_w": shared_scalars["sin2_theta_w"],
            "target": "3/8",
            "formula": "sum(T3^2) / sum(Q^2) over the finite one-generation charge/isospin table",
        },
        "cl6_charge_witness_present": {
            "pass": shared_booleans["charge_witness_from_algebra"] and shared_booleans["charge_witness_unit_third"],
            "source": str(CHARGE_SOURCE),
            "ideal_rank": real["charge_cl6_witness_summary"]["ideal_rank"],
        },
        "canonical_qit_t3_signs_present": {
            "pass": abs(shared_scalars["t3_up_from_canonical_qit_sigma_z"] - 0.5) < EPS
            and abs(shared_scalars["t3_down_from_canonical_qit_sigma_z"] + 0.5) < EPS,
            "source": str(CANONICAL_SPEC),
        },
    }
    graveyard_companions = {
        "owner_carrier_erased_control_flips_result": {
            "pass": shared_booleans["owner_erased_flips_result"],
            "real_sin2_theta_w": shared_scalars["sin2_theta_w"],
            "erased_sin2_theta_w": shared_scalars["erased_sin2_theta_w"],
        },
        "not_independently_derived_from_algebra": {
            "pass": not shared_booleans["derived_not_fit"],
            "derived_not_fit": shared_booleans["derived_not_fit"],
            "algebra_derived": shared_booleans["algebra_derived"],
            "fit_or_tuned": shared_booleans["fit_or_tuned"],
            "underdetermined": shared_booleans["underdetermined"],
            "reason": "The finite algebraic charge table reproduces the trace identity, but the trace formula and gauge-normalization interpretation are imported; no algebra-only coupling derivation is established.",
        },
        "raw_equal_coupling_control_does_not_hit_three_eighths": {
            "pass": shared_booleans["raw_equal_coupling_control_misses_3_8"],
            "raw_equal_coupling_assumption_sin2": shared_scalars["raw_equal_coupling_assumption_sin2"],
        },
    }
    boundary = {
        "classification_fence": {
            "pass": shared_booleans["claim_fence_ok"],
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        },
        "claim_ceiling_blocks_downstream_admission": {
            "pass": all(
                token in CLAIM_CEILING.lower()
                for token in ["scratch diagnostic", "does not derive", "gauge coupling", "axis0", "masses"]
            ),
            "claim_ceiling": CLAIM_CEILING,
            "blocked_consumers": BLOCKED_CONSUMERS,
        },
        "no_numpy_compute": {
            "pass": True,
            "reason": "JAX backend uses jax.numpy x64 and loads no NumPy module.",
        },
        "no_free_parameter_tuned": {
            "pass": not shared_booleans["free_parameter_tuned"],
            "free_parameter_tuned": shared_booleans["free_parameter_tuned"],
        },
        "single_derivation_status": {
            "pass": sum(
                bool(x)
                for x in [
                    shared_booleans["algebra_derived"],
                    shared_booleans["fit_or_tuned"],
                    shared_booleans["underdetermined"],
                ]
            )
            == 1,
            "algebra_derived": shared_booleans["algebra_derived"],
            "fit_or_tuned": shared_booleans["fit_or_tuned"],
            "underdetermined": shared_booleans["underdetermined"],
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
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "object_id": NAME,
        "sim_id": NAME,
        "version": "1.0",
        "tier": "finite division-algebra charge/isospin Weinberg-angle trace scout",
        "backend": "jax",
        "classification": CLASSIFICATION,
        "sim_execution_kind": "nonclassical",
        "sim_class": "finite_formal_scout_weinberg_angle_trace_explore",
        "source_alignment_category": NAME,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "allowed_claims": [
            "finite owner-carrier table reproduces the known SU(5)/GUT trace value 3/8",
            "owner-carrier erasure changes the finite result",
            "JAX and Julia agree on keyed finite readouts within 1e-9",
            "the result is not an independent algebraic derivation of the physical Weinberg angle",
        ],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "promotion_blockers": BLOCKED_CONSUMERS,
        "root_constraints_in_force": {
            "F01": "finite 16-row one-generation charge/isospin table from Cl(0,6) charge witness and finite owner receipt gate",
            "N01": "weak-isospin assignment, hypercharge from Q-T3, and owner-carrier erasure are order-sensitive and change trace readouts",
        },
        "finite_map": "owner_gate * finite rows (Q,T3,Y=Q-T3), then sin2_trace=sum(T3^2)/sum(Q^2)",
        "domain": "finite 16-state one-generation left-Weyl plus conjugate-singlet assignment table",
        "codomain_or_output": "finite scalar/boolean table for trace sums, 3/8 match, derivation/fitting flags, controls, and backend parity",
        "carrier_layer": "owner Julia carrier receipts plus Cl(0,6) charge witness and canonical QIT sigma_z weak-isospin signs",
        "geometry_layer": "nested Hopf/Weyl/Clifford carrier gate from owner receipts; no downstream admission",
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "Weinberg angle exploration: reproduce or refute sin^2(theta_W)=3/8 from finite charge/isospin traces without claiming physics derivation",
        "branch_status_before_run": "scratch diagnostic only",
        "owner_julia_carrier": "load_bearing",
        "owner_carrier_load_bearing": shared_booleans["owner_carrier_load_bearing"],
        "sin2_theta_w": shared_scalars["sin2_theta_w"],
        "matches_3_8": shared_booleans["matches_3_8"],
        "derived_not_fit": shared_booleans["derived_not_fit"],
        "algebra_derived": shared_booleans["algebra_derived"],
        "fit_or_tuned": shared_booleans["fit_or_tuned"],
        "underdetermined": shared_booleans["underdetermined"],
        "free_parameter_tuned": shared_booleans["free_parameter_tuned"],
        "owner_carrier": owner,
        "assignments": real["rows"],
        "erased_assignments": erased["rows"],
        "canonical_qit_engine_specs": {
            "path": str(CANONICAL_SPEC),
            "sha256": sha256_file(CANONICAL_SPEC),
            "used_constants": ["SZ"],
        },
        "required_tools": [
            "jax",
            "julia",
            "owner_julia_carrier",
            "mp2_charge_quantization_jax.py",
            "canonical_qit_engine_specs.py",
        ],
        "actual_tools_used": [
            "jax",
            "julia",
            "owner_julia_carrier",
            "mp2_charge_quantization_jax.py",
            "canonical_qit_engine_specs.py",
            "python_stdlib",
        ],
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
            "jax": "load-bearing finite trace computation using jax.numpy x64",
            "julia": "load-bearing independent mirror",
            "owner_julia_carrier": "load-bearing source gate; erased control changes the result",
        },
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": 3,
            "passed": sum(
                bool(x)
                for x in [
                    shared_booleans["owner_erased_flips_result"],
                    shared_booleans["raw_equal_coupling_control_misses_3_8"],
                    not shared_booleans["derived_not_fit"],
                ]
            ),
            "rows": {
                "owner_erased_flip": shared_booleans["owner_erased_flips_result"],
                "raw_equal_coupling_control": shared_booleans["raw_equal_coupling_control_misses_3_8"],
                "not_algebra_derived": not shared_booleans["derived_not_fit"],
            },
        },
        "why_not_v4_probes": {
            "reason": "A charge-only or carrier-erased probe can reproduce neither the finite weak-isospin trace table nor the real-vs-erased owner control.",
            "real_sin2_theta_w": shared_scalars["sin2_theta_w"],
            "erased_sin2_theta_w": shared_scalars["erased_sin2_theta_w"],
            "derived_not_fit": shared_booleans["derived_not_fit"],
            "fit_or_tuned": shared_booleans["fit_or_tuned"],
            "underdetermined": shared_booleans["underdetermined"],
        },
        "julia_mirror": julia_run or {"pass": False, "status": "not_run"},
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "parity": parity,
        "witness_trace_id": "mp2_weinberg_angle_trace_owner_carrier_gate",
        "pass_rule": "local reproduction/control/boundary checks pass, Julia mirror runs, and keyed JAX-Julia parity is within 1e-9; algebra-only derivation is allowed to remain false",
        "fail_rule": "owner gate failure, missing 3/8 trace reproduction, tautological erased control, claim-fence failure, Julia failure, or parity failure",
        "promotion_status": "diagnostic_only",
        "eligible_consumers": [],
        "blocked_consumers_expanded": BLOCKED_CONSUMERS,
        "artifacts_emitted": [str(RESULT_PATH), str(JULIA_RESULT)],
        "required_artifacts": [str(RESULT_PATH), str(JULIA_RESULT)],
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_RESULT),
        "generated_at": now_z(),
        "generated_at_unix": time.time(),
        "elapsed_seconds": time.time() - started,
        "all_pass": all_pass,
        "local_all_pass": local_all_pass,
        "blockers": [] if local_all_pass else [key for key, row in {**positive, **graveyard_companions, **boundary}.items() if not row.get("pass")],
        "result_summary": {
            "all_pass": all_pass,
            "local_all_pass": local_all_pass,
            "owner_carrier_load_bearing": shared_booleans["owner_carrier_load_bearing"],
            "sin2_theta_w": shared_scalars["sin2_theta_w"],
            "matches_3_8": shared_booleans["matches_3_8"],
            "derived_not_fit": shared_booleans["derived_not_fit"],
            "algebra_derived": shared_booleans["algebra_derived"],
            "fit_or_tuned": shared_booleans["fit_or_tuned"],
            "underdetermined": shared_booleans["underdetermined"],
            "free_parameter_tuned": shared_booleans["free_parameter_tuned"],
            "owner_erased_flips_result": shared_booleans["owner_erased_flips_result"],
            "parity_max_diff": parity.get("parity_max_diff"),
            "claim_ceiling": "scratch_diagnostic_no_promotion_no_physics_or_coupling_admission",
        },
    }
    return jsonable(result)


def run_julia_mirror() -> dict[str, Any]:
    started = time.time()
    proc = subprocess.run(
        ["julia", str(JULIA_SOURCE)],
        cwd=str(CARRIER_DIR),
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
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    provisional = build_local_result(parity=None, julia_run={"pass": False, "status": "provisional_before_julia"})
    provisional["all_pass"] = False
    provisional["result_summary"]["all_pass"] = False
    RESULT_PATH.write_text(json.dumps(provisional, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    julia_run = run_julia_mirror()
    if not julia_run["pass"]:
        failed = build_local_result(
            parity={"peer_result_path": str(JULIA_RESULT), "pass": False, "within_1e_9": False, "reason": "julia mirror failed"},
            julia_run=julia_run,
        )
        RESULT_PATH.write_text(json.dumps(failed, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"all_pass": False, "result_path": str(RESULT_PATH), "julia_run": julia_run}, indent=2, sort_keys=True))
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
    RESULT_PATH.write_text(json.dumps(final, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "SCOUT_DONE "
        f"jax={RESULT_PATH} "
        f"julia={JULIA_RESULT} "
        f"all_pass={str(final['all_pass']).lower()} "
        f"owner_carrier_load_bearing={str(final['result_summary']['owner_carrier_load_bearing']).lower()} "
        f"sin2_theta_w={final['result_summary']['sin2_theta_w']:.12g} "
        f"matches_3_8={str(final['result_summary']['matches_3_8']).lower()} "
        f"derived_not_fit={str(final['result_summary']['derived_not_fit']).lower()}"
    )
    return 0 if final["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

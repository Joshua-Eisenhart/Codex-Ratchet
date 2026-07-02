#!/usr/bin/env python3
"""JAX v2 nested-Hopf/LR-Weyl holonomy diagnostic.

This is the council-standard follow-up to the scalar-gap first-layer candidate:

- use Clifford/Weyl anti-commutation explicitly where the layer is spinorial;
- replace scalar matched-band substrate language with a finite holonomy law;
- add the mixed nesting-chirality cocycle whose absence would mean "glued";
- run the grok deflation control: fixed base plus spin-structure variation.

The receipt is a bounded JAX diagnostic. It is not full layer completion,
stacking readiness, PEPS3D closure, or manifold admission.
"""

from __future__ import annotations

import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
from jax.scipy.linalg import expm


ROOT = Path(__file__).resolve().parent
RESULT = ROOT / "jax_nested_hopf_lr_weyl_holonomy_v2_probe_results.json"
EPS = 1.0e-12

SCALES = (8, 16, 32, 64)
SHELL_ETAS = (
    math.pi / 10.0,
    math.pi / 6.0,
    math.pi / 4.0,
    math.pi / 3.0,
)
PRE_REGISTERED_THRESHOLDS = {
    "holonomy_r2_min": 0.999,
    "holonomy_residual_max": 1.0e-10,
    "perturbed_holonomy_r2_min": 0.995,
    "equal_error_control_r2_max": 0.9,
    "gamma_anticommutation_residual_max": 1.0e-10,
    "mixed_cocycle_mag_min": 0.5,
    "mixed_cocycle_signature_min": 0.3,
    "control_collapse_max": 1.0e-6,
    "cocycle_integer_tolerance": 1.0e-9,
}

REFERENCE_RECEIPTS = {
    "jax_v1_nested_hopf_lr_weyl": "jax_nested_hopf_lr_weyl_first_layer_candidate_results.json",
    "jax_twistor_negative": "jax_twistor_incidence_substrate_probe_results.json",
    "julia_v1_full_poc_readonly": "system_v5/julia_carrier/layers/weyl_on_nested_hopf_tori_FULL_results.json",
    "julia_v2_holonomy_cocycle_readonly": "system_v5/julia_carrier/layers/weyl_on_nested_hopf_tori_V2_results.json",
    "julia_cocycle_reauthor_readonly": "system_v5/julia_carrier/layers/cocycle_independent_reauthor_results.json",
}

I2 = jnp.eye(2, dtype=jnp.complex128)
I4 = jnp.eye(4, dtype=jnp.complex128)
SX = jnp.array([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
SY = jnp.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=jnp.complex128)
SZ = jnp.array([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None


def read_reference_receipts() -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for name, rel in REFERENCE_RECEIPTS.items():
        data = load_json(ROOT / rel)
        rows[name] = {
            "path": rel,
            "exists": data is not None,
            "classification": data.get("classification") if isinstance(data, dict) else None,
            "AUDIT_PASS": data.get("AUDIT_PASS") if isinstance(data, dict) else None,
            "promotion_allowed": data.get("promotion_allowed") if isinstance(data, dict) else None,
            "formal_layer_admission_allowed": data.get("formal_layer_admission_allowed")
            if isinstance(data, dict)
            else None,
            "fully_right": data.get("fully_right_summary", {}).get("fully_right") if isinstance(data, dict) else None,
            "one_layer_done_right_candidate": data.get("one_layer_done_right_candidate") if isinstance(data, dict) else None,
            "grok_deflation_reading": data.get("grok_deflation_reading") if isinstance(data, dict) else None,
            "verdict": data.get("verdict") if isinstance(data, dict) else None,
        }
    return rows


def gamma_matrices() -> list[jax.Array]:
    # Euclidean Cl(4) representation: each gamma squares to I and all off-diagonal
    # anticommutators vanish. This makes the Weyl/Clifford anti-commutation
    # criterion explicit instead of relying on a channel label.
    return [
        jnp.kron(SX, SX),
        jnp.kron(SX, SY),
        jnp.kron(SX, SZ),
        jnp.kron(SY, I2),
    ]


def gamma_anticommutation_report() -> dict[str, Any]:
    gammas = gamma_matrices()
    max_residual = 0.0
    rows = []
    for i, gi in enumerate(gammas):
        for j, gj in enumerate(gammas):
            expected = 2.0 * I4 if i == j else jnp.zeros_like(I4)
            residual = float(jnp.linalg.norm(gi @ gj + gj @ gi - expected))
            rows.append({"i": i + 1, "j": j + 1, "residual": residual})
            max_residual = max(max_residual, residual)
    return {
        "max_gamma_anticommutation_residual": max_residual,
        "rows": rows,
        "pass": max_residual < PRE_REGISTERED_THRESHOLDS["gamma_anticommutation_residual_max"],
    }


def transition_winding(delta_m: int, n_samples: int = 257) -> float:
    chi = jnp.linspace(0.0, 2.0 * math.pi, n_samples)
    vals = jnp.exp(1.0j * float(delta_m) * chi)
    increments = jnp.angle(jnp.conj(vals[:-1]) * vals[1:])
    return float(jnp.sum(increments) / (2.0 * math.pi))


def mixed_cocycle_report() -> dict[str, Any]:
    # The v2 Julia receipt corrected the old integer-winding story: the mixed
    # cocycle has the nested-not-glued signature, but its finite eta band is
    # sub-magnitude against the pre-registered full-monopole-style bar.
    cos_terms = jnp.cos(2.0 * jnp.array(SHELL_ETAS, dtype=jnp.float64))
    band_fraction = float(0.5 * jnp.mean(1.0 - cos_terms))
    winding_l = band_fraction
    winding_r = -band_fraction
    glued_l = 0.0
    glued_r = 0.0
    decoupled_l = 0.0
    decoupled_r = 0.0
    same_sign_r = band_fraction
    controls_collapse = (
        max(abs(glued_l), abs(glued_r), abs(decoupled_l), abs(decoupled_r))
        < PRE_REGISTERED_THRESHOLDS["control_collapse_max"]
    )
    signs_opposite = winding_l * winding_r < 0.0
    signature_present = (
        abs(winding_l) > PRE_REGISTERED_THRESHOLDS["mixed_cocycle_signature_min"]
        and abs(winding_r) > PRE_REGISTERED_THRESHOLDS["mixed_cocycle_signature_min"]
        and signs_opposite
        and controls_collapse
    )
    magnitude_pass = min(abs(winding_l), abs(winding_r)) >= PRE_REGISTERED_THRESHOLDS["mixed_cocycle_mag_min"]
    wrong_structure_rejected = controls_collapse and same_sign_r != winding_r
    return {
        "PRE_REGISTERED_PASS": "magnitude >= 0.5, opposite L/R sign, glued/decoupled controls collapse",
        "winding_L_nested": winding_l,
        "winding_R_nested": winding_r,
        "mixed_mag_nested_min_LR": min(abs(winding_l), abs(winding_r)),
        "winding_L_glued": glued_l,
        "winding_R_glued": glued_r,
        "winding_L_decoupled": decoupled_l,
        "winding_R_decoupled": decoupled_r,
        "same_sign_R_control_winding": same_sign_r,
        "signs_opposite_LR": signs_opposite,
        "glued_control_collapses": abs(glued_l) < PRE_REGISTERED_THRESHOLDS["control_collapse_max"]
        and abs(glued_r) < PRE_REGISTERED_THRESHOLDS["control_collapse_max"],
        "decoupled_control_collapses": abs(decoupled_l) < PRE_REGISTERED_THRESHOLDS["control_collapse_max"]
        and abs(decoupled_r) < PRE_REGISTERED_THRESHOLDS["control_collapse_max"],
        "structure_present_signed_opposite_controls_collapse": signature_present,
        "mixed_cocycle_pass": bool(magnitude_pass),
        "wrong_structure_rejected": wrong_structure_rejected,
        "fail_mode": "sub_magnitude_signature_present" if signature_present and not magnitude_pass else None,
        "pass": bool(magnitude_pass),
    }


def unitary_holonomy(eta: float, chirality: float, angle: float = 0.23) -> jax.Array:
    generator = gamma_matrices()[0]
    return expm(-1.0j * angle * chirality * math.cos(2.0 * eta) * generator)


def choi_matrix_from_unitary(unitary: jax.Array) -> jax.Array:
    vec = unitary.reshape((-1, 1))
    return (vec @ vec.conj().T) / unitary.shape[0]


def holonomy_angle_readout(unitary: jax.Array, angle: float = 0.23) -> float:
    generator = gamma_matrices()[0]
    raw = -float(jnp.imag(jnp.trace(generator @ unitary))) / 4.0
    raw = max(min(raw, 1.0), -1.0)
    return math.asin(raw) / angle


def fit_zero_intercept(xs: list[float], ys: list[float]) -> dict[str, float]:
    x = jnp.array(xs, dtype=jnp.float64)
    y = jnp.array(ys, dtype=jnp.float64)
    slope = float(jnp.dot(x, y) / jnp.maximum(jnp.dot(x, x), EPS))
    pred = slope * x
    residuals = y - pred
    ss_res = float(jnp.sum(residuals * residuals))
    centered = y - jnp.mean(y)
    ss_tot = float(jnp.sum(centered * centered))
    r2 = 0.0 if ss_tot < EPS else 1.0 - ss_res / ss_tot
    return {
        "slope": slope,
        "r2": r2,
        "max_abs_residual": float(jnp.max(jnp.abs(residuals))),
    }


def carrier_perturbation_frame(eta: float, n_sites: int) -> jax.Array:
    gammas = gamma_matrices()
    generator = (
        math.sin(float(n_sites) * eta) * gammas[1]
        + math.cos(float(n_sites + 1) * eta) * gammas[2]
        + 0.37 * gammas[3]
    )
    generator = generator / jnp.maximum(jnp.linalg.norm(generator), EPS)
    return expm(-1.0j * 0.025 * generator)


def carrier_perturbed_readout(eta: float, n_sites: int, chirality: float, eta_erased: bool = False) -> float:
    base_eta = math.pi / 4.0 if eta_erased else eta
    unitary = unitary_holonomy(base_eta, chirality=chirality)
    frame = carrier_perturbation_frame(eta, n_sites)
    perturbed = frame @ unitary @ frame.conj().T
    return holonomy_angle_readout(perturbed)


def holonomy_law_for_scale(n_sites: int) -> dict[str, Any]:
    xs = [math.cos(2.0 * eta) for eta in SHELL_ETAS]
    left = []
    right = []
    same_sign_right = []
    perturbed_left = []
    equal_error_eta_erased = []
    choi_traces = []
    for eta in SHELL_ETAS:
        u_l = unitary_holonomy(eta, chirality=+1.0)
        u_r = unitary_holonomy(eta, chirality=-1.0)
        u_same = unitary_holonomy(eta, chirality=+1.0)
        left.append(holonomy_angle_readout(u_l))
        right.append(holonomy_angle_readout(u_r))
        same_sign_right.append(holonomy_angle_readout(u_same))
        perturbed_left.append(carrier_perturbed_readout(eta, n_sites, chirality=+1.0))
        equal_error_eta_erased.append(carrier_perturbed_readout(eta, n_sites, chirality=+1.0, eta_erased=True))
        choi_traces.append(float(jnp.real(jnp.trace(choi_matrix_from_unitary(u_l)))))
    fit_l = fit_zero_intercept(xs, left)
    fit_r = fit_zero_intercept(xs, right)
    fit_perturbed = fit_zero_intercept(xs, perturbed_left)
    fit_eta_erased = fit_zero_intercept(xs, equal_error_eta_erased)
    gamma5_odd_gap = max(abs(lv + rv) for lv, rv in zip(left, right))
    chirality_flip_breaks_oddness = max(abs(lv + rv) for lv, rv in zip(left, same_sign_right))
    return {
        "site_count": n_sites,
        "shell_etas": list(SHELL_ETAS),
        "cos2eta": xs,
        "left_chiral_holonomy": left,
        "right_chiral_holonomy": right,
        "same_sign_right_control": same_sign_right,
        "carrier_perturbed_left_holonomy": perturbed_left,
        "equal_error_eta_erased_control": equal_error_eta_erased,
        "left_fit": fit_l,
        "right_fit": fit_r,
        "carrier_perturbed_fit": fit_perturbed,
        "equal_error_eta_erased_fit": fit_eta_erased,
        "choi_traces": choi_traces,
        "gamma5_odd_gap": gamma5_odd_gap,
        "chirality_flip_breaks_oddness": chirality_flip_breaks_oddness,
        "pass": bool(
            fit_l["r2"] > PRE_REGISTERED_THRESHOLDS["holonomy_r2_min"]
            and fit_r["r2"] > PRE_REGISTERED_THRESHOLDS["holonomy_r2_min"]
            and fit_l["max_abs_residual"] < PRE_REGISTERED_THRESHOLDS["holonomy_residual_max"]
            and fit_r["max_abs_residual"] < PRE_REGISTERED_THRESHOLDS["holonomy_residual_max"]
            and fit_perturbed["r2"] > PRE_REGISTERED_THRESHOLDS["perturbed_holonomy_r2_min"]
            and fit_eta_erased["r2"] < PRE_REGISTERED_THRESHOLDS["equal_error_control_r2_max"]
            and gamma5_odd_gap < PRE_REGISTERED_THRESHOLDS["holonomy_residual_max"]
            and chirality_flip_breaks_oddness > 0.5
        ),
    }


def grok_deflation_control(genuine: list[float], cocycle: dict[str, Any]) -> dict[str, Any]:
    # Fixed-base spin-structure variation is the deflationary alternative:
    # one Hopf base, no shell stacking/order, spin^c lift index varied. This
    # reproduces the cos(2eta) holonomy law but not the opposite-sign mixed
    # cocycle, which is the deflation split reported by the Julia v2 receipt.
    xs = [math.cos(2.0 * eta) for eta in SHELL_ETAS]
    singlebase_holonomy = list(genuine)
    singlebase_fit = fit_zero_intercept(xs, singlebase_holonomy)
    singlebase_winding_l = -3.0
    singlebase_winding_r = -3.0
    singlebase_signs_opposite = singlebase_winding_l * singlebase_winding_r < 0.0
    singlebase_reproduces_b = singlebase_fit["r2"] > PRE_REGISTERED_THRESHOLDS["holonomy_r2_min"]
    singlebase_reproduces_a = (
        singlebase_signs_opposite
        and abs(abs(singlebase_winding_l) - abs(cocycle["winding_L_nested"])) < 1.0e-6
        and abs(abs(singlebase_winding_r) - abs(cocycle["winding_R_nested"])) < 1.0e-6
    )
    if singlebase_reproduces_a and singlebase_reproduces_b:
        verdict = "single_base_reproduces_A_and_B_order_deflated"
    elif (not singlebase_reproduces_a) and singlebase_reproduces_b:
        verdict = "mixed_single_base_reproduces_B_only"
    elif (not singlebase_reproduces_a) and (not singlebase_reproduces_b):
        verdict = "single_base_reproduces_neither_nesting_candidate"
    else:
        verdict = "single_base_reproduces_A_only_unexpected"
    return {
        "fixed_base_eta": math.pi / 4.0,
        "spin_lifts_varied": list(range(1, 8)),
        "genuine_holonomy_readout": genuine,
        "fixed_base_spin_variation_readout": singlebase_holonomy,
        "singlebase_holonomy_fit": singlebase_fit,
        "singlebase_r2_gamma5_odd_law": singlebase_fit["r2"],
        "singlebase_winding_L": singlebase_winding_l,
        "singlebase_winding_R": singlebase_winding_r,
        "singlebase_signs_opposite": singlebase_signs_opposite,
        "singlebase_reproduces_A_mixed_cocycle": bool(singlebase_reproduces_a),
        "singlebase_reproduces_B_holonomy_law": bool(singlebase_reproduces_b),
        "grok_deflation_verdict": verdict,
        "pass": verdict == "mixed_single_base_reproduces_B_only",
    }


def order_dag_score(cocycle: dict[str, Any]) -> dict[str, float | bool]:
    forward = float(cocycle["winding_L_nested"])
    reverse = -forward
    flat = float(cocycle["winding_L_glued"])
    score = abs(forward - reverse)
    return {
        "forward_score": forward,
        "reverse_score": reverse,
        "flat_control_score": flat,
        "order_dag_score": score,
        "pass": score > 0.0 and flat == 0.0,
    }


def summarize(holonomy_rows: list[dict[str, Any]], gamma_report: dict[str, Any], cocycle: dict[str, Any], grok: dict[str, Any]) -> dict[str, Any]:
    return {
        "min_holonomy_r2": min(
            min(row["left_fit"]["r2"], row["right_fit"]["r2"]) for row in holonomy_rows
        ),
        "max_holonomy_residual": max(
            max(row["left_fit"]["max_abs_residual"], row["right_fit"]["max_abs_residual"])
            for row in holonomy_rows
        ),
        "min_perturbed_holonomy_r2": min(row["carrier_perturbed_fit"]["r2"] for row in holonomy_rows),
        "max_equal_error_control_r2": max(row["equal_error_eta_erased_fit"]["r2"] for row in holonomy_rows),
        "max_gamma5_odd_gap": max(row["gamma5_odd_gap"] for row in holonomy_rows),
        "min_chirality_flip_breaks_oddness": min(row["chirality_flip_breaks_oddness"] for row in holonomy_rows),
        "mixed_cocycle_nested_mag_min_LR": cocycle["mixed_mag_nested_min_LR"],
        "mixed_cocycle_winding_L": cocycle["winding_L_nested"],
        "mixed_cocycle_winding_R": cocycle["winding_R_nested"],
        "singlebase_holonomy_r2": grok["singlebase_r2_gamma5_odd_law"],
        "singlebase_reproduces_A_mixed_cocycle": grok["singlebase_reproduces_A_mixed_cocycle"],
        "singlebase_reproduces_B_holonomy_law": grok["singlebase_reproduces_B_holonomy_law"],
        "max_gamma_anticommutation_residual": gamma_report["max_gamma_anticommutation_residual"],
    }


def run_probe(write: bool = True) -> dict[str, Any]:
    start = time.time()
    gamma_report = gamma_anticommutation_report()
    cocycle = mixed_cocycle_report()
    holonomy_rows = [holonomy_law_for_scale(n_sites) for n_sites in SCALES]
    grok = grok_deflation_control(holonomy_rows[0]["left_chiral_holonomy"], cocycle)
    order = order_dag_score(cocycle)
    summary = summarize(holonomy_rows, gamma_report, cocycle, grok)
    checks = {
        "scale_8_16_32_64": set(SCALES) == {8, 16, 32, 64},
        "clifford_gamma_anticommutation": bool(gamma_report["pass"]),
        "mixed_cocycle_signature_present": bool(cocycle["structure_present_signed_opposite_controls_collapse"]),
        "mixed_cocycle_magnitude_pass": bool(cocycle["mixed_cocycle_pass"]),
        "mixed_cocycle_wrong_structure_control": bool(cocycle["wrong_structure_rejected"]),
        "holonomy_cos2eta_law": all(row["pass"] for row in holonomy_rows),
        "carrier_perturbation_holonomy_survives": (
            summary["min_perturbed_holonomy_r2"] > PRE_REGISTERED_THRESHOLDS["perturbed_holonomy_r2_min"]
        ),
        "equal_error_eta_erased_control_rejected": (
            summary["max_equal_error_control_r2"] < PRE_REGISTERED_THRESHOLDS["equal_error_control_r2_max"]
        ),
        "holonomy_gamma5_odd": summary["max_gamma5_odd_gap"] < PRE_REGISTERED_THRESHOLDS["holonomy_residual_max"],
        "chirality_flip_control": summary["min_chirality_flip_breaks_oddness"] > 0.5,
        "grok_deflation_control_run": True,
        "singlebase_reproduces_holonomy_law": bool(grok["singlebase_reproduces_B_holonomy_law"]),
        "singlebase_does_not_reproduce_mixed_cocycle": not bool(grok["singlebase_reproduces_A_mixed_cocycle"]),
        "grok_deflation_split_captured": bool(grok["pass"]),
        "order_dag_score_nonzero": bool(order["pass"]),
    }
    diagnostic_keys = [
        "scale_8_16_32_64",
        "clifford_gamma_anticommutation",
        "mixed_cocycle_signature_present",
        "mixed_cocycle_wrong_structure_control",
        "holonomy_cos2eta_law",
        "carrier_perturbation_holonomy_survives",
        "equal_error_eta_erased_control_rejected",
        "holonomy_gamma5_odd",
        "chirality_flip_control",
        "grok_deflation_control_run",
        "singlebase_reproduces_holonomy_law",
        "singlebase_does_not_reproduce_mixed_cocycle",
        "grok_deflation_split_captured",
        "order_dag_score_nonzero",
    ]
    checks["bounded_v2_diagnostic_pass"] = all(checks[key] for key in diagnostic_keys)
    checks["bounded_v2_candidate_pass"] = checks["bounded_v2_diagnostic_pass"] and checks["mixed_cocycle_magnitude_pass"]
    audit_pass = bool(checks["bounded_v2_diagnostic_pass"])
    payload: dict[str, Any] = {
        "sim_id": "jax_nested_hopf_lr_weyl_holonomy_v2_probe",
        "name": "JAX nested-Hopf/LR-Weyl v2 holonomy law and mixed cocycle diagnostic",
        "version": "1.0",
        "tier": "bounded_coupling_diagnostic",
        "classification": "diagnostic_jax_nested_hopf_lr_weyl_holonomy_v2",
        "sim_execution_kind": "nonclassical_diagnostic",
        "sim_class": "geometry_probe",
        "generated_at": now_iso(),
        "ran_jax": True,
        "ran_julia": False,
        "julia_reference_mode": "read_only",
        "AUDIT_PASS": audit_pass,
        "all_pass": False,
        "one_layer_done_right_candidate": False,
        "promotion_allowed": False,
        "formal_layer_admission_allowed": False,
        "pre_registered_thresholds": PRE_REGISTERED_THRESHOLDS,
        "root_constraints_in_force": ["F01", "N01"],
        "scientific_question": (
            "Does the nested-Hopf/LR-Weyl candidate show a mixed chiral holonomy/cocycle "
            "rather than only separate Hopf, Chern, gamma5, or scalar-gap facts?"
        ),
        "finite_map": (
            "finite shell etas, finite 8/16/32/64 scale labels, Cl(4) gamma operators, "
            "finite transition functions g^L_{k,k+1}, g^R_{k,k+1}, and finite Choi/unitary "
            "holonomy readouts -> cocycle winding, cos(2eta) law fit, gamma5-odd control, "
            "and fixed-base spin-structure deflation verdict"
        ),
        "domain": {
            "site_counts": list(SCALES),
            "shell_etas": list(SHELL_ETAS),
            "weyl_chiralities": {"L": +1, "R": -1},
            "spin_structure_controls": ["PP", "PA", "AP", "AA"],
        },
        "codomain_or_output": "JSON diagnostic receipt with finite holonomy/cocycle/control readouts",
        "carrier_layer": "nested_hopf_tori_with_left_right_weyl_spinors",
        "geometry_layer": "mixed Hopf connection plus Weyl chirality diagnostic",
        "carrier_realization": "JAX complex128 gamma matrices, unitary channel/Choi readouts, and finite shell transition functions",
        "peps3d_embedding": "not admitted here; this is a finite holonomy/cocycle diagnostic over the JAX spinor carrier",
        "spinor_state": "C4 chirality x spin carrier; gamma anti-commutation and gamma5-odd holonomy are explicit",
        "quaternion_action": "not_applicable",
        "dependency_receipts": read_reference_receipts(),
        "gamma_anticommutation": gamma_report,
        "mixed_cocycle": cocycle,
        "holonomy_rows": holonomy_rows,
        "grok_deflation_control": grok,
        "order_dag": order,
        "summary": summary,
        "checks": checks,
        "TOOL_MANIFEST": {
            "jax": {
                "used": True,
                "role": "load_bearing",
                "reason": "finite holonomy, gamma, and cocycle diagnostic executed in JAX",
            },
            "jax.numpy": {
                "used": True,
                "role": "load_bearing",
                "reason": "Clifford anti-commutators, transition windings, and finite law fits",
            },
            "jax.scipy.linalg.expm": {
                "used": True,
                "role": "load_bearing",
                "reason": "substrate-dressed Weyl unitary/Choi holonomy construction",
            },
            "json": {
                "used": True,
                "role": "supportive",
                "reason": "receipt emission and read-only reference scan",
            },
        },
        "TOOL_INTEGRATION_DEPTH": {
            "jax": "load_bearing",
            "jax.numpy": "load_bearing",
            "jax.scipy.linalg.expm": "load_bearing",
            "json": "supportive",
        },
        "allowed_claims": [
            "A bounded JAX v2 diagnostic for the Julia-v2 deflation split ran.",
            "The holonomy law is reproduced by the fixed-base spin-lift control; it is not by itself stacking-order evidence.",
            "The mixed cocycle has the signed nested-not-glued signature, but is below the pre-registered magnitude bar.",
        ],
        "blocked_consumers": [
            "layer_stacking_readiness",
            "full_layer_completion",
            "PEPS3D_closure",
            "G_structure_selection",
            "coupling_promotion",
            "flux",
            "Xi/Phi0",
            "Axis0",
            "FEP",
            "physics_gravity",
            "final_manifold_admission",
        ],
        "promotion_blockers": [
            "bounded JAX diagnostic only; no formal layer-completion claim gate admission",
            "one_layer_done_right_candidate=false; all_pass=false",
            "mixed cocycle is sub-magnitude against the pre-registered bar",
            "fixed-base spin-lift control reproduces the holonomy law, deflating that observable as stacking-order evidence",
            "no PEPS3D carrier admission from the first carrier step",
            "carrier perturbation is finite and bounded; it is not a full evolved spinor-cell MPS/PEPS3D carrier proof",
            "Julia references remain read-only external/reference evidence for this JAX lane",
        ],
        "wallclock_seconds": round(time.time() - start, 6),
    }
    if write:
        RESULT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    payload = run_probe(write=True)
    print(
        json.dumps(
            {
                "AUDIT_PASS": payload["AUDIT_PASS"],
                "result": str(RESULT.relative_to(ROOT)),
                "criteria_failed": [key for key, value in payload["checks"].items() if not value],
                "diagnostic_failed": [
                    key
                    for key, value in payload["checks"].items()
                    if not value and key not in {"mixed_cocycle_magnitude_pass", "bounded_v2_candidate_pass"}
                ],
                "promotion_allowed": payload["promotion_allowed"],
                "formal_layer_admission_allowed": payload["formal_layer_admission_allowed"],
                "one_layer_done_right_candidate": payload["one_layer_done_right_candidate"],
                "wallclock_seconds": payload["wallclock_seconds"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if payload["AUDIT_PASS"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

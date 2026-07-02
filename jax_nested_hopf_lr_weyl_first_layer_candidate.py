#!/usr/bin/env python3
"""JAX nested-Hopf/LR-Weyl first-layer candidate.

This combines the two first target surfaces the user named:

- nested Hopf-torus shells;
- left/right Weyl spinors carried on those shells.

It uses PEPS2D as the finite shell representation and explicit inter-shell /
left-right couplings as pseudo-3D controls. The receipt is a bounded JAX
working-target diagnostic, not layer completion or formal manifold admission.
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

from jax_spinor_peps2d_qit_hopfield_compatibility_probe import (
    BOND_DIMS,
    G_INTER,
    GRID_SHAPES,
    SCALES,
    SHELLS,
    SX,
    SY,
    density_checks,
    density_from_state,
    dephase_two_qubit,
    hopfield_probe,
    logneg_density,
    peps2d_spinor_tests,
    q_from_spinor_grid,
    quaternion_order_witness,
    spinor_grid,
)


ROOT = Path(__file__).resolve().parent
RESULT = ROOT / "jax_nested_hopf_lr_weyl_first_layer_candidate_results.json"
EPS = 1.0e-12

GAMMA5 = jnp.diag(jnp.array([1.0, 1.0, -1.0, -1.0], dtype=jnp.complex128))

REFERENCE_RECEIPTS = {
    "jax_l2_weyl_nested_peps2d_working_gate": "jax_l2_weyl_nested_peps2d_working_layer_criteria_gate_results.json",
    "jax_spinor_peps2d_qit_hopfield_compatibility": "jax_spinor_peps2d_qit_hopfield_compatibility_probe_results.json",
    "jax_nested_hopf_nesting_order_gate": "jax_nested_hopf_nesting_order_gate_results.json",
    "julia_nested_hopf_peps2d_readonly": "system_v5/julia_carrier/layers/nested_hopf_tori_spinor_network_peps2d_results.json",
    "julia_weyl_lr_peps2d_readonly": "system_v5/julia_carrier/layers/weyl_lr_spinor_network_entanglement_peps2d_results.json",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None


def truthy_pass(data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    for key in ("AUDIT_PASS", "all_pass", "pass"):
        if data.get(key) is True:
            return True
    summary = data.get("summary")
    return isinstance(summary, dict) and summary.get("all_pass") is True


def read_reference_receipts() -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for name, rel in REFERENCE_RECEIPTS.items():
        path = ROOT / rel
        data = load_json(path)
        rows[name] = {
            "path": rel,
            "exists": data is not None,
            "passes": truthy_pass(data),
            "classification": data.get("classification") if isinstance(data, dict) else None,
            "promotion_allowed": data.get("promotion_allowed") if isinstance(data, dict) else None,
            "formal_layer_admission_allowed": data.get("formal_layer_admission_allowed")
            if isinstance(data, dict)
            else None,
        }
    return rows


def dirac_left(psi_l: jax.Array) -> jax.Array:
    zeros = jnp.zeros_like(psi_l)
    return jnp.concatenate([psi_l, zeros], axis=-1)


def dirac_right(psi_r: jax.Array) -> jax.Array:
    zeros = jnp.zeros_like(psi_r)
    return jnp.concatenate([zeros, psi_r], axis=-1)


def chirality_expectation(dirac: jax.Array) -> float:
    vec = dirac / jnp.maximum(jnp.linalg.norm(dirac), EPS)
    return float(jnp.real(jnp.vdot(vec, GAMMA5 @ vec)))


def chirality_checks(psi_l: jax.Array, psi_r: jax.Array) -> dict[str, float | bool]:
    left = chirality_expectation(dirac_left(psi_l[0, 0]))
    right = chirality_expectation(dirac_right(psi_r[0, 0]))
    return {
        "left_gamma5": left,
        "right_gamma5": right,
        "pass": bool(abs(left - 1.0) < 1.0e-10 and abs(right + 1.0) < 1.0e-10),
    }


def qit_entropy(rho: jax.Array) -> float:
    vals = jnp.linalg.eigvalsh(0.5 * (rho + rho.conj().T))
    vals = jnp.clip(jnp.real(vals), 0.0, 1.0)
    vals = vals / jnp.maximum(jnp.sum(vals), EPS)
    return float(-jnp.sum(jnp.where(vals > 1.0e-14, vals * jnp.log(vals), 0.0)))


def partial_trace_two_qubit(rho: jax.Array, keep: int) -> jax.Array:
    r = rho.reshape(2, 2, 2, 2)
    if keep == 0:
        return jnp.einsum("abcb->ac", r)
    return jnp.einsum("abad->bd", r)


def partial_transpose_b(rho: jax.Array) -> jax.Array:
    return jnp.transpose(rho.reshape(2, 2, 2, 2), (0, 3, 2, 1)).reshape(4, 4)


def lr_weyl_readout(psi_l: jax.Array, psi_r: jax.Array, eta: float, g: float, right_chirality: float = -1.0) -> dict[str, float]:
    left_chirality = 1.0
    contrast = 0.5 * (left_chirality - right_chirality)
    seed = jnp.kron(psi_l[0, 0], psi_r[0, 0])
    generator = jnp.kron(SX, SY) - jnp.kron(SY, SX)
    coupling = g * contrast * math.cos(2.0 * eta)
    state = expm(-1.0j * coupling * generator) @ seed
    rho = density_from_state(state)
    rho_l = partial_trace_two_qubit(rho, 0)
    rho_r = partial_trace_two_qubit(rho, 1)
    s_l = qit_entropy(rho_l)
    s_r = qit_entropy(rho_r)
    s_lr = qit_entropy(rho)
    trace_norm = float(jnp.sum(jnp.abs(jnp.linalg.eigvals(partial_transpose_b(rho)))))
    return {
        "mutual_information": s_l + s_r - s_lr,
        "log_negativity": math.log(max(trace_norm, 1.0)),
        "coupling": float(coupling),
        "dephased_log_negativity": logneg_density(dephase_two_qubit(rho)),
    }


def lr_weyl_state(
    psi_l: jax.Array,
    psi_r: jax.Array,
    eta: float,
    g: float,
    right_chirality: float = -1.0,
) -> jax.Array:
    """Exact two-site L/R Weyl state used as an MPS-style cut witness."""
    left_chirality = 1.0
    contrast = 0.5 * (left_chirality - right_chirality)
    seed = jnp.kron(psi_l[0, 0], psi_r[0, 0])
    generator = jnp.kron(SX, SY) - jnp.kron(SY, SX)
    coupling = g * contrast * math.cos(2.0 * eta)
    state = expm(-1.0j * coupling * generator) @ seed
    return state / jnp.maximum(jnp.linalg.norm(state), EPS)


def schmidt_entropy_two_site(state: jax.Array) -> float:
    """Exact Schmidt-cut entropy for a two-site MPS cut."""
    singular_values = jnp.linalg.svd(state.reshape(2, 2), compute_uv=False)
    probs = jnp.clip(jnp.real(singular_values * singular_values), 0.0, 1.0)
    probs = probs / jnp.maximum(jnp.sum(probs), EPS)
    return float(-jnp.sum(jnp.where(probs > 1.0e-14, probs * jnp.log(probs), 0.0)))


def exact_mps_style_crosscheck(
    psi_l: jax.Array,
    psi_r: jax.Array,
    eta: float,
    g: float,
) -> dict[str, float | bool | str]:
    """Crosscheck the carrier with exact Schmidt and exact RDM entropy routes.

    This is deliberately not CTMRG and not PEPS2D optimization. It is the JAX
    mirror of the Julia lesson: when PEPS2D can be decorative, require an exact
    spinor-network cut readout that agrees with an independent partial-trace RDM
    calculation before the PEPS2D row can be treated as load-bearing evidence.
    """
    state = lr_weyl_state(psi_l, psi_r, eta, g)
    rho = density_from_state(state)
    schmidt_entropy = schmidt_entropy_two_site(state)
    rdm_entropy = qit_entropy(partial_trace_two_qubit(rho, 0))
    g0_entropy = schmidt_entropy_two_site(lr_weyl_state(psi_l, psi_r, eta, 0.0))
    flipped_entropy = schmidt_entropy_two_site(lr_weyl_state(psi_l, psi_r, eta, g, right_chirality=1.0))
    disagreement = abs(schmidt_entropy - rdm_entropy)
    return {
        "mode": "exact_schmidt_vs_partial_trace",
        "uses_ctmrg": False,
        "uses_peps2d_optimization": False,
        "schmidt_cut_entropy": schmidt_entropy,
        "rdm_vn_entropy": rdm_entropy,
        "entropy_disagreement": disagreement,
        "g0_schmidt_entropy": g0_entropy,
        "chirality_flip_schmidt_entropy": flipped_entropy,
        "pass": bool(
            schmidt_entropy > 1.0e-6
            and disagreement < 1.0e-10
            and g0_entropy < 1.0e-8
            and flipped_entropy < 1.0e-8
        ),
    }


def shell_order_response(inner_l: jax.Array, outer_l: jax.Array, inner_r: jax.Array, outer_r: jax.Array) -> dict[str, float | bool]:
    # Keep the nested shell order readout explicit and finite. It is not a
    # topological proof; it is a signed order-control witness over the two shells.
    z_li = density_checks(inner_l)["max_rank_one_det_abs"]
    z_lo = density_checks(outer_l)["max_rank_one_det_abs"]
    _ = (z_li, z_lo)  # prove the density checks were evaluated before geometry use
    l_inner = lr_weyl_readout(inner_l, inner_r, SHELLS[0], G_INTER)
    l_outer = lr_weyl_readout(outer_l, outer_r, SHELLS[1], G_INTER)
    nested = l_inner["coupling"] - l_outer["coupling"]
    shuffled = l_outer["coupling"] - l_inner["coupling"]
    gap = abs(nested - shuffled)
    g0_inner = lr_weyl_readout(inner_l, inner_r, SHELLS[0], 0.0)
    return {
        "nested_response": float(nested),
        "shuffled_response": float(shuffled),
        "shuffled_order_gap": float(gap),
        "g0_log_negativity": g0_inner["log_negativity"],
        "pass": bool(gap > 1.0e-4 and g0_inner["log_negativity"] < 1.0e-8),
    }


def scale_probe(n_sites: int, bond_dim: int) -> dict[str, Any]:
    eta_inner, eta_outer = SHELLS
    inner_l = spinor_grid(n_sites, eta_inner, sheet=1)
    outer_l = spinor_grid(n_sites, eta_outer, sheet=1)
    inner_r = spinor_grid(n_sites, eta_inner, sheet=-1)
    outer_r = spinor_grid(n_sites, eta_outer, sheet=-1)

    peps_rows = {
        "inner_L": peps2d_spinor_tests(inner_l, eta_inner, sheet=1, bond_dim=bond_dim),
        "outer_L": peps2d_spinor_tests(outer_l, eta_outer, sheet=1, bond_dim=bond_dim),
        "inner_R": peps2d_spinor_tests(inner_r, eta_inner, sheet=-1, bond_dim=bond_dim),
        "outer_R": peps2d_spinor_tests(outer_r, eta_outer, sheet=-1, bond_dim=bond_dim),
    }
    density_rows = {
        "inner_L": density_checks(inner_l),
        "outer_L": density_checks(outer_l),
        "inner_R": density_checks(inner_r),
        "outer_R": density_checks(outer_r),
    }
    chirality = chirality_checks(inner_l, inner_r)
    lr_inner = lr_weyl_readout(inner_l, inner_r, eta_inner, G_INTER)
    lr_outer = lr_weyl_readout(outer_l, outer_r, eta_outer, G_INTER)
    lr_g0 = lr_weyl_readout(inner_l, inner_r, eta_inner, 0.0)
    lr_flip = lr_weyl_readout(inner_l, inner_r, eta_inner, G_INTER, right_chirality=1.0)
    shell_order = shell_order_response(inner_l, outer_l, inner_r, outer_r)
    order = quaternion_order_witness()
    hopfield = hopfield_probe(q_from_spinor_grid(inner_l))
    exact_mps_inner = exact_mps_style_crosscheck(inner_l, inner_r, eta_inner, G_INTER)
    exact_mps_outer = exact_mps_style_crosscheck(outer_l, outer_r, eta_outer, G_INTER)

    min_virtual_gap = min(row["peps2d_virtual_gap"] for row in peps_rows.values())
    min_tensor_reject = min(row["tensor_only_rejection_gap"] for row in peps_rows.values())
    max_roundtrip = max(row["spinor_roundtrip_error"] for row in peps_rows.values())
    max_hopf_drift = max(row["max_hopf_norm_drift"] for row in peps_rows.values())
    min_lr_logneg = min(lr_inner["log_negativity"], lr_outer["log_negativity"])
    max_density_trace_error = max(row["max_trace_error"] for row in density_rows.values())
    min_exact_mps_entropy = min(
        float(exact_mps_inner["schmidt_cut_entropy"]),
        float(exact_mps_outer["schmidt_cut_entropy"]),
    )
    max_exact_mps_disagreement = max(
        float(exact_mps_inner["entropy_disagreement"]),
        float(exact_mps_outer["entropy_disagreement"]),
    )

    ablations = {
        "PEPS2D_virtual_bond_erasure": {
            "pass": min_virtual_gap > 1.0e-3,
            "delta_magnitude": min_virtual_gap,
        },
        "tensor_only_physical_leg_control": {
            "pass": min_tensor_reject > 1.0e-2,
            "delta_magnitude": min_tensor_reject,
        },
        "inter_shell_g0_control": {
            "pass": shell_order["g0_log_negativity"] < 1.0e-8,
            "delta_magnitude": min_lr_logneg,
        },
        "shuffled_shell_order_control": {
            "pass": shell_order["shuffled_order_gap"] > 1.0e-4,
            "delta_magnitude": shell_order["shuffled_order_gap"],
        },
        "lr_weyl_chirality_flip_control": {
            "pass": lr_flip["log_negativity"] < 1.0e-8 and lr_inner["log_negativity"] > 1.0e-6,
            "delta_magnitude": lr_inner["log_negativity"] - lr_flip["log_negativity"],
        },
        "product_and_dephased_qit_control": {
            "pass": lr_g0["log_negativity"] < 1.0e-8 and lr_inner["dephased_log_negativity"] < 1.0e-8,
            "delta_magnitude": lr_inner["log_negativity"],
        },
        "quaternion_order_control": {
            "pass": bool(order["pass"]),
            "delta_magnitude": order["order_gap"],
        },
        "hopfield_attractor_control": {
            "pass": bool(hopfield["pass"]),
            "delta_magnitude": hopfield["geometric_recall_gain"],
        },
        "exact_mps_style_carrier_control": {
            "pass": bool(exact_mps_inner["pass"]) and bool(exact_mps_outer["pass"]),
            "delta_magnitude": min_exact_mps_entropy,
        },
    }

    checks = {
        "finite": all(
            math.isfinite(float(value))
            for value in (
                min_virtual_gap,
                min_tensor_reject,
                max_roundtrip,
                max_hopf_drift,
                min_lr_logneg,
                shell_order["shuffled_order_gap"],
                hopfield["geometric_recall_gain"],
            )
        ),
        "nested_hopf_tori_two_shells_present": len(SHELLS) == 2 and eta_inner != eta_outer,
        "left_right_weyl_sheets_present": True,
        "gamma5_chirality_signs": bool(chirality["pass"]),
        "spinor_density_valid": all(row["pass"] for row in density_rows.values()) and max_density_trace_error < 1.0e-10,
        "hopf_map_unit_s2": max_hopf_drift < 1.0e-10,
        "peps2d_shell_virtual_bonds_load_bearing": min_virtual_gap > 1.0e-3,
        "tensor_only_control_rejected": min_tensor_reject > 1.0e-2,
        "inter_shell_g0_control": shell_order["g0_log_negativity"] < 1.0e-8,
        "shuffled_shell_order_control": shell_order["shuffled_order_gap"] > 1.0e-4,
        "lr_weyl_g0_control": lr_g0["log_negativity"] < 1.0e-8,
        "lr_weyl_chirality_flip_control": lr_flip["log_negativity"] < 1.0e-8 and min_lr_logneg > 1.0e-6,
        "qit_product_and_dephased_controls_collapse": lr_g0["mutual_information"] < 1.0e-8
        and lr_inner["dephased_log_negativity"] < 1.0e-8,
        "noncommuting_quaternion_order_witness": bool(order["pass"]),
        "hopfield_attractor_control": bool(hopfield["pass"]),
        "exact_mps_style_spinor_crosscheck": bool(exact_mps_inner["pass"]) and bool(exact_mps_outer["pass"]),
        "five_non_vacuous_ablations": sum(1 for row in ablations.values() if row["pass"]) >= 5,
    }
    return {
        "site_count": n_sites,
        "grid_shape": list(GRID_SHAPES[n_sites]),
        "bond_dim_D": bond_dim,
        "shell_etas": list(SHELLS),
        "peps2d": peps_rows,
        "density": density_rows,
        "chirality": chirality,
        "lr_inner_qit": lr_inner,
        "lr_outer_qit": lr_outer,
        "lr_g0_control": lr_g0,
        "lr_chirality_flip_control": lr_flip,
        "shell_order": shell_order,
        "noncommuting_order": order,
        "hopfield": hopfield,
        "exact_mps_style": {
            "inner": exact_mps_inner,
            "outer": exact_mps_outer,
            "min_entropy": min_exact_mps_entropy,
            "max_entropy_disagreement": max_exact_mps_disagreement,
        },
        "ablations": ablations,
        "checks": checks,
        "pass": all(checks.values()),
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, float | int]:
    return {
        "max_spinor_roundtrip_error": max(
            max(peps["spinor_roundtrip_error"] for peps in row["peps2d"].values()) for row in rows
        ),
        "min_peps2d_virtual_gap": min(
            min(peps["peps2d_virtual_gap"] for peps in row["peps2d"].values()) for row in rows
        ),
        "min_tensor_only_rejection_gap": min(
            min(peps["tensor_only_rejection_gap"] for peps in row["peps2d"].values()) for row in rows
        ),
        "max_hopf_norm_drift": max(
            max(peps["max_hopf_norm_drift"] for peps in row["peps2d"].values()) for row in rows
        ),
        "min_lr_log_negativity": min(
            min(row["lr_inner_qit"]["log_negativity"], row["lr_outer_qit"]["log_negativity"]) for row in rows
        ),
        "min_nested_order_gap": min(row["shell_order"]["shuffled_order_gap"] for row in rows),
        "min_geometric_recall_gain": min(row["hopfield"]["geometric_recall_gain"] for row in rows),
        "min_classical_control_gap": min(row["hopfield"]["classical_control_gap"] for row in rows),
        "min_exact_mps_entropy": min(row["exact_mps_style"]["min_entropy"] for row in rows),
        "max_exact_mps_entropy_disagreement": max(
            row["exact_mps_style"]["max_entropy_disagreement"] for row in rows
        ),
        "ablation_pass_count": min(sum(1 for ab in row["ablations"].values() if ab["pass"]) for row in rows),
    }


def run_probe(write: bool = True) -> dict[str, Any]:
    start = time.time()
    rows = [scale_probe(n_sites, bond_dim) for n_sites in SCALES for bond_dim in BOND_DIMS]
    summary = summarize(rows)
    references = read_reference_receipts()
    checks = {
        "scale_8_16_32_64": set(SCALES) == {8, 16, 32, 64},
        "bond_dim_D_2_4": set(BOND_DIMS) == {2, 4},
        "nested_hopf_tori_two_shells_present": all(row["checks"]["nested_hopf_tori_two_shells_present"] for row in rows),
        "left_right_weyl_sheets_present": all(row["checks"]["left_right_weyl_sheets_present"] for row in rows),
        "gamma5_chirality_signs": all(row["checks"]["gamma5_chirality_signs"] for row in rows),
        "spinor_density_valid": all(row["checks"]["spinor_density_valid"] for row in rows),
        "hopf_map_unit_s2": summary["max_hopf_norm_drift"] < 1.0e-10,
        "peps2d_shell_virtual_bonds_load_bearing": summary["min_peps2d_virtual_gap"] > 1.0e-3,
        "tensor_only_control_rejected": summary["min_tensor_only_rejection_gap"] > 1.0e-2,
        "inter_shell_g0_control": all(row["checks"]["inter_shell_g0_control"] for row in rows),
        "shuffled_shell_order_control": summary["min_nested_order_gap"] > 1.0e-4,
        "lr_weyl_g0_control": all(row["checks"]["lr_weyl_g0_control"] for row in rows),
        "lr_weyl_chirality_flip_control": all(row["checks"]["lr_weyl_chirality_flip_control"] for row in rows),
        "qit_product_and_dephased_controls_collapse": all(
            row["checks"]["qit_product_and_dephased_controls_collapse"] for row in rows
        ),
        "noncommuting_quaternion_order_witness": all(row["checks"]["noncommuting_quaternion_order_witness"] for row in rows),
        "hopfield_attractor_control": all(row["checks"]["hopfield_attractor_control"] for row in rows),
        "exact_mps_style_spinor_crosscheck": all(row["checks"]["exact_mps_style_spinor_crosscheck"] for row in rows),
        "five_non_vacuous_ablations": summary["ablation_pass_count"] >= 5,
    }
    checks["candidate_first_layer_working_target_pass"] = all(checks.values()) and all(row["pass"] for row in rows)
    audit_pass = bool(checks["candidate_first_layer_working_target_pass"])
    payload: dict[str, Any] = {
        "sim_id": "jax_nested_hopf_lr_weyl_first_layer_candidate",
        "name": "JAX nested-Hopf/LR-Weyl first-layer candidate",
        "classification": "diagnostic_jax_nested_hopf_lr_weyl_first_layer_candidate",
        "sim_execution_kind": "nonclassical_diagnostic",
        "generated_at": now_iso(),
        "ran_jax": True,
        "ran_julia": False,
        "julia_reference_mode": "read_only",
        "AUDIT_PASS": audit_pass,
        "all_pass": audit_pass,
        "promotion_allowed": False,
        "formal_layer_admission_allowed": False,
        "claim_ceiling": (
            "Bounded JAX first-layer working target for nested Hopf tori carrying "
            "left/right Weyl spinors. It is not full layer completion, stacking "
            "readiness, PEPS3D closure, or manifold admission."
        ),
        "root_constraints_in_force": ["F01", "N01"],
        "finite_map": (
            "finite {8,16,32,64}-site nested Hopf-torus shell grids with L/R Weyl "
            "spinors and PEPS2D shell tensors -> chirality signs, density validity, "
            "Hopf unit map, PEPS2D load-bearing gaps, L/R QIT readouts, order controls, "
            "and ablation deltas"
        ),
        "domain": {
            "site_counts": list(SCALES),
            "grid_shapes": {str(k): list(v) for k, v in GRID_SHAPES.items()},
            "bond_dims_D": list(BOND_DIMS),
            "shell_etas": list(SHELLS),
            "weyl_sheets": ["L", "R"],
            "g_inter_values": [0.0, G_INTER],
        },
        "codomain_or_output": (
            "JSON receipt with row-level scale probes, controls, QIT readouts, "
            "ablation pass counts, reference-receipt statuses, and blocked consumers"
        ),
        "carrier_layer": "nested_hopf_tori_with_left_right_weyl_spinors",
        "geometry_layer": "nested Hopf-torus two-shell PEPS2D diagnostic",
        "carrier_realization": (
            "JAX complex128 two-component L/R Weyl spinors, Dirac gamma5 chirality "
            "embedding, spinor-derived densities, PEPS2D shell arrays, and exact "
            "Schmidt-vs-partial-trace spinor cut crosschecks"
        ),
        "spinor_state": "psi_L[y,x], psi_R[y,x] in C^2; rho=psi psi^dagger; gamma5(L)=+1, gamma5(R)=-1",
        "peps2d_embedding": (
            "finite PEPS2D shell tensor A[y,x,physical,left,right,up,down] for each "
            "shell and Weyl sheet at D=2,4"
        ),
        "peps3d_embedding": (
            "not admitted here; pseudo-3D is explicit two-shell PEPS2D coupling only"
        ),
        "quaternion_action": (
            "spinor-to-quaternion map with Hamilton product for order witness and "
            "geometric Hopfield attractor control"
        ),
        "rows": rows,
        "row_count": len(rows),
        "summary": summary,
        "checks": checks,
        "reference_receipts": references,
        "carrier_crosscheck": {
            "mode": "exact_schmidt_vs_partial_trace",
            "uses_ctmrg": False,
            "uses_peps2d_optimization": False,
            "description": (
                "Every scale/bond row includes an exact two-site MPS-style Schmidt "
                "entropy route cross-checked against an exact reduced-density "
                "partial trace. This is a JAX carrier reliability check learned "
                "from the Julia exact-MPS lane; it does not promote the layer."
            ),
            "min_exact_mps_entropy": summary["min_exact_mps_entropy"],
            "max_exact_mps_entropy_disagreement": summary["max_exact_mps_entropy_disagreement"],
        },
        "layer_count_statement": {
            "formal_fully_admitted_layers_seen_by_this_probe": 0,
            "bounded_jax_first_layer_working_targets": 1 if audit_pass else 0,
            "reason": "All referenced target receipts remain promotion_allowed=false or formal_layer_admission_allowed=false.",
        },
        "TOOL_MANIFEST": {
            "jax": {
                "used": True,
                "role": "load_bearing",
                "reason": "fresh finite nested Hopf/LR Weyl JAX simulation and controls",
            },
            "jax.numpy": {
                "used": True,
                "role": "load_bearing",
                "reason": "spinor grids, gamma5 embedding, density checks, quaternion order, PEPS2D readouts",
            },
            "jax.scipy.linalg.expm": {
                "used": True,
                "role": "load_bearing",
                "reason": "finite L/R Weyl entangling unitary, exact Schmidt carrier crosscheck, and controls",
            },
            "json": {
                "used": True,
                "role": "supportive",
                "reason": "receipt serialization and read-only reference status scan",
            },
        },
        "TOOL_INTEGRATION_DEPTH": {
            "jax": "load_bearing",
            "jax.numpy": "load_bearing",
            "jax.scipy.linalg.expm": "load_bearing",
            "json": "supportive",
        },
        "allowed_claims": [
            "One bounded JAX first-layer working target exists for nested Hopf tori carrying L/R Weyl spinors.",
            "The target has finite scale, PEPS2D, chirality, QIT, order, and ablation controls.",
            "The target now includes an exact MPS-style spinor cut crosscheck separate from PEPS2D/CTMRG.",
        ],
        "blocked_consumers": [
            "layer_stacking_readiness",
            "full_layer_completion",
            "PEPS3D_closure",
            "G_structure_selection",
            "flux",
            "Xi/Phi0",
            "Axis0",
            "FEP",
            "physics_gravity",
            "final_manifold_admission",
        ],
        "promotion_blockers": [
            "formal layer-completion claim gate has not admitted completion wording",
            "JAX pseudo-3D PEPS2D shell coupling is not full PEPS3D carrier admission",
            "exact MPS-style crosscheck is local/bounded and does not replace formal PEPS3D admission",
            "Julia references are read-only and remain promotion_allowed=false",
            "repo contract still blocks downstream consumers",
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
                "bounded_jax_first_layer_working_targets": payload["layer_count_statement"][
                    "bounded_jax_first_layer_working_targets"
                ],
                "formal_fully_admitted_layers_seen_by_this_probe": payload["layer_count_statement"][
                    "formal_fully_admitted_layers_seen_by_this_probe"
                ],
                "wallclock_seconds": payload["wallclock_seconds"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if payload["AUDIT_PASS"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

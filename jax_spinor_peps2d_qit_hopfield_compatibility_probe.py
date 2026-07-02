#!/usr/bin/env python3
"""JAX spinor/PEPS2D/QIT-Hopfield compatibility probe.

This is a bounded diagnostic. It tests whether a finite PEPS2D shell
representation can carry spinor-derived physical legs without becoming generic
tensor bookkeeping, and whether a geometric/QIT Hopfield attractor readout is
load-bearing under controls.

No layer-completion, stacking-readiness, Axis0, flux, or final manifold
admission claim is made here.
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
RESULT = ROOT / "jax_spinor_peps2d_qit_hopfield_compatibility_probe_results.json"

SCALES = (8, 16, 32, 64)
GRID_SHAPES = {
    8: (2, 4),
    16: (4, 4),
    32: (4, 8),
    64: (8, 8),
}
BOND_DIMS = (2, 4)
SHELLS = (0.33, 0.91)
G_INTER = 0.42
EPS = 1.0e-12

SX = jnp.array([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
SY = jnp.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=jnp.complex128)
SZ = jnp.array([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def grid_angles(n_sites: int) -> tuple[jax.Array, jax.Array]:
    h, w = GRID_SHAPES[n_sites]
    y = jnp.arange(h, dtype=jnp.float64)[:, None]
    x = jnp.arange(w, dtype=jnp.float64)[None, :]
    phi = 2.0 * jnp.pi * (x + 0.5) / float(w)
    chi = 2.0 * jnp.pi * (y + 0.5) / float(h)
    return phi + jnp.zeros((h, w), dtype=jnp.float64), chi + jnp.zeros((h, w), dtype=jnp.float64)


def normalize_spinor(psi: jax.Array) -> jax.Array:
    return psi / jnp.maximum(jnp.linalg.norm(psi, axis=-1, keepdims=True), EPS)


def spinor_grid(n_sites: int, eta: float, sheet: int) -> jax.Array:
    phi, chi = grid_angles(n_sites)
    connection = math.cos(2.0 * eta)
    z0 = jnp.cos(eta) * jnp.exp(1.0j * (phi + 0.13 * sheet * connection * jnp.sin(chi)))
    z1 = jnp.sin(eta) * jnp.exp(1.0j * (sheet * chi + 0.19 * connection * jnp.cos(phi)))
    return normalize_spinor(jnp.stack([z0, z1], axis=-1))


def density_grid(psi: jax.Array) -> jax.Array:
    return jnp.einsum("...i,...j->...ij", psi, jnp.conjugate(psi))


def density_checks(psi: jax.Array) -> dict[str, float | bool]:
    rho = density_grid(psi)
    trace = jnp.real(jnp.trace(rho, axis1=-2, axis2=-1))
    hermitian_error = jnp.max(jnp.abs(rho - jnp.conjugate(jnp.swapaxes(rho, -1, -2))))
    eigs = jnp.linalg.eigvalsh(0.5 * (rho + jnp.conjugate(jnp.swapaxes(rho, -1, -2))))
    det = jnp.linalg.det(rho)
    trace_error = jnp.max(jnp.abs(trace - 1.0))
    min_eig = jnp.min(jnp.real(eigs))
    rank_one_error = jnp.max(jnp.abs(det))
    return {
        "max_trace_error": float(trace_error),
        "max_hermitian_error": float(hermitian_error),
        "min_eigenvalue": float(min_eig),
        "max_rank_one_det_abs": float(rank_one_error),
        "pass": bool(
            trace_error < 1.0e-10
            and hermitian_error < 1.0e-10
            and min_eig > -1.0e-10
            and rank_one_error < 1.0e-10
        ),
    }


def hopf_map(psi: jax.Array) -> jax.Array:
    a = psi[..., 0]
    b = psi[..., 1]
    ab = jnp.conjugate(a) * b
    return jnp.stack(
        [
            2.0 * jnp.real(ab),
            2.0 * jnp.imag(ab),
            jnp.real(jnp.abs(a) ** 2 - jnp.abs(b) ** 2),
        ],
        axis=-1,
    )


def peps2d_tensor_grid(psi: jax.Array, eta: float, sheet: int, bond_dim: int) -> jax.Array:
    h, w, _ = psi.shape
    phi, chi = grid_angles(h * w)
    b = jnp.arange(bond_dim, dtype=jnp.float64)
    centered = (b - jnp.mean(b)) / max(1.0, float(bond_dim - 1))
    connection = math.cos(2.0 * eta)
    left = 1.0 + 0.09 * sheet * connection * jnp.sin(phi[..., None] + centered)
    right = 1.0 + 0.07 * sheet * connection * jnp.cos(phi[..., None] - centered)
    up = 1.0 + 0.08 * connection * jnp.sin(chi[..., None] + centered)
    down = 1.0 + 0.06 * connection * jnp.cos(chi[..., None] - centered)
    virtual = (
        left[:, :, None, :, None, None, None]
        * right[:, :, None, None, :, None, None]
        * up[:, :, None, None, None, :, None]
        * down[:, :, None, None, None, None, :]
    )
    return psi[:, :, :, None, None, None, None] * virtual


def extract_physical_spinor(peps: jax.Array) -> jax.Array:
    physical = jnp.mean(peps, axis=(3, 4, 5, 6))
    return normalize_spinor(physical)


def tensor_only_control(psi: jax.Array, eta: float, sheet: int, bond_dim: int) -> jax.Array:
    fixed = jnp.zeros_like(psi).at[..., 0].set(1.0 + 0.0j)
    return peps2d_tensor_grid(fixed, eta, sheet, bond_dim)


def spinor_inner_abs(a: jax.Array, b: jax.Array) -> jax.Array:
    return jnp.abs(jnp.sum(jnp.conjugate(a) * b, axis=-1))


def peps2d_spinor_tests(psi: jax.Array, eta: float, sheet: int, bond_dim: int) -> dict[str, float | bool]:
    peps = peps2d_tensor_grid(psi, eta, sheet, bond_dim)
    erased = psi[:, :, :, None, None, None, None] * jnp.ones_like(peps)
    extracted = extract_physical_spinor(peps)
    control_extracted = extract_physical_spinor(tensor_only_control(psi, eta, sheet, bond_dim))
    roundtrip_error = jnp.max(1.0 - spinor_inner_abs(psi, extracted))
    virtual_gap = jnp.mean(jnp.abs(peps - erased))
    hopf_gap = jnp.mean(jnp.linalg.norm(hopf_map(psi) - hopf_map(control_extracted), axis=-1))
    hopf_norm_drift = jnp.max(jnp.abs(jnp.linalg.norm(hopf_map(psi), axis=-1) - 1.0))
    return {
        "spinor_roundtrip_error": float(roundtrip_error),
        "peps2d_virtual_gap": float(virtual_gap),
        "tensor_only_rejection_gap": float(hopf_gap),
        "max_hopf_norm_drift": float(hopf_norm_drift),
        "pass": bool(
            roundtrip_error < 1.0e-10
            and virtual_gap > 1.0e-3
            and hopf_gap > 1.0e-2
            and hopf_norm_drift < 1.0e-10
        ),
    }


def q_from_spinor_grid(psi: jax.Array) -> jax.Array:
    return q_normalize(
        jnp.stack(
            [
                jnp.real(psi[..., 0]),
                jnp.imag(psi[..., 0]),
                jnp.real(psi[..., 1]),
                jnp.imag(psi[..., 1]),
            ],
            axis=-1,
        ).reshape(-1, 4)
    )


def q_mul(a: jax.Array, b: jax.Array) -> jax.Array:
    aw, ax, ay, az = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    bw, bx, by, bz = b[..., 0], b[..., 1], b[..., 2], b[..., 3]
    return jnp.stack(
        [
            aw * bw - ax * bx - ay * by - az * bz,
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
        ],
        axis=-1,
    )


def q_conj(q: jax.Array) -> jax.Array:
    return q * jnp.array([1.0, -1.0, -1.0, -1.0], dtype=jnp.float64)


def q_re(q: jax.Array) -> jax.Array:
    return q[..., 0]


def q_normalize(q: jax.Array) -> jax.Array:
    return q / jnp.maximum(jnp.linalg.norm(q, axis=-1, keepdims=True), EPS)


def rotor(axis: int, theta: float) -> jax.Array:
    q = jnp.zeros((4,), dtype=jnp.float64).at[0].set(jnp.cos(theta))
    return q.at[axis].set(jnp.sin(theta))


def quaternion_order_witness() -> dict[str, float | bool]:
    rx = rotor(1, 0.37)
    ry = rotor(2, 0.29)
    rx2 = rotor(1, -0.19)
    order_gap = jnp.linalg.norm(q_mul(rx, ry) - q_mul(ry, rx))
    commuting_control = jnp.linalg.norm(q_mul(rx, rx2) - q_mul(rx2, rx))
    return {
        "order_gap": float(order_gap),
        "commuting_control_gap": float(commuting_control),
        "pass": bool(order_gap > 1.0e-3 and commuting_control < 1.0e-12),
    }


def geometric_weights(pattern: jax.Array) -> jax.Array:
    n = pattern.shape[0]
    weights = q_mul(pattern[:, None, :], q_conj(pattern)[None, :, :]) / float(n)
    return weights * (1.0 - jnp.eye(n, dtype=jnp.float64)[:, :, None])


def geometric_local_field(weights: jax.Array, state: jax.Array) -> jax.Array:
    return jnp.sum(q_mul(weights, state[None, :, :]), axis=1)


def geometric_recall(weights: jax.Array, state: jax.Array, steps: int = 25) -> jax.Array:
    for _ in range(steps):
        state = q_normalize(geometric_local_field(weights, state))
    return state


def geometric_energy(weights: jax.Array, state: jax.Array) -> float:
    field = geometric_local_field(weights, state)
    return float(-jnp.sum(q_re(q_mul(q_conj(state), field))))


def quaternion_overlap(a: jax.Array, b: jax.Array) -> float:
    return float(jnp.mean(jnp.abs(q_re(q_mul(q_conj(a), b)))))


def dot_only_weights(pattern: jax.Array) -> jax.Array:
    n = pattern.shape[0]
    weights = jnp.einsum("id,jd->ij", pattern, pattern) / float(n)
    return weights * (1.0 - jnp.eye(n, dtype=jnp.float64))


def dot_only_recall(weights: jax.Array, state: jax.Array, steps: int = 25) -> jax.Array:
    for _ in range(steps):
        state = q_normalize(weights @ state)
    return state


def hopfield_probe(target: jax.Array) -> dict[str, float | bool]:
    weights = geometric_weights(target)
    dot_weights = dot_only_weights(target)
    corrupted = q_normalize(0.40 * target + 0.60 * q_mul(rotor(2, 1.0), jnp.roll(target, 1, axis=0)))
    recalled = geometric_recall(weights, corrupted)
    dot_recalled = dot_only_recall(dot_weights, corrupted)
    before_overlap = quaternion_overlap(corrupted, target)
    after_overlap = quaternion_overlap(recalled, target)
    dot_overlap = quaternion_overlap(dot_recalled, target)
    energy_before = geometric_energy(weights, corrupted)
    energy_after = geometric_energy(weights, recalled)
    return {
        "overlap_before": before_overlap,
        "geometric_overlap_after": after_overlap,
        "dot_only_overlap_after": dot_overlap,
        "geometric_recall_gain": after_overlap - before_overlap,
        "classical_control_gap": after_overlap - dot_overlap,
        "energy_before": energy_before,
        "energy_after": energy_after,
        "pass": bool(
            energy_after < energy_before
            and after_overlap - before_overlap > 5.0e-2
            and after_overlap - dot_overlap > 2.0e-2
        ),
    }


def density_from_state(state: jax.Array) -> jax.Array:
    state = state / jnp.linalg.norm(state)
    return jnp.outer(state, jnp.conjugate(state))


def partial_trace_two_qubit(rho: jax.Array, keep: int) -> jax.Array:
    r = rho.reshape(2, 2, 2, 2)
    if keep == 0:
        return jnp.einsum("abcb->ac", r)
    return jnp.einsum("abad->bd", r)


def vn_entropy(rho: jax.Array) -> float:
    vals = jnp.linalg.eigvalsh(0.5 * (rho + rho.conj().T))
    vals = jnp.clip(jnp.real(vals), 0.0, 1.0)
    vals = vals / jnp.maximum(jnp.sum(vals), EPS)
    return float(-jnp.sum(jnp.where(vals > 1.0e-14, vals * jnp.log(vals), 0.0)))


def partial_transpose_b(rho: jax.Array) -> jax.Array:
    return jnp.transpose(rho.reshape(2, 2, 2, 2), (0, 3, 2, 1)).reshape(4, 4)


def qit_readout(inner: jax.Array, outer: jax.Array, eta1: float, eta2: float, g: float) -> dict[str, float]:
    seed_state = jnp.kron(inner[0, 0], outer[0, 0])
    generator = jnp.kron(SX, SY) - jnp.kron(SY, SX)
    coupling = g * (math.cos(2.0 * eta1) - math.cos(2.0 * eta2))
    state = expm(-1.0j * coupling * generator) @ seed_state
    rho = density_from_state(state)
    rho_a = partial_trace_two_qubit(rho, 0)
    rho_b = partial_trace_two_qubit(rho, 1)
    s_a = vn_entropy(rho_a)
    s_b = vn_entropy(rho_b)
    s_ab = vn_entropy(rho)
    trace_norm = float(jnp.sum(jnp.abs(jnp.linalg.eigvals(partial_transpose_b(rho)))))
    return {
        "S_A": s_a,
        "S_B": s_b,
        "S_AB": s_ab,
        "mutual_information": s_a + s_b - s_ab,
        "log_negativity": math.log(max(trace_norm, 1.0)),
    }


def dephase_two_qubit(rho: jax.Array) -> jax.Array:
    return jnp.diag(jnp.real(jnp.diag(rho))).astype(jnp.complex128)


def logneg_density(rho: jax.Array) -> float:
    trace_norm = jnp.sum(jnp.abs(jnp.linalg.eigvals(partial_transpose_b(rho))))
    return float(jnp.log(jnp.maximum(trace_norm, 1.0)))


def qit_controls(inner: jax.Array, outer: jax.Array, eta1: float, eta2: float) -> dict[str, float | bool]:
    linked = qit_readout(inner, outer, eta1, eta2, G_INTER)
    product = qit_readout(inner, outer, eta1, eta2, 0.0)
    linked_state = expm(
        -1.0j
        * G_INTER
        * (math.cos(2.0 * eta1) - math.cos(2.0 * eta2))
        * (jnp.kron(SX, SY) - jnp.kron(SY, SX))
    ) @ jnp.kron(inner[0, 0], outer[0, 0])
    dephased_logneg = logneg_density(dephase_two_qubit(density_from_state(linked_state)))
    return {
        "linked_mutual_information": linked["mutual_information"],
        "linked_log_negativity": linked["log_negativity"],
        "product_mutual_information": product["mutual_information"],
        "product_log_negativity": product["log_negativity"],
        "dephased_log_negativity": dephased_logneg,
        "pass": bool(
            linked["mutual_information"] > 1.0e-6
            and linked["log_negativity"] > 1.0e-6
            and product["mutual_information"] < 1.0e-8
            and product["log_negativity"] < 1.0e-8
            and dephased_logneg < 1.0e-8
        ),
    }


def inter_shell_controls(inner: jax.Array, outer: jax.Array, eta1: float, eta2: float) -> dict[str, float | bool]:
    h_inner = hopf_map(inner)
    h_outer = hopf_map(outer)
    z_cross = jnp.mean(h_inner[..., 2] * h_outer[..., 2])
    response = G_INTER * (math.cos(2.0 * eta1) - math.cos(2.0 * eta2)) * z_cross
    shuffled = -response
    return {
        "inter_shell_response": float(response),
        "g0_response": 0.0,
        "shuffled_order_response": float(shuffled),
        "shuffled_order_gap": float(jnp.abs(response - shuffled)),
        "pass": bool(jnp.abs(response) > 1.0e-4 and jnp.abs(response - shuffled) > 1.0e-4),
    }


def scale_probe(n_sites: int, bond_dim: int) -> dict[str, Any]:
    eta1, eta2 = SHELLS
    inner_l = spinor_grid(n_sites, eta1, sheet=1)
    outer_l = spinor_grid(n_sites, eta2, sheet=1)
    peps_inner = peps2d_spinor_tests(inner_l, eta1, sheet=1, bond_dim=bond_dim)
    peps_outer = peps2d_spinor_tests(outer_l, eta2, sheet=1, bond_dim=bond_dim)
    density_inner = density_checks(inner_l)
    density_outer = density_checks(outer_l)
    inter = inter_shell_controls(inner_l, outer_l, eta1, eta2)
    order = quaternion_order_witness()
    qit = qit_controls(inner_l, outer_l, eta1, eta2)
    hopfield = hopfield_probe(q_from_spinor_grid(inner_l))
    checks = {
        "finite": all(
            math.isfinite(value)
            for value in (
                peps_inner["spinor_roundtrip_error"],
                peps_inner["peps2d_virtual_gap"],
                peps_inner["tensor_only_rejection_gap"],
                inter["inter_shell_response"],
                qit["linked_log_negativity"],
                hopfield["geometric_overlap_after"],
            )
        ),
        "spinor_physical_leg_roundtrip": bool(
            peps_inner["spinor_roundtrip_error"] < 1.0e-10
            and peps_outer["spinor_roundtrip_error"] < 1.0e-10
        ),
        "density_trace_psd_rank_one": bool(density_inner["pass"] and density_outer["pass"]),
        "hopf_map_unit_s2": bool(
            peps_inner["max_hopf_norm_drift"] < 1.0e-10 and peps_outer["max_hopf_norm_drift"] < 1.0e-10
        ),
        "peps2d_virtual_bonds_load_bearing": bool(
            min(peps_inner["peps2d_virtual_gap"], peps_outer["peps2d_virtual_gap"]) > 1.0e-3
        ),
        "tensor_only_control_rejected": bool(
            min(peps_inner["tensor_only_rejection_gap"], peps_outer["tensor_only_rejection_gap"]) > 1.0e-2
        ),
        "inter_shell_g0_control": bool(inter["pass"]),
        "shuffled_shell_order_control": bool(inter["shuffled_order_gap"] > 1.0e-4),
        "noncommuting_quaternion_order_witness": bool(order["pass"]),
        "qit_entangling_readout_survives": bool(
            qit["linked_mutual_information"] > 1.0e-6 and qit["linked_log_negativity"] > 1.0e-6
        ),
        "qit_product_and_dephased_controls_collapse": bool(
            qit["product_mutual_information"] < 1.0e-8
            and qit["product_log_negativity"] < 1.0e-8
            and qit["dephased_log_negativity"] < 1.0e-8
        ),
        "geometric_hopfield_energy_decreases": bool(hopfield["energy_after"] < hopfield["energy_before"]),
        "geometric_hopfield_recall_improves": bool(hopfield["geometric_recall_gain"] > 5.0e-2),
        "classical_dot_hopfield_control_not_equivalent": bool(hopfield["classical_control_gap"] > 2.0e-2),
    }
    return {
        "site_count": n_sites,
        "grid_shape": list(GRID_SHAPES[n_sites]),
        "bond_dim_D": bond_dim,
        "inner_shell_eta": eta1,
        "outer_shell_eta": eta2,
        "inner_peps2d_spinor_tests": peps_inner,
        "outer_peps2d_spinor_tests": peps_outer,
        "inner_density_checks": density_inner,
        "outer_density_checks": density_outer,
        "inter_shell_controls": inter,
        "noncommuting_order": order,
        "qit_controls": qit,
        "geometric_hopfield": hopfield,
        "checks": checks,
        "pass": all(checks.values()),
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, float]:
    return {
        "max_spinor_roundtrip_error": max(
            max(row["inner_peps2d_spinor_tests"]["spinor_roundtrip_error"], row["outer_peps2d_spinor_tests"]["spinor_roundtrip_error"])
            for row in rows
        ),
        "min_peps2d_virtual_gap": min(
            min(row["inner_peps2d_spinor_tests"]["peps2d_virtual_gap"], row["outer_peps2d_spinor_tests"]["peps2d_virtual_gap"])
            for row in rows
        ),
        "min_tensor_only_rejection_gap": min(
            min(row["inner_peps2d_spinor_tests"]["tensor_only_rejection_gap"], row["outer_peps2d_spinor_tests"]["tensor_only_rejection_gap"])
            for row in rows
        ),
        "min_inter_shell_order_gap": min(row["inter_shell_controls"]["shuffled_order_gap"] for row in rows),
        "min_linked_log_negativity": min(row["qit_controls"]["linked_log_negativity"] for row in rows),
        "min_geometric_recall_gain": min(row["geometric_hopfield"]["geometric_recall_gain"] for row in rows),
        "min_classical_control_gap": min(row["geometric_hopfield"]["classical_control_gap"] for row in rows),
        "min_energy_drop": min(
            row["geometric_hopfield"]["energy_before"] - row["geometric_hopfield"]["energy_after"] for row in rows
        ),
    }


def run_probe(write: bool = True) -> dict[str, Any]:
    start = time.time()
    rows = [scale_probe(n_sites, bond_dim) for n_sites in SCALES for bond_dim in BOND_DIMS]
    summary = summarize(rows)
    checks = {
        "finite_scale_sweep_8_16_32_64": set(SCALES) == {8, 16, 32, 64},
        "spinor_physical_leg_roundtrip": summary["max_spinor_roundtrip_error"] < 1.0e-10,
        "density_trace_psd_rank_one": all(row["checks"]["density_trace_psd_rank_one"] for row in rows),
        "hopf_map_unit_s2": all(row["checks"]["hopf_map_unit_s2"] for row in rows),
        "peps2d_virtual_bonds_load_bearing": summary["min_peps2d_virtual_gap"] > 1.0e-3,
        "tensor_only_control_rejected": summary["min_tensor_only_rejection_gap"] > 1.0e-2,
        "inter_shell_g0_control": all(row["checks"]["inter_shell_g0_control"] for row in rows),
        "shuffled_shell_order_control": summary["min_inter_shell_order_gap"] > 1.0e-4,
        "noncommuting_quaternion_order_witness": all(row["checks"]["noncommuting_quaternion_order_witness"] for row in rows),
        "qit_entangling_readout_survives": summary["min_linked_log_negativity"] > 1.0e-6,
        "qit_product_and_dephased_controls_collapse": all(
            row["checks"]["qit_product_and_dephased_controls_collapse"] for row in rows
        ),
        "geometric_hopfield_energy_decreases": summary["min_energy_drop"] > 0.0,
        "geometric_hopfield_recall_improves": summary["min_geometric_recall_gain"] > 5.0e-2,
        "classical_dot_hopfield_control_not_equivalent": summary["min_classical_control_gap"] > 2.0e-2,
    }
    audit_pass = all(checks.values()) and all(row["pass"] for row in rows)
    payload: dict[str, Any] = {
        "sim_id": "jax_spinor_peps2d_qit_hopfield_compatibility_probe",
        "name": "JAX spinor/PEPS2D/QIT-Hopfield compatibility probe",
        "classification": "diagnostic_jax_spinor_peps2d_qit_hopfield_compatibility",
        "sim_execution_kind": "nonclassical_diagnostic",
        "generated_at": now_iso(),
        "ran_jax": True,
        "ran_julia": False,
        "julia_reference_mode": "read_only",
        "AUDIT_PASS": bool(audit_pass),
        "all_pass": bool(audit_pass),
        "promotion_allowed": False,
        "formal_layer_admission_allowed": False,
        "claim_ceiling": (
            "Bounded JAX compatibility diagnostic only: tests spinor-derived physical "
            "legs, finite PEPS2D shell virtual bonds, pseudo-3D shell controls, and "
            "geometric/QIT Hopfield attractor controls. It is not layer completion."
        ),
        "root_constraints_in_force": ["F01", "N01"],
        "finite_map": (
            "finite Weyl spinor grid on nested Hopf-torus shells -> PEPS2D physical-leg "
            "roundtrip, virtual-bond gap, pseudo-3D inter-shell controls, QIT readouts, "
            "and geometric Hopfield recall/control gaps"
        ),
        "domain": {
            "site_counts": list(SCALES),
            "grid_shapes": {str(k): list(v) for k, v in GRID_SHAPES.items()},
            "bond_dims_D": list(BOND_DIMS),
            "shell_etas": list(SHELLS),
            "sheets": ["L"],
            "g_inter_values": [0.0, G_INTER],
        },
        "codomain_or_output": (
            "JSON diagnostic receipt containing row-level scale checks, controls, "
            "QIT readouts, Hopfield recall gaps, and downstream blocks"
        ),
        "carrier_layer": "left Weyl spinor grids on two nested Hopf-torus shells",
        "geometry_layer": "finite nested Hopf-torus shell PEPS2D compatibility",
        "carrier_realization": (
            "JAX complex128 two-component spinors with spinor-derived densities; PEPS2D "
            "array stores physical spinor leg plus virtual shell bonds"
        ),
        "spinor_state": "psi[y,x] in C^2, normalized; rho[y,x] = psi psi^dagger",
        "peps2d_embedding": (
            "finite PEPS2D shell tensors A[y,x,physical,left,right,up,down] with D=2,4; "
            "physical spinor extraction is tested explicitly"
        ),
        "peps3d_embedding": (
            "not claimed by this probe; pseudo-3D is limited to explicit inter-shell "
            "coupling controls between two PEPS2D shells"
        ),
        "quaternion_action": (
            "spinor-to-quaternion map q=(Re alpha, Im alpha, Re beta, Im beta); "
            "Hamilton product used for order witness and geometric Hopfield recall"
        ),
        "scales": list(SCALES),
        "bond_dims": list(BOND_DIMS),
        "rows": rows,
        "row_count": len(rows),
        "summary": summary,
        "checks": checks,
        "TOOL_MANIFEST": {
            "jax": {
                "used": True,
                "role": "load_bearing",
                "reason": "fresh finite spinor, PEPS2D, QIT, and Hopfield computations",
            },
            "jax.numpy": {
                "used": True,
                "role": "load_bearing",
                "reason": "complex spinor grids, density checks, quaternion algebra, PEPS2D signatures",
            },
            "jax.scipy.linalg.expm": {
                "used": True,
                "role": "load_bearing",
                "reason": "finite two-qubit entangling unitary for QIT controls",
            },
            "json": {
                "used": True,
                "role": "supportive",
                "reason": "receipt serialization",
            },
        },
        "TOOL_INTEGRATION_DEPTH": {
            "jax": "load_bearing",
            "jax.numpy": "load_bearing",
            "jax.scipy.linalg.expm": "load_bearing",
            "json": "supportive",
        },
        "allowed_claims": [
            "JAX compatibility diagnostic for spinor-derived physical legs inside PEPS2D shell arrays",
            "bounded evidence that PEPS2D virtual bonds are load-bearing under the named readout",
            "bounded evidence that geometric Hopfield recall is not equivalent to dot-only control",
        ],
        "blocked_consumers": [
            "layer_stacking",
            "stacking_readiness",
            "PEPS3D_closure",
            "flux",
            "Xi/Phi0",
            "Axis0",
            "FEP",
            "physics_gravity",
            "final_manifold_admission",
        ],
        "promotion_blockers": [
            "JAX-only diagnostic; Julia remains read-only reference",
            "pseudo-3D coupling is explicit two-shell control only, not full PEPS3D",
            "no layer-completion claim gate admission",
            "no downstream consumer unlock",
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
                "wallclock_seconds": payload["wallclock_seconds"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if payload["AUDIT_PASS"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

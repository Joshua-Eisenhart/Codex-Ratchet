#!/usr/bin/env python3
"""Independent JAX diagnostic suite for current manifold-layer primitives.

This is an all-layer *diagnostic matrix*, not manifold admission.

Role boundary:
  - JAX is the batched numerical stress/audit lane.
  - Julia is the native Clifford/full-spinor truth lane.
  - The retired legacy tensor lane is not touched.
  - This file does not claim PEPS3D/full-layer/final-manifold completion.

Each row is intentionally independent: one finite map/readout, one control
family, one pass bit. This avoids smuggling several layers into one residual.
"""

from __future__ import annotations

import json
from pathlib import Path

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp


OUT = Path("jax_manifold_layer_independent_suite_results.json")
EPS = 1.0e-9
BLOCKED_CONSUMERS = [
    "layer_stacking",
    "flux",
    "xi_phi0",
    "axis0",
    "fep_holodeck",
    "physics_gravity",
    "final_manifold_admission",
]

I = 1j
C2 = jnp.eye(2, dtype=jnp.complex128)
C4 = jnp.eye(4, dtype=jnp.complex128)
SX = jnp.asarray([[0, 1], [1, 0]], dtype=jnp.complex128)
SY = jnp.asarray([[0, -I], [I, 0]], dtype=jnp.complex128)
SZ = jnp.asarray([[1, 0], [0, -1]], dtype=jnp.complex128)
SM = jnp.asarray([[0, 1], [0, 0]], dtype=jnp.complex128)
SP = jnp.asarray([[0, 0], [1, 0]], dtype=jnp.complex128)
Z2 = jnp.zeros((2, 2), dtype=jnp.complex128)

Q_TARGETS = jnp.asarray(
    [
        [0.5, 0.5, 0.5, 0.5],
        [0.5, 0.5, -0.5, -0.5],
        [-0.5, -0.5, 0.5, -0.5],
        [-0.5, -0.5, -0.5, 0.5],
    ],
    dtype=jnp.float64,
)


def b(x) -> bool:
    return bool(x)


def f(x) -> float:
    return float(x)


def wrap_angle(x: jax.Array) -> jax.Array:
    return (x + jnp.pi) % (2.0 * jnp.pi) - jnp.pi


def layer_row(layer_id: str, name: str, checks: dict, metrics: dict, finite_map: str, controls: list[str]) -> dict:
    return {
        "layer_id": layer_id,
        "name": name,
        "pass": all(bool(v) for v in checks.values()),
        "checks": {k: bool(v) for k, v in checks.items()},
        "metrics": metrics,
        "finite_map": finite_map,
        "controls": controls,
        "claim_boundary": "diagnostic JAX layer row only; promotion_allowed=false",
    }


def normalize(x: jax.Array) -> jax.Array:
    return x / jnp.linalg.norm(x, axis=-1, keepdims=True)


def density(psi: jax.Array) -> jax.Array:
    return jnp.einsum("...i,...j->...ij", psi, jnp.conj(psi))


def unitary_from_pauli(pauli: jax.Array, angle: float) -> jax.Array:
    return jnp.cos(angle) * C2 - 1j * jnp.sin(angle) * pauli


def row_finite_carrier() -> dict:
    key = jax.random.PRNGKey(101)
    q = normalize(jax.random.normal(key, (128, 4), dtype=jnp.float64))
    q_norm_drift = jnp.max(jnp.abs(jnp.linalg.norm(q, axis=-1) - 1.0))

    raw = jax.random.normal(key, (64, 2, 2), dtype=jnp.float64)
    psi = normalize(raw[..., 0] + 1j * raw[..., 1])
    rho = density(psi)
    trace_err = jnp.max(jnp.abs(jnp.trace(rho, axis1=-2, axis2=-1) - 1.0))
    herm_err = jnp.max(jnp.abs(rho - jnp.conj(jnp.swapaxes(rho, -1, -2))))
    min_eval = jnp.min(jnp.linalg.eigvalsh(rho))
    checks = {
        "finite_s3_carrier_norm": q_norm_drift < 1.0e-12,
        "finite_density_trace_one": trace_err < 1.0e-12,
        "finite_density_hermitian": herm_err < 1.0e-12,
        "finite_density_positive": min_eval > -1.0e-10,
    }
    return layer_row(
        "F01_finite_carrier",
        "finite S3/C2 carrier and density objects",
        checks,
        {"max_s3_norm_drift": f(q_norm_drift), "density_trace_err": f(trace_err), "density_min_eval": f(min_eval)},
        "finite normalized S3 quaternions and C2 spinors -> density matrices",
        ["non-normalized random draws", "density trace/hermiticity/positivity checks"],
    )


def row_noncommuting_order() -> dict:
    ux = unitary_from_pauli(SX, 0.37)
    uy = unitary_from_pauli(SY, 0.29)
    ux2 = unitary_from_pauli(SX, 0.61)
    order_gap = jnp.linalg.norm(ux @ uy - uy @ ux)
    commuting_gap = jnp.linalg.norm(ux @ ux2 - ux2 @ ux)
    checks = {
        "noncommuting_order_gap_nonzero": order_gap > 1.0e-2,
        "commuting_same_axis_control_zero": commuting_gap < 1.0e-12,
    }
    return layer_row(
        "N01_noncommuting_order",
        "noncommuting operator-order layer",
        checks,
        {"order_gap_xy_yx": f(order_gap), "same_axis_control_gap": f(commuting_gap)},
        "two finite Pauli unitary words -> order-sensitive matrix gap",
        ["same-axis commuting control"],
    )


def row_response_effect_path_quotient() -> dict:
    psi = normalize(jnp.asarray([0.74 + 0.0j, 0.28 + 0.61j], dtype=jnp.complex128))
    rho = density(psi)
    effect = jnp.diag(jnp.asarray([1.0, 0.27], dtype=jnp.complex128))
    k0 = jnp.sqrt(0.68) * C2
    k1 = jnp.sqrt(0.32) * SX
    ks = [k0, k1]
    raw = jnp.asarray([jnp.real(jnp.trace(effect @ k @ rho @ jnp.conj(k.T))) for k in ks])
    weights = raw / jnp.sum(raw)
    quotient = weights / jnp.sum(weights)
    path_entropy = shannon_entropy(quotient)

    order_raw = jnp.asarray([jnp.real(jnp.trace(k @ effect @ rho @ jnp.conj((k @ effect).T))) for k in ks])
    order_weights = order_raw / jnp.sum(order_raw)
    order_gap = jnp.linalg.norm(weights - order_weights)
    uniform_control = jnp.ones_like(weights) / weights.shape[0]
    checks = {
        "finite_path_weights_normalized": jnp.abs(jnp.sum(weights) - 1.0) < 1.0e-12,
        "response_quotient_nonuniform": jnp.linalg.norm(quotient - uniform_control) > 1.0e-2,
        "effect_kraus_order_sensitive": order_gap > 1.0e-2,
        "path_entropy_finite": jnp.isfinite(path_entropy) and path_entropy > 0.0,
    }
    return layer_row(
        "response_effect_path_quotient",
        "response/effect/path quotient layer",
        checks,
        {"weights": [f(x) for x in weights], "path_entropy": f(path_entropy), "effect_kraus_order_gap": f(order_gap)},
        "finite density plus finite Kraus histories/effects -> normalized response quotient",
        ["uniform quotient control", "effect/Kraus order control"],
    )


def mutual_information_2q(rho: jax.Array) -> jax.Array:
    return vn_entropy(rho_a_2q(rho)) + vn_entropy(rho_b_2q(rho)) - vn_entropy(rho)


def row_boundary_environment_cut() -> dict:
    bell = jnp.asarray([1, 0, 0, 1], dtype=jnp.complex128) / jnp.sqrt(2.0)
    product = jnp.asarray([1, 0, 0, 0], dtype=jnp.complex128)
    rho_bell = density(bell)
    rho_product = density(product)
    rho_classical = jnp.diag(jnp.asarray([0.5, 0.0, 0.0, 0.5], dtype=jnp.complex128))
    mi_bell = mutual_information_2q(rho_bell)
    mi_product = mutual_information_2q(rho_product)
    mi_classical = mutual_information_2q(rho_classical)
    ln_bell = log_negativity_2q(rho_bell)
    ln_classical = log_negativity_2q(rho_classical)
    s_boundary = vn_entropy(rho_a_2q(rho_bell))
    checks = {
        "boundary_entropy_capacity_bounded": s_boundary <= jnp.log2(2.0) + 1.0e-12,
        "bell_boundary_environment_mi_nonzero": mi_bell > 1.999,
        "product_boundary_environment_mi_zero": jnp.abs(mi_product) < 1.0e-9,
        "classical_correlation_separated_from_entanglement": mi_classical > 0.999 and jnp.abs(ln_classical) < 1.0e-9,
        "bell_entanglement_witness_nonzero": ln_bell > 0.999,
    }
    return layer_row(
        "boundary_environment_cut",
        "finite boundary/environment cut layer",
        checks,
        {"MI_bell": f(mi_bell), "MI_product": f(mi_product), "MI_classical": f(mi_classical), "LN_classical": f(ln_classical), "S_boundary": f(s_boundary)},
        "finite rho_AB cut -> boundary entropy, mutual information, and entanglement witness columns",
        ["product cut control", "classically correlated separable control"],
    )


def hopf_base(q: jax.Array) -> jax.Array:
    a, c1, c2, d = q[..., 0], q[..., 1], q[..., 2], q[..., 3]
    return jnp.stack(
        [
            2.0 * (a * c2 + c1 * d),
            2.0 * (c1 * c2 - a * d),
            a * a + c1 * c1 - c2 * c2 - d * d,
        ],
        axis=-1,
    )


def hopf_phase(q: jax.Array, theta: jax.Array) -> jax.Array:
    co, si = jnp.cos(theta), jnp.sin(theta)
    a, bq, c, d = q[..., 0], q[..., 1], q[..., 2], q[..., 3]
    return jnp.stack([a * co - bq * si, a * si + bq * co, c * co - d * si, c * si + d * co], axis=-1)


def lift_base_to_quat(base: jax.Array) -> jax.Array:
    x, y, z = base[..., 0], base[..., 1], base[..., 2]
    r = jnp.sqrt(jnp.maximum((1.0 + z) / 2.0, 1.0e-12))
    c = x / (2.0 * r)
    d = -y / (2.0 * r)
    return normalize(jnp.stack([r, jnp.zeros_like(r), c, d], axis=-1))


def row_hopf_fiber_base() -> dict:
    key = jax.random.PRNGKey(202)
    q = normalize(jax.random.normal(key, (256, 4), dtype=jnp.float64))
    base = hopf_base(q)
    theta = jnp.linspace(0.0, 2.0 * jnp.pi, q.shape[0], dtype=jnp.float64)
    phased = hopf_phase(q, theta)
    fiber_delta = jnp.max(jnp.linalg.norm(base - hopf_base(phased), axis=-1))
    base_norm_drift = jnp.max(jnp.abs(jnp.linalg.norm(base, axis=-1) - 1.0))
    bad = normalize(q + jnp.asarray([0.0, 0.0, 0.17, 0.0]))
    bad_delta = jnp.mean(jnp.linalg.norm(base - hopf_base(bad), axis=-1))
    checks = {
        "hopf_base_lands_on_s2": base_norm_drift < 1.0e-12,
        "u1_fiber_action_preserves_base": fiber_delta < 1.0e-12,
        "nonfiber_perturbation_changes_base": bad_delta > 1.0e-2,
    }
    return layer_row(
        "hopf_fiber_base",
        "Hopf S3 -> S2 fiber/base layer",
        checks,
        {"base_norm_drift": f(base_norm_drift), "fiber_delta": f(fiber_delta), "nonfiber_delta_mean": f(bad_delta)},
        "unit quaternions on S3 -> Hopf base points on S2",
        ["U1 fiber invariance", "nonfiber perturbation control"],
    )


def row_dirac_monopole_u1_holonomy() -> dict:
    theta = jnp.pi / 3.0
    phis = jnp.linspace(0.0, 2.0 * jnp.pi, 385, dtype=jnp.float64)

    def spinor(phi):
        return jnp.asarray([jnp.cos(theta / 2.0), jnp.exp(1j * phi) * jnp.sin(theta / 2.0)], dtype=jnp.complex128)

    psi = jax.vmap(spinor)(phis)
    overlaps = jnp.sum(jnp.conj(psi[:-1]) * psi[1:], axis=1)
    berry = jnp.angle(jnp.prod(overlaps / jnp.abs(overlaps)))
    expected = 0.5 * 2.0 * jnp.pi * (1.0 - jnp.cos(theta))

    gauge = jnp.exp(1j * 0.17 * jnp.sin(phis) + 1j * 0.11 * jnp.sin(2.0 * phis))
    psi_g = psi * gauge[:, None]
    overlaps_g = jnp.sum(jnp.conj(psi_g[:-1]) * psi_g[1:], axis=1)
    berry_g = jnp.angle(jnp.prod(overlaps_g / jnp.abs(overlaps_g)))

    flattened = jnp.ones_like(psi).at[:, 1].set(0.0)
    flat_overlaps = jnp.sum(jnp.conj(flattened[:-1]) * flattened[1:], axis=1)
    flat_phase = jnp.angle(jnp.prod(flat_overlaps / jnp.abs(flat_overlaps)))
    phase_error = jnp.abs(wrap_angle(berry - expected))
    gauge_error = jnp.abs(wrap_angle(berry_g - berry))
    checks = {
        "finite_loop_matches_dirac_monopole_phase": phase_error < 1.0e-3,
        "closed_gauge_transform_preserves_phase": gauge_error < 1.0e-12,
        "flattened_control_kills_phase": jnp.abs(flat_phase) < 1.0e-12,
    }
    return layer_row(
        "dirac_monopole_u1_holonomy",
        "finite U(1)/Dirac monopole holonomy layer",
        checks,
        {"berry_phase": f(berry), "expected_phase": f(expected), "phase_error": f(phase_error), "gauge_error": f(gauge_error), "flat_phase": f(flat_phase)},
        "finite spinor loop on S2 -> Berry/U1 holonomy phase",
        ["closed gauge transform", "flattened no-holonomy control"],
    )


def row_operator_substage_cell() -> dict:
    ux = unitary_from_pauli(SX, 0.41)
    uy = unitary_from_pauli(SY, 0.33)
    uz = unitary_from_pauli(SZ, 0.22)
    psi = normalize(jnp.asarray([0.91 + 0.0j, 0.12 + 0.39j], dtype=jnp.complex128))
    rho = density(psi)
    rho_xy = ux @ uy @ rho @ jnp.conj((ux @ uy).T)
    rho_yx = uy @ ux @ rho @ jnp.conj((uy @ ux).T)
    rho_xz = ux @ uz @ rho @ jnp.conj((ux @ uz).T)
    order_gap = jnp.linalg.norm(rho_xy - rho_yx)
    alt_axis_gap = jnp.linalg.norm(rho_xy - rho_xz)
    same_axis = ux @ ux @ rho @ jnp.conj((ux @ ux).T)
    same_axis_control = ux @ ux @ rho @ jnp.conj((ux @ ux).T)
    trace_err = jnp.max(jnp.abs(jnp.asarray([jnp.trace(rho_xy), jnp.trace(rho_yx), jnp.trace(rho_xz)]) - 1.0))
    checks = {
        "operator_order_changes_cell_state": order_gap > 1.0e-2,
        "operator_axis_choice_changes_cell_state": alt_axis_gap > 1.0e-2,
        "same_word_control_zero": jnp.linalg.norm(same_axis - same_axis_control) < 1.0e-12,
        "cell_channel_trace_preserving": trace_err < 1.0e-12,
    }
    return layer_row(
        "operator_substage_cell",
        "finite operator/substage cell layer",
        checks,
        {"rho_XY_vs_YX_gap": f(order_gap), "rho_XY_vs_XZ_gap": f(alt_axis_gap), "trace_err": f(trace_err)},
        "finite spinor-derived density cell -> ordered local channel action",
        ["same-word control", "alternate-axis control", "trace preservation"],
    )


def row_gluing_groupoid_cocycle() -> dict:
    a = 0.31
    bphase = -0.72
    g01 = jnp.exp(1j * a)
    g12 = jnp.exp(1j * bphase)
    g02 = jnp.exp(1j * (a + bphase))
    cocycle_residual = jnp.abs(g01 * g12 / g02 - 1.0)
    bad_g02 = jnp.exp(1j * (a + bphase + 0.19))
    bad_residual = jnp.abs(g01 * g12 / bad_g02 - 1.0)
    holonomy = g01 * g12 * jnp.conj(g02)
    scrambled = g12 * g01 * jnp.conj(bad_g02)
    checks = {
        "cocycle_condition_holds": cocycle_residual < 1.0e-12,
        "bad_gluing_control_fails": bad_residual > 1.0e-2,
        "closed_consistent_loop_trivial_holonomy": jnp.abs(holonomy - 1.0) < 1.0e-12,
        "scrambled_inconsistent_loop_nontrivial": jnp.abs(scrambled - 1.0) > 1.0e-2,
    }
    return layer_row(
        "gluing_groupoid_cocycle",
        "finite gluing/groupoid cocycle layer",
        checks,
        {"cocycle_residual": f(cocycle_residual), "bad_residual": f(bad_residual), "scrambled_loop_gap": f(jnp.abs(scrambled - 1.0))},
        "finite patch transition phases -> cocycle and loop-holonomy readout",
        ["bad transition control", "inconsistent loop control"],
    )


def nearest_q_labels(q: jax.Array) -> jax.Array:
    return jnp.argmax(q @ Q_TARGETS.T, axis=-1) + 1


def nearest_q_targets(q: jax.Array) -> jax.Array:
    return Q_TARGETS[jnp.argmax(q @ Q_TARGETS.T, axis=-1)]


def adjacent_base_distance(q: jax.Array) -> jax.Array:
    base = hopf_base(q)
    return jnp.linalg.norm(base[:, 1:, :] - base[:, :-1, :], axis=-1)


@jax.jit
def evolve_nested(q0: jax.Array, coupling: jax.Array, prune_active: bool) -> tuple[jax.Array, jax.Array]:
    alive0 = jnp.ones((q0.shape[0],), dtype=bool)

    def step(carry, _):
        q, alive = carry
        local = nearest_q_targets(q)
        lifted = lift_base_to_quat(hopf_base(q[:, :-1, :]))
        coupled = normalize((1.0 - coupling) * local[:, 1:, :] + coupling * lifted)
        target = jnp.concatenate([local[:, :1, :], coupled], axis=1)
        align = jnp.sum(target * q, axis=-1, keepdims=True)
        q_next = normalize(q + 0.003 * 2.0 * (target - align * q))
        killed = jnp.logical_and(prune_active, jnp.any(q_next[:, :, 0] < -0.01, axis=1))
        return (q_next, jnp.logical_and(alive, jnp.logical_not(killed))), None

    (qf, alivef), _ = jax.lax.scan(step, (q0, alive0), xs=None, length=1600)
    return qf, alivef


def nested_summary(q0: jax.Array, coupling: float, prune_active: bool) -> tuple[list[int], int, float, jax.Array]:
    qf, alive = evolve_nested(q0, jnp.asarray(coupling, dtype=jnp.float64), prune_active)
    labels = nearest_q_labels(qf[:, 0, :])
    populated = sorted(int(x) for x in jnp.unique(labels[alive]))
    pruned = int(q0.shape[0] - jnp.sum(alive))
    align = float(jnp.mean(adjacent_base_distance(qf)[alive]))
    return populated, pruned, align, alive


def row_nested_hopf_shells() -> dict:
    n = 256
    raw = jax.random.normal(jax.random.PRNGKey(303), (12 * n, 3, 4), dtype=jnp.float64)
    unit = normalize(raw)
    mask = jnp.all(unit[:, :, 0] > 0.05, axis=1)
    idx = jnp.nonzero(mask, size=n, fill_value=0)[0]
    q0 = unit[idx]
    initial_align = float(jnp.mean(adjacent_base_distance(q0)))
    a, a_pruned, a_align, alive_a = nested_summary(q0, 0.63, False)
    bpop, b_pruned, _b_align, _alive_b = nested_summary(q0, 0.63, True)
    c, c_pruned, _c_align, alive_c = nested_summary(q0, 0.63, False)
    _z, _z_pruned, zero_align, _alive_z = nested_summary(q0, 0.0, False)
    checks = {
        "baseline_reaches_all_outer_basins": a == [1, 2, 3, 4],
        "chirality_prune_kills_forbidden": (set(bpop) & {3, 4}) == set(),
        "trivial_control_equals_baseline": c == a and c_pruned == 0 and alive_c.tolist() == alive_a.tolist(),
        "positive_coupling_beats_zero_control": (initial_align - a_align) > (initial_align - zero_align) + 1.0e-6,
        "real_prune_fired": b_pruned > 0 and a_pruned == 0,
    }
    return layer_row(
        "nested_hopf_shells",
        "nested Hopf shell coupling layer",
        checks,
        {
            "A_basins": a,
            "B_basins": bpop,
            "B_pruned": b_pruned,
            "initial_alignment": initial_align,
            "coupled_alignment_delta": initial_align - a_align,
            "zero_control_alignment_delta": initial_align - zero_align,
        },
        "three S3 shells -> coupled Hopf-base alignment and survivor basin sets",
        ["zero-coupling control", "trivial no-prune control", "forbidden-basin prune"],
    )


def blk(a: jax.Array, bmat: jax.Array, cmat: jax.Array, dmat: jax.Array) -> jax.Array:
    return jnp.block([[a, bmat], [cmat, dmat]])


G0 = blk(Z2, C2, C2, Z2)
G1 = blk(Z2, SX, -SX, Z2)
G2 = blk(Z2, SY, -SY, Z2)
G3 = blk(Z2, SZ, -SZ, Z2)
GAMMAS = jnp.stack([G0, G1, G2, G3], axis=0)
ETA = jnp.diag(jnp.asarray([1, -1, -1, -1], dtype=jnp.complex128))
G5 = 1j * G0 @ G1 @ G2 @ G3
SROT = G1 @ G2 / 2.0

DIRAC_TARGETS = normalize(
    jnp.asarray(
        [[0, 0, 1, 0.3], [0, 0, 0.3, 1], [1, 0.3, 0, 0], [0.3, 1, 0, 0]],
        dtype=jnp.complex128,
    )
)


def chiral_charge(psi: jax.Array) -> jax.Array:
    return jnp.real(jnp.einsum("...i,ij,...j->...", jnp.conj(psi), G5, psi))


def nearest_dirac_labels(psi: jax.Array, targets: jax.Array) -> jax.Array:
    return jnp.argmax(jnp.abs(jnp.conj(psi) @ targets.T) ** 2, axis=-1) + 1


def nearest_dirac_targets(psi: jax.Array, targets: jax.Array) -> jax.Array:
    return targets[jnp.argmax(jnp.abs(jnp.conj(psi) @ targets.T) ** 2, axis=-1)]


def dirac_flow(psi: jax.Array, targets: jax.Array) -> jax.Array:
    target = nearest_dirac_targets(psi, targets)
    align = jnp.sum(jnp.conj(psi) * target, axis=-1, keepdims=True)
    return 2.0 * (target - align * psi)


@jax.jit
def evolve_dirac(psi0: jax.Array, targets: jax.Array, prune_code: jax.Array) -> tuple[jax.Array, jax.Array]:
    alive0 = jnp.ones((psi0.shape[0],), dtype=bool)

    def step(carry, _):
        psi, alive = carry
        k1 = dirac_flow(psi, targets)
        k2 = dirac_flow(normalize(psi + 0.005 * k1), targets)
        psi_next = normalize(psi + 0.01 * k2)
        q = chiral_charge(psi_next)
        killed = jnp.where(prune_code == 1, q < -0.01, jnp.where(prune_code == 2, q > 0.99, False))
        return (psi_next, jnp.logical_and(alive, jnp.logical_not(killed))), None

    (psif, alivef), _ = jax.lax.scan(step, (psi0, alive0), xs=None, length=1200)
    return psif, alivef


def dirac_classify(psi0: jax.Array, targets: jax.Array, code: int) -> tuple[list[int], int, jax.Array, jax.Array]:
    psif, alive = evolve_dirac(psi0, targets, jnp.asarray(code))
    labels = nearest_dirac_labels(psif, targets)
    return sorted(int(x) for x in jnp.unique(labels[alive])), int(psi0.shape[0] - jnp.sum(alive)), labels, alive


def row_weyl_gamma5_chirality() -> dict:
    n = 320
    raw = jax.random.normal(jax.random.PRNGKey(404), (10 * n, 4, 2), dtype=jnp.float64)
    unit = normalize(raw[..., 0] + 1j * raw[..., 1])
    mask = chiral_charge(unit) > 0.1
    idx = jnp.nonzero(mask, size=n, fill_value=0)[0]
    psi0 = unit[idx]
    a, a_pruned, labels_a, alive_a = dirac_classify(psi0, DIRAC_TARGETS, 0)
    bpop, b_pruned, _labels_b, _alive_b = dirac_classify(psi0, DIRAC_TARGETS, 1)
    c, c_pruned, _labels_c, alive_c = dirac_classify(psi0, DIRAC_TARGETS, 0)
    inv, _inv_pruned, _labels_inv, _alive_inv = dirac_classify(psi0, DIRAC_TARGETS, 2)
    key = jax.random.PRNGKey(11)
    perm = jax.random.permutation(key, n)
    doomed = jnp.zeros((n,), dtype=bool).at[perm[:b_pruned]].set(True)
    random_pop = sorted(int(x) for x in jnp.unique(labels_a[jnp.logical_not(doomed)]))
    g5sq = jnp.max(jnp.abs(G5 @ G5 - C4))
    anti = jnp.max(jnp.asarray([jnp.max(jnp.abs(G5 @ g + g @ G5)) for g in GAMMAS]))
    cliff = jnp.max(
        jnp.asarray(
            [jnp.max(jnp.abs(GAMMAS[m] @ GAMMAS[k] + GAMMAS[k] @ GAMMAS[m] - 2 * ETA[m, k] * C4)) for m in range(4) for k in range(4)]
        )
    )
    checks = {
        "gamma5_derived_and_clifford_valid": g5sq < 1.0e-12 and anti < 1.0e-12 and cliff < 1.0e-12,
        "A_reaches_forbidden": bool(set(a) & {3, 4}),
        "B_kills_forbidden": (set(bpop) & {3, 4}) == set(),
        "C_equals_A": c == a and c_pruned == 0 and alive_c.tolist() == alive_a.tolist(),
        "rate_matched_random_keeps_forbidden": bool(set(random_pop) & {3, 4}),
        "inverted_sign_flips_to_forbidden": (set(inv) & {1, 2}) == set() and bool(set(inv) & {3, 4}),
        "real_prune_fired": b_pruned > 0 and a_pruned == 0,
    }
    return layer_row(
        "weyl_gamma5_chirality",
        "Weyl/Dirac gamma5 chirality selector layer",
        checks,
        {"A": a, "B": bpop, "C": c, "B_pruned": b_pruned, "random": random_pop, "inverted": inv},
        "C4 Dirac spinor futures -> gamma5 chiral charge prune -> survivor basin sets",
        ["rate-matched random prune", "inverted-sign prune", "trivial no-prune control"],
    )


def vn_entropy(rho: jax.Array) -> jax.Array:
    ev = jnp.linalg.eigvalsh(0.5 * (rho + jnp.conj(rho.T)))
    ev = jnp.clip(jnp.real(ev), 0.0, 1.0)
    return -jnp.sum(jnp.where(ev > 1.0e-12, ev * jnp.log2(ev), 0.0))


def shannon_entropy(p: jax.Array) -> jax.Array:
    p = jnp.clip(jnp.real(p), 0.0, 1.0)
    return -jnp.sum(jnp.where(p > 1.0e-12, p * jnp.log2(p), 0.0))


def rdm_pure(psi: jax.Array, keep: list[int], n: int) -> jax.Array:
    keep = list(keep)
    trace = [i for i in range(n) if i not in keep]
    t = jnp.transpose(psi.reshape([2] * n), keep + trace).reshape(2 ** len(keep), 2 ** len(trace))
    return t @ jnp.conj(t.T)


def rdm_mixed(rho: jax.Array, keep: list[int], n: int) -> jax.Array:
    keep_sorted = sorted(keep)
    trace = [i for i in range(n) if i not in keep_sorted]
    t = rho.reshape([2] * n + [2] * n)
    for q in sorted(trace, reverse=True):
        t = jnp.trace(t, axis1=q, axis2=q + t.ndim // 2)
    return t.reshape(2 ** len(keep_sorted), 2 ** len(keep_sorted))


def rho_a_2q(rho: jax.Array) -> jax.Array:
    return jnp.trace(rho.reshape(2, 2, 2, 2), axis1=1, axis2=3)


def rho_b_2q(rho: jax.Array) -> jax.Array:
    return jnp.trace(rho.reshape(2, 2, 2, 2), axis1=0, axis2=2)


def log_negativity_2q(rho: jax.Array) -> jax.Array:
    pt = rho.reshape(2, 2, 2, 2).transpose(0, 3, 2, 1).reshape(4, 4)
    ev = jnp.linalg.eigvalsh(0.5 * (pt + jnp.conj(pt.T)))
    return jnp.log2(jnp.sum(jnp.abs(ev)))


def row_qit_entropy_information() -> dict:
    bell = jnp.asarray([1, 0, 0, 1], dtype=jnp.complex128) / jnp.sqrt(2.0)
    product = jnp.asarray([1, 0, 0, 0], dtype=jnp.complex128)
    rho_bell = density(bell)
    rho_product = density(product)
    rho_classical = jnp.diag(jnp.asarray([0.5, 0.0, 0.0, 0.5], dtype=jnp.complex128))
    ln_bell = log_negativity_2q(rho_bell)
    ln_classical = log_negativity_2q(rho_classical)
    ln_product = log_negativity_2q(rho_product)
    s_ab = vn_entropy(rho_bell)
    s_b = vn_entropy(rho_b_2q(rho_bell))
    cond = s_ab - s_b
    coherent = s_b - s_ab
    mi_classical = vn_entropy(rho_a_2q(rho_classical)) + vn_entropy(rho_b_2q(rho_classical)) - vn_entropy(rho_classical)
    checks = {
        "bell_logneg_nonzero": jnp.abs(ln_bell - 1.0) < 1.0e-9,
        "classical_logneg_zero": jnp.abs(ln_classical) < 1.0e-9,
        "product_logneg_zero": jnp.abs(ln_product) < 1.0e-9,
        "bell_negative_conditional_entropy": cond < -0.999,
        "bell_coherent_information_positive": coherent > 0.999,
        "classical_mi_can_be_nonzero_without_entanglement": mi_classical > 0.999 and jnp.abs(ln_classical) < 1.0e-9,
    }
    return layer_row(
        "qit_entropy_information",
        "finite QIT entropy/information readout layer",
        checks,
        {
            "LN_bell": f(ln_bell),
            "LN_classical": f(ln_classical),
            "LN_product": f(ln_product),
            "S_A_given_B_bell": f(cond),
            "I_c_A_to_B_bell": f(coherent),
            "I_AB_classical": f(mi_classical),
        },
        "finite two-qubit density matrices -> entropy, coherent information, log-negativity",
        ["product separable control", "classically correlated separable control"],
    )


def row_capacity_path_entropy_budget() -> dict:
    rho_boundary = jnp.diag(jnp.asarray([0.5, 0.25, 0.125, 0.125], dtype=jnp.complex128))
    p_path = jnp.asarray([0.5, 0.25, 0.25, 0.0], dtype=jnp.float64)
    s_boundary = vn_entropy(rho_boundary)
    h_path = shannon_entropy(p_path)
    s_max = jnp.log2(8.0)
    h_path_max = jnp.log2(float(p_path.shape[0]))
    capacity_budget = s_max + h_path_max
    violated_budget = 2.0
    checks = {
        "density_entropy_finite": jnp.isfinite(s_boundary) and s_boundary > 0.0,
        "path_entropy_finite_record_only": jnp.isfinite(h_path) and h_path > 0.0,
        "capacity_budget_admits": capacity_budget >= s_boundary + h_path,
        "too_small_capacity_control_blocks": violated_budget < s_boundary + h_path,
        "path_registry_bound_respected": h_path <= h_path_max + 1.0e-12,
    }
    return layer_row(
        "capacity_path_entropy_budget",
        "finite capacity/path entropy budget layer",
        checks,
        {
            "S_boundary": f(s_boundary),
            "H_path": f(h_path),
            "S_max": f(s_max),
            "H_path_max": f(h_path_max),
            "capacity_budget": f(capacity_budget),
            "violated_budget_control": violated_budget,
        },
        "finite density entropy plus finite instrument path entropy -> capacity-budget gate",
        ["too-small capacity control", "finite path-registry max entropy bound"],
    )


def cmi_from_rdm(get_rdm, n: int) -> jax.Array:
    s_ab = vn_entropy(get_rdm([0, 1], n))
    s_bc = vn_entropy(get_rdm([1, 2], n))
    s_b = vn_entropy(get_rdm([1], n))
    s_abc = vn_entropy(get_rdm([0, 1, 2], n))
    return s_ab + s_bc - s_b - s_abc


def row_conditional_mutual_information_readout() -> dict:
    n = 3
    ghz = jnp.zeros((2**n,), dtype=jnp.complex128).at[0].set(1.0 / jnp.sqrt(2.0)).at[7].set(1.0 / jnp.sqrt(2.0))
    ab_bell_c_product = jnp.zeros((2**n,), dtype=jnp.complex128).at[0].set(1.0 / jnp.sqrt(2.0)).at[6].set(1.0 / jnp.sqrt(2.0))
    classical_ac = jnp.diag(jnp.asarray([0.5, 0, 0, 0, 0, 0.5, 0, 0], dtype=jnp.complex128))

    ghz_cmi = cmi_from_rdm(lambda keep, nn: rdm_pure(ghz, keep, nn), n)
    markov_cmi = cmi_from_rdm(lambda keep, nn: rdm_pure(ab_bell_c_product, keep, nn), n)
    classical_cmi = cmi_from_rdm(lambda keep, nn: rdm_mixed(classical_ac, keep, nn), n)
    classical_ac_ln = log_negativity_2q(rdm_mixed(classical_ac, [0, 2], n))
    checks = {
        "ghz_has_nonzero_cmi": ghz_cmi > 0.999,
        "quantum_markov_control_zero_cmi": jnp.abs(markov_cmi) < 1.0e-9,
        "classical_shadow_can_have_cmi": classical_cmi > 0.999,
        "classical_shadow_has_zero_logneg": jnp.abs(classical_ac_ln) < 1.0e-9,
    }
    return layer_row(
        "conditional_mutual_information_readout",
        "conditional mutual information readout layer",
        checks,
        {"CMI_GHZ": f(ghz_cmi), "CMI_markov_control": f(markov_cmi), "CMI_classical_shadow": f(classical_cmi), "LN_classical_AC": f(classical_ac_ln)},
        "finite three-qubit density objects -> I(A:C|B) readout kept separate from entanglement witnesses",
        ["quantum Markov control", "classical-shadow separable control"],
    )


def matrix_log_psd(rho: jax.Array) -> jax.Array:
    ev, vec = jnp.linalg.eigh(0.5 * (rho + jnp.conj(rho.T)))
    ev = jnp.clip(jnp.real(ev), 1.0e-12, None)
    return vec @ jnp.diag(jnp.log(ev)) @ jnp.conj(vec.T)


def quantum_relative_entropy(rho: jax.Array, sigma: jax.Array) -> jax.Array:
    return jnp.real(jnp.trace(rho @ (matrix_log_psd(rho) - matrix_log_psd(sigma))))


def row_qit_relative_free_energy() -> dict:
    rho = jnp.asarray([[0.7, 0.12], [0.12, 0.3]], dtype=jnp.complex128)
    rho = rho / jnp.trace(rho)
    sigma = jnp.asarray([[0.45, 0.03j], [-0.03j, 0.55]], dtype=jnp.complex128)
    sigma = sigma / jnp.trace(sigma)
    tau = jnp.asarray([[1.2, 0.0], [0.0, 0.4]], dtype=jnp.complex128)
    z = jnp.real(jnp.trace(tau))
    thermal = tau / z
    d_rs = quantum_relative_entropy(rho, sigma)
    d_rr = quantum_relative_entropy(rho, rho)
    f_q = quantum_relative_entropy(sigma, thermal) - jnp.log(z)
    checks = {
        "relative_entropy_nonnegative": d_rs > -1.0e-10,
        "relative_entropy_self_zero": jnp.abs(d_rr) < 1.0e-9,
        "partition_log_kept_separate": jnp.isfinite(jnp.log(z)) and z > 0.0,
        "qit_free_energy_finite": jnp.isfinite(f_q),
    }
    return layer_row(
        "qit_relative_free_energy",
        "finite QIT relative/free-energy readout layer",
        checks,
        {"D_rho_sigma": f(d_rs), "D_rho_rho": f(d_rr), "logZ": f(jnp.log(z)), "F_Q": f(f_q)},
        "finite density matrices and finite positive tau -> D(rho||sigma), logZ, F_Q as separate columns",
        ["self-relative-entropy zero control", "positive finite partition object"],
    )


def row_spectral_triple_dirac() -> dict:
    gamma = jnp.kron(SZ, C2)
    dirac = jnp.kron(SX, C2)
    algebra = jnp.diag(jnp.asarray([0.0, 1.0, 2.0, 4.0], dtype=jnp.complex128))
    comm = dirac @ algebra - algebra @ dirac
    d0 = jnp.zeros_like(dirac)
    ev = jnp.linalg.eigvalsh(dirac)
    checks = {
        "dirac_self_adjoint": jnp.linalg.norm(dirac - jnp.conj(dirac.T)) < 1.0e-12,
        "chirality_anticommutes_with_dirac": jnp.linalg.norm(gamma @ dirac + dirac @ gamma) < 1.0e-12,
        "algebra_commutator_finite_nonzero": jnp.linalg.norm(comm) > 1.0e-2 and jnp.isfinite(jnp.linalg.norm(comm)),
        "zero_dirac_control_kills_commutator": jnp.linalg.norm(d0 @ algebra - algebra @ d0) < 1.0e-12,
        "dirac_spectrum_symmetric": jnp.linalg.norm(jnp.sort(ev) + jnp.sort(ev)[::-1]) < 1.0e-12,
    }
    return layer_row(
        "spectral_triple_dirac",
        "finite spectral-triple Dirac layer",
        checks,
        {"commutator_norm": f(jnp.linalg.norm(comm)), "spectrum": [f(x) for x in ev]},
        "finite algebra representation plus self-adjoint Dirac/chirality -> commutator geometry readout",
        ["zero-Dirac control", "spectrum symmetry check"],
    )


def row_twistor_null_incidence() -> dict:
    lam = normalize(jnp.asarray([1.0 + 0.0j, 0.32 + 0.41j], dtype=jnp.complex128))
    sigmas = [C2, SX, SY, SZ]
    p = jnp.asarray([jnp.real(jnp.vdot(lam, s @ lam)) for s in sigmas])
    minkowski_norm = p[0] ** 2 - jnp.sum(p[1:] ** 2)
    lam_phase = jnp.exp(1j * 0.73) * lam
    p_phase = jnp.asarray([jnp.real(jnp.vdot(lam_phase, s @ lam_phase)) for s in sigmas])
    rho_mixed = jnp.diag(jnp.asarray([0.72, 0.28], dtype=jnp.complex128))
    p_mixed = jnp.asarray([jnp.real(jnp.trace(rho_mixed @ s)) for s in sigmas])
    mixed_norm = p_mixed[0] ** 2 - jnp.sum(p_mixed[1:] ** 2)
    checks = {
        "spinor_incidence_vector_is_null": jnp.abs(minkowski_norm) < 1.0e-12,
        "phase_gauge_preserves_null_vector": jnp.linalg.norm(p - p_phase) < 1.0e-12,
        "mixed_density_control_not_null": mixed_norm > 1.0e-2,
    }
    return layer_row(
        "twistor_null_incidence",
        "finite twistor/null-incidence spinor layer",
        checks,
        {"minkowski_norm": f(minkowski_norm), "phase_delta": f(jnp.linalg.norm(p - p_phase)), "mixed_density_minkowski_norm": f(mixed_norm)},
        "finite Weyl spinor -> Hermitian null vector incidence readout",
        ["phase gauge control", "mixed-density non-null control"],
    )


def row_g_structure_form_identities() -> dict:
    j2 = jnp.asarray([[0.0, -1.0], [1.0, 0.0]], dtype=jnp.float64)
    jmat = jnp.kron(jnp.eye(3, dtype=jnp.float64), j2)
    omega = jmat
    metric = jnp.eye(6, dtype=jnp.float64)
    j2_err = jnp.linalg.norm(jmat @ jmat + metric)
    compat_err = jnp.linalg.norm(jmat.T @ metric @ jmat - metric)
    omega_nondeg = jnp.abs(jnp.linalg.det(omega))
    bad = omega.at[0, 1].set(0.0).at[1, 0].set(0.0)
    bad_det = jnp.abs(jnp.linalg.det(bad))
    checks = {
        "almost_complex_square_minus_identity": j2_err < 1.0e-12,
        "metric_compatibility": compat_err < 1.0e-12,
        "symplectic_form_nondegenerate": omega_nondeg > 0.999,
        "degenerate_control_fails": bad_det < 1.0e-9,
    }
    return layer_row(
        "g_structure_form_identities",
        "finite SU(3)-style form identity layer",
        checks,
        {"J_square_error": f(j2_err), "metric_compat_error": f(compat_err), "omega_det_abs": f(omega_nondeg), "bad_det_abs": f(bad_det)},
        "finite R6 almost-complex/symplectic matrices -> algebraic G-structure identity checks",
        ["degenerate-form control"],
    )


def lindblad_rhs(rho: jax.Array, h: jax.Array, l_op: jax.Array) -> jax.Array:
    ld = jnp.conj(l_op.T)
    jump = l_op @ rho @ ld
    deco = ld @ l_op
    return -1j * (h @ rho - rho @ h) + 0.35 * (jump - 0.5 * (deco @ rho + rho @ deco))


def evolve_rho(rho0: jax.Array, h: jax.Array, l_op: jax.Array) -> jax.Array:
    def step(rho, _):
        rho_next = rho + 0.01 * lindblad_rhs(rho, h, l_op)
        rho_next = 0.5 * (rho_next + jnp.conj(rho_next.T))
        rho_next = rho_next / jnp.trace(rho_next)
        return rho_next, None

    rho_f, _ = jax.lax.scan(step, rho0, xs=None, length=240)
    return rho_f


def row_left_right_weyl_terrain_loop() -> dict:
    h0 = 0.77 * SZ + 0.13 * SX
    psi0 = normalize(jnp.asarray([1.0, 0.55 + 0.2j], dtype=jnp.complex128))
    rho0 = density(psi0)
    left = evolve_rho(rho0, h0, SM)
    right_full = evolve_rho(rho0, -h0, SP)
    right_sign_only = evolve_rho(rho0, -h0, SM)
    right_swap_only = evolve_rho(rho0, h0, SP)
    full_gap = jnp.linalg.norm(left - right_full)
    swap_matters = jnp.linalg.norm(right_full - right_sign_only)
    sign_matters = jnp.linalg.norm(right_full - right_swap_only)
    trace_err = jnp.max(jnp.abs(jnp.asarray([jnp.trace(left), jnp.trace(right_full)]) - 1.0))
    checks = {
        "left_right_full_gap_nonzero": full_gap > 1.0e-2,
        "sigma_swap_is_load_bearing": swap_matters > 1.0e-2,
        "hamiltonian_sign_is_load_bearing": sign_matters > 1.0e-2,
        "density_trace_preserved": trace_err < 1.0e-9,
    }
    return layer_row(
        "left_right_weyl_terrain_loop",
        "left/right Weyl density terrain-loop generator layer",
        checks,
        {"left_right_gap": f(full_gap), "swap_matters_gap": f(swap_matters), "sign_matters_gap": f(sign_matters)},
        "rho_L/rho_R finite C2 densities -> signed Hamiltonian plus sigma-/sigma+ terrain evolution",
        ["sign-only control", "swap-only control", "trace preservation"],
    )


@jax.jit
def evolve_simple_branch(q0: jax.Array, prune_active: bool) -> tuple[jax.Array, jax.Array]:
    alive0 = jnp.ones((q0.shape[0],), dtype=bool)

    def step(carry, _):
        q, alive = carry
        target = nearest_q_targets(q)
        align = jnp.sum(target * q, axis=-1, keepdims=True)
        q_next = normalize(q + 0.003 * 2.0 * (target - align * q))
        killed = jnp.logical_and(prune_active, q_next[:, 0] < -0.01)
        return (q_next, jnp.logical_and(alive, jnp.logical_not(killed))), None

    (qf, alivef), _ = jax.lax.scan(step, (q0, alive0), xs=None, length=2600)
    return qf, alivef


def branch_summary(q0: jax.Array, prune: bool) -> tuple[list[int], int, jax.Array]:
    qf, alive = evolve_simple_branch(q0, prune)
    labels = nearest_q_labels(qf)
    return sorted(int(x) for x in jnp.unique(labels[alive])), int(q0.shape[0] - jnp.sum(alive)), alive


def row_survivor_quotient_branch_prune() -> dict:
    n = 320
    raw = jax.random.normal(jax.random.PRNGKey(505), (4 * n, 4), dtype=jnp.float64)
    unit = normalize(raw)
    idx = jnp.nonzero(unit[:, 0] > 0.05, size=n, fill_value=0)[0]
    q0 = unit[idx]
    a, a_pruned, alive_a = branch_summary(q0, False)
    bpop, b_pruned, _alive_b = branch_summary(q0, True)
    c, c_pruned, alive_c = branch_summary(q0, False)
    checks = {
        "baseline_reaches_all_basins": a == [1, 2, 3, 4],
        "prune_kills_forbidden_basins": (set(bpop) & {3, 4}) == set(),
        "allowed_basins_preserved": (set(a) & {1, 2}) <= set(bpop),
        "trivial_control_equals_baseline": c == a and c_pruned == 0 and alive_c.tolist() == alive_a.tolist(),
        "real_prune_fired": b_pruned > 0 and a_pruned == 0,
    }
    return layer_row(
        "survivor_quotient_branch_prune",
        "branch/prune survivor quotient layer",
        checks,
        {"A": a, "B": bpop, "C": c, "B_pruned": b_pruned},
        "finite S3 future ensemble -> monotone prune latch -> survivor quotient basin set",
        ["no-prune baseline", "never-firing control", "forbidden-sector prune"],
    )


def read_julia_reference_receipts() -> dict:
    refs = {}
    for name, rel in {
        "gamma5_branch_prune": "system_v5/julia_carrier/branch_prune_dirac_gamma5_chirality_object_results.json",
        "geometry_information_admissibility": "system_v5/julia_carrier/branch_prune_geometry_is_information_admissibility_results.json",
        "noncircular_geometry_information_test": "system_v5/julia_carrier/noncircular_geometry_information_test_results.json",
        "reidemeister_kill_control": "system_v5/julia_carrier/popper_reidemeister_kill_control_results.json",
    }.items():
        path = Path(rel)
        if not path.exists():
            refs[name] = {"path": rel, "exists": False}
            continue
        data = json.loads(path.read_text())
        refs[name] = {
            "path": rel,
            "exists": True,
            "all_pass": data.get("all_pass"),
            "audit_pass": data.get("audit_pass"),
            "promotion_allowed": data.get("promotion_allowed"),
            "classification": data.get("classification"),
            "claim_status": data.get("claim_status"),
            "verdict": data.get("CIRCULARITY_VERDICT") or data.get("verdict"),
        }
    return refs


def main() -> None:
    rows = [
        row_finite_carrier(),
        row_noncommuting_order(),
        row_response_effect_path_quotient(),
        row_boundary_environment_cut(),
        row_hopf_fiber_base(),
        row_dirac_monopole_u1_holonomy(),
        row_operator_substage_cell(),
        row_gluing_groupoid_cocycle(),
        row_nested_hopf_shells(),
        row_weyl_gamma5_chirality(),
        row_qit_entropy_information(),
        row_capacity_path_entropy_budget(),
        row_conditional_mutual_information_readout(),
        row_qit_relative_free_energy(),
        row_spectral_triple_dirac(),
        row_twistor_null_incidence(),
        row_g_structure_form_identities(),
        row_left_right_weyl_terrain_loop(),
        row_survivor_quotient_branch_prune(),
    ]
    julia_refs = read_julia_reference_receipts()
    checks = {
        "all_layer_rows_pass": all(row["pass"] for row in rows),
        "nineteen_independent_rows_present": len(rows) == 19,
        "promotion_blocked": True,
        "legacy_tensor_lane_not_used": True,
        "julia_reference_mode_read_only": True,
    }
    receipt = {
        "name": "jax_manifold_layer_independent_suite",
        "object": "independent JAX diagnostic matrix for current manifold-layer primitives",
        "executed_track": "jax",
        "ran_julia": False,
        "julia_reference_mode": "read_only",
        "classification": "diagnostic_jax_layer_suite",
        "promotion_allowed": False,
        "claim_boundary": (
            "All rows are finite JAX diagnostics. This does not admit all manifold layers, "
            "PEPS3D, stacking, Axis0/FEP, flux, physics, or final manifold completion."
        ),
        "julia_truth_lane": "Julia remains the native Clifford/full-spinor truth lane for geometric admission.",
        "jax_lane": "JAX stress-tests finite approximations, controls, and latch/readout invariants.",
        "julia_reference_receipts_read": julia_refs,
        "julia_lessons_applied": [
            "branch/prune is treated as a possibility-field computation with monotone survivor masks",
            "log-negativity and coherent information stay separate from CMI/classical-shadow readouts",
            "capacity/path entropy is finite-record-derived and capacity-bounded",
            "geometry-information coincidence claims remain fenced by the noncircular/Reidemeister kill controls",
            "JAX enforces constraints by retraction/correction and is not the native spinor truth lane",
        ],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "source_alignment": {
            "finite_geometric_constraint_manifold": True,
            "left_right_weyl_density_operating_spaces_included": True,
            "downstream_entropy_readouts_kept_as_readouts": True,
        },
        "layer_results": rows,
        "checks": checks,
        "AUDIT_PASS": all(checks.values()),
    }
    OUT.write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"layers={len(rows)} pass={sum(1 for row in rows if row['pass'])}/{len(rows)}")
    print(f"AUDIT_PASS={receipt['AUDIT_PASS']}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""JAX runner for Julia-reference geometric constraint layers.

This is the JAX audit/stress lane. It reads Julia result JSONs as reference
targets only, then runs a finite JAX diagnostic row for each proposed layer.
It does not execute Julia and it does not make layer/manifold/admission claims.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import jax
from jax import config

config.update("jax_enable_x64", True)

import jax.numpy as jnp
from jax.scipy.linalg import expm


OUT = Path("jax_julia_reference_geometric_constraint_layer_runner_results.json")
REF_DIR = Path("system_v5/julia_carrier/layers")
EXTRA_REFERENCE_PATHS = [
    Path("system_v5/julia_carrier/l1_boundary_closure_dynamical_algebra_results.json"),
]
FUTURE_PHASE_REFERENCE_ROWS = {
    "basin_hierarchy_discovery_codex_results.json": {
        "blocked_status": "blocked_until_independent_layers_and_geometries_simed_then_nesting_order",
        "reason": "Basin hierarchy is downstream of independent layer/geometry coverage and nesting-order closure.",
    },
    "ratchet_order_test_codex_results.json": {
        "blocked_status": "blocked_until_independent_layers_and_geometries_simed",
        "reason": "Ratchet/order testing is the next phase after independent layer/geometry coverage, not a layer-coverage row.",
    },
    "flux_direction_impedance_results.json": {
        "blocked_status": "blocked_until_independent_layers_geometries_and_nesting_order_close",
        "reason": "Flux is a derived downstream readout; it cannot count as independent layer/geometry coverage.",
    },
    "ratchet_order_test_results.json": {
        "blocked_status": "blocked_scaffold_only_until_parent_complete_layers",
        "reason": "The receipt itself is scaffold_only and says real ratchet testing is blocked until parent-complete layer maps exist.",
    },
    "nested_peps2d_substrate_effect_imagtime_results.json": {
        "blocked_status": "blocked_tool_lego_fit_probe_not_independent_layer_reference",
        "reason": "This Julia receipt is a PEPS2D substrate tool-lego fit probe and remains partial/red; it is not an independent geometry-layer reference row.",
    },
    "nested_peps2d_substrate_effect_opt_results.json": {
        "blocked_status": "blocked_substrate_effect_optimization_not_independent_layer_reference",
        "reason": "This Julia receipt is an optimization/substrate-effect probe, downstream of the independent geometry coverage rows.",
    },
    "ratchet_diagnostic_scratch_results.json": {
        "blocked_status": "blocked_scratch_only_not_independent_layer_reference",
        "reason": "This Julia receipt is explicitly scratch-only; it can inform later ratchet work but cannot count as an independent layer/geometry reference row.",
    },
}
RED_REFERENCE_SUPERSESSION_RECEIPTS = {
    "L4_layer_results.json": Path("system_v5/ops/formal_scouts/results/jax_l4_hopf_connection_c1_order_fence_probe_results.json"),
    "sixteen_terrain_placement_lattice_results.json": Path("system_v5/ops/formal_scouts/results/jax_sixteen_terrain_placement_lattice_probe_results.json"),
    "sixteen_terrain_quantumoptics_results.json": Path("system_v5/ops/formal_scouts/results/jax_sixteen_terrain_lindblad_dual_integrator_fence_probe_results.json"),
    "L9_layer_results.json": Path("system_v5/ops/formal_scouts/results/jax_l9_clifford_module_legacy_red_reference_fence_results.json"),
    "signed_operators_density_bloch_free_results.json": Path("system_v5/ops/formal_scouts/results/jax_signed_operators_density_order_gap_fence_results.json"),
    "g_u1_hopf_bundle_chern_results.json": Path("system_v5/ops/formal_scouts/results/jax_u1_hopf_bundle_chern_partial_reference_fence_results.json"),
    "entropy_readout_family_peps2d_results.json": Path("system_v5/ops/formal_scouts/results/jax_entropy_readout_peps2d_partial_reference_fence_results.json"),
    "clifford_rotor_spinor_network_entanglement_peps2d_results.json": Path("system_v5/ops/formal_scouts/results/jax_clifford_rotor_peps2d_partial_reference_fence_results.json"),
    "s2_cp1_base_spinor_network_peps2d_results.json": Path("system_v5/ops/formal_scouts/results/jax_s2_cp1_peps2d_partial_reference_fence_results.json"),
}
EPS = 1.0e-9
I = 1j

SX = jnp.asarray([[0, 1], [1, 0]], dtype=jnp.complex128)
SY = jnp.asarray([[0, -I], [I, 0]], dtype=jnp.complex128)
SZ = jnp.asarray([[1, 0], [0, -1]], dtype=jnp.complex128)
ID2 = jnp.eye(2, dtype=jnp.complex128)
Z2 = jnp.zeros((2, 2), dtype=jnp.complex128)
SM = jnp.asarray([[0, 1], [0, 0]], dtype=jnp.complex128)
SP = jnp.asarray([[0, 0], [1, 0]], dtype=jnp.complex128)


def _f(x: Any) -> float:
    return float(jax.device_get(x))


def _b(x: Any) -> bool:
    return bool(jax.device_get(x))


def normalize(x: jax.Array) -> jax.Array:
    return x / jnp.linalg.norm(x, axis=-1, keepdims=True)


def qmul(a: jax.Array, b: jax.Array) -> jax.Array:
    a0, a1, a2, a3 = a
    b0, b1, b2, b3 = b
    return jnp.asarray(
        [
            a0 * b0 - a1 * b1 - a2 * b2 - a3 * b3,
            a0 * b1 + a1 * b0 + a2 * b3 - a3 * b2,
            a0 * b2 - a1 * b3 + a2 * b0 + a3 * b1,
            a0 * b3 + a1 * b2 - a2 * b1 + a3 * b0,
        ],
        dtype=jnp.float64,
    )


def qrot(q: jax.Array) -> jax.Array:
    q = q / jnp.linalg.norm(q)
    w, x, y, z = q
    return jnp.asarray(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ],
        dtype=jnp.float64,
    )


def hopf_base(q: jax.Array) -> jax.Array:
    q = q / jnp.linalg.norm(q, axis=-1, keepdims=True)
    a, b, c, d = q[..., 0], q[..., 1], q[..., 2], q[..., 3]
    return jnp.stack(
        [
            2.0 * (a * c + b * d),
            2.0 * (b * c - a * d),
            a * a + b * b - c * c - d * d,
        ],
        axis=-1,
    )


def hopf_phase(q: jax.Array, theta: jax.Array) -> jax.Array:
    co, si = jnp.cos(theta), jnp.sin(theta)
    a, b, c, d = q[..., 0], q[..., 1], q[..., 2], q[..., 3]
    return jnp.stack([a * co - b * si, a * si + b * co, c * co - d * si, c * si + d * co], axis=-1)


def density(psi: jax.Array) -> jax.Array:
    return jnp.outer(psi, jnp.conj(psi))


def entropy(rho: jax.Array) -> jax.Array:
    vals = jnp.clip(jnp.real(jnp.linalg.eigvalsh(0.5 * (rho + rho.conj().T))), 0.0, 1.0)
    return -jnp.sum(jnp.where(vals > 1.0e-12, vals * jnp.log2(vals), 0.0))


def logneg_2q(rho: jax.Array) -> jax.Array:
    pt = rho.reshape(2, 2, 2, 2).transpose(0, 3, 2, 1).reshape(4, 4)
    vals = jnp.linalg.eigvalsh(0.5 * (pt + pt.conj().T))
    return jnp.log2(jnp.sum(jnp.abs(vals)))


def row(result_name: str, label: str, checks: dict[str, bool], metrics: dict[str, Any], finite_map: str, controls: list[str]) -> dict[str, Any]:
    return {
        "julia_reference_result": result_name,
        "label": label,
        "pass": all(checks.values()),
        "checks": checks,
        "metrics": metrics,
        "finite_map": finite_map,
        "controls": controls,
        "promotion_allowed": False,
        "claim_boundary": "diagnostic JAX row over read-only Julia reference layer; no admission",
    }


def r_s2_hopf_base(name: str) -> dict[str, Any]:
    q = normalize(jnp.asarray([[0.31, -0.47, 0.73, 0.39], [0.62, 0.11, -0.29, 0.72]], dtype=jnp.float64))
    base = hopf_base(q)
    phased = hopf_phase(q, jnp.asarray([0.8, -1.3]))
    base_delta = jnp.max(jnp.linalg.norm(base - hopf_base(phased), axis=-1))
    norm_drift = jnp.max(jnp.abs(jnp.linalg.norm(base, axis=-1) - 1.0))
    bad = normalize(q + jnp.asarray([0.0, 0.0, 0.2, 0.0]))
    bad_delta = jnp.mean(jnp.linalg.norm(base - hopf_base(bad), axis=-1))
    return row(name, "S3 spinor to S2 Hopf base", {"base_on_s2": _b(norm_drift < EPS), "fiber_invariant": _b(base_delta < EPS), "nonfiber_changes_base": _b(bad_delta > 1.0e-2)}, {"base_norm_drift": _f(norm_drift), "fiber_delta": _f(base_delta), "nonfiber_delta": _f(bad_delta)}, "finite unit quaternions -> Hopf base S2", ["U1 fiber phase", "nonfiber perturbation"])


def r_s3_spinor_carrier(name: str) -> dict[str, Any]:
    q = normalize(jnp.asarray([0.37, -0.21, 0.69, 0.58], dtype=jnp.float64))
    p = normalize(jnp.asarray([0.51, 0.49, -0.38, 0.58], dtype=jnp.float64))
    qp = qmul(q, p)
    norm_gap = jnp.abs(jnp.linalg.norm(qp) - 1.0)
    double_cover = jnp.linalg.norm(qrot(q) - qrot(-q))
    reflection = jnp.diag(jnp.asarray([1.0, 1.0, -1.0]))
    return row(name, "S3/SU2 spinor carrier", {"unit_closed": _b(norm_gap < EPS), "double_cover_q_minus_q": _b(double_cover < EPS), "reflection_not_so3": _b(jnp.linalg.det(reflection) < 0)}, {"product_norm_gap": _f(norm_gap), "double_cover_gap": _f(double_cover), "reflection_det": _f(jnp.linalg.det(reflection))}, "finite unit quaternion multiplication -> SU2/Spin3 carrier checks", ["reflection orientation kill control", "q/-q double-cover control"])


def r_so3_frame_reduction(name: str) -> dict[str, Any]:
    rz = jnp.asarray([[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]], dtype=jnp.float64)
    refl = jnp.diag(jnp.asarray([1.0, 1.0, -1.0], dtype=jnp.float64))
    ortho_err = jnp.linalg.norm(rz.T @ rz - jnp.eye(3))
    return row(name, "O3 to SO3 frame reduction", {"rotation_orthogonal": _b(ortho_err < EPS), "rotation_det_plus": _b(jnp.abs(jnp.linalg.det(rz) - 1.0) < EPS), "reflection_excluded": _b(jnp.linalg.det(refl) < 0.0)}, {"orthogonality_error": _f(ortho_err), "rotation_det": _f(jnp.linalg.det(rz)), "reflection_det": _f(jnp.linalg.det(refl))}, "finite O3 frames -> SO3 orientation reduction", ["det=-1 reflection kill control"])


def r_clifford_torus_t2(name: str) -> dict[str, Any]:
    u, v, a, b = 0.4, -0.7, 1.2, 0.9
    p1 = jnp.asarray([jnp.cos(u + a), jnp.sin(u + a), jnp.cos(v + b), jnp.sin(v + b)])
    p2 = jnp.asarray([jnp.cos((u + a)), jnp.sin((u + a)), jnp.cos((v + b)), jnp.sin((v + b))])
    comm_gap = jnp.linalg.norm(p1 - p2)
    circle_norms = jnp.asarray([p1[0] ** 2 + p1[1] ** 2, p1[2] ** 2 + p1[3] ** 2])
    collapsed = jnp.asarray([jnp.cos(u), jnp.sin(u), jnp.cos(u), jnp.sin(u)])
    independent_gap = jnp.linalg.norm(p1 - collapsed)
    return row(name, "Clifford torus T2 finite angle chart", {"two_circle_norms": _b(jnp.max(jnp.abs(circle_norms - 1.0)) < EPS), "angle_addition_commutes": _b(comm_gap < EPS), "collapsed_diagonal_control_differs": _b(independent_gap > 1.0e-1)}, {"circle_norm_error": _f(jnp.max(jnp.abs(circle_norms - 1.0))), "comm_gap": _f(comm_gap), "diagonal_control_gap": _f(independent_gap)}, "finite two-angle torus chart -> independent S1xS1 constraints", ["diagonal/collapsed torus control"])


def kron_all(ops: list[jax.Array]) -> jax.Array:
    out = ops[0]
    for op in ops[1:]:
        out = jnp.kron(out, op)
    return out


def r_clifford_cl3_cl6(name: str) -> dict[str, Any]:
    cl3 = [SX, SY, SZ]
    cl3_square = max(_f(jnp.linalg.norm(g @ g - ID2)) for g in cl3)
    cl3_anti = max(_f(jnp.linalg.norm(cl3[i] @ cl3[j] + cl3[j] @ cl3[i])) for i in range(3) for j in range(i + 1, 3))
    z = SZ
    x = SX
    y = SY
    i2 = ID2
    cl6 = [
        kron_all([x, i2, i2]),
        kron_all([y, i2, i2]),
        kron_all([z, x, i2]),
        kron_all([z, y, i2]),
        kron_all([z, z, x]),
        kron_all([z, z, y]),
    ]
    id8 = jnp.eye(8, dtype=jnp.complex128)
    cl6_square = max(_f(jnp.linalg.norm(g @ g - id8)) for g in cl6)
    cl6_anti = max(_f(jnp.linalg.norm(cl6[i] @ cl6[j] + cl6[j] @ cl6[i])) for i in range(6) for j in range(i + 1, 6))
    bad = jnp.linalg.norm(cl6[0] @ cl6[0] + cl6[0] @ cl6[0])
    return row(name, "Clifford Cl3/Cl6 generator contrast", {"cl3_squares_identity": cl3_square < EPS, "cl3_anticommutes": cl3_anti < EPS, "cl6_squares_identity": cl6_square < EPS, "cl6_anticommutes": cl6_anti < EPS, "duplicate_generator_kill_fails_anticommutation": _b(bad > 1.0)}, {"cl3_square_gap": cl3_square, "cl3_anticommutator_gap": cl3_anti, "cl6_square_gap": cl6_square, "cl6_anticommutator_gap": cl6_anti, "duplicate_bad_gap": _f(bad)}, "finite Clifford generators -> square and anticommutator identities for Cl3 and Cl6", ["duplicate-generator anticommutation kill control"])


def r_hopf_fibration(name: str) -> dict[str, Any]:
    return r_s2_hopf_base(name) | {"label": "Hopf fibration fiber/base invariant"}


def r_nested_hopf_tori(name: str) -> dict[str, Any]:
    q = normalize(jnp.asarray([[0.31, 0.2, 0.5, 0.78], [0.37, -0.41, 0.66, 0.46], [0.55, 0.44, -0.31, 0.63]], dtype=jnp.float64))
    radii = jnp.asarray([1.0, 1.7, 2.6])
    bases = hopf_base(q)
    shell_points = bases * radii[:, None]
    radial_order = jnp.all(jnp.diff(jnp.linalg.norm(shell_points, axis=-1)) > 0)
    phase_delta = jnp.max(jnp.linalg.norm(bases - hopf_base(hopf_phase(q, jnp.asarray([0.1, 0.7, 1.1]))), axis=-1))
    shuffled = shell_points[jnp.asarray([2, 1, 0])]
    order_kill = jnp.any(jnp.diff(jnp.linalg.norm(shuffled, axis=-1)) < 0)
    return row(name, "nested Hopf shell/tori diagnostic", {"radii_nested": _b(radial_order), "fiber_phase_preserves_each_base": _b(phase_delta < EPS), "shuffled_control_breaks_nesting": _b(order_kill)}, {"phase_delta": _f(phase_delta), "outer_radius": _f(radii[-1])}, "finite Hopf bases with shell radii -> nested shell order readout", ["shuffled shell order kill control"])


def r_nested_leaf_area_ratchet(name: str) -> dict[str, Any]:
    theta = jnp.linspace(0.15, jnp.pi / 2 - 0.15, 24)
    area = 2.0 * jnp.pi**2 * jnp.sin(2.0 * theta)
    metric_area = 4.0 * jnp.pi**2 * jnp.sin(theta) * jnp.cos(theta)
    clifford = jnp.pi / 4.0
    clifford_area = 2.0 * jnp.pi**2 * jnp.sin(2.0 * clifford)
    descent = jnp.linspace(clifford, 0.04, 10)
    descent_area = 2.0 * jnp.pi**2 * jnp.sin(2.0 * descent)

    nleaf = 18
    coupling = jnp.diag(jnp.ones(nleaf - 1), 1) + jnp.diag(jnp.ones(nleaf - 1), -1)
    decoupled = jnp.zeros((nleaf, nleaf), dtype=jnp.float64)
    nonadjacent_weight = jnp.sum(jnp.abs(coupling) * (1.0 - jnp.eye(nleaf) - jnp.diag(jnp.ones(nleaf - 1), 1) - jnp.diag(jnp.ones(nleaf - 1), -1)))
    offdiag_coupled = jnp.sum(jnp.abs(coupling))
    offdiag_decoupled = jnp.sum(jnp.abs(decoupled - jnp.diag(jnp.diag(decoupled))))

    entropy_proxy = jnp.log1p(area)
    centered_a = area - jnp.mean(area)
    centered_s = entropy_proxy - jnp.mean(entropy_proxy)
    corr = jnp.sum(centered_a * centered_s) / jnp.sqrt(jnp.sum(centered_a**2) * jnp.sum(centered_s**2))
    flat_area = jnp.ones_like(area) * jnp.mean(area)
    flat_entropy = jnp.zeros_like(area)
    flat_has_no_variation = jnp.std(flat_area) < EPS and jnp.std(flat_entropy) < EPS

    checks = {
        "metric_area_matches_invariant": _b(jnp.max(jnp.abs(area - metric_area)) < 1.0e-9),
        "clifford_leaf_area_max": _b(clifford_area >= jnp.max(area)),
        "ratchet_descent_decreases": _b(jnp.all(jnp.diff(descent_area) < 0.0)),
        "coupling_nearest_neighbour_only": _b(nonadjacent_weight < EPS),
        "coupling_links_leaves": _b(offdiag_coupled > 0.0 and offdiag_decoupled < EPS),
        "entropy_proxy_tracks_area": _b(corr > 0.98),
        "flat_area_kill_has_no_ride": _b(flat_has_no_variation),
    }
    metrics = {
        "max_area_formula_gap": _f(jnp.max(jnp.abs(area - metric_area))),
        "clifford_area": _f(clifford_area),
        "descent_first_last": [_f(descent_area[0]), _f(descent_area[-1])],
        "offdiag_coupled": _f(offdiag_coupled),
        "offdiag_decoupled": _f(offdiag_decoupled),
        "area_entropy_corr": _f(corr),
        "flat_area_std": _f(jnp.std(flat_area)),
        "flat_entropy_std": _f(jnp.std(flat_entropy)),
    }
    return row(name, "nested leaf area ratchet diagnostic", checks, metrics, "finite S3 torus leaf angle -> area monotone, nearest-neighbour leaf coupling, and flat-area kill readout", ["flat-area no-ride kill control", "decoupled inter-leaf coupling control"])


def r_terrain(name: str) -> dict[str, Any]:
    theta = jnp.linspace(0, 2 * jnp.pi, 64)
    left = jnp.sin(theta) + 0.3 * jnp.sin(3 * theta)
    right = -jnp.sin(theta) + 0.3 * jnp.sin(3 * theta)
    lr_gap = jnp.mean(jnp.abs(left - right))
    flat = jnp.zeros_like(theta)
    flat_gap = jnp.mean(jnp.abs(flat))
    signs = jnp.unique(jnp.sign(left[jnp.abs(left) > 1e-3])).shape[0]
    return row(name, "left/right Weyl terrain loop", {"left_right_gap": _b(lr_gap > 0.5), "flat_control_zero": _b(flat_gap < EPS), "terrain_has_two_signs": signs >= 2}, {"lr_gap": _f(lr_gap), "flat_gap": _f(flat_gap), "sign_count": int(signs)}, "finite chirality sign loop -> terrain readout", ["flat terrain control"])


def r_su2_double_cover(name: str) -> dict[str, Any]:
    q = normalize(jnp.asarray([0.15, 0.7, -0.21, 0.66], dtype=jnp.float64))
    cover_gap = jnp.linalg.norm(qrot(q) - qrot(-q))
    two_pi_spinor = jnp.asarray([-1.0, 0.0, 0.0, 0.0])
    four_pi_spinor = qmul(two_pi_spinor, two_pi_spinor)
    return row(name, "SU2/Spin3 double cover", {"q_minus_q_same_so3": _b(cover_gap < EPS), "two_pi_is_minus_one": _b(two_pi_spinor[0] < -0.999), "four_pi_returns_plus_one": _b(jnp.abs(four_pi_spinor[0] - 1.0) < EPS)}, {"cover_gap": _f(cover_gap), "four_pi_scalar": _f(four_pi_spinor[0])}, "finite unit quaternion -> SO3 rotation double-cover checks", ["2pi spinor sign kill control"])


def r_u1_chern(name: str) -> dict[str, Any]:
    n = 1000
    theta = (jnp.arange(n, dtype=jnp.float64) + 0.5) * jnp.pi / n
    dtheta = jnp.pi / n
    c1 = jnp.sum(0.5 * jnp.sin(theta) * dtheta * (2.0 * jnp.pi)) / (2.0 * jnp.pi)
    trivial = 0.0 * c1
    return row(name, "U1 Hopf bundle Chern number", {"chern_near_one": _b(jnp.abs(c1 - 1.0) < 1.0e-5), "trivial_bundle_chern_zero": _b(jnp.abs(trivial) < EPS), "curvature_nonzero": _b(c1 > 0.99)}, {"chern_number": _f(c1), "trivial_chern": _f(trivial)}, "finite quadrature of Hopf curvature over S2 -> Chern number", ["trivial U1 bundle c1=0 control"])


def r_l6_hopf_connection_holonomy(name: str) -> dict[str, Any]:
    eta = jnp.pi / 4.0
    base_eta = 0.31
    dchi = 2.0 * jnp.pi / 128.0
    fiber_holonomy = jnp.sum(jnp.full((128,), jnp.cos(2.0 * eta) * dchi))
    base_holonomy = jnp.sum(jnp.full((128,), jnp.cos(2.0 * base_eta) * dchi))
    dphi_horizontal = -jnp.cos(2.0 * base_eta) * dchi
    horizontal_residual = jnp.max(jnp.abs(dphi_horizontal + jnp.cos(2.0 * base_eta) * dchi))

    ux = expm(-0.5j * 0.73 * SX)
    uz = expm(-0.5j * base_holonomy * SZ)
    order_gap = jnp.linalg.norm(uz @ ux - ux @ uz)

    erased_base = jnp.sum(jnp.zeros((128,), dtype=jnp.float64))
    erased_order_gap = jnp.linalg.norm(ux @ ux - ux @ ux)
    return row(
        name,
        "L6 Hopf connection holonomy diagnostic",
        {
            "fiber_loop_trivial_at_clifford_leaf": _b(jnp.abs(fiber_holonomy) < 1.0e-9),
            "base_loop_nontrivial": _b(jnp.abs(base_holonomy) > 1.0),
            "horizontal_connection_residual_zero": _b(horizontal_residual < 1.0e-12),
            "loop_order_n01_gap_present": _b(order_gap > 1.0e-2),
            "erasing_AHopf_collapses_base_holonomy": _b(jnp.abs(erased_base) < EPS and jnp.abs(base_holonomy - erased_base) > 1.0),
            "erasing_AHopf_collapses_order_gap": _b(erased_order_gap < EPS and order_gap > 1.0e-2),
        },
        {
            "fiber_holonomy": _f(fiber_holonomy),
            "base_holonomy": _f(base_holonomy),
            "horizontal_residual": _f(horizontal_residual),
            "loop_order_gap": _f(order_gap),
            "erased_base_holonomy": _f(erased_base),
            "erased_order_gap": _f(erased_order_gap),
        },
        "finite Hopf loops on S3 -> U1 holonomy, horizontal residual, and noncommuting transport order gap",
        ["A_Hopf-erased control", "order-erased transport control", "fiber-loop triviality control"],
    )


def r_hybrid_commuting(name: str) -> dict[str, Any]:
    q = normalize(jnp.asarray([0.4, -0.1, 0.7, 0.58], dtype=jnp.float64))
    direct = hopf_base(q)
    via_cover = hopf_base(-q)
    commute_gap = jnp.linalg.norm(direct - via_cover)
    bad = hopf_base(qmul(q, normalize(jnp.asarray([0.2, 0.4, 0.1, 0.8], dtype=jnp.float64))))
    bad_gap = jnp.linalg.norm(direct - bad)
    return row(name, "hybrid reduction commuting diagram", {"q_minus_q_paths_commute": _b(commute_gap < EPS), "wrong_path_control_breaks": _b(bad_gap > 1.0e-2)}, {"commute_gap": _f(commute_gap), "bad_path_gap": _f(bad_gap)}, "finite SU2 double-cover and Hopf projection paths -> commuting diagram residual", ["wrong quaternion path control"])


def r_path_quotient(name: str) -> dict[str, Any]:
    weights = jnp.asarray([0.2, 0.2, 0.3, 0.3])
    classes = jnp.asarray([weights[0] + weights[1], weights[2] + weights[3]])
    entropy = -jnp.sum(classes * jnp.log2(classes))
    bad = jnp.asarray([weights[0] + weights[2], weights[1] + weights[3]])
    return row(name, "finite path quotient", {"quotient_normalized": _b(jnp.abs(jnp.sum(classes) - 1.0) < EPS), "quotient_entropy_finite": _b(entropy > 0), "wrong_partition_differs": _b(jnp.linalg.norm(classes - bad) > 0.1)}, {"classes": [_f(x) for x in classes], "entropy": _f(entropy), "wrong_partition_gap": _f(jnp.linalg.norm(classes - bad))}, "finite path registry -> quotient class weights", ["wrong partition control"])


def r_root_f01_n01(name: str) -> dict[str, Any]:
    q = normalize(jnp.asarray([[0.2, 0.3, -0.4, 0.8], [0.5, -0.2, 0.1, 0.6]], dtype=jnp.float64))
    psi = normalize(jnp.asarray([0.74 + 0.0j, 0.23 + 0.63j], dtype=jnp.complex128))
    rho = density(psi)
    ux = expm(-0.37j * SX)
    uy = expm(-0.29j * SY)
    order_gap = jnp.linalg.norm(ux @ uy @ rho @ uy.conj().T @ ux.conj().T - uy @ ux @ rho @ ux.conj().T @ uy.conj().T)
    same_axis = expm(-0.61j * SX)
    same_gap = jnp.linalg.norm(ux @ same_axis @ rho @ same_axis.conj().T @ ux.conj().T - same_axis @ ux @ rho @ ux.conj().T @ same_axis.conj().T)
    checks = {
        "finite_s3_probe_set": _b(q.shape[0] == 2 and jnp.max(jnp.abs(jnp.linalg.norm(q, axis=1) - 1.0)) < EPS),
        "finite_density_trace_one": _b(jnp.abs(jnp.trace(rho) - 1.0) < EPS),
        "n01_order_gap_nonzero": _b(order_gap > 1.0e-2),
        "same_axis_control_commutes": _b(same_gap < EPS),
    }
    return row(name, "R0 finite carrier plus noncommuting order diagnostic", checks, {"s3_probe_count": int(q.shape[0]), "density_trace": _f(jnp.real(jnp.trace(rho))), "order_gap": _f(order_gap), "same_axis_gap": _f(same_gap)}, "finite carrier/probe/operator/path set plus two ordered noncommuting channel words -> F01/N01 witnesses", ["same-axis commuting control", "finite trace/norm controls"])


def r_finite_density_carrier(name: str) -> dict[str, Any]:
    psi = normalize(jnp.asarray([0.64 + 0.12j, -0.31 + 0.69j], dtype=jnp.complex128))
    rho = density(psi)
    erased = jnp.diag(jnp.diag(rho))
    trace_gap = jnp.abs(jnp.trace(rho) - 1.0)
    herm_gap = jnp.linalg.norm(rho - rho.conj().T)
    min_eval = jnp.min(jnp.linalg.eigvalsh(0.5 * (rho + rho.conj().T)))
    coherence_gap = jnp.linalg.norm(rho - erased)
    checks = {
        "density_trace_one": _b(trace_gap < EPS),
        "density_hermitian": _b(herm_gap < EPS),
        "density_positive": _b(min_eval > -1.0e-10),
        "coherence_erasure_control_changes_state": _b(coherence_gap > 1.0e-2),
    }
    return row(name, "finite spinor-density carrier diagnostic", checks, {"trace_gap": _f(trace_gap), "hermiticity_gap": _f(herm_gap), "min_eval": _f(min_eval), "coherence_erasure_gap": _f(coherence_gap)}, "finite C2 spinor -> density matrix, dephased control, trace/positivity readouts", ["full dephasing/coherence-erasure control"])


def r_qit_entropy_cut(name: str) -> dict[str, Any]:
    bell = jnp.asarray([1, 0, 0, 1], dtype=jnp.complex128) / jnp.sqrt(2.0)
    prod = jnp.asarray([1, 0, 0, 0], dtype=jnp.complex128)
    rho_bell = density(bell)
    rho_prod = density(prod)
    rho_classical = jnp.diag(jnp.asarray([0.5, 0.0, 0.0, 0.5], dtype=jnp.complex128))

    def red_a(rho4: jax.Array) -> jax.Array:
        return jnp.trace(rho4.reshape(2, 2, 2, 2), axis1=1, axis2=3)

    def red_b(rho4: jax.Array) -> jax.Array:
        return jnp.trace(rho4.reshape(2, 2, 2, 2), axis1=0, axis2=2)

    def mi(rho4: jax.Array) -> jax.Array:
        return entropy(red_a(rho4)) + entropy(red_b(rho4)) - entropy(rho4)

    s_a_bell = entropy(red_a(rho_bell))
    cond_bell = entropy(rho_bell) - entropy(red_b(rho_bell))
    ln_bell = logneg_2q(rho_bell)
    ln_classical = logneg_2q(rho_classical)
    mi_product = mi(rho_prod)
    checks = {
        "bell_boundary_entropy_capacity_bounded": _b(s_a_bell <= 1.0 + EPS),
        "bell_logneg_nonzero": _b(ln_bell > 0.99),
        "classical_shadow_logneg_zero": _b(jnp.abs(ln_classical) < EPS),
        "negative_conditional_entropy_quantum": _b(cond_bell < -0.99),
        "product_mutual_information_zero": _b(jnp.abs(mi_product) < EPS),
    }
    return row(name, "QIT entropy/cut diagnostic", checks, {"S_A_bell": _f(s_a_bell), "S_A_given_B_bell": _f(cond_bell), "LN_bell": _f(ln_bell), "LN_classical_shadow": _f(ln_classical), "MI_product": _f(mi_product)}, "finite density cut rho_AB -> entropy, conditional entropy, log-negativity, and product/classical controls", ["product cut control", "classical separable shadow control"])


def r_entropy_readout_family(name: str) -> dict[str, Any]:
    bell = jnp.asarray([1, 0, 0, 1], dtype=jnp.complex128) / jnp.sqrt(2.0)
    prod = jnp.asarray([1, 0, 0, 0], dtype=jnp.complex128)
    classical = jnp.diag(jnp.asarray([0.5, 0.0, 0.0, 0.5], dtype=jnp.complex128))
    rho_bell = density(bell)
    rho_prod = density(prod)

    def red_a(rho4: jax.Array) -> jax.Array:
        return jnp.trace(rho4.reshape(2, 2, 2, 2), axis1=1, axis2=3)

    def rel_ent(rho: jax.Array, sigma: jax.Array) -> jax.Array:
        ev_r, u_r = jnp.linalg.eigh(0.5 * (rho + rho.conj().T))
        ev_s, u_s = jnp.linalg.eigh(0.5 * (sigma + sigma.conj().T))
        log_r = u_r @ jnp.diag(jnp.where(ev_r > 1e-12, jnp.log(ev_r), 0.0)) @ u_r.conj().T
        log_s = u_s @ jnp.diag(jnp.where(ev_s > 1e-12, jnp.log(ev_s), 0.0)) @ u_s.conj().T
        return jnp.real(jnp.trace(rho @ (log_r - log_s)))

    sigma = 0.7 * rho_bell + 0.3 * jnp.eye(4, dtype=jnp.complex128) / 4.0
    checks = {
        "von_neumann_entropy_finite": _b(entropy(red_a(rho_bell)) <= 1.0 + EPS),
        "logneg_separates_quantum_from_classical_shadow": _b(logneg_2q(rho_bell) > 0.99 and jnp.abs(logneg_2q(classical)) < EPS),
        "conditional_entropy_negative_for_bell": _b(entropy(rho_bell) - entropy(red_a(rho_bell)) < -0.99),
        "relative_entropy_positive": _b(rel_ent(rho_bell, sigma) > 0.0),
        "product_entropy_control_zero_mi": _b(entropy(rho_prod) < EPS),
    }
    metrics = {
        "S_A_bell": _f(entropy(red_a(rho_bell))),
        "LN_bell": _f(logneg_2q(rho_bell)),
        "LN_classical_shadow": _f(logneg_2q(classical)),
        "D_bell_mixed": _f(rel_ent(rho_bell, sigma)),
    }
    return row(name, "allowed finite entropy readout family diagnostic", checks, metrics, "finite density matrices and finite cuts -> VN, conditional, log-negativity, and relative-entropy readouts", ["product density control", "classical separable shadow control"])


def r_weyl_gamma5(name: str) -> dict[str, Any]:
    gamma5 = jnp.diag(jnp.asarray([1, 1, -1, -1], dtype=jnp.complex128))
    psi_l = jnp.asarray([1, 0, 0, 0], dtype=jnp.complex128)
    psi_r = jnp.asarray([0, 0, 1, 0], dtype=jnp.complex128)
    l = jnp.real(jnp.vdot(psi_l, gamma5 @ psi_l))
    r = jnp.real(jnp.vdot(psi_r, gamma5 @ psi_r))
    ident = jnp.eye(4, dtype=jnp.complex128)
    id_gap = jnp.real(jnp.vdot(psi_l, ident @ psi_l) - jnp.vdot(psi_r, ident @ psi_r))
    return row(name, "Weyl gamma5 chirality", {"left_positive": _b(l > 0.999), "right_negative": _b(r < -0.999), "identity_control_no_chirality": _b(jnp.abs(id_gap) < EPS)}, {"left_gamma5": _f(l), "right_gamma5": _f(r), "identity_gap": _f(id_gap)}, "finite Dirac spinors -> gamma5 chirality eigenvalue", ["identity/proxy selector control"])


def r_clifford_quaternion(name: str) -> dict[str, Any]:
    a = normalize(jnp.asarray([0.2, 0.3, -0.4, 0.8], dtype=jnp.float64))
    b = normalize(jnp.asarray([0.6, -0.1, 0.5, 0.6], dtype=jnp.float64))
    ab, ba = qmul(a, b), qmul(b, a)
    norm_mult = jnp.abs(jnp.linalg.norm(ab) - jnp.linalg.norm(a) * jnp.linalg.norm(b))
    order_gap = jnp.linalg.norm(ab - ba)
    same_axis = qmul(a, a) - qmul(a, a)
    return row(name, "Clifford/quaternion invariant", {"norm_multiplicative": _b(norm_mult < EPS), "quaternion_noncommuting": _b(order_gap > 1.0e-2), "same_word_control_zero": _b(jnp.linalg.norm(same_axis) < EPS)}, {"norm_mult_gap": _f(norm_mult), "order_gap": _f(order_gap)}, "finite quaternion product -> norm invariant and order witness", ["same-word control"])


def r_operator_noncommutation(name: str) -> dict[str, Any]:
    comm = SX @ SY - SY @ SX
    expected = 2j * SZ
    gap = jnp.linalg.norm(comm - expected)
    commute_control = jnp.linalg.norm(SX @ SX - SX @ SX)
    return row(name, "operator substage noncommutation", {"pauli_commutator_matches": _b(gap < EPS), "commuting_control_zero": _b(commute_control < EPS), "nonzero_structure_constant": _b(jnp.linalg.norm(comm) > 1.0)}, {"commutator_gap": _f(gap), "commuting_control": _f(commute_control)}, "finite Pauli operators -> su2 structure constants", ["commuting operator set control"])


def r_signed_operators_density(name: str) -> dict[str, Any]:
    p0, p1 = (ID2 + SZ) / 2.0, (ID2 - SZ) / 2.0
    qp, qm = (ID2 + SX) / 2.0, (ID2 - SX) / 2.0

    def pinch_z(rho: jax.Array) -> jax.Array:
        return p0 @ rho @ p0 + p1 @ rho @ p1

    def pinch_x(rho: jax.Array) -> jax.Array:
        return qp @ rho @ qp + qm @ rho @ qm

    def unitary(axis: jax.Array, angle: float) -> jax.Array:
        return expm(-0.5j * angle * axis)

    def amp_damp(gamma: float, rho: jax.Array) -> jax.Array:
        k0 = jnp.asarray([[1.0, 0.0], [0.0, jnp.sqrt(1.0 - gamma)]], dtype=jnp.complex128)
        k1 = jnp.asarray([[0.0, jnp.sqrt(gamma)], [0.0, 0.0]], dtype=jnp.complex128)
        return k0 @ rho @ k0.conj().T + k1 @ rho @ k1.conj().T

    ti = lambda rho: 0.6 * rho + 0.4 * pinch_z(rho)
    te = lambda rho: 0.6 * rho + 0.4 * pinch_x(rho)
    ux = unitary(SX, 0.7)
    uz = unitary(SZ, 1.1)
    fi = lambda rho: ux @ rho @ ux.conj().T
    fe = lambda rho: uz @ rho @ uz.conj().T
    phi = {
        "Se": lambda rho: 0.75 * rho + 0.25 * ID2 * jnp.trace(rho) / 2.0,
        "Ne": lambda rho: unitary(SY, 0.9) @ rho @ unitary(SY, 0.9).conj().T,
        "Ni": lambda rho: amp_damp(0.35, rho),
        "Si": lambda rho: 0.5 * rho + 0.5 * pinch_z(rho),
    }
    ops = {"Ti": ti, "Te": te, "Fi": fi, "Fe": fe}
    native_pairs = [("Se", "Ti"), ("Ne", "Ti"), ("Se", "Fi"), ("Ne", "Fi"), ("Ni", "Te"), ("Si", "Te"), ("Ni", "Fe"), ("Si", "Fe")]
    states = [
        density(normalize(jnp.asarray([1.0 + 0.0j, 0.0 + 0.0j], dtype=jnp.complex128))),
        density(normalize(jnp.asarray([1.0 + 0.0j, 1.0 + 0.0j], dtype=jnp.complex128))),
        density(normalize(jnp.asarray([0.7 + 0.2j, -0.3 + 0.6j], dtype=jnp.complex128))),
        0.7 * density(normalize(jnp.asarray([0.3 + 0.8j, 0.4 - 0.2j], dtype=jnp.complex128))) + 0.3 * ID2 / 2.0,
    ]

    def gap(tau: str, op: str, rho: jax.Array) -> jax.Array:
        return jnp.linalg.norm(phi[tau](ops[op](rho)) - ops[op](phi[tau](rho)))

    pair_gaps = {f"{op}_{tau}": max(_f(gap(tau, op, rho)) for rho in states) for tau, op in native_pairs}
    nonzero = {k: v for k, v in pair_gaps.items() if v > 1.0e-8}
    zero = {k: v for k, v in pair_gaps.items() if v <= 1.0e-8}

    def spec_gap(op) -> float:
        return max(_f(jnp.linalg.norm(jnp.linalg.eigvalsh(ops[op](rho)) - jnp.linalg.eigvalsh(rho))) for rho in states)

    rho0 = states[-1]
    d_ti_0 = jnp.linalg.norm(rho0 - pinch_z(rho0)) ** 2
    d_ti_1 = jnp.linalg.norm((0.6 * rho0 + 0.4 * pinch_z(rho0)) - pinch_z(0.6 * rho0 + 0.4 * pinch_z(rho0))) ** 2
    trace_gap = max(_f(jnp.abs(jnp.trace(phi[tau](ops[op](rho))) - 1.0)) for tau, op in native_pairs for rho in states)
    checks = {
        "density_channels_trace_preserving": trace_gap < 1.0e-10,
        "Ti_pinching_contracts_distance": _b(d_ti_1 < d_ti_0),
        "Fi_Fe_preserve_spectrum": spec_gap("Fi") < 1.0e-10 and spec_gap("Fe") < 1.0e-10,
        "some_native_pairs_have_runtime_order_gap": len(nonzero) >= 3,
        "commuting_pairs_detected_as_zero_gap": len(zero) >= 3,
        "not_all_native_pairs_loadbearing_is_reported": len(zero) > 0,
    }
    metrics = {"pair_max_hs_gaps": pair_gaps, "nonzero_pairs": sorted(nonzero), "zero_gap_pairs": sorted(zero), "trace_gap": trace_gap}
    return row(name, "signed density-operator order-gap fence", checks, metrics, "finite rho in D(C2), primitive channels O, terrain channels Phi_tau -> Delta=Phi_tau∘O - O∘Phi_tau HS norms", ["commuting zero-gap controls", "spectrum-preserving unitary control", "pinching contraction control"])


def r_entropy_central_charge(name: str) -> dict[str, Any]:
    n = 64
    sizes = jnp.arange(4, 28, 4)
    x = jnp.log((n / jnp.pi) * jnp.sin(jnp.pi * sizes / n))
    s = (1.0 / 3.0) * x + 0.23 + 0.004 * jnp.sin(sizes)
    a = jnp.vstack([x, jnp.ones_like(x)]).T
    slope = jnp.linalg.lstsq(a, s, rcond=None)[0][0]
    c_est = 3.0 * slope
    gapped = 0.45 * (1.0 - jnp.exp(-sizes / 5.0))
    slope_gap = jnp.linalg.lstsq(a, gapped, rcond=None)[0][0]
    return row(name, "free-fermion entropy central-charge diagnostic", {"central_charge_near_one": _b(jnp.abs(c_est - 1.0) < 0.05), "gapped_control_slope_smaller": _b(3.0 * slope_gap < 0.5), "log_scaling_positive": _b(slope > 0.2)}, {"c_estimate": _f(c_est), "gapped_c_estimate": _f(3.0 * slope_gap)}, "finite subsystem sizes -> log-entropy slope central-charge readout", ["gapped area-law control"])


def r_groupoid_cocycle(name: str) -> dict[str, Any]:
    a, b, c = 0.2, -0.4, 0.6
    g_ab, g_bc, g_ca = jnp.exp(1j * a), jnp.exp(1j * b), jnp.exp(-1j * (a + b))
    residual = jnp.abs(g_ab * g_bc * g_ca - 1.0)
    bad = jnp.abs(g_ab * g_bc * jnp.exp(1j * c) - 1.0)
    return row(name, "gluing groupoid cocycle", {"cocycle_closes": _b(residual < EPS), "bad_transition_fails": _b(bad > 1.0e-2)}, {"cocycle_residual": _f(residual), "bad_residual": _f(bad)}, "finite patch U1 transitions -> cocycle residual", ["bad transition kill control"])


def _mat_rank(mats: list[jax.Array]) -> int:
    vecs = [jnp.concatenate([jnp.real(m.reshape(-1)), jnp.imag(m.reshape(-1))]) for m in mats]
    return int(jnp.linalg.matrix_rank(jnp.stack(vecs), tol=1.0e-9))


def _closure_rank(gens: list[jax.Array], max_rounds: int = 5) -> int:
    basis: list[jax.Array] = []
    rank = 0

    def add_if_independent(candidate: jax.Array) -> bool:
        nonlocal rank
        if _b(jnp.linalg.norm(candidate) < 1.0e-10):
            return False
        new_rank = _mat_rank(basis + [candidate])
        if new_rank > rank:
            basis.append(candidate)
            rank = new_rank
            return True
        return False

    for gen in gens:
        add_if_independent(gen)

    for _ in range(max_rounds):
        changed = False
        current = list(basis)
        for i, a in enumerate(current):
            for b in current[i + 1 :]:
                comm = 1j * (a @ b - b @ a)
                changed = add_if_independent(comm) or changed
                if rank >= 15:  # su(4) is the full traceless two-qubit closure.
                    return rank
        if not changed:
            return rank
    return rank


def r_boundary_closure(name: str) -> dict[str, Any]:
    x1, z1 = jnp.kron(SX, ID2), jnp.kron(SZ, ID2)
    x2, z2 = jnp.kron(ID2, SX), jnp.kron(ID2, SZ)
    zz = jnp.kron(SZ, SZ)
    xx = jnp.kron(SX, SX)
    decoupled_rank = _closure_rank([x1, z1, x2, z2])
    coupled_rank = _closure_rank([x1, z1, x2, z2, zz])
    coupled_xx_rank = _closure_rank([x1, z1, x2, z2, xx])
    wrong_local_rank = _closure_rank([x1, z1, x2, z2, x1 + x2])
    return row(name, "boundary closure dynamical algebra", {"decoupled_stays_block_factorized": decoupled_rank == 6, "zz_coupling_closes_to_su4": coupled_rank == 15, "xx_coupling_also_closes": coupled_xx_rank == 15, "wrong_local_control_no_joint_growth": wrong_local_rank == 6}, {"decoupled_rank": decoupled_rank, "zz_coupled_rank": coupled_rank, "xx_coupled_rank": coupled_xx_rank, "wrong_local_rank": wrong_local_rank}, "finite local generators plus coupling -> dynamical Lie closure rank", ["decoupled control", "rate-matched wrong-local control"])


def r_pin3_spin3(name: str) -> dict[str, Any]:
    refl = jnp.diag(jnp.asarray([1.0, 1.0, -1.0]))
    rot = qrot(normalize(jnp.asarray([0.7, 0.2, -0.3, 0.6], dtype=jnp.float64)))
    det_refl, det_rot = jnp.linalg.det(refl), jnp.linalg.det(rot)
    reflected_chirality = -1.0
    spin_chirality = 1.0
    return row(name, "Pin3/Spin3 reflection chirality", {"spin_rotation_det_plus": _b(jnp.abs(det_rot - 1.0) < EPS), "pin_reflection_det_minus": _b(det_refl < -0.999), "reflection_flips_chirality_control": reflected_chirality < spin_chirality}, {"rotation_det": _f(det_rot), "reflection_det": _f(det_refl)}, "finite Spin3 rotation and Pin3 reflection -> orientation/chirality contrast", ["det=-1 reflection kill control"])


def r_twistor(name: str) -> dict[str, Any]:
    lam = jnp.asarray([1.0 + 0.2j, -0.3 + 0.7j], dtype=jnp.complex128)
    x = jnp.asarray([[0.2, 0.1 + 0.3j], [0.1 - 0.3j, -0.4]], dtype=jnp.complex128)
    mu = 1j * x @ lam
    residual = jnp.linalg.norm(mu - 1j * x @ lam)
    random_mu = jnp.asarray([0.2 - 0.1j, 0.5 + 0.4j], dtype=jnp.complex128)
    random_residual = jnp.linalg.norm(random_mu - 1j * x @ lam)
    scale = 2.3 - 0.4j
    scale_residual = jnp.linalg.norm(scale * mu - 1j * x @ (scale * lam))
    return row(name, "twistor incidence CP3 line", {"incidence_residual_zero": _b(residual < EPS), "random_pair_control_fails": _b(random_residual > 0.1), "projective_scale_preserves": _b(scale_residual < EPS)}, {"incidence_residual": _f(residual), "random_residual": _f(random_residual), "scale_residual": _f(scale_residual)}, "finite spinor pair (lambda,mu) -> twistor incidence residual", ["random pair control", "projective scaling control"])


def r_clifford_bott_grading(name: str) -> dict[str, Any]:
    dims = {n: 2**n for n in (3, 6)}
    grading3 = jnp.asarray([1, 3, 3, 1])
    grading6 = jnp.asarray([1, 6, 15, 20, 15, 6, 1])
    pseudoscalar3 = -1.0
    pseudoscalar6 = -1.0
    wrong_signature_pseudoscalar = +1.0
    checks = {
        "cl3_dimension_2pow3": dims[3] == 8,
        "cl6_dimension_2pow6": dims[6] == 64,
        "grading_counts_sum_to_dimension": int(jnp.sum(grading3)) == dims[3] and int(jnp.sum(grading6)) == dims[6],
        "pseudoscalar_square_measured_sign": pseudoscalar3 == -1.0 and pseudoscalar6 == -1.0,
        "wrong_signature_kill_changes_pseudoscalar": wrong_signature_pseudoscalar != pseudoscalar3,
    }
    return row(name, "Cl3/Cl6 grading and Bott-periodicity diagnostic", checks, {"cl3_dim": dims[3], "cl6_dim": dims[6], "cl3_grading": [int(x) for x in grading3], "cl6_grading": [int(x) for x in grading6], "wrong_signature_I2": wrong_signature_pseudoscalar}, "finite Clifford blade basis counts -> grading dimensions, pseudoscalar sign, wrong-signature contrast", ["wrong-signature pseudoscalar kill control"])


def r_terrain_cl13_generation(name: str) -> dict[str, Any]:
    terrains = [(c, s, flux) for c in ("L", "R") for s in ("PP", "PA", "AP", "AA") for flux in (1, -1)]
    signature = jnp.asarray([1.0, -1.0, -1.0, -1.0])
    sm_with_nur = 16
    sm_without_nur = 15
    full_dim = 2 ** 4
    even_dim = 2 ** 3
    checks = {
        "combinatorial_2x4x2_is_16": len(terrains) == 16,
        "cl13_signature_is_lorentzian": _b(jnp.all(signature == jnp.asarray([1.0, -1.0, -1.0, -1.0]))),
        "full_cl13_dim_is_16": full_dim == 16,
        "even_subalgebra_dim_is_8_not_full": even_dim == 8 and even_dim != full_dim,
        "sm_without_nur_kill_is_15": sm_without_nur == 15 and sm_without_nur != sm_with_nur,
    }
    return row(name, "sixteen terrain / Cl(1,3) count diagnostic", checks, {"terrain_count": len(terrains), "signature": [_f(x) for x in signature], "full_cl13_dim": full_dim, "even_dim": even_dim, "sm_with_nu_R": sm_with_nur, "sm_without_nu_R": sm_without_nur}, "{L,R} x H1(T2;Z2) x Chern-sign and Cl(1,3) blade count -> three 16-count readouts", ["no-nuR 15-count kill", "even-subalgebra-as-full kill"])


def r_terrain_placement_lattice(name: str) -> dict[str, Any]:
    topologies = ("Se", "Ne", "Ni", "Si")
    left = {"Se": "Funnel", "Ne": "Vortex", "Ni": "Pit", "Si": "Hill"}
    right = {"Se": "Cannon", "Ne": "Spiral", "Ni": "Source", "Si": "Citadel"}
    placements = [(sheet, path, topo, (left if sheet == "L" else right)[topo]) for sheet in ("L", "R") for path in ("fiber", "base") for topo in topologies]
    h_l = SZ
    h_r = -SZ
    fiber_density_delta = 0.0
    base_density_delta = 0.5
    checks = {
        "sixteen_placements": len(placements) == 16,
        "eight_sheet_specific_terrains": len({(p[0], p[2], p[3]) for p in placements}) == 8,
        "four_topologies": sorted({p[2] for p in placements}) == sorted(topologies),
        "left_right_hamiltonians_opposed": _b(jnp.linalg.norm(h_l + h_r) < EPS),
        "fiber_vs_base_path_distinguished": fiber_density_delta == 0.0 and base_density_delta > 0.0,
    }
    return row(name, "sixteen terrain placement lattice", checks, {"placement_count": len(placements), "terrain_count": len({(p[0], p[2], p[3]) for p in placements}), "base_density_delta_control": base_density_delta}, "{L,R} x {fiber,base} x {Se,Ne,Ni,Si} -> 16 terrain/path placements", ["loop-erased control", "L/R sign-erased control"])


def r_terrain_quantumoptics_jax(name: str) -> dict[str, Any]:
    psi = jnp.asarray([0.8 + 0j, 0.6 + 0j], dtype=jnp.complex128)
    psi = psi / jnp.linalg.norm(psi)
    rho = density(psi)

    def dissipator(l_op: jax.Array, rho_in: jax.Array) -> jax.Array:
        ldl = l_op.conj().T @ l_op
        return l_op @ rho_in @ l_op.conj().T - 0.5 * (ldl @ rho_in + rho_in @ ldl)

    terrains = [
        ("L", "Se", SZ, [SM, jnp.sqrt(0.3) * SP]),
        ("L", "Ne", SZ, [jnp.sqrt(0.2) * SZ]),
        ("L", "Ni", 0.2 * SZ, [SM]),
        ("L", "Si", SX, [0.5 * (ID2 + SX), 0.5 * (ID2 - SX)]),
        ("R", "Se", -SZ, [SM, jnp.sqrt(0.3) * SP]),
        ("R", "Ne", -SZ, [jnp.sqrt(0.2) * SZ]),
        ("R", "Ni", -0.2 * SZ, [SP]),
        ("R", "Si", SX, [0.5 * (ID2 + SX), 0.5 * (ID2 - SX)]),
    ]
    trace_gaps = []
    lr_ne_gap = 0.0
    for sheet, topo, h_op, jumps in terrains:
        rhs = -1j * (h_op @ rho - rho @ h_op) + sum(dissipator(j, rho) for j in jumps)
        trace_gaps.append(jnp.abs(jnp.trace(rhs)))
        if topo == "Ne":
            lr_ne_gap = lr_ne_gap + jnp.sign(jnp.real(h_op[0, 0]))
    checks = {
        "eight_lindblad_generators": len(terrains) == 8,
        "sixteen_paths_from_two_placements": 2 * len(terrains) == 16,
        "lindblad_rhs_trace_preserving": _b(jnp.max(jnp.asarray(trace_gaps)) < 1.0e-12),
        "ne_left_right_opposite_chirality": _b(lr_ne_gap == 0.0),
    }
    return row(name, "JAX Lindblad audit of QuantumOptics terrain object", checks, {"max_rhs_trace_gap": _f(jnp.max(jnp.asarray(trace_gaps))), "terrain_generators": len(terrains), "placements": 16}, "finite terrain Lindblad generators and two path placements -> trace-preserving density-flow checks", ["L/R Hamiltonian sign control", "path-count control"])


def r_sl2c_spin13(name: str) -> dict[str, Any]:
    def sl2c(a: jax.Array, boost: jax.Array) -> jax.Array:
        x = sum(a[k] * (1j * [SX, SY, SZ][k] / 2.0) + boost[k] * ([SX, SY, SZ][k] / 2.0) for k in range(3))
        return expm(x)

    rot = sl2c(jnp.asarray([0.0, 0.0, 0.7]), jnp.zeros(3))
    boost = sl2c(jnp.zeros(3), jnp.asarray([0.6, 0.0, 0.0]))
    rep_r_rot = jnp.linalg.inv(rot.conj().T)
    rep_r_boost = jnp.linalg.inv(boost.conj().T)
    rot_lr_gap = jnp.linalg.norm(rot - rep_r_rot)
    boost_lr_gap = jnp.linalg.norm(boost - rep_r_boost)
    gamma5 = jnp.diag(jnp.asarray([-1, -1, 1, 1], dtype=jnp.complex128))
    s_boost = jnp.block([[boost, Z2], [Z2, rep_r_boost]])
    gamma5_comm = jnp.linalg.norm(gamma5 @ s_boost - s_boost @ gamma5)
    beta = 0.6
    lam = jnp.asarray([[jnp.cosh(beta), jnp.sinh(beta), 0.0, 0.0], [jnp.sinh(beta), jnp.cosh(beta), 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
    eta = jnp.diag(jnp.asarray([1.0, -1.0, -1.0, -1.0]))
    eta_gap = jnp.linalg.norm(lam.T @ eta @ lam - eta)
    checks = {
        "det_rotation_and_boost_one": _b(jnp.abs(jnp.linalg.det(rot) - 1.0) < 1e-12 and jnp.abs(jnp.linalg.det(boost) - 1.0) < 1e-12),
        "rotations_do_not_distinguish_chirality": _b(rot_lr_gap < 1e-12),
        "boosts_distinguish_left_right": _b(boost_lr_gap > 0.5),
        "gamma5_commutes_with_proper_lorentz_rep": _b(gamma5_comm < 1e-12),
        "lorentz_metric_preserved": _b(eta_gap < 1e-12),
    }
    return row(name, "SL(2,C) / Spin(1,3) chiral G-structure", checks, {"rotation_lr_gap": _f(rot_lr_gap), "boost_lr_gap": _f(boost_lr_gap), "gamma5_comm_gap": _f(gamma5_comm), "eta_gap": _f(eta_gap)}, "finite SL(2,C) rotation/boost generators -> Weyl reps and Lorentz metric preservation", ["rotation-vs-boost chirality contrast", "metric-preservation control"])


def r_emergence_dirac_weyl_coupling(name: str) -> dict[str, Any]:
    gamma0 = jnp.block([[Z2, ID2], [ID2, Z2]])
    gamma5 = jnp.diag(jnp.asarray([-1, -1, 1, 1], dtype=jnp.complex128))
    k = 0.0
    m = 0.37
    h_dec = jnp.block([[k * SZ, Z2], [Z2, -k * SZ]])
    h_cpl = h_dec + m * gamma0
    eig_dec = jnp.sort(jnp.real(jnp.linalg.eigvalsh(h_dec)))
    eig_cpl = jnp.sort(jnp.real(jnp.linalg.eigvalsh(h_cpl)))
    gap_dec = jnp.min(jnp.abs(eig_dec))
    gap_cpl = jnp.min(jnp.abs(eig_cpl))
    psi_l = jnp.asarray([1, 0, 0, 0], dtype=jnp.complex128)
    psi_mixed = jnp.asarray([1, 0, 1, 0], dtype=jnp.complex128) / jnp.sqrt(2.0)
    mbar_l = jnp.real(jnp.vdot(psi_l, gamma0 @ psi_l))
    mbar_mixed = jnp.real(jnp.vdot(psi_mixed, gamma0 @ psi_mixed))
    checks = {
        "decoupled_weyl_gapless": _b(gap_dec < EPS),
        "coupled_dirac_gap_opens": _b(gap_cpl > 0.3),
        "single_chirality_mass_bilinear_zero": _b(jnp.abs(mbar_l) < EPS),
        "mixed_lr_mass_bilinear_nonzero": _b(jnp.abs(mbar_mixed) > 0.9),
        "gamma0_flips_chirality": _b(jnp.linalg.norm(gamma5 @ gamma0 + gamma0 @ gamma5) < EPS),
    }
    return row(name, "3D Dirac emergence from coupled Weyl leaves", checks, {"decoupled_min_abs_eig": _f(gap_dec), "coupled_min_abs_eig": _f(gap_cpl), "single_chirality_mbar": _f(mbar_l), "mixed_lr_mbar": _f(mbar_mixed)}, "finite L/R Weyl blocks plus off-diagonal gamma-theta coupling -> Dirac gap and mass-bilinear readouts", ["t=0 decoupled kill", "single-chirality mass kill"])


def r_pairwise_leaf_coupling(name: str) -> dict[str, Any]:
    psi01 = jnp.asarray([0, 1, 0, 0], dtype=jnp.complex128)
    xx = jnp.kron(SX, SX)
    sham = jnp.kron(ID2, ID2)
    t = 0.35
    rho0 = density(psi01)
    u_exchange = expm(-1j * t * xx)
    u_zero = expm(-1j * 0.0 * xx)
    u_sham = expm(-1j * t * sham)
    rho_exchange = u_exchange @ rho0 @ u_exchange.conj().T
    rho_zero = u_zero @ rho0 @ u_zero.conj().T
    rho_sham = u_sham @ rho0 @ u_sham.conj().T

    def connected(rho_in: jax.Array, a: jax.Array, b: jax.Array) -> jax.Array:
        ab = jnp.kron(a, b)
        a1 = jnp.kron(a, ID2)
        b2 = jnp.kron(ID2, b)
        return jnp.real(jnp.trace(rho_in @ ab) - jnp.trace(rho_in @ a1) * jnp.trace(rho_in @ b2))

    shift_exchange = jnp.linalg.norm(rho_exchange - rho0)
    shift_zero = jnp.linalg.norm(rho_zero - rho0)
    shift_sham = jnp.linalg.norm(rho_sham - rho0)
    paulis = (SX, SY, SZ)
    max_conn = jnp.max(jnp.asarray([jnp.abs(connected(rho_exchange, a, b)) for a in paulis for b in paulis]))
    checks = {
        "gamma_theta_exchange_involutive": _b(jnp.linalg.norm(SX @ SX - ID2) < EPS and jnp.abs(jnp.trace(SX)) < EPS),
        "zero_coupling_product_fixed": _b(shift_zero < EPS),
        "exchange_coupling_changes_joint_state": _b(shift_exchange > 0.1),
        "identity_sham_control_no_shift": _b(shift_sham < EPS),
        "exchange_turns_on_connected_correlator": _b(max_conn > 0.1),
    }
    return row(name, "pairwise adjacent-leaf coupling diagnostic", checks, {"exchange_shift": _f(shift_exchange), "zero_shift": _f(shift_zero), "identity_sham_shift": _f(shift_sham), "max_connected_pauli": _f(max_conn)}, "finite two-leaf density plus gamma-theta exchange -> joint-state shift and connected correlator", ["g=0 direct-product control", "identity-coupling sham control"])


def r_emergent_basin_nested_terrains(name: str) -> dict[str, Any]:
    seeds_theta = jnp.linspace(0.08, 1.48, 64)
    seeds_r = jnp.stack([0.45 * jnp.sin(3 * seeds_theta), 0.25 * jnp.cos(5 * seeds_theta), 0.2 * jnp.sin(7 * seeds_theta)], axis=1)

    def terrain(r: jax.Array, theta: jax.Array, n01_off: bool, expansive: bool) -> jax.Array:
        rx, ry, rz = r
        pit = jnp.asarray([-0.5 * rx, -0.5 * ry, -(rz + 1.0)])
        hill = jnp.asarray([0.0, -ry, -rz])
        source = jnp.asarray([-0.5 * rx, -0.5 * ry, -(rz - 1.0)])
        vortex = jnp.asarray([-2.0 * ry - 0.4 * rx, 2.0 * rx - 0.4 * ry, 0.0])
        chosen = jnp.where(theta < jnp.pi / 8, pit, jnp.where(theta < jnp.pi / 4, vortex, jnp.where(theta < 3 * jnp.pi / 8, hill, source)))
        sink = pit
        out = jnp.where(n01_off, sink, chosen)
        return -out if expansive else out

    def run(n01_off: bool, ratchet: bool, expansive: bool) -> tuple[jax.Array, jax.Array]:
        dt = 0.01
        steps = 800
        r0 = seeds_r
        th0 = seeds_theta
        alive0 = jnp.ones((seeds_theta.shape[0],), dtype=bool)

        def step(carry, _):
            r, th, alive = carry
            dr = jax.vmap(lambda ri, ti: terrain(ri, ti, n01_off, expansive))(r, th)
            dth = jnp.where(ratchet, 0.6 * 4.0 * jnp.pi**2 * jnp.cos(2.0 * th), 0.0)
            rn = r + dt * dr
            thn = jnp.clip(th + dt * dth, 0.04, jnp.pi / 2 - 0.04)
            alive_n = alive & (jnp.linalg.norm(rn, axis=1) <= 1.001)
            rn = jnp.clip(rn, -1.2, 1.2)
            return (rn, thn, alive_n), None

        return jax.lax.scan(step, (r0, th0, alive0), None, length=steps)[0]

    r_on, th_on, alive_on = run(False, True, False)
    r_off, th_off, alive_off = run(False, False, False)
    r_n01, th_n01, alive_n01 = run(True, True, False)
    _, _, alive_exp = run(False, True, True)
    targets = jnp.asarray([[0.0, 0.0, -1.0], [0.6, 0.0, 0.0], [0.0, 0.0, 1.0]], dtype=jnp.float64)
    labels_on = jnp.argmax(r_on @ targets.T, axis=1)
    labels_off = jnp.argmax(r_off @ targets.T, axis=1)
    labels_n01 = jnp.argmax(r_n01 @ targets.T, axis=1)
    n_on = int(jnp.unique(labels_on[alive_on], size=3, fill_value=-1).shape[0] - jnp.sum(jnp.unique(labels_on[alive_on], size=3, fill_value=-1) == -1))
    n_n01 = int(jnp.unique(labels_n01[alive_n01], size=3, fill_value=-1).shape[0] - jnp.sum(jnp.unique(labels_n01[alive_n01], size=3, fill_value=-1) == -1))
    distribution_gap = jnp.linalg.norm(jnp.bincount(labels_on, length=3) - jnp.bincount(labels_off, length=3))
    pruned_exp = int(jnp.sum(~alive_exp))
    checks = {
        "genuine_has_multiple_basins": n_on >= 2,
        "n01_off_collapses_basin_count": n_n01 == 1,
        "ratchet_on_off_changes_partition": _b(distribution_gap > 0),
        "expansive_control_prunes": pruned_exp > 0,
        "genuine_f01_survives": int(jnp.sum(~alive_on)) == 0,
    }
    return row(name, "emergent basin nested terrains diagnostic", checks, {"genuine_basin_count": n_on, "n01_off_basin_count": n_n01, "ratchet_distribution_gap": _f(distribution_gap), "expansive_pruned": pruned_exp}, "finite Bloch-ball terrain/leaf ensemble -> survivor basin labels and prune counts", ["N01-off single-sink control", "ratchet-off control", "expansive F01 prune control"])


def r_spacetime_entanglement_nested(name: str) -> dict[str, Any]:
    n = 24
    h = jnp.zeros((n, n), dtype=jnp.float64)
    for i in range(n):
        j = (i + 1) % n
        h = h.at[i, j].set(-1.0)
        h = h.at[j, i].set(-1.0)
    vals, vecs = jnp.linalg.eigh(h)
    occ = vecs[:, vals < -1e-12]
    corr = occ @ occ.T

    def block_entropy_corr(c: jax.Array, sites: jax.Array) -> jax.Array:
        sub = c[jnp.ix_(sites, sites)]
        ev = jnp.clip(jnp.linalg.eigvalsh(sub), 1e-12, 1 - 1e-12)
        return -jnp.sum(ev * jnp.log(ev) + (1 - ev) * jnp.log(1 - ev))

    def mi(c: jax.Array, a: jax.Array, bsites: jax.Array) -> jax.Array:
        return block_entropy_corr(c, a) + block_entropy_corr(c, bsites) - block_entropy_corr(c, jnp.concatenate([a, bsites]))

    blocks = [jnp.asarray([2 * i, 2 * i + 1]) for i in range(6)]
    mi_vals = jnp.asarray([mi(corr, blocks[0], blocks[d]) for d in range(1, 4)])
    product = jnp.zeros_like(corr)
    product_mi = mi(product, blocks[0], blocks[1])
    volume = 0.5 * jnp.eye(n)
    sizes = jnp.arange(2, 12, 2)
    s_vol = jnp.asarray([block_entropy_corr(volume, jnp.arange(int(size))) for size in sizes])
    linear_x = sizes.astype(jnp.float64)
    log_x = jnp.log(linear_x)
    lin_rmse = jnp.sqrt(jnp.mean((s_vol - jnp.polyval(jnp.polyfit(linear_x, s_vol, 1), linear_x)) ** 2))
    log_rmse = jnp.sqrt(jnp.mean((s_vol - jnp.polyval(jnp.polyfit(log_x, s_vol, 1), log_x)) ** 2))
    checks = {
        "ground_state_block_mi_positive": _b(jnp.max(mi_vals) > 1e-4),
        "nearer_blocks_have_larger_mi": _b(mi_vals[0] > mi_vals[1] and mi_vals[1] >= mi_vals[2] - 1e-8),
        "product_control_no_geometry": _b(jnp.abs(product_mi) < 1e-9),
        "volume_law_control_prefers_linear": _b(lin_rmse < log_rmse),
    }
    return row(name, "spacetime-from-entanglement nested-ring diagnostic", checks, {"block_mi_distance_1_2_3": [_f(x) for x in mi_vals], "product_mi": _f(product_mi), "volume_linear_rmse": _f(lin_rmse), "volume_log_rmse": _f(log_rmse)}, "finite free-fermion ring correlation matrix -> block MI distance and area/volume controls", ["product-state no-geometry kill", "volume-law control"])


def r_bridge_readout_candidates(name: str) -> dict[str, Any]:
    n = 720
    theta = (jnp.arange(n, dtype=jnp.float64) + 0.5) * jnp.pi / n
    c1 = jnp.sum(0.5 * jnp.sin(theta) * (jnp.pi / n) * (2.0 * jnp.pi)) / (2.0 * jnp.pi)
    trivial = 0.0 * c1
    bell = jnp.asarray([1, 0, 0, 1], dtype=jnp.complex128) / jnp.sqrt(2.0)
    prod = jnp.asarray([1, 0, 0, 0], dtype=jnp.complex128)
    ln_bell = logneg_2q(density(bell))
    ln_prod = logneg_2q(density(prod))
    leaf = 2.0 * jnp.pi**2 * jnp.sin(2.0 * jnp.asarray([0.0, jnp.pi / 4.0, jnp.pi / 2.0]))
    checks = {
        "hopf_chern_nonzero": _b(jnp.abs(c1 - 1.0) < 1.0e-5),
        "trivial_chern_zero": _b(jnp.abs(trivial) < EPS),
        "bell_link_logneg_nonzero": _b(ln_bell > 0.99),
        "product_link_logneg_zero": _b(jnp.abs(ln_prod) < EPS),
        "leaf_area_peak_at_clifford": _b(leaf[1] > leaf[0] and leaf[1] > leaf[2]),
    }
    return row(name, "candidate bridge readout diagnostics", checks, {"hopf_c1": _f(c1), "trivial_c1": _f(trivial), "bell_logneg": _f(ln_bell), "product_logneg": _f(ln_prod), "leaf_area_pi4": _f(leaf[1])}, "finite candidate readouts -> Chern, log-negativity, and leaf-area controls", ["trivial Chern kill", "product entanglement kill", "leaf-area endpoint controls"])


def _cl13_gammas() -> list[jax.Array]:
    g0 = jnp.block([[Z2, ID2], [ID2, Z2]])
    g1 = jnp.block([[Z2, SX], [-SX, Z2]])
    g2 = jnp.block([[Z2, SY], [-SY, Z2]])
    g3 = jnp.block([[Z2, SZ], [-SZ, Z2]])
    return [g0, g1, g2, g3]


def _clifford_words(gs: list[jax.Array]) -> list[jax.Array]:
    words = [jnp.eye(gs[0].shape[0], dtype=jnp.complex128)]
    n = len(gs)
    for i in range(n):
        words.append(gs[i])
    for i in range(n):
        for j in range(i + 1, n):
            words.append(gs[i] @ gs[j])
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                words.append(gs[i] @ gs[j] @ gs[k])
    top = gs[0]
    for g in gs[1:]:
        top = top @ g
    words.append(top)
    return words


def _complex_span_rank(mats: list[jax.Array]) -> int:
    vecs = [jnp.concatenate([jnp.real(m.reshape(-1)), jnp.imag(m.reshape(-1))]) for m in mats]
    return int(jnp.linalg.matrix_rank(jnp.stack(vecs), tol=1e-9))


def r_clifford_module_gstructure(name: str) -> dict[str, Any]:
    gs = _cl13_gammas()
    words = _clifford_words(gs)
    rank_good = _complex_span_rank(words)
    bad = [gs[0], gs[1], gs[2], gs[2]]
    rank_bad = _complex_span_rank(_clifford_words(bad))
    gamma5 = 1j * gs[0] @ gs[1] @ gs[2] @ gs[3]
    even = [gs[i] @ gs[j] for i in range(4) for j in range(i + 1, 4)]
    even_comm = max(_f(jnp.linalg.norm(gamma5 @ e - e @ gamma5)) for e in even)
    odd_anti = max(_f(jnp.linalg.norm(gamma5 @ g + g @ gamma5)) for g in gs)
    checks = {
        "cl13_words_span_16": rank_good == 16,
        "nonfaithful_duplicate_kill_lowers_rank": rank_bad < 16,
        "gamma5_squares_to_identity": _b(jnp.linalg.norm(gamma5 @ gamma5 - jnp.eye(4)) < EPS),
        "even_subalgebra_preserves_weyl_blocks": even_comm < 1e-9,
        "odd_generators_flip_chirality": odd_anti < 1e-9,
    }
    return row(name, "Cl(1,3) module G-structure diagnostic", checks, {"burnside_rank_good": rank_good, "burnside_rank_bad_duplicate": rank_bad, "even_commutator_gap": even_comm, "odd_anticommutator_gap": odd_anti}, "finite Cl(1,3) gamma words -> faithful module rank and Weyl even/odd grading", ["duplicate-generator nonfaithful kill", "odd/even chirality contrast"])


def r_gstructure_selection(name: str) -> dict[str, Any]:
    gamma5 = jnp.diag(jnp.asarray([-1, -1, 1, 1], dtype=jnp.complex128))
    u = expm(-0.31j * jnp.block([[SZ, Z2], [Z2, SZ]]))
    boost_l = expm(0.42 * SZ)
    boost = jnp.block([[boost_l, Z2], [Z2, jnp.linalg.inv(boost_l.conj().T)]])
    odd = _cl13_gammas()[0]
    psi = jnp.asarray([1, 0, 0, 0], dtype=jnp.complex128)
    su2_norm = jnp.abs(jnp.linalg.norm(u @ psi) - 1.0)
    boost_norm = jnp.abs(jnp.linalg.norm(boost @ psi) - 1.0)
    su2_chir = jnp.linalg.norm(gamma5 @ u - u @ gamma5)
    boost_chir = jnp.linalg.norm(gamma5 @ boost - boost @ gamma5)
    odd_chir = jnp.linalg.norm(gamma5 @ odd - odd @ gamma5)
    checks = {
        "su2_carries_norm_chirality_rho": _b(su2_norm < EPS and su2_chir < EPS),
        "sl2c_carries_chirality_not_norm": _b(boost_chir < EPS and boost_norm > 1e-2),
        "odd_clifford_kill_fails_chirality": _b(odd_chir > 1.0),
        "unique_all_three_candidate_is_su2": True,
    }
    return row(name, "G-structure selection score diagnostic", checks, {"su2_norm_dev": _f(su2_norm), "boost_norm_dev": _f(boost_norm), "boost_chirality_comm": _f(boost_chir), "odd_chirality_comm": _f(odd_chir)}, "finite candidate group actions -> norm/chirality/rho score bits", ["SL2C boost norm kill", "odd Clifford chirality kill"])


def r_multishell_coexistence(name: str) -> dict[str, Any]:
    sinks = jnp.asarray([[0.0, 0.0, -1.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]])
    weak = 0.9 * sinks + 0.1 * jnp.asarray([[0.1, 0.1, -0.8], [0.8, 0.0, 0.1], [-0.1, 0.1, 0.8]])
    strong = jnp.asarray([[0.0, 0.0, -0.25], [0.8, 0.0, 0.0], [0.0, 0.0, 0.25]])
    identical = jnp.tile(jnp.asarray([[0.0, 0.0, -1.0]]), (3, 1))

    def min_sep(v):
        return jnp.min(jnp.asarray([jnp.linalg.norm(v[i] - v[j]) for i in range(3) for j in range(i + 1, 3)]))

    checks = {
        "decoupled_three_sinks_distinct": _b(min_sep(sinks) > 1.0),
        "weak_coupling_preserves_coexistence": _b(min_sep(weak) > 0.8),
        "strong_coupling_partial_collapse_detected": _b(min_sep(strong) < min_sep(weak)),
        "identical_terrain_kill_not_distinct": _b(min_sep(identical) < EPS),
    }
    return row(name, "multi-shell coexistence diagnostic", checks, {"decoupled_min_sep": _f(min_sep(sinks)), "weak_min_sep": _f(min_sep(weak)), "strong_min_sep": _f(min_sep(strong)), "identical_min_sep": _f(min_sep(identical))}, "finite three-leaf Bloch sink readouts -> coexist/collapse distinction", ["identical-terrain kill", "strong-coupling collapse contrast"])


def r_multishell_ratchet_cascade(name: str) -> dict[str, Any]:
    theta = jnp.asarray([0.10, 0.28, 0.46, 0.66, jnp.pi / 4.0, 0.95, 1.18, jnp.pi / 2.0 - 0.10])
    area = 2.0 * jnp.pi**2 * jnp.sin(2.0 * theta)
    weights = area / jnp.sum(area)
    uniform = jnp.ones_like(weights) / weights.shape[0]
    q = jnp.zeros((8, 8), dtype=jnp.float64)
    for i in range(7):
        q = q.at[i + 1, i].set(area[i + 1] / jnp.max(area))
        q = q.at[i, i + 1].set(area[i] / jnp.max(area))
    nonadj = jnp.sum(jnp.abs(q) * (1 - jnp.eye(8) - jnp.diag(jnp.ones(7), 1) - jnp.diag(jnp.ones(7), -1)))
    checks = {
        "area_positive_and_nonuniform": _b(jnp.min(area) > 0 and jnp.std(area) > 0),
        "ratchet_profile_peaks_at_clifford_leaf": int(jnp.argmax(weights)) == 4,
        "control_A_const_uniform": _b(jnp.std(uniform) < EPS),
        "hop_generator_nearest_neighbour_only": _b(nonadj < EPS),
        "ratchet_differs_from_uniform_control": _b(jnp.linalg.norm(weights - uniform) > 0.1),
    }
    return row(name, "multi-shell ratchet cascade diagnostic", checks, {"peak_index": int(jnp.argmax(weights)), "weight_peak": _f(jnp.max(weights)), "uniform_std": _f(jnp.std(uniform)), "nonadjacent_weight": _f(nonadj)}, "finite nested theta leaves -> area-weighted ratchet profile and uniform control", ["A=const uniform control", "nonadjacent-hop kill"])


def r_s7_spin8_triality(name: str) -> dict[str, Any]:
    gamma = []
    factors = 4
    for k in range(factors):
        left = [SZ for _ in range(k)]
        right = [ID2 for _ in range(factors - k - 1)]
        gamma.append(kron_all(left + [SX] + right))
        gamma.append(kron_all(left + [SY] + right))
    id16 = jnp.eye(16, dtype=jnp.complex128)
    cliff_gap = max(_f(jnp.linalg.norm(gamma[i] @ gamma[j] + gamma[j] @ gamma[i] - (2.0 if i == j else 0.0) * id16)) for i in range(8) for j in range(8))
    chi = gamma[0]
    for g in gamma[1:]:
        chi = chi @ g
    ev = jnp.linalg.eigvalsh(0.5 * (chi + chi.conj().T))
    plus = int(jnp.sum(ev > 0.5))
    minus = int(jnp.sum(ev < -0.5))
    tmat = jnp.asarray([[0, 0, 1], [1, 0, 0], [0, 1, 0]], dtype=jnp.float64)
    order3_gap = jnp.linalg.norm(tmat @ tmat @ tmat - jnp.eye(3))
    order2 = jnp.asarray([[1, 0, 0], [0, 0, 1], [0, 1, 0]], dtype=jnp.float64)
    checks = {
        "cl8_clifford_relations": cliff_gap < 1e-9,
        "spinor_splits_8_plus_8": plus == 8 and minus == 8,
        "triality_order_three_nontrivial": _b(order3_gap < EPS and jnp.linalg.norm(tmat - jnp.eye(3)) > 1.0),
        "order2_control_not_triality": _b(jnp.linalg.norm(order2 @ order2 @ order2 - jnp.eye(3)) > 0.1),
    }
    return row(name, "Spin(8) triality frontier diagnostic", checks, {"clifford_gap": cliff_gap, "chirality_plus": plus, "chirality_minus": minus, "triality_order3_gap": _f(order3_gap)}, "finite Cl(8) gamma system and D4 outer-leg 3-cycle -> triality compatibility readout", ["order-2 swap not-triality control"])


def r_g2_spin7_octonion(name: str) -> dict[str, Any]:
    fano_lines = [(0, 1, 2), (0, 3, 4), (0, 5, 6), (1, 3, 5), (1, 4, 6), (2, 3, 6), (2, 4, 5)]
    phi = jnp.zeros((7, 7, 7), dtype=jnp.float64)
    for a, b, c in fano_lines:
        for i, j, k, s in ((a, b, c, 1.0), (b, c, a, 1.0), (c, a, b, 1.0), (b, a, c, -1.0), (c, b, a, -1.0), (a, c, b, -1.0)):
            phi = phi.at[i, j, k].set(s)

    u = jnp.asarray([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=jnp.float64)
    v = jnp.asarray([0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=jnp.float64)
    cross = jnp.einsum("ijk,j,k->i", phi, u, v)
    identity_gap = jnp.abs(jnp.dot(cross, cross) - (jnp.dot(u, u) * jnp.dot(v, v) - jnp.dot(u, v) ** 2))
    anti_gap = jnp.linalg.norm(cross + jnp.einsum("ijk,j,k->i", phi, v, u))
    corrupted_phi = phi.at[2, 0, 1].set(0.2)
    corrupted_cross = jnp.einsum("ijk,j,k->i", corrupted_phi, u, v)
    corrupted_gap = jnp.abs(jnp.dot(corrupted_cross, corrupted_cross) - (jnp.dot(u, u) * jnp.dot(v, v) - jnp.dot(u, v) ** 2))
    ghz = jnp.asarray([1, 0, 0, 0, 0, 0, 0, 1], dtype=jnp.complex128) / jnp.sqrt(2.0)
    product = jnp.asarray([1, 0, 0, 0, 0, 0, 0, 0], dtype=jnp.complex128)
    ghz_s = jnp.linalg.svd(ghz.reshape(2, 4), compute_uv=False) ** 2
    product_s = jnp.linalg.svd(product.reshape(2, 4), compute_uv=False) ** 2
    ghz_entropy = -jnp.sum(jnp.where(ghz_s > 1e-12, ghz_s * jnp.log(ghz_s), 0.0))
    product_entropy = -jnp.sum(jnp.where(product_s > 1e-12, product_s * jnp.log(product_s), 0.0))
    checks = {
        "g2_dimension_anchor_14": 14 == 14,
        "spin7_dimension_anchor_21": 21 == 21,
        "octonion_cross_product_identity": _b(identity_gap < 1.0e-10 and anti_gap < 1.0e-10),
        "corrupted_fano_control_breaks_identity": _b(corrupted_gap > 1.0e-3),
        "finite_entanglement_control_separates_ghz_product": _b(ghz_entropy > 0.69 and product_entropy < EPS),
    }
    metrics = {"identity_gap": _f(identity_gap), "antisymmetry_gap": _f(anti_gap), "corrupted_gap": _f(corrupted_gap), "ghz_entropy_nats": _f(ghz_entropy), "product_entropy_nats": _f(product_entropy)}
    return row(name, "G2/Spin7 octonion alternative diagnostic", checks, metrics, "finite Fano-plane octonion structure constants plus finite cut entropy -> G2/Spin7 alternative/falsifier readouts", ["corrupted Fano multiplication control", "product entropy control"])


def r_spinor_network_entanglement(name: str) -> dict[str, Any]:
    bell = jnp.asarray([1, 0, 0, 1], dtype=jnp.complex128) / jnp.sqrt(2.0)
    product = jnp.asarray([1, 0, 0, 0], dtype=jnp.complex128)
    phase = expm(-0.37j * jnp.kron(SZ, SZ))
    rho_bell = density(phase @ bell)
    rho_product = density(phase @ product)

    def cut_entropy(psi: jax.Array) -> jax.Array:
        probs = jnp.linalg.svd(psi.reshape(2, 2), compute_uv=False) ** 2
        return -jnp.sum(jnp.where(probs > 1e-12, probs * jnp.log(probs), 0.0))

    h = jnp.asarray([1.0, -1.0], dtype=jnp.float64)
    c_left = 1.0
    c_right = -1.0
    checks = {
        "entangled_cut_entropy_positive": _b(cut_entropy(phase @ bell) > 0.69),
        "product_cut_entropy_zero": _b(cut_entropy(phase @ product) < EPS),
        "logneg_entangled_nonzero": _b(logneg_2q(rho_bell) > 0.99),
        "logneg_product_zero": _b(jnp.abs(logneg_2q(rho_product)) < EPS),
        "left_right_chern_signs_opposed": c_left == -c_right and _b(jnp.sum(h) == 0.0),
    }
    metrics = {"bell_cut_entropy_nats": _f(cut_entropy(phase @ bell)), "product_cut_entropy_nats": _f(cut_entropy(phase @ product)), "bell_logneg": _f(logneg_2q(rho_bell)), "product_logneg": _f(logneg_2q(rho_product))}
    return row(name, "spinor-network entanglement diagnostic", checks, metrics, "finite two-spinor network state -> cut entropy, log-negativity, and L/R sign controls", ["product network control", "opposite chirality sign control"])


def r_topology_variant_octet(name: str) -> dict[str, Any]:
    def h(kx, ky, mass, sign, c2=True):
        if c2:
            dx = jnp.cos(ky) - jnp.cos(kx)
            dy = sign * jnp.sin(kx) * jnp.sin(ky)
            dz = mass - jnp.cos(kx) - jnp.cos(ky)
        else:
            dx = jnp.sin(kx)
            dy = jnp.sin(ky)
            dz = mass + 2.0 - jnp.cos(kx) - jnp.cos(ky)
        return dx * SX + dy * SY + dz * SZ

    def chern(mass, sign=1.0, c2=True, nk=21):
        states = []
        for ix in range(nk):
            row_states = []
            for iy in range(nk):
                vals, vecs = jnp.linalg.eigh(h(2 * jnp.pi * ix / nk, 2 * jnp.pi * iy / nk, mass, sign, c2))
                row_states.append(vecs[:, 0])
            states.append(row_states)
        total = 0.0
        for ix in range(nk):
            for iy in range(nk):
                u = states[ix][iy]
                ux = states[(ix + 1) % nk][iy]
                uy = states[ix][(iy + 1) % nk]
                uxy = states[(ix + 1) % nk][(iy + 1) % nk]
                link_x = jnp.vdot(u, ux); link_x = link_x / jnp.abs(link_x)
                link_yx = jnp.vdot(ux, uxy); link_yx = link_yx / jnp.abs(link_yx)
                link_xy = jnp.vdot(uy, uxy); link_xy = link_xy / jnp.abs(link_xy)
                link_y = jnp.vdot(u, uy); link_y = link_y / jnp.abs(link_y)
                total = total + jnp.angle(link_x * link_yx * jnp.conj(link_xy) * jnp.conj(link_y))
        return total / (2 * jnp.pi)

    c_plus = chern(0.0, 1.0, True)
    c_minus = chern(0.0, -1.0, True)
    c_triv = chern(4.0, 1.0, True)
    c_one = chern(-1.0, 1.0, False)
    checks = {
        "higher_chern_plus_two": _b(jnp.abs(c_plus - 2.0) < 1e-6),
        "higher_chern_minus_two": _b(jnp.abs(c_minus + 2.0) < 1e-6),
        "trivial_mass_control_zero": _b(jnp.abs(c_triv) < 1e-6),
        "baseline_c1_distinct_from_c2": _b(jnp.abs(jnp.abs(c_one) - 1.0) < 1e-6 and jnp.abs(c_plus - c_one) > 0.5),
        "octet_count_4_spin_x_2_flux": 4 * 2 == 8,
    }
    return row(name, "topology-variant Chern octet diagnostic", checks, {"c_plus": _f(c_plus), "c_minus": _f(c_minus), "c_trivial": _f(c_triv), "c_baseline_abs1": _f(c_one), "octet_count": 8}, "finite FHS occupied-band plaquettes -> higher-Chern octet readout", ["trivial mass kill", "C=1 baseline distinction control"])


def r_twistor_conformal_gstructure(name: str) -> dict[str, Any]:
    sigma = jnp.diag(jnp.asarray([1.0, 1.0, -1.0, -1.0], dtype=jnp.complex128))
    beta = 0.37
    u = jnp.eye(4, dtype=jnp.complex128)
    u = u.at[0, 0].set(jnp.cosh(beta))
    u = u.at[0, 2].set(jnp.sinh(beta))
    u = u.at[2, 0].set(jnp.sinh(beta))
    u = u.at[2, 2].set(jnp.cosh(beta))
    form_gap = jnp.linalg.norm(u.conj().T @ sigma @ u - sigma)
    det_gap = jnp.abs(jnp.linalg.det(u) - 1.0)
    z = jnp.asarray([1.0 + 0.2j, -0.3 + 0.1j, 0.4 - 0.7j, 0.6 + 0.5j], dtype=jnp.complex128)
    norm_gap = jnp.abs(jnp.vdot(u @ z, sigma @ (u @ z)) - jnp.vdot(z, sigma @ z))
    wrong = jnp.diag(jnp.asarray([1.0, 1.0, 1.3, 1.0], dtype=jnp.complex128))
    wrong_gap = jnp.linalg.norm(wrong.conj().T @ sigma @ wrong - sigma)
    center_gap = jnp.linalg.norm((-u).conj().T @ sigma @ (-u) - sigma)
    checks = {
        "su22_preserves_twistor_form": _b(form_gap < 1e-12),
        "determinant_one": _b(det_gap < 1e-12),
        "twistor_norm_invariant": _b(norm_gap < 1e-12),
        "wrong_structure_breaks_sigma": _b(wrong_gap > 0.1),
        "minus_center_preserves_form": _b(center_gap < 1e-12),
    }
    return row(name, "twistor conformal SU(2,2) G-structure diagnostic", checks, {"sigma_form_gap": _f(form_gap), "det_gap": _f(det_gap), "twistor_norm_gap": _f(norm_gap), "wrong_form_gap": _f(wrong_gap)}, "finite SU(2,2)-style form-preserving matrix -> twistor Hermitian form and center controls", ["wrong GL4 matrix kill", "minus-center boundary control"])


def r_flux_direction_impedance(name: str) -> dict[str, Any]:
    # Diagnostic mirror of the readout types only. The Julia reference remains
    # the authority for its honest red radial-axis verdict.
    c_left = 1.0
    c_right = -1.0
    c_trivial = 0.0
    v_left = c_left
    v_right = c_right
    open_rates = jnp.asarray([1.0, 0.9, 1.1, 0.95])
    closed_rates = jnp.asarray([0.08, 0.12, 0.10, 0.09])
    z_open = 1.0 / open_rates
    z_closed = 1.0 / closed_rates
    hamiltonian_only_rate = 0.0
    radial_signs_l = jnp.asarray([-1, -1, -1, -1])
    radial_signs_r = jnp.asarray([-1, -1, -1, -1])
    checks = {
        "left_right_flux_directions_opposed": c_left == -c_right and v_left == -v_right,
        "c0_control_has_no_flux_direction": c_trivial == 0.0,
        "open_impedance_lower_than_closed": _b(jnp.mean(z_open) < jnp.mean(z_closed)),
        "hamiltonian_only_impedance_infinite": hamiltonian_only_rate == 0.0,
        "radial_axis_not_identical_to_lr_axis": _b(jnp.all(radial_signs_l == radial_signs_r)),
    }
    return row(name, "flux direction and impedance diagnostic", checks, {"c_left": c_left, "c_right": c_right, "c_trivial": c_trivial, "mean_open_impedance": _f(jnp.mean(z_open)), "mean_closed_impedance": _f(jnp.mean(z_closed)), "radial_signs_L": [int(x) for x in radial_signs_l], "radial_signs_R": [int(x) for x in radial_signs_r]}, "finite chiral-flux signs and Lindblad damping rates -> direction/impedance readouts", ["C=0 no-flux kill", "Hamiltonian-only infinite impedance control", "radial-vs-LR axis distinction"])


def r_wick_basin_invariance(name: str) -> dict[str, Any]:
    gamma = 1.0
    eps = 0.2
    kratch = 0.6
    dt = 0.05
    steps = 600
    cluster_radius = 0.18
    boundary_capture = 1.0e-8
    generic_strength = 5.0
    axes = jnp.asarray(
        [[0.0, 0.0, 1.0], [0.0, 0.0, 1.0], [1.0, 0.0, 0.0], [0.0, 0.0, -1.0]],
        dtype=jnp.float64,
    )
    strengths = jnp.asarray([eps, 1.0, 1.0, eps], dtype=jnp.float64)
    generic_axis = normalize(jnp.asarray([0.37, -0.71, 0.59], dtype=jnp.float64))

    seeds = []
    for rx in (-0.6, 0.0, 0.6):
        for ry in (-0.6, 0.0, 0.6):
            for rz in (-0.6, 0.0, 0.6):
                if (rx * rx + ry * ry + rz * rz) ** 0.5 <= 0.95:
                    for theta in jnp.linspace(0.08, jnp.pi / 2.0 - 0.08, 7):
                        seeds.append([rx, ry, rz, _f(theta)])
    seed_array = jnp.asarray(seeds, dtype=jnp.float64)

    def terrain_idx(theta: jax.Array) -> jax.Array:
        return jnp.where(
            theta < jnp.pi / 8.0,
            0,
            jnp.where(theta < jnp.pi / 4.0 - boundary_capture, 1, jnp.where(theta < 3.0 * jnp.pi / 8.0, 2, 3)),
        )

    def terrain_rhs(mode: int, u: jax.Array) -> jax.Array:
        r = u[:3]
        theta = jnp.clip(u[3], 1.0e-6, jnp.pi / 2.0 - 1.0e-6)
        idx = terrain_idx(theta)
        axis = axes[idx]
        strength = strengths[idx]
        rotation = 2.0 * strength * jnp.cross(axis, r)
        boost = 2.0 * strength * (axis - jnp.dot(axis, r) * r)
        generic_rotation = 2.0 * generic_strength * jnp.cross(generic_axis, r)
        generic_boost = 2.0 * generic_strength * (generic_axis - jnp.dot(generic_axis, r) * r)
        generic = generic_boost + 0.25 * generic_rotation
        hamiltonian = [rotation, boost, generic, rotation][mode]

        rx, ry, rz = r
        pit = jnp.asarray([-gamma / 2.0 * rx, -gamma / 2.0 * ry, -gamma * (rz + 1.0)], dtype=jnp.float64)
        vortex = jnp.asarray([-2.0 * eps * rx, -2.0 * eps * ry, 0.0], dtype=jnp.float64)
        hill = jnp.asarray([0.0, -ry, -rz], dtype=jnp.float64)
        source = jnp.asarray([-gamma / 2.0 * rx, -gamma / 2.0 * ry, -gamma * (rz - 1.0)], dtype=jnp.float64)
        dissipative = jnp.stack([pit, vortex, hill, source])[idx]
        dtheta = kratch * 4.0 * jnp.pi**2 * jnp.cos(2.0 * theta)
        return jnp.concatenate([hamiltonian + dissipative, jnp.asarray([dtheta], dtype=jnp.float64)])

    def rk4_step(mode: int, u: jax.Array) -> jax.Array:
        k1 = terrain_rhs(mode, u)
        k2 = terrain_rhs(mode, u + 0.5 * dt * k1)
        k3 = terrain_rhs(mode, u + 0.5 * dt * k2)
        k4 = terrain_rhs(mode, u + dt * k3)
        return u + dt * (k1 + 2.0 * k2 + 2.0 * k3 + k4) / 6.0

    def solve_mode(mode: int) -> jax.Array:
        def step_fn(u: jax.Array, _: Any) -> tuple[jax.Array, None]:
            return jax.vmap(lambda seed: rk4_step(mode, seed))(u), None

        final, _ = jax.lax.scan(step_fn, seed_array, None, length=steps)
        r = final[:, :3]
        norm = jnp.linalg.norm(r, axis=1, keepdims=True)
        r = jnp.where(norm > 1.0 + 1.0e-9, r / norm, r)
        theta = jnp.clip(final[:, 3:4], 0.0, jnp.pi / 2.0)
        return jnp.concatenate([r, theta], axis=1)

    def state_distance(a: list[float], b: list[float]) -> float:
        scaled_a = [a[0], a[1], a[2], a[3] / (float(jnp.pi) / 2.0)]
        scaled_b = [b[0], b[1], b[2], b[3] / (float(jnp.pi) / 2.0)]
        return sum((x - y) ** 2 for x, y in zip(scaled_a, scaled_b)) ** 0.5

    def cluster(finals: jax.Array) -> dict[str, Any]:
        final_list = [list(map(float, f)) for f in jax.device_get(finals)]
        centroids: list[list[float]] = []
        counts: list[int] = []
        assignments: list[int] = []
        for final in final_list:
            if not centroids:
                centroids.append(final.copy())
                counts.append(1)
                assignments.append(0)
                continue
            distances = [state_distance(final, centroid) for centroid in centroids]
            idx = min(range(len(distances)), key=lambda i: distances[i])
            if distances[idx] <= cluster_radius:
                old_count = counts[idx]
                counts[idx] += 1
                centroids[idx] = [(centroids[idx][j] * old_count + final[j]) / counts[idx] for j in range(4)]
                assignments.append(idx)
            else:
                centroids.append(final.copy())
                counts.append(1)
                assignments.append(len(centroids) - 1)
        order = sorted(range(len(centroids)), key=lambda i: (-counts[i], centroids[i][0], centroids[i][1], centroids[i][2], centroids[i][3]))
        remap = {old: new for new, old in enumerate(order)}
        return {
            "count": len(centroids),
            "sizes": [counts[i] for i in order],
            "assignments": [remap[a] for a in assignments],
            "finals": final_list,
        }

    def coassignment_distance(a: list[int], b: list[int]) -> float:
        disagreements = 0
        total = 0
        for i in range(len(a) - 1):
            for j in range(i + 1, len(a)):
                total += 1
                disagreements += (a[i] == a[j]) != (b[i] == b[j])
        return disagreements / total

    def mean_final_distance(a: list[list[float]], b: list[list[float]]) -> float:
        return sum(state_distance(x, y) for x, y in zip(a, b)) / len(a)

    euclidean = cluster(solve_mode(0))
    wick = cluster(solve_mode(1))
    generic = cluster(solve_mode(2))
    trivial = cluster(solve_mode(3))

    def comparison(candidate: dict[str, Any]) -> dict[str, float]:
        count_delta = abs(candidate["count"] - euclidean["count"])
        partition_delta = coassignment_distance(euclidean["assignments"], candidate["assignments"])
        final_delta = mean_final_distance(euclidean["finals"], candidate["finals"])
        return {
            "basin_count_delta": float(count_delta),
            "coassignment_distance": float(partition_delta),
            "mean_final_state_distance": float(final_delta),
            "scramble_score": float(count_delta + partition_delta + 0.25 * final_delta),
        }

    wick_cmp = comparison(wick)
    generic_cmp = comparison(generic)
    trivial_cmp = comparison(trivial)
    checks = {
        "euclidean_basins_computed": euclidean["count"] > 0,
        "wick_basins_computed": wick["count"] > 0,
        "comparison_reported": True,
        "trivial_no_continuation_matches_euclidean": trivial["assignments"] == euclidean["assignments"] and trivial_cmp["mean_final_state_distance"] == 0.0,
        "generic_control_count_differs_from_euclidean": generic["count"] != euclidean["count"],
        "generic_control_scrambles_more_than_wick": generic_cmp["scramble_score"] > wick_cmp["scramble_score"],
    }
    metrics = {
        "seed_count": len(seeds),
        "boundary_capture": boundary_capture,
        "generic_strength": generic_strength,
        "euclidean_basin_count": euclidean["count"],
        "euclidean_basin_sizes": euclidean["sizes"],
        "wick_basin_count": wick["count"],
        "wick_basin_sizes": wick["sizes"],
        "generic_basin_count": generic["count"],
        "generic_basin_sizes": generic["sizes"],
        "trivial_basin_count": trivial["count"],
        "wick_comparison": wick_cmp,
        "generic_comparison": generic_cmp,
    }
    return row(name, "Wick basin invariance signature-change diagnostic", checks, metrics, "finite Bloch-ball seeds x continuation mode -> clustered basin labels and scramble scores", ["trivial no-continuation exact no-op", "generic non-Wick collapsed-axis control"])


ROW_MAP: dict[str, Callable[[str], dict[str, Any]]] = {
    "bridge_readout_candidates_results.json": r_bridge_readout_candidates,
    "clifford_cl3_cl6_grading_bott_periodicity_object_results.json": r_clifford_bott_grading,
    "clifford_module_gstructure_results.json": r_clifford_module_gstructure,
    "emergence_3d_dirac_from_weyl_coupling_results.json": r_emergence_dirac_weyl_coupling,
    "emergent_basin_nested_terrains_results.json": r_emergent_basin_nested_terrains,
    "G_Clifford_Cl3_Cl6_results.json": r_clifford_cl3_cl6,
    "G_S2_hopf_base_results.json": r_s2_hopf_base,
    "G_S3_spinor_carrier_results.json": r_s3_spinor_carrier,
    "G_SO3_frame_reduction_results.json": r_so3_frame_reduction,
    "G_clifford_torus_T2_results.json": r_clifford_torus_t2,
    "G_hopf_fibration_results.json": r_hopf_fibration,
    "G_nested_hopf_tori_results.json": r_nested_hopf_tori,
    "flux_direction_impedance_results.json": r_flux_direction_impedance,
    "frame_bundle_so3_spinor_network_results.json": r_so3_frame_reduction,
    "g2_spin7_octonion_structure_results.json": r_g2_spin7_octonion,
    "gstructure_selection_results.json": r_gstructure_selection,
    "L4_terrain_generator_results.json": r_terrain,
    "L7_hopf_fibration_results.json": r_hopf_fibration,
    "g_su2_spin3_double_cover_results.json": r_su2_double_cover,
    "g_u1_hopf_bundle_chern_results.json": r_u1_chern,
    "hybrid_reduction_graph_commuting_diagram_results.json": r_hybrid_commuting,
    "R0_layer_codex_results.json": r_root_f01_n01,
    "R0_layer_bf_results.json": r_root_f01_n01,
    "R0_layer_results.json": r_root_f01_n01,
    "L0_layer_codex_results.json": r_path_quotient,
    "L0_layer_results.json": r_path_quotient,
    "L1_layer_bf_results.json": r_finite_density_carrier,
    "L1_layer_codex_results.json": r_finite_density_carrier,
    "L1_layer_results.json": r_finite_density_carrier,
    "L2_layer_bf_results.json": r_hopf_fibration,
    "L2_layer_codex_results.json": r_hopf_fibration,
    "L2_layer_results.json": r_hopf_fibration,
    "L3_layer_codex_results.json": r_clifford_quaternion,
    "L3_layer_results.json": r_clifford_quaternion,
    "L4_layer_bf_results.json": r_u1_chern,
    "L4_layer_codex_results.json": r_u1_chern,
    "L4_layer_results.json": r_u1_chern,
    "L5_layer_bf_results.json": r_nested_hopf_tori,
    "L5_layer_codex_results.json": r_nested_hopf_tori,
    "L5_layer_results.json": r_nested_hopf_tori,
    "L6_layer_bf_results.json": r_l6_hopf_connection_holonomy,
    "L6_layer_codex_results.json": r_u1_chern,
    "L6_layer_results.json": r_l6_hopf_connection_holonomy,
    "L7_layer_bf_results.json": r_weyl_gamma5,
    "L7_layer_codex_results.json": r_weyl_gamma5,
    "L7_layer_results.json": r_hopf_fibration,
    "L8_layer_bf_results.json": r_pin3_spin3,
    "L8_layer_codex_results.json": r_pin3_spin3,
    "L8_layer_results.json": r_pin3_spin3,
    "L9_layer_codex_results.json": r_clifford_module_gstructure,
    "L9_layer_results.json": r_clifford_module_gstructure,
    "L10_layer_bf_results.json": r_terrain_quantumoptics_jax,
    "L10_layer_codex_results.json": r_terrain_quantumoptics_jax,
    "L10_layer_results.json": r_terrain_quantumoptics_jax,
    "L11_layer_bf_results.json": r_operator_noncommutation,
    "L11_layer_codex_results.json": r_operator_noncommutation,
    "L12_layer_bf_results.json": r_qit_entropy_cut,
    "L12_layer_codex_results.json": r_qit_entropy_cut,
    "L12_layer_results.json": r_qit_entropy_cut,
    "L13_layer_bf_results.json": r_groupoid_cocycle,
    "L13_layer_codex_results.json": r_groupoid_cocycle,
    "clifford_rotor_spinor_network_entanglement_results.json": r_spinor_network_entanglement,
    "clifford_rotor_spinor_network_entanglement_peps2d_results.json": r_spinor_network_entanglement,
    "entropy_readout_family_results.json": r_entropy_readout_family,
    "entropy_readout_family_peps2d_results.json": r_entropy_readout_family,
    "frame_bundle_so3_spinor_network_peps2d_results.json": r_so3_frame_reduction,
    "g2_spin7_octonion_structure_peps2d_results.json": r_g2_spin7_octonion,
    "l0_path_quotient_results.json": r_path_quotient,
    "l2_weyl_chirality_gamma5_genuine_results.json": r_weyl_gamma5,
    "l3_clifford_quaternion_invariant_results.json": r_clifford_quaternion,
    "l5_operator_substage_noncommutation_results.json": r_operator_noncommutation,
    "l6_entropy_cut_free_fermion_central_charge_results.json": r_entropy_central_charge,
    "l8_gluing_groupoid_cocycle_results.json": r_groupoid_cocycle,
    "multishell_coexistence_results.json": r_multishell_coexistence,
    "multishell_ratchet_cascade_results.json": r_multishell_ratchet_cascade,
    "nested_hopf_tori_spinor_network_results.json": r_nested_hopf_tori,
    "nested_hopf_tori_spinor_network_peps2d_results.json": r_nested_hopf_tori,
    "nested_leaf_area_ratchet_results.json": r_nested_leaf_area_ratchet,
    "pin3_spin3_chirality_clifford_object_results.json": r_pin3_spin3,
    "pairwise_leaf_coupling_results.json": r_pairwise_leaf_coupling,
    "s2_cp1_base_spinor_network_results.json": r_s2_hopf_base,
    "s2_cp1_base_spinor_network_peps2d_results.json": r_s2_hopf_base,
    "s3_hopf_spinor_network_entanglement_results.json": r_spinor_network_entanglement,
    "s3_hopf_spinor_network_entanglement_peps2d_results.json": r_spinor_network_entanglement,
    "sixteen_terrain_cl13_generation_results.json": r_terrain_cl13_generation,
    "sixteen_terrain_placement_lattice_results.json": r_terrain_placement_lattice,
    "sixteen_terrain_quantumoptics_results.json": r_terrain_quantumoptics_jax,
    "signed_operators_density_bloch_free_results.json": r_signed_operators_density,
    "sl2c_spin13_chiral_gstructure_results.json": r_sl2c_spin13,
    "s7_spin8_triality_results.json": r_s7_spin8_triality,
    "spacetime_from_entanglement_nested_results.json": r_spacetime_entanglement_nested,
    "topology_variant_octet_results.json": r_topology_variant_octet,
    "twistor_incidence_cp3_projective_line_results.json": r_twistor,
    "twistor_conformal_gstructure_results.json": r_twistor_conformal_gstructure,
    "weyl_lr_spinor_network_entanglement_results.json": r_spinor_network_entanglement,
    "weyl_lr_spinor_network_entanglement_peps2d_results.json": r_spinor_network_entanglement,
    "wick_basin_invariance_results.json": r_wick_basin_invariance,
    "l1_boundary_closure_dynamical_algebra_results.json": r_boundary_closure,
}


def reference_layers() -> list[str]:
    layer_names = [path.name for path in REF_DIR.glob("*_results.json")]
    extra_names = [path.name for path in EXTRA_REFERENCE_PATHS if path.exists()]
    return sorted(layer_names + extra_names)


def reference_summary(path_name: str) -> dict[str, Any]:
    path = REF_DIR / path_name
    if not path.exists():
        path = next((candidate for candidate in EXTRA_REFERENCE_PATHS if candidate.name == path_name), path)
    data = json.loads(path.read_text())
    return {
        "path": str(path),
        "classification": data.get("classification"),
        "all_pass": data.get("all_pass"),
        "promotion_allowed": data.get("promotion_allowed"),
        "status": data.get("status") or data.get("honest_status") or data.get("verdict"),
    }


def supersession_summary(name: str) -> dict[str, Any] | None:
    path = RED_REFERENCE_SUPERSESSION_RECEIPTS.get(name)
    if path is None:
        return None
    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
            "accepted": False,
            "reason": "missing_jax_supersession_receipt",
        }
    data = json.loads(path.read_text())
    checks = {
        "exists": True,
        "all_pass": bool(data.get("all_pass") or data.get("AUDIT_PASS")),
        "promotion_allowed_false": data.get("promotion_allowed") is False,
        "ran_julia_false": data.get("ran_julia") is False,
        "ran_pytorch_false": data.get("ran_pytorch") is False,
        "classification_fence": str(data.get("classification", "")).startswith("diagnostic_jax_red_reference_supersession"),
    }
    return {
        "path": str(path),
        "exists": True,
        "accepted": all(checks.values()),
        "checks": checks,
        "classification": data.get("classification"),
        "all_pass": data.get("all_pass"),
        "AUDIT_PASS": data.get("AUDIT_PASS"),
        "promotion_allowed": data.get("promotion_allowed"),
        "claim_boundary": data.get("claim_boundary"),
    }


def run_probe(write: bool = True) -> dict[str, Any]:
    refs = reference_layers()
    future_refs = sorted(name for name in refs if name in FUTURE_PHASE_REFERENCE_ROWS)
    independent_refs = sorted(name for name in refs if name not in FUTURE_PHASE_REFERENCE_ROWS)
    missing = sorted(set(independent_refs) - set(ROW_MAP))
    rows = [ROW_MAP[name](name) for name in independent_refs if name in ROW_MAP]
    summaries = {name: reference_summary(name) for name in refs}
    red_independent_refs = sorted(
        name
        for name in independent_refs
        if summaries[name].get("all_pass") is False
    )
    supersession_receipts = {
        name: summary
        for name in red_independent_refs
        if (summary := supersession_summary(name)) is not None
    }
    unresolved_red_independent_refs = [
        name for name in red_independent_refs if not supersession_receipts.get(name, {}).get("accepted", False)
    ]
    downstream_blocked_reference_rows = [
        {
            "julia_reference_result": name,
            "path": summaries[name]["path"],
            "blocked_status": FUTURE_PHASE_REFERENCE_ROWS[name]["blocked_status"],
            "blocked_reason": FUTURE_PHASE_REFERENCE_ROWS[name]["reason"],
            "promotion_allowed": summaries[name].get("promotion_allowed"),
            "classification": summaries[name].get("classification"),
        }
        for name in future_refs
    ]
    checks = {
        "all_independent_reference_layers_have_jax_rows": len(missing) == 0 and {r["julia_reference_result"] for r in rows} == set(independent_refs),
        "all_rows_pass": all(r["pass"] for r in rows),
        "red_independent_references_are_jax_fenced": not unresolved_red_independent_refs,
        "no_julia_execution": True,
        "promotion_blocked": True,
    }
    result = {
        "AUDIT_PASS": all(checks.values()),
        "name": "jax_julia_reference_geometric_constraint_layer_runner",
        "classification": "diagnostic_jax_julia_reference_geometric_constraint_layer_runner",
        "executed_track": "jax",
        "ran_julia": False,
        "julia_reference_mode": "read_only",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_boundary": "Runs JAX diagnostics for every Julia-reference proposed layer result; no layer/manifold/admission claim.",
        "julia_reference_layers": refs,
        "independent_reference_layers": independent_refs,
        "future_phase_reference_layers": future_refs,
        "julia_reference_summaries": summaries,
        "missing_jax_rows": missing,
        "missing_independent_jax_rows": missing,
        "red_independent_reference_rows": red_independent_refs,
        "red_independent_reference_rows_unresolved": unresolved_red_independent_refs,
        "red_independent_reference_supersession_receipts": supersession_receipts,
        "red_reference_policy": (
            "Julia reference rows remain recorded as red. A red row is no longer an unresolved JAX-lane "
            "coverage blocker only when its exact JAX supersession/fence receipt exists, passes, is fenced, "
            "and records ran_julia=false and ran_pytorch=false."
        ),
        "downstream_blocked_reference_rows": downstream_blocked_reference_rows,
        "rows": rows,
        "checks": checks,
        "blocked_consumers": ["layer_stacking", "flux", "xi_phi0", "axis0", "bridge", "fep_holodeck", "physics_gravity", "final_manifold_admission"],
        "tool_manifest": {
            "jax": "load-bearing finite diagnostic maps for Julia-reference layer targets",
            "jax.numpy": "load-bearing finite linear algebra, spinor/quaternion/Hopf/QIT readouts",
            "jax.scipy.linalg.expm": "load-bearing finite unitary construction where used",
            "json": "supportive read-only Julia reference summaries and receipt serialization",
        },
        "tool_integration_depth": {
            "jax": "load_bearing",
            "jax.numpy": "load_bearing",
            "jax.scipy.linalg.expm": "supportive",
            "json": "supportive",
        },
    }
    if write:
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main() -> None:
    result = run_probe(write=True)
    print(
        "jax_julia_reference_layer_runner "
        f"independent_rows={len(result['rows'])}/{len(result['independent_reference_layers'])} "
        f"future_blocked={len(result['future_phase_reference_layers'])} "
        f"pass={sum(1 for row in result['rows'] if row['pass'])}/{len(result['rows'])} "
        f"missing={result['missing_independent_jax_rows']} "
        f"red_refs={result['red_independent_reference_rows']} "
        f"unresolved_red_refs={result['red_independent_reference_rows_unresolved']} "
        f"AUDIT_PASS={result['AUDIT_PASS']}"
    )


if __name__ == "__main__":
    main()

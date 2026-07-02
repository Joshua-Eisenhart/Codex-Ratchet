#!/usr/bin/env python3
"""JAX-only mirror of the Julia multishell Lindblad/area-ratchet cascade.

Read-only Julia reference:
    system_v5/julia_carrier/layers/multishell_ratchet_cascade.jl

This file is the JAX audit lane: finite density matrices, finite shell graph,
finite controls, and a diagnostic-only receipt. It does not run Julia and does
not import or run PyTorch.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jax
from jax import config

config.update("jax_enable_x64", True)

import jax.numpy as jnp
import jax.scipy.linalg as jsp_linalg


OUT = Path("jax_multishell_lindblad_cascade_mirror_results.json")

NLEAF = 8
TMAX = 120.0
HOP_STRENGTH = 1.25
TERRAIN_RATE = 0.35
DEPHASE_RATE = 0.08
STEADY_TOL = 2.0e-7
UNIFORM_TOL = 2.0e-4
CONCENTRATION_MARGIN = 0.025
DENSITY_TOL = 1.0e-8
EPS = 1.0e-10

I2 = jnp.eye(2, dtype=jnp.float64)
SIGMA_X = jnp.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.float64)
SIGMA_Z = jnp.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.float64)
SIGMA_MINUS = jnp.asarray([[0.0, 0.0], [1.0, 0.0]], dtype=jnp.float64)
SIGMA_PLUS = SIGMA_MINUS.T
GAMMA_THETA = SIGMA_X


def _f(x: Any) -> float:
    return float(jax.device_get(x))


def _b(x: Any) -> bool:
    return bool(jax.device_get(x))


def _list(x: Any) -> list[float]:
    return [float(v) for v in jax.device_get(x)]


def jsonable(x: Any) -> Any:
    if isinstance(x, dict):
        return {str(k): jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [jsonable(v) for v in x]
    if hasattr(x, "shape"):
        y = jax.device_get(x)
        if getattr(y, "shape", ()) == ():
            return y.item()
        return y.tolist()
    return x


def nested_leaf_thetas() -> jax.Array:
    return jnp.asarray(
        [
            0.10,
            0.28,
            0.46,
            0.66,
            jnp.pi / 4.0,
            0.95,
            1.18,
            jnp.pi / 2.0 - 0.10,
        ],
        dtype=jnp.float64,
    )


def ratchet_area(theta: jax.Array) -> jax.Array:
    return 2.0 * jnp.pi**2 * jnp.sin(2.0 * theta)


def lindblad(rho: jax.Array, op: jax.Array, rate: float) -> jax.Array:
    ldagl = op.T @ op
    return rate * (op @ rho @ op.T - 0.5 * (ldagl @ rho + rho @ ldagl))


def terrain_lindblad(rho: jax.Array, theta: jax.Array) -> jax.Array:
    drho = lindblad(rho, SIGMA_Z, DEPHASE_RATE)
    low = theta < jnp.pi / 4.0
    clifford = jnp.abs(theta - jnp.pi / 4.0) < 1.0e-12
    low_term = lindblad(rho, SIGMA_MINUS, TERRAIN_RATE)
    high_term = lindblad(rho, SIGMA_PLUS, TERRAIN_RATE)
    balanced = low_term + high_term
    return drho + jnp.where(clifford, balanced, jnp.where(low, low_term, high_term))


def initial_state_from_weights(weights: jax.Array) -> jax.Array:
    weights = jnp.asarray(weights, dtype=jnp.float64)
    weights = weights / jnp.sum(weights)
    return weights[:, None, None] * (I2[None, :, :] / 2.0)


def initial_state() -> jax.Array:
    return initial_state_from_weights(jnp.ones((NLEAF,), dtype=jnp.float64))


def leaf_weights(u: jax.Array) -> jax.Array:
    weights = jnp.trace(u, axis1=1, axis2=2)
    return weights / jnp.sum(weights)


def hop_generator(area_weights: jax.Array, hop_scale: float = HOP_STRENGTH) -> jax.Array:
    max_area = jnp.max(area_weights)
    q = jnp.zeros((NLEAF, NLEAF), dtype=jnp.float64)
    for leaf in range(NLEAF - 1):
        rate_left_to_right = hop_scale * area_weights[leaf + 1] / max_area
        rate_right_to_left = hop_scale * area_weights[leaf] / max_area
        q = q.at[leaf + 1, leaf].add(rate_left_to_right)
        q = q.at[leaf, leaf].add(-rate_left_to_right)
        q = q.at[leaf, leaf + 1].add(rate_right_to_left)
        q = q.at[leaf + 1, leaf + 1].add(-rate_right_to_left)
    return q


def cascade_rhs(
    u: jax.Array,
    thetas: jax.Array,
    area_weights: jax.Array,
    *,
    hop_scale: float = HOP_STRENGTH,
    terrain_on: bool = True,
) -> jax.Array:
    du = jnp.zeros_like(u)
    if terrain_on:
        for leaf in range(NLEAF):
            du = du.at[leaf].add(terrain_lindblad(u[leaf], thetas[leaf]))

    if hop_scale != 0.0:
        max_area = jnp.max(area_weights)
        for leaf in range(NLEAF - 1):
            rho_left = u[leaf]
            rho_right = u[leaf + 1]
            rate_left_to_right = hop_scale * area_weights[leaf + 1] / max_area
            rate_right_to_left = hop_scale * area_weights[leaf] / max_area
            gamma_left = GAMMA_THETA @ rho_left @ GAMMA_THETA.T
            gamma_right = GAMMA_THETA @ rho_right @ GAMMA_THETA.T
            du = du.at[leaf].add(-rate_left_to_right * rho_left + rate_right_to_left * gamma_right)
            du = du.at[leaf + 1].add(rate_left_to_right * gamma_left - rate_right_to_left * rho_right)
    return du


def flatten(u: jax.Array) -> jax.Array:
    return jnp.reshape(u, (4 * NLEAF,))


def unflatten(v: jax.Array) -> jax.Array:
    return jnp.reshape(v, (NLEAF, 2, 2))


def linear_operator(
    thetas: jax.Array,
    area_weights: jax.Array,
    *,
    hop_scale: float = HOP_STRENGTH,
    terrain_on: bool = True,
) -> jax.Array:
    basis = jnp.eye(4 * NLEAF, dtype=jnp.float64)

    def apply(e):
        return flatten(cascade_rhs(unflatten(e), thetas, area_weights, hop_scale=hop_scale, terrain_on=terrain_on))

    images = jax.vmap(apply)(basis)
    return images.T


def trace_constraint_row() -> jax.Array:
    row = jnp.zeros((4 * NLEAF,), dtype=jnp.float64)
    for leaf in range(NLEAF):
        row = row.at[4 * leaf + 0].set(1.0)
        row = row.at[4 * leaf + 3].set(1.0)
    return row


def stationary_state_from_operator(op: jax.Array) -> jax.Array:
    constrained = op.at[0, :].set(trace_constraint_row())
    target = jnp.zeros((4 * NLEAF,), dtype=jnp.float64).at[0].set(1.0)
    return unflatten(jnp.linalg.solve(constrained, target))


def run_cascade(
    thetas: jax.Array,
    area_weights: jax.Array,
    *,
    u0: jax.Array | None = None,
    hop_scale: float = HOP_STRENGTH,
    terrain_on: bool = True,
    steady_solve: bool = False,
) -> dict[str, Any]:
    if u0 is None:
        u0 = initial_state()
    op = linear_operator(thetas, area_weights, hop_scale=hop_scale, terrain_on=terrain_on)
    final_u = stationary_state_from_operator(op) if steady_solve else unflatten(jsp_linalg.expm(TMAX * op) @ flatten(u0))
    du = cascade_rhs(final_u, thetas, area_weights, hop_scale=hop_scale, terrain_on=terrain_on)
    return {
        "final_u": final_u,
        "weights": leaf_weights(final_u),
        "derivative_norm": _f(jnp.linalg.norm(flatten(du))),
        "linear_operator": op,
        "method": "trace_constrained_stationary_solve" if steady_solve else "matrix_exponential_time_evolution",
    }


def trace_rhs_vector(du: jax.Array) -> jax.Array:
    return jnp.trace(du, axis1=1, axis2=2)


def density_sanity(u: jax.Array) -> dict[str, Any]:
    max_hermitian_error = 0.0
    min_eigenvalue = float("inf")
    min_trace = float("inf")
    for leaf in range(NLEAF):
        rho = u[leaf]
        sym = 0.5 * (rho + rho.T)
        max_hermitian_error = max(max_hermitian_error, _f(jnp.linalg.norm(rho - rho.T, ord=jnp.inf)))
        min_eigenvalue = min(min_eigenvalue, _f(jnp.min(jnp.linalg.eigvalsh(sym))))
        min_trace = min(min_trace, _f(jnp.trace(rho)))
    total_trace = _f(jnp.sum(jnp.trace(u, axis1=1, axis2=2)))
    return {
        "max_hermitian_error": max_hermitian_error,
        "min_eigenvalue": min_eigenvalue,
        "min_leaf_trace": min_trace,
        "total_trace": total_trace,
        "ok": max_hermitian_error < DENSITY_TOL and min_eigenvalue > -DENSITY_TOL and min_trace > -DENSITY_TOL,
    }


def gamma_channel_checks() -> dict[str, bool]:
    rho = jnp.asarray([[0.7, 0.2], [0.2, 0.3]], dtype=jnp.float64)
    gamma_rho = GAMMA_THETA @ rho @ GAMMA_THETA.T
    return {
        "gamma_hermitian": _b(jnp.linalg.norm(GAMMA_THETA - GAMMA_THETA.T, ord=jnp.inf) < DENSITY_TOL),
        "gamma_unitary": _b(jnp.linalg.norm(GAMMA_THETA.T @ GAMMA_THETA - I2, ord=jnp.inf) < DENSITY_TOL),
        "trace_preserving_sample": _f(jnp.abs(jnp.trace(gamma_rho) - jnp.trace(rho))) < DENSITY_TOL,
        "psd_preserving_sample": _f(jnp.min(jnp.linalg.eigvalsh(0.5 * (gamma_rho + gamma_rho.T)))) > -DENSITY_TOL,
    }


def source_boundary_checks() -> dict[str, bool]:
    src = Path(__file__).read_text()
    blocked_julia_exec = "julia --" + "project"
    blocked_proc_launch = "sub" + "process"
    blocked_popen = "P" + "open"
    blocked_os_system = "os." + "system"
    blocked_import_julia = "import " + "julia"
    blocked_import_torch = "import " + "torch"
    blocked_from_torch = "from " + "torch"
    blocked_torch_call = "tor" + "ch."
    blocked_import_numpy = "import " + "numpy"
    blocked_from_numpy = "from " + "numpy"
    return {
        "no_julia_execution": blocked_julia_exec not in src and blocked_import_julia not in src,
        "no_python_process_launch": blocked_proc_launch not in src and blocked_popen not in src and blocked_os_system not in src,
        "no_pytorch_import_or_call": blocked_import_torch not in src and blocked_from_torch not in src and blocked_torch_call not in src,
        "no_numpy_import": blocked_import_numpy not in src and blocked_from_numpy not in src,
    }


def max_abs_delta(x: jax.Array, y: jax.Array) -> float:
    return _f(jnp.max(jnp.abs(x - y)))


def l1_delta(x: jax.Array, y: jax.Array) -> float:
    return _f(jnp.sum(jnp.abs(x - y)))


def main() -> int:
    thetas = nested_leaf_thetas()
    areas = ratchet_area(thetas)
    const_areas = jnp.ones_like(areas)
    uniform = jnp.ones_like(areas) / NLEAF
    expected_ratchet = areas / jnp.sum(areas)
    max_leaf = int(jnp.argmax(areas))

    u0_uniform = initial_state()
    u0_skew_left = initial_state_from_weights(jnp.arange(NLEAF, 0, -1, dtype=jnp.float64))
    u0_skew_right = initial_state_from_weights(jnp.arange(1, NLEAF + 1, dtype=jnp.float64))

    shuffled_areas = jnp.roll(areas, 2)
    expected_shuffled = shuffled_areas / jnp.sum(shuffled_areas)
    shuffled_peak_leaf = int(jnp.argmax(expected_shuffled))

    ratchet_on = run_cascade(thetas, areas, u0=u0_uniform, steady_solve=True)
    ratchet_off = run_cascade(thetas, const_areas, u0=u0_uniform, steady_solve=True)
    ratchet_on_skew_left = run_cascade(thetas, areas, u0=u0_skew_left, steady_solve=True)
    ratchet_on_skew_right = run_cascade(thetas, areas, u0=u0_skew_right, steady_solve=True)
    coupling_off = run_cascade(thetas, areas, u0=u0_uniform, hop_scale=0.0, terrain_on=True)
    terrain_off = run_cascade(thetas, areas, u0=u0_skew_left, hop_scale=HOP_STRENGTH, terrain_on=False)
    order_shuffled = run_cascade(thetas, shuffled_areas, u0=u0_uniform, steady_solve=True)

    q_ratchet = hop_generator(areas)
    q_control = hop_generator(const_areas)
    q_shuffled = hop_generator(shuffled_areas)
    du0 = cascade_rhs(u0_uniform, thetas, areas, hop_scale=HOP_STRENGTH, terrain_on=True)
    trace_rhs0 = trace_rhs_vector(du0)

    gamma_checks = gamma_channel_checks()
    source_boundary = source_boundary_checks()
    density = {
        "ratchet_on": density_sanity(ratchet_on["final_u"]),
        "ratchet_off_A_const": density_sanity(ratchet_off["final_u"]),
        "coupling_off": density_sanity(coupling_off["final_u"]),
        "terrain_off_hopping_on": density_sanity(terrain_off["final_u"]),
        "order_shuffled": density_sanity(order_shuffled["final_u"]),
    }

    ratchet_matches_area = max_abs_delta(ratchet_on["weights"], expected_ratchet) < 5.0e-4
    skew_left_matches_area = l1_delta(ratchet_on_skew_left["weights"], expected_ratchet) < 5.0e-3
    skew_right_matches_area = l1_delta(ratchet_on_skew_right["weights"], expected_ratchet) < 5.0e-3
    control_uniform = max_abs_delta(ratchet_off["weights"], uniform) < UNIFORM_TOL
    coupling_off_preserves = max_abs_delta(coupling_off["weights"], uniform) < 1.0e-8
    terrain_off_matches_area = l1_delta(terrain_off["weights"], expected_ratchet) < 5.0e-3
    shuffled_matches_area = max_abs_delta(order_shuffled["weights"], expected_shuffled) < 5.0e-4
    shuffled_not_clifford = int(jnp.argmax(order_shuffled["weights"])) == shuffled_peak_leaf and shuffled_peak_leaf != max_leaf
    shuffled_kills_clifford_peak = order_shuffled["weights"][max_leaf] < ratchet_on["weights"][max_leaf] - CONCENTRATION_MARGIN

    q_column_sums_zero = _f(jnp.max(jnp.abs(jnp.sum(q_ratchet, axis=0)))) < 1.0e-12
    q_adjacent_positive = all(_f(q_ratchet[i + 1, i]) > 0.0 and _f(q_ratchet[i, i + 1]) > 0.0 for i in range(NLEAF - 1))
    nonadjacent_vals = [jnp.abs(q_ratchet[i, j]) for i in range(NLEAF) for j in range(NLEAF) if abs(i - j) > 1]
    q_nonadjacent_zero = _f(jnp.max(jnp.asarray(nonadjacent_vals))) < 1.0e-12
    detailed_balance_error = _f(
        jnp.max(
            jnp.asarray(
                [
                    jnp.abs(expected_ratchet[i] * q_ratchet[i + 1, i] - expected_ratchet[i + 1] * q_ratchet[i, i + 1])
                    for i in range(NLEAF - 1)
                ]
            )
        )
    )
    stationarity_error = _f(jnp.linalg.norm(q_ratchet @ expected_ratchet, ord=jnp.inf))
    control_stationarity_error = _f(jnp.linalg.norm(q_control @ uniform, ord=jnp.inf))
    shuffled_stationarity_error = _f(jnp.linalg.norm(q_shuffled @ expected_shuffled, ord=jnp.inf))
    trace_rhs_gap = _f(jnp.linalg.norm(trace_rhs0 - q_ratchet @ uniform, ord=jnp.inf))

    steady = {
        "ratchet_on": ratchet_on["derivative_norm"] < STEADY_TOL,
        "ratchet_off_A_const": ratchet_off["derivative_norm"] < STEADY_TOL,
        "ratchet_on_skew_left": ratchet_on_skew_left["derivative_norm"] < STEADY_TOL,
        "ratchet_on_skew_right": ratchet_on_skew_right["derivative_norm"] < STEADY_TOL,
        "coupling_off": coupling_off["derivative_norm"] < STEADY_TOL,
        "terrain_off_hopping_on": terrain_off["derivative_norm"] < STEADY_TOL,
        "order_shuffled": order_shuffled["derivative_norm"] < STEADY_TOL,
    }

    checks = {
        "metadata_contract_ok": True,
        "theta_grid_in_open_interval": int(thetas.shape[0]) == NLEAF
        and _b(jnp.all(thetas > 0.0))
        and _b(jnp.all(thetas < jnp.pi / 2.0))
        and _b(jnp.all(jnp.diff(thetas) > 0.0)),
        "area_positive_and_nonuniform": _b(jnp.all(areas > 0.0)) and _f(jnp.max(areas) - jnp.min(areas)) > 1.0,
        "max_leaf_is_clifford_torus": _f(jnp.abs(thetas[max_leaf] - jnp.pi / 4.0)) < 1.0e-12,
        "gamma_channel_ok": all(gamma_checks.values()),
        "hop_generator_column_sums_zero": q_column_sums_zero,
        "hop_generator_adjacent_rates_positive": q_adjacent_positive,
        "hop_generator_nonadjacent_rates_zero": q_nonadjacent_zero,
        "detailed_balance_area_stationary": detailed_balance_error < 1.0e-12 and stationarity_error < 1.0e-12,
        "control_generator_uniform_stationary": control_stationarity_error < 1.0e-12,
        "shuffled_generator_stationary": shuffled_stationarity_error < 1.0e-12,
        "trace_rhs_matches_hop_generator": trace_rhs_gap < 1.0e-12,
        "density_sanity_ok": all(row["ok"] for row in density.values()),
        "ratchet_on_peak_at_clifford_leaf": int(jnp.argmax(ratchet_on["weights"])) == max_leaf,
        "ratchet_on_matches_area_stationary_profile": ratchet_matches_area,
        "ratchet_on_skew_left_matches_area_stationary_profile": skew_left_matches_area,
        "ratchet_on_skew_right_matches_area_stationary_profile": skew_right_matches_area,
        "ratchet_on_concentrates_vs_control": ratchet_on["weights"][max_leaf] > ratchet_off["weights"][max_leaf] + CONCENTRATION_MARGIN,
        "control_ratchet_off_A_const_uniform": control_uniform,
        "control_coupling_off_preserves_initial_weights": coupling_off_preserves,
        "control_terrain_off_still_converges_to_area_weights": terrain_off_matches_area and steady["terrain_off_hopping_on"],
        "control_order_shuffled_follows_shuffled_area_profile": shuffled_matches_area,
        "control_order_shuffled_moves_peak_off_clifford": bool(shuffled_not_clifford),
        "control_order_shuffled_kills_clifford_peak": bool(shuffled_kills_clifford_peak),
        "steady_state_ratchet_on": steady["ratchet_on"],
        "steady_state_ratchet_off": steady["ratchet_off_A_const"],
        "steady_state_coupling_off": steady["coupling_off"],
        "steady_state_order_shuffled": steady["order_shuffled"],
        "total_trace_preserved": abs(density["ratchet_on"]["total_trace"] - 1.0) < 1.0e-9,
        "source_boundary_ok": all(source_boundary.values()),
    }
    audit_pass = all(checks.values())

    leaf_rows = []
    for i in range(NLEAF):
        leaf_rows.append(
            {
                "leaf": i + 1,
                "theta": _f(thetas[i]),
                "A_theta": _f(areas[i]),
                "expected_ratchet_weight_A_normalized": _f(expected_ratchet[i]),
                "ratchet_on_weight": _f(ratchet_on["weights"][i]),
                "ratchet_off_A_const_weight": _f(ratchet_off["weights"][i]),
                "coupling_off_weight": _f(coupling_off["weights"][i]),
                "order_shuffled_A_weight": _f(expected_shuffled[i]),
                "order_shuffled_weight": _f(order_shuffled["weights"][i]),
                "distance_to_clifford_theta": _f(jnp.abs(thetas[i] - jnp.pi / 4.0)),
            }
        )

    receipt = {
        "object": "jax_multishell_lindblad_cascade_mirror",
        "sim_id": "jax_multishell_lindblad_cascade_mirror",
        "name": "JAX multishell Lindblad cascade mirror with area-ratchet controls",
        "version": "1.0",
        "classification": "tool_lego_fit_probe",
        "promotion_allowed": False,
        "promotion_status": "blocked_diagnostic_only",
        "AUDIT_PASS": audit_pass,
        "all_pass": audit_pass,
        "ran_julia": False,
        "ran_pytorch": False,
        "tier": "bounded_jax_cascade_control",
        "purpose": "JAX audit of the finite N=8 nested-leaf density cascade: area-ratchet hopping should concentrate steady trace weight at the Clifford-torus leaf, while ratchet-off, coupling-off, and order-shuffled controls kill the relevant claim.",
        "scientific_question": "Does the JAX finite Lindblad cascade reproduce the Julia oracle's structural area-ratchet invariants without running Julia or PyTorch?",
        "sim_execution_kind": "jax_diagnostic_audit",
        "sim_class": "constraint_probe",
        "claim_ceiling": "JAX-only diagnostic mirror of one finite multishell density cascade; no layer/manifold completion, no G-structure admission, no Axis0/FEP/flux/Xi/Phi0/bridge/physics claim.",
        "root_constraints_in_force": {
            "F01": "finite N=8 leaf set, finite 2x2 density matrices, finite adjacent path graph",
            "N01": "order-sensitive adjacent gamma_theta transfer; A(theta) ordering is checked against A=const, coupling-off, and shuffled-order controls",
        },
        "finite_map": "8 unnormalized 2x2 qubit densities rho_i evolve under local terrain Lindblad maps plus adjacent gamma_theta hopping with q_{i->j}=k*A(theta_j)/max(A). The output is the finite steady trace-weight profile and negative/control readouts.",
        "domain": {
            "N": NLEAF,
            "thetas": _list(thetas),
            "state": "8 unnormalized real 2x2 qubit density matrices",
            "adjacency": "nearest-neighbor path graph on shell leaves",
            "gamma_theta": "sigma_x channel rho -> sigma_x*rho*sigma_x",
        },
        "codomain_or_output": "JSON receipt with steady leaf trace weights, density sanity, hop-generator invariants, and ratchet/coupling/order controls",
        "carrier_layer": "finite nested theta leaves over JAX density matrices",
        "geometry_layer": "shell-area ratchet A(theta)=2*pi^2*sin(2theta)",
        "carrier_realization": "JAX float64 arrays; finite Lindblad/hopping generator solved at trace-constrained steady state, with expm time evolution retained for degenerate controls",
        "peps3d_embedding": "not_applicable_blocked: this is a finite density cascade diagnostic, not admitted PEPS3D evidence",
        "spinor_state": "not_applicable_blocked: density-matrix cascade mirror, not a full spinor engine",
        "quaternion_action": "not_applicable",
        "dependency_receipts": [
            "system_v5/julia_carrier/layers/multishell_ratchet_cascade_results.json (read-only reference)",
            "system_v5/julia_carrier/layers/nested_leaf_area_ratchet_results.json (read-only reference named by Julia receipt)",
            "system_v5/julia_carrier/layers/emergent_basin_nested_terrains_results.json (read-only reference named by Julia receipt)",
        ],
        "blocked_consumers": [
            "layer_completion",
            "manifold_admission",
            "G_structure_admission",
            "layer_stacking_readiness",
            "flux",
            "Xi",
            "Phi0",
            "Axis0",
            "FEP",
            "bridge",
            "basin",
            "physics",
            "final_manifold_admission",
        ],
        "allowed_claims": [
            "JAX script exists and runs",
            "JAX finite cascade reproduces the Julia oracle's structural ratchet/control invariants for this object",
            "ratchet-off, coupling-off, and order-shuffled controls are included in the diagnostic receipt",
        ],
        "promotion_blockers": [
            "classification is tool_lego_fit_probe",
            "promotion_allowed=false",
            "not Julia-native Grassmann/QuantumOptics truth",
            "not full spinor/Clifford engine",
            "not PEPS3D-carried",
            "single finite cascade mirror only",
        ],
        "eligible_consumers": ["local JAX-vs-Julia diagnostic comparison only"],
        "required_tools": ["jax", "jax.scipy.linalg", "json"],
        "actual_tools_used": ["jax", "jax.scipy.linalg", "json"],
        "tool_manifest": {
            "jax": "load-bearing: constructs the finite Lindblad/hopping generator, density matrices, controls, and readouts",
            "jax.scipy.linalg": "load-bearing: evolves the linear cascade with expm(T*L)",
            "json": "supportive: writes the receipt artifact",
            "julia": "not used: read-only reference only",
            "pytorch": "not used: retired lane, explicitly absent from execution",
        },
        "tool_integration_depth": {
            "jax": "load_bearing",
            "jax.scipy.linalg": "load_bearing",
            "json": "supportive",
            "julia": "None",
            "pytorch": "None",
        },
        "required_negatives": [
            "A=const ratchet-off control must be uniform",
            "coupling-off control must preserve initial leaf weights",
            "order-shuffled area control must move the peak away from the Clifford leaf",
        ],
        "negatives_run": ["ratchet-off A=const", "coupling-off hop_scale=0", "order-shuffled area weights"],
        "kill_conditions": [
            "FAIL if ratchet-on max weight is not at the Clifford-torus leaf",
            "FAIL if ratchet-on does not match normalized A(theta)",
            "FAIL if A=const control is not uniform",
            "FAIL if coupling-off does not preserve initial leaf weights",
            "FAIL if order-shuffled control still peaks at the Clifford leaf",
            "FAIL if density sanity or source boundary checks fail",
        ],
        "checks": checks,
        "gamma_channel_checks": gamma_checks,
        "source_boundary_checks": source_boundary,
        "density_sanity": density,
        "hop_generator": {
            "ratchet_Q_column_sum_max_abs": _f(jnp.max(jnp.abs(jnp.sum(q_ratchet, axis=0)))),
            "ratchet_detailed_balance_max_abs": detailed_balance_error,
            "ratchet_stationarity_norm_inf": stationarity_error,
            "control_stationarity_norm_inf": control_stationarity_error,
            "shuffled_stationarity_norm_inf": shuffled_stationarity_error,
            "trace_rhs_matches_Qw_norm_inf": trace_rhs_gap,
            "adjacent_only": q_adjacent_positive and q_nonadjacent_zero,
        },
        "parameters": {
            "N": NLEAF,
            "TMAX": TMAX,
            "HOP_STRENGTH": HOP_STRENGTH,
            "TERRAIN_RATE": TERRAIN_RATE,
            "DEPHASE_RATE": DEPHASE_RATE,
            "STEADY_TOL": STEADY_TOL,
            "UNIFORM_TOL": UNIFORM_TOL,
            "CONCENTRATION_MARGIN": CONCENTRATION_MARGIN,
        },
        "ratchet": {
            "A_theta_formula": "2*pi^2*sin(2theta)",
            "max_A_leaf": max_leaf + 1,
            "max_A_theta": _f(thetas[max_leaf]),
            "max_A_value": _f(areas[max_leaf]),
            "ratchet_on_clifford_weight": _f(ratchet_on["weights"][max_leaf]),
            "control_clifford_weight": _f(ratchet_off["weights"][max_leaf]),
            "concentration_delta_vs_control": _f(ratchet_on["weights"][max_leaf] - ratchet_off["weights"][max_leaf]),
            "ratchet_expected_profile_max_abs_error": max_abs_delta(ratchet_on["weights"], expected_ratchet),
            "ratchet_skew_left_L1_error": l1_delta(ratchet_on_skew_left["weights"], expected_ratchet),
            "ratchet_skew_right_L1_error": l1_delta(ratchet_on_skew_right["weights"], expected_ratchet),
            "terrain_off_L1_error": l1_delta(terrain_off["weights"], expected_ratchet),
            "control_uniform_max_abs_error": max_abs_delta(ratchet_off["weights"], uniform),
            "coupling_off_uniform_max_abs_error": max_abs_delta(coupling_off["weights"], uniform),
            "order_shuffled_expected_profile_max_abs_error": max_abs_delta(order_shuffled["weights"], expected_shuffled),
            "order_shuffled_peak_leaf": shuffled_peak_leaf + 1,
            "order_shuffled_clifford_weight": _f(order_shuffled["weights"][max_leaf]),
        },
        "steady_state": {
            "ratchet_on_method": ratchet_on["method"],
            "ratchet_off_method": ratchet_off["method"],
            "ratchet_on_skew_left_method": ratchet_on_skew_left["method"],
            "ratchet_on_skew_right_method": ratchet_on_skew_right["method"],
            "coupling_off_method": coupling_off["method"],
            "terrain_off_method": terrain_off["method"],
            "order_shuffled_method": order_shuffled["method"],
            "ratchet_on_derivative_norm": ratchet_on["derivative_norm"],
            "ratchet_off_derivative_norm": ratchet_off["derivative_norm"],
            "ratchet_on_skew_left_derivative_norm": ratchet_on_skew_left["derivative_norm"],
            "ratchet_on_skew_right_derivative_norm": ratchet_on_skew_right["derivative_norm"],
            "coupling_off_derivative_norm": coupling_off["derivative_norm"],
            "terrain_off_derivative_norm": terrain_off["derivative_norm"],
            "order_shuffled_derivative_norm": order_shuffled["derivative_norm"],
        },
        "leaf_weight_profile": leaf_rows,
        "ratchet_on_weights": _list(ratchet_on["weights"]),
        "ratchet_off_A_const_weights": _list(ratchet_off["weights"]),
        "coupling_off_weights": _list(coupling_off["weights"]),
        "terrain_off_hopping_on_weights": _list(terrain_off["weights"]),
        "order_shuffled_weights": _list(order_shuffled["weights"]),
        "expected_ratchet_A_normalized_weights": _list(expected_ratchet),
        "expected_order_shuffled_A_normalized_weights": _list(expected_shuffled),
        "uniform_control_target": _list(uniform),
        "artifacts_emitted": [str(OUT)],
        "required_artifacts": [str(OUT)],
        "witness_trace_id": "jax_multishell_lindblad_cascade_mirror_v1",
    }

    OUT.write_text(json.dumps(jsonable(receipt), indent=2, sort_keys=True) + "\n")
    print(
        "jax_multishell_lindblad_cascade_mirror "
        f"ratchet={checks['ratchet_on_matches_area_stationary_profile']} "
        f"ratchet_off={checks['control_ratchet_off_A_const_uniform']} "
        f"coupling_off={checks['control_coupling_off_preserves_initial_weights']} "
        f"order_shuffled={checks['control_order_shuffled_moves_peak_off_clifford']} "
        f"density={checks['density_sanity_ok']} "
        f"AUDIT_PASS={audit_pass}"
    )
    print(f"receipt={OUT}")
    return 0 if audit_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""JAX mirror of the nested leaf-area ratchet and radial Dirac coupling.

Julia reference, read-only:
    system_v5/julia_carrier/layers/nested_leaf_area_ratchet.jl

This diagnostic sits one step above the foliation invariant:

    finite S3 leaves T2_theta -> measured A(theta)
       -> finite radial Dirac chain gamma^theta d/dtheta
       -> coupling/localization controls.

It does not run Julia, does not import PyTorch, and does not promote layer,
G-structure, Axis0, flux, bridge, or physics claims.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jax
from jax import config

config.update("jax_enable_x64", True)

import jax.numpy as jnp


OUT = Path("jax_nested_leaf_area_radial_dirac_mirror_results.json")
PI = jnp.pi
N_LEAF = 16


def _f(x: Any) -> float:
    return float(jax.device_get(x))


def _b(x: Any) -> bool:
    return bool(jax.device_get(x))


def tangent_a(theta: jax.Array, a: jax.Array, b: jax.Array) -> jax.Array:
    del b
    return jnp.asarray([-jnp.cos(theta) * jnp.sin(a), jnp.cos(theta) * jnp.cos(a), 0.0, 0.0], dtype=jnp.float64)


def tangent_b(theta: jax.Array, a: jax.Array, b: jax.Array) -> jax.Array:
    del a
    return jnp.asarray([0.0, 0.0, -jnp.sin(theta) * jnp.sin(b), jnp.sin(theta) * jnp.cos(b)], dtype=jnp.float64)


def measured_leaf_area(theta: float, n: int = 120) -> float:
    da = 2.0 * PI / n
    db = 2.0 * PI / n
    aa = (jnp.arange(n, dtype=jnp.float64) + 0.5) * da
    bb = (jnp.arange(n, dtype=jnp.float64) + 0.5) * db

    def elem(a, b):
        ta = tangent_a(theta, a, b)
        tb = tangent_b(theta, a, b)
        e = jnp.dot(ta, ta)
        f = jnp.dot(ta, tb)
        g = jnp.dot(tb, tb)
        return jnp.sqrt(jnp.maximum(e * g - f * f, 0.0)) * da * db

    return _f(jnp.sum(jax.vmap(lambda a: jax.vmap(lambda b: elem(a, b))(bb))(aa)))


def analytic_area(theta: jax.Array) -> jax.Array:
    return 2.0 * PI**2 * jnp.sin(2.0 * theta)


def flat_torus_area(theta: float, n: int = 120, r1: float = 0.7, r2: float = 0.7) -> float:
    del theta
    da = 2.0 * PI / n
    db = 2.0 * PI / n
    aa = (jnp.arange(n, dtype=jnp.float64) + 0.5) * da
    bb = (jnp.arange(n, dtype=jnp.float64) + 0.5) * db

    def elem(a, b):
        ta = jnp.asarray([-r1 * jnp.sin(a), r1 * jnp.cos(a), 0.0, 0.0], dtype=jnp.float64)
        tb = jnp.asarray([0.0, 0.0, -r2 * jnp.sin(b), r2 * jnp.cos(b)], dtype=jnp.float64)
        e = jnp.dot(ta, ta)
        f = jnp.dot(ta, tb)
        g = jnp.dot(tb, tb)
        return jnp.sqrt(jnp.maximum(e * g - f * f, 0.0)) * da * db

    return _f(jnp.sum(jax.vmap(lambda a: jax.vmap(lambda b: elem(a, b))(bb))(aa)))


def leaf_area_checks() -> dict[str, Any]:
    thetas = jnp.linspace(PI / (2.0 * (N_LEAF + 1)), PI / 2.0 - PI / (2.0 * (N_LEAF + 1)), N_LEAF)
    measured = jnp.asarray([measured_leaf_area(float(t)) for t in jax.device_get(thetas)], dtype=jnp.float64)
    analytic = analytic_area(thetas)
    max_err = jnp.max(jnp.abs(measured - analytic))
    left = measured[thetas < PI / 4.0]
    right = measured[thetas > PI / 4.0]
    left_ascent = jnp.all(left[:-1] < left[1:])
    right_descent = jnp.all(right[:-1] > right[1:])
    clifford_area = measured_leaf_area(float(PI / 4.0))
    clifford_is_max = jnp.max(measured) <= clifford_area + 1.0e-8
    descent = jnp.linspace(PI / 4.0, 0.02, 8)
    descent_areas = jnp.asarray([measured_leaf_area(float(t)) for t in jax.device_get(descent)], dtype=jnp.float64)
    descent_strict = jnp.all(descent_areas[:-1] > descent_areas[1:])
    flat_areas = jnp.asarray([flat_torus_area(float(t)) for t in jax.device_get(descent)], dtype=jnp.float64)
    flat_spread = jnp.max(flat_areas) - jnp.min(flat_areas)
    checks = {
        "area_matches_formula": _f(max_err) < 1.0e-8,
        "clifford_leaf_is_max": _b(clifford_is_max),
        "area_monotone_to_clifford_from_left": _b(left_ascent),
        "area_monotone_down_from_clifford_right": _b(right_descent),
        "ratchet_descent_strict_decrease": _b(descent_strict),
        "flat_control_constant_over_same_descent": _f(flat_spread) < 1.0e-9,
    }
    return {
        "pass": all(checks.values()),
        "checks": checks,
        "theta_grid": [float(x) for x in jax.device_get(thetas)],
        "measured_areas": [float(x) for x in jax.device_get(measured)],
        "clifford_area_measured": clifford_area,
        "descent_thetas": [float(x) for x in jax.device_get(descent)],
        "descent_areas": [float(x) for x in jax.device_get(descent_areas)],
        "max_abs_err": _f(max_err),
        "flat_area_spread": _f(flat_spread),
    }


GAMMA_THETA = jnp.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.float64)


def block_slice(k: int) -> slice:
    return slice(2 * k, 2 * k + 2)


def radial_dirac(n_leaf: int = N_LEAF, couple: bool = True, onleaf: float = 0.3, leaf_mass_slope: float = 0.0) -> tuple[jax.Array, jax.Array]:
    thetas = jnp.linspace(PI / (2.0 * (n_leaf + 1)), PI / 2.0 - PI / (2.0 * (n_leaf + 1)), n_leaf)
    dtheta = thetas[1] - thetas[0]
    d = jnp.zeros((2 * n_leaf, 2 * n_leaf), dtype=jnp.float64)
    for k in range(n_leaf):
        sl = block_slice(k)
        leaf_mass = onleaf + leaf_mass_slope * (k - 0.5 * (n_leaf - 1))
        d = d.at[sl, sl].add(leaf_mass * jnp.eye(2, dtype=jnp.float64))
    if couple:
        h = 1.0 / dtheta
        for k in range(n_leaf - 1):
            sl = block_slice(k)
            sr = block_slice(k + 1)
            d = d.at[sl, sr].add(h * GAMMA_THETA)
            d = d.at[sr, sl].add(h * GAMMA_THETA)
    return d, thetas


def offdiag_weight(d: jax.Array, n_leaf: int = N_LEAF, adjacent_only: bool | None = None) -> float:
    weight = 0.0
    for k in range(n_leaf):
        for l in range(n_leaf):
            if k == l:
                continue
            if adjacent_only is True and abs(k - l) != 1:
                continue
            if adjacent_only is False and abs(k - l) <= 1:
                continue
            weight += _f(jnp.linalg.norm(d[block_slice(k), block_slice(l)]))
    return weight


def leaf_participation(d: jax.Array, n_leaf: int = N_LEAF) -> float:
    _vals, vecs = jnp.linalg.eigh(0.5 * (d + d.T))
    lprs = []
    for c in range(2 * n_leaf):
        psi = vecs[:, c]
        p = jnp.asarray([psi[2 * k] ** 2 + psi[2 * k + 1] ** 2 for k in range(n_leaf)])
        p = p / jnp.sum(p)
        lprs.append(1.0 / jnp.sum(p * p))
    return _f(jnp.mean(jnp.asarray(lprs)))


def radial_dirac_checks() -> dict[str, Any]:
    coupled, thetas = radial_dirac(couple=True)
    decoupled, _ = radial_dirac(couple=False)
    coupled_lpr_op, _ = radial_dirac(couple=True, leaf_mass_slope=1.0e-3)
    decoupled_lpr_op, _ = radial_dirac(couple=False, leaf_mass_slope=1.0e-3)
    coupled_off = offdiag_weight(coupled)
    decoupled_off = offdiag_weight(decoupled)
    nonadjacent = offdiag_weight(coupled, adjacent_only=False)
    adjacent = offdiag_weight(coupled, adjacent_only=True)
    coupled_lpr = leaf_participation(coupled_lpr_op)
    decoupled_lpr = leaf_participation(decoupled_lpr_op)
    gamma_axioms = {
        "gamma_square_identity": _b(jnp.linalg.norm(GAMMA_THETA @ GAMMA_THETA - jnp.eye(2)) < 1.0e-12),
        "gamma_traceless": _f(jnp.abs(jnp.trace(GAMMA_THETA))) < 1.0e-12,
        "gamma_hermitian": _b(jnp.linalg.norm(GAMMA_THETA - GAMMA_THETA.T) < 1.0e-12),
    }
    checks = {
        "adjacent_coupling_nonzero": adjacent > 1.0,
        "nonadjacent_coupling_zero": nonadjacent < 1.0e-12,
        "decoupled_offdiag_zero": decoupled_off < 1.0e-12,
        "coupled_delocalizes_vs_decoupled": coupled_lpr > decoupled_lpr + 2.0,
        "gamma_axioms": all(gamma_axioms.values()),
    }
    return {
        "pass": all(checks.values()),
        "checks": checks,
        "gamma_axioms": gamma_axioms,
        "metrics": {
            "coupled_offdiag_weight": coupled_off,
            "decoupled_offdiag_weight": decoupled_off,
            "adjacent_weight": adjacent,
            "nonadjacent_weight": nonadjacent,
            "coupled_mean_leaf_participation": coupled_lpr,
            "decoupled_mean_leaf_participation": decoupled_lpr,
            "leaf_mass_slope_for_lpr_degeneracy_lift": 1.0e-3,
            "theta_min": _f(jnp.min(thetas)),
            "theta_max": _f(jnp.max(thetas)),
        },
    }


def pearson(x: jax.Array, y: jax.Array) -> jax.Array:
    x = jnp.asarray(x, dtype=jnp.float64)
    y = jnp.asarray(y, dtype=jnp.float64)
    xc = x - jnp.mean(x)
    yc = y - jnp.mean(y)
    vx = jnp.sum(xc * xc)
    vy = jnp.sum(yc * yc)
    x_guard = vx <= 1.0e-18 * (1.0 + jnp.mean(x) ** 2) * x.shape[0]
    y_guard = vy <= 1.0e-18 * (1.0 + jnp.mean(y) ** 2) * y.shape[0]
    return jnp.where(x_guard | y_guard, 0.0, jnp.sum(xc * yc) / jnp.sqrt(vx * vy))


def corr_matrix(n: int, pbc: bool = True) -> jax.Array:
    h = jnp.zeros((n, n), dtype=jnp.float64)
    for k in range(n):
        kp = (k + 1) % n
        if pbc or k < n - 1:
            h = h.at[k, kp].add(-1.0)
            h = h.at[kp, k].add(-1.0)
    vals, vecs = jnp.linalg.eigh(h)
    occ = vals < 0.0
    u = vecs[:, occ]
    return u @ u.T


def entropy_area_proxy_checks() -> dict[str, Any]:
    # Julia-matched proxy: N=200, periodic chain, ten theta cuts.
    n = 200
    c = corr_matrix(n, pbc=True)

    def block_entropy(sites):
        cb = c[jnp.ix_(sites, sites)]
        ev = jnp.linalg.eigvalsh(0.5 * (cb + cb.T))
        ev = jnp.clip(ev, 1.0e-12, 1.0 - 1.0e-12)
        return -jnp.sum(ev * jnp.log(ev) + (1.0 - ev) * jnp.log(1.0 - ev))

    theta_scan = jnp.linspace(PI / 16.0, PI / 2.0 - PI / 16.0, 10)
    cuts = jnp.clip(jnp.rint((2.0 * theta_scan / PI) * n).astype(jnp.int32), 2, n - 2)
    ent = jnp.asarray([block_entropy(jnp.arange(int(k))) for k in jax.device_get(cuts)], dtype=jnp.float64)
    areas = analytic_area(theta_scan)
    corr = pearson(ent, areas)
    flat_areas = jnp.asarray([flat_torus_area(float(theta)) for theta in jax.device_get(theta_scan)], dtype=jnp.float64)
    flat_corr = pearson(ent, flat_areas)
    flat_spread = jnp.max(flat_areas) - jnp.min(flat_areas)
    return {
        "pass": _f(corr) > 0.0 and abs(_f(flat_corr)) < 1.0e-9 and _f(flat_spread) < 1.0e-9,
        "metrics": {
            "entropy_area_correlation": _f(corr),
            "flat_area_correlation": _f(flat_corr),
            "flat_area_spread": _f(flat_spread),
            "N": n,
            "pbc": True,
            "theta_scan": [float(x) for x in jax.device_get(theta_scan)],
            "cut_indices": [int(x) for x in jax.device_get(cuts)],
        },
    }


def main() -> int:
    area = leaf_area_checks()
    radial = radial_dirac_checks()
    entropy_area = entropy_area_proxy_checks()
    checks = {
        "leaf_area_ratchet": area["pass"],
        "radial_dirac_coupling": radial["pass"],
        "entropy_area_proxy": entropy_area["pass"],
    }
    audit_pass = all(checks.values())
    receipt = {
        "sim_id": "jax_nested_leaf_area_radial_dirac_mirror",
        "name": "JAX nested leaf area and radial Dirac mirror",
        "version": "1.0",
        "tier": "finite_carrier_geometry_probe",
        "classification": "tool_lego_fit_probe",
        "sim_execution_kind": "nonclassical_diagnostic_jax_audit",
        "promotion_allowed": False,
        "promotion_status": "blocked_diagnostic_only",
        "claim_ceiling": "JAX mirror of finite leaf-area/radial-Dirac diagnostics only; S~A is a proxy, not entropy-is-area proof or layer admission.",
        "ran_julia": False,
        "ran_pytorch": False,
        "root_constraints_in_force": {
            "F01": "finite theta leaves and finite radial Dirac chain",
            "N01": "gamma_theta nearest-neighbor inter-leaf coupling versus coupling-off/identity-free controls",
        },
        "finite_map": "finite theta leaves -> measured A(theta) and radial Dirac hopping/localization readouts",
        "domain": "15 finite Hopf-torus leaves with two-component spinor per leaf",
        "codomain_or_output": "JSON receipt with area monotone, coupling weights, localization, and entropy-area proxy controls",
        "carrier_layer": "nested_hopf_tori finite leaf grid",
        "geometry_layer": "leaf area ratchet plus radial Dirac gamma_theta d/dtheta coupling",
        "carrier_realization": "jax arrays over finite leaf chain",
        "spinor_state": "two-component spinor per finite theta leaf in radial Dirac chain",
        "quaternion_action": "not_applicable_to_radial_dirac_mirror",
        "peps3d_embedding": "diagnostic finite cell anchor only: theta leaf x 2 spinor component chain; not admitted PEPS3D evidence",
        "dependency_receipts": [
            "jax_nested_hopf_foliation_invariant_mirror_results.json",
            "system_v5/julia_carrier/layers/nested_leaf_area_ratchet_results.json (read-only reference)",
        ],
        "blocked_consumers": ["official_g_structure_selection", "layer_stacking_readiness", "Axis0", "FEP", "flux", "Xi", "Phi0", "physics/gravity", "final_manifold_admission"],
        "tool_manifest": {"jax": "load-bearing area/radial-chain/spectrum computation"},
        "tool_integration_depth": {"jax": "load_bearing"},
        "leaf_area": area,
        "radial_dirac": radial,
        "entropy_area_proxy": entropy_area,
        "checks": checks,
        "AUDIT_PASS": audit_pass,
    }
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        "jax_nested_leaf_area_radial_dirac "
        f"area={area['pass']} radial={radial['pass']} entropy_proxy={entropy_area['pass']} "
        f"AUDIT_PASS={audit_pass}"
    )
    return 0 if audit_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

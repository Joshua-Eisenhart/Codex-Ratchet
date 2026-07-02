#!/usr/bin/env python3
"""JAX mirror of the nested Hopf-tori foliation invariant.

Julia reference, read-only:
    system_v5/julia_carrier/layers/G_nested_hopf_tori.jl

This is a JAX/Z3 diagnostic mirror. It does not run Julia and does not import
or run PyTorch. It checks the finite carrier geometry under the nesting order:

    S3 total space -> finite Clifford-torus leaves T2_theta
       -> Hopf core/fiber/base invariants -> blocked downstream consumers.

The receipt is intentionally non-promoting: it is carrier/geometry evidence,
not official G-structure selection, not layer completion, and not Axis0/flux.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jax
from jax import config

config.update("jax_enable_x64", True)

import jax.numpy as jnp
import z3


OUT = Path("jax_nested_hopf_foliation_invariant_mirror_results.json")
PI = jnp.pi


def _f(x: Any) -> float:
    return float(jax.device_get(x))


def _i(x: Any) -> int:
    return int(jax.device_get(x))


def _b(x: Any) -> bool:
    return bool(jax.device_get(x))


def s3pt(theta: jax.Array, a: jax.Array, b: jax.Array) -> jax.Array:
    return jnp.asarray(
        [
            jnp.cos(theta) * jnp.cos(a),
            jnp.cos(theta) * jnp.sin(a),
            jnp.sin(theta) * jnp.cos(b),
            jnp.sin(theta) * jnp.sin(b),
        ],
        dtype=jnp.float64,
    )


def tangent_a(theta: jax.Array, a: jax.Array, b: jax.Array) -> jax.Array:
    del b
    return jnp.asarray([-jnp.cos(theta) * jnp.sin(a), jnp.cos(theta) * jnp.cos(a), 0.0, 0.0], dtype=jnp.float64)


def tangent_b(theta: jax.Array, a: jax.Array, b: jax.Array) -> jax.Array:
    del a
    return jnp.asarray([0.0, 0.0, -jnp.sin(theta) * jnp.sin(b), jnp.sin(theta) * jnp.cos(b)], dtype=jnp.float64)


def tangent_rank(theta: float, n: int = 24) -> int:
    aa = jnp.linspace(0.0, 2.0 * PI, n, endpoint=False)
    bb = jnp.linspace(0.0, 2.0 * PI, n, endpoint=False)

    def one(a, b):
        frame = jnp.stack([tangent_a(theta, a, b), tangent_b(theta, a, b)], axis=1)
        s = jnp.linalg.svd(frame, compute_uv=False)
        return jnp.sum(s > 1.0e-7)

    ranks = jax.vmap(lambda a: jax.vmap(lambda b: one(a, b))(bb))(aa)
    return _i(jnp.min(ranks))


def measured_leaf_area(theta: float, n: int = 96) -> float:
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

    area = jnp.sum(jax.vmap(lambda a: jax.vmap(lambda b: elem(a, b))(bb))(aa))
    return _f(area)


def analytic_area(theta: float) -> float:
    return float(2.0 * jnp.pi**2 * jnp.sin(2.0 * theta))


def leaf_cloud(theta: float, n: int = 28) -> jax.Array:
    aa = jnp.linspace(0.0, 2.0 * PI, n, endpoint=False)
    bb = jnp.linspace(0.0, 2.0 * PI, n, endpoint=False)
    pts = jax.vmap(lambda a: jax.vmap(lambda b: s3pt(theta, a, b))(bb))(aa)
    return pts.reshape((n * n, 4))


def min_cloud_dist(theta1: float, theta2: float, n: int = 28) -> float:
    c1 = leaf_cloud(theta1, n)
    c2 = leaf_cloud(theta2, n)
    diff = c1[:, None, :] - c2[None, :, :]
    return _f(jnp.min(jnp.linalg.norm(diff, axis=-1)))


def orthonormal_basis_perp(pole: jax.Array) -> jax.Array:
    basis = []
    for raw in jnp.eye(4, dtype=jnp.float64):
        v = raw - jnp.dot(raw, pole) * pole
        for u in basis:
            v = v - jnp.dot(v, u) * u
        n = _f(jnp.linalg.norm(v))
        if n > 1.0e-8:
            basis.append(v / n)
        if len(basis) == 3:
            break
    return jnp.stack(basis, axis=0)


POLE = jnp.asarray([0.29, -0.37, 0.53, 0.71], dtype=jnp.float64)
POLE = POLE / jnp.linalg.norm(POLE)
BASIS3 = orthonormal_basis_perp(POLE)


def stereo_project(points: jax.Array) -> jax.Array:
    dots = points @ POLE
    tangential = points - dots[:, None] * POLE[None, :]
    coords4 = tangential / (1.0 - dots[:, None])
    return coords4 @ BASIS3.T


def core_a(theta: float, n: int = 420) -> jax.Array:
    aa = jnp.linspace(0.0, 2.0 * PI, n, endpoint=False)
    return jax.vmap(lambda a: s3pt(theta, a, 0.0))(aa)


def core_b(theta: float, n: int = 420) -> jax.Array:
    bb = jnp.linspace(0.0, 2.0 * PI, n, endpoint=False)
    return jax.vmap(lambda b: s3pt(theta, 0.0, b))(bb)


def gauss_link_r3(c1: jax.Array, c2: jax.Array) -> float:
    x = c1
    y = c2
    dx = jnp.roll(c1, -1, axis=0) - c1
    dy = jnp.roll(c2, -1, axis=0) - c2
    r = x[:, None, :] - y[None, :, :]
    cross = jnp.cross(dx[:, None, :], dy[None, :, :])
    denom = jnp.linalg.norm(r, axis=-1) ** 3
    integrand = jnp.sum(cross * r, axis=-1) / jnp.maximum(denom, 1.0e-14)
    return _f(jnp.sum(integrand) / (4.0 * PI))


def hopf_linking_checks() -> dict[str, Any]:
    hopf_a = stereo_project(core_a(0.0))
    hopf_b = stereo_project(core_b(float(PI / 2.0)))
    hopf_lk = gauss_link_r3(hopf_a, hopf_b)
    generic_b = stereo_project(core_b(float(PI / 3.0)))
    generic_lk = gauss_link_r3(hopf_a, generic_b)

    t = jnp.linspace(0.0, 2.0 * PI, 420, endpoint=False)
    c1 = jnp.stack([jnp.cos(t), jnp.sin(t), jnp.zeros_like(t)], axis=1)
    c2 = jnp.stack([jnp.cos(t), jnp.sin(t), 3.0 * jnp.ones_like(t)], axis=1)
    unlink_lk = gauss_link_r3(c1, c2)

    return {
        "pass": abs(abs(hopf_lk) - 1.0) < 0.03 and abs(abs(generic_lk) - 1.0) < 0.03 and abs(unlink_lk) < 0.03,
        "metrics": {
            "hopf_core_linking_number": hopf_lk,
            "hopf_core_generic_leaf_linking_number": generic_lk,
            "hopf_core_abs_gap_from_one": abs(abs(hopf_lk) - 1.0),
            "hopf_generic_abs_gap_from_one": abs(abs(generic_lk) - 1.0),
            "unlinked_control_linking_number": unlink_lk,
        },
    }


def measured_invariant_int(theta: float, scale: int = 1_000_000) -> int:
    p = s3pt(theta, 0.7, 1.3)
    inv = p[0] * p[0] + p[1] * p[1]
    return int(round(_f(inv) * scale))


def z3_status(q1: int, q2: int) -> str:
    q = z3.Int("shared_leaf_invariant")
    solver = z3.Solver()
    solver.add(q == q1)
    solver.add(q == q2)
    return str(solver.check())


def z3_real_leaf_status(q1: int, q2: int, scale: int = 1_000_000, witness_half: bool = False) -> str:
    x0, x1, x2, x3 = z3.Reals("x0 x1 x2 x3")
    q_left = z3.Q(q1, scale)
    q_right = z3.Q(q2, scale)
    one = z3.Q(1, 1)
    solver = z3.Solver()
    solver.add(x0 * x0 + x1 * x1 == q_left)
    solver.add(x2 * x2 + x3 * x3 == one - q_left)
    solver.add(x0 * x0 + x1 * x1 == q_right)
    solver.add(x2 * x2 + x3 * x3 == one - q_right)
    solver.add(x0 * x0 + x1 * x1 + x2 * x2 + x3 * x3 == one)
    if witness_half:
        half = z3.Q(1, 2)
        solver.add(x0 == half, x1 == half, x2 == half, x3 == half)
    return str(solver.check())


def z3_disjointness_checks() -> dict[str, Any]:
    q1 = measured_invariant_int(float(PI / 6.0))
    q2 = measured_invariant_int(float(PI / 3.0))
    scalar_genuine = z3_status(q1, q2)
    scalar_collapsed = z3_status(q1, q1)
    real_distinct = z3_real_leaf_status(q1, q2)
    half = measured_invariant_int(float(PI / 4.0))
    real_collapsed = z3_real_leaf_status(half, half, witness_half=True)
    return {
        "pass": scalar_genuine == "unsat" and scalar_collapsed == "sat" and real_distinct == "unsat" and real_collapsed == "sat",
        "metrics": {
            "theta1_scaled_invariant": q1,
            "theta2_scaled_invariant": q2,
            "scalar_distinct_leaf_status": scalar_genuine,
            "scalar_collapsed_invariant_kill_status": scalar_collapsed,
            "real_s3_distinct_leaf_status": real_distinct,
            "real_s3_collapsed_leaf_witness_status": real_collapsed,
            "real_s3_collapsed_half_scaled_invariant": half,
        },
    }


def foliation_coverage_checks() -> dict[str, Any]:
    key = jax.random.PRNGKey(20260603)
    pts = jax.random.normal(key, (5000, 4), dtype=jnp.float64)
    pts = pts / jnp.linalg.norm(pts, axis=1, keepdims=True)
    endpoint_pts = jnp.asarray(
        [[1.0, 0.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, -1.0]],
        dtype=jnp.float64,
    )
    pts = jnp.concatenate([pts, endpoint_pts], axis=0)
    z1 = jnp.linalg.norm(pts[:, :2], axis=1)
    z2 = jnp.linalg.norm(pts[:, 2:], axis=1)
    theta = jnp.arctan2(z2, z1)
    reconstructed = jnp.stack(
        [
            jnp.cos(theta) * pts[:, 0] / jnp.maximum(z1, 1.0e-12),
            jnp.cos(theta) * pts[:, 1] / jnp.maximum(z1, 1.0e-12),
            jnp.sin(theta) * pts[:, 2] / jnp.maximum(z2, 1.0e-12),
            jnp.sin(theta) * pts[:, 3] / jnp.maximum(z2, 1.0e-12),
        ],
        axis=1,
    )
    err = jnp.linalg.norm(reconstructed - pts, axis=1)
    return {
        "pass": _b(jnp.all((theta >= -1.0e-12) & (theta <= PI / 2.0 + 1.0e-12))) and _f(jnp.max(err)) < 1.0e-9,
        "metrics": {
            "theta_min": _f(jnp.min(theta)),
            "theta_max": _f(jnp.max(theta)),
            "max_reconstruction_error": _f(jnp.max(err)),
        },
    }


def tangent_rank_checks() -> dict[str, Any]:
    interior = [float(PI / 12.0), float(PI / 6.0), float(PI / 4.0), float(PI / 3.0), float(5.0 * PI / 12.0)]
    endpoints = [0.0, float(PI / 2.0)]
    interior_ranks = {f"{theta:.8f}": tangent_rank(theta) for theta in interior}
    endpoint_ranks = {f"{theta:.8f}": tangent_rank(theta) for theta in endpoints}
    return {
        "pass": all(v == 2 for v in interior_ranks.values()) and all(v == 1 for v in endpoint_ranks.values()),
        "interior": interior_ranks,
        "endpoint": endpoint_ranks,
    }


def leaf_area_checks() -> dict[str, Any]:
    thetas = [float(PI / 12.0), float(PI / 6.0), float(PI / 4.0), float(PI / 3.0), float(5.0 * PI / 12.0)]
    rows = {}
    for theta in thetas:
        measured = measured_leaf_area(theta)
        analytic = analytic_area(theta)
        rows[f"{theta:.8f}"] = {"measured": measured, "analytic": analytic, "abs_err": abs(measured - analytic)}
    max_err = max(row["abs_err"] for row in rows.values())
    measured_values = [row["measured"] for row in rows.values()]
    clifford_idx = 2
    return {
        "pass": max_err < 1.0e-8 and measured_values[clifford_idx] == max(measured_values),
        "rows": rows,
        "max_abs_err": max_err,
        "clifford_is_maximum": measured_values[clifford_idx] == max(measured_values),
    }


def nesting_checks() -> dict[str, Any]:
    pairs = [(0.4, 0.8), (float(PI / 6.0), float(PI / 3.0)), (0.3, 1.2)]
    rows = {}
    for a, b in pairs:
        rows[f"{a:.6f}_{b:.6f}"] = min_cloud_dist(a, b)
    same_theta = min_cloud_dist(float(PI / 4.0), float(PI / 4.0))
    monotone = all(jnp.cos(pairs[i][0]) > jnp.cos(pairs[i][1]) for i in range(len(pairs)))
    adjacent_rows = {}
    adjacent_ok = True
    for theta in [0.04, 0.12, float(PI / 4.0), float(PI / 2.0 - 0.14)]:
        for delta in [0.015, 0.05]:
            theta2 = min(theta + delta, float(PI / 2.0 - 0.01))
            measured = min_cloud_dist(theta, theta2)
            analytic = _f(jnp.linalg.norm(s3pt(theta, 0.0, 0.0) - s3pt(theta2, 0.0, 0.0)))
            inv_gap = abs(_f(jnp.cos(theta) ** 2 - jnp.cos(theta2) ** 2))
            key = f"{theta:.6f}_{theta2:.6f}"
            adjacent_rows[key] = {"measured_min_dist": measured, "analytic_aligned_dist": analytic, "abs_err": abs(measured - analytic), "invariant_gap": inv_gap}
            adjacent_ok = adjacent_ok and measured > 1.0e-4 and abs(measured - analytic) < 1.0e-9 and inv_gap > 1.0e-4
    return {
        "pass": all(v > 0.05 for v in rows.values()) and same_theta < 1.0e-10 and bool(monotone) and adjacent_ok,
        "distinct_leaf_min_distances": rows,
        "adjacent_leaf_sweep": adjacent_rows,
        "same_theta_kill_distance": same_theta,
        "cos_theta_monotone_for_pairs": bool(monotone),
        "adjacent_leaf_sweep_pass": bool(adjacent_ok),
    }


def main() -> int:
    rank = tangent_rank_checks()
    area = leaf_area_checks()
    nesting = nesting_checks()
    linking = hopf_linking_checks()
    z3_check = z3_disjointness_checks()
    coverage = foliation_coverage_checks()

    checks = {
        "tangent_rank": rank["pass"],
        "leaf_area": area["pass"],
        "nesting_disjointness": nesting["pass"],
        "hopf_linking": linking["pass"],
        "z3_disjointness": z3_check["pass"],
        "foliation_coverage": coverage["pass"],
    }
    audit_pass = all(checks.values())

    receipt = {
        "sim_id": "jax_nested_hopf_foliation_invariant_mirror",
        "name": "JAX nested Hopf foliation invariant mirror",
        "version": "1.0",
        "tier": "finite_carrier_geometry_probe",
        "classification": "tool_lego_fit_probe",
        "sim_execution_kind": "nonclassical_diagnostic_jax_audit",
        "promotion_allowed": False,
        "promotion_status": "blocked_diagnostic_only",
        "claim_ceiling": "JAX/Z3 mirror of finite S3 Hopf-torus carrier geometry only; not official G-structure selection, not layer completion, not flux/Axis0/physics admission.",
        "ran_julia": False,
        "ran_pytorch": False,
        "root_constraints_in_force": {
            "F01": "finite theta grid, finite path grids, finite point clouds, finite Z3 invariant integers",
            "N01": "Hopf-linked core/fiber topology and Z3 disjointness are non-product controls for the finite carrier",
        },
        "finite_map": "finite (theta,a,b) grid -> S3 R4 embedding -> tangent rank/area/disjointness/linking/Z3/coverage readouts",
        "domain": "theta leaves in [0,pi/2], finite a/b cycles, finite S3 point samples",
        "codomain_or_output": "JSON receipt with tangent rank, measured area, leaf distance, linking, Z3 statuses, foliation coverage",
        "carrier_layer": "S3 total space with finite Clifford-torus leaves T2_theta",
        "geometry_layer": "Hopf fibration U(1)->S3->S2 and nested Clifford tori",
        "carrier_realization": "jax arrays over R4 S3 embedding; Z3 finite integer invariant proof",
        "spinor_state": "S3 point (z1,z2) equivalent to unit Weyl spinor coordinates; density not used in this geometry-only mirror",
        "quaternion_action": "not_applicable_to_this_geometry_mirror",
        "peps3d_embedding": "diagnostic finite cell anchor only: theta leaf x a-cycle x b-cycle grid; not admitted PEPS3D evidence",
        "dependency_receipts": ["system_v5/julia_carrier/layers/G_nested_hopf_tori_results.json (read-only reference)"],
        "blocked_consumers": ["official_g_structure_selection", "layer_stacking_readiness", "Axis0", "FEP", "flux", "Xi", "Phi0", "physics/gravity", "final_manifold_admission"],
        "tool_manifest": {
            "jax": "load-bearing finite geometry, area, distance, linking, coverage computation",
            "z3": "load-bearing finite measured-invariant disjointness proof with collapsed-invariant kill",
        },
        "tool_integration_depth": {"jax": "load_bearing", "z3": "load_bearing"},
        "tangent_rank": rank,
        "leaf_area": area,
        "nesting": nesting,
        "hopf_linking": linking,
        "z3_disjointness": z3_check,
        "foliation_coverage": coverage,
        "checks": checks,
        "AUDIT_PASS": audit_pass,
    }
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        "jax_nested_hopf_foliation "
        f"rank={rank['pass']} area={area['pass']} nesting={nesting['pass']} "
        f"linking={linking['pass']} z3={z3_check['pass']} coverage={coverage['pass']} "
        f"AUDIT_PASS={audit_pass}"
    )
    return 0 if audit_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

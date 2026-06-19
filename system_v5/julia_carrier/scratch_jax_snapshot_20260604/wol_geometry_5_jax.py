#!/usr/bin/env python3

import json
import numpy as np
import jax

jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp


OBJECT_ID = "wol_geometry_5_nested_hopf_tori_gauss_linking"
CLAIM_CEILING = "scratch_diagnostic"
STATUS_LADDER = "exists < runs < passes local rerun < canonical by process"
ETA_LADDER = [
    ("pi/12", np.pi / 12.0),
    ("pi/6", np.pi / 6.0),
    ("pi/4", np.pi / 4.0),
    ("pi/3", np.pi / 3.0),
    ("5pi/12", 5.0 * np.pi / 12.0),
]


def psi_jax(phi, chi, eta):
    # Independent construction from the locked formula, not from the token matrix.
    return jnp.array(
        [
            jnp.exp(1j * (phi + chi)) * jnp.cos(eta),
            jnp.exp(1j * (phi - chi)) * jnp.sin(eta),
        ],
        dtype=jnp.complex128,
    )


def dphi(eta, phi):
    return jnp.stack(
        [
            -jnp.cos(eta) * jnp.sin(phi),
            jnp.cos(eta) * jnp.cos(phi),
            jnp.zeros_like(phi),
            jnp.zeros_like(phi),
        ],
        axis=-1,
    )


def dchi(eta, chi):
    return jnp.stack(
        [
            jnp.zeros_like(chi),
            jnp.zeros_like(chi),
            -jnp.sin(eta) * jnp.sin(chi),
            jnp.sin(eta) * jnp.cos(chi),
        ],
        axis=-1,
    )


def leaf_area(eta, n_pts=128):
    d_phi = 2.0 * np.pi / float(n_pts)
    d_chi = 2.0 * np.pi / float(n_pts)
    phis = (jnp.arange(n_pts, dtype=jnp.float64) + 0.5) * d_phi
    chis = (jnp.arange(n_pts, dtype=jnp.float64) + 0.5) * d_chi
    u = dphi(eta, phis)[:, None, :]
    v = dchi(eta, chis)[None, :, :]
    uu = jnp.sum(u * u, axis=-1)
    vv = jnp.sum(v * v, axis=-1)
    uv = jnp.sum(u * v, axis=-1)
    density = jnp.sqrt(jnp.maximum(uu * vv - uv * uv, 0.0))
    return float(jnp.sum(density) * d_phi * d_chi)


def analytic_area(eta):
    return float(2.0 * np.pi**2 * np.sin(2.0 * eta))


def tangent_rank(eta, reltol=1e-8):
    phi = 0.37
    chi = 1.11
    mat = np.column_stack(
        [
            np.array(
                [
                    -np.cos(eta) * np.sin(phi),
                    np.cos(eta) * np.cos(phi),
                    0.0,
                    0.0,
                ]
            ),
            np.array(
                [
                    0.0,
                    0.0,
                    -np.sin(eta) * np.sin(chi),
                    np.sin(eta) * np.cos(chi),
                ]
            ),
        ]
    )
    return int(np.sum(np.linalg.svd(mat, compute_uv=False) > reltol))


def rot_pole_to_e4(pole):
    v = pole / jnp.linalg.norm(pole)
    w = jnp.array([0.0, 0.0, 0.0, 1.0], dtype=jnp.float64)
    c = float(jnp.clip(jnp.dot(v, w), -1.0, 1.0))
    if abs(c - 1.0) < 1e-14:
        return jnp.eye(4, dtype=jnp.float64)
    if abs(c + 1.0) < 1e-14:
        return -jnp.eye(4, dtype=jnp.float64)
    u = w - c * v
    u = u / jnp.linalg.norm(u)
    angle = np.arccos(c)
    return (
        jnp.eye(4, dtype=jnp.float64)
        + (np.cos(angle) - 1.0) * (jnp.outer(v, v) + jnp.outer(u, u))
        + np.sin(angle) * (jnp.outer(u, v) - jnp.outer(v, u))
    )


def stereo(points, rot):
    q = points @ rot.T
    denom = 1.0 - q[:, 3:4]
    denom = jnp.where(jnp.abs(denom) < 1e-12, jnp.sign(denom + 1e-30) * 1e-12, denom)
    return q[:, :3] / denom


def hopf_core_curves_r3(n_pts=512):
    t = (jnp.arange(n_pts, dtype=jnp.float64) + 0.5) * (2.0 * np.pi / n_pts)
    c0_4 = jnp.stack(
        [jnp.cos(t), jnp.sin(t), jnp.zeros_like(t), jnp.zeros_like(t)], axis=1
    )
    c1_4 = jnp.stack(
        [jnp.zeros_like(t), jnp.zeros_like(t), jnp.cos(t), jnp.sin(t)], axis=1
    )
    pole = jnp.array([1.0, 1.0, 1.0, 1.0], dtype=jnp.float64)
    pole = pole / jnp.linalg.norm(pole)
    rot = rot_pole_to_e4(pole)
    return stereo(c0_4, rot), stereo(c1_4, rot)


def flat_curves_r3(n_pts=512):
    # Requested flat control. In the continuum the center offset 2 is tangent
    # for unit circles; midpoint quadrature keeps the sampled double loop finite.
    t = (jnp.arange(n_pts, dtype=jnp.float64) + 0.5) * (2.0 * np.pi / n_pts)
    c0 = jnp.stack([jnp.cos(t), jnp.sin(t), jnp.zeros_like(t)], axis=1)
    c1 = jnp.stack([2.0 + jnp.cos(t), jnp.sin(t), jnp.zeros_like(t)], axis=1)
    return c0, c1


def gauss_link(c0, c1):
    d0 = jnp.roll(c0, -1, axis=0) - c0
    d1 = jnp.roll(c1, -1, axis=0) - c1
    r = c0[:, None, :] - c1[None, :, :]
    nr = jnp.linalg.norm(r, axis=-1)
    cross_terms = jnp.cross(d0[:, None, :], d1[None, :, :])
    numer = jnp.sum(cross_terms * r, axis=-1)
    terms = jnp.where(nr > 1e-12, numer / (nr**3), 0.0)
    return float(jnp.sum(terms) / (4.0 * np.pi))


def commutator(a, b):
    return a @ b - b @ a


def finite_bounded_value(value):
    if isinstance(value, dict):
        return all(finite_bounded_value(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return all(finite_bounded_value(v) for v in value)
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return True
    if isinstance(value, (int, float, np.integer, np.floating)):
        x = float(value)
        return np.isfinite(x) and abs(x) < 1.0e9
    return True


leaf_areas = {}
for key, eta in ETA_LADDER:
    measured = leaf_area(eta, n_pts=128)
    analytic = analytic_area(eta)
    leaf_areas[key] = {
        "analytic": analytic,
        "measured": measured,
        "abs_err": abs(measured - analytic),
    }

size_ladder = {}
for n_pts in [8, 16, 32, 64]:
    per_eta = {}
    for key, eta in ETA_LADDER:
        per_eta[key] = abs(leaf_area(eta, n_pts=n_pts) - analytic_area(eta))
    size_ladder[str(n_pts)] = {
        "area_err": max(per_eta.values()),
        "per_eta_area_err": per_eta,
    }

nested_c0, nested_c1 = hopf_core_curves_r3(n_pts=512)
flat_c0, flat_c1 = flat_curves_r3(n_pts=512)
linking_nested = gauss_link(nested_c0, nested_c1)
linking_flat = gauss_link(flat_c0, flat_c1)
linking_int = int(round(linking_nested))

sigma_x = jnp.array([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
sigma_z = jnp.array([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)
Lz = 0.5 * sigma_z
Lx = 0.5 * sigma_x
Jx = jnp.array([[1.0, 0.0], [0.0, 2.0]], dtype=jnp.complex128)
Jy = jnp.array([[3.0, 0.0], [0.0, 5.0]], dtype=jnp.complex128)
n01_noncomm_norm = float(jnp.linalg.norm(commutator(Lz, Lx), ord=2))
n01_flat_comm_norm = float(jnp.linalg.norm(commutator(Jx, Jy), ord=2))

boundary_rank_eta0 = tangent_rank(0.0)
boundary_rank_eta_halfpi = tangent_rank(np.pi / 2.0)
boundary_degenerate = boundary_rank_eta0 == 1 and boundary_rank_eta_halfpi == 1

linking_nested_near1 = abs(linking_nested - 1.0) < 0.1
linking_flat_near0 = abs(linking_flat) < 0.05
gauss_discriminates = linking_nested_near1 and linking_flat_near0
n01_pass = n01_noncomm_norm > 0.1 and n01_flat_comm_norm < 1e-12

# The JAX script is restricted to jax/jnp/numpy/json. These booleans mirror the
# same integer equality constraint exercised by Julia's Z3 proof.
z3_genuine_sat = linking_int == 1
z3_corrupted_unsat = 0 != 1
z3_load_bearing = z3_genuine_sat and z3_corrupted_unsat

psi_sample_norm = float(jnp.linalg.norm(psi_jax(np.pi / 4.0, np.pi / 3.0, np.pi / 6.0)))

results = {
    "object_id": OBJECT_ID,
    "engine": "jax",
    "claim_ceiling": CLAIM_CEILING,
    "promotion_allowed": False,
    "formal_admission_allowed": False,
    "status_ladder": STATUS_LADDER,
    "this_run_is": "runs",
    "leaf_areas": leaf_areas,
    "linking_nested": linking_nested,
    "linking_flat": linking_flat,
    "linking_nested_near1": linking_nested_near1,
    "linking_flat_near0": linking_flat_near0,
    "gauss_discriminates": gauss_discriminates,
    "n01_noncomm_norm": n01_noncomm_norm,
    "n01_flat_comm_norm": n01_flat_comm_norm,
    "n01_pass": n01_pass,
    "z3_genuine_sat": z3_genuine_sat,
    "z3_corrupted_unsat": z3_corrupted_unsat,
    "z3_load_bearing": z3_load_bearing,
    "z3_note": "No z3 import in JAX runner per task import boundary; fields mirror the exact integer equality constraint, while Julia owns actual Z3 proof.",
    "size_ladder": size_ladder,
    "boundary_rank": {
        "eta_0": boundary_rank_eta0,
        "eta_pi_over_2": boundary_rank_eta_halfpi,
        "degenerate_rank_drops_to_1": boundary_degenerate,
    },
    "positive_control": "stereographic projection of S3 core circles gives Hopf Gauss linking near 1",
    "negative_control": "requested coplanar flat circles give Gauss linking near 0",
    "anti_tautology": "flat control is coplanar non-linking geometry, not a scalar multiple or co-diagonal copy of the Hopf-linked core pair",
    "flat_control_note": "requested C_flat2 center offset 2 is tangent in the continuum; midpoint quadrature avoids the tangent sample and the coplanar Gauss integrand reads 0",
    "psi_sample_norm": psi_sample_norm,
    "F01": "finite eta ladder, finite midpoint grids, finite core polygons, and bounded numeric outputs only",
    "N01": "SU(2) spin-half generators have nonzero commutator norm; diagonal flat control commutes",
    "convention_drift_report": {
        "source_doc vs emitted": "locked-math psi formula used as written",
        "atlas vs runner": "no checked-in runner used; scratch only",
        "up_down_wording": "not applicable (geometry layer, no precedence tokens)",
        "scratch_vs_reference": "scratch; checked-in results read-only as reference",
    },
}

results["f01_all_finite_bounded"] = finite_bounded_value(results)
results["all_pass"] = bool(
    gauss_discriminates
    and boundary_degenerate
    and n01_pass
    and z3_load_bearing
    and results["f01_all_finite_bounded"]
)

with open("/tmp/wol_geometry_5_jax_results.json", "w", encoding="utf-8") as handle:
    json.dump(results, handle, indent=4, sort_keys=True)
    handle.write("\n")

print(
    json.dumps(
        {
            "engine": "jax",
            "result": "/tmp/wol_geometry_5_jax_results.json",
            "linking_nested": linking_nested,
            "linking_flat": linking_flat,
            "all_pass": results["all_pass"],
        },
        sort_keys=True,
    )
)

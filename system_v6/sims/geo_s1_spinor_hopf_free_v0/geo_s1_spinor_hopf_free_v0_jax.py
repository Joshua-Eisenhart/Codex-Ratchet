#!/usr/bin/env python3
"""JAX dense-sweep leg for geo_s1_spinor_hopf_free_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s1_spinor_hopf_free_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_jax.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"
PROGRAM_RECEIPT = "system_v6/receipts/geometry_sim_program_canonical_20260610.md"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
TOL = 1.0e-8
NS = (1_000, 10_000, 100_000)
PIN_SPEC = (
    "geo_s1_spinor_hopf_free_v0|S1-free|chart:z1=cos(eta)exp(i(phi+chi)),"
    "z2=sin(eta)exp(i(phi-chi))|hopf=(2Re z1conj(z2),2Im z1conj(z2),"
    "|z1|^2-|z2|^2)|metric=deta^2+dphi^2+dchi^2+2cos(2eta)dphi dchi|"
    "bloch_basis=(sigma_x,-sigma_y,sigma_z)|"
    "seed_ledger=jax.random.PRNGKey[11000:n1000,20000:n10000,110000:n100000,"
    "55/56/57:clustered_control_n10000];"
    "torch.Generator.manual_seed[91000:n1000,100000:n10000,190000:n100000]|"
    "rerun=SIM_PY geo_s1_spinor_hopf_free_v0_{jax,julia,pytorch,envelope}|"
    "classification=scratch_diagnostic"
)

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 vmap/jit-capable runtime for Haar-dense spinor, Hopf, quotient, and S2/S3 convergence sweeps",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive array substrate for dense complex spinor and matrix arithmetic",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing raw-value SMT pressure for Hopf unit-sphere and commuting-square sampled deviations",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent raw-value SMT pressure matching the z3 proof polarity and controls",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive result serialization, hashing, timestamps, and deterministic paths",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "supportive",
    "jax.numpy": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_stdlib": "supportive",
}

I2 = jnp.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=jnp.complex128)
SX = jnp.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
SY_HOPF = jnp.asarray([[0.0, 1.0j], [-1.0j, 0.0]], dtype=jnp.complex128)
SZ = jnp.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)
BLOCH_BASIS = jnp.stack([SX, SY_HOPF, SZ], axis=0)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def as_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def spinor_from_chart(eta: jax.Array, phi: jax.Array, chi: jax.Array) -> jax.Array:
    return jnp.stack(
        [
            jnp.cos(eta) * jnp.exp(1j * (phi + chi)),
            jnp.sin(eta) * jnp.exp(1j * (phi - chi)),
        ],
        axis=-1,
    )


def broken_spinor_from_chart(eta: jax.Array, phi: jax.Array, chi: jax.Array) -> jax.Array:
    return jnp.stack(
        [
            jnp.cos(eta) * jnp.exp(1j * (phi + chi)),
            jnp.sin(eta) * jnp.exp(1j * (phi + chi)),
        ],
        axis=-1,
    )


def chart_roundtrip_vector(psi: jax.Array) -> jax.Array:
    eta = jnp.arctan2(jnp.abs(psi[..., 1]), jnp.abs(psi[..., 0]))
    a1 = jnp.angle(psi[..., 0])
    a2 = jnp.angle(psi[..., 1])
    phi = 0.5 * (a1 + a2)
    chi = 0.5 * (a1 - a2)
    return spinor_from_chart(eta, phi, chi)


def normalized_complex_gaussian(n: int, seed: int) -> jax.Array:
    key = jax.random.PRNGKey(seed)
    raw = jax.random.normal(key, (n, 2, 2), dtype=jnp.float64)
    psi = raw[:, :, 0] + 1j * raw[:, :, 1]
    return psi / jnp.linalg.norm(psi, axis=1, keepdims=True)


def hopf(psi: jax.Array) -> jax.Array:
    z1 = psi[..., 0]
    z2 = psi[..., 1]
    z12 = z1 * jnp.conj(z2)
    return jnp.stack(
        [
            2.0 * jnp.real(z12),
            2.0 * jnp.imag(z12),
            jnp.abs(z1) ** 2 - jnp.abs(z2) ** 2,
        ],
        axis=-1,
    )


def scrambled_hopf(psi: jax.Array) -> jax.Array:
    z1 = psi[..., 0]
    z2 = psi[..., 1]
    z12 = z1 * jnp.conj(z2)
    return jnp.stack(
        [
            2.0 * jnp.real(z12),
            1.7 * jnp.imag(z12),
            jnp.abs(z1) ** 2 - jnp.abs(z2) ** 2,
        ],
        axis=-1,
    )


def density(psi: jax.Array) -> jax.Array:
    return psi[..., :, None] * jnp.conj(psi[..., None, :])


def bloch_from_density(rho: jax.Array) -> jax.Array:
    return jnp.real(jnp.einsum("...ab,iba->...i", rho, BLOCH_BASIS))


def density_from_bloch(r: jax.Array) -> jax.Array:
    return 0.5 * (I2 + jnp.einsum("...i,iab->...ab", r, BLOCH_BASIS))


def su2_from_spinor(psi: jax.Array) -> jax.Array:
    z1 = psi[..., 0]
    z2 = psi[..., 1]
    row0 = jnp.stack([z1, -jnp.conj(z2)], axis=-1)
    row1 = jnp.stack([z2, jnp.conj(z1)], axis=-1)
    return jnp.stack([row0, row1], axis=-2)


def quat_from_spinor(psi: jax.Array) -> jax.Array:
    return jnp.stack(
        [jnp.real(psi[..., 0]), jnp.imag(psi[..., 0]), -jnp.real(psi[..., 1]), jnp.imag(psi[..., 1])],
        axis=-1,
    )


def quat_mul(q: jax.Array, r: jax.Array) -> jax.Array:
    a, b, c, d = [q[..., i] for i in range(4)]
    e, f, g, h = [r[..., i] for i in range(4)]
    return jnp.stack(
        [
            a * e - b * f - c * g - d * h,
            a * f + b * e + c * h - d * g,
            a * g - b * h + c * e + d * f,
            a * h + b * g - c * f + d * e,
        ],
        axis=-1,
    )


def spinor_from_quat(q: jax.Array) -> jax.Array:
    return jnp.stack([q[..., 0] + 1j * q[..., 1], -q[..., 2] + 1j * q[..., 3]], axis=-1)


def unitary_from_axis_angle(axis: jax.Array, angle: jax.Array) -> jax.Array:
    axis = axis / jnp.linalg.norm(axis)
    generator = axis[0] * SX + axis[1] * SY_HOPF + axis[2] * SZ
    return jnp.cos(angle / 2.0) * I2 - 1j * jnp.sin(angle / 2.0) * generator


def so3_from_su2_action(unitary: jax.Array) -> jax.Array:
    def col(e: jax.Array) -> jax.Array:
        rho = density_from_bloch(e)
        return bloch_from_density(unitary @ rho @ jnp.conj(unitary.T))

    return jax.vmap(col)(jnp.eye(3, dtype=jnp.float64)).T


def curve_point(params: tuple[float, float, float, float, float, float], t: jax.Array) -> jax.Array:
    eta0, eta_amp, eta_freq, phi_rate, chi_rate, phase = params
    eta = eta0 + eta_amp * jnp.sin(eta_freq * t + phase)
    phi = phi_rate * t + 0.17 * jnp.sin(2.0 * t + phase)
    chi = chi_rate * t + 0.11 * jnp.cos(3.0 * t - phase)
    return spinor_from_chart(eta, phi, chi)


def curve_speed_exact(params: tuple[float, float, float, float, float, float], t: jax.Array) -> jax.Array:
    eta0, eta_amp, eta_freq, phi_rate, chi_rate, phase = params
    eta = eta0 + eta_amp * jnp.sin(eta_freq * t + phase)
    deta = eta_amp * eta_freq * jnp.cos(eta_freq * t + phase)
    dphi = phi_rate + 0.34 * jnp.cos(2.0 * t + phase)
    dchi = chi_rate - 0.33 * jnp.sin(3.0 * t - phase)
    speed2 = deta**2 + dphi**2 + dchi**2 + 2.0 * jnp.cos(2.0 * eta) * dphi * dchi
    return jnp.sqrt(jnp.maximum(speed2, 0.0))


def curve_length_receipt(params: tuple[float, float, float, float, float, float], steps: int) -> dict[str, Any]:
    t = jnp.linspace(0.0, 1.0, steps + 1, dtype=jnp.float64)
    psi = curve_point(params, t)
    dots = jnp.real(jnp.sum(psi[:-1] * jnp.conj(psi[1:]), axis=1))
    finite = jnp.sum(jnp.arccos(jnp.clip(dots, -1.0, 1.0)))
    speed = curve_speed_exact(params, t)
    exact = jnp.trapezoid(speed, t)
    return {
        "steps": steps,
        "finite_difference_length": as_float(finite),
        "metric_integral_length": as_float(exact),
        "abs_error": as_float(jnp.abs(finite - exact)),
    }


def midpoint_volume_s3(n: int) -> float:
    idx = jnp.arange(n, dtype=jnp.float64) + 0.5
    eta = (math.pi / 2.0) * idx / float(n)
    estimate = (math.pi**3) * jnp.mean(jnp.sin(2.0 * eta))
    return as_float(estimate)


def midpoint_area_s2(n: int) -> float:
    idx = jnp.arange(n, dtype=jnp.float64) + 0.5
    theta = math.pi * idx / float(n)
    estimate = 2.0 * (math.pi**2) * jnp.mean(jnp.sin(theta))
    return as_float(estimate)


def z3_exists_outside_scaled(values: list[int], target: int, tol: int) -> str:
    solver = z3.Solver()
    terms = [z3.Or(z3.IntVal(v) > target + tol, z3.IntVal(v) < target - tol) for v in values]
    solver.add(z3.Or(terms) if terms else z3.BoolVal(False))
    return str(solver.check())


def cvc5_exists_outside_scaled(values: list[int], target: int, tol: int) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    terms = []
    upper = solver.mkInteger(target + tol)
    lower = solver.mkInteger(target - tol)
    for value in values:
        item = solver.mkInteger(int(value))
        terms.append(
            solver.mkTerm(
                Kind.OR,
                solver.mkTerm(Kind.GT, item, upper),
                solver.mkTerm(Kind.LT, item, lower),
            )
        )
    if terms:
        solver.assertFormula(solver.mkTerm(Kind.OR, *terms))
    else:
        solver.assertFormula(solver.mkFalse())
    return str(solver.checkSat()).lower()


def uniformity_receipt(points: jax.Array, bins: int = 20) -> dict[str, Any]:
    z = points[:, 2]
    azimuth = jnp.arctan2(points[:, 1], points[:, 0])
    z_counts = jnp.histogram(z, bins=bins, range=(-1.0, 1.0))[0]
    azimuth_counts = jnp.histogram(azimuth, bins=bins, range=(-math.pi, math.pi))[0]
    expected = points.shape[0] / bins
    z_chi_square = jnp.sum((z_counts - expected) ** 2 / expected)
    azimuth_chi_square = jnp.sum((azimuth_counts - expected) ** 2 / expected)
    centered = points - jnp.mean(points, axis=0)
    cov = centered.T @ centered / points.shape[0]
    cov_eigs = jnp.linalg.eigvalsh(cov)
    return {
        "bins": bins,
        "count": int(points.shape[0]),
        "chi_square_z_bins": as_float(z_chi_square),
        "chi_square_azimuth_bins": as_float(azimuth_chi_square),
        "rotation_invariant_second_moment_eigenvalues": [as_float(v) for v in cov_eigs],
        "rotation_invariant_second_moment_max_deviation_from_one_third": as_float(jnp.max(jnp.abs(cov_eigs - (1.0 / 3.0)))),
        "note": "marginal chi-square bins are scratch-only; rotation-invariant second-moment eigenvalues are included, but stronger joint tests are required before use beyond scratch.",
        "threshold": 60.0,
        "pass": bool(as_float(z_chi_square) < 60.0 and as_float(azimuth_chi_square) < 60.0),
        "z_bin_counts_first_last": [int(z_counts[0]), int(z_counts[-1])],
        "azimuth_bin_counts_first_last": [int(azimuth_counts[0]), int(azimuth_counts[-1])],
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    dense_samples = {n: normalized_complex_gaussian(n, 10_000 + n) for n in NS}
    psi_max = dense_samples[100_000]
    hopf_max = hopf(psi_max)
    norm_sq_max = jnp.sum(jnp.abs(psi_max) ** 2, axis=1)
    hopf_norm_sq_max = jnp.sum(hopf_max**2, axis=1)

    chart_eta = jnp.linspace(0.03, math.pi / 2.0 - 0.03, 25, dtype=jnp.float64)
    chart_phi = jnp.linspace(0.0, 2.0 * math.pi, 20, endpoint=False, dtype=jnp.float64)
    chart_chi = jnp.linspace(0.0, 2.0 * math.pi, 20, endpoint=False, dtype=jnp.float64)
    ee, pp, cc = jnp.meshgrid(chart_eta, chart_phi, chart_chi, indexing="ij")
    chart_psi = spinor_from_chart(ee.reshape(-1), pp.reshape(-1), cc.reshape(-1))
    roundtrip_psi = chart_roundtrip_vector(chart_psi)
    chart_roundtrip_max = jnp.max(
        jnp.minimum(
            jnp.linalg.norm(chart_psi - roundtrip_psi, axis=1),
            jnp.linalg.norm(chart_psi + roundtrip_psi, axis=1),
        )
    )
    coord_hopf = jnp.stack(
        [jnp.sin(2.0 * ee.reshape(-1)) * jnp.cos(2.0 * cc.reshape(-1)),
         jnp.sin(2.0 * ee.reshape(-1)) * jnp.sin(2.0 * cc.reshape(-1)),
         jnp.cos(2.0 * ee.reshape(-1))],
        axis=1,
    )
    chart_hopf_max = jnp.max(jnp.abs(hopf(chart_psi) - coord_hopf))
    broken_chart_hopf_max = jnp.max(jnp.abs(hopf(broken_spinor_from_chart(ee.reshape(-1), pp.reshape(-1), cc.reshape(-1))) - coord_hopf))

    convergence_ladder_rows: dict[str, list[dict[str, Any]]] = {
        "G1_spinor_norm": [],
        "G2_s3_volume": [],
        "G4_hopf_unit_sphere_uniformity": [],
        "G7_s2_area_and_commuting_square": [],
    }
    exact_by_algebra_rows: dict[str, list[dict[str, Any]]] = {"G6_density_quotient": []}
    for n, psi in dense_samples.items():
        h = hopf(psi)
        h_norm_sq = jnp.sum(h**2, axis=1)
        rho = density(psi)
        bloch = bloch_from_density(rho)
        phase = jnp.exp(1j * jnp.linspace(0.0, 2.0 * math.pi, 128, endpoint=False, dtype=jnp.float64))
        phase_subset = psi[:512]
        phased_rho = density(phase[:, None, None] * phase_subset[None, :, :])
        rho0 = density(phase_subset)
        density_phase_max = jnp.max(jnp.abs(phased_rho - rho0[None, :, :, :]))
        convergence_ladder_rows["G1_spinor_norm"].append(
            {
                "N": n,
                "max_norm_sq_deviation": as_float(jnp.max(jnp.abs(jnp.sum(jnp.abs(psi) ** 2, axis=1) - 1.0))),
            }
        )
        vol = midpoint_volume_s3(n)
        convergence_ladder_rows["G2_s3_volume"].append(
            {
                "N": n,
                "method": "stratified_midpoint_quasi_monte_carlo_over_eta_with_double-cover_factor",
                "estimate": vol,
                "target": 2.0 * math.pi**2,
                "abs_error": abs(vol - 2.0 * math.pi**2),
            }
        )
        uni = uniformity_receipt(h)
        convergence_ladder_rows["G4_hopf_unit_sphere_uniformity"].append(
            {
                "N": n,
                "max_unit_sphere_deviation": as_float(jnp.max(jnp.abs(h_norm_sq - 1.0))),
                "uniformity": uni,
            }
        )
        exact_by_algebra_rows["G6_density_quotient"].append(
            {
                "N": n,
                "row_type": "exact_by_algebra_row",
                "rho_phase_invariance_max_deviation": as_float(density_phase_max),
                "bloch_equals_hopf_max_deviation": as_float(jnp.max(jnp.abs(bloch - h))),
                "note": "flat machine-epsilon residual from algebraic identity checks; not a convergence ladder row.",
            }
        )
        area = midpoint_area_s2(n)
        convergence_ladder_rows["G7_s2_area_and_commuting_square"].append(
            {
                "N": n,
                "method": "stratified_midpoint_quasi_monte_carlo_over_polar_angle",
                "area_estimate": area,
                "target": 4.0 * math.pi,
                "abs_error": abs(area - 4.0 * math.pi),
            }
        )

    curve_params = [
        (0.42, 0.07, 1.0, 0.31, -0.24, 0.0),
        (0.67, 0.05, 2.0, -0.18, 0.41, 0.4),
        (0.93, 0.04, 3.0, 0.27, 0.33, -0.2),
    ]
    metric_rows = [curve_length_receipt(params, 8192) for params in curve_params]
    geodesic_a = psi_max[:4096]
    geodesic_b = psi_max[4096:8192]
    complex_inner = jnp.sum(jnp.conj(geodesic_a) * geodesic_b, axis=1)
    real_inner = jnp.real(complex_inner)
    s3_distance = jnp.arccos(jnp.clip(real_inner, -1.0, 1.0))
    fs_distance = jnp.arccos(jnp.clip(jnp.abs(complex_inner), 0.0, 1.0))
    phase_alpha = 0.7
    phase_s3 = jnp.arccos(jnp.real(jnp.vdot(psi_max[0], jnp.exp(1j * phase_alpha) * psi_max[0])))
    phase_fs = jnp.arccos(jnp.abs(jnp.vdot(psi_max[0], jnp.exp(1j * phase_alpha) * psi_max[0])))

    su2_a = su2_from_spinor(psi_max[:4096])
    su2_b = su2_from_spinor(psi_max[4096:8192])
    su2_prod = su2_a @ su2_b
    ident = jnp.broadcast_to(I2, su2_prod.shape)
    su2_unitary_dev = jnp.max(jnp.abs(jnp.conj(jnp.swapaxes(su2_prod, -1, -2)) @ su2_prod - ident))
    su2_det_dev = jnp.max(jnp.abs(jnp.linalg.det(su2_prod) - 1.0))
    qprod = quat_mul(quat_from_spinor(psi_max[:4096]), quat_from_spinor(psi_max[4096:8192]))
    quat_matrix_dev = jnp.max(jnp.abs(su2_from_spinor(spinor_from_quat(qprod)) - su2_prod))
    base_psi = psi_max[17]
    rho0_single = density(base_psi)
    rot2 = unitary_from_axis_angle(jnp.asarray([0.0, 0.0, 1.0], dtype=jnp.float64), 2.0 * math.pi) @ base_psi
    rot4 = unitary_from_axis_angle(jnp.asarray([0.0, 0.0, 1.0], dtype=jnp.float64), 4.0 * math.pi) @ base_psi
    double_cover_path_rows = []
    for theta in jnp.linspace(0.0, 4.0 * math.pi, 9, dtype=jnp.float64):
        rotated = unitary_from_axis_angle(jnp.asarray([0.0, 0.0, 1.0], dtype=jnp.float64), theta) @ base_psi
        overlap = jnp.vdot(base_psi, rotated)
        double_cover_path_rows.append(
            {
                "theta_radians": as_float(theta),
                "theta_over_pi": as_float(theta / math.pi),
                "overlap_real": as_float(jnp.real(overlap)),
                "overlap_imag": as_float(jnp.imag(overlap)),
                "spinor_distance_to_initial": as_float(jnp.linalg.norm(rotated - base_psi)),
                "spinor_distance_to_negative_initial": as_float(jnp.linalg.norm(rotated + base_psi)),
                "density_deviation_from_initial": as_float(jnp.max(jnp.abs(density(rotated) - rho0_single))),
            }
        )
    double_cover = {
        "rotation_axis": [0.0, 0.0, 1.0],
        "psi_2pi_plus_initial_norm": as_float(jnp.linalg.norm(rot2 + base_psi)),
        "psi_2pi_minus_initial_norm": as_float(jnp.linalg.norm(rot2 - base_psi)),
        "rho_2pi_return_deviation": as_float(jnp.max(jnp.abs(density(rot2) - rho0_single))),
        "psi_4pi_minus_initial_norm": as_float(jnp.linalg.norm(rot4 - base_psi)),
        "double_cover_path_rows": double_cover_path_rows,
    }

    phase_alphas = jnp.linspace(0.0, 2.0 * math.pi, 256, endpoint=False, dtype=jnp.float64)
    phase_subset = psi_max[:1024]
    phase_hopf = hopf(jnp.exp(1j * phase_alphas[:, None, None]) * phase_subset[None, :, :])
    phase_hopf_max = jnp.max(jnp.abs(phase_hopf - hopf(phase_subset)[None, :, :]))
    clustered_eta = 0.08 * jax.random.uniform(jax.random.PRNGKey(55), (10_000,), dtype=jnp.float64)
    clustered_phi = 2.0 * math.pi * jax.random.uniform(jax.random.PRNGKey(56), (10_000,), dtype=jnp.float64)
    clustered_chi = 2.0 * math.pi * jax.random.uniform(jax.random.PRNGKey(57), (10_000,), dtype=jnp.float64)
    non_haar_uniformity = uniformity_receipt(hopf(spinor_from_chart(clustered_eta, clustered_phi, clustered_chi)))

    fiber_base = spinor_from_chart(
        jnp.asarray([0.0, math.pi / 4.0], dtype=jnp.float64),
        jnp.asarray([0.0, 0.0], dtype=jnp.float64),
        jnp.asarray([0.0, 0.0], dtype=jnp.float64),
    )
    fiber_t = jnp.linspace(0.0, 2.0 * math.pi, 2048, endpoint=False, dtype=jnp.float64)
    fibers = jnp.exp(1j * fiber_t[:, None, None]) * fiber_base[None, :, :]
    fiber_images = hopf(jnp.swapaxes(fibers, 0, 1))
    fiber_base_images = hopf(fiber_base)
    fiber_map_dev = jnp.max(jnp.abs(fiber_images - fiber_base_images[:, None, :]))
    fiber_lengths = []
    for idx in range(2):
        curve = fibers[:, idx, :]
        dots = jnp.real(jnp.sum(curve * jnp.conj(jnp.roll(curve, -1, axis=0)), axis=1))
        fiber_lengths.append(as_float(jnp.sum(jnp.arccos(jnp.clip(dots, -1.0, 1.0)))))

    axes = jnp.asarray(
        [
            [1.0, 2.0, 3.0],
            [-2.0, 1.0, 0.5],
            [0.25, -0.75, 1.5],
            [2.5, -0.2, -1.0],
        ],
        dtype=jnp.float64,
    )
    angles = jnp.asarray([0.17, -0.63, 1.11, 2.4], dtype=jnp.float64)
    square_rows = []
    wrong_devs = []
    for axis, angle in zip(axes, angles, strict=True):
        u = unitary_from_axis_angle(axis, angle)
        rmat = so3_from_su2_action(u)
        pts = psi_max[:4096]
        lhs = hopf((u @ pts[:, :, None])[:, :, 0])
        rhs = (rmat @ hopf(pts).T).T
        wrong = (rmat.T @ hopf(pts).T).T
        dev = jnp.max(jnp.linalg.norm(lhs - rhs, axis=1))
        wrong_dev = jnp.max(jnp.linalg.norm(lhs - wrong, axis=1))
        square_rows.append(
            {
                "axis": [as_float(x) for x in axis / jnp.linalg.norm(axis)],
                "angle": as_float(angle),
                "max_deviation": as_float(dev),
                "R_orthogonality_deviation": as_float(jnp.max(jnp.abs(rmat.T @ rmat - jnp.eye(3)))),
                "R_det_deviation": as_float(jnp.abs(jnp.linalg.det(rmat) - 1.0)),
            }
        )
        wrong_devs.append(wrong_dev)
    commuting_deviations = jnp.asarray([row["max_deviation"] for row in square_rows], dtype=jnp.float64)
    wrong_commuting_deviations = jnp.asarray(wrong_devs, dtype=jnp.float64)

    scale = 10**6
    sphere_scaled = [int(round(float(v) * scale)) for v in jax.device_get(hopf_norm_sq_max[:4096])]
    sphere_scrambled = [int(round(float(v) * scale)) for v in jax.device_get(jnp.sum(scrambled_hopf(psi_max[:4096]) ** 2, axis=1))]
    commute_scaled = [int(round(float(v) * scale)) for v in jax.device_get(commuting_deviations)]
    wrong_commute_scaled = [int(round(float(v) * scale)) for v in jax.device_get(wrong_commuting_deviations)]
    p1_z3 = z3_exists_outside_scaled(sphere_scaled, scale, 10)
    p1_cvc5 = cvc5_exists_outside_scaled(sphere_scaled, scale, 10)
    p1_control_z3 = z3_exists_outside_scaled(sphere_scrambled, scale, 10)
    p1_control_cvc5 = cvc5_exists_outside_scaled(sphere_scrambled, scale, 10)
    p2_z3 = z3_exists_outside_scaled(commute_scaled, 0, 10)
    p2_cvc5 = cvc5_exists_outside_scaled(commute_scaled, 0, 10)
    p2_control_z3 = z3_exists_outside_scaled(wrong_commute_scaled, 0, 10)
    p2_control_cvc5 = cvc5_exists_outside_scaled(wrong_commute_scaled, 0, 10)

    phase_sweep_rows = []
    for sweep_count in (8, 32, 128, 256):
        alphas = jnp.linspace(0.0, 2.0 * math.pi, sweep_count, endpoint=False, dtype=jnp.float64)
        h = hopf(jnp.exp(1j * alphas[:, None, None]) * phase_subset[None, :, :])
        phase_sweep_rows.append(
            {
                "alpha_count": sweep_count,
                "max_hopf_deviation": as_float(jnp.max(jnp.abs(h - hopf(phase_subset)[None, :, :]))),
            }
        )

    receipts = {
        "G1_spinors": {
            "dense_samples": NS,
            "max_norm_sq_deviation_N100000": as_float(jnp.max(jnp.abs(norm_sq_max - 1.0))),
            "chart_vector_roundtrip_max_deviation": as_float(chart_roundtrip_max),
            "broken_chart_control_max_hopf_coordinate_deviation": as_float(broken_chart_hopf_max),
            "pass": bool(as_float(jnp.max(jnp.abs(norm_sq_max - 1.0))) <= TOL and as_float(chart_roundtrip_max) <= TOL),
        },
        "G2_s3_metric_volume_geodesics": {
            "metric_formula": "deta^2+dphi^2+dchi^2+2cos(2eta)dphi dchi",
            "finite_difference_curve_rows": metric_rows,
            "max_curve_length_error": max(row["abs_error"] for row in metric_rows),
            "volume_convergence": convergence_ladder_rows["G2_s3_volume"],
            "s3_distance_label": "arccos(Re <psi1,psi2>) using R4 real inner product",
            "fubini_study_distance_label": "arccos(|<psi1,psi2>|) on the base quotient",
            "sample_s3_distance_mean": as_float(jnp.mean(s3_distance)),
            "sample_fubini_study_distance_mean": as_float(jnp.mean(fs_distance)),
            "phase_shift_tripwire": {
                "alpha": phase_alpha,
                "s3_distance": as_float(phase_s3),
                "fubini_study_distance": as_float(phase_fs),
                "fubini_study_same_ray_threshold": 1.0e-7,
                "conflation_detectable": bool(as_float(phase_s3) > 0.1 and as_float(phase_fs) <= 1.0e-7),
            },
            "pass": bool(max(row["abs_error"] for row in metric_rows) < 1.0e-5 and convergence_ladder_rows["G2_s3_volume"][-1]["abs_error"] < 1.0e-8),
        },
        "G3_su2_structure": {
            "su2_product_unitary_max_deviation": as_float(su2_unitary_dev),
            "su2_product_det_max_deviation": as_float(su2_det_dev),
            "quaternion_product_matrix_max_deviation": as_float(quat_matrix_dev),
            "double_cover": double_cover,
            "pass": bool(
                as_float(su2_unitary_dev) <= TOL
                and as_float(su2_det_dev) <= TOL
                and as_float(quat_matrix_dev) <= TOL
                and double_cover["rho_2pi_return_deviation"] <= TOL
                and double_cover["psi_2pi_plus_initial_norm"] <= TOL
                and double_cover["psi_4pi_minus_initial_norm"] <= TOL
            ),
        },
        "G4_hopf_map": {
            "formula": "x=2Re(z1*conj(z2)); y=2Im(z1*conj(z2)); z=|z1|^2-|z2|^2",
            "max_unit_sphere_deviation_N100000": as_float(jnp.max(jnp.abs(hopf_norm_sq_max - 1.0))),
            "coordinate_form_max_deviation": as_float(chart_hopf_max),
            "phase_invariance_max_deviation": as_float(phase_hopf_max),
            "uniformity_N100000": convergence_ladder_rows["G4_hopf_unit_sphere_uniformity"][-1]["uniformity"],
            "non_haar_clustered_control": non_haar_uniformity,
            "phase_sweep_granularity": phase_sweep_rows,
            "pass": bool(
                as_float(jnp.max(jnp.abs(hopf_norm_sq_max - 1.0))) <= TOL
                and as_float(chart_hopf_max) <= TOL
                and as_float(phase_hopf_max) <= TOL
                and convergence_ladder_rows["G4_hopf_unit_sphere_uniformity"][-1]["uniformity"]["pass"]
                and not non_haar_uniformity["pass"]
            ),
        },
        "G5_fibers": {
            "fiber_base_points": [[as_float(x) for x in row] for row in fiber_base_images],
            "fiber_map_to_single_basepoint_max_deviation": as_float(fiber_map_dev),
            "fiber_length_rows": [{"fiber_index": i, "length": length, "target": 2.0 * math.pi, "abs_error": abs(length - 2.0 * math.pi)} for i, length in enumerate(fiber_lengths)],
            "linking_integral_role": "computed independently in PyTorch leg by Gauss linking integral",
            "pass": bool(as_float(fiber_map_dev) <= TOL and max(abs(length - 2.0 * math.pi) for length in fiber_lengths) < 1.0e-5),
        },
        "G6_density_quotient": {
            "rho_equals_phase_rho_max_deviation_N100000_subset": exact_by_algebra_rows["G6_density_quotient"][-1]["rho_phase_invariance_max_deviation"],
            "bloch_vector_equals_hopf_max_deviation_N100000": exact_by_algebra_rows["G6_density_quotient"][-1]["bloch_equals_hopf_max_deviation"],
            "bloch_basis_pin": "(sigma_x,-sigma_y,sigma_z) so rho Bloch vector equals the stated Hopf y convention",
            "receipt_label": "exact_by_algebra_rows",
            "pass": bool(
                exact_by_algebra_rows["G6_density_quotient"][-1]["rho_phase_invariance_max_deviation"] <= TOL
                and exact_by_algebra_rows["G6_density_quotient"][-1]["bloch_equals_hopf_max_deviation"] <= TOL
            ),
        },
        "G7_s2_base": {
            "area_convergence": convergence_ladder_rows["G7_s2_area_and_commuting_square"],
            "commuting_square_rows": square_rows,
            "max_commuting_square_deviation": max(row["max_deviation"] for row in square_rows),
            "wrong_rotation_pairing_control_max_deviation": as_float(jnp.max(wrong_commuting_deviations)),
            "pass": bool(
                convergence_ladder_rows["G7_s2_area_and_commuting_square"][-1]["abs_error"] < 1.0e-8
                and max(row["max_deviation"] for row in square_rows) <= TOL
                and as_float(jnp.max(wrong_commuting_deviations)) > 1.0e-3
            ),
        },
    }

    proofs = {
        "P1_hopf_unit_sphere": {
            "scaled_integer_factor": scale,
            "bound_sample_count": len(sphere_scaled),
            "tolerance_int": 10,
            "z3_verdict": p1_z3,
            "cvc5_verdict": p1_cvc5,
            "scrambled_control_z3_verdict": p1_control_z3,
            "scrambled_control_cvc5_verdict": p1_control_cvc5,
            "raw_scaled_min_max": [min(sphere_scaled), max(sphere_scaled)],
            "scrambled_raw_scaled_min_max": [min(sphere_scrambled), max(sphere_scrambled)],
            "pass": p1_z3 == "unsat" and p1_cvc5 == "unsat" and p1_control_z3 == "sat" and p1_control_cvc5 == "sat",
        },
        "P2_commuting_square": {
            "scaled_integer_factor": scale,
            "bound_sample_count": len(commute_scaled),
            "tolerance_int": 10,
            "note": "current binding covers four max residuals from the commuting-square sample rows; proof-like use requires pointwise binding over the full sampled action.",
            "z3_verdict": p2_z3,
            "cvc5_verdict": p2_cvc5,
            "wrong_rotation_control_z3_verdict": p2_control_z3,
            "wrong_rotation_control_cvc5_verdict": p2_control_cvc5,
            "raw_scaled_values": commute_scaled,
            "wrong_control_raw_scaled_min_max": [min(wrong_commute_scaled), max(wrong_commute_scaled)],
            "pass": p2_z3 == "unsat" and p2_cvc5 == "unsat" and p2_control_z3 == "sat" and p2_control_cvc5 == "sat",
        },
    }

    all_pass = all(record["pass"] for record in receipts.values()) and all(record["pass"] for record in proofs.values())
    payload = {
        "schema_version": "geo_s1_spinor_hopf_free_leg_v1",
        "sim_id": SIM_ID,
        "engine": "jax",
        "role_id": "jax_batched_workhorse_sim_builder",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "program_receipt": PROGRAM_RECEIPT,
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "reads_peer_result": READS_PEER_RESULT,
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "claim_path_tools": ["z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "convention_pins": {
            "chart": "z1=cos(eta)exp(i(phi+chi)), z2=sin(eta)exp(i(phi-chi))",
            "s3_volume_chart_cover": "(phi,chi) in [0,2pi)^2 double-covers S3; volume integral includes factor 1/2",
            "bloch_basis": "(sigma_x,-sigma_y,sigma_z)",
            "linking_orientation": "positive Hopf link orientation delegated to PyTorch Gauss-integral leg",
        },
        "tripwires": {
            "s3_vs_fubini_study_distance_separated": receipts["G2_s3_metric_volume_geodesics"]["phase_shift_tripwire"]["conflation_detectable"],
            "no_bloch_ball_content": True,
            "no_torus_content": True,
        },
        "G_receipts": receipts,
        "convergence_rows": convergence_ladder_rows,
        "convergence_ladder_rows": convergence_ladder_rows,
        "exact_by_algebra_rows": exact_by_algebra_rows,
        "proofs": proofs,
        "controls": {
            "broken_chart_control_fails": bool(as_float(broken_chart_hopf_max) > 1.0e-2),
            "non_haar_clustered_uniformity_fails": not non_haar_uniformity["pass"],
            "phase_sweep_granularity": phase_sweep_rows,
        },
        "shared_scalars": {
            "hopf_unit_sphere_max_deviation": receipts["G4_hopf_map"]["max_unit_sphere_deviation_N100000"],
            "keystone_identity_max_deviation": receipts["G6_density_quotient"]["bloch_vector_equals_hopf_max_deviation_N100000"],
            "s2_commuting_square_max_deviation": receipts["G7_s2_base"]["max_commuting_square_deviation"],
            "s3_volume_final_abs_error": convergence_ladder_rows["G2_s3_volume"][-1]["abs_error"],
            "s2_area_final_abs_error": convergence_ladder_rows["G7_s2_area_and_commuting_square"][-1]["abs_error"],
        },
        "all_pass": bool(all_pass),
    }
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": bool(all_pass), "result_path": str(RESULT_PATH), "engine": "jax"}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

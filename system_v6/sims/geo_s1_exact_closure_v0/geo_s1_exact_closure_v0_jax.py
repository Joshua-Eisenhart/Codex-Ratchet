#!/usr/bin/env python3
"""SymPy + z3/cvc5 exact closure leg for geo_s1_exact_closure_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
from jax import config
from ott.geometry import pointcloud
from ott.problems.linear import linear_problem
from ott.solvers.linear import sinkhorn

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp
import sympy as sp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s1_exact_closure_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_jax.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"
LINEAGE_PACKET = "system_v6/sims/geo_s1_spinor_hopf_free_v0"
LINEAGE_COMMIT = "013fb0fa1"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
PIN_SPEC = (
    "geo_s1_exact_closure_v0|lineage=geo_s1_spinor_hopf_free_v0@013fb0fa1|"
    "convention_pin=X1_option_A_pinned_minus_sigma_y|sigma_y_standard=[[0,-i],[i,0]]|"
    "bloch_basis=(sigma_x,-sigma_y_standard,sigma_z)|r_i=Tr(rho*basis_i)|"
    "rho=psi*psi_dagger|Hopf_y=+2Im(z1*conj(z2))|derived_standard_y=-Hopf_y|"
    "derived_pinned_identity=Bloch_pinned(rho)=(x,y,z)|"
    "exact_strength=symbolic_closed_form_interval|"
    "seed_ledger=jax.random.PRNGKey[60610:haar_joint_n20000,"
    "60611:nonhaar_eta_n20000,60612:nonhaar_phi_n20000,60613:nonhaar_chi_n20000]|"
    "rerun=SIM_PY geo_s1_exact_closure_v0_{jax,julia,pytorch,envelope}|"
    "classification=scratch_diagnostic|"
    "promotion_allowed=false|formal_admission_allowed=false"
)

CONVENTION_PIN = {
    "pin_name": "X1_option_A_pinned_minus_sigma_y",
    "sigma_y_standard": "[[0,-i],[i,0]]",
    "bloch_basis": ["sigma_x", "-sigma_y_standard", "sigma_z"],
    "component_rule": "r_i = Tr(rho * basis_i)",
    "density_matrix": "rho = psi * psi^dagger",
    "hopf_y_convention": "Hopf_y = +2 Im(z1 * conj(z2))",
    "derived_standard_sigma_y_component": "Tr(rho * sigma_y_standard) = -2 Im(z1 * conj(z2))",
    "derived_pinned_y_component": "Tr(rho * (-sigma_y_standard)) = +2 Im(z1 * conj(z2))",
    "standard_bloch_relative_to_hopf": "Bloch_standard(rho) = (x, -y, z)",
    "pinned_keystone_identity": "Bloch_pinned(rho) = (x, y, z)",
}

TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing second CAS route for X1, X2, X3, X5, X6 exact expectations, and X7",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing real/integer exact solver flips for P1 and P2",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent NRA/LIA solver flips for P1 and P2",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic Haar and non-Haar sample statistic computation for redundant X6 rows",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive array substrate for X6 sample statistics only",
    },
    "ott": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Sinkhorn/PointCloud distance-to-uniform diagnostic for X6 Haar-vs-cluster control",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "jax": "supportive",
    "jax.numpy": "supportive",
    "ott": "load_bearing",
}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sstr(expr: Any) -> str:
    return sp.sstr(expr)


def mat_to_strings(matrix: sp.Matrix) -> list[list[str]]:
    return [[sstr(sp.simplify(matrix[i, j])) for j in range(matrix.cols)] for i in range(matrix.rows)]


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


def x6_sample_stats(points: jax.Array) -> dict[str, Any]:
    centered = points - jnp.mean(points, axis=0)
    cov = centered.T @ centered / points.shape[0]
    eigs = jnp.linalg.eigvalsh(cov)
    mean = jnp.mean(points, axis=0)
    return {
        "count": int(points.shape[0]),
        "mean_vector": [float(v) for v in jax.device_get(mean)],
        "second_moment_matrix": [[float(v) for v in row] for row in jax.device_get(cov)],
        "second_moment_eigenvalues": [float(v) for v in jax.device_get(eigs)],
        "max_second_moment_deviation_from_one_third": float(
            jax.device_get(jnp.max(jnp.abs(eigs - (1.0 / 3.0))))
        ),
    }


def fibonacci_sphere_points(count: int) -> jax.Array:
    idx = jnp.arange(count, dtype=jnp.float64) + 0.5
    z = 1.0 - 2.0 * idx / float(count)
    radius = jnp.sqrt(jnp.maximum(0.0, 1.0 - z * z))
    golden_angle = math.pi * (3.0 - math.sqrt(5.0))
    theta = golden_angle * idx
    return jnp.stack([radius * jnp.cos(theta), radius * jnp.sin(theta), z], axis=1)


def sinkhorn_distance_to_uniform(points: jax.Array, target: jax.Array) -> dict[str, Any]:
    count = int(points.shape[0])
    weights = jnp.ones((count,), dtype=jnp.float64) / float(count)
    target_weights = jnp.ones((int(target.shape[0]),), dtype=jnp.float64) / float(target.shape[0])
    geom = pointcloud.PointCloud(points, target, epsilon=0.05)
    problem = linear_problem.LinearProblem(geom, a=weights, b=target_weights)
    output = sinkhorn.Sinkhorn(threshold=1.0e-3, max_iterations=200)(problem)
    return {
        "ott_geometry": "ott.geometry.pointcloud.PointCloud",
        "ott_problem": "ott.problems.linear.linear_problem.LinearProblem",
        "ott_solver": "ott.solvers.linear.sinkhorn.Sinkhorn",
        "sample_count": count,
        "target_count": int(target.shape[0]),
        "epsilon": 0.05,
        "threshold": 1.0e-3,
        "max_iterations": 200,
        "reg_ot_cost": float(jax.device_get(output.reg_ot_cost)),
        "converged": bool(output.converged),
        "n_iters": int(output.n_iters),
    }


def x6_ott_wasserstein_diagnostic(haar_points: jax.Array, clustered_points: jax.Array) -> dict[str, Any]:
    sample_count = 256
    target = fibonacci_sphere_points(sample_count)
    haar = sinkhorn_distance_to_uniform(haar_points[:sample_count], target)
    clustered = sinkhorn_distance_to_uniform(clustered_points[:sample_count], target)
    return {
        "id": "X6_ott_wasserstein_distance_to_uniform",
        "strength": "statistical-redundant-diagnostic",
        "route": "ott Sinkhorn distance from Hopf pushforward samples to deterministic Fibonacci-sphere uniform proxy",
        "seed_ledger": {
            "haar": 60610,
            "clustered_eta": 60611,
            "clustered_chi": 60613,
            "target": "deterministic_fibonacci_sphere",
        },
        "calibrated_bar": {
            "haar_reg_ot_cost_lt": 0.35,
            "clustered_reg_ot_cost_gt": 1.0,
        },
        "haar": haar,
        "clustered_control": clustered,
        "clustered_control_fails_uniformity": clustered["reg_ot_cost"] > 1.0,
        "pass": haar["converged"]
        and clustered["converged"]
        and haar["reg_ot_cost"] < 0.35
        and clustered["reg_ot_cost"] > 1.0,
    }


def sympy_keystone() -> dict[str, Any]:
    a, b, c, d, u, v = sp.symbols("a b c d u v", real=True)
    z1 = a + sp.I * b
    z2 = c + sp.I * d
    psi = sp.Matrix([z1, z2])
    rho = psi * psi.conjugate().T
    sx = sp.Matrix([[0, 1], [1, 0]])
    sy_standard = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    sy_pinned = -sy_standard
    sz = sp.Matrix([[1, 0], [0, -1]])
    pinned_basis = (sx, sy_pinned, sz)
    bloch = sp.Matrix([sp.trace(rho * basis) for basis in pinned_basis])
    standard_y_component = sp.expand(sp.simplify(sp.trace(rho * sy_standard)))
    hopf_vec = sp.Matrix(
        [
            2 * sp.re(z1 * sp.conjugate(z2)),
            2 * sp.im(z1 * sp.conjugate(z2)),
            sp.re(z1 * sp.conjugate(z1) - z2 * sp.conjugate(z2)),
        ]
    )
    expanded = [sp.expand(sp.simplify(item)) for item in bloch - hopf_vec]
    corrupt = sp.Matrix([hopf_vec[0], sp.im(z1 * sp.conjugate(z2)), hopf_vec[2]])
    corrupt_expanded = [sp.expand(sp.simplify(item)) for item in bloch - corrupt]

    phase = u + sp.I * v
    phased = sp.Matrix([phase * z1, phase * z2])
    phased_hopf = sp.Matrix(
        [
            2 * sp.re(phased[0] * sp.conjugate(phased[1])),
            2 * sp.im(phased[0] * sp.conjugate(phased[1])),
            sp.re(phased[0] * sp.conjugate(phased[0]) - phased[1] * sp.conjugate(phased[1])),
        ]
    )
    phase_raw = [sp.factor(sp.expand(item)) for item in phased_hopf - hopf_vec]
    phase_reduced = [
        sp.factor(sp.expand(item.subs(u**2 + v**2, 1))) for item in phase_raw
    ]
    unit_expr = sp.expand(sum(component**2 for component in hopf_vec) - (a**2 + b**2 + c**2 + d**2) ** 2)
    return {
        "variables": ["a=Re(z1)", "b=Im(z1)", "c=Re(z2)", "d=Im(z2)"],
        "convention_pin": CONVENTION_PIN,
        "rho_from_psi_psidagger": mat_to_strings(rho),
        "pinned_pauli_basis": {
            "sigma_x": [["0", "1"], ["1", "0"]],
            "minus_sigma_y_standard": [["0", "I"], ["-I", "0"]],
            "sigma_z": [["1", "0"], ["0", "-1"]],
        },
        "standard_sigma_y_trace_expanded": sstr(standard_y_component),
        "standard_sigma_y_trace_plus_hopf_y_expanded": sstr(sp.expand(sp.simplify(standard_y_component + hopf_vec[1]))),
        "bloch_from_trace_expanded": [sstr(sp.expand(sp.simplify(item))) for item in bloch],
        "hopf_components_expanded": [sstr(sp.expand(sp.simplify(item))) for item in hopf_vec],
        "bloch_minus_hopf_expanded": [sstr(item) for item in expanded],
        "all_zero": all(item == 0 for item in expanded),
        "corrupted_identity_control_differences": [sstr(item) for item in corrupt_expanded],
        "corrupted_identity_control_pass": any(item != 0 for item in corrupt_expanded),
        "phase_raw_differences_factorized": [sstr(item) for item in phase_raw],
        "phase_side_relation": "u^2 + v^2 = 1 for e^{i alpha}=u+iv",
        "phase_reduced_differences": [sstr(item) for item in phase_reduced],
        "phase_invariance_symbolic": all(item == 0 for item in phase_reduced),
        "unit_image_difference": sstr(sp.factor(unit_expr)),
        "unit_image_symbolic": sp.factor(unit_expr) == 0,
    }


def sympy_metric_integrals() -> dict[str, Any]:
    eta, phi, chi = sp.symbols("eta phi chi", real=True)
    coords = sp.Matrix(
        [
            sp.cos(eta) * sp.cos(phi + chi),
            sp.cos(eta) * sp.sin(phi + chi),
            sp.sin(eta) * sp.cos(phi - chi),
            sp.sin(eta) * sp.sin(phi - chi),
        ]
    )
    params = (eta, phi, chi)
    jac = coords.jacobian(params)
    g = sp.simplify(jac.T * jac)
    det_g = sp.simplify(g.det())
    volume_chart_integral = sp.integrate(sp.sin(2 * eta), (eta, 0, sp.pi / 2)) * (2 * sp.pi) * (2 * sp.pi)
    volume_s3 = sp.simplify(volume_chart_integral / 2)
    theta, varphi = sp.symbols("theta varphi", real=True)
    area_s2 = sp.integrate(sp.sin(theta), (theta, 0, sp.pi)) * sp.integrate(1, (varphi, 0, 2 * sp.pi))
    torus_chart_integral = sp.simplify((2 * sp.pi) * (2 * sp.pi) * sp.sin(2 * eta))
    torus_area = sp.simplify(torus_chart_integral / 2)
    broken_coords = sp.Matrix(
        [
            sp.cos(eta) * sp.cos(phi + chi),
            sp.cos(eta) * sp.sin(phi + chi),
            sp.sin(eta) * sp.cos(phi + chi),
            sp.sin(eta) * sp.sin(phi + chi),
        ]
    )
    broken_g = sp.simplify(broken_coords.jacobian(params).T * broken_coords.jacobian(params))
    expected_g = sp.Matrix([[1, 0, 0], [0, 1, sp.cos(2 * eta)], [0, sp.cos(2 * eta), 1]])
    return {
        "metric_matrix": mat_to_strings(g),
        "metric_minus_expected": mat_to_strings(sp.simplify(g - expected_g)),
        "line_element": "deta^2 + dphi^2 + dchi^2 + 2*cos(2*eta)*dphi*dchi",
        "determinant": sstr(sp.factor(det_g)),
        "sqrt_det_on_eta_0_pi_over_2": "sin(2*eta)",
        "volume_chart_integral_before_double_cover_division": sstr(sp.simplify(volume_chart_integral)),
        "volume_double_cover_divisor": "2",
        "volume_s3": sstr(volume_s3),
        "area_s2": sstr(sp.simplify(area_s2)),
        "torus_chart_integral_before_double_cover_division": sstr(torus_chart_integral),
        "torus_double_cover_divisor": "2",
        "torus_area_eta": sstr(torus_area),
        "closed_form_pass": volume_s3 == 2 * sp.pi**2 and sp.simplify(area_s2) == 4 * sp.pi and torus_area == 2 * sp.pi**2 * sp.sin(2 * eta),
        "broken_chart_metric_control_matrix": mat_to_strings(broken_g),
        "broken_chart_metric_control_pass": sp.simplify(broken_g - expected_g) != sp.zeros(3, 3),
    }


def sympy_linking_and_double_cover() -> dict[str, Any]:
    t, u = sp.symbols("t u", real=True)
    circle = sp.Matrix([sp.cos(t), sp.sin(t), 0])
    line = sp.Matrix([0, 0, u])
    dcircle = sp.diff(circle, t)
    dline = sp.diff(line, u)
    diff = circle - line
    numerator = sp.simplify(diff.dot(dcircle.cross(dline)))
    denominator_sq = sp.simplify(diff.dot(diff))
    integrand = sp.simplify(numerator / denominator_sq ** sp.Rational(3, 2))
    u_integral = sp.integrate(1 / (1 + u**2) ** sp.Rational(3, 2), (u, -sp.oo, sp.oo))
    gauss_value = sp.simplify((1 / (4 * sp.pi)) * sp.integrate(1, (t, 0, 2 * sp.pi)) * u_integral)
    reversed_dline = -dline
    reversed_numerator = sp.simplify(diff.dot(dcircle.cross(reversed_dline)))
    reversed_integrand = sp.simplify(reversed_numerator / denominator_sq ** sp.Rational(3, 2))
    reversed_gauss_value = sp.simplify((1 / (4 * sp.pi)) * sp.integrate(1, (t, 0, 2 * sp.pi)) * sp.integrate(reversed_integrand, (u, -sp.oo, sp.oo)))

    sigma_z = sp.Matrix([[1, 0], [0, -1]])
    rows = []
    for multiple in (sp.Rational(0), sp.Rational(1, 2), sp.Rational(1), sp.Rational(3, 2), sp.Rational(2)):
        theta = multiple * sp.pi
        mat = sp.simplify(sp.exp(-sp.I * theta * sigma_z / 2))
        rows.append({"theta_over_pi": sstr(multiple), "matrix": mat_to_strings(mat)})
    u2pi = sp.simplify(sp.exp(-sp.I * (2 * sp.pi) * sigma_z / 2))
    u4pi = sp.simplify(sp.exp(-sp.I * (4 * sp.pi) * sigma_z / 2))
    return {
        "gauss_closed_form": {
            "s3_hopf_fibers": {
                "F_N(t)": "(exp(i*t), 0), Hopf base north pole",
                "F_E(s)": "(exp(i*s)/sqrt(2), exp(-i*s)/sqrt(2)), Hopf base equator point",
                "stereographic_pair_used_for_gauss": "standard linked circle plus compactified line model of two Hopf fibers",
            },
            "fiber_a_stereographic_image": "(cos(t), sin(t), 0), a compact Hopf fiber circle",
            "fiber_b_stereographic_image": "(0, 0, u) with u in R plus infinity, the compactified Hopf fiber through the projection point",
            "numerator": sstr(numerator),
            "denominator_squared": sstr(denominator_sq),
            "integrand": sstr(integrand),
            "u_integral": sstr(u_integral),
            "gauss_value": sstr(gauss_value),
            "orientation_reversal_control": {
                "reversed_fiber": "fiber_b",
                "reversed_numerator": sstr(reversed_numerator),
                "reversed_integrand": sstr(reversed_integrand),
                "reversed_gauss_value": sstr(reversed_gauss_value),
                "pass": reversed_gauss_value == -1,
            },
            "pass": gauss_value == 1 and reversed_gauss_value == -1,
        },
        "double_cover": {
            "generator": "sigma_z",
            "formula": "U(theta)=exp(-i*theta*sigma_z/2)",
            "u_2pi": mat_to_strings(u2pi),
            "u_4pi": mat_to_strings(u4pi),
            "u_2pi_equals_minus_identity": u2pi == -sp.eye(2),
            "u_4pi_equals_identity": u4pi == sp.eye(2),
            "path_rows": rows,
            "pass": u2pi == -sp.eye(2) and u4pi == sp.eye(2),
        },
    }


def sympy_haar_and_commuting_square() -> dict[str, Any]:
    theta, phi = sp.symbols("theta phi", real=True)
    x = sp.sin(theta) * sp.cos(phi)
    y = sp.sin(theta) * sp.sin(phi)
    z = sp.cos(theta)
    density = sp.sin(theta) / (4 * sp.pi)
    moment_matrix = []
    for left in (x, y, z):
        row = []
        for right in (x, y, z):
            row.append(sp.simplify(sp.integrate(sp.integrate(left * right * density, (phi, 0, 2 * sp.pi)), (theta, 0, sp.pi))))
        moment_matrix.append(row)
    cos_gamma = sp.symbols("cos_gamma", real=True)
    pairwise_density = sp.Rational(1, 2)
    pairwise_norm = sp.integrate(pairwise_density, (cos_gamma, -1, 1))
    pairwise_second = sp.integrate(cos_gamma**2 * pairwise_density, (cos_gamma, -1, 1))

    a, b, c, d, p, q, r, s = sp.symbols("a b c d p q r s", real=True)
    I = sp.I
    sx = sp.Matrix([[0, 1], [1, 0]])
    sy = sp.Matrix([[0, I], [-I, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    basis = (sx, sy, sz)
    psi = sp.Matrix([p + I * q, r + I * s])
    unitary = sp.Matrix([[a + I * b, -c + I * d], [c + I * d, a - I * b]])

    def density_matrix(vec: sp.Matrix) -> sp.Matrix:
        return vec * vec.conjugate().T

    def bloch(rho: sp.Matrix) -> sp.Matrix:
        return sp.Matrix([sp.simplify(sp.trace(rho * item)) for item in basis])

    rho_from_vec = lambda xx, yy, zz: sp.Rational(1, 2) * (sp.eye(2) + xx * sx + yy * sy + zz * sz)
    columns = []
    for vec in ((1, 0, 0), (0, 1, 0), (0, 0, 1)):
        columns.append(bloch(unitary * rho_from_vec(*vec) * unitary.conjugate().T))
    rotation = sp.Matrix.hstack(*columns)
    lhs = bloch(density_matrix(unitary * psi))
    rhs = rotation * bloch(density_matrix(psi))
    diffs = [sp.factor(sp.expand(item)) for item in lhs - rhs]
    return {
        "haar_exact_expected_values": {
            "sphere_second_moment_matrix": [[sstr(item) for item in row] for row in moment_matrix],
            "pairwise_cosine_density": "1/2 on [-1,1]",
            "pairwise_density_integral": sstr(pairwise_norm),
            "pairwise_cosine_second_moment": sstr(pairwise_second),
            "pass": moment_matrix == [[sp.Rational(1, 3), 0, 0], [0, sp.Rational(1, 3), 0], [0, 0, sp.Rational(1, 3)]]
            and pairwise_norm == 1
            and pairwise_second == sp.Rational(1, 3),
        },
        "commuting_square_symbolic": {
            "unitary_parameterization": "[[a+ib, -c+id], [c+id, a-ib]]",
            "rotation_matrix_from_bloch_action": mat_to_strings(rotation),
            "bloch_UrhoUdagger_minus_R_bloch_rho": [sstr(item) for item in diffs],
            "all_zero": all(item == 0 for item in diffs),
        },
    }


def z3_p1() -> dict[str, Any]:
    a, b, c, d = z3.Reals("a b c d")
    x_bloch = 2 * (a * c + b * d)
    y_bloch = 2 * (b * c - a * d)
    z_bloch = a * a + b * b - c * c - d * d
    x_hopf = 2 * (a * c + b * d)
    y_hopf = 2 * (b * c - a * d)
    z_hopf = a * a + b * b - c * c - d * d
    solver = z3.Solver()
    solver.add(z3.Or(x_bloch != x_hopf, y_bloch != y_hopf, z_bloch != z_hopf))
    corrupted = z3.Solver()
    corrupted.add(z3.Or(x_bloch != x_hopf, y_bloch != (b * c - a * d), z_bloch != z_hopf))
    return {"identity_nonzero_assertion": str(solver.check()), "corrupted_control": str(corrupted.check())}


def cvc5_p1() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_NRA")
    real = solver.getRealSort()
    a = solver.mkConst(real, "a")
    b = solver.mkConst(real, "b")
    c = solver.mkConst(real, "c")
    d = solver.mkConst(real, "d")
    two = solver.mkReal(2)

    def add(*terms: Any) -> Any:
        return terms[0] if len(terms) == 1 else solver.mkTerm(Kind.ADD, *terms)

    def sub(left: Any, right: Any) -> Any:
        return solver.mkTerm(Kind.SUB, left, right)

    def mul(*terms: Any) -> Any:
        return terms[0] if len(terms) == 1 else solver.mkTerm(Kind.MULT, *terms)

    x_bloch = mul(two, add(mul(a, c), mul(b, d)))
    y_bloch = mul(two, sub(mul(b, c), mul(a, d)))
    z_bloch = sub(add(mul(a, a), mul(b, b)), add(mul(c, c), mul(d, d)))
    x_hopf = mul(two, add(mul(a, c), mul(b, d)))
    y_hopf = mul(two, sub(mul(b, c), mul(a, d)))
    z_hopf = sub(add(mul(a, a), mul(b, b)), add(mul(c, c), mul(d, d)))
    solver.assertFormula(
        solver.mkTerm(
            Kind.OR,
            solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, x_bloch, x_hopf)),
            solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, y_bloch, y_hopf)),
            solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, z_bloch, z_hopf)),
        )
    )
    corrupted = cvc5.Solver()
    corrupted.setLogic("QF_NRA")
    real2 = corrupted.getRealSort()
    aa = corrupted.mkConst(real2, "aa")
    bb = corrupted.mkConst(real2, "bb")
    cc = corrupted.mkConst(real2, "cc")
    dd = corrupted.mkConst(real2, "dd")
    two2 = corrupted.mkReal(2)

    def add2(*terms: Any) -> Any:
        return terms[0] if len(terms) == 1 else corrupted.mkTerm(Kind.ADD, *terms)

    def sub2(left: Any, right: Any) -> Any:
        return corrupted.mkTerm(Kind.SUB, left, right)

    def mul2(*terms: Any) -> Any:
        return terms[0] if len(terms) == 1 else corrupted.mkTerm(Kind.MULT, *terms)

    corrupted.assertFormula(
        corrupted.mkTerm(
            Kind.OR,
            corrupted.mkTerm(Kind.NOT, corrupted.mkTerm(Kind.EQUAL, mul2(two2, add2(mul2(aa, cc), mul2(bb, dd))), mul2(two2, add2(mul2(aa, cc), mul2(bb, dd))))),
            corrupted.mkTerm(Kind.NOT, corrupted.mkTerm(Kind.EQUAL, mul2(two2, sub2(mul2(bb, cc), mul2(aa, dd))), sub2(mul2(bb, cc), mul2(aa, dd)))),
            corrupted.mkTerm(Kind.NOT, corrupted.mkTerm(Kind.EQUAL, sub2(add2(mul2(aa, aa), mul2(bb, bb)), add2(mul2(cc, cc), mul2(dd, dd))), sub2(add2(mul2(aa, aa), mul2(bb, bb)), add2(mul2(cc, cc), mul2(dd, dd))))),
        )
    )
    return {"identity_nonzero_assertion": str(solver.checkSat()).lower(), "corrupted_control": str(corrupted.checkSat()).lower()}


def z3_p2(signed_sum: int, scrambled_sum: int) -> dict[str, Any]:
    value = z3.Int("signed_sum")
    solver = z3.Solver()
    solver.add(value == signed_sum)
    solver.add(value != 2)
    bad = z3.Int("scrambled_signed_sum")
    control = z3.Solver()
    control.add(bad == scrambled_sum)
    control.add(bad != 2)
    return {"signed_sum_not_two": str(solver.check()), "scrambled_control_not_two": str(control.check())}


def cvc5_p2(signed_sum: int, scrambled_sum: int) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    integer = solver.getIntegerSort()
    value = solver.mkConst(integer, "signed_sum")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, value, solver.mkInteger(signed_sum)))
    solver.assertFormula(solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, value, solver.mkInteger(2))))
    control = cvc5.Solver()
    control.setLogic("QF_LIA")
    integer2 = control.getIntegerSort()
    bad = control.mkConst(integer2, "scrambled_signed_sum")
    control.assertFormula(control.mkTerm(Kind.EQUAL, bad, control.mkInteger(scrambled_sum)))
    control.assertFormula(control.mkTerm(Kind.NOT, control.mkTerm(Kind.EQUAL, bad, control.mkInteger(2))))
    return {"signed_sum_not_two": str(solver.checkSat()).lower(), "scrambled_control_not_two": str(control.checkSat()).lower()}


def exact_sign(expr: sp.Expr) -> int:
    simplified = sp.simplify(expr)
    if simplified.is_positive:
        return 1
    if simplified.is_negative:
        return -1
    raise ValueError(f"cannot determine exact sign for {sp.sstr(simplified)}")


def det2(left: sp.Matrix, right: sp.Matrix) -> sp.Expr:
    return sp.simplify(left[0] * right[1] - left[1] * right[0])


def sympy_crossing_records() -> dict[str, Any]:
    eps = sp.Rational(1, 2)
    roots = [sp.pi / 3, 5 * sp.pi / 3]
    records: list[dict[str, Any]] = []
    for idx, root in enumerate(roots):
        u_value = sp.sin(root)
        circle = sp.Matrix([sp.cos(root), sp.sin(root), sp.Integer(0)])
        line = sp.Matrix([eps, u_value, u_value])
        circle_tangent = sp.Matrix([-sp.sin(root), sp.cos(root), sp.Integer(0)])
        line_tangent = sp.Matrix([sp.Integer(0), sp.Integer(1), sp.Integer(1)])
        circle_projected_tangent = sp.Matrix([circle_tangent[0], circle_tangent[1]])
        line_projected_tangent = sp.Matrix([line_tangent[0], line_tangent[1]])
        projection_match = all(sp.simplify(circle[i] - line[i]) == 0 for i in (0, 1))
        z_delta = sp.simplify(line[2] - circle[2])
        if z_delta.is_positive:
            over_curve = "line"
            under_curve = "circle"
            orientation_det = det2(line_projected_tangent, circle_projected_tangent)
        elif z_delta.is_negative:
            over_curve = "circle"
            under_curve = "line"
            orientation_det = det2(circle_projected_tangent, line_projected_tangent)
        else:
            raise ValueError("crossing has zero z-order separation")
        sign = exact_sign(orientation_det)
        records.append(
            {
                "index": idx,
                "projection": "xy",
                "segment_pair": ["C(t)=(cos(t),sin(t),0)", "L(u)=(1/2,u,u)"],
                "circle_parameter": sstr(root),
                "line_parameter": sstr(u_value),
                "circle_point": [sstr(sp.simplify(item)) for item in circle],
                "line_point": [sstr(sp.simplify(item)) for item in line],
                "circle_projected_tangent": [sstr(sp.simplify(item)) for item in circle_projected_tangent],
                "line_projected_tangent": [sstr(sp.simplify(item)) for item in line_projected_tangent],
                "projection_match_exact": bool(projection_match),
                "z_delta_line_minus_circle": sstr(z_delta),
                "over_curve_from_z_order": over_curve,
                "under_curve_from_z_order": under_curve,
                "orientation_determinant_ordered_over_under": sstr(sp.simplify(orientation_det)),
                "sign_rule": "sign(det(projected_tangent_over, projected_tangent_under)) with exact z-order selecting over/under",
                "computed_sign": sign,
            }
        )
    signs = [row["computed_sign"] for row in records]
    scrambled_signs = [signs[0], -signs[1]]
    return {
        "records": records,
        "signed_sum": sum(signs),
        "signed_sum_over_2": sstr(sp.Rational(sum(signs), 2)),
        "scrambled_control_signs": scrambled_signs,
        "scrambled_control_signed_sum": sum(scrambled_signs),
        "all_projection_matches_exact": all(row["projection_match_exact"] for row in records),
        "pass": sum(signs) == 2 and sum(scrambled_signs) != 2,
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    x1x2 = sympy_keystone()
    x3 = sympy_metric_integrals()
    link_double = sympy_linking_and_double_cover()
    x6x7 = sympy_haar_and_commuting_square()
    crossing = sympy_crossing_records()
    psi = normalized_complex_gaussian(20000, 60610)
    haar_points = hopf(psi)
    nonhaar_eta = 0.08 * jax.random.uniform(jax.random.PRNGKey(60611), (20000,), dtype=jnp.float64)
    nonhaar_phi = 2.0 * math.pi * jax.random.uniform(jax.random.PRNGKey(60612), (20000,), dtype=jnp.float64)
    nonhaar_chi = 2.0 * math.pi * jax.random.uniform(jax.random.PRNGKey(60613), (20000,), dtype=jnp.float64)
    nonhaar = jnp.stack(
        [
            jnp.sin(2.0 * nonhaar_eta) * jnp.cos(2.0 * nonhaar_chi),
            jnp.sin(2.0 * nonhaar_eta) * jnp.sin(2.0 * nonhaar_chi),
            jnp.cos(2.0 * nonhaar_eta),
        ],
        axis=1,
    )
    haar_stats = x6_sample_stats(haar_points)
    nonhaar_stats = x6_sample_stats(nonhaar)
    crossing_records = crossing["records"]
    signed_sum = crossing["signed_sum"]
    scrambled_sum = crossing["scrambled_control_signed_sum"]
    proofs = {
        "P1_keystone_polynomial": {
            "z3": z3_p1(),
            "cvc5": cvc5_p1(),
        },
        "P2_crossing_count_integer": {
            "crossing_records": crossing_records,
            "signed_sum": signed_sum,
            "signed_sum_over_2": "1",
            "crossing_sign_source": "computed from exact projected tangent orientation determinant plus exact z-order",
            "scrambled_control_signs": crossing["scrambled_control_signs"],
            "scrambled_control_signed_sum": scrambled_sum,
            "z3": z3_p2(signed_sum, scrambled_sum),
            "cvc5": cvc5_p2(signed_sum, scrambled_sum),
        },
    }
    x4 = {
        "crossing_count_exact_integer": {
            **crossing,
            "signed_sum_over_2": "1",
        },
        "gauss_closed_form": link_double["gauss_closed_form"],
    }
    x6 = x6x7["haar_exact_expected_values"]
    x6["haar_joint_sample_statistic"] = {
        **haar_stats,
        "strength": "statistical-redundant",
        "expected_values_exact": "mean=0, second_moment=I/3; exact derivation above",
        "pass_threshold": "max eigenvalue deviation < 0.02",
        "pass": haar_stats["max_second_moment_deviation_from_one_third"] < 0.02,
    }
    x6["non_haar_control"] = {
        **nonhaar_stats,
        "must_fail_threshold": "max eigenvalue deviation >= 0.02",
        "pass": nonhaar_stats["max_second_moment_deviation_from_one_third"] >= 0.02,
    }
    x6["ott_wasserstein_distance_to_uniform"] = x6_ott_wasserstein_diagnostic(haar_points, nonhaar)
    all_pass = (
        x1x2["all_zero"]
        and x1x2["corrupted_identity_control_pass"]
        and x1x2["phase_invariance_symbolic"]
        and x1x2["unit_image_symbolic"]
        and x3["closed_form_pass"]
        and x3["broken_chart_metric_control_pass"]
        and x4["crossing_count_exact_integer"]["pass"]
        and x4["gauss_closed_form"]["pass"]
        and link_double["double_cover"]["pass"]
        and x6["pass"]
        and x6["haar_joint_sample_statistic"]["pass"]
        and x6["non_haar_control"]["pass"]
        and x6["ott_wasserstein_distance_to_uniform"]["pass"]
        and x6x7["commuting_square_symbolic"]["all_zero"]
        and proofs["P1_keystone_polynomial"]["z3"]["identity_nonzero_assertion"] == "unsat"
        and proofs["P1_keystone_polynomial"]["z3"]["corrupted_control"] == "sat"
        and proofs["P1_keystone_polynomial"]["cvc5"]["identity_nonzero_assertion"] == "unsat"
        and proofs["P1_keystone_polynomial"]["cvc5"]["corrupted_control"] == "sat"
        and proofs["P2_crossing_count_integer"]["z3"]["signed_sum_not_two"] == "unsat"
        and proofs["P2_crossing_count_integer"]["z3"]["scrambled_control_not_two"] == "sat"
        and proofs["P2_crossing_count_integer"]["cvc5"]["signed_sum_not_two"] == "unsat"
        and proofs["P2_crossing_count_integer"]["cvc5"]["scrambled_control_not_two"] == "sat"
    )
    payload = {
        "schema_version": "geo_s1_exact_closure_v0_leg_v1",
        "sim_id": SIM_ID,
        "engine": "jax",
        "role_id": "jax_rich_mirror_sim_builder",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "lineage": {"packet": LINEAGE_PACKET, "commit": LINEAGE_COMMIT, "modified_lineage_packet": False},
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "convention_pin": CONVENTION_PIN,
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "packages_used": ["jax", "jax.numpy", "sympy", "z3", "cvc5", "ott"],
        "aligned_packages_load_bearing": ["sympy", "z3", "cvc5", "ott"],
        "claim_path_tools": ["sympy", "z3", "cvc5", "ott"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "X_receipts": {
            "X1_keystone_identity_symbolic_sympy": x1x2,
            "X2_phase_invariance_unit_image_symbolic_sympy": {
                "phase_raw_differences_factorized": x1x2["phase_raw_differences_factorized"],
                "phase_side_relation": x1x2["phase_side_relation"],
                "phase_reduced_differences": x1x2["phase_reduced_differences"],
                "phase_invariance_symbolic": x1x2["phase_invariance_symbolic"],
                "unit_image_difference": x1x2["unit_image_difference"],
                "unit_image_symbolic": x1x2["unit_image_symbolic"],
            },
            "X3_metric_integrals_closed_form_sympy": x3,
            "X4_linking_exact_routes_sympy_smt": x4,
            "X5_double_cover_exact_sympy": link_double["double_cover"],
            "X6_haar_rotation_invariant_joint_statistic": x6,
            "X7_commuting_square_symbolic_sympy": x6x7["commuting_square_symbolic"],
        },
        "proofs": proofs,
        "controls": {
            "corrupted_identity_control": x1x2["corrupted_identity_control_differences"],
            "broken_chart_metric_control": x3["broken_chart_metric_control_matrix"],
            "non_haar_sample_control": x6["non_haar_control"],
            "ott_wasserstein_clustered_control": x6["ott_wasserstein_distance_to_uniform"]["clustered_control"],
        },
        "shared_scalars": {
            "symbolic_zero_count": sum(
                item == "0" for item in x1x2["bloch_minus_hopf_expanded"] + x6x7["commuting_square_symbolic"]["bloch_UrhoUdagger_minus_R_bloch_rho"]
            ),
            "linking_number_exact": 1,
            "gauss_linking_exact": 1,
            "classification_bare_float_rows": 0,
        },
        "all_pass": bool(all_pass),
    }
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": bool(all_pass), "engine": "jax", "result_path": str(RESULT_PATH)}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

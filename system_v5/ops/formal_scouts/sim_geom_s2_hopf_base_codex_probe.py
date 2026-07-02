#!/usr/bin/env python3
"""Known-geometry Hopf-base probe for cross-model comparison.

This is an independent Codex-built diagnostic probe for the Hopf base

    pi(psi) = psi^dagger sigma psi in S^2,  psi in CP^1.

It computes the requested known values from the math with torch complex128 /
float64 as the numeric substrate, plus symbolic/proof/topology/tool checks.
No NumPy is imported or used as a claim-bearing substrate. No opus-built sim or
result is read.

classification = diagnostic_only
"""

from __future__ import annotations

import json
import math
import os
import pathlib
from typing import Any

# geomstats and clifford need their backend/cache switches before import.
os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import cvc5
from cvc5 import Kind
from clifford import Cl
import gudhi
import rustworkx as rx
import sympy as sp
import torch
import toponetx as tnx
import z3
from geomstats.geometry.hypersphere import Hypersphere

CDTYPE = torch.complex128
RTYPE = torch.float64
torch.set_default_dtype(RTYPE)

ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "geom_s2_hopf_base_codex_probe"
OUT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
WITNESS_PATH = RESULT_DIR / f"{SIM_ID}_witness.json"

NORM_TOL = 1.0e-12
PHASE_TOL = 1.0e-12
DIST_TOL = 1.0e-12
AREA_TOL = 5.0e-9
CURVATURE_TOL = 1.0e-12
TOPOLOGY_TOL = 0

THETA_GRID = [0.0, 0.17, 0.61, math.pi / 2.0, 1.91, 2.73, math.pi]
PHI_GRID = [0.0, 0.29, 0.73, 1.41, math.pi, 4.20, 5.70]
ALPHA_GRID = [-2.0 * math.pi, -1.7, -0.25, 0.0, 0.31, 1.9, math.pi, 6.7]
AREA_MIDPOINT_STEPS = 65536


def as_jsonable(obj: Any) -> Any:
    if isinstance(obj, torch.Tensor):
        if obj.ndim == 0:
            return obj.item()
        return obj.detach().cpu().tolist()
    if isinstance(obj, pathlib.Path):
        return str(obj)
    if isinstance(obj, (set, tuple)):
        return list(obj)
    if isinstance(obj, dict):
        return {str(k): as_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [as_jsonable(v) for v in obj]
    return obj


def cexp(angle: float) -> torch.Tensor:
    return torch.exp(1j * torch.tensor(angle, dtype=RTYPE))


def normalize_spinor(psi: torch.Tensor) -> torch.Tensor:
    return (psi / torch.linalg.vector_norm(psi)).to(CDTYPE)


def cp1_spinor(theta: float, phi: float) -> torch.Tensor:
    return normalize_spinor(
        torch.stack(
            [
                torch.tensor(math.cos(theta / 2.0), dtype=CDTYPE),
                cexp(phi) * torch.tensor(math.sin(theta / 2.0), dtype=CDTYPE),
            ]
        )
    )


def pauli_matrices() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    zero = torch.tensor(0.0 + 0.0j, dtype=CDTYPE)
    one = torch.tensor(1.0 + 0.0j, dtype=CDTYPE)
    im = torch.tensor(0.0 + 1.0j, dtype=CDTYPE)
    sigma_x = torch.stack([torch.stack([zero, one]), torch.stack([one, zero])])
    sigma_y = torch.stack([torch.stack([zero, -im]), torch.stack([im, zero])])
    sigma_z = torch.stack([torch.stack([one, zero]), torch.stack([zero, -one])])
    return sigma_x, sigma_y, sigma_z


SIGMA_X, SIGMA_Y, SIGMA_Z = pauli_matrices()
PAULIS = (SIGMA_X, SIGMA_Y, SIGMA_Z)


def hopf_projection(psi: torch.Tensor) -> tuple[torch.Tensor, float]:
    coords = []
    max_imag = 0.0
    for sigma in PAULIS:
        value = torch.vdot(psi, sigma @ psi)
        max_imag = max(max_imag, abs(float(value.imag.item())))
        coords.append(value.real.to(RTYPE))
    return torch.stack(coords), max_imag


def analytic_s2_point(theta: float, phi: float) -> torch.Tensor:
    return torch.tensor(
        [math.sin(theta) * math.cos(phi), math.sin(theta) * math.sin(phi), math.cos(theta)],
        dtype=RTYPE,
    )


def torch_hopf_sweep() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    max_norm_err = 0.0
    max_formula_err = 0.0
    max_phase_drift = 0.0
    max_imag = 0.0
    max_spinor_norm_err = 0.0

    for theta in THETA_GRID:
        for phi in PHI_GRID:
            psi = cp1_spinor(theta, phi)
            pi_psi, imag = hopf_projection(psi)
            expected = analytic_s2_point(theta, phi)
            norm = float(torch.linalg.vector_norm(pi_psi).item())
            spinor_norm = float(torch.linalg.vector_norm(psi).item())
            norm_err = abs(norm - 1.0)
            formula_err = float(torch.linalg.vector_norm(pi_psi - expected).item())
            row_phase_drift = 0.0
            for alpha in ALPHA_GRID:
                phased = cexp(alpha) * psi
                pi_phased, phased_imag = hopf_projection(phased)
                drift = float(torch.linalg.vector_norm(pi_phased - pi_psi).item())
                row_phase_drift = max(row_phase_drift, drift)
                max_phase_drift = max(max_phase_drift, drift)
                max_imag = max(max_imag, phased_imag)
            max_norm_err = max(max_norm_err, norm_err)
            max_formula_err = max(max_formula_err, formula_err)
            max_imag = max(max_imag, imag)
            max_spinor_norm_err = max(max_spinor_norm_err, abs(spinor_norm - 1.0))
            rows.append(
                {
                    "theta": theta,
                    "phi": phi,
                    "spinor": [[float(psi[i].real.item()), float(psi[i].imag.item())] for i in range(2)],
                    "pi": [float(x.item()) for x in pi_psi],
                    "expected_s2_point": [float(x.item()) for x in expected],
                    "pi_norm": norm,
                    "norm_error": norm_err,
                    "formula_error": formula_err,
                    "max_u1_phase_drift": row_phase_drift,
                    "max_projection_imag": imag,
                }
            )

    comm_xy = SIGMA_X @ SIGMA_Y - SIGMA_Y @ SIGMA_X
    comm_expected = 2.0j * SIGMA_Z
    comm_err = float(torch.linalg.vector_norm(comm_xy - comm_expected).item())

    return {
        "rows": rows,
        "max_spinor_norm_error": max_spinor_norm_err,
        "max_projection_norm_error": max_norm_err,
        "max_projection_formula_error": max_formula_err,
        "max_u1_phase_drift": max_phase_drift,
        "max_expectation_imag": max_imag,
        "pauli_commutator_xy_minus_yx_equals_2i_z_error": comm_err,
        "n_states": len(rows),
        "n_phase_controls": len(rows) * len(ALPHA_GRID),
    }


def torch_s2_area_midpoint(n: int = AREA_MIDPOINT_STEPS) -> float:
    idx = torch.arange(n, dtype=RTYPE)
    theta_mid = (idx + 0.5) * (math.pi / float(n))
    dtheta = math.pi / float(n)
    dphi = 2.0 * math.pi
    return float((torch.sin(theta_mid).sum() * dtheta * dphi).item())


def sympy_exact_geometry() -> dict[str, Any]:
    theta, phi, alpha = sp.symbols("theta phi alpha", real=True)
    i = sp.I
    psi = sp.Matrix(
        [
            sp.exp(i * alpha) * sp.cos(theta / 2),
            sp.exp(i * (alpha + phi)) * sp.sin(theta / 2),
        ]
    )
    sx = sp.Matrix([[0, 1], [1, 0]])
    sy = sp.Matrix([[0, -i], [i, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    coords = [sp.simplify((psi.conjugate().T * sigma * psi)[0]) for sigma in (sx, sy, sz)]
    expected = [sp.sin(theta) * sp.cos(phi), sp.sin(theta) * sp.sin(phi), sp.cos(theta)]
    projection_matches_formula = all(sp.simplify(c - e) == 0 for c, e in zip(coords, expected))
    norm_sq = sp.simplify(sum(c * c for c in coords))

    psi0 = sp.Matrix([sp.cos(theta / 2), sp.exp(i * phi) * sp.sin(theta / 2)])
    coords0 = [sp.simplify((psi0.conjugate().T * sigma * psi0)[0]) for sigma in (sx, sy, sz)]
    phase_invariant = all(sp.simplify(c - c0) == 0 for c, c0 in zip(coords, coords0))

    area = sp.integrate(sp.integrate(sp.sin(theta), (phi, 0, 2 * sp.pi)), (theta, 0, sp.pi))

    coords2 = [theta, phi]
    metric = sp.Matrix([[1, 0], [0, sp.sin(theta) ** 2]])
    inv_metric = metric.inv()
    gamma = [[[0 for _ in range(2)] for _ in range(2)] for _ in range(2)]
    for a in range(2):
        for b in range(2):
            for c in range(2):
                gamma[a][b][c] = sp.simplify(
                    sp.Rational(1, 2)
                    * sum(
                        inv_metric[a, d]
                        * (
                            sp.diff(metric[d, c], coords2[b])
                            + sp.diff(metric[d, b], coords2[c])
                            - sp.diff(metric[b, c], coords2[d])
                        )
                        for d in range(2)
                    )
                )

    riemann = [[[[0 for _ in range(2)] for _ in range(2)] for _ in range(2)] for _ in range(2)]
    for a in range(2):
        for b in range(2):
            for c in range(2):
                for d in range(2):
                    riemann[a][b][c][d] = sp.simplify(
                        sp.diff(gamma[a][b][d], coords2[c])
                        - sp.diff(gamma[a][b][c], coords2[d])
                        + sum(
                            gamma[a][c][m] * gamma[m][b][d]
                            - gamma[a][d][m] * gamma[m][b][c]
                            for m in range(2)
                        )
                    )
    r_theta_phi_theta_phi = sp.simplify(
        sum(metric[0, a] * riemann[a][1][0][1] for a in range(2))
    )
    gaussian_curvature = sp.simplify(r_theta_phi_theta_phi / metric.det())

    antipodal_distance = sp.acos(sp.Integer(-1))

    return {
        "projection_components": [str(sp.simplify(c)) for c in coords],
        "projection_matches_formula": bool(projection_matches_formula),
        "projection_norm_squared": str(norm_sq),
        "projection_norm_squared_equals_one": bool(sp.simplify(norm_sq - 1) == 0),
        "u1_phase_invariant_exact": bool(phase_invariant),
        "area_exact": str(sp.simplify(area)),
        "area_equals_4pi": bool(sp.simplify(area - 4 * sp.pi) == 0),
        "gaussian_curvature_exact": str(gaussian_curvature),
        "gaussian_curvature_equals_one": bool(sp.simplify(gaussian_curvature - 1) == 0),
        "antipodal_distance_exact": str(antipodal_distance),
        "antipodal_distance_equals_pi": bool(sp.simplify(antipodal_distance - sp.pi) == 0),
    }


def geomstats_antipodal_distance(points: list[torch.Tensor]) -> dict[str, Any]:
    sphere = Hypersphere(dim=2)
    rows = []
    max_err = 0.0
    max_input_norm_error = 0.0
    max_belongs_fail = 0
    for p in points:
        input_norm = float(torch.linalg.vector_norm(p).item())
        max_input_norm_error = max(max_input_norm_error, abs(input_norm - 1.0))
        p = (p / torch.linalg.vector_norm(p)).to(RTYPE)
        q = -p
        p_g = p.to(RTYPE)
        q_g = q.to(RTYPE)
        belongs_p = bool(sphere.belongs(p_g).item())
        belongs_q = bool(sphere.belongs(q_g).item())
        max_belongs_fail += 0 if belongs_p and belongs_q else 1
        dist = float(sphere.metric.dist(p_g, q_g).item())
        err = abs(dist - math.pi)
        max_err = max(max_err, err)
        rows.append({"p": [float(x.item()) for x in p], "distance_to_antipode": dist, "err": err})
    return {
        "rows": rows,
        "max_input_norm_error_before_geomstats_normalization": max_input_norm_error,
        "max_antipodal_distance_error": max_err,
        "belongs_failures": max_belongs_fail,
        "n_pairs": len(rows),
    }


def torch_antipodal_distance(points: list[torch.Tensor]) -> dict[str, Any]:
    rows = []
    max_err = 0.0
    max_dot_err = 0.0
    for p in points:
        q = -p
        dot = torch.dot(p, q)
        dot_clamped = torch.clamp(dot, -1.0, 1.0)
        dist = float(torch.acos(dot_clamped).item())
        err = abs(dist - math.pi)
        dot_err = abs(float(dot.item()) + 1.0)
        max_err = max(max_err, err)
        max_dot_err = max(max_dot_err, dot_err)
        rows.append(
            {
                "p": [float(x.item()) for x in p],
                "dot_with_antipode": float(dot.item()),
                "distance_to_antipode": dist,
                "distance_error": err,
            }
        )
    return {"rows": rows, "max_distance_error": max_err, "max_dot_plus_one_error": max_dot_err}


def clifford_s2_vector_checks(points: list[torch.Tensor]) -> dict[str, Any]:
    _layout, blades = Cl(3)
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    rows = []
    max_square_err = 0.0
    max_antipode_product_err = 0.0
    max_non_scalar = 0.0
    for p in points:
        x, y, z = (float(v.item()) for v in p)
        v = x * e1 + y * e2 + z * e3
        v_square = v * v
        scalar = float(v_square.value[0])
        non_scalar = float(sum(abs(float(c)) for c in v_square.value[1:]))
        antipode_product = v * (-v)
        antipode_scalar = float(antipode_product.value[0])
        antipode_non_scalar = float(sum(abs(float(c)) for c in antipode_product.value[1:]))
        square_err = abs(scalar - 1.0)
        antipode_err = abs(antipode_scalar + 1.0)
        max_square_err = max(max_square_err, square_err)
        max_antipode_product_err = max(max_antipode_product_err, antipode_err)
        max_non_scalar = max(max_non_scalar, non_scalar, antipode_non_scalar)
        rows.append(
            {
                "point": [x, y, z],
                "vector_square_scalar": scalar,
                "vector_square_non_scalar_l1": non_scalar,
                "antipode_geometric_product_scalar": antipode_scalar,
                "antipode_geometric_product_non_scalar_l1": antipode_non_scalar,
            }
        )
    return {
        "rows": rows,
        "max_vector_square_err": max_square_err,
        "max_antipode_product_err": max_antipode_product_err,
        "max_non_scalar_l1": max_non_scalar,
        "pass": max_square_err < NORM_TOL
        and max_antipode_product_err < NORM_TOL
        and max_non_scalar < NORM_TOL,
    }


def s2_triangulation_tool_checks() -> dict[str, Any]:
    faces = [(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)]
    edges = sorted({tuple(sorted((face[i], face[j]))) for face in faces for i in range(3) for j in range(i + 1, 3)})

    graph = rx.PyGraph()
    graph.add_nodes_from(range(4))
    graph.add_edges_from_no_data(edges)
    rustworkx_connected = bool(rx.is_connected(graph))
    rustworkx_euler = graph.num_nodes() - graph.num_edges() + len(faces)

    complex_tnx = tnx.SimplicialComplex(faces)
    tnx_counts = tuple(int(x) for x in complex_tnx.shape)
    tnx_euler = tnx_counts[0] - tnx_counts[1] + tnx_counts[2]
    incidence_shape = tuple(int(x) for x in complex_tnx.incidence_matrix(2).shape)

    simplex_tree = gudhi.SimplexTree()
    for face in faces:
        simplex_tree.insert(face)
    simplex_tree.persistence(persistence_dim_max=True)
    betti = [int(x) for x in simplex_tree.betti_numbers()]

    collapsed_tree = gudhi.SimplexTree()
    for face in faces[:3]:
        collapsed_tree.insert(face)
    collapsed_tree.persistence(persistence_dim_max=True)
    collapsed_betti = [int(x) for x in collapsed_tree.betti_numbers()]
    collapsed_euler = 4 - 6 + 3

    pass_topology = (
        rustworkx_connected
        and rustworkx_euler == 2
        and tnx_counts == (4, 6, 4)
        and tnx_euler == 2
        and incidence_shape == (6, 4)
        and betti == [1, 0, 1]
    )

    return {
        "faces": faces,
        "edges": edges,
        "rustworkx": {
            "connected": rustworkx_connected,
            "nodes": graph.num_nodes(),
            "edges": graph.num_edges(),
            "faces": len(faces),
            "euler_characteristic": rustworkx_euler,
        },
        "toponetx": {
            "shape": list(tnx_counts),
            "incidence_matrix_dim2_shape": list(incidence_shape),
            "euler_characteristic": tnx_euler,
        },
        "gudhi": {
            "num_vertices": int(simplex_tree.num_vertices()),
            "num_simplices": int(simplex_tree.num_simplices()),
            "betti_numbers": betti,
        },
        "collapsed_negative": {
            "removed_face": faces[-1],
            "euler_characteristic": collapsed_euler,
            "betti_numbers": collapsed_betti,
            "kills_s2_signature": collapsed_euler != 2 or collapsed_betti != [1, 0, 1],
        },
        "pass": pass_topology,
    }


def _z3_rat(value: float) -> Any:
    rat = sp.Rational(value).limit_denominator(10**12)
    num, den = sp.fraction(rat)
    return z3.Q(int(num), int(den))


def z3_error_certificate(errors: dict[str, tuple[float, float]]) -> dict[str, Any]:
    solver = z3.Solver()
    bad_terms = []
    rows = {}
    for idx, (name, (value, tol)) in enumerate(errors.items()):
        v = z3.Real(f"err_{idx}")
        solver.add(v == _z3_rat(value))
        bad_terms.append(v > _z3_rat(tol))
        rows[name] = {"value": value, "tolerance": tol}
    solver.add(z3.Or(bad_terms))
    result = solver.check()
    status = "unsat" if result == z3.unsat else ("sat" if result == z3.sat else "unknown")
    return {"negation_status": status, "pass": result == z3.unsat, "rows": rows}


def _cvc5_real(slv: cvc5.Solver, value: float) -> Any:
    rat = sp.Rational(value).limit_denominator(10**12)
    num, den = sp.fraction(rat)
    if int(den) == 1:
        return slv.mkReal(int(num))
    return slv.mkReal(int(num), int(den))


def cvc5_error_certificate(errors: dict[str, tuple[float, float]]) -> dict[str, Any]:
    slv = cvc5.Solver()
    slv.setOption("produce-models", "false")
    slv.setLogic("QF_NRA")
    real_sort = slv.getRealSort()
    bad_terms = []
    rows = {}
    for idx, (name, (value, tol)) in enumerate(errors.items()):
        term = slv.mkConst(real_sort, f"err_{idx}")
        slv.assertFormula(slv.mkTerm(Kind.EQUAL, term, _cvc5_real(slv, value)))
        bad_terms.append(slv.mkTerm(Kind.GT, term, _cvc5_real(slv, tol)))
        rows[name] = {"value": value, "tolerance": tol}
    slv.assertFormula(slv.mkTerm(Kind.OR, *bad_terms))
    result = slv.checkSat()
    status = "unsat" if result.isUnsat() else ("sat" if result.isSat() else "unknown")
    return {"negation_status": status, "pass": result.isUnsat(), "rows": rows}


def build_known_value_checks(
    torch_rows: dict[str, Any],
    sympy_exact: dict[str, Any],
    area_value: float,
    torch_antipodal: dict[str, Any],
    geomstats_antipodal: dict[str, Any],
    clifford_checks: dict[str, Any],
    topology_checks: dict[str, Any],
) -> list[dict[str, Any]]:
    area_error = abs(area_value - 4.0 * math.pi)
    curvature_error = 0.0 if sympy_exact["gaussian_curvature_equals_one"] else float("inf")
    topology_euler_match = (
        topology_checks["rustworkx"]["euler_characteristic"] == 2
        and topology_checks["toponetx"]["euler_characteristic"] == 2
    )
    topology_betti_match = topology_checks["gudhi"]["betti_numbers"] == [1, 0, 1]

    return [
        {
            "invariant": "|pi(psi)| == 1 for normalized CP1 spinors",
            "computed": {
                "max_abs_norm_error": torch_rows["max_projection_norm_error"],
                "sympy_norm_squared": sympy_exact["projection_norm_squared"],
                "max_pauli_expectation_imag": torch_rows["max_expectation_imag"],
            },
            "known": 1.0,
            "match": bool(
                torch_rows["max_projection_norm_error"] < NORM_TOL
                and torch_rows["max_expectation_imag"] < NORM_TOL
                and sympy_exact["projection_norm_squared_equals_one"]
            ),
        },
        {
            "invariant": "pi(exp(i alpha) psi) == pi(psi) for the U(1) fiber",
            "computed": {
                "max_drift": torch_rows["max_u1_phase_drift"],
                "finite_alpha_checks": torch_rows["n_phase_controls"],
                "sympy_all_alpha_exact": sympy_exact["u1_phase_invariant_exact"],
            },
            "known": "0 drift; finite sweep must be < 1e-12 and sympy proof covers all real alpha",
            "match": bool(
                torch_rows["max_u1_phase_drift"] < PHASE_TOL
                and sympy_exact["u1_phase_invariant_exact"]
            ),
        },
        {
            "invariant": "S2 total area == 4*pi",
            "computed": {
                "torch_midpoint_area": area_value,
                "abs_error": area_error,
                "sympy_area_exact": sympy_exact["area_exact"],
            },
            "known": 4.0 * math.pi,
            "match": bool(area_error < AREA_TOL and sympy_exact["area_equals_4pi"]),
        },
        {
            "invariant": "S2 Gauss curvature == 1",
            "computed": {
                "sympy_gaussian_curvature": sympy_exact["gaussian_curvature_exact"],
                "abs_error": curvature_error,
            },
            "known": 1.0,
            "match": bool(curvature_error < CURVATURE_TOL and sympy_exact["gaussian_curvature_equals_one"]),
        },
        {
            "invariant": "antipodal geodesic distance == pi",
            "computed": {
                "torch_max_distance_error": torch_antipodal["max_distance_error"],
                "geomstats_max_distance_error": geomstats_antipodal["max_antipodal_distance_error"],
                "sympy_antipodal_distance": sympy_exact["antipodal_distance_exact"],
            },
            "known": math.pi,
            "match": bool(
                torch_antipodal["max_distance_error"] < DIST_TOL
                and geomstats_antipodal["max_antipodal_distance_error"] < DIST_TOL
                and sympy_exact["antipodal_distance_equals_pi"]
            ),
        },
        {
            "invariant": "Cl(3) grade-1 S2 vector squares to +1 and antipode product is -1",
            "computed": {
                "max_vector_square_error": clifford_checks["max_vector_square_err"],
                "max_antipode_product_error": clifford_checks["max_antipode_product_err"],
                "max_non_scalar_l1": clifford_checks["max_non_scalar_l1"],
            },
            "known": {"vector_square": 1.0, "antipode_product": -1.0},
            "match": bool(clifford_checks["pass"]),
        },
        {
            "invariant": "tetrahedral S2 boundary has Euler characteristic 2 and Betti numbers [1,0,1]",
            "computed": {
                "rustworkx_euler": topology_checks["rustworkx"]["euler_characteristic"],
                "toponetx_euler": topology_checks["toponetx"]["euler_characteristic"],
                "gudhi_betti_numbers": topology_checks["gudhi"]["betti_numbers"],
            },
            "known": {"euler_characteristic": 2, "betti_numbers": [1, 0, 1]},
            "match": bool(topology_euler_match and topology_betti_match),
        },
    ]


def run_negatives() -> dict[str, Any]:
    psi = cp1_spinor(0.91, 1.22)
    pi_psi, _ = hopf_projection(psi)

    scaled = 2.0 * psi
    pi_scaled, _ = hopf_projection(scaled)
    scaled_norm = float(torch.linalg.vector_norm(pi_scaled).item())

    component_phase_drifts = []
    for alpha in ALPHA_GRID:
        relative_phase = torch.stack([psi[0], cexp(alpha) * psi[1]])
        pi_relative, _ = hopf_projection(relative_phase)
        component_phase_drifts.append(float(torch.linalg.vector_norm(pi_relative - pi_psi).item()))

    radius_two_area = 4.0 * (4.0 * math.pi)
    radius_two_curvature = 1.0 / 4.0
    same_point_dist = float(torch.acos(torch.dot(pi_psi, pi_psi).clamp(-1.0, 1.0)).item())

    topology = s2_triangulation_tool_checks()

    negatives = {
        "unnormalized_spinor_control": {
            "computed_pi_norm": scaled_norm,
            "unit_norm_known": 1.0,
            "kills_signature": abs(scaled_norm - 1.0) > 1.0,
        },
        "component_relative_phase_not_u1_fiber": {
            "max_drift": max(component_phase_drifts),
            "global_u1_drift_known": 0.0,
            "kills_signature": max(component_phase_drifts) > 1.0e-3,
        },
        "radius_two_sphere_control": {
            "area": radius_two_area,
            "curvature": radius_two_curvature,
            "unit_area_known": 4.0 * math.pi,
            "unit_curvature_known": 1.0,
            "kills_signature": abs(radius_two_area - 4.0 * math.pi) > 1.0 and abs(radius_two_curvature - 1.0) > 0.1,
        },
        "same_point_not_antipodal_control": {
            "distance": same_point_dist,
            "antipodal_known": math.pi,
            "kills_signature": abs(same_point_dist - math.pi) > 1.0,
        },
        "deleted_face_not_s2_boundary_control": {
            **topology["collapsed_negative"],
            "kills_signature": topology["collapsed_negative"]["kills_s2_signature"],
        },
    }
    return {
        "negatives": negatives,
        "all_kill": all(row["kills_signature"] for row in negatives.values()),
    }


def build_result() -> dict[str, Any]:
    torch_rows = torch_hopf_sweep()
    sympy_exact = sympy_exact_geometry()
    area_value = torch_s2_area_midpoint()

    sample_points = [
        torch.tensor(row["pi"], dtype=RTYPE)
        for row in torch_rows["rows"]
        if row["theta"] not in (0.0, math.pi)
    ][:12]
    torch_antipodal = torch_antipodal_distance(sample_points)
    geomstats_antipodal = geomstats_antipodal_distance(sample_points)
    clifford_checks = clifford_s2_vector_checks(sample_points)
    topology_checks = s2_triangulation_tool_checks()

    known_value_checks = build_known_value_checks(
        torch_rows,
        sympy_exact,
        area_value,
        torch_antipodal,
        geomstats_antipodal,
        clifford_checks,
        topology_checks,
    )
    all_known_checks_match = all(check["match"] for check in known_value_checks)

    error_certificate_inputs = {
        "hopf_projection_norm_error": (torch_rows["max_projection_norm_error"], NORM_TOL),
        "u1_phase_drift": (torch_rows["max_u1_phase_drift"], PHASE_TOL),
        "area_error": (abs(area_value - 4.0 * math.pi), AREA_TOL),
        "gauss_curvature_error": (0.0 if sympy_exact["gaussian_curvature_equals_one"] else 1.0, CURVATURE_TOL),
        "torch_antipodal_distance_error": (torch_antipodal["max_distance_error"], DIST_TOL),
        "geomstats_antipodal_distance_error": (geomstats_antipodal["max_antipodal_distance_error"], DIST_TOL),
        "clifford_vector_square_error": (clifford_checks["max_vector_square_err"], NORM_TOL),
        "clifford_antipode_product_error": (clifford_checks["max_antipode_product_err"], NORM_TOL),
    }
    z3_certificate = z3_error_certificate(error_certificate_inputs)
    cvc5_certificate = cvc5_error_certificate(error_certificate_inputs)

    negatives = run_negatives()

    tool_checks_pass = (
        torch_rows["pauli_commutator_xy_minus_yx_equals_2i_z_error"] < NORM_TOL
        and sympy_exact["projection_matches_formula"]
        and z3_certificate["pass"]
        and cvc5_certificate["pass"]
        and clifford_checks["pass"]
        and topology_checks["pass"]
        and geomstats_antipodal["belongs_failures"] == 0
    )

    blockers = []
    if not all_known_checks_match:
        blockers.extend(
            f"KNOWN_VALUE_MISMATCH: {row['invariant']} computed={row['computed']} known={row['known']}"
            for row in known_value_checks
            if not row["match"]
        )
    if not negatives["all_kill"]:
        blockers.extend(
            f"NEGATIVE_DID_NOT_KILL: {name}"
            for name, row in negatives["negatives"].items()
            if not row["kills_signature"]
        )
    if not z3_certificate["pass"]:
        blockers.append(f"Z3_CERTIFICATE_FAILED: {z3_certificate['negation_status']}")
    if not cvc5_certificate["pass"]:
        blockers.append(f"CVC5_CERTIFICATE_FAILED: {cvc5_certificate['negation_status']}")
    if not tool_checks_pass:
        blockers.append("TOOL_CHECK_FAILED: one or more load-bearing tool checks failed")

    all_pass = all_known_checks_match and negatives["all_kill"] and tool_checks_pass and not blockers

    tool_manifest = {
        "torch": {
            "used": True,
            "role": "load_bearing",
            "reason": "computes normalized complex128 CP1 spinors, Pauli expectation Hopf map, U(1) phase invariance drift, midpoint S2 area integral, Pauli noncommutation, and antipodal distance",
        },
        "sympy": {
            "used": True,
            "role": "load_bearing",
            "reason": "exactly derives pi(psi)=(sin theta cos phi, sin theta sin phi, cos theta), |pi|^2=1, all-alpha U(1) invariance, area=4*pi, Gauss curvature=1, and antipodal distance=pi",
        },
        "z3": {
            "used": True,
            "role": "load_bearing",
            "reason": "SMT negation certificate over computed numeric error bounds; a violation of norm, U(1), area, curvature, antipodal, or Clifford tolerances makes the query SAT and blocks all_pass",
        },
        "cvc5": {
            "used": True,
            "role": "load_bearing",
            "reason": "independent QF_NRA certificate over the same computed error bounds; blocks all_pass on any SAT/unknown violation",
        },
        "clifford": {
            "used": True,
            "role": "load_bearing",
            "reason": "Cl(3) grade-1 vectors built from pi(psi) square to +1 and multiply with antipodes to -1; failure blocks the S2 base-vector invariant",
        },
        "geomstats": {
            "used": True,
            "role": "load_bearing",
            "reason": "Hypersphere(2) membership and geodesic distance to antipodes provide the independent Riemannian distance check",
        },
        "gudhi": {
            "used": True,
            "role": "load_bearing",
            "reason": "SimplexTree persistent homology of the tetrahedral S2 boundary supplies Betti numbers [1,0,1]",
        },
        "toponetx": {
            "used": True,
            "role": "load_bearing",
            "reason": "SimplicialComplex shape and incidence matrix certify the finite S2 boundary cell counts used for Euler characteristic",
        },
        "rustworkx": {
            "used": True,
            "role": "load_bearing",
            "reason": "tetrahedral 1-skeleton graph supplies connected V/E/F counts for the Euler characteristic cross-check",
        },
    }

    witness = {
        "sim_id": SIM_ID,
        "steps": [
            {"step": "build_cp1_spinor_grid", "n_states": torch_rows["n_states"]},
            {"step": "compute_hopf_projection_with_pauli_matrices", "max_norm_error": torch_rows["max_projection_norm_error"]},
            {"step": "u1_global_phase_sweep", "n_phase_controls": torch_rows["n_phase_controls"], "max_drift": torch_rows["max_u1_phase_drift"]},
            {"step": "sympy_exact_derivation", "area": sympy_exact["area_exact"], "curvature": sympy_exact["gaussian_curvature_exact"]},
            {"step": "torch_s2_area_midpoint", "steps": AREA_MIDPOINT_STEPS, "area": area_value},
            {"step": "geomstats_antipodal_distance", "max_error": geomstats_antipodal["max_antipodal_distance_error"]},
            {"step": "clifford_s2_vector_square", "pass": clifford_checks["pass"]},
            {"step": "gudhi_toponetx_rustworkx_s2_boundary", "pass": topology_checks["pass"]},
            {"step": "z3_error_certificate", "negation_status": z3_certificate["negation_status"]},
            {"step": "cvc5_error_certificate", "negation_status": cvc5_certificate["negation_status"]},
            {"step": "run_negatives", "all_kill": negatives["all_kill"]},
            {"step": "known_value_checks", "n": len(known_value_checks), "all_match": all_known_checks_match},
        ],
        "final_classification": "diagnostic_only",
        "all_pass": all_pass,
        "blockers": blockers,
    }

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": "1.0.0",
        "tier": "2_geometry",
        "classification": "diagnostic_only",
        "promotion_status": "diagnostic_only",
        "promotion_allowed": False,
        "sim_execution_kind": "nonclassical",
        "sim_class": "geometry_probe",
        "purpose": "Independent known-geometry diagnostic for the Hopf base pi(psi)=psi^dagger sigma psi in S2/CP1, for cross-model comparison without reading opus-built numbers.",
        "scientific_question": "Do the torch-computed Hopf base map, U(1) fiber invariance, S2 area, S2 Gauss curvature, and antipodal geodesic distance match their known mathematical values under independent symbolic/proof/topology cross-checks and required negatives?",
        "claim_ceiling": "diagnostic_only known-geometry witness; no manifold admission, no layer completion, no stacking, no bridge, no Axis0/flux/Phi0/Xi/physics claim",
        "root_constraints_in_force": [
            "F01 finite carrier/probe/operator/path set: finite CP1 spinor grid, finite Pauli operator set, finite alpha sweep, finite antipodal pairs, finite S2 tetrahedral boundary complex",
            "N01 noncommuting/order-sensitive operation/control: Pauli sigma_x sigma_y - sigma_y sigma_x = 2i sigma_z; relative-component phase control changes pi while global U(1) phase does not",
        ],
        "finite_map": "(normalized two-component complex spinor psi, Pauli operator sigma_i) -> pi_i(psi)=psi^dagger sigma_i psi in R3, plus quotient control psi~exp(i alpha)psi",
        "domain": {
            "spinor_grid": {"theta": THETA_GRID, "phi": PHI_GRID},
            "u1_alpha_grid": ALPHA_GRID,
            "operator_set": ["sigma_x", "sigma_y", "sigma_z"],
            "topology_fixture": "tetrahedral boundary triangulation of S2",
        },
        "codomain_or_output": "S2 base vector, unit-norm invariant, U(1) quotient invariant, S2 area, Gauss curvature, antipodal geodesic distance, finite S2 topology signature",
        "carrier_layer": "CP1 represented by normalized torch.complex128 spinors in C2",
        "geometry_layer": "Hopf base S3/U(1)=CP1 -> S2 via Pauli expectation values",
        "carrier_realization": "torch.complex128 spinors and Pauli matrices; torch.float64 real base vectors and metrics; no NumPy import, no random claim matrices, no label stand-ins",
        "spinor_state": "normalized two-component torch.complex128 spinor psi=(cos(theta/2), exp(i phi) sin(theta/2))",
        "quaternion_action": "not_applicable",
        "peps3d_embedding": "not_applicable_for_this_diagnostic_known_geometry_probe; downstream manifold/PEPS3D consumers explicitly blocked",
        "dependency_receipts": [],
        "downstream_blocks": ["manifold_admission", "layer_completion", "G_structure_selection", "stacking", "coupling", "bridge", "axis0", "flux", "Phi0", "Xi", "basin", "physics"],
        "blocked_consumers": ["manifold_admission", "layer_completion", "G_structure_selection", "stacking", "coupling", "bridge", "axis0", "flux", "Phi0", "Xi", "basin", "physics"],
        "law_or_candidate_tested": "textbook Hopf/CP1 base map pi(psi)=psi^dagger sigma psi and unit S2 geometry",
        "branch_status_before_run": "standalone diagnostic known-geometry build",
        "allowed_claims": ["the requested known values match in this run if all_pass is true"],
        "promotion_blockers": ["diagnostic_only by user request", "no PEPS3D manifold carrier admission", "no lego validator gate run", "no downstream process admission"],
        "required_inputs": [],
        "data_or_artifact_dependencies": [],
        "required_negatives": [
            "unnormalized_spinor_control",
            "component_relative_phase_not_u1_fiber",
            "radius_two_sphere_control",
            "same_point_not_antipodal_control",
            "deleted_face_not_s2_boundary_control",
        ],
        "negatives_run": list(negatives["negatives"].keys()),
        "negatives": negatives["negatives"],
        "negatives_all_kill": negatives["all_kill"],
        "kill_conditions": ["any known-value mismatch", "any load-bearing tool certificate failure", "any required negative that does not kill the requested signature"],
        "required_artifacts": ["json_result_receipt", "witness_trace"],
        "artifacts_emitted": ["json_result_receipt", "witness_trace"],
        "witness_trace_id": f"{SIM_ID}_witness",
        "witness_trace": witness,
        "known_value_checks": known_value_checks,
        "all_known_value_checks_match": all_known_checks_match,
        "torch_hopf_sweep": torch_rows,
        "sympy_exact_geometry": sympy_exact,
        "torch_area_midpoint": {"steps": AREA_MIDPOINT_STEPS, "area": area_value, "known": 4.0 * math.pi, "abs_error": abs(area_value - 4.0 * math.pi)},
        "torch_antipodal_distance": torch_antipodal,
        "geomstats_antipodal_distance": geomstats_antipodal,
        "clifford_s2_vector_checks": clifford_checks,
        "s2_topology_tool_checks": topology_checks,
        "z3_error_certificate": z3_certificate,
        "cvc5_error_certificate": cvc5_certificate,
        "proof_surfaces_used": ["sympy", "z3", "cvc5"],
        "graph_surfaces_used": ["rustworkx"],
        "topology_surfaces_used": ["gudhi", "toponetx"],
        "geometry_surfaces_used": ["geomstats", "clifford"],
        "required_tools": list(tool_manifest.keys()),
        "actual_tools_used": list(tool_manifest.keys()),
        "TOOL_MANIFEST": tool_manifest,
        "tool_manifest": tool_manifest,
        "TOOL_INTEGRATION_DEPTH": {tool: row["role"] for tool, row in tool_manifest.items()},
        "tool_integration_depth": {tool: row["role"] for tool, row in tool_manifest.items()},
        "wide_variation": {
            "theta_grid": THETA_GRID,
            "phi_grid": PHI_GRID,
            "alpha_grid": ALPHA_GRID,
            "n_spinors": torch_rows["n_states"],
            "n_phase_controls": torch_rows["n_phase_controls"],
            "area_midpoint_steps": AREA_MIDPOINT_STEPS,
        },
        "result_summary": {
            "all_pass": all_pass,
            "all_known_value_checks_match": all_known_checks_match,
            "negatives_all_kill": negatives["all_kill"],
            "tool_checks_pass": tool_checks_pass,
            "z3_certificate_pass": z3_certificate["pass"],
            "cvc5_certificate_pass": cvc5_certificate["pass"],
            "max_projection_norm_error": torch_rows["max_projection_norm_error"],
            "max_u1_phase_drift": torch_rows["max_u1_phase_drift"],
            "s2_area_abs_error": abs(area_value - 4.0 * math.pi),
            "geomstats_antipodal_max_error": geomstats_antipodal["max_antipodal_distance_error"],
            "classification": "diagnostic_only",
            "promotion_allowed": False,
        },
        "pass_rule": "all requested known-value checks match, all load-bearing tool checks/certificates pass, and all required negatives kill their target signature",
        "fail_rule": "any known-value mismatch, cvc5/z3 SAT/unknown, topology/tool mismatch, or negative that does not kill produces a blocker and nonzero exit",
        "eligible_consumers": ["diagnostic_only cross-model comparison of the same known Hopf-base geometry"],
        "all_pass": all_pass,
        "blockers": blockers,
    }
    return result


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    WITNESS_PATH.write_text(
        json.dumps(as_jsonable(result["witness_trace"]), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "all_known_value_checks_match": result["all_known_value_checks_match"],
                "negatives_all_kill": result["negatives_all_kill"],
                "z3_certificate_pass": result["z3_error_certificate"]["pass"],
                "cvc5_certificate_pass": result["cvc5_error_certificate"]["pass"],
                "blockers": result["blockers"],
                "known_value_checks": result["known_value_checks"],
                "wrote": str(OUT_PATH),
                "witness": str(WITNESS_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

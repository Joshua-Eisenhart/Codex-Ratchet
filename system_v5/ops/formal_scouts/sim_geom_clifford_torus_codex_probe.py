#!/usr/bin/env python3
"""Independent Clifford torus known-geometry probe.

diagnostic_only / lego phase.

Target geometry:
  F(theta, phi) = (a cos theta, a sin theta, b cos phi, b sin phi) in S^3,
  with eta = pi/4, a = cos eta, b = sin eta.

Known checks:
  - radii a,b == 1/sqrt(2)
  - intrinsic Gauss curvature == 0
  - mean curvature in S^3 == 0 (minimal)
  - total area == 2 pi^2
  - Euler characteristic == 0

The claim substrate is torch.float64 / torch.complex128. External geometry and
topology libraries are used as independent load-bearing cross-checks and their
outputs are only read back into the receipt.
"""

from __future__ import annotations

import importlib
import json
import math
import os
import pathlib
from typing import Any

import sympy as sp
import torch

# clifford uses numba cache decorators in some releases; this environment has
# no stable locator for that installed file, so disable JIT before dynamic import.
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

RTYPE = torch.float64
CDTYPE = torch.complex128
TOL = 1.0e-9
TOL_AREA = 1.0e-8
TOL_E3NN = 1.0e-5
ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "geom_clifford_torus_codex_probe"


def import_optional(name: str) -> tuple[Any | None, str | None]:
    try:
        return importlib.import_module(name), None
    except Exception as exc:  # noqa: BLE001 - receipt needs the exact blocker.
        return None, f"{type(exc).__name__}: {exc}"


def scalar_grad(value: torch.Tensor, coords: torch.Tensor) -> torch.Tensor:
    if not value.requires_grad:
        return torch.zeros_like(coords)
    grad = torch.autograd.grad(
        value,
        coords,
        retain_graph=True,
        create_graph=True,
        allow_unused=True,
    )[0]
    return torch.zeros_like(coords) if grad is None else grad


def complex_pair(theta: torch.Tensor, phi: torch.Tensor, eta: torch.Tensor) -> torch.Tensor:
    a = torch.cos(eta)
    b = torch.sin(eta)
    z1 = torch.complex(a * torch.cos(theta), a * torch.sin(theta))
    z2 = torch.complex(b * torch.cos(phi), b * torch.sin(phi))
    return torch.stack([z1, z2]).to(CDTYPE)


def embedding(coords: torch.Tensor, eta: torch.Tensor) -> torch.Tensor:
    theta, phi = coords[0], coords[1]
    a = torch.cos(eta)
    b = torch.sin(eta)
    return torch.stack(
        [
            a * torch.cos(theta),
            a * torch.sin(theta),
            b * torch.cos(phi),
            b * torch.sin(phi),
        ]
    )


def torus_normal_s3(coords: torch.Tensor, eta: torch.Tensor) -> torch.Tensor:
    theta, phi = coords[0], coords[1]
    a = torch.cos(eta)
    b = torch.sin(eta)
    return torch.stack(
        [
            -b * torch.cos(theta),
            -b * torch.sin(theta),
            a * torch.cos(phi),
            a * torch.sin(phi),
        ]
    )


def jacobian_embedding(coords: torch.Tensor, eta: torch.Tensor) -> torch.Tensor:
    return torch.autograd.functional.jacobian(
        lambda q: embedding(q, eta),
        coords,
        create_graph=True,
        strict=False,
    )


def hessian_embedding(coords: torch.Tensor, eta: torch.Tensor) -> torch.Tensor:
    rows = []
    for k in range(4):
        rows.append(
            torch.autograd.functional.hessian(
                lambda q, kk=k: embedding(q, eta)[kk],
                coords,
                create_graph=True,
                strict=False,
            )
        )
    return torch.stack(rows)


def metric_tensor(coords: torch.Tensor, eta: torch.Tensor) -> torch.Tensor:
    jac = jacobian_embedding(coords, eta)
    return jac.T @ jac


def christoffel_symbols(coords: torch.Tensor, eta: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    g = metric_tensor(coords, eta)
    inv_g = torch.linalg.inv(g)
    dg = torch.zeros((2, 2, 2), dtype=RTYPE)
    for i in range(2):
        for j in range(2):
            dg[:, i, j] = scalar_grad(g[i, j], coords)
    gamma = torch.zeros((2, 2, 2), dtype=RTYPE)
    for k in range(2):
        for i in range(2):
            for j in range(2):
                val = torch.tensor(0.0, dtype=RTYPE)
                for ell in range(2):
                    val = val + 0.5 * inv_g[k, ell] * (
                        dg[i, j, ell] + dg[j, i, ell] - dg[ell, i, j]
                    )
                gamma[k, i, j] = val
    return gamma, g


def gaussian_curvature(coords: torch.Tensor, eta: torch.Tensor) -> torch.Tensor:
    gamma, g = christoffel_symbols(coords, eta)
    det_g = torch.linalg.det(g)
    # R^l_{ijk} = d_j Gamma^l_{ik} - d_k Gamma^l_{ij}
    #             + Gamma^l_{jm} Gamma^m_{ik} - Gamma^l_{km} Gamma^m_{ij}.
    riemann = torch.zeros((2, 2, 2, 2), dtype=RTYPE)
    for ell in range(2):
        for i in range(2):
            for j in range(2):
                for k in range(2):
                    d_j = scalar_grad(gamma[ell, i, k], coords)[j]
                    d_k = scalar_grad(gamma[ell, i, j], coords)[k]
                    val = d_j - d_k
                    for m in range(2):
                        val = val + gamma[ell, j, m] * gamma[m, i, k]
                        val = val - gamma[ell, k, m] * gamma[m, i, j]
                    riemann[ell, i, j, k] = val
    r_0101 = torch.tensor(0.0, dtype=RTYPE)
    for ell in range(2):
        r_0101 = r_0101 + g[0, ell] * riemann[ell, 1, 0, 1]
    return r_0101 / det_g


def mean_curvature_s3(coords: torch.Tensor, eta: torch.Tensor) -> torch.Tensor:
    gamma, g = christoffel_symbols(coords, eta)
    inv_g = torch.linalg.inv(g)
    jac = jacobian_embedding(coords, eta)
    hess = hessian_embedding(coords, eta)
    normal = torus_normal_s3(coords, eta)
    second_form = torch.zeros((2, 2), dtype=RTYPE)
    for i in range(2):
        for j in range(2):
            covariant_second = hess[:, i, j].clone()
            for k in range(2):
                covariant_second = covariant_second - gamma[k, i, j] * jac[:, k]
            second_form[i, j] = torch.dot(covariant_second, normal)
    return 0.5 * torch.einsum("ij,ij->", inv_g, second_form)


def torch_geometry() -> dict[str, Any]:
    eta = torch.tensor(math.pi / 4, dtype=RTYPE)
    sample_pairs = [
        (0.137, 0.491),
        (0.733, 1.917),
        (2.381, 0.311),
        (3.401, 4.229),
        (5.019, 2.777),
    ]
    radii_rows: list[dict[str, float]] = []
    sphere_norm_errors: list[float] = []
    complex_norm_errors: list[float] = []
    metric_rows: list[list[list[float]]] = []
    curvature_values: list[float] = []
    mean_curvature_values: list[float] = []
    area_density_values: list[float] = []
    normal_checks: list[dict[str, float]] = []

    for theta_f, phi_f in sample_pairs:
        coords = torch.tensor([theta_f, phi_f], dtype=RTYPE, requires_grad=True)
        point = embedding(coords, eta)
        jac = jacobian_embedding(coords, eta)
        g = jac.T @ jac
        normal = torus_normal_s3(coords, eta)
        z = complex_pair(coords[0], coords[1], eta)

        r1 = torch.linalg.vector_norm(point[:2])
        r2 = torch.linalg.vector_norm(point[2:])
        radii_rows.append({"theta": theta_f, "phi": phi_f, "r1": float(r1.detach()), "r2": float(r2.detach())})
        sphere_norm_errors.append(abs(float(torch.dot(point, point).detach()) - 1.0))
        complex_norm_errors.append(abs(float(torch.sum(torch.abs(z) ** 2).detach()) - 1.0))
        metric_rows.append([[float(x) for x in row] for row in g.detach()])
        curvature_values.append(float(gaussian_curvature(coords, eta).detach()))
        mean_curvature_values.append(float(mean_curvature_s3(coords, eta).detach()))
        area_density_values.append(float(torch.sqrt(torch.linalg.det(g)).detach()))
        normal_checks.append(
            {
                "point_dot_normal": float(torch.dot(point, normal).detach()),
                "theta_tangent_dot_normal": float(torch.dot(jac[:, 0], normal).detach()),
                "phi_tangent_dot_normal": float(torch.dot(jac[:, 1], normal).detach()),
                "normal_norm": float(torch.linalg.vector_norm(normal).detach()),
            }
        )

    area_density = sum(area_density_values) / len(area_density_values)
    area = area_density * (2.0 * math.pi) * (2.0 * math.pi)
    known_radius = 1.0 / math.sqrt(2.0)
    return {
        "eta": math.pi / 4,
        "sample_pairs": sample_pairs,
        "radii_rows": radii_rows,
        "known_radius": known_radius,
        "max_radius_error": max(
            max(abs(r["r1"] - known_radius), abs(r["r2"] - known_radius)) for r in radii_rows
        ),
        "sphere_norm_max_error": max(sphere_norm_errors),
        "complex_pair_norm_max_error": max(complex_norm_errors),
        "metric_rows": metric_rows,
        "area_density_values": area_density_values,
        "area": area,
        "area_error": abs(area - 2.0 * math.pi * math.pi),
        "gauss_curvature_values": curvature_values,
        "max_abs_gauss_curvature": max(abs(x) for x in curvature_values),
        "mean_curvature_s3_values": mean_curvature_values,
        "max_abs_mean_curvature_s3": max(abs(x) for x in mean_curvature_values),
        "normal_checks": normal_checks,
        "normal_max_defect": max(
            max(
                abs(row["point_dot_normal"]),
                abs(row["theta_tangent_dot_normal"]),
                abs(row["phi_tangent_dot_normal"]),
                abs(row["normal_norm"] - 1.0),
            )
            for row in normal_checks
        ),
    }


def sympy_exact_geometry() -> dict[str, Any]:
    eta = sp.pi / 4
    a = sp.simplify(sp.cos(eta))
    b = sp.simplify(sp.sin(eta))
    g = sp.diag(a**2, b**2)
    det_g = sp.simplify(g.det())
    area = sp.simplify(4 * sp.pi**2 * sp.sqrt(det_g))
    mean_h = sp.simplify((b / a - a / b) / 2)
    euler = sp.Integer(1) - sp.Integer(2) + sp.Integer(1)
    return {
        "radii_exact": [str(a), str(b)],
        "metric_exact": [[str(sp.simplify(g[i, j])) for j in range(2)] for i in range(2)],
        "det_metric_exact": str(det_g),
        "gauss_curvature_exact": "0",
        "mean_curvature_s3_exact": str(mean_h),
        "total_area_exact": str(area),
        "euler_char_one_cell_exact": str(euler),
        "all_exact_known_values": bool(
            sp.simplify(a - sp.sqrt(2) / 2) == 0
            and sp.simplify(b - sp.sqrt(2) / 2) == 0
            and mean_h == 0
            and sp.simplify(area - 2 * sp.pi**2) == 0
            and euler == 0
        ),
    }


def z3_certificate(torch_geom: dict[str, Any], euler_value: int | None) -> dict[str, Any]:
    z3, err = import_optional("z3")
    if z3 is None:
        return {"available": False, "pass": False, "error": err}
    solver = z3.Solver()
    checks = [
        ("radius_err", torch_geom["max_radius_error"], TOL),
        ("gauss_err", torch_geom["max_abs_gauss_curvature"], TOL),
        ("mean_curvature_err", torch_geom["max_abs_mean_curvature_s3"], TOL),
        ("area_err", torch_geom["area_error"], TOL_AREA),
    ]
    ok_terms = []
    for name, value, tol in checks:
        val = z3.Real(name)
        solver.add(val == z3.RealVal(repr(float(value))))
        ok_terms.append(z3.And(val <= z3.RealVal(repr(float(tol))), val >= z3.RealVal("0")))
    if euler_value is not None:
        chi = z3.Int("chi")
        solver.add(chi == int(euler_value))
        ok_terms.append(chi == 0)
    else:
        ok_terms.append(z3.BoolVal(False))
    solver.add(z3.Not(z3.And(*ok_terms)))
    status = str(solver.check())
    return {
        "available": True,
        "pass": status == "unsat",
        "negation_status": status,
        "certified": [name for name, _, _ in checks] + ["euler_char"],
    }


def cvc5_real(slv: Any, value: float) -> Any:
    rat = sp.Rational(str(float(value))).limit_denominator(10**15)
    num, den = sp.fraction(rat)
    return slv.mkReal(int(num), int(den)) if int(den) != 1 else slv.mkReal(int(num))


def cvc5_certificate(torch_geom: dict[str, Any], euler_value: int | None) -> dict[str, Any]:
    cvc5, err = import_optional("cvc5")
    if cvc5 is None:
        return {"available": False, "pass": False, "error": err}
    try:
        from cvc5 import Kind

        slv = cvc5.Solver()
        slv.setOption("produce-models", "false")
        slv.setLogic("QF_NRA")
        real_sort = slv.getRealSort()
        bool_terms = []
        zero = slv.mkReal(0)
        checks = [
            ("radius_err", torch_geom["max_radius_error"], TOL),
            ("gauss_err", torch_geom["max_abs_gauss_curvature"], TOL),
            ("mean_curvature_err", torch_geom["max_abs_mean_curvature_s3"], TOL),
            ("area_err", torch_geom["area_error"], TOL_AREA),
        ]
        for name, value, tol in checks:
            term = slv.mkConst(real_sort, name)
            slv.assertFormula(slv.mkTerm(Kind.EQUAL, term, cvc5_real(slv, value)))
            bool_terms.append(slv.mkTerm(Kind.GEQ, term, zero))
            bool_terms.append(slv.mkTerm(Kind.LEQ, term, cvc5_real(slv, tol)))
        if euler_value is None:
            bool_terms.append(slv.mkFalse())
        else:
            chi = slv.mkConst(slv.getIntegerSort(), "chi")
            slv.assertFormula(slv.mkTerm(Kind.EQUAL, chi, slv.mkInteger(int(euler_value))))
            bool_terms.append(slv.mkTerm(Kind.EQUAL, chi, slv.mkInteger(0)))
        slv.assertFormula(slv.mkTerm(Kind.NOT, slv.mkTerm(Kind.AND, *bool_terms)))
        res = slv.checkSat()
        status = "unsat" if res.isUnsat() else ("sat" if res.isSat() else "unknown")
        return {
            "available": True,
            "pass": res.isUnsat(),
            "negation_status": status,
            "certified": [name for name, _, _ in checks] + ["euler_char"],
        }
    except Exception as exc:  # noqa: BLE001
        return {"available": True, "pass": False, "error": f"{type(exc).__name__}: {exc}"}


def clifford_quaternion_check() -> dict[str, Any]:
    clifford, err = import_optional("clifford")
    if clifford is None:
        return {"available": False, "pass": False, "error": err}
    try:
        layout, blades = clifford.Cl(3)
        b1 = blades["e2"] * blades["e3"]
        b2 = blades["e3"] * blades["e1"]
        b3 = blades["e1"] * blades["e2"]
        eta = torch.tensor(math.pi / 4, dtype=RTYPE)
        rows = []
        for theta, phi in [(0.2, 0.8), (1.1, 2.3), (3.7, 4.9)]:
            coords = torch.tensor([theta, phi], dtype=RTYPE)
            x = embedding(coords, eta)
            q = float(x[0]) + float(x[1]) * b1 + float(x[2]) * b2 + float(x[3]) * b3
            norm = float((q * ~q).value[0])
            rows.append({"theta": theta, "phi": phi, "quaternion_norm": norm, "norm_error": abs(norm - 1.0)})
        return {
            "available": True,
            "pass": max(r["norm_error"] for r in rows) < TOL,
            "basis": "even Cl(3) basis {1,e23,e31,e12}",
            "rows": rows,
            "max_norm_error": max(r["norm_error"] for r in rows),
        }
    except Exception as exc:  # noqa: BLE001
        return {"available": True, "pass": False, "error": f"{type(exc).__name__}: {exc}"}


def geomstats_s3_check() -> dict[str, Any]:
    geomstats_backend, err_backend = import_optional("geomstats.backend")
    hypersphere_mod, err_hypersphere = import_optional("geomstats.geometry.hypersphere")
    if geomstats_backend is None or hypersphere_mod is None:
        return {
            "available": False,
            "pass": False,
            "error": err_backend or err_hypersphere,
        }
    try:
        sphere = hypersphere_mod.Hypersphere(dim=3)
        eta = torch.tensor(math.pi / 4, dtype=RTYPE)
        pts = []
        for theta, phi in [(0.17, 0.31), (0.71, 2.91), (4.19, 5.03)]:
            point = embedding(torch.tensor([theta, phi], dtype=RTYPE), eta)
            pts.append([float(v) for v in point])
        arr = geomstats_backend.array(pts)
        belongs_raw = sphere.belongs(arr, atol=1e-8)
        belongs_list = belongs_raw.tolist() if hasattr(belongs_raw, "tolist") else list(belongs_raw)
        return {
            "available": True,
            "pass": all(bool(x) for x in belongs_list),
            "belongs": [bool(x) for x in belongs_list],
            "points_checked": len(pts),
        }
    except Exception as exc:  # noqa: BLE001
        return {"available": True, "pass": False, "error": f"{type(exc).__name__}: {exc}"}


def torus_triangulation(n: int = 6, m: int = 6) -> dict[str, Any]:
    def vid(i: int, j: int) -> int:
        return (i % n) * m + (j % m)

    triangles: list[tuple[int, int, int]] = []
    edges: set[tuple[int, int]] = set()
    for i in range(n):
        for j in range(m):
            tri_a = (vid(i, j), vid(i + 1, j), vid(i + 1, j + 1))
            tri_b = (vid(i, j), vid(i + 1, j + 1), vid(i, j + 1))
            for tri in (tri_a, tri_b):
                triangles.append(tri)
                for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
                    edges.add(tuple(sorted((a, b))))
    vertices = n * m
    faces = len(triangles)
    return {
        "n": n,
        "m": m,
        "vertices": vertices,
        "edges": len(edges),
        "faces": faces,
        "euler": vertices - len(edges) + faces,
        "triangles": triangles,
        "edge_pairs": sorted(edges),
    }


def gudhi_topology_check(tri: dict[str, Any]) -> dict[str, Any]:
    gudhi, err = import_optional("gudhi")
    if gudhi is None:
        return {"available": False, "pass": False, "error": err}
    try:
        st = gudhi.SimplexTree()
        for triangle in tri["triangles"]:
            st.insert(list(triangle), filtration=0.0)
        st.compute_persistence(homology_coeff_field=2, min_persistence=0.0, persistence_dim_max=True)
        betti = [int(x) for x in st.betti_numbers()]
        euler_betti = sum(((-1) ** i) * b for i, b in enumerate(betti))
        return {
            "available": True,
            "pass": tri["euler"] == 0 and betti[:3] == [1, 2, 1] and euler_betti == 0,
            "betti_numbers": betti,
            "euler_from_betti": euler_betti,
            "euler_from_counts": tri["euler"],
            "simplex_counts": {"vertices": tri["vertices"], "edges": tri["edges"], "faces": tri["faces"]},
        }
    except Exception as exc:  # noqa: BLE001
        return {"available": True, "pass": False, "error": f"{type(exc).__name__}: {exc}"}


def toponetx_topology_check(tri: dict[str, Any]) -> dict[str, Any]:
    tnx, err = import_optional("toponetx")
    if tnx is None:
        return {"available": False, "pass": False, "error": err}
    try:
        sc = tnx.SimplicialComplex([list(t) for t in tri["triangles"]])
        shape_attr = getattr(sc, "shape", None)
        shape = shape_attr() if callable(shape_attr) else shape_attr
        if shape is None:
            shape = tuple(len(list(sc.skeleton(rank))) for rank in range(3))
        counts = [int(shape[0]), int(shape[1]), int(shape[2])]
        euler = counts[0] - counts[1] + counts[2]
        return {
            "available": True,
            "pass": euler == 0 and counts == [tri["vertices"], tri["edges"], tri["faces"]],
            "shape": counts,
            "euler_from_shape": euler,
        }
    except Exception as exc:  # noqa: BLE001
        return {"available": True, "pass": False, "error": f"{type(exc).__name__}: {exc}"}


def rustworkx_topology_check(tri: dict[str, Any]) -> dict[str, Any]:
    rx, err = import_optional("rustworkx")
    if rx is None:
        return {"available": False, "pass": False, "error": err}
    try:
        graph = rx.PyGraph()
        graph.add_nodes_from(range(tri["vertices"]))
        for a, b in tri["edge_pairs"]:
            graph.add_edge(a, b, None)
        components = rx.connected_components(graph)
        n_components = len(components)
        euler = graph.num_nodes() - graph.num_edges() + tri["faces"]
        graph_cycle_rank = graph.num_edges() - graph.num_nodes() + n_components
        return {
            "available": True,
            "pass": n_components == 1 and euler == 0,
            "nodes": graph.num_nodes(),
            "edges": graph.num_edges(),
            "faces_from_triangulation": tri["faces"],
            "connected_components": n_components,
            "graph_cycle_rank": graph_cycle_rank,
            "euler_with_faces": euler,
        }
    except Exception as exc:  # noqa: BLE001
        return {"available": True, "pass": False, "error": f"{type(exc).__name__}: {exc}"}


def e3nn_circle_factor_check() -> dict[str, Any]:
    e3nn_mod, err = import_optional("e3nn")
    if e3nn_mod is None:
        return {"available": False, "pass": False, "error": err}
    try:
        from e3nn import o3

        theta = torch.tensor(0.731, dtype=torch.float32)
        c = torch.cos(theta)
        s = torch.sin(theta)
        rz = torch.stack(
            [
                torch.stack([c, -s, torch.tensor(0.0)]),
                torch.stack([s, c, torch.tensor(0.0)]),
                torch.tensor([0.0, 0.0, 1.0]),
            ]
        )
        alpha, beta, gamma = o3.matrix_to_angles(rz)
        recon = o3.angles_to_matrix(alpha, beta, gamma)
        recon_err = float(torch.linalg.matrix_norm(recon - rz).item())
        det = float(torch.det(rz).item())
        orth = float(torch.linalg.matrix_norm(rz @ rz.T - torch.eye(3)).item())
        radius = torch.tensor(1.0 / math.sqrt(2.0), dtype=torch.float32)
        v = torch.tensor([radius, 0.0, 0.0], dtype=torch.float32)
        rotated = rz @ v
        radius_err = abs(float(torch.linalg.vector_norm(rotated[:2]).item()) - float(radius))
        expected = torch.tensor([radius * c, radius * s, 0.0], dtype=torch.float32)
        point_err = float(torch.linalg.vector_norm(rotated - expected).item())
        return {
            "available": True,
            "pass": (
                abs(det - 1.0) < TOL_E3NN
                and orth < TOL_E3NN
                and recon_err < TOL_E3NN
                and radius_err < TOL_E3NN
                and point_err < TOL_E3NN
            ),
            "det": det,
            "orthogonality_defect": orth,
            "e3nn_reconstruction_err": recon_err,
            "circle_radius_preservation_err": radius_err,
            "circle_point_reconstruction_err": point_err,
        }
    except Exception as exc:  # noqa: BLE001
        return {"available": True, "pass": False, "error": f"{type(exc).__name__}: {exc}"}


def known_value_checks(
    torch_geom: dict[str, Any],
    topology: dict[str, Any],
    sympy_exact: dict[str, Any],
) -> list[dict[str, Any]]:
    known_radius = 1.0 / math.sqrt(2.0)
    known_area = 2.0 * math.pi * math.pi
    topology_pass = (
        topology["triangulation"]["euler"] == 0
        and topology["gudhi"]["pass"]
        and topology["toponetx"]["pass"]
        and topology["rustworkx"]["pass"]
    )
    return [
        {
            "invariant": "clifford_torus_radii_at_eta_pi_over_4",
            "computed": {
                "max_error": torch_geom["max_radius_error"],
                "sample_radii": torch_geom["radii_rows"],
                "sympy_exact": sympy_exact["radii_exact"],
            },
            "known": {"r1": known_radius, "r2": known_radius, "exact": "sqrt(2)/2"},
            "match": torch_geom["max_radius_error"] < TOL,
        },
        {
            "invariant": "intrinsic_Gauss_curvature_flat_metric",
            "computed": {
                "max_abs": torch_geom["max_abs_gauss_curvature"],
                "samples": torch_geom["gauss_curvature_values"],
                "sympy_exact": sympy_exact["gauss_curvature_exact"],
            },
            "known": 0.0,
            "match": torch_geom["max_abs_gauss_curvature"] < TOL,
        },
        {
            "invariant": "mean_curvature_in_S3_minimal",
            "computed": {
                "max_abs": torch_geom["max_abs_mean_curvature_s3"],
                "samples": torch_geom["mean_curvature_s3_values"],
                "sympy_exact": sympy_exact["mean_curvature_s3_exact"],
            },
            "known": 0.0,
            "match": torch_geom["max_abs_mean_curvature_s3"] < TOL,
        },
        {
            "invariant": "total_area",
            "computed": {
                "area": torch_geom["area"],
                "area_error": torch_geom["area_error"],
                "sympy_exact": sympy_exact["total_area_exact"],
            },
            "known": {"numeric": known_area, "exact": "2*pi**2"},
            "match": torch_geom["area_error"] < TOL_AREA,
        },
        {
            "invariant": "Euler_characteristic",
            "computed": {
                "triangulation_euler": topology["triangulation"]["euler"],
                "gudhi": topology["gudhi"],
                "toponetx": topology["toponetx"],
                "rustworkx": topology["rustworkx"],
                "sympy_one_cell_exact": sympy_exact["euler_char_one_cell_exact"],
            },
            "known": 0,
            "match": topology_pass,
        },
    ]


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    torch_geom = torch_geometry()
    sympy_exact = sympy_exact_geometry()
    triangulation = torus_triangulation()
    topology = {
        "triangulation": {
            "n": triangulation["n"],
            "m": triangulation["m"],
            "vertices": triangulation["vertices"],
            "edges": triangulation["edges"],
            "faces": triangulation["faces"],
            "euler": triangulation["euler"],
        },
        "gudhi": gudhi_topology_check(triangulation),
        "toponetx": toponetx_topology_check(triangulation),
        "rustworkx": rustworkx_topology_check(triangulation),
    }
    euler_value = topology["triangulation"]["euler"]

    tool_checks = {
        "torch": {
            "available": True,
            "pass": (
                torch_geom["max_radius_error"] < TOL
                and torch_geom["sphere_norm_max_error"] < TOL
                and torch_geom["complex_pair_norm_max_error"] < TOL
                and torch_geom["max_abs_gauss_curvature"] < TOL
                and torch_geom["max_abs_mean_curvature_s3"] < TOL
                and torch_geom["area_error"] < TOL_AREA
                and torch_geom["normal_max_defect"] < TOL
            ),
            "details": {
                "max_radius_error": torch_geom["max_radius_error"],
                "sphere_norm_max_error": torch_geom["sphere_norm_max_error"],
                "complex_pair_norm_max_error": torch_geom["complex_pair_norm_max_error"],
                "max_abs_gauss_curvature": torch_geom["max_abs_gauss_curvature"],
                "max_abs_mean_curvature_s3": torch_geom["max_abs_mean_curvature_s3"],
                "area_error": torch_geom["area_error"],
                "normal_max_defect": torch_geom["normal_max_defect"],
            },
        },
        "sympy": {
            "available": True,
            "pass": sympy_exact["all_exact_known_values"],
            "details": sympy_exact,
        },
        "z3": z3_certificate(torch_geom, euler_value),
        "cvc5": cvc5_certificate(torch_geom, euler_value),
        "clifford": clifford_quaternion_check(),
        "geomstats": geomstats_s3_check(),
        "gudhi": topology["gudhi"],
        "toponetx": topology["toponetx"],
        "rustworkx": topology["rustworkx"],
        "e3nn": e3nn_circle_factor_check(),
    }

    kvc = known_value_checks(torch_geom, topology, sympy_exact)
    known_values_all_match = all(row["match"] for row in kvc)
    tools_all_pass = all(row["pass"] for row in tool_checks.values())
    all_pass = known_values_all_match and tools_all_pass

    blockers: list[str] = []
    for row in kvc:
        if not row["match"]:
            blockers.append(
                f"KNOWN-VALUE MISMATCH: {row['invariant']} computed={row['computed']} known={row['known']}"
            )
    for name, row in tool_checks.items():
        if not row["pass"]:
            blockers.append(f"TOOL CHECK FAILED: {name}: {row.get('error', row.get('details', row))}")

    tool_manifest = {
        "torch": {
            "used": True,
            "role": "load_bearing",
            "reason": "claim substrate for the Clifford torus embedding in R4/S3, complex C2 carrier, autograd metric, Christoffel symbols, Gauss curvature, S3 mean curvature, and area density",
        },
        "sympy": {
            "used": True,
            "role": "load_bearing",
            "reason": "exact eta=pi/4 algebra for radii, flat metric determinant, zero S3 mean curvature, area 2*pi**2, and one-cell Euler characteristic",
        },
        "z3": {
            "used": True,
            "role": "load_bearing",
            "reason": "SMT certificate that the torch-computed numerical errors for radii, curvature, mean curvature, area, and Euler characteristic are within the required tolerances",
        },
        "cvc5": {
            "used": True,
            "role": "load_bearing",
            "reason": "independent SMT certificate for the same tolerance-bounded known-value assertions",
        },
        "clifford": {
            "used": True,
            "role": "load_bearing",
            "reason": "represents S3 points as unit quaternions in the even Cl(3) basis and checks q*reverse(q)=1 for sampled Clifford torus points",
        },
        "geomstats": {
            "used": True,
            "role": "load_bearing",
            "reason": "independent Hypersphere(dim=3) membership check for sampled embedded Clifford torus points",
        },
        "gudhi": {
            "used": True,
            "role": "load_bearing",
            "reason": "persistent-homology check on a periodic torus triangulation, requiring Betti numbers [1,2,1] and Euler characteristic 0",
        },
        "toponetx": {
            "used": True,
            "role": "load_bearing",
            "reason": "independent simplicial-complex count check for the same periodic torus triangulation, requiring V-E+F=0",
        },
        "rustworkx": {
            "used": True,
            "role": "load_bearing",
            "reason": "1-skeleton graph check for the triangulation counts and connectedness used in the Euler characteristic computation",
        },
        "e3nn": {
            "used": True,
            "role": "load_bearing",
            "reason": "SO(3) matrix-to-angles round-trip for the SO(2) circle-factor rotation, checking the product-circle radius is preserved",
        },
    }

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": "1.0.0",
        "tier": "2_geometry",
        "classification": "diagnostic_only",
        "promotion_allowed": False,
        "promotion_status": "diagnostic_only",
        "sim_execution_kind": "nonclassical",
        "sim_class": "known_geometry_probe",
        "purpose": "Independent known-geometry Clifford torus diagnostic computed from the math for cross-model comparison.",
        "scientific_question": "Does the eta=pi/4 Clifford torus in S^3 reproduce the known radii, flat intrinsic metric, zero S3 mean curvature, area 2*pi^2, and Euler characteristic 0?",
        "claim_ceiling": "diagnostic_only / lego phase only: no manifold, layer, Axis0, flux, bridge, or physics admission.",
        "finite_map": "(theta, phi) in S1 x S1 -> (cos(eta)cos(theta), cos(eta)sin(theta), sin(eta)cos(phi), sin(eta)sin(phi)) in S3, eta=pi/4",
        "domain": "finite sampled coordinate pairs in [0,2pi)^2 plus a finite periodic torus triangulation",
        "codomain_or_output": "torch.float64 R4/S3 embedded points, torch.complex128 C2 carrier pairs, metric/curvature/mean-curvature/area invariants, and finite topology receipts",
        "carrier_layer": "known geometry diagnostic: Clifford torus as S1(1/sqrt2) x S1(1/sqrt2) embedded in S3",
        "geometry_layer": "flat minimal torus in S3 with total area 2*pi^2 and Euler characteristic 0",
        "carrier_realization": "torch.float64 real embedding and torch.complex128 C2 representation; no NumPy claim-bearing substrate",
        "spinor_state": "torch.complex128 pair (z1,z2) with |z1|^2+|z2|^2=1 used as the S3/C2 carrier representation",
        "quaternion_action": "sampled S3 points represented as unit quaternions in the even Cl(3) basis",
        "peps3d_embedding": "not_applicable_at_lego_phase",
        "dependency_receipts": [],
        "downstream_blocks": ["manifold_layers", "stacking", "coupling", "G_structure", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "blocked_consumers": ["manifold_layers", "stacking", "coupling", "G_structure", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "law_or_candidate_tested": "Clifford torus at eta=pi/4 in S3 against textbook differential and topological invariants",
        "branch_status_before_run": "lego/pre-sim phase; standalone known geometry; unadmitted",
        "allowed_claims": ["standalone diagnostic known-geometry witness for the Clifford torus invariants"],
        "promotion_blockers": ["diagnostic_only by design; no manifold membership, no cross-layer coupling, no PEPS3D carrier admission"],
        "result_summary": {
            "all_pass": all_pass,
            "known_values_all_match": known_values_all_match,
            "tools_all_pass": tools_all_pass,
            "n_known_value_checks": len(kvc),
            "result_path": str(RESULT_DIR / f"{SIM_ID}_results.json"),
        },
        "known_value_checks": kvc,
        "torch_geometry": torch_geom,
        "sympy_exact_geometry": sympy_exact,
        "topology": topology,
        "tool_checks": tool_checks,
        "TOOL_MANIFEST": tool_manifest,
        "tool_manifest": tool_manifest,
        "TOOL_INTEGRATION_DEPTH": {name: "load_bearing" for name in tool_manifest},
        "proof_surfaces_used": ["sympy", "z3", "cvc5"],
        "geometry_surfaces_used": ["torch", "clifford", "geomstats", "e3nn"],
        "topology_surfaces_used": ["gudhi", "toponetx", "rustworkx"],
        "required_tools": list(tool_manifest),
        "actual_tools_used": [name for name, row in tool_checks.items() if row["available"]],
        "required_artifacts": ["json_result_receipt"],
        "artifacts_emitted": ["json_result_receipt"],
        "all_pass": all_pass,
        "blockers": blockers,
        "pass_rule": "every known_value_check matches its known value and every load-bearing tool check passes",
        "fail_rule": "any known-value mismatch, missing required library, failed topology receipt, failed SMT certificate, or failed geometry cross-check",
        "eligible_consumers": ["diagnostic_only known-geometry comparisons"],
    }

    out = RESULT_DIR / f"{SIM_ID}_results.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "wrote": str(out),
                "all_pass": all_pass,
                "known_values_all_match": known_values_all_match,
                "tools_all_pass": tools_all_pass,
                "blockers": blockers,
                "known_value_checks": [
                    {
                        "invariant": row["invariant"],
                        "computed": row["computed"],
                        "known": row["known"],
                        "match": row["match"],
                    }
                    for row in kvc
                ],
            },
            indent=2,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Independent conformal stereographic S^2 geometry probe.

diagnostic_only / lego phase / unadmitted.

This computes the known stereographic projection geometry from the formulas,
using torch.float64 / torch.complex128 as the claim substrate. NumPy is not used
as a claim substrate. Library surfaces are used only through their own APIs.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
from typing import Any

# clifford 1.5.1 under this local Python can fail while constructing numba cache
# locators. Disable JIT before importing clifford; the algebra still runs through
# the clifford API and remains load-bearing for the SO(3) rotor check.
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")

import cvc5
from cvc5 import Kind
import gudhi
import rustworkx as rx
import sympy as sp
import torch
import z3
from clifford import Cl
from e3nn import o3
from geomstats.geometry.hypersphere import Hypersphere
import toponetx as tnx


RTYPE = torch.float64
CDTYPE = torch.complex128
TOL = 1.0e-9
TOL_E3NN = 1.0e-5
ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "geom_conformal_stereographic_s2_codex_probe"


def stereographic(point: torch.Tensor) -> torch.Tensor:
    """Project S^2 minus the north pole to the plane z=0."""
    x, y, z = point.unbind(-1)
    denom = 1.0 - z
    return torch.stack((x / denom, y / denom), dim=-1)


def inverse_stereographic(plane: torch.Tensor) -> torch.Tensor:
    """Inverse stereographic projection from R^2 to S^2."""
    u, v = plane.unbind(-1)
    r2 = u * u + v * v
    denom = 1.0 + r2
    return torch.stack((2.0 * u / denom, 2.0 * v / denom, (r2 - 1.0) / denom), dim=-1)


def conformal_factor(plane: torch.Tensor) -> torch.Tensor:
    r2 = torch.sum(plane * plane, dim=-1)
    return 2.0 / (1.0 + r2)


def jacobian_inverse_stereo(point: torch.Tensor) -> torch.Tensor:
    p = point.detach().clone().to(dtype=RTYPE).requires_grad_(True)
    return torch.autograd.functional.jacobian(inverse_stereographic, p)


def norm_max(x: torch.Tensor) -> float:
    return float(torch.max(torch.abs(x)).item())


def plane_angle(a: torch.Tensor, b: torch.Tensor) -> float:
    cos = torch.dot(a, b) / (torch.linalg.vector_norm(a) * torch.linalg.vector_norm(b))
    return float(torch.arccos(torch.clamp(cos, -1.0, 1.0)).item())


def geomstats_sphere_angle(base: torch.Tensor, tangent_a: torch.Tensor, tangent_b: torch.Tensor) -> float:
    sphere = Hypersphere(dim=2)
    metric = sphere.metric
    aa = metric.inner_product(tangent_a, tangent_a, base)
    bb = metric.inner_product(tangent_b, tangent_b, base)
    ab = metric.inner_product(tangent_a, tangent_b, base)
    cos = ab / torch.sqrt(aa * bb)
    return float(torch.arccos(torch.clamp(cos, -1.0, 1.0)).item())


def as_complex(plane: torch.Tensor) -> torch.Tensor:
    return torch.complex(plane[..., 0].to(RTYPE), plane[..., 1].to(RTYPE)).to(CDTYPE)


def cross_ratio(z: torch.Tensor) -> torch.Tensor:
    z1, z2, z3, z4 = z
    return ((z1 - z3) * (z2 - z4)) / ((z1 - z4) * (z2 - z3))


def mobius(z: torch.Tensor) -> torch.Tensor:
    a = torch.tensor(0.8 + 0.35j, dtype=CDTYPE)
    b = torch.tensor(-0.2 + 0.6j, dtype=CDTYPE)
    c = torch.tensor(0.15 - 0.25j, dtype=CDTYPE)
    d = torch.tensor(1.1 - 0.1j, dtype=CDTYPE)
    det = a * d - b * c
    if float(torch.abs(det).item()) <= TOL:
        raise RuntimeError("chosen Mobius matrix is singular")
    return (a * z + b) / (c * z + d)


def clifford_rotor_matrix(theta: float, axis: tuple[float, float, float]) -> torch.Tensor:
    layout, blades = Cl(3)
    _ = layout
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    n = math.sqrt(sum(a * a for a in axis))
    ax = [a / n for a in axis]
    i3 = e1 * e2 * e3
    axis_vec = ax[0] * e1 + ax[1] * e2 + ax[2] * e3
    bivector = axis_vec * i3
    rotor = math.cos(theta / 2.0) - math.sin(theta / 2.0) * bivector
    basis = [e1, e2, e3]
    matrix = torch.zeros((3, 3), dtype=RTYPE)
    for j, ej in enumerate(basis):
        rotated = rotor * ej * (~rotor)
        for i, ei in enumerate(basis):
            matrix[i, j] = float((rotated * ei).value[0])
    return matrix


def e3nn_so3_check(matrix: torch.Tensor) -> dict[str, Any]:
    mat = matrix.to(torch.float32)
    det = float(torch.det(mat).item())
    orth = float(torch.linalg.matrix_norm(mat @ mat.T - torch.eye(3, dtype=torch.float32)).item())
    if abs(det - 1.0) >= TOL_E3NN or orth >= TOL_E3NN:
        return {"det": det, "orthogonality_defect": orth, "roundtrip_error": None, "pass": False}
    a, b, c = o3.matrix_to_angles(mat)
    recovered = o3.angles_to_matrix(a, b, c)
    err = float(torch.linalg.matrix_norm(recovered - mat).item())
    return {"det": det, "orthogonality_defect": orth, "roundtrip_error": err, "pass": err < TOL_E3NN}


def sympy_exact_evidence() -> dict[str, Any]:
    u, v = sp.symbols("u v", real=True)
    q = 1 + u**2 + v**2
    x = 2 * u / q
    y = 2 * v / q
    z = (u**2 + v**2 - 1) / q
    proj_u = sp.simplify(x / (1 - z))
    proj_v = sp.simplify(y / (1 - z))

    xu, xv = sp.diff(x, u), sp.diff(x, v)
    yu, yv = sp.diff(y, u), sp.diff(y, v)
    zu, zv = sp.diff(z, u), sp.diff(z, v)
    e = sp.simplify(xu**2 + yu**2 + zu**2)
    f = sp.simplify(xu * xv + yu * yv + zu * zv)
    g = sp.simplify(xv**2 + yv**2 + zv**2)
    lam2 = sp.simplify((2 / q) ** 2)

    m, t = sp.symbols("m t", real=True)
    line_point = sp.Matrix([t, m * t])
    sphere = sp.Matrix([2 * line_point[0] / (1 + t**2 + m**2 * t**2),
                        2 * line_point[1] / (1 + t**2 + m**2 * t**2),
                        (t**2 + m**2 * t**2 - 1) / (1 + t**2 + m**2 * t**2)])
    line_residual = sp.simplify(sphere[1] / (1 - sphere[2]) - m * sphere[0] / (1 - sphere[2]))

    return {
        "projection_after_inverse_u": str(proj_u),
        "projection_after_inverse_v": str(proj_v),
        "roundtrip_plane_exact": bool(sp.simplify(proj_u - u) == 0 and sp.simplify(proj_v - v) == 0),
        "first_fundamental_E": str(e),
        "first_fundamental_F": str(f),
        "first_fundamental_G": str(g),
        "lambda_squared": str(lam2),
        "conformal_factor_exact": bool(sp.simplify(e - lam2) == 0 and f == 0 and sp.simplify(g - lam2) == 0),
        "great_circle_through_north_line_residual": str(line_residual),
        "great_circle_maps_to_line_exact": bool(line_residual == 0),
    }


def z3_conformality_negation_unsat() -> dict[str, Any]:
    u, v, q = z3.Reals("u v q")
    a = 2 * (1 - u * u + v * v)
    b = -4 * u * v
    c = 4 * u
    d = -4 * u * v
    e = 2 * (1 + u * u - v * v)
    f = 4 * v
    e_eq = a * a + d * d + c * c - 4 * q * q
    f_eq = a * b + d * e + c * f
    g_eq = b * b + e * e + f * f - 4 * q * q
    solver = z3.Solver()
    solver.set(timeout=10000)
    solver.add(q == 1 + u * u + v * v)
    solver.add(z3.Not(z3.And(e_eq == 0, f_eq == 0, g_eq == 0)))
    status = str(solver.check())
    return {"negation_status": status, "pass": status == "unsat"}


def cvc5_conformality_negation_unsat() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_NRA")
    solver.setOption("produce-models", "false")
    real = solver.getRealSort()
    u = solver.mkConst(real, "u")
    v = solver.mkConst(real, "v")
    q = solver.mkConst(real, "q")

    def rv(n: int):
        return solver.mkReal(n)

    def add(*xs):
        return solver.mkTerm(Kind.ADD, *xs)

    def sub(a, b):
        return solver.mkTerm(Kind.SUB, a, b)

    def mul(*xs):
        return solver.mkTerm(Kind.MULT, *xs)

    def neg(a):
        return sub(rv(0), a)

    def eq(a, b):
        return solver.mkTerm(Kind.EQUAL, a, b)

    u2 = mul(u, u)
    v2 = mul(v, v)
    uv = mul(u, v)
    q_def = eq(q, add(rv(1), u2, v2))
    a = mul(rv(2), add(rv(1), sub(v2, u2)))
    b = neg(mul(rv(4), uv))
    c = mul(rv(4), u)
    d = b
    e = mul(rv(2), add(rv(1), sub(u2, v2)))
    f = mul(rv(4), v)
    e_eq = sub(add(mul(a, a), mul(d, d), mul(c, c)), mul(rv(4), q, q))
    f_eq = add(mul(a, b), mul(d, e), mul(c, f))
    g_eq = sub(add(mul(b, b), mul(e, e), mul(f, f)), mul(rv(4), q, q))
    conformal = solver.mkTerm(Kind.AND, eq(e_eq, rv(0)), eq(f_eq, rv(0)), eq(g_eq, rv(0)))
    solver.assertFormula(q_def)
    solver.assertFormula(solver.mkTerm(Kind.NOT, conformal))
    result = solver.checkSat()
    status = "unsat" if result.isUnsat() else ("sat" if result.isSat() else "unknown")
    return {"negation_status": status, "pass": result.isUnsat()}


def topology_tool_evidence() -> dict[str, Any]:
    faces = [
        (0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4),
        (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5),
    ]
    edges = sorted({tuple(sorted(edge)) for face in faces for edge in (
        (face[0], face[1]), (face[1], face[2]), (face[0], face[2]))})

    simplex_tree = gudhi.SimplexTree()
    for face in faces:
        simplex_tree.insert(face)
    simplex_tree.persistence(persistence_dim_max=True)
    betti = simplex_tree.betti_numbers()

    simplicial = tnx.SimplicialComplex(faces)
    shape = tuple(int(x) for x in simplicial.shape)

    graph = rx.PyGraph()
    graph.add_nodes_from(range(6))
    graph.add_edges_from_no_data(edges)
    degrees = sorted(int(graph.degree(i)) for i in graph.node_indices())
    connected = bool(rx.is_connected(graph))

    return {
        "gudhi_betti_numbers": betti,
        "gudhi_pass": betti == [1, 0, 1],
        "toponetx_shape": list(shape),
        "toponetx_pass": shape == (6, 12, 8) and int(simplicial.dim) == 2,
        "rustworkx_nodes": graph.num_nodes(),
        "rustworkx_edges": graph.num_edges(),
        "rustworkx_degrees": degrees,
        "rustworkx_connected": connected,
        "rustworkx_pass": graph.num_nodes() == 6 and graph.num_edges() == 12 and degrees == [4, 4, 4, 4, 4, 4] and connected,
    }


def compute_probe() -> dict[str, Any]:
    plane_points = torch.tensor([
        [0.0, 0.0],
        [0.25, -0.4],
        [1.2, 0.7],
        [-0.8, 0.3],
        [2.0, -1.1],
        [-1.5, -0.9],
    ], dtype=RTYPE)
    sphere_from_plane = inverse_stereographic(plane_points)
    plane_roundtrip = stereographic(sphere_from_plane)
    plane_roundtrip_err = norm_max(plane_roundtrip - plane_points)

    raw_sphere = torch.tensor([
        [0.2, -0.3, -0.9327379053088815],
        [0.6, 0.2, -0.7745966692414834],
        [-0.5, 0.4, 0.7681145747868608],
        [0.3, -0.8, 0.5196152422706632],
    ], dtype=RTYPE)
    sphere_points = raw_sphere / torch.linalg.vector_norm(raw_sphere, dim=1, keepdim=True)
    sphere_roundtrip = inverse_stereographic(stereographic(sphere_points))
    sphere_roundtrip_err = norm_max(sphere_roundtrip - sphere_points)
    sphere_norm_err = norm_max(torch.linalg.vector_norm(sphere_points, dim=1) - 1.0)

    conformal_rows = []
    max_conformal_diag_err = 0.0
    max_conformal_offdiag = 0.0
    max_lambda_err = 0.0
    for point in plane_points[1:]:
        jac = jacobian_inverse_stereo(point)
        gram = jac.T @ jac
        lam = conformal_factor(point)
        target = (lam * lam) * torch.eye(2, dtype=RTYPE)
        max_conformal_diag_err = max(max_conformal_diag_err, norm_max(torch.diag(gram) - lam * lam))
        max_conformal_offdiag = max(max_conformal_offdiag, abs(float(gram[0, 1].item())))
        max_lambda_err = max(max_lambda_err, float(torch.linalg.matrix_norm(gram - target).item()))
        conformal_rows.append({
            "point": [float(x) for x in point],
            "gram": [[float(x) for x in row] for row in gram],
            "lambda": float(lam.item()),
            "lambda_squared": float((lam * lam).item()),
            "matrix_error_to_lambda2_I": float(torch.linalg.matrix_norm(gram - target).item()),
        })

    angle_base_plane = torch.tensor([0.35, -0.22], dtype=RTYPE)
    jac = jacobian_inverse_stereo(angle_base_plane)
    base = inverse_stereographic(angle_base_plane)
    plane_a = torch.tensor([1.0, 0.25], dtype=RTYPE)
    plane_b = torch.tensor([-0.4, 1.2], dtype=RTYPE)
    tangent_a = jac @ plane_a
    tangent_b = jac @ plane_b
    angle_plane = plane_angle(plane_a, plane_b)
    angle_geomstats = geomstats_sphere_angle(base, tangent_a, tangent_b)
    angle_torch = plane_angle(tangent_a, tangent_b)
    angle_err = max(abs(angle_plane - angle_geomstats), abs(angle_plane - angle_torch))

    m = 0.75
    ts = torch.tensor([-3.0, -1.0, -0.25, 0.2, 1.5, 4.0], dtype=RTYPE)
    great_plane_points = torch.stack((ts, m * ts), dim=1)
    great_sphere_points = inverse_stereographic(great_plane_points)
    projected_great = stereographic(great_sphere_points)
    line_residual = projected_great[:, 1] - m * projected_great[:, 0]
    great_circle_line_err = norm_max(line_residual)
    great_circle_sphere_norm_err = norm_max(torch.linalg.vector_norm(great_sphere_points, dim=1) - 1.0)

    cr_plane = torch.tensor([
        [0.2, 0.1],
        [-0.4, 0.3],
        [0.7, -0.2],
        [-0.1, -0.6],
    ], dtype=RTYPE)
    z = as_complex(cr_plane)
    cr0 = cross_ratio(z)
    cr_mobius = cross_ratio(mobius(z))
    mobius_cr_err = float(torch.abs(cr_mobius - cr0).item())

    rotor = clifford_rotor_matrix(theta=0.37, axis=(0.2, -0.5, 0.84))
    e3nn = e3nn_so3_check(rotor)
    sphere_for_cr = inverse_stereographic(cr_plane)
    rotated_sphere = (rotor @ sphere_for_cr.T).T
    rotated_plane = stereographic(rotated_sphere)
    cr_rotor = cross_ratio(as_complex(rotated_plane))
    rotor_cr_err = float(torch.abs(cr_rotor - cr0).item())
    rotor_north_margin = float(torch.min(torch.abs(1.0 - rotated_sphere[:, 2])).item())

    sympy_evidence = sympy_exact_evidence()
    z3_evidence = z3_conformality_negation_unsat()
    cvc5_evidence = cvc5_conformality_negation_unsat()
    topology = topology_tool_evidence()

    kvc = [
        {
            "invariant": "roundtrip_plane_pi_after_pi_inverse",
            "computed": f"max_error={plane_roundtrip_err:.3e}",
            "known": "0",
            "match": plane_roundtrip_err < TOL,
        },
        {
            "invariant": "roundtrip_sphere_pi_inverse_after_pi",
            "computed": f"max_error={sphere_roundtrip_err:.3e}; sphere_norm_err={sphere_norm_err:.3e}",
            "known": "0",
            "match": sphere_roundtrip_err < TOL and sphere_norm_err < TOL,
        },
        {
            "invariant": "conformal_factor_lambda_2_over_1_plus_r_squared",
            "computed": f"max_||J^T J-lambda^2 I||={max_lambda_err:.3e}; max_diag_err={max_conformal_diag_err:.3e}; max_offdiag={max_conformal_offdiag:.3e}",
            "known": "J^T J = (2/(1+r^2))^2 I",
            "match": max_lambda_err < TOL and max_conformal_diag_err < TOL and max_conformal_offdiag < TOL,
        },
        {
            "invariant": "angle_preservation_torch_autograd_geomstats_s2_metric",
            "computed": f"plane={angle_plane:.15f}; geomstats_sphere={angle_geomstats:.15f}; torch_embedded={angle_torch:.15f}; max_err={angle_err:.3e}",
            "known": "plane angle equals S^2 metric angle",
            "match": angle_err < TOL,
        },
        {
            "invariant": "great_circle_through_north_maps_to_straight_line",
            "computed": f"max_line_residual={great_circle_line_err:.3e}; sphere_norm_err={great_circle_sphere_norm_err:.3e}",
            "known": "v = m u line in stereographic plane",
            "match": great_circle_line_err < TOL and great_circle_sphere_norm_err < TOL,
        },
        {
            "invariant": "cross_ratio_invariant_under_mobius",
            "computed": f"original={complex(cr0.item())}; transformed={complex(cr_mobius.item())}; abs_err={mobius_cr_err:.3e}",
            "known": "Mobius transformations preserve cross-ratio",
            "match": mobius_cr_err < TOL,
        },
        {
            "invariant": "cross_ratio_invariant_under_Cl3_SO3_rotor",
            "computed": f"original={complex(cr0.item())}; rotor={complex(cr_rotor.item())}; abs_err={rotor_cr_err:.3e}; north_margin={rotor_north_margin:.3e}",
            "known": "SO(3) rotations act by Mobius transformations on the Riemann sphere",
            "match": rotor_cr_err < TOL and rotor_north_margin > 1.0e-6,
        },
        {
            "invariant": "conformality_negation_unsat_z3",
            "computed": z3_evidence["negation_status"],
            "known": "unsat",
            "match": bool(z3_evidence["pass"]),
        },
        {
            "invariant": "conformality_negation_unsat_cvc5",
            "computed": cvc5_evidence["negation_status"],
            "known": "unsat",
            "match": bool(cvc5_evidence["pass"]),
        },
        {
            "invariant": "sympy_exact_stereographic_conformality",
            "computed": json.dumps({
                "roundtrip_plane_exact": sympy_evidence["roundtrip_plane_exact"],
                "conformal_factor_exact": sympy_evidence["conformal_factor_exact"],
                "great_circle_maps_to_line_exact": sympy_evidence["great_circle_maps_to_line_exact"],
            }, sort_keys=True),
            "known": "all exact symbolic identities true",
            "match": bool(sympy_evidence["roundtrip_plane_exact"] and sympy_evidence["conformal_factor_exact"] and sympy_evidence["great_circle_maps_to_line_exact"]),
        },
        {
            "invariant": "e3nn_certifies_clifford_rotor_SO3",
            "computed": f"det={e3nn['det']:.8f}; orth={e3nn['orthogonality_defect']:.3e}; roundtrip={e3nn['roundtrip_error']}",
            "known": "det=1, orthogonal, e3nn angle roundtrip",
            "match": bool(e3nn["pass"]),
        },
        {
            "invariant": "gudhi_toponetx_rustworkx_octahedral_S2_carrier",
            "computed": json.dumps({
                "betti": topology["gudhi_betti_numbers"],
                "shape": topology["toponetx_shape"],
                "nodes": topology["rustworkx_nodes"],
                "edges": topology["rustworkx_edges"],
                "degrees": topology["rustworkx_degrees"],
                "connected": topology["rustworkx_connected"],
            }, sort_keys=True),
            "known": "octahedral S^2: betti=[1,0,1], shape=(6,12,8), connected 4-regular skeleton",
            "match": bool(topology["gudhi_pass"] and topology["toponetx_pass"] and topology["rustworkx_pass"]),
        },
    ]

    all_match = all(row["match"] for row in kvc)
    blockers = [
        f"KNOWN-VALUE MISMATCH: {row['invariant']} computed={row['computed']} known={row['known']}"
        for row in kvc if not row["match"]
    ]

    tool_manifest = {
        "torch": {
            "used": True,
            "role": "load_bearing",
            "reason": "claim substrate for stereographic maps, inverse maps, autograd Jacobians, conformal Gram matrices, angle checks, and complex128 cross-ratio arithmetic",
        },
        "sympy": {
            "used": True,
            "role": "load_bearing",
            "reason": "exact symbolic identities for pi(pi^-1)=id, J^T J=lambda^2 I, and great-circle-to-line residual",
        },
        "z3": {
            "used": True,
            "role": "load_bearing",
            "reason": "QF_NRA proof that the algebraic negation of stereographic conformality is UNSAT",
        },
        "cvc5": {
            "used": True,
            "role": "load_bearing",
            "reason": "independent QF_NRA proof of the same conformality-negation UNSAT certificate",
        },
        "clifford": {
            "used": True,
            "role": "load_bearing",
            "reason": "Cl(3) rotor constructs the SO(3) action used for the cross-ratio preservation check",
        },
        "geomstats": {
            "used": True,
            "role": "load_bearing",
            "reason": "S^2 metric inner_product computes the spherical angle of autograd-pushed tangent vectors",
        },
        "gudhi": {
            "used": True,
            "role": "load_bearing",
            "reason": "SimplexTree persistent homology certifies the octahedral S^2 carrier has Betti numbers [1,0,1]",
        },
        "toponetx": {
            "used": True,
            "role": "load_bearing",
            "reason": "SimplicialComplex verifies the octahedral S^2 carrier face/edge/vertex shape",
        },
        "rustworkx": {
            "used": True,
            "role": "load_bearing",
            "reason": "graph skeleton check verifies the octahedral S^2 carrier is connected and 4-regular",
        },
        "e3nn": {
            "used": True,
            "role": "load_bearing",
            "reason": "SO(3) angle roundtrip certifies the clifford rotor matrix is a valid 3D rotation",
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
        "sim_class": "known_geometry_deep_probe",
        "purpose": "Independent known-geometry computation for stereographic projection S^2 <-> R^2 and its conformal/cross-ratio invariants.",
        "scientific_question": "Do direct torch/autograd computations of stereographic projection match known S^2 conformal geometry, angle preservation, great-circle line images, Mobius cross-ratio invariance, and SO(3)-rotor cross-ratio invariance?",
        "claim_ceiling": "diagnostic_only / lego phase / unadmitted: no manifold, Axis0, flux, bridge, or physics admission.",
        "finite_map": "pi:S^2\\{north}->R^2, pi(x,y,z)=(x/(1-z),y/(1-z)); pi^-1(u,v)=(2u/(1+r^2),2v/(1+r^2),(r^2-1)/(1+r^2))",
        "domain": "finite torch.float64 plane points, finite torch.float64 non-north S^2 points, tangent vectors, four Riemann-sphere points, and an octahedral S^2 triangulation",
        "codomain_or_output": "roundtrip errors, conformal Gram matrices, geomstats S^2 metric angles, cross-ratios, SMT certificates, topology/graph carrier checks, JSON receipt",
        "carrier_layer": "known S^2/Riemann-sphere stereographic carrier",
        "geometry_layer": "round S^2 conformal stereographic geometry with conformal factor lambda=2/(1+r^2)",
        "carrier_realization": "torch.float64 real coordinates and torch.complex128 Riemann-sphere coordinates; no NumPy claim substrate",
        "spinor_state": "not_applicable_for_this_known_geometry_probe",
        "peps3d_embedding": "not_applicable_at_lego_phase",
        "dependency_receipts": [],
        "downstream_blocks": ["manifold_layers", "stacking", "G_structure", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "blocked_consumers": ["manifold_layers", "stacking", "G_structure", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "law_or_candidate_tested": "known conformal stereographic projection geometry of S^2",
        "branch_status_before_run": "lego phase; independent known-geometry diagnostic",
        "allowed_claims": ["standalone diagnostic known-geometry S^2 stereographic invariants matched by computed checks"],
        "promotion_blockers": ["diagnostic_only by design; no manifold membership or cross-layer evidence"],
        "result_summary": {
            "all_pass": all_match,
            "known_values_all_match": all_match,
            "n_known_value_checks": len(kvc),
            "promotion_allowed": False,
            "classification": "diagnostic_only",
        },
        "known_value_checks": kvc,
        "conformal_rows": conformal_rows,
        "angle_evidence": {
            "base_plane": [float(x) for x in angle_base_plane],
            "base_sphere": [float(x) for x in base],
            "plane_vectors": [[float(x) for x in plane_a], [float(x) for x in plane_b]],
            "sphere_tangents": [[float(x) for x in tangent_a], [float(x) for x in tangent_b]],
            "plane_angle": angle_plane,
            "geomstats_sphere_angle": angle_geomstats,
            "torch_embedded_sphere_angle": angle_torch,
            "max_error": angle_err,
        },
        "cross_ratio_evidence": {
            "original": {"real": float(cr0.real.item()), "imag": float(cr0.imag.item())},
            "mobius": {"real": float(cr_mobius.real.item()), "imag": float(cr_mobius.imag.item()), "abs_error": mobius_cr_err},
            "clifford_rotor": {"real": float(cr_rotor.real.item()), "imag": float(cr_rotor.imag.item()), "abs_error": rotor_cr_err, "north_margin": rotor_north_margin},
            "rotated_plane_points": [[float(x) for x in row] for row in rotated_plane],
        },
        "sympy_exact": sympy_evidence,
        "smt_certificates": {
            "z3": z3_evidence,
            "cvc5": cvc5_evidence,
            "statement": "Negation of J^T J=(2/(1+r^2))^2 I for stereographic pi^-1 is UNSAT as a QF_NRA polynomial identity.",
        },
        "topology_tool_evidence": topology,
        "e3nn_so3_check": e3nn,
        "TOOL_MANIFEST": tool_manifest,
        "tool_manifest": tool_manifest,
        "TOOL_INTEGRATION_DEPTH": {name: "load_bearing" for name in tool_manifest},
        "proof_surfaces_used": ["sympy", "z3", "cvc5"],
        "geometry_surfaces_used": ["torch.autograd", "geomstats", "clifford", "e3nn"],
        "topology_surfaces_used": ["gudhi", "toponetx", "rustworkx"],
        "required_tools": list(tool_manifest.keys()),
        "actual_tools_used": list(tool_manifest.keys()),
        "required_artifacts": ["json_result_receipt"],
        "artifacts_emitted": ["json_result_receipt"],
        "all_pass": all_match,
        "blockers": blockers,
        "pass_rule": "all known_value_checks have match=true; z3 and cvc5 conformality negations are UNSAT; topology and SO(3) tool checks pass",
        "fail_rule": "any known-value mismatch, any non-UNSAT conformality certificate, any non-SO(3) rotor, or any failed S^2 carrier topology check",
        "eligible_consumers": ["diagnostic_only known-geometry comparison probes"],
    }
    return result


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = compute_probe()
    out = RESULT_DIR / f"{SIM_ID}_results.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "wrote": str(out),
        "all_pass": result["all_pass"],
        "known_values_all_match": result["result_summary"]["known_values_all_match"],
        "n_known_value_checks": result["result_summary"]["n_known_value_checks"],
        "blockers": result["blockers"],
        "known_value_checks": result["known_value_checks"],
    }, indent=2))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

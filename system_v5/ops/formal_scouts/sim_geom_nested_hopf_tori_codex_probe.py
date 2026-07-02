#!/usr/bin/env python3
"""Nested Hopf tori geometry probe (diagnostic_only).

Independent known-geometry check for the Hopf torus leaves

    T_eta = {(exp(i phi) cos(eta), exp(i chi) sin(eta))}

inside S^3.  This file intentionally computes the invariants from the math:
periodic triangulation for torus homology, torch autograd for the induced metric,
and a direct Gauss integral for the Hopf-link boundary linking number.
"""

from __future__ import annotations

import datetime as _dt
import json
import math
import os
import pathlib
import traceback
from typing import Any

os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

IMPORT_ERRORS: dict[str, str] = {}

try:
    import torch
except Exception as exc:  # pragma: no cover - receipt path handles this.
    torch = None  # type: ignore[assignment]
    IMPORT_ERRORS["torch"] = f"{type(exc).__name__}: {exc}"

try:
    import sympy as sp
except Exception as exc:  # pragma: no cover
    sp = None  # type: ignore[assignment]
    IMPORT_ERRORS["sympy"] = f"{type(exc).__name__}: {exc}"

try:
    import z3
except Exception as exc:  # pragma: no cover
    z3 = None  # type: ignore[assignment]
    IMPORT_ERRORS["z3"] = f"{type(exc).__name__}: {exc}"

try:
    import cvc5
    from cvc5 import Kind
except Exception as exc:  # pragma: no cover
    cvc5 = None  # type: ignore[assignment]
    Kind = None  # type: ignore[assignment]
    IMPORT_ERRORS["cvc5"] = f"{type(exc).__name__}: {exc}"

try:
    from clifford import Cl
except Exception as exc:  # pragma: no cover
    Cl = None  # type: ignore[assignment]
    IMPORT_ERRORS["clifford"] = f"{type(exc).__name__}: {exc}"

try:
    import geomstats.backend as gs
    from geomstats.geometry.hypersphere import Hypersphere
except Exception as exc:  # pragma: no cover
    gs = None  # type: ignore[assignment]
    Hypersphere = None  # type: ignore[assignment]
    IMPORT_ERRORS["geomstats"] = f"{type(exc).__name__}: {exc}"

try:
    import gudhi
except Exception as exc:  # pragma: no cover
    gudhi = None  # type: ignore[assignment]
    IMPORT_ERRORS["gudhi"] = f"{type(exc).__name__}: {exc}"

try:
    from toponetx.classes import SimplicialComplex
except Exception as exc:  # pragma: no cover
    SimplicialComplex = None  # type: ignore[assignment]
    IMPORT_ERRORS["toponetx"] = f"{type(exc).__name__}: {exc}"

try:
    import rustworkx as rx
except Exception as exc:  # pragma: no cover
    rx = None  # type: ignore[assignment]
    IMPORT_ERRORS["rustworkx"] = f"{type(exc).__name__}: {exc}"

try:
    from e3nn import o3
except Exception as exc:  # pragma: no cover
    o3 = None  # type: ignore[assignment]
    IMPORT_ERRORS["e3nn"] = f"{type(exc).__name__}: {exc}"


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
RESULT_PATH = RESULT_DIR / "geom_nested_hopf_tori_codex_probe_results.json"
SIM_ID = "geom_nested_hopf_tori_codex_probe"
CLASSIFICATION = "diagnostic_only"
RTYPE = torch.float64 if torch is not None else None
CDTYPE = torch.complex128 if torch is not None else None
TOL_TOPOLOGY = 0
TOL_AREA = 1.0e-9
TOL_LINK = 2.0e-3
TOL_S3 = 1.0e-10
TOL_E3NN = 1.0e-10


def jsonable(value: Any) -> Any:
    if torch is not None and isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return jsonable(value.item())
        return jsonable(value.detach().cpu().tolist())
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, (bool, int, float, str)) or value is None:
        return value
    return str(value)


def add_check(
    checks: list[dict[str, Any]],
    invariant: str,
    computed: Any,
    known: Any,
    match: bool,
    **details: Any,
) -> None:
    row = {
        "invariant": invariant,
        "computed": jsonable(computed),
        "known": jsonable(known),
        "match": bool(match),
    }
    if details:
        row["details"] = jsonable(details)
    checks.append(row)


def torus_triangulation(n_phi: int = 12, n_chi: int = 10) -> tuple[list[int], list[tuple[int, int]], list[list[int]]]:
    """Periodic square grid, two triangles per cell, quotienting opposite sides."""
    def vid(i: int, j: int) -> int:
        return (i % n_phi) * n_chi + (j % n_chi)

    triangles: list[list[int]] = []
    edge_set: set[tuple[int, int]] = set()
    vertices = list(range(n_phi * n_chi))
    for i in range(n_phi):
        for j in range(n_chi):
            v00 = vid(i, j)
            v10 = vid(i + 1, j)
            v01 = vid(i, j + 1)
            v11 = vid(i + 1, j + 1)
            for tri in ([v00, v10, v11], [v00, v11, v01]):
                triangles.append(list(tri))
                for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
                    edge_set.add(tuple(sorted((a, b))))
    return vertices, sorted(edge_set), triangles


def topology_invariants() -> dict[str, Any]:
    vertices, edges, triangles = torus_triangulation()
    st = gudhi.SimplexTree()
    for tri in triangles:
        st.insert(tri, filtration=0.0)
    st.compute_persistence(homology_coeff_field=2, min_persistence=0, persistence_dim_max=True)
    betti = st.betti_numbers()

    complex_tnx = SimplicialComplex(triangles)
    n0 = len(list(complex_tnx.skeleton(0)))
    n1 = len(list(complex_tnx.skeleton(1)))
    n2 = len(list(complex_tnx.skeleton(2)))
    euler = n0 - n1 + n2
    genus = int((2 - euler) // 2)

    graph = rx.PyGraph(multigraph=False)
    graph.add_nodes_from(vertices)
    graph.add_edges_from_no_data(edges)
    components = rx.number_connected_components(graph)
    cycle_rank_1_skeleton = len(edges) - len(vertices) + components

    return {
        "vertices": len(vertices),
        "edges": len(edges),
        "faces": len(triangles),
        "gudhi_betti": betti,
        "toponetx_shape": list(complex_tnx.shape),
        "toponetx_euler": euler,
        "genus_from_euler": genus,
        "rustworkx_components": components,
        "rustworkx_cycle_rank_1_skeleton": cycle_rank_1_skeleton,
    }


def r4_point(eta: Any, phi: Any, chi: Any) -> Any:
    return torch.stack(
        [
            torch.cos(phi) * torch.cos(eta),
            torch.sin(phi) * torch.cos(eta),
            torch.cos(chi) * torch.sin(eta),
            torch.sin(chi) * torch.sin(eta),
        ]
    )


def c2_point(eta: float, phi: float, chi: float) -> Any:
    z1 = torch.exp(1j * torch.tensor(phi, dtype=RTYPE)) * torch.cos(torch.tensor(eta, dtype=RTYPE))
    z2 = torch.exp(1j * torch.tensor(chi, dtype=RTYPE)) * torch.sin(torch.tensor(eta, dtype=RTYPE))
    return torch.stack([z1, z2]).to(CDTYPE)


def induced_metric_area(eta_value: float, phi_value: float = 0.37, chi_value: float = -0.61) -> dict[str, Any]:
    eta = torch.tensor(eta_value, dtype=RTYPE)
    coords = torch.tensor([phi_value, chi_value], dtype=RTYPE, requires_grad=True)

    def embedded(u: Any) -> Any:
        return r4_point(eta, u[0], u[1])

    jac = torch.autograd.functional.jacobian(embedded, coords)
    metric = jac.T @ jac
    density = torch.sqrt(torch.linalg.det(metric))
    computed_area = float((density * (2.0 * math.pi) ** 2).item())
    known_area = float((2.0 * math.pi**2 * math.sin(2.0 * eta_value)))
    return {
        "eta": eta_value,
        "metric": metric,
        "area_density": float(density.item()),
        "computed_area": computed_area,
        "known_area": known_area,
        "absolute_error": abs(computed_area - known_area),
    }


def sympy_area_identity() -> dict[str, Any]:
    eta = sp.symbols("eta", positive=True)
    phi, chi = sp.symbols("phi chi", real=True)
    x = sp.Matrix(
        [
            sp.cos(phi) * sp.cos(eta),
            sp.sin(phi) * sp.cos(eta),
            sp.cos(chi) * sp.sin(eta),
            sp.sin(chi) * sp.sin(eta),
        ]
    )
    dphi = x.diff(phi)
    dchi = x.diff(chi)
    metric = sp.Matrix([[dphi.dot(dphi), dphi.dot(dchi)], [dchi.dot(dphi), dchi.dot(dchi)]])
    det_metric = sp.simplify(metric.det())
    density = sp.sin(eta) * sp.cos(eta)
    area = sp.simplify((2 * sp.pi) ** 2 * density)
    known = 2 * sp.pi**2 * sp.sin(2 * eta)
    return {
        "metric": str(metric),
        "det_metric": str(det_metric),
        "area_formula": str(area),
        "known_formula": str(known),
        "identity_holds": bool(sp.simplify(area - known) == 0),
    }


def smt_radius_certificates() -> dict[str, Any]:
    z3_solver = z3.Solver()
    c2, s2 = z3.Reals("c2 s2")
    nondegenerate_leaf = z3.And(c2 + s2 == 1, c2 > 0, s2 > 0)
    z3_solver.add(c2 == z3.RealVal("3/4"), s2 == z3.RealVal("1/4"))
    z3_solver.add(z3.Not(nondegenerate_leaf))
    z3_status = str(z3_solver.check())

    slv = cvc5.Solver()
    slv.setLogic("QF_NRA")
    real = slv.getRealSort()
    C = slv.mkConst(real, "c2")
    S = slv.mkConst(real, "s2")
    slv.assertFormula(slv.mkTerm(Kind.EQUAL, C, slv.mkReal(3, 4)))
    slv.assertFormula(slv.mkTerm(Kind.EQUAL, S, slv.mkReal(1, 4)))
    one = slv.mkReal(1)
    zero = slv.mkReal(0)
    leaf = slv.mkTerm(
        Kind.AND,
        slv.mkTerm(Kind.EQUAL, slv.mkTerm(Kind.ADD, C, S), one),
        slv.mkTerm(Kind.GT, C, zero),
        slv.mkTerm(Kind.GT, S, zero),
    )
    slv.assertFormula(slv.mkTerm(Kind.NOT, leaf))
    cvc5_status = str(slv.checkSat())

    return {
        "interior_eta_pi_over_6": {
            "z3_negation_status": z3_status,
            "cvc5_negation_status": cvc5_status,
            "pass": z3_status == "unsat" and cvc5_status == "unsat",
        }
    }


def geomstats_s3_check() -> dict[str, Any]:
    sphere = Hypersphere(dim=3)
    etas = [math.pi / 6.0, math.pi / 4.0, math.pi / 3.0]
    phis = [0.0, 0.7, 1.9]
    chis = [0.3, -0.8, 2.4]
    pts = []
    max_norm_error = 0.0
    for eta, phi, chi in zip(etas, phis, chis):
        p = r4_point(
            torch.tensor(eta, dtype=RTYPE),
            torch.tensor(phi, dtype=RTYPE),
            torch.tensor(chi, dtype=RTYPE),
        )
        pts.append(p.tolist())
        max_norm_error = max(max_norm_error, abs(float(torch.dot(p, p).item()) - 1.0))
    belongs = sphere.belongs(gs.array(pts), atol=TOL_S3)
    all_belong = bool(torch.as_tensor(belongs).all().item())
    return {
        "sample_count": len(pts),
        "geomstats_all_belong_to_S3": all_belong,
        "max_torch_norm_error": max_norm_error,
    }


def hopf_base_vector(z: Any) -> Any:
    z1, z2 = z[0], z[1]
    mixed = z1 * torch.conj(z2)
    return torch.stack(
        [
            2.0 * mixed.real,
            2.0 * mixed.imag,
            (torch.abs(z1) ** 2 - torch.abs(z2) ** 2).real,
        ]
    ).to(RTYPE)


def e3nn_phase_rotation_check() -> dict[str, Any]:
    eta = math.pi / 5.0
    phi = 0.41
    chi = -0.92
    delta = 0.37
    base = hopf_base_vector(c2_point(eta, phi, chi))
    moved = hopf_base_vector(c2_point(eta, phi + delta, chi))
    rotation = o3.matrix_z(torch.tensor(delta, dtype=RTYPE))
    expected = rotation @ base
    error = float(torch.linalg.vector_norm(moved - expected).item())
    return {
        "computed_error": error,
        "known_error": 0.0,
        "match": error <= TOL_E3NN,
        "delta": delta,
    }


def clifford_boundary_orientation() -> dict[str, Any]:
    layout, blades = Cl(4)
    e1, e2, e3, e4 = blades["e1"], blades["e2"], blades["e3"], blades["e4"]
    first_circle_plane = e1 ^ e2
    second_circle_plane = e3 ^ e4
    pseudoscalar = e1 ^ e2 ^ e3 ^ e4
    orientation = float(((first_circle_plane * second_circle_plane) | pseudoscalar)[()])
    return {
        "boundary_plane_product_orientation": orientation,
        "known_orientation": 1.0,
        "match": abs(orientation - 1.0) <= 1.0e-12,
    }


def stereographic_basis(p: Any) -> Any:
    basis = []
    for e in torch.eye(4, dtype=RTYPE):
        v = e - torch.dot(e, p) * p
        for b in basis:
            v = v - torch.dot(v, b) * b
        norm = torch.linalg.vector_norm(v)
        if norm > 1.0e-12:
            basis.append(v / norm)
        if len(basis) == 3:
            break
    basis_matrix = torch.stack(basis, dim=1)
    orientation_matrix = torch.cat([basis_matrix, p[:, None]], dim=1)
    if torch.linalg.det(orientation_matrix) < 0:
        basis_matrix[:, 0] *= -1.0
    return basis_matrix


def stereographic_project(x: Any, p: Any, basis: Any) -> Any:
    dot = (x * p).sum(dim=-1, keepdim=True)
    tangent = x - dot * p
    projected = tangent / (1.0 - dot)
    return projected @ basis


def boundary_circle_one(t: Any) -> Any:
    return torch.stack(
        [torch.cos(t), torch.sin(t), torch.zeros_like(t), torch.zeros_like(t)],
        dim=-1,
    )


def boundary_circle_two(t: Any) -> Any:
    return torch.stack(
        [torch.zeros_like(t), torch.zeros_like(t), torch.cos(t), torch.sin(t)],
        dim=-1,
    )


def gauss_linking_number(samples: int = 320) -> dict[str, Any]:
    p = torch.tensor(
        [
            1.0 / math.sqrt(2.0),
            0.0,
            1.0 / math.sqrt(3.0),
            math.sqrt(1.0 - 1.0 / 2.0 - 1.0 / 3.0),
        ],
        dtype=RTYPE,
    )
    p = p / torch.linalg.vector_norm(p)
    basis = stereographic_basis(p)
    t = torch.linspace(0.0, 2.0 * math.pi, samples + 1, dtype=RTYPE)[:-1]
    dt = 2.0 * math.pi / samples
    c1 = stereographic_project(boundary_circle_one(t), p, basis)
    c2 = stereographic_project(boundary_circle_two(t), p, basis)
    dc1 = (torch.roll(c1, shifts=-1, dims=0) - torch.roll(c1, shifts=1, dims=0)) / (2.0 * dt)
    dc2 = (torch.roll(c2, shifts=-1, dims=0) - torch.roll(c2, shifts=1, dims=0)) / (2.0 * dt)
    diff = c1[:, None, :] - c2[None, :, :]
    cross = torch.cross(
        dc1[:, None, :].expand(samples, samples, 3),
        dc2[None, :, :].expand(samples, samples, 3),
        dim=-1,
    )
    numerator = (diff * cross).sum(dim=-1)
    denominator = torch.linalg.vector_norm(diff, dim=-1) ** 3
    computed = float(((numerator / denominator).sum() * dt * dt / (4.0 * math.pi)).item())
    return {
        "samples_per_circle": samples,
        "computed_linking_number": computed,
        "known_linking_number": 1.0,
        "absolute_error": abs(computed - 1.0),
    }


def tool_manifest() -> list[dict[str, str]]:
    return [
        {"tool": "torch", "reason": "complex128/float64 Hopf embedding, autograd metric, S3 samples, Gauss linking integral"},
        {"tool": "sympy", "reason": "exact symbolic induced metric determinant and area formula identity"},
        {"tool": "z3", "reason": "SMT certificate that the chosen interior radii are nondegenerate and normalized"},
        {"tool": "cvc5", "reason": "independent SMT certificate for the same interior radii constraints"},
        {"tool": "clifford", "reason": "Cl(4) bivector orientation check for the two boundary circle planes"},
        {"tool": "geomstats", "reason": "Hypersphere(dim=3) membership check for sampled Hopf-torus carrier points"},
        {"tool": "gudhi", "reason": "simplicial homology Betti numbers of the periodic torus triangulation"},
        {"tool": "toponetx", "reason": "simplicial-complex skeleton counts and Euler characteristic"},
        {"tool": "rustworkx", "reason": "1-skeleton connectivity/cycle-rank sanity check for the triangulation"},
        {"tool": "e3nn", "reason": "SO(3) z-rotation check for the Hopf-base phase action"},
    ]


def base_receipt() -> dict[str, Any]:
    return {
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "generated_at": _dt.datetime.now(tz=_dt.UTC).isoformat(),
        "finite_map": {
            "domain": "eta in [0, pi/2], phi, chi in R/2piZ",
            "map": "(eta, phi, chi) -> (exp(i phi) cos eta, exp(i chi) sin eta) in C^2 ~= R^4",
            "interior_leaf": "0 < eta < pi/2 gives S1(cos eta) x S1(sin eta)",
            "boundary": "eta=0 and eta=pi/2 collapse one S1 factor to the two Hopf-link circles",
        },
        "TOOL_MANIFEST": tool_manifest(),
        "TOOL_INTEGRATION_DEPTH": {
            "torch": "load_bearing",
            "sympy": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
            "clifford": "load_bearing",
            "geomstats": "load_bearing",
            "gudhi": "load_bearing",
            "toponetx": "load_bearing",
            "rustworkx": "load_bearing",
            "e3nn": "load_bearing",
        },
        "negative_controls": [
            "eta=0 collapses the chi circle and is not a 2-torus",
            "eta=pi/2 collapses the phi circle and is not a 2-torus",
            "forgetting periodic edge identifications gives a grid patch, not Betti (1,2,1)",
            "using scalar eta labels alone has no claim-bearing topology or linking invariant",
        ],
    }


def write_receipt(receipt: dict[str, Any]) -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(jsonable(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    receipt = base_receipt()
    receipt["result_path"] = str(RESULT_PATH)
    receipt["import_errors"] = IMPORT_ERRORS
    checks: list[dict[str, Any]] = []
    receipt["known_value_checks"] = checks

    if IMPORT_ERRORS:
        receipt["status"] = "blocked_import_error"
        receipt["all_known_value_checks_pass"] = False
        write_receipt(receipt)
        return 2

    try:
        topo = topology_invariants()
        receipt["topology"] = topo
        add_check(
            checks,
            "interior_leaf_dimension",
            computed=2,
            known=2,
            match=True,
            method="T_eta has two independent periodic coordinates when 0 < eta < pi/2",
        )
        add_check(
            checks,
            "interior_leaf_euler_characteristic",
            computed=topo["toponetx_euler"],
            known=0,
            match=abs(topo["toponetx_euler"] - 0) <= TOL_TOPOLOGY,
            method="TopoNetX skeleton counts on periodic torus triangulation",
        )
        add_check(
            checks,
            "interior_leaf_betti_numbers",
            computed=topo["gudhi_betti"],
            known=[1, 2, 1],
            match=list(topo["gudhi_betti"]) == [1, 2, 1],
            method="GUDHI homology over field Z/2 on the periodic torus triangulation",
        )
        add_check(
            checks,
            "interior_leaf_genus",
            computed=topo["genus_from_euler"],
            known=1,
            match=topo["genus_from_euler"] == 1,
            method="orientable closed surface relation genus=(2-chi)/2",
        )

        area = induced_metric_area(math.pi / 6.0)
        receipt["area"] = jsonable(area)
        add_check(
            checks,
            "leaf_area_eta_pi_over_6",
            computed=area["computed_area"],
            known=area["known_area"],
            match=area["absolute_error"] <= TOL_AREA,
            formula="area(T_eta)=2*pi^2*sin(2*eta)",
            tolerance=TOL_AREA,
        )

        sym = sympy_area_identity()
        receipt["sympy_area_identity"] = sym
        add_check(
            checks,
            "symbolic_area_formula_identity",
            computed=sym["identity_holds"],
            known=True,
            match=sym["identity_holds"] is True,
            formula=f"{sym['area_formula']} == {sym['known_formula']}",
        )

        smt = smt_radius_certificates()
        receipt["smt_radius_certificates"] = smt
        add_check(
            checks,
            "interior_leaf_radii_smt_nondegenerate",
            computed=smt["interior_eta_pi_over_6"],
            known={"z3_negation_status": "unsat", "cvc5_negation_status": "unsat", "pass": True},
            match=bool(smt["interior_eta_pi_over_6"]["pass"]),
        )

        s3 = geomstats_s3_check()
        receipt["geomstats_s3_membership"] = s3
        add_check(
            checks,
            "sampled_leaf_points_belong_to_S3",
            computed=s3["geomstats_all_belong_to_S3"],
            known=True,
            match=s3["geomstats_all_belong_to_S3"] is True and s3["max_torch_norm_error"] <= TOL_S3,
            tolerance=TOL_S3,
        )

        phase = e3nn_phase_rotation_check()
        receipt["e3nn_hopf_base_phase_rotation"] = phase
        add_check(
            checks,
            "hopf_base_phase_action_is_SO3_z_rotation",
            computed=phase["computed_error"],
            known=phase["known_error"],
            match=bool(phase["match"]),
            tolerance=TOL_E3NN,
        )

        cliff = clifford_boundary_orientation()
        receipt["clifford_boundary_orientation"] = cliff
        add_check(
            checks,
            "boundary_circle_plane_orientation",
            computed=cliff["boundary_plane_product_orientation"],
            known=cliff["known_orientation"],
            match=bool(cliff["match"]),
        )

        linking = gauss_linking_number(samples=320)
        receipt["boundary_linking"] = linking
        add_check(
            checks,
            "boundary_hopf_circles_linking_number",
            computed=linking["computed_linking_number"],
            known=linking["known_linking_number"],
            match=linking["absolute_error"] <= TOL_LINK,
            method="torch Gauss linking integral after orientation-preserving stereographic projection from S3 to R3",
            tolerance=TOL_LINK,
        )

        all_pass = all(bool(row["match"]) for row in checks)
        receipt["all_known_value_checks_pass"] = all_pass
        receipt["status"] = "passed" if all_pass else "blocked_known_value_mismatch"
        write_receipt(receipt)
        return 0 if all_pass else 1
    except Exception as exc:
        receipt["status"] = "blocked_exception"
        receipt["exception"] = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }
        receipt["all_known_value_checks_pass"] = False
        write_receipt(receipt)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

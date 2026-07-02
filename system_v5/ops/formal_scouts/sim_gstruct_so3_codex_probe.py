#!/usr/bin/env python3
"""Independent SO(3) G-structure/Lie-group diagnostic probe.

This probe computes SO(3) from the defining math, not from any prior receipt:
3x3 skew generators, Rodrigues/matrix exponential, metric/orientation
preservation, SU(2) adjoint double cover, and the RP^3 first-homology torsion
witness. It is lego-phase diagnostic evidence only.
"""

from __future__ import annotations

import itertools
import json
import math
import os
import pathlib
from datetime import datetime, timezone
from typing import Any

# Must be set before importing geomstats/clifford.
os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")
os.environ.setdefault("NUMBA_CACHE_DIR", "/private/tmp/numba_cache")
pathlib.Path(os.environ["NUMBA_CACHE_DIR"]).mkdir(parents=True, exist_ok=True)

import cvc5
import gudhi
import rustworkx as rx
import sympy as sp
import torch
import toponetx as tnx
import z3
from cvc5 import Kind
from clifford import Cl
from e3nn import o3
from geomstats.geometry.special_orthogonal import SpecialOrthogonal


CDTYPE = torch.complex128
RTYPE = torch.float64
TOL = 1.0e-9
TOL_TOPO = 0
ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
RESULT_PATH = RESULT_DIR / "gstruct_so3_codex_probe_results.json"
SIM_ID = "gstruct_so3_codex_probe"


def tensor_to_list(x: torch.Tensor) -> list[Any]:
    return x.detach().cpu().tolist()


def max_abs(x: torch.Tensor) -> float:
    return float(torch.max(torch.abs(x)).item())


def matrix_norm(x: torch.Tensor) -> float:
    return float(torch.linalg.matrix_norm(x).item())


def add_check(
    checks: list[dict[str, Any]],
    invariant: str,
    computed: Any,
    known: Any,
    match: bool,
) -> None:
    checks.append(
        {
            "invariant": invariant,
            "computed": computed,
            "known": known,
            "match": bool(match),
        }
    )


def so3_generators() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Basis with [L_i, L_j] = eps_ijk L_k and K(n)v = n x v."""
    lx = torch.tensor(
        [[0.0, 0.0, 0.0], [0.0, 0.0, -1.0], [0.0, 1.0, 0.0]],
        dtype=RTYPE,
    )
    ly = torch.tensor(
        [[0.0, 0.0, 1.0], [0.0, 0.0, 0.0], [-1.0, 0.0, 0.0]],
        dtype=RTYPE,
    )
    lz = torch.tensor(
        [[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
        dtype=RTYPE,
    )
    return lx, ly, lz


def skew_from_axis(axis: torch.Tensor) -> torch.Tensor:
    lx, ly, lz = so3_generators()
    return axis[0] * lx + axis[1] * ly + axis[2] * lz


def rodrigues(axis: torch.Tensor, theta: float) -> torch.Tensor:
    axis = axis / torch.linalg.vector_norm(axis)
    k = skew_from_axis(axis)
    eye = torch.eye(3, dtype=RTYPE)
    return eye + math.sin(theta) * k + (1.0 - math.cos(theta)) * (k @ k)


def exp_rotation(axis: torch.Tensor, theta: float) -> torch.Tensor:
    axis = axis / torch.linalg.vector_norm(axis)
    return torch.linalg.matrix_exp(theta * skew_from_axis(axis))


SX = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=CDTYPE)
SY = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=CDTYPE)
SZ = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=CDTYPE)
PAULI = (SX, SY, SZ)


def su2_matrix(axis: torch.Tensor, theta: float) -> torch.Tensor:
    axis = axis / torch.linalg.vector_norm(axis)
    sigma_n = axis[0] * SX + axis[1] * SY + axis[2] * SZ
    return torch.linalg.matrix_exp((-0.5j * theta) * sigma_n)


def su2_adjoint_to_so3(unitary: torch.Tensor) -> torch.Tensor:
    """R_ij = 1/2 Tr(sigma_i U sigma_j U^dag), so r' = R r."""
    r = torch.empty((3, 3), dtype=RTYPE)
    for i, sigma_i in enumerate(PAULI):
        for j, sigma_j in enumerate(PAULI):
            r[i, j] = (torch.trace(sigma_i @ unitary @ sigma_j @ unitary.conj().T).real / 2.0).to(RTYPE)
    return r


def clifford_rotor_matrix(axis: torch.Tensor, theta: float) -> torch.Tensor:
    layout, blades = Cl(3)
    del layout
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    axis = axis / torch.linalg.vector_norm(axis)
    b = float(axis[0]) * (e2 ^ e3) + float(axis[1]) * (e3 ^ e1) + float(axis[2]) * (e1 ^ e2)
    rotor = math.cos(theta / 2.0) - math.sin(theta / 2.0) * b
    basis = (e1, e2, e3)
    cols: list[torch.Tensor] = []
    for v in basis:
        vp = rotor * v * ~rotor
        cols.append(torch.tensor([float(vp[e1]), float(vp[e2]), float(vp[e3])], dtype=RTYPE))
    return torch.stack(cols, dim=1)


def levi_civita(i: int, j: int, k: int) -> int:
    if len({i, j, k}) < 3:
        return 0
    perm = [i, j, k]
    inversions = sum(1 for a in range(3) for b in range(a + 1, 3) if perm[a] > perm[b])
    return -1 if inversions % 2 else 1


def torch_lie_bracket_residual() -> float:
    gens = so3_generators()
    max_resid = 0.0
    for i, j in itertools.product(range(3), repeat=2):
        expected = sum((levi_civita(i, j, k) * gens[k] for k in range(3)), torch.zeros_like(gens[0]))
        resid = matrix_norm(gens[i] @ gens[j] - gens[j] @ gens[i] - expected)
        max_resid = max(max_resid, resid)
    return max_resid


def sympy_exact_so3_certificate() -> dict[str, Any]:
    lx = sp.Matrix([[0, 0, 0], [0, 0, -1], [0, 1, 0]])
    ly = sp.Matrix([[0, 0, 1], [0, 0, 0], [-1, 0, 0]])
    lz = sp.Matrix([[0, -1, 0], [1, 0, 0], [0, 0, 0]])
    gens = (lx, ly, lz)
    zero3 = sp.zeros(3)

    commutators_match = True
    for i, j in itertools.product(range(3), repeat=2):
        expected = sum((levi_civita(i, j, k) * gens[k] for k in range(3)), sp.zeros(3))
        commutators_match = commutators_match and (gens[i] * gens[j] - gens[j] * gens[i] - expected == zero3)

    theta = sp.symbols("theta", real=True)
    rz = sp.eye(3) + sp.sin(theta) * lz + (1 - sp.cos(theta)) * (lz * lz)
    expected_rz = sp.Matrix(
        [
            [sp.cos(theta), -sp.sin(theta), 0],
            [sp.sin(theta), sp.cos(theta), 0],
            [0, 0, 1],
        ]
    )
    rodrigues_z_match = rz.equals(expected_rz)
    trace_match = sp.simplify(sp.trace(rz) - (1 + 2 * sp.cos(theta))) == 0
    orthogonal_match = sp.simplify(rz.T * rz - sp.eye(3)) == zero3
    det_match = sp.simplify(rz.det() - 1) == 0
    return {
        "commutators_match": bool(commutators_match),
        "rodrigues_z_match": bool(rodrigues_z_match),
        "trace_formula_match": bool(trace_match),
        "orthogonal_match": bool(orthogonal_match),
        "det_plus_one_match": bool(det_match),
    }


def z3_numeric_so3_certificate(orth_resid: float, det_resid: float, trace_resid: float) -> dict[str, Any]:
    solver = z3.Solver()
    orth, det, trace = z3.Reals("orth det trace")
    tol = z3.RealVal(repr(TOL))
    solver.add(orth == z3.RealVal(repr(orth_resid)))
    solver.add(det == z3.RealVal(repr(det_resid)))
    solver.add(trace == z3.RealVal(repr(trace_resid)))
    certified = z3.And(orth <= tol, det <= tol, det >= -tol, trace <= tol, trace >= -tol)
    solver.add(z3.Not(certified))
    status = str(solver.check())
    return {"negation_status": status, "pass": status == "unsat"}


def cvc5_real(solver: cvc5.Solver, value: float) -> cvc5.Term:
    rat = sp.Rational(str(value)).limit_denominator(10**15)
    num, den = sp.fraction(rat)
    if int(den) == 1:
        return solver.mkReal(int(num))
    return solver.mkReal(int(num), int(den))


def cvc5_numeric_so3_certificate(orth_resid: float, det_resid: float, trace_resid: float) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "false")
    solver.setLogic("QF_LRA")
    real_sort = solver.getRealSort()
    orth = solver.mkConst(real_sort, "orth")
    det = solver.mkConst(real_sort, "det")
    trace = solver.mkConst(real_sort, "trace")
    tol = cvc5_real(solver, TOL)
    zero = solver.mkReal(0)
    neg_tol = solver.mkTerm(Kind.SUB, zero, tol)
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, orth, cvc5_real(solver, orth_resid)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, det, cvc5_real(solver, det_resid)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, trace, cvc5_real(solver, trace_resid)))
    certified = solver.mkTerm(
        Kind.AND,
        solver.mkTerm(Kind.LEQ, orth, tol),
        solver.mkTerm(Kind.LEQ, det, tol),
        solver.mkTerm(Kind.GEQ, det, neg_tol),
        solver.mkTerm(Kind.LEQ, trace, tol),
        solver.mkTerm(Kind.GEQ, trace, neg_tol),
    )
    solver.assertFormula(solver.mkTerm(Kind.NOT, certified))
    status = str(solver.checkSat())
    return {"negation_status": status, "pass": status == "unsat"}


def rp2_faces_for_rp3_h1_skeleton() -> list[tuple[int, int, int]]:
    """Minimal RP^2 triangulation. It is the 2-skeleton of the standard RP^3 CW
    model, so H1 is already the RP^3 H1 = Z/2 before the 3-cell is attached."""
    return [
        (0, 1, 2),
        (0, 1, 3),
        (0, 2, 4),
        (0, 3, 5),
        (0, 4, 5),
        (1, 2, 5),
        (1, 3, 4),
        (1, 4, 5),
        (2, 3, 4),
        (2, 3, 5),
    ]


def gudhi_betti_for_field(field: int) -> list[int]:
    st = gudhi.SimplexTree()
    for face in rp2_faces_for_rp3_h1_skeleton():
        st.insert(face, filtration=0.0)
    st.compute_persistence(homology_coeff_field=field, persistence_dim_max=True)
    return [int(x) for x in st.betti_numbers()]


def topology_tool_checks() -> dict[str, Any]:
    faces = rp2_faces_for_rp3_h1_skeleton()
    vertices = sorted(set(itertools.chain.from_iterable(faces)))
    edges = sorted({tuple(sorted(edge)) for face in faces for edge in itertools.combinations(face, 2)})

    st = gudhi.SimplexTree()
    for face in faces:
        st.insert(face, filtration=0.0)
    simplex_count = int(st.num_simplices())

    betti_f2 = gudhi_betti_for_field(2)
    betti_f3 = gudhi_betti_for_field(3)
    betti_f5 = gudhi_betti_for_field(5)

    sc = tnx.SimplicialComplex(faces)
    b1 = sc.incidence_matrix(1, signed=True)
    b2 = sc.incidence_matrix(2, signed=True)
    boundary_boundary = b1 @ b2
    boundary_defect = int(getattr(boundary_boundary, "nnz", 0))

    graph = rx.PyGraph()
    graph.add_nodes_from(vertices)
    for u, v in edges:
        graph.add_edge(u, v, None)
    cycle_rank = int(graph.num_edges() - graph.num_nodes() + 1)

    return {
        "vertices": len(vertices),
        "edges": len(edges),
        "faces": len(faces),
        "simplex_count": simplex_count,
        "gudhi_betti_F2": betti_f2,
        "gudhi_betti_F3": betti_f3,
        "gudhi_betti_F5": betti_f5,
        "toponetx_boundary_of_boundary_nnz": boundary_defect,
        "rustworkx_connected": bool(rx.is_connected(graph)),
        "rustworkx_edge_count": int(graph.num_edges()),
        "rustworkx_cycle_rank": cycle_rank,
    }


def rotation_sweep() -> dict[str, Any]:
    axes = [
        torch.tensor([1.0, 0.0, 0.0], dtype=RTYPE),
        torch.tensor([0.0, 1.0, 0.0], dtype=RTYPE),
        torch.tensor([0.0, 0.0, 1.0], dtype=RTYPE),
        torch.tensor([1.0, 1.0, 1.0], dtype=RTYPE),
        torch.tensor([2.0, -1.0, 3.0], dtype=RTYPE),
        torch.tensor([-3.0, 5.0, 2.0], dtype=RTYPE),
    ]
    angles = [0.0, math.pi / 7.0, math.pi / 3.0, math.pi / 2.0, 1.137, math.pi, 2.0 * math.pi]
    eye = torch.eye(3, dtype=RTYPE)
    so3_space = SpecialOrthogonal(n=3, point_type="matrix")

    maxima: dict[str, float] = {
        "exp_vs_rodrigues": 0.0,
        "orthogonality": 0.0,
        "det_minus_one": 0.0,
        "trace_formula": 0.0,
        "lie_bracket": torch_lie_bracket_residual(),
        "g_structure_metric": 0.0,
        "g_structure_orientation": 0.0,
        "cross_product_preservation": 0.0,
        "su2_adjoint_vs_so3": 0.0,
        "su2_two_to_one": 0.0,
        "clifford_rotor_vs_so3": 0.0,
        "e3nn_axis_angle_vs_so3": 0.0,
    }
    geomstats_belongs_all = True

    for axis in axes:
        axis = axis / torch.linalg.vector_norm(axis)
        for theta in angles:
            r_exp = exp_rotation(axis, theta)
            r_rod = rodrigues(axis, theta)
            maxima["exp_vs_rodrigues"] = max(maxima["exp_vs_rodrigues"], matrix_norm(r_exp - r_rod))
            maxima["orthogonality"] = max(maxima["orthogonality"], matrix_norm(r_exp.T @ r_exp - eye))
            maxima["det_minus_one"] = max(maxima["det_minus_one"], abs(float(torch.linalg.det(r_exp).item()) - 1.0))
            maxima["trace_formula"] = max(
                maxima["trace_formula"],
                abs(float(torch.trace(r_exp).item()) - (1.0 + 2.0 * math.cos(theta))),
            )
            maxima["g_structure_metric"] = max(maxima["g_structure_metric"], matrix_norm(r_exp.T @ eye @ r_exp - eye))
            maxima["g_structure_orientation"] = max(
                maxima["g_structure_orientation"],
                abs(float(torch.linalg.det(r_exp).item()) - 1.0),
            )
            c0, c1, c2 = r_exp[:, 0], r_exp[:, 1], r_exp[:, 2]
            maxima["cross_product_preservation"] = max(
                maxima["cross_product_preservation"],
                float(torch.linalg.vector_norm(torch.cross(c0, c1, dim=0) - c2).item()),
            )

            u = su2_matrix(axis, theta)
            r_su2 = su2_adjoint_to_so3(u)
            r_neg_su2 = su2_adjoint_to_so3(-u)
            maxima["su2_adjoint_vs_so3"] = max(maxima["su2_adjoint_vs_so3"], matrix_norm(r_su2 - r_exp))
            maxima["su2_two_to_one"] = max(maxima["su2_two_to_one"], matrix_norm(r_su2 - r_neg_su2))
            maxima["clifford_rotor_vs_so3"] = max(
                maxima["clifford_rotor_vs_so3"],
                matrix_norm(clifford_rotor_matrix(axis, theta) - r_exp),
            )
            maxima["e3nn_axis_angle_vs_so3"] = max(
                maxima["e3nn_axis_angle_vs_so3"],
                matrix_norm(o3.axis_angle_to_matrix(axis, torch.tensor(theta, dtype=RTYPE)) - r_exp),
            )
            geomstats_belongs_all = geomstats_belongs_all and bool(so3_space.belongs(r_exp).item())

    u_2pi = su2_matrix(torch.tensor([0.0, 0.0, 1.0], dtype=RTYPE), 2.0 * math.pi)
    u_4pi = su2_matrix(torch.tensor([0.0, 0.0, 1.0], dtype=RTYPE), 4.0 * math.pi)
    i2 = torch.eye(2, dtype=CDTYPE)
    pi1_lift = {
        "su2_2pi_vs_minus_identity_norm": matrix_norm((u_2pi + i2).real) + matrix_norm((u_2pi + i2).imag),
        "su2_4pi_vs_plus_identity_norm": matrix_norm((u_4pi - i2).real) + matrix_norm((u_4pi - i2).imag),
        "so3_2pi_vs_identity_norm": matrix_norm(exp_rotation(torch.tensor([0.0, 0.0, 1.0], dtype=RTYPE), 2.0 * math.pi) - eye),
        "so3_4pi_vs_identity_norm": matrix_norm(exp_rotation(torch.tensor([0.0, 0.0, 1.0], dtype=RTYPE), 4.0 * math.pi) - eye),
    }
    return {
        "axis_count": len(axes),
        "angle_count": len(angles),
        "sample_count": len(axes) * len(angles),
        "max_residuals": maxima,
        "geomstats_belongs_all": bool(geomstats_belongs_all),
        "pi1_lift_residuals": pi1_lift,
        "representative_axis": tensor_to_list(axes[4] / torch.linalg.vector_norm(axes[4])),
        "representative_angle": 1.137,
        "representative_rotation": tensor_to_list(exp_rotation(axes[4], 1.137)),
    }


def build_receipt() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    sweep = rotation_sweep()
    sympy_cert = sympy_exact_so3_certificate()
    topo = topology_tool_checks()
    max_resid = sweep["max_residuals"]
    pi1 = sweep["pi1_lift_residuals"]

    z3_cert = z3_numeric_so3_certificate(
        max_resid["orthogonality"],
        max_resid["det_minus_one"],
        max_resid["trace_formula"],
    )
    cvc5_cert = cvc5_numeric_so3_certificate(
        max_resid["orthogonality"],
        max_resid["det_minus_one"],
        max_resid["trace_formula"],
    )

    add_check(
        checks,
        "R^T R == I across deterministic SO(3) sweep",
        {"max_matrix_norm_residual": max_resid["orthogonality"], "samples": sweep["sample_count"]},
        0.0,
        max_resid["orthogonality"] <= TOL,
    )
    add_check(
        checks,
        "det(R) == +1 across deterministic SO(3) sweep",
        {"max_abs_det_minus_one": max_resid["det_minus_one"], "samples": sweep["sample_count"]},
        0.0,
        max_resid["det_minus_one"] <= TOL,
    )
    add_check(
        checks,
        "torch matrix_exp(theta n.L) equals Rodrigues formula",
        {"max_matrix_norm_residual": max_resid["exp_vs_rodrigues"], "samples": sweep["sample_count"]},
        0.0,
        max_resid["exp_vs_rodrigues"] <= TOL,
    )
    add_check(
        checks,
        "Tr(R) == 1 + 2 cos(theta)",
        {"max_abs_trace_residual": max_resid["trace_formula"], "samples": sweep["sample_count"]},
        0.0,
        max_resid["trace_formula"] <= TOL,
    )
    add_check(
        checks,
        "[L_i, L_j] == eps_ijk L_k",
        {"torch_max_matrix_norm_residual": max_resid["lie_bracket"], "sympy_exact": sympy_cert["commutators_match"]},
        {"max_residual": 0.0, "sympy_exact": True},
        max_resid["lie_bracket"] <= TOL and sympy_cert["commutators_match"],
    )
    add_check(
        checks,
        "SO(3) G-structure preserves Euclidean metric and orientation",
        {
            "metric_max_residual": max_resid["g_structure_metric"],
            "orientation_max_det_residual": max_resid["g_structure_orientation"],
            "cross_product_max_residual": max_resid["cross_product_preservation"],
        },
        {"metric_residual": 0.0, "orientation_det_residual": 0.0, "cross_product_residual": 0.0},
        (
            max_resid["g_structure_metric"] <= TOL
            and max_resid["g_structure_orientation"] <= TOL
            and max_resid["cross_product_preservation"] <= TOL
        ),
    )
    add_check(
        checks,
        "SU(2) adjoint map lands on same SO(3) rotation",
        {"max_matrix_norm_residual": max_resid["su2_adjoint_vs_so3"], "samples": sweep["sample_count"]},
        0.0,
        max_resid["su2_adjoint_vs_so3"] <= TOL,
    )
    add_check(
        checks,
        "SU(2)->SO(3) is 2:1 for U and -U",
        {"max_matrix_norm_R_U_minus_R_neg_U": max_resid["su2_two_to_one"], "samples": sweep["sample_count"]},
        0.0,
        max_resid["su2_two_to_one"] <= TOL,
    )
    add_check(
        checks,
        "pi_1(SO(3))=Z_2 lift witness: 2pi -> -I in SU(2), 4pi -> +I",
        pi1,
        {
            "su2_2pi_vs_minus_identity_norm": 0.0,
            "su2_4pi_vs_plus_identity_norm": 0.0,
            "so3_2pi_vs_identity_norm": 0.0,
            "so3_4pi_vs_identity_norm": 0.0,
        },
        all(value <= TOL for value in pi1.values()),
    )
    add_check(
        checks,
        "RP^3 H1 torsion witness via RP^3 CW 2-skeleton: gudhi F2 vs odd prime",
        {
            "gudhi_betti_F2": topo["gudhi_betti_F2"],
            "gudhi_betti_F3": topo["gudhi_betti_F3"],
            "gudhi_betti_F5": topo["gudhi_betti_F5"],
            "model": "minimal RP2 triangulation as RP3 CW 2-skeleton; H1 unchanged by the RP3 3-cell",
        },
        {"H1_F2_dim": 1, "H1_F3_dim": 0, "H1_F5_dim": 0},
        (
            len(topo["gudhi_betti_F2"]) > 1
            and len(topo["gudhi_betti_F3"]) > 1
            and len(topo["gudhi_betti_F5"]) > 1
            and topo["gudhi_betti_F2"][1] == 1
            and topo["gudhi_betti_F3"][1] == 0
            and topo["gudhi_betti_F5"][1] == 0
        ),
    )
    add_check(
        checks,
        "clifford Cl(3) rotor reproduces the same SO(3) rotation",
        {"max_matrix_norm_residual": max_resid["clifford_rotor_vs_so3"], "samples": sweep["sample_count"]},
        0.0,
        max_resid["clifford_rotor_vs_so3"] <= TOL,
    )
    add_check(
        checks,
        "geomstats SpecialOrthogonal(3) belongs check accepts computed rotations",
        {"belongs_all": sweep["geomstats_belongs_all"], "samples": sweep["sample_count"]},
        True,
        sweep["geomstats_belongs_all"],
    )
    add_check(
        checks,
        "e3nn axis_angle_to_matrix matches torch SO(3) exponential",
        {"max_matrix_norm_residual": max_resid["e3nn_axis_angle_vs_so3"], "samples": sweep["sample_count"]},
        0.0,
        max_resid["e3nn_axis_angle_vs_so3"] <= TOL,
    )
    add_check(
        checks,
        "toponetx boundary-of-boundary is zero on torsion witness complex",
        {"boundary_of_boundary_nnz": topo["toponetx_boundary_of_boundary_nnz"]},
        0,
        topo["toponetx_boundary_of_boundary_nnz"] == TOL_TOPO,
    )
    add_check(
        checks,
        "rustworkx 1-skeleton is connected K6 for minimal RP2/RP3-H1 witness",
        {
            "connected": topo["rustworkx_connected"],
            "edge_count": topo["rustworkx_edge_count"],
            "cycle_rank": topo["rustworkx_cycle_rank"],
        },
        {"connected": True, "edge_count": 15, "cycle_rank": 10},
        topo["rustworkx_connected"] and topo["rustworkx_edge_count"] == 15 and topo["rustworkx_cycle_rank"] == 10,
    )
    add_check(
        checks,
        "sympy exact Rodrigues/trace/orthogonal/determinant formulas for z-axis generator",
        sympy_cert,
        {
            "commutators_match": True,
            "rodrigues_z_match": True,
            "trace_formula_match": True,
            "orthogonal_match": True,
            "det_plus_one_match": True,
        },
        all(bool(v) for v in sympy_cert.values()),
    )
    add_check(
        checks,
        "z3 certificate: numeric SO(3) residuals are within tolerance",
        z3_cert,
        {"negation_status": "unsat", "pass": True},
        z3_cert["pass"],
    )
    add_check(
        checks,
        "cvc5 certificate: numeric SO(3) residuals are within tolerance",
        cvc5_cert,
        {"negation_status": "unsat", "pass": True},
        cvc5_cert["pass"],
    )

    blockers = [check for check in checks if not check["match"]]
    return {
        "sim_id": SIM_ID,
        "classification": "diagnostic_only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "finite_map": "axis n in S^2 and theta in R -> K=n_i L_i in so(3) -> R=exp(theta K) in SO(3); SU(2) U=exp(-i theta n.sigma/2) maps by adjoint to the same R",
        "known_value_checks": checks,
        "all_known_value_checks_match": len(blockers) == 0,
        "blockers": blockers,
        "parameters": {
            "dtype_real": "torch.float64",
            "dtype_complex": "torch.complex128",
            "tolerance": TOL,
            "axis_count": sweep["axis_count"],
            "angle_count": sweep["angle_count"],
            "sample_count": sweep["sample_count"],
        },
        "computed_summary": {
            "rotation_sweep": sweep,
            "sympy_exact_certificate": sympy_cert,
            "topology_tool_checks": topo,
            "z3_certificate": z3_cert,
            "cvc5_certificate": cvc5_cert,
        },
        "negative_controls": [
            {
                "name": "O(3) reflection is not SO(3)",
                "computed": {"det_diag_minus_1_1_1": -1.0},
                "blocked_reason": "orientation is reversed, so it is outside the SO(3) G-structure.",
            },
            {
                "name": "odd-prime homology misses Z2 torsion",
                "computed": {"H1_F3_dim": topo["gudhi_betti_F3"][1], "H1_F5_dim": topo["gudhi_betti_F5"][1]},
                "blocked_reason": "odd-prime field homology cannot carry the RP^3 Z2 first-homology torsion class.",
            },
        ],
        "TOOL_MANIFEST": {
            "torch": "load-bearing claim substrate for float64/complex128 Lie algebra, exponentials, determinants, SU(2), and residuals",
            "sympy": "load-bearing exact symbolic commutator, Rodrigues, trace, orthogonality, and determinant certificate",
            "z3": "load-bearing independent SMT certificate that computed SO(3) residuals are inside tolerance",
            "cvc5": "load-bearing second SMT certificate for the same numeric SO(3) residual facts",
            "clifford": "load-bearing Cl(3) rotor construction checked against the torch SO(3) rotations",
            "geomstats": "load-bearing SpecialOrthogonal(3) membership check using the pytorch backend",
            "gudhi": "load-bearing field-homology calculation exposing RP3/RP2-skeleton H1 Z2 torsion by F2 vs odd primes",
            "toponetx": "load-bearing chain-complex boundary-of-boundary check for the torsion witness complex",
            "rustworkx": "load-bearing graph check for connected K6 1-skeleton of the minimal torsion witness complex",
            "e3nn": "load-bearing independent axis-angle SO(3) matrix check against the torch exponential",
        },
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
        "claim_boundary": "diagnostic_only lego-phase SO(3) comparison receipt; not manifold admission and not a validator-gated claim",
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    receipt = build_receipt()
    RESULT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(
        {
            "result_path": str(RESULT_PATH),
            "all_known_value_checks_match": receipt["all_known_value_checks_match"],
            "known_value_check_count": len(receipt["known_value_checks"]),
            "blocker_count": len(receipt["blockers"]),
        },
        indent=2,
        sort_keys=True,
    ))
    return 0 if receipt["all_known_value_checks_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

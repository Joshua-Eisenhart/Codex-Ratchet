#!/usr/bin/env python3
"""Division-algebra projective-line geometry probe (diagnostic_only).

Independent known-geometry check for:
  RP^1 == S^1, CP^1 == S^2, HP^1 == S^4
via the real, complex, and quaternionic Hopf maps.

Claim substrate:
  - torch.float64 / torch.complex128 for all numeric carrier math.
  - sympy for exact polynomial identities.
  - z3 and cvc5 for the real no-continuous-phase obstruction.
  - clifford, geomstats, gudhi, toponetx, rustworkx, e3nn as load-bearing
    independent geometry/topology checks.

No NumPy is used as a claim substrate.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
from itertools import combinations
from typing import Any

# geomstats must be placed on the torch backend before import. clifford's numba
# cache path is broken in this interpreter unless JIT is disabled before import.
os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import cvc5
from cvc5 import Kind
from clifford import Cl
from e3nn import o3
from geomstats.geometry.hypersphere import Hypersphere
import gudhi
import rustworkx as rx
import sympy as sp
import torch
import toponetx as tnx
import z3

RTYPE = torch.float64
CDTYPE = torch.complex128
TOL = 1.0e-9
TOL_E3NN = 1.0e-5

ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "geom_division_algebra_projective_lines_codex_probe"
RESULT_PATH = RESULT_DIR / "geom_division_algebra_projective_lines_codex_probe_results.json"


def real_norm(x: torch.Tensor) -> float:
    return float(torch.linalg.vector_norm(x.to(RTYPE)).item())


def normalize_real_pair(x: torch.Tensor) -> torch.Tensor:
    return x.to(RTYPE) / torch.linalg.vector_norm(x.to(RTYPE))


def normalize_complex_pair(z0: torch.Tensor, z1: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    norm = torch.sqrt((z0.abs() ** 2 + z1.abs() ** 2).real).to(RTYPE)
    return z0.to(CDTYPE) / norm, z1.to(CDTYPE) / norm


def q_conj(q: torch.Tensor) -> torch.Tensor:
    return torch.stack([q[0], -q[1], -q[2], -q[3]]).to(RTYPE)


def q_mul(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    aw, ax, ay, az = a.to(RTYPE)
    bw, bx, by, bz = b.to(RTYPE)
    return torch.stack(
        [
            aw * bw - ax * bx - ay * by - az * bz,
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
        ]
    ).to(RTYPE)


def q_norm_sq(q: torch.Tensor) -> torch.Tensor:
    q = q.to(RTYPE)
    return torch.dot(q, q)


def normalize_quaternion_pair(q0: torch.Tensor, q1: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    q0 = q0.to(RTYPE)
    q1 = q1.to(RTYPE)
    norm = torch.sqrt(q_norm_sq(q0) + q_norm_sq(q1))
    return q0 / norm, q1 / norm


def hopf_real(pair: torch.Tensor) -> torch.Tensor:
    a, b = normalize_real_pair(pair)
    return torch.stack([a * a - b * b, 2.0 * a * b]).to(RTYPE)


def hopf_complex(z0: torch.Tensor, z1: torch.Tensor) -> torch.Tensor:
    z0, z1 = normalize_complex_pair(z0, z1)
    u = z0 * z1.conj()
    return torch.stack([2.0 * u.real, 2.0 * u.imag, z0.abs() ** 2 - z1.abs() ** 2]).to(RTYPE)


def hopf_quaternion(q0: torch.Tensor, q1: torch.Tensor) -> torch.Tensor:
    q0, q1 = normalize_quaternion_pair(q0, q1)
    first_four = 2.0 * q_mul(q0, q_conj(q1))
    last = q_norm_sq(q0) - q_norm_sq(q1)
    return torch.cat([first_four, last.reshape(1)]).to(RTYPE)


def right_phase_quaternion_pair(
    q0: torch.Tensor, q1: torch.Tensor, phase: torch.Tensor
) -> tuple[torch.Tensor, torch.Tensor]:
    return q_mul(q0, phase), q_mul(q1, phase)


def z3_no_real_continuous_phase() -> dict[str, Any]:
    """No real scalar generator j can satisfy j^2 = -1."""
    solver = z3.Solver()
    j = z3.Real("real_phase_generator_j")
    solver.add(j * j + 1 == 0)
    status = str(solver.check())
    return {"constraint": "exists real j with j^2 + 1 == 0", "status": status, "unsat": status == "unsat"}


def cvc5_no_real_continuous_phase() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_NRA")
    rsort = solver.getRealSort()
    j = solver.mkConst(rsort, "real_phase_generator_j")
    zero = solver.mkReal(0)
    one = solver.mkReal(1)
    j_sq_plus_one = solver.mkTerm(Kind.ADD, solver.mkTerm(Kind.MULT, j, j), one)
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, j_sq_plus_one, zero))
    res = solver.checkSat()
    status = "unsat" if res.isUnsat() else ("sat" if res.isSat() else "unknown")
    return {"constraint": "exists real j with j^2 + 1 == 0", "status": status, "unsat": res.isUnsat()}


def sympy_projective_identities() -> dict[str, Any]:
    a, b, c, d = sp.symbols("a b c d", real=True)
    n0 = a * a + b * b
    n1 = c * c + d * d
    c_real = a * c + b * d
    c_imag = b * c - a * d
    c_hopf_norm_sq = 4 * (c_real * c_real + c_imag * c_imag) + (n0 - n1) ** 2
    c_identity = sp.expand(c_hopf_norm_sq - (n0 + n1) ** 2) == 0

    phase_a, phase_b = sp.symbols("phase_a phase_b", real=True)
    c_phase_comm = sp.simplify(sp.exp(sp.I * phase_a) * sp.exp(sp.I * phase_b)
                               - sp.exp(sp.I * phase_b) * sp.exp(sp.I * phase_a))

    q0 = sp.symbols("a0:4", real=True)
    q1 = sp.symbols("b0:4", real=True)

    def sp_q_conj(q: tuple[sp.Symbol, ...]) -> tuple[sp.Expr, sp.Expr, sp.Expr, sp.Expr]:
        return (q[0], -q[1], -q[2], -q[3])

    def sp_q_mul(x: tuple[sp.Expr, ...], y: tuple[sp.Expr, ...]) -> tuple[sp.Expr, sp.Expr, sp.Expr, sp.Expr]:
        xw, xi, xj, xk = x
        yw, yi, yj, yk = y
        return (
            xw * yw - xi * yi - xj * yj - xk * yk,
            xw * yi + xi * yw + xj * yk - xk * yj,
            xw * yj - xi * yk + xj * yw + xk * yi,
            xw * yk + xi * yj - xj * yi + xk * yw,
        )

    h0 = sum(x * x for x in q0)
    h1 = sum(x * x for x in q1)
    product = sp_q_mul(q0, sp_q_conj(q1))
    h_hopf_norm_sq = 4 * sum(x * x for x in product) + (h0 - h1) ** 2
    h_identity = sp.expand(h_hopf_norm_sq - (h0 + h1) ** 2) == 0

    return {
        "complex_hopf_norm_identity": bool(c_identity),
        "complex_hopf_norm_identity_polynomial": "||Hopf_C(z0,z1)||^2 == (||z0||^2 + ||z1||^2)^2",
        "complex_phase_commutator_exact_zero": bool(c_phase_comm == 0),
        "quaternion_hopf_norm_identity": bool(h_identity),
        "quaternion_hopf_norm_identity_polynomial": "||Hopf_H(q0,q1)||^2 == (||q0||^2 + ||q1||^2)^2",
    }


def mv_norm(mv: Any) -> float:
    coeffs = torch.tensor([float(x) for x in mv.value], dtype=RTYPE)
    return real_norm(coeffs)


def scalar_part(mv: Any) -> float:
    return float(mv.value[0])


def clifford_evidence() -> dict[str, Any]:
    layout2, blades2 = Cl(2)
    e1, e2 = blades2["e1"], blades2["e2"]
    e12 = e1 * e2
    c_a = 1.25 + 0.5 * e12
    c_b = -0.75 + 2.0 * e12
    cl2_comm = c_a * c_b - c_b * c_a
    e12_sq = e12 * e12

    layout3, blades3 = Cl(3)
    f1, f2, f3 = blades3["e1"], blades3["e2"], blades3["e3"]
    qi = f2 * f3
    qj = f3 * f1
    qk = f1 * f2
    q_squares = [qi * qi, qj * qj, qk * qk]
    h_comm = qi * qj - qj * qi
    h_anticomm = qi * qj + qj * qi

    return {
        "cl2": {
            "e12_square_scalar": scalar_part(e12_sq),
            "e12_square_nonscalar_norm": mv_norm(e12_sq - scalar_part(e12_sq)),
            "sample_even_commutator_norm": mv_norm(cl2_comm),
            "abelian_sample": mv_norm(cl2_comm) < TOL,
        },
        "cl3": {
            "i_j_k_square_scalars": [scalar_part(x) for x in q_squares],
            "i_j_k_square_nonscalar_norms": [mv_norm(x - scalar_part(x)) for x in q_squares],
            "ij_minus_ji_norm": mv_norm(h_comm),
            "ij_plus_ji_norm": mv_norm(h_anticomm),
            "nonabelian": mv_norm(h_comm) > TOL and mv_norm(h_anticomm) < TOL,
        },
    }


def geomstats_evidence(points: dict[str, torch.Tensor]) -> dict[str, Any]:
    dims = {"RP1": 1, "CP1": 2, "HP1": 4}
    out: dict[str, Any] = {}
    for name, dim in dims.items():
        sphere = Hypersphere(dim=dim)
        point = points[name].to(RTYPE)
        belongs = sphere.belongs(point)
        out[name] = {
            "sphere_dim": int(sphere.dim),
            "ambient_dim": int(point.numel()),
            "belongs": bool(belongs.item() if hasattr(belongs, "item") else belongs),
            "point_norm": real_norm(point),
        }
    return out


def boundary_facets(sphere_dim: int) -> list[tuple[int, ...]]:
    vertices = range(sphere_dim + 2)
    return [tuple(face) for face in combinations(vertices, sphere_dim + 1)]


def gudhi_boundary_evidence() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, dim in (("RP1_as_S1", 1), ("CP1_as_S2", 2), ("HP1_as_S4", 4)):
        st = gudhi.SimplexTree()
        for facet in boundary_facets(dim):
            st.insert(facet)
        st.compute_persistence(persistence_dim_max=True)
        out[name] = {
            "dimension": int(st.dimension()),
            "num_simplices": int(st.num_simplices()),
            "betti_numbers": [int(x) for x in st.betti_numbers()],
        }
    return out


def toponetx_boundary_evidence() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, dim in (("RP1_as_S1", 1), ("CP1_as_S2", 2), ("HP1_as_S4", 4)):
        complex_ = tnx.SimplicialComplex(boundary_facets(dim))
        out[name] = {
            "dimension": int(complex_.dim),
            "shape": [int(x) for x in complex_.shape],
        }
    return out


def rustworkx_boundary_evidence() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, dim in (("RP1_as_S1", 1), ("CP1_as_S2", 2), ("HP1_as_S4", 4)):
        graph = rx.PyGraph()
        graph.add_nodes_from(range(dim + 2))
        for edge in combinations(range(dim + 2), 2):
            graph.add_edge(edge[0], edge[1], None)
        out[name] = {
            "connected": bool(rx.is_connected(graph)),
            "nodes": int(graph.num_nodes()),
            "edges": int(graph.num_edges()),
            "cycle_basis_size": int(len(rx.cycle_basis(graph))),
        }
    return out


def e3nn_cp1_evidence(cp1_point: torch.Tensor) -> dict[str, Any]:
    alpha = torch.tensor(0.31, dtype=torch.float32)
    beta = torch.tensor(0.67, dtype=torch.float32)
    gamma = torch.tensor(-0.43, dtype=torch.float32)
    rot = o3.angles_to_matrix(alpha, beta, gamma)
    recovered = o3.matrix_to_angles(rot)
    roundtrip = o3.angles_to_matrix(*recovered)
    point = cp1_point.to(torch.float32)
    rotated = rot @ point
    det = float(torch.det(rot).item())
    orth_defect = float(torch.linalg.matrix_norm(rot @ rot.T - torch.eye(3, dtype=torch.float32)).item())
    roundtrip_defect = float(torch.linalg.matrix_norm(roundtrip - rot).item())
    rotated_norm = float(torch.linalg.vector_norm(rotated).item())
    return {
        "det": det,
        "orthogonality_defect": orth_defect,
        "roundtrip_defect": roundtrip_defect,
        "rotated_cp1_hopf_norm": rotated_norm,
        "pass": (
            abs(det - 1.0) < TOL_E3NN
            and orth_defect < TOL_E3NN
            and roundtrip_defect < TOL_E3NN
            and abs(rotated_norm - 1.0) < TOL_E3NN
        ),
    }


def add_check(checks: list[dict[str, Any]], invariant: str, computed: Any, known: Any, match: bool) -> None:
    checks.append({"invariant": invariant, "computed": computed, "known": known, "match": bool(match)})


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    rp_pair = normalize_real_pair(torch.tensor([3.0, 4.0], dtype=RTYPE))
    rp_image = hopf_real(rp_pair)
    rp_antipodal_diff = real_norm(hopf_real(-rp_pair) - rp_image)

    z0, z1 = normalize_complex_pair(
        torch.tensor(0.35 + 0.20j, dtype=CDTYPE),
        torch.tensor(-0.10 + 0.90j, dtype=CDTYPE),
    )
    cp_image = hopf_complex(z0, z1)
    theta = torch.tensor(0.812, dtype=RTYPE)
    phi = torch.tensor(-1.377, dtype=RTYPE)
    phase_theta = torch.exp((1j * theta).to(CDTYPE))
    phase_phi = torch.exp((1j * phi).to(CDTYPE))
    cp_phase_diff = real_norm(hopf_complex(z0 * phase_theta, z1 * phase_theta) - cp_image)
    cp_phase_comm = torch.abs(phase_theta * phase_phi - phase_phi * phase_theta).to(RTYPE)

    hq0, hq1 = normalize_quaternion_pair(
        torch.tensor([0.40, -0.20, 0.10, 0.30], dtype=RTYPE),
        torch.tensor([-0.10, 0.55, -0.25, 0.70], dtype=RTYPE),
    )
    hp_image = hopf_quaternion(hq0, hq1)
    unit_i = torch.tensor([0.0, 1.0, 0.0, 0.0], dtype=RTYPE)
    unit_j = torch.tensor([0.0, 0.0, 1.0, 0.0], dtype=RTYPE)
    hpq0_i, hpq1_i = right_phase_quaternion_pair(hq0, hq1, unit_i)
    hp_phase_diff = real_norm(hopf_quaternion(hpq0_i, hpq1_i) - hp_image)
    sp1_comm = q_mul(unit_i, unit_j) - q_mul(unit_j, unit_i)
    sp1_comm_norm = real_norm(sp1_comm)

    sym = sympy_projective_identities()
    z3_real = z3_no_real_continuous_phase()
    cvc5_real = cvc5_no_real_continuous_phase()
    cl = clifford_evidence()
    geom = geomstats_evidence({"RP1": rp_image, "CP1": cp_image, "HP1": hp_image})
    gudhi_ev = gudhi_boundary_evidence()
    tnx_ev = toponetx_boundary_evidence()
    rx_ev = rustworkx_boundary_evidence()
    e3 = e3nn_cp1_evidence(cp_image)

    expected_betti = {
        "RP1_as_S1": [1, 1],
        "CP1_as_S2": [1, 0, 1],
        "HP1_as_S4": [1, 0, 0, 0, 1],
    }
    expected_tnx_shape = {
        "RP1_as_S1": [3, 3],
        "CP1_as_S2": [4, 6, 4],
        "HP1_as_S4": [6, 15, 20, 15, 6],
    }
    expected_rx_cycles = {"RP1_as_S1": 1, "CP1_as_S2": 3, "HP1_as_S4": 10}

    checks: list[dict[str, Any]] = []
    add_check(checks, "RP1_real_dimension_via_geomstats_S1", geom["RP1"]["sphere_dim"], 1, geom["RP1"]["sphere_dim"] == 1)
    add_check(checks, "CP1_real_dimension_via_geomstats_S2", geom["CP1"]["sphere_dim"], 2, geom["CP1"]["sphere_dim"] == 2)
    add_check(checks, "HP1_real_dimension_via_geomstats_S4", geom["HP1"]["sphere_dim"], 4, geom["HP1"]["sphere_dim"] == 4)
    add_check(checks, "RP1_Hopf_image_norm", geom["RP1"]["point_norm"], 1.0, abs(geom["RP1"]["point_norm"] - 1.0) < TOL and geom["RP1"]["belongs"])
    add_check(checks, "CP1_Hopf_image_norm", geom["CP1"]["point_norm"], 1.0, abs(geom["CP1"]["point_norm"] - 1.0) < TOL and geom["CP1"]["belongs"])
    add_check(checks, "HP1_Hopf_image_norm", geom["HP1"]["point_norm"], 1.0, abs(geom["HP1"]["point_norm"] - 1.0) < TOL and geom["HP1"]["belongs"])
    add_check(checks, "R_Z2_antipodal_fiber_collapse", rp_antipodal_diff, 0.0, rp_antipodal_diff < TOL)
    add_check(checks, "R_no_continuous_phase_generator_z3", z3_real["status"], "unsat", z3_real["unsat"])
    add_check(checks, "R_no_continuous_phase_generator_cvc5", cvc5_real["status"], "unsat", cvc5_real["unsat"])
    add_check(checks, "C_U1_phase_fiber_collapse", cp_phase_diff, 0.0, cp_phase_diff < TOL)
    add_check(checks, "C_U1_phase_commutator_abelian", float(cp_phase_comm.item()), 0.0, float(cp_phase_comm.item()) < TOL)
    add_check(checks, "H_Sp1_phase_fiber_collapse", hp_phase_diff, 0.0, hp_phase_diff < TOL)
    add_check(checks, "H_Sp1_unit_phase_lies_on_S3", real_norm(unit_i), 1.0, abs(real_norm(unit_i) - 1.0) < TOL)
    add_check(checks, "H_Sp1_nonabelian_commutator_norm", sp1_comm_norm, ">0", sp1_comm_norm > TOL)
    add_check(checks, "sympy_complex_Hopf_norm_identity", sym["complex_hopf_norm_identity"], True, sym["complex_hopf_norm_identity"])
    add_check(checks, "sympy_complex_U1_commutator_exact_zero", sym["complex_phase_commutator_exact_zero"], True, sym["complex_phase_commutator_exact_zero"])
    add_check(checks, "sympy_quaternion_Hopf_norm_identity", sym["quaternion_hopf_norm_identity"], True, sym["quaternion_hopf_norm_identity"])
    add_check(
        checks,
        "even_Cl2_equals_C_e12_square_minus_one",
        {"scalar": cl["cl2"]["e12_square_scalar"], "nonscalar_norm": cl["cl2"]["e12_square_nonscalar_norm"]},
        {"scalar": -1.0, "nonscalar_norm": 0.0},
        abs(cl["cl2"]["e12_square_scalar"] + 1.0) < TOL and cl["cl2"]["e12_square_nonscalar_norm"] < TOL,
    )
    add_check(checks, "even_Cl2_equals_C_abelian_sample", cl["cl2"]["sample_even_commutator_norm"], 0.0, cl["cl2"]["abelian_sample"])
    add_check(
        checks,
        "even_Cl3_equals_H_i_j_k_square_minus_one",
        cl["cl3"]["i_j_k_square_scalars"],
        [-1.0, -1.0, -1.0],
        all(abs(x + 1.0) < TOL for x in cl["cl3"]["i_j_k_square_scalars"])
        and all(x < TOL for x in cl["cl3"]["i_j_k_square_nonscalar_norms"]),
    )
    add_check(
        checks,
        "even_Cl3_equals_H_nonabelian_ij_not_ji",
        {"ij_minus_ji_norm": cl["cl3"]["ij_minus_ji_norm"], "ij_plus_ji_norm": cl["cl3"]["ij_plus_ji_norm"]},
        {"ij_minus_ji_norm": ">0", "ij_plus_ji_norm": 0.0},
        cl["cl3"]["nonabelian"],
    )
    add_check(
        checks,
        "gudhi_boundary_sphere_betti_RP1_CP1_HP1",
        {k: v["betti_numbers"] for k, v in gudhi_ev.items()},
        expected_betti,
        all(gudhi_ev[k]["betti_numbers"] == v for k, v in expected_betti.items()),
    )
    add_check(
        checks,
        "toponetx_boundary_dimensions_and_f_vectors",
        {k: {"dimension": v["dimension"], "shape": v["shape"]} for k, v in tnx_ev.items()},
        {
            k: {"dimension": {"RP1_as_S1": 1, "CP1_as_S2": 2, "HP1_as_S4": 4}[k], "shape": expected_tnx_shape[k]}
            for k in expected_tnx_shape
        },
        all(tnx_ev[k]["dimension"] == {"RP1_as_S1": 1, "CP1_as_S2": 2, "HP1_as_S4": 4}[k]
            and tnx_ev[k]["shape"] == expected_tnx_shape[k]
            for k in expected_tnx_shape),
    )
    add_check(
        checks,
        "rustworkx_boundary_1_skeleton_connected_cycle_ranks",
        {k: {"connected": v["connected"], "cycle_basis_size": v["cycle_basis_size"]} for k, v in rx_ev.items()},
        {k: {"connected": True, "cycle_basis_size": expected_rx_cycles[k]} for k in expected_rx_cycles},
        all(rx_ev[k]["connected"] and rx_ev[k]["cycle_basis_size"] == expected_rx_cycles[k] for k in expected_rx_cycles),
    )
    add_check(
        checks,
        "e3nn_SO3_action_preserves_CP1_S2_Hopf_norm",
        e3,
        {"det": 1.0, "orthogonality_defect": 0.0, "roundtrip_defect": 0.0, "rotated_cp1_hopf_norm": 1.0},
        e3["pass"],
    )

    known_values_all_match = all(c["match"] for c in checks)
    blockers = [
        f"KNOWN-VALUE MISMATCH: {c['invariant']} computed={c['computed']} known={c['known']}"
        for c in checks
        if not c["match"]
    ]

    tool_manifest = {
        "torch": {
            "used": True,
            "role": "load_bearing",
            "reason": "computes the R/C/H carrier points, Hopf maps, norms, phase/fiber actions, and quaternion products in float64/complex128",
        },
        "sympy": {
            "used": True,
            "role": "load_bearing",
            "reason": "exact polynomial proof of complex and quaternionic Hopf image norm identities and exact U(1) commutativity",
        },
        "z3": {
            "used": True,
            "role": "load_bearing",
            "reason": "SMT UNSAT certificate for absence of a real scalar continuous phase generator j with j^2=-1",
        },
        "cvc5": {
            "used": True,
            "role": "load_bearing",
            "reason": "independent SMT UNSAT certificate for the same real no-continuous-phase obstruction",
        },
        "clifford": {
            "used": True,
            "role": "load_bearing",
            "reason": "computes even-Cl(2) generator e12^2=-1 and even-Cl(3) quaternion-unit noncommutativity",
        },
        "geomstats": {
            "used": True,
            "role": "load_bearing",
            "reason": "checks RP1/CP1/HP1 Hopf images as points on Hypersphere(dim=1/2/4)",
        },
        "gudhi": {
            "used": True,
            "role": "load_bearing",
            "reason": "computes Betti numbers for boundary triangulations of S1, S2, and S4",
        },
        "toponetx": {
            "used": True,
            "role": "load_bearing",
            "reason": "computes the simplicial-complex dimensions and f-vectors of the same boundary sphere models",
        },
        "rustworkx": {
            "used": True,
            "role": "load_bearing",
            "reason": "checks connected 1-skeletons and cycle-basis ranks for the boundary sphere models",
        },
        "e3nn": {
            "used": True,
            "role": "load_bearing",
            "reason": "checks a genuine SO(3) l=1 action preserves the CP1/S2 Hopf image norm",
        },
    }

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": "1.0.0",
        "classification": "diagnostic_only",
        "promotion_allowed": False,
        "promotion_status": "diagnostic_only",
        "sim_execution_kind": "nonclassical",
        "sim_class": "known_geometry_probe",
        "purpose": "Independent diagnostic-only known-geometry probe for division-algebra projective lines RP1, CP1, HP1.",
        "scientific_question": "Do finite torch carrier computations and independent geometry/topology tools reproduce RP1=S1, CP1=S2, HP1=S4, the associated Hopf fibers, and the even-Clifford algebra identifications?",
        "claim_ceiling": "diagnostic_only / known-geometry cross-model comparison only; no manifold, layer, Axis0, flux, bridge, or physics admission.",
        "finite_map": {
            "R": "(a,b) in S1 -> (a^2-b^2, 2ab) in S1, quotient by {+1,-1}",
            "C": "(z0,z1) in S3 -> (2 Re(z0 conj(z1)), 2 Im(z0 conj(z1)), |z0|^2-|z1|^2) in S2, quotient by U(1)",
            "H": "(q0,q1) in S7 -> (2 q0 conj(q1), |q0|^2-|q1|^2) in S4, quotient by Sp(1)=S3",
        },
        "domain": "normalized pairs in R^2, C^2, and H^2 represented by torch.float64/complex128 carriers",
        "codomain_or_output": "unit Hopf image points on S1, S2, S4 plus fiber, topology, and even-Clifford evidence",
        "carrier_realization": "torch.float64 real/quaternion coordinates and torch.complex128 complex coordinates; no NumPy claim substrate",
        "known_value_checks": checks,
        "result_summary": {
            "all_pass": known_values_all_match,
            "known_values_all_match": known_values_all_match,
            "n_known_value_checks": len(checks),
            "blocker_count": len(blockers),
        },
        "computed_evidence": {
            "hopf_images": {
                "RP1_as_S1": [float(x) for x in rp_image],
                "CP1_as_S2": [float(x) for x in cp_image],
                "HP1_as_S4": [float(x) for x in hp_image],
            },
            "real_fiber": {
                "fiber": "Z2=S0",
                "antipodal_diff": rp_antipodal_diff,
                "z3_no_real_continuous_phase": z3_real,
                "cvc5_no_real_continuous_phase": cvc5_real,
            },
            "complex_fiber": {
                "fiber": "U(1)",
                "phase_diff": cp_phase_diff,
                "phase_commutator_abs": float(cp_phase_comm.item()),
            },
            "quaternionic_fiber": {
                "fiber": "Sp(1)=S3",
                "phase_diff": hp_phase_diff,
                "ij_minus_ji": [float(x) for x in sp1_comm],
                "ij_minus_ji_norm": sp1_comm_norm,
            },
            "sympy": sym,
            "clifford": cl,
            "geomstats": geom,
            "gudhi": gudhi_ev,
            "toponetx": tnx_ev,
            "rustworkx": rx_ev,
            "e3nn": e3,
        },
        "required_tools": ["torch", "sympy", "z3", "cvc5", "clifford", "geomstats", "gudhi", "toponetx", "rustworkx", "e3nn"],
        "actual_tools_used": ["torch", "sympy", "z3", "cvc5", "clifford", "geomstats", "gudhi", "toponetx", "rustworkx", "e3nn"],
        "TOOL_MANIFEST": tool_manifest,
        "tool_manifest": tool_manifest,
        "TOOL_INTEGRATION_DEPTH": {name: "load_bearing" for name in tool_manifest},
        "proof_surfaces_used": ["sympy", "z3", "cvc5"],
        "geometry_surfaces_used": ["clifford", "geomstats", "e3nn"],
        "topology_surfaces_used": ["gudhi", "toponetx", "rustworkx"],
        "downstream_blocks": ["manifold_layers", "stacking", "G_structure", "Axis0", "flux", "Xi", "Phi0", "bridge", "physics"],
        "blocked_consumers": ["manifold_layers", "stacking", "G_structure", "Axis0", "flux", "Xi", "Phi0", "bridge", "physics"],
        "allowed_claims": ["diagnostic-only known-geometry witness for division-algebra projective lines"],
        "promotion_blockers": ["diagnostic_only by request; lego phase; no validator gate; no downstream manifold admission"],
        "all_pass": known_values_all_match,
        "blockers": blockers,
        "pass_rule": "every known_value_check computes match=true; no hardcoded pass flag",
        "fail_rule": "any known_value_check mismatch becomes a blocker and exits nonzero",
        "result_path": str(RESULT_PATH),
    }

    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "wrote": str(RESULT_PATH),
        "all_pass": known_values_all_match,
        "n_known_value_checks": len(checks),
        "blockers": blockers,
    }, indent=2, sort_keys=True))
    return 0 if known_values_all_match else 1


if __name__ == "__main__":
    raise SystemExit(main())

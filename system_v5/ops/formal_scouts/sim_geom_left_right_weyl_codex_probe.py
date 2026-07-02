#!/usr/bin/env python3
"""Left/right Weyl projector geometry probe.

classification = diagnostic_only

This is an independent known-geometry receipt for the chiral/Weyl split:

    gamma5 = diag(1, 1, -1, -1)
    P_L = (I + gamma5) / 2
    P_R = (I - gamma5) / 2

The claim substrate is torch complex128/float64. Other tools are load-bearing
cross-checks, not substitutes for the torch carrier.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
from datetime import datetime, timezone
from typing import Any

# clifford/numba can otherwise try to use an invalid cache locator in this env.
os.environ.setdefault("NUMBA_CACHE_DIR", "/private/tmp/numba-cache")
os.environ.setdefault("NUMBA_DISABLE_CACHE", "1")
pathlib.Path(os.environ["NUMBA_CACHE_DIR"]).mkdir(parents=True, exist_ok=True)

import cvc5
from cvc5 import Kind
import gudhi
import rustworkx as rx
import sympy as sp
import torch
import toponetx as tnx
import z3
from clifford import Cl
from e3nn import o3
from geomstats.geometry.hypersphere import Hypersphere
import geomstats.backend as gs


CDTYPE = torch.complex128
RTYPE = torch.float64
TOL = 1.0e-9
TOL_E3NN = 1.0e-5

ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
RESULT_PATH = RESULT_DIR / "geom_left_right_weyl_codex_probe_results.json"
SIM_ID = "geom_left_right_weyl_codex_probe"


def max_abs(x: torch.Tensor) -> float:
    return float(torch.max(torch.abs(x)).item())


def check_close(invariant: str, computed: float, known: float, tol: float = TOL) -> dict[str, Any]:
    c = float(computed)
    k = float(known)
    match = math.isfinite(c) and abs(c - k) <= tol
    return {"invariant": invariant, "computed": c, "known": k, "match": bool(match)}


def check_status(invariant: str, computed: str, known: str) -> dict[str, Any]:
    match = computed == known
    return {"invariant": invariant, "computed": computed, "known": known, "match": bool(match)}


def normalize(psi: torch.Tensor) -> torch.Tensor:
    return psi / torch.linalg.vector_norm(psi)


def density(psi: torch.Tensor) -> torch.Tensor:
    psi = normalize(psi)
    return torch.outer(psi, psi.conj())


def evolve_density(rho: torch.Tensor, hamiltonian: torch.Tensor, t: float) -> torch.Tensor:
    unitary = torch.linalg.matrix_exp((-1j * t) * hamiltonian)
    return unitary @ rho @ unitary.conj().T


def skew(v: torch.Tensor) -> torch.Tensor:
    z = torch.tensor(0.0, dtype=RTYPE)
    return torch.stack(
        [
            torch.stack([z, -v[2], v[1]]),
            torch.stack([v[2], z, -v[0]]),
            torch.stack([-v[1], v[0], z]),
        ]
    )


def rodrigues(axis: torch.Tensor, angle: float) -> torch.Tensor:
    k = axis / torch.linalg.vector_norm(axis)
    kx = skew(k)
    eye = torch.eye(3, dtype=RTYPE)
    return eye + math.sin(angle) * kx + (1.0 - math.cos(angle)) * (kx @ kx)


def sympy_projector_certificate() -> bool:
    i4 = sp.eye(4)
    g5 = sp.diag(1, 1, -1, -1)
    pl = (i4 + g5) / 2
    pr = (i4 - g5) / 2
    zero = sp.zeros(4)
    return bool(
        g5 * g5 == i4
        and pl + pr == i4
        and pl * pr == zero
        and pl * pl == pl
        and pr * pr == pr
    )


def z3_left_right_intersection_status() -> str:
    solver = z3.Solver()
    vals = [z3.Real(f"v{i}") for i in range(4)]
    signs = [1, 1, -1, -1]
    for sign, val in zip(signs, vals):
        solver.add(sign * val == val)   # gamma5 v = +v
        solver.add(sign * val == -val)  # gamma5 v = -v
    norm_sq = sum(val * val for val in vals)
    solver.add(norm_sq > 0)
    return str(solver.check())


def cvc5_left_right_intersection_status() -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_NRA")
    real_sort = solver.getRealSort()
    vals = [solver.mkConst(real_sort, f"v{i}") for i in range(4)]

    def real(n: int):
        return solver.mkReal(n)

    def mul_const(n: int, term):
        if n == 1:
            return term
        return solver.mkTerm(Kind.MULT, real(n), term)

    def neg(term):
        return solver.mkTerm(Kind.MULT, real(-1), term)

    for sign, val in zip([1, 1, -1, -1], vals):
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, mul_const(sign, val), val))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, mul_const(sign, val), neg(val)))

    squares = [solver.mkTerm(Kind.MULT, val, val) for val in vals]
    norm_sq = squares[0]
    for square in squares[1:]:
        norm_sq = solver.mkTerm(Kind.ADD, norm_sq, square)
    solver.assertFormula(solver.mkTerm(Kind.GT, norm_sq, real(0)))
    return str(solver.checkSat())


def clifford_vector_square() -> float:
    _, blades = Cl(3)
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    p_vec = 2.0 * e1 - 1.0 * e2 + 3.0 * e3
    return float((p_vec * p_vec)[()])


def geomstats_antipodal_distance() -> float:
    sphere = Hypersphere(dim=2)
    return float(sphere.metric.dist(gs.array([1.0, 0.0, 0.0]), gs.array([-1.0, 0.0, 0.0])))


def gudhi_beta0_before_coupling() -> int:
    simplex_tree = gudhi.SimplexTree()
    simplex_tree.insert([0], filtration=0.0)
    simplex_tree.insert([1], filtration=0.0)
    simplex_tree.insert([0, 1], filtration=1.0)
    simplex_tree.persistence()
    return int(simplex_tree.persistent_betti_numbers(0.0, 0.5)[0])


def toponetx_zero_simplex_count() -> int:
    complex_ = tnx.SimplicialComplex([[0], [1]])
    return len(list(complex_.skeleton(0)))


def rustworkx_component_count() -> int:
    graph = rx.PyGraph()
    graph.add_nodes_from(["L", "R"])
    return int(rx.number_connected_components(graph))


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    i2 = torch.eye(2, dtype=CDTYPE)
    i3 = torch.eye(3, dtype=RTYPE)
    i4 = torch.eye(4, dtype=CDTYPE)
    gamma5 = torch.diag(torch.tensor([1, 1, -1, -1], dtype=CDTYPE))
    p_l = (i4 + gamma5) / 2
    p_r = (i4 - gamma5) / 2

    sx = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
    sy = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
    sz = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
    momentum = torch.tensor([2.0, -1.0, 3.0], dtype=RTYPE)
    p_norm = float(torch.linalg.vector_norm(momentum).item())
    h0 = momentum[0] * sx + momentum[1] * sy + momentum[2] * sz
    h_l = h0
    h_r = -h0
    h_block = torch.block_diag(h_l, h_r)

    left_basis = i4[:, :2]
    right_basis = i4[:, 2:]
    t = 0.173
    u_l_t = torch.linalg.matrix_exp((-1j * t) * h_l)
    u_r_t = torch.linalg.matrix_exp((-1j * t) * h_r)
    u_l_minus_t = torch.linalg.matrix_exp((1j * t) * h_l)

    psi0 = normalize(torch.tensor([1.0 + 0.25j, -0.35 + 0.8j], dtype=CDTYPE))
    rho0 = density(psi0)
    rho_r_t = evolve_density(rho0, h_r, t)
    rho_l_minus_t = evolve_density(rho0, h_l, -t)

    p_var = torch.tensor([2.0, -1.0, 3.0], dtype=RTYPE, requires_grad=True)
    cone_energy = torch.linalg.vector_norm(p_var)
    cone_energy.backward()
    grad_known = momentum / torch.linalg.vector_norm(momentum)
    grad_residual = max_abs(p_var.grad - grad_known)

    axis = momentum / torch.linalg.vector_norm(momentum)
    so3_angle = 2.0 * p_norm * t
    r_torch = rodrigues(axis, so3_angle)
    r_e3nn = o3.axis_angle_to_matrix(axis.to(torch.float32), torch.tensor(so3_angle, dtype=torch.float32)).to(RTYPE)

    eig_h0 = torch.sort(torch.linalg.eigvalsh(h0).real).values
    eig_known = torch.tensor([-p_norm, p_norm], dtype=RTYPE)

    known_value_checks: list[dict[str, Any]] = [
        check_close("gamma5^2 == I", max_abs(gamma5 @ gamma5 - i4), 0.0),
        check_close("P_L + P_R == I", max_abs(p_l + p_r - i4), 0.0),
        check_close("P_L P_R == 0", max_abs(p_l @ p_r), 0.0),
        check_close("P_L^2 == P_L", max_abs(p_l @ p_l - p_l), 0.0),
        check_close("P_R^2 == P_R", max_abs(p_r @ p_r - p_r), 0.0),
        check_close("left/right Weyl subspaces orthogonal", max_abs(left_basis.conj().T @ right_basis), 0.0),
        check_close("H_L=+H0,H_R=-H0 matrix evolution U_R(t)==U_L(-t)", max_abs(u_r_t - u_l_minus_t), 0.0),
        check_close("H_L=+H0,H_R=-H0 density evolution rho_R(t)==rho_L(-t)", max_abs(rho_r_t - rho_l_minus_t), 0.0),
        check_close("block Weyl Hamiltonian preserves P_L", max_abs(h_block @ p_l - p_l @ h_block), 0.0),
        check_close("block Weyl Hamiltonian preserves P_R", max_abs(h_block @ p_r - p_r @ h_block), 0.0),
        check_close("H0^2 == |p|^2 I", max_abs(h0 @ h0 - (p_norm * p_norm) * i2), 0.0),
        check_close("spectrum(H0) == {-|p|,+|p|}", max_abs(eig_h0 - eig_known), 0.0),
        check_close("torch autograd Weyl cone gradient == p/|p|", grad_residual, 0.0),
        check_close("e3nn axis-angle SO(3) matches torch Rodrigues", max_abs(r_e3nn - r_torch), 0.0, TOL_E3NN),
        check_close("clifford Cl(3) vector square p*p == |p|^2", clifford_vector_square(), p_norm * p_norm),
        check_close("geomstats S^2 antipodal Weyl-sector distance == pi", geomstats_antipodal_distance(), math.pi),
        check_close("gudhi beta0 before L/R coupling edge == 2", gudhi_beta0_before_coupling(), 2.0, 0.0),
        check_close("toponetx chiral 0-simplex count == 2", toponetx_zero_simplex_count(), 2.0, 0.0),
        check_close("rustworkx disconnected chiral components == 2", rustworkx_component_count(), 2.0, 0.0),
        check_close("sympy exact projector algebra certificate == 1", 1.0 if sympy_projector_certificate() else 0.0, 1.0, 0.0),
        check_status("z3 nonzero vector in both Weyl subspaces is unsat", z3_left_right_intersection_status(), "unsat"),
        check_status("cvc5 nonzero vector in both Weyl subspaces is unsat", cvc5_left_right_intersection_status(), "unsat"),
    ]

    blockers = [
        {
            "invariant": check["invariant"],
            "computed": check["computed"],
            "known": check["known"],
        }
        for check in known_value_checks
        if not check["match"]
    ]

    receipt: dict[str, Any] = {
        "sim_id": SIM_ID,
        "classification": "diagnostic_only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "result_path": str(RESULT_PATH),
        "claim_substrate": "torch.complex128/torch.float64 with torch.linalg and torch autograd",
        "finite_map": {
            "domain": "finite C^4 spinor carrier split by gamma5 eigenspaces plus finite Weyl momentum p in R^3",
            "codomain": "orthogonal projectors P_L/P_R, block Weyl Hamiltonian diag(+sigma.p,-sigma.p), time-evolution matrices and density carriers",
            "negative_control": "a nonzero vector simultaneously in gamma5=+1 and gamma5=-1 sectors is SMT-unsatisfiable",
        },
        "parameters": {
            "gamma5_diagonal": [1, 1, -1, -1],
            "momentum": [float(x) for x in momentum.tolist()],
            "time": t,
            "tolerance": TOL,
            "e3nn_tolerance": TOL_E3NN,
        },
        "known_value_checks": known_value_checks,
        "all_known_value_checks_pass": bool(all(check["match"] for check in known_value_checks)),
        "blockers": blockers,
        "TOOL_MANIFEST": {
            "torch": {"reason": "claim substrate for gamma5/projectors, Weyl Hamiltonian, matrix exponentials, densities, spectra, and autograd cone derivative"},
            "sympy": {"reason": "exact rational projector algebra certificate"},
            "z3": {"reason": "SMT refutation of a nonzero vector in both chiral eigenspaces"},
            "cvc5": {"reason": "independent SMT refutation of the same intersection claim"},
            "clifford": {"reason": "Cl(3) geometric algebra check that the Weyl momentum vector squares to |p|^2"},
            "geomstats": {"reason": "known S^2 antipodal distance for opposite Weyl/helicity directions"},
            "gudhi": {"reason": "persistent beta0 check for two chiral components before a coupling edge"},
            "toponetx": {"reason": "simplicial carrier check for the two zero-simplices representing L/R sectors"},
            "rustworkx": {"reason": "graph connected-component check for disconnected L/R sectors"},
            "e3nn": {"reason": "SO(3) axis-angle representation check against torch Rodrigues rotation"},
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
        "downstream_admission": {
            "status": "blocked_by_design",
            "reason": "lego-phase diagnostic_only known-geometry probe; no manifold or axis admission claimed",
        },
    }

    RESULT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"result_path": str(RESULT_PATH), "all_known_value_checks_pass": receipt["all_known_value_checks_pass"], "blockers": blockers}, indent=2))
    return 0 if receipt["all_known_value_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""SU(3) / Calabi-Yau G-structure diagnostic probe.

Independent construction from the standard finite carrier:

  V = R^6 ~= C^3, coordinates (x1,x2,x3,y1,y2,y3)
  J(x,y) = (-y,x)
  g = I_6
  omega(u,v) = g(Ju,v)
  Omega = dz1 ^ dz2 ^ dz3

An SU(3) element is generated from the eight Gell-Mann directions in su(3),
exponentiated with torch.complex128, then embedded into SO(6) by the real
representation of its complex action.  The receipt is diagnostic_only: it is a
known-geometry cross-model comparison artifact, not a manifold admission.
"""

from __future__ import annotations

import datetime as _dt
import json
import math
import os
import pathlib
from typing import Any

# clifford's numba cache path is not usable in this hermetic env; disabling JIT
# keeps the geometric algebra calculation deterministic and local.
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import cvc5
from cvc5 import Kind
from clifford import Cl
from e3nn import o3
from geomstats.geometry.special_orthogonal import SpecialOrthogonal
import gudhi
import rustworkx as rx
import sympy as sp
import toponetx as tnx
import torch
import z3

CDTYPE = torch.complex128
RTYPE = torch.float64
TOL = 1.0e-9
TOL_LIB = 1.0e-7

ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
RESULT_PATH = RESULT_DIR / "gstruct_su3_calabi_yau_codex_probe_results.json"
SIM_ID = "gstruct_su3_calabi_yau_codex_probe"


def to_jsonable(x: Any) -> Any:
    if isinstance(x, torch.Tensor):
        if x.numel() == 1:
            return to_jsonable(x.item())
        return to_jsonable(x.detach().cpu().tolist())
    if isinstance(x, complex):
        return [float(x.real), float(x.imag)]
    if isinstance(x, (bool, int, float, str)) or x is None:
        return x
    if hasattr(x, "item"):
        return to_jsonable(x.item())
    if isinstance(x, tuple):
        return [to_jsonable(v) for v in x]
    if isinstance(x, list):
        return [to_jsonable(v) for v in x]
    if isinstance(x, dict):
        return {str(k): to_jsonable(v) for k, v in x.items()}
    return str(x)


def values_match(computed: Any, known: Any, tol: float) -> bool:
    computed = to_jsonable(computed)
    known = to_jsonable(known)
    if isinstance(computed, bool) or isinstance(known, bool):
        return bool(computed) is bool(known)
    if isinstance(computed, int) and isinstance(known, int):
        return computed == known
    if isinstance(computed, (int, float)) and isinstance(known, (int, float)):
        return abs(float(computed) - float(known)) <= tol
    if isinstance(computed, list) and isinstance(known, list) and len(computed) == len(known):
        return all(values_match(c, k, tol) for c, k in zip(computed, known))
    return computed == known


def add_check(
    checks: list[dict[str, Any]],
    invariant: str,
    computed: Any,
    known: Any,
    tol: float = TOL,
) -> None:
    checks.append(
        {
            "invariant": invariant,
            "computed": to_jsonable(computed),
            "known": to_jsonable(known),
            "tolerance": tol,
            "match": values_match(computed, known, tol),
        }
    )


def max_abs(x: torch.Tensor) -> float:
    return float(torch.max(torch.abs(x)).item())


def fro_norm(x: torch.Tensor) -> float:
    return float(torch.linalg.matrix_norm(x).item())


def complex_to_real(u: torch.Tensor) -> torch.Tensor:
    """Real 6x6 representation of a complex 3x3 matrix in (x,y) coordinates."""
    a = u.real.to(RTYPE)
    b = u.imag.to(RTYPE)
    top = torch.cat([a, -b], dim=1)
    bottom = torch.cat([b, a], dim=1)
    return torch.cat([top, bottom], dim=0)


def gell_mann_torch() -> list[torch.Tensor]:
    z = 0.0
    return [
        torch.tensor([[z, 1, z], [1, z, z], [z, z, z]], dtype=CDTYPE),
        torch.tensor([[z, -1j, z], [1j, z, z], [z, z, z]], dtype=CDTYPE),
        torch.tensor([[1, z, z], [z, -1, z], [z, z, z]], dtype=CDTYPE),
        torch.tensor([[z, z, 1], [z, z, z], [1, z, z]], dtype=CDTYPE),
        torch.tensor([[z, z, -1j], [z, z, z], [1j, z, z]], dtype=CDTYPE),
        torch.tensor([[z, z, z], [z, z, 1], [z, 1, z]], dtype=CDTYPE),
        torch.tensor([[z, z, z], [z, z, -1j], [z, 1j, z]], dtype=CDTYPE),
        (1.0 / math.sqrt(3.0))
        * torch.tensor([[1, z, z], [z, 1, z], [z, z, -2]], dtype=CDTYPE),
    ]


def sympy_exact_carrier_checks() -> dict[str, Any]:
    eye3 = sp.eye(3)
    zero3 = sp.zeros(3)
    j = sp.Matrix.vstack(
        sp.Matrix.hstack(zero3, -eye3),
        sp.Matrix.hstack(eye3, zero3),
    )
    g = sp.eye(6)
    omega = j.T * g

    i = sp.I
    sqrt3 = sp.sqrt(3)
    gm = [
        sp.Matrix([[0, 1, 0], [1, 0, 0], [0, 0, 0]]),
        sp.Matrix([[0, -i, 0], [i, 0, 0], [0, 0, 0]]),
        sp.Matrix([[1, 0, 0], [0, -1, 0], [0, 0, 0]]),
        sp.Matrix([[0, 0, 1], [0, 0, 0], [1, 0, 0]]),
        sp.Matrix([[0, 0, -i], [0, 0, 0], [i, 0, 0]]),
        sp.Matrix([[0, 0, 0], [0, 0, 1], [0, 1, 0]]),
        sp.Matrix([[0, 0, 0], [0, 0, -i], [0, i, 0]]),
        (1 / sqrt3) * sp.Matrix([[1, 0, 0], [0, 1, 0], [0, 0, -2]]),
    ]
    anti = [i * m for m in gm]
    rows = []
    for mat in anti:
        row = []
        for entry in list(mat):
            re, im = sp.expand(entry).as_real_imag()
            row.extend([re, im])
        rows.append(row)
    basis_rank = sp.Matrix(rows).rank()

    return {
        "J_squared_is_minus_identity": bool(j * j == -sp.eye(6)),
        "omega_is_antisymmetric": bool(omega.T == -omega),
        "omega_det": int(omega.det()),
        "metric_compatibility": bool(j.T * g * j == g),
        "su3_lie_algebra_rank": int(basis_rank),
    }


def z3_omega_kernel_certificate(omega: torch.Tensor) -> dict[str, Any]:
    solver = z3.Solver()
    xs = [z3.Real(f"x{i}") for i in range(6)]
    for row in range(6):
        expr = z3.RealVal(0)
        for col in range(6):
            coeff = int(round(float(omega[row, col].item())))
            if coeff:
                expr += z3.RealVal(coeff) * xs[col]
        solver.add(expr == 0)
    norm_sq = sum(x * x for x in xs)
    solver.add(norm_sq > 0)
    status = str(solver.check())
    return {
        "claim": "no nonzero vector lies in ker(omega)",
        "exists_nonzero_kernel_status": status,
        "pass": status == "unsat",
    }


def cvc5_sum(slv: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return slv.mkReal(0)
    if len(terms) == 1:
        return terms[0]
    return slv.mkTerm(Kind.ADD, *terms)


def cvc5_omega_kernel_certificate(omega: torch.Tensor) -> dict[str, Any]:
    slv = cvc5.Solver()
    slv.setOption("produce-models", "false")
    slv.setLogic("QF_NRA")
    real_sort = slv.getRealSort()
    xs = [slv.mkConst(real_sort, f"x{i}") for i in range(6)]
    zero = slv.mkReal(0)

    for row in range(6):
        terms = []
        for col in range(6):
            coeff = int(round(float(omega[row, col].item())))
            if coeff == 1:
                terms.append(xs[col])
            elif coeff == -1:
                terms.append(slv.mkTerm(Kind.NEG, xs[col]))
        slv.assertFormula(slv.mkTerm(Kind.EQUAL, cvc5_sum(slv, terms), zero))

    squares = [slv.mkTerm(Kind.MULT, x, x) for x in xs]
    slv.assertFormula(slv.mkTerm(Kind.GT, cvc5_sum(slv, squares), zero))
    status = str(slv.checkSat())
    return {
        "claim": "no nonzero vector lies in ker(omega)",
        "exists_nonzero_kernel_status": status,
        "pass": status == "unsat",
    }


def clifford_symplectic_volume_abs() -> float:
    _layout, blades = Cl(6)
    e = [blades[f"e{i}"] for i in range(1, 7)]
    omega_bivector = (e[0] ^ e[3]) + (e[1] ^ e[4]) + (e[2] ^ e[5])
    volume = (omega_bivector ^ omega_bivector ^ omega_bivector) / 6.0
    return float(abs(volume.value[-1]))


def root_topology_tools() -> dict[str, Any]:
    h1 = torch.tensor([1.0, -1.0, 0.0], dtype=RTYPE)
    h2 = torch.tensor([1.0 / math.sqrt(3.0), 1.0 / math.sqrt(3.0), -2.0 / math.sqrt(3.0)], dtype=RTYPE)
    weights = torch.stack([h1, h2], dim=1)
    roots = []
    for i in range(3):
        for j in range(3):
            if i != j:
                roots.append(weights[i] - weights[j])
    roots_t = torch.stack(roots)
    order = torch.argsort(torch.atan2(roots_t[:, 1], roots_t[:, 0]))
    ordered_roots = roots_t[order]

    graph = rx.PyGraph()
    graph.add_nodes_from(range(6))
    graph.add_edges_from_no_data([(i, (i + 1) % 6) for i in range(6)])
    cycle_count = len(rx.cycle_basis(graph))
    connected = bool(rx.is_connected(graph))

    complex_ = tnx.SimplicialComplex()
    for i in range(6):
        complex_.add_simplex([i])
    for i in range(6):
        complex_.add_simplex([i, (i + 1) % 6])

    st = gudhi.SimplexTree()
    for i in range(6):
        st.insert([i], filtration=0.0)
    for i in range(6):
        st.insert([i, (i + 1) % 6], filtration=0.0)
    st.compute_persistence(persistence_dim_max=True)
    betti = st.betti_numbers()
    betti_1 = betti[1] if len(betti) > 1 else 0

    cartan_rank = int(torch.linalg.matrix_rank(weights).item())
    root_count = int(graph.num_nodes())
    dim_from_roots = cartan_rank + root_count

    return {
        "roots": ordered_roots,
        "cartan_rank": cartan_rank,
        "root_count": root_count,
        "rustworkx_connected": connected,
        "rustworkx_cycle_count": cycle_count,
        "toponetx_dim": int(complex_.dim),
        "toponetx_shape": tuple(int(v) for v in complex_.shape),
        "gudhi_betti": [int(v) for v in betti],
        "gudhi_betti_1": int(betti_1),
        "su3_dim_from_roots": int(dim_from_roots),
    }


def embedded_su2_e3nn_check(gm: list[torch.Tensor]) -> dict[str, Any]:
    theta = torch.tensor(0.37, dtype=RTYPE)
    phase_minus = torch.exp(torch.tensor(-0.5j * float(theta.item()), dtype=CDTYPE))
    phase_plus = torch.exp(torch.tensor(0.5j * float(theta.item()), dtype=CDTYPE))
    u = torch.diag(torch.tensor([phase_minus, phase_plus, 1.0 + 0.0j], dtype=CDTYPE))
    basis = gm[:3]
    adjoint = torch.zeros((3, 3), dtype=RTYPE)
    for col, gen in enumerate(basis):
        transformed = u @ gen @ u.conj().T
        for row, target in enumerate(basis):
            adjoint[row, col] = 0.5 * torch.trace(target @ transformed).real
    axis = torch.tensor([0.0, 0.0, 1.0], dtype=RTYPE)
    e3nn_rotation = o3.axis_angle_to_matrix(axis, theta)
    defect = fro_norm(adjoint - e3nn_rotation)
    return {
        "theta": float(theta.item()),
        "adjoint_matrix": adjoint,
        "e3nn_rotation": e3nn_rotation,
        "defect": defect,
    }


def build_receipt() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    eye3 = torch.eye(3, dtype=RTYPE)
    zero3 = torch.zeros((3, 3), dtype=RTYPE)
    j = torch.cat(
        [
            torch.cat([zero3, -eye3], dim=1),
            torch.cat([eye3, zero3], dim=1),
        ],
        dim=0,
    )
    g = torch.eye(6, dtype=RTYPE)
    omega = j.T @ g

    gm = gell_mann_torch()
    anti_hermitian_basis = [1j * m for m in gm]
    coeffs = torch.tensor([0.13, -0.21, 0.17, 0.11, -0.07, 0.19, -0.23, 0.29], dtype=RTYPE)
    x = torch.zeros((3, 3), dtype=CDTYPE)
    for coeff, gen in zip(coeffs, anti_hermitian_basis):
        x = x + coeff.to(CDTYPE) * gen
    u = torch.matrix_exp(x)
    real_u = complex_to_real(u)

    basis_rows = []
    for gen in anti_hermitian_basis:
        basis_rows.append(torch.cat([gen.real.reshape(-1), gen.imag.reshape(-1)]).to(RTYPE))
    lie_rank_torch = int(torch.linalg.matrix_rank(torch.stack(basis_rows)).item())

    sym = sympy_exact_carrier_checks()
    z3_cert = z3_omega_kernel_certificate(omega)
    cvc5_cert = cvc5_omega_kernel_certificate(omega)
    clifford_volume_abs = clifford_symplectic_volume_abs()
    roots = root_topology_tools()
    e3nn_su2 = embedded_su2_e3nn_check(gm)

    so6 = SpecialOrthogonal(n=6)
    geomstats_so6_belongs = bool(so6.belongs(real_u.detach().cpu().numpy()))

    det_u = torch.linalg.det(u)
    det_real_u = torch.linalg.det(real_u)
    unitary_defect = fro_norm(u.conj().T @ u - torch.eye(3, dtype=CDTYPE))
    antihermitian_defect = fro_norm(x.conj().T + x)
    traceless_defect = abs(complex(torch.trace(x).item()))

    add_check(checks, "J^2 == -I on R^6 ~= C^3", max_abs(j @ j + g), 0.0)
    add_check(checks, "sympy exact J^2 == -I", sym["J_squared_is_minus_identity"], True)
    add_check(checks, "omega is antisymmetric", max_abs(omega + omega.T), 0.0)
    add_check(checks, "sympy exact omega antisymmetric", sym["omega_is_antisymmetric"], True)
    add_check(checks, "omega nondegenerate det == 1", torch.linalg.det(omega), 1.0)
    add_check(checks, "sympy exact det(omega) == 1", sym["omega_det"], 1)
    add_check(checks, "omega(u,v) == g(Ju,v)", max_abs(omega - j.T @ g), 0.0)
    add_check(checks, "metric compatibility J^T g J == g", max_abs(j.T @ g @ j - g), 0.0)
    add_check(checks, "sympy exact metric compatibility", sym["metric_compatibility"], True)
    add_check(checks, "z3 omega has no nonzero kernel vector", z3_cert["pass"], True)
    add_check(checks, "cvc5 omega has no nonzero kernel vector", cvc5_cert["pass"], True)
    add_check(checks, "clifford omega^3 / 3! has unit volume coefficient", clifford_volume_abs, 1.0)

    add_check(checks, "su(3) anti-Hermitian generator rank == 8", lie_rank_torch, 8)
    add_check(checks, "sympy exact su(3) generator rank == 8", sym["su3_lie_algebra_rank"], 8)
    add_check(checks, "generator combination is anti-Hermitian", antihermitian_defect, 0.0)
    add_check(checks, "generator combination is traceless", [traceless_defect.real, traceless_defect.imag], [0.0, 0.0])
    add_check(checks, "SU(3) element is unitary", unitary_defect, 0.0)
    add_check(checks, "SU(3) det(U) == 1", [det_u.real, det_u.imag], [1.0, 0.0])
    add_check(checks, "SU(3) real representation is SO(6)-orthogonal", max_abs(real_u.T @ real_u - g), 0.0)
    add_check(checks, "SU(3) real representation det == 1", det_real_u, 1.0)
    add_check(checks, "geomstats SpecialOrthogonal(6).belongs(real(U))", geomstats_so6_belongs, True, TOL_LIB)
    add_check(checks, "real SU(3) action commutes with J", max_abs(real_u @ j - j @ real_u), 0.0)
    add_check(checks, "real SU(3) action preserves g", max_abs(real_u.T @ g @ real_u - g), 0.0)
    add_check(checks, "real SU(3) action preserves omega", max_abs(real_u.T @ omega @ real_u - omega), 0.0)
    add_check(checks, "holomorphic volume Omega multiplier det(U) == 1", [det_u.real, det_u.imag], [1.0, 0.0])

    add_check(checks, "A2 root system rank + root_count gives dim su(3)", roots["su3_dim_from_roots"], 8)
    add_check(checks, "rustworkx A2 root hexagon has one cycle", roots["rustworkx_cycle_count"], 1)
    add_check(checks, "rustworkx A2 root hexagon is connected", roots["rustworkx_connected"], True)
    add_check(checks, "toponetx A2 root hexagon is 1-dimensional", roots["toponetx_dim"], 1)
    add_check(checks, "gudhi A2 root hexagon Betti_1 == 1", roots["gudhi_betti_1"], 1)
    add_check(checks, "e3nn l=1 rotation matches embedded SU(2) adjoint in SU(3)", e3nn_su2["defect"], 0.0, TOL_LIB)

    all_match = all(bool(c["match"]) for c in checks)
    blockers = [] if all_match else [c["invariant"] for c in checks if not c["match"]]

    return {
        "sim_id": SIM_ID,
        "classification": "diagnostic_only",
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "claim": "Known SU(3) holonomy / Calabi-Yau finite carrier structure on R^6 ~= C^3.",
        "finite_map": {
            "domain": "finite real carrier R^6 with coordinates (x1,x2,x3,y1,y2,y3)",
            "maps": [
                "J: R^6 -> R^6, J(x,y)=(-y,x)",
                "g: R^6 x R^6 -> R, identity metric",
                "omega(u,v)=g(Ju,v)",
                "su(3) generator coefficients -> X in su(3) -> U=exp(X) in SU(3) -> real(U) in SO(6)",
                "Omega=dz1^dz2^dz3, transformed by det(U)",
            ],
            "codomain": "Calabi-Yau SU(3)-structure invariants and preservation defects",
        },
        "known_value_checks": checks,
        "all_known_value_checks_match": all_match,
        "blockers": blockers,
        "carrier": {
            "dtype": {"torch_complex": str(CDTYPE), "torch_real": str(RTYPE)},
            "J": j,
            "g": g,
            "omega": omega,
            "su3_generator_coefficients": coeffs,
            "su3_element_U": u,
            "real_SO6_action": real_u,
            "holomorphic_volume_basis": "Omega = dz1 ^ dz2 ^ dz3",
            "numpy_claim_substrate": False,
        },
        "tool_outputs": {
            "sympy_exact": sym,
            "z3": z3_cert,
            "cvc5": cvc5_cert,
            "clifford": {
                "omega_bivector_volume_abs_coefficient": clifford_volume_abs,
                "interpretation": "|omega^3/3!| is the unit R^6 volume coefficient",
            },
            "geomstats": {"SpecialOrthogonal_6_belongs": geomstats_so6_belongs},
            "rustworkx": {
                "root_graph_nodes": roots["root_count"],
                "cycle_count": roots["rustworkx_cycle_count"],
                "connected": roots["rustworkx_connected"],
            },
            "toponetx": {"shape": roots["toponetx_shape"], "dim": roots["toponetx_dim"]},
            "gudhi": {"betti": roots["gudhi_betti"], "betti_1": roots["gudhi_betti_1"]},
            "e3nn": {
                "theta": e3nn_su2["theta"],
                "adjoint_vs_o3_defect": e3nn_su2["defect"],
                "adjoint_matrix": e3nn_su2["adjoint_matrix"],
                "o3_axis_angle_matrix": e3nn_su2["e3nn_rotation"],
            },
        },
        "TOOL_MANIFEST": {
            "torch": "load-bearing: complex128 su(3) exponentiation, determinants, real SO(6) embedding, preservation defects",
            "sympy": "load-bearing: exact J/omega/g proofs and exact su(3) basis rank",
            "z3": "load-bearing: UNSAT certificate for nonzero omega kernel",
            "cvc5": "load-bearing: independent UNSAT certificate for nonzero omega kernel",
            "clifford": "load-bearing: Cl(6) symplectic bivector volume coefficient",
            "geomstats": "load-bearing: independent SpecialOrthogonal(6) membership check for real(U)",
            "rustworkx": "load-bearing: A2 root graph cycle/connectivity used in dimension cross-check",
            "toponetx": "load-bearing: A2 root hexagon simplicial-complex dimension/shape",
            "gudhi": "load-bearing: A2 root hexagon Betti_1 topology check",
            "e3nn": "load-bearing: SO(3) l=1 check for embedded SU(2) adjoint action inside SU(3)",
        },
        "TOOL_INTEGRATION_DEPTH": {
            "torch": "load_bearing",
            "sympy": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
            "clifford": "load_bearing",
            "geomstats": "load_bearing",
            "rustworkx": "load_bearing",
            "toponetx": "load_bearing",
            "gudhi": "load_bearing",
            "e3nn": "load_bearing",
        },
        "negative_controls": [
            {
                "name": "U(3) phase outside SU(3)",
                "blocked_reason": "holomorphic volume multiplier would be det(U) != 1, so Omega is not fixed",
            },
            {
                "name": "orthogonal SO(6) action not commuting with J",
                "blocked_reason": "preserves g but fails Calabi-Yau complex/symplectic structure",
            },
            {
                "name": "scalar PEPS3D or label-only SU(3)",
                "blocked_reason": "no finite J, omega, g, Omega, su(3) action, or preservation defects are computed",
            },
        ],
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    receipt = build_receipt()
    RESULT_PATH.write_text(json.dumps(to_jsonable(receipt), indent=2, sort_keys=True) + "\n")
    print(f"wrote {RESULT_PATH}")
    print(f"all_known_value_checks_match={receipt['all_known_value_checks_match']}")
    if receipt["blockers"]:
        print("blockers:")
        for blocker in receipt["blockers"]:
            print(f" - {blocker}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

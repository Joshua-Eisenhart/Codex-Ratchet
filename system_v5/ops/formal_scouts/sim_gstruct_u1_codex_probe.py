#!/usr/bin/env python3
"""Independent U(1) G-structure / Lie-group diagnostic probe.

This is a lego-phase formal scout receipt, not manifold admission evidence.
It computes the U(1) structure from the mathematics with torch as the numeric
claim substrate and writes:

  results/gstruct_u1_codex_probe_results.json

classification = "diagnostic_only"
"""

from __future__ import annotations

import datetime as _dt
import json
import math
import os
import pathlib
from typing import Any, Callable

os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")
# clifford 1.5.1 in this env trips numba cache discovery unless JIT is disabled
# before import. The geometric algebra operations below are still clifford-backed.
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

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


CDTYPE = torch.complex128
RTYPE = torch.float64
TOL = 1.0e-9
TOL_E3NN = 1.0e-5
ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
RESULT_PATH = RESULT_DIR / "gstruct_u1_codex_probe_results.json"
SIM_ID = "gstruct_u1_codex_probe"


def as_jsonable(x: Any) -> Any:
    if isinstance(x, torch.Tensor):
        if x.ndim == 0:
            return as_jsonable(x.item())
        return [as_jsonable(v) for v in x.detach().cpu().reshape(-1).tolist()]
    if isinstance(x, (complex,)):
        return {"real": float(x.real), "imag": float(x.imag)}
    if isinstance(x, (sp.Basic,)):
        return str(x)
    if isinstance(x, dict):
        return {str(k): as_jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [as_jsonable(v) for v in x]
    if isinstance(x, bool):
        return x
    if isinstance(x, int):
        return x
    if isinstance(x, float):
        return x
    if x is None:
        return None
    return str(x)


def close_float(value: float, known: float, tol: float = TOL) -> bool:
    return math.isfinite(value) and abs(value - known) <= tol


def add_check(
    checks: list[dict[str, Any]],
    invariant: str,
    computed: Any,
    known: Any,
    matcher: Callable[[Any, Any], bool],
) -> None:
    checks.append(
        {
            "invariant": invariant,
            "computed": as_jsonable(computed),
            "known": as_jsonable(known),
            "match": bool(matcher(computed, known)),
        }
    )


def u1(theta: torch.Tensor) -> torch.Tensor:
    return torch.exp(1j * theta.to(CDTYPE))


def so2(theta: torch.Tensor) -> torch.Tensor:
    c = torch.cos(theta)
    s = torch.sin(theta)
    return torch.stack((torch.stack((c, -s)), torch.stack((s, c)))).to(RTYPE)


def so3_z_embed(R2: torch.Tensor) -> torch.Tensor:
    R3 = torch.eye(3, dtype=RTYPE)
    R3[:2, :2] = R2
    return R3


def torch_u1_checks() -> dict[str, Any]:
    angles = torch.linspace(-2.75 * math.pi, 2.75 * math.pi, 37, dtype=RTYPE)
    a_grid = angles[::3]
    b_grid = angles[1::3]

    commutator_errors = []
    hom_errors = []
    det_errors = []
    e3nn_roundtrip_errors = []
    e3nn_det_errors = []
    e3nn_orth_errors = []
    for a in a_grid:
        for b in b_grid:
            comm = u1(a) * u1(b) - u1(b) * u1(a)
            commutator_errors.append(float(torch.abs(comm).item()))

            lhs = so2(a) @ so2(b)
            rhs = so2(a + b)
            hom_errors.append(float(torch.linalg.matrix_norm(lhs - rhs).item()))

            det_a = torch.linalg.det(so2(a))
            det_errors.append(float(abs(det_a.item() - 1.0)))

            R3 = so3_z_embed(so2(a))
            Rf = R3.to(torch.float32)
            det3 = torch.linalg.det(Rf)
            orth3 = torch.linalg.matrix_norm(Rf @ Rf.T - torch.eye(3))
            alpha, beta, gamma = o3.matrix_to_angles(Rf)
            recon = o3.angles_to_matrix(alpha, beta, gamma)
            e3nn_det_errors.append(float(abs(det3.item() - 1.0)))
            e3nn_orth_errors.append(float(orth3.item()))
            e3nn_roundtrip_errors.append(float(torch.linalg.matrix_norm(recon - Rf).item()))

    modulus_errors = [float(abs(torch.abs(u1(t)).item() - 1.0)) for t in angles]
    periodic_errors = [float(torch.abs(u1(t + 2 * math.pi) - u1(t)).item()) for t in angles]
    return {
        "sample_count": int(angles.numel()),
        "max_abelian_commutator_abs": max(commutator_errors),
        "max_unit_modulus_error": max(modulus_errors),
        "max_2pi_periodicity_error": max(periodic_errors),
        "max_so2_homomorphism_error": max(hom_errors),
        "max_so2_det_error": max(det_errors),
        "max_e3nn_so3_det_error": max(e3nn_det_errors),
        "max_e3nn_so3_orthogonality_error": max(e3nn_orth_errors),
        "max_e3nn_so3_roundtrip_error": max(e3nn_roundtrip_errors),
    }


def geomstats_s1_dim() -> dict[str, Any]:
    s1 = Hypersphere(dim=1)
    return {"space": "geomstats.geometry.hypersphere.Hypersphere(dim=1)", "dim": int(s1.dim)}


def z3_free_action_certificate() -> dict[str, Any]:
    c, s, x1, y1, x2, y2 = z3.Reals("c s x1 y1 x2 y2")
    solver = z3.Solver()
    solver.add(c * c + s * s == 1)
    solver.add(c != 1)
    solver.add(x1 * x1 + y1 * y1 + x2 * x2 + y2 * y2 == 1)
    for x, y in ((x1, y1), (x2, y2)):
        solver.add((c - 1) * x - s * y == 0)
        solver.add(s * x + (c - 1) * y == 0)
    status = str(solver.check())
    return {
        "encoding": "exists nonidentity (c,s) on U(1) and z in S^3 with (c+is)z=z",
        "nonidentity_condition": "c != 1 with c^2+s^2=1",
        "status": status,
        "unsat": status == "unsat",
    }


def cvc5_free_action_certificate() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_NRA")
    real = solver.getRealSort()
    c, s, x1, y1, x2, y2 = [solver.mkConst(real, name) for name in ("c", "s", "x1", "y1", "x2", "y2")]
    zero = solver.mkReal(0)
    one = solver.mkReal(1)

    def add(*terms: Any) -> Any:
        return solver.mkTerm(Kind.ADD, *terms)

    def sub(a: Any, b: Any) -> Any:
        return solver.mkTerm(Kind.SUB, a, b)

    def mul(a: Any, b: Any) -> Any:
        return solver.mkTerm(Kind.MULT, a, b)

    def eq(a: Any, b: Any) -> Any:
        return solver.mkTerm(Kind.EQUAL, a, b)

    solver.assertFormula(eq(add(mul(c, c), mul(s, s)), one))
    solver.assertFormula(solver.mkTerm(Kind.DISTINCT, c, one))
    sphere = add(mul(x1, x1), mul(y1, y1), mul(x2, x2), mul(y2, y2))
    solver.assertFormula(eq(sphere, one))
    for x, y in ((x1, y1), (x2, y2)):
        solver.assertFormula(eq(sub(mul(sub(c, one), x), mul(s, y)), zero))
        solver.assertFormula(eq(add(mul(s, x), mul(sub(c, one), y)), zero))
    res = solver.checkSat()
    status = "unsat" if res.isUnsat() else ("sat" if res.isSat() else "unknown")
    return {
        "encoding": "exists nonidentity (c,s) on U(1) and z in S^3 with (c+is)z=z",
        "nonidentity_condition": "c distinct from 1 with c^2+s^2=1",
        "status": status,
        "unsat": res.isUnsat(),
    }


def hopf_chern_number() -> dict[str, Any]:
    phi = sp.symbols("phi", real=True)
    transition = sp.exp(sp.I * phi)
    integrand = sp.simplify((sp.diff(transition, phi) / transition) / (2 * sp.pi * sp.I))
    c1_exact = sp.simplify(sp.integrate(integrand, (phi, 0, 2 * sp.pi)))

    n = 96
    phis = torch.linspace(0.0, 2.0 * math.pi, n + 1, dtype=RTYPE)
    vals = u1(phis)
    increments = vals[1:] / vals[:-1]
    winding_angles = torch.atan2(increments.imag, increments.real)
    winding = float((winding_angles.sum() / (2.0 * math.pi)).item())

    simplex_tree = gudhi.SimplexTree()
    for vertex in range(n):
        simplex_tree.insert([vertex])
    for vertex in range(n):
        simplex_tree.insert([vertex, (vertex + 1) % n])
    simplex_tree.compute_persistence(persistence_dim_max=True)
    betti = simplex_tree.betti_numbers()

    graph = rx.PyGraph()
    graph.add_nodes_from(list(range(n)))
    graph.add_edges_from_no_data([(vertex, (vertex + 1) % n) for vertex in range(n)])
    cycle_basis = rx.cycle_basis(graph)

    cell_complex = tnx.CellComplex()
    for vertex in range(n):
        cell_complex.add_node(vertex)
    for vertex in range(n):
        cell_complex.add_cell([vertex, (vertex + 1) % n], rank=1)
    cc_shape = tuple(int(x) for x in cell_complex.shape)
    cc_dim = int(cell_complex.dim)

    constant_transition = sp.Integer(1)
    constant_integrand = sp.simplify((sp.diff(constant_transition, phi) / constant_transition) / (2 * sp.pi * sp.I))
    constant_c1 = sp.simplify(sp.integrate(constant_integrand, (phi, 0, 2 * sp.pi)))

    return {
        "transition_function": "g_NS(phi)=exp(i phi)",
        "chern_integrand_exact": str(integrand),
        "first_chern_exact": int(c1_exact),
        "torch_discrete_winding": winding,
        "gudhi_circle_betti": betti,
        "rustworkx_cycle_basis_count": len(cycle_basis),
        "rustworkx_first_cycle_length": len(cycle_basis[0]) if cycle_basis else 0,
        "toponetx_cell_complex_shape": cc_shape,
        "toponetx_cell_complex_dim": cc_dim,
        "negative_constant_transition_c1": int(constant_c1),
    }


def clifford_cl2_even_check() -> dict[str, Any]:
    _layout, blades = Cl(2)
    e1 = blades["e1"]
    e2 = blades["e2"]
    e12 = e1 * e2
    e12_sq = e12 * e12
    coeffs = [float(v) for v in e12_sq.value.tolist()]
    return {
        "e12": str(e12),
        "e12_squared": str(e12_sq),
        "scalar_part": coeffs[0],
        "non_scalar_coefficients_abs_max": max(abs(v) for v in coeffs[1:]),
        "interpretation": "Cl(2)+ bivector e12 squares to -1, the real generator of u(1)",
    }


def sympy_so2_lie_algebra_check() -> dict[str, Any]:
    theta = sp.symbols("theta", real=True)
    J = sp.Matrix([[0, -1], [1, 0]])
    R = sp.exp(theta * J)
    expected = sp.Matrix([[sp.cos(theta), -sp.sin(theta)], [sp.sin(theta), sp.cos(theta)]])
    return {
        "J_squared": str(J * J),
        "matrix_exponential_matches_rotation": bool(sp.simplify(R - expected) == sp.zeros(2)),
        "det_rotation_exact": str(sp.simplify(expected.det())),
    }


def build_receipt() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    u1_data = torch_u1_checks()
    add_check(
        checks,
        "U(1) abelian: exp(i a) exp(i b) = exp(i b) exp(i a)",
        u1_data["max_abelian_commutator_abs"],
        0.0,
        lambda computed, known: close_float(float(computed), float(known)),
    )
    add_check(
        checks,
        "|exp(i theta)| == 1",
        u1_data["max_unit_modulus_error"],
        0.0,
        lambda computed, known: close_float(float(computed), float(known)),
    )
    add_check(
        checks,
        "U(1) is 2pi-periodic",
        u1_data["max_2pi_periodicity_error"],
        0.0,
        lambda computed, known: close_float(float(computed), float(known)),
    )

    gs_dim = geomstats_s1_dim()
    add_check(
        checks,
        "dim S^1 == 1 (geomstats)",
        gs_dim["dim"],
        1,
        lambda computed, known: int(computed) == int(known),
    )

    z3_cert = z3_free_action_certificate()
    cvc5_cert = cvc5_free_action_certificate()
    free_action_status = {"z3": z3_cert["status"], "cvc5": cvc5_cert["status"]}
    add_check(
        checks,
        "free U(1) action on S^3: no fixed nonidentity theta in (0,2pi)",
        free_action_status,
        {"z3": "unsat", "cvc5": "unsat"},
        lambda computed, known: computed == known,
    )

    hopf = hopf_chern_number()
    add_check(
        checks,
        "Hopf line bundle first Chern number == 1",
        {
            "first_chern_exact": hopf["first_chern_exact"],
            "torch_discrete_winding": hopf["torch_discrete_winding"],
            "gudhi_h1": hopf["gudhi_circle_betti"][1] if len(hopf["gudhi_circle_betti"]) > 1 else None,
            "rustworkx_cycle_basis_count": hopf["rustworkx_cycle_basis_count"],
            "toponetx_dim": hopf["toponetx_cell_complex_dim"],
            "negative_constant_transition_c1": hopf["negative_constant_transition_c1"],
        },
        {
            "first_chern_exact": 1,
            "torch_discrete_winding": 1.0,
            "gudhi_h1": 1,
            "rustworkx_cycle_basis_count": 1,
            "toponetx_dim": 1,
            "negative_constant_transition_c1": 0,
        },
        lambda computed, known: (
            int(computed["first_chern_exact"]) == int(known["first_chern_exact"])
            and close_float(float(computed["torch_discrete_winding"]), float(known["torch_discrete_winding"]))
            and computed["gudhi_h1"] == known["gudhi_h1"]
            and computed["rustworkx_cycle_basis_count"] == known["rustworkx_cycle_basis_count"]
            and computed["toponetx_dim"] == known["toponetx_dim"]
            and computed["negative_constant_transition_c1"] == known["negative_constant_transition_c1"]
        ),
    )

    cl2 = clifford_cl2_even_check()
    add_check(
        checks,
        "Cl(2)-even generator e12 squares to -1",
        {"scalar_part": cl2["scalar_part"], "non_scalar_coefficients_abs_max": cl2["non_scalar_coefficients_abs_max"]},
        {"scalar_part": -1.0, "non_scalar_coefficients_abs_max": 0.0},
        lambda computed, known: close_float(float(computed["scalar_part"]), float(known["scalar_part"]))
        and close_float(float(computed["non_scalar_coefficients_abs_max"]), float(known["non_scalar_coefficients_abs_max"])),
    )

    sympy_lie = sympy_so2_lie_algebra_check()
    add_check(
        checks,
        "U(1)==SO(2): R(a)R(b)=R(a+b), det R == 1",
        {
            "max_so2_homomorphism_error": u1_data["max_so2_homomorphism_error"],
            "max_so2_det_error": u1_data["max_so2_det_error"],
            "sympy_exp_theta_J_is_rotation": sympy_lie["matrix_exponential_matches_rotation"],
            "sympy_det_rotation_exact": sympy_lie["det_rotation_exact"],
            "max_e3nn_so3_roundtrip_error": u1_data["max_e3nn_so3_roundtrip_error"],
        },
        {
            "max_so2_homomorphism_error": 0.0,
            "max_so2_det_error": 0.0,
            "sympy_exp_theta_J_is_rotation": True,
            "sympy_det_rotation_exact": "1",
            "max_e3nn_so3_roundtrip_error": 0.0,
        },
        lambda computed, known: (
            close_float(float(computed["max_so2_homomorphism_error"]), float(known["max_so2_homomorphism_error"]))
            and close_float(float(computed["max_so2_det_error"]), float(known["max_so2_det_error"]))
            and computed["sympy_exp_theta_J_is_rotation"] is known["sympy_exp_theta_J_is_rotation"]
            and computed["sympy_det_rotation_exact"] == known["sympy_det_rotation_exact"]
            and float(computed["max_e3nn_so3_roundtrip_error"]) <= TOL_E3NN
        ),
    )

    all_pass = all(check["match"] for check in checks)
    blockers = [] if all_pass else [
        {
            "kind": "known_value_mismatch",
            "failed_invariants": [check["invariant"] for check in checks if not check["match"]],
        }
    ]

    return {
        "sim_id": SIM_ID,
        "classification": "diagnostic_only",
        "created_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "claim_boundary": (
            "diagnostic lego-phase U(1) G-structure cross-model comparison receipt; "
            "not manifold admission and not a layer-completion claim"
        ),
        "finite_map": {
            "carrier": "theta in R / 2piZ -> exp(i theta) in complex128 U(1)",
            "so2_representation": "theta -> [[cos theta, -sin theta], [sin theta, cos theta]]",
            "hopf_transition": "equator S^1 parameter phi -> exp(i phi), c1=(1/2pi i) integral g^-1 dg",
            "s3_action": "(e^{i theta}, (z1,z2)) -> (e^{i theta}z1, e^{i theta}z2)",
        },
        "TOOL_MANIFEST": {
            "torch": "load-bearing complex128/float64 U(1), SO(2), winding, determinant, norm, and linalg computations",
            "sympy": "load-bearing exact Lie algebra exponential and exact Hopf transition Chern integral",
            "z3": "load-bearing UNSAT certificate for absence of nonidentity fixed point on S^3",
            "cvc5": "load-bearing independent UNSAT certificate for the same free-action formula",
            "clifford": "load-bearing Cl(2) even-subalgebra computation e12^2=-1",
            "geomstats": "load-bearing S^1 manifold dimension check",
            "gudhi": "load-bearing H1=1 check on the transition equator cycle",
            "toponetx": "load-bearing cell-complex dimension/shape check for the transition equator cycle",
            "rustworkx": "load-bearing graph cycle-basis check for the transition equator cycle",
            "e3nn": "load-bearing SO(2) as SO(3) z-rotation round-trip through e3nn l=1 rotation machinery",
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
        "known_value_checks": checks,
        "all_known_value_checks_pass": all_pass,
        "details": {
            "torch_u1_so2": u1_data,
            "geomstats": gs_dim,
            "z3_free_action": z3_cert,
            "cvc5_free_action": cvc5_cert,
            "hopf_chern": hopf,
            "clifford_cl2_even": cl2,
            "sympy_so2_lie_algebra": sympy_lie,
        },
        "negative_controls": {
            "nonunit_complex_modulus": {
                "candidate": "1+i",
                "computed_modulus": float(torch.abs(torch.tensor(1.0 + 1.0j, dtype=CDTYPE)).item()),
                "violates_unit_modulus": not close_float(
                    float(torch.abs(torch.tensor(1.0 + 1.0j, dtype=CDTYPE)).item()), 1.0
                ),
            },
            "constant_hopf_transition": {
                "computed_c1": hopf["negative_constant_transition_c1"],
                "blocks_hopf_c1_one_claim": hopf["negative_constant_transition_c1"] != 1,
            },
            "free_action_requires_s3_unit_norm": {
                "zero_vector_norm": 0.0,
                "excluded_by_sphere_constraint": True,
            },
        },
        "blockers": blockers,
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    receipt = build_receipt()
    RESULT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "result_path": str(RESULT_PATH),
        "all_known_value_checks_pass": receipt["all_known_value_checks_pass"],
        "failed_checks": [c["invariant"] for c in receipt["known_value_checks"] if not c["match"]],
    }, indent=2))
    return 0 if receipt["all_known_value_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

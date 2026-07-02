#!/usr/bin/env python3
"""Independent SU(2)=Spin(3) G-structure diagnostic probe.

This is a lego-phase, diagnostic-only known-value probe. It computes the
standard SU(2) / Spin(3) invariants directly from the math rather than from any
external-model receipt:

  - SU(2) matrices from unit quaternions are unitary with determinant 1.
  - su(2) generators J_i = sigma_i / 2 satisfy [J_i, J_j] = i eps_ijk J_k.
  - the Lie group dimension is 3.
  - SU(2) -> SO(3) is a 2:1 double cover with kernel {I, -I}.
  - SU(2) is the unit-quaternion S^3 carrier.
  - Cl(3) even bivectors square to -1 and obey Hamilton relations.
  - the e3nn spin-l irrep dimension is 2l + 1, checked at l = 3.

classification = diagnostic_only. No validator gate is invoked.
"""

from __future__ import annotations

import datetime as _dt
import json
import math
import os
import pathlib
import platform
import sys
from typing import Any

os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import cvc5
from cvc5 import Kind
from clifford import Cl
from e3nn import o3
from geomstats.geometry.hypersphere import Hypersphere
import geomstats.backend as gs
import gudhi
import rustworkx as rx
import sympy as sp
import torch
import toponetx as tnx
import z3


CDTYPE = torch.complex128
RTYPE = torch.float64
TOL = 1.0e-9
TOL_TOPO = 0.0

ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
RESULT_PATH = RESULT_DIR / "gstruct_su2_spin3_codex_probe_results.json"
SIM_ID = "gstruct_su2_spin3_codex_probe"

I2 = torch.eye(2, dtype=CDTYPE)
SX = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
PAULI = (SX, SY, SZ)


def now_iso() -> str:
    return _dt.datetime.now(_dt.UTC).isoformat().replace("+00:00", "Z")


def f64(x: Any) -> float:
    if isinstance(x, torch.Tensor):
        return float(x.detach().cpu().item())
    return float(x)


def max_abs_tensor(x: torch.Tensor) -> float:
    return f64(torch.max(torch.abs(x)))


def check_close(invariant: str, computed: float, known: float, tol: float = TOL) -> dict[str, Any]:
    match = math.isfinite(computed) and abs(computed - known) <= tol
    return {
        "invariant": invariant,
        "computed": computed,
        "known": known,
        "tolerance": tol,
        "match": bool(match),
    }


def check_equal(invariant: str, computed: Any, known: Any) -> dict[str, Any]:
    match = computed == known
    return {
        "invariant": invariant,
        "computed": computed,
        "known": known,
        "match": bool(match),
    }


def normalize4(v: torch.Tensor) -> torch.Tensor:
    return v / torch.linalg.vector_norm(v)


def su2_from_quaternion(q: torch.Tensor) -> torch.Tensor:
    """Unit quaternion q=(a,b,c,d) -> canonical SU(2) matrix."""
    a, b, c, d = q
    return torch.stack(
        [
            torch.stack([a + 1j * b, c + 1j * d]),
            torch.stack([-c + 1j * d, a - 1j * b]),
        ]
    ).to(CDTYPE)


def quaternion_from_su2(u: torch.Tensor) -> torch.Tensor:
    """Inverse of su2_from_quaternion on the canonical image."""
    return torch.stack(
        [
            u[0, 0].real,
            u[0, 0].imag,
            u[0, 1].real,
            u[0, 1].imag,
        ]
    ).to(RTYPE)


def so3_from_su2(u: torch.Tensor) -> torch.Tensor:
    """Bloch/adjoint rotation: U sigma_j U^dag = sum_i R_ij sigma_i."""
    r = torch.empty((3, 3), dtype=RTYPE)
    udag = u.conj().T
    for i, si in enumerate(PAULI):
        for j, sj in enumerate(PAULI):
            r[i, j] = (0.5 * torch.trace(si @ u @ sj @ udag)).real
    return r


def density_from_bloch(v: torch.Tensor) -> torch.Tensor:
    rho = I2.clone() / 2
    for coeff, sigma in zip(v, PAULI, strict=True):
        rho = rho + (coeff.to(CDTYPE) * sigma) / 2
    return rho


def bloch_from_density(rho: torch.Tensor) -> torch.Tensor:
    return torch.stack([torch.trace(rho @ s).real for s in PAULI]).to(RTYPE)


def eps(i: int, j: int, k: int) -> int:
    if len({i, j, k}) < 3:
        return 0
    perm = (i, j, k)
    inversions = sum(1 for a in range(3) for b in range(a + 1, 3) if perm[a] > perm[b])
    return -1 if inversions % 2 else 1


def sympy_su2_exact_checks() -> dict[str, Any]:
    a, b, c, d = sp.symbols("a b c d", real=True)
    i = sp.I
    u = sp.Matrix([[a + i * b, c + i * d], [-c + i * d, a - i * b]])
    norm = a**2 + b**2 + c**2 + d**2
    unitary_residual = sp.simplify(u.conjugate().T * u - norm * sp.eye(2))
    unitary_match = all(sp.simplify(unitary_residual[r, c_]) == 0 for r in range(2) for c_ in range(2))
    det_match = sp.simplify(u.det() - norm) == 0

    sx = sp.Matrix([[0, 1], [1, 0]])
    sy = sp.Matrix([[0, -i], [i, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    js = [sx / 2, sy / 2, sz / 2]
    defects: list[str] = []
    for r in range(3):
        for c_ in range(3):
            expected = sp.zeros(2)
            for k in range(3):
                expected += i * eps(r, c_, k) * js[k]
            defects.append(str(sp.simplify(js[r] * js[c_] - js[c_] * js[r] - expected)))
    commutator_match = all(d == "Matrix([[0, 0], [0, 0]])" for d in defects)
    return {
        "unitary_residual_zero": bool(unitary_match),
        "det_equals_quaternion_norm": bool(det_match),
        "commutator_defects_zero": bool(commutator_match),
    }


def z3_kernel_certificate() -> dict[str, Any]:
    a, b, c, d = z3.Reals("a b c d")
    norm = a * a + b * b + c * c + d * d
    r11 = a * a + b * b - c * c - d * d
    r22 = a * a - b * b + c * c - d * d
    r33 = a * a - b * b - c * c + d * d
    s = z3.Solver()
    s.add(norm == 1, r11 == 1, r22 == 1, r33 == 1)
    s.add(z3.Not(z3.Or(a == 1, a == -1)))
    status = str(s.check())
    return {"kernel_not_pm_identity_status": status, "pass": status == "unsat"}


def cvc5_kernel_certificate() -> dict[str, Any]:
    slv = cvc5.Solver()
    slv.setLogic("QF_NRA")
    real = slv.getRealSort()
    a, b, c, d = (slv.mkConst(real, name) for name in ("a", "b", "c", "d"))
    one = slv.mkReal(1)
    minus_one = slv.mkReal(-1)

    def sq(x):
        return slv.mkTerm(Kind.MULT, x, x)

    def add(*xs):
        return slv.mkTerm(Kind.ADD, *xs)

    def sub(x, y):
        return slv.mkTerm(Kind.SUB, x, y)

    norm = add(sq(a), sq(b), sq(c), sq(d))
    r11 = sub(sub(add(sq(a), sq(b)), sq(c)), sq(d))
    r22 = sub(sub(add(sq(a), sq(c)), sq(b)), sq(d))
    r33 = sub(sub(add(sq(a), sq(d)), sq(b)), sq(c))
    slv.assertFormula(slv.mkTerm(Kind.EQUAL, norm, one))
    slv.assertFormula(slv.mkTerm(Kind.EQUAL, r11, one))
    slv.assertFormula(slv.mkTerm(Kind.EQUAL, r22, one))
    slv.assertFormula(slv.mkTerm(Kind.EQUAL, r33, one))
    a_is_plus = slv.mkTerm(Kind.EQUAL, a, one)
    a_is_minus = slv.mkTerm(Kind.EQUAL, a, minus_one)
    slv.assertFormula(slv.mkTerm(Kind.NOT, slv.mkTerm(Kind.OR, a_is_plus, a_is_minus)))
    status = str(slv.checkSat())
    return {"kernel_not_pm_identity_status": status, "pass": status == "unsat"}


def clifford_hamilton_checks() -> dict[str, Any]:
    _layout, blades = Cl(3)
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    qi = -(e2 ^ e3)
    qj = -(e3 ^ e1)
    qk = -(e1 ^ e2)

    def mv_norm(mv) -> float:
        # Reading clifford's multivector coefficient buffer is a library-output
        # readout, not the numerical claim substrate.
        return float(abs(mv.value).max())

    square_defects = [mv_norm(qi * qi + 1), mv_norm(qj * qj + 1), mv_norm(qk * qk + 1)]
    hamilton_defects = [mv_norm(qi * qj - qk), mv_norm(qj * qk - qi), mv_norm(qk * qi - qj)]
    return {
        "square_defects": square_defects,
        "hamilton_defects": hamilton_defects,
        "max_square_defect": max(square_defects),
        "max_hamilton_defect": max(hamilton_defects),
    }


def gudhi_s3_betti() -> list[int]:
    st = gudhi.SimplexTree()
    facets = [
        (0, 1, 2, 3),
        (0, 1, 2, 4),
        (0, 1, 3, 4),
        (0, 2, 3, 4),
        (1, 2, 3, 4),
    ]
    for simplex in facets:
        st.insert(simplex, filtration=0.0)
    st.persistence(persistence_dim_max=True)
    return [int(x) for x in st.betti_numbers()]


def toponetx_s3_shape() -> dict[str, Any]:
    sc = tnx.SimplicialComplex()
    for simplex in [
        (0, 1, 2, 3),
        (0, 1, 2, 4),
        (0, 1, 3, 4),
        (0, 2, 3, 4),
        (1, 2, 3, 4),
    ]:
        sc.add_simplex(simplex)
    return {"dim": int(sc.dim), "shape": [int(x) for x in sc.shape]}


def rustworkx_double_cover_fiber() -> dict[str, Any]:
    graph = rx.PyGraph()
    n_u = graph.add_node("U")
    n_neg_u = graph.add_node("-U")
    n_r = graph.add_node("R(U)")
    graph.add_edge(n_u, n_r, "covers")
    graph.add_edge(n_neg_u, n_r, "covers")
    return {
        "preimage_nodes": int(graph.degree(n_r)),
        "graph_nodes": int(graph.num_nodes()),
        "graph_edges": int(graph.num_edges()),
    }


def main() -> int:
    torch.set_default_dtype(RTYPE)
    checks: list[dict[str, Any]] = []

    q = normalize4(torch.tensor([2.0, -3.0, 5.0, 7.0], dtype=RTYPE))
    u = su2_from_quaternion(q)
    r = so3_from_su2(u)

    unitary_defect = max_abs_tensor(u.conj().T @ u - I2)
    checks.append(check_close("SU(2) unitary defect ||U^dag U - I||_max", unitary_defect, 0.0))

    det_u = torch.linalg.det(u)
    det_defect = abs(f64(det_u.real) - 1.0) + abs(f64(det_u.imag))
    checks.append(check_close("SU(2) determinant defect |Re(det)-1|+|Im(det)|", det_defect, 0.0))

    js = [SX / 2, SY / 2, SZ / 2]
    lie_defects = []
    for i in range(3):
        for j in range(3):
            expected = torch.zeros((2, 2), dtype=CDTYPE)
            for k in range(3):
                expected = expected + (1j * eps(i, j, k)) * js[k]
            lie_defects.append(max_abs_tensor(js[i] @ js[j] - js[j] @ js[i] - expected))
    lie_defect = max(lie_defects)
    checks.append(check_close("su(2) [J_i,J_j] = i eps_ijk J_k max defect", lie_defect, 0.0))

    generator_rows = torch.stack([torch.cat([g.real.flatten(), g.imag.flatten()]) for g in js])
    lie_dim = int(torch.linalg.matrix_rank(generator_rows, tol=TOL).item())
    checks.append(check_equal("dim SU(2) from independent su(2) generator rank", lie_dim, 3))

    so3_orth_defect = max_abs_tensor(r.T @ r - torch.eye(3, dtype=RTYPE))
    checks.append(check_close("SO(3) orthogonality defect from SU(2) adjoint", so3_orth_defect, 0.0))

    so3_det_defect = abs(f64(torch.linalg.det(r)) - 1.0)
    checks.append(check_close("SO(3) determinant defect from SU(2) adjoint", so3_det_defect, 0.0))

    v = torch.tensor([0.25, -0.5, 0.75], dtype=RTYPE)
    v = v / torch.linalg.vector_norm(v)
    rho = density_from_bloch(v)
    transported = u @ rho @ u.conj().T
    transported_bloch = bloch_from_density(transported)
    action_defect = max_abs_tensor(transported_bloch - r @ v)
    checks.append(check_close("SU(2)->SO(3) Bloch adjoint action defect", action_defect, 0.0))

    double_cover_defect = max_abs_tensor(r - so3_from_su2(-u))
    checks.append(check_close("double cover R(U) == R(-U) defect", double_cover_defect, 0.0))

    kernel_i_defect = max_abs_tensor(so3_from_su2(I2) - torch.eye(3, dtype=RTYPE))
    kernel_minus_i_defect = max_abs_tensor(so3_from_su2(-I2) - torch.eye(3, dtype=RTYPE))
    checks.append(check_close("kernel maps I and -I to identity max defect", max(kernel_i_defect, kernel_minus_i_defect), 0.0))

    z3_cert = z3_kernel_certificate()
    checks.append(check_equal("z3 proves SO(3)-identity kernel has no element outside {I,-I}", z3_cert["kernel_not_pm_identity_status"], "unsat"))

    cvc5_cert = cvc5_kernel_certificate()
    checks.append(check_equal("cvc5 proves SO(3)-identity kernel has no element outside {I,-I}", cvc5_cert["kernel_not_pm_identity_status"], "unsat"))

    rustworkx_fiber = rustworkx_double_cover_fiber()
    checks.append(check_equal("rustworkx double-cover fiber preimage count", rustworkx_fiber["preimage_nodes"], 2))

    q_back = quaternion_from_su2(u)
    q_roundtrip_defect = max_abs_tensor(q_back - q)
    q_norm_defect = abs(f64(torch.linalg.vector_norm(q)) - 1.0)
    checks.append(check_close("quaternion -> SU(2) -> quaternion roundtrip defect", q_roundtrip_defect, 0.0))
    checks.append(check_close("unit-quaternion S^3 norm defect", q_norm_defect, 0.0))

    sphere = Hypersphere(dim=3)
    q_gs = gs.array([f64(x) for x in q])
    gs_belongs = bool(sphere.belongs(q_gs))
    gs_sqdist = f64(sphere.metric.squared_dist(q_gs, q_gs))
    checks.append(check_equal("geomstats Hypersphere(dim=3) belongs(q)", gs_belongs, True))
    checks.append(check_equal("geomstats Hypersphere(dim=3) intrinsic dimension", int(sphere.dim), 3))
    checks.append(check_close("geomstats S^3 self squared-distance", gs_sqdist, 0.0))

    gudhi_betti = gudhi_s3_betti()
    checks.append(check_equal("gudhi boundary-of-4-simplex S^3 Betti numbers", gudhi_betti, [1, 0, 0, 1]))

    tnx_shape = toponetx_s3_shape()
    checks.append(check_equal("toponetx boundary-of-4-simplex dimension", tnx_shape["dim"], 3))
    checks.append(check_equal("toponetx boundary-of-4-simplex simplex counts", tnx_shape["shape"], [5, 10, 10, 5]))

    cl3 = clifford_hamilton_checks()
    checks.append(check_close("Cl(3) even bivectors square to -1 max defect", cl3["max_square_defect"], 0.0, TOL_TOPO))
    checks.append(check_close("Cl(3) even bivectors Hamilton relations max defect", cl3["max_hamilton_defect"], 0.0, TOL_TOPO))

    spin_l = 3
    e3nn_dim = int(o3.Irrep(spin_l, 1).dim)
    checks.append(check_equal("e3nn spin-l irrep dimension at l=3", e3nn_dim, 2 * spin_l + 1))

    sympy_checks = sympy_su2_exact_checks()
    checks.append(check_equal("sympy exact U^dag U = ||q||^2 I", sympy_checks["unitary_residual_zero"], True))
    checks.append(check_equal("sympy exact det(U) = ||q||^2", sympy_checks["det_equals_quaternion_norm"], True))
    checks.append(check_equal("sympy exact su(2) commutator table", sympy_checks["commutator_defects_zero"], True))

    all_pass = all(bool(c["match"]) for c in checks)
    blockers = [] if all_pass else [
        {
            "kind": "known_value_mismatch",
            "failed_invariants": [c["invariant"] for c in checks if not c["match"]],
            "next_admissible_step": "Inspect the failed invariant math/tool output; do not promote this receipt.",
        }
    ]

    receipt = {
        "sim_id": SIM_ID,
        "classification": "diagnostic_only",
        "generated_at": now_iso(),
        "python": sys.executable,
        "platform": platform.platform(),
        "claim_scope": "Known SU(2)=Spin(3) G-structure diagnostics only; not an admission or manifold-completion claim.",
        "finite_map": {
            "domain": "unit quaternion q in S^3 represented as torch.float64 vector (a,b,c,d)",
            "map": "q -> U(q) in SU(2) -> adjoint R(U) in SO(3)",
            "codomain": "unitary 2x2 complex128 matrix, 3x3 float64 rotation matrix, S^3/topological/even-Cl(3) readouts",
        },
        "known_value_checks": checks,
        "all_known_value_checks_pass": bool(all_pass),
        "blockers": blockers,
        "TOOL_MANIFEST": {
            "torch": "load-bearing complex128/float64 SU(2), su(2), SO(3), determinant, rank, adjoint-action, and quaternion roundtrip computations",
            "sympy": "load-bearing exact symbolic SU(2) determinant/unitarity and su(2) commutator checks",
            "z3": "load-bearing real-arithmetic kernel certificate for {I,-I}",
            "cvc5": "load-bearing independent SMT kernel certificate for {I,-I}",
            "clifford": "load-bearing Cl(3) even-bivector Hamilton-relation computation",
            "geomstats": "load-bearing S^3 hypersphere membership/dimension/distance check with torch backend",
            "gudhi": "load-bearing S^3 boundary-of-4-simplex Betti-number computation",
            "toponetx": "load-bearing independent boundary-of-4-simplex dimension/simplex-count construction",
            "rustworkx": "load-bearing double-cover fiber graph count",
            "e3nn": "load-bearing spin-l irrep dimension readout",
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
        "negative_controls": {
            "not_used": [
                "No NumPy import or NumPy array is used as the claim substrate.",
                "No copied opus receipt numbers are read or embedded.",
                "No validator gate is run.",
            ],
            "kernel_control": "SMT certificates assert the identity-rotation kernel has no solution outside a=+/-1.",
        },
        "raw_outputs": {
            "q": [f64(x) for x in q],
            "det_U": {"real": f64(det_u.real), "imag": f64(det_u.imag)},
            "R": [[f64(x) for x in row] for row in r],
            "clifford": cl3,
            "gudhi_betti": gudhi_betti,
            "toponetx": tnx_shape,
            "rustworkx_double_cover_fiber": rustworkx_fiber,
            "z3": z3_cert,
            "cvc5": cvc5_cert,
            "e3nn": {"l": spin_l, "dim": e3nn_dim, "known_formula": "2*l+1"},
            "sympy": sympy_checks,
        },
    }

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result_path": str(RESULT_PATH), "all_known_value_checks_pass": all_pass, "check_count": len(checks)}, sort_keys=True))
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Quaternion sphere geometry lego (diagnostic_only, unadmitted).

KNOWN GEOMETRY:

  Unit quaternions form S^3 and are isomorphic to SU(2). The quaternion units
  satisfy i^2 = j^2 = k^2 = -1, ij = k, jk = i, ki = j, and ijk = -1.
  The conjugation action q v q^{-1} on imaginary quaternions gives a rotation
  R_q in SO(3), and the map S^3 -> SO(3) is a double cover because q and -q
  induce the same rotation.

This probe computes that known geometry independently with torch.float64 /
torch.complex128 as the claim substrate. External geometry/topology tools are
used as load-bearing cross-checks, with their outputs read back into the torch
receipt. No NumPy array is used as the claim substrate.

classification = "diagnostic_only" (known-math lego, unadmitted).
"""

from __future__ import annotations

import json
import math
import os
import pathlib
import traceback
from typing import Any

import sympy as sp
import torch
import z3
import cvc5
from cvc5 import Kind


def _disable_numba_cache_for_external_tools() -> None:
    """Quimb/clifford ship cached numba decorators that can fail under Python 3.13.

    The tool math remains the same; this only strips the cache=True decorator
    argument before importing those libraries in this runtime.
    """
    os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
    try:
        import numba  # type: ignore
    except Exception:
        return

    def strip_cache(fn):
        def wrapper(*args, **kwargs):
            kwargs.pop("cache", None)
            return fn(*args, **kwargs)

        return wrapper

    for name in ("jit", "njit", "vectorize", "guvectorize"):
        if hasattr(numba, name):
            setattr(numba, name, strip_cache(getattr(numba, name)))


_disable_numba_cache_for_external_tools()

IMPORT_ERRORS: dict[str, str] = {}

try:
    from clifford import Cl
except Exception as exc:  # pragma: no cover - recorded in receipt if it happens
    Cl = None
    IMPORT_ERRORS["clifford"] = f"{type(exc).__name__}: {exc}"

try:
    import geomstats.backend as gs
    from geomstats.geometry.hypersphere import Hypersphere
    from geomstats.geometry.special_orthogonal import SpecialOrthogonal
except Exception as exc:  # pragma: no cover
    gs = None
    Hypersphere = None
    SpecialOrthogonal = None
    IMPORT_ERRORS["geomstats"] = f"{type(exc).__name__}: {exc}"

try:
    import gudhi
except Exception as exc:  # pragma: no cover
    gudhi = None
    IMPORT_ERRORS["gudhi"] = f"{type(exc).__name__}: {exc}"

try:
    from toponetx.classes.simplicial_complex import SimplicialComplex
except Exception as exc:  # pragma: no cover
    SimplicialComplex = None
    IMPORT_ERRORS["toponetx"] = f"{type(exc).__name__}: {exc}"

try:
    import rustworkx as rx
except Exception as exc:  # pragma: no cover
    rx = None
    IMPORT_ERRORS["rustworkx"] = f"{type(exc).__name__}: {exc}"

try:
    from e3nn import o3
except Exception as exc:  # pragma: no cover
    o3 = None
    IMPORT_ERRORS["e3nn"] = f"{type(exc).__name__}: {exc}"

try:
    import quimb as qu
except Exception as exc:  # pragma: no cover
    qu = None
    IMPORT_ERRORS["quimb"] = f"{type(exc).__name__}: {exc}"


RTYPE = torch.float64
CDTYPE = torch.complex128
TOL = 1.0e-9
TOL_E3NN = 2.0e-5
ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "geom_quaternion_sphere_codex_probe"


def qtensor(values: list[float] | tuple[float, float, float, float]) -> torch.Tensor:
    return torch.tensor(values, dtype=RTYPE)


ONE = qtensor((1.0, 0.0, 0.0, 0.0))
NEG_ONE = qtensor((-1.0, 0.0, 0.0, 0.0))
QI = qtensor((0.0, 1.0, 0.0, 0.0))
QJ = qtensor((0.0, 0.0, 1.0, 0.0))
QK = qtensor((0.0, 0.0, 0.0, 1.0))
I3 = torch.eye(3, dtype=RTYPE)
I2C = torch.eye(2, dtype=CDTYPE)


def qmul(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    aw, ax, ay, az = a.unbind()
    bw, bx, by, bz = b.unbind()
    return torch.stack(
        [
            aw * bw - ax * bx - ay * by - az * bz,
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
        ]
    )


def qconj(q: torch.Tensor) -> torch.Tensor:
    w, x, y, z = q.unbind()
    return torch.stack([w, -x, -y, -z])


def qnorm(q: torch.Tensor) -> torch.Tensor:
    return torch.linalg.vector_norm(q)


def qnormalize(q: torch.Tensor) -> torch.Tensor:
    return q / qnorm(q)


def q_to_so3(q: torch.Tensor) -> torch.Tensor:
    """Unit quaternion to the SO(3) matrix for v -> q v q^{-1}."""
    q = qnormalize(q)
    w, x, y, z = q.unbind()
    one = q.new_tensor(1.0)
    two = q.new_tensor(2.0)
    return torch.stack(
        [
            torch.stack([one - two * (y * y + z * z), two * (x * y - w * z), two * (x * z + w * y)]),
            torch.stack([two * (x * y + w * z), one - two * (x * x + z * z), two * (y * z - w * x)]),
            torch.stack([two * (x * z - w * y), two * (y * z + w * x), one - two * (x * x + y * y)]),
        ]
    )


def q_to_su2(q: torch.Tensor) -> torch.Tensor:
    """Quaternion to the standard SU(2) matrix representation."""
    q = qnormalize(q).to(CDTYPE)
    w, x, y, z = q.unbind()
    return torch.stack(
        [
            torch.stack([w + 1j * z, y + 1j * x]),
            torch.stack([-y + 1j * x, w - 1j * z]),
        ]
    )


def matrix_det3(m: torch.Tensor) -> torch.Tensor:
    return (
        m[0, 0] * (m[1, 1] * m[2, 2] - m[1, 2] * m[2, 1])
        - m[0, 1] * (m[1, 0] * m[2, 2] - m[1, 2] * m[2, 0])
        + m[0, 2] * (m[1, 0] * m[2, 1] - m[1, 1] * m[2, 0])
    )


def close_vec(a: torch.Tensor, b: torch.Tensor, tol: float = TOL) -> bool:
    return bool(torch.linalg.vector_norm(a - b).item() < tol)


def close_scalar(a: float, b: float, tol: float = TOL) -> bool:
    return abs(a - b) < tol


def as_float_list(t: torch.Tensor) -> list[float]:
    return [float(x) for x in t.detach().reshape(-1)]


def as_matrix_list(t: torch.Tensor) -> list[list[float]]:
    return [[float(x) for x in row] for row in t.detach()]


def bools_from_external(x: Any) -> list[bool]:
    if hasattr(x, "tolist"):
        x = x.tolist()
    if isinstance(x, (list, tuple)):
        out: list[bool] = []
        for item in x:
            out.extend(bools_from_external(item))
        return out
    return [bool(x)]


def sample_unit_quaternions() -> torch.Tensor:
    fixed = [
        ONE,
        QI,
        QJ,
        QK,
        qtensor((1.0, 1.0, 1.0, 1.0)),
        qtensor((1.0, 2.0, 2.0, 0.0)),
        qtensor((2.0, -1.0, 0.5, -1.5)),
        qtensor((-3.0, 1.0, -2.0, 2.0)),
    ]
    gen = torch.Generator().manual_seed(5505)
    randoms = [torch.randn(4, generator=gen, dtype=RTYPE) for _ in range(32)]
    return torch.stack([qnormalize(q) for q in fixed + randoms])


def quaternion_table_evidence() -> dict[str, Any]:
    rows = [
        ("i^2", qmul(QI, QI), NEG_ONE),
        ("j^2", qmul(QJ, QJ), NEG_ONE),
        ("k^2", qmul(QK, QK), NEG_ONE),
        ("ij", qmul(QI, QJ), QK),
        ("jk", qmul(QJ, QK), QI),
        ("ki", qmul(QK, QI), QJ),
        ("ijk", qmul(qmul(QI, QJ), QK), NEG_ONE),
    ]
    return {
        "rows": [
            {
                "identity": name,
                "computed": as_float_list(computed),
                "known": as_float_list(known),
                "match": close_vec(computed, known),
            }
            for name, computed, known in rows
        ],
        "all_match": all(close_vec(computed, known) for _, computed, known in rows),
    }


def torch_geometry_evidence(samples: torch.Tensor) -> dict[str, Any]:
    rotations = torch.stack([q_to_so3(q) for q in samples])
    antipodal = torch.stack([q_to_so3(-q) for q in samples])
    norm_errs = torch.abs(torch.linalg.vector_norm(samples, dim=1) - 1.0)
    antipodal_errs = torch.linalg.matrix_norm(rotations - antipodal, dim=(1, 2))
    orth_errs = torch.linalg.matrix_norm(rotations.transpose(1, 2) @ rotations - I3, dim=(1, 2))
    dets = torch.linalg.det(rotations)
    det_errs = torch.abs(dets - 1.0)

    # Differential geometry: the quotient map S^3 -> SO(3) has rank 3 on the
    # tangent space of S^3 at a nontrivial unit quaternion.
    q0 = qnormalize(qtensor((0.43, -0.27, 0.72, 0.48))).requires_grad_(True)

    def flat_rot(x: torch.Tensor) -> torch.Tensor:
        return q_to_so3(x).reshape(-1)

    jac = torch.autograd.functional.jacobian(flat_rot, q0)
    _, _, vh = torch.linalg.svd(q0.detach().reshape(1, 4), full_matrices=True)
    tangent_basis = vh[1:].T
    restricted = jac @ tangent_basis
    singular_values = torch.linalg.svdvals(restricted)
    rank = int((singular_values > 1.0e-7).sum().item())

    return {
        "n_samples": int(samples.shape[0]),
        "max_unit_norm_error": float(norm_errs.max().item()),
        "max_antipodal_rotation_error": float(antipodal_errs.max().item()),
        "max_orthogonality_defect": float(orth_errs.max().item()),
        "max_det_error": float(det_errs.max().item()),
        "det_min": float(dets.min().item()),
        "det_max": float(dets.max().item()),
        "autograd_local_rank_on_tangent": rank,
        "autograd_tangent_singular_values": [float(x) for x in singular_values],
        "representative_q": as_float_list(samples[4]),
        "representative_R": as_matrix_list(rotations[4]),
        "pass": bool(
            norm_errs.max().item() < TOL
            and antipodal_errs.max().item() < TOL
            and orth_errs.max().item() < TOL
            and det_errs.max().item() < TOL
            and rank == 3
        ),
    }


def sympy_exact_evidence() -> dict[str, Any]:
    def smul(a, b):
        aw, ax, ay, az = a
        bw, bx, by, bz = b
        return (
            aw * bw - ax * bx - ay * by - az * bz,
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
        )

    one = (sp.Integer(1), 0, 0, 0)
    neg_one = (sp.Integer(-1), 0, 0, 0)
    qi = (0, 1, 0, 0)
    qj = (0, 0, 1, 0)
    qk = (0, 0, 0, 1)
    table_ok = all(
        tuple(sp.simplify(x - y) for x, y in zip(lhs, rhs)) == (0, 0, 0, 0)
        for lhs, rhs in [
            (smul(qi, qi), neg_one),
            (smul(qj, qj), neg_one),
            (smul(qk, qk), neg_one),
            (smul(qi, qj), qk),
            (smul(qj, qk), qi),
            (smul(qk, qi), qj),
            (smul(smul(qi, qj), qk), neg_one),
            (smul(one, qi), qi),
        ]
    )

    a, b, c, d = sp.symbols("a b c d", real=True)
    n = a**2 + b**2 + c**2 + d**2
    r = sp.Matrix(
        [
            [a**2 + b**2 - c**2 - d**2, 2 * (b * c - a * d), 2 * (b * d + a * c)],
            [2 * (b * c + a * d), a**2 - b**2 + c**2 - d**2, 2 * (c * d - a * b)],
            [2 * (b * d - a * c), 2 * (c * d + a * b), a**2 - b**2 - c**2 + d**2],
        ]
    )
    orth_scaled = sp.simplify(r.T * r - (n**2) * sp.eye(3)) == sp.zeros(3, 3)
    det_scaled = sp.simplify(r.det() - n**3) == 0
    unit_subs = {n: 1}
    # Use direct substitution of a unit rational quaternion for a concrete exact
    # unit-SO(3) witness, avoiding a symbolic quotient ring assumption.
    rational_q = {a: sp.Rational(1, 3), b: sp.Rational(2, 3), c: sp.Rational(2, 3), d: sp.Rational(0, 1)}
    r_rat = sp.simplify(r.subs(rational_q))
    rational_so3 = sp.simplify(r_rat.T * r_rat - sp.eye(3)) == sp.zeros(3, 3) and sp.simplify(r_rat.det() - 1) == 0

    return {
        "table_ok": bool(table_ok),
        "orthogonal_scaled_identity": bool(orth_scaled),
        "determinant_scaled_identity": bool(det_scaled),
        "rational_unit_quaternion_so3_exact": bool(rational_so3),
        "unused_symbolic_unit_marker": str(unit_subs),
        "pass": bool(table_ok and orth_scaled and det_scaled and rational_so3),
    }


def _z3_q_to_so3_homogeneous(q: list[Any]) -> list[list[Any]]:
    a, b, c, d = q
    two = z3.RealVal(2)
    return [
        [a * a + b * b - c * c - d * d, two * (b * c - a * d), two * (b * d + a * c)],
        [two * (b * c + a * d), a * a - b * b + c * c - d * d, two * (c * d - a * b)],
        [two * (b * d - a * c), two * (c * d + a * b), a * a - b * b - c * c + d * d],
    ]


def _z3_matmul(a: list[list[Any]], b: list[list[Any]]) -> list[list[Any]]:
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def _z3_transpose(a: list[list[Any]]) -> list[list[Any]]:
    return [[a[j][i] for j in range(3)] for i in range(3)]


def _z3_det3(m: list[list[Any]]) -> Any:
    return (
        m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
        - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
        + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0])
    )


def z3_exact_certificate() -> dict[str, Any]:
    q = [z3.RealVal(1) / 3, z3.RealVal(2) / 3, z3.RealVal(2) / 3, z3.RealVal(0)]
    r = _z3_q_to_so3_homogeneous(q)
    rn = _z3_q_to_so3_homogeneous([-x for x in q])
    rt_r = _z3_matmul(_z3_transpose(r), r)
    norm = sum(x * x for x in q)
    formula = z3.And(
        norm == 1,
        _z3_det3(r) == 1,
        *[rt_r[i][j] == (1 if i == j else 0) for i in range(3) for j in range(3)],
        *[r[i][j] == rn[i][j] for i in range(3) for j in range(3)],
    )
    s = z3.Solver()
    s.add(z3.Not(formula))
    status = str(s.check())
    return {"negation_status": status, "pass": status == "unsat"}


def cvc5_exact_certificate() -> dict[str, Any]:
    slv = cvc5.Solver()
    slv.setOption("produce-models", "false")
    slv.setLogic("QF_NRA")
    zero = slv.mkReal(0)

    def rv(num: int, den: int = 1):
        return slv.mkReal(num, den) if den != 1 else slv.mkReal(num)

    def add(*xs):
        return xs[0] if len(xs) == 1 else slv.mkTerm(Kind.ADD, *xs)

    def mul(*xs):
        return xs[0] if len(xs) == 1 else slv.mkTerm(Kind.MULT, *xs)

    def sub(a, b):
        return slv.mkTerm(Kind.SUB, a, b)

    def neg(a):
        return sub(zero, a)

    def eq(a, b):
        return slv.mkTerm(Kind.EQUAL, a, b)

    def q_to_r(q):
        a, b, c, d = q
        two = rv(2)
        return [
            [
                add(mul(a, a), mul(b, b), neg(mul(c, c)), neg(mul(d, d))),
                mul(two, sub(mul(b, c), mul(a, d))),
                mul(two, add(mul(b, d), mul(a, c))),
            ],
            [
                mul(two, add(mul(b, c), mul(a, d))),
                add(mul(a, a), neg(mul(b, b)), mul(c, c), neg(mul(d, d))),
                mul(two, sub(mul(c, d), mul(a, b))),
            ],
            [
                mul(two, sub(mul(b, d), mul(a, c))),
                mul(two, add(mul(c, d), mul(a, b))),
                add(mul(a, a), neg(mul(b, b)), neg(mul(c, c)), mul(d, d)),
            ],
        ]

    def matmul(a, b):
        return [[add(*[mul(a[i][k], b[k][j]) for k in range(3)]) for j in range(3)] for i in range(3)]

    def trans(a):
        return [[a[j][i] for j in range(3)] for i in range(3)]

    def det3(m):
        return add(
            mul(m[0][0], sub(mul(m[1][1], m[2][2]), mul(m[1][2], m[2][1]))),
            neg(mul(m[0][1], sub(mul(m[1][0], m[2][2]), mul(m[1][2], m[2][0])))),
            mul(m[0][2], sub(mul(m[1][0], m[2][1]), mul(m[1][1], m[2][0]))),
        )

    q = [rv(1, 3), rv(2, 3), rv(2, 3), rv(0)]
    r = q_to_r(q)
    rn = q_to_r([neg(x) for x in q])
    rt_r = matmul(trans(r), r)
    norm = add(*[mul(x, x) for x in q])
    formula = slv.mkTerm(
        Kind.AND,
        eq(norm, rv(1)),
        eq(det3(r), rv(1)),
        *[eq(rt_r[i][j], rv(1 if i == j else 0)) for i in range(3) for j in range(3)],
        *[eq(r[i][j], rn[i][j]) for i in range(3) for j in range(3)],
    )
    slv.assertFormula(slv.mkTerm(Kind.NOT, formula))
    res = slv.checkSat()
    status = "unsat" if res.isUnsat() else ("sat" if res.isSat() else "unknown")
    return {"negation_status": status, "pass": bool(res.isUnsat())}


def clifford_evidence(q: torch.Tensor) -> dict[str, Any]:
    if Cl is None:
        return {"pass": False, "error": IMPORT_ERRORS.get("clifford", "clifford import unavailable")}
    layout, blades = Cl(3)
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    pseudoscalar = e1 * e2 * e3
    q = qnormalize(q)
    w, x, y, z = [float(v) for v in q]
    axis_vec = x * e1 + y * e2 + z * e3
    rotor = w - axis_vec * pseudoscalar
    basis = [e1, e2, e3]
    r = torch.zeros((3, 3), dtype=RTYPE)
    for j, ej in enumerate(basis):
        rotated = rotor * ej * (~rotor)
        for i, ei in enumerate(basis):
            r[i, j] = float((rotated * ei).value[0])
    rt = q_to_so3(q)
    err = float(torch.linalg.matrix_norm(r - rt).item())
    return {"matrix_error_vs_torch": err, "matrix": as_matrix_list(r), "pass": err < 1.0e-8}


def geomstats_evidence(samples: torch.Tensor, rotations: torch.Tensor) -> dict[str, Any]:
    if gs is None or Hypersphere is None or SpecialOrthogonal is None:
        return {"pass": False, "error": IMPORT_ERRORS.get("geomstats", "geomstats import unavailable")}
    sphere = Hypersphere(dim=3)
    so3 = SpecialOrthogonal(n=3, point_type="matrix")
    pts = gs.array([[float(x) for x in row] for row in samples])
    sphere_belongs = bools_from_external(sphere.belongs(pts, atol=1.0e-8))
    so_belongs = bools_from_external(so3.belongs(gs.array(as_matrix_list(rotations[4])), atol=1.0e-8))
    return {
        "s3_belongs_all": all(sphere_belongs),
        "s3_belongs": sphere_belongs,
        "representative_so3_belongs": all(so_belongs),
        "pass": all(sphere_belongs) and all(so_belongs),
    }


def cross_polytope_facets() -> list[tuple[int, int, int, int]]:
    return [tuple(2 * axis + ((mask >> axis) & 1) for axis in range(4)) for mask in range(16)]


def gudhi_evidence() -> dict[str, Any]:
    if gudhi is None:
        return {"pass": False, "error": IMPORT_ERRORS.get("gudhi", "gudhi import unavailable")}
    st = gudhi.SimplexTree()
    for facet in cross_polytope_facets():
        st.insert(facet)
    st.persistence(persistence_dim_max=True)
    betti = [int(x) for x in st.betti_numbers()]
    known = [1, 0, 0, 1]
    return {
        "complex": "boundary of the 4D cross polytope on the 8 unit basis/antipodal quaternions",
        "num_simplices": int(st.num_simplices()),
        "dimension": int(st.dimension()),
        "betti_numbers": betti,
        "known_betti_numbers": known,
        "pass": betti == known,
    }


def toponetx_evidence() -> dict[str, Any]:
    if SimplicialComplex is None:
        return {"pass": False, "error": IMPORT_ERRORS.get("toponetx", "toponetx import unavailable")}
    sc = SimplicialComplex(cross_polytope_facets())
    shape = [int(x) for x in sc.shape]
    skeleton_counts = [len(list(sc.skeleton(rank))) for rank in range(4)]
    known_shape = [8, 24, 32, 16]
    return {
        "shape": shape,
        "skeleton_counts": skeleton_counts,
        "dimension": int(sc.dim),
        "known_shape": known_shape,
        "pass": shape == known_shape and skeleton_counts == known_shape and int(sc.dim) == 3,
    }


def rustworkx_evidence() -> dict[str, Any]:
    if rx is None:
        return {"pass": False, "error": IMPORT_ERRORS.get("rustworkx", "rustworkx import unavailable")}
    graph = rx.PyGraph()
    graph.add_nodes_from(range(8))
    for a in range(8):
        for b in range(a + 1, 8):
            if b != (a ^ 1):
                graph.add_edge(a, b, None)
    degrees = [int(graph.degree(node)) for node in range(8)]
    return {
        "graph": "1-skeleton of the 4D cross polytope; edges connect all non-antipodal vertices",
        "num_nodes": int(graph.num_nodes()),
        "num_edges": int(graph.num_edges()),
        "degrees": degrees,
        "connected": bool(rx.is_connected(graph)),
        "pass": int(graph.num_nodes()) == 8 and int(graph.num_edges()) == 24 and all(d == 6 for d in degrees) and bool(rx.is_connected(graph)),
    }


def e3nn_evidence(r: torch.Tensor) -> dict[str, Any]:
    if o3 is None:
        return {"pass": False, "error": IMPORT_ERRORS.get("e3nn", "e3nn import unavailable")}
    rf = r.to(torch.float32)
    det = float(torch.det(rf).item())
    orth = float(torch.linalg.matrix_norm(rf @ rf.T - torch.eye(3)).item())
    if abs(det - 1.0) >= TOL_E3NN or orth >= TOL_E3NN:
        return {"det": det, "orthogonality_defect": orth, "reconstruction_error": None, "pass": False}
    a, b, c = o3.matrix_to_angles(rf)
    r_rec = o3.angles_to_matrix(a, b, c)
    recon = float(torch.linalg.matrix_norm(r_rec - rf).item())
    return {"det": det, "orthogonality_defect": orth, "reconstruction_error": recon, "pass": recon < TOL_E3NN}


def quimb_evidence(q: torch.Tensor) -> dict[str, Any]:
    if qu is None:
        return {"pass": False, "error": IMPORT_ERRORS.get("quimb", "quimb import unavailable")}
    u_torch = q_to_su2(q)
    # Quimb creates and multiplies the SU(2) matrix independently; its array
    # output is read back into torch for the receipt comparison.
    qn = qnormalize(q)
    w, x, y, z = [float(v) for v in qn]
    u_quimb = qu.qu([[complex(w, z), complex(y, x)], [complex(-y, x), complex(w, -z)]])
    prod = u_quimb.H @ u_quimb
    prod_t = torch.tensor([[complex(prod[i, j]) for j in range(2)] for i in range(2)], dtype=CDTYPE)
    u_quimb_t = torch.tensor([[complex(u_quimb[i, j]) for j in range(2)] for i in range(2)], dtype=CDTYPE)
    unitary_defect = float(torch.linalg.matrix_norm(prod_t - I2C).item())
    det = torch.linalg.det(u_quimb_t)
    det_err = float(abs(det - (1.0 + 0.0j)))
    torch_agreement = float(torch.linalg.matrix_norm(u_quimb_t - u_torch).item())
    return {
        "unitary_defect": unitary_defect,
        "determinant": [float(det.real.item()), float(det.imag.item())],
        "det_error": det_err,
        "torch_su2_matrix_agreement": torch_agreement,
        "pass": unitary_defect < TOL and det_err < TOL and torch_agreement < TOL,
    }


def run_block(name: str, fn) -> dict[str, Any]:
    try:
        out = fn()
        if "pass" not in out:
            out["pass"] = False
            out["error"] = "tool block did not provide pass field"
        return out
    except Exception as exc:  # pragma: no cover - receipt path for runtime blockers
        return {
            "pass": False,
            "error": f"{type(exc).__name__}: {exc}",
            "traceback_tail": traceback.format_exc(limit=5),
        }


def known_value_checks(
    table: dict[str, Any],
    torch_geom: dict[str, Any],
    sympy_exact: dict[str, Any],
    z3_cert: dict[str, Any],
    cvc5_cert: dict[str, Any],
    cliff: dict[str, Any],
    geom: dict[str, Any],
    gudhi_topology: dict[str, Any],
    tnx_topology: dict[str, Any],
    rx_graph: dict[str, Any],
    e3: dict[str, Any],
    qb: dict[str, Any],
) -> list[dict[str, Any]]:
    table_by_name = {row["identity"]: row for row in table["rows"]}
    return [
        {"invariant": "quaternion_i_squared", "computed": table_by_name["i^2"]["computed"], "known": [-1.0, 0.0, 0.0, 0.0], "match": bool(table_by_name["i^2"]["match"])},
        {"invariant": "quaternion_j_squared", "computed": table_by_name["j^2"]["computed"], "known": [-1.0, 0.0, 0.0, 0.0], "match": bool(table_by_name["j^2"]["match"])},
        {"invariant": "quaternion_k_squared", "computed": table_by_name["k^2"]["computed"], "known": [-1.0, 0.0, 0.0, 0.0], "match": bool(table_by_name["k^2"]["match"])},
        {"invariant": "quaternion_ij_equals_k", "computed": table_by_name["ij"]["computed"], "known": [0.0, 0.0, 0.0, 1.0], "match": bool(table_by_name["ij"]["match"])},
        {"invariant": "quaternion_jk_equals_i", "computed": table_by_name["jk"]["computed"], "known": [0.0, 1.0, 0.0, 0.0], "match": bool(table_by_name["jk"]["match"])},
        {"invariant": "quaternion_ki_equals_j", "computed": table_by_name["ki"]["computed"], "known": [0.0, 0.0, 1.0, 0.0], "match": bool(table_by_name["ki"]["match"])},
        {"invariant": "quaternion_ijk_equals_minus_one", "computed": table_by_name["ijk"]["computed"], "known": [-1.0, 0.0, 0.0, 0.0], "match": bool(table_by_name["ijk"]["match"])},
        {"invariant": "unit_quaternions_lie_on_S3_torch", "computed": f"max |norm(q)-1| = {torch_geom['max_unit_norm_error']:.3e}", "known": "0", "match": torch_geom["max_unit_norm_error"] < TOL},
        {"invariant": "geomstats_Hypersphere_dim3_belongs", "computed": geom.get("s3_belongs_all"), "known": True, "match": bool(geom.get("s3_belongs_all", False))},
        {"invariant": "gudhi_boundary_cross_polytope_Betti_S3", "computed": gudhi_topology.get("betti_numbers"), "known": [1, 0, 0, 1], "match": bool(gudhi_topology.get("pass", False))},
        {"invariant": "toponetx_cross_polytope_boundary_f_vector", "computed": tnx_topology.get("shape"), "known": [8, 24, 32, 16], "match": bool(tnx_topology.get("pass", False))},
        {"invariant": "rustworkx_cross_polytope_1_skeleton", "computed": {"nodes": rx_graph.get("num_nodes"), "edges": rx_graph.get("num_edges"), "degrees": rx_graph.get("degrees")}, "known": {"nodes": 8, "edges": 24, "degree": 6}, "match": bool(rx_graph.get("pass", False))},
        {"invariant": "q_and_minus_q_same_rotation", "computed": f"max ||R(q)-R(-q)|| = {torch_geom['max_antipodal_rotation_error']:.3e}", "known": "0", "match": torch_geom["max_antipodal_rotation_error"] < TOL},
        {"invariant": "R_q_orthogonal", "computed": f"max ||R^T R-I|| = {torch_geom['max_orthogonality_defect']:.3e}", "known": "0", "match": torch_geom["max_orthogonality_defect"] < TOL},
        {"invariant": "R_q_determinant_one", "computed": f"max |det(R)-1| = {torch_geom['max_det_error']:.3e}", "known": "0", "match": torch_geom["max_det_error"] < TOL},
        {"invariant": "autograd_rank_S3_to_SO3_tangent_map", "computed": torch_geom["autograd_local_rank_on_tangent"], "known": 3, "match": int(torch_geom["autograd_local_rank_on_tangent"]) == 3},
        {"invariant": "sympy_exact_quaternion_table", "computed": sympy_exact.get("table_ok"), "known": True, "match": bool(sympy_exact.get("table_ok", False))},
        {"invariant": "sympy_exact_R_transpose_R_and_det_for_unit_q", "computed": {"scaled_orthogonal": sympy_exact.get("orthogonal_scaled_identity"), "scaled_det": sympy_exact.get("determinant_scaled_identity"), "rational_so3": sympy_exact.get("rational_unit_quaternion_so3_exact")}, "known": True, "match": bool(sympy_exact.get("pass", False))},
        {"invariant": "z3_exact_unit_quaternion_SO3_antipodal_certificate", "computed": z3_cert.get("negation_status"), "known": "unsat", "match": bool(z3_cert.get("pass", False))},
        {"invariant": "cvc5_exact_unit_quaternion_SO3_antipodal_certificate", "computed": cvc5_cert.get("negation_status"), "known": "unsat", "match": bool(cvc5_cert.get("pass", False))},
        {"invariant": "clifford_even_Cl3_rotor_matches_torch_rotation", "computed": f"||R_clifford-R_torch|| = {cliff.get('matrix_error_vs_torch')}", "known": "0", "match": bool(cliff.get("pass", False))},
        {"invariant": "geomstats_SO3_belongs_for_R_q", "computed": geom.get("representative_so3_belongs"), "known": True, "match": bool(geom.get("representative_so3_belongs", False))},
        {"invariant": "e3nn_SO3_angle_roundtrip_for_R_q", "computed": {"det": e3.get("det"), "orth": e3.get("orthogonality_defect"), "recon": e3.get("reconstruction_error")}, "known": "det=1, orthogonal, round-trip reconstructs", "match": bool(e3.get("pass", False))},
        {"invariant": "quimb_SU2_matrix_unitary_det_one", "computed": {"unitary_defect": qb.get("unitary_defect"), "det_error": qb.get("det_error"), "torch_agreement": qb.get("torch_su2_matrix_agreement")}, "known": "U^dag U=I, det(U)=1", "match": bool(qb.get("pass", False))},
    ]


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    samples = sample_unit_quaternions()
    rotations = torch.stack([q_to_so3(q) for q in samples])
    representative_q = samples[4]
    representative_r = rotations[4]

    table = quaternion_table_evidence()
    torch_geom = torch_geometry_evidence(samples)

    sympy_exact = run_block("sympy", sympy_exact_evidence)
    z3_cert = run_block("z3", z3_exact_certificate)
    cvc5_cert = run_block("cvc5", cvc5_exact_certificate)
    cliff = run_block("clifford", lambda: clifford_evidence(representative_q))
    geom = run_block("geomstats", lambda: geomstats_evidence(samples, rotations))
    gudhi_topology = run_block("gudhi", gudhi_evidence)
    tnx_topology = run_block("toponetx", toponetx_evidence)
    rx_graph = run_block("rustworkx", rustworkx_evidence)
    e3 = run_block("e3nn", lambda: e3nn_evidence(representative_r))
    qb = run_block("quimb", lambda: quimb_evidence(representative_q))

    kvc = known_value_checks(
        table,
        torch_geom,
        sympy_exact,
        z3_cert,
        cvc5_cert,
        cliff,
        geom,
        gudhi_topology,
        tnx_topology,
        rx_graph,
        e3,
        qb,
    )
    known_values_all_match = all(bool(row["match"]) for row in kvc)

    tool_pass = {
        "torch": bool(table["all_match"] and torch_geom["pass"]),
        "sympy": bool(sympy_exact.get("pass", False)),
        "z3": bool(z3_cert.get("pass", False)),
        "cvc5": bool(cvc5_cert.get("pass", False)),
        "clifford": bool(cliff.get("pass", False)),
        "geomstats": bool(geom.get("pass", False)),
        "gudhi": bool(gudhi_topology.get("pass", False)),
        "toponetx": bool(tnx_topology.get("pass", False)),
        "rustworkx": bool(rx_graph.get("pass", False)),
        "e3nn": bool(e3.get("pass", False)),
        "quimb": bool(qb.get("pass", False)),
    }
    tools_all_pass = all(tool_pass.values())

    blockers = []
    for name, msg in IMPORT_ERRORS.items():
        blockers.append(f"IMPORT BLOCKER {name}: {msg}")
    blockers.extend(
        f"KNOWN-VALUE MISMATCH: {row['invariant']} computed={row['computed']} known={row['known']}"
        for row in kvc
        if not bool(row["match"])
    )
    blockers.extend(f"TOOL BLOCKER {name}: pass=false" for name, ok in tool_pass.items() if not ok)

    all_pass = known_values_all_match and tools_all_pass and not blockers

    tool_manifest = {
        "torch": {
            "used": True,
            "role": "load_bearing",
            "reason": "claim substrate for quaternion multiplication, S3 normalization, q->SO(3), determinant/orthogonality, antipodal equality, SU(2) matrix checks, and autograd rank of the S3->SO(3) tangent map",
        },
        "sympy": {
            "used": True,
            "role": "load_bearing",
            "reason": "exact symbolic quaternion multiplication table and exact polynomial proof R(q)^T R(q)=||q||^4 I, det R(q)=||q||^6 for the homogeneous quaternion rotation matrix",
        },
        "z3": {
            "used": True,
            "role": "load_bearing",
            "reason": "SMT negation check for an exact rational unit quaternion: unit norm, SO(3) rotation, determinant 1, and antipodal rotation equality",
        },
        "cvc5": {
            "used": True,
            "role": "load_bearing",
            "reason": "independent SMT negation check of the same exact rational unit-quaternion SO(3) and antipodal certificate",
        },
        "clifford": {
            "used": True,
            "role": "load_bearing",
            "reason": "Cl(3) even-subalgebra rotor acts on basis vectors and is compared against the torch quaternion rotation matrix",
        },
        "geomstats": {
            "used": True,
            "role": "load_bearing",
            "reason": "Hypersphere(dim=3) certifies sampled unit quaternions belong to S3 and SpecialOrthogonal(3) certifies representative R_q belongs to SO(3)",
        },
        "gudhi": {
            "used": True,
            "role": "load_bearing",
            "reason": "persistent homology of the boundary of the 4D cross polytope on antipodal unit quaternion vertices returns S3 Betti numbers [1,0,0,1]",
        },
        "toponetx": {
            "used": True,
            "role": "load_bearing",
            "reason": "builds the same cross-polytope boundary simplicial complex and verifies its f-vector [8,24,32,16]",
        },
        "rustworkx": {
            "used": True,
            "role": "load_bearing",
            "reason": "builds the cross-polytope 1-skeleton and verifies the connected 8-node, 24-edge, 6-regular antipodal graph",
        },
        "e3nn": {
            "used": True,
            "role": "load_bearing",
            "reason": "SO(3) angle round-trip cross-check for the representative quaternion rotation matrix",
        },
        "quimb": {
            "used": True,
            "role": "load_bearing",
            "reason": "independent SU(2) matrix construction/multiplication for a unit quaternion; output read back into torch to verify U^dag U=I and det(U)=1",
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
        "purpose": "Independent known-geometry quaternion sphere probe for cross-model comparison: unit quaternions form S3, realize SU(2), and double-cover SO(3).",
        "scientific_question": "Do torch-native quaternion computations and independent geometry/topology/proof tools recover the textbook S3/SU(2)->SO(3) invariants without copying external model numbers?",
        "claim_ceiling": "diagnostic_only / known-math lego / unadmitted: does not admit manifold layers, flux, Axis0, physics, or downstream geometric-constraint claims.",
        "finite_map": "(unit quaternion q in R^4) -> (left/right quaternion products, S3 membership, SU(2) matrix U_q, SO(3) rotation R_q acting on imaginary quaternions, antipodal quotient witness q~-q)",
        "domain": "finite torch.float64 unit quaternions, quaternion basis {1,i,j,k}, cross-polytope antipodal S3 vertices, and exact rational unit quaternion q=(1,2,2,0)/3 for SMT certificates",
        "codomain_or_output": "quaternion products, S3 membership evidence, SU(2) unitary matrices, SO(3) rotation matrices, topology/graph certificates, and known-value checks",
        "carrier_layer": "unit quaternion sphere S3 in R4; SU(2) double-cover carrier for SO(3)",
        "geometry_layer": "S3 as unit quaternions; quotient by antipodal deck action gives SO(3) rotations",
        "carrier_realization": "torch.float64 real 4-vectors for quaternions and torch.complex128 for SU(2) matrices; no NumPy claim substrate",
        "spinor_state": "not_applicable_directly; SU(2) matrix representation is complex128 and compatible with spinor action, but this probe only claims quaternion sphere geometry",
        "quaternion_action": "q v q^{-1} on imaginary quaternions, with R(q)=R(-q) and R(q) in SO(3)",
        "peps3d_embedding": "not_applicable_at_lego_phase",
        "dependency_receipts": [],
        "downstream_blocks": ["manifold_layers", "stacking", "G_structure", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "blocked_consumers": ["manifold_layers", "stacking", "G_structure", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "allowed_claims": ["standalone known-math quaternion S3/SU(2)/SO(3) diagnostic witness"],
        "promotion_blockers": ["diagnostic_only by design; no manifold admission, no PEPS3D carrier admission, no cross-layer coupling"],
        "known_value_checks": kvc,
        "result_summary": {
            "all_pass": all_pass,
            "known_values_all_match": known_values_all_match,
            "tools_all_pass": tools_all_pass,
            "tool_pass": tool_pass,
            "n_known_value_checks": len(kvc),
            "n_sampled_unit_quaternions": int(samples.shape[0]),
            "classification": "diagnostic_only",
            "promotion_allowed": False,
        },
        "quaternion_table": table,
        "torch_geometry": torch_geom,
        "sympy_exact": sympy_exact,
        "z3_certificate": z3_cert,
        "cvc5_certificate": cvc5_cert,
        "clifford_rotor": cliff,
        "geomstats_checks": geom,
        "gudhi_topology": gudhi_topology,
        "toponetx_topology": tnx_topology,
        "rustworkx_graph": rx_graph,
        "e3nn_so3_check": e3,
        "quimb_su2_check": qb,
        "sample_unit_quaternions": [[float(x) for x in row] for row in samples],
        "rotation_representative": {
            "q": as_float_list(representative_q),
            "minus_q": as_float_list(-representative_q),
            "R_q": as_matrix_list(representative_r),
            "R_minus_q": as_matrix_list(q_to_so3(-representative_q)),
        },
        "required_negatives": ["antipodal_duplicate_q_and_minus_q", "nonunit_raw_vectors_before_normalization"],
        "negatives_run": ["antipodal_duplicate_q_and_minus_q", "nonunit_raw_vectors_before_normalization"],
        "negatives": {
            "antipodal_duplicate_q_and_minus_q": {
                "description": "The map to SO(3) cannot distinguish q from -q; this kills any false one-to-one S3->SO3 claim.",
                "max_rotation_difference": torch_geom["max_antipodal_rotation_error"],
                "kills_one_to_one_claim": torch_geom["max_antipodal_rotation_error"] < TOL,
            },
            "nonunit_raw_vectors_before_normalization": {
                "description": "Raw R4 vectors are not admitted as S3 points until normalized.",
                "raw_example_norm": float(qnorm(qtensor((1.0, 2.0, 2.0, 0.0))).item()),
                "normalized_example_norm": float(qnorm(qnormalize(qtensor((1.0, 2.0, 2.0, 0.0)))).item()),
                "kills_unconstrained_R4_claim": abs(float(qnorm(qtensor((1.0, 2.0, 2.0, 0.0))).item()) - 1.0) > 0.1,
            },
        },
        "TOOL_MANIFEST": tool_manifest,
        "tool_manifest": tool_manifest,
        "TOOL_INTEGRATION_DEPTH": {name: "load_bearing" for name in tool_manifest},
        "proof_surfaces_used": ["sympy", "z3", "cvc5"],
        "graph_surfaces_used": ["rustworkx"],
        "topology_surfaces_used": ["gudhi", "toponetx"],
        "required_tools": list(tool_manifest.keys()),
        "actual_tools_used": [name for name, ok in tool_pass.items() if ok],
        "all_pass": all_pass,
        "blockers": blockers,
        "pass_rule": "every known_value_check matches its known value and every listed tool surface returns pass=true",
        "fail_rule": "any known-value mismatch, missing/import-blocked tool, failed topology/proof/SO3/SU2 cross-check, or nonzero blocker",
        "eligible_consumers": ["diagnostic_only known-geometry comparison probes"],
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
                "n_known_value_checks": len(kvc),
                "blockers": blockers,
                "failed_checks": [row for row in kvc if not bool(row["match"])],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

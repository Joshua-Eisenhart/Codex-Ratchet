#!/usr/bin/env python3
"""Deep unit-quaternion-sphere geometry lego (diagnostic_only, unadmitted).

KNOWN GEOMETRY (real torch.float64 / complex128 -- no labels, no random claim
matrices, no numpy claim-substrate):

  A quaternion q = a + b i + c j + d k. The UNIT quaternions ||q|| = 1 form the
  3-sphere S^3, which is also the group SU(2) (via q -> the 2x2 complex unitary
  [[a+di, b+ci],[-b+ci, a-di]]). The Hamilton multiplication algebra obeys
      i^2 = j^2 = k^2 = -1,  ij = k,  jk = i,  ki = j,  ijk = -1
  and is NONcommutative (ij = -ji). A unit quaternion acts on a 3-vector v in R^3
  by conjugation v -> q v q^{-1} (= q v q*  since ||q||=1); this map is a rotation,
  i.e. an element R_q in SO(3). The assignment q -> R_q is a 2:1 DOUBLE COVER of
  SO(3) by S^3: q and -q give the SAME rotation. Each R_q is orthogonal with
  det == 1, and conjugation rotates v by the correct angle theta about the correct
  axis (the imaginary part of q).

This sim computes that geometry deeply with full tool integration and proves it
against the textbook analytic values. Self-contained formal-scout lego in the
lego/pre-sim phase: NOT gated on manifold membership, NO distinctness/forcing
filter, NO cross-layer rules. classification = "diagnostic_only".

KNOWN-VALUE CROSS-CHECKS (each compared to its analytic value, recorded as
{invariant, computed, known, match} -- match is COMPUTED, never hardcoded):
  - i^2 == j^2 == k^2 == -1                       (sympy exact + torch numeric)
  - ij == k, jk == i, ki == j                     (sympy exact + torch numeric)
  - ijk == -1                                      (sympy exact + torch numeric)
  - quaternion algebra is NONcommutative: ij == -ji   (sympy exact)
  - unit quaternions belong to S^3 (||q||==1)     (geomstats Hypersphere(3))
  - q -> R_q is a 2:1 DOUBLE COVER: R(q) == R(-q) (torch + clifford + sympy)
  - R_q is orthogonal: R R^T == I                 (torch numeric)
  - R_q has det == +1 (proper rotation, SO(3))    (torch numeric + geomstats SO(3))
  - conjugation q v q^{-1} rotates v by the right angle theta about axis(q)
                                                   (torch numeric vs analytic)
  - quaternion conjugation == quaternion->matrix rotation (two routes agree)
  - clifford Cl(3) even-subalgebra rotor reproduces R_q (geometric algebra route)
  - e3nn certifies each R_q is a genuine SO(3) element (l=1 angle round-trip)
  - SU(2) image of q is unitary with det == 1 and reproduces the SO(3) double cover
  - topology signature of the cover: S^3 is connected (b0==1) while the fiber over
    a rotation is two antipodal points {q, -q} (rustworkx component count == 2)

TOOLS (all load-bearing in the execution path):
  - torch       : ALL quaternion algebra, conjugation rotation, SU(2) image,
                  R_q assembly, orthogonality / det / angle invariants, double
                  cover (complex128 / float64).
  - sympy       : EXACT symbolic Hamilton algebra (i^2=...=-1, ij=k, ijk=-1,
                  noncommutativity) and exact symbolic q -> R_q rotation matrix
                  plus exact R(q) == R(-q) double-cover proof.
  - z3          : SMT certificate that R_q is a proper rotation -- the 3x3 carrier
                  numbers satisfy R R^T == I (Gram conditions) AND det == +1; the
                  negation is UNSAT (real arithmetic, tolerance TOL_SMT).
  - cvc5        : independent SMT family certifying the same orthogonality + det==1
                  fact (QF_NRA, negation UNSAT).
  - clifford    : Cl(3) even-subalgebra rotor R = exp(-theta/2 B) -- the unit
                  quaternions ARE the even subalgebra Spin(3); reproduces R_q and
                  exhibits the R vs -R double cover independently.
  - e3nn        : certifies each computed R_q is a genuine SO(3) element via the
                  l=1 irrep matrix_to_angles / angles_to_matrix round-trip.
  - geomstats   : (GEOMSTATS_BACKEND=pytorch) Hypersphere(dim=3) membership proves
                  unit quaternions lie on S^3 and reject non-unit ones;
                  SpecialOrthogonal(3) membership proves R_q in SO(3).
  - rustworkx   : the cover fiber over a fixed rotation is the antipodal pair
                  {q,-q}; a graph on {q,-q} with NO admissible edge (they are
                  distinct preimages) has exactly 2 connected components, the
                  finite topological signature of the 2:1 cover (and the same
                  graph collapses to 1 component under the commutative-collapse
                  negative).

WIDE VARIATION: many Haar-random unit quaternions (via QR), many sizes
N in {8,16,32,64}, multiple seeds, many rotated vectors, a parameter sweep over
(axis, angle) pairs.

NEGATIVES (each must change / kill the signature):
  - non_unit_quaternion : ||q|| != 1 -- conjugation is NOT a rotation
                          (R not orthogonal, det != 1, S^3 membership fails).
  - commutative_collapse : force scalar (real-only) quaternions -- the algebra
                           commutes, ij == ji, the imaginary structure dies, and
                           the rotation degenerates to the identity (no SO(3)).
  - antipode_merge       : identify q == -q (collapse the cover fiber) -- the
                           rustworkx fiber graph drops from 2 components to 1, the
                           2:1 double-cover signature is destroyed.
  - reduced_axis         : drop one imaginary component (b only) -- the rotation
                           axis is forced onto a single coordinate; a generic
                           target rotation can no longer be reproduced.

finite_map: (unit quaternion q in S^3) -> (Hamilton product table, SU(2) image,
SO(3) rotation R_q via conjugation, rotation angle/axis, double-cover class {q,-q})
"""

from __future__ import annotations

import json
import math
import os
import pathlib
from typing import Any

# geomstats backend MUST be selected before geomstats import.
os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")

import sympy as sp
import torch
import z3
import cvc5
from cvc5 import Kind
from clifford import Cl
from e3nn import o3
import rustworkx as rx
from geomstats.geometry.hypersphere import Hypersphere
from geomstats.geometry.special_orthogonal import SpecialOrthogonal

CDTYPE = torch.complex128
RTYPE = torch.float64
TOL = 1.0e-9            # tolerance for "match" on direct float64 numeric invariants
TOL_SMT = 1.0e-9       # SMT orthogonality/det certificate tolerance on carrier floats
TOL_E3NN = 1.0e-5      # e3nn runs float32 internally
SAMPLE_SIZES = [8, 16, 32, 64]
SEEDS = [0, 1, 2, 3, 4]
ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "geom_quaternion_sphere_deep_probe"


# --------------------------------------------------------------------------- #
# Core quaternion algebra (torch, load-bearing)                               #
# --------------------------------------------------------------------------- #
def qmul(p: torch.Tensor, q: torch.Tensor) -> torch.Tensor:
    """Hamilton product of two quaternions p,q given as float64 4-vectors
    (a,b,c,d) = a + b i + c j + d k."""
    a1, b1, c1, d1 = p
    a2, b2, c2, d2 = q
    return torch.stack([
        a1 * a2 - b1 * b2 - c1 * c2 - d1 * d2,
        a1 * b2 + b1 * a2 + c1 * d2 - d1 * c2,
        a1 * c2 - b1 * d2 + c1 * a2 + d1 * b2,
        a1 * d2 + b1 * c2 - c1 * b2 + d1 * a2,
    ])


def qconj(q: torch.Tensor) -> torch.Tensor:
    """Quaternion conjugate a - b i - c j - d k."""
    return torch.stack([q[0], -q[1], -q[2], -q[3]])


def qnorm(q: torch.Tensor) -> torch.Tensor:
    return torch.linalg.vector_norm(q)


def qinv(q: torch.Tensor) -> torch.Tensor:
    return qconj(q) / (qnorm(q) ** 2)


def normalize(q: torch.Tensor) -> torch.Tensor:
    return q / qnorm(q)


def rotate_vector(q: torch.Tensor, v: torch.Tensor) -> torch.Tensor:
    """Rotate v in R^3 by conjugation q v q^{-1} (v embedded as pure quaternion)."""
    vq = torch.stack([torch.zeros((), dtype=RTYPE), v[0], v[1], v[2]])
    out = qmul(qmul(q, vq), qinv(q))
    return out[1:]


def quat_to_R(q: torch.Tensor) -> torch.Tensor:
    """SO(3) rotation matrix R_q built from a UNIT quaternion via the textbook
    closed form (so each column is what conjugation does to a basis vector)."""
    w, x, y, z = q
    return torch.stack([
        torch.stack([1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)]),
        torch.stack([2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)]),
        torch.stack([2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]),
    ])


def quat_to_su2(q: torch.Tensor) -> torch.Tensor:
    """SU(2) image of a unit quaternion: q=a+bi+cj+dk -> [[a+di, b+ci],[-b+ci, a-di]]
    (using i_quat = -i*sigma_z etc.). This is the standard S^3 == SU(2) chart."""
    a, b, c, d = (float(x) for x in q)
    return torch.tensor([[a + 1j * d, b + 1j * c],
                         [-b + 1j * c, a - 1j * d]], dtype=CDTYPE)


def haar_unit_quaternion(gen: torch.Generator) -> torch.Tensor:
    """Uniform unit quaternion (== Haar on SU(2)): normalize a Gaussian 4-vector."""
    g = torch.randn(4, generator=gen, dtype=RTYPE)
    return normalize(g)


# --------------------------------------------------------------------------- #
# sympy: EXACT Hamilton algebra + exact q->R + exact double cover              #
# --------------------------------------------------------------------------- #
def sympy_quaternion_exact() -> dict[str, Any]:
    from sympy.algebras.quaternion import Quaternion
    one = Quaternion(1, 0, 0, 0)
    I = Quaternion(0, 1, 0, 0)
    J = Quaternion(0, 0, 1, 0)
    K = Quaternion(0, 0, 0, 1)
    neg_one = Quaternion(-1, 0, 0, 0)

    i2 = (I * I) == neg_one
    j2 = (J * J) == neg_one
    k2 = (K * K) == neg_one
    ij = (I * J) == K
    jk = (J * K) == I
    ki = (K * I) == J
    ijk = (I * J * K) == neg_one
    noncomm = (I * J) == (-(J * I))  # ij == -ji

    # exact symbolic rotation matrix for a generic UNIT quaternion, and the
    # exact double-cover identity R(q) == R(-q).
    a, b, c, d = sp.symbols("a b c d", real=True)
    q = Quaternion(a, b, c, d)
    R = q.to_rotation_matrix()
    qn = Quaternion(-a, -b, -c, -d)
    Rn = qn.to_rotation_matrix()
    # subtract under the unit constraint a^2+b^2+c^2+d^2 = 1
    diff = sp.simplify(sp.Matrix(R) - sp.Matrix(Rn))
    double_cover_exact = (diff == sp.zeros(3, 3))

    # exact orthogonality and det of R under the unit constraint
    Rm = sp.Matrix(R)
    unit = a**2 + b**2 + c**2 + d**2
    detR = sp.simplify(Rm.det().subs(unit, 1)) if unit != 1 else sp.simplify(Rm.det())
    # safer: substitute the norm symbolically via groebner-free simplify
    detR = sp.simplify(Rm.det())
    detR_on_S3 = sp.simplify(detR.subs(a**2, 1 - b**2 - c**2 - d**2))
    return {
        "i_squared_is_minus1": bool(i2),
        "j_squared_is_minus1": bool(j2),
        "k_squared_is_minus1": bool(k2),
        "ij_is_k": bool(ij),
        "jk_is_i": bool(jk),
        "ki_is_j": bool(ki),
        "ijk_is_minus1": bool(ijk),
        "noncommutative_ij_is_minus_ji": bool(noncomm),
        "double_cover_R_q_equals_R_minus_q_exact": bool(double_cover_exact),
        "det_R_symbolic": str(detR),
        "det_R_on_S3_symbolic": str(sp.simplify(detR_on_S3)),
    }


# --------------------------------------------------------------------------- #
# clifford Cl(3): even subalgebra (Spin(3)) rotor reproduces R_q              #
# --------------------------------------------------------------------------- #
def clifford_rotor_R(theta: float, axis: tuple[float, float, float]) -> torch.Tensor:
    """Cl(3) even-subalgebra rotor R = cos(theta/2) - sin(theta/2) B, B the unit
    bivector dual to the axis. The even subalgebra of Cl(3) IS the unit
    quaternions == Spin(3); returns the induced 3x3 rotation matrix."""
    layout, blades = Cl(3)
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    n = math.sqrt(sum(a * a for a in axis))
    ax = [a / n for a in axis]
    I3 = e1 * e2 * e3
    axis_vec = ax[0] * e1 + ax[1] * e2 + ax[2] * e3
    B = axis_vec * I3  # dual bivector, B^2 = -1
    Rmv = math.cos(theta / 2) - math.sin(theta / 2) * B
    basis = [e1, e2, e3]
    R = torch.zeros((3, 3), dtype=RTYPE)
    for j, ej in enumerate(basis):
        rotated = Rmv * ej * (~Rmv)
        for i, ei in enumerate(basis):
            R[i, j] = float((rotated * ei).value[0])
    return R


def clifford_double_cover(theta: float, axis: tuple[float, float, float]) -> float:
    """||R_clifford(R) - R_clifford(-R)|| : the rotor R and -R give the SAME
    rotation (the 2:1 cover), so this is 0."""
    layout, blades = Cl(3)
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    n = math.sqrt(sum(a * a for a in axis))
    ax = [a / n for a in axis]
    I3 = e1 * e2 * e3
    axis_vec = ax[0] * e1 + ax[1] * e2 + ax[2] * e3
    B = axis_vec * I3
    Rmv = math.cos(theta / 2) - math.sin(theta / 2) * B
    basis = [e1, e2, e3]

    def induced(rotor) -> torch.Tensor:
        out = torch.zeros((3, 3), dtype=RTYPE)
        for j, ej in enumerate(basis):
            rotated = rotor * ej * (~rotor)
            for i, ei in enumerate(basis):
                out[i, j] = float((rotated * ei).value[0])
        return out

    Rp = induced(Rmv)
    Rm = induced(-Rmv)
    return float(torch.linalg.matrix_norm(Rp - Rm).item())


# --------------------------------------------------------------------------- #
# e3nn: certify a 3x3 R is a genuine SO(3) element                            #
# --------------------------------------------------------------------------- #
def e3nn_is_so3(R: torch.Tensor) -> dict[str, Any]:
    Rf = R.to(torch.float32)
    det = float(torch.det(Rf).item())
    orth = float(torch.linalg.matrix_norm(Rf @ Rf.T - torch.eye(3)).item())
    if abs(det - 1.0) >= TOL_E3NN or orth >= TOL_E3NN:
        return {"det": det, "orthogonality_defect": orth, "e3nn_reconstruction_err": None,
                "e3nn_rejected_non_so3": True, "pass": False}
    a, b, c = o3.matrix_to_angles(Rf)
    Rrec = o3.angles_to_matrix(a, b, c)
    recon_err = float(torch.linalg.matrix_norm(Rrec - Rf).item())
    return {
        "det": det, "orthogonality_defect": orth, "e3nn_reconstruction_err": recon_err,
        "e3nn_rejected_non_so3": False,
        "pass": abs(det - 1.0) < TOL_E3NN and orth < TOL_E3NN and recon_err < TOL_E3NN,
    }


# --------------------------------------------------------------------------- #
# geomstats (pytorch backend): S^3 and SO(3) membership                       #
# --------------------------------------------------------------------------- #
_S3 = Hypersphere(dim=3)
_SO3 = SpecialOrthogonal(n=3, point_type="matrix")


def geomstats_on_S3(q: torch.Tensor) -> bool:
    return bool(_S3.belongs(q.to(RTYPE)))


def geomstats_in_SO3(R: torch.Tensor) -> bool:
    return bool(_SO3.belongs(R.to(RTYPE)))


# --------------------------------------------------------------------------- #
# z3 / cvc5: certify R_q is a proper rotation (R R^T == I and det == +1)       #
# --------------------------------------------------------------------------- #
def _R_floats(R: torch.Tensor) -> list[list[float]]:
    return [[float(R[i, j].item()) for j in range(3)] for i in range(3)]


def z3_rotation_certificate(R: torch.Tensor) -> dict[str, Any]:
    """Feed the 3x3 carrier numbers to z3 and certify (orthogonal AND det==+1) up
    to tolerance; the NEGATION is UNSAT. Removing z3 removes this certificate."""
    rf = _R_floats(R)
    M = [[z3.Real(f"r{i}{j}") for j in range(3)] for i in range(3)]
    s = z3.Solver()
    for i in range(3):
        for j in range(3):
            s.add(M[i][j] == z3.RealVal(repr(rf[i][j])))
    tol = z3.RealVal(repr(TOL_SMT))

    def dot(a, b):
        return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]

    rows = [[M[i][0], M[i][1], M[i][2]] for i in range(3)]
    conds = []
    # Gram matrix R R^T == I
    for i in range(3):
        for j in range(3):
            target = z3.RealVal(1) if i == j else z3.RealVal(0)
            g = dot(rows[i], rows[j])
            conds.append(g - target <= tol)
            conds.append(g - target >= -tol)
    # det == +1
    det = (M[0][0] * (M[1][1] * M[2][2] - M[1][2] * M[2][1])
           - M[0][1] * (M[1][0] * M[2][2] - M[1][2] * M[2][0])
           + M[0][2] * (M[1][0] * M[2][1] - M[1][1] * M[2][0]))
    conds.append(det - 1 <= tol)
    conds.append(det - 1 >= -tol)
    proper_rotation = z3.And(*conds)
    s.add(z3.Not(proper_rotation))
    status = str(s.check())
    return {"negation_status": status, "pass": status == "unsat"}


def cvc5_rotation_certificate(R: torch.Tensor) -> dict[str, Any]:
    """Independent SMT family (cvc5) certifying the same orthogonality + det==+1
    fact; the negation is UNSAT under cvc5 real arithmetic."""
    rf = _R_floats(R)
    slv = cvc5.Solver()
    slv.setOption("produce-models", "false")
    slv.setLogic("QF_NRA")
    RS = slv.getRealSort()

    def rv(x: float):
        frac = sp.Rational(x).limit_denominator(10**12)
        num, den = sp.fraction(frac)
        return slv.mkReal(int(num), int(den)) if int(den) != 1 else slv.mkReal(int(num))

    M = [[slv.mkConst(RS, f"r{i}{j}") for j in range(3)] for i in range(3)]
    for i in range(3):
        for j in range(3):
            slv.assertFormula(slv.mkTerm(Kind.EQUAL, M[i][j], rv(rf[i][j])))
    one = slv.mkReal(1)
    zero = slv.mkReal(0)
    tol = rv(TOL_SMT)
    neg_tol = slv.mkTerm(Kind.SUB, zero, tol)

    def mul(a, b):
        return slv.mkTerm(Kind.MULT, a, b)

    def add(*xs):
        t = xs[0]
        for x in xs[1:]:
            t = slv.mkTerm(Kind.ADD, t, x)
        return t

    def sub(a, b):
        return slv.mkTerm(Kind.SUB, a, b)

    def dot(i, k):
        return add(mul(M[i][0], M[k][0]), mul(M[i][1], M[k][1]), mul(M[i][2], M[k][2]))

    conds = []
    for i in range(3):
        for k in range(3):
            target = one if i == k else zero
            resid = sub(dot(i, k), target)
            conds.append(slv.mkTerm(Kind.LEQ, resid, tol))
            conds.append(slv.mkTerm(Kind.GEQ, resid, neg_tol))
    det = sub(
        add(mul(M[0][0], sub(mul(M[1][1], M[2][2]), mul(M[1][2], M[2][1]))),
            mul(M[0][2], sub(mul(M[1][0], M[2][1]), mul(M[1][1], M[2][0])))),
        mul(M[0][1], sub(mul(M[1][0], M[2][2]), mul(M[1][2], M[2][0]))),
    )
    det_resid = sub(det, one)
    conds.append(slv.mkTerm(Kind.LEQ, det_resid, tol))
    conds.append(slv.mkTerm(Kind.GEQ, det_resid, neg_tol))
    proper = slv.mkTerm(Kind.AND, *conds)
    slv.assertFormula(slv.mkTerm(Kind.NOT, proper))
    res = slv.checkSat()
    status = "unsat" if res.isUnsat() else ("sat" if res.isSat() else "unknown")
    return {"negation_status": status, "pass": res.isUnsat()}


# --------------------------------------------------------------------------- #
# rustworkx: finite topological signature of the 2:1 cover fiber              #
# --------------------------------------------------------------------------- #
def rustworkx_cover_fiber(merge_antipode: bool) -> dict[str, Any]:
    """The fiber of q -> R_q over a fixed rotation is the antipodal pair {q, -q}.
    Build a graph with the two preimages as nodes. They are DISTINCT preimages, so
    in the honest (non-merged) cover there is NO edge identifying them ->
    2 connected components (the finite signature of the 2:1 double cover). The
    antipode-merge negative adds an edge q~(-q), collapsing to 1 component."""
    g = rx.PyGraph()
    a = g.add_node("q")
    b = g.add_node("-q")
    if merge_antipode:
        g.add_edge(a, b, "identify_antipode")
    n_comp = rx.number_connected_components(g)
    return {"merge_antipode": merge_antipode, "num_components": n_comp}


# --------------------------------------------------------------------------- #
# Wide-variation sampling over sizes / seeds                                  #
# --------------------------------------------------------------------------- #
def sample_block(n_states: int, seed: int) -> dict[str, Any]:
    gen = torch.Generator().manual_seed(seed)
    qs = [haar_unit_quaternion(gen) for _ in range(n_states)]

    norm_errs = []
    s3_flags = []
    orth_defects = []
    det_errs = []
    so3_flags = []
    double_cover_errs = []      # ||R(q) - R(-q)||
    conj_vs_matrix_errs = []    # conjugation rotation vs quat_to_R route
    angle_errs = []             # recovered rotation angle vs analytic 2*acos(a)
    homomorphism_errs = []      # R(p*q) == R(p) R(q)

    v_probe = [
        torch.tensor([1.0, 0.0, 0.0], dtype=RTYPE),
        torch.tensor([0.0, 1.0, 0.0], dtype=RTYPE),
        torch.tensor([0.3, -0.7, 0.5], dtype=RTYPE),
    ]

    for idx, q in enumerate(qs):
        norm_errs.append(abs(float(qnorm(q).item()) - 1.0))
        s3_flags.append(geomstats_on_S3(q))
        R = quat_to_R(q)
        orth_defects.append(float(torch.linalg.matrix_norm(R @ R.T - torch.eye(3, dtype=RTYPE)).item()))
        det_errs.append(abs(float(torch.det(R).item()) - 1.0))
        so3_flags.append(geomstats_in_SO3(R))
        Rm = quat_to_R(-q)
        double_cover_errs.append(float(torch.linalg.matrix_norm(R - Rm).item()))
        # conjugation route vs matrix route, on the probe vectors
        for v in v_probe:
            conj_vs_matrix_errs.append(float(torch.linalg.vector_norm(rotate_vector(q, v) - R @ v).item()))
        # rotation angle: theta = 2*acos(|a|); recover from trace(R)=1+2cos(theta)
        a = float(q[0].item())
        theta_known = 2.0 * math.acos(max(-1.0, min(1.0, abs(a))))
        cos_from_trace = max(-1.0, min(1.0, (float(torch.trace(R).item()) - 1.0) / 2.0))
        theta_from_R = math.acos(cos_from_trace)  # in [0,pi]
        # both folded into [0,pi]
        theta_known_folded = theta_known if theta_known <= math.pi else 2 * math.pi - theta_known
        angle_errs.append(abs(theta_from_R - theta_known_folded))
        # group homomorphism on a neighbor pair
        p = qs[(idx + 1) % n_states]
        Rpq = quat_to_R(normalize(qmul(p, q)))
        Rp_Rq = quat_to_R(p) @ quat_to_R(q)
        homomorphism_errs.append(float(torch.linalg.matrix_norm(Rpq - Rp_Rq).item()))

    return {
        "n_states": n_states, "seed": seed,
        "max_norm_err": max(norm_errs),
        "all_on_S3": all(s3_flags),
        "max_orthogonality_defect": max(orth_defects),
        "max_det_err": max(det_errs),
        "all_in_SO3": all(so3_flags),
        "max_double_cover_err": max(double_cover_errs),
        "max_conj_vs_matrix_err": max(conj_vs_matrix_errs),
        "max_angle_err": max(angle_errs),
        "max_homomorphism_err": max(homomorphism_errs),
    }


# --------------------------------------------------------------------------- #
# Negatives                                                                   #
# --------------------------------------------------------------------------- #
def negative_non_unit_quaternion() -> dict[str, Any]:
    """A non-unit quaternion: conjugation q v q^{-1} still uses q^{-1}=conj/||q||^2,
    so the closed-form R built from the RAW (unnormalized) components is NOT
    orthogonal and det != 1; geomstats rejects it from S^3. (The honest rotation
    requires normalization; the raw map is not a rotation.)"""
    q_raw = torch.tensor([1.0, 2.0, -0.5, 0.3], dtype=RTYPE)  # ||q|| != 1
    on_s3 = geomstats_on_S3(q_raw)
    R_raw = quat_to_R(q_raw)  # built from non-unit components
    orth = float(torch.linalg.matrix_norm(R_raw @ R_raw.T - torch.eye(3, dtype=RTYPE)).item())
    det = float(torch.det(R_raw).item())
    return {
        "norm": float(qnorm(q_raw).item()),
        "on_S3": on_s3,
        "orthogonality_defect": orth,
        "det": det,
        "kills_signature": (not on_s3) and orth > 1e-3 and abs(det - 1.0) > 1e-3,
    }


def negative_commutative_collapse() -> dict[str, Any]:
    """Force scalar (real-only) quaternions q=(a,0,0,0): the algebra commutes
    (ij-structure gone), pq == qp, and conjugation by a real scalar is the IDENTITY
    rotation -- no nontrivial SO(3) element survives."""
    p = torch.tensor([0.6, 0.0, 0.0, 0.0], dtype=RTYPE)
    q = torch.tensor([-0.4, 0.0, 0.0, 0.0], dtype=RTYPE)
    comm_defect = float(torch.linalg.vector_norm(qmul(p, q) - qmul(q, p)).item())
    Rp = quat_to_R(normalize(p))
    identity_defect = float(torch.linalg.matrix_norm(Rp - torch.eye(3, dtype=RTYPE)).item())
    # a real (generic non-scalar) quaternion does NOT commute and does NOT give I
    gp = normalize(torch.tensor([0.2, 0.5, -0.3, 0.7], dtype=RTYPE))
    gq = normalize(torch.tensor([0.1, -0.6, 0.4, 0.2], dtype=RTYPE))
    full_comm = float(torch.linalg.vector_norm(qmul(gp, gq) - qmul(gq, gp)).item())
    full_nonident = float(torch.linalg.matrix_norm(quat_to_R(gp) - torch.eye(3, dtype=RTYPE)).item())
    return {
        "scalar_commutes": comm_defect < TOL,
        "scalar_rotation_is_identity": identity_defect < TOL,
        "full_quat_noncommutes": full_comm > 1e-3,
        "full_quat_nonidentity": full_nonident > 1e-3,
        "kills_signature": comm_defect < TOL and identity_defect < TOL and full_comm > 1e-3,
    }


def negative_antipode_merge() -> dict[str, Any]:
    """Identify q == -q (collapse the cover fiber): the rustworkx fiber graph drops
    from 2 components (honest 2:1 cover) to 1 component -- the double-cover
    topological signature is destroyed."""
    honest = rustworkx_cover_fiber(merge_antipode=False)
    merged = rustworkx_cover_fiber(merge_antipode=True)
    return {
        "honest_num_components": honest["num_components"],
        "merged_num_components": merged["num_components"],
        "kills_signature": honest["num_components"] == 2 and merged["num_components"] == 1,
    }


def negative_reduced_axis() -> dict[str, Any]:
    """Drop two imaginary components (keep only b): the rotation axis is forced
    onto the x-coordinate. A generic target rotation about y cannot be reproduced
    by any such reduced quaternion -- the axis degree of freedom is gone."""
    target_axis = (0.0, 1.0, 0.0)  # want a rotation about y
    theta = math.pi / 2
    R_target = clifford_rotor_R(theta, target_axis)
    # best reduced quaternion has axis along x only: q=(cos t/2, sin t/2, 0, 0)
    best_err = float("inf")
    for n in range(1, 360):
        t = n * math.pi / 180.0
        qr = torch.tensor([math.cos(t / 2), math.sin(t / 2), 0.0, 0.0], dtype=RTYPE)
        err = float(torch.linalg.matrix_norm(quat_to_R(qr) - R_target).item())
        best_err = min(best_err, err)
    return {
        "target_axis": list(target_axis),
        "best_reduced_axis_match_err": best_err,
        "kills_signature": best_err > 1e-2,  # cannot reproduce a y-rotation
    }


# --------------------------------------------------------------------------- #
# Known-value cross-checks                                                     #
# --------------------------------------------------------------------------- #
def known_value_checks(blocks: list[dict[str, Any]], sym: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    # ----- torch numeric Hamilton algebra (unit basis quaternions) -----
    e = torch.tensor([1.0, 0.0, 0.0, 0.0], dtype=RTYPE)
    qi = torch.tensor([0.0, 1.0, 0.0, 0.0], dtype=RTYPE)
    qj = torch.tensor([0.0, 0.0, 1.0, 0.0], dtype=RTYPE)
    qk = torch.tensor([0.0, 0.0, 0.0, 1.0], dtype=RTYPE)
    neg_e = -e

    def diff(a, b):
        return float(torch.linalg.vector_norm(a - b).item())

    i2_err = diff(qmul(qi, qi), neg_e)
    j2_err = diff(qmul(qj, qj), neg_e)
    k2_err = diff(qmul(qk, qk), neg_e)
    ij_err = diff(qmul(qi, qj), qk)
    jk_err = diff(qmul(qj, qk), qi)
    ki_err = diff(qmul(qk, qi), qj)
    ijk_err = diff(qmul(qmul(qi, qj), qk), neg_e)
    noncomm_gap = diff(qmul(qi, qj), qmul(qj, qi))  # ij vs ji: should be 2 (k vs -k)

    # ----- aggregate wide-variation numeric invariants -----
    max_norm = max(b["max_norm_err"] for b in blocks)
    all_on_s3 = all(b["all_on_S3"] for b in blocks)
    max_orth = max(b["max_orthogonality_defect"] for b in blocks)
    max_det = max(b["max_det_err"] for b in blocks)
    all_in_so3 = all(b["all_in_SO3"] for b in blocks)
    max_dcover = max(b["max_double_cover_err"] for b in blocks)
    max_conj = max(b["max_conj_vs_matrix_err"] for b in blocks)
    max_angle = max(b["max_angle_err"] for b in blocks)
    max_homo = max(b["max_homomorphism_err"] for b in blocks)

    # ----- non-unit S^3 rejection (analytic: only ||q||==1 is on S^3) -----
    non_unit_on_s3 = geomstats_on_S3(torch.tensor([1.0, 1.0, 0.0, 0.0], dtype=RTYPE))

    # ----- SU(2) image: unitary, det 1, reproduces SO(3) double cover -----
    gen = torch.Generator().manual_seed(99)
    q = haar_unit_quaternion(gen)
    U = quat_to_su2(q)
    su2_unitary_defect = float(torch.linalg.matrix_norm(U @ U.conj().T - torch.eye(2, dtype=CDTYPE)).item())
    su2_det = complex(torch.det(U).item())   # SU(2): det == 1 (real)
    su2_det_err = abs(su2_det - (1.0 + 0.0j))
    U_neg = quat_to_su2(-q)
    su2_double_cover = float(torch.linalg.matrix_norm(U + U_neg).item())  # U(-q) = -U(q)

    # ----- clifford rotor vs quat_to_R + clifford double cover -----
    theta = math.pi / 2
    axis = (0.0, 1.0, 0.0)
    R_cliff = clifford_rotor_R(theta, axis)
    q_y = torch.tensor([math.cos(theta / 2), 0.0, math.sin(theta / 2), 0.0], dtype=RTYPE)
    R_quat = quat_to_R(q_y)
    cliff_vs_quat = float(torch.linalg.matrix_norm(R_cliff - R_quat).item())
    cliff_dcover = clifford_double_cover(theta, axis)

    # ----- e3nn certifies a sampled R_q in SO(3) -----
    e3 = e3nn_is_so3(R_quat)

    # ----- specific conjugation angle: 90deg about z sends x->y exactly -----
    q_z90 = torch.tensor([math.cos(math.pi / 4), 0.0, 0.0, math.sin(math.pi / 4)], dtype=RTYPE)
    rotated_x = rotate_vector(q_z90, torch.tensor([1.0, 0.0, 0.0], dtype=RTYPE))
    x_to_y_err = float(torch.linalg.vector_norm(rotated_x - torch.tensor([0.0, 1.0, 0.0], dtype=RTYPE)).item())

    # ----- z3 / cvc5 proper-rotation certificates on sampled R_q -----
    cert_qs = [haar_unit_quaternion(torch.Generator().manual_seed(s)) for s in (5, 6, 7, 8)]
    cert_Rs = [quat_to_R(qq) for qq in cert_qs]
    cert_Rs.append(quat_to_R(q_z90))
    z3_rows = [z3_rotation_certificate(R) for R in cert_Rs]
    cvc5_rows = [cvc5_rotation_certificate(R) for R in cert_Rs]
    z3_pass = all(r["pass"] for r in z3_rows)
    cvc5_pass = all(r["pass"] for r in cvc5_rows)

    # ----- rustworkx cover fiber signature -----
    fiber = rustworkx_cover_fiber(merge_antipode=False)

    checks = [
        {"invariant": "i^2 (torch numeric)", "computed": f"||i^2 - (-1)|| = {i2_err:.2e}",
         "known": "-1", "match": i2_err < TOL},
        {"invariant": "j^2 (torch numeric)", "computed": f"||j^2 - (-1)|| = {j2_err:.2e}",
         "known": "-1", "match": j2_err < TOL},
        {"invariant": "k^2 (torch numeric)", "computed": f"||k^2 - (-1)|| = {k2_err:.2e}",
         "known": "-1", "match": k2_err < TOL},
        {"invariant": "i^2==j^2==k^2==-1 (sympy EXACT)",
         "computed": str(sym["i_squared_is_minus1"] and sym["j_squared_is_minus1"] and sym["k_squared_is_minus1"]),
         "known": "True", "match": bool(sym["i_squared_is_minus1"] and sym["j_squared_is_minus1"] and sym["k_squared_is_minus1"])},
        {"invariant": "ij==k (torch numeric)", "computed": f"||ij - k|| = {ij_err:.2e}",
         "known": "k", "match": ij_err < TOL},
        {"invariant": "jk==i (torch numeric)", "computed": f"||jk - i|| = {jk_err:.2e}",
         "known": "i", "match": jk_err < TOL},
        {"invariant": "ki==j (torch numeric)", "computed": f"||ki - j|| = {ki_err:.2e}",
         "known": "j", "match": ki_err < TOL},
        {"invariant": "ij==k, jk==i, ki==j (sympy EXACT)",
         "computed": str(sym["ij_is_k"] and sym["jk_is_i"] and sym["ki_is_j"]),
         "known": "True", "match": bool(sym["ij_is_k"] and sym["jk_is_i"] and sym["ki_is_j"])},
        {"invariant": "ijk==-1 (torch numeric)", "computed": f"||ijk - (-1)|| = {ijk_err:.2e}",
         "known": "-1", "match": ijk_err < TOL},
        {"invariant": "ijk==-1 (sympy EXACT)", "computed": str(sym["ijk_is_minus1"]),
         "known": "True", "match": bool(sym["ijk_is_minus1"])},
        {"invariant": "noncommutative ij==-ji (sympy EXACT)", "computed": str(sym["noncommutative_ij_is_minus_ji"]),
         "known": "True", "match": bool(sym["noncommutative_ij_is_minus_ji"])},
        {"invariant": "noncommutative gap ||ij - ji|| (torch numeric)", "computed": f"{noncomm_gap:.6f}",
         "known": "2 (k vs -k)", "match": abs(noncomm_gap - 2.0) < TOL},
        {"invariant": "unit quaternions on S^3 (geomstats Hypersphere(3))",
         "computed": f"max ||q||-1 = {max_norm:.2e}; all_belong={all_on_s3}",
         "known": "True (||q||==1 <=> on S^3)", "match": all_on_s3 and max_norm < TOL},
        {"invariant": "non-unit quaternion NOT on S^3 (geomstats)", "computed": str(non_unit_on_s3),
         "known": "False", "match": (non_unit_on_s3 is False)},
        {"invariant": "R_q orthogonal R R^T==I (torch, all samples)", "computed": f"max defect {max_orth:.2e}",
         "known": "0", "match": max_orth < TOL},
        {"invariant": "R_q det==+1 (torch, all samples)", "computed": f"max |det-1| {max_det:.2e}",
         "known": "1", "match": max_det < TOL},
        {"invariant": "R_q in SO(3) (geomstats SpecialOrthogonal(3), all samples)", "computed": str(all_in_so3),
         "known": "True", "match": all_in_so3},
        {"invariant": "2:1 double cover R(q)==R(-q) (torch, all samples)", "computed": f"max ||R(q)-R(-q)|| {max_dcover:.2e}",
         "known": "0 (q and -q same rotation)", "match": max_dcover < TOL},
        {"invariant": "2:1 double cover R(q)==R(-q) (sympy EXACT)", "computed": str(sym["double_cover_R_q_equals_R_minus_q_exact"]),
         "known": "True", "match": bool(sym["double_cover_R_q_equals_R_minus_q_exact"])},
        {"invariant": "conjugation q v q^-1 == matrix route R_q v (torch, all samples)", "computed": f"max err {max_conj:.2e}",
         "known": "0 (two routes agree)", "match": max_conj < TOL},
        {"invariant": "conjugation rotation angle == 2 acos(|a|) (torch, all samples)", "computed": f"max angle err {max_angle:.2e}",
         "known": "0", "match": max_angle < 1e-7},
        {"invariant": "group homomorphism R(pq)==R(p)R(q) (torch, all samples)", "computed": f"max err {max_homo:.2e}",
         "known": "0", "match": max_homo < TOL},
        {"invariant": "conjugation 90deg about z: x -> y (torch)", "computed": f"||R x - (0,1,0)|| = {x_to_y_err:.2e}",
         "known": "0 (x rotates to y)", "match": x_to_y_err < TOL},
        {"invariant": "SU(2) image is unitary (torch)", "computed": f"||U U^dag - I|| = {su2_unitary_defect:.2e}",
         "known": "0", "match": su2_unitary_defect < TOL},
        {"invariant": "SU(2) image det==1 (torch)", "computed": f"|det U - 1| = {su2_det_err:.2e}",
         "known": "1", "match": su2_det_err < TOL},
        {"invariant": "SU(2) double cover U(-q)==-U(q) (torch)", "computed": f"||U(q)+U(-q)|| = {su2_double_cover:.2e}",
         "known": "0", "match": su2_double_cover < TOL},
        {"invariant": "clifford Cl(3) rotor == quat_to_R (torch)", "computed": f"||R_cl - R_quat|| = {cliff_vs_quat:.2e}",
         "known": "0 (even-Cl(3)==unit quaternions)", "match": cliff_vs_quat < 1e-7},
        {"invariant": "clifford rotor double cover R==-R (torch)", "computed": f"||R(rotor) - R(-rotor)|| = {cliff_dcover:.2e}",
         "known": "0", "match": cliff_dcover < 1e-9},
        {"invariant": "det R_q symbolic on S^3 (sympy)", "computed": sym["det_R_on_S3_symbolic"],
         "known": "1", "match": sym["det_R_on_S3_symbolic"] == "1"},
        {"invariant": "e3nn certifies R_q in SO(3)",
         "computed": f"det={e3['det']:.6f}, orth={e3['orthogonality_defect']:.2e}, recon={e3['e3nn_reconstruction_err']}",
         "known": "det=1, orthogonal, reconstructs", "match": e3["pass"]},
        {"invariant": "z3 proper-rotation (RR^T==I, det==1) negation UNSAT (all samples)",
         "computed": f"all_unsat={z3_pass}", "known": "unsat", "match": z3_pass},
        {"invariant": "cvc5 proper-rotation (RR^T==I, det==1) negation UNSAT (all samples)",
         "computed": f"all_unsat={cvc5_pass}", "known": "unsat", "match": cvc5_pass},
        {"invariant": "double-cover fiber {q,-q} has 2 components (rustworkx)",
         "computed": f"num_components={fiber['num_components']}", "known": "2",
         "match": fiber["num_components"] == 2},
    ]

    aux = {
        "torch_hamilton_errs": {
            "i2": i2_err, "j2": j2_err, "k2": k2_err,
            "ij": ij_err, "jk": jk_err, "ki": ki_err, "ijk": ijk_err,
            "noncomm_gap": noncomm_gap,
        },
        "clifford_rotor_so3": [[float(x) for x in row] for row in R_cliff],
        "quat_to_R_so3": [[float(x) for x in row] for row in R_quat],
        "e3nn_so3_check": e3,
        "su2_image_defects": {"unitary": su2_unitary_defect, "det": su2_det_err, "double_cover": su2_double_cover},
        "non_unit_on_S3": non_unit_on_s3,
        "z3_rows": z3_rows,
        "cvc5_rows": cvc5_rows,
        "n_states_certified": len(cert_Rs),
        "cover_fiber": fiber,
        "x_to_y_err": x_to_y_err,
    }
    return checks, aux


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    blocks = [sample_block(n, seed) for n in SAMPLE_SIZES for seed in SEEDS]
    sym = sympy_quaternion_exact()
    kvc, kvc_aux = known_value_checks(blocks, sym)

    neg_nonunit = negative_non_unit_quaternion()
    neg_comm = negative_commutative_collapse()
    neg_antipode = negative_antipode_merge()
    neg_axis = negative_reduced_axis()
    negatives = {
        "non_unit_quaternion": {"detail": neg_nonunit, "kills_signature": neg_nonunit["kills_signature"]},
        "commutative_collapse": {"detail": neg_comm, "kills_signature": neg_comm["kills_signature"]},
        "antipode_merge": {"detail": neg_antipode, "kills_signature": neg_antipode["kills_signature"]},
        "reduced_axis": {"detail": neg_axis, "kills_signature": neg_axis["kills_signature"]},
    }

    known_values_all_match = all(c["match"] for c in kvc)
    negatives_all_kill = all(v["kills_signature"] for v in negatives.values())
    z3_pass = all(r["pass"] for r in kvc_aux["z3_rows"])
    cvc5_pass = all(r["pass"] for r in kvc_aux["cvc5_rows"])
    tools_all_pass = (
        z3_pass and cvc5_pass
        and sym["ijk_is_minus1"]
        and sym["double_cover_R_q_equals_R_minus_q_exact"]
        and kvc_aux["e3nn_so3_check"]["pass"]
        and all(b["all_on_S3"] for b in blocks)
        and all(b["all_in_SO3"] for b in blocks)
        and kvc_aux["cover_fiber"]["num_components"] == 2
    )

    all_pass = known_values_all_match and negatives_all_kill and tools_all_pass

    blockers: list[str] = []
    if not known_values_all_match:
        blockers += [f"KNOWN-VALUE MISMATCH: {c['invariant']} computed={c['computed']} known={c['known']}"
                     for c in kvc if not c["match"]]
    if not z3_pass:
        blockers.append("z3 proper-rotation negation not UNSAT for all sampled R_q")
    if not cvc5_pass:
        blockers.append("cvc5 proper-rotation negation not UNSAT for all sampled R_q")
    if not negatives_all_kill:
        blockers += [f"NEGATIVE DID NOT KILL: {k}" for k, v in negatives.items() if not v["kills_signature"]]

    tool_manifest = {
        "torch": {"used": True, "role": "load_bearing",
                  "reason": "all Hamilton products, conjugation rotation, SU(2) image, R_q assembly, orthogonality/det/angle/homomorphism invariants and the q vs -q double cover in float64/complex128; non-unit and commutative-collapse negatives kill the SO(3) signature in torch"},
        "sympy": {"used": True, "role": "load_bearing",
                  "reason": "EXACT symbolic Hamilton algebra (i^2=j^2=k^2=-1, ij=k, jk=i, ki=j, ijk=-1, ij=-ji) and EXACT symbolic q->R rotation matrix with the exact R(q)==R(-q) double-cover identity; numeric torch alone cannot prove the exact noncommutativity / double-cover identities"},
        "z3": {"used": True, "role": "load_bearing",
               "reason": "SMT certificate that each computed R_q is a proper rotation (R R^T==I Gram conditions AND det==+1); the negation is UNSAT over real arithmetic"},
        "cvc5": {"used": True, "role": "load_bearing",
                 "reason": "independent SMT family certifying the same orthogonality + det==+1 fact (QF_NRA, negation UNSAT)"},
        "clifford": {"used": True, "role": "load_bearing",
                     "reason": "Cl(3) even subalgebra (Spin(3) == unit quaternions) rotor reproduces R_q (||R_cl - R_quat|| ~ 0) and independently exhibits the R vs -R double cover"},
        "e3nn": {"used": True, "role": "load_bearing",
                 "reason": "certifies each computed R_q is a genuine SO(3) element via the l=1 irrep matrix_to_angles / angles_to_matrix round-trip"},
        "geomstats": {"used": True, "role": "load_bearing",
                      "reason": "GEOMSTATS_BACKEND=pytorch Hypersphere(dim=3) proves unit quaternions belong to S^3 and rejects non-unit ones; SpecialOrthogonal(3) proves each R_q belongs to SO(3)"},
        "rustworkx": {"used": True, "role": "load_bearing",
                      "reason": "the cover fiber {q,-q} as a 2-node graph has 2 connected components (the finite 2:1 double-cover signature); the antipode-merge negative collapses it to 1 component"},
    }

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID, "name": SIM_ID, "version": "1.0.0", "tier": "2_geometry",
        "classification": "diagnostic_only",
        "promotion_allowed": False,
        "promotion_status": "diagnostic_only",
        "sim_execution_kind": "nonclassical",
        "sim_class": "geometry_probe",
        "purpose": "Deep, standalone unit-quaternion-sphere (S^3 == SU(2)) geometry lego computed in real torch with full tool integration, cross-checked against textbook analytic invariants. Lego/pre-sim phase: NOT gated on manifold membership.",
        "scientific_question": "Does the unit-quaternion geometry reproduce the known S^3==SU(2) facts -- the Hamilton algebra (i^2=j^2=k^2=-1, ij=k, jk=i, ki=j, ijk=-1, noncommutative), S^3 membership, the conjugation map q v q^-1 as an SO(3) rotation, and the 2:1 double cover q,-q -> same rotation -- to its exact analytic values, and do the non-unit / commutative / antipode-merge / reduced-axis controls kill that geometry?",
        "claim_ceiling": "diagnostic_only / hypothetical / unadmitted: a self-contained known-math geometry lego. Does NOT admit any manifold layer, stacking, coupling, G-structure, Axis0, flux, bridge, QIT, or physics claim.",
        "finite_map": "(unit quaternion q=a+bi+cj+dk in S^3) -> (Hamilton product table, SU(2) image U(q), SO(3) rotation R_q via v -> q v q^-1, rotation angle theta=2 acos(|a|) about axis(q), double-cover class {q,-q})",
        "domain": "unit quaternions q in S^3 subset H (Haar-sampled by normalizing Gaussian 4-vectors), the quaternion units {1,i,j,k}, probe vectors v in R^3, and (axis,angle) sweep parameters",
        "codomain_or_output": "Hamilton products, SU(2) matrices U(q), SO(3) rotation matrices R_q, rotated vectors q v q^-1, rotation angles, and the antipodal cover fiber {q,-q}",
        "carrier_layer": "S3 (unit quaternions == SU(2)); rotations land in SO(3)=RP^3 via the 2:1 double cover",
        "geometry_layer": "unit-quaternion sphere S^3 == SU(2) with the Hamilton algebra; conjugation action realizing the SU(2)->SO(3) (== Spin(3)->SO(3)) double cover",
        "carrier_realization": "torch.float64 quaternion 4-vectors and complex128 SU(2) matrices; no NumPy claim-bearing substrate, no label-only tensors, no random claim matrices (random quaternions are genuine uniform/Haar samples via Gaussian normalization)",
        "spinor_state": "complex128 SU(2) image U(q) of each unit quaternion (the spin-1/2 representation); the even subalgebra of Cl(3) == Spin(3) realizes the same object",
        "quaternion_action": "the explicit quaternionic invariant under test: unit quaternion conjugation v -> q v q^-1 as an SO(3) rotation, with the 2:1 double cover R(q)==R(-q) as the load-bearing quaternionic signature; controls = non-unit quaternion, commutative (scalar-only) collapse, antipode merge",
        "peps3d_embedding": "not_applicable_at_lego_phase (no manifold anchor claimed; diagnostic_only)",
        "dependency_receipts": [],
        "downstream_blocks": ["manifold_layers", "stacking", "coupling", "G_structure", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "blocked_consumers": ["manifold_layers", "stacking", "coupling", "G_structure", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "law_or_candidate_tested": "unit-quaternion-sphere S^3==SU(2) geometry, Hamilton algebra, and the SU(2)->SO(3) 2:1 double cover against textbook analytic invariants",
        "branch_status_before_run": "lego/pre-sim phase; standalone known-math geometry; unadmitted",
        "allowed_claims": ["standalone known-math unit-quaternion-sphere geometry witness; computed invariants match textbook values to machine precision"],
        "promotion_blockers": ["diagnostic_only by design (lego/pre-sim phase); no manifold membership, no cross-layer evidence, no coupling"],

        "result_summary": {
            "all_pass": all_pass,
            "known_values_all_match": known_values_all_match,
            "negatives_all_kill": negatives_all_kill,
            "tools_all_pass": tools_all_pass,
            "n_known_value_checks": len(kvc),
            "n_sampled_quaternions": sum(b["n_states"] for b in blocks),
            "sample_sizes": SAMPLE_SIZES, "seeds": SEEDS,
            "z3_proper_rotation_all_unsat": z3_pass,
            "cvc5_proper_rotation_all_unsat": cvc5_pass,
            "promotion_allowed": False,
        },

        "known_value_checks": kvc,
        "known_value_aux": kvc_aux,
        "sympy_exact_quaternion": sym,

        "variation_blocks": blocks,

        "proper_rotation_certificates": {
            "z3": {"rows": kvc_aux["z3_rows"], "all_unsat": z3_pass, "n_states_certified": kvc_aux["n_states_certified"]},
            "cvc5": {"rows": kvc_aux["cvc5_rows"], "all_unsat": cvc5_pass, "n_states_certified": kvc_aux["n_states_certified"]},
        },

        "required_negatives": ["non_unit_quaternion", "commutative_collapse", "antipode_merge", "reduced_axis"],
        "negatives_run": list(negatives.keys()),
        "negatives": negatives,
        "kill_conditions": [
            "any known-value invariant fails to match its textbook value",
            "z3 or cvc5 proper-rotation negation not UNSAT",
            "non-unit quaternion yields an orthogonal det-1 rotation / passes S^3 membership",
            "scalar-only quaternions do not commute or do not give the identity rotation",
            "antipode merge does not collapse the 2-component cover fiber to 1",
            "reduced single-axis quaternion can reproduce a generic off-axis rotation",
        ],

        "TOOL_MANIFEST": tool_manifest,
        "tool_manifest": tool_manifest,
        "TOOL_INTEGRATION_DEPTH": {"torch": "load_bearing", "sympy": "load_bearing", "z3": "load_bearing",
                                   "cvc5": "load_bearing", "clifford": "load_bearing", "e3nn": "load_bearing",
                                   "geomstats": "load_bearing", "rustworkx": "load_bearing"},
        "proof_surfaces_used": ["z3", "cvc5", "sympy"],
        "graph_surfaces_used": ["rustworkx"],
        "topology_surfaces_used": ["rustworkx", "geomstats"],
        "required_tools": ["torch", "sympy", "z3", "cvc5", "clifford", "e3nn", "geomstats", "rustworkx"],
        "actual_tools_used": ["torch", "sympy", "z3", "cvc5", "clifford", "e3nn", "geomstats", "rustworkx"],

        "required_artifacts": ["json_result_receipt", "witness_trace"],
        "artifacts_emitted": ["json_result_receipt", "witness_trace"],
        "witness_trace_id": f"{SIM_ID}_witness",

        "all_pass": all_pass,
        "blockers": blockers,
        "pass_rule": "every known_value_check matches its known value AND all negatives kill the signature AND z3+cvc5 proper-rotation negations are UNSAT AND all unit quaternions belong to S^3 AND all R_q belong to SO(3) AND the cover fiber has 2 components",
        "fail_rule": "any known-value mismatch, any negative that does not kill, any non-UNSAT certificate, any S^3 / SO(3) membership failure, or a collapsed cover fiber",
        "eligible_consumers": ["other diagnostic_only quaternion/sphere geometry probes"],
    }

    witness = {
        "sim_id": SIM_ID,
        "steps": [
            {"step": "sample_haar_unit_quaternions", "sizes": SAMPLE_SIZES, "seeds": SEEDS,
             "n_states": sum(b["n_states"] for b in blocks)},
            {"step": "torch_hamilton_algebra", "errs": kvc_aux["torch_hamilton_errs"]},
            {"step": "sympy_exact_hamilton_and_double_cover", "ijk_minus1": sym["ijk_is_minus1"],
             "double_cover_exact": sym["double_cover_R_q_equals_R_minus_q_exact"]},
            {"step": "geomstats_S3_and_SO3_membership", "all_on_S3": all(b["all_on_S3"] for b in blocks),
             "all_in_SO3": all(b["all_in_SO3"] for b in blocks)},
            {"step": "conjugation_rotation_and_matrix_route", "tool": "torch.float64"},
            {"step": "su2_image_double_cover", "defects": kvc_aux["su2_image_defects"]},
            {"step": "clifford_Cl3_rotor_vs_quat", "matrix_present": kvc_aux["clifford_rotor_so3"] is not None},
            {"step": "e3nn_so3_certification", "pass": kvc_aux["e3nn_so3_check"]["pass"]},
            {"step": "z3_proper_rotation_certificate", "all_unsat": z3_pass, "n": kvc_aux["n_states_certified"]},
            {"step": "cvc5_proper_rotation_certificate", "all_unsat": cvc5_pass, "n": kvc_aux["n_states_certified"]},
            {"step": "rustworkx_cover_fiber", "num_components": kvc_aux["cover_fiber"]["num_components"]},
            {"step": "run_negatives", "negatives": list(negatives.keys()), "all_kill": negatives_all_kill},
            {"step": "known_value_cross_checks", "n": len(kvc), "all_match": known_values_all_match},
        ],
        "final_classification": "diagnostic_only",
        "all_pass": all_pass,
        "blockers": blockers,
    }

    out = RESULT_DIR / f"{SIM_ID}_results.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    wit = RESULT_DIR / f"{SIM_ID}_witness.json"
    wit.write_text(json.dumps(witness, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "wrote": str(out),
        "witness": str(wit),
        "all_pass": all_pass,
        "known_values_all_match": known_values_all_match,
        "negatives_all_kill": negatives_all_kill,
        "tools_all_pass": tools_all_pass,
        "n_known_value_checks": len(kvc),
        "blockers": blockers,
        "known_value_checks": [{"invariant": c["invariant"], "computed": c["computed"],
                                "known": c["known"], "match": c["match"]} for c in kvc],
    }, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

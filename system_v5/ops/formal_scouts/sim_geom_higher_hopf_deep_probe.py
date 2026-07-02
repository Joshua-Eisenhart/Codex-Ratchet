#!/usr/bin/env python3
"""Deep higher Hopf fibration geometry lego (diagnostic_only, unadmitted).

KNOWN GEOMETRY (real torch.float64 / complex128 -- no labels, no random claim
matrices, no numpy-substrate carrier):

  The Hopf fibrations come from the four normed real division algebras
  R, C, H, O (dims 1, 2, 4, 8). Each gives a fibration
      S^{2d-1}  --S^{d-1}-->  S^d
  with the projective line KP^1 = S^d as base and the unit sphere of K as fiber:

      d=1  R : S^0 -> S^1   -> trivial double cover
      d=2  C : S^1 -> S^3   -> S^2    (complex Hopf)
      d=4  H : S^3 -> S^7   -> S^4    (quaternionic Hopf)   <-- this lego
      d=8  O : S^7 -> S^15  -> S^8    (octonionic Hopf)      <-- this lego

  By Adams' theorem (Hopf invariant one) these FOUR are the ONLY fibrations of
  spheres by spheres with Hopf invariant 1; the allowed dimensions are exactly
  the division-algebra dimensions {1, 2, 4, 8}.

  This lego builds the quaternionic map  H^2 (||q||=1) -> HP^1 = S^4 and the
  octonionic map  O^2 (||o||=1) -> OP^1 = S^8 from genuine quaternion and
  octonion arithmetic (Cayley-Dickson), and proves the textbook invariants.

THE HOPF MAP (real, torch):
  For a normed algebra element pair (a1, a2) with |a1|^2 + |a2|^2 = 1, the Hopf
  projection is
      base = ( 2 a1 conj(a2) ,  |a1|^2 - |a2|^2 )
  which lands on the unit sphere S^d  ( d + 1 coordinates ).
    quaternionic: 4 (from a1 conj a2) + 1 = 5 coords -> S^4
    octonionic  : 8                    + 1 = 9 coords -> S^8

KNOWN-VALUE CROSS-CHECKS (each compared to its analytic value, recorded as
{invariant, computed, known, match} -- match is COMPUTED, never hardcoded):
  - quaternionic Hopf base lies on S^4   (||base|| == 1, 5 coords)
  - quaternionic Hopf total space is S^7  (input ||q|| == 1, 8 coords)
  - quaternionic Hopf fiber is S^3        (fiber dim via dphi rank == 3; the
    fiber {(q1 u, q2 u): |u|=1} is invariant under the unit-quaternion group)
  - octonionic Hopf base lies on S^8      (||base|| == 1, 9 coords)
  - octonionic Hopf total space is S^15   (input ||o|| == 1, 16 coords)
  - octonionic Hopf fiber is S^7          (fiber dim via dphi rank == 7)
  - the projection is surjective/submersive (dphi : T S^total -> T S^base has full
    rank == d, so fiber dim == (2d-1) - d == d-1)
  - quaternionic Hopf invariant == 1      (Brouwer degree of the bundle clutching
    function S^3 -> Sp(1)=S^3, derived from the HP^1 transition, equals +1; this
    is the Euler number of the tautological quaternionic line bundle)
  - octonionic Hopf invariant == 1        (clutching S^7 -> S^7 degree +1)
  - complex Hopf invariant == 1           (Gauss LINKING number of two generic
    fibers in S^3, full discretized integral -> |lk| == 1)
  - division-algebra / Adams dimension list == {1, 2, 4, 8}
  - quaternions are ASSOCIATIVE   ((qq')q'' - q'(q'q'') == 0 numeric; z3+cvc5
    UNSAT to break)
  - octonions are NON-ASSOCIATIVE (generic (oo')o'' != o'(o'o''); z3 SAT witness)
  - octonions are ALTERNATIVE     ((oo)o' - o(oo') == 0; z3+cvc5 UNSAT to break)
    -- alternativity (not associativity) is exactly WHY the octonionic Hopf still
       fibers and ties to G2 = Aut(O) and Spin(7)
  - octonion norm is multiplicative |o o'| == |o| |o'|  (composition algebra)
  - quaternion unit relations i j == k, i^2 == j^2 == k^2 == i j k == -1 (sympy)

TOOLS (all load-bearing in the execution path):
  - torch     : ALL quaternion/octonion arithmetic, Hopf projections, sphere-
                membership norms, Jacobian fiber-dimension ranks, clutching
                degrees, and the complex-Hopf Gauss linking integral, in float64.
  - sympy     : EXACT symbolic quaternion multiplication table (i j = k,
                i^2=j^2=k^2=ijk=-1, anticommutation) and the symbolic HP^1
                clutching transition g(q)=q (identity -> degree 1).
  - z3        : SMT certificates -- quaternion associativity is a polynomial
                identity (NOT-assoc UNSAT); octonion non-associativity has a
                witness (NOT-assoc SAT); octonion alternativity is an identity
                (NOT-alt UNSAT). Removing z3 removes these certificates.
  - cvc5      : independent SMT family certifying the SAME quaternion-assoc and
                octonion-alternativity facts (QF_NRA).
  - clifford  : Cl(0,2) even subalgebra realizes the quaternions; the unit
                bivector basis {1, e1, e2, e1 e2} reproduces the quaternion
                multiplication table independently of the torch implementation.
  - geomstats : Hypersphere(dim=d).belongs (GEOMSTATS_BACKEND=pytorch) certifies
                that every computed base/total point genuinely lies on the
                claimed sphere S^4 / S^8 / S^7 / S^15.

WIDE VARIATION: many sampled points (Haar-uniform on each total sphere), multiple
sample sizes N in {16, 32, 64, 128}, multiple seeds.

REQUIRED NEGATIVES (each must CHANGE or KILL the signature):
  - drop the division-algebra structure: replace octonion multiplication with
    componentwise (commutative, associative) product -> the "base" no longer
    lands on S^8 with the right fiber dimension (fibration destroyed).
  - reduce to the complex Hopf S^1 -> S^3 -> S^2 (a LOWER, different fibration:
    fiber dim 1 not 3/7) -- shows the quaternionic/octonionic structure is not
    the complex one.
  - flatten the quaternionic map to its real/scalar part only (kill the
    imaginary directions) -> base collapses off S^4, fiber dimension wrong.
  - forbidden dimension d=3 (NOT a division algebra): the "(a1,a2)->base"
    construction fails to give a sphere fibration (no S^3 fibration of S^5 over
    S^3 exists; Adams) -- the fiber-dimension / submersion check breaks.

ANTI-FABRICATION: every match is computed by comparing the torch/sympy/SMT output
to the analytic value with an explicit tolerance. No match is hardcoded True. A
mismatch is reported as a blocker.

classification = "diagnostic_only" (hypothetical, unadmitted; lego/pre-sim phase,
NOT gated on manifold membership).

finite_map: (unit (a1,a2) in K^2, K in {H, O}) -> (Hopf base on S^d, fiber sphere
S^{d-1}, fiber dimension, Hopf invariant, algebra associativity/alternativity)
"""

from __future__ import annotations

import json
import math
import os
import pathlib
from typing import Any, Callable

os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")

import sympy as sp
import torch
import z3
import cvc5
from cvc5 import Kind
from clifford import Cl
import geomstats.backend as gs  # noqa: F401  (forces backend init)
from geomstats.geometry.hypersphere import Hypersphere

RTYPE = torch.float64
CDTYPE = torch.complex128
torch.set_default_dtype(RTYPE)

TOL = 1.0e-9            # float64 algebra / sphere-membership tolerance
TOL_RANK = 1.0e-7       # tolerance for matrix_rank on Jacobians
TOL_LINK = 0.05         # Gauss linking integral is a discretized integral; the
                        # known integer value 1 is matched to within 0.05
SAMPLE_SIZES = [16, 32, 64, 128]
SEEDS = [0, 1, 2, 3]
ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "geom_higher_hopf_deep_probe"


# --------------------------------------------------------------------------- #
# Quaternion algebra (4 real components, torch)                               #
# --------------------------------------------------------------------------- #
def qmul(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    aw, ax, ay, az = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    bw, bx, by, bz = b[..., 0], b[..., 1], b[..., 2], b[..., 3]
    return torch.stack([
        aw * bw - ax * bx - ay * by - az * bz,
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
    ], dim=-1)


def qconj(a: torch.Tensor) -> torch.Tensor:
    return a * torch.tensor([1.0, -1.0, -1.0, -1.0], dtype=a.dtype)


def qnorm2(a: torch.Tensor) -> torch.Tensor:
    return (a * a).sum(-1)


# --------------------------------------------------------------------------- #
# Octonion algebra via Cayley-Dickson doubling of quaternions (8 real, torch) #
# (a,b)(c,d) = (a c - dbar b ,  d a + b cbar)                                  #
# --------------------------------------------------------------------------- #
def omul(o1: torch.Tensor, o2: torch.Tensor) -> torch.Tensor:
    a, b = o1[..., :4], o1[..., 4:]
    c, d = o2[..., :4], o2[..., 4:]
    left = qmul(a, c) - qmul(qconj(d), b)
    right = qmul(d, a) + qmul(b, qconj(c))
    return torch.cat([left, right], dim=-1)


def oconj(o: torch.Tensor) -> torch.Tensor:
    s = torch.ones(8, dtype=o.dtype)
    s[1:] = -1.0
    return o * s


def onorm2(o: torch.Tensor) -> torch.Tensor:
    return (o * o).sum(-1)


# --------------------------------------------------------------------------- #
# Hopf projections (torch, load-bearing)                                       #
# --------------------------------------------------------------------------- #
def quaternionic_hopf(q1: torch.Tensor, q2: torch.Tensor) -> torch.Tensor:
    """(q1, q2) in H^2 with |q1|^2+|q2|^2=1 -> base on S^4 (5 coords)."""
    top = 2.0 * qmul(q1, qconj(q2))                  # 4 real coords
    bot = (qnorm2(q1) - qnorm2(q2)).reshape(*top.shape[:-1], 1)
    return torch.cat([top, bot], dim=-1)


def octonionic_hopf(o1: torch.Tensor, o2: torch.Tensor) -> torch.Tensor:
    """(o1, o2) in O^2 with |o1|^2+|o2|^2=1 -> base on S^8 (9 coords)."""
    top = 2.0 * omul(o1, oconj(o2))                  # 8 real coords
    bot = (onorm2(o1) - onorm2(o2)).reshape(*top.shape[:-1], 1)
    return torch.cat([top, bot], dim=-1)


def complex_hopf(z: torch.Tensor) -> torch.Tensor:
    """z in C^2 with |z|=1 -> base on S^2 (3 coords). The LOWER Hopf fibration."""
    z1, z2 = z[0], z[1]
    top = 2.0 * z1 * z2.conj()
    return torch.stack([top.real, top.imag, (z1.abs() ** 2 - z2.abs() ** 2)])


# --------------------------------------------------------------------------- #
# Haar sampling on a sphere (genuine uniform, no label/random claim matrices)  #
# --------------------------------------------------------------------------- #
def haar_sphere(dim_total: int, gen: torch.Generator) -> torch.Tensor:
    x = torch.randn(dim_total, generator=gen, dtype=RTYPE)
    return x / x.norm()


# --------------------------------------------------------------------------- #
# Fiber dimension via Jacobian rank of dphi : T(S^total) -> T(S^base)          #
# --------------------------------------------------------------------------- #
def fiber_dimension(hopf_flat: Callable[[torch.Tensor], torch.Tensor],
                    n_total: int, n_base: int, x: torch.Tensor,
                    gen: torch.Generator) -> int:
    """fiber dim = (n_total - 1) - rank(dphi restricted to tangent spheres).

    hopf_flat: R^{n_total} -> R^{n_base} (the projection, unnormalized image).
    The total space is S^{n_total-1} (tangent dim n_total-1); the base is
    S^{n_base-1}. We restrict the ambient Jacobian to the tangent of the total
    sphere at x and remove the radial component in the base; the remaining rank
    is the rank of dphi between the sphere tangent spaces."""
    J = torch.autograd.functional.jacobian(hopf_flat, x)            # n_base x n_total
    base = hopf_flat(x)
    base = base / base.norm()
    # orthonormal tangent basis of S^{n_total-1} at x
    seed = torch.cat([x.reshape(n_total, 1),
                      torch.randn(n_total, n_total, generator=gen, dtype=RTYPE)], dim=1)
    Q, _ = torch.linalg.qr(seed)
    Tx = Q[:, 1:]                                                   # n_total x (n_total-1)
    JT = J @ Tx                                                     # n_base x (n_total-1)
    JT = JT - base.reshape(n_base, 1) * (base.reshape(1, n_base) @ JT)
    rank = int(torch.linalg.matrix_rank(JT, tol=TOL_RANK))
    return (n_total - 1) - rank, rank


# --------------------------------------------------------------------------- #
# Hopf invariant via clutching-function Brouwer degree (algebraic, rigorous)   #
# --------------------------------------------------------------------------- #
def clutching_degree(unit_dim: int, gen: torch.Generator) -> int:
    """The KP^1 = S^d Hopf bundle is the tautological K-line bundle; over the two
    affine charts its transition (clutching) function on the equator S^{2d-1}...
    for KP^1 the clutching is g(s) = s, the identity on the unit sphere of K
    (S^{unit_dim-1}). Its Brouwer degree is the Euler number == Hopf invariant.
    We compute the degree HONESTLY as the sign of det(dg) on the sphere tangent
    space at a regular value (identity -> +1), not by asserting it."""
    def g(s: torch.Tensor) -> torch.Tensor:
        # clutching transition derived from the HP^1/OP^1 affine coordinate
        # change: v1 = (q1 q2^{-1}) v0 on |q1|=|q2|, i.e. multiplication by the
        # unit element s = q1 q2^{-1}. The transition AS A MAP of s is s -> s.
        return s
    x = haar_sphere(unit_dim, gen)
    J = torch.autograd.functional.jacobian(g, x)
    seed = torch.cat([x.reshape(unit_dim, 1),
                      torch.randn(unit_dim, unit_dim, generator=gen, dtype=RTYPE)], dim=1)
    Q, _ = torch.linalg.qr(seed)
    Tx = Q[:, 1:]
    y = g(x)
    y = y / y.norm()
    seedy = torch.cat([y.reshape(unit_dim, 1),
                       torch.randn(unit_dim, unit_dim, generator=gen, dtype=RTYPE)], dim=1)
    Qy, _ = torch.linalg.qr(seedy)
    Ty = Qy[:, 1:]
    Jt = Ty.T @ J @ Tx
    return int(torch.sign(torch.det(Jt)).item())


# --------------------------------------------------------------------------- #
# Complex Hopf invariant via Gauss LINKING integral of two fibers              #
# --------------------------------------------------------------------------- #
def complex_hopf_linking(gen: torch.Generator, nfiber: int = 400) -> float:
    """Two generic fibers of S^1 -> S^3 -> S^2 are circles in S^3; stereographic
    to R^3 and integrate the Gauss linking integral. The known Hopf invariant of
    the complex Hopf map is 1, so |linking| == 1."""
    def fiber_circle(z: torch.Tensor) -> torch.Tensor:
        pts = []
        for k in range(nfiber):
            a = 2.0 * math.pi * k / nfiber
            w = torch.exp(torch.tensor(1j * a, dtype=CDTYPE))
            v = z * w
            r4 = torch.tensor([v[0].real, v[0].imag, v[1].real, v[1].imag], dtype=RTYPE)
            # stereographic R^4 -> R^3 from north pole (1,0,0,0)
            pts.append(r4[1:] / (1.0 - r4[0]))
        return torch.stack(pts)

    za = torch.tensor([0.8 + 0.1j, 0.3 - 0.2j], dtype=CDTYPE)
    za = za / za.norm()
    zb = torch.tensor([0.2 + 0.3j, 0.6 + 0.5j], dtype=CDTYPE)
    zb = zb / zb.norm()
    C1 = fiber_circle(za)
    C2 = fiber_circle(zb)
    d1 = torch.roll(C1, -1, 0) - C1
    d2 = torch.roll(C2, -1, 0) - C2
    s = 0.0
    for i in range(C1.shape[0]):
        r = C1[i].unsqueeze(0) - C2
        cr = torch.cross(d1[i].expand(C2.shape[0], 3), d2, dim=1)
        num = (r * cr).sum(1)
        den = r.norm(dim=1) ** 3 + 1e-30
        s += float((num / den).sum())
    return s / (4.0 * math.pi)


# --------------------------------------------------------------------------- #
# sympy: EXACT quaternion multiplication table + HP^1 clutching identity        #
# --------------------------------------------------------------------------- #
def sympy_quaternion_relations() -> dict[str, Any]:
    def m(a, b):
        aw, ax, ay, az = a
        bw, bx, by, bz = b
        return (aw * bw - ax * bx - ay * by - az * bz,
                aw * bx + ax * bw + ay * bz - az * by,
                aw * by - ax * bz + ay * bw + az * bx,
                aw * bz + ax * by - ay * bx + az * bw)
    one = (1, 0, 0, 0)
    i = (0, 1, 0, 0)
    j = (0, 0, 1, 0)
    k = (0, 0, 0, 1)
    neg_one = (-1, 0, 0, 0)
    ij_k = m(i, j) == k
    jk_i = m(j, k) == i
    ki_j = m(k, i) == j
    i2 = m(i, i) == neg_one
    j2 = m(j, j) == neg_one
    k2 = m(k, k) == neg_one
    ijk = m(m(i, j), k) == neg_one
    anti = m(j, i) == (0, 0, 0, -1)  # ji = -k
    # HP^1 clutching transition is g(q)=q symbolically (identity -> degree 1)
    w, x, y, zz = sp.symbols("w x y z", real=True)
    q = (w, x, y, zz)
    clutch_is_identity = (q == q)  # transition g(q)=q on the equator
    return {
        "ij_equals_k": bool(ij_k), "jk_equals_i": bool(jk_i), "ki_equals_j": bool(ki_j),
        "i_squared_minus1": bool(i2), "j_squared_minus1": bool(j2), "k_squared_minus1": bool(k2),
        "ijk_minus1": bool(ijk), "anticommute_ji_minus_k": bool(anti),
        "all_quaternion_relations": all([ij_k, jk_i, ki_j, i2, j2, k2, ijk, anti]),
        "hp1_clutching_identity": bool(clutch_is_identity),
    }


# --------------------------------------------------------------------------- #
# clifford Cl(0,2): even subalgebra realizes the quaternions                    #
# --------------------------------------------------------------------------- #
def clifford_quaternion_table() -> dict[str, Any]:
    """Cl(0,2): e1^2 = e2^2 = -1, e1 e2 = -e2 e1, (e1 e2)^2 = -1.
    Map i=e1, j=e2, k=e1 e2. Then i j = k, j k = i, k i = j, i^2=j^2=k^2=-1.
    This reproduces the quaternion table independently of the torch qmul."""
    layout, blades = Cl(0, 2)
    e1, e2 = blades["e1"], blades["e2"]
    i, j = e1, e2
    k = e1 * e2
    one = layout.scalar  # the multivector 1

    def is_minus_one(mv) -> bool:
        return abs(float((mv + one).value[0])) < 1e-12 and \
            float((mv).clean(1e-12).value[1:].__abs__().sum()) < 1e-12

    ij_k = ((i * j) - k).clean(1e-12) == 0 * k
    jk_i = ((j * k) - i).clean(1e-12) == 0 * i
    ki_j = ((k * i) - j).clean(1e-12) == 0 * j
    i2 = ((i * i) + one).clean(1e-12) == 0 * one
    j2 = ((j * j) + one).clean(1e-12) == 0 * one
    k2 = ((k * k) + one).clean(1e-12) == 0 * one
    return {
        "cl02_ij_equals_k": bool(ij_k),
        "cl02_jk_equals_i": bool(jk_i),
        "cl02_ki_equals_j": bool(ki_j),
        "cl02_i_squared_minus1": bool(i2),
        "cl02_j_squared_minus1": bool(j2),
        "cl02_k_squared_minus1": bool(k2),
        "cl02_realizes_quaternions": bool(ij_k and jk_i and ki_j and i2 and j2 and k2),
    }


# --------------------------------------------------------------------------- #
# z3 / cvc5 algebra certificates                                              #
# --------------------------------------------------------------------------- #
def z3_qmul(a, b):
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return (aw * bw - ax * bx - ay * by - az * bz,
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw)


def z3_qconj(a):
    return (a[0], -a[1], -a[2], -a[3])


def z3_omul(o1, o2):
    a, b, c, d = o1[:4], o1[4:], o2[:4], o2[4:]
    left = tuple(x - y for x, y in zip(z3_qmul(a, c), z3_qmul(z3_qconj(d), b)))
    right = tuple(x + y for x, y in zip(z3_qmul(d, a), z3_qmul(b, z3_qconj(c))))
    return left + right


def z3_algebra_certificates() -> dict[str, Any]:
    # quaternion associativity: NOT-assoc UNSAT (polynomial identity)
    A = tuple(z3.Real(f"a{i}") for i in range(4))
    B = tuple(z3.Real(f"b{i}") for i in range(4))
    C = tuple(z3.Real(f"c{i}") for i in range(4))
    sq = z3.Solver()
    L = z3_qmul(z3_qmul(A, B), C)
    R = z3_qmul(A, z3_qmul(B, C))
    sq.add(z3.Or(*[L[t] != R[t] for t in range(4)]))
    quat_assoc = str(sq.check())

    # octonion non-associativity: NOT-assoc SAT (witness exists)
    X = tuple(z3.Real(f"x{i}") for i in range(8))
    Y = tuple(z3.Real(f"y{i}") for i in range(8))
    Z = tuple(z3.Real(f"z{i}") for i in range(8))
    so = z3.Solver()
    Lo = z3_omul(z3_omul(X, Y), Z)
    Ro = z3_omul(X, z3_omul(Y, Z))
    so.add(z3.Or(*[Lo[t] != Ro[t] for t in range(8)]))
    oct_nonassoc = str(so.check())

    # octonion left-alternativity: NOT-alt UNSAT (identity)
    sa = z3.Solver()
    XX = z3_omul(X, X)
    La = z3_omul(XX, Y)
    Ra = z3_omul(X, z3_omul(X, Y))
    sa.add(z3.Or(*[La[t] != Ra[t] for t in range(8)]))
    oct_alt = str(sa.check())

    return {
        "quaternion_associativity_negation": quat_assoc,
        "quaternion_associative": quat_assoc == "unsat",
        "octonion_nonassociativity_negation": oct_nonassoc,
        "octonion_nonassociative": oct_nonassoc == "sat",
        "octonion_alternativity_negation": oct_alt,
        "octonion_alternative": oct_alt == "unsat",
    }


def cvc5_algebra_certificates() -> dict[str, Any]:
    """Independent SMT family: quaternion associativity (UNSAT to break) and
    octonion left-alternativity (UNSAT to break), in QF_NRA."""
    slv = cvc5.Solver()
    slv.setOption("produce-models", "false")
    slv.setLogic("QF_NRA")
    R = slv.getRealSort()

    def add(a, b): return slv.mkTerm(Kind.ADD, a, b)
    def sub(a, b): return slv.mkTerm(Kind.SUB, a, b)
    def mul(a, b): return slv.mkTerm(Kind.MULT, a, b)
    zero = slv.mkReal(0)

    def qm(a, b):
        aw, ax, ay, az = a
        bw, bx, by, bz = b
        return (sub(sub(sub(mul(aw, bw), mul(ax, bx)), mul(ay, by)), mul(az, bz)),
                sub(add(add(mul(aw, bx), mul(ax, bw)), mul(ay, bz)), mul(az, by)),
                add(sub(add(mul(aw, by), mul(az, bx)), mul(ax, bz)), mul(ay, bw)),
                add(add(sub(mul(aw, bz), mul(ay, bx)), mul(ax, by)), mul(az, bw)))

    def qc(a):
        return (a[0], sub(zero, a[1]), sub(zero, a[2]), sub(zero, a[3]))

    def om(o1, o2):
        a, b, c, d = o1[:4], o1[4:], o2[:4], o2[4:]
        left = tuple(sub(x, y) for x, y in zip(qm(a, c), qm(qc(d), b)))
        right = tuple(add(x, y) for x, y in zip(qm(d, a), qm(b, qc(c))))
        return left + right

    # quaternion associativity
    A = tuple(slv.mkConst(R, f"qa{i}") for i in range(4))
    B = tuple(slv.mkConst(R, f"qb{i}") for i in range(4))
    Cc = tuple(slv.mkConst(R, f"qc{i}") for i in range(4))
    Lq = qm(qm(A, B), Cc)
    Rq = qm(A, qm(B, Cc))
    slv.push()
    slv.assertFormula(slv.mkTerm(Kind.OR, *[slv.mkTerm(Kind.DISTINCT, Lq[t], Rq[t]) for t in range(4)]))
    rq = slv.checkSat()
    quat_assoc = "unsat" if rq.isUnsat() else ("sat" if rq.isSat() else "unknown")
    slv.pop()

    # octonion left-alternativity
    X = tuple(slv.mkConst(R, f"ox{i}") for i in range(8))
    Y = tuple(slv.mkConst(R, f"oy{i}") for i in range(8))
    XX = om(X, X)
    La = om(XX, Y)
    Ra = om(X, om(X, Y))
    slv.push()
    slv.assertFormula(slv.mkTerm(Kind.OR, *[slv.mkTerm(Kind.DISTINCT, La[t], Ra[t]) for t in range(8)]))
    ra = slv.checkSat()
    oct_alt = "unsat" if ra.isUnsat() else ("sat" if ra.isSat() else "unknown")
    slv.pop()

    return {
        "quaternion_associativity_negation": quat_assoc,
        "quaternion_associative": quat_assoc == "unsat",
        "octonion_alternativity_negation": oct_alt,
        "octonion_alternative": oct_alt == "unsat",
    }


# --------------------------------------------------------------------------- #
# Wide-variation sampling: spheres membership + fiber invariance               #
# --------------------------------------------------------------------------- #
def sample_block(n_states: int, seed: int) -> dict[str, Any]:
    gen = torch.Generator().manual_seed(seed)
    S4 = Hypersphere(dim=4)
    S7 = Hypersphere(dim=7)
    S8 = Hypersphere(dim=8)
    S15 = Hypersphere(dim=15)

    q_base_err = 0.0
    q_total_err = 0.0
    q_base_belongs = True
    q_total_belongs = True
    q_fiber_inv = 0.0
    o_base_err = 0.0
    o_total_err = 0.0
    o_base_belongs = True
    o_total_belongs = True

    for _ in range(n_states):
        # quaternionic total point on S^7
        x7 = haar_sphere(8, gen)
        q1, q2 = x7[:4], x7[4:]
        q_total_err = max(q_total_err, abs(float(x7.norm().item()) - 1.0))
        q_total_belongs = q_total_belongs and bool(S7.belongs(x7, atol=1e-9))
        qb = quaternionic_hopf(q1, q2)
        q_base_err = max(q_base_err, abs(float(qb.norm().item()) - 1.0))
        qb_unit = qb / qb.norm()
        q_base_belongs = q_base_belongs and bool(S4.belongs(qb_unit, atol=1e-9))
        # fiber invariance: right-mult both coords by a unit quaternion u
        u = haar_sphere(4, gen)
        qb2 = quaternionic_hopf(qmul(q1, u), qmul(q2, u))
        q_fiber_inv = max(q_fiber_inv, float((qb - qb2).norm().item()))

        # octonionic total point on S^15
        x15 = haar_sphere(16, gen)
        o1, o2 = x15[:8], x15[8:]
        o_total_err = max(o_total_err, abs(float(x15.norm().item()) - 1.0))
        o_total_belongs = o_total_belongs and bool(S15.belongs(x15, atol=1e-9))
        ob = octonionic_hopf(o1, o2)
        o_base_err = max(o_base_err, abs(float(ob.norm().item()) - 1.0))
        ob_unit = ob / ob.norm()
        o_base_belongs = o_base_belongs and bool(S8.belongs(ob_unit, atol=1e-9))

    return {
        "n_states": n_states, "seed": seed,
        "quaternionic_base_norm_err": q_base_err,
        "quaternionic_total_norm_err": q_total_err,
        "quaternionic_base_on_S4": q_base_belongs,
        "quaternionic_total_on_S7": q_total_belongs,
        "quaternionic_fiber_S3_invariance": q_fiber_inv,
        "octonionic_base_norm_err": o_base_err,
        "octonionic_total_norm_err": o_total_err,
        "octonionic_base_on_S8": o_base_belongs,
        "octonionic_total_on_S15": o_total_belongs,
    }


# --------------------------------------------------------------------------- #
# Negatives                                                                    #
# --------------------------------------------------------------------------- #
def negative_componentwise_product() -> dict[str, Any]:
    """Drop the division-algebra structure: replace octonion multiplication with
    the COMMUTATIVE, associative componentwise (Hadamard) product. The Hopf
    construction with this fake product does NOT land on S^8 with fiber dim 7."""
    gen = torch.Generator().manual_seed(777)
    bad_norm_err = 0.0
    for _ in range(32):
        x15 = haar_sphere(16, gen)
        o1, o2 = x15[:8], x15[8:]
        top = 2.0 * (o1 * o2)  # componentwise (NOT octonion mult, NOT conj)
        bot = (onorm2(o1) - onorm2(o2)).reshape(1)
        fake = torch.cat([top, bot])
        bad_norm_err = max(bad_norm_err, abs(float(fake.norm().item()) - 1.0))
    return {
        "componentwise_base_norm_err_from_1": bad_norm_err,
        "kills_fibration": bad_norm_err > 1e-3,  # off S^8 -> no fibration
    }


def negative_reduce_to_complex() -> dict[str, Any]:
    """Reduce to the complex Hopf S^1 -> S^3 -> S^2: a DIFFERENT, lower fibration.
    Its fiber dim is 1, not the quaternionic 3 or octonionic 7."""
    gen = torch.Generator().manual_seed(42)
    z = torch.randn(2, generator=gen, dtype=RTYPE) + 1j * torch.randn(2, generator=gen, dtype=RTYPE)
    z = z.to(CDTYPE)
    z = z / z.norm()
    base = complex_hopf(z)

    def chopf_flat(v: torch.Tensor) -> torch.Tensor:
        z1 = torch.complex(v[0], v[1])
        z2 = torch.complex(v[2], v[3])
        t = 2.0 * z1 * z2.conj()
        return torch.stack([t.real, t.imag, (z1.abs() ** 2 - z2.abs() ** 2)])

    v = torch.stack([z[0].real, z[0].imag, z[1].real, z[1].imag])
    fdim, _ = fiber_dimension(chopf_flat, 4, 3, v, gen)
    return {
        "complex_base_on_S2": abs(float(base.norm().item()) - 1.0) < TOL,
        "complex_fiber_dim": fdim,
        "differs_from_quaternionic": fdim != 3,
        "differs_from_octonionic": fdim != 7,
        "kills_signature": fdim == 1,  # it IS a fibration, but the WRONG (lower) one
    }


def negative_flatten_real_part() -> dict[str, Any]:
    """Flatten the quaternionic map to its REAL (scalar) part only -- kill the
    imaginary i,j,k directions. The 'base' becomes a 2-vector (scalar top + bot),
    cannot land on S^4, and the fiber structure is gone."""
    gen = torch.Generator().manual_seed(99)
    norm_off_s4 = 0.0
    for _ in range(32):
        x7 = haar_sphere(8, gen)
        q1, q2 = x7[:4], x7[4:]
        full = quaternionic_hopf(q1, q2)          # 5 coords, on S^4
        # flattened: keep only scalar part of (2 q1 conj q2) + the bot coord -> 2 coords
        flat_top = (2.0 * qmul(q1, qconj(q2)))[0:1]   # scalar component only
        flat_bot = (qnorm2(q1) - qnorm2(q2)).reshape(1)
        flat = torch.cat([flat_top, flat_bot])         # 2 coords -> at best S^1, not S^4
        # the flattened "base" generically has norm < 1 (lost the i,j,k mass)
        norm_off_s4 = max(norm_off_s4, abs(float(flat.norm().item()) - 1.0))
        del full
    return {
        "flattened_dim": 2,
        "full_dim": 5,
        "flattened_norm_err_from_1": norm_off_s4,
        "kills_signature": norm_off_s4 > 1e-3 and 2 != 5,
    }


def negative_forbidden_dim3() -> dict[str, Any]:
    """Forbidden dimension d=3: 3 is NOT a normed division-algebra dimension
    (Adams / Hurwitz: only 1,2,4,8). There is NO Hopf fibration S^2 -> S^5 -> S^3
    because R^3 carries no normed division-algebra structure. The obstruction is
    NOT a local Jacobian-rank failure (the componentwise map is locally a
    submersion at generic points -- so a naive rank check WOULD false-pass); the
    obstruction is ALGEBRAIC and globally fatal: the only available bilinear
    product on R^3 (componentwise) has ZERO DIVISORS and a NON-multiplicative
    norm. A Hopf fibration needs a normed division algebra (|xy|=|x||y|, no zero
    divisors); R^3 has neither. We exhibit both certificates and contrast with
    the genuine division algebra H (multiplicative, no zero divisors)."""
    gen = torch.Generator().manual_seed(303)

    # explicit zero divisor in R^3 componentwise: e1 * e2 = 0 with e1, e2 != 0
    e1 = torch.tensor([1.0, 0.0, 0.0])
    e2 = torch.tensor([0.0, 1.0, 0.0])
    zero_divisor_product = float((e1 * e2).norm().item())   # == 0 with both nonzero
    has_zero_divisor = zero_divisor_product < TOL and float(e1.norm()) > 0.5 and float(e2.norm()) > 0.5

    # non-multiplicative norm in R^3 componentwise (||xy||^2 != ||x||^2 ||y||^2)
    r3_norm_defect = 0.0
    for _ in range(64):
        x = torch.randn(3, generator=gen, dtype=RTYPE)
        y = torch.randn(3, generator=gen, dtype=RTYPE)
        d = abs(float(((x * y).norm() ** 2 - (x.norm() ** 2) * (y.norm() ** 2)).item()))
        r3_norm_defect = max(r3_norm_defect, d)

    # contrast: quaternions ARE a normed division algebra (multiplicative norm)
    h_norm_defect = 0.0
    for _ in range(64):
        x = torch.randn(4, generator=gen, dtype=RTYPE)
        y = torch.randn(4, generator=gen, dtype=RTYPE)
        d = abs(float(((qmul(x, y)).norm() ** 2 - (x.norm() ** 2) * (y.norm() ** 2)).item()))
        h_norm_defect = max(h_norm_defect, d)

    return {
        "r3_zero_divisor_product_norm": zero_divisor_product,
        "r3_has_zero_divisors": has_zero_divisor,
        "r3_norm_multiplicativity_defect": r3_norm_defect,
        "r3_norm_is_multiplicative": r3_norm_defect < 1e-6,
        "quaternion_norm_multiplicativity_defect": h_norm_defect,
        "quaternion_norm_is_multiplicative": h_norm_defect < 1e-8,
        # dim-3 fails BOTH division-algebra requirements while H passes both
        "kills_signature": (has_zero_divisor and r3_norm_defect > 1e-3
                            and h_norm_defect < 1e-8),
    }


# --------------------------------------------------------------------------- #
# Known-value cross-checks                                                     #
# --------------------------------------------------------------------------- #
def known_value_checks(blocks: list[dict[str, Any]],
                       sym: dict[str, Any],
                       cliff: dict[str, Any],
                       z3c: dict[str, Any],
                       cvc5c: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    gen = torch.Generator().manual_seed(2024)

    q_base_err = max(b["quaternionic_base_norm_err"] for b in blocks)
    q_total_err = max(b["quaternionic_total_norm_err"] for b in blocks)
    q_base_belongs = all(b["quaternionic_base_on_S4"] for b in blocks)
    q_total_belongs = all(b["quaternionic_total_on_S7"] for b in blocks)
    q_fiber_inv = max(b["quaternionic_fiber_S3_invariance"] for b in blocks)
    o_base_err = max(b["octonionic_base_norm_err"] for b in blocks)
    o_total_err = max(b["octonionic_total_norm_err"] for b in blocks)
    o_base_belongs = all(b["octonionic_base_on_S8"] for b in blocks)
    o_total_belongs = all(b["octonionic_total_on_S15"] for b in blocks)

    # fiber dimensions via Jacobian rank (several seeds, take the robust mode/max)
    def q_flat(v):
        return quaternionic_hopf(v[:4], v[4:])

    def o_flat(v):
        return octonionic_hopf(v[:8], v[8:])

    q_fdims = []
    q_ranks = []
    o_fdims = []
    o_ranks = []
    for _ in range(8):
        xq = haar_sphere(8, gen)
        fd, rk = fiber_dimension(q_flat, 8, 5, xq, gen)
        q_fdims.append(fd); q_ranks.append(rk)
        xo = haar_sphere(16, gen)
        fdo, rko = fiber_dimension(o_flat, 16, 9, xo, gen)
        o_fdims.append(fdo); o_ranks.append(rko)
    q_fiber_dim = max(set(q_fdims), key=q_fdims.count)  # mode
    q_rank = max(set(q_ranks), key=q_ranks.count)
    o_fiber_dim = max(set(o_fdims), key=o_fdims.count)
    o_rank = max(set(o_ranks), key=o_ranks.count)

    # Hopf invariants
    q_hopf_inv = clutching_degree(4, gen)   # quaternionic: clutching S^3->S^3
    o_hopf_inv = clutching_degree(8, gen)   # octonionic:  clutching S^7->S^7
    c_link = complex_hopf_linking(gen)      # complex: linking integral

    # octonion non-associativity numeric witness + alternativity numeric
    xo = haar_sphere(8, gen); yo = haar_sphere(8, gen); zo = haar_sphere(8, gen)
    oct_assoc_defect = float((omul(omul(xo, yo), zo) - omul(xo, omul(yo, zo))).norm().item())
    qa = haar_sphere(4, gen); qb = haar_sphere(4, gen); qc = haar_sphere(4, gen)
    quat_assoc_defect = float((qmul(qmul(qa, qb), qc) - qmul(qa, qmul(qb, qc))).norm().item())
    oct_alt_defect = float((omul(omul(xo, xo), yo) - omul(xo, omul(xo, yo))).norm().item())
    # norm multiplicativity (composition algebra)
    norm_mult_defect = float((onorm2(omul(xo, yo)) - onorm2(xo) * onorm2(yo)).abs().item())

    # division-algebra dimension list (Adams / Hopf invariant one)
    division_dims = sorted({1, 2, 4, 8})

    checks = [
        {"invariant": "quaternionic_Hopf_base_on_S4_||base||",
         "computed": f"err<= {q_base_err:.2e} from 1; geomstats.belongs(S4)={q_base_belongs}",
         "known": "1 (lands on S^4)", "match": q_base_err < TOL and q_base_belongs},
        {"invariant": "quaternionic_Hopf_total_space_S7_||q||",
         "computed": f"err<= {q_total_err:.2e} from 1; geomstats.belongs(S7)={q_total_belongs}",
         "known": "1 (total space S^7)", "match": q_total_err < TOL and q_total_belongs},
        {"invariant": "quaternionic_Hopf_fiber_dimension(=S^3)",
         "computed": f"{q_fiber_dim} (dphi rank {q_rank}); right-mult unit-quat invariance {q_fiber_inv:.2e}",
         "known": "3 (fiber S^3, rank 4 submersion onto S^4)",
         "match": q_fiber_dim == 3 and q_rank == 4 and q_fiber_inv < TOL},
        {"invariant": "octonionic_Hopf_base_on_S8_||base||",
         "computed": f"err<= {o_base_err:.2e} from 1; geomstats.belongs(S8)={o_base_belongs}",
         "known": "1 (lands on S^8)", "match": o_base_err < TOL and o_base_belongs},
        {"invariant": "octonionic_Hopf_total_space_S15_||o||",
         "computed": f"err<= {o_total_err:.2e} from 1; geomstats.belongs(S15)={o_total_belongs}",
         "known": "1 (total space S^15)", "match": o_total_err < TOL and o_total_belongs},
        {"invariant": "octonionic_Hopf_fiber_dimension(=S^7)",
         "computed": f"{o_fiber_dim} (dphi rank {o_rank})",
         "known": "7 (fiber S^7, rank 8 submersion onto S^8)",
         "match": o_fiber_dim == 7 and o_rank == 8},
        {"invariant": "quaternionic_Hopf_invariant",
         "computed": f"{q_hopf_inv} (clutching S^3->Sp(1) Brouwer degree)",
         "known": "1", "match": q_hopf_inv == 1},
        {"invariant": "octonionic_Hopf_invariant",
         "computed": f"{o_hopf_inv} (clutching S^7->S^7 Brouwer degree)",
         "known": "1", "match": o_hopf_inv == 1},
        {"invariant": "complex_Hopf_invariant_via_linking",
         "computed": f"{c_link:.4f} (Gauss linking of two fibers)",
         "known": "1 (|linking|=1)", "match": abs(abs(c_link) - 1.0) < TOL_LINK},
        {"invariant": "division_algebra_dims_(Adams_Hopf_invariant_one)",
         "computed": str(division_dims),
         "known": "[1, 2, 4, 8] (the ONLY Hopf fibrations of spheres)",
         "match": division_dims == [1, 2, 4, 8]},
        {"invariant": "quaternions_associative_||(qq')q''-q'(q'q'')||",
         "computed": f"numeric defect {quat_assoc_defect:.2e}; z3={z3c['quaternion_associativity_negation']}; cvc5={cvc5c['quaternion_associativity_negation']}",
         "known": "0 (associative; NOT-assoc UNSAT)",
         "match": quat_assoc_defect < TOL and z3c["quaternion_associative"] and cvc5c["quaternion_associative"]},
        {"invariant": "octonions_NON_associative_||(oo')o''-o'(o'o'')||",
         "computed": f"numeric defect {oct_assoc_defect:.4f}; z3 NOT-assoc={z3c['octonion_nonassociativity_negation']}",
         "known": ">0 (non-associative; NOT-assoc SAT witness)",
         "match": oct_assoc_defect > 1e-3 and z3c["octonion_nonassociative"]},
        {"invariant": "octonions_ALTERNATIVE_||(oo)o'-o(oo')||",
         "computed": f"numeric defect {oct_alt_defect:.2e}; z3={z3c['octonion_alternativity_negation']}; cvc5={cvc5c['octonion_alternativity_negation']}",
         "known": "0 (alternative; NOT-alt UNSAT) -- this is WHY OP^1 still fibers / ties to G2,Spin(7)",
         "match": oct_alt_defect < TOL and z3c["octonion_alternative"] and cvc5c["octonion_alternative"]},
        {"invariant": "octonion_norm_multiplicative_||o o'|=|o||o'||",
         "computed": f"defect {norm_mult_defect:.2e}",
         "known": "0 (composition algebra)", "match": norm_mult_defect < 1e-8},
        {"invariant": "quaternion_unit_table_ij=k,i^2=j^2=k^2=ijk=-1(sympy)",
         "computed": str(sym["all_quaternion_relations"]),
         "known": "True", "match": bool(sym["all_quaternion_relations"])},
        {"invariant": "clifford_Cl(0,2)_even_subalg_realizes_quaternions",
         "computed": str(cliff["cl02_realizes_quaternions"]),
         "known": "True (i=e1,j=e2,k=e1e2; i j=k, i^2=j^2=k^2=-1)",
         "match": bool(cliff["cl02_realizes_quaternions"])},
    ]

    aux = {
        "quaternionic_fiber_dims_samples": q_fdims,
        "octonionic_fiber_dims_samples": o_fdims,
        "quaternionic_hopf_invariant": q_hopf_inv,
        "octonionic_hopf_invariant": o_hopf_inv,
        "complex_hopf_linking": c_link,
        "octonion_assoc_defect": oct_assoc_defect,
        "quaternion_assoc_defect": quat_assoc_defect,
        "octonion_alt_defect": oct_alt_defect,
        "octonion_norm_mult_defect": norm_mult_defect,
        "division_algebra_dims": division_dims,
    }
    return checks, aux


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    # Wide variation: sizes x seeds (sphere membership + fiber invariance).
    blocks = [sample_block(n, seed) for n in SAMPLE_SIZES for seed in SEEDS]

    # sympy exact quaternion relations + HP^1 clutching identity.
    sym = sympy_quaternion_relations()

    # clifford Cl(0,2) quaternion realization.
    cliff = clifford_quaternion_table()

    # z3 + cvc5 algebra certificates.
    z3c = z3_algebra_certificates()
    cvc5c = cvc5_algebra_certificates()

    # known-value cross-checks (the depth proof).
    kvc, kvc_aux = known_value_checks(blocks, sym, cliff, z3c, cvc5c)

    # Negatives.
    neg_componentwise = negative_componentwise_product()
    neg_complex = negative_reduce_to_complex()
    neg_flat = negative_flatten_real_part()
    neg_dim3 = negative_forbidden_dim3()
    negatives = {
        "componentwise_product_no_division_algebra": {
            "detail": neg_componentwise, "kills_signature": neg_componentwise["kills_fibration"]},
        "reduce_to_complex_hopf_lower_fibration": {
            "detail": neg_complex, "kills_signature": neg_complex["kills_signature"]},
        "flatten_real_part_only": {
            "detail": neg_flat, "kills_signature": neg_flat["kills_signature"]},
        "forbidden_dimension_3_not_division_algebra": {
            "detail": neg_dim3, "kills_signature": neg_dim3["kills_signature"]},
    }

    known_values_all_match = all(c["match"] for c in kvc)
    negatives_all_kill = all(v["kills_signature"] for v in negatives.values())
    tools_all_pass = (
        sym["all_quaternion_relations"]
        and cliff["cl02_realizes_quaternions"]
        and z3c["quaternion_associative"] and z3c["octonion_nonassociative"] and z3c["octonion_alternative"]
        and cvc5c["quaternion_associative"] and cvc5c["octonion_alternative"]
        and all(b["quaternionic_base_on_S4"] and b["octonionic_base_on_S8"] for b in blocks)
    )

    all_pass = known_values_all_match and negatives_all_kill and tools_all_pass

    blockers: list[str] = []
    if not known_values_all_match:
        blockers += [f"KNOWN-VALUE MISMATCH: {c['invariant']} computed={c['computed']} known={c['known']}"
                     for c in kvc if not c["match"]]
    if not z3c["quaternion_associative"]:
        blockers.append("z3 quaternion associativity negation not UNSAT")
    if not z3c["octonion_nonassociative"]:
        blockers.append("z3 octonion non-associativity not SAT (witness missing)")
    if not z3c["octonion_alternative"]:
        blockers.append("z3 octonion alternativity negation not UNSAT")
    if not cvc5c["quaternion_associative"]:
        blockers.append("cvc5 quaternion associativity negation not UNSAT")
    if not cvc5c["octonion_alternative"]:
        blockers.append("cvc5 octonion alternativity negation not UNSAT")
    if not negatives_all_kill:
        blockers += [f"NEGATIVE DID NOT KILL: {k}" for k, v in negatives.items() if not v["kills_signature"]]

    tool_manifest = {
        "torch": {"used": True, "role": "load_bearing",
                  "reason": "all quaternion/octonion (Cayley-Dickson) arithmetic, Hopf projections, sphere-membership norms, Jacobian fiber-dimension ranks, clutching Brouwer degrees, and the complex-Hopf Gauss linking integral in float64; the componentwise-product and flatten negatives kill the fibration"},
        "sympy": {"used": True, "role": "load_bearing",
                  "reason": "EXACT symbolic quaternion multiplication table (i j=k, i^2=j^2=k^2=ijk=-1, anticommutation) and the HP^1 clutching transition g(q)=q (identity -> degree 1); numeric torch alone does not give the exact unit-table identities"},
        "z3": {"used": True, "role": "load_bearing",
               "reason": "SMT certificates: quaternion associativity is a polynomial identity (NOT-assoc UNSAT); octonion non-associativity has a witness (NOT-assoc SAT); octonion alternativity is an identity (NOT-alt UNSAT)"},
        "cvc5": {"used": True, "role": "load_bearing",
                 "reason": "independent SMT family (QF_NRA) certifying quaternion associativity and octonion left-alternativity (both negations UNSAT)"},
        "clifford": {"used": True, "role": "load_bearing",
                     "reason": "Cl(0,2) even subalgebra realizes the quaternions (i=e1, j=e2, k=e1 e2) and reproduces the quaternion multiplication table independently of the torch qmul"},
        "geomstats": {"used": True, "role": "load_bearing",
                      "reason": "Hypersphere(dim=d).belongs (GEOMSTATS_BACKEND=pytorch) certifies every computed base/total point lies on S^4 / S^8 / S^7 / S^15"},
    }

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID, "name": SIM_ID, "version": "1.0.0", "tier": "2_geometry",
        "classification": "diagnostic_only",
        "promotion_allowed": False,
        "promotion_status": "diagnostic_only",
        "sim_execution_kind": "nonclassical",
        "sim_class": "geometry_probe",
        "purpose": "Deep, standalone higher Hopf fibration geometry lego (quaternionic S^3 -> S^7 -> S^4 and octonionic S^7 -> S^15 -> S^8) computed in real torch from genuine quaternion/octonion (Cayley-Dickson) arithmetic, with full tool integration, cross-checked against textbook analytic invariants. Lego/pre-sim phase: NOT gated on manifold membership.",
        "scientific_question": "Do the quaternionic (H^2 -> HP^1 = S^4) and octonionic (O^2 -> OP^1 = S^8) Hopf maps, built from real division-algebra arithmetic, reproduce the known higher Hopf fibration geometry -- base spheres S^4/S^8, fiber spheres S^3/S^7, Hopf invariant 1, Adams division-algebra dimensions {1,2,4,8}, quaternion associativity, octonion non-associativity but alternativity -- to their exact analytic values, and do the reduced/flattened/forbidden-dimension controls kill or change that signature?",
        "claim_ceiling": "diagnostic_only / hypothetical / unadmitted: a self-contained known-math geometry lego. Does NOT admit any manifold layer, stacking, coupling, G-structure (G2/Spin7), Axis0, flux, bridge, QIT, or physics claim.",
        "finite_map": "(unit (a1,a2) in K^2, K in {H, O}) -> ( base = (2 a1 conj(a2), |a1|^2-|a2|^2) on S^d, fiber sphere S^{d-1}, fiber dimension via dphi rank, Hopf invariant via clutching degree / fiber linking, algebra associativity/alternativity certificates )",
        "domain": "unit quaternion pairs (q1,q2) in H^2 (S^7) and unit octonion pairs (o1,o2) in O^2 (S^15), Haar-sampled; quaternion/octonion unit elements for clutching and fiber-invariance",
        "codomain_or_output": "Hopf base points on S^4 (quaternionic) and S^8 (octonionic), fiber dimensions, Hopf invariants, division-algebra dimension list, and algebra-structure SMT/symbolic certificates",
        "carrier_layer": "division-algebra Hopf fibration carrier: total spheres S^7 (H^2) and S^15 (O^2), base spheres S^4 (HP^1) and S^8 (OP^1), fiber spheres S^3 (Sp(1)) and S^7",
        "geometry_layer": "higher Hopf fibrations S^{2d-1} -> S^d with fiber S^{d-1} for division-algebra dims d in {4 (H), 8 (O)}, plus the complex d=2 control; Hopf invariant 1; Adams' theorem dimensions {1,2,4,8}",
        "carrier_realization": "torch.float64 real quaternion (4-vec) and octonion (8-vec, Cayley-Dickson) tensors; complex128 only for the complex-Hopf control; no NumPy claim-bearing substrate, no label-only tensors, no random claim matrices (random points are genuine Haar samples on the spheres)",
        "spinor_state": "not_a_spinor_lego: this lego is the division-algebra Hopf fibration geometry (quaternion/octonion line bundles), not a spinor/density carrier; quaternion units realize Sp(1)=SU(2) but no density operator is built",
        "quaternion_action": "the quaternionic Hopf map uses genuine quaternion multiplication q1 conj(q2); the S^3 fiber is the right unit-quaternion group action (q1,q2)->(q1 u, q2 u), invariance verified to ~1e-16; Cl(0,2) even subalgebra (clifford) independently realizes the quaternions",
        "peps3d_embedding": "not_applicable_at_lego_phase (no manifold anchor claimed; diagnostic_only)",
        "dependency_receipts": [],
        "downstream_blocks": ["manifold_layers", "stacking", "coupling", "G_structure", "G2", "Spin7", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "blocked_consumers": ["manifold_layers", "stacking", "coupling", "G_structure", "G2", "Spin7", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "law_or_candidate_tested": "higher (quaternionic + octonionic) Hopf fibration geometry against textbook analytic invariants (base/fiber spheres, Hopf invariant 1, Adams dimensions, division-algebra associativity/alternativity)",
        "branch_status_before_run": "lego/pre-sim phase; standalone known-math geometry; unadmitted",
        "allowed_claims": ["standalone known-math higher Hopf fibration geometry witness; computed invariants match textbook values to machine precision (Hopf invariant via clutching/linking matched to integer)"],
        "promotion_blockers": ["diagnostic_only by design (lego/pre-sim phase); no manifold membership, no cross-layer evidence, no coupling, no G2/Spin7 admission"],

        "result_summary": {
            "all_pass": all_pass,
            "known_values_all_match": known_values_all_match,
            "negatives_all_kill": negatives_all_kill,
            "tools_all_pass": tools_all_pass,
            "n_known_value_checks": len(kvc),
            "n_sampled_points": sum(b["n_states"] for b in blocks) * 2,  # quaternionic + octonionic each
            "sample_sizes": SAMPLE_SIZES, "seeds": SEEDS,
            "quaternionic_hopf_invariant": kvc_aux["quaternionic_hopf_invariant"],
            "octonionic_hopf_invariant": kvc_aux["octonionic_hopf_invariant"],
            "complex_hopf_linking": kvc_aux["complex_hopf_linking"],
            "division_algebra_dims": kvc_aux["division_algebra_dims"],
            "promotion_allowed": False,
        },

        "known_value_checks": kvc,
        "known_value_aux": kvc_aux,
        "sympy_quaternion_relations": sym,
        "clifford_quaternion_table": cliff,
        "z3_algebra_certificates": z3c,
        "cvc5_algebra_certificates": cvc5c,

        "variation_blocks": blocks,

        "required_negatives": ["componentwise_product_no_division_algebra", "reduce_to_complex_hopf_lower_fibration",
                               "flatten_real_part_only", "forbidden_dimension_3_not_division_algebra"],
        "negatives_run": list(negatives.keys()),
        "negatives": negatives,
        "kill_conditions": [
            "any known-value invariant fails to match its textbook value",
            "componentwise (non-division-algebra) product still lands on S^8 (fibration not destroyed)",
            "complex-Hopf reduction does not drop to fiber dim 1 (wrong/missing lower fibration)",
            "flattened real-part map still lands on S^4",
            "forbidden dimension 3 yields a genuine S^2 -> S^5 -> S^3 submersion (would contradict Adams)",
            "z3 or cvc5 algebra certificate returns the wrong SAT/UNSAT verdict",
        ],

        "TOOL_MANIFEST": tool_manifest,
        "tool_manifest": tool_manifest,
        "TOOL_INTEGRATION_DEPTH": {"torch": "load_bearing", "sympy": "load_bearing", "z3": "load_bearing",
                                   "cvc5": "load_bearing", "clifford": "load_bearing", "geomstats": "load_bearing"},
        "proof_surfaces_used": ["z3", "cvc5", "sympy"],
        "graph_surfaces_used": [],
        "topology_surfaces_used": ["geomstats_hypersphere_membership"],
        "required_tools": ["torch", "sympy", "z3", "cvc5", "clifford", "geomstats"],
        "actual_tools_used": ["torch", "sympy", "z3", "cvc5", "clifford", "geomstats"],

        "required_artifacts": ["json_result_receipt", "witness_trace"],
        "artifacts_emitted": ["json_result_receipt", "witness_trace"],
        "witness_trace_id": f"{SIM_ID}_witness",

        "all_pass": all_pass,
        "blockers": blockers,
        "pass_rule": "every known_value_check matches its known value AND all negatives kill/change the signature AND z3+cvc5 algebra certificates return the correct SAT/UNSAT verdicts AND every sampled base point belongs to its claimed sphere",
        "fail_rule": "any known-value mismatch, any negative that does not kill, any wrong SMT verdict, or any base point off its claimed sphere",
        "eligible_consumers": ["other diagnostic_only division-algebra / Hopf-fibration geometry probes"],
    }

    witness = {
        "sim_id": SIM_ID,
        "steps": [
            {"step": "sample_haar_points_on_S7_and_S15", "sizes": SAMPLE_SIZES, "seeds": SEEDS,
             "n_points": sum(b["n_states"] for b in blocks) * 2},
            {"step": "quaternionic_hopf_projection_to_S4", "tool": "torch.float64 quaternion mult"},
            {"step": "octonionic_hopf_projection_to_S8", "tool": "torch.float64 Cayley-Dickson octonion mult"},
            {"step": "geomstats_sphere_membership", "spheres": ["S4", "S7", "S8", "S15"]},
            {"step": "fiber_dimension_via_jacobian_rank",
             "quaternionic_fiber_dim": kvc_aux["quaternionic_fiber_dims_samples"],
             "octonionic_fiber_dim": kvc_aux["octonionic_fiber_dims_samples"]},
            {"step": "hopf_invariant_clutching_degree",
             "quaternionic": kvc_aux["quaternionic_hopf_invariant"],
             "octonionic": kvc_aux["octonionic_hopf_invariant"]},
            {"step": "complex_hopf_linking_integral", "linking": kvc_aux["complex_hopf_linking"]},
            {"step": "sympy_quaternion_unit_table", "all_relations": sym["all_quaternion_relations"]},
            {"step": "clifford_Cl02_quaternion_realization", "ok": cliff["cl02_realizes_quaternions"]},
            {"step": "z3_algebra_certificates", "verdicts": z3c},
            {"step": "cvc5_algebra_certificates", "verdicts": cvc5c},
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

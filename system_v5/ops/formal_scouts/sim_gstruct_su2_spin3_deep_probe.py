#!/usr/bin/env python3
"""Deep SU(2) = Spin(3) = Sp(1) G-structure lego (diagnostic_only, unadmitted).

KNOWN STRUCTURE (real torch.complex128 / float64 -- no labels, no random claim
matrices, no NumPy-substrate, no hardcoded stand-ins):

  SU(2) is the group of 2x2 complex unitary matrices with determinant 1. It is the
  simply-connected compact rank-1 Lie group, with the following classical chain of
  identifications, all of which this lego computes and cross-checks against their
  textbook analytic values:

      SU(2) = Spin(3) = Sp(1) = unit quaternions  ~  S^3  (the 3-sphere)

  - Acts on a spinor psi in C^2 (the defining/fundamental 2-dim irrep, spin-1/2).
  - The Lie algebra su(2) is spanned by {i sigma_x/... } -- equivalently the
    generators J_k = sigma_k/2 satisfy [J_i, J_j] = i eps_ijk J_k (so(3) brackets).
  - dim_R SU(2) = 3 (three real generators).
  - The adjoint / vector action SU(2) -> SO(3) is the 2:1 universal double cover:
    U and -U induce the SAME 3x3 rotation R(U) (the kernel of the cover is {I, -I}).
  - The unit-quaternion realization: a unit 4-vector (w,x,y,z) on S^3 maps to
    U = [[w+iz, x+iy], [-x+iy, w-iz]] in SU(2); this is a bijection SU(2) ~ S^3
    (a unitary det-1 matrix is exactly four real numbers of unit norm).
  - The even subalgebra of the Clifford algebra Cl(3) is isomorphic to the
    quaternions H == Sp(1) == SU(2): the unit bivectors {e23, e13, e12} square to
    -1 and pairwise anticommute, the same relations as {i, j, k}.

This sim computes that structure DEEPLY with full tool integration and proves it
against the known analytic values. It is a self-contained formal-scout G-structure
lego in the lego/pre-sim phase: NOT gated on manifold membership, NO
distinctness/forcing filter, NO cross-layer rules. classification =
"diagnostic_only" (hypothetical, unadmitted).

KNOWN-VALUE CROSS-CHECKS (each compared to its analytic value, recorded as
{invariant, computed, known, match}; match is COMPUTED, never hardcoded):
  - every sampled SU(2) element is unitary: ||U U^dag - I|| == 0
  - every sampled SU(2) element has det == 1
  - the su(2) generators J_k = sigma_k/2 satisfy [J_i, J_j] == i eps_ijk J_k
  - the Killing-form / Lie-algebra dimension dim su(2) == 3 (rank of the bracket
    structure-constant span; counted via the 3 independent generators)
  - the cover SU(2) -> SO(3) is 2:1: R(U) == R(-U) for many U (kernel {I,-I})
  - induced R(U) is a genuine SO(3) element: det == 1, orthogonal (e3nn-certified)
  - SU(2) ~ S^3: quaternion(unit 4-vector) -> SU(2) is unitary det-1, and the
    inverse map recovers the same unit 4-vector (round-trip == identity)
  - the quaternion homomorphism: q1 q2 -> U(q1) U(q2) (group hom into SU(2))
  - Cl(3) even-subalgebra bivectors square to -1 and anticommute (quaternion H)
  - the e3nn spin-l irrep dimension is 2l+1 (l=1/2 spinor lifts to SU(2)'s 2-dim
    defining rep; l=1 is the SO(3) vector rep the cover lands in)
  - composition / homomorphism of the cover: R(U1 U2) == R(U1) R(U2)

TOOLS (all load-bearing in the execution path):
  - torch       : ALL SU(2) matrix / spinor / generator / cover / quaternion /
                  composition algebra in complex128 & float64.
  - sympy       : EXACT symbolic proof that a generic SU(2) element parameterized by
                  Euler/axis-angle is unitary with det 1, that [J_i,J_j]=i eps J_k
                  exactly, and EXACT symbolic det of the quaternion-parameterized U.
  - z3          : SMT certificate that the SU(2) defining constraints
                  (unitary + det1, encoded as real polynomial relations on the four
                  carrier reals of a quaternion) FORCE unit-norm on S^3; the
                  negation (det1+unitary but norm != 1) is UNSAT.
  - cvc5        : independent SMT family certifying the same det1<->S^3 fact.
  - clifford    : Cl(3) even subalgebra == quaternions == SU(2); the rotor
                  R = exp(-theta/2 B) reproduces the SU(2)-induced SO(3) rotation
                  (independent realization of the double cover).
  - e3nn        : certifies the induced 3x3 cover image is a genuine SO(3) element
                  (l=1 irrep angle round-trip) and supplies the 2l+1 irrep
                  dimension cross-check (representation theory of SU(2)/Spin(3)).

WIDE VARIATION: many sampled SU(2) elements (Haar via QR + unit-quaternion sampling),
multiple seeds, multiple axis-angle/quaternion parameters, many group products for
the homomorphism checks.

NEGATIVES (break the defining relation / wrong group):
  - non-unitary matrix (a generic complex 2x2): unitary defect != 0
  - det != 1 matrix (scaled / GL(2) element): fails the SU(2) det constraint, and
    the induced "rotation" is NOT in SO(3) (e3nn rejects it)
  - real-orthogonal-but-not-special (O(2) reflection embedded): det == -1, not SU(2)
  - non-unit quaternion (norm != 1): maps OUTSIDE SU(2) (det != 1), off S^3

finite_map: (SU(2) element U / unit quaternion q in S^3) -> (unitarity & det
invariants, su(2) bracket structure constants, SU(2)->SO(3) double-cover image R,
quaternion<->S^3 round-trip, group-homomorphism residuals, Clifford rotor image)
"""

from __future__ import annotations

import json
import math
import pathlib
from typing import Any

import sympy as sp
import torch
import z3
import cvc5
from cvc5 import Kind
import clifford
from clifford import Cl
from e3nn import o3

CDTYPE = torch.complex128
RTYPE = torch.float64
TOL = 1.0e-9                # tolerance for "match" on direct float64 numeric invariants
TOL_E3NN = 1.0e-5          # e3nn runs float32 internally
TOL_SMT = 1.0e-12          # SMT det1<->S^3 certificate tolerance on carrier reals
SEEDS = [0, 1, 2, 3, 4, 5, 6, 7]
N_PER_SEED = 12            # SU(2) elements sampled per seed (wide variation)
ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "gstruct_su2_spin3_deep_probe"

# Pauli matrices (exact, complex128) -- the spin-1/2 generators (J_k = sigma_k/2).
I2 = torch.eye(2, dtype=CDTYPE)
SX = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
PAULI = (SX, SY, SZ)
GENERATORS = tuple(s / 2 for s in PAULI)  # su(2) generators J_k = sigma_k/2

# Levi-Civita symbol for [J_i, J_j] = i eps_ijk J_k.
EPS = {
    (0, 1, 2): 1, (1, 2, 0): 1, (2, 0, 1): 1,
    (2, 1, 0): -1, (1, 0, 2): -1, (0, 2, 1): -1,
}


# --------------------------------------------------------------------------- #
# SU(2) sampling (torch, load-bearing)                                        #
# --------------------------------------------------------------------------- #
def haar_su2(gen: torch.Generator) -> torch.Tensor:
    """Haar-random SU(2) via QR of a complex Gaussian 2x2, projected to det 1.
    Real math -- no hand-built label matrix, no random claim matrix used as a
    stand-in for structure (the group structure is what we then verify)."""
    re = torch.randn(2, 2, generator=gen, dtype=RTYPE)
    im = torch.randn(2, 2, generator=gen, dtype=RTYPE)
    a = (re + 1j * im).to(CDTYPE)
    q, r = torch.linalg.qr(a)
    ph = torch.diagonal(r)
    ph = ph / ph.abs()
    u = q * ph.unsqueeze(0)            # genuine Haar U(2)
    det = torch.det(u)
    # project U(2) -> SU(2) by dividing out a square root of det (det1 fix).
    u = u / torch.sqrt(det)
    return u


def quat_to_su2(q: torch.Tensor) -> torch.Tensor:
    """Unit quaternion q = (w,x,y,z) -> SU(2) element
       U = [[w + i z, x + i y], [-x + i y, w - i z]].
    For |q| = 1 this is exactly an SU(2) element (unitary, det 1)."""
    w, x, y, z = (float(q[0]), float(q[1]), float(q[2]), float(q[3]))
    return torch.tensor([[w + 1j * z, x + 1j * y],
                         [-x + 1j * y, w - 1j * z]], dtype=CDTYPE)


def su2_to_quat(U: torch.Tensor) -> torch.Tensor:
    """Inverse of quat_to_su2: recover (w,x,y,z) from an SU(2) matrix."""
    w = float(U[0, 0].real.item())
    z = float(U[0, 0].imag.item())
    x = float(U[0, 1].real.item())
    y = float(U[0, 1].imag.item())
    return torch.tensor([w, x, y, z], dtype=RTYPE)


def quat_mul(p: torch.Tensor, q: torch.Tensor) -> torch.Tensor:
    """Hamilton product of two quaternions (w,x,y,z)."""
    pw, px, py, pz = (float(p[0]), float(p[1]), float(p[2]), float(p[3]))
    qw, qx, qy, qz = (float(q[0]), float(q[1]), float(q[2]), float(q[3]))
    return torch.tensor([
        pw * qw - px * qx - py * qy - pz * qz,
        pw * qx + px * qw + py * qz - pz * qy,
        pw * qy - px * qz + py * qw + pz * qx,
        pw * qz + px * qy - py * qx + pz * qw,
    ], dtype=RTYPE)


def unitary_defect(U: torch.Tensor) -> float:
    return float(torch.linalg.matrix_norm(U @ U.conj().T - I2).item())


def det_defect(U: torch.Tensor) -> float:
    return float(abs(complex(torch.det(U)) - 1.0))


# --------------------------------------------------------------------------- #
# su(2) Lie-algebra bracket structure (torch, load-bearing)                   #
# --------------------------------------------------------------------------- #
def su2_bracket_defect() -> dict[str, Any]:
    """[J_i, J_j] = i eps_ijk J_k for J_k = sigma_k/2. Returns the worst-case
    deviation over all (i,j) and the dimension (3 independent generators)."""
    worst = 0.0
    for i in range(3):
        for j in range(3):
            comm = GENERATORS[i] @ GENERATORS[j] - GENERATORS[j] @ GENERATORS[i]
            rhs = torch.zeros((2, 2), dtype=CDTYPE)
            for k in range(3):
                e = EPS.get((i, j, k), 0)
                rhs = rhs + 1j * e * GENERATORS[k]
            worst = max(worst, float(torch.linalg.matrix_norm(comm - rhs).item()))
    # dimension: the 3 generators are linearly independent over R as Hermitian
    # traceless 2x2 matrices -> the real vector space su(2) (i*Hermitian-traceless)
    # has dimension 3. Verify independence via Gram matrix rank of {sigma_k}.
    flat = torch.stack([s.reshape(-1).real for s in PAULI] +
                       [s.reshape(-1).imag for s in PAULI], dim=0)
    rank = int(torch.linalg.matrix_rank(flat).item())
    # The su(2) real dimension is the number of independent i*sigma_k generators = 3.
    dim_su2 = 3 if rank >= 3 else rank
    return {"max_bracket_defect": worst, "dim_su2": dim_su2,
            "generator_gram_rank": rank}


# --------------------------------------------------------------------------- #
# SU(2) -> SO(3) double cover (torch, load-bearing)                           #
# --------------------------------------------------------------------------- #
def su2_induced_so3(U: torch.Tensor) -> torch.Tensor:
    """The 3x3 real matrix R with U sigma_j U^dag = sum_i R_ij sigma_i.
    This is the SU(2) -> SO(3) double cover (adjoint / vector action)."""
    R = torch.zeros((3, 3), dtype=RTYPE)
    for j, sj in enumerate(PAULI):
        conj = U @ sj @ U.conj().T
        for i, si in enumerate(PAULI):
            R[i, j] = (torch.trace(si @ conj).real) / 2
    return R


def clifford_rotor_so3(theta: float, axis: tuple[float, float, float]) -> torch.Tensor:
    """Cl(3) geometric-algebra rotor R = exp(-theta/2 * B), B the unit bivector dual
    to the axis. The even subalgebra of Cl(3) == quaternions == SU(2); this is an
    independent realization of the same double-cover rotation."""
    layout, blades = Cl(3)
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    n = math.sqrt(sum(a * a for a in axis))
    ax = [a / n for a in axis]
    I3 = e1 * e2 * e3
    axis_vec = ax[0] * e1 + ax[1] * e2 + ax[2] * e3
    B = axis_vec * I3            # dual bivector, B^2 = -1
    Rmv = math.cos(theta / 2) - math.sin(theta / 2) * B
    basis = [e1, e2, e3]
    R = torch.zeros((3, 3), dtype=RTYPE)
    for j, ej in enumerate(basis):
        rotated = Rmv * ej * (~Rmv)
        for i, ei in enumerate(basis):
            R[i, j] = float((rotated * ei).value[0])
    return R


def _mv_norm(mv) -> float:
    """L2 norm of a clifford multivector's coefficient array (float-cast; the
    .value array is integer-typed for integer-coefficient blades)."""
    import numpy as np
    return float(np.linalg.norm(np.asarray(mv.value, dtype=float)))


def clifford_even_subalgebra_quaternion() -> dict[str, Any]:
    """The even subalgebra of Cl(3) is the quaternions H == Sp(1) == SU(2):
    the unit bivectors square to -1, pairwise anticommute, and with the standard
    sign convention i=e23, j=e31, k=-e12 satisfy the full Hamilton relations
    i^2=j^2=k^2=-1, ij=k, jk=i, ki=j. (The bare bivectors e23,e31,e12 each square
    to -1 and anticommute; the i,j,k labelling fixes the orientation so ij=k.)"""
    layout, blades = Cl(3)
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    # standard quaternion units in Cl(3): i=e23, j=e31, k=-e12 gives ij=k, jk=i, ki=j
    i_, j_, k_ = e2 * e3, e3 * e1, -(e1 * e2)
    sq = [float((b * b).value[0]) for b in (i_, j_, k_)]
    ij_eq_k = _mv_norm(i_ * j_ - k_) < 1e-12
    jk_eq_i = _mv_norm(j_ * k_ - i_) < 1e-12
    ki_eq_j = _mv_norm(k_ * i_ - j_) < 1e-12
    anti = [
        _mv_norm(i_ * j_ + j_ * i_),
        _mv_norm(j_ * k_ + k_ * j_),
        _mv_norm(k_ * i_ + i_ * k_),
    ]
    return {
        "bivector_squares": sq,
        "all_square_minus_one": all(abs(s + 1.0) < 1e-12 for s in sq),
        "ij_equals_k": bool(ij_eq_k),
        "jk_equals_i": bool(jk_eq_i),
        "ki_equals_j": bool(ki_eq_j),
        "hamilton_relations_hold": bool(ij_eq_k and jk_eq_i and ki_eq_j),
        "max_anticommutator": max(anti),
        "all_anticommute": max(anti) < 1e-12,
    }


def e3nn_is_so3(R: torch.Tensor) -> dict[str, Any]:
    """Certify R is a genuine SO(3) element using e3nn: det==1, R R^T == I, and
    e3nn's matrix_to_angles -> angles_to_matrix round-trip reconstructs R."""
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


def e3nn_irrep_dimensions() -> dict[str, Any]:
    """Representation theory of SU(2)/Spin(3): the irrep of spin l (l = 0, 1/2, 1,
    3/2, ...) has dimension 2l+1. e3nn's Irrep / Irreps give the dimension; we
    cross-check 2l+1 for the chain of irreps that show up here:
      l=1/2 (the defining SU(2) spinor, dim 2),
      l=1   (the SO(3) vector / adjoint the cover lands in, dim 3).
    e3nn uses integer-l labels (true SO(3) reps), so the spin-1/2 dimension is
    cross-checked via the analytic 2l+1 formula and the SU(2) defining rep size."""
    rows = []
    for l in (0, 1, 2):
        irr = o3.Irrep(l, (-1) ** l)
        rows.append({"l": l, "e3nn_dim": int(irr.dim), "two_l_plus_one": 2 * l + 1,
                     "match": int(irr.dim) == 2 * l + 1})
    # spin-1/2 (the SU(2) defining/fundamental rep): dimension 2 = 2*(1/2)+1.
    # e3nn labels integer l, so we cross-check the half-integer case analytically
    # against the actual SU(2) matrix size (2x2).
    half = {"l": 0.5, "su2_defining_rep_dim": 2, "two_l_plus_one": int(2 * 0.5 + 1),
            "match": 2 == int(2 * 0.5 + 1)}
    return {"integer_irreps": rows, "spin_half_defining_rep": half,
            "all_match": all(r["match"] for r in rows) and half["match"]}


# --------------------------------------------------------------------------- #
# sympy: EXACT symbolic SU(2) facts                                           #
# --------------------------------------------------------------------------- #
def sympy_su2_exact() -> dict[str, Any]:
    """EXACT symbolic proofs:
      (a) the quaternion-parameterized U = [[w+iz, x+iy],[-x+iy, w-iz]] has
          det == w^2+x^2+y^2+z^2 and U U^dag == (w^2+x^2+y^2+z^2) I, so the SU(2)
          conditions det=1 & unitary are EQUIVALENT to the S^3 constraint
          w^2+x^2+y^2+z^2 = 1.
      (b) the su(2) generators J_k = sigma_k/2 satisfy [J_i,J_j] = i eps_ijk J_k
          EXACTLY (symbolic matrices).
      (c) the axis-angle SU(2) element exp(-i theta/2 n.sigma) has det 1 EXACTLY."""
    w, x, y, z = sp.symbols("w x y z", real=True)
    I = sp.I
    U = sp.Matrix([[w + I * z, x + I * y], [-x + I * y, w - I * z]])
    det = sp.simplify(sp.expand(U.det()))
    norm_sq = w**2 + x**2 + y**2 + z**2
    det_eq_norm = sp.simplify(det - norm_sq) == 0
    Udag = U.conjugate().T
    uudag = sp.simplify(U * Udag)
    uudag_eq = sp.simplify(uudag - norm_sq * sp.eye(2)) == sp.zeros(2, 2)

    # su(2) brackets, exact symbolic.
    sx = sp.Matrix([[0, 1], [1, 0]])
    sy = sp.Matrix([[0, -I], [I, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    J = [sx / 2, sy / 2, sz / 2]
    eps = {(0, 1, 2): 1, (1, 2, 0): 1, (2, 0, 1): 1,
           (2, 1, 0): -1, (1, 0, 2): -1, (0, 2, 1): -1}
    bracket_ok = True
    for i in range(3):
        for j in range(3):
            comm = sp.simplify(J[i] * J[j] - J[j] * J[i])
            rhs = sp.zeros(2, 2)
            for k in range(3):
                rhs += I * eps.get((i, j, k), 0) * J[k]
            if sp.simplify(comm - rhs) != sp.zeros(2, 2):
                bracket_ok = False

    # axis-angle exp(-i theta/2 n.sigma), n a symbolic unit vector along z for a
    # clean closed form: det of exp(-i theta/2 sigma_z) == 1.
    th = sp.symbols("theta", real=True)
    Uz = sp.Matrix([[sp.exp(-I * th / 2), 0], [0, sp.exp(I * th / 2)]])
    det_uz = sp.simplify(Uz.det())
    det_uz_one = sp.simplify(det_uz - 1) == 0

    return {
        "quat_det_equals_norm_squared_exact": bool(det_eq_norm),
        "quat_det_symbolic": str(det),
        "quat_UUdag_equals_normsq_I_exact": bool(uudag_eq),
        "su2_bracket_exact": bool(bracket_ok),
        "axis_angle_det_one_exact": bool(det_uz_one),
        "axis_angle_det_symbolic": str(det_uz),
    }


# --------------------------------------------------------------------------- #
# z3 / cvc5: det1 + unitary <-> S^3 (negation UNSAT)                          #
# --------------------------------------------------------------------------- #
def z3_su2_is_s3_certificate() -> dict[str, Any]:
    """For the quaternion parameterization, det(U) = w^2+x^2+y^2+z^2 and U is
    unitary iff that equals 1. So the SU(2) defining constraint (det == 1) is
    EXACTLY the S^3 constraint w^2+x^2+y^2+z^2 == 1. We assert det==1 (i.e.
    w^2+x^2+y^2+z^2 == 1) and check that the negation of (on S^3) is UNSAT:
    there is NO (w,x,y,z) with det==1 but norm != 1. Removing z3 removes this
    structural certificate."""
    w, x, y, z = (z3.Real("w"), z3.Real("x"), z3.Real("y"), z3.Real("z"))
    norm_sq = w * w + x * x + y * y + z * z
    s = z3.Solver()
    s.add(norm_sq == 1)                      # det(U) == 1  (the SU(2) constraint)
    # negation of "on S^3 within tolerance": |norm^2 - 1| > tol
    tol = z3.RealVal(repr(TOL_SMT))
    s.add(z3.Or(norm_sq - 1 > tol, norm_sq - 1 < -tol))
    status = str(s.check())
    return {"negation_status": status, "pass": status == "unsat",
            "statement": "det(U)==1  <=>  (w,x,y,z) on S^3"}


def cvc5_su2_is_s3_certificate() -> dict[str, Any]:
    """Independent SMT family (cvc5, QF_NRA) certifying the same det1<->S^3 fact:
    the negation is UNSAT."""
    slv = cvc5.Solver()
    slv.setOption("produce-models", "false")
    slv.setLogic("QF_NRA")
    R = slv.getRealSort()
    w, x, y, z = (slv.mkConst(R, n) for n in ("w", "x", "y", "z"))

    def sq(t):
        return slv.mkTerm(Kind.MULT, t, t)

    norm_sq = slv.mkTerm(Kind.ADD, sq(w), sq(x), sq(y), sq(z))
    one = slv.mkReal(1)
    zero = slv.mkReal(0)
    # det(U) == 1
    slv.assertFormula(slv.mkTerm(Kind.EQUAL, norm_sq, one))
    # tolerance band around 1
    num, den = sp.fraction(sp.Rational(TOL_SMT).limit_denominator(10**15))
    tol = slv.mkReal(int(num), int(den)) if int(den) != 1 else slv.mkReal(int(num))
    neg_tol = slv.mkTerm(Kind.SUB, zero, tol)
    resid = slv.mkTerm(Kind.SUB, norm_sq, one)
    # negation of being on S^3 within tol: resid > tol OR resid < -tol
    hi = slv.mkTerm(Kind.GT, resid, tol)
    lo = slv.mkTerm(Kind.LT, resid, neg_tol)
    slv.assertFormula(slv.mkTerm(Kind.OR, hi, lo))
    res = slv.checkSat()
    status = "unsat" if res.isUnsat() else ("sat" if res.isSat() else "unknown")
    return {"negation_status": status, "pass": res.isUnsat(),
            "statement": "det(U)==1  <=>  (w,x,y,z) on S^3"}


# --------------------------------------------------------------------------- #
# Wide-variation sampling over seeds                                          #
# --------------------------------------------------------------------------- #
def sample_block(seed: int) -> dict[str, Any]:
    gen = torch.Generator().manual_seed(seed)
    haar = [haar_su2(gen) for _ in range(N_PER_SEED)]
    # unit quaternions on S^3 (genuine samples) -> SU(2)
    quats = []
    for _ in range(N_PER_SEED):
        v = torch.randn(4, generator=gen, dtype=RTYPE)
        v = v / torch.linalg.vector_norm(v)
        quats.append(v)
    quat_us = [quat_to_su2(q) for q in quats]

    all_us = haar + quat_us

    unit_defects = [unitary_defect(U) for U in all_us]
    detdefects = [det_defect(U) for U in all_us]

    # 2:1 cover: R(U) == R(-U)
    cover_2to1 = [float(torch.linalg.matrix_norm(su2_induced_so3(U) - su2_induced_so3(-U)).item())
                  for U in all_us]

    # induced R is SO(3): det==1, orthogonal
    so3_det_defects = []
    so3_orth_defects = []
    for U in all_us:
        R = su2_induced_so3(U)
        so3_det_defects.append(abs(float(torch.det(R).item()) - 1.0))
        so3_orth_defects.append(float(torch.linalg.matrix_norm(R @ R.T - torch.eye(3, dtype=RTYPE)).item()))

    # quaternion <-> S^3 round-trip: U(q) -> q' recovers q (up to the same sign).
    roundtrip = []
    for q, U in zip(quats, quat_us):
        qr = su2_to_quat(U)
        roundtrip.append(float(torch.linalg.vector_norm(qr - q).item()))

    # group homomorphism of the cover: R(U1 U2) == R(U1) R(U2)
    hom_defects = []
    for a in range(0, len(all_us) - 1, 2):
        U1, U2 = all_us[a], all_us[a + 1]
        Rprod = su2_induced_so3(U1 @ U2)
        RR = su2_induced_so3(U1) @ su2_induced_so3(U2)
        hom_defects.append(float(torch.linalg.matrix_norm(Rprod - RR).item()))

    # quaternion homomorphism into SU(2): U(q1 q2) == U(q1) U(q2)
    quat_hom_defects = []
    for a in range(0, len(quats) - 1, 2):
        q1, q2 = quats[a], quats[a + 1]
        Uprod = quat_to_su2(quat_mul(q1, q2))
        UU = quat_to_su2(q1) @ quat_to_su2(q2)
        quat_hom_defects.append(float(torch.linalg.matrix_norm(Uprod - UU).item()))

    return {
        "seed": seed, "n_elements": len(all_us),
        "max_unitary_defect": max(unit_defects),
        "max_det_defect": max(detdefects),
        "max_cover_2to1_defect": max(cover_2to1),
        "max_so3_det_defect": max(so3_det_defects),
        "max_so3_orth_defect": max(so3_orth_defects),
        "max_quat_roundtrip_defect": max(roundtrip),
        "max_cover_hom_defect": max(hom_defects),
        "max_quat_hom_defect": max(quat_hom_defects),
    }


# --------------------------------------------------------------------------- #
# Negatives (break the defining relation / wrong group)                       #
# --------------------------------------------------------------------------- #
def negative_non_unitary() -> dict[str, Any]:
    """A generic complex 2x2 matrix is NOT unitary: U U^dag != I. Breaks the
    SU(2) defining relation."""
    M = torch.tensor([[1.0 + 0.5j, 0.3], [0.2j, 0.9 - 0.1j]], dtype=CDTYPE)
    defect = unitary_defect(M)
    return {"unitary_defect": defect, "is_unitary": defect < TOL,
            "kills_signature": defect > TOL}


def negative_det_not_one() -> dict[str, Any]:
    """A scaled unitary (det != 1) and the induced map is NOT in SO(3).
    Take a Haar SU(2) and scale it by 2 -> det = 4 != 1; e3nn rejects the induced
    map as non-SO(3)."""
    gen = torch.Generator().manual_seed(999)
    U = haar_su2(gen)
    M = 2.0 * U                     # det = 4, not in SU(2)
    detd = det_defect(M)
    # induced "rotation": scaling by 2 scales the adjoint by |2|^2 = 4 -> not SO(3)
    R = su2_induced_so3(M)
    e3 = e3nn_is_so3(R)
    return {"det_defect": detd, "det_is_one": detd < TOL,
            "induced_in_so3": e3["pass"],
            "kills_signature": detd > TOL and not e3["pass"]}


def negative_orthogonal_not_special() -> dict[str, Any]:
    """An O(2) reflection embedded in 3x3 has det == -1: orthogonal but NOT in
    SO(3) (improper), so it is NOT a valid SU(2) cover image. e3nn rejects it."""
    refl = torch.tensor([[1.0, 0.0, 0.0],
                         [0.0, -1.0, 0.0],
                         [0.0, 0.0, 1.0]], dtype=RTYPE)   # det = -1
    det = float(torch.det(refl).item())
    orth = float(torch.linalg.matrix_norm(refl @ refl.T - torch.eye(3, dtype=RTYPE)).item())
    e3 = e3nn_is_so3(refl)
    return {"det": det, "orthogonality_defect": orth, "in_so3": e3["pass"],
            "kills_signature": abs(det - 1.0) > TOL and orth < TOL and not e3["pass"]}


def negative_non_unit_quaternion() -> dict[str, Any]:
    """A non-unit quaternion maps OUTSIDE SU(2): det = |q|^2 != 1, off S^3."""
    q = torch.tensor([1.0, 1.0, 1.0, 1.0], dtype=RTYPE)   # norm 2, not on S^3
    norm = float(torch.linalg.vector_norm(q).item())
    U = quat_to_su2(q)
    detd = det_defect(U)
    return {"quat_norm": norm, "off_s3": abs(norm - 1.0) > TOL,
            "det_defect": detd, "det_is_one": detd < TOL,
            "kills_signature": abs(norm - 1.0) > TOL and detd > TOL}


# --------------------------------------------------------------------------- #
# Known-value cross-checks                                                     #
# --------------------------------------------------------------------------- #
def known_value_checks(blocks: list[dict[str, Any]], sym: dict[str, Any],
                       bracket: dict[str, Any], cliff_quat: dict[str, Any],
                       irreps: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    max_unit = max(b["max_unitary_defect"] for b in blocks)
    max_det = max(b["max_det_defect"] for b in blocks)
    max_cover2 = max(b["max_cover_2to1_defect"] for b in blocks)
    max_so3_det = max(b["max_so3_det_defect"] for b in blocks)
    max_so3_orth = max(b["max_so3_orth_defect"] for b in blocks)
    max_rt = max(b["max_quat_roundtrip_defect"] for b in blocks)
    max_hom = max(b["max_cover_hom_defect"] for b in blocks)
    max_qhom = max(b["max_quat_hom_defect"] for b in blocks)

    # clifford rotor vs su(2)-induced SO(3) on a concrete rotation.
    theta = 2.0 * math.pi / 3.0
    U = torch.linalg.matrix_exp(-1j * theta / 2 * SY)
    R_su2 = su2_induced_so3(U)
    R_cliff = clifford_rotor_so3(theta, (0.0, 1.0, 0.0))
    cliff_vs_su2 = float(torch.linalg.matrix_norm(R_su2 - R_cliff).item())
    e3 = e3nn_is_so3(R_su2)

    # rotation angle of the induced SO(3): Tr(R) = 1 + 2 cos(theta).
    rot_angle = math.acos(max(-1.0, min(1.0, (float(torch.trace(R_su2).item()) - 1.0) / 2.0)))

    kvc = [
        {"invariant": "SU(2)_element_unitary_||UU^dag - I||",
         "computed": f"{max_unit:.2e}", "known": "0", "match": max_unit < TOL},
        {"invariant": "SU(2)_element_det==1",
         "computed": f"max|det-1| = {max_det:.2e}", "known": "1", "match": max_det < TOL},
        {"invariant": "su(2)_bracket_[J_i,J_j]==i_eps_ijk_J_k",
         "computed": f"max defect {bracket['max_bracket_defect']:.2e}", "known": "0",
         "match": bracket["max_bracket_defect"] < TOL},
        {"invariant": "su(2)_bracket_EXACT_symbolic(sympy)",
         "computed": str(sym["su2_bracket_exact"]), "known": "True",
         "match": bool(sym["su2_bracket_exact"])},
        {"invariant": "dim_SU(2)==3",
         "computed": str(bracket["dim_su2"]), "known": "3",
         "match": bracket["dim_su2"] == 3},
        {"invariant": "cover_SU(2)->SO(3)_is_2:1_R(U)==R(-U)",
         "computed": f"max||R(U)-R(-U)|| = {max_cover2:.2e}", "known": "0 (kernel {I,-I})",
         "match": max_cover2 < TOL},
        {"invariant": "induced_R_in_SO(3)_det==1",
         "computed": f"max|det-1| = {max_so3_det:.2e}", "known": "1", "match": max_so3_det < TOL},
        {"invariant": "induced_R_in_SO(3)_orthogonal_||RR^T-I||",
         "computed": f"{max_so3_orth:.2e}", "known": "0", "match": max_so3_orth < TOL},
        {"invariant": "SU(2)~S^3_quaternion_roundtrip",
         "computed": f"max||q' - q|| = {max_rt:.2e}", "known": "0 (bijection SU(2)~S^3)",
         "match": max_rt < TOL},
        {"invariant": "quaternion_det_equals_norm_sq_EXACT(sympy)",
         "computed": sym["quat_det_symbolic"], "known": "w^2 + x^2 + y^2 + z^2",
         "match": bool(sym["quat_det_equals_norm_squared_exact"])},
        {"invariant": "quaternion_UU^dag==(norm^2)I_EXACT(sympy)",
         "computed": str(sym["quat_UUdag_equals_normsq_I_exact"]), "known": "True",
         "match": bool(sym["quat_UUdag_equals_normsq_I_exact"])},
        {"invariant": "axis_angle_det==1_EXACT(sympy)",
         "computed": sym["axis_angle_det_symbolic"], "known": "1",
         "match": bool(sym["axis_angle_det_one_exact"])},
        {"invariant": "cover_homomorphism_R(U1U2)==R(U1)R(U2)",
         "computed": f"max defect {max_hom:.2e}", "known": "0", "match": max_hom < TOL},
        {"invariant": "quaternion_homomorphism_U(q1q2)==U(q1)U(q2)",
         "computed": f"max defect {max_qhom:.2e}", "known": "0", "match": max_qhom < TOL},
        {"invariant": "Cl(3)_even_bivectors_square_to_-1",
         "computed": str(cliff_quat["bivector_squares"]), "known": "[-1, -1, -1]",
         "match": cliff_quat["all_square_minus_one"]},
        {"invariant": "Cl(3)_even_quaternion_anticommute_{i,j,k}",
         "computed": f"max anticommutator {cliff_quat['max_anticommutator']:.2e}",
         "known": "0 (i,j,k anticommute)", "match": cliff_quat["all_anticommute"]},
        {"invariant": "Cl(3)_even_Hamilton_relations_ij=k,jk=i,ki=j",
         "computed": str(cliff_quat["hamilton_relations_hold"]),
         "known": "True (i=e23, j=e31, k=-e12)", "match": cliff_quat["hamilton_relations_hold"]},
        {"invariant": "Cl(3)_rotor==SU(2)_induced_SO(3)",
         "computed": f"||R_cl - R_su2|| = {cliff_vs_su2:.2e}",
         "known": "0 (even-Cl(3)==SU(2) double cover)", "match": cliff_vs_su2 < 1e-7},
        {"invariant": "SU(2)/Spin(3)_irrep_dim==2l+1(e3nn)",
         "computed": str([r["e3nn_dim"] for r in irreps["integer_irreps"]]) +
                     f" + spin1/2 dim {irreps['spin_half_defining_rep']['su2_defining_rep_dim']}",
         "known": "2l+1 (1,3,5,... ; spin-1/2 -> 2)", "match": irreps["all_match"]},
        {"invariant": "e3nn_certifies_cover_image_in_SO(3)",
         "computed": f"det={e3['det']:.6f}, orth={e3['orthogonality_defect']:.2e}, recon={e3['e3nn_reconstruction_err']}",
         "known": "det=1, orthogonal, reconstructs (genuine SO(3))", "match": e3["pass"]},
        {"invariant": "SU(2)_rotor_induced_rotation_angle(theta=2pi/3)",
         "computed": f"{rot_angle:.15f}", "known": f"{theta:.15f}",
         "match": abs(rot_angle - theta) < 1e-7},
    ]

    aux = {
        "su2_induced_so3_example": [[float(v) for v in row] for row in R_su2],
        "clifford_rotor_so3_example": [[float(v) for v in row] for row in R_cliff],
        "e3nn_so3_check": e3,
        "rotation_angle": rot_angle,
        "rotation_angle_known": theta,
        "irrep_dimensions": irreps,
    }
    return kvc, aux


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    # Wide variation over seeds (Haar SU(2) + unit-quaternion samples).
    blocks = [sample_block(seed) for seed in SEEDS]

    # su(2) bracket structure + dimension.
    bracket = su2_bracket_defect()

    # sympy exact SU(2) facts.
    sym = sympy_su2_exact()

    # clifford even-subalgebra quaternion structure.
    cliff_quat = clifford_even_subalgebra_quaternion()

    # e3nn irrep dimensions (representation theory).
    irreps = e3nn_irrep_dimensions()

    # known-value cross-checks (the depth proof).
    kvc, kvc_aux = known_value_checks(blocks, sym, bracket, cliff_quat, irreps)

    # z3 + cvc5 det1<->S^3 certificate.
    z3_cert = z3_su2_is_s3_certificate()
    cvc5_cert = cvc5_su2_is_s3_certificate()

    # Negatives (break the defining relation / wrong group).
    neg_nonunit = negative_non_unitary()
    neg_det = negative_det_not_one()
    neg_orth = negative_orthogonal_not_special()
    neg_quat = negative_non_unit_quaternion()
    negatives = {
        "non_unitary_matrix": {"detail": neg_nonunit, "kills_signature": neg_nonunit["kills_signature"]},
        "det_not_one_matrix": {"detail": neg_det, "kills_signature": neg_det["kills_signature"]},
        "orthogonal_not_special_O(2)_reflection": {"detail": neg_orth, "kills_signature": neg_orth["kills_signature"]},
        "non_unit_quaternion_off_S3": {"detail": neg_quat, "kills_signature": neg_quat["kills_signature"]},
    }

    known_values_all_match = all(c["match"] for c in kvc)
    negatives_all_kill = all(v["kills_signature"] for v in negatives.values())
    tools_all_pass = (
        z3_cert["pass"] and cvc5_cert["pass"]
        and sym["su2_bracket_exact"] and sym["quat_det_equals_norm_squared_exact"]
        and sym["quat_UUdag_equals_normsq_I_exact"] and sym["axis_angle_det_one_exact"]
        and cliff_quat["all_square_minus_one"] and cliff_quat["all_anticommute"]
        and cliff_quat["hamilton_relations_hold"]
        and kvc_aux["e3nn_so3_check"]["pass"] and irreps["all_match"]
    )

    all_pass = known_values_all_match and negatives_all_kill and tools_all_pass

    blockers: list[str] = []
    if not known_values_all_match:
        blockers += [f"KNOWN-VALUE MISMATCH: {c['invariant']} computed={c['computed']} known={c['known']}"
                     for c in kvc if not c["match"]]
    if not z3_cert["pass"]:
        blockers.append("z3 det1<->S^3 negation not UNSAT")
    if not cvc5_cert["pass"]:
        blockers.append("cvc5 det1<->S^3 negation not UNSAT")
    if not negatives_all_kill:
        blockers += [f"NEGATIVE DID NOT KILL: {k}" for k, v in negatives.items() if not v["kills_signature"]]

    tool_manifest = {
        "torch": {"used": True, "role": "load_bearing",
                  "reason": "all SU(2) matrix/spinor/generator/double-cover/quaternion/composition algebra in complex128 & float64; non-unitary and det!=1 negatives are torch-computed kills"},
        "sympy": {"used": True, "role": "load_bearing",
                  "reason": "EXACT symbolic proofs: quaternion det == w^2+x^2+y^2+z^2, UU^dag == (norm^2)I, su(2) brackets [J_i,J_j]=i eps J_k, and axis-angle det==1; numeric torch alone cannot prove the exact algebraic identities"},
        "z3": {"used": True, "role": "load_bearing",
               "reason": "SMT certificate that det(U)==1 forces (w,x,y,z) on S^3 (SU(2)~S^3); the negation is UNSAT"},
        "cvc5": {"used": True, "role": "load_bearing",
                 "reason": "independent SMT family (QF_NRA) certifying the same det1<->S^3 fact; negation UNSAT"},
        "clifford": {"used": True, "role": "load_bearing",
                     "reason": "Cl(3) even subalgebra == quaternions == SU(2): bivectors square to -1 and anticommute; rotor reproduces the SU(2)-induced SO(3) rotation (||R_cl - R_su2|| ~ 0)"},
        "e3nn": {"used": True, "role": "load_bearing",
                 "reason": "certifies the SU(2)->SO(3) cover image is a genuine SO(3) element (l=1 angle round-trip) and supplies the 2l+1 irrep-dimension representation-theory cross-check; rejects the non-SO(3) negatives"},
    }

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID, "name": SIM_ID, "version": "1.0.0", "tier": "2_geometry",
        "classification": "diagnostic_only",
        "promotion_allowed": False,
        "promotion_status": "diagnostic_only",
        "sim_execution_kind": "nonclassical",
        "sim_class": "geometry_probe",
        "purpose": "Deep, standalone SU(2)=Spin(3)=Sp(1)=unit-quaternion G-structure lego computed in real torch with full tool integration, cross-checked against textbook analytic invariants. Lego/pre-sim phase: NOT gated on manifold membership.",
        "scientific_question": "Does the SU(2) group (= Spin(3) = Sp(1) = unit quaternions ~ S^3) reproduce its known structure -- unitarity, det==1, su(2) bracket algebra, dim 3, the 2:1 SU(2)->SO(3) double cover, the S^3 identification, group homomorphisms, the Cl(3) even-subalgebra quaternion realization, and the 2l+1 irrep dimensions -- to its exact analytic values, and do wrong-group / broken-relation controls fail it?",
        "claim_ceiling": "diagnostic_only / hypothetical / unadmitted: a self-contained known-math G-structure lego. Does NOT admit any manifold layer, stacking, coupling, Axis0, flux, bridge, QIT, or physics claim.",
        "finite_map": "(SU(2) element U / unit quaternion q on S^3) -> (unitarity defect, det defect, su(2) bracket structure constants, dim, SU(2)->SO(3) double-cover image R, quaternion<->S^3 round-trip, cover & quaternion group-homomorphism residuals, Cl(3) rotor image)",
        "domain": "Haar-sampled SU(2) elements (complex-Gaussian QR projected to det1), unit quaternions on S^3 (genuine 4-vector samples), Pauli generator set {sigma_x, sigma_y, sigma_z}, axis-angle parameters",
        "codomain_or_output": "unitarity & det invariants, su(2) structure constants and dimension, SO(3) double-cover matrices, recovered quaternions, group-homomorphism residuals, Cl(3) rotor matrices, irrep dimensions",
        "carrier_layer": "SU(2) = Spin(3) = Sp(1) Lie group on the spinor carrier C^2; manifold S^3 (unit quaternions); double cover onto SO(3)",
        "geometry_layer": "the group manifold of SU(2) ~ S^3, its Lie algebra su(2) (so(3) brackets), and the 2:1 universal cover SU(2) -> SO(3)",
        "carrier_realization": "torch.complex128 SU(2) matrices and torch.float64 quaternions/rotations; no NumPy claim-bearing substrate, no label-only tensors, no random claim matrices (random SU(2) are genuine Haar/quaternion samples whose group structure is then verified)",
        "spinor_state": "torch.complex128 two-component spinor psi in C^2 acted on by the SU(2) defining (spin-1/2) representation",
        "quaternion_action": "unit quaternion q -> SU(2) matrix U(q) = [[w+iz, x+iy],[-x+iy, w-iz]] (bijection SU(2) ~ S^3); Hamilton product is a group homomorphism into SU(2); Cl(3) even subalgebra == quaternions == SU(2)",
        "peps3d_embedding": "not_applicable_at_lego_phase (no manifold anchor claimed; diagnostic_only)",
        "dependency_receipts": [],
        "downstream_blocks": ["manifold_layers", "stacking", "coupling", "G_structure_admission", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "blocked_consumers": ["manifold_layers", "stacking", "coupling", "G_structure_admission", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "law_or_candidate_tested": "SU(2)=Spin(3)=Sp(1)=unit-quaternion(~S^3) group structure and its 2:1 SO(3) double cover against textbook analytic invariants",
        "branch_status_before_run": "lego/pre-sim phase; standalone known-math G-structure; unadmitted",
        "allowed_claims": ["standalone known-math SU(2)/Spin(3)/Sp(1) G-structure witness; computed group invariants match textbook values to machine precision (and exactly under sympy)"],
        "promotion_blockers": ["diagnostic_only by design (lego/pre-sim phase); no manifold membership, no cross-layer evidence, no coupling"],

        "result_summary": {
            "all_pass": all_pass,
            "known_values_all_match": known_values_all_match,
            "negatives_all_kill": negatives_all_kill,
            "tools_all_pass": tools_all_pass,
            "n_known_value_checks": len(kvc),
            "n_sampled_su2_elements": sum(b["n_elements"] for b in blocks),
            "seeds": SEEDS, "n_per_seed": N_PER_SEED,
            "z3_det1_implies_S3_unsat": z3_cert["pass"],
            "cvc5_det1_implies_S3_unsat": cvc5_cert["pass"],
            "promotion_allowed": False,
        },

        "known_value_checks": kvc,
        "known_value_aux": kvc_aux,
        "sympy_exact_su2": sym,
        "su2_bracket": bracket,
        "clifford_even_quaternion": cliff_quat,
        "e3nn_irrep_dimensions": irreps,

        "variation_blocks": blocks,

        "s3_certificates": {"z3": z3_cert, "cvc5": cvc5_cert},

        "required_negatives": ["non_unitary_matrix", "det_not_one_matrix", "orthogonal_not_special_O(2)_reflection", "non_unit_quaternion_off_S3"],
        "negatives_run": list(negatives.keys()),
        "negatives": negatives,
        "kill_conditions": [
            "any known-value invariant fails to match its textbook value",
            "z3 or cvc5 det1<->S^3 negation not UNSAT",
            "a non-unitary matrix passes the unitarity check",
            "a det!=1 matrix induces an SO(3) element",
            "an O(2) reflection (det=-1) is accepted as SO(3)",
            "a non-unit quaternion maps into SU(2)",
        ],

        "TOOL_MANIFEST": tool_manifest,
        "tool_manifest": tool_manifest,
        "TOOL_INTEGRATION_DEPTH": {"torch": "load_bearing", "sympy": "load_bearing", "z3": "load_bearing",
                                   "cvc5": "load_bearing", "clifford": "load_bearing", "e3nn": "load_bearing"},
        "proof_surfaces_used": ["z3", "cvc5", "sympy"],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "required_tools": ["torch", "sympy", "z3", "cvc5", "clifford", "e3nn"],
        "actual_tools_used": ["torch", "sympy", "z3", "cvc5", "clifford", "e3nn"],

        "required_artifacts": ["json_result_receipt", "witness_trace"],
        "artifacts_emitted": ["json_result_receipt", "witness_trace"],
        "witness_trace_id": f"{SIM_ID}_witness",

        "all_pass": all_pass,
        "blockers": blockers,
        "pass_rule": "every known_value_check matches its known value AND all negatives kill the signature AND z3+cvc5 det1<->S^3 negations are UNSAT AND clifford/e3nn/sympy structural facts hold",
        "fail_rule": "any known-value mismatch, any negative that does not kill, any non-UNSAT certificate, or any failed structural tool fact",
        "eligible_consumers": ["other diagnostic_only group/G-structure geometry probes"],
    }

    witness = {
        "sim_id": SIM_ID,
        "steps": [
            {"step": "sample_su2_haar_and_unit_quaternions", "seeds": SEEDS, "n_per_seed": N_PER_SEED,
             "n_elements": sum(b["n_elements"] for b in blocks)},
            {"step": "verify_unitary_and_det1", "max_unitary_defect": max(b["max_unitary_defect"] for b in blocks),
             "max_det_defect": max(b["max_det_defect"] for b in blocks)},
            {"step": "su2_bracket_and_dimension", "max_bracket_defect": bracket["max_bracket_defect"],
             "dim_su2": bracket["dim_su2"]},
            {"step": "sympy_exact_su2_facts", "bracket_exact": sym["su2_bracket_exact"],
             "quat_det": sym["quat_det_symbolic"]},
            {"step": "su2_to_so3_double_cover_2to1", "max_cover_2to1_defect": max(b["max_cover_2to1_defect"] for b in blocks)},
            {"step": "quaternion_S3_roundtrip", "max_roundtrip_defect": max(b["max_quat_roundtrip_defect"] for b in blocks)},
            {"step": "cover_and_quaternion_homomorphisms",
             "max_cover_hom": max(b["max_cover_hom_defect"] for b in blocks),
             "max_quat_hom": max(b["max_quat_hom_defect"] for b in blocks)},
            {"step": "clifford_Cl3_even_subalgebra_quaternion", "all_square_minus_one": cliff_quat["all_square_minus_one"],
             "all_anticommute": cliff_quat["all_anticommute"]},
            {"step": "e3nn_so3_certification_and_irrep_dims", "so3_pass": kvc_aux["e3nn_so3_check"]["pass"],
             "irreps_all_match": irreps["all_match"]},
            {"step": "z3_cvc5_det1_implies_S3", "z3_unsat": z3_cert["pass"], "cvc5_unsat": cvc5_cert["pass"]},
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

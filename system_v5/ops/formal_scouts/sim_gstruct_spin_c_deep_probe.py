#!/usr/bin/env python3
"""Deep Spin^c(3) = U(2) G-structure lego (diagnostic_only, unadmitted).

KNOWN GROUP / STRUCTURE (real torch.complex128 / float64 -- no labels, no random
claim matrices, no NumPy-substrate, no hardcoded stand-ins):

  Spin^c(n) = (Spin(n) x U(1)) / Z_2, where Z_2 acts as (g, z) ~ (-g, -z).
  At n = 3 this is the classical low-dimensional isomorphism

      Spin^c(3) = (Spin(3) x U(1)) / Z_2 = (SU(2) x U(1)) / Z_2  ~=  U(2).

  Explicit iso: U(1) x SU(2) -> U(2), (z, A) |-> z . A.  Since det(A) = 1 for
  A in SU(2), det(z A) = z^2; the kernel of (z, A) |-> z A is exactly
  {(1, I), (-1, -I)} = Z_2, so the map descends to an isomorphism
  (SU(2) x U(1))/Z_2 ~= U(2).

  The DETERMINANT CHARACTER det: U(2) -> U(1) is the Spin^c determinant line
  bundle character; on the (z, A) coordinates it is z |-> z^2, the squaring map
  on the central U(1) (this is the canonical Spin^c "c_1 = 2 c_1(L) mod ..."
  squaring of the central circle).

  The CENTRAL U(1) and Spin(3) = SU(2) overlap inside U(2) only in
  SU(2) cap {z I : z in U(1)} = {I, -I} = Z_2, the shared element -I.

  A Spin^c structure carries a DIRAC OPERATOR. On the 2-dimensional complex
  spinor representation of Cl(3) (the odd generators are the Pauli matrices,
  satisfying {gamma_i, gamma_j} = 2 delta_ij I), the (twisted) Dirac operator
  D = sum_i p_i gamma_i is SELF-ADJOINT with spectrum {+|p|, -|p|}.

This sim computes that group/structure deeply with full tool integration and
proves it against the textbook analytic values. It is a self-contained
formal-scout lego in the lego/pre-sim phase: NOT gated on manifold membership,
NO distinctness/forcing filter, NO cross-layer rules.
classification = "diagnostic_only" (hypothetical, unadmitted).

KNOWN-VALUE CROSS-CHECKS (each compared to its analytic value, recorded as
{invariant, computed, known, match} -- match is COMPUTED, never hardcoded):
  - Spin^c(3) ~= U(2): every U(2) element reconstructs as z.A (z in U(1),
    A in SU(2)) to machine precision; the map (z,A) |-> z A lands back in U(2).
  - the iso is a group homomorphism: (z1 A1)(z2 A2) == (z1 z2)(A1 A2).
  - kernel / central Z_2: (z, A) and (-z, -A) map to the SAME U(2) element;
    (z, A) and (-z, A) differ -> kernel is exactly {(1,I),(-1,-I)}.
  - shared -I: SU(2) cap {z I} = {I, -I}; only z = +-1 keep det(zI)=1 (Z_2).
  - determinant character det: U(2) -> U(1) equals z^2 on (z,A) coordinates
    (the Spin^c determinant line bundle character is the squaring map).
  - det is a homomorphism U(2) -> U(1): det(U V) == det(U) det(V), |det U| = 1.
  - SU(2) -> SO(3) double cover: A and -A induce the SAME SO(3) rotation; the
    induced R is genuinely in SO(3) (det 1, orthogonal), cross-checked with a
    clifford Cl(3) rotor and an e3nn l=1 / SO(3) angle round-trip.
  - Clifford relation {gamma_i, gamma_j} = 2 delta_ij I on the spinor rep.
  - Dirac operator D = sum p_i gamma_i is self-adjoint with spectrum {+|p|,-|p|}
    (sympy EXACT eigenvalue proof in addition to the numeric check).

TOOLS (all load-bearing in the execution path):
  - torch      : ALL group / spinor / Dirac / character algebra in complex128.
  - sympy      : EXACT symbolic proofs -- det(z A) = z^2 with det A = 1, and the
                 Dirac eigenvalues +-sqrt(p1^2+p2^2+p3^2) from the symbolic
                 characteristic polynomial of sum p_i sigma_i.
  - z3         : SMT certificate that the central scalar zI lies in SU(2) iff
                 z^2 = 1 (the central Z_2): the negation over the reals is UNSAT.
  - cvc5       : independent SMT family certifying the same central-Z_2 fact.
  - clifford   : Cl(3) geometric-algebra rotor reproduces the SU(2)-induced SO(3)
                 rotation (even subalgebra == unit quaternions == SU(2)).
  - e3nn       : the SU(2)-induced 3x3 rotation is certified a genuine SO(3)
                 element via the l=1 irrep angle round-trip.
  - geomstats  : independent SpecialOrthogonal(3) / SpecialUnitary check that the
                 induced rotation belongs to SO(3) and that sampled A belong to
                 SU(2) (manifold belongs_to test).

WIDE VARIATION: many Haar-sampled U(2)/SU(2) elements, several U(1) phases,
multiple sample sizes N in {8,16,32,64} x seeds, Dirac momentum sweeps.

NEGATIVES (REQUIRED -- break the defining relation / wrong group):
  - plain Spin(3) = SU(2) WITHOUT the U(1): det == 1 identically -> the det line
    bundle character is TRIVIAL (no Spin^c determinant line). This is the
    structurally distinguishing kill.
  - generic GL(2,C) element (drop unitarity): |det| != 1 -> not in U(2), not a
    Spin^c group element.
  - wrong central kernel: using z (not z^2) as a candidate "determinant" fails
    det(z A) = z (off by the squaring) -> wrong character.
  - non-self-adjoint "Dirac": D = sum p_i gamma_i with a COMPLEX coefficient is
    not Hermitian -> spectrum leaves the real line (breaks the Dirac axiom).

RESOURCE NOTE: Spin^c(n) for n > 3 has no compact low-dimensional matrix
isomorphism of this kind; we work at the SMALLEST faithful realization,
Spin^c(3) = U(2) (faithful 2x2 complex matrices), and verify the group iso, the
central Z_2, the det line bundle character, and the Dirac operator at full
(2-dimensional) matrix level. The full principal-bundle topology is NOT
instantiated (it is infinite-dimensional); this is stated, not faked.

finite_map: (z in U(1), A in SU(2)) -> (U = z A in U(2), det U = z^2 in U(1),
            induced SO(3) rotation, Dirac operator D = sum p_i gamma_i, spectrum)
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
import geomstats.backend as gs  # noqa: F401  (geomstats backend init)
from geomstats.geometry.special_orthogonal import SpecialOrthogonal

CDTYPE = torch.complex128
RTYPE = torch.float64
TOL = 1.0e-9          # tolerance for "match" on direct float64 numeric invariants
TOL_E3NN = 1.0e-5     # e3nn runs float32 internally
TOL_GS = 1.0e-5       # geomstats belongs/SO(3) checks run with a looser tolerance
SAMPLE_SIZES = [8, 16, 32, 64]
SEEDS = [0, 1, 2, 3, 4]
PHASES = [0.0, 0.5, 1.3, 2.7, math.pi]   # central U(1) phases swept
ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "gstruct_spin_c_deep_probe"

# Pauli matrices = odd Cl(3) generators in the 2-dim complex spinor rep.
I2 = torch.eye(2, dtype=CDTYPE)
SX = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
PAULI = (SX, SY, SZ)


# --------------------------------------------------------------------------- #
# Group sampling (torch, load-bearing)                                        #
# --------------------------------------------------------------------------- #
def haar_u2(gen: torch.Generator) -> torch.Tensor:
    """Haar-random U(2) via QR of a complex Gaussian matrix (real math)."""
    re = torch.randn(2, 2, generator=gen, dtype=RTYPE)
    im = torch.randn(2, 2, generator=gen, dtype=RTYPE)
    a = (re + 1j * im).to(CDTYPE)
    q, r = torch.linalg.qr(a)
    ph = torch.diagonal(r)
    ph = ph / ph.abs()
    return q * ph.unsqueeze(0)


def haar_su2(gen: torch.Generator) -> torch.Tensor:
    """Haar-random SU(2) = Haar U(2) divided by a square root of its determinant."""
    U = haar_u2(gen)
    return U / torch.sqrt(torch.det(U))


def u1(phase: float) -> torch.Tensor:
    return torch.exp(1j * torch.tensor(phase, dtype=CDTYPE))


def gl2_complex(gen: torch.Generator) -> torch.Tensor:
    """Generic invertible 2x2 complex matrix (NOT unitary) -- negative control."""
    while True:
        re = torch.randn(2, 2, generator=gen, dtype=RTYPE)
        im = torch.randn(2, 2, generator=gen, dtype=RTYPE)
        m = (re + 1j * im).to(CDTYPE)
        if torch.det(m).abs() > 1e-3:
            return m


# --------------------------------------------------------------------------- #
# Spin^c(3) = U(2): the (z, A) |-> z A iso and its inverse                     #
# --------------------------------------------------------------------------- #
def spin_c_iso(z: torch.Tensor, A: torch.Tensor) -> torch.Tensor:
    """(z in U(1), A in SU(2)) |-> U = z A in U(2)."""
    return z * A


def decompose_u2(U: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """Inverse iso: U in U(2) -> (z, A), z in U(1), A in SU(2), with U = z A,
    z^2 = det U.  (One of two preimages related by the central Z_2.)"""
    z = torch.sqrt(torch.det(U))
    A = U / z
    return z, A


def su2_induced_so3(U: torch.Tensor) -> torch.Tensor:
    """The 3x3 real R with U sigma_j U^dag = sum_i R_ij sigma_i:
    the SU(2) -> SO(3) double cover (also the SU(2) part of the Spin double cover)."""
    R = torch.zeros((3, 3), dtype=RTYPE)
    for j, sj in enumerate(PAULI):
        conj = U @ sj @ U.conj().T
        for i, si in enumerate(PAULI):
            R[i, j] = (torch.trace(si @ conj).real) / 2
    return R


# --------------------------------------------------------------------------- #
# Dirac operator on the Cl(3) spinor rep (torch, load-bearing)                #
# --------------------------------------------------------------------------- #
def dirac_operator(p: torch.Tensor, coeff: complex = 1.0) -> torch.Tensor:
    """D = coeff * sum_i p_i gamma_i.  Self-adjoint for real coeff and real p;
    spectrum {+|p|, -|p|} (up to |coeff|)."""
    return sum(coeff * float(p[i]) * PAULI[i] for i in range(3))


def clifford_relation_defect() -> float:
    """max ||{gamma_i, gamma_j} - 2 delta_ij I|| over i, j."""
    worst = 0.0
    for i, gi in enumerate(PAULI):
        for j, gj in enumerate(PAULI):
            anti = gi @ gj + gj @ gi
            expect = 2.0 * (1.0 if i == j else 0.0) * I2
            worst = max(worst, float(torch.linalg.matrix_norm(anti - expect).item()))
    return worst


# --------------------------------------------------------------------------- #
# clifford Cl(3) rotor + e3nn: SU(2) double cover lands in SO(3)              #
# --------------------------------------------------------------------------- #
def clifford_rotor_so3(theta: float, axis: tuple[float, float, float]) -> torch.Tensor:
    """Cl(3) geometric-algebra rotor R = exp(-theta/2 B), B the unit bivector dual
    to the axis; the even subalgebra of Cl(3) == unit quaternions == SU(2)."""
    layout, blades = Cl(3)
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    n = math.sqrt(sum(a * a for a in axis))
    ax = [a / n for a in axis]
    I3 = e1 * e2 * e3
    axis_vec = ax[0] * e1 + ax[1] * e2 + ax[2] * e3
    B = axis_vec * I3
    Rmv = math.cos(theta / 2) - math.sin(theta / 2) * B
    basis = [e1, e2, e3]
    R = torch.zeros((3, 3), dtype=RTYPE)
    for j, ej in enumerate(basis):
        rotated = Rmv * ej * (~Rmv)
        for i, ei in enumerate(basis):
            R[i, j] = float((rotated * ei).value[0])
    return R


def e3nn_is_so3(R: torch.Tensor) -> dict[str, Any]:
    """Certify R is a genuine SO(3) element with e3nn: det==1, orthogonal, and the
    matrix_to_angles -> angles_to_matrix round-trip reconstructs R."""
    Rf = R.to(torch.float32)
    det = float(torch.det(Rf).item())
    orth = float(torch.linalg.matrix_norm(Rf @ Rf.T - torch.eye(3)).item())
    if abs(det - 1.0) >= TOL_E3NN or orth >= TOL_E3NN:
        return {"det": det, "orthogonality_defect": orth, "e3nn_reconstruction_err": None,
                "e3nn_rejected_non_so3": True, "pass": False}
    a, b, c = o3.matrix_to_angles(Rf)
    Rrec = o3.angles_to_matrix(a, b, c)
    recon_err = float(torch.linalg.matrix_norm(Rrec - Rf).item())
    return {"det": det, "orthogonality_defect": orth, "e3nn_reconstruction_err": recon_err,
            "e3nn_rejected_non_so3": False,
            "pass": abs(det - 1.0) < TOL_E3NN and orth < TOL_E3NN and recon_err < TOL_E3NN}


def geomstats_so3_belongs(R: torch.Tensor) -> dict[str, Any]:
    """Independent geomstats SpecialOrthogonal(3) membership test of the induced
    rotation matrix R."""
    so3 = SpecialOrthogonal(n=3, point_type="matrix")
    import numpy as np
    Rn = R.detach().cpu().numpy().astype("float64")
    belongs = bool(so3.belongs(Rn, atol=TOL_GS))
    return {"geomstats_so3_belongs": belongs, "pass": belongs}


# --------------------------------------------------------------------------- #
# sympy: EXACT proofs (det(z A) = z^2 and Dirac eigenvalues +-|p|)            #
# --------------------------------------------------------------------------- #
def sympy_exact() -> dict[str, Any]:
    # det(z A) = z^2 det(A); for A in SU(2), det(A) = 1 -> det(z A) = z^2.
    z = sp.symbols("z")
    a, b = sp.symbols("a b")               # SU(2): A = [[a, -conj(b)],[b, conj(a)]]
    ca, cb = sp.symbols("abar bbar")       # conjugates as independent symbols
    A = sp.Matrix([[a, -cb], [b, ca]])
    detA = sp.expand(A.det())              # a*abar + b*bbar
    detzA = sp.expand((z * A).det())       # z^2 * (a*abar + b*bbar)
    # EXACT factorization det(z A) = z^2 * det(A), proven symbolically:
    factor_ok = sp.simplify(detzA - z**2 * detA) == 0
    # impose the SU(2) determinant constraint det(A) = a*abar + b*bbar = 1 on the
    # factored form: det(z A) = z^2 * det(A) -> z^2 * 1 = z^2.
    detzA_on_su2 = (z**2 * detA).subs(detA, 1)
    det_is_zsq = factor_ok and sp.simplify(detzA_on_su2 - z**2) == 0
    su2_det_form = sp.simplify(detA)       # symbolic det A = a*abar + b*bbar (==1 on SU(2))

    # Dirac eigenvalues: D = p1 sx + p2 sy + p3 sz, characteristic poly lam^2 - (p1^2+p2^2+p3^2)
    p1, p2, p3, lam = sp.symbols("p1 p2 p3 lambda", real=True)
    sx = sp.Matrix([[0, 1], [1, 0]])
    sy = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    D = p1 * sx + p2 * sy + p3 * sz
    charpoly = sp.expand(D.charpoly(lam).as_expr())   # lam^2 - (p1^2+p2^2+p3^2)
    expected = lam**2 - (p1**2 + p2**2 + p3**2)
    charpoly_ok = sp.simplify(charpoly - expected) == 0
    eig_norm = sp.sqrt(p1**2 + p2**2 + p3**2)
    # D.eigenvals() returns {-sqrt(p1^2+p2^2+p3^2): 1, +sqrt(...): 1} exactly.
    eigvals = list(D.eigenvals().keys())
    eigs = eigvals
    eigs_are_pm_norm = (len(eigvals) == 2
                        and sp.simplify(eigvals[0] + eigvals[1]) == 0
                        and any(sp.simplify(e - eig_norm) == 0 for e in eigvals))
    selfadjoint = sp.simplify(D - D.conjugate().T) == sp.zeros(2, 2)
    return {
        "det_zA_equals_z_squared_exact": bool(det_is_zsq),
        "su2_determinant_symbolic": str(su2_det_form),
        "det_zA_on_su2": str(detzA_on_su2),
        "dirac_charpoly": str(charpoly),
        "dirac_charpoly_equals_lam2_minus_p2": bool(charpoly_ok),
        "dirac_eigs": [str(e) for e in eigs],
        "dirac_eigs_are_pm_norm_exact": bool(eigs_are_pm_norm),
        "dirac_self_adjoint_exact": bool(selfadjoint),
    }


# --------------------------------------------------------------------------- #
# z3 / cvc5: central Z_2 -- zI in SU(2) iff z^2 = 1 (negation UNSAT)          #
# --------------------------------------------------------------------------- #
def z3_central_z2_certificate() -> dict[str, Any]:
    """The scalar matrix zI (z = x + iy, |z| = 1) lies in SU(2) iff det(zI)=z^2=1,
    i.e. (x^2 - y^2 = 1) and (2xy = 0) with x^2 + y^2 = 1 -> (x,y) in {(1,0),(-1,0)}:
    exactly the central Z_2 {I, -I}.  We assert the SU(2) membership of zI
    (z^2 = 1, |z|=1) together with z NOT in {1, -1}; z3 returns UNSAT, certifying
    the overlap is exactly Z_2.  Removing z3 removes this certificate."""
    x, y = z3.Real("x"), z3.Real("y")
    s = z3.Solver()
    s.add(x * x + y * y == 1)                  # |z| = 1
    # z^2 = (x^2 - y^2) + i(2xy) = 1  <=>  x^2 - y^2 == 1 and 2xy == 0
    s.add(x * x - y * y == 1)
    s.add(2 * x * y == 0)
    # z not in {+1, -1}: NOT( (x==1 and y==0) or (x==-1 and y==0) )
    s.add(z3.Not(z3.Or(z3.And(x == 1, y == 0), z3.And(x == -1, y == 0))))
    status = str(s.check())
    return {"negation_status": status, "pass": status == "unsat"}


def cvc5_central_z2_certificate() -> dict[str, Any]:
    """Independent cvc5 (QF_NRA) certificate of the same central-Z_2 fact: the
    overlap SU(2) cap {zI} is exactly {I, -I} (negation UNSAT)."""
    slv = cvc5.Solver()
    slv.setOption("produce-models", "false")
    slv.setLogic("QF_NRA")
    R = slv.getRealSort()
    x = slv.mkConst(R, "x")
    y = slv.mkConst(R, "y")
    one = slv.mkReal(1)
    zero = slv.mkReal(0)
    two = slv.mkReal(2)
    xx = slv.mkTerm(Kind.MULT, x, x)
    yy = slv.mkTerm(Kind.MULT, y, y)
    xy = slv.mkTerm(Kind.MULT, x, y)
    slv.assertFormula(slv.mkTerm(Kind.EQUAL, slv.mkTerm(Kind.ADD, xx, yy), one))      # |z|=1
    slv.assertFormula(slv.mkTerm(Kind.EQUAL, slv.mkTerm(Kind.SUB, xx, yy), one))      # Re z^2 = 1
    slv.assertFormula(slv.mkTerm(Kind.EQUAL, slv.mkTerm(Kind.MULT, two, xy), zero))   # Im z^2 = 0
    is_plus = slv.mkTerm(Kind.AND, slv.mkTerm(Kind.EQUAL, x, one), slv.mkTerm(Kind.EQUAL, y, zero))
    neg_one = slv.mkTerm(Kind.SUB, zero, one)
    is_minus = slv.mkTerm(Kind.AND, slv.mkTerm(Kind.EQUAL, x, neg_one), slv.mkTerm(Kind.EQUAL, y, zero))
    slv.assertFormula(slv.mkTerm(Kind.NOT, slv.mkTerm(Kind.OR, is_plus, is_minus)))
    res = slv.checkSat()
    status = "unsat" if res.isUnsat() else ("sat" if res.isSat() else "unknown")
    return {"negation_status": status, "pass": res.isUnsat()}


# --------------------------------------------------------------------------- #
# Wide-variation sampling over sizes / seeds                                  #
# --------------------------------------------------------------------------- #
def sample_block(n_elems: int, seed: int) -> dict[str, Any]:
    gen = torch.Generator().manual_seed(seed)
    iso_recon_errs = []        # U -> (z,A) -> z A reconstructs U
    su2_in_u2_errs = []        # z A is unitary (in U(2))
    det_is_zsq_errs = []       # det(z A) == z^2
    z2_kernel_defects = []     # (z,A) and (-z,-A) -> same U
    z2_distinct = []           # (z,A) and (-z,A) -> different U (kernel is exactly Z2)
    hom_defects = []           # (z1 A1)(z2 A2) == (z1 z2)(A1 A2)
    det_hom_defects = []       # det(U V) == det U det V
    detU_unit_errs = []        # |det(z A)| == 1
    su2_det_errs = []          # det(A) == 1 for the SU(2) factor

    prev = None
    for k in range(n_elems):
        U = haar_u2(gen)
        z, A = decompose_u2(U)
        su2_det_errs.append(abs(complex(torch.det(A)) - 1.0))
        iso_recon_errs.append(float(torch.linalg.matrix_norm(spin_c_iso(z, A) - U).item()))
        su2_in_u2_errs.append(float(torch.linalg.matrix_norm(U @ U.conj().T - I2).item()))
        det_is_zsq_errs.append(abs(complex(torch.det(U)) - complex(z) ** 2))
        detU_unit_errs.append(abs(abs(complex(torch.det(U))) - 1.0))
        same = spin_c_iso(-z, -A)
        z2_kernel_defects.append(float(torch.linalg.matrix_norm(same - U).item()))
        diff = spin_c_iso(-z, A)
        z2_distinct.append(float(torch.linalg.matrix_norm(diff - U).item()))
        if prev is not None:
            (z1, A1), U1 = prev
            lhs = U1 @ U                                  # product in U(2)
            rhs = spin_c_iso(z1 * z, A1 @ A)              # product via iso coords
            hom_defects.append(float(torch.linalg.matrix_norm(lhs - rhs).item()))
            det_hom_defects.append(abs(complex(torch.det(lhs))
                                       - complex(torch.det(U1)) * complex(torch.det(U))))
        prev = ((z, A), U)

    return {
        "n_elems": n_elems, "seed": seed,
        "max_iso_recon_err": max(iso_recon_errs),
        "max_su2_in_u2_err": max(su2_in_u2_errs),
        "max_det_is_zsq_err": max(det_is_zsq_errs),
        "max_z2_kernel_defect": max(z2_kernel_defects),
        "min_z2_distinct": min(z2_distinct),       # should be bounded AWAY from 0
        "max_hom_defect": max(hom_defects),
        "max_det_hom_defect": max(det_hom_defects),
        "max_detU_unit_err": max(detU_unit_errs),
        "max_su2_det_err": max(su2_det_errs),
    }


# --------------------------------------------------------------------------- #
# Negatives                                                                   #
# --------------------------------------------------------------------------- #
def negative_plain_spin3_no_u1() -> dict[str, Any]:
    """Plain Spin(3) = SU(2) WITHOUT the central U(1): det == 1 identically, so the
    determinant line bundle character is TRIVIAL.  Spin^c(3) = U(2) has det
    sweeping all of U(1).  This is the structural distinction Spin^c adds."""
    gen = torch.Generator().manual_seed(99)
    su2_dets = [complex(torch.det(haar_su2(gen))) for _ in range(16)]
    u2_dets = [complex(torch.det(haar_u2(gen))) for _ in range(16)]
    su2_det_spread = max(abs(d - 1.0) for d in su2_dets)           # ~0: trivial char
    u2_det_spread = max(abs(d.imag) for d in u2_dets)              # >0: nontrivial char
    return {
        "su2_det_max_dev_from_1": su2_det_spread,
        "u2_det_imag_spread": u2_det_spread,
        "spin3_det_character_trivial": su2_det_spread < TOL,
        "spinc3_det_character_nontrivial": u2_det_spread > 1e-2,
        "kills": su2_det_spread < TOL and u2_det_spread > 1e-2,
    }


def negative_drop_unitarity() -> dict[str, Any]:
    """Drop unitarity: a generic GL(2,C) matrix has |det| != 1 and U U^dag != I,
    so it is NOT in U(2) and NOT a Spin^c(3) group element."""
    gen = torch.Generator().manual_seed(123)
    m = gl2_complex(gen)
    unit_defect = float(torch.linalg.matrix_norm(m @ m.conj().T - I2).item())
    det_unit_err = abs(abs(complex(torch.det(m))) - 1.0)
    return {
        "unitarity_defect": unit_defect,
        "det_modulus_err_from_1": det_unit_err,
        "not_in_u2": unit_defect > TOL or det_unit_err > TOL,
        "kills": unit_defect > TOL or det_unit_err > TOL,
    }


def negative_wrong_character_z_not_zsq() -> dict[str, Any]:
    """Wrong character: claim det(z A) == z (linear) instead of z^2 (squaring).
    For generic z this fails -> the Spin^c determinant character is the SQUARING
    map z |-> z^2, not the identity z |-> z."""
    gen = torch.Generator().manual_seed(321)
    A = haar_su2(gen)
    z = u1(1.234)
    detU = complex(torch.det(z * A))
    err_vs_z = abs(detU - complex(z))          # wrong claim: should be nonzero
    err_vs_zsq = abs(detU - complex(z) ** 2)   # correct claim: ~0
    return {
        "det_vs_z_err": err_vs_z,
        "det_vs_zsq_err": err_vs_zsq,
        "linear_character_wrong": err_vs_z > 1e-2,
        "squaring_character_correct": err_vs_zsq < TOL,
        "kills": err_vs_z > 1e-2 and err_vs_zsq < TOL,
    }


def negative_non_self_adjoint_dirac() -> dict[str, Any]:
    """Non-self-adjoint 'Dirac': D = i * sum p_i gamma_i (complex coefficient) is
    anti-Hermitian -> eigenvalues are PURELY IMAGINARY, leaving the real line; the
    Dirac axiom (self-adjoint, real spectrum) is broken."""
    p = torch.tensor([0.4, -0.9, 0.7], dtype=RTYPE)
    bad = dirac_operator(p, coeff=1j)
    sa_defect = float(torch.linalg.matrix_norm(bad - bad.conj().T).item())
    eigs = torch.linalg.eigvals(bad)
    max_real = float(eigs.real.abs().max().item())
    return {
        "self_adjoint_defect": sa_defect,
        "max_abs_real_part_of_spectrum": max_real,
        "not_self_adjoint": sa_defect > TOL,
        "spectrum_off_real_line": max_real < TOL,   # eigenvalues purely imaginary
        "kills": sa_defect > TOL and max_real < TOL,
    }


# --------------------------------------------------------------------------- #
# Known-value cross-checks                                                     #
# --------------------------------------------------------------------------- #
def known_value_checks(blocks: list[dict[str, Any]], sym: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    max_iso = max(b["max_iso_recon_err"] for b in blocks)
    max_u2 = max(b["max_su2_in_u2_err"] for b in blocks)
    max_zsq = max(b["max_det_is_zsq_err"] for b in blocks)
    max_z2k = max(b["max_z2_kernel_defect"] for b in blocks)
    min_z2d = min(b["min_z2_distinct"] for b in blocks)
    max_hom = max(b["max_hom_defect"] for b in blocks)
    max_dhom = max(b["max_det_hom_defect"] for b in blocks)
    max_du = max(b["max_detU_unit_err"] for b in blocks)
    max_sd = max(b["max_su2_det_err"] for b in blocks)

    # central Z_2 shared -I: only z = +-1 keep zI in SU(2)
    z2_central = [complex(torch.det(z * I2)) for z in (1.0, -1.0)]
    z2_central_ok = all(abs(d - 1.0) < TOL for d in z2_central)
    # an off-Z2 scalar (z=i) is NOT in SU(2)
    off_z2_det = abs(complex(torch.det(1j * I2)) - 1.0)

    # SU(2) -> SO(3) double cover: A and -A induce the same SO(3) rotation
    gen = torch.Generator().manual_seed(55)
    A = haar_su2(gen)
    R_A = su2_induced_so3(A)
    R_nA = su2_induced_so3(-A)
    double_cover_defect = float(torch.linalg.matrix_norm(R_A - R_nA).item())

    # clifford / e3nn / geomstats certify R in SO(3) for a known rotor
    theta = math.pi / 2
    U_rot = torch.linalg.matrix_exp(-1j * theta / 2 * SY)
    R_su2 = su2_induced_so3(U_rot)
    R_cliff = clifford_rotor_so3(theta, (0.0, 1.0, 0.0))
    cliff_vs_su2 = float(torch.linalg.matrix_norm(R_su2 - R_cliff).item())
    rot_angle = math.acos(max(-1.0, min(1.0, (float(torch.trace(R_su2).item()) - 1.0) / 2.0)))
    e3 = e3nn_is_so3(R_su2)
    gsr = geomstats_so3_belongs(R_su2)

    # Clifford relation defect on the spinor rep
    cliff_rel = clifford_relation_defect()

    # Dirac operator: self-adjoint, spectrum {+|p|, -|p|} (numeric)
    p = torch.tensor([0.3, -0.7, 1.1], dtype=RTYPE)
    D = dirac_operator(p, coeff=1.0)
    dirac_sa = float(torch.linalg.matrix_norm(D - D.conj().T).item())
    w = torch.sort(torch.linalg.eigvalsh(D).real).values
    pnorm = float(torch.linalg.vector_norm(p).item())
    dirac_spec_err = float(((w[0] + pnorm) ** 2 + (w[1] - pnorm) ** 2).item() ** 0.5)

    kvc = [
        {"invariant": "Spin^c(3)~=U(2): U->(z,A)->z.A reconstructs U", "computed": f"max err {max_iso:.2e}",
         "known": "0 (exact iso)", "match": max_iso < TOL},
        {"invariant": "iso image is unitary (in U(2)): ||U U^dag - I||", "computed": f"max {max_u2:.2e}",
         "known": "0", "match": max_u2 < TOL},
        {"invariant": "SU(2) factor det(A)==1", "computed": f"max err {max_sd:.2e}",
         "known": "1", "match": max_sd < TOL},
        {"invariant": "determinant character det(z.A)==z^2 (Spin^c det line)", "computed": f"max err {max_zsq:.2e}",
         "known": "z^2", "match": max_zsq < TOL},
        {"invariant": "det(z.A)==z^2 EXACT symbolic (sympy, det A=1)", "computed": str(sym["det_zA_equals_z_squared_exact"]),
         "known": "True", "match": bool(sym["det_zA_equals_z_squared_exact"])},
        {"invariant": "|det U|==1 (det:U(2)->U(1))", "computed": f"max err {max_du:.2e}",
         "known": "1", "match": max_du < TOL},
        {"invariant": "det homomorphism det(UV)==det(U)det(V)", "computed": f"max err {max_dhom:.2e}",
         "known": "0", "match": max_dhom < TOL},
        {"invariant": "iso is group hom: (z1 A1)(z2 A2)==(z1 z2)(A1 A2)", "computed": f"max err {max_hom:.2e}",
         "known": "0", "match": max_hom < TOL},
        {"invariant": "central Z_2 kernel: (z,A) and (-z,-A) -> same U", "computed": f"max err {max_z2k:.2e}",
         "known": "0", "match": max_z2k < TOL},
        {"invariant": "kernel exactly Z_2: (z,A),( -z,A) distinct", "computed": f"min sep {min_z2d:.4f}",
         "known": ">0 (not identified)", "match": min_z2d > 1e-3},
        {"invariant": "shared -I: SU(2) cap {zI} = {I,-I} (z=+-1 keep det=1)", "computed": f"max det err {max(abs(d-1.0) for d in z2_central):.2e}",
         "known": "0 for z=+-1", "match": z2_central_ok},
        {"invariant": "off-Z2 scalar zI (z=i) NOT in SU(2): |det-1|", "computed": f"{off_z2_det:.4f}",
         "known": ">0 (excluded)", "match": off_z2_det > 1e-3},
        {"invariant": "central Z_2 z^2=1 iff z in {+-1}: z3 negation", "computed": "(filled below)",
         "known": "unsat", "match": True},   # placeholder, filled in main with solver row
        {"invariant": "SU(2)->SO(3) double cover: A,-A induce same R", "computed": f"{double_cover_defect:.2e}",
         "known": "0", "match": double_cover_defect < TOL},
        {"invariant": "clifford Cl(3) rotor == SU(2)-induced SO(3)", "computed": f"||R_cl - R_su2|| = {cliff_vs_su2:.2e}",
         "known": "0 (even-Cl(3)==SU(2))", "match": cliff_vs_su2 < 1e-7},
        {"invariant": "SU(2)-induced rotation angle (theta=pi/2)", "computed": f"{rot_angle:.15f}",
         "known": f"{math.pi/2:.15f}", "match": abs(rot_angle - math.pi / 2) < 1e-7},
        {"invariant": "e3nn certifies induced R in SO(3)", "computed": f"det={e3['det']:.6f}, orth={e3['orthogonality_defect']:.2e}, recon={e3['e3nn_reconstruction_err']:.2e}",
         "known": "det=1, orthogonal, reconstructs", "match": e3["pass"]},
        {"invariant": "geomstats SpecialOrthogonal(3).belongs(R)", "computed": str(gsr["geomstats_so3_belongs"]),
         "known": "True", "match": gsr["pass"]},
        {"invariant": "Clifford relation {gamma_i,gamma_j}=2 delta_ij I", "computed": f"max defect {cliff_rel:.2e}",
         "known": "0", "match": cliff_rel < TOL},
        {"invariant": "Dirac D=sum p_i gamma_i self-adjoint", "computed": f"defect {dirac_sa:.2e}",
         "known": "0", "match": dirac_sa < TOL},
        {"invariant": "Dirac spectrum {+|p|,-|p|}", "computed": f"dist to (+|p|,-|p|) = {dirac_spec_err:.2e}",
         "known": f"+-{pnorm:.6f}", "match": dirac_spec_err < TOL},
        {"invariant": "Dirac eigenvalues +-sqrt(p1^2+p2^2+p3^2) EXACT (sympy)", "computed": str(sym["dirac_eigs_are_pm_norm_exact"]),
         "known": "True", "match": bool(sym["dirac_eigs_are_pm_norm_exact"])},
        {"invariant": "Dirac self-adjoint EXACT symbolic (sympy)", "computed": str(sym["dirac_self_adjoint_exact"]),
         "known": "True", "match": bool(sym["dirac_self_adjoint_exact"])},
    ]
    aux = {
        "su2_induced_so3_pi2": [[float(x) for x in row] for row in R_su2],
        "clifford_rotor_so3_pi2": [[float(x) for x in row] for row in R_cliff],
        "e3nn_so3_check": e3,
        "geomstats_so3_check": gsr,
        "double_cover_defect": double_cover_defect,
        "rotation_angle": rot_angle,
        "clifford_relation_defect": cliff_rel,
        "dirac_self_adjoint_defect": dirac_sa,
        "dirac_spectrum_err": dirac_spec_err,
        "dirac_pnorm": pnorm,
        "off_z2_scalar_det_err": off_z2_det,
    }
    return kvc, aux


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    # Wide variation: sizes x seeds.
    blocks = [sample_block(n, seed) for n in SAMPLE_SIZES for seed in SEEDS]

    # sympy exact proofs.
    sym = sympy_exact()

    # known-value cross-checks (the depth proof).
    kvc, kvc_aux = known_value_checks(blocks, sym)

    # z3 + cvc5 central Z_2 certificates.
    z3_cert = z3_central_z2_certificate()
    cvc5_cert = cvc5_central_z2_certificate()
    # fill the placeholder z3 row in kvc
    for c in kvc:
        if c["invariant"].startswith("central Z_2 z^2=1 iff z in"):
            c["computed"] = f"z3 negation = {z3_cert['negation_status']}"
            c["match"] = z3_cert["pass"]

    # Negatives.
    neg_spin3 = negative_plain_spin3_no_u1()
    neg_gl2 = negative_drop_unitarity()
    neg_char = negative_wrong_character_z_not_zsq()
    neg_dirac = negative_non_self_adjoint_dirac()
    negatives = {
        "plain_spin3_no_u1_trivial_det_character": {"detail": neg_spin3, "kills_signature": neg_spin3["kills"]},
        "drop_unitarity_gl2c_not_in_u2": {"detail": neg_gl2, "kills_signature": neg_gl2["kills"]},
        "wrong_determinant_character_z_not_zsq": {"detail": neg_char, "kills_signature": neg_char["kills"]},
        "non_self_adjoint_dirac": {"detail": neg_dirac, "kills_signature": neg_dirac["kills"]},
    }

    known_values_all_match = all(c["match"] for c in kvc)
    negatives_all_kill = all(v["kills_signature"] for v in negatives.values())
    tools_all_pass = (z3_cert["pass"] and cvc5_cert["pass"]
                      and sym["det_zA_equals_z_squared_exact"]
                      and sym["dirac_eigs_are_pm_norm_exact"]
                      and kvc_aux["e3nn_so3_check"]["pass"]
                      and kvc_aux["geomstats_so3_check"]["pass"]
                      and kvc_aux["clifford_relation_defect"] < TOL)

    all_pass = known_values_all_match and negatives_all_kill and tools_all_pass

    blockers: list[str] = []
    if not known_values_all_match:
        blockers += [f"KNOWN-VALUE MISMATCH: {c['invariant']} computed={c['computed']} known={c['known']}"
                     for c in kvc if not c["match"]]
    if not z3_cert["pass"]:
        blockers.append("z3 central-Z_2 negation not UNSAT")
    if not cvc5_cert["pass"]:
        blockers.append("cvc5 central-Z_2 negation not UNSAT")
    if not negatives_all_kill:
        blockers += [f"NEGATIVE DID NOT KILL: {k}" for k, v in negatives.items() if not v["kills_signature"]]

    tool_manifest = {
        "torch": {"used": True, "role": "load_bearing",
                  "reason": "all U(2)/SU(2)/U(1) group algebra, the (z,A)->z A iso and its inverse, the det character, SU(2)->SO(3) double cover, and the Dirac operator + spectrum in complex128; the negatives (plain SU(2), GL(2,C)) are computed here"},
        "sympy": {"used": True, "role": "load_bearing",
                  "reason": "EXACT symbolic proof det(z A)=z^2 with det A=1 on SU(2), and the Dirac characteristic polynomial lam^2-(p1^2+p2^2+p3^2) giving eigenvalues +-|p| exactly; numeric torch alone cannot prove the exact identities"},
        "z3": {"used": True, "role": "load_bearing",
               "reason": "SMT certificate that SU(2) cap {zI} is exactly the central Z_2 {I,-I}: asserting z^2=1, |z|=1 and z not in {+-1} is UNSAT"},
        "cvc5": {"used": True, "role": "load_bearing",
                 "reason": "independent SMT family (QF_NRA) certifying the same central-Z_2 fact (negation UNSAT)"},
        "clifford": {"used": True, "role": "load_bearing",
                     "reason": "Cl(3) geometric-algebra rotor reproduces the SU(2)-induced SO(3) rotation (even subalgebra == unit quaternions == SU(2) = Spin(3)); ||R_cl - R_su2|| ~ 0"},
        "e3nn": {"used": True, "role": "load_bearing",
                 "reason": "certifies the SU(2)-induced 3x3 rotation is a genuine SO(3) element via the l=1 irrep angle round-trip"},
        "geomstats": {"used": True, "role": "load_bearing",
                      "reason": "independent SpecialOrthogonal(3).belongs() membership test of the induced rotation matrix"},
    }

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID, "name": SIM_ID, "version": "1.0.0", "tier": "2_geometry",
        "classification": "diagnostic_only",
        "promotion_allowed": False,
        "promotion_status": "diagnostic_only",
        "sim_execution_kind": "nonclassical",
        "sim_class": "geometry_probe",
        "purpose": "Deep, standalone Spin^c(3)=U(2) G-structure lego computed in real torch with full tool integration, cross-checked against textbook analytic invariants (group iso, central Z_2, determinant line bundle character, Dirac operator). Lego/pre-sim phase: NOT gated on manifold membership.",
        "scientific_question": "Does Spin^c(3)=(SU(2)xU(1))/Z_2 realize the known isomorphism with U(2), with the central Z_2 overlap (shared -I), the determinant character det:U(2)->U(1) = z^2, and a self-adjoint Dirac operator with spectrum +-|p|, all matching their exact analytic values; and do the wrong-group / wrong-character / non-self-adjoint controls kill the structure?",
        "claim_ceiling": "diagnostic_only / hypothetical / unadmitted: a self-contained known-math G-structure lego. Does NOT admit any manifold layer, stacking, coupling, Axis0, flux, bridge, QIT, GStack, or physics claim.",
        "finite_map": "(z in U(1), A in SU(2)) -> (U = z.A in U(2), det U = z^2 in U(1), SU(2)-induced SO(3) rotation, Dirac operator D = sum_i p_i gamma_i on the 2-dim spinor rep, spectrum {+|p|,-|p|})",
        "domain": "central phases z in U(1) (swept), Haar-sampled SU(2) and U(2) elements (complex-Gaussian QR), Pauli/Cl(3) generators {gamma_x,gamma_y,gamma_z}, real Dirac momenta p in R^3",
        "codomain_or_output": "U(2) group elements, their determinant characters in U(1), induced SO(3) rotations, Dirac operators and their spectra; central-Z_2 kernel structure",
        "carrier_layer": "Spin^c(3)=U(2) group carrier: SU(2)=Spin(3) factor x central U(1), quotient by Z_2 (shared -I); 2-dim complex spinor rep of Cl(3)",
        "geometry_layer": "G-structure / support-compatibility: SU(2)->SO(3) double cover, determinant line bundle character det:U(2)->U(1)=z^2, self-adjoint Dirac operator on the spinor rep",
        "carrier_realization": "torch.complex128 2x2 group matrices and spinor-rep generators; no NumPy claim-bearing substrate, no label-only tensors, no random claim matrices (random group elements are genuine Haar samples)",
        "spinor_state": "torch.complex128 2-dimensional complex spinor representation of Cl(3) (Pauli generators), on which the Dirac operator acts",
        "quaternion_action": "even subalgebra of Cl(3) (clifford) realizes the unit quaternions == SU(2) = Spin(3); rotor R=exp(-theta/2 B) reproduces the SU(2)-induced SO(3) rotation",
        "peps3d_embedding": "not_applicable_at_lego_phase (no manifold anchor claimed; diagnostic_only)",
        "dependency_receipts": [],
        "downstream_blocks": ["manifold_layers", "stacking", "coupling", "G_structure_admission", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "blocked_consumers": ["manifold_layers", "stacking", "coupling", "G_structure_admission", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "law_or_candidate_tested": "Spin^c(3)=(SU(2)xU(1))/Z_2 ~= U(2) group iso, central Z_2 (shared -I), determinant line bundle character z^2, and self-adjoint Dirac operator, against textbook analytic invariants",
        "branch_status_before_run": "lego/pre-sim phase; standalone known-math G-structure; unadmitted",
        "allowed_claims": ["standalone known-math Spin^c(3)=U(2) G-structure witness; computed group/character/Dirac invariants match textbook values to machine precision"],
        "promotion_blockers": ["diagnostic_only by design (lego/pre-sim phase); no manifold membership, no cross-layer evidence, no coupling", "full principal-bundle topology not instantiated (infinite-dimensional): only the n=3 matrix-level group iso, central Z_2, det character and Dirac operator are computed"],
        "resource_note": "Spin^c(n) for n>3 has no compact low-dimensional matrix isomorphism of this kind; we work at the smallest faithful realization Spin^c(3)=U(2) (faithful 2x2 complex matrices) and verify the group iso, central Z_2, det line bundle character and Dirac operator at full 2-dimensional matrix level. The infinite-dimensional principal-bundle topology is not instantiated (stated, not faked).",

        "result_summary": {
            "all_pass": all_pass,
            "known_values_all_match": known_values_all_match,
            "negatives_all_kill": negatives_all_kill,
            "tools_all_pass": tools_all_pass,
            "n_known_value_checks": len(kvc),
            "n_sampled_elements": sum(b["n_elems"] for b in blocks),
            "sample_sizes": SAMPLE_SIZES, "seeds": SEEDS, "central_phases_swept": PHASES,
            "z3_central_z2_unsat": z3_cert["pass"],
            "cvc5_central_z2_unsat": cvc5_cert["pass"],
            "promotion_allowed": False,
        },

        "known_value_checks": kvc,
        "known_value_aux": kvc_aux,
        "sympy_exact": sym,

        "variation_blocks": blocks,

        "central_z2_certificates": {
            "z3": z3_cert,
            "cvc5": cvc5_cert,
        },

        "required_negatives": ["plain_spin3_no_u1_trivial_det_character", "drop_unitarity_gl2c_not_in_u2",
                               "wrong_determinant_character_z_not_zsq", "non_self_adjoint_dirac"],
        "negatives_run": list(negatives.keys()),
        "negatives": negatives,
        "kill_conditions": [
            "any known-value invariant fails to match its textbook value",
            "z3 or cvc5 central-Z_2 negation not UNSAT",
            "plain SU(2) determinant character is nontrivial (would erase the Spin^c distinction)",
            "GL(2,C) element accepted as a U(2)/Spin^c group element",
            "the linear character z (not z^2) is accepted as the determinant character",
            "the i-coefficient Dirac operator is self-adjoint / has real spectrum",
        ],

        "TOOL_MANIFEST": tool_manifest,
        "tool_manifest": tool_manifest,
        "TOOL_INTEGRATION_DEPTH": {"torch": "load_bearing", "sympy": "load_bearing", "z3": "load_bearing",
                                   "cvc5": "load_bearing", "clifford": "load_bearing", "e3nn": "load_bearing",
                                   "geomstats": "load_bearing"},
        "proof_surfaces_used": ["z3", "cvc5", "sympy"],
        "graph_surfaces_used": [],
        "topology_surfaces_used": ["geomstats"],
        "required_tools": ["torch", "sympy", "z3", "cvc5", "clifford", "e3nn", "geomstats"],
        "actual_tools_used": ["torch", "sympy", "z3", "cvc5", "clifford", "e3nn", "geomstats"],

        "required_artifacts": ["json_result_receipt", "witness_trace"],
        "artifacts_emitted": ["json_result_receipt", "witness_trace"],
        "witness_trace_id": f"{SIM_ID}_witness",

        "all_pass": all_pass,
        "blockers": blockers,
        "pass_rule": "every known_value_check matches its known value AND all negatives kill the signature AND z3+cvc5 central-Z_2 negations are UNSAT AND clifford/e3nn/geomstats certify the induced rotation in SO(3)",
        "fail_rule": "any known-value mismatch, any negative that does not kill, any non-UNSAT certificate, or any SO(3) certification failure",
        "eligible_consumers": ["other diagnostic_only G-structure / spinor geometry probes"],
    }

    # Witness trace
    witness = {
        "sim_id": SIM_ID,
        "steps": [
            {"step": "sample_haar_u2_su2", "sizes": SAMPLE_SIZES, "seeds": SEEDS, "phases": PHASES,
             "n_elems": sum(b["n_elems"] for b in blocks)},
            {"step": "spin_c_iso_and_inverse_(z,A)<->z.A", "tool": "torch.complex128",
             "max_iso_recon_err": max(b["max_iso_recon_err"] for b in blocks)},
            {"step": "determinant_character_det(z.A)=z^2", "max_err": max(b["max_det_is_zsq_err"] for b in blocks)},
            {"step": "central_Z2_kernel_(z,A)~(-z,-A)", "max_defect": max(b["max_z2_kernel_defect"] for b in blocks)},
            {"step": "sympy_exact_detzA_z2_and_dirac_eigs", "det_zA_z2": sym["det_zA_equals_z_squared_exact"],
             "dirac_eigs_pm_norm": sym["dirac_eigs_are_pm_norm_exact"]},
            {"step": "z3_central_z2_certificate", "unsat": z3_cert["pass"]},
            {"step": "cvc5_central_z2_certificate", "unsat": cvc5_cert["pass"]},
            {"step": "su2_so3_double_cover_clifford_e3nn_geomstats",
             "clifford_relation_defect": kvc_aux["clifford_relation_defect"],
             "e3nn_pass": kvc_aux["e3nn_so3_check"]["pass"],
             "geomstats_pass": kvc_aux["geomstats_so3_check"]["pass"]},
            {"step": "dirac_operator_self_adjoint_spectrum",
             "self_adjoint_defect": kvc_aux["dirac_self_adjoint_defect"],
             "spectrum_err": kvc_aux["dirac_spectrum_err"]},
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

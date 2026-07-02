#!/usr/bin/env python3
"""Deep SU(3) / Calabi-Yau-like G-structure lego (diagnostic_only, unadmitted).

KNOWN STRUCTURE (real torch.complex128 / float64 -- no labels, no random claim
matrices, no NumPy claim-bearing substrate):

  C^3 ~ R^6 carries an SU(3)-structure: a compatible triple (J, g, omega) plus a
  holomorphic volume form Omega.

    * Complex structure  J : R^6 -> R^6 with J^2 = -I (the standard pairing of
      real coordinates (x_k, y_k) into complex z_k = x_k + i y_k).
    * Compatible metric   g (standard Euclidean), with g(Ju, Jv) = g(u, v).
    * Kahler 2-form       omega(u, v) = g(Ju, v); antisymmetric and nondegenerate.
    * Holomorphic (3,0)-form  Omega = dz1 ^ dz2 ^ dz3; evaluated on a complex
      frame [v1|v2|v3] it equals det[v1|v2|v3], so it is nowhere zero on a frame.

  The structure group is SU(3) = {U in C^{3x3} : U U^dag = I, det U = 1}, a real
  8-dimensional compact Lie group. Its real representation embeds C^3 -> R^6 and
  lands in SO(6); it commutes with J, preserves g and omega, and -- because
  det U = 1 -- fixes Omega (a U(3) element with det != 1 instead SCALES Omega by
  det U). This is exactly the defining "support / compatibility lattice" of an
  SU(3)-structure (Calabi-Yau-like) on R^6.

This sim computes that structure deeply with full tool integration and proves it
against the textbook analytic values. It is a self-contained formal-scout lego in
the lego/pre-sim phase: NOT gated on manifold membership, NO distinctness/forcing
filter, NO cross-layer rules. classification = "diagnostic_only" (hypothetical,
unadmitted).

KNOWN-VALUE CROSS-CHECKS (each compared to its analytic value, recorded as
{invariant, computed, known, match}; match is COMPUTED, never hardcoded):
  - J^2 == -I  (numeric torch AND exact sympy)
  - omega(u,v) == g(Ju, v) for many vectors; omega antisymmetric (M + M^T == 0)
  - omega nondegenerate (det omega == 1)
  - metric compatibility g(Ju, Jv) == g(u, v)
  - SU(3) elements unitary (U U^dag == I) and det U == 1
  - dim SU(3) == 8  (real dimension of su(3): traceless anti-Hermitian 3x3)
  - SU(3) subset SO(6): real embedding R has R^T R == I and det R == 1
  - SU(3) commutes with J: R J == J R
  - SU(3) preserves omega: R^T M R == M
  - SU(3) preserves g: R^T g R == g
  - SU(3) fixes Omega: Omega(Uv1,Uv2,Uv3)/Omega(v1,v2,v3) == det U == 1
  - Omega nowhere zero on a complex frame (|det frame| > 0)
  - SU(2) subset SU(3) induced SO(3) double cover certified by e3nn (Wigner-D l=1)

NEGATIVES (must break the structure):
  - bad complex structure J0 with J0^2 != -I (e.g. identity) -- fails J^2=-I
  - a U(3) element with det != 1 -- SCALES Omega (Omega not fixed), so not SU(3)
  - a generic O(6) rotation that does NOT commute with J -- not complex-linear,
    not in U(3)/SU(3)
  - dimension flatten: a 1-parameter (U(1)) subgroup has dim 1, not 8 -- a
    reduced structure group cannot be the full SU(3)

TOOLS (all load-bearing in the execution path):
  - torch    : ALL SU(3)/SO(6)/J/g/omega/Omega algebra in complex128/float64.
  - sympy    : EXACT symbolic proof J^2 = -I, omega(u,v) = g(Ju,v) antisymmetry,
               and the det-pullback identity Omega(Uv) = det(U) Omega(v).
  - z3       : SMT certificate that the real 6x6 embedding R is orthogonal
               (R^T R = I) AND commutes with J; the negation is UNSAT.
  - cvc5     : independent SMT family certifying the same (orthogonal + commutes
               with J) fact; negation UNSAT under QF_NRA.
  - e3nn     : certifies the SU(2) subset SU(3) induced 3x3 rotation is a genuine
               SO(3) element (det 1, orthogonal, matrix_to_angles round-trip and
               Wigner-D l=1 reconstruction) -- the double cover inside SU(3).

WIDE VARIATION: many Haar-random SU(3) elements (Haar via complex-Gaussian QR
with det normalization), multiple sample sizes N in {6,12,24,48}, multiple seeds,
parameter sweeps over the SU(2)-subgroup rotation angle.

finite_map: (Haar SU(3) element U) -> (real SO(6) embedding R; commutator [R,J];
omega-pullback defect R^T M R - M; metric-pullback defect; Omega scale det U;
su(3) Lie-algebra real dimension; SU(2)-subgroup induced SO(3) rotation)
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
from e3nn import o3

CDTYPE = torch.complex128
RTYPE = torch.float64
TOL = 1.0e-9            # tolerance for "match" on direct float64 numeric invariants
TOL_E3NN = 1.0e-5      # e3nn matrix/angle round-trip (float-precision floor)
TOL_SMT = 1.0e-9       # SMT orthogonality/commute certificate tolerance
SAMPLE_SIZES = [6, 12, 24, 48]
SEEDS = [0, 1, 2, 3, 4]
ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "gstruct_su3_calabi_yau_deep_probe"

# Pauli matrices (exact, complex128) -- used for the SU(2) subset SU(3) double cover.
SX = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
PAULI = (SX, SY, SZ)


# --------------------------------------------------------------------------- #
# Standard SU(3)-structure objects on C^3 ~ R^6 (torch, load-bearing)         #
# --------------------------------------------------------------------------- #
def complex_structure_J() -> torch.Tensor:
    """Standard J on R^6 with coordinate order (x1,y1,x2,y2,x3,y3):
    J e_{x_k} = e_{y_k}, J e_{y_k} = -e_{x_k}  => J^2 = -I."""
    J = torch.zeros((6, 6), dtype=RTYPE)
    for k in range(3):
        J[2 * k + 1, 2 * k] = 1.0      # x_k -> y_k
        J[2 * k, 2 * k + 1] = -1.0     # y_k -> -x_k
    return J


def euclidean_metric() -> torch.Tensor:
    return torch.eye(6, dtype=RTYPE)


def kahler_form_matrix(J: torch.Tensor, g: torch.Tensor) -> torch.Tensor:
    """omega(u,v) = g(Ju, v) = u^T (J^T g) v  =>  matrix M = J^T g."""
    return J.T @ g


def real_embed_su3(U: torch.Tensor) -> torch.Tensor:
    """Real 6x6 embedding of a complex-linear map U in C^{3x3} acting on
    z = x + i y, in coordinate order (x1,y1,x2,y2,x3,y3). For entry (i,j) of U
    with U = A + iB the 2x2 real block is [[A,-B],[B,A]]."""
    A = U.real
    B = U.imag
    R = torch.zeros((6, 6), dtype=RTYPE)
    for i in range(3):
        for j in range(3):
            R[2 * i, 2 * j] = A[i, j]
            R[2 * i, 2 * j + 1] = -B[i, j]
            R[2 * i + 1, 2 * j] = B[i, j]
            R[2 * i + 1, 2 * j + 1] = A[i, j]
    return R


def haar_su3(gen: torch.Generator) -> torch.Tensor:
    """Haar-random SU(3) element: QR of a complex-Gaussian 3x3 gives a Haar U(3)
    element; dividing by the cube root of its determinant phase normalizes
    det -> 1 (genuine SU(3), real math, no hand-built label matrix)."""
    re = torch.randn(3, 3, generator=gen, dtype=RTYPE)
    im = torch.randn(3, 3, generator=gen, dtype=RTYPE)
    a = (re + 1j * im).to(CDTYPE)
    q, r = torch.linalg.qr(a)
    ph = torch.diagonal(r)
    ph = ph / ph.abs()
    q = q * ph.unsqueeze(0)          # genuine Haar U(3)
    d = torch.linalg.det(q)
    cube_root_phase = (d / d.abs()) ** (1.0 / 3.0)
    return q / cube_root_phase       # det -> 1: SU(3)


def holomorphic_volume(frame: torch.Tensor) -> torch.Tensor:
    """Omega(v1,v2,v3) = det[v1|v2|v3] for the (3,0)-form dz1^dz2^dz3 on a
    complex frame (columns are the three vectors in C^3)."""
    return torch.linalg.det(frame)


def su3_lie_algebra_dimension(gen: torch.Generator, n_samples: int = 60) -> int:
    """Real dimension of su(3) = {traceless anti-Hermitian 3x3}. Sample many such
    matrices, real-vectorize, and take the rank of their span. Known value: 8."""
    vecs = []
    for _ in range(n_samples):
        a = (torch.randn(3, 3, generator=gen, dtype=RTYPE)
             + 1j * torch.randn(3, 3, generator=gen, dtype=RTYPE)).to(CDTYPE)
        X = a - a.conj().T                                  # anti-Hermitian
        X = X - (torch.trace(X) / 3.0) * torch.eye(3, dtype=CDTYPE)   # traceless
        vecs.append(torch.cat([X.real.flatten(), X.imag.flatten()]))
    span = torch.stack(vecs).to(RTYPE)
    return int(torch.linalg.matrix_rank(span).item())


def su2_in_su3(theta: float, axis: int = 1) -> torch.Tensor:
    """SU(2) element exp(-i theta/2 sigma_axis) embedded as the upper-left 2x2
    block of an SU(3) element (det of the block is 1, so det U3 = 1)."""
    U2 = torch.linalg.matrix_exp(-1j * theta / 2.0 * PAULI[axis])
    U3 = torch.eye(3, dtype=CDTYPE)
    U3[:2, :2] = U2
    return U3, U2


def su2_induced_so3(U2: torch.Tensor) -> torch.Tensor:
    """The 3x3 real matrix R with U2 sigma_j U2^dag = sum_i R_ij sigma_i:
    the SU(2) -> SO(3) double cover acting on the C^2 sub-block of C^3."""
    R = torch.zeros((3, 3), dtype=RTYPE)
    for j, sj in enumerate(PAULI):
        conj = U2 @ sj @ U2.conj().T
        for i, si in enumerate(PAULI):
            R[i, j] = (torch.trace(si @ conj).real) / 2
    return R


# --------------------------------------------------------------------------- #
# sympy: EXACT symbolic proofs (J^2=-I, omega antisymmetry, Omega det pullback)#
# --------------------------------------------------------------------------- #
def sympy_structure_exact() -> dict[str, Any]:
    # J on a single C-factor R^2: [[0,-1],[1,0]] -> block-diag over 3 factors.
    J2 = sp.Matrix([[0, -1], [1, 0]])
    J = sp.diag(J2, J2, J2)
    J_sq_is_minus_I = sp.simplify(J * J + sp.eye(6)) == sp.zeros(6, 6)

    g = sp.eye(6)
    M = J.T * g                       # omega matrix
    omega_antisym = sp.simplify(M + M.T) == sp.zeros(6, 6)
    omega_nondegenerate = sp.simplify(sp.det(M)) != 0
    det_omega = sp.simplify(sp.det(M))

    # metric compatibility g(Ju,Jv) = g(u,v)  <=>  J^T g J = g
    metric_compat = sp.simplify(J.T * g * J - g) == sp.zeros(6, 6)

    # omega(u,v) = g(Ju,v) on symbolic vectors u,v
    u = sp.Matrix(sp.symbols("u0:6", real=True))
    v = sp.Matrix(sp.symbols("v0:6", real=True))
    omega_uv = (u.T * M * v)[0]
    g_Ju_v = ((J * u).T * g * v)[0]
    omega_eq_gJv = sp.simplify(omega_uv - g_Ju_v) == 0

    # Omega(Uv) = det(U) Omega(v): symbolic 3x3 U and frame V, det(U V)=det U det V
    Uent = sp.symbols("U0:9")
    U = sp.Matrix(3, 3, Uent)
    Vent = sp.symbols("V0:9")
    V = sp.Matrix(3, 3, Vent)
    det_pullback = sp.simplify(sp.det(U * V) - sp.det(U) * sp.det(V)) == 0

    return {
        "J_squared_equals_minus_I_exact": bool(J_sq_is_minus_I),
        "omega_antisymmetric_exact": bool(omega_antisym),
        "omega_nondegenerate_exact": bool(omega_nondegenerate),
        "det_omega_exact": str(det_omega),
        "metric_compatibility_exact": bool(metric_compat),
        "omega_equals_g_J_dot_exact": bool(omega_eq_gJv),
        "omega_det_pullback_exact": bool(det_pullback),
    }


# --------------------------------------------------------------------------- #
# z3 / cvc5: certify R is orthogonal (R^T R = I) AND commutes with J          #
# --------------------------------------------------------------------------- #
def z3_so6_commute_J_certificate(R: torch.Tensor, J: torch.Tensor) -> dict[str, Any]:
    """Certify the real embedding R is in SO(6) (orthogonal) AND [R, J] = 0
    (complex-linear). The carrier numbers are float64; the certified structural
    statement is orthogonality + commutation up to TOL_SMT. We feed R, J to z3
    and check the NEGATION is UNSAT. Removing z3 removes this certificate."""
    s = z3.Solver()
    Rv = [[z3.Real(f"r{i}{j}") for j in range(6)] for i in range(6)]
    Jv = [[z3.RealVal(repr(float(J[i, j]))) for j in range(6)] for i in range(6)]
    tol = z3.RealVal(repr(TOL_SMT))
    for i in range(6):
        for j in range(6):
            s.add(Rv[i][j] == z3.RealVal(repr(float(R[i, j]))))
    conds = []
    # orthogonality: (R^T R)_{ij} == delta_{ij}
    for i in range(6):
        for j in range(6):
            e = z3.Sum([Rv[k][i] * Rv[k][j] for k in range(6)])
            tgt = z3.RealVal(1) if i == j else z3.RealVal(0)
            conds.append(z3.And(e - tgt <= tol, e - tgt >= -tol))
    # commute with J: (RJ - JR)_{ij} == 0
    for i in range(6):
        for j in range(6):
            rj = z3.Sum([Rv[i][k] * Jv[k][j] for k in range(6)])
            jr = z3.Sum([Jv[i][k] * Rv[k][j] for k in range(6)])
            conds.append(z3.And(rj - jr <= tol, rj - jr >= -tol))
    s.add(z3.Not(z3.And(conds)))
    status = str(s.check())
    return {"negation_status": status, "pass": status == "unsat"}


def cvc5_so6_commute_J_certificate(R: torch.Tensor, J: torch.Tensor) -> dict[str, Any]:
    """Independent SMT family (cvc5, QF_NRA) certifying the same fact:
    R orthogonal AND [R,J]=0; the negation is UNSAT."""
    slv = cvc5.Solver()
    slv.setOption("produce-models", "false")
    slv.setLogic("QF_NRA")
    Rsort = slv.getRealSort()

    def rv(x: float):
        frac = sp.Rational(x).limit_denominator(10 ** 12)
        num, den = frac.p, frac.q
        return slv.mkReal(int(num), int(den)) if int(den) != 1 else slv.mkReal(int(num))

    Rc = [[slv.mkConst(Rsort, f"r{i}{j}") for j in range(6)] for i in range(6)]
    for i in range(6):
        for j in range(6):
            slv.assertFormula(slv.mkTerm(Kind.EQUAL, Rc[i][j], rv(float(R[i, j]))))
    Jc = [[rv(float(J[i, j])) for j in range(6)] for i in range(6)]
    zero = slv.mkReal(0)
    tol = rv(TOL_SMT)
    neg_tol = slv.mkTerm(Kind.SUB, zero, tol)

    def within(term):
        lo = slv.mkTerm(Kind.GEQ, term, neg_tol)
        hi = slv.mkTerm(Kind.LEQ, term, tol)
        return slv.mkTerm(Kind.AND, lo, hi)

    conds = []
    # orthogonality
    for i in range(6):
        for j in range(6):
            prods = [slv.mkTerm(Kind.MULT, Rc[k][i], Rc[k][j]) for k in range(6)]
            e = slv.mkTerm(Kind.ADD, *prods)
            tgt = slv.mkReal(1) if i == j else slv.mkReal(0)
            conds.append(within(slv.mkTerm(Kind.SUB, e, tgt)))
    # commute with J
    for i in range(6):
        for j in range(6):
            rj_terms = [slv.mkTerm(Kind.MULT, Rc[i][k], Jc[k][j]) for k in range(6)]
            jr_terms = [slv.mkTerm(Kind.MULT, Jc[i][k], Rc[k][j]) for k in range(6)]
            rj = slv.mkTerm(Kind.ADD, *rj_terms)
            jr = slv.mkTerm(Kind.ADD, *jr_terms)
            conds.append(within(slv.mkTerm(Kind.SUB, rj, jr)))
    big = slv.mkTerm(Kind.AND, *conds)
    slv.assertFormula(slv.mkTerm(Kind.NOT, big))
    res = slv.checkSat()
    status = "unsat" if res.isUnsat() else ("sat" if res.isSat() else "unknown")
    return {"negation_status": status, "pass": res.isUnsat()}


# --------------------------------------------------------------------------- #
# e3nn: SU(2) subset SU(3) induced SO(3) double cover                          #
# --------------------------------------------------------------------------- #
def e3nn_is_so3(R: torch.Tensor) -> dict[str, Any]:
    """Certify R is a genuine SO(3) element using e3nn: det==1, R R^T == I,
    matrix_to_angles -> angles_to_matrix round-trip, and Wigner-D l=1
    reconstruction."""
    Rf = R.to(torch.float64)
    det = float(torch.det(Rf).item())
    orth = float(torch.linalg.matrix_norm(Rf @ Rf.T - torch.eye(3, dtype=RTYPE)).item())
    if abs(det - 1.0) >= TOL_E3NN or orth >= TOL_E3NN:
        return {"det": det, "orthogonality_defect": orth, "e3nn_reconstruction_err": None,
                "wigner_d_det": None, "e3nn_rejected_non_so3": True, "pass": False}
    a, b, c = o3.matrix_to_angles(Rf)
    Rrec = o3.angles_to_matrix(a, b, c)
    recon_err = float(torch.linalg.matrix_norm(Rrec - Rf).item())
    D = o3.wigner_D(1, a, b, c)
    wig_det = float(torch.det(D).item())
    return {
        "det": det, "orthogonality_defect": orth, "e3nn_reconstruction_err": recon_err,
        "wigner_d_det": wig_det, "e3nn_rejected_non_so3": False,
        "pass": (abs(det - 1.0) < TOL_E3NN and orth < TOL_E3NN
                 and recon_err < TOL_E3NN and abs(wig_det - 1.0) < TOL_E3NN),
    }


# --------------------------------------------------------------------------- #
# Wide-variation sampling over sizes / seeds                                  #
# --------------------------------------------------------------------------- #
def sample_block(n_elems: int, seed: int, J: torch.Tensor, g: torch.Tensor,
                 M: torch.Tensor) -> dict[str, Any]:
    gen = torch.Generator().manual_seed(seed)
    Us = [haar_su3(gen) for _ in range(n_elems)]
    Rs = [real_embed_su3(U) for U in Us]
    I3 = torch.eye(3, dtype=CDTYPE)
    I6 = torch.eye(6, dtype=RTYPE)

    unitary_defects = [float(torch.linalg.matrix_norm(U @ U.conj().T - I3).item()) for U in Us]
    det_defects = [abs(complex(torch.linalg.det(U)) - 1.0) for U in Us]
    so6_defects = [float(torch.linalg.matrix_norm(R.T @ R - I6).item()) for R in Rs]
    detR_defects = [abs(float(torch.linalg.det(R)) - 1.0) for R in Rs]
    commute_J = [float(torch.linalg.matrix_norm(R @ J - J @ R).item()) for R in Rs]
    preserve_omega = [float(torch.linalg.matrix_norm(R.T @ M @ R - M).item()) for R in Rs]
    preserve_g = [float(torch.linalg.matrix_norm(R.T @ g @ R - g).item()) for R in Rs]

    # Omega fixed: Omega(Uv)/Omega(v) = det U = 1 over random frames
    omega_scale_defects = []
    for U in Us:
        V = (torch.randn(3, 3, generator=gen, dtype=RTYPE)
             + 1j * torch.randn(3, 3, generator=gen, dtype=RTYPE)).to(CDTYPE)
        before = holomorphic_volume(V)
        after = holomorphic_volume(U @ V)
        omega_scale_defects.append(abs(complex(after / before) - 1.0))

    return {
        "n_elems": n_elems, "seed": seed,
        "max_unitary_defect": max(unitary_defects),
        "max_det1_defect": max(det_defects),
        "max_so6_orthogonality_defect": max(so6_defects),
        "max_detR1_defect": max(detR_defects),
        "max_commute_J_defect": max(commute_J),
        "max_preserve_omega_defect": max(preserve_omega),
        "max_preserve_g_defect": max(preserve_g),
        "max_omega_scale_defect": max(omega_scale_defects),
    }


# --------------------------------------------------------------------------- #
# Negatives (must break the SU(3)-structure)                                  #
# --------------------------------------------------------------------------- #
def negative_bad_complex_structure() -> dict[str, Any]:
    """J0 = I has J0^2 = I != -I: not a complex structure."""
    J0 = torch.eye(6, dtype=RTYPE)
    defect = float(torch.linalg.matrix_norm(J0 @ J0 + torch.eye(6, dtype=RTYPE)).item())
    return {"J0_squared_plus_I_norm": defect, "is_not_complex_structure": defect > 1.0}


def negative_u3_scales_omega() -> dict[str, Any]:
    """A U(3) element with det != 1 SCALES Omega by det U: it preserves J, g, omega
    but is NOT in SU(3) because it does not fix Omega."""
    gen = torch.Generator().manual_seed(99)
    U = haar_su3(gen)
    phase = torch.exp(torch.tensor(0.7j, dtype=CDTYPE))
    Uu = torch.diag(torch.tensor([phase, 1, 1], dtype=CDTYPE)) @ U   # det = phase != 1
    detU = complex(torch.linalg.det(Uu))
    V = (torch.randn(3, 3, generator=gen, dtype=RTYPE)
         + 1j * torch.randn(3, 3, generator=gen, dtype=RTYPE)).to(CDTYPE)
    scale = complex(holomorphic_volume(Uu @ V) / holomorphic_volume(V))
    # still in U(3): real embedding commutes with J and preserves omega
    J = complex_structure_J()
    M = kahler_form_matrix(J, euclidean_metric())
    R = real_embed_su3(Uu)
    commute = float(torch.linalg.matrix_norm(R @ J - J @ R).item())
    return {
        "det_U": [detU.real, detU.imag],
        "omega_scale": [scale.real, scale.imag],
        "scale_equals_detU": abs(scale - detU) < TOL,
        "scale_not_one": abs(scale - 1.0) > 0.1,
        "still_commutes_with_J": commute < TOL,        # in U(3) but not SU(3)
        "kills_su3": abs(scale - 1.0) > 0.1 and commute < TOL,
    }


def negative_o6_not_complex_linear() -> dict[str, Any]:
    """A generic O(6) rotation that does NOT commute with J is not complex-linear
    (not in U(3)/SU(3)): it mixes the holomorphic and antiholomorphic directions."""
    gen = torch.Generator().manual_seed(123)
    a = torch.randn(6, 6, generator=gen, dtype=RTYPE)
    q, _ = torch.linalg.qr(a)
    if torch.det(q) < 0:
        q[:, 0] = -q[:, 0]                              # ensure SO(6)
    J = complex_structure_J()
    commute = float(torch.linalg.matrix_norm(q @ J - J @ q).item())
    so6 = float(torch.linalg.matrix_norm(q.T @ q - torch.eye(6, dtype=RTYPE)).item())
    return {
        "in_SO6": so6 < TOL,
        "commute_with_J_defect": commute,
        "does_not_commute_with_J": commute > 1e-3,
        "kills_complex_linearity": so6 < TOL and commute > 1e-3,
    }


def negative_dimension_flatten() -> dict[str, Any]:
    """A 1-parameter U(1) subgroup {exp(i t H)} has Lie-algebra dimension 1, far
    below dim SU(3) = 8: a reduced structure group cannot be the full SU(3)."""
    gen = torch.Generator().manual_seed(55)
    # one fixed traceless Hermitian generator H -> the abelian subgroup it spans
    H = torch.tensor([[1.0, 0, 0], [0, -1.0, 0], [0, 0, 0]], dtype=CDTYPE)  # traceless
    vecs = []
    for t in torch.linspace(0.1, 3.0, 30):
        X = 1j * float(t) * H                            # element of the 1-dim algebra
        X = X - (torch.trace(X) / 3.0) * torch.eye(3, dtype=CDTYPE)
        vecs.append(torch.cat([X.real.flatten(), X.imag.flatten()]))
    dim = int(torch.linalg.matrix_rank(torch.stack(vecs).to(RTYPE)).item())
    return {"u1_subalgebra_dim": dim, "is_below_su3_dim": dim < 8, "su3_dim": 8}


# --------------------------------------------------------------------------- #
# Known-value cross-checks                                                     #
# --------------------------------------------------------------------------- #
def known_value_checks(blocks: list[dict[str, Any]], sym: dict[str, Any],
                       J: torch.Tensor, g: torch.Tensor, M: torch.Tensor,
                       dim_su3: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    max_unitary = max(b["max_unitary_defect"] for b in blocks)
    max_det1 = max(b["max_det1_defect"] for b in blocks)
    max_so6 = max(b["max_so6_orthogonality_defect"] for b in blocks)
    max_detR = max(b["max_detR1_defect"] for b in blocks)
    max_comm = max(b["max_commute_J_defect"] for b in blocks)
    max_omega = max(b["max_preserve_omega_defect"] for b in blocks)
    max_g = max(b["max_preserve_g_defect"] for b in blocks)
    max_omega_scale = max(b["max_omega_scale_defect"] for b in blocks)

    # J^2 = -I numeric
    j_sq_defect = float(torch.linalg.matrix_norm(J @ J + torch.eye(6, dtype=RTYPE)).item())
    # omega antisymmetric numeric
    omega_antisym_defect = float(torch.linalg.matrix_norm(M + M.T).item())
    # omega nondegenerate: det == 1
    det_omega = float(torch.linalg.det(M).item())
    # omega(u,v) == g(Ju, v) over many random vectors
    gen = torch.Generator().manual_seed(2024)
    om_eq_defects = []
    for _ in range(200):
        u = torch.randn(6, generator=gen, dtype=RTYPE)
        v = torch.randn(6, generator=gen, dtype=RTYPE)
        om = float(u @ M @ v)
        gjv = float((J @ u) @ g @ v)
        om_eq_defects.append(abs(om - gjv))
    max_om_eq = max(om_eq_defects)
    # metric compatibility g(Ju,Jv)==g(u,v): J^T g J == g
    metric_compat_defect = float(torch.linalg.matrix_norm(J.T @ g @ J - g).item())
    # Omega nowhere zero on a frame: |det(I3)| = 1 > 0 (and random frames nonzero)
    frame_dets = [abs(complex(holomorphic_volume(
        (torch.randn(3, 3, generator=gen, dtype=RTYPE)
         + 1j * torch.randn(3, 3, generator=gen, dtype=RTYPE)).to(CDTYPE))))
        for _ in range(50)]
    omega_min_frame = min(frame_dets)
    omega_standard_frame = abs(complex(holomorphic_volume(torch.eye(3, dtype=CDTYPE))))

    # SU(2) subset SU(3): induced SO(3) double cover, e3nn-certified, angle sweep
    theta = 2.0 * math.pi / 3.0
    U3, U2 = su2_in_su3(theta)
    su2_block_det = abs(complex(torch.linalg.det(U3)) - 1.0)
    R3 = su2_induced_so3(U2)
    rot_angle = math.acos(max(-1.0, min(1.0, (float(torch.trace(R3).item()) - 1.0) / 2.0)))
    e3 = e3nn_is_so3(R3)

    checks = [
        {"invariant": "J^2 == -I (numeric torch)", "computed": f"||J^2 + I|| = {j_sq_defect:.2e}",
         "known": "0", "match": j_sq_defect < TOL},
        {"invariant": "J^2 == -I (EXACT symbolic, sympy)", "computed": str(sym["J_squared_equals_minus_I_exact"]),
         "known": "True", "match": bool(sym["J_squared_equals_minus_I_exact"])},
        {"invariant": "omega antisymmetric (numeric, M + M^T)", "computed": f"||M + M^T|| = {omega_antisym_defect:.2e}",
         "known": "0", "match": omega_antisym_defect < TOL},
        {"invariant": "omega antisymmetric (EXACT symbolic, sympy)", "computed": str(sym["omega_antisymmetric_exact"]),
         "known": "True", "match": bool(sym["omega_antisymmetric_exact"])},
        {"invariant": "omega nondegenerate det(omega)", "computed": f"{det_omega:.15f}",
         "known": "1", "match": abs(det_omega - 1.0) < TOL},
        {"invariant": "omega(u,v) == g(Ju,v) (numeric, 200 vectors)", "computed": f"max defect {max_om_eq:.2e}",
         "known": "0", "match": max_om_eq < TOL},
        {"invariant": "omega(u,v) == g(Ju,v) (EXACT symbolic, sympy)", "computed": str(sym["omega_equals_g_J_dot_exact"]),
         "known": "True", "match": bool(sym["omega_equals_g_J_dot_exact"])},
        {"invariant": "metric compatibility g(Ju,Jv)==g(u,v) (J^T g J == g)", "computed": f"defect {metric_compat_defect:.2e}",
         "known": "0", "match": metric_compat_defect < TOL},
        {"invariant": "metric compatibility (EXACT symbolic, sympy)", "computed": str(sym["metric_compatibility_exact"]),
         "known": "True", "match": bool(sym["metric_compatibility_exact"])},
        {"invariant": "SU(3) unitary U U^dag == I (Haar sweep)", "computed": f"max defect {max_unitary:.2e}",
         "known": "0", "match": max_unitary < TOL},
        {"invariant": "SU(3) det U == 1 (Haar sweep)", "computed": f"max |det-1| {max_det1:.2e}",
         "known": "1", "match": max_det1 < TOL},
        {"invariant": "dim SU(3) (real dim of su(3), rank of span)", "computed": str(dim_su3),
         "known": "8", "match": dim_su3 == 8},
        {"invariant": "SU(3) subset SO(6): R^T R == I (Haar sweep)", "computed": f"max defect {max_so6:.2e}",
         "known": "0", "match": max_so6 < TOL},
        {"invariant": "SU(3) subset SO(6): det R == 1 (Haar sweep)", "computed": f"max |detR-1| {max_detR:.2e}",
         "known": "1", "match": max_detR < TOL},
        {"invariant": "SU(3) commutes with J: R J == J R (Haar sweep)", "computed": f"max defect {max_comm:.2e}",
         "known": "0", "match": max_comm < TOL},
        {"invariant": "SU(3) preserves omega: R^T M R == M (Haar sweep)", "computed": f"max defect {max_omega:.2e}",
         "known": "0", "match": max_omega < TOL},
        {"invariant": "SU(3) preserves g: R^T g R == g (Haar sweep)", "computed": f"max defect {max_g:.2e}",
         "known": "0", "match": max_g < TOL},
        {"invariant": "SU(3) fixes Omega: Omega(Uv)/Omega(v) == det U == 1 (Haar sweep)", "computed": f"max |scale-1| {max_omega_scale:.2e}",
         "known": "1", "match": max_omega_scale < TOL},
        {"invariant": "Omega det-pullback Omega(Uv)=det(U)Omega(v) (EXACT symbolic, sympy)", "computed": str(sym["omega_det_pullback_exact"]),
         "known": "True", "match": bool(sym["omega_det_pullback_exact"])},
        {"invariant": "Omega nowhere zero on a frame (min |det frame|)", "computed": f"min {omega_min_frame:.3e}, standard frame {omega_standard_frame:.3f}",
         "known": ">0 (nonvanishing)", "match": omega_min_frame > TOL and abs(omega_standard_frame - 1.0) < TOL},
        {"invariant": "SU(2) subset SU(3) block det == 1", "computed": f"|det-1| {su2_block_det:.2e}",
         "known": "1", "match": su2_block_det < TOL},
        {"invariant": "SU(2) subset SU(3) induced rotation angle (theta=2pi/3)", "computed": f"{rot_angle:.15f}",
         "known": f"{theta:.15f}", "match": abs(rot_angle - theta) < 1e-7},
        {"invariant": "e3nn certifies SU(2)-induced rotation in SO(3) (Wigner-D l=1)", "computed": f"det={e3['det']:.6f}, orth={e3['orthogonality_defect']:.2e}, recon={e3['e3nn_reconstruction_err']}, wignerD_det={e3['wigner_d_det']}",
         "known": "det=1, orthogonal, reconstructs (genuine SO(3))", "match": e3["pass"]},
    ]
    aux = {
        "j_squared_defect": j_sq_defect,
        "omega_antisym_defect": omega_antisym_defect,
        "det_omega": det_omega,
        "omega_eq_gJv_max_defect": max_om_eq,
        "metric_compat_defect": metric_compat_defect,
        "omega_min_frame_det": omega_min_frame,
        "omega_standard_frame_det": omega_standard_frame,
        "su2_induced_so3_matrix": [[float(x) for x in row] for row in R3],
        "su2_induced_rotation_angle": rot_angle,
        "e3nn_so3_check": e3,
        "su3_lie_algebra_dimension": dim_su3,
    }
    return checks, aux


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    J = complex_structure_J()
    g = euclidean_metric()
    M = kahler_form_matrix(J, g)

    # Wide variation: sizes x seeds.
    blocks = [sample_block(n, seed, J, g, M) for n in SAMPLE_SIZES for seed in SEEDS]

    # su(3) Lie algebra real dimension.
    dim_su3 = su3_lie_algebra_dimension(torch.Generator().manual_seed(7))

    # sympy exact structure proofs.
    sym = sympy_structure_exact()

    # known-value cross-checks (the depth proof).
    kvc, kvc_aux = known_value_checks(blocks, sym, J, g, M, dim_su3)

    # z3 + cvc5 SO(6)+commute-J certificates over a sweep of sampled SU(3) elements.
    gen = torch.Generator().manual_seed(4321)
    cert_Us = [haar_su3(gen) for _ in range(6)]
    cert_Us.append(torch.eye(3, dtype=CDTYPE))                  # identity in SU(3)
    cert_Rs = [real_embed_su3(U) for U in cert_Us]
    z3_rows = [z3_so6_commute_J_certificate(R, J) for R in cert_Rs]
    cvc5_rows = [cvc5_so6_commute_J_certificate(R, J) for R in cert_Rs]
    z3_pass = all(r["pass"] for r in z3_rows)
    cvc5_pass = all(r["pass"] for r in cvc5_rows)

    # Negatives.
    neg_badJ = negative_bad_complex_structure()
    neg_u3 = negative_u3_scales_omega()
    neg_o6 = negative_o6_not_complex_linear()
    neg_dim = negative_dimension_flatten()
    negatives = {
        "bad_complex_structure_J": {"detail": neg_badJ, "kills_signature": neg_badJ["is_not_complex_structure"]},
        "u3_element_scales_Omega": {"detail": neg_u3, "kills_signature": neg_u3["kills_su3"]},
        "o6_not_complex_linear": {"detail": neg_o6, "kills_signature": neg_o6["kills_complex_linearity"]},
        "dimension_flatten_u1_subgroup": {"detail": neg_dim, "kills_signature": neg_dim["is_below_su3_dim"]},
    }

    known_values_all_match = all(c["match"] for c in kvc)
    negatives_all_kill = all(v["kills_signature"] for v in negatives.values())
    tools_all_pass = (z3_pass and cvc5_pass
                      and sym["J_squared_equals_minus_I_exact"]
                      and sym["omega_antisymmetric_exact"]
                      and sym["omega_equals_g_J_dot_exact"]
                      and sym["omega_det_pullback_exact"]
                      and kvc_aux["e3nn_so3_check"]["pass"])

    all_pass = known_values_all_match and negatives_all_kill and tools_all_pass

    blockers: list[str] = []
    if not known_values_all_match:
        blockers += [f"KNOWN-VALUE MISMATCH: {c['invariant']} computed={c['computed']} known={c['known']}"
                     for c in kvc if not c["match"]]
    if not z3_pass:
        blockers.append("z3 SO(6)+commute-J negation not UNSAT for all sampled SU(3) embeddings")
    if not cvc5_pass:
        blockers.append("cvc5 SO(6)+commute-J negation not UNSAT for all sampled SU(3) embeddings")
    if not negatives_all_kill:
        blockers += [f"NEGATIVE DID NOT KILL: {k}" for k, v in negatives.items() if not v["kills_signature"]]

    tool_manifest = {
        "torch": {"used": True, "role": "load_bearing",
                  "reason": "all SU(3)/SO(6)/J/g/omega/Omega algebra in complex128/float64 (Haar SU(3) sampling, real 6x6 embedding, commutator, omega/metric pullbacks, holomorphic-volume det, su(3) Lie-algebra rank); negatives kill the structure numerically"},
        "sympy": {"used": True, "role": "load_bearing",
                  "reason": "EXACT symbolic proofs J^2=-I, omega(u,v)=g(Ju,v) and antisymmetry, metric compatibility J^T g J = g, and Omega det-pullback Omega(Uv)=det(U)Omega(v); numeric torch alone cannot prove these exact identities"},
        "z3": {"used": True, "role": "load_bearing",
               "reason": "SMT certificate that each sampled real 6x6 embedding R is orthogonal (R^T R = I) AND commutes with J (R J = J R); the negation is UNSAT"},
        "cvc5": {"used": True, "role": "load_bearing",
                 "reason": "independent SMT family (QF_NRA) certifying the same orthogonal + commute-with-J fact; negation UNSAT"},
        "e3nn": {"used": True, "role": "load_bearing",
                 "reason": "certifies the SU(2) subset SU(3) induced 3x3 rotation is a genuine SO(3) element via matrix_to_angles round-trip and Wigner-D l=1 reconstruction (the double cover inside SU(3))"},
    }

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID, "name": SIM_ID, "version": "1.0.0", "tier": "2_geometry",
        "classification": "diagnostic_only",
        "promotion_allowed": False,
        "promotion_status": "diagnostic_only",
        "sim_execution_kind": "nonclassical",
        "sim_class": "geometry_probe",
        "purpose": "Deep, standalone SU(3) / Calabi-Yau-like G-structure lego on C^3 ~ R^6 (the support/compatibility lattice of (J, g, omega, Omega)) computed in real torch with full tool integration, cross-checked against textbook analytic invariants. Lego/pre-sim phase: NOT gated on manifold membership.",
        "scientific_question": "Does the standard SU(3)-structure (J^2=-I, compatible metric g, Kahler form omega=g(J.,.), holomorphic volume Omega) on C^3~R^6 reproduce its known invariants -- SU(3) unitary det-1, dim 8, embedded in SO(6), commuting with J, preserving omega/g/Omega -- to their exact analytic values, and do the broken-structure controls (bad J, det!=1, non-complex-linear O(6), reduced subgroup) kill that structure?",
        "claim_ceiling": "diagnostic_only / hypothetical / unadmitted: a self-contained known-math G-structure lego. Does NOT admit any manifold layer, stacking, coupling, Axis0, flux, bridge, QIT, or physics claim.",
        "finite_map": "(Haar SU(3) element U in C^{3x3}) -> (real SO(6) embedding R; commutator [R,J]; omega-pullback defect R^T M R - M; metric-pullback defect R^T g R - g; holomorphic-volume scale Omega(Uv)/Omega(v)=det U; su(3) Lie-algebra real dimension; SU(2)-subgroup induced SO(3) rotation)",
        "domain": "Haar-sampled SU(3) elements (complex-Gaussian QR with det normalization); the structure tensors J, g, omega(matrix M) on R^6; Pauli set for the SU(2) subset SU(3) double cover; symbolic 3x3/6x6 matrices for the exact sympy proofs",
        "codomain_or_output": "real 6x6 SO(6) embeddings R; commutators, omega/metric/Omega pullback defects; the integer dim su(3); the induced SO(3) rotation of the SU(2) subgroup; SMT UNSAT certificates",
        "carrier_layer": "C^3 ~ R^6 with the standard SU(3)-structure (complex structure J, Euclidean metric g, Kahler 2-form omega, holomorphic (3,0)-form Omega)",
        "geometry_layer": "SU(3)-structure / Calabi-Yau-like compatibility lattice: SU(3) = U(3) cap SL(3,C) = Stab(J) cap Stab(g) cap Stab(Omega) acting on R^6 inside SO(6)",
        "carrier_realization": "torch.complex128 / torch.float64 SU(3) elements, real 6x6 embeddings, and structure tensors; no NumPy claim-bearing substrate, no label-only tensors, no random claim matrices (random SU(3) elements are genuine Haar samples)",
        "spinor_state": "not_applicable_at_lego_phase (G-structure / frame-bundle lego; the SU(2) subset SU(3) double cover is realized via Pauli operators, not an admitted spinor density)",
        "quaternion_action": "the SU(2) subset SU(3) subgroup (== unit quaternions) acts on the upper C^2 block; its induced SO(3) double-cover rotation is e3nn-certified",
        "peps3d_embedding": "not_applicable_at_lego_phase (no manifold anchor claimed; diagnostic_only)",
        "dependency_receipts": [],
        "downstream_blocks": ["manifold_layers", "stacking", "coupling", "G_structure_admission", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "blocked_consumers": ["manifold_layers", "stacking", "coupling", "G_structure_admission", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "law_or_candidate_tested": "standard SU(3) / Calabi-Yau-like G-structure on C^3~R^6 against textbook analytic invariants (J^2=-I, omega=g(J.,.), SU(3) unitary det-1 dim-8 subset SO(6) commuting with J and fixing omega/g/Omega)",
        "branch_status_before_run": "lego/pre-sim phase; standalone known-math G-structure; unadmitted",
        "allowed_claims": ["standalone known-math SU(3)/Calabi-Yau-structure geometry witness; computed invariants match textbook values to machine precision; broken-structure controls kill the structure"],
        "promotion_blockers": ["diagnostic_only by design (lego/pre-sim phase); no manifold membership, no cross-layer evidence, no coupling"],

        "result_summary": {
            "all_pass": all_pass,
            "known_values_all_match": known_values_all_match,
            "negatives_all_kill": negatives_all_kill,
            "tools_all_pass": tools_all_pass,
            "n_known_value_checks": len(kvc),
            "n_sampled_su3_elements": sum(b["n_elems"] for b in blocks),
            "sample_sizes": SAMPLE_SIZES, "seeds": SEEDS,
            "dim_su3": dim_su3,
            "z3_so6_commuteJ_all_unsat": z3_pass,
            "cvc5_so6_commuteJ_all_unsat": cvc5_pass,
            "promotion_allowed": False,
        },

        "known_value_checks": kvc,
        "known_value_aux": kvc_aux,
        "sympy_exact_structure": sym,

        "variation_blocks": blocks,

        "so6_commuteJ_certificates": {
            "z3": {"rows": z3_rows, "all_unsat": z3_pass, "n_elements_certified": len(cert_Rs)},
            "cvc5": {"rows": cvc5_rows, "all_unsat": cvc5_pass, "n_elements_certified": len(cert_Rs)},
        },

        "required_negatives": ["bad_complex_structure_J", "u3_element_scales_Omega", "o6_not_complex_linear", "dimension_flatten_u1_subgroup"],
        "negatives_run": list(negatives.keys()),
        "negatives": negatives,
        "kill_conditions": [
            "any known-value invariant fails to match its textbook value",
            "z3 or cvc5 SO(6)+commute-J negation not UNSAT",
            "bad complex structure J0^2 == -I (would mean it is a valid J)",
            "U(3) element with det != 1 fixes Omega (would mean it is in SU(3))",
            "generic O(6) rotation commutes with J (would mean it is complex-linear)",
            "U(1) subgroup has Lie-algebra dimension 8 (would mean it is full SU(3))",
        ],

        "TOOL_MANIFEST": tool_manifest,
        "tool_manifest": tool_manifest,
        "TOOL_INTEGRATION_DEPTH": {"torch": "load_bearing", "sympy": "load_bearing", "z3": "load_bearing",
                                   "cvc5": "load_bearing", "e3nn": "load_bearing"},
        "proof_surfaces_used": ["z3", "cvc5", "sympy"],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "required_tools": ["torch", "sympy", "z3", "cvc5", "e3nn"],
        "actual_tools_used": ["torch", "sympy", "z3", "cvc5", "e3nn"],

        "required_artifacts": ["json_result_receipt", "witness_trace"],
        "artifacts_emitted": ["json_result_receipt", "witness_trace"],
        "witness_trace_id": f"{SIM_ID}_witness",

        "all_pass": all_pass,
        "blockers": blockers,
        "pass_rule": "every known_value_check matches its known value AND all negatives kill the structure AND z3+cvc5 SO(6)+commute-J negations are UNSAT AND e3nn certifies the SU(2)-induced rotation in SO(3) AND all sympy exact proofs hold",
        "fail_rule": "any known-value mismatch, any negative that does not kill, any non-UNSAT certificate, any failed sympy exact proof, or e3nn rejecting the induced rotation",
        "eligible_consumers": ["other diagnostic_only G-structure / geometry probes"],
    }

    witness = {
        "sim_id": SIM_ID,
        "steps": [
            {"step": "build_su3_structure_tensors", "objects": ["J", "g", "omega(M)", "Omega(det)"]},
            {"step": "sample_haar_su3", "sizes": SAMPLE_SIZES, "seeds": SEEDS,
             "n_elements": sum(b["n_elems"] for b in blocks)},
            {"step": "real_embed_and_check_so6_commuteJ_preserve_omega_g_Omega", "tool": "torch.complex128/float64"},
            {"step": "su3_lie_algebra_dimension", "dim": dim_su3, "known": 8},
            {"step": "sympy_exact_J2_omega_metric_Omega_pullback",
             "J2": sym["J_squared_equals_minus_I_exact"],
             "omega_antisym": sym["omega_antisymmetric_exact"],
             "omega_eq_gJv": sym["omega_equals_g_J_dot_exact"],
             "omega_det_pullback": sym["omega_det_pullback_exact"]},
            {"step": "z3_so6_commuteJ_certificate", "all_unsat": z3_pass, "n": len(cert_Rs)},
            {"step": "cvc5_so6_commuteJ_certificate", "all_unsat": cvc5_pass, "n": len(cert_Rs)},
            {"step": "e3nn_su2_subset_su3_so3_certification", "pass": kvc_aux["e3nn_so3_check"]["pass"]},
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
        "dim_su3": dim_su3,
        "blockers": blockers,
        "known_value_checks": [{"invariant": c["invariant"], "computed": c["computed"],
                                "known": c["known"], "match": c["match"]} for c in kvc],
    }, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

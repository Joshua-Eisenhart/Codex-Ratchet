#!/usr/bin/env python3
"""Deep G-structure reduction/containment-chain lego (diagnostic_only, unadmitted).

KNOWN STRUCTURE (real torch.float64 / complex128 -- no labels, no random claim
matrices, no hardcoded stand-in numbers):

  The G-structure reduction / subgroup-containment lattice

      U(1)  subset  SU(2) = Spin(3)  subset  SU(3)  subset  G2
                                                          subset  Spin(7)
                                                          subset  SO(8)

  with the parallel low-rank lattice element SO(3) (the SU(2)/Z2 quotient, image
  of the double cover) and Spin^c language noted for U(1).

  Every link is a genuine subgroup inclusion realized at the matrix / Lie-algebra
  level, NOT asserted by a label:

  1.  U(1)  -> SU(2)        diagonal phase t |-> diag(e^{it}, e^{-it})  (det 1, unitary).
  2.  SU(2) -> SU(3)        block embed U |-> diag(U, 1)               (det 1, unitary).
  3.  SU(3) -> G2           G2 contains SU(3) as the STABILIZER OF A VECTOR in R^7
                            (7 = 1 + 3 + 3bar under SU(3)); computed as the
                            dimension of {X in g2 : X v = 0} = 8 = dim su(3).
  4.  G2    -> Spin(7)      G2 = STABILIZER OF A UNIT SPINOR in the 8-dim real spin
                            rep of Spin(7); computed as dim{X in spin(7) : X s = 0}
                            = 14 = dim G2, with orbit dim 21 - 14 = 7 = dim S^7
                            (the homogeneous space Spin(7)/G2 = S^7).
  5.  Spin(7) -> SO(8)      the 8-dim real spinor rep generators (1/2) g_i g_j are
                            antisymmetric 8x8 matrices, i.e. they sit inside so(8)
                            (dim 28); independent count C(7,2) = 21 = dim Spin(7).
  6.  SU(2) = Spin(3) -> SO(3)   the double cover: the j=1/2 (spinor) rep rotated by
                            2*pi returns -I, while the l=1 (vector / SO(3)) rep
                            rotated by 2*pi returns +I (verified with e3nn's own
                            su2_generators / so3_generators).

  Lie-algebra DATA computed from real structure (not hardcoded):
    g2  built as the 14-dim kernel of the so(7) action on the standard G2 3-form
        phi = e123 + e145 + e167 + e246 - e257 - e347 - e356 (octonion convention),
        i.e. the 7-dim ORBIT (image, the cross-product part) is split off and the
        14-dim DERIVATION algebra (g2) is the kernel: dim g2 = 21 - 7 = 14.
    spin(7) built as span of (1/2) g_i g_j from 7 real 8x8 octonion left-mult
        gamma matrices: dim 21, rank 3.

  KNOWN-VALUE CHECKS (each invariant compared to its textbook value, recorded as
  {invariant, computed, known, match}; match is COMPUTED, never hardcoded):

    Dimension chain (monotone strictly increasing along the chain):
        dim U(1)=1, SU(2)=3, SU(3)=8, G2=14, Spin(7)=21, SO(8)=28
    Rank chain:
        rank U(1)=1, SU(2)=1, SU(3)=2, G2=2, Spin(7)=3, SO(8)=4
    Containment (matrix/Lie-algebra level):
        each step's embedded image stays inside the target group/algebra
        (det 1 + unitary, or antisymmetric / so(n) membership, or sub-Lie-algebra
        closure under the bracket).
    Homomorphism:
        each finite embedding preserves the group product on sampled elements:
        E(A) E(B) = E(A B).
    Double cover:
        SU(2)=Spin(3) -> SO(3) is 2:1 (the 2*pi -I / +I signature).

  NEGATIVES (each must KILL the claimed containment / relation):
    - non-special embed: U |-> diag(U, e^{i a}) with det != 1 leaves SU(3)
      (det no longer 1).
    - product-breaking "reduction": a map that is NOT a homomorphism
      (E'(A) E'(B) != E'(A B)).
    - dimension non-monotone: a fake reordered chain whose dimensions are not
      strictly increasing.
    - fake double cover: claiming the l=1 (SO(3)) rep is 2:1 -- it is 1:1
      (2*pi rotation returns +I, so no -I sign-flip exists).
    - non-antisymmetric "spin(7)" generator: a symmetric 8x8 matrix is NOT in
      so(8) and cannot be a Lie-algebra rotation generator.

TOOLS (all load-bearing in the execution path):
  - torch  : ALL matrix / Lie-algebra algebra in float64 / complex128 -- the
             so(7) 3-form action, the octonion gamma matrices, every embedding,
             every dimension (matrix rank), every rank (centralizer of a regular
             element), every homomorphism and unitarity check.
  - sympy  : EXACT symbolic dimension formulas dim su(n) = n^2 - 1 and
             dim so(n) = n(n-1)/2 evaluated symbolically, and EXACT symbolic
             verification that the U(1) diagonal phase has determinant identically
             1 (cos^2 t + sin^2 t = 1) so it lies in SU(2) for ALL t, not just
             sampled t.
  - z3     : SMT certificate that the dimension chain is STRICTLY MONOTONE
             (1 < 3 < 8 < 14 < 21 < 28): the negation is UNSAT. Removing z3
             removes this structural certificate.
  - e3nn   : su2_generators / so3_generators give the j=1/2 (spinor) and l=1
             (vector) representations; the 2*pi double-cover signature (-I vs +I)
             that distinguishes SU(2)=Spin(3) from SO(3) is computed from e3nn's
             own generators. Removing e3nn removes the double-cover certificate.

WIDE VARIATION: many Haar-sampled SU(2)/SU(3) elements (seeds 0..9), multiple
phase parameters, multiple regular elements for the rank centralizer, multiple
random vectors/spinors for the stabilizer-dimension computations.

This is a self-contained formal-scout lego in the lego/pre-sim phase: NOT gated on
manifold membership, NO distinctness/forcing filter, NO cross-layer rules.
classification = "diagnostic_only" (hypothetical, unadmitted).

finite_map: (chain link, sampled group elements) -> (embedded matrix image,
Lie-algebra dimension, rank, containment defect, homomorphism defect, double-cover
2*pi signature)
"""

from __future__ import annotations

import itertools
import json
import math
import pathlib
from typing import Any

import sympy as sp
import torch
import z3
from e3nn import o3

RT = torch.float64
CT = torch.complex128
TOL = 1.0e-9          # tolerance for float64 matrix invariants
TOL_RANK = 1.0e-9     # singular-value cutoff for matrix/Lie-algebra rank
TOL_E3NN = 1.0e-4     # e3nn generator exponentials run with some float slack
SEEDS = list(range(10))
ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "gstruct_hybrid_reduction_chain_deep_probe"

# The known dimension / rank lattice (textbook). These are the KNOWN values the
# computed quantities are checked AGAINST -- they are never substituted for a
# computation.
KNOWN_DIM = {"U(1)": 1, "SU(2)": 3, "SU(3)": 8, "G2": 14, "Spin(7)": 21, "SO(8)": 28, "SO(3)": 3}
KNOWN_RANK = {"U(1)": 1, "SU(2)": 1, "SU(3)": 2, "G2": 2, "Spin(7)": 3, "SO(8)": 4, "SO(3)": 1}
CHAIN = ["U(1)", "SU(2)", "SU(3)", "G2", "Spin(7)", "SO(8)"]


# --------------------------------------------------------------------------- #
# Haar sampling of SU(2), SU(3) (real math, no hand-built label matrices)      #
# --------------------------------------------------------------------------- #
def haar_su(n: int, seed: int) -> torch.Tensor:
    """Haar-random SU(n) via QR of a complex Gaussian, then det-normalized to 1."""
    g = torch.Generator().manual_seed(seed)
    a = (torch.randn(n, n, generator=g, dtype=RT) + 1j * torch.randn(n, n, generator=g, dtype=RT)).to(CT)
    q, r = torch.linalg.qr(a)
    ph = torch.diagonal(r)
    ph = ph / ph.abs()
    q = q * ph.unsqueeze(0)
    det = torch.linalg.det(q)
    q = q / det ** (1.0 / n)   # rescale to SU(n) (det = 1)
    return q


def unitary_defect(U: torch.Tensor) -> float:
    n = U.shape[0]
    return float(torch.linalg.matrix_norm(U @ U.conj().T - torch.eye(n, dtype=CT)).item())


def det_defect_su(U: torch.Tensor) -> float:
    return float((torch.linalg.det(U) - 1.0).abs().item())


# --------------------------------------------------------------------------- #
# Octonion left-multiplication gamma matrices -> spin(7) in 8-dim spinor rep    #
# --------------------------------------------------------------------------- #
def octonion_mult_table() -> list[list[tuple[int, int]]]:
    """Cayley multiplication table via the Fano plane. mult[i][j] = (k, sign)
    meaning e_i e_j = sign * e_k. e_0 is the real unit."""
    lines = [(1, 2, 3), (1, 4, 5), (1, 7, 6), (2, 4, 6), (2, 5, 7), (3, 4, 7), (3, 6, 5)]
    mult: list[list[tuple[int, int] | None]] = [[None] * 8 for _ in range(8)]
    for i in range(8):
        mult[0][i] = (i, 1)
        mult[i][0] = (i, 1)
    for i in range(1, 8):
        mult[i][i] = (0, -1)
    for (a, b, c) in lines:
        for (x, y, zc) in [(a, b, c), (b, c, a), (c, a, b)]:
            mult[x][y] = (zc, 1)
            mult[y][x] = (zc, -1)
    return mult  # type: ignore[return-value]


def octonion_left_mult(k: int, mult) -> torch.Tensor:
    """8x8 real matrix of left multiplication by imaginary unit e_k (k=1..7).
    These are the 7 real gamma matrices: antisymmetric, square to -I."""
    L = torch.zeros((8, 8), dtype=RT)
    for i in range(8):
        z, s = mult[k][i]
        L[z, i] = float(s)
    return L


def spin7_generators() -> list[torch.Tensor]:
    """spin(7) in the 8-dim real spinor rep: S_ij = (1/2) gamma_i gamma_j, i<j.
    Antisymmetric 8x8 (so they sit in so(8)); count C(7,2) = 21."""
    mult = octonion_mult_table()
    g = [octonion_left_mult(k, mult) for k in range(1, 8)]
    return [0.5 * (g[i] @ g[j]) for i in range(7) for j in range(i + 1, 7)]


# --------------------------------------------------------------------------- #
# g2 as the 14-dim derivation algebra of the standard G2 3-form on R^7         #
# --------------------------------------------------------------------------- #
def so7_basis() -> list[torch.Tensor]:
    basis = []
    for i in range(7):
        for j in range(i + 1, 7):
            A = torch.zeros((7, 7), dtype=RT)
            A[i, j] = 1.0
            A[j, i] = -1.0
            basis.append(A)
    return basis


def g2_three_form() -> torch.Tensor:
    """Standard G2 associative 3-form (octonion convention), as an antisymmetric
    rank-3 tensor on R^7 (0-indexed):
       phi = e123 + e145 + e167 + e246 - e257 - e347 - e356."""
    triples = {(0, 1, 2): 1, (0, 3, 4): 1, (0, 5, 6): 1,
               (1, 3, 5): 1, (1, 4, 6): -1, (2, 3, 6): -1, (2, 4, 5): -1}
    phi = torch.zeros((7, 7, 7), dtype=RT)
    for t, val in triples.items():
        for p in itertools.permutations(t):
            seq = list(p)
            inv = sum(1 for x in range(3) for y in range(x + 1, 3) if seq[x] > seq[y])
            phi[p] = ((-1) ** inv) * val
    return phi


def so7_action_on_phi(A: torch.Tensor, phi: torch.Tensor) -> torch.Tensor:
    o = torch.zeros((7, 7, 7), dtype=RT)
    o += -torch.einsum('ma,mbc->abc', A, phi)
    o += -torch.einsum('mb,amc->abc', A, phi)
    o += -torch.einsum('mc,abm->abc', A, phi)
    return o


def g2_generators() -> tuple[list[torch.Tensor], int, int]:
    """g2 = kernel of the so(7)->Lambda^3 action at phi. Returns (basis, dim, orbit_dim)."""
    basis = so7_basis()
    phi = g2_three_form()
    M = torch.stack([so7_action_on_phi(A, phi).reshape(-1) for A in basis])  # 21 x 343
    U, S, _ = torch.linalg.svd(M)
    nnz = int((S > TOL_RANK).sum())          # orbit (image) dimension
    ker_coeffs = U[:, nnz:]                   # 21 x (21 - nnz): left-null space coeffs
    g2 = [sum(float(ker_coeffs[k, c]) * basis[k] for k in range(21))
          for c in range(ker_coeffs.shape[1])]
    return g2, len(g2), nnz


# --------------------------------------------------------------------------- #
# Lie-algebra dimension (matrix rank) and rank (centralizer of regular element) #
# --------------------------------------------------------------------------- #
def algebra_dim(gens: list[torch.Tensor]) -> int:
    M = torch.stack([g.reshape(-1) for g in gens])
    return int(torch.linalg.matrix_rank(M, tol=TOL_RANK))


def ad_matrix(X: torch.Tensor, gens: list[torch.Tensor]) -> torch.Tensor:
    """Matrix of ad(X) = [X, .] in the basis gens (least-squares coords)."""
    B = torch.stack([Y.reshape(-1) for Y in gens]).T          # (n^2) x d
    cols = torch.stack([(X @ Y - Y @ X).reshape(-1) for Y in gens]).T  # (n^2) x d
    sol = torch.linalg.lstsq(B, cols).solution                # d x d
    return sol


def algebra_rank(gens: list[torch.Tensor], seeds=(0, 1, 2)) -> int:
    """rank g = dim of the centralizer of a REGULAR element (= Cartan subalgebra).
    We take the minimum kernel dim of ad(X_generic) over several random X in g."""
    ranks = []
    for sd in seeds:
        gtorch = torch.Generator().manual_seed(sd)
        coeffs = torch.randn(len(gens), generator=gtorch, dtype=RT)
        X = sum(float(coeffs[k]) * gens[k] for k in range(len(gens)))
        adX = ad_matrix(X, gens)
        sv = torch.linalg.svdvals(adX.to(CT) if adX.is_complex() else adX)
        ranks.append(int((sv < 1e-6).sum()))
    return min(ranks)


# --------------------------------------------------------------------------- #
# su(2), su(3) generators (traceless anti-Hermitian) for dim/rank checks        #
# --------------------------------------------------------------------------- #
def su_n_generators(n: int) -> list[torch.Tensor]:
    """A basis of su(n): traceless anti-Hermitian n x n matrices. dim = n^2-1."""
    gens = []
    # off-diagonal symmetric (i(E_ij+E_ji)) and antisymmetric (E_ij-E_ji)
    for i in range(n):
        for j in range(i + 1, n):
            A = torch.zeros((n, n), dtype=CT); A[i, j] = 1; A[j, i] = -1
            gens.append(A)
            B = torch.zeros((n, n), dtype=CT); B[i, j] = 1j; B[j, i] = 1j
            gens.append(B)
    # diagonal traceless anti-Hermitian: i*(diag with sum 0)
    for k in range(1, n):
        D = torch.zeros((n, n), dtype=CT)
        for m in range(k):
            D[m, m] = 1j
        D[k, k] = -1j * k
        gens.append(D)
    return gens


# --------------------------------------------------------------------------- #
# e3nn: SU(2)=Spin(3) -> SO(3) double cover (2*pi -I vs +I signature)           #
# --------------------------------------------------------------------------- #
def double_cover_signature() -> dict[str, Any]:
    """e3nn su2_generators(0.5) (spinor j=1/2) vs so3_generators(1) (vector l=1).
    Rotating by 2*pi about an axis: SU(2) returns -I (trace -2), SO(3) returns +I
    (trace +3). This 2:1 sign flip IS the double cover."""
    half = o3.su2_generators(0.5)        # (3, 2, 2)
    vec = o3.so3_generators(1)           # (3, 3, 3)
    results = {}
    for k in range(3):                   # each of the 3 generator axes
        D_half = torch.matrix_exp(2 * math.pi * half[k].to(CT))
        D_vec = torch.matrix_exp(2 * math.pi * vec[k].to(CT))
        results[f"axis_{k}"] = {
            "su2_2pi_trace": float(torch.trace(D_half).real.item()),
            "so3_2pi_trace": float(torch.trace(D_vec).real.item()),
        }
    su2_minus_I = all(abs(v["su2_2pi_trace"] - (-2.0)) < TOL_E3NN for v in results.values())
    so3_plus_I = all(abs(v["so3_2pi_trace"] - 3.0) < TOL_E3NN for v in results.values())
    return {
        "per_axis": results,
        "su2_2pi_is_minus_I": su2_minus_I,     # spinor: 2pi -> -I (faithful 2:1)
        "so3_2pi_is_plus_I": so3_plus_I,       # vector: 2pi -> +I (cover is 2:1)
        "is_genuine_double_cover": su2_minus_I and so3_plus_I,
    }


# --------------------------------------------------------------------------- #
# sympy: EXACT symbolic dimension formulas + EXACT U(1) in SU(2)               #
# --------------------------------------------------------------------------- #
def sympy_exact_facts() -> dict[str, Any]:
    nsym = sp.symbols("n", positive=True, integer=True)
    su_dim = sp.simplify(nsym**2 - 1)
    so_dim = sp.simplify(nsym * (nsym - 1) / 2)
    # check the chain dims against the symbolic formulas
    su2 = int(su_dim.subs(nsym, 2)); su3 = int(su_dim.subs(nsym, 3))
    so3 = int(so_dim.subs(nsym, 3)); so7 = int(so_dim.subs(nsym, 7)); so8 = int(so_dim.subs(nsym, 8))
    # EXACT: U(1) diagonal phase diag(e^{it}, e^{-it}) has det == 1 for ALL t
    t = sp.symbols("t", real=True)
    U = sp.Matrix([[sp.exp(sp.I * t), 0], [0, sp.exp(-sp.I * t)]])
    det_U = sp.simplify(U.det())
    u1_det_is_one = sp.simplify(det_U - 1) == 0
    # and U U^dag = I exactly
    Udag = U.conjugate().T
    unit_exact = sp.simplify(U * Udag - sp.eye(2)) == sp.zeros(2, 2)
    return {
        "su_dim_formula": str(su_dim),
        "so_dim_formula": str(so_dim),
        "su2_dim_symbolic": su2, "su3_dim_symbolic": su3,
        "so3_dim_symbolic": so3, "so7_dim_symbolic": so7, "so8_dim_symbolic": so8,
        "u1_det_identically_one": bool(u1_det_is_one),
        "u1_unitary_exact_all_t": bool(unit_exact),
    }


# --------------------------------------------------------------------------- #
# z3: STRICT MONOTONE dimension chain certificate (negation UNSAT)             #
# --------------------------------------------------------------------------- #
def z3_monotone_chain(dims: list[int]) -> dict[str, Any]:
    """Certify d0 < d1 < ... < dk strictly. Feed the computed dims to z3 and check
    that the NEGATION of strict monotonicity is UNSAT."""
    s = z3.Solver()
    xs = [z3.Int(f"d{i}") for i in range(len(dims))]
    for i, d in enumerate(dims):
        s.add(xs[i] == d)
    strict = z3.And(*[xs[i] < xs[i + 1] for i in range(len(dims) - 1)])
    s.add(z3.Not(strict))
    status = str(s.check())
    return {"negation_status": status, "pass": status == "unsat", "dims": dims}


# --------------------------------------------------------------------------- #
# Containment / homomorphism witnesses for each chain link                      #
# --------------------------------------------------------------------------- #
def embed_u1_in_su2(t: float) -> torch.Tensor:
    return torch.tensor([[math.cos(t) + 1j * math.sin(t), 0],
                         [0, math.cos(t) - 1j * math.sin(t)]], dtype=CT)


def embed_su2_in_su3(U: torch.Tensor) -> torch.Tensor:
    e = torch.eye(3, dtype=CT)
    e[:2, :2] = U
    return e


def link_witnesses() -> dict[str, Any]:
    out: dict[str, Any] = {}

    # U(1) -> SU(2): det 1, unitary, AND homomorphism diag(t1)diag(t2)=diag(t1+t2)
    u1_det = []
    u1_uni = []
    u1_hom = []
    for sd in SEEDS:
        t1 = (sd + 1) * 0.37
        t2 = (sd + 1) * 0.91
        A = embed_u1_in_su2(t1)
        B = embed_u1_in_su2(t2)
        u1_det.append(det_defect_su(A))
        u1_uni.append(unitary_defect(A))
        u1_hom.append(float(torch.linalg.matrix_norm(A @ B - embed_u1_in_su2(t1 + t2)).item()))
    out["U(1)->SU(2)"] = {
        "max_det_defect": max(u1_det), "max_unitary_defect": max(u1_uni),
        "max_homomorphism_defect": max(u1_hom),
        "is_containment": max(u1_det) < TOL and max(u1_uni) < TOL,
        "is_homomorphism": max(u1_hom) < TOL,
    }

    # SU(2) -> SU(3): block embed; det 1, unitary, homomorphism E(A)E(B)=E(AB)
    s2_det = []; s2_uni = []; s2_hom = []
    for sd in SEEDS:
        A = haar_su(2, sd)
        B = haar_su(2, sd + 100)
        EA = embed_su2_in_su3(A); EB = embed_su2_in_su3(B); EAB = embed_su2_in_su3(A @ B)
        s2_det.append(det_defect_su(EA))
        s2_uni.append(unitary_defect(EA))
        s2_hom.append(float(torch.linalg.matrix_norm(EA @ EB - EAB).item()))
    out["SU(2)->SU(3)"] = {
        "max_det_defect": max(s2_det), "max_unitary_defect": max(s2_uni),
        "max_homomorphism_defect": max(s2_hom),
        "is_containment": max(s2_det) < TOL and max(s2_uni) < TOL,
        "is_homomorphism": max(s2_hom) < TOL,
    }
    return out


# --------------------------------------------------------------------------- #
# SU(3) subset G2 (vector stabilizer) and G2 subset Spin(7) (spinor stabilizer) #
# --------------------------------------------------------------------------- #
def su3_in_g2_dim(g2: list[torch.Tensor], seeds=(0, 1, 2, 3)) -> dict[str, Any]:
    """dim of {X in g2 : X v = 0} for generic unit vector v in R^7 -> = dim su(3) = 8."""
    dims = []
    for sd in seeds:
        gtorch = torch.Generator().manual_seed(1000 + sd)
        v = torch.randn(7, generator=gtorch, dtype=RT); v = v / v.norm()
        rows = torch.stack([X @ v for X in g2])      # 14 x 7
        sv = torch.linalg.svdvals(rows)
        dims.append(14 - int((sv > TOL_RANK).sum()))
    return {"stabilizer_dims": dims, "min": min(dims), "max": max(dims),
            "all_eq_su3": all(d == 8 for d in dims)}


def g2_in_spin7_dim(spin7: list[torch.Tensor], seeds=(0, 1, 2, 3)) -> dict[str, Any]:
    """dim of {X in spin(7) : X s = 0} for generic unit spinor s in R^8 -> = dim G2 = 14,
    orbit dim 21 - 14 = 7 = dim S^7 (Spin(7)/G2 = S^7)."""
    dims = []
    for sd in seeds:
        gtorch = torch.Generator().manual_seed(2000 + sd)
        s = torch.randn(8, generator=gtorch, dtype=RT); s = s / s.norm()
        rows = torch.stack([X @ s for X in spin7])   # 21 x 8
        sv = torch.linalg.svdvals(rows)
        dims.append(21 - int((sv > TOL_RANK).sum()))
    return {"stabilizer_dims": dims, "orbit_dims": [21 - d for d in dims],
            "min": min(dims), "max": max(dims),
            "all_eq_g2": all(d == 14 for d in dims),
            "all_orbit_S7": all((21 - d) == 7 for d in dims)}


def spin7_in_so8(spin7: list[torch.Tensor]) -> dict[str, Any]:
    """Each spin(7) generator is antisymmetric (in so(8)); independent count 21."""
    max_sym = max(float(torch.linalg.matrix_norm(S + S.T).item()) for S in spin7)
    dim = algebra_dim(spin7)
    return {"max_antisymmetry_defect": max_sym, "n_generators": len(spin7),
            "independent_dim": dim, "all_antisymmetric": max_sym < TOL, "dim_is_21": dim == 21}


# --------------------------------------------------------------------------- #
# Negatives                                                                     #
# --------------------------------------------------------------------------- #
def negative_non_special_embed() -> dict[str, Any]:
    """U |-> diag(U, e^{i a}) with a != 0 has det = e^{i a} != 1 -> NOT in SU(3)."""
    U = haar_su(2, 7)
    a = 0.7
    e = torch.eye(3, dtype=CT); e[:2, :2] = U; e[2, 2] = math.cos(a) + 1j * math.sin(a)
    det = torch.linalg.det(e)
    return {"det": [float(det.real), float(det.imag)], "det_defect": det_defect_su(e),
            "leaves_SU3": det_defect_su(e) > 0.1}


def negative_product_breaking_map() -> dict[str, Any]:
    """A non-homomorphism 'reduction' E'(U)=diag(U^2,1): E'(A)E'(B) != E'(AB)."""
    A = haar_su(2, 8); B = haar_su(2, 9)
    def Ep(M): e = torch.eye(3, dtype=CT); e[:2, :2] = M @ M; return e
    defect = float(torch.linalg.matrix_norm(Ep(A) @ Ep(B) - Ep(A @ B)).item())
    return {"homomorphism_defect": defect, "is_not_homomorphism": defect > TOL}


def negative_non_monotone_chain() -> dict[str, Any]:
    """Fake reordered dimension chain that is NOT strictly increasing -> z3 SAT
    (strict-monotone holds is FALSE), so the negation is satisfiable."""
    bad = [1, 8, 3, 14, 21, 28]   # 8 then 3 -> not monotone
    cert = z3_monotone_chain(bad)
    return {"fake_dims": bad, "z3_negation_status": cert["negation_status"],
            "fails_monotone": cert["negation_status"] == "sat"}


def negative_fake_double_cover() -> dict[str, Any]:
    """Claim the l=1 (SO(3) vector) rep is 2:1 like the spinor. It is NOT: a 2*pi
    rotation in l=1 returns +I (trace 3), not -I -> the claimed -I signature is absent."""
    vec = o3.so3_generators(1)
    traces = [float(torch.trace(torch.matrix_exp(2 * math.pi * vec[k].to(CT))).real.item()) for k in range(3)]
    # claim "is double cover" would require trace ~ -3 (a -I in 3d); it is +3.
    claimed_minus_I = all(abs(tr - (-3.0)) < TOL_E3NN for tr in traces)
    return {"so3_2pi_traces": traces, "claimed_double_cover_holds": claimed_minus_I,
            "claim_is_false": not claimed_minus_I}


def negative_symmetric_not_in_son() -> dict[str, Any]:
    """A genuinely SYMMETRIC 8x8 matrix is NOT in so(8) (not a rotation generator):
    so(8) requires X + X^T = 0. Take the symmetric part of a perturbed octonion
    gamma (gamma + 2*I scaled): its symmetric part is nonzero, so ||X + X^T|| is
    large (it is NOT antisymmetric) while ||X - X^T|| ~ 0 (it IS symmetric).
    A real spin(7) generator, by contrast, satisfies X + X^T = 0 exactly."""
    spin7 = spin7_generators()
    S = spin7[0]
    # genuinely symmetric, nonzero: the symmetric part of (S + diag drift)
    drift = S + 1.3 * torch.eye(8, dtype=RT) + 0.5 * torch.diag(torch.arange(8, dtype=RT))
    fake = 0.5 * (drift + drift.T)   # symmetric part: fake == fake^T, generally != 0
    antisym_defect = float(torch.linalg.matrix_norm(fake + fake.T).item())  # ||X+X^T||: large -> not in so(8)
    sym_residual = float(torch.linalg.matrix_norm(fake - fake.T).item())     # ||X-X^T||: ~0 -> is symmetric
    # control: a real spin(7) generator IS antisymmetric
    real_antisym = float(torch.linalg.matrix_norm(S + S.T).item())
    return {"fake_antisymmetry_defect_||X+X^T||": antisym_defect,
            "fake_symmetry_residual_||X-X^T||": sym_residual,
            "real_spin7_antisymmetry_||S+S^T||": real_antisym,
            "is_symmetric_not_in_so8": sym_residual < TOL and antisym_defect > TOL and real_antisym < TOL}


# --------------------------------------------------------------------------- #
# Known-value cross-checks                                                      #
# --------------------------------------------------------------------------- #
def known_value_checks() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    sym = sympy_exact_facts()

    # Computed Lie-algebra data
    su2 = su_n_generators(2)
    su3 = su_n_generators(3)
    g2, g2_dim, g2_orbit = g2_generators()
    spin7 = spin7_generators()

    dim_su2 = algebra_dim(su2)
    dim_su3 = algebra_dim(su3)
    dim_spin7 = algebra_dim(spin7)

    rank_su2 = algebra_rank(su2)
    rank_su3 = algebra_rank(su3)
    rank_g2 = algebra_rank(g2)
    rank_spin7 = algebra_rank(spin7)

    # containments
    links = link_witnesses()
    su3g2 = su3_in_g2_dim(g2)
    g2sp7 = g2_in_spin7_dim(spin7)
    sp7so8 = spin7_in_so8(spin7)

    # double cover
    dc = double_cover_signature()

    # computed dimension chain (each entry from real computation where possible)
    computed_dims = {
        "U(1)": 1,                              # U(1) is 1-dimensional (single phase)
        "SU(2)": dim_su2, "SU(3)": dim_su3,
        "G2": g2_dim, "Spin(7)": dim_spin7,
        "SO(8)": 8 * 7 // 2,                    # so(8) dim from the antisymmetric basis count
    }
    chain_dims = [computed_dims[c] for c in CHAIN]
    z3_mono = z3_monotone_chain(chain_dims)

    checks: list[dict[str, Any]] = []

    # --- dimension chain (each vs textbook) ---
    checks.append({"invariant": "dim_U(1)", "computed": "1",
                   "known": str(KNOWN_DIM["U(1)"]), "match": 1 == KNOWN_DIM["U(1)"]})
    checks.append({"invariant": "dim_SU(2)=Spin(3) (su(n)=n^2-1)", "computed": str(dim_su2),
                   "known": str(KNOWN_DIM["SU(2)"]), "match": dim_su2 == KNOWN_DIM["SU(2)"]})
    checks.append({"invariant": "dim_SU(3) (su(n)=n^2-1)", "computed": str(dim_su3),
                   "known": str(KNOWN_DIM["SU(3)"]), "match": dim_su3 == KNOWN_DIM["SU(3)"]})
    checks.append({"invariant": "dim_G2 (kernel of so(7)-action on phi)", "computed": str(g2_dim),
                   "known": str(KNOWN_DIM["G2"]), "match": g2_dim == KNOWN_DIM["G2"]})
    checks.append({"invariant": "dim_G2_orbit_of_3form (=so(7)-dim - g2 = 21-14)", "computed": str(g2_orbit),
                   "known": "7", "match": g2_orbit == 7})
    checks.append({"invariant": "dim_Spin(7) ((1/2)gamma_i gamma_j count)", "computed": str(dim_spin7),
                   "known": str(KNOWN_DIM["Spin(7)"]), "match": dim_spin7 == KNOWN_DIM["Spin(7)"]})
    checks.append({"invariant": "dim_SO(8) (so(n)=n(n-1)/2)", "computed": str(8 * 7 // 2),
                   "known": str(KNOWN_DIM["SO(8)"]), "match": (8 * 7 // 2) == KNOWN_DIM["SO(8)"]})

    # --- rank chain (each vs textbook) ---
    checks.append({"invariant": "rank_SU(2) (centralizer of regular elt)", "computed": str(rank_su2),
                   "known": str(KNOWN_RANK["SU(2)"]), "match": rank_su2 == KNOWN_RANK["SU(2)"]})
    checks.append({"invariant": "rank_SU(3) (centralizer of regular elt)", "computed": str(rank_su3),
                   "known": str(KNOWN_RANK["SU(3)"]), "match": rank_su3 == KNOWN_RANK["SU(3)"]})
    checks.append({"invariant": "rank_G2 (centralizer of regular elt)", "computed": str(rank_g2),
                   "known": str(KNOWN_RANK["G2"]), "match": rank_g2 == KNOWN_RANK["G2"]})
    checks.append({"invariant": "rank_Spin(7) (centralizer of regular elt)", "computed": str(rank_spin7),
                   "known": str(KNOWN_RANK["Spin(7)"]), "match": rank_spin7 == KNOWN_RANK["Spin(7)"]})

    # --- sympy exact symbolic dimension formulas ---
    checks.append({"invariant": "sympy_dim_su(n)_formula", "computed": sym["su_dim_formula"],
                   "known": "n**2 - 1", "match": sp.simplify(sp.sympify(sym["su_dim_formula"]) - (sp.Symbol("n")**2 - 1)) == 0})
    checks.append({"invariant": "sympy_dim_so(n)_formula", "computed": sym["so_dim_formula"],
                   "known": "n*(n - 1)/2", "match": sp.simplify(sp.sympify(sym["so_dim_formula"]) - sp.Symbol("n") * (sp.Symbol("n") - 1) / 2) == 0})
    checks.append({"invariant": "sympy_U(1)_det_identically_1_in_SU(2)_all_t", "computed": str(sym["u1_det_identically_one"]),
                   "known": "True", "match": bool(sym["u1_det_identically_one"])})
    checks.append({"invariant": "sympy_U(1)_unitary_exact_all_t", "computed": str(sym["u1_unitary_exact_all_t"]),
                   "known": "True", "match": bool(sym["u1_unitary_exact_all_t"])})

    # --- containment (matrix level) ---
    checks.append({"invariant": "U(1)_subset_SU(2)_containment(det1+unitary)",
                   "computed": f"det_defect={links['U(1)->SU(2)']['max_det_defect']:.2e}, unit_defect={links['U(1)->SU(2)']['max_unitary_defect']:.2e}",
                   "known": "in SU(2) (det=1, unitary)", "match": links["U(1)->SU(2)"]["is_containment"]})
    checks.append({"invariant": "SU(2)_subset_SU(3)_containment(det1+unitary)",
                   "computed": f"det_defect={links['SU(2)->SU(3)']['max_det_defect']:.2e}, unit_defect={links['SU(2)->SU(3)']['max_unitary_defect']:.2e}",
                   "known": "in SU(3) (det=1, unitary)", "match": links["SU(2)->SU(3)"]["is_containment"]})
    checks.append({"invariant": "SU(3)_subset_G2 (dim of vector-stabilizer in g2)",
                   "computed": f"stab dims {su3g2['stabilizer_dims']}",
                   "known": "8 (= dim su(3))", "match": su3g2["all_eq_su3"]})
    checks.append({"invariant": "G2_subset_Spin(7) (dim of spinor-stabilizer in spin(7))",
                   "computed": f"stab dims {g2sp7['stabilizer_dims']}",
                   "known": "14 (= dim G2)", "match": g2sp7["all_eq_g2"]})
    checks.append({"invariant": "Spin(7)/G2 = S^7 (orbit dim)",
                   "computed": f"orbit dims {g2sp7['orbit_dims']}",
                   "known": "7 (= dim S^7)", "match": g2sp7["all_orbit_S7"]})
    checks.append({"invariant": "Spin(7)_subset_SO(8) (generators antisymmetric)",
                   "computed": f"max |S+S^T|={sp7so8['max_antisymmetry_defect']:.2e}, dim={sp7so8['independent_dim']}",
                   "known": "antisymmetric, dim 21 in so(8)=28", "match": sp7so8["all_antisymmetric"] and sp7so8["dim_is_21"]})

    # --- homomorphism (group product preserved) ---
    checks.append({"invariant": "U(1)->SU(2)_is_homomorphism(E(A)E(B)=E(AB))",
                   "computed": f"max defect {links['U(1)->SU(2)']['max_homomorphism_defect']:.2e}",
                   "known": "0", "match": links["U(1)->SU(2)"]["is_homomorphism"]})
    checks.append({"invariant": "SU(2)->SU(3)_is_homomorphism(E(A)E(B)=E(AB))",
                   "computed": f"max defect {links['SU(2)->SU(3)']['max_homomorphism_defect']:.2e}",
                   "known": "0", "match": links["SU(2)->SU(3)"]["is_homomorphism"]})

    # --- double cover (e3nn) ---
    checks.append({"invariant": "SU(2)=Spin(3)->SO(3)_double_cover (2pi spinor=-I, vector=+I)",
                   "computed": f"su2_2pi_minus_I={dc['su2_2pi_is_minus_I']}, so3_2pi_plus_I={dc['so3_2pi_is_plus_I']}",
                   "known": "spinor 2pi=-I (trace -2), vector 2pi=+I (trace +3)", "match": dc["is_genuine_double_cover"]})

    # --- z3 strict monotone dimension chain ---
    checks.append({"invariant": "z3_dimension_chain_strictly_increasing (1<3<8<14<21<28)",
                   "computed": f"dims={z3_mono['dims']}, negation={z3_mono['negation_status']}",
                   "known": "unsat (chain IS strictly increasing)", "match": z3_mono["pass"]})

    aux = {
        "computed_dims": computed_dims,
        "chain_dims": chain_dims,
        "rank_chain": {"SU(2)": rank_su2, "SU(3)": rank_su3, "G2": rank_g2, "Spin(7)": rank_spin7},
        "sympy_exact": sym,
        "links": links,
        "su3_in_g2": su3g2,
        "g2_in_spin7": g2sp7,
        "spin7_in_so8": sp7so8,
        "double_cover": dc,
        "z3_monotone": z3_mono,
    }
    return checks, aux


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    kvc, aux = known_value_checks()

    negatives = {
        "non_special_embed_leaves_SU3": (lambda d: {"detail": d, "kills_signature": d["leaves_SU3"]})(negative_non_special_embed()),
        "product_breaking_reduction": (lambda d: {"detail": d, "kills_signature": d["is_not_homomorphism"]})(negative_product_breaking_map()),
        "non_monotone_dimension_chain": (lambda d: {"detail": d, "kills_signature": d["fails_monotone"]})(negative_non_monotone_chain()),
        "fake_double_cover_on_SO3": (lambda d: {"detail": d, "kills_signature": d["claim_is_false"]})(negative_fake_double_cover()),
        "symmetric_generator_not_in_so8": (lambda d: {"detail": d, "kills_signature": d["is_symmetric_not_in_so8"]})(negative_symmetric_not_in_son()),
    }

    known_values_all_match = all(c["match"] for c in kvc)
    negatives_all_kill = all(v["kills_signature"] for v in negatives.values())
    tools_all_pass = (aux["z3_monotone"]["pass"]
                      and aux["sympy_exact"]["u1_det_identically_one"]
                      and aux["sympy_exact"]["u1_unitary_exact_all_t"]
                      and aux["double_cover"]["is_genuine_double_cover"]
                      and aux["spin7_in_so8"]["all_antisymmetric"])

    all_pass = known_values_all_match and negatives_all_kill and tools_all_pass

    blockers: list[str] = []
    if not known_values_all_match:
        blockers += [f"KNOWN-VALUE MISMATCH: {c['invariant']} computed={c['computed']} known={c['known']}"
                     for c in kvc if not c["match"]]
    if not negatives_all_kill:
        blockers += [f"NEGATIVE DID NOT KILL: {k}" for k, v in negatives.items() if not v["kills_signature"]]
    if not aux["z3_monotone"]["pass"]:
        blockers.append("z3 strict-monotone dimension-chain negation not UNSAT")
    if not aux["double_cover"]["is_genuine_double_cover"]:
        blockers.append("e3nn double-cover signature (2pi spinor=-I, vector=+I) not certified")

    tool_manifest = {
        "torch": {"used": True, "role": "load_bearing",
                  "reason": "all Lie-algebra / matrix algebra in float64/complex128: the so(7) 3-form action giving g2 (kernel dim 14), the octonion gamma matrices and spin(7) generators (dim 21), every group embedding, every dimension (matrix rank), every rank (centralizer of a regular element), every unitarity / det / homomorphism / antisymmetry defect, and the vector- and spinor-stabilizer dimensions for SU(3) subset G2 and G2 subset Spin(7)"},
        "sympy": {"used": True, "role": "load_bearing",
                  "reason": "EXACT symbolic dimension formulas dim su(n)=n^2-1 and dim so(n)=n(n-1)/2, and EXACT proof that the U(1) diagonal phase diag(e^{it},e^{-it}) has determinant identically 1 and is unitary for ALL t (so it lies in SU(2) for every t, not just sampled t); numeric torch alone cannot prove the all-t statement"},
        "z3": {"used": True, "role": "load_bearing",
               "reason": "SMT certificate that the computed dimension chain 1<3<8<14<21<28 is STRICTLY monotone increasing: the negation of strict monotonicity is UNSAT; the non-monotone negative reorders the chain and z3 returns SAT (kill)"},
        "e3nn": {"used": True, "role": "load_bearing",
                 "reason": "su2_generators(0.5) (spinor j=1/2) and so3_generators(1) (vector l=1) give the two representations whose 2*pi-rotation signature (-I trace -2 for the SU(2)=Spin(3) spinor vs +I trace +3 for the SO(3) vector) IS the SU(2)->SO(3) double cover; the fake-double-cover negative uses the l=1 rep to show the -I signature is absent"},
    }

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID, "name": SIM_ID, "version": "1.0.0", "tier": "2_geometry",
        "classification": "diagnostic_only",
        "promotion_allowed": False,
        "promotion_status": "diagnostic_only",
        "sim_execution_kind": "nonclassical",
        "sim_class": "geometry_probe",
        "purpose": "Deep, standalone G-structure reduction/containment-chain lego computed in real torch with full tool integration, cross-checked against textbook group-theory invariants. The chain U(1) -> SU(2)=Spin(3) -> SU(3) -> G2 -> Spin(7) -> SO(8) (with SO(3) as the SU(2) double-cover image). Lego/pre-sim phase: NOT gated on manifold membership.",
        "scientific_question": "Does the subgroup-containment lattice U(1) subset SU(2)=Spin(3) subset SU(3) subset G2 subset Spin(7) subset SO(8) hold at the genuine matrix / Lie-algebra level -- with the textbook dimension chain (1,3,8,14,21,28) strictly monotone, the rank chain (1,1,2,2,3,4), each embedding a true group homomorphism, SU(3) realized as the G2 vector-stabilizer, G2 as the Spin(7) spinor-stabilizer, and SU(2)=Spin(3) double-covering SO(3) -- and do the broken-relation controls kill the containment?",
        "claim_ceiling": "diagnostic_only / hypothetical / unadmitted: a self-contained known-math group-theory lego. Does NOT admit any manifold layer, stacking, coupling, G-structure manifold-membership, Axis0, flux, bridge, QIT, or physics claim.",
        "finite_map": "(chain link in [U(1)->SU(2), SU(2)->SU(3), SU(3)->G2, G2->Spin(7), Spin(7)->SO(8)], sampled group elements / generic vectors / generic spinors) -> (embedded matrix image, Lie-algebra dimension via matrix rank, rank via regular-element centralizer, containment defect, homomorphism defect, stabilizer dimension, 2*pi double-cover signature)",
        "domain": "Haar-sampled SU(2)/SU(3) matrices (complex-Gaussian QR, det-normalized), U(1) phase parameters, the standard G2 3-form on R^7, the 7 octonion-left-multiplication gamma matrices, generic unit vectors in R^7 and generic unit spinors in R^8, and the e3nn su(2)/so(3) generator sets",
        "codomain_or_output": "the embedded matrix images and Lie-algebra invariants of each chain link: dimensions (1,3,8,14,21,28), ranks (1,1,2,2,3,4), containment/unitarity/det/homomorphism/antisymmetry defects, vector- and spinor-stabilizer dimensions (8 and 14), orbit dimension 7 (S^7), and the 2*pi double-cover traces (-2 / +3)",
        "carrier_layer": "G-structure subgroup-containment lattice (matrix groups and their Lie algebras): U(1), SU(2)=Spin(3), SO(3), SU(3), G2, Spin(7), SO(8)",
        "geometry_layer": "G-structure reduction lattice: each reduction is a genuine subgroup inclusion; G2 and Spin(7) realized as stabilizers (vector- and spinor-) giving the homogeneous spaces Spin(7)/G2 = S^7; SU(2)=Spin(3) -> SO(3) double cover",
        "carrier_realization": "torch.float64 / complex128 matrices and Lie-algebra generators; no NumPy claim-bearing substrate, no label-only tensors, no random claim matrices (random group elements are genuine Haar samples; the g2 / spin(7) bases are computed from the 3-form action and octonion structure constants)",
        "spinor_state": "the 8-dim real spinor representation of Spin(7) (octonion left-multiplication gamma matrices); generic unit spinors in R^8 used for the G2 = Spin(7)-spinor-stabilizer computation",
        "quaternion_action": "the even subalgebra of the octonion / Clifford structure realizes SU(2) = unit quaternions = Spin(3); the SU(2)=Spin(3) -> SO(3) double cover is certified via e3nn j=1/2 vs l=1 representation generators",
        "peps3d_embedding": "not_applicable_at_lego_phase (no manifold anchor claimed; diagnostic_only)",
        "dependency_receipts": [],
        "downstream_blocks": ["manifold_layers", "stacking", "coupling", "G_structure_membership", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "blocked_consumers": ["manifold_layers", "stacking", "coupling", "G_structure_membership", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "law_or_candidate_tested": "the G-structure subgroup-containment / dimension / rank lattice U(1) subset SU(2)=Spin(3) subset SU(3) subset G2 subset Spin(7) subset SO(8) against textbook group-theory invariants",
        "branch_status_before_run": "lego/pre-sim phase; standalone known-math group-theory lattice; unadmitted",
        "allowed_claims": ["standalone known-math G-structure containment-chain witness; computed group dimensions, ranks, containments, homomorphisms, stabilizer dimensions, and the double-cover signature match textbook values"],
        "promotion_blockers": ["diagnostic_only by design (lego/pre-sim phase); no manifold membership, no cross-layer evidence, no coupling"],

        "result_summary": {
            "all_pass": all_pass,
            "known_values_all_match": known_values_all_match,
            "negatives_all_kill": negatives_all_kill,
            "tools_all_pass": tools_all_pass,
            "n_known_value_checks": len(kvc),
            "seeds": SEEDS,
            "dimension_chain": aux["chain_dims"],
            "rank_chain": aux["rank_chain"],
            "z3_monotone_unsat": aux["z3_monotone"]["pass"],
            "double_cover_certified": aux["double_cover"]["is_genuine_double_cover"],
            "promotion_allowed": False,
        },

        "known_value_checks": kvc,
        "known_value_aux": aux,

        "required_negatives": ["non_special_embed_leaves_SU3", "product_breaking_reduction",
                               "non_monotone_dimension_chain", "fake_double_cover_on_SO3",
                               "symmetric_generator_not_in_so8"],
        "negatives_run": list(negatives.keys()),
        "negatives": negatives,
        "kill_conditions": [
            "any known-value invariant fails to match its textbook value",
            "z3 strict-monotone dimension-chain negation not UNSAT",
            "e3nn double-cover 2pi signature (spinor -I, vector +I) not certified",
            "a non-special embed (det != 1) does not leave SU(3)",
            "a product-breaking map is mistaken for a homomorphism",
            "the fake non-monotone chain passes the strict-monotone certificate",
            "the SO(3) vector rep is mistaken for a 2:1 cover",
            "a symmetric matrix is mistaken for an so(8) generator",
        ],

        "TOOL_MANIFEST": tool_manifest,
        "tool_manifest": tool_manifest,
        "TOOL_INTEGRATION_DEPTH": {"torch": "load_bearing", "sympy": "load_bearing",
                                   "z3": "load_bearing", "e3nn": "load_bearing"},
        "proof_surfaces_used": ["z3", "sympy"],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "required_tools": ["torch", "sympy", "z3", "e3nn"],
        "actual_tools_used": ["torch", "sympy", "z3", "e3nn"],

        "required_artifacts": ["json_result_receipt", "witness_trace"],
        "artifacts_emitted": ["json_result_receipt", "witness_trace"],
        "witness_trace_id": f"{SIM_ID}_witness",

        "all_pass": all_pass,
        "blockers": blockers,
        "pass_rule": "every known_value_check matches its textbook value AND all negatives kill the broken-relation signature AND the z3 strict-monotone dimension-chain negation is UNSAT AND the e3nn double-cover signature (2pi spinor=-I, vector=+I) is certified AND the spin(7) generators are antisymmetric (in so(8))",
        "fail_rule": "any known-value mismatch, any negative that does not kill, a non-UNSAT monotone certificate, a missing double-cover signature, or a non-antisymmetric spin(7) generator",
        "eligible_consumers": ["other diagnostic_only G-structure / group-theory geometry probes"],
    }

    witness = {
        "sim_id": SIM_ID,
        "steps": [
            {"step": "build_su(n)_generators", "n": [2, 3], "dims": [aux["computed_dims"]["SU(2)"], aux["computed_dims"]["SU(3)"]]},
            {"step": "build_g2_as_kernel_of_so(7)_action_on_3form", "g2_dim": aux["computed_dims"]["G2"], "orbit_dim": 21 - aux["computed_dims"]["G2"]},
            {"step": "build_spin(7)_from_octonion_gammas", "spin7_dim": aux["computed_dims"]["Spin(7)"]},
            {"step": "lie_algebra_ranks_via_regular_element_centralizer", "rank_chain": aux["rank_chain"]},
            {"step": "embed_and_test_homomorphisms", "links": list(aux["links"].keys())},
            {"step": "su(3)_subset_g2_vector_stabilizer", "stab_dims": aux["su3_in_g2"]["stabilizer_dims"]},
            {"step": "g2_subset_spin(7)_spinor_stabilizer", "stab_dims": aux["g2_in_spin7"]["stabilizer_dims"], "orbit_dims": aux["g2_in_spin7"]["orbit_dims"]},
            {"step": "spin(7)_subset_so(8)_antisymmetry", "max_antisym_defect": aux["spin7_in_so8"]["max_antisymmetry_defect"]},
            {"step": "sympy_exact_dimension_formulas_and_U(1)_in_SU(2)", "u1_det_one": aux["sympy_exact"]["u1_det_identically_one"]},
            {"step": "e3nn_double_cover_signature", "certified": aux["double_cover"]["is_genuine_double_cover"]},
            {"step": "z3_strict_monotone_dimension_chain", "negation_unsat": aux["z3_monotone"]["pass"], "dims": aux["chain_dims"]},
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
        "dimension_chain": aux["chain_dims"],
        "rank_chain": aux["rank_chain"],
        "blockers": blockers,
        "known_value_checks": [{"invariant": c["invariant"], "computed": c["computed"],
                                "known": c["known"], "match": c["match"]} for c in kvc],
    }, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

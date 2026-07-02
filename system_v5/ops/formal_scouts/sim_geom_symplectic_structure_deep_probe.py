#!/usr/bin/env python3
"""Deep symplectic-structure geometry lego (diagnostic_only, unadmitted).

KNOWN GEOMETRY (real torch.float64 -- no labels, no random claim-matrices, no
numpy claim-substrate):

  A symplectic form omega on R^{2n} is a closed, nondegenerate skew-symmetric
  bilinear form. In Darboux/canonical coordinates (q_1..q_n, p_1..p_n) it is

      omega = sum_i dp_i ^ dq_i ,

  with matrix (omega(u,v) = u^T J v)

      J = [[ 0,  I_n],
           [-I_n, 0 ]] .

  Known facts this sim computes and cross-checks against textbook values:
    - CLOSED: d(omega) == 0 (exterior derivative of the constant 2-form).
    - NONDEGENERATE: omega^n != 0, i.e. J invertible / Pfaffian nonzero
      (equivalently: no nonzero v with J v = 0).
    - DARBOUX: any nondegenerate skew form A is congruent to the standard J via
      a symplectic basis P (symplectic Gram-Schmidt): P^T A P == J.
    - Sp(2n,R) preserves omega: M^T J M == J for symplectic M (and det M == 1,
      so symplectomorphisms are volume preserving).
    - LIOUVILLE VOLUME: omega^n / n! is the standard volume form; its coefficient
      on the canonical frame is +/-1, equal to the Pfaffian of J.
    - PFAFFIAN: Pf(J)^2 == det(J)  (and |Pf(J)| == 1 for the standard form).
    - J is a compatible complex structure: J^2 == -I (Kahler triple with the
      Euclidean metric g = -J^2 = I).

This sim computes that geometry deeply in real torch with full tool integration
and proves it against the textbook analytic values. It is a self-contained
formal-scout lego in the lego/pre-sim phase: NOT gated on manifold membership, NO
distinctness/forcing filter, NO cross-layer rules. classification =
"diagnostic_only" (hypothetical, unadmitted).

KNOWN-VALUE CROSS-CHECKS (each compared to its analytic value, recorded as
{invariant, computed, known, match}; match is COMPUTED, never hardcoded):
  - d(omega) == 0 (closed)                       [sympy diffgeom exterior deriv]
  - J^n nondegenerate: det(J) == 1               [torch]
  - J^2 == -I (compatible complex structure)     [torch]
  - Pfaffian(J)^2 == det(J), |Pf(J)| == 1        [sympy exact]
  - Darboux: ||P^T A P - J|| == 0 for generic A  [torch]
  - Sp(2n): ||M^T J M - J|| == 0, det(M) == 1    [torch]
  - Liouville coeff |omega^n / n!| == 1          [sympy diffgeom wedge n<=2 +
                                                  Pfaffian theorem all n]
  - nondegeneracy: (exists v!=0 : Jv=0) is UNSAT [z3 + cvc5]
  - J in SkewSymmetric(2n); -J^2 in SPD(2n)      [geomstats, pytorch backend]
  - clifford Cl(2) bivector B=e1e2, B^2==-1, acts as J on R^2   [clifford]
  - symplectic-orthogonal U(1)=SO(2) is a genuine SO(3) element [e3nn]
  - Darboux pairing graph is a perfect matching (n pairs)       [rustworkx]
  - pairing complex Betti: H0==n, H1==0                         [gudhi]
  - Hodge L0 kernel dim == b0 == n                              [toponetx]

TOOLS (all load-bearing in the execution path):
  - torch     : ALL symplectic linear algebra in float64 (J, det, J^2, exp of
                Hamiltonian generators, Darboux symplectic Gram-Schmidt, M^T J M).
  - sympy     : EXACT symbolic exterior derivative d(omega)=0 (diffgeom), exact
                Pfaffian^2==det, and the Liouville wedge-power coefficient
                omega^n/n! (diffgeom WedgeProduct). Numeric torch cannot prove the
                exact closed/Pfaffian identities.
  - z3        : SMT nondegeneracy certificate -- (exists nonzero v : J v = 0) is
                UNSAT for the standard form; SAT for the degenerate negative.
  - cvc5      : independent SMT family certifying the same nondegeneracy fact and
                separating the degenerate negative (SAT).
  - clifford  : Cl(2) unit bivector B=e1*e2 with B^2=-1 realizes the compatible
                complex structure J on R^2 (n=1): the symplectic form's matrix.
  - e3nn      : the symplectic-orthogonal subgroup U(n)=Sp(2n)/\\O(2n) at n=1 is
                SO(2); e3nn certifies the embedded rotation is a genuine SO(3)
                element (l=1 angle round-trip).
  - geomstats : (pytorch backend) certifies J in SkewSymmetric(2n) and the
                compatible Kahler metric -J^2 in SPD(2n).
  - rustworkx : the Darboux conjugate-pair structure (q_i<->p_i) is exactly a
                perfect matching on 2n vertices; certified by max-weight matching.
  - gudhi     : persistent homology of the pairing complex gives Betti H0=n
                (n conjugate-pair components), H1=0 (a matching is a forest).
  - toponetx  : Hodge 0-Laplacian of the pairing complex has kernel dim = b0 = n
                (independent Hodge-spectral confirmation of the same topology).

WIDE VARIATION: n in {1, 2, 3}; multiple random nondegenerate skew forms (seeds)
for the Darboux test; multiple random Hamiltonian generators (seeds) for the
Sp(2n) test; a sweep of symplectic-flow times.

NEGATIVES (each must KILL the symplectic signature):
  - degenerate 2-form: omega^n == 0 (det == 0, Pfaffian == 0), NOT symplectic;
    nondegeneracy SMT flips to SAT (a nonzero null vector exists).
  - non-closed 2-form: alpha with d(alpha) != 0 (sympy exterior derivative
    nonzero), NOT a symplectic form.
  - flattened/collapsed form: the zero form, which is both degenerate and (as a
    matching graph) has no conjugate pairs (empty matching, all-isolated complex).

finite_map: (canonical R^{2n}, n in {1,2,3}) -> (standard symplectic form J,
its closedness d(omega), nondegeneracy det/Pfaffian, Darboux symplectic basis,
Sp(2n) preservation, Liouville volume, conjugate-pair graph/complex invariants)
"""

from __future__ import annotations

import json
import math
import os
import pathlib
from typing import Any

os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")

import numpy as np
import sympy as sp
import torch
import z3
import cvc5
from cvc5 import Kind
from clifford import Cl
from e3nn import o3
import rustworkx as rx
import gudhi
import geomstats.backend as gs
from geomstats.geometry.skew_symmetric_matrices import SkewSymmetricMatrices
from geomstats.geometry.spd_matrices import SPDMatrices
from sympy.diffgeom import Manifold, Patch, CoordSystem, WedgeProduct, Differential
from toponetx import SimplicialComplex

torch.set_default_dtype(torch.float64)

RTYPE = torch.float64
TOL = 1.0e-9            # tolerance for direct float64 numeric invariants
TOL_E3NN = 1.0e-5       # e3nn runs float32 internally
N_VALUES = [1, 2, 3]
SEEDS = [0, 1, 2, 3, 4]
FLOW_TIMES = [0.1, 0.3, 0.7, 1.0, 1.5]
ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "geom_symplectic_structure_deep_probe"


# --------------------------------------------------------------------------- #
# Core symplectic geometry (torch, load-bearing)                              #
# --------------------------------------------------------------------------- #
def std_J(n: int) -> torch.Tensor:
    """Standard symplectic form J on R^{2n}: [[0, I],[-I, 0]], omega(u,v)=u^T J v."""
    Z = torch.zeros(n, n, dtype=RTYPE)
    I = torch.eye(n, dtype=RTYPE)
    return torch.cat([torch.cat([Z, I], dim=1), torch.cat([-I, Z], dim=1)], dim=0)


def pfaffian(M: torch.Tensor) -> float:
    """Pfaffian of an even-dimensional skew-symmetric matrix via the exact
    recursive (first-row) cofactor expansion. Pf(J)^2 == det(J)."""
    m = M.shape[0]
    if m == 0:
        return 1.0
    if m == 2:
        return float(M[0, 1].item())
    res = 0.0
    for j in range(1, m):
        sign = (-1) ** (j - 1)
        keep = [r for r in range(m) if r != 0 and r != j]
        sub = M[keep][:, keep]
        res += sign * float(M[0, j].item()) * pfaffian(sub)
    return res


def random_nondegenerate_skew(n: int, seed: int) -> torch.Tensor:
    """A generic skew-symmetric 2n x 2n form A = G - G^T (generically
    nondegenerate); resampled until |det| is comfortably nonzero."""
    g = torch.Generator().manual_seed(1000 * n + seed)
    for _ in range(50):
        G = torch.randn(2 * n, 2 * n, generator=g, dtype=RTYPE)
        A = G - G.T
        if abs(torch.det(A).item()) > 1e-3:
            return A
    raise RuntimeError("could not sample nondegenerate skew form")


def symplectic_basis(A: torch.Tensor, n: int) -> torch.Tensor:
    """Darboux symplectic Gram-Schmidt: find basis P with P^T A P == std_J(n).
    Builds conjugate pairs (e_i, f_i) with omega(e_i, f_i) = 1, symplectically
    orthogonalizing each new candidate against the pairs already chosen."""
    n2 = 2 * n
    basis_e: list[torch.Tensor] = []
    basis_f: list[torch.Tensor] = []
    candidates = [torch.eye(n2, dtype=RTYPE)[:, i].clone() for i in range(n2)]

    def sympl_orth(v: torch.Tensor) -> torch.Tensor:
        w = v.clone()
        for ee, ff in zip(basis_e, basis_f):
            w = w - (w @ A @ ff) * ee + (w @ A @ ee) * ff
        return w

    while len(basis_e) < n:
        e = None
        for cand in candidates:
            v = sympl_orth(cand)
            if torch.linalg.vector_norm(v) > 1e-9:
                e = v
                break
        f = None
        for cand in candidates:
            w = sympl_orth(cand)
            pair = (e @ A @ w).item()
            if abs(pair) > 1e-9:
                f = w / pair
                break
        basis_e.append(e)
        basis_f.append(f)
    # column order: e_1..e_n, f_1..f_n  ->  P^T A P = [[0,I],[-I,0]] = std_J
    return torch.stack(basis_e + basis_f, dim=1)


def hamiltonian_generator(n: int, seed: int) -> torch.Tensor:
    """An element of the symplectic Lie algebra sp(2n,R): X with X^T J + J X = 0.
    Constructed as X = J^{-1} S with S symmetric (the standard sp(2n) parametriz.)."""
    n2 = 2 * n
    J = std_J(n)
    g = torch.Generator().manual_seed(7000 * n + seed)
    S = torch.randn(n2, n2, generator=g, dtype=RTYPE)
    S = (S + S.T) / 2
    return torch.linalg.solve(J, S)


# --------------------------------------------------------------------------- #
# sympy: exact closedness (exterior derivative) + Pfaffian + Liouville wedge   #
# --------------------------------------------------------------------------- #
def sympy_closed_and_liouville(n: int) -> dict[str, Any]:
    """sympy diffgeom: build omega = sum dp_i ^ dq_i, prove d(omega) == 0 (closed),
    and compute the Liouville coefficient omega^n / n! on the canonical frame.

    The wedge-power expansion is combinatorial; for n >= 3 it is expensive, so the
    direct diffgeom wedge coefficient is computed only for n <= 2, while the
    Pfaffian theorem (Liouville coeff == Pf(J)) supplies the value for all n."""
    import itertools

    n2 = 2 * n
    coords = [sp.Symbol(f"q{i}") for i in range(n)] + [sp.Symbol(f"p{i}") for i in range(n)]
    m = Manifold("M", n2)
    patch = Patch("P", m)
    cs = CoordSystem("C", patch, coords)
    oneforms = cs.base_oneforms()
    vecs = cs.base_vectors()
    dq = oneforms[:n]
    dp = oneforms[n:]
    omega = None
    for i in range(n):
        term = WedgeProduct(dp[i], dq[i])
        omega = term if omega is None else omega + term

    # exact exterior derivative: d(omega) is a 3-form; all components must vanish.
    d_omega = Differential(omega)
    closed = True
    for trip in itertools.combinations(range(n2), 3):
        comp = sp.simplify(d_omega(vecs[trip[0]], vecs[trip[1]], vecs[trip[2]]))
        if comp != 0:
            closed = False
            break

    # Liouville wedge coefficient omega^n / n! on the canonical frame (n <= 2).
    liouville_wedge_coeff = None
    if n <= 2:
        w = omega
        for _ in range(n - 1):
            w = WedgeProduct(w, omega)
        liouville_wedge_coeff = sp.nsimplify(w(*vecs) / sp.factorial(n))

    return {
        "n": n,
        "closed_d_omega_is_zero": bool(closed),
        "liouville_wedge_coeff": (str(liouville_wedge_coeff)
                                  if liouville_wedge_coeff is not None else None),
        "liouville_wedge_abs_is_one": (abs(int(liouville_wedge_coeff)) == 1
                                       if liouville_wedge_coeff is not None else None),
    }


def sympy_pfaffian_exact(n: int) -> dict[str, Any]:
    """Exact symbolic Pfaffian of the standard J: Pf(J)^2 == det(J), |Pf(J)| == 1."""
    J = sp.zeros(2 * n, 2 * n)
    for i in range(n):
        J[i, n + i] = 1
        J[n + i, i] = -1

    def pf_sym(M):
        mm = M.shape[0]
        if mm == 0:
            return sp.Integer(1)
        if mm == 2:
            return M[0, 1]
        res = sp.Integer(0)
        for j in range(1, mm):
            sign = (-1) ** (j - 1)
            keep = [r for r in range(mm) if r != 0 and r != j]
            sub = M[keep, keep]
            res += sign * M[0, j] * pf_sym(sub)
        return sp.simplify(res)

    pf = pf_sym(J)
    det = sp.det(J)
    return {
        "n": n,
        "pfaffian": str(pf),
        "det": str(det),
        "pf_squared_equals_det": bool(sp.simplify(pf ** 2 - det) == 0),
        "pf_abs_is_one": bool(sp.simplify(sp.Abs(pf) - 1) == 0),
    }


# --------------------------------------------------------------------------- #
# z3 / cvc5: nondegeneracy certificate (exists nonzero v : J v = 0) is UNSAT   #
# --------------------------------------------------------------------------- #
def z3_nondegeneracy(J: torch.Tensor) -> dict[str, Any]:
    """A skew form is NONDEGENERATE iff J v = 0 has no nonzero solution.
    We assert (J v == 0) AND (v != 0) and check: UNSAT == nondegenerate.
    Removing z3 removes this certificate."""
    n2 = J.shape[0]
    s = z3.Solver()
    v = [z3.Real(f"v{i}") for i in range(n2)]
    for i in range(n2):
        s.add(sum(z3.RealVal(repr(float(J[i, j].item()))) * v[j] for j in range(n2)) == 0)
    s.add(z3.Or([vi != 0 for vi in v]))
    status = str(s.check())
    return {"null_vector_status": status, "nondegenerate": status == "unsat"}


def cvc5_nondegeneracy(J: torch.Tensor) -> dict[str, Any]:
    """Independent SMT family (cvc5) certifying the same nondegeneracy fact:
    (exists nonzero v : J v = 0) is UNSAT for a nondegenerate form, SAT for a
    degenerate one."""
    n2 = J.shape[0]
    slv = cvc5.Solver()
    slv.setOption("produce-models", "true")
    slv.setLogic("QF_LRA")
    R = slv.getRealSort()
    v = [slv.mkConst(R, f"v{i}") for i in range(n2)]
    zero = slv.mkReal(0)

    def rv(x: float):
        frac = sp.Rational(x).limit_denominator(10 ** 9)
        num, den = sp.fraction(frac)
        return slv.mkReal(int(num), int(den)) if int(den) != 1 else slv.mkReal(int(num))

    for i in range(n2):
        terms = [slv.mkTerm(Kind.MULT, rv(float(J[i, j].item())), v[j])
                 for j in range(n2) if abs(float(J[i, j].item())) > 0]
        if not terms:
            continue
        lhs = terms[0]
        for t in terms[1:]:
            lhs = slv.mkTerm(Kind.ADD, lhs, t)
        slv.assertFormula(slv.mkTerm(Kind.EQUAL, lhs, zero))
    neq = [slv.mkTerm(Kind.DISTINCT, vi, zero) for vi in v]
    slv.assertFormula(slv.mkTerm(Kind.OR, *neq) if len(neq) > 1 else neq[0])
    res = slv.checkSat()
    status = "unsat" if res.isUnsat() else ("sat" if res.isSat() else "unknown")
    return {"null_vector_status": status, "nondegenerate": res.isUnsat()}


# --------------------------------------------------------------------------- #
# clifford Cl(2): unit bivector B = e1 e2 realizes the compatible complex       #
# structure J on R^2 (n = 1)                                                    #
# --------------------------------------------------------------------------- #
def clifford_complex_structure() -> dict[str, Any]:
    """In Cl(2), the unit bivector B = e1*e2 satisfies B^2 = -1 and its right
    action on R^2 is the compatible complex structure J = std_J(1) (up to sign):
    e1 -> e2, e2 -> -e1. The even subalgebra Cl^+(2) == C realizes J."""
    layout, blades = Cl(2)
    e1, e2 = blades["e1"], blades["e2"]
    B = e1 * e2
    b_squared = float((B * B).value[0])  # scalar part of B^2
    M = torch.zeros(2, 2, dtype=RTYPE)
    for j, ej in enumerate((e1, e2)):
        r = ej * B  # right-multiply: the complex-structure action
        for i, ei in enumerate((e1, e2)):
            M[i, j] = float((r * ei).value[0])
    Jstd = std_J(1)
    # the bivector action equals +/- J (sign is the right/left convention)
    matches_J = (torch.linalg.matrix_norm(M - Jstd).item() < TOL
                 or torch.linalg.matrix_norm(M + Jstd).item() < TOL)
    return {
        "bivector_squared": b_squared,
        "bivector_is_complex_unit": abs(b_squared + 1.0) < TOL,
        "bivector_action_matrix": [[float(x) for x in row] for row in M],
        "action_equals_pm_J": bool(matches_J),
    }


# --------------------------------------------------------------------------- #
# e3nn: symplectic-orthogonal U(1) = SO(2) embeds as a genuine SO(3) element    #
# --------------------------------------------------------------------------- #
def e3nn_symplectic_orthogonal_so3(theta: float) -> dict[str, Any]:
    """U(n) = Sp(2n,R) \\cap O(2n). For n=1 this is SO(2): a planar rotation that
    preserves J(1). Embed it in SO(3) and certify it via e3nn's l=1 angle
    round-trip (matrix_to_angles -> angles_to_matrix)."""
    Rot2 = torch.tensor([[math.cos(theta), -math.sin(theta)],
                         [math.sin(theta), math.cos(theta)]], dtype=RTYPE)
    J = std_J(1)
    preserves_J = float(torch.linalg.matrix_norm(Rot2.T @ J @ Rot2 - J).item())
    R3 = torch.eye(3, dtype=RTYPE)
    R3[:2, :2] = Rot2
    R3f = R3.to(torch.float32)
    det = float(torch.det(R3f).item())
    orth = float(torch.linalg.matrix_norm(R3f @ R3f.T - torch.eye(3)).item())
    if abs(det - 1.0) >= TOL_E3NN or orth >= TOL_E3NN:
        return {"preserves_J": preserves_J, "det": det, "orthogonality_defect": orth,
                "e3nn_reconstruction_err": None, "pass": False}
    a, b, c = o3.matrix_to_angles(R3f)
    Rrec = o3.angles_to_matrix(a, b, c)
    recon_err = float(torch.linalg.matrix_norm(Rrec - R3f).item())
    return {
        "preserves_J": preserves_J, "det": det, "orthogonality_defect": orth,
        "e3nn_reconstruction_err": recon_err,
        "pass": (preserves_J < TOL and abs(det - 1.0) < TOL_E3NN
                 and orth < TOL_E3NN and recon_err < TOL_E3NN),
    }


# --------------------------------------------------------------------------- #
# geomstats (pytorch backend): J in Skew(2n); compatible metric -J^2 in SPD     #
# --------------------------------------------------------------------------- #
def geomstats_skew_and_spd(J: torch.Tensor, n: int) -> dict[str, Any]:
    n2 = 2 * n
    skew = SkewSymmetricMatrices(n2)
    j_in_skew = bool(skew.belongs(gs.array(J.cpu().numpy())))
    metric = -(J @ J)  # = I_{2n}, the compatible Kahler metric g(u,v)=omega(u,Jv)
    spd = SPDMatrices(n2)
    metric_in_spd = bool(spd.belongs(gs.array(metric.cpu().numpy())))
    return {
        "J_in_skew_symmetric": j_in_skew,
        "compatible_metric_in_spd": metric_in_spd,
        "metric_is_identity": bool(torch.linalg.matrix_norm(metric - torch.eye(n2)).item() < TOL),
    }


# --------------------------------------------------------------------------- #
# Conjugate-pair graph / complex topology (rustworkx, gudhi, toponetx)         #
# --------------------------------------------------------------------------- #
def pairing_edges(J: torch.Tensor) -> list[tuple[int, int]]:
    """Edges (i,j) with J[i,j] != 0: the conjugate-pair (q_i <-> p_i) structure."""
    n2 = J.shape[0]
    edges = []
    for i in range(n2):
        for j in range(i + 1, n2):
            if abs(J[i, j].item()) > 1e-12:
                edges.append((i, j))
    return edges


def rustworkx_perfect_matching(J: torch.Tensor, n: int) -> dict[str, Any]:
    """The Darboux conjugate-pair structure is a PERFECT MATCHING on 2n vertices:
    n disjoint q_i--p_i edges, every vertex degree 1. rustworkx's max-weight
    matching returns exactly the n canonical conjugate pairs."""
    n2 = 2 * n
    edges = pairing_edges(J)
    G = rx.PyGraph()
    G.add_nodes_from(list(range(n2)))
    for (i, j) in edges:
        G.add_edge(i, j, abs(J[i, j].item()))
    m = rx.max_weight_matching(G, max_cardinality=True)
    degs = [G.degree(v) for v in range(n2)]
    is_perfect = len(m) == n and all(d == 1 for d in degs) and len(edges) == n
    return {
        "n_edges": len(edges),
        "matching_size": len(m),
        "all_degree_one": all(d == 1 for d in degs),
        "is_perfect_matching": bool(is_perfect),
        "matched_pairs": sorted(tuple(sorted(e)) for e in m),
    }


def gudhi_pairing_homology(J: torch.Tensor, n: int) -> dict[str, Any]:
    """Persistent homology of the conjugate-pair complex (n disjoint edges):
    Betti H0 = n (n conjugate-pair components), H1 = 0 (a matching is a forest)."""
    n2 = 2 * n
    st = gudhi.SimplexTree()
    for v in range(n2):
        st.insert([v])
    for (i, j) in pairing_edges(J):
        st.insert([i, j])
    st.compute_persistence(persistence_dim_max=True)
    betti = st.betti_numbers()
    b0 = betti[0] if len(betti) > 0 else 0
    b1 = betti[1] if len(betti) > 1 else 0
    return {
        "betti": list(betti),
        "b0": int(b0), "b1": int(b1),
        "b0_equals_n": int(b0) == n,
        "b1_is_zero": int(b1) == 0,
    }


def toponetx_hodge_b0(J: torch.Tensor, n: int) -> dict[str, Any]:
    """Hodge 0-Laplacian of the conjugate-pair simplicial complex: dim ker L0 = b0
    = number of connected components = n. Independent Hodge-spectral confirmation
    of the same topology gudhi gives via persistent homology."""
    n2 = 2 * n
    edges = pairing_edges(J)
    SC = SimplicialComplex()
    for v in range(n2):
        SC.add_simplex([v])
    for (i, j) in edges:
        SC.add_simplex([i, j])
    if len(edges) == 0:
        # A 0-dimensional complex (no edges): the Hodge 0-Laplacian L0 = B1 B1^T is
        # the zero matrix (no coboundary), so every vertex is in its kernel.
        L0d = torch.zeros(n2, n2, dtype=RTYPE)
    else:
        L0 = SC.hodge_laplacian_matrix(rank=0)
        L0d = torch.tensor(np.asarray(L0.todense()), dtype=RTYPE)
    evals = torch.linalg.eigvalsh(L0d)
    ker_dim = int((evals.abs() < 1e-9).sum().item())
    return {
        "hodge_L0_shape": list(L0d.shape),
        "hodge_L0_kernel_dim": ker_dim,
        "kernel_dim_equals_n": ker_dim == n,
    }


# --------------------------------------------------------------------------- #
# Per-n geometry block (torch core)                                           #
# --------------------------------------------------------------------------- #
def geometry_block(n: int) -> dict[str, Any]:
    n2 = 2 * n
    J = std_J(n)
    det = float(torch.det(J).item())
    pf = pfaffian(J)
    j_sq_defect = float(torch.linalg.matrix_norm(J @ J + torch.eye(n2)).item())

    # Darboux over multiple random nondegenerate skew forms.
    darboux_errs = []
    for seed in SEEDS:
        A = random_nondegenerate_skew(n, seed)
        P = symplectic_basis(A, n)
        Jrec = P.T @ A @ P
        darboux_errs.append(float(torch.linalg.matrix_norm(Jrec - J).item()))

    # Sp(2n) preservation over multiple Hamiltonian generators x flow times.
    sp_preserve_errs = []
    sp_det_errs = []
    lie_defects = []
    for seed in SEEDS:
        X = hamiltonian_generator(n, seed)
        lie_defects.append(float(torch.linalg.matrix_norm(X.T @ J + J @ X).item()))
        for t in FLOW_TIMES:
            M = torch.linalg.matrix_exp(t * X)
            sp_preserve_errs.append(float(torch.linalg.matrix_norm(M.T @ J @ M - J).item()))
            sp_det_errs.append(abs(float(torch.det(M).item()) - 1.0))

    return {
        "n": n, "dim": n2,
        "det_J": det,
        "pfaffian_J": pf,
        "pf_squared": pf * pf,
        "pf_squared_equals_det": abs(pf * pf - det) < TOL,
        "pf_abs_is_one": abs(abs(pf) - 1.0) < TOL,
        "j_squared_plus_I_defect": j_sq_defect,
        "j_squared_is_minus_I": j_sq_defect < TOL,
        "max_darboux_err": max(darboux_errs),
        "max_sp_preserve_err": max(sp_preserve_errs),
        "max_sp_det_err": max(sp_det_errs),
        "max_lie_algebra_defect": max(lie_defects),
        "n_darboux_forms": len(SEEDS),
        "n_sp_elements": len(SEEDS) * len(FLOW_TIMES),
    }


# --------------------------------------------------------------------------- #
# Negatives                                                                   #
# --------------------------------------------------------------------------- #
def negative_degenerate_form() -> dict[str, Any]:
    """A degenerate 2-form on R^2: omega = [[0,0],[0,0]] (the zero form). It has
    omega^n == 0 (det == 0, Pfaffian == 0) and a nonzero null vector exists, so
    the nondegeneracy SMT certificate FLIPS to SAT. NOT a symplectic form. We also
    test a rank-deficient skew form on R^4 (one conjugate pair missing)."""
    # zero form on R^2
    A0 = torch.zeros(2, 2, dtype=RTYPE)
    det0 = float(torch.det(A0).item())
    pf0 = pfaffian(A0)
    z3_0 = z3_nondegeneracy(A0)
    cvc5_0 = cvc5_nondegeneracy(A0)
    # rank-2 (degenerate) skew form on R^4: only the (0,1) pair, (2,3) missing
    A4 = torch.zeros(4, 4, dtype=RTYPE)
    A4[0, 1] = 1.0
    A4[1, 0] = -1.0
    det4 = float(torch.det(A4).item())
    pf4 = pfaffian(A4)
    z3_4 = z3_nondegeneracy(A4)
    return {
        "zero_form_det": det0, "zero_form_pfaffian": pf0,
        "zero_form_omega_n_is_zero": abs(det0) < TOL and abs(pf0) < TOL,
        "zero_form_z3_null_vector_status": z3_0["null_vector_status"],
        "zero_form_cvc5_null_vector_status": cvc5_0["null_vector_status"],
        "rank_deficient_det": det4, "rank_deficient_pfaffian": pf4,
        "rank_deficient_omega_n_is_zero": abs(det4) < TOL and abs(pf4) < TOL,
        "rank_deficient_z3_null_vector_status": z3_4["null_vector_status"],
        # the negative KILLS the signature: degenerate (det==0/pf==0) AND the
        # nondegeneracy certificate is SAT (a null vector exists) for both solvers.
        "kills_signature": (abs(det0) < TOL and abs(pf0) < TOL
                            and z3_0["null_vector_status"] == "sat"
                            and cvc5_0["null_vector_status"] == "sat"
                            and abs(det4) < TOL and z3_4["null_vector_status"] == "sat"),
    }


def negative_non_closed_form() -> dict[str, Any]:
    """A non-closed 2-form on R^4: alpha = q0 * (dp0 ^ dq1) has d(alpha) != 0, so
    it is NOT a symplectic form even though its matrix can be nondegenerate at a
    point. sympy's exterior derivative is nonzero on at least one 3-frame."""
    import itertools
    n2 = 4
    coords = list(sp.symbols("q0 q1 p0 p1"))
    m = Manifold("Mneg", n2)
    patch = Patch("Pneg", m)
    cs = CoordSystem("Cneg", patch, coords)
    q0 = cs.coord_functions()[0]
    oneforms = cs.base_oneforms()
    vecs = cs.base_vectors()
    dq0, dq1, dp0, dp1 = oneforms
    alpha = q0 * WedgeProduct(dp0, dq1)
    d_alpha = Differential(alpha)
    nonzero_components = []
    for trip in itertools.combinations(range(n2), 3):
        comp = sp.simplify(d_alpha(vecs[trip[0]], vecs[trip[1]], vecs[trip[2]]))
        if comp != 0:
            nonzero_components.append([list(trip), str(comp)])
    return {
        "form": "q0 * (dp0 ^ dq1)",
        "d_alpha_nonzero_components": nonzero_components,
        "is_non_closed": len(nonzero_components) > 0,
        # KILLS the symplectic signature: d(alpha) != 0 means not closed.
        "kills_signature": len(nonzero_components) > 0,
    }


def negative_flattened_form() -> dict[str, Any]:
    """A flattened/collapsed form: the zero form on R^4. As a conjugate-pair graph
    it has NO edges -> empty matching (no conjugate pairs), and as a complex it is
    all isolated vertices (b0 = 2n != n). The Darboux/pairing structure is gone."""
    n = 2
    A = torch.zeros(2 * n, 2 * n, dtype=RTYPE)
    rw = rustworkx_perfect_matching(A, n)
    gd = gudhi_pairing_homology(A, n)
    tp = toponetx_hodge_b0(A, n)
    return {
        "n_edges": rw["n_edges"],
        "matching_size": rw["matching_size"],
        "no_conjugate_pairs": rw["n_edges"] == 0 and rw["matching_size"] == 0,
        "betti_b0": gd["b0"],
        "b0_is_2n_not_n": gd["b0"] == 2 * n and gd["b0"] != n,
        "hodge_kernel_dim": tp["hodge_L0_kernel_dim"],
        # KILLS the signature: no perfect matching (no conjugate pairs) and the
        # collapsed complex has b0 = 2n (all isolated), not n.
        "kills_signature": (rw["n_edges"] == 0 and rw["matching_size"] == 0
                            and gd["b0"] == 2 * n and tp["hodge_L0_kernel_dim"] == 2 * n),
    }


# --------------------------------------------------------------------------- #
# Known-value cross-checks                                                     #
# --------------------------------------------------------------------------- #
def build_known_value_checks(
    blocks: dict[int, dict[str, Any]],
    sym_closed: dict[int, dict[str, Any]],
    sym_pf: dict[int, dict[str, Any]],
    z3_rows: dict[int, dict[str, Any]],
    cvc5_rows: dict[int, dict[str, Any]],
    geo_rows: dict[int, dict[str, Any]],
    rw_rows: dict[int, dict[str, Any]],
    gd_rows: dict[int, dict[str, Any]],
    tp_rows: dict[int, dict[str, Any]],
    cliff: dict[str, Any],
    e3: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    for n in N_VALUES:
        b = blocks[n]
        sc = sym_closed[n]
        spf = sym_pf[n]

        checks.append({
            "invariant": f"n={n}: closed d(omega)==0 (sympy exterior derivative)",
            "computed": str(sc["closed_d_omega_is_zero"]),
            "known": "True", "match": bool(sc["closed_d_omega_is_zero"])})
        checks.append({
            "invariant": f"n={n}: nondegenerate det(J)",
            "computed": f"{b['det_J']:.15f}",
            "known": "1", "match": abs(b["det_J"] - 1.0) < TOL})
        checks.append({
            "invariant": f"n={n}: J^2 == -I (compatible complex structure)",
            "computed": f"||J^2 + I|| = {b['j_squared_plus_I_defect']:.2e}",
            "known": "0", "match": b["j_squared_is_minus_I"]})
        checks.append({
            "invariant": f"n={n}: Pfaffian(J)^2 == det(J) (sympy exact)",
            "computed": f"pf={spf['pfaffian']}, pf^2-det reduces to 0: {spf['pf_squared_equals_det']}",
            "known": "True", "match": bool(spf["pf_squared_equals_det"])})
        checks.append({
            "invariant": f"n={n}: |Pfaffian(J)| == 1 (sympy exact)",
            "computed": str(spf["pf_abs_is_one"]),
            "known": "True", "match": bool(spf["pf_abs_is_one"])})
        checks.append({
            "invariant": f"n={n}: Pfaffian(J)^2 == det(J) (torch numeric)",
            "computed": f"pf^2={b['pf_squared']:.6f}, det={b['det_J']:.6f}",
            "known": "equal", "match": b["pf_squared_equals_det"]})
        checks.append({
            "invariant": f"n={n}: Darboux ||P^T A P - J|| over {b['n_darboux_forms']} random skew forms",
            "computed": f"max {b['max_darboux_err']:.2e}",
            "known": "0", "match": b["max_darboux_err"] < TOL})
        checks.append({
            "invariant": f"n={n}: Sp(2n) preserves omega ||M^T J M - J|| over {b['n_sp_elements']} elements",
            "computed": f"max {b['max_sp_preserve_err']:.2e}",
            "known": "0", "match": b["max_sp_preserve_err"] < TOL})
        checks.append({
            "invariant": f"n={n}: Sp(2n) volume-preserving |det(M) - 1|",
            "computed": f"max {b['max_sp_det_err']:.2e}",
            "known": "0", "match": b["max_sp_det_err"] < TOL})
        # Liouville: |omega^n / n!| == 1. n<=2 has direct diffgeom wedge coeff;
        # all n have the Pfaffian-theorem value (Liouville coeff == Pf(J)).
        if sc["liouville_wedge_coeff"] is not None:
            checks.append({
                "invariant": f"n={n}: Liouville |omega^n/n!| (sympy diffgeom wedge)",
                "computed": f"coeff={sc['liouville_wedge_coeff']}",
                "known": "+/-1", "match": bool(sc["liouville_wedge_abs_is_one"])})
        checks.append({
            "invariant": f"n={n}: Liouville coeff == Pfaffian(J), |coeff| == 1",
            "computed": f"|pf|={abs(b['pfaffian_J']):.6f}",
            "known": "1", "match": abs(abs(b["pfaffian_J"]) - 1.0) < TOL})
        checks.append({
            "invariant": f"n={n}: nondegeneracy (exists v!=0:Jv=0) UNSAT (z3)",
            "computed": z3_rows[n]["null_vector_status"],
            "known": "unsat", "match": z3_rows[n]["nondegenerate"]})
        checks.append({
            "invariant": f"n={n}: nondegeneracy (exists v!=0:Jv=0) UNSAT (cvc5)",
            "computed": cvc5_rows[n]["null_vector_status"],
            "known": "unsat", "match": cvc5_rows[n]["nondegenerate"]})
        checks.append({
            "invariant": f"n={n}: J in SkewSymmetric(2n) (geomstats)",
            "computed": str(geo_rows[n]["J_in_skew_symmetric"]),
            "known": "True", "match": bool(geo_rows[n]["J_in_skew_symmetric"])})
        checks.append({
            "invariant": f"n={n}: compatible metric -J^2 in SPD(2n) (geomstats)",
            "computed": str(geo_rows[n]["compatible_metric_in_spd"]),
            "known": "True", "match": bool(geo_rows[n]["compatible_metric_in_spd"])})
        checks.append({
            "invariant": f"n={n}: Darboux pairing graph is perfect matching, {n} pairs (rustworkx)",
            "computed": f"matching_size={rw_rows[n]['matching_size']}, perfect={rw_rows[n]['is_perfect_matching']}",
            "known": f"{n}", "match": rw_rows[n]["is_perfect_matching"] and rw_rows[n]["matching_size"] == n})
        checks.append({
            "invariant": f"n={n}: pairing complex Betti H0 (gudhi)",
            "computed": str(gd_rows[n]["b0"]),
            "known": f"{n}", "match": gd_rows[n]["b0_equals_n"]})
        checks.append({
            "invariant": f"n={n}: pairing complex Betti H1 (gudhi)",
            "computed": str(gd_rows[n]["b1"]),
            "known": "0", "match": gd_rows[n]["b1_is_zero"]})
        checks.append({
            "invariant": f"n={n}: Hodge L0 kernel dim == b0 (toponetx)",
            "computed": str(tp_rows[n]["hodge_L0_kernel_dim"]),
            "known": f"{n}", "match": tp_rows[n]["kernel_dim_equals_n"]})

    # n=1-only tool checks (clifford complex structure, e3nn SO(2)->SO(3))
    checks.append({
        "invariant": "n=1: clifford Cl(2) bivector B=e1e2, B^2 == -1",
        "computed": f"B^2={cliff['bivector_squared']:.6f}",
        "known": "-1", "match": cliff["bivector_is_complex_unit"]})
    checks.append({
        "invariant": "n=1: clifford bivector action == +/- J (compatible complex structure)",
        "computed": str(cliff["action_equals_pm_J"]),
        "known": "True", "match": bool(cliff["action_equals_pm_J"])})
    checks.append({
        "invariant": "n=1: symplectic-orthogonal U(1)=SO(2) preserves J & is genuine SO(3) (e3nn)",
        "computed": (f"preserves_J={e3['preserves_J']:.2e}, det={e3['det']:.6f}, "
                     f"recon={e3['e3nn_reconstruction_err']:.2e}"),
        "known": "preserves J, det=1, reconstructs (genuine SO(3))", "match": e3["pass"]})

    aux = {
        "clifford_complex_structure": cliff,
        "e3nn_symplectic_orthogonal": e3,
        "per_n_geometry": blocks,
    }
    return checks, aux


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    blocks = {n: geometry_block(n) for n in N_VALUES}
    sym_closed = {n: sympy_closed_and_liouville(n) for n in N_VALUES}
    sym_pf = {n: sympy_pfaffian_exact(n) for n in N_VALUES}
    z3_rows = {n: z3_nondegeneracy(std_J(n)) for n in N_VALUES}
    cvc5_rows = {n: cvc5_nondegeneracy(std_J(n)) for n in N_VALUES}
    geo_rows = {n: geomstats_skew_and_spd(std_J(n), n) for n in N_VALUES}
    rw_rows = {n: rustworkx_perfect_matching(std_J(n), n) for n in N_VALUES}
    gd_rows = {n: gudhi_pairing_homology(std_J(n), n) for n in N_VALUES}
    tp_rows = {n: toponetx_hodge_b0(std_J(n), n) for n in N_VALUES}
    cliff = clifford_complex_structure()
    e3 = e3nn_symplectic_orthogonal_so3(math.pi / 3)

    kvc, kvc_aux = build_known_value_checks(
        blocks, sym_closed, sym_pf, z3_rows, cvc5_rows, geo_rows,
        rw_rows, gd_rows, tp_rows, cliff, e3)

    # Negatives.
    neg_degenerate = negative_degenerate_form()
    neg_non_closed = negative_non_closed_form()
    neg_flattened = negative_flattened_form()
    negatives = {
        "degenerate_2form": {"detail": neg_degenerate, "kills_signature": neg_degenerate["kills_signature"]},
        "non_closed_2form": {"detail": neg_non_closed, "kills_signature": neg_non_closed["kills_signature"]},
        "flattened_collapsed_form": {"detail": neg_flattened, "kills_signature": neg_flattened["kills_signature"]},
    }

    known_values_all_match = all(c["match"] for c in kvc)
    negatives_all_kill = all(v["kills_signature"] for v in negatives.values())
    tools_all_pass = (
        all(z3_rows[n]["nondegenerate"] for n in N_VALUES)
        and all(cvc5_rows[n]["nondegenerate"] for n in N_VALUES)
        and all(sym_closed[n]["closed_d_omega_is_zero"] for n in N_VALUES)
        and all(sym_pf[n]["pf_squared_equals_det"] for n in N_VALUES)
        and all(geo_rows[n]["J_in_skew_symmetric"] and geo_rows[n]["compatible_metric_in_spd"] for n in N_VALUES)
        and all(rw_rows[n]["is_perfect_matching"] for n in N_VALUES)
        and all(gd_rows[n]["b0_equals_n"] and gd_rows[n]["b1_is_zero"] for n in N_VALUES)
        and all(tp_rows[n]["kernel_dim_equals_n"] for n in N_VALUES)
        and cliff["bivector_is_complex_unit"] and cliff["action_equals_pm_J"]
        and e3["pass"]
    )

    all_pass = known_values_all_match and negatives_all_kill and tools_all_pass

    blockers: list[str] = []
    if not known_values_all_match:
        blockers += [f"KNOWN-VALUE MISMATCH: {c['invariant']} computed={c['computed']} known={c['known']}"
                     for c in kvc if not c["match"]]
    if not all(z3_rows[n]["nondegenerate"] for n in N_VALUES):
        blockers.append("z3 nondegeneracy null-vector search not UNSAT for some n")
    if not all(cvc5_rows[n]["nondegenerate"] for n in N_VALUES):
        blockers.append("cvc5 nondegeneracy null-vector search not UNSAT for some n")
    if not negatives_all_kill:
        blockers += [f"NEGATIVE DID NOT KILL: {k}" for k, v in negatives.items() if not v["kills_signature"]]

    tool_manifest = {
        "torch": {"used": True, "role": "load_bearing",
                  "reason": "all symplectic linear algebra in float64: standard J, det/nondegeneracy, J^2=-I, matrix-exp of Hamiltonian sp(2n) generators, Darboux symplectic Gram-Schmidt basis (P^T A P == J), and M^T J M preservation"},
        "sympy": {"used": True, "role": "load_bearing",
                  "reason": "EXACT symbolic exterior derivative d(omega)=0 (diffgeom Differential), exact Pfaffian^2==det, and the Liouville wedge-power coefficient omega^n/n! (diffgeom WedgeProduct); numeric torch cannot prove the exact closed/Pfaffian identities, and the non-closed negative is detected by a nonzero d(alpha)"},
        "z3": {"used": True, "role": "load_bearing",
               "reason": "SMT nondegeneracy certificate: (exists nonzero v : J v = 0) is UNSAT for the standard form and SAT for the degenerate negative"},
        "cvc5": {"used": True, "role": "load_bearing",
                 "reason": "independent SMT family (QF_LRA) certifying the same nondegeneracy fact and separating the degenerate negative (SAT)"},
        "clifford": {"used": True, "role": "load_bearing",
                     "reason": "Cl(2) unit bivector B=e1*e2 has B^2=-1 and its action realizes the compatible complex structure J=std_J(1), i.e. the symplectic form's matrix for n=1"},
        "e3nn": {"used": True, "role": "load_bearing",
                 "reason": "certifies the symplectic-orthogonal subgroup U(1)=Sp(2)\\cap O(2)=SO(2) (preserving J) embeds as a genuine SO(3) element via the l=1 angle round-trip"},
        "geomstats": {"used": True, "role": "load_bearing",
                      "reason": "pytorch backend certifies J in SkewSymmetricMatrices(2n) (omega is a skew bilinear form) and the compatible Kahler metric -J^2 in SPDMatrices(2n)"},
        "rustworkx": {"used": True, "role": "load_bearing",
                      "reason": "certifies the Darboux conjugate-pair structure is a perfect matching on 2n vertices (n disjoint q_i--p_i edges); the collapsed negative has an empty matching"},
        "gudhi": {"used": True, "role": "load_bearing",
                  "reason": "persistent homology of the conjugate-pair complex gives Betti H0=n (n pair components) and H1=0 (a matching is a forest); the collapsed negative has H0=2n"},
        "toponetx": {"used": True, "role": "load_bearing",
                     "reason": "Hodge 0-Laplacian of the conjugate-pair complex has kernel dim = b0 = n; independent Hodge-spectral confirmation of the topology gudhi gives via persistence"},
    }

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID, "name": SIM_ID, "version": "1.0.0", "tier": "2_geometry",
        "classification": "diagnostic_only",
        "promotion_allowed": False,
        "promotion_status": "diagnostic_only",
        "sim_execution_kind": "nonclassical",
        "sim_class": "geometry_probe",
        "purpose": "Deep, standalone symplectic-structure geometry lego (the standard symplectic form omega = sum dp_i ^ dq_i on R^{2n}) computed in real torch with full tool integration, cross-checked against textbook analytic invariants. Lego/pre-sim phase: NOT gated on manifold membership.",
        "scientific_question": "Does the standard symplectic form J on R^{2n} (n in {1,2,3}) reproduce the known symplectic geometry -- closed (d omega = 0), nondegenerate (omega^n != 0, det/Pfaffian nonzero), Darboux-standard, Sp(2n)-preserved, with Liouville volume omega^n/n! and Pfaffian^2 = det -- to its exact analytic values, and do the degenerate / non-closed / collapsed controls kill that signature?",
        "claim_ceiling": "diagnostic_only / hypothetical / unadmitted: a self-contained known-math geometry lego. Does NOT admit any manifold layer, stacking, coupling, G-structure, Axis0, flux, bridge, QIT, or physics claim.",
        "finite_map": "(canonical R^{2n}, n in {1,2,3}) -> (standard symplectic form J=[[0,I],[-I,0]], closedness d(omega), nondegeneracy det(J)/Pfaffian(J), Darboux symplectic basis P with P^T A P=J, Sp(2n) preservation M^T J M=J, Liouville volume omega^n/n!, conjugate-pair perfect matching, pairing-complex Betti numbers, Hodge L0 kernel)",
        "domain": "even-dimensional real vector spaces R^{2n} for n in {1,2,3}; the standard symplectic form J; generic random nondegenerate skew forms A (for Darboux); symplectic Lie-algebra generators X with X^T J + J X = 0 (for Sp(2n)); the conjugate-pair graph and simplicial complex of J",
        "codomain_or_output": "the symplectic invariants: det(J)=1, Pfaffian(J)=+/-1 with Pf^2=det, d(omega)=0, J^2=-I, Darboux congruence to J, Sp(2n)-preservation and det=1, Liouville coefficient |omega^n/n!|=1, perfect matching of n conjugate pairs, Betti (H0=n, H1=0), Hodge L0 kernel dim=n",
        "carrier_layer": "linear symplectic carrier (R^{2n}, omega): the even-dimensional partner of the contact structure; pure linear-symplectic / Darboux layer",
        "geometry_layer": "symplectic geometry: a closed nondegenerate skew 2-form omega = sum dp_i ^ dq_i; Sp(2n,R) structure group; compatible complex structure J^2=-I (Kahler triple with g=-J^2); Liouville volume omega^n/n!",
        "carrier_realization": "torch.float64 symplectic-form matrices, symplectic bases, and Sp(2n) group/algebra elements; no NumPy claim-bearing substrate (numpy appears only as a geomstats/toponetx adapter for membership/Laplacian readout), no label-only tensors, no random claim-matrices (random skew forms are genuine generic samples used to exhibit Darboux's theorem)",
        "spinor_state": "not_applicable_at_this_lego (linear symplectic structure; the clifford even subalgebra Cl^+(2)==C realizes the compatible complex structure J, but no spinor-derived density state is claimed)",
        "quaternion_action": "not_applicable (n=1 uses the complex unit bivector of Cl(2), not a quaternion map; no quaternion language is used as a load-bearing claim)",
        "peps3d_embedding": "not_applicable_at_lego_phase (no manifold anchor claimed; diagnostic_only)",
        "dependency_receipts": [],
        "downstream_blocks": ["manifold_layers", "stacking", "coupling", "G_structure", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "blocked_consumers": ["manifold_layers", "stacking", "coupling", "G_structure", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "law_or_candidate_tested": "the standard symplectic structure on R^{2n} (closed, nondegenerate skew 2-form; Darboux normal form; Sp(2n) invariance; Liouville volume; Pfaffian^2=det) against textbook analytic invariants",
        "branch_status_before_run": "lego/pre-sim phase; standalone known-math geometry; unadmitted",
        "allowed_claims": ["standalone known-math symplectic-structure geometry witness; computed invariants match textbook values to machine precision (numeric) and exactly (symbolic)"],
        "promotion_blockers": ["diagnostic_only by design (lego/pre-sim phase); no manifold membership, no cross-layer evidence, no coupling"],

        "result_summary": {
            "all_pass": all_pass,
            "known_values_all_match": known_values_all_match,
            "negatives_all_kill": negatives_all_kill,
            "tools_all_pass": tools_all_pass,
            "n_known_value_checks": len(kvc),
            "n_values": N_VALUES,
            "seeds": SEEDS,
            "flow_times": FLOW_TIMES,
            "z3_nondegeneracy_all_unsat": all(z3_rows[n]["nondegenerate"] for n in N_VALUES),
            "cvc5_nondegeneracy_all_unsat": all(cvc5_rows[n]["nondegenerate"] for n in N_VALUES),
            "promotion_allowed": False,
        },

        "known_value_checks": kvc,
        "known_value_aux": kvc_aux,
        "sympy_closed_and_liouville": sym_closed,
        "sympy_pfaffian_exact": sym_pf,
        "per_n_geometry_blocks": blocks,
        "nondegeneracy_certificates": {
            "z3": z3_rows, "cvc5": cvc5_rows,
        },
        "geomstats_skew_spd": geo_rows,
        "rustworkx_perfect_matching": rw_rows,
        "gudhi_pairing_homology": gd_rows,
        "toponetx_hodge_b0": tp_rows,
        "clifford_complex_structure": cliff,
        "e3nn_symplectic_orthogonal": e3,

        "required_negatives": ["degenerate_2form", "non_closed_2form", "flattened_collapsed_form"],
        "negatives_run": list(negatives.keys()),
        "negatives": negatives,
        "kill_conditions": [
            "any known-value invariant fails to match its textbook value",
            "z3 or cvc5 nondegeneracy null-vector search not UNSAT for the standard form",
            "degenerate form retains nondegeneracy (det/Pfaffian nonzero or UNSAT null-vector)",
            "non-closed form has d(alpha) == 0 (would falsely look closed)",
            "collapsed form retains a perfect matching / pairing-complex b0 == n",
        ],

        "TOOL_MANIFEST": tool_manifest,
        "tool_manifest": tool_manifest,
        "TOOL_INTEGRATION_DEPTH": {k: "load_bearing" for k in tool_manifest},
        "proof_surfaces_used": ["z3", "cvc5", "sympy"],
        "graph_surfaces_used": ["rustworkx"],
        "topology_surfaces_used": ["gudhi", "toponetx"],
        "required_tools": ["torch", "sympy", "z3", "cvc5", "clifford", "e3nn", "geomstats", "rustworkx", "gudhi", "toponetx"],
        "actual_tools_used": ["torch", "sympy", "z3", "cvc5", "clifford", "e3nn", "geomstats", "rustworkx", "gudhi", "toponetx"],

        "required_artifacts": ["json_result_receipt", "witness_trace"],
        "artifacts_emitted": ["json_result_receipt", "witness_trace"],
        "witness_trace_id": f"{SIM_ID}_witness",

        "all_pass": all_pass,
        "blockers": blockers,
        "pass_rule": "every known_value_check matches its known value AND all negatives kill the signature AND z3+cvc5 nondegeneracy null-vector searches are UNSAT AND d(omega)=0 (closed) AND Pfaffian^2=det for all n",
        "fail_rule": "any known-value mismatch, any negative that does not kill, any non-UNSAT nondegeneracy certificate for the standard form, a non-closed standard omega, or Pfaffian^2 != det",
        "eligible_consumers": ["other diagnostic_only symplectic/contact geometry probes"],
    }

    witness = {
        "sim_id": SIM_ID,
        "steps": [
            {"step": "build_standard_symplectic_form_J", "n_values": N_VALUES},
            {"step": "torch_det_pfaffian_J2", "all_nondegenerate": all(abs(blocks[n]["det_J"] - 1.0) < TOL for n in N_VALUES)},
            {"step": "sympy_exterior_derivative_closed", "all_closed": all(sym_closed[n]["closed_d_omega_is_zero"] for n in N_VALUES)},
            {"step": "sympy_pfaffian_squared_equals_det", "all_match": all(sym_pf[n]["pf_squared_equals_det"] for n in N_VALUES)},
            {"step": "torch_darboux_symplectic_basis", "max_err": max(blocks[n]["max_darboux_err"] for n in N_VALUES)},
            {"step": "torch_Sp2n_preservation", "max_err": max(blocks[n]["max_sp_preserve_err"] for n in N_VALUES)},
            {"step": "sympy_liouville_wedge_coeff", "computed_n": [n for n in N_VALUES if sym_closed[n]["liouville_wedge_coeff"] is not None]},
            {"step": "z3_cvc5_nondegeneracy", "z3_all_unsat": all(z3_rows[n]["nondegenerate"] for n in N_VALUES),
             "cvc5_all_unsat": all(cvc5_rows[n]["nondegenerate"] for n in N_VALUES)},
            {"step": "geomstats_skew_spd", "all_pass": all(geo_rows[n]["J_in_skew_symmetric"] and geo_rows[n]["compatible_metric_in_spd"] for n in N_VALUES)},
            {"step": "clifford_complex_structure", "B_squared": cliff["bivector_squared"], "action_eq_J": cliff["action_equals_pm_J"]},
            {"step": "e3nn_symplectic_orthogonal_so3", "pass": e3["pass"]},
            {"step": "rustworkx_perfect_matching", "all_perfect": all(rw_rows[n]["is_perfect_matching"] for n in N_VALUES)},
            {"step": "gudhi_pairing_homology", "all_b0_eq_n": all(gd_rows[n]["b0_equals_n"] for n in N_VALUES)},
            {"step": "toponetx_hodge_b0", "all_ker_eq_n": all(tp_rows[n]["kernel_dim_equals_n"] for n in N_VALUES)},
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

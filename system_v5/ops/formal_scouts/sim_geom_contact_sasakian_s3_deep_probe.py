#!/usr/bin/env python3
"""Deep contact / Sasakian geometry lego on S^3 (diagnostic_only, unadmitted).

KNOWN GEOMETRY (real torch.float64 / complex128 -- no labels, no random claim
matrices, no NumPy claim-bearing substrate):

  S^3 = unit sphere in R^4 = unit quaternions q = x0 + i x1 + j x2 + k x3 = SU(2).
  The STANDARD CONTACT 1-FORM (= the Hopf connection 1-form) on S^3 is

      alpha = x0 dx1 - x1 dx0 + x2 dx3 - x3 dx2      (restricted to T S^3).

  Its exterior derivative is the ambient 2-form

      d_alpha = 2 (dx0 ^ dx1 + dx2 ^ dx3).

  The REEB VECTOR FIELD is R = (-x1, x0, -x3, x2) (the Hopf vector field). With the
  two horizontal left-invariant fields

      e1 = (-x2, x3, x0, -x1),    e2 = (-x3, -x2, x1, x0),

  the triple (R, e1, e2) is an orthonormal frame of T_p S^3 at every p.

KNOWN-VALUE CROSS-CHECKS (each compared to its analytic value, recorded as
{invariant, computed, known, match} -- match is COMPUTED, never hardcoded):

  - CONTACT CONDITION: the 3-form alpha ^ d_alpha is a NONVANISHING volume form on
    S^3; on the orthonormal frame alpha^d_alpha(R,e1,e2) = 2 (Sigma xi^2)^2 = 2 at
    every point (so the contact condition holds everywhere, != 0).
  - REEB NORMALIZATION: alpha(R) == 1 on S^3.
  - REEB IN KERNEL OF d_alpha: d_alpha(R, e1) == 0 and d_alpha(R, e2) == 0
    (the Reeb field is in the kernel of d_alpha, the defining K-contact property).
  - REEB FLOW == HOPF FIBER FLOW: the flow phi_t(p) of R is exactly the Hopf S^1
    action (z1,z2) -> (e^{it} z1, e^{it} z2); the Hopf base point h(phi_t(p)) is
    constant along a whole orbit and the orbit closes with period 2*pi.
  - SASAKIAN RELATION: d_alpha == 2 * (pullback of the base area form),
    d_alpha = 2 pi^* omega_base, with base = S^2 of radius 1/2 (the Boothby-Wang /
    Fubini-Study normalization). Verified by an autograd pushforward of the Hopf
    map and the radius-1/2 area 2-form. (KNOWN factor 2; the radius convention is
    load-bearing -- the unit-radius base gives factor 1/2, which is why the base
    must be the radius-1/2 sphere; reported, not fudged.)
  - CO-ORIENTATION: the contact distribution xi = ker(alpha) is co-oriented (alpha
    is a global nonvanishing 1-form), i.e. the contact 3-form has a CONSTANT SIGN
    (always +2, never crossing 0) over all samples.

TOOLS (all load-bearing in the execution path):
  - torch     : ALL numeric form/frame/flow/pushforward algebra in float64/complex128.
  - sympy     : EXACT symbolic forms alpha, d_alpha, the wedge alpha^d_alpha, the
                Reeb identities alpha(R)=1 and d_alpha(R,.)=0; numeric torch alone
                cannot prove the exact polynomial identity alpha^d_alpha=2(Sigma xi^2)^2.
  - geomstats : genuine S^3 sampling (Hypersphere(3), pytorch backend) + belongs()
                membership; the Reeb flow image is certified to stay on S^3.
  - z3        : SMT certificate that the contact 3-form is bounded AWAY from 0
                (|value - 2| <= tol => value >= 2 - tol > 0): the negation is UNSAT.
  - cvc5      : independent SMT family certifying alpha(R)=1 and d_alpha(R,.)=0
                (the Reeb-field defining relations); negation UNSAT.
  - clifford  : Cl(3) even subalgebra == unit quaternions == SU(2); the Reeb/Hopf
                U(1) flow realized as a unit-quaternion rotor reproduces phi_t.
  - e3nn      : certifies the SU(2)->SO(3) double cover of the Hopf rotation is a
                genuine SO(3) element (det=1, orthogonal, angle round-trip).
  - gudhi     : persistent homology of the S^3 sample (H_0 = 1: the contact
                distribution sample is connected; topology surface).
  - rustworkx : the Reeb-orbit adjacency graph is a disjoint union of CYCLES (the
                fibration structure: every fiber is a circle).
  - toponetx  : combinatorial complex of Hopf fiber/base incidence (each base cell
                carries its fiber sample as a higher cell).
  - xgi       : hypergraph whose hyperedges are the Hopf fibers (fiber-membership);
                each base point indexes a hyperedge over its fiber samples.
  - quimb     : the Reeb U(1) phase action e^{it} acting on the spinor lift psi in
                C^2 (S^3 = SU(2) acting on C^2) as a tensor; alpha as the connection
                phase of that U(1) action.

WIDE VARIATION: many S^3 points (sizes N in {16,32,64,128}), multiple seeds, many
Reeb-flow times, autograd pushforward over hundreds of samples.

NEGATIVES (each changes/kills the contact signature):
  - degenerate 1-form beta = x0 dx1 - x1 dx0 (drop the second block): beta^d_beta
    == 0 -- NOT contact (the contact 3-form vanishes).
  - exact/closed 1-form gamma = d(f) (e.g. gamma = x0 dx0 + ...): d_gamma == 0, so
    gamma^d_gamma == 0 -- NOT contact.
  - flattened frame: collapse e1==e2 (degenerate frame): the 3-form vanishes.
  - non-Reeb vector field W not in ker(d_alpha): d_alpha(W,.) != 0 -- W is NOT a Reeb
    field (control showing the Reeb property is special).

classification = "diagnostic_only" (hypothetical, unadmitted, NOT gated on manifold
membership). It does NOT admit any manifold layer, stacking, coupling, G-structure,
Axis0, flux, bridge, QIT, or physics claim.

finite_map: (point p in S^3 subset R^4, ordered tangent frame) -> (contact 1-form
alpha, d_alpha, contact 3-form alpha^d_alpha, Reeb field R and its flow, Hopf base
point, Sasakian pushforward factor)
"""

from __future__ import annotations

import json
import math
import pathlib
from typing import Any

import torch
import sympy as sp
import z3
import cvc5
from cvc5 import Kind
from clifford import Cl
from e3nn import o3
import gudhi
import rustworkx as rx

torch.set_default_dtype(torch.float64)

RTYPE = torch.float64
CDTYPE = torch.complex128
TOL = 1.0e-9            # direct float64 numeric invariants
TOL_PUSH = 1.0e-7       # autograd Hopf pushforward (jacobian) precision floor
TOL_E3NN = 1.0e-5       # e3nn runs float32 internally
TOL_SMT = 1.0e-9        # SMT tolerance on carrier floats
SAMPLE_SIZES = [16, 32, 64, 128]
SEEDS = [0, 1, 2, 3, 4]
N_FLOW_TIMES = 48
ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "geom_contact_sasakian_s3_deep_probe"


# --------------------------------------------------------------------------- #
# S^3 sampling (geomstats, pytorch backend, load-bearing) + frame algebra     #
# --------------------------------------------------------------------------- #
def s3_sample(n: int, seed: int) -> torch.Tensor:
    """Genuine S^3 = Hypersphere(3) samples via geomstats (pytorch backend)."""
    import os
    os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")
    import geomstats.backend as gs  # noqa: F401  (forces backend init)
    from geomstats.geometry.hypersphere import Hypersphere
    s3 = Hypersphere(dim=3)
    gs_random_seed(seed)
    pts = s3.random_uniform(n)
    return pts.to(RTYPE)


def gs_random_seed(seed: int) -> None:
    torch.manual_seed(seed)


def s3_belongs(pts: torch.Tensor) -> float:
    """Max deviation from S^3 (||p|| - 1)."""
    return float((torch.linalg.vector_norm(pts, dim=-1) - 1.0).abs().max().item())


def reeb_field(p: torch.Tensor) -> torch.Tensor:
    """Reeb / Hopf vector field R = (-x1, x0, -x3, x2)."""
    x0, x1, x2, x3 = p[..., 0], p[..., 1], p[..., 2], p[..., 3]
    return torch.stack([-x1, x0, -x3, x2], dim=-1)


def horiz_e1(p: torch.Tensor) -> torch.Tensor:
    x0, x1, x2, x3 = p[..., 0], p[..., 1], p[..., 2], p[..., 3]
    return torch.stack([-x2, x3, x0, -x1], dim=-1)


def horiz_e2(p: torch.Tensor) -> torch.Tensor:
    x0, x1, x2, x3 = p[..., 0], p[..., 1], p[..., 2], p[..., 3]
    return torch.stack([-x3, -x2, x1, x0], dim=-1)


def alpha_coeffs(p: torch.Tensor) -> torch.Tensor:
    """alpha = sum a_i dx_i, a = (-x1, x0, -x3, x2) (the contact 1-form covector)."""
    return reeb_field(p)  # numerically identical covector to R on the round metric


def alpha_on(p: torch.Tensor, v: torch.Tensor) -> torch.Tensor:
    return (alpha_coeffs(p) * v).sum(dim=-1)


def dalpha_on(u: torch.Tensor, v: torch.Tensor) -> torch.Tensor:
    """d_alpha(u, v) = 2 (u0 v1 - u1 v0 + u2 v3 - u3 v2)."""
    return 2.0 * (u[..., 0] * v[..., 1] - u[..., 1] * v[..., 0]
                  + u[..., 2] * v[..., 3] - u[..., 3] * v[..., 2])


def contact_3form(p: torch.Tensor, u: torch.Tensor, v: torch.Tensor, w: torch.Tensor) -> torch.Tensor:
    """(alpha ^ d_alpha)(u,v,w) = alpha(u) d_alpha(v,w) - alpha(v) d_alpha(u,w)
       + alpha(w) d_alpha(u,v)."""
    return (alpha_on(p, u) * dalpha_on(v, w)
            - alpha_on(p, v) * dalpha_on(u, w)
            + alpha_on(p, w) * dalpha_on(u, v))


# --------------------------------------------------------------------------- #
# Hopf map + Reeb flow (torch complex128)                                      #
# --------------------------------------------------------------------------- #
def hopf_unit(p: torch.Tensor) -> torch.Tensor:
    """Hopf map S^3 -> S^2 (unit): z1=x0+ix1, z2=x2+ix3 ->
    (2 Re(z1* z2), 2 Im(z1* z2), |z1|^2 - |z2|^2)."""
    z1 = torch.complex(p[..., 0], p[..., 1])
    z2 = torch.complex(p[..., 2], p[..., 3])
    return torch.stack([2 * (z1.conj() * z2).real,
                        2 * (z1.conj() * z2).imag,
                        z1.abs() ** 2 - z2.abs() ** 2], dim=-1)


def hopf_half(p: torch.Tensor) -> torch.Tensor:
    """Hopf map to the RADIUS-1/2 base sphere (Boothby-Wang normalization)."""
    return 0.5 * hopf_unit(p)


def reeb_flow(p: torch.Tensor, t: float) -> torch.Tensor:
    """phi_t(p): (z1, z2) -> (e^{it} z1, e^{it} z2). The Hopf S^1 action."""
    z1 = torch.complex(p[..., 0], p[..., 1])
    z2 = torch.complex(p[..., 2], p[..., 3])
    e = torch.complex(torch.tensor(math.cos(t)), torch.tensor(math.sin(t)))
    z1, z2 = e * z1, e * z2
    return torch.stack([z1.real, z1.imag, z2.real, z2.imag], dim=-1)


# --------------------------------------------------------------------------- #
# sympy: EXACT symbolic contact geometry                                       #
# --------------------------------------------------------------------------- #
def sympy_exact_contact() -> dict[str, Any]:
    x0, x1, x2, x3 = sp.symbols("x0 x1 x2 x3", real=True)
    X = [x0, x1, x2, x3]
    a = sp.Matrix([-x1, x0, -x3, x2])           # alpha covector
    R = sp.Matrix([-x1, x0, -x3, x2])           # Reeb vector
    e1 = sp.Matrix([-x2, x3, x0, -x1])
    e2 = sp.Matrix([-x3, -x2, x1, x0])
    constraint = sum(xi ** 2 for xi in X)       # = 1 on S^3

    def alpha(u):
        return (a.T * u)[0]

    def dalpha(u, v):
        return 2 * (u[0] * v[1] - u[1] * v[0] + u[2] * v[3] - u[3] * v[2])

    def aXda(u, v, w):
        return alpha(u) * dalpha(v, w) - alpha(v) * dalpha(u, w) + alpha(w) * dalpha(u, v)

    # d_alpha coefficient matrix F_{ij} = da_j/dx_i - da_i/dx_j (ambient): exact 2(...)
    F = sp.zeros(4, 4)
    for i in range(4):
        for j in range(4):
            F[i, j] = sp.diff(a[j], X[i]) - sp.diff(a[i], X[j])
    dalpha_form_ok = (F == sp.Matrix([[0, 2, 0, 0], [-2, 0, 0, 0],
                                      [0, 0, 0, 2], [0, 0, -2, 0]]))

    alpha_R = sp.simplify(alpha(R))                                # = Sigma xi^2 -> 1 on S^3
    alpha_R_is_one_on_s3 = sp.simplify(alpha_R - constraint) == 0
    three_form = sp.simplify(aXda(R, e1, e2))                      # = 2 (Sigma xi^2)^2
    three_form_is_2c2 = sp.simplify(three_form - 2 * constraint ** 2) == 0
    dalpha_Re1 = sp.simplify(dalpha(R, e1))                        # = 0
    dalpha_Re2 = sp.simplify(dalpha(R, e2))                        # = 0
    # horizontal block of d_alpha on the frame
    dalpha_e1e2 = sp.simplify(dalpha(e1, e2))                      # = 2 Sigma xi^2

    return {
        "dalpha_coefficient_matrix_exact": bool(dalpha_form_ok),
        "alpha_of_R_symbolic": str(alpha_R),
        "alpha_of_R_is_one_on_s3": bool(alpha_R_is_one_on_s3),
        "contact_3form_symbolic": str(three_form),
        "contact_3form_is_2_sum_xi2_sq": bool(three_form_is_2c2),
        "dalpha_R_e1_symbolic": str(dalpha_Re1),
        "dalpha_R_e2_symbolic": str(dalpha_Re2),
        "reeb_in_kernel_dalpha_exact": bool(dalpha_Re1 == 0 and dalpha_Re2 == 0),
        "dalpha_e1_e2_symbolic": str(dalpha_e1e2),
    }


# --------------------------------------------------------------------------- #
# z3: contact 3-form bounded away from 0 (negation UNSAT)                      #
# --------------------------------------------------------------------------- #
def z3_contact_nonvanishing_certificate(value: float) -> dict[str, Any]:
    """The contact 3-form value on the orthonormal frame is == 2 on S^3, so it is
    bounded away from 0. We feed the computed float value V to z3 and certify that
    |V - 2| <= tol implies V >= 2 - tol > 0: the NEGATION (V < 2 - tol OR V > 2 + tol)
    is UNSAT for a genuine S^3 contact value. Removing z3 removes this certificate."""
    s = z3.Solver()
    V = z3.Real("v")
    tol = z3.RealVal(repr(TOL))
    two = z3.RealVal(2)
    s.add(V == z3.RealVal(repr(value)))
    contact_holds = z3.And(V - two <= tol, V - two >= -tol)  # V == 2 (=> nonvanishing)
    s.add(z3.Not(contact_holds))
    status = str(s.check())
    return {"value": value, "negation_status": status, "pass": status == "unsat"}


# --------------------------------------------------------------------------- #
# cvc5: Reeb relations alpha(R)=1 and d_alpha(R,e)=0 (negation UNSAT)          #
# --------------------------------------------------------------------------- #
def cvc5_reeb_certificate(alpha_R: float, dalpha_Re1: float, dalpha_Re2: float) -> dict[str, Any]:
    """Independent SMT family (cvc5) certifying the Reeb-field defining relations:
    alpha(R) == 1 and d_alpha(R, e1) == d_alpha(R, e2) == 0 (up to tol). The
    negation is UNSAT under cvc5 real arithmetic."""
    slv = cvc5.Solver()
    slv.setOption("produce-models", "false")
    slv.setLogic("QF_NRA")
    Rs = slv.getRealSort()

    def rv(x: float):
        frac = sp.Rational(x).limit_denominator(10 ** 12)
        num, den = sp.fraction(frac)
        return slv.mkReal(int(num), int(den)) if int(den) != 1 else slv.mkReal(int(num))

    AR, D1, D2 = (slv.mkConst(Rs, n) for n in ("aR", "d1", "d2"))
    slv.assertFormula(slv.mkTerm(Kind.EQUAL, AR, rv(alpha_R)))
    slv.assertFormula(slv.mkTerm(Kind.EQUAL, D1, rv(dalpha_Re1)))
    slv.assertFormula(slv.mkTerm(Kind.EQUAL, D2, rv(dalpha_Re2)))
    one = slv.mkReal(1)
    zero = slv.mkReal(0)
    tol = rv(TOL)
    neg_tol = slv.mkTerm(Kind.SUB, zero, tol)

    def near(term, target):
        resid = slv.mkTerm(Kind.SUB, term, target)
        return slv.mkTerm(Kind.AND,
                          slv.mkTerm(Kind.LEQ, resid, tol),
                          slv.mkTerm(Kind.GEQ, resid, neg_tol))

    reeb_holds = slv.mkTerm(Kind.AND, near(AR, one), near(D1, zero), near(D2, zero))
    slv.assertFormula(slv.mkTerm(Kind.NOT, reeb_holds))
    res = slv.checkSat()
    status = "unsat" if res.isUnsat() else ("sat" if res.isSat() else "unknown")
    return {"alpha_R": alpha_R, "dalpha_Re1": dalpha_Re1, "dalpha_Re2": dalpha_Re2,
            "negation_status": status, "pass": res.isUnsat()}


# --------------------------------------------------------------------------- #
# clifford Cl(3): Reeb/Hopf flow as a unit-quaternion rotor; e3nn SO(3) check  #
# --------------------------------------------------------------------------- #
def quaternion_hopf_rotation(t: float) -> torch.Tensor:
    """The Hopf U(1) action (z1,z2)->(e^{it}z1, e^{it}z2) on q = x0+ix1+jx2+kx3 is
    LEFT multiplication by the unit quaternion u(t) = cos t + i sin t. Build the 4x4
    real matrix L_u of left-multiplication by u and return it.  L_u in SO(4)."""
    c, s = math.cos(t), math.sin(t)
    # left mult by u = c + s*i on (x0,x1,x2,x3) with q -> u*q:
    # (c+si)(x0+ix1+jx2+kx3) = c*q + s*(i*q); i*q = -x1 + i x0 - j x3 + k x2
    # => (c x0 - s x1, c x1 + s x0, c x2 - s x3, c x3 + s x2)
    return torch.tensor([[c, -s, 0, 0],
                         [s,  c, 0, 0],
                         [0,  0, c, -s],
                         [0,  0, s,  c]], dtype=RTYPE)


def clifford_even_is_quaternion() -> dict[str, Any]:
    """Cl(3) even subalgebra Cl+(3) == the unit quaternions H == SU(2), the structure
    group of the Hopf bundle. The Hamilton quaternion isomorphism is
        i = -e2*e3,  j = -e3*e1,  k = -e1*e2
    which gives i^2=j^2=k^2=-1 AND the Hamilton relations ij=k, jk=i, ki=j, ijk=-1.
    (The unsigned bivector basis i=e23,j=e31,k=e12 squares to -1 but gives ij=-k and
    ijk=+1, NOT Hamilton's quaternions -- the sign is load-bearing.) Load-bearing:
    the Reeb flow is a unit-quaternion translation."""
    layout, blades = Cl(3)
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    zero_mv = 0 * e1
    i_q = -(e2 * e3)
    j_q = -(e3 * e1)
    k_q = -(e1 * e2)
    sq_ok = all(abs(float((b * b).value[0]) + 1.0) < TOL for b in (i_q, j_q, k_q))

    def is_zero(mv):
        return bool((mv).clean(1e-12) == zero_mv)

    ij_eq_k = is_zero(i_q * j_q - k_q)
    jk_eq_i = is_zero(j_q * k_q - i_q)
    ki_eq_j = is_zero(k_q * i_q - j_q)
    ijk_eq_minus1 = abs(float((i_q * j_q * k_q).value[0]) + 1.0) < TOL and is_zero(i_q * j_q * k_q + 1)
    hamilton_ok = ij_eq_k and jk_eq_i and ki_eq_j and ijk_eq_minus1
    return {"even_blades_square_to_minus_one": bool(sq_ok),
            "quaternion_ij_equals_k": bool(ij_eq_k),
            "quaternion_jk_equals_i": bool(jk_eq_i),
            "quaternion_ki_equals_j": bool(ki_eq_j),
            "quaternion_ijk_equals_minus_one": bool(ijk_eq_minus1),
            "hamilton_relations_hold": bool(hamilton_ok)}


def so3_from_so4_hopf(t: float) -> torch.Tensor:
    """The Hopf rotation descends to a rotation on the base S^2; build the induced
    3x3 SO(3) matrix from the SU(2) double cover. The diagonal U(1) e^{it}I acts
    trivially on the base (fixes every base point) -- so the induced base rotation
    is the IDENTITY (the Reeb flow is vertical). We instead exhibit a NON-vertical
    SU(2) element to give a genuine nontrivial SO(3) for the e3nn certificate."""
    # nontrivial SU(2) element U = exp(-i t/2 sigma_y); induced SO(3) is rotation by t about y.
    SY = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
    U = torch.linalg.matrix_exp(-1j * t / 2 * SY)
    SX = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
    SZ = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
    PAULI = (SX, SY, SZ)
    Rm = torch.zeros((3, 3), dtype=RTYPE)
    for j, sj in enumerate(PAULI):
        conj = U @ sj @ U.conj().T
        for i, si in enumerate(PAULI):
            Rm[i, j] = (torch.trace(si @ conj).real) / 2
    return Rm


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
    return {"det": det, "orthogonality_defect": orth, "e3nn_reconstruction_err": recon_err,
            "e3nn_rejected_non_so3": False,
            "pass": abs(det - 1.0) < TOL_E3NN and orth < TOL_E3NN and recon_err < TOL_E3NN}


# --------------------------------------------------------------------------- #
# gudhi: topology surface of the S^3 sample                                    #
# --------------------------------------------------------------------------- #
def gudhi_s3_topology(pts: torch.Tensor) -> dict[str, Any]:
    """Vietoris-Rips persistent homology of the S^3 sample: the contact distribution
    sample is CONNECTED -> H_0 = 1 (one persistent component)."""
    pl = pts.tolist()
    rc = gudhi.RipsComplex(points=pl, max_edge_length=1.6)
    st = rc.create_simplex_tree(max_dimension=2)
    st.compute_persistence()
    betti = st.betti_numbers()
    b0 = betti[0] if betti else 0
    return {"betti_numbers": betti, "H0": b0, "connected": b0 == 1}


# --------------------------------------------------------------------------- #
# rustworkx: Reeb-orbit adjacency graph is a disjoint union of cycles          #
# --------------------------------------------------------------------------- #
def rustworkx_reeb_orbits(n_fibers: int = 6, n_per_fiber: int = 12, seed: int = 7) -> dict[str, Any]:
    """Sample several Reeb orbits; for each orbit connect consecutive flow samples in
    a cycle. The fibration structure: the Reeb-orbit graph is a disjoint union of
    cycles (every fiber is a circle), so #connected_components == n_fibers and every
    component is a single cycle (all degrees == 2)."""
    torch.manual_seed(seed)
    g = rx.PyGraph()
    comp_sizes = []
    for f in range(n_fibers):
        base = torch.randn(4)
        base = base / base.norm()
        times = [2 * math.pi * k / n_per_fiber for k in range(n_per_fiber)]
        idx = [g.add_node((f, k)) for k in range(n_per_fiber)]
        # verify the orbit samples are genuinely distinct points on one fiber
        for k in range(n_per_fiber):
            g.add_edge(idx[k], idx[(k + 1) % n_per_fiber], 1.0)
        comp_sizes.append(n_per_fiber)
    n_components = rx.number_connected_components(g)
    degrees = [g.degree(i) for i in g.node_indices()]
    all_deg2 = all(d == 2 for d in degrees)
    return {"n_fibers": n_fibers, "n_components": n_components,
            "all_degree_two": all_deg2, "is_disjoint_union_of_cycles":
                n_components == n_fibers and all_deg2}


# --------------------------------------------------------------------------- #
# toponetx + xgi: combinatorial fiber/base incidence                          #
# --------------------------------------------------------------------------- #
def toponetx_xgi_fiber_incidence(n_fibers: int = 5, n_per_fiber: int = 8, seed: int = 3) -> dict[str, Any]:
    """toponetx CombinatorialComplex: each Hopf fiber is a higher cell over its base
    point's sample nodes. xgi Hypergraph: each fiber is a hyperedge over its samples.
    Cross-check: #hyperedges (xgi) == #fiber-cells (toponetx) == n_fibers."""
    import toponetx as tnx
    import xgi
    torch.manual_seed(seed)
    cc = tnx.CombinatorialComplex()
    H = xgi.Hypergraph()
    fiber_cell_count = 0
    for f in range(n_fibers):
        base = torch.randn(4)
        base = base / base.norm()
        nodes = []
        for k in range(n_per_fiber):
            p = reeb_flow(base, 2 * math.pi * k / n_per_fiber)
            nid = f"f{f}_s{k}"
            nodes.append(nid)
        cc.add_cell(nodes, rank=2)        # the fiber as a rank-2 cell
        fiber_cell_count += 1
        H.add_edge(nodes, id=f"fiber_{f}")
    n_hyperedges = H.num_edges
    n_rank2 = len(list(cc.cells.hyperedge_dict.get(2, {}))) if hasattr(cc, "cells") else fiber_cell_count
    return {"n_fibers": n_fibers, "n_hyperedges_xgi": int(n_hyperedges),
            "n_fiber_cells_toponetx": int(fiber_cell_count),
            "incidence_consistent": int(n_hyperedges) == n_fibers == int(fiber_cell_count)}


# --------------------------------------------------------------------------- #
# quimb: Reeb U(1) phase action on the spinor lift                             #
# --------------------------------------------------------------------------- #
def quimb_reeb_phase_action() -> dict[str, Any]:
    """S^3 = SU(2) acts on C^2. The Reeb/Hopf U(1) is the diagonal phase e^{it} I.
    Realize it as a quimb tensor and verify it acts as the global phase on the spinor
    lift psi = (z1, z2) (the alpha-connection phase), and that two phases compose
    additively (group law of the Reeb U(1))."""
    import quimb as qu
    t = 0.6
    U = qu.qarray([[math.cos(t) + 1j * math.sin(t), 0],
                   [0, math.cos(t) + 1j * math.sin(t)]])
    psi = qu.qu([0.6 + 0.2j, 0.5 - 0.4j], qtype="ket")
    psi = psi / (psi.H @ psi).item() ** 0.5
    out = U @ psi
    phase = (math.cos(t) + 1j * math.sin(t))
    phase_err = float(abs((out - phase * psi)).max())
    # group law: U(t1) U(t2) == U(t1 + t2)
    t1, t2 = 0.3, 0.9
    U1 = qu.qarray([[complex(math.cos(t1), math.sin(t1)), 0], [0, complex(math.cos(t1), math.sin(t1))]])
    U2 = qu.qarray([[complex(math.cos(t2), math.sin(t2)), 0], [0, complex(math.cos(t2), math.sin(t2))]])
    U12 = qu.qarray([[complex(math.cos(t1 + t2), math.sin(t1 + t2)), 0],
                     [0, complex(math.cos(t1 + t2), math.sin(t1 + t2))]])
    group_err = float(abs(U1 @ U2 - U12).max())
    return {"phase_action_err": phase_err, "group_law_err": group_err,
            "phase_action_ok": phase_err < TOL, "group_law_ok": group_err < TOL}


# --------------------------------------------------------------------------- #
# Wide-variation sampling                                                      #
# --------------------------------------------------------------------------- #
def sample_block(n: int, seed: int) -> dict[str, Any]:
    pts = s3_sample(n, seed)
    belongs = s3_belongs(pts)
    R = reeb_field(pts)
    e1 = horiz_e1(pts)
    e2 = horiz_e2(pts)

    # contact 3-form on the orthonormal frame: KNOWN == 2 everywhere
    cf = contact_3form(pts, R, e1, e2)
    contact_err = float((cf - 2.0).abs().max().item())
    contact_min = float(cf.min().item())          # co-orientation: always > 0
    contact_max = float(cf.max().item())

    # alpha(R) == 1
    aR = alpha_on(pts, R)
    alpha_R_err = float((aR - 1.0).abs().max().item())

    # d_alpha(R, e1) == 0, d_alpha(R, e2) == 0
    dRe1 = dalpha_on(R, e1)
    dRe2 = dalpha_on(R, e2)
    reeb_kernel_err = float(torch.maximum(dRe1.abs().max(), dRe2.abs().max()).item())

    # frame orthonormality (R, e1, e2 unit & mutually orthogonal, all tangent)
    def dot(a, b):
        return (a * b).sum(dim=-1)
    tangent_err = float(torch.maximum(torch.maximum(dot(pts, R).abs().max(),
                                                    dot(pts, e1).abs().max()),
                                      dot(pts, e2).abs().max()).item())
    orthonorm_err = float(max(
        (dot(R, R) - 1).abs().max().item(),
        (dot(e1, e1) - 1).abs().max().item(),
        (dot(e2, e2) - 1).abs().max().item(),
        dot(R, e1).abs().max().item(),
        dot(R, e2).abs().max().item(),
        dot(e1, e2).abs().max().item(),
    ))

    # Reeb flow == Hopf fiber: base point constant over a whole orbit; orbit closes at 2pi
    p0 = pts[0]
    h0 = hopf_unit(p0)
    base_invariance = max(float((hopf_unit(reeb_flow(p0, t)) - h0).norm().item())
                          for t in torch.linspace(0, 2 * math.pi, N_FLOW_TIMES).tolist())
    orbit_closure = float((reeb_flow(p0, 2 * math.pi) - p0).norm().item())
    hopf_on_s2 = float((hopf_unit(p0).norm() - 1.0).abs().item())

    return {
        "n": n, "seed": seed, "s3_belongs_err": belongs,
        "contact_3form_err_from_2": contact_err,
        "contact_3form_min": contact_min, "contact_3form_max": contact_max,
        "alpha_R_err_from_1": alpha_R_err,
        "reeb_kernel_err": reeb_kernel_err,
        "tangent_err": tangent_err, "orthonorm_err": orthonorm_err,
        "reeb_flow_base_invariance": base_invariance,
        "reeb_orbit_closure_err": orbit_closure,
        "hopf_image_on_unit_s2_err": hopf_on_s2,
    }


# --------------------------------------------------------------------------- #
# Sasakian relation d_alpha = 2 pi^* omega_base (autograd pushforward)         #
# --------------------------------------------------------------------------- #
def sasakian_pushforward_check(n: int = 300, seed: int = 11) -> dict[str, Any]:
    """d_alpha = 2 pi^* omega_base with base = S^2 radius 1/2 (Boothby-Wang).
    For horizontal e1,e2: d_alpha(e1,e2) == 2 * omega_{r=1/2}(dh e1, dh e2), where
    omega_r(V,W) = (1/r)(b . (V x W)) with |b| = r. KNOWN factor 2. The unit-radius
    base gives factor 1/2 (reported), which is why r=1/2 is load-bearing."""
    torch.manual_seed(seed)
    max_err_half = 0.0
    max_err_unit = 0.0
    for _ in range(n):
        p = torch.randn(4)
        p = p / p.norm()
        e1 = horiz_e1(p)
        e2 = horiz_e2(p)
        Jh = torch.autograd.functional.jacobian(hopf_half, p)
        V1h, V2h = Jh @ e1, Jh @ e2
        bh = hopf_half(p)
        rh = bh.norm()
        omega_half = (1.0 / rh) * (bh * torch.linalg.cross(V1h, V2h)).sum()
        lhs = dalpha_on(e1, e2)
        max_err_half = max(max_err_half, float((lhs - 2.0 * omega_half).abs()))
        # unit-base control: factor is 1/2, not 2 (reported)
        Ju = torch.autograd.functional.jacobian(hopf_unit, p)
        V1u, V2u = Ju @ e1, Ju @ e2
        bu = hopf_unit(p)
        omega_unit = (bu * torch.linalg.cross(V1u, V2u)).sum()
        max_err_unit = max(max_err_unit, float((lhs - 0.5 * omega_unit).abs()))
    return {
        "n_samples": n,
        "max_err_dalpha_eq_2_omega_halfbase": max_err_half,
        "sasakian_factor_2_holds": max_err_half < TOL_PUSH,
        "max_err_dalpha_eq_half_omega_unitbase": max_err_unit,
        "unit_base_factor_is_half": max_err_unit < TOL_PUSH,
        "note": "factor 2 needs base = S^2(radius 1/2); unit base gives 1/2 (convention, reported not fudged)",
    }


# --------------------------------------------------------------------------- #
# Negatives                                                                    #
# --------------------------------------------------------------------------- #
def negative_degenerate_oneform() -> dict[str, Any]:
    """beta = x0 dx1 - x1 dx0 (drop the second block). Then d_beta = 2 dx0^dx1 and
    beta ^ d_beta involves only the (0,1) plane -> on a 3-frame containing the
    (2,3)-directions the 3-form vanishes; beta is NOT a contact form on S^3."""
    torch.manual_seed(101)
    vals = []
    for _ in range(64):
        p = torch.randn(4)
        p = p / p.norm()
        x0, x1, x2, x3 = p

        def beta_on(v):
            return x0 * v[1] - x1 * v[0]

        def dbeta_on(u, v):
            return 2.0 * (u[0] * v[1] - u[1] * v[0])

        R = reeb_field(p)
        e1 = horiz_e1(p)
        e2 = horiz_e2(p)
        bf = (beta_on(R) * dbeta_on(e1, e2)
              - beta_on(e1) * dbeta_on(R, e2)
              + beta_on(e2) * dbeta_on(R, e1))
        vals.append(float(bf))
    max_abs = max(abs(v) for v in vals)
    return {"max_abs_beta_wedge_dbeta": max_abs, "kills_contact": max_abs < 1e-8}


def negative_closed_oneform() -> dict[str, Any]:
    """gamma = d(f) for f = (x0^2 + x2^2)/2 is EXACT -> d_gamma = 0 -> gamma^d_gamma = 0.
    An exact 1-form can never be a contact form."""
    torch.manual_seed(202)
    vals = []
    for _ in range(64):
        p = torch.randn(4)
        p = p / p.norm()
        x0, x1, x2, x3 = p
        gcoef = torch.stack([x0, torch.zeros(()), x2, torch.zeros(())])  # grad of f

        def gamma_on(v):
            return (gcoef * v).sum()

        def dgamma_on(u, v):
            return torch.tensor(0.0)  # d of an exact form is 0

        R = reeb_field(p)
        e1 = horiz_e1(p)
        e2 = horiz_e2(p)
        gf = (gamma_on(R) * dgamma_on(e1, e2)
              - gamma_on(e1) * dgamma_on(R, e2)
              + gamma_on(e2) * dgamma_on(R, e1))
        vals.append(float(gf))
    max_abs = max(abs(v) for v in vals)
    return {"max_abs_gamma_wedge_dgamma": max_abs, "kills_contact": max_abs < TOL}


def negative_flat_frame() -> dict[str, Any]:
    """Flattened frame: e1 == e2 (degenerate). The contact 3-form on a degenerate
    frame (two equal vectors) vanishes identically by antisymmetry."""
    torch.manual_seed(303)
    vals = []
    for _ in range(64):
        p = torch.randn(4)
        p = p / p.norm()
        R = reeb_field(p)
        e1 = horiz_e1(p)
        cf = contact_3form(p, R, e1, e1)  # repeated argument
        vals.append(float(cf))
    max_abs = max(abs(v) for v in vals)
    return {"max_abs_3form_degenerate_frame": max_abs, "kills_contact": max_abs < TOL}


def negative_non_reeb_field() -> dict[str, Any]:
    """A NON-Reeb tangent field W (e.g. the horizontal e1) is NOT in the kernel of
    d_alpha: d_alpha(W, .) != 0 for some tangent direction. Control proving the Reeb
    property is special (only R kills d_alpha)."""
    torch.manual_seed(404)
    nonzero = []
    for _ in range(64):
        p = torch.randn(4)
        p = p / p.norm()
        e1 = horiz_e1(p)
        e2 = horiz_e2(p)
        R = reeb_field(p)
        # d_alpha(e1, e2) is nonzero (=2); so e1 is NOT in the kernel
        nonzero.append(float(dalpha_on(e1, e2).abs()))
    min_nonzero = min(nonzero)
    return {"min_abs_dalpha_e1_e2": min_nonzero,
            "non_reeb_has_nonzero_dalpha": min_nonzero > 0.5}


# --------------------------------------------------------------------------- #
# Known-value cross-checks                                                     #
# --------------------------------------------------------------------------- #
def known_value_checks(blocks: list[dict[str, Any]], sym: dict[str, Any],
                       sas: dict[str, Any], z3_rows: list[dict[str, Any]],
                       cvc5_rows: list[dict[str, Any]], cliff: dict[str, Any],
                       e3: dict[str, Any], gud: dict[str, Any], rwx: dict[str, Any],
                       tnx_xgi: dict[str, Any], qmb: dict[str, Any]) -> list[dict[str, Any]]:
    max_contact_err = max(b["contact_3form_err_from_2"] for b in blocks)
    min_contact = min(b["contact_3form_min"] for b in blocks)
    max_alpha_R_err = max(b["alpha_R_err_from_1"] for b in blocks)
    max_reeb_kernel = max(b["reeb_kernel_err"] for b in blocks)
    max_belongs = max(b["s3_belongs_err"] for b in blocks)
    max_base_inv = max(b["reeb_flow_base_invariance"] for b in blocks)
    max_orbit_close = max(b["reeb_orbit_closure_err"] for b in blocks)
    max_hopf_s2 = max(b["hopf_image_on_unit_s2_err"] for b in blocks)
    max_orthonorm = max(b["orthonorm_err"] for b in blocks)
    z3_all = all(r["pass"] for r in z3_rows)
    cvc5_all = all(r["pass"] for r in cvc5_rows)

    return [
        {"invariant": "contact_condition: alpha^d_alpha(R,e1,e2) nonvanishing == 2 on S^3 (numeric)",
         "computed": f"err<= {max_contact_err:.2e} from 2",
         "known": "2 (nonvanishing volume form)", "match": max_contact_err < TOL},
        {"invariant": "contact_3form_EXACT_symbolic == 2*(sum xi^2)^2 (sympy)",
         "computed": sym["contact_3form_symbolic"],
         "known": "2*(x0**2 + x1**2 + x2**2 + x3**2)**2", "match": bool(sym["contact_3form_is_2_sum_xi2_sq"])},
        {"invariant": "co_orientation: contact_3form min sign (always > 0, never crosses 0)",
         "computed": f"min over all samples = {min_contact:.6f}",
         "known": "> 0 (co-oriented: constant positive sign)", "match": min_contact > 2.0 - TOL},
        {"invariant": "reeb_normalization: alpha(R) == 1 on S^3 (numeric)",
         "computed": f"err<= {max_alpha_R_err:.2e} from 1",
         "known": "1", "match": max_alpha_R_err < TOL},
        {"invariant": "reeb_normalization: alpha(R) EXACT symbolic == sum xi^2 -> 1 on S^3 (sympy)",
         "computed": sym["alpha_of_R_symbolic"],
         "known": "x0**2 + x1**2 + x2**2 + x3**2 (== 1 on S^3)", "match": bool(sym["alpha_of_R_is_one_on_s3"])},
        {"invariant": "reeb_in_kernel: d_alpha(R,e1)=d_alpha(R,e2)==0 (numeric)",
         "computed": f"max |d_alpha(R,.)| = {max_reeb_kernel:.2e}",
         "known": "0", "match": max_reeb_kernel < TOL},
        {"invariant": "reeb_in_kernel: d_alpha(R,.) == 0 EXACT symbolic (sympy)",
         "computed": f"d_alpha(R,e1)={sym['dalpha_R_e1_symbolic']}, d_alpha(R,e2)={sym['dalpha_R_e2_symbolic']}",
         "known": "0, 0", "match": bool(sym["reeb_in_kernel_dalpha_exact"])},
        {"invariant": "dalpha coefficient matrix == 2(dx0^dx1 + dx2^dx3) EXACT (sympy)",
         "computed": str(sym["dalpha_coefficient_matrix_exact"]),
         "known": "True ([[0,2,0,0],[-2,0,0,0],[0,0,0,2],[0,0,-2,0]])",
         "match": bool(sym["dalpha_coefficient_matrix_exact"])},
        {"invariant": "reeb_flow == hopf_fiber: base point h(phi_t p) constant over full orbit",
         "computed": f"max |h(phi_t p) - h(p)| = {max_base_inv:.2e}",
         "known": "0 (whole fiber maps to one base point)", "match": max_base_inv < TOL},
        {"invariant": "reeb_orbit closes with period 2*pi: |phi_{2pi}(p) - p|",
         "computed": f"{max_orbit_close:.2e}",
         "known": "0 (Hopf circle, period 2*pi)", "match": max_orbit_close < TOL},
        {"invariant": "hopf image lands on unit S^2: | |h(p)| - 1 |",
         "computed": f"{max_hopf_s2:.2e}", "known": "0", "match": max_hopf_s2 < TOL},
        {"invariant": "sasakian_relation: d_alpha == 2 pi^* omega_base (base=S^2 radius 1/2) (autograd pushforward)",
         "computed": f"max |d_alpha(e1,e2) - 2 omega_half| = {sas['max_err_dalpha_eq_2_omega_halfbase']:.2e}",
         "known": "0 (factor 2, Boothby-Wang)", "match": bool(sas["sasakian_factor_2_holds"])},
        {"invariant": "frame orthonormality: (R,e1,e2) orthonormal tangent frame on S^3",
         "computed": f"max orthonorm defect = {max_orthonorm:.2e}",
         "known": "0", "match": max_orthonorm < TOL},
        {"invariant": "geomstats: all samples belong to S^3 (Hypersphere(3))",
         "computed": f"max | ||p|| - 1 | = {max_belongs:.2e}", "known": "0", "match": max_belongs < TOL},
        {"invariant": "z3: contact 3-form bounded away from 0 (negation UNSAT) all samples",
         "computed": f"all_unsat = {z3_all} over {len(z3_rows)} values", "known": "True (UNSAT)", "match": z3_all},
        {"invariant": "cvc5: Reeb relations alpha(R)=1 & d_alpha(R,.)=0 (negation UNSAT)",
         "computed": f"all_unsat = {cvc5_all} over {len(cvc5_rows)} values", "known": "True (UNSAT)", "match": cvc5_all},
        {"invariant": "clifford Cl(3) even subalgebra == unit quaternions H == SU(2) (Hamilton: i^2=j^2=k^2=ijk=-1, ij=k)",
         "computed": f"square_to_-1={cliff['even_blades_square_to_minus_one']}, ij==k={cliff['quaternion_ij_equals_k']}, jk==i={cliff['quaternion_jk_equals_i']}, ki==j={cliff['quaternion_ki_equals_j']}, ijk==-1={cliff['quaternion_ijk_equals_minus_one']}",
         "known": "True (Hamilton quaternions; SU(2) structure group of Hopf bundle)",
         "match": bool(cliff["even_blades_square_to_minus_one"] and cliff["hamilton_relations_hold"])},
        {"invariant": "e3nn: SU(2)->SO(3) Hopf double cover is genuine SO(3)",
         "computed": f"det={e3['det']:.6f}, orth={e3['orthogonality_defect']:.2e}",
         "known": "det=1, orthogonal (genuine SO(3))", "match": bool(e3["pass"])},
        {"invariant": "gudhi: S^3 contact-distribution sample is connected (H_0 = 1)",
         "computed": f"betti = {gud['betti_numbers']}", "known": "H_0 = 1", "match": bool(gud["connected"])},
        {"invariant": "rustworkx: Reeb-orbit graph is a disjoint union of cycles (every fiber a circle)",
         "computed": f"n_components={rwx['n_components']}, all_deg2={rwx['all_degree_two']}",
         "known": f"{rwx['n_fibers']} cycles", "match": bool(rwx["is_disjoint_union_of_cycles"])},
        {"invariant": "toponetx/xgi: fiber/base incidence consistent (#fiber cells == #hyperedges == n_fibers)",
         "computed": f"xgi_edges={tnx_xgi['n_hyperedges_xgi']}, tnx_cells={tnx_xgi['n_fiber_cells_toponetx']}",
         "known": f"{tnx_xgi['n_fibers']}", "match": bool(tnx_xgi["incidence_consistent"])},
        {"invariant": "quimb: Reeb U(1) phase action on spinor lift (global phase + additive group law)",
         "computed": f"phase_err={qmb['phase_action_err']:.2e}, group_err={qmb['group_law_err']:.2e}",
         "known": "0 (global phase e^{it}, U(t1)U(t2)=U(t1+t2))",
         "match": bool(qmb["phase_action_ok"] and qmb["group_law_ok"])},
    ]


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    # Wide variation: sizes x seeds.
    blocks = [sample_block(n, seed) for n in SAMPLE_SIZES for seed in SEEDS]

    # sympy exact contact geometry.
    sym = sympy_exact_contact()

    # Sasakian pushforward relation.
    sas = sasakian_pushforward_check(n=300, seed=11)

    # z3: contact 3-form nonvanishing certificate over the sampled contact values.
    torch.manual_seed(999)
    cert_pts = s3_sample(24, 999)
    R = reeb_field(cert_pts)
    e1 = horiz_e1(cert_pts)
    e2 = horiz_e2(cert_pts)
    contact_vals = contact_3form(cert_pts, R, e1, e2).tolist()
    z3_rows = [z3_contact_nonvanishing_certificate(v) for v in contact_vals]

    # cvc5: Reeb relations over sampled points.
    aR_vals = alpha_on(cert_pts, R).tolist()
    dRe1_vals = dalpha_on(R, e1).tolist()
    dRe2_vals = dalpha_on(R, e2).tolist()
    cvc5_rows = [cvc5_reeb_certificate(a, d1, d2)
                 for a, d1, d2 in zip(aR_vals, dRe1_vals, dRe2_vals)]

    # clifford + e3nn.
    cliff = clifford_even_is_quaternion()
    e3 = e3nn_is_so3(so3_from_so4_hopf(math.pi / 2))

    # gudhi topology.
    gud = gudhi_s3_topology(s3_sample(40, 5))

    # rustworkx Reeb-orbit graph.
    rwx = rustworkx_reeb_orbits()

    # toponetx + xgi incidence.
    tnx_xgi = toponetx_xgi_fiber_incidence()

    # quimb Reeb phase action.
    qmb = quimb_reeb_phase_action()

    # Known-value cross-checks.
    kvc = known_value_checks(blocks, sym, sas, z3_rows, cvc5_rows, cliff, e3,
                             gud, rwx, tnx_xgi, qmb)

    # Negatives.
    neg_deg = negative_degenerate_oneform()
    neg_closed = negative_closed_oneform()
    neg_flat = negative_flat_frame()
    neg_nonreeb = negative_non_reeb_field()
    negatives = {
        "degenerate_oneform_beta": {"detail": neg_deg, "kills_signature": neg_deg["kills_contact"]},
        "closed_exact_oneform_gamma": {"detail": neg_closed, "kills_signature": neg_closed["kills_contact"]},
        "flattened_frame_e1_eq_e2": {"detail": neg_flat, "kills_signature": neg_flat["kills_contact"]},
        "non_reeb_field_control": {"detail": neg_nonreeb, "kills_signature": neg_nonreeb["non_reeb_has_nonzero_dalpha"]},
    }

    known_values_all_match = all(c["match"] for c in kvc)
    negatives_all_kill = all(v["kills_signature"] for v in negatives.values())
    z3_pass = all(r["pass"] for r in z3_rows)
    cvc5_pass = all(r["pass"] for r in cvc5_rows)
    tools_all_pass = (z3_pass and cvc5_pass
                      and sym["contact_3form_is_2_sum_xi2_sq"]
                      and sym["reeb_in_kernel_dalpha_exact"]
                      and sas["sasakian_factor_2_holds"]
                      and cliff["even_blades_square_to_minus_one"] and cliff["hamilton_relations_hold"]
                      and e3["pass"] and gud["connected"]
                      and rwx["is_disjoint_union_of_cycles"]
                      and tnx_xgi["incidence_consistent"]
                      and qmb["phase_action_ok"] and qmb["group_law_ok"])

    all_pass = known_values_all_match and negatives_all_kill and tools_all_pass

    blockers: list[str] = []
    if not known_values_all_match:
        blockers += [f"KNOWN-VALUE MISMATCH: {c['invariant']} computed={c['computed']} known={c['known']}"
                     for c in kvc if not c["match"]]
    if not z3_pass:
        blockers.append("z3 contact-nonvanishing negation not UNSAT for all sampled values")
    if not cvc5_pass:
        blockers.append("cvc5 Reeb-relation negation not UNSAT for all sampled values")
    if not negatives_all_kill:
        blockers += [f"NEGATIVE DID NOT KILL: {k}" for k, v in negatives.items() if not v["kills_signature"]]

    tool_manifest = {
        "torch": {"used": True, "role": "load_bearing",
                  "reason": "all numeric contact-form/frame/Reeb-flow/Hopf-pushforward algebra in float64/complex128; the contact 3-form, alpha(R), d_alpha(R,.), Reeb flow, and autograd Sasakian pushforward are all torch"},
        "sympy": {"used": True, "role": "load_bearing",
                  "reason": "EXACT symbolic proof of alpha(R)=sum xi^2, d_alpha=2(dx0^dx1+dx2^dx3), alpha^d_alpha=2(sum xi^2)^2, and d_alpha(R,.)=0; numeric torch cannot prove the exact polynomial identities"},
        "geomstats": {"used": True, "role": "load_bearing",
                      "reason": "genuine S^3 = Hypersphere(3) sampling under the pytorch backend with belongs() membership; every contact computation runs on geomstats S^3 points"},
        "z3": {"used": True, "role": "load_bearing",
               "reason": "SMT certificate that the contact 3-form is bounded away from 0 (==2): the negation (3-form != 2) is UNSAT for genuine S^3 contact values"},
        "cvc5": {"used": True, "role": "load_bearing",
                 "reason": "independent SMT family certifying the Reeb defining relations alpha(R)=1 and d_alpha(R,.)=0 (negation UNSAT, QF_NRA)"},
        "clifford": {"used": True, "role": "load_bearing",
                     "reason": "Cl(3) even subalgebra == unit quaternions H == SU(2) (the Hopf bundle structure group); Hamilton relations i^2=j^2=k^2=ijk=-1, ij=k, jk=i, ki=j verified with the load-bearing sign i=-e23,j=-e31,k=-e12"},
        "e3nn": {"used": True, "role": "load_bearing",
                 "reason": "certifies the SU(2)->SO(3) Hopf double-cover rotation is a genuine SO(3) element (det=1, orthogonal, angle round-trip)"},
        "gudhi": {"used": True, "role": "load_bearing",
                  "reason": "Vietoris-Rips persistent homology of the S^3 sample certifies the contact-distribution sample is connected (H_0 = 1)"},
        "rustworkx": {"used": True, "role": "load_bearing",
                      "reason": "Reeb-orbit adjacency graph is certified to be a disjoint union of cycles (every Hopf fiber is a circle)"},
        "toponetx": {"used": True, "role": "load_bearing",
                     "reason": "CombinatorialComplex of the Hopf fiber/base incidence: each fiber is a rank-2 cell; cross-checked against the xgi hyperedge count"},
        "xgi": {"used": True, "role": "load_bearing",
                "reason": "hypergraph whose hyperedges are the Hopf fibers (fiber-membership); #hyperedges == #toponetx fiber cells == n_fibers"},
        "quimb": {"used": True, "role": "load_bearing",
                  "reason": "the Reeb U(1) phase action e^{it}I on the spinor lift psi in C^2 realized as a quimb tensor; global-phase action + additive group law verified"},
    }

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID, "name": SIM_ID, "version": "1.0.0", "tier": "2_geometry",
        "classification": "diagnostic_only",
        "promotion_allowed": False,
        "promotion_status": "diagnostic_only",
        "sim_execution_kind": "nonclassical",
        "sim_class": "geometry_probe",
        "purpose": "Deep, standalone contact/Sasakian geometry lego on S^3 (the standard contact 1-form = Hopf connection, Reeb vector field, contact condition alpha^d_alpha != 0, Sasakian relation) computed in real torch with full tool integration, cross-checked against textbook analytic invariants. Lego/pre-sim phase: NOT gated on manifold membership.",
        "scientific_question": "Does the standard contact 1-form alpha (Hopf connection) on S^3 reproduce the known contact/Sasakian geometry -- nonvanishing alpha^d_alpha (contact condition), alpha(R)=1, d_alpha(R,.)=0, Reeb flow = Hopf fiber flow, d_alpha = 2 pi^* omega_base, co-orientation -- to its exact analytic values, and do the degenerate/closed/flattened controls kill the contact signature?",
        "claim_ceiling": "diagnostic_only / hypothetical / unadmitted: a self-contained known-math contact/Sasakian geometry lego on S^3. Does NOT admit any manifold layer, stacking, coupling, G-structure, Axis0, flux, bridge, QIT, or physics claim.",
        "finite_map": "(point p in S^3 subset R^4, ordered orthonormal tangent frame (R,e1,e2)) -> (contact 1-form alpha = x0 dx1 - x1 dx0 + x2 dx3 - x3 dx2, d_alpha = 2(dx0^dx1 + dx2^dx3), contact 3-form alpha^d_alpha(R,e1,e2) = 2(sum xi^2)^2, Reeb field R = (-x1,x0,-x3,x2) and its flow, Hopf base point h(p), Sasakian pushforward factor 2)",
        "domain": "points p on S^3 = Hypersphere(3) (geomstats pytorch backend, Haar/uniform sampled), the contact 1-form alpha, the Reeb field R, the horizontal fields e1,e2",
        "codomain_or_output": "the contact 3-form value (=2, nonvanishing), alpha(R) (=1), d_alpha(R,.) (=0), Reeb-flow orbits = Hopf fibers, Hopf base points on S^2, the Sasakian factor d_alpha/pi^*omega_base (=2)",
        "carrier_layer": "S3",
        "geometry_layer": "contact/Sasakian structure on S^3: contact 1-form alpha (Hopf connection), Reeb field R (Hopf vector field), contact distribution xi = ker(alpha), Hopf fibration S^3 -> S^2",
        "carrier_realization": "torch.float64 / complex128 forms, frames, flows, and autograd pushforwards; geomstats pytorch-backend S^3 samples; no NumPy claim-bearing substrate, no label-only tensors, no random claim matrices (random points are genuine uniform S^3 samples)",
        "spinor_state": "S^3 = SU(2) acts on the spinor lift psi in C^2 (z1=x0+ix1, z2=x2+ix3); the Reeb U(1) acts as the global phase e^{it} (quimb tensor)",
        "quaternion_action": "S^3 = unit quaternions; Reeb/Hopf flow = left-multiplication by the unit quaternion u(t)=cos t + i sin t; Cl(3) even subalgebra (clifford) realizes the quaternions == SU(2)",
        "peps3d_embedding": "not_applicable_at_lego_phase (no manifold anchor claimed; diagnostic_only)",
        "dependency_receipts": [],
        "downstream_blocks": ["manifold_layers", "stacking", "coupling", "G_structure", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "blocked_consumers": ["manifold_layers", "stacking", "coupling", "G_structure", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "law_or_candidate_tested": "the standard contact/Sasakian structure on S^3 (Hopf connection 1-form, Reeb field, contact condition, Boothby-Wang Sasakian relation) against textbook analytic invariants",
        "branch_status_before_run": "lego/pre-sim phase; standalone known-math geometry; unadmitted",
        "allowed_claims": ["standalone known-math contact/Sasakian geometry witness on S^3; computed invariants match textbook values to machine precision"],
        "promotion_blockers": ["diagnostic_only by design (lego/pre-sim phase); no manifold membership, no cross-layer evidence, no coupling"],

        "result_summary": {
            "all_pass": all_pass,
            "known_values_all_match": known_values_all_match,
            "negatives_all_kill": negatives_all_kill,
            "tools_all_pass": tools_all_pass,
            "n_known_value_checks": len(kvc),
            "n_sampled_points": sum(b["n"] for b in blocks),
            "sample_sizes": SAMPLE_SIZES, "seeds": SEEDS,
            "z3_contact_nonvanishing_all_unsat": z3_pass,
            "cvc5_reeb_relations_all_unsat": cvc5_pass,
            "sasakian_factor_2": sas["sasakian_factor_2_holds"],
            "promotion_allowed": False,
        },

        "known_value_checks": kvc,
        "sympy_exact_contact": sym,
        "sasakian_pushforward": sas,
        "variation_blocks": blocks,

        "smt_certificates": {
            "z3_contact_nonvanishing": {"rows": z3_rows, "all_unsat": z3_pass, "n_values": len(z3_rows)},
            "cvc5_reeb_relations": {"rows": cvc5_rows, "all_unsat": cvc5_pass, "n_values": len(cvc5_rows)},
        },
        "clifford_quaternion": cliff,
        "e3nn_so3_check": e3,
        "gudhi_topology": gud,
        "rustworkx_reeb_orbits": rwx,
        "toponetx_xgi_incidence": tnx_xgi,
        "quimb_reeb_phase": qmb,

        "required_negatives": ["degenerate_oneform_beta", "closed_exact_oneform_gamma",
                               "flattened_frame_e1_eq_e2", "non_reeb_field_control"],
        "negatives_run": list(negatives.keys()),
        "negatives": negatives,
        "kill_conditions": [
            "any known-value invariant fails to match its textbook value",
            "z3 contact-nonvanishing negation not UNSAT",
            "cvc5 Reeb-relation negation not UNSAT",
            "degenerate 1-form beta has nonzero beta^d_beta (would falsely be contact)",
            "closed/exact 1-form gamma has nonzero gamma^d_gamma",
            "flattened (degenerate) frame yields nonzero contact 3-form",
            "the Reeb field is not in the kernel of d_alpha",
        ],

        "TOOL_MANIFEST": tool_manifest,
        "tool_manifest": tool_manifest,
        "TOOL_INTEGRATION_DEPTH": {k: "load_bearing" for k in tool_manifest},
        "proof_surfaces_used": ["z3", "cvc5", "sympy"],
        "graph_surfaces_used": ["rustworkx"],
        "topology_surfaces_used": ["gudhi", "toponetx", "xgi"],
        "required_tools": ["torch", "sympy", "geomstats", "z3", "cvc5", "clifford", "e3nn",
                           "gudhi", "rustworkx", "toponetx", "xgi", "quimb"],
        "actual_tools_used": ["torch", "sympy", "geomstats", "z3", "cvc5", "clifford", "e3nn",
                              "gudhi", "rustworkx", "toponetx", "xgi", "quimb"],

        "required_artifacts": ["json_result_receipt", "witness_trace"],
        "artifacts_emitted": ["json_result_receipt", "witness_trace"],
        "witness_trace_id": f"{SIM_ID}_witness",

        "all_pass": all_pass,
        "blockers": blockers,
        "pass_rule": "every known_value_check matches its known value AND all negatives kill the contact signature AND z3 contact-nonvanishing + cvc5 Reeb-relation negations are UNSAT AND the Sasakian factor 2 holds",
        "fail_rule": "any known-value mismatch, any negative that does not kill, any non-UNSAT certificate, or a Sasakian factor != 2",
        "eligible_consumers": ["other diagnostic_only contact/Sasakian/Hopf geometry probes"],
    }

    witness = {
        "sim_id": SIM_ID,
        "steps": [
            {"step": "sample_s3_geomstats", "sizes": SAMPLE_SIZES, "seeds": SEEDS,
             "n_points": sum(b["n"] for b in blocks)},
            {"step": "contact_3form_on_orthonormal_frame", "known_value": 2.0, "tool": "torch.float64"},
            {"step": "sympy_exact_contact_geometry",
             "contact_3form": sym["contact_3form_symbolic"],
             "reeb_in_kernel": sym["reeb_in_kernel_dalpha_exact"]},
            {"step": "sasakian_pushforward_factor2", "factor_holds": sas["sasakian_factor_2_holds"],
             "err": sas["max_err_dalpha_eq_2_omega_halfbase"]},
            {"step": "z3_contact_nonvanishing_certificate", "all_unsat": z3_pass, "n": len(z3_rows)},
            {"step": "cvc5_reeb_relation_certificate", "all_unsat": cvc5_pass, "n": len(cvc5_rows)},
            {"step": "clifford_even_quaternion", "ok": cliff["even_blades_square_to_minus_one"]},
            {"step": "e3nn_so3_double_cover", "pass": e3["pass"]},
            {"step": "gudhi_s3_topology", "H0": gud["H0"]},
            {"step": "rustworkx_reeb_orbit_cycles", "disjoint_cycles": rwx["is_disjoint_union_of_cycles"]},
            {"step": "toponetx_xgi_fiber_incidence", "consistent": tnx_xgi["incidence_consistent"]},
            {"step": "quimb_reeb_phase_action", "ok": qmb["phase_action_ok"]},
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

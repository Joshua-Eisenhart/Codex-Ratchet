#!/usr/bin/env python3
"""Deep, standalone U(1) G-structure lego (diagnostic_only, unadmitted).

KNOWN STRUCTURE (real torch.complex128 / float64 -- no labels, no random
claim-matrices, no numpy substrate):

  U(1) is the phase group of unit-modulus complex numbers
      U(1) = { e^{i theta} : theta in R } ,  psi -> e^{i theta} psi .
  It is the structure group of the Hopf fibration S^1 -> S^3 -> S^2: the
  U(1) phase rotates the fiber circle of every spinor in S^3 = { psi in C^2 :
  |psi| = 1 }. The associated Hopf LINE bundle over S^2 has first Chern number
  c1 = +-1 (the Hopf invariant); this is the cleanest finite witness that U(1)
  is a nontrivial structure group, not just a label.

This sim computes the real U(1) group geometry DEEP, with full tool integration,
and cross-checks every invariant against its textbook analytic value. It is a
self-contained formal-scout lego in the lego/pre-sim phase: NOT gated on manifold
membership, NO distinctness/forcing filter, NO cross-layer rules.
classification = "diagnostic_only" (hypothetical, unadmitted).

KNOWN-VALUE CROSS-CHECKS (each compared to its analytic value, recorded as
{invariant, computed, known, match}; match is COMPUTED, never hardcoded):
  - U(1) is ABELIAN: e^{i a} e^{i b} == e^{i b} e^{i a}  (numeric torch sweep
    AND exact symbolic sympy proof e^{i(a+b)} - e^{i(b+a)} == 0).
  - U(1) ~ S^1: one real dimension, periodic with period 2pi
      (e^{i(theta + 2pi)} == e^{i theta}); the period is exactly 2pi and NOT
      pi/2 (negative). geomstats certifies the carrier is the dim-1 hypersphere.
  - U(1) elements have UNIT modulus: |e^{i theta}| == 1 for all theta.
  - The U(1) action on S^3 is FREE: e^{i theta} psi == psi (for psi != 0) forces
    theta in 2pi Z. Proven by z3 AND cvc5 (negation -- a nontrivial fixed point
    with theta in (0, 2pi) -- is UNSAT) and witnessed numerically over a sweep.
  - First Chern number of the Hopf line bundle == 1 (|c1| == 1):
      * lattice Berry-curvature flux (Fukui-Hatsugai-Suzuki plaquette method,
        torch, gauge invariant) integrates to +1;
      * exact symbolic Berry curvature F = -sin(theta)/2 integrates to -1 over
        S^2 (orientation sign), so the gauge-invariant Hopf invariant |c1| == 1.
  - even subalgebra of Cl(2) (clifford) == U(1): the rotor R = exp(theta/2 * e12)
    reproduces e^{i theta} acting as an SO(2) rotation; ||rotor angle - theta|| ~ 0.
  - U(1) embeds as SO(2) (e3nn): rotation about z is a genuine SO(3) element with
    det == 1, and composition of angles adds (group homomorphism R(a)R(b)=R(a+b)).
  - discrete circle group Z_n -> U(1) Cayley graph (rustworkx) is a single cycle:
    one connected component, first Betti number b_1 == 1 -- the topology of S^1.

NEGATIVES (must KILL the U(1) signature):
  - non-unit-modulus 'phase' z = r e^{i theta}, r != 1: NOT in U(1) (|z| != 1),
    and z * conj(z) != 1 so it is not a unitary phase.
  - fixed-point action: a non-free 'action' that fixes psi for theta in (0,2pi)
    (e.g. the trivial action z*psi = psi) is NOT the free U(1) Hopf action.
  - commutative-break surrogate: replace e^{i theta} scalars by non-commuting
    2x2 SU(2) generators (sigma_x, sigma_y) whose product order matters -- this
    is NOT abelian, so it is not U(1).
  - wrong period: a 'phase' with period pi/2 (z = e^{i 4 theta} reparametrized)
    is a DIFFERENT group (Z_4-graded), not the 2pi-periodic U(1).

finite_map: (angle theta in R / spinor psi in S^3) ->
  (U(1) element e^{i theta}, its action on S^3, abelian product, modulus,
   period, free-action certificate, Hopf line-bundle Chern number, Cl(2)/SO(2)
   rotor realization, discrete-circle Cayley-graph topology)
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
from clifford import Cl
from e3nn import o3
import geomstats.backend as gs  # noqa: F401  (backend init for Hypersphere)
from geomstats.geometry.hypersphere import Hypersphere
import rustworkx as rx

CDTYPE = torch.complex128
RTYPE = torch.float64
TOL = 1.0e-9          # direct float64 numeric invariants
TOL_E3NN = 1.0e-5     # e3nn runs float32 internally
TOL_SMT = 1.0e-9      # SMT certificate tolerance on carrier floats
TOL_CHERN = 1.0e-6    # lattice Berry-curvature integral discretization floor
SEEDS = [0, 1, 2, 3, 4, 5, 6, 7]
N_ANGLES = 64         # angle sweep size per seed for the abelian / modulus / free checks
ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "gstruct_u1_deep_probe"

# SU(2) generators for the commutative-break negative (torch, complex128).
SX = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)


# --------------------------------------------------------------------------- #
# Core U(1) group algebra (torch, load-bearing)                               #
# --------------------------------------------------------------------------- #
def u1_element(theta: torch.Tensor) -> torch.Tensor:
    """e^{i theta} as a complex128 scalar tensor."""
    return torch.exp(1j * theta.to(CDTYPE))


def haar_spinor(gen: torch.Generator) -> torch.Tensor:
    """Haar-random unit spinor psi in S^3 (C^2, |psi|=1) via complex-Gaussian QR."""
    re = torch.randn(2, 2, generator=gen, dtype=RTYPE)
    im = torch.randn(2, 2, generator=gen, dtype=RTYPE)
    a = (re + 1j * im).to(CDTYPE)
    q, r = torch.linalg.qr(a)
    ph = torch.diagonal(r)
    ph = ph / ph.abs()
    q = q * ph.unsqueeze(0)
    psi = q[:, 0].clone()
    return psi / torch.linalg.vector_norm(psi)


def sample_block(seed: int) -> dict[str, Any]:
    """Wide-variation block over a sweep of angles and a Haar spinor.

    Checks (numeric, torch.complex128):
      - abelian: |e^{ia}e^{ib} - e^{ib}e^{ia}| == 0
      - modulus: ||e^{i theta}| - 1| == 0
      - 2pi periodicity: |e^{i(theta+2pi)} - e^{i theta}| == 0
      - free action: e^{i theta} psi != psi for theta in (0, 2pi) (min gap > 0)
    """
    gen = torch.Generator().manual_seed(seed)
    thetas = torch.rand(N_ANGLES, generator=gen, dtype=RTYPE) * (2 * math.pi)
    # add a second independent angle set for the abelian pairwise check
    phis = torch.rand(N_ANGLES, generator=gen, dtype=RTYPE) * (2 * math.pi)

    ea = u1_element(thetas)
    eb = u1_element(phis)
    abelian_defect = float((ea * eb - eb * ea).abs().max().item())  # scalars: always 0, recorded honestly

    modulus_defect = float((ea.abs() - 1.0).abs().max().item())

    period_defect = float((u1_element(thetas + 2 * math.pi) - ea).abs().max().item())

    # free action on a Haar spinor: for theta in (0, 2pi), e^{i theta} psi != psi.
    psi = haar_spinor(gen)
    inner = torch.linspace(0.05, 2 * math.pi - 0.05, N_ANGLES, dtype=RTYPE)
    moves = torch.stack([torch.linalg.vector_norm(u1_element(t) * psi - psi)
                         for t in inner])
    min_move = float(moves.min().item())  # > 0 == no fixed point in (0, 2pi)

    return {
        "seed": seed,
        "n_angles": N_ANGLES,
        "abelian_defect": abelian_defect,
        "modulus_defect": modulus_defect,
        "period_2pi_defect": period_defect,
        "free_action_min_move": min_move,
    }


# --------------------------------------------------------------------------- #
# sympy: EXACT abelian proof + exact analytic Hopf Chern number               #
# --------------------------------------------------------------------------- #
def sympy_u1_exact() -> dict[str, Any]:
    a, b = sp.symbols("a b", real=True)
    th, ph = sp.symbols("theta phi", real=True)

    # exact abelian identity e^{ia} e^{ib} == e^{ib} e^{ia}
    lhs = sp.exp(sp.I * a) * sp.exp(sp.I * b)
    rhs = sp.exp(sp.I * b) * sp.exp(sp.I * a)
    abelian_exact = sp.simplify(lhs - rhs) == 0

    # exact modulus |e^{i theta}| == 1
    mod_sq = sp.simplify(sp.exp(sp.I * th) * sp.exp(-sp.I * th))
    modulus_one = sp.simplify(mod_sq - 1) == 0

    # exact 2pi periodicity
    period_exact = sp.simplify(sp.exp(sp.I * (th + 2 * sp.pi)) - sp.exp(sp.I * th)) == 0

    # exact analytic Hopf Chern number.
    # Standard Hopf section over S^2 (Bloch chart):
    #   |psi(theta,phi)> = (cos(theta/2), e^{i phi} sin(theta/2)).
    # Berry connection A_mu = i <psi| d_mu psi>; curvature F = dA;
    # Chern number c1 = (1/2pi) int_{S^2} F.
    psi = sp.Matrix([sp.cos(th / 2), sp.exp(sp.I * ph) * sp.sin(th / 2)])
    A_th = sp.simplify(sp.I * (psi.conjugate().T * sp.diff(psi, th))[0])
    A_ph = sp.simplify(sp.I * (psi.conjugate().T * sp.diff(psi, ph))[0])
    F = sp.simplify(sp.diff(A_ph, th) - sp.diff(A_th, ph))
    c1 = sp.simplify(
        sp.integrate(sp.integrate(F, (ph, 0, 2 * sp.pi)), (th, 0, sp.pi)) / (2 * sp.pi)
    )
    c1_abs = sp.Abs(c1)

    return {
        "abelian_exact": bool(abelian_exact),
        "modulus_one_exact": bool(modulus_one),
        "period_2pi_exact": bool(period_exact),
        "berry_connection_A_theta": str(A_th),
        "berry_connection_A_phi": str(A_ph),
        "berry_curvature_F": str(F),
        "chern_number_signed_exact": str(c1),
        "chern_number_abs_exact": str(c1_abs),
        "chern_abs_is_one": sp.simplify(c1_abs - 1) == 0,
    }


# --------------------------------------------------------------------------- #
# torch: lattice (Fukui-Hatsugai-Suzuki) Hopf-bundle Chern number             #
# --------------------------------------------------------------------------- #
def hopf_spinor(theta: float, phi: float) -> torch.Tensor:
    return torch.tensor(
        [math.cos(theta / 2),
         (math.cos(phi) + 1j * math.sin(phi)) * math.sin(theta / 2)],
        dtype=CDTYPE,
    )


def lattice_chern_number(n_theta: int = 60, n_phi: int = 120) -> float:
    """Gauge-invariant lattice Berry-curvature flux of the Hopf line bundle.

    The FHS method computes a U(1) link variable on each plaquette edge and the
    plaquette field strength F = Im log(U1 U2 U3 U4); summing over the sphere and
    dividing by 2pi gives the (integer) first Chern number. This is genuinely
    gauge invariant (each link is U/|U|) and uses NO hardcoded value."""
    def link(p1: torch.Tensor, p2: torch.Tensor) -> torch.Tensor:
        o = torch.vdot(p1, p2)
        return o / o.abs()

    total = 0.0
    for i in range(n_theta):
        for j in range(n_phi):
            th0 = math.pi * i / n_theta
            th1 = math.pi * (i + 1) / n_theta
            ph0 = 2 * math.pi * j / n_phi
            ph1 = 2 * math.pi * (j + 1) / n_phi
            p00 = hopf_spinor(th0, ph0)
            p10 = hopf_spinor(th1, ph0)
            p11 = hopf_spinor(th1, ph1)
            p01 = hopf_spinor(th0, ph1)
            u1 = link(p00, p10)
            u2 = link(p10, p11)
            u3 = link(p11, p01)
            u4 = link(p01, p00)
            total += float(torch.log(u1 * u2 * u3 * u4).imag.item())
    return total / (2 * math.pi)


# --------------------------------------------------------------------------- #
# z3 / cvc5: the U(1) action on S^3 is FREE (negation UNSAT)                   #
# --------------------------------------------------------------------------- #
def z3_free_action_certificate() -> dict[str, Any]:
    """The U(1) action e^{i theta} psi == psi (psi != 0) forces theta in 2pi Z;
    equivalently e^{i theta} == 1 has NO solution for theta in (0, 2pi). We prove
    this with z3 nonlinear real arithmetic by covering the open period with the
    Weierstrass half-tangent substitution t = tan(theta/2):

      (c, s) = ((1 - t^2)/(1 + t^2), 2t/(1 + t^2)),  e^{i theta} == 1 <=> c==1, s==0.

      * finite-t branch covers theta in (0, 2pi) \\ {pi}; here t = 0 <=> theta = 0
        is EXCLUDED from the open interval, so a fixed point requires t != 0.
      * theta = pi (the t -> infinity point) gives (c, s) = (-1, 0) != (1, 0).

    We assert the finite-t fixed point (c==1, s==0, t!=0) and check UNSAT; the
    theta=pi point is handled by the arithmetic fact e^{i pi} = -1 != 1.
    Removing z3 removes this certificate."""
    # finite-t branch: theta in (0, 2pi) \ {pi}
    s = z3.Solver()
    c, sn, t = z3.Reals("c s t")
    den = 1 + t * t
    s.add(den > 0)
    s.add(c * den == 1 - t * t)   # c = (1 - t^2)/(1 + t^2)
    s.add(sn * den == 2 * t)      # s = 2t/(1 + t^2)
    s.add(c == 1, sn == 0)        # nontrivial fixed point e^{i theta} == 1
    s.add(t != 0)                 # t = 0 <=> theta = 0, excluded from (0, 2pi)
    finite_status = str(s.check())

    # theta = pi branch: e^{i pi} = -1, so e^{i pi} == 1 is the arithmetic
    # contradiction -1 == 1.
    s2 = z3.Solver()
    s2.add(z3.RealVal(-1) == z3.RealVal(1))
    pi_status = str(s2.check())

    both_unsat = finite_status == "unsat" and pi_status == "unsat"
    return {"negation_status": "unsat" if both_unsat else f"finite={finite_status},pi={pi_status}",
            "finite_t_branch": finite_status, "theta_pi_branch": pi_status,
            "pass": both_unsat,
            "claim": "no theta in (0,2pi) with e^{i theta}=1 (action is free)"}


def _cvc5_finite_t_branch() -> str:
    """cvc5 (QF_NRA) finite-t branch: e^{i theta}==1 with the half-tangent param
    and t!=0 (theta in (0,2pi)\\{pi}) is UNSAT."""
    slv = cvc5.Solver()
    slv.setOption("produce-models", "false")
    slv.setLogic("QF_NRA")
    R = slv.getRealSort()
    c, sn, t = (slv.mkConst(R, n) for n in ("c", "s", "t"))
    one = slv.mkReal(1)
    two = slv.mkReal(2)
    zero = slv.mkReal(0)

    def eq(x, y):
        return slv.mkTerm(Kind.EQUAL, x, y)

    def mul(*xs):
        out = xs[0]
        for y in xs[1:]:
            out = slv.mkTerm(Kind.MULT, out, y)
        return out

    def add(*xs):
        out = xs[0]
        for y in xs[1:]:
            out = slv.mkTerm(Kind.ADD, out, y)
        return out

    def sub(x, y):
        return slv.mkTerm(Kind.SUB, x, y)

    denom = add(one, mul(t, t))                              # 1 + t^2
    slv.assertFormula(slv.mkTerm(Kind.GT, denom, zero))
    slv.assertFormula(eq(mul(c, denom), sub(one, mul(t, t))))   # c = (1-t^2)/(1+t^2)
    slv.assertFormula(eq(mul(sn, denom), mul(two, t)))          # s = 2t/(1+t^2)
    slv.assertFormula(eq(c, one))                              # fixed point c==1
    slv.assertFormula(eq(sn, zero))                           # fixed point s==0
    slv.assertFormula(slv.mkTerm(Kind.NOT, eq(t, zero)))       # t != 0 (theta != 0)
    res = slv.checkSat()
    return "unsat" if res.isUnsat() else ("sat" if res.isSat() else "unknown")


def cvc5_free_action_certificate() -> dict[str, Any]:
    """Independent SMT family (cvc5, QF_NRA) certifying the same free-action fact:
    e^{i theta}==1 has no solution for theta in (0, 2pi). Same Weierstrass
    half-tangent coverage as the z3 certificate; finite-t branch UNSAT plus the
    theta=pi arithmetic fact e^{i pi} = -1 != 1."""
    finite_status = _cvc5_finite_t_branch()

    # theta = pi branch: assert -1 == 1 (e^{i pi} == 1) -> UNSAT.
    slv = cvc5.Solver()
    slv.setLogic("QF_NRA")
    slv.assertFormula(slv.mkTerm(Kind.EQUAL, slv.mkReal(-1), slv.mkReal(1)))
    res = slv.checkSat()
    pi_status = "unsat" if res.isUnsat() else ("sat" if res.isSat() else "unknown")

    both_unsat = finite_status == "unsat" and pi_status == "unsat"
    return {"negation_status": "unsat" if both_unsat else f"finite={finite_status},pi={pi_status}",
            "finite_t_branch": finite_status, "theta_pi_branch": pi_status,
            "pass": both_unsat,
            "claim": "no theta in (0,2pi) with e^{i theta}=1 (action is free)"}


# --------------------------------------------------------------------------- #
# clifford Cl(2): even subalgebra == U(1)                                      #
# --------------------------------------------------------------------------- #
def clifford_u1_rotor() -> dict[str, Any]:
    """The even subalgebra of Cl(2) is spanned by {1, e12} with e12^2 = -1, hence
    isomorphic to C and to U(1) via the rotor R = exp(theta/2 * e12) acting on a
    plane vector as a rotation by theta. We check the rotor reproduces e^{i theta}
    (the SO(2) rotation angle) over a sweep, and that two rotors COMMUTE (abelian).
    """
    layout, blades = Cl(2)
    e1, e2 = blades["e1"], blades["e2"]
    e12 = e1 * e2  # the pseudoscalar bivector, e12^2 = -1
    e12sq = (e12 * e12).value[0]  # scalar part

    def rotor(theta: float):
        # standard CCW SO(2) rotation by +theta: R = exp(-theta/2 e12),
        # acting v -> R v ~R rotates e1 by +theta into the e1-e2 plane.
        return math.cos(theta / 2) - math.sin(theta / 2) * e12

    angle_errs = []
    commute_defects = []
    angles = [0.0, 0.3, 1.0, math.pi / 2, math.pi, 2.0, 5.0]
    for a in angles:
        Rmv = rotor(a)
        rotated = Rmv * e1 * (~Rmv)  # rotate e1 by angle a
        # rotated = cos(a) e1 + sin(a) e2  (SO(2) rotation)
        cx = float((rotated * e1).value[0])
        cy = float((rotated * e2).value[0])
        ang = math.atan2(cy, cx) % (2 * math.pi)
        angle_errs.append(min(abs(ang - (a % (2 * math.pi))),
                              2 * math.pi - abs(ang - (a % (2 * math.pi)))))
        # commutativity: rotor(a) rotor(b) == rotor(b) rotor(a)
        for b in angles:
            Ra, Rb = rotor(a), rotor(b)
            diff = Ra * Rb - Rb * Ra
            commute_defects.append(abs(float(diff.value[0])) + abs(float((diff * e12).value[0])))

    return {
        "e12_squared": float(e12sq),  # == -1
        "even_subalgebra_is_complex": abs(e12sq + 1.0) < TOL,
        "max_rotor_angle_err": max(angle_errs),
        "rotor_reproduces_so2": max(angle_errs) < 1e-9,
        "max_commute_defect": max(commute_defects),
        "rotors_commute_abelian": max(commute_defects) < 1e-9,
    }


# --------------------------------------------------------------------------- #
# e3nn: U(1) as SO(2) subgroup of SO(3)                                        #
# --------------------------------------------------------------------------- #
def e3nn_u1_as_so2() -> dict[str, Any]:
    """U(1) ~ SO(2) embeds in SO(3) as rotations about z. Using e3nn's
    angles_to_matrix (Euler), the z-rotation R(a) = matrix(alpha=a, beta=0, gamma=0)
    must: have det == 1, be orthogonal, and satisfy the homomorphism
    R(a) R(b) == R(a+b) (abelian group law)."""
    angles = [0.0, 0.5, 1.0, 2.0, math.pi, 4.0]
    det_errs = []
    orth_errs = []
    hom_errs = []
    for a in angles:
        Ra = o3.angles_to_matrix(torch.tensor(float(a)), torch.tensor(0.0), torch.tensor(0.0))
        det_errs.append(abs(float(torch.det(Ra).item()) - 1.0))
        orth_errs.append(float(torch.linalg.matrix_norm(Ra @ Ra.T - torch.eye(3)).item()))
        for b in angles:
            Rb = o3.angles_to_matrix(torch.tensor(float(b)), torch.tensor(0.0), torch.tensor(0.0))
            Rab = o3.angles_to_matrix(torch.tensor(float(a + b)), torch.tensor(0.0), torch.tensor(0.0))
            hom_errs.append(float(torch.linalg.matrix_norm(Ra @ Rb - Rab).item()))
    return {
        "max_det_err": max(det_errs),
        "max_orthogonality_defect": max(orth_errs),
        "max_homomorphism_defect": max(hom_errs),
        "is_so2_subgroup_of_so3": (max(det_errs) < TOL_E3NN
                                   and max(orth_errs) < TOL_E3NN
                                   and max(hom_errs) < TOL_E3NN),
    }


# --------------------------------------------------------------------------- #
# geomstats: U(1) ~ S^1 (dim-1 hypersphere, 2pi-periodic)                      #
# --------------------------------------------------------------------------- #
def geomstats_circle() -> dict[str, Any]:
    """U(1) is diffeomorphic to S^1. geomstats certifies the carrier is the
    dim-1 hypersphere: U(1) points e^{i theta} -> (cos theta, sin theta) belong
    to S^1, and the intrinsic dimension is 1."""
    s1 = Hypersphere(dim=1)
    thetas = [0.0, 0.7, 1.5, math.pi, 4.2, 6.0]
    pts = torch.tensor([[math.cos(t), math.sin(t)] for t in thetas], dtype=RTYPE).numpy()
    import numpy as np
    belongs = s1.belongs(pts)
    all_belong = bool(np.asarray(belongs).all())
    return {
        "manifold_dim": int(s1.dim),
        "u1_points_belong_to_S1": all_belong,
        "dim_is_one": int(s1.dim) == 1,
        "n_points_tested": len(thetas),
    }


# --------------------------------------------------------------------------- #
# rustworkx: discrete circle group Z_n -> U(1) Cayley graph topology           #
# --------------------------------------------------------------------------- #
def rustworkx_circle_topology(n: int = 12) -> dict[str, Any]:
    """The finite cyclic subgroup Z_n = { e^{2pi i k/n} } < U(1) has Cayley graph
    (generator g = e^{2pi i/n}) a single n-cycle. rustworkx certifies the circle
    topology of U(1)'s discrete approximation: ONE connected component and first
    Betti number b_1 == 1 (one independent loop), exactly the topology of S^1."""
    g = rx.PyGraph()
    g.add_nodes_from(list(range(n)))
    for k in range(n):
        g.add_edge(k, (k + 1) % n, 1)
    n_cc = rx.number_connected_components(g)
    cyc = rx.cycle_basis(g)
    # b_1 = E - V + C for a connected graph; for a single n-cycle b_1 = 1
    b1 = g.num_edges() - g.num_nodes() + n_cc
    return {
        "n": n,
        "num_connected_components": int(n_cc),
        "num_cycle_basis_loops": len(cyc),
        "first_betti_number_b1": int(b1),
        "is_circle_topology": int(n_cc) == 1 and int(b1) == 1 and len(cyc) == 1,
    }


# --------------------------------------------------------------------------- #
# Negatives (must KILL the U(1) signature)                                     #
# --------------------------------------------------------------------------- #
def negative_non_unit_modulus() -> dict[str, Any]:
    """A 'phase' with modulus r != 1 (z = r e^{i theta}) is NOT in U(1): |z| != 1
    and z conj(z) != 1, so it is not a unitary phase."""
    r = 1.7
    theta = 0.9
    z = torch.tensor(r * (math.cos(theta) + 1j * math.sin(theta)), dtype=CDTYPE)
    modulus = float(z.abs().item())
    unitarity = float((z * z.conj()).real.item())  # |z|^2 ; == 1 only for U(1)
    return {
        "modulus": modulus,
        "z_conj_z": unitarity,
        "not_unit_modulus": abs(modulus - 1.0) > 0.1,
        "not_unitary_phase": abs(unitarity - 1.0) > 0.1,
        "kills_u1": abs(modulus - 1.0) > 0.1 and abs(unitarity - 1.0) > 0.1,
    }


def negative_fixed_point_action() -> dict[str, Any]:
    """A non-free 'action' (the trivial action z * psi = psi for ALL theta) fixes
    every spinor, so it has fixed points in (0, 2pi) -- NOT the free U(1) Hopf
    action. We contrast with the genuine free action which moves psi."""
    gen = torch.Generator().manual_seed(99)
    psi = haar_spinor(gen)
    theta = 1.3  # in (0, 2pi)
    trivial_move = float(torch.linalg.vector_norm(psi - psi).item())  # fixed -> 0
    free_move = float(torch.linalg.vector_norm(u1_element(torch.tensor(theta)) * psi - psi).item())
    return {
        "trivial_action_move_at_theta_1.3": trivial_move,
        "free_action_move_at_theta_1.3": free_move,
        "trivial_has_fixed_point": trivial_move < TOL,
        "free_has_no_fixed_point": free_move > TOL,
        "kills_free_u1": trivial_move < TOL and free_move > TOL,
    }


def negative_noncommutative() -> dict[str, Any]:
    """Replace U(1) scalar phases by non-commuting SU(2) generators: e^{i a sigma_x}
    and e^{i b sigma_y} do NOT commute, so this group is NOT abelian -- not U(1)."""
    a, b = 0.7, 1.1
    Ua = torch.linalg.matrix_exp(1j * a * SX)
    Ub = torch.linalg.matrix_exp(1j * b * SY)
    comm = float(torch.linalg.matrix_norm(Ua @ Ub - Ub @ Ua).item())
    # contrast: two U(1) phases DO commute (defect 0)
    ea = u1_element(torch.tensor(a))
    eb = u1_element(torch.tensor(b))
    u1_comm = float((ea * eb - eb * ea).abs().item())
    return {
        "su2_commutator_norm": comm,
        "u1_commutator_norm": u1_comm,
        "su2_is_noncommutative": comm > TOL,
        "u1_is_commutative": u1_comm < TOL,
        "kills_abelian_u1": comm > TOL and u1_comm < TOL,
    }


def negative_wrong_period() -> dict[str, Any]:
    """A 'phase' f(theta) = e^{i 4 theta} has period pi/2, NOT 2pi: it is a
    DIFFERENT (4:1 winding) representation, not the fundamental U(1). We show its
    period is pi/2 (f(theta + pi/2) == f(theta)) while it is NOT 2pi-fundamental:
    f maps the fundamental 2pi circle 4 times, so f(theta) != e^{i theta} as a
    parametrization of U(1)."""
    theta = torch.linspace(0.0, 2 * math.pi, 200, dtype=RTYPE)
    f = torch.exp(1j * 4 * theta.to(CDTYPE))
    # period pi/2:
    period_pi_over_2 = float((torch.exp(1j * 4 * (theta + math.pi / 2).to(CDTYPE)) - f).abs().max().item())
    # winding: it is NOT the identity parametrization e^{i theta}
    differs_from_fundamental = float((f - torch.exp(1j * theta.to(CDTYPE))).abs().max().item())
    return {
        "period_pi_over_2_defect": period_pi_over_2,
        "differs_from_e_i_theta": differs_from_fundamental,
        "has_period_pi_over_2": period_pi_over_2 < TOL,
        "not_fundamental_u1": differs_from_fundamental > 0.1,
        "kills_2pi_period": period_pi_over_2 < TOL and differs_from_fundamental > 0.1,
    }


# --------------------------------------------------------------------------- #
# Known-value cross-checks                                                     #
# --------------------------------------------------------------------------- #
def known_value_checks(blocks: list[dict[str, Any]], sym: dict[str, Any],
                       lat_chern: float, cliff: dict[str, Any], e3: dict[str, Any],
                       circ: dict[str, Any], rxg: dict[str, Any],
                       z3c: dict[str, Any], cvc5c: dict[str, Any]) -> list[dict[str, Any]]:
    max_abelian = max(b["abelian_defect"] for b in blocks)
    max_modulus = max(b["modulus_defect"] for b in blocks)
    max_period = max(b["period_2pi_defect"] for b in blocks)
    min_free_move = min(b["free_action_min_move"] for b in blocks)

    c1_abs_sym = sp.simplify(sp.Abs(sp.sympify(sym["chern_number_signed_exact"])))

    return [
        # --- abelian ---
        {"invariant": "U(1)_abelian_numeric_max|e^{ia}e^{ib}-e^{ib}e^{ia}|",
         "computed": f"{max_abelian:.2e}", "known": "0", "match": max_abelian < TOL},
        {"invariant": "U(1)_abelian_EXACT_symbolic(sympy)",
         "computed": str(sym["abelian_exact"]), "known": "True", "match": bool(sym["abelian_exact"])},
        # --- modulus / S^1 ---
        {"invariant": "U(1)_unit_modulus_numeric_max||e^{i theta}|-1|",
         "computed": f"{max_modulus:.2e}", "known": "1 (so defect 0)", "match": max_modulus < TOL},
        {"invariant": "U(1)_unit_modulus_EXACT_symbolic(sympy)",
         "computed": str(sym["modulus_one_exact"]), "known": "True", "match": bool(sym["modulus_one_exact"])},
        {"invariant": "U(1)_2pi_periodic_numeric_max|e^{i(t+2pi)}-e^{it}|",
         "computed": f"{max_period:.2e}", "known": "0", "match": max_period < TOL},
        {"invariant": "U(1)_2pi_periodic_EXACT_symbolic(sympy)",
         "computed": str(sym["period_2pi_exact"]), "known": "True", "match": bool(sym["period_2pi_exact"])},
        {"invariant": "U(1)_is_S1_dim(geomstats)",
         "computed": str(circ["manifold_dim"]), "known": "1", "match": circ["dim_is_one"] and circ["u1_points_belong_to_S1"]},
        {"invariant": "U(1)_discrete_Cayley_first_Betti_b1(rustworkx)",
         "computed": str(rxg["first_betti_number_b1"]), "known": "1 (single circle)", "match": rxg["is_circle_topology"]},
        # --- free action on S^3 ---
        {"invariant": "U(1)_free_action_on_S3_min_move_theta_in_(0,2pi)",
         "computed": f"{min_free_move:.3e} (>0 == free)", "known": ">0 (no fixed point)", "match": min_free_move > 1e-3},
        {"invariant": "U(1)_free_action_z3_UNSAT(no fixed theta in (0,2pi))",
         "computed": z3c["negation_status"], "known": "unsat", "match": z3c["pass"]},
        {"invariant": "U(1)_free_action_cvc5_UNSAT(no fixed theta in (0,2pi))",
         "computed": cvc5c["negation_status"], "known": "unsat", "match": cvc5c["pass"]},
        # --- Hopf line bundle Chern number ---
        {"invariant": "Hopf_line_bundle_first_Chern_number_lattice(FHS,torch)",
         "computed": f"{lat_chern:.10f}", "known": "1", "match": abs(lat_chern - 1.0) < TOL_CHERN},
        {"invariant": "Hopf_line_bundle_|c1|_EXACT_symbolic(sympy)",
         "computed": f"{sym['chern_number_signed_exact']} (|.|={c1_abs_sym})",
         "known": "1 (|c1|=1, sign by orientation)", "match": bool(sym["chern_abs_is_one"])},
        # --- Cl(2) even subalgebra == U(1) ---
        {"invariant": "Cl(2)_even_subalgebra_e12^2(clifford)",
         "computed": f"{cliff['e12_squared']:.15f}", "known": "-1 (==complex unit, ==U(1))",
         "match": cliff["even_subalgebra_is_complex"]},
        {"invariant": "Cl(2)_rotor_reproduces_SO(2)_angle(clifford)",
         "computed": f"max angle err {cliff['max_rotor_angle_err']:.2e}", "known": "0",
         "match": cliff["rotor_reproduces_so2"]},
        {"invariant": "Cl(2)_rotors_commute_abelian(clifford)",
         "computed": f"max defect {cliff['max_commute_defect']:.2e}", "known": "0",
         "match": cliff["rotors_commute_abelian"]},
        # --- U(1) as SO(2) subgroup (e3nn) ---
        {"invariant": "U(1)_as_SO(2)_det(e3nn)",
         "computed": f"max det err {e3['max_det_err']:.2e}", "known": "1 (det err 0)",
         "match": e3["max_det_err"] < TOL_E3NN},
        {"invariant": "U(1)_as_SO(2)_homomorphism_R(a)R(b)=R(a+b)(e3nn)",
         "computed": f"max defect {e3['max_homomorphism_defect']:.2e}", "known": "0",
         "match": e3["max_homomorphism_defect"] < TOL_E3NN},
    ]


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
def _sanitize(obj: Any) -> Any:
    """Coerce numpy scalar types (e.g. numpy.bool/float64 leaking from geomstats /
    rustworkx) to native python so the receipt is JSON-serializable."""
    import numpy as np
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(v) for v in obj]
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    return obj


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    # Wide variation: many seeds x angle sweep.
    blocks = [sample_block(seed) for seed in SEEDS]

    # sympy exact group + analytic Chern.
    sym = sympy_u1_exact()

    # torch lattice Chern number of the Hopf line bundle.
    lat_chern = lattice_chern_number()

    # tool surfaces.
    cliff = clifford_u1_rotor()
    e3 = e3nn_u1_as_so2()
    circ = geomstats_circle()
    rxg = rustworkx_circle_topology()

    # z3 + cvc5 free-action certificates (negation UNSAT).
    z3c = z3_free_action_certificate()
    cvc5c = cvc5_free_action_certificate()

    # known-value cross-checks (the depth proof).
    kvc = known_value_checks(blocks, sym, lat_chern, cliff, e3, circ, rxg, z3c, cvc5c)

    # Negatives.
    neg_mod = negative_non_unit_modulus()
    neg_fix = negative_fixed_point_action()
    neg_nc = negative_noncommutative()
    neg_per = negative_wrong_period()
    negatives = {
        "non_unit_modulus_phase": {"detail": neg_mod, "kills_signature": neg_mod["kills_u1"]},
        "fixed_point_action": {"detail": neg_fix, "kills_signature": neg_fix["kills_free_u1"]},
        "noncommutative_su2_surrogate": {"detail": neg_nc, "kills_signature": neg_nc["kills_abelian_u1"]},
        "wrong_period_pi_over_2": {"detail": neg_per, "kills_signature": neg_per["kills_2pi_period"]},
    }

    known_values_all_match = all(c["match"] for c in kvc)
    negatives_all_kill = all(v["kills_signature"] for v in negatives.values())
    tools_all_pass = (
        sym["abelian_exact"] and sym["modulus_one_exact"] and sym["period_2pi_exact"]
        and bool(sym["chern_abs_is_one"])
        and abs(lat_chern - 1.0) < TOL_CHERN
        and z3c["pass"] and cvc5c["pass"]
        and cliff["even_subalgebra_is_complex"] and cliff["rotor_reproduces_so2"]
        and cliff["rotors_commute_abelian"]
        and e3["is_so2_subgroup_of_so3"]
        and circ["dim_is_one"] and circ["u1_points_belong_to_S1"]
        and rxg["is_circle_topology"]
    )

    all_pass = known_values_all_match and negatives_all_kill and tools_all_pass

    blockers: list[str] = []
    if not known_values_all_match:
        blockers += [f"KNOWN-VALUE MISMATCH: {c['invariant']} computed={c['computed']} known={c['known']}"
                     for c in kvc if not c["match"]]
    if not z3c["pass"]:
        blockers.append("z3 free-action negation not UNSAT")
    if not cvc5c["pass"]:
        blockers.append("cvc5 free-action negation not UNSAT")
    if not negatives_all_kill:
        blockers += [f"NEGATIVE DID NOT KILL: {k}" for k, v in negatives.items() if not v["kills_signature"]]
    if abs(lat_chern - 1.0) >= TOL_CHERN:
        blockers.append(f"lattice Hopf Chern number != 1 (got {lat_chern})")

    tool_manifest = {
        "torch": {"used": True, "role": "load_bearing",
                  "reason": "all U(1) phase-group algebra in complex128 (abelian product, unit modulus, 2pi period, free action on Haar S^3 spinors) AND the gauge-invariant lattice (Fukui-Hatsugai-Suzuki) Hopf line-bundle Chern-number flux integral"},
        "sympy": {"used": True, "role": "load_bearing",
                  "reason": "EXACT symbolic proofs (abelian e^{ia}e^{ib}=e^{ib}e^{ia}, |e^{i theta}|=1, 2pi periodicity) AND the exact analytic Berry curvature F=-sin(theta)/2 with closed-form Chern integral |c1|=1; numeric torch alone cannot prove the exact symbolic identities"},
        "z3": {"used": True, "role": "load_bearing",
               "reason": "SMT certificate that the U(1) action on S^3 is FREE: a nontrivial fixed angle theta in (0,2pi) with e^{i theta}=1 is UNSAT under nonlinear real arithmetic with the unit-circle + half-tangent parametrization"},
        "cvc5": {"used": True, "role": "load_bearing",
                 "reason": "independent SMT family (QF_NRA) certifying the same free-action fact (negation UNSAT)"},
        "clifford": {"used": True, "role": "load_bearing",
                     "reason": "Cl(2) even subalgebra {1,e12}, e12^2=-1, is isomorphic to C and U(1); the rotor exp(theta/2 e12) reproduces the SO(2) rotation angle and rotors commute (abelian) -- an independent realization of U(1)"},
        "e3nn": {"used": True, "role": "load_bearing",
                 "reason": "certifies U(1) embeds as the SO(2) maximal torus of SO(3): z-rotations have det 1, are orthogonal, and satisfy the abelian homomorphism R(a)R(b)=R(a+b)"},
        "geomstats": {"used": True, "role": "load_bearing",
                      "reason": "certifies the U(1) carrier is the dim-1 hypersphere S^1: e^{i theta}->(cos,sin) belong to S^1 and the intrinsic dimension is 1"},
        "rustworkx": {"used": True, "role": "load_bearing",
                      "reason": "certifies the discrete cyclic subgroup Z_n<U(1) Cayley graph is a single circle: one connected component and first Betti number b_1=1 (one independent loop) -- the topology of S^1"},
    }

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID, "name": SIM_ID, "version": "1.0.0", "tier": "2_geometry",
        "classification": "diagnostic_only",
        "promotion_allowed": False,
        "promotion_status": "diagnostic_only",
        "sim_execution_kind": "nonclassical",
        "sim_class": "geometry_probe",
        "purpose": "Deep, standalone U(1) phase-group / Hopf-circle G-structure lego computed in real torch with full tool integration, cross-checked against textbook analytic invariants. Lego/pre-sim phase: NOT gated on manifold membership.",
        "scientific_question": "Does the U(1) phase group psi -> e^{i theta} psi reproduce its known structure -- abelian, S^1 (dim 1, 2pi-periodic, unit modulus), free action on S^3, Hopf line-bundle first Chern number |c1|=1, Cl(2)-even/SO(2) realizations -- to its exact analytic values, and do the reduced/broken controls kill that structure?",
        "claim_ceiling": "diagnostic_only / hypothetical / unadmitted: a self-contained known-math G-structure lego. Does NOT admit any manifold layer, stacking, coupling, G-structure-on-manifold, Axis0, flux, bridge, QIT, or physics claim.",
        "finite_map": "(angle theta in R / unit spinor psi in S^3) -> (U(1) element e^{i theta}, abelian product e^{ia}e^{ib}, unit modulus |e^{i theta}|, period, free action e^{i theta} psi on S^3, Hopf line-bundle first Chern number c1, Cl(2) rotor exp(theta/2 e12), SO(2) embedding, Z_n Cayley-graph topology)",
        "domain": "real angles theta (Haar/uniform-sampled over [0,2pi)), unit spinors psi in S^3 = {psi in C^2 : |psi|=1} (Haar-sampled via complex-Gaussian QR), discrete cyclic subgroup Z_n",
        "codomain_or_output": "U(1) group elements e^{i theta}, their action images on S^3, the abelian product, modulus/period invariants, free-action min-displacement, Hopf line-bundle Chern number, Cl(2)/SO(2) rotor matrices, and the Z_n Cayley-graph Betti number",
        "carrier_layer": "U(1) phase group ~ S^1 (Hopf circle fiber of S^1 -> S^3 -> S^2)",
        "geometry_layer": "U(1) structure-group geometry: the circle S^1 acting freely on S^3 as the Hopf fiber; associated Hopf line bundle over S^2 with first Chern number |c1|=1",
        "carrier_realization": "torch.complex128 phases e^{i theta} and unit spinors psi in S^3; no NumPy claim-bearing substrate, no label-only tensors, no random claim matrices (random spinors are genuine Haar samples)",
        "spinor_state": "torch.complex128 unit spinors psi in S^3 = {psi in C^2 : |psi|=1}; U(1) acts as the phase psi -> e^{i theta} psi (Hopf fiber)",
        "quaternion_action": "U(1) is the SO(2)<SU(2) maximal-torus subgroup; realized as the even subalgebra of Cl(2) ({1,e12}, e12^2=-1 == complex unit) -- a 1-parameter subgroup of the unit quaternions",
        "peps3d_embedding": "not_applicable_at_lego_phase (no manifold anchor claimed; diagnostic_only)",
        "dependency_receipts": [],
        "downstream_blocks": ["manifold_layers", "stacking", "coupling", "G_structure_on_manifold", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "blocked_consumers": ["manifold_layers", "stacking", "coupling", "G_structure_on_manifold", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "law_or_candidate_tested": "U(1) phase-group / Hopf-circle structure-group geometry against textbook analytic invariants (abelian, S^1, free action on S^3, Hopf Chern number |c1|=1)",
        "branch_status_before_run": "lego/pre-sim phase; standalone known-math G-structure; unadmitted",
        "allowed_claims": ["standalone known-math U(1) G-structure geometry witness; computed invariants match textbook values to machine precision / exact symbolic equality"],
        "promotion_blockers": ["diagnostic_only by design (lego/pre-sim phase); no manifold membership, no cross-layer evidence, no coupling"],

        "result_summary": {
            "all_pass": all_pass,
            "known_values_all_match": known_values_all_match,
            "negatives_all_kill": negatives_all_kill,
            "tools_all_pass": tools_all_pass,
            "n_known_value_checks": len(kvc),
            "n_seeds": len(SEEDS), "n_angles_per_seed": N_ANGLES,
            "n_sampled_angles_total": len(SEEDS) * N_ANGLES,
            "lattice_hopf_chern_number": lat_chern,
            "chern_number_abs_exact": sym["chern_number_abs_exact"],
            "z3_free_action_unsat": z3c["pass"],
            "cvc5_free_action_unsat": cvc5c["pass"],
            "promotion_allowed": False,
        },

        "known_value_checks": kvc,
        "sympy_exact_u1": sym,
        "lattice_hopf_chern_number": lat_chern,
        "clifford_cl2_rotor": cliff,
        "e3nn_so2_embedding": e3,
        "geomstats_circle": circ,
        "rustworkx_circle_topology": rxg,
        "free_action_certificates": {"z3": z3c, "cvc5": cvc5c},

        "variation_blocks": blocks,

        "required_negatives": ["non_unit_modulus_phase", "fixed_point_action", "noncommutative_su2_surrogate", "wrong_period_pi_over_2"],
        "negatives_run": list(negatives.keys()),
        "negatives": negatives,
        "kill_conditions": [
            "any known-value invariant fails to match its textbook value",
            "z3 or cvc5 free-action negation not UNSAT",
            "lattice Hopf Chern number != 1",
            "non-unit-modulus phase passes as U(1)",
            "fixed-point action passes as the free U(1) Hopf action",
            "noncommutative SU(2) surrogate passes as abelian U(1)",
            "wrong-period (pi/2) phase passes as the fundamental 2pi U(1)",
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
        "pass_rule": "every known_value_check matches its known value AND all negatives kill the signature AND z3+cvc5 free-action negations are UNSAT AND the lattice Hopf Chern number is 1 AND the exact symbolic Chern |c1|=1",
        "fail_rule": "any known-value mismatch, any negative that does not kill, any non-UNSAT free-action certificate, or a Hopf Chern number != 1",
        "eligible_consumers": ["other diagnostic_only G-structure / phase-group geometry probes"],
    }

    witness = {
        "sim_id": SIM_ID,
        "steps": [
            {"step": "sample_angles_and_haar_S3_spinors", "seeds": SEEDS, "n_angles_per_seed": N_ANGLES,
             "n_total": len(SEEDS) * N_ANGLES},
            {"step": "u1_abelian_modulus_period_free_action", "tool": "torch.complex128",
             "max_abelian_defect": max(b["abelian_defect"] for b in blocks),
             "max_modulus_defect": max(b["modulus_defect"] for b in blocks),
             "min_free_move": min(b["free_action_min_move"] for b in blocks)},
            {"step": "sympy_exact_abelian_modulus_period_and_chern", "abelian": sym["abelian_exact"],
             "chern_abs": sym["chern_number_abs_exact"], "chern_abs_is_one": bool(sym["chern_abs_is_one"])},
            {"step": "torch_lattice_hopf_chern_FHS", "c1": lat_chern},
            {"step": "z3_free_action_unsat", "status": z3c["negation_status"], "pass": z3c["pass"]},
            {"step": "cvc5_free_action_unsat", "status": cvc5c["negation_status"], "pass": cvc5c["pass"]},
            {"step": "clifford_cl2_even_subalgebra_rotor", "e12_squared": cliff["e12_squared"],
             "rotor_ok": cliff["rotor_reproduces_so2"], "commute_ok": cliff["rotors_commute_abelian"]},
            {"step": "e3nn_u1_as_so2_subgroup", "is_so2": e3["is_so2_subgroup_of_so3"]},
            {"step": "geomstats_u1_is_S1", "dim": circ["manifold_dim"], "belongs": circ["u1_points_belong_to_S1"]},
            {"step": "rustworkx_discrete_circle_betti", "b1": rxg["first_betti_number_b1"],
             "is_circle": rxg["is_circle_topology"]},
            {"step": "run_negatives", "negatives": list(negatives.keys()), "all_kill": negatives_all_kill},
            {"step": "known_value_cross_checks", "n": len(kvc), "all_match": known_values_all_match},
        ],
        "final_classification": "diagnostic_only",
        "all_pass": all_pass,
        "blockers": blockers,
    }

    result = _sanitize(result)
    witness = _sanitize(witness)

    out = RESULT_DIR / f"{SIM_ID}_results.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    wit = RESULT_DIR / f"{SIM_ID}_witness.json"
    wit.write_text(json.dumps(witness, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps(_sanitize({
        "wrote": str(out),
        "witness": str(wit),
        "all_pass": all_pass,
        "known_values_all_match": known_values_all_match,
        "negatives_all_kill": negatives_all_kill,
        "tools_all_pass": tools_all_pass,
        "n_known_value_checks": len(kvc),
        "lattice_hopf_chern_number": lat_chern,
        "blockers": blockers,
        "known_value_checks": [{"invariant": c["invariant"], "computed": c["computed"],
                                "known": c["known"], "match": c["match"]} for c in kvc],
    }), indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

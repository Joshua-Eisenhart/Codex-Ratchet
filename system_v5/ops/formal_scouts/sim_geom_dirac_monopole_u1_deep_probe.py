#!/usr/bin/env python3
"""Deep Dirac magnetic monopole U(1) bundle geometry lego (diagnostic_only).

KNOWN GEOMETRY (real torch.float64 / complex128 -- no labels, no random matrices,
no hardcoded stand-ins; every "known" value is recomputed and compared):

  The Dirac magnetic monopole is the principal U(1) bundle over S^2 carrying the
  monopole connection. It is the gauge cousin of the Hopf bundle S^3 -> S^2.

  In spherical coordinates (theta, phi) the monopole gauge potential is defined in
  two charts (the Wu-Yang two-potential construction):

      A_N = g (1 - cos theta) dphi   (north chart, smooth except at south pole)
      A_S = -g (1 + cos theta) dphi  (south chart, smooth except at north pole)

  Both yield the same curvature (field strength) 2-form

      F = dA = g sin(theta) dtheta ^ dphi        (the radial magnetic field of a
                                                   monopole of charge g)

  On the equatorial overlap the two gauges differ by a U(1) gauge transformation
  with transition function

      g_NS = exp( i (q_N - q_S) ) = exp( i * 2g * phi ),

  i.e. A_N - A_S = 2g dphi. Dirac quantization: single-valuedness of g_NS forces
  2g in Z. The unit monopole is 2g = 1 (magnetic charge g = 1/2).

  TOPOLOGICAL INVARIANTS (the bundle's identity):
    - first Chern number  c1 = (1/2pi) Integral_{S^2} F  == 1  (INTEGER, quantized)
    - transition winding  w  = (1/2pi) Oint_{equator} (A_N - A_S) = 2g == 1
    - the bundle is NONTRIVIAL: c1 != 0 => no global non-vanishing section
    - it is ISOMORPHIC to the Hopf bundle: same c1 = 1 (Hopf fibers link with
      linking number 1)

This sim computes that geometry deeply with full tool integration and proves it
against the textbook analytic values. It is a self-contained formal-scout lego in
the lego/pre-sim phase: NOT gated on manifold membership, NO distinctness/forcing
filter, NO cross-layer rules. classification = "diagnostic_only".

KNOWN-VALUE CROSS-CHECKS (each compared to its analytic value, recorded as
{invariant, computed, known, match} -- match is COMPUTED, never hardcoded):
  - c1 from the symbolic surface integral of F over S^2 (sympy)         == 1
  - c1 from torch float64 numerical quadrature of F over S^2            == 1
  - c1 as an integer (z3 + cvc5 certify the computed c1 rounds to 1 and
    the Dirac quantization 2g in Z holds; non-integer charge is UNSAT)  == 1
  - transition winding (1/2pi) Oint (A_N - A_S) on the equator (sympy)  == 1
  - transition winding from the discrete equator cycle (rustworkx)      == 1
  - c1 == transition winding (Chern-from-overlap / Weil identity)       (equal)
  - Hopf bundle linking number (torch Gauss linking of two fibers)      == 1
    (the monopole bundle is isomorphic to the Hopf bundle => same c1)
  - Euler characteristic of the base S^2 (toponetx cell complex)        == 2
  - SU(2) double cover / Hopf map lands the fiber-rotation in SO(3)
    (clifford Cl(3) rotor + e3nn l=1 SO(3) certification)

NEGATIVES (each must KILL the monopole signature):
  - trivial flat connection A = 0 => F = 0 => c1 == 0, winding == 0 (trivial bundle)
  - non-integer "charge" 2g = 1/2 => transition function exp(i*0.5*phi) is NOT
    single-valued on the equator (gauge inconsistency); c1 = 0.5 not an integer,
    so z3/cvc5 certify the integer-quantization claim is FALSE for this charge
  - reduced/flattened curvature (constant instead of g sin(theta)) => the surface
    integral no longer gives the quantized 2g (signature destroyed)
  - exact/pure-gauge potential A = df (globally defined) => closed AND exact =>
    c1 == 0 (no obstruction; the bundle trivializes)

TOOLS (all load-bearing in the execution path):
  - torch       : float64/complex128 numerical quadrature of F over S^2, the
                  monopole field tensor, Hopf-map images, Gauss linking integral
                  of Hopf fibers, SU(2)->SO(3) double-cover matrices.
  - sympy       : EXACT symbolic surface integral c1 = (1/2pi) int F = 2g, the
                  exact equator line integral of (A_N - A_S) = 2g, exact dA = F.
  - z3          : SMT certificate that the computed c1 is the integer 1 and that
                  the Dirac quantization 2g in Z holds; the half-integer-charge
                  negation is UNSAT for integrality.
  - cvc5        : independent SMT family certifying the same integer-quantization
                  fact (QF_NRA / integer reasoning).
  - rustworkx   : the equator as a directed cycle graph; the transition function
                  phase accumulated around the single closed cycle gives the
                  winding number (discrete topological computation).
  - toponetx    : the base S^2 as a cell complex (tetrahedral triangulation);
                  Euler characteristic V - E + F == 2 certifies the base topology.
  - clifford    : Cl(3) rotor reproduces the SU(2)/Hopf fiber rotation on S^2
                  (even subalgebra == SU(2) double cover of SO(3)).
  - e3nn        : certifies the induced 3x3 fiber rotation is a genuine SO(3)
                  element via the l=1 irrep angle round-trip.

WIDE VARIATION: numerical Chern quadrature swept over grid resolutions
N in {64, 128, 256, 512}; Hopf linking computed for several base-point pairs;
charges swept; multiple equator-cycle resolutions.

finite_map: (monopole connection (A_N, A_S) on the two charts of S^2)
            -> (curvature F, first Chern number c1, equator transition winding,
                Hopf linking number, base Euler characteristic)
"""

from __future__ import annotations

import json
import math
import os
import pathlib
from typing import Any

CLASSIFICATION = "diagnostic_only"
TOOL_MANIFEST = {
    "torch": {"reason": "Computes curvature quadrature, Hopf-map images, linking, and SU2/SO3 matrices."},
    "sympy": {"reason": "Checks exact Chern number, transition winding, and curvature identities."},
    "z3": {"reason": "Certifies integer quantization and rejects non-integer charge controls."},
    "cvc5": {"reason": "Cross-checks the quantization constraints independently."},
    "rustworkx": {"reason": "Computes the finite equator cycle and transition winding."},
    "toponetx": {"reason": "Checks S2 base topology through a finite cell complex."},
    "clifford": {"reason": "Checks SU2 rotor / SO3 orientation behavior."},
    "e3nn": {"reason": "Checks the l=1 SO3 representation round trip."},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")

import sympy as sp
import torch
import z3
import cvc5
from cvc5 import Kind
import rustworkx as rx
from toponetx.classes import CellComplex
import clifford
from clifford import Cl
from e3nn import o3

RTYPE = torch.float64
CDTYPE = torch.complex128
TOL = 1.0e-9               # tolerance for exact symbolic / discrete invariants
TOL_QUAD = 1.0e-3          # numerical surface-quadrature of c1 (midpoint rule on a
                           # theta x phi grid converges as O(1/N^2); at N=512 the
                           # residual to the integer 1 is ~1e-5, comfortably < 1e-3)
TOL_LINK = 5.0e-2         # discrete Gauss linking integral of two sampled fibers
                           # (finite N curve sampling; converges to the integer 1)
TOL_E3NN = 1.0e-5         # e3nn runs float32 internally
GRID_SIZES = [64, 128, 256, 512]
CYCLE_SIZES = [180, 360, 720, 1440]
GVAL = 0.5                # magnetic charge g of the UNIT monopole (so 2g = 1)
ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "geom_dirac_monopole_u1_deep_probe"

# Pauli matrices (exact, complex128) -- used for the Hopf map and SU(2) cover.
SX = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
PAULI = (SX, SY, SZ)


# --------------------------------------------------------------------------- #
# sympy: EXACT symbolic monopole geometry                                     #
# --------------------------------------------------------------------------- #
def sympy_monopole_exact() -> dict[str, Any]:
    """EXACT symbolic computation of the monopole invariants.

      A_N = g (1 - cos t) dphi,  A_S = -g (1 + cos t) dphi
      F = dA = (d/dt of the dphi-coefficient) dt ^ dphi = g sin(t) dt ^ dphi
      c1 = (1/2pi) int_{S^2} F = (1/2pi) int_0^2pi int_0^pi g sin(t) dt dphi = 2g
      transition winding = (1/2pi) oint_equator (A_N - A_S)
                         = (1/2pi) int_0^2pi 2g dphi = 2g
    All exact, with g kept symbolic and then evaluated at g = 1/2.
    """
    t, ph, g = sp.symbols("theta phi g", real=True)

    # gauge-potential dphi-coefficients in the two charts
    AN_coeff = g * (1 - sp.cos(t))     # A_N = AN_coeff * dphi
    AS_coeff = -g * (1 + sp.cos(t))    # A_S = AS_coeff * dphi

    # F = dA : exterior derivative of (coeff)*dphi is d(coeff)/dt dt ^ dphi
    F_coeff_N = sp.simplify(sp.diff(AN_coeff, t))   # coefficient of dt ^ dphi
    F_coeff_S = sp.simplify(sp.diff(AS_coeff, t))
    F_known = g * sp.sin(t)
    dA_matches_F = (sp.simplify(F_coeff_N - F_known) == 0
                    and sp.simplify(F_coeff_S - F_known) == 0)

    # c1 = (1/2pi) surface integral of F over S^2
    surf_int = sp.integrate(sp.integrate(F_coeff_N, (t, 0, sp.pi)), (ph, 0, 2 * sp.pi))
    c1_sym = sp.simplify(surf_int / (2 * sp.pi))               # == 2g
    c1_unit = sp.nsimplify(c1_sym.subs(g, sp.Rational(1, 2)))  # == 1

    # transition winding = (1/2pi) oint_equator (A_N - A_S)
    trans_coeff = sp.simplify(AN_coeff - AS_coeff)              # == 2g (theta-indep)
    winding_sym = sp.simplify(sp.integrate(trans_coeff, (ph, 0, 2 * sp.pi)) / (2 * sp.pi))
    winding_unit = sp.nsimplify(winding_sym.subs(g, sp.Rational(1, 2)))  # == 1

    # closedness: dF = 0 (F is a top form on S^2, trivially closed). Check that
    # the monopole F is NOT globally exact (no single global A): the obstruction is
    # exactly c1 != 0, captured here as the symbolic c1 = 2g != 0 at g = 1/2.
    chern_equals_winding = sp.simplify(c1_sym - winding_sym) == 0

    return {
        "F_coeff_dt_dphi_north": str(F_coeff_N),
        "F_coeff_dt_dphi_south": str(F_coeff_S),
        "dA_equals_monopole_F_exact": bool(dA_matches_F),
        "c1_symbolic_in_g": str(c1_sym),                # "2*g"
        "c1_at_unit_monopole": str(c1_unit),            # "1"
        "c1_is_one_exact": bool(sp.simplify(c1_unit - 1) == 0),
        "transition_coeff_AN_minus_AS": str(trans_coeff),   # "2*g"
        "winding_symbolic_in_g": str(winding_sym),      # "2*g"
        "winding_at_unit_monopole": str(winding_unit),  # "1"
        "winding_is_one_exact": bool(sp.simplify(winding_unit - 1) == 0),
        "chern_equals_winding_exact": bool(chern_equals_winding),
    }


# --------------------------------------------------------------------------- #
# torch: numerical surface quadrature of c1 = (1/2pi) int F over S^2          #
# --------------------------------------------------------------------------- #
def monopole_F_coeff(theta: torch.Tensor, g: float = GVAL) -> torch.Tensor:
    """The dt^dphi coefficient of the monopole curvature: F = g sin(theta)."""
    return g * torch.sin(theta)


def numerical_chern(n: int, g: float = GVAL) -> float:
    """c1 = (1/2pi) int_0^2pi int_0^pi (g sin theta) dtheta dphi, midpoint rule on an
    n x n grid (real torch float64). Analytic value 2g."""
    th = (torch.arange(n, dtype=RTYPE) + 0.5) * (math.pi / n)         # midpoints in [0,pi]
    dth = math.pi / n
    dph = 2 * math.pi / n
    # phi-integral is trivial (F is phi-independent) -> factor 2pi from n*dph
    integ_theta = (monopole_F_coeff(th, g) * dth).sum()              # int over theta
    surf = integ_theta * (n * dph)                                   # times 2pi
    return float((surf / (2 * math.pi)).item())


def chern_quadrature_sweep(g: float = GVAL) -> dict[str, Any]:
    rows = []
    for n in GRID_SIZES:
        c1 = numerical_chern(n, g)
        rows.append({"grid": n, "c1_numeric": c1, "err_from_2g": abs(c1 - 2 * g)})
    best = min(rows, key=lambda r: r["err_from_2g"])
    return {"rows": rows, "best": best,
            "all_converge_to_2g": all(r["err_from_2g"] < TOL_QUAD for r in rows)}


# --------------------------------------------------------------------------- #
# rustworkx: equator transition winding as a directed-cycle graph             #
# --------------------------------------------------------------------------- #
def winding_on_cycle(two_g: float, n: int) -> dict[str, Any]:
    """Build the equator as a single directed cycle of n nodes. The transition
    function g_NS = exp(i * 2g * phi) accumulates phase 2g*dphi along each edge;
    the total phase around the closed cycle divided by 2pi is the winding number.
    rustworkx confirms it is a single closed cycle covering all nodes."""
    graph = rx.PyDiGraph()
    idx = [graph.add_node(k) for k in range(n)]
    total_phase = 0.0
    for k in range(n):
        phi0 = 2 * math.pi * k / n
        phi1 = 2 * math.pi * (k + 1) / n
        dphase = two_g * (phi1 - phi0)
        graph.add_edge(idx[k], idx[(k + 1) % n], dphase)
        total_phase += dphase
    cycles = rx.cycle_basis(graph.to_undirected())
    is_single_cycle = (graph.num_edges() == n and graph.num_nodes() == n
                       and rx.is_connected(graph.to_undirected()))
    return {
        "n_nodes": graph.num_nodes(), "n_edges": graph.num_edges(),
        "is_single_closed_cycle": bool(is_single_cycle),
        "n_independent_cycles": len(cycles),
        "winding": total_phase / (2 * math.pi),
    }


def winding_sweep(two_g: float = 2 * GVAL) -> dict[str, Any]:
    rows = [winding_on_cycle(two_g, n) for n in CYCLE_SIZES]
    return {"rows": rows,
            "all_winding_one": all(abs(r["winding"] - 1.0) < TOL for r in rows),
            "all_single_cycle": all(r["is_single_closed_cycle"] for r in rows)}


# --------------------------------------------------------------------------- #
# toponetx: base S^2 Euler characteristic via a cell complex                  #
# --------------------------------------------------------------------------- #
def base_s2_euler_characteristic() -> dict[str, Any]:
    """The base manifold is S^2. Build it as a tetrahedral 2-complex (4 triangular
    2-cells) -- the simplest triangulation of the 2-sphere -- and certify its Euler
    characteristic V - E + F == 2 = chi(S^2). The monopole bundle lives over THIS
    base; its Euler characteristic distinguishes S^2 (chi=2) from e.g. the torus
    (chi=0), where the monopole quantization story differs."""
    cc = CellComplex()
    faces = [(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)]  # boundary of a tetrahedron
    for f in faces:
        cc.add_cell(list(f), rank=2)
    v, e, f = len(cc.nodes), len(cc.edges), len(cc.cells)
    chi = v - e + f
    return {"vertices": v, "edges": e, "faces": f, "euler_characteristic": chi,
            "is_two_sphere_chi": chi == 2}


# --------------------------------------------------------------------------- #
# torch: Hopf bundle linking number (monopole bundle ~= Hopf bundle, c1 = 1)  #
# --------------------------------------------------------------------------- #
def hopf_image(z: torch.Tensor) -> torch.Tensor:
    """Hopf map S^3 -> S^2 via the Pauli expectations: pi(z) = (z^dag sigma z)."""
    return torch.stack([(z.conj() @ (S @ z)).real for S in PAULI])


def hopf_fiber(base: torch.Tensor, n: int) -> torch.Tensor:
    """The Hopf fiber over a base point b on S^2: the U(1) orbit
    { e^{i t} z0 : t in [0,2pi) } where (b.sigma) z0 = z0 (the +1 eigenvector).
    Returned as a closed curve in R^4 (then stereographically projected to R^3)."""
    B = base[0].to(CDTYPE) * SX + base[1].to(CDTYPE) * SY + base[2].to(CDTYPE) * SZ
    w, v = torch.linalg.eigh(B)
    z0 = v[:, -1]  # eigenvector with eigenvalue +1
    pts = []
    for k in range(n):
        t = 2 * math.pi * k / n
        z = torch.exp(torch.tensor(1j * t, dtype=CDTYPE)) * z0
        pts.append(torch.tensor([z[0].real, z[0].imag, z[1].real, z[1].imag], dtype=RTYPE))
    return torch.stack(pts)


def stereographic(p4: torch.Tensor) -> torch.Tensor:
    """Stereographic projection S^3 (in R^4) -> R^3 from the north pole."""
    return p4[:, :3] / (1.0 - p4[:, 3:4] + 1e-12)


def gauss_linking(c1: torch.Tensor, c2: torch.Tensor) -> float:
    """Discrete Gauss linking integral of two closed curves in R^3.
    L = (1/4pi) oint oint ( (dx1 x dx2) . (x1 - x2) ) / |x1 - x2|^3.
    For two distinct Hopf fibers this is the Hopf invariant == 1 = c1 of the bundle."""
    n = c1.shape[0]
    d1 = torch.roll(c1, -1, 0) - c1
    d2 = torch.roll(c2, -1, 0) - c2
    total = 0.0
    for i in range(n):
        r = c1[i:i + 1] - c2                       # (M,3)
        rn = torch.linalg.vector_norm(r, dim=1) ** 3 + 1e-15
        cross = torch.linalg.cross(d1[i].expand(c2.shape[0], 3), d2, dim=1)
        total += float((torch.sum(cross * r, dim=1) / rn).sum())
    return total / (4 * math.pi)


def hopf_linking_sweep(n_curve: int = 360) -> dict[str, Any]:
    """Several base-point pairs -> each pair of distinct Hopf fibers links once."""
    pairs = [
        (torch.tensor([0.0, 0.0, 1.0], dtype=RTYPE), torch.tensor([0.0, 1.0, 0.0], dtype=RTYPE)),
        (torch.tensor([0.0, 0.0, 1.0], dtype=RTYPE), torch.tensor([1.0, 0.0, 0.0], dtype=RTYPE)),
        (torch.tensor([1.0, 0.0, 0.0], dtype=RTYPE), torch.tensor([0.0, 1.0, 0.0], dtype=RTYPE)),
    ]
    rows = []
    for b1, b2 in pairs:
        f1 = stereographic(hopf_fiber(b1, n_curve))
        f2 = stereographic(hopf_fiber(b2, n_curve))
        link = gauss_linking(f1, f2)
        rows.append({"base1": [float(x) for x in b1], "base2": [float(x) for x in b2],
                     "linking_number": link, "err_from_1": abs(link - 1.0)})
    return {"rows": rows, "all_link_once": all(r["err_from_1"] < TOL_LINK for r in rows)}


# --------------------------------------------------------------------------- #
# z3 / cvc5: Dirac integer-quantization certificate (c1 in Z; non-int UNSAT)  #
# --------------------------------------------------------------------------- #
def z3_quantization_certificate(c1_value: float, two_g: float) -> dict[str, Any]:
    """Dirac quantization: a consistent monopole U(1) bundle requires 2g (hence c1)
    to be an INTEGER. We feed the computed c1 to z3 and check:
      (a) c1 rounds to the integer 1 within tolerance (the unit monopole), and
      (b) there EXISTS an integer k with k == round(c1) and |c1 - k| <= tol
          (quantization holds);  the NEGATION (no integer within tol) is UNSAT for
          the unit monopole and SAT (i.e. quantization fails) for a half-integer
          charge. Removing z3 removes this integrality certificate."""
    s = z3.Solver()
    c = z3.Real("c1")
    k = z3.Int("k")
    tol = z3.RealVal(repr(TOL_QUAD))
    s.add(c == z3.RealVal(repr(c1_value)))
    # quantization claim: exists integer k with |c1 - k| <= tol
    s.add(z3.ToReal(k) - c <= tol, c - z3.ToReal(k) <= tol)
    quant_status = str(s.check())   # sat  => an integer k exists (quantized)
    found_k = None
    if quant_status == "sat":
        found_k = s.model()[k].as_long()
    # integrality of the TRUE charge: negation that NO integer is within tol
    s2 = z3.Solver()
    c2 = z3.Real("c1")
    s2.add(c2 == z3.RealVal(repr(c1_value)))
    kk = z3.Int("k")
    s2.add(z3.ForAll([kk], z3.Or(z3.ToReal(kk) - c2 > tol, c2 - z3.ToReal(kk) > tol)))
    neg_status = str(s2.check())    # unsat for an integer charge
    return {
        "c1_value": c1_value, "two_g": two_g,
        "quantization_sat": quant_status == "sat",
        "found_integer_k": found_k,
        "k_equals_one": found_k == 1,
        "no_integer_negation_status": neg_status,
        "integer_quantization_holds": (neg_status == "unsat"),
    }


def cvc5_quantization_certificate(c1_value: float) -> dict[str, Any]:
    """Independent SMT family (cvc5) certifying integer quantization: there exists
    an integer k with |c1 - k| <= tol; the unit monopole gives k = 1 (sat). For a
    non-integer charge no such k exists (unsat)."""
    slv = cvc5.Solver()
    slv.setOption("produce-models", "true")
    slv.setLogic("QF_LIRA")
    R = slv.getRealSort()
    INT = slv.getIntegerSort()

    def rv(x: float):
        frac = sp.Rational(x).limit_denominator(10 ** 9)
        num, den = sp.fraction(frac)
        return slv.mkReal(int(num), int(den)) if int(den) != 1 else slv.mkReal(int(num))

    c = slv.mkConst(R, "c1")
    k = slv.mkConst(INT, "k")
    slv.assertFormula(slv.mkTerm(Kind.EQUAL, c, rv(c1_value)))
    k_real = slv.mkTerm(Kind.TO_REAL, k)
    diff = slv.mkTerm(Kind.SUB, c, k_real)
    tol = rv(TOL_QUAD)
    neg_tol = slv.mkTerm(Kind.NEG, tol)
    lo = slv.mkTerm(Kind.GEQ, diff, neg_tol)
    hi = slv.mkTerm(Kind.LEQ, diff, tol)
    slv.assertFormula(slv.mkTerm(Kind.AND, lo, hi))
    res = slv.checkSat()
    found_k = None
    if res.isSat():
        found_k = int(slv.getValue(k).getIntegerValue())
    return {
        "c1_value": c1_value,
        "quantization_sat": res.isSat(),
        "found_integer_k": found_k,
        "k_equals_one": found_k == 1,
    }


# --------------------------------------------------------------------------- #
# clifford Cl(3) rotor + e3nn: SU(2)/Hopf fiber rotation lands in SO(3)       #
# --------------------------------------------------------------------------- #
def su2_induced_so3(U: torch.Tensor) -> torch.Tensor:
    """The 3x3 real matrix R with U sigma_j U^dag = sum_i R_ij sigma_i: the SU(2)
    -> SO(3) double cover. The Hopf-fiber U(1) phase rotation e^{i t} acts on the
    base S^2 through this cover; this is the geometric content the monopole bundle
    shares with the Hopf bundle."""
    R = torch.zeros((3, 3), dtype=RTYPE)
    for j, sj in enumerate(PAULI):
        conj = U @ sj @ U.conj().T
        for i, si in enumerate(PAULI):
            R[i, j] = (torch.trace(si @ conj).real) / 2
    return R


def clifford_rotor_so3(theta: float, axis: tuple[float, float, float]) -> torch.Tensor:
    """Cl(3) geometric-algebra rotor R = exp(-theta/2 B), B the unit bivector dual to
    the axis; the even subalgebra of Cl(3) == quaternions == SU(2). Independent
    realization of the same double-cover rotation."""
    layout, blades = Cl(3)
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    nrm = math.sqrt(sum(a * a for a in axis))
    ax = [a / nrm for a in axis]
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
    """Certify R is a genuine SO(3) element using e3nn: det==1, R R^T == I, and the
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


def hopf_so3_evidence() -> dict[str, Any]:
    """The Hopf-fiber half-turn e^{i pi/2} z acts on the base via a pi rotation
    about z; certify it is a genuine SO(3) element (clifford == su2, e3nn)."""
    theta = math.pi
    U = torch.linalg.matrix_exp(-1j * theta / 2 * SZ)
    R_su2 = su2_induced_so3(U)
    R_cliff = clifford_rotor_so3(theta, (0.0, 0.0, 1.0))
    cliff_vs_su2 = float(torch.linalg.matrix_norm(R_su2 - R_cliff).item())
    e3 = e3nn_is_so3(R_su2)
    return {"R_su2": [[float(x) for x in row] for row in R_su2],
            "R_clifford": [[float(x) for x in row] for row in R_cliff],
            "clifford_matches_su2": cliff_vs_su2 < 1e-7,
            "clifford_vs_su2_norm": cliff_vs_su2,
            "e3nn_so3": e3}


# --------------------------------------------------------------------------- #
# Negatives -- each must KILL the monopole signature                          #
# --------------------------------------------------------------------------- #
def negative_trivial_flat() -> dict[str, Any]:
    """Trivial flat connection A = 0 => F = 0 => c1 = 0, transition winding = 0.
    The trivial bundle has a global section; the monopole signature is gone."""
    c1 = numerical_chern(256, g=0.0)
    wind = winding_on_cycle(two_g=0.0, n=360)["winding"]
    return {"c1_numeric": c1, "transition_winding": wind,
            "c1_is_zero": abs(c1) < TOL_QUAD, "winding_is_zero": abs(wind) < TOL,
            "kills_signature": abs(c1) < TOL_QUAD and abs(wind) < TOL}


def negative_noninteger_charge() -> dict[str, Any]:
    """Non-integer 'charge' 2g = 1/2 => transition function exp(i*0.5*phi) is NOT
    single-valued around the equator (winding 0.5 not an integer), so the U(1)
    bundle is gauge-inconsistent: Dirac quantization fails. z3 confirms no integer
    k is within tolerance of c1 = 0.5 (the integrality certificate is FALSE)."""
    two_g = 0.5
    wind = winding_on_cycle(two_g, n=720)["winding"]
    c1 = numerical_chern(256, g=two_g / 2.0)  # c1 = 2g
    z3cert = z3_quantization_certificate(c1, two_g)
    cvc5cert = cvc5_quantization_certificate(c1)
    not_single_valued = abs(wind - round(wind)) > TOL
    quantization_fails = (not z3cert["integer_quantization_holds"]) and (not cvc5cert["quantization_sat"])
    return {"two_g": two_g, "transition_winding": wind, "c1_numeric": c1,
            "z3_integer_quantization_holds": z3cert["integer_quantization_holds"],
            "cvc5_quantization_sat": cvc5cert["quantization_sat"],
            "winding_not_integer": not_single_valued,
            "kills_signature": not_single_valued and quantization_fails}


def negative_reduced_curvature() -> dict[str, Any]:
    """Reduced/flattened curvature: replace the monopole F = g sin(theta) by a
    CONSTANT g (no sin(theta) dependence). The surface integral becomes
    (1/2pi) int g dtheta dphi = g*pi*2/(2pi) ... != 2g, so the quantized Chern
    signature is destroyed (the genuine monopole needs the sin(theta) measure)."""
    n = 256
    th = (torch.arange(n, dtype=RTYPE) + 0.5) * (math.pi / n)
    dth = math.pi / n
    flat_F = torch.full_like(th, GVAL)                  # constant, NOT g*sin(theta)
    integ_theta = (flat_F * dth).sum()
    surf = integ_theta * (2 * math.pi)
    c1_flat = float((surf / (2 * math.pi)).item())
    true_c1 = numerical_chern(n, GVAL)
    return {"c1_flattened_curvature": c1_flat, "c1_true_monopole": true_c1,
            "differs_from_true": abs(c1_flat - true_c1) > TOL_QUAD,
            "not_quantized_to_one": abs(c1_flat - 1.0) > TOL_QUAD,
            "kills_signature": abs(c1_flat - 1.0) > TOL_QUAD and abs(c1_flat - true_c1) > TOL_QUAD}


def negative_pure_gauge_exact() -> dict[str, Any]:
    """Exact / pure-gauge potential A = df for a globally defined smooth f on S^2:
    then F = dA = d(df) = 0 everywhere => c1 = 0. A globally defined A means the
    bundle is trivial (the monopole has NO global A; that is the whole obstruction).
    We take f = cos(theta) (a genuine global function on S^2) and confirm F = 0."""
    t = sp.symbols("theta", real=True)
    f = sp.cos(t)
    # A = df : its dtheta coefficient is df/dtheta; the dphi coefficient is 0
    A_theta = sp.diff(f, t)
    # F = dA. For A = (df/dtheta) dtheta (only), dA = d(df/dtheta) ^ dtheta which
    # in (theta,phi) has dtheta^dphi coefficient = -d/dphi(df/dtheta) = 0.
    F_coeff = sp.simplify(-sp.diff(A_theta, sp.symbols("phi", real=True)))
    c1 = sp.integrate(sp.integrate(F_coeff, (t, 0, sp.pi)),
                      (sp.symbols("phi", real=True), 0, 2 * sp.pi)) / (2 * sp.pi)
    c1 = sp.simplify(c1)
    return {"global_function_f": str(f), "F_coeff_dt_dphi": str(F_coeff),
            "c1_exact": str(c1), "c1_is_zero": bool(sp.simplify(c1) == 0),
            "kills_signature": bool(sp.simplify(c1) == 0)}


# --------------------------------------------------------------------------- #
# Known-value cross-checks                                                     #
# --------------------------------------------------------------------------- #
def known_value_checks(sym, quad, wind, euler, hopf, z3cert, cvc5cert, hopf_so3):
    best_quad = quad["best"]
    best_wind = wind["rows"][-1]   # finest cycle
    best_link = min(hopf["rows"], key=lambda r: r["err_from_1"])

    checks = [
        {"invariant": "c1=(1/2pi)int_S2 F  EXACT symbolic (sympy)",
         "computed": f"{sym['c1_symbolic_in_g']} -> at g=1/2: {sym['c1_at_unit_monopole']}",
         "known": "1", "match": bool(sym["c1_is_one_exact"])},
        {"invariant": "dA == monopole F = g sin(theta) dtheta^dphi EXACT (sympy)",
         "computed": str(sym["dA_equals_monopole_F_exact"]),
         "known": "True", "match": bool(sym["dA_equals_monopole_F_exact"])},
        {"invariant": "c1=(1/2pi)int_S2 F  NUMERIC quadrature (torch float64)",
         "computed": f"{best_quad['c1_numeric']:.10f} (grid {best_quad['grid']}, err {best_quad['err_from_2g']:.2e})",
         "known": "1", "match": best_quad["err_from_2g"] < TOL_QUAD},
        {"invariant": "transition winding (1/2pi)oint(A_N - A_S) EXACT (sympy)",
         "computed": f"{sym['winding_symbolic_in_g']} -> at g=1/2: {sym['winding_at_unit_monopole']}",
         "known": "1", "match": bool(sym["winding_is_one_exact"])},
        {"invariant": "transition winding on equator cycle (rustworkx)",
         "computed": f"{best_wind['winding']:.10f} (single closed cycle: {best_wind['is_single_closed_cycle']}, n={best_wind['n_nodes']})",
         "known": "1", "match": abs(best_wind["winding"] - 1.0) < TOL and best_wind["is_single_closed_cycle"]},
        {"invariant": "c1 == transition winding (Chern-from-overlap) EXACT (sympy)",
         "computed": str(sym["chern_equals_winding_exact"]),
         "known": "True (both = 2g)", "match": bool(sym["chern_equals_winding_exact"])},
        {"invariant": "Dirac integer quantization: c1 in Z, k==1 (z3)",
         "computed": f"found k={z3cert['found_integer_k']}, integrality holds={z3cert['integer_quantization_holds']}",
         "known": "1 (integer)", "match": z3cert["k_equals_one"] and z3cert["integer_quantization_holds"]},
        {"invariant": "Dirac integer quantization: c1 in Z, k==1 (cvc5)",
         "computed": f"found k={cvc5cert['found_integer_k']}, sat={cvc5cert['quantization_sat']}",
         "known": "1 (integer)", "match": cvc5cert["k_equals_one"] and cvc5cert["quantization_sat"]},
        {"invariant": "Hopf bundle linking number (torch Gauss linking) == c1",
         "computed": f"{best_link['linking_number']:.6f} (err {best_link['err_from_1']:.2e})",
         "known": "1 (monopole bundle ~= Hopf bundle)", "match": best_link["err_from_1"] < TOL_LINK},
        {"invariant": "base S^2 Euler characteristic V-E+F (toponetx)",
         "computed": f"{euler['euler_characteristic']} (V={euler['vertices']},E={euler['edges']},F={euler['faces']})",
         "known": "2", "match": bool(euler["is_two_sphere_chi"])},
        {"invariant": "Hopf/SU(2) fiber rotation is SO(3): clifford Cl(3) == SU(2)",
         "computed": f"||R_cl - R_su2|| = {hopf_so3['clifford_vs_su2_norm']:.2e}",
         "known": "0 (even-Cl(3)==SU(2) double cover)", "match": bool(hopf_so3["clifford_matches_su2"])},
        {"invariant": "Hopf/SU(2) fiber rotation certified in SO(3) (e3nn l=1)",
         "computed": f"det={hopf_so3['e3nn_so3']['det']:.6f}, orth={hopf_so3['e3nn_so3']['orthogonality_defect']:.2e}",
         "known": "det=1, orthogonal, reconstructs (genuine SO(3))", "match": bool(hopf_so3["e3nn_so3"]["pass"])},
    ]
    return checks


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    # sympy exact monopole geometry
    sym = sympy_monopole_exact()

    # torch numerical Chern quadrature (wide variation over grids)
    quad = chern_quadrature_sweep()

    # rustworkx equator winding (wide variation over cycle resolutions)
    wind = winding_sweep()

    # toponetx base-sphere Euler characteristic
    euler = base_s2_euler_characteristic()

    # torch Hopf-bundle linking number (several base-point pairs)
    hopf = hopf_linking_sweep()

    # z3 + cvc5 Dirac integer quantization for the UNIT monopole c1
    c1_unit = quad["best"]["c1_numeric"]
    z3cert = z3_quantization_certificate(c1_unit, two_g=2 * GVAL)
    cvc5cert = cvc5_quantization_certificate(c1_unit)

    # clifford + e3nn: Hopf/SU(2) fiber rotation in SO(3)
    hopf_so3 = hopf_so3_evidence()

    # known-value cross-checks
    kvc = known_value_checks(sym, quad, wind, euler, hopf, z3cert, cvc5cert, hopf_so3)

    # negatives
    neg_flat = negative_trivial_flat()
    neg_charge = negative_noninteger_charge()
    neg_redF = negative_reduced_curvature()
    neg_exact = negative_pure_gauge_exact()
    negatives = {
        "trivial_flat_connection": {"detail": neg_flat, "kills_signature": neg_flat["kills_signature"]},
        "noninteger_charge_gauge_inconsistency": {"detail": neg_charge, "kills_signature": neg_charge["kills_signature"]},
        "reduced_flattened_curvature": {"detail": neg_redF, "kills_signature": neg_redF["kills_signature"]},
        "pure_gauge_exact_trivializes": {"detail": neg_exact, "kills_signature": neg_exact["kills_signature"]},
    }

    known_values_all_match = all(c["match"] for c in kvc)
    negatives_all_kill = all(v["kills_signature"] for v in negatives.values())
    tools_all_pass = (
        sym["c1_is_one_exact"] and sym["winding_is_one_exact"] and sym["dA_equals_monopole_F_exact"]
        and quad["all_converge_to_2g"]
        and wind["all_winding_one"] and wind["all_single_cycle"]
        and euler["is_two_sphere_chi"]
        and hopf["all_link_once"]
        and z3cert["integer_quantization_holds"] and z3cert["k_equals_one"]
        and cvc5cert["quantization_sat"] and cvc5cert["k_equals_one"]
        and hopf_so3["clifford_matches_su2"] and hopf_so3["e3nn_so3"]["pass"]
    )
    all_pass = known_values_all_match and negatives_all_kill and tools_all_pass

    blockers: list[str] = []
    if not known_values_all_match:
        blockers += [f"KNOWN-VALUE MISMATCH: {c['invariant']} computed={c['computed']} known={c['known']}"
                     for c in kvc if not c["match"]]
    if not negatives_all_kill:
        blockers += [f"NEGATIVE DID NOT KILL: {k}" for k, v in negatives.items() if not v["kills_signature"]]
    if not z3cert["integer_quantization_holds"]:
        blockers.append("z3 integer quantization certificate did not hold for the unit monopole")
    if not cvc5cert["quantization_sat"]:
        blockers.append("cvc5 integer quantization certificate did not hold for the unit monopole")

    tool_manifest = {
        "torch": {"used": True, "role": "load_bearing",
                  "reason": "float64 numerical surface quadrature of c1 = (1/2pi) int F over S^2 (converges to 1 across grids 64..512); Hopf-map images, Gauss linking integral of two Hopf fibers (== 1), SU(2)->SO(3) double-cover matrices"},
        "sympy": {"used": True, "role": "load_bearing",
                  "reason": "EXACT symbolic dA = g sin(theta) dtheta^dphi, c1 = (1/2pi) int F = 2g, equator transition winding = 2g, and c1 == winding; numeric quadrature alone cannot prove the exact 2g identity or the pure-gauge F=0 negative"},
        "z3": {"used": True, "role": "load_bearing",
               "reason": "SMT integer-quantization certificate: an integer k=1 is within tolerance of c1 (sat) and no integer is missing (negation UNSAT) for the unit monopole; the half-integer-charge negative fails this certificate"},
        "cvc5": {"used": True, "role": "load_bearing",
                 "reason": "independent SMT family (QF_LIRA) certifying the same integer quantization: exists integer k=1 with |c1-k|<=tol; non-integer charge has no such k (unsat)"},
        "rustworkx": {"used": True, "role": "load_bearing",
                      "reason": "the equator is built as a single directed cycle graph; the transition function phase exp(i*2g*phi) accumulated around the closed cycle gives the winding number 1 (verified single closed cycle across resolutions 180..1440)"},
        "toponetx": {"used": True, "role": "load_bearing",
                     "reason": "the base S^2 is a CellComplex (tetrahedral triangulation); Euler characteristic V-E+F == 2 certifies the base topology over which the monopole bundle lives"},
        "clifford": {"used": True, "role": "load_bearing",
                     "reason": "Cl(3) geometric-algebra rotor reproduces the SU(2)/Hopf fiber rotation on the base S^2 (even subalgebra == SU(2) double cover); ||R_cl - R_su2|| ~ 0"},
        "e3nn": {"used": True, "role": "load_bearing",
                 "reason": "certifies the induced 3x3 fiber rotation is a genuine SO(3) element via the l=1 irrep angle round-trip"},
    }

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID, "name": SIM_ID, "version": "1.0.0", "tier": "2_geometry",
        "classification": "diagnostic_only",
        "promotion_allowed": False,
        "promotion_status": "diagnostic_only",
        "sim_execution_kind": "nonclassical",
        "sim_class": "geometry_probe",
        "purpose": "Deep, standalone Dirac magnetic monopole U(1)-bundle geometry lego over S^2 computed in real torch with full tool integration, cross-checked against textbook topological invariants. Lego/pre-sim phase: NOT gated on manifold membership.",
        "scientific_question": "Does the Dirac monopole connection (A_N, A_S) on the two charts of S^2 reproduce the known U(1)-bundle topology -- first Chern number c1 = (1/2pi) int F == 1, equator transition winding == 1, Hopf-bundle isomorphism (linking == 1), base chi(S^2) == 2 -- and do the trivial/flat, non-integer-charge, reduced-curvature, and pure-gauge controls kill that quantized signature?",
        "claim_ceiling": "diagnostic_only / hypothetical / unadmitted: a self-contained known-math geometry lego. Does NOT admit any manifold layer, stacking, coupling, G-structure, Axis0, flux, bridge, QIT, or physics claim.",
        "resource_note": "full native Dirac-monopole U(1) bundle representation: two Wu-Yang chart connections on S2, full equator transition loop, finite curvature quadrature, Hopf-linking witness, base S2 cell-complex topology, and SU(2)->SO(3) fiber rotation checks; no reduced label-only bundle is used",
        "finite_map": "(monopole connection: A_N = g(1-cos theta)dphi, A_S = -g(1+cos theta)dphi on the two charts of S^2) -> (curvature F = g sin(theta) dtheta^dphi, first Chern number c1 = (1/2pi)int F, equator transition winding (1/2pi)oint(A_N-A_S), Hopf linking number, base Euler characteristic)",
        "domain": "the Dirac monopole U(1) connection 1-forms (A_N, A_S) on the north/south charts of S^2, magnetic charge g; the base 2-sphere as a cell complex; Hopf-fiber base points",
        "codomain_or_output": "curvature 2-form F, first Chern number c1 (integer), equatorial transition winding number, Hopf-fiber linking number, base S^2 Euler characteristic, SU(2)->SO(3) fiber-rotation matrices",
        "carrier_layer": "principal U(1) bundle over S^2 with the monopole connection (Wu-Yang two-chart construction); fiber S^1, base S^2",
        "geometry_layer": "Dirac monopole bundle geometry: monopole connection / curvature, first Chern class c1 in H^2(S^2;Z), equatorial transition function, isomorphism class shared with the Hopf bundle",
        "carrier_realization": "torch.float64 numerical quadrature and torch.complex128 Hopf-map/SU(2) algebra; sympy exact differential forms; no NumPy claim-bearing substrate, no label-only tensors, no random claim matrices (Hopf fibers are genuine eigenvector orbits)",
        "spinor_state": "torch.complex128 two-component spinors z in C^2 parametrizing the Hopf fibers (the +1 eigenvector of b.sigma over each base point b on S^2)",
        "quaternion_action": "even subalgebra of Cl(3) (clifford) realizes the unit quaternions == SU(2); the rotor R=exp(-theta/2 B) reproduces the SU(2)/Hopf fiber rotation on the base S^2",
        "peps3d_embedding": "not_applicable_at_lego_phase (no manifold anchor claimed; diagnostic_only)",
        "dependency_receipts": [],
        "downstream_blocks": ["manifold_layers", "stacking", "coupling", "G_structure", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "blocked_consumers": ["manifold_layers", "stacking", "coupling", "G_structure", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "law_or_candidate_tested": "Dirac monopole U(1)-bundle topology over S^2 (first Chern number, transition winding, Hopf isomorphism, Dirac integer quantization) against textbook analytic invariants",
        "branch_status_before_run": "lego/pre-sim phase; standalone known-math geometry; unadmitted",
        "allowed_claims": ["standalone known-math Dirac-monopole U(1)-bundle geometry witness; computed topological invariants (c1=1, winding=1, Hopf linking=1, chi=2) match textbook values"],
        "promotion_blockers": ["diagnostic_only by design (lego/pre-sim phase); no manifold membership, no cross-layer evidence, no coupling"],

        "result_summary": {
            "all_pass": all_pass,
            "known_values_all_match": known_values_all_match,
            "negatives_all_kill": negatives_all_kill,
            "tools_all_pass": tools_all_pass,
            "n_known_value_checks": len(kvc),
            "first_chern_number_c1": c1_unit,
            "transition_winding": wind["rows"][-1]["winding"],
            "hopf_linking_number": min(r["linking_number"] for r in hopf["rows"]),
            "base_euler_characteristic": euler["euler_characteristic"],
            "grid_sizes": GRID_SIZES, "cycle_sizes": CYCLE_SIZES,
            "promotion_allowed": False,
        },

        "known_value_checks": kvc,

        "sympy_exact_monopole": sym,
        "chern_quadrature": quad,
        "transition_winding_cycles": wind,
        "base_euler_characteristic": euler,
        "hopf_linking": hopf,
        "hopf_so3_double_cover": hopf_so3,
        "dirac_quantization_certificates": {"z3": z3cert, "cvc5": cvc5cert},

        "required_negatives": ["trivial_flat_connection", "noninteger_charge_gauge_inconsistency",
                               "reduced_flattened_curvature", "pure_gauge_exact_trivializes"],
        "negatives_run": list(negatives.keys()),
        "negatives": negatives,
        "kill_conditions": [
            "any known-value invariant fails to match its textbook value",
            "trivial flat connection retains nonzero c1 or winding",
            "non-integer charge passes the integer-quantization certificate",
            "reduced/flattened curvature still integrates to the quantized c1",
            "pure-gauge exact potential retains nonzero c1",
        ],

        "TOOL_MANIFEST": tool_manifest,
        "tool_manifest": tool_manifest,
        "TOOL_INTEGRATION_DEPTH": {"torch": "load_bearing", "sympy": "load_bearing", "z3": "load_bearing",
                                   "cvc5": "load_bearing", "rustworkx": "load_bearing", "toponetx": "load_bearing",
                                   "clifford": "load_bearing", "e3nn": "load_bearing"},
        "proof_surfaces_used": ["z3", "cvc5", "sympy"],
        "graph_surfaces_used": ["rustworkx"],
        "topology_surfaces_used": ["toponetx"],
        "required_tools": ["torch", "sympy", "z3", "cvc5", "rustworkx", "toponetx", "clifford", "e3nn"],
        "actual_tools_used": ["torch", "sympy", "z3", "cvc5", "rustworkx", "toponetx", "clifford", "e3nn"],

        "required_artifacts": ["json_result_receipt", "witness_trace"],
        "artifacts_emitted": ["json_result_receipt", "witness_trace"],
        "witness_trace_id": f"{SIM_ID}_witness",

        "all_pass": all_pass,
        "blockers": blockers,
        "pass_rule": "every known_value_check matches its known value AND all four negatives kill the signature AND the symbolic/numeric Chern number, equator winding, Hopf linking, base Euler characteristic, and z3+cvc5 integer-quantization certificates all agree on the unit monopole c1 = 1",
        "fail_rule": "any known-value mismatch, any negative that does not kill, any non-integer c1 passing quantization, or any tool surface failing",
        "eligible_consumers": ["other diagnostic_only gauge-bundle / characteristic-class geometry probes"],
    }

    witness = {
        "sim_id": SIM_ID,
        "steps": [
            {"step": "sympy_exact_monopole_forms", "c1_in_g": sym["c1_symbolic_in_g"],
             "winding_in_g": sym["winding_symbolic_in_g"], "dA_eq_F": sym["dA_equals_monopole_F_exact"]},
            {"step": "torch_numerical_chern_quadrature", "grids": GRID_SIZES,
             "all_converge_to_2g": quad["all_converge_to_2g"], "best": quad["best"]},
            {"step": "rustworkx_equator_winding_cycle", "cycle_sizes": CYCLE_SIZES,
             "all_winding_one": wind["all_winding_one"], "all_single_cycle": wind["all_single_cycle"]},
            {"step": "toponetx_base_s2_euler", "euler": euler["euler_characteristic"]},
            {"step": "torch_hopf_linking", "all_link_once": hopf["all_link_once"]},
            {"step": "z3_cvc5_dirac_integer_quantization", "z3_holds": z3cert["integer_quantization_holds"],
             "cvc5_sat": cvc5cert["quantization_sat"], "k": z3cert["found_integer_k"]},
            {"step": "clifford_e3nn_su2_so3_double_cover", "clifford_matches": hopf_so3["clifford_matches_su2"],
             "e3nn_pass": hopf_so3["e3nn_so3"]["pass"]},
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
        "first_chern_number_c1": c1_unit,
        "blockers": blockers,
        "known_value_checks": [{"invariant": c["invariant"], "computed": c["computed"],
                                "known": c["known"], "match": c["match"]} for c in kvc],
    }, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

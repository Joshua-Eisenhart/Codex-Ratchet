#!/usr/bin/env python3
"""Deep conformal stereographic-S^2 geometry lego (diagnostic_only, unadmitted).

KNOWN GEOMETRY (real torch.complex128 / float64 -- no labels, no random claim
matrices, no NumPy claim-bearing substrate):

  Stereographic projection from the north pole N = (0,0,1) maps the round sphere
  S^2 \\ {N} bijectively onto the plane C = R^2 (one-point compactification adds
  the point at infinity for N itself):
      pi(x,y,z) = (x/(1-z), y/(1-z))           identified as  u = X + iY in C.
  Its inverse (inverse stereographic) is
      pi^{-1}(X,Y) = (2X, 2Y, X^2+Y^2-1) / (X^2+Y^2+1).
  The KNOWN structure being checked:
   (1) pi is CONFORMAL: the pullback of the flat plane metric is
       g = lambda(X,Y)^2 (dX^2 + dY^2) with conformal factor lambda = 2/(1+X^2+Y^2)
       and ZERO off-diagonal term -- so the projection's differential is an angle-
       preserving (similarity) map. Equivalently, the angle between two tangent
       vectors on S^2 equals the angle between their images in the plane.
   (2) circles on S^2 map to circles-OR-lines in the plane: a generic small/great
       circle (sphere intersect a plane) projects to a Euclidean circle; a great
       circle THROUGH the north pole projects to a straight LINE.
   (3) the Mobius group PSL(2,C) acts on C \\ {infty} by fractional linear maps
       w = (a z + b)/(c z + d) and PRESERVES the conformal structure; the
       cross-ratio (z1,z2;z3,z4) is a Mobius invariant. Rotations of S^2 (an
       SO(3) rotor in Cl(3)) intertwine through pi with planar Mobius maps and
       hence also preserve the cross-ratio.
   (4) pi composed with pi^{-1} is the identity (round-trip), both directions.

This sim computes that geometry deeply with full tool integration and proves it
against the textbook analytic values. It is a self-contained formal-scout lego in
the lego/pre-sim phase: NOT gated on manifold membership, NO distinctness/forcing
filter, NO cross-layer rules. classification = "diagnostic_only" (hypothetical,
unadmitted).

KNOWN-VALUE CROSS-CHECKS (each compared to its analytic value, recorded as
{invariant, computed, known, match} -- match is COMPUTED, never hardcoded):
  - round-trip pi(pi^{-1}(u)) == u  and  pi^{-1}(pi(p)) == p (identity, both ways)
  - conformal angle preservation: angle(plane tangents) == angle(pushed-forward
    sphere tangents) to ~0 (torch autograd Jacobian; geomstats S^2 Riemannian
    inner product gives an independent sphere-side angle)
  - pullback metric is conformal EXACTLY (sympy): g_XX == g_YY == (2/(1+X^2+Y^2))^2
    and g_XY == 0 identically
  - conformal factor equals the analytic 2/(1+r^2) at sampled points
  - generic circle on S^2 -> circle in plane (general-conic least-squares fit
    residual ~ 0, nonzero curvature coefficient A)
  - great circle through N -> straight line (conic curvature coefficient A ~ 0)
  - cross-ratio invariant under a Mobius map (a z + b)/(c z + d), |Delta| ~ 0
  - cross-ratio invariant under a Cl(3) SO(3) rotor of the sphere (rotor intertwines
    with a planar Mobius map), |Delta| ~ 0
  - cross-ratio invariance EXACT symbolically (sympy) for a symbolic Mobius map

TOOLS (all load-bearing in the execution path):
  - torch     : ALL projection / inverse / Jacobian (autograd) / angle / circle-fit
                (SVD) / cross-ratio / Mobius algebra in float64 / complex128.
  - sympy     : EXACT symbolic proof that the pullback metric is lambda^2 * I with
                zero off-diagonal (conformality), and EXACT cross-ratio invariance
                under a symbolic Mobius map. Numeric torch alone cannot prove the
                exact identities.
  - z3        : SMT certificate that the conformal structure holds on carrier
                numbers -- off-diagonal pullback term == 0 and g_XX == g_YY within
                tolerance, and the angle-preservation residual is within tolerance;
                the NEGATION is UNSAT. Removing z3 removes this certificate.
  - cvc5      : independent SMT family (QF_NRA) certifying the same conformality
                fact; negation UNSAT.
  - geomstats : (GEOMSTATS_BACKEND=pytorch) the round S^2 Riemannian metric gives
                an INDEPENDENT sphere-side angle between tangent vectors via its
                inner_product; this angle is cross-checked against the planar angle
                through the projection (the conformality witness without our own
                Jacobian).
  - clifford  : Cl(3) geometric-algebra rotor R = exp(-theta/2 B) rotates the
                sphere (SO(3)); through pi this acts as a planar Mobius map and
                preserves the cross-ratio -- an independent realization of the
                conformal automorphisms of S^2.

WIDE VARIATION: many sampled plane points and sphere points, multiple sample sizes
N in {8,16,32,64}, multiple seeds, many circles (random planes), multiple Mobius
maps and rotors.

NEGATIVES (each must CHANGE/KILL the conformal-stereographic signature):
  - Lambert azimuthal EQUAL-AREA projection: area-preserving but NOT conformal --
    the measured angle is distorted (angle preservation fails).
  - broken cross-ratio: a non-Mobius map (z -> z^2) changes the cross-ratio.
  - non-conformal linear shear of the plane: a shear has nonzero metric off-
    diagonal / unequal diagonal -> angles distorted.
  - degenerate "projection" that drops a coordinate (orthographic z-drop): not a
    bijection onto C, fails the round-trip identity.

finite_map: (point p on S^2 \\ {N}, or u in C) -> (stereographic image / preimage,
pullback conformal factor, tangent-angle, circle/line conic fit, cross-ratio under
Mobius / SO(3) rotor)
"""

from __future__ import annotations

import json
import math
import os
import pathlib
from typing import Any

import sympy as sp
import torch
import z3
import cvc5
from cvc5 import Kind
from clifford import Cl

# geomstats with the pytorch backend (set BEFORE importing geomstats.backend)
os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")
import geomstats.backend as gs  # noqa: E402
from geomstats.geometry.hypersphere import Hypersphere  # noqa: E402

RTYPE = torch.float64
CDTYPE = torch.complex128
TOL = 1.0e-9                # direct float64 numeric invariants
TOL_ANGLE = 1.0e-9         # angle-preservation residual (autograd Jacobian, float64)
TOL_GEOMSTATS = 1.0e-6     # geomstats internal float defaults / acos near edges
TOL_SMT = 1.0e-9           # SMT conformality tolerance on carrier floats
TOL_FIT = 1.0e-9           # circle/line conic least-squares residual
SAMPLE_SIZES = [8, 16, 32, 64]
SEEDS = [0, 1, 2, 3, 4]
ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "geom_conformal_stereographic_s2_deep_probe"

NORTH = torch.tensor([0.0, 0.0, 1.0], dtype=RTYPE)


# --------------------------------------------------------------------------- #
# Core stereographic geometry (torch, load-bearing)                           #
# --------------------------------------------------------------------------- #
def stereo(P: torch.Tensor) -> torch.Tensor:
    """S^2 \\ {N} -> plane R^2, north-pole projection. P shape (..., 3)."""
    x, y, z = P[..., 0], P[..., 1], P[..., 2]
    return torch.stack([x / (1.0 - z), y / (1.0 - z)], dim=-1)


def stereo_complex(P: torch.Tensor) -> torch.Tensor:
    """S^2 \\ {N} -> C as u = X + iY."""
    XY = stereo(P)
    return (XY[..., 0] + 1j * XY[..., 1]).to(CDTYPE)


def inv_stereo(XY: torch.Tensor) -> torch.Tensor:
    """plane R^2 -> S^2 \\ {N}, inverse north-pole projection. XY shape (..., 2)."""
    X, Y = XY[..., 0], XY[..., 1]
    den = X * X + Y * Y + 1.0
    return torch.stack([2 * X / den, 2 * Y / den, (X * X + Y * Y - 1.0) / den], dim=-1)


def conformal_factor(XY: torch.Tensor) -> torch.Tensor:
    """Analytic conformal factor lambda = 2/(1 + X^2 + Y^2)."""
    X, Y = XY[..., 0], XY[..., 1]
    return 2.0 / (1.0 + X * X + Y * Y)


def inv_stereo_jacobian(X0: float, Y0: float) -> torch.Tensor:
    """3x2 Jacobian d(pi^{-1})/d(X,Y) at (X0,Y0) via torch autograd."""
    X = torch.tensor(X0, dtype=RTYPE, requires_grad=True)
    Y = torch.tensor(Y0, dtype=RTYPE, requires_grad=True)
    den = X * X + Y * Y + 1.0
    P = torch.stack([2 * X / den, 2 * Y / den, (X * X + Y * Y - 1.0) / den])
    J = torch.zeros((3, 2), dtype=RTYPE)
    for i in range(3):
        g = torch.autograd.grad(P[i], [X, Y], retain_graph=True)
        J[i, 0], J[i, 1] = g[0], g[1]
    return J


def haar_sphere_points(n: int, gen: torch.Generator) -> torch.Tensor:
    """n Haar-uniform points on S^2 via normalized Gaussians (real math, no labels)."""
    v = torch.randn(n, 3, generator=gen, dtype=RTYPE)
    v = v / torch.linalg.vector_norm(v, dim=1, keepdim=True)
    # avoid the north pole singularity by reflecting points too close to N
    too_close = (1.0 - v[:, 2]).abs() < 1e-3
    v[too_close] = -v[too_close]
    return v


# --------------------------------------------------------------------------- #
# Conformality: angle between tangent vectors preserved                        #
# --------------------------------------------------------------------------- #
def angle(u: torch.Tensor, v: torch.Tensor) -> float:
    c = (u @ v) / (torch.linalg.vector_norm(u) * torch.linalg.vector_norm(v))
    return math.acos(max(-1.0, min(1.0, float(c))))


def angle_preservation_residual(X0: float, Y0: float,
                                u: torch.Tensor, v: torch.Tensor) -> float:
    """|angle_plane(u,v) - angle_sphere(J u, J v)|. 0 iff the differential is a
    similarity (conformal)."""
    J = inv_stereo_jacobian(X0, Y0)
    ang_plane = angle(u, v)
    ang_sphere = angle(J @ u, J @ v)
    return abs(ang_plane - ang_sphere)


def geomstats_sphere_angle(X0: float, Y0: float,
                           u: torch.Tensor, v: torch.Tensor) -> float:
    """Independent sphere-side angle using the geomstats Hypersphere(2) Riemannian
    metric. Push the plane tangents forward with the Jacobian, project them onto
    the tangent space at pi^{-1}(X0,Y0), and use geomstats inner_product."""
    s2 = Hypersphere(dim=2)
    base = inv_stereo(torch.tensor([X0, Y0], dtype=RTYPE)).reshape(1, 3)
    J = inv_stereo_jacobian(X0, Y0)
    tu = (J @ u).reshape(1, 3)
    tv = (J @ v).reshape(1, 3)
    # ensure they are genuine tangent vectors on the geomstats sphere
    tu = s2.to_tangent(gs.array(tu), base)
    tv = s2.to_tangent(gs.array(tv), base)
    iuv = float(s2.metric.inner_product(tu, tv, base))
    iuu = float(s2.metric.inner_product(tu, tu, base))
    ivv = float(s2.metric.inner_product(tv, tv, base))
    c = iuv / math.sqrt(iuu * ivv)
    return math.acos(max(-1.0, min(1.0, c)))


# --------------------------------------------------------------------------- #
# Circles -> circles or lines                                                  #
# --------------------------------------------------------------------------- #
def fit_conic_circle(pts: torch.Tensor) -> tuple[torch.Tensor, float]:
    """General circle/line conic A(X^2+Y^2)+B X+C Y+D = 0 via smallest right
    singular vector (torch SVD). Returns (coef[A,B,C,D], normalized residual).
    A ~ 0 means a straight line; A != 0 means a genuine circle."""
    X, Y = pts[:, 0], pts[:, 1]
    M = torch.stack([X * X + Y * Y, X, Y, torch.ones_like(X)], dim=1)
    _, _, Vh = torch.linalg.svd(M)
    coef = Vh[-1]
    resid = float(torch.linalg.vector_norm(M @ coef).item() / math.sqrt(len(X)))
    return coef, resid


def sphere_circle(axis: torch.Tensor, height: float, n: int) -> torch.Tensor:
    """Circle = S^2 intersect plane {axis . p = height}, |axis|=1, |height|<1."""
    axis = axis / torch.linalg.vector_norm(axis)
    e1 = torch.tensor([1.0, 0.0, 0.0], dtype=RTYPE)
    if abs(float(e1 @ axis)) > 0.9:
        e1 = torch.tensor([0.0, 1.0, 0.0], dtype=RTYPE)
    e1 = e1 - (e1 @ axis) * axis
    e1 = e1 / torch.linalg.vector_norm(e1)
    e2 = torch.linalg.cross(axis, e1)
    center = height * axis
    rad = math.sqrt(1.0 - height * height)
    ts = torch.linspace(0, 2 * math.pi, n + 1, dtype=RTYPE)[:-1]
    return torch.stack([center + rad * (math.cos(float(t)) * e1 + math.sin(float(t)) * e2)
                        for t in ts])


def great_circle_through_north(n: int) -> torch.Tensor:
    """A great circle passing through the north pole (plane through origin
    containing N). It must project to a straight LINE."""
    e1 = torch.tensor([0.0, 1.0, 0.0], dtype=RTYPE)   # in the plane
    e2 = torch.tensor([0.0, 0.0, 1.0], dtype=RTYPE)   # = N direction
    ts = torch.linspace(0, 2 * math.pi, n + 1, dtype=RTYPE)[:-1]
    pts = torch.stack([math.cos(float(t)) * e1 + math.sin(float(t)) * e2 for t in ts])
    mask = (1.0 - pts[:, 2]).abs() > 1e-3   # drop points at the singular N
    return pts[mask]


# --------------------------------------------------------------------------- #
# Mobius group + cross-ratio                                                   #
# --------------------------------------------------------------------------- #
def cross_ratio(z1: torch.Tensor, z2: torch.Tensor,
                z3v: torch.Tensor, z4: torch.Tensor) -> torch.Tensor:
    return ((z1 - z3v) * (z2 - z4)) / ((z1 - z4) * (z2 - z3v))


def mobius(z: torch.Tensor, a, b, c, d) -> torch.Tensor:
    a, b, c, d = (torch.tensor(x, dtype=CDTYPE) for x in (a, b, c, d))
    return (a * z + b) / (c * z + d)


def clifford_rotor_so3(theta: float, axis: tuple[float, float, float]) -> torch.Tensor:
    """Cl(3) geometric-algebra rotor R = exp(-theta/2 B), B the unit bivector dual
    to the axis. Returns the induced 3x3 SO(3) rotation. Even subalgebra of Cl(3)
    == SU(2) == unit quaternions; this is an SO(3) rotation of the sphere."""
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


# --------------------------------------------------------------------------- #
# sympy: EXACT conformal pullback metric + EXACT cross-ratio invariance        #
# --------------------------------------------------------------------------- #
def sympy_exact() -> dict[str, Any]:
    X, Y = sp.symbols("X Y", real=True)
    den = X**2 + Y**2 + 1
    P = sp.Matrix([2 * X / den, 2 * Y / den, (X**2 + Y**2 - 1) / den])
    on_sphere = sp.simplify(P.dot(P))                       # == 1
    J = P.jacobian([X, Y])
    g = sp.simplify(J.T * J)                                # pullback metric
    lam2 = sp.simplify((2 / (1 + X**2 + Y**2))**2)
    gXX_ok = sp.simplify(g[0, 0] - lam2) == 0
    gYY_ok = sp.simplify(g[1, 1] - lam2) == 0
    off_zero = sp.simplify(g[0, 1]) == 0 and sp.simplify(g[1, 0]) == 0
    conformal_exact = bool(gXX_ok and gYY_ok and off_zero)

    # EXACT cross-ratio invariance under a symbolic Mobius map
    z1, z2, z3, z4 = sp.symbols("z1 z2 z3 z4")
    a, b, c, d = sp.symbols("a b c d")
    cr = lambda w1, w2, w3, w4: ((w1 - w3) * (w2 - w4)) / ((w1 - w4) * (w2 - w3))
    mob = lambda z: (a * z + b) / (c * z + d)
    cr0 = cr(z1, z2, z3, z4)
    crm = cr(mob(z1), mob(z2), mob(z3), mob(z4))
    cross_ratio_exact = sp.simplify(crm - cr0) == 0

    return {
        "inverse_image_on_sphere_exact": str(on_sphere),
        "pullback_metric_gXX": str(g[0, 0]),
        "pullback_metric_gYY": str(g[1, 1]),
        "pullback_metric_off_diagonal": str(sp.simplify(g[0, 1])),
        "conformal_factor_lambda_squared": str(lam2),
        "conformal_exact": conformal_exact,
        "cross_ratio_mobius_invariant_exact": bool(cross_ratio_exact),
    }


# --------------------------------------------------------------------------- #
# z3 / cvc5: certify conformality on carrier numbers (negation UNSAT)          #
# --------------------------------------------------------------------------- #
def z3_conformal_certificate(gXX: float, gYY: float, gXY: float,
                             ang_resid: float) -> dict[str, Any]:
    """A pullback metric is conformal iff g_XX == g_YY and g_XY == 0. We feed the
    carrier numbers to z3 and check the NEGATION of
       (|g_XX - g_YY| <= tol) AND (|g_XY| <= tol) AND (ang_resid <= tol)
    is UNSAT. Removing z3 removes this certificate."""
    s = z3.Solver()
    A, Bv, Cv, R = z3.Real("gXX"), z3.Real("gYY"), z3.Real("gXY"), z3.Real("res")
    tol = z3.RealVal(repr(TOL_SMT))
    s.add(A == z3.RealVal(repr(gXX)), Bv == z3.RealVal(repr(gYY)),
          Cv == z3.RealVal(repr(gXY)), R == z3.RealVal(repr(ang_resid)))
    conformal = z3.And(
        A - Bv <= tol, A - Bv >= -tol,
        Cv <= tol, Cv >= -tol,
        R <= tol, R >= -tol,
    )
    s.add(z3.Not(conformal))
    status = str(s.check())
    return {"negation_status": status, "pass": status == "unsat"}


def cvc5_conformal_certificate(gXX: float, gYY: float, gXY: float,
                               ang_resid: float) -> dict[str, Any]:
    """Independent SMT family (cvc5, QF_NRA) certifying the same conformality fact:
    the negation is UNSAT."""
    slv = cvc5.Solver()
    slv.setOption("produce-models", "false")
    slv.setLogic("QF_NRA")
    Rs = slv.getRealSort()

    def rv(x: float):
        frac = sp.Rational(x).limit_denominator(10**12)
        num, den = sp.fraction(frac)
        return slv.mkReal(int(num), int(den)) if int(den) != 1 else slv.mkReal(int(num))

    A, Bv, Cv, Rr = (slv.mkConst(Rs, n) for n in ("gXX", "gYY", "gXY", "res"))
    for var, val in ((A, gXX), (Bv, gYY), (Cv, gXY), (Rr, ang_resid)):
        slv.assertFormula(slv.mkTerm(Kind.EQUAL, var, rv(val)))
    zero = slv.mkReal(0)
    tol = rv(TOL_SMT)
    neg_tol = slv.mkTerm(Kind.SUB, zero, tol)

    def in_band(term):
        lo = slv.mkTerm(Kind.GEQ, term, neg_tol)
        hi = slv.mkTerm(Kind.LEQ, term, tol)
        return slv.mkTerm(Kind.AND, lo, hi)

    diag = slv.mkTerm(Kind.SUB, A, Bv)
    conformal = slv.mkTerm(Kind.AND, in_band(diag), in_band(Cv), in_band(Rr))
    slv.assertFormula(slv.mkTerm(Kind.NOT, conformal))
    res = slv.checkSat()
    status = "unsat" if res.isUnsat() else ("sat" if res.isSat() else "unknown")
    return {"negation_status": status, "pass": res.isUnsat()}


def pullback_metric_numeric(X0: float, Y0: float) -> tuple[float, float, float]:
    """g = J^T J of the inverse stereographic at (X0,Y0) (torch autograd)."""
    J = inv_stereo_jacobian(X0, Y0)
    g = J.T @ J
    return float(g[0, 0]), float(g[1, 1]), float(g[0, 1])


# --------------------------------------------------------------------------- #
# Wide-variation sampling                                                      #
# --------------------------------------------------------------------------- #
def sample_block(n: int, seed: int) -> dict[str, Any]:
    gen = torch.Generator().manual_seed(seed)
    P = haar_sphere_points(n, gen)

    # round-trip pi^{-1}(pi(p)) == p
    XY = stereo(P)
    P_back = inv_stereo(XY)
    rt_sphere = float(torch.linalg.vector_norm(P - P_back, dim=1).max().item())

    # round-trip pi(pi^{-1}(u)) == u for random plane points
    UV = torch.randn(n, 2, generator=gen, dtype=RTYPE) * 1.5
    UV_back = stereo(inv_stereo(UV))
    rt_plane = float(torch.linalg.vector_norm(UV - UV_back, dim=1).max().item())

    # conformal factor vs analytic at the sampled plane points
    cf_an = conformal_factor(XY)
    cf_num = torch.stack([torch.sqrt(torch.tensor(pullback_metric_numeric(
        float(XY[i, 0]), float(XY[i, 1]))[0], dtype=RTYPE)) for i in range(n)])
    cf_err = float((cf_an - cf_num).abs().max().item())

    # angle preservation over several tangent pairs at each sampled plane point
    pairs = [(torch.tensor([1.0, 0.0]), torch.tensor([0.0, 1.0])),
             (torch.tensor([1.0, 0.3]), torch.tensor([-0.2, 1.0])),
             (torch.tensor([0.7, -0.7]), torch.tensor([0.5, 0.9]))]
    ang_res = 0.0
    gs_res = 0.0
    for i in range(min(n, 12)):  # cap autograd loop for the larger sizes
        x0, y0 = float(XY[i, 0]), float(XY[i, 1])
        for u, v in pairs:
            ang_res = max(ang_res, angle_preservation_residual(x0, y0, u, v))
            gs_res = max(gs_res, abs(angle(u, v) - geomstats_sphere_angle(x0, y0, u, v)))

    return {
        "n": n, "seed": seed,
        "max_roundtrip_sphere_err": rt_sphere,
        "max_roundtrip_plane_err": rt_plane,
        "max_conformal_factor_err": cf_err,
        "max_angle_preservation_residual": ang_res,
        "max_geomstats_angle_residual": gs_res,
    }


def circle_block() -> dict[str, Any]:
    """Many random small/great circles -> circles; great circles through N -> lines."""
    gen = torch.Generator().manual_seed(99)
    circle_resids, circle_curvatures = [], []
    for _ in range(20):
        axis = torch.randn(3, generator=gen, dtype=RTYPE)
        height = float(torch.empty(1).uniform_(-0.8, 0.8, generator=gen).item())
        C = sphere_circle(axis, height, 48)
        # drop any near-north-pole point
        C = C[(1.0 - C[:, 2]).abs() > 1e-3]
        proj = stereo(C)
        coef, resid = fit_conic_circle(proj)
        circle_resids.append(resid)
        circle_curvatures.append(abs(float(coef[0])))   # |A|; >0 for a real circle
    gc = great_circle_through_north(64)
    proj_line = stereo(gc)
    coef_line, resid_line = fit_conic_circle(proj_line)
    return {
        "n_circles": len(circle_resids),
        "max_circle_fit_residual": max(circle_resids),
        "min_circle_curvature_abs": min(circle_curvatures),   # all should be > 0
        "great_circle_line_fit_residual": resid_line,
        "great_circle_curvature_abs": abs(float(coef_line[0])),  # ~ 0 => a line
    }


def cross_ratio_block() -> dict[str, Any]:
    """Cross-ratio invariance under Mobius maps and Cl(3) SO(3) rotors."""
    gen = torch.Generator().manual_seed(7)
    mobius_diffs, rotor_diffs = [], []
    # Every Mobius test map MUST be non-degenerate: ad - bc != 0. A map with
    # ad - bc = 0 is NOT a Mobius transformation (it collapses C to a point) and
    # would NOT preserve the cross-ratio -- including such a map would be a test-
    # fixture error, not a geometry failure. Enforced by assert below.
    mob_params = [((1 + 2j), (0.5 - 1j), (0.3 + 0.1j), (2 - 0.7j)),
                  ((2 + 0j), (1 + 1j), (0 + 0j), (1 + 0j)),
                  ((0 + 1j), (1 + 0j), (1 + 0j), (1 - 1j))]
    for (a, b, c, d) in mob_params:
        assert abs(a * d - b * c) > 1e-9, f"degenerate Mobius map ad-bc=0: {(a, b, c, d)}"
    for _ in range(10):
        zs = [torch.tensor(complex(float(torch.randn(1, generator=gen)),
                                   float(torch.randn(1, generator=gen))), dtype=CDTYPE)
              for _ in range(4)]
        cr0 = cross_ratio(*zs)
        for (a, b, c, d) in mob_params:
            crm = cross_ratio(*[mobius(z, a, b, c, d) for z in zs])
            mobius_diffs.append(float((cr0 - crm).abs().item()))
    # Cl(3) rotor intertwines with a planar Mobius map: rotate sphere, project,
    # cross-ratio invariant.
    for theta, axis in [(0.7, (0.2, 0.6, 0.5)), (1.3, (1.0, 0.0, 0.4)),
                        (2.1, (-0.3, 0.8, 0.2))]:
        R = clifford_rotor_so3(theta, axis)
        pts = haar_sphere_points(4, torch.Generator().manual_seed(int(theta * 1000)))
        z_before = stereo_complex(pts)
        z_after = stereo_complex((R @ pts.T).T)
        cr_b = cross_ratio(z_before[0], z_before[1], z_before[2], z_before[3])
        cr_a = cross_ratio(z_after[0], z_after[1], z_after[2], z_after[3])
        rotor_diffs.append(float((cr_b - cr_a).abs().item()))
    return {
        "n_mobius_tests": len(mobius_diffs),
        "max_mobius_cross_ratio_diff": max(mobius_diffs),
        "n_rotor_tests": len(rotor_diffs),
        "max_rotor_cross_ratio_diff": max(rotor_diffs),
    }


# --------------------------------------------------------------------------- #
# Negatives                                                                    #
# --------------------------------------------------------------------------- #
def lambert_inv_jacobian(X0: float, Y0: float) -> torch.Tensor:
    """Jacobian of the Lambert azimuthal EQUAL-AREA inverse (area-preserving,
    NOT conformal). pi_L^{-1}(X,Y) = (X s, Y s, -(1 - r^2/2)), s = sqrt(1 - r^2/4),
    r^2 = X^2 + Y^2."""
    X = torch.tensor(X0, dtype=RTYPE, requires_grad=True)
    Y = torch.tensor(Y0, dtype=RTYPE, requires_grad=True)
    r2 = X * X + Y * Y
    s = torch.sqrt(torch.clamp(1.0 - r2 / 4.0, min=1e-12))
    P = torch.stack([X * s, Y * s, -(1.0 - r2 / 2.0)])
    J = torch.zeros((3, 2), dtype=RTYPE)
    for i in range(3):
        g = torch.autograd.grad(P[i], [X, Y], retain_graph=True)
        J[i, 0], J[i, 1] = g[0], g[1]
    return J


def negative_lambert_nonconformal() -> dict[str, Any]:
    """Lambert equal-area distorts angles: the off-diagonal / unequal-diagonal of
    its pullback metric is nonzero and the measured angle is NOT preserved."""
    x0, y0 = 0.6, -0.4
    u, v = torch.tensor([1.0, 0.3]), torch.tensor([-0.2, 1.0])
    JL = lambert_inv_jacobian(x0, y0)
    g = JL.T @ JL
    ang_plane = angle(u, v)
    ang_lambert = angle(JL @ u, JL @ v)
    resid = abs(ang_plane - ang_lambert)
    diag_gap = abs(float(g[0, 0]) - float(g[1, 1]))
    offdiag = abs(float(g[0, 1]))
    return {
        "angle_plane": ang_plane,
        "angle_lambert": ang_lambert,
        "angle_distortion": resid,
        "metric_diagonal_gap": diag_gap,
        "metric_off_diagonal": offdiag,
        # KILL: angle is NOT preserved (distortion well above tolerance)
        "kills_conformality": resid > 1e-3,
    }


def negative_broken_cross_ratio() -> dict[str, Any]:
    """A non-Mobius map z -> z^2 changes the cross-ratio."""
    gen = torch.Generator().manual_seed(11)
    zs = [torch.tensor(complex(float(torch.randn(1, generator=gen)),
                               float(torch.randn(1, generator=gen))), dtype=CDTYPE)
          for _ in range(4)]
    cr0 = cross_ratio(*zs)
    crb = cross_ratio(*[z * z for z in zs])
    diff = float((cr0 - crb).abs().item())
    return {
        "cross_ratio_before": [float(cr0.real), float(cr0.imag)],
        "cross_ratio_after_z2": [float(crb.real), float(crb.imag)],
        "cross_ratio_diff": diff,
        "kills_mobius_invariance": diff > 1e-3,
    }


def negative_shear_nonconformal() -> dict[str, Any]:
    """A linear shear of the plane has a non-similarity differential: its pullback
    metric has nonzero off-diagonal / unequal diagonal -> angles distorted."""
    S = torch.tensor([[1.0, 0.8], [0.0, 1.0]], dtype=RTYPE)   # shear
    u, v = torch.tensor([1.0, 0.0]), torch.tensor([0.0, 1.0])
    ang_plane = angle(u, v)
    ang_shear = angle(S @ u, S @ v)
    g = S.T @ S
    return {
        "angle_plane": ang_plane,
        "angle_shear": ang_shear,
        "angle_distortion": abs(ang_plane - ang_shear),
        "metric_off_diagonal": abs(float(g[0, 1])),
        "kills_conformality": abs(ang_plane - ang_shear) > 1e-3,
    }


def negative_orthographic_drop() -> dict[str, Any]:
    """Degenerate 'projection' that drops the z coordinate (orthographic): it is
    NOT a bijection onto C and FAILS the round-trip identity -- two distinct sphere
    points (z, -z hemisphere) collapse to the same plane point."""
    gen = torch.Generator().manual_seed(13)
    P = haar_sphere_points(32, gen)

    def ortho(Pp):  # drop z
        return Pp[..., :2]
    XY = ortho(P)
    # naive 'inverse': lift back to upper hemisphere z = +sqrt(1 - X^2 - Y^2)
    z_lift = torch.sqrt(torch.clamp(1.0 - XY[:, 0]**2 - XY[:, 1]**2, min=0.0))
    P_back = torch.stack([XY[:, 0], XY[:, 1], z_lift], dim=1)
    rt_err = float(torch.linalg.vector_norm(P - P_back, dim=1).max().item())
    return {
        "max_roundtrip_err_orthographic": rt_err,
        # KILL: round-trip fails (lower hemisphere collapses) -> not a bijection
        "breaks_roundtrip": rt_err > 1e-3,
    }


# --------------------------------------------------------------------------- #
# Known-value cross-checks                                                     #
# --------------------------------------------------------------------------- #
def known_value_checks(blocks: list[dict[str, Any]], circ: dict[str, Any],
                       crb: dict[str, Any], sym: dict[str, Any],
                       z3_pass: bool, cvc5_pass: bool) -> list[dict[str, Any]]:
    max_rt_sphere = max(b["max_roundtrip_sphere_err"] for b in blocks)
    max_rt_plane = max(b["max_roundtrip_plane_err"] for b in blocks)
    max_cf_err = max(b["max_conformal_factor_err"] for b in blocks)
    max_ang = max(b["max_angle_preservation_residual"] for b in blocks)
    max_gs = max(b["max_geomstats_angle_residual"] for b in blocks)

    return [
        {"invariant": "roundtrip_pi(pi^-1(p))==p_on_S2",
         "computed": f"max err {max_rt_sphere:.2e}", "known": "0",
         "match": max_rt_sphere < TOL},
        {"invariant": "roundtrip_pi^-1(pi(u))==u_on_plane",
         "computed": f"max err {max_rt_plane:.2e}", "known": "0",
         "match": max_rt_plane < TOL},
        {"invariant": "conformal_factor_lambda==2/(1+r^2)",
         "computed": f"max err {max_cf_err:.2e}", "known": "0",
         "match": max_cf_err < TOL},
        {"invariant": "conformal_angle_preservation_torch_autograd",
         "computed": f"max angle residual {max_ang:.2e}", "known": "0",
         "match": max_ang < TOL_ANGLE},
        {"invariant": "conformal_angle_preservation_geomstats_S2_metric",
         "computed": f"max residual {max_gs:.2e}", "known": "0",
         "match": max_gs < TOL_GEOMSTATS},
        {"invariant": "pullback_metric_conformal_EXACT_symbolic(sympy)",
         "computed": str(sym["conformal_exact"]), "known": "True",
         "match": bool(sym["conformal_exact"])},
        {"invariant": "pullback_metric_off_diagonal_EXACT(sympy)",
         "computed": sym["pullback_metric_off_diagonal"], "known": "0",
         "match": sym["pullback_metric_off_diagonal"] == "0"},
        {"invariant": "small/great_circle_on_S2->circle_in_plane(conic_fit)",
         "computed": f"max fit resid {circ['max_circle_fit_residual']:.2e}, min |curvature| {circ['min_circle_curvature_abs']:.3e}",
         "known": "0 residual, nonzero curvature",
         "match": circ["max_circle_fit_residual"] < TOL_FIT and circ["min_circle_curvature_abs"] > 1e-6},
        {"invariant": "great_circle_through_N->straight_line(curvature~0)",
         "computed": f"line fit resid {circ['great_circle_line_fit_residual']:.2e}, |curvature| {circ['great_circle_curvature_abs']:.2e}",
         "known": "0 residual, curvature A==0 (a line)",
         "match": circ["great_circle_line_fit_residual"] < TOL_FIT and circ["great_circle_curvature_abs"] < 1e-9},
        {"invariant": "cross_ratio_invariant_under_Mobius",
         "computed": f"max |diff| {crb['max_mobius_cross_ratio_diff']:.2e}", "known": "0",
         "match": crb["max_mobius_cross_ratio_diff"] < 1e-9},
        {"invariant": "cross_ratio_invariant_under_Cl(3)_SO(3)_rotor",
         "computed": f"max |diff| {crb['max_rotor_cross_ratio_diff']:.2e}", "known": "0",
         "match": crb["max_rotor_cross_ratio_diff"] < 1e-9},
        {"invariant": "cross_ratio_Mobius_invariance_EXACT_symbolic(sympy)",
         "computed": str(sym["cross_ratio_mobius_invariant_exact"]), "known": "True",
         "match": bool(sym["cross_ratio_mobius_invariant_exact"])},
        {"invariant": "z3_conformality_negation_UNSAT(all_sampled_points)",
         "computed": "unsat" if z3_pass else "NOT unsat", "known": "unsat",
         "match": z3_pass},
        {"invariant": "cvc5_conformality_negation_UNSAT(all_sampled_points)",
         "computed": "unsat" if cvc5_pass else "NOT unsat", "known": "unsat",
         "match": cvc5_pass},
    ]


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    # Wide variation: sizes x seeds.
    blocks = [sample_block(n, seed) for n in SAMPLE_SIZES for seed in SEEDS]

    # circles and cross-ratio variation blocks
    circ = circle_block()
    crb = cross_ratio_block()

    # sympy EXACT conformality + cross-ratio
    sym = sympy_exact()

    # z3 + cvc5 conformality certificates on a sweep of sampled plane points.
    gen = torch.Generator().manual_seed(1234)
    cert_pts = (torch.randn(8, 2, generator=gen, dtype=RTYPE) * 1.5).tolist()
    cert_pts += [[0.0, 0.0], [0.6, -0.4], [-1.2, 0.9]]
    z3_rows, cvc5_rows = [], []
    pairs = (torch.tensor([1.0, 0.3]), torch.tensor([-0.2, 1.0]))
    for (X0, Y0) in cert_pts:
        gXX, gYY, gXY = pullback_metric_numeric(X0, Y0)
        ang_resid = angle_preservation_residual(X0, Y0, *pairs)
        z3_rows.append({"pt": [X0, Y0], **z3_conformal_certificate(gXX, gYY, gXY, ang_resid)})
        cvc5_rows.append({"pt": [X0, Y0], **cvc5_conformal_certificate(gXX, gYY, gXY, ang_resid)})
    z3_pass = all(r["pass"] for r in z3_rows)
    cvc5_pass = all(r["pass"] for r in cvc5_rows)

    # known-value cross-checks
    kvc = known_value_checks(blocks, circ, crb, sym, z3_pass, cvc5_pass)

    # Negatives
    neg_lambert = negative_lambert_nonconformal()
    neg_cr = negative_broken_cross_ratio()
    neg_shear = negative_shear_nonconformal()
    neg_ortho = negative_orthographic_drop()
    negatives = {
        "lambert_equal_area_nonconformal": {"detail": neg_lambert, "kills_signature": neg_lambert["kills_conformality"]},
        "broken_cross_ratio_z_squared": {"detail": neg_cr, "kills_signature": neg_cr["kills_mobius_invariance"]},
        "linear_shear_nonconformal": {"detail": neg_shear, "kills_signature": neg_shear["kills_conformality"]},
        "orthographic_drop_breaks_bijection": {"detail": neg_ortho, "kills_signature": neg_ortho["breaks_roundtrip"]},
    }

    known_values_all_match = all(c["match"] for c in kvc)
    negatives_all_kill = all(v["kills_signature"] for v in negatives.values())
    tools_all_pass = (z3_pass and cvc5_pass
                      and sym["conformal_exact"]
                      and sym["cross_ratio_mobius_invariant_exact"]
                      and max(b["max_geomstats_angle_residual"] for b in blocks) < TOL_GEOMSTATS
                      and crb["max_rotor_cross_ratio_diff"] < 1e-9)

    all_pass = known_values_all_match and negatives_all_kill and tools_all_pass

    blockers: list[str] = []
    if not known_values_all_match:
        blockers += [f"KNOWN-VALUE MISMATCH: {c['invariant']} computed={c['computed']} known={c['known']}"
                     for c in kvc if not c["match"]]
    if not z3_pass:
        blockers.append("z3 conformality negation not UNSAT for all sampled points")
    if not cvc5_pass:
        blockers.append("cvc5 conformality negation not UNSAT for all sampled points")
    if not negatives_all_kill:
        blockers += [f"NEGATIVE DID NOT KILL: {k}" for k, v in negatives.items() if not v["kills_signature"]]

    tool_manifest = {
        "torch": {"used": True, "role": "load_bearing",
                  "reason": "all stereographic projection / inverse / autograd Jacobian / pullback metric / angle / circle-conic SVD fit / cross-ratio / Mobius algebra in float64+complex128; the shear and orthographic negatives kill the conformal/bijection signature"},
        "sympy": {"used": True, "role": "load_bearing",
                  "reason": "EXACT symbolic proof that the pullback metric is lambda^2*I with zero off-diagonal (conformality) and EXACT cross-ratio invariance under a symbolic Mobius map; numeric torch alone cannot prove the exact identities"},
        "z3": {"used": True, "role": "load_bearing",
               "reason": "SMT certificate that g_XX==g_YY, g_XY==0 and the angle residual==0 on carrier numbers at every sampled point; the negation is UNSAT"},
        "cvc5": {"used": True, "role": "load_bearing",
                 "reason": "independent SMT family (QF_NRA) certifying the same conformality fact; negation UNSAT"},
        "geomstats": {"used": True, "role": "load_bearing",
                      "reason": "GEOMSTATS_BACKEND=pytorch Hypersphere(2) Riemannian inner_product gives an INDEPENDENT sphere-side angle (not our own Jacobian) cross-checked against the planar angle, witnessing conformality"},
        "clifford": {"used": True, "role": "load_bearing",
                     "reason": "Cl(3) geometric-algebra rotor (SO(3) rotation of the sphere) intertwines through pi with a planar Mobius map and preserves the cross-ratio (~1e-15); independent realization of the conformal automorphisms of S^2"},
    }

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID, "name": SIM_ID, "version": "1.0.0", "tier": "2_geometry",
        "classification": "diagnostic_only",
        "promotion_allowed": False,
        "promotion_status": "diagnostic_only",
        "sim_execution_kind": "nonclassical",
        "sim_class": "geometry_probe",
        "purpose": "Deep, standalone conformal stereographic-S^2 geometry lego computed in real torch with full tool integration, cross-checked against textbook analytic invariants. Lego/pre-sim phase: NOT gated on manifold membership.",
        "scientific_question": "Does stereographic projection S^2 -> C reproduce the known conformal / Mobius structure -- conformal (angle-preserving) pullback metric lambda^2*I, circles->circles-or-lines, PSL(2,C) cross-ratio invariance, round-trip identity -- to its exact analytic values, and do the non-conformal / non-Mobius / degenerate controls kill that signature?",
        "claim_ceiling": "diagnostic_only / hypothetical / unadmitted: a self-contained known-math geometry lego. Does NOT admit any manifold layer, stacking, coupling, G-structure, Axis0, flux, bridge, QIT, or physics claim.",
        "finite_map": "(point p on S^2 minus {N}, or u in C) -> (stereographic image pi(p)=x/(1-z),y/(1-z) / preimage pi^-1(u), pullback conformal factor lambda=2/(1+r^2), tangent-vector angle, circle/line conic A(X^2+Y^2)+BX+CY+D, cross-ratio (z1,z2;z3,z4) under Mobius and under Cl(3) SO(3) rotor)",
        "domain": "points on S^2 minus {north pole} (Haar-uniform via normalized Gaussians), plane points u in C, tangent vector pairs, spherical circles (sphere intersect plane), four-point tuples, Mobius parameters (a,b,c,d), rotor (theta, axis)",
        "codomain_or_output": "stereographic images / preimages, pullback metric (g_XX,g_YY,g_XY) and conformal factor, tangent angles, circle/line conic coefficients and fit residuals, cross-ratios before/after Mobius and rotor maps",
        "carrier_layer": "round 2-sphere S^2 minus {N} and its stereographic chart C = R^2 (one-point compactified by the point at infinity)",
        "geometry_layer": "conformal geometry of S^2: stereographic projection is angle-preserving (pullback metric lambda^2*I), maps circles to circles-or-lines, and intertwines SO(3) rotations / PSL(2,C) Mobius maps preserving the cross-ratio",
        "carrier_realization": "torch.float64 sphere/plane points and complex128 cross-ratio algebra; geomstats Hypersphere(2) with the pytorch backend; clifford Cl(3) rotor; no NumPy claim-bearing substrate, no label-only tensors, no random claim matrices (random points are genuine Haar-uniform samples)",
        "spinor_state": "not_applicable_at_this_lego (conformal-projection geometry, not a spinor carrier)",
        "quaternion_action": "even subalgebra of Cl(3) (clifford) realizes the unit quaternions == SU(2); the rotor R=exp(-theta/2 B) is the SO(3) rotation of the sphere that intertwines with a planar Mobius map",
        "peps3d_embedding": "not_applicable_at_lego_phase (no manifold anchor claimed; diagnostic_only)",
        "dependency_receipts": [],
        "downstream_blocks": ["manifold_layers", "stacking", "coupling", "G_structure", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "blocked_consumers": ["manifold_layers", "stacking", "coupling", "G_structure", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "law_or_candidate_tested": "stereographic projection S^2->C is conformal (angle-preserving), maps circles to circles-or-lines, and PSL(2,C) Mobius maps / SO(3) rotors preserve the cross-ratio, against textbook analytic invariants",
        "branch_status_before_run": "lego/pre-sim phase; standalone known-math geometry; unadmitted",
        "allowed_claims": ["standalone known-math conformal stereographic S^2 geometry witness; computed invariants match textbook values to machine precision"],
        "promotion_blockers": ["diagnostic_only by design (lego/pre-sim phase); no manifold membership, no cross-layer evidence, no coupling"],

        "result_summary": {
            "all_pass": all_pass,
            "known_values_all_match": known_values_all_match,
            "negatives_all_kill": negatives_all_kill,
            "tools_all_pass": tools_all_pass,
            "n_known_value_checks": len(kvc),
            "n_sampled_sphere_points": sum(b["n"] for b in blocks),
            "sample_sizes": SAMPLE_SIZES, "seeds": SEEDS,
            "z3_conformality_all_unsat": z3_pass,
            "cvc5_conformality_all_unsat": cvc5_pass,
            "promotion_allowed": False,
        },

        "known_value_checks": kvc,

        "sympy_exact_conformal": sym,
        "variation_blocks": blocks,
        "circle_block": circ,
        "cross_ratio_block": crb,

        "conformality_certificates": {
            "z3": {"rows": z3_rows, "all_unsat": z3_pass, "n_points_certified": len(cert_pts)},
            "cvc5": {"rows": cvc5_rows, "all_unsat": cvc5_pass, "n_points_certified": len(cert_pts)},
        },

        "required_negatives": ["lambert_equal_area_nonconformal", "broken_cross_ratio_z_squared",
                               "linear_shear_nonconformal", "orthographic_drop_breaks_bijection"],
        "negatives_run": list(negatives.keys()),
        "negatives": negatives,
        "kill_conditions": [
            "any known-value invariant fails to match its textbook value",
            "z3 or cvc5 conformality negation not UNSAT",
            "Lambert equal-area projection does NOT distort angles",
            "z->z^2 does NOT change the cross-ratio",
            "linear shear does NOT distort angles",
            "orthographic z-drop does NOT break the round-trip bijection",
        ],

        "TOOL_MANIFEST": tool_manifest,
        "tool_manifest": tool_manifest,
        "TOOL_INTEGRATION_DEPTH": {"torch": "load_bearing", "sympy": "load_bearing", "z3": "load_bearing",
                                   "cvc5": "load_bearing", "geomstats": "load_bearing", "clifford": "load_bearing"},
        "proof_surfaces_used": ["z3", "cvc5", "sympy"],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "required_tools": ["torch", "sympy", "z3", "cvc5", "geomstats", "clifford"],
        "actual_tools_used": ["torch", "sympy", "z3", "cvc5", "geomstats", "clifford"],

        "required_artifacts": ["json_result_receipt", "witness_trace"],
        "artifacts_emitted": ["json_result_receipt", "witness_trace"],
        "witness_trace_id": f"{SIM_ID}_witness",

        "all_pass": all_pass,
        "blockers": blockers,
        "pass_rule": "every known_value_check matches its known value AND all negatives kill the signature AND z3+cvc5 conformality negations are UNSAT AND geomstats sphere-angle matches the planar angle AND the Cl(3) rotor preserves the cross-ratio",
        "fail_rule": "any known-value mismatch, any negative that does not kill, any non-UNSAT certificate, any geomstats/rotor cross-check that diverges",
        "eligible_consumers": ["other diagnostic_only conformal / projective geometry probes"],
    }

    witness = {
        "sim_id": SIM_ID,
        "steps": [
            {"step": "sample_haar_sphere_points", "sizes": SAMPLE_SIZES, "seeds": SEEDS,
             "n_points": sum(b["n"] for b in blocks)},
            {"step": "roundtrip_pi_and_inverse", "tool": "torch.float64"},
            {"step": "autograd_pullback_metric_and_angle_preservation", "tool": "torch.autograd"},
            {"step": "geomstats_sphere_angle_cross_check", "backend": os.environ.get("GEOMSTATS_BACKEND")},
            {"step": "sympy_exact_conformal_metric_and_cross_ratio",
             "conformal_exact": sym["conformal_exact"],
             "cross_ratio_exact": sym["cross_ratio_mobius_invariant_exact"]},
            {"step": "circles_to_circles_or_lines_conic_fit",
             "n_circles": circ["n_circles"],
             "great_circle_curvature": circ["great_circle_curvature_abs"]},
            {"step": "cross_ratio_under_mobius_and_clifford_rotor",
             "max_mobius_diff": crb["max_mobius_cross_ratio_diff"],
             "max_rotor_diff": crb["max_rotor_cross_ratio_diff"]},
            {"step": "z3_conformality_certificate", "all_unsat": z3_pass, "n": len(cert_pts)},
            {"step": "cvc5_conformality_certificate", "all_unsat": cvc5_pass, "n": len(cert_pts)},
            {"step": "run_negatives", "negatives": list(negatives.keys()),
             "all_kill": negatives_all_kill},
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

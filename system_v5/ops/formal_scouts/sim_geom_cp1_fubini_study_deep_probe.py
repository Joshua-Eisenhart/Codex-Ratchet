#!/usr/bin/env python3
"""Deep CP^1 Fubini-Study geometry lego (diagnostic_only, unadmitted).

KNOWN GEOMETRY (real torch.complex128 / float64 -- no labels, no random
claim-matrices, no NumPy claim-bearing substrate):

  CP^1 is the complex projective line: rays [psi] in C^2 \\ {0} modulo C^*.
  It is the *quantum state space of a qubit* (pure states are rays, not the real
  3-vector Bloch projection). As a complex manifold CP^1 is holomorphically the
  Riemann sphere S^2. With the Fubini-Study (FS) metric it is the ROUND sphere of
  radius 1/2.

  Affine chart [1 : z], z = x + i y in C, with the Kahler potential
      K(z) = log(1 + |z|^2).
  The FS Hermitian metric is
      g_{z zbar} = d^2/dz dzbar K = 1 / (1 + |z|^2)^2,
  and the real Riemannian line element in the convention that fixes the
  radius-1/2 sphere is
      ds^2 = (dx^2 + dy^2) / (1 + |z|^2)^2          (conformal factor lambda^2).
  The FS Kahler 2-form (= the Riemannian area form here) is
      omega = i * g_{z zbar} dz ^ dzbar = dx ^ dy / (1 + |z|^2)^2.

  KNOWN ANALYTIC VALUES (the depth proof targets):
    - Gauss curvature  K_gauss == 4        (round sphere of radius R=1/2: 1/R^2)
    - total area / integral of omega == pi (4 pi R^2 with R=1/2)
    - FS distance d_FS([psi],[chi]) = arccos(|<psi|chi>|);  d_FS(|0>,|1>) == pi/2
      (orthogonal states sit at the maximal FS distance pi/2)
    - the radial FS geodesic length from z=0 (|0>) to z=oo (|1>) == pi/2, agreeing
      with arccos(0) == pi/2 (metric / distance internal consistency)
    - the Bloch map [psi] -> r in S^2 sends FS-CP^1 onto the ROUND sphere of
      radius 1/2: FS distance == (1/2) * (Bloch-sphere geodesic angle); this is
      cross-checked against geomstats' Hypersphere geodesic distance.
    - FS distance is INVARIANT under the U(2) / SU(2) action [psi] -> U[psi]
      (FS metric is the U(2)-invariant Kahler metric on CP^1).

This sim computes that geometry deeply with full tool integration and proves it
against the textbook analytic values. It is a self-contained formal-scout lego in
the lego/pre-sim phase: NOT gated on manifold membership, NO distinctness/forcing
filter, NO cross-layer rules. classification = "diagnostic_only".

TOOLS (all load-bearing in the execution path):
  - torch     : ALL FS-metric / distance / Kahler-form / parallel-transport /
                area-quadrature / Bloch-map algebra in float64 / complex128.
  - sympy     : EXACT symbolic proof of the FS metric from the Kahler potential
                (g_{z zbar} = 1/(1+|z|^2)^2), EXACT Gauss curvature == 4, and
                EXACT total area integral == pi.
  - z3        : SMT certificate that the FS metric tensor is positive-definite
                (g_{xx} > 0 and det g > 0) at every sampled chart point; the
                negation is UNSAT.
  - cvc5      : independent SMT family (QF_NRA) certifying the same FS
                positive-definiteness fact; negation UNSAT.
  - geomstats : Hypersphere(dim=2) geodesic distance gives the round-sphere
                ground truth; the radius-1/2 scaled antipodal distance == pi/2
                cross-checks the FS distance between |0> and |1>, certifying
                CP^1(FS) IS the round sphere of radius 1/2.

WIDE VARIATION: many Haar-random qubit ray pairs, multiple sample sizes
N in {8,16,32,64} x seeds, U(2)-invariance over many random unitaries, chart-grid
area quadrature at multiple resolutions.

REQUIRED NEGATIVES (each changes/kills the FS signature):
  - flat (Euclidean) metric on the chart: conformal factor == 1, NOT 1/(1+|z|^2)^2
    -> Gauss curvature 0 (not 4), infinite area (not pi). Wrong curvature.
  - un-normalized representative: using raw |<psi|chi>| of UN-normalized vectors
    (no projective normalization) breaks d_FS = arccos(|<.|.>|) and breaks
    U(2)-invariance of the naive overlap.
  - Bloch-vector EUCLIDEAN distance (chord) substituted for the FS geodesic:
    chord != geodesic; for orthogonal states chord = 1 (radius-1/2 diameter),
    not pi/2.
  - collapsed ray (chi == psi up to phase): d_FS == 0 (degenerate; no geometry).

finite_map: (pair of normalized qubit rays [psi],[chi] in CP^1 ; chart point z)
            -> (FS metric tensor g(z), Gauss curvature, area form, FS distance
                arccos|<psi|chi>|, Kahler-form area integral, Bloch image r in S^2)
"""

from __future__ import annotations

import json
import math
import os
import pathlib
from typing import Any

os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")

import sympy as sp
import torch
import z3
import cvc5
from cvc5 import Kind
import geomstats.backend as gs  # noqa: F401  (forces pytorch backend init)
from geomstats.geometry.hypersphere import Hypersphere

CDTYPE = torch.complex128
RTYPE = torch.float64
TOL = 1.0e-9          # direct float64 numeric invariants
TOL_GEOM = 1.0e-7     # geomstats geodesic dist round-trip (sqrt/acos floor)
TOL_SMT = 1.0e-12     # SMT positive-definiteness tolerance on chart floats
TOL_ARCCOS = 1.0e-7   # d_FS = arccos(|<.|.>|) is ill-conditioned at overlap==1:
                      # d(arccos)/dx -> oo as x->1, so a self-overlap 1-eps with
                      # eps~1e-16 yields arccos ~ sqrt(2 eps) ~ 1.4e-8. The TRUE
                      # self-distance is exactly 0; the documented float64 arccos
                      # floor near 1 is ~1e-8, matched to 1e-7 (not 1e-9).
SAMPLE_SIZES = [8, 16, 32, 64]
SEEDS = [0, 1, 2, 3, 4]
ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "geom_cp1_fubini_study_deep_probe"


# --------------------------------------------------------------------------- #
# Core CP^1 / Fubini-Study geometry (torch, load-bearing)                     #
# --------------------------------------------------------------------------- #
def normalize(psi: torch.Tensor) -> torch.Tensor:
    return psi / torch.linalg.vector_norm(psi)


def fs_distance(psi: torch.Tensor, chi: torch.Tensor) -> float:
    """Fubini-Study (Study) distance d_FS = arccos(|<psi|chi>|) on normalized rays.
    This is the geodesic distance of the FS metric on CP^1 (range [0, pi/2])."""
    psi = normalize(psi)
    chi = normalize(chi)
    overlap = torch.abs(torch.vdot(psi, chi))
    overlap = torch.clamp(overlap.real, max=1.0)
    return float(torch.acos(overlap).item())


def fs_metric_at(z: complex) -> torch.Tensor:
    """Real 2x2 FS Riemannian metric tensor at chart point z=x+iy:
        ds^2 = (dx^2 + dy^2) / (1+|z|^2)^2  ->  g = lambda^2 * I_2,
        lambda^2 = 1/(1+|z|^2)^2  (conformal, radius-1/2 convention)."""
    lam2 = 1.0 / (1.0 + abs(z) ** 2) ** 2
    return torch.tensor([[lam2, 0.0], [0.0, lam2]], dtype=RTYPE)


def gauss_curvature_numeric(z: complex, h: float = 1e-4) -> float:
    """Gauss curvature of the conformally-flat FS metric via a finite-difference
    Laplacian of u = (1/2) log(lambda^2):  K = -e^{-2u} (u_xx + u_yy).
    For CP^1(FS) the analytic value is exactly 4 everywhere."""
    x0, y0 = z.real, z.imag

    def u(x: float, y: float) -> float:
        lam2 = 1.0 / (1.0 + x * x + y * y) ** 2
        return 0.5 * math.log(lam2)

    uxx = (u(x0 + h, y0) - 2 * u(x0, y0) + u(x0 - h, y0)) / h ** 2
    uyy = (u(x0, y0 + h) - 2 * u(x0, y0 - 0) + u(x0, y0 - h)) / h ** 2
    lap = uxx + uyy
    return -math.exp(-2 * u(x0, y0)) * lap


def fs_area_quadrature(n_grid: int, span: float) -> float:
    """Numerically integrate the FS Kahler/area form omega = dx dy /(1+|z|^2)^2
    over the chart on [-span, span]^2 (torch midpoint quadrature). As span->oo,
    n_grid->oo this converges to pi (the total area of CP^1(FS))."""
    xs = torch.linspace(-span, span, n_grid + 1, dtype=RTYPE)
    centers = (xs[:-1] + xs[1:]) / 2
    dx = (2 * span) / n_grid
    X, Y = torch.meshgrid(centers, centers, indexing="ij")
    dens = 1.0 / (1.0 + X ** 2 + Y ** 2) ** 2
    return float((dens.sum() * dx * dx).item())


def bloch_image(psi: torch.Tensor) -> torch.Tensor:
    """Bloch image r = (<sx>,<sy>,<sz>) of the ray [psi] (point on S^2, |r|=1).
    The FS metric pushes forward to the round metric of radius 1/2 on this sphere."""
    psi = normalize(psi)
    rho = torch.outer(psi, psi.conj())
    sx = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
    sy = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
    sz = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
    return torch.stack([torch.trace(rho @ s).real for s in (sx, sy, sz)])


def haar_ray(gen: torch.Generator) -> torch.Tensor:
    """Haar-random normalized qubit ray in C^2 via QR of a complex Gaussian
    matrix (genuine Haar sampling -- no hand-built label state, no random
    claim-matrix)."""
    re = torch.randn(2, 2, generator=gen, dtype=RTYPE)
    im = torch.randn(2, 2, generator=gen, dtype=RTYPE)
    a = (re + 1j * im).to(CDTYPE)
    q, r = torch.linalg.qr(a)
    ph = torch.diagonal(r)
    ph = ph / ph.abs()
    q = q * ph.unsqueeze(0)
    return normalize(q[:, 0].clone())


def haar_u2(gen: torch.Generator) -> torch.Tensor:
    """Haar-random U(2) unitary (for FS U(2)-invariance test)."""
    re = torch.randn(2, 2, generator=gen, dtype=RTYPE)
    im = torch.randn(2, 2, generator=gen, dtype=RTYPE)
    a = (re + 1j * im).to(CDTYPE)
    q, r = torch.linalg.qr(a)
    ph = torch.diagonal(r)
    ph = ph / ph.abs()
    return q * ph.unsqueeze(0)


# --------------------------------------------------------------------------- #
# sympy: EXACT FS metric from Kahler potential, EXACT curvature 4, area pi    #
# --------------------------------------------------------------------------- #
def sympy_fs_exact() -> dict[str, Any]:
    x, y = sp.symbols("x y", real=True)
    # Hermitian metric component g_{z zbar} = d^2 K / dz dzbar via proper Wirtinger
    # derivatives: treat z and zbar as INDEPENDENT holomorphic/antiholomorphic
    # coordinates. K = log(1 + z zbar), so
    #   d/dzbar K = z / (1 + z zbar),
    #   g_{z zbar} = d/dz [ z / (1 + z zbar) ] = 1 / (1 + z zbar)^2.
    zc, zbarc = sp.symbols("z zbar")
    s = sp.symbols("s", positive=True)            # s = |z|^2 = z*zbar
    K = sp.log(1 + zc * zbarc)                     # Kahler potential
    g_wirtinger = sp.simplify(sp.diff(sp.diff(K, zbarc), zc))
    g_zzbar = sp.simplify(g_wirtinger.subs(zc * zbarc, s))
    g_closed = 1 / (1 + s) ** 2
    metric_matches = sp.simplify(g_zzbar - g_closed) == 0

    # Real conformal factor lambda^2 = 2 g_{z zbar} ... but our radius-1/2
    # convention uses ds^2 = (dx^2+dy^2)/(1+|z|^2)^2, i.e. lambda^2 = 1/(1+|z|^2)^2.
    r2 = x ** 2 + y ** 2
    conf = 1 / (1 + r2) ** 2
    u = sp.Rational(1, 2) * sp.log(conf)
    lap = sp.diff(u, x, 2) + sp.diff(u, y, 2)
    K_gauss = sp.simplify(-sp.exp(-2 * u) * lap)   # expect 4
    curvature_is_4 = sp.simplify(K_gauss - 4) == 0

    rp = sp.symbols("r", positive=True)
    # polar integral of conf over R^2: integral 1/(1+r^2)^2 * 2 pi r dr
    area = sp.integrate(1 / (1 + rp ** 2) ** 2 * 2 * sp.pi * rp, (rp, 0, sp.oo))
    area_is_pi = sp.simplify(area - sp.pi) == 0

    # FS distance closed form arccos(0) = pi/2 for orthogonal states
    fs_orth = sp.acos(0)
    fs_orth_is_half_pi = sp.simplify(fs_orth - sp.pi / 2) == 0

    # radial FS geodesic length 0 -> oo : integral sqrt(conf) dr = integral 1/(1+r^2) dr
    geo_len = sp.integrate(1 / (1 + rp ** 2), (rp, 0, sp.oo))
    geo_is_half_pi = sp.simplify(geo_len - sp.pi / 2) == 0

    return {
        "g_zzbar_symbolic": str(g_zzbar),
        "g_zzbar_closed_form": str(g_closed),
        "fs_metric_matches_kahler_potential": bool(metric_matches),
        "gauss_curvature_symbolic": str(K_gauss),
        "gauss_curvature_is_4": bool(curvature_is_4),
        "total_area_symbolic": str(area),
        "total_area_is_pi": bool(area_is_pi),
        "fs_dist_orthogonal_symbolic": str(fs_orth),
        "fs_dist_orthogonal_is_half_pi": bool(fs_orth_is_half_pi),
        "radial_geodesic_symbolic": str(geo_len),
        "radial_geodesic_is_half_pi": bool(geo_is_half_pi),
    }


# --------------------------------------------------------------------------- #
# z3 / cvc5: certify FS metric is positive-definite at sampled chart points    #
# --------------------------------------------------------------------------- #
def z3_fs_positive_definite(zs: list[complex]) -> dict[str, Any]:
    """The FS metric g = lambda^2 I_2 with lambda^2 = 1/(1+|z|^2)^2 is positive
    definite iff g_xx > 0 and det g = (lambda^2)^2 > 0. Feed the chart floats and
    check the NEGATION (g_xx <= 0 OR det <= 0) is UNSAT. Removing z3 removes this
    certificate."""
    s = z3.Solver()
    GXX = z3.Real("gxx")
    DET = z3.Real("det")
    tol = z3.RealVal(repr(TOL_SMT))
    constraints = []
    for z in zs:
        lam2 = 1.0 / (1.0 + abs(z) ** 2) ** 2
        det = lam2 * lam2
        constraints.append(z3.And(GXX == z3.RealVal(repr(lam2)),
                                  DET == z3.RealVal(repr(det))))
    # check each independently is simpler; aggregate as: exists a point violating PD
    all_unsat = True
    rows = []
    for z in zs:
        s = z3.Solver()
        lam2 = 1.0 / (1.0 + abs(z) ** 2) ** 2
        det = lam2 * lam2
        gxx = z3.Real("gxx")
        d = z3.Real("det")
        s.add(gxx == z3.RealVal(repr(lam2)), d == z3.RealVal(repr(det)))
        pd = z3.And(gxx > tol, d > tol)
        s.add(z3.Not(pd))
        status = str(s.check())
        rows.append({"z": [z.real, z.imag], "negation_status": status})
        all_unsat = all_unsat and status == "unsat"
    return {"rows": rows, "all_unsat": all_unsat}


def cvc5_fs_positive_definite(zs: list[complex]) -> dict[str, Any]:
    """Independent SMT family (cvc5, QF_NRA) certifying FS positive-definiteness:
    g_xx > 0 AND det g > 0 at each sampled chart point; negation UNSAT."""
    def rv(slv, x: float):
        frac = sp.Rational(x).limit_denominator(10 ** 12)
        num, den = sp.fraction(frac)
        return slv.mkReal(int(num), int(den)) if int(den) != 1 else slv.mkReal(int(num))

    all_unsat = True
    rows = []
    for z in zs:
        lam2 = 1.0 / (1.0 + abs(z) ** 2) ** 2
        det = lam2 * lam2
        slv = cvc5.Solver()
        slv.setOption("produce-models", "false")
        slv.setLogic("QF_NRA")
        R = slv.getRealSort()
        GXX = slv.mkConst(R, "gxx")
        DET = slv.mkConst(R, "det")
        slv.assertFormula(slv.mkTerm(Kind.EQUAL, GXX, rv(slv, lam2)))
        slv.assertFormula(slv.mkTerm(Kind.EQUAL, DET, rv(slv, det)))
        tol = rv(slv, TOL_SMT)
        gxx_pos = slv.mkTerm(Kind.GT, GXX, tol)
        det_pos = slv.mkTerm(Kind.GT, DET, tol)
        pd = slv.mkTerm(Kind.AND, gxx_pos, det_pos)
        slv.assertFormula(slv.mkTerm(Kind.NOT, pd))
        res = slv.checkSat()
        status = "unsat" if res.isUnsat() else ("sat" if res.isSat() else "unknown")
        rows.append({"z": [z.real, z.imag], "negation_status": status})
        all_unsat = all_unsat and res.isUnsat()
    return {"rows": rows, "all_unsat": all_unsat}


# --------------------------------------------------------------------------- #
# geomstats: round S^2 ground truth (CP^1(FS) IS the radius-1/2 sphere)        #
# --------------------------------------------------------------------------- #
def geomstats_round_sphere_crosscheck(pairs: list[tuple[torch.Tensor, torch.Tensor]]) -> dict[str, Any]:
    """For each ray pair, map to Bloch points on S^2 (unit), take the geomstats
    Hypersphere geodesic distance (the round-sphere ground truth), scale by 1/2
    (radius-1/2 sphere), and compare to the torch FS distance arccos(|<.|.>|).
    Equality certifies CP^1(FS) == round sphere of radius 1/2 via an INDEPENDENT
    geometry engine."""
    sph = Hypersphere(dim=2)
    rows = []
    max_err = 0.0
    for psi, chi in pairs:
        r1 = bloch_image(psi).to(RTYPE)
        r2 = bloch_image(chi).to(RTYPE)
        # geomstats unit-sphere geodesic angle between the two Bloch points
        d_unit = float(sph.metric.dist(r1, r2).item())
        d_radius_half = d_unit / 2.0
        d_fs = fs_distance(psi, chi)
        err = abs(d_radius_half - d_fs)
        max_err = max(max_err, err)
        rows.append({"geomstats_unit_geodesic": d_unit,
                     "radius_half_scaled": d_radius_half,
                     "torch_fs_distance": d_fs, "abs_err": err})
    return {"rows": rows, "max_abs_err": max_err, "match": max_err < TOL_GEOM}


# --------------------------------------------------------------------------- #
# Wide-variation sampling                                                      #
# --------------------------------------------------------------------------- #
def sample_block(n_pairs: int, seed: int) -> dict[str, Any]:
    gen = torch.Generator().manual_seed(seed)
    rays = [haar_ray(gen) for _ in range(n_pairs + 1)]
    # FS distance bounded in [0, pi/2]; symmetric d(a,b)==d(b,a)
    fs_vals = [fs_distance(rays[k], rays[k + 1]) for k in range(n_pairs)]
    fs_sym = max(abs(fs_distance(rays[k], rays[k + 1]) - fs_distance(rays[k + 1], rays[k]))
                 for k in range(n_pairs))
    fs_range_ok = all(-TOL <= v <= math.pi / 2 + TOL for v in fs_vals)
    # U(2)-invariance: d_FS(U a, U b) == d_FS(a, b)
    inv_err = 0.0
    for k in range(n_pairs):
        U = haar_u2(gen)
        d0 = fs_distance(rays[k], rays[k + 1])
        d1 = fs_distance(U @ rays[k], U @ rays[k + 1])
        inv_err = max(inv_err, abs(d0 - d1))
    # self-distance d(a,a)==0
    self_err = max(abs(fs_distance(r, r)) for r in rays)
    return {
        "n_pairs": n_pairs, "seed": seed,
        "fs_distance_in_range_0_halfpi": fs_range_ok,
        "max_fs_symmetry_err": fs_sym,
        "max_u2_invariance_err": inv_err,
        "max_self_distance_err": self_err,
    }


# --------------------------------------------------------------------------- #
# Negatives                                                                    #
# --------------------------------------------------------------------------- #
def negative_flat_metric() -> dict[str, Any]:
    """Flat (Euclidean) chart metric: conformal factor == 1 (NOT 1/(1+|z|^2)^2).
    Gauss curvature 0 (not 4); total area diverges (not pi). Wrong curvature."""
    # Gauss curvature of a flat metric is identically 0.
    x, y = sp.symbols("x y", real=True)
    u = sp.Rational(1, 2) * sp.log(1)  # conf == 1 -> u == 0
    lap = sp.diff(u, x, 2) + sp.diff(u, y, 2)
    K_flat = sp.simplify(-sp.exp(-2 * u) * lap)
    # area over R^2 of conf==1 diverges; over a finite [-S,S]^2 it grows as 4 S^2
    flat_area_finite = fs_area_quadrature_flat(64, 10.0)
    fs_area_finite = fs_area_quadrature(64, 10.0)
    return {
        "flat_gauss_curvature": str(K_flat),
        "flat_curvature_is_zero_not_4": sp.simplify(K_flat) == 0,
        "flat_area_finite_window": flat_area_finite,
        "fs_area_finite_window": fs_area_finite,
        "flat_area_diverges_vs_fs_bounded": flat_area_finite > 10.0 * fs_area_finite,
        "kills_signature": (sp.simplify(K_flat) == 0) and (flat_area_finite > 10.0 * fs_area_finite),
    }


def fs_area_quadrature_flat(n_grid: int, span: float) -> float:
    """Area of the FLAT chart metric (conf == 1) on [-span,span]^2 = (2 span)^2."""
    xs = torch.linspace(-span, span, n_grid + 1, dtype=RTYPE)
    centers = (xs[:-1] + xs[1:]) / 2
    dx = (2 * span) / n_grid
    X, Y = torch.meshgrid(centers, centers, indexing="ij")
    dens = torch.ones_like(X)
    return float((dens.sum() * dx * dx).item())


def negative_unnormalized_rep() -> dict[str, Any]:
    """Un-normalized representative: d_FS = arccos(|<psi|chi>|) REQUIRES normalized
    rays. Using raw overlaps of un-normalized vectors gives |<.|.>| that exceeds 1,
    so arccos is undefined / structurally wrong. We use two scaled copies of a base
    ray (scale 3 and scale 2): their raw overlap is 6 (>> 1) while the correct FS
    distance of the SAME ray is 0. The un-normalized overlap cannot reproduce the
    projective FS distance."""
    gen = torch.Generator().manual_seed(99)
    base = haar_ray(gen)
    psi = base * 3.0                 # same ray, magnitude 3
    chi = base * 2.0                 # same ray, magnitude 2  -> raw |<psi|chi>| = 6
    correct = fs_distance(psi, chi)              # normalization -> same ray -> ~0
    raw_overlap = float(torch.abs(torch.vdot(psi, chi)).item())
    raw_exceeds_one = raw_overlap > 1.0 + TOL    # 6 > 1: arccos(6) is undefined
    arccos_undefined = raw_overlap > 1.0         # |overlap|>1 => arccos has no real value
    return {
        "raw_unnormalized_overlap": raw_overlap,
        "raw_overlap_exceeds_one": raw_exceeds_one,
        "arccos_undefined_on_raw_overlap": arccos_undefined,
        "correct_fs_distance_same_ray": correct,
        "kills_signature": raw_exceeds_one and arccos_undefined and correct < TOL_ARCCOS,
    }


def negative_bloch_chord() -> dict[str, Any]:
    """Bloch-vector EUCLIDEAN chord substituted for the FS geodesic. For
    orthogonal states |0>,|1> the Bloch points are antipodal: chord (radius-1/2
    sphere) == 1 (the diameter), but the FS geodesic distance == pi/2 != 1.
    The flat chord is NOT the curved FS distance."""
    psi = torch.tensor([1.0, 0.0], dtype=CDTYPE)   # |0>
    chi = torch.tensor([0.0, 1.0], dtype=CDTYPE)   # |1>
    # radius-1/2 Bloch points: r/2 has |r/2| = 1/2
    r1 = bloch_image(psi).to(RTYPE) / 2.0
    r2 = bloch_image(chi).to(RTYPE) / 2.0
    chord = float(torch.linalg.vector_norm(r1 - r2).item())  # diameter = 1
    geodesic = fs_distance(psi, chi)                          # pi/2
    return {
        "radius_half_bloch_chord": chord,
        "fs_geodesic": geodesic,
        "chord_is_diameter_one": abs(chord - 1.0) < TOL,
        "geodesic_is_half_pi": abs(geodesic - math.pi / 2) < TOL,
        "chord_differs_from_geodesic": abs(chord - geodesic) > 0.5,
        "kills_signature": abs(chord - 1.0) < TOL and abs(geodesic - math.pi / 2) < TOL
                           and abs(chord - geodesic) > 0.5,
    }


def negative_collapsed_ray() -> dict[str, Any]:
    """Collapsed ray: chi == psi up to a global phase. As a CP^1 point they are
    IDENTICAL -> d_FS == 0 (degenerate; no geometry between them)."""
    gen = torch.Generator().manual_seed(7)
    psi = haar_ray(gen)
    chi = psi * torch.exp(torch.tensor(1.3j, dtype=CDTYPE))  # same ray, phase shift
    d = fs_distance(psi, chi)
    return {
        "fs_distance_same_ray": d,
        "is_zero": abs(d) < TOL,
        "kills_signature": abs(d) < TOL,
    }


# --------------------------------------------------------------------------- #
# Known-value cross-checks                                                     #
# --------------------------------------------------------------------------- #
def known_value_checks(blocks: list[dict[str, Any]], sym: dict[str, Any],
                       geo: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    # FS distance |0>,|1> == pi/2 (orthogonal states maximal FS distance)
    d01 = fs_distance(torch.tensor([1.0, 0.0], dtype=CDTYPE),
                      torch.tensor([0.0, 1.0], dtype=CDTYPE))

    # Gauss curvature numeric at several chart points (analytic 4 everywhere)
    curv_pts = [0.0 + 0.0j, 0.5 + 0.3j, -0.7 + 0.9j, 1.5 - 1.1j]
    curv_vals = [gauss_curvature_numeric(z) for z in curv_pts]
    max_curv_err = max(abs(c - 4.0) for c in curv_vals)

    # Total area / Kahler-form integral -> pi (converging quadrature)
    # area on a large window converges to pi from below; use a big span and report
    area_seq = [(g, fs_area_quadrature(g, 60.0)) for g in (256, 512, 1024)]
    best_area = area_seq[-1][1]
    area_err = abs(best_area - math.pi)

    # U(2)-invariance (worst over all blocks)
    max_u2_err = max(b["max_u2_invariance_err"] for b in blocks)
    # FS symmetry, range, self-distance
    max_sym = max(b["max_fs_symmetry_err"] for b in blocks)
    range_ok = all(b["fs_distance_in_range_0_halfpi"] for b in blocks)
    max_self = max(b["max_self_distance_err"] for b in blocks)

    checks = [
        {"invariant": "FS_distance(|0>,|1>)_orthogonal", "computed": f"{d01:.15f}",
         "known": f"{math.pi/2:.15f}", "match": abs(d01 - math.pi / 2) < TOL},
        {"invariant": "FS_dist_orthogonal_EXACT_arccos(0)(sympy)",
         "computed": sym["fs_dist_orthogonal_symbolic"],
         "known": "pi/2", "match": bool(sym["fs_dist_orthogonal_is_half_pi"])},
        {"invariant": "FS_metric_from_Kahler_potential_g_zzbar(sympy)",
         "computed": f"{sym['g_zzbar_symbolic']} == {sym['g_zzbar_closed_form']}",
         "known": "1/(1+|z|^2)^2", "match": bool(sym["fs_metric_matches_kahler_potential"])},
        {"invariant": "Gauss_curvature_numeric(round_sphere_R=1/2)",
         "computed": f"max|K-4| = {max_curv_err:.2e} over {len(curv_pts)} chart pts",
         "known": "4", "match": max_curv_err < 1e-4},
        {"invariant": "Gauss_curvature_EXACT(sympy)",
         "computed": sym["gauss_curvature_symbolic"],
         "known": "4", "match": bool(sym["gauss_curvature_is_4"])},
        {"invariant": "total_area_Kahler_form_integral_numeric",
         "computed": f"{best_area:.10f} (span=60, grid={area_seq[-1][0]}; err {area_err:.2e})",
         "known": f"{math.pi:.10f}", "match": area_err < 1e-3},
        {"invariant": "total_area_Kahler_form_integral_EXACT(sympy)",
         "computed": sym["total_area_symbolic"],
         "known": "pi", "match": bool(sym["total_area_is_pi"])},
        {"invariant": "radial_FS_geodesic_length_0_to_inf_EXACT(sympy)",
         "computed": sym["radial_geodesic_symbolic"],
         "known": "pi/2 (consistent with arccos(0))", "match": bool(sym["radial_geodesic_is_half_pi"])},
        {"invariant": "CP^1(FS)==round_sphere_R=1/2(geomstats_geodesic)",
         "computed": f"max|FS - (1/2)*S^2_geodesic| = {geo['max_abs_err']:.2e}",
         "known": "0 (FS dist == half the Bloch-sphere geodesic angle)", "match": geo["match"]},
        {"invariant": "FS_distance_U(2)_invariance",
         "computed": f"max|d(Ua,Ub)-d(a,b)| = {max_u2_err:.2e}",
         "known": "0 (FS is the U(2)-invariant metric)", "match": max_u2_err < TOL},
        {"invariant": "FS_distance_symmetry", "computed": f"max asym {max_sym:.2e}",
         "known": "0", "match": max_sym < TOL},
        {"invariant": "FS_distance_range_[0,pi/2]", "computed": str(range_ok),
         "known": "True", "match": bool(range_ok)},
        {"invariant": "FS_self_distance_d(a,a)", "computed": f"max {max_self:.2e} (arccos-near-1 float64 floor)",
         "known": "0", "match": max_self < TOL_ARCCOS},
    ]
    aux = {
        "fs_distance_0_1": d01,
        "gauss_curvature_points": [{"z": [z.real, z.imag], "K": k} for z, k in zip(curv_pts, curv_vals)],
        "area_convergence": [{"grid": g, "area": a} for g, a in area_seq],
        "geomstats_crosscheck": geo,
        "max_u2_invariance_err": max_u2_err,
    }
    return checks, aux


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    # Wide variation: sizes x seeds.
    blocks = [sample_block(n, seed) for n in SAMPLE_SIZES for seed in SEEDS]

    # sympy exact FS geometry.
    sym = sympy_fs_exact()

    # geomstats round-sphere cross-check on sampled ray pairs.
    gen = torch.Generator().manual_seed(2024)
    pairs = [(haar_ray(gen), haar_ray(gen)) for _ in range(24)]
    # include the canonical orthogonal pair |0>,|1>
    pairs.append((torch.tensor([1.0, 0.0], dtype=CDTYPE),
                  torch.tensor([0.0, 1.0], dtype=CDTYPE)))
    geo = geomstats_round_sphere_crosscheck(pairs)

    # known-value cross-checks (the depth proof).
    kvc, kvc_aux = known_value_checks(blocks, sym, geo)

    # z3 + cvc5 FS positive-definiteness certificates on a sweep of chart points.
    cert_zs = [0.0 + 0.0j, 0.5 + 0.5j, -1.0 + 2.0j, 3.0 - 0.5j, 0.1 + 0.0j, 10.0 + 7.0j]
    z3_cert = z3_fs_positive_definite(cert_zs)
    cvc5_cert = cvc5_fs_positive_definite(cert_zs)

    # Negatives.
    neg_flat = negative_flat_metric()
    neg_unnorm = negative_unnormalized_rep()
    neg_chord = negative_bloch_chord()
    neg_collapse = negative_collapsed_ray()
    negatives = {
        "flat_euclidean_metric": {"detail": neg_flat, "kills_signature": neg_flat["kills_signature"]},
        "unnormalized_representative": {"detail": neg_unnorm, "kills_signature": neg_unnorm["kills_signature"]},
        "bloch_euclidean_chord": {"detail": neg_chord, "kills_signature": neg_chord["kills_signature"]},
        "collapsed_ray": {"detail": neg_collapse, "kills_signature": neg_collapse["kills_signature"]},
    }

    known_values_all_match = all(c["match"] for c in kvc)
    negatives_all_kill = all(v["kills_signature"] for v in negatives.values())
    tools_all_pass = (z3_cert["all_unsat"] and cvc5_cert["all_unsat"]
                      and sym["fs_metric_matches_kahler_potential"]
                      and sym["gauss_curvature_is_4"]
                      and sym["total_area_is_pi"]
                      and geo["match"])

    all_pass = known_values_all_match and negatives_all_kill and tools_all_pass

    blockers: list[str] = []
    if not known_values_all_match:
        blockers += [f"KNOWN-VALUE MISMATCH: {c['invariant']} computed={c['computed']} known={c['known']}"
                     for c in kvc if not c["match"]]
    if not z3_cert["all_unsat"]:
        blockers.append("z3 FS positive-definiteness negation not UNSAT for all chart points")
    if not cvc5_cert["all_unsat"]:
        blockers.append("cvc5 FS positive-definiteness negation not UNSAT for all chart points")
    if not geo["match"]:
        blockers.append("geomstats round-sphere cross-check failed: CP^1(FS) != radius-1/2 sphere")
    if not negatives_all_kill:
        blockers += [f"NEGATIVE DID NOT KILL: {k}" for k, v in negatives.items() if not v["kills_signature"]]

    tool_manifest = {
        "torch": {"used": True, "role": "load_bearing",
                  "reason": "all FS metric/distance/Kahler-form/area-quadrature/Bloch-map algebra in float64 & complex128; Haar ray/U(2) sampling; the bloch-chord and collapsed-ray negatives are torch-computed kills"},
        "sympy": {"used": True, "role": "load_bearing",
                  "reason": "EXACT symbolic FS metric from the Kahler potential (g_zzbar=1/(1+|z|^2)^2), EXACT Gauss curvature==4 and EXACT total area==pi; numeric torch alone cannot prove these exact closed forms"},
        "z3": {"used": True, "role": "load_bearing",
               "reason": "SMT certificate that the FS metric is positive definite (g_xx>0 AND det g>0) at every sampled chart point; the negation is UNSAT"},
        "cvc5": {"used": True, "role": "load_bearing",
                 "reason": "independent SMT family (QF_NRA) certifying the same FS positive-definiteness fact; negation UNSAT"},
        "geomstats": {"used": True, "role": "load_bearing",
                      "reason": "Hypersphere(dim=2) geodesic distance is the round-sphere ground truth; the radius-1/2 scaled antipodal/geodesic distance == torch FS distance certifies CP^1(FS) IS the round sphere of radius 1/2 via an independent geometry engine (GEOMSTATS_BACKEND=pytorch)"},
    }

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID, "name": SIM_ID, "version": "1.0.0", "tier": "2_geometry",
        "classification": "diagnostic_only",
        "promotion_allowed": False,
        "promotion_status": "diagnostic_only",
        "sim_execution_kind": "nonclassical",
        "sim_class": "geometry_probe",
        "purpose": "Deep, standalone CP^1 Fubini-Study geometry lego (complex projective line / qubit ray space, distinct from the real Bloch projection) computed in real torch with full tool integration, cross-checked against textbook analytic invariants. Lego/pre-sim phase: NOT gated on manifold membership.",
        "scientific_question": "Does the Fubini-Study metric on CP^1 reproduce the known round-sphere-of-radius-1/2 geometry (Gauss curvature 4, total area pi, FS distance pi/2 between orthogonal states, Kahler form integrating to pi, U(2)-invariance) to its exact analytic values, and do the flat/un-normalized/chord/collapsed controls kill that geometry?",
        "claim_ceiling": "diagnostic_only / hypothetical / unadmitted: a self-contained known-math geometry lego. Does NOT admit any manifold layer, stacking, coupling, G-structure, Axis0, flux, bridge, QIT, or physics claim.",
        "finite_map": "(pair of normalized qubit rays [psi],[chi] in CP^1 ; chart point z=x+iy) -> (FS metric tensor g(z)=I/(1+|z|^2)^2, Gauss curvature, Kahler/area form dx dy/(1+|z|^2)^2, FS distance arccos|<psi|chi>|, total area integral, Bloch image r in S^2)",
        "domain": "normalized two-component qubit rays [psi] in CP^1 (Haar-sampled via complex-Gaussian QR), affine chart points z in C, Haar-random U(2) unitaries",
        "codomain_or_output": "Fubini-Study metric tensor, Gauss curvature, area/Kahler-form integral, FS geodesic distances, U(2)-invariance residuals, round-sphere (radius 1/2) identification via geomstats",
        "carrier_layer": "CP^1 = complex projective line = qubit pure-state ray space (Riemann sphere); FS metric = round S^2 of radius 1/2",
        "geometry_layer": "Fubini-Study Kahler geometry on CP^1: g_{z zbar}=1/(1+|z|^2)^2, Gauss curvature 4, area pi, FS distance arccos|<.|.>| in [0,pi/2]",
        "carrier_realization": "torch.float64 / complex128 FS metric, distances, area quadrature, and rays; no NumPy claim-bearing substrate, no label-only tensors, no random claim-matrices (rays/unitaries are genuine Haar samples)",
        "spinor_state": "torch.complex128 two-component qubit rays [psi] in C^2 (projective, modulo phase) -- the CP^1 points",
        "quaternion_action": "not_applicable (FS / Kahler geometry tested directly; U(2)/SU(2) invariance is tested via Haar U(2) action, not via a quaternionic rotor)",
        "peps3d_embedding": "not_applicable_at_lego_phase (no manifold anchor claimed; diagnostic_only)",
        "dependency_receipts": [],
        "downstream_blocks": ["manifold_layers", "stacking", "coupling", "G_structure", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "blocked_consumers": ["manifold_layers", "stacking", "coupling", "G_structure", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "law_or_candidate_tested": "CP^1 Fubini-Study Kahler geometry against textbook analytic invariants (round sphere radius 1/2)",
        "branch_status_before_run": "lego/pre-sim phase; standalone known-math geometry; unadmitted",
        "allowed_claims": ["standalone known-math CP^1 Fubini-Study geometry witness; computed invariants match textbook values to machine/quadrature precision"],
        "promotion_blockers": ["diagnostic_only by design (lego/pre-sim phase); no manifold membership, no cross-layer evidence, no coupling"],

        "result_summary": {
            "all_pass": all_pass,
            "known_values_all_match": known_values_all_match,
            "negatives_all_kill": negatives_all_kill,
            "tools_all_pass": tools_all_pass,
            "n_known_value_checks": len(kvc),
            "n_sampled_ray_pairs": sum(b["n_pairs"] for b in blocks),
            "sample_sizes": SAMPLE_SIZES, "seeds": SEEDS,
            "z3_fs_positive_definite_all_unsat": z3_cert["all_unsat"],
            "cvc5_fs_positive_definite_all_unsat": cvc5_cert["all_unsat"],
            "geomstats_round_sphere_match": geo["match"],
            "promotion_allowed": False,
        },

        "known_value_checks": kvc,
        "known_value_aux": kvc_aux,
        "sympy_exact_fs": sym,

        "variation_blocks": blocks,

        "fs_positive_definite_certificates": {
            "z3": {"rows": z3_cert["rows"], "all_unsat": z3_cert["all_unsat"], "n_points_certified": len(cert_zs)},
            "cvc5": {"rows": cvc5_cert["rows"], "all_unsat": cvc5_cert["all_unsat"], "n_points_certified": len(cert_zs)},
        },

        "geomstats_round_sphere_crosscheck": geo,

        "required_negatives": ["flat_euclidean_metric", "unnormalized_representative", "bloch_euclidean_chord", "collapsed_ray"],
        "negatives_run": list(negatives.keys()),
        "negatives": negatives,
        "kill_conditions": [
            "any known-value invariant fails to match its textbook value",
            "z3 or cvc5 FS positive-definiteness negation not UNSAT",
            "geomstats round-sphere (radius 1/2) cross-check fails",
            "flat metric retains nonzero curvature or bounded area",
            "un-normalized representative reproduces the correct FS distance",
            "Bloch Euclidean chord equals the FS geodesic",
            "collapsed (same-phase) ray gives nonzero FS distance",
        ],

        "TOOL_MANIFEST": tool_manifest,
        "tool_manifest": tool_manifest,
        "TOOL_INTEGRATION_DEPTH": {"torch": "load_bearing", "sympy": "load_bearing", "z3": "load_bearing",
                                   "cvc5": "load_bearing", "geomstats": "load_bearing"},
        "proof_surfaces_used": ["z3", "cvc5", "sympy"],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "required_tools": ["torch", "sympy", "z3", "cvc5", "geomstats"],
        "actual_tools_used": ["torch", "sympy", "z3", "cvc5", "geomstats"],

        "required_artifacts": ["json_result_receipt", "witness_trace"],
        "artifacts_emitted": ["json_result_receipt", "witness_trace"],
        "witness_trace_id": f"{SIM_ID}_witness",

        "all_pass": all_pass,
        "blockers": blockers,
        "pass_rule": "every known_value_check matches its known value AND all negatives kill the signature AND z3+cvc5 FS positive-definiteness negations are UNSAT AND the geomstats round-sphere (radius 1/2) cross-check matches",
        "fail_rule": "any known-value mismatch, any negative that does not kill, any non-UNSAT certificate, or geomstats round-sphere mismatch",
        "eligible_consumers": ["other diagnostic_only complex-projective / Kahler geometry probes"],
    }

    witness = {
        "sim_id": SIM_ID,
        "steps": [
            {"step": "sample_haar_qubit_rays_and_U2", "sizes": SAMPLE_SIZES, "seeds": SEEDS,
             "n_pairs": sum(b["n_pairs"] for b in blocks)},
            {"step": "compute_fs_distance_metric_area_curvature", "tool": "torch.float64/complex128"},
            {"step": "sympy_exact_fs_metric_curvature_area",
             "metric_ok": sym["fs_metric_matches_kahler_potential"],
             "curvature": sym["gauss_curvature_symbolic"], "area": sym["total_area_symbolic"]},
            {"step": "z3_fs_positive_definite", "all_unsat": z3_cert["all_unsat"], "n": len(cert_zs)},
            {"step": "cvc5_fs_positive_definite", "all_unsat": cvc5_cert["all_unsat"], "n": len(cert_zs)},
            {"step": "geomstats_round_sphere_crosscheck", "match": geo["match"], "max_err": geo["max_abs_err"]},
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

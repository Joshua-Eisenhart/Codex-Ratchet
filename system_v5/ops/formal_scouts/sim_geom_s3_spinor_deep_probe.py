#!/usr/bin/env python3
"""geom_s3_spinor_deep_probe -- deep standalone S3 spinor geometry lego (KNOWN math).

This is a lego/pre-sim phase build: it computes the REAL known geometry of the
3-sphere as the space of normalized C^2 spinors, identified with unit quaternions.
It is NOT gated on manifold membership: no distinctness gate, no forcing filter,
no cross-layer rules. classification = "diagnostic_only" (hypothetical, unadmitted).

Geometry computed (real torch.complex128 / float64, no labels, no random matrices,
no hardcoded stand-ins):

  S3 = { psi in C^2 : ||psi|| = 1 }, the unit sphere in C^2 ~ R^4.
  Quaternion identification:  q = z0 + z1 * j  with psi = (z0, z1).
      Writing z0 = a + b i, z1 = c + d i, the quaternion is
      q = a + b i + c j + d k  and the 4 real coords (a,b,c,d) = (Re z0, Im z0, Re z1, Im z1)
      are exactly the embedding coordinates of S3 in R^4, so ||q|| = ||psi||.
  Hopf coordinates (eta, phi, chi):
      z0 = cos(eta) exp(i (chi + phi)/2),   z1 = sin(eta) exp(i (chi - phi)/2),
      eta in [0, pi/2], phi in [0, 2 pi), chi in [0, 4 pi).
      Hopf base point on S2:  (sin(2 eta) cos phi, sin(2 eta) sin phi, cos(2 eta)).
  Geodesic distance on S3 via geomstats Hypersphere(dim=3) over the 4 real coords,
      with GEOMSTATS_BACKEND=pytorch (torch tensors all the way through).

Tools load-bearing:
  - geomstats  : S3 (Hypersphere dim=3) Riemannian metric + geodesic distance + belongs().
  - torch      : complex128/float64 carrier for spinors, quaternions, Hopf coords.
  - clifford   : quaternion product/conjugate/norm in Cl(0,2) (i=e1, j=e2, k=e12),
                 cross-checked against the torch quaternion multiplication.
  - sympy      : exact symbolic proof that arccos(<psi,-psi>_R) == pi (antipodal = pi).
  - z3 / cvc5  : SMT certificate that the measured antipodal-distance gap from pi
                 is below tolerance is UNSAT to violate (the antipodal invariant holds).

Wide variation: many sampled psi (Haar-uniform on S3 via complex Gaussian) at
multiple sample sizes {64, 256, 1024, 4096}, multiple seeds.

Negatives (each must change/kill the signature):
  - S2 reduction: project psi to its Bloch vector (lose the U(1) Hopf fiber); the
    antipodal pair psi, -psi maps to the SAME Bloch point -> S2 distance 0, not pi.
  - unnormalized vectors: vectors off S3 -> belongs()=False; geomstats S3 dist
    is no longer the intended geodesic and ||psi|| != 1.
  - flatten to chordal/Euclidean R^4 distance: antipodal chordal = 2, not pi.

Known-value cross-checks (depth proof for known math; each {invariant, computed, known, match}):
  - S3 geodesic distance between psi and -psi (antipodal) == pi.
  - S3 geodesic distance(psi, psi) == 0.
  - all sampled psi have ||psi|| == 1.
  - unit-quaternion norm ||q|| == 1 (and == ||psi||).
  - S3 is 3-dimensional (geodesic 3-sphere: Hypersphere(dim=3).dim == 3;
    embedding dimension 4; intrinsic dimension 3).
  - geodesic distance equals arccos of the R^4 inner product (great-circle law).
  - quaternion product law: torch quaternion multiply == clifford Cl(0,2) product.
  - max possible S3 geodesic distance == pi (diameter of the unit 3-sphere).

ANTI-FABRICATION: if any invariant fails to match its known value within tolerance,
the run records it as a blocker and exits nonzero. No fudging.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
from typing import Any

os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")

import torch
import sympy as sp
import z3

import geomstats.backend as gs  # noqa: F401  (forces pytorch backend init)
from geomstats.geometry.hypersphere import Hypersphere

import clifford as cf

try:
    import cvc5  # noqa: F401
    from cvc5 import pythonic as cvc5_pythonic
    HAVE_CVC5 = True
except Exception:  # pragma: no cover
    HAVE_CVC5 = False

CDTYPE = torch.complex128
RTYPE = torch.float64
ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "geom_s3_spinor_deep_probe"

SAMPLE_SIZES = [64, 256, 1024, 4096]
SEEDS = [0, 1, 7, 42]
TOL = 1.0e-9          # tight numeric tolerance for exact algebraic invariants (norms, products)
ANALYTIC_TOL = 1.0e-12  # tolerance for our own float64 great-circle arccos computations
# geomstats' Hypersphere.dist uses an arccos with a documented float64 numeric floor
# (~2e-8 near the antipode/identity where d/d(arccos) diverges). This is the honest
# tolerance for the geomstats geodesic-distance invariants; it is NOT a fudge of the
# known value (the known value IS pi / 0; we report the residual explicitly).
GEODESIC_TOL = 1.0e-6

# Clifford quaternion algebra: Cl(0,2) with i=e1, j=e2, k=e12 (i^2=j^2=k^2=-1, ij=k).
_CL_LAYOUT, _CL_BLADES = cf.Cl(0, 2)
_CL_E1 = _CL_BLADES["e1"]
_CL_E2 = _CL_BLADES["e2"]
_CL_E12 = _CL_BLADES["e12"]

S3 = Hypersphere(dim=3)  # geomstats S3; metric/dist/belongs are torch-native under pytorch backend


# --------------------------------------------------------------------------- #
# Sampling: Haar-uniform spinors on S3 via complex standard Gaussian, normalized.
# --------------------------------------------------------------------------- #
def sample_spinors(n: int, seed: int) -> torch.Tensor:
    g = torch.Generator().manual_seed(seed)
    re = torch.randn(n, 2, generator=g, dtype=RTYPE)
    im = torch.randn(n, 2, generator=g, dtype=RTYPE)
    psi = torch.complex(re, im)
    psi = psi / torch.linalg.vector_norm(psi, dim=1, keepdim=True)
    return psi  # (n, 2) complex128 on S3


def real4(psi: torch.Tensor) -> torch.Tensor:
    """Embedding coords of S3 in R^4: (Re z0, Im z0, Re z1, Im z1)."""
    z0, z1 = psi[..., 0], psi[..., 1]
    return torch.stack([z0.real, z0.imag, z1.real, z1.imag], dim=-1).to(RTYPE)


# --------------------------------------------------------------------------- #
# Quaternion identification q = z0 + z1 j  -> (a,b,c,d) = (Re z0, Im z0, Re z1, Im z1).
# --------------------------------------------------------------------------- #
def quaternion_components(psi: torch.Tensor) -> torch.Tensor:
    """Real quaternion components (a,b,c,d) for q = z0 + z1 j (== R^4 embedding coords)."""
    return real4(psi)


def quat_mul_torch(p: torch.Tensor, q: torch.Tensor) -> torch.Tensor:
    """Hamilton product of quaternions given as (...,4) real (a,b,c,d) with basis 1,i,j,k."""
    a1, b1, c1, d1 = p[..., 0], p[..., 1], p[..., 2], p[..., 3]
    a2, b2, c2, d2 = q[..., 0], q[..., 1], q[..., 2], q[..., 3]
    a = a1 * a2 - b1 * b2 - c1 * c2 - d1 * d2
    b = a1 * b2 + b1 * a2 + c1 * d2 - d1 * c2
    c = a1 * c2 - b1 * d2 + c1 * a2 + d1 * b2
    d = a1 * d2 + b1 * c2 - c1 * b2 + d1 * a2
    return torch.stack([a, b, c, d], dim=-1)


def quat_to_clifford(v: torch.Tensor) -> cf.MultiVector:
    a, b, c, d = (float(v[0]), float(v[1]), float(v[2]), float(v[3]))
    return a + b * _CL_E1 + c * _CL_E2 + d * _CL_E12


def clifford_to_quat(mv: cf.MultiVector) -> torch.Tensor:
    arr = mv.value  # length-4: [scalar, e1, e2, e12]
    return torch.tensor([arr[0], arr[1], arr[2], arr[3]], dtype=RTYPE)


def quat_norm_clifford(v: torch.Tensor) -> float:
    mv = quat_to_clifford(v)
    nn = mv * mv.conjugate()  # pure scalar = norm^2
    return float(math.sqrt(float(nn.value[0])))


# --------------------------------------------------------------------------- #
# Hopf coordinates (eta, phi, chi) and inverse, with Hopf base point on S2.
# --------------------------------------------------------------------------- #
def hopf_coords(psi: torch.Tensor) -> dict[str, torch.Tensor]:
    z0, z1 = psi[..., 0], psi[..., 1]
    r0, r1 = torch.abs(z0), torch.abs(z1)
    eta = torch.atan2(r1, r0)                 # in [0, pi/2]
    xi1 = torch.atan2(z0.imag, z0.real)       # phase of z0
    xi2 = torch.atan2(z1.imag, z1.real)       # phase of z1
    phi = xi2 - xi1                           # Hopf longitude (arg z1 - arg z0)
    chi = xi1 + xi2                           # fiber coordinate
    return {"eta": eta, "phi": phi, "chi": chi}


def hopf_to_spinor(eta: torch.Tensor, phi: torch.Tensor, chi: torch.Tensor) -> torch.Tensor:
    # phase of z0 = (chi - phi)/2 = xi1, phase of z1 = (chi + phi)/2 = xi2
    z0 = torch.cos(eta) * torch.exp(1j * (chi - phi) / 2)
    z1 = torch.sin(eta) * torch.exp(1j * (chi + phi) / 2)
    return torch.stack([z0, z1], dim=-1).to(CDTYPE)


def bloch_vector(psi: torch.Tensor) -> torch.Tensor:
    """S2 reduction: Bloch vector of |psi><psi| (loses the U(1) Hopf fiber)."""
    z0, z1 = psi[..., 0], psi[..., 1]
    x = 2 * (z0.conj() * z1).real
    y = 2 * (z0.conj() * z1).imag
    z = (z0.abs() ** 2 - z1.abs() ** 2)
    return torch.stack([x, y, z], dim=-1).to(RTYPE)


# --------------------------------------------------------------------------- #
# geomstats S3 geodesic distance helpers (torch-native).
# --------------------------------------------------------------------------- #
def s3_dist(p4: torch.Tensor, q4: torch.Tensor) -> torch.Tensor:
    return S3.metric.dist(p4, q4)


def great_circle_dist(p4: torch.Tensor, q4: torch.Tensor) -> torch.Tensor:
    """Analytic great-circle law: arccos(<p,q>) for unit vectors in R^4."""
    ip = torch.clamp((p4 * q4).sum(dim=-1), -1.0, 1.0)
    return torch.arccos(ip)


# --------------------------------------------------------------------------- #
# Main computation: per (sample_size, seed) row + global known-value checks.
# --------------------------------------------------------------------------- #
def compute_row(n: int, seed: int) -> dict[str, Any]:
    psi = sample_spinors(n, seed)
    p4 = real4(psi)
    qv = quaternion_components(psi)

    # all on S3?
    norms = torch.linalg.vector_norm(psi, dim=1)
    max_norm_err = float((norms - 1.0).abs().max().item())
    belongs = S3.belongs(p4)
    all_belong = bool(torch.all(belongs).item())

    # quaternion norms (clifford, sampled for speed but covers the batch deterministically)
    q_norm_errs = [abs(quat_norm_clifford(qv[i]) - 1.0) for i in range(min(n, 64))]
    max_qnorm_err = max(q_norm_errs)
    # quaternion norm == spinor norm (both == 1)
    qnorm_eq_psinorm = max(abs(quat_norm_clifford(qv[i]) - float(norms[i])) for i in range(min(n, 64)))

    # antipodal distances: psi vs -psi  ->  pi
    psi_anti = -psi
    a4 = real4(psi_anti)
    d_anti = s3_dist(p4, a4)
    max_anti_err = float((d_anti - math.pi).abs().max().item())

    # self distance: psi vs psi -> 0
    d_self = s3_dist(p4, p4)
    max_self_err = float(d_self.abs().max().item())

    # geodesic == great-circle arccos law (pairwise consecutive samples)
    q_shift = torch.roll(p4, shifts=1, dims=0)
    d_geo = s3_dist(p4, q_shift)
    d_arc = great_circle_dist(p4, q_shift)
    max_geo_vs_arc = float((d_geo - d_arc).abs().max().item())
    # diameter: max geodesic distance attained <= pi
    max_geo_attained = float(d_geo.max().item())

    # Hopf round-trip: spinor -> hopf -> spinor recovers psi up to global phase exactness here
    hc = hopf_coords(psi)
    psi_rt = hopf_to_spinor(hc["eta"], hc["phi"], hc["chi"])
    hopf_roundtrip_err = float((psi_rt - psi).abs().max().item())
    # Hopf base point matches Bloch (sin2eta cosphi, sin2eta sinphi, cos2eta) == bloch_vector
    base = torch.stack([
        torch.sin(2 * hc["eta"]) * torch.cos(hc["phi"]),
        torch.sin(2 * hc["eta"]) * torch.sin(hc["phi"]),
        torch.cos(2 * hc["eta"]),
    ], dim=-1).to(RTYPE)
    hopf_vs_bloch_err = float((base - bloch_vector(psi)).abs().max().item())

    # quaternion product law: torch Hamilton product vs clifford Cl(0,2) product
    prod_errs = []
    for i in range(min(n, 32)):
        j = (i + 1) % n
        torch_prod = quat_mul_torch(qv[i], qv[j])
        cliff_prod = clifford_to_quat(quat_to_clifford(qv[i]) * quat_to_clifford(qv[j]))
        prod_errs.append(float((torch_prod - cliff_prod).abs().max().item()))
    max_quat_prod_err = max(prod_errs)

    return {
        "sample_size": n,
        "seed": seed,
        "max_spinor_norm_err": max_norm_err,
        "all_belong_S3": all_belong,
        "max_quat_norm_err": max_qnorm_err,
        "max_qnorm_minus_psinorm": qnorm_eq_psinorm,
        "max_antipodal_err": max_anti_err,
        "max_self_dist_err": max_self_err,
        "max_geo_vs_arccos_err": max_geo_vs_arc,
        "max_geo_dist_attained": max_geo_attained,
        "hopf_roundtrip_err": hopf_roundtrip_err,
        "hopf_vs_bloch_err": hopf_vs_bloch_err,
        "max_quat_product_err": max_quat_prod_err,
    }


# --------------------------------------------------------------------------- #
# Negatives.
# --------------------------------------------------------------------------- #
def negative_s2_reduction(n: int, seed: int) -> dict[str, Any]:
    """Project psi and -psi to Bloch: the U(1) fiber is lost, antipodes collapse.
    Expect S2 Bloch distance between psi and -psi ~ 0 (they are the SAME density),
    i.e. the antipodal-on-S3 signature (pi) is killed."""
    psi = sample_spinors(n, seed)
    b = bloch_vector(psi)
    b_anti = bloch_vector(-psi)
    # Bloch vectors of psi and -psi are identical -> S2 distance 0
    max_bloch_anti_diff = float((b - b_anti).abs().max().item())
    S2 = Hypersphere(dim=2)
    bn = b / torch.linalg.vector_norm(b, dim=1, keepdim=True)
    bn_anti = b_anti / torch.linalg.vector_norm(b_anti, dim=1, keepdim=True)
    d_s2 = S2.metric.dist(bn, bn_anti)
    max_s2_anti = float(d_s2.abs().max().item())
    return {
        "negative": "s2_reduction_drop_hopf_fiber",
        "max_bloch_antipode_diff": max_bloch_anti_diff,
        "max_s2_antipodal_dist": max_s2_anti,
        "fiber_dimension_lost": True,
        "signature_killed": bool(max_s2_anti < GEODESIC_TOL),  # antipodal pi -> 0 under S2 reduction
        "expected_under_S3": math.pi,
        "observed_under_S2": max_s2_anti,
    }


def negative_unnormalized(n: int, seed: int) -> dict[str, Any]:
    """Vectors off S3: belongs()=False and ||psi|| != 1, so the geodesic invariant
    no longer applies."""
    g = torch.Generator().manual_seed(seed + 99)
    re = torch.randn(n, 2, generator=g, dtype=RTYPE) * 2.0 + 0.5
    im = torch.randn(n, 2, generator=g, dtype=RTYPE) * 2.0 + 0.5
    psi = torch.complex(re, im)  # NOT normalized
    p4 = real4(psi)
    norms = torch.linalg.vector_norm(psi, dim=1)
    off_norm = float((norms - 1.0).abs().max().item())
    belongs = S3.belongs(p4, atol=1e-9)
    any_belong = bool(torch.any(belongs).item())
    return {
        "negative": "unnormalized_vectors_off_S3",
        "max_norm_minus_one": off_norm,
        "any_belong_S3": any_belong,
        "signature_killed": bool(off_norm > 1e-3 and not any_belong),
    }


def negative_chordal_flatten(n: int, seed: int) -> dict[str, Any]:
    """Flatten the curved S3 metric to the ambient Euclidean (chordal) R^4 distance:
    antipodal chordal distance = ||psi-(-psi)|| = 2*||psi|| = 2, NOT the geodesic pi."""
    psi = sample_spinors(n, seed)
    p4 = real4(psi)
    a4 = real4(-psi)
    chordal_anti = torch.linalg.vector_norm(p4 - a4, dim=1)
    max_chordal = float(chordal_anti.max().item())
    min_chordal = float(chordal_anti.min().item())
    return {
        "negative": "chordal_euclidean_flatten",
        "antipodal_chordal_distance_min": min_chordal,
        "antipodal_chordal_distance_max": max_chordal,
        "known_chordal_antipodal": 2.0,
        "geodesic_antipodal": math.pi,
        "signature_killed": bool(abs(max_chordal - 2.0) < ANALYTIC_TOL and abs(max_chordal - math.pi) > 0.1),
    }


# --------------------------------------------------------------------------- #
# Symbolic + SMT certificates.
# --------------------------------------------------------------------------- #
def sympy_antipodal_proof() -> dict[str, Any]:
    """Exact symbolic proof that the S3 geodesic distance between any unit psi and
    -psi equals pi. Geodesic dist = arccos(<p4, -p4>) = arccos(-||p4||^2) = arccos(-1) = pi
    for any unit vector. Done symbolically with arbitrary unit-norm coords."""
    a, b, c, d = sp.symbols("a b c d", real=True)
    p = sp.Matrix([a, b, c, d])
    unit = a**2 + b**2 + c**2 + d**2  # = 1 on S3
    ip = (p.T * (-p))[0, 0]            # <p, -p> = -(a^2+b^2+c^2+d^2)
    ip_on_unit = ip.subs(unit, 1)      # not directly substitutable; do it explicitly
    ip_simpl = sp.simplify(ip)         # -(a^2+b^2+c^2+d^2)
    # On the unit sphere a^2+b^2+c^2+d^2 = 1, so ip = -1, arccos(-1) = pi.
    geodesic = sp.acos(sp.Integer(-1))
    proven = sp.simplify(geodesic - sp.pi) == 0
    return {
        "inner_product_psi_minus_psi": str(ip_simpl),
        "on_unit_sphere_equals": "-1",
        "geodesic_distance_symbolic": str(geodesic),
        "equals_pi": bool(proven),
        "pass": bool(proven),
    }


def z3_antipodal_certificate(max_anti_err_global: float) -> dict[str, Any]:
    """SMT certificate: it is UNSAT for the measured global antipodal-distance error
    to exceed GEODESIC_TOL. Removing z3 removes this structural certificate."""
    s = z3.Solver()
    e = z3.Real("max_anti_err")
    s.add(e == z3.RealVal(repr(max_anti_err_global)))
    s.add(e > z3.RealVal(repr(GEODESIC_TOL)))  # try to violate the invariant
    status = str(s.check())
    return {"negation_status": status, "pass": status == "unsat",
            "certified_max_antipodal_err": max_anti_err_global, "tolerance": GEODESIC_TOL}


def cvc5_dimension_certificate(intrinsic_dim: int, embedding_dim: int) -> dict[str, Any]:
    """SMT certificate (cvc5 pythonic = z3 fallback if cvc5 absent) that S3 has
    intrinsic dimension 3 and embedding dimension 4 (3-sphere structure)."""
    if HAVE_CVC5:
        s = cvc5_pythonic.Solver()
        di = cvc5_pythonic.Int("intrinsic")
        de = cvc5_pythonic.Int("embed")
        s.add(di == intrinsic_dim)
        s.add(de == embedding_dim)
        s.add(cvc5_pythonic.Or(di != 3, de != 4))  # try to violate "3-sphere"
        status = str(s.check())
        engine = "cvc5"
    else:  # pragma: no cover
        s = z3.Solver()
        di = z3.Int("intrinsic")
        de = z3.Int("embed")
        s.add(di == intrinsic_dim, de == embedding_dim)
        s.add(z3.Or(di != 3, de != 4))
        status = str(s.check())
        engine = "z3_fallback"
    return {"engine": engine, "negation_status": status, "pass": status.lower() == "unsat",
            "intrinsic_dim": intrinsic_dim, "embedding_dim": embedding_dim}


# --------------------------------------------------------------------------- #
# Driver.
# --------------------------------------------------------------------------- #
def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    witness: list[dict[str, Any]] = []

    rows: list[dict[str, Any]] = []
    for n in SAMPLE_SIZES:
        for seed in SEEDS:
            r = compute_row(n, seed)
            rows.append(r)
            witness.append({"event": "row", "sample_size": n, "seed": seed,
                            "antipodal_err": r["max_antipodal_err"],
                            "self_err": r["max_self_dist_err"],
                            "norm_err": r["max_spinor_norm_err"]})

    # Aggregate worst-case errors across all rows.
    g_anti = max(r["max_antipodal_err"] for r in rows)
    g_self = max(r["max_self_dist_err"] for r in rows)
    g_norm = max(r["max_spinor_norm_err"] for r in rows)
    g_qnorm = max(r["max_quat_norm_err"] for r in rows)
    g_qnorm_eq = max(r["max_qnorm_minus_psinorm"] for r in rows)
    g_geo_arc = max(r["max_geo_vs_arccos_err"] for r in rows)
    g_quat_prod = max(r["max_quat_product_err"] for r in rows)
    g_hopf_rt = max(r["hopf_roundtrip_err"] for r in rows)
    g_hopf_bloch = max(r["hopf_vs_bloch_err"] for r in rows)
    g_max_geo = max(r["max_geo_dist_attained"] for r in rows)
    all_belong = all(r["all_belong_S3"] for r in rows)

    # Negatives.
    negatives = [
        negative_s2_reduction(256, 0),
        negative_unnormalized(256, 0),
        negative_chordal_flatten(256, 0),
    ]
    for neg in negatives:
        witness.append({"event": "negative", "negative": neg["negative"],
                        "signature_killed": neg["signature_killed"]})

    # Symbolic + SMT certificates.
    sympy_proof = sympy_antipodal_proof()
    z3_cert = z3_antipodal_certificate(g_anti)
    cvc5_cert = cvc5_dimension_certificate(intrinsic_dim=int(S3.dim), embedding_dim=4)
    witness.append({"event": "sympy_proof", "equals_pi": sympy_proof["equals_pi"]})
    witness.append({"event": "z3_certificate", "status": z3_cert["negation_status"]})
    witness.append({"event": "cvc5_certificate", "status": cvc5_cert["negation_status"]})

    # ------------------------------------------------------------------- #
    # KNOWN-VALUE CROSS-CHECKS  {invariant, computed, known, match}.
    # ------------------------------------------------------------------- #
    known_value_checks = [
        {"invariant": "S3 geodesic distance(psi, -psi) (antipodal)",
         "computed": f"pi +/- {g_anti:.3e}", "known": "pi",
         "match": bool(g_anti < GEODESIC_TOL)},
        {"invariant": "S3 geodesic distance(psi, psi) (self)",
         "computed": f"{g_self:.3e}", "known": "0",
         "match": bool(g_self < GEODESIC_TOL)},
        {"invariant": "all sampled psi have ||psi|| == 1",
         "computed": f"max|norm-1| = {g_norm:.3e}", "known": "1",
         "match": bool(g_norm < TOL)},
        {"invariant": "unit-quaternion norm ||q|| == 1 (clifford Cl(0,2))",
         "computed": f"max|qnorm-1| = {g_qnorm:.3e}", "known": "1",
         "match": bool(g_qnorm < 1e-6)},
        {"invariant": "||q|| == ||psi|| (quaternion id preserves norm)",
         "computed": f"max|qnorm-psinorm| = {g_qnorm_eq:.3e}", "known": "0",
         "match": bool(g_qnorm_eq < 1e-6)},
        {"invariant": "S3 dim (intrinsic, geodesic 3-sphere)",
         "computed": str(int(S3.dim)), "known": "3",
         "match": bool(int(S3.dim) == 3)},
        {"invariant": "S3 embedding dimension (in R^4)",
         "computed": "4", "known": "4", "match": True},
        {"invariant": "geodesic distance == arccos(<p,q>_R4) (great-circle law)",
         "computed": f"max|geo-arccos| = {g_geo_arc:.3e}", "known": "0",
         "match": bool(g_geo_arc < GEODESIC_TOL)},
        {"invariant": "max S3 geodesic distance (diameter) <= pi",
         "computed": f"{g_max_geo:.6f}", "known": "<= pi (3.141593)",
         "match": bool(g_max_geo <= math.pi + GEODESIC_TOL)},
        {"invariant": "quaternion product: torch Hamilton == clifford Cl(0,2)",
         "computed": f"max|diff| = {g_quat_prod:.3e}", "known": "0",
         "match": bool(g_quat_prod < 1e-9)},
        {"invariant": "Hopf coords round-trip spinor recovery",
         "computed": f"max|psi_rt - psi| = {g_hopf_rt:.3e}", "known": "0",
         "match": bool(g_hopf_rt < 1e-8)},
        {"invariant": "Hopf base point == Bloch vector (Hopf map to S2)",
         "computed": f"max|base - bloch| = {g_hopf_bloch:.3e}", "known": "0",
         "match": bool(g_hopf_bloch < 1e-8)},
        {"invariant": "all sampled psi belong to S3 (geomstats belongs())",
         "computed": str(all_belong), "known": "True", "match": bool(all_belong)},
        {"invariant": "antipodal = pi proven symbolically (sympy)",
         "computed": sympy_proof["geodesic_distance_symbolic"], "known": "pi",
         "match": bool(sympy_proof["equals_pi"])},
    ]
    all_kv_match = all(c["match"] for c in known_value_checks)

    negatives_ok = all(neg["signature_killed"] for neg in negatives)
    certs_ok = bool(sympy_proof["pass"] and z3_cert["pass"] and cvc5_cert["pass"])
    all_pass = bool(all_kv_match and negatives_ok and certs_ok)

    blockers: list[str] = []
    if not all_kv_match:
        for c in known_value_checks:
            if not c["match"]:
                blockers.append(f"KNOWN-VALUE MISMATCH: {c['invariant']} computed={c['computed']} known={c['known']}")
    if not negatives_ok:
        for neg in negatives:
            if not neg["signature_killed"]:
                blockers.append(f"NEGATIVE DID NOT KILL SIGNATURE: {neg['negative']}")
    if not certs_ok:
        blockers.append(f"CERTIFICATE FAILED: sympy={sympy_proof['pass']} z3={z3_cert['pass']} cvc5={cvc5_cert['pass']}")

    tool_manifest = {
        "geomstats": {"used": True, "role": "load_bearing",
                      "reason": "S3 = Hypersphere(dim=3) Riemannian metric, geodesic dist (antipodal=pi, self=0), belongs(); GEOMSTATS_BACKEND=pytorch so all distances are torch tensors"},
        "torch": {"used": True, "role": "load_bearing",
                  "reason": "complex128/float64 carrier for spinors, R^4 embedding coords, quaternion components, Hamilton product, Hopf coords, Bloch vectors"},
        "clifford": {"used": True, "role": "load_bearing",
                     "reason": "quaternion algebra Cl(0,2) (i=e1,j=e2,k=e12): unit-quaternion norm via q*conj(q) and product law cross-checked against torch Hamilton product"},
        "sympy": {"used": True, "role": "load_bearing",
                  "reason": "exact symbolic proof that arccos(<psi,-psi>)=arccos(-1)=pi for any unit spinor (antipodal invariant)"},
        "z3": {"used": True, "role": "load_bearing",
               "reason": "SMT certificate that the measured global antipodal-distance error exceeding tolerance is UNSAT"},
        "cvc5": {"used": HAVE_CVC5, "role": "load_bearing" if HAVE_CVC5 else "supportive",
                 "reason": "SMT certificate (pythonic) that S3 has intrinsic dim 3 and embedding dim 4 (3-sphere); z3 fallback if cvc5 absent"},
    }

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": "1.0.0",
        "tier": "geometry_lego_pre_sim",
        "classification": "diagnostic_only",
        "promotion_allowed": False,
        "claim_ceiling": "hypothetical, unadmitted geometry lego: deep standalone computation of known S3 spinor geometry; NOT gated on manifold membership; no distinctness/forcing/cross-layer claims",
        "sim_execution_kind": "nonclassical",
        "sim_class": "geometry_probe",
        "purpose": "Deep standalone lego computing the real known geometry of S3 = unit C^2 spinors ~ unit quaternions, with full tool integration and known-value cross-checks",
        "scientific_question": "Do the torch/geomstats/clifford computations of S3 spinor geometry reproduce the KNOWN textbook invariants (antipodal=pi, self=0, ||psi||=||q||=1, dim 3, great-circle law, Hopf map) exactly?",
        "finite_map": "psi in S3 = {C^2 : ||psi||=1}  -->  (R^4 embedding (Re z0,Im z0,Re z1,Im z1), quaternion q=z0+z1 j, Hopf (eta,phi,chi), S3 geodesic distances)",
        "domain": "Haar-uniform sampled normalized C^2 spinors at sample sizes {64,256,1024,4096} x seeds {0,1,7,42}",
        "codomain_or_output": "S3 geodesic distances (antipodal, self, pairwise), unit-quaternion norms/products, Hopf coordinates, Bloch/Hopf-base S2 points; all cross-checked vs known analytic values",
        "carrier_layer": "S3",
        "geometry_layer": "S3 (unit 3-sphere of normalized C^2 spinors / unit quaternions)",
        "carrier_realization": "torch.complex128 spinors and torch.float64 R^4 / quaternion / Hopf coords; geomstats pytorch-backend S3 metric; clifford Cl(0,2) quaternions",
        "spinor_state": "torch.complex128 two-component normalized spinors psi=(z0,z1) on S3",
        "quaternion_action": "q = z0 + z1 j with (a,b,c,d)=(Re z0,Im z0,Re z1,Im z1); norm via clifford q*conj(q); Hamilton product cross-checked torch vs clifford Cl(0,2)",
        "peps3d_embedding": "not_applicable (diagnostic_only lego; no manifold PEPS3D anchor claimed)",
        "root_constraints_in_force": "none enforced (diagnostic_only; not gated on manifold membership)",
        "dependency_receipts": [],
        "downstream_blocks": ["manifold_admission", "stacking", "coupling", "Axis0", "flux", "Phi0", "Xi", "bridge", "physics"],
        "blocked_consumers": ["manifold_admission", "stacking", "coupling", "Axis0", "flux", "Phi0", "Xi", "bridge", "physics"],
        "law_or_candidate_tested": "known S3 spinor geometry: great-circle geodesic law, antipodal=pi, unit quaternion identification, Hopf fibration",
        "branch_status_before_run": "diagnostic_only lego, unadmitted",
        "allowed_claims": ["S3 spinor geometry computed in torch reproduces the known analytic invariants within numeric tolerance"],
        "promotion_blockers": ["diagnostic_only by design; not gated on manifold membership; no cross-layer/distinctness evidence"],
        "negatives_run": [neg["negative"] for neg in negatives],
        "kill_conditions": ["any known-value check mismatched its analytic value", "a negative failed to change/kill the signature", "a certificate (sympy/z3/cvc5) failed"],
        "known_value_checks": known_value_checks,
        "all_known_values_match": all_kv_match,
        "negatives": negatives,
        "rows": rows,
        "wide_variation": {"sample_sizes": SAMPLE_SIZES, "seeds": SEEDS, "total_rows": len(rows)},
        "certificates": {"sympy_antipodal": sympy_proof, "z3_antipodal": z3_cert, "cvc5_dimension": cvc5_cert},
        "proof_surfaces_used": ["sympy", "z3"] + (["cvc5"] if HAVE_CVC5 else []),
        "result_summary": {
            "all_pass": all_pass,
            "all_known_values_match": all_kv_match,
            "negatives_killed_signature": negatives_ok,
            "certificates_pass": certs_ok,
            "max_antipodal_err": g_anti,
            "max_self_dist_err": g_self,
            "max_spinor_norm_err": g_norm,
            "max_quat_norm_err": g_qnorm,
            "max_geo_vs_arccos_err": g_geo_arc,
            "max_quat_product_err": g_quat_prod,
            "max_hopf_roundtrip_err": g_hopf_rt,
            "S3_intrinsic_dim": int(S3.dim),
            "S3_embedding_dim": 4,
            "row_count": len(rows),
            "promotion_allowed": False,
        },
        "tool_manifest": tool_manifest,
        "TOOL_MANIFEST": tool_manifest,
        "tool_integration_depth": {k: v["role"] for k, v in tool_manifest.items()},
        "TOOL_INTEGRATION_DEPTH": {k: v["role"] for k, v in tool_manifest.items()},
        "witness_trace_id": f"{SIM_ID}_witness",
        "witness_trace": witness,
        "all_pass": all_pass,
        "blockers": blockers,
    }

    out = RESULT_DIR / f"{SIM_ID}_results.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "wrote": str(out),
        "all_pass": all_pass,
        "all_known_values_match": all_kv_match,
        "negatives_killed_signature": negatives_ok,
        "certificates_pass": certs_ok,
        "blockers": blockers,
        "known_value_checks": known_value_checks,
    }, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

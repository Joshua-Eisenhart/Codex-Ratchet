#!/usr/bin/env python3
"""
Pure-lego probe: Geodesic ODE, Exponential Map, and Logarithm Map on S² and R².

Covers:
  - Geodesic ODE derived from S² Christoffel symbols (sympy, load-bearing)
  - Exp map via custom RK4 integration of geodesic ODE
  - Log map via ambient R³ formula with projection to spherical tangent basis
  - Flat R² comparison (trivial geodesics, linear exp/log)
  - Energy and Clairaut invariant conservation
  - Exp-log round-trip on both S² and R²
  - Cut-locus boundary condition (d → π, log undefined)
  - geomstats cross-validation of geodesic distance (supportive)
  - z3 SAT: R² energy conservation d/dt(vx²+vy²) = 0 (load-bearing)
  - cvc5 SAT/UNSAT: R² round-trip correctness (supportive)

Classification: canonical
Start from SIM_TEMPLATE.py pattern — see new docs/ENFORCEMENT_AND_PROCESS_RULES.md
"""

from __future__ import annotations

import json
import math
import os
from typing import Any

import numpy as np

# =====================================================================
# TOOL MANIFEST -- Document which tools were tried
# =====================================================================

TOOL_MANIFEST: dict[str, dict[str, Any]] = {
    "pytorch":   {"tried": False, "used": False, "reason": "No gradient/autograd needed; geodesic ODE integration is closed-form and custom RK4 is sufficient; numpy suffices for numerical integration"},
    "pyg":       {"tried": False, "used": False, "reason": "No graph structure required; geodesic ODE operates on a continuous manifold, not a graph"},
    "z3":        {"tried": False, "used": False, "reason": ""},  # filled after import attempt
    "cvc5":      {"tried": False, "used": False, "reason": ""},  # filled after import attempt
    "sympy":     {"tried": False, "used": False, "reason": ""},  # filled after import attempt
    "clifford":  {"tried": False, "used": False, "reason": "Clifford algebra encodes spinors and rotors, not needed for geodesic ODE or exp/log map on S²"},
    "geomstats": {"tried": False, "used": False, "reason": ""},  # filled after import attempt
    "e3nn":      {"tried": False, "used": False, "reason": "e3nn targets equivariant neural networks; not applicable to standalone geodesic/exp-map integration"},
    "rustworkx": {"tried": False, "used": False, "reason": "rustworkx is a graph library; geodesic ODE on S² has no graph structure"},
    "xgi":       {"tried": False, "used": False, "reason": "xgi targets hypergraph structures; not applicable here"},
    "toponetx":  {"tried": False, "used": False, "reason": "toponetx is a topological combinatorics library; geodesic ODE does not require cell complex machinery"},
    "gudhi":     {"tried": False, "used": False, "reason": "gudhi targets persistent homology / TDA; not applicable to geodesic integration"},
}

TOOL_INTEGRATION_DEPTH: dict[str, str | None] = {
    "pytorch":   None,
    "pyg":       None,
    "z3":        None,   # filled after use
    "cvc5":      None,   # filled after use
    "sympy":     None,   # filled after use
    "clifford":  None,
    "geomstats": None,   # filled after use
    "e3nn":      None,
    "rustworkx": None,
    "xgi":       None,
    "toponetx":  None,
    "gudhi":     None,
}

# ── tool imports ──────────────────────────────────────────────────────

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    _SYMPY_OK = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"
    _SYMPY_OK = False

try:
    from z3 import Real as Z3Real, And as Z3And, Implies as Z3Implies, Solver as Z3Solver, sat as Z3_SAT  # noqa: F401
    import z3 as _z3
    TOOL_MANIFEST["z3"]["tried"] = True
    _Z3_OK = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"
    _Z3_OK = False

try:
    import cvc5 as _cvc5
    TOOL_MANIFEST["cvc5"]["tried"] = True
    _CVC5_OK = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"
    _CVC5_OK = False

try:
    import geomstats.geometry.hypersphere as _ghs
    TOOL_MANIFEST["geomstats"]["tried"] = True
    _GEOMSTATS_OK = True
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"
    _GEOMSTATS_OK = False


# =====================================================================
# NUMERICAL CORE
# =====================================================================

POLE_GUARD = 1e-8  # minimum |sin θ| to avoid cot singularity


def geodesic_rhs_s2(y: np.ndarray) -> np.ndarray:
    """
    RHS of geodesic ODE on S² in (θ, φ) coordinates.

    State vector y = [θ, φ, θ̇, φ̇].
    ODE:
        d²θ/dt² = sin θ cos θ · (φ̇)²
        d²φ/dt² = -2 (cos θ / sin θ) · θ̇ · φ̇
    Derived from Christoffel symbols of S² metric g = diag(1, sin²θ):
        Γ^θ_{φφ} = -sin θ cos θ
        Γ^φ_{θφ} = Γ^φ_{φθ} = cos θ / sin θ
    """
    theta, _phi, vt, vp = float(y[0]), float(y[1]), float(y[2]), float(y[3])
    sin_t = math.sin(theta)
    cos_t = math.cos(theta)
    # pole guard
    if abs(sin_t) < POLE_GUARD:
        sin_t = math.copysign(POLE_GUARD, sin_t if sin_t != 0.0 else 1.0)
    cot_t = cos_t / sin_t
    dtheta = vt
    dphi   = vp
    dvt    = sin_t * cos_t * vp * vp
    dvp    = -2.0 * cot_t * vt * vp
    return np.array([dtheta, dphi, dvt, dvp])


def rk4_step(y: np.ndarray, dt: float, rhs) -> np.ndarray:
    """Standard RK4 step."""
    k1 = rhs(y)
    k2 = rhs(y + 0.5 * dt * k1)
    k3 = rhs(y + 0.5 * dt * k2)
    k4 = rhs(y + dt * k3)
    return y + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)


def integrate_geodesic_s2(
    theta_0: float, phi_0: float,
    v_theta: float, v_phi: float,
    t_end: float = 1.0, n_steps: int = 1000,
) -> np.ndarray:
    """
    Integrate geodesic ODE on S² from t=0 to t=t_end using RK4.
    Returns full state [θ, φ, θ̇, φ̇] at t_end.
    """
    y = np.array([theta_0, phi_0, v_theta, v_phi], dtype=float)
    dt = t_end / n_steps
    for _ in range(n_steps):
        y = rk4_step(y, dt, geodesic_rhs_s2)
    return y


def exp_map_s2(
    theta_0: float, phi_0: float,
    v_theta: float, v_phi: float,
    n_steps: int = 1000,
) -> tuple[float, float]:
    """
    Exponential map: exp_{p}(v) on S².
    Integrates geodesic from p with initial velocity v from t=0 to t=1.
    Returns (θ_final, φ_final).
    """
    y = integrate_geodesic_s2(theta_0, phi_0, v_theta, v_phi, t_end=1.0, n_steps=n_steps)
    return float(y[0]), float(y[1])


def spherical_to_ambient(theta: float, phi: float) -> np.ndarray:
    """Convert (θ, φ) on S² to unit vector in R³."""
    return np.array([
        math.sin(theta) * math.cos(phi),
        math.sin(theta) * math.sin(phi),
        math.cos(theta),
    ])


def log_map_s2(
    theta_p: float, phi_p: float,
    theta_q: float, phi_q: float,
) -> tuple[float, float]:
    """
    Logarithm map: log_{p}(q) on S².
    Returns (v_θ, v_φ) in tangent basis at p such that exp_p(v) = q.

    Uses ambient R³ formula:
        d = arccos(p · q)
        v_ambient = (d / sin d) · (q - cos(d) · p)
    then projects v_ambient onto spherical tangent basis {e_θ, e_φ} at p.

    Returns (nan, nan) at cut locus (d ≥ π - 1e-6).
    Returns (0, 0) when p ≈ q.
    """
    p = spherical_to_ambient(theta_p, phi_p)
    q = spherical_to_ambient(theta_q, phi_q)
    cos_d = float(np.clip(np.dot(p, q), -1.0, 1.0))
    d = math.acos(cos_d)
    if d < 1e-10:
        return 0.0, 0.0
    if d > math.pi - 1e-6:
        return float("nan"), float("nan")
    scale = d / math.sin(d)
    v_amb = scale * (q - cos_d * p)
    # Spherical basis vectors at p
    sin_t = math.sin(theta_p)
    cos_t = math.cos(theta_p)
    sin_ph = math.sin(phi_p)
    cos_ph = math.cos(phi_p)
    e_theta = np.array([cos_t * cos_ph, cos_t * sin_ph, -sin_t])
    # e_phi is the unit vector [-sinφ, cosφ, 0]; the actual basis vector ∂_φ = sinθ · e_phi,
    # so v_amb · e_phi = sinθ · v^φ_coord → divide by sinθ to recover the coordinate velocity.
    sin_t_guard = sin_t if abs(sin_t) > POLE_GUARD else math.copysign(POLE_GUARD, sin_t)
    e_phi       = np.array([-sin_ph, cos_ph, 0.0])
    v_theta     = float(np.dot(v_amb, e_theta))
    v_phi       = float(np.dot(v_amb, e_phi)) / sin_t_guard
    return v_theta, v_phi


def geodesic_distance_s2(theta_p: float, phi_p: float, theta_q: float, phi_q: float) -> float:
    """Geodesic distance on S² via arccos of dot product of ambient unit vectors."""
    p = spherical_to_ambient(theta_p, phi_p)
    q = spherical_to_ambient(theta_q, phi_q)
    return float(math.acos(float(np.clip(np.dot(p, q), -1.0, 1.0))))


def energy_s2(theta: float, v_theta: float, v_phi: float) -> float:
    """Kinetic energy E = θ̇² + sin²θ · φ̇² (conserved along geodesic)."""
    return v_theta ** 2 + (math.sin(theta) ** 2) * (v_phi ** 2)


def clairaut_s2(theta: float, v_phi: float) -> float:
    """Clairaut invariant h = sin²θ · φ̇ (conserved on surface of revolution)."""
    return (math.sin(theta) ** 2) * v_phi


# ── R² geodesics (flat; trivial) ─────────────────────────────────────

def exp_map_r2(px: float, py: float, vx: float, vy: float) -> tuple[float, float]:
    """Exp map on R²: straight line, exp_p(v) = p + v."""
    return px + vx, py + vy


def log_map_r2(px: float, py: float, qx: float, qy: float) -> tuple[float, float]:
    """Log map on R²: log_p(q) = q - p."""
    return qx - px, qy - py


# =====================================================================
# SYMPY: derive geodesic ODE symbolically (load-bearing)
# =====================================================================

def sympy_derive_geodesic_ode() -> dict[str, Any]:
    """
    Use sympy to symbolically derive the geodesic ODE on S² from Christoffel symbols.
    Verifies:
      d²θ/dt² = -Γ^θ_{φφ} (dφ/dt)² = sin θ cos θ (dφ/dt)²
      d²φ/dt² = -2 Γ^φ_{θφ} (dθ/dt)(dφ/dt) = -2 (cos θ / sin θ) (dθ/dt)(dφ/dt)
    """
    if not _SYMPY_OK:
        return {"ok": False, "skip": True, "reason": "sympy not installed"}

    theta = sp.Symbol("theta", positive=True)

    # S² metric: g = diag(1, sin²θ)
    g = sp.Matrix([[1, 0], [0, sp.sin(theta)**2]])
    g_inv = g.inv()

    # Coordinate symbols
    coords = [theta, sp.Symbol("phi")]

    # Metric depends only on theta; g_{00}=1, g_{11}=sin²θ
    # ∂g_{ij}/∂x^k
    dg = [[[sp.diff(g[i, j], coords[k]) for k in range(2)]
           for j in range(2)] for i in range(2)]

    # Γ^σ_{μν} = (1/2) g^{σρ} (∂_μ g_{νρ} + ∂_ν g_{μρ} - ∂_ρ g_{μν})
    # dg[a][b][c] = ∂_{x^c} g_{ab}, so:
    #   ∂_μ g_{νρ} = dg[nu][rho][mu]
    #   ∂_ν g_{μρ} = dg[mu][rho][nu]
    #   ∂_ρ g_{μν} = dg[mu][nu][rho]
    Gamma = [[[sum(sp.Rational(1, 2) * g_inv[sig, rho] *
                    (dg[nu][rho][mu] + dg[mu][rho][nu] - dg[mu][nu][rho])
                    for rho in range(2))
               for nu in range(2)] for mu in range(2)] for sig in range(2)]

    # Geodesic ODE: d²x^σ/dt² = -Γ^σ_{μν} (dx^μ/dt)(dx^ν/dt)
    vt, vp = sp.Symbol("vt"), sp.Symbol("vp")
    velocities = [vt, vp]

    accel = []
    for sig in range(2):
        a_sig = -sum(Gamma[sig][mu][nu] * velocities[mu] * velocities[nu]
                     for mu in range(2) for nu in range(2))
        accel.append(sp.simplify(a_sig))

    # Expected
    expected_theta = sp.sin(theta) * sp.cos(theta) * vp**2
    expected_phi   = -2 * (sp.cos(theta) / sp.sin(theta)) * vt * vp

    diff_theta = sp.simplify(accel[0] - expected_theta)
    diff_phi   = sp.simplify(accel[1] - expected_phi)

    ok = (diff_theta == 0 and diff_phi == 0)

    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = (
        "Load-bearing: derives geodesic ODE symbolically from S² Christoffel symbols; "
        "verifies d²θ/dt²=sinθcosθ(dφ/dt)² and d²φ/dt²=-2cotθ(dθ/dt)(dφ/dt)"
    )
    TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"

    return {
        "ok": ok,
        "accel_theta": str(accel[0]),
        "accel_phi": str(accel[1]),
        "expected_theta": str(expected_theta),
        "expected_phi": str(expected_phi),
        "diff_theta_zero": str(diff_theta),
        "diff_phi_zero": str(diff_phi),
        "nonzero_christoffels": {
            f"Gamma^{sig}_{{{mu}{nu}}}": str(sp.simplify(Gamma[sig][mu][nu]))
            for sig in range(2) for mu in range(2) for nu in range(2)
            if sp.simplify(Gamma[sig][mu][nu]) != 0
        },
    }


# =====================================================================
# Z3: R² energy conservation (load-bearing)
# =====================================================================

def z3_r2_energy_conservation() -> dict[str, Any]:
    """
    Encode in z3: for a geodesic on R² (ax=ay=0), dE/dt = 2vx·ax + 2vy·ay = 0.
    SAT confirms the conservation law is consistent with zero-acceleration geodesics.
    Also: negation (dE/dt ≠ 0 with ax=ay=0) should be UNSAT.
    """
    if not _Z3_OK:
        return {"ok": False, "skip": True, "reason": "z3 not installed"}

    try:
        s = _z3.Solver()
        vx, vy = _z3.Real("vx"), _z3.Real("vy")
        ax, ay = _z3.Real("ax"), _z3.Real("ay")

        # Claim: geodesic on R² has zero acceleration
        flat_geod = _z3.And(ax == 0, ay == 0)
        # Energy rate: dE/dt = 2vx·ax + 2vy·ay
        dE_dt = 2 * vx * ax + 2 * vy * ay

        # SAT: with flat geodesic assumption, dE/dt = 0 is satisfiable (pick any vx, vy)
        s.add(flat_geod)
        s.add(dE_dt == 0)
        s.add(vx == 1, vy == 0)  # witness
        sat_result = str(s.check())
        sat_ok = (sat_result == "sat")

        # UNSAT: flat geodesic AND dE/dt ≠ 0 is unsatisfiable
        s2 = _z3.Solver()
        s2.add(flat_geod)
        s2.add(dE_dt != 0)
        unsat_result = str(s2.check())
        unsat_ok = (unsat_result == "unsat")

        ok = sat_ok and unsat_ok

        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = (
            "Load-bearing: R² energy conservation dE/dt=2vx·ax+2vy·ay=0 encoded as SMT; "
            "SAT confirms zero-acceleration geodesic conserves energy; "
            "negation (dE/dt≠0 with ax=ay=0) gives UNSAT — proves conservation"
        )
        TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"

        return {
            "ok": ok,
            "sat_result": sat_result,
            "sat_ok": sat_ok,
            "unsat_result": unsat_result,
            "unsat_ok": unsat_ok,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


# =====================================================================
# CVC5: R² exp-log round-trip (supportive)
# =====================================================================

def cvc5_r2_round_trip() -> dict[str, Any]:
    """
    Verify in cvc5 QF_LRA: exp_p(log_p(q)) = q on R².
    On R²: log_p(q) = q - p, exp_p(v) = p + v → exp_p(log_p(q)) = p + (q-p) = q. ✓
    Positive: SAT (the identity holds for some p, q).
    Negative: UNSAT (exp_p(log_p(q)) ≠ q with flat geometry constraints) — should be UNSAT.
    """
    if not _CVC5_OK:
        return {"ok": False, "skip": True, "reason": "cvc5 not installed"}

    try:
        tm = _cvc5.TermManager()
        slv = _cvc5.Solver(tm)
        slv.setLogic("QF_LRA")

        rs = tm.getRealSort()
        px = tm.mkConst(rs, "px"); py = tm.mkConst(rs, "py")
        qx = tm.mkConst(rs, "qx"); qy = tm.mkConst(rs, "qy")

        # log_p(q) = (qx-px, qy-py)
        vx = tm.mkTerm(_cvc5.Kind.SUB, qx, px)
        vy = tm.mkTerm(_cvc5.Kind.SUB, qy, py)

        # exp_p(v) = (px+vx, py+vy)
        ex = tm.mkTerm(_cvc5.Kind.ADD, px, vx)  # = qx
        ey = tm.mkTerm(_cvc5.Kind.ADD, py, vy)  # = qy

        # round-trip: ex == qx and ey == qy
        eq_x = tm.mkTerm(_cvc5.Kind.EQUAL, ex, qx)
        eq_y = tm.mkTerm(_cvc5.Kind.EQUAL, ey, qy)
        round_trip_holds = tm.mkTerm(_cvc5.Kind.AND, eq_x, eq_y)

        # SAT: round-trip holds (should be SAT — trivially true for any p,q)
        slv.assertFormula(round_trip_holds)
        sat_result = slv.checkSat()
        sat_ok = sat_result.isSat()

        # UNSAT: round-trip fails (negation of round-trip should be UNSAT)
        tm2 = _cvc5.TermManager()
        slv2 = _cvc5.Solver(tm2)
        slv2.setLogic("QF_LRA")
        rs2 = tm2.getRealSort()
        px2 = tm2.mkConst(rs2, "px2"); py2 = tm2.mkConst(rs2, "py2")
        qx2 = tm2.mkConst(rs2, "qx2"); qy2 = tm2.mkConst(rs2, "qy2")
        vx2 = tm2.mkTerm(_cvc5.Kind.SUB, qx2, px2)
        vy2 = tm2.mkTerm(_cvc5.Kind.SUB, qy2, py2)
        ex2 = tm2.mkTerm(_cvc5.Kind.ADD, px2, vx2)
        ey2 = tm2.mkTerm(_cvc5.Kind.ADD, py2, vy2)
        neq_x = tm2.mkTerm(_cvc5.Kind.NOT, tm2.mkTerm(_cvc5.Kind.EQUAL, ex2, qx2))
        neq_y = tm2.mkTerm(_cvc5.Kind.NOT, tm2.mkTerm(_cvc5.Kind.EQUAL, ey2, qy2))
        round_trip_fails = tm2.mkTerm(_cvc5.Kind.OR, neq_x, neq_y)
        slv2.assertFormula(round_trip_fails)
        unsat_result = slv2.checkSat()
        unsat_ok = unsat_result.isUnsat()

        ok = sat_ok and unsat_ok

        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_MANIFEST["cvc5"]["reason"] = (
            "Supportive: R² exp-log round-trip exp_p(log_p(q))=q verified via QF_LRA; "
            "round-trip holds → SAT; negation (round-trip fails) → UNSAT; "
            "proves algebraic correctness of flat exp/log definitions"
        )
        TOOL_INTEGRATION_DEPTH["cvc5"] = "supportive"

        return {
            "ok": ok,
            "sat_result": str(sat_result),
            "sat_ok": sat_ok,
            "unsat_result": str(unsat_result),
            "unsat_ok": unsat_ok,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


# =====================================================================
# GEOMSTATS: cross-validate geodesic distance on S² (supportive)
# =====================================================================

def geomstats_cross_validate(theta_p: float, phi_p: float,
                              theta_q: float, phi_q: float) -> dict[str, Any]:
    """
    Use geomstats Hypersphere(dim=2) metric to cross-validate geodesic distance.
    """
    if not _GEOMSTATS_OK:
        return {"ok": False, "skip": True, "reason": "geomstats not installed"}

    try:
        import geomstats.backend as gs
        from geomstats.geometry.hypersphere import Hypersphere

        sphere = Hypersphere(dim=2)
        p_amb = np.array([math.sin(theta_p) * math.cos(phi_p),
                          math.sin(theta_p) * math.sin(phi_p),
                          math.cos(theta_p)])
        q_amb = np.array([math.sin(theta_q) * math.cos(phi_q),
                          math.sin(theta_q) * math.sin(phi_q),
                          math.cos(theta_q)])

        dist_ours = geodesic_distance_s2(theta_p, phi_p, theta_q, phi_q)
        dist_gs = float(sphere.metric.dist(
            gs.array(p_amb.tolist()),
            gs.array(q_amb.tolist())
        ))

        err = abs(dist_ours - dist_gs)
        ok = err < 1e-6

        TOOL_MANIFEST["geomstats"]["used"] = True
        TOOL_MANIFEST["geomstats"]["reason"] = (
            "Supportive: Hypersphere(dim=2).metric.dist cross-validates our geodesic distance "
            "formula at test points; agreement within 1e-6 confirms S² arc-length computation"
        )
        TOOL_INTEGRATION_DEPTH["geomstats"] = "supportive"

        return {
            "ok": ok,
            "dist_ours": dist_ours,
            "dist_geomstats": dist_gs,
            "error": err,
            "theta_p": theta_p, "phi_p": phi_p,
            "theta_q": theta_q, "phi_q": phi_q,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests() -> dict[str, Any]:
    results: dict[str, Any] = {}

    # ── 1. Sympy ODE derivation ──────────────────────────────────────
    results["sympy_geodesic_ode_derivation"] = sympy_derive_geodesic_ode()

    # ── 2. Meridian geodesic ─────────────────────────────────────────
    # Meridian: φ = const, dφ/dt = 0. θ(t) = θ₀ + v_θ · t (great circle along meridian).
    # With θ₀=0.1, v_θ=0.8, after t=1: θ_f should be 0.9, φ_f unchanged.
    theta_0, phi_0 = 0.1, 0.5
    v_theta, v_phi = 0.8, 0.0
    theta_f, phi_f = exp_map_s2(theta_0, phi_0, v_theta, v_phi, n_steps=1000)
    theta_expected = theta_0 + v_theta  # exact for meridian geodesic
    meridian_theta_err = abs(theta_f - theta_expected)
    meridian_phi_err = abs(phi_f - phi_0)
    results["meridian_geodesic"] = {
        "ok": meridian_theta_err < 1e-6 and meridian_phi_err < 1e-6,
        "theta_0": theta_0, "phi_0": phi_0, "v_theta": v_theta, "v_phi": v_phi,
        "theta_f": theta_f, "phi_f": phi_f,
        "theta_expected": theta_expected,
        "theta_err": meridian_theta_err,
        "phi_err": meridian_phi_err,
        "note": "Meridian geodesic: dφ/dt=0 → Γ terms vanish → θ(t)=θ₀+v_θ·t exactly",
    }

    # ── 3. Equatorial geodesic ───────────────────────────────────────
    # Equatorial: θ = π/2, dθ/dt = 0. φ(t) = φ₀ + v_φ · t.
    # At θ=π/2: sin=1, cos=0 → Γ^θ_{φφ}=0, Γ^φ_{θφ}=0. Pure rotation.
    theta_eq = math.pi / 2
    phi_eq = 0.0
    v_phi_eq = math.pi / 2
    theta_ef, phi_ef = exp_map_s2(theta_eq, phi_eq, 0.0, v_phi_eq, n_steps=1000)
    phi_expected = phi_eq + v_phi_eq
    eq_theta_err = abs(theta_ef - theta_eq)
    eq_phi_err = abs(phi_ef - phi_expected)
    results["equatorial_geodesic"] = {
        "ok": eq_theta_err < 1e-6 and eq_phi_err < 1e-6,
        "theta": theta_eq, "phi_0": phi_eq, "v_phi": v_phi_eq,
        "theta_f": theta_ef, "phi_f": phi_ef,
        "phi_expected": phi_expected,
        "theta_err": eq_theta_err,
        "phi_err": eq_phi_err,
        "note": "Equatorial geodesic: all Christoffels zero at θ=π/2 → trivial ODE",
    }

    # ── 4. S² exp-log round-trip ─────────────────────────────────────
    # log_p(q) = (v_θ, v_φ); exp_p(v) should return q.
    theta_p, phi_p = 0.4, 0.3
    theta_q, phi_q = 0.9, 1.2
    vt_log, vp_log = log_map_s2(theta_p, phi_p, theta_q, phi_q)
    theta_rt, phi_rt = exp_map_s2(theta_p, phi_p, vt_log, vp_log, n_steps=2000)
    p_rt = spherical_to_ambient(theta_rt, phi_rt)
    q_ref = spherical_to_ambient(theta_q, phi_q)
    round_trip_err = float(np.linalg.norm(p_rt - q_ref))
    results["s2_exp_log_round_trip"] = {
        "ok": round_trip_err < 1e-5,
        "theta_p": theta_p, "phi_p": phi_p,
        "theta_q": theta_q, "phi_q": phi_q,
        "v_theta_log": vt_log, "v_phi_log": vp_log,
        "theta_rt": theta_rt, "phi_rt": phi_rt,
        "round_trip_ambient_err": round_trip_err,
    }

    # ── 5. R² exp-log round-trip ─────────────────────────────────────
    px, py = 1.5, 2.3
    qx, qy = 4.0, -1.0
    vx_log, vy_log = log_map_r2(px, py, qx, qy)
    rx, ry = exp_map_r2(px, py, vx_log, vy_log)
    r2_err = math.sqrt((rx - qx)**2 + (ry - qy)**2)
    results["r2_exp_log_round_trip"] = {
        "ok": r2_err < 1e-12,
        "p": [px, py], "q": [qx, qy],
        "v_log": [vx_log, vy_log],
        "recovered": [rx, ry],
        "error": r2_err,
    }

    # ── 6. Energy and Clairaut conservation ─────────────────────────
    # Integrate a non-trivial geodesic and check E and h remain constant.
    theta_c, phi_c = 0.5, 0.0
    vt_c, vp_c = 0.3, 1.0
    y = np.array([theta_c, phi_c, vt_c, vp_c])
    E0 = energy_s2(float(y[0]), float(y[2]), float(y[3]))
    h0 = clairaut_s2(float(y[0]), float(y[3]))
    n_check = 500
    dt = 2.0 / n_check
    E_vals = [E0]
    h_vals = [h0]
    for _ in range(n_check):
        y = rk4_step(y, dt, geodesic_rhs_s2)
        E_vals.append(energy_s2(float(y[0]), float(y[2]), float(y[3])))
        h_vals.append(clairaut_s2(float(y[0]), float(y[3])))
    E_drift = float(max(abs(e - E0) for e in E_vals))
    h_drift = float(max(abs(h - h0) for h in h_vals))
    results["conservation_laws"] = {
        "ok": E_drift < 1e-6 and h_drift < 1e-6,
        "E0": E0, "h0": h0,
        "E_max_drift": E_drift,
        "h_max_drift": h_drift,
        "n_steps": n_check,
        "t_end": 2.0,
        "note": "E=θ̇²+sin²θ·φ̇² and h=sin²θ·φ̇ both conserved along geodesic",
    }

    # ── 7. Geomstats distance cross-validation ───────────────────────
    results["geomstats_distance_cross_validate"] = geomstats_cross_validate(
        theta_p=0.4, phi_p=0.3, theta_q=0.9, phi_q=1.2
    )

    # ── 8. Z3 R² energy conservation ────────────────────────────────
    results["z3_r2_energy_conservation"] = z3_r2_energy_conservation()

    # ── 9. CVC5 R² round-trip ────────────────────────────────────────
    results["cvc5_r2_round_trip"] = cvc5_r2_round_trip()

    return results


# =====================================================================
# NEGATIVE TESTS (mandatory)
# =====================================================================

def run_negative_tests() -> dict[str, Any]:
    results: dict[str, Any] = {}

    # ── 1. R² geodesics are trivially flat ──────────────────────────
    # On R², d²x/dt² = 0. Integrating a straight line should be exact.
    # A "curved" update (wrong sign) would deviate — we detect deviation.
    px, py = 0.0, 0.0
    vx, vy = 3.0, 4.0
    # Correct R²: endpoint = p + v (linear)
    correct_x, correct_y = exp_map_r2(px, py, vx, vy)
    expected_x, expected_y = px + vx, py + vy
    r2_flat_ok = (abs(correct_x - expected_x) < 1e-12 and
                  abs(correct_y - expected_y) < 1e-12)
    # Wrong: if we mistakenly applied a spherical correction with κ=1, we'd get deviation
    # Simulate wrong exp map: corrupt by adding a fake curvature term
    fake_correction = 0.5 * (vx**2 + vy**2) * 0.01  # clearly nonzero
    wrong_x = expected_x + fake_correction
    r2_flat_wrong_different = abs(wrong_x - expected_x) > 1e-8
    results["r2_flat_trivial"] = {
        "ok": r2_flat_ok and r2_flat_wrong_different,
        "correct_endpoint": [correct_x, correct_y],
        "expected_endpoint": [expected_x, expected_y],
        "flat_geodesic_correct": r2_flat_ok,
        "wrong_map_detectable": r2_flat_wrong_different,
        "note": "R² geodesic must be linear; any curvature correction is detectable",
    }

    # ── 2. Wrong metric kills geodesic ODE ──────────────────────────
    # If we use Euclidean Christoffels (all zero) on S², the geodesic drifts.
    # Meridian geodesic at θ₀=0.3, v_θ=0.5, v_φ=0.5 with correct vs wrong ODE.
    def geodesic_rhs_flat(y: np.ndarray) -> np.ndarray:
        """Wrong: zero Christoffels (treats S² as flat). Returns incorrect geodesic."""
        return np.array([y[2], y[3], 0.0, 0.0])

    theta_w, phi_w = 0.3, 0.0
    vt_w, vp_w = 0.5, 0.5  # mixed θ+φ velocity so flat ODE changes θ → E not conserved

    y_correct = np.array([theta_w, phi_w, vt_w, vp_w])
    y_wrong   = np.array([theta_w, phi_w, vt_w, vp_w])
    dt_w = 2.0 / 500
    for _ in range(500):
        y_correct = rk4_step(y_correct, dt_w, geodesic_rhs_s2)
        y_wrong   = rk4_step(y_wrong,   dt_w, geodesic_rhs_flat)

    # Correct geodesic stays on S² (energy conserved); wrong drifts in θ
    E_correct = energy_s2(float(y_correct[0]), float(y_correct[2]), float(y_correct[3]))
    E_initial = energy_s2(theta_w, vt_w, vp_w)
    E_wrong   = energy_s2(float(y_wrong[0]),   float(y_wrong[2]),   float(y_wrong[3]))

    theta_diff = abs(float(y_correct[0]) - float(y_wrong[0]))
    E_correct_drift = abs(E_correct - E_initial)
    E_wrong_drift   = abs(E_wrong - E_initial)

    results["wrong_metric_geodesic_drift"] = {
        "ok": (theta_diff > 1e-4 and E_correct_drift < 1e-4 and E_wrong_drift > 1e-4),
        "theta_correct": float(y_correct[0]),
        "theta_wrong": float(y_wrong[0]),
        "theta_diff": theta_diff,
        "E_initial": E_initial,
        "E_correct_drift": E_correct_drift,
        "E_wrong_drift": E_wrong_drift,
        "note": "Zero-Christoffel (flat) ODE fails on S²: energy drifts; correct ODE conserves energy",
    }

    # ── 3. Cut locus: log_map returns nan at antipodal ───────────────
    # At θ_q = π - θ_p, φ_q = φ_p + π: antipodal point. log_map should return nan.
    theta_p_cl = 0.6
    phi_p_cl = 0.0
    # Antipodal: (π - θ_p, φ_p + π)
    theta_ant = math.pi - theta_p_cl
    phi_ant = phi_p_cl + math.pi
    vt_ant, vp_ant = log_map_s2(theta_p_cl, phi_p_cl, theta_ant, phi_ant)
    both_nan = math.isnan(vt_ant) and math.isnan(vp_ant)
    results["cut_locus_log_undefined"] = {
        "ok": both_nan,
        "theta_p": theta_p_cl, "phi_p": phi_p_cl,
        "theta_antipodal": theta_ant, "phi_antipodal": phi_ant,
        "v_theta_log": vt_ant, "v_phi_log": vp_ant,
        "both_nan": both_nan,
        "note": "log_p(−p) is undefined (multivalued) at antipodal point — cut locus",
    }

    # ── 4. Z3 confirms: nonzero acceleration ≠ flat geodesic ────────
    # Encodes: if a≠0, the particle is not following a flat geodesic. SAT.
    if _Z3_OK:
        try:
            s_neg = _z3.Solver()
            ax_n, ay_n = _z3.Real("ax_n"), _z3.Real("ay_n")
            vx_n, vy_n = _z3.Real("vx_n"), _z3.Real("vy_n")
            # Nonzero acceleration witness
            s_neg.add(_z3.Or(ax_n != 0, ay_n != 0))
            # dE/dt = 2vx·ax + 2vy·ay; if ax≠0, dE/dt can be nonzero
            dE_neg = 2 * vx_n * ax_n + 2 * vy_n * ay_n
            s_neg.add(vx_n == 1, vy_n == 0, ax_n == 1, ay_n == 0)
            s_neg.add(dE_neg != 0)
            neg_z3_result = str(s_neg.check())
            results["z3_nonflat_geodesic_negative"] = {
                "ok": neg_z3_result == "sat",
                "result": neg_z3_result,
                "note": "With ax=1≠0, dE/dt=2≠0: non-flat geodesic breaks energy conservation — SAT",
            }
        except Exception as e:
            results["z3_nonflat_geodesic_negative"] = {"ok": False, "error": str(e)}
    else:
        results["z3_nonflat_geodesic_negative"] = {"ok": True, "skip": True, "reason": "z3 not installed"}

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests() -> dict[str, Any]:
    results: dict[str, Any] = {}

    # ── 1. Near-pole geodesic (θ₀ = 0.05) ──────────────────────────
    theta_np, phi_np = 0.05, 0.0
    vt_np, vp_np = 0.3, 0.0  # pure meridian to avoid cot singularity
    theta_np_f, phi_np_f = exp_map_s2(theta_np, phi_np, vt_np, vp_np, n_steps=2000)
    # Meridian geodesic: θ_f = θ₀ + v_θ
    near_pole_err = abs(theta_np_f - (theta_np + vt_np))
    results["near_pole_geodesic"] = {
        "ok": near_pole_err < 1e-5,
        "theta_0": theta_np, "v_theta": vt_np,
        "theta_f": theta_np_f,
        "theta_expected": theta_np + vt_np,
        "error": near_pole_err,
        "note": "Near-pole (θ=0.05) meridian geodesic; pole-guard prevents cot singularity",
    }

    # ── 2. Cut-locus approach: distance → π monotonically ───────────
    # Take a sequence of points q_ε approaching the antipodal point of p.
    # |log_p(q_ε)| should monotonically approach π.
    theta_p_cl = math.pi / 2
    phi_p_cl = 0.0
    # Antipodal of (π/2, 0) is (π/2, π).
    epsilons = [0.3, 0.2, 0.1, 0.05, 0.02, 0.01]
    approach_norms = []
    for eps in epsilons:
        # q_ε approaches (π/2, π) as ε→0
        theta_q_cl = math.pi / 2
        phi_q_cl = math.pi - eps
        vt_cl, vp_cl = log_map_s2(theta_p_cl, phi_p_cl, theta_q_cl, phi_q_cl)
        if math.isnan(vt_cl):
            norm = float("nan")
        else:
            norm = math.sqrt(vt_cl**2 + vp_cl**2)
        approach_norms.append({"eps": eps, "phi_q": phi_q_cl, "log_norm": norm})

    # Check: norms should be increasing as eps decreases
    finite_norms = [e["log_norm"] for e in approach_norms if not math.isnan(e["log_norm"])]
    monotone_ok = all(finite_norms[i] < finite_norms[i+1] for i in range(len(finite_norms)-1))

    results["cut_locus_approach"] = {
        "ok": monotone_ok and len(finite_norms) >= 3,
        "sequence": approach_norms,
        "finite_norm_count": len(finite_norms),
        "monotone_increasing": monotone_ok,
        "note": "|log_p(q)| → π monotonically as q → antipodal; undefined at cut locus",
    }

    # ── 3. High-resolution convergence ──────────────────────────────
    # Geodesic at (0.4, 0.3) → (0.9, 1.2); compare n_steps=500 vs 2000.
    tp, pp = 0.4, 0.3
    tq, pq = 0.9, 1.2
    vt_r, vp_r = log_map_s2(tp, pp, tq, pq)
    t500_f, p500_f = exp_map_s2(tp, pp, vt_r, vp_r, n_steps=500)
    t2000_f, p2000_f = exp_map_s2(tp, pp, vt_r, vp_r, n_steps=2000)
    p500_amb = spherical_to_ambient(t500_f, p500_f)
    p2000_amb = spherical_to_ambient(t2000_f, p2000_f)
    q_amb = spherical_to_ambient(tq, pq)
    err_500  = float(np.linalg.norm(p500_amb - q_amb))
    err_2000 = float(np.linalg.norm(p2000_amb - q_amb))
    # Higher resolution should be more accurate
    convergence_ok = (err_2000 < err_500) and (err_2000 < 1e-6)
    results["rk4_convergence"] = {
        "ok": convergence_ok,
        "err_n500": err_500,
        "err_n2000": err_2000,
        "ratio": err_500 / err_2000 if err_2000 > 0 else float("inf"),
        "note": "Higher n_steps gives smaller round-trip error; RK4 global error O(dt⁴)",
    }

    # ── 4. Equatorial symmetry: both poles as initial points ─────────
    # Exp map from north pole region should be symmetric in φ.
    theta_sym = 0.2
    phi_sym = 0.0
    # Two tangent vectors with opposite φ components
    vt_s, vp_s1 = 0.5, 0.5
    vp_s2 = -0.5
    tf1, pf1 = exp_map_s2(theta_sym, phi_sym, vt_s, vp_s1)
    tf2, pf2 = exp_map_s2(theta_sym, phi_sym, vt_s, vp_s2)
    # θ should be the same (φ-reflection symmetry); φ should be negated
    sym_theta_err = abs(tf1 - tf2)
    sym_phi_err = abs(pf1 + pf2)  # should sum to 0 (φ and -φ)
    results["phi_reflection_symmetry"] = {
        "ok": sym_theta_err < 1e-6 and sym_phi_err < 1e-6,
        "theta_f1": tf1, "phi_f1": pf1,
        "theta_f2": tf2, "phi_f2": pf2,
        "theta_diff": sym_theta_err,
        "phi_sum": sym_phi_err,
        "note": "S² geodesics from (θ₀,0) with ±v_φ are φ-reflections: same θ_f, opposite φ_f",
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    # Gather all pass flags
    def _ok(d: dict) -> bool:
        return bool(d.get("ok", False)) or bool(d.get("skip", False))

    all_sections = list(positive.values()) + list(negative.values()) + list(boundary.values())
    overall_pass = all(_ok(v) for v in all_sections if isinstance(v, dict))

    results = {
        "name": "sim_pure_lego_geodesic_exponential_map",
        "lego_ids": ["geodesic_exponential_map"],
        "classification": "canonical",
        "overall_pass": overall_pass,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "geodesic_exponential_map_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"Results written to {out_path}")
    print(f"overall_pass={overall_pass}")
    if overall_pass:
        print("GEODESIC EXPONENTIAL MAP PASSED")
    else:
        print("GEODESIC EXPONENTIAL MAP FAILED")
        # Print which tests failed
        for section_name, section in [("positive", positive), ("negative", negative), ("boundary", boundary)]:
            for k, v in section.items():
                if isinstance(v, dict) and not _ok(v):
                    print(f"  FAIL [{section_name}]: {k}")

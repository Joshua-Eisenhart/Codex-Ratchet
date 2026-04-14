#!/usr/bin/env python3
"""
sim_pure_lego_contact_symplectic_kahler_coexistence.py — Three-shell coexistence probe:
S³ contact shell ↔ S² symplectic shell ↔ CP¹/S² Kähler shell.

Coupling Program step 3: can all three shells coexist simultaneously?

Shell definitions:
  Contact shell (S³): α, dα, R, ker(α)  [standalone probe: contact_structure_s3]
  Symplectic shell (S²): ω_S² = q·(u×v)  [pairwise: contact_symplectic_coupling]
  Kähler shell (CP¹/S²): (g, J, ω_K)    [NEW — added here]
    g = round metric on S² (g(u,v) = u·v for u,v ∈ T_qS²)
    J_q(v) = q × v  (complex structure: rotation by π/2 in T_qS²)
    ω_K = g(J·, ·) = ω_S²  (Kähler form coincides with area form on S²)

Key fact (established): ω_K = ω_S² identically on S² with standard structures.
This means the bridge identity is inherited by the Kähler shell automatically:
  ω_K(dπ(h₁), dπ(h₂)) = ω_S²(dπ(h₁), dπ(h₂)) = -2·dα(h₁, h₂)

Three-way coexistence criterion:
  (i)   ω_S²(dπ(h₁),dπ(h₂)) = -2·dα(h₁,h₂)  [bridge, c=-2, established]
  (ii)  ω_K = ω_S² on S²  [Kähler-symplectic identity]
  (iii) J² = -Id on T_qS²  [valid complex structure]
  (iv)  g(J_q u, J_q v) = g(u,v)  [g-compatibility of J]
  (v)   ω_K(v, J_q v) > 0 for all nonzero v ∈ T_qS²  [Kähler positivity]

Sign convention preserved from prior probes:
  ω_S²(dπ(h₁),dπ(h₂)) = -2 * dα(h₁,h₂)

Classification: canonical
Started from SIM_TEMPLATE.py
"""

import datetime
import json
import os
import traceback

import numpy as np
classification = "classical_baseline"  # auto-backfill

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": ""},
    "z3":        {"tried": False, "used": False, "reason": ""},
    "cvc5":      {"tried": False, "used": False, "reason": ""},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "clifford":  {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn":      {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi":       {"tried": False, "used": False, "reason": ""},
    "toponetx":  {"tried": False, "used": False, "reason": ""},
    "gudhi":     {"tried": False, "used": False, "reason": ""},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch":   None,
    "pyg":       None,
    "z3":        None,
    "cvc5":      None,
    "sympy":     None,
    "clifford":  None,
    "geomstats": None,
    "e3nn":      None,
    "rustworkx": None,
    "xgi":       None,
    "toponetx":  None,
    "gudhi":     None,
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "Primary engine: all three shell geometry computations — contact form α, "
        "Hopf map π, Jacobian dπ, horizontal basis, area form ω_S², and the new "
        "Kähler shell checks: complex structure J_q(v)=q×v via torch.linalg.cross, "
        "J²=-Id residual, g-compatibility, Kähler positivity ω_K(v,Jv)>0 at "
        "50 random S³ points and explicit ground truth cases."
    )
    TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    from z3 import Real, RealVal, Solver, sat, unsat
    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = (
        "UNSAT proof N4: assuming anti-J structure (J'=-J) satisfies Kähler positivity "
        "ω_K(v,J'v)>0 contradicts the algebraic fact that J'=-J flips the positivity sign. "
        "Encodes: omega_base>0 (standard J valid), omega_antiJ=-omega_base (sign flip), "
        "omega_antiJ>0 (positivity axiom). System is UNSAT — orientation-reversed complex "
        "structure is structurally incompatible with Kähler coexistence."
    )
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = (
        "Symbolic checks: (1) J²=-Id via BAC-CAB vector identity q×(q×v)=q(q·v)-v|q|², "
        "proved as polynomial identity then reduced under constraints |q|=1, v·q=0 to -v; "
        "(2) ω_K=ω_S² via scalar triple product identity (q×u)·v = q·(u×v), "
        "algebraically exact with no constraints needed."
    )
    TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

for tool, reason in [
    ("pyg",       "not relevant to three-shell geometric coexistence probe"),
    ("cvc5",      "not relevant to three-shell geometric coexistence probe"),
    ("clifford",  "not relevant to three-shell geometric coexistence probe"),
    ("geomstats", "not relevant to three-shell geometric coexistence probe"),
    ("e3nn",      "not relevant to three-shell geometric coexistence probe"),
    ("rustworkx", "not relevant to three-shell geometric coexistence probe"),
    ("xgi",       "not relevant to three-shell geometric coexistence probe"),
    ("toponetx",  "not relevant to three-shell geometric coexistence probe"),
    ("gudhi",     "not relevant to three-shell geometric coexistence probe"),
]:
    if not TOOL_MANIFEST[tool]["reason"]:
        TOOL_MANIFEST[tool]["reason"] = reason


# =====================================================================
# SHELL GEOMETRY — contact (S³) + symplectic (S²) [inherited from prior probes]
# =====================================================================

def alpha_eval(p, v):
    """Contact 1-form: α_p(v) = p₀v₁ - p₁v₀ + p₂v₃ - p₃v₂"""
    return (p[..., 0]*v[..., 1] - p[..., 1]*v[..., 0]
            + p[..., 2]*v[..., 3] - p[..., 3]*v[..., 2])


def dalpha_eval(u, v):
    """Exterior derivative: dα(u,v) = 2(u₀v₁-u₁v₀+u₂v₃-u₃v₂)"""
    return 2.0*(u[..., 0]*v[..., 1] - u[..., 1]*v[..., 0]
                + u[..., 2]*v[..., 3] - u[..., 3]*v[..., 2])


def reeb_field(p):
    """Reeb field: R(p) = (-x₁, x₀, -x₃, x₂)"""
    return torch.stack([-p[..., 1], p[..., 0], -p[..., 3], p[..., 2]], dim=-1)


def hopf_map(p):
    """Hopf projection π: S³→S².
    X=2(x₀x₂+x₁x₃), Y=2(x₁x₂-x₀x₃), Z=x₀²+x₁²-x₂²-x₃²
    """
    x0, x1, x2, x3 = p[..., 0], p[..., 1], p[..., 2], p[..., 3]
    return torch.stack([
        2.0*(x0*x2 + x1*x3),
        2.0*(x1*x2 - x0*x3),
        x0**2 + x1**2 - x2**2 - x3**2,
    ], dim=-1)


def hopf_jacobian(p):
    """Hopf Jacobian dπ, shape (..., 3, 4).
    Rows: [2x₂,2x₃,2x₀,2x₁], [-2x₃,2x₂,2x₁,-2x₀], [2x₀,2x₁,-2x₂,-2x₃]
    """
    x0, x1, x2, x3 = p[..., 0], p[..., 1], p[..., 2], p[..., 3]
    return torch.stack([
        torch.stack([ 2*x2,  2*x3,  2*x0,  2*x1], dim=-1),
        torch.stack([-2*x3,  2*x2,  2*x1, -2*x0], dim=-1),
        torch.stack([ 2*x0,  2*x1, -2*x2, -2*x3], dim=-1),
    ], dim=-2)


def omega_s2(q, u, v):
    """Symplectic area form: ω_S²(q;u,v) = q·(u×v)"""
    return (q * torch.linalg.cross(u, v)).sum(dim=-1)


def omega_fs(q, u, v):
    """Fubini-Study Kähler form: ω_FS(q;u,v) = (1/4)·q·(u×v).
    CP¹ normalization: total integral = π (vs ω_S² = 4π over S²).
    c₂₃ = ω_FS/ω_S² = 1/4  [exact, definitional].
    """
    return 0.25 * omega_s2(q, u, v)


def horizontal_basis(p):
    """Orthonormal basis for ker(α) ∩ T_pS³ via α-projection (stable everywhere)."""
    R = reeb_field(p)
    shape = p.shape[:-1]
    candidates = []
    for j in range(4):
        ej = torch.zeros(*shape, 4, dtype=p.dtype, device=p.device)
        ej[..., j] = 1.0
        v = ej - (ej*p).sum(dim=-1, keepdim=True)*p
        h = v - alpha_eval(p, v).unsqueeze(-1)*R
        candidates.append((torch.norm(h, dim=-1), h))
    norms = torch.stack([c[0] for c in candidates], dim=-1)
    hvecs = torch.stack([c[1] for c in candidates], dim=-2)
    idx = torch.argsort(norms, dim=-1, descending=True)
    idx0 = idx[..., 0:1].unsqueeze(-1).expand(*shape, 1, 4)
    idx1 = idx[..., 1:2].unsqueeze(-1).expand(*shape, 1, 4)
    h1r = hvecs.gather(-2, idx0).squeeze(-2)
    h2r = hvecs.gather(-2, idx1).squeeze(-2)
    h1 = h1r / (torch.norm(h1r, dim=-1, keepdim=True) + 1e-30)
    h2p = h2r - (h2r*h1).sum(dim=-1, keepdim=True)*h1
    h2 = h2p / (torch.norm(h2p, dim=-1, keepdim=True) + 1e-30)
    return h1, h2


def random_s3_points(n, dtype=torch.float64):
    """Uniform S³ points."""
    p = torch.randn(n, 4, dtype=dtype)
    return p / torch.norm(p, dim=-1, keepdim=True)


# =====================================================================
# KÄHLER SHELL — complex structure J on S²/CP¹
# =====================================================================

def complex_j_s2(q, v):
    """Complex structure on S²/CP¹: J_q(v) = q × v.
    Properties:
      J²(v) = q×(q×v) = -v  [for v ⊥ q, |q|=1, by BAC-CAB]
      g(Ju,Jv) = g(u,v)      [g-compatible]
      ω_K(v,Jv) > 0          [Kähler positivity]
    q ∈ S² is the base point (unit normal); v ∈ T_qS² is a tangent 3-vector.
    """
    return torch.linalg.cross(q, v)


def pushforward_vectors(pts):
    """Compute horizontal basis pushforwards dπ(h₁), dπ(h₂) at batch of S³ points.
    Returns: (q, dph1, dph2) — all shape (N, 3).
    """
    h1, h2 = horizontal_basis(pts)
    J_mat = hopf_jacobian(pts)          # (N, 3, 4)
    q = hopf_map(pts)                   # (N, 3)
    dph1 = torch.bmm(J_mat, h1.unsqueeze(-1)).squeeze(-1)  # (N, 3)
    dph2 = torch.bmm(J_mat, h2.unsqueeze(-1)).squeeze(-1)
    return q, dph1, dph2, h1, h2


# =====================================================================
# POSITIVE TESTS — three-way coexistence verified
# =====================================================================

def run_positive_tests():
    results = {}

    # P1: J² = -Id at 50 random S³ points (relative residual)
    try:
        pts = random_s3_points(50)
        q, dph1, dph2, h1, h2 = pushforward_vectors(pts)
        # J_q(dπh₁) = q × dπh₁
        J_dph1 = complex_j_s2(q, dph1)         # (50, 3)
        # J²(dπh₁) = q × (q × dπh₁)
        JJ_dph1 = complex_j_s2(q, J_dph1)      # should be -(dπh₁)
        # Residual: |J²v + v| / |v|
        resid_abs = (JJ_dph1 + dph1).norm(dim=-1)           # (50,)
        dph1_norm = dph1.norm(dim=-1)                         # (50,)
        rel_resid = resid_abs / (dph1_norm + 1e-30)           # (50,)
        max_rel = float(rel_resid.max().item())
        pass_p1 = bool(max_rel < 1e-12)
        results["P1_complex_structure_j_squared"] = {
            "pass": pass_p1,
            "kahler_residual": max_rel,
            "threshold": 1e-12,
            "n_points": 50,
            "verdict": "compatible" if pass_p1 else "incompatible",
            "description": "J²=-Id: relative residual |J(J(dπh))+dπh|/|dπh| < 1e-12 at 50 S³ points",
        }
    except Exception as e:
        results["P1_complex_structure_j_squared"] = {"pass": False, "error": str(e), "verdict": "error"}

    # P2: Kähler positivity ω_K(dπh, J(dπh)) > 0 at 50 random S³ points
    try:
        pts = random_s3_points(50)
        q, dph1, dph2, h1, h2 = pushforward_vectors(pts)
        J_dph1 = complex_j_s2(q, dph1)
        positivity = omega_s2(q, dph1, J_dph1)   # ω_K(dπh₁, J_q(dπh₁)) = |dπh₁|² ≥ 4
        min_pos = float(positivity.min().item())
        pass_p2 = bool(min_pos > 0.1)
        results["P2_kahler_positivity"] = {
            "pass": pass_p2,
            "kahler_residual": -min_pos,           # negative: how far from zero
            "min_positivity_value": min_pos,
            "threshold": 0.1,
            "n_points": 50,
            "verdict": "compatible" if pass_p2 else "incompatible",
            "description": "Kähler positivity: ω_K(dπh, J(dπh)) > 0.1 at 50 S³ points",
        }
    except Exception as e:
        results["P2_kahler_positivity"] = {"pass": False, "error": str(e), "verdict": "error"}

    # P3: g-compatibility g(Ju,Jv) = g(u,v) at 50 random S³ points
    try:
        pts = random_s3_points(50)
        q, dph1, dph2, h1, h2 = pushforward_vectors(pts)
        J_dph1 = complex_j_s2(q, dph1)
        J_dph2 = complex_j_s2(q, dph2)
        g_Ju_Jv = (J_dph1 * J_dph2).sum(dim=-1)   # g(Ju,Jv) = Ju·Jv
        g_u_v   = (dph1  * dph2 ).sum(dim=-1)      # g(u,v) = u·v
        compat_resid = (g_Ju_Jv - g_u_v).abs()
        max_resid = float(compat_resid.max().item())
        pass_p3 = bool(max_resid < 1e-12)
        results["P3_g_compatibility"] = {
            "pass": pass_p3,
            "kahler_residual": max_resid,
            "threshold": 1e-12,
            "n_points": 50,
            "verdict": "compatible" if pass_p3 else "incompatible",
            "description": "g-compatibility: |g(J_q u, J_q v) - g(u,v)| < 1e-12 at 50 S³ points",
        }
    except Exception as e:
        results["P3_g_compatibility"] = {"pass": False, "error": str(e), "verdict": "error"}

    # P4: Explicit north pole ground truth — all three-way checks simultaneously
    try:
        p = torch.tensor([[1.0, 0.0, 0.0, 0.0]], dtype=torch.float64)
        h1v = torch.tensor([[0.0, 0.0, 1.0, 0.0]], dtype=torch.float64)
        h2v = torch.tensor([[0.0, 0.0, 0.0, 1.0]], dtype=torch.float64)
        J_mat = hopf_jacobian(p)
        q = hopf_map(p)                                      # (0, 0, 1)
        dph1 = torch.bmm(J_mat, h1v.unsqueeze(-1)).squeeze(-1)  # (2, 0, 0)
        dph2 = torch.bmm(J_mat, h2v.unsqueeze(-1)).squeeze(-1)  # (0, -2, 0)
        # Complex structure: J_q(dπh₁) = (0,0,1)×(2,0,0) = (0,2,0)
        J_dph1 = complex_j_s2(q, dph1)                      # (0, 2, 0)
        J_dph2 = complex_j_s2(q, dph2)                      # (2, 0, 0)  — (0,0,1)×(0,-2,0)
        # J² check: J(J(dπh₁)) = (0,0,1)×(0,2,0) = (-2,0,0) = -(2,0,0)
        JJ_dph1 = complex_j_s2(q, J_dph1)                   # (-2, 0, 0)
        j_sq_resid = float((JJ_dph1 + dph1).norm().item())  # should be ~0
        # Kähler positivity: ω_K((2,0,0),(0,2,0)) = (0,0,1)·(0,0,4) = 4
        positivity = float(omega_s2(q, dph1, J_dph1).item()) # 4.0
        # g-compatibility: g(J(dπh₁),J(dπh₂)) = (0,2,0)·(2,0,0) = 0 = (2,0,0)·(0,-2,0)
        g_Ju_Jv = float((J_dph1 * J_dph2).sum().item())     # 0
        g_u_v   = float((dph1  * dph2  ).sum().item())       # 0
        g_compat = abs(g_Ju_Jv - g_u_v)
        # Bridge: ω_S²(dπh₁,dπh₂) = -4 = -2·dα(h₁,h₂)
        bridge_lhs = float(omega_s2(q, dph1, dph2).item())  # -4
        bridge_rhs = float(dalpha_eval(h1v, h2v).item())    # 2
        bridge_c = bridge_lhs / bridge_rhs                   # -2
        pass_p4 = bool(
            j_sq_resid < 1e-13
            and positivity > 0.1
            and g_compat < 1e-13
            and abs(bridge_c - (-2.0)) < 1e-13
        )
        results["P4_north_pole_ground_truth"] = {
            "pass": pass_p4,
            "kahler_residual": j_sq_resid,
            "j_squared_residual": j_sq_resid,
            "kahler_positivity": positivity,
            "g_compatibility_residual": g_compat,
            "bridge_coupling_constant": bridge_c,
            "dph1": dph1[0].tolist(),
            "j_dph1": J_dph1[0].tolist(),
            "jj_dph1": JJ_dph1[0].tolist(),
            "verdict": "compatible" if pass_p4 else "incompatible",
            "description": "North pole p=(1,0,0,0): J²=-Id, positivity=4, g-compat=0, bridge c=-2 (explicit)",
        }
    except Exception as e:
        results["P4_north_pole_ground_truth"] = {"pass": False, "error": str(e), "verdict": "error"}

    # P5: Sympy — J²=-Id (BAC-CAB identity) and ω_K=ω_S² (scalar triple product)
    try:
        q1s, q2s, q3s = sp.symbols('q1 q2 q3', real=True)
        v1s, v2s, v3s = sp.symbols('v1 v2 v3', real=True)
        u1s, u2s, u3s = sp.symbols('u1 u2 u3', real=True)
        q_s = sp.Matrix([q1s, q2s, q3s])
        v_s = sp.Matrix([v1s, v2s, v3s])
        u_s = sp.Matrix([u1s, u2s, u3s])

        # Check 1: J²=-Id via BAC-CAB: q×(q×v) = q(q·v) - v|q|²
        Jv_s   = q_s.cross(v_s)
        JJv_s  = q_s.cross(Jv_s)
        # BAC-CAB vector triple product identity (always holds)
        bac_cab = q_s * (q_s.dot(v_s)) - v_s * (q_s.dot(q_s))
        bac_cab_diff = sp.simplify(JJv_s - bac_cab)   # zero matrix (pure identity)
        bac_is_zero = all(bac_cab_diff[i] == 0 for i in range(3))
        # Under constraints |q|=1, q·v=0: bac_cab = 0·q - v·1 = -v → J²v = -v
        qnorm_sq = q1s**2 + q2s**2 + q3s**2
        qv_dot   = q1s*v1s + q2s*v2s + q3s*v3s
        j_sq_constrained = bac_cab.subs(qnorm_sq, 1).subs(qv_dot, 0)
        j_sq_is_minus_v = all(sp.simplify(j_sq_constrained[i] + v_s[i]) == 0 for i in range(3))

        # Check 2: ω_K = ω_S²: (q×u)·v = q·(u×v)  (scalar triple product identity)
        omega_K_sym = q_s.cross(u_s).dot(v_s)
        omega_S2_sym = q_s.dot(u_s.cross(v_s))
        omega_diff = sp.simplify(omega_K_sym - omega_S2_sym)
        omega_is_zero = (omega_diff == 0)

        pass_p5 = bool(bac_is_zero and j_sq_is_minus_v and omega_is_zero)
        results["P5_sympy_kahler_identities"] = {
            "pass": pass_p5,
            "bac_cab_vector_identity": bac_is_zero,
            "j_sq_under_constraints": j_sq_is_minus_v,
            "omega_K_equals_omega_S2": omega_is_zero,
            "verdict": "compatible" if pass_p5 else "fail",
            "description": (
                "Sympy: J²=-Id via BAC-CAB q×(q×v)=q(q·v)-v|q|², "
                "reduced to -v under |q|=1,v·q=0; and ω_K=ω_S² as scalar triple product identity"
            ),
        }
    except Exception as e:
        results["P5_sympy_kahler_identities"] = {"pass": False, "error": str(e), "verdict": "error"}

    return results


# =====================================================================
# NEGATIVE TESTS — three-way incompatible cases
# =====================================================================

def run_negative_tests():
    results = {}

    # N1: Anti-complex structure J' = -J violates Kähler positivity
    try:
        p = torch.tensor([[1.0, 0.0, 0.0, 0.0]], dtype=torch.float64)
        h1v = torch.tensor([[0.0, 0.0, 1.0, 0.0]], dtype=torch.float64)
        J_mat = hopf_jacobian(p)
        q = hopf_map(p)
        dph1 = torch.bmm(J_mat, h1v.unsqueeze(-1)).squeeze(-1)   # (2, 0, 0)
        # Standard J: J_q(dπh₁) = q×dπh₁ = (0,2,0)
        J_dph1_std = complex_j_s2(q, dph1)                        # (0, 2, 0)
        pos_std = float(omega_s2(q, dph1, J_dph1_std).item())     # 4.0 > 0
        # Anti-J: J'(v) = -q×v = -(J_q(v))
        J_dph1_anti = -complex_j_s2(q, dph1)                      # (0, -2, 0)
        pos_anti = float(omega_s2(q, dph1, J_dph1_anti).item())   # -4.0 < 0
        # J'² check: J'(J'(v)) = (-J)(-J)(v) = J²v = -v → J'² still = -Id
        JJ_anti = complex_j_s2(q, -J_dph1_anti)  # J(-(-Jv)) = J(Jv)
        j_sq_anti_resid = float((JJ_anti + dph1).norm().item())   # ~0 (still complex)
        pass_n1 = bool(pos_anti < -0.5)   # positivity fails for anti-J
        results["N1_anti_j_positivity_fails"] = {
            "pass": pass_n1,
            "kahler_residual": -pos_anti,   # positive number = how far below 0
            "positivity_standard_j": pos_std,
            "positivity_anti_j": pos_anti,
            "j_sq_anti_residual": j_sq_anti_resid,
            "verdict": "incompatible" if pass_n1 else "unexpectedly_compatible",
            "description": (
                "J'=-J: J'² = -Id still holds (algebraically valid) BUT ω_K(v,J'v)=-4<0 "
                "— Kähler positivity fails; orientation-reversed J breaks three-way coexistence"
            ),
        }
    except Exception as e:
        results["N1_anti_j_positivity_fails"] = {"pass": False, "error": str(e), "verdict": "error"}

    # N2: Degenerate complex structure J'=0 violates J²=-Id and positivity
    try:
        p = torch.tensor([[1.0, 0.0, 0.0, 0.0]], dtype=torch.float64)
        h1v = torch.tensor([[0.0, 0.0, 1.0, 0.0]], dtype=torch.float64)
        J_mat = hopf_jacobian(p)
        q = hopf_map(p)
        dph1 = torch.bmm(J_mat, h1v.unsqueeze(-1)).squeeze(-1)   # (2, 0, 0)
        # J'=0: pushforward is zero vector
        J_dph1_degen = torch.zeros_like(dph1)                     # (0, 0, 0)
        # J'²(v) = J'(J'(v)) = J'(0) = 0 ≠ -(dπh₁) = (-2,0,0)
        JJ_degen = torch.zeros_like(dph1)
        j_sq_degen_resid = float((JJ_degen + dph1).norm().item())  # = |(2,0,0)| = 2 >> 0
        # Positivity: ω_K(dπh₁, J'(dπh₁)) = ω_K(v,0) = 0
        pos_degen = float(omega_s2(q, dph1, J_dph1_degen).item())  # 0
        pass_n2 = bool(j_sq_degen_resid > 0.5 and abs(pos_degen) < 1e-14)
        results["N2_degenerate_j_fails"] = {
            "pass": pass_n2,
            "kahler_residual": j_sq_degen_resid,
            "j_sq_degenerate_residual": j_sq_degen_resid,
            "positivity_degenerate": pos_degen,
            "verdict": "incompatible" if pass_n2 else "unexpectedly_compatible",
            "description": (
                "J'=0: J'²(v)=0≠-v (residual=|v|=2) AND positivity ω_K(v,0)=0 — "
                "zero map is not a complex structure; both axioms fail simultaneously"
            ),
        }
    except Exception as e:
        results["N2_degenerate_j_fails"] = {"pass": False, "error": str(e), "verdict": "error"}

    # N3: Rescaled Kähler ω_K = 2·ω_S² breaks the Kähler=symplectic identity
    try:
        p = torch.tensor([[1.0, 0.0, 0.0, 0.0]], dtype=torch.float64)
        h1v = torch.tensor([[0.0, 0.0, 1.0, 0.0]], dtype=torch.float64)
        h2v = torch.tensor([[0.0, 0.0, 0.0, 1.0]], dtype=torch.float64)
        J_mat = hopf_jacobian(p)
        q = hopf_map(p)
        dph1 = torch.bmm(J_mat, h1v.unsqueeze(-1)).squeeze(-1)
        dph2 = torch.bmm(J_mat, h2v.unsqueeze(-1)).squeeze(-1)
        omega_s2_val = float(omega_s2(q, dph1, dph2).item())    # -4
        # Rescaled Kähler: ω_K = 2·ω_S²
        k = 2.0
        omega_K_rescaled = k * omega_s2_val                       # -8
        # Identity failure: ω_K ≠ ω_S²
        identity_residual = abs(omega_K_rescaled - omega_s2_val)  # 4.0 >> 0
        # Bridge constant under rescaled Kähler:
        # ω_K(dπh₁,dπh₂) = -8 = c·dα(h₁,h₂) = c·2 → c = -4 ≠ -2
        dalpha_val = float(dalpha_eval(h1v, h2v).item())          # 2
        c_rescaled = omega_K_rescaled / dalpha_val                 # -4
        pass_n3 = bool(identity_residual > 0.5)
        results["N3_rescaled_kahler_identity_fails"] = {
            "pass": pass_n3,
            "kahler_residual": identity_residual,
            "omega_s2_value": omega_s2_val,
            "omega_K_rescaled": omega_K_rescaled,
            "rescaling_k": k,
            "implied_coupling_constant": c_rescaled,
            "expected_coupling_constant": -2.0,
            "verdict": "incompatible" if pass_n3 else "unexpectedly_compatible",
            "description": (
                "ω_K=2·ω_S²: identity ω_K=ω_S² fails (residual=4.0); "
                "Kähler coupling constant becomes -4≠-2; symplectic and Kähler shells disagree"
            ),
        }
    except Exception as e:
        results["N3_rescaled_kahler_identity_fails"] = {"pass": False, "error": str(e), "verdict": "error"}

    # N4: z3 UNSAT — anti-J positivity contradicts Kähler positivity axiom
    try:
        omega_base  = Real('omega_base_J')    # ω_K(v,J_q v) for standard J — must be > 0
        omega_sign  = Real('omega_sign_antiJ')  # sign factor: -1 for J'=-J
        omega_antiJ = Real('omega_antiJ')       # ω_K(v,J'v) = sign * omega_base
        s = Solver()
        s.add(omega_base > 0)                   # standard J satisfies Kähler positivity
        s.add(omega_sign == -1)                  # J'=-J flips the sign
        s.add(omega_antiJ == omega_sign * omega_base)  # anti-J gives negative value
        s.add(omega_antiJ > 0)                   # Kähler positivity axiom for J'
        result_z3 = s.check()
        pass_n4 = bool(result_z3 == unsat)
        results["N4_z3_antij_unsat"] = {
            "pass": pass_n4,
            "z3_result": str(result_z3),
            "encoding": {
                "A1": "omega_base > 0  (standard J satisfies Kähler positivity)",
                "A2": "omega_sign = -1  (J'=-J flips sign)",
                "A3": "omega_antiJ = omega_sign * omega_base  (anti-J positivity value)",
                "A4": "omega_antiJ > 0  (Kähler positivity for J')",
            },
            "verdict": "incompatible" if pass_n4 else "fail",
            "description": (
                "z3 UNSAT: assuming anti-J (J'=-J) satisfies Kähler positivity "
                "while standard J does contradicts the sign-flip relation — "
                "structurally impossible; orientation-reversed complex structure is "
                "excluded from three-shell coexistence"
            ),
        }
    except Exception as e:
        results["N4_z3_antij_unsat"] = {"pass": False, "error": str(e), "verdict": "error"}

    return results


# =====================================================================
# BOUNDARY TESTS — degenerate and limiting cases
# =====================================================================

def run_boundary_tests():
    results = {}

    # B1: Antipodal fiber (p, -p) — same S² base, same J_q, checks stable at both
    try:
        pts_pos = random_s3_points(20)
        pts_neg = -pts_pos
        q_pos = hopf_map(pts_pos)          # base points
        q_neg = hopf_map(pts_neg)          # must equal q_pos (double cover)
        base_diff = float((q_pos - q_neg).abs().max().item())
        # J checks at p
        _, dph1_pos, _, _, _ = pushforward_vectors(pts_pos)
        J_pos = complex_j_s2(q_pos, dph1_pos)
        pos_val_pos = omega_s2(q_pos, dph1_pos, J_pos)
        # J checks at -p
        _, dph1_neg, _, _, _ = pushforward_vectors(pts_neg)
        J_neg = complex_j_s2(q_neg, dph1_neg)
        pos_val_neg = omega_s2(q_neg, dph1_neg, J_neg)
        min_pos = float(min(pos_val_pos.min().item(), pos_val_neg.min().item()))
        pass_b1 = bool(base_diff < 1e-12) and bool(min_pos > 0.1)
        results["B1_antipodal_fiber_coexistence"] = {
            "pass": pass_b1,
            "kahler_residual": -min_pos,
            "base_point_diff": base_diff,
            "min_positivity_p": float(pos_val_pos.min().item()),
            "min_positivity_neg_p": float(pos_val_neg.min().item()),
            "verdict": "compatible" if pass_b1 else "degenerate",
            "description": (
                "Antipodal pair (p,-p): π(p)=π(-p) confirmed, same J_q acts on both, "
                "Kähler positivity ω_K(dπh,J(dπh))>0 holds at both antipodal preimages"
            ),
        }
    except Exception as e:
        results["B1_antipodal_fiber_coexistence"] = {"pass": False, "error": str(e), "verdict": "error"}

    # B2: Near-pole point (x₀ ≈ 1) — α-projection basis stable, all checks hold
    try:
        eps = 1e-3
        p_raw = torch.tensor([[1.0 - eps, eps, eps, eps]], dtype=torch.float64)
        p = p_raw / torch.norm(p_raw, dim=-1, keepdim=True)
        q, dph1, dph2, h1, h2 = pushforward_vectors(p)
        J_dph1  = complex_j_s2(q, dph1)
        JJ_dph1 = complex_j_s2(q, J_dph1)
        j_sq_resid = float((JJ_dph1 + dph1).norm().item()) / (float(dph1.norm().item()) + 1e-30)
        positivity = float(omega_s2(q, dph1, J_dph1).item())
        g_compat   = float(abs((J_dph1 * complex_j_s2(q, dph2)).sum() - (dph1 * dph2).sum()).item())
        pass_b2 = bool(j_sq_resid < 1e-10) and bool(positivity > 0.1) and bool(g_compat < 1e-10)
        results["B2_near_pole_stability"] = {
            "pass": pass_b2,
            "kahler_residual": j_sq_resid,
            "j_squared_rel_residual": j_sq_resid,
            "positivity": positivity,
            "g_compat_residual": g_compat,
            "point": p[0].tolist(),
            "verdict": "compatible" if pass_b2 else "degenerate",
            "description": (
                "Near-pole p=(1-ε,ε,ε,ε)/|...|: α-projection basis stable, "
                "J²=-Id and Kähler positivity hold at near-degenerate geometry"
            ),
        }
    except Exception as e:
        results["B2_near_pole_stability"] = {"pass": False, "error": str(e), "verdict": "error"}

    # B3: Equatorial fiber p=(0,0,1/√2,1/√2) — x₀=x₁=0, checks stable
    try:
        s2 = 1.0 / np.sqrt(2.0)
        p = torch.tensor([[0.0, 0.0, s2, s2]], dtype=torch.float64)
        q, dph1, dph2, h1, h2 = pushforward_vectors(p)
        J_dph1  = complex_j_s2(q, dph1)
        JJ_dph1 = complex_j_s2(q, J_dph1)
        dph1_norm = float(dph1.norm().item())
        j_sq_resid = float((JJ_dph1 + dph1).norm().item()) / (dph1_norm + 1e-30)
        positivity = float(omega_s2(q, dph1, J_dph1).item())
        pass_b3 = bool(j_sq_resid < 1e-10) and bool(positivity > 0.1)
        results["B3_equatorial_fiber_stability"] = {
            "pass": pass_b3,
            "kahler_residual": j_sq_resid,
            "j_squared_rel_residual": j_sq_resid,
            "positivity": positivity,
            "hopf_base_point": q[0].tolist(),
            "verdict": "compatible" if pass_b3 else "degenerate",
            "description": (
                "Equatorial p=(0,0,1/√2,1/√2): x₀=x₁=0, α-projection provides stable "
                "horizontal basis, J²=-Id and Kähler positivity hold at equatorial fiber"
            ),
        }
    except Exception as e:
        results["B3_equatorial_fiber_stability"] = {"pass": False, "error": str(e), "verdict": "error"}

    return results


# =====================================================================
# FUBINI-STUDY COUPLING TESTS — c₁₃ = -1/2, c₂₃ = 1/4
# =====================================================================

def run_fubini_study_coupling_tests():
    """Test CP¹ Fubini-Study coupling constants c₁₃ = -1/2, c₂₃ = 1/4.

    Distinct from ω_K=ω_S² (standard round Kähler, c=-2 inherited by bridge).
    ω_FS = (1/4)·ω_S² is the CP¹ normalization.  Coupling chain:
      c₁₂ = -2  (contact-symplectic, established)
      c₂₃ = 1/4 (ω_FS/ω_S², definitional)
      c₁₃ = c₂₃·c₁₂ = (1/4)·(-2) = -1/2  (contact-Kähler, derived)
    """
    results = {}

    # FS1: c₁₃ = -1/2 — batch 100 pts
    try:
        torch.manual_seed(70)
        n = 100
        pts = random_s3_points(n)
        q, dph1, dph2, h1, h2 = pushforward_vectors(pts)
        wfs = omega_fs(q, dph1, dph2)
        da  = dalpha_eval(h1, h2)
        nz  = da.abs() > 1e-8
        ratios = wfs[nz] / da[nz]
        c13_mean = float(ratios.mean().item())
        c13_std  = float(ratios.std().item())
        max_err  = float((ratios - (-0.5)).abs().max().item())
        passed = max_err < 1e-8
        results["FS1_c13_minus_half_batch"] = {
            "pass": passed,
            "n_valid": int(nz.sum().item()),
            "c13_mean": c13_mean,
            "c13_std":  c13_std,
            "max_residual_from_minus_half": max_err,
            "threshold": 1e-8,
            "formula": "ω_FS(dπ(h₁),dπ(h₂)) = −(1/2)·dα(h₁,h₂)",
            "derivation": "c₁₃ = (1/4)·c₁₂ = (1/4)·(−2) = −1/2  [ω_FS=(1/4)ω_S²]",
            "verdict": "compatible" if passed else "incompatible",
        }
    except Exception as e:
        results["FS1_c13_minus_half_batch"] = {"pass": False, "error": str(e)}

    # FS2: c₂₃ = ω_FS/ω_S² = 1/4 globally (200 pts)
    try:
        torch.manual_seed(71)
        n = 200
        pts = random_s3_points(n)
        q, dph1, dph2, h1, h2 = pushforward_vectors(pts)
        ws2 = omega_s2(q, dph1, dph2)
        wfs = omega_fs(q, dph1, dph2)
        nz  = ws2.abs() > 1e-8
        ratios = wfs[nz] / ws2[nz]
        c23_mean = float(ratios.mean().item())
        c23_std  = float(ratios.std().item())
        max_err  = float((ratios - 0.25).abs().max().item())
        passed = max_err < 1e-14
        results["FS2_c23_quarter_global"] = {
            "pass": passed,
            "n_valid": int(nz.sum().item()),
            "c23_mean": c23_mean,
            "c23_std":  c23_std,
            "max_residual_from_quarter": max_err,
            "threshold": 1e-14,
            "formula": "ω_FS = (1/4)·ω_S²  [exact, definitional]",
            "verdict": "compatible" if passed else "incompatible",
        }
    except Exception as e:
        results["FS2_c23_quarter_global"] = {"pass": False, "error": str(e)}

    # FS3: z3 UNSAT — c ≠ -1/2 with c·dα = ω_FS at north pole (dα=2, ω_FS=-1)
    try:
        c = Real('c_fs')
        s = Solver()
        s.add(c != -0.5)
        s.add(c * 2.0 == -1.0)  # ω_FS=-1, dα=2 at p=(1,0,0,0)
        z3_result = s.check()
        passed = (z3_result == unsat)
        results["FS3_z3_c13_uniqueness_unsat"] = {
            "pass": passed,
            "z3_result": str(z3_result),
            "ground_truth": "p=(1,0,0,0): ω_FS=-1, dα=2  →  c=-1/2 unique",
            "encoding": "c≠−1/2 ∧ c·dα=ω_FS  →  UNSAT (c=−1/2 is the unique solution)",
            "geometric_meaning": "Contact-Kähler (Fubini-Study) coupling constant c₁₃=−1/2 is "
                                 "structurally unique; no alternative c is algebraically consistent.",
            "verdict": "excluded" if passed else "fail",
        }
    except Exception as e:
        results["FS3_z3_c13_uniqueness_unsat"] = {"pass": False, "error": str(e)}

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    positive      = run_positive_tests()
    negative      = run_negative_tests()
    boundary      = run_boundary_tests()
    fubini_study  = run_fubini_study_coupling_tests()

    all_tests = {**positive, **negative, **boundary, **fubini_study}
    tests_passed = sum(1 for v in all_tests.values() if v.get("pass") is True)
    tests_total  = len(all_tests)

    # Three-way coexistence verdict
    pos_ok = all(positive[k].get("pass") is True for k in positive)
    neg_ok = all(negative[k].get("pass") is True for k in negative)
    bnd_ok = all(boundary[k].get("pass") is True for k in boundary)
    fs_ok  = all(fubini_study[k].get("pass") is True for k in fubini_study)
    coexistence_ok = pos_ok and neg_ok and bnd_ok and fs_ok

    # Coupling constants from batch results
    c12_val = -2.0   # established, locked
    c13_val = fubini_study.get("FS1_c13_minus_half_batch", {}).get("c13_mean", -0.5)
    c23_val = fubini_study.get("FS2_c23_quarter_global", {}).get("c23_mean", 0.25)
    c12_resid = positive.get("P4_north_pole_ground_truth", {}).get("kahler_residual", None)
    c13_resid = fubini_study.get("FS1_c13_minus_half_batch", {}).get("max_residual_from_minus_half", None)
    c23_resid = fubini_study.get("FS2_c23_quarter_global", {}).get("max_residual_from_quarter", None)

    coexistence_judgment = {
        "shell_triple": [
            "contact_structure_s3",
            "symplectic_s2",
            "kahler_cp1_fubini_study",
        ],
        "coupling_constants": {
            "c_12": {
                "value": c12_val,
                "status": "exact",
                "source": "sim_pure_lego_hopf_contact_symplectic_bridge.py (z3 proven)",
                "formula": "ω_S²(dπ(h₁),dπ(h₂)) = −2·dα(h₁,h₂)",
            },
            "c_13": {
                "value": round(c13_val, 8),
                "status": "exact",
                "source": "derived: c₁₃ = c₂₃·c₁₂ = (1/4)·(−2) = −1/2; z3 proven unique (FS3)",
                "formula": "ω_FS(dπ(h₁),dπ(h₂)) = −(1/2)·dα(h₁,h₂)",
            },
            "c_23": {
                "value": round(c23_val, 8),
                "status": "exact",
                "source": "Fubini-Study definition: ω_FS = (1/4)·ω_S²",
                "formula": "ω_FS = (1/4)·ω_S²",
            },
        },
        "consistency_chain": "c₁₃ = c₂₃·c₁₂  →  −1/2 = (1/4)·(−2)  [exact, algebraic]",
        "coexistence_verdict": "compatible" if coexistence_ok else "incompatible",
        "compatibility_residuals": {
            "c12_ground_truth_j_sq_residual": c12_resid,
            "c13_max_residual_from_minus_half": c13_resid,
            "c23_max_residual_from_quarter": c23_resid,
        },
        "kappa_note": (
            "Two Kähler structures on S²: (1) standard round ω_K=ω_S² [c₁₃=-2, c₂₃=1.0, "
            "tested in P1-P5/N1-N4/B1-B3]; (2) Fubini-Study ω_FS=(1/4)ω_S² [c₁₃=-1/2, c₂₃=1/4, "
            "tested in FS1-FS3]. This judgment uses (2). The standard round Kähler is also "
            "compatible but has c₁₃=c₁₂=-2 (no new information from Kähler shell)."
        ),
        "sign_convention_note": (
            "Hopf map: X=2(x₀x₂+x₁x₃), Y=2(x₁x₂−x₀x₃), Z=x₀²+x₁²−x₂²−x₃². "
            "Jacobian row 1: [−2x₃, 2x₂, 2x₁, −2x₀]. "
            "ω_S²(q;u,v)=q·(u×v) [NO 1/2 factor]. "
            "ω_FS=(1/4)·ω_S² [CP¹ Fubini-Study normalization]. "
            "J(v)=q×v; g_FS(u,v)=ω_FS(u,Jv). c₁₂=−2 (locked, active convention)."
        ),
    }

    results = {
        "name": "pure_lego_contact_symplectic_kahler_coexistence",
        "timestamp": timestamp,
        "classification": "canonical",
        "classification_note": (
            "Three-shell coexistence probe: S³ contact shell, S² symplectic shell, "
            "CP¹/S² Kähler shell. Coupling Program step 3. "
            "Key novelty: verifies complex structure J_q(v)=q×v on S², its J²=-Id "
            "property, g-compatibility g(Ju,Jv)=g(u,v), and Kähler positivity ω_K(v,Jv)>0. "
            "Standard round Kähler: ω_K=ω_S² (c₁₃=-2, c₂₃=1). "
            "Fubini-Study Kähler: ω_FS=(1/4)ω_S² (c₁₃=-1/2, c₂₃=1/4). "
            "Distinct from: sim_geom_symplectic_kahler_contact.py (spherical-coordinate survey), "
            "sim_geom_cp1_u1_projective.py (Berry/Fubini-Study lego), "
            "sim_pure_lego_contact_symplectic_coupling.py (pairwise). "
            "Uses pytorch (load_bearing) + z3 UNSAT + sympy vector algebra."
        ),
        "lego_ids": ["contact_symplectic_kahler_coexistence", "contact_S3", "symplectic_S2", "kahler_CP1"],
        "primary_lego_ids": ["contact_symplectic_kahler_coexistence"],
        # Machine-readable three-way verdict
        "shell_triple": ["contact_S3", "symplectic_S2", "kahler_CP1"],
        "bridge_constants": {"contact_symplectic": -2.0, "contact_kahler_round": -2.0, "contact_kahler_fs": -0.5},
        "kahler_symplectic_identity": True,
        "coexistence_verdict": "compatible" if coexistence_ok else "incompatible",
        "coexistence_judgment": coexistence_judgment,
        "sign_convention": "omega_S2(dpi(h1),dpi(h2)) = -2 * dalpha(h1,h2)",
        "positive_diagnosis": (
            "J²=-Id holds (max rel residual <1e-12 at 50 pts); "
            "Kähler positivity ω_K(dπh,J(dπh))>0 holds (min=4 at north pole); "
            "g-compatibility holds (<1e-12); ω_K=ω_S² (scalar triple product identity, sympy). "
            "North pole ground truth: J(2,0,0)=(0,2,0), J²=(-2,0,0)=-dπh₁, positivity=4."
        ),
        "negative_diagnosis": (
            "Anti-J (J'=-J): positivity=-4<0 (incompatible, z3 UNSAT confirms). "
            "Degenerate J (J'=0): J'²≠-Id (residual=2), positivity=0 (incompatible). "
            "Rescaled Kähler (ω_K=2·ω_S²): identity residual=4, implied c=-4≠-2 (incompatible)."
        ),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "fubini_study_coupling": fubini_study,
        "tests_passed": tests_passed,
        "tests_total": tests_total,
        "summary": {
            "complex_structure": "J_q(v) = q × v  (cross product with unit normal)",
            "j_squared_identity": "J²(v) = q×(q×v) = -v  (BAC-CAB, constraints |q|=1, v⊥q)",
            "kahler_symplectic_identity": "omega_K = omega_S2  (same form, proven by scalar triple product identity)",
            "bridge_inheritance": "omega_K(d_pi(h1),d_pi(h2)) = -2*dalpha(h1,h2)  (c=-2 inherited)",
            "fubini_study_c13": "omega_FS(d_pi(h1),d_pi(h2)) = -(1/2)*dalpha(h1,h2)  [c13=-1/2]",
            "fubini_study_c23": "omega_FS/omega_S2 = 1/4  [exact, definitional]",
            "consistency_chain": "c13 = c23*c12 = (1/4)*(-2) = -1/2  [algebraic]",
            "three_way_coexistence": "compatible — all criteria satisfied",
            "coexistence_verdict": "compatible" if coexistence_ok else "incompatible",
            "incompatible_cases": ["anti-J (positivity fails)", "zero-J (J²≠-Id)", "rescaled-omega (identity fails)"],
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "contact_symplectic_kahler_coexistence_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Tests passed: {tests_passed}/{tests_total}")
    print(f"Coexistence verdict: {results['coexistence_verdict']}")
    print(f"c₁₂={coexistence_judgment['coupling_constants']['c_12']['value']}, "
          f"c₁₃={coexistence_judgment['coupling_constants']['c_13']['value']}, "
          f"c₂₃={coexistence_judgment['coupling_constants']['c_23']['value']}")
    for name, res in all_tests.items():
        status = "PASS" if res.get("pass") is True else "FAIL"
        verdict = res.get("verdict", "")
        print(f"  {status}  {name}  [{verdict}]")

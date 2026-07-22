#!/usr/bin/env python3
"""Geometry restriction probe: Bures metric to Fubini--Study metric plus Berry
curvature.

Object: the MIXED layer is the Bloch ball of 2x2 density operators, carrying
the Bures (fidelity/SLD) metric g^B.  The PURE boundary is CP^1, the pure-state
sphere, carrying the Fubini--Study metric g^FS and Berry curvature F via the
Provost-Vallee quantum geometric tensor Q = g^FS + (i/2) F.  The proposed
restriction map is the r->1 boundary limit of g^B, compared against g^FS
computed directly from the pure-state family |psi(theta,phi)>.

This is the GEOMETRY companion to the committed pure_to_vn.py entropy arrow
(same C^2 object, same mixed->pure boundary, geometric rather than entropic
readout).

classification = "tool_lego_fit_probe"; promotion_allowed = False;
ordering_status = "PROPOSED not canon".  This finite probe does not settle a
canonical layer ordering or support bridge/axis/canonical promotion.

HONESTY NOTE (computed, not assumed): the build card for this probe expected
the restriction constant g^B|_pure = (1/4) g^FS.  That figure holds under one
common convention where g^FS is taken to be the bare round-sphere metric
dtheta^2+sin^2(theta) dphi^2.  This probe instead computes g^FS directly from
the Provost-Vallee quantum geometric tensor Q = <dpsi|dpsi> - |<psi|dpsi>|^2,
exactly as specified for part (a) ("FS via Q's real part").  Under that
specific pairing -- Bures via the exact Uhlmann-fidelity Taylor expansion,
restricted to the same-radius (tangential-only) sphere, versus g^FS = Re(Q) --
the two tensors come out numerically and symbolically IDENTICAL at the pure
boundary (ratio 1, not 1/4).  This is cross-checked three independent ways
below (symbolic Hessian of the closed-form Bures distance, symbolic
Provost-Vallee Q, and a numeric finite-difference sweep) and is also the
standard quantum-metrology identity F_Q = 4 g^FS for the SLD/QFI (Bures = QFI/4
=> Bures|_pure = g^FS).  The computed value is reported as-is; the 1/4 figure
is not forced onto the result.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import sympy as sp
from z3 import Function, RealSort, RealVal, Solver, sat, unsat

try:
    import cvc5
except ImportError:  # Recorded honestly below; z3 remains the primary proof leg.
    cvc5 = None


classification = "tool_lego_fit_probe"
promotion_allowed = False
ordering_status = "PROPOSED not canon"
TOL = 1.0e-8

TOOL_MANIFEST = {
    "sympy": {"tried": True, "used": True,
              "reason": "Exact Hessian of the closed-form Uhlmann-fidelity Bures distance and exact Provost-Vallee QGT differentiation."},
    "numpy": {"tried": True, "used": True,
              "reason": "Finite-difference Bures-Hessian sweep over sampled Bloch-ball and pure-boundary points, plus the interior closed-form cross-check."},
    "z3": {"tried": True, "used": True,
           "reason": "Primary SMT contradiction: one function of the (real, symmetric) Bures/FS metric components cannot return both signs of Berry curvature."},
    "cvc5": {"tried": cvc5 is not None, "used": False,
             "reason": "Cross-check attempted when bindings are available; updated at runtime with its actual solver result."},
    "jax": {"tried": False, "used": False,
            "reason": "Queued: memory usage above the 0.40 build-time threshold (heavy engines gated); explicitly not run."},
    "julia": {"tried": False, "used": False,
              "reason": "Queued: memory usage above the 0.40 build-time threshold (heavy engines gated); explicitly not run."},
}

TOOL_INTEGRATION_DEPTH = {
    "sympy": "load_bearing",
    "numpy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": None,
    "jax": None,
    "julia": None,
}


# ---------------------------------------------------------------------------
# Numeric primitives (Bloch ball, Uhlmann fidelity, Bures distance).
# ---------------------------------------------------------------------------

def bloch_unit(theta: float, phi: float) -> np.ndarray:
    return np.array([
        math.sin(theta) * math.cos(phi),
        math.sin(theta) * math.sin(phi),
        math.cos(theta),
    ])


def fidelity_bloch(a: np.ndarray, b: np.ndarray) -> float:
    """Nielsen-Chuang closed form for 2x2 density-matrix fidelity in Bloch coords."""
    norm_a2 = float(np.dot(a, a))
    norm_b2 = float(np.dot(b, b))
    radicand = (1.0 - norm_a2) * (1.0 - norm_b2)
    return 0.5 * (1.0 + float(np.dot(a, b)) + math.sqrt(max(radicand, 0.0)))


def bures_d2(a: np.ndarray, b: np.ndarray) -> float:
    fidelity = min(max(fidelity_bloch(a, b), 0.0), 1.0)
    return 2.0 * (1.0 - math.sqrt(fidelity))


def numeric_metric_tensor(func, dim: int, h: float = 2.0e-3) -> np.ndarray:
    """Metric tensor g_ij such that func(d) = g_ij d^i d^j + O(d^3), for a
    scalar squared-distance func: R^dim -> R with func(0)=0 and a minimum at 0
    (odd terms vanish).  g_ij = (1/2) * central-difference-Hessian(func)_ij,
    since d^T Hess(d^T G d) d = 2 d^T G d (the raw second-derivative Hessian is
    twice the metric-tensor coefficient, not equal to it)."""
    hessian = np.zeros((dim, dim))
    for i in range(dim):
        ei = np.zeros(dim)
        ei[i] = h
        hessian[i, i] = (func(ei) - 2.0 * func(np.zeros(dim)) + func(-ei)) / (h * h)
    for i in range(dim):
        for j in range(i + 1, dim):
            ei, ej = np.zeros(dim), np.zeros(dim)
            ei[i], ej[j] = h, h
            value = (func(ei + ej) - func(ei - ej) - func(-ei + ej) + func(-ei - ej)) / (4.0 * h * h)
            hessian[i, j] = value
            hessian[j, i] = value
    return 0.5 * hessian


def perturbed_angular_point(r: float, theta: float, phi: float, d: np.ndarray) -> np.ndarray:
    """Bloch vector at (r, theta+d_theta, phi+d_phi); d=[dtheta, dphi]."""
    dtheta, dphi = d
    return r * bloch_unit(theta + dtheta, phi + dphi)


def perturbed_mixed_point(r: float, theta: float, phi: float, d: np.ndarray) -> np.ndarray:
    """Bloch vector at (r+d_r, theta+d_theta, phi+d_phi); d=[dr, dtheta, dphi]."""
    dr, dtheta, dphi = d
    return (r + dr) * bloch_unit(theta + dtheta, phi + dphi)


# ---------------------------------------------------------------------------
# Symbolic (sympy exact) layer.
# ---------------------------------------------------------------------------

def symbolic_bures_boundary_metric(theta0: sp.Expr) -> dict[str, Any]:
    """Metric tensor g^B_ij = (1/2) Hessian_ij of the closed-form Bures
    distance restricted to the r=1 sphere (same-radius pair, so the divergent
    radial 1/(1-r^2) term never appears; the (1/2) is required because
    D_B^2(d)=g_ij d^i d^j directly, so the raw second derivative is 2 g_ij, not
    g_ij), evaluated exactly at phi0=0 (g^FS/g^B here do not depend on phi)."""
    dtheta, dphi = sp.symbols("dtheta dphi", real=True)

    def unit(t: sp.Expr, p: sp.Expr) -> sp.Matrix:
        return sp.Matrix([sp.sin(t) * sp.cos(p), sp.sin(t) * sp.sin(p), sp.cos(t)])

    a = unit(theta0, sp.Integer(0))
    b = unit(theta0 + dtheta, dphi)
    cos_gamma = sp.simplify((a.T * b)[0])
    fidelity = (1 + cos_gamma) / 2
    d2 = 2 * (1 - sp.sqrt(fidelity))
    hessian = sp.hessian(d2, (dtheta, dphi))
    hessian0 = sp.simplify(sp.Rational(1, 2) * hessian.subs({dtheta: 0, dphi: 0}))
    return {
        "theta0": str(theta0),
        "g_tt": sp.nsimplify(hessian0[0, 0]),
        "g_pp": sp.nsimplify(hessian0[1, 1]),
        "g_tp": sp.nsimplify(hessian0[0, 1]),
    }


def symbolic_qgt() -> dict[str, Any]:
    """Provost-Vallee quantum geometric tensor Q=g^FS+(i/2)F for the qubit
    coherent state |psi(theta,phi)>=cos(theta/2)|0>+e^{i phi}sin(theta/2)|1>,
    and for its coordinatewise complex-conjugate family chi=psi*."""
    theta, phi = sp.symbols("theta phi", real=True)

    def qgt_component(state: sp.Matrix, mu: sp.Symbol, nu: sp.Symbol) -> sp.Expr:
        d_mu = state.diff(mu)
        d_nu = state.diff(nu)
        inner = (d_mu.conjugate().T * d_nu)[0]
        # Provost-Vallee: Q_munu = <d_mu psi|d_nu psi> - <d_mu psi|psi><psi|d_nu psi>.
        # NOT <psi|d_mu psi><psi|d_nu psi> -- those two agree only when the
        # overlap is real, which it is not here (it is purely imaginary), so
        # using the wrong pairing previously corrupted the phi-phi component.
        correction = (d_mu.conjugate().T * state)[0] * (state.conjugate().T * d_nu)[0]
        return sp.simplify(inner - correction)

    psi = sp.Matrix([sp.cos(theta / 2), sp.exp(sp.I * phi) * sp.sin(theta / 2)])
    chi = sp.Matrix([sp.cos(theta / 2), sp.exp(-sp.I * phi) * sp.sin(theta / 2)])  # coordinatewise conjugate family

    q_tt = qgt_component(psi, theta, theta)
    q_pp = qgt_component(psi, phi, phi)
    q_tp = qgt_component(psi, theta, phi)

    q_tt_chi = qgt_component(chi, theta, theta)
    q_pp_chi = qgt_component(chi, phi, phi)
    q_tp_chi = qgt_component(chi, theta, phi)

    g_fs_tt = sp.simplify(sp.re(q_tt))
    g_fs_pp = sp.simplify(sp.re(q_pp))
    g_fs_tp = sp.simplify(sp.re(q_tp))
    berry_f = sp.simplify(2 * sp.im(q_tp))
    berry_f_chi = sp.simplify(2 * sp.im(q_tp_chi))

    return {
        "g_fs_tt": g_fs_tt, "g_fs_pp": g_fs_pp, "g_fs_tp": g_fs_tp,
        "berry_f": berry_f, "berry_f_chi": berry_f_chi,
        "g_fs_tt_chi": sp.simplify(sp.re(q_tt_chi)), "g_fs_pp_chi": sp.simplify(sp.re(q_pp_chi)),
        "g_fs_tp_chi": sp.simplify(sp.re(q_tp_chi)),
        "off_diagonal_is_zero": bool(sp.simplify(g_fs_tp) == 0),
        "conjugate_shares_real_part": bool(sp.simplify(g_fs_tt - sp.re(q_tt_chi)) == 0
                                            and sp.simplify(g_fs_pp - sp.re(q_pp_chi)) == 0),
        "conjugate_flips_berry": bool(sp.simplify(berry_f + berry_f_chi) == 0 and berry_f != 0),
    }


# ---------------------------------------------------------------------------
# SMT: Berry curvature is not a function of the real Bures/FS components.
# ---------------------------------------------------------------------------

def z3_berry_irreducibility(g_tt: float, g_pp: float, g_tp: float, f_plus: float, f_minus: float) -> dict[str, str]:
    recover_f = Function("recover_berry_from_bures", RealSort(), RealSort(), RealSort(), RealSort())
    gtt, gpp, gtp = RealVal(str(g_tt)), RealVal(str(g_pp)), RealVal(str(g_tp))
    fplus, fminus = RealVal(str(f_plus)), RealVal(str(f_minus))
    solver = Solver()
    # Same real, symmetric Bures/FS metric components (shared by psi and its
    # conjugate family chi=psi*) must recover both +F and -F.
    solver.add(recover_f(gtt, gpp, gtp) == fplus, recover_f(gtt, gpp, gtp) == fminus)
    result = solver.check()
    assert result == unsat
    relaxed = Solver()
    relaxed.add(recover_f(gtt, gpp, gtp) == fplus)
    relaxed_result = relaxed.check()
    assert relaxed_result == sat
    return {"encoding": "same real (g_tt,g_pp,g_tp) shared by conjugate families psi,chi must recover both +F and -F",
            "result": str(result), "erased_constraint_result": str(relaxed_result)}


def cvc5_berry_irreducibility(g_tt: float, g_pp: float, g_tp: float, f_plus: float, f_minus: float) -> dict[str, str]:
    if cvc5 is None:
        return {"result": "not_run", "erased_constraint_result": "not_run", "reason": "cvc5 Python bindings unavailable"}
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_UFLRA")
        real = solver.getRealSort()
        function = solver.mkConst(solver.mkFunctionSort([real, real, real], real), "recover_berry_from_bures")
        gtt, gpp, gtp = solver.mkReal(str(g_tt)), solver.mkReal(str(g_pp)), solver.mkReal(str(g_tp))
        fplus, fminus = solver.mkReal(str(f_plus)), solver.mkReal(str(f_minus))
        app = solver.mkTerm(cvc5.Kind.APPLY_UF, function, gtt, gpp, gtp)
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, app, fplus))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, app, fminus))
        result = solver.checkSat()
        if not result.isUnsat():
            raise RuntimeError(f"expected unsat, got {result}")
        relaxed = cvc5.Solver()
        relaxed.setLogic("QF_UFLRA")
        real2 = relaxed.getRealSort()
        function2 = relaxed.mkConst(relaxed.mkFunctionSort([real2, real2, real2], real2), "recover_berry_from_bures_relaxed")
        gtt2, gpp2, gtp2 = relaxed.mkReal(str(g_tt)), relaxed.mkReal(str(g_pp)), relaxed.mkReal(str(g_tp))
        app2 = relaxed.mkTerm(cvc5.Kind.APPLY_UF, function2, gtt2, gpp2, gtp2)
        relaxed.assertFormula(relaxed.mkTerm(cvc5.Kind.EQUAL, app2, relaxed.mkReal(str(f_plus))))
        relaxed_result = relaxed.checkSat()
        if not relaxed_result.isSat():
            raise RuntimeError(f"expected sat after erasure, got {relaxed_result}")
        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_MANIFEST["cvc5"]["reason"] = "Cross-check SMT contradiction returned unsat; erased-constraint control returned sat."
        TOOL_INTEGRATION_DEPTH["cvc5"] = "supportive"
        return {"result": str(result), "erased_constraint_result": str(relaxed_result),
                "reason": "same conjugate-pair Bures/FS metric-component contradiction"}
    except Exception as error:  # No false engine-use claim if the local API differs.
        TOOL_MANIFEST["cvc5"]["used"] = False
        TOOL_MANIFEST["cvc5"]["reason"] = f"Bindings available but cross-check did not run successfully: {error}"
        return {"result": "not_run", "erased_constraint_result": "not_run", "reason": str(error)}


def main() -> None:
    # --- (a) RESTRICTION: symbolic Bures-at-boundary vs Provost-Vallee FS ---
    theta_symbols = [sp.pi / 6, sp.pi / 4, sp.pi / 3, sp.pi / 2, 2 * sp.pi / 3]
    boundary_checks = [symbolic_bures_boundary_metric(t) for t in theta_symbols]

    qgt = symbolic_qgt()
    theta_sym = sp.symbols("theta", real=True)
    g_fs_tt_fn = sp.lambdify(theta_sym, qgt["g_fs_tt"], "math")
    g_fs_pp_fn = sp.lambdify(theta_sym, qgt["g_fs_pp"], "math")
    berry_fn = sp.lambdify(theta_sym, qgt["berry_f"], "math")

    exact_deviations = []
    exact_ratios = []
    for entry, t in zip(boundary_checks, theta_symbols):
        t_float = float(t)
        g_tt_bures = float(entry["g_tt"])
        g_pp_bures = float(entry["g_pp"])
        g_tt_fs = g_fs_tt_fn(t_float)
        g_pp_fs = g_fs_pp_fn(t_float)
        exact_deviations.append(abs(g_tt_bures - g_tt_fs))
        if abs(g_pp_fs) > 1.0e-12:
            exact_deviations.append(abs(g_pp_bures - g_pp_fs))
            exact_ratios.append(g_pp_bures / g_pp_fs)
        exact_ratios.append(g_tt_bures / g_tt_fs)
        entry["g_tp"] = float(entry["g_tp"])  # off-diagonal, expect 0

    # --- (a) sampled numeric cross-check via finite-difference Hessian ---
    sampled_thetas = np.linspace(0.05, math.pi - 0.05, 25)
    sampled_deviations = []
    sampled_ratios = []
    bures_antisym_max = 0.0
    for theta in sampled_thetas:
        def d2(d: np.ndarray, theta=theta) -> float:
            a = perturbed_angular_point(1.0, theta, 0.0, np.zeros(2))
            b = perturbed_angular_point(1.0, theta, 0.0, d)
            return bures_d2(a, b)

        hessian = numeric_metric_tensor(d2, 2, h=2.0e-3)
        bures_antisym_max = max(bures_antisym_max, float(abs(hessian[0, 1] - hessian[1, 0]) / 2.0))
        g_tt_fs, g_pp_fs = float(g_fs_tt_fn(theta)), float(g_fs_pp_fn(theta))
        sampled_deviations.append(float(abs(hessian[0, 0] - g_tt_fs)))
        if g_pp_fs > 1.0e-6:
            sampled_deviations.append(float(abs(hessian[1, 1] - g_pp_fs)))
            sampled_ratios.append(float(hessian[1, 1] / g_pp_fs))
        sampled_ratios.append(float(hessian[0, 0] / g_tt_fs))

    max_dev = float(max(exact_deviations + sampled_deviations))
    proportionality_constant = float(np.mean(exact_ratios + sampled_ratios))
    proportionality_spread = float(max(abs(r - proportionality_constant) for r in exact_ratios + sampled_ratios))

    # --- MIXED-layer interior closed-form cross-check (Bloch-ball, r<1) ---
    interior_points = [(0.3, math.pi / 5, 0.7), (0.6, math.pi / 3, 2.1), (0.85, 2 * math.pi / 3, 4.0)]
    interior_deviations = []
    for r0, theta0, phi0 in interior_points:
        def d2_mixed(d: np.ndarray, r0=r0, theta0=theta0, phi0=phi0) -> float:
            a = perturbed_mixed_point(r0, theta0, phi0, np.zeros(3))
            b = perturbed_mixed_point(r0, theta0, phi0, d)
            return bures_d2(a, b)

        hessian3 = numeric_metric_tensor(d2_mixed, 3, h=2.0e-3)
        expected_rr = 1.0 / (4.0 * (1.0 - r0 * r0))
        expected_tt = r0 * r0 / 4.0
        expected_pp = r0 * r0 * math.sin(theta0) ** 2 / 4.0
        interior_deviations.append(abs(hessian3[0, 0] - expected_rr))
        interior_deviations.append(abs(hessian3[1, 1] - expected_tt))
        interior_deviations.append(abs(hessian3[2, 2] - expected_pp))
    interior_max_dev = float(max(interior_deviations))
    # Finite-difference truncation floor at h=2e-3 is ~1e-5-1e-4 (this check is
    # a numeric sanity cross-check of the closed form, not the core (a)/(c)
    # boundary-restriction claim, which is covered by max_dev above at
    # near-machine precision via the exact/lambdified boundary comparison).
    interior_closed_form_confirmed = interior_max_dev < 5.0e-4

    # --- (b) Berry curvature value + irreducibility witness ---
    berry_at_pi_2 = float(berry_fn(math.pi / 2))
    berry_expected_monopole = 0.5 * math.sin(math.pi / 2)
    berry_matches_monopole = abs(berry_at_pi_2 - berry_expected_monopole) < TOL

    conjugate_g_tt = float(g_fs_tt_fn(math.pi / 2))
    conjugate_g_pp = float(g_fs_pp_fn(math.pi / 2))
    conjugate_g_tp = 0.0
    f_plus = berry_at_pi_2
    f_minus = -berry_at_pi_2

    z3_result = z3_berry_irreducibility(conjugate_g_tt, conjugate_g_pp, conjugate_g_tp, f_plus, f_minus)
    cvc5_result = cvc5_berry_irreducibility(conjugate_g_tt, conjugate_g_pp, conjugate_g_tp, f_plus, f_minus)

    # --- (c) control: the real part IS recoverable (genuine flip vs (b)) ---
    # Gated on the boundary restriction (near-machine-precision exact+sampled
    # comparison), which is the object part (c) actually asks about; the
    # interior mixed-layer sweep above is a separate, FD-precision-limited
    # sanity check on the closed form and is reported on its own.
    control_real_recoverable = max_dev < 1.0e-6 and interior_closed_form_confirmed
    berry_irreducible = (qgt["conjugate_shares_real_part"] and qgt["conjugate_flips_berry"]
                          and z3_result["result"] == "unsat" and z3_result["erased_constraint_result"] == "sat"
                          and bures_antisym_max < 1.0e-6)

    core_ok = (control_real_recoverable and berry_matches_monopole and qgt["off_diagonal_is_zero"]
               and z3_result["result"] == "unsat" and z3_result["erased_constraint_result"] == "sat")

    verdict = "FAILED"
    notes = [
        "Finite/sampled+exact probe only; proposed layer ordering is not canon.",
        "Bures via Hessian of the closed-form Uhlmann-fidelity Bures distance D_B^2=2(1-sqrt(F)), F=(1/2)(1+a.b+sqrt((1-|a|^2)(1-|b|^2))) (Nielsen-Chuang closed form for 2x2 density operators).",
        "Fubini-Study/Berry via Provost-Vallee Q=<dpsi|dpsi>-|<psi|dpsi>|^2 on |psi(theta,phi)>=cos(theta/2)|0>+e^{i phi}sin(theta/2)|1>.",
        f"Computed proportionality constant (Bures at r=1 tangential vs Re(Q)) = {proportionality_constant:.6f}, "
        "not the frequently-cited 1/4 -- see module docstring HONESTY NOTE for the convention this depends on.",
        "Berry irreducibility witness: psi(theta,phi) and its coordinatewise conjugate family chi=psi* share identical (g_tt,g_pp,g_tp) at every theta but have Berry curvature F and -F respectively.",
    ]
    if core_ok and berry_irreducible:
        verdict = "BERRY_IRREDUCIBLE"
    elif core_ok and not berry_irreducible:
        verdict = "BY_CONSTRUCTION"
        notes.append("The conjugate-pair witness did not genuinely separate F from the real Bures/FS components; directionality would be by construction.")
    else:
        notes.append("At least one required check failed; inspect check details.")

    result = {
        "schema_version": "1.0",
        "mixed_layer": "2x2 density operators (Bloch ball, 0<=r<1), Bures (fidelity/SLD) metric g^B; closed form ds_B^2=(1/4)[dr^2/(1-r^2)+r^2(dtheta^2+sin^2(theta)dphi^2)].",
        "pure_layer": "CP^1, the pure-state sphere (r=1), Fubini-Study metric g^FS and Berry curvature F via the Provost-Vallee quantum geometric tensor Q=g^FS+(i/2)F.",
        "bures_restricts_to_fs": {
            "proportionality_constant": proportionality_constant,
            "proportionality_spread": proportionality_spread,
            "max_dev": max_dev,
            "prompt_expected_constant": 0.25,
            "convention_note": "Computed with g^FS=Re(Q) (Provost-Vallee), Bures via the exact Uhlmann-fidelity Hessian restricted to the same-radius (r=1) sphere. Under this pairing the two tensors coincide (ratio 1); see module docstring.",
        },
        "mixed_layer_interior_closed_form_check": {
            "points_checked": [{"r": r0, "theta": theta0, "phi": phi0} for r0, theta0, phi0 in interior_points],
            "max_dev_vs_closed_form": interior_max_dev,
            "confirmed": interior_closed_form_confirmed,
            "closed_form": "ds_B^2=(1/4)[dr^2/(1-r^2)+r^2(dtheta^2+sin^2(theta)dphi^2)]",
            "note": "Finite-difference (h=2e-3) numeric sanity check on the interior closed form; precision floor is FD-truncation-limited (~1e-5), not comparable to the near-machine-precision boundary check above.",
        },
        "berry_curvature_value": {"theta": "pi/2", "value": berry_at_pi_2, "expected_monopole": berry_expected_monopole,
                                   "matches_monopole": berry_matches_monopole},
        "bures_antisymmetric_part": {"max_abs_over_sampled_thetas": bures_antisym_max,
                                      "note": "Bures metric is the Hessian of a real scalar (D_B^2); Hessians are symmetric by construction, so no antisymmetric/Berry-curvature content can appear in g^B at all."},
        "berry_irreducible_witness": {
            "description": "psi(theta,phi) and chi(theta,phi)=psi(theta,phi)* (coordinatewise complex conjugate family) share identical real (g_tt,g_pp,g_tp) at every theta, with Berry curvature F_chi=-F_psi.",
            "theta": "pi/2",
            "shared_g_tt": conjugate_g_tt, "shared_g_pp": conjugate_g_pp, "shared_g_tp": conjugate_g_tp,
            "f_psi": f_plus, "f_chi": f_minus,
            "symbolic_check": {"off_diagonal_is_zero": qgt["off_diagonal_is_zero"],
                                "conjugate_shares_real_part": qgt["conjugate_shares_real_part"],
                                "conjugate_flips_berry": qgt["conjugate_flips_berry"]},
        },
        "z3": z3_result["result"],
        "z3_erased_constraint": z3_result["erased_constraint_result"],
        "cvc5": cvc5_result["result"],
        "cvc5_erased_constraint": cvc5_result["erased_constraint_result"],
        "control_real_part_recoverable": control_real_recoverable,
        "control_channel": "Real part (g^FS) recomputed independently on the same sampled/exact points and compared to the Bures restriction; deviation ~0 confirms it is genuinely recoverable, unlike F.",
        "berry_irreducible": berry_irreducible,
        "verdict": verdict,
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "ordering_status": ordering_status,
        "floor_claims": [{"key": "ratcheting.bures_to_fs.berry_flux", "value": berry_at_pi_2, "direction": "higher_is_better"}],
        "engines_ran": {"sympy": True, "numpy": True, "z3": True, "cvc5": bool(TOOL_MANIFEST["cvc5"]["used"]),
                        "jax": False, "julia": False},
        "tool_manifest": TOOL_MANIFEST,
        "notes": notes,
    }
    output = Path(__file__).resolve().parent / "results" / "bures_to_fubini_study.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "result": str(output), "verdict": verdict,
        "proportionality_constant": proportionality_constant, "max_dev": max_dev,
        "berry_at_pi_2": berry_at_pi_2, "berry_irreducible": berry_irreducible,
        "control_real_part_recoverable": control_real_recoverable,
        "z3": z3_result["result"], "z3_erased_constraint": z3_result["erased_constraint_result"],
        "cvc5": cvc5_result["result"], "cvc5_erased_constraint": cvc5_result["erased_constraint_result"],
    }, indent=2))


if __name__ == "__main__":
    main()

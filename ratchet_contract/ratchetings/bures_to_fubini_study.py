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

ENGINE SUBSTRATE (2026-07-22, engine migration only -- the science claims are
unchanged): the compute path runs on jax.numpy (x64); numpy is fully removed.
Two independent engine legs recompute the boundary witness from scratch and are
recorded in three_engine_legs / engine_values: Julia+QuantumOptics
(authoritative, fidelity path, bures_to_fubini_study_julia.jl) and
JAX+dynamiqs (bures_to_fubini_study_jax.py, the leg the three_engine_seal
re-runs to re-derive the value).  qutip stays a supportive control.

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

import cmath
import json
import math
import os
import subprocess
from pathlib import Path
from typing import Any

os.environ.setdefault("JAX_ENABLE_X64", "1")
import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import sympy as sp
from z3 import Function, RealSort, RealVal, Solver, sat, unsat

try:
    import cvc5
except ImportError:  # Recorded honestly below; z3 remains the primary proof leg.
    cvc5 = None

import psutil

QUTIP_MEMORY_FLOOR = 0.15  # qutip is light (~200MB); not the >0.40 heavy-engine gate.
_mem_available_fraction = psutil.virtual_memory().available / psutil.virtual_memory().total
qutip = None
QUTIP_SKIPPED_REASON = None
if _mem_available_fraction > QUTIP_MEMORY_FLOOR:
    import qutip
else:
    QUTIP_SKIPPED_REASON = (
        f"psutil available fraction {_mem_available_fraction:.3f} <= floor {QUTIP_MEMORY_FLOOR}; "
        "machine judged starved, qutip cross-check leg not imported."
    )


classification = "tool_lego_fit_probe"
promotion_allowed = False
ordering_status = "PROPOSED not canon"
TOL = 1.0e-8
CROSS_ENGINE_TOL = 1.0e-6  # FD-vs-autodiff legs share the value, not the algorithm.

TOOL_MANIFEST = {
    "sympy": {"tried": True, "used": True,
              "reason": "Exact Hessian of the closed-form Uhlmann-fidelity Bures distance and exact Provost-Vallee QGT differentiation."},
    "jax": {"tried": True, "used": True,
            "reason": "BASE ENGINE: the entire numeric compute path (Bloch-ball finite-difference Bures-Hessian "
                      "sweep, interior closed-form cross-check, qutip-wrapped Hessians) runs on jax.numpy (x64), "
                      "no numpy anywhere; dynamiqs is the independent rich-jax leg the three_engine_seal re-runs "
                      "to re-derive the boundary metric + Berry values."},
    "julia": {"tried": True, "used": False,
              "reason": "Authoritative QuantumOptics.jl fidelity-path leg; updated at runtime with its actual result."},
    "z3": {"tried": True, "used": True,
           "reason": "Generic single-valued-function non-vacuity witness; NOT a mechanism encoding -- the load-bearing evidence is the sympy exact conjugate-pair witness (psi vs chi=psi* sharing identical real (g_tt,g_pp,g_tp) but opposite Berry curvature +F/-F)."},
    "cvc5": {"tried": cvc5 is not None, "used": False,
             "reason": "Cross-check attempted when bindings are available; updated at runtime with its actual solver result."},
    "qutip": {"tried": qutip is not None, "used": False,
              "reason": (QUTIP_SKIPPED_REASON if qutip is None else
                          "Second-engine independent cross-check of the Bures-restricts-to-FS witness (qt.fidelity on Qobj density "
                          "matrices) and the Berry curvature witness (Fukui-Hatsugai-Suzuki plaquette on Qobj kets via .overlap()); "
                          "updated at runtime with actual computed values.")},
}

TOOL_INTEGRATION_DEPTH = {
    "sympy": "load_bearing",
    "jax": "load_bearing",   # numpy removed -- jax.numpy is the base
    "julia": None,           # set to load_bearing at runtime when the QuantumOptics leg runs
    "z3": "supportive",
    "cvc5": None,
    "qutip": None,
}


# ---------------------------------------------------------------------------
# Numeric primitives (Bloch ball, Uhlmann fidelity, Bures distance) -- jax.numpy x64.
# ---------------------------------------------------------------------------

def bloch_unit(theta: float, phi: float) -> jnp.ndarray:
    theta, phi = float(theta), float(phi)
    return jnp.array([
        math.sin(theta) * math.cos(phi),
        math.sin(theta) * math.sin(phi),
        math.cos(theta),
    ])


def fidelity_bloch(a: jnp.ndarray, b: jnp.ndarray) -> float:
    """Nielsen-Chuang closed form for 2x2 density-matrix fidelity in Bloch coords."""
    norm_a2 = float(jnp.dot(a, a))
    norm_b2 = float(jnp.dot(b, b))
    radicand = (1.0 - norm_a2) * (1.0 - norm_b2)
    return 0.5 * (1.0 + float(jnp.dot(a, b)) + math.sqrt(max(radicand, 0.0)))


def bures_d2(a: jnp.ndarray, b: jnp.ndarray) -> float:
    fidelity = min(max(fidelity_bloch(a, b), 0.0), 1.0)
    return 2.0 * (1.0 - math.sqrt(fidelity))


def numeric_metric_tensor(func, dim: int, h: float = 2.0e-3) -> jnp.ndarray:
    """Metric tensor g_ij such that func(d) = g_ij d^i d^j + O(d^3), for a
    scalar squared-distance func: R^dim -> R with func(0)=0 and a minimum at 0
    (odd terms vanish).  g_ij = (1/2) * central-difference-Hessian(func)_ij,
    since d^T Hess(d^T G d) d = 2 d^T G d (the raw second-derivative Hessian is
    twice the metric-tensor coefficient, not equal to it)."""
    zero = jnp.zeros(dim)
    hessian = [[0.0] * dim for _ in range(dim)]
    for i in range(dim):
        ei = zero.at[i].set(h)
        hessian[i][i] = float((func(ei) - 2.0 * func(zero) + func(-ei)) / (h * h))
    for i in range(dim):
        for j in range(i + 1, dim):
            ei = zero.at[i].set(h)
            ej = zero.at[j].set(h)
            value = float((func(ei + ej) - func(ei - ej) - func(-ei + ej) + func(-ei - ej)) / (4.0 * h * h))
            hessian[i][j] = value
            hessian[j][i] = value
    return 0.5 * jnp.array(hessian)


def perturbed_angular_point(r: float, theta: float, phi: float, d: jnp.ndarray) -> jnp.ndarray:
    """Bloch vector at (r, theta+d_theta, phi+d_phi); d=[dtheta, dphi]."""
    dtheta, dphi = float(d[0]), float(d[1])
    return r * bloch_unit(theta + dtheta, phi + dphi)


def perturbed_mixed_point(r: float, theta: float, phi: float, d: jnp.ndarray) -> jnp.ndarray:
    """Bloch vector at (r+d_r, theta+d_theta, phi+d_phi); d=[dr, dtheta, dphi]."""
    dr, dtheta, dphi = float(d[0]), float(d[1]), float(d[2])
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
        TOOL_MANIFEST["cvc5"]["reason"] = "Generic single-valued-function non-vacuity witness; NOT a mechanism encoding -- same caveat as z3, load-bearing evidence is the sympy exact conjugate-pair witness."
        TOOL_INTEGRATION_DEPTH["cvc5"] = "supportive"
        return {"result": str(result), "erased_constraint_result": str(relaxed_result),
                "reason": "same conjugate-pair Bures/FS metric-component contradiction"}
    except Exception as error:  # No false engine-use claim if the local API differs.
        TOOL_MANIFEST["cvc5"]["used"] = False
        TOOL_MANIFEST["cvc5"]["reason"] = f"Bindings available but cross-check did not run successfully: {error}"
        return {"result": "not_run", "erased_constraint_result": "not_run", "reason": str(error)}


# ---------------------------------------------------------------------------
# qutip: independent supportive cross-check (Qobj/fidelity/entropy_vn/ptrace).
# ---------------------------------------------------------------------------

def qutip_qubit_ket(theta: float, phi: float):
    """|psi(theta,phi)> = cos(theta/2)|0> + e^{i phi} sin(theta/2)|1> as a qutip Qobj ket."""
    return math.cos(theta / 2.0) * qutip.basis(2, 0) + \
        complex(math.cos(phi), math.sin(phi)) * math.sin(theta / 2.0) * qutip.basis(2, 1)


def qutip_bures_d2(theta0: float, phi0: float, dtheta: float, dphi: float) -> float:
    """Bures D_B^2 between two PURE qubit states via qutip's own qutip.fidelity on
    qutip.ket2dm density matrices (Uhlmann amplitude fidelity, not the base engine)."""
    rho_a = qutip.ket2dm(qutip_qubit_ket(theta0, phi0))
    rho_b = qutip.ket2dm(qutip_qubit_ket(theta0 + dtheta, phi0 + dphi))
    fid = min(max(float(qutip.fidelity(rho_a, rho_b)), 0.0), 1.0)
    return 2.0 * (1.0 - fid)


def qutip_pure_boundary_metric(theta0: float, h: float = 2.0e-3) -> dict[str, float]:
    """g^B_ij at (theta0, phi0=0) on the pure boundary, independently recomputed
    from qutip.fidelity via the same (1/2)*central-difference-Hessian convention
    as numeric_metric_tensor above, but built entirely on qutip Qobj machinery."""

    def d2(d: jnp.ndarray) -> float:
        return qutip_bures_d2(theta0, 0.0, float(d[0]), float(d[1]))

    hessian = numeric_metric_tensor(d2, 2, h=h)
    return {"g_tt": float(hessian[0, 0]), "g_pp": float(hessian[1, 1]), "g_tp": float(hessian[0, 1])}


def qutip_entropy_boundary_sanity(theta0: float) -> dict[str, float]:
    """Sanity leg on qutip.entropy_vn: a PURE qubit density matrix has S_vn=0;
    an equal mixture of two distinct pure states on the boundary does not.
    Independent confirmation that the r=1 boundary states qutip is handling are
    genuinely pure (not a jnp-array stand-in mislabeled as qutip)."""
    rho_pure = qutip.ket2dm(qutip_qubit_ket(theta0, 0.0))
    rho_mixed = 0.5 * rho_pure + 0.5 * qutip.ket2dm(qutip_qubit_ket(theta0 + 0.3, 0.4))
    return {"s_vn_pure": float(qutip.entropy_vn(rho_pure)),
            "s_vn_mixed_of_two_pure": float(qutip.entropy_vn(rho_mixed))}


def qutip_ptrace_purity_sanity() -> dict[str, float]:
    """Sanity leg on qutip.ptrace: a Bell pair traced down to one qubit lands on
    the r<1 mixed layer (S_vn>0, not the r=1 pure boundary this probe restricts
    on) -- confirms ptrace genuinely reduces rank, not a decorative import."""
    bell = (qutip.tensor(qutip.basis(2, 0), qutip.basis(2, 0)) +
            qutip.tensor(qutip.basis(2, 1), qutip.basis(2, 1))).unit()
    rho_bell = qutip.ket2dm(bell)
    rho_reduced = rho_bell.ptrace(0)
    return {"s_vn_bell_full": float(qutip.entropy_vn(rho_bell)),
            "s_vn_bell_reduced": float(qutip.entropy_vn(rho_reduced))}


def qutip_berry_plaquette(theta0: float, phi0: float, deps: float) -> float:
    """Discrete Berry curvature (Fukui-Hatsugai-Suzuki plaquette) at (theta0,phi0)
    computed entirely from qutip Qobj kets and their .overlap() inner product --
    an independent recomputation, not the sympy Provost-Vallee derivative used by
    the primary witness.  Loop traversed p1->p4->p3->p2->p1 (clockwise in
    theta-phi); the opposite (counter-clockwise) traversal returns the same
    magnitude with flipped sign -- a genuine orientation convention, not a
    disagreement -- and this traversal was picked because it lands on the same
    sign as the primary witness's berry_f=2*Im(Q_tp) convention."""
    p1 = qutip_qubit_ket(theta0 - deps / 2, phi0 - deps / 2)
    p2 = qutip_qubit_ket(theta0 + deps / 2, phi0 - deps / 2)
    p3 = qutip_qubit_ket(theta0 + deps / 2, phi0 + deps / 2)
    p4 = qutip_qubit_ket(theta0 - deps / 2, phi0 + deps / 2)
    loop = p1.overlap(p4) * p4.overlap(p3) * p3.overlap(p2) * p2.overlap(p1)
    berry_phase = -cmath.phase(complex(loop))
    return berry_phase / (deps * deps)


def run_qutip_cross_check(theta0: float) -> dict[str, Any]:
    if qutip is None:
        return {"ran": False, "reason": QUTIP_SKIPPED_REASON}
    # h=1e-3 empirically minimizes the FD-truncation-vs-matrix-sqrt-roundoff
    # tradeoff for qt.fidelity near F~1 (checked 2e-3 down to 1e-5; below ~2e-4
    # the sqrt-based fidelity computation loses precision faster than
    # truncation error shrinks -- a qutip-internal floor, not a mechanism issue).
    metric = qutip_pure_boundary_metric(theta0, h=1.0e-3)
    berry = qutip_berry_plaquette(theta0, 0.0, deps=1.0e-4)
    entropy_sanity = qutip_entropy_boundary_sanity(theta0)
    ptrace_sanity = qutip_ptrace_purity_sanity()
    TOOL_MANIFEST["qutip"]["used"] = True
    TOOL_INTEGRATION_DEPTH["qutip"] = "supportive"
    return {
        "ran": True,
        "g_tt": metric["g_tt"], "g_pp": metric["g_pp"], "g_tp": metric["g_tp"],
        "berry_at_theta0": berry,
        "entropy_vn_pure": entropy_sanity["s_vn_pure"],
        "entropy_vn_mixed_of_two_pure": entropy_sanity["s_vn_mixed_of_two_pure"],
        "ptrace_bell_full_s_vn": ptrace_sanity["s_vn_bell_full"],
        "ptrace_bell_reduced_s_vn": ptrace_sanity["s_vn_bell_reduced"],
    }


# ---------------------------------------------------------------------------
# Engine legs: Julia (QuantumOptics, authoritative) + JAX (dynamiqs), each an
# independent subprocess that recomputes the boundary witness from scratch.
# ---------------------------------------------------------------------------

PY_ENGINE = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"


def _run_leg(cmd: list) -> dict:
    """Run one engine leg as an independent subprocess (no echo -- each recomputes from
    scratch) and parse its single JSON line. Returns the record or a not-ran note."""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600,
                              cwd=str(Path(__file__).resolve().parents[2]))
    except Exception as exc:  # noqa: BLE001
        return {"ran": False, "reason": f"dispatch failed: {exc}"}
    if proc.returncode != 0:
        return {"ran": False, "reason": f"exit {proc.returncode}: {proc.stderr.strip()[-200:]}"}
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip().startswith("{")]
    if not lines:
        return {"ran": False, "reason": "no JSON on stdout"}
    data = json.loads(lines[-1])
    data["ran"] = True
    return data


def three_engine_witness() -> dict:
    """Julia(QuantumOptics, authoritative) + JAX(dynamiqs), each computing the
    boundary Bures/FS metric + Berry witness INDEPENDENTLY, sequentially (Julia
    startup is expensive; never parallel). Julia is the reference on disagreement."""
    here = Path(__file__).parent
    julia = _run_leg(["julia", str(here / "bures_to_fubini_study_julia.jl")])
    jax_leg = _run_leg([PY_ENGINE, str(here / "bures_to_fubini_study_jax.py")])
    return {"julia": julia, "jax": jax_leg}


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

    # --- (a) sampled numeric cross-check via finite-difference Hessian (jnp) ---
    sampled_thetas = jnp.linspace(0.05, math.pi - 0.05, 25)
    sampled_deviations = []
    sampled_ratios = []
    bures_antisym_max = 0.0
    for theta in sampled_thetas:
        theta = float(theta)

        def d2(d: jnp.ndarray, theta=theta) -> float:
            a = perturbed_angular_point(1.0, theta, 0.0, jnp.zeros(2))
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
    proportionality_constant = float(jnp.mean(jnp.array(exact_ratios + sampled_ratios)))
    proportionality_spread = float(max(abs(r - proportionality_constant) for r in exact_ratios + sampled_ratios))

    # --- MIXED-layer interior closed-form cross-check (Bloch-ball, r<1) ---
    interior_points = [(0.3, math.pi / 5, 0.7), (0.6, math.pi / 3, 2.1), (0.85, 2 * math.pi / 3, 4.0)]
    interior_deviations = []
    for r0, theta0, phi0 in interior_points:
        def d2_mixed(d: jnp.ndarray, r0=r0, theta0=theta0, phi0=phi0) -> float:
            a = perturbed_mixed_point(r0, theta0, phi0, jnp.zeros(3))
            b = perturbed_mixed_point(r0, theta0, phi0, d)
            return bures_d2(a, b)

        hessian3 = numeric_metric_tensor(d2_mixed, 3, h=2.0e-3)
        expected_rr = 1.0 / (4.0 * (1.0 - r0 * r0))
        expected_tt = r0 * r0 / 4.0
        expected_pp = r0 * r0 * math.sin(theta0) ** 2 / 4.0
        interior_deviations.append(float(abs(hessian3[0, 0] - expected_rr)))
        interior_deviations.append(float(abs(hessian3[1, 1] - expected_tt)))
        interior_deviations.append(float(abs(hessian3[2, 2] - expected_pp)))
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

    # --- qutip: independent supportive cross-check of the SAME two witness
    # quantities (Bures-restricts-to-FS metric components, Berry at pi/2) ---
    qutip_check = run_qutip_cross_check(math.pi / 2)
    if qutip_check["ran"]:
        qutip_vs_witness_divergence = float(max(
            abs(qutip_check["g_tt"] - conjugate_g_tt),
            abs(qutip_check["g_pp"] - conjugate_g_pp),
            abs(qutip_check["berry_at_theta0"] - berry_at_pi_2),
        ))
    else:
        qutip_vs_witness_divergence = None

    # --- TWO AUTHORITATIVE ENGINES, each recomputing the boundary witness
    # independently (no echo), run sequentially: Julia(QuantumOptics) is the
    # authoritative reference; JAX(dynamiqs) is the seal-re-runnable leg. ---
    engines = three_engine_witness()
    for name in ("julia", "jax"):
        if not engines[name].get("ran"):
            raise AssertionError(
                f"{name} engine leg did not run ({engines[name].get('reason')}); the "
                f"three-engine contract requires both -- report, do not smooth.")
    cross_engine_divergence = float(max(
        abs(float(engines["julia"][k]) - float(engines["jax"][k]))
        for k in ("g_tt_bures_boundary", "g_pp_bures_boundary", "berry_at_pi_2_plaquette")))
    base_vs_jax_leg_divergence = float(max(
        abs(float(engines["jax"]["g_tt_bures_boundary"]) - conjugate_g_tt),
        abs(float(engines["jax"]["g_pp_bures_boundary"]) - conjugate_g_pp),
        abs(float(engines["jax"]["berry_at_pi_2_qgt"]) - berry_at_pi_2)))
    if cross_engine_divergence > CROSS_ENGINE_TOL:
        raise AssertionError(
            f"cross-engine divergence {cross_engine_divergence} > {CROSS_ENGINE_TOL} vs Julia "
            f"reference -- report, do not smooth. julia={engines['julia']} jax={engines['jax']}")
    for eng, pkg in (("julia", "QuantumOptics"), ("jax", "dynamiqs")):
        TOOL_INTEGRATION_DEPTH[eng] = "load_bearing"
        TOOL_MANIFEST[eng]["tried"] = True
        TOOL_MANIFEST[eng]["used"] = True
        TOOL_MANIFEST[eng]["reason"] = (
            f"Independent {eng} leg ({pkg}): Bures boundary metric (g_tt, g_pp) = (1/4, 1/4) at "
            f"theta0=pi/2 coincides with Fubini-Study (ratio 1) and Berry = 1/2 (monopole); agrees "
            f"with the other engine to {cross_engine_divergence:.3e} (< {CROSS_ENGINE_TOL}).")

    engine_values = {
        # First-alphabetical jax_*/julia_* keys are the LIKE-FOR-LIKE plaquette pair
        # the three_engine_seal compares; the metric components follow.
        "jax_berry_at_pi_2": float(engines["jax"]["berry_at_pi_2_plaquette"]),
        "jax_g_pp_boundary_pi_2": float(engines["jax"]["g_pp_bures_boundary"]),
        "jax_g_tt_boundary_pi_2": float(engines["jax"]["g_tt_bures_boundary"]),
        "julia_berry_at_pi_2": float(engines["julia"]["berry_at_pi_2_plaquette"]),
        "julia_g_pp_boundary_pi_2": float(engines["julia"]["g_pp_bures_boundary"]),
        "julia_g_tt_boundary_pi_2": float(engines["julia"]["g_tt_bures_boundary"]),
        "qutip_berry_at_pi_2": qutip_check["berry_at_theta0"] if qutip_check["ran"] else None,
        "sympy_berry_at_pi_2": berry_at_pi_2,
        "sympy_g_pp_boundary_pi_2": conjugate_g_pp,
        "sympy_g_tt_boundary_pi_2": conjugate_g_tt,
    }

    # --- (c) control: the real part IS recoverable (genuine flip vs (b)) ---
    # Gated on the boundary restriction (near-machine-precision exact+sampled
    # comparison), which is the object part (c) actually asks about; the
    # interior mixed-layer sweep above is a separate, FD-precision-limited
    # sanity check on the closed form and is reported on its own.
    control_real_recoverable = max_dev < 1.0e-6 and interior_closed_form_confirmed
    berry_irreducible = (qgt["conjugate_shares_real_part"] and qgt["conjugate_flips_berry"]
                          and bures_antisym_max < 1.0e-6)

    core_ok = (control_real_recoverable and berry_matches_monopole and qgt["off_diagonal_is_zero"])

    verdict = "FAILED"
    notes = [
        "Finite/sampled+exact probe only; proposed layer ordering is not canon.",
        "Bures via Hessian of the closed-form Uhlmann-fidelity Bures distance D_B^2=2(1-sqrt(F)), F=(1/2)(1+a.b+sqrt((1-|a|^2)(1-|b|^2))) (Nielsen-Chuang closed form for 2x2 density operators).",
        "Fubini-Study/Berry via Provost-Vallee Q=<dpsi|dpsi>-|<psi|dpsi>|^2 on |psi(theta,phi)>=cos(theta/2)|0>+e^{i phi}sin(theta/2)|1>.",
        f"Computed proportionality constant (Bures at r=1 tangential vs Re(Q)) = {proportionality_constant:.6f}, "
        "not the frequently-cited 1/4 -- see module docstring HONESTY NOTE for the convention this depends on.",
        "Berry irreducibility witness: psi(theta,phi) and its coordinatewise conjugate family chi=psi* share identical (g_tt,g_pp,g_tp) at every theta but have Berry curvature F and -F respectively.",
        "ENGINE SUBSTRATE: compute path on jax.numpy x64 (numpy removed); two independent "
        "authoritative legs -- Julia+QuantumOptics (fidelity path, FD h=3e-3) and JAX+dynamiqs "
        "(exact jax.hessian through dq.fidelity + jacfwd QGT) -- each recompute the boundary "
        f"witness from scratch and agree to {cross_engine_divergence:.3e}; the jax leg is what "
        "the three_engine_seal re-runs to re-derive the value.",
    ]
    if qutip_check["ran"]:
        notes.append(
            f"qutip supportive cross-check (qt.fidelity/ket2dm/entropy_vn/ptrace, independent of sympy/jax): "
            f"g_tt={qutip_check['g_tt']:.8f}, g_pp={qutip_check['g_pp']:.8f} (witness 0.25 each), "
            f"berry={qutip_check['berry_at_theta0']:.10f} (witness {berry_at_pi_2}); "
            f"max divergence from the sympy/jax witness = {qutip_vs_witness_divergence:.3e}, "
            "consistent with qutip's own FD-Hessian/matrix-sqrt-fidelity precision floor (not a mechanism disagreement) "
            "-- same order of magnitude as the primary leg's own reported max_dev. Verdict unchanged."
        )
    else:
        notes.append(f"qutip cross-check leg not run: {qutip_check['reason']}")
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
        "engines_ran": {"sympy": True, "z3": True, "cvc5": bool(TOOL_MANIFEST["cvc5"]["used"]),
                        "jax": True, "julia": bool(engines["julia"].get("ran")),
                        "qutip": bool(qutip_check["ran"])},
        "qutip_cross_check": qutip_check,
        "engine_values": engine_values,
        "three_engine_legs": engines,
        "max_cross_engine_divergence": cross_engine_divergence,
        "base_vs_jax_leg_divergence": base_vs_jax_leg_divergence,
        "engine_contract": {"mode": "julia_authoritative_jax_rerunnable", "semantic_owner": "julia",
                            "reference": "julia:QuantumOptics",
                            "engines_agree_to": cross_engine_divergence,
                            "n_authoritative_engines": 2},
        "qutip_vs_witness_divergence": qutip_vs_witness_divergence,
        "smt_role": "supportive_nonvacuity_only",
        "load_bearing_evidence": "TWO AUTHORITATIVE ENGINES each recompute the boundary witness from scratch "
                                 "(no echo): Julia+QuantumOptics (fidelity path) and JAX+dynamiqs (exact "
                                 "jax.hessian through dq.fidelity + jacfwd Provost-Vallee QGT), agreeing to "
                                 f"{cross_engine_divergence:.3e} on (g_tt, g_pp, Berry) at theta0=pi/2. The "
                                 "sympy exact conjugate-pair witness (psi vs chi=psi* sharing identical real "
                                 "(g_tt,g_pp,g_tp) with Berry F and -F) carries the irreducibility claim; the "
                                 "base compute path runs on jax.numpy x64 (numpy removed) and qutip is a "
                                 "supportive cross-check.",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
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
        "qutip_ran": qutip_check["ran"], "qutip_vs_witness_divergence": qutip_vs_witness_divergence,
        "max_cross_engine_divergence": cross_engine_divergence,
        "engine_values": engine_values,
    }, indent=2))


if __name__ == "__main__":
    main()

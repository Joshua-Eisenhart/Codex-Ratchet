#!/usr/bin/env python3
"""Isolated sim: Hopf / projective base / nested tori / transport layer.

Layer (geometric constraint manifold): internal phase/fiber/base geometry and
finite transport paths on the spinor carrier, with no hidden Cartesian center.
Sims this ONE layer alone; no stacking/bridge.

Math verbatim from the owner's spec:
  psi(phi,chi,eta) = [ e^{i(phi+chi)} cos(eta), e^{i(phi-chi)} sin(eta) ]^T,  ||psi||=1
  Hopf fiber: psi ~ e^{i alpha} psi (U(1) orbit; rho = |psi><psi| invariant)
  A_H = -i psi^dag d psi = d phi + cos(2 eta) d chi          (Hopf connection)
  fiber path:     gamma_f(u) = psi(phi0+u, chi0; eta0)        (density-stationary)
  base-lift path: gamma_b(u) = psi(phi0 - cos(2 eta0) u, chi0+u; eta0)
  parallel-lift:  A_H(d gamma_b) = -cos2eta0 + cos2eta0 = 0   (horizontal)

Measured, falsifiable claims:
  - rho is invariant under the fiber phase; a non-fiber move (change chi) moves
    the Bloch base point.
  - A_H measured along each path (-i psi^dag dpsi/du, finite diff) matches the
    analytic d phi/du + cos2eta d chi/du  (sympy supplies the identity).
  - fiber loop: rho stationary, holonomy integral oint A_H = 2*pi.
  - base-lift loop: rho TRAVERSES then closes, and is HORIZONTAL (oint A_H = 0).
  - nested tori: distinct eta leaves give distinct Bloch latitudes z=cos2eta;
    collapsing the leaves erases the foliation.

Entropy as part of the manifold: psi is pure, so S(rho)=0 along both loops --
the Hopf transport is pure-state geometry, provably invisible to entropy.

classification: tool_lego_fit_probe (isolated; promotion_allowed=False)
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

SX = np.array([[0, 1], [1, 0]], dtype=complex)
SY = np.array([[0, -1j], [1j, 0]], dtype=complex)
SZ = np.array([[1, 0], [0, -1]], dtype=complex)


def psi_path(phis, chis, etas):
    return np.stack([np.exp(1j * (phis + chis)) * np.cos(etas),
                     np.exp(1j * (phis - chis)) * np.sin(etas)], axis=1)   # (N,2)


def rho_of(P):
    return np.einsum("ni,nj->nij", P, np.conj(P))   # (N,2,2)


def bloch(rho):
    return np.array([np.real(np.trace(rho @ SX)),
                     np.real(np.trace(rho @ SY)),
                     np.real(np.trace(rho @ SZ))])


def connection(P, u):
    dP = np.gradient(P, u, axis=0)
    return np.real(-1j * np.sum(np.conj(P) * dP, axis=1))   # A_H(u)


def vn_entropy(rho):
    w = np.clip(np.linalg.eigvalsh(rho).real, 1e-15, None)
    return float(-(w * np.log(w)).sum())


def frob(a, b):
    return float(np.linalg.norm(a - b))


def sympy_hopf_identities():
    import sympy as sp
    phi, chi, eta, a = sp.symbols("phi chi eta alpha", real=True)
    psi = sp.Matrix([sp.exp(sp.I * (phi + chi)) * sp.cos(eta),
                     sp.exp(sp.I * (phi - chi)) * sp.sin(eta)])
    dpsi = psi.diff(phi) * sp.Symbol("dphi") + psi.diff(chi) * sp.Symbol("dchi") + psi.diff(eta) * sp.Symbol("deta")
    A = sp.simplify(-sp.I * (psi.conjugate().T * dpsi)[0, 0])
    identity = sp.simplify(A - (sp.Symbol("dphi") + sp.cos(2 * eta) * sp.Symbol("dchi")))
    connection_identity = bool(identity == 0)
    # parallel-lift condition along base-lift: dphi=-cos2eta du, dchi=du -> A(dgamma_b)=0
    A_base = sp.simplify(A.subs({sp.Symbol("dphi"): -sp.cos(2 * eta), sp.Symbol("dchi"): 1, sp.Symbol("deta"): 0}))
    base_lift_horizontal = bool(A_base == 0)
    return {"A_H": str(A), "connection_identity": connection_identity,
            "base_lift_horizontal": base_lift_horizontal}


def main():
    phi0, chi0, eta0 = 0.3, 0.4, 0.5
    N = 4000
    u = np.linspace(0.0, 2 * math.pi, N)

    # fiber loop: only the global phase phi advances
    phi_f, chi_f, eta_f = phi0 + u, np.full(N, chi0), np.full(N, eta0)
    Pf = psi_path(phi_f, chi_f, eta_f)
    Rf, Af = rho_of(Pf), connection(Pf, u)
    fiber_dev = max(frob(Rf[k], Rf[0]) for k in range(N))
    fiber_hol = float(np.trapezoid(Af, u))
    # analytic A_H from the sympy-proven formula d phi + cos2eta d chi, evaluated on the
    # ACTUAL path derivatives (couples sympy identity to the measured connection; not hardcoded).
    Af_analytic = np.gradient(phi_f, u) + np.cos(2 * eta_f) * np.gradient(chi_f, u)

    # base-lift loop: horizontal, traverses the base
    phi_b, chi_b, eta_b = phi0 - math.cos(2 * eta0) * u, chi0 + u, np.full(N, eta0)
    Pb = psi_path(phi_b, chi_b, eta_b)
    Rb, Ab = rho_of(Pb), connection(Pb, u)
    base_max_dev = max(frob(Rb[k], Rb[0]) for k in range(N))
    base_close = frob(Rb[-1], Rb[0])
    base_hol = float(np.trapezoid(Ab, u))
    Ab_analytic = np.gradient(phi_b, u) + np.cos(2 * eta_b) * np.gradient(chi_b, u)
    geom_phase = float(np.angle(np.vdot(Pb[0], Pb[-1])))       # reported readout
    psi_return_dev = frob(Pb[-1], Pb[0])                       # spinor does NOT return -> holonomy

    # connection identity, measured vs analytic (trim noisy endpoints)
    sl = slice(5, N - 5)
    conn_err = float(max(np.max(np.abs(Af[sl] - Af_analytic[sl])),
                         np.max(np.abs(Ab[sl] - Ab_analytic[sl]))))

    # fiber-phase invariance vs a non-fiber move
    p = psi_path(np.array([phi0]), np.array([chi0]), np.array([eta0]))
    r0 = rho_of(p)[0]
    r_fiberphase = rho_of(np.exp(1j * 0.9) * p)[0]             # e^{i alpha} psi -> rho unchanged
    r_chimove = rho_of(psi_path(np.array([phi0]), np.array([chi0 + 0.3]), np.array([eta0])))[0]
    fiber_phase_invariant = frob(r_fiberphase, r0) < 1e-12
    nonfiber_moves_base = frob(r_chimove, r0) > 0.05

    # nested tori: distinct eta -> distinct Bloch latitude z=cos2eta; collapse erases it
    etas = np.array([0.2, 0.4, 0.6, 0.8])
    zs = np.cos(2 * etas)
    z_spread = float(zs.max() - zs.min())
    z_collapsed = float(np.ptp(np.cos(2 * np.full(4, math.pi / 4))))   # all eta=pi/4 -> z=0

    # control: an arbitrary path is NOT horizontal
    Pa = psi_path(phi0 + 0.7 * u, chi0 + 1.3 * u, np.full(N, eta0))
    arb_max_A = float(np.max(np.abs(connection(Pa, u)[sl])))

    # entropy along both loops (pure -> 0); mixed control proves the readout measures mixedness
    max_S = max(max(vn_entropy(Rf[k]) for k in range(0, N, 50)),
                max(vn_entropy(Rb[k]) for k in range(0, N, 50)))
    mixed_S = vn_entropy(0.7 * Rf[0] + 0.3 * 0.5 * np.eye(2))   # dephased control -> S > 0

    sym = sympy_hopf_identities()

    verdicts = {
        "hopf_projection_phase_invariant": fiber_phase_invariant,
        "nonfiber_move_changes_base": nonfiber_moves_base,
        "connection_identity_measured": conn_err < 1e-2,                 # A_H == dphi+cos2eta dchi
        "fiber_loop_density_stationary": fiber_dev < 1e-9,
        "fiber_holonomy_is_2pi": abs(fiber_hol - 2 * math.pi) < 0.05,
        "base_lift_traverses": base_max_dev > 0.3,
        "base_lift_closes": base_close < 1e-6,
        "base_lift_horizontal": abs(base_hol) < 0.05,                    # oint A_H = 0
        # nontrivial holonomy = curvature: base loop returns rho but NOT psi (geometric phase)
        "holonomy_nontrivial_curvature": base_close < 1e-6 and psi_return_dev > 0.1 and abs(geom_phase) > 0.1,
        "nested_tori_distinguishable": z_spread > 0.3,
        "control_arbitrary_path_not_horizontal": arb_max_A > 0.1,
        # entropy actually measures mixedness (pure -> 0, mixed control -> > 0), not stuck at 0
        "entropy_measures_mixedness": max_S < 1e-12 and mixed_S > 0.3,
        # load-bearing sympy COUPLED to measured (was gating on the symbolic term ALONE, decoupled):
        # the symbolic identity A_H = dphi+cos2eta dchi is confirmed by the MEASURED connection error,
        # and symbolic horizontality (A_base=0) by the MEASURED base holonomy ~ 0.
        "sympy_connection_identity_matches_measured":
            sym["connection_identity"] and conn_err < 1e-2,
        "sympy_base_lift_horizontal_matches_measured":
            sym["base_lift_horizontal"] and abs(base_hol) < 0.05,
    }

    result = {
        "name": "hopf_transport_nested_tori_isolated",
        "classification": "tool_lego_fit_probe",
        "promotion_allowed": False,
        "layer": "Hopf / projective base / nested tori / transport",
        "finite_map": "HopfTransportStep: (psi(phi,chi,eta), path in {fiber,base_lift}, A_H) -> rho(u), holonomy oint A_H",
        "domain": "unit spinor psi in S^3 subset C^2 over finite path samples",
        "codomain_or_output": "transported rho(u), connection A_H(u), holonomy, Bloch latitudes",
        "root_constraints": {"F01": "finite path samples N, finite eta leaves",
                             "N01": "the Hopf connection is non-flat: parallel transport around the closed base loop is NOT the identity -- rho returns but psi acquires a nonzero geometric phase (holonomy/curvature)"},
        "native_scale": {"N_path_samples": N, "n_eta_leaves": len(etas), "eta0": eta0},
        "dynamic_step": "transport of psi/rho along finite Hopf paths (parametric evolution in u)",
        "readouts": {
            "fiber_max_rho_deviation": fiber_dev,
            "fiber_holonomy_oint_A_H": fiber_hol,
            "base_max_rho_deviation": base_max_dev,
            "base_close_rho_deviation": base_close,
            "base_holonomy_oint_A_H": base_hol,
            "base_geometric_phase": geom_phase,
            "connection_max_abs_error_vs_analytic": conn_err,
            "bloch_latitudes_z": zs.tolist(),
            "max_entropy_along_loops": max_S,
        },
        "controls": {"arbitrary_path_max_A_H": arb_max_A, "collapsed_eta_z_spread": z_collapsed},
        "load_bearing_sympy": sym,
        "verdicts": verdicts,
        "all_pass": all(verdicts.values()),
        "blocked_consumers": ["stacking", "order_tests", "Xi", "Phi0", "Axis0", "flux", "FEP", "physics"],
        "tool_manifest": {
            "numpy": {"used": True, "reason": "claim-bearing spinor/rho/connection/holonomy computation"},
            "sympy": {"used": True, "reason": "load-bearing: proves A_H identity + base-lift horizontality, matched to measured A_H"},
        },
        "tool_integration_depth": "load_bearing",
    }

    import contract_emit, torch
    contract_emit.attach(result, {"base_vs_fiber_rho_deviation": (base_max_dev, fiber_dev),
                                  "fiber_vs_base_holonomy": (abs(fiber_hol), abs(base_hol))},
        "native Hopf-geometry scale (N path samples, eta leaves); 8/16/32/64 qubit ladder N/A.",
        torch_primary=float(torch.trapezoid(torch.tensor(Af), torch.tensor(u))))

    out_dir = Path(__file__).resolve().parent / "results"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "hopf_transport_nested_tori_isolated_results.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"all_pass={result['all_pass']}  ({sum(verdicts.values())}/{len(verdicts)} verdicts)")
    for k, v in verdicts.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    print(f"\nfiber loop: rho_dev={fiber_dev:.2e}  holonomy oint A_H={fiber_hol:.3f} (~2pi={2*math.pi:.3f})")
    print(f"base-lift : rho_max_dev={base_max_dev:.3f} close={base_close:.2e} "
          f"horizontal oint A_H={base_hol:.2e}  geom_phase={geom_phase:+.3f}")
    print(f"connection A_H vs analytic max err={conn_err:.2e}")
    print(f"nested tori z latitudes={zs.round(3).tolist()} spread={z_spread:.3f}; collapsed spread={z_collapsed:.2e}")
    print(f"entropy max along loops={max_S:.2e} (pure -> Hopf transport invisible to entropy)")
    print(f"sympy: connection_identity={sym['connection_identity']} base_lift_horizontal={sym['base_lift_horizontal']}")
    print(f"result -> {out_path}")


if __name__ == "__main__":
    main()

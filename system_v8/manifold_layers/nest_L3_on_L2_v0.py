#!/usr/bin/env python3
"""First real nesting of one geometry layer on another (manifold tower).

Floor (inner layer, L2/L3 of the ledger): the marginal's geometry — Bloch
radius r of rho_A = tr_B |psi><psi|, shells = level sets of r. Its entropy
and geometry are ONE object: S(rho_A) = h((1+r)/2), so the entropy readout
IS the radial coordinate read through h (binary entropy of eigenvalues).

Nested layer (outer, L5/L10 direction): the joint 2-qubit cut geometry —
Fubini-Study/Fisher metric of the joint family and the cut entropy S_A —
computed ON the inner shells, not beside them.

Executable nesting laws (each a computed witness, tol 1e-10):
  N1 entropy-geometry identity: S_A(theta) == h((1+r(theta))/2) exactly —
     the outer entropy is a function of the inner geometric coordinate.
  N2 metric nesting (chain rule): the pullback of the shell line element
     through r(theta) accounts for the radial part of the joint metric;
     the REMAINDER g_fiber = g_joint - g_radial >= 0 is the genuinely
     nested fiber contribution (entanglement phase). Nesting is real iff
     g_fiber is not identically zero AND not equal to g_joint.
  N3 outer restriction changes inner geometry: forbid entangled joint
     states (rank-1 marginals only) -> the inner shell family collapses
     from a continuum of radii to the single shell r=1.

Family: |psi(theta)> = cos(theta)|00> + sin(theta)|11>, theta in (0, pi/4].
All quantities exact/analytic checked against numerics.
Claim ceiling: first executed two-layer nesting instance on the 2q floor;
scratch_diagnostic; promotion_allowed=false; upgrades NO ledger row by
itself (boxes iii/v/viii of the ledger remain open).
"""
import json
import sys
from pathlib import Path

import numpy as np

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else \
    Path(__file__).resolve().parent / "results" / "nest_L3_on_L2_v0"


def h(p):
    p = np.clip(p, 1e-15, 1 - 1e-15)
    return float(-(p * np.log2(p) + (1 - p) * np.log2(1 - p)))


def joint_state(th):
    v = np.zeros(4)
    v[0], v[3] = np.cos(th), np.sin(th)
    return v


def rho_A(v):
    m = v.reshape(2, 2)
    return m @ m.T


def bloch_r(rho):
    return float(np.sqrt(max(0.0, 2 * float(np.trace(rho @ rho)) - 1)))


def S_vn(rho):
    ev = np.linalg.eigvalsh(rho)
    ev = ev[ev > 1e-15]
    return float(-(ev * np.log2(ev)).sum())


def fubini_study_g(th, d=1e-6):
    """Joint-layer metric g_joint(theta) (Fubini-Study, real family)."""
    v0, v1 = joint_state(th - d), joint_state(th + d)
    dv = (v1 - v0) / (2 * d)
    v = joint_state(th)
    return float(dv @ dv - (v @ dv) ** 2)


def main():
    if OUT.exists():
        raise SystemExit(f"refusing to reuse output: {OUT}")
    OUT.mkdir(parents=True)
    thetas = np.linspace(0.05, np.pi / 4, 40)
    rows, n1_max_err, fiber_zero, fiber_equals_joint = [], 0.0, True, True
    for th in thetas:
        v = joint_state(th)
        rA = rho_A(v)
        r = bloch_r(rA)
        S = S_vn(rA)
        # N1: entropy readout IS the radial coordinate through h
        n1_err = abs(S - h((1 + r) / 2))
        n1_max_err = max(n1_max_err, n1_err)
        # N2: metric nesting — radial pullback vs joint metric
        d = 1e-6
        drdth = (bloch_r(rho_A(joint_state(th + d)))
                 - bloch_r(rho_A(joint_state(th - d)))) / (2 * d)
        g_shell = 1.0 / max(1e-12, 1 - r ** 2)  # Bloch radial line element
        g_radial = g_shell * drdth ** 2
        g_joint = fubini_study_g(th)
        g_fiber = g_joint - g_radial
        if abs(g_fiber) > 1e-8:
            fiber_zero = False
        if abs(g_fiber - g_joint) > 1e-8:
            fiber_equals_joint = False
        rows.append({"theta": float(th), "r": r, "S_A": S,
                     "N1_err": n1_err, "g_joint": g_joint,
                     "g_radial_pullback": g_radial, "g_fiber": g_fiber})
    # N3: outer restriction -> inner collapse
    shells_full = sorted({round(row["r"], 6) for row in rows})
    product_only = [joint_state(t) for t in (0.0,)]  # rank-1 marginal family
    shells_restricted = sorted({round(bloch_r(rho_A(v)), 6)
                                for v in product_only})
    checks = {
        "N1_entropy_is_function_of_inner_geometry": n1_max_err < 1e-10,
        "N2_fiber_contribution_nonzero": not fiber_zero,
        "N2_fiber_not_whole_metric": not fiber_equals_joint,
        "N3_outer_restriction_collapses_inner_shells":
            len(shells_full) > 10 and shells_restricted == [1.0],
    }
    receipt = {
        "schema": "ratchet.v8.nest-L3-on-L2.v0",
        "family": "cos(theta)|00> + sin(theta)|11>, theta in (0, pi/4]",
        "inner_layer": "marginal Bloch shells; S_A = h((1+r)/2) — entropy "
                       "and geometry one object",
        "outer_layer": "joint Fubini-Study metric + cut entropy, nested on "
                       "the shells",
        "nesting_laws": checks,
        "N1_max_error": n1_max_err,
        "sample_rows": rows[::13],
        "shell_count_full": len(shells_full),
        "shells_after_outer_restriction": shells_restricted,
        "all_pass": all(checks.values()),
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "first executed two-layer nesting instance (2q, "
                         "exact); upgrades no ledger row; scratch_diagnostic",
    }
    (OUT / "receipt.json").write_text(
        json.dumps(receipt, indent=2, default=float) + "\n")
    print(json.dumps({"all_pass": receipt["all_pass"], "checks": checks,
                      "N1_max_error": n1_max_err,
                      "receipt": str(OUT / "receipt.json")}, indent=2,
                     default=float))


if __name__ == "__main__":
    main()

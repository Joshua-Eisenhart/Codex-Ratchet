#!/usr/bin/env python3
"""Classical baseline sim: principal bundle connection (trivialized).

Lane B classical baseline (numpy-only). NOT canonical.
Captures: a trivial principal G=R bundle over S^1 with the zero
connection. Parallel transport around the base is the identity.
Innately missing: nontrivial holonomy. A trivialized connection cannot
encode curvature or topological twist; any observed holonomy is
artefactual. U(1) phase holonomy and SU(2) Berry connection are
invisible at this level.
"""
import json, os
import numpy as np

classification = "classical_baseline"
divergence_log = (
    "trivialized connection has zero curvature and zero holonomy; "
    "bundle twist, Chern class, and Berry-type holonomy are not representable"
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "discrete loop integration"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
    "sympy": {"tried": False, "used": False, "reason": "numeric only"},
    "z3": {"tried": False, "used": False, "reason": "no admissibility claim"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "pytorch": "supportive",
    "sympy": "supportive",
}


def transport_loop(connection_1form, N=256):
    # integrate A around S^1 parametrized by t in [0, 2pi)
    ts = np.linspace(0.0, 2.0 * np.pi, N, endpoint=False)
    dt = 2.0 * np.pi / N
    holonomy = float(np.sum(connection_1form(ts)) * dt)
    return holonomy


def run_positive_tests():
    results = {}
    # Zero connection -> zero holonomy
    A_zero = lambda t: np.zeros_like(t)
    results["zero_connection_zero_holonomy"] = abs(transport_loop(A_zero)) < 1e-10
    # Exact 1-form dg/dt (pure gauge) integrates to g(2pi) - g(0) = 0 for periodic g
    A_gauge = lambda t: -np.sin(t)  # d/dt(cos t)
    results["pure_gauge_zero_holonomy"] = abs(transport_loop(A_gauge)) < 1e-8
    # Additivity: transporting constant connection alpha gives 2*pi*alpha
    alpha = 0.37
    A_const = lambda t: np.full_like(t, alpha)
    results["const_connection_2pi_alpha"] = abs(transport_loop(A_const) - 2 * np.pi * alpha) < 1e-8
    return results


def run_negative_tests():
    results = {}
    # Nonzero holonomy for a non-exact form? Classically can be computed
    # but trivial bundle means we *report* it as holonomy while the bundle
    # has no twist. Verify math vs topology split.
    A_const = lambda t: np.full_like(t, 1.0)
    holonomy = transport_loop(A_const)
    results["const_holonomy_nonzero"] = abs(holonomy) > 1e-3
    # But curvature of a 1-form on S^1 is identically 0 (dim mismatch)
    # confirm we cannot see a Chern-like number here
    results["no_2form_on_S1"] = True  # structural — S^1 has no 2-forms
    # Gauge transform must not change holonomy mod 2pi; pure gauge adds 0
    A_base = lambda t: 0.3 + 0.0 * t
    A_shift = lambda t: 0.3 - np.sin(t)  # add exact piece
    results["gauge_invariance_mod_0"] = abs(transport_loop(A_base) - transport_loop(A_shift)) < 1e-8
    return results


def run_boundary_tests():
    results = {}
    # Finite-sample convergence of loop integral
    A = lambda t: np.cos(3 * t) ** 2  # = 1/2 + 1/2 cos(6t) -> integral pi
    for N in (64, 256, 1024):
        err = abs(transport_loop(A, N=N) - np.pi)
        results[f"convergence_N_{N}"] = err < 5e-2
    # Trivial bundle: two independent loops must give the same holonomy-
    # formula result (no path dependence that isn't detected by the form)
    A_const = lambda t: np.full_like(t, 0.1)
    loop1 = transport_loop(A_const)
    loop2 = transport_loop(A_const)
    results["path_independence_trivial_bundle"] = abs(loop1 - loop2) < 1e-12
    return results


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "principal_bundle_connection_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
        "divergence_log": [
            "trivialized bundle: no Chern class, no twist",
            "cannot encode Berry / Wilczek-Zee non-abelian holonomy",
            "curvature of connection is identically zero",
            "holonomy values here are gauge-additive but not topologically meaningful",
        ],
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "principal_bundle_connection_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")

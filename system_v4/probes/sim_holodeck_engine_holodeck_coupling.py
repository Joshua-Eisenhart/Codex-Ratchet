#!/usr/bin/env python3
"""sim_holodeck_engine_holodeck_coupling -- THE INVERSION.

Thesis (load-bearing): the holodeck is co-generative with the engines.
Coupling is bidirectional: engine state E modifies carrier C; carrier
admissibility A(C) narrows which engine states are admissible. We test
the *fixed-point* structure: a joint (E,C) is admissible iff both
phi(E|C) and psi(C|E) hold. A one-way coupling is insufficient.
"""
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _holodeck_common import build_manifest, write_results, summary_ok

TOOL_MANIFEST = build_manifest()
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["numpy"] = "load_bearing"
TOOL_MANIFEST["numpy"]["used"] = True
TOOL_MANIFEST["numpy"]["reason"] = "fixed-point iteration"


def engine_to_carrier(E):  # phi: engine proposes carrier
    return np.tanh(E)


def carrier_to_engine(C):  # psi: carrier narrows engine
    return 0.5 * C


def joint_admissible(E, C, tol=1e-8):
    return np.allclose(engine_to_carrier(E), C, atol=tol) and \
           np.allclose(carrier_to_engine(C), E, atol=tol)


def fixed_point(E0, iters=200):
    E = E0.copy()
    for _ in range(iters):
        C = engine_to_carrier(E)
        E_new = carrier_to_engine(C)
        if np.allclose(E, E_new, atol=1e-12):
            break
        E = E_new
    return E, engine_to_carrier(E)


def run_positive_tests():
    r = {}
    E, C = fixed_point(np.array([0.3, -0.2]))
    r["joint_admissible"] = joint_admissible(E, C)
    # trivial fixed point at zero
    E0, C0 = fixed_point(np.array([0.0, 0.0]))
    r["zero_fixed_point"] = joint_admissible(E0, C0)
    return r


def run_negative_tests():
    r = {}
    # One-way coupling: only phi satisfied -- joint admissibility should FAIL
    E = np.array([0.5, 0.5])
    C = engine_to_carrier(E)
    # force E inconsistent with psi(C)
    E_wrong = E + 1.0
    r["one_way_passes"] = joint_admissible(E_wrong, C)
    # arbitrary unrelated (E,C)
    r["random_passes"] = joint_admissible(np.array([1.7, -0.4]),
                                          np.array([0.1, 0.9]))
    return r


def run_boundary_tests():
    r = {}
    # large-scale initial condition still converges to a joint fixed point
    E, C = fixed_point(np.array([10.0, -10.0]))
    r["large_init_converges"] = joint_admissible(E, C)
    # narrowing is strict: carrier admissible set has lower dimension than
    # engine x carrier product (dim narrowing measured by residual)
    grid = [(e, c) for e in np.linspace(-1, 1, 11) for c in np.linspace(-1, 1, 11)]
    admissible = sum(1 for e, c in grid
                     if joint_admissible(np.array([e]), np.array([c]), tol=0.05))
    r["narrowing_strict"] = admissible < len(grid) // 4
    return r


if __name__ == "__main__":
    results = {
        "name": "sim_holodeck_engine_holodeck_coupling",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    results["pass"] = summary_ok(results)
    path = write_results("sim_holodeck_engine_holodeck_coupling", results)
    print(f"pass={results['pass']} -> {path}")
    sys.exit(0 if results["pass"] else 1)

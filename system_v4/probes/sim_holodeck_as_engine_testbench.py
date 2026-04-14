#!/usr/bin/env python3
"""sim_holodeck_as_engine_testbench.

Thesis: every candidate engine must *run* inside the holodeck without
violating carrier admissibility. We instantiate a toy engine family and
simulate each for N steps inside the carrier; admissibility = state
stays within the projective unit sphere (norm-preserving up to tol).
"""
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _holodeck_common import build_manifest, write_results, summary_ok

TOOL_MANIFEST = build_manifest()
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["numpy"] = "load_bearing"
TOOL_MANIFEST["numpy"]["used"] = True
TOOL_MANIFEST["numpy"]["reason"] = "unitary evolution check"


def evolve(U, v0, steps):
    v = v0.copy()
    traj = [v.copy()]
    for _ in range(steps):
        v = U @ v
        traj.append(v.copy())
    return traj


def admissible(traj, tol=1e-6):
    n0 = np.linalg.norm(traj[0])
    return all(abs(np.linalg.norm(v) - n0) < tol for v in traj)


def random_unitary(n, seed):
    rng = np.random.default_rng(seed)
    A = rng.standard_normal((n, n)) + 1j * rng.standard_normal((n, n))
    Q, _ = np.linalg.qr(A)
    return Q


def run_positive_tests():
    r = {}
    v0 = np.array([1.0, 0, 0, 0], dtype=complex)
    # 3 candidate engines all unitary
    for i in range(3):
        U = random_unitary(4, seed=i)
        traj = evolve(U, v0, 20)
        r[f"engine_{i}_admissible"] = admissible(traj)
    return r


def run_negative_tests():
    r = {}
    v0 = np.array([1.0, 0, 0, 0], dtype=complex)
    # non-unitary engine: carrier norm drifts -- MUST NOT be admissible
    U_bad = 1.2 * np.eye(4)
    r["non_unitary_admissible"] = admissible(evolve(U_bad, v0, 10))
    # singular (norm-killing) engine
    U_zero = np.zeros((4, 4))
    r["zero_engine_admissible"] = admissible(evolve(U_zero, v0, 5))
    return r


def run_boundary_tests():
    r = {}
    v0 = np.array([1.0, 0, 0, 0], dtype=complex)
    # identity engine trivially admissible
    r["identity_engine"] = admissible(evolve(np.eye(4), v0, 50))
    # 1 step only: every engine trivially returns 2 states
    U = random_unitary(4, seed=42)
    r["one_step"] = len(evolve(U, v0, 1)) == 2
    return r


if __name__ == "__main__":
    results = {
        "name": "sim_holodeck_as_engine_testbench",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    results["pass"] = summary_ok(results)
    path = write_results("sim_holodeck_as_engine_testbench", results)
    print(f"pass={results['pass']} -> {path}")
    sys.exit(0 if results["pass"] else 1)

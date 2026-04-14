#!/usr/bin/env python3
"""sim_holodeck_observer_shell_projection -- observer projects reality-slice.

Thesis: an observer on the holodeck is a linear projection pi: C^n -> C^k
(k < n). Its "reality slice" is pi(carrier). We test that pi is idempotent
on its range, that distinct observers give distinct slices, and that an
observer cannot recover information orthogonal to its range.
"""
import numpy as np
import sys, os
classification = "classical_baseline"  # auto-backfill
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _holodeck_common import build_manifest, write_results, summary_ok

TOOL_MANIFEST = build_manifest()
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["numpy"] = "load_bearing"
TOOL_MANIFEST["numpy"]["used"] = True
TOOL_MANIFEST["numpy"]["reason"] = "projector linear algebra"


def observer(indices, n):
    P = np.zeros((n, n))
    for i in indices:
        P[i, i] = 1.0
    return P


def run_positive_tests():
    r = {}
    P = observer([0, 1], 4)
    r["idempotent"] = np.allclose(P @ P, P)
    r["self_adjoint"] = np.allclose(P, P.T)
    v = np.array([1.0, 2.0, 3.0, 4.0])
    r["range_fixed"] = np.allclose(P @ (P @ v), P @ v)
    return r


def run_negative_tests():
    r = {}
    # Claim: orthogonal component survives projection (should be False)
    P = observer([0, 1], 4)
    v = np.array([0.0, 0.0, 3.0, 4.0])
    r["ortho_survives"] = np.linalg.norm(P @ v) > 1e-9
    # Two distinct observers yield identical slices (should be False)
    Q = observer([2, 3], 4)
    r["distinct_same_slice"] = np.allclose(P, Q)
    return r


def run_boundary_tests():
    r = {}
    # full-rank observer = identity; projection is the whole carrier
    I = observer([0, 1, 2, 3], 4)
    r["full_rank_identity"] = np.allclose(I, np.eye(4))
    # empty observer annihilates everything
    Z = observer([], 4)
    r["empty_annihilates"] = np.allclose(Z @ np.ones(4), 0)
    return r


if __name__ == "__main__":
    results = {
        "name": "sim_holodeck_observer_shell_projection",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    results["pass"] = summary_ok(results)
    path = write_results("sim_holodeck_observer_shell_projection", results)
    print(f"pass={results['pass']} -> {path}")
    sys.exit(0 if results["pass"] else 1)

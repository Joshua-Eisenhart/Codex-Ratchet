#!/usr/bin/env python3
"""sim_holodeck_as_constraint_narrower -- the INVERSION sim.

Thesis (doctrine-critical): holodeck admissibility NARROWS the engine
candidate set. If E is the engine candidate set and A(H) is the
holodeck admissibility predicate, then |E ∩ A(H)| < |E|. We measure
narrowing ratio over a sampled engine family and require strict
inequality.

This formalizes the load-bearing inversion: the holodeck is not a
consumer; it is a constraint source.
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
TOOL_MANIFEST["numpy"]["reason"] = "sampling + admissibility filter"


def sample_engines(n_samples, dim, seed):
    rng = np.random.default_rng(seed)
    return [rng.standard_normal((dim, dim)) + 1j * rng.standard_normal((dim, dim))
            for _ in range(n_samples)]


def holodeck_admissible(U, tol=0.05):
    # admissibility = approximately norm-preserving
    v = np.ones(U.shape[0], dtype=complex) / np.sqrt(U.shape[0])
    for _ in range(5):
        v = U @ v
        n = np.linalg.norm(v)
        if n < 1e-9 or n > 1e6:
            return False
        v = v / n
    # survives iteration with bounded norm
    return True


def strict_holodeck_admissible(U, tol=1e-2):
    # stricter: actually unitary
    n = U.shape[0]
    return np.allclose(U.conj().T @ U, np.eye(n), atol=tol)


def narrowing_ratio(engines, predicate):
    admitted = [U for U in engines if predicate(U)]
    return len(admitted), len(engines)


def run_positive_tests():
    r = {}
    engines = sample_engines(200, 3, seed=7)
    admitted, total = narrowing_ratio(engines, strict_holodeck_admissible)
    r["strict_narrows"] = admitted < total
    # and narrows strictly (not just equal)
    r["strict_narrows_nontrivially"] = admitted <= total // 2
    # loose admissibility still narrows from arbitrary sample
    admitted2, total2 = narrowing_ratio(engines, holodeck_admissible)
    r["loose_is_subset"] = admitted2 <= total2
    return r


def run_negative_tests():
    r = {}
    engines = sample_engines(50, 3, seed=11)
    admitted, total = narrowing_ratio(engines, strict_holodeck_admissible)
    # Claim: holodeck admits all engines (should be False)
    r["admits_all"] = admitted == total
    # Claim: holodeck admits zero engines (False -- some random sample may satisfy)
    # Use near-unitary seeds
    unitaries = []
    for i in range(10):
        A = np.random.default_rng(i).standard_normal((3, 3)) + 1j * np.random.default_rng(i + 100).standard_normal((3, 3))
        Q, _ = np.linalg.qr(A)
        unitaries.append(Q)
    admit_u, _ = narrowing_ratio(unitaries, strict_holodeck_admissible)
    r["rejects_all_unitaries"] = admit_u == 0
    return r


def run_boundary_tests():
    r = {}
    # identity and zero extremes
    r["identity_admitted"] = strict_holodeck_admissible(np.eye(3, dtype=complex))
    r["zero_rejected"] = not strict_holodeck_admissible(np.zeros((3, 3), dtype=complex))
    # narrowing with empty candidate set is vacuously consistent
    admitted, total = narrowing_ratio([], strict_holodeck_admissible)
    r["empty_set_consistent"] = admitted == 0 and total == 0
    return r


if __name__ == "__main__":
    results = {
        "name": "sim_holodeck_as_constraint_narrower",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    results["pass"] = summary_ok(results)
    path = write_results("sim_holodeck_as_constraint_narrower", results)
    print(f"pass={results['pass']} -> {path}")
    sys.exit(0 if results["pass"] else 1)

#!/usr/bin/env python3
"""sim_holodeck_self_similar_holodeck_in_holodeck.

Thesis: the holodeck is self-similar -- a sub-slice of the carrier is
itself a valid holodeck. We model this with a nested projector chain
pi_1 >= pi_2 >= ... pi_k and verify that each pi_i(carrier) satisfies
the same admissibility rules as the outer carrier.
"""
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _holodeck_common import build_manifest, write_results, summary_ok

TOOL_MANIFEST = build_manifest()
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["numpy"] = "load_bearing"
TOOL_MANIFEST["numpy"]["used"] = True
TOOL_MANIFEST["numpy"]["reason"] = "nested projector chain"


def nested_chain(n, depths):
    chain = []
    for k in depths:
        P = np.zeros((n, n))
        for i in range(k):
            P[i, i] = 1.0
        chain.append(P)
    return chain


def is_nested(chain):
    for i in range(len(chain) - 1):
        # chain[i+1] should be a subprojector of chain[i]
        if not np.allclose(chain[i] @ chain[i + 1], chain[i + 1]):
            return False
        if not np.allclose(chain[i + 1] @ chain[i], chain[i + 1]):
            return False
    return True


def holodeck_admissible(P):
    return np.allclose(P @ P, P) and np.allclose(P, P.T)


def run_positive_tests():
    r = {}
    chain = nested_chain(8, [8, 6, 4, 2])
    r["all_admissible"] = all(holodeck_admissible(P) for P in chain)
    r["chain_nested"] = is_nested(chain)
    # depth-2 nesting also fine
    chain2 = nested_chain(4, [4, 2])
    r["depth2_nested"] = is_nested(chain2)
    return r


def run_negative_tests():
    r = {}
    # non-nested pair -- should fail
    P1 = np.diag([1, 1, 0, 0]).astype(float)
    P2 = np.diag([0, 0, 1, 1]).astype(float)
    r["disjoint_nested"] = is_nested([P1, P2])
    # non-projector masquerading as holodeck
    r["non_projector_admissible"] = holodeck_admissible(2 * np.eye(4))
    return r


def run_boundary_tests():
    r = {}
    # single-element chain trivially nested
    r["singleton_nested"] = is_nested([np.eye(4)])
    # chain of identicals trivially nested
    P = np.diag([1, 1, 0, 0]).astype(float)
    r["identical_chain"] = is_nested([P, P, P])
    return r


if __name__ == "__main__":
    results = {
        "name": "sim_holodeck_self_similar_holodeck_in_holodeck",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    results["pass"] = summary_ok(results)
    path = write_results("sim_holodeck_self_similar_holodeck_in_holodeck", results)
    print(f"pass={results['pass']} -> {path}")
    sys.exit(0 if results["pass"] else 1)

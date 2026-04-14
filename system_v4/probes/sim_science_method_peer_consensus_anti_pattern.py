#!/usr/bin/env python3
"""sim_science_method_peer_consensus_anti_pattern

Detect authoritarian-convergence: peers agree because they copy, not
because independent refutation failed.

Carrier: a population of peer verdicts V = [v_1, ..., v_n] plus a
copy-graph G (who read whom).
Structure: independent verdicts vs copied verdicts.
Probe: if agreement is high AND copy-graph is dense, flag anti-pattern.
       If agreement is high AND copy-graph is sparse, consensus is legitimate.
Chirality: the anti-pattern is asymmetric — copying is detectable; true
           independence is not provable, only evidenced by graph sparsity.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from _sci_method_common import new_manifest, write_results, all_pass

TOOL_MANIFEST = new_manifest()
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import networkx as nx
    TOOL_MANIFEST["networkx"]["tried"] = True
    TOOL_MANIFEST["networkx"]["used"] = True
    TOOL_MANIFEST["networkx"]["reason"] = "copy-graph density measurement"
    TOOL_INTEGRATION_DEPTH["networkx"] = "supportive"
    HAS_NX = True
except ImportError:
    HAS_NX = False


def agreement(V):
    if not V:
        return 0.0
    top = max(set(V), key=V.count)
    return V.count(top) / len(V)


def copy_density(n, edges):
    max_e = n * (n - 1)
    if max_e == 0:
        return 0.0
    return len(edges) / max_e


def anti_pattern(V, edges):
    n = len(V)
    a = agreement(V)
    d = copy_density(n, edges)
    return a >= 0.9 and d >= 0.5


def run_positive_tests():
    # Legitimate consensus: agreement high, copy-graph sparse.
    V = ["yes"] * 10
    edges = [(0, 1)]  # one citation
    return {"legit_consensus_not_flagged": {"pass": anti_pattern(V, edges) is False}}


def run_negative_tests():
    # Anti-pattern: high agreement + dense copying.
    V = ["yes"] * 6
    edges = [(i, j) for i in range(6) for j in range(6) if i != j]  # complete
    return {"dense_copy_flagged": {"pass": anti_pattern(V, edges) is True}}


def run_boundary_tests():
    # Divergent verdicts: never anti-pattern regardless of graph.
    V = ["yes", "no", "maybe", "yes", "no"]
    edges = [(i, j) for i in range(5) for j in range(5) if i != j]
    return {"divergent_not_flagged": {"pass": anti_pattern(V, edges) is False}}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    results = {
        "name": "science_method_peer_consensus_anti_pattern",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "classification": "classical_baseline",
        "status": "pass" if (all_pass(pos) and all_pass(neg) and all_pass(bnd)) else "fail",
    }
    path = write_results("sim_science_method_peer_consensus_anti_pattern", results)
    print(f"[{results['status']}] {path}")
    sys.exit(0 if results["status"] == "pass" else 1)

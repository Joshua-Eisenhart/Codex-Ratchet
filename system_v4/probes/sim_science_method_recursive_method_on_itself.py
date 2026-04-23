#!/usr/bin/env python3
"""sim_science_method_recursive_method_on_itself

Self-similar test: apply the science method to the science method's own
claim ("the method survives its own gates").

Carrier: the method itself as a predicate M(claim) -> admit/reject.
Structure: self-claim S := "M admits claims with observable distinguishability".
Reduction: apply M to S; S must have an observable test of its own.
Admissibility: M(S) = True.
Chirality: recursion depth bounded (stop at depth=2).
"""
import os, sys
classification = "classical_baseline"  # auto-backfill
sys.path.insert(0, os.path.dirname(__file__))
from _sci_method_common import new_manifest, write_results, all_pass

TOOL_MANIFEST = new_manifest()
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}


def method_admits(claim):
    """Minimal M: claim admitted iff it has a test_fn that distinguishes 2+ obs."""
    test_fn = claim.get("test_fn")
    obs = claim.get("obs", [])
    if test_fn is None or len(obs) < 2:
        return False
    outs = [test_fn(o) for o in obs]
    return len(set(map(repr, outs))) > 1


def self_claim():
    # The claim "M distinguishes admissible from non-admissible claims".
    sample_claims = [
        {"test_fn": lambda x: x % 2 == 0, "obs": [1, 2]},   # admissible
        {"test_fn": None, "obs": [1, 2]},                    # not admissible
    ]
    return {
        "test_fn": lambda c: method_admits(c),
        "obs": sample_claims,
    }


def run_positive_tests():
    # Depth 1: method applied to itself admits it (M(S) == True).
    ok = method_admits(self_claim())
    return {"depth1_admits_self": {"pass": ok is True}}


def run_negative_tests():
    # Degenerate self-claim: no sample claims -> method should NOT admit.
    bad = {"test_fn": lambda c: method_admits(c), "obs": []}
    return {"empty_self_rejected": {"pass": method_admits(bad) is False}}


def run_boundary_tests():
    # Depth 2: wrap the self-claim as an obs of a meta-claim.
    inner = self_claim()
    meta = {
        "test_fn": lambda c: method_admits(c),
        "obs": [inner, {"test_fn": None, "obs": [1]}],
    }
    return {"depth2_admits": {"pass": method_admits(meta) is True}}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    results = {
        "name": "science_method_recursive_method_on_itself",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "classification": "classical_baseline",
        "status": "pass" if (all_pass(pos) and all_pass(neg) and all_pass(bnd)) else "fail",
    }
    path = write_results("sim_science_method_recursive_method_on_itself", results)
    print(f"[{results['status']}] {path}")
    sys.exit(0 if results["status"] == "pass" else 1)

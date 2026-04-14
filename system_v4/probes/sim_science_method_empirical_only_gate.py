#!/usr/bin/env python3
"""sim_science_method_empirical_only_gate

Reject claims with no observable distinguishability test.

Carrier: claim := (statement, observable_test_fn or None).
Structure: gate(claim) := observable_test_fn is not None AND produces
           different outputs on at least two observations (distinguishability).
Admissibility: gate returns True.
Probe: gate rejects pure-label claims.
"""
import os, sys
classification = "classical_baseline"  # auto-backfill
sys.path.insert(0, os.path.dirname(__file__))
from _sci_method_common import new_manifest, write_results, all_pass

TOOL_MANIFEST = new_manifest()
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}


def gate(claim, obs_samples):
    stmt, test_fn = claim
    if test_fn is None:
        return False
    try:
        outs = [test_fn(o) for o in obs_samples]
    except Exception:
        return False
    return len(set(map(repr, outs))) > 1  # distinguishes at least 2


def run_positive_tests():
    claim = ("x is even", lambda x: x % 2 == 0)
    obs = [1, 2, 3, 4]
    return {"parity_observable": {"pass": gate(claim, obs)}}


def run_negative_tests():
    claim_none = ("x is beautiful", None)
    claim_const = ("x is x", lambda x: True)
    obs = [1, 2, 3]
    return {
        "no_test_rejected": {"pass": gate(claim_none, obs) is False},
        "constant_test_rejected": {"pass": gate(claim_const, obs) is False},
    }


def run_boundary_tests():
    # Single observation: cannot distinguish — reject.
    claim = ("x even", lambda x: x % 2 == 0)
    return {"single_obs_rejected": {"pass": gate(claim, [2]) is False}}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    results = {
        "name": "science_method_empirical_only_gate",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "classification": "classical_baseline",
        "status": "pass" if (all_pass(pos) and all_pass(neg) and all_pass(bnd)) else "fail",
    }
    path = write_results("sim_science_method_empirical_only_gate", results)
    print(f"[{results['status']}] {path}")
    sys.exit(0 if results["status"] == "pass" else 1)

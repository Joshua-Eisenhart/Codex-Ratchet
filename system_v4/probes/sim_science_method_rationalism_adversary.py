#!/usr/bin/env python3
"""sim_science_method_rationalism_adversary

Detect Platonic / label-substituted-for-computation patterns.

Carrier: claim as dict {label, computation_trace, observable_outputs}.
Structure: pattern = (has_label AND (trace is empty OR outputs is empty)).
Reduction: adversary flags claims where a name does the work of a computation.
Probe: returns True if rationalist-residue detected.
Chirality: detection is one-way (finds residue; absence is not proof of purity).
"""
import os, sys
classification = "classical_baseline"  # auto-backfill
sys.path.insert(0, os.path.dirname(__file__))
from _sci_method_common import new_manifest, write_results, all_pass

TOOL_MANIFEST = new_manifest()
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}


def is_rationalist_residue(claim):
    label = claim.get("label", "")
    trace = claim.get("computation_trace", [])
    outputs = claim.get("observable_outputs", [])
    if not label:
        return False
    if not trace:
        return True
    if not outputs:
        return True
    # label is a proper noun / capitalized abstract term with no op behind it?
    if len(trace) == 1 and trace[0] == f"assume({label})":
        return True
    return False


def run_positive_tests():
    # Real computation with outputs: not residue.
    c = {"label": "add", "computation_trace": ["1+2", "=3"], "observable_outputs": [3]}
    return {"grounded_claim_clean": {"pass": is_rationalist_residue(c) is False}}


def run_negative_tests():
    c1 = {"label": "Essence", "computation_trace": [], "observable_outputs": []}
    c2 = {"label": "Form", "computation_trace": ["assume(Form)"], "observable_outputs": []}
    return {
        "bare_label_flagged": {"pass": is_rationalist_residue(c1) is True},
        "assume_only_flagged": {"pass": is_rationalist_residue(c2) is True},
    }


def run_boundary_tests():
    # Empty claim: no label -> not flagged (not a rationalism case; it's an empty case).
    c = {"label": "", "computation_trace": [], "observable_outputs": []}
    return {"empty_not_flagged": {"pass": is_rationalist_residue(c) is False}}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    results = {
        "name": "science_method_rationalism_adversary",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "classification": "classical_baseline",
        "status": "pass" if (all_pass(pos) and all_pass(neg) and all_pass(bnd)) else "fail",
    }
    path = write_results("sim_science_method_rationalism_adversary", results)
    print(f"[{results['status']}] {path}")
    sys.exit(0 if results["status"] == "pass" else 1)

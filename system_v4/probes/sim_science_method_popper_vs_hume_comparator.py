#!/usr/bin/env python3
"""sim_science_method_popper_vs_hume_comparator

Distinguishability test between falsification-frame (Popper) and
no-causality-frame (Hume). Both frames are admissible under different
probes; the comparator reports where they agree and where they split.

Carrier: an observed sequence of (cause_candidate, effect) pairs.
Structure:
  - Popper frame: accept a law L iff no counterexample in data AND L is
    falsifiable (there exists a hypothetical observation that would refute L).
  - Hume frame: accept a regularity R iff constant conjunction observed;
    no causal claim attached.
Probe: compare verdicts.
Chirality: Popper is future-oriented (could be falsified); Hume is
           past-oriented (constant conjunction so far).
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from _sci_method_common import new_manifest, write_results, all_pass

TOOL_MANIFEST = new_manifest()
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}


def popper_accepts(law, data, falsifier_exists):
    # law: callable (c,e)->bool; must hold on all data AND be falsifiable
    if not falsifier_exists:
        return False
    return all(law(c, e) for c, e in data)


def hume_accepts(data):
    # regularity: effect constant given cause
    if not data:
        return False
    effect_for = {}
    for c, e in data:
        if c in effect_for and effect_for[c] != e:
            return False
        effect_for[c] = e
    return True


def run_positive_tests():
    # "fire -> smoke" observed consistently.
    data = [("fire", "smoke")] * 5
    law = lambda c, e: (c == "fire") <= (e == "smoke")  # implication
    p = popper_accepts(law, data, falsifier_exists=True)
    h = hume_accepts(data)
    return {"both_accept_regular": {"pass": p is True and h is True}}


def run_negative_tests():
    # Unfalsifiable claim: Popper rejects, Hume accepts (regularity holds vacuously).
    data = [("x", "y")]
    law = lambda c, e: True
    p = popper_accepts(law, data, falsifier_exists=False)
    h = hume_accepts(data)
    return {"unfalsifiable_splits": {"pass": p is False and h is True,
                                      "popper": p, "hume": h}}


def run_boundary_tests():
    # Contradiction in data: both reject.
    data = [("fire", "smoke"), ("fire", "nothing")]
    law = lambda c, e: (c == "fire") <= (e == "smoke")
    p = popper_accepts(law, data, falsifier_exists=True)
    h = hume_accepts(data)
    return {"contradiction_both_reject": {"pass": p is False and h is False}}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    results = {
        "name": "science_method_popper_vs_hume_comparator",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "classification": "classical_baseline",
        "status": "pass" if (all_pass(pos) and all_pass(neg) and all_pass(bnd)) else "fail",
    }
    path = write_results("sim_science_method_popper_vs_hume_comparator", results)
    print(f"[{results['status']}] {path}")
    sys.exit(0 if results["status"] == "pass" else 1)

#!/usr/bin/env python3
"""sim_science_method_forward_potential_vs_past_causality_split

Orientation test. The method has two temporal framings that must NOT be
collapsed:
  - past-causality: "E happened because of C" (backward-admissibility).
  - forward-potential: "C is compatible with future E" (forward-constraint).

Carrier: an event pair (C, E) with a timestamp.
Structure: split(E) -> {past_causes: [...], future_potentials: [...]}.
Probe: verify the two sets are computed by different operators and
       that the orientation labels do not leak.
Chirality: forward vs backward — these are the two chirality classes.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from _sci_method_common import new_manifest, write_results, all_pass

TOOL_MANIFEST = new_manifest()
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}


def past_causes(events, t):
    return [e for e in events if e["t"] < t]


def future_potentials(events, t):
    return [e for e in events if e["t"] > t]


def orientation_split(events, t):
    p = past_causes(events, t)
    f = future_potentials(events, t)
    disjoint = not (set(id(x) for x in p) & set(id(x) for x in f))
    return {"past": p, "future": f, "disjoint": disjoint}


def run_positive_tests():
    events = [{"t": 0, "tag": "a"}, {"t": 1, "tag": "b"}, {"t": 2, "tag": "c"}]
    sp = orientation_split(events, 1.5)
    ok = sp["disjoint"] and len(sp["past"]) == 2 and len(sp["future"]) == 1
    return {"basic_split": {"pass": ok, "split": {"past": len(sp["past"]), "future": len(sp["future"])}}}


def run_negative_tests():
    # Collapsing the two: treating "past" as "future" must produce wrong count.
    events = [{"t": 0}, {"t": 2}]
    wrong = past_causes(events, 1.0) == future_potentials(events, 1.0)
    return {"collapse_detected": {"pass": wrong is False}}


def run_boundary_tests():
    # Event exactly at t: belongs to neither past nor future (strict <).
    events = [{"t": 1.0, "tag": "now"}]
    sp = orientation_split(events, 1.0)
    return {"simultaneous_excluded": {"pass": len(sp["past"]) == 0 and len(sp["future"]) == 0}}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    results = {
        "name": "science_method_forward_potential_vs_past_causality_split",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "classification": "classical_baseline",
        "status": "pass" if (all_pass(pos) and all_pass(neg) and all_pass(bnd)) else "fail",
    }
    path = write_results("sim_science_method_forward_potential_vs_past_causality_split", results)
    print(f"[{results['status']}] {path}")
    sys.exit(0 if results["status"] == "pass" else 1)

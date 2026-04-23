#!/usr/bin/env python3
"""sim_science_method_method_triangle_prep

Coupling prep stub for the holodeck <-> FEP <-> science-method triangle.

Carrier: three shell-local frames with a shared observation channel.
  - holodeck: generative-surface frame (forward potential)
  - FEP:      free-energy-minimization frame (surprise reduction)
  - science-method: refutation frame (counterexample search)
Structure: three unary projectors on a shared observation o.
Reduction: projections must be DIFFERENT (otherwise the frames collapse).
Probe: count distinct projections; require >=2 distinct values on a
       heterogeneous observation (coupling nontrivial).
Chirality/orientation: each frame has its own orientation; coupling stub
       does NOT claim they commute. This is prep only, per coupling-program
       step 2. Step 3 (coexistence) is out of scope here.
"""
import os, sys
classification = "classical_baseline"  # auto-backfill
sys.path.insert(0, os.path.dirname(__file__))
from _sci_method_common import new_manifest, write_results, all_pass

TOOL_MANIFEST = new_manifest()
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}


def holodeck_project(o):
    # forward-potential: admissible futures = elements > median
    if not o: return []
    m = sorted(o)[len(o)//2]
    return [x for x in o if x > m]


def fep_project(o):
    # surprise reduction: return most frequent value
    if not o: return []
    return [max(set(o), key=o.count)]


def method_project(o):
    # refutation: keep items that could refute a "all equal" claim
    if not o: return []
    ref = o[0]
    return [x for x in o if x != ref]


def triangle(o):
    return {
        "holodeck": holodeck_project(o),
        "fep": fep_project(o),
        "method": method_project(o),
    }


def run_positive_tests():
    o = [1, 2, 2, 3, 4]
    t = triangle(o)
    distinct = len({repr(v) for v in t.values()})
    return {"heterogeneous_three_distinct": {"pass": distinct >= 2, "distinct": distinct, "triangle": t}}


def run_negative_tests():
    # Homogeneous obs: frames collapse (all return empty or single value sets).
    o = [5, 5, 5]
    t = triangle(o)
    all_trivial = all(len(v) <= 1 for v in t.values())
    return {"homogeneous_collapses": {"pass": all_trivial is True, "triangle": t}}


def run_boundary_tests():
    # Empty obs: all three return [].
    t = triangle([])
    all_empty = all(v == [] for v in t.values())
    return {"empty_all_empty": {"pass": all_empty}}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    results = {
        "name": "science_method_method_triangle_prep",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "classification": "classical_baseline",
        "status": "pass" if (all_pass(pos) and all_pass(neg) and all_pass(bnd)) else "fail",
        "note": "coupling_prep_only; step_3_coexistence_out_of_scope",
    }
    path = write_results("sim_science_method_method_triangle_prep", results)
    print(f"[{results['status']}] {path}")
    sys.exit(0 if results["status"] == "pass" else 1)

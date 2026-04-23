#!/usr/bin/env python3
"""sim_fence_bc09_unsat.py -- BC09 Probability ban (no probabilistic primitives).

scope_note: LADDERS_FENCES_ADMISSION_REFERENCE.md line 119: "BC09 |
Probability ban | no probabilistic primitives at base". Literal reading:
smuggled axiom asserts a primitive probability measure p: Event -> Real in
[0,1], normalized over a finite admitted partition E1..En summing to 1.
Preserved witness: all-zero probabilities on the partition (base has no
probabilistic primitive, so the only consistent "prob" assignment must be
non-informative/unconstrained). Smuggled normalization + witness UNSAT.

classification: canonical
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from _fence_unsat_common import fresh_manifest

TOOL_MANIFEST = fresh_manifest()
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
try:
    import z3
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    z3 = None
    TOOL_MANIFEST["z3"]["reason"] = "not installed -- BLOCKER"


def _theory(include_witness=True, include_smuggle=True):
    p1, p2, p3 = z3.Reals("p1 p2 p3")
    s = z3.Solver()
    if include_smuggle:
        # smuggled primitive: probabilities in [0,1] summing to 1 over partition
        s.add(p1 >= 0, p2 >= 0, p3 >= 0)
        s.add(p1 <= 1, p2 <= 1, p3 <= 1)
        s.add(p1 + p2 + p3 == 1)
    if include_witness:
        # preserved witness: base has no probabilistic content -> all zero
        s.add(p1 == 0, p2 == 0, p3 == 0)
    return s


def run_positive_tests():
    r = _theory(True, True).check()
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "UNSAT of (normalization smuggling + no-probabilistic-content witness) IS the fence"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    return {"fence_unsat": {"verdict": str(r), "pass": r == z3.unsat}}


def run_negative_tests():
    r = _theory(False, True).check()
    return {"no_smuggle_sat": {"verdict": str(r), "pass": r == z3.sat}}


def run_boundary_tests():
    r = _theory(True, False).check()
    return {"smuggle_alone_sat": {"verdict": str(r), "pass": r == z3.sat}}


if __name__ == "__main__":
    results = {
        "name": "sim_fence_bc09_unsat",
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md BC09 line 119 (Probability ban).",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_fence_bc09_unsat_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    all_pass = all(v["pass"] for v in list(results["positive"].values()) + list(results["negative"].values()) + list(results["boundary"].values()))
    print(f"[{'PASS' if all_pass else 'FAIL'}] {results['name']} -> {out_path}")

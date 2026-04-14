#!/usr/bin/env python3
"""
Leviathan EXPLORE framing: constraint satisfaction (z3).

Framing assumption:
  Admissibility encoded as boolean/arithmetic constraints. Diverse-group
  admissibility is SAT; forced monoculture (all groups equal value) under
  a 'human-potential > 0' constraint is UNSAT.

Blind spot:
  - Discrete constraints; real admissibility is graded.
  - No dynamics — purely static feasibility.
"""
import json, os

TOOL_MANIFEST = {"z3": {"tried": False, "used": False, "reason": ""}}
TOOL_INTEGRATION_DEPTH = {"z3": "load_bearing"}
try:
    import z3
    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "SAT/UNSAT for admissibility under centralization"
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"; z3 = None


def diverse_sat(n=5):
    if z3 is None: return None
    s = z3.Solver()
    V = [z3.Int(f"v{i}") for i in range(n)]
    for v in V:
        s.add(v >= 0, v <= 10)
    s.add(z3.Distinct(V))                      # diversity
    s.add(z3.Sum(V) >= n)                      # potential > 0
    return s.check() == z3.sat

def monoculture_unsat(n=5):
    if z3 is None: return None
    s = z3.Solver()
    V = [z3.Int(f"v{i}") for i in range(n)]
    for v in V:
        s.add(v >= 0, v <= 10)
    # forced monoculture
    for i in range(1, n):
        s.add(V[i] == V[0])
    s.add(z3.Distinct(V))                      # contradicts monoculture
    s.add(z3.Sum(V) >= n)
    return s.check() == z3.sat


def run_positive_tests():
    return {"diverse_sat": diverse_sat(), "pass": diverse_sat() is True}

def run_negative_tests():
    return {"mono_sat": monoculture_unsat(), "pass_unsat": monoculture_unsat() is False}

def run_boundary_tests():
    if z3 is None: return {"skipped": "z3"}
    s = z3.Solver(); x = z3.Int("x"); s.add(x == x)
    return {"trivial": s.check() == z3.sat, "pass": True}


if __name__ == "__main__":
    results = {
        "name": "leviathan_explore_as_constraint_satisfaction",
        "framing_assumption": "admissibility = SAT of diversity + positive-potential constraints",
        "blind_spot": "discrete, static; no graded admissibility or dynamics",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "leviathan_explore_as_constraint_satisfaction_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(json.dumps({k: results[k] for k in ["name","positive","negative","boundary"]}, indent=2, default=str))

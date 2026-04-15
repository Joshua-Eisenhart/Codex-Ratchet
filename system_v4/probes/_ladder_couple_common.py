"""Common scaffolding for ladder pairwise coupling sims.

scope_note: see system_v5/new docs/LADDERS_FENCES_ADMISSION_REFERENCE.md
Exclusion language only: 'admissible under coupling' / 'excluded under coupling'
/ 'survived joint probe' / 'indistinguishable under coupling'. Never causal.
"""
import json, os

def empty_manifest():
    return {
        "pytorch": {"tried": False, "used": False, "reason": ""},
        "z3":       {"tried": False, "used": False, "reason": ""},
        "sympy":    {"tried": False, "used": False, "reason": ""},
        "clifford": {"tried": False, "used": False, "reason": ""},
    }

def write_results(sim_name, results):
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{sim_name}_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    return out_path

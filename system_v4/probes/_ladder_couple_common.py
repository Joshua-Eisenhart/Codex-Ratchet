"""Common scaffolding for ladder pairwise coupling sims.

scope_note: see system_v5/docs/LADDERS_FENCES_ADMISSION_REFERENCE.md
Exclusion language only: 'admissible under coupling' / 'excluded under coupling'
/ 'survived joint probe' / 'indistinguishable under coupling'. Never causal.
"""
import json, os

classification = "canonical"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "helper scaffolding only; tool use is delegated to the pairwise wrapper sims"},
    "pyg": {"tried": False, "used": False, "reason": "helper scaffolding only; tool use is delegated to the pairwise wrapper sims"},
    "z3": {"tried": False, "used": False, "reason": "helper scaffolding only; tool use is delegated to the pairwise wrapper sims"},
    "cvc5": {"tried": False, "used": False, "reason": "helper scaffolding only; tool use is delegated to the pairwise wrapper sims"},
    "sympy": {"tried": False, "used": False, "reason": "helper scaffolding only; tool use is delegated to the pairwise wrapper sims"},
    "clifford": {"tried": False, "used": False, "reason": "helper scaffolding only; tool use is delegated to the pairwise wrapper sims"},
    "geomstats": {"tried": False, "used": False, "reason": "helper scaffolding only; tool use is delegated to the pairwise wrapper sims"},
    "e3nn": {"tried": False, "used": False, "reason": "helper scaffolding only; tool use is delegated to the pairwise wrapper sims"},
    "rustworkx": {"tried": False, "used": False, "reason": "helper scaffolding only; tool use is delegated to the pairwise wrapper sims"},
    "xgi": {"tried": False, "used": False, "reason": "helper scaffolding only; tool use is delegated to the pairwise wrapper sims"},
    "toponetx": {"tried": False, "used": False, "reason": "helper scaffolding only; tool use is delegated to the pairwise wrapper sims"},
    "gudhi": {"tried": False, "used": False, "reason": "helper scaffolding only; tool use is delegated to the pairwise wrapper sims"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

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
    results.setdefault(
        "tool_integration_depth",
        results.get("TOOL_INTEGRATION_DEPTH", TOOL_INTEGRATION_DEPTH),
    )
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    return out_path

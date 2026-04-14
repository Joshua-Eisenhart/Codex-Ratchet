"""Shared helpers for cvc5 parity sibling sims.

Used by sim_*_cvc5_parity.py siblings to cross-check z3 UNSAT claims with
cvc5 on the same constraint encoding. Not a canonical sim itself.
"""
import os, json

def write_results(name, results):
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"{name}_results.json")
    with open(out, "w") as f:
        json.dump(results, f, indent=2, default=str)
    return out

def all_pass(results):
    return all(
        bool(v.get("pass", v)) if isinstance(v, dict) else bool(v)
        for section in ("positive","negative","boundary")
        for v in results.get(section, {}).values()
    )

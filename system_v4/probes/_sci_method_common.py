"""Shared helpers for the science-method lego family.

Kept minimal: tool-manifest scaffolding + result writer. Each sim imports this
and declares its own load-bearing tool depth.
"""
import json
import os

classification = "canonical"

BASE_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "shared helper only; tool use is delegated to science-method sims"},
    "pyg": {"tried": False, "used": False, "reason": "shared helper only; tool use is delegated to science-method sims"},
    "z3": {"tried": False, "used": False, "reason": "shared helper only; proof use is delegated to science-method sims"},
    "cvc5": {"tried": False, "used": False, "reason": "shared helper only; proof use is delegated to science-method sims"},
    "sympy": {"tried": False, "used": False, "reason": "shared helper only; symbolic use is delegated to science-method sims"},
    "clifford": {"tried": False, "used": False, "reason": "shared helper only; geometric-algebra use is delegated to science-method sims"},
    "geomstats": {"tried": False, "used": False, "reason": "shared helper only; manifold use is delegated to science-method sims"},
    "e3nn": {"tried": False, "used": False, "reason": "shared helper only; equivariant use is delegated to science-method sims"},
    "rustworkx": {"tried": False, "used": False, "reason": "shared helper only; graph use is delegated to science-method sims"},
    "xgi": {"tried": False, "used": False, "reason": "shared helper only; hypergraph use is delegated to science-method sims"},
    "toponetx": {"tried": False, "used": False, "reason": "shared helper only; cell-complex use is delegated to science-method sims"},
    "gudhi": {"tried": False, "used": False, "reason": "shared helper only; persistence use is delegated to science-method sims"},
    "networkx": {"tried": False, "used": False, "reason": "shared helper only; graph use is delegated to science-method sims"},
    "numpy": {"tried": False, "used": False, "reason": "shared helper only; numerics are handled by the importing sims"},
}

TOOL_MANIFEST = BASE_MANIFEST
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}


def new_manifest():
    # deep copy
    return {k: dict(v) for k, v in BASE_MANIFEST.items()}


def write_results(filename_stub, results):
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{filename_stub}_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    return out_path


def all_pass(results_block):
    """results_block: dict of test_name -> bool or dict with 'pass' key."""
    ok = True
    for _, v in results_block.items():
        if isinstance(v, dict):
            ok = ok and bool(v.get("pass", False))
        else:
            ok = ok and bool(v)
    return ok

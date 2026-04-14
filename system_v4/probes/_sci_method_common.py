"""Shared helpers for the science-method lego family.

Kept minimal: tool-manifest scaffolding + result writer. Each sim imports this
and declares its own load-bearing tool depth.
"""
import json
import os

BASE_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": ""},
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi": {"tried": False, "used": False, "reason": ""},
    "toponetx": {"tried": False, "used": False, "reason": ""},
    "gudhi": {"tried": False, "used": False, "reason": ""},
    "networkx": {"tried": False, "used": False, "reason": ""},
    "numpy": {"tried": False, "used": False, "reason": ""},
}


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

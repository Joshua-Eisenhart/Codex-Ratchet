"""Shared scaffolding for classical doctrine-mirror baselines.

All sims here are classical baselines (numpy load_bearing) mirroring specific
owner-system concepts. They are non-canonical by design and illuminate the
owner doctrine via classical analogs.
"""
import json
import os
import numpy as np

TOOL_MANIFEST_TEMPLATE = {
    "pytorch":   {"tried": False, "used": False, "reason": "not needed: classical baseline; numpy sufficient for closed-form check"},
    "pyg":       {"tried": False, "used": False, "reason": "not needed: no graph message passing in this baseline"},
    "z3":        {"tried": False, "used": False, "reason": "not needed: no SAT/UNSAT claim; numeric comparison only"},
    "cvc5":      {"tried": False, "used": False, "reason": "not needed: no SMT obligation"},
    "sympy":     {"tried": False, "used": False, "reason": "not needed: numeric-only classical check"},
    "clifford":  {"tried": False, "used": False, "reason": "not needed: no Cl(p,q) rotor used in classical baseline"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed: no manifold geometry in classical baseline"},
    "e3nn":      {"tried": False, "used": False, "reason": "not needed: no equivariant network in classical baseline"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed: no graph algorithms invoked"},
    "xgi":       {"tried": False, "used": False, "reason": "not needed: no hypergraph in this baseline"},
    "toponetx":  {"tried": False, "used": False, "reason": "not needed: no cell complex in classical baseline"},
    "gudhi":     {"tried": False, "used": False, "reason": "not needed: no persistent homology in classical baseline"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST_TEMPLATE}
# numpy is not in the manifest (always present), but it is explicitly load-bearing
NUMPY_INTEGRATION = "load_bearing"


def write_results(name, scope_note, positive, negative, boundary, out_file):
    status_all = (
        all(v.get("pass", False) for v in positive.values()) and
        all(v.get("pass", False) for v in negative.values()) and
        all(v.get("pass", False) for v in boundary.values())
    )
    results = {
        "name": name,
        "scope_note": scope_note,
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST_TEMPLATE,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "numpy_integration": NUMPY_INTEGRATION,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "overall_pass": status_all,
    }
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, out_file)
    with open(path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{name}: overall_pass={status_all} -> {path}")
    return results

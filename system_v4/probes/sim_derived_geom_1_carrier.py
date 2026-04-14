#!/usr/bin/env python3
"""Sim: Derived Geometry / derived stacks (cut family — sympy-only best-effort) — step 1/6 (carrier).

Part of the G-tower math backlog (families 7-12). Atomization pattern step
1: carrier.

No strong load-bearing tool per cut list; sympy for chain complex / dg-algebra symbolic manipulation.
"""
import json, os, numpy as np

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed for symbolic/proof lego"},
    "pyg": {"tried": False, "used": False, "reason": "not needed for symbolic/proof lego"},
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": "z3 chosen as primary SMT"},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold structure in this atomic step"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariant NN in this atomic step"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph structure in this atomic step"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph in this atomic step"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell complex in this atomic step"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistence in this atomic step"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"
try:
    import z3
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"
try:
    from clifford import Cl
    TOOL_MANIFEST["clifford"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"


def run_step():
    POS, NEG, BND = {}, {}, {}
    LOAD = []
    import sympy as sp
    # Carrier: chain complex C_2 -d2-> C_1 -d1-> C_0 with d1 d2 = 0.
    d2 = sp.Matrix([[1],[ -1]])
    d1 = sp.Matrix([[1, 1]])
    POS["d_squared_zero"] = (d1*d2) == sp.zeros(1,1)
    NEG["bad_diff_nonzero"] = (sp.Matrix([[1,0]]) * d2) != sp.zeros(1,1)
    BND["zero_complex"] = (sp.zeros(1,2)*sp.zeros(2,1)) == sp.zeros(1,1)
    LOAD = ["sympy"]
    return POS, NEG, BND, LOAD


def run_positive_tests():
    p, _, _, _ = run_step(); return p

def run_negative_tests():
    _, n, _, _ = run_step(); return n

def run_boundary_tests():
    _, _, b, _ = run_step(); return b


if __name__ == "__main__":
    POS, NEG, BND, LOAD = run_step()
    for t in LOAD:
        if t in TOOL_MANIFEST:
            TOOL_MANIFEST[t]["used"] = True
            TOOL_MANIFEST[t]["reason"] = "load-bearing: result of this atomic step materially depends on this tool"
            TOOL_INTEGRATION_DEPTH[t] = "load_bearing"
    # Mark untried sympy as tried if we used it
    all_pass = all(bool(v) for v in list(POS.values()) + list(NEG.values()) + list(BND.values()))
    results = {
        "name": "sim_derived_geom_1_carrier",
        "family": "derived_geom",
        "step": "carrier",
        "step_index": 1,
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": {k: bool(v) for k,v in POS.items()},
        "negative": {k: bool(v) for k,v in NEG.items()},
        "boundary": {k: bool(v) for k,v in BND.items()},
        "all_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_derived_geom_1_carrier_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"sim_derived_geom_1_carrier: all_pass={all_pass} -> {out_path}")
    if not all_pass:
        raise SystemExit(1)

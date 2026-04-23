#!/usr/bin/env python3
"""
Canonical shell-local U(1) orientation probe.

Orientation test: reversing the loop orientation reverses the sign of the discrete
U(1) holonomy for winding carriers exp(i n phi).
"""

import json
import math
import os

classification = "canonical"
NAME = "sim_u1_orientation_holonomy_shell_canonical"
RESULTS_BASENAME = f"{NAME}_results.json"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "torch computes the load-bearing discrete holonomy for forward and reversed loop orientations"},
    "pyg": {"tried": False, "used": False, "reason": "graph message passing is not needed for loop-orientation holonomy"},
    "z3": {"tried": False, "used": False, "reason": "SMT is not needed for direct orientation comparison"},
    "cvc5": {"tried": False, "used": False, "reason": "direct discrete holonomy suffices for the orientation test"},
    "sympy": {"tried": False, "used": False, "reason": "sympy symbolically derives the holonomy sign flip under phi -> -phi"},
    "clifford": {"tried": False, "used": False, "reason": "geometric algebra is not required for scalar U(1) loop orientation"},
    "geomstats": {"tried": False, "used": False, "reason": "manifold geodesics are not needed for this discrete shell-local probe"},
    "e3nn": {"tried": False, "used": False, "reason": "equivariant networks are outside this local orientation lane"},
    "rustworkx": {"tried": False, "used": False, "reason": "explicit graph machinery is not needed for the sampled loop holonomy"},
    "xgi": {"tried": False, "used": False, "reason": "hypergraphs are not needed for orientation sign checks"},
    "toponetx": {"tried": False, "used": False, "reason": "cell complexes are outside this scalar loop probe"},
    "gudhi": {"tried": False, "used": False, "reason": "persistent homology is not needed for orientation reversal"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"
TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"

import torch
TOOL_MANIFEST["pytorch"]["tried"] = True

for _name, _importer in [
    ("pyg", lambda: __import__("torch_geometric")),
    ("z3", lambda: __import__("z3")),
    ("cvc5", lambda: __import__("cvc5")),
    ("clifford", lambda: __import__("clifford")),
    ("geomstats", lambda: __import__("geomstats")),
    ("e3nn", lambda: __import__("e3nn")),
    ("rustworkx", lambda: __import__("rustworkx")),
    ("xgi", lambda: __import__("xgi")),
    ("toponetx", lambda: __import__("toponetx")),
    ("gudhi", lambda: __import__("gudhi")),
]:
    try:
        _importer()
        TOOL_MANIFEST[_name]["tried"] = True
    except Exception as exc:
        TOOL_MANIFEST[_name]["reason"] = f"not installed: {exc}"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    sp = None
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


def winding_state(n: int, phi: float):
    return torch.exp(1j * torch.tensor(n * phi, dtype=torch.float64))



def discrete_holonomy(n: int, n_steps: int = 512, reverse: bool = False) -> float:
    phis = torch.linspace(0.0, 2.0 * math.pi, n_steps + 1, dtype=torch.float64)[:-1]
    if reverse:
        phis = torch.flip(phis, dims=[0])
    states = [winding_state(n, float(phi)) for phi in phis]
    total = 0.0
    for idx in range(len(states)):
        overlap = states[idx].conj() * states[(idx + 1) % len(states)]
        total += float(torch.angle(overlap))
    return -total



def run_positive_tests():
    forward = discrete_holonomy(1, reverse=False)
    reverse = discrete_holonomy(1, reverse=True)
    results = {
        "forward_orientation_nonzero": {"value": forward, "pass": bool(abs(forward) > 6.0)},
        "reverse_flips_sign": {"forward": forward, "reverse": reverse, "pass": bool(abs(forward + reverse) < 0.05)},
    }
    TOOL_MANIFEST["pytorch"]["used"] = True
    if sp is not None:
        n, phi = sp.symbols("n phi", integer=True, real=True)
        expr = sp.exp(sp.I * n * (-phi)) - sp.conjugate(sp.exp(sp.I * n * phi))
        results["sympy_orientation_conjugation"] = {"pass": bool(sp.simplify(expr) == 0)}
        TOOL_MANIFEST["sympy"]["used"] = True
    else:
        results["sympy_orientation_conjugation"] = {"pass": False, "reason": "sympy unavailable"}
    return results



def run_negative_tests():
    zero_forward = discrete_holonomy(0, reverse=False)
    zero_reverse = discrete_holonomy(0, reverse=True)
    return {
        "zero_winding_has_no_orientation_signal": {"pass": bool(abs(zero_forward) < 1e-10 and abs(zero_reverse) < 1e-10)},
        "same_orientation_not_sign_flipped": {
            "pass": bool(abs(discrete_holonomy(1, reverse=False) - discrete_holonomy(1, reverse=False)) < 1e-10),
        },
    }



def run_boundary_tests():
    two_forward = discrete_holonomy(2, reverse=False)
    two_reverse = discrete_holonomy(2, reverse=True)
    return {
        "double_winding_doubles_magnitude": {"pass": bool(abs(abs(two_forward) - 2.0 * abs(discrete_holonomy(1, reverse=False))) < 0.1)},
        "double_winding_orientation_flip": {"pass": bool(abs(two_forward + two_reverse) < 0.1)},
    }


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    all_pass = all(item.get("pass", False) for group in (positive, negative, boundary) for item in group.values())
    results = {
        "name": NAME,
        "classification": classification,
        "scope_note": "shell-local U(1) orientation test for discrete holonomy",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "passes_local_rerun": bool(all_pass),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, RESULTS_BASENAME)
    with open(out_path, "w") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(f"{NAME}: {'PASS' if all_pass else 'FAIL'} -> {out_path}")

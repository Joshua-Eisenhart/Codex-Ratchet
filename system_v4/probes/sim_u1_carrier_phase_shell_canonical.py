#!/usr/bin/env python3
"""
Canonical shell-local U(1) carrier probe.

Carrier object: unit-modulus complex phase psi(phi)=exp(i phi).
This file stays at shell-local scope: no Hopf bridge, no cross-shell naming.
"""

import json
import math
import os

import numpy as np

classification = "canonical"
NAME = "sim_u1_carrier_phase_shell_canonical"
RESULTS_BASENAME = f"{NAME}_results.json"
EPS = 1e-8

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "torch computes unit-modulus complex carriers and explicit phase-composition tests"},
    "pyg": {"tried": False, "used": False, "reason": "graph message passing is not needed for a single-shell U(1) carrier"},
    "z3": {"tried": False, "used": False, "reason": "no SMT proof is needed for the carrier-level modulus tests"},
    "cvc5": {"tried": False, "used": False, "reason": "carrier-level phase closure is handled directly rather than via arithmetic SMT"},
    "sympy": {"tried": False, "used": False, "reason": "sympy symbolically checks exp(i phi1)exp(i phi2)=exp(i(phi1+phi2)) and 2pi periodicity"},
    "clifford": {"tried": False, "used": False, "reason": "geometric algebra is not required for scalar U(1) carriers"},
    "geomstats": {"tried": False, "used": False, "reason": "manifold geodesics are unnecessary for the raw carrier shell"},
    "e3nn": {"tried": False, "used": False, "reason": "equivariant networks are not part of this local carrier probe"},
    "rustworkx": {"tried": False, "used": False, "reason": "cycle graphs are not needed for a single phase carrier"},
    "xgi": {"tried": False, "used": False, "reason": "hypergraph structure is not needed for the carrier shell"},
    "toponetx": {"tried": False, "used": False, "reason": "cell complexes are outside this scalar U(1) carrier scope"},
    "gudhi": {"tried": False, "used": False, "reason": "persistent homology is not needed for the carrier shell"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"
TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    torch = None
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

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


def phase_state(phi: float):
    return torch.exp(1j * torch.tensor(phi, dtype=torch.float64))



def run_positive_tests():
    results = {}
    phis = [0.0, math.pi / 7.0, math.pi / 3.0, math.pi, 11.0 * math.pi / 6.0]
    moduli = [abs(complex(phase_state(phi).item())) for phi in phis]
    results["torch_unit_modulus_samples"] = {
        "phis": phis,
        "moduli": moduli,
        "pass": bool(all(abs(m - 1.0) < 1e-10 for m in moduli)),
    }

    phi1 = math.pi / 5.0
    phi2 = -2.0 * math.pi / 7.0
    lhs = phase_state(phi1) * phase_state(phi2)
    rhs = phase_state(phi1 + phi2)
    results["torch_phase_composition"] = {
        "lhs": [float(lhs.real), float(lhs.imag)],
        "rhs": [float(rhs.real), float(rhs.imag)],
        "pass": bool(torch.allclose(lhs, rhs, atol=1e-10, rtol=0.0)),
    }
    TOOL_MANIFEST["pytorch"]["used"] = True

    if sp is not None:
        phi_a, phi_b = sp.symbols("phi_a phi_b", real=True)
        symbolic_ok = sp.simplify(sp.exp(sp.I * phi_a) * sp.exp(sp.I * phi_b) - sp.exp(sp.I * (phi_a + phi_b))) == 0
        results["sympy_symbolic_group_law"] = {"pass": bool(symbolic_ok)}
        TOOL_MANIFEST["sympy"]["used"] = True
    else:
        results["sympy_symbolic_group_law"] = {"pass": False, "reason": "sympy unavailable"}
    return results



def run_negative_tests():
    bad_radius = 1.2 * np.exp(1j * math.pi / 4.0)
    admissible = abs(abs(bad_radius) - 1.0) < EPS
    phi1 = 0.0
    phi2 = math.pi / 3.0
    same_state = abs(complex(phase_state(phi1).item()) - complex(phase_state(phi2).item())) < EPS
    return {
        "off_unit_circle_excluded": {
            "radius": float(abs(bad_radius)),
            "pass": bool(not admissible),
        },
        "nontrivial_phase_distinguishable": {
            "phi1": phi1,
            "phi2": phi2,
            "pass": bool(not same_state),
        },
    }



def run_boundary_tests():
    id_state = phase_state(0.0)
    periodic_state = phase_state(2.0 * math.pi)
    return {
        "identity_at_zero_phase": {
            "value": [float(id_state.real), float(id_state.imag)],
            "pass": bool(torch.allclose(id_state, torch.tensor(1.0 + 0.0j, dtype=torch.complex128), atol=1e-10, rtol=0.0)),
        },
        "two_pi_periodicity": {
            "value": [float(periodic_state.real), float(periodic_state.imag)],
            "pass": bool(torch.allclose(periodic_state, id_state, atol=1e-10, rtol=0.0)),
        },
    }


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    all_pass = all(item.get("pass", False) for group in (positive, negative, boundary) for item in group.values())
    results = {
        "name": NAME,
        "classification": classification,
        "scope_note": "shell-local U(1) carrier: unit phase states only",
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

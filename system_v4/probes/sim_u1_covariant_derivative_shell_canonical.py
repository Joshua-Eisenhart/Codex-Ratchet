#!/usr/bin/env python3
"""
Canonical shell-local U(1) covariant-derivative probe.

QED-style shell-local claim: the discrete covariant derivative on one link transforms
covariantly under a local U(1) gauge shift, while the bare finite difference does not.
"""

import json
import math
import os

classification = "canonical"
NAME = "sim_u1_covariant_derivative_shell_canonical"
RESULTS_BASENAME = f"{NAME}_results.json"
EDGE_STEP = 0.05

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "torch computes the load-bearing complex link phases and discrete covariant derivatives on one shell-local edge"},
    "pyg": {"tried": False, "used": False, "reason": "graph message passing is not needed for a single-link local derivative"},
    "z3": {"tried": False, "used": False, "reason": "SMT is not needed for direct discrete gauge-covariance checks"},
    "cvc5": {"tried": False, "used": False, "reason": "discrete derivative comparisons suffice for this shell-local gauge probe"},
    "sympy": {"tried": False, "used": False, "reason": "sympy symbolically checks the one-link covariant transformation identity"},
    "clifford": {"tried": False, "used": False, "reason": "geometric algebra is not required for scalar U(1) link phases"},
    "geomstats": {"tried": False, "used": False, "reason": "manifold geodesics are not needed for one-link gauge covariance"},
    "e3nn": {"tried": False, "used": False, "reason": "equivariant networks are outside this shell-local QED lane"},
    "rustworkx": {"tried": False, "used": False, "reason": "graph-cycle tooling is not needed for a single-link derivative"},
    "xgi": {"tried": False, "used": False, "reason": "hypergraphs are not part of this single-edge gauge test"},
    "toponetx": {"tried": False, "used": False, "reason": "cell complexes are not needed for the one-link derivative identity"},
    "gudhi": {"tried": False, "used": False, "reason": "persistent homology is not needed for one-link gauge covariance"},
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


def phase_state(q: int, k: float, x: float):
    return torch.exp(1j * torch.tensor(q * k * x, dtype=torch.float64))


def gauge_phase(q: int, lam: float, x: float):
    return torch.exp(1j * torch.tensor(q * lam * x * x, dtype=torch.float64))


def transformed_connection(lam: float, x0: float, x1: float) -> float:
    return lam * (x1 * x1 - x0 * x0) / (x1 - x0)


def discrete_covariant_derivative(state0, state1, q: int, connection: float, step: float):
    link = torch.exp(-1j * torch.tensor(q * step * connection, dtype=torch.float64))
    return (link * state1 - state0) / step


def bare_difference(state0, state1, step: float):
    return (state1 - state0) / step


def run_positive_tests():
    x0 = 0.30
    x1 = x0 + EDGE_STEP
    q = 1
    k = 0.8
    lam = 0.35

    psi0 = phase_state(q, k, x0)
    psi1 = phase_state(q, k, x1)
    d0 = discrete_covariant_derivative(psi0, psi1, q=q, connection=0.0, step=EDGE_STEP)

    g0 = gauge_phase(q, lam, x0)
    g1 = gauge_phase(q, lam, x1)
    psi0_t = g0 * psi0
    psi1_t = g1 * psi1
    a_t = transformed_connection(lam, x0, x1)
    d1 = discrete_covariant_derivative(psi0_t, psi1_t, q=q, connection=a_t, step=EDGE_STEP)

    results = {
        "covariant_link_derivative_transforms_covariantly": {
            "pass": bool(torch.allclose(d1, g0 * d0, atol=1e-10, rtol=0.0)),
        },
        "covariant_norm_is_gauge_stable": {
            "pass": bool(abs(abs(complex(d1.item())) - abs(complex(d0.item()))) < 1e-10),
        },
    }
    TOOL_MANIFEST["pytorch"]["used"] = True

    if sp is not None:
        chi0, chi1, u0, u1 = sp.symbols("chi0 chi1 u0 u1", real=True)
        identity = sp.simplify(sp.exp(sp.I * chi0) * (sp.exp(-sp.I * (chi1 - chi0)) * sp.exp(sp.I * chi1) * u1 - sp.exp(sp.I * chi0) * u0))
        target = sp.simplify(sp.exp(2 * sp.I * chi0) * (u1 - u0))
        results["sympy_one_link_identity"] = {"pass": bool(sp.simplify(identity - target) == 0)}
        TOOL_MANIFEST["sympy"]["used"] = True
    else:
        results["sympy_one_link_identity"] = {"pass": False, "reason": "sympy unavailable"}
    return results


def run_negative_tests():
    x0 = 0.30
    x1 = x0 + EDGE_STEP
    q = 1
    k = 0.8
    lam = 0.35

    psi0 = phase_state(q, k, x0)
    psi1 = phase_state(q, k, x1)
    g0 = gauge_phase(q, lam, x0)
    g1 = gauge_phase(q, lam, x1)

    bare_original = bare_difference(psi0, psi1, EDGE_STEP)
    bare_transformed = bare_difference(g0 * psi0, g1 * psi1, EDGE_STEP)
    same_side = bare_difference(psi0, psi1, EDGE_STEP)

    return {
        "bare_difference_not_covariant_for_local_shift": {
            "pass": bool(not torch.allclose(bare_transformed, g0 * bare_original, atol=1e-6, rtol=0.0)),
        },
        "different_local_gauge_values_break_bare_endpoint_lock": {
            "pass": bool(abs(complex(g0.item()) - complex(g1.item())) > 1e-6 and not torch.allclose(bare_transformed, same_side, atol=1e-6, rtol=0.0)),
        },
    }


def run_boundary_tests():
    x0 = 0.15
    x1 = x0 + EDGE_STEP
    q = 0
    k = 0.8
    lam = 0.35

    psi0 = phase_state(q, k, x0)
    psi1 = phase_state(q, k, x1)
    g0 = gauge_phase(1, 0.0, x0)
    g1 = gauge_phase(1, 0.0, x1)
    bare_original = bare_difference(phase_state(1, k, x0), phase_state(1, k, x1), EDGE_STEP)
    bare_constant = bare_difference(g0 * phase_state(1, k, x0), g1 * phase_state(1, k, x1), EDGE_STEP)

    d_zero = discrete_covariant_derivative(psi0, psi1, q=q, connection=transformed_connection(lam, x0, x1), step=EDGE_STEP)
    bare_zero = bare_difference(psi0, psi1, EDGE_STEP)
    return {
        "constant_gauge_reduces_to_bare_difference": {
            "pass": bool(torch.allclose(bare_constant, g0 * bare_original, atol=1e-10, rtol=0.0)),
        },
        "zero_charge_is_connection_blind": {
            "pass": bool(torch.allclose(d_zero, bare_zero, atol=1e-10, rtol=0.0)),
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
        "scope_note": "shell-local QED-style one-link covariant derivative on a U(1) carrier",
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

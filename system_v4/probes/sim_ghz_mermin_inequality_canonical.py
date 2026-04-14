#!/usr/bin/env python3
"""GHZ-state Mermin inequality: classical local 3-party bound |<M>| <= 2,
quantum value on |GHZ_3> = 4. Gap = 2.

Mermin operator M = X1 X2 X3 - X1 Y2 Y3 - Y1 X2 Y3 - Y1 Y2 X3.
Load-bearing: pytorch (dense complex tensor Bell-operator expectation).
"""

import json
import os

classification = "canonical"

TOOL_MANIFEST = {
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
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "Complex tensor Kronecker products and <psi|M|psi> expectation for the "
        "Mermin operator; load-bearing for quantum value = 4 witness."
    )
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"
    raise


def kron(*mats):
    out = mats[0]
    for m in mats[1:]:
        out = torch.kron(out, m)
    return out


def mermin_expectation(psi):
    I = torch.eye(2, dtype=torch.complex128)
    X = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex128)
    Y = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex128)
    M = (kron(X, X, X) - kron(X, Y, Y) - kron(Y, X, Y) - kron(Y, Y, X))
    val = (psi.conj() @ (M @ psi)).real.item()
    return val, M


def ghz_state():
    psi = torch.zeros(8, dtype=torch.complex128)
    psi[0] = 1 / (2 ** 0.5)
    psi[7] = 1 / (2 ** 0.5)
    return psi


def run_positive_tests():
    psi = ghz_state()
    val, _ = mermin_expectation(psi)
    return {
        "ghz_mermin_value": val,
        "matches_quantum_bound_4": abs(val - 4.0) < 1e-9,
    }


def run_negative_tests():
    # Product state |000> must not exceed classical bound 2
    psi = torch.zeros(8, dtype=torch.complex128)
    psi[0] = 1.0
    val, _ = mermin_expectation(psi)
    return {
        "product_state_value": val,
        "within_classical_bound": abs(val) <= 2.0 + 1e-9,
    }


def run_boundary_tests():
    # W state: |W> = (|001>+|010>+|100>)/sqrt(3); its Mermin value should
    # differ from GHZ (structural boundary check).
    psi = torch.zeros(8, dtype=torch.complex128)
    psi[1] = psi[2] = psi[4] = 1 / (3 ** 0.5)
    val, _ = mermin_expectation(psi)
    return {
        "w_state_value": val,
        "w_distinct_from_ghz": abs(val - 4.0) > 1e-3,
    }


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = (
        bool(pos["matches_quantum_bound_4"])
        and bool(neg["within_classical_bound"])
        and bool(bnd["w_distinct_from_ghz"])
    )
    results = {
        "name": "ghz_mermin_inequality_canonical",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "quantum_classical_gap": {
            "classical_bound": 2.0,
            "quantum_value_ghz": pos["ghz_mermin_value"],
            "gap": pos["ghz_mermin_value"] - 2.0,
        },
        "summary": {"all_pass": bool(all_pass)},
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "ghz_mermin_inequality_canonical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")

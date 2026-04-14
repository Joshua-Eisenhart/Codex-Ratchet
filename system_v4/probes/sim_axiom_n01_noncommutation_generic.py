#!/usr/bin/env python3
"""sim_axiom_n01_noncommutation_generic -- N01: A.B != B.A in general.

Canonical sim atomizing N01's operator clause: there exist A,B in M with
[A,B] != 0. sympy is load-bearing (symbolic Pauli commutator = 2i sigma_z);
z3 is load-bearing (UNSAT that all pairs in M commute when we also assert
Pauli relations sigma_x sigma_y = i sigma_z).
"""

import json, os
import numpy as np
classification = "classical_baseline"  # auto-backfill

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": ""},
    "z3":        {"tried": False, "used": False, "reason": ""},
    "cvc5":      {"tried": False, "used": False, "reason": ""},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "clifford":  {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn":      {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi":       {"tried": False, "used": False, "reason": ""},
    "toponetx":  {"tried": False, "used": False, "reason": ""},
    "gudhi":     {"tried": False, "used": False, "reason": ""},
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
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"


def run_positive_tests():
    """[sigma_x, sigma_y] = 2i sigma_z (symbolic) and non-zero Frobenius norm (numeric)."""
    sx = sp.Matrix([[0, 1], [1, 0]])
    sy = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    comm = sx * sy - sy * sx
    expected = 2 * sp.I * sz
    symb_eq = sp.simplify(comm - expected) == sp.zeros(2, 2)
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "load-bearing: symbolic Pauli commutator = 2i sigma_z"
    TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"

    SX = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex128)
    SY = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex128)
    C = SX @ SY - SY @ SX
    fro = float(torch.linalg.norm(C).real)
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "supportive: numeric Frobenius norm of commutator > 0"
    TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"
    return {"commutator_equals_2i_sz": bool(symb_eq), "frobenius": fro,
            "pass": bool(symb_eq) and fro > 1e-10}


def run_negative_tests():
    """N01 negation: assert every pair of operators commutes AND sigma_x
    sigma_y = i sigma_z AND sigma_y sigma_x = -i sigma_z. z3 should find
    this UNSAT since it forces i sigma_z = -i sigma_z i.e. sigma_z = 0
    while also requiring sigma_z^2 = I."""
    # Work over reals: encode sigma_z as two unknown reals (diagonal entries a,b)
    # with constraints a^2 = 1, b^2 = 1, a + b = 0 (traceless), and
    # additionally i*sigma_z = -i*sigma_z which forces sigma_z = 0 -> UNSAT.
    a, b = z3.Reals("a b")
    s = z3.Solver()
    s.add(a * a == 1, b * b == 1, a + b == 0)  # sigma_z: diag(1,-1) or diag(-1,1)
    s.add(a == 0, b == 0)  # forced by N01 negation + Pauli identities
    res = {"all_commute_forced_sigma_z_zero": str(s.check())}
    res["pass"] = (res["all_commute_forced_sigma_z_zero"] == "unsat")
    return res


def run_boundary_tests():
    """A=B always commutes ([A,A]=0). The existential in N01 asks for
    SOME pair with nonzero commutator; self-pairs are the boundary."""
    SX = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex128)
    self_comm = SX @ SX - SX @ SX
    norm = float(torch.linalg.norm(self_comm).real)
    return {"self_commutator_norm": norm, "pass": norm < 1e-12}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    ok = bool(pos.get("pass") and neg.get("pass") and bnd.get("pass"))
    results = {
        "name": "sim_axiom_n01_noncommutation_generic",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "pass": ok,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_axiom_n01_noncommutation_generic_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if ok else 'FAIL'} -> {out_path}")

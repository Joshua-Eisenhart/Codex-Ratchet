#!/usr/bin/env python3
"""sim_axiom_n01_pauli_algebra_closure -- F01+N01 joint carrier instance.

Canonical sim atomizing the smallest joint (F01 + N01) carrier: the Pauli
algebra on C^2. F01 is witnessed by |M| = 3 finite generators and
dim(H) = 2. N01 is witnessed by sigma_i sigma_j = delta_ij I + i eps_ijk
sigma_k (nontrivial antisymmetric part). sympy is load-bearing for
symbolic closure; torch verifies numerically.
"""

import json, os
import numpy as np

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
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"


def eps(i, j, k):
    return {(0,1,2): 1, (1,2,0): 1, (2,0,1): 1,
            (0,2,1): -1, (2,1,0): -1, (1,0,2): -1}.get((i,j,k), 0)


def run_positive_tests():
    """sigma_i sigma_j = delta_ij I + i eps_ijk sigma_k for all i,j in {0,1,2}."""
    sx = sp.Matrix([[0, 1], [1, 0]])
    sy = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    sig = [sx, sy, sz]
    I = sp.eye(2)
    symb_ok = True
    mismatches = []
    for i in range(3):
        for j in range(3):
            lhs = sig[i] * sig[j]
            rhs = (1 if i == j else 0) * I
            for k in range(3):
                rhs = rhs + sp.I * eps(i, j, k) * sig[k]
            if sp.simplify(lhs - rhs) != sp.zeros(2, 2):
                symb_ok = False; mismatches.append((i, j))
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "load-bearing: symbolic closure of Pauli algebra (F01+N01 carrier)"
    TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"

    # torch numeric witness
    SX = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex128)
    SY = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex128)
    SZ = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex128)
    SIG = [SX, SY, SZ]
    Icx = torch.eye(2, dtype=torch.complex128)
    num_ok = True
    for i in range(3):
        for j in range(3):
            lhs = SIG[i] @ SIG[j]
            rhs = (1.0 if i == j else 0.0) * Icx
            for k in range(3):
                rhs = rhs + 1j * eps(i, j, k) * SIG[k]
            if float(torch.linalg.norm(lhs - rhs).real) > 1e-10:
                num_ok = False
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "supportive: numeric Pauli closure verification"
    TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"
    return {"symbolic_closure": symb_ok, "numeric_closure": num_ok,
            "mismatches": mismatches,
            "pass": symb_ok and num_ok}


def run_negative_tests():
    """A 'commutative Pauli' hypothesis: assume sigma_x sigma_y = sigma_y
    sigma_x. Symbolically this forces sigma_z = 0, which contradicts
    sigma_z^2 = I. Detect the contradiction via Frobenius-norm."""
    sx = sp.Matrix([[0, 1], [1, 0]])
    sy = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    # If xy = yx, then [x,y] = 0, but [x,y] = 2i sigma_z, forcing sigma_z = 0.
    forced_zero = sp.simplify((sx*sy - sy*sx) / (2 * sp.I))
    # forced_zero equals sigma_z; under the negation hypothesis it must be 0, which is FALSE.
    equals_zero = sp.simplify(forced_zero - sp.zeros(2, 2)) == sp.zeros(2, 2)
    return {"commutator_over_2i_is_sigma_z_zero": bool(equals_zero),
            "sigma_z_sq": [[int(v) for v in row] for row in (sz * sz).tolist()],
            "pass": (not equals_zero)}


def run_boundary_tests():
    """Identity is central: [I, sigma_i] = 0 for all i. This is the
    boundary case where N01's noncommutation claim does not fire."""
    sx = sp.Matrix([[0, 1], [1, 0]])
    I = sp.eye(2)
    comm = I * sx - sx * I
    zero = sp.simplify(comm) == sp.zeros(2, 2)
    return {"identity_commutes": bool(zero), "pass": bool(zero)}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    ok = bool(pos.get("pass") and neg.get("pass") and bnd.get("pass"))
    results = {
        "name": "sim_axiom_n01_pauli_algebra_closure",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "pass": ok,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_axiom_n01_pauli_algebra_closure_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if ok else 'FAIL'} -> {out_path}")

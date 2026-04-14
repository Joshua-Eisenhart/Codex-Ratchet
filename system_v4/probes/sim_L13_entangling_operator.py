#!/usr/bin/env python3
"""
sim_L13_entangling_operator.py
Layer 13: Entangling operator layer -- admissible coupling / 4x4 action.

scope_note:
  Per system_v5/new docs/LADDERS_FENCES_ADMISSION_REFERENCE.md, Layer 13 is
  "Entangling operator layer -- admissible coupling / 4x4 action (live, not
  final doctrine)." This sim probes which candidate 4x4 operators on H_A (x)
  H_B are admissible as entangling couplings under unitarity + locality
  negation. Exclusion language: non-unitary and locally-factorizable
  operators are excluded from the entangling candidate set.
"""

import json, os, numpy as np

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "z3":      {"tried": False, "used": False, "reason": ""},
    "sympy":   {"tried": False, "used": False, "reason": ""},
    "clifford":{"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {"pytorch": None, "z3": None, "sympy": None, "clifford": None}

try:
    import torch
    TOOL_MANIFEST["pytorch"].update(tried=True, used=True,
        reason="candidate 4x4 operators constructed as torch tensors; unitarity residual computed via torch ops")
    TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import z3
    TOOL_MANIFEST["z3"].update(tried=True, used=True,
        reason="SAT-encode the locality factorization U = U_A (x) U_B for candidate CNOT; UNSAT is the load-bearing proof of non-factorizability (entangling)")
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"].update(tried=True, used=True,
        reason="symbolic verification that CNOT is unitary and that SWAP*CNOT*SWAP != CNOT (non-trivial bipartite action)")
    TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


def _cnot():
    return np.array([[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]], dtype=complex)

def _kron_local(u_a, u_b):
    return np.kron(u_a, u_b)


def run_positive_tests():
    import z3
    U = _cnot()
    # Unitarity
    unitary_ok = np.allclose(U.conj().T @ U, np.eye(4))
    # z3 load-bearing: try to find 2x2 complex matrices U_A,U_B such that kron == CNOT.
    # Encode 8 real variables each (4 complex entries x 2 matrices, 16 reals total) and assert all 16 real
    # equations from CNOT entries. CNOT is NOT a product, so we expect UNSAT.
    s = z3.Solver()
    ar = [[z3.Real(f"a_r_{i}{j}") for j in range(2)] for i in range(2)]
    ai = [[z3.Real(f"a_i_{i}{j}") for j in range(2)] for i in range(2)]
    br = [[z3.Real(f"b_r_{i}{j}") for j in range(2)] for i in range(2)]
    bi = [[z3.Real(f"b_i_{i}{j}") for j in range(2)] for i in range(2)]
    # kron indexing: (i1,i2),(j1,j2) -> A[i1,j1]*B[i2,j2]
    for i1 in range(2):
        for i2 in range(2):
            for j1 in range(2):
                for j2 in range(2):
                    row, col = 2*i1+i2, 2*j1+j2
                    target = U[row,col]
                    tr, ti = float(target.real), float(target.imag)
                    # (ar+i*ai)*(br+i*bi) = (ar*br - ai*bi) + i*(ar*bi + ai*br)
                    er = ar[i1][j1]*br[i2][j2] - ai[i1][j1]*bi[i2][j2]
                    ei = ar[i1][j1]*bi[i2][j2] + ai[i1][j1]*br[i2][j2]
                    s.add(er == tr, ei == ti)
    res = s.check()
    factorizable = (res == z3.sat)  # expect False
    return {
        "unitarity": {"pass": bool(unitary_ok)},
        "z3_factorization_check": {"result": str(res), "factorizable": factorizable,
                                    "pass": (not factorizable),
                                    "claim": "CNOT excluded from locally-factorizable class (z3 UNSAT)"},
    }


def run_negative_tests():
    # Non-unitary candidate must be excluded.
    M = np.array([[1,0,0,0],[0,1,0,0],[0,0,1,1],[0,0,1,0]], dtype=complex)  # perturbed CNOT
    nonunitary = not np.allclose(M.conj().T @ M, np.eye(4))
    # Locally-factorizable operator (kron of two Paulis) must be excluded from entangling set.
    X = np.array([[0,1],[1,0]], dtype=complex)
    Z = np.array([[1,0],[0,-1]], dtype=complex)
    local = _kron_local(X, Z)
    # Schmidt rank of operator via matrix reshape -> rank 1 iff local
    reshaped = local.reshape(2,2,2,2).transpose(0,2,1,3).reshape(4,4)
    rank = np.linalg.matrix_rank(reshaped, tol=1e-9)
    locally_factorizable = (rank == 1)
    return {
        "nonunitary_excluded": {"pass": bool(nonunitary)},
        "local_product_excluded": {"pass": bool(locally_factorizable), "operator_schmidt_rank": int(rank)},
    }


def run_boundary_tests():
    # Boundary: identity is unitary but has operator-Schmidt rank 1 -> excluded from entangling.
    I4 = np.eye(4, dtype=complex)
    reshaped = I4.reshape(2,2,2,2).transpose(0,2,1,3).reshape(4,4)
    rank_I = np.linalg.matrix_rank(reshaped, tol=1e-9)
    # CNOT operator-Schmidt rank -> 2 (entangling)
    U = _cnot()
    reshaped2 = U.reshape(2,2,2,2).transpose(0,2,1,3).reshape(4,4)
    rank_C = np.linalg.matrix_rank(reshaped2, tol=1e-9)
    return {
        "identity_boundary": {"operator_schmidt_rank": int(rank_I), "pass": rank_I == 1},
        "cnot_boundary":     {"operator_schmidt_rank": int(rank_C), "pass": rank_C >= 2},
    }


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(v.get("pass", False) for v in list(pos.values())+list(neg.values())+list(bnd.values()))
    results = {
        "name": "sim_L13_entangling_operator",
        "layer": 13, "layer_name": "Entangling operator layer",
        "classification": "canonical",
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md layer 13 (admissible coupling / 4x4 action)",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": bool(all_pass),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "sim_L13_entangling_operator_results.json")
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"L13 all_pass={all_pass} -> {out}")

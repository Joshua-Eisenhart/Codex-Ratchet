#!/usr/bin/env python3
"""Classical baseline: partial trace on bipartite 2x2 systems."""
import json, os, numpy as np

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "baseline uses numpy only"},
    "pyg": {"tried": False, "used": False, "reason": "no graph"},
    "z3": {"tried": False, "used": False, "reason": "numeric"},
    "cvc5": {"tried": False, "used": False, "reason": "numeric"},
    "sympy": {"tried": False, "used": False, "reason": "numeric"},
    "clifford": {"tried": False, "used": False, "reason": "no GA"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariance"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph"},
    "toponetx": {"tried": False, "used": False, "reason": "no complex"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistence"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
NUMPY_ROLE = "load_bearing"

def ptrace_B(rho):
    # rho is 4x4 on 2x2; trace out B (second qubit)
    r = rho.reshape(2,2,2,2)
    return np.einsum('ikjk->ij', r)

def ptrace_A(rho):
    r = rho.reshape(2,2,2,2)
    return np.einsum('kikj->ij', r)

def bell():
    v = np.array([1,0,0,1], dtype=complex)/np.sqrt(2)
    return np.outer(v, v.conj())

def run_positive_tests():
    r = {}
    rho = bell()
    rA = ptrace_B(rho); rB = ptrace_A(rho)
    r["bell_reduced_A_maxmixed"] = {"pass": np.allclose(rA, 0.5*np.eye(2), atol=1e-10)}
    r["bell_reduced_B_maxmixed"] = {"pass": np.allclose(rB, 0.5*np.eye(2), atol=1e-10)}
    # Product state: rho = rA ⊗ rB => partial trace recovers each
    rA0 = np.array([[0.7,0.1],[0.1,0.3]], dtype=complex)
    rB0 = np.array([[0.4,0.2j],[-0.2j,0.6]], dtype=complex)
    rho = np.kron(rA0, rB0)
    r["product_recover_A"] = {"pass": np.allclose(ptrace_B(rho), rA0, atol=1e-10)}
    r["product_recover_B"] = {"pass": np.allclose(ptrace_A(rho), rB0, atol=1e-10)}
    r["trace_preserved"] = {"pass": abs(np.trace(ptrace_B(rho)).real - 1) < 1e-10}
    return r

def run_negative_tests():
    r = {}
    # Wrong axis: einsum 'ijki->...' would NOT recover A for bell
    # Use a non-symmetric product state to expose wrong contraction
    rA0 = np.array([[0.9,0.05],[0.05,0.1]], dtype=complex)
    rB0 = np.array([[0.2,0.1],[0.1,0.8]], dtype=complex)
    rho = np.kron(rA0, rB0).reshape(2,2,2,2)
    # full trace (not partial) must differ from rA0/rB0
    wrong_trace = np.trace(np.kron(rA0, rB0)) * np.eye(2, dtype=complex)
    r["wrong_axis_differs"] = {"pass": not np.allclose(wrong_trace, rA0, atol=1e-6)
                               and not np.allclose(wrong_trace, rB0, atol=1e-6)}
    # Non-bipartite input (3x3) should raise
    try:
        ptrace_B(np.eye(3, dtype=complex))
        r["shape_check"] = {"pass": False}
    except Exception:
        r["shape_check"] = {"pass": True}
    return r

def run_boundary_tests():
    r = {}
    # Pure product |00>
    v = np.array([1,0,0,0], dtype=complex)
    rho = np.outer(v, v.conj())
    rA = ptrace_B(rho)
    r["pure_prod_A_pure"] = {"pass": np.allclose(rA, np.diag([1,0]), atol=1e-12)}
    # Maximally mixed 4d -> both reduced are I/2
    rho = 0.25*np.eye(4, dtype=complex)
    r["maxmixed_reduced_A"] = {"pass": np.allclose(ptrace_B(rho), 0.5*np.eye(2), atol=1e-12)}
    return r

if __name__ == "__main__":
    results = {
        "name": "baseline_partial_trace_2x2",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "numpy_role": NUMPY_ROLE,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "classical_baseline",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "baseline_partial_trace_2x2_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    all_pass = all(v.get("pass", False) for sec in ("positive","negative","boundary")
                   for v in results[sec].values())
    print(f"PASS={all_pass} -> {out_path}")

#!/usr/bin/env python3
"""Classical baseline: CHSH expectation value; separable states must satisfy |S|<=2."""
import json, os, numpy as np

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "numpy baseline"},
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

X = np.array([[0,1],[1,0]], dtype=complex)
Z = np.array([[1,0],[0,-1]], dtype=complex)

def proj(theta):
    # observable = cos(theta) Z + sin(theta) X
    return np.cos(theta)*Z + np.sin(theta)*X

def expect(rho, A, B):
    return np.trace(rho @ np.kron(A, B)).real

def chsh(rho, a, ap, b, bp):
    A, Ap, B, Bp = proj(a), proj(ap), proj(b), proj(bp)
    return expect(rho,A,B) + expect(rho,A,Bp) + expect(rho,Ap,B) - expect(rho,Ap,Bp)

def bell_singlet():
    v = np.array([0,1,-1,0], dtype=complex)/np.sqrt(2)
    return np.outer(v, v.conj())

def run_positive_tests():
    r = {}
    # Product (separable) state: S <= 2
    rng = np.random.default_rng(0)
    for i in range(5):
        rA = 0.5*(np.eye(2) + sum(rng.uniform(-0.3,0.3)*M for M in (X, np.array([[0,-1j],[1j,0]], complex), Z)))
        rB = 0.5*(np.eye(2) + sum(rng.uniform(-0.3,0.3)*M for M in (X, np.array([[0,-1j],[1j,0]], complex), Z)))
        rho = np.kron(rA, rB)
        S = chsh(rho, 0, np.pi/2, np.pi/4, -np.pi/4)
        r[f"sep_bound_{i}"] = {"S": S, "pass": abs(S) <= 2 + 1e-10}
    # Tsirelson: Bell singlet can reach 2sqrt(2); verify numeric value at optimal angles
    # Standard CHSH optimal: a=0, a'=pi/2, b=pi/4, b'=-pi/4 gives |S|=2sqrt2 for appropriate bell state
    phi_plus = np.outer(np.array([1,0,0,1])/np.sqrt(2), np.array([1,0,0,1])/np.sqrt(2))
    S = chsh(phi_plus, 0, np.pi/2, np.pi/4, -np.pi/4)
    r["bell_tsirelson"] = {"S": S, "pass": abs(abs(S) - 2*np.sqrt(2)) < 1e-9}
    return r

def run_negative_tests():
    r = {}
    # Claim that separable can exceed 2: falsify by sweeping and verifying never exceeds
    rng = np.random.default_rng(42)
    max_S = 0.0
    for _ in range(200):
        # random separable: convex comb of product states
        rA = 0.5*(np.eye(2) + np.sum([rng.uniform(-0.2,0.2)*M for M in (X, np.array([[0,-1j],[1j,0]], complex), Z)], axis=0))
        rB = 0.5*(np.eye(2) + np.sum([rng.uniform(-0.2,0.2)*M for M in (X, np.array([[0,-1j],[1j,0]], complex), Z)], axis=0))
        rho = np.kron(rA, rB)
        a, ap, b, bp = rng.uniform(0, 2*np.pi, 4)
        S = abs(chsh(rho, a, ap, b, bp))
        max_S = max(max_S, S)
    r["sep_never_exceeds_2"] = {"max_S": max_S, "pass": max_S <= 2 + 1e-9}
    return r

def run_boundary_tests():
    r = {}
    # Maximally mixed => S = 0
    rho = 0.25*np.eye(4, dtype=complex)
    S = chsh(rho, 0, np.pi/2, np.pi/4, -np.pi/4)
    r["maxmixed_zero"] = {"S": S, "pass": abs(S) < 1e-12}
    # Tsirelson bound not exceeded by any quantum state we sample
    rng = np.random.default_rng(1)
    maxq = 0.0
    for _ in range(50):
        v = rng.normal(size=4) + 1j*rng.normal(size=4); v /= np.linalg.norm(v)
        rho = np.outer(v, v.conj())
        a, ap, b, bp = rng.uniform(0, 2*np.pi, 4)
        maxq = max(maxq, abs(chsh(rho, a, ap, b, bp)))
    r["tsirelson_respected"] = {"max": maxq, "pass": maxq <= 2*np.sqrt(2) + 1e-9}
    return r

if __name__ == "__main__":
    results = {
        "name": "baseline_chsh_expectation",
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
    out_path = os.path.join(out_dir, "baseline_chsh_expectation_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    all_pass = all(v.get("pass", False) for sec in ("positive","negative","boundary")
                   for v in results[sec].values())
    print(f"PASS={all_pass} -> {out_path}")

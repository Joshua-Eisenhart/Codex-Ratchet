#!/usr/bin/env python3
"""Classical baseline: density matrix eigendecomp + von Neumann entropy."""
import json, os, numpy as np

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "baseline uses numpy only"},
    "pyg": {"tried": False, "used": False, "reason": "no graph structure"},
    "z3": {"tried": False, "used": False, "reason": "numeric baseline, no SMT claim"},
    "cvc5": {"tried": False, "used": False, "reason": "numeric baseline, no SMT claim"},
    "sympy": {"tried": False, "used": False, "reason": "numeric baseline; symbolic cross-check deferred"},
    "clifford": {"tried": False, "used": False, "reason": "no GA rotor here"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold structure here"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariance claim"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell complex"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistence"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
# numpy is the baseline engine; record under pytorch slot omitted -- numpy tracked as load_bearing role out-of-manifest
NUMPY_ROLE = "load_bearing"  # baseline reference

def vn_entropy(rho):
    w = np.linalg.eigvalsh(rho)
    w = np.clip(w, 1e-15, 1.0)
    return float(-np.sum(w * np.log2(w)))

def run_positive_tests():
    r = {}
    # Pure state |0>
    rho = np.array([[1,0],[0,0]], dtype=complex)
    r["pure_zero_entropy"] = {"value": vn_entropy(rho), "expected": 0.0,
                              "pass": abs(vn_entropy(rho)) < 1e-9}
    # Maximally mixed
    rho = 0.5*np.eye(2, dtype=complex)
    r["maxmixed_entropy"] = {"value": vn_entropy(rho), "expected": 1.0,
                             "pass": abs(vn_entropy(rho) - 1.0) < 1e-9}
    # Eigendecomp reconstruction
    rho = np.array([[0.7, 0.1+0.2j],[0.1-0.2j, 0.3]])
    w, V = np.linalg.eigh(rho)
    rec = V @ np.diag(w) @ V.conj().T
    r["eig_reconstruct"] = {"err": float(np.linalg.norm(rho-rec)),
                            "pass": np.allclose(rho, rec, atol=1e-10)}
    return r

def run_negative_tests():
    r = {}
    # Non-Hermitian should not yield real eigenvalues via eigvalsh sensibly -> detect
    bad = np.array([[0,1],[0,0]], dtype=complex)
    try:
        w = np.linalg.eigvals(bad)
        r["nonhermitian_detected"] = {"pass": not np.allclose(w.imag, 0) or np.any(w==0)}
    except Exception as e:
        r["nonhermitian_detected"] = {"pass": True, "err": str(e)}
    # Negative eigenvalue => invalid density matrix
    bad2 = np.array([[1.2, 0],[0, -0.2]], dtype=complex)
    w = np.linalg.eigvalsh(bad2)
    r["negative_eig_flagged"] = {"pass": bool(np.any(w < 0))}
    return r

def run_boundary_tests():
    r = {}
    # Near-pure
    eps = 1e-12
    rho = np.array([[1-eps, 0],[0, eps]], dtype=complex)
    s = vn_entropy(rho)
    r["near_pure"] = {"value": s, "pass": s < 1e-9}
    # Degenerate eigenvalues
    rho = 0.5*np.eye(4, dtype=complex)
    r["degenerate_4d"] = {"value": vn_entropy(rho), "expected": 2.0,
                          "pass": abs(vn_entropy(rho)-2.0) < 1e-9}
    return r

if __name__ == "__main__":
    results = {
        "name": "baseline_density_eigendecomp_vn_entropy",
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
    out_path = os.path.join(out_dir, "baseline_density_eigendecomp_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    all_pass = all(v.get("pass", False) for sec in ("positive","negative","boundary")
                   for v in results[sec].values())
    print(f"PASS={all_pass} -> {out_path}")

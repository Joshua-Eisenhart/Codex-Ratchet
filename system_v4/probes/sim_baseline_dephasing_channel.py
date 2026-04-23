#!/usr/bin/env python3
"""Classical baseline: dephasing channel forward evolution."""
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

def dephase(rho, p):
    # Phase-flip channel: (1-p) rho + p Z rho Z
    Z = np.array([[1,0],[0,-1]], dtype=complex)
    return (1-p)*rho + p*(Z @ rho @ Z)

def run_positive_tests():
    r = {}
    # |+> becomes diagonal as p->1/2 kills off-diagonals at p=1/2? phase-flip: off-diag * (1-2p)
    plus = 0.5*np.array([[1,1],[1,1]], dtype=complex)
    out = dephase(plus, 0.5)
    r["half_dephase_kills_coh"] = {"pass": abs(out[0,1]) < 1e-12}
    # p=0 identity
    out = dephase(plus, 0.0)
    r["p0_identity"] = {"pass": np.allclose(out, plus, atol=1e-12)}
    # Trace preserved
    rho = np.array([[0.7, 0.2],[0.2, 0.3]], dtype=complex)
    r["trace_preserved"] = {"pass": abs(np.trace(dephase(rho, 0.3)).real - 1) < 1e-12}
    # Diagonal invariant
    diag = np.diag([0.6, 0.4]).astype(complex)
    r["diag_invariant"] = {"pass": np.allclose(dephase(diag, 0.4), diag, atol=1e-12)}
    return r

def run_negative_tests():
    r = {}
    # p outside [0,1] => not CP; off-diag scaling |1-2p|>1
    plus = 0.5*np.array([[1,1],[1,1]], dtype=complex)
    out = dephase(plus, 1.5)
    r["invalid_p_detected"] = {"pass": abs(out[0,1]) > 0.5}
    # Wrong op (X instead of Z) should NOT preserve diagonal
    X = np.array([[0,1],[1,0]], dtype=complex)
    diag = np.diag([0.6,0.4]).astype(complex)
    wrong = 0.5*diag + 0.5*(X @ diag @ X)
    r["wrong_op_not_dephasing"] = {"pass": not np.allclose(wrong, diag, atol=1e-6)}
    return r

def run_boundary_tests():
    r = {}
    plus = 0.5*np.array([[1,1],[1,1]], dtype=complex)
    # p=1: full Z conjugation, off-diag sign flipped magnitude preserved
    out = dephase(plus, 1.0)
    r["p1_full"] = {"pass": abs(out[0,1] + 0.5) < 1e-12}
    # Monotone decay of |coherence|
    ps = np.linspace(0, 0.5, 11)
    coh = [abs(dephase(plus, p)[0,1]) for p in ps]
    r["monotone_decay"] = {"pass": all(coh[i] >= coh[i+1] - 1e-12 for i in range(len(coh)-1))}
    return r

if __name__ == "__main__":
    results = {
        "name": "baseline_dephasing_channel",
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
    out_path = os.path.join(out_dir, "baseline_dephasing_channel_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    all_pass = all(v.get("pass", False) for sec in ("positive","negative","boundary")
                   for v in results[sec].values())
    print(f"PASS={all_pass} -> {out_path}")

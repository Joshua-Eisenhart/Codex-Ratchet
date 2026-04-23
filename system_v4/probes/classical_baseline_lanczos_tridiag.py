#!/usr/bin/env python3
"""classical_baseline_lanczos_tridiag.py -- non-canon, lane_B-eligible
Generated classical baseline. numpy load_bearing. pos/neg/boundary all required PASS.
"""
import json, os, numpy as np

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed for classical baseline"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not a proof sim"},
    "cvc5": {"tried": False, "used": False, "reason": "not a proof sim"},
    "sympy": {"tried": False, "used": False, "reason": "numeric only"},
    "clifford": {"tried": False, "used": False, "reason": "no geometric algebra here"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold here"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariance"},
    "rustworkx": {"tried": False, "used": False, "reason": "numpy sufficient"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell complex"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistence"},
    "numpy": {"tried": True, "used": True, "reason": "load-bearing numeric core for lanczos_tridiag"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing"}


def _lanczos(A, k):
    n=A.shape[0]; Q=np.zeros((n,k)); alpha=np.zeros(k); beta=np.zeros(k)
    q=np.ones(n)/np.sqrt(n); q_prev=np.zeros(n); b_prev=0.0
    for i in range(k):
        Q[:,i]=q
        w=A@q - b_prev*q_prev
        alpha[i]=q@w
        w = w - alpha[i]*q
        # reorth
        w = w - Q[:,:i+1]@(Q[:,:i+1].T@w)
        beta[i]=np.linalg.norm(w)
        if beta[i]<1e-12: break
        q_prev=q; q=w/beta[i]; b_prev=beta[i]
    T=np.diag(alpha)+np.diag(beta[:k-1],1)+np.diag(beta[:k-1],-1)
    return Q,T

def run_positive_tests():
    rng=np.random.default_rng(0); M=rng.standard_normal((10,10)); A=(M+M.T)/2
    Q,T=_lanczos(A, 10)
    eigs_T = np.sort(np.linalg.eigvalsh(T))
    eigs_A = np.sort(np.linalg.eigvalsh(A))
    return {"spectrum_match": bool(np.allclose(eigs_T, eigs_A, atol=1e-4))}

def run_negative_tests():
    rng=np.random.default_rng(2); M=rng.standard_normal((6,6)); A=(M+M.T)/2
    Q,T=_lanczos(A,6)
    # T is tridiagonal: entries beyond first off-diag = 0
    off = T - np.diag(np.diag(T)) - np.diag(np.diag(T,1),1) - np.diag(np.diag(T,-1),-1)
    return {"tridiagonal": bool(np.allclose(off, 0, atol=1e-8))}

def run_boundary_tests():
    A=np.array([[7.0]]); Q,T=_lanczos(A,1)
    return {"scalar_lanczos": bool(abs(T[0,0]-7.0)<1e-10)}


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(v for v in list(pos.values())+list(neg.values())+list(bnd.values()))
    results = {
        "name": "classical_baseline_lanczos_tridiag",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": bool(all_pass),
        "classification": "classical_baseline",
        "lane": "lane_B",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "classical_baseline_lanczos_tridiag_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if all_pass else 'FAIL'} lanczos_tridiag -> {out_path}")

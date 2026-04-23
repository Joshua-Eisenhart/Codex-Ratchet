#!/usr/bin/env python3
"""classical_baseline_jacobi_eigen.py -- non-canon, lane_B-eligible
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
    "numpy": {"tried": True, "used": True, "reason": "load-bearing numeric core for jacobi_eigen"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing"}


def _jacobi(A, tol=1e-10, maxit=200):
    A=A.astype(float).copy(); n=A.shape[0]
    for _ in range(maxit):
        off = A - np.diag(np.diag(A))
        if np.max(np.abs(off))<tol: break
        # pick largest off-diagonal
        i,j=np.unravel_index(np.argmax(np.abs(off)), A.shape)
        if i==j: break
        if A[i,i]==A[j,j]:
            theta=np.pi/4
        else:
            theta=0.5*np.arctan(2*A[i,j]/(A[i,i]-A[j,j]))
        c,s=np.cos(theta), np.sin(theta)
        G=np.eye(n); G[i,i]=c; G[j,j]=c; G[i,j]=-s; G[j,i]=s
        A = G.T @ A @ G
    return np.sort(np.diag(A))

def run_positive_tests():
    rng=np.random.default_rng(0); M=rng.standard_normal((5,5)); A=(M+M.T)/2
    e_j=_jacobi(A); e_np=np.sort(np.linalg.eigvalsh(A))
    return {"match_numpy": bool(np.allclose(e_j, e_np, atol=1e-6))}

def run_negative_tests():
    A=np.diag([1.,2.,3.]); e=_jacobi(A)
    return {"diagonal_preserved": bool(np.allclose(e, [1,2,3]))}

def run_boundary_tests():
    A=np.array([[9.0]]); e=_jacobi(A)
    return {"scalar": bool(e[0]==9.0)}


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(v for v in list(pos.values())+list(neg.values())+list(bnd.values()))
    results = {
        "name": "classical_baseline_jacobi_eigen",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": bool(all_pass),
        "classification": "classical_baseline",
        "lane": "lane_B",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "classical_baseline_jacobi_eigen_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if all_pass else 'FAIL'} jacobi_eigen -> {out_path}")

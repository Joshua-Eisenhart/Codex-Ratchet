#!/usr/bin/env python3
"""sim_geomstats_stiefel_retraction: Stiefel V(n,k) retraction preserves column-orthonormality.

geomstats load-bearing: Stiefel exp/projection returns a point on the manifold
(Q^T Q = I_k) after tangent-space update; naive Euclidean X + V does not.
"""
import json, os, numpy as np

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

from geomstats.geometry.stiefel import Stiefel
TOOL_MANIFEST["geomstats"]["tried"] = True

N, K = 5, 3
ST = Stiefel(n=N, p=K)

def _rand_stiefel(rng):
    A = rng.normal(size=(N, K))
    Q, _ = np.linalg.qr(A)
    return Q

def run_positive_tests():
    rng = np.random.default_rng(6)
    max_err = 0.0
    for _ in range(10):
        X = _rand_stiefel(rng)
        # tangent vector: V such that X^T V + V^T X = 0
        A = rng.normal(size=(K, K)); A = A - A.T  # skew
        B = rng.normal(size=(N - K, K))
        # V = X*A + X_perp * B
        # build X_perp via QR on random complement
        M = rng.normal(size=(N, N))
        Q_full, _ = np.linalg.qr(np.hstack([X, M[:, :N-K]]))
        X_perp = Q_full[:, K:]
        V = X @ A + X_perp @ B
        V = 0.1 * V / max(np.linalg.norm(V), 1e-9)
        Y = ST.metric.exp(tangent_vec=V, base_point=X)
        err = float(np.linalg.norm(Y.T @ Y - np.eye(K)))
        max_err = max(max_err, err)
    return {"retraction_preserves_orthonormality": {"max_err": max_err, "pass": max_err < 1e-8}}

def run_negative_tests():
    # Naive Euclidean update breaks orthonormality.
    rng = np.random.default_rng(7)
    X = _rand_stiefel(rng); V = 0.3 * rng.normal(size=(N, K))
    Y_naive = X + V
    err = float(np.linalg.norm(Y_naive.T @ Y_naive - np.eye(K)))
    return {"euclidean_update_breaks_orthonormality": {"err": err, "pass": err > 0.05}}

def run_boundary_tests():
    # Zero tangent vector -> retraction is identity.
    rng = np.random.default_rng(8)
    X = _rand_stiefel(rng)
    V = np.zeros((N, K))
    Y = ST.metric.exp(tangent_vec=V, base_point=X)
    err = float(np.linalg.norm(Y - X))
    return {"zero_tangent_is_identity": {"err": err, "pass": err < 1e-8}}

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    TOOL_MANIFEST["geomstats"].update(used=True, reason="Stiefel exp retraction with horizontal/vertical split")
    TOOL_INTEGRATION_DEPTH["geomstats"] = "load_bearing"
    results = {"name":"sim_geomstats_stiefel_retraction","tool_manifest":TOOL_MANIFEST,
               "tool_integration_depth":TOOL_INTEGRATION_DEPTH,
               "positive":pos,"negative":neg,"boundary":bnd,"classification":"canonical"}
    out_dir = os.path.join(os.path.dirname(__file__),"a2_state","sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir,"sim_geomstats_stiefel_retraction_results.json")
    with open(out_path,"w") as f: json.dump(results, f, indent=2, default=str)
    all_pass = all(v.get("pass") for v in {**pos,**neg,**bnd}.values())
    print(f"PASS={all_pass} -> {out_path}")

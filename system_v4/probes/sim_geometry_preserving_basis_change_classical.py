#!/usr/bin/env python3
"""Classical baseline: geometry_preserving_basis_change.
Orthogonal/unitary basis changes preserve inner product, norms, eigenvalues.
Non-orthogonal changes break these. Tests both positive and negative cases."""
import json, os, numpy as np
classification = "classical_baseline"
divergence_log = "Classical baseline: geometry-preserving basis change is modeled here by orthogonal/unitary invariance numerics, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "basis-change invariance, norms, and eigenspectrum numerics"},
    "sympy": {"tried": False, "used": False, "reason": "not needed for this numeric baseline"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "sympy": None,
}
NAME = "geometry_preserving_basis_change"

def run_positive_tests():
    r = {}; rng = np.random.default_rng(0)
    for n in (3, 5, 7):
        A = rng.standard_normal((n, n)); H = (A + A.T) / 2
        Q, _ = np.linalg.qr(rng.standard_normal((n, n)))
        u = rng.standard_normal(n); v = rng.standard_normal(n)
        # inner product preserved
        ip0 = u @ v; ip1 = (Q @ u) @ (Q @ v)
        r[f"inner_product_n{n}"] = bool(abs(ip0 - ip1) < 1e-10)
        # norm preserved
        r[f"norm_n{n}"] = bool(abs(np.linalg.norm(u) - np.linalg.norm(Q @ u)) < 1e-10)
        # eigenvalues preserved
        w0 = np.sort(np.linalg.eigvalsh(H)); w1 = np.sort(np.linalg.eigvalsh(Q.T @ H @ Q))
        r[f"eigs_n{n}"] = bool(np.allclose(w0, w1, atol=1e-8))
        # determinant of Q = +-1
        r[f"det_unit_n{n}"] = bool(abs(abs(np.linalg.det(Q)) - 1.0) < 1e-10)
    return r

def run_negative_tests():
    r = {}; rng = np.random.default_rng(1)
    n = 4; M = rng.standard_normal((n, n)) * 2.0  # not orthogonal
    u = rng.standard_normal(n); v = rng.standard_normal(n)
    r["nonortho_breaks_ip"] = bool(abs((u @ v) - (M @ u) @ (M @ v)) > 1e-3)
    H = rng.standard_normal((n, n)); H = (H + H.T) / 2
    w0 = np.sort(np.linalg.eigvalsh(H))
    w1 = np.sort(np.linalg.eigvalsh(M @ H @ M.T))  # similarity only if M invertible & M.T=M^-1
    r["nonortho_breaks_eigs"] = bool(not np.allclose(w0, w1, atol=1e-3))
    return r

def run_boundary_tests():
    r = {}
    I = np.eye(4); u = np.arange(4.0)
    r["identity_preserves"] = bool(np.allclose(I @ u, u))
    # reflection preserves geometry but flips det
    R = np.diag([-1.0, 1, 1, 1])
    r["reflection_det_neg"] = bool(np.isclose(np.linalg.det(R), -1.0))
    r["reflection_preserves_norm"] = bool(abs(np.linalg.norm(R @ u) - np.linalg.norm(u)) < 1e-12)
    return r

if __name__ == "__main__":
    results = {"name": NAME, "classification": "classical_baseline",
               "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
               "positive": run_positive_tests(), "negative": run_negative_tests(),
               "boundary": run_boundary_tests(),
               "classical_captured": "O(n)/U(n) preservation of inner product, norms, spectrum",
               "innately_missing": "basis-change constraints imposed by coupling / probe-admissible frames"}
    results["all_pass"] = all(v for s in ("positive","negative","boundary") for v in results[s].values())
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results", f"{NAME}_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out,"w") as f: json.dump(results,f,indent=2,default=str)
    print(f"all_pass={results['all_pass']} -> {out}")

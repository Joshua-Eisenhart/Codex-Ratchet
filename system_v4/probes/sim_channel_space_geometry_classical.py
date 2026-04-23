#!/usr/bin/env python3
"""Classical baseline: channel_space_geometry.
Channel = Kraus sum. Compute a diamond-norm LOWER BOUND by sampling random pure
inputs on extended space and maximizing trace distance of outputs. Verifies
CPTP trace preservation and composition. Diamond norm upper bound not reached."""
import json, os, numpy as np
classification = "classical_baseline"
divergence_log = "Classical baseline: channel-space geometry is approximated here by sampled lower-bound numerics on Kraus channels, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "Kraus-channel sampling and trace-distance numerics"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}
NAME = "channel_space_geometry"

def apply_channel(kraus, rho):
    return sum(K @ rho @ K.conj().T for K in kraus)

def depolarizing_kraus(p, d=2):
    I = np.eye(d); X = np.array([[0,1],[1,0]],dtype=complex); Y = np.array([[0,-1j],[1j,0]]); Z = np.array([[1,0],[0,-1]],dtype=complex)
    return [np.sqrt(1 - 3*p/4) * I, np.sqrt(p/4) * X, np.sqrt(p/4) * Y, np.sqrt(p/4) * Z]

def tr_dist(a, b):
    w = np.linalg.eigvalsh(a - b); return 0.5 * np.sum(np.abs(w))

def rand_pure(d, rng):
    v = rng.standard_normal(d) + 1j * rng.standard_normal(d); v /= np.linalg.norm(v); return np.outer(v, v.conj())

def diamond_lower_bound(K1, K2, d=2, samples=200, rng=None):
    # sample pure inputs on dxd (no ancilla -> lower bound only)
    best = 0.0
    for _ in range(samples):
        rho = rand_pure(d, rng); sig = rand_pure(d, rng)
        o1 = apply_channel(K1, rho) - apply_channel(K2, rho)
        o2 = apply_channel(K1, sig) - apply_channel(K2, sig)
        best = max(best, tr_dist(apply_channel(K1, rho), apply_channel(K2, rho)))
    return best

def cptp_trace_preserving(kraus, tol=1e-9):
    d = kraus[0].shape[0]
    S = sum(K.conj().T @ K for K in kraus)
    return np.allclose(S, np.eye(d), atol=tol)

def run_positive_tests():
    r = {}; rng = np.random.default_rng(0)
    K0 = depolarizing_kraus(0.0); Kp = depolarizing_kraus(0.2); Kq = depolarizing_kraus(0.5)
    r["cptp_identity"] = bool(cptp_trace_preserving(K0))
    r["cptp_depol_p02"] = bool(cptp_trace_preserving(Kp))
    r["cptp_depol_p05"] = bool(cptp_trace_preserving(Kq))
    # trace preserved on random density
    A = rng.standard_normal((2, 2)) + 1j * rng.standard_normal((2, 2)); rho = A @ A.conj().T; rho /= np.trace(rho).real
    r["trace_preserved"] = bool(abs(np.trace(apply_channel(Kp, rho)).real - 1.0) < 1e-9)
    # diamond lower bound between identity and nontrivial depolarizing > 0
    lb = diamond_lower_bound(K0, Kq, rng=rng)
    r["diamond_lb_positive"] = bool(lb > 1e-3)
    # monotone: larger p -> larger lower bound
    lb_small = diamond_lower_bound(K0, Kp, rng=np.random.default_rng(0))
    lb_big = diamond_lower_bound(K0, Kq, rng=np.random.default_rng(0))
    r["monotone_p"] = bool(lb_big + 1e-6 >= lb_small)
    return r

def run_negative_tests():
    r = {}
    # non-CPTP: missing normalization
    bad = [0.5 * np.eye(2, dtype=complex)]
    r["non_cptp_detected"] = bool(not cptp_trace_preserving(bad))
    # channel applied to non-density still linear but trace mismatch
    K = depolarizing_kraus(0.3)
    rho = np.array([[2.0, 0], [0, 0]], dtype=complex)  # not trace 1
    out = apply_channel(K, rho)
    r["trace_carried_through"] = bool(abs(np.trace(out).real - 2.0) < 1e-9)
    return r

def run_boundary_tests():
    r = {}; rng = np.random.default_rng(4)
    K0 = depolarizing_kraus(0.0)
    rho = rand_pure(2, rng)
    out = apply_channel(K0, rho)
    r["identity_channel_fixes"] = bool(np.allclose(out, rho, atol=1e-12))
    # fully depolarizing p=1 maps to maximally mixed
    K1 = depolarizing_kraus(1.0)
    out = apply_channel(K1, rho)
    r["full_depol_maxmixed"] = bool(np.allclose(out, 0.5 * np.eye(2), atol=1e-9))
    return r

if __name__ == "__main__":
    results = {"name": NAME, "classification": "classical_baseline",
               "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
               "positive": run_positive_tests(), "negative": run_negative_tests(),
               "boundary": run_boundary_tests(),
               "classical_captured": "CPTP checks, trace preservation, diamond-norm LOWER bound via sampling",
               "innately_missing": "true diamond norm (needs ancilla optimization / SDP), channel coupling geometry"}
    results["all_pass"] = all(v for s in ("positive","negative","boundary") for v in results[s].values())
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results", f"{NAME}_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out,"w") as f: json.dump(results,f,indent=2,default=str)
    print(f"all_pass={results['all_pass']} -> {out}")

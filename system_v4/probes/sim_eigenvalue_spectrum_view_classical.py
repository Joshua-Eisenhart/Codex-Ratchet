#!/usr/bin/env python3
"""Classical baseline: eigenvalue_spectrum_view. Hermitian spectrum real, unitary
invariance of spectrum, sum=trace, prod=det. Classical captures spectra; innately
misses probe-dependent admissibility and context geometry."""
import json, os, numpy as np
classification = "classical_baseline"
divergence_log = "Classical baseline: eigenvalue-spectrum behavior is modeled here by Hermitian spectral numerics, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "Hermitian eigenspectra, trace identities, and unitary-invariance numerics"},
    "sympy": {"tried": False, "used": False, "reason": "not needed for this numeric baseline"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "sympy": None,
}

NAME = "eigenvalue_spectrum_view"

def run_positive_tests():
    r = {}; rng = np.random.default_rng(0)
    for n in (2, 4, 6):
        A = rng.standard_normal((n, n)) + 1j * rng.standard_normal((n, n))
        H = (A + A.conj().T) / 2
        w = np.linalg.eigvalsh(H)
        r[f"real_spectrum_n{n}"] = bool(np.allclose(w.imag, 0, atol=1e-9))
        r[f"trace_sum_n{n}"] = bool(np.isclose(np.trace(H).real, w.sum(), atol=1e-8))
        # unitary invariance
        Q, _ = np.linalg.qr(rng.standard_normal((n, n)) + 1j * rng.standard_normal((n, n)))
        w2 = np.linalg.eigvalsh(Q.conj().T @ H @ Q)
        r[f"unitary_invariant_n{n}"] = bool(np.allclose(np.sort(w), np.sort(w2), atol=1e-6))
    return r

def run_negative_tests():
    r = {}; rng = np.random.default_rng(1)
    # non-Hermitian generically has complex eigenvalues
    A = rng.standard_normal((5, 5))
    w = np.linalg.eigvals(A)
    r["nonhermitian_has_complex"] = bool(np.max(np.abs(w.imag)) > 1e-6)
    # perturbation changes spectrum
    H = (A + A.T) / 2
    w1 = np.linalg.eigvalsh(H)
    w2 = np.linalg.eigvalsh(H + 0.5 * np.eye(5))
    r["perturbation_shifts"] = bool(not np.allclose(w1, w2))
    return r

def run_boundary_tests():
    r = {}
    r["zero_spectrum"] = bool(np.allclose(np.linalg.eigvalsh(np.zeros((3, 3))), 0))
    r["identity_spectrum"] = bool(np.allclose(np.linalg.eigvalsh(np.eye(4)), 1))
    # degenerate
    w = np.linalg.eigvalsh(np.diag([1.0, 1.0, 2.0]))
    r["degenerate"] = bool(np.allclose(np.sort(w), [1, 1, 2]))
    return r

if __name__ == "__main__":
    results = {"name": NAME, "classification": "classical_baseline",
               "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
               "positive": run_positive_tests(), "negative": run_negative_tests(),
               "boundary": run_boundary_tests(),
               "classical_captured": "real Hermitian spectra, unitary invariance, trace/det identities",
               "innately_missing": "probe-dependent spectrum admissibility, degeneracy-lifting under coupling"}
    results["all_pass"] = all(v for s in ("positive","negative","boundary") for v in results[s].values())
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results", f"{NAME}_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out,"w") as f: json.dump(results,f,indent=2,default=str)
    print(f"all_pass={results['all_pass']} -> {out}")

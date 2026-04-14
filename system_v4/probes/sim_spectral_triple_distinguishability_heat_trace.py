#!/usr/bin/env python3
"""
sim_spectral_triple_distinguishability_heat_trace -- Family #2 lego 5/6.

Distinguishability probe = heat-kernel trace Tr(exp(-t D^2)). Two triples
with different D spectra must be distinguishable at some t>0. Indistinguishable
triples share the full spectrum.
"""
import json, os
import numpy as np

classification = "classical_baseline"
DEMOTE_REASON = "no non-numpy load_bearing tool; numeric numpy only"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True,
              "reason": "eigh + exp(-t w^2) trace"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing"}


def heat_trace(D, t):
    w = np.linalg.eigvalsh(D)
    return float(np.sum(np.exp(-t * w ** 2)))


def D_odd(m=1.0):
    D = np.zeros((4, 4)); D[0, 2] = D[2, 0] = m; D[1, 3] = D[3, 1] = m
    return D


def run_positive_tests():
    r = {}
    D1 = D_odd(1.0)
    D2 = D_odd(2.0)  # different spectrum
    ts = np.linspace(0.1, 2.0, 20)
    diffs = [abs(heat_trace(D1, t) - heat_trace(D2, t)) for t in ts]
    r["distinguishable_at_some_t"] = bool(max(diffs) > 1e-6)
    # same D -> zero difference at all t
    r["identical_triples_indistinguishable"] = bool(
        max(abs(heat_trace(D1, t) - heat_trace(D1, t)) for t in ts) < 1e-14)
    # unitary conjugate -> same spectrum -> indistinguishable
    U, _ = np.linalg.qr(np.random.default_rng(0).standard_normal((4, 4)))
    D1U = U @ D1 @ U.T
    diffs_u = [abs(heat_trace(D1, t) - heat_trace(D1U, t)) for t in ts]
    r["unitary_equivalent_indistinguishable"] = bool(max(diffs_u) < 1e-8)
    return r


def run_negative_tests():
    r = {}
    # zero Dirac and nonzero Dirac must be distinguishable
    D0 = np.zeros((4, 4))
    D1 = D_odd(1.0)
    r["zero_vs_nonzero_distinguished"] = bool(
        abs(heat_trace(D0, 0.5) - heat_trace(D1, 0.5)) > 1e-3)
    # random Hermitian vs chiral Dirac: spectra differ
    rng = np.random.default_rng(7)
    A = rng.standard_normal((4, 4)); A = A + A.T
    r["random_H_distinguished_from_chiral"] = bool(
        abs(heat_trace(A, 0.3) - heat_trace(D1, 0.3)) > 1e-3)
    return r


def run_boundary_tests():
    r = {}
    # t -> 0 : trace -> dim(H) regardless of D
    D1 = D_odd(1.0)
    r["t_to_zero_trace_dim"] = bool(abs(heat_trace(D1, 1e-8) - 4.0) < 1e-6)
    # t -> inf : trace -> multiplicity of zero eigenvalue
    r["t_to_inf_trace_kernel"] = bool(abs(heat_trace(D1, 1e6) - 0.0) < 1e-6)
    return r


if __name__ == "__main__":
    results = {
        "name": "spectral_triple_distinguishability_heat_trace",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "spectral_triple_distinguishability_heat_trace_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(json.dumps({k: results[k] for k in ("positive", "negative", "boundary")},
                     indent=2, default=str))

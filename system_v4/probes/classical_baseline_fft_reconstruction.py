#!/usr/bin/env python3
"""classical_baseline_fft_reconstruction.py -- non-canon, lane_B-eligible
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
    "numpy": {"tried": True, "used": True, "reason": "load-bearing numeric core for fft_reconstruction"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing"}


def run_positive_tests():
    rng = np.random.default_rng(0)
    x = rng.standard_normal(512)
    X = np.fft.fft(x); y = np.fft.ifft(X).real
    return {"roundtrip": bool(np.allclose(x, y, atol=1e-10))}

def run_negative_tests():
    # random spectrum should not reconstruct to original
    rng = np.random.default_rng(1)
    x = rng.standard_normal(128)
    Xbad = np.fft.fft(rng.standard_normal(128))
    ybad = np.fft.ifft(Xbad).real
    return {"wrong_spectrum_mismatch": bool(not np.allclose(x, ybad, atol=1e-3))}

def run_boundary_tests():
    x = np.zeros(64); X = np.fft.fft(x)
    return {"zero_signal_zero_spectrum": bool(np.allclose(X, 0))}


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(v for v in list(pos.values())+list(neg.values())+list(bnd.values()))
    results = {
        "name": "classical_baseline_fft_reconstruction",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": bool(all_pass),
        "classification": "classical_baseline",
        "lane": "lane_B",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "classical_baseline_fft_reconstruction_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if all_pass else 'FAIL'} fft_reconstruction -> {out_path}")

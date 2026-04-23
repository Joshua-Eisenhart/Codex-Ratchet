#!/usr/bin/env python3
"""
sim_numpy_deep_density_matrix_baseline.py

Deep numpy integration sim -- REFERENCE BASELINE ONLY.
Lego: density-matrix eigendecomposition (2-qubit rho). This sim's role
is as the ablation reference that the pytorch-autograd canonical sim is
compared against. numpy is load-bearing HERE for the baseline numeric
verdict, but the sim itself is classified as classical_baseline: its
output is the ground truth a canonical sim must MATCH, not exceed.

Classification: classical_baseline.
"""
import json, os
import numpy as np

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "deliberately excluded -- this is the numpy-only baseline"},
    "pyg": {"tried": False, "used": False, "reason": "no graph"},
    "z3": {"tried": False, "used": False, "reason": "numeric eigendecomp, not FOL"},
    "cvc5": {"tried": False, "used": False, "reason": "numeric eigendecomp, not FOL"},
    "sympy": {"tried": False, "used": False, "reason": "numeric, not symbolic"},
    "clifford": {"tried": False, "used": False, "reason": "standard complex matrix suffices"},
    "geomstats": {"tried": False, "used": False, "reason": "flat spectral problem"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariance"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell complex"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistent homology"},
    "numpy": {"tried": True, "used": True, "reason": "baseline eigendecomp reference that a torch-autograd canonical sim will be compared against"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["numpy"] = "load_bearing"  # load-bearing FOR THE BASELINE ROLE


def bell_rho():
    v = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2.0)
    return np.outer(v, v.conj())


def mixed_rho(p=0.3):
    """p|Phi+><Phi+| + (1-p) I/4."""
    return p * bell_rho() + (1.0 - p) * np.eye(4, dtype=complex) / 4.0


def positive_bell_spectrum():
    rho = bell_rho()
    w, V = np.linalg.eigh(rho)
    # Pure state: spectrum = [0,0,0,1]
    ok = (abs(w[-1] - 1.0) < 1e-10) and (abs(w[0]) < 1e-10) and (abs(w[1]) < 1e-10)
    purity = float(np.real(np.trace(rho @ rho)))
    return ok and abs(purity - 1.0) < 1e-10, {
        "spectrum": w.tolist(), "purity": purity,
    }


def positive_mixed_spectrum():
    p = 0.3
    rho = mixed_rho(p)
    w = np.linalg.eigvalsh(rho)
    # Expected: one eigenvalue p + (1-p)/4 = 0.475; three at (1-p)/4 = 0.175
    expected = sorted([(1 - p) / 4.0] * 3 + [p + (1 - p) / 4.0])
    ok = bool(np.allclose(np.sort(w), expected, atol=1e-10))
    return ok, {"spectrum": w.tolist(), "expected": expected}


def negative_nonhermitian_invalid_rho():
    """Construct a non-Hermitian matrix -- np.linalg.eigvalsh must fail
    to produce a valid probability spectrum (e.g. complex eigenvalues if
    we used eig, or misleading output if we forced eigh). We detect the
    violation by checking Hermiticity BEFORE decomposition."""
    M = np.array([[1, 1, 0, 0],
                  [0, 0, 0, 0],
                  [0, 0, 0, 0],
                  [0, 0, 0, 0]], dtype=complex)
    herm = np.allclose(M, M.conj().T)
    # Expect NOT hermitian -> we correctly reject as a density matrix.
    return (not herm), {"hermitian": herm}


def boundary_max_mixed_uniform_spectrum():
    rho = np.eye(4, dtype=complex) / 4.0
    w = np.linalg.eigvalsh(rho)
    ok = bool(np.allclose(w, 0.25, atol=1e-12))
    purity = float(np.real(np.trace(rho @ rho)))
    return ok and abs(purity - 0.25) < 1e-12, {"spectrum": w.tolist(), "purity": purity}


def run_positive_tests():
    ok1, i1 = positive_bell_spectrum()
    ok2, i2 = positive_mixed_spectrum()
    return {"bell_pure_spectrum": {"pass": ok1, **i1},
            "werner_mixed_spectrum": {"pass": ok2, **i2}}


def run_negative_tests():
    ok, info = negative_nonhermitian_invalid_rho()
    return {"nonhermitian_rejected": {"pass": ok, **info}}


def run_boundary_tests():
    ok, info = boundary_max_mixed_uniform_spectrum()
    return {"maximally_mixed_uniform": {"pass": ok, **info}}


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = (all(v["pass"] for v in pos.values())
                and all(v["pass"] for v in neg.values())
                and all(v["pass"] for v in bnd.values()))
    results = {
        "name": "sim_numpy_deep_density_matrix_baseline",
        "classification": "classical_baseline",
        "baseline_role": "reference ground truth for torch-autograd canonical sim; NOT canonical itself",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "overall_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_numpy_deep_density_matrix_baseline_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"PASS={all_pass} -> {out_path}")

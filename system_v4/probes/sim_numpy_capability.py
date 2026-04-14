#!/usr/bin/env python3
"""
sim_numpy_capability.py -- Tool-capability isolation sim for numpy.

numpy is the classical baseline substrate. Load-bearing for linear algebra,
einsum, eigendecomposition used by classical_baseline sims. This probes only
those primitives, not the full ratchet.
"""

classification = "canonical"

import json
import os

TOOL_MANIFEST = {
    "numpy":     {"tried": False, "used": False, "reason": "under test"},
    "pytorch":   {"tried": False, "used": False, "reason": "separate probe"},
    "pyg":       {"tried": False, "used": False, "reason": "not needed"},
    "z3":        {"tried": False, "used": False, "reason": "not needed"},
    "cvc5":      {"tried": False, "used": False, "reason": "not needed"},
    "sympy":     {"tried": False, "used": False, "reason": "not needed"},
    "clifford":  {"tried": False, "used": False, "reason": "not geometry-relevant"},
    "geomstats": {"tried": False, "used": False, "reason": "not geometry-relevant"},
    "e3nn":      {"tried": False, "used": False, "reason": "not geometry-relevant"},
    "rustworkx": {"tried": False, "used": False, "reason": "not graph-relevant"},
    "xgi":       {"tried": False, "used": False, "reason": "not graph-relevant"},
    "toponetx":  {"tried": False, "used": False, "reason": "not topology-relevant"},
    "gudhi":     {"tried": False, "used": False, "reason": "not topology-relevant"},
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None, "sympy": None,
    "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}

try:
    import numpy as np
    TOOL_MANIFEST["numpy"]["tried"] = True
    TOOL_MANIFEST["numpy"]["used"] = True
    TOOL_MANIFEST["numpy"]["reason"] = "capability under test -- linalg, einsum, eig"
    NP_OK = True
    NP_VERSION = np.__version__
except Exception as exc:
    NP_OK = False
    NP_VERSION = None
    TOOL_MANIFEST["numpy"]["reason"] = f"not installed: {exc}"


def run_positive_tests():
    r = {}
    if not NP_OK:
        r["numpy_available"] = {"pass": False, "detail": "numpy missing"}
        return r
    r["numpy_available"] = {"pass": True, "version": NP_VERSION}

    # matmul
    A = np.array([[1.0, 2.0], [3.0, 4.0]])
    B = np.eye(2)
    r["matmul_identity"] = {"pass": np.allclose(A @ B, A)}

    # einsum partial trace aiaj->ij on 4x4 reshape
    rho = np.eye(4) / 4
    reduced = np.einsum("aiaj->ij", rho.reshape(2, 2, 2, 2))
    r["einsum_partial_trace"] = {
        "pass": np.allclose(reduced, np.eye(2) / 2),
    }

    # eigendecomposition of hermitian: eigenvalues AND eigenvector orthonormality
    H = np.array([[2.0, 1.0], [1.0, 2.0]])
    w, V = np.linalg.eigh(H)
    orth_err = float(np.abs(V.T @ V - np.eye(2)).max())
    recon_err = float(np.abs(V @ np.diag(w) @ V.T - H).max())
    r["eigh_symmetric"] = {
        "pass": (np.allclose(sorted(w.tolist()), [1.0, 3.0])
                 and orth_err < 1e-10
                 and recon_err < 1e-10),
        "eigvals": w.tolist(),
        "orthonormality_err": orth_err,
        "reconstruction_err": recon_err,
    }

    # SVD reconstruction + singular-value non-negativity + U,V orthonormality
    M = np.random.RandomState(0).randn(4, 3)
    U, s, Vt = np.linalg.svd(M, full_matrices=False)
    u_err = float(np.abs(U.T @ U - np.eye(3)).max())
    v_err = float(np.abs(Vt @ Vt.T - np.eye(3)).max())
    r["svd_reconstruct"] = {
        "pass": (np.allclose(U @ np.diag(s) @ Vt, M, atol=1e-10)
                 and bool(np.all(s >= -1e-12))
                 and u_err < 1e-10
                 and v_err < 1e-10),
        "U_orth_err": u_err,
        "Vt_orth_err": v_err,
        "min_singular_value": float(s.min()),
    }

    # linalg.solve against a handbuilt system: [[2,1],[1,3]] x = [4, 5] -> [1.4, 1.2]
    A_sys = np.array([[2.0, 1.0], [1.0, 3.0]])
    b_sys = np.array([4.0, 5.0])
    x_sys = np.linalg.solve(A_sys, b_sys)
    residual = float(np.abs(A_sys @ x_sys - b_sys).max())
    r["linalg_solve"] = {
        "pass": residual < 1e-12 and np.allclose(x_sys, [1.4, 1.2]),
        "residual": residual,
        "solution": x_sys.tolist(),
    }
    return r


def run_negative_tests():
    r = {}
    if not NP_OK:
        return r

    raised = False
    err = None
    try:
        _ = np.zeros((3, 4)) @ np.zeros((5, 2))
    except Exception as exc:
        raised = True
        err = type(exc).__name__
    r["shape_mismatch_raises"] = {"pass": raised, "error_type": err}

    # Singular matrix inv must raise
    raised2 = False
    err2 = None
    try:
        _ = np.linalg.inv(np.zeros((2, 2)))
    except Exception as exc:
        raised2 = True
        err2 = type(exc).__name__
    r["singular_inverse_raises"] = {"pass": raised2, "error_type": err2}
    return r


def run_boundary_tests():
    r = {}
    if not NP_OK:
        return r

    e = np.zeros((0, 3))
    r["empty_array"] = {"pass": e.shape == (0, 3) and e.size == 0}

    x = np.ones(10_000)
    r["large_sum"] = {"pass": abs(float(x.sum()) - 10_000.0) < 1e-6}

    z = np.array([1 + 2j, 3 - 4j])
    r["complex_conj"] = {"pass": np.allclose(z.conj(), np.array([1 - 2j, 3 + 4j]))}
    return r


def _all_pass(section):
    return all(bool(v.get("pass", False)) for v in section.values())


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    summary = {
        "positive_all_pass": _all_pass(pos),
        "negative_all_pass": _all_pass(neg),
        "boundary_all_pass": _all_pass(bnd),
    }
    summary["all_pass"] = all(summary.values())

    results = {
        "name": "sim_numpy_capability",
        "purpose": "Tool-capability isolation probe for numpy -- primitives only.",
        "numpy_version": NP_VERSION,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "witness_file": "system_v4/probes/sim_cross_fep_x_igt.py",
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "numpy_capability_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"summary.all_pass = {summary['all_pass']}")

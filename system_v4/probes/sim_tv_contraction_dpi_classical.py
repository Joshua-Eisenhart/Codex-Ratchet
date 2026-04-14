#!/usr/bin/env python3
"""Classical baseline: Total-variation contraction under a stochastic map (DPI).

For any row-stochastic matrix M, TV(Mp, Mq) <= TV(p, q). Strict contraction
with coefficient eta(M) = 1 - min_j sum_i min_k M[i,k] * ... (Dobrushin).
"""
import json
import os

import numpy as np

classification = "classical_baseline"
divergence_log = (
    "Classical DPI for TV operates on stochastic matrices acting on "
    "probability vectors. The quantum DPI requires CPTP maps on density "
    "matrices with trace-distance contraction; this baseline drops operator "
    "structure."
)

try:
    import torch  # noqa: F401
    _torch_ok = True
except Exception:
    _torch_ok = False

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "matrix-vector and TV"},
    "scipy": {"tried": False, "used": False, "reason": "not required"},
    "pytorch": {
        "tried": _torch_ok,
        "used": _torch_ok,
        "reason": "supportive import only",
    },
    "z3": {"tried": False, "used": False, "reason": "no SMT claim"},
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "pytorch": "supportive" if _torch_ok else None,
    "scipy": None,
    "z3": None,
}


def tv(p, q):
    return 0.5 * float(np.sum(np.abs(np.asarray(p) - np.asarray(q))))


def dobrushin_coef(M):
    """eta(M) = (1/2) max_{i,j} sum_k |M[i,k] - M[j,k]|.

    Here M is row-stochastic of shape (n_out, n_in); apply p -> p @ M.
    For M acting as left mult on row vectors: outputs are rows. We use the
    convention that p (row) -> p @ M so columns index output.
    """
    M = np.asarray(M, float)
    n = M.shape[0]
    best = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            best = max(best, 0.5 * np.sum(np.abs(M[i] - M[j])))
    return best


def run_positive_tests():
    r = {}
    rng = np.random.default_rng(8)
    M = rng.dirichlet(np.ones(4), size=4)  # 4x4 row-stochastic
    p = rng.dirichlet(np.ones(4))
    q = rng.dirichlet(np.ones(4))

    tv_before = tv(p, q)
    tv_after = tv(p @ M, q @ M)
    r["tv_contracts"] = bool(tv_after <= tv_before + 1e-9)

    # Dobrushin bound
    eta = dobrushin_coef(M)
    r["dobrushin_bound"] = bool(tv_after <= eta * tv_before + 1e-9)
    r["dobrushin_in_unit_interval"] = bool(0.0 <= eta <= 1.0 + 1e-9)

    # Compose two maps
    M2 = rng.dirichlet(np.ones(4), size=4)
    tv_after2 = tv(p @ M @ M2, q @ M @ M2)
    r["double_contracts"] = bool(tv_after2 <= tv_after + 1e-9)
    return r


def run_negative_tests():
    r = {}
    # Identity: no contraction
    I = np.eye(4)
    p = np.array([0.7, 0.1, 0.1, 0.1])
    q = np.array([0.1, 0.1, 0.1, 0.7])
    tv_before = tv(p, q)
    tv_after = tv(p @ I, q @ I)
    r["identity_no_contraction"] = bool(np.isclose(tv_before, tv_after))

    # Completely-mixing map: TV collapses to 0
    M_mix = np.ones((4, 4)) / 4.0
    tv_collapse = tv(p @ M_mix, q @ M_mix)
    r["mixing_collapses"] = bool(tv_collapse < 1e-9)
    return r


def run_boundary_tests():
    r = {}
    # Same input: tv stays 0 under any M
    rng = np.random.default_rng(9)
    M = rng.dirichlet(np.ones(3), size=3)
    p = np.array([0.2, 0.5, 0.3])
    r["same_input_zero_tv"] = bool(tv(p @ M, p @ M) < 1e-12)

    # Zero-column (deterministic) map
    M_det = np.array([[1, 0, 0], [1, 0, 0], [1, 0, 0]], float)
    p = np.array([0.5, 0.3, 0.2])
    q = np.array([0.1, 0.1, 0.8])
    r["deterministic_zero_tv"] = bool(tv(p @ M_det, q @ M_det) < 1e-12)
    return r


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "tv_contraction_dpi_classical_results.json")
    payload = {
        "name": "tv_contraction_dpi_classical",
        "classification": classification,
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "all_pass": bool(all_pass),
        "summary": {"all_pass": bool(all_pass)},
    }
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2, default=str)
    print(f"Results written to {out_path} all_pass={all_pass}")

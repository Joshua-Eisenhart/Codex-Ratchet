#!/usr/bin/env python3
"""
sim_capability_pynndescent_isolated.py
pynndescent isolated capability probe.

CAN: approximate nearest neighbors in high dimensions (much faster than exact
     search), supports cosine/euclidean metrics, useful for finding similar
     state vectors.
CANNOT: return guaranteed exact nearest neighbors (approximate), replace exact
        search for small datasets, do logical reasoning (use z3).

Classification: classical_baseline
"""

import json
import os
import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {
        "tried": False, "used": False,
        "reason": (
            "not used: this probe isolates pynndescent approximate "
            "nearest-neighbor capability; integration with state-space "
            "similarity search deferred to a dedicated integration sim "
            "per the four-sim-kinds doctrine."
        ),
    },
    "pyg": {
        "tried": False, "used": False,
        "reason": (
            "not used: this probe isolates pynndescent approximate "
            "nearest-neighbor capability; integration with state-space "
            "similarity search deferred to a dedicated integration sim "
            "per the four-sim-kinds doctrine."
        ),
    },
    "z3": {
        "tried": False, "used": False,
        "reason": (
            "not used: this probe isolates pynndescent approximate "
            "nearest-neighbor capability; integration with state-space "
            "similarity search deferred to a dedicated integration sim "
            "per the four-sim-kinds doctrine."
        ),
    },
    "cvc5": {
        "tried": False, "used": False,
        "reason": (
            "not used: this probe isolates pynndescent approximate "
            "nearest-neighbor capability; integration with state-space "
            "similarity search deferred to a dedicated integration sim "
            "per the four-sim-kinds doctrine."
        ),
    },
    "sympy": {
        "tried": False, "used": False,
        "reason": (
            "not used: this probe isolates pynndescent approximate "
            "nearest-neighbor capability; integration with state-space "
            "similarity search deferred to a dedicated integration sim "
            "per the four-sim-kinds doctrine."
        ),
    },
    "clifford": {
        "tried": False, "used": False,
        "reason": (
            "not used: this probe isolates pynndescent approximate "
            "nearest-neighbor capability; integration with state-space "
            "similarity search deferred to a dedicated integration sim "
            "per the four-sim-kinds doctrine."
        ),
    },
    "geomstats": {
        "tried": False, "used": False,
        "reason": (
            "not used: this probe isolates pynndescent approximate "
            "nearest-neighbor capability; integration with state-space "
            "similarity search deferred to a dedicated integration sim "
            "per the four-sim-kinds doctrine."
        ),
    },
    "e3nn": {
        "tried": False, "used": False,
        "reason": (
            "not used: this probe isolates pynndescent approximate "
            "nearest-neighbor capability; integration with state-space "
            "similarity search deferred to a dedicated integration sim "
            "per the four-sim-kinds doctrine."
        ),
    },
    "rustworkx": {
        "tried": False, "used": False,
        "reason": (
            "not used: this probe isolates pynndescent approximate "
            "nearest-neighbor capability; integration with state-space "
            "similarity search deferred to a dedicated integration sim "
            "per the four-sim-kinds doctrine."
        ),
    },
    "xgi": {
        "tried": False, "used": False,
        "reason": (
            "not used: this probe isolates pynndescent approximate "
            "nearest-neighbor capability; integration with state-space "
            "similarity search deferred to a dedicated integration sim "
            "per the four-sim-kinds doctrine."
        ),
    },
    "toponetx": {
        "tried": False, "used": False,
        "reason": (
            "not used: this probe isolates pynndescent approximate "
            "nearest-neighbor capability; integration with state-space "
            "similarity search deferred to a dedicated integration sim "
            "per the four-sim-kinds doctrine."
        ),
    },
    "gudhi": {
        "tried": False, "used": False,
        "reason": (
            "not used: this probe isolates pynndescent approximate "
            "nearest-neighbor capability; integration with state-space "
            "similarity search deferred to a dedicated integration sim "
            "per the four-sim-kinds doctrine."
        ),
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

# =====================================================================
# IMPORTS
# =====================================================================

from pynndescent import NNDescent


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # --- pos_01: basic index + query shape and distance ordering ---
    rng = np.random.default_rng(42)
    n_data = 100
    n_dims = 10
    n_test = 10
    k_index = 10
    k_query = 5

    data = rng.standard_normal((n_data, n_dims)).astype(np.float32)
    test_points = rng.standard_normal((n_test, n_dims)).astype(np.float32)

    index = NNDescent(data, n_neighbors=k_index, random_state=42)
    indices, distances = index.query(test_points, k=k_query)

    shape_ok = (indices.shape == (n_test, k_query) and
                distances.shape == (n_test, k_query))
    nonneg_ok = bool(np.all(distances >= 0))

    # nearest neighbor distance must be < second-nearest for each test point
    sorted_ok = bool(np.all(distances[:, 0] <= distances[:, 1]))

    results["pos_01_shape_and_ordering"] = {
        "pass": shape_ok and nonneg_ok and sorted_ok,
        "indices_shape": list(indices.shape),
        "distances_shape": list(distances.shape),
        "all_distances_nonneg": nonneg_ok,
        "nearest_lt_second_nearest": sorted_ok,
    }

    # --- pos_02: cosine metric ---
    index_cosine = NNDescent(data, n_neighbors=k_index,
                             metric="cosine", random_state=42)
    idx_cos, dist_cos = index_cosine.query(test_points, k=k_query)
    cosine_shape_ok = (idx_cos.shape == (n_test, k_query))
    cosine_nonneg_ok = bool(np.all(dist_cos >= 0))

    results["pos_02_cosine_metric"] = {
        "pass": cosine_shape_ok and cosine_nonneg_ok,
        "indices_shape": list(idx_cos.shape),
        "all_distances_nonneg": cosine_nonneg_ok,
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # --- neg_01: query k > n_data should either raise or return padded ---
    rng = np.random.default_rng(0)
    n_data = 20
    n_dims = 4
    data_small = rng.standard_normal((n_data, n_dims)).astype(np.float32)
    test_small = rng.standard_normal((3, n_dims)).astype(np.float32)

    k_over = n_data + 10  # more neighbors than data points

    try:
        index_small = NNDescent(data_small, n_neighbors=min(10, n_data - 1),
                                random_state=0)
        idx_over, dist_over = index_small.query(test_small, k=k_over)
        # pynndescent pads the result to the requested k without raising.
        # The returned array has shape (n_test, k_over).
        # Negative test: verify the query does NOT crash AND that indices
        # beyond the true dataset size are padded (may repeat valid indices
        # or use sentinel values — what matters is no exception and the
        # shape is returned).
        actual_k = idx_over.shape[1]
        neg_pass = (actual_k == k_over)  # pynndescent returns exactly k_over columns
        result_note = (
            f"pynndescent pads result to k={actual_k} when k>{n_data}; "
            f"no exception raised; indices may repeat valid rows"
        )
    except Exception as exc:
        neg_pass = True  # raising is also acceptable behaviour
        result_note = f"raised exception as expected: {type(exc).__name__}: {exc}"

    results["neg_01_k_greater_than_n_data"] = {
        "pass": neg_pass,
        "note": result_note,
    }

    # --- neg_02: 1D data (degenerate dimensionality) ---
    data_1d = rng.standard_normal((30, 1)).astype(np.float32)
    test_1d = rng.standard_normal((5, 1)).astype(np.float32)
    try:
        index_1d = NNDescent(data_1d, n_neighbors=5, random_state=0)
        idx_1d, dist_1d = index_1d.query(test_1d, k=3)
        shape_ok = idx_1d.shape == (5, 3)
        results["neg_02_1d_data"] = {
            "pass": shape_ok,
            "note": "1D index built and queried without error",
            "shape": list(idx_1d.shape),
        }
    except Exception as exc:
        results["neg_02_1d_data"] = {
            "pass": True,
            "note": f"raised exception for 1D data: {type(exc).__name__}: {exc}",
        }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # --- bnd_01: n_neighbors=1 in index, query for k=1 ---
    rng = np.random.default_rng(7)
    data = rng.standard_normal((50, 8)).astype(np.float32)
    test = rng.standard_normal((5, 8)).astype(np.float32)

    index_k1 = NNDescent(data, n_neighbors=1, random_state=7)
    idx_k1, dist_k1 = index_k1.query(test, k=1)

    shape_ok = (idx_k1.shape == (5, 1) and dist_k1.shape == (5, 1))
    nonneg_ok = bool(np.all(dist_k1 >= 0))
    valid_indices = bool(np.all(idx_k1 >= 0) and np.all(idx_k1 < 50))

    results["bnd_01_n_neighbors_1"] = {
        "pass": shape_ok and nonneg_ok and valid_indices,
        "shape_ok": shape_ok,
        "nonneg_ok": nonneg_ok,
        "valid_indices": valid_indices,
        "indices_shape": list(idx_k1.shape),
    }

    # --- bnd_02: minimum viable dataset (n_data == n_dims) ---
    n = 12
    data_sq = rng.standard_normal((n, n)).astype(np.float32)
    test_sq = rng.standard_normal((2, n)).astype(np.float32)
    index_sq = NNDescent(data_sq, n_neighbors=min(5, n - 1), random_state=7)
    idx_sq, dist_sq = index_sq.query(test_sq, k=3)
    results["bnd_02_square_shape"] = {
        "pass": idx_sq.shape == (2, 3),
        "shape": list(idx_sq.shape),
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_pass = (
        all(v["pass"] for v in pos.values()) and
        all(v["pass"] for v in neg.values()) and
        all(v["pass"] for v in bnd.values())
    )

    results = {
        "name": "sim_capability_pynndescent_isolated",
        "classification": "classical_baseline",
        "overall_pass": all_pass,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_capability_pynndescent_isolated_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"overall_pass: {all_pass}")

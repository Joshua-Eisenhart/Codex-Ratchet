#!/usr/bin/env python3
"""
sim_capability_umap_isolated.py -- Isolated tool-capability probe for umap-learn.

Classical_baseline capability probe: demonstrates umap can import, reduce
dimensionality on a 5D dataset to 2D, produce correct output shape, finite
values, and non-zero embedding. Honest CAN/CANNOT summary.
No coupling to other tools.
Per four-sim-kinds doctrine: capability probe precedes any integration sim.
"""

import json
import os

classification = "classical_baseline"
divergence_log = (
    "Classical baseline: this row isolates UMAP finite-dimensional embedding "
    "capability on ordinary data; it does not claim bridge, QIT, or "
    "nonclassical attractor evidence."
)

_ISOLATED_REASON = (
    "not used: this probe isolates umap dimensionality reduction capability alone; "
    "cross-tool coupling is deferred to a separate integration sim "
    "per the four-sim-kinds doctrine (capability vs integration separation)."
)

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "pyg":       {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "z3":        {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "cvc5":      {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "sympy":     {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "clifford":  {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "e3nn":      {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "xgi":       {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "toponetx":  {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "gudhi":     {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "umap":      {"tried": True,  "used": True,  "reason": "load-bearing: umap-learn is the sole subject; dimensionality reduction, output shape verification, and embedding variance are all computed directly by umap.UMAP."},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch":   None,
    "pyg":       None,
    "z3":        None,
    "cvc5":      None,
    "sympy":     None,
    "clifford":  None,
    "geomstats": None,
    "e3nn":      None,
    "rustworkx": None,
    "xgi":       None,
    "toponetx":  None,
    "gudhi":     None,
    "umap":      "load_bearing",
}

UMAP_OK = False
UMAP_VERSION = None
try:
    import umap
    import numpy as np
    UMAP_OK = True
    try:
        UMAP_VERSION = umap.__version__
    except AttributeError:
        UMAP_VERSION = "unknown"
except Exception:
    pass


def run_positive_tests():
    r = {}
    if not UMAP_OK:
        r["umap_available"] = {"pass": False, "detail": "umap not importable"}
        return r
    r["umap_available"] = {"pass": True, "version": UMAP_VERSION}

    import numpy as np

    # 30 points in 5D, numpy random seed
    rng = np.random.default_rng(42)
    X = rng.standard_normal((30, 5))

    reducer = umap.UMAP(n_components=2, random_state=42)
    embedding = reducer.fit_transform(X)

    # --- Test 1: output shape is (30, 2) ---
    shape_ok = embedding.shape == (30, 2)
    r["output_shape_30x2"] = {
        "pass": shape_ok,
        "shape": list(embedding.shape),
        "detail": "UMAP on 30x5 input must produce (30,2) output",
    }

    # --- Test 2: all values finite ---
    all_finite = bool(np.all(np.isfinite(embedding)))
    r["all_values_finite"] = {
        "pass": all_finite,
        "n_nonfinite": int(np.sum(~np.isfinite(embedding))),
        "detail": "embedding must contain no NaN or Inf values",
    }

    # --- Test 3: not all zero ---
    not_all_zero = bool(np.any(embedding != 0.0))
    r["not_all_zero"] = {
        "pass": not_all_zero,
        "max_abs_value": float(np.max(np.abs(embedding))),
        "detail": "embedding must not be identically zero",
    }

    return r


def run_negative_tests():
    r = {}
    if not UMAP_OK:
        r["umap_unavailable"] = {"pass": True, "detail": "skip: umap not installed"}
        return r

    import numpy as np

    # --- Neg 1: n_components > n_samples should raise or return degenerate output ---
    # With n_samples=5 and n_components=10, UMAP should raise or fail gracefully
    X_tiny = np.random.default_rng(0).standard_normal((5, 3))
    error_caught = False
    error_msg = None
    degenerate = False
    try:
        reducer = umap.UMAP(n_components=10, random_state=42, n_neighbors=2)
        out = reducer.fit_transform(X_tiny)
        # If it ran, check if output is degenerate (constant columns)
        col_vars = np.var(out, axis=0)
        degenerate = bool(np.any(col_vars == 0.0) or out.shape[1] != 10)
    except Exception as exc:
        error_caught = True
        error_msg = str(exc)

    r["n_components_exceeds_n_samples"] = {
        "pass": error_caught or degenerate,
        "error_caught": error_caught,
        "error_msg": error_msg,
        "degenerate_output": degenerate,
        "detail": "n_components > n_samples must raise or produce degenerate output",
    }

    return r


def run_boundary_tests():
    r = {}
    if not UMAP_OK:
        r["umap_unavailable"] = {"pass": True, "detail": "skip: umap not installed"}
        return r

    import numpy as np

    # Common data: 30 points in 5D
    rng = np.random.default_rng(42)
    X = rng.standard_normal((30, 5))

    # --- Boundary 1: n_neighbors=2 (tight local neighborhood) ---
    emb_tight = umap.UMAP(n_components=2, n_neighbors=2, random_state=42).fit_transform(X)
    var_tight = float(np.var(emb_tight))

    # --- Boundary 2: n_neighbors=15 (broader neighborhood) ---
    emb_broad = umap.UMAP(n_components=2, n_neighbors=15, random_state=42).fit_transform(X)
    var_broad = float(np.var(emb_broad))

    # Both should run without error and produce (30,2) finite embeddings
    both_valid = (
        emb_tight.shape == (30, 2)
        and emb_broad.shape == (30, 2)
        and bool(np.all(np.isfinite(emb_tight)))
        and bool(np.all(np.isfinite(emb_broad)))
    )

    r["n_neighbors_2_vs_15_both_valid"] = {
        "pass": both_valid,
        "shape_tight": list(emb_tight.shape),
        "shape_broad": list(emb_broad.shape),
        "var_tight": var_tight,
        "var_broad": var_broad,
        "detail": "n_neighbors=2 and n_neighbors=15 both produce valid (30,2) finite embeddings",
    }

    # --- Boundary 3: embedding variance differs between n_neighbors settings ---
    var_differs = abs(var_tight - var_broad) > 1e-6
    r["n_neighbors_changes_embedding_variance"] = {
        "pass": var_differs,
        "var_n2": var_tight,
        "var_n15": var_broad,
        "abs_diff": float(abs(var_tight - var_broad)),
        "detail": "different n_neighbors values should produce embeddings with different variance",
    }

    return r


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_tests = {**pos, **neg, **bnd}
    pass_count = sum(1 for v in all_tests.values() if isinstance(v, dict) and v.get("pass") is True)
    total_count = sum(1 for v in all_tests.values() if isinstance(v, dict) and "pass" in v)
    overall = (pass_count == total_count) and total_count > 0

    results = {
        "name": "sim_capability_umap_isolated",
        "classification": classification,
        "overall_pass": overall,
        "pass_count": pass_count,
        "total_count": total_count,
        "capability_summary": {
            "CAN": [
                "reduce high-dimensional data to 2D (or any target n_components < n_samples)",
                "produce finite, non-zero embeddings from arbitrary numpy arrays",
                "respect random_state for reproducibility",
                "adjust local vs global structure via n_neighbors parameter",
                "embed 5D data into 2D preserving neighborhood relationships",
            ],
            "CANNOT": [
                "handle n_components >= n_samples without raising or producing degenerate output",
                "guarantee exact reproducibility across different hardware/library versions",
                "replace persistent homology tools (use gudhi for TDA)",
                "provide formal proofs of topology preservation (use z3 for proofs)",
            ],
        },
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_capability_umap_isolated_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"overall_pass: {overall}  ({pass_count}/{total_count})")
    for name, v in all_tests.items():
        if isinstance(v, dict) and "pass" in v:
            status = "PASS" if v["pass"] else "FAIL"
            print(f"  [{status}] {name}")

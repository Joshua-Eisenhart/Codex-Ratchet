#!/usr/bin/env python3
"""
sim_gudhi_capability.py -- Tool-capability isolation sim for GUDHI.

Purpose: Bounded probe of GUDHI's persistent-homology capability envelope before
trusting it as load_bearing in larger nonclassical sims. Governed by
~/wiki/concepts/tool-capability-sim-program.md.

Witness load-bearing use cases in this repo:
  - sim_gudhi_concurrence_filtration.py
  - sim_hopf_torus_lego.py
  - sim_persistence_geometry.py
These sims treat GUDHI persistence as decisive structure -- this probe provides
the missing isolation test unblocking that use.
"""

classification = "canonical"

import json
import math
import os

import numpy as np

from receipt_boundary import apply_default_receipt_boundary

# =====================================================================
# TOOL MANIFEST
# =====================================================================

_NOT_USED_REASON = (
    "not used: this bounded GUDHI capability receipt isolates persistent-homology "
    "APIs on fixed point-cloud and SimplexTree controls; other tool families require separate receipts."
)

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "pyg":       {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "z3":        {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "cvc5":      {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "sympy":     {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "clifford":  {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "e3nn":      {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "xgi":       {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "toponetx":  {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "gudhi":     {"tried": False, "used": False, "reason": ""},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None, "sympy": None,
    "clifford": None, "geomstats": None, "e3nn": None, "rustworkx": None,
    "xgi": None, "toponetx": None,
    "gudhi": "load_bearing",  # GUDHI is the object under test
}

CANDIDATE_SIM_SPEC = {
    "operation_sequence": [
        "construct a finite jittered circle point cloud and build a GUDHI Rips complex",
        "compute persistence and count persistent H0/H1 features from the Rips diagram",
        "build a GUDHI AlphaComplex on the same point cloud and compare H0/H1 counts",
        "extract H1 barcode intervals and query persistent Betti numbers at a midpoint filtration",
        "compare GUDHI H0 alive-at-epsilon against a numpy connected-components baseline",
        "run random-noise, empty-cloud, single-point, and duplicate-point controls",
    ],
    "carrier_topology": (
        "finite point-cloud and SimplexTree persistent-homology fixture; no "
        "topology lego promotion, manifold admission, bridge, axis, GStack, "
        "QIT engine, or nonclassical claim"
    ),
    "observable": (
        "persistent H0/H1 counts, H1 barcode interval count and lifetime, "
        "persistent Betti vector at a declared filtration, numpy connected "
        "component agreement, and degenerate input behavior"
    ),
    "pass_fail_predicate": (
        "pass iff circle Rips and Alpha complexes expose one persistent H0 and "
        "one persistent H1 feature, barcode and Betti APIs agree at the probe "
        "filtration, numpy and GUDHI H0 counts match on separated clusters, "
        "noise has no robust H1, and degenerate boundaries behave as declared"
    ),
    "graveyards": [
        "random noise cloud must not expose a robust H1 feature at the declared threshold",
        "empty point cloud must not fabricate persistence features",
        "single point must document GUDHI's empty-diagram capability limit",
        "duplicate points must collapse to one connected component",
        "numpy connected-components baseline must agree with GUDHI H0 alive-at-epsilon",
    ],
    "baselines": [
        "numpy connected-components count on an epsilon graph",
        "AlphaComplex on the same circle cloud as an alternate GUDHI construction",
        "random Gaussian point cloud as a no-robust-cycle counterfactual",
        "empty, singleton, and duplicate-point degenerate controls",
    ],
    "alternative_formulations": [
        "manual SimplexTree insertion for a declared filtered complex",
        "Rips filtration over a square or annulus fixture",
        "persistence diagram stability sweep under small point-cloud perturbations",
    ],
    "tool_function_needs": [
        "gudhi.RipsComplex(points, max_edge_length).create_simplex_tree",
        "gudhi.AlphaComplex(points).create_simplex_tree",
        "SimplexTree.persistence",
        "SimplexTree.persistence_intervals_in_dimension",
        "SimplexTree.persistent_betti_numbers",
        "SimplexTree.insert and num_vertices for degenerate controls",
    ],
    "lego_coupling_target": (
        "bounded GUDHI persistent-homology capability evidence before exact "
        "topology lego-fit or coupling packets"
    ),
    "claim_ceiling": (
        "finite sim_gudhi_capability tool-capability receipt only; no bridge, "
        "GStack, axis, QIT, or nonclassical admission"
    ),
}

try:
    import gudhi  # noqa
    TOOL_MANIFEST["gudhi"]["tried"] = True
    TOOL_MANIFEST["gudhi"]["used"] = True
    TOOL_MANIFEST["gudhi"]["reason"] = (
        "load-bearing capability under test: GUDHI RipsComplex, AlphaComplex, "
        "SimplexTree persistence, intervals, and persistent Betti APIs decide the receipt verdicts."
    )
    GUDHI_OK = True
except ImportError as e:
    TOOL_MANIFEST["gudhi"]["reason"] = f"not installed: {e}"
    GUDHI_OK = False


# ---------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------

def _circle_points(n=24, r=1.0, seed=0):
    rng = np.random.default_rng(seed)
    theta = np.linspace(0, 2 * math.pi, n, endpoint=False)
    jitter = rng.normal(0, 0.01, size=(n, 2))
    return np.stack([r * np.cos(theta), r * np.sin(theta)], axis=1) + jitter


def _betti_from_diag(diag, persistence_min=0.05):
    """Count ESSENTIAL (infinite-lifetime) + long-lived features per dim.
    For a noise-free connected shape, essential H0=1 (one component surviving
    to inf); H1 features have finite death but long life."""
    b0 = b1 = 0
    for dim, (b, d) in diag:
        infinite = (d == float("inf"))
        life = float("inf") if infinite else (d - b)
        if dim == 0:
            # Only essential class counts as a persistent component
            if infinite:
                b0 += 1
        elif dim == 1:
            if infinite or life >= persistence_min:
                b1 += 1
    return b0, b1


def _cc_count_numpy(points, eps):
    """Simple connected-components count on eps-graph via union-find."""
    n = len(points)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for i in range(n):
        for j in range(i + 1, n):
            if np.linalg.norm(points[i] - points[j]) <= eps:
                union(i, j)
    return len({find(i) for i in range(n)})


# ---------------------------------------------------------------------
# POSITIVE TESTS
# ---------------------------------------------------------------------

def run_positive_tests():
    results = {}
    if not GUDHI_OK:
        return {"skipped": "gudhi not importable"}

    pts = _circle_points(n=24, r=1.0, seed=0)

    # --- 1. Rips complex + persistence on circle ---
    rips = gudhi.RipsComplex(points=pts, max_edge_length=2.5)
    st = rips.create_simplex_tree(max_dimension=2)
    diag_rips = st.persistence()
    b0_r, b1_r = _betti_from_diag(diag_rips, persistence_min=0.1)
    results["rips_circle_homology"] = {
        "b0": b0_r, "b1": b1_r,
        "expected_b0": 1, "expected_b1": 1,
        "pass": b0_r == 1 and b1_r == 1,
        "n_features": len(diag_rips),
    }

    # --- 2. Alpha complex matches Rips on same data ---
    alpha = gudhi.AlphaComplex(points=pts.tolist())
    st_a = alpha.create_simplex_tree()
    diag_alpha = st_a.persistence()
    b0_a, b1_a = _betti_from_diag(diag_alpha, persistence_min=0.01)
    results["alpha_matches_rips"] = {
        "alpha_b0": b0_a, "alpha_b1": b1_a,
        "rips_b0": b0_r, "rips_b1": b1_r,
        "pass": (b0_a == b0_r and b1_a == b1_r),
    }

    # --- 3. Persistence diagram / barcode extraction ---
    intervals_h1 = st.persistence_intervals_in_dimension(1)
    longest = None
    if len(intervals_h1) > 0:
        lifetimes = [(d if np.isfinite(d) else 10.0) - b for b, d in intervals_h1]
        longest = float(max(lifetimes))
    results["barcode_extraction"] = {
        "h1_intervals": len(intervals_h1),
        "longest_h1_lifetime": longest,
        "pass": longest is not None and longest > 0.3,  # circle feature should be prominent
    }

    # --- 4. Persistent Betti numbers at a filtration slice through the H1 feature ---
    # Find the longest H1 interval and probe at its midpoint
    h1 = st.persistence_intervals_in_dimension(1)
    if len(h1) > 0:
        b_, d_ = max(h1, key=lambda bd: (bd[1] if np.isfinite(bd[1]) else 1e9) - bd[0])
        mid = 0.5 * (b_ + (d_ if np.isfinite(d_) else b_ + 1.0))
        pb = st.persistent_betti_numbers(mid, mid)
        results["betti_api"] = {
            "persistent_betti_at_mid": list(pb),
            "probe_filtration": float(mid),
            "expected": [1, 1],
            "pass": len(pb) >= 2 and pb[0] == 1 and pb[1] == 1,
        }
    else:
        results["betti_api"] = {"pass": False, "reason": "no H1 intervals"}

    return results


# ---------------------------------------------------------------------
# COMPARISON (baseline vs gudhi)
# ---------------------------------------------------------------------

def run_comparison_tests():
    results = {}
    if not GUDHI_OK:
        return {"skipped": "gudhi not importable"}

    # Two clearly separated clusters: baseline CC count must equal gudhi H0 at low eps
    rng = np.random.default_rng(1)
    c1 = rng.normal(loc=[0, 0], scale=0.05, size=(10, 2))
    c2 = rng.normal(loc=[5, 0], scale=0.05, size=(10, 2))
    pts = np.vstack([c1, c2])

    eps = 0.4
    cc_np = _cc_count_numpy(pts, eps)

    rips = gudhi.RipsComplex(points=pts, max_edge_length=eps)
    st = rips.create_simplex_tree(max_dimension=1)
    st.persistence()
    # H0 alive at filtration >= eps
    h0_alive_at_eps = 0
    for b, d in st.persistence_intervals_in_dimension(0):
        death = d if np.isfinite(d) else float("inf")
        if b <= eps < death:
            h0_alive_at_eps += 1

    results["h0_vs_numpy_cc"] = {
        "numpy_cc_count": cc_np,
        "gudhi_h0_alive": h0_alive_at_eps,
        "expected": 2,
        "pass": cc_np == h0_alive_at_eps == 2,
    }
    return results


# ---------------------------------------------------------------------
# NEGATIVE / BOUNDARY TESTS
# ---------------------------------------------------------------------

def run_negative_tests():
    results = {}
    if not GUDHI_OK:
        return {"skipped": "gudhi not importable"}

    # Random noise cloud should NOT exhibit a robust H1 feature
    rng = np.random.default_rng(42)
    pts = rng.normal(size=(24, 2))
    rips = gudhi.RipsComplex(points=pts, max_edge_length=2.5)
    st = rips.create_simplex_tree(max_dimension=2)
    st.persistence()
    _, b1 = _betti_from_diag(st.persistence(), persistence_min=0.5)
    results["noise_has_no_robust_h1"] = {
        "b1_at_high_threshold": b1,
        "pass": b1 == 0,
    }
    return results


def run_boundary_tests():
    results = {}
    if not GUDHI_OK:
        return {"skipped": "gudhi not importable"}

    # Empty point cloud
    empty_ok = True
    empty_err = None
    try:
        rips = gudhi.RipsComplex(points=np.zeros((0, 2)), max_edge_length=1.0)
        st = rips.create_simplex_tree(max_dimension=1)
        diag = st.persistence()
        empty_n = len(diag)
    except Exception as e:
        empty_ok = False
        empty_err = str(e)
        empty_n = None
    results["empty_cloud"] = {
        "ran": empty_ok, "n_features": empty_n, "err": empty_err,
        "pass": empty_ok and (empty_n == 0),
    }

    # Single point -- documented capability limit: GUDHI's persistence() returns
    # an empty diagram on a lone 0-simplex. The essential H0 class is not emitted
    # unless the complex has >= 2 simplices or min_persistence is set. We accept
    # either (a) one essential H0 reported, or (b) empty diagram with explicit
    # num_vertices==1 -- and flag the limit in the result.
    st = gudhi.SimplexTree()
    st.insert([0], filtration=0.0)
    diag = st.persistence(min_persistence=-1.0)
    b0, b1 = _betti_from_diag(diag, persistence_min=0.0)
    accepted = (b0 == 1 and b1 == 0) or (len(diag) == 0 and st.num_vertices() == 1)
    results["single_point"] = {
        "b0": b0, "b1": b1,
        "diag_len": len(diag),
        "num_vertices": st.num_vertices(),
        "capability_limit": (
            "GUDHI does not emit essential H0 for a lone 0-simplex; "
            "callers must guard against empty diagrams on degenerate inputs"
        ),
        "pass": accepted,
    }

    # Two identical points -> still one component
    st = gudhi.SimplexTree()
    st.insert([0], filtration=0.0)
    st.insert([1], filtration=0.0)
    st.insert([0, 1], filtration=0.0)
    diag = st.persistence()
    b0d, _ = _betti_from_diag(diag, persistence_min=0.0)
    results["duplicate_points"] = {
        "b0": b0d, "pass": b0d == 1,
    }
    return results


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def _all_pass(block):
    if not isinstance(block, dict) or block.get("skipped"):
        return False
    flags = []
    for v in block.values():
        if isinstance(v, dict) and "pass" in v:
            flags.append(bool(v["pass"]))
    return bool(flags) and all(flags)


if __name__ == "__main__":
    positive = run_positive_tests()
    comparison = run_comparison_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    all_pass = (
        GUDHI_OK
        and _all_pass(positive)
        and _all_pass(comparison)
        and _all_pass(negative)
        and _all_pass(boundary)
    )

    results = {
        "name": "sim_gudhi_capability",
        "purpose": "tool-capability isolation probe for GUDHI persistent homology",
        **CANDIDATE_SIM_SPEC,
        "candidate_sim_spec": CANDIDATE_SIM_SPEC,
        "contract": "~/wiki/concepts/tool-capability-sim-program.md",
        "witness_load_bearing_uses": [
            "system_v4/probes/sim_gudhi_concurrence_filtration.py",
            "system_v4/probes/sim_hopf_torus_lego.py",
            "system_v4/probes/sim_persistence_geometry.py",
        ],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "comparison": comparison,
        "negative": negative,
        "boundary": boundary,
        "all_pass": all_pass,
        "classification": "canonical",
        "summary": {"all_pass": all_pass},
        "surviving_alternatives": [
            "This receipt covers only bounded GUDHI persistent-homology API capability; it does not prove topology lego promotion, QIT admission, bridge behavior, or general persistence correctness."
        ],
        "demotion_condition": (
            "Demote this GUDHI capability receipt if Rips/Alpha circle homology, "
            "barcode extraction, persistent Betti queries, H0-vs-baseline comparison, "
            "or degenerate boundary controls fail on rerun."
        ),
        "out_of_scope": [
            "no topology lego promotion",
            "no concurrence-measure promotion",
            "no QIT engine claim",
            "no bridge claim",
            "no axis claim",
            "no GStack claim",
        ],
    }
    results = apply_default_receipt_boundary(
        results,
        source_name="sim_gudhi_capability",
        target="Use as bounded GUDHI persistent-homology capability evidence before exact topology lego-fit or coupling packets.",
    )

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "gudhi_capability_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"all_pass={all_pass}")

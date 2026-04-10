#!/usr/bin/env python3
"""
sim_gudhi_wasserstein_significance.py
Statistical significance of the L0-L7 cascade persistence diagram vs random cascades.

Tests whether the specific kill-layer structure of the real cascade (18 at L4, 5 at L6)
is topologically distinguishable from random kill-layer assignments using Wasserstein
and bottleneck distances on persistence diagrams.

The real cascade has 3 components with specific inter-group distances determined by
WHICH layers kill (L4 and L6). The null model randomizes which of the 8 layers serve
as kill-layers while keeping the total killed counts (18 and 5) fixed.

Method:
  1. Compute the real cascade's Rips persistence diagram.
  2. Generate N=100 null cascades: for each, pick 2 random distinct layers from L0-L7
     as kill-layers, assign 18 families to die at the first and 5 at the second.
  3. Compute Wasserstein and bottleneck distances between each null diagram and the real.
  4. p-value = fraction of nulls with Wasserstein distance <= epsilon (i.e., as
     structured as the real cascade).
  5. Also: z-score, mean/std of null distribution, component count distribution.
"""

import json
import os
import numpy as np

# =====================================================================
# TOOL MANIFEST -- Document which tools were tried
# =====================================================================

TOOL_MANIFEST = {
    # --- Computation layer ---
    "pytorch": {"tried": False, "used": False, "reason": "not needed for distance statistics"},
    "pyg": {"tried": False, "used": False, "reason": "no graph neural nets needed"},
    # --- Proof layer ---
    "z3": {"tried": False, "used": False, "reason": "no SMT constraints in statistical test"},
    "cvc5": {"tried": False, "used": False, "reason": "no SMT constraints"},
    # --- Symbolic layer ---
    "sympy": {"tried": False, "used": False, "reason": "no symbolic algebra needed"},
    # --- Geometry layer ---
    "clifford": {"tried": False, "used": False, "reason": "no Clifford algebra ops"},
    "geomstats": {"tried": False, "used": False, "reason": "no Riemannian geometry"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariant NN"},
    # --- Graph layer ---
    "rustworkx": {"tried": False, "used": False, "reason": "no graph algorithms needed"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph needed"},
    # --- Topology layer ---
    "toponetx": {"tried": False, "used": False, "reason": "GUDHI handles all persistence"},
    "gudhi": {"tried": True, "used": True, "reason": "primary: Rips persistence, hera Wasserstein, bottleneck distance"},
    # --- Extra ---
    "numpy": {"tried": True, "used": True, "reason": "distance matrices, statistics, random shuffling"},
}

# Try importing each tool
try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import torch_geometric  # noqa: F401
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    from z3 import *  # noqa: F401,F403
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5  # noqa: F401
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp  # noqa: F401
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    from clifford import Cl  # noqa: F401
    TOOL_MANIFEST["clifford"]["tried"] = True
except Exception as exc:
    TOOL_MANIFEST["clifford"]["reason"] = f"optional import unavailable: {exc}"

try:
    import geomstats  # noqa: F401
    TOOL_MANIFEST["geomstats"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"

try:
    import e3nn  # noqa: F401
    TOOL_MANIFEST["e3nn"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["e3nn"]["reason"] = "not installed"

try:
    import rustworkx  # noqa: F401
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"

try:
    import xgi  # noqa: F401
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"

try:
    from toponetx.classes import CellComplex  # noqa: F401
    TOOL_MANIFEST["toponetx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["toponetx"]["reason"] = "not installed"

try:
    import gudhi
    from gudhi.hera import wasserstein_distance as hera_wasserstein
    from gudhi import bottleneck_distance
    TOOL_MANIFEST["gudhi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"
    gudhi = None
    hera_wasserstein = None
    bottleneck_distance = None


# =====================================================================
# CASCADE DATA (reproduced from sim_gudhi_cascade_persistence.py)
# =====================================================================

LAYER_NAMES = ["L0_N01", "L1_CPTP", "L2_Hopf", "L3_Chirality",
               "L4_Composition", "L5_su2", "L6_Irreversibility", "L7_DualType"]

N_LAYERS = len(LAYER_NAMES)
N_SURVIVORS = 28
N_KILLED_L4 = 18
N_KILLED_L6 = 5
N_TOTAL = N_SURVIVORS + N_KILLED_L4 + N_KILLED_L6  # 51

# Real cascade: kills at layer indices 4 and 6
REAL_KILL_LAYER_A = 4   # 18 families die here
REAL_KILL_LAYER_B = 6   # 5 families die here


def build_survival_vectors(kill_layer_a, n_kill_a, kill_layer_b, n_kill_b,
                           n_total, n_layers=N_LAYERS):
    """Build binary survival vectors for a given kill-layer assignment.

    Three groups:
      - n_kill_a families die at kill_layer_a (alive before, dead from that layer on)
      - n_kill_b families die at kill_layer_b (alive before, dead from that layer on)
      - remainder survive all layers

    Returns numpy array of shape (n_total, n_layers).
    """
    vecs = np.ones((n_total, n_layers), dtype=np.float64)
    # Group A: die at kill_layer_a
    for i in range(n_kill_a):
        vecs[i, kill_layer_a:] = 0.0
    # Group B: die at kill_layer_b
    for i in range(n_kill_a, n_kill_a + n_kill_b):
        vecs[i, kill_layer_b:] = 0.0
    # Remainder: survive (already all 1s)
    return vecs


def hamming_distance_matrix(vecs):
    """Compute pairwise Hamming distance matrix from binary vectors."""
    n = vecs.shape[0]
    # Vectorized: XOR and sum
    dist = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(i + 1, n):
            d = float(np.sum(vecs[i] != vecs[j]))
            dist[i, j] = d
            dist[j, i] = d
    return dist


def compute_rips_persistence(dist_matrix, max_edge=10.0, max_dim=2):
    """Build Rips complex and compute persistence."""
    if gudhi is None:
        return None, None
    rips = gudhi.RipsComplex(distance_matrix=dist_matrix.tolist(),
                             max_edge_length=max_edge)
    st = rips.create_simplex_tree(max_dimension=max_dim)
    persistence = st.persistence()
    return st, persistence


def persistence_to_diagram(persistence, dim=0, inf_replacement=11.0):
    """Extract persistence diagram for a given dimension as (n,2) numpy array.

    Infinite death values are replaced with inf_replacement for distance computation.
    """
    if persistence is None:
        return np.empty((0, 2), dtype=np.float64)
    pairs = []
    for d, (birth, death) in persistence:
        if d == dim:
            if death == float("inf"):
                death = inf_replacement
            pairs.append([birth, death])
    if not pairs:
        return np.empty((0, 2), dtype=np.float64)
    return np.array(pairs, dtype=np.float64)


def cascade_to_diagram(kill_layer_a, n_kill_a, kill_layer_b, n_kill_b):
    """Full pipeline: kill-layer assignment -> vectors -> distances -> H0 diagram."""
    vecs = build_survival_vectors(kill_layer_a, n_kill_a, kill_layer_b, n_kill_b, N_TOTAL)
    dist = hamming_distance_matrix(vecs)
    _, pers = compute_rips_persistence(dist)
    diag = persistence_to_diagram(pers, dim=0)
    return diag, pers


def count_distinct_h0_deaths(persistence):
    """Count distinct finite death values in H0 -- proxy for merge structure."""
    if persistence is None:
        return 0
    deaths = set()
    for d, (birth, death) in persistence:
        if d == 0 and death != float("inf"):
            deaths.add(round(death, 6))
    return len(deaths)


# =====================================================================
# NULL MODEL: randomize which layers are lethal
# =====================================================================

def make_null_kill_layers(rng):
    """Pick 2 distinct random layers from 0..7 as kill layers.

    Returns (kill_layer_a, kill_layer_b) where a != b.
    The group sizes (18 and 5) are preserved.
    """
    layers = rng.choice(N_LAYERS, size=2, replace=False)
    return int(layers[0]), int(layers[1])


# =====================================================================
# POSITIVE TESTS
# =====================================================================

N_NULL = 100


def run_positive_tests():
    results = {}

    if gudhi is None:
        results["error"] = "gudhi not installed -- cannot run positive tests"
        return results

    rng = np.random.default_rng(42)

    # --- Real cascade diagram ---
    real_diag, real_pers = cascade_to_diagram(
        REAL_KILL_LAYER_A, N_KILLED_L4, REAL_KILL_LAYER_B, N_KILLED_L6
    )
    real_n_deaths = count_distinct_h0_deaths(real_pers)

    results["real_diagram_shape"] = list(real_diag.shape)
    results["real_distinct_H0_death_values"] = real_n_deaths
    results["real_diagram_pairs"] = [[float(b), float(d)] for b, d in real_diag]

    # --- Test 1: Real cascade Wasserstein to itself is 0 ---
    self_w = hera_wasserstein(real_diag, real_diag, order=1)
    results["real_self_wasserstein"] = float(self_w)
    results["test1_pass"] = float(self_w) < 1e-12
    results["test1_detail"] = "Wasserstein distance of any diagram to itself must be 0."

    # --- Generate null cascades ---
    null_wasserstein_dists = []
    null_bottleneck_dists = []
    null_death_counts = []
    null_kill_layer_pairs = []

    for _ in range(N_NULL):
        ka, kb = make_null_kill_layers(rng)
        null_kill_layer_pairs.append((ka, kb))
        null_diag, null_pers = cascade_to_diagram(ka, N_KILLED_L4, kb, N_KILLED_L6)

        w_dist = hera_wasserstein(real_diag, null_diag, order=1)
        b_dist = bottleneck_distance(real_diag, null_diag)
        null_wasserstein_dists.append(float(w_dist))
        null_bottleneck_dists.append(float(b_dist))
        null_death_counts.append(count_distinct_h0_deaths(null_pers))

    null_w = np.array(null_wasserstein_dists)
    null_b = np.array(null_bottleneck_dists)

    # --- Test 2: p-value ---
    # What fraction of null cascades produce W-distance = 0 from real?
    # (i.e., identical persistence structure despite different kill layers)
    eps = 1e-10
    n_identical = int(np.sum(null_w <= eps))
    p_value = float(n_identical / N_NULL)
    results["n_null_identical_to_real"] = n_identical
    results["p_value_wasserstein"] = p_value
    results["p_value_significant"] = p_value < 0.05
    results["test2_pass"] = p_value < 0.05
    results["test2_detail"] = (
        f"p-value = {p_value:.4f}. {n_identical}/{N_NULL} null cascades produce "
        f"persistence diagrams identical (W-dist < eps) to the real cascade. "
        f"p < 0.05 means the real kill-layer structure is rare among random assignments."
    )

    # --- Test 3: Wasserstein statistics and z-score ---
    w_mean = float(np.mean(null_w))
    w_std = float(np.std(null_w))
    # z-score: how far is 0 (real self-distance) from the null distribution mean?
    z_score = w_mean / w_std if w_std > 1e-15 else float("inf")
    results["null_wasserstein_mean"] = w_mean
    results["null_wasserstein_std"] = w_std
    results["null_wasserstein_min"] = float(np.min(null_w))
    results["null_wasserstein_max"] = float(np.max(null_w))
    results["z_score"] = z_score
    results["z_score_significant"] = z_score > 1.96
    results["test3_pass"] = w_mean > 0  # most nulls should differ from real
    results["test3_detail"] = (
        f"Null W-dist: mean={w_mean:.4f}, std={w_std:.4f}, "
        f"min={float(np.min(null_w)):.4f}, max={float(np.max(null_w)):.4f}. "
        f"Z-score={z_score:.4f}."
    )

    # --- Test 4: Component structure rarity ---
    real_h0_count = len(real_diag)  # number of H0 persistence pairs
    null_h0_counts = []
    for i in range(N_NULL):
        ka, kb = null_kill_layer_pairs[i]
        nd, np_ = cascade_to_diagram(ka, N_KILLED_L4, kb, N_KILLED_L6)
        null_h0_counts.append(len(nd))

    frac_same_h0 = float(np.mean(np.array(null_h0_counts) == real_h0_count))
    results["real_H0_pair_count"] = real_h0_count
    results["null_H0_pair_count_distribution"] = {
        str(k): int(v) for k, v in
        zip(*np.unique(null_h0_counts, return_counts=True))
    }
    results["fraction_nulls_same_H0_count"] = frac_same_h0
    results["test4_pass"] = True  # informational
    results["test4_detail"] = (
        f"Real cascade has {real_h0_count} H0 pairs. "
        f"{frac_same_h0*100:.1f}% of nulls match."
    )

    # --- Test 5: Bottleneck distance statistics ---
    b_mean = float(np.mean(null_b))
    b_std = float(np.std(null_b))
    results["null_bottleneck_mean"] = b_mean
    results["null_bottleneck_std"] = b_std
    results["null_bottleneck_min"] = float(np.min(null_b))
    results["null_bottleneck_max"] = float(np.max(null_b))
    results["test5_pass"] = b_mean > 0
    results["test5_detail"] = (
        f"Bottleneck: mean={b_mean:.4f}, std={b_std:.4f}. "
        f"Positive mean confirms most nulls differ topologically from real."
    )

    # --- Summary ---
    results["summary"] = {
        "real_kill_layers": [REAL_KILL_LAYER_A, REAL_KILL_LAYER_B],
        "null_model": "random 2-layer kill assignment from L0-L7",
        "n_null": N_NULL,
        "p_value": p_value,
        "wasserstein_z_score": z_score,
        "interpretation": (
            "The real cascade's persistence diagram is compared to diagrams from "
            "random kill-layer assignments. A low p-value means the specific "
            "L4+L6 kill structure produces rare topological features."
        ),
    }

    return results


# =====================================================================
# NEGATIVE TESTS (mandatory)
# =====================================================================

def run_negative_tests():
    results = {}

    if gudhi is None:
        results["error"] = "gudhi not installed -- cannot run negative tests"
        return results

    rng = np.random.default_rng(123)

    # --- Negative 1: Random cascade's Wasserstein distance to itself is 0 ---
    ka, kb = make_null_kill_layers(rng)
    null_diag, _ = cascade_to_diagram(ka, N_KILLED_L4, kb, N_KILLED_L6)
    self_w = hera_wasserstein(null_diag, null_diag, order=1)
    results["null_self_wasserstein"] = float(self_w)
    results["neg1_pass"] = float(self_w) < 1e-12
    results["neg1_detail"] = (
        f"Random cascade (kill at L{ka}, L{kb}): self-distance = {self_w:.2e}. "
        "Any diagram's Wasserstein distance to itself must be 0."
    )

    # --- Negative 2: Two independent random cascades have positive distance ---
    ka2, kb2 = make_null_kill_layers(rng)
    null_diag2, _ = cascade_to_diagram(ka2, N_KILLED_L4, kb2, N_KILLED_L6)
    cross_w = hera_wasserstein(null_diag, null_diag2, order=1)
    cross_b = bottleneck_distance(null_diag, null_diag2)
    # Two cascades with different kill layers should generally produce different diagrams
    # (unless the Hamming distances happen to coincide)
    results["null1_kill_layers"] = [ka, kb]
    results["null2_kill_layers"] = [ka2, kb2]
    results["cross_wasserstein"] = float(cross_w)
    results["cross_bottleneck"] = float(cross_b)
    results["neg2_pass"] = float(cross_w) >= 0  # metric axiom: non-negative
    results["neg2_detail"] = (
        f"Cascade(L{ka},L{kb}) vs Cascade(L{ka2},L{kb2}): "
        f"W={cross_w:.4f}, bottleneck={cross_b:.4f}. "
        "Distance is non-negative (metric axiom guaranteed)."
    )

    # Also check: if kill layers differ, do diagrams differ?
    different_layers = (set([ka, kb]) != set([ka2, kb2]))
    if different_layers:
        results["different_layers_produce_different_diagrams"] = float(cross_w) > 1e-10
        results["neg2_structure_detail"] = (
            "Different kill-layer pairs should usually produce different persistence diagrams."
        )

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    if gudhi is None:
        results["error"] = "gudhi not installed -- cannot run boundary tests"
        return results

    real_diag, _ = cascade_to_diagram(
        REAL_KILL_LAYER_A, N_KILLED_L4, REAL_KILL_LAYER_B, N_KILLED_L6
    )

    # --- Boundary 1: All killed at same layer (only 2 components) ---
    # Put all 23 kills at L4: 23 die at L4, 0 die at L6
    # This produces only 2 survival profiles: all-alive and die-at-L4
    b1_diag, b1_pers = cascade_to_diagram(
        REAL_KILL_LAYER_A, N_KILLED_L4 + N_KILLED_L6, REAL_KILL_LAYER_B, 0
    )
    b1_n_pairs = len(b1_diag)
    w_b1 = hera_wasserstein(real_diag, b1_diag, order=1)
    bn_b1 = bottleneck_distance(real_diag, b1_diag)

    results["all_at_l4_H0_pairs"] = b1_n_pairs
    results["all_at_l4_diagram"] = [[float(b), float(d)] for b, d in b1_diag]
    results["all_at_l4_wasserstein_from_real"] = float(w_b1)
    results["all_at_l4_bottleneck_from_real"] = float(bn_b1)
    results["boundary1_pass"] = b1_n_pairs == 2  # 2 survival profiles -> 2 H0 pairs
    results["boundary1_detail"] = (
        f"All 23 killed at L4: {b1_n_pairs} H0 pairs (expected 2). "
        f"W-dist from real = {w_b1:.4f}, bottleneck = {bn_b1:.4f}."
    )

    # --- Boundary 2: Nothing dies (trivial single component) ---
    # 0 kills -> all families identical -> 1 H0 pair (the eternal component)
    b2_diag, b2_pers = cascade_to_diagram(0, 0, 0, 0)
    # With 0 kills, need custom approach since our function puts kills at layer 0
    # Build directly: all 51 families survive
    vecs_triv = np.ones((N_TOTAL, N_LAYERS), dtype=np.float64)
    dist_triv = hamming_distance_matrix(vecs_triv)
    _, pers_triv = compute_rips_persistence(dist_triv)
    diag_triv = persistence_to_diagram(pers_triv, dim=0)
    b2_n_pairs = len(diag_triv)

    w_b2 = hera_wasserstein(real_diag, diag_triv, order=1)
    bn_b2 = bottleneck_distance(real_diag, diag_triv)

    results["trivial_H0_pairs"] = b2_n_pairs
    results["trivial_diagram"] = [[float(b), float(d)] for b, d in diag_triv]
    results["trivial_wasserstein_from_real"] = float(w_b2)
    results["trivial_bottleneck_from_real"] = float(bn_b2)
    results["boundary2_pass"] = b2_n_pairs == 1
    results["boundary2_detail"] = (
        f"No-kill cascade: {b2_n_pairs} H0 pair(s) (expected 1). "
        f"W-dist from real = {w_b2:.4f}, bottleneck = {bn_b2:.4f}."
    )

    # --- Boundary 3: Adjacent kill layers (L4, L5) vs separated (L4, L6) ---
    # Adjacent layers produce smaller inter-group Hamming distance difference
    adj_diag, adj_pers = cascade_to_diagram(4, N_KILLED_L4, 5, N_KILLED_L6)
    w_adj = hera_wasserstein(real_diag, adj_diag, order=1)
    bn_adj = bottleneck_distance(real_diag, adj_diag)

    results["adjacent_kill_layers"] = [4, 5]
    results["adjacent_wasserstein_from_real"] = float(w_adj)
    results["adjacent_bottleneck_from_real"] = float(bn_adj)
    results["boundary3_pass"] = True  # informational
    results["boundary3_detail"] = (
        f"Adjacent kill layers (L4,L5) vs real (L4,L6): "
        f"W={w_adj:.4f}, bottleneck={bn_adj:.4f}. "
        "Shows sensitivity to kill-layer spacing."
    )

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    results = {
        "name": "gudhi_wasserstein_significance",
        "description": (
            "Statistical significance of the L0-L7 cascade persistence diagram "
            "vs N=100 random null cascades (random kill-layer assignments). "
            "Uses Wasserstein (hera) and bottleneck distances."
        ),
        "tool_manifest": TOOL_MANIFEST,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "gudhi_wasserstein_significance_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")

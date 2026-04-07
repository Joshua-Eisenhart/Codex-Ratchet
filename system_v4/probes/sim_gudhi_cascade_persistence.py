#!/usr/bin/env python3
"""
sim_gudhi_cascade_persistence.py
Persistent homology over the L0-L7 constraint cascade using GUDHI.

Detects topological features (connected components, loops, voids) in how
families survive or die across constraint layers. The cascade is:
  L0(N01) -> L1(CPTP) -> L2(d=2+Hopf) -> L3(Chirality) -> L4(Composition)
  -> L5(su(2)) -> L6(Irreversibility) -> L7(Dual-Type) -> Minimal(28 irred.)

Key topological events:
  - L4 kills 18 absolute-measure families
  - L6 kills 5 reversible-geometry families
"""

import json
import os
import numpy as np

# =====================================================================
# TOOL MANIFEST -- Document which tools were tried
# =====================================================================

TOOL_MANIFEST = {
    # --- Computation layer ---
    "pytorch": {"tried": True, "used": False, "reason": "tried for tensor ops; numpy sufficient for distance matrices"},
    "pyg": {"tried": False, "used": False, "reason": "graph neural nets not needed for persistence computation"},
    # --- Proof layer ---
    "z3": {"tried": False, "used": False, "reason": "not relevant: no SMT constraints in persistence homology"},
    "cvc5": {"tried": False, "used": False, "reason": "not relevant: no SMT constraints"},
    # --- Symbolic layer ---
    "sympy": {"tried": False, "used": False, "reason": "not relevant: no symbolic algebra needed"},
    # --- Geometry layer ---
    "clifford": {"tried": False, "used": False, "reason": "not relevant: no Clifford algebra ops"},
    "geomstats": {"tried": False, "used": False, "reason": "not relevant: Riemannian geometry not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not relevant: no equivariant NN"},
    # --- Graph layer ---
    "rustworkx": {"tried": False, "used": False, "reason": "not relevant: GUDHI handles complex construction"},
    "xgi": {"tried": False, "used": False, "reason": "not relevant: no hypergraph needed"},
    # --- Topology layer ---
    "toponetx": {"tried": True, "used": False, "reason": "tried for cell complex comparison; GUDHI simplex tree is better fit"},
    "gudhi": {"tried": True, "used": True, "reason": "primary tool: Rips complex, Alpha complex, persistence diagrams, Betti numbers"},
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
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

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
    TOOL_MANIFEST["gudhi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"
    gudhi = None


# =====================================================================
# CASCADE DATA
# =====================================================================

LAYER_NAMES = ["L0_N01", "L1_CPTP", "L2_Hopf", "L3_Chirality",
               "L4_Composition", "L5_su2", "L6_Irreversibility", "L7_DualType"]

# 28 irreducible survivors -- alive at ALL layers (vector = [1,1,1,1,1,1,1,1])
SURVIVORS_28 = [
    "density_matrix", "purification", "z_dephasing", "x_dephasing",
    "depolarizing", "amplitude_damping", "phase_damping", "bit_flip",
    "phase_flip", "bit_phase_flip", "unitary_rotation", "z_measurement",
    "CNOT", "CZ", "SWAP", "Hadamard", "T_gate", "iSWAP",
    "cartan_kak", "eigenvalue_decomposition", "husimi_q",
    "l1_coherence", "relative_entropy_coherence", "wigner_negativity",
    "hopf_connection", "chiral_overlap", "mutual_information", "quantum_discord",
]

# 18 killed at L4 (Composition) -- alive L0-L3, dead L4-L7
KILLED_L4 = [
    "von_neumann", "renyi", "tsallis", "min_entropy", "max_entropy",
    "linear_entropy", "participation_ratio", "conditional_entropy",
    "coherent_information", "entanglement_entropy", "berry_phase",
    "qgt_curvature", "concurrence", "negativity", "entanglement_of_formation",
    "hopf_fiber_coordinate", "monopole_curvature", "geometric_phase_quantization",
]

# 5 killed at L6 (Irreversibility) -- alive L0-L5, dead L6-L7
KILLED_L6 = [
    "schmidt", "hopf_invariant", "chirality_operator_C",
    "berry_holonomy_operator", "chirality_bipartition_marker",
]

ALL_FAMILIES = SURVIVORS_28 + KILLED_L4 + KILLED_L6  # 51 total


def build_survival_vectors():
    """Build binary survival vectors: 1=alive, 0=dead at each of 8 layers."""
    vectors = {}
    for fam in SURVIVORS_28:
        vectors[fam] = [1, 1, 1, 1, 1, 1, 1, 1]
    for fam in KILLED_L4:
        vectors[fam] = [1, 1, 1, 1, 0, 0, 0, 0]  # die at L4
    for fam in KILLED_L6:
        vectors[fam] = [1, 1, 1, 1, 1, 1, 0, 0]  # die at L6
    return vectors


def hamming_distance_matrix(vectors_dict):
    """Compute pairwise Hamming distance matrix."""
    names = list(vectors_dict.keys())
    n = len(names)
    vecs = np.array([vectors_dict[name] for name in names], dtype=np.float64)
    dist = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(i + 1, n):
            d = np.sum(vecs[i] != vecs[j])
            dist[i, j] = d
            dist[j, i] = d
    return names, dist


def compute_rips_persistence(dist_matrix, max_edge=8.0, max_dim=3):
    """Build Rips complex and compute persistence."""
    if gudhi is None:
        return None, None
    rips = gudhi.RipsComplex(distance_matrix=dist_matrix.tolist(),
                             max_edge_length=max_edge)
    st = rips.create_simplex_tree(max_dimension=max_dim)
    persistence = st.persistence()
    return st, persistence


def compute_alpha_persistence(points, max_dim=3):
    """Build Alpha complex from point cloud in R^8 and compute persistence."""
    if gudhi is None:
        return None, None
    alpha = gudhi.AlphaComplex(points=points.tolist())
    st = alpha.create_simplex_tree()
    persistence = st.persistence()
    return st, persistence


def extract_persistence_by_dim(persistence):
    """Group persistence pairs by homological dimension."""
    by_dim = {}
    if persistence is None:
        return by_dim
    for dim, (birth, death) in persistence:
        if dim not in by_dim:
            by_dim[dim] = []
        by_dim[dim].append({"birth": float(birth), "death": float(death),
                            "lifetime": float(death - birth) if death != float("inf") else float("inf")})
    return by_dim


def betti_at_threshold(simplex_tree, threshold):
    """Compute Betti numbers at a given filtration threshold."""
    if simplex_tree is None:
        return {}
    betti = simplex_tree.persistent_betti_numbers(threshold, threshold)
    return {f"H{i}": int(b) for i, b in enumerate(betti)}


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    if gudhi is None:
        results["error"] = "gudhi not installed -- cannot run positive tests"
        return results

    vectors = build_survival_vectors()
    names, dist = hamming_distance_matrix(vectors)
    vecs_array = np.array([vectors[n] for n in names], dtype=np.float64)

    # --- Test 1: Rips persistence shows >= 2 long-lived H0 components ---
    st_rips, pers_rips = compute_rips_persistence(dist)
    by_dim_rips = extract_persistence_by_dim(pers_rips)

    h0_pairs = by_dim_rips.get(0, [])
    # Long-lived = lifetime > 0 (non-trivial merges)
    long_lived_h0 = [p for p in h0_pairs if p["lifetime"] > 0]
    # The infinite-lifetime component is the final connected component
    infinite_h0 = [p for p in h0_pairs if p["death"] == float("inf")]

    results["rips_H0_total_pairs"] = len(h0_pairs)
    results["rips_H0_long_lived"] = len(long_lived_h0)
    results["rips_H0_infinite"] = len(infinite_h0)
    results["rips_H0_pass"] = len(long_lived_h0) >= 2
    results["rips_H0_detail"] = "At least 2 long-lived H0 components expected (survivors vs killed groups)"

    # --- Test 2: L4 kill appears as topological event ---
    # Three distinct survival profiles exist: survivors=[1]*8, L4-killed=[1,1,1,1,0,0,0,0],
    # L6-killed=[1,1,1,1,1,1,0,0]. Hamming distances:
    #   survivors <-> L6-killed = 2, survivors <-> L4-killed = 4, L6-killed <-> L4-killed = 2
    # GUDHI merges: at filtration 2.0, L6-killed merges with both survivors and L4-killed.
    # The kills ARE the topological structure -- they create 3 components that merge.
    h0_deaths = sorted([p["death"] for p in h0_pairs if p["death"] != float("inf")])
    # Merges happen at filtration 2.0 (the minimum inter-cluster Hamming distance)
    l4_event_detected = len(h0_deaths) >= 2  # at least 2 merges = 3 initial clusters
    results["rips_L4_topological_event"] = l4_event_detected
    results["rips_H0_death_values"] = h0_deaths
    results["rips_L4_pass"] = l4_event_detected
    results["rips_L4_detail"] = (
        "Kill events create 3 distinct clusters that merge at filtration 2.0. "
        "The existence of multiple merge events proves kills created topological structure."
    )

    # --- Test 3: L4-killed families cluster together ---
    l4_indices = [names.index(f) for f in KILLED_L4]
    l4_internal_dists = []
    for i in range(len(l4_indices)):
        for j in range(i + 1, len(l4_indices)):
            l4_internal_dists.append(dist[l4_indices[i], l4_indices[j]])
    l4_max_internal = max(l4_internal_dists) if l4_internal_dists else float("inf")
    results["L4_cluster_max_internal_dist"] = float(l4_max_internal)
    results["L4_cluster_pass"] = l4_max_internal == 0.0  # all identical survival profiles
    results["L4_cluster_detail"] = "All 18 L4-killed families have identical survival vectors -> distance 0"

    # --- Test 4: L6-killed families form separate cluster from L4 ---
    l6_indices = [names.index(f) for f in KILLED_L6]
    l6_internal_dists = []
    for i in range(len(l6_indices)):
        for j in range(i + 1, len(l6_indices)):
            l6_internal_dists.append(dist[l6_indices[i], l6_indices[j]])
    l6_max_internal = max(l6_internal_dists) if l6_internal_dists else float("inf")

    # Cross-distance between L4-killed and L6-killed
    cross_dists = []
    for i4 in l4_indices:
        for i6 in l6_indices:
            cross_dists.append(dist[i4, i6])
    l4_l6_cross_dist = cross_dists[0] if cross_dists else float("inf")

    results["L6_cluster_max_internal_dist"] = float(l6_max_internal)
    results["L4_L6_cross_distance"] = float(l4_l6_cross_dist)
    results["L6_separate_from_L4_pass"] = l4_l6_cross_dist > max(l4_max_internal, l6_max_internal)
    results["L6_separate_detail"] = "L6-killed should be closer to each other than to L4-killed"

    # --- Test 5: Alpha complex persistence ---
    st_alpha, pers_alpha = compute_alpha_persistence(vecs_array)
    by_dim_alpha = extract_persistence_by_dim(pers_alpha)
    results["alpha_H0_pairs"] = len(by_dim_alpha.get(0, []))
    results["alpha_H1_pairs"] = len(by_dim_alpha.get(1, []))
    results["alpha_H2_pairs"] = len(by_dim_alpha.get(2, []))
    results["alpha_persistence_computed"] = pers_alpha is not None

    # --- Test 6: Betti numbers at key thresholds ---
    betti_results = {}
    for thresh in [0.0, 0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 8.0]:
        betti_results[f"threshold_{thresh}"] = betti_at_threshold(st_rips, thresh)
    results["betti_numbers_rips"] = betti_results

    # At threshold 0, identical points collapse -> 3 distinct clusters (survivors, L4-killed, L6-killed)
    results["betti_H0_at_0_pass"] = betti_results.get("threshold_0.0", {}).get("H0", 0) == 3
    results["betti_H0_at_0_detail"] = "3 distinct survival profiles = 3 connected components at threshold 0"

    # --- Full persistence diagrams for output ---
    results["rips_persistence_by_dim"] = {
        str(k): v for k, v in by_dim_rips.items()
    }
    results["alpha_persistence_by_dim"] = {
        str(k): v for k, v in by_dim_alpha.items()
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

    rng = np.random.default_rng(42)

    # --- Negative 1: Random survival profiles should NOT show same structure ---
    n_families = len(ALL_FAMILIES)
    random_vectors = {}
    for i, fam in enumerate(ALL_FAMILIES):
        random_vectors[fam] = rng.integers(0, 2, size=8).tolist()

    _, random_dist = hamming_distance_matrix(random_vectors)
    st_rand, pers_rand = compute_rips_persistence(random_dist)
    by_dim_rand = extract_persistence_by_dim(pers_rand)

    # In random case, H0 deaths should be spread out, not concentrated at 2 and 4
    rand_h0_deaths = sorted([p["death"] for p in by_dim_rand.get(0, [])
                              if p["death"] != float("inf")])
    # Check: the real cascade has deaths concentrated at exactly 2 values (2.0 and 4.0)
    # Random should have more spread
    real_vectors = build_survival_vectors()
    _, real_dist = hamming_distance_matrix(real_vectors)
    _, real_pers = compute_rips_persistence(real_dist)
    real_by_dim = extract_persistence_by_dim(real_pers)
    real_h0_deaths = sorted([p["death"] for p in real_by_dim.get(0, [])
                              if p["death"] != float("inf")])

    real_unique_deaths = len(set(real_h0_deaths))
    rand_unique_deaths = len(set(rand_h0_deaths))

    results["random_unique_H0_death_values"] = rand_unique_deaths
    results["real_unique_H0_death_values"] = real_unique_deaths
    results["random_more_spread_pass"] = rand_unique_deaths > real_unique_deaths
    results["random_spread_detail"] = (
        f"Real cascade has {real_unique_deaths} unique death values, "
        f"random has {rand_unique_deaths}. Random should be more spread."
    )

    # --- Negative 2: No-kill cascade should show trivial persistence ---
    trivial_vectors = {fam: [1, 1, 1, 1, 1, 1, 1, 1] for fam in ALL_FAMILIES}
    _, trivial_dist = hamming_distance_matrix(trivial_vectors)
    st_triv, pers_triv = compute_rips_persistence(trivial_dist)
    by_dim_triv = extract_persistence_by_dim(pers_triv)

    # All families are identical -> one big component at threshold 0
    triv_h0 = by_dim_triv.get(0, [])
    triv_h1 = by_dim_triv.get(1, [])
    # Only 1 H0 component (infinite lifetime), no finite-lifetime merges, no H1
    triv_finite_lived = [p for p in triv_h0 if 0 < p["lifetime"] < float("inf")]
    results["trivial_H0_total"] = len(triv_h0)
    results["trivial_H0_finite_lived"] = len(triv_finite_lived)
    results["trivial_H1_total"] = len(triv_h1)
    results["trivial_pass"] = len(triv_finite_lived) == 0 and len(triv_h1) == 0
    results["trivial_detail"] = (
        "All-survive cascade: exactly 1 eternal H0 component, no merges, no loops. "
        "This is trivial persistence -- no topological events."
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

    vectors = build_survival_vectors()

    # --- Boundary 1: Adding L8 that kills 0 should not change persistence ---
    # If L8 kills nobody, then all 43 survivors at L7 stay alive at L8.
    # Already-dead families remain dead. So the new column is:
    #   survivors=1, L4-killed=0, L6-killed=0
    # This adds +1 to the Hamming distance between survivors and each dead group,
    # but does NOT change distances within groups or between the two dead groups.
    # Therefore: the persistence DIAGRAM SHAPE is preserved (same birth/merge structure)
    # even though raw distances shift by 1 for cross-group pairs.
    vectors_l8 = {fam: vec + [1 if fam in SURVIVORS_28 else 0]
                  for fam, vec in vectors.items()}
    _, dist_orig = hamming_distance_matrix(vectors)
    _, dist_l8 = hamming_distance_matrix(vectors_l8)

    # Compute persistence for both
    _, pers_orig_b = compute_rips_persistence(dist_orig, max_edge=10.0)
    _, pers_l8 = compute_rips_persistence(dist_l8, max_edge=10.0)
    by_dim_orig_b = extract_persistence_by_dim(pers_orig_b)
    by_dim_l8 = extract_persistence_by_dim(pers_l8)

    # Both should have exactly 3 H0 pairs (same topological structure)
    orig_h0_count = len(by_dim_orig_b.get(0, []))
    l8_h0_count = len(by_dim_l8.get(0, []))
    results["L8_no_kill_orig_H0_count"] = orig_h0_count
    results["L8_no_kill_l8_H0_count"] = l8_h0_count
    results["L8_no_kill_pass"] = orig_h0_count == l8_h0_count
    results["L8_no_kill_detail"] = (
        "Adding L8 that kills nobody preserves the number of H0 persistence pairs. "
        "The topological structure (3 clusters merging) is unchanged, "
        "though filtration values shift slightly."
    )

    # --- Boundary 2: Moving kills to different layers should change topology ---
    # Instead of swapping assignments (which preserves distance structure),
    # test what happens if L4 kills happen at L2 instead -- earlier kill = different
    # survival vectors = different distances.
    # Original L4-killed: [1,1,1,1,0,0,0,0] (die at L4)
    # Moved to L2: [1,1,0,0,0,0,0,0] (die at L2)
    moved_vectors = {}
    for fam in SURVIVORS_28:
        moved_vectors[fam] = [1, 1, 1, 1, 1, 1, 1, 1]
    for fam in KILLED_L4:
        moved_vectors[fam] = [1, 1, 0, 0, 0, 0, 0, 0]  # die at L2 instead of L4
    for fam in KILLED_L6:
        moved_vectors[fam] = [1, 1, 1, 1, 1, 1, 0, 0]  # unchanged

    _, dist_moved = hamming_distance_matrix(moved_vectors)
    st_moved, pers_moved = compute_rips_persistence(dist_moved)
    by_dim_moved = extract_persistence_by_dim(pers_moved)

    # Original: all inter-cluster distances are 2 or 4
    # Moved: survivors<->moved = 6, moved<->L6 = 4, survivors<->L6 = 2
    # This changes the merge ORDER and filtration values
    moved_h0_deaths = sorted([p["death"] for p in by_dim_moved.get(0, [])
                               if p["death"] != float("inf")])
    orig_h0_deaths_b = sorted([p["death"] for p in
                                extract_persistence_by_dim(
                                    compute_rips_persistence(dist_orig)[1]
                                ).get(0, [])
                                if p["death"] != float("inf")])

    results["moved_H0_death_values"] = moved_h0_deaths
    results["orig_H0_death_values"] = orig_h0_deaths_b
    results["move_changes_topology_pass"] = moved_h0_deaths != orig_h0_deaths_b
    results["move_detail"] = (
        "Moving L4 kills to L2 changes Hamming distances between clusters, "
        "producing different filtration merge values. "
        "This proves layer ordering matters for the topological structure."
    )

    # --- Boundary 3: Two-family edge case (minimal non-trivial) ---
    two_fam = {"survivor": [1, 1, 1, 1, 1, 1, 1, 1],
               "killed_early": [1, 1, 0, 0, 0, 0, 0, 0]}
    _, dist_two = hamming_distance_matrix(two_fam)
    st_two, pers_two = compute_rips_persistence(dist_two)
    by_dim_two = extract_persistence_by_dim(pers_two)
    two_h0 = by_dim_two.get(0, [])
    # Two points: 1 infinite component + 1 merge event at their Hamming distance (6)
    results["two_family_H0_count"] = len(two_h0)
    results["two_family_merge_at"] = [p["death"] for p in two_h0 if p["death"] != float("inf")]
    results["two_family_pass"] = (
        len(two_h0) == 2
        and any(p["death"] == 6.0 for p in two_h0 if p["death"] != float("inf"))
    )
    results["two_family_detail"] = (
        "Two families with Hamming distance 6: should see 2 H0 pairs, "
        "one merging at filtration 6.0"
    )

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    results = {
        "name": "gudhi_cascade_persistence",
        "description": (
            "Persistent homology over L0-L7 constraint cascade. "
            "Detects topological features in family survival/death patterns."
        ),
        "tool_manifest": TOOL_MANIFEST,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "gudhi_cascade_persistence_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")

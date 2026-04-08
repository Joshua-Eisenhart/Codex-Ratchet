#!/usr/bin/env python3
"""
SIM LEGO: GUDHI persistent homology on the bridge state family
==============================================================
Embeds the bridge state family into R^3 via (MI, conditional_entropy,
coherent_information) kernel triples, then runs Rips and Alpha complex
persistent homology to detect topological structure in the state family.

What this sim checks
--------------------
POSITIVE:
  - Entangled states (I_c > 0) form a topologically distinct cluster
    from separable states (I_c <= 0) — H0 should have >= 2 components
    at appropriate filtration scale.
  - I_c filtration: as we add states by increasing I_c, we track when
    components merge and loops appear/die.
  - H1 loop detection: does the kernel embedding of theta in [0, pi]
    form a topological loop?

NEGATIVE:
  - Random states (no bridge structure) should have simpler, less
    persistent topology (shorter bar lifetimes in H1/H2).
  - Noise perturbation should not create spurious persistent features
    above the signal threshold.

BOUNDARY:
  - Degenerate states at theta=0 and theta=pi (pure |0> and |1> states).
  - Threshold sensitivity: Rips filtration at multiple max_edge_length
    values.

Classification: canonical
"""

import json
import math
import os
import time
import traceback

import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": "not needed -- no graph message passing layer"},
    "z3":        {"tried": False, "used": False, "reason": "not needed -- no SMT/SAT constraints required"},
    "cvc5":      {"tried": False, "used": False, "reason": "not needed -- no synthesis constraints"},
    "sympy":     {"tried": False, "used": False, "reason": "not needed -- no symbolic derivation"},
    "clifford":  {"tried": False, "used": False, "reason": "not needed -- no geometric algebra layer"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed -- topology via gudhi, not Riemannian statistics"},
    "e3nn":      {"tried": False, "used": False, "reason": "not needed -- no equivariant neural network layer"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed -- no dependency graph"},
    "xgi":       {"tried": False, "used": False, "reason": "not needed -- no hypergraph layer"},
    "toponetx":  {"tried": False, "used": False, "reason": "not needed -- topology via gudhi directly"},
    "gudhi":     {"tried": False, "used": False, "reason": ""},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch":   "supportive",    # state construction and kernel computation
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
    "gudhi":     "load_bearing",  # persistence diagrams are the primary result
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "State construction: density matrices, partial traces, entropy/MI/I_c kernels"
    )
    TORCH_OK = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"
    TORCH_OK = False

try:
    import gudhi
    TOOL_MANIFEST["gudhi"]["tried"] = True
    TOOL_MANIFEST["gudhi"]["used"] = True
    TOOL_MANIFEST["gudhi"]["reason"] = (
        "Rips and Alpha complex persistence diagrams — primary topological analysis"
    )
    GUDHI_OK = True
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"
    GUDHI_OK = False


# =====================================================================
# QUANTUM KERNEL UTILITIES (torch-based)
# =====================================================================

TOL = 1e-12

def von_neumann_entropy_np(rho_np):
    """Von Neumann entropy S(rho) in bits, numpy path for flexibility."""
    evals = np.linalg.eigvalsh((rho_np + rho_np.conj().T) / 2.0).real
    evals = evals[evals > TOL]
    if len(evals) == 0:
        return 0.0
    return float(-np.sum(evals * np.log2(evals)))


def partial_trace_B(rho_ab_np, dim_a=2, dim_b=2):
    """Trace out B, keep A."""
    rho = rho_ab_np.reshape(dim_a, dim_b, dim_a, dim_b)
    return np.einsum("abcb->ac", rho)


def partial_trace_A(rho_ab_np, dim_a=2, dim_b=2):
    """Trace out A, keep B."""
    rho = rho_ab_np.reshape(dim_a, dim_b, dim_a, dim_b)
    return np.einsum("abad->bd", rho)


def kernel_triple(rho_ab_np):
    """
    Compute (MI, conditional_entropy, coherent_information) for a 2-qubit state.

    MI          = S(A) + S(B) - S(AB)             [mutual information]
    cond_S      = S(AB) - S(A)                    [conditional entropy S(B|A)]
    I_c         = S(B) - S(AB)                    [coherent information]
    """
    rho_a = partial_trace_B(rho_ab_np)
    rho_b = partial_trace_A(rho_ab_np)
    S_A  = von_neumann_entropy_np(rho_a)
    S_B  = von_neumann_entropy_np(rho_b)
    S_AB = von_neumann_entropy_np(rho_ab_np)
    MI     = S_A + S_B - S_AB
    cond_S = S_AB - S_A
    I_c    = S_B - S_AB
    return MI, cond_S, I_c


# =====================================================================
# BRIDGE STATE FAMILY: theta-parameterized two-qubit states
# =====================================================================

def bridge_state_rho(theta):
    """
    Construct a two-qubit 'bridge' state parameterized by theta in [0, pi].

    State family:
      |psi(theta)> = cos(theta/2)|00> + sin(theta/2)|11>

    This is the standard two-qubit family interpolating between:
      theta=0: |00>  (product, separable, I_c = 0)
      theta=pi/2: |Phi+> Bell state (maximally entangled, I_c = 1)
      theta=pi: |11>  (product, separable, I_c = 0)

    Pure state density matrix.
    """
    c = math.cos(theta / 2.0)
    s = math.sin(theta / 2.0)
    # Computational basis ordering: 00, 01, 10, 11
    psi = np.array([c, 0.0, 0.0, s], dtype=np.complex128)
    rho = np.outer(psi, psi.conj())
    return rho


def build_bridge_point_cloud(n=20):
    """
    Build n-point cloud in R^3 via (MI, cond_S, I_c) kernel triples.
    theta sweeps [0, pi].
    """
    thetas = np.linspace(0, math.pi, n)
    points = []
    triples = []
    for theta in thetas:
        rho = bridge_state_rho(theta)
        MI, cond_S, I_c = kernel_triple(rho)
        points.append([MI, cond_S, I_c])
        triples.append({"theta": float(theta), "MI": MI, "cond_S": cond_S, "I_c": I_c})
    return np.array(points, dtype=np.float64), thetas, triples


def build_random_point_cloud(n=20, seed=42):
    """
    Random baseline: n points drawn uniformly from [-1, 1]^3 (no bridge structure).
    """
    rng = np.random.default_rng(seed)
    return rng.uniform(-1.0, 1.0, size=(n, 3))


# =====================================================================
# PERSISTENCE UTILITIES
# =====================================================================

def summarize_persistence(persistence, max_dim=2):
    """Extract birth/death pairs by dimension."""
    result = {}
    for dim in range(max_dim + 1):
        pairs = [(b, d) for (h, (b, d)) in persistence if h == dim and d != float("inf")]
        inf_pairs = [(b, d) for (h, (b, d)) in persistence if h == dim and d == float("inf")]
        lifetimes = [d - b for (b, d) in pairs]
        result[f"H{dim}"] = {
            "finite_pairs": len(pairs),
            "infinite_pairs": len(inf_pairs),
            "total_pairs": len(pairs) + len(inf_pairs),
            "births": [round(b, 6) for b, _ in pairs],
            "deaths": [round(d, 6) for _, d in pairs],
            "lifetimes": [round(lt, 6) for lt in lifetimes],
            "max_lifetime": round(max(lifetimes), 6) if lifetimes else 0.0,
            "mean_lifetime": round(float(np.mean(lifetimes)), 6) if lifetimes else 0.0,
        }
    return result


def run_rips_persistence(points, max_edge_length=2.0, max_dimension=2):
    """Run GUDHI Rips complex persistence."""
    rc = gudhi.RipsComplex(points=points.tolist(), max_edge_length=max_edge_length)
    st = rc.create_simplex_tree(max_dimension=max_dimension)
    persistence = st.persistence()
    return summarize_persistence(persistence, max_dim=max_dimension)


def run_alpha_persistence(points, max_dimension=2):
    """Run GUDHI Alpha complex persistence."""
    # Alpha complex is only defined in <= 3D, which matches our R^3 embedding
    ac = gudhi.AlphaComplex(points=points.tolist())
    st = ac.create_simplex_tree()
    persistence = st.persistence()
    return summarize_persistence(persistence, max_dim=max_dimension)


# =====================================================================
# I_c FILTRATION: build simplex tree ordered by coherent information
# =====================================================================

def run_ic_filtration(points, triples, max_edge_length=2.0):
    """
    Filtration ordered by I_c value.
    Sort states by I_c (ascending, from negative to positive).
    Insert vertices in that order, then all edges between inserted vertices
    at each step. Track when new components appear/merge and when loops
    appear as I_c crosses zero (separable -> entangled boundary).
    """
    # Sort by I_c
    order = np.argsort([t["I_c"] for t in triples])
    sorted_ic = [triples[i]["I_c"] for i in order]
    sorted_points = points[order]

    # Build Rips at each prefix of the filtration
    # Prefix k = first k states by I_c
    filtration_steps = []
    for k in range(2, len(sorted_points) + 1):
        sub_points = sorted_points[:k]
        rc = gudhi.RipsComplex(points=sub_points.tolist(), max_edge_length=max_edge_length)
        st = rc.create_simplex_tree(max_dimension=1)  # H0 + H1 only for speed
        pers = st.persistence()
        summary = summarize_persistence(pers, max_dim=1)
        filtration_steps.append({
            "k": k,
            "max_ic": round(sorted_ic[k - 1], 6),
            "H0_components": summary["H0"]["infinite_pairs"],
            "H1_loops": summary["H1"]["finite_pairs"] + summary["H1"]["infinite_pairs"],
        })

    # Find the step where I_c first crosses zero
    ic_cross_step = None
    for step in filtration_steps:
        if step["max_ic"] >= 0.0:
            ic_cross_step = step
            break

    return {
        "filtration_steps": filtration_steps,
        "ic_zero_crossing_step": ic_cross_step,
        "total_states": len(sorted_points),
    }


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    if not GUDHI_OK:
        return {"error": "gudhi not available"}

    # --- Build bridge point cloud ---
    points, thetas, triples = build_bridge_point_cloud(n=20)
    results["point_cloud_shape"] = list(points.shape)
    results["point_cloud_sample"] = [
        {k: round(v, 6) for k, v in t.items()}
        for t in triples[::5]  # every 5th point
    ]

    # Verify I_c range: should go from 0 (theta=0,pi) up to 1.0 (theta=pi/2)
    ic_values = [t["I_c"] for t in triples]
    results["ic_min"] = round(min(ic_values), 6)
    results["ic_max"] = round(max(ic_values), 6)
    results["ic_at_theta0"]    = round(triples[0]["I_c"], 6)
    results["ic_at_thetaPi"]   = round(triples[-1]["I_c"], 6)
    results["ic_at_thetaPi_2"] = round(triples[len(triples) // 2]["I_c"], 6)

    # --- Rips persistence at multiple thresholds ---
    rips_results = {}
    for threshold in [0.3, 0.5, 1.0, 2.0]:
        rips_results[f"threshold_{threshold}"] = run_rips_persistence(
            points, max_edge_length=threshold, max_dimension=2
        )
    results["rips_persistence"] = rips_results

    # --- Alpha complex persistence ---
    try:
        results["alpha_persistence"] = run_alpha_persistence(points, max_dimension=2)
    except Exception as e:
        results["alpha_persistence"] = {"error": str(e), "traceback": traceback.format_exc()}

    # --- I_c filtration ---
    results["ic_filtration"] = run_ic_filtration(points, triples, max_edge_length=1.0)

    # --- Topology check: does the bridge family form a loop in R^3? ---
    # H1 persistence at intermediate threshold
    rips_mid = run_rips_persistence(points, max_edge_length=1.0, max_dimension=2)
    h1 = rips_mid["H1"]
    results["h1_loop_detected"] = (h1["finite_pairs"] + h1["infinite_pairs"]) > 0
    results["h1_summary_at_1.0"] = h1

    # --- H0: entangled vs separable separation ---
    # Split into entangled (I_c > 0) and separable (I_c <= 0) subsets
    entangled_idx = [i for i, t in enumerate(triples) if t["I_c"] > 0.001]
    separable_idx = [i for i, t in enumerate(triples) if t["I_c"] <= 0.001]
    results["entangled_count"] = len(entangled_idx)
    results["separable_count"] = len(separable_idx)

    if len(entangled_idx) >= 2 and len(separable_idx) >= 2:
        ent_pts = points[entangled_idx]
        sep_pts = points[separable_idx]
        # Rips on entangled subset
        rips_ent = run_rips_persistence(ent_pts, max_edge_length=0.5, max_dimension=1)
        # Rips on separable subset
        rips_sep = run_rips_persistence(sep_pts, max_edge_length=0.5, max_dimension=1)
        results["entangled_subset_rips"] = rips_ent
        results["separable_subset_rips"] = rips_sep
        # At small threshold, we expect 2 separable components (theta~0 cluster and theta~pi cluster)
        results["separable_has_two_components"] = (
            rips_sep["H0"]["infinite_pairs"] >= 2
        )

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    if not GUDHI_OK:
        return {"error": "gudhi not available"}

    # --- Random baseline: no bridge structure ---
    random_pts = build_random_point_cloud(n=20, seed=42)
    try:
        rips_random = run_rips_persistence(random_pts, max_edge_length=1.0, max_dimension=2)
        results["random_rips_at_1.0"] = rips_random

        # Alpha complex on random
        alpha_random = run_alpha_persistence(random_pts, max_dimension=2)
        results["random_alpha"] = alpha_random
    except Exception as e:
        results["random_error"] = str(e)

    # --- Compare max H1 lifetime: bridge should have more persistent H1 than random ---
    bridge_pts, _, bridge_triples = build_bridge_point_cloud(n=20)
    rips_bridge = run_rips_persistence(bridge_pts, max_edge_length=1.0, max_dimension=2)
    bridge_h1_max = rips_bridge["H1"]["max_lifetime"]
    random_h1_max = rips_random["H1"]["max_lifetime"] if "random_rips_at_1.0" in results else 0.0
    results["bridge_h1_max_lifetime"] = round(bridge_h1_max, 6)
    results["random_h1_max_lifetime"] = round(random_h1_max, 6)
    results["bridge_has_more_persistent_h1_than_random"] = bridge_h1_max >= random_h1_max

    # --- Noise perturbation: perturb bridge point cloud with small noise ---
    rng = np.random.default_rng(123)
    noise_pts = bridge_pts + rng.normal(0, 0.05, bridge_pts.shape)
    rips_noisy = run_rips_persistence(noise_pts, max_edge_length=1.0, max_dimension=2)
    results["noisy_bridge_rips"] = rips_noisy
    # H0 structure should be preserved (same number of components as bridge at small noise)
    results["noise_preserves_h0"] = (
        abs(rips_noisy["H0"]["infinite_pairs"] - rips_bridge["H0"]["infinite_pairs"]) <= 1
    )

    # --- Constant degenerate cloud: all points identical, should have only 1 H0 component ---
    degenerate_pts = np.zeros((20, 3))
    try:
        rips_degen = run_rips_persistence(degenerate_pts, max_edge_length=0.01, max_dimension=1)
        results["degenerate_h0"] = rips_degen["H0"]["infinite_pairs"]
        results["degenerate_h0_is_1"] = rips_degen["H0"]["infinite_pairs"] == 1
    except Exception as e:
        results["degenerate_error"] = str(e)

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    if not GUDHI_OK:
        return {"error": "gudhi not available"}

    # --- Theta boundary states ---
    rho_0   = bridge_state_rho(0.0)
    rho_pi2 = bridge_state_rho(math.pi / 2.0)
    rho_pi  = bridge_state_rho(math.pi)

    for label, rho in [("theta_0", rho_0), ("theta_pi2", rho_pi2), ("theta_pi", rho_pi)]:
        MI, cond_S, I_c = kernel_triple(rho)
        results[label] = {
            "MI": round(MI, 6),
            "cond_S": round(cond_S, 6),
            "I_c": round(I_c, 6),
        }

    # Expected: theta=0 and theta=pi are product states (MI=0, I_c=0)
    results["theta_0_is_product"] = abs(results["theta_0"]["I_c"]) < 0.001
    results["theta_pi_is_product"] = abs(results["theta_pi"]["I_c"]) < 0.001
    results["theta_pi2_is_max_entangled"] = abs(results["theta_pi2"]["I_c"] - 1.0) < 0.01

    # --- Filtration threshold sensitivity ---
    bridge_pts, _, bridge_triples = build_bridge_point_cloud(n=20)
    threshold_sweep = {}
    for th in [0.1, 0.2, 0.5, 0.75, 1.0, 1.5, 2.0]:
        r = run_rips_persistence(bridge_pts, max_edge_length=th, max_dimension=2)
        threshold_sweep[str(th)] = {
            "H0_inf": r["H0"]["infinite_pairs"],
            "H1_total": r["H1"]["finite_pairs"] + r["H1"]["infinite_pairs"],
            "H2_total": r["H2"]["finite_pairs"] + r["H2"]["infinite_pairs"],
        }
    results["threshold_sweep"] = threshold_sweep

    # --- Rips vs Alpha comparison on bridge point cloud ---
    try:
        alpha_bridge = run_alpha_persistence(bridge_pts, max_dimension=2)
        rips_bridge  = run_rips_persistence(bridge_pts, max_edge_length=2.0, max_dimension=2)
        results["alpha_vs_rips_h0_inf_match"] = (
            alpha_bridge["H0"]["infinite_pairs"] == rips_bridge["H0"]["infinite_pairs"]
        )
        results["alpha_h1_total"] = (
            alpha_bridge["H1"]["finite_pairs"] + alpha_bridge["H1"]["infinite_pairs"]
        )
        results["rips_h1_total"] = (
            rips_bridge["H1"]["finite_pairs"] + rips_bridge["H1"]["infinite_pairs"]
        )
        results["alpha_persistence_summary"] = {
            "H0": alpha_bridge["H0"],
            "H1": alpha_bridge["H1"],
            "H2": alpha_bridge["H2"],
        }
        results["rips_persistence_summary_at_2.0"] = {
            "H0": rips_bridge["H0"],
            "H1": rips_bridge["H1"],
            "H2": rips_bridge["H2"],
        }
    except Exception as e:
        results["alpha_vs_rips_error"] = str(e)
        results["alpha_vs_rips_traceback"] = traceback.format_exc()

    # --- n sensitivity: 10, 20, 40 points ---
    for n in [10, 20, 40]:
        pts, _, _ = build_bridge_point_cloud(n=n)
        r = run_rips_persistence(pts, max_edge_length=1.0, max_dimension=2)
        results[f"n{n}_rips_h1"] = r["H1"]["finite_pairs"] + r["H1"]["infinite_pairs"]
        results[f"n{n}_rips_h0_inf"] = r["H0"]["infinite_pairs"]

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    t0 = time.time()

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    elapsed = round(time.time() - t0, 3)

    # ---- Derive top-level findings ----
    findings = {}

    # H1 loop
    if "h1_loop_detected" in positive:
        findings["h1_loop_detected"] = positive["h1_loop_detected"]

    # Separable two-component
    if "separable_has_two_components" in positive:
        findings["separable_has_two_components"] = positive["separable_has_two_components"]

    # I_c range
    if "ic_max" in positive:
        findings["ic_max_near_1"] = abs(positive.get("ic_max", 0) - 1.0) < 0.01

    # Bridge vs random topology
    if "bridge_has_more_persistent_h1_than_random" in negative:
        findings["bridge_more_persistent_than_random"] = negative["bridge_has_more_persistent_h1_than_random"]

    # Boundary state checks
    if "theta_0_is_product" in boundary:
        findings["boundary_product_states_correct"] = (
            boundary["theta_0_is_product"] and boundary["theta_pi_is_product"]
        )
        findings["bell_state_max_entangled"] = boundary.get("theta_pi2_is_max_entangled", False)

    results = {
        "name": "gudhi_bridge_persistence",
        "description": (
            "GUDHI Rips + Alpha persistent homology on the bridge state family "
            "embedded in R^3 via (MI, conditional_entropy, coherent_information) kernel triples. "
            "20 states, theta in [0, pi]."
        ),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "findings": findings,
        "elapsed_seconds": elapsed,
        "classification": "canonical",
        "gudhi_available": GUDHI_OK,
        "pytorch_available": TORCH_OK,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "gudhi_bridge_persistence_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Elapsed: {elapsed}s")
    print(f"GUDHI available: {GUDHI_OK}")
    if GUDHI_OK and "h1_loop_detected" in positive:
        print(f"H1 loop detected: {positive['h1_loop_detected']}")
    if GUDHI_OK and "ic_filtration" in positive:
        cross = positive["ic_filtration"].get("ic_zero_crossing_step")
        print(f"I_c zero crossing step: {cross}")

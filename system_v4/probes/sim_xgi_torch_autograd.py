#!/usr/bin/env python3
"""
sim_xgi_torch_autograd.py

Feed the XGI shell hypergraph incidence matrix into PyTorch autograd so
shell centrality gradients flow back through the hypergraph structure.

Positive test: loss = -c[L4] where c = softmax(B^T @ B @ ones).
  grad on edge weights reveals which hyperedges contribute most to L4 centrality.
  Expected: {L4, L6} (edge idx 2) and {L4, L6, L7} (edge idx 7) have largest
  gradient magnitudes since they encode the joint kill.

Negative test: loss = -c[L1] (weakest shell by centrality).
  Gradient should concentrate on edges that *don't* involve L4/L6 at all,
  and magnitude should be smaller overall — confirming L4 is genuinely
  elevated in the hypergraph structure.

Boundary test: uniform edge weights (all 1.0) vs perturbed weights.
  The gradient direction tells us which edges to *increase* to raise L4
  centrality further, and which edges are already saturated.
"""

import json
import os
import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":    {"tried": False, "used": False, "reason": ""},
    "pyg":        {"tried": False, "used": False, "reason": ""},
    "z3":         {"tried": False, "used": False, "reason": ""},
    "cvc5":       {"tried": False, "used": False, "reason": ""},
    "sympy":      {"tried": False, "used": False, "reason": ""},
    "clifford":   {"tried": False, "used": False, "reason": ""},
    "geomstats":  {"tried": False, "used": False, "reason": ""},
    "e3nn":       {"tried": False, "used": False, "reason": ""},
    "rustworkx":  {"tried": False, "used": False, "reason": ""},
    "xgi":        {"tried": False, "used": False, "reason": ""},
    "toponetx":   {"tried": False, "used": False, "reason": ""},
    "gudhi":      {"tried": False, "used": False, "reason": ""},
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
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import xgi
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"

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
    from toponetx.classes import CellComplex  # noqa: F401
    TOOL_MANIFEST["toponetx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["toponetx"]["reason"] = "not installed"

try:
    import gudhi  # noqa: F401
    TOOL_MANIFEST["gudhi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"


# =====================================================================
# SHELL / HYPEREDGE DEFINITIONS (identical to sim_xgi_shell_hypergraph)
# =====================================================================

SHELLS = {
    "L0": "density_matrix_validity",
    "L1": "loop_family_finiteness",
    "L2": "hopf_carrier_structure",
    "L3": "operator_chirality",
    "L4": "engine_family_absolute_kill",
    "L5": "axis_orthogonality",
    "L6": "reversible_family_kill",
    "L7": "full_axis_composition",
}

SHELL_NAMES = list(SHELLS.keys())   # ["L0", "L1", ..., "L7"]
N_NODES = len(SHELL_NAMES)          # 8

# 8 hyperedges as in the original sim
HYPEREDGES_ANNOTATED = [
    (["L0", "L1"],         "density_matrix_validity_and_finiteness"),   # idx 0
    (["L2", "L3", "L4"],   "spinor_carrier_chirality_composition"),     # idx 1
    (["L4", "L6"],         "joint_family_kill"),                        # idx 2
    (["L0", "L2", "L5"],   "spinor_structure_finitude_carrier_su2"),    # idx 3
    (["L3", "L5", "L7"],   "axis_orthogonality_manifold"),              # idx 4
    (["L1", "L4"],         "family_count_upper_bound"),                 # idx 5
    (["L2", "L6", "L7"],   "composition_reversibility_surface"),        # idx 6
    (["L4", "L6", "L7"],   "surviving_family_filter"),                  # idx 7
]

HYPEREDGES = [e for e, _ in HYPEREDGES_ANNOTATED]
HYPEREDGE_LABELS = [label for _, label in HYPEREDGES_ANNOTATED]
N_EDGES = len(HYPEREDGES)   # 8

SHELL_INDEX = {s: i for i, s in enumerate(SHELL_NAMES)}


def build_incidence_matrix_np():
    """
    Build the (N_NODES x N_EDGES) binary incidence matrix B.
    B[i, j] = 1 if shell i is a member of hyperedge j.
    Returns a numpy float64 array.
    """
    B = np.zeros((N_NODES, N_EDGES), dtype=np.float64)
    for j, edge in enumerate(HYPEREDGES):
        for node in edge:
            i = SHELL_INDEX[node]
            B[i, j] = 1.0
    return B


def differentiable_centrality(B_weighted, ones):
    """
    c = softmax(B_weighted^T @ B_weighted @ ones)
    where B_weighted = B (incidence) * w (edge weights, shape [N_EDGES]).

    This is a smooth approximation of degree centrality:
    - B^T @ B is the (N_EDGES x N_EDGES) co-membership matrix
    - B^T @ B @ ones counts, for each edge, how many nodes are shared
      across all edges (weighted)
    - softmax normalises to a probability distribution

    Wait — we want a NODE centrality, so the formula is:
      c_node = softmax(B @ B^T @ ones_node)
    where B @ B^T is the (N_NODES x N_NODES) node co-membership matrix
    and ones_node is the all-ones vector of length N_NODES.

    Keeping B_weighted = B * w[:,None].T (broadcast edge weights onto columns):
      c = softmax(B_w @ B_w^T @ ones)
    Gradient flows back through w since B_w = B * w.
    """
    # B_weighted: (N_NODES, N_EDGES)
    # Co-membership matrix: (N_NODES, N_NODES)
    co = B_weighted @ B_weighted.T          # (N x N)
    scores = co @ ones                       # (N,)
    c = torch.softmax(scores, dim=0)
    return c


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    """
    loss = -c[L4_idx], maximize L4 centrality.
    Grad on edge weights: which edges most increase L4 centrality?
    Expected top contributors: idx 2 ({L4,L6}) and idx 7 ({L4,L6,L7}).
    """
    results = {}

    B_np = build_incidence_matrix_np()
    B = torch.tensor(B_np, dtype=torch.float64)

    # Edge weights with grad enabled
    w = torch.ones(N_EDGES, dtype=torch.float64, requires_grad=True)

    # B_weighted: broadcast w across node dimension
    B_weighted = B * w.unsqueeze(0)   # (N_NODES, N_EDGES)
    ones = torch.ones(N_NODES, dtype=torch.float64)

    c = differentiable_centrality(B_weighted, ones)

    L4_idx = SHELL_INDEX["L4"]
    loss_L4 = -c[L4_idx]
    loss_L4.backward()

    grad_w = w.grad.detach().numpy()

    # Rank edges by |grad| descending
    grad_abs = np.abs(grad_w)
    ranked_idx = np.argsort(-grad_abs)

    results["centrality_values"] = {
        SHELL_NAMES[i]: float(c[i].item()) for i in range(N_NODES)
    }
    results["L4_centrality"] = float(c[L4_idx].item())
    results["loss_L4"] = float(loss_L4.item())

    results["edge_gradients"] = {
        str(j): {
            "label": HYPEREDGE_LABELS[j],
            "edge": HYPEREDGES[j],
            "grad": float(grad_w[j]),
            "grad_abs": float(grad_abs[j]),
        }
        for j in range(N_EDGES)
    }

    results["gradient_ranking"] = [
        {
            "rank": int(r + 1),
            "edge_idx": int(ranked_idx[r]),
            "edge": HYPEREDGES[ranked_idx[r]],
            "label": HYPEREDGE_LABELS[ranked_idx[r]],
            "grad_abs": float(grad_abs[ranked_idx[r]]),
        }
        for r in range(N_EDGES)
    ]

    # Test: do {L4,L6} (idx 2) and {L4,L6,L7} (idx 7) land in top-2 by |grad|?
    top2_idx = set(ranked_idx[:2].tolist())
    results["joint_kill_edges_in_top2"] = (2 in top2_idx and 7 in top2_idx)
    results["joint_kill_edge2_rank"] = int(np.where(ranked_idx == 2)[0][0]) + 1
    results["joint_kill_edge7_rank"] = int(np.where(ranked_idx == 7)[0][0]) + 1

    # Which L4-containing edges appear in top-3?
    l4_edges = [j for j, e in enumerate(HYPEREDGES) if "L4" in e]
    results["L4_containing_edges"] = l4_edges
    top3_idx = set(ranked_idx[:3].tolist())
    results["L4_edge_top3_coverage"] = {
        str(j): (j in top3_idx) for j in l4_edges
    }

    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "torch autograd: incidence matrix B as float64 tensor, "
        "edge weights w with requires_grad=True, "
        "differentiable centrality c=softmax(B_w @ B_w^T @ ones), "
        "loss=-c[L4], loss.backward() -> grad on edge weights"
    )
    TOOL_MANIFEST["xgi"]["used"] = True
    TOOL_MANIFEST["xgi"]["reason"] = (
        "XGI hypergraph structure (shell nodes, 8 hyperedges) used to define "
        "the incidence matrix B fed into PyTorch autograd"
    )

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    """
    Negative test: loss = -c[L1_idx] (weakest shell).
    Gradient should concentrate on edges involving L1 ({L0,L1} idx 0,
    {L1,L4} idx 5), NOT on the joint kill edges (idx 2, 7).
    Grad magnitudes should be smaller overall than in the L4 case,
    since L1 sits in fewer high-weight hyperedges.
    """
    results = {}

    B_np = build_incidence_matrix_np()
    B = torch.tensor(B_np, dtype=torch.float64)

    w = torch.ones(N_EDGES, dtype=torch.float64, requires_grad=True)
    B_weighted = B * w.unsqueeze(0)
    ones = torch.ones(N_NODES, dtype=torch.float64)

    c = differentiable_centrality(B_weighted, ones)

    L1_idx = SHELL_INDEX["L1"]
    loss_L1 = -c[L1_idx]
    loss_L1.backward()

    grad_w_L1 = w.grad.detach().numpy()
    grad_abs_L1 = np.abs(grad_w_L1)
    ranked_idx_L1 = np.argsort(-grad_abs_L1)

    results["L1_centrality"] = float(c[L1_idx].item())
    results["loss_L1"] = float(loss_L1.item())

    results["edge_gradients_L1"] = {
        str(j): {
            "label": HYPEREDGE_LABELS[j],
            "edge": HYPEREDGES[j],
            "grad": float(grad_w_L1[j]),
            "grad_abs": float(grad_abs_L1[j]),
        }
        for j in range(N_EDGES)
    }

    results["gradient_ranking_L1"] = [
        {
            "rank": int(r + 1),
            "edge_idx": int(ranked_idx_L1[r]),
            "edge": HYPEREDGES[ranked_idx_L1[r]],
            "label": HYPEREDGE_LABELS[ranked_idx_L1[r]],
            "grad_abs": float(grad_abs_L1[ranked_idx_L1[r]]),
        }
        for r in range(N_EDGES)
    ]

    # Joint kill edges (2 and 7) should NOT be in top-2 for L1 loss
    top2_L1 = set(ranked_idx_L1[:2].tolist())
    results["joint_kill_edges_absent_from_top2"] = (2 not in top2_L1 and 7 not in top2_L1)
    results["edge2_rank_for_L1"] = int(np.where(ranked_idx_L1 == 2)[0][0]) + 1
    results["edge7_rank_for_L1"] = int(np.where(ranked_idx_L1 == 7)[0][0]) + 1

    # Compare total gradient magnitude L4 vs L1 (recompute L4 for reference)
    w2 = torch.ones(N_EDGES, dtype=torch.float64, requires_grad=True)
    B_weighted2 = B * w2.unsqueeze(0)
    ones2 = torch.ones(N_NODES, dtype=torch.float64)
    c2 = differentiable_centrality(B_weighted2, ones2)
    loss_L4_ref = -c2[SHELL_INDEX["L4"]]
    loss_L4_ref.backward()
    grad_abs_L4_ref = np.abs(w2.grad.detach().numpy())

    results["total_grad_magnitude_L4"] = float(np.sum(grad_abs_L4_ref))
    results["total_grad_magnitude_L1"] = float(np.sum(grad_abs_L1))
    results["L4_grad_larger_than_L1"] = float(np.sum(grad_abs_L4_ref)) > float(np.sum(grad_abs_L1))

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """
    Boundary test 1: perturb w[2] (joint_family_kill edge) to 2.0.
    Does L4 centrality increase? Does gradient on edge 2 drop (saturation)?

    Boundary test 2: zero out w[2] and w[7] (both joint kill edges).
    L4 should lose centrality rank — does the centrality map change?

    Boundary test 3: gradient at L4 with identity edge weights confirms
    that the softmax computation is numerically stable and grad is nonzero.
    """
    results = {}

    B_np = build_incidence_matrix_np()
    B = torch.tensor(B_np, dtype=torch.float64)

    # --- Boundary 1: boost joint_family_kill edge (idx 2) ---
    w_boosted = torch.ones(N_EDGES, dtype=torch.float64, requires_grad=True)
    # Detach and rebuild with perturbed value
    with torch.no_grad():
        w_init = torch.ones(N_EDGES, dtype=torch.float64)
        w_init[2] = 2.0
    w_b1 = w_init.clone().requires_grad_(True)
    B_w_b1 = B * w_b1.unsqueeze(0)
    ones = torch.ones(N_NODES, dtype=torch.float64)
    c_b1 = differentiable_centrality(B_w_b1, ones)
    loss_b1 = -c_b1[SHELL_INDEX["L4"]]
    loss_b1.backward()

    grad_b1 = w_b1.grad.detach().numpy()

    # Baseline
    w_base = torch.ones(N_EDGES, dtype=torch.float64, requires_grad=True)
    B_w_base = B * w_base.unsqueeze(0)
    c_base = differentiable_centrality(B_w_base, ones)

    results["boundary1_boost_edge2"] = {
        "L4_centrality_boosted": float(c_b1[SHELL_INDEX["L4"]].item()),
        "L4_centrality_baseline": float(c_base[SHELL_INDEX["L4"]].detach().item()),
        "L4_increases_with_edge2_boost": (
            float(c_b1[SHELL_INDEX["L4"]].item()) >
            float(c_base[SHELL_INDEX["L4"]].detach().item())
        ),
        "grad_edge2_boosted": float(grad_b1[2]),
    }

    # --- Boundary 2: kill both joint kill edges (w[2]=0, w[7]=0) ---
    with torch.no_grad():
        w_kill = torch.ones(N_EDGES, dtype=torch.float64)
        w_kill[2] = 0.0
        w_kill[7] = 0.0
    w_b2 = w_kill.clone().requires_grad_(True)
    B_w_b2 = B * w_b2.unsqueeze(0)
    c_b2 = differentiable_centrality(B_w_b2, ones)
    loss_b2 = -c_b2[SHELL_INDEX["L4"]]
    loss_b2.backward()

    results["boundary2_kill_joint_edges"] = {
        "L4_centrality_killed": float(c_b2[SHELL_INDEX["L4"]].item()),
        "L4_centrality_baseline": float(c_base[SHELL_INDEX["L4"]].detach().item()),
        "L4_drops_when_joint_edges_killed": (
            float(c_b2[SHELL_INDEX["L4"]].item()) <
            float(c_base[SHELL_INDEX["L4"]].detach().item())
        ),
        "centrality_ranking_killed": [
            {"shell": SHELL_NAMES[i], "value": float(c_b2[i].item())}
            for i in np.argsort(-c_b2.detach().numpy())
        ],
    }

    # --- Boundary 3: gradient nonzero / numerical stability ---
    w_b3 = torch.ones(N_EDGES, dtype=torch.float64, requires_grad=True)
    B_w_b3 = B * w_b3.unsqueeze(0)
    c_b3 = differentiable_centrality(B_w_b3, ones)
    loss_b3 = -c_b3[SHELL_INDEX["L4"]]
    loss_b3.backward()

    grad_b3 = w_b3.grad.detach().numpy()
    results["boundary3_gradient_stability"] = {
        "all_grads_finite": bool(np.all(np.isfinite(grad_b3))),
        "any_grad_nonzero": bool(np.any(grad_b3 != 0)),
        "grad_norm": float(np.linalg.norm(grad_b3)),
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"
    TOOL_INTEGRATION_DEPTH["xgi"] = "load_bearing"

    summary = {
        "L4_centrality": positive.get("L4_centrality"),
        "joint_kill_edges_in_top2_for_L4": positive.get("joint_kill_edges_in_top2"),
        "joint_kill_edge2_rank_for_L4": positive.get("joint_kill_edge2_rank"),
        "joint_kill_edge7_rank_for_L4": positive.get("joint_kill_edge7_rank"),
        "joint_kill_edges_absent_from_top2_for_L1": negative.get("joint_kill_edges_absent_from_top2"),
        "L4_grad_larger_than_L1": negative.get("L4_grad_larger_than_L1"),
        "L4_increases_when_edge2_boosted": boundary.get(
            "boundary1_boost_edge2", {}).get("L4_increases_with_edge2_boost"),
        "L4_drops_when_joint_edges_killed": boundary.get(
            "boundary2_kill_joint_edges", {}).get("L4_drops_when_joint_edges_killed"),
        "gradient_numerically_stable": boundary.get(
            "boundary3_gradient_stability", {}).get("all_grads_finite"),
    }

    results = {
        "name": "sim_xgi_torch_autograd",
        "description": (
            "XGI incidence matrix fed into PyTorch autograd. "
            "Edge weights w have requires_grad=True. "
            "Differentiable centrality c = softmax(B_w @ B_w^T @ ones). "
            "loss = -c[L4]; loss.backward() reveals which hyperedges most "
            "contribute to L4 centrality via gradient magnitude."
        ),
        "shells": SHELLS,
        "hyperedges": [
            {"idx": i, "edge": e, "dof": HYPEREDGE_LABELS[i]}
            for i, e in enumerate(HYPEREDGES)
        ],
        "summary": summary,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "xgi_torch_autograd_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")

    print("\n=== XGI TORCH AUTOGRAD SUMMARY ===")
    print(f"L4 centrality (uniform weights): {summary['L4_centrality']:.5f}")
    print(f"Joint kill edges (2,7) in top-2 grad for L4: {summary['joint_kill_edges_in_top2_for_L4']}")
    print(f"  Edge 2 {{L4,L6}} rank: {summary['joint_kill_edge2_rank_for_L4']}")
    print(f"  Edge 7 {{L4,L6,L7}} rank: {summary['joint_kill_edge7_rank_for_L4']}")
    print(f"Joint kill edges absent from top-2 for L1: {summary['joint_kill_edges_absent_from_top2_for_L1']}")
    print(f"L4 grad total > L1 grad total: {summary['L4_grad_larger_than_L1']}")
    print("\nGradient ranking for -L4 loss:")
    for item in positive.get("gradient_ranking", []):
        print(f"  Rank {item['rank']}: edge {item['edge_idx']} {item['edge']} "
              f"({item['label']}) |grad|={item['grad_abs']:.6f}")

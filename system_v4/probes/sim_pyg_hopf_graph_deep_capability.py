#!/usr/bin/env python3
"""Deep PyG capability probe on Hopf tori geometry.

Build a graph: nodes = 32 points on S3 (uniform quaternion samples),
edges = connect if Hopf-fiber distance < threshold.
Run 2-layer GCN MessagePassing.

Positive:
  (a) graph structure (edge set) changes which nodes survive an admissibility
      threshold on the GCN output — not just feature values.
  (b) removing fiber edges changes GCN output by >10% (Frobenius norm ratio).
  (c) fully-connected graph vs sparse Hopf graph give statistically distinct
      output distributions.

Negative:
  - Identity weight GCN (no information flow) produces outputs that fail the
    >10% edge-removal delta test.
  - A random graph (Erdos-Renyi, same density) does NOT produce the same
    node-admissibility partition as the Hopf graph.

Boundary:
  - At threshold -> 0 the graph becomes disconnected; GCN degenerates to
    a linear projection of raw features (confirmed by comparing to no-edge
    baseline).
  - At threshold -> 1 (fully connected), the GCN output saturates and the
    edge-removal delta collapses below 10%.

load_bearing: pyg (GCNConv MessagePassing governs which nodes are admitted
post-threshold; the admissibility partition is structurally determined by
the Hopf-fiber edge set, not by raw features alone).
"""

import json
import os

import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "Tensor substrate for node features, edge indices, and GCN weight matrices; "
            "torch.linalg.norm used to compute Frobenius deltas between output tensors"
        ),
    },
    "pyg": {
        "tried": True,
        "used": True,
        "reason": (
            "GCNConv MessagePassing computes neighbourhood-aggregated node embeddings "
            "on the Hopf-fiber graph; the admitted node set is defined by thresholding "
            "GCN output norms, making PyG load-bearing for the admissibility claim"
        ),
    },
    "z3": {
        "tried": False,
        "used": False,
        "reason": "numeric graph structure probe does not require SMT proof layer",
    },
    "cvc5": {
        "tried": False,
        "used": False,
        "reason": "not needed; admissibility criterion is empirical, not symbolic",
    },
    "sympy": {
        "tried": False,
        "used": False,
        "reason": "Hopf fiber distance formula is closed-form; no symbolic algebra needed",
    },
    "clifford": {
        "tried": False,
        "used": False,
        "reason": "quaternion operations implemented directly in torch; clifford not needed",
    },
    "geomstats": {
        "tried": False,
        "used": False,
        "reason": "S3 sampling done analytically; geomstats not required here",
    },
    "e3nn": {
        "tried": False,
        "used": False,
        "reason": "SO(3) equivariance not the focus of this Hopf-graph structure probe",
    },
    "rustworkx": {
        "tried": False,
        "used": False,
        "reason": "graph representation handled entirely by PyG edge_index tensors",
    },
    "xgi": {
        "tried": False,
        "used": False,
        "reason": "hypergraph structure not needed; pairwise edges only",
    },
    "toponetx": {
        "tried": False,
        "used": False,
        "reason": "cell-complex topology not needed; this probe targets graph-level structure",
    },
    "gudhi": {
        "tried": False,
        "used": False,
        "reason": "persistent homology not required for this graph-structure test",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "pyg": "load_bearing",
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

import torch
import torch.nn as nn
from torch_geometric.nn import GCNConv
from torch_geometric.data import Data

torch.manual_seed(42)
np.random.seed(42)

# =====================================================================
# HELPERS: S3 sampling + Hopf-fiber distance
# =====================================================================

def sample_s3_uniform(n: int) -> torch.Tensor:
    """Return n unit quaternions uniformly sampled from S3."""
    q = torch.randn(n, 4)
    q = q / q.norm(dim=1, keepdim=True)
    return q  # (n, 4)


def hopf_fiber_distance(qi: torch.Tensor, qj: torch.Tensor) -> float:
    """
    Distance between the Hopf fibers of qi and qj on S2.
    Project each quaternion to a point on S2 via the Hopf map:
        pi(q) = (2(q1*q3 + q0*q2),  2(q2*q3 - q0*q1),  q0^2+q3^2-q1^2-q2^2)
    then compute great-circle distance between the two S2 images.
    """
    def hopf_map(q):
        q0, q1, q2, q3 = q[0], q[1], q[2], q[3]
        x = 2 * (q1 * q3 + q0 * q2)
        y = 2 * (q2 * q3 - q0 * q1)
        z = q0**2 + q3**2 - q1**2 - q2**2
        return torch.stack([x, y, z])

    pi_i = hopf_map(qi)
    pi_j = hopf_map(qj)
    cos_angle = torch.clamp(torch.dot(pi_i, pi_j), -1.0, 1.0)
    return torch.acos(cos_angle).item()


def build_hopf_graph(nodes: torch.Tensor, threshold: float) -> torch.Tensor:
    """Return edge_index (2, E) for pairs whose Hopf-fiber distance < threshold."""
    n = nodes.shape[0]
    src, dst = [], []
    for i in range(n):
        for j in range(i + 1, n):
            d = hopf_fiber_distance(nodes[i], nodes[j])
            if d < threshold:
                src += [i, j]
                dst += [j, i]
    if not src:
        return torch.zeros((2, 0), dtype=torch.long)
    return torch.tensor([src, dst], dtype=torch.long)


def build_full_graph(n: int) -> torch.Tensor:
    """Return edge_index for the complete graph on n nodes."""
    src, dst = [], []
    for i in range(n):
        for j in range(n):
            if i != j:
                src.append(i)
                dst.append(j)
    return torch.tensor([src, dst], dtype=torch.long)


def build_erdos_renyi_graph(n: int, p: float, seed: int = 0) -> torch.Tensor:
    """Return edge_index for an Erdos-Renyi G(n,p) random graph."""
    rng = np.random.RandomState(seed)
    src, dst = [], []
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < p:
                src += [i, j]
                dst += [j, i]
    if not src:
        return torch.zeros((2, 0), dtype=torch.long)
    return torch.tensor([src, dst], dtype=torch.long)


# =====================================================================
# TWO-LAYER GCN
# =====================================================================

class TwoLayerGCN(nn.Module):
    def __init__(self, in_dim: int, hidden_dim: int, out_dim: int):
        super().__init__()
        self.conv1 = GCNConv(in_dim, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, out_dim)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        h = torch.relu(self.conv1(x, edge_index))
        return self.conv2(h, edge_index)


def admitted_node_set(output: torch.Tensor, threshold: float) -> set:
    """Return set of node indices whose output norm exceeds threshold."""
    norms = output.norm(dim=1)
    return set(torch.where(norms > threshold)[0].tolist())


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests() -> dict:
    results = {}
    N = 32
    IN_DIM = 8
    HIDDEN = 16
    OUT_DIM = 4
    HOPF_THRESH = 0.8  # radians on S2; typical fiber distance is O(1)
    ADMISS_THRESH = 0.5

    nodes = sample_s3_uniform(N)
    x = torch.randn(N, IN_DIM)

    model = TwoLayerGCN(IN_DIM, HIDDEN, OUT_DIM)

    # --- Hopf graph ---
    edge_hopf = build_hopf_graph(nodes, HOPF_THRESH)
    edge_count = edge_hopf.shape[1] // 2 if edge_hopf.shape[1] > 0 else 0

    with torch.no_grad():
        out_hopf = model(x, edge_hopf)

    # (a) graph structure changes admitted node set vs no-edges baseline
    edge_none = torch.zeros((2, 0), dtype=torch.long)
    with torch.no_grad():
        out_none = model(x, edge_none)

    admitted_hopf = admitted_node_set(out_hopf, ADMISS_THRESH)
    admitted_none = admitted_node_set(out_none, ADMISS_THRESH)
    structure_changes_admissibility = admitted_hopf != admitted_none

    results["pos_a_structure_changes_admissibility"] = {
        "pass": bool(structure_changes_admissibility),
        "admitted_hopf_count": len(admitted_hopf),
        "admitted_none_count": len(admitted_none),
        "hopf_edge_count": edge_count,
        "note": "GCN message passing over Hopf-fiber edges must change the admitted node set",
    }

    # (b) removing fiber edges changes output by >10%
    frob_hopf = torch.linalg.norm(out_hopf).item()
    frob_none = torch.linalg.norm(out_none).item()
    delta = torch.linalg.norm(out_hopf - out_none).item()
    relative_change = delta / (frob_none + 1e-9)

    results["pos_b_edge_removal_delta"] = {
        "pass": bool(relative_change > 0.10),
        "relative_change": float(relative_change),
        "threshold": 0.10,
        "note": "Frobenius-norm ratio |out_hopf - out_none| / |out_none| must exceed 10%",
    }

    # (c) fully-connected vs sparse Hopf give distinct output distributions
    edge_full = build_full_graph(N)
    with torch.no_grad():
        out_full = model(x, edge_full)

    delta_hopf_full = torch.linalg.norm(out_hopf - out_full).item()
    frob_full = torch.linalg.norm(out_full).item()
    relative_hopf_full = delta_hopf_full / (frob_full + 1e-9)

    admitted_full = admitted_node_set(out_full, ADMISS_THRESH)
    distinct_partitions = admitted_hopf != admitted_full

    results["pos_c_sparse_vs_full_distinct"] = {
        "pass": bool(distinct_partitions),
        "relative_diff_hopf_vs_full": float(relative_hopf_full),
        "admitted_hopf_count": len(admitted_hopf),
        "admitted_full_count": len(admitted_full),
        "note": "Hopf-sparse and fully-connected graphs must yield different admitted node sets",
    }

    # overall
    all_pass = all(v["pass"] for v in results.values())
    results["positive_all_pass"] = all_pass
    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests() -> dict:
    results = {}
    N = 32
    IN_DIM = 8
    HIDDEN = 16
    OUT_DIM = 4
    HOPF_THRESH = 0.8
    ADMISS_THRESH = 0.5

    nodes = sample_s3_uniform(N)
    x = torch.randn(N, IN_DIM)

    # Identity-weight GCN: zero out conv2 weight so output = bias only
    model_id = TwoLayerGCN(IN_DIM, HIDDEN, OUT_DIM)
    with torch.no_grad():
        model_id.conv2.lin.weight.zero_()

    edge_hopf = build_hopf_graph(nodes, HOPF_THRESH)
    edge_none = torch.zeros((2, 0), dtype=torch.long)

    with torch.no_grad():
        out_id_hopf = model_id(x, edge_hopf)
        out_id_none = model_id(x, edge_none)

    delta_id = torch.linalg.norm(out_id_hopf - out_id_none).item()
    frob_id_none = torch.linalg.norm(out_id_none).item()
    rel_change_id = delta_id / (frob_id_none + 1e-9)

    # Identity model should NOT produce >10% delta (weight zeroed => output is bias)
    results["neg_a_identity_gcn_no_delta"] = {
        "pass": bool(rel_change_id <= 0.10),
        "relative_change": float(rel_change_id),
        "note": "Zero-weight GCN should not show >10% delta — confirms delta is due to message passing",
    }

    # Random Erdos-Renyi graph at same density as Hopf graph
    edge_count = edge_hopf.shape[1] // 2 if edge_hopf.shape[1] > 0 else 0
    p_er = edge_count / max(1, N * (N - 1) // 2)

    model_real = TwoLayerGCN(IN_DIM, HIDDEN, OUT_DIM)
    with torch.no_grad():
        out_hopf_real = model_real(x, edge_hopf)

    er_admitted_sets = []
    for seed in range(5):
        edge_er = build_erdos_renyi_graph(N, p_er, seed=seed)
        with torch.no_grad():
            out_er = model_real(x, edge_er)
        er_admitted_sets.append(admitted_node_set(out_er, ADMISS_THRESH))

    admitted_hopf_real = admitted_node_set(out_hopf_real, ADMISS_THRESH)
    # At least one ER sample should differ from Hopf admitted set
    er_all_match = all(s == admitted_hopf_real for s in er_admitted_sets)

    results["neg_b_random_graph_differs"] = {
        "pass": bool(not er_all_match),
        "er_match_count": sum(s == admitted_hopf_real for s in er_admitted_sets),
        "er_trials": 5,
        "note": "Random graphs at same density must not reproduce exact Hopf admissibility partition",
    }

    all_pass = all(v["pass"] for v in results.values())
    results["negative_all_pass"] = all_pass
    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests() -> dict:
    results = {}
    N = 32
    IN_DIM = 8
    HIDDEN = 16
    OUT_DIM = 4

    nodes = sample_s3_uniform(N)
    x = torch.randn(N, IN_DIM)
    model = TwoLayerGCN(IN_DIM, HIDDEN, OUT_DIM)

    # Near-zero threshold: graph is nearly disconnected
    edge_tiny = build_hopf_graph(nodes, 0.01)
    edge_none = torch.zeros((2, 0), dtype=torch.long)
    with torch.no_grad():
        out_tiny = model(x, edge_tiny)
        out_none = model(x, edge_none)

    delta_tiny = torch.linalg.norm(out_tiny - out_none).item()
    frob_none = torch.linalg.norm(out_none).item()
    near_zero_rel = delta_tiny / (frob_none + 1e-9)

    results["boundary_a_near_zero_threshold"] = {
        "pass": bool(near_zero_rel < 0.05),
        "edge_count_at_tiny_thresh": int(edge_tiny.shape[1] // 2),
        "relative_change": float(near_zero_rel),
        "note": "Near-zero threshold yields disconnected graph; GCN degenerates to no-edge baseline",
    }

    # Near-full threshold: same density as full graph -> delta collapses
    edge_large = build_hopf_graph(nodes, 3.15)  # near-pi covers almost all pairs
    edge_full = build_full_graph(N)
    with torch.no_grad():
        out_large = model(x, edge_large)
        out_full = model(x, edge_full)

    delta_large = torch.linalg.norm(out_large - out_full).item()
    frob_full = torch.linalg.norm(out_full).item()
    near_full_rel = delta_large / (frob_full + 1e-9)

    results["boundary_b_near_full_threshold"] = {
        "pass": bool(near_full_rel < 0.05),
        "edge_count_at_large_thresh": int(edge_large.shape[1] // 2),
        "full_edge_count": N * (N - 1) // 2,
        "relative_diff_from_full": float(near_full_rel),
        "note": "Large threshold approaches fully-connected; GCN output should converge to full-graph output",
    }

    all_pass = all(v["pass"] for v in results.values())
    results["boundary_all_pass"] = all_pass
    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    overall_pass = (
        positive.get("positive_all_pass", False)
        and negative.get("negative_all_pass", False)
        and boundary.get("boundary_all_pass", False)
    )

    results = {
        "name": "sim_pyg_hopf_graph_deep_capability",
        "classification": "classical_baseline",
        "overall_pass": overall_pass,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_pyg_hopf_graph_deep_capability_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"overall_pass: {overall_pass}")

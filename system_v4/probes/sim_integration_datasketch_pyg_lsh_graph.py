#!/usr/bin/env python3
"""
SIM INTEGRATION: datasketch MinHashLSH + PyG MessagePassing Graph
==================================================================
Coupling: datasketch MinHash LSH determines graph edges; PyG MessagePassing
propagates features over the resulting graph.

Lego domain: sim-verdict signature similarity graph.

Each node represents a simulated "verdict signature" -- a frozenset of
symbolic tokens drawn from a fixed vocabulary (e.g., "PASS", "FAIL",
"CANONICAL", "EXCLUDED", "STABLE", "BOUNDARY"). The signature models
what a sim verdict looks like as a bag-of-tokens.

Pipeline:
  1. Build N=10 node signatures (each is a set of tokens from vocabulary).
  2. Compute MinHash (128 permutations) for each signature via datasketch.
  3. Insert into MinHashLSH with threshold=0.3 (Jaccard similarity gate).
  4. Query each node's neighbors => adjacency list => PyG edge_index.
  5. Initialize node features: one-hot over vocabulary membership (dim=6).
  6. Run 1-layer PyG MessagePassing (mean aggregation) over the LSH graph.
  7. Compare post-MP features to pre-MP features.

Claims:
  1. LSH graph connectivity differs from a zero-edge (empty) graph:
     at least 1 edge exists (datasketch found at least one similar pair).
  2. MessagePassing changes at least one node's feature vector
     (post-MP != pre-MP for at least one node with a neighbor).
  3. LSH graph is NOT fully connected (not all N*(N-1)/2 pairs are edges):
     the Jaccard threshold filters some dissimilar pairs.
  Both datasketch (load_bearing for edge construction) and pyg
  (load_bearing for feature propagation) are required.

classification="canonical"
"""

import json
import os
import time

import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": True,  "used": True,
                  "reason": "load_bearing via PyG: PyG MessagePassing requires torch tensors "
                             "for edge_index and node feature matrices; all feature propagation "
                             "runs through torch.Tensor operations inside the MessagePassing layer"},
    "pyg":       {"tried": True,  "used": True,
                  "reason": "load_bearing: PyG MessagePassing propagates similarity scores across "
                             "the LSH-constructed graph; node features after MessagePassing differ "
                             "from initial features, demonstrating genuine graph computation "
                             "that depends on the edge structure supplied by datasketch LSH"},
    "z3":        {"tried": False, "used": False,
                  "reason": "not needed -- LSH graph construction and MessagePassing do not "
                             "require formal constraint encoding or SAT/SMT reasoning"},
    "cvc5":      {"tried": False, "used": False,
                  "reason": "not needed -- no quantifier reasoning required for similarity graph"},
    "sympy":     {"tried": False, "used": False,
                  "reason": "not needed -- Jaccard similarity and MinHash are numeric; "
                             "no symbolic algebra required"},
    "clifford":  {"tried": False, "used": False,
                  "reason": "not needed -- node features are bag-of-tokens vectors, "
                             "not Clifford algebra elements"},
    "geomstats": {"tried": False, "used": False,
                  "reason": "not needed -- graph topology is flat; "
                             "no Riemannian manifold structure involved"},
    "e3nn":      {"tried": False, "used": False,
                  "reason": "not needed -- no SO(3) equivariance in the token similarity graph"},
    "rustworkx": {"tried": False, "used": False,
                  "reason": "not needed -- graph is passed directly to PyG as edge_index tensor; "
                             "no separate graph library needed for this sim"},
    "xgi":       {"tried": False, "used": False,
                  "reason": "not needed -- LSH graph has pairwise edges only, no hyperedges"},
    "toponetx":  {"tried": False, "used": False,
                  "reason": "not needed -- no cell complex structure; "
                             "sim uses simple graph message passing on LSH edges"},
    "gudhi":     {"tried": False, "used": False,
                  "reason": "not needed -- no persistent homology; "
                             "topology of the sim graph is captured by LSH adjacency"},
    "datasketch": {"tried": True,  "used": True,
                   "reason": "load_bearing: MinHash (128 permutations) and MinHashLSH determine "
                              "which node pairs become edges in the PyG graph; the threshold=0.3 "
                              "Jaccard gate filters dissimilar signatures so the edge_index is "
                              "strictly a function of datasketch output, not random or fully-connected"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch":    "load_bearing",
    "pyg":        "load_bearing",
    "z3":         None,
    "cvc5":       None,
    "sympy":      None,
    "clifford":   None,
    "geomstats":  None,
    "e3nn":       None,
    "rustworkx":  None,
    "xgi":        None,
    "toponetx":   None,
    "gudhi":      None,
    "datasketch": "load_bearing",
}

# ---- imports ----

_torch_available = False
try:
    import torch
    _torch_available = True
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"
    torch = None  # type: ignore

_pyg_available = False
try:
    from torch_geometric.nn import MessagePassing
    import torch_geometric  # noqa: F401
    _pyg_available = True
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"
    MessagePassing = None  # type: ignore

_datasketch_available = False
try:
    from datasketch import MinHash, MinHashLSH
    _datasketch_available = True
    TOOL_MANIFEST["datasketch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["datasketch"]["reason"] = "not installed"
    MinHash = None  # type: ignore
    MinHashLSH = None  # type: ignore


# =====================================================================
# VOCABULARY AND SIGNATURE DEFINITIONS
# =====================================================================

VOCAB = ["PASS", "FAIL", "CANONICAL", "EXCLUDED", "STABLE", "BOUNDARY"]
VOCAB_INDEX = {tok: i for i, tok in enumerate(VOCAB)}

# 10 node signatures: each is a subset of VOCAB tokens.
# Designed so that some pairs share many tokens (high Jaccard) and some share few.
NODE_SIGNATURES_RAW = [
    {"PASS", "CANONICAL", "STABLE"},          # node 0
    {"PASS", "CANONICAL", "STABLE", "BOUNDARY"},  # node 1  -- similar to 0
    {"PASS", "STABLE"},                        # node 2  -- similar to 0, 1
    {"FAIL", "EXCLUDED"},                      # node 3
    {"FAIL", "EXCLUDED", "BOUNDARY"},          # node 4  -- similar to 3
    {"FAIL", "EXCLUDED", "CANONICAL"},         # node 5  -- somewhat similar to 3
    {"PASS", "BOUNDARY"},                      # node 6
    {"CANONICAL", "STABLE", "BOUNDARY"},       # node 7  -- similar to 0, 1
    {"FAIL", "PASS"},                          # node 8  -- mixed
    {"EXCLUDED", "STABLE", "CANONICAL"},       # node 9  -- mixed
]


def signature_to_feature_vector(sig: set) -> list:
    """One-hot membership vector over VOCAB."""
    return [1.0 if tok in sig else 0.0 for tok in VOCAB]


def build_minhash(sig: set, num_perm: int = 128) -> "MinHash":
    m = MinHash(num_perm=num_perm)
    for token in sig:
        m.update(token.encode("utf8"))
    return m


# =====================================================================
# PYG MEAN AGGREGATION MESSAGE PASSING
# =====================================================================

if _torch_available and _pyg_available:
    class MeanAggMP(MessagePassing):
        """
        Single-layer mean-aggregation MessagePassing.
        new_x_i = mean({x_j : j in N(i)})
        If a node has no neighbors, its feature stays unchanged.
        """
        def __init__(self):
            super().__init__(aggr="mean")

        def forward(self, x, edge_index):
            return self.propagate(edge_index, x=x)

        def message(self, x_j):
            return x_j

        def update(self, aggr_out, x):
            # If a node had neighbors, use aggregated mean.
            # If aggr_out is zero (no neighbors, mean aggr returns zeros),
            # keep original feature.
            has_neighbors = (aggr_out.abs().sum(dim=-1, keepdim=True) > 0).float()
            return has_neighbors * aggr_out + (1.0 - has_neighbors) * x
else:
    MeanAggMP = None  # type: ignore


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests() -> dict:
    results = {}

    if not _datasketch_available or not _torch_available or not _pyg_available:
        results["skipped"] = "datasketch or torch or pyg not available"
        return results

    N = len(NODE_SIGNATURES_RAW)
    num_perm = 128
    lsh_threshold = 0.3

    # 1. Build MinHashes
    minhashes = [build_minhash(sig, num_perm) for sig in NODE_SIGNATURES_RAW]

    # 2. Build LSH index and insert all nodes
    lsh = MinHashLSH(threshold=lsh_threshold, num_perm=num_perm)
    for i, mh in enumerate(minhashes):
        lsh.insert(str(i), mh)

    # 3. Query neighbors for each node -> edge list (undirected, no self-loops)
    edges = set()
    for i, mh in enumerate(minhashes):
        neighbors = lsh.query(mh)
        for nb_key in neighbors:
            j = int(nb_key)
            if j != i:
                edge = (min(i, j), max(i, j))
                edges.add(edge)

    edge_list = sorted(edges)
    n_edges = len(edge_list)
    results["lsh_n_edges"] = n_edges
    results["lsh_max_possible_edges"] = N * (N - 1) // 2

    # Claim 1: at least 1 edge (LSH found similar pairs)
    results["lsh_has_at_least_one_edge"] = n_edges >= 1

    # Claim 3: NOT fully connected
    results["lsh_not_fully_connected"] = n_edges < N * (N - 1) // 2

    # 4. Build PyG edge_index (undirected = both directions)
    if n_edges > 0:
        src = [e[0] for e in edge_list] + [e[1] for e in edge_list]
        dst = [e[1] for e in edge_list] + [e[0] for e in edge_list]
        edge_index = torch.tensor([src, dst], dtype=torch.long)
    else:
        edge_index = torch.zeros((2, 0), dtype=torch.long)

    # 5. Build node feature matrix (N x 6)
    feat_np = np.array([signature_to_feature_vector(sig) for sig in NODE_SIGNATURES_RAW],
                       dtype=np.float32)
    x_pre = torch.tensor(feat_np, dtype=torch.float32)

    # 6. Run MessagePassing
    mp_layer = MeanAggMP()
    mp_layer.eval()
    with torch.no_grad():
        x_post = mp_layer(x_pre.clone(), edge_index)

    # 7. Check that at least one node's feature changed
    diff = (x_post - x_pre).abs().sum(dim=1)  # per-node change
    max_feature_diff = float(diff.max().item())
    n_changed_nodes = int((diff > 1e-6).sum().item())

    results["mp_max_feature_diff"] = max_feature_diff
    results["mp_n_nodes_changed"] = n_changed_nodes

    # Claim 2: MessagePassing changes at least one node
    results["mp_changes_at_least_one_node"] = n_changed_nodes >= 1

    # Record which edges were found (for inspection)
    results["lsh_edges_found"] = edge_list

    results["pass"] = (
        results["lsh_has_at_least_one_edge"]
        and results["mp_changes_at_least_one_node"]
        and results["lsh_not_fully_connected"]
    )
    return results


# =====================================================================
# NEGATIVE TESTS (mandatory)
# =====================================================================

def run_negative_tests() -> dict:
    results = {}

    if not _datasketch_available or not _torch_available or not _pyg_available:
        results["skipped"] = "datasketch or torch or pyg not available"
        return results

    # Negative 1: Two completely disjoint signatures should NOT be admitted
    # as LSH neighbors (Jaccard = 0).
    sig_a = {"PASS", "CANONICAL"}
    sig_b = {"FAIL", "EXCLUDED"}
    mh_a = build_minhash(sig_a)
    mh_b = build_minhash(sig_b)
    jaccard_estimate = mh_a.jaccard(mh_b)
    results["disjoint_jaccard_estimate"] = float(jaccard_estimate)
    results["disjoint_jaccard_below_threshold"] = jaccard_estimate < 0.3

    # LSH with high threshold -- query should not return b as neighbor of a
    lsh_strict = MinHashLSH(threshold=0.5, num_perm=128)
    lsh_strict.insert("b", mh_b)
    neighbors_of_a = lsh_strict.query(mh_a)
    results["disjoint_lsh_no_match"] = "b" not in neighbors_of_a

    # Negative 2: MessagePassing on empty graph (no edges) should return
    # features unchanged.
    N = 4
    x_test = torch.ones(N, 6, dtype=torch.float32)
    empty_edge_index = torch.zeros((2, 0), dtype=torch.long)
    mp_layer = MeanAggMP()
    mp_layer.eval()
    with torch.no_grad():
        x_out = mp_layer(x_test.clone(), empty_edge_index)
    diff_empty = float((x_out - x_test).abs().max().item())
    results["mp_empty_graph_max_diff"] = diff_empty
    results["mp_empty_graph_unchanged"] = diff_empty < 1e-6

    results["pass"] = (
        results["disjoint_jaccard_below_threshold"]
        and results["disjoint_lsh_no_match"]
        and results["mp_empty_graph_unchanged"]
    )
    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests() -> dict:
    results = {}

    if not _datasketch_available or not _torch_available or not _pyg_available:
        results["skipped"] = "datasketch or torch or pyg not available"
        return results

    # Boundary 1: Two identical signatures -- Jaccard = 1.0 -- should always
    # be admitted at any threshold.
    sig_same = {"PASS", "CANONICAL", "STABLE"}
    mh1 = build_minhash(sig_same)
    mh2 = build_minhash(sig_same)
    jaccard_identical = mh1.jaccard(mh2)
    results["identical_jaccard_estimate"] = float(jaccard_identical)
    results["identical_jaccard_near_1"] = jaccard_identical > 0.95

    lsh_wide = MinHashLSH(threshold=0.1, num_perm=128)
    lsh_wide.insert("n2", mh2)
    neighbors = lsh_wide.query(mh1)
    results["identical_lsh_admits_match"] = "n2" in neighbors

    # Boundary 2: Single-node graph -- MessagePassing with self-loop excluded;
    # node has no neighbors => feature must be unchanged.
    x_single = torch.tensor([[1.0, 0.0, 1.0, 0.0, 1.0, 0.0]], dtype=torch.float32)
    edge_index_single = torch.zeros((2, 0), dtype=torch.long)
    mp_layer = MeanAggMP()
    mp_layer.eval()
    with torch.no_grad():
        x_single_out = mp_layer(x_single.clone(), edge_index_single)
    diff_single = float((x_single_out - x_single).abs().max().item())
    results["single_node_mp_diff"] = diff_single
    results["single_node_mp_unchanged"] = diff_single < 1e-6

    # Boundary 3: Verify MinHash with num_perm=32 (minimal) still runs without error.
    mh_small = build_minhash({"PASS", "STABLE"}, num_perm=32)
    results["minhash_small_num_perm_runs"] = mh_small is not None

    results["pass"] = (
        results["identical_jaccard_near_1"]
        and results["identical_lsh_admits_match"]
        and results["single_node_mp_unchanged"]
        and results["minhash_small_num_perm_runs"]
    )
    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    t0 = time.time()

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    elapsed = time.time() - t0

    overall_pass = (
        positive.get("pass", False)
        and negative.get("pass", False)
        and boundary.get("pass", False)
    )

    classification = "canonical"

    results = {
        "name": "sim_integration_datasketch_pyg_lsh_graph",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "overall_pass": overall_pass,
        "elapsed_s": round(elapsed, 3),
    }

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_integration_datasketch_pyg_lsh_graph_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"overall_pass={overall_pass}  classification={classification}  elapsed={elapsed:.2f}s")
    if not overall_pass:
        import sys
        sys.exit(1)

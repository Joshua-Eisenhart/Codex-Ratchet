#!/usr/bin/env python3
"""torch_graph_drive.py — torch_graph lane of the engine-native probe set.

Graph/autograd lanes welded INTO the manifold pipeline (Lev-governed, gates are code).

L0/L1: capacity complex from source_packets.json as torch_geometric Data per packet.
       Per-packet Hamming-1 graph: Laplacian spectral gap + component structure
       (spectral null-space count cross-checked against an independent union-find).
       DRIVE FROM THE GRAPH: prefix-trie as PyG Data, extension counts per node
       (out-degree), leaf count derived from the graph -> Hartley capacity per
       packet -> dC series under chaining in declared order. Gate: graph-derived
       dC must equal direct set-count dC EXACTLY for every packet (>=3 required).

L12:   Fisher metric as exact torch.func.hessian of KL on each packet's
       continuation distribution (2-bit-prefix continuation mass). Gate: matches
       diag(1/p) analytic law to 1e-12. Then the NESTED chain identity
       g_p = g_P + sum_g P_g g_(p|g) verified on a 2-level grouping of one
       packet with BOTH sides computed by autograd (block assembly), no hand
       algebra on the left side.

Weld:  export the graph-derived drive series to JSON; load the julia receipt's
       dC series and compare; record structural difference honestly if not
       directly comparable.

Ceiling: scratch_diagnostic. promotion_allowed: false. Not proof-level.
"""

import json
import math
import os
import sys

import torch
from torch_geometric.data import Data
from torch_geometric.utils import degree, get_laplacian, to_dense_adj, to_scipy_sparse_matrix
from scipy.sparse.csgraph import connected_components

torch.set_default_dtype(torch.float64)

REPO = "/Users/joshuaeisenhart/Codex-Ratchet"
SRC = os.path.join(REPO, "system_v8/manifold/results/source_packets.json")
JULIA_RECEIPT = os.path.join(REPO, "system_v8/engine_native/results/julia_manifold/receipt.json")
OUTDIR = os.path.join(REPO, "system_v8/engine_native/results/torch_graph")

# ---- refuse-to-reuse outdir -------------------------------------------------
if os.path.exists(OUTDIR):
    print(f"REFUSE: outdir already exists: {OUTDIR}", file=sys.stderr)
    sys.exit(2)
os.makedirs(OUTDIR)

with open(SRC) as f:
    src = json.load(f)
packets = src["base_packets"]  # declared order = list order

checks = {}
data = {"packets": {}}
findings = []

# ============================================================================
# L0/L1 — capacity complex per packet as torch_geometric Data
# ============================================================================

def trie_data(words, width):
    """Prefix trie of the accepted words as a PyG Data graph (parent->child)."""
    node_of = {"": 0}
    edges = []
    for w in words:
        for k in range(1, width + 1):
            pre, par = w[:k], w[: k - 1]
            if pre not in node_of:
                node_of[pre] = len(node_of)
                edges.append((node_of[par], node_of[pre]))
    ei = torch.tensor(edges, dtype=torch.long).t().contiguous()
    return Data(edge_index=ei, num_nodes=len(node_of))


def graph_depths(d: Data, width: int):
    """Node depths derived from the graph alone (edge propagation from root 0)."""
    depth = torch.full((d.num_nodes,), -1, dtype=torch.long)
    depth[0] = 0
    src_n, dst_n = d.edge_index
    for _ in range(width):
        known = depth[src_n] >= 0
        depth[dst_n[known]] = depth[src_n[known]] + 1
    return depth


def hamming_graph(words):
    """Hamming-distance-1 graph on accepted words (undirected, both directions)."""
    n = len(words)
    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            if sum(a != b for a, b in zip(words[i], words[j])) == 1:
                edges.append((i, j))
                edges.append((j, i))
    if edges:
        ei = torch.tensor(edges, dtype=torch.long).t().contiguous()
    else:
        ei = torch.zeros((2, 0), dtype=torch.long)
    return Data(edge_index=ei, num_nodes=n)


graph_counts, direct_counts = [], []
exact_dC_match = []
leaf_identity_ok = []
comp_crosscheck_ok = []

for p in packets:
    pid, words, width = p["packet_id"], p["accepted_words"], p["width"]
    assert len(words) == p["accepted_count"], f"{pid}: accepted_count mismatch in source"

    # --- trie / drive ---
    td = trie_data(words, width)
    ext = degree(td.edge_index[0], num_nodes=td.num_nodes, dtype=torch.long)  # extension counts per node
    depth = graph_depths(td, width)
    n_leaf_graph = int((depth == width).sum())            # graph-derived accepted count
    n_direct = len(set(words))                            # direct set count
    # internal graph identity: leaves == sum of extension counts at depth width-1
    leaf_via_ext = int(ext[depth == width - 1].sum())
    leaf_identity_ok.append(leaf_via_ext == n_leaf_graph)
    graph_counts.append(n_leaf_graph)
    direct_counts.append(n_direct)

    # --- Hamming-1 graph: spectral gap + components ---
    hd = hamming_graph(words)
    lap_i, lap_w = get_laplacian(hd.edge_index, num_nodes=hd.num_nodes)
    L = to_dense_adj(lap_i, edge_attr=lap_w, max_num_nodes=hd.num_nodes)[0]
    evals = torch.linalg.eigvalsh(L)
    n_comp_spec = int((evals < 1e-8).sum())
    gap = float(evals[1]) if hd.num_nodes > 1 else 0.0
    # independent component count (union-find via scipy csgraph)
    if hd.edge_index.numel() > 0:
        A = to_scipy_sparse_matrix(hd.edge_index, num_nodes=hd.num_nodes)
        n_comp_uf = int(connected_components(A, directed=False)[0])
    else:
        n_comp_uf = hd.num_nodes
    comp_crosscheck_ok.append(n_comp_spec == n_comp_uf)

    data["packets"][pid] = {
        "width": width,
        "count_graph": n_leaf_graph,
        "count_direct": n_direct,
        "trie_nodes": td.num_nodes,
        "trie_edges": int(td.edge_index.shape[1]),
        "extension_counts_root": int(ext[0]),
        "hartley_capacity_bits": math.log2(n_leaf_graph),
        "spectral_gap": gap,
        "laplacian_eigs_first4": [float(x) for x in evals[:4]],
        "components_spectral": n_comp_spec,
        "components_unionfind": n_comp_uf,
    }

# drive series: Hartley capacity per packet, chained in declared order
C_graph = [math.log2(c) for c in graph_counts]
C_direct = [math.log2(c) for c in direct_counts]
Ccum = []
acc = 0.0
for c in C_graph:
    acc += c
    Ccum.append(acc)
dC_graph = C_graph[:]           # per-chain-step capacity increment
dC_direct = C_direct[:]
for k in range(len(packets)):
    exact_dC_match.append(graph_counts[k] == direct_counts[k] and dC_graph[k] == dC_direct[k])

# chained total count as exact integer product, cross-checked against cumulative capacity
prod = 1
for c in graph_counts:
    prod *= c
checks["drive_chain_product_matches_cumulative_capacity"] = abs(Ccum[-1] - math.log2(prod)) < 1e-9

checks["drive_graph_dC_matches_setcount_exact_all9"] = all(exact_dC_match) and len(exact_dC_match) >= 3
checks["trie_leaf_count_equals_extension_sum_all9"] = all(leaf_identity_ok)
checks["components_spectral_matches_unionfind_all9"] = all(comp_crosscheck_ok)

# targeted spectral gates (exact known values, can fail):
full = data["packets"]["qca_finite_depth_local_circuit_cut_relation"]
checks["hypercube_Q4_gap_exactly_2"] = (
    full["count_graph"] == 16
    and full["components_spectral"] == 1
    and abs(full["spectral_gap"] - 2.0) < 1e-9
)
ident = data["packets"]["qca_identity_cut_relation"]
checks["identity_packet_4_isolated_components"] = (
    ident["components_spectral"] == 4 and ident["spectral_gap"] < 1e-9
)

data["drive"] = {
    "declared_order": [p["packet_id"] for p in packets],
    "counts_graph": graph_counts,
    "counts_direct": direct_counts,
    "dC_bits_graph": dC_graph,
    "dC_bits_direct": dC_direct,
    "C_cumulative_bits": Ccum,
    "chained_total_count": prod,
}

# ============================================================================
# L12 — Fisher metric = exact torch.func.hessian of KL on continuation dists
# ============================================================================

def kl(p0, q):
    return torch.sum(p0 * (torch.log(p0) - torch.log(q)))


fisher_max_err = 0.0
for p in packets:
    pid, words = p["packet_id"], p["accepted_words"]
    # continuation distribution: mass over 2-bit prefixes (continuations of the cut)
    pref = {}
    for w in words:
        pref[w[:2]] = pref.get(w[:2], 0) + 1
    keys = sorted(pref)
    p0 = torch.tensor([pref[k] / len(words) for k in keys])
    H = torch.func.hessian(lambda q: kl(p0, q))(p0.clone())
    err = float(torch.max(torch.abs(H - torch.diag(1.0 / p0))))
    fisher_max_err = max(fisher_max_err, err)
    data["packets"][pid]["continuation_dist"] = {k: float(v) for k, v in zip(keys, p0)}
    data["packets"][pid]["fisher_vs_diag_inv_p_max_abs_err"] = err

checks["fisher_hessian_matches_diag_inv_p_1e-12_all9"] = fisher_max_err <= 1e-12
data["fisher_max_abs_err_over_packets"] = fisher_max_err

# ---- nested chain identity g_p = g_P + sum_g P_g g_(p|g), by autograd -------
# 2-level grouping of gcm_completion_projection (N=7, odd => grouping by first
# bit is FORCED asymmetric, so the P_g weights are load-bearing: a swapped or
# wrong P_g cannot cancel). First-run finding: the ring packet's first-bit
# grouping had P_groups=[0.5,0.5], leaving P_g undetectable — regated here.
# Non-uniform word weights: 2-bit-prefix continuation mass (graph-flavoured
# weight). Run-2 finding: gcm's 3-bit prefixes are all distinct, which made the
# 3-bit weights UNIFORM and honestly failed nested_grouping_nontrivial (kept as
# results/torch_graph_run2_uniform_weights_negative). 2-bit mass is non-uniform
# on gcm (00:2, 01:2, 11:2, 10:1).
NEST_PACKET = "gcm_completion_projection"
ring = next(p for p in packets if p["packet_id"] == NEST_PACKET)
words = ring["accepted_words"]
w3 = {}
for w in words:
    w3[w[:2]] = w3.get(w[:2], 0) + 1
weights = torch.tensor([float(w3[w[:2]]) for w in words])
p_full0 = weights / weights.sum()

groups = {"0": [i for i, w in enumerate(words) if w[0] == "0"],
          "1": [i for i, w in enumerate(words) if w[0] == "1"]}
gkeys = sorted(groups)
P0 = torch.tensor([float(p_full0[groups[g]].sum()) for g in gkeys])          # marginal over groups
cond0 = {g: p_full0[groups[g]] / p_full0[groups[g]].sum() for g in gkeys}    # conditionals

n0, n1 = len(groups["0"]), len(groups["1"])
# split coordinates: theta = [u (P(group1) free coord), v0 (n0-1), v1 (n1-1)]
theta0 = torch.cat([P0[1:2], cond0["0"][:-1], cond0["1"][:-1]])


def full_dist(theta):
    u = theta[0]
    v0 = torch.cat([theta[1:n0], (1 - theta[1:n0].sum()).reshape(1)])
    v1 = torch.cat([theta[n0:n0 + n1 - 1], (1 - theta[n0:n0 + n1 - 1].sum()).reshape(1)])
    p = torch.zeros(len(words), dtype=theta.dtype)
    p = p.index_put((torch.tensor(groups["0"]),), (1 - u) * v0)
    p = p.index_put((torch.tensor(groups["1"]),), u * v1)
    return p


# LHS: full Fisher by autograd on the joint KL
g_full = torch.func.hessian(lambda th: kl(p_full0, full_dist(th)))(theta0.clone())

# RHS pieces, each by autograd (no hand algebra):
def marg_dist(u):
    return torch.stack([1 - u[0], u[0]])


g_P = torch.func.hessian(lambda u: kl(P0, marg_dist(u)))(theta0[0:1].clone())


def cond_dist(v):
    return torch.cat([v, (1 - v.sum()).reshape(1)])


g_c0 = torch.func.hessian(lambda v: kl(cond0["0"], cond_dist(v)))(cond0["0"][:-1].clone())
g_c1 = torch.func.hessian(lambda v: kl(cond0["1"], cond_dist(v)))(cond0["1"][:-1].clone())

rhs = torch.zeros_like(g_full)
rhs[0, 0] = g_P[0, 0]
rhs[1:n0, 1:n0] = P0[0] * g_c0
rhs[n0:, n0:] = P0[1] * g_c1

chain_err = float(torch.max(torch.abs(g_full - rhs)))
off = g_full.clone()
off[0, 0] = 0
off[1:n0, 1:n0] = 0
off[n0:, n0:] = 0
cross_block_max = float(torch.max(torch.abs(off)))

checks["nested_chain_identity_gp_eq_gP_plus_sum_Pg_gcond_1e-10"] = chain_err <= 1e-10
checks["nested_chain_cross_blocks_vanish_1e-10"] = cross_block_max <= 1e-10
checks["nested_grouping_nontrivial"] = (n0 >= 2 and n1 >= 2
                                        and float(torch.std(p_full0)) > 0.0)
# P_g must be load-bearing: equal group masses would make a wrong P_g invisible
checks["nested_grouping_asymmetric_P_groups"] = abs(float(P0[0] - P0[1])) > 1e-6
data["nested_chain"] = {
    "packet": NEST_PACKET,
    "grouping": "first bit",
    "group_sizes": [n0, n1],
    "P_groups": [float(x) for x in P0],
    "p_full_nonuniform_std": float(torch.std(p_full0)),
    "max_abs_err_full_vs_assembled": chain_err,
    "cross_block_max_abs": cross_block_max,
}

# ============================================================================
# Weld check — export drive series, compare to julia receipt dC
# ============================================================================
drive_path = os.path.join(OUTDIR, "graph_drive_series.json")
with open(drive_path, "w") as f:
    json.dump(data["drive"], f, indent=1)
with open(drive_path) as f:
    reread = json.load(f)
checks["weld_drive_series_exported_and_reloads_identically"] = (
    reread["dC_bits_graph"] == data["drive"]["dC_bits_graph"]
    and reread["chained_total_count"] == prod
)

weld = {"julia_receipt": JULIA_RECEIPT}
try:
    with open(JULIA_RECEIPT) as f:
        jr = json.load(f)
    j_dC = jr["data"]["base_series"]["dC"]
    weld["julia_dC_len"] = len(j_dC)
    weld["julia_dC_first3"] = j_dC[:3]
    weld["julia_dC_all_positive_recomputed"] = all(x > 0 for x in j_dC)
    checks["weld_julia_dC_loaded_and_all_positive"] = (
        len(j_dC) > 0 and all(math.isfinite(x) and x > 0 for x in j_dC)
    )
    # comparability: julia dC is a per-TICK ln-based transfer-matrix count-growth
    # series (len 30, period-3 over its gamma schedule) on the manifold tick loop;
    # the torch series is per-PACKET log2 Hartley capacity under chaining (len 9).
    # Different index sets and different objects -> NOT directly comparable.
    same_len = len(j_dC) == len(dC_graph)
    weld["directly_comparable"] = False
    weld["structural_difference"] = (
        "julia dC: per-tick ln count-growth of the manifold drive "
        f"(len {len(j_dC)}, ln-based, gamma-schedule period 3); "
        f"torch dC: per-packet log2 Hartley capacity under declared-order chaining "
        f"(len {len(dC_graph)}, log2-based, one entry per source packet). "
        "Both are count-derived drive series; index sets and carriers differ."
    )
    weld["both_series_strictly_positive"] = (
        all(x > 0 for x in j_dC) and all(x > 0 for x in dC_graph)
    )
    checks["weld_both_drive_series_strictly_positive"] = weld["both_series_strictly_positive"]
    checks["weld_not_falsely_claimed_comparable"] = not same_len  # guard: if lengths ever
    # collide this gate fails and forces a real element-wise comparison to be written.
except (OSError, KeyError) as e:  # honest negative if julia receipt missing
    weld["error"] = str(e)
    checks["weld_julia_dC_loaded_and_all_positive"] = False
    checks["weld_both_drive_series_strictly_positive"] = False
    checks["weld_not_falsely_claimed_comparable"] = False
data["weld"] = weld

# ============================================================================
# Receipt
# ============================================================================
all_pass = all(checks.values())
receipt = {
    "schema": "engine_native_probe_v1",
    "lane": "torch_graph",
    "engine": {
        "python": sys.version.split()[0],
        "torch": torch.__version__,
        "torch_geometric": __import__("torch_geometric").__version__,
    },
    "source_packets": SRC,
    "source_digest": src.get("result_digest"),
    "conventions": {
        "capacity": "Hartley, log2 of graph-derived leaf count of the prefix trie",
        "fisher": "exact torch.func.hessian of KL(p0||q) at q=p0; law diag(1/p0)",
        "nested_chain": "g_p = g_P + sum_g P_g g_(p|g), both sides autograd, split coords",
        "spectral": "graph Laplacian (get_laplacian), eigvalsh, gap = second eigenvalue",
    },
    "checks": checks,
    "data": data,
    "all_pass": all_pass,
    "promotion_allowed": False,
    "claim_ceiling": (
        "scratch_diagnostic; torch_geometric graph lanes + torch.func autograd doing "
        "load-bearing work on manifold source packets; no physics claim beyond the "
        "executed checks; not comparable element-wise to the julia tick dC series "
        "(structural difference recorded)"
    ),
}
rp = os.path.join(OUTDIR, "receipt.json")
with open(rp, "w") as f:
    json.dump(receipt, f, indent=1)

print(f"receipt: {rp}")
for k, v in checks.items():
    print(f"  {'PASS' if v else 'FAIL'}  {k}")
print(f"all_pass: {all_pass}")
print(f"fisher_max_err: {fisher_max_err:.3e}  chain_err: {chain_err:.3e}  cross_block: {cross_block_max:.3e}")
print(f"dC_bits_graph: {[round(x,4) for x in dC_graph]}")
sys.exit(0 if all_pass else 1)

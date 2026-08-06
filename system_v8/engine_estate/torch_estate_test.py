#!/usr/bin/env python3
"""PyTorch engine-estate test — system_v8.

Phase PyTorch of the three-engine estate probe (graph/autograd lane; Julia and
JAX phases already green). One engine stack loaded (torch); gates are code;
promotion_allowed: false. NOT proof-level: goal is working sims where packages
do load-bearing work on real manifold content.

Manifold content: system_v8/manifold/results/source_packets.json base_packets.
Each packet is a width-4 cut relation: accepted words over coordinates
(input_site_2, input_site_3, output_site_2, output_site_3). The first two bits
are the input half, the last two the output half.

Graph definitions (stated exactly, per packet):
  continuation digraph:  wi -> wj  iff  out(wi) == in(wj)
  capacity complex (shared-continuation, PRIMARY, undirected):
      wi -- wj (i != j)  iff  the continuation sets of wi and wj intersect,
      i.e. exists wk in the packet with in(wk) == out(wi) == out(wj).

Lanes (scoped by the phase card):
  L0   torch_geometric: build the capacity complex as a real Data graph per
       packet; components via torch_geometric utils checked against a pure-
       python union-find (independent path).
  L1   message passing (MessagePassing subclass, max aggregation, run to fixed
       point) labels components; checked against union-find. Spectral: number
       of near-zero eigenvalues of the normalized Laplacian == number of
       components (graph-theory law, code gate); spectral gap recorded.
  L12  autograd: Fisher metric as EXACT Hessian of KL via torch.func.hessian,
       on a real nonuniform distribution (continuation-count distribution of a
       packet). Analytic: Hess KL(p0||p)|_{p=p0} = diag(1/p0) (the delta_ij/p_i
       law). Second parameterization: softmax logits, Hess = diag(p) - p p^T.
  Lgs  geomstats: categorical Fisher-Rao distance vs closed form
       2*arccos(sum sqrt(p q)); quadratic-form weld dist(p, p+eps*v)^2/eps^2 vs
       v^T H v with H the torch Hessian from L12; Bures-Wasserstein on
       commuting SPD (diagonal) vs closed form sum (sqrt a - sqrt b)^2.

Smoke lanes (import-plus): e3nn, clifford, torch_ga — one tiny check each.

Receipt: results/torch/receipt.json
"""

import json
import math
import os
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
PACKETS = os.path.join(
    HERE, "..", "manifold", "results", "source_packets.json"
)
OUTDIR = os.environ.get("ENGINE_ESTATE_RESULTS_DIR", os.path.join(HERE, "results", "torch"))
os.makedirs(OUTDIR, exist_ok=True)

receipt = {
    "engine": "pytorch",
    "phase": "system_v8 engine_estate PyTorch phase (graph/autograd lane)",
    "date": "2026-07-19",
    "python": sys.version,
    "interpreter": sys.executable,
    "promotion_allowed": False,
    "claim_ceiling": "working-sim estate probe; not canonical, not proof-level",
    "source_packets": os.path.relpath(PACKETS, HERE),
    "versions": {},
    "checks": {},
    "timings": {},
    "per_packet": {},
    "blocked": [],
    "findings": [],
}

def check(name, ok, detail=""):
    receipt["checks"][name] = {"pass": bool(ok), "detail": str(detail)}
    print(f"[{'PASS' if ok else 'FAIL'}] {name}  {detail}")

# ---------------------------------------------------------------- inventory
import torch
import torch_geometric
from torch_geometric.data import Data
from torch_geometric.nn import MessagePassing
from torch_geometric.utils import get_laplacian, to_dense_adj, to_undirected

receipt["versions"]["torch"] = torch.__version__
receipt["versions"]["torch_geometric"] = torch_geometric.__version__
torch.manual_seed(0)
torch.set_default_dtype(torch.float64)

import numpy as np
receipt["versions"]["numpy"] = np.__version__

with open(PACKETS) as f:
    src = json.load(f)
base_packets = src["base_packets"]
receipt["source_packet_digest"] = src.get("result_digest", "")
check("packets_loaded", len(base_packets) == 9, f"{len(base_packets)} base packets")

W = 4
HALF = W // 2

def halves(word):
    return word[:HALF], word[HALF:]

# ============================================================ L0: graph build
def build_graphs(words):
    """Return (continuation digraph edges, shared-continuation undirected edges)."""
    n = len(words)
    ins = {}
    for k, w in enumerate(words):
        ins.setdefault(halves(w)[0], set()).add(k)
    cont = {k: frozenset(ins.get(halves(w)[1], frozenset()))
            for k, w in enumerate(words)}
    di = [(i, j) for i in range(n) for j in cont[i]]
    und = [(i, j) for i in range(n) for j in range(i + 1, n)
           if cont[i] & cont[j]]
    return di, und

class UnionFind:
    def __init__(self, n):
        self.p = list(range(n))
    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x
    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[ra] = rb

# ================================================= L1: message passing layer
class MaxProp(MessagePassing):
    """Propagate max node label along edges — pure torch_geometric machinery."""
    def __init__(self):
        super().__init__(aggr="max")
    def forward(self, x, edge_index):
        out = self.propagate(edge_index, x=x)
        return torch.maximum(x, out)
    def message(self, x_j):
        return x_j

t0 = time.perf_counter()
mp_layer = MaxProp()
l0_all_ok, l1_mp_all_ok, l1_spec_all_ok = True, True, True
gap_summary = {}

for pkt in base_packets:
    pid = pkt["packet_id"]
    words = pkt["accepted_words"]
    n = len(words)
    di, und = build_graphs(words)

    # independent path: pure-python union-find on the undirected edge list
    uf = UnionFind(n)
    for a, b in und:
        uf.union(a, b)
    uf_labels = [uf.find(k) for k in range(n)]
    n_comp_uf = len(set(uf_labels))

    # torch_geometric Data graph
    if und:
        ei = torch.tensor(und, dtype=torch.long).t()
        ei = to_undirected(ei)
    else:
        ei = torch.zeros((2, 0), dtype=torch.long)
    data = Data(x=torch.arange(n, dtype=torch.float64).unsqueeze(1),
                edge_index=ei, num_nodes=n)
    ok_data = data.validate(raise_on_error=False)

    # L1a: message passing to fixed point -> component labels
    x = data.x.clone()
    for _ in range(n):
        x_new = mp_layer(x, data.edge_index)
        if torch.equal(x_new, x):
            break
        x = x_new
    mp_labels = [int(v) for v in x.squeeze(1).tolist()]
    # same partition as union-find?
    part_uf = {}
    for k, lab in enumerate(uf_labels):
        part_uf.setdefault(lab, set()).add(k)
    part_mp = {}
    for k, lab in enumerate(mp_labels):
        part_mp.setdefault(lab, set()).add(k)
    mp_ok = set(map(frozenset, part_uf.values())) == set(map(frozenset, part_mp.values()))

    # L1b: Laplacian spectra. Law (universal): for the UNNORMALIZED Laplacian
    # L = D - A, #(zero eigenvalues) == #(connected components). For the
    # sym-normalized Laplacian torch_geometric assigns isolated (degree-0)
    # nodes a diagonal of 1, so each isolated-node component contributes
    # eigenvalue 1, not 0; the exact prediction there is
    # #(zero eigs) == n_components - n_isolated_nodes.
    lap_ei_u, lap_w_u = get_laplacian(data.edge_index, num_nodes=n)
    L_u = to_dense_adj(lap_ei_u, edge_attr=lap_w_u, max_num_nodes=n).squeeze(0)
    evals_u = torch.linalg.eigvalsh(L_u)
    n_zero_u = int((evals_u < 1e-8).sum())

    lap_ei, lap_w = get_laplacian(data.edge_index, normalization="sym",
                                  num_nodes=n)
    L = to_dense_adj(lap_ei, edge_attr=lap_w, max_num_nodes=n).squeeze(0)
    evals = torch.linalg.eigvalsh(L)
    n_zero = int((evals < 1e-8).sum())
    nonzero = evals[evals >= 1e-8]
    gap = float(nonzero[0]) if len(nonzero) else None
    touched = set(a for e in und for a in e)
    n_isolated = n - len(touched)
    spec_ok = (n_zero_u == n_comp_uf) and (n_zero == n_comp_uf - n_isolated)

    l0_all_ok &= bool(ok_data)
    l1_mp_all_ok &= mp_ok
    l1_spec_all_ok &= spec_ok
    receipt["per_packet"][pid] = {
        "n_nodes": n,
        "n_edges_continuation_digraph": len(di),
        "n_edges_shared_continuation": len(und),
        "n_components_unionfind": n_comp_uf,
        "n_components_message_passing": len(part_mp),
        "n_isolated_nodes": n_isolated,
        "n_zero_unnormalized_laplacian_eigs": n_zero_u,
        "n_zero_sym_laplacian_eigs": n_zero,
        "spectral_gap_normalized_laplacian": gap,
        "laplacian_eigs_head": [round(float(v), 8) for v in evals[:5].tolist()],
    }
    gap_summary[pid] = gap

receipt["timings"]["L0_L1_graphs_9pkts_s"] = time.perf_counter() - t0
check("L0_pyg_data_valid_all_packets", l0_all_ok,
      "Data.validate() on all 9 capacity-complex graphs")
check("L1_message_passing_components_match_unionfind", l1_mp_all_ok,
      "MaxProp fixed-point partition == pure-python union-find, all 9 packets")
check("L1_spectral_zero_eigs_equal_components", l1_spec_all_ok,
      "unnormalized: zeros==components; sym: zeros==components-isolated, all 9")
receipt["findings"].append(
    "torch_geometric get_laplacian(normalization='sym') assigns degree-0 nodes "
    "a diagonal of 1, so isolated-node components contribute eigenvalue 1, not "
    "0; the components law was gated on the unnormalized Laplacian (universal) "
    "plus the exact sym-convention prediction zeros == components - isolated.")
print("spectral gaps:", json.dumps(gap_summary, indent=1))

# ==================================================== L12: Fisher via torch.func
# Real nonuniform distribution: continuation-count distribution of the
# gcm_completion_projection packet (source_observation role, 7 words).
pkt = next(p for p in base_packets if p["packet_id"] == "gcm_completion_projection")
words = pkt["accepted_words"]
di, _ = build_graphs(words)
counts = [1 + sum(1 for a, b in di if a == k) for k in range(len(words))]  # +1 smoothing keeps p>0
p0 = torch.tensor(counts, dtype=torch.float64)
p0 = p0 / p0.sum()
receipt["L12_distribution"] = {
    "packet": pkt["packet_id"],
    "construction": "1 + out-degree in continuation digraph, normalized",
    "p0": [round(float(v), 8) for v in p0.tolist()],
}
nonuniform = float(p0.max() - p0.min()) > 1e-6
check("L12_p0_real_nonuniform", nonuniform,
      f"p0 range [{float(p0.min()):.4f}, {float(p0.max()):.4f}]")

from torch.func import hessian

t0 = time.perf_counter()

def kl_p(p):  # KL(p0 || p), p the free parameter (simplex-ambient coords)
    return torch.sum(p0 * (torch.log(p0) - torch.log(p)))

H_p = hessian(kl_p)(p0.clone())
analytic_p = torch.diag(1.0 / p0)
err_p = float((H_p - analytic_p).abs().max())
check("L12_hessian_KL_equals_delta_over_p", err_p < 1e-8,
      f"max|Hess - diag(1/p)| = {err_p:.3e}")

theta0 = torch.log(p0)  # softmax(theta0) == p0

def kl_theta(theta):
    logq = theta - torch.logsumexp(theta, dim=0)
    return torch.sum(p0 * (torch.log(p0) - logq))

H_t = hessian(kl_theta)(theta0.clone())
analytic_t = torch.diag(p0) - torch.outer(p0, p0)
err_t = float((H_t - analytic_t).abs().max())
check("L12_hessian_softmax_equals_diagp_minus_ppT", err_t < 1e-8,
      f"max|Hess - (diag(p)-pp^T)| = {err_t:.3e}")
receipt["timings"]["L12_two_hessians_s"] = time.perf_counter() - t0
receipt["timings"]["L12_hessian_dim"] = int(p0.numel())

# ============================================================ Lgs: geomstats
try:
    import geomstats
    receipt["versions"]["geomstats"] = geomstats.__version__
    from geomstats.information_geometry.categorical import CategoricalDistributions

    dim = int(p0.numel())
    cd = CategoricalDistributions(dim)
    # second real distribution: same construction on v7_ring_presentation_relation
    pkt2 = next(p for p in base_packets
                if p["packet_id"] == "v7_ring_presentation_relation")
    di2, _ = build_graphs(pkt2["accepted_words"])
    c2 = [1 + sum(1 for a, b in di2 if a == k) for k in range(len(pkt2["accepted_words"]))]
    # coarse-grain to dim bins so both live on the same simplex
    q_np = np.zeros(dim)
    for k, c in enumerate(c2):
        q_np[k % dim] += c
    q_np = q_np / q_np.sum()
    p_np = p0.numpy()

    t0 = time.perf_counter()
    d_gs = float(cd.metric.dist(p_np, q_np))
    d_closed = 2.0 * math.acos(min(1.0, float(np.sum(np.sqrt(p_np * q_np)))))
    err_fr = abs(d_gs - d_closed)
    check("Lgs_fisher_rao_dist_matches_closed_form", err_fr < 1e-8,
          f"|{d_gs:.10f} - {d_closed:.10f}| = {err_fr:.3e}")

    # weld: geomstats local distance vs torch-autograd Fisher quadratic form
    eps = 1e-4
    v = q_np - p_np
    v = v - v.mean()          # tangent to the simplex
    v = v / np.linalg.norm(v)
    p_eps = p_np + eps * v
    d2 = float(cd.metric.dist(p_np, p_eps)) ** 2
    quad = float(v @ H_p.numpy() @ v) * eps ** 2   # H_p = torch Hessian (L12)
    rel = abs(d2 - quad) / quad
    check("Lgs_local_dist2_matches_torch_hessian_quadform", rel < 1e-3,
          f"dist^2={d2:.6e} vs v^T H v eps^2={quad:.6e}, rel err {rel:.2e}")
    receipt["timings"]["Lgs_fisher_rao_s"] = time.perf_counter() - t0

    # Bures-Wasserstein on commuting SPD: diagonal density-like matrices from
    # the two packet distributions; closed form sum (sqrt a - sqrt b)^2.
    from geomstats.geometry.spd_matrices import SPDMatrices, SPDBuresWassersteinMetric
    spd = SPDMatrices(dim, equip=False)
    spd.equip_with_metric(SPDBuresWassersteinMetric)
    A = np.diag(p_np)
    B = np.diag(q_np)
    t0 = time.perf_counter()
    d_bw = float(spd.metric.dist(A, B))
    d_bw_closed = math.sqrt(float(np.sum((np.sqrt(p_np) - np.sqrt(q_np)) ** 2)))
    err_bw = abs(d_bw - d_bw_closed)
    check("Lgs_bures_wasserstein_diagonal_closed_form", err_bw < 1e-8,
          f"|{d_bw:.10f} - {d_bw_closed:.10f}| = {err_bw:.3e}")
    receipt["timings"]["Lgs_bures_s"] = time.perf_counter() - t0
except Exception as e:
    traceback.print_exc()
    receipt["blocked"].append({"package": "geomstats",
                               "error": f"{type(e).__name__}: {e}"})
    check("Lgs_geomstats", False, f"BLOCKED: {type(e).__name__}: {e}")

# ============================================================ smoke lanes
try:
    import e3nn
    from e3nn import o3
    receipt["versions"]["e3nn"] = e3nn.__version__
    irreps = o3.Irreps("1x0e + 1x1o")
    ok = irreps.dim == 4
    R = o3.rand_matrix()
    D = irreps.D_from_matrix(R)
    ok = ok and bool(torch.allclose(D @ D.T, torch.eye(4), atol=1e-10))
    check("smoke_e3nn_irreps_rep_orthogonal", ok,
          "Irreps(0e+1o) dim 4; D(R) orthogonal to 1e-10")
except Exception as e:
    receipt["blocked"].append({"package": "e3nn", "error": f"{type(e).__name__}: {e}"})
    check("smoke_e3nn", False, f"BLOCKED: {e}")

try:
    import clifford
    receipt["versions"]["clifford"] = clifford.__version__
    layout, blades = clifford.Cl(3)
    e1, e2 = blades["e1"], blades["e2"]
    ok = (e1 * e2 == -(e2 * e1)) and ((e1 * e2) ** 2 == -1)
    check("smoke_clifford_cl3_bivector", bool(ok),
          "e1e2 = -e2e1 and (e12)^2 = -1 in Cl(3)")
except Exception as e:
    receipt["blocked"].append({"package": "clifford", "error": f"{type(e).__name__}: {e}"})
    check("smoke_clifford", False, f"BLOCKED: {e}")

try:
    import torch_ga
    from torch_ga import GeometricAlgebra
    receipt["versions"]["torch_ga"] = getattr(torch_ga, "__version__", "0.0.6 (pip)")
    # torch_ga builds float32 internals; it breaks under a float64 default
    # (recorded as a finding), so run its smoke at float32.
    torch.set_default_dtype(torch.float32)
    try:
        ga = GeometricAlgebra([1.0, 1.0, 1.0])
        a, b = ga.e("0"), ga.e("1")
        ok = bool(torch.allclose(ga.geom_prod(a, b), -ga.geom_prod(b, a)))
    finally:
        torch.set_default_dtype(torch.float64)
    check("smoke_torch_ga_anticommute", ok, "e0 e1 = -e1 e0 (torch tensors, float32)")
    receipt["findings"].append(
        "torch_ga 0.0.6 mixes hard-coded float32 internals with default-dtype "
        "tensors: under torch.set_default_dtype(torch.float64) geom_prod raises "
        "'expected m1 and m2 to have the same dtype: float != double'. Works at "
        "the float32 default; not float64-safe.")
except Exception as e:
    receipt["blocked"].append({"package": "torch_ga", "error": f"{type(e).__name__}: {e}"})
    check("smoke_torch_ga", False, f"BLOCKED: {e}")

# ============================================================ receipt
n_pass = sum(1 for c in receipt["checks"].values() if c["pass"])
n_tot = len(receipt["checks"])
receipt["checks_passed"] = n_pass
receipt["checks_total"] = n_tot
receipt["all_pass"] = (n_pass == n_tot)
out = os.path.join(OUTDIR, "receipt.json")
with open(out, "w") as f:
    json.dump(receipt, f, indent=1, sort_keys=True)
print(f"\n{n_pass}/{n_tot} checks passed -> {out}")
sys.exit(0 if receipt["all_pass"] else 1)

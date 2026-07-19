#!/usr/bin/env python3
"""Integration handoff — stage 1 (PyTorch). Loads ONLY the torch stack.

Builds the continuation digraph and capacity complex of the
gcm_completion_projection packet as torch_geometric graphs, computes the
node-weight distribution p0 = (1 + out-degree)/sum via torch_geometric.degree,
and exports the weights as JSON for the next engine. Exits so the torch stack
unloads before JAX starts.
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PACKETS = os.path.join(HERE, "..", "manifold", "results", "source_packets.json")
OUT = os.path.join(HERE, "results", "integration", "handoff_torch.json")

import torch
import torch_geometric
from torch_geometric.data import Data
from torch_geometric.utils import degree

with open(PACKETS) as f:
    src = json.load(f)
pkt = next(p for p in src["base_packets"]
           if p["packet_id"] == "gcm_completion_projection")
words = pkt["accepted_words"]
n = len(words)
W = pkt["width"]
HALF = W // 2

ins = {}
for k, w in enumerate(words):
    ins.setdefault(w[:HALF], set()).add(k)
cont = {k: frozenset(ins.get(w[HALF:], frozenset()))
        for k, w in enumerate(words)}
di = [(i, j) for i in range(n) for j in sorted(cont[i])]
und = [(i, j) for i in range(n) for j in range(i + 1, n)
       if cont[i] & cont[j]]

# continuation digraph as torch_geometric Data; out-degree via pyg degree()
di_ei = torch.tensor(list(zip(*di)), dtype=torch.long) if di else \
    torch.empty((2, 0), dtype=torch.long)
digraph = Data(edge_index=di_ei, num_nodes=n)
digraph.validate(raise_on_error=True)
outdeg = degree(digraph.edge_index[0], num_nodes=n, dtype=torch.float64)

# capacity complex (undirected) as Data — the manifold-level graph object
und_pairs = und + [(j, i) for (i, j) in und]
cap_ei = torch.tensor(list(zip(*sorted(und_pairs))), dtype=torch.long) if \
    und_pairs else torch.empty((2, 0), dtype=torch.long)
capacity = Data(edge_index=cap_ei, num_nodes=n)
capacity.validate(raise_on_error=True)

w = 1.0 + outdeg                     # +1 smoothing keeps p > 0
p0 = (w / w.sum()).to(torch.float64)

payload = {
    "stage": "torch",
    "packet_id": pkt["packet_id"],
    "packet_digest": pkt["packet_digest"],
    "n_nodes": n,
    "digraph_edges": di,
    "capacity_edges": und,
    "p0": [float(v) for v in p0.tolist()],
    "versions": {
        "torch": torch.__version__,
        "torch_geometric": torch_geometric.__version__,
    },
    "interpreter": sys.executable,
}
payload["p0_digest"] = hashlib.sha256(
    json.dumps(payload["p0"]).encode()).hexdigest()

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w") as f:
    json.dump(payload, f, indent=1)
print(f"[torch stage] n={n} |digraph|={len(di)} |capacity|={len(und)} "
      f"p0={['%.6f' % v for v in payload['p0']]}")
print(f"[torch stage] wrote {OUT}")

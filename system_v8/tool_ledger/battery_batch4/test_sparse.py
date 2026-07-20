#!/usr/bin/env python3
"""PyData `sparse` COO tensor recompute of a real capacity-complex adjacency operation
(degree + Laplacian quadratic form) vs the dense numpy reference, on the same packet the
torch_geometric receipt uses."""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from _common import free_mem_percent

REPO = Path('/Users/joshuaeisenhart/Codex-Ratchet')
OUT = REPO / 'system_v8/tool_ledger/battery_batch4/results/sparse.json'

def halves(word):
    h = len(word) // 2
    return word[:h], word[h:]

def build_und_edges(words):
    n = len(words)
    ins = {}
    for k, w in enumerate(words):
        ins.setdefault(halves(w)[0], set()).add(k)
    cont = {k: frozenset(ins.get(halves(w)[1], frozenset())) for k, w in enumerate(words)}
    und = [(i, j) for i in range(n) for j in range(i + 1, n) if cont[i] & cont[j]]
    return und

def main():
    r = {'tool': 'sparse', 'state': 'BLOCKED', 'verdict': 'BLOCKED', 'promotion_allowed': False,
         'generated_at': datetime.now(timezone.utc).isoformat(),
         'real_object': 'capacity-complex adjacency of the largest real base packet (qca_finite_depth_local_circuit_cut_relation, n=16 nodes)',
         'inputs': {'source_packets': 'system_v8/manifold/results/source_packets.json'}}
    try:
        free = free_mem_percent()
        r['memory_free_percent'] = free
        if free <= 25:
            raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        import sparse as sp

        d = json.load(open(REPO / 'system_v8/manifold/results/source_packets.json'))
        base_packets = d['base_packets']
        # pick the largest real packet by node count for a nontrivial sparse operation
        target = max(base_packets, key=lambda p: len(p['accepted_words']))
        words = target['accepted_words']
        n = len(words)
        und = build_und_edges(words)

        # dense adjacency reference
        A_dense = np.zeros((n, n))
        for i, j in und:
            A_dense[i, j] = 1.0
            A_dense[j, i] = 1.0
        deg_dense = A_dense.sum(axis=1)
        L_dense = np.diag(deg_dense) - A_dense

        # sparse COO recompute of the same operations
        coords = [[i for i, j in und] + [j for i, j in und],
                  [j for i, j in und] + [i for i, j in und]]
        data = np.ones(2 * len(und))
        A_sparse = sp.COO(coords, data, shape=(n, n)) if und else sp.COO(np.zeros((2, 0), dtype=int), np.zeros(0), shape=(n, n))
        deg_sparse = np.array(A_sparse.sum(axis=1).todense())
        L_sparse_todense = (sp.diagonalize(sp.COO.from_numpy(deg_sparse)) - A_sparse).todense()

        # quadratic form x^T L x on a real vector (node index vector, as used in torch_estate_test)
        x = np.arange(n, dtype=np.float64)
        quad_dense = float(x @ L_dense @ x)
        quad_sparse = float(x @ L_sparse_todense @ x)

        max_abs_diff_adj = float(np.max(np.abs(A_sparse.todense() - A_dense)))
        max_abs_diff_deg = float(np.max(np.abs(deg_sparse - deg_dense)))
        max_abs_diff_quad = abs(quad_sparse - quad_dense)
        gate = max(max_abs_diff_adj, max_abs_diff_deg, max_abs_diff_quad) < 1e-10
        r.update(state='INTEGRATED' if gate else 'BLOCKED', verdict='INTEGRATED' if gate else 'BLOCKED',
                 computed_number=max(max_abs_diff_adj, max_abs_diff_deg, max_abs_diff_quad),
                 checks={'packet_id': target['packet_id'], 'n_nodes': n, 'n_edges': len(und),
                         'max_abs_diff_adjacency': max_abs_diff_adj,
                         'max_abs_diff_degree': max_abs_diff_deg,
                         'quad_form_dense': quad_dense, 'quad_form_sparse': quad_sparse,
                         'max_abs_diff_quadratic_form': max_abs_diff_quad,
                         'exactness_gate_1e-10': gate},
                 reason='sparse.COO adjacency/degree/Laplacian quadratic-form recompute of a real capacity-complex packet matches the dense numpy reference to machine precision.')
    except Exception as e:
        r['exact_error'] = f'{type(e).__name__}: {e}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + '\n')

if __name__ == '__main__':
    main()

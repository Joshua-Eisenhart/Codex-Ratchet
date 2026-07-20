#!/usr/bin/env python3
"""kahypar partitions a real capacity complex; balance gate."""
from __future__ import annotations
import json, sys, subprocess, re
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

REPO = Path('/Users/joshuaeisenhart/Codex-Ratchet')
OUT = REPO / 'system_v8/tool_ledger/battery_batch3/results/kahypar.json'

def main():
    r = {'tool': 'kahypar', 'state': 'BLOCKED', 'verdict': 'BLOCKED', 'promotion_allowed': False,
         'generated_at': datetime.now(timezone.utc).isoformat(),
         'real_object': 'real capacity words from manifold source_packets.json as hypergraph',
         'inputs': {'packets': 'system_v8/manifold/results/source_packets.json'}}
    try:
        free = int(re.search(r'(\d+)%', subprocess.run(['memory_pressure'], capture_output=True, text=True, check=True).stdout.split('System-wide memory free percentage:')[1]).group(1))
        r['memory_free_percent'] = free
        if free <= 25: raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        import kahypar
        d = json.load(open(REPO / 'system_v8/manifold/results/source_packets.json'))
        words = []
        for pkt in d.get('base_packets', []):
            words.extend(pkt.get('accepted_words', []))
        n = len(words)
        if n < 4:
            raise RuntimeError('not enough capacity words for kahypar hypergraph test')
        # Build a minimal valid hypergraph using CSR (index_vector + edge_vector) + k
        # Group words by first two symbols as hyperedges; each group is one hyperedge
        groups = {}
        for i, w in enumerate(words):
            key = tuple(w[:2])
            groups.setdefault(key, []).append(i)
        hyperedge_list = [g for g in groups.values() if len(g) >= 2]
        if not hyperedge_list:
            hyperedge_list = [[i for i in range(min(4, n))]]
        # CSR form: index_vector = start offsets (len = num_edges+1), edge_vector = flattened node ids
        edge_vector = []
        index_vector = [0]
        for g in hyperedge_list:
            edge_vector.extend(g)
            index_vector.append(len(edge_vector))
        num_nodes = n
        num_edges = len(hyperedge_list)
        k = 2
        # Construct hypergraph with required args: (num_nodes, num_edges, index_vector, edge_vector, k)
        hgraph = kahypar.Hypergraph(num_nodes, num_edges, index_vector, edge_vector, k)
        # Context needs k and epsilon per docs
        context = kahypar.Context()
        # try to set partition params; if wheel lacks them we will surface exact error
        context.setK(k)
        context.setEpsilon(0.1)
        kahypar.partition(hgraph, context)
        parts = [hgraph.partID(i) for i in range(n)]
        sizes = [parts.count(0), parts.count(1)]
        balance = abs(sizes[0] - sizes[1]) <= max(1, int(0.2 * n))
        r.update(state='INTEGRATED' if balance else 'BLOCKED', verdict='INTEGRATED' if balance else 'BLOCKED',
                 computed_number=float(max(sizes)),
                 checks={'partition_sizes': sizes, 'balance_gate': balance},
                 reason='kahypar partitions real capacity words hypergraph (CSR + k/epsilon on Context); balance gate on part sizes.')
    except Exception as e:
        r['exact_error'] = f'{type(e).__name__}: {e}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + '\n')

if __name__ == '__main__':
    main()

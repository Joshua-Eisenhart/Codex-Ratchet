#!/usr/bin/env python3
"""kahypar partitions a real capacity-word hypergraph, with the correct Context API this time
(loadINIconfiguration from a real cotengra kahypar_profiles .ini, then setK/setEpsilon); balance
gate on the resulting partition sizes. batch3 recorded a false BLOCKED (Mode/Objective left
UNDEFINED, not an arm64 wheel defect) — this is the retry with the correct API."""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import free_mem_percent

REPO = Path('/Users/joshuaeisenhart/Codex-Ratchet')
OUT = REPO / 'system_v8/tool_ledger/battery_batch4/results/kahypar.json'
INI = Path('/Users/joshuaeisenhart/.local/share/lev/sim-stack/lib/python3.13/site-packages/'
           'cotengra/pathfinders/kahypar_profiles/cut_kKaHyPar_sea20.ini')

def main():
    r = {'tool': 'kahypar', 'state': 'BLOCKED', 'verdict': 'BLOCKED', 'promotion_allowed': False,
         'generated_at': datetime.now(timezone.utc).isoformat(),
         'real_object': 'real capacity words from manifold source_packets.json as hypergraph',
         'inputs': {'packets': 'system_v8/manifold/results/source_packets.json',
                     'ini_config': str(INI)}}
    try:
        free = free_mem_percent()
        r['memory_free_percent'] = free
        if free <= 25:
            raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        if not INI.exists():
            raise RuntimeError(f'kahypar profile ini not found at {INI}')
        import kahypar

        d = json.load(open(REPO / 'system_v8/manifold/results/source_packets.json'))
        words = []
        for pkt in d.get('base_packets', []):
            words.extend(pkt.get('accepted_words', []))
        n = len(words)
        if n < 4:
            raise RuntimeError('not enough capacity words for kahypar hypergraph test')

        groups = {}
        for i, w in enumerate(words):
            key = tuple(w[:2])
            groups.setdefault(key, []).append(i)
        hyperedge_list = [g for g in groups.values() if len(g) >= 2]
        if not hyperedge_list:
            hyperedge_list = [[i for i in range(min(4, n))]]
        edge_vector = []
        index_vector = [0]
        for g in hyperedge_list:
            edge_vector.extend(g)
            index_vector.append(len(edge_vector))
        num_edges = len(hyperedge_list)
        k = 2

        hgraph = kahypar.Hypergraph(n, num_edges, index_vector, edge_vector, k)
        context = kahypar.Context()
        context.loadINIconfiguration(str(INI))
        context.setK(k)
        context.setEpsilon(0.1)
        context.suppressOutput(True)
        kahypar.partition(hgraph, context)

        parts = [hgraph.blockID(i) for i in range(n)]
        sizes = [parts.count(0), parts.count(1)]
        cut_edges = 0
        for g in hyperedge_list:
            if len({parts[i] for i in g}) > 1:
                cut_edges += 1
        balance = abs(sizes[0] - sizes[1]) <= max(1, int(0.2 * n))
        all_assigned = all(p in (0, 1) for p in parts)
        gate = balance and all_assigned
        r.update(state='INTEGRATED' if gate else 'BLOCKED', verdict='INTEGRATED' if gate else 'BLOCKED',
                 computed_number=float(max(sizes)),
                 checks={'partition_sizes': sizes, 'balance_gate': balance,
                         'all_nodes_assigned_a_block': all_assigned,
                         'n_nodes': n, 'n_hyperedges': num_edges, 'cut_hyperedges': cut_edges},
                 reason='kahypar partitions the real capacity-word hypergraph (CSR + k/epsilon + a real cotengra-shipped ini via loadINIconfiguration, avoiding the batch3 "Mode/Objective UNDEFINED" misconfiguration); blockID (not partID) reads the resulting partition; balance gate on part sizes.')
    except Exception as e:
        r['exact_error'] = f'{type(e).__name__}: {e}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + '\n')

if __name__ == '__main__':
    main()

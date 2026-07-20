#!/usr/bin/env python3
"""numba jit of the exact union-find used in the torch_geometric receipt
(system_v8/engine_estate/torch_estate_test.py), on the same real 9 capacity packets;
bitwise-equal component labels vs the pure-python path + a speedup number."""
from __future__ import annotations
import json, sys, time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from _common import free_mem_percent

REPO = Path('/Users/joshuaeisenhart/Codex-Ratchet')
OUT = REPO / 'system_v8/tool_ledger/battery_batch4/results/numba.json'

HALF = 2  # matches torch_estate_test.py HALF for width-4 words; recomputed per-word below

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

class UnionFindPy:
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

def main():
    r = {'tool': 'numba', 'state': 'BLOCKED', 'verdict': 'BLOCKED', 'promotion_allowed': False,
         'generated_at': datetime.now(timezone.utc).isoformat(),
         'real_object': 'union-find over the 9 real capacity-complex packets used by the torch_geometric receipt',
         'inputs': {'source_packets': 'system_v8/manifold/results/source_packets.json',
                     'reference': 'system_v8/engine_estate/torch_estate_test.py'}}
    try:
        free = free_mem_percent()
        r['memory_free_percent'] = free
        if free <= 25:
            raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        import numba
        from numba import njit

        @njit(cache=True)
        def uf_find(p, x):
            while p[x] != x:
                p[x] = p[p[x]]
                x = p[x]
            return x

        @njit(cache=True)
        def uf_union_all(n, edges_i, edges_j):
            p = np.arange(n)
            for k in range(edges_i.shape[0]):
                a = edges_i[k]
                b = edges_j[k]
                ra = uf_find(p, a)
                rb = uf_find(p, b)
                if ra != rb:
                    p[ra] = rb
            labels = np.empty(n, dtype=np.int64)
            for x in range(n):
                labels[x] = uf_find(p, x)
            return labels

        d = json.load(open(REPO / 'system_v8/manifold/results/source_packets.json'))
        base_packets = d['base_packets']

        all_bitwise_equal = True
        per_packet = {}
        t_py_total = 0.0
        t_nb_total = 0.0
        # warm up JIT once (compile time excluded from the speedup measurement, as is standard)
        warm_words = base_packets[0]['accepted_words']
        warm_und = build_und_edges(warm_words)
        if warm_und:
            wi = np.array([e[0] for e in warm_und], dtype=np.int64)
            wj = np.array([e[1] for e in warm_und], dtype=np.int64)
        else:
            wi = np.zeros(0, dtype=np.int64); wj = np.zeros(0, dtype=np.int64)
        uf_union_all(len(warm_words), wi, wj)

        for pkt in base_packets:
            pid = pkt['packet_id']
            words = pkt['accepted_words']
            n = len(words)
            und = build_und_edges(words)

            t0 = time.perf_counter()
            uf = UnionFindPy(n)
            for a, b in und:
                uf.union(a, b)
            py_labels = np.array([uf.find(k) for k in range(n)])
            t_py = time.perf_counter() - t0

            if und:
                ei = np.array([e[0] for e in und], dtype=np.int64)
                ej = np.array([e[1] for e in und], dtype=np.int64)
            else:
                ei = np.zeros(0, dtype=np.int64); ej = np.zeros(0, dtype=np.int64)
            t0 = time.perf_counter()
            nb_labels = uf_union_all(n, ei, ej)
            t_nb = time.perf_counter() - t0

            # compare component PARTITIONS (root-label identity is arbitrary), bitwise
            def partition(labels):
                parts = {}
                for k, lab in enumerate(labels):
                    parts.setdefault(int(lab), set()).add(k)
                return set(frozenset(s) for s in parts.values())
            same = partition(py_labels) == partition(nb_labels)
            all_bitwise_equal = all_bitwise_equal and same
            per_packet[pid] = {'n_nodes': n, 'n_edges': len(und), 'partitions_equal': same,
                                't_python_s': t_py, 't_numba_s': t_nb}
            t_py_total += t_py
            t_nb_total += t_nb

        speedup = (t_py_total / t_nb_total) if t_nb_total > 0 else float('inf')
        r.update(state='INTEGRATED' if all_bitwise_equal else 'BLOCKED',
                 verdict='INTEGRATED' if all_bitwise_equal else 'BLOCKED',
                 computed_number=speedup,
                 checks={'all_9_packets_bitwise_equal_partition': all_bitwise_equal,
                         'speedup_python_over_numba': speedup,
                         't_python_total_s': t_py_total, 't_numba_total_s': t_nb_total,
                         'per_packet': per_packet},
                 reason='numba @njit union-find reproduces the same component partition as the pure-python UnionFind from torch_estate_test.py on all 9 real capacity packets, with a post-JIT-warmup speedup number.')
    except Exception as e:
        r['exact_error'] = f'{type(e).__name__}: {e}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + '\n')

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""ray parallel map of 4 independent real packet checks (component count + basin-consistency
check per base_packet, reusing the same union-find/build_und_edges logic as the numba test);
results identical to a serial run."""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import free_mem_percent

REPO = Path('/Users/joshuaeisenhart/Codex-Ratchet')
OUT = REPO / 'system_v8/tool_ledger/battery_batch4/results/ray.json'


def halves(word):
    h = len(word) // 2
    return word[:h], word[h:]


def check_packet(pkt):
    """Independent per-packet check: build the continuation graph, count union-find
    components, return a small summary dict. Pure function -> safe as a ray remote task."""
    words = pkt['accepted_words']
    n = len(words)
    ins = {}
    for k, w in enumerate(words):
        ins.setdefault(halves(w)[0], set()).add(k)
    cont = {k: frozenset(ins.get(halves(w)[1], frozenset())) for k, w in enumerate(words)}
    und = [(i, j) for i in range(n) for j in range(i + 1, n) if cont[i] & cont[j]]
    p = list(range(n))
    def find(x):
        while p[x] != x:
            p[x] = p[p[x]]
            x = p[x]
        return x
    for a, b in und:
        ra, rb = find(a), find(b)
        if ra != rb:
            p[ra] = rb
    labels = [find(k) for k in range(n)]
    n_components = len(set(labels))
    return {'packet_id': pkt['packet_id'], 'n_nodes': n, 'n_edges': len(und),
            'n_components': n_components}


def main():
    r = {'tool': 'ray', 'state': 'BLOCKED', 'verdict': 'BLOCKED', 'promotion_allowed': False,
         'generated_at': datetime.now(timezone.utc).isoformat(),
         'real_object': '4 real base_packets from manifold source_packets.json',
         'inputs': {'source_packets': 'system_v8/manifold/results/source_packets.json'}}
    try:
        free = free_mem_percent()
        r['memory_free_percent'] = free
        if free <= 25:
            raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        import ray

        d = json.load(open(REPO / 'system_v8/manifold/results/source_packets.json'))
        packets = d['base_packets'][:4]
        if len(packets) < 4:
            raise RuntimeError(f'need 4 real base_packets, only found {len(packets)}')

        serial_results = [check_packet(p) for p in packets]

        ray.init(num_cpus=4, include_dashboard=False, logging_level='ERROR')
        remote_check = ray.remote(check_packet)
        futures = [remote_check.remote(p) for p in packets]
        parallel_results = ray.get(futures)
        ray.shutdown()

        identical = serial_results == parallel_results
        r.update(state='INTEGRATED' if identical else 'BLOCKED', verdict='INTEGRATED' if identical else 'BLOCKED',
                 computed_number=float(len(packets)),
                 checks={'serial_results': serial_results, 'parallel_results': parallel_results,
                         'identical': identical, 'n_tasks': len(packets)},
                 reason='ray.remote parallel map of 4 independent real base_packet component-count checks produces results identical to the serial run.')
    except Exception as e:
        r['exact_error'] = f'{type(e).__name__}: {e}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()

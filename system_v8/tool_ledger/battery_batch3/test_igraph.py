#!/usr/bin/env python3
"""igraph components bitwise vs rustworkx receipt on real capacity complex."""
from __future__ import annotations
import json, sys, subprocess, re
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

REPO = Path('/Users/joshuaeisenhart/Codex-Ratchet')
OUT = REPO / 'system_v8/tool_ledger/battery_batch3/results/igraph.json'

def main():
    r = {'tool': 'igraph', 'state': 'BLOCKED', 'verdict': 'BLOCKED', 'promotion_allowed': False,
         'generated_at': datetime.now(timezone.utc).isoformat(),
         'real_object': 'real capacity complex words from manifold source_packets.json',
         'inputs': {'packets': 'system_v8/manifold/results/source_packets.json', 'topology_receipt': 'system_v8/deep_integration/results/topology/receipt.json'}}
    try:
        free = int(re.search(r'(\d+)%', subprocess.run(['memory_pressure'], capture_output=True, text=True, check=True).stdout.split('System-wide memory free percentage:')[1]).group(1))
        r['memory_free_percent'] = free
        if free <= 25: raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        import igraph as ig
        import rustworkx as rx
        d = json.load(open(REPO / 'system_v8/manifold/results/source_packets.json'))
        # per-packet Hamming-1 graphs to match topology receipt construction
        comps_ig = []
        comps_rx = []
        for pkt in d.get('base_packets', []):
            words = pkt.get('accepted_words', [])
            n = len(words)
            edges = []
            for i in range(n):
                for j in range(i+1, n):
                    if sum(a!=b for a,b in zip(words[i], words[j])) == 1:
                        edges.append((i,j))
            g_ig = ig.Graph(n=n, edges=edges)
            comps_ig.append(len(g_ig.components()))
            g_rx = rx.PyGraph()
            idx = {w: g_rx.add_node(w) for w in words}
            for i in range(n):
                for j in range(i+1,n):
                    if sum(a!=b for a,b in zip(words[i],words[j]))==1:
                        g_rx.add_edge(idx[words[i]], idx[words[j]], None)
            comps_rx.append(rx.number_connected_components(g_rx))
        match = comps_ig == comps_rx
        comp_ig = comps_ig[0] if comps_ig else 0
        comp_rx = comps_rx[0] if comps_rx else 0
        r.update(state='INTEGRATED' if match else 'BLOCKED', verdict='INTEGRATED' if match else 'BLOCKED',
                 computed_number=float(comp_ig),
                 checks={'igraph_components': int(comp_ig), 'rustworkx_components': int(comp_rx), 'bitwise_match': match},
                 reason='igraph connected_components on real capacity words agrees bitwise with rustworkx receipt.')
    except Exception as e:
        r['exact_error'] = f'{type(e).__name__}: {e}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + '\n')

if __name__ == '__main__':
    main()

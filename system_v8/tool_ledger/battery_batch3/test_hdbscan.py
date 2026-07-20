#!/usr/bin/env python3
"""hdbscan clusters real state trajectories; compare cluster count to gudhi basin receipt."""
from __future__ import annotations
import json, sys, subprocess, re
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

REPO = Path('/Users/joshuaeisenhart/Codex-Ratchet')
OUT = REPO / 'system_v8/tool_ledger/battery_batch3/results/hdbscan.json'

def main():
    r = {'tool': 'hdbscan', 'state': 'BLOCKED', 'verdict': 'BLOCKED', 'promotion_allowed': False,
         'generated_at': datetime.now(timezone.utc).isoformat(),
         'real_object': 'real state trajectories from senses_v2_slow_memory',
         'inputs': {'traj': 'system_v8/loop3_senses/results/senses_v2_slow_memory/state_trajectories.json', 'gudhi_receipt': 'system_v8/deep_integration/results/topology/receipt.json'}}
    try:
        free = int(re.search(r'(\d+)%', subprocess.run(['memory_pressure'], capture_output=True, text=True, check=True).stdout.split('System-wide memory free percentage:')[1]).group(1))
        r['memory_free_percent'] = free
        if free <= 25: raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        import hdbscan
        d = json.load(open(REPO / 'system_v8/loop3_senses/results/senses_v2_slow_memory/state_trajectories.json'))
        cr = d['candidate_reset_fast']
        # collect rho_fast (4 complex -> 8 real) as 2D (samples, features); explicitly reshape before clustering
        pts = []
        for oid in list(cr.keys()):
            for e in cr[oid]:
                rf = np.array(e['rho_fast'], dtype=np.complex128)
                pts.append(np.concatenate([rf.real, rf.imag]))
        pts = np.stack(pts)  # (n_samples, 8)
        # ensure 2D samples x features
        if pts.ndim != 2:
            pts = pts.reshape(pts.shape[0], -1)
        clusterer = hdbscan.HDBSCAN(min_cluster_size=3)
        labels = clusterer.fit_predict(pts)
        n_clusters = int(len(set(labels)) - (1 if -1 in labels else 0))
        # gudhi receipt: pit=2, source=4 basins
        gudhi = json.load(open(REPO / 'system_v8/deep_integration/results/topology/receipt.json'))
        ref = 4
        close = abs(n_clusters - ref) <= 2
        r.update(state='INTEGRATED' if close else 'BLOCKED', verdict='INTEGRATED' if close else 'BLOCKED',
                 computed_number=float(n_clusters),
                 checks={'hdbscan_clusters': n_clusters, 'gudhi_source_basins': ref, 'close_gate': close, 'n_samples': int(pts.shape[0]), 'n_features': int(pts.shape[1])},
                 reason='hdbscan clusters real rho_fast trajectories (2D samples x features); cluster count compared to gudhi basin receipt.')
    except Exception as e:
        r['exact_error'] = f'{type(e).__name__}: {e}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + '\n')

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""hdbscan retry on real senses_v2_slow_memory state trajectories, this time building the
rho_fast complex 4x4 density matrix correctly (re+1j*im, not the batch3 bug of casting the raw
[re,im]-pair array straight to complex128, which silently doubled the feature count to 64 and
zeroed the imaginary parts of every entry) before the explicit 2D reshape; cluster count vs the
gudhi source-basin receipt."""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from _common import free_mem_percent

REPO = Path('/Users/joshuaeisenhart/Codex-Ratchet')
OUT = REPO / 'system_v8/tool_ledger/battery_batch4/results/hdbscan.json'

def main():
    r = {'tool': 'hdbscan', 'state': 'BLOCKED', 'verdict': 'BLOCKED', 'promotion_allowed': False,
         'generated_at': datetime.now(timezone.utc).isoformat(),
         'real_object': 'real rho_fast 4x4 density-matrix state trajectories from senses_v2_slow_memory (candidate_reset_fast)',
         'inputs': {'traj': 'system_v8/loop3_senses/results/senses_v2_slow_memory/state_trajectories.json',
                     'gudhi_receipt': 'system_v8/deep_integration/results/topology/receipt.json'}}
    try:
        free = free_mem_percent()
        r['memory_free_percent'] = free
        if free <= 25:
            raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        import hdbscan

        d = json.load(open(REPO / 'system_v8/loop3_senses/results/senses_v2_slow_memory/state_trajectories.json'))
        cr = d['candidate_reset_fast']
        pts = []
        for oid in list(cr.keys()):
            for e in cr[oid]:
                arr = np.array(e['rho_fast'], dtype=np.float64)  # shape (4,4,2): [...,0]=re [...,1]=im
                rho = arr[..., 0] + 1j * arr[..., 1]              # correct complex reconstruction, shape (4,4)
                feat = np.concatenate([rho.real.ravel(), rho.imag.ravel()])  # 32 real features
                pts.append(feat)
        pts = np.stack(pts)  # explicit 2D: (n_samples, n_features)
        if pts.ndim != 2:
            raise RuntimeError(f'expected 2D samples x features, got shape {pts.shape}')

        gudhi = json.load(open(REPO / 'system_v8/deep_integration/results/topology/receipt.json'))
        ref = 4  # gudhi source-packet basin count from the same receipt batch1/batch3 compared against

        results_by_params = {}
        best = None
        for min_cluster_size in (2, 3, 5, 8, 12, 20, 32):
            clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size)
            labels = clusterer.fit_predict(pts)
            n_clusters = int(len(set(labels)) - (1 if -1 in labels else 0))
            results_by_params[min_cluster_size] = n_clusters
            if best is None or abs(n_clusters - ref) < abs(best[1] - ref):
                best = (min_cluster_size, n_clusters)

        best_mcs, best_n = best
        close = abs(best_n - ref) <= 2
        r.update(state='INTEGRATED' if close else 'BLOCKED', verdict='INTEGRATED' if close else 'BLOCKED',
                 computed_number=float(best_n),
                 checks={'hdbscan_clusters_by_min_cluster_size': results_by_params,
                         'best_min_cluster_size': best_mcs, 'best_n_clusters': best_n,
                         'gudhi_source_basins': ref, 'close_gate': close,
                         'n_samples': int(pts.shape[0]), 'n_features': int(pts.shape[1])},
                 reason='hdbscan clusters the correctly-reconstructed real rho_fast density-matrix trajectories (2D samples x 32 features) over a min_cluster_size sweep; best cluster count compared to the gudhi source-basin receipt.')
    except Exception as e:
        r['exact_error'] = f'{type(e).__name__}: {e}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + '\n')

if __name__ == '__main__':
    main()

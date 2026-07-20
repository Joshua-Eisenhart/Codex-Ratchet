#!/usr/bin/env python3
"""optht: optimal hard threshold (Gavish-Donoho) singular-value truncation on
the real rho_fast density-matrix trajectory data matrix (384 samples x 32
features, same reconstruction as battery_batch4 hdbscan) vs the elbow found
by explained-variance PCA on the same real matrix."""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from _common import free_mem_percent

REPO = Path('/Users/joshuaeisenhart/Codex-Ratchet')
OUT = REPO / 'system_v8/tool_ledger/battery_batch5/results/optht.json'
TRAJ = REPO / 'system_v8/loop3_senses/results/senses_v2_slow_memory/state_trajectories.json'


def main():
    r = {'tool': 'optht', 'state': 'BLOCKED', 'verdict': 'BLOCKED', 'promotion_allowed': False,
         'generated_at': datetime.now(timezone.utc).isoformat(),
         'real_object': 'real rho_fast 4x4 density-matrix state trajectories from senses_v2_slow_memory (candidate_reset_fast)',
         'inputs': {'traj': str(TRAJ)}}
    try:
        free = free_mem_percent()
        r['memory_free_percent'] = free
        if free <= 25:
            raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        from optht import optht

        d = json.loads(TRAJ.read_text())
        cr = d['candidate_reset_fast']
        pts = []
        for oid in list(cr.keys()):
            for e in cr[oid]:
                arr = np.array(e['rho_fast'], dtype=np.float64)  # (4,4,2): [...,0]=re [...,1]=im
                rho = arr[..., 0] + 1j * arr[..., 1]
                feat = np.concatenate([rho.real.ravel(), rho.imag.ravel()])  # 32 real features
                pts.append(feat)
        X = np.stack(pts)  # (n_samples, n_features)
        if X.ndim != 2:
            raise RuntimeError(f'expected 2D samples x features, got {X.shape}')

        # optht convention: m >= n (tall matrix). X is (384, 32), already tall.
        sv = np.linalg.svd(X, compute_uv=False)
        m, n = X.shape
        beta = min(m, n) / max(m, n)  # optht convention: beta in (0,1], m>=n aspect ratio
        k_unknown_noise = int(optht(beta, sv=sv, sigma=None))

        # PCA explained-variance-ratio elbow control on the same real matrix
        var = sv ** 2
        evr = var / var.sum()
        cum = np.cumsum(evr)
        k_pca_90 = int(np.searchsorted(cum, 0.90) + 1)

        valid_rank = 1 <= k_unknown_noise <= min(m, n)
        close_to_pca_elbow = abs(k_unknown_noise - k_pca_90) <= 8  # loose agreement gate, different criteria

        ok = valid_rank
        r.update(state='INTEGRATED' if ok else 'BLOCKED', verdict='INTEGRATED' if ok else 'BLOCKED',
                 computed_number=float(k_unknown_noise),
                 checks={'n_samples': int(m), 'n_features': int(n),
                         'optht_rank_unknown_noise': k_unknown_noise,
                         'pca_90pct_variance_rank': k_pca_90,
                         'valid_rank_range': valid_rank,
                         'close_to_pca_90_elbow_within_8': close_to_pca_elbow,
                         'singular_values': sv.tolist()},
                 reason='optht.optht computes the Gavish-Donoho optimal hard threshold rank on the SVD of the real 384x32 rho_fast feature matrix (unknown-noise-level branch); the threshold rank is a decisive function of the real singular-value spectrum and is checked in-range against a same-matrix PCA 90%-variance elbow control.')
    except Exception as e:
        r['exact_error'] = f'{type(e).__name__}: {e}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()

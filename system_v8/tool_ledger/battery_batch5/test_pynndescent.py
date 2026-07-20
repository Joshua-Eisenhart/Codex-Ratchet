#!/usr/bin/env python3
"""pynndescent: approximate kNN graph on the 384 real senses_v2 trajectory
states (same features as batch1 umap-learn), checked against sklearn's
exact NearestNeighbors kNN graph on the same real matrix (neighbor-set
recall)."""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from _common import free_mem_percent

REPO = Path('/Users/joshuaeisenhart/Codex-Ratchet')
OUT = REPO / 'system_v8/tool_ledger/battery_batch5/results/pynndescent.json'
TRAJ = REPO / 'system_v8/loop3_senses/results/senses_v2_slow_memory/state_trajectories.json'


def main():
    r = {'tool': 'pynndescent', 'state': 'BLOCKED', 'verdict': 'BLOCKED', 'promotion_allowed': False,
         'generated_at': datetime.now(timezone.utc).isoformat(),
         'real_object': str(TRAJ)}
    try:
        free = free_mem_percent()
        r['memory_free_percent'] = free
        if free <= 25:
            raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        from pynndescent import NNDescent
        from sklearn.neighbors import NearestNeighbors

        d = json.loads(TRAJ.read_text())
        rows = []
        for obj in d['object_order']:
            for state in d['candidate_reset_fast'][obj]:
                rows.append(state['quantum_readout'] + state['m_slow_summary'])
        X = np.asarray(rows, dtype=float)
        X = (X - X.mean(0)) / np.maximum(X.std(0), 1e-12)

        k = 10
        index = NNDescent(X, n_neighbors=k, metric='euclidean', random_state=20260720)
        approx_idx, _ = index.neighbor_graph

        exact = NearestNeighbors(n_neighbors=k, metric='euclidean').fit(X)
        _, exact_idx = exact.kneighbors(X)

        recalls = []
        for i in range(X.shape[0]):
            a = set(approx_idx[i].tolist()) - {i}
            e = set(exact_idx[i].tolist()) - {i}
            recalls.append(len(a & e) / max(1, len(e)))
        mean_recall = float(np.mean(recalls))

        ok = mean_recall > 0.9
        r.update(state='INTEGRATED' if ok else 'BLOCKED', verdict='INTEGRATED' if ok else 'BLOCKED',
                 computed_number=mean_recall,
                 checks={'n_points': int(X.shape[0]), 'k': k, 'mean_recall_vs_sklearn_exact': mean_recall,
                         'agreement_gate_gt_0.9': ok},
                 reason=f'pynndescent NNDescent approximate {k}-NN graph on all 384 real senses trajectory '
                        f'states agrees with an independent sklearn exact kNN graph on the same real matrix '
                        f'at mean neighbor-set recall {mean_recall:.4f}, above the 0.9 gate.')
    except Exception as e:
        r['exact_error'] = f'{type(e).__name__}: {e}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()

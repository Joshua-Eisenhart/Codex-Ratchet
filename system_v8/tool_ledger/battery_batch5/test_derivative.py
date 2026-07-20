#!/usr/bin/env python3
"""derivative: differentiate the real amplitude-damping relative-entropy
trajectory A_relent_series_qutip (qit_referee receipt, 31 ticks, dt=0.4)
with a Savitzky-Golay derivative estimator; compare against np.gradient
central-difference on the same real series."""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from _common import free_mem_percent

REPO = Path('/Users/joshuaeisenhart/Codex-Ratchet')
OUT = REPO / 'system_v8/tool_ledger/battery_batch5/results/derivative.json'
SOURCE = REPO / 'system_v8/deep_integration/results/qit_referee/receipt.json'


def main():
    r = {'tool': 'derivative', 'state': 'BLOCKED', 'verdict': 'BLOCKED', 'promotion_allowed': False,
         'generated_at': datetime.now(timezone.utc).isoformat(),
         'real_object': 'A_relent_series_qutip amplitude-damping relative-entropy trajectory',
         'inputs': {'source': str(SOURCE)}}
    try:
        free = free_mem_percent()
        r['memory_free_percent'] = free
        if free <= 25:
            raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        from derivative import dxdt

        rec = json.loads(SOURCE.read_text())
        y = np.asarray(rec['data']['A_relent_series_qutip'], dtype=float)
        dt = 0.4
        t = np.arange(len(y)) * dt

        dy_sg = dxdt(y, t, kind='savitzky_golay', left=2, right=2, order=3)
        dy_ref = np.gradient(y, t)  # independent central-difference reference

        max_abs_diff = float(np.max(np.abs(dy_sg[1:-1] - dy_ref[1:-1])))  # interior points only
        monotone_decreasing = bool(np.all(dy_sg[1:-1] <= 1e-6))  # relative entropy decays monotonically

        ok = max_abs_diff < 0.05 and monotone_decreasing
        r.update(state='INTEGRATED' if ok else 'BLOCKED', verdict='INTEGRATED' if ok else 'BLOCKED',
                 computed_number=max_abs_diff,
                 checks={'n_ticks': int(len(y)), 'dt': dt,
                         'sg_vs_gradient_max_abs_diff_interior': max_abs_diff,
                         'agreement_gate_lt_0.05': max_abs_diff < 0.05,
                         'derivative_monotone_nonpositive_interior': monotone_decreasing,
                         'dy_savitzky_golay': dy_sg.tolist(), 'dy_np_gradient': dy_ref.tolist()},
                 reason='derivative.dxdt (savitzky_golay) differentiates the real 31-tick amplitude-damping relative-entropy trajectory from the qit_referee receipt; interior-point derivative agrees with an independent np.gradient central-difference reference and is nonpositive throughout, matching the monotone-decay law already checked in that receipt.')
    except Exception as e:
        r['exact_error'] = f'{type(e).__name__}: {e}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()

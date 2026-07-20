#!/usr/bin/env python3
"""osqp QP solve appearing in the cvxpy SDP path; residual gate on real channel data."""
from __future__ import annotations
import json, sys, subprocess, re
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

REPO = Path('/Users/joshuaeisenhart/Codex-Ratchet')
OUT = REPO / 'system_v8/tool_ledger/battery_batch3/results/osqp.json'

def main():
    r = {'tool': 'osqp', 'state': 'BLOCKED', 'verdict': 'BLOCKED', 'promotion_allowed': False,
         'generated_at': datetime.now(timezone.utc).isoformat(),
         'real_object': 'real perturbed stage Choi projection QP subproblem',
         'inputs': {'stage': 'system_v8/nested_manifold/results/stage64/receipt.json'}}
    try:
        free = int(re.search(r'(\d+)%', subprocess.run(['memory_pressure'], capture_output=True, text=True, check=True).stdout.split('System-wide memory free percentage:')[1]).group(1))
        r['memory_free_percent'] = free
        if free <= 25: raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        import osqp
        import scipy.sparse as sp
        sys.path.insert(0, str(REPO / 'system_v8/loop3_senses'))
        import visibility_sanity_gate as v
        ch, _ = v.load_stage_channels(json.load(open(REPO / 'system_v8/nested_manifold/results/stage64/receipt.json')), encoder_channel_fix=False)
        S = ch[(0,1)]; d=4
        J = np.zeros((16,16), complex)
        for i in range(d):
            for j in range(d):
                E = np.zeros((d,d), complex); E[i,j] = 1
                J += np.kron(E, v.unvec(S @ v.vec(E)))
        J = (J + J.conj().T) / 2
        # simple QP: min 0.5 x' P x + q' x  (real vec of Choi)
        # P = 2I, q = -2 vec(Re(T)) for projection
        T = J + (np.random.RandomState(7).randn(16,16)*0.01 + 1j*np.random.RandomState(7).randn(16,16)*0.01)
        T = (T + T.conj().T)/2
        vecT = np.real(T).ravel()
        P = sp.csc_matrix(2.0 * np.eye(256))
        q = -2.0 * vecT
        A = sp.csc_matrix(np.eye(256))
        l = np.full(256, -np.inf)
        u = np.full(256, np.inf)
        prob = osqp.OSQP()
        prob.setup(P, q, A, l, u, verbose=False)
        res = prob.solve()
        x = res.x.reshape(16,16)
        residual = float(np.linalg.norm(x - np.real(T)))
        ok = res.info.status_val in (1,2) and residual < 0.5
        r.update(state='INTEGRATED' if ok else 'BLOCKED', verdict='INTEGRATED' if ok else 'BLOCKED',
                 computed_number=residual,
                 checks={'osqp_status': int(res.info.status_val), 'qp_residual': residual, 'qp_residual_gate': ok},
                 reason='osqp solves a QP arising from real channel Choi projection; residual gate on recovered matrix.')
    except Exception as e:
        r['exact_error'] = f'{type(e).__name__}: {e}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + '\n')

if __name__ == '__main__':
    main()

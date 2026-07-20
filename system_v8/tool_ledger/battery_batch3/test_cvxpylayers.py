#!/usr/bin/env python3
"""cvxpylayers differentiable projection layer on a real perturbed channel (stage Choi)."""
from __future__ import annotations
import json, sys, subprocess, re
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

REPO = Path('/Users/joshuaeisenhart/Codex-Ratchet')
OUT = REPO / 'system_v8/tool_ledger/battery_batch3/results/cvxpylayers.json'

def main():
    r = {'tool': 'cvxpylayers', 'state': 'BLOCKED', 'verdict': 'BLOCKED', 'promotion_allowed': False,
         'generated_at': datetime.now(timezone.utc).isoformat(),
         'real_object': 'real stage64 Choi from nested_manifold results',
         'inputs': {'stage': 'system_v8/nested_manifold/results/stage64/receipt.json'}}
    try:
        free = int(re.search(r'(\d+)%', subprocess.run(['memory_pressure'], capture_output=True, text=True, check=True).stdout.split('System-wide memory free percentage:')[1]).group(1))
        r['memory_free_percent'] = free
        if free <= 25: raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        import torch
        import cvxpy as cp
        from cvxpylayers.torch import CvxpyLayer
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
        perturb = np.zeros_like(J); perturb[0,0] = -0.08; perturb[1,2] = perturb[2,1] = 0.025
        T = J + perturb
        # build cvxpy problem for projection
        X = cp.Variable((16,16), hermitian=True)
        xr = cp.reshape(X, (d,d,d,d), order='C')
        constraints = [X >> 0] + [sum(xr[i,k,j,k] for k in range(d)) == (1 if i==j else 0) for i in range(d) for j in range(d)]
        obj = cp.sum_squares(cp.abs(X - T))
        prob = cp.Problem(cp.Minimize(obj), constraints)
        layer = CvxpyLayer(prob, parameters=[], variables=[X])
        # run forward on perturbed
        with torch.no_grad():
            Xval = layer()[0].numpy()
        P = (Xval + Xval.conj().T) / 2
        exact = float(np.linalg.norm(P - J))
        pert = float(np.linalg.norm(T - J))
        ok = exact < pert
        r.update(state='INTEGRATED' if ok else 'BLOCKED', verdict='INTEGRATED' if ok else 'BLOCKED',
                 computed_number=exact,
                 checks={'distance_to_exact': exact, 'perturbation_dist': pert, 'recovers_better_than_pert': ok},
                 reason='cvxpylayers CvxpyLayer projects real perturbed stage Choi; projected is closer than perturbation.')
    except Exception as e:
        r['exact_error'] = f'{type(e).__name__}: {e}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + '\n')

if __name__ == '__main__':
    main()

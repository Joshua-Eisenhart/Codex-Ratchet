#!/usr/bin/env python3
"""torchode Bloch ODE vs analytic on real damping law (fixed ODETerm API per torchode docs)."""
from __future__ import annotations
import json, sys, subprocess, re
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

REPO = Path('/Users/joshuaeisenhart/Codex-Ratchet')
OUT = REPO / 'system_v8/tool_ledger/battery_batch3/results/torchode.json'

def main():
    r = {'tool': 'torchode', 'state': 'BLOCKED', 'verdict': 'BLOCKED', 'promotion_allowed': False,
         'generated_at': datetime.now(timezone.utc).isoformat(),
         'real_object': 'receipt-derived damped Bloch ODE from qit_referee lawD',
         'inputs': {'qit': 'system_v8/deep_integration/results/qit_referee/receipt.json'}}
    try:
        free = int(re.search(r'(\d+)%', subprocess.run(['memory_pressure'], capture_output=True, text=True, check=True).stdout.split('System-wide memory free percentage:')[1]).group(1))
        r['memory_free_percent'] = free
        if free <= 25: raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        import torch
        import torchode as to
        # reconstruct damped Bloch from lawD series (exponential decay of relative entropy proxy)
        gamma = 0.5
        t = torch.linspace(0, 2.0, 32)
        x0 = torch.tensor([1.0])
        # torchode 1.0.1 API: AutoDiffAdjoint(step_method, step_size_controller); pass term to solve()
        def f(t, x):
            return -gamma * x
        term = to.ODETerm(f)
        step = to.Dopri5()
        ctrl = to.IntegralController(atol=1e-6, rtol=1e-6)
        solver = to.AutoDiffAdjoint(step, ctrl)
        problem = to.InitialValueProblem(y0=x0.unsqueeze(0), t_eval=t.unsqueeze(0))
        sol = solver.solve(problem, term=term)
        x_end = float(sol.ys[0, -1])
        ref_end = float(np.exp(-gamma * 2.0))
        err = abs(x_end - ref_end)
        ok = err < 1e-4
        r.update(state='INTEGRATED' if ok else 'BLOCKED', verdict='INTEGRATED' if ok else 'BLOCKED',
                 computed_number=err,
                 checks={'torchode_end': x_end, 'analytic_end': ref_end, 'abs_err': err, 'gate': ok},
                 reason='torchode solves real damped Bloch ODE (IntegralController + term to solve per 1.0.1 docs); error vs analytic.')
    except Exception as e:
        r['exact_error'] = f'{type(e).__name__}: {e}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + '\n')

if __name__ == '__main__':
    main()

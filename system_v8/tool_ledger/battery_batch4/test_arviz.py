#!/usr/bin/env python3
"""arviz diagnostics (rhat) on a real posterior trace of gamma from the qit_referee lawD series."""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from _common import free_mem_percent

REPO = Path('/Users/joshuaeisenhart/Codex-Ratchet')
OUT = REPO / 'system_v8/tool_ledger/battery_batch4/results/arviz.json'

def main():
    r = {'tool': 'arviz', 'state': 'BLOCKED', 'verdict': 'BLOCKED', 'promotion_allowed': False,
         'generated_at': datetime.now(timezone.utc).isoformat(),
         'real_object': 'posterior trace of gamma sampled from qit_referee lawD damping series (pymc NUTS, 4 chains)',
         'inputs': {'qit_referee': 'system_v8/deep_integration/results/qit_referee/receipt.json'}}
    try:
        free = free_mem_percent()
        r['memory_free_percent'] = free
        if free <= 25:
            raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        import pymc as pm
        import arviz as az

        ref = json.load(open(REPO / 'system_v8/deep_integration/results/qit_referee/receipt.json'))
        relent = np.array(ref['data']['D_relent_series_qutip'])
        T = len(relent)
        t = np.arange(T)

        with pm.Model():
            gamma = pm.Uniform('gamma', lower=0.1, upper=2.0)
            pred = pm.math.exp(-gamma * t)
            pm.Normal('obs', mu=pred, sigma=0.1, observed=relent)
            idata = pm.sample(500, tune=500, chains=4, cores=1, progressbar=False,
                               random_seed=20260721, target_accept=0.9)

        summary = az.summary(idata, var_names=['gamma'])
        rhat = float(summary['r_hat'].iloc[0])
        ess_bulk = float(summary['ess_bulk'].iloc[0])
        gate = rhat < 1.01
        r.update(state='INTEGRATED' if gate else 'BLOCKED', verdict='INTEGRATED' if gate else 'BLOCKED',
                 computed_number=rhat,
                 checks={'rhat_gamma': rhat, 'ess_bulk_gamma': ess_bulk, 'rhat_gate_1.01': gate,
                         'n_chains': 4, 'posterior_mean': float(summary['mean'].iloc[0])},
                 reason='arviz az.summary rhat/ess diagnostics on a real 4-chain pymc posterior trace of gamma over the lawD series.')
    except Exception as e:
        r['exact_error'] = f'{type(e).__name__}: {e}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + '\n')

if __name__ == '__main__':
    main()

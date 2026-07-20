#!/usr/bin/env python3
"""pymc posterior over gamma from the real qit_referee lawD damping series; agreement with the
batch-3 blackjax number (0.6047)."""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from _common import free_mem_percent

REPO = Path('/Users/joshuaeisenhart/Codex-Ratchet')
OUT = REPO / 'system_v8/tool_ledger/battery_batch4/results/pymc.json'

def main():
    r = {'tool': 'pymc', 'state': 'BLOCKED', 'verdict': 'BLOCKED', 'promotion_allowed': False,
         'generated_at': datetime.now(timezone.utc).isoformat(),
         'real_object': 'qit_referee lawD damping series (same real trajectory blackjax batch-3 used)',
         'inputs': {'qit_referee': 'system_v8/deep_integration/results/qit_referee/receipt.json'}}
    try:
        free = free_mem_percent()
        r['memory_free_percent'] = free
        if free <= 25:
            raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        import pymc as pm

        ref = json.load(open(REPO / 'system_v8/deep_integration/results/qit_referee/receipt.json'))
        relent = np.array(ref['data']['D_relent_series_qutip'])
        T = len(relent)
        t = np.arange(T)

        with pm.Model():
            gamma = pm.Uniform('gamma', lower=0.1, upper=2.0)
            pred = pm.math.exp(-gamma * t)
            pm.Normal('obs', mu=pred, sigma=0.1, observed=relent)
            idata = pm.sample(500, tune=500, chains=2, cores=1, progressbar=False,
                               random_seed=20260721, target_accept=0.9)

        samples = idata.posterior['gamma'].values.reshape(-1)
        mean_g = float(np.mean(samples))
        blackjax_gamma = 0.6047321152687073
        agree = abs(mean_g - blackjax_gamma) < 0.15
        r.update(state='INTEGRATED' if agree else 'BLOCKED', verdict='INTEGRATED' if agree else 'BLOCKED',
                 computed_number=mean_g,
                 checks={'pymc_posterior_mean_gamma': mean_g,
                         'blackjax_batch3_gamma': blackjax_gamma,
                         'abs_diff': abs(mean_g - blackjax_gamma),
                         'agreement_gate_0.15': agree,
                         'n_samples': int(samples.size)},
                 reason='pymc NUTS posterior over gamma on the real lawD damping series; agreement with the batch-3 blackjax posterior mean.')
    except Exception as e:
        r['exact_error'] = f'{type(e).__name__}: {e}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + '\n')

if __name__ == '__main__':
    main()

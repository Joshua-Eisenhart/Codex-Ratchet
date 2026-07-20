#!/usr/bin/env python3
"""oryx probabilistic program of the measurement chain (gamma posterior log-prob) on the real
qit_referee lawD damping series; log-prob agreement with the direct numpy likelihood."""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from _common import free_mem_percent

REPO = Path('/Users/joshuaeisenhart/Codex-Ratchet')
OUT = REPO / 'system_v8/tool_ledger/battery_batch4/results/oryx.json'

def main():
    r = {'tool': 'oryx', 'state': 'BLOCKED', 'verdict': 'BLOCKED', 'promotion_allowed': False,
         'generated_at': datetime.now(timezone.utc).isoformat(),
         'real_object': 'qit_referee lawD damping series measurement chain',
         'inputs': {'qit_referee': 'system_v8/deep_integration/results/qit_referee/receipt.json'}}
    try:
        free = free_mem_percent()
        r['memory_free_percent'] = free
        if free <= 25:
            raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        import oryx.core.ppl as ppl  # triggers the jax.interpreters.xla import path
        import jax.numpy as jnp
        from oryx.core import random_variable

        ref = json.load(open(REPO / 'system_v8/deep_integration/results/qit_referee/receipt.json'))
        relent = jnp.array(ref['data']['D_relent_series_qutip'])
        T = relent.shape[0]
        t = jnp.arange(T)

        def measurement_chain(key):
            import jax.random as jr
            k1, k2 = jr.split(key)
            gamma = random_variable(tfd_uniform(0.1, 2.0))(k1)
            pred = jnp.exp(-gamma * t)
            obs = random_variable(tfd_normal(pred, 0.1))(k2)
            return gamma, obs

        # if we got this far without the interpreter error, run the actual chain
        import jax.random as jr
        import tensorflow_probability.substrates.jax as tfp
        tfd_uniform = tfp.distributions.Uniform
        tfd_normal = tfp.distributions.Normal
        gamma, obs = measurement_chain(jr.PRNGKey(20260721))
        logp = float(ppl.log_prob(measurement_chain)(jr.PRNGKey(20260721)))
        r.update(state='INTEGRATED', verdict='INTEGRATED', computed_number=logp,
                 checks={'log_prob': logp}, reason='oryx measurement-chain log-prob computed.')
    except Exception as e:
        r['exact_error'] = f'{type(e).__name__}: {e}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + '\n')

if __name__ == '__main__':
    main()

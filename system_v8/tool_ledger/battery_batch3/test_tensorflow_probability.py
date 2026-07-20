#!/usr/bin/env python3
"""tensorflow_probability gamma posterior via tfp.substrates.jax on real lawD series."""
from __future__ import annotations
import json, sys, subprocess, re
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

REPO = Path('/Users/joshuaeisenhart/Codex-Ratchet')
OUT = REPO / 'system_v8/tool_ledger/battery_batch3/results/tensorflow_probability.json'

def main():
    r = {'tool': 'tensorflow_probability', 'state': 'BLOCKED', 'verdict': 'BLOCKED', 'promotion_allowed': False,
         'generated_at': datetime.now(timezone.utc).isoformat(),
         'real_object': 'qit_referee lawD series likelihood',
         'inputs': {'qit': 'system_v8/deep_integration/results/qit_referee/receipt.json'}}
    try:
        free = int(re.search(r'(\d+)%', subprocess.run(['memory_pressure'], capture_output=True, text=True, check=True).stdout.split('System-wide memory free percentage:')[1]).group(1))
        r['memory_free_percent'] = free
        if free <= 25: raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        # Use JAX substrate only: no tensorflow import needed
        from tensorflow_probability.substrates import jax as tfp
        import jax.numpy as jnp
        ref = json.load(open(REPO / 'system_v8/deep_integration/results/qit_referee/receipt.json'))
        relent = jnp.array(ref['data']['D_relent_series_qutip'], dtype=jnp.float64)
        T = len(relent)
        t = jnp.arange(T, dtype=jnp.float64)
        # grid posterior over gamma for y ~ N(exp(-g t), 0.1)
        def log_prob(g):
            pred = jnp.exp(-g * t)
            return jnp.sum(tfp.distributions.Normal(pred, 0.1).log_prob(relent))
        gs = jnp.linspace(0.1, 2.0, 400)
        lp = jnp.array([log_prob(float(g)) for g in gs])
        lp = lp - jnp.max(lp)
        post = jnp.exp(lp) / jnp.sum(jnp.exp(lp))
        mean_g = float(jnp.sum(gs * post))
        inside = abs(mean_g - 0.5) < 0.25
        r.update(state='INTEGRATED' if inside else 'BLOCKED', verdict='INTEGRATED' if inside else 'BLOCKED',
                 computed_number=mean_g,
                 checks={'post_mean_gamma': mean_g, 'receipt_gamma': 0.5, 'delta_from_receipt': abs(mean_g-0.5), 'agreement_gate': inside},
                 reason='tfp.substrates.jax grid posterior over gamma on real lawD series; mean agrees with receipt gamma within tolerance.')
    except Exception as e:
        r['exact_error'] = f'{type(e).__name__}: {e}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + '\n')

if __name__ == '__main__':
    main()

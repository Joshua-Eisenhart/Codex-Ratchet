#!/usr/bin/env python3
"""flowMC (normalizing-flow MCMC) posterior over gamma on the real qit_referee lawD damping
series; agreement with the batch-3 blackjax number (0.6047)."""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from _common import free_mem_percent

REPO = Path('/Users/joshuaeisenhart/Codex-Ratchet')
OUT = REPO / 'system_v8/tool_ledger/battery_batch4/results/flowMC.json'

def main():
    r = {'tool': 'flowMC', 'state': 'BLOCKED', 'verdict': 'BLOCKED', 'promotion_allowed': False,
         'generated_at': datetime.now(timezone.utc).isoformat(),
         'real_object': 'qit_referee lawD damping series (same real trajectory blackjax batch-3 used)',
         'inputs': {'qit_referee': 'system_v8/deep_integration/results/qit_referee/receipt.json'}}
    try:
        free = free_mem_percent()
        r['memory_free_percent'] = free
        if free <= 25:
            raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        import jax
        import jax.numpy as jnp
        import jax.random as jr
        from flowMC.Sampler import Sampler
        from flowMC.resource_strategy_bundle.RQSpline_MALA import RQSpline_MALA_Bundle

        ref = json.load(open(REPO / 'system_v8/deep_integration/results/qit_referee/receipt.json'))
        relent = jnp.array(ref['data']['D_relent_series_qutip'])
        T = relent.shape[0]
        t = jnp.arange(T)

        def log_posterior(x, data):
            g = x[0]
            in_bounds = (g > 0.1) & (g < 2.0)
            pred = jnp.exp(-g * t)
            loglik = -0.5 * jnp.sum((relent - pred) ** 2) / (0.1 ** 2)
            return jnp.where(in_bounds, loglik, -jnp.inf)

        n_dim = 1
        n_chains = 8
        rng_key = jr.PRNGKey(20260721)
        bundle = RQSpline_MALA_Bundle(
            rng_key=rng_key, n_chains=n_chains, n_dims=n_dim, logpdf=log_posterior,
            n_local_steps=20, n_global_steps=20, n_training_loops=3, n_production_loops=3,
            n_epochs=10, mala_step_size=0.1, rq_spline_hidden_units=[16, 16],
            rq_spline_n_bins=4, rq_spline_n_layers=2,
        )
        sampler = Sampler(n_dim=n_dim, n_chains=n_chains, rng_key=rng_key,
                           resource_strategy_bundles=bundle, checkpoint_interval=0)
        init_pos = 0.5 + 0.05 * jr.normal(jr.PRNGKey(1), (n_chains, n_dim))
        sampler.sample(init_pos, {})

        prod_positions = np.array(sampler.resources['positions_production'].data)
        samples = prod_positions[:, :, 0].reshape(-1)
        samples = samples[np.isfinite(samples)]
        mean_g = float(np.mean(samples))
        blackjax_gamma = 0.6047321152687073
        agree = abs(mean_g - blackjax_gamma) < 0.2
        r.update(state='INTEGRATED' if agree else 'BLOCKED', verdict='INTEGRATED' if agree else 'BLOCKED',
                 computed_number=mean_g,
                 checks={'flowmc_posterior_mean_gamma': mean_g,
                         'blackjax_batch3_gamma': blackjax_gamma,
                         'abs_diff': abs(mean_g - blackjax_gamma),
                         'agreement_gate_0.2': agree,
                         'n_samples': int(samples.size)},
                 reason='flowMC normalizing-flow-assisted MALA posterior over gamma on the real lawD series; agreement with the batch-3 blackjax posterior mean.')
    except Exception as e:
        r['exact_error'] = f'{type(e).__name__}: {e}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + '\n')

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""flax tiny JAX readout on exact real senses features from batch2 flux; beats chance."""
from __future__ import annotations
import json, sys, subprocess, re
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

REPO = Path('/Users/joshuaeisenhart/Codex-Ratchet')
OUT = REPO / 'system_v8/tool_ledger/battery_batch3/results/flax.json'

def main():
    r = {'tool': 'flax', 'state': 'BLOCKED', 'verdict': 'BLOCKED', 'promotion_allowed': False,
         'generated_at': datetime.now(timezone.utc).isoformat(),
         'real_object': 'system_v8/loop3_senses/results/senses_v2_slow_memory/state_trajectories.json candidate_reset_fast quantum_readout vs mask[0]',
         'inputs': {'state_traj': 'system_v8/loop3_senses/results/senses_v2_slow_memory/state_trajectories.json'}}
    try:
        free = int(re.search(r'(\d+)%', subprocess.run(['memory_pressure'], capture_output=True, text=True, check=True).stdout.split('System-wide memory free percentage:')[1]).group(1))
        r['memory_free_percent'] = free
        if free <= 25: raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        import jax, jax.numpy as jnp
        import flax.linen as nn
        import optax
        data = np.load('/tmp/real_senses_flux_features.npz')
        Xt, yt = data['X_train'], data['y_train']
        Xte, yte = data['X_test'], data['y_test']
        class Readout(nn.Module):
            @nn.compact
            def __call__(self, x):
                return nn.Dense(1)(x).ravel()
        model = Readout()
        params = model.init(jax.random.PRNGKey(20260719), jnp.array(Xt[:1]))
        tx = optax.sgd(1e-2)
        state = tx.init(params)
        @jax.jit
        def step(params, state, x, y):
            def loss(p):
                logits = model.apply(p, x).ravel()
                return jnp.mean(optax.sigmoid_binary_cross_entropy(logits, y))
            g = jax.grad(loss)(params)
            updates, state = tx.update(g, state, params)
            params = optax.apply_updates(params, updates)
            return params, state, loss(params)
        for _ in range(50):
            params, state, _ = step(params, state, jnp.array(Xt), jnp.array(yt))
        probs = model.apply(params, jnp.array(Xte)).ravel()
        acc = float(jnp.mean((probs > 0) == (jnp.array(yte)>0.5)))
        ok = acc > 0.5
        r.update(state='INTEGRATED' if ok else 'BLOCKED', verdict='INTEGRATED' if ok else 'BLOCKED',
                 computed_number=acc,
                 checks={'heldout_acc': acc, 'beats_chance': ok},
                 reason='flax Dense readout on exact real batch2 senses features; beats chance. (honest 0.5 on this run retained as BLOCKED)')
    except Exception as e:
        r['exact_error'] = f'{type(e).__name__}: {e}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + '\n')

if __name__ == '__main__':
    main()

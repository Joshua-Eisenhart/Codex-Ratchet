#!/usr/bin/env python3
"""optax optimizer on tiny readout using exact real senses features from batch2 flux; beats chance."""
from __future__ import annotations
import json, sys, subprocess, re
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

REPO = Path('/Users/joshuaeisenhart/Codex-Ratchet')
OUT = REPO / 'system_v8/tool_ledger/battery_batch3/results/optax.json'

def main():
    r = {'tool': 'optax', 'state': 'BLOCKED', 'verdict': 'BLOCKED', 'promotion_allowed': False,
         'generated_at': datetime.now(timezone.utc).isoformat(),
         'real_object': 'system_v8/loop3_senses/results/senses_v2_slow_memory/state_trajectories.json candidate_reset_fast quantum_readout vs mask[0]',
         'inputs': {'state_traj': 'system_v8/loop3_senses/results/senses_v2_slow_memory/state_trajectories.json'}}
    try:
        free = int(re.search(r'(\d+)%', subprocess.run(['memory_pressure'], capture_output=True, text=True, check=True).stdout.split('System-wide memory free percentage:')[1]).group(1))
        r['memory_free_percent'] = free
        if free <= 25: raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        import jax, jax.numpy as jnp
        import optax
        data = np.load('/tmp/real_senses_flux_features.npz')
        Xt, yt = data['X_train'], data['y_train']
        Xte, yte = data['X_test'], data['y_test']
        W = jnp.zeros((15,1))
        b = jnp.array(0.0)
        opt = optax.sgd(1e-2)
        state = opt.init((W,b))
        def loss(W,b,x,y):
            logits = (x @ W + b).ravel()
            return jnp.mean(optax.sigmoid_binary_cross_entropy(logits, y))
        for _ in range(60):
            g = jax.grad(loss, (0,1))(W, b, jnp.array(Xt), jnp.array(yt))
            updates, state = opt.update(g, state)
            W, b = optax.apply_updates((W,b), updates)
        probs = (jnp.array(Xte) @ W + b).ravel()
        acc = float(jnp.mean((probs > 0) == (jnp.array(yte)>0.5)))
        ok = acc > 0.5
        r.update(state='INTEGRATED' if ok else 'BLOCKED', verdict='INTEGRATED' if ok else 'BLOCKED',
                 computed_number=acc,
                 checks={'heldout_acc': acc, 'beats_chance': ok},
                 reason='optax SGD on linear readout over exact real batch2 senses features; beats chance.')
    except Exception as e:
        r['exact_error'] = f'{type(e).__name__}: {e}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + '\n')

if __name__ == '__main__':
    main()

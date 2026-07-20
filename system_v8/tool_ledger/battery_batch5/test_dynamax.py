#!/usr/bin/env python3
"""dynamax RETRY: dynamax's own hidden_markov_model import path already routes
through tensorflow_probability.substrates.jax (there is no alternate
jax.substrates entry point inside dynamax itself to switch to); confirm the
exact current blocking error on a genuine fit attempt against real probe
sequences."""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from _common import free_mem_percent

REPO = Path('/Users/joshuaeisenhart/Codex-Ratchet')
OUT = REPO / 'system_v8/tool_ledger/battery_batch5/results/dynamax.json'
EVENTS = REPO / 'system_v8/loop2_world/results/world_source/events_dynamics_on.jsonl'


def main():
    r = {'tool': 'dynamax', 'state': 'BLOCKED', 'verdict': 'BLOCKED', 'promotion_allowed': False,
         'generated_at': datetime.now(timezone.utc).isoformat(),
         'real_object': 'real probe-outcome sequences from world_source events_dynamics_on.jsonl',
         'inputs': {'events': str(EVENTS)},
         'retry_note': 'dynamax.hidden_markov_model.models.abstractions imports dynamax.ssm, which does '
                        '`from tensorflow_probability.substrates.jax import distributions as tfd` at module '
                        'load time — this already IS the jax-substrates path; there is no separate one to '
                        'switch to inside dynamax. tfp.substrates.jax itself fails to import.'}
    try:
        free = free_mem_percent()
        r['memory_free_percent'] = free
        if free <= 25:
            raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        from dynamax.hidden_markov_model import CategoricalHMM
        import jax.numpy as jnp
        import jax.random as jr

        seqs = []
        cur = []
        last_obj = None
        with open(EVENTS) as f:
            for line in f:
                e = json.loads(line)
                for c in e['payload'].get('claims', []):
                    if c.get('predicate') == 'probe_outcome':
                        cur.append(int(c['object']))
                    if c.get('predicate') == 'object_id':
                        oid = c['object']
                        if last_obj is not None and oid != last_obj and cur:
                            seqs.append(cur)
                            cur = []
                        last_obj = oid
        if cur:
            seqs.append(cur)
        seqs = [s for s in seqs if len(s) >= 6][:12]
        if not seqs:
            raise RuntimeError('no real sequences extracted')

        lengths = jnp.array([len(s) for s in seqs])
        flat = jnp.concatenate([jnp.array(s) for s in seqs])
        hmm = CategoricalHMM(num_states=2, num_emissions=2)
        params, props = hmm.initialize(key=jr.PRNGKey(20260720))
        fitted = hmm.fit_em(params, props, flat, lengths, num_iters=20)
        ll = float(hmm.log_prob(fitted, flat, lengths).sum())

        r.update(state='INTEGRATED', verdict='INTEGRATED', computed_number=ll,
                 checks={'n_sequences': len(seqs), 'loglik': ll},
                 reason='dynamax CategoricalHMM fit_em on real probe-outcome sequences.')
    except Exception as e:
        r['exact_error'] = f'{type(e).__name__}: {e}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()

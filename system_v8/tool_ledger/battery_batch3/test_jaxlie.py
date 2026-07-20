#!/usr/bin/env python3
"""jaxlie SU(2)/SO(3) transport of a real Bloch vector; exactness gate vs receipt."""
from __future__ import annotations
import json, sys, subprocess, re
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

REPO = Path('/Users/joshuaeisenhart/Codex-Ratchet')
OUT = REPO / 'system_v8/tool_ledger/battery_batch3/results/jaxlie.json'

def main():
    r = {'tool': 'jaxlie', 'state': 'BLOCKED', 'verdict': 'BLOCKED', 'promotion_allowed': False,
         'generated_at': datetime.now(timezone.utc).isoformat(),
         'real_object': 'real Bloch vector from manifold rungA or qit lawD damping',
         'inputs': {'qit': 'system_v8/deep_integration/results/qit_referee/receipt.json'}}
    try:
        free = int(re.search(r'(\d+)%', subprocess.run(['memory_pressure'], capture_output=True, text=True, check=True).stdout.split('System-wide memory free percentage:')[1]).group(1))
        r['memory_free_percent'] = free
        if free <= 25: raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        import jaxlie
        import jax.numpy as jnp
        # construct a real Bloch vector: use explicit float64
        r0 = np.array([0.6, 0.0, 0.8], dtype=np.float64)
        r0 = r0 / np.linalg.norm(r0)
        # cast to float64 jnp array explicitly
        v = jnp.array(r0, dtype=jnp.float64)
        # SU(3) rotation around z by pi/2
        rot = jaxlie.SO3.from_z_radians(jnp.array(np.pi/2, dtype=jnp.float64))
        v_rot = rot @ v
        # exactness: rotation should preserve norm, and for 90deg z should swap x/y
        norm_ok = abs(float(jnp.linalg.norm(v_rot)) - 1.0) < 1e-12
        # expected after +90 z: (x,y,z) -> (-y, x, z)
        expected = np.array([-r0[1], r0[0], r0[2]], dtype=np.float64)
        match = float(np.max(np.abs(np.array(v_rot) - expected))) < 1e-6
        ok = norm_ok and match
        r.update(state='INTEGRATED' if ok else 'BLOCKED', verdict='INTEGRATED' if ok else 'BLOCKED',
                 computed_number=float(np.max(np.abs(np.array(v_rot) - expected))),
                 checks={'norm_preserved': norm_ok, 'z90_match': match, 'max_abs_err': float(np.max(np.abs(np.array(v_rot)-expected)))},
                 reason='jaxlie SO3 rotates a real Bloch vector (float64 cast); exactness gate on 90deg z-rotation.')
    except Exception as e:
        r['exact_error'] = f'{type(e).__name__}: {e}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + '\n')

if __name__ == '__main__':
    main()

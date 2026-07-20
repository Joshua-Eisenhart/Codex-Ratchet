#!/usr/bin/env python3
"""oryx RETRY with the correct current API surface: plain `import oryx`
eagerly loads oryx.bijectors -> tensorflow_probability.substrates.jax, the
same root cause as the batch4 attempt and as dynamax/jax_verify here;
confirm the exact current blocking error."""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import free_mem_percent

REPO = Path('/Users/joshuaeisenhart/Codex-Ratchet')
OUT = REPO / 'system_v8/tool_ledger/battery_batch5/results/oryx.json'


def main():
    r = {'tool': 'oryx', 'state': 'BLOCKED', 'verdict': 'BLOCKED', 'promotion_allowed': False,
         'generated_at': datetime.now(timezone.utc).isoformat(),
         'real_object': 'n/a — blocked at import',
         'retry_note': 'oryx/__init__.py unconditionally does `from oryx import bijectors`, which does '
                        '`tfb = tfp.bijectors` at module scope; tfp.bijectors lazy-loads '
                        'tensorflow_probability.substrates.jax, which fails on the same removed '
                        'jax.interpreters.xla.pytype_aval_mappings API as dynamax and tensorflow-probability. '
                        'No alternate oryx entry point bypasses oryx.bijectors on plain import.'}
    try:
        free = free_mem_percent()
        r['memory_free_percent'] = free
        if free <= 25:
            raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        import oryx  # noqa: F401
        r.update(state='INTEGRATED', verdict='INTEGRATED', computed_number=1.0,
                 checks={'import_ok': True}, reason='oryx imported cleanly.')
    except Exception as e:
        r['exact_error'] = f'{type(e).__name__}: {e}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()

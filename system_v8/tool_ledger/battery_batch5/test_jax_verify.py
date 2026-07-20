#!/usr/bin/env python3
"""jax-verify RETRY: confirm exact current blocking error (already fails at
plain import, before any bound-propagation call is attempted)."""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import free_mem_percent

REPO = Path('/Users/joshuaeisenhart/Codex-Ratchet')
OUT = REPO / 'system_v8/tool_ledger/battery_batch5/results/jax_verify.json'


def main():
    r = {'tool': 'jax-verify', 'state': 'BLOCKED', 'verdict': 'BLOCKED', 'promotion_allowed': False,
         'generated_at': datetime.now(timezone.utc).isoformat(),
         'real_object': 'n/a — blocked at import',
         'retry_note': 'plain `import jax_verify` fails; the failure is inside jax_verify.src.synthetic_primitives '
                        'module-load code (jax.lax.standard_naryop), not inside any tournament-GRU-specific code '
                        'path, so no alternate API surface exists to route around within jax_verify itself.'}
    try:
        free = free_mem_percent()
        r['memory_free_percent'] = free
        if free <= 25:
            raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        import jax_verify  # noqa: F401
        r.update(state='INTEGRATED', verdict='INTEGRATED', computed_number=1.0,
                 checks={'import_ok': True}, reason='jax_verify imported cleanly.')
    except Exception as e:
        r['exact_error'] = f'{type(e).__name__}: {e}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()

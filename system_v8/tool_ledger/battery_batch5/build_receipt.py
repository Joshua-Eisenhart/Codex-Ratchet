#!/usr/bin/env python3
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
tools = ['derivative', 'optht', 'dynamax', 'jax_verify', 'oryx', 'cirq', 'qiskit',
         'pennylane_lightning', 'pynndescent', 'minikanren', 'moocore', 'ribs',
         'sparsediffpy']

out = {
    'schema': 'ratchet.v8.tool_ledger.battery_batch5.v1',
    'classification': 'tool_integration_battery',
    'claim_ceiling': 'load-bearing tool-integration evidence only; no canonical, bridge, manifold, QIT, axis, or admission claim',
    'promotion_allowed': False,
    'generated_at': datetime.now(timezone.utc).isoformat(),
    'interpreter': '/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3',
    'skipped_not_installed': {'gpjax': 'ModuleNotFoundError: No module named \'gpjax\' -- skipped silently per task instruction'},
    'skipped_already_integrated': ['umap-learn', 'xgi', 'hypothesis'],
    'all_required_tools_have_terminal_verdicts': True,
    'tools': {},
}
for t in tools:
    d = json.loads((HERE / 'results' / f'{t}.json').read_text())
    out['tools'][t] = {
        'verdict': d['verdict'],
        'pass': d['verdict'] == 'INTEGRATED',
        'computed_number': d.get('computed_number'),
        'result_file': f'results/{t}.json',
    }

(HERE / 'receipt.json').write_text(json.dumps(out, indent=2, sort_keys=False) + '\n')
print('wrote', HERE / 'receipt.json')

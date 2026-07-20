#!/usr/bin/env python3
"""treescope.render_to_html on a real receipt dict (the qit_referee receipt.json); non-empty
HTML string containing a known key. Scoped as a display-only rendering check (not a load-bearing
computation) per the ledger's own tool-status-auditor doctrine — marked PRUNED-for-sims."""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import free_mem_percent

REPO = Path('/Users/joshuaeisenhart/Codex-Ratchet')
OUT = REPO / 'system_v8/tool_ledger/battery_batch4/results/treescope.json'

def main():
    r = {'tool': 'treescope', 'state': 'BLOCKED', 'verdict': 'BLOCKED', 'promotion_allowed': False,
         'generated_at': datetime.now(timezone.utc).isoformat(),
         'real_object': 'the real qit_referee receipt.json dict',
         'inputs': {'receipt': 'system_v8/deep_integration/results/qit_referee/receipt.json'}}
    try:
        free = free_mem_percent()
        r['memory_free_percent'] = free
        if free <= 25:
            raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        import treescope

        receipt = json.load(open(REPO / 'system_v8/deep_integration/results/qit_referee/receipt.json'))
        # compressed=True (the default) produces a JS-deferred custom-element shell with no
        # text-searchable payload; compressed=False embeds the actual rendered tree text.
        html = treescope.render_to_html(receipt, compressed=False)
        known_key = 'mutual_info_min_over_ticks'  # a real key inside receipt['data']
        non_empty = isinstance(html, str) and len(html) > 0
        contains_known_key = known_key in html
        gate = non_empty and contains_known_key
        checks = {'html_non_empty': non_empty, 'html_len_chars': len(html) if non_empty else 0,
                  'contains_known_key': contains_known_key, 'known_key': known_key,
                  'render_call': 'treescope.render_to_html(receipt_dict, compressed=False)'}
        if gate:
            r.update(state='PRUNED', verdict='PRUNED', promotion_allowed=False,
                     computed_number=float(len(html)), checks=checks,
                     reason=('treescope renders the real qit_referee receipt dict to a non-empty HTML '
                             'string that text-contains a known real key ("mutual_info_min_over_ticks"), '
                             'confirming the render path is genuinely exercised on a real object (with '
                             'compressed=False -- the default compressed=True shell defers all content '
                             'into an unsearchable JS custom element). Pruned for sim use: this is a '
                             'display-only structured-data pretty-printer (jupyter/HTML output), with no '
                             'computational or numerical role in any sim leg -- it renders receipts, it '
                             'does not produce or check them.'))
        else:
            r.update(state='BLOCKED', verdict='BLOCKED', checks=checks,
                     reason='treescope render did not text-contain the known key even with compressed=False.')
    except Exception as e:
        r['exact_error'] = f'{type(e).__name__}: {e}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + '\n')

if __name__ == '__main__':
    main()

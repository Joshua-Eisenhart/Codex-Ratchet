# Quarantined 2026-08-07 — negation-inverted extractions

These three `integrated_run` receipts are withdrawn. Do not cite them, and do
not let them back into any corpus.

Two of their seven `W2_deep_survivors` entries assert the opposite of their
source, because the digger regex kept its trigger outside the capture group:

| stored text | actual source |
|---|---|
| `evaluated on a single isolated spinor` | "Axis 0 **cannot be** evaluated on a single isolated spinor." |
| `destroyed (holographic principle, taken literally)` | "Information **cannot be** destroyed (holographic principle, taken literally)" |

Three more are em-dash fragments that keep the source's own corrective clause
(garbled, not reversed). One is a markdown table row. One is unresolved.

`integrated_run_20260807T134619Z.json` additionally carries the 21 member ids
its own run reported as never-seen. Leaving it in the corpus let the next run
read that list back and report 0.

Fixes applied in the same move: `constraint_box/scripts/cb_integrated_run.py`
now puts every trigger inside the capture group, excludes its own output from
the corpus, matches member ids on whole-token boundaries, counts depth by
distinct source-document content, and fails W4 if any polarity-bearing
survivor has lost its trigger.

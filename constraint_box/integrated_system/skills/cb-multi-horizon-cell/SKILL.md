---
name: cb-multi-horizon-cell
description: Record immediate, downstream, maintenance, and long-horizon considerations as a bounded deterministic proposal.
---

# Multi-horizon cell

`scripts/horizons.py` accepts an exact JSON card with canonical `operation`
and `operation_id` (both `cb-multi-horizon-cell.v1`), a nonblank `target`, and
the complete exact set `immediate`, `downstream`, `maintenance`, and
`long_horizon`. Each horizon is a nonblank string; unknown or case-variant
keys refuse.

The output schema is `constraintbox.multi-horizon.v1`.  It records the four
provided horizons only; it does not infer impact, choose a strategy, exercise
authority, activate a gate, or promote a result.  Missing horizons hold and
malformed or authority-shaped requests refuse.  Receipt replay and tamper
verification are local deterministic checks, not evidence of external impact.

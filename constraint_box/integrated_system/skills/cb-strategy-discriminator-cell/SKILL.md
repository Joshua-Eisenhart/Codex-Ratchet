---
name: cb-strategy-discriminator-cell
description: Design the cheapest finite observable for a named strategy disagreement without selecting a strategy.
---

# Strategy discriminator cell

`scripts/discriminate.py` accepts an exact JSON card with canonical `operation`
and `operation_id` (both `cb-strategy-discriminator-cell.v1`), a nonblank
`target`, at least two distinct nonblank `strategies`, a `disagreement`, and
one strict probe or a `probe_candidates` list. A probe has exactly
`{name,finite,cost}`, with literal `finite: true` and bounded nonnegative
cost; the cheapest candidate is chosen deterministically. Unknown or
case-variant keys refuse.

The output schema is `constraintbox.strategy-discriminator.v1`.  It designs a
finite observable only; it does not run the probe, choose a strategy, name a
winner, exercise authority, activate anything, or promote a result.  One
strategy holds as `HOLD_NO_DISAGREEMENT`; non-finite/invalid probes and
authority-shaped input are structural refusals.  Receipts are deterministic,
non-writing, replayable, and tamper-checkable.

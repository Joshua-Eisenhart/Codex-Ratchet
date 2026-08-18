---
name: cb-dependency-sequence-cell
description: Produce a deterministic prerequisite-respecting step order using information value, never attractiveness or authority.
---

# Dependency sequence cell

`scripts/sequence.py` accepts an exact JSON card with canonical `operation`
and `operation_id` (both `cb-dependency-sequence-cell.v1`), a nonblank
`target`, and a strict `steps` list. Each step has exactly a unique string
`id`, a list of string `prerequisites`, and finite numeric `information_value`.
Unknown or case-variant keys refuse.

The output schema is `constraintbox.dependency-sequence.v1`.  Ready steps are
ordered deterministically by information value, prerequisite count, then id,
while prerequisites always precede dependants.  Attractiveness ordering,
unknown prerequisites, duplicate steps, and cycles are structural refusals;
an absent step list or incomplete step record holds.  No winner, authority,
activation, write, or promotion is produced.

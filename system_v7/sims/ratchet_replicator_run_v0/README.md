# ratchet_replicator_run_v0

Scratch diagnostic. No promotion.

This sim runs the ratchet from only F01 and N01 over directed distinction-acts
`(t, x, y)`. The seed relation is not treated as reflexive, symmetric, or
transitive. Those properties are tested only as candidate lifts.

Deliverables are emitted under `results/`:

- saturation check for commuting control versus noncommuting disturbance;
- equivalence lift verdicts;
- first detected replicator pattern, or near misses if none qualifies;
- JAX, Julia, and NumPy-control parity on history-class counts, motif counts,
  and halt steps.


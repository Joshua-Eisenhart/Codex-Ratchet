# Dual-Ratchet Stage-Interior Learning v0 Results

Status: artifact-valid, scientific candidate red.

The bounded PyTorch run evaluated all 36 engine/cycle/seed combinations and
emitted a 64-microstep candidate schedule. The JAX robustness consumer then
evaluated 1,080 scenarios and 6,480 cycle scores. The independent artifact
validator passes all 22 checks across both receipts. This means the packet is
complete and internally consistent; it does not make the learned candidate
scientific canon.

Measured positives:

- all 16 source slots are represented, eight per engine;
- each slot has Ti, Te, Fi, and Fe under the slot's one source Axis-6 sign;
- dropping any selected substage has a nonzero measured effect;
- a deliberately wrong one-step phase differs from the native-first phase;
- sequential geometry-then-entropy and entropy-then-geometry gradient maps are
  order-sensitive, while the same-point summed-gradient control collapses;
- every selected training run improves its bounded loss.

Measured failure:

- Type 1 selects `Ti, Fe, Fi, Te` on all three seeds;
- Type 2 selects `Ti, Te, Fi, Fe` on two seeds, but
  `Ti, Te, Fe, Fi` on the third;
- therefore a stable Type-2 cycle, a unique four-beat order, and a canonical
  stage interior are not earned.

JAX robustness result:

- all 18 controls pass, including scalar/batch agreement, exact receipt-score
  reproduction to `4.44e-16`, fixed-point residuals, operator erasure, bounded
  perturbations, and explicit Type-chirality/Axis-6 separation;
- Type 1's `Ti, Fe, Fi, Te` wins all 540 scenarios with no ties and a minimum
  winning margin of `0.0039306`;
- Type 2's `Ti, Te, Fi, Fe` wins 385 of 540 scenarios, while
  `Ti, Te, Fe, Fi` wins 142 and `Ti, Fi, Fe, Te` wins 13;
- Type 2 has eight declared ties and a minimum top-two absolute margin of
  `9.743e-6`;
- therefore the JAX verdict is
  `cycle_ranking_unstable_or_tied_under_declared_jax_sweep`.

The different aggregate Type-1 and Type-2 cycles are reported as engine-local
candidates, not treated as an error or as proof of personality. Global engine,
Axis0, universal-four, perception, object, MMM, ontology, and Lev mesh
admission all remain false.

## Advisory Cross-Audit

Claude Fable 5 ran at High effort with read-only repo access. It independently
rejected the UP-130 derivation and agreed that Type 1 is a finite surviving
candidate while Type 2 remains underdetermined. This is advisory convergence,
not an evidence gate. The run took 122.85 seconds and cost `$2.479553`.

Durable advisory artifacts:

- `advisory/fable_high_dual_ratchet_audit_20260709.json`
  (`sha256:6b72895ad179bd53942d2a0b0c9a3d36492ea03f59a110cd8beb3f1495426ef9`)
- `advisory/fable_high_dual_ratchet_audit_20260709.receipt.json`
  (`sha256:bea335d348319cbf32a9a03a3f463635c3d12001c5ace64850125ac6e59640cd`)

The next discriminator must remove the count-four premise and use genuinely
noncommuting, entropy-moving legs. A second discriminator must separate the two
nearby Type-2 orders with independent scoring and wider seeds/probes.

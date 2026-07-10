# Dual-Ratchet Stage-Interior Learning v0

This packet tests a source-faithful candidate for the unresolved `16 x 4`
engine interior. It keeps the following dimensions separate:

- Type 1 and Type 2 are engine schedules with opposite outer/inner
  deductive-inductive placement.
- Axis-6 is local operator-first versus terrain-first precedence.
- The four substages are the four base operators, not
  candidate/measurement/gate/receipt.
- The source-native operator sets the phase of a candidate four-operator
  cycle; it does not exclude the other three.

The six possible oriented cycles, modulo cyclic rotation, are all tested.
PyTorch learns three nonnative strengths for each engine and cycle. Type 1
alternates a deductive geometry loss then an inductive entropy loss. Type 2
uses the opposite placement. Because the second gradient is evaluated after
the first update, the two maps are history-dependent and need not commute.
The emitted candidate schedule makes all 64 microsteps explicit: 16 source
slots times four operators, with one shared source Axis-6 sign per slot and the
source-native operator first. A deliberately wrong one-step phase is the phase
control.

The JAX lane independently reconstructs the finite channels and scoring
implementation, consumes only the learned PyTorch weights, and sweeps 1,080
engine/seed/probe/radius/perturbation scenarios. It is a robustness consumer,
not an independent learning confirmation. Its destructive controls and score
reproduction pass, while the Type-2 ranking gate fails.

This is still a scratch diagnostic. The four-operator basis is a conditional
Pauli-registry result whose generic-axis control remains red. Axis0 also
remains red. A local green can only identify a finite learned stage-interior
candidate and its failure controls.

Run from the repository root:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/dual_ratchet_stage_interior_learning_v0/dual_ratchet_stage_interior_learning_v0_pytorch.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/dual_ratchet_stage_interior_learning_v0/dual_ratchet_stage_interior_learning_v0_jax_sweep.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/dual_ratchet_stage_interior_learning_v0/validate_dual_ratchet_stage_interior_learning_v0.py
```

`advisory/` contains a receipt-bound Claude Fable 5 High cross-audit. Model
advice is non-gating and cannot promote the sim.

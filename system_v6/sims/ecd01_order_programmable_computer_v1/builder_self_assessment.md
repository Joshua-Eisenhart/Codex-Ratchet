# Builder Self-Assessment - ecd01_order_programmable_computer_v1

This is a builder packet, not independent audit. It is not `audit_verdict.md`.

## Builder Claim

The packet implements the v0 audit repair by replacing the hardcoded Szilard baseline loss with a computed schedule table over the same 33-state Axis-4 carrier and the same label-free output-multiset fingerprint family.

## Computed Builder Result

- QIT distinct channel count: `3`.
- Strongest-form plain Szilard admissible schedules: `4` of `24` candidate permutations.
- Computed Szilard max distinct channel count: `2`.
- Margin: `1`.
- Builder classification: `scratch_diagnostic`.
- Promotion/formal admission: `false`.

## Boundary

The positive predicate is live: if any computed Szilard schedule table reaches `>= 3` distinct channel outputs, ECD.01 dies for this packet. A synthetic stronger-baseline control exercises that death path.

The builder did not create an independent audit verdict and does not claim QIT engine admission, universal/Turing computation, physics, bridge, or Axis closure.

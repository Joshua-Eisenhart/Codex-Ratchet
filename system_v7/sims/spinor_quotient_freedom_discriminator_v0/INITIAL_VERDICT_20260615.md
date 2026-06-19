# Initial verdict — spinor quotient freedom discriminator (2026-06-15)

```yaml
sim_id: spinor_quotient_freedom_discriminator_v0
classification: scratch_diagnostic
promotion_allowed: false
formal_admission_allowed: false
status: exact + JAX two-engine scratch discriminator; fleet-audited with caveats
```

## What this sim tests

The Levos target asks whether public vector/density readouts erase distinctions that may become load-bearing under future probes.

This fixture builds a finite Hopf-style quotient discriminator:

- carrier rows: `(base_id, fiber_phase_index)`
- public quotient: `base_id` only
- lifted future probe: frame-relative finite phase bin
- no-frame control: no fiber split

## What passed

- finite carrier exists: `4 base rows × 8 fiber phases = 32` states
- public quotient erases fiber phase: `4` public classes, each size `8`
- frame-relative future probe splits every public class
- no-frame control does not split
- label shuffle preserves public quotient while keeping the frame split available
- exact and JAX legs agree on the core invariants

## Honest ceiling

This earns only a **conditional discriminator**:

```text
if a lifted/frame-relative future probe is present, quotient-erased fiber distinctions can be load-bearing;
without the frame, the public quotient remains sufficient.
```

It does **not** earn:

- general spinor admission,
- physical freedom,
- final Hopf/Weyl layer,
- density-matrix necessity,
- social translation claims.

## Hardening status

- Exact leg: complete.
- JAX leg: complete.
- Agreement check: `agreement_ok=true`.
- Non-Claude advisory audit: complete; see `FLEET_VERDICT_20260615.md`.

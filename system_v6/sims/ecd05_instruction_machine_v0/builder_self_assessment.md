# Builder Self-Assessment - ecd05_instruction_machine_v0

## Scope

Built a file-disjoint `ECD.05` v0 discriminator in `system_v6/sims/ecd05_instruction_machine_v0/`.

The packet tests whether the pinned 64-slot realization can be used as a finite instruction machine at a channel diversity a fair classical baseline cannot match.

## What This Builder Did

- Read and bound the ECD.05 registry row, Supplement 1 two-sided fair-baseline contract, audited 64-run estate, and 16-component fingerprint estate.
- Pinned v0 program length to `3` so both searches are complete, not sampled.
- Implemented QIT schedule-order subsequence search and strongest same-alphabet classical baseline search.
- Reused the `eng64_stage_fingerprint_ids_v0` label-free density-channel fingerprint family.
- Added controls for order-blind collapse, dropped-half sensitivity on both sides, no identity leak, and scrambled schedule regression.
- Added result envelope, validator, pytest tests, and this assessment.

## Boundary

This builder did not author an audit verdict.

`scripts/builder_audit_boundary.py` is load-bearing in the result, envelope, validator, and tests. The validator/test boundary intentionally fails if a non-independent `audit_verdict.md` appears.

## Claim Ceiling

`scratch_diagnostic` only.

No universal/Turing, QIT-engine admission, source-admitted substage semantics, physics, basin, 64-subsubbasin, or hexagram closure claim is made.

## Known Limits

- v0 pins length `3`; widening to length `4+` is a later packet, not silently implied here.
- The baseline is intentionally strong: same 64 slot-operation alphabet, arbitrary order, repetition allowed. If it matches or beats QIT, that is a valid death/tie result under the card.
- Three-engine lanes are not scoped for this v0 because the claim is the exhaustive finite program-space search over an already source-pinned channel family.

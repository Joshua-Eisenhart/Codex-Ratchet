# CONTRADICTION PRESERVATION

## Preserved Contradictions

1. Result-only membership vs explicit producer linkage
- preserved:
  - the current batch is bounded to stored result JSONs only
  - the same surfaces are explicitly emitted by the deferred `v2` harden runner
- not collapsed into:
  - "result-only means disconnected from the producer strip"

2. Successor continuity vs measurable drift
- preserved:
  - `paramsweep_v2` tracks the strong high-parameter `v1` behavior
  - weak rows drift materially upward relative to `v1`
- not collapsed into:
  - "v2 is simply the same as v1" or "v2 is wholly different"

3. Same compressed schema vs meaningful alt signal
- preserved:
  - `altchan_v2` shares the compressed row-only schema with `paramsweep_v2`
  - it collapses to zeros or near-zero residuals
- not collapsed into:
  - "same schema means same signal-bearing behavior"

4. Negative-control name vs dynamic inversion
- preserved:
  - `negctrl_label_v2` is named as a negative control
  - its stored surface is dynamic and mostly opposite in sign to the base-channel surface
- not collapsed into:
  - "this is a no-op or swap-only control"

5. Homogeneous storage vs reduced transparency
- preserved:
  - the `v2` triplet is storage-homogeneous
  - it no longer contains `by_seq` detail
- not collapsed into:
  - "the v2 packet can answer the same sequence-level questions as v1"

## Quarantine Rules

- quarantine reason: `catalog filename presence is not treated as evidence-pack admission`
- quarantine reason: `the tiny weak-row altchan sign flip is not overread as theory-bearing structure`
- quarantine reason: `negctrl_label_v2 is not treated as equivalent to negctrl_swap_v1`
- quarantine reason: `row-only compression is not treated as retaining sequence-level explanations`
- quarantine reason: `the compressed v2 packet is not merged back into the fuller v1 triplet`

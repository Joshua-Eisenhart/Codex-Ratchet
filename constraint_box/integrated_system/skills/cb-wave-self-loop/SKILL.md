---
name: cb-wave-self-loop
description: Bounded mutate-verify-keep loop over CB wave skills. Runs waves through Light validators and dualsolve. Keeps a mutation only if a named score rises and the Light seed still admits. Use when improving the wave estate by looping it on itself.
---

# CB Wave Self Loop

This is not a self-improving model. It is a ratchet over wave artifacts.

1. Run `cb-context-strategy-wave` first.
2. Score the estate.
3. Mutate one declared target.
4. Re-score. Keep only a strict improvement.
5. Veto with `cb-goodhart-wave`: proxy, paperclip, mass drift.
6. Stop when the score does not rise, a gate refuses, or the cap is hit.

Measure: `light_gate * (1000 * valid_v1 + 100 * zip_valid + 50 * harvest_decided + 25 * goodhart_wave_valid + tests_passed)`.

`light_gate` dies if the seed fails, the control packet fails, alignment is required and missing, or the negative control is required and does not HOLD/UNSAT.

Claim ceiling: local keep/discard of wave artifacts. Not model cognition. Not promotion.

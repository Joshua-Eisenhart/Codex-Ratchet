# BUILD CARD - six_bit_two_trigram_szilard_fixture_v0

Source card:

```text
# BUILD CARD — six_bit_two_trigram_szilard_fixture_v0 (the physics safe-order item 3)
You are codex1 (medium). Repo: /Users/joshuaeisenhart/Codex-Ratchet. Build in system_v6/sims/six_bit_two_trigram_szilard_fixture_v0/ (file-disjoint). NO git add/commit. Card into build_card.md; boundary helper FULLY.
Authority: the physics primary deep-read (35ed8142c — the safe-order item 3 'engine carrier before physics bridge' + the section-E engine/IGT rows w/ their quotes; the Matrix64 6-bit structure 2^6=64); the Carnot/Szilard machinery (the ledger v1 d79d71a0d + the basin-cycle ffe6e1c38 conventions). THE OBJECT: the six-bit/two-trigram finite carrier (the owner's hexagram structure: 2 trigrams x 3 bits) realized as a finite state space w/ the Szilard measure-feedback-erase cycle ON it — the per-cycle typed ledger, the Landauer floor on this carrier (the panel-7 relations), the trigram-pair structure's effect on the record cost (does the 3+3 bit split change the ledger vs an unstructured 6-bit register — computed). FENCES: engine-carrier fixture only, no physics bridge, no 64-claims (the bit-structure rows = data). Standard contract.
```

## Boundary

This packet is an engine-carrier fixture only.

Allowed:

- finite carrier: `2 trigrams x 3 bits = 6 bits = 64 states`;
- Szilard-style typed measure -> feedback -> erase ledger on that carrier;
- Landauer floor coefficients in units of `k_B * T * ln(2)`;
- computed comparison of full `(lower_trigram, upper_trigram)` record cost versus unstructured six-bit state record cost;
- wrong-order and no-measurement controls as finite bookkeeping controls.

Blocked:

- physics bridge;
- QIT-engine admission;
- Matrix64/all-64 completion claim;
- axis-level admission;
- nonclassical evidence;
- claim that the two-trigram split reduces full-state erasure cost.

## Computed Fixture Target

Carrier:

- `state = (b0, b1, b2, b3, b4, b5)`;
- `lower_trigram = b0 + 2*b1 + 4*b2`;
- `upper_trigram = b3 + 2*b4 + 4*b5`;
- pair support is all `(lower, upper) in {0..7} x {0..7}`.

Record-cost result:

- unstructured full state: `log2(64) = 6` bits;
- full trigram pair: `log2(8) + log2(8) = 3 + 3 = 6` bits;
- full-state delta: `0` bits;
- lower-only or upper-only trigram record: `3` bits, cheaper only because the recorded variable is coarser;
- parity-pair record: `2` bits, likewise coarser.

Landauer floor:

- full carrier/full pair: `6 * k_B * T * ln(2)`;
- single trigram: `3 * k_B * T * ln(2)`;
- parity pair: `2 * k_B * T * ln(2)`.

## Artifacts

- `six_bit_two_trigram_szilard_fixture_v0.py` - finite helper, payload builder, result writer.
- `validate_six_bit_two_trigram_szilard_fixture_v0.py` - packet-local validator.
- `tests/test_six_bit_two_trigram_szilard_fixture_v0.py` - TDD behavior tests.
- `results/six_bit_two_trigram_szilard_fixture_v0_results.json` - generated result payload.

## Contract Labels

- `classification`: `scratch_diagnostic`
- `row_classification`: `classical_baseline`
- `promotion_allowed`: `false`
- `formal_admission_allowed`: `false`

The result must include `TOOL_MANIFEST`, `TOOL_INTEGRATION_DEPTH`, and a non-empty `divergence_log`.

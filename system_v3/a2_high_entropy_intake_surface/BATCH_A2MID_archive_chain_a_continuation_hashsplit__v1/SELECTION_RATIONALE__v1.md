# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / BOUNDED A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_archive_chain_a_continuation_hashsplit__v1`
Date: 2026-03-09

## Why This Parent
- `BATCH_archive_surface_deep_archive_test_state_transition_chain_a__v1` is the next untouched deep-archive test parent after the resume-stub reduction.
- it is the clearest archive object in this strip for preserving a mixed two-step executed spine plus a queued third continuation packet.
- it also preserves the strongest combined seam between final-hash drift, replay-versus-real-LLM demand mismatch, and duplicate residue files.

## Bounded Goal
- reduce the parent into a smaller archive chain packet that preserves:
  - two executed steps plus queued third continuation
  - summary/soak/sequence count inflation to three
  - summary/state final hash versus last event endpoint split
  - queued third packet using the final hash as its input
  - replay attribution alongside `needs_real_llm true`
  - second-step schema fail and mixed survivor carryover
  - exact duplicate ` 3` file residue

## Why No Raw Source Reread
- the parent intake already retains the packet lattice, event rows, sequence counters, final-hash split, survivor carryover, duplicate residue files, and runtime-path leakage needed for second-pass compression
- the consulted A2-mid anchors already preserve the immediately preceding resume-stub floor and the adjacent two-step execution contrast

## Deferred Nearby Parents
- `BATCH_archive_surface_deep_archive_test_state_transition_chain_b__v1`
  - best next target once the exact-duplicate chain-A contradiction packet is preserved
- `BATCH_archive_surface_deep_archive_test_state_transition_mutation__v1`
  - useful later for mutation-side divergence after both chain variants are reduced


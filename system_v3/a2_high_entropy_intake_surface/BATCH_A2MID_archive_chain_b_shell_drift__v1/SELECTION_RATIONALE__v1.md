# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / BOUNDED A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_archive_chain_b_shell_drift__v1`
Date: 2026-03-09

## Why This Parent
- `BATCH_archive_surface_deep_archive_test_state_transition_chain_b__v1` is the next untouched deep-archive test parent after chain A.
- it preserves the same high-value chain contradiction as chain A, but with a distinct residue profile:
  - mixed-suffix duplicate files
  - empty `zip_packets 2/` shell
- that makes it the cleanest follow-on comparison batch rather than a duplicate of chain A.

## Bounded Goal
- reduce the parent into a smaller archive chain-variant packet that preserves:
  - two executed steps plus queued third continuation
  - three-step count inflation
  - final-hash versus last-event split
  - replay-versus-real-LLM demand mismatch
  - second-step schema fail and mixed survivor carryover
  - mixed-suffix duplicate file family
  - empty `zip_packets 2/` shell as packaging residue

## Why No Raw Source Reread
- the parent intake already retains the event/state/hash contradictions, queued third packet, duplicate-file pattern, empty-shell residue, and runtime-path leakage needed for second-pass compression
- the consulted A2-mid anchors already preserve the direct chain-A comparison and the preceding resume-stub floor

## Deferred Nearby Parents
- `BATCH_archive_surface_deep_archive_test_state_transition_mutation__v1`
  - best next target once both chain variants are reduced
- `BATCH_archive_surface_deep_archive_run_foundation_packet_failure__v1`
  - useful later for non-chain archive packet-failure comparison


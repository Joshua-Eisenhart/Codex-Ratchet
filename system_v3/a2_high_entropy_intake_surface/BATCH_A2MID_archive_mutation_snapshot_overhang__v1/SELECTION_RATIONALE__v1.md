# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / BOUNDED A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_archive_mutation_snapshot_overhang__v1`
Date: 2026-03-09

## Why This Parent
- `BATCH_archive_surface_deep_archive_test_state_transition_mutation__v1` is the next untouched compact archive-test parent after both chain variants.
- it keeps the archive-test lane bounded while changing the contradiction shape:
  - one executed mutation step instead of a multi-step chain
  - final snapshot/state closure above the only event row
  - snapshot/export residue that outruns final bookkeeping
  - duplicate ` 2` file and empty-shell packaging noise
- that makes it the cleanest next archive packet after `chain_a` and `chain_b`, rather than reopening the chain family again.

## Bounded Goal
- reduce the parent into a smaller archive mutation packet that preserves:
  - the one-step executed strategy/export/snapshot spine with two SIM returns
  - final-hash authority over the sole event endpoint
  - zero packet parks alongside two `PARKED` promotion states
  - snapshot `EVIDENCE_PENDING` residue above empty final `evidence_pending`
  - export/snapshot `KILL_IF ... NEG_NEG_BOUNDARY` residue above empty final `kill_log`
  - duplicate ` 2` files, empty residue directories, and runtime-path leakage as residue only

## Why No Raw Source Reread
- the parent intake already retains the one-step executed core, final-hash split, promotion contradiction, snapshot/export overhang, duplicate ` 2` family, empty shells, and runtime-path leakage needed for second-pass compression
- the consulted A2-mid anchors already preserve the nearby chain-variant floor and the earlier resume-stub residue comparison

## Deferred Nearby Parents
- `BATCH_archive_surface_deep_archive_v2_zipv2_packet_e2e_001__v1`
  - strongest next target once the mutation-side contradiction packet is preserved
- `BATCH_archive_surface_deep_archive_run_foundation_packet_failure__v1`
  - useful later for packet-failure comparison outside the compact archive-test strip

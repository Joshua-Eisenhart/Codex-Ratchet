# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_test_resume_001__v1`
Date: 2026-03-09

## Cluster 1: Zero-Work External Handoff Run
- archive meaning:
  - this run preserves outbound A0-to-A1 request behavior without any accepted, parked, rejected, or simulated work
- bound evidence:
  - summary and soak both report `accepted 0`, `parked 0`, `rejected 0`
  - stop reason is `A1_NEEDS_EXTERNAL_STRATEGY`
  - final state keeps zero accepted batches, zero canonical ledger items, zero sim registry entries, and zero survivor entries
- retained interpretation:
  - useful historical example of a run that stops at the external strategy boundary rather than at a lower-loop execution boundary

## Cluster 2: Duplicate Step-1 Save Requests
- archive meaning:
  - the archive preserves two outbound save requests even though the summary claims only one step and both event rows still report `step 1`
- bound evidence:
  - `summary.json` keeps `steps_completed 1` and `steps_requested 1`
  - `events.jsonl` has two `a1_strategy_request_emitted` rows
  - both event rows retain `step 1`
  - `zip_packets/` contains sequence `1` and sequence `2` save zips
- retained interpretation:
  - useful archive evidence of duplicate external request emission inside a one-step shell

## Cluster 3: Active-Runtime Path Leakage Inside Archived Events
- archive meaning:
  - the archived event ledger points to live-runtime absolute paths rather than archive-local packet paths
- bound evidence:
  - each `a1_strategy_request_emitted` row stores an `a0_to_a1_save_zip` path under `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/...`
  - the actual preserved packets live under `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/.../TEST_RESUME_001/zip_packets/`
- retained interpretation:
  - useful historical seam between live runtime provenance and later archive relocation

## Cluster 4: Duplicated Save Payload With Sequence-Only Header Drift
- archive meaning:
  - the two outbound save packets carry the same `A0_SAVE_SUMMARY.json` and `MANIFEST.json`, with only `ZIP_HEADER.json` changing between sequences
- bound evidence:
  - both packets share identical member hashes for `A0_SAVE_SUMMARY.json` and `MANIFEST.json`
  - the packet-level sha256 differs
  - header sequence changes from `1` to `2`
  - top-level save summary still reports `step 1` in both packets
- retained interpretation:
  - useful archive example of replayed or retried handoff packaging without payload progression

## Cluster 5: Real State Hash Wrapped Around Sample Strategy Payload
- archive meaning:
  - the save packet binds to the run’s real final state hash at the top level while embedding a generic sample strategy with placeholder hashes and a zero input state hash
- bound evidence:
  - `A0_SAVE_SUMMARY.state_hash` equals `de0e5fe9...`
  - embedded `base_strategy.strategy_id` is `STRAT_SAMPLE_0001`
  - embedded `base_strategy.inputs.state_hash` is all zeroes
  - embedded self-audit and rule hashes are repeated `1111...`, `2222...`, `3333...`, `4444...` placeholders
- retained interpretation:
  - useful historical example of generic resume payload scaffolding wrapped in run-specific outer metadata

## Cluster 6: Inert Machine State With Rich Lexical Shell
- archive meaning:
  - no operational state survives, but lexical and formula requirement surfaces still remain populated
- bound evidence:
  - `state.json` keeps empty registries for probes, specs, sims, survivors, rejects, kills, and evidence
  - `derived_only_terms`, `formula_glyph_requirements`, and `l0_lexeme_set` remain populated
- retained interpretation:
  - useful archive example of static vocabulary scaffolding surviving after operational state has collapsed to zero

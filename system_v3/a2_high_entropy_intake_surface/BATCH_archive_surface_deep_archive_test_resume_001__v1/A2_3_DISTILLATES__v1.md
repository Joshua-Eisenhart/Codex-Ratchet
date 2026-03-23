# A2_3_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_test_resume_001__v1`
Date: 2026-03-09

## Distillate 1
`TEST_RESUME_001` is a zero-work A0-to-A1 handoff stub with no retained inbound strategy, no earned state change, and stop reason `A1_NEEDS_EXTERNAL_STRATEGY`.

## Distillate 2
Its main historical contradiction is duplicate request emission inside a one-step shell: summary reports one step, but the event ledger preserves two `a1_strategy_request_emitted` rows and two outbound save packets.

## Distillate 3
The second save packet is not a progressed payload. It reuses the exact same `A0_SAVE_SUMMARY.json` and `MANIFEST.json` as the first packet, changing only the header sequence from `1` to `2`.

## Distillate 4
Event provenance leaks the old live-runtime location: archived event rows point to `system_v3/runtime/.../zip_packets/...` rather than to the archive-local packet paths now preserved.

## Distillate 5
The retained save payload is generic sample scaffolding: `STRAT_SAMPLE_0001`, placeholder audit hashes, and an inner all-zero input state hash wrapped by an outer run-specific hash `de0e5fe9...`.

# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / BOUNDED A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_archive_v2_replay_hashbridge_schemafail__v1`
Date: 2026-03-09

## Why This Parent
- `BATCH_archive_surface_deep_archive_v2_zipv2_replay_001__v1` is the next untouched ZIPv2 sibling after the request-side bootstrap batch.
- it keeps the archive strip bounded while changing the contradiction shape:
  - two executed replay steps plus a queued third strategy packet
  - summary/soak count three while the event ledger retains only two steps
  - replay authorship still coexists with `needs_real_llm true`
  - step-2 `SCHEMA_FAIL` advances only the alternative lane in final state
  - packet-facing evidence and kill residue outrun final bookkeeping
- that makes it the cleanest replay-side sibling to the earlier packet-e2e and request-only ZIPv2 reductions.

## Bounded Goal
- reduce the parent into a smaller replay-side contradiction packet that preserves:
  - two executed replay steps plus one queued third strategy packet
  - three-count summary/soak surfaces versus two-step event retention
  - both hidden hash bridges across the executed spine and final retained state
  - replay labeling with real-LLM demand and no retained inbox continuation
  - step-2 `SCHEMA_FAIL` with only the alternative `S0002` lane surviving
  - packet-facing evidence and kill residue above empty final bookkeeping

## Why No Raw Source Reread
- the parent intake already retains the executed-step spine, queued third packet, hidden hash bridges, replay-versus-real-LLM seam, schema-fail asymmetry, and packet-facing residue needed for second-pass compression
- the consulted A2-mid ZIPv2 anchors already preserve the closest request-side and packet-e2e sibling comparisons

## Deferred Nearby Parents
- `BATCH_archive_surface_heat_dumps_root_family_split__v1`
  - strongest next untouched archive parent after the compact ZIPv2 strip completes
- `BATCH_archive_surface_deep_archive_run_foundation_packet_failure__v1`
  - useful later for broader packet-failure comparison outside the ZIPv2 family

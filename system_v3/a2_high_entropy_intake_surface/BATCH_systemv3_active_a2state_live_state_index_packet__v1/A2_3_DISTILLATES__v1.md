# A2_3_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / OUTER DISTILLATE
Batch: `BATCH_systemv3_active_a2state_live_state_index_packet__v1`
Extraction mode: `ACTIVE_A2_LIVE_STATE_AND_INGEST_INDEX_PASS`
Date: 2026-03-09

## Distillate D1
- proposal-only read:
  - the remaining `a2_state` packet is not more narrative policy; it is the system’s live registry/index layer

## Distillate D2
- proposal-only read:
  - the active A2 state keeps at least four distinct store types separate:
    - compact registries and snapshots
    - ingest indices
    - curated doc-card abstractions
    - append-log memory plus shard history

## Distillate D3
- proposal-only read:
  - the two `215`-doc ingest indices are membership-equivalent but still distinct artifacts with separate generation times and hashes

## Distillate D4
- proposal-only read:
  - `doc_index.json` is the broader classification layer, not just another copy of the ingest index

## Distillate D5
- proposal-only read:
  - the doc-card and system-map packet is a curated role overlay over a smaller subset, not a one-to-one mirror of the ingest inventory

## Distillate D6
- proposal-only read:
  - the doc-card/system-map overlay uses an id and path scheme that does not cleanly match the active ingest index and therefore needs explicit reconciliation rather than silent normalization

## Distillate D7
- proposal-only read:
  - `memory.jsonl` is mostly autosave cadence around a smaller but meaningful stream of tuning, audit, runtime-fix, campaign, and ingest events

## Distillate D8
- proposal-only read:
  - `memory_shard_000001.jsonl` acts as the older semantic base layer while `memory.jsonl` functions as the current append log opening from that shard

## Distillate D9
- proposal-only read:
  - the system already keeps small active registries for:
    - rosetta mappings
    - campaign status
    - blocked concepts
    - A1 brain events
    - extracted fuel fragments

## Distillate D10
- proposal-only quarantine:
  - do not collapse kernel survivors, constraint survivors, rosetta mappings, and autosave counters into one progress metric

## Distillate D11
- proposal-only quarantine:
  - do not infer trustworthy admission from indexed presence alone; `doc_index.json` explicitly retains quarantined high-entropy sources

## Distillate D12
- proposal-only next-step note:
  - with the remaining source-like `a2_state` packet now bounded, the next pass should move into the first active `a1_state` campaign/control family

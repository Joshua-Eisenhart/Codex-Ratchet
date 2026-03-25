# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_systemv3_active_a2state_live_state_index_packet__v1`
Extraction mode: `ACTIVE_A2_LIVE_STATE_AND_INGEST_INDEX_PASS`
Batch scope: remaining source-like `a2_state` live-state packet covering memory stores, A1/A2 registries, ingest indices, doc cards, integrity sidecars, and lightweight control snapshots
Date: 2026-03-09

## 1) Folder-Order Selection
- the prior bounded batch stopped at:
  - `SYSTEM_V3_FULL_SURFACE_INTEGRATION_AUDIT__v1.md`
- this bounded batch covers the rest of the source-like `a2_state` residue:
  - `a1_brain.jsonl`
  - `autosave_seq.txt`
  - `campaign_status/CAMPAIGN_STATUS__20260224T225042Z.json`
  - `constraint_surface.json`
  - `core_docs_ingest_index_v1.json`
  - `core_docs_ingest_index_v1.sha256`
  - `doc_index.json`
  - `fuel_queue.json`
  - `ingest/index_v1.json`
  - `ingest/index_v1.sha256`
  - `ingest/system_map_v1.md`
  - `ingest/doc_cards/*.md` (`30` files)
  - `memory.jsonl`
  - `memory_shards/index_v1.json`
  - `memory_shards/index_v1.sha256`
  - `memory_shards/memory_shard_000001.jsonl`
  - `rosetta.json`
- bundling reason:
  - these surfaces collectively encode the current active A2 live-state layer:
    - event memory
    - shard linkage
    - A1/A2 side registries
    - ingest cataloging
    - doc-card abstraction
    - snapshot counters and integrity sidecars
- handoff after this batch:
  - the remaining active-priority queue leaves `a2_state/` and moves into `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/`
- deferred next docs in priority order:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_BRAIN_SLICE__v1.md`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_CARTRIDGE_REVIEW__ACTIVE_FAMILY_CROSS_JUDGMENT__v1.md`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_CARTRIDGE_REVIEW__CORRELATION_DIVERSITY_FUNCTIONAL__v1.md`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_CARTRIDGE_REVIEW__CORRELATION_POLARITY__v1.md`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_CARTRIDGE_REVIEW__ENTROPY_PRODUCTION_RATE__v1.md`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_CARTRIDGE_REVIEW__PROBE_OPERATOR__v1.md`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_ENTROPY_BRANCH_BUDGET_AND_MERGE_PACK__v1.md`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_ENTROPY_BRIDGE_COLDER_WITNESS_PACK__v1.md`

## 2) Source Membership By Subfamily
- live state and lightweight control:
  - `a1_brain.jsonl`
  - `autosave_seq.txt`
  - `campaign_status/CAMPAIGN_STATUS__20260224T225042Z.json`
  - `constraint_surface.json`
  - `fuel_queue.json`
  - `rosetta.json`
- ingest indices and integrity sidecars:
  - `core_docs_ingest_index_v1.json`
  - `core_docs_ingest_index_v1.sha256`
  - `doc_index.json`
  - `ingest/index_v1.json`
  - `ingest/index_v1.sha256`
- doc-card abstraction packet:
  - `ingest/system_map_v1.md`
  - `ingest/doc_cards/*.md` (`30` files)
- memory chain packet:
  - `memory.jsonl`
  - `memory_shards/index_v1.json`
  - `memory_shards/index_v1.sha256`
  - `memory_shards/memory_shard_000001.jsonl`
- full hashes, sizes, and line counts for all `46` source members are preserved in `MANIFEST.json`

## 3) Live State And Control Registry Packet
- `a1_brain.jsonl:1-5`
  - stores five A1 events:
    - FEP-to-QIT steelman notes
    - one `A1_ROSETTA_DISTILLERY_INGEST_EVENT_v1`
    - dual-thread rosetta delta ingest
    - CODEX-only execution blueprint
    - audit-surface alignment fix
- `autosave_seq.txt:1`
  - current autosave counter is `233`
- `campaign_status/CAMPAIGN_STATUS__20260224T225042Z.json:1-33`
  - compact A2 awareness snapshot
  - records `7` kernel survivors and `3` parked sim-promotion entries
  - explicitly says it is not a per-loop history dump
- `constraint_surface.json:1-43`
  - compact constraint/graveyard summary
  - records `43` survivors, `8` graveyard items, ratio `0.157`
  - rejection reasons are limited to:
    - `DERIVED_ONLY_PRIMITIVE_USE`
    - `UNDEFINED_TERM_USE`
- `fuel_queue.json:1-4883`
  - large distilled queue with `603` entries
  - tags skew heavily toward:
    - `DERIVE`
    - `OPEN`
    - `ASSUME`
  - the heaviest source-doc contributors are refined-fuel admissibility docs, not high-entropy inputs
- `rosetta.json:1-252`
  - active bidirectional jargon-to-B mapping store
  - carries `41` mappings
  - note says it is updated when B admits terms and when A1 reports back

## 4) Ingest Index And Classification Packet
- `core_docs_ingest_index_v1.json:1`
  - `215` indexed docs
  - schema `DOC_INDEX_v1`
- `ingest/index_v1.json:1`
  - also `215` indexed docs
  - same schema and same doc membership as `core_docs_ingest_index_v1.json`
  - generated at a different time and hashes to a different file value
- `core_docs_ingest_index_v1.sha256:1`
  - integrity sidecar for the root ingest index
- `ingest/index_v1.sha256:1`
  - integrity sidecar for the ingest-subtree index
- `doc_index.json:1`
  - broader `A2_DOC_INDEX_v1` classification layer with `222` documents
  - layers split across:
    - `A1_FUEL_RATCHET_FUEL`
    - `A2_FUEL_HIGH_ENTROPY`
    - `UPGRADE_DOCS`
    - `A2_ARCHIVED_STATE`
    - `CORE_DOCS_OTHER`
  - includes `16` `QUARANTINE_SOURCE` entries
  - also includes `7` extra paths not present in the `215`-doc ingest indices:
    - `core_docs/Archive.zip`
    - three `__pycache__/*.pyc` files
    - three extra high-entropy text surfaces

## 5) System Map And Doc Card Packet
- `ingest/system_map_v1.md:1-64`
  - role-indexes a curated subset across:
    - `A2`
    - `A1`
    - `A0`
    - `B`
    - `SIM`
  - contains `53` references over only `21` unique `DOC_*` identifiers
  - reuses the same doc identifiers across multiple roles
- `ingest/doc_cards/*.md`
  - `30` curated doc-card surfaces with repeated sections:
    - `PURPOSE`
    - `HARD_FENCES`
    - `CONTAINERS`
    - `ALLOWED_SPEC_KINDS`
    - `FORBIDDEN_PRIMITIVES`
    - `ROLE_IN_SYSTEM`
    - `OPEN_QUESTIONS`
  - role counts are mixed and non-exclusive:
    - `B` appears most often
    - `A1`, `A0`, `SIM`, `A2`, and `UNMAPPED` all appear
  - most cards say `NONE_SPECIFIED` for allowed spec kinds, but some preserve `MATH_DEF`, `CANON_PERMIT`, `TERM_DEF`, `LABEL_DEF`, and smaller special kinds
- important cross-surface observation:
  - the doc-card `DOC_*` id namespace matches `system_map_v1.md`
  - it does not match the `doc_id` namespace in `ingest/index_v1.json`
  - `system_map_v1.md` path strings also use older path labels that do not match the current ingest-index paths exactly

## 6) Memory Chain Packet
- `memory_shards/index_v1.json:1`
  - one-shard index pointing to `memory_shard_000001.jsonl`
- `memory_shards/index_v1.sha256:1`
  - integrity sidecar for the shard index
- `memory_shards/memory_shard_000001.jsonl:1-160`
  - older base shard dominated by:
    - `learned`
    - `intent`
    - `decision`
  - also contains smaller autosave, failed, and system entries
- `memory.jsonl:1-323`
  - live append log begins by opening the prior shard
  - then records `323` lines, dominated by `220` `a2_autosave_tick` entries
  - the rest is a mixed event stream of campaign, audit, tuning, storage, runtime-fix, A1 process, and stage-2 ingest events
  - the last autosave tick reports:
    - `seq = 233`
    - `file_count = 40`
    - `total_bytes = 717857`
  - that aligns with `autosave_seq.txt`

## 7) Source-Class Read
- best classification:
  - active A2 operational state packet with generated registries, ingest metadata, curated abstraction layers, and memory-chain continuity
- strongest direct value:
  - shows how A2 currently stores memory, A1 feedback, rosetta mappings, fuel extraction, and corpus indexing
  - preserves both rawer index layers and curated doc-card abstraction layers
  - exposes integrity sidecars and shard linkage rather than only the content files
  - completes the active `a2_state` sweep without mutating the stores
- caution:
  - these surfaces mix authoritative-looking counters with generated overlays and housekeeping noise
  - count values across campaign, constraint, rosetta, and memory surfaces are not interchangeable
  - doc-card and system-map ids/paths cannot be silently unified with the ingest-index ids/paths

# ZIP, Save, and Tapes Spec
Status: DRAFT / NONCANON
Date: 2026-02-20
Owner: `RQ-090..RQ-096`

Companion repair targets:
- semantic `FULL+` restore bundle:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/73_FULL_PLUS_SEMANTIC_SAVE_ZIP__v1.md`
- A0 save/report surfaces:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/74_A0_SAVE_REPORT_SURFACES__v1.md`

## ZIP_JOB Carrier (`RQ-090`)
- `RQ-090` MUST: inter-thread communication uses `ZIP_JOB` bundles as atomic deterministic carriers.

## ZIP No-Split + Deterministic Sharding (`RQ-091`, `RQ-092`)
- `RQ-091` MUST: ZIP containers never split; sharding happens only by splitting documents *inside* a single ZIP.
- `RQ-092` MUST: shard deterministically inside ZIP with strict limits:
  - `MAX_TEXT_FILE_BYTES = 65536`
  - `MAX_TEXT_FILE_LINES = 2000`
  - ASCII-only content (no curly quotes); LF-only newlines
  - if exceeded: shard as `<name>_0001.<ext>`, `<name>_0002.<ext>`, ... (same ZIP)

## ZIP_JOB as Deterministic Subagent (Operational)
Source intent (non-normative pointer): Megaboot describes ZIPs as “deterministic, chatless subagents”.

Operational meaning in v3:
- a `ZIP_JOB` is a single atomic bundle that can be moved between threads/tools without any prose context
- the bundle is self-describing via an internal manifest
- the bundle can be validated deterministically before use
- ZIP ingestion is a single-line deterministic action (no multi-step conversational unpacking)

`ZIP_JOB` is a carrier protocol above the kernel boundary:
- B does not ingest ZIPs directly
- B ingests only its accepted containers (e.g. `EXPORT_BLOCK`, `SIM_EVIDENCE`, snapshot)

## ZIP_JOB Internal Manifest (Active Stage-2 Profile)
Every ZIP_JOB MUST contain:

1) `ZIP_JOB_MANIFEST_v1.json`
- ASCII-only, LF-only
- deterministic JSON key ordering (sorted)
- current live Stage-2 validator requires these top-level keys:
  - `schema`
  - `zip_job_id`
  - `zip_job_kind`
  - `producer_role`
  - `consumer_role`
  - `text_profile`
  - `source_reference_list`
  - `task_execution_order`
  - `required_output_file_list`
  - `file_sha256_registry`
- compatibility aliases may still appear in live templates during migration:
  - `producer`
  - `consumer`
  - `task_order`
  - `source_refs`
  - `expected_outputs`
- `task_execution_order` is the active execution list; `task_order` is legacy alias only
- `source_reference_list` is the active source list; `source_refs` is legacy alias only

Schema:
```json
{
  "schema": "ZIP_JOB_MANIFEST_v1",
  "zip_job_id": "ZIP_JOB__<KIND>__<UTC>__<HASH12>",
  "zip_job_kind": "A2_FUEL|A1_STRATEGY|A1_BATCH|EXPORT_BLOCK|SIM_REQUEST|SIM_RESULTS|SIM_EVIDENCE_PACK|FULL_PLUS_SAVE|FULL_PLUS_PLUS_ARCHIVE|TAPE",
  "created_utc": "YYYY-MM-DDTHH:MM:SSZ",
  "producer_role": "THREAD_A2|THREAD_A1|THREAD_A0|THREAD_SIM|EXTERNAL",
  "consumer_role": "THREAD_A2|THREAD_A1|THREAD_A0|THREAD_B|THREAD_SIM|EXTERNAL",
  "text_profile": "UTF8_OK|ASCII_ONLY",
  "source_reference_list": [
    "core_docs/..."
  ],
  "task_execution_order": [
    "tasks/00_TASK__EXAMPLE.task.md"
  ],
  "required_output_file_list": [
    "output/EXAMPLE_OUTPUT__v1.md"
  ],
  "file_sha256_registry": {}
}
```

Shape note:
- `file_sha256_registry` is required by the active validator, but its exact container
  shape is still provisional in live templates (`{}` and `[]` both appear)

2) `SHA256SUMS.txt` (optional but recommended)
- one line per file: `<sha256>  <relative_path>`
- deterministic sort by `<relative_path>`

## Naming (Draft)
ZIP filename (suggested):
- `ZIP_JOB__<KIND>__<UTC>__<HASH12>.zip`

ZIP internal paths (current live template layout):
- `tasks/` (ordered task files referenced by `task_execution_order`)
- `output/` (required emitted outputs referenced by `required_output_file_list`)
- `meta/` (manifest + hashes live here)

## Save Levels (`RQ-093`)
- `RQ-093` MUST: save levels are explicit and stable:
  - `MIN`: fast rebootable checkpoint.
  - `FULL+`: canon restore carrier; sufficient to restore B canon and proceed without Rosetta.
  - `FULL++`: `FULL+` plus campaign tape plus optional Rosetta/mining overlays; never required by B.

Repair clarification:
- current generic save/profile ZIP exports are not automatically semantic `FULL+` restore bundles
- semantic `FULL+` bundle shape is defined in the companion repair spec

### Resume-State Surfaces (Operational)
- run-local resume continuity may use a split state surface:
  - `state.json`: lean resume/control surface
  - `state.heavy.json`: heavy derived cache sidecar
- `_CURRENT_STATE/state.json` is allowed only as a lean current-run pointer/cache and must not duplicate full run state
- `_CURRENT_STATE/sequence_state.json` is allowed as the matching lean live sequence cache
- numbered `_CURRENT_STATE/state N.json` and `_CURRENT_STATE/sequence_state N.json` files are historical cache buildup, not authoritative lineage, and may be dropped during controlled thinning
- tools must treat ZIP packets and tapes as the authoritative lineage surfaces; broad duplicate text exports are fallback/diagnostic only

### Regeneration Witness Retention (Operational)
- local runs should not retain full transient memo churn by default
- when a run or family must remain auditable across the memo -> cold-core -> selector path after transient pruning, retain a compact regeneration witness instead of the full transient workspace
- preferred retained witness shape for an anchor run or anchor family:
  - latest memo request or compact memo-summary witness
  - latest `A1_COLD_CORE_PROPOSALS_v1.json`
  - latest emitted `A1_STRATEGY_v1`
  - provenance note tying the triple together
- this witness is a replay/audit aid, not full transient history
- non-anchor runs may thin transient memo workspaces without preserving a regeneration witness when packet/state/report lineage is already sufficient for their intended role
- anchor runs or anchor families should prefer a compact repo-held witness or anchor-surface summary over keeping large transient memo directories locally
- when a normalized regeneration witness exists and the corresponding family-level doctrine has been migrated to anchor surfaces, the underlying run may be archive-demoted and the witness/anchor surfaces should be rewritten to the archive location in the same bounded move
- local retention should prefer:
  - `_CURRENT_STATE`
  - a small `ACTIVE` set
  - a small `ANCHOR` set
  over broad historical family run retention

### Packet-Journal Compaction (Provisional Operational Rule)
- packet compaction is class-specific; do not use one retention rule for every ZIP class
- current checkpoint-like classes:
  - `B_TO_A0_STATE_UPDATE_ZIP`
  - `A0_TO_A1_SAVE_ZIP`
- current operational compaction rule for those classes may retain:
  - earliest packet
  - latest packet
  - sparse checkpoints
  - recent tail
  and drop superseded interior packets
- current strategy-history compaction, when used, is more conservative:
  - `A1_TO_A0_STRATEGY_ZIP` may retain earliest/latest, sparse checkpoints, recent tail, and family-shape transitions
- `SIM_TO_A0_SIM_RESULT_ZIP` remains evidence-bearing and should not be compacted aggressively without stronger proof
- `A0_TO_B_EXPORT_BATCH_ZIP` is lower-value to compact than the snapshot and strategy classes and should not be treated as the primary size lever

### Archive Demotion After Anchor Coverage (Operational)
- when a run family has:
  - a run-anchor surface,
  - a regeneration-witness surface,
  - and repetitive family-level citations migrated away from raw local run paths,
  the underlying runs may be moved to external archive heat-dump storage without deletion
- this is a move-with-witness-rewrite operation:
  - move the run(s)
  - write a demotion manifest
  - rewrite anchor/witness surfaces to the archive paths in the same bounded step
- this allows local `system_v3/runs` to shrink without losing family-level doctrine or memo -> cold-core -> strategy auditability

## Campaign Tape (`RQ-094`)
- `RQ-094` MUST: `CAMPAIGN_TAPE v1` is mandatory and append-only.
- `RQ-094` MUST: `CAMPAIGN_TAPE v1` records `(EXPORT_BLOCK + THREAD_B_REPORT)` pairs in canonical order.

### CAMPAIGN_TAPE v1 (File Format; Deterministic JSONL)
Run-scope location (default):
- `system_v3/runs/<run_id>/tapes/campaign_tape.000.jsonl` (shardable)

Each line is one JSON object with sorted keys:
- required keys:
  - `seq` (monotonic int)
  - `export_id` (verbatim from EXPORT_BLOCK header; else `UNKNOWN_EXPORT_ID`)
  - `export_block_sha256`
  - `export_block_relpath`
  - `thread_b_report_sha256`
  - `thread_b_report_relpath`
- optional keys:
  - `snapshot_sha256`
  - `snapshot_relpath`
  - `sim_evidence_pack_sha256s[]`
  - `sim_evidence_pack_relpaths[]`
  - `notes` (noncanon; must not affect determinism if excluded from canonical hashing)

Deterministic sharding:
- follow `RQ-092` shard limits.
- shard suffix: `.000.jsonl`, `.001.jsonl`, ...

## Export Tape (`RQ-095`)
- `RQ-095` MUST: `EXPORT_TAPE v1` is a pre-run ordered list of `EXPORT_BLOCK`s (no B reports).
- `RQ-095` MUST: after execution, `EXPORT_TAPE v1` can be promoted into `CAMPAIGN_TAPE v1` by appending the corresponding B reports in order.

### EXPORT_TAPE v1 (File Format; Deterministic JSONL)
Run-scope location (default):
- `system_v3/runs/<run_id>/tapes/export_tape.000.jsonl` (shardable)

Each line is one JSON object:
- `seq` (monotonic int)
- `export_id` (verbatim or `UNKNOWN_EXPORT_ID`)
- `export_block_sha256`
- `export_block_relpath`

Authoritative source rule:
- when `A0_TO_B_EXPORT_BATCH_ZIP` packet lineage exists, `export_block_relpath` should point to the packet-member provenance rather than requiring a duplicated `outbox/export_block_*.txt` file

## Graveyard Rescue Share (`RQ-096`)
- `RQ-096` MUST: when graveyard is non-empty, A0 targets `>= 50%` graveyard-rescue share in each batch (by count), subject to caps.

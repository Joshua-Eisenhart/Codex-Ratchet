# ZIP, Save, and Tapes Spec
Status: DRAFT / NONCANON
Date: 2026-02-20
Owner: `RQ-090..RQ-096`

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

## ZIP_JOB Internal Manifest (Draft Schema)
Every ZIP_JOB MUST contain:

1) `ZIP_JOB_MANIFEST_v1.json`
- ASCII-only, LF-only
- deterministic JSON key ordering (sorted) and deterministic list ordering (sort by `path`)

Schema:
```json
{
  "schema": "ZIP_JOB_MANIFEST_v1",
  "zip_job_id": "ZIP_JOB__<KIND>__<UTC>__<HASH12>",
  "kind": "A2_FUEL|A1_STRATEGY|A1_BATCH|EXPORT_BLOCK|SIM_REQUEST|SIM_RESULTS|SIM_EVIDENCE_PACK|FULL_PLUS_SAVE|FULL_PLUS_PLUS_ARCHIVE|TAPE",
  "created_utc": "YYYY-MM-DDTHH:MM:SSZ",
  "producer": "THREAD_A2|THREAD_A1|THREAD_A0|THREAD_SIM|EXTERNAL",
  "consumer": "THREAD_A2|THREAD_A1|THREAD_A0|THREAD_B|THREAD_SIM|EXTERNAL",
  "source_refs": [
    {"path": "core_docs/...", "sha256": "<hex>"}
  ],
  "files": [
    {"path": "payload/<name>.txt", "sha256": "<hex>", "bytes": 1234}
  ]
}
```

2) `SHA256SUMS.txt` (optional but recommended)
- one line per file: `<sha256>  <relative_path>`
- deterministic sort by `<relative_path>`

## Naming (Draft)
ZIP filename (suggested):
- `ZIP_JOB__<KIND>__<UTC>__<HASH12>.zip`

ZIP internal paths (suggested):
- `payload/` (all payload files live here)
- `meta/` (manifest + hashes live here)

## Save Levels (`RQ-093`)
- `RQ-093` MUST: save levels are explicit and stable:
  - `MIN`: fast rebootable checkpoint.
  - `FULL+`: canon restore carrier; sufficient to restore B canon and proceed without Rosetta.
  - `FULL++`: `FULL+` plus campaign tape plus optional Rosetta/mining overlays; never required by B.

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

## Graveyard Rescue Share (`RQ-096`)
- `RQ-096` MUST: when graveyard is non-empty, A0 targets `>= 50%` graveyard-rescue share in each batch (by count), subject to caps.

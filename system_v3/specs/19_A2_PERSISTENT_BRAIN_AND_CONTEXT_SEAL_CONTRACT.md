# A2 Persistent Brain and Context Seal Contract
Status: DRAFT / NONCANON
Date: 2026-02-20
Owner: `RQ-109..RQ-116`

## Scope
This document defines canonical A2 state schemas, seal mechanics, compaction mechanics, and sharding rules.

## Normative Clauses
- `RQ-109` MUST: every canonical A2 file declares `schema` and `schema_version`; writes with unknown schema version are rejected.
- `RQ-110` MUST: each seal operation appends one deterministic `SEAL_RECORD` with source hash set, unresolved actions, and next-read pointers.
- `RQ-111` MUST: entropy compaction writes append-only derived summaries linked to exact source entry IDs; source entries remain immutable.
- `RQ-112` MUST: each fuel queue entry includes provenance (`source_paths[]`, `source_hashes[]`), dependency hints, and `validity_state`.
- `RQ-113` MUST: rosetta overlays are fully removable overlays and cannot mutate canonical B state projections.
- `RQ-114` MUST: contradiction records carry `status` in `{UNRESOLVED, WAIVED, RESOLVED}` plus evidence references and decision references.
- `RQ-115` MUST: document index refresh performs deterministic full scan with path-lexicographic ordering and stable sha256 content hashes.
- `RQ-116` MUST: A2 sharding policy is explicit and deterministic for append logs and derived registries.

## Current Live Compatibility Profile
Current live autosave/snapshot tooling is narrower than the full target-state contract below.

Observed live behavior on the active autosave path:
- `system_v3/tools/a2_state_persist_tick.py` appends lean autosave events to `memory.jsonl`
- current autosave event shape is compatibility-style, not full target-state seal shape:
  - required live keys observed: `ts`, `type`
  - common live autosave keys observed: `seq`, `manifest_sha256`, `file_count`, `total_bytes`
  - optional live autosave key observed: `latest_zip_sha256`
- memory sharding currently uses:
  - `system_v3/a2_state/memory_shards/index_v1.json`
  - shard files named `memory_shard_<N>.jsonl`
  - rollover event `type = memory_shard_open`
- live snapshot manifest emitted by `a2_state_persist_tick.py` / `a2_state_snapshot.py` is manifest-led:
  - manifest schema currently observed: `A2_STATE_MANIFEST_v1` or `A2_STATE_SNAPSHOT_MANIFEST_v1`
  - current manifest fields are centered on `file_count`, `total_bytes`, and `files[{rel_path,byte_size,sha256}]`
- optional latest zip path on the active autosave path is:
  - `system_v3/a2_state/snapshots/a2_state_snapshot_latest.zip`

Compatibility implication:
- the detailed sections below remain useful as the fuller target-state contract
- but the current live path does not yet enforce the full `schema_version` / `SEAL_RECORD` / canonical registry schema set described below
- audits should treat the autosave compatibility profile as the active implementation truth until the fuller seal contract is actually wired into the tools

## Canonical File Interface
Canonical directory:
- `system_v3/a2_state/`

Canonical files:
- `memory.jsonl` (append-only)
- `doc_index.json` (rewrite allowed; deterministic sort)
- `fuel_queue.json` (rewrite allowed; deterministic sort)
- `rosetta.json` (rewrite allowed; overlay-only)
- `constraint_surface.json` (derived; rewrite allowed)
- `INTENT_SUMMARY.md` (derived compaction)
- `MODEL_CONTEXT.md` (derived compaction)

## Schema: memory.jsonl
One JSON object per line.

Required keys:
- `schema`: `A2_MEMORY_ENTRY_v1`
- `entry_id`: monotonic lexical ID
- `ts_utc`: ISO-8601 UTC
- `entry_type`: string enum
- `content`: object or string
- `source_refs[]`: list of `{path, sha256}`
- `tags[]`: list of strings

Optional keys:
- `run_id`
- `state_hash`
- `derived_from_entry_ids[]`

## Schema: doc_index.json
Required top-level keys:
- `schema`: `A2_DOC_INDEX_v1`
- `schema_version`: `1`
- `generated_utc`
- `documents[]`

`documents[]` entry keys:
- `path`
- `sha256`
- `size_bytes`
- `layer`
- `source_local_status`

Legacy compatibility:
- `canon_status` may still be present in generated indices as a compatibility alias.
- `source_local_status` is the preferred field name because it does not imply earned ratchet truth.

Ordering:
- sorted strictly by `path` ascending.

## Schema: fuel_queue.json
Required top-level keys:
- `schema`: `A2_FUEL_QUEUE_v1`
- `schema_version`: `1`
- `generated_utc`
- `entries[]`

`entries[]` entry keys:
- `fuel_id`
- `label`
- `body`
- `source_paths[]`
- `source_hashes[]`
- `dependency_hints[]`
- `validity_state`: `ACTIVE|INVALIDATED|CONSUMED`
- `priority`

Ordering:
- sort key `(priority desc, fuel_id asc)`.

## Schema: rosetta.json
Required top-level keys:
- `schema`: `A2_ROSETTA_OVERLAY_v1`
- `schema_version`: `1`
- `mappings{}` object

Mapping entry required keys:
- `overlay_term`
- `kernel_target_id` or `kernel_target_term`
- `mapping_state`: `PROPOSED|ACTIVE|DEPRECATED`
- `source_refs[]`

Hard boundary:
- rosetta mappings are annotations only.

## Schema: contradiction registry
Location:
- `system_v3/a2_derived_indices_noncanonical/contradictions.yaml`

Required per entry:
- `contradiction_id`
- `statement_a`
- `statement_b`
- `status`: `UNRESOLVED|WAIVED|RESOLVED`
- `evidence_refs[]`
- `decision_refs[]`
- `updated_utc`

## SEAL_RECORD Contract
Location:
- `system_v3/a2_derived_indices_noncanonical/thread_seals.000.jsonl` (shardable)

One record per seal action.

Required keys:
- `schema`: `A2_SEAL_RECORD_v1`
- `seal_id`
- `ts_utc`
- `source_memory_head_entry_id`
- `source_memory_head_hash`
- `pending_actions[]`
- `next_read_set[]`
- `state_digest_hash`

## THREAD_CLOSEOUT_PACKET Sink (Operational Companion)
Location:
- `system_v3/a2_derived_indices_noncanonical/thread_closeout_packets.000.jsonl` (shardable)

Purpose:
- capture returned worker-thread closeout audits as repo-held comparison packets

Required keys:
- `schema`: `THREAD_CLOSEOUT_PACKET_v1`
- `captured_utc`
- `source_thread_label`
- `final_decision`
- `thread_diagnosis`
- `role_and_scope`
- `strongest_outputs`
- `keepers`
- `if_one_more_step`
- `risks`
- `handoff_packet`
- `closed_statement`

## Entropy Compaction Contract
Compaction direction:
- high entropy entries -> low entropy summaries

Compaction artifacts:
- `INTENT_SUMMARY.md`
- `MODEL_CONTEXT.md`

Compaction record requirement:
- each compaction write appends `A2_MEMORY_ENTRY_v1` with `entry_type = COMPACTION_EVENT`
- includes `derived_from_entry_ids[]`
- includes `output_hashes[]`

## Sharding Policy
Apply to append-only A2 logs:
- `MAX_BYTES_PER_SHARD = 65536`
- `MAX_LINES_PER_SHARD = 2000`
- suffix format `.000`, `.001`, `.002`, ...

Shard rollover rule:
- when either size or line limit reached, close current shard and open next shard.

Merge prohibition:
- closed shards are immutable.
- compaction/merge products are new files with new IDs.

## Deterministic Refresh Sequence (A2 Tick)
Ordered sequence:
1. refresh `doc_index.json`
2. append mining/decision entries to `memory.jsonl`
3. refresh `fuel_queue.json`
4. refresh overlay `rosetta.json`
5. refresh derived summaries (if compaction trigger hit)
6. append `SEAL_RECORD` if seal trigger hit

No reorder is allowed within one tick.

## Acceptance Criteria (Spec-Level)
1. missing `schema_version` in canonical file -> reject write.
2. out-of-order `entry_id` append in `memory.jsonl` -> reject write.
3. seal write without source hash set -> reject write.
4. fuel entry without provenance fields -> reject write.
5. contradiction entry missing status enum -> reject write.

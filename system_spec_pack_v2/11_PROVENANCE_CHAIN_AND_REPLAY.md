# Provenance Chain + Replay (v1)
Status: DRAFT / NONCANON
Date: 2026-02-20

Goal: make runs replayable and auditable without exploding documents.

==================================================
1) Provenance Objects
==================================================

Run directory stores:
- canonical state (`state.json`)
- append-only event log shards (`events.###.jsonl`)
- outbox shards (`outbox/export_blocks.###.txt`)
- sim manifests (`sim_manifests/*.json`)

==================================================
2) Event Log Record (JSONL)
==================================================

Each event record must include:
- `seq`: int (monotonic within shard)
- `ts_utc`: ISO-8601
- `stage`: enum (A2 | A1 | A0 | B | SIM | FEEDBACK)
- `event`: string (e.g., `strategy_loaded`, `export_block_written`, `accept`, `reject`, `sim_run`)
- `inputs_hash`: sha256 hex (canonical input object hash, if applicable)
- `outputs_hash`: sha256 hex (canonical output object hash, if applicable)
- `state_hash_before`: sha256 hex (optional)
- `state_hash_after`: sha256 hex (optional)

Optional but recommended:
- `prev_event_hash`: sha256 hex
- `event_hash`: sha256 hex

Hash chaining rule (if enabled):
- `event_hash = SHA256(prev_event_hash || canonical_json(event_record_without_hashes))`

==================================================
3) Strategy and LLM Provenance
==================================================

If A1 is LLM-driven:
- store hashes for:
  - prompt (canonicalized)
  - model id
  - response (canonicalized)
- store the *strategy* object itself in the run directory (as YAML/JSON)

Lean default:
- store only hashes + the final strategy declaration
- store raw transcripts only if explicitly enabled (opt-in)

==================================================
4) Replay Definition
==================================================

A run is replayable if:
- all artifacts used for acceptance are present in the run directory (or content-addressed store)
- deterministic components are pinned:
  - B bootpack id/hash (ruleset)
  - sim code hash
  - canonical state serialization

Replay means:
- same inputs + same ruleset + same sim code => same accept/reject outcomes and same hashes


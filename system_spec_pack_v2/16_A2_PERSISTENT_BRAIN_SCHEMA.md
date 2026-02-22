# A2 Persistent Brain Schema (v1)
Status: DRAFT / NONCANON
Date: 2026-02-20

Goal: make A2 persistent memory explicit, deterministic, and lean.

==================================================
1) Canonical A2 State Files
==================================================

Required fixed file set under `work/a2_state/`:
- `memory.jsonl` (append-only event memory)
- `doc_index.json` (document index for deterministic boot)
- `fuel_queue.json` (structured fuel candidates for A1)
- `rosetta.json` (overlay mappings, noncanon)
- `constraint_surface.json` (derived analysis snapshot)
- `INTENT_SUMMARY.md` (derived, human-readable compaction)
- `MODEL_CONTEXT.md` (derived, non-authoritative context)

No additional files are required for canonical A2 state.

==================================================
2) memory.jsonl Entry Schema
==================================================

Each line is a JSON object with required keys:
- `ts`: ISO-8601 UTC string
- `type`: enum `learned` | `decision` | `failure` | `constraint` | `todo` | `evidence`
- `content`: string (explicit statement; no opaque references only)

Optional keys:
- `source_paths`: list[string]
- `tags`: list[string]
- `run_id`: string
- `state_hash`: string

Hard rules:
- append-only (no in-place edits)
- one JSON object per line
- stable key order preferred for deterministic diffs

==================================================
3) doc_index.json Schema
==================================================

Minimum fields:
- `generated_utc`: ISO-8601 UTC
- `documents`: list of objects with:
  - `path`
  - `sha256`
  - `size_bytes`
  - `layer` (`A2` | `A1` | `A0` | `B` | `SIM` | `LADDER` | `OTHER`)

Hard rules:
- deterministic sort by `path`
- no inferred facts in index fields

==================================================
4) fuel_queue.json Schema
==================================================

Top-level:
- `schema`: `A2_FUEL_QUEUE_v1`
- `generated_utc`
- `entries`: ordered list

Entry fields:
- `id`: stable string id
- `label`: short explicit name
- `body`: source content fragment
- `source_doc`: source path
- `concepts_needed`: list[string]
- `priority`: int (lower = earlier attempt)

Hard rules:
- no direct canon claims in fuel entries
- no implicit dependencies; `concepts_needed` must be explicit

==================================================
5) rosetta.json Schema
==================================================

Top-level:
- `schema`: `A2_ROSETTA_v1`
- `mappings`: object keyed by overlay token

Mapping value fields:
- `b_spec_id` (canon reference when available)
- `binds`
- `state`
- `admitted_cycle` (bool)

Hard rules:
- rosetta never overrides canon
- rosetta terms are non-authoritative overlays only

==================================================
6) Compaction + Refresh Rules
==================================================

- `INTENT_SUMMARY.md` and `MODEL_CONTEXT.md` are derived artifacts.
- refresh trigger:
  - after every N appended memory entries, OR
  - before major planning/implementation phase
- summaries must reference source memory/doc paths when making specific claims.

==================================================
7) Do Not Do (A2)
==================================================

- Do NOT store canon decisions directly in A2 files without B evidence.
- Do NOT replace `memory.jsonl` with YAML as canonical log.
- Do NOT allow unbounded A2 file proliferation; keep fixed file set + deterministic updates.


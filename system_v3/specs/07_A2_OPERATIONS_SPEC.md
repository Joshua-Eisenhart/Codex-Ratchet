# A2 Operations Specification
Status: DRAFT / NONCANON
Date: 2026-02-20
Owner: `RQ-070..RQ-078`

## Role
A2 is system debug/upgrade/mining/orchestration memory layer.
This thread is operating in A2 function.

Schema-depth companion:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md`

## Mining Function
A2 is the miner for:
- high-entropy docs
- prior thread transcripts
- failed-run artifacts

Mining outputs are structured fuel and explicit contradiction/risk records.

## Persistent Brain (`RQ-070`)
Canonical A2 persistent state lives under `system_v3/a2_state/`.

Required artifacts (fixed interface):
- append-only:
  - `system_v3/a2_state/memory.jsonl`
- registries (rewrite allowed; deterministic ordering required):
  - `system_v3/a2_state/doc_index.json`
  - `system_v3/a2_state/fuel_queue.json`
  - `system_v3/a2_state/rosetta.json` (noncanon overlay map; never overrides canon)
  - `system_v3/a2_state/constraint_surface.json` (derived snapshot; regenerable)
- derived context compactions (human-readable; non-authoritative):
  - `system_v3/a2_state/INTENT_SUMMARY.md`
  - `system_v3/a2_state/MODEL_CONTEXT.md`

Optional (non-required) A2 helper indices may live under `system_v3/a2_derived_indices_noncanonical/` as derived views
over the canonical A2 state (regenerable; bounded; never treated as canon inputs).

Optional derived index set (bounded; regenerable; noncanon):
- `system_v3/a2_derived_indices_noncanonical/brain_manifest.yaml` (pointers + hashes + shard map)
- `system_v3/a2_derived_indices_noncanonical/decisions.yaml` (extracted from `memory.jsonl` entries of type `decision`)
- `system_v3/a2_derived_indices_noncanonical/contradictions.yaml` (extracted from `memory.jsonl` + doc audits)
- `system_v3/a2_derived_indices_noncanonical/pending_actions.yaml` (extracted from `memory.jsonl` + open TODOs)
- `system_v3/a2_derived_indices_noncanonical/thread_seals.000.jsonl` (append-only seal cadence log; shardable)

YAML usage:
- YAML is permitted above the kernel boundary for authoring/drafts (A2/A1).
- Canonical A2 state remains JSON/JSONL for deterministic hashing and stable tooling.

## Canonical Schemas (Summary)
`memory.jsonl` (append-only):
- one JSON object per line
- required keys: `ts` (ISO-8601 UTC), `type`, `content`
- optional keys: `source_paths[]`, `tags[]`, `run_id`, `state_hash`

`doc_index.json` (rewrite allowed; deterministic sort):
- required: `generated_utc`, `documents[]`
- document fields: `path`, `sha256`, `size_bytes`, `layer`
- deterministic ordering: sort `documents` by `path`

`fuel_queue.json` (rewrite allowed; deterministic ordering):
- required: `schema`, `generated_utc`, `entries[]`
- entry fields: `id`, `label`, `body`, `source_doc`, `concepts_needed[]`, `priority`

`rosetta.json` (rewrite allowed; overlay only):
- required: `schema`, `mappings{overlay_term: mapping}`
- mapping fields: `b_spec_id` (optional), `binds` (optional), `state` (optional)

`constraint_surface.json` (derived; regenerable):
- derived snapshot of failure patterns + graveyard summaries for A1/A2 use
- must not be treated as canon authority

## Contradiction Handling (`RQ-071`)
A2 must:
- preserve conflict pairs with source pointers
- mark unresolved items explicitly
- avoid forced narrative harmonization

## Upgrade and Debug Function (`RQ-072`)
A2 responsibilities:
- diagnose A1/A0/B/SIM failure patterns
- draft upgrade specs and deltas
- maintain boundary discipline across layers

## Lean Doc Interface (`RQ-073`)
Controls:
- fixed primary file interfaces
- append+shard logs
- bounded generated output areas
- archive separation for large artifacts

## Reversible Upgrade Discipline (`RQ-074`)
Upgrades must be:
- additive in versioned paths
- manifested
- rollback-capable by path switch

## Seal Cadence (`RQ-075`)
A2 must maintain:
- periodic thread seals
- seal triggers: scope completion, context risk, or batch milestone
- explicit pending-action queue update at seal time

## Delta Manifest Requirement (`RQ-076`)
Each upgrade set includes:
- changed files list
- requirement ids impacted
- unresolved gaps
- migration notes

## Model Declaration (`RQ-077`)
Each major task must record:
- active model
- reason for model choice
- boundary of expected outputs (spec/code/audit/run)

## Legacy Protection (`RQ-078`)
- legacy docs are read-only
- promotions occur only via new versioned spec sets
- no in-place rewrites of historical canon sources

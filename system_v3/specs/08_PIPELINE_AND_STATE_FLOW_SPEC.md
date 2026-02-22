# Pipeline and State Flow Specification
Status: DRAFT / NONCANON
Date: 2026-02-20

## End-to-End Loop
1. A2 prepares/updates fuel and strategy context.
2. A1 (Rosetta+planner) generates `A1_STRATEGY_v1` with mappings, branches, alternatives, sim plans.
3. A0 canonicalizes strategy and compiles deterministic B artifacts.
4. B adjudicates artifacts (`ACCEPT/PARK/REJECT`).
5. A0 requests/loads `THREAD_S_SAVE_SNAPSHOT v2` and validates snapshot structure.
6. A0 dispatches deterministic SIM queue to SIM executor.
7. SIM runs pending evidence suites and returns `SIM_EVIDENCE`.
8. B ingests `SIM_EVIDENCE`.
9. A1/A2 consume feedback for next cycle.

Build-phase companion:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/21_IMPLEMENTATION_BUILD_SEQUENCE_AND_ACCEPTANCE_MATRIX.md`

## State Objects
- canonical state (B-owned)
- parked set
- graveyard
- term registry
- pending evidence map
- sim manifest store
- strategy hash index

## Event Classes
- `A2_CONTEXT_UPDATE`
- `A1_STRATEGY_EMIT`
- `A0_COMPILE_EMIT`
- `B_ACCEPT`
- `B_PARK`
- `B_REJECT`
- `SIM_PASS`
- `SIM_FAIL`
- `B_EVIDENCE_INGEST`

## Determinism Rules
- deterministic serialization and hashing at each boundary
- append-only logs
- stable replay from saved artifacts

## Stall Surfaces
- repeated same-tag rejection domination
- pending-evidence accumulation without closure
- park-set growth without dependency resolution
- branch diversity collapse

## Progress Surfaces
- growth of evidence-backed meaningful survivors
- closure of stress-family coverage
- tier promotion progress
- structured graveyard expansion tied to real targets

## Run Surface (Filesystem Contract; Lean + Deterministic)
All generated artifacts for a run must live under:
- `system_v3/runs/<run_id>/`

Suggested `<run_id>` pattern (operational; noncanon):
- `RUN__YYYYMMDD_HHMMSSZ__<strategy_hash12>__<baseline_state_hash12>`

Fixed subpaths (create only if needed):
- `outbox/`:
  - compiled `EXPORT_BLOCK vN` artifacts, one file per batch
- `b_reports/`:
  - Thread B report outputs for each submitted batch (verbatim text containers)
- `snapshots/`:
  - `THREAD_S_SAVE_SNAPSHOT v2` outputs (verbatim)
- `sim/`:
  - sim requests, manifests, outputs
  - sim evidence packs (verbatim `SIM_EVIDENCE v1` blocks)
- `tapes/`:
  - `EXPORT_TAPE v1` and `CAMPAIGN_TAPE v1` (JSONL, sharded)
- `logs/`:
  - append-only deterministic JSONL event logs + derived metrics (sharded)

Sharding:
- follow `RQ-092` file/line limits and deterministic shard suffixing.

No-sprawl rule:
- no new top-level directories
- no writing into `core_docs/`, `system_spec_pack_v2/`, or legacy `work/` during v3 runs

# Implementation Build Sequence and Acceptance Matrix
Status: DRAFT / NONCANON
Date: 2026-02-20
Owner: `RQ-125..RQ-132`

## Scope
This document defines the ordered implementation sequence from specs to a running A1/A0/B/SIM loop.

Run-surface scaffolding companion:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/22_RUN_SURFACE_TEMPLATE_AND_SCAFFOLDER_CONTRACT.md`

## Normative Clauses
- `RQ-125` MUST: implementation follows fixed phases `P0..P7` in order; skipping a phase is forbidden.
- `RQ-126` MUST: exit from `P2_B_CONFORMANCE` requires full green status on bootpack conformance fixtures.
- `RQ-127` MUST: exit from `P4_A1_TO_B_SMOKE` requires deterministic 50-cycle replay with identical per-cycle state hashes across two runs.
- `RQ-128` MUST: exit from `P5_SIM_EVIDENCE_LOOP` requires evidence-ingest pass for positive, negative, and kill-signal paths.
- `RQ-129` MUST: survivor significance gate checks linked trio (`positive_sim_ids[]`, `negative_sim_ids[]`, `graveyard_alt_ids[]`) before promotion eligibility.
- `RQ-130` MUST: long-run execution writes only inside run-scoped surfaces and enforces deterministic sharding caps.
- `RQ-131` MUST: release candidate gate requires two complete end-to-end replay passes with identical final state and event-log hashes.
- `RQ-132` MUST: release candidate includes `RELEASE_CHECKLIST_v1.json` with all mandatory gate artifact references.
- `RQ-132A` MUST: when loop-health enforcement is enabled, release candidate gate requires `LOOP_HEALTH_DIAGNOSTIC_v1` status `PASS` (or `WARN` only if explicitly waived).

## Phase Matrix
`P0_SPEC_LOCK`
- Inputs:
  - owner docs and ledger finalized
- Exit criteria:
  - `spec_lint.py` zero owner/orphan collisions
  - `reports/spec_lock_report.json` status `PASS`

`P1_ARTIFACT_GRAMMAR`
- Inputs:
  - bootpack extract (`spec 17`)
- Exit criteria:
  - parsers/emitters accept valid containers and reject malformed fixtures
  - `reports/artifact_grammar_report.json` status `PASS`

`P2_B_CONFORMANCE`
- Inputs:
  - B kernel implementation
  - fixture suite
- Exit criteria:
  - fixture pass for grammar, lexeme, undefined-term, derived-only, probe pressure, evidence checks

`P3_A0_COMPILER`
- Inputs:
  - compile-ready `A1_STRATEGY_v1` objects
- Exit criteria:
  - deterministic `EXPORT_BLOCK` generation for identical strategy input
  - dependency report + preflight report emitted
  - `reports/a0_compile_report.json` status `PASS`

`P4_A1_TO_B_SMOKE`
- Inputs:
  - A1 packet generation + A0 compile + B adjudication
- Exit criteria:
  - 50-cycle deterministic smoke replay (`RQ-127`)
  - no uncontrolled prose in kernel lane

`P5_SIM_EVIDENCE_LOOP`
- Inputs:
  - SIM runner + evidence pack emit
- Exit criteria:
  - evidence token updates verified
  - negative sim and kill pathways verified (`RQ-128`)

`P6_LONG_RUN_DISCIPLINE`
- Inputs:
  - full loop run harness
- Exit criteria:
  - bounded writes under run-scoped directories only
  - sharding limits enforced (`RQ-130`)
  - `reports/long_run_write_guard_report.json` status `PASS`

`P7_RELEASE_CANDIDATE`
- Inputs:
  - full conformance outputs + replay outputs
- Exit criteria:
  - dual replay hash equality (`RQ-131`)
  - checklist artifact complete (`RQ-132`)

## Mandatory Gate Artifacts
Per run candidate, required files:
- `reports/spec_lock_report.json`
- `reports/artifact_grammar_report.json`
- `reports/conformance_report.json`
- `reports/a0_compile_report.json`
- `reports/phase_transition_report.json`
- `reports/replay_pass_1.json`
- `reports/replay_pass_2.json`
- `reports/replay_pair_report.json`
- `reports/evidence_ingest_report.json`
- `reports/graveyard_integrity_report.json`
- `reports/long_run_write_guard_report.json`
- `reports/loop_health_diagnostic.json`
- `reports/release_checklist_v1.json`

## Survivor Significance Gate (P5+)
For each candidate promoted as meaningful survivor:
- must have `positive_sim_ids[]` length `>= 1`
- must have `negative_sim_ids[]` length `>= 1`
- must have `graveyard_alt_ids[]` length `>= 1`
- all referenced IDs must resolve in current run artifacts

Failure on any item blocks promotion.

## Run Surface Guard
Allowed write root:
- `system_v3/runs/<run_id>/`

Forbidden write targets during runs:
- `core_docs/`
- `system_spec_pack_v2/`
- `work/`
- top-level new root directories

## Release Checklist Schema
`RELEASE_CHECKLIST_v1.json` required fields:
- `schema`
- `candidate_id`
- `final_state_hash`
- `final_event_log_hash`
- `phase_status{P0..P7}`
- `artifact_refs[]`
- `waivers[]`
- `approved_utc`

Checklist without artifact references is invalid.

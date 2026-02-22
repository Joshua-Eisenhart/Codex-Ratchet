# Controlled Tuning and Upgrade Contract
Status: DRAFT / NONCANON
Date: 2026-02-20
Owner: `RQ-117..RQ-124`

## Scope
This document defines controlled tuning of existing A0/B/SIM implementations without uncontrolled redesign.

## Normative Clauses
- `RQ-117` MUST: every tuning run starts from a declared `TUNING_PROPOSAL` artifact and writes all outputs under a new run-scoped directory.
- `RQ-118` MUST: each proposal declares objective metric, stop condition, rollback target, and maximum mutation budget before execution.
- `RQ-119` MUST: tuning logs store deterministic baseline/candidate hashes and a machine-readable delta summary.
- `RQ-120` MUST: any tuning that changes admission outcomes executes fixed conformance replays against frozen fixture suites.
- `RQ-121` MUST: each proposal is labeled `SAFE_PARAM`, `RULE_INTERPRETATION`, or `SEMANTIC_CHANGE` and handled by class-specific gates.
- `RQ-122` MUST: only `SAFE_PARAM` proposals may auto-apply after passing replay checks; other classes require explicit review approval.
- `RQ-123` MUST: failed tuning branches are preserved in tuning graveyard records with failure evidence and deterministic revert steps.
- `RQ-124` MUST: promotion candidate must produce identical final state hash and identical event-log hash across two full deterministic replays.

## TUNING_PROPOSAL v1 Schema
Required keys:
- `schema`: `TUNING_PROPOSAL_v1`
- `proposal_id`
- `classification`: `SAFE_PARAM|RULE_INTERPRETATION|SEMANTIC_CHANGE`
- `target_components[]`: subset of `A0|B|SIM`
- `baseline_refs`: object
- `change_set`: object
- `objective_metrics[]`
- `stop_conditions[]`
- `mutation_budget`
- `rollback_target`

`baseline_refs` required keys:
- `baseline_state_hash`
- `baseline_event_log_hash`
- `baseline_spec_hash`

`change_set` required keys:
- `changed_files[]`
- `changed_knobs[]`
- `expected_effects[]`

## Allowed Knob Classes
`SAFE_PARAM` example knobs:
- A0 truncation limits
- A1 branch operator quotas (if represented as data)
- SIM timeout and batch sizes
- logging shard thresholds

`RULE_INTERPRETATION` knobs:
- parser interpretation disambiguation
- fence exception handling clarification

`SEMANTIC_CHANGE` knobs:
- new rule introduction
- changed stage ordering
- changed fence semantics

## Tuning Run Filesystem Contract
Run root:
- `system_v3/runs/<run_id>/`

Required files:
- `tuning/proposal.json`
- `tuning/baseline_snapshot.json`
- `tuning/candidate_snapshot.json`
- `tuning/delta_report.json`
- `tuning/replay_report_1.json`
- `tuning/replay_report_2.json`
- `tuning/promotion_decision.json`
- `logs/events.000.jsonl` (shardable)

## Deterministic Replay Contract
Replay inputs must be identical:
- same baseline state snapshot
- same ordered artifact inputs
- same fixed fixture suites
- same runtime knobs

Replay outputs compared:
- final canonical state hash
- full event log hash
- admission/park/reject counts
- graveyard delta hash

Mismatch handling:
- mark candidate `NONDETERMINISTIC`
- write graveyard record
- block promotion

## Conformance Replay Gate
Conformance fixture set categories:
- grammar validation fixtures
- lexeme/undefined-term/derived-only fence fixtures
- probe pressure fixtures
- evidence ingestion fixtures

Pass condition:
- expected statuses and tags match exactly for all fixtures.

## Tuning Graveyard Record
Each failed proposal appends one JSON record:
- `proposal_id`
- `classification`
- `failure_phase`
- `failure_evidence_refs[]`
- `state_hash_before`
- `state_hash_after`
- `revert_recipe`
- `ts_utc`

This graveyard is append-only.

## Promotion Gate
Promotion is allowed only if:
1. class gate passes (`SAFE_PARAM` auto or explicit approval for others),
2. conformance replay passes,
3. two deterministic replays match exactly (`RQ-124`),
4. rollback target is verified reachable.

Otherwise promotion is blocked.

## Non-Goals
- no in-place rewrite of `core_docs/`
- no silent rule changes
- no “helpful” undocumented fallback logic
- no deletion of failed tuning evidence


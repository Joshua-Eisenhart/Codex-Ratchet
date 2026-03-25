# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_systemv3_active_root_spec_control_spine__v1`
Extraction mode: `ACTIVE_CONTROL_SPINE_PASS`
Date: 2026-03-09

## T1) `ACTIVE_GUIDANCE_VS_DRAFT_STATUS_LABELS`
- tension:
  - many of the files doing real active control work still self-label as `DRAFT / NONCANON`
  - root docs such as `00_CANONICAL_ENTRYPOINTS_v1.md` and `01_OPERATIONS_RUNBOOK_v1.md` self-label as `ACTIVE`
- preserve:
  - status labels are source-local metadata
  - operational importance comes from actual repo role and cross-reference density, not the label alone
- main sources:
  - `00_CANONICAL_ENTRYPOINTS_v1.md`
  - `01_OPERATIONS_RUNBOOK_v1.md`
  - `specs/00_MANIFEST.md`
  - `specs/03..19`

## T2) `OWNER_SINGLE_SOURCE_VS_HELPER_EXTRACT_SPREAD`
- tension:
  - `specs/02_OWNERSHIP_MAP.md` insists each `RQ-*` has one normative owner
  - the batch also contains multiple helper or projection surfaces that restate or compact behavior:
    - `specs/10_INITIAL_AUDIT_REPORT.md`
    - `specs/14_A_THREAD_BOOTPACK_PROJECTION.md`
    - `specs/15_ROSETTA_AND_MINING_ARTIFACTS.md`
    - `specs/17_BOOTPACK...EXTRACT...md`
- preserve:
  - helper surfaces are useful for implementation and operator clarity
  - they remain non-owner and must not outrank owner docs or bootpack authority
- main sources:
  - `specs/02_OWNERSHIP_MAP.md`
  - `specs/10_INITIAL_AUDIT_REPORT.md`
  - `specs/14_A_THREAD_BOOTPACK_PROJECTION.md`
  - `specs/15_ROSETTA_AND_MINING_ARTIFACTS.md`
  - `specs/17_BOOTPACK_THREAD_B_v3.9.13_ENFORCEABLE_CONTRACT_EXTRACT_FOR_IMPLEMENTATION_v1.md`

## T3) `A1_MACRO_SCHEDULER_VS_A1_MICRO_QUOTA_TABLE`
- tension:
  - `specs/05_A1_STRATEGY_AND_REPAIR_SPEC.md` defines a coarse branch scheduler quota set
  - `specs/18_A1_WIGGLE_EXECUTION_CONTRACT.md` defines a finer operator quota table with different buckets and values
- preserve:
  - these can be read as macro-vs-micro layers
  - that layering is not explicitly normalized inside the source set yet
- consequence risk:
  - later A1-state or runtime audits could silently choose one quota table and forget the other
- main sources:
  - `specs/05_A1_STRATEGY_AND_REPAIR_SPEC.md`
  - `specs/18_A1_WIGGLE_EXECUTION_CONTRACT.md`

## T4) `A2_BROAD_CONTROL_SURFACE_SET_VS_A2_CANONICAL_FILE_INTERFACE`
- tension:
  - `specs/07_A2_OPERATIONS_SPEC.md` names a broad active A2 control/brain surface set
  - `specs/19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md` presents a narrower canonical file interface centered on schemas, compaction artifacts, and seal mechanics
- preserve:
  - `07` reads like the active control loop and required human-facing surface family
  - `19` reads like the canonical schema/write contract
  - the boundary between those two roles is useful but not fully collapsed into one crisp statement here
- main sources:
  - `specs/07_A2_OPERATIONS_SPEC.md`
  - `specs/19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md`

## T5) `ZIP_PROTOCOL_MINIMALISM_VS_ZIP_JOB_OPERATIONAL_OVERLAY`
- tension:
  - `specs/ZIP_PROTOCOL_v2.md` insists transport is structure-only and must not absorb policy or routing logic
  - `specs/16_ZIP_SAVE_AND_TAPES_SPEC.md` describes `ZIP_JOB` as a deterministic subagent/carrier with internal manifest and operational packaging language
- preserve:
  - strict packet validation and broader packaging doctrine coexist in the source set
  - they are related but not identical authority surfaces
- main sources:
  - `specs/16_ZIP_SAVE_AND_TAPES_SPEC.md`
  - `specs/ZIP_PROTOCOL_v2.md`

## T6) `RUN_SURFACE_THICKNESS_VS_LEAN_LINEAGE_PRESSURE`
- tension:
  - root docs and `specs/08_PIPELINE_AND_STATE_FLOW_SPEC.md` still describe a relatively broad run surface with `snapshots/`, `sim/`, `outbox/`, and shared current-state surfaces
  - `specs/16_ZIP_SAVE_AND_TAPES_SPEC.md` pushes lean resume-state surfaces, witness retention, and packet-journal compaction
- preserve:
  - this batch captures an in-between state rather than one final resolved save doctrine
- main sources:
  - `00_CANONICAL_ENTRYPOINTS_v1.md`
  - `01_OPERATIONS_RUNBOOK_v1.md`
  - `specs/08_PIPELINE_AND_STATE_FLOW_SPEC.md`
  - `specs/16_ZIP_SAVE_AND_TAPES_SPEC.md`

## T7) `WORKSPACE_WRITE_POLICY_VS_NEW_INTAKE_SURFACE_REALITY`
- tension:
  - `WORKSPACE_LAYOUT_v1.md` lists default write targets but does not include `a2_high_entropy_intake_surface/`
  - the current intake process explicitly uses that surface as the bounded output location for fresh high-entropy workers
- preserve:
  - workspace layout guidance is useful historical operator law
  - it is visibly stale relative to the newer intake workflow
- main sources:
  - `WORKSPACE_LAYOUT_v1.md`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/A2_HIGH_ENTROPY_INTAKE_PROCESS__v1.md`

## T8) `LIGHT_RUNBOOK_STARTUP_VS_HEAVIER_PROMOTION_GATE_STACK`
- tension:
  - `01_OPERATIONS_RUNBOOK_v1.md` foregrounds sprawl/archive guards and basic run steps
  - `specs/09_CONFORMANCE_AND_REDUNDANCY_GATES.md`, `specs/10_INITIAL_AUDIT_REPORT.md`, and `specs/12_BOOTPACK_SYNC_AUDIT_SPEC.md` define a denser gate stack for promotion and drift control
- preserve:
  - startup/run instructions are not the same thing as promotion criteria
  - the source set does not fully centralize that distinction
- main sources:
  - `01_OPERATIONS_RUNBOOK_v1.md`
  - `specs/09_CONFORMANCE_AND_REDUNDANCY_GATES.md`
  - `specs/10_INITIAL_AUDIT_REPORT.md`
  - `specs/12_BOOTPACK_SYNC_AUDIT_SPEC.md`

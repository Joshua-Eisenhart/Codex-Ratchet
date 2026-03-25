# SIM_CAMPAIGN_AND_SUITE_MODES__v1
Status: DRAFT / NONCANON / REPAIR TARGET
Date: 2026-03-14
Owner: `A0` / `SIM` runtime repair

## Purpose

This spec restores the missing operator-facing SIM process discipline without changing the current `A2 -> A1 -> A0 -> B -> SIM` architecture.

It exists because the current system preserves:
- `SIM_EVIDENCE v1`
- tier labels
- promotion gates
- graveyard linkage

but weaker operator/process structure for:
- staged suite progression
- failure isolation
- replay from tapes/save surfaces
- whole-system mega-gate discipline

This spec is the process-layer companion to:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/06_SIM_EVIDENCE_AND_TIERS_SPEC.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/08_PIPELINE_AND_STATE_FLOW_SPEC.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/04_A0_COMPILER_SPEC.md`

Legacy witness surfaces:
- `/home/ratchet/Desktop/Codex Ratchet/core_docs/BOOTPACKS/BOOTPACK_THREAD_SIM_v2.10.md`
- `/home/ratchet/Desktop/mega legacy/RATCHET_BUNDLE_v2.0.12 2/SIM_RUNBOOK_v1.4.md`
- `/home/ratchet/Desktop/mega legacy/RATCHET_BUNDLE_v2.0.12 2/SIM_CATALOG_v1.3.md`
- `/home/ratchet/Desktop/mega legacy/RATCHET_BUNDLE_v2.0.12 2/SIM_EVIDENCE_PACK_autogen_v2.txt`

Normative anchors:
- `RQ-050`
- `RQ-051`
- `RQ-052`
- `RQ-053`
- `RQ-054`
- `RQ-055`
- `RQ-056`
- `RQ-057`
- `RQ-058`
- `RQ-059`
- `RQ-064`
- `RQ-096`

## Core rule

The SIM system is not a flat queue of pending checks.

The SIM system is a staged campaign:
- simple term/atom checks first
- then compound/operator/structure checks
- then system-segment and engine checks
- then whole-system mega checks

No higher-stage campaign may be treated as meaningful if lower-stage closure is still materially open.

## Required campaign stages

Every staged SIM campaign must declare these stage classes explicitly:

1. `TERM_SEED`
- maps to `T0_ATOM`

2. `COMPOUND`
- maps to `T1_COMPOUND`

3. `OPERATOR`
- maps to `T2_OPERATOR`

4. `STRUCTURE`
- maps to `T3_STRUCTURE`

5. `SEGMENT`
- maps to `T4_SYSTEM_SEGMENT`

6. `ENGINE`
- maps to `T5_ENGINE`

7. `MEGA`
- maps to `T6_WHOLE_SYSTEM`

Allowed omission:
- a campaign may stop before higher stages if its scope is intentionally local
- a campaign may not silently skip directly to `ENGINE` or `MEGA`

## Required suite modes

Every staged SIM system must support these suite modes:

1. `micro_suite`
- used for `TERM_SEED` and `COMPOUND`
- goal: primitive and local compositional closure

2. `mid_suite`
- used for `OPERATOR` and `STRUCTURE`
- goal: transformation and structural stability checks

3. `segment_suite`
- used for `SEGMENT`
- goal: bounded subsystem pressure

4. `engine_suite`
- used for `ENGINE`
- goal: cross-segment engine closure

5. `mega_suite`
- used for `MEGA`
- goal: whole-system closure only after lower-stage closure

6. `failure_isolation`
- used when a prior suite fails or produces mixed evidence
- goal: bisect the failing family, dependency, or probe seam

7. `graveyard_rescue`
- used when graveyard targets need direct rescue pressure
- goal: attempt salvage or sharper invalidation against graveyarded candidates

8. `replay_from_tape`
- used to replay a saved campaign or save-derived witness
- goal: deterministically reproduce prior campaign structure and evidence surfaces

## Stage law

1. `NO_IMPLICIT_STAGE_INVENTION`
- stages must be explicitly declared by strategy or repaired strategy
- bridge/compiler may normalize formatting
- bridge/compiler may not invent a missing campaign ladder for `A1_STRATEGY_v2`

2. `EXPLICIT_DEPENDENCY_DAG`
- every non-root stage must declare `depends_on`
- dependencies must be acyclic
- dependency stages must be lower-tier

3. `NO_MEGA_WITHOUT_LOWER_CLOSURE`
- `mega_suite` is illegal unless lower stages are sufficiently closed

4. `NO_ENGINE_SHORTCUT`
- `engine_suite` may not become the practical first serious suite just because lower-stage sims are absent or thin

5. `FAILURE_ISOLATION_REQUIRED_AFTER_MEANINGFUL_FAIL`
- if a suite produces a real blocking fail, the next legal path is:
  - `failure_isolation`
  - or explicit stop with unresolved blocker report

6. `GRAVEYARD_RESCUE_IS_ACTIVE_WORK`
- graveyard rescue is part of the campaign plan, not passive bookkeeping

## Required campaign fields

Every staged SIM campaign must bind:
- `program_id`
- `stage_id`
- `tier`
- `suite_kind`
- `families`
- `target_classes`
- `depends_on`
- `max_sims`
- `failure_policy`

Every SIM plan row must bind:
- `sim_id`
- `binds_to`
- `stage_id`

Every compiled `SIM_SPEC` must preserve:
- `TIER`
- `FAMILY`
- `TARGET_CLASS`
- `PROBE_TERM`
- `STAGE_ID`
- `STAGE_DEPENDS_ON` (repeatable if needed)

## Required execution order

Within a campaign, execution order must be determined by:

1. dependency closure
2. stage tier
3. suite kind
4. deterministic lexical identity

Within a stage:
- run baseline coverage first
- then boundary/perturbation/adversarial/composition pressure
- if failure occurs and policy requires isolation, dispatch `failure_isolation` before resuming forward expansion

## Replay law

`replay_from_tape` is valid only if it binds to one of:
- `CAMPAIGN_TAPE`
- `EXPORT_TAPE` plus matching B reports
- semantic `FULL+` or `FULL++` save-derived witness
- deterministic packet lineage sufficient to reconstruct the campaign

Replay must preserve:
- stage order
- suite kind
- sim ids
- hashes
- evidence token expectations

Replay is for:
- proof
- regression
- recovery

Replay is not license to bypass lower-stage closure.

## Required reports

Every staged SIM campaign run must emit enough information to reconstruct:
- stage order
- suite kinds executed
- blocked stages
- failure isolation branches
- graveyard rescue branches
- replay source when used

Minimum run report fields:
- `campaign_program_id`
- `stages_seen[]`
- `suite_modes_seen[]`
- `blocked_stage_ids[]`
- `failure_isolation_count`
- `graveyard_rescue_count`
- `replay_source`
- `master_sim_status`
- `promotion_blockers[]`

## Acceptance criteria

This spec is satisfied only when:
- the dispatcher is stage-aware, not only tier-sorted
- the runner can execute explicit suite modes
- `ENGINE` and `MEGA` runs are impossible without lower-stage closure
- failure isolation is a first-class path
- replay from saved lineage is explicit and deterministic

## Current patch targets

Primary runtime files:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/sim_dispatcher.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/a1_a0_b_sim_runner.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_evidence_ingest_gate.py`

Primary schema/compile files:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/a1_strategy.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/a1_bridge.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/a0_compiler.py`

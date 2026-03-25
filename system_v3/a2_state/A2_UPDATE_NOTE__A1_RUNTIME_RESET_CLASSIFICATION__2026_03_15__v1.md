# A2_UPDATE_NOTE__A1_RUNTIME_RESET_CLASSIFICATION__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 CONTROL NOTE
Date: 2026-03-15
Role: classify recent A1/runtime/control surfaces into rewrite-first, demote/review, and likely-keep buckets after the 2026-03-15 reset audit

## Scope

This note does not perform any code mutation.

It classifies the recently audited A1/runtime/control surfaces so future reset work starts from the highest-risk seams first instead of treating the entire recent set as one undifferentiated block.

## Source basis

- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__A1_RUNTIME_RESET_AND_SPEC_OBJECT_DIRECTION__2026_03_15__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_IMPACT_NOTE__A1_RUNTIME_RESET_AND_SPEC_OBJECT_DIRECTION__2026_03_15__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/autoratchet.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_real_loop.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_a1_wiggle_control_cycle.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_a1_autoratchet_controller_result.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_a1_autoratchet_cycle_audit.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/a1_request_to_codex_prompt.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/a1_llm_lane_driver.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/a1_sandbox_only_runner.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_a1_consolidation_prepack_job.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/a1_pack_selector.py`

Doctrine/control anchors:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/30_A2_TO_A1_HANDOFF_CONTRACT__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/31_A1_THREAD_BOOT__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_TARGET_FAMILY_MODEL__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_EXECUTABLE_DISTILLATION_UPDATE__SOURCE_BOUND_v2.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/specs/A1_CONSOLIDATION_PREPACK_JOB__v1.md`

## REWRITE_FIRST

### `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_real_loop.py`

Reason:
- manufactures PASS-looking compile/dependency/preflight reports from reconstructed export blocks at `#L223`
- generates synthetic event shards from ZIP headers at `#L273`
- fabricates SIM evidence packs from manifests/graveyard state at `#L408`
- materializes fallback tapes at `#L489`
- then validates the run through the gate pipeline at `#L785`
- also hardwires the campaign shape through `refined_fuel`, `interleaved`, `graveyard_first_then_recovery`, and a minimum `96` planner steps at `#L687`

Classification:
- rewrite first

### `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`

Reason:
- still encodes the active A1 path as fixed goal families/ladders:
  - `CORE_GOALS` at `#L93`
  - `PHYSICS_FUEL_GOALS` at `#L266`
  - `AXIS_FOUNDATION_GOALS` at `#L318`
  - `MASTER_CONJUNCTION_GOALS` at `#L374`
  - `REFINED_FUEL_GOALS` at `#L437`
- this remains the main doctrinal mismatch with bounded A2-driven family/cartridge campaigns

Classification:
- rewrite first

### `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/autoratchet.py`

Reason:
- hardwires required probe terms by goal profile at `#L238`
- preserves the profile-driven scripted campaign shape as the main runtime entry

Classification:
- rewrite first

### `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_a1_wiggle_control_cycle.py`

Reason:
- claims guardrail knobs like `--stall-limit-cycles`, `--max-run-bytes`, `--project-save-every-cycles`, and `--max-cycles-without-progress` at `#L71`
- but does not forward them to `autoratchet` or the audit command at `#L101` and `#L133`
- also remains coupled to the scripted `autoratchet` path instead of a doctrine-aligned A1 control surface

Classification:
- rewrite first

### `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_a1_autoratchet_controller_result.py`

Reason:
- can stop a run purely because `a1_semantic_gate_status == PASS` at `#L68`
- does not check doctrinal family obligations, branch diversity, rescue/graveyard completeness, or bounded A2-handoff integrity

Classification:
- rewrite first

### `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_a1_autoratchet_cycle_audit.py`

Reason:
- audit only checks for summary presence, step counts, packet presence, visible branch pressure, and minimum graveyard count at `#L38`
- that is too thin to validate the real A1 doctrine

Classification:
- rewrite first

### `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/a1_request_to_codex_prompt.py`

Reason:
- explicitly treats broad refined fuel and multiple A2 surfaces as admissible A1 brain-upload material at `#L146`
- comment at `#L208` says all of `a1_refined_Ratchet Fuel` is admissible A1 upload fuel
- that conflicts with the tighter A2 -> A1 bounded-handoff direction

Classification:
- rewrite first

### `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/a1_llm_lane_driver.py`

Reason:
- institutionalizes a prompt/ZIP host-LLM lane around `a1_request_to_codex_prompt.py` at `#L16` and `#L54`
- so it inherits the broad-fuel-loading and prompt-wrapper drift instead of representing the real A1 runtime

Classification:
- rewrite first

### `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py`

Reason:
- protects the scripted ladder instead of the doctrine:
  - substrate ordering at `#L29` and `#L44`
  - entropy ladder expectations at `#L124`
- green tests here are weak evidence of doctrinal alignment

Classification:
- rewrite first alongside planner rewrite

## DEMOTE_OR_REVIEW

### `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/a1_sandbox_only_runner.py`

Reason:
- sandbox-only helper, not the main runtime
- but seeds wrong default focus/graveyard terms in the default brain at `#L151`

Classification:
- do not treat as an owner/runtime model
- demote in operator importance
- later cleanup/review

## LIKELY_KEEP_WITH_LATER_REVIEW

### `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_a1_consolidation_prepack_job.py`

Reason:
- acts as a strict consolidation wrapper around:
  - sink ingestion
  - cold-core strip
  - deterministic pack selection
- fails closed on unsupported schemas and mixed strategy/memo inputs at `#L399` and `#L412`
- routes memo consolidation through `a1_lawyer_sink.py`, `a1_cold_core_strip.py`, and `a1_pack_selector.py` at `#L453`, `#L458`, and `#L477`
- refuses selector-reported sequence mismatch at `#L587`
- validates direct strategy passthrough at `#L651`

Classification:
- likely keep
- later doctrine review still needed, but not a first reset target

### `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/a1_pack_selector.py`

Reason:
- already serves as a doctrine-to-runtime bridge rather than the whole runtime:
  - loads family admissibility hints at `#L287`
  - builds admissibility blocks at `#L607`
  - refines target terms against admissibility at `#L939`
  - emits `admissibility` and `family_terms` on the final strategy at `#L1494`
- this seam looks closer to the intended “many-worker richness -> one strict pre-A0 surface” direction

Classification:
- likely keep
- later re-audit for doctrine fit, but not the first reset seam

## HOLD

- selector/admissibility warning/provenance cleanup work remains more salvageable than the planner/runtime loop
- SIM/save/report helper work should be re-audited later, but it is not currently the highest reset priority

## Operational reading

If reset work starts soon, the correct order is:

1. stop trusting the loop harness and scripted planner path
2. rewrite the planner/runtime/controller audit trio
3. only after that, decide how much of the helper/control-plane shell survives unchanged

This note should not be read as permission to delete anything immediately.
It is a controller-side classification surface for sequencing the reset.

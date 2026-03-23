# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_systemv3_active_spec_stage2_public_conformance__v1`
Extraction mode: `ACTIVE_SPEC_STAGE2_AND_PUBLIC_BOUNDARY_PASS`
Date: 2026-03-09

## T1) `FIXTURE_TAG_EXPECTATION_VS_OWNER_TAG_FENCE`
- tension:
  - the conformance fixture pack expects `UNDEFINED_LEXEME` for `FIX_LEX_001_UNDEFINED_COMPONENT_PARK`
  - the earlier B owner spec tag fence enumerates `UNDEFINED_TERM_USE` but not `UNDEFINED_LEXEME`
- preserve:
  - this is an active contract-drift signature, not a wording nicety
- main sources:
  - `conformance/fixtures_v1/expected_outcomes.json`
  - `conformance/fixtures_v1/fixtures/FIX_LEX_001_UNDEFINED_COMPONENT_PARK.txt`
  - cross-batch anchor: `specs/03_B_KERNEL_SPEC.md`

## T2) `SYSTEM_V3_ONLY_WRITE_POSTURE_VS_WORK_PATH_STAGE3_BUNDLE`
- tension:
  - the active repo posture increasingly centers new v3 artifacts in `system_v3/`
  - `specs/29_STAGE_3_TEMPLATE_AND_SCHEMA_GATE_FLOW__v1.md` points its concrete bundle root into `work/zip_job_templates/...`
  - `specs/24_NAMING_AND_ARTIFACT_RULES__STAGE_0_FREEZE.md` also names `work/zip_dropins/` and `work/zip_job_templates/` as immediate adoption targets
- preserve:
  - late packaging docs still carry live `work/` spillover assumptions
  - they should not be silently normalized into a clean `system_v3`-only story
- main sources:
  - `specs/24_NAMING_AND_ARTIFACT_RULES__STAGE_0_FREEZE.md`
  - `specs/29_STAGE_3_TEMPLATE_AND_SCHEMA_GATE_FLOW__v1.md`
  - cross-batch anchor: `WORKSPACE_LAYOUT_v1.md`

## T3) `PREFERRED_TARGET_TERM_VS_LEGACY_CANONICAL_TERM_ALIAS`
- tension:
  - the Stage-2 A1 rosetta schema explicitly prefers `target_term`
  - the same schema still preserves legacy alias `canonical_term`
- preserve:
  - the alias is compatibility baggage, not earned-canon language
- main sources:
  - `specs/schemas/A1_BRAIN_ROSETTA_UPDATE_PACKET_STAGE2_v1.schema.json`

## T4) `PUBLIC_INTENT_AUTHORITY_SHORTCUT_VS_INTERNAL_A2_BOOT_DISCIPLINE`
- tension:
  - `00_PUBLIC_FACING_SYSTEM_INTENT...` points newcomers to `system_v3/a2_state/INTENT_SUMMARY.md` as the authoritative user-intent pointer
  - active internal A2 docs already state that `INTENT_SUMMARY.md` is not sufficient by itself as the standing A2 brain
- preserve:
  - public explanation needs a simple pointer
  - internal control law requires a thicker boot set
- main sources:
  - `public_facing_docs/00_PUBLIC_FACING_SYSTEM_INTENT_AND_CONSTRAINTS_ON_INTERPRETATION_v1.md`
  - cross-batch anchors:
    - `specs/07_A2_OPERATIONS_SPEC.md`
    - `a2_state/INTENT_SUMMARY.md`

## T5) `ACTIVE_CONTROLLER_PROCESS_VS_PROVISIONAL_CONTROLLER_PROCESS`
- tension:
  - `27_MASTER_CONTROLLER_THREAD_PROCESS__v1` is labeled `ACTIVE / NONCANONICAL`
  - the body repeatedly calls the controller architecture provisional and revisable
- preserve:
  - the controller process is live enough to use
  - it is not closed enough to flatten into fixed architecture
- main sources:
  - `specs/27_MASTER_CONTROLLER_THREAD_PROCESS__v1.md`

## T6) `STRICT_RUN_SURFACE_CONTRACT_VS_HELPER_HEAVINESS`
- tension:
  - `specs/22_RUN_SURFACE_TEMPLATE_AND_SCAFFOLDER_CONTRACT.md` pushes deterministic, fail-closed, pre-emitted run structure
  - the same doc also accumulates a broad helper/tool chain and a large minimum directory/report surface
- preserve:
  - strict structure and helper sprawl pressures coexist
  - this is a real packaging tension rather than a resolved “lean” state
- main sources:
  - `specs/22_RUN_SURFACE_TEMPLATE_AND_SCAFFOLDER_CONTRACT.md`
  - `specs/21_IMPLEMENTATION_BUILD_SEQUENCE_AND_ACCEPTANCE_MATRIX.md`

## T7) `PUBLIC_FLOWMIND_HOSTING_VS_KERNEL_SEALING`
- tension:
  - public-facing host docs invite higher-level orchestration/hosting
  - those same docs strongly forbid new kernel primitives, reinterpretation, or A0 bypass
  - `specs/30_CHATUI_CLAW_PLAYWRIGHT_PROTOCOL_v1.md` adds browser-mediated nondeterministic reasoning as an operational path above the boundary
- preserve:
  - orchestration expansion pressure is real
  - kernel sealing remains the dominant limit
- main sources:
  - `public_facing_docs/02_PUBLIC_FACING_FLOWMIND_A3_HOSTING_INTERFACE_CONTRACT_v1.md`
  - `public_facing_docs/01_PUBLIC_FACING_LAYERED_ARCHITECTURE_AND_ENTROPY_BOUNDARY_v1.md`
  - `specs/30_CHATUI_CLAW_PLAYWRIGHT_PROTOCOL_v1.md`

## T8) `DETACHED_NORMATIVE_HASH_BASELINE_VS_EXPANDING_SPEC_SET`
- tension:
  - `_normative_hash_baseline.json` is a tiny detached digest surface
  - this batch and the previous batch together show a much larger evolving owner/helper spec pack
- preserve:
  - the baseline digest is useful
  - this intake pass does not prove the digest is fresh or complete relative to the full active spec corpus
- main sources:
  - `specs/_normative_hash_baseline.json`
  - `specs/09_CONFORMANCE_AND_REDUNDANCY_GATES.md`

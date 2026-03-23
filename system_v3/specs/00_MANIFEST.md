# SYSTEM_V3 SPEC MANIFEST
Status: DRAFT / NONCANON
Date: 2026-02-20

## Purpose
Build a clean, non-redundant spec spine for A2/A1/A0/B/SIM.
This pack is a rewrite surface; legacy specs remain untouched.

## Rules
- Deterministic read order is mandatory.
- Each requirement has exactly one normative owner document.
- Non-owner documents may reference requirements but may not restate normative clauses.
- Contradictions are logged, never smoothed.

## Deterministic Read Order
1. `system_v3/specs/01_REQUIREMENTS_LEDGER.md`
2. `system_v3/specs/02_OWNERSHIP_MAP.md`
3. `system_v3/specs/03_B_KERNEL_SPEC.md`
4. `system_v3/specs/17_BOOTPACK_THREAD_B_v3.9.13_ENFORCEABLE_CONTRACT_EXTRACT_FOR_IMPLEMENTATION_v1.md`
5. `system_v3/specs/04_A0_COMPILER_SPEC.md`
6. `system_v3/specs/16_ZIP_SAVE_AND_TAPES_SPEC.md`
7. `system_v3/specs/05_A1_STRATEGY_AND_REPAIR_SPEC.md`
8. `system_v3/specs/18_A1_WIGGLE_EXECUTION_CONTRACT.md`
9. `system_v3/specs/06_SIM_EVIDENCE_AND_TIERS_SPEC.md`
10. `system_v3/specs/07_A2_OPERATIONS_SPEC.md`
11. `system_v3/specs/19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md`
12. `system_v3/specs/08_PIPELINE_AND_STATE_FLOW_SPEC.md`
13. `system_v3/specs/09_CONFORMANCE_AND_REDUNDANCY_GATES.md`
14. `system_v3/specs/20_CONTROLLED_TUNING_AND_UPGRADE_CONTRACT.md`
15. `system_v3/specs/21_IMPLEMENTATION_BUILD_SEQUENCE_AND_ACCEPTANCE_MATRIX.md`
16. `system_v3/specs/22_RUN_SURFACE_TEMPLATE_AND_SCAFFOLDER_CONTRACT.md`
17. `system_v3/specs/23_BOOTPACK_CONFORMANCE_FIXTURE_MATRIX_CONTRACT.md`
18. `system_v3/specs/10_INITIAL_AUDIT_REPORT.md`
19. `system_v3/specs/11_MIGRATION_HANDOFF_SPEC.md`
20. `system_v3/specs/12_BOOTPACK_SYNC_AUDIT_SPEC.md`
21. `system_v3/specs/13_CONTENT_REDUNDANCY_LINT_SPEC.md`
22. `system_v3/specs/14_A_THREAD_BOOTPACK_PROJECTION.md`
23. `system_v3/specs/15_ROSETTA_AND_MINING_ARTIFACTS.md`
24. `system_v3/specs/24_NAMING_AND_ARTIFACT_RULES__STAGE_0_FREEZE.md`
25. `system_v3/specs/25_BOOTPACK_A2_REFINERY__v1.md`
26. `system_v3/specs/26_BOOTPACK_A1_WIGGLE__v1.md`
27. `system_v3/specs/27_BOOTPACK_RATCHET_FUEL_MINT__v1.md`
28. `system_v3/specs/28_STAGE_2_JOB_SCHEMAS_AND_VALIDATION_STUBS__v1.md`
29. `system_v3/specs/29_STAGE_3_TEMPLATE_AND_SCHEMA_GATE_FLOW__v1.md`

Repo-state note:
- In some workspaces, items `24` through `29` exist as active local extension surfaces but are not yet part of tracked repo history.
- When they are present but untracked, treat `00` through `23` as the tracked baseline and record the extension-pack dependency explicitly in any audit or fresh-thread bootstrap.

## A1 Reload Hygiene
- `system_v3/specs/05_A1_STRATEGY_AND_REPAIR_SPEC.md` and `system_v3/specs/18_A1_WIGGLE_EXECUTION_CONTRACT.md` remain in the read spine because they own requirement ranges.
- But sections explicitly labeled `Legacy` inside those files are historical draft doctrine, not the live runtime/control operator law.
- For a compact current A1 packet/profile read, use:
  - `system_v3/specs/77_A1_LIVE_PACKET_PROFILE_EXTRACT__v1.md`
- For a compact historical A1 branch/wiggle read, use:
  - `system_v3/specs/78_A1_HISTORICAL_BRANCH_WIGGLE_EXTRACT__v1.md`
- For the live operator enum/mapping used by the current A1 runtime/control path, use:
  - `system_v3/control_plane_bundle_work/system_v3_control_plane/specs/ENUM_REGISTRY_v1.md`
  - `system_v3/control_plane_bundle_work/system_v3_control_plane/specs/A1_REPAIR_OPERATOR_MAPPING_v1.md`
  - `system_v3/control_plane_bundle_work/system_v3_control_plane/specs/A1_STRATEGY_v1.md`

## Active Process Supplements
Read these after the core spine when the task touches the corresponding active path:
- `system_v3/specs/ZIP_PROTOCOL_v2.md`
- `system_v3/specs/27_MASTER_CONTROLLER_THREAD_PROCESS__v1.md`
- `system_v3/specs/28_A2_THREAD_BOOT__v1.md`
- `system_v3/specs/30_A2_TO_A1_HANDOFF_CONTRACT__v1.md`
- `system_v3/specs/31_A1_THREAD_BOOT__v1.md`
- `system_v3/specs/32_A1_QUEUE_STATUS_SURFACE__v1.md`
- `system_v3/specs/34_A1_READY_PACKET__v1.md`
- `system_v3/specs/40_PARALLEL_CODEX_THREAD_CONTROL__v1.md`
- `system_v3/specs/66_PARALLEL_CODEX_RUN_PLAYBOOK__v1.md`
- `system_v3/specs/71_A2_CONTROLLER_LAUNCH_PACKET__v1.md`
- `system_v3/specs/72_SIM_CAMPAIGN_AND_SUITE_MODES__v1.md`
- `system_v3/specs/73_FULL_PLUS_SEMANTIC_SAVE_ZIP__v1.md`
- `system_v3/specs/74_A0_SAVE_REPORT_SURFACES__v1.md`
- `system_v3/specs/75_A2_MINING_AND_ROSETTA_ARTIFACT_PACKS__v1.md`
- `system_v3/specs/76_SYSTEM_BUNDLE_AND_REBOOT_PLAYBOOK__v1.md`
- `system_v3/specs/77_A1_LIVE_PACKET_PROFILE_EXTRACT__v1.md`
- `system_v3/specs/78_A1_HISTORICAL_BRANCH_WIGGLE_EXTRACT__v1.md`
- `system_v3/specs/79_INTEGRATION_LEDGER__v1.md`
- `system_v3/specs/30_CHATUI_CLAW_PLAYWRIGHT_PROTOCOL_v1.md`
- `system_v3/a2_high_entropy_intake_surface/A2_HIGH_ENTROPY_INTAKE_PROCESS__v1.md`
- `system_v3/a2_high_entropy_intake_surface/A2_MID_REFINEMENT_PROCESS__v1.md`

Supplement note:
- `27_MASTER_CONTROLLER_THREAD_PROCESS__v1.md` and `30_CHATUI_CLAW_PLAYWRIGHT_PROTOCOL_v1.md` may also appear as workspace-local overlays before they are tracked.
- If absent from tracked history, keep the audit anchored to the tracked spine plus live runtime/tools and call out the missing overlay explicitly rather than assuming canonical availability.

## Scope
- In scope: system architecture, contracts, gates, ownership, audit.
- Out of scope: modifying canon state, modifying core docs, running ratchet loops.

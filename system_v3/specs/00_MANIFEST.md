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

## Scope
- In scope: system architecture, contracts, gates, ownership, audit.
- Out of scope: modifying canon state, modifying core docs, running ratchet loops.

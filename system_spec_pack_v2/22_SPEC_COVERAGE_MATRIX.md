# Spec Coverage Matrix (v1)
Status: DRAFT / NONCANON
Date: 2026-02-20

Goal: map requirement IDs (`21_SYSTEM_REQUIREMENTS_LEDGER.md`) to current spec-pack coverage and explicit gaps.

Status legend:
- `FULL`: requirement is explicitly specified in current pack.
- `PARTIAL`: requirement is present but missing operational detail.
- `GAP`: requirement not yet fully specified in this pack.

| Requirement | Covered In | Status | Gap Notes |
| --- | --- | --- | --- |
| RQ-001 RQ-002 | `01_OVERVIEW.md`, `04_CANON_STATE_SCHEMA.md`, `14_DO_NOT_DO_AND_FORBIDDEN_MOVES.md` | FULL |  |
| RQ-003 RQ-004 | `02_THREADS_AND_BOOT.md`, `10_TRANSLATOR_BOUNDARY_AND_POLICY.md` | FULL |  |
| RQ-010 | `08_MODEL_SWITCH_PROTOCOL.md`, `09_A1_STRATEGY_DECLARATION.md`, `17_A1_REPAIR_LOOP_AND_WIGGLE_PROTOCOL.md` | PARTIAL | runtime LLM planner contract is specified but not yet acceptance-tested in this pack |
| RQ-011 RQ-012 RQ-013 | `02_THREADS_AND_BOOT.md`, `03_B_ARTIFACTS_AND_FENCES.md`, `11_PROVENANCE_CHAIN_AND_REPLAY.md` | FULL |  |
| RQ-014 RQ-015 | `10_TRANSLATOR_BOUNDARY_AND_POLICY.md`, `13_A2_YAML_USAGE_AND_COMPACTION.md`, `16_A2_PERSISTENT_BRAIN_SCHEMA.md` | FULL |  |
| RQ-020 RQ-021 RQ-022 | `09_A1_STRATEGY_DECLARATION.md`, `17_A1_REPAIR_LOOP_AND_WIGGLE_PROTOCOL.md`, `15_AUDIT_GATES_AND_SUCCESS_CRITERIA.md` | PARTIAL | large-scale branch budgeting rules not fully parameterized |
| RQ-023 | `03_B_ARTIFACTS_AND_FENCES.md`, `10_TRANSLATOR_BOUNDARY_AND_POLICY.md`, `14_DO_NOT_DO_AND_FORBIDDEN_MOVES.md` | FULL |  |
| RQ-030 RQ-031 | `12_TERM_COMPOSITION_AND_RATCHET_COMPLETENESS.md` | FULL |  |
| RQ-032 RQ-033 | `03_B_ARTIFACTS_AND_FENCES.md`, `14_DO_NOT_DO_AND_FORBIDDEN_MOVES.md` | FULL |  |
| RQ-034 | `10_TRANSLATOR_BOUNDARY_AND_POLICY.md`, `14_DO_NOT_DO_AND_FORBIDDEN_MOVES.md`, `16_A2_PERSISTENT_BRAIN_SCHEMA.md` | FULL |  |
| RQ-040 RQ-041 RQ-042 RQ-043 | `05_EVIDENCE_SIMS_NEGATIVE.md`, `12_TERM_COMPOSITION_AND_RATCHET_COMPLETENESS.md`, `15_AUDIT_GATES_AND_SUCCESS_CRITERIA.md` | FULL |  |
| RQ-044 RQ-045 | `03_B_ARTIFACTS_AND_FENCES.md`, `05_EVIDENCE_SIMS_NEGATIVE.md`, `11_PROVENANCE_CHAIN_AND_REPLAY.md` | FULL |  |
| RQ-046 RQ-047 RQ-048 | `19_SIM_TIER_ARCHITECTURE.md`, `20_SIM_PROMOTION_AND_MASTER_SIM.md`, `15_AUDIT_GATES_AND_SUCCESS_CRITERIA.md`, `18_A1_A2_CONFORMANCE_CHECKLIST.md` | FULL |  |
| RQ-050 RQ-051 RQ-052 RQ-053 | `06_GRAVEYARD_AND_ALTERNATIVES.md`, `12_TERM_COMPOSITION_AND_RATCHET_COMPLETENESS.md`, `14_DO_NOT_DO_AND_FORBIDDEN_MOVES.md`, `15_AUDIT_GATES_AND_SUCCESS_CRITERIA.md` | FULL |  |
| RQ-060 RQ-061 | `07_DOC_SYSTEM_AND_SHARDING.md`, `15_AUDIT_GATES_AND_SUCCESS_CRITERIA.md` | FULL |  |
| RQ-062 | `00_MANIFEST.md`, `07_DOC_SYSTEM_AND_SHARDING.md` | FULL |  |
| RQ-063 | `11_PROVENANCE_CHAIN_AND_REPLAY.md` | FULL |  |
| RQ-064 RQ-065 | `13_A2_YAML_USAGE_AND_COMPACTION.md`, `16_A2_PERSISTENT_BRAIN_SCHEMA.md` | FULL |  |
| RQ-070 RQ-071 | `14_DO_NOT_DO_AND_FORBIDDEN_MOVES.md`, `15_AUDIT_GATES_AND_SUCCESS_CRITERIA.md` | FULL |  |
| RQ-072 RQ-073 | `14_DO_NOT_DO_AND_FORBIDDEN_MOVES.md`, `15_AUDIT_GATES_AND_SUCCESS_CRITERIA.md` | FULL |  |
| RQ-074 | `08_MODEL_SWITCH_PROTOCOL.md`, `18_A1_A2_CONFORMANCE_CHECKLIST.md` | FULL |  |
| RQ-080 RQ-081 RQ-082 | `01_OVERVIEW.md`, `05_EVIDENCE_SIMS_NEGATIVE.md`, `19_SIM_TIER_ARCHITECTURE.md`, `20_SIM_PROMOTION_AND_MASTER_SIM.md` | PARTIAL | basin metrics are declared but not yet formalized as numeric acceptance thresholds |

==================================================
Open Spec Gaps (explicit)
==================================================

1) A1 LLM strategy acceptance tests:
- Missing deterministic conformance tests for A1 planner outputs before A0 compilation.

2) Basin metrics formalization:
- Need exact quantitative thresholds for "stability", "coverage closure", and "promotion readiness".

3) Scale-control parameters:
- Need fixed defaults for branch budget / repair budget / sim budget per cycle in one authoritative table.

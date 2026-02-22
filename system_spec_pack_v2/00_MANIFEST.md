# SYSTEM SPEC PACK v2 — MANIFEST
Status: DRAFT / NONCANON
Date: 2026-02-20

## Purpose
- Provide a **small, deterministic read spine** that describes the whole system (A2/A1/A0/B/SIM) structurally.
- Prevent doc explosion: fixed file set, with references outward to `core_docs/` and `work/ratchet_core/` only.
- Preserve contradictions: do not resolve bootpack/megaboot drift here.

## Authority
- Source of truth (read-only): `core_docs/`
- Executable prototype (noncanon, audited): `work/ratchet_core/`
- This pack is: draft guidance only.

## Deterministic Read Order
1. `system_v2/specs/system_spec_pack_v2/01_OVERVIEW.md`
2. `system_v2/specs/system_spec_pack_v2/02_THREADS_AND_BOOT.md`
3. `system_v2/specs/system_spec_pack_v2/03_B_ARTIFACTS_AND_FENCES.md`
4. `system_v2/specs/system_spec_pack_v2/04_CANON_STATE_SCHEMA.md`
5. `system_v2/specs/system_spec_pack_v2/05_EVIDENCE_SIMS_NEGATIVE.md`
6. `system_v2/specs/system_spec_pack_v2/06_GRAVEYARD_AND_ALTERNATIVES.md`
7. `system_v2/specs/system_spec_pack_v2/07_DOC_SYSTEM_AND_SHARDING.md`
8. `system_v2/specs/system_spec_pack_v2/08_MODEL_SWITCH_PROTOCOL.md`
9. `system_v2/specs/system_spec_pack_v2/09_A1_STRATEGY_DECLARATION.md`
10. `system_v2/specs/system_spec_pack_v2/10_TRANSLATOR_BOUNDARY_AND_POLICY.md`
11. `system_v2/specs/system_spec_pack_v2/11_PROVENANCE_CHAIN_AND_REPLAY.md`
12. `system_v2/specs/system_spec_pack_v2/12_TERM_COMPOSITION_AND_RATCHET_COMPLETENESS.md`
13. `system_v2/specs/system_spec_pack_v2/13_A2_YAML_USAGE_AND_COMPACTION.md`
14. `system_v2/specs/system_spec_pack_v2/14_DO_NOT_DO_AND_FORBIDDEN_MOVES.md`
15. `system_v2/specs/system_spec_pack_v2/15_AUDIT_GATES_AND_SUCCESS_CRITERIA.md`
16. `system_v2/specs/system_spec_pack_v2/16_A2_PERSISTENT_BRAIN_SCHEMA.md`
17. `system_v2/specs/system_spec_pack_v2/17_A1_REPAIR_LOOP_AND_WIGGLE_PROTOCOL.md`
18. `system_v2/specs/system_spec_pack_v2/18_A1_A2_CONFORMANCE_CHECKLIST.md`
19. `system_v2/specs/system_spec_pack_v2/19_SIM_TIER_ARCHITECTURE.md`
20. `system_v2/specs/system_spec_pack_v2/20_SIM_PROMOTION_AND_MASTER_SIM.md`
21. `system_v2/specs/system_spec_pack_v2/21_SYSTEM_REQUIREMENTS_LEDGER.md`
22. `system_v2/specs/system_spec_pack_v2/22_SPEC_COVERAGE_MATRIX.md`

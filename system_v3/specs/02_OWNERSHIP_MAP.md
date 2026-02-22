# Ownership Map
Status: DRAFT / NONCANON
Date: 2026-02-20

## Rule
Each requirement ID has exactly one normative owner.
If a non-owner doc needs the requirement, it references the ID only.

## Normative Owners
- `03_B_KERNEL_SPEC.md` owns: `RQ-020..RQ-029`, `RQ-060..RQ-064` (B-side graveyard write contract)
- `04_A0_COMPILER_SPEC.md` owns: `RQ-030..RQ-039`
- `05_A1_STRATEGY_AND_REPAIR_SPEC.md` owns: `RQ-040..RQ-049`, `RQ-097..RQ-098`
- `06_SIM_EVIDENCE_AND_TIERS_SPEC.md` owns: `RQ-050..RQ-059`
- `07_A2_OPERATIONS_SPEC.md` owns: `RQ-070..RQ-078`
- `09_CONFORMANCE_AND_REDUNDANCY_GATES.md` owns: `RQ-080..RQ-088`
- `16_ZIP_SAVE_AND_TAPES_SPEC.md` owns: `RQ-090..RQ-096`
- `18_A1_WIGGLE_EXECUTION_CONTRACT.md` owns: `RQ-100..RQ-108`
- `19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md` owns: `RQ-109..RQ-116`
- `20_CONTROLLED_TUNING_AND_UPGRADE_CONTRACT.md` owns: `RQ-117..RQ-124`
- `21_IMPLEMENTATION_BUILD_SEQUENCE_AND_ACCEPTANCE_MATRIX.md` owns: `RQ-125..RQ-132`
- `22_RUN_SURFACE_TEMPLATE_AND_SCAFFOLDER_CONTRACT.md` owns: `RQ-133..RQ-138`
- `23_BOOTPACK_CONFORMANCE_FIXTURE_MATRIX_CONTRACT.md` owns: `RQ-139..RQ-144`

## Global IDs
- `RQ-001..RQ-004`, `RQ-010..RQ-014` are global constraints defined in `01_REQUIREMENTS_LEDGER.md`.

## Extract/Reference Docs (Non-Owners)
- `17_BOOTPACK_THREAD_B_v3.9.13_ENFORCEABLE_CONTRACT_EXTRACT_FOR_IMPLEMENTATION_v1.md`
  - Purpose: compact implementer-facing extract of container grammar + enforceable fence rules.
  - Owner: NONE (authority remains in `core_docs/BOOTPACK_THREAD_B_v3.9.13.md`).

## Non-owner Usage
Non-owner docs may only:
- cite `RQ-*`
- add implementation notes
- add cross-references

Non-owner docs may not:
- redefine MUST clauses
- relax/strengthen requirement semantics
- change requirement IDs

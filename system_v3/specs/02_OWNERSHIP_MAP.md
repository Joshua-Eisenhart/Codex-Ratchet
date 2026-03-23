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
- `07_A2_OPERATIONS_SPEC.md` owns: `RQ-070..RQ-078`, `RQ-145..RQ-147`
- `09_CONFORMANCE_AND_REDUNDANCY_GATES.md` owns: `RQ-080..RQ-088`
- `16_ZIP_SAVE_AND_TAPES_SPEC.md` owns: `RQ-090..RQ-096`
- `18_A1_WIGGLE_EXECUTION_CONTRACT.md` owns: `RQ-100..RQ-108`
- `19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md` owns: `RQ-109..RQ-116`
- `20_CONTROLLED_TUNING_AND_UPGRADE_CONTRACT.md` owns: `RQ-117..RQ-124`
- `21_IMPLEMENTATION_BUILD_SEQUENCE_AND_ACCEPTANCE_MATRIX.md` owns: `RQ-125..RQ-132`
- `22_RUN_SURFACE_TEMPLATE_AND_SCAFFOLDER_CONTRACT.md` owns: `RQ-133..RQ-138`
- `23_BOOTPACK_CONFORMANCE_FIXTURE_MATRIX_CONTRACT.md` owns: `RQ-139..RQ-144`

## A1 Owner-Scope Note
- `05_A1_STRATEGY_AND_REPAIR_SPEC.md` remains the owner for `RQ-040..RQ-049` and `RQ-097..RQ-098`.
- But it is a mixed draft surface: use its live/profile-facing sections for current packet/profile guidance, and treat sections explicitly labeled `Legacy` as historical branch-model doctrine.
- `18_A1_WIGGLE_EXECUTION_CONTRACT.md` remains the owner for `RQ-100..RQ-108`, but its operator/quota sections are historical draft wiggle doctrine rather than the live runtime/control operator law.
- For the live A1 operator enum/mapping used by the current runtime/control path, use:
  - `system_v3/control_plane_bundle_work/system_v3_control_plane/specs/ENUM_REGISTRY_v1.md`
  - `system_v3/control_plane_bundle_work/system_v3_control_plane/specs/A1_REPAIR_OPERATOR_MAPPING_v1.md`
  - `system_v3/control_plane_bundle_work/system_v3_control_plane/specs/A1_STRATEGY_v1.md`

## Global IDs
- `RQ-001..RQ-004`, `RQ-010..RQ-014` are global constraints defined in `01_REQUIREMENTS_LEDGER.md`.

## Extract/Reference Docs (Non-Owners)
- `17_BOOTPACK_THREAD_B_v3.9.13_ENFORCEABLE_CONTRACT_EXTRACT_FOR_IMPLEMENTATION_v1.md`
  - Purpose: compact implementer-facing extract of container grammar + enforceable fence rules.
  - Owner: NONE (authority remains in `core_docs/BOOTPACK_THREAD_B_v3.9.13.md`).
- `77_A1_LIVE_PACKET_PROFILE_EXTRACT__v1.md`
  - Purpose: compact current A1 packet/profile reload surface extracted from the mixed `05` owner doc plus live control-plane strategy/operator surfaces.
  - Owner: NONE (authority remains in `05_A1_STRATEGY_AND_REPAIR_SPEC.md` and the control-plane A1 strategy/operator specs).
- `78_A1_HISTORICAL_BRANCH_WIGGLE_EXTRACT__v1.md`
  - Purpose: compact historical branch/wiggle reload surface extracted from `18` and the legacy sections of `05`.
  - Owner: NONE (authority remains in the draft owner surfaces `05_A1_STRATEGY_AND_REPAIR_SPEC.md` and `18_A1_WIGGLE_EXECUTION_CONTRACT.md`).

## Non-owner Usage
Non-owner docs may only:
- cite `RQ-*`
- add implementation notes
- add cross-references

Non-owner docs may not:
- redefine MUST clauses
- relax/strengthen requirement semantics
- change requirement IDs

# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID DEPENDENCY MAP
Batch: `BATCH_A2MID_megaboot_authority_topology_bootpack_drift__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Parent batch
- `BATCH_upgrade_docs_megaboot_ratchet_suite_source_map__v1`
- reused parent artifacts:
  - `SOURCE_MAP__v1.md`
  - `CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_DISTILLATES__v1.md`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md`
  - `MANIFEST.json`

## Parent-batch read
- the parent already isolates the main reusable seams of the composite megadoc:
  - one canon-labeled wrapper over mixed internal authorities
  - unresolved `THREAD_S` / `THREAD_SIM` / A0 topology and ownership drift
  - plural save and restore paths
  - duplicated embedded Thread B copies with a real correction
  - aggressive exploration pressure bounded by linting, replay, and one-container discipline
- the parent is broad, but it is already segmented enough that no raw-source reread is needed for this bounded reduction

## Control-surface dependencies read but not mutated
- `system_v3/specs/07_A2_OPERATIONS_SPEC.md`
- `system_v3/a2_state/SURFACE_CLASS_AND_MEMORY_ADMISSION_RULES__v1.md`
- `system_v3/a2_state/A2_BRAIN_SLICE__v1.md`
- `system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md`
- `system_v3/a2_state/A2_TERM_CONFLICT_MAP__v1.md`
- `system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md`
- `system_v3/a2_state/OPEN_UNRESOLVED__v1.md`
- `system_v3/a2_high_entropy_intake_surface/A2_HIGH_ENTROPY_INTAKE_PROCESS__v1.md`
- `system_v3/a2_high_entropy_intake_surface/A2_MID_REFINEMENT_PROCESS__v1.md`
- `system_v3/a2_high_entropy_intake_surface/BATCH_INDEX__v1.md`

## Comparison anchors
- `BATCH_A2MID_bootpack_thread_b_kernel_gating__v1`
  - used to preserve the later standalone upgrade-doc Thread B copy as a sibling kernel/gating reduction rather than collapsing it into the megadoc wrapper
- `BATCH_A2MID_a2feed_thread_b_provenance_admission_fences__v1`
  - used to keep the earlier a2feed Thread B lineage visible so the megadoc's embedded `v3.9.13` pair is read as one family layer, not as universal closure
- `BATCH_A2MID_reentry_gap_selection_audit__v1`
  - used only as the immediate lane-selection anchor for why this large parent was chosen after the compact Thread B child was completed

## Candidate dependency map
- `RC1 MEGABOOT_CANON_WRAPPER_IS_MIXED_AUTHORITY_ENVELOPE`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C9`
    - `A2_3_DISTILLATES__v1.md:D1`
    - `A2_3_DISTILLATES__v1.md:D8`
    - `TENSION_MAP__v1.md:T2`
- `RC2 MEGABOOT_AUTHORITY_STOPS_ABOVE_B_KERNEL_LOAD_BOUNDARY`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C1`
    - `CLUSTER_MAP__v1.md:C9`
    - `TENSION_MAP__v1.md:T4`
  - comparison anchors:
    - `BATCH_A2MID_bootpack_thread_b_kernel_gating__v1:A2_2_REFINED_CANDIDATES__v1.md:RC1`
    - `BATCH_A2MID_a2feed_thread_b_provenance_admission_fences__v1:A2_2_REFINED_CANDIDATES__v1.md:RC5`
- `RC3 THREAD_S_THREAD_SIM_AND_A0_OWNERSHIP_REMAINS_PLURAL`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C1`
    - `CLUSTER_MAP__v1.md:C2`
    - `CLUSTER_MAP__v1.md:C5`
    - `A2_3_DISTILLATES__v1.md:D2`
    - `A2_3_DISTILLATES__v1.md:D6`
    - `TENSION_MAP__v1.md:T1`
    - `TENSION_MAP__v1.md:T9`
- `RC4 RESTORE_PATHS_REMAIN_PLURAL_WITH_COMPATIBILITY_RESIDUE`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C2`
    - `A2_3_DISTILLATES__v1.md:D2`
    - `TENSION_MAP__v1.md:T6`
- `RC5 EMBEDDED_THREAD_B_PAIR_MUST_STAY_COPY_DELTA_PRESERVED`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C8`
    - `A2_3_DISTILLATES__v1.md:D7`
    - `TENSION_MAP__v1.md:T7`
  - comparison anchors:
    - `BATCH_A2MID_bootpack_thread_b_kernel_gating__v1:A2_2_REFINED_CANDIDATES__v1.md:RC6`
    - `BATCH_A2MID_a2feed_thread_b_provenance_admission_fences__v1:A2_2_REFINED_CANDIDATES__v1.md:RC1`
- `RC6 EXPLORATION_SCALE_REQUIRES_RECORDING_LINT_AND_REPLAY_DISCIPLINE`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C5`
    - `A2_3_DISTILLATES__v1.md:D5`
    - `TENSION_MAP__v1.md:T5`

## Quarantine dependency map
- `Q1 CANON_WRAPPER_LABEL_AS_INTERNAL_AUTHORITY_RESOLUTION`
  - `A2_3_DISTILLATES__v1.md:D8`
  - `TENSION_MAP__v1.md:T2`
- `Q2 NO_SEPARATE_THREAD_S_THREAD_SIM_AS_FINAL_TOPOLOGY`
  - `A2_3_DISTILLATES__v1.md:D6`
  - `TENSION_MAP__v1.md:T1`
- `Q3 THREAD_A0_THREAD_A_THREAD_S_AND_OWNERSHIP_DRIFT_AS_ALREADY_CLEANED_UP`
  - `TENSION_MAP__v1.md:T3`
  - `TENSION_MAP__v1.md:T9`
- `Q4 DIRECT_LEGACY_PASTE_OR_A0_RESTORE_AS_ONLY_VALID_RESTORE_PATH`
  - `TENSION_MAP__v1.md:T6`
  - `A2_3_DISTILLATES__v1.md:D2`
- `Q5 SILENT_SELECTION_OF_ONE_EMBEDDED_THREAD_B_COPY`
  - `A2_3_DISTILLATES__v1.md:D7`
  - `TENSION_MAP__v1.md:T7`
- `Q6 MASSIVE_EXPLORATION_AS_IF_ONE_CONTAINER_AND_REPLAY_BOUNDS_DO_NOT_APPLY`
  - `A2_3_DISTILLATES__v1.md:D5`
  - `TENSION_MAP__v1.md:T5`
- `Q7 SACRED_HEART_N01_AS_ALREADY_NAMESPACE_COMPATIBLE_WITH_EMBEDDED_THREAD_B`
  - `TENSION_MAP__v1.md:T8`
  - `A2_TERM_CONFLICT_MAP__v1.md`

## Raw reread status
- raw source reread needed: `false`
- reason:
  - the parent source-map batch already isolates the required contradiction families and embedded-bootpack drift markers
  - the two standalone Thread B children provide enough sibling context to keep this reduction comparison-ready without reopening raw megadoc text

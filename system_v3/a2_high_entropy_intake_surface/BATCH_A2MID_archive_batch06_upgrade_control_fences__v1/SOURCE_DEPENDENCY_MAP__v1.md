# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID SOURCE DEPENDENCY MAP
Batch: `BATCH_A2MID_archive_batch06_upgrade_control_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Primary parent batch
- `BATCH_archive_surface_batch06_upgrade_bootpack_and_plan_passes_1_4__v1`

## Comparison anchors used for narrowing
- `BATCH_A2MID_archive_batch05_mint_boundary_fences__v1`
- `BATCH_A2MID_a2feed_thread_b_provenance_admission_fences__v1`
- `BATCH_A2MID_megaboot_authority_topology_bootpack_drift__v1`

## Parent artifacts read
- `MANIFEST.json`
- `SOURCE_MAP__v1.md`
- `CLUSTER_MAP__v1.md`
- `TENSION_MAP__v1.md`
- `A2_3_DISTILLATES__v1.md`
- `A2_2_CANDIDATE_SUMMARIES__v1.md`

## Dependency notes
- this pass operates from the archive batch06 upgrade-control package as the primary artifact
- the batch05 child is used to preserve the archive shift:
  - batch05 centers stage-2 mint history and weaker locks
  - batch06 shifts into upgrade-control doctrine with restored exact lock rows
- the source-bearing Thread B child is used to keep source-local provenance, admission grammar, and replay discipline above archive upgrade synthesis
- the megaboot child is used to keep wrapper-versus-kernel authority and plural topology contradictions visible above this archive packet
- no raw-source reread was needed because the parent already isolates:
  - output-only retention
  - restored but meta-dependent lock outputs
  - Thread S instability
  - ZIP taxonomy collapse
  - fail-closed enforcement drift
  - graveyard and Rosetta noncanon exploration

## Candidate-to-parent dependency map
- `RC1_ARCHIVE_BATCH06_STAYS_UPGRADE_CONTROL_MINT_HISTORY`
  - parent source map:
    - output-only upgrade-control package class
  - parent distillate:
    - `D1`
  - parent candidate:
    - `C1`
  - parent tension:
    - `T1`
- `RC2_UPGRADE_LINEAGE_PACKET_AROUND_THREAD_S_ZIP_AND_MODE_CONFIRMATION`
  - parent clusters:
    - `Cluster 3`
    - `Cluster 4`
    - `Cluster 5`
  - parent distillates:
    - `D2`
    - `D5`
    - `D7`
  - parent candidate:
    - `C2`
  - comparison anchor:
    - `BATCH_A2MID_archive_batch05_mint_boundary_fences__v1:RC2`
- `RC3_RESTORED_ROSETTA_LOCKS_REMAIN_META_DEPENDENT_ARCHIVE_LINEAGE`
  - parent cluster:
    - `Cluster 6`
  - parent distillate:
    - `D3`
  - parent candidate:
    - `C3`
  - parent tension:
    - `T2`
  - comparison anchors:
    - `BATCH_A2MID_archive_batch05_mint_boundary_fences__v1:RC3`
    - `BATCH_A2MID_archive_batch05_mint_boundary_fences__v1:RC4`
- `RC4_THREAD_S_INSTABILITY_REMAINS_THE_CENTRAL_ARCHITECTURE_CONTRADICTION`
  - parent cluster:
    - `Cluster 3`
  - parent distillate:
    - `D4`
  - parent candidate:
    - `C2`
  - parent tension:
    - `T4`
  - comparison anchor:
    - `BATCH_A2MID_megaboot_authority_topology_bootpack_drift__v1:RC3`
- `RC5_ZIP_FIRST_DOCTRINE_REQUIRES_TAXONOMY_AND_BOUNDARY_NARROWING`
  - parent cluster:
    - `Cluster 4`
  - parent distillates:
    - `D5`
    - `D7`
  - parent candidate:
    - `C2`
  - parent tension:
    - `T5`
- `RC6_OUTPUT_CONTRACT_FAIL_CLOSED_LANGUAGE_DRIFTS_BELOW_BOOTPACK_ENFORCEMENT`
  - parent clusters:
    - `Cluster 2`
    - `Cluster 5`
  - parent distillate:
    - `D6`
  - parent candidate:
    - `C4`
  - parent tension:
    - `T6`
  - comparison anchors:
    - `BATCH_A2MID_a2feed_thread_b_provenance_admission_fences__v1:RC2`
    - `BATCH_A2MID_a2feed_thread_b_provenance_admission_fences__v1:RC6`
- `RC7_GRAVEYARD_AND_ROSETTA_EXPLORATION_STAY_NONCANON_SUPPORT_ONLY`
  - parent cluster:
    - `Cluster 7`
  - parent distillate:
    - `D2`
  - parent candidate:
    - `C2`
  - parent tension:
    - `T8`

## Quarantine dependency map
- `Q1_ARCHIVE_UPGRADE_CONTROL_PACKAGE_AS_ACTIVE_RUNTIME_AUTHORITY`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C1`
  - `TENSION_MAP__v1.md:T1`
- `Q2_RESTORED_LOCK_OUTPUTS_AS_IN_BUNDLE_SEED_VERIFIED_AUTHORITY`
  - `A2_3_DISTILLATES__v1.md:D3`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C3`
  - `TENSION_MAP__v1.md:T2`
- `Q3_PASS_TEMPLATE_STRUCT_AS_BUNDLE_CONTAINED_SCHEMA_PROOF`
  - `TENSION_MAP__v1.md:T3`
- `Q4_THREAD_S_ROLE_AS_STABILIZED_UPGRADE_OUTCOME`
  - `A2_3_DISTILLATES__v1.md:D4`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C5`
  - `TENSION_MAP__v1.md:T4`
- `Q5_ZIP_AS_DEFINITIONALLY_CLEAN_CHATLESS_SUBAGENT_DOCTRINE`
  - `A2_3_DISTILLATES__v1.md:D5`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C5`
  - `TENSION_MAP__v1.md:T5`
- `Q6_FAIL_CLOSED_OUTPUT_CONTRACT_AS_KERNEL_GRADE_PROOF_SURFACE`
  - `A2_3_DISTILLATES__v1.md:D6`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C4`
  - `TENSION_MAP__v1.md:T6`
- `Q7_GRAVEYARD_OR_ROSETTA_EXPLORATION_AS_CANONICAL_CONTROL_LAW`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C5`
  - `TENSION_MAP__v1.md:T8`

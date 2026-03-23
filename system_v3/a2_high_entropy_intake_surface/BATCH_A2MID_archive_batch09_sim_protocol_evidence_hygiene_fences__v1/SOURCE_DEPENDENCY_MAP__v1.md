# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID SOURCE DEPENDENCY MAP
Batch: `BATCH_A2MID_archive_batch09_sim_protocol_evidence_hygiene_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Primary parent batch
- `BATCH_archive_surface_batch09_sim_protocol_and_evidence_surface__v1`

## Comparison anchors used for narrowing
- `BATCH_A2MID_archive_batch08_structural_memory_lock_transport_fences__v1`
- `BATCH_A2MID_archive_batch07_audit_gap_zip_taxonomy_fences__v1`
- `BATCH_A2MID_archive_batch06_upgrade_control_fences__v1`

## Parent artifacts read
- `MANIFEST.json`
- `SOURCE_MAP__v1.md`
- `CLUSTER_MAP__v1.md`
- `TENSION_MAP__v1.md`
- `A2_3_DISTILLATES__v1.md`
- `A2_2_CANDIDATE_SUMMARIES__v1.md`

## Dependency notes
- this pass operates from the archive batch09 SIM protocol and evidence package as the primary artifact
- the batch08 child is used to preserve the archive shift:
  - batch08 centers structural-memory carrier, transport hardening, and exact lock lineage
  - batch09 centers SIM workflow, evidence hygiene, protocol contradictions, and topic-label drift
- the batch07 child is used to keep audit-gap and hygiene contradiction lineage visible below the more protocol-specific package
- the batch06 child is used to preserve the earlier exact-lock archive seam below active authority
- no raw-source reread was needed because the parent already isolates:
  - output-only retention
  - Thread-B purity and deterministic SIM workflow
  - SIM_EVIDENCE formatting
  - code-fence and blank-line contamination contradictions
  - absent-meta rosetta seam
  - topic-label overreach

## Candidate-to-parent dependency map
- `RC1_ARCHIVE_BATCH09_STAYS_SIM_PROTOCOL_AND_EVIDENCE_HISTORY`
  - parent source map:
    - archive protocol/evidence output carrier class
  - parent distillate:
    - `D1`
  - parent candidate:
    - `C1`
  - parent tension:
    - `T1`
- `RC2_THREAD_B_PURITY_AND_DETERMINISTIC_SIM_WORKFLOW_ARE_CORE_REUSABLE_LINEAGE`
  - parent cluster:
    - `Cluster 2`
  - parent distillates:
    - `D2`
    - `D6`
  - parent candidate:
    - `C2`
  - parent tension:
    - `T2`
- `RC3_EVIDENCE_SURFACE_FORMATTING_AND_CONTAMINATION_RULES_REMAIN_HIGH_VALUE_CLEANUP_PACKET`
  - parent clusters:
    - `Cluster 3`
    - `Cluster 5`
  - parent distillate:
    - `D4`
  - parent candidate:
    - `C2`
  - parent tensions:
    - `T3`
    - `T4`
  - comparison anchor:
    - `BATCH_A2MID_archive_batch07_audit_gap_zip_taxonomy_fences__v1:RC5`
- `RC4_METRIC_BEARING_EVIDENCE_REMAINS_ENGINEERING_CONTEXT_NOT_STANDALONE_TRUTH`
  - parent clusters:
    - `Cluster 2`
    - `Cluster 3`
  - parent distillates:
    - `D2`
    - `D6`
  - parent candidate:
    - `C3`
  - parent tension:
    - `T2`
- `RC5_EXACT_ROSETTA_TABLES_REMAIN_ABSENT_META_DEPENDENT_OVERLAY_LINEAGE`
  - parent cluster:
    - `Cluster 4`
  - parent distillate:
    - `D3`
  - parent candidate:
    - `C4`
  - parent tension:
    - `T6`
  - comparison anchors:
    - `BATCH_A2MID_archive_batch08_structural_memory_lock_transport_fences__v1:RC4`
    - `BATCH_A2MID_archive_batch06_upgrade_control_fences__v1:RC3`
- `RC6_TOPIC_LABEL_OVERREACH_REMAINS_EXPLICIT_SEMANTIC_DRIFT_PACKET`
  - parent cluster:
    - `Cluster 6`
  - parent distillate:
    - `D5`
  - parent candidates:
    - `C3`
    - `C5`
  - parent tensions:
    - `T7`
    - `T8`

## Quarantine dependency map
- `Q1_ARCHIVE_SIM_PROTOCOL_PACKAGE_AS_CURRENT_ACTIVE_SIM_AUTHORITY`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C1`
  - `TENSION_MAP__v1.md:T1`
- `Q2_METRIC_BEARING_EVIDENCE_AS_STANDALONE_TRUTH_SIGNAL`
  - `A2_3_DISTILLATES__v1.md:D2`
  - `A2_3_DISTILLATES__v1.md:D6`
  - `TENSION_MAP__v1.md:T2`
- `Q3_CODE_FENCED_CORRECT_EXAMPLE_AS_RESOLUTION_OF_CONTAMINATION_RULES`
  - `A2_3_DISTILLATES__v1.md:D4`
  - `TENSION_MAP__v1.md:T3`
- `Q4_BLANK_LINE_SEPARATORS_AS_FULLY_THREAD_B_PURE`
  - `A2_3_DISTILLATES__v1.md:D4`
  - `TENSION_MAP__v1.md:T4`
- `Q5_ABSENT_META_ROSETTA_TABLES_AS_IN_BUNDLE_AUTHORITY`
  - `A2_3_DISTILLATES__v1.md:D3`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C4`
  - `TENSION_MAP__v1.md:T6`
- `Q6_SOCIETAL_RESILIENCE_AND_ALIGNMENT_LABELS_AS_EXPLICITLY_SOURCED_HERE`
  - `A2_3_DISTILLATES__v1.md:D5`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C5`
  - `TENSION_MAP__v1.md:T7`
  - `TENSION_MAP__v1.md:T8`

# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID DEPENDENCY MAP
Batch: `BATCH_A2MID_upgrade_family_topology_control_seams__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Parent batch
- `BATCH_upgrade_docs_system_upgrade_plan_extract_family_source_map__v1`
- reused parent artifacts:
  - `SOURCE_MAP__v1.md`
  - `CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_DISTILLATES__v1.md`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md`
  - `MANIFEST.json`

## Comparison anchors
- `BATCH_A2MID_upgrade_plan_integration_targets__v1`
  - used because the upgrade-pass family repeatedly restates megaboot-preserving upgrade intent, ZIP-first continuity pressure, and nonclosure around planned changes
- `BATCH_A2MID_sims_evidence_boundary__v1`
  - used because the family's SIM contract is strongest where approval, deterministic execution, and evidence return remain role-separated
- `BATCH_A2MID_zip_index_bundle_boundaries__v1`
  - used because the family's ZIP language is best interpreted against the archived bundle and transport-boundary drift already narrowed in the zip-index pass

## Candidate dependency map
- `RC1 STAGED_EXTRACTION_SCAFFOLD_NONAUTHORITY_RULE`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C9`
    - `A2_3_DISTILLATES__v1.md:D1`
    - `A2_3_DISTILLATES__v1.md:D7`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C1`
    - `TENSION_MAP__v1.md:T6`
- `RC2 MEGABOOT_INSIDE_SOURCE_AND_THREAD_CONSOLIDATION_PACKET`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C1`
    - `CLUSTER_MAP__v1.md:C2`
    - `A2_3_DISTILLATES__v1.md:D2`
    - `A2_3_DISTILLATES__v1.md:D3`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C2`
    - `TENSION_MAP__v1.md:T1`
    - `TENSION_MAP__v1.md:T3`
    - `TENSION_MAP__v1.md:T5`
  - comparison anchors:
    - `BATCH_A2MID_upgrade_plan_integration_targets__v1:RC2`
- `RC3 ZIP_SUBAGENT_BOUNDARY_DESIRED_BUT_UNSTABLE_PACKET`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C3`
    - `A2_3_DISTILLATES__v1.md:D3`
    - `A2_3_DISTILLATES__v1.md:D8`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C2`
    - `TENSION_MAP__v1.md:T2`
    - `TENSION_MAP__v1.md:T8`
  - comparison anchors:
    - `BATCH_A2MID_upgrade_plan_integration_targets__v1:RC5`
    - `BATCH_A2MID_zip_index_bundle_boundaries__v1:RC6`
- `RC4 SIM_APPROVAL_AND_EVIDENCE_RETURN_CONTRACT`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C4`
    - `A2_3_DISTILLATES__v1.md:D4`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C2`
  - comparison anchors:
    - `BATCH_A2MID_sims_evidence_boundary__v1:RC2`
    - `BATCH_A2MID_sims_evidence_boundary__v1:RC3`
- `RC5 A1_MODE_CONTROL_REAL_BUT_ENFORCEMENT_DOUBTFUL_PACKET`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C7`
    - `A2_3_DISTILLATES__v1.md:D6`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C2`
    - `TENSION_MAP__v1.md:T4`
- `RC6 EXTRACTION_LOOP_AND_REDUNDANCY_DEFENSE_RULE`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C9`
    - `A2_3_DISTILLATES__v1.md:D1`
    - `A2_3_DISTILLATES__v1.md:D7`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C1`
    - `TENSION_MAP__v1.md:T6`
    - `TENSION_MAP__v1.md:T9`

## Quarantine dependency map
- `Q1 CLEAN_THREAD_S_ELIMINATION_STORY`
  - `CLUSTER_MAP__v1.md:C2`
  - `A2_3_DISTILLATES__v1.md:D2`
  - `A2_3_DISTILLATES__v1.md:D8`
  - `TENSION_MAP__v1.md:T3`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C3`
- `Q2 FULLY_SETTLED_ZIP_SUBAGENT_ONTOLOGY`
  - `CLUSTER_MAP__v1.md:C3`
  - `A2_3_DISTILLATES__v1.md:D3`
  - `A2_3_DISTILLATES__v1.md:D8`
  - `TENSION_MAP__v1.md:T2`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C3`
- `Q3 DETERMINISTIC_A1_MODE_ENFORCEMENT_AS_SOLVED`
  - `CLUSTER_MAP__v1.md:C7`
  - `A2_3_DISTILLATES__v1.md:D6`
  - `TENSION_MAP__v1.md:T4`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C3`
- `Q4 FINALIZED_SAVE_LOAD_HASH_AND_FULLPLUS_RESTORE_DOCTRINE`
  - `CLUSTER_MAP__v1.md:C8`
  - `A2_3_DISTILLATES__v1.md:D8`
  - `TENSION_MAP__v1.md:T8`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C3`
- `Q5 EXTRACTION_OUTPUTS_AS_AUTHORITATIVE_RUNTIME_SPEC`
  - `CLUSTER_MAP__v1.md:C9`
  - `A2_3_DISTILLATES__v1.md:D7`
  - `TENSION_MAP__v1.md:T5`
  - `TENSION_MAP__v1.md:T9`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C3`

## Raw reread status
- raw source reread needed: `false`
- reason:
  - the parent batch already isolates the repeated topology, ZIP, SIM, mode-control, and extraction-loop seams needed for this bounded contradiction-preserving reduction

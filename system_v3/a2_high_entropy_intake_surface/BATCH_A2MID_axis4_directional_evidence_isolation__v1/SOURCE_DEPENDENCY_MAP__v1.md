# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID DEPENDENCY MAP
Batch: `BATCH_A2MID_axis4_directional_evidence_isolation__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Parent batch
- `BATCH_sims_axis4_directional_suite_family__v1`
- reused parent artifacts:
  - `SOURCE_MAP__v1.md`
  - `SIM_CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_SIM_DISTILLATES__v1.md`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md`
  - `MANIFEST.json`

## Comparison anchors
- `BATCH_A2MID_sims_evidence_boundary__v1`
  - used because it provides the nearest existing sims-wide evidence transport contract and hash-anchored boundary packet
- `BATCH_A2MID_sims_axis4_p03_evidence_path__v1`
  - used because it provides the nearest earlier Axis4 evidence-alignment packet and polarity-specific sequence read
- `BATCH_A2MID_sims_runner_pairing_hygiene__v1`
  - used because it provides the nearest runner/result pairing rule and direction-sensitive anti-flattening packet

## Candidate dependency map
- `RC1 AXIS4_DIRECTIONAL_SUITE_EXECUTABLE_THEORY_AND_EVIDENCE_SPLIT`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:S1`
    - `SIM_CLUSTER_MAP__v1.md:S2`
    - `SIM_CLUSTER_MAP__v1.md:S5`
    - `SIM_CLUSTER_MAP__v1.md:S6`
    - `A2_3_SIM_DISTILLATES__v1.md:D1`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C1`
- `RC2 RUNNER_RESULT_PAIRING_WITH_PRODUCER_HASH_SUSPENSION_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:S6`
    - `A2_3_SIM_DISTILLATES__v1.md:D5`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C4`
    - `TENSION_MAP__v1.md:T1`
  - comparison anchors:
    - `BATCH_A2MID_sims_evidence_boundary__v1:RC3`
    - `BATCH_A2MID_sims_runner_pairing_hygiene__v1:RC1`
- `RC3 DIRECTION_LABEL_NOT_DIRECTION_ISOLATION_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:S6`
    - `TENSION_MAP__v1.md:T2`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C4`
  - comparison anchors:
    - `BATCH_A2MID_sims_evidence_boundary__v1:RC3`
- `RC4 AGGREGATE_BIDIR_MINUS_ONLY_COMPRESSION_LAYER_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:S5`
    - `A2_3_SIM_DISTILLATES__v1.md:D4`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C3`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C5`
    - `TENSION_MAP__v1.md:T3`
- `RC5 TYPE2_RESULT_AND_AGGREGATE_PRESENCE_WITH_TOPLEVEL_EVIDENCE_GAP`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:S2`
    - `A2_3_SIM_DISTILLATES__v1.md:D6`
    - `TENSION_MAP__v1.md:T4`
  - comparison anchors:
    - `BATCH_A2MID_sims_axis4_p03_evidence_path__v1:RC4`
- `RC6 PLUS_BRANCH_TYPE_INERTIA_AND_MINUS_BRANCH_SIGNAL_SPLIT`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:S3`
    - `SIM_CLUSTER_MAP__v1.md:S4`
    - `A2_3_SIM_DISTILLATES__v1.md:D2`
    - `A2_3_SIM_DISTILLATES__v1.md:D3`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C2`
    - `TENSION_MAP__v1.md:T5`
  - comparison anchors:
    - `BATCH_A2MID_sims_axis4_p03_evidence_path__v1:RC5`
    - `BATCH_A2MID_sims_runner_pairing_hygiene__v1:RC6`

## Quarantine dependency map
- `Q1 CURRENT_DIRECTIONAL_RUNNER_FILENAMES_AS_PROVEN_EVIDENCED_PRODUCER_PATH`
  - `SIM_CLUSTER_MAP__v1.md:S6`
  - `A2_3_SIM_DISTILLATES__v1.md:D5`
  - `TENSION_MAP__v1.md:T1`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C4`
- `Q2 ONE_DIRECTION_LABEL_EQUALS_ONE_DIRECTION_ONLY_EVIDENCE_BLOCK`
  - `TENSION_MAP__v1.md:T2`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C4`
- `Q3 AGGREGATE_BIDIR_SIBLING_AS_FULL_FAMILY_SUMMARY`
  - `SIM_CLUSTER_MAP__v1.md:S5`
  - `A2_3_SIM_DISTILLATES__v1.md:D4`
  - `TENSION_MAP__v1.md:T3`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C5`
- `Q4 TYPE2_AS_FULLY_EVIDENCED_OR_AS_ABSENT`
  - `A2_3_SIM_DISTILLATES__v1.md:D6`
  - `TENSION_MAP__v1.md:T4`
- `Q5 UNIFORM_PER_SEQUENCE_ARTIFACT_POLICY_ACROSS_THE_FAMILY`
  - `TENSION_MAP__v1.md:T6`

## Raw reread status
- raw source reread needed: `false`
- reason:
  - the parent batch already isolates the executable/theory/evidence split, provenance mismatch, branch behavior, and coverage gaps needed for this bounded evidence-isolation reduction

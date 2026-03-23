# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_A2MID_archive_ladder_seed_action_name_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Parent dependency map
- `RC1`
  - parent:
    - `A2_3_DISTILLATES__v1.md:Distillate 1`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:Candidate Summary A`
    - `SOURCE_MAP__v1.md:Segment A`
  - comparison:
    - `BATCH_A2MID_archive_working_run_bundle_packet_identity_fences__v1:RC1`
    - `BATCH_A2MID_archive_progress_bundle_v2_patch_resume_fences__v1:RC1`
- `RC2`
  - parent:
    - `A2_3_DISTILLATES__v1.md:Distillate 3`
    - `TENSION_MAP__v1.md:Tension 1`
    - `SOURCE_MAP__v1.md:Segments B and C`
- `RC3`
  - parent:
    - `A2_3_DISTILLATES__v1.md:Distillate 2`
    - `TENSION_MAP__v1.md:Tension 2`
    - `SOURCE_MAP__v1.md:Segment D`
  - comparison:
    - `BATCH_A2MID_archive_working_run_bundle_packet_identity_fences__v1:RC4`
- `RC4`
  - parent:
    - `A2_3_DISTILLATES__v1.md:Distillate 4`
    - `TENSION_MAP__v1.md:Tension 3`
    - `SOURCE_MAP__v1.md:Segments B and E`
  - comparison:
    - `BATCH_A2MID_archive_run_foundation_packet_failure_evidence_fences__v1:RC4`
    - `BATCH_A2MID_archive_run_foundation_packet_failure_evidence_fences__v1:RC5`
- `RC5`
  - parent:
    - `A2_3_DISTILLATES__v1.md:Distillate 4`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:Candidate Summary C`
    - `SOURCE_MAP__v1.md:Segments A and E`
  - comparison:
    - `BATCH_A2MID_archive_working_run_bundle_packet_identity_fences__v1:RC3`
    - `BATCH_A2MID_archive_progress_bundle_v2_patch_resume_fences__v1:RC5`
- `RC6`
  - parent:
    - `SOURCE_MAP__v1.md`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:Candidate Summary A`

## Quarantine dependency map
- `Q1`
  - parent:
    - `A2_3_DISTILLATES__v1.md:Distillate 1`
    - `SOURCE_MAP__v1.md:Segment A`
- `Q2`
  - parent:
    - `A2_3_DISTILLATES__v1.md:Distillate 3`
    - `TENSION_MAP__v1.md:Tension 1`
- `Q3`
  - parent:
    - `TENSION_MAP__v1.md:Tension 2`
    - `SOURCE_MAP__v1.md:Segment D`
- `Q4`
  - parent:
    - `TENSION_MAP__v1.md:Tension 3`
    - `SOURCE_MAP__v1.md:Segment E`
- `Q5`
  - parent:
    - `SOURCE_MAP__v1.md:Segments A and B`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:Candidate Summary A`
  - comparison:
    - `BATCH_A2MID_archive_working_run_bundle_packet_identity_fences__v1:RC1`
    - `BATCH_A2MID_archive_progress_bundle_v2_patch_resume_fences__v1:RC1`
- `Q6`
  - parent:
    - `SOURCE_MAP__v1.md:Segments B and E`
    - `TENSION_MAP__v1.md:Tension 3`
  - comparison:
    - `BATCH_A2MID_archive_run_foundation_packet_failure_evidence_fences__v1:RC4`

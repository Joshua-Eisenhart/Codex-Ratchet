# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / SOURCE-LINKED REDUCTION MAP
Batch: `BATCH_A2MID_full_axis_sampler_descendant_drift__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Parent batch
- `BATCH_sims_full_axis_suite_sampler_family__v1`

## Parent artifacts used directly
- `MANIFEST.json`
- `SOURCE_MAP__v1.md`
- `SIM_CLUSTER_MAP__v1.md`
- `TENSION_MAP__v1.md`
- `A2_3_SIM_DISTILLATES__v1.md`
- `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md`

## Comparison anchors used
- `BATCH_A2MID_batch_v3_precursor_lineage__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - reused for precursor nonauthority and descendant drift comparison
- `BATCH_A2MID_sims_evidence_boundary__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - reused for sims evidence-lane and admission-boundary comparison
- `BATCH_A2MID_engine32_delta_absolute_fences__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - reused for the nearest adjacent-family separation contrast

## Dependency compression
### Parent seams retained
- sampler / precursor family status:
  - parent cluster `S1`
  - parent distillate `D1`
  - parent candidate `C1`
- emitted-name to descendant-name drift:
  - parent cluster `S2`
  - parent distillate `D2`
  - parent candidate `C4`
  - parent tension `T1`
- axis-specific continuity instead of uniform continuity:
  - parent cluster `S3`
  - parent distillates:
    - `D2`
    - `D4`
  - parent candidate `C3`
  - parent tensions:
    - `T2`
    - `T5`
- top-level evidence shift away from sampler SIM_IDs:
  - parent distillate `D3`
  - parent candidate `C2`
  - parent tension `T3`
- sampler hash split from current evidenced descendants:
  - parent cluster `S4`
  - parent distillate `D5`
  - parent candidate `C5`
  - parent tension `T4`
- Axis4 dedicated divergence:
  - parent cluster `S5`
  - parent distillate `D4`
  - parent tension `T6`

## Explicit exclusions
- no raw-doc reread
- no fresh `core_docs` pass beyond the already-intaken parent batch
- no merge with the next history-scan family
- no promotion to A2-1 or A1
- no runtime execution or result regeneration

## Reduced output target
- preserve only the smallest reusable `full_axis_suite` packets:
  - sampler nonauthority
  - rename drift
  - nonuniform continuity
  - evidence-name shift
  - hash-path split
  - Axis4 special divergence

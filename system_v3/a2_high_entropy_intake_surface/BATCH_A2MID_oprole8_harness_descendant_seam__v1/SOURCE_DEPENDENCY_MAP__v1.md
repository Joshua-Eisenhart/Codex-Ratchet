# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / SOURCE-LINKED REDUCTION MAP
Batch: `BATCH_A2MID_oprole8_harness_descendant_seam__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Parent batch
- `BATCH_sims_oprole8_left_right_harness_family__v1`

## Parent artifacts used directly
- `MANIFEST.json`
- `SOURCE_MAP__v1.md`
- `SIM_CLUSTER_MAP__v1.md`
- `TENSION_MAP__v1.md`
- `A2_3_SIM_DISTILLATES__v1.md`
- `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md`

## Comparison anchors used
- `BATCH_A2MID_sims_evidence_boundary__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - reused for the sims evidence-admission boundary and source-local versus repo-top evidence distinction
- `BATCH_A2MID_history_strip_provenance_asymmetry__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - reused for the nearest catalog/local-output versus top-level-admission caution
- `BATCH_sims_sim_suite_v1_descendant_bundle__v1/A2_2_SIM_CANDIDATE_SUMMARIES__v1.md`
  - reused for the nearest descendant-bundle provenance split around `run_sim_suite_v1.py`

## Dependency compression
### Parent seams retained
- standalone harness micro-family identity:
  - parent cluster `A`
  - parent distillate `D1`
  - parent candidates:
    - `C1`
    - `C2`
- placeholder role fence:
  - parent cluster `A`
  - parent distillate `D2`
  - parent candidate `C3`
  - parent tension `T1`
- local evidence versus missing repo-top admission:
  - parent cluster `A`
  - parent distillate `D4`
  - parent tension `T3`
- operator4 descendant separation:
  - parent cluster `B`
  - parent distillate `D3`
  - parent tensions:
    - `T2`
    - `T5`
  - parent candidate `C4`
- descendant evidence-hash versus current-emitter mismatch:
  - parent clusters:
    - `B`
    - `C`
  - parent distillate `D4`
  - parent candidate `C5`
  - parent tension `T4`
- harness-schema and role-behavior seam:
  - parent cluster `A`
  - parent distillate `D5`
  - parent tension `T6`

## Explicit exclusions
- no raw-doc reread
- no fresh `core_docs` pass beyond the already-intaken parent batch
- no merge with `run_sim_suite_v1.py` or `run_sim_suite_v2_full_axes.py`
- no promotion to A2-1 or A1
- no runtime execution or result regeneration

## Reduced output target
- preserve only the smallest reusable `oprole8` packets:
  - harness identity
  - placeholder-role fence
  - local-evidence admission caution
  - descendant separation
  - descendant provenance mismatch
  - schema/behavior seam

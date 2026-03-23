# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / SOURCE-LINKED REDUCTION MAP
Batch: `BATCH_A2MID_sim_suite_v2_externalized_provenance__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Parent batch
- `BATCH_sims_sim_suite_v2_successor_bundle__v1`

## Parent artifacts used directly
- `MANIFEST.json`
- `SOURCE_MAP__v1.md`
- `SIM_CLUSTER_MAP__v1.md`
- `TENSION_MAP__v1.md`
- `A2_3_SIM_DISTILLATES__v1.md`
- `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md`

## Comparison anchors used
- `BATCH_A2MID_sims_evidence_boundary__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - reused for evidence coverage versus provenance-admission separation
- `BATCH_A2MID_sim_suite_v1_descendant_provenance_split__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - reused for predecessor-bundle provenance crossover and bundle-boundary contrast
- `BATCH_A2MID_oprole8_harness_descendant_seam__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - reused for the nearest operator4 current-evidence-hash versus current-emitter mismatch

## Dependency compression
### Parent seams retained
- coherent successor-bundle emission identity:
  - parent cluster `A`
  - parent distillates:
    - `D1`
    - `D4`
  - parent candidates:
    - `C1`
    - `C2`
- all seven evidenced but none under current successor-bundle hash:
  - parent distillate `D2`
  - parent candidate:
    - `C3`
    - `C4`
  - parent tension `T1`
- dedicated-runner externalization:
  - parent cluster `B`
  - parent distillate `D3`
  - parent tensions:
    - `T2`
    - `T3`
    - `T6`
- operator4 cross-bundle provenance seam:
  - parent cluster `C`
  - parent distillate `D3`
  - parent tension `T4`
- Stage16 V5 provenance drift plus byte identity with V4:
  - parent clusters:
    - `C`
    - `D`
  - parent tensions:
    - `T5`
- Negctrl malformed and foreign provenance:
  - parent cluster `C`
  - parent tensions:
    - `T7`
    - `T8`
- next-family boundary at Stage16 mix-control:
  - parent tension `T9`
  - parent candidate `C6`

## Explicit exclusions
- no raw-doc reread
- no fresh `core_docs` pass beyond the already-intaken parent batch
- no merge with `run_stage16_axis6_mix_control.py`
- no promotion to A2-1 or A1
- no runtime execution or result regeneration

## Reduced output target
- preserve only the smallest reusable `sim_suite_v2` packets:
  - successor-bundle identity
  - externalized provenance rule
  - dedicated-runner externalization trio
  - operator4 predecessor crossover
  - Stage16 V5 drift packet
  - Negctrl anomaly packet

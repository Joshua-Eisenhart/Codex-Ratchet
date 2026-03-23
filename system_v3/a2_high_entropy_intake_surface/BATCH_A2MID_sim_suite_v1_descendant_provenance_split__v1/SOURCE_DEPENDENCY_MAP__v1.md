# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / SOURCE-LINKED REDUCTION MAP
Batch: `BATCH_A2MID_sim_suite_v1_descendant_provenance_split__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Parent batch
- `BATCH_sims_sim_suite_v1_descendant_bundle__v1`

## Parent artifacts used directly
- `MANIFEST.json`
- `SOURCE_MAP__v1.md`
- `SIM_CLUSTER_MAP__v1.md`
- `TENSION_MAP__v1.md`
- `A2_3_SIM_DISTILLATES__v1.md`
- `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md`

## Comparison anchors used
- `BATCH_A2MID_sims_evidence_boundary__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - reused for evidence-lane coverage and provenance-admission separation
- `BATCH_A2MID_oprole8_harness_descendant_seam__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - reused for the nearest current `run_sim_suite_v1.py` hash mismatch against a different current emitter path
- `BATCH_A2MID_axis4_directional_evidence_isolation__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - reused for the nearest Axis4 dedicated-lineage producer-path separation

## Dependency compression
### Parent seams retained
- one executable bundle emits ten descendants:
  - parent cluster `A`
  - parent distillate `D1`
  - parent candidates:
    - `C1`
    - `C2`
- full repo-top evidence coverage with mixed current provenance:
  - parent distillate `D2`
  - parent tension `T1`
- aligned four-descendant subset:
  - parent cluster `B`
  - parent distillate `D3`
  - parent tension `T2`
- migrated six-descendant subset:
  - parent cluster `C`
  - parent distillate `D4`
  - parent tensions:
    - `T3`
    - `T4`
    - `T5`
- Stage16 version-label drift with payload identity:
  - parent cluster `C`
  - parent tension `T6`
- Negctrl successor-hash crossover:
  - parent clusters:
    - `C`
    - `D`
  - parent tension `T7`
- adjacent successor-bundle boundary:
  - parent cluster `D`
  - parent distillate `D6`
  - parent candidates:
    - `C5`
    - `C6`
  - parent tension `T8`

## Explicit exclusions
- no raw-doc reread
- no fresh `core_docs` pass beyond the already-intaken parent batch
- no merge with `run_sim_suite_v2_full_axes.py`
- no promotion to A2-1 or A1
- no runtime execution or result regeneration

## Reduced output target
- preserve only the smallest reusable `sim_suite_v1` packets:
  - bundle identity
  - full coverage plus split provenance
  - aligned subset versus migrated subset
  - Stage16 version/payload drift
  - Negctrl crossover drift
  - successor-bundle boundary

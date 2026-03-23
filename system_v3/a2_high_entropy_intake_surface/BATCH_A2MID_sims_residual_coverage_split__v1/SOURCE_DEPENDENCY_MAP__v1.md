# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID SOURCE DEPENDENCY MAP
Batch: `BATCH_A2MID_sims_residual_coverage_split__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## 1) Parent Batch
- parent batch:
  - `BATCH_sims_residual_inventory_closure_audit__v1`
- parent artifacts used:
  - `SOURCE_MAP__v1.md`
  - `SIM_CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_SIM_DISTILLATES__v1.md`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md`
  - `MANIFEST.json`
- parent role in this reduction:
  - provides the closure-audit frame after raw-order `simpy/` exhaustion
  - keeps the residual class counts source-bound
  - separates paired backlog, anchor-only reuse, orphan surfaces, and hygiene residue without rereading raw sims files

## 2) Comparison Anchors
- comparison anchor:
  - `BATCH_A2MID_ultra_sweep_terminal_exhaustion__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - role:
    - supplies the terminal raw-order exhaustion packet used here as the handoff boundary into residual work
- comparison anchor:
  - `BATCH_A2MID_sims_evidence_boundary__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - role:
    - supplies the three-layer catalog / evidence / source-class separation pattern reused here at residual-closure scale
- comparison anchor:
  - `BATCH_A2MID_sim_suite_v1_descendant_provenance_split__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - role:
    - supplies the strongest already-refined pattern for keeping descendant evidence or comparison reuse weaker than clean current direct-source attribution

## 3) Candidate Dependency Map
### RC1) `RAW_ORDER_EXHAUSTION_NOT_FULL_COVERAGE_RULE`
- parent dependencies:
  - cross-cluster read
  - distillate `D1`
  - candidate summary `C1`
  - tension `T1`
- comparison anchor dependencies:
  - `BATCH_A2MID_ultra_sweep_terminal_exhaustion__v1:RC6`

### RC2) `DIRECT_SOURCE_MEMBERSHIP_OVER_COMPARISON_REUSE_RULE`
- parent dependencies:
  - cluster `B`
  - distillate `D3`
  - candidate summary `C4`
  - tension `T2`
- comparison anchor dependencies:
  - `BATCH_A2MID_sim_suite_v1_descendant_provenance_split__v1:RC2`

### RC3) `PAIRED_RESIDUAL_BACKLOG_PRIORITY_RULE`
- parent dependencies:
  - cluster `C`
  - distillate `D2`
  - candidate summary `C3`
  - tension `T3`

### RC4) `NONPAIRED_RESIDUAL_REBOUND_RULE`
- parent dependencies:
  - clusters:
    - `D`
    - `E`
  - distillates:
    - `D5`
    - `D6`
  - candidate summary `C5`
  - tensions:
    - `T4`
    - `T6`
    - `T7`

### RC5) `CATALOG_EVIDENCE_SOURCE_VISIBILITY_TRIAD_RULE`
- parent dependencies:
  - cluster `A`
  - distillate `D4`
  - tension `T5`
- comparison anchor dependencies:
  - `BATCH_A2MID_sims_evidence_boundary__v1:RC1`
  - `BATCH_A2MID_sims_evidence_boundary__v1:RC2`
  - `BATCH_A2MID_sims_evidence_boundary__v1:RC3`

### RC6) `POST_RAW_ORDER_WORK_IS_RESIDUAL_PRIORITIZATION_RULE`
- parent dependencies:
  - cross-cluster read
  - distillate `D5`
  - candidate summary `C6`
  - tension `T1`

## 4) Quarantine Dependency Map
### Q1) `RAW_ORDER_EXHAUSTION_AS_FULL_SIMS_COVERAGE`
- parent dependencies:
  - distillate `D1`
  - tension `T1`

### Q2) `COMPARISON_REUSE_AS_DIRECT_SOURCE_COVERAGE`
- parent dependencies:
  - distillate `D3`
  - candidate summary `C4`
  - tension `T2`

### Q3) `ALL_RESIDUAL_ARTIFACTS_AS_CLEAN_PAIRED_FAMILIES`
- parent dependencies:
  - clusters:
    - `C`
    - `D`
    - `E`
  - candidate summary `C5`
  - tensions:
    - `T3`
    - `T4`
    - `T6`
    - `T7`

### Q4) `CATALOG_OR_EVIDENCE_VISIBILITY_AS_LOCAL_FAMILY_COVERAGE`
- parent dependencies:
  - distillate `D4`
  - tension `T5`

### Q5) `MORE_RAW_ORDER_SIMPY_CONTINUATION_REMAINS`
- parent dependencies:
  - distillate `D5`
  - candidate summary `C6`
  - tension `T1`

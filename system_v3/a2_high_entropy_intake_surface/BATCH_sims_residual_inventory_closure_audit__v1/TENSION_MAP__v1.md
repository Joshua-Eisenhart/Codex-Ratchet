# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_residual_inventory_closure_audit__v1`
Extraction mode: `SIM_RESIDUAL_CLOSURE_AUDIT_PASS`

## T1) Raw-order `simpy` family intake is exhausted, but sims-side source coverage is not
- source markers:
  - `BATCH_sims_ultra_axis0_ab_axis6_sweep_family__v1/MANIFEST.json`
  - filename inventory across `sims`, `simpy`, and `simson`
- tension:
  - the prior ultra sweep batch already established that `run_ultra_axis0_ab_axis6_sweep.py` is `51 / 51` in raw `simpy` order
  - the current closure audit still finds `44` sims-side files that never became direct source members
- preserved read:
  - raw-order family completion is not the same as full sims inventory coverage
- possible downstream consequence:
  - future residual work should be framed as backlog prioritization, not as continuation of raw-order intake

## T2) Some residual runners already shaped earlier bundle batches as comparison anchors, but they still never became source members
- source markers:
  - `BATCH_sims_sim_suite_v1_descendant_bundle__v1/MANIFEST.json:32-40`
  - `BATCH_sims_sim_suite_v2_successor_bundle__v1/MANIFEST.json:31-39`
- tension:
  - earlier suite batches comparison-read:
    - `run_axis0_traj_corr_suite.py`
    - `run_axis12_channel_realization_suite.py`
    - `run_axis12_seq_constraints.py`
    - `run_axis12_topology4_channelfamily_suite_v2.py`
  - those same runners still remain outside direct source membership
- preserved read:
  - comparison reuse and source membership must stay distinct
- possible downstream consequence:
  - future residual intake should not assume these four families are already fully covered

## T3) Twelve direct runner/result pairs still exist outside source membership
- source markers:
  - filename inventory across `simpy` and `simson`
  - `SIM_CATALOG_v1.3.md:43-50,60-69,75-76,135-138`
- tension:
  - `12` residual families still have both a runner and a paired result surface present in the repo
  - several are catalog-visible, yet none entered direct source membership in the finished raw-order campaign
- preserved read:
  - keep these paired families visible as backlog rather than smoothing them into the claim that sims intake is finished
- possible downstream consequence:
  - if residual family work resumes, these pairs are the cleanest place to restart

## T4) Ten result-only residual surfaces remain without a residual runner pair
- source markers:
  - filename inventory across `simson`
  - `SIM_CATALOG_v1.3.md:43,51-52,60-66,116,118`
- tension:
  - the residual set still includes result-only surfaces such as:
    - `results_axis0_boundary_bookkeep_v1.json`
    - `results_axis0_traj_corr_suite_v2.json`
    - `results_axis12_altchan_v1.json`
    - `results_ultra_big_ax012346.json`
  - these files are inventory-real but not currently cleanly pairable inside the residual set
- preserved read:
  - keep orphan result presence distinct from family-level extraction completeness
- possible downstream consequence:
  - later work should not over-interpret orphan results without rebounding them first

## T5) Catalog visibility is broader than source-membership coverage, and evidence-pack visibility is narrower than both
- source markers:
  - `SIM_CATALOG_v1.3.md:43-69,116,118,135-138`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:2-54,89`
- tension:
  - the catalog names many residual local families and runners
  - the evidence pack instead foregrounds descendant or renamed surfaces such as:
    - `S_SIM_AXIS0_TRAJ_CORR_SUITE_V4`
    - `S_SIM_AXIS0_TRAJ_CORR_SUITE_V5`
    - `S_SIM_AXIS12_CHANNEL_REALIZATION_V4`
    - `S_SIM_AXIS12_SEQ_CONSTRAINTS_V2`
    - `S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1`
- preserved read:
  - keep catalog presence, evidence-pack presence, and direct source membership as three separate visibility layers
- possible downstream consequence:
  - later priority decisions should not mistake evidence-pack admission for full local-family coverage

## T6) The sims tree contains hygiene artifacts that can be mistaken for meaningful intake residue
- source markers:
  - filename inventory across top-level `sims` and `simpy/__pycache__`
- tension:
  - `.DS_Store` and `3` committed `__pycache__` files are still inside the sims tree
  - those files are residual inventory, but not sim-family evidence
- preserved read:
  - keep filesystem noise distinct from executable or result surfaces
- possible downstream consequence:
  - future audits should not inflate residual family counts by treating noise as a source class

## T7) Diagnostic and proof scripts share the sims namespace, but their intake status is unresolved
- source markers:
  - filename inventory across `simpy`
  - negative residual pair check for:
    - `mega_sims_failure_detector.py`
    - `mega_sims_run_02.py`
    - `mega_sims_trivial_check.py`
    - `prove_foundation.py`
- tension:
  - these scripts exist inside `simpy`
  - none currently presents as a clean residual runner/result pair
  - none has been source-batched in the finished raw-order campaign
- preserved read:
  - keep diagnostic or proof residue separate from ordinary sim-family extraction
- possible downstream consequence:
  - any later treatment of these scripts should be a deliberate special-case audit, not silent inclusion in family counts

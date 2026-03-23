# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_stage16_sub4_axis6u_absolute_surface__v1`
Extraction mode: `SIM_STAGE16_SUB4_AXIS6U_ABSOLUTE_PASS`

## T1) The current local Stage16 SIM_ID exists, but the repo-held top-level evidence pack omits it
- source markers:
  - `run_stage16_sub4_axis6u.py:1-228`
  - negative search for `S_SIM_STAGE16_SUB4_AXIS6U` in `SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:336-414`
- tension:
  - the current runner writes local evidence for `S_SIM_STAGE16_SUB4_AXIS6U`
  - the repo-held top-level pack instead admits:
    - `S_SIM_STAGE16_SUB4_AXIS6_UNIFORM_V4`
    - `S_SIM_STAGE16_SUB4_UNIFORM_AXIS6_V5`
- preserved read:
  - keep local-writer existence distinct from repo-top evidence admission
- possible downstream consequence:
  - this batch should stay proposal-side in provenance strength

## T2) The current Stage16 result and the top-level V4 / V5 descendants share the stage lattice but not the same output contract
- source markers:
  - `results_stage16_sub4_axis6u.json:1-168`
  - `results_S_SIM_STAGE16_SUB4_AXIS6_UNIFORM_V4.json:1-50`
  - `results_S_SIM_STAGE16_SUB4_UNIFORM_AXIS6_V5.json:1-50`
- tension:
  - the current result stores absolute `vn_entropy_mean` / `purity_mean` values plus minima and maxima
  - the V4 / V5 descendants store only `dS` / `dP` deltas
  - V4 and V5 are byte-identical to each other but are not the current local result surface
- preserved read:
  - do not collapse these three surfaces into one equivalent Stage16 artifact
- possible downstream consequence:
  - later Stage16 summaries should separate absolute baselines from delta descendants

## T3) `stage16_sub4_axis6u` matches the control baseline up to floating-point noise, but it is still a separate bounded family
- source markers:
  - `results_stage16_sub4_axis6u.json:1-168`
  - `results_stage16_axis6_mix_control.json:1-166`
- tension:
  - all `16` cells align with the control `U_Smean` / `U_Pmean` baseline values up to floating-point noise
  - only `3` cells differ at all, and the maximum absolute difference is `1.1102230246251565e-16`
  - the current surface remains an absolute baseline result, not a mixed comparison
- preserved read:
  - keep baseline identity separate from family identity
- possible downstream consequence:
  - later mixed-axis6 interpretation can cite this batch as the baseline anchor without merging the families

## T4) Catalog grouping is broader than evidence-pack admission
- source markers:
  - `SIM_CATALOG_v1.3.md:104-146`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:336-414`
- tension:
  - the catalog lists:
    - the current `stage16_sub4_axis6u`
    - the V4 / V5 descendants
    - the adjacent `terrain8_sign_suite`
  - the evidence pack admits only the V4 / V5 descendants among those Stage16-local relatives
- preserved read:
  - keep catalog visibility distinct from evidence-pack visibility
- possible downstream consequence:
  - batch promotion should continue to follow evidence strength, not catalog co-location

## T5) Raw-order adjacency to `terrain8_sign_suite` does not imply a shared family
- source markers:
  - `run_stage16_sub4_axis6u.py:1-228`
  - `run_terrain8_sign_suite.py:1-137`
  - `results_terrain8_sign_suite.json:1-20`
- tension:
  - `stage16_sub4_axis6u` is a `16`-cell Stage16 absolute lattice with outer / inner loops and operators
  - `terrain8_sign_suite` is an `8`-metric sign-by-terrain sweep with `256` states and `64` cycles
- preserved read:
  - the terrain-only suite begins the next bounded family
- possible downstream consequence:
  - the next batch should start at `run_terrain8_sign_suite.py`

## T6) The strongest terrain-only sign gap sits in `Ni`, but that signal does not belong inside the current Stage16 batch
- source markers:
  - `results_terrain8_sign_suite.json:1-20`
- tension:
  - the adjacent terrain suite already shows its own sign asymmetry:
    - `Ni` entropy gap `= 0.001752965040475507`
    - `Si` entropy gap `= 0.00113301080489836`
  - those metrics are not Stage16 outer / inner cell metrics
- preserved read:
  - keep the terrain-only sign asymmetry quarantined to the next family
- possible downstream consequence:
  - later summaries should not treat these terrain-only deltas as Stage16 cell behavior

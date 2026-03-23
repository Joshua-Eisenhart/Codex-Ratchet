# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_axis0_mi_discrim_branches_family__v1`
Extraction mode: `SIM_AXIS0_MI_DISCRIM_BRANCHES_PASS`
Batch scope: standalone residual axis0 branch-discriminator family centered on `run_axis0_mi_discrim_branches.py` and `results_axis0_mi_discrim_branches.json`, with top-level visibility, residual continuity, and the adjacent `_ab` branch held comparison-only
Date: 2026-03-09

## 1) Batch Selection
- starting residual-priority source:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_mi_discrim_branches.py`
- selected sources:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_mi_discrim_branches.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_mi_discrim_branches.json`
- reason for bounded family:
  - the prior residual paired-family batch deferred this pair as the next clean runner/result unit
  - one runner emits one paired result surface with one local SIM_ID
  - the adjacent `_ab` sibling changes the executable contract by adding explicit AB coupling and therefore starts the next bounded family
- comparison-only anchors read:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_mi_discrim_branches_ab.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_mi_discrim_branches_ab.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis0_historyop_rec_suite_v1_family__v1/MANIFEST.json`
- deferred next residual-priority source:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_mi_discrim_branches_ab.py`

## 2) Source Membership
- Runner:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_mi_discrim_branches.py`
  - sha256: `49338bbe6f69d03f7ee5ffaa5bae9e78a22f2ae8ebd9670652342c512a1d6d92`
  - size bytes: `7290`
  - line count: `227`
  - source role: non-AB axis0 MI discriminator runner
- Result surface:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_mi_discrim_branches.json`
  - sha256: `72ed211fa667e98520eab3c600a7f28f49b44adb5709f1c053cb45c4107db244`
  - size bytes: `998`
  - line count: `48`
  - source role: compact two-branch discriminator result surface

## 3) Structural Map Of The Family
### Runner contract: `run_axis0_mi_discrim_branches.py`
- anchors:
  - `run_axis0_mi_discrim_branches.py:1-227`
- source role:
  - one axis0 branch discriminator runner comparing:
    - `SEQ01 = [Se, Ne, Ni, Si]`
    - `SEQ02 = [Se, Si, Ni, Ne]`
  - fixed runtime parameters:
    - seed `0`
    - trials `512`
    - cycles `64`
    - axis3 sign `+1`
    - theta `0.07`
    - n-vector `(0.3, 0.4, 0.866025403784)`
    - terrain params `{gamma: 0.12, p: 0.08, q: 0.10}`
  - applies:
    - local axis unitary on `A`
    - terrain CPTP map on `A` only
  - does not apply any explicit AB entangler
  - emits one local SIM_ID:
    - `S_SIM_AXIS0_MI_DISCRIM_BRANCHES`

### Result structure: `results_axis0_mi_discrim_branches.json`
- top-level shape:
  - one compact result surface with:
    - `metrics_SEQ01`
    - `metrics_SEQ02`
    - `delta_MI_mean_SEQ02_minus_SEQ01`
    - `delta_SAgB_mean_SEQ02_minus_SEQ01`
- strongest bounded metrics:
  - `metrics_SEQ01.MI_mean = -2.190088388420719e-17`
  - `metrics_SEQ02.MI_mean = -1.9949319973733282e-17`
  - `delta_MI_mean_SEQ02_minus_SEQ01 = 1.951563910473908e-18`
  - `delta_SAgB_mean_SEQ02_minus_SEQ01 = -0.002669220066020328`
  - `metrics_SEQ01.neg_SAgB_frac = 0.0`
  - `metrics_SEQ02.neg_SAgB_frac = 0.0`
- bounded implication:
  - the stored branch difference is carried by `SAgB`, not by any materially nonzero MI split
  - stored MI remains at machine-zero scale across both branches

### Boundary to the `_ab` sibling
- comparison anchors:
  - `run_axis0_mi_discrim_branches_ab.py:1-236`
  - `results_axis0_mi_discrim_branches_ab.json:1-49`
- bounded comparison read:
  - the `_ab` sibling inserts explicit AB coupling:
    - `rho = apply_unitary_AB(rho, CNOT)`
  - that sibling produces materially nonzero stored MI:
    - `metrics_SEQ01.MI_mean = 0.005174869538448677`
    - `metrics_SEQ02.MI_mean = 0.005913066231490261`
    - `delta_MI_mean_SEQ02_minus_SEQ01 = 0.0007381966930415842`
  - the current non-AB family instead keeps MI at machine-zero scale
  - the sibling therefore begins the next bounded family instead of being merged here

### Top-level visibility relation
- comparison anchors:
  - `SIM_CATALOG_v1.3.md:45-46`
  - negative search for `axis0_mi_discrim_branches` and `S_SIM_AXIS0_MI_DISCRIM_BRANCHES` in `SIM_EVIDENCE_PACK_autogen_v2.txt`
- bounded read:
  - the catalog lists both:
    - `axis0_mi_discrim_branches`
    - `axis0_mi_discrim_branches_ab`
  - the repo-held top-level evidence pack contains no current block for the non-AB local SIM_ID
  - this leaves the family catalog-visible and locally evidenced, but not repo-top admitted

## 4) Comparison Anchors
- comparison sources:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_mi_discrim_branches_ab.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_mi_discrim_branches_ab.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis0_historyop_rec_suite_v1_family__v1/MANIFEST.json`
- relevant anchors:
  - `SIM_CATALOG_v1.3.md:45-46`
  - `BATCH_sims_axis0_historyop_rec_suite_v1_family__v1/MANIFEST.json`
- bounded comparison read:
  - the prior residual paired-family batch set this pair as next in queue
  - the catalog confirms the current file and the `_ab` sibling are both first-class sims artifacts
  - the `_ab` sibling is similar enough to matter for boundary setting, but different enough in contract to remain out of batch

## 5) Source-Class Read
- Best classification:
  - standalone non-AB axis0 discriminator family with one compact local SIM_ID surface
- Not best classified as:
  - a successful MI discriminator in the stored non-AB form
  - the same bounded family as the `_ab` sibling
  - repo-top evidenced surface
- Theory-facing vs executable-facing split:
  - executable-facing:
    - current runner is strictly A-local in its repeated update loop
  - theory-facing:
    - current stored branch split appears in `SAgB` while MI stays effectively zero
  - evidence-facing:
    - local evidence is explicit in the runner contract
    - repo-top evidence-pack admission is absent
- possible downstream consequence:
  - later residual intake should treat the current file as the non-AB control branch family and let the `_ab` sibling start the next bounded family

# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_axis0_mi_discrim_branches_ab_family__v1`
Extraction mode: `SIM_AXIS0_MI_DISCRIM_BRANCHES_AB_PASS`
Batch scope: standalone residual axis0 AB-coupled branch-discriminator family centered on `run_axis0_mi_discrim_branches_ab.py` and `results_axis0_mi_discrim_branches_ab.json`, with top-level visibility, prior non-AB sibling, and residual continuity held comparison-only
Date: 2026-03-09

## 1) Batch Selection
- starting residual-priority source:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_mi_discrim_branches_ab.py`
- selected sources:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_mi_discrim_branches_ab.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_mi_discrim_branches_ab.json`
- reason for bounded family:
  - the prior non-AB batch deferred this pair as the next clean residual runner/result unit
  - one runner emits one paired result surface with one local SIM_ID
  - the current runner adds explicit AB coupling and therefore deserves its own bounded family rather than being collapsed into the prior non-AB control batch
- comparison-only anchors read:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_mi_discrim_branches.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_mi_discrim_branches.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis0_mi_discrim_branches_family__v1/MANIFEST.json`
- deferred next residual-priority source:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_mutual_info.py`

## 2) Source Membership
- Runner:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_mi_discrim_branches_ab.py`
  - sha256: `31bc04df3228af340cc357f8af21119c6e84cd1e9c843178438a77cdb41cb23d`
  - size bytes: `7710`
  - line count: `236`
  - source role: AB-coupled axis0 MI discriminator runner
- Result surface:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_mi_discrim_branches_ab.json`
  - sha256: `8f09e92293fb2f5e55c7f802e021174bd500cac7c7ad9f6e20484790b8214428`
  - size bytes: `1030`
  - line count: `49`
  - source role: compact two-branch AB discriminator result surface

## 3) Structural Map Of The Family
### Runner contract: `run_axis0_mi_discrim_branches_ab.py`
- anchors:
  - `run_axis0_mi_discrim_branches_ab.py:1-236`
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
    - explicit AB coupling:
      - `rho = apply_unitary_AB(rho, CNOT)`
  - the runner even labels that insertion as:
    - `# <-- AB coupling (the fix)`
  - emits one local SIM_ID:
    - `S_SIM_AXIS0_MI_DISCRIM_BRANCHES_AB`

### Result structure: `results_axis0_mi_discrim_branches_ab.json`
- top-level shape:
  - one compact result surface with:
    - `metrics_SEQ01`
    - `metrics_SEQ02`
    - `delta_MI_mean_SEQ02_minus_SEQ01`
    - `delta_SAgB_mean_SEQ02_minus_SEQ01`
    - `delta_negfrac_SEQ02_minus_SEQ01`
- strongest bounded metrics:
  - `metrics_SEQ01.MI_mean = 0.005174869538448677`
  - `metrics_SEQ02.MI_mean = 0.005913066231490261`
  - `delta_MI_mean_SEQ02_minus_SEQ01 = 0.0007381966930415842`
  - `delta_SAgB_mean_SEQ02_minus_SEQ01 = -0.0013163402139951819`
  - `delta_negfrac_SEQ02_minus_SEQ01 = 0.0`
  - `metrics_SEQ01.neg_SAgB_frac = 0.0`
  - `metrics_SEQ02.neg_SAgB_frac = 0.0`
- bounded implication:
  - explicit AB coupling revives a real, stored MI branch split
  - the family still does not generate any stored negative conditional-entropy fraction

### Relation to the prior non-AB sibling
- comparison anchors:
  - `run_axis0_mi_discrim_branches.py:1-227`
  - `results_axis0_mi_discrim_branches.json:1-48`
  - `BATCH_sims_axis0_mi_discrim_branches_family__v1/MANIFEST.json`
- bounded comparison read:
  - the prior non-AB family kept MI at machine-zero scale:
    - `SEQ01.MI_mean = -2.190088388420719e-17`
    - `SEQ02.MI_mean = -1.9949319973733282e-17`
    - `delta_MI_mean_SEQ02_minus_SEQ01 = 1.951563910473908e-18`
  - the current AB family increases stored MI by:
    - `SEQ01` gain over non-AB `= 0.005174869538448698`
    - `SEQ02` gain over non-AB `= 0.005913066231490281`
    - delta-MI gain over non-AB `= 0.0007381966930415822`
  - the current AB family also attenuates the absolute `SAgB` branch split relative to non-AB:
    - shift vs non-AB `= 0.0013528798520251462`
  - the sibling relation is therefore real but non-equivalent

### Top-level visibility relation
- comparison anchors:
  - `SIM_CATALOG_v1.3.md:46`
  - negative search for `axis0_mi_discrim_branches_ab` and `S_SIM_AXIS0_MI_DISCRIM_BRANCHES_AB` in `SIM_EVIDENCE_PACK_autogen_v2.txt`
- bounded read:
  - the catalog lists the AB family result surface
  - the repo-held top-level evidence pack contains no current block for the AB local SIM_ID
  - this leaves the family catalog-visible and locally evidenced, but not repo-top admitted

## 4) Comparison Anchors
- comparison sources:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_mi_discrim_branches.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_mi_discrim_branches.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis0_mi_discrim_branches_family__v1/MANIFEST.json`
- relevant anchors:
  - `SIM_CATALOG_v1.3.md:46`
  - `BATCH_sims_axis0_mi_discrim_branches_family__v1/MANIFEST.json`
- bounded comparison read:
  - the prior residual paired-family batch set this pair as next in queue
  - the catalog confirms the family is a first-class sims artifact
  - the prior non-AB sibling is the correct comparison boundary, not a merge target

## 5) Source-Class Read
- Best classification:
  - standalone AB-coupled axis0 discriminator family with one compact local SIM_ID surface
- Not best classified as:
  - repo-top evidenced surface
  - the same bounded family as the prior non-AB control branch
  - a negativity-producing family
- Theory-facing vs executable-facing split:
  - executable-facing:
    - current runner is the same branch shell as the non-AB sibling plus explicit `CNOT` coupling
  - theory-facing:
    - AB coupling turns on a real MI branch signal while softening the `SAgB` branch split
  - evidence-facing:
    - local evidence is explicit in the runner contract
    - repo-top evidence-pack admission is absent
- possible downstream consequence:
  - later residual intake should treat this family as the AB-coupled successor to the non-AB control branch family and let `run_axis0_mutual_info.py` begin the next bounded pair

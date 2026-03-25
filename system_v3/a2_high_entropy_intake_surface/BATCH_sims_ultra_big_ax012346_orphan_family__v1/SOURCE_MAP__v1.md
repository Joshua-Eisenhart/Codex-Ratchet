# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_ultra_big_ax012346_orphan_family__v1`
Extraction mode: `SIM_ULTRA_BIG_AX012346_ORPHAN_PASS`
Batch scope: residual result-only ultra-big orphan centered on `results_ultra_big_ax012346.json`, compared against the prior ultra3 orphan and the residual closure audit without merging it into earlier ultra strip families
Date: 2026-03-09

## 1) Batch Selection
- starting residual-priority source:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra_big_ax012346.json`
- selected sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra_big_ax012346.json`
- reason for bounded family:
  - the prior ultra3 orphan batch explicitly deferred this surface next
  - the current orphan has its own macro contract:
    - `axis0_params`
    - `axis0_traj_metrics`
    - `topology4_metrics`
    - `SEQ01` and `SEQ02` only
  - repo-local comparison shows it is not the same family as the ultra3 geometry/stage16 orphan
  - the residual closure audit listed this as the final remaining result-only orphan surface
- comparison-only anchors read:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_ultra3_full_geometry_stage16_axis0_orphan_family__v1/MANIFEST.json`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_residual_inventory_closure_audit__v1/MANIFEST.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_INDEX__v1.md`
- deferred next residual-priority source:
  - diagnostic/proof residue beginning at `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/mega_sims_failure_detector.py`

## 2) Source Membership
- Result surface:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra_big_ax012346.json`
  - sha256: `4426aeee0da8231679b4699202e572d5bc6cb29793c3647af802a5ab14ba6e9f`
  - size bytes: `8997`
  - line count: `305`
  - source role: compact ultra-big result-only orphan combining axis0 trajectory summaries with topology4 summary metrics

## 3) Structural Map Of The Family
### Result structure: `results_ultra_big_ax012346.json`
- anchors:
  - `results_ultra_big_ax012346.json:1-305`
- source role:
  - one compact macro result surface with:
    - `axis0_params`
    - `axis0_traj_metrics`
    - `topology4_metrics`
    - `k_list`
    - `p0_list`
    - `seeds`
  - bounded counts:
    - `axis0_traj_metrics` branch count = `4`
    - `topology4_metrics` branch count = `4`
    - sequence count = `2`
    - seed count = `8`
    - `axis0_cycles = 128`
    - `axis0_trials = 96`
    - `entangle_reps = 2`
    - `num_states = 65536`
    - `lin_trials = 4096`
- bounded implication:
  - the current orphan is a compact two-sequence trajectory-plus-topology macro surface, not a stage16 or berry-flux ultra surface

### Axis0 parameter layer
- anchors:
  - `results_ultra_big_ax012346.json:1-305`
- bounded read:
  - only two sequences are stored:
    - `SEQ01 = [Se, Ne, Ni, Si]`
    - `SEQ02 = [Se, Si, Ni, Ne]`
  - terrain parameters are fixed:
    - `gamma = 0.01`
    - `p = 0.01`
    - `q = 0.01`
- bounded implication:
  - the current orphan is built around one two-sequence contrast rather than a four-sequence lattice

### Axis0 trajectory branch
- anchors:
  - `results_ultra_big_ax012346.json:1-305`
- bounded read:
  - branch keys are:
    - `sign-1_ent0`
    - `sign-1_ent1`
    - `sign1_ent0`
    - `sign1_ent1`
  - strongest stored Bell mean case is:
    - `sign1_ent1 / SEQ02 / BELL`
    - `MI_mean = 0.14992355527789028`
    - `negfrac_mean = 0.068359375`
  - under `sign1`, `SEQ02 - SEQ01` for Bell is stable across entanglement repeats:
    - `dMI_mean = 0.002251349097335875`
    - `dSAgB_mean = -0.0027451465467724923`
    - `dnegfrac_mean = 0.001953125`
  - Bell stays negative-fraction-active while Ginibre stays at zero negativity throughout the stored surface
- bounded implication:
  - the main stored sequence split sits in Bell metrics, not in any large sign or repeat effect

### Entanglement-repeat seam
- anchors:
  - `results_ultra_big_ax012346.json:1-305`
- bounded read:
  - the file declares `entangle_reps = 2`
  - `ent0` and `ent1` are effectively identical to machine precision:
    - max absolute metric difference for `sign-1` = `3.469446951953614e-17`
    - max absolute metric difference for `sign1` = `1.1102230246251565e-16`
- bounded implication:
  - the repeat axis is declared in metadata but nearly invisible in the stored results

### Sign seam
- anchors:
  - `results_ultra_big_ax012346.json:1-305`
- bounded read:
  - for `SEQ02 / BELL`, `sign1 - sign-1` is tiny and stable across entanglement repeats:
    - `dMI_mean = 3.584325813296707e-05`
    - `dSAgB_mean = -0.0005204740469357816`
    - `dnegfrac_mean = 0.0`
- bounded implication:
  - the stored sign effect is real but much smaller than the stored sequence effect

### Topology4 branch
- anchors:
  - `results_ultra_big_ax012346.json:1-305`
- bounded read:
  - branch keys are:
    - `EC_AD`
    - `EC_FX`
    - `EO_AD`
    - `EO_FX`
  - adaptive families carry the only nontrivial linearity error:
    - `EC_AD.lin_err_mean = 0.014091694511819554`
    - `EO_AD.lin_err_mean = 0.0075609087008042045`
  - fixed families are effectively linear:
    - `EC_FX.lin_err_mean = 3.004368099334242e-16`
    - `EO_FX.lin_err_mean = 3.0489084424395665e-16`
  - even inside this split, control-axis behavior diverges:
    - `EC_*` commuting control deltaH stays near zero
    - `EO_*` commuting control deltaH stays materially nonzero
- bounded implication:
  - the topology4 branch is not a single homogeneous proof layer; it preserves both adaptive-vs-fixed and EC-vs-EO splits

### Separation from the prior ultra3 orphan
- comparison anchors:
  - `BATCH_sims_ultra3_full_geometry_stage16_axis0_orphan_family__v1/MANIFEST.json`
- bounded read:
  - ultra3 has:
    - berry flux
    - `stage16`
    - `128` `axis0_ab` entries
    - `4` sequences
  - current orphan has:
    - no berry flux
    - no `stage16`
    - no `axis0_ab` map
    - `2` sequences
    - topology4 metrics instead
- bounded implication:
  - the current orphan should stay separate from the ultra3 seam family

### Visibility relation
- comparison anchors:
  - `SIM_CATALOG_v1.3.md:118`
  - negative search for `ultra_big` in `SIM_EVIDENCE_PACK_autogen_v2.txt`
  - negative runner-name search in current `simpy/`
- bounded read:
  - the catalog lists `ultra_big_ax012346`
  - the repo-held evidence pack omits it
  - no direct runner-name hit is recoverable in current `simpy/`
- bounded implication:
  - the orphan is catalog-visible by filename alias only and remains unadmitted at both the evidence-pack and direct-runner layers

## 4) Comparison Anchors
- comparison sources:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_ultra3_full_geometry_stage16_axis0_orphan_family__v1/MANIFEST.json`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_residual_inventory_closure_audit__v1/MANIFEST.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
- relevant anchors:
  - `BATCH_sims_ultra3_full_geometry_stage16_axis0_orphan_family__v1/MANIFEST.json`
  - `BATCH_sims_residual_inventory_closure_audit__v1/MANIFEST.json`
  - `SIM_CATALOG_v1.3.md:118`
- bounded comparison read:
  - the prior ultra3 batch explicitly kept this file separate
  - the closure audit identified this as the final unbatched result-only orphan
  - the current orphan closes the result-only residual class and leaves only diagnostic/proof and hygiene residue

## 5) Source-Class Read
- Best classification:
  - residual result-only ultra-big macro orphan with two-sequence axis0 trajectory summaries plus topology4 summary metrics
- Not best classified as:
  - the same family as ultra3
  - a stage16 or berry-flux ultra surface
  - a directly evidenced or directly runnable sim family
- Theory-facing vs executable-facing split:
  - executable-facing:
    - two-sequence axis0 contrast
    - four trajectory branches across sign and entanglement-repeat labels
    - four topology4 branches across EC/EO and AD/FX labels
  - theory-facing:
    - Bell carries the durable sequence split
    - entanglement-repeat labels are nearly inert at stored precision
    - adaptive topology4 families are the only nonlinear ones
  - evidence-facing:
    - catalog-visible by filename alias only
    - absent from the top-level evidence pack
    - no direct runner-name anchor recovered in current `simpy/`
- possible downstream consequence:
  - the next residual pass should leave result-only work and begin the diagnostic/proof residue starting with the `mega_sims_*` strip

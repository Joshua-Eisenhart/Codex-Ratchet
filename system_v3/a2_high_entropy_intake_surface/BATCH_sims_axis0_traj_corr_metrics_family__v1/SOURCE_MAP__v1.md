# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_axis0_traj_corr_metrics_family__v1`
Extraction mode: `SIM_AXIS0_TRAJ_CORR_METRICS_PASS`
Batch scope: standalone residual axis0 trajectory-correlation metrics family centered on `run_axis0_traj_corr_metrics.py` and `results_axis0_traj_corr_metrics.json`, with top-level visibility and residual-pair continuity preserved without merging the next suite family
Date: 2026-03-09

## 1) Batch Selection
- starting residual-priority source:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_traj_corr_metrics.py`
- selected sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_traj_corr_metrics.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_traj_corr_metrics.json`
- reason for bounded family:
  - the prior residual paired-family batch deferred this exact pair next
  - one runner emits one paired result surface with one local SIM_ID
  - the current family shifts from compact endpoint summaries to full-trajectory functionals and dual-init comparison, so it should stay separate from both the prior Bell-seed batch and the next suite batch
- comparison-only anchors read:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis0_sagb_entangle_seed_family__v1/MANIFEST.json`
- deferred next residual-priority source:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_traj_corr_suite.py`

## 2) Source Membership
- Runner:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_traj_corr_metrics.py`
  - sha256: `13b2fd6c2e539107f3a957e78d8ea97104f5cbeaa23ad88f835441f203aa5b76`
  - size bytes: `10511`
  - line count: `293`
  - source role: dual-init axis0 trajectory-correlation metric runner
- Result surface:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_traj_corr_metrics.json`
  - sha256: `83a3a84e8de1cc9bcfa51b5c1d5a1cdbc248c8cf91cff26bd03d17f67550e335`
  - size bytes: `2357`
  - line count: `77`
  - source role: compact dual-init trajectory-functional result surface

## 3) Structural Map Of The Family
### Runner contract: `run_axis0_traj_corr_metrics.py`
- anchors:
  - `run_axis0_traj_corr_metrics.py:157-212`
  - `run_axis0_traj_corr_metrics.py:214-288`
- source role:
  - one axis0 branch family comparing:
    - `SEQ01 = [Se, Ne, Ni, Si]`
    - `SEQ02 = [Se, Si, Ni, Ne]`
  - fixed runtime parameters:
    - seed `0`
    - trials `256`
    - cycles `64`
    - axis3 sign `+1`
    - theta `0.07`
    - n-vector `(0.3, 0.4, 0.866025403784)`
    - terrain params `{gamma: 0.02, p: 0.02, q: 0.02}`
    - entangle reps `1`
  - init contract:
    - one run covers both `GINIBRE` and `BELL`
  - tracked functionals:
    - `MI_traj_mean`
    - `MI_init_mean`
    - `MI_final_mean`
    - `MI_lambda_fit`
    - `SAgB_traj_mean`
    - `SAgB_init_mean`
    - `SAgB_final_mean`
    - `SAgB_neg_frac_traj`
  - emits one local SIM_ID:
    - `S_SIM_AXIS0_TRAJ_CORR_METRICS`

### Result structure: `results_axis0_traj_corr_metrics.json`
- top-level shape:
  - one compact result surface with:
    - `GINIBRE_SEQ01`
    - `GINIBRE_SEQ02`
    - `BELL_SEQ01`
    - `BELL_SEQ02`
    - four init-specific branch deltas
- strongest bounded metrics:
  - `BELL_SEQ01.MI_init_mean = 1.3862943611198788`
  - `BELL_SEQ01.SAgB_init_mean = -0.6931471805599333`
  - `BELL_SEQ01.SAgB_neg_frac_traj = 0.09753605769230769`
  - `BELL_SEQ02.SAgB_neg_frac_traj = 0.09723557692307692`
  - `GINIBRE_SEQ01.MI_init_mean = 0.27570814574973346`
  - `GINIBRE_SEQ01.SAgB_init_mean = 0.32673009003320846`
  - `GINIBRE_SEQ01.SAgB_neg_frac_traj = 0.0`
  - `GINIBRE_SEQ02.SAgB_neg_frac_traj = 0.0`
- bounded implication:
  - Bell initialization begins from maximally entangled negative-conditional-entropy space and preserves nonzero negativity incidence across the whole stored trajectory
  - Ginibre initialization begins from positive conditional entropy and keeps trajectory negativity at zero in both stored branches

### Dual-init trajectory split
- bounded read:
  - the family compares the same sequence pair under two init modes rather than one state-preparation regime
  - both modes decay to small final MI values and positive final `SAgB`, but their trajectory histories differ sharply
- strongest contrasts:
  - Bell:
    - `MI_traj_mean` near `0.199`
    - `SAgB_traj_mean` near `0.459`
    - negative-trajectory fraction near `0.097`
  - Ginibre:
    - `MI_traj_mean` near `0.043`
    - `SAgB_traj_mean` near `0.613`
    - negative-trajectory fraction exactly `0.0`

### Sequence-order deltas flip sign across init modes
- bounded read:
  - `BELL_delta_MI_traj_mean_SEQ02_minus_SEQ01 = -0.0004972841850615362`
  - `GINIBRE_delta_MI_traj_mean_SEQ02_minus_SEQ01 = 0.00017745381487310752`
  - `BELL_delta_SAgB_traj_mean_SEQ02_minus_SEQ01 = 0.00047040060007191853`
  - `GINIBRE_delta_SAgB_traj_mean_SEQ02_minus_SEQ01 = -0.00020947935777215765`
- bounded implication:
  - the direction of the sequence-order effect depends on initialization regime
  - branch-order claims should therefore stay init-qualified

### Final-state convergence vs trajectory negativity
- bounded read:
  - Bell final `SAgB` means are positive:
    - `SEQ01 = 0.6460960417722438`
    - `SEQ02 = 0.6460646351342514`
  - Ginibre final `SAgB` means are also positive:
    - `SEQ01 = 0.6488507737880436`
    - `SEQ02 = 0.6487357467902918`
  - only Bell stores nonzero `SAgB_neg_frac_traj`
- bounded implication:
  - stored trajectory negativity is not the same thing as negative final-state conditional entropy

### Top-level visibility relation
- comparison anchors:
  - `SIM_CATALOG_v1.3.md:50`
  - negative search for `axis0_traj_corr_metrics` and `S_SIM_AXIS0_TRAJ_CORR_METRICS` in `SIM_EVIDENCE_PACK_autogen_v2.txt`
- bounded read:
  - the catalog lists the trajectory-correlation metrics family
  - the repo-held top-level evidence pack contains no current block for the local SIM_ID
  - this leaves the family catalog-visible and locally evidenced, but not repo-top admitted

## 4) Comparison Anchors
- comparison sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis0_sagb_entangle_seed_family__v1/MANIFEST.json`
- relevant anchors:
  - `SIM_CATALOG_v1.3.md:50`
  - `BATCH_sims_axis0_sagb_entangle_seed_family__v1/MANIFEST.json`
- bounded comparison read:
  - the prior batch explicitly set this pair next
  - the current family widens from one fixed Bell-seed endpoint surface to a dual-init trajectory-functional surface
  - the next residual pair should therefore move to `run_axis0_traj_corr_suite.py` rather than merge that next family here

## 5) Source-Class Read
- Best classification:
  - standalone dual-init axis0 trajectory-correlation metrics family with one local SIM_ID surface
- Not best classified as:
  - a final-state negativity surface
  - a repo-top evidenced surface
  - a merged trajectory-suite family
- Theory-facing vs executable-facing split:
  - executable-facing:
    - current runner executes both `GINIBRE` and `BELL` init modes against the same branch pair
    - it tracks full-cycle time series and fits `MI_lambda_fit`
  - theory-facing:
    - Bell and Ginibre init modes produce materially different trajectory-negativity behavior
    - sequence-order effects are small and init-sensitive rather than globally signed
  - evidence-facing:
    - local evidence is explicit in the runner contract
    - repo-top evidence-pack admission is absent
- possible downstream consequence:
  - later residual intake should preserve this family as the trajectory-functional bridge between the fixed entangle-seed batch and the next `traj_corr_suite` family

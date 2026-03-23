# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_axis0_traj_corr_suite_family__v1`
Extraction mode: `SIM_AXIS0_TRAJ_CORR_SUITE_PASS`
Batch scope: standalone residual axis0 trajectory-correlation suite family centered on `run_axis0_traj_corr_suite.py` and `results_axis0_traj_corr_suite.json`, with descendant `V4/V5` compression seams preserved and the next axis12 residual pair held separate
Date: 2026-03-09

## 1) Batch Selection
- starting residual-priority source:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_traj_corr_suite.py`
- selected sources:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_traj_corr_suite.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_traj_corr_suite.json`
- reason for bounded family:
  - the prior residual paired-family batch deferred this exact pair next
  - one runner emits one paired result surface with one local SIM_ID
  - the current family expands from the prior two-sequence metrics surface to a four-sequence by sign by direction by init lattice and should stay separate from both the prior metrics batch and the repo-top `V4/V5` descendants
- comparison-only anchors read:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis0_traj_corr_metrics_family__v1/MANIFEST.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V4.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V5.json`
- deferred next residual-priority source:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_channel_realization_suite.py`

## 2) Source Membership
- Runner:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_traj_corr_suite.py`
  - sha256: `a42e220706a47d27283a332980398c35035e81efc7c188896ad388e5de5961bb`
  - size bytes: `9311`
  - line count: `271`
  - source role: signed directional axis0 trajectory-correlation suite runner
- Result surface:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_traj_corr_suite.json`
  - sha256: `694fc9a8edffa169b959ee585702379e5915d5ee91822d3b3aaadd681d6c652f`
  - size bytes: `12857`
  - line count: `364`
  - source role: 32-case trajectory-functional suite result surface

## 3) Structural Map Of The Family
### Runner contract: `run_axis0_traj_corr_suite.py`
- anchors:
  - `run_axis0_traj_corr_suite.py:150-268`
- source role:
  - one suite over four sequences:
    - `SEQ01 = [Se, Ne, Ni, Si]`
    - `SEQ02 = [Se, Si, Ni, Ne]`
    - `SEQ03 = [Se, Ne, Si, Ni]`
    - `SEQ04 = [Se, Si, Ne, Ni]`
  - fixed runtime parameters:
    - seed `0`
    - trials `128`
    - cycles `64`
    - theta `0.07`
    - n-vector `(0.3, 0.4, 0.866025403784)`
    - terrain params `{gamma: 0.02, p: 0.02, q: 0.02}`
    - entangle reps `1`
  - sweep axes:
    - `axis3_sign in {+1, -1}`
    - `init_mode in {GINIBRE, BELL}`
    - `direction in {FWD, REV}`
    - `sequence in {SEQ01, SEQ02, SEQ03, SEQ04}`
  - emits one local SIM_ID:
    - `S_SIM_AXIS0_TRAJ_CORR_SUITE`

### Result structure: `results_axis0_traj_corr_suite.json`
- top-level shape:
  - one compact suite result with:
    - fixed metadata
    - `seqs`
    - `results` containing `32` case keys
- strongest bounded extrema:
  - max stored `SAgB_neg_frac_traj`:
    - `sign-1_BELL_REV_SEQ04 = 0.14182692307692307`
  - max stored `MI_traj_mean`:
    - `sign1_BELL_REV_SEQ04 = 0.29728021483432243`
  - min stored `SAgB_traj_mean`:
    - `sign1_BELL_REV_SEQ04 = 0.358440136696848`
- bounded implication:
  - the suite is not approximately flat across sequence, sign, direction, and init mode
  - the strongest deviation sits in the `REV / BELL / SEQ04` corner

### Bell vs Ginibre suite split
- bounded read:
  - all stored Bell cases keep nonzero trajectory negativity
  - all stored Ginibre cases keep `SAgB_neg_frac_traj = 0.0`
- representative anchors:
  - `sign1_BELL_FWD_SEQ01.SAgB_neg_frac_traj = 0.09699519230769231`
  - `sign1_BELL_REV_SEQ04.SAgB_neg_frac_traj = 0.1373798076923077`
  - `sign1_GINIBRE_FWD_SEQ01.SAgB_neg_frac_traj = 0.0`
  - `sign-1_GINIBRE_REV_SEQ04.SAgB_neg_frac_traj = 0.0`
- bounded implication:
  - the suite keeps the init-regime split from the prior metrics batch, but now across the full 32-case lattice

### `SEQ04` flips behavior under direction in the Bell regime
- bounded read:
  - `sign1_BELL_FWD_SEQ04`:
    - `MI_traj_mean = 0.1470168871279225`
    - `SAgB_neg_frac_traj = 0.06995192307692308`
    - `SAgB_traj_mean = 0.5110568647917657`
  - `sign1_BELL_REV_SEQ04`:
    - `MI_traj_mean = 0.29728021483432243`
    - `SAgB_neg_frac_traj = 0.1373798076923077`
    - `SAgB_traj_mean = 0.358440136696848`
- bounded implication:
  - direction reversal turns `SEQ04` from a lower-MI / lower-negativity Bell case into the strongest stored Bell anomaly

### Evidence compression relation
- comparison anchors:
  - `run_axis0_traj_corr_suite.py:238-263`
  - `results_axis0_traj_corr_suite.json:1-364`
- bounded read:
  - the full result surface stores all `32` case metrics
  - the runner's local evidence block emits only `SEQ01`-relative deltas for `SEQ02`, `SEQ03`, and `SEQ04` under each sign/init/direction slice
- bounded implication:
  - the emitted evidence block is a compressed view of the suite, not the whole stored surface

### Top-level descendant relation
- comparison anchors:
  - `SIM_CATALOG_v1.3.md:39-40`
  - `SIM_CATALOG_v1.3.md:51-52`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:1-26`
  - `results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V4.json:1-17`
  - `results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V5.json:1-26`
- bounded read:
  - the repo-held top-level evidence pack contains:
    - `S_SIM_AXIS0_TRAJ_CORR_SUITE_V4`
    - `S_SIM_AXIS0_TRAJ_CORR_SUITE_V5`
  - both descendant evidence blocks carry the same code hash as the current runner:
    - `a42e220706a47d27283a332980398c35035e81efc7c188896ad388e5de5961bb`
  - the repo-held evidence pack omits the local SIM_ID:
    - `S_SIM_AXIS0_TRAJ_CORR_SUITE`
  - `V4` and `V5` are narrower descendant surfaces:
    - `V4` is a single-sequence aggregate with `16` cycles and `256` trials
    - `V5` is a two-sequence entangled-init delta surface with `64` cycles and `256` trials
- bounded implication:
  - code-level provenance aligns with the current runner, but top-level admission selects later compressed descendants rather than the local suite SIM_ID

## 4) Comparison Anchors
- comparison sources:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis0_traj_corr_metrics_family__v1/MANIFEST.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V4.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V5.json`
- relevant anchors:
  - `SIM_CATALOG_v1.3.md:39-40`
  - `SIM_CATALOG_v1.3.md:51-52`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:1-26`
  - `BATCH_sims_axis0_traj_corr_metrics_family__v1/MANIFEST.json`
- bounded comparison read:
  - the prior residual batch set this pair next
  - the current family expands the prior metrics family from a two-sequence signless slice to a full sign/init/direction/sequence lattice
  - the repo-top `V4/V5` descendants should stay comparison-only here because they are compressed descendants under the same runner hash, not the local suite surface itself

## 5) Source-Class Read
- Best classification:
  - standalone signed directional axis0 trajectory-correlation suite family with one local SIM_ID surface and one 32-case result lattice
- Not best classified as:
  - a repo-top admitted local SIM_ID surface
  - a single-direction or single-sign family
  - a direct synonym for `V4` or `V5`
- Theory-facing vs executable-facing split:
  - executable-facing:
    - current runner executes four sequences across two signs, two directions, and two init modes
    - local evidence emission compresses the result to `SEQ01`-relative deltas
  - theory-facing:
    - Bell and Ginibre still split sharply on stored trajectory negativity
    - `SEQ04` is direction-sensitive rather than uniformly extreme
    - sign reversal is near-symmetric but not exact
  - evidence-facing:
    - local evidence is explicit in the runner contract
    - repo-top evidence-pack admission exists only for `V4/V5` descendants under the same code hash
- possible downstream consequence:
  - later residual intake should preserve this family as the wide axis0 suite surface and let `run_axis12_channel_realization_suite.py` begin the next bounded residual pair

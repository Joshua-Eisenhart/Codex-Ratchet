# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_ultra4_full_stack_family__v1`
Extraction mode: `SIM_ULTRA4_FULL_STACK_PASS`
Batch scope: full-stack macro family centered on `run_ultra4_full_stack.py` and `results_ultra4_full_stack.json`, with `ultra_axis0_ab_axis6_sweep` held comparison-only as the next raw-order family
Date: 2026-03-09

## 1) Batch Selection
- starting file in raw simpy folder order:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_ultra4_full_stack.py`
- selected sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_ultra4_full_stack.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra4_full_stack.json`
- reason for bounded family:
  - `run_ultra4_full_stack.py` is the next unprocessed raw-folder-order source
  - it has one direct paired result surface with the same basename
  - it is a broader full-stack macro family than `ultra2`, adding berry-flux reporting and full four-sequence Axis0 AB coverage
  - the adjacent `run_ultra_axis0_ab_axis6_sweep.py` is better treated as the next bounded family because it drops berry flux and Axis12 while retaining only the Stage16 and Axis0 sweep shell
- comparison-only anchors read:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_ultra_axis0_ab_axis6_sweep.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra_axis0_ab_axis6_sweep.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
- deferred next raw-folder-order source:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_ultra_axis0_ab_axis6_sweep.py`

## 2) Source Membership
- Runner:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_ultra4_full_stack.py`
  - sha256: `06a1d4d23d8987d055760456ee4bcc278f0be2562acdd8af14905c20926cda40`
  - size bytes: `15688`
  - line count: `412`
  - source role: full-stack macro runner
- Result surface:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra4_full_stack.json`
  - sha256: `368539c44719f2154fb01192ab01c2ae22596a1723f7d73720852b36b608e9fe`
  - size bytes: `25955`
  - line count: `906`
  - source role: full-stack macro result surface

## 3) Structural Map Of The Family
### Ultra4 full-stack runner: `run_ultra4_full_stack.py`
- anchors:
  - `run_ultra4_full_stack.py:1-412`
  - `run_ultra4_full_stack.py:280-412`
- source role:
  - one full-stack macro runner that stores:
    - `berry_flux_plus`
    - `berry_flux_minus`
    - `stage16`
    - `axis0_ab`
    - `axis12`
    - `seqs`
  - writes one local SIM_ID:
    - `S_SIM_ULTRA4_FULL_STACK`
  - current result shape:
    - `stage16` keys: `48`
    - `axis0_ab` keys: `128`
    - `axis12` keys: `8`
    - `seqs` keys: `4`

### Berry-flux layer
- source markers:
  - `run_ultra4_full_stack.py:39-58`
  - `results_ultra4_full_stack.json`
- bounded read:
  - the full-stack result adds geometry-facing metrics absent from `ultra2`:
    - `berry_flux_plus = 6.217735460226628`
    - `berry_flux_minus = -6.217735460226628`
  - the sign flip is exact at stored precision
  - the magnitude is near, but not equal to, the comment-level expectation of `±2π`

### Stage16 branch
- source markers:
  - `results_ultra4_full_stack.json`
- bounded read:
  - the strongest Stage16 absolute effect is tied between:
    - `T1_outer_1_Se_UP_MIX_A`
    - `T1_inner_1_Se_DOWN_MIX_B`
  - both reach:
    - `abs(dS) = 0.00304873827915781`
  - the next strongest cells remain Se-focused:
    - `T2_inner_1_Se_DOWN_MIX_B`
    - `T2_outer_1_Se_UP_MIX_A`

### Axis0 AB branch
- source markers:
  - `run_ultra4_full_stack.py:332-412`
  - `results_ultra4_full_stack.json`
- bounded read:
  - the `axis0_ab` map mixes two record classes in one surface:
    - `32` absolute `SEQ01` baseline records
    - `96` delta records for `SEQ02` through `SEQ04`
  - the strongest stored delta is:
    - `T2_REV_BELL_CNOT_R1_SEQ04`
    - `dMI = 0.1396523788319004`
    - `dSAgB = -0.13947245906413996`
    - `dNegFrac = 0.06346153846153846`
  - large deltas concentrate in `SEQ04` reverse Bell settings

### Boundary to `ultra_axis0_ab_axis6_sweep`
- comparison anchors:
  - `run_ultra_axis0_ab_axis6_sweep.py:300-398`
  - `results_ultra_axis0_ab_axis6_sweep.json:1-912`
- bounded comparison read:
  - `ultra_axis0_ab_axis6_sweep` keeps:
    - `stage16`
    - `axis0_ab`
    - `seqs`
  - but drops:
    - `berry_flux_plus`
    - `berry_flux_minus`
    - `axis12`
  - it foregrounds `entanglers`, `entangle_reps_list`, and `mix_modes` instead
  - raw-order adjacency therefore marks the next bounded family, not a merged continuation

## 4) Comparison Anchors
- comparison sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_ultra_axis0_ab_axis6_sweep.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra_axis0_ab_axis6_sweep.json`
- relevant anchors:
  - `SIM_CATALOG_v1.3.md:117`
  - `SIM_CATALOG_v1.3.md:131`
  - `SIM_CATALOG_v1.3.md:148-149`
- bounded comparison read:
  - the catalog lists both `ultra4_full_stack` and `ultra_axis0_ab_axis6_sweep`
  - the repo-held top-level evidence pack contains neither `S_SIM_ULTRA4_FULL_STACK` nor `S_SIM_ULTRA_AXIS0_AB_STAGE16_AXIS6_SWEEP`
  - the next raw-order handoff remains a true family boundary within the ultra macro strip

## 5) Source-Class Read
- Best classification:
  - standalone full-stack macro family with geometry, Stage16, Axis0 AB, and Axis12 layers stored in one result
- Not best classified as:
  - a repo-top evidenced macro surface
  - the same bounded family as `run_ultra_axis0_ab_axis6_sweep.py`
  - one uniform effect-scale surface
- Theory-facing vs executable-facing split:
  - executable-facing:
    - one runner emits mixed geometry, Stage16, Axis0 AB, and Axis12 branches into one JSON
  - theory-facing:
    - one proposal-side full-stack composite intended to align geometric sign, sequence, and mixed-axis effects
  - evidence-facing:
    - local SIM_ID exists only in the writer contract
    - the current repo-held top-level evidence pack omits the full-stack family
- possible downstream consequence:
  - later sims interpretation should keep `ultra4` as its own full-stack batch and let `ultra_axis0_ab_axis6_sweep` begin the next narrower ultra family

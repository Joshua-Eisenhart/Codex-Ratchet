# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_engine32_axis0_axis6_attack_family__v1`
Extraction mode: `SIM_ENGINE32_ATTACK_PASS`
Batch scope: focused `engine32_axis0_axis6_attack` runner/result family with adjacent exclusion of `full_axis_suite`
Date: 2026-03-08

## 1) Batch Selection
- starting file in raw simpy folder order:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_engine32_axis0_axis6_attack.py`
- selected sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_engine32_axis0_axis6_attack.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_engine32_axis0_axis6_attack.json`
- reason for bounded family:
  - `run_engine32_axis0_axis6_attack.py` is the next unprocessed raw-folder-order source after the prior `batch_v3` composite precursor batch
  - the script and its paired result are structurally self-contained:
    - one runner
    - one SIM_ID
    - one result file
    - one 32-cell result lattice under a single `results` object
- adjacent-source exclusion decision:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_full_axis_suite.py` was read because it is the immediate next raw-folder-order source
  - it does not belong in this batch because it is a cross-axis sampler:
    - six SIM_EVIDENCE blocks
    - one compact six-block result object
    - axes 3, 4, 5, and 6 only
    - no Axis0 attack lattice
  - it is deferred as the next separate family rather than merged into `engine32`
- comparison-only adjacent-family anchors read:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_full_axis_suite.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_full_axis_suite.json`
  - current standalone descendant surfaces for the adjacent sampler:
    - `results_S_SIM_AXIS3_WEYL_HOPF_GRID_V1.json`
    - `results_S_SIM_AXIS4_COMP_FETI_TEFI_CHECK_V1.json`
    - `results_S_SIM_AXIS5_FGA_SWEEP_V1.json`
    - `results_S_SIM_AXIS5_FSA_SWEEP_V1.json`
    - `results_S_SIM_AXIS6_LR_MULTI_V1.json`

## 2) Source Membership
- Runner:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_engine32_axis0_axis6_attack.py`
  - sha256: `9d9a0a5f73f261b84be6b85df255a2f1f153c4abf090ca7485ae793c3dd0faf0`
  - size bytes: `8682`
  - line count: `238`
  - source role: focused Axis0/Axis6 attack runner
- Result surface:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_engine32_axis0_axis6_attack.json`
  - sha256: `fa5c5fd2da0f8501a39aca0a14c378190b4baea41df77c6a014fa4fc0cda0a41`
  - size bytes: `18434`
  - line count: `689`
  - source role: paired attack result lattice

## 3) Structural Map Of The Family
### Runner: `run_engine32_axis0_axis6_attack.py`
- anchors:
  - `run_engine32_axis0_axis6_attack.py:2-5`
  - `run_engine32_axis0_axis6_attack.py:111-123`
  - `run_engine32_axis0_axis6_attack.py:143-161`
  - `run_engine32_axis0_axis6_attack.py:168-201`
  - `run_engine32_axis0_axis6_attack.py:219-232`
- source role:
  - defines a focused attack lattice over:
    - type sign `T1` / `T2`
    - sequence `SEQ01` .. `SEQ04`
    - loop orientation `outer` / `inner`
    - axis6 mix mode `UNIFORM` / `MIX_R`
  - that yields `32` keyed result cells
  - explicit simplification:
    - “Axis0 proxy score on 1-qubit”
    - “No AB coupling in this batch”
  - evidence output is one SIM_EVIDENCE block for `S_SIM_ENGINE32_AXIS0_AXIS6_ATTACK`
  - that evidence flattens only `MIX_R - UNIFORM` stage deltas rather than storing all absolute cells

### Result surface: `results_engine32_axis0_axis6_attack.json`
- anchors:
  - `results_engine32_axis0_axis6_attack.json:1-689`
- source role:
  - stores global knobs:
    - `seed=0`
    - `states=256`
    - `cycles=16`
    - `theta=0.07`
    - `terrain_params={gamma:0.12,p:0.08,q:0.10}`
    - `operator_params={theta_te:0.05,q_fi:0.06,d_fe:0.04}`
  - stores `32` result cells under `results`
  - each cell stores stage-level absolute trajectory means, not just deltas
- bounded read:
  - for every type and sequence:
    - outer-loop `MIX_R` raises mean stage entropy and lowers mean stage purity relative to `UNIFORM`
    - inner-loop `MIX_R` lowers mean stage entropy and raises mean stage purity relative to `UNIFORM`
  - strongest stored outer mean-stage entropy delta:
    - `T1_SEQ03_outer = +0.0032259641060854993`
  - strongest stored inner mean-stage entropy delta magnitude:
    - `T2_SEQ04_inner = -0.0015717624203513553`

### Adjacent excluded family: `full_axis_suite`
- anchors:
  - `run_full_axis_suite.py:2-5`
  - `run_full_axis_suite.py:84-205`
  - `run_full_axis_suite.py:224-253`
  - `results_full_axis_suite.json:1-36`
- exclusion read:
  - one compact cross-axis sampler with six top-level blocks:
    - `axis3_plus`
    - `axis3_minus`
    - `axis4_composites`
    - `axis5_fga`
    - `axis5_fsa`
    - `axis6_lr`
  - six emitted SIM_IDs rather than one attack SIM_ID
  - no Axis0 lattice and no `32`-cell attack result shape
- bounded decision:
  - keep `full_axis_suite` out of this batch

## 4) Comparison Anchors
- comparison sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - adjacent family sources listed above
- relevant anchors:
  - `SIM_CATALOG_v1.3.md:54`
  - `SIM_CATALOG_v1.3.md:103`
  - `SIM_CATALOG_v1.3.md:125`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:93-107`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:269-298`
- bounded comparison read:
  - the catalog lists `engine32_axis0_axis6_attack` as its own named result surface
  - the catalog separately lists `full_axis_suite` under `OTHER`
  - no direct top-level evidence-pack block was found for `S_SIM_ENGINE32_AXIS0_AXIS6_ATTACK`
  - the adjacent `full_axis_suite` appears to be a precursor-style cross-axis sampler whose current top-level evidence emphasis has shifted to differently named standalone descendants:
    - `S_SIM_AXIS3_WEYL_HOPF_GRID_V1`
    - `S_SIM_AXIS4_COMP_FETI_TEFI_CHECK_V1`
    - `S_SIM_AXIS5_FGA_SWEEP_V1`
    - `S_SIM_AXIS5_FSA_SWEEP_V1`
    - `S_SIM_AXIS6_LR_MULTI_V1`

## 5) Source-Class Read
- Best classification:
  - focused executable-facing attack family on Axis0-proxy / Axis6 order perturbation
- Not best classified as:
  - AB-coupled Axis0 family
  - cross-axis sampler family
  - top-level evidence-pack-grounded family
- Theory-facing vs executable-facing split:
  - executable-facing:
    - 32-cell lattice over type, sequence, loop orientation, and mix mode
    - explicit terrain/operator knobs
    - one paired result file
  - theory-facing:
    - “Axis0 attack” wording is partly abstracted away by the script's own one-qubit proxy simplification
  - evidence-facing:
    - script-local evidence reports only per-stage delta metrics
    - no current top-level evidence-pack anchor was found
- possible downstream consequence:
  - later sims interpretation should distinguish this focused local attack lattice from adjacent composite samplers and from AB-coupled Axis0 families elsewhere in the repo

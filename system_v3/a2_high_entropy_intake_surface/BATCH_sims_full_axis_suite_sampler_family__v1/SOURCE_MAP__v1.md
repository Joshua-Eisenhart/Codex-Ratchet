# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_full_axis_suite_sampler_family__v1`
Extraction mode: `SIM_FULL_AXIS_SAMPLER_PASS`
Batch scope: cross-axis sampler/precursor family centered on `run_full_axis_suite.py` and `results_full_axis_suite.json`, with descendant comparison against current standalone axis surfaces
Date: 2026-03-08

## 1) Batch Selection
- starting file in raw simpy folder order:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_full_axis_suite.py`
- selected sources:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_full_axis_suite.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_full_axis_suite.json`
- reason for bounded family:
  - `run_full_axis_suite.py` is the next unprocessed raw-folder-order source after the `engine32` batch
  - the script and its paired result are one compact cross-axis sampler:
    - six top-level result blocks
    - six SIM_EVIDENCE blocks
    - one aggregate result file
  - the current repo also contains clearly corresponding standalone descendant surfaces for axes 3, 4, 5, and 6, so those were read as comparison anchors rather than merged into source membership
- comparison-only descendant anchors read:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS3_WEYL_HOPF_GRID_V1.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS4_COMP_FETI_TEFI_CHECK_V1.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS5_FGA_SWEEP_V1.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS5_FSA_SWEEP_V1.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS6_LR_MULTI_V1.json`
- deferred next raw-folder-order source:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_history_invariant_gradient_scan_v11.py`

## 2) Source Membership
- Runner:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_full_axis_suite.py`
  - sha256: `71aa883f4c16db4258e00b90944a990e1c8ee9c049cb3a1a51929c1361f060eb`
  - size bytes: `9982`
  - line count: `259`
  - source role: cross-axis sampler / precursor runner
- Result surface:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_full_axis_suite.json`
  - sha256: `14aacaeee692b72eabdd78b08204babd0e4ce5c1eaeede6be3efa02ead16102b`
  - size bytes: `1023`
  - line count: `36`
  - source role: compact six-block sampler result surface

## 3) Structural Map Of The Family
### Runner: `run_full_axis_suite.py`
- anchors:
  - `run_full_axis_suite.py:2-5`
  - `run_full_axis_suite.py:84-106`
  - `run_full_axis_suite.py:109-136`
  - `run_full_axis_suite.py:138-151`
  - `run_full_axis_suite.py:154-203`
  - `run_full_axis_suite.py:224-253`
- source role:
  - samples six axis-themed blocks in one script:
    - `axis3_plus`
    - `axis3_minus`
    - `axis4_composites`
    - `axis5_fga`
    - `axis5_fsa`
    - `axis6_lr`
  - writes one aggregate JSON and one evidence pack with six SIM_EVIDENCE blocks
  - emitted sampler SIM_IDs are:
    - `S_SIM_AXIS3_WEYL_HOPF_PLUS`
    - `S_SIM_AXIS3_WEYL_HOPF_MINUS`
    - `S_SIM_AXIS6_LEFT_RIGHT`
    - `S_SIM_AXIS5_FGA_MONOTONE`
    - `S_SIM_AXIS5_FSA_MONOTONE`
    - `S_SIM_AXIS4_COMPOSITES`

### Result surface: `results_full_axis_suite.json`
- anchors:
  - `results_full_axis_suite.json:1-36`
- source role:
  - stores one compact object with the same six top-level blocks
  - notable stored values:
    - `axis3_plus.berry_flux_approx = 6.283201456311079`
    - `axis3_minus.berry_flux_approx = -6.283201456311079`
    - `axis4_composites.delta_entropy_mean = -0.0003577950542427155`
    - `axis4_composites.delta_purity_mean = 0.00034054630700652844`
    - `axis5_fga.dS_mean = 0.061212233653433076`
    - `axis5_fsa.dS_mean = -3.8878812278972386e-17`
    - `axis6_lr.delta_trace_mean = 0.7668532349210637`
    - `axis6_lr.comm_norm_mean = 0.8864436143270445`

### Descendant comparison read
- descendant surfaces:
  - Axis3: `results_S_SIM_AXIS3_WEYL_HOPF_GRID_V1.json`
  - Axis4: `results_S_SIM_AXIS4_COMP_FETI_TEFI_CHECK_V1.json`
  - Axis5 FGA: `results_S_SIM_AXIS5_FGA_SWEEP_V1.json`
  - Axis5 FSA: `results_S_SIM_AXIS5_FSA_SWEEP_V1.json`
  - Axis6: `results_S_SIM_AXIS6_LR_MULTI_V1.json`
- bounded comparison read:
  - the sampler appears to anticipate these standalone families, but not as exact file-level or metric-level copies
  - Axis3:
    - chirality signs match exactly
    - Berry flux magnitudes are close but not identical
    - descendant adds explicit grid parameters `grid_theta` and `grid_phi`
  - Axis4:
    - descendant naming shifts from `COMPOSITES` to `COMP_FETI_TEFI_CHECK`
    - stored delta signs invert relative to the sampler result
    - top-level evidence pack ties this descendant to hash `b741c60d...`, not to the sampler hash
  - Axis5:
    - FSA remains near-zero in both sampler and descendant
    - FGA mean differs materially (`0.061212233653433076` in sampler vs `0.0456039355887` in descendant evidence/result)
  - Axis6:
    - sampler and descendant measure the same conceptual pair through `delta_trace_mean` and `comm_norm_mean`, alongside corresponding min/max fields
    - means differ materially (`delta_trace_mean` lower in sampler, `comm_norm_mean` slightly higher in sampler)

## 4) Comparison Anchors
- comparison sources:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
- relevant anchors:
  - `SIM_CATALOG_v1.3.md:11-16`
  - `SIM_CATALOG_v1.3.md:86`
  - `SIM_CATALOG_v1.3.md:103`
  - `SIM_CATALOG_v1.3.md:125`
  - `SIM_CATALOG_v1.3.md:139`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:93-107`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:269-298`
- bounded comparison read:
  - the catalog lists `full_axis_suite` under `OTHER`
  - the catalog and evidence pack separately foreground the standalone descendants rather than the sampler's own six emitted SIM_ID names
  - descendant evidence uses different code hashes:
    - `1c8a7ac3...` for current Axis3 / Axis5 / Axis6 standalone descendants
    - `b741c60d...` for current Axis4 descendant
  - no top-level evidence-pack block was found for any of the sampler's emitted SIM_ID names

## 5) Source-Class Read
- Best classification:
  - cross-axis sampler / precursor family with partial descendant anticipation
- Not best classified as:
  - one coherent current evidence family
  - exact producer of the current standalone descendant surfaces
  - same source family as later history-gradient scans
- Theory-facing vs executable-facing split:
  - executable-facing:
    - one sampler script
    - one compact result object
    - six emitted evidence blocks
  - theory-facing:
    - the script samples multiple axis stories in one surface, acting as a cross-axis bridge rather than a dedicated family runner
  - evidence-facing:
    - current repo-top evidence emphasis has moved to differently named standalone descendants
- possible downstream consequence:
  - later sims interpretation should use this batch as a cross-axis precursor map, not as proof that the standalone descendants share one direct producer path

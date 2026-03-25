# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_axis0_traj_corr_suite_v2_orphan_family__v1`
Extraction mode: `SIM_AXIS0_TRAJ_CORR_SUITE_V2_ORPHAN_PASS`
Batch scope: residual result-only axis0 trajectory-correlation `v2` orphan centered on `results_axis0_traj_corr_suite_v2.json`, compared against the earlier local trajectory-correlation family and the repo-top `V4`/`V5` descendants without merging them
Date: 2026-03-09

## 1) Batch Selection
- starting residual-priority source:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_traj_corr_suite_v2.json`
- selected sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_traj_corr_suite_v2.json`
- reason for bounded family:
  - the prior boundary/bookkeep orphan batch explicitly deferred this surface next and kept it separate
  - the current orphan has a distinct 128-case trajectory-correlation contract with no direct runner-name hit in `simpy/`
  - repo-local comparison shows it is related to the earlier local trajectory-correlation family and the repo-top descendants, but it is not identical to either
- comparison-only anchors read:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis0_boundary_bookkeep_v1_orphan_slice__v1/MANIFEST.json`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis0_traj_corr_suite_family__v1/MANIFEST.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_traj_corr_suite.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V4.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V5.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_INDEX__v1.md`
- deferred next residual-priority source:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra3_full_geometry_stage16_axis0.json`

## 2) Source Membership
- Result surface:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_traj_corr_suite_v2.json`
  - sha256: `057c85359ed0c4a874a1f67beed9a4e4f0c2d836b673a8325f600aab95bcf6cf`
  - size bytes: `30375`
  - line count: `939`
  - source role: compressed 128-case axis0 trajectory-correlation successor/orphan surface with seq01 absolute baselines and seq02-04 deltas

## 3) Structural Map Of The Family
### Result structure: `results_axis0_traj_corr_suite_v2.json`
- anchors:
  - `results_axis0_traj_corr_suite_v2.json:1-939`
- source role:
  - one compressed trajectory-correlation lattice with:
    - `4` sequence definitions
    - `128` total entries inside `axis0_traj`
    - `32` absolute base entries
    - `96` delta entries
    - `trials = 128`
    - `cycles = 64`
    - shared `theta = 0.07`
- strongest bounded reads:
  - all absolute base entries are `SEQ01` only
  - all deltas target:
    - `SEQ02`
    - `SEQ03`
    - `SEQ04`
  - the hidden prefix lattice is:
    - `T1` and `T2`
    - directions `FWD` and `REV`
    - init classes `BELL` and `GINIBRE`
    - gates `CNOT` and `CZ`
    - repetitions `R1` and `R2`
  - strongest stored base MI trajectory case:
    - `T1_REV_BELL_CZ_R1_SEQ01`
    - `MI_traj_mean = 0.03093941684451413`
  - strongest stored delta case:
    - `T1_REV_BELL_CNOT_R1_SEQ04`
    - `dMI = 0.08605915916874307`
    - `dNegFrac = 0.00958251953125`
    - `dSAgB = -0.07798693536836021`
- bounded implication:
  - the surface is not a flat all-absolute suite; it is a seq01-baseline-plus-deltas contract over a hidden 32-prefix lattice

### Hidden-axis prefix tension
- anchors:
  - `results_axis0_traj_corr_suite_v2.json:1-939`
- bounded read:
  - the top-level metadata does not expose `T1` / `T2` as named axes
  - the key lattice requires them:
    - `T1` base prefix count = `16`
    - `T2` base prefix count = `16`
- bounded implication:
  - one important axis is encoded only in keys rather than in explicit metadata

### Separation from the earlier local trajectory-correlation family
- comparison anchors:
  - `BATCH_sims_axis0_traj_corr_suite_family__v1/MANIFEST.json`
  - `results_axis0_traj_corr_suite.json:1-364`
- bounded read:
  - earlier local family:
    - `32` absolute cases
    - explicit sign labels
    - no gate axis
    - no repetition axis
    - all four sequences stored as absolutes
    - local max `MI_traj_mean = 0.29728021483432243` at `sign1_BELL_REV_SEQ04`
  - current orphan:
    - `32` absolute `SEQ01` baselines only
    - `96` deltas for `SEQ02-04`
    - explicit gate axis `CNOT` / `CZ`
    - explicit repetition axis `R1` / `R2`
    - hidden `T1` / `T2` axis
    - max absolute base `MI_traj_mean = 0.03093941684451413`
- bounded implication:
  - the current orphan is not a simple `v2` rerendering of the earlier local suite; it uses a materially different storage and axis contract

### Separation from repo-top descendants `V4` and `V5`
- comparison anchors:
  - `results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V4.json:1-16`
  - `results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V5.json:1-23`
  - `BATCH_sims_axis0_traj_corr_suite_family__v1/MANIFEST.json`
- bounded read:
  - `V4`:
    - one single-sequence aggregate
    - `cycles = 16`
    - `trials = 256`
  - `V5`:
    - two-sequence entangled-init delta contract
    - `cycles = 64`
    - `trials = 256`
  - current orphan:
    - `128` entries
    - four-sequence baseline-plus-delta lattice
    - `cycles = 64`
    - `trials = 128`
- bounded implication:
  - the current orphan is neither the earlier local full-absolute suite nor either repo-top compressed descendant

### Visibility relation
- comparison anchors:
  - `SIM_CATALOG_v1.3.md:51-52`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt`
- bounded read:
  - the top-level catalog lists:
    - `axis0_traj_corr_suite`
    - `axis0_traj_corr_suite_v2`
  - the repo-held evidence pack omits:
    - `axis0_traj_corr_suite_v2`
    - `results_axis0_traj_corr_suite_v2.json`
    - any explicit `S_SIM_AXIS0_TRAJ_CORR_SUITE_V2`
- bounded implication:
  - the orphan is catalog-visible by filename alias only and remains unadmitted at the evidence-pack layer

## 4) Comparison Anchors
- comparison sources:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis0_boundary_bookkeep_v1_orphan_slice__v1/MANIFEST.json`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis0_traj_corr_suite_family__v1/MANIFEST.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_traj_corr_suite.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V4.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V5.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
- relevant anchors:
  - `BATCH_sims_axis0_traj_corr_suite_family__v1/MANIFEST.json`
  - `SIM_CATALOG_v1.3.md:51-52`
  - `results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V4.json`
  - `results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V5.json`
- bounded comparison read:
  - the prior boundary/bookkeep orphan batch explicitly kept this file separate
  - the earlier local trajectory-correlation family is the closest analog, but the current orphan changes both storage and lattice structure
  - the repo-top descendants are even more compressed and use different contracts again

## 5) Source-Class Read
- Best classification:
  - residual result-only axis0 trajectory-correlation orphan family with seq01 baselines and seq02-04 deltas over a hidden gate/repetition lattice
- Not best classified as:
  - the earlier local trajectory-correlation suite with a version bump
  - a repo-top descendant surface
  - part of the boundary/bookkeep family
- Theory-facing vs executable-facing split:
  - executable-facing:
    - one hidden `T1`/`T2` axis encoded only in keys
    - explicit direction, init, gate, and repetition axes
    - base entries for `SEQ01` only, deltas for `SEQ02-04`
  - theory-facing:
    - strongest delta perturbation concentrates on `T1_REV_BELL_CNOT_R1_SEQ04`
    - the contract privileges relative sequence change over full absolute reporting
  - evidence-facing:
    - no direct runner-name anchor is recoverable in current `simpy/`
    - top-level visibility is catalog-only and absent from the evidence pack
- possible downstream consequence:
  - the next residual result-only pass should leave axis0 and process `results_ultra3_full_geometry_stage16_axis0.json`, deciding separately whether `results_ultra_big_ax012346.json` belongs in the same bounded ultra family

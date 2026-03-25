# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_axis12_channel_realization_suite_family__v1`
Extraction mode: `SIM_AXIS12_CHANNEL_REALIZATION_SUITE_PASS`
Batch scope: standalone residual axis12 channel-realization suite family centered on `run_axis12_channel_realization_suite.py` and `results_axis12_channel_realization_suite.json`, with repo-top `V4` descendant separation preserved and runner-only harden surfaces kept out of batch
Date: 2026-03-09

## 1) Batch Selection
- starting residual-priority source:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_channel_realization_suite.py`
- selected sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_channel_realization_suite.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_channel_realization_suite.json`
- reason for bounded family:
  - the prior residual paired-family batch deferred this exact pair next
  - one runner emits one paired result surface with one local SIM_ID
  - the current family is a local fixed-parameter axis12 edge-and-endpoint suite and should stay separate from the repo-top `V4` descendant grid scan and the adjacent runner-only harden surfaces
- comparison-only anchors read:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis0_traj_corr_suite_family__v1/MANIFEST.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS12_CHANNEL_REALIZATION_V4.json`
- deferred next residual-priority source:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_seq_constraints.py`

## 2) Source Membership
- Runner:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_channel_realization_suite.py`
  - sha256: `5e6358240110019fd266675f9ff1e520c7822114a811d597b630a62aa9efd6f5`
  - size bytes: `6370`
  - line count: `185`
  - source role: local axis12 edge-and-endpoint realization suite runner
- Result surface:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_channel_realization_suite.json`
  - sha256: `01cde71ebef55ec240c146a372dcebc78c38ecc2141a280c1a4a461069e023e2`
  - size bytes: `1670`
  - line count: `93`
  - source role: compact four-sequence endpoint realization result surface

## 3) Structural Map Of The Family
### Runner contract: `run_axis12_channel_realization_suite.py`
- anchors:
  - `run_axis12_channel_realization_suite.py:80-181`
- source role:
  - one four-sequence axis12 family:
    - `SEQ01 = [Se, Ne, Ni, Si]`
    - `SEQ02 = [Se, Si, Ni, Ne]`
    - `SEQ03 = [Se, Ne, Si, Ni]`
    - `SEQ04 = [Se, Si, Ne, Ni]`
  - fixed runtime parameters:
    - seed `0`
    - cycles `64`
    - states `256`
    - theta `0.07`
    - n-vector `(0.3, 0.4, 0.866025403784)`
    - terrain params `{gamma: 0.12, p: 0.08, q: 0.10}`
  - two evaluated layers:
    - axis12 edge booleans:
      - `SENI`
      - `NESI`
    - endpoint realization under `axis3_sign in {+1, -1}`
  - emits one local SIM_ID:
    - `S_SIM_AXIS12_CHANNEL_REALIZATION_SUITE`

### Result structure: `results_axis12_channel_realization_suite.json`
- top-level shape:
  - one compact result surface with:
    - `axis12_edges`
    - `results`
    - fixed metadata
- stored edge partition:
  - `SEQ01` and `SEQ02`:
    - `SENI = 0`
    - `NESI = 0`
  - `SEQ03` and `SEQ04`:
    - `SENI = 1`
    - `NESI = 1`
- strongest bounded endpoint read:
  - plus sign best entropy and purity both land on `SEQ02`:
    - `vn_entropy_mean = 0.6331874849867805`
    - `purity_mean = 0.558751368096289`
  - minus sign best entropy and purity also land on `SEQ02`:
    - `vn_entropy_mean = 0.6402117280644419`
    - `purity_mean = 0.551994589317754`

### Edge classes do not determine within-class ordering
- bounded read:
  - `SEQ01` and `SEQ02` share identical edge flags but differ materially:
    - plus entropy delta `SEQ02 - SEQ01 = -0.00266922006375`
    - plus purity delta `SEQ02 - SEQ01 = 0.002563614167709406`
  - `SEQ03` and `SEQ04` also share identical edge flags but differ:
    - plus entropy delta `SEQ04 - SEQ03 = -0.001101633951014794`
    - plus purity delta `SEQ04 - SEQ03 = 0.001059969130392873`
- bounded implication:
  - the axis12 edge booleans partition the suite into two coarse classes, but do not fully determine endpoint order inside each class

### Axis3 sign effect is uniform in direction across all sequences
- bounded read:
  - for every sequence, `axis3_sign = +1` stores:
    - lower `vn_entropy_mean`
    - higher `purity_mean`
  - largest plus-minus gap occurs on `SEQ02`:
    - `delta_entropy_plus_minus = -0.007024243077661474`
    - `delta_purity_plus_minus = 0.0067567787785349775`
- bounded implication:
  - sign choice is globally directional in this local suite even though the size of the effect varies by sequence

### Top-level descendant relation
- comparison anchors:
  - `SIM_CATALOG_v1.3.md:57`
  - `SIM_CATALOG_v1.3.md:62`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:30-35`
  - `results_S_SIM_AXIS12_CHANNEL_REALIZATION_V4.json:1-596`
- bounded read:
  - the repo-held top-level evidence pack admits:
    - `S_SIM_AXIS12_CHANNEL_REALIZATION_V4`
  - that evidence block carries the same code hash as the current runner:
    - `5e6358240110019fd266675f9ff1e520c7822114a811d597b630a62aa9efd6f5`
  - the repo-held evidence pack omits the local SIM_ID:
    - `S_SIM_AXIS12_CHANNEL_REALIZATION_SUITE`
  - the repo-top `V4` surface is a parameter grid over:
    - `gamma in {0.02, 0.08, 0.14}`
    - `p in {0.02, 0.08, 0.14}`
    - `q in {0.02, 0.08, 0.14}`
    - `theta in {0.03, 0.07, 0.12}`
  - the local suite is instead one fixed-parameter, four-sequence endpoint comparison
- bounded implication:
  - code-level provenance aligns, but the repo-top admitted artifact is a broader descendant grid surface rather than the local suite SIM_ID

## 4) Comparison Anchors
- comparison sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis0_traj_corr_suite_family__v1/MANIFEST.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS12_CHANNEL_REALIZATION_V4.json`
- relevant anchors:
  - `SIM_CATALOG_v1.3.md:57,62,137`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:30-35`
  - `BATCH_sims_axis0_traj_corr_suite_family__v1/MANIFEST.json`
- bounded comparison read:
  - the prior residual batch set this pair next
  - the current family is local and fixed-parameter
  - the repo-top `V4` descendant should stay comparison-only here because it is a grid scan under the same runner hash, not the local suite surface itself
  - adjacent `run_axis12_harden_triple_v1.py` and `run_axis12_harden_v2_triple.py` stay out of batch because they are runner-only residuals with no paired result surface

## 5) Source-Class Read
- Best classification:
  - standalone local axis12 edge-and-endpoint realization suite with one local SIM_ID surface and one fixed-parameter result snapshot
- Not best classified as:
  - the repo-top admitted `V4` surface
  - a full parameter-scan family
  - a merged batch with runner-only harden surfaces
- Theory-facing vs executable-facing split:
  - executable-facing:
    - current runner computes coarse axis12 edge flags and endpoint realization summaries for sign `±1`
    - the local result is compact and fixed-parameter
  - theory-facing:
    - edge classes separate the four sequences into two groups, but do not explain the full within-group ordering
    - plus sign consistently lowers entropy and raises purity for all four sequences
  - evidence-facing:
    - local evidence is explicit in the runner contract
    - repo-top evidence-pack admission exists only for the `V4` descendant under the same code hash
- possible downstream consequence:
  - later residual intake should preserve this family as the local fixed-parameter axis12 realization suite and let `run_axis12_seq_constraints.py` begin the next bounded paired family

# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_batch_v3_composite_precursor_bundle__v1`
Extraction mode: `SIM_BATCH_BUNDLE_PASS`
Batch scope: composite precursor bundle centered on `run_batch_v3.py` and `results_batch_v3.json`, with adjacent-family exclusion for `run_engine32_axis0_axis6_attack.py`
Date: 2026-03-08

## 1) Batch Selection
- starting file in raw simpy folder order:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_batch_v3.py`
- selected sources:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_batch_v3.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_batch_v3.json`
- reason for bounded family:
  - `run_batch_v3.py` is the first unprocessed raw-folder-order source after the prior Axis4 directional suite batch
  - the script is structurally one composite bundle: it defines four embedded sims, writes one aggregate `results_batch_v3.json`, and writes one packed evidence file with four SIM_EVIDENCE blocks
  - the paired result surface mirrors that bundle by storing four top-level embedded payloads rather than one focused family schema
- adjacent-source exclusion decision:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_engine32_axis0_axis6_attack.py` was read as the immediately adjacent raw-order source
  - it does not belong in this batch because it is one focused attack suite with one SIM_ID, one result family, a different result schema, and a different catalog placement
  - it is deferred as the next raw-folder-order family rather than merged into this precursor bundle
- comparison-only descendant anchors read for bundle interpretation:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS12_CHANNEL_REALIZATION_V4.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V4.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V5.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_STAGE16_SUB4_AXIS6_UNIFORM_V4.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_STAGE16_SUB4_UNIFORM_AXIS6_V5.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_NEGCTRL_AXIS6_COMMUTE_V2.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_NEGCTRL_AXIS6_COMMUTE_V3.json`

## 2) Source Membership
- Composite runner:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_batch_v3.py`
  - sha256: `42d532b98cfa1a054fdff2a70e4df1fa77a5f1e9c4f39d7b18a2cf09d8862a91`
  - size bytes: `17527`
  - line count: `503`
  - source role: composite precursor bundle runner
- Aggregate result surface:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_batch_v3.json`
  - sha256: `d58eb25c13d9629f2d3ab27669c780a6f79fb7f07593a88a4a4a342700410d96`
  - size bytes: `6186`
  - line count: `222`
  - source role: aggregate multi-sim result container

## 3) Structural Map Of The Family
### Composite runner: `run_batch_v3.py`
- anchors:
  - `run_batch_v3.py:2-5`
  - `run_batch_v3.py:214-263`
  - `run_batch_v3.py:264-324`
  - `run_batch_v3.py:326-401`
  - `run_batch_v3.py:402-434`
  - `run_batch_v3.py:435-500`
- source role:
  - defines four embedded sims:
    - `S_SIM_AXIS12_CHANNEL_REALIZATION_V3`
    - `S_SIM_STAGE16_SUB4_AXIS6_UNIFORM_V3`
    - `S_SIM_AXIS0_TRAJ_CORR_SUITE_V3`
    - `S_SIM_NEGCTRL_AXIS6_COMMUTE_V1`
  - writes one aggregate `results_batch_v3.json`
  - writes one `sim_evidence_pack.txt` containing four SIM_EVIDENCE blocks
  - evidence hashes are computed per embedded payload, not from the aggregate `results_batch_v3.json` container

### Aggregate result surface: `results_batch_v3.json`
- anchors:
  - `results_batch_v3.json:1-222`
- source role:
  - stores four top-level payloads keyed by embedded SIM_ID rather than one normalized family schema
  - aggregate file hash is `d58eb25c13d9629f2d3ab27669c780a6f79fb7f07593a88a4a4a342700410d96`
  - embedded payload hashes derived from the stored result are:
    - `S_SIM_AXIS12_CHANNEL_REALIZATION_V3` -> `43e11d9da4a361844b9b9d509b3c255a956953653d4c5d4670498238522411a7`
    - `S_SIM_STAGE16_SUB4_AXIS6_UNIFORM_V3` -> `855d4daa4a17b3add8fdd088859cae6b670543a544b5bd41e60624a30896953d`
    - `S_SIM_AXIS0_TRAJ_CORR_SUITE_V3` -> `e5569eeded69ce2ee6b046ae8c67d04d0a0b131302d8117c682b531a934abdb0`
    - `S_SIM_NEGCTRL_AXIS6_COMMUTE_V1` -> `0524d2f133ba5a4240ec83a3b6956393b1501ef61fed795503fe89a3dbec2002`

### Adjacent excluded family: `engine32_axis0_axis6_attack`
- anchors:
  - `run_engine32_axis0_axis6_attack.py:2-5`
  - `run_engine32_axis0_axis6_attack.py:141-209`
  - `run_engine32_axis0_axis6_attack.py:210-238`
  - `results_engine32_axis0_axis6_attack.json:1-689`
- exclusion read:
  - one script
  - one SIM_ID: `S_SIM_ENGINE32_AXIS0_AXIS6_ATTACK`
  - one result file with `32` keyed result cells under one `results` object
  - no composite precursor structure and no mixed embedded subfamily naming
- bounded decision:
  - keep `engine32` as the next separate batch

## 4) Comparison Anchors
- comparison sources:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - the seven descendant result surfaces listed above
- relevant anchors:
  - `SIM_CATALOG_v1.3.md:39-54`
  - `SIM_CATALOG_v1.3.md:102-108`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:2-40`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:318-414`
- bounded comparison read:
  - the catalog places `batch_v3` under `OTHER`, while the bundle internally carries Axis12, Axis0, Stage16, and Axis6-negctrl content that later appears as standalone surfaces elsewhere in the catalog
  - the top-level evidence pack does not expose the bundle's four V3/V1 SIM_IDs directly
  - instead, it exposes later standalone descendants:
    - `S_SIM_AXIS12_CHANNEL_REALIZATION_V4`
    - `S_SIM_AXIS0_TRAJ_CORR_SUITE_V4`
    - `S_SIM_AXIS0_TRAJ_CORR_SUITE_V5`
    - `S_SIM_NEGCTRL_AXIS6_COMMUTE_V2`
    - `S_SIM_NEGCTRL_AXIS6_COMMUTE_V3`
    - `S_SIM_STAGE16_SUB4_AXIS6_UNIFORM_V4`
    - `S_SIM_STAGE16_SUB4_UNIFORM_AXIS6_V5`
  - descendant drift is real:
    - Axis12 V4 becomes an `81`-row parameter grid rather than the bundle's sequence-count plus plus/minus channel snapshot
    - Axis0 V4 and V5 collapse or transform the bundle's dual-sign suite into later standalone result schemas
    - Stage16 V4 and V5 are byte-identical result files with different names and SIM_IDs
    - Negctrl V2 and V3 keep identical mean metrics but change the stored trial count from `256` to `512`

## 5) Source-Class Read
- Best classification:
  - composite sims precursor bundle with later descendant family drift
- Not best classified as:
  - one coherent present-tense executable family
  - one clean evidence-linked result surface
  - the same family as adjacent `engine32_axis0_axis6_attack`
- Theory-facing vs executable-facing split:
  - executable-facing:
    - one runner with four embedded sim functions
    - per-embedded-payload evidence hashing
    - one aggregate result container
  - theory-facing:
    - the bundle now reads mostly as a precursor index for later standalone families rather than as the primary evidence surface for those families
  - evidence-facing:
    - current top-level evidence emphasis has shifted to decomposed standalone descendants rather than this aggregate bundle
- possible downstream consequence:
  - later sims intake should keep `batch_v3` as a precursor/reference bundle and process `engine32` next as its own direct executable family

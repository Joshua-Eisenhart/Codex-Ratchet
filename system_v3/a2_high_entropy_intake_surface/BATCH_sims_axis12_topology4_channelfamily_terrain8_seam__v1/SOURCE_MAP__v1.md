# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_axis12_topology4_channelfamily_terrain8_seam__v1`
Extraction mode: `SIM_AXIS12_TOPOLOGY4_CHANNELFAMILY_TERRAIN8_SEAM_PASS`
Batch scope: topology4 residual seam family centered on `run_axis12_topology4_channelfamily_suite_v2.py` and the repo-held admitted `results_S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1.json`, with the runner's own incompatible local result surface preserved comparison-only
Date: 2026-03-09

## 1) Batch Selection
- starting residual-priority source:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_topology4_channelfamily_suite_v2.py`
- selected sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_topology4_channelfamily_suite_v2.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1.json`
- reason for bounded family:
  - the prior residual paired-family batch deferred this exact runner and admitted terrain8 surface next
  - the repo-held evidence pack directly admits `S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1` under the current runner hash
  - the current runner source now names a different SIM_ID and a different local result file, so the batch is best framed as one preserved seam rather than a normal clean runner/result pair
- comparison-only anchors read:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_topology4_channelfamily_suite_v2.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis12_seq_constraints_family__v1/MANIFEST.json`
- deferred next residual-priority source:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_topology4_channelgrid_v1.py`

## 2) Source Membership
- Runner:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_topology4_channelfamily_suite_v2.py`
  - sha256: `be1a8c714b57ebfe98559d14237d85b258f760f5db2691f10b3f778660edcb12`
  - size bytes: `7090`
  - line count: `213`
  - source role: topology4 channel-family suite runner with current local `CHANNELFAMILY_V2` contract
- Repo-held admitted result surface:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1.json`
  - sha256: `218b43b4a1adee0149363f5103840329693d81e82beea73485fdc1235e2a6e9a`
  - size bytes: `1833`
  - line count: `78`
  - source role: repo-top admitted terrain8 endpoint surface attributed to the same runner hash

## 3) Structural Map Of The Family
### Runner contract: `run_axis12_topology4_channelfamily_suite_v2.py`
- anchors:
  - `run_axis12_topology4_channelfamily_suite_v2.py:1-211`
- source role:
  - one topology4 family over:
    - axis1 in `{EO, EC}`
    - axis2 in `{FX, AD}`
  - current output contract:
    - `results_axis12_topology4_channelfamily_suite_v2.json`
    - local SIM_ID `S_SIM_AXIS12_TOPOLOGY4_CHANNELFAMILY_SUITE_V2`
  - tracked family metrics:
    - `deltaH_absmean`
    - `deltaH_absmax`
    - `min_eig_min`
    - `dS_mean`
    - `lin_err_mean`
  - strongest current local family metrics:
    - max `lin_err_mean`:
      - `EC_AD = 0.02232371509931299`
    - max `deltaH_absmean`:
      - `EO_FX = 0.12029928053976777`
  - bounded implication:
    - the current executable-facing contract is a four-family channel-math suite, not a terrain8 endpoint surface

### Selected admitted result surface: `results_S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1.json`
- top-level shape:
  - one terrain8-style endpoint surface with `16` cells:
    - terrains `{Se, Ne, Ni, Si}`
    - signs `{sign1, sign-1}`
    - directions `{UP, DOWN}`
  - stored metrics per cell:
    - `entropy_mean`
    - `purity_mean`
- strongest bounded metrics:
  - lowest entropy overall:
    - `Si_sign-1_DOWN = 0.32534208782053975`
  - highest purity overall:
    - `Si_sign-1_UP = 0.8057525632184778`
  - example sign-pattern reversals:
    - `Se`: sign `+1` improves relative to sign `-1`
    - `Ne`: sign `+1` worsens relative to sign `-1`
    - `Si`: sign `+1` worsens strongly relative to sign `-1`
- bounded implication:
  - the admitted surface carries real terrain-specific sign structure, not topology4 family metrics

### Runner-local result surface stays comparison-only because it is incompatible with the selected admitted surface
- comparison anchors:
  - `results_axis12_topology4_channelfamily_suite_v2.json:1-37`
- bounded read:
  - the runner's local result surface stores:
    - `families.EC_AD`
    - `families.EC_FX`
    - `families.EO_AD`
    - `families.EO_FX`
  - the selected admitted terrain8 surface stores:
    - `Se_sign...`
    - `Ne_sign...`
    - `Ni_sign...`
    - `Si_sign...`
  - the two result surfaces are not format-equivalent and do not expose the same metric families
- bounded implication:
  - the current batch must preserve the mismatch rather than pretend the runner and admitted surface form a normal clean pair

### Repo-top evidence relation
- comparison anchors:
  - `SIM_CATALOG_v1.3.md:59,68,75,77,80,138`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:54-89`
- bounded read:
  - the repo-held top-level evidence pack directly admits:
    - `S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1`
  - that block carries:
    - current runner code hash `be1a8c714b57ebfe98559d14237d85b258f760f5db2691f10b3f778660edcb12`
    - selected output hash `218b43b4a1adee0149363f5103840329693d81e82beea73485fdc1235e2a6e9a`
  - the evidence pack does not admit the current local SIM_ID:
    - `S_SIM_AXIS12_TOPOLOGY4_CHANNELFAMILY_SUITE_V2`
  - evidence metric tokenization also diverges from the selected JSON keys:
    - evidence lines use `sign_1`
    - selected JSON keys use `sign-1`
- bounded implication:
  - repo-top admission is exact for the terrain8 surface, but the current runner comments, local output contract, and local result surface all point elsewhere

## 4) Comparison Anchors
- comparison sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_topology4_channelfamily_suite_v2.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis12_seq_constraints_family__v1/MANIFEST.json`
- relevant anchors:
  - `SIM_CATALOG_v1.3.md:59,68,69,75,76,77,80,138`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:54-89`
  - `BATCH_sims_axis12_seq_constraints_family__v1/MANIFEST.json`
- bounded comparison read:
  - the prior residual batch set this runner/admitted surface seam next
  - the following topology4 channelgrid pair remains separate because it has its own runner and paired result surface
  - the current runner's own local result file stays comparison-only because its contract is incompatible with the admitted terrain8 surface

## 5) Source-Class Read
- Best classification:
  - topology4 provenance seam family where one current runner hash is attached to two incompatible result contracts
- Not best classified as:
  - a normal clean runner/result pair
  - a pure topology4 channel-family batch
  - a pure terrain8 endpoint batch
- Theory-facing vs executable-facing split:
  - executable-facing:
    - the current runner now implements a four-family topology4 math suite with `EO/EC` and `FX/AD`
    - the local result surface matches that contract
  - theory-facing:
    - the admitted terrain8 surface expresses terrain-by-sign-by-direction endpoint ordering, with `Si` strongest overall
    - sign effects are terrain-specific rather than uniform
  - evidence-facing:
    - repo-top admission is exact for the selected terrain8 surface
    - the admitted SIM_ID and selected output hash do not match the current runner's local output contract
- possible downstream consequence:
  - later residual intake should preserve this seam as-is and let `run_axis12_topology4_channelgrid_v1.py` begin the next bounded paired family

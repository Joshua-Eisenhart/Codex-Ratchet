# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_axis12_topology4_channelgrid_family__v1`
Extraction mode: `SIM_AXIS12_TOPOLOGY4_CHANNELGRID_PASS`
Batch scope: standalone residual axis12 topology4 channelgrid family centered on `run_axis12_topology4_channelgrid_v1.py` and `results_axis12_topology4_channelgrid_v1.json`, with the neighboring terrain8 admission seam preserved comparison-only
Date: 2026-03-09

## 1) Batch Selection
- starting residual-priority source:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_topology4_channelgrid_v1.py`
- selected sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_topology4_channelgrid_v1.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_topology4_channelgrid_v1.json`
- reason for bounded family:
  - the prior topology4 seam batch deferred this exact runner/result pair next
  - one runner emits one paired result surface with one local SIM_ID
  - the current family is a clean topology4 channelgrid contract and should stay separate from the neighboring terrain8 admission seam
- comparison-only anchors read:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis12_topology4_channelfamily_terrain8_seam__v1/MANIFEST.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1.json`
- deferred next residual-priority source:
  - none inside the residual paired-family campaign; the paired-family strip is exhausted after this batch

## 2) Source Membership
- Runner:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_topology4_channelgrid_v1.py`
  - sha256: `f4017440edddbcfe71718df1bbb70647be0ead5179f97edba880fa3afa885cf2`
  - size bytes: `7541`
  - line count: `212`
  - source role: topology4 channelgrid runner with explicit test-vs-control sign layer
- Result surface:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_topology4_channelgrid_v1.json`
  - sha256: `e8e2bb00ae3bc88fc7eb4d695d6e1ba13ff52844c4481bb817bf4cb047f05979`
  - size bytes: `2624`
  - line count: `72`
  - source role: compact topology4 channelgrid result surface

## 3) Structural Map Of The Family
### Runner contract: `run_axis12_topology4_channelgrid_v1.py`
- anchors:
  - `run_axis12_topology4_channelgrid_v1.py:120-209`
- source role:
  - one topology4 family over:
    - axis1 in `{EO, EC}`
    - axis2 in `{FX, AD}`
  - explicit axis3 sign test:
    - `n_test = (0.3, 0.4, 0.866025403784)` should not commute with `Z`
    - `n_ctrl = (0.0, 0.0, 1.0)` should commute with `Z`
    - `theta = 0.07`
  - stored family metrics:
    - `TEST_plus_deltaH_absmean`
    - `TEST_minus_deltaH_absmean`
    - `TEST_delta_deltaH_absmean`
    - `CTRL_plus_deltaH_absmean`
    - `CTRL_minus_deltaH_absmean`
    - `CTRL_delta_deltaH_absmean`
    - `TEST_plus_dS_mean`
    - `TEST_minus_dS_mean`
    - `CTRL_plus_dS_mean`
    - `CTRL_minus_dS_mean`
    - `lin_err_mean`
  - emits one local SIM_ID:
    - `S_SIM_AXIS12_TOPOLOGY4_CHANNELGRID_V1`

### Result structure: `results_axis12_topology4_channelgrid_v1.json`
- top-level shape:
  - one compact result surface with:
    - `families`
    - shared topology4 metadata
- strongest bounded metrics:
  - max `lin_err_mean`:
    - `EC_AD = 0.023410521136522085`
  - max test-axis sign gap:
    - `EO_FX.TEST_delta_deltaH_absmean = -0.0009384673072792976`
  - max control-axis sign gap:
    - `EO_FX.CTRL_delta_deltaH_absmean = 2.7755575615628914e-17`
- bounded implication:
  - adaptive families carry the axis2 nonlinearity signal
  - the commuting control axis suppresses sign sensitivity down to numerical noise

### Fixed vs adaptive split is clean on `lin_err_mean`
- bounded read:
  - adaptive families:
    - `EO_AD.lin_err_mean = 0.01302066155298634`
    - `EC_AD.lin_err_mean = 0.023410521136522085`
  - fixed families:
    - `EO_FX.lin_err_mean = 3.0498805390193284e-16`
    - `EC_FX.lin_err_mean = 2.9483925735467206e-16`
- bounded implication:
  - `lin_err_mean` cleanly separates `AD` from `FX` inside this family

### Negative-control sign suppression works
- bounded read:
  - all control-axis sign gaps collapse to floating-point noise:
    - `EC_AD.CTRL_delta_deltaH_absmean = 7.49454751730605e-18`
    - `EC_FX.CTRL_delta_deltaH_absmean = 5.082197683525802e-18`
    - `EO_AD.CTRL_delta_deltaH_absmean = 0.0`
    - `EO_FX.CTRL_delta_deltaH_absmean = 2.7755575615628914e-17`
  - the noncommuting test axis still leaves small but nonzero sign gaps
- bounded implication:
  - the control does what the runner says it should do, without removing the family-level topology4 signals

### Energy-open vs energy-closed split
- bounded read:
  - `EO_FX` carries the largest absolute energy-shift magnitude:
    - `TEST_plus_deltaH_absmean = 0.11991500306420856`
    - `TEST_minus_deltaH_absmean = 0.12085347037148786`
  - `EC_*` families keep `deltaH_absmean` near `0.0266`
  - `EC_*` families carry the largest entropy increase:
    - `EC_FX.TEST_plus_dS_mean = 0.11986406370809063`
    - `EC_AD.TEST_plus_dS_mean = 0.11237919801950716`
- bounded implication:
  - the current channelgrid family separates energy-shift magnitude from entropy-shift magnitude across topology4 quadrants

### Top-level visibility relation
- comparison anchors:
  - `SIM_CATALOG_v1.3.md:59,69,76,77`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:54-89`
- bounded read:
  - the repo-held top-level evidence pack admits the neighboring topology4 terrain8 surface:
    - `S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1`
  - the pack does not admit the current local SIM_ID:
    - `S_SIM_AXIS12_TOPOLOGY4_CHANNELGRID_V1`
  - the catalog lists both surfaces in the same topology4 strip
- bounded implication:
  - the current clean channelgrid pair is catalog-visible but not repo-top admitted, while the neighboring terrain8 surface is admitted

## 4) Comparison Anchors
- comparison sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis12_topology4_channelfamily_terrain8_seam__v1/MANIFEST.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1.json`
- relevant anchors:
  - `SIM_CATALOG_v1.3.md:59,69,76,77`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:54-89`
  - `BATCH_sims_axis12_topology4_channelfamily_terrain8_seam__v1/MANIFEST.json`
- bounded comparison read:
  - the prior batch preserved the terrain8 admission seam under a different runner hash
  - the current family is the clean local topology4 pair adjacent to that seam
  - together, the two batches preserve both the admitted terrain8 artifact and the unadmitted channelgrid contract without merging them

## 5) Source-Class Read
- Best classification:
  - standalone local topology4 channelgrid family with a clean runner/result pairing and explicit test-vs-control sign contract
- Not best classified as:
  - a repo-top admitted surface
  - the admitted terrain8 topology4 surface
  - a seam batch
- Theory-facing vs executable-facing split:
  - executable-facing:
    - current runner measures topology4 families under test and control axes
    - negative-control commuting behavior is explicit and works
  - theory-facing:
    - adaptive families carry the convexity/nonlinearity signal
    - energy-open and energy-closed families trade off deltaH magnitude vs entropy increase
  - evidence-facing:
    - local evidence is explicit in the runner contract
    - repo-top evidence-pack admission remains absent for the current SIM_ID
- possible downstream consequence:
  - later residual work should mark the residual paired-family campaign complete after this batch and move to the remaining runner-only, result-only, diagnostic, and hygiene classes

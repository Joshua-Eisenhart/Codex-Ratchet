# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_axis12_topology4_channelgrid_family__v1`
Extraction mode: `SIM_AXIS12_TOPOLOGY4_CHANNELGRID_PASS`

## T1) The current local pair is clean and source-matched, but the repo-held evidence pack still admits only the neighboring terrain8 topology4 surface
- source markers:
  - `run_axis12_topology4_channelgrid_v1.py:199-209`
  - `results_axis12_topology4_channelgrid_v1.json:1-72`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:54-89`
- tension:
  - the current runner and result pair match cleanly on SIM_ID and schema
  - the repo-held evidence pack omits `S_SIM_AXIS12_TOPOLOGY4_CHANNELGRID_V1`
  - the same topology4 strip in the evidence pack admits `S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1`
- preserved read:
  - keep local pairing quality distinct from repo-top admission status
- possible downstream consequence:
  - later summaries should not equate clean local pairing with top-level admission

## T2) The negative control suppresses sign sensitivity to numerical noise, but the test axis still leaves small nonzero sign gaps
- source markers:
  - `run_axis12_topology4_channelgrid_v1.py:127-181`
  - `results_axis12_topology4_channelgrid_v1.json:1-72`
- tension:
  - control gaps are near zero:
    - `EO_FX.CTRL_delta_deltaH_absmean = 2.7755575615628914e-17`
    - `EO_AD.CTRL_delta_deltaH_absmean = 0.0`
  - test gaps remain nonzero:
    - `EO_FX.TEST_delta_deltaH_absmean = -0.0009384673072792976`
    - `EO_AD.TEST_delta_deltaH_absmean = -0.0009138345998696978`
- preserved read:
  - the control behaves correctly without removing the test-axis sign effect entirely
- possible downstream consequence:
  - later summaries should preserve both the success of the control and the small residual sign sensitivity on the test axis

## T3) Adaptive families carry the axis2 nonlinearity signal, while fixed families are effectively linear
- source markers:
  - `results_axis12_topology4_channelgrid_v1.json:3-55`
- tension:
  - `AD` families:
    - `EO_AD.lin_err_mean = 0.01302066155298634`
    - `EC_AD.lin_err_mean = 0.023410521136522085`
  - `FX` families:
    - `EO_FX.lin_err_mean = 3.0498805390193284e-16`
    - `EC_FX.lin_err_mean = 2.9483925735467206e-16`
- preserved read:
  - `lin_err_mean` is effectively a clean discriminator between adaptive and fixed topology4 quadrants in this family
- possible downstream consequence:
  - later summaries should preserve axis2 nonlinearity as the strongest clean split in the current pair

## T4) Energy-open families dominate absolute energy-shift magnitude, while energy-closed families dominate entropy increase
- source markers:
  - `results_axis12_topology4_channelgrid_v1.json:3-55`
- tension:
  - `EO_FX` has the largest `deltaH_absmean`:
    - `TEST_minus_deltaH_absmean = 0.12085347037148786`
  - `EC_FX` and `EC_AD` have the largest `dS_mean` values:
    - `EC_FX.TEST_minus_dS_mean = 0.1200742885995791`
    - `EC_AD.TEST_minus_dS_mean = 0.11277223516534254`
- preserved read:
  - energy-shift magnitude and entropy increase do not peak in the same quadrant
- possible downstream consequence:
  - later summaries should not collapse topology4 behavior into one scalar notion of “strongest family”

## T5) The current topology4 channelgrid family and the prior terrain8 seam share a naming neighborhood, but encode different axes entirely
- source markers:
  - `BATCH_sims_axis12_topology4_channelfamily_terrain8_seam__v1/MANIFEST.json`
  - `results_axis12_topology4_channelgrid_v1.json:1-72`
- tension:
  - the prior batch preserved a terrain-by-sign-by-direction admission seam
  - the current pair measures topology4 quadrants with explicit test/control axes and no terrain grid
- preserved read:
  - keep the neighboring topology4 families distinct despite shared labels
- possible downstream consequence:
  - later summaries should not merge the channelgrid contract into the terrain8 seam batch

## T6) This batch closes the residual paired-family campaign, but other residual classes still remain
- source markers:
  - residual inventory tracking in the intake surface
  - confirmation that `BATCH_sims_axis12_topology4_channelgrid_family__v1` was the only missing paired-family batch
- tension:
  - paired-family intake is now complete
  - runner-only, result-only, diagnostic, and hygiene residual classes are still not exhausted
- preserved read:
  - completion of one residual class does not imply closure of the whole sims residual inventory
- possible downstream consequence:
  - future work should shift from paired families to the remaining residual classes rather than pretending the entire closure audit is finished

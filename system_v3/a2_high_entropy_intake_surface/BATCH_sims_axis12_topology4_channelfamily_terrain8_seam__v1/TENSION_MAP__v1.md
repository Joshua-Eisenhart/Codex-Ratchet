# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_axis12_topology4_channelfamily_terrain8_seam__v1`
Extraction mode: `SIM_AXIS12_TOPOLOGY4_CHANNELFAMILY_TERRAIN8_SEAM_PASS`

## T1) The repo-held evidence pack directly admits the selected terrain8 surface under the current runner hash, but the current runner names a different SIM_ID and a different result file
- source markers:
  - `run_axis12_topology4_channelfamily_suite_v2.py:1-11`
  - `run_axis12_topology4_channelfamily_suite_v2.py:193-211`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:54-89`
- tension:
  - the current runner says it produces:
    - `results_axis12_topology4_channelfamily_suite_v2.json`
    - `S_SIM_AXIS12_TOPOLOGY4_CHANNELFAMILY_SUITE_V2`
  - the repo-held evidence pack admits:
    - `results_S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1.json`
    - `S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1`
  - both point to the same code hash `be1a8c714b57ebfe98559d14237d85b258f760f5db2691f10b3f778660edcb12`
- preserved read:
  - keep provenance continuity distinct from present-day output-contract continuity
- possible downstream consequence:
  - later summaries should not present this as a clean runner/result pair

## T2) The current local result and the admitted terrain8 surface are structurally incompatible despite sharing one runner hash
- source markers:
  - `results_axis12_topology4_channelfamily_suite_v2.json:1-37`
  - `results_S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1.json:1-78`
- tension:
  - the current local result stores:
    - four topology4 families with `deltaH_absmean`, `deltaH_absmax`, `min_eig_min`, `dS_mean`, `lin_err_mean`
  - the admitted terrain8 surface stores:
    - `16` terrain/sign/direction cells with `entropy_mean` and `purity_mean`
- preserved read:
  - same-hash provenance does not imply same output schema or same measured phenomenon
- possible downstream consequence:
  - later summaries should keep the local topology4-family surface and the admitted terrain8 surface separate

## T3) The current runner is framed around topology4 channel families, but the admitted surface is organized by terrain, sign, and direction
- source markers:
  - `run_axis12_topology4_channelfamily_suite_v2.py:8-11`
  - `results_S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1.json:1-78`
- tension:
  - the current runner's named families are:
    - `EO_FX`
    - `EO_AD`
    - `EC_FX`
    - `EC_AD`
  - the admitted surface's named cells are:
    - `Se_sign...`
    - `Ne_sign...`
    - `Ni_sign...`
    - `Si_sign...`
- preserved read:
  - the admitted artifact is not just a renamed reformatting of the current local result
- possible downstream consequence:
  - later summaries should preserve the topology4-family vs terrain8-endpoint distinction

## T4) The admitted terrain8 surface has real sign-pattern structure, but the current local topology4 result does not expose that axis at all
- source markers:
  - `results_S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1.json:1-78`
  - `results_axis12_topology4_channelfamily_suite_v2.json:1-37`
- tension:
  - in the admitted surface:
    - `Se` improves under sign `+1`
    - `Ne` worsens under sign `+1`
    - `Si` worsens strongly under sign `+1`
  - the current local topology4 result has no terrain-by-sign axis to express that pattern
- preserved read:
  - the admitted surface contains sign-sensitive terrain ordering that is invisible in the current local contract
- possible downstream consequence:
  - later summaries should not infer terrain sign behavior from the local topology4 result alone

## T5) The evidence-pack tokenization differs from the admitted JSON keys even when the output hash matches exactly
- source markers:
  - `results_S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1.json:1-78`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:54-89`
- tension:
  - selected JSON keys use forms like:
    - `Ne_sign-1_DOWN`
  - evidence-pack metric names use forms like:
    - `Ne_sign_1_DOWN_entropy_mean`
- preserved read:
  - exact output admission still coexists with a naming-layer rewrite in the evidence pack
- possible downstream consequence:
  - later summaries should preserve token-format drift rather than silently normalize it away

## T6) The following topology4 channelgrid pair stays separate even though the current seam already spans two topology4 surface types
- source markers:
  - raw folder order placing `run_axis12_topology4_channelgrid_v1.py` after the current runner
  - existence of `results_axis12_topology4_channelgrid_v1.json`
- tension:
  - the current batch already preserves a seam between topology4-family and terrain8-endpoint surfaces
  - the adjacent topology4 channelgrid pair still remains out of batch
- preserved read:
  - keep adjacent topology4 families separate even when the current seam is already cross-surface
- possible downstream consequence:
  - future work should continue pair-by-pair at `run_axis12_topology4_channelgrid_v1.py`

# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / SOURCE-BOUND DISTILLATE
Batch: `BATCH_sims_terrain8_sign_suite_family__v1`
Extraction mode: `SIM_TERRAIN8_SIGN_SUITE_PASS`

## Distillate D1
- strongest source-bound read:
  - `run_terrain8_sign_suite.py` and `results_terrain8_sign_suite.json` form one bounded standalone terrain-only sign family
- supporting anchors:
  - raw-folder position
  - one runner plus one paired result surface

## Distillate D2
- strongest source-bound read:
  - the local terrain suite isolates sign sensitivity without Stage16, Axis0 AB, or Topology4 machinery
- supporting anchors:
  - one-qubit repeated-cycle contract
  - eight final terrain/sign mean metrics

## Distillate D3
- strongest source-bound read:
  - repo-top Terrain8 evidence currently points to a different family:
    - `S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1`
  - not the current local `S_SIM_TERRAIN8_SIGN_SUITE`
- supporting anchors:
  - negative search for `S_SIM_TERRAIN8_SIGN_SUITE`
  - positive evidence block at `SIM_EVIDENCE_PACK_autogen_v2.txt:54-89`

## Distillate D4
- evidence assumptions extracted:
  - catalog presence includes the local terrain suite and the adjacent `ultra2` macro bundle
  - repo-top evidence presence includes the Topology4 Terrain8 descendant only
  - the local terrain suite is stronger as a stored executable/result pair than as an admitted top-level evidence surface
- supporting anchors:
  - `SIM_CATALOG_v1.3.md:13,59,77,115,128,146-147`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:54-89`

## Distillate D5
- runtime expectations extracted:
  - the current runner uses `256` random states, `64` cycles, one axis unitary, and one terrain channel per pass
  - `Se` stays the purest / lowest-entropy terrain
  - `Ne` stays the most mixed / highest-entropy terrain
  - `Ni` carries the strongest sign effect
- supporting anchors:
  - current runner contract
  - current result metrics

## Distillate D6
- failure modes extracted:
  - conflating the local terrain suite with the Topology4 Terrain8 descendant because of shared naming
  - overstating sign sensitivity as if all terrains responded equally
  - merging the adjacent `ultra2` composite bundle into this terrain-only family
- supporting anchors:
  - tension items `T1` through `T5`

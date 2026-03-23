# A2-2 REFINED CANDIDATES

## Candidate 1: AXIS12_HARDEN_V1_RESULT_ONLY_SHELL

- status: `A2_2_CANDIDATE`
- type: `result-only residual shell`
- claim:
  - `results_axis12_paramsweep_v1.json`, `results_axis12_altchan_v1.json`, and `results_axis12_negctrl_swap_v1.json` form the first bounded `v1` result-only orphan triplet reopened from the deferred harden strip
- source lineage:
  - parent batch: `BATCH_sims_axis12_harden_v1_result_orphan_triplet__v1`
  - parent basis: cluster A, distillate D1, candidates C1-C3
- retained boundary:
  - source membership stays at the three stored `v1` result surfaces only

## Candidate 2: PRODUCER_LINKED_RESULT_ONLY_BOUNDARY

- status: `A2_2_CANDIDATE`
- type: `runner-result seam packet`
- claim:
  - the triplet remains result-only in source membership while still being explicitly defined by the deferred `run_axis12_harden_triple_v1.py` producer contract, so bounded source membership and producer linkage must be preserved together
- source lineage:
  - parent basis: clusters A and E, tension T1, distillates D1 and D5, candidate C2
- retained contradiction marker:
  - result-only boundary survives
  - producer-side coupling remains explicit

## Candidate 3: PARAMSWEEP_V1_SIGNAL_WITH_SPLIT_PEAKS

- status: `A2_2_CANDIDATE`
- type: `dynamic signal packet`
- claim:
  - `paramsweep_v1` is the only surface in the triplet with a clear stored `seni` partition signal, and its strongest partition separation and strongest absolute entropy occur on different rows, so the surface must not be flattened into one scalar “best row”
- source lineage:
  - parent basis: cluster B, tension T2, distillate D2, candidate C3
- retained contradiction marker:
  - partition peak survives
  - absolute entropy peak survives
  - they do not coincide

## Candidate 4: ALTCHAN_V1_SCHEMA_SAME_SIGNAL_COLLAPSE

- status: `A2_2_CANDIDATE`
- type: `alternate-channel collapse packet`
- claim:
  - `altchan_v1` uses the same outer schema as `paramsweep_v1` but nearly annihilates the discriminative signal and reaches exact max mixing on stronger rows, so same schema does not imply corroborating behavior
- source lineage:
  - parent basis: cluster C, tension T3, distillate D3
- retained contradiction marker:
  - schema continuity survives
  - signal continuity does not

## Candidate 5: NEGCTRL_SWAP_V1_OBSERVATIONAL_INERTIA

- status: `A2_2_CANDIDATE`
- type: `control packet`
- claim:
  - `negctrl_swap_v1` is a structurally present swapped-flag control surface, but on this four-sequence lattice its stored boolean pattern is observationally unchanged relative to the original flags, so it should not be described as a visible reversal
- source lineage:
  - parent basis: cluster D, tension T4, distillate D4, candidate C5
- retained contradiction marker:
  - control naming survives
  - visible per-sequence reversal does not

## Candidate 6: MIXED_TRIPLET_SCHEMA_AND_V2_BOUNDARY

- status: `A2_2_CANDIDATE`
- type: `bundle fence packet`
- claim:
  - the `v1` triplet is coherent by producer contract but internally heterogeneous, mixing two full dynamic surfaces with one purely combinatorial control, and it must stay separate from the later fully dynamic `v2` successor triplet
- source lineage:
  - parent basis: tension T6, distillate D6, candidate C6
- retained boundary:
  - do not merge the `v2` orphan triplet into this `v1` packet

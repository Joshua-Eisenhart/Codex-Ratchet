# A2-2 REFINED CANDIDATES

## Candidate 1: AXIS12_HARDEN_V2_RESULT_ONLY_SHELL

- status: `A2_2_CANDIDATE`
- type: `result-only residual shell`
- claim:
  - `results_axis12_paramsweep_v2.json`, `results_axis12_altchan_v2.json`, and `results_axis12_negctrl_label_v2.json` form the bounded successor `v2` result-only orphan triplet reopened from the deferred harden strip
- source lineage:
  - parent batch: `BATCH_sims_axis12_harden_v2_result_orphan_triplet__v1`
  - parent basis: cluster A, distillate D1, candidates C1-C3
- retained boundary:
  - source membership stays at the three stored `v2` result surfaces only

## Candidate 2: PRODUCER_LINKED_RESULT_ONLY_SUCCESSOR_BOUNDARY

- status: `A2_2_CANDIDATE`
- type: `runner-result seam packet`
- claim:
  - the triplet remains result-only in source membership while still being explicitly emitted by the deferred `run_axis12_harden_v2_triple.py` producer contract, so bounded source membership and producer linkage must stay preserved together
- source lineage:
  - parent basis: clusters A and E, tension T1, distillate D5, candidate C2
- retained contradiction marker:
  - result-only boundary survives
  - producer-side coupling remains explicit

## Candidate 3: PARAMSWEEP_V2_CONTINUITY_WITH_WEAKROW_DRIFT

- status: `A2_2_CANDIDATE`
- type: `dynamic successor packet`
- claim:
  - `paramsweep_v2` preserves the strong high-parameter `seni` split from `v1`, but the weakest parameter rows drift materially upward, so the successor relation is neither "identical" nor "wholly different"
- source lineage:
  - parent basis: cluster B, tension T2, distillate D2
- retained contradiction marker:
  - high-parameter continuity survives
  - weak-row drift also survives

## Candidate 4: ALTCHAN_V2_NEAR_ZERO_COLLAPSE

- status: `A2_2_CANDIDATE`
- type: `alternate-channel collapse packet`
- claim:
  - `altchan_v2` keeps the same compressed schema as `paramsweep_v2` but collapses to exact zero on all medium and high rows, while the remaining weak-row residuals are too small to treat the sign flip as theory-bearing structure
- source lineage:
  - parent basis: cluster C, tension T3, distillate D3, candidate C3
- retained contradiction marker:
  - schema continuity survives
  - meaningful signal continuity does not

## Candidate 5: NEGCTRL_LABEL_V2_DYNAMIC_INVERSION

- status: `A2_2_CANDIDATE`
- type: `control rewrite packet`
- claim:
  - `negctrl_label_v2` is not a no-op or combinatorial swap control; it is a real dynamic successor surface with mostly negative `dS`, partially inverting the base-channel discriminator instead of nulling it out
- source lineage:
  - parent basis: cluster D, tension T4, distillate D4, candidate C5
- retained contradiction marker:
  - negative-control naming survives
  - inert-control interpretation does not

## Candidate 6: COMPRESSED_SUCCESSOR_SCHEMA_FENCE

- status: `A2_2_CANDIDATE`
- type: `schema and version boundary packet`
- claim:
  - the `v2` triplet is more schema-homogeneous than `v1` because all three surfaces are row-summary dynamics, but the compression removes `by_seq` transparency, so this packet must stay separate from the fuller `v1` triplet and cannot answer sequence-level questions the stored schema no longer contains
- source lineage:
  - parent basis: tension T5, distillate D6, candidate C4
- retained boundary:
  - do not merge the compressed `v2` triplet back into the fuller `v1` result packet

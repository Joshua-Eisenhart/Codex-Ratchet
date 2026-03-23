# A2_2_SIM_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / INTERMEDIATE CANDIDATE SUMMARY
Batch: `BATCH_sims_axis12_harden_v2_result_orphan_triplet__v1`
Extraction mode: `SIM_AXIS12_HARDEN_V2_RESULT_ORPHAN_PASS`

## Candidate Summary C1
- proposal-only reading:
  - this is the correct next residual batch because the prior `v1` result-only batch explicitly deferred these three `v2` results next
- supporting anchors:
  - prior `v1` orphan batch manifest
  - current source membership

## Candidate Summary C2
- proposal-only reading:
  - the bounded family should stay at three stored `v2` result surfaces and not be merged back into either the runner-only batch or the `v1` triplet
- supporting anchors:
  - current source membership
  - current comparison anchors

## Candidate Summary C3
- proposal-only reading:
  - the strongest interpretation is “compressed successor triplet where base survives, alt collapses, and control becomes mostly inverted dynamic rerun”
- supporting anchors:
  - current `paramsweep_v2`
  - current `altchan_v2`
  - current `negctrl_label_v2`

## Candidate Summary C4
- proposal-only quarantine:
  - do not infer sequence-level causal structure from this batch, because the `v2` surfaces no longer store `by_seq` details
- supporting anchors:
  - current `v2` row-only schema

## Candidate Summary C5
- proposal-only quarantine:
  - do not describe `negctrl_label_v2` as equivalent to `negctrl_swap_v1`, because the third surface changed from combinatorial label swap to dynamic relabeled-channel rerun
- supporting anchors:
  - current `v2` control surface
  - prior `v1` orphan batch manifest

## Candidate Summary C6
- proposal-only next-step note:
  - if residual work continues, the next step should leave the harden strip and process the next remaining result-only orphan beginning with `results_axis0_boundary_bookkeep_v1.json`, while keeping diagnostic and hygiene residue separate
- supporting anchors:
  - current deferred-next-source decision

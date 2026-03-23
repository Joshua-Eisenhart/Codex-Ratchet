# A2_2_SIM_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / INTERMEDIATE CANDIDATE SUMMARY
Batch: `BATCH_sims_axis12_harden_v1_result_orphan_triplet__v1`
Extraction mode: `SIM_AXIS12_HARDEN_V1_RESULT_ORPHAN_PASS`

## Candidate Summary C1
- proposal-only reading:
  - this is the correct next residual batch because the prior harden runner strip explicitly deferred these three `v1` results first
- supporting anchors:
  - prior runner-only batch manifest
  - current source membership

## Candidate Summary C2
- proposal-only reading:
  - the bounded family should stay at three stored `v1` result surfaces and leave the `v2` orphan triplet for the next pass
- supporting anchors:
  - current source membership
  - deferred next-source decision

## Candidate Summary C3
- proposal-only reading:
  - the strongest interpretation is “base-channel axis12 signal survives, alternate-channel signal collapses, swapped-flag control is observationally inert”
- supporting anchors:
  - current `paramsweep_v1`
  - current `altchan_v1`
  - current `negctrl_swap_v1`

## Candidate Summary C4
- proposal-only quarantine:
  - do not treat the catalog listing as full admission, because the catalog names the filenames but not the local SIM_IDs and the evidence pack omits the triplet entirely
- supporting anchors:
  - catalog filename hits
  - evidence-pack omission

## Candidate Summary C5
- proposal-only quarantine:
  - do not overread the negative control as a meaningful visible flip on the current sequence set, because the swapped booleans are sequence-by-sequence unchanged
- supporting anchors:
  - current base flags
  - current swapped flags

## Candidate Summary C6
- proposal-only next-step note:
  - if residual work continues, the next step should process the `v2` orphan triplet at `results_axis12_paramsweep_v2.json`, `results_axis12_altchan_v2.json`, and `results_axis12_negctrl_label_v2.json`, while keeping diagnostic and hygiene residue separate
- supporting anchors:
  - current deferred-next-source decision

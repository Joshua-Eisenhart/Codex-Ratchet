# A2_2_SIM_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / INTERMEDIATE CANDIDATE SUMMARY
Batch: `BATCH_sims_axis12_harden_runner_strip__v1`
Extraction mode: `SIM_AXIS12_HARDEN_RUNNER_STRIP_PASS`

## Candidate Summary C1
- proposal-only reading:
  - this is the correct next residual batch because the paired-family campaign is already complete and the closure audit isolated these two harden runners as the remaining runner-only strip
- supporting anchors:
  - prior paired-family completion
  - closure audit manifest

## Candidate Summary C2
- proposal-only reading:
  - the bounded family should stay at two source members:
    - `run_axis12_harden_triple_v1.py`
    - `run_axis12_harden_v2_triple.py`
  - the six declared result surfaces should remain deferred to the result-only residual class
- supporting anchors:
  - current source membership
  - closure audit manifest

## Candidate Summary C3
- proposal-only reading:
  - the strongest interpretation is “axis12 harden runner strip with explicit but unsynchronized runner/result class split”
- supporting anchors:
  - current write contracts
  - current closure-audit relation

## Candidate Summary C4
- proposal-only quarantine:
  - do not treat top-level catalog/evidence omission as proof that the harden strip is unimportant, because the scripts define six explicit SIM_IDs and six explicit output filenames
- supporting anchors:
  - current runner evidence sections
  - top-level omission checks

## Candidate Summary C5
- proposal-only quarantine:
  - do not collapse `v1` and `v2` into one interchangeable harden script, because the third family changes from swapped-flag control to relabeled-channel rerun and the storage contracts change as well
- supporting anchors:
  - current `v1` and `v2` bodies

## Candidate Summary C6
- proposal-only next-step note:
  - if residual work continues, the next step should process the axis12 result-only orphan strip beginning with `results_axis12_paramsweep_v1.json`, `results_axis12_altchan_v1.json`, and `results_axis12_negctrl_swap_v1.json`, while keeping diagnostic and hygiene residue separate
- supporting anchors:
  - current deferred-next-source decision

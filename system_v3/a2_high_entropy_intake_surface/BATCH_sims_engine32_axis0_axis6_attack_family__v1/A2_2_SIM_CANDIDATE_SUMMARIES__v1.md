# A2_2_SIM_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / INTERMEDIATE CANDIDATE SUMMARY
Batch: `BATCH_sims_engine32_axis0_axis6_attack_family__v1`
Extraction mode: `SIM_ENGINE32_ATTACK_PASS`

## Candidate Summary C1
- proposal-only reading:
  - this is the correct next raw-order batch because `run_engine32_axis0_axis6_attack.py` and `results_engine32_axis0_axis6_attack.json` form one self-contained executable/result family
- supporting anchors:
  - batch source membership

## Candidate Summary C2
- proposal-only reading:
  - the strongest executable-facing claim here is a loop-orientation split, not a generic Axis0 effect
- supporting anchors:
  - `results_engine32_axis0_axis6_attack.json`

## Candidate Summary C3
- proposal-only reading:
  - one reusable pattern from this batch is “full result lattice in JSON, compressed delta-only evidence in sidecar”
- supporting anchors:
  - `run_engine32_axis0_axis6_attack.py:219-232`
  - `results_engine32_axis0_axis6_attack.json:1-689`

## Candidate Summary C4
- proposal-only quarantine:
  - do not read the family as AB-coupled Axis0 evidence from this batch alone; the script explicitly narrows it to a one-qubit proxy
- supporting anchors:
  - `run_engine32_axis0_axis6_attack.py:111-121`

## Candidate Summary C5
- proposal-only quarantine:
  - do not merge adjacent `full_axis_suite` into this batch; it is a cross-axis sampler with six blocks and different descendant naming
- supporting anchors:
  - `run_full_axis_suite.py:224-253`
  - `results_full_axis_suite.json:1-36`

## Candidate Summary C6
- proposal-only next-step note:
  - the next bounded sims batch should start at `run_full_axis_suite.py`, pair it with `results_full_axis_suite.json`, and read it as a cross-axis sampler/precursor family against the current standalone descendants it appears to anticipate
- supporting anchors:
  - adjacent-family comparison in this batch

# A2_2_SIM_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / INTERMEDIATE CANDIDATE SUMMARY
Batch: `BATCH_sims_axis4_p03_core_harness_family__v1`
Extraction mode: `SIM_AXIS4_CORE_PASS`

## Candidate Summary C1
- proposal-only reading:
  - this batch is the correct Axis4 core intake unit because it starts at the first unprocessed Axis4 source and captures the full currently evidenced P03 harness/result family
- supporting anchors:
  - batch source membership and comparison anchor

## Candidate Summary C2
- proposal-only reading:
  - one reusable Axis4 pattern from this batch is “same semantic family, duplicate harnesses, divergent evidence sidecar contracts”
- supporting anchors:
  - `axis4_seq_cycle_sim.py:247-263`
  - `run_axis4_sims.py:215-229`

## Candidate Summary C3
- proposal-only reading:
  - the cleanest current executable-facing Axis4 claim is not about all sequence effects, but about polarity ordering:
    - `+` branch stable across P03 sequences
    - `-` branch sequence-sensitive
- supporting anchors:
  - all four P03 result JSONs

## Candidate Summary C4
- proposal-only reading:
  - the strongest provenance claim here is that the stored P03 results and the top-level evidence pack line up under the `axis4_seq_cycle_sim.py` hash
- supporting anchors:
  - four P03 result files
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:111-183`

## Candidate Summary C5
- proposal-only quarantine:
  - do not treat `run_axis4_sims.py` as either dead code or authoritative code from this batch alone
- supporting anchors:
  - duplicate-harness evidence in this batch

## Candidate Summary C6
- proposal-only next-step note:
  - the next bounded Axis4 batch should process `run_axis4_seq01_both_dirs.py`, `run_axis4_seq02_both_dirs.py`, `run_axis4_seq03_seq04_both_dirs.py`, `run_axis4_type2_all_seq_both_dirs.py`, and their paired result files as the directional-suite family
- supporting anchors:
  - deferred same-family sources listed in this batch

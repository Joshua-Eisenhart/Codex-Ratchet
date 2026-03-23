# A2_2_SIM_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / INTERMEDIATE CANDIDATE SUMMARY
Batch: `BATCH_sims_axis4_directional_suite_family__v1`
Extraction mode: `SIM_AXIS4_DIRECTIONAL_PASS`

## Candidate Summary C1
- proposal-only reading:
  - this is the correct next Axis4 intake unit because it starts at the first deferred directional-suite source and includes both the executable-facing runners/results and the adjacent aggregate sibling
- supporting anchors:
  - batch source membership and comparison anchors

## Candidate Summary C2
- proposal-only reading:
  - the strongest executable-facing claim here is branch-specific:
    - plus branch depends on direction but not on sequence or type
    - minus branch depends on sequence, direction, and type
- supporting anchors:
  - all four executable result files in this batch
  - shared polarity logic in the four runner scripts

## Candidate Summary C3
- proposal-only reading:
  - the strongest theory-facing compression claim is that `S_SIM_AXIS4_SEQ_ALL_BIDIR_V1` reproduces the minus branch of the directional runners across T1 and T2
- supporting anchors:
  - `results_S_SIM_AXIS4_SEQ_ALL_BIDIR_V1.json`
  - all four executable result files in this batch

## Candidate Summary C4
- proposal-only quarantine:
  - do not treat the top-level evidence pack as proof that the current directional runner files produced the stored directional results
- supporting anchors:
  - runner hashes in this batch
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:418-662`

## Candidate Summary C5
- proposal-only quarantine:
  - do not treat `S_SIM_AXIS4_SEQ_ALL_BIDIR_V1` as a full-family summary because it drops the plus branch and compresses multiple executable surfaces into one theory-facing artifact
- supporting anchors:
  - `results_S_SIM_AXIS4_SEQ_ALL_BIDIR_V1.json`
  - all four executable result files in this batch

## Candidate Summary C6
- proposal-only next-step note:
  - the next bounded sims batch should resume raw folder order at `run_batch_v3.py` and pair it with its nearest stored result surface before deciding whether neighboring suite files belong in the same family
- supporting anchors:
  - deferred next raw-folder-order source in this batch

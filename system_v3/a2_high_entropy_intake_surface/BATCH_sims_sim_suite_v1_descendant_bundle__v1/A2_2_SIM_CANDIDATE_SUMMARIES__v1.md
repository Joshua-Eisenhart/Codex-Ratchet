# A2_2_SIM_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / INTERMEDIATE CANDIDATE SUMMARY
Batch: `BATCH_sims_sim_suite_v1_descendant_bundle__v1`
Extraction mode: `SIM_SUITE_V1_BUNDLE_PASS`

## Candidate Summary C1
- proposal-only reading:
  - this is the correct next raw-order batch because `run_sim_suite_v1.py` is the next unprocessed entrypoint and directly names ten descendant result outputs in its `main()`
- supporting anchors:
  - `run_sim_suite_v1.py:568-623`

## Candidate Summary C2
- proposal-only reading:
  - the bounded family should include the bundle runner plus the ten descendant result files it explicitly writes
- supporting anchors:
  - batch source membership

## Candidate Summary C3
- proposal-only reading:
  - the bundle is executable-facingly coherent, but provenance-facingly mixed
- supporting anchors:
  - evidence-pack code-hash split across emitted descendants

## Candidate Summary C4
- proposal-only quarantine:
  - do not claim that the current `run_sim_suite_v1.py` hash is the repo-top evidenced producer path for Axis0, Axis12, Axis4, Stage16, or Negctrl V2 descendants
- supporting anchors:
  - current hash matches and evidence-pack blocks in this batch

## Candidate Summary C5
- proposal-only quarantine:
  - do not merge `run_sim_suite_v2_full_axes.py` into this batch just because its hash already appears in the evidence chain of one `v1` descendant
- supporting anchors:
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:318-323`
  - `run_sim_suite_v2_full_axes.py:423-450`

## Candidate Summary C6
- proposal-only next-step note:
  - the next bounded sims batch should start at `run_sim_suite_v2_full_axes.py`, pair it with the descendants it directly emits, and preserve the version/provenance seam against the `sim_suite_v1` bundle
- supporting anchors:
  - deferred next raw-folder-order source in this batch

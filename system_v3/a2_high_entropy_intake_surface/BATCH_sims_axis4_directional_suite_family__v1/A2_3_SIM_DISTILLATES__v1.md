# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / OUTER-CACHE DISTILLATE
Batch: `BATCH_sims_axis4_directional_suite_family__v1`
Extraction mode: `SIM_AXIS4_DIRECTIONAL_PASS`

## Distillate D1
- statement:
  - the current Axis4 directional suite is one bounded family of four runners, four paired executable result files, and one adjacent theory-facing aggregate sibling
- source anchors:
  - batch source membership
- possible downstream consequence:
  - later Axis4 intake can reference this as the full bidirectional family slice without reopening the prior P03 core harness batch

## Distillate D2
- statement:
  - the plus branch is direction-specific but sequence-invariant, and it is numerically identical across Type-1 and Type-2
- source anchors:
  - all four executable result files in this batch
  - `run_axis4_seq01_both_dirs.py:101-104`
  - `run_axis4_seq02_both_dirs.py:102-103`
  - `run_axis4_seq03_seq04_both_dirs.py:101-103`
  - `run_axis4_type2_all_seq_both_dirs.py:101-103`
- possible downstream consequence:
  - later type or sequence claims should not attribute the plus-branch split to sequence order or `axis3_sign`

## Distillate D3
- statement:
  - the minus branch carries the real discriminating signal for this family: it varies by sequence, by direction, and by type, with reverse entropy lower than forward entropy in every stored case
- source anchors:
  - all four executable result files in this batch
- possible downstream consequence:
  - later theory-facing summaries should treat the minus branch as the main Axis4 directional evidence surface

## Distillate D4
- statement:
  - `results_S_SIM_AXIS4_SEQ_ALL_BIDIR_V1.json` is a minus-only compression layer over the executable result files, spanning both Type-1 and Type-2
- source anchors:
  - `results_S_SIM_AXIS4_SEQ_ALL_BIDIR_V1.json:1-200`
  - all four executable result files in this batch
- possible downstream consequence:
  - high-level summaries can use the aggregate sibling for compactness, but only if they mark the loss of plus-branch coverage

## Distillate D5
- statement:
  - the top-level evidence pack ties the directional suite to the earlier core hash `b741c60d...`, not to the hashes of the four directional runners
- source anchors:
  - runner hashes in this batch
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:418-662`
- possible downstream consequence:
  - provenance and authorship for the directional suite remain unresolved at the source level

## Distillate D6
- statement:
  - Type-2 has executable and aggregate presence but lacks per-direction top-level evidence-pack blocks in the current repo-held record
- source anchors:
  - `run_axis4_type2_all_seq_both_dirs.py:148-220`
  - `results_axis4_type2_all_seq_both_dirs.json:1-221`
  - `results_S_SIM_AXIS4_SEQ_ALL_BIDIR_V1.json:1-200`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:187-250`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:418-662`
- possible downstream consequence:
  - later claims about Type-2 certainty should preserve the difference between result presence and evidence-pack coverage

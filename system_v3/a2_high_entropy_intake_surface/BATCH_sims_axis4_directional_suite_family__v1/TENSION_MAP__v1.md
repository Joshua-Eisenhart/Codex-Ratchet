# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_axis4_directional_suite_family__v1`
Extraction mode: `SIM_AXIS4_DIRECTIONAL_PASS`

## T1) Directional runner hashes vs top-level evidence-pack hash
- source markers:
  - runner hashes in this batch
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:418-662`
- tension:
  - the four directional runner scripts have hashes `03dd8e6e...`, `a4c0e6ef...`, `1af5c548...`, and `e3295255...`
  - the repo-held evidence blocks for `S_SIM_AXIS4_SEQ01_FWD` through `S_SIM_AXIS4_SEQ04_REV` use code hash `b741c60d...`
- preserved read:
  - keep filename/result pairing and evidence-pack provenance separate; do not silently infer that the current directional runner files are the evidenced producers
- possible downstream consequence:
  - any later producer-path claim for the directional suite needs an explicit provenance audit

## T2) Direction-labeled evidence blocks are dual-direction packets
- source markers:
  - `run_axis4_seq01_both_dirs.py:180-184`
  - `run_axis4_seq02_both_dirs.py:185-189`
  - `run_axis4_seq03_seq04_both_dirs.py:199-205`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:418-662`
- tension:
  - the directional runners generate separate `FWD` and `REV` SIM_ID blocks
  - each stored evidence block in the top-level pack carries both `fwd_*` and `rev_*` metrics
- preserved read:
  - keep this as evidence-contract ambiguity, not as direction-specific proof
- possible downstream consequence:
  - later evidence consumers should not assume one evidence block equals one isolated direction

## T3) Aggregate bidirectional sibling is minus-only while executable results store both branches
- source markers:
  - all four executable result files in this batch
  - `results_S_SIM_AXIS4_SEQ_ALL_BIDIR_V1.json:1-200`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:187-250`
- tension:
  - the executable-facing result files store `plus` and `minus` for each direction
  - the aggregate sibling stores only `T1_fwd`, `T1_rev`, `T2_fwd`, and `T2_rev`, and those values match the runners' minus branch only
- preserved read:
  - keep the aggregate surface visible as a theory-facing compression, not as a complete family summary
- possible downstream consequence:
  - later high-level Axis4 summaries can understate the role of the plus branch if they lean only on the aggregate artifact

## T4) Type-2 is present in results and aggregate, but absent as per-direction top-level evidence
- source markers:
  - `run_axis4_type2_all_seq_both_dirs.py:148-220`
  - `results_axis4_type2_all_seq_both_dirs.json:1-221`
  - `results_S_SIM_AXIS4_SEQ_ALL_BIDIR_V1.json:1-200`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:187-250`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:418-662`
- tension:
  - the repo holds a full Type-2 runner and Type-2 paired result file
  - the aggregate sibling carries Type-2 metrics
  - no per-direction Type-2 SIM_ID blocks were found in the top-level evidence pack
- preserved read:
  - do not flatten this into “Type-2 is fully evidenced” or “Type-2 is absent”; both claims overstate the source record
- possible downstream consequence:
  - later evidence-grade claims should distinguish executable presence, aggregate presence, and top-level evidence-pack presence

## T5) `axis3_sign` is advertised as the type switch, but the plus branch is numerically unchanged
- source markers:
  - `run_axis4_seq01_both_dirs.py:101-104`
  - `run_axis4_type2_all_seq_both_dirs.py:101-103`
  - all result files in this batch
- tension:
  - Type-1 and Type-2 are separated by `axis3_sign`
  - the polarity `+` path bypasses the unitary and the stored plus-branch metrics are identical across Type-1 and Type-2 by direction
- preserved read:
  - keep the sign switch as partially inert in the current stored metric space rather than speaking about a uniform type split
- possible downstream consequence:
  - later type-family descriptions should specify which branch the sign switch actually changes

## T6) Output granularity is inconsistent inside one family
- source markers:
  - `run_axis4_seq01_both_dirs.py:171-184`
  - `run_axis4_seq02_both_dirs.py:175-189`
  - `run_axis4_seq03_seq04_both_dirs.py:195-205`
  - `run_axis4_type2_all_seq_both_dirs.py:203-220`
- tension:
  - Seq01 and Seq02 each get dedicated result files
  - Seq03 and Seq04 are merged into one Type-1 result file
  - all four Type-2 sequences are merged into one larger result file
- preserved read:
  - keep the storage asymmetry visible rather than implying one uniform per-sequence artifact policy
- possible downstream consequence:
  - later automation or evidence stitching must account for three different batching granularities inside this one family

## T7) Family bundling crosses a previously processed adjacent Axis4 file
- source markers:
  - raw `simpy/` order around `run_axis4_seq03_seq04_both_dirs.py`
  - prior batch `BATCH_sims_axis4_p03_core_harness_family__v1`
- tension:
  - `run_axis4_sims.py` sits between `run_axis4_seq03_seq04_both_dirs.py` and `run_axis4_type2_all_seq_both_dirs.py` in raw folder order
  - this batch still keeps the directional suite together
- preserved read:
  - keep the bundling choice explicit as an intake decision, not as evidence that raw order stopped mattering
- possible downstream consequence:
  - the next batch should resume raw-folder-order progression cleanly after this directional family

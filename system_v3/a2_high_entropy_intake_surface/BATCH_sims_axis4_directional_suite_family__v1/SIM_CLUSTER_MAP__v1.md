# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_axis4_directional_suite_family__v1`
Extraction mode: `SIM_AXIS4_DIRECTIONAL_PASS`

## Cluster S1: Type-1 bidirectional sequence family
- source anchors:
  - `run_axis4_seq01_both_dirs.py:140-146`
  - `run_axis4_seq02_both_dirs.py:142-149`
  - `run_axis4_seq03_seq04_both_dirs.py:154-158`
  - `results_axis4_seq01_both_dirs.json:1-63`
  - `results_axis4_seq03_seq04_both_dirs.json:1-107`
- cluster members:
  - `S_SIM_AXIS4_SEQ01_FWD`
  - `S_SIM_AXIS4_SEQ01_REV`
  - `S_SIM_AXIS4_SEQ02_FWD`
  - `S_SIM_AXIS4_SEQ02_REV`
  - `S_SIM_AXIS4_SEQ03_FWD`
  - `S_SIM_AXIS4_SEQ03_REV`
  - `S_SIM_AXIS4_SEQ04_FWD`
  - `S_SIM_AXIS4_SEQ04_REV`
- compressed read:
  - the Type-1 directional suite holds one shared knob block and preserves forward/reverse results for all four sequence orders, but spreads them across three runner scripts and three result files
- possible downstream consequence:
  - later Axis4 summaries should treat Seq03 and Seq04 as being stored under a different result granularity than Seq01 and Seq02

## Cluster S2: Type-2 all-sequence family
- source anchors:
  - `run_axis4_type2_all_seq_both_dirs.py:148-160`
  - `run_axis4_type2_all_seq_both_dirs.py:203-220`
  - `results_axis4_type2_all_seq_both_dirs.json:1-221`
- cluster members:
  - `S_SIM_AXIS4_SEQ01_T2_FWD`
  - `S_SIM_AXIS4_SEQ01_T2_REV`
  - `S_SIM_AXIS4_SEQ02_T2_FWD`
  - `S_SIM_AXIS4_SEQ02_T2_REV`
  - `S_SIM_AXIS4_SEQ03_T2_FWD`
  - `S_SIM_AXIS4_SEQ03_T2_REV`
  - `S_SIM_AXIS4_SEQ04_T2_FWD`
  - `S_SIM_AXIS4_SEQ04_T2_REV`
- compressed read:
  - the Type-2 runner is a full eight-surface sweep with the same fixed knobs as Type-1 except `axis3_sign=-1`
- possible downstream consequence:
  - this is the cleanest executable-facing Type-2 presence in the current Axis4 folder slice

## Cluster S3: Shared polarity kernel and inert plus-branch type switch
- source anchors:
  - `run_axis4_seq01_both_dirs.py:101-104`
  - `run_axis4_seq02_both_dirs.py:102-103`
  - `run_axis4_seq03_seq04_both_dirs.py:101-103`
  - `run_axis4_type2_all_seq_both_dirs.py:101-103`
  - all result files in this batch
- cluster members:
  - polarity `+`
  - polarity `-`
  - `axis3_sign`
  - forward and reverse direction metrics
- compressed read:
  - the code path for polarity `+` applies terrain then pinch and does not use the unitary sign, so Type-1 and Type-2 plus-branch results are numerically identical by direction
- possible downstream consequence:
  - later type-family interpretations should not claim plus-branch separation from the sign switch

## Cluster S4: Minus-branch directional and sequence sensitivity
- source anchors:
  - `results_axis4_seq01_both_dirs.json:9-56`
  - `results_axis4_seq02_both_dirs.json:9-56`
  - `results_axis4_seq03_seq04_both_dirs.json:13-100`
  - `results_axis4_type2_all_seq_both_dirs.json:13-214`
- cluster members:
  - Type-1 minus branch
  - Type-2 minus branch
  - forward vs reverse
  - Seq01 through Seq04
- compressed read:
  - minus-branch entropy and purity vary by both sequence and direction for both type families; reverse minus entropy is lower than forward minus entropy for every stored sequence in both Type-1 and Type-2
- possible downstream consequence:
  - the directional suite's real discriminating signal lives on the minus branch rather than on the plus branch

## Cluster S5: Theory-facing aggregate compression surface
- source anchors:
  - `results_S_SIM_AXIS4_SEQ_ALL_BIDIR_V1.json:1-200`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:187-250`
- cluster members:
  - `S_SIM_AXIS4_SEQ_ALL_BIDIR_V1`
  - `T1_fwd`
  - `T1_rev`
  - `T2_fwd`
  - `T2_rev`
- compressed read:
  - the aggregate sibling and its evidence-pack block compress the family into a minus-only T1/T2 summary with one params object
- possible downstream consequence:
  - later theory-facing summaries should mark this surface as a compression layer, not as a full replacement for the executable result files

## Cluster S6: Evidence-pack producer mismatch
- source anchors:
  - runner hashes in this batch
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:418-662`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:187-250`
- cluster members:
  - directional runner hashes:
    - `03dd8e6e...`
    - `a4c0e6ef...`
    - `1af5c548...`
    - `e3295255...`
  - evidence-pack hash `b741c60d...`
  - aggregate output hash `e088e8ce...`
- compressed read:
  - the top-level evidence pack binds both the per-direction Type-1 surfaces and the aggregate bidirectional surface to the earlier core harness hash, not to the hashes of the directional runner scripts in this batch
- possible downstream consequence:
  - provenance claims for this family must preserve the mismatch instead of silently treating filename pairing as proof of authorship

# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / SOURCE-BOUND DISTILLATE
Batch: `BATCH_sims_axis12_seq_constraints_family__v1`
Extraction mode: `SIM_AXIS12_SEQ_CONSTRAINTS_PASS`

## Distillate D1
- strongest source-bound read:
  - `run_axis12_seq_constraints.py` and `results_axis12_seq_constraints.json` form one clean residual paired family
- supporting anchors:
  - one runner plus one paired result
  - prior residual pair ordering

## Distillate D2
- strongest source-bound read:
  - the local family stores both axis1-style within-pair counts and axis2-style adjacency nonmembership counts
- supporting anchors:
  - `seni_within_*`
  - `nesi_within_*`
  - `seta_bad_*`
  - `setb_bad_*`

## Distillate D3
- strongest source-bound read:
  - the stored local constraints split the four sequences into a balanced pair (`SEQ01/SEQ02`) and an asymmetric pair (`SEQ03/SEQ04`)
- supporting anchors:
  - balanced counts for `SEQ01/SEQ02`
  - asymmetric extremes for `SEQ03/SEQ04`

## Distillate D4
- evidence assumptions extracted:
  - the local suite SIM_ID is omitted from the repo-held top-level evidence pack
  - the repo-held pack admits `S_SIM_AXIS12_SEQ_CONSTRAINTS_V2` under the same runner hash
  - the current family is stronger as a local full constraint surface than as a repo-top admitted artifact
- supporting anchors:
  - `SIM_EVIDENCE_PACK_autogen_v2.txt`
  - shared code hash `45a914e43629cbd18486c08e8fe4716488bc39b91c9222ccb4ad267d86c6a725`

## Distillate D5
- runtime expectations extracted:
  - one run covers:
    - four sequences
    - wraparound cycle edges
    - four metric families
    - one local evidence block
  - the next residual paired family begins at `run_axis12_topology4_channelfamily_suite_v2.py`
- supporting anchors:
  - current runner contract
  - residual ordering

## Distillate D6
- failure modes extracted:
  - mistaking the local surface for the repo-top `V2` descendant because the code hash matches
  - dropping the local axis2 counts because the repo-top descendant does not keep them
  - treating `SEQ03` and `SEQ04` as one undifferentiated asymmetric class
  - assuming the balanced pair is semantically resolved just because the current counts do not separate it
- supporting anchors:
  - tension items `T1` through `T5`

# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_axis12_channel_realization_suite_family__v1`
Extraction mode: `SIM_AXIS12_CHANNEL_REALIZATION_SUITE_PASS`

## T1) The local suite SIM_ID is omitted from the repo-held top-level evidence pack, but `V4` is admitted under the same code hash
- source markers:
  - `run_axis12_channel_realization_suite.py:146-177`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:30-35`
- tension:
  - the current runner emits local evidence for `S_SIM_AXIS12_CHANNEL_REALIZATION_SUITE`
  - the repo-held evidence pack omits that SIM_ID
  - the repo-held evidence pack instead admits `S_SIM_AXIS12_CHANNEL_REALIZATION_V4`
  - the admitted `V4` block carries the current runner hash `5e6358240110019fd266675f9ff1e520c7822114a811d597b630a62aa9efd6f5`
- preserved read:
  - keep code-hash continuity distinct from SIM_ID continuity
- possible downstream consequence:
  - later summaries should not treat the local suite as repo-top admitted just because `V4` shares its runner hash

## T2) The axis12 edge flags partition the sequences into two classes, but do not determine the full endpoint ordering inside each class
- source markers:
  - `run_axis12_channel_realization_suite.py:120-144`
  - `results_axis12_channel_realization_suite.json:2-58`
- tension:
  - `SEQ01` and `SEQ02` both have `SENI = 0`, `NESI = 0`, yet `SEQ02` is better on both entropy and purity
  - `SEQ03` and `SEQ04` both have `SENI = 1`, `NESI = 1`, yet they still differ measurably
- preserved read:
  - edge flags are a coarse classifier, not a complete predictor of endpoint outcome
- possible downstream consequence:
  - later summaries should not overread the boolean edge layer as a full ordering model

## T3) Axis3 sign is globally directional even though the suite is about axis12 structural differences
- source markers:
  - `results_axis12_channel_realization_suite.json:26-58`
- tension:
  - for all four sequences, sign `+1` stores lower entropy and higher purity than sign `-1`
  - the largest sign gap lands on `SEQ02`:
    - `delta_entropy_plus_minus = -0.007024243077661474`
    - `delta_purity_plus_minus = 0.0067567787785349775`
- preserved read:
  - the axis3 sign layer materially steers the endpoint realization inside an axis12-labeled family
- possible downstream consequence:
  - later summaries should keep the sign layer explicit instead of treating the family as purely axis12-structural

## T4) The local suite is a fixed-parameter endpoint snapshot, but the repo-top `V4` descendant is a broad grid scan
- source markers:
  - `run_axis12_channel_realization_suite.py:97-145`
  - `results_S_SIM_AXIS12_CHANNEL_REALIZATION_V4.json:1-596`
- tension:
  - the local suite fixes:
    - `gamma = 0.12`
    - `p = 0.08`
    - `q = 0.10`
    - `theta = 0.07`
  - the repo-top `V4` surface spans a `3 x 3 x 3 x 3` grid over `gamma`, `p`, `q`, and `theta`
- preserved read:
  - the descendant is not just a renamed copy of the local suite; it is a broader sweep family under the same code hash
- possible downstream consequence:
  - later summaries should preserve the fixed-snapshot vs grid-scan difference

## T5) The family is catalog-visible and locally evidenced, but adjacent runner-only harden surfaces still stay out of batch
- source markers:
  - `SIM_CATALOG_v1.3.md:62,137`
  - raw folder order showing `run_axis12_harden_triple_v1.py` and `run_axis12_harden_v2_triple.py` between the current source and the next paired family
- tension:
  - the current family is locally complete and catalog-visible
  - the adjacent harden scripts are raw-order neighbors
  - they remain excluded because they are runner-only residuals, not paired families
- preserved read:
  - keep paired-family intake separate from runner-only residuals even when names cluster tightly
- possible downstream consequence:
  - future work should move next to `run_axis12_seq_constraints.py` while leaving runner-only harden surfaces for their own residual class

## T6) `SEQ02` is best under both signs even though it shares the no-edge class with `SEQ01`
- source markers:
  - `results_axis12_channel_realization_suite.json:26-58`
- tension:
  - `SEQ02` is best on both entropy and purity under sign `+1` and sign `-1`
  - `SEQ01` shares the same edge-flag class but never outranks it
- preserved read:
  - the family carries a stable `SEQ02` advantage that is not explained by the coarse edge partition alone
- possible downstream consequence:
  - later summaries should preserve `SEQ02` as the strongest local endpoint channel realization in this fixed-parameter suite

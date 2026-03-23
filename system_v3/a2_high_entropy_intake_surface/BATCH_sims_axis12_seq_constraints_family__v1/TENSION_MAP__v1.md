# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_axis12_seq_constraints_family__v1`
Extraction mode: `SIM_AXIS12_SEQ_CONSTRAINTS_PASS`

## T1) The local suite SIM_ID is omitted from the repo-held top-level evidence pack, but `V2` is admitted under the same code hash
- source markers:
  - `run_axis12_seq_constraints.py:79-99`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:39-50`
- tension:
  - the current runner emits local evidence for `S_SIM_AXIS12_SEQ_CONSTRAINTS`
  - the repo-held evidence pack omits that SIM_ID
  - the repo-held evidence pack instead admits `S_SIM_AXIS12_SEQ_CONSTRAINTS_V2`
  - the admitted `V2` block carries the current runner hash `45a914e43629cbd18486c08e8fe4716488bc39b91c9222ccb4ad267d86c6a725`
- preserved read:
  - keep code-hash continuity distinct from SIM_ID continuity
- possible downstream consequence:
  - later summaries should not treat the local surface as repo-top admitted just because `V2` shares its runner hash

## T2) The local surface stores four constraint layers, but the repo-top `V2` descendant keeps only a narrower edge subset
- source markers:
  - `run_axis12_seq_constraints.py:61-76`
  - `results_axis12_seq_constraints.json:1-45`
  - `results_S_SIM_AXIS12_SEQ_CONSTRAINTS_V2.json:1-24`
- tension:
  - the local surface stores:
    - `seta_bad_*`
    - `setb_bad_*`
    - `seni_within_*`
    - `nesi_within_*`
  - the repo-top `V2` descendant stores only:
    - `nesi_edges`
    - `seni_edges`
- preserved read:
  - the descendant is not just a renamed copy of the local surface; it is a narrower metric contract
- possible downstream consequence:
  - later summaries should preserve the local axis2 counts instead of collapsing them into the descendant edge subset

## T3) The shared code hash does not preserve the same stored `seni` behavior
- source markers:
  - `results_axis12_seq_constraints.json:2-19`
  - `results_S_SIM_AXIS12_SEQ_CONSTRAINTS_V2.json:1-24`
- tension:
  - the local surface stores:
    - `seni_within_SEQ03 = 1`
    - `seni_within_SEQ04 = 1`
  - the repo-top `V2` descendant stores:
    - `SEQ03_seni_edges = 0`
    - `SEQ04_seni_edges = 0`
- preserved read:
  - same-hash provenance coexists with a real behavioral divergence in stored `seni` outcomes
- possible downstream consequence:
  - later summaries should preserve this contradiction instead of normalizing one surface into the other

## T4) `SEQ03` and `SEQ04` share both within-pair activations, yet split on opposite axis2 failures
- source markers:
  - `results_axis12_seq_constraints.json:2-19`
- tension:
  - both `SEQ03` and `SEQ04` store:
    - `seni_within = 1`
    - `nesi_within = 1`
  - but their worst axis2 failures differ:
    - `SEQ03`: `seta_bad = 4`, `setb_bad = 2`
    - `SEQ04`: `seta_bad = 2`, `setb_bad = 4`
- preserved read:
  - the asymmetric pair shares the same axis1 profile but diverges on axis2 orientation
- possible downstream consequence:
  - later summaries should keep `SEQ03` and `SEQ04` distinct rather than treating them as one duplicated asymmetric class

## T5) `SEQ01` and `SEQ02` are both balanced on axis2, but the family still does not collapse them into one sequence
- source markers:
  - `results_axis12_seq_constraints.json:2-19`
- tension:
  - `SEQ01` and `SEQ02` both store:
    - `seta_bad = 2`
    - `setb_bad = 2`
    - `seni_within = 0`
    - `nesi_within = 0`
- preserved read:
  - the local constraint family keeps both balanced sequences distinct even though the current metrics do not separate them
- possible downstream consequence:
  - later summaries should note that the local metric layer cannot distinguish the balanced pair on the stored counts alone

## T6) The residual paired-family campaign continues cleanly, but the next topology4 paired family still stays out of batch
- source markers:
  - `BATCH_sims_axis12_channel_realization_suite_family__v1/MANIFEST.json`
  - raw folder order placing `run_axis12_topology4_channelfamily_suite_v2.py` after the current source
- tension:
  - the current paired-family campaign advances cleanly
  - the next topology4 paired family remains deferred
- preserved read:
  - keep adjacent paired families separate even when both belong to the axis12 strip
- possible downstream consequence:
  - future work should continue pair-by-pair at `run_axis12_topology4_channelfamily_suite_v2.py`

# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_axis12_harden_v2_result_orphan_triplet__v1`
Extraction mode: `SIM_AXIS12_HARDEN_V2_RESULT_ORPHAN_PASS`

## T1) The current triplet is result-only in source membership, but it is directly defined by the deferred runner-only harden strip
- source markers:
  - `BATCH_sims_axis12_harden_runner_strip__v1/MANIFEST.json`
  - `run_axis12_harden_v2_triple.py:171-249`
  - current three result surfaces
- tension:
  - the current batch is bounded to stored JSON surfaces only
  - those surfaces are explicitly emitted by the deferred `run_axis12_harden_v2_triple.py` contract
- preserved read:
  - keep the runner/result class split without pretending the two halves are unrelated
- possible downstream consequence:
  - later summaries should preserve both bounded source membership and producer-side linkage

## T2) `paramsweep_v2` preserves the high-parameter `seni` split from `v1`, but the weakest parameter rows drift materially upward while stronger rows stay nearly identical
- source markers:
  - `results_axis12_paramsweep_v2.json:1-75`
  - comparison to `BATCH_sims_axis12_harden_v1_result_orphan_triplet__v1/MANIFEST.json`
- tension:
  - high and medium parameter rows differ from `v1` only at numerical-noise scale
  - weak parameter drift relative to `v1` is larger:
    - sign `+1` `delta_dS = 0.00018284670210544363`
    - sign `-1` `delta_dS = 6.575172043210564e-05`
- preserved read:
  - the successor base surface is both continuous with `v1` and measurably shifted at the weakest point
- possible downstream consequence:
  - later summaries should not flatten the `v1`→`v2` relation into either “same” or “completely different”

## T3) `altchan_v2` keeps the same compressed schema as `paramsweep_v2`, but it collapses to near-zero and even flips the weak-row sign relative to `v1`
- source markers:
  - `results_axis12_altchan_v2.json:1-75`
  - comparison to `BATCH_sims_axis12_harden_v1_result_orphan_triplet__v1/MANIFEST.json`
- tension:
  - medium and high parameter rows are exact zeros
  - weak rows keep only tiny residuals:
    - sign `+1` `dS = -7.83910577561997e-08`
    - sign `-1` `dS = -4.605091896703328e-08`
  - `v1` weak-row `dS` values were tiny positive
- preserved read:
  - the alternate-channel successor remains functionally collapsed, and the surviving weak-row sign is not stable enough to treat as theory-bearing structure
- possible downstream consequence:
  - later summaries should not overread the sign flip as meaningful if its magnitude stays at near-zero scale

## T4) `negctrl_label_v2` is called a negative control, but it is a real dynamic rerun and mostly inverts the base-channel discriminator polarity rather than eliminating it
- source markers:
  - `results_axis12_negctrl_label_v2.json:1-75`
  - `run_axis12_harden_v2_triple.py:195-205`
- tension:
  - the surface is dynamic, not combinatorial
  - `dS` is negative on `5` of `6` rows
  - one weak-row exception stays positive
  - strongest negative response:
    - `dS = -0.0007217115914999184`
    - sign `+1`
    - `gamma = 0.12`, `p = 0.08`, `q = 0.1`
- preserved read:
  - the successor control changes the sign structure rather than simply nulling it out
- possible downstream consequence:
  - later summaries should not describe the third `v2` surface as a no-op control

## T5) The `v2` triplet is more schema-homogeneous than `v1`, but it loses sequence-level transparency
- source markers:
  - current three `v2` results
  - comparison to current `v1` orphan batch manifest
- tension:
  - `v1` mixed:
    - two full dynamic surfaces with `by_seq`
    - one combinatorial control
  - `v2` unified:
    - three dynamic row-summary surfaces
    - no `by_seq` information
- preserved read:
  - storage homogeneity improves while interpretability declines
- possible downstream consequence:
  - later summaries should not pretend the `v2` triplet can answer sequence-level questions that the stored schema no longer contains

## T6) The top-level catalog lists all three `v2` filenames, but neither the catalog nor the evidence pack admits their local SIM_IDs
- source markers:
  - `SIM_CATALOG_v1.3.md:61,63,66`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt`
- tension:
  - filename alias visibility in catalog:
    - yes
  - SIM_ID visibility in catalog:
    - no
  - filename or SIM_ID visibility in evidence pack:
    - no
- preserved read:
  - keep filename-level catalog visibility separate from evidence-pack admission
- possible downstream consequence:
  - later summaries should not mistake catalog presence for full evidence admission

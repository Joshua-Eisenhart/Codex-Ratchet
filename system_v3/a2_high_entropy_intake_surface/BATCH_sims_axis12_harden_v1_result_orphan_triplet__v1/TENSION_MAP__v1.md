# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_axis12_harden_v1_result_orphan_triplet__v1`
Extraction mode: `SIM_AXIS12_HARDEN_V1_RESULT_ORPHAN_PASS`

## T1) The current triplet is result-only in source membership, but it is directly defined by the deferred runner-only harden strip
- source markers:
  - `BATCH_sims_axis12_harden_runner_strip__v1/MANIFEST.json`
  - `run_axis12_harden_triple_v1.py:221-323`
  - current three result surfaces
- tension:
  - the current batch is bounded to stored JSON surfaces only
  - those surfaces are explicitly emitted by the deferred `run_axis12_harden_triple_v1.py` contract
- preserved read:
  - keep the runner/result class split without pretending the two halves are unrelated
- possible downstream consequence:
  - later summaries should preserve both bounded source membership and producer-side linkage

## T2) `paramsweep_v1` carries a real `seni` partition signal, but strongest partition separation and strongest absolute entropy do not occur on the same row
- source markers:
  - `results_axis12_paramsweep_v1.json:1-408`
- tension:
  - strongest stored partition gap:
    - `delta_entropy_seni1_minus_seni0 = 0.0025521238656023293`
    - `sign = +1`
    - `gamma = 0.12`, `p = 0.08`, `q = 0.1`
  - strongest absolute entropy:
    - `SEQ03`
    - `sign = -1`
    - `gamma = 0.08`, `p = 0.08`, `q = 0.08`
    - `vn_entropy_mean = 0.6637775258929544`
- preserved read:
  - partition strength and absolute entropy peak are not the same notion of “best” in this surface
- possible downstream consequence:
  - later summaries should not collapse the dynamic surface to one scalar ranking

## T3) `altchan_v1` uses the same outer lattice as `paramsweep_v1`, but it nearly annihilates the discriminative signal
- source markers:
  - `results_axis12_altchan_v1.json:1-408`
- tension:
  - `paramsweep_v1` mean `delta_entropy_seni1_minus_seni0`:
    - sign `+1`: `0.0013166644435990877`
    - sign `-1`: `0.0006575892864619052`
  - `altchan_v1` mean `delta_entropy_seni1_minus_seni0`:
    - sign `+1`: `3.3508485319799775e-08`
    - sign `-1`: `3.6372251432936764e-08`
  - stronger `altchan_v1` parameter points hit exact stored maximum mixing:
    - `vn_entropy_mean = 0.6931471805599454`
    - `purity_mean = 0.5`
- preserved read:
  - same schema does not imply same signal-bearing behavior
- possible downstream consequence:
  - later summaries should keep the alternate-channel result from being treated as corroboration of the base-channel separation

## T4) `negctrl_swap_v1` is named as a swapped-flag negative control, but on this exact four-sequence lattice the stored boolean pattern is observationally unchanged
- source markers:
  - `results_axis12_negctrl_swap_v1.json:1-27`
  - `results_axis12_paramsweep_v1.json:1-408`
- tension:
  - original dynamic-surface flags:
    - `SEQ01`, `SEQ02` are `(seni_within, nesi_within) = (0, 0)`
    - `SEQ03`, `SEQ04` are `(1, 1)`
  - swapped control flags:
    - `SEQ01`, `SEQ02` remain `(0, 0)`
    - `SEQ03`, `SEQ04` remain `(1, 1)`
- preserved read:
  - the control changes label semantics without producing an observable per-sequence boolean change here
- possible downstream consequence:
  - later summaries should not overstate this control as a visible structural reversal on the current sequence set

## T5) The top-level catalog lists all three result filenames, but neither the catalog nor the evidence pack admits their local SIM_IDs
- source markers:
  - `SIM_CATALOG_v1.3.md:60,64,65`
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

## T6) The triplet belongs together as one emitted `v1` bundle, but it mixes two full dynamic surfaces with one purely combinatorial control surface
- source markers:
  - current three result surfaces
  - `run_axis12_harden_triple_v1.py:221-323`
- tension:
  - `paramsweep_v1` and `altchan_v1` contain entropy and purity metrics
  - `negctrl_swap_v1` contains only swapped flags and bad-edge counters
- preserved read:
  - the bundle is coherent by producer contract, not by homogeneous metric schema
- possible downstream consequence:
  - later summaries should keep the internal heterogeneity explicit instead of pretending all three surfaces answer the same question

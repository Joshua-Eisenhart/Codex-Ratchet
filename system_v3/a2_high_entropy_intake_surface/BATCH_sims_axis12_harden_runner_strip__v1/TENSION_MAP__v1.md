# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_axis12_harden_runner_strip__v1`
Extraction mode: `SIM_AXIS12_HARDEN_RUNNER_STRIP_PASS`

## T1) The closure audit classifies the harden strip as runner-only, but the scripts themselves declare six emitted result surfaces that the same audit lists as result-only residuals
- source markers:
  - `BATCH_sims_residual_inventory_closure_audit__v1/MANIFEST.json`
  - `run_axis12_harden_triple_v1.py:4-13`
  - `run_axis12_harden_v2_triple.py:171-249`
- tension:
  - the closure audit keeps:
    - `run_axis12_harden_triple_v1.py`
    - `run_axis12_harden_v2_triple.py`
    in `runner_only_residuals`
  - the same closure audit separately lists:
    - `results_axis12_paramsweep_v1.json`
    - `results_axis12_altchan_v1.json`
    - `results_axis12_negctrl_swap_v1.json`
    - `results_axis12_paramsweep_v2.json`
    - `results_axis12_altchan_v2.json`
    - `results_axis12_negctrl_label_v2.json`
    in `result_only_residuals`
  - both scripts explicitly write those files
- preserved read:
  - keep the operational class split, but preserve that it is not semantically clean
- possible downstream consequence:
  - later summaries should not treat the runner-only and result-only strips as unrelated families

## T2) The harden strip defines six local SIM_IDs and explicit evidence blocks, but the repo-held top-level catalog and evidence pack omit the strip entirely
- source markers:
  - `run_axis12_harden_triple_v1.py:287-322`
  - `run_axis12_harden_v2_triple.py:209-249`
  - negative substring search in `SIM_CATALOG_v1.3.md`
  - negative substring search in `SIM_EVIDENCE_PACK_autogen_v2.txt`
- tension:
  - local SIM_IDs exist for:
    - `S_SIM_AXIS12_PARAMSWEEP_V1`
    - `S_SIM_AXIS12_ALTCHAN_V1`
    - `S_SIM_AXIS12_NEGCTRL_SWAP_V1`
    - `S_SIM_AXIS12_PARAMSWEEP_V2`
    - `S_SIM_AXIS12_ALTCHAN_V2`
    - `S_SIM_AXIS12_NEGCTRL_LABEL_V2`
  - repo-top catalog visibility is zero
  - repo-top evidence-pack visibility is zero
- preserved read:
  - explicit local evidence contracts do not imply catalog admission or evidence-pack admission
- possible downstream consequence:
  - later summaries should keep local producer explicitness separate from top-level visibility

## T3) `v1` and `v2` share the same axis12 lattice, but their storage contracts and third negative-control families are materially different
- source markers:
  - `run_axis12_harden_triple_v1.py:221-323`
  - `run_axis12_harden_v2_triple.py:171-249`
- tension:
  - `v1` stores full `by_seq` blocks plus summaries for the first two surfaces and a pure swapped-flag control for the third
  - `v2` stores only compressed discriminative rows and changes the third family into a relabeled-channel rerun
  - `v1` uses `num_states = 256`
  - `v2` uses `num_states = 512`
- preserved read:
  - `v2` is not just a rename or light hardening pass
- possible downstream consequence:
  - later summaries should not collapse `NEGCTRL_SWAP_V1` and `NEGCTRL_LABEL_V2` into one interchangeable control surface

## T4) Both scripts write the same `sim_evidence_pack.txt`, so sequential execution in one working directory would overwrite the earlier evidence surface
- source markers:
  - `run_axis12_harden_triple_v1.py:322-329`
  - `run_axis12_harden_v2_triple.py:248-251`
- tension:
  - both scripts name their evidence sink `sim_evidence_pack.txt`
  - result filenames are versioned and do not collide
  - the evidence-pack filename is not versioned and does collide
- preserved read:
  - the harden strip is locally executable, but its evidence emission is overwrite-prone across versions
- possible downstream consequence:
  - later runtime-facing interpretation should not assume both versions' evidence packs can coexist without path management

## T5) The harden strip is a bundled multi-SIM producer class, not an ordinary single-SIM runner family
- source markers:
  - `run_axis12_harden_triple_v1.py:221-323`
  - `run_axis12_harden_v2_triple.py:171-249`
- tension:
  - each script emits three result surfaces and three SIM_EVIDENCE blocks
  - the residual campaign is currently batching the strip at the runner level instead of at the emitted-result level
- preserved read:
  - keep producer-strip structure distinct from ordinary paired-family structure
- possible downstream consequence:
  - later result-only intake should reopen the six declared outputs as their own bounded residual class rather than retroactively forcing them into this runner-only batch

## T6) The six corresponding orphan result surfaces are clearly linked to this strip, but this batch must still keep them out of source membership to preserve residual-class separation
- source markers:
  - `BATCH_sims_residual_inventory_closure_audit__v1/MANIFEST.json`
  - filename inventory of `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson`
- tension:
  - the six declared result filenames are present in the repo-side result inventory
  - they belong to the next residual class, not this one
  - admitting them here would blur the residual-class boundary the closure audit established
- preserved read:
  - keep semantic coupling explicit while keeping source membership bounded
- possible downstream consequence:
  - the next pass should process the axis12 orphan result strip directly instead of treating the current runner-only batch as complete coverage of the harden family

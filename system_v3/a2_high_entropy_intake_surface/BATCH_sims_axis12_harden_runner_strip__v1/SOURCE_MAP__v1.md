# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_axis12_harden_runner_strip__v1`
Extraction mode: `SIM_AXIS12_HARDEN_RUNNER_STRIP_PASS`
Batch scope: residual runner-only axis12 harden producer strip centered on `run_axis12_harden_triple_v1.py` and `run_axis12_harden_v2_triple.py`, with the six declared orphan result surfaces deferred to the result-only residual class
Date: 2026-03-09

## 1) Batch Selection
- starting residual-priority source:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_harden_triple_v1.py`
- selected sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_harden_triple_v1.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_harden_v2_triple.py`
- reason for bounded family:
  - the closure audit identified these two adjacent scripts as the remaining runner-only residual strip after paired-family completion
  - both scripts are bundled multi-SIM producers rather than single-family runners
  - both scripts declare explicit output contracts for three result files plus one local `sim_evidence_pack.txt`
  - the six declared result filenames are already separated into the residual result-only class, so this batch keeps source membership runner-only and preserves that class split instead of smoothing it away
- comparison-only anchors read:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_residual_inventory_closure_audit__v1/MANIFEST.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_INDEX__v1.md`
- deferred next residual-priority source:
  - the axis12 result-only orphan strip beginning with:
    - `results_axis12_paramsweep_v1.json`
    - `results_axis12_altchan_v1.json`
    - `results_axis12_negctrl_swap_v1.json`

## 2) Source Membership
- Runner:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_harden_triple_v1.py`
  - sha256: `6dabd8879afc8a14900120a5a6d10130258d7043f6a2b9f342b7d04e94cc2570`
  - size bytes: `11183`
  - line count: `331`
  - source role: v1 axis12 harden triple runner producing base paramsweep, alternate-channel, and swapped-flag negative-control surfaces
- Runner:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_harden_v2_triple.py`
  - sha256: `08180eb2fb801fb57c7bd19b88e497420117df9e1e55dd2163892f0a8672a787`
  - size bytes: `9195`
  - line count: `253`
  - source role: v2 axis12 harden triple runner producing base paramsweep, alternate-channel, and relabeled-channel negative-control surfaces

## 3) Structural Map Of The Family
### Runner contract: `run_axis12_harden_triple_v1.py`
- anchors:
  - `run_axis12_harden_triple_v1.py:4-13`
  - `run_axis12_harden_triple_v1.py:221-323`
- source role:
  - one bundled producer strip with three emitted result files:
    - `results_axis12_paramsweep_v1.json`
    - `results_axis12_altchan_v1.json`
    - `results_axis12_negctrl_swap_v1.json`
  - one emitted evidence file:
    - `sim_evidence_pack.txt`
  - three local SIM_IDs:
    - `S_SIM_AXIS12_PARAMSWEEP_V1`
    - `S_SIM_AXIS12_ALTCHAN_V1`
    - `S_SIM_AXIS12_NEGCTRL_SWAP_V1`
- executable-facing read:
  - shared executable lattice:
    - `SEQ01` through `SEQ04`
    - `3` sweep points
    - axis3 signs `+1` and `-1`
    - `cycles = 64`
    - `theta = 0.07`
    - `num_states = 256`
  - `paramsweep_v1` and `altchan_v1` store full `by_seq` blocks plus discriminative summaries
  - `negctrl_swap_v1` is a pure combinatorial flag-swap control and does not rerun the state-evolution loop

### Runner contract: `run_axis12_harden_v2_triple.py`
- anchors:
  - `run_axis12_harden_v2_triple.py:136-249`
- source role:
  - one bundled successor strip with three emitted result files:
    - `results_axis12_paramsweep_v2.json`
    - `results_axis12_altchan_v2.json`
    - `results_axis12_negctrl_label_v2.json`
  - one emitted evidence file:
    - `sim_evidence_pack.txt`
  - three local SIM_IDs:
    - `S_SIM_AXIS12_PARAMSWEEP_V2`
    - `S_SIM_AXIS12_ALTCHAN_V2`
    - `S_SIM_AXIS12_NEGCTRL_LABEL_V2`
- executable-facing read:
  - shared executable lattice remains close to `v1`:
    - same `SEQ01` through `SEQ04`
    - same `3` sweep points
    - same axis3 sign set
    - same `cycles = 64`
    - same `theta = 0.07`
  - `num_states` increases to `512`
  - all three emitted surfaces are compressed to `rows` with `disc` summaries rather than full `by_seq` state summaries
  - `negctrl_label_v2` is not a pure flag swap; it reruns dynamics under a relabeled channel map

### Shared harden-strip relation
- anchors:
  - `run_axis12_harden_triple_v1.py:110-139`
  - `run_axis12_harden_v2_triple.py:87-135`
- bounded read:
  - both scripts use the same four-sequence axis12 lattice and the same edge-flag logic:
    - `seni_within`
    - `nesi_within`
    - `seta_bad`
    - `setb_bad`
  - both scripts define one bundled triple rather than one single SIM
  - both scripts write the same evidence-pack filename `sim_evidence_pack.txt`
- bounded implication:
  - the harden strip is a producer class with shared axis12 structure but divergent output compression and negative-control semantics

### Closure-audit split vs actual output contract
- comparison anchors:
  - `BATCH_sims_residual_inventory_closure_audit__v1/MANIFEST.json`
- bounded read:
  - the closure audit classifies:
    - `run_axis12_harden_triple_v1.py`
    - `run_axis12_harden_v2_triple.py`
    as `runner_only_residuals`
  - the same closure audit separately classifies these declared outputs as `result_only_residuals`:
    - `results_axis12_paramsweep_v1.json`
    - `results_axis12_altchan_v1.json`
    - `results_axis12_negctrl_swap_v1.json`
    - `results_axis12_paramsweep_v2.json`
    - `results_axis12_altchan_v2.json`
    - `results_axis12_negctrl_label_v2.json`
- bounded implication:
  - the closure-audit split is operationally useful but semantically incomplete; the runner-only strip and result-only strip are directly coupled by the scripts' own declared write contracts

### Top-level visibility relation
- comparison anchors:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
- bounded read:
  - the repo-held top-level catalog contains no mentions of:
    - `run_axis12_harden_triple_v1.py`
    - `run_axis12_harden_v2_triple.py`
    - any of the six harden-strip SIM_IDs
  - the repo-held top-level evidence pack also contains no mentions of the harden strip or its six SIM_IDs
- bounded implication:
  - the current batch is locally explicit at the runner level but invisible in the repo-top catalog/evidence surfaces

## 4) Comparison Anchors
- comparison sources:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_residual_inventory_closure_audit__v1/MANIFEST.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_INDEX__v1.md`
- relevant anchors:
  - `BATCH_sims_residual_inventory_closure_audit__v1/MANIFEST.json`
  - negative substring search in `SIM_CATALOG_v1.3.md` for both runner names and all six harden-strip SIM_IDs
  - negative substring search in `SIM_EVIDENCE_PACK_autogen_v2.txt` for both runner names and all six harden-strip SIM_IDs
- bounded comparison read:
  - the closure audit is the only repo-local surface that currently groups these two runners and their six corresponding orphan result filenames in one residual picture
  - the top-level sims inventory surfaces do not expose the harden strip at all
  - the ledger continuity now shifts from paired-family completion into runner-only residual intake

## 5) Source-Class Read
- Best classification:
  - residual runner-only axis12 harden producer strip with six declared but deferred result counterparts
- Not best classified as:
  - a clean paired family
  - a single-SIM runner
  - a catalog-visible or evidence-pack-visible sims family
- Theory-facing vs executable-facing split:
  - executable-facing:
    - both runners define concrete output contracts, sweep parameters, axis12 flags, and evidence-pack emission
    - `v2` raises `num_states` and changes the third control from flag swap to relabeled rerun
    - both runners share one overwrite-prone `sim_evidence_pack.txt`
  - theory-facing:
    - the harden strip is organized around axis12 combinatorics and how sequence-edge constraints separate entropy and purity summaries
    - `v1` preserves fuller per-sequence state summaries, while `v2` compresses to discriminative summaries
  - evidence-facing:
    - the scripts declare six local SIM_IDs and six output files
    - the repo-top catalog and evidence pack omit the strip entirely
    - the six declared result surfaces remain deferred to the next residual class rather than being merged into this batch
- possible downstream consequence:
  - the next residual pass should move to the axis12 result-only orphan strip and process the six declared harden outputs as their own source class without retroactively broadening this runner-only batch

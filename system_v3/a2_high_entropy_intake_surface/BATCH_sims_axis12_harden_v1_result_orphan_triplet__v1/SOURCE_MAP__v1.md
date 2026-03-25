# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_axis12_harden_v1_result_orphan_triplet__v1`
Extraction mode: `SIM_AXIS12_HARDEN_V1_RESULT_ORPHAN_PASS`
Batch scope: residual result-only axis12 harden `v1` triplet centered on `results_axis12_paramsweep_v1.json`, `results_axis12_altchan_v1.json`, and `results_axis12_negctrl_swap_v1.json`, with the runner-only harden strip preserved comparison-only
Date: 2026-03-09

## 1) Batch Selection
- starting residual-priority source:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_paramsweep_v1.json`
- selected sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_paramsweep_v1.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_altchan_v1.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_negctrl_swap_v1.json`
- reason for bounded family:
  - the prior runner-only batch explicitly deferred these three `v1` outputs next
  - all three surfaces are declared by one runner contract:
    - `run_axis12_harden_triple_v1.py`
  - the three surfaces belong together as the first result-only half of the harden strip
  - the parallel `v2` orphan triplet stays deferred so the `v1` and `v2` result contracts are not smoothed together
- comparison-only anchors read:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis12_harden_runner_strip__v1/MANIFEST.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_harden_triple_v1.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_INDEX__v1.md`
- deferred next residual-priority source:
  - the `v2` orphan triplet beginning with:
    - `results_axis12_paramsweep_v2.json`
    - `results_axis12_altchan_v2.json`
    - `results_axis12_negctrl_label_v2.json`

## 2) Source Membership
- Result surface:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_paramsweep_v1.json`
  - sha256: `08c6694c794d1a1e53668c814eba326a16f0051234d6578af3601ef23c7eae59`
  - size bytes: `13053`
  - line count: `408`
  - source role: full dynamic `v1` base-channel paramsweep surface
- Result surface:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_altchan_v1.json`
  - sha256: `a73210ee34762684d4ebb0aa41bf2852a8d014c160fad8810bf13390f5ce77ae`
  - size bytes: `12590`
  - line count: `408`
  - source role: full dynamic `v1` alternate-channel realization surface
- Result surface:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_negctrl_swap_v1.json`
  - sha256: `2689b869a4f997ab7d73ad3172bc5e82ffd2fe32c0b0e230b797374ad1341cf3`
  - size bytes: `528`
  - line count: `27`
  - source role: pure combinatorial `v1` swapped-flag negative-control surface

## 3) Structural Map Of The Family
### Result structure: `results_axis12_paramsweep_v1.json`
- anchors:
  - `results_axis12_paramsweep_v1.json:1-408`
  - `run_axis12_harden_triple_v1.py:221-241`
- source role:
  - dynamic base-channel surface with:
    - `6` rows
    - axis3 signs `+1` and `-1`
    - `3` parameter points
    - full `by_seq` blocks for `SEQ01` through `SEQ04`
    - per-row summary over the `seni_within` partition
- strongest bounded reads:
  - the `seni` partition is real and strengthens with harsher parameters
  - sign `+1` carries larger mean separation than sign `-1`
  - strongest stored partition gap:
    - `delta_entropy_seni1_minus_seni0 = 0.0025521238656023293`
    - at `sign = +1`, `gamma = 0.12`, `p = 0.08`, `q = 0.1`
  - strongest absolute entropy point is elsewhere:
    - `SEQ03`
    - `sign = -1`
    - `gamma = 0.08`, `p = 0.08`, `q = 0.08`
    - `vn_entropy_mean = 0.6637775258929544`
  - lowest stored entropy point:
    - `SEQ02`
    - `sign = +1`
    - `gamma = 0.12`, `p = 0.08`, `q = 0.1`
    - `vn_entropy_mean = 0.6331874849867805`
- bounded implication:
  - the base-channel result surface retains real axis12 separation, but strongest separation and strongest absolute entropy do not occur at the same parameter point

### Result structure: `results_axis12_altchan_v1.json`
- anchors:
  - `results_axis12_altchan_v1.json:1-408`
  - `run_axis12_harden_triple_v1.py:243-263`
- source role:
  - dynamic alternate-channel surface with the same outer lattice:
    - `6` rows
    - axis3 signs `+1` and `-1`
    - `3` parameter points
    - full `by_seq` blocks plus per-row summary
- strongest bounded reads:
  - the alternate-channel surface almost entirely erases sequence discrimination
  - at the two stronger parameter points, every row lands at exact stored maximum mixing:
    - `vn_entropy_mean = 0.6931471805599454`
    - `purity_mean = 0.5`
    - zero row-level entropy span across all four sequences
  - only the weakest parameter point retains any visible difference, and it is tiny:
    - max absolute `delta_entropy_seni1_minus_seni0 = 1.0911675429881029e-07`
- bounded implication:
  - this alternate realization uses the same result schema as `paramsweep_v1`, but it functionally destroys the axis12 discriminative signal

### Result structure: `results_axis12_negctrl_swap_v1.json`
- anchors:
  - `results_axis12_negctrl_swap_v1.json:1-27`
  - `run_axis12_harden_triple_v1.py:265-280`
- source role:
  - pure combinatorial negative-control surface with:
    - `4` `by_seq` entries
    - swapped `seni_within` / `nesi_within` labels
    - no entropy or purity metrics
- strongest bounded read:
  - the surface is observationally inert on this exact sequence set:
    - `SEQ01` and `SEQ02` remain `(0, 0)`
    - `SEQ03` and `SEQ04` remain `(1, 1)`
  - because the original flags already coincide sequence-by-sequence in the dynamic `v1` surfaces, swapping the labels changes names but not the stored boolean pattern
- bounded implication:
  - the control is structurally linked to the dynamic surfaces but does not create a meaningful visible permutation on the current four-sequence lattice

### Cross-surface relation inside the triplet
- comparison anchors:
  - `run_axis12_harden_triple_v1.py:221-323`
- bounded read:
  - `paramsweep_v1` and `altchan_v1` are homogeneous dynamic surfaces with identical schema
  - `negctrl_swap_v1` is a different class of artifact:
    - no dynamic metrics
    - only swapped booleans
  - the three surfaces still belong together because the runner emits them as one bundled `v1` triple
- bounded implication:
  - the current result-only batch is internally mixed between dynamic and combinatorial result types, and that mix should stay explicit

### Top-level visibility relation
- comparison anchors:
  - `SIM_CATALOG_v1.3.md:60,64,65`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt`
- bounded read:
  - the top-level catalog lists all three filenames:
    - `results_axis12_altchan_v1.json`
    - `results_axis12_negctrl_swap_v1.json`
    - `results_axis12_paramsweep_v1.json`
  - the catalog does not list their local SIM_ID strings
  - the repo-held top-level evidence pack omits both the filenames and the SIM_IDs
- bounded implication:
  - the triplet is catalog-visible only as filename aliases and remains wholly unadmitted at the top-level evidence-pack layer

## 4) Comparison Anchors
- comparison sources:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis12_harden_runner_strip__v1/MANIFEST.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_harden_triple_v1.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
- relevant anchors:
  - `BATCH_sims_axis12_harden_runner_strip__v1/MANIFEST.json`
  - `run_axis12_harden_triple_v1.py:221-323`
  - `SIM_CATALOG_v1.3.md:60,64,65`
- bounded comparison read:
  - the runner-only batch established the producer-side contract and deferred the current triplet as result-only
  - the current batch reopens the stored result behavior without broadening source membership back to the runner
  - the catalog retains only filename-level visibility, while the evidence pack retains no visibility at all

## 5) Source-Class Read
- Best classification:
  - residual result-only `v1` harden triplet linked to the runner-only harden strip but bounded to stored JSON surfaces
- Not best classified as:
  - a clean paired family
  - a homogeneous all-dynamic family
  - a top-level admitted sims family
- Theory-facing vs executable-facing split:
  - executable-facing:
    - the stored `paramsweep_v1` surface shows real partition separation under the base channel
    - the stored `altchan_v1` surface collapses almost completely to maximum mixing
    - the stored `negctrl_swap_v1` surface is purely combinatorial and observationally inert on the current sequence set
  - theory-facing:
    - the `seni` partition remains usable under the base channel but is nearly erased under the alternate channel
    - the strongest separation and the strongest absolute entropy do not align on the same row
  - evidence-facing:
    - the triplet is directly linked to the runner-only harden batch
    - top-level visibility is filename-only in the catalog and absent in the evidence pack
- possible downstream consequence:
  - the next residual result-only pass should process the `v2` harden triplet separately rather than collapsing `v1` and `v2`

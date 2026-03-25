# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / SIM-ONLY CLUSTER MAP
Batch: `BATCH_sims_axis12_harden_v1_result_orphan_triplet__v1`
Extraction mode: `SIM_AXIS12_HARDEN_V1_RESULT_ORPHAN_PASS`

## Cluster A
- cluster label:
  - core result-only triplet
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_paramsweep_v1.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_altchan_v1.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_negctrl_swap_v1.json`
- family role:
  - canonical source-bounded member set for this batch
- executable-facing read:
  - three stored results from one deferred `v1` producer strip
- tension anchor:
  - source membership is result-only even though the triplet remains directly coupled to the runner-only harden batch

## Cluster B
- cluster label:
  - base-channel dynamic surface
- members:
  - `results_axis12_paramsweep_v1.json`
  - `6` rows
  - `by_seq`
  - `summary`
- family role:
  - main dynamic evidence surface for the `v1` triplet
- executable-facing read:
  - real `seni`-partition separation
  - stronger effect under sign `+1`
- tension anchor:
  - strongest partition gap and strongest absolute entropy occur on different rows

## Cluster C
- cluster label:
  - alternate-channel collapse surface
- members:
  - `results_axis12_altchan_v1.json`
  - `6` rows
  - `by_seq`
  - `summary`
- family role:
  - dynamic alternate realization surface
- executable-facing read:
  - same outer schema as `paramsweep_v1`
  - near-total collapse to maximum mixing
- tension anchor:
  - same lattice, same shape, radically weaker discriminative signal

## Cluster D
- cluster label:
  - swapped-flag combinatorial control
- members:
  - `results_axis12_negctrl_swap_v1.json`
  - `seni_within_swapped`
  - `nesi_within_swapped`
  - `seta_bad`
  - `setb_bad`
- family role:
  - control-side result surface
- executable-facing read:
  - no entropy or purity data
  - boolean pattern matches the original flags on this sequence set
- tension anchor:
  - the named swap changes labels without changing observable per-sequence values

## Cluster E
- cluster label:
  - producer linkage and top-level omission
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis12_harden_runner_strip__v1/MANIFEST.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_harden_triple_v1.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
- family role:
  - comparison-only provenance and visibility cluster
- executable-facing read:
  - current triplet is the stored half of the deferred `v1` producer strip
  - catalog mentions filenames only
  - evidence pack omits the triplet entirely
- tension anchor:
  - producer-side explicitness and top-level omission coexist

## Cross-Cluster Read
- Cluster A is the only in-batch source family
- Cluster B carries the real dynamic axis12 signal
- Cluster C shows the alternate-channel collapse of that signal
- Cluster D shows a named negative control that is structurally present but observationally inert
- Cluster E preserves the linkage back to the runner-only strip and the top-level visibility seam

# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / SIM-ONLY CLUSTER MAP
Batch: `BATCH_sims_axis12_harden_v2_result_orphan_triplet__v1`
Extraction mode: `SIM_AXIS12_HARDEN_V2_RESULT_ORPHAN_PASS`

## Cluster A
- cluster label:
  - core result-only successor triplet
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_paramsweep_v2.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_altchan_v2.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_negctrl_label_v2.json`
- family role:
  - canonical source-bounded member set for this batch
- executable-facing read:
  - three stored successor surfaces from one deferred `v2` producer strip
- tension anchor:
  - source membership is result-only even though the triplet remains directly coupled to the runner-only harden batch

## Cluster B
- cluster label:
  - base-channel compressed surface
- members:
  - `results_axis12_paramsweep_v2.json`
  - `6` rows
  - `disc`
- family role:
  - main dynamic evidence surface for the `v2` triplet
- executable-facing read:
  - positive `dS` on all rows
  - strongest response at the harshest parameter point under sign `+1`
- tension anchor:
  - high-parameter behavior tracks `v1`, but weak-parameter rows drift materially

## Cluster C
- cluster label:
  - alternate-channel collapse surface
- members:
  - `results_axis12_altchan_v2.json`
  - `6` rows
  - `disc`
- family role:
  - dynamic alternate realization surface
- executable-facing read:
  - same compressed schema as `paramsweep_v2`
  - all medium and high parameter rows collapse to exact zero
- tension anchor:
  - storage parity with the base surface coexists with near-total signal collapse

## Cluster D
- cluster label:
  - relabeled-channel dynamic control
- members:
  - `results_axis12_negctrl_label_v2.json`
  - `6` rows
  - `disc`
- family role:
  - dynamic negative-control successor surface
- executable-facing read:
  - mostly negative `dS`
  - only one weak-row exception stays positive
- tension anchor:
  - the `v2` control is dynamic and partially inverted, not purely combinatorial

## Cluster E
- cluster label:
  - version seam and top-level omission
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis12_harden_v1_result_orphan_triplet__v1/MANIFEST.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis12_harden_runner_strip__v1/MANIFEST.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_harden_v2_triple.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
- family role:
  - comparison-only provenance and visibility cluster
- executable-facing read:
  - current triplet is the compressed successor half of the harden strip
  - the third surface changes class relative to `v1`
  - catalog mentions filenames only
  - evidence pack omits the triplet entirely
- tension anchor:
  - producer-side continuity, version drift, and top-level omission coexist

## Cross-Cluster Read
- Cluster A is the only in-batch source family
- Cluster B keeps the robust positive base-channel separation
- Cluster C shows alternate-channel collapse to near-zero
- Cluster D shows the successor control rewrite into a dynamic, mostly inverted surface
- Cluster E preserves the `v1`/`v2` seam and the top-level visibility seam without broadening the batch

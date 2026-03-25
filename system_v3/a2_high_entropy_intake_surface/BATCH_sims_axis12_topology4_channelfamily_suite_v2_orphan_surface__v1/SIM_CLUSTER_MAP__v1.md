# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / SIM-ONLY CLUSTER MAP
Batch: `BATCH_sims_axis12_topology4_channelfamily_suite_v2_orphan_surface__v1`
Extraction mode: `SIM_AXIS12_TOPOLOGY4_CHANNELFAMILY_SUITE_V2_ORPHAN_SURFACE_PASS`

## Cluster A
- cluster label:
  - core orphan surface
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_topology4_channelfamily_suite_v2.json`
- family role:
  - canonical source-bounded member set for this correction batch
- executable-facing read:
  - one compact topology4 local result surface
- tension anchor:
  - the surface was already read earlier, but only as a seam anchor and not as a direct member

## Cluster B
- cluster label:
  - topology4 family map
- members:
  - `EC_AD`
  - `EC_FX`
  - `EO_AD`
  - `EO_FX`
  - `lin_err_mean`
  - `deltaH_absmean`
  - `min_eig_min`
- family role:
  - local result-content cluster
- executable-facing read:
  - adaptive-vs-fixed and EC-vs-EO splits are both visible
- tension anchor:
  - the local topology4 summary is meaningful in its own right even though the earlier seam batch did not source-admit it

## Cluster C
- cluster label:
  - terrain8 admission seam anchor
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis12_topology4_channelfamily_terrain8_seam__v1/MANIFEST.json`
- family role:
  - comparison-only seam-preservation anchor
- executable-facing read:
  - current local result and admitted terrain8 result remain separate surfaces under the same runner hash
- tension anchor:
  - source admission here must not erase the earlier mismatch-preservation batch

## Cluster D
- cluster label:
  - closure correction anchor
- members:
  - aggregate direct-source coverage scan
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_hygiene_residue_artifacts__v1/MANIFEST.json`
- family role:
  - closure-completion anchor
- executable-facing read:
  - this batch exists because the final closure scan found one uncovered sims file
- tension anchor:
  - the earlier “complete” closure claim was one file short

## Cross-Cluster Read
- Cluster A is the only in-batch source family
- Cluster B preserves the local topology4 summary content
- Cluster C preserves the earlier terrain8-admission seam
- Cluster D records that this batch is a closure correction rather than a newly discovered family

# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / SIM-ONLY CLUSTER MAP
Batch: `BATCH_sims_axis12_topology4_channelgrid_family__v1`
Extraction mode: `SIM_AXIS12_TOPOLOGY4_CHANNELGRID_PASS`

## Cluster A
- cluster label:
  - core source pair
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_topology4_channelgrid_v1.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_topology4_channelgrid_v1.json`
- family role:
  - canonical source-bounded member set for this batch
- executable-facing read:
  - one runner
  - one paired result
  - one local SIM_ID
- tension anchor:
  - the local topology4 pair is clean even though the neighboring topology4 terrain8 surface is the one repo-top admitted

## Cluster B
- cluster label:
  - topology4 quadrant contract
- members:
  - `EO_FX`
  - `EO_AD`
  - `EC_FX`
  - `EC_AD`
- family role:
  - executable family lattice carried by the runner
- executable-facing read:
  - axis1 distinguishes energy-open vs energy-closed
  - axis2 distinguishes fixed vs adaptive
- tension anchor:
  - deltaH magnitude and entropy increase do not align on the same quadrant

## Cluster C
- cluster label:
  - test-vs-control sign layer
- members:
  - `n_test`
  - `n_ctrl`
  - `TEST_delta_deltaH_absmean`
  - `CTRL_delta_deltaH_absmean`
- family role:
  - executable axis3 validation layer
- executable-facing read:
  - test axis leaves small but real sign gaps
  - control axis suppresses sign gaps to numerical noise
- tension anchor:
  - the negative control works without collapsing the topology4 family differences

## Cluster D
- cluster label:
  - fixed-vs-adaptive nonlinearity split
- members:
  - `lin_err_mean`
  - `AD` families
  - `FX` families
- family role:
  - stored axis2-signal cluster
- executable-facing read:
  - `AD` families have real nonlinearity
  - `FX` families are effectively linear at stored precision
- tension anchor:
  - axis2 signal is strong even when some sign effects stay tiny

## Cluster E
- cluster label:
  - visibility seam and campaign closure
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis12_topology4_channelfamily_terrain8_seam__v1/MANIFEST.json`
- family role:
  - comparison-only visibility and closure cluster
- executable-facing read:
  - neighboring terrain8 topology4 surface is repo-top admitted
  - current channelgrid SIM_ID is not
  - residual paired-family campaign completes with this batch
- tension anchor:
  - campaign completion and repo-top omission coexist

## Cross-Cluster Read
- Cluster A is the only in-batch source family
- Cluster B shows the topology4 quadrant structure
- Cluster C shows the working negative-control sign layer
- Cluster D shows the clean adaptive-vs-fixed separation
- Cluster E preserves the visibility seam and paired-family closure without broadening the batch

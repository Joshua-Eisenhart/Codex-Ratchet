# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / SIM-ONLY CLUSTER MAP
Batch: `BATCH_sims_axis12_seq_constraints_family__v1`
Extraction mode: `SIM_AXIS12_SEQ_CONSTRAINTS_PASS`

## Cluster A
- cluster label:
  - core source pair
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_seq_constraints.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_seq_constraints.json`
- family role:
  - canonical source-bounded member set for this batch
- executable-facing read:
  - one runner
  - one paired result
  - one local SIM_ID
- tension anchor:
  - the local source contains a fuller constraint layer than the repo-top descendant admitted under the same code hash

## Cluster B
- cluster label:
  - axis1 and axis2 constraint lattice
- members:
  - `seta_bad_*`
  - `setb_bad_*`
  - `seni_within_*`
  - `nesi_within_*`
  - wraparound cycle edges
- family role:
  - executable combinatorial contract carried by the runner
- executable-facing read:
  - axis2 counts track allowed-adjacency nonmembership
  - axis1 counts track within-pair cohesion
- tension anchor:
  - the two constraint layers do not collapse into one redundant summary

## Cluster C
- cluster label:
  - balanced vs asymmetric sequence classes
- members:
  - `SEQ01`
  - `SEQ02`
  - `SEQ03`
  - `SEQ04`
- family role:
  - stored sequence-class behavior cluster
- executable-facing read:
  - `SEQ01/SEQ02` are balanced on `seta_bad` vs `setb_bad`
  - `SEQ03/SEQ04` are asymmetric and activate both within-pair counters
- tension anchor:
  - the asymmetric pair splits on opposite axis2 failures even though both sequences activate the same within-pair signals

## Cluster D
- cluster label:
  - repo-top descendant and evidence seam
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS12_SEQ_CONSTRAINTS_V2.json`
  - shared runner hash `45a914e43629cbd18486c08e8fe4716488bc39b91c9222ccb4ad267d86c6a725`
- family role:
  - comparison-only evidence and descendant cluster
- executable-facing read:
  - repo-top admission exists for `V2`
  - the local suite SIM_ID is omitted
  - `V2` stores only a narrower edge summary and diverges on the `seni` layer
- tension anchor:
  - code-hash continuity coexists with metric-surface divergence

## Cluster E
- cluster label:
  - campaign continuity
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis12_channel_realization_suite_family__v1/MANIFEST.json`
  - deferred next residual pair:
    - `run_axis12_topology4_channelfamily_suite_v2.py`
    - `results_S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1.json`
- family role:
  - comparison-only continuity and backlog cluster
- executable-facing read:
  - the prior batch hands off into the current local constraint family
  - the next topology4 paired family remains out of batch
- tension anchor:
  - family continuity exists without collapsing adjacent paired families into one batch

## Cross-Cluster Read
- Cluster A is the only in-batch source family
- Cluster B shows the full local constraint layer
- Cluster C shows the balanced pair vs asymmetric pair split
- Cluster D preserves the local-surface-vs-`V2` descendant seam
- Cluster E preserves residual campaign continuity without broadening the batch

# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / SIM-ONLY CLUSTER MAP
Batch: `BATCH_sims_axis12_topology4_channelfamily_terrain8_seam__v1`
Extraction mode: `SIM_AXIS12_TOPOLOGY4_CHANNELFAMILY_TERRAIN8_SEAM_PASS`

## Cluster A
- cluster label:
  - seam source pair
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_topology4_channelfamily_suite_v2.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1.json`
- family role:
  - canonical source-bounded seam pair for this batch
- executable-facing read:
  - one runner hash
  - one repo-top admitted terrain8 surface
  - incompatible current local output contract
- tension anchor:
  - the selected pair is source-linked by provenance, not by matching present-day output contract

## Cluster B
- cluster label:
  - current local topology4 family contract
- members:
  - `EO_FX`
  - `EO_AD`
  - `EC_FX`
  - `EC_AD`
  - `deltaH_absmean`
  - `lin_err_mean`
  - `dS_mean`
- family role:
  - executable-facing contract encoded in the current runner and local result
- executable-facing read:
  - adaptive families carry nonzero linearity error
  - fixed families are near-zero on linearity error
  - `EO_FX` dominates energy-shift magnitude
- tension anchor:
  - the current executable contract is topology4-family math, not terrain8 endpoint enumeration

## Cluster C
- cluster label:
  - admitted terrain8 endpoint surface
- members:
  - `Se_sign...`
  - `Ne_sign...`
  - `Ni_sign...`
  - `Si_sign...`
  - `entropy_mean`
  - `purity_mean`
- family role:
  - repo-top admitted result cluster
- executable-facing read:
  - `Si` is strongest overall on stored entropy/purity
  - sign effects vary by terrain
  - `UP` vs `DOWN` is tiny for most cells and exactly zero for `Si`
- tension anchor:
  - the admitted surface has a terrain-by-sign-by-direction geometry absent from the current local topology4 result

## Cluster D
- cluster label:
  - direct evidence-pack admission
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `SIM_ID: S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1`
  - `CODE_HASH_SHA256: be1a8c714b57ebfe98559d14237d85b258f760f5db2691f10b3f778660edcb12`
  - `OUTPUT_HASH_SHA256: 218b43b4a1adee0149363f5103840329693d81e82beea73485fdc1235e2a6e9a`
- family role:
  - exact repo-top admission cluster
- executable-facing read:
  - repo-top evidence directly matches the selected terrain8 surface
  - the evidence tokenization still diverges from JSON key formatting
- tension anchor:
  - exact admission coexists with key-format and contract mismatch against the current runner

## Cluster E
- cluster label:
  - campaign continuity and next paired family
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis12_seq_constraints_family__v1/MANIFEST.json`
  - deferred next residual pair:
    - `run_axis12_topology4_channelgrid_v1.py`
    - `results_axis12_topology4_channelgrid_v1.json`
- family role:
  - comparison-only continuity and backlog cluster
- executable-facing read:
  - the current seam batch is complete
  - the next topology4 paired family stays out of batch
- tension anchor:
  - adjacent topology4 families remain separate despite shared naming

## Cross-Cluster Read
- Cluster A is the only in-batch source family
- Cluster B shows the current local topology4-family contract
- Cluster C shows the admitted terrain8 endpoint surface
- Cluster D preserves the exact repo-top admission link
- Cluster E preserves residual campaign continuity without broadening the batch

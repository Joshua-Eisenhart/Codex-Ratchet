# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / SIM-ONLY CLUSTER MAP
Batch: `BATCH_sims_hygiene_residue_artifacts__v1`
Extraction mode: `SIM_HYGIENE_RESIDUE_ARTIFACT_PASS`

## Cluster A
- cluster label:
  - core hygiene residue family
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/__pycache__/ run_axis0_boundary_bookkeep_sweep_v2.cpython-313.pyc`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/__pycache__/ run_axis12_axis0_link_v1.cpython-313.pyc`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/__pycache__/ run_mega_axis0_ab_stage16_axis6.cpython-313.pyc`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/.DS_Store`
- family role:
  - canonical source-bounded member set for the final hygiene pass
- executable-facing read:
  - artifact-class residue only
  - no new sim outputs or executable claims
- tension anchor:
  - the batch is inside the sims source class but contains no simulation content

## Cluster B
- cluster label:
  - committed pycache artifacts
- members:
  - `run_axis0_boundary_bookkeep_sweep_v2.cpython-313.pyc`
  - `run_axis12_axis0_link_v1.cpython-313.pyc`
  - `run_mega_axis0_ab_stage16_axis6.cpython-313.pyc`
- family role:
  - bytecode-cache subcluster
- executable-facing read:
  - these files shadow already-batched executable harnesses
  - they are compiled artifacts, not source or result surfaces
- tension anchor:
  - the cache artifacts inherit runner names from meaningful families while adding no new source-level content

## Cluster C
- cluster label:
  - top-level filesystem noise
- members:
  - `.DS_Store`
- family role:
  - platform-noise subcluster
- executable-facing read:
  - Apple Desktop Services metadata only
- tension anchor:
  - it shares residual status with pycache but not executable lineage

## Cluster D
- cluster label:
  - leading-space runner shadow anchor
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_leading_space_runner_result_family__v1/MANIFEST.json`
- family role:
  - comparison-only executable lineage anchor
- executable-facing read:
  - the three `.pyc` artifacts correspond to the three leading-space runners first batched in folder order
- tension anchor:
  - already-batched source families still left behind compiled residue

## Cross-Cluster Read
- Cluster A is the only in-batch source family
- Cluster B preserves the bytecode-cache subgroup
- Cluster C preserves top-level platform noise as a separate semantic class
- Cluster D ties the pycache artifacts back to the earlier executable lineage without re-batching the runners

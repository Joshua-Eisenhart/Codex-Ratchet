# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / SIM-ONLY CLUSTER MAP
Batch: `BATCH_sims_residual_inventory_closure_audit__v1`
Extraction mode: `SIM_RESIDUAL_CLOSURE_AUDIT_PASS`

## Cluster A
- cluster label:
  - coverage-anchor docs
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
- family role:
  - canonical source-bounded member set for this closure batch
- executable-facing read:
  - these two docs do not execute sims
  - they anchor inventory visibility and evidence-admission visibility
- tension anchor:
  - catalog visibility is broader than direct source-membership coverage, and evidence-pack visibility is narrower still

## Cluster B
- cluster label:
  - residual paired families already comparison-read elsewhere
- members:
  - `run_axis0_traj_corr_suite.py` + `results_axis0_traj_corr_suite.json`
  - `run_axis12_channel_realization_suite.py` + `results_axis12_channel_realization_suite.json`
  - `run_axis12_seq_constraints.py` + `results_axis12_seq_constraints.json`
  - `run_axis12_topology4_channelfamily_suite_v2.py` + `results_axis12_topology4_channelfamily_suite_v2.json`
- family role:
  - residual executable/result pairs that already influenced earlier bundle batches without becoming direct source members
- executable-facing read:
  - each pair still exists as a standalone local runner plus paired result
  - earlier bundle batches instead foregrounded descendant or renamed surfaces
- tension anchor:
  - comparison-anchor reuse is not the same as direct source-membership coverage

## Cluster C
- cluster label:
  - residual paired families never promoted into any earlier sims batch
- members:
  - `run_axis0_historyop_rec_suite_v1.py` + `results_axis0_historyop_rec_suite_v1.json`
  - `run_axis0_mi_discrim_branches.py` + `results_axis0_mi_discrim_branches.json`
  - `run_axis0_mi_discrim_branches_ab.py` + `results_axis0_mi_discrim_branches_ab.json`
  - `run_axis0_mutual_info.py` + `results_axis0_mutual_info.json`
  - `run_axis0_negsagb_stress.py` + `results_axis0_negsagb_stress.json`
  - `run_axis0_sagb_entangle_seed.py` + `results_axis0_sagb_entangle_seed.json`
  - `run_axis0_traj_corr_metrics.py` + `results_axis0_traj_corr_metrics.json`
  - `run_axis12_topology4_channelgrid_v1.py` + `results_axis12_topology4_channelgrid_v1.json`
- family role:
  - direct residual executable/result pairs still outside both source membership and comparison reuse
- executable-facing read:
  - these are the cleanest future candidates if residual family processing is ever resumed
- tension anchor:
  - raw-order family completion left intact runner/result pairs behind

## Cluster D
- cluster label:
  - residual runner-only and result-only orphan surfaces
- members:
  - runner-only:
    - `run_axis12_harden_triple_v1.py`
    - `run_axis12_harden_v2_triple.py`
  - result-only:
    - `results_axis0_boundary_bookkeep_v1.json`
    - `results_axis0_traj_corr_suite_v2.json`
    - `results_axis12_altchan_v1.json`
    - `results_axis12_altchan_v2.json`
    - `results_axis12_negctrl_label_v2.json`
    - `results_axis12_negctrl_swap_v1.json`
    - `results_axis12_paramsweep_v1.json`
    - `results_axis12_paramsweep_v2.json`
    - `results_ultra3_full_geometry_stage16_axis0.json`
    - `results_ultra_big_ax012346.json`
- family role:
  - residual surfaces that cannot currently be treated as clean paired families
- executable-facing read:
  - the two harden runners have no residual paired result surface
  - the ten listed result files have no residual paired runner surface
- tension anchor:
  - catalog visibility exists for many of these files, but direct family bounding does not

## Cluster E
- cluster label:
  - diagnostics, proof scripts, and hygiene artifacts
- members:
  - `mega_sims_failure_detector.py`
  - `mega_sims_run_02.py`
  - `mega_sims_trivial_check.py`
  - `prove_foundation.py`
  - `.DS_Store`
  - `__pycache__/ run_axis0_boundary_bookkeep_sweep_v2.cpython-313.pyc`
  - `__pycache__/ run_axis12_axis0_link_v1.cpython-313.pyc`
  - `__pycache__/ run_mega_axis0_ab_stage16_axis6.cpython-313.pyc`
- family role:
  - non-family residuals inside the sims tree
- executable-facing read:
  - these files do not currently present as clean runner/result family members
- tension anchor:
  - filesystem presence inside the sims tree does not make a file a source-worthy sim family

## Cross-Cluster Read
- Cluster A is the only direct source-member set in this batch
- Cluster B proves that prior comparison reuse did not equal source-membership coverage
- Cluster C is the strongest residual family backlog if future intake work is requested
- Cluster D holds orphan or half-paired surfaces that need separate rebounding before interpretation
- Cluster E is hygiene or diagnostic residue and should stay quarantined from normal sim-family extraction

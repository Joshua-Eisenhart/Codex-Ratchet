# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / SIM-ONLY CLUSTER MAP
Batch: `BATCH_sims_stage16_axis6_mix_control_sweep_family__v1`
Extraction mode: `SIM_STAGE16_AXIS6_MIX_FAMILY_PASS`

## Cluster A
- cluster label:
  - Stage16 paired-control surface
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_stage16_axis6_mix_control.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_stage16_axis6_mix_control.json`
- family role:
  - smallest mixed-axis6 perturbation surface
- executable-facing read:
  - one mixed pattern against one uniform baseline
  - same `rho0` is reused for the paired comparison inside each trial
- tension anchor:
  - local comparison contract is tighter than the broader sweep contract

## Cluster B
- cluster label:
  - Stage16 mix-mode sweep surface
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_stage16_axis6_mix_sweep.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_stage16_axis6_mix_sweep.json`
- family role:
  - broader mixed-axis6 sweep surface
- executable-facing read:
  - compares `MIX_A`, `MIX_B`, and `MIX_R` against uniform
  - uses separate `run_one_stage` calls for uniform and mixed draws
- tension anchor:
  - same high-level question as Cluster A, but not the same sampling contract

## Cluster C
- cluster label:
  - uniform baseline anchor
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_stage16_sub4_axis6u.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_stage16_sub4_axis6u.json`
- family role:
  - comparison-only absolute baseline for the mixed-axis6 family
- executable-facing read:
  - absolute stage means only
  - no mixed-pattern comparison
- tension anchor:
  - exact numeric baseline identity to control does not make it the same bounded family

## Cross-Cluster Read
- `mix_control` and `mix_sweep` belong together as the mixed-axis6 family
- `sub4_axis6u` belongs beside them as the exact baseline anchor, not as a merged family member
- evidence and admission split:
  - catalog groups the three surfaces
  - top-level evidence pack admits none of them

# SIM Catalog v1.3 (from simson.zip results files)

Generated at UTC: 2026-01-30T00:00:00Z

This catalog is derived from the JSON filenames in `simson.zip` (62 result files).


## Axis meaning note (for interpreting this catalog)

- **AXIS‑4** entries include both (a) SEQ/FWD/REV loop experiments and (b) a direct variance‑order check
  (`S_SIM_AXIS4_COMP_FETI_TEFI_CHECK_V1`). In your notes, AXIS‑4 is the **variance‑order split**
  (deductive vs inductive). The loop orders are treated as *derived probes* of that split.
- **TOPOLOGY4** appears in the Axis12 suite (`S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1`).
  In your framework, Topology4 is the **AXIS‑1 × AXIS‑2** product (four base topologies),
  while “edges” are later adjacency structure between these bases.
- **AXIS‑3** Weyl/Hopf runs (`S_SIM_AXIS3_WEYL_HOPF_GRID_V1`) are the chirality substrate;
  “terrain” should be read as derived-from-flux rather than assumed metric geometry.

Additional planning note (noncanon):
- If you are pursuing the “Stage8 on Weyl loops” picture (outer/inner loop × 4 bases),
  treat the Topology4 + Axis3 Weyl/Hopf runs as the two anchor surfaces, and treat Axis4 SEQ runs as probes.

## Categories
- **MESO: Axis0**: 16 result files
- **MESO: Axis12**: 13 result files
- **MESO: Topology4 (Axis1×Axis2)**: 3 result files (subset of Axis12)
- **MESO: Axis4**: 10 result files
- **OTHER**: 5 result files
- **MESO: Axis5**: 2 result files
- **MESO: Axis6**: 3 result files
- **MESO: Stage16**: 6 result files
- **MACRO: ULTRA**: 4 result files
- **MICRO: Operator roles**: 2 result files
- **MESO: Axis3**: 1 result files
- **MICRO: Terrain**: 1 result files
- **MACRO: ULTRA4**: 1 result files

## MESO: Axis0
- `S_SIM_AXIS0_TRAJ_CORR_SUITE_V4`  →  `results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V4.json`
- `S_SIM_AXIS0_TRAJ_CORR_SUITE_V5`  →  `results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V5.json`
- `S_SIM_NEGCTRL_AXIS0_NOENT_V1`  →  `results_S_SIM_NEGCTRL_AXIS0_NOENT_V1.json`
- `axis0_boundary_bookkeep_sweep_v2`  →  `results_axis0_boundary_bookkeep_sweep_v2.json`
- `axis0_boundary_bookkeep_v1`  →  `results_axis0_boundary_bookkeep_v1.json`
- `axis0_historyop_rec_suite_v1`  →  `results_axis0_historyop_rec_suite_v1.json`
- `axis0_mi_discrim_branches`  →  `results_axis0_mi_discrim_branches.json`
- `axis0_mi_discrim_branches_ab`  →  `results_axis0_mi_discrim_branches_ab.json`
- `axis0_mutual_info`  →  `results_axis0_mutual_info.json`
- `axis0_negsagb_stress`  →  `results_axis0_negsagb_stress.json`
- `axis0_sagb_entangle_seed`  →  `results_axis0_sagb_entangle_seed.json`
- `axis0_traj_corr_metrics`  →  `results_axis0_traj_corr_metrics.json`
- `axis0_traj_corr_suite`  →  `results_axis0_traj_corr_suite.json`
- `axis0_traj_corr_suite_v2`  →  `results_axis0_traj_corr_suite_v2.json`
- `axis12_axis0_link_v1`  →  `results_axis12_axis0_link_v1.json`
- `engine32_axis0_axis6_attack`  →  `results_engine32_axis0_axis6_attack.json`

## MESO: Axis12
- `S_SIM_AXIS12_CHANNEL_REALIZATION_V4`  →  `results_S_SIM_AXIS12_CHANNEL_REALIZATION_V4.json`
- `S_SIM_AXIS12_SEQ_CONSTRAINTS_V2`  →  `results_S_SIM_AXIS12_SEQ_CONSTRAINTS_V2.json`
- `S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1`  →  `results_S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1.json`
- `axis12_altchan_v1`  →  `results_axis12_altchan_v1.json`
- `axis12_altchan_v2`  →  `results_axis12_altchan_v2.json`
- `axis12_channel_realization_suite`  →  `results_axis12_channel_realization_suite.json`
- `axis12_negctrl_label_v2`  →  `results_axis12_negctrl_label_v2.json`
- `axis12_negctrl_swap_v1`  →  `results_axis12_negctrl_swap_v1.json`
- `axis12_paramsweep_v1`  →  `results_axis12_paramsweep_v1.json`
- `axis12_paramsweep_v2`  →  `results_axis12_paramsweep_v2.json`
- `axis12_seq_constraints`  →  `results_axis12_seq_constraints.json`
- `axis12_topology4_channelfamily_suite_v2`  →  `results_axis12_topology4_channelfamily_suite_v2.json`
- `axis12_topology4_channelgrid_v1`  →  `results_axis12_topology4_channelgrid_v1.json`

## MESO: Topology4 (Axis1×Axis2 product)

These runs are the clearest *Axis‑1×Axis‑2* “Topology4” evidence surfaces in the current bundle:

- `axis12_topology4_channelfamily_suite_v2`  →  `results_axis12_topology4_channelfamily_suite_v2.json`
- `axis12_topology4_channelgrid_v1`  →  `results_axis12_topology4_channelgrid_v1.json`
- `S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1`  →  `results_S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1.json`

Entry points:
- `run_axis12_topology4_channelfamily_suite_v2.py`

Note:
- “Topology4” is treated as a **base-class space**. Graph edges / adjacency are secondary artifacts.

## MESO: Axis4
- `S_SIM_AXIS4_COMP_FETI_TEFI_CHECK_V1`  →  `results_S_SIM_AXIS4_COMP_FETI_TEFI_CHECK_V1.json`
- `S_SIM_AXIS4_SEQ01_P03`  →  `results_S_SIM_AXIS4_SEQ01_P03.json`
- `S_SIM_AXIS4_SEQ02_P03`  →  `results_S_SIM_AXIS4_SEQ02_P03.json`
- `S_SIM_AXIS4_SEQ03_P03`  →  `results_S_SIM_AXIS4_SEQ03_P03.json`
- `S_SIM_AXIS4_SEQ04_P03`  →  `results_S_SIM_AXIS4_SEQ04_P03.json`
- `S_SIM_AXIS4_SEQ_ALL_BIDIR_V1`  →  `results_S_SIM_AXIS4_SEQ_ALL_BIDIR_V1.json`
- `axis4_seq01_both_dirs`  →  `results_axis4_seq01_both_dirs.json`
- `axis4_seq02_both_dirs`  →  `results_axis4_seq02_both_dirs.json`
- `axis4_seq03_seq04_both_dirs`  →  `results_axis4_seq03_seq04_both_dirs.json`
- `axis4_type2_all_seq_both_dirs`  →  `results_axis4_type2_all_seq_both_dirs.json`

## MESO: Axis5

## MESO: Axis6

## OTHER
- `batch_v3`  →  `results_batch_v3.json`
- `full_axis_suite`  →  `results_full_axis_suite.json`
- `history_invariant_gradient_scan_v11`  →  `results_history_invariant_gradient_scan_v11.json`

## MESO: Stage16
- `S_SIM_STAGE16_SUB4_AXIS6_UNIFORM_V4`  →  `results_S_SIM_STAGE16_SUB4_AXIS6_UNIFORM_V4.json`
- `S_SIM_STAGE16_SUB4_UNIFORM_AXIS6_V5`  →  `results_S_SIM_STAGE16_SUB4_UNIFORM_AXIS6_V5.json`
- `mega_axis0_ab_stage16_axis6`  →  `results_mega_axis0_ab_stage16_axis6.json`
- `stage16_axis6_mix_control`  →  `results_stage16_axis6_mix_control.json`
- `stage16_axis6_mix_sweep`  →  `results_stage16_axis6_mix_sweep.json`
- `stage16_sub4_axis6u`  →  `results_stage16_sub4_axis6u.json`

## MACRO: ULTRA
- `ultra2_axis0_ab_stage16_axis6`  →  `results_ultra2_axis0_ab_stage16_axis6.json`
- `ultra3_full_geometry_stage16_axis0`  →  `results_ultra3_full_geometry_stage16_axis0.json`
- `ultra_axis0_ab_axis6_sweep`  →  `results_ultra_axis0_ab_axis6_sweep.json`
- `ultra_big_ax012346`  →  `results_ultra_big_ax012346.json`

## MICRO: Operator roles
- `S_SIM_AXIS56_OPERATOR4_LR_SUITE_V1`  →  `results_S_SIM_AXIS56_OPERATOR4_LR_SUITE_V1.json`
- `oprole8_left_right_suite`  →  `results_oprole8_left_right_suite.json`

## MESO: Axis3
- `S_SIM_AXIS3_WEYL_HOPF_GRID_V1`  →  `results_S_SIM_AXIS3_WEYL_HOPF_GRID_V1.json`

## MICRO: Terrain
- `terrain8_sign_suite`  →  `results_terrain8_sign_suite.json`

## MACRO: ULTRA4
- `ultra4_full_stack`  →  `results_ultra4_full_stack.json`

## Relevant simpy entrypoints observed

- `run_axis0_historyop_rec_suite_v1.py`
- `run_axis0_traj_corr_suite.py`
- `run_axis12_channel_realization_suite.py`
- `run_axis12_topology4_channelfamily_suite_v2.py`
- `run_full_axis_suite.py`
- `run_oprole8_left_right_suite.py`
- `run_sim_suite_v1.py`
- `run_sim_suite_v2_full_axes.py`
- `run_stage16_axis6_mix_control.py`
- `run_stage16_axis6_mix_sweep.py`
- `run_stage16_sub4_axis6u.py`
- `run_terrain8_sign_suite.py`
- `run_ultra2_axis0_ab_stage16_axis6.py`
- `run_ultra4_full_stack.py`
- `run_ultra_axis0_ab_axis6_sweep.py`

## Suggested execution order (repeatable)

1. MICRO sanity (terrain / operator-role / sign suites)
2. Axis0 + Axis4 (fast parameter sweeps)
3. Axis12/13 (history scans)
4. Stage16 axis6 mixes (control + sweep)
5. ULTRA runs (end-to-end)

For each stage: fix seeds, hash code, normalize output, then generate SIM_EVIDENCE blocks.
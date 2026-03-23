# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / SOURCE-BOUND DISTILLATE
Batch: `BATCH_sims_sim_suite_v1_descendant_bundle__v1`
Extraction mode: `SIM_SUITE_V1_BUNDLE_PASS`

## Distillate D1
- strongest source-bound read:
  - `run_sim_suite_v1.py` is a genuine multisim descendant bundle that currently emits ten stored results in one executable surface
- supporting anchors:
  - `run_sim_suite_v1.py:568-623`
  - batch source membership

## Distillate D2
- strongest source-bound read:
  - all ten emitted descendants are represented in the repo-held top-level evidence pack, but only four keep the current `run_sim_suite_v1.py` hash there
- supporting anchors:
  - evidence-pack blocks for all ten SIM_IDs

## Distillate D3
- strongest source-bound read:
  - the current clean bundle-aligned subset is:
    - Axis3 Hopf grid
    - Axis6 left/right multi
    - Axis5 FGA
    - Axis5 FSA
- supporting anchors:
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:93-98`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:269-298`

## Distillate D4
- strongest source-bound read:
  - the rest of the emitted descendants have migrated to other current provenance anchors:
    - Axis12 seq constraints -> `run_axis12_seq_constraints.py`
    - Axis12 channel realization -> `run_axis12_channel_realization_suite.py`
    - Axis4 all bidir -> `axis4_seq_cycle_sim.py`
    - Axis0 traj corr V4 -> `run_axis0_traj_corr_suite.py`
    - Stage16 V4 -> ` simpy/ run_mega_axis0_ab_stage16_axis6.py`
    - Negctrl Axis6 V2 -> current `run_sim_suite_v2_full_axes.py` hash
- supporting anchors:
  - evidence-pack code hashes and current hash matches in this batch

## Distillate D5
- runtime expectations extracted:
  - the bundle writes ten result files and one local evidence pack
  - internal scales differ by subfamily:
    - Axis3 uses a `400 x 400` grid
    - Axis6 and Axis5 use `512` trials
    - Axis4 uses `256` states over `64` cycles across four sequences and two signs
    - Axis12 channel realization uses `81` parameter rows with `256` trials each
    - Stage16, negctrl, and Axis0 use `256` trial-class settings
- supporting anchors:
  - sim definitions and `main()` in `run_sim_suite_v1.py`

## Distillate D6
- failure modes extracted:
  - treating bundle emission as identical to top-level current provenance
  - treating adjacent `sim_suite_v2` as part of the same bounded batch
  - treating Stage16 V4/V5 or Negctrl V2/V3 version differences as proof of payload change without checking stored outputs
- supporting anchors:
  - tension items `T1` through `T8`

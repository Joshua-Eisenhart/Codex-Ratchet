# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_axis0_historyop_rec_suite_v1_family__v1`
Extraction mode: `SIM_AXIS0_HISTORYOP_REC_SUITE_PASS`

## T1) The runner emits four explicit local SIM_ID evidence blocks, but the repo-held top-level evidence pack omits all of them
- source markers:
  - `run_axis0_historyop_rec_suite_v1.py:321-350`
  - negative search for `axis0_historyop_rec_suite_v1` and `S_SIM_AXIS0_HISTORYOP_REC_*` in `SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `SIM_CATALOG_v1.3.md:44,135`
- tension:
  - the runner explicitly writes four local evidence blocks
  - the catalog lists the family
  - the repo-held evidence pack still contains no matching block
- preserved read:
  - keep local evidence emission distinct from repo-top admission
- possible downstream consequence:
  - later sims summaries should treat this family as source-real but not top-level evidenced

## T2) Reconstruction mode strongly changes reconstruction error, but the stored trajectory MI summaries remain invariant
- source markers:
  - `run_axis0_historyop_rec_suite_v1.py:163-197`
  - `results_axis0_historyop_rec_suite_v1.json`
- tension:
  - average `ERR_traj` mean rises from:
    - `0.0` in `REC_ID`
    - `0.20640436952859126` in `REC_MARG`
    - `0.3310559568545458` in `REC_MIX`
    - `0.42241966974449235` in `REC_SCR`
  - average `MI_traj` mean stays fixed at `0.12588103091253527` across all four rec modes
- preserved read:
  - reconstruction fidelity and stored trajectory MI should not be collapsed into one effect dimension
- possible downstream consequence:
  - later interpretation should not assume that larger reconstruction error implies altered MI trajectory behavior here

## T3) Sequence-order signal survives every reconstruction mode, but negativity never appears
- source markers:
  - `run_axis0_historyop_rec_suite_v1.py:289-316`
  - `results_axis0_historyop_rec_suite_v1.json`
- tension:
  - `dMI_traj_mean_SEQ02_minus_SEQ01` remains positive in every case, ranging from `0.003501770382473929` to `0.008794687193699025`
  - `dNEG_end_frac_SEQ02_minus_SEQ01` remains exactly `0.0` in every run of every case
- preserved read:
  - order sensitivity is present without any stored negative conditional-entropy event
- possible downstream consequence:
  - later backlog work should not treat negative-end-fraction absence as evidence that the family is sequence-invariant

## T4) `REC_ID` is exact enough to drive all stored error summaries to zero, but it does not erase the sequence-order MI effect
- source markers:
  - `run_axis0_historyop_rec_suite_v1.py:164-178`
  - `results_axis0_historyop_rec_suite_v1.json`
- tension:
  - `REC_ID` reconstructs the full state exactly, so all stored `ERR_traj` and `ERR_end` statistics are `0.0`
  - the same exact-reconstruction case still carries the strongest stored `dMI_traj_mean_SEQ02_minus_SEQ01`
- preserved read:
  - exact reconstruction removes reconstruction error, not the family’s sequence-order discriminators
- possible downstream consequence:
  - later summaries should not confuse rec-quality controls with removal of the underlying axis0 signal

## T5) The strongest stored effects localize on `SEQ03`, not on the `SEQ01` baseline emphasized by the evidence writer
- source markers:
  - `run_axis0_historyop_rec_suite_v1.py:333-344`
  - `results_axis0_historyop_rec_suite_v1.json`
- tension:
  - the emitted evidence writer reports:
    - `DELTA_SEQ02_SEQ01`
    - `SEQ01` baseline end means
  - the strongest stored `MI_traj` and lowest stored `SAgB_end` both occur at:
    - case `S_SIM_AXIS0_HISTORYOP_REC_ID_V1`
    - run `BELL_s-1`
    - sequence `SEQ03`
- preserved read:
  - the evidence writer’s compact summary is not the whole numerical story of the family
- possible downstream consequence:
  - later extraction should not overfit interpretation to the emitted `SEQ02-SEQ01` summary lines alone

## T6) This family is the first residual paired-family intake after closure audit, but the next residual pair should stay separate
- source markers:
  - `BATCH_sims_residual_inventory_closure_audit__v1/MANIFEST.json`
  - residual pair inventory ordering
- tension:
  - `run_axis0_historyop_rec_suite_v1.py` is the first prioritized residual pair
  - `run_axis0_mi_discrim_branches.py` is the next clean residual pair
- preserved read:
  - keep the residual backlog pairwise and source-bounded
- possible downstream consequence:
  - the next batch should begin at `run_axis0_mi_discrim_branches.py`

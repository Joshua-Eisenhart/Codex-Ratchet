# A2-2 REFINED CANDIDATES

## Candidate 1: AXIS0_TRAJ_V2_ORPHAN_SHELL

- status: `A2_2_CANDIDATE`
- type: `result-only orphan shell`
- claim:
  - `results_axis0_traj_corr_suite_v2.json` is a bounded one-file result-only orphan surface and should remain a standalone packet rather than being absorbed into nearby trajectory families
- source lineage:
  - parent batch: `BATCH_sims_axis0_traj_corr_suite_v2_orphan_family__v1`
  - parent basis: cluster A, distillate D1, candidates C1-C3
- retained boundary:
  - source membership remains one file only

## Candidate 2: FAMILY_RESEMBLANCE_WITHOUT_RUNNER_ANCHOR

- status: `A2_2_CANDIDATE`
- type: `anchor-quality packet`
- claim:
  - the current orphan is clearly trajectory-correlation related, but no direct `traj_corr_suite_v2` runner-name hit exists in present `simpy/`, so family resemblance must remain explicit without fabricating a current runner anchor
- source lineage:
  - parent basis: tension T1, distillates D1 and D5, candidate C4
- retained contradiction marker:
  - family relation survives
  - direct runner anchor does not

## Candidate 3: SEQ01_BASELINE_PLUS_DELTAS_CONTRACT

- status: `A2_2_CANDIDATE`
- type: `storage-contract packet`
- claim:
  - the orphan uses a `SEQ01`-baseline-plus-deltas contract: `32` absolute base entries are all `SEQ01`, while `96` delta entries encode `SEQ02-04`, so missing absolute `SEQ02-04` values must not be misread as absent runs
- source lineage:
  - parent basis: clusters B and C, tension T2, distillate D2, candidate C3
- retained contradiction marker:
  - four-sequence family survives
  - full absolute reporting does not

## Candidate 4: HIDDEN_T_AXIS_AND_PERTURBATION_FOCUS

- status: `A2_2_CANDIDATE`
- type: `lattice packet`
- claim:
  - the real lattice exceeds top-level metadata because `T1` / `T2` live in key prefixes, and the strongest stored perturbation concentrates on `T1_REV_BELL_CNOT_R1_SEQ04`
- source lineage:
  - parent basis: clusters C and D, tensions T3 and T5, distillates D2 and D3
- retained boundary:
  - do not flatten the lattice to only the visible metadata axes

## Candidate 5: NOT_LOCAL_TRAJ_SUITE_PACKET

- status: `A2_2_CANDIDATE`
- type: `local-family separation packet`
- claim:
  - the orphan is not the earlier local trajectory-correlation suite, because the current surface uses a `128`-entry baseline-plus-deltas lattice with hidden `T` prefixes, gate and repetition axes, and far smaller base `MI` scale
- source lineage:
  - parent basis: cluster E, tension T3, distillate D4, candidate C5
- retained contradiction marker:
  - family resemblance survives
  - local-suite equivalence does not

## Candidate 6: NOT_V4_V5_AND_NOT_EVIDENCE_ADMITTED

- status: `A2_2_CANDIDATE`
- type: `descendant and visibility fence`
- claim:
  - the orphan is neither repo-top descendant `V4` nor `V5`, and although it is catalog-visible by filename alias, the top-level evidence pack omits it entirely, so descendant continuity and evidence admission must both remain denied here
- source lineage:
  - parent basis: cluster E, tensions T4 and T6, distillates D4 and D5, candidate C5
- retained contradiction marker:
  - catalog visibility survives
  - descendant equivalence and evidence admission do not

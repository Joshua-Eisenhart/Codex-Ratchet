# A2-2 REFINED CANDIDATES

## Candidate 1: AXIS12_HARDEN_RUNNER_ONLY_SHELL

- status: `A2_2_CANDIDATE`
- type: `runner-only residual shell`
- claim:
  - `run_axis12_harden_triple_v1.py` and `run_axis12_harden_v2_triple.py` form a bounded two-runner producer strip that correctly begins the runner-only residual-class campaign after paired-family completion
- source lineage:
  - parent batch: `BATCH_sims_axis12_harden_runner_strip__v1`
  - parent basis: cluster A, distillate D1, candidates C1-C3
- retained boundary:
  - no result surfaces are admitted as source members in this shell

## Candidate 2: RUNNER_ONLY_CLASS_WITH_DECLARED_RESULT_DEPENDENTS

- status: `A2_2_CANDIDATE`
- type: `class-split contradiction packet`
- claim:
  - the closure-audit runner-only label remains operationally useful, but the same two scripts explicitly declare six emitted result files that reopen later as result-only residuals, so the class split must be preserved without pretending the families are unrelated
- source lineage:
  - parent basis: clusters A and E, tension T1, distillates D2 and D3, candidate C2
- retained contradiction marker:
  - class split survives
  - semantic separation does not become absolute

## Candidate 3: LOCAL_EXPLICITNESS_WITH_ZERO_REPOTOP_VISIBILITY

- status: `A2_2_CANDIDATE`
- type: `visibility seam packet`
- claim:
  - the harden strip defines six local SIM_IDs and explicit evidence blocks, yet none of those runners or SIM_IDs appear in the repo-top catalog or evidence pack, so local producer explicitness must stay separate from top-level visibility
- source lineage:
  - parent basis: cluster E, tension T2, distillate D4, candidate C4
- retained contradiction marker:
  - local explicitness survives
  - repo-top visibility remains zero

## Candidate 4: V1_V2_CONTROL_CONTRACT_CHANGE

- status: `A2_2_CANDIDATE`
- type: `cross-version contract delta packet`
- claim:
  - `v2` is not a cosmetic rename of `v1`: it raises `num_states` from `256` to `512`, compresses the stored surfaces, and changes the third family from swapped-flag control to relabeled-channel rerun
- source lineage:
  - parent basis: clusters B and C, tension T3, distillate D5, candidate C5
- retained boundary:
  - `NEGCTRL_SWAP_V1` and `NEGCTRL_LABEL_V2` remain noninterchangeable control surfaces

## Candidate 5: SHARED_EVIDENCE_FILENAME_OVERWRITE_HAZARD

- status: `A2_2_CANDIDATE`
- type: `emission hazard packet`
- claim:
  - both harden runners write versioned result files but share the same unversioned `sim_evidence_pack.txt`, so sequential execution in one working directory would overwrite the earlier evidence emission even though result filenames do not collide
- source lineage:
  - parent basis: cluster D, tension T4, distillate D5
- retained contradiction marker:
  - result filenames are separated
  - evidence-pack emission is not

## Candidate 6: RESULT_ONLY_REOPEN_BOUNDARY

- status: `A2_2_CANDIDATE`
- type: `next-pass boundary packet`
- claim:
  - the six declared outputs are clearly linked to this runner strip, but they remain outside source membership here and reopen later as bounded result-only orphan passes beginning with the `v1` triplet
- source lineage:
  - parent basis: tension T6, distillate D6, candidate C6
- retained boundary:
  - do not merge the `v1` and `v2` orphan result surfaces back into this runner-only batch

# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_axis12_edge_partition_v4_seam__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Candidate RC1) `AXIS12_REALIZATION_SUITE_PAIR_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- `run_axis12_channel_realization_suite.py` and `results_axis12_channel_realization_suite.json` should stay compressed as:
  - one standalone fixed-parameter axis12 realization residual pair
  - one runner plus one paired result
  - one bounded family rather than one merged axis12 omnibus block

Why this survives reduction:
- it is the parent batch's cleanest family-shell claim
- it preserves the realization suite as its own reusable unit inside the residual lane

Source lineage:
- parent cluster `A`
- parent distillate `D1`
- parent candidate summaries:
  - `C1`
  - `C2`

Preserved limits:
- this batch does not absorb the next residual pair
- it preserves only the current axis12 realization pair as one bounded family

## Candidate RC2) `LOCAL_SUITE_VS_V4_DESCENDANT_ADMISSION_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest admission seam in the parent batch is:
  - the local suite emits evidence for `S_SIM_AXIS12_CHANNEL_REALIZATION_SUITE`
  - the repo-held evidence pack omits that local `SIM_ID`
  - the same pack admits `S_SIM_AXIS12_CHANNEL_REALIZATION_V4`
  - the admitted `V4` block shares the current runner hash
- code-hash continuity is not the same as local-suite SIM_ID admission

Why this survives reduction:
- it is the parent batch's clearest descendant seam
- later summaries need a compact rule for not collapsing the local suite into the admitted `V4` descendant

Source lineage:
- parent cluster `D`
- parent distillates:
  - `D4`
  - `D6`
- parent candidate summary `C4`
- parent tension `T1`
- comparison anchors:
  - `BATCH_A2MID_sims_evidence_boundary__v1:RC3`
  - `BATCH_A2MID_axis0_traj_suite_descendant_seams__v1:RC2`

Preserved limits:
- this batch does not deny runner-hash continuity
- it preserves only that hash continuity is weaker than local-suite admission

## Candidate RC3) `EDGE_PARTITION_COARSE_CLASSIFIER_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest structural packet in the parent batch is:
  - `SEQ01` and `SEQ02` share `SENI = 0`, `NESI = 0`
  - `SEQ03` and `SEQ04` share `SENI = 1`, `NESI = 1`
  - within each pair, endpoint metrics still differ
- the edge flags form a coarse classifier rather than a full endpoint-order explanation

Why this survives reduction:
- it is the parent batch's clearest anti-overread packet for the axis12 structural layer
- later summaries need a compact rule for preserving the boolean partition without inflating it into a full ordering model

Source lineage:
- parent clusters:
  - `B`
  - `C`
- parent distillates:
  - `D2`
  - `D6`
- parent candidate summary `C3`
- parent tension `T2`

Preserved limits:
- this batch does not deny that the edge partition is useful
- it preserves only that it is weaker than a complete endpoint-order model

## Candidate RC4) `GLOBAL_AXIS3_SIGN_DIRECTIONALITY_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest sign-layer packet in the parent batch is:
  - for all four sequences, sign `+1` stores lower entropy and higher purity than sign `-1`
  - the largest sign gap lands on `SEQ02`
- the axis3 sign layer is globally directional inside this axis12-labeled family

Why this survives reduction:
- it is the parent batch's clearest anti-collapse packet between axis12 structural labeling and sign-driven endpoint behavior
- later summaries need a compact rule for keeping the sign layer explicit

Source lineage:
- parent cluster `C`
- parent distillates:
  - `D2`
  - `D6`
- parent tension `T3`

Preserved limits:
- this batch does not deny that the family is still axis12-labeled
- it preserves only that the sign layer materially steers the realized endpoint order

## Candidate RC5) `FIXED_SNAPSHOT_VS_GRIDSCAN_DESCENDANT_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest local-versus-descendant surface-shape packet in the parent batch is:
  - the local suite fixes one `gamma/p/q/theta` tuple
  - the repo-top `V4` descendant spans a `3 x 3 x 3 x 3` parameter grid
- the admitted descendant is not just a renamed copy of the local snapshot

Why this survives reduction:
- it is the parent batch's clearest anti-copy packet
- later summaries need a compact rule for separating local fixed snapshots from broader descendant sweeps under the same runner hash

Source lineage:
- parent clusters:
  - `A`
  - `D`
- parent distillates:
  - `D2`
  - `D4`
  - `D6`
- parent candidate summary `C5`
- parent tension `T4`
- comparison anchor:
  - `BATCH_A2MID_axis0_traj_suite_descendant_seams__v1:RC2`

Preserved limits:
- this batch does not deny that both surfaces belong to the same broader code lineage
- it preserves only that local snapshot and descendant grid scan remain different surface types

## Candidate RC6) `SEQ02_STABLE_LOCAL_BEST_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest local endpoint packet in the parent batch is:
  - `SEQ02` is best on both entropy and purity under sign `+1`
  - `SEQ02` is best on both entropy and purity under sign `-1`
  - `SEQ01` shares the same no-edge class but never outranks it
- the family carries a stable `SEQ02` advantage not explained by the coarse edge partition alone

Why this survives reduction:
- it is the parent batch's clearest endpoint-order packet
- later summaries need a compact rule for keeping the local best sequence distinct from the coarser edge classes

Source lineage:
- parent clusters:
  - `B`
  - `C`
- parent distillates:
  - `D3`
  - `D6`
- parent candidate summary `C3`
- parent tension `T6`

Preserved limits:
- this batch does not deny that `SEQ01` and `SEQ02` share one coarse edge class
- it preserves only that shared class does not erase the stable local advantage of `SEQ02`

## Quarantined Residue Q1) `LOCAL_SUITE_AS_REPOTOP_ADMITTED_VIA_SHARED_HASH`
Status:
- `QUARANTINED`

Preserved residue:
- `V4` shares the current runner hash
- all retold as if the local suite SIM_ID were therefore repo-top admitted

Why it stays quarantined:
- the parent batch explicitly preserves omission of the local suite SIM_ID from the repo-held evidence pack
- shared hash is weaker than local-suite admission

Source lineage:
- parent distillates:
  - `D4`
  - `D6`
- parent candidate summary `C4`
- parent tension `T1`

## Quarantined Residue Q2) `EDGE_FLAGS_AS_FULL_ENDPOINT_ORDERING_MODEL`
Status:
- `QUARANTINED`

Preserved residue:
- the `SENI/NESI` edge partition
- all treated as if it fully determined the endpoint order inside each class

Why it stays quarantined:
- the parent batch explicitly preserves `SEQ02` as better than `SEQ01` and measurable differences between `SEQ03` and `SEQ04`
- coarse partitioning is weaker than full endpoint ordering

Source lineage:
- parent distillates:
  - `D2`
  - `D6`
- parent candidate summary `C3`
- parent tension `T2`

## Quarantined Residue Q3) `AXIS12_FAMILY_AS_PURELY_AXIS12_STRUCTURAL_WITHOUT_SIGN_LAYER`
Status:
- `QUARANTINED`

Preserved residue:
- axis12 structural labeling
- all treated as if the family carried no global sign directionality

Why it stays quarantined:
- the parent batch explicitly preserves a consistent sign `+1` advantage across all four sequences
- axis12 labeling is weaker than a claim that the sign layer is absent

Source lineage:
- parent distillates:
  - `D2`
  - `D6`
- parent tension `T3`

## Quarantined Residue Q4) `V4_AS_RENAMED_COPY_OF_LOCAL_SNAPSHOT`
Status:
- `QUARANTINED`

Preserved residue:
- `V4` descendant admission under the same runner hash
- all treated as if `V4` were just a renamed copy of the local fixed-parameter suite

Why it stays quarantined:
- the parent batch explicitly preserves one fixed snapshot locally and one grid scan in the admitted descendant
- code lineage is weaker than surface identity

Source lineage:
- parent distillates:
  - `D4`
  - `D6`
- parent candidate summary `C5`
- parent tension `T4`

## Quarantined Residue Q5) `ADJACENT_HARDEN_RUNNERS_AS_CURRENT_PAIRED_BATCH`
Status:
- `QUARANTINED`

Preserved residue:
- adjacent harden runner scripts in raw order
- all treated as if they belonged inside the current paired-family batch

Why it stays quarantined:
- the parent batch explicitly preserves runner-only harden surfaces as a different residual class
- raw adjacency is weaker than paired-family membership

Source lineage:
- parent distillates:
  - `D5`
  - `D6`
- parent candidate summary `C2`
- parent tension `T5`

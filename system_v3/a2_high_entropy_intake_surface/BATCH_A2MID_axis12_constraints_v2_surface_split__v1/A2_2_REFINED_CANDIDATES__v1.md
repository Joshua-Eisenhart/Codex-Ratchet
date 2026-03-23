# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_axis12_constraints_v2_surface_split__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Candidate RC1) `AXIS12_SEQ_CONSTRAINTS_PAIR_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- `run_axis12_seq_constraints.py` and `results_axis12_seq_constraints.json` should stay compressed as:
  - one standalone full axis12 constraint residual pair
  - one runner plus one paired result
  - one bounded family rather than one merged axis12 omnibus block

Why this survives reduction:
- it is the parent batch's cleanest family-shell claim
- it preserves the local full constraint pair as its own reusable unit inside the residual lane

Source lineage:
- parent cluster `A`
- parent distillate `D1`
- parent candidate summaries:
  - `C1`
  - `C2`

Preserved limits:
- this batch does not absorb the next residual pair
- it preserves only the current constraints pair as one bounded family

## Candidate RC2) `LOCAL_SURFACE_VS_V2_DESCENDANT_ADMISSION_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest admission seam in the parent batch is:
  - the local surface emits evidence for `S_SIM_AXIS12_SEQ_CONSTRAINTS`
  - the repo-held evidence pack omits that local `SIM_ID`
  - the same pack admits `S_SIM_AXIS12_SEQ_CONSTRAINTS_V2`
  - the admitted `V2` block shares the current runner hash
- code-hash continuity is not the same as local-surface SIM_ID admission

Why this survives reduction:
- it is the parent batch's clearest descendant seam
- later summaries need a compact rule for not collapsing the local full surface into the admitted `V2` descendant

Source lineage:
- parent cluster `D`
- parent distillates:
  - `D4`
  - `D6`
- parent candidate summary `C4`
- parent tension `T1`
- comparison anchors:
  - `BATCH_A2MID_sims_evidence_boundary__v1:RC3`
  - `BATCH_A2MID_axis12_edge_partition_v4_seam__v1:RC2`

Preserved limits:
- this batch does not deny runner-hash continuity
- it preserves only that hash continuity is weaker than local-surface admission

## Candidate RC3) `LOCAL_FOUR_LAYER_VS_V2_EDGE_SUBSET_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest metric-surface seam in the parent batch is:
  - the local surface stores:
    - `seta_bad_*`
    - `setb_bad_*`
    - `seni_within_*`
    - `nesi_within_*`
  - the repo-top `V2` descendant stores only:
    - `nesi_edges`
    - `seni_edges`
- the descendant is a narrower metric contract rather than a full copy of the local surface

Why this survives reduction:
- it is the parent batch's clearest local-versus-descendant surface packet
- later summaries need a compact rule for preserving the local axis2 counts instead of collapsing them into the narrower descendant edge subset

Source lineage:
- parent clusters:
  - `B`
  - `D`
- parent distillates:
  - `D2`
  - `D4`
  - `D6`
- parent candidate summary `C5`
- parent tension `T2`
- comparison anchor:
  - `BATCH_A2MID_axis0_traj_suite_descendant_seams__v1:RC3`

Preserved limits:
- this batch does not deny that the descendant keeps some real edge information
- it preserves only that the local four-layer surface is richer than the repo-top descendant contract

## Candidate RC4) `SAME_HASH_SENI_DIVERGENCE_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest same-hash divergence packet in the parent batch is:
  - the local surface stores:
    - `seni_within_SEQ03 = 1`
    - `seni_within_SEQ04 = 1`
  - the repo-top `V2` descendant stores:
    - `SEQ03_seni_edges = 0`
    - `SEQ04_seni_edges = 0`
- same-hash provenance coexists with real stored `seni` divergence

Why this survives reduction:
- it is the parent batch's clearest behavioral-divergence seam
- later summaries need a compact rule for preserving this contradiction rather than normalizing one surface into the other

Source lineage:
- parent clusters:
  - `B`
  - `D`
- parent distillates:
  - `D2`
  - `D4`
  - `D6`
- parent candidate summary `C5`
- parent tension `T3`

Preserved limits:
- this batch does not deny the shared runner hash
- it preserves only that hash continuity is weaker than behavioral identity

## Candidate RC5) `ASYMMETRIC_PAIR_AXIS2_ORIENTATION_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest asymmetric-pair packet in the parent batch is:
  - `SEQ03` and `SEQ04` both store:
    - `seni_within = 1`
    - `nesi_within = 1`
  - but their worst axis2 failures diverge:
    - `SEQ03`: `seta_bad = 4`, `setb_bad = 2`
    - `SEQ04`: `seta_bad = 2`, `setb_bad = 4`
- the asymmetric pair shares one axis1 profile while splitting on axis2 orientation

Why this survives reduction:
- it is the parent batch's clearest asymmetric-class refinement
- later summaries need a compact rule for keeping `SEQ03` and `SEQ04` distinct rather than flattening them into one asymmetric duplicate

Source lineage:
- parent clusters:
  - `B`
  - `C`
- parent distillates:
  - `D2`
  - `D3`
  - `D6`
- parent candidate summary `C3`
- parent tension `T4`

Preserved limits:
- this batch does not deny that `SEQ03` and `SEQ04` belong to the same broader asymmetric pair
- it preserves only that their axis2 orientation remains distinct

## Candidate RC6) `BALANCED_PAIR_NONSEPARATION_LIMIT_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest balanced-pair caution in the parent batch is:
  - `SEQ01` and `SEQ02` both store:
    - `seta_bad = 2`
    - `setb_bad = 2`
    - `seni_within = 0`
    - `nesi_within = 0`
  - the local metric layer therefore does not separate the balanced pair on stored counts alone
- the balanced pair is retained, but not resolved, by the current metric layer

Why this survives reduction:
- it is the parent batch's clearest limit packet for the balanced class
- later summaries need a compact rule for not overstating what the current stored counts can distinguish

Source lineage:
- parent clusters:
  - `B`
  - `C`
- parent distillates:
  - `D2`
  - `D3`
  - `D6`
- parent candidate summary `C3`
- parent tension `T5`

Preserved limits:
- this batch does not deny that `SEQ01` and `SEQ02` remain distinct sequence labels
- it preserves only that the current stored counts do not separate them

## Quarantined Residue Q1) `LOCAL_SURFACE_AS_REPOTOP_ADMITTED_VIA_SHARED_HASH`
Status:
- `QUARANTINED`

Preserved residue:
- `V2` shares the current runner hash
- all retold as if the local surface SIM_ID were therefore repo-top admitted

Why it stays quarantined:
- the parent batch explicitly preserves omission of the local surface SIM_ID from the repo-held evidence pack
- shared hash is weaker than local-surface admission

Source lineage:
- parent distillates:
  - `D4`
  - `D6`
- parent candidate summary `C4`
- parent tension `T1`

## Quarantined Residue Q2) `V2_AS_FULL_LOCAL_METRIC_SURFACE`
Status:
- `QUARANTINED`

Preserved residue:
- admitted `V2` descendant under the same runner hash
- all treated as if it retained the full local four-layer metric surface

Why it stays quarantined:
- the parent batch explicitly preserves a narrower edge-only descendant contract
- descendant admission is weaker than full local metric retention

Source lineage:
- parent distillates:
  - `D2`
  - `D4`
  - `D6`
- parent candidate summary `C5`
- parent tension `T2`

## Quarantined Residue Q3) `SAME_HASH_AS_BEHAVIORAL_IDENTITY`
Status:
- `QUARANTINED`

Preserved residue:
- same-hash provenance between the local surface and `V2`
- all treated as if the stored `seni` behavior therefore matched exactly

Why it stays quarantined:
- the parent batch explicitly preserves `seni` divergence for `SEQ03/SEQ04`
- shared hash is weaker than behavioral identity

Source lineage:
- parent distillates:
  - `D4`
  - `D6`
- parent candidate summary `C5`
- parent tension `T3`

## Quarantined Residue Q4) `SEQ03_SEQ04_AS_ONE_UNDIFFERENTIATED_ASYMMETRIC_CLASS`
Status:
- `QUARANTINED`

Preserved residue:
- the asymmetric pair label
- all treated as if `SEQ03` and `SEQ04` were one duplicated class with no internal orientation split

Why it stays quarantined:
- the parent batch explicitly preserves opposite axis2 failure orientation across the pair
- shared asymmetric classification is weaker than identical local role

Source lineage:
- parent distillates:
  - `D3`
  - `D6`
- parent candidate summary `C3`
- parent tension `T4`

## Quarantined Residue Q5) `BALANCED_PAIR_AS_SEMANTICALLY_RESOLVED`
Status:
- `QUARANTINED`

Preserved residue:
- the balanced pair label
- all treated as if the current stored counts fully resolved `SEQ01` and `SEQ02`

Why it stays quarantined:
- the parent batch explicitly preserves no stored count separation inside the balanced pair
- balanced labeling is weaker than semantic resolution

Source lineage:
- parent distillates:
  - `D3`
  - `D6`
- parent candidate summary `C3`
- parent tension `T5`

# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / A2-MID SELECTION NOTE
Batch: `BATCH_A2MID_stage16_mix_contract_baseline__v1`
Date: 2026-03-09

## Why this parent batch was selected
- it is the next strong Stage16 intake batch after the successor-bundle provenance pass
- it already cleanly exposes:
  - one mixed-axis6 Stage16 question-family
  - one paired-control contract and one sweep contract
  - one exact `sub4_axis6u` baseline anchor that must not be merged
  - one clear catalog-versus-top-level-evidence split
  - one real effect-scale and dominant-cell asymmetry between control and sweep
- that makes it a strong bounded contradiction-reprocess target without rereading raw sims artifacts

## Why this reduction is bounded
- the pass keeps only the smaller reusable packets:
  - mixed-family identity with contract split
  - noninterchangeability between paired control and sweep modes
  - exact baseline anchoring without family merge
  - catalog grouping with top-level evidence absence
  - control-versus-sweep scale asymmetry
  - Se-dominant control versus Si-dominant sweep signal placement
- the pass does not reopen raw runner or result files because the parent batch already extracted the needed tensions

## Why comparison anchors were used
- `BATCH_A2MID_sims_evidence_boundary__v1`
  - used because it gives the nearest sims-wide catalog/evidence separation and evidence-transport boundary packet
- `BATCH_A2MID_sim_suite_v1_descendant_provenance_split__v1`
  - used because it gives the nearest earlier Stage16 warning that local Stage16 surfaces, stored identity, and current top-level provenance can diverge
- `BATCH_A2MID_sim_suite_v2_externalized_provenance__v1`
  - used because it gives the nearest successor-side version/provenance drift packet for the same Stage16 neighborhood

## Why no raw reread was needed
- the parent batch already extracted the relevant contract split, baseline identity, admission gap, and dominant-cell shift
- the needed work here was second-pass narrowing and quarantine, not source recovery

## Deferred alternatives
- `BATCH_sims_stage16_sub4_axis6u_absolute_surface__v1`
  - deferred to the next bounded step because this pass is about the mixed family and its exact baseline relation, not the standalone absolute baseline surface itself
- `fresh_raw_stage16_mix_family_reread`
  - deferred because this thread prefers existing intake artifacts unless a parent batch proves insufficient

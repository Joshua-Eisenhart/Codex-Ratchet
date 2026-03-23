# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_active_lineage_schema_reuse_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Candidate RC1: `ACTIVE_CHAIN_COMPLETENESS_AUDIT_RULE`
- candidate read:
  - the active-system intake chain is structurally complete at the packet layer:
    - `14` active batches are present
    - `84` batch-local artifacts are present
    - every active batch currently has the required six-artifact packet
  and this completeness should be preserved as a verification fact rather than rederived by reopening the source sweep
- why candidate:
  - this is the parent audit's strongest bounded verification result
- parent dependencies:
  - `CLUSTER_MAP__v1:Cluster A`
  - `A2_3_DISTILLATES__v1:D1`
  - `A2_3_DISTILLATES__v1:D2`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C1`

## Candidate RC2: `REDUCTION_LINEAGE_IS_CLEAR_EVEN_WHEN_LINK_STYLE_DRIFTS`
- candidate read:
  - the active reduction chain remains clear in practice:
    - first-pass intake layer
    - postsweep cross-batch reduction
    - operator kernel capsule
    - operator boot card
    - audit layer
  even though explicit parent-link styles differ across those stages
- why candidate:
  - this preserves the parent audit's main lineage result without flattening away the visible drift in how lineage is encoded
- parent dependencies:
  - `CLUSTER_MAP__v1:Cluster B`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C3`
  - `TENSION_MAP__v1:T2`

## Candidate RC3: `MANIFEST_SCHEMA_HETEROGENEITY_IS_REAL_NOT_NOISE`
- candidate read:
  - lineage is intact but not schema-uniform:
    - first-pass packets and the postsweep reduction are source-membership centered
    - the operator kernel capsule is intentionally lighter and parent-batch centered
    - the operator boot card mixes parent linkage and source membership
  and that heterogeneity should be preserved as a real audit fact rather than normalized away inside the verification layer
- why candidate:
  - this is the parent audit's sharpest schema-side fence and the best preparation for a later manifest bridge
- parent dependencies:
  - `CLUSTER_MAP__v1:Cluster C`
  - `A2_3_DISTILLATES__v1:D3`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C2`
  - `TENSION_MAP__v1:T1`

## Candidate RC4: `CONTRADICTION_CORRIDORS_SURVIVE_THE_FULL_CHAIN`
- candidate read:
  - the most repeated contradiction corridors remain stable across the verified chain:
    - narrow authority versus wide operational shell
    - direct entropy pressure versus colder executable routing
    - useful generated or reduced artifacts versus nonowner status
    - thin operator recall versus thick real boot or decision context
  so the audit should be read as confirming corridor stability rather than resolving those contradictions
- why candidate:
  - this preserves the parent audit's highest-value continuity signal
- parent dependencies:
  - `A2_3_DISTILLATES__v1:D4`
  - `A2_3_DISTILLATES__v1:D5`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C4`
  - `TENSION_MAP__v1:T5`
  - `TENSION_MAP__v1:T6`

## Candidate RC5: `TIERED_REUSE_REQUIRES_REOPEN_PARENT_DISCIPLINE`
- candidate read:
  - safe reuse remains explicitly tiered:
    - use the boot card for fast recall
    - use the kernel capsule for operator orientation
    - use the cross-batch reduction for system-scale mapping
    - reopen first-pass batches before decisions, promotion claims, or mutations
  and the audit should preserve that reopen-parent rule rather than acting as a shortcut around it
- why candidate:
  - this is the parent audit's most operationally useful reuse fence
- parent dependencies:
  - `CLUSTER_MAP__v1:Cluster D`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C5`
  - `TENSION_MAP__v1:T3`
  - `TENSION_MAP__v1:T4`

## Candidate RC6: `AUDIT_LAYER_VERIFIES_BUT_DOES_NOT_CLOSE_THE_CHAIN`
- candidate read:
  - the audit confirms completeness, lineage, and reuse limits, but it does not settle authority, promotion, mutation, or the core contradiction between narrow authority and the wider operational shell
- why candidate:
  - this is the parent audit's main anti-overread fence and the right endpoint for a bounded verification reduction
- parent dependencies:
  - `A2_2_CANDIDATE_SUMMARIES__v1:C6`
  - `A2_3_DISTILLATES__v1:D6`
  - `A2_3_DISTILLATES__v1:D7`

## Quarantined Q1: `VERIFICATION_LAYER_AS_SCHEMA_NORMALIZATION`
- quarantine read:
  - do not treat this audit reduction as if it had normalized the active manifest chain into one schema; schema heterogeneity remains part of the preserved lineage record
- why quarantined:
  - the parent explicitly treats manifest drift as real evidence rather than cleanup residue
- parent dependencies:
  - `TENSION_MAP__v1:T1`
  - `TENSION_MAP__v1:T2`
  - `A2_3_DISTILLATES__v1:D3`

## Quarantined Q2: `AUDIT_SUCCESS_AS_AUTHORITY_OR_MUTATION_PERMISSION`
- quarantine read:
  - do not read audit completeness or reuse clarity as permission to settle authority, make promotion claims, or mutate active surfaces without reopening the thicker parent layers the audit points back to
- why quarantined:
  - the parent explicitly frames reuse as tiered and escalation-based rather than self-authorizing
- parent dependencies:
  - `TENSION_MAP__v1:T3`
  - `TENSION_MAP__v1:T4`
  - `A2_3_DISTILLATES__v1:D6`

# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_active_ingest_promotion_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Candidate RC1: `HETEROGENEOUS_INGEST_PACKET_LINEAGE_RULE`
- candidate read:
  - active ingest retention should preserve packet heterogeneity explicitly:
    - `COMPLETE`
    - `PARTIAL`
    - `NOT_PRESENT`
  and should not average later completeness upward just because the packet family is operationally useful
- why candidate:
  - this is the cleanest controller-facing reduction of the parent ingest-storage packet
- parent dependencies:
  - `CLUSTER_MAP__v1:Cluster A`
  - `A2_3_DISTILLATES__v1:D1`
  - `A2_3_DISTILLATES__v1:D2`
  - `A2_3_DISTILLATES__v1:D3`
  - `TENSION_MAP__v1:T1`
  - `TENSION_MAP__v1:T2`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C1`

## Candidate RC2: `FAIL_CLOSED_ROSETTA_ABSENCE_GATE`
- candidate read:
  - controller-side rosetta handling should keep the anti-fabrication rule explicit:
    - preserve evidenced rows with locators when locks exist
    - preserve empty tables and absence markers when locks do not exist
    - do not seed rows from memory to fill the gap
- why candidate:
  - this is the strongest reusable engineering rule in the parent and the clearest anti-hallucination packet
- parent dependencies:
  - `CLUSTER_MAP__v1:Cluster B`
  - `A2_3_DISTILLATES__v1:D4`
  - `A2_3_DISTILLATES__v1:D5`
  - `TENSION_MAP__v1:T4`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C3`

## Candidate RC3: `RUNNABLE_PROPOSAL_EDGE_LANE_TRIAGE`
- candidate read:
  - active lane triage should preserve the current runnable floor as:
    - entropy correlation executable branch
    - entropy structure seeded continuation
    - broad entropy rescue route
    - substrate and enrichment families
  while keeping six-term entropy bridge work proposal-side and holodeck/direct classical-engine work fenced at the A2 edge
- why candidate:
  - this is the sharpest compact reduction of the parent validation-target and promotion-boundary cluster
- parent dependencies:
  - `CLUSTER_MAP__v1:Cluster C`
  - `A2_3_DISTILLATES__v1:D6`
  - `A2_3_DISTILLATES__v1:D7`
  - `TENSION_MAP__v1:T6`
  - `TENSION_MAP__v1:T7`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C1`

## Candidate RC4: `SOURCE_BOUND_PROMOTION_AUDIT_ON_EXCLUDED_EVIDENCE`
- candidate read:
  - family-promotion audits and contracts remain useful active A2 reads, but when they rely on excluded `runs/` and `run_anchor_surface/` evidence they must stay source-bound rather than being treated as re-earned proof in this lane
- why candidate:
  - this is the parent's cleanest controller-facing boundary against over-promoting audit language into lower-loop truth
- parent dependencies:
  - `CLUSTER_MAP__v1:Cluster C`
  - `A2_3_DISTILLATES__v1:D8`
  - `A2_3_DISTILLATES__v1:D11`
  - `TENSION_MAP__v1:T5`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C7`

## Candidate RC5: `PASS_WITH_DEBT_NONCLOSURE_RULE`
- candidate read:
  - post-update PASS language should be retained only together with the same surface's debt, open-issue, and blocker inventory; PASS does not mean the lane is closed, saturated issues are solved, or helper residue is gone
- why candidate:
  - this is the sharpest reduction of the parent audit contradiction and it compresses the mixed-state read into one controller rule
- parent dependencies:
  - `CLUSTER_MAP__v1:Cluster D`
  - `A2_3_DISTILLATES__v1:D9`
  - `TENSION_MAP__v1:T6`
  - `TENSION_MAP__v1:T8`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C2`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C4`

## Candidate RC6: `FULL_SURFACE_CLASSIFICATION_IS_CROSSCHECK_NOT_SUPERSEDER`
- candidate read:
  - the full-surface integration audit is best used as:
    - a lean classification cross-check
    - a repo-shape confirmation surface
    - not a superseding authority that erases earlier source-bounded batching of root docs, specs, or active state families
- why candidate:
  - this keeps the parent's whole-tree audit useful without letting one classification plaque replace the actual read order
- parent dependencies:
  - `CLUSTER_MAP__v1:Cluster E`
  - `A2_3_DISTILLATES__v1:D10`
  - `TENSION_MAP__v1:T9`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C5`

## Quarantined Q1: `INGEST_MEMORY_UPDATE_INTENT_AS_EXECUTED_ACTIVE_MUTATION_FACT`
- quarantine read:
  - do not treat the ingest packet family's memory-update wording as if this intake lane has directly mutated active A2/A1 stores
- why quarantined:
  - the parent preserves intended downstream memory effects, but this worker lane remains intake-only and proposal-side
- parent dependencies:
  - `TENSION_MAP__v1:T3`
  - `A2_3_DISTILLATES__v1:D1`
  - `A2_3_DISTILLATES__v1:D3`

## Quarantined Q2: `ACTIVE_PROVEN_AS_CLOSED_REPO_WIDE_SUCCESS`
- quarantine read:
  - do not collapse active/proven promotion reads, PASS verdicts, and repo-integration optimism into one closed-success story
- why quarantined:
  - the parent explicitly preserves saturation, pending closure, helper residue, open issues, and unresolved entropy-lane blockers in the same packet family
- parent dependencies:
  - `TENSION_MAP__v1:T6`
  - `TENSION_MAP__v1:T8`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C2`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C4`

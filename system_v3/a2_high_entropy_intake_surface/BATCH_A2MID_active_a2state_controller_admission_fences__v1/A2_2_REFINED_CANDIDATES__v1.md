# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_active_a2state_controller_admission_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Candidate RC1: `INPUT_TRUST_AND_QUARANTINE_GATE`
- candidate read:
  - controller intake should classify candidate inputs by trust tier and quarantine reason before any downstream reuse or reduction decision
- why candidate:
  - this is the cleanest controller-facing reduction of the parent trust and source-precedence packet
- parent dependencies:
  - `CLUSTER_MAP__v1:Cluster A`
  - `A2_3_DISTILLATES__v1:D1`
  - `TENSION_MAP__v1:T2`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C1`

## Candidate RC2: `OUTSIDE_PATTERN_METHOD_NOT_WORLDVIEW_RULE`
- candidate read:
  - outside systems may be borrowed for control methods, transport patterns, anti-drift structure, or replay logic, but not as worldview or ontology imports
- why candidate:
  - this gives the controller a compact filter for adjacent-model reuse without semantic contamination
- parent dependencies:
  - `CLUSTER_MAP__v1:Cluster A`
  - `A2_3_DISTILLATES__v1:D3`
  - `TENSION_MAP__v1:T2`

## Candidate RC3: `FOUNDATION_VS_SCAFFOLD_LANE_TRIAGE`
- candidate read:
  - controller lane triage should distinguish machinery-proofing/scaffold work from genuine foundation-building, and shift priority toward foundation-mode when the blocker is not true machinery failure
- why candidate:
  - this is the strongest compact controller rule in the parent for deciding what kind of work a lane is really doing
- parent dependencies:
  - `CLUSTER_MAP__v1:Cluster B`
  - `A2_3_DISTILLATES__v1:D2`
  - `A2_3_DISTILLATES__v1:D7`
  - `TENSION_MAP__v1:T4`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C5`

## Candidate RC4: `ENTROPY_FRONTIER_STEERING_OVER_WORDING_CHURN`
- candidate read:
  - the controller should treat the entropy lane as a stable failure-frontier problem that needs cluster-aware rescue and residue-aware bridge work, not more broad wording churn
- why candidate:
  - this is the most actionable reduction of the parent entropy rescue and topology packet
- parent dependencies:
  - `CLUSTER_MAP__v1:Cluster C`
  - `CLUSTER_MAP__v1:Cluster D`
  - `A2_3_DISTILLATES__v1:D4`
  - `A2_3_DISTILLATES__v1:D5`
  - `A2_3_DISTILLATES__v1:D6`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C2`

## Candidate RC5: `HOLODECK_A2_EDGE_SEAL`
- candidate read:
  - holodeck/world-edge work may remain as A2-edge memory and world-model fuel, but it must not bypass A2 and touch lower-loop truth paths directly
- why candidate:
  - this gives the controller a narrow placement rule for world-model exploration without architecture contamination
- parent dependencies:
  - `CLUSTER_MAP__v1:Cluster E`
  - `A2_3_DISTILLATES__v1:D8`
  - `TENSION_MAP__v1:T7`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C6`

## Quarantined Q1: `PLAYBOOK_DIRECT_ACTIVE_A2_MUTATION`
- quarantine read:
  - do not treat playbook instructions to update `MODEL_CONTEXT.md` or `INTENT_SUMMARY.md` as permission to mutate active A2 from this intake lane
- why quarantined:
  - the parent preserves intended downstream integration, but this thread remains intake-surface only
- parent dependencies:
  - `TENSION_MAP__v1:T3`
  - `A2_3_DISTILLATES__v1:D9`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C3`

## Quarantined Q2: `HUMAN_AUTO_TOPOLOGY_NUMERIC_COLLAPSE`
- quarantine read:
  - do not collapse the human-readable and auto-generated entropy-topology surfaces into one numerically settled truth from this pass
- why quarantined:
  - the parent preserves a qualitative match with numeric/presentation mismatch that deserves its own contradiction pass
- parent dependencies:
  - `TENSION_MAP__v1:T5`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C4`

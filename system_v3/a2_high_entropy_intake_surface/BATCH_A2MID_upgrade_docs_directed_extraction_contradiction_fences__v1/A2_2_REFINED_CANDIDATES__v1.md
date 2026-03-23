# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_upgrade_docs_directed_extraction_contradiction_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Candidate RC1: `DIRECTED_EXTRACTION_AFTER_BROAD_SWEEP_SATURATION`
- candidate read:
  - once broad extraction is hitting diminishing returns, controller reads should pivot to bounded question-driven extraction instead of extending the generic sweep
- why candidate:
  - this is the cleanest controller reduction of the parent’s method shift
- parent dependencies:
  - `CLUSTER_MAP__v1:C1`
  - `A2_3_DISTILLATES__v1:D1`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C1`

## Candidate RC2: `ANSWER_VARIANT_DELTA_IS_SIGNAL_NOT_NOISE`
- candidate read:
  - when two answer sheets address the same bounded questions, their divergence should be preserved as a controller instability signal rather than flattened into one synthetic answer
- why candidate:
  - this turns the parent’s highest-value contradiction feature into a direct controller rule
- parent dependencies:
  - `CLUSTER_MAP__v1:C8`
  - `A2_3_DISTILLATES__v1:D3`
  - `TENSION_MAP__v1:T1`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C2`

## Candidate RC3: `ZIP_TRANSPORT_CORE_STABLE_VARIANT_EDGES_QUARANTINED`
- candidate read:
  - controller reads may reuse the shared ZIP transport core, but variant extras and proposal-side overlay naming should remain quarantined until independently stabilized
- why candidate:
  - this is the strongest controller-facing reduction of the parent’s ZIP-family split
- parent dependencies:
  - `CLUSTER_MAP__v1:C2`
  - `A2_3_DISTILLATES__v1:D2`
  - `A2_3_DISTILLATES__v1:D4`
  - `TENSION_MAP__v1:T2`
  - `TENSION_MAP__v1:T7`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C5`

## Candidate RC4: `FULL_PLUS_AND_FULL_PLUS_PLUS_CONFIRMATION_REMAIN_UNSETTLED`
- candidate read:
  - FULL+ and FULL++ confirmation semantics should be treated as unresolved across structural-versus-content meaning, refusal behavior, required-versus-optional confirmation, and unconfirmed FULL++ status
- why candidate:
  - this isolates the parent’s tightest contradiction cluster into a controller nonsettlement fence
- parent dependencies:
  - `CLUSTER_MAP__v1:C5`
  - `CLUSTER_MAP__v1:C7`
  - `A2_3_DISTILLATES__v1:D3`
  - `A2_3_DISTILLATES__v1:D7`
  - `TENSION_MAP__v1:T3`
  - `TENSION_MAP__v1:T4`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C4`

## Candidate RC5: `QUALITATIVE_GUIDANCE_WITHOUT_FALSE_NUMERIC_LOCK`
- candidate read:
  - batch-scale, sharding, and exploration-to-convergence guidance should be preserved as directional and partly human-judged without overpromoting concrete-looking markers into fixed ratcheted policy
- why candidate:
  - this gives the controller a compact caution fence across the remaining three policy seams
- parent dependencies:
  - `CLUSTER_MAP__v1:C3`
  - `CLUSTER_MAP__v1:C4`
  - `CLUSTER_MAP__v1:C6`
  - `A2_3_DISTILLATES__v1:D5`
  - `A2_3_DISTILLATES__v1:D6`
  - `A2_3_DISTILLATES__v1:D8`
  - `TENSION_MAP__v1:T5`
  - `TENSION_MAP__v1:T6`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C3`

## Quarantined Q1: `ROSETTA_OVERLAY_ZIP_AS_ESTABLISHED_TRANSPORT_TYPE`
- quarantine read:
  - do not treat `ROSETTA_OVERLAY_ZIP` as an established ZIP type from this pass
- why quarantined:
  - the parent preserves it as variant proposal-side naming that conflicts with the audit’s do-not-design posture
- parent dependencies:
  - `CLUSTER_MAP__v1:C2`
  - `A2_3_DISTILLATES__v1:D4`
  - `TENSION_MAP__v1:T2`
  - `TENSION_MAP__v1:T7`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C3`

## Quarantined Q2: `STRONGER_CONFIRMATION_CLAIMS_AS_SETTLED_DOCTRINE`
- quarantine read:
  - do not promote source 1’s stronger FULL+ and FULL++ confirmation claims into settled doctrine
- why quarantined:
  - the parent explicitly preserves unresolved confirmation semantics across the two answer variants
- parent dependencies:
  - `CLUSTER_MAP__v1:C5`
  - `A2_3_DISTILLATES__v1:D7`
  - `TENSION_MAP__v1:T3`
  - `TENSION_MAP__v1:T4`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C3`

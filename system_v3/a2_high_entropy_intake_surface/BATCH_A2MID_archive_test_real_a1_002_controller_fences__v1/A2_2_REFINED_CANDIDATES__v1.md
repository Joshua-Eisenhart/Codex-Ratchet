# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_archive_test_real_a1_002_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Candidate RC1: `TEST_REAL_A1_002_PRESERVES_A_TWO_STEP_PACKET_SPINE_WITH_NO_QUEUED_CONTINUATION`
- candidate read:
  - controller reads should preserve that `TEST_REAL_A1_002` has a compact two-step execution with a balanced `2/2/2/2` packet lattice and no queued continuation packet in `a1_inbox/`
- why candidate:
  - this is the parent's strongest execution-shape fence
- parent dependencies:
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:Candidate Summary A`
  - `A2_3_DISTILLATES__v1.md:Distillate 1`
  - `CLUSTER_MAP__v1.md:Cluster 1`

## Candidate RC2: `REAL_A1_NAMING_DOES_NOT_OUTRANK_REPLAY_ATTRIBUTION_OR_EMPTY_INBOX_LINEAGE`
- candidate read:
  - controller reads should preserve the run-id claim `TEST_REAL_A1_002` alongside:
    - `a1_source replay`
    - `needs_real_llm false`
    - empty `a1_inbox/`
  without letting any one label rewrite the archive lineage surface by itself
- why candidate:
  - this is the parent's clearest naming-versus-lineage authority fence
- parent dependencies:
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:Candidate Summary B`
  - `A2_3_DISTILLATES__v1.md:Distillate 2`
  - `CLUSTER_MAP__v1.md:Cluster 2`
  - `TENSION_MAP__v1.md:Tension 1`

## Candidate RC3: `HIDDEN_HASH_BRIDGES_STAY_VISIBLE_AND_THE_MISSING_SEQUENCE_LEDGER_STAYS_MISSING`
- candidate read:
  - controller reads should preserve both closure splits:
    - step 1 ends on `7a249c9e...` while step 2 begins from `cc9ebfe4...`
    - the last event ends on `7716a637...` while summary/state bind to `b87bc843...`
  and should keep the missing `sequence_state.json` as a real retention gap rather than a surface to reconstruct
- why candidate:
  - this is the parent's narrowest closure-layer fence
- parent dependencies:
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:Candidate Summary B`
  - `A2_3_DISTILLATES__v1.md:Distillate 3`
  - `CLUSTER_MAP__v1.md:Cluster 5`
  - `TENSION_MAP__v1.md:Tension 2`
  - `TENSION_MAP__v1.md:Tension 3`
  - `TENSION_MAP__v1.md:Tension 4`

## Candidate RC4: `ONE_STRATEGY_ID_CAN_DESCEND_FROM_PERTURBATION_T1_TO_BASELINE_T0`
- candidate read:
  - controller reads should preserve that both retained strategy packets use one `strategy_id`, while the inner step regime descends from:
    - `PERTURBATION / T1_COMPOUND`
    - to `BASELINE / T0_ATOM`
  across step 1 and step 2
- why candidate:
  - this is the parent's clearest multi-step family-descent seam
- parent dependencies:
  - `A2_3_DISTILLATES__v1.md:Distillate 4`
  - `CLUSTER_MAP__v1.md:Cluster 3`

## Candidate RC5: `SECOND_STEP_SCHEMA_FAIL_AND_BLANK_TARGET_NEGATIVE_CLASS_STAY_CORRELATED_NOT_CAUSALLY_CLOSED`
- candidate read:
  - controller reads should preserve that step 2 carries:
    - `SCHEMA_FAIL / ITEM_PARSE / STAGE_2_SCHEMA_CHECK`
    - a paired export block where the target `NEGATIVE_CLASS` is blank and the alternative still retains `NEG_BOUNDARY`
  without promoting that correlation into a stronger causal claim than the archive proves
- why candidate:
  - this is the parent's narrowest fail-surface fence
- parent dependencies:
  - `CLUSTER_MAP__v1.md:Cluster 4`
  - `TENSION_MAP__v1.md:Tension 5`
  - `A2_3_DISTILLATES__v1.md:Distillate 4`

## Candidate RC6: `MIXED_SURVIVOR_LINEAGE_AND_EMPTY_KILL_BOOKKEEPING_PREVENT_SEMANTIC_CLOSURE`
- candidate read:
  - controller reads should preserve that the second-step proposal advances both lanes to `S0002`, but final survivor lineage is mixed:
    - `S_SIM_ALT_OMEGA_ALT_S0002` survives
    - `S_SIM_TARGET_SIGMA_S0002` does not
    - `S_SIM_TARGET_SIGMA_S0001` remains
  while both SIM packets emit `NEG_NEG_BOUNDARY`, final state keeps `kill_log` empty, and promotion status remains `PARKED`
- why candidate:
  - this is the parent's strongest anti-closure fence
- parent dependencies:
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:Candidate Summary C`
  - `A2_3_DISTILLATES__v1.md:Distillate 5`
  - `CLUSTER_MAP__v1.md:Cluster 6`
  - `CLUSTER_MAP__v1.md:Cluster 7`
  - `TENSION_MAP__v1.md:Tension 6`
  - `TENSION_MAP__v1.md:Tension 7`

## Quarantined Q1: `REAL_A1_RUN_NAME_AS_PROOF_OF_REAL_LLM_OR_ACTIVE_RUNTIME_AUTHORITY`
- quarantine read:
  - do not let the run name `TEST_REAL_A1_002` outweigh replay attribution, empty inbox lineage, or archive-only handling
- why quarantined:
  - the parent preserves a naming-versus-lineage contradiction rather than earned real-LLM authority
- parent dependencies:
  - `CLUSTER_MAP__v1.md:Cluster 2`
  - `TENSION_MAP__v1.md:Tension 1`
  - `MANIFEST.json`

## Quarantined Q2: `MISSING_SEQUENCE_LEDGER_RECONSTRUCTED_AS_IF_RETAINED`
- quarantine read:
  - do not synthesize a clean sequence ledger from the visible packet lattice and hash chain as if that surface still existed
- why quarantined:
  - the parent explicitly preserves the missing ledger as a real retention gap
- parent dependencies:
  - `CLUSTER_MAP__v1.md:Cluster 5`
  - `TENSION_MAP__v1.md:Tension 2`
  - `TENSION_MAP__v1.md:Tension 3`

## Quarantined Q3: `STEP2_S0002_PROPOSAL_AS_PROOF_OF_CLEAN_FULL_ADVANCEMENT`
- quarantine read:
  - do not treat the step-2 `S0002` proposal surface as proof that both target and alternative lineages advanced cleanly into final state
- why quarantined:
  - the parent explicitly preserves mixed survivor carryover instead
- parent dependencies:
  - `CLUSTER_MAP__v1.md:Cluster 6`
  - `TENSION_MAP__v1.md:Tension 6`

## Quarantined Q4: `ZERO_PACKET_PARKS_AND_EMPTY_KILL_LOG_AS_PROOF_OF_SEMANTIC_CLOSURE`
- quarantine read:
  - do not let clean packet counters or empty final kill bookkeeping erase the retained `PARKED` promotion states and SIM kill signals
- why quarantined:
  - the parent explicitly preserves open semantic residue beneath clean transport counts
- parent dependencies:
  - `CLUSTER_MAP__v1.md:Cluster 7`
  - `TENSION_MAP__v1.md:Tension 7`


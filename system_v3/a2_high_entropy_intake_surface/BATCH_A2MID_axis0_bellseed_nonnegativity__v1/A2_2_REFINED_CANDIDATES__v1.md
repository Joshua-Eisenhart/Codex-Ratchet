# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_axis0_bellseed_nonnegativity__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Candidate RC1) `AXIS0_BELLSEED_ENTANGLE_PAIR_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- `run_axis0_sagb_entangle_seed.py` and `results_axis0_sagb_entangle_seed.json` should stay compressed as:
  - one standalone Bell-seed entangle residual pair
  - one runner plus one paired result
  - one bounded family rather than one merged zero-negativity omnibus block

Why this survives reduction:
- it is the parent batch's cleanest family-shell claim
- it preserves the Bell-seed pair as its own reusable unit inside the residual lane

Source lineage:
- parent cluster `A`
- parent distillate `D1`
- parent candidate summaries:
  - `C1`
  - `C2`

Preserved limits:
- this batch does not absorb the next residual pair
- it preserves only the current Bell-seed pair as one bounded family

## Candidate RC2) `RANDOMIZED_BELLSCRAMBLE_WITH_DETERMINISTIC_OUTPUT_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest initialization-versus-outcome seam in the parent batch is:
  - each trial begins from a Bell seed with randomized local scramble
  - stored branch ranges collapse to floating-point-noise scale:
    - branch `MI` ranges `= 2.6645352591003757e-15`
    - branch `SAgB` ranges `~ 2.5e-15`
- randomized initialization does not automatically imply meaningful stored trial dispersion

Why this survives reduction:
- it is the parent batch's clearest determinism packet
- later summaries need a compact rule for describing the family as effectively deterministic at stored precision

Source lineage:
- parent cluster `B`
- parent distillates:
  - `D2`
  - `D6`
- parent candidate summary `C5`
- parent tension `T1`

Preserved limits:
- this batch does not deny that local scrambling is real
- it preserves only that the stored output is effectively deterministic at the retained precision

## Candidate RC3) `ENTANGLING_SETUP_WITH_ZERO_NEGATIVITY_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest setup-versus-negativity seam in the parent batch is:
  - Bell seed
  - weak noise `0.005`
  - `2` `CNOT` repetitions per terrain step
  - both branches still store:
    - `neg_SAgB_frac = 0.0`
    - positive `SAgB_min`
- strongly entangling setup does not automatically imply negative conditional entropy in storage

Why this survives reduction:
- it is the parent batch's clearest anti-projection packet
- later summaries need a compact rule for blocking negativity overread from the family setup alone

Source lineage:
- parent clusters:
  - `B`
  - `C`
- parent distillates:
  - `D3`
  - `D6`
- parent candidate summary `C4`
- parent tension `T2`

Preserved limits:
- this batch does not deny that the setup is intentionally entangling
- it preserves only that the stored surface remains fully nonnegative

## Candidate RC4) `POSITIVE_SPACE_BRANCH_DISCRIMINATION_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the family should preserve one compact discrimination packet:
  - `delta_MI_mean_SEQ02_minus_SEQ01 = 9.72232227303138e-06`
  - `delta_SAgB_min_SEQ02_minus_SEQ01 = -2.675544964136911e-05`
  - `delta_negfrac_SEQ02_minus_SEQ01 = 0.0`
- the family stores tiny branch discrimination in positive `S(A|B)` space rather than negativity space

Why this survives reduction:
- it is the parent batch's clearest branch-difference packet
- it blocks a simplistic equation between small branch deltas and negativity success

Source lineage:
- parent cluster `C`
- parent distillate `D3`
- parent candidate summary `C3`
- parent tension `T3`
- comparison anchor:
  - `BATCH_A2MID_axis0_ab_mi_revival__v1:RC4`

Preserved limits:
- this batch does not deny that the branch deltas are real
- it preserves only that they remain weaker than any negativity-success claim

## Candidate RC5) `FIXED_CONTRACT_NONNEGATIVITY_VS_SEARCH_FAILURE_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the comparison to the prior negativity-stress family should keep one distinction packet:
  - the prior stress family searched `3456` settings and still stored `best.score = 0.0`
  - the current family is one fixed Bell-seed contract that also stores zero negativity
- same stored nonnegativity outcome does not mean the same failure mode

Why this survives reduction:
- it is the parent batch's clearest anti-flattening comparison packet
- later backlog work needs a compact rule for preserving fixed-contract nonnegativity versus search-failure nonnegativity

Source lineage:
- parent clusters:
  - `D`
  - `E`
- parent distillates:
  - `D5`
  - `D6`
- parent candidate summary `C3`
- parent tension `T4`
- comparison anchor:
  - `BATCH_A2MID_axis0_negsagb_search_failure__v1:RC2`

Preserved limits:
- this batch does not deny that both families currently store zero negativity
- it preserves only that the path to that outcome is different

## Candidate RC6) `LOCAL_BELLSEED_EVIDENCE_WITHOUT_REPOTOP_ADMISSION_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest evidence-status packet in the parent batch is:
  - the catalog lists the family
  - the runner emits a local evidence block
  - the repo-held top-level evidence pack omits the local `SIM_ID`
- local evidence and catalog visibility must stay weaker than repo-top admission

Why this survives reduction:
- it is the parent batch's main visibility contradiction
- later residual summaries need the family kept source-real and locally evidenced without overstating its repo-top status

Source lineage:
- parent cluster `E`
- parent distillate `D4`
- parent tension `T5`
- comparison anchor:
  - `BATCH_A2MID_sims_evidence_boundary__v1:RC3`

Preserved limits:
- this batch does not deny the local evidence contract
- it preserves only that local evidence, catalog presence, and repo-top admission are not the same layer

## Quarantined Residue Q1) `RANDOM_BELL_SCRAMBLE_AS_MEANINGFUL_TRIAL_VARIANCE`
Status:
- `QUARANTINED`

Preserved residue:
- randomized Bell-seed scrambling at every trial
- all retold as if it produced meaningful stored trial dispersion

Why it stays quarantined:
- the parent batch explicitly preserves branch ranges only at floating-point-noise scale
- randomized initialization is weaker than substantive stored variance

Source lineage:
- parent distillates:
  - `D2`
  - `D6`
- parent candidate summary `C5`
- parent tension `T1`

## Quarantined Residue Q2) `BELL_SEED_PLUS_CNOT_AS_NEGATIVITY_PROOF`
Status:
- `QUARANTINED`

Preserved residue:
- Bell seed, weak noise, and repeated `CNOT` coupling
- all treated as if that setup alone proved negative conditional entropy in the stored surface

Why it stays quarantined:
- the parent batch explicitly preserves zero stored negativity in both branches
- entangling setup is weaker than negativity proof

Source lineage:
- parent distillates:
  - `D3`
  - `D6`
- parent candidate summary `C4`
- parent tension `T2`

## Quarantined Residue Q3) `TINY_BRANCH_DELTAS_AS_NEGATIVITY_SUCCESS`
Status:
- `QUARANTINED`

Preserved residue:
- tiny nonzero branch deltas
- all treated as if they established negativity success

Why it stays quarantined:
- the parent batch explicitly preserves `delta_negfrac_SEQ02_minus_SEQ01 = 0.0`
- tiny branch deltas are weaker than negativity onset

Source lineage:
- parent distillate `D3`
- parent candidate summary `C3`
- parent tension `T3`

## Quarantined Residue Q4) `ZERO_NEGATIVITY_CONVERGENCE_AS_SAME_FAILURE_MODE`
Status:
- `QUARANTINED`

Preserved residue:
- the current Bell-seed family and the prior stress family both store zero negativity
- all retold as if that meant they were the same type of failure

Why it stays quarantined:
- the parent batch explicitly preserves one fixed-contract nonnegative surface and one broader search-failure surface
- shared outcome is weaker than identical failure mode

Source lineage:
- parent distillates:
  - `D5`
  - `D6`
- parent tension `T4`

## Quarantined Residue Q5) `LOCAL_EVIDENCE_AS_REPOTOP_ADMISSION`
Status:
- `QUARANTINED`

Preserved residue:
- catalog presence and local evidence emission
- all treated as if either one promoted the family into repo-top evidence admission

Why it stays quarantined:
- the parent batch explicitly preserves omission of the local `SIM_ID` from the repo-held top-level evidence pack
- local evidence is weaker than repo-top admission

Source lineage:
- parent distillate `D4`
- parent tension `T5`

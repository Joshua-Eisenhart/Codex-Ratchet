# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_stage16_mix_contract_baseline__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Candidate RC1) `STAGE16_MIXED_AXIS6_QUESTION_FAMILY_WITH_CONTRACT_SPLIT`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- `run_stage16_axis6_mix_control.py` and `run_stage16_axis6_mix_sweep.py` should stay compressed as:
  - one Stage16 mixed-axis6 question-family
  - two distinct executable contracts
  - paired same-`rho0` control logic in one branch
  - multi-mode separate-stage sweep logic in the other
- not one numerically interchangeable surface

Why this survives reduction:
- it is the parent batch's clearest structural read
- later Stage16 summaries need the family kinship without losing the contract split that generates the main contradiction

Source lineage:
- parent clusters:
  - `A`
  - `B`
- parent distillates:
  - `D1`
  - `D3`
- parent candidate `C2`
- parent tension `T1`

Preserved limits:
- this batch does not deny that both scripts ask the same theory-facing question
- it preserves only that shared family identity does not erase contract differences

## Candidate RC2) `PAIRED_CONTROL_VERSUS_SWEEP_MODE_NONINTERCHANGEABILITY_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest numerical anti-flattening packet in the parent batch is:
  - control compares one mixed pattern against one reused-state uniform baseline
  - sweep compares `MIX_A`, `MIX_B`, and `MIX_R` against separately sampled uniform and mixed stage runs
  - control values should not be treated as direct stand-ins for sweep-mode cells

Why this survives reduction:
- it is the smallest reusable rule that keeps the executable difference visible in downstream numeric reading
- it is cleaner than carrying forward the full result tables

Source lineage:
- parent clusters:
  - `A`
  - `B`
- parent distillate `D3`
- parent candidate `C5`
- parent tension `T1`

Preserved limits:
- this batch does not claim one contract is better or more canonical than the other
- it preserves only that they are not numerically interchangeable

## Candidate RC3) `SUB4_AXIS6U_EXACT_UNIFORM_BASELINE_ANCHOR_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- `run_stage16_sub4_axis6u.py` is best kept here as:
  - the exact uniform baseline anchor for the mixed-axis6 family
  - comparison-only for this batch
  - not a merged family member despite exact `U_*` baseline identity

Why this survives reduction:
- it is the parent batch's cleanest bridge between the mixed family and the standalone absolute baseline surface
- later Stage16 baseline work needs this exact-anchor rule before opening the separate absolute batch

Source lineage:
- parent cluster `C`
- parent distillate `D2`
- parent candidate `C3`
- parent tension `T2`

Preserved limits:
- this batch does not collapse the baseline anchor into the mixed family
- it also does not replace the need for the separate `sub4_axis6u` absolute-surface batch

## Candidate RC4) `CATALOG_STAGE16_TRIO_WITH_TOPLEVEL_EVIDENCE_ABSENCE_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest provenance and admission packet in the parent batch is:
  - the catalog groups `mix_control`, `mix_sweep`, and `sub4_axis6u`
  - the repo-held top-level evidence pack admits none of the three
- naming coverage and evidence admission must stay separate

Why this survives reduction:
- it is the clearest reusable admission boundary in the parent batch
- later Stage16 lineage work needs a compact rule for not reading catalog presence as evidence admission

Source lineage:
- parent cross-cluster read
- parent distillate `D4`
- parent candidate `C4`
- parent tension `T3`
- comparison anchor:
  - `BATCH_A2MID_sims_evidence_boundary__v1:RC2`

Preserved limits:
- this batch does not deny local result richness or catalog usefulness
- it preserves only that catalog grouping is weaker than top-level evidence admission

## Candidate RC5) `CONTROL_LOCALITY_VERSUS_SWEEP_SCALE_ASYMMETRY_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the family should preserve two different response scales at once:
  - control shifts are small and localized
  - sweep shifts are larger and mode-sensitive
  - sweep mode choice can dominate family effect size

Why this survives reduction:
- it is the parent batch's clearest compact signal from the numeric highlights
- later interpretation should not average the family into one uniform perturbation scale

Source lineage:
- parent clusters:
  - `A`
  - `B`
- parent distillate `D5`
- parent tensions:
  - `T4`
  - `T5`

Preserved limits:
- this batch does not reduce the family to one global average
- it preserves only the control-versus-sweep scale split

## Candidate RC6) `CONTROL_SE_REGION_VERSUS_SWEEP_SI_REGION_DOMINANCE_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the dominant Stage16 cell should stay split by contract:
  - control is Se-focused around `1_Se_*`
  - sweep peaks at `type2.inner.4_Si_DOWN`, especially under `MIX_B`
- control intuition should not be projected onto sweep dominance

Why this survives reduction:
- it is the parent batch's cleanest stage-specific anti-flattening packet
- later mixed-axis6 summaries need a compact rule for preserving where the signal actually concentrates

Source lineage:
- parent distillate `D5`
- parent tensions:
  - `T5`
  - `T6`

Preserved limits:
- this batch does not settle any theory-facing explanation for the dominant cells
- it preserves only the shift in where the strongest signal appears

## Quarantined Residue Q1) `SAME_COMPUTATION_JUST_MORE_MODES_STORY`
Status:
- `QUARANTINED`

Preserved residue:
- one Stage16 mixed-axis6 family
- both executable surfaces
- all treated as if `mix_sweep` were only a larger copy of `mix_control`

Why it stays quarantined:
- the parent batch explicitly preserves a paired-control contract in one branch and a separate-stage sweep contract in the other
- flattening them this way erases the main executable contradiction

Source lineage:
- parent distillate `D3`
- parent candidate `C5`
- parent tension `T1`

## Quarantined Residue Q2) `EXACT_BASELINE_EQUALITY_AS_FAMILY_MEMBERSHIP`
Status:
- `QUARANTINED`

Preserved residue:
- exact `U_*` baseline identity between control and `sub4_axis6u`
- all treated as if that numeric identity alone merged the baseline anchor into the mixed family

Why it stays quarantined:
- the parent batch explicitly preserves `sub4_axis6u` as comparison-only and absolute rather than mixed
- equality of baseline numbers is weaker than bounded-family identity

Source lineage:
- parent distillate `D2`
- parent candidate `C3`
- parent tension `T2`

## Quarantined Residue Q3) `CATALOG_MEMBERSHIP_AS_TOPLEVEL_EVIDENCE_ADMISSION`
Status:
- `QUARANTINED`

Preserved residue:
- catalog grouping of the Stage16 trio
- all treated as if that grouping already admitted the family into the repo-held top-level evidence pack

Why it stays quarantined:
- the parent batch explicitly preserves a zero-block top-level evidence outcome for all three surfaces
- catalog coverage is structural and weaker than evidence admission

Source lineage:
- parent distillate `D4`
- parent candidate `C4`
- parent tension `T3`

## Quarantined Residue Q4) `ONE_UNIFORM_PERTURBATION_SCALE_ACROSS_CONTROL_AND_SWEEP`
Status:
- `QUARANTINED`

Preserved residue:
- control and sweep both treated as if they lived on one shared magnitude scale

Why it stays quarantined:
- the parent batch explicitly preserves small localized control shifts and larger mode-sensitive sweep excursions
- flattening the family into one scale erases the usable numeric asymmetry

Source lineage:
- parent distillate `D5`
- parent tensions:
  - `T4`
  - `T5`

## Quarantined Residue Q5) `CONTROL_SE_DOMINANCE_AS_FULL_SWEEP_MAP`
Status:
- `QUARANTINED`

Preserved residue:
- control's Se-focused strongest cell
- all treated as if it predicted the dominant region of the sweep surface too

Why it stays quarantined:
- the parent batch explicitly preserves sweep dominance at `type2.inner.4_Si_DOWN`
- control intuition is too weak to settle the broader sweep map

Source lineage:
- parent distillate `D5`
- parent tension `T6`

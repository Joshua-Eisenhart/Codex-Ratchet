# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_sims_axis0_traj_corr_suite_v2_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Candidate RC1) `TRAJ_CORR_V2_REMAINS_RESULT_ONLY_AND_RUNNERLESS`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the current axis0 trajectory-correlation `v2` orphan should be read as:
  - one bounded result-only orphan surface
  - clearly related to the trajectory-correlation family
  - but still lacking a direct recoverable runner-name anchor in current `simpy/`

Why this survives reduction:
- it is the parent batch's strongest provenance rule
- it keeps family relation explicit without inventing a runner anchor

Source lineage:
- parent cluster `A`
- parent distillates:
  - `D1`
  - `D5`
- parent candidates:
  - `C1`
  - `C4`
- parent tension `T1`

Preserved limits:
- this batch does not deny family resemblance
- it preserves only that resemblance is weaker than a present runner anchor

## Candidate RC2) `SEQ01_BASELINES_AND_SEQ02_04_DELTAS_ARE_THE_STORAGE_CONTRACT`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the current orphan is not a flat all-absolute suite because it stores:
  - `32` absolute `SEQ01` baselines
  - `96` delta entries for `SEQ02` through `SEQ04`

Why this survives reduction:
- it is the parent batch's clearest storage-contract rule
- it prevents missing absolute `SEQ02-04` values from being retold as absent runs

Source lineage:
- parent clusters:
  - `B`
  - `C`
- parent distillate `D2`
- parent candidate `C3`
- parent tension `T2`

Preserved limits:
- this batch does not reconstruct missing absolutes
- it preserves only that the deltas are the intended storage contract

## Candidate RC3) `HIDDEN_T_AXIS_AND_STRONGEST_DELTA_CASE_MUST_STAY_ATTACHED`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- controller reads should keep two facts attached together:
  - the real lattice includes hidden `T1` / `T2` prefixes beyond the explicit metadata
  - the strongest stored delta response concentrates on `T1_REV_BELL_CNOT_R1_SEQ04`

Why this survives reduction:
- it is the parent batch's sharpest anti-flattening result packet
- it keeps the strongest perturbation tied to the actual hidden-axis lattice that carries it

Source lineage:
- parent clusters:
  - `C`
  - `D`
- parent distillates:
  - `D2`
  - `D3`
- parent candidate `C3`
- parent tension `T5`

Preserved limits:
- this batch does not infer a full theory from one strongest case
- it preserves only that the case and the hidden axis must stay explicit

## Candidate RC4) `CURRENT_ORPHAN_IS_NOT_THE_LOCAL_SUITE_OR_V4_V5`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the current orphan must stay distinct from:
  - the earlier local full-absolute trajectory-correlation suite
  - repo-top descendant `V4`
  - repo-top descendant `V5`
  - because all three use materially different storage and lattice contracts

Why this survives reduction:
- it is the parent batch's strongest anti-collapse family-boundary rule
- it prevents false continuity lines across clearly different contracts

Source lineage:
- parent cluster `E`
- parent distillate `D4`
- parent candidates:
  - `C2`
  - `C5`
- parent tensions:
  - `T3`
  - `T4`

Preserved limits:
- this batch does not deny family resemblance
- it preserves only that resemblance is weaker than contract equivalence

## Candidate RC5) `CATALOG_VISIBILITY_IS_WEAKER_THAN_EVIDENCE_ADMISSION`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the controller should keep one visibility rule here:
  - the orphan is catalog-visible by filename alias
  - but remains absent from the evidence-pack layer

Why this survives reduction:
- it is the parent batch's cleanest evidence-boundary packet
- it prevents catalog visibility from being retold as maintained evidence admission

Source lineage:
- parent cluster `E`
- parent distillate `D5`
- parent tension `T6`

Preserved limits:
- this batch does not deny that catalog listing is useful
- it preserves only that catalog visibility and evidence admission are not interchangeable

## Quarantined Residue Q1) `FAMILY_RESEMBLANCE_AS_INVENTED_RUNNER_ANCHOR`
Status:
- `QUARANTINED`

Preserved residue:
- the current orphan resembles the trajectory-correlation family
- all retold as if a present runner anchor therefore exists

Why it stays quarantined:
- the parent batch explicitly preserves zero direct runner-name hits in current `simpy/`
- resemblance is weaker than runner provenance

Source lineage:
- parent distillate `D5`
- parent candidate `C4`
- parent tension `T1`

## Quarantined Residue Q2) `MISSING_SEQ02_04_ABSOLUTES_AS_ABSENT_RUNS`
Status:
- `QUARANTINED`

Preserved residue:
- the file lacks absolute `SEQ02-04` entries
- all retold as if those runs are absent rather than delta-encoded

Why it stays quarantined:
- the parent batch explicitly preserves seq01 baselines plus seq02-04 deltas as the storage contract
- missing absolutes are weaker than absent execution

Source lineage:
- parent distillate `D2`
- parent tension `T2`

## Quarantined Residue Q3) `CONTRACT_SHIFT_AS_SIMPLE_VERSION_BUMP`
Status:
- `QUARANTINED`

Preserved residue:
- the current orphan, the earlier local suite, and `V4` / `V5` all share a trajectory-correlation family resemblance
- all retold as if they therefore form one simple version line

Why it stays quarantined:
- the parent batch explicitly preserves material contract changes across all three surfaces
- resemblance is weaker than contract continuity

Source lineage:
- parent distillate `D4`
- parent candidate `C5`
- parent tensions:
  - `T3`
  - `T4`

## Quarantined Residue Q4) `HIDDEN_T_AXIS_ERASURE_AND_GENERIC_DELTA_RETELLING`
Status:
- `QUARANTINED`

Preserved residue:
- delta behavior is discussed
- while the hidden `T1` / `T2` lattice and strongest-case attachment are erased

Why it stays quarantined:
- the parent batch explicitly preserves the hidden-axis structure and its strongest delta carrier
- generic delta talk is weaker than the actual lattice read

Source lineage:
- parent distillates:
  - `D2`
  - `D3`
- parent tension `T5`

## Quarantined Residue Q5) `CATALOG_PRESENCE_AS_EVIDENCE_ADMISSION`
Status:
- `QUARANTINED`

Preserved residue:
- the current orphan is catalog-listed
- all retold as if the evidence pack therefore admits the same family

Why it stays quarantined:
- the parent batch explicitly preserves evidence-pack omission
- catalog listing is weaker than evidence admission

Source lineage:
- parent distillate `D5`
- parent tension `T6`

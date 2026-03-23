# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_axis0_traj_suite_descendant_seams__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Candidate RC1) `AXIS0_TRAJ_SUITE_PAIR_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- `run_axis0_traj_corr_suite.py` and `results_axis0_traj_corr_suite.json` should stay compressed as:
  - one standalone signed directional trajectory-suite residual pair
  - one runner plus one paired result
  - one bounded family rather than one merged axis0 trajectory omnibus block

Why this survives reduction:
- it is the parent batch's cleanest family-shell claim
- it preserves the suite pair as its own reusable unit inside the residual lane

Source lineage:
- parent cluster `A`
- parent distillate `D1`
- parent candidate summaries:
  - `C1`
  - `C2`

Preserved limits:
- this batch does not absorb the next residual pair
- it preserves only the current suite pair as one bounded family

## Candidate RC2) `LOCAL_SUITE_VS_V4V5_DESCENDANT_ADMISSION_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest admission seam in the parent batch is:
  - the local suite emits evidence for `S_SIM_AXIS0_TRAJ_CORR_SUITE`
  - the repo-held evidence pack omits that local `SIM_ID`
  - the same pack admits:
    - `S_SIM_AXIS0_TRAJ_CORR_SUITE_V4`
    - `S_SIM_AXIS0_TRAJ_CORR_SUITE_V5`
  - both descendants share the current runner hash
- code-hash continuity is not the same as local-suite SIM_ID admission

Why this survives reduction:
- it is the parent batch's clearest descendant seam
- later summaries need a compact rule for not collapsing the local suite into admitted descendants

Source lineage:
- parent cluster `D`
- parent distillates:
  - `D4`
  - `D6`
- parent candidate summary `C4`
- parent tension `T1`
- comparison anchor:
  - `BATCH_A2MID_sims_evidence_boundary__v1:RC3`

Preserved limits:
- this batch does not deny runner-hash continuity
- it preserves only that hash continuity is weaker than SIM_ID continuity

## Candidate RC3) `DELTA_EVIDENCE_VS_FULL_LATTICE_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest storage-versus-evidence seam in the parent batch is:
  - the result surface stores a full `32`-case lattice
  - the emitted evidence block compresses each sign/init/direction slice to `SEQ01`-relative deltas
- the local evidence block is not the same as the full stored lattice

Why this survives reduction:
- it is the parent batch's clearest compression packet
- later summaries need a compact rule for not reconstructing the whole suite from delta-only evidence emission

Source lineage:
- parent clusters:
  - `A`
  - `D`
- parent distillates:
  - `D2`
  - `D4`
  - `D6`
- parent candidate summary `C5`
- parent tension `T2`

Preserved limits:
- this batch does not deny that the emitted deltas are useful
- it preserves only that they are weaker than the full 32-case surface

## Candidate RC4) `SEQ04_DIRECTION_FLIP_ANOMALY_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest local-case anomaly in the parent batch is:
  - `sign1_BELL_FWD_SEQ04` stores:
    - `MI_traj_mean = 0.1470168871279225`
    - `SAgB_neg_frac_traj = 0.06995192307692308`
    - `SAgB_traj_mean = 0.5110568647917657`
  - `sign1_BELL_REV_SEQ04` stores:
    - `MI_traj_mean = 0.29728021483432243`
    - `SAgB_neg_frac_traj = 0.1373798076923077`
    - `SAgB_traj_mean = 0.358440136696848`
- `SEQ04` is direction-sensitive rather than uniformly weak or uniformly strong

Why this survives reduction:
- it is the parent batch's clearest case-level anomaly packet
- later summaries need a compact rule for keeping direction attached to any `SEQ04` claim

Source lineage:
- parent clusters:
  - `B`
  - `C`
- parent distillates:
  - `D2`
  - `D3`
  - `D6`
- parent candidate summary `C3`
- parent tension `T3`
- comparison anchor:
  - `BATCH_A2MID_axis0_bellseed_nonnegativity__v1:RC4`

Preserved limits:
- this batch does not deny that `SEQ04` belongs to the same suite lattice
- it preserves only that its behavior flips with direction inside the Bell regime

## Candidate RC5) `BELL_GINIBRE_SUITE_NEGATIVITY_FIELD_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest regime packet in the parent batch is:
  - Bell cases keep nonzero `SAgB_neg_frac_traj` across the suite
  - Ginibre cases keep `SAgB_neg_frac_traj = 0.0` across the suite
- the Bell/Ginibre split remains absolute at the stored trajectory-negativity level

Why this survives reduction:
- it is the parent batch's clearest regime-level packet
- later summaries need a compact rule for not averaging Bell and Ginibre into one negativity field

Source lineage:
- parent clusters:
  - `B`
  - `C`
- parent distillates:
  - `D2`
  - `D3`
- parent candidate summary `C3`
- parent tension `T4`
- comparison anchor:
  - `BATCH_A2MID_axis0_traj_bell_ginibre_asymmetry__v1:RC2`

Preserved limits:
- this batch does not deny that Bell and Ginibre live in one runner surface
- it preserves only that their stored negativity behavior remains separated

## Candidate RC6) `NEAR_SIGN_SYMMETRY_WITH_NONZERO_RESIDUAL_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest sign-symmetry caution in the parent batch is:
  - sign reversal often looks nearly symmetric
  - stored residuals remain nonzero, for example:
    - `sign1_BELL_FWD_SEQ01` vs `sign-1_BELL_FWD_SEQ01` keeps nonzero deltas in `MI`, `SAgB`, and `SAgB_neg_frac_traj`
    - `sign1_BELL_REV_SEQ04` vs `sign-1_BELL_REV_SEQ04` does the same
- sign symmetry is close but not exact

Why this survives reduction:
- it is the parent batch's clearest anti-overstatement packet
- later summaries need a compact rule for keeping near-symmetry distinct from exact symmetry

Source lineage:
- parent clusters:
  - `B`
  - `C`
- parent distillates:
  - `D2`
  - `D6`
- parent tension `T5`

Preserved limits:
- this batch does not deny the broad symmetry pattern
- it preserves only that exact symmetry is stronger than the stored result warrants

## Quarantined Residue Q1) `LOCAL_SUITE_AS_REPOTOP_ADMITTED_VIA_CODE_HASH`
Status:
- `QUARANTINED`

Preserved residue:
- descendant evidence blocks share the current runner hash
- all retold as if the local suite SIM_ID were therefore repo-top admitted

Why it stays quarantined:
- the parent batch explicitly preserves omission of the local suite SIM_ID from the repo-held evidence pack
- code-hash continuity is weaker than local-suite admission

Source lineage:
- parent distillates:
  - `D4`
  - `D6`
- parent candidate summary `C4`
- parent tension `T1`

## Quarantined Residue Q2) `DELTA_EVIDENCE_BLOCK_AS_FULL_32CASE_SURFACE`
Status:
- `QUARANTINED`

Preserved residue:
- emitted `SEQ01`-relative delta evidence
- all treated as if it fully represented the 32 stored cases

Why it stays quarantined:
- the parent batch explicitly preserves a larger stored lattice than the emitted evidence summary
- delta-only evidence is weaker than full lattice coverage

Source lineage:
- parent distillates:
  - `D4`
  - `D6`
- parent candidate summary `C5`
- parent tension `T2`

## Quarantined Residue Q3) `SEQ04_AS_DIRECTION_INVARIANT`
Status:
- `QUARANTINED`

Preserved residue:
- `SEQ04` anomaly behavior
- all treated as if its Bell effect were direction-invariant

Why it stays quarantined:
- the parent batch explicitly preserves stronger Bell anomaly behavior in `REV` than in `FWD`
- case identity is weaker than direction-qualified case identity

Source lineage:
- parent distillates:
  - `D3`
  - `D6`
- parent candidate summary `C3`
- parent tension `T3`

## Quarantined Residue Q4) `BELL_AND_GINIBRE_AS_ONE_AVERAGED_NEGATIVITY_FIELD`
Status:
- `QUARANTINED`

Preserved residue:
- one suite contains Bell and Ginibre cases
- all retold as if the suite therefore supported one averaged negativity field

Why it stays quarantined:
- the parent batch explicitly preserves nonzero Bell negativity and zero Ginibre negativity across the suite
- one lattice is weaker than one unified regime story

Source lineage:
- parent distillates:
  - `D2`
  - `D3`
- parent tension `T4`

## Quarantined Residue Q5) `EXACT_SIGN_SYMMETRY`
Status:
- `QUARANTINED`

Preserved residue:
- broad sign-reversal similarity
- all treated as if the suite were exactly sign-symmetric

Why it stays quarantined:
- the parent batch explicitly preserves nonzero residuals under sign reversal
- near symmetry is weaker than exact symmetry

Source lineage:
- parent distillates:
  - `D2`
  - `D6`
- parent tension `T5`

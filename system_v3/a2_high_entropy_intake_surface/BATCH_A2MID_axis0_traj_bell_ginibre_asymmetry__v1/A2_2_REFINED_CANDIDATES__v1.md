# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_axis0_traj_bell_ginibre_asymmetry__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Candidate RC1) `AXIS0_TRAJ_CORR_PAIR_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- `run_axis0_traj_corr_metrics.py` and `results_axis0_traj_corr_metrics.json` should stay compressed as:
  - one standalone dual-init trajectory-correlation residual pair
  - one runner plus one paired result
  - one bounded family rather than one merged trajectory omnibus block

Why this survives reduction:
- it is the parent batch's cleanest family-shell claim
- it preserves the trajectory-metrics pair as its own reusable unit inside the residual lane

Source lineage:
- parent cluster `A`
- parent distillate `D1`
- parent candidate summaries:
  - `C1`
  - `C2`

Preserved limits:
- this batch does not absorb the next residual pair
- it preserves only the current trajectory-metrics pair as one bounded family

## Candidate RC2) `BELL_VS_GINIBRE_TRAJECTORY_NEGATIVITY_SPLIT_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest init-regime split in the parent batch is:
  - Bell stores nonzero trajectory negativity:
    - `SEQ01.SAgB_neg_frac_traj = 0.09753605769230769`
    - `SEQ02.SAgB_neg_frac_traj = 0.09723557692307692`
  - Ginibre stores zero trajectory negativity in both branches
- initialization regime changes whether the stored trajectory ever enters negative-conditional-entropy territory

Why this survives reduction:
- it is the parent batch's clearest dual-init packet
- later summaries need a compact rule for keeping Bell and Ginibre trajectory-negativity claims separate

Source lineage:
- parent clusters:
  - `B`
  - `C`
- parent distillates:
  - `D2`
  - `D3`
- parent candidate summary `C3`
- parent tension `T1`
- comparison anchor:
  - `BATCH_A2MID_axis0_bellseed_nonnegativity__v1:RC3`

Preserved limits:
- this batch does not claim Bell preserves final-state negativity
- it preserves only the stored trajectory split between the two init regimes

## Candidate RC3) `TRAJECTORY_NEGATIVITY_WITH_POSITIVE_FINAL_STATE_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest trajectory-versus-final-state seam in the parent batch is:
  - Bell begins at negative conditional entropy:
    - `SAgB_init_mean = -0.6931471805599333`
  - Bell still ends with positive final `S(A|B)` in both branches:
    - `SEQ01.SAgB_final_mean = 0.6460960417722438`
    - `SEQ02.SAgB_final_mean = 0.6460646351342514`
- trajectory negativity is not the same as negative final-state conditional entropy

Why this survives reduction:
- it is the parent batch's clearest anti-collapse packet
- later summaries need a compact rule for not translating trajectory negativity into final-state negativity

Source lineage:
- parent cluster `C`
- parent distillates:
  - `D3`
  - `D6`
- parent candidate summary `C4`
- parent tension `T2`

Preserved limits:
- this batch does not deny that Bell carries real trajectory negativity
- it preserves only that the final stored state remains positive in both branches

## Candidate RC4) `INIT_QUALIFIED_SEQUENCE_DIRECTION_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the family should preserve one init-qualified sequence packet:
  - Bell:
    - `delta_MI_traj_mean_SEQ02_minus_SEQ01 = -0.0004972841850615362`
    - `delta_SAgB_traj_mean_SEQ02_minus_SEQ01 = 0.00047040060007191853`
  - Ginibre:
    - `delta_MI_traj_mean_SEQ02_minus_SEQ01 = 0.00017745381487310752`
    - `delta_SAgB_traj_mean_SEQ02_minus_SEQ01 = -0.00020947935777215765`
- sequence-order direction is not globally signed across init regimes

Why this survives reduction:
- it is the parent batch's clearest directionality packet
- later summaries need a compact rule for keeping sequence conclusions init-qualified

Source lineage:
- parent clusters:
  - `B`
  - `C`
- parent distillates:
  - `D2`
  - `D6`
- parent candidate summary `C5`
- parent tension `T3`

Preserved limits:
- this batch does not deny that the deltas are small
- it preserves only that their sign flip blocks one init-independent direction story

## Candidate RC5) `MI_VS_SAGB_TRAJECTORY_DECOUPLING_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest metric anti-collapse packet in the parent batch is:
  - Bell carries larger trajectory `MI`:
    - `MI_traj_mean` near `0.199`
  - Ginibre carries larger positive trajectory `SAgB`:
    - `SAgB_traj_mean` near `0.613`
- higher stored mutual information does not track with higher positive `S(A|B)` trajectory mean in this family

Why this survives reduction:
- it is the parent batch's clearest metric-decoupling packet
- later summaries need a compact rule for not forcing `MI` and `SAgB` trajectory means into one co-moving story

Source lineage:
- parent cluster `C`
- parent distillates:
  - `D3`
  - `D6`
- parent candidate summary `C3`
- parent tension `T4`
- comparison anchor:
  - `BATCH_A2MID_axis0_ab_mi_revival__v1:RC5`

Preserved limits:
- this batch does not deny that both metrics remain useful
- it preserves only that they move differently across the two init regimes

## Candidate RC6) `LOCAL_TRAJ_EVIDENCE_WITHOUT_REPOTOP_ADMISSION_RULE`
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
- parent cluster `D`
- parent distillate `D4`
- parent tension `T5`
- comparison anchor:
  - `BATCH_A2MID_sims_evidence_boundary__v1:RC3`

Preserved limits:
- this batch does not deny the local evidence contract
- it preserves only that local evidence, catalog presence, and repo-top admission are not the same layer

## Quarantined Residue Q1) `BELL_TRAJECTORY_NEGATIVITY_AS_NEGATIVE_FINAL_STATE`
Status:
- `QUARANTINED`

Preserved residue:
- Bell stores nonzero trajectory negativity
- all retold as if Bell therefore ended in negative final-state conditional entropy

Why it stays quarantined:
- the parent batch explicitly preserves positive Bell final `S(A|B)` means in both branches
- trajectory negativity is weaker than negative final-state proof

Source lineage:
- parent distillates:
  - `D3`
  - `D6`
- parent candidate summary `C4`
- parent tension `T2`

## Quarantined Residue Q2) `SMALL_SEQUENCE_DELTAS_AS_INIT_INDEPENDENT_DIRECTION`
Status:
- `QUARANTINED`

Preserved residue:
- small sequence-order deltas
- all treated as if they established one global direction across init modes

Why it stays quarantined:
- the parent batch explicitly preserves sign flips between Bell and Ginibre
- small deltas are weaker than init-independent directionality

Source lineage:
- parent distillates:
  - `D2`
  - `D6`
- parent candidate summary `C5`
- parent tension `T3`

## Quarantined Residue Q3) `MI_AND_POSITIVE_SAGB_TRAJECTORY_MEANS_AS_CO_MOVING`
Status:
- `QUARANTINED`

Preserved residue:
- Bell has larger trajectory `MI`
- all retold as if Bell therefore also had larger positive trajectory `S(A|B)` mean

Why it stays quarantined:
- the parent batch explicitly preserves larger positive trajectory `S(A|B)` means for Ginibre instead
- higher `MI` is weaker than a one-direction metric bundle story

Source lineage:
- parent distillates:
  - `D3`
  - `D6`
- parent tension `T4`

## Quarantined Residue Q4) `BELL_AND_GINIBRE_AS_ONE_REGIME_STORY`
Status:
- `QUARANTINED`

Preserved residue:
- one runner covers both init modes
- all retold as if Bell and Ginibre therefore supported one undifferentiated regime story

Why it stays quarantined:
- the parent batch explicitly preserves materially different trajectory-negativity behavior across the two init modes
- one runner is weaker than one unified regime interpretation

Source lineage:
- parent distillates:
  - `D2`
  - `D3`
- parent candidate summary `C3`
- parent tension `T1`

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

# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_sims_runner_pairing_hygiene__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-08

## Candidate RC1) `RUNNER_RESULT_PAIRING_AND_SCOPE_PATTERN`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- one reusable sims executable pattern here is:
  - runner advertises an output contract
  - paired JSON result exposes the real stored shape
  - sidecar evidence exists but stays outside this bounded read

Why this survives reduction:
- it is the clearest pair-level outer interface in the parent batch
- it keeps runner, JSON result, and sidecar roles separate instead of flattening them

Source lineage:
- parent source map selection and structural map
- parent distillate `D1`
- parent candidate:
  - `C1`
  - `C2`
- parent tension `T6`

Preserved limits:
- this batch does not reconcile the sidecar packs
- pairing alone does not upgrade the results into earned lower-lane evidence

## Candidate RC2) `DETERMINISTIC_KNOB_AND_HASHED_OUTPUT_PATTERN`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- all three runners share one strong engineering pattern:
  - explicit seeds, trials, cycles, or seed lists
  - JSON serialization first
  - code hash and output hash
  - compact `SIM_EVIDENCE` emission after the JSON write

Why this survives reduction:
- it is the cleanest executable-facing common structure across the family
- it remains reusable even though the underlying experiments differ

Source lineage:
- parent cluster `S5`
- parent distillate `D6`
- parent candidate `C4`
- parent tension `T6`

Preserved limits:
- this batch does not claim the sidecar contents were checked against the JSON payloads
- deterministic knob blocks remain source-local until later runtime or sidecar audit

## Candidate RC3) `BOUNDARY_RECORD_COMPRESSION_STRESS_SPLIT`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the boundary bookkeeping pair should be read as a split family:
  - `REC1` and `REC3` as visibly lossy compression stress cases
  - `REC9` as a near-lossless or full-record sanity case

Why this survives reduction:
- it is the smallest clean reduction from the boundary sweep pair
- it preserves the difference between compression pressure and sanity-baseline behavior

Source lineage:
- parent cluster `S1`
- parent distillate `D2`
- parent candidate `C5`
- parent tension `T2`

Preserved limits:
- this batch does not collapse the three record classes into one generic evidence family
- near-lossless behavior is preserved as source-local observation, not global law

## Candidate RC4) `AXIS12_BOOKKEEPING_VS_AXIS0_INVARIANCE_SPLIT`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest reusable read of the linkage pair is:
  - Axis12 variant sets drive combinatorial bookkeeping changes
  - the stored Axis0 metric blocks remain invariant across `canon`, `swap`, and `rand`

Why this survives reduction:
- it preserves the parent batch's clearest label-vs-payload split
- it is more reusable than the broader raw linkage rhetoric

Source lineage:
- parent cluster:
  - `S2`
  - `S3`
- parent distillate `D3`
- parent candidate `C3`
- parent tension `T3`

Preserved limits:
- this batch does not deny that later evidence could show a narrower linkage effect elsewhere
- it only states what this runner/result pair currently exposes

## Candidate RC5) `MEGA_STAGE16_VS_AXIS0_AB_SUBFAMILY_SPLIT`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the mega artifact is best kept as a two-part aggregate:
  - Stage16 one-qubit delta family
  - Axis0 AB trajectory family

Why this survives reduction:
- it keeps the convenience package usable without pretending it is one homogeneous evidence family
- it is the parent batch's clearest aggregate-interpretability boundary

Source lineage:
- parent cluster `S4`
- parent distillate `D4`
- parent candidate `C5`
- parent tension `T4`

Preserved limits:
- this batch does not split the raw source into separate intake families
- it only preserves the subfamily boundary for downstream use

## Candidate RC6) `DIRECTIONAL_SEQUENCE_EFFECT_PRESERVATION`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- sequence-order effects in the mega family should stay direction-specific:
  - one direction can show depressed MI for `SEQ04` versus `SEQ01`
  - another direction can show elevated MI for the same comparison

Why this survives reduction:
- it is the parent batch's clearest anti-flattening result for sequence effects
- it protects the family from simplistic better/worse ordering claims

Source lineage:
- parent cluster `S4`
- parent distillate `D5`
- parent tension `T5`

Preserved limits:
- this batch does not infer a universal ordering claim across families
- it keeps the statement at the specific direction-sensitive level visible in the parent batch

## Quarantined Residue Q1) `LEADING_SPACE_RUNNER_PATH_HAZARD`
Status:
- `QUARANTINED`

Preserved residue:
- leading-space runner basenames
- clean result filenames on the paired JSON side
- matching leading-space cache artifacts outside source membership

Why it stays quarantined:
- this is real executable-facing hygiene pressure
- it is not itself a clean reusable evidence or family-pattern surface

Source lineage:
- parent cluster `S6`
- parent candidate `C5`
- parent tension `T1`
- parent manifest failure modes

## Quarantined Residue Q2) `SIDECAR_EVIDENCE_RECONCILIATION_DEFERRED`
Status:
- `QUARANTINED`

Preserved residue:
- each runner claims sidecar evidence emission
- this bounded batch reads only runners and paired JSON results

Why it stays quarantined:
- sidecar comparison remains outside the parent batch boundary
- stronger transport claims would overstate what was actually read

Source lineage:
- parent cluster `S5`
- parent candidate `C2`
- parent tension `T6`
- parent manifest failure modes

## Quarantined Residue Q3) `CROSS_AXIS_CAUSATION_OVERREAD`
Status:
- `QUARANTINED`

Preserved residue:
- linkage naming suggests stronger cross-axis coupling than the current Axis0 payload shows

Why it stays quarantined:
- a broader causal claim would go beyond the actual runner/result evidence preserved in this batch
- the safe reduction is the bookkeeping-vs-invariance split, not a positive causal story

Source lineage:
- parent cluster:
  - `S2`
  - `S3`
- parent candidate `C3`
- parent tension `T3`

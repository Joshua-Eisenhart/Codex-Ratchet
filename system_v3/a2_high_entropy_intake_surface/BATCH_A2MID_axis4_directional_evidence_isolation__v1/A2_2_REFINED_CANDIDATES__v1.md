# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_axis4_directional_evidence_isolation__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Candidate RC1) `AXIS4_DIRECTIONAL_SUITE_EXECUTABLE_THEORY_AND_EVIDENCE_SPLIT`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- this family is safest when split into:
  - executable runners and paired JSON results
  - one theory-facing aggregate sibling
  - one separate top-level evidence-pack lineage

Why this survives reduction:
- the parent batch's strongest structural signal is that these three layers coexist but should not be flattened together
- this gives later Axis4 summaries a compact family map without collapsing producer path, result storage, and theory compression

Source lineage:
- parent clusters:
  - `S1`
  - `S2`
  - `S5`
  - `S6`
- parent distillate `D1`
- parent candidate `C1`

Preserved limits:
- this batch does not promote the aggregate sibling into ordinary executable evidence
- it preserves the three-layer split explicitly

## Candidate RC2) `RUNNER_RESULT_PAIRING_WITH_PRODUCER_HASH_SUSPENSION_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the directional suite should be read as:
  - runner advertises an output contract
  - paired JSON exposes the stored shape
  - producer authorship remains suspended where the top-level evidence pack points to a different code hash

Why this survives reduction:
- it is the cleanest producer-path rule that survives the parent batch
- it keeps filename/result pairing usable without overstating evidentiary provenance

Source lineage:
- parent cluster `S6`
- parent distillate `D5`
- parent candidate `C4`
- parent tension `T1`
- comparison anchors:
  - `BATCH_A2MID_sims_evidence_boundary__v1:RC3`
  - `BATCH_A2MID_sims_runner_pairing_hygiene__v1:RC1`

Preserved limits:
- this batch does not claim the current directional runners are the evidenced producers
- it preserves producer-path uncertainty explicitly

## Candidate RC3) `DIRECTION_LABEL_NOT_DIRECTION_ISOLATION_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- for this family, a direction-labeled evidence block should not be assumed to isolate one direction, because the stored top-level blocks carry both `fwd_*` and `rev_*` metrics

Why this survives reduction:
- it is the parent batch's clearest evidence-contract ambiguity
- it protects later readers from a simple but wrong one-block-per-direction inference

Source lineage:
- parent cluster `S6`
- parent tension `T2`
- parent candidate `C4`
- comparison anchor:
  - `BATCH_A2MID_sims_evidence_boundary__v1:RC3`

Preserved limits:
- this batch does not deny the direction labels exist
- it preserves only that the stored evidence packets are not direction-isolated

## Candidate RC4) `AGGREGATE_BIDIR_MINUS_ONLY_COMPRESSION_LAYER_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- `S_SIM_AXIS4_SEQ_ALL_BIDIR_V1` should be kept as:
  - a theory-facing compression layer
  - spanning Type-1 and Type-2
  - reproducing the minus branch only
  - not replacing the executable family surfaces that also carry the plus branch

Why this survives reduction:
- it is the cleanest compact read of the aggregate sibling
- it preserves the convenience of the aggregate while keeping its lossiness explicit

Source lineage:
- parent cluster `S5`
- parent distillate `D4`
- parent candidates:
  - `C3`
  - `C5`
- parent tension `T3`

Preserved limits:
- this batch does not treat the aggregate sibling as a full family summary
- it preserves the plus-branch omission explicitly

## Candidate RC5) `TYPE2_RESULT_AND_AGGREGATE_PRESENCE_WITH_TOPLEVEL_EVIDENCE_GAP`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the safest Type-2 read in this family is:
  - Type-2 is executable-present
  - Type-2 is stored in paired results
  - Type-2 is represented in the aggregate sibling
  - Type-2 lacks per-direction top-level evidence-pack blocks in the current repo-held record

Why this survives reduction:
- it is the parent batch's clearest anti-flattening coverage rule
- it avoids the two overreads the parent explicitly warns against: `fully evidenced` and `absent`

Source lineage:
- parent cluster `S2`
- parent distillate `D6`
- parent tension `T4`
- comparison anchor:
  - `BATCH_A2MID_sims_axis4_p03_evidence_path__v1:RC4`

Preserved limits:
- this batch does not upgrade aggregate presence into per-direction evidence
- it preserves the coverage gap explicitly

## Candidate RC6) `PLUS_BRANCH_TYPE_INERTIA_AND_MINUS_BRANCH_SIGNAL_SPLIT`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest branch-specific summary here is:
  - the plus branch is direction-specific but sequence-invariant
  - the plus branch is numerically identical across Type-1 and Type-2
  - the minus branch carries the real discriminating signal by sequence, direction, and type

Why this survives reduction:
- it is the cleanest interpretive packet in the parent batch
- it keeps type and sequence claims tied to the branch where they actually show up

Source lineage:
- parent clusters:
  - `S3`
  - `S4`
- parent distillates:
  - `D2`
  - `D3`
- parent candidate `C2`
- parent tension `T5`
- comparison anchors:
  - `BATCH_A2MID_sims_axis4_p03_evidence_path__v1:RC5`
  - `BATCH_A2MID_sims_runner_pairing_hygiene__v1:RC6`

Preserved limits:
- this batch does not claim a uniform type split across both branches
- it preserves branch-specific interpretation only

## Quarantined Residue Q1) `CURRENT_DIRECTIONAL_RUNNER_FILENAMES_AS_PROVEN_EVIDENCED_PRODUCER_PATH`
Status:
- `QUARANTINED`

Preserved residue:
- current directional runner filenames
- paired result filenames
- all read as if they already prove the evidenced producer path

Why it stays quarantined:
- the top-level evidence pack binds the directional SIM_ID blocks to a different code hash
- filename pairing alone is not enough to close the provenance gap

Source lineage:
- parent cluster `S6`
- parent distillate `D5`
- parent tension `T1`
- parent candidate `C4`

## Quarantined Residue Q2) `ONE_DIRECTION_LABEL_EQUALS_ONE_DIRECTION_ONLY_EVIDENCE_BLOCK`
Status:
- `QUARANTINED`

Preserved residue:
- direction-labeled SIM_ID blocks
- all read as if each stored evidence block contained only one direction

Why it stays quarantined:
- the stored top-level blocks carry both forward and reverse metrics
- later evidence consumers should not collapse the block semantics to the label alone

Source lineage:
- parent tension `T2`
- parent candidate `C4`

## Quarantined Residue Q3) `AGGREGATE_BIDIR_SIBLING_AS_FULL_FAMILY_SUMMARY`
Status:
- `QUARANTINED`

Preserved residue:
- `S_SIM_AXIS4_SEQ_ALL_BIDIR_V1`
- compact T1 and T2 aggregate fields
- all read as if the sibling fully summarizes the family

Why it stays quarantined:
- the aggregate drops the plus branch and compresses multiple executable surfaces into one theory-facing artifact
- this is a convenience layer, not a full replacement

Source lineage:
- parent cluster `S5`
- parent distillate `D4`
- parent tension `T3`
- parent candidate `C5`

## Quarantined Residue Q4) `TYPE2_AS_FULLY_EVIDENCED_OR_AS_ABSENT`
Status:
- `QUARANTINED`

Preserved residue:
- Type-2 results and aggregate presence
- missing per-direction top-level evidence blocks
- all collapsed into either `fully evidenced` or `absent`

Why it stays quarantined:
- both claims overstate the source record
- the source record preserves a real middle state that has to stay visible

Source lineage:
- parent distillate `D6`
- parent tension `T4`

## Quarantined Residue Q5) `UNIFORM_PER_SEQUENCE_ARTIFACT_POLICY_ACROSS_THE_FAMILY`
Status:
- `QUARANTINED`

Preserved residue:
- Seq01 and Seq02 dedicated files
- Seq03 and Seq04 merged file
- all Type-2 sequences merged into one file
- all read as if the family had one uniform per-sequence artifact policy

Why it stays quarantined:
- the parent batch explicitly preserves three different storage granularities
- later stitching or automation should not assume one uniform artifact grain

Source lineage:
- parent tension `T6`

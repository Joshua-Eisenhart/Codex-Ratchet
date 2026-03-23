# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_sims_axis4_p03_evidence_path__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-08

## Candidate RC1) `AXIS4_P03_DUAL_HARNESS_SINGLE_RESULT_NAMESPACE_PATTERN`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the current Axis4 P03 core family is best read as:
  - two near-duplicate harnesses
  - one shared four-file P03 result namespace
  - divergent sidecar evidence contracts layered on top of the same result targets

Why this survives reduction:
- it is the clearest outer interface pattern in the parent batch
- it keeps same-family duplication visible without flattening the harnesses into one script

Source lineage:
- parent cluster:
  - `S1`
  - `S3`
- parent distillate `D1`
- parent candidate `C2`
- parent tension:
  - `T2`
  - `T3`

Preserved limits:
- this batch does not declare either harness authoritative
- it does not claim the two sidecar contracts are equivalent

## Candidate RC2) `AXIS4_POLARITY_ORDERING_EXECUTABLE_SEAM`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the clearest executable-facing Axis4 seam in the parent batch is:
  - polarity `+` as terrain CPTP then pinch
  - polarity `-` as unitary redistribution then terrain CPTP

Why this survives reduction:
- both harnesses encode the same ordering story
- it is the cleanest reusable Axis4 claim in the parent batch

Source lineage:
- parent cluster `S2`
- parent distillate `D2`
- parent candidate `C3`
- parent tension `T4`

Preserved limits:
- this batch does not turn the polarity seam into a generic theory law
- the sequence-effect read remains polarity-specific rather than universal

## Candidate RC3) `TYPE1_ONLY_P03_SCOPE_GATE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the stored P03 family should be kept explicitly scoped to:
  - `axis3_sign = +1`
  - `seed = 0`
  - `num_states = 256`
  - `cycles = 64`

Why this survives reduction:
- it is the parent batch's strongest anti-overread boundary
- it prevents the current P03 family from being silently extended into Type-2 or broader Axis4 claims

Source lineage:
- parent distillate `D3`
- parent candidate:
  - `C1`
  - `C3`
- parent tension `T5`

Preserved limits:
- this batch does not infer missing negative-sign family behavior
- scope gating here is family-local, not a generic repo rule

## Candidate RC4) `P03_RESULT_HASH_TO_TOPLEVEL_EVIDENCE_ALIGNMENT`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- one clean evidence-path claim does survive reduction:
  - the four stored P03 result hashes align with the top-level evidence-pack entries
  - those entries bind to the `axis4_seq_cycle_sim.py` code hash

Why this survives reduction:
- it is the parent batch's clearest current runner/result/evidence linkage
- it is narrower and cleaner than any broader producer-authority claim

Source lineage:
- parent cluster `S4`
- parent distillate `D5`
- parent candidate `C4`
- parent tension `T2`

Preserved limits:
- this batch does not declare the alternate harness dead
- it only preserves the currently evidenced producer path

## Candidate RC5) `POLARITY_SPECIFIC_SEQUENCE_SENSITIVITY`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the current P03 result family should be summarized as:
  - `polarity_plus` sequence-invariant across `SEQ01` to `SEQ04`
  - `polarity_minus` sequence-sensitive across the same set

Why this survives reduction:
- it is the cleanest anti-flattening result in the parent batch
- it keeps sequence claims tied to the branch where they actually appear

Source lineage:
- parent cluster `S5`
- parent distillate `D4`
- parent candidate `C3`
- parent tension `T4`

Preserved limits:
- this batch does not speak for later directional suites or Type-2 families
- it does not summarize Axis4 as generically sequence-sensitive

## Quarantined Residue Q1) `HARNESS_FILENAME_IDENTITY_DRIFT`
Status:
- `QUARANTINED`

Preserved residue:
- `axis4_seq_cycle_sim.py` self-labels as `run_axis4_sims.py`
- a separate real `run_axis4_sims.py` file also exists

Why it stays quarantined:
- this is genuine source-level identity confusion
- it should stay visible as residue rather than being silently normalized into one filename story

Source lineage:
- parent cluster `S6`
- parent tension `T1`
- parent source map structural map

## Quarantined Residue Q2) `ALTERNATE_HARNESS_AUTHORITY_UNRESOLVED`
Status:
- `QUARANTINED`

Preserved residue:
- one harness hash is evidenced in the top-level pack
- the alternate harness hash currently lacks that evidence-pack anchor

Why it stays quarantined:
- the current batch is not enough to kill or crown the alternate harness
- producer authority remains unresolved even though one path is presently evidenced

Source lineage:
- parent cluster:
  - `S4`
  - `S6`
- parent candidate `C5`
- parent tension `T2`

## Quarantined Residue Q3) `SIDECAR_RECONCILIATION_UNRESOLVED`
Status:
- `QUARANTINED`

Preserved residue:
- one harness writes per-SIM evidence files
- the other writes one packed `sim_evidence_pack.txt`

Why it stays quarantined:
- the sidecar texts were not reconciled inside the parent batch
- keeping the contract divergence visible is cleaner than implying a common sidecar standard

Source lineage:
- parent cluster `S3`
- parent candidate `C2`
- parent tension `T3`

# A2_2_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / CANDIDATE REDUCTIONS
Batch: `BATCH_work_surface_bootstrap_revision_ladder_completion__v1`
Extraction mode: `BOOTSTRAP_REVISION_LADDER_PASS`

## Candidate 1: `V3_BOOTSTRAP_PLATEAU_PACKET`
- candidate type:
  - revision-stability subset
- compressed read:
  - `v3__rev4` through `v3__rev8` share the same sampled embedded control payloads despite differing outer zip hashes and sizes
- promotion caution:
  - preserve the persistent internal `v2` self-label and wrapper-churn ambiguity

## Candidate 2: `REV9_BOOTSTRAP_BREAK_PACKET`
- candidate type:
  - revision-break subset
- compressed read:
  - `rev9` is the first remaining `v3` revision that updates the embedded identity and adds three saved `system_v3` files
- promotion caution:
  - keep the late sidecar adoption and the file-count jump explicit

## Candidate 3: `V4_BOOTSTRAP_CONTROL_SPINE_PACKET`
- candidate type:
  - bootstrap-shell subset
- compressed read:
  - `v4__rev2` keeps the `v4` identity and a leaner save-profile count while adding runtime-lock and batching docs to the bootstrap shell
- promotion caution:
  - preserve the fact that shell growth and saved-payload growth diverge here

## Candidate 4: `BOOTSTRAP_SIDEcar_INTEGRITY_PACKET`
- candidate type:
  - integrity subset
- compressed read:
  - sidecar checksums appear only at the late end of the ladder and remain one-line digests without filename binding
- promotion caution:
  - keep the auditability limits of this integrity style visible

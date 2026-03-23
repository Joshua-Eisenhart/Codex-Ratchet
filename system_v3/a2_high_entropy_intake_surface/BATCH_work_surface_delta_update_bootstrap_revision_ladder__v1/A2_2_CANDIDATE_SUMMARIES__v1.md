# A2_2_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / CANDIDATE REDUCTIONS
Batch: `BATCH_work_surface_delta_update_bootstrap_revision_ladder__v1`
Extraction mode: `REVISION_LADDER_EXPORT_PASS`

## Candidate 1: `DELTA_REVISION_LADDER_PACKET`
- candidate type:
  - external-thread delta subset
- compressed read:
  - delta `v2` to `v4` keeps the same canon-lock/tooling bridge while adding branch-thread extracts and issue ledgers
- promotion caution:
  - preserve the frozen inner `v2` naming and the “small pack” vs growing size tension

## Candidate 2: `EXTERNAL_REPAIR_PROMPT_PACKET`
- candidate type:
  - prompt-and-deliverables subset
- compressed read:
  - the embedded delta prompt asks for a lean canon-lock patch bootstrap plus reasoning-job and batch-generation outputs
- promotion caution:
  - keep it proposal-side and spillover-side, not active lower-loop contract

## Candidate 3: `UPDATE_PACK_STALE_MANIFEST_PACKET`
- candidate type:
  - transport-audit subset
- compressed read:
  - update-pack `v2` keeps a stale `648` copied-file count while dropping two archive members relative to `v1`
- promotion caution:
  - later reduction should check active packaging tooling before generalizing any fix

## Candidate 4: `BOOTSTRAP_READ_FIRST_EVOLUTION_PACKET`
- candidate type:
  - bootstrap-revision subset
- compressed read:
  - bootstrap `v3` is internally mislabeled as `v2`, while bootstrap `v4__rev1` expands the read-first control spine with runtime-lock and batch-discipline docs
- promotion caution:
  - keep the naming lag and the added-doc delta visible together

## Candidate 5: `DETACHED_CHECKSUM_STYLE_PACKET`
- candidate type:
  - integrity subset
- compressed read:
  - sidecar checksums remain one-line digests without filename binding and appear unevenly across adjacent revisions
- promotion caution:
  - preserve the lower auditability of this style compared with richer ledgers or manifests

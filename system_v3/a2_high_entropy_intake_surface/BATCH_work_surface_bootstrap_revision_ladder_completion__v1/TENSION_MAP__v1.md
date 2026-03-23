# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_work_surface_bootstrap_revision_ladder_completion__v1`
Extraction mode: `BOOTSTRAP_REVISION_LADDER_PASS`

## T1) outer `v3` revision ladder vs internal `v2` identity
- source markers:
  - embedded `00_READ_FIRST.md` from `v3__rev4` through `v3__rev8`: `1-30`
- tension:
  - outer filenames say `SYSTEM_REPAIR_BOOTSTRAP_v3__rev4` through `rev8`
  - embedded read-first still says `SYSTEM_REPAIR_BOOTSTRAP_v2`
- preserved read:
  - outer revisioning outruns internal identity cleanup for most of the remaining `v3` ladder

## T2) stable embedded controls vs drifting outer archives
- source markers:
  - `v3__rev4` through `v3__rev8` size/hash table
  - identical embedded read-first and save-profile hashes across `rev4` through `rev8`
- tension:
  - the key embedded control artifacts are identical
  - the outer zip bytes and hashes still differ across revisions
- preserved read:
  - wrapper-level churn exists even when the sampled control payload is stable

## T3) `rev9` grows the saved system payload vs `v4__rev2` shrinks it again
- source markers:
  - `v3__rev9` embedded save-profile `file_count: 644`
  - `v4__rev2` embedded save-profile `file_count: 641`
  - normalized save-profile diff between `rev9` and `v4__rev2`
- tension:
  - `rev9` adds three `system_v3` files
  - `v4__rev2` removes those three while still becoming a larger outer zip
- preserved read:
  - bootstrap shell growth and saved system payload growth do not move together

## T4) larger `v4__rev2` zip vs leaner save profile
- source markers:
  - outer byte sizes for `rev9` and `v4__rev2`
  - normalized zip diff between `rev9` and `v4__rev2`
- tension:
  - `v4__rev2` is a larger archive
  - its save-profile manifest is smaller while its bootstrap layer adds many control docs
- preserved read:
  - the bundle invests in overlay/control breadth rather than in broader saved `SYSTEM/` membership

## T5) late sidecar adoption vs earlier unpaired revisions
- source markers:
  - presence of sidecars only for `v3__rev9` and `v4__rev2`
  - absence of sidecars for `v3__rev4` through `v3__rev8`
- tension:
  - integrity sidecars appear in the late revisions
  - the earlier remaining ladder revisions have no adjacent sidecars in `work/out`
- preserved read:
  - integrity practice matures late and unevenly

## T6) `rev9` internal identity repair vs `v4__rev2` broader control escalation
- source markers:
  - `rev9` embedded read-first: `1-30`
  - `v4__rev2` embedded read-first: `1-49`
- tension:
  - `rev9` fixes the internal top-line name to `v3`
  - `v4__rev2` goes further by expanding runtime-lock, append-log, path-family, integration-map, and batching guidance
- preserved read:
  - fixing the name and tightening the bootstrap control spine are related but distinct steps

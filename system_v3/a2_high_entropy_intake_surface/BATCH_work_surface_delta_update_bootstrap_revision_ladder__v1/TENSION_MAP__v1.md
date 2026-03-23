# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_work_surface_delta_update_bootstrap_revision_ladder__v1`
Extraction mode: `REVISION_LADDER_EXPORT_PASS`

## T1) outer delta versions advance while inner packaging stays frozen at `v2`
- source markers:
  - delta `v2`, `v3`, `v4` zip listings
- tension:
  - the outer archive names advance from `v2` to `v4`
  - the inner folder, readme, and prompt naming remain `PRO_THREAD_DELTA__v2`
- preserved read:
  - revision labels are not synchronized across wrapper and payload layers

## T2) small-delta claim vs steady extract accretion
- source markers:
  - embedded delta `v2` README: `1-27`
  - normalized delta diffs `v2 -> v3` and `v3 -> v4`
- tension:
  - the readme says the delta is intentionally small
  - each revision adds more extracted context and by `v4` the archive size has roughly doubled from `v2`
- preserved read:
  - “small” here describes intent, not fixed size

## T3) prompt says keep the next artifact lean vs update-pack `v2` rebundles broadly
- source markers:
  - embedded delta prompt: `24-27`
  - update-pack `v2` embedded manifest: `1-23`
- tension:
  - the delta prompt allows a lean patch and warns against duplicating full trees
  - the nearby update-pack `v2` remains a broad multi-hundred-file export
- preserved read:
  - the spillover line has not converged on one stable downstream packaging scale

## T4) update-pack `v2` manifest count vs actual reduced content set
- source markers:
  - update-pack `v2` embedded manifest: `1-23`
  - normalized diff against update-pack `v1`
- tension:
  - embedded manifest still declares `648` copied files
  - normalized content diff shows two archive removals relative to `v1`
- preserved read:
  - metadata lag remains explicit; do not silently trust the copied-file count

## T5) update-pack `v2` points forward to `SYSTEM_REPAIR_BOOTSTRAP_v4__rev2.zip` while this ladder is still on first bootstrap artifacts
- source markers:
  - update-pack `v2` embedded manifest: `5-12`
  - bootstrap sources in this batch: `v3` and `v4__rev1`
- tension:
  - the update pack already bundles a later bootstrap revision than the adjacent first bootstrap artifacts processed here
- preserved read:
  - the export families are not perfectly sequential even when they sit next to each other in `work/out`

## T6) bootstrap `v3` wrapper name vs internal read-first name
- source markers:
  - bootstrap `v3` embedded read-first: `1-5`
- tension:
  - the outer zip is `SYSTEM_REPAIR_BOOTSTRAP_v3.zip`
  - the read-first plaque still says `SYSTEM_REPAIR_BOOTSTRAP_v2`
- preserved read:
  - bootstrap self-description drift is concrete and should stay visible

## T7) bootstrap `v4` adds runtime-lock docs while keeping the same broad overlay claim
- source markers:
  - bootstrap `v3` embedded read-first: `15-30`
  - bootstrap `v4` embedded read-first: `15-42`
- tension:
  - both read-first plaques keep the same repair/overlay framing
  - `v4` materially expands read-first control guidance with runtime canon, append log, spinner, degree-of-freedom, batch generation, and crosscheck surfaces
- preserved read:
  - stable narrative framing coexists with real operational tightening

## T8) detached checksum sidecars remain thin and unevenly adopted
- source markers:
  - all sidecars: `1-1`
  - absence of adjacent sidecar for bootstrap `v3` in this batch
- tension:
  - integrity digests are present for most revisions
  - they remain path-dependent one-line files, and bootstrap sidecar adoption is not even across adjacent versions
- preserved read:
  - checksum presence is not the same thing as strong self-describing transport integrity

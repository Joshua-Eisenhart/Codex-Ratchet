# TENSION_MAP__v1
Batch: `BATCH_archived_state_zip_index_v1__v1`
Extraction mode: `ZIP_INDEX_PASS`

## Tension T1
- label: inventory presence vs authority
- source anchors: `ZIP_INDEX_v1.md:1-202`
- why it matters:
  - the index lists many serious-sounding system artifacts, but the document itself only proves package inclusion
- proposal-side handling:
  - do not promote indexed payloads into active law from this batch

## Tension T2
- label: transport-heavy archive vs current non-mutation boundary
- source anchors: `ZIP_INDEX_v1.md:47-50`, `ZIP_INDEX_v1.md:189-202`
- why it matters:
  - the bundle contains both thread-save and export-pack zip artifacts
  - active A2 contrast already in scope says save ZIPs are informational only and A2 must not emit mutation containers
- proposal-side handling:
  - treat this as archived transport history and drift evidence

## Tension T3
- label: duplicated state vs single-current-state expectation
- source anchors: `ZIP_INDEX_v1.md:185-202`
- why it matters:
  - core A2 docs appear once under `A2_UPDATED_MEMORY` and again inside `A2_EXPORT_PACK_SMALL_2026-02-12T043701Z`
- proposal-side handling:
  - preserve duplication as stale-state and packaging-history evidence

## Tension T4
- label: curated archive vs noisy package residue
- source anchors: `ZIP_INDEX_v1.md:8`, `ZIP_INDEX_v1.md:203-326`
- why it matters:
  - `.DS_Store`, `.meta`, and `__MACOSX` mirrors coexist with intended payloads
- proposal-side handling:
  - preserve the noise because it signals how the archive was actually assembled

## Tension T5
- label: bounded-lane rules vs indexed forbidden payload classes
- source anchors: `ZIP_INDEX_v1.md:27-46`
- why it matters:
  - this archived index names `upgrade docs`, but this lane is explicitly not allowed to process those docs themselves
- proposal-side handling:
  - retain only the index-level fact that they were present in the bundle

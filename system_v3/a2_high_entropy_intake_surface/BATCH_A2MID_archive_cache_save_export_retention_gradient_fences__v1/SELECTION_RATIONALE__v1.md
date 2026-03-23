# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / A2-MID SELECTION RATIONALE
Batch: `BATCH_A2MID_archive_cache_save_export_retention_gradient_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Why this child batch exists
- the early `a2_feed` big-doc lane closure audit selected the purgeable cache save-export family as the strongest next archive parent
- the family is small enough to reduce cleanly in one bounded child
- it also sits at a useful bridge point between:
  - fuller retained save exports
  - thinner later archive-derived extraction packages

## Why this reduction is bounded this way
- the parent is not useful as doctrine
- its least noisy value is archival and comparative:
  - export-lineage
  - profile split
  - near-live state drift
  - detached checksum practice
  - retention-gradient evidence
- the first child should therefore preserve:
  - purgeability-versus-value tension
  - minimal integrity witness
  - fuller save-body witness
- and quarantine:
  - runtime overread
  - provenance overread
  - folder-order bias

## Why comparison anchors were chosen
- `BATCH_A2MID_early_a2feed_bigdoc_lane_closure_audit__v1`
  - used to preserve the live-ledger routing rule that this family now outranks deep-archive root descent
- `BATCH_A2MID_archive_batch10_terminal_savekit_vocabulary_fences__v1`
  - used to preserve the contrast between richer purgeable cache save bodies and the thinner terminal archive-derived save-kit scaffold
- `BATCH_archive_surface_deep_archive_root_milestone_split__v1`
  - used to preserve the rule that topology-first deep-archive descent remains real but should follow this smaller bridge

## Why no raw source reread was needed
- the parent first-pass artifacts already isolate:
  - family membership
  - profile split
  - integrity sidecars
  - drift pattern
  - retention-gradient value
- that is enough for a bounded comparative child
- a later quote-bound or embedded-manifest pass can reopen raw zip payloads if needed

## Why this is not yet a deep-archive child
- the deep-archive root remains topology-first and much larger
- the cache export family is the cleaner next bridge because it directly explains what later archive-derived packages lost

## Best next consequence from this child
- later work can now compare:
  - fuller purgeable cache exports
  - thinner later archive packages
  - deeper milestone and migrated-run retention
- without flattening those archive tiers into one lane

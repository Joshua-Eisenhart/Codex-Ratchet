# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / A2-MID SELECTION RATIONALE
Batch: `BATCH_A2MID_early_a2feed_bigdoc_lane_closure_audit__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Why this audit batch exists
- the queued next step after the A0 child was not another direct source reduction
- the real bounded job was to confirm whether the early `a2_feed` big-doc lane was now actually closed
- repo state now shows direct A2-mid children for:
  - `A0` threadsave
  - GPT trigram
  - Grok integrated-model
  - Grok/Gemini replay
- that means the lane should now be exited by live-ledger audit rather than stale queue habit

## Why the early a2feed lane is no longer the best next pool
- the prior post-archive selection audit was explicitly pointing at this pool because it was still unchilded
- that selection has now been discharged
- reopening the same lane again would mostly repeat already-earned reduction coverage

## Why the next target moves into archive save/export versus deep-archive routing
- after early a2feed closure, the strongest unresolved source-bearing archive pool is now:
  - the purgeable cache save-export family
  - the deep-archive milestone root family
- those are the next remaining source-bearing archive parents with clear unresolved re-entry value

## Why the purgeable cache save-export family wins now
- it is much smaller and more bounded than the deep-archive root
- it is checksum-tight and structurally explicit:
  - five save exports
  - detached sha256 sidecars
  - bootstrap/debug profile split
  - narrow current-state drift across near-duplicates
- its first-pass candidate summaries also preserve the highest-yield reason to reopen it:
  - these exports retain fuller save bodies than later archive-derived extraction packages
- that makes it the cleanest bridge between:
  - historical full-save retention
  - later top-layer archive loss

## Why the deep-archive root is not next
- it is still highly valuable
- but its own first-pass result says it is mainly a root topology map
- the main reusable seam there is the registry-guided descent, not immediate root-level A2-mid reduction
- the family mass is still too dominated by:
  - `7805` files
  - migrated run-root topology
  - current-state residue
- that makes it a lower-yield next child than the cache export bridge

## Best next existing intake target
- `BATCH_archive_surface_cache_recent_purgeable_save_exports__v1`

## Best next consequence from this audit
- after the cache export family gets its first A2-mid child, the next routing question can be revisited cleanly:
  - whether to descend through deep-archive root topology first
  - or to target one of the already-isolated deep-archive run descendants

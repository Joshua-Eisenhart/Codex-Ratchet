# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / A2-MID SELECTION RATIONALE
Batch: `BATCH_A2MID_post_archive_a2feed_bigdoc_selection_audit__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Why this audit batch exists
- the stale queued next step still pointed at archive-root closure work
- repo state already contains:
  - the archive packaged-sequence closure audit
  - the batch03 child
  - the batch02 child
  - the batch01 child
- the real bounded job now is a fresh residual audit from the live ledger

## Why the archive-root packaged family is no longer the best next lane
- batch01 through batch10 now have enough direct-child coverage to stop dominating next-step selection
- the archive lane still has historical value, but it no longer provides the strongest immediate unresolved source-bearing parent
- repeating archive-package closure work would now be stale-lane reopening

## Why the next target should come from the early a2feed big-doc pool
- the strongest still-unchilded source-bearing parents now cluster in the early `a2_feed_high entropy doc` root
- these are big mixed transcripts, but they are direct source surfaces rather than archive packaging or purgeable inventory
- the four real candidates are:
  - `BATCH_a2feed_a0_threadsave_source_map__v1`
  - `BATCH_a2feed_gpt_thread_a1_trigram_source_map__v1`
  - `BATCH_a2feed_grok_eisenhart_model_source_map__v1`
  - `BATCH_a2feed_grok_gemini_digested_model_source_map__v1`

## Why the A0 threadsave root is not next
- it is extremely valuable as early lineage and corpus inventory
- but its source-map value is still composite and operationally broad:
  - embedded bootpacks
  - reports
  - snapshots
  - export cycles
  - sim-runner instructions
- that makes it lower-yield for the immediate next bounded reduction than the GPT trigram workshop

## Why the Grok integrated-model file is not next
- it remains broad, repetitive, and revisionary
- its later seams are real:
  - operator or terrain conflict
  - bit `3<->6` swap lineage
  - vortex versus spiral naming
- but the file still carries heavier integrated worldview residue and stronger late-repair turbulence than the GPT trigram file

## Why the Grok-Gemini digested model file is not next
- it has strong historical value
- but it is more replay-heavy and duplication-dense:
  - UI residue
  - replay blocks
  - mining outputs
  - save snapshots
  - correction manifesto
- its next clean pass is still possible, but it is less bounded for immediate reduction than the GPT trigram file

## Why the GPT trigram file is the strongest next target
- it is explicitly `REVISIT_REQUIRED`
- its own source map already names the right narrower later passes:
  - Thread A / Thread B bridge law
  - SIM and evidence protocol material
  - correlation-first foundation material
  - axis and trigram conflict material
- it also has stronger nearby sibling anchors than the other candidates:
  - branchthread workflow repair
  - apple axis term conflicts
  - Thread A outer interface

## Best next existing intake target
- `BATCH_a2feed_gpt_thread_a1_trigram_source_map__v1`

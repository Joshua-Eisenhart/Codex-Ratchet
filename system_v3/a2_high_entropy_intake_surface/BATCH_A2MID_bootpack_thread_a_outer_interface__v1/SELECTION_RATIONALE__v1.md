# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / A2-MID BATCH SELECTION NOTE
Batch: `BATCH_A2MID_bootpack_thread_a_outer_interface__v1`
Extraction mode: `ENGINE_PATTERN_REDUCTION_PASS`
Date: 2026-03-08

## 1) Selected Parent Batch
Selected parent:
- `BATCH_upgrade_docs_bootpack_thread_a_engine_pattern__v1`

## 2) Why This Was The Next A2-Mid Target
Selection basis:
- it already existed as a packaged intake batch
- it is more process-facing and lower-noise than starting another large theory-heavy raw source
- its strongest reusable value is outer-interface workflow patterning, not ontology

Why it is worth a bounded A2-mid pass now:
- validator-first routing is already compressed enough to reduce cleanly
- provenance/comparability gating is a distinct subfamily
- the doc makes its own noncanon/thread-local limits explicit, which makes quarantine boundaries clearer

## 3) Why Thread B Was Not Pulled In
Deferred parent:
- `BOOTPACK_THREAD_B_v3.9.13.md`

Reason for deferral:
- the user asked to stay inside existing intake artifacts
- the Thread A parent batch explicitly preserved its incompleteness relative to Thread B
- pairing them now would turn this step into a broader family re-read rather than a bounded reduction of one existing batch

## 4) Narrowing Choice Inside The Selected Parent
This reduction batch deliberately keeps only:
- noncanon outer-interface split
- atomic validator-first routing
- provenance/comparability gate patterns
- macro compression over stable atomic routes

This reduction batch deliberately quarantines:
- thread-local command vocabularies
- local rule-id surfaces with collisions
- any contract parts that clearly defer to unread Thread B

## 5) Batch Result Type
Result type for this pass:
- reusable outer-interface engine-pattern reduction
- contradiction-preserving
- source-linked to the parent intake batch
- proposal-side only

This is not:
- a live repo API surface
- a Thread A/Thread B merged contract
- an A2-1 promotion
- a raw upgrade-doc reread

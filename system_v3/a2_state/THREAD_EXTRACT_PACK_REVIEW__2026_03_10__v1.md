# THREAD_EXTRACT_PACK_REVIEW__2026_03_10__v1

Status: DRAFT / NONCANON / A2 CONTROL NOTE
Date: 2026-03-10
Role: bounded review of `PRO_CONTEXT_PACK__THREAD_EXTRACT__v1` versus `PRO_CONTEXT_PACK__THREAD_EXTRACT__AUTO__v1`

## 1) Size read

- `PRO_CONTEXT_PACK__THREAD_EXTRACT__v1`: `344K`
- `PRO_CONTEXT_PACK__THREAD_EXTRACT__AUTO__v1`: `484K`
- `PRO_CONTEXT_PACK__THREAD_EXTRACT__v1.zip`: `104K`
- `PRO_CONTEXT_PACK__THREAD_EXTRACT__AUTO__v1.zip`: `144K`

This is not a meaningful size pressure class.

## 2) Structural read

### `PRO_CONTEXT_PACK__THREAD_EXTRACT__v1`
- older/manual-style structured pack
- explicit subfolders:
  - `00_READ_FIRST`
  - `BRAINS`
  - `CANON_LOCK`
  - `SYSTEM_CORE_DOCS`
  - `SYSTEM_SPECS`
  - `UPGRADE_DOCS`

### `PRO_CONTEXT_PACK__THREAD_EXTRACT__AUTO__v1`
- auto-built pack
- flatter layout with:
  - `CONTEXT_PACK_INVENTORY.json`
  - `core_docs`
  - `system_v3`
  - `work`

## 3) Reference read

Live repo references found in current active surfaces point to:
- `PRO_CONTEXT_PACK__THREAD_EXTRACT__AUTO__v1`

No active-owner dependency was found for:
- `PRO_CONTEXT_PACK__THREAD_EXTRACT__v1`

But this is still not enough to prove the manual pack is useless, because it represents a distinct packaging form rather than a simple stale duplicate.

## 4) Decision

No archive mutation from this review.

Reason:
- both packs are small
- they appear to serve distinct manual vs auto packaging roles
- there is no urgent size pressure here
- forcing a cleanup decision now would be lower-value than resolving larger ambiguous surfaces

## 5) Keep decision

Keep for now:
- `PRO_CONTEXT_PACK__THREAD_EXTRACT__v1`
- `PRO_CONTEXT_PACK__THREAD_EXTRACT__v1.zip`
- `PRO_CONTEXT_PACK__THREAD_EXTRACT__v1.zip.sha256`
- `PRO_CONTEXT_PACK__THREAD_EXTRACT__AUTO__v1`
- `PRO_CONTEXT_PACK__THREAD_EXTRACT__AUTO__v1.zip`
- `PRO_CONTEXT_PACK__THREAD_EXTRACT__AUTO__v1.zip.sha256`

## 6) Follow-on implication

Stop broad send-surface cleanup here.

The next higher-value local maintenance target is:
- narrower quarantine-prep investigation of `work/system_v3`

That is still the largest ambiguous spillover surface left after the send-surface cleanup passes.

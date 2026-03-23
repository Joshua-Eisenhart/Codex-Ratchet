# A2_3_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / QUARANTINED DISTILLATES
Batch: `BATCH_work_surface_bootstrap_revision_ladder_completion__v1`
Extraction mode: `BOOTSTRAP_REVISION_LADDER_PASS`
Promotion status: `A2_3_REUSABLE`

## 1) Reusable Process Patterns
### `PLATEAU_VS_BREAK_DETECTION_USING_EMBEDDED_HASHES`
- source anchors:
  - `v3__rev4` through `v3__rev9`
- distillate:
  - useful revision-audit pattern:
    - do not trust outer revision increments alone
    - compare embedded control-file hashes
    - detect the exact point where content actually changes
- possible downstream consequence:
  - useful later for auditing spillover export ladders without over-reading wrapper churn

### `BOOTSTRAP_SHELL_TIGHTENING_WITHOUT_PAYLOAD_EXPANSION`
- source anchors:
  - `v3__rev9`
  - `v4__rev2`
- distillate:
  - useful packaging pattern:
    - strengthen the read-first/control shell
    - keep or reduce the saved system payload
- possible downstream consequence:
  - useful later when comparing lean overlay upgrades against broad environment bundles

### `LATE_SIDEcar_INTEGRITY_ADOPTION`
- source anchors:
  - `v3__rev9.zip.sha256`
  - `v4__rev2.zip.sha256`
- distillate:
  - useful process pattern:
    - add detached checksums at later revision stages even if earlier revisions lacked them
- possible downstream consequence:
  - useful later when mapping transport hardening stages

## 2) Migration Debt / Prototype Residue
### `INNER_LABEL_LAG_ACROSS_FIVE_REVISIONS`
- read:
  - `v3__rev4` through `v3__rev8` still self-label as `v2`
- quarantine note:
  - this is persistent internal version drift, not a one-off typo

### `WRAPPER_CHURN_WITH_STABLE_CONTROLS`
- read:
  - outer zip hashes and sizes shift across `rev4` through `rev8` while key embedded control hashes remain identical
- quarantine note:
  - likely packaging/process churn remains visible even when sampled payloads are stable

### `SAVE_PROFILE_SCOPE_OSCILLATION`
- read:
  - save-profile `file_count` rises to `644` at `rev9`, then falls back to `641` at `v4__rev2`
- quarantine note:
  - saved-system scope is still being actively tuned

## 3) Contradiction-Preserving Summary
- the remaining bootstrap ladder is not one smooth monotone sequence
- it has:
  - a long stable plateau with stale internal naming
  - one late `v3` break that adds three saved files
  - one `v4` step that makes the bundle larger by strengthening bootstrap controls while slimming the saved system set
- preserving that split is more useful than flattening the ladder into “just newer is better”

## 4) Downstream Use Policy
- use this batch for:
  - bootstrap-revision archaeology
  - plateau-vs-break detection patterns
  - save-profile vs bootstrap-shell scope comparison
- do not use this batch for:
  - declaring any bootstrap export canonical
  - assuming later outer revisions are always semantically broader
  - treating sidecar presence as strong transport proof by itself

# B Accepted Containers (verbatim skeletons)

Status: NONCANON | Updated: 2026-02-18  
Source of truth: `core_docs/BOOTPACK_THREAD_B_v3.9.13.md`

## Accepted container skeletons (boot text)

From bootpack section `3) ACCEPTED CONTAINERS`:

- **EXPORT_BLOCK vN**
  - `BEGIN EXPORT_BLOCK vN`
  - `EXPORT_ID: <string>`
  - `TARGET: THREAD_B_ENFORCEMENT_KERNEL`
  - `PROPOSAL_TYPE: <string>`
  - `(Optional) RULESET_SHA256: <64hex>`
  - `CONTENT:`
  - (indented grammar lines only)
  - `END EXPORT_BLOCK vN`

- **SIM_EVIDENCE v1**
  - `BEGIN SIM_EVIDENCE v1`
  - `SIM_ID: <ID>`
  - `CODE_HASH_SHA256: <hex>`
  - `OUTPUT_HASH_SHA256: <hex>`
  - `METRIC: <k>=<v>`
  - `EVIDENCE_SIGNAL <SIM_ID> CORR <TOKEN> (repeatable)`
  - `KILL_SIGNAL <TARGET_ID> CORR <TOKEN>  (optional, repeatable)`
  - `END SIM_EVIDENCE v1`

- **THREAD_S_SAVE_SNAPSHOT v2**
  - `BEGIN THREAD_S_SAVE_SNAPSHOT v2`
  - `BOOT_ID: <string>`
  - `SURVIVOR_LEDGER:`
  - (indented verbatim accepted items)
  - `PARK_SET:`
  - (indented verbatim parked items)
  - `TERM_REGISTRY:`
  - (indented dump)
  - `EVIDENCE_PENDING:`
  - (indented dump)
  - `PROVENANCE:`
  - (indented metadata)
  - `END THREAD_S_SAVE_SNAPSHOT v2`

## Tag→rule pointer map (boot text only)

This is intentionally a pointer map; do not infer behavior not stated in the bootpack.

- `MULTI_ARTIFACT_OR_PROSE`: `MSG-001`
- `COMMENT_BAN`: `MSG-002`
- `SNAPSHOT_NONVERBATIM`: `MSG-003`
- `SHADOW_ATTEMPT`: `BR-004` (kill), also referenced by immutability semantics
- `FORWARD_DEPEND`: `BR-006` (park)
- `NEAR_REDUNDANT`: `BR-007` (park)
- `UNQUOTED_EQUAL`: `BR-0F3` (reject line)
- `UNDEFINED_TERM_USE`: `BR-0U1` (reject line)
- `DERIVED_ONLY_PRIMITIVE_USE`: `BR-0D1` (reject line)
- `DERIVED_ONLY_NOT_PERMITTED`: `BR-0D2` (reject line), also appears in formula scanning guards
- `GLYPH_NOT_PERMITTED`: `BR-0F5` / `BR-0F6` (reject line)
- `KERNEL_ERROR`: evidence-pack verification section (`SIM_EVIDENCE v1` requirements)
- `SCHEMA_FAIL`: multiple schema checks; also used as fallback when an unpermitted tag would otherwise be emitted

Observed-in-boot mismatch (do not resolve here):

- The string `TERM_DRIFT` is referenced by a “TERM_DRIFT_BAN” line, but `TERM_DRIFT` is not listed in `BR-000A TAG_FENCE` in the same bootpack copy.

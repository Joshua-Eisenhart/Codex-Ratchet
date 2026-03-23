# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_systemv3_active_a2state_entropy_pattern_drift_refresh__v1`
Extraction mode: `ACTIVE_A2STATE_ENTROPY_PATTERN_DRIFT_REFRESH_PASS`
Date: 2026-03-09

## 1) Scope
- bounded live-source refresh over the drifted entropy-topology subset inside the earlier active `a2_state` entropy-pattern family
- purpose:
  - preserve the exact three live topology files that no longer match the earlier first-pass manifest
  - keep the earlier batch intact as a historical snapshot
  - record where the entropy graveyard control packet thickened after the original pass

## 2) Source Set
- live drifted source members:
  - `system_v3/a2_state/ENTROPY_GRAVEYARD_FAILURE_TOPOLOGY__AUTO__v1.json`
  - `system_v3/a2_state/ENTROPY_GRAVEYARD_FAILURE_TOPOLOGY__AUTO__v1.md`
  - `system_v3/a2_state/ENTROPY_GRAVEYARD_FAILURE_TOPOLOGY__v1.md`
- comparison anchors:
  - `BATCH_systemv3_active_a2state_entropy_pattern_packet__v1/MANIFEST.json`
  - `BATCH_systemv3_active_a2state_ingest_validation_promotion_packet__v1/MANIFEST.json`

## 3) Why This Refresh Exists
- the queued reuse check failed because the earlier active `a2_state` entropy-pattern manifest no longer matched live repo state
- drift count:
  - changed members: `3`
  - unchanged members from the earlier family: `8`
- this packet does not replace the earlier batch
- it preserves the earlier batch as a source-bound March 9 snapshot and adds the now-live topology delta surface beside it

## 4) Drifted Membership By Function
- `a2_state/ENTROPY_GRAVEYARD_FAILURE_TOPOLOGY__AUTO__v1.json`
  - old snapshot: `157` lines / `5544` bytes
  - live source: `236` lines / `8142` bytes
  - main live drift:
    - top-level shape now foregrounds `aggregate_kill_tokens`, `cluster_projection`, `per_snapshot`, `profile`, and provenance keys
    - machine output is now a fuller projection surface rather than the thinner earlier auto topology snapshot
- `a2_state/ENTROPY_GRAVEYARD_FAILURE_TOPOLOGY__AUTO__v1.md`
  - old snapshot: `109` lines / `3600` bytes
  - live source: `112` lines / `3887` bytes
  - main live drift:
    - the generated control surface now foregrounds aggregate kill tokens, stable frontier tokens, cluster projection, and per-snapshot projection in a slightly thicker layout
- `a2_state/ENTROPY_GRAVEYARD_FAILURE_TOPOLOGY__v1.md`
  - old snapshot: `141` lines / `4738` bytes
  - live source: `140` lines / `4505` bytes
  - main live drift:
    - the human control surface now speaks more explicitly about the generated companion surfaces as mechanical confirmation
    - it adds a clearer divergence rule: audit source runs before changing A2/A1 control packs

## 5) Grouped Read
- machine-readable topology packet:
  - `ENTROPY_GRAVEYARD_FAILURE_TOPOLOGY__AUTO__v1.json`
- generated human-readable topology packet:
  - `ENTROPY_GRAVEYARD_FAILURE_TOPOLOGY__AUTO__v1.md`
- human control topology packet:
  - `ENTROPY_GRAVEYARD_FAILURE_TOPOLOGY__v1.md`

## 6) Current Best Read
- the earlier active entropy-pattern batch remains historically useful, but it is not current on these three topology files
- the live topology packet is now more explicit about:
  - aggregate kill-token frontier shape
  - cluster projection as an active control abstraction
  - per-snapshot projection as the main auto reporting frame
  - human-vs-auto divergence procedure
- the trust/quarantine, external-pattern, ladder, scaffold/foundation, quarry, and holodeck members from the earlier batch still source-match and do not need re-extraction here

## 7) Notes
- no active source was mutated
- no older batch was rewritten
- this packet is a bounded refresh surface, not a retroactive normalization of the earlier active `a2_state` entropy-pattern batch

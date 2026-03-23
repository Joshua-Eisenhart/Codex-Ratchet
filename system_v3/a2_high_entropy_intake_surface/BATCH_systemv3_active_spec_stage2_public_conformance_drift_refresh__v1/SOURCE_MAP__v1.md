# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_systemv3_active_spec_stage2_public_conformance_drift_refresh__v1`
Extraction mode: `ACTIVE_SPEC_STAGE2_PUBLIC_CONFORMANCE_DRIFT_REFRESH_PASS`
Date: 2026-03-09

## 1) Scope
- bounded live-source refresh over the drifted late-spec subset inside the earlier active Stage-2/public-conformance family
- purpose:
  - preserve the exact three live files that no longer match the earlier first-pass manifest
  - keep the earlier batch intact as a historical snapshot
  - record where the late delivery/build/schema packet thickened after the original pass

## 2) Source Set
- live drifted source members:
  - `system_v3/specs/21_IMPLEMENTATION_BUILD_SEQUENCE_AND_ACCEPTANCE_MATRIX.md`
  - `system_v3/specs/22_RUN_SURFACE_TEMPLATE_AND_SCAFFOLDER_CONTRACT.md`
  - `system_v3/specs/28_STAGE_2_JOB_SCHEMAS_AND_VALIDATION_STUBS__v1.md`
- comparison anchors:
  - `BATCH_systemv3_active_spec_stage2_public_conformance__v1/MANIFEST.json`
  - `BATCH_systemv3_active_a2state_entropy_pattern_packet__v1/MANIFEST.json`

## 3) Why This Refresh Exists
- the queued reuse check failed because the earlier Stage-2/public-conformance manifest no longer matched live repo state
- drift count:
  - changed members: `3`
  - unchanged members from the earlier family: `33`
- this packet does not replace the earlier batch
- it preserves the earlier batch as a source-bound March 9 snapshot and adds the now-live delta surface beside it

## 4) Drifted Membership By Function
- `specs/21_IMPLEMENTATION_BUILD_SEQUENCE_AND_ACCEPTANCE_MATRIX.md`
  - old snapshot: `128` lines / `4584` bytes
  - live source: `131` lines / `4734` bytes
  - main live drift:
    - sharper loop-health gate clause `RQ-132A`
    - explicit `Run Surface Guard`
    - explicit `RELEASE_CHECKLIST_v1.json` field schema
- `specs/22_RUN_SURFACE_TEMPLATE_AND_SCAFFOLDER_CONTRACT.md`
  - old snapshot: `299` lines / `9079` bytes
  - live source: `319` lines / `10193` bytes
  - main live drift:
    - explicit template-root fallback behavior
    - fuller producer and phase-gate CLI contracts
    - expanded real-loop helper, determinism-pair, and loop-health helper packet
    - thicker run-directory, determinism, fail-closed, and versioning rules
- `specs/28_STAGE_2_JOB_SCHEMAS_AND_VALIDATION_STUBS__v1.md`
  - old snapshot: `27` lines / `1125` bytes
  - live source: `29` lines / `1371` bytes
  - main live drift:
    - stub language now explicitly names current executable validator helpers
    - next-step language now frames Stage-3 as expanding existing validator use, not inventing validators from scratch

## 5) Grouped Read
- build and release hardening packet:
  - `specs/21_IMPLEMENTATION_BUILD_SEQUENCE_AND_ACCEPTANCE_MATRIX.md`
- run-surface and scaffolder concretion packet:
  - `specs/22_RUN_SURFACE_TEMPLATE_AND_SCAFFOLDER_CONTRACT.md`
- stage-2 schema-to-validator bridge packet:
  - `specs/28_STAGE_2_JOB_SCHEMAS_AND_VALIDATION_STUBS__v1.md`

## 6) Current Best Read
- the earlier Stage-2/public-conformance batch remains historically useful, but it is not current on these three files
- the live late-spec packet is now more explicit about:
  - guarded run-surface write posture and release-checklist structure
  - template-aware scaffolding with built-in deterministic fallback
  - stage-gate helper tooling and run helper surface area
  - validator-helper presence inside the Stage-2 schema story
- the conformance fixtures, public docs, schema JSON surfaces, and remaining late specs from the earlier batch still source-match and do not need re-extraction here

## 7) Notes
- no active source was mutated
- no older batch was rewritten
- this packet is a bounded refresh surface, not a retroactive normalization of the earlier active Stage-2/public packet

# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_systemv3_active_spec_stage2_public_conformance_drift_refresh__v1`
Extraction mode: `ACTIVE_SPEC_STAGE2_PUBLIC_CONFORMANCE_DRIFT_REFRESH_PASS`
Date: 2026-03-09

## T1) `SOURCE_BOUND_FIRST_PASS_EXACTNESS_VS_LIVE_STAGE2_SPEC_DRIFT`
- tension:
  - the earlier stage-2/public-conformance batch was source-bound and valid when created
  - three live members of that family now differ materially from the recorded snapshot
- preserve:
  - the older batch remains a historical snapshot
  - current reuse claims must follow live-source exactness, not merely batch existence

## T2) `RUN_SCOPED_WRITE_POSTURE_VS_HELPER_AND_TEMPLATE_EXPANSION`
- tension:
  - `specs/21` now sharpens the run-scoped write boundary and forbids `work/` as a run target
  - `specs/22` simultaneously expands helper/tooling, template-backed source refs, and fallback behavior
- preserve:
  - filesystem discipline remains the rule
  - helper and template surface expansion is real and should not be smoothed into a falsely lean story

## T3) `STAGE2_SCHEMA_STUB_LANGUAGE_VS_ALREADY_EXISTING_VALIDATOR_HELPERS`
- tension:
  - `specs/28` is still framed as a schema-stub surface
  - the live file now explicitly states that validator helpers already exist for active ZIP/job paths
- preserve:
  - schema hardening is still incomplete
  - executable validation presence is now stronger than the earlier pure-stub read implied

## T4) `EARLIER_LATE_SPEC_PACKET_VS_LIVE_RELEASE_CHECKLIST_CONCRETION`
- tension:
  - the earlier batch already carried release and run-surface language
  - the live `specs/21` surface now makes release-checklist fields and run-surface guardrails much more concrete
- preserve:
  - the older read was not false
  - the live build/release packet now carries stronger operational consequences than the first-pass packet recorded

## T5) `BOUNDED_REFRESH_VALUE_VS_FOLDER_ORDER_CONTINUITY`
- tension:
  - this refresh is necessary because the old batch can no longer be honestly reused
  - the folder-order continuation still moves into the active `system_v3/a2_state/` packet
- preserve:
  - the refresh has real value
  - it must not be mistaken for a change in continuation order or an excuse to reopen unchanged conformance/public members

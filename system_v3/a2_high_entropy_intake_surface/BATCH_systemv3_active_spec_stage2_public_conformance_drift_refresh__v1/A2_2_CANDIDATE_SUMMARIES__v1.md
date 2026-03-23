# A2_2_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / INTERMEDIATE CANDIDATE SUMMARY
Batch: `BATCH_systemv3_active_spec_stage2_public_conformance_drift_refresh__v1`
Extraction mode: `ACTIVE_SPEC_STAGE2_PUBLIC_CONFORMANCE_DRIFT_REFRESH_PASS`
Date: 2026-03-09

## Candidate Summary C1
- proposal-only reading:
  - the strongest reusable value in this packet is the rule that active late-spec reuse must be verified against live source membership, not assumed from an already-indexed batch name
- support:
  - three live members of the earlier stage-2/public packet no longer match its stored manifest

## Candidate Summary C2
- proposal-only reading:
  - the sharpest build/release drift is now concentrated in `specs/21`
- support:
  - the live file hardens run-surface write posture, release-checklist structure, and loop-health release gating

## Candidate Summary C3
- proposal-only reading:
  - the sharpest scaffolder/runtime drift is now concentrated in `specs/22`
- support:
  - the live file adds template fallback behavior, fuller helper CLI surface, and thicker run-directory / fail-closed / versioning rules

## Candidate Summary C4
- proposal-only reading:
  - the sharpest stage-2 validator drift is now concentrated in `specs/28`
- support:
  - the live file explicitly names current validator helpers and reframes Stage-3 as expanding existing executable validation rather than inventing it later

## Candidate Summary C5
- proposal-only reading:
  - the earlier `BATCH_systemv3_active_spec_stage2_public_conformance__v1` should now be treated as an early snapshot of the late-spec packet, not as the complete current read of that family
- support:
  - the earlier batch remains useful history, but it is no longer source-exact on the three drifted files

## Candidate Summary C6
- proposal-only reading:
  - the unchanged conformance/public/schema-json members should remain preserved from the earlier batch rather than being redundantly re-extracted here
- support:
  - drift is concentrated and bounded, not global across the full family

## Candidate Summary C7
- proposal-only next-step note:
  - the next bounded active-system continuation should now validate and reuse the active `a2_state` entropy-pattern packet
- support:
  - this refresh repaired only the current-family drift and did not change folder-order continuation

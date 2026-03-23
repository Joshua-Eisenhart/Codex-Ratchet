# A2_2_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / INTERMEDIATE CANDIDATE SUMMARY
Batch: `BATCH_systemv3_active_root_spec_control_spine_drift_refresh__v1`
Extraction mode: `ACTIVE_CONTROL_SPINE_DRIFT_REFRESH_PASS`
Date: 2026-03-09

## Candidate Summary C1
- proposal-only reading:
  - the strongest reusable value in this packet is the rule that active-family reuse must be verified against live source membership, not assumed from an existing bounded batch name alone
- support:
  - six live members of the earlier control-spine batch no longer match its stored manifest

## Candidate Summary C2
- proposal-only reading:
  - the sharpest owner/control drift packet is the combined expansion across `specs/00`, `specs/05`, and `specs/07`
- support:
  - together they add explicit overlay-aware read order, live A1 packet-profile detail, and stronger A2 freshness/audit rules

## Candidate Summary C3
- proposal-only reading:
  - the sharpest run/persistence drift packet is the combined expansion across `specs/08`, `specs/16`, and `specs/19`
- support:
  - together they make the filesystem contract, witness retention, archive demotion, compatibility profile, and refresh sequence much more concrete

## Candidate Summary C4
- proposal-only reading:
  - the earlier `BATCH_systemv3_active_root_spec_control_spine__v1` should now be treated as an early snapshot, not as the complete current read of the active root/spec control spine
- support:
  - the earlier batch remains useful history, but it is no longer source-exact on the six drifted files

## Candidate Summary C5
- proposal-only reading:
  - later active-lineage audit and manifest-reader helper packets remain useful, but they should be read as audit/bridge history over the older snapshot, not as proof that no live drift occurred afterward
- support:
  - those later packets explicitly depend on the older control-spine batch rather than the current live sources

## Candidate Summary C6
- proposal-only next-step note:
  - the next bounded active-system continuation should still validate and reuse `BATCH_systemv3_active_spec_stage2_public_conformance__v1`
- support:
  - this refresh repaired only the current-family drift and did not change folder-order continuation

## Candidate Summary C7
- proposal-only quarantine:
  - do not promote these live expansions straight into active A2-1 law from this batch alone
- support:
  - this packet is a bounded source refresh, not a promotion or rewrite authority surface

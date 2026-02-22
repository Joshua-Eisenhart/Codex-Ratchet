# Conformance and Redundancy Gates
Status: DRAFT / NONCANON
Date: 2026-02-20
Owner: `RQ-080..RQ-088`

## Gate 0: Authority Coverage (`RQ-088`)
- `RQ-088` MUST: run `system_v3/tools/authority_coverage_audit.py` and record `authority_gap_report.json` before any promotion.

## Gate 1: Ownership Integrity (`RQ-080`)
- each `RQ-*` has one owner doc
- non-owner docs may reference but not redefine owner requirements

## Gate 2: Unknown Handling (`RQ-081`)
- unresolved semantics are marked `UNKNOWN`
- unverified inference cannot be promoted to normative clause

## Gate 3: Root Constraint Protection (`RQ-082`)
- no spec weakens `RQ-001` / `RQ-002`
- any violation is immediate hard fail

## Gate 4: Anti-Paperclip (`RQ-083`)
Hard fail triggers:
- fake evidence tokens
- graveyard padding with untied junk
- admission-count optimization without evidence coverage

## Gate 5: Pre-Run Conformance (`RQ-084`)
Required before long runs:
- ownership map check
- schema check
- determinism check
- sim coverage check
- graveyard integrity check

## Gate 6: Owner/Orphan Lint (`RQ-085`)
Machine lint must verify:
- no owner collisions
- no orphan requirements
- no owner ranges missing from ledger

## Gate 7: Normative Drift Hash (`RQ-086`)
Maintain hash baseline for normative clauses:
- hash source: all `RQ-*` owner clauses
- compare against last promoted baseline
- report changed requirement ids and diff summary

## Gate 8: Promotion Audit Package (`RQ-087`)
Promotion requires:
- conformance pass report
- unresolved risks list
- change manifest
- rollback reference

Without full package, promotion is blocked.

## Gate 9: Controlled Tuning Class Gate
Before applying any runtime tuning proposal:
- require `TUNING_PROPOSAL_v1` classification present
- allow auto-apply only for `SAFE_PARAM` class
- require explicit review sign-off for `RULE_INTERPRETATION` and `SEMANTIC_CHANGE`
- require deterministic dual replay pass before promotion

## Gate 10: Fixture Matrix Lock
Before applying `RULE_INTERPRETATION` or `SEMANTIC_CHANGE`:
- lock fixture pack version and fixture pack hash
- run full conformance suite
- require 100% fixture match
- require bootpack hash match in conformance report

## Redundancy Lint Outputs
Minimum output artifacts:
- `owner_collision_report.json`
- `orphan_requirements_report.json`
- `normative_hash_report.json`
- `redundancy_report.json`

## Promotion Rule
No spec-pack promotion unless all gates pass.

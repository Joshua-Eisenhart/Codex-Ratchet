# Bootpack Sync Audit Spec (v1)
Status: DRAFT / NONCANON
Date: 2026-02-20

## Purpose
Detect drift between v3 owner docs and bootpack authority text.

Conformance-fixture companion:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/23_BOOTPACK_CONFORMANCE_FIXTURE_MATRIX_CONTRACT.md`

## Authority Inputs
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/BOOTPACK_THREAD_B_v3.9.13.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/BOOTPACK_THREAD_A_v2.60.md`

## Audit Scope
1. Container grammar sync
2. Fence/rule id sync
3. Stage order sync
4. Required policy flags sync
5. Allowed rejection tag sync
6. Known ambiguity/duplication regions (recorded, not smoothed)

## Output Artifact
- `reports/bootpack_sync_report.json`

Required fields:
- `sync_status`: `PASS|WARN|FAIL`
- `critical_drift[]`
- `noncritical_drift[]`
- `unknown_sections[]`
- `source_hashes`

## Severity Model
- `CRITICAL`: can alter admission outcomes.
- `MAJOR`: can alter operator behavior or repair routing.
- `MINOR`: wording/order mismatch without behavior change.

## Blocking Rule
Any `CRITICAL` drift blocks v3 promotion until resolved or explicitly waived with rationale.

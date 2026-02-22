# Bootpack Conformance Fixture Matrix Contract
Status: DRAFT / NONCANON
Date: 2026-02-20
Owner: `RQ-139..RQ-144`

## Scope
This document defines deterministic conformance fixture requirements used to validate B behavior and block drift.

Runner tool:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/run_conformance_fixture_matrix.py`

## Normative Clauses
- `RQ-139` MUST: each fixture has immutable `fixture_id`, `expected_status`, and `expected_tags[]`.
- `RQ-140` MUST: fixture metadata declares targeted rule families and carries minimal reproducible artifact payload only.
- `RQ-141` MUST: conformance runner emits per-fixture observed status/tags and mismatch diagnostics in deterministic JSON.
- `RQ-142` MUST: fixture set versions are append-only (`fixtures_v1`, `fixtures_v2`, ...); historical expectations remain immutable.
- `RQ-143` MUST: any tuning class `RULE_INTERPRETATION` or `SEMANTIC_CHANGE` requires 100% pass on frozen fixture set before promotion.
- `RQ-144` MUST: conformance report includes `bootpack_hash` and `fixture_pack_hash`.

## Fixture Pack Layout
Recommended location:
- `system_v3/conformance/fixtures_v1/`

Required files:
- `expected_outcomes.json`
- `fixtures/` (artifact payload files)
- `manifest.json`
- `observed_results.template.json`

`manifest.json` required keys:
- `schema`: `CONFORMANCE_FIXTURE_MANIFEST_v1`
- `fixture_pack_version`
- `fixture_count`
- `generated_utc`
- `bootpack_target`
- `fixture_pack_hash`

## Fixture Record Schema
Each fixture entry in `expected_outcomes.json`:
- `fixture_id`
- `rule_families[]` (e.g., `LEXEME_FENCE`, `UNDEFINED_TERM_FENCE`)
- `artifact_path`
- `expected_status`: `PASS|PARK|REJECT`
- `expected_tags[]`
- `preconditions` (optional object; deterministic setup requirements)
- `notes` (optional; non-normative)

## Minimum Rule Family Coverage
Required families in each fixture pack version:
- `MESSAGE_DISCIPLINE`
- `SCHEMA_CHECK`
- `LEXEME_FENCE`
- `UNDEFINED_TERM_FENCE`
- `DERIVED_ONLY_FENCE`
- `FORMULA_GLYPH_FENCE`
- `PROBE_PRESSURE`
- `EVIDENCE_INGEST`
- `DEPENDENCY_FORWARD_REF`
- `NEAR_DUPLICATE_PARK`

## Conformance Runner Output Contract
Required output:
- `conformance_results.json`

Observed-input contract (for non-dry runs):
- `observed_results.json` matching template schema.

Required top-level fields:
- `schema`: `CONFORMANCE_RESULTS_v1`
- `bootpack_hash`
- `fixture_pack_hash`
- `run_id`
- `totals`:
  - `pass_count`
  - `fail_count`
  - `mismatch_count`
- `results[]`

`results[]` entry fields:
- `fixture_id`
- `expected_status`
- `observed_status`
- `expected_tags[]`
- `observed_tags[]`
- `match` (boolean)
- `diagnostics[]`

## Promotion Gate Behavior
Blocking conditions:
- any `match = false`
- missing required rule family coverage
- bootpack hash mismatch against declared target
- fixture pack hash mismatch

If any blocking condition occurs:
- emit `sync_status = FAIL`
- block tuning promotion

## Acceptance Criteria (Spec-Level)
1. fixture without immutable `fixture_id` -> invalid fixture pack.
2. fixture without expected status/tags -> invalid fixture pack.
3. conformance report missing bootpack hash or fixture hash -> invalid report.
4. semantic tuning promotion attempted with non-green conformance -> block.

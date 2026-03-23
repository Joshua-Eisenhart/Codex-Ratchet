# A1_CONSOLIDATION_PREPACK_JOB__v1

Status: DRAFT / NONCANON
Date: 2026-03-06
Role: upper-layer ZIP_JOB family for merging many A1 worker outputs into one strict pre-A0 strategy surface

## 1) Purpose

This family exists to solve one specific upper-layer problem:

- many A1 workers can generate branch-rich family outputs
- only one ordered, deduped, provenance-preserving strategy surface should proceed toward `A0`

This family is:
- upper-layer only
- proposal-only
- noncanon
- a packaging and normalization step

This family is not:
- a transport ZIP type
- a lower-loop mutation path
- a replacement for `A1_TO_A0_STRATEGY_ZIP`

## 2) Position in the system

Execution order:
1. many A1 workers generate family outputs
2. one consolidation/prepack job normalizes those outputs
3. the job emits one strict `A1_STRATEGY_v1.json` candidate plus audit surfaces
4. only then may standard transport/package steps create `A1_TO_A0_STRATEGY_ZIP`

## 3) Inputs

Expected inputs are one or more worker result bundles containing:
- target families
- branch families
- negative classes
- rescue lineage candidates
- expected failure modes
- SIM hook sketches
- provenance / source refs

Inputs may come from:
- Codex A1 worker runs
- browser/Pro A1 worker runs
- prior A2->A1 distillation passes

## 4) Required outputs

Every valid consolidation/prepack run must emit:

1. one consolidated source registry
2. one term-family ordering report
3. one negative/rescue merge report
4. one conflict and dedup report
5. one `A1_STRATEGY_v1.json` candidate
6. one transport-readiness / fail-closed audit report

## 4.1) Active adapter path

Current active adapters:
- `system_v3/tools/run_a1_consolidation_prepack_job.py`
- `system_v3/tools/a1_external_memo_batch_driver.py` in exchange mode, which invokes the prepack adapter on each external response and records `exchange_prepack_rows` in the batch-driver report

## 5) Hard rules

- no canon claims
- no mutation containers
- no direct B-facing artifacts
- no hidden deduplication
- no silent conflict resolution
- no free-form collapse of distinct families into one narrative
- all worker provenance remains visible above the lower boundary
- unresolved schema conflict => FAIL_CLOSED
- unresolved target collision => FAIL_CLOSED unless explicitly partitioned

## 6) Ordering rules

The prepack step must produce one ordered strategy surface.

Ordering must respect:
- dependency prerequisites first
- substrate-before-axis ordering
- term-family grouping
- negative/rescue attachment to the correct family
- deterministic tie-breaks when two worker outputs compete

## 7) Provenance rules

Every merged family should preserve:
- worker/source bundle id
- source file refs
- branch lineage refs when present
- rescue lineage refs when present
- conflict notes for any dropped or partitioned candidate

## 8) Promotion rule

This family may emit a candidate `A1_STRATEGY_v1.json`.

It may not itself emit:
- `A1_TO_A0_STRATEGY_ZIP`
- `EXPORT_BLOCK`
- `SIM_EVIDENCE`
- `THREAD_S_SAVE_SNAPSHOT`

Transport packaging remains a separate step under transport law.

## 9) Prototype lineage

This family is derived from the already-existing prototype line:
- `work/zip_dropins/ZIP_JOB__A2_LAYER_1_5__MULTI_RUN_CONSOLIDATION_AND_A1_WIGGLE_PREP__*`
- `work/golden_tests/expected_checks/GOLDEN_CHECK__A2_LAYER_1_5__MULTI_RUN_CONSOLIDATION__v1.json`

It narrows that line into a cleaner A1-specific family.

## 10) Bottom line

This family turns many-worker exploratory richness into one strict pre-A0 proposal surface.

It is the missing upper-layer packaging contract between:
- broad A1 generation
and
- the existing deterministic lower loop.

## 11) Active adapter path

Current active adapter:
- `system_v3/tools/run_a1_consolidation_prepack_job.py`

That adapter is intentionally lean:
- ingest many worker memo JSONs (or one direct strategy JSON)
- normalize them into one sandbox sequence
- run existing `a1_lawyer_sink.py`
- run existing `a1_cold_core_strip.py`
- run existing `a1_pack_selector.py`
- emit one strict pre-A0 `A1_STRATEGY_v1` candidate plus a prepack report

This keeps the family aligned with existing tooling rather than inventing a new lower-loop path.

# EXTERNAL_RETURN_AUDIT_MESSAGE__ENTROPY_CARNOT_SZILARD__2026_03_10__v1

Status: DRAFT / NONCANON / A2 CONTROL NOTE
Date: 2026-03-10
Role: exact copy-paste audit message for the first external entropy / Carnot / Szilard monitored lane

Use this after the external thread returns.

Expected full output set:
- `SOURCE_AND_METHOD_MAP.out.md`
- `MATH_ASSUMPTION_AND_RETOOL_MAP.out.md`
- `RATCHET_FUEL_SELECTION_MATRIX.out.md`
- `PRO_THREAD_BOOT_AND_QUERY_PLAN.out.md`
- `INSTANT_AUDIT_BRIEF.out.md`
- `QUALITY_GATE_REPORT.out.md`
- `PORTABLE_OUTPUT_CONTRACT_AND_FAIL_CLOSED_VALIDATION.out.md`

Copy-paste message:

```text
Audit this external return before any A2 ingestion.

Required checks:
- completeness of the full output set
- citation quality
- overclaim
- ontology smuggling
- process-vs-math-vs-ontology separation
- explicit usable-now / usable-after-retool / reject-quarantine split
- preservation of disagreements between entropy forms and engine interpretations

Return exactly:
1. completeness: COMPLETE or INCOMPLETE
2. audit_result: PASS / PASS_WITH_CAUTIONS / FAIL_CLOSED
3. routing_decision: SAFE_FOR_A2_REDUCTION / HOLD_FOR_CORRECTION / RERUN_WITH_NARROWER_OR_CORRECTED_BOOT
4. strongest_keepers: up to 5
5. missing_or_blurred_lines
6. hard_fail_flags
7. next_controller_step

Do not smooth.
Do not ingest to A2 inside this step.
```

Controller note:
- if incomplete, stop at correction/rerun
- if `FAIL_CLOSED`, do not route into A2
- only if `SAFE_FOR_A2_REDUCTION`, continue with:
  - `a2-brain-refresh`
  - `a1-from-a2-distillation`
  - `a2-a1-memory-admission-guard`
  - `brain-delta-consolidation`

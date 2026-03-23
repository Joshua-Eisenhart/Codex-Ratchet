# EXTERNAL_RETURN_AUDIT_AND_INGEST_PACKET__ENTROPY_CARNOT_SZILARD__2026_03_10__v1

Status: DRAFT / NONCANON / A2 CONTROL NOTE
Date: 2026-03-10
Role: single return-side audit and ingest packet for the first external entropy / Carnot / Szilard monitored lane

## 1) Expected return set

The external thread return is only complete if all of these are present:
- `SOURCE_AND_METHOD_MAP.out.md`
- `MATH_ASSUMPTION_AND_RETOOL_MAP.out.md`
- `RATCHET_FUEL_SELECTION_MATRIX.out.md`
- `PRO_THREAD_BOOT_AND_QUERY_PLAN.out.md`
- `INSTANT_AUDIT_BRIEF.out.md`
- `QUALITY_GATE_REPORT.out.md`
- `PORTABLE_OUTPUT_CONTRACT_AND_FAIL_CLOSED_VALIDATION.out.md`

If one or more are missing:
- classify the return as incomplete
- hold for correction or rerun
- do not ingest into A2

## 2) Audit order

Use this exact order:

1. `pro-return-instant-audit`
2. `external-research-return-ingest`
3. if audit passes:
   - `a2-brain-refresh`
   - `a1-from-a2-distillation`
   - `a2-a1-memory-admission-guard`
   - `brain-delta-consolidation`

If the thread itself drifted or overran before producing a clean return:
- `thread-closeout-auditor`
- `closeout-result-ingest`

## 3) Pass/fail criteria

The return must be held at audit unless it preserves all of these:
- disagreement between entropy forms
- disagreement between engine interpretations
- process flow separated from mathematical primitives
- mathematical primitives separated from ontology/worldview claims
- explicit `usable now` / `usable after retool` / `reject / quarantine` split
- concrete citations or source locators

Hard fail conditions:
- smoothing disagreement into a single theory line
- converting retool-only lines into usable-now
- missing citations/source locators
- process-vs-math collapse
- major omitted adjacent lines
- elegant recap that does not satisfy the required output contract

## 4) Controller audit result classes

Use exactly one:
- `PASS`
- `PASS_WITH_CAUTIONS`
- `FAIL_CLOSED`

And exactly one routing decision:
- `SAFE_FOR_A2_REDUCTION`
- `HOLD_FOR_CORRECTION`
- `RERUN_WITH_NARROWER_OR_CORRECTED_BOOT`

## 5) Exact bounded audit packet to request or produce

The audit result should be compressed to:
- `completeness`
- `audit_result`
- `routing_decision`
- `strongest_keepers`
- `missing_or_blurred_lines`
- `hard_fail_flags`
- `next_controller_step`

Keep it controller-grade and short.

## 6) First A2 reduction target if safe

If the routing decision is `SAFE_FOR_A2_REDUCTION`, reduce the return into exactly these bounded A2 surfaces:
- entropy-family distinctions worth keeping active
- engine-family residue classes
- retool-eligible method families
- quarantine classes that must stay out of direct promotion

Do not convert the external return into broad doctrine.

## 7) First A1 impact target if safe

If the A2 reduction succeeds, the first A1 impact should stay proposal-only and bounded to:
- entropy-family branch planning
- Carnot / Szilard / demon residue transforms
- negative-SIM hooks
- external-fuel follow-on priorities

Do not create doctrine-head families directly from the raw external return.

## 8) Exact audit/ingest copy-paste prompt

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

## 9) Controller stop point

This packet is the only return-side owner surface needed for the first external monitored lane.

After the external return arrives, use this packet first.
Do not improvise a broader audit flow before checking against this file.

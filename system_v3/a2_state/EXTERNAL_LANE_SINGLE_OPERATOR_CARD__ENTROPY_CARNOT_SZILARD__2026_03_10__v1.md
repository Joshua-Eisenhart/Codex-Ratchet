# EXTERNAL_LANE_SINGLE_OPERATOR_CARD__ENTROPY_CARNOT_SZILARD__2026_03_10__v1

Status: DRAFT / NONCANON / A2 CONTROL NOTE
Date: 2026-03-10
Role: single operator card for launching and auditing the external entropy / Carnot / Szilard lane

## 1) Required attachment

Attach only:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/to_send_to_pro/jobs/PRO_BOOT_JOB__ZIP_JOB__EXTERNAL_RESEARCH_RETOOL_REFINERY__ENTROPY_CARNOT_SZILARD_ENGINE_FAMILIES__CHATUI_DROPIN__v1__20260309_204341Z.zip`

Do not attach:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/to_send_to_pro/jobs/PRO_BOOT_JOB__ZIP_JOB__EXTERNAL_RESEARCH_RETOOL_REFINERY__ENTROPY_CARNOT_SZILARD_ENGINE_FAMILIES__CHATUI_DROPIN__v1__20260309_204020Z.zip`

## 2) Launch message

```text
Use only the attached boot zip and the job's internal task contracts.

Produce every required output file with exact file fences.
Preserve disagreements.
Keep citations/source locators.
Separate:
- process flow
- mathematical primitives
- ontology/worldview assumptions

Explicitly classify every major line as:
- usable now
- usable after retool
- reject / quarantine

Do not smooth.
Fail closed if a required file or citation-backed section is missing.

Return the full bounded output set:
- SOURCE_AND_METHOD_MAP.out.md
- MATH_ASSUMPTION_AND_RETOOL_MAP.out.md
- RATCHET_FUEL_SELECTION_MATRIX.out.md
- PRO_THREAD_BOOT_AND_QUERY_PLAN.out.md
- INSTANT_AUDIT_BRIEF.out.md
- QUALITY_GATE_REPORT.out.md
- PORTABLE_OUTPUT_CONTRACT_AND_FAIL_CLOSED_VALIDATION.out.md
```

## 3) Wait condition

Wait for the full bounded return set.
Do not ingest to A2 on receipt alone.

## 4) Return audit message

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

## 5) Routing rule

- `PASS` or `PASS_WITH_CAUTIONS` plus `SAFE_FOR_A2_REDUCTION`:
  - proceed to bounded A2 reduction
- `INCOMPLETE`, `FAIL_CLOSED`, or `HOLD_FOR_CORRECTION`:
  - do not ingest
- `RERUN_WITH_NARROWER_OR_CORRECTED_BOOT`:
  - correct the lane rather than broadening it

## 6) Stop condition

This card is the final local prep surface for this lane.
After this, the next meaningful state change is external execution or return audit.

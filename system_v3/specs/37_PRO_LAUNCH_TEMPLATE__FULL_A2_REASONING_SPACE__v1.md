# PRO_LAUNCH_TEMPLATE__FULL_A2_REASONING_SPACE__v1
Status: DRAFT / NONCANON / ACTIVE OPERATOR TEMPLATE
Date: 2026-03-11
Owner: current `A2` controller for exploratory high-context external reasoning lanes

## Purpose

This template is the current launch contract for:
- `PRO_THREAD_CLASS = FULL_A2_REASONING_SPACE`
- `BOOT_LEVEL = PRO_BOOT_LEVEL_4__FULL_A2_REASONING_SPACE`

Use it when the external thread is intentionally a high-context exploratory reasoning space.

## Use conditions

Use this template only when:
- the task is synthetic, retooling-heavy, philosophy-heavy, or difficult to scope narrowly
- a narrow source worker would be too context-starved
- the output is being treated as exploratory fuel, not authority

Examples:
- broad retooling across multiple external systems
- theory-alignment exploration against current project structure
- system-aware external synthesis that still returns through audit

## Required launch declaration

Every launch built from this template must include:
- `PRO_THREAD_CLASS: FULL_A2_REASONING_SPACE`
- `BOOT_LEVEL: PRO_BOOT_LEVEL_4__FULL_A2_REASONING_SPACE`
- `ROLE: EXPLORATORY_A2_STYLE_REASONING`
- `BOUNDED_SCOPE`
- `RETURN_CONTRACT`
- `AUDIT_MODE: Thinking/Heavy`

## Required context rule

The issued ZIP may include:
- large `A2` slices
- broad `system_v3` process law
- selected execution-state/control surfaces
- selected source packets

But it must still stay bounded to one declared reasoning problem.

## Exact launch prompt skeleton

```text
Use only the attached boot zip and the files inside it.

PRO_THREAD_CLASS: FULL_A2_REASONING_SPACE
BOOT_LEVEL: PRO_BOOT_LEVEL_4__FULL_A2_REASONING_SPACE
ROLE: EXPLORATORY_A2_STYLE_REASONING

Before doing any real work, do this exact preflight:
1. verify that you can open and read the attached zip
2. if not, stop immediately and return:
   ATTACHMENT_ACCESS_FAIL
   reason: <one short reason>
   retry_same_upload_likely_to_help: YES or NO
3. if yes, return:
   ZIP_ACCESS_OK
   top_level_files:
   - <file 1>
   - <file 2>
   - <file 3>
   - ...

Only continue if the zip is readable.

This is an exploratory high-context reasoning pass.
Treat all output as non-authoritative exploratory fuel unless later audit and reduction preserve it.

Task:
- work through the bounded reasoning problem using only the attached context
- preserve disagreements
- keep distinctions between process flow, mathematical primitives, and ontology/worldview assumptions
- explicitly mark:
  - usable now
  - usable after retool
  - reject / quarantine
- do not smooth conflicts into one narrative
- do not claim canon or lower-loop truth

Required outputs:
- SOURCE_AND_METHOD_MAP.out.md
- MATH_ASSUMPTION_AND_RETOOL_MAP.out.md
- RATCHET_FUEL_SELECTION_MATRIX.out.md
- PRO_THREAD_BOOT_AND_QUERY_PLAN.out.md
- INSTANT_AUDIT_BRIEF.out.md
- QUALITY_GATE_REPORT.out.md
- PORTABLE_OUTPUT_CONTRACT_AND_FAIL_CLOSED_VALIDATION.out.md

Additional expectation:
- make it explicit which parts are exploratory synthesis versus source-bearing support

After creating the files:
1. rebundle them into one zip
2. provide the downloadable zip
3. list the filenames included in that returned zip
```

## Stop rule

Stop when:
- attachment preflight fails, or
- one rebundled exploratory return zip is produced

Do not start second-wave refinement inside the same thread.

## Audit expectation

Audit must check:
- exploratory vs source-bearing separation
- overreach into authority
- ontology smuggling
- whether later A2 reduction is even admissible

## Immediate implication

Current gap closed by this note:
- there is now a runnable launch template for the high-context exploratory `Pro` class you described as a controlled hallucination space

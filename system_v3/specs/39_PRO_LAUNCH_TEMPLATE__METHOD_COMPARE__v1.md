# PRO_LAUNCH_TEMPLATE__METHOD_COMPARE__v1
Status: DRAFT / NONCANON / ACTIVE OPERATOR TEMPLATE
Date: 2026-03-11
Owner: current `A2` controller for bounded external method-compare `Pro` threads

## Purpose

This template is the current launch contract for:
- `PRO_THREAD_CLASS = METHOD_COMPARE_WORKER`
- `BOOT_LEVEL = PRO_BOOT_LEVEL_2__METHOD_COMPARE`

Use it when one `Pro` thread is meant to compare a small adjacent method/lab/thinker set against one bounded question.

## Use conditions

Use this template only when:
- the question is comparative rather than purely source-acquisition
- the packet set is smaller than a lane-refinery bundle
- the task is more than one packet but less than a broad exploratory `A2` reasoning space

Examples:
- AlphaGeometry vs adjacent search-control method comparison
- solver vs model-check vs fuzz method comparison
- one bounded Friston/FEP method comparison against one QIT-reconstruction line

## Required launch declaration

Every launch built from this template must include:
- `PRO_THREAD_CLASS: METHOD_COMPARE_WORKER`
- `BOOT_LEVEL: PRO_BOOT_LEVEL_2__METHOD_COMPARE`
- `ROLE: COMPARATIVE_METHOD_SCOUTING`
- `BOUNDED_SCOPE`
- `RETURN_CONTRACT`
- `AUDIT_MODE: Thinking/Heavy`

## Required attachment

The issued ZIP should include:
- the selected small packet family set under `sources/`
- bounded comparison `input/`
- comparison `tasks/`
- comparison `templates/`
- `meta/`

It may include:
- selected `MODEL_CONTEXT` or `INTENT_SUMMARY` slices
- bounded current `A2` comparison criteria

It should not include:
- broad whole-system context
- unrelated packet families
- unrelated run/runtime surfaces

## Exact launch prompt skeleton

```text
Use only the attached boot zip and the files inside it.

PRO_THREAD_CLASS: METHOD_COMPARE_WORKER
BOOT_LEVEL: PRO_BOOT_LEVEL_2__METHOD_COMPARE
ROLE: COMPARATIVE_METHOD_SCOUTING

Before doing any real work, do this exact preflight:
1. verify that you can actually open and read the attached zip
2. if you cannot open and read the zip, stop immediately and return exactly:
   ATTACHMENT_ACCESS_FAIL
   reason: <one short reason>
   retry_same_upload_likely_to_help: YES or NO
3. if you can read the zip, first return:
   ZIP_ACCESS_OK
   top_level_files:
   - <file 1>
   - <file 2>
   - <file 3>
   - ...

Only continue if the zip is actually readable.

Use only the selected bounded packet set and comparison criteria carried in the zip.
Preserve distinctions between compared methods, labs, or thinkers.
Do not smooth them into one method family.
Do not treat overlay-only residue as source-bearing completion.

Task:
- compare the bounded method/lab/thinker set using only the attached packet set
- preserve disagreements
- keep citations and source locators
- separate:
  - process flow
  - mathematical primitives
  - ontology/worldview assumptions
- classify every major line as:
  - usable now
  - usable after retool
  - reject / quarantine
- make distinctions and incompatibilities explicit
- do not invent missing source material

Required output files:
- SOURCE_AND_METHOD_MAP.out.md
- MATH_ASSUMPTION_AND_RETOOL_MAP.out.md
- RATCHET_FUEL_SELECTION_MATRIX.out.md
- PRO_THREAD_BOOT_AND_QUERY_PLAN.out.md
- INSTANT_AUDIT_BRIEF.out.md
- QUALITY_GATE_REPORT.out.md
- PORTABLE_OUTPUT_CONTRACT_AND_FAIL_CLOSED_VALIDATION.out.md

After creating the files:
1. rebundle them into one zip
2. provide the downloadable zip
3. list the filenames included in that returned zip
```

## Stop rule

Stop when:
- attachment preflight fails, or
- one rebundled bounded return zip is produced

Do not widen into lane-refinery scope or full-system exploratory reasoning inside the same thread.

## Audit expectation

Audit must check:
- distinction preservation
- citation quality
- overclaim
- method smoothing
- thinker/lab authority inflation
- whether the comparison stayed bounded

## Immediate implication

Current gap closed by this note:
- the fourth missing `Pro` launch class now has a concrete runnable template

# PRO_LAUNCH_TEMPLATE__LANE_REFINERY__v1
Status: DRAFT / NONCANON / ACTIVE OPERATOR TEMPLATE
Date: 2026-03-11
Owner: current `A2` controller for bounded external lane-refinery `Pro` threads

## Purpose

This template is the current launch contract for:
- `PRO_THREAD_CLASS = LANE_REFINERY_WORKER`
- `BOOT_LEVEL = PRO_BOOT_LEVEL_3__LANE_REFINERY`

Use it when one `Pro` thread is meant to work a bounded external lane spanning multiple related packet families.

## Use conditions

Use this template only when:
- the lane has multiple related packet families
- one bounded external question spans those families
- the task is more than a narrow source packet
- the task is less than a full-context exploratory A2 reasoning space

Examples:
- entropy / Carnot / Szilard / Maxwell lane
- QIT reconstruction + FEP + method-bridge lane

## Required launch declaration

Every launch built from this template must include:
- `PRO_THREAD_CLASS: LANE_REFINERY_WORKER`
- `BOOT_LEVEL: PRO_BOOT_LEVEL_3__LANE_REFINERY`
- `ROLE: LANE_LEVEL_FUEL_PRODUCTION`
- `BOUNDED_SCOPE`
- `RETURN_CONTRACT`
- `AUDIT_MODE: Thinking/Heavy`

## Required attachment

The issued ZIP should include:
- multiple packet families under `sources/`
- bounded lane `input/`
- lane-level `tasks/`
- lane-level `templates/`
- `meta/`

It may include selected current `A2` framing and selected execution-state notes.

It should not include:
- broad unrelated whole-system context
- unrelated run/runtime surfaces
- free ambient project mass

## Exact launch prompt skeleton

```text
Use only the attached boot zip and the files inside it.

PRO_THREAD_CLASS: LANE_REFINERY_WORKER
BOOT_LEVEL: PRO_BOOT_LEVEL_3__LANE_REFINERY
ROLE: LANE_LEVEL_FUEL_PRODUCTION

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

Use the bundled lane packet families first.
Treat scaffold-only packet families and local residue seed maps as support structure, not as source-bearing completion.

Task:
- work the bounded external lane using only the attached lane packet set
- preserve disagreements between packet families
- keep citations and source locators
- separate:
  - process flow
  - mathematical primitives
  - ontology/worldview assumptions
- classify every major line as:
  - usable now
  - usable after retool
  - reject / quarantine
- make the source-bearing vs scaffold-only split explicit
- do not smooth
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

Do not expand into full-system exploratory work inside the same thread.

## Audit expectation

Audit must check:
- source-bearing vs scaffold-only split
- citation quality
- overclaim
- thinker/lab authority inflation
- whether later A2 reduction is admissible

## Immediate implication

Current gap closed by this note:
- the most common current external lane class now has a concrete runnable launch template

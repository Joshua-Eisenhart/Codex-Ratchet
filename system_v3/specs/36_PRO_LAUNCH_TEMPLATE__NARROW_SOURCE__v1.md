# PRO_LAUNCH_TEMPLATE__NARROW_SOURCE__v1
Status: DRAFT / NONCANON / ACTIVE OPERATOR TEMPLATE
Date: 2026-03-11
Owner: current `A2` controller for narrow source-bearing external acquisition threads

## Purpose

This template is the current launch contract for:
- `PRO_THREAD_CLASS = NARROW_SOURCE_WORKER`
- `BOOT_LEVEL = PRO_BOOT_LEVEL_1__NARROW_SOURCE`

Use it when one `Pro` thread is being asked to work on one source family only.

## Use conditions

Use this template only when:
- one packet family is the actual target
- one bounded source family is enough
- no broad system-aware reasoning is needed

Examples:
- `carnot_primary`
- `maxwell_demon_primary`
- `qit_reconstruction_primary`

## Required launch declaration

Every launch built from this template must include:
- `PRO_THREAD_CLASS: NARROW_SOURCE_WORKER`
- `BOOT_LEVEL: PRO_BOOT_LEVEL_1__NARROW_SOURCE`
- `ROLE: SOURCE_ACQUISITION_AND_EXTRACTION`
- `BOUNDED_SCOPE`
- `RETURN_CONTRACT`
- `AUDIT_MODE: Thinking/Heavy`

## Required attachment

The issued ZIP must include at minimum:
- `sources/external/<target packet>/`
- `input/`
- `tasks/`
- `templates/`
- `meta/`

It should not include broad whole-system context by default.

## Exact launch prompt skeleton

```text
Use only the attached boot zip and the files inside it.

PRO_THREAD_CLASS: NARROW_SOURCE_WORKER
BOOT_LEVEL: PRO_BOOT_LEVEL_1__NARROW_SOURCE
ROLE: SOURCE_ACQUISITION_AND_EXTRACTION

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

Use only the one bounded target packet and the files it points to.
Do not expand into broader thinker/lab comparison.
Do not treat local residue seed maps as source-bearing authority.

Task:
- acquire, classify, and extract the bounded source family named in the packet
- preserve disagreements
- keep citations and source locators
- separate process flow, mathematical primitives, and ontology/worldview assumptions
- classify every major line as:
  - usable now
  - usable after retool
  - reject / quarantine

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

Do not continue to second-wave comparison inside the same thread.

## Audit expectation

Audit must check:
- source-bearing coverage vs scaffold-only coverage
- citation quality
- overclaim
- whether the packet stayed narrow

## Immediate implication

Current gap closed by this note:
- there is now a runnable launch template for the narrowest valid `Pro` class

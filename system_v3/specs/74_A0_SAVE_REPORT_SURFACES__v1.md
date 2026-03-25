# A0_SAVE_REPORT_SURFACES__v1
Status: DRAFT / NONCANON / REPAIR TARGET
Date: 2026-03-14
Owner: `A0` save/report tooling recovery

## Purpose

This spec restores the missing deterministic A0 save/report surface family that used to live closer to old `Thread S`.

It exists because the current system has:
- ZIP/save/tape spine
- compile/report spine

but weaker first-class operator/report surfaces for:
- semantic project saves
- semantic save auditing
- export linting
- tape summaries
- term-chain analysis
- instrumentation/forensics

Legacy witness surface:
- `/home/ratchet/Desktop/Codex Ratchet/core_docs/BOOTPACKS/BOOTPACK_THREAD_S_v1.64.md`

Current normative anchors:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/04_A0_COMPILER_SPEC.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/16_ZIP_SAVE_AND_TAPES_SPEC.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/08_PIPELINE_AND_STATE_FLOW_SPEC.md`

## Core rule

These surfaces are deterministic A0/operator artifacts.

They are:
- not B input
- not canon by themselves
- not freeform notes

They are audit/replay/save/control surfaces.

## Required surface family

### 1. `PROJECT_SAVE_DOC v1`

Purpose:
- one semantic save document describing a restorable save state

Minimum contents:
- save level
- required member inventory
- source pointers
- integrity witness references
- restore-sufficiency judgment

### 2. `AUDIT_PROJECT_SAVE_DOC_REPORT v1`

Purpose:
- pass/fail structural audit of a `PROJECT_SAVE_DOC`

Minimum checks:
- required sections present
- no placeholder fuel
- restore sufficiency explicit
- member list internally consistent

### 3. `EXPORT_BLOCK_LINT_REPORT v1`

Purpose:
- structural preflight scan against known kernel fences before B submission

Minimum checks:
- ascii/glyph checks
- undefined-term heuristic
- derived-only heuristic
- duplicate item ids

### 4. `TAPE_SUMMARY_REPORT v1`

Purpose:
- deterministic summary of `EXPORT_TAPE` and/or `CAMPAIGN_TAPE`

Minimum contents:
- counts
- first/last entries
- branch coverage
- missing-pair anomalies

### 5. `TERM_CHAIN_REPORT v1`

Purpose:
- decompose compound/sentence terms into segments and dependency chain witness

Minimum contents:
- compound literal
- segments
- known/unknown segment status
- source pointers

### 6. `INSTRUMENTATION_REPORT v1`

Purpose:
- deterministic process-health report over save/tape/compile surfaces

Minimum contents:
- counts
- duplicate pressure
- unresolved/unknown counts
- drift warnings

## Optional later surface family

Later but valid:
- `REJECT_HISTOGRAM`
- `RULE_HIT_REPORT`
- `FORENSIC_TREND_REPORT`
- `CHANGELOG`
- `FEED_LOG`

These are useful, but secondary to the six required surfaces above.

## Build law

1. `DETERMINISTIC_ORDER`
- outputs must be deterministically ordered

2. `SOURCE_POINTER_REQUIRED`
- each reported finding or entry must cite source pointers or explicitly say `provided text`

3. `NO_INFERENCE_BEYOND_SURFACE`
- if a required source section is missing, return explicit failure or `UNKNOWN`

4. `ONE_REPORT_ONE_CONTAINER`
- each tool invocation produces one deterministic report/container

## Tooling targets

Primary expected tools:
- `build_project_save_doc.py`
- `audit_project_save_doc.py`
- `build_export_block_lint_report.py`
- `build_tape_summary_report.py`
- `build_term_chain_report.py`
- `build_instrumentation_report.py`

Likely neighbors:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_save_profile_zip.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_replay_pair_gate.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_a0_compile_gate.py`

## Acceptance criteria

This spec is satisfied only when:
- the six required surfaces exist as actual executable tools or validators
- each has deterministic inputs/outputs
- the current system no longer relies on old bootpack text alone to describe them

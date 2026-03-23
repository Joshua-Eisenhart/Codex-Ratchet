# SKILL_STACK_APPLICATION__ENTROPY_CARNOT_SZILARD_EXTERNAL_LANE__v1

Status: DRAFT / NONCANON / A2 CONTROL NOTE
Date: 2026-03-10
Role: apply the newly installed skill stack to one real external-research refinery lane

## 1) Chosen lane

Use the existing entropy / Carnot / Szilard external-research dropin:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/zip_dropins/ZIP_JOB__EXTERNAL_RESEARCH_RETOOL_REFINERY__ENTROPY_CARNOT_SZILARD_ENGINE_FAMILIES__CHATUI_DROPIN__v1`

Existing built job zip:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/zip_dropins/builds/ZIP_JOB__EXTERNAL_RESEARCH_RETOOL_REFINERY__ENTROPY_CARNOT_SZILARD_ENGINE_FAMILIES__CHATUI_DROPIN__v1.zip`

Existing narrow boot outputs:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/to_send_to_pro/jobs/PRO_BOOT_JOB__ZIP_JOB__EXTERNAL_RESEARCH_RETOOL_REFINERY__ENTROPY_CARNOT_SZILARD_ENGINE_FAMILIES__CHATUI_DROPIN__v1__20260309_204020Z.zip.sha256`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/to_send_to_pro/jobs/PRO_BOOT_JOB__ZIP_JOB__EXTERNAL_RESEARCH_RETOOL_REFINERY__ENTROPY_CARNOT_SZILARD_ENGINE_FAMILIES__CHATUI_DROPIN__v1__20260309_204341Z.zip.sha256`

## 2) Skill order

Apply the new skills in this exact order:

1. `external-research-refinery-launcher`
2. `pro-return-instant-audit`
3. `a2-brain-refresh`
4. `a1-from-a2-distillation`
5. `a2-a1-memory-admission-guard`
6. `brain-delta-consolidation`

`thread-closeout-auditor` is only needed if the external worker thread runs too long.

## 3) Launcher-side exact inputs

Topic brief:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/zip_dropins/ZIP_JOB__EXTERNAL_RESEARCH_RETOOL_REFINERY__ENTROPY_CARNOT_SZILARD_ENGINE_FAMILIES__CHATUI_DROPIN__v1/input/RESEARCH_TOPIC_BRIEF.md`

Seed notes:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/zip_dropins/ZIP_JOB__EXTERNAL_RESEARCH_RETOOL_REFINERY__ENTROPY_CARNOT_SZILARD_ENGINE_FAMILIES__CHATUI_DROPIN__v1/input/RESEARCH_SEED_NOTES.md`

Key required outputs inside the job:
- source-and-method map
- math-assumption / retool map
- ratchet-fuel selection matrix
- Pro-thread boot and query plan
- instant-audit brief
- quality gate report

## 4) Narrow-boot command

Use the existing narrow boot pattern:

```text
python3 system_v3/tools/build_pro_boot_job_zip.py \
  --profile bootstrap \
  --repo-root . \
  --job-zip work/zip_dropins/builds/ZIP_JOB__EXTERNAL_RESEARCH_RETOOL_REFINERY__ENTROPY_CARNOT_SZILARD_ENGINE_FAMILIES__CHATUI_DROPIN__v1.zip \
  --no-default-system-save \
  --include-relpath system_v3/specs/07_A2_OPERATIONS_SPEC.md \
  --include-relpath system_v3/specs/16_ZIP_SAVE_AND_TAPES_SPEC.md \
  --include-relpath system_v3/specs/27_MASTER_CONTROLLER_THREAD_PROCESS__v1.md \
  --include-relpath system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md \
  --include-relpath system_v3/a2_state/INTENT_SUMMARY.md \
  --include-relpath system_v3/a2_state/MODEL_CONTEXT.md \
  --include-relpath system_v3/a2_state/OPEN_UNRESOLVED__v1.md \
  --include-relpath work/zip_subagents/ZIP_JOB__SUBAGENT_BUNDLE_PROTOCOL_v1.md \
  --include-relpath work/zip_subagents/ZIP_JOB__VARIANT__EXTERNAL_RESEARCH_RETOOL_REFINERY_v1.md \
  --include-relpath work/zip_subagents/EXTERNAL_RESEARCH_CONTROLLER_BOOT_RECIPE__v1.md
```

## 5) Minimal send text

Use the existing minimal send surface:

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
```

## 6) Return-audit contract

When the Pro/deep-research return arrives, the audit skill should check:
- citation quality
- overclaim
- ontology smuggling
- process-vs-math confusion
- missing adjacent lines
- whether the return actually produced the explicit:
  - `usable now`
  - `usable after retool`
  - `reject / quarantine`
  split

If weak:
- hold for correction
- or rerun with narrower boot / follow-on pass

Do not ingest directly into A2.

## 7) A2 / A1 follow-on

Only after the return passes instant audit:

1. `a2-brain-refresh`
   - emit bounded A2 update notes for:
     - entropy-family distinctions
     - engine-family residue classes
     - thinker/lab method fuel
     - usable-now vs after-retool splits

2. `a1-from-a2-distillation`
   - derive proposal-only impacts for:
     - entropy-family branch planning
     - Carnot / Szilard / demon residue transforms
     - negative-SIM hooks
     - external-fuel follow-on priorities

3. `a2-a1-memory-admission-guard`
   - gate all candidate writes into active A2/A1 surfaces

4. `brain-delta-consolidation`
   - compress the audited return into:
     - `A2_UPDATE_DELTA`
     - `A1_IMPACT_DELTA`
     - `UNRESOLVED_TENSIONS`
     - `HOLD_OR_REVISIT`

## 8) Why this lane first

This is the cleanest first live application because:
- the topic brief already exists
- the dropin already exists
- the narrow boot already exists
- the topic is already listed as the first external refinery lane in the next-batch plan
- it directly exercises the new external research + A2/A1 consolidation stack

## 9) Current controller judgment

This lane is ready to run as soon as an external Pro/deep-research thread is assigned to the boot zip.

The remaining blocker is not system design.
It is only the actual execution and return capture of the external thread.

---
name: external-research-refinery-launcher
description: Build and launch bounded external research refinery jobs for the Codex Ratchet system. Use when a topic like entropy families, Carnot/Szilard engines, FEP, thinker/lab method surveys, or AlphaGeometry-style method mining needs a ZIP-job pack, a narrow Pro boot, and a controller-grade query plan.
---

# External Research Refinery Launcher

Use this skill when a bounded external research lane needs to be launched through the ZIP-job system.

## Core rules

- Keep the boot narrow.
- External research outputs remain upper-layer refinery artifacts until reduced into A2.
- Separate process flow, mathematical primitives, and ontology/worldview in the launched task.
- Require explicit `usable now / usable after retool / reject` discipline.
- Do not widen a topic pack into a whole-system literature survey.

## Owner surfaces

- `work/zip_subagents/ZIP_JOB__VARIANT__EXTERNAL_RESEARCH_RETOOL_REFINERY_v1.md`
- `work/zip_subagents/EXTERNAL_RESEARCH_CONTROLLER_BOOT_RECIPE__v1.md`
- `work/zip_subagents/ZIP_JOB__SUBAGENT_BUNDLE_PROTOCOL_v1.md`
- `work/zip_job_templates/EXTERNAL_RESEARCH_RETOOL_REFINERY__BUNDLE_TEMPLATE_v1/meta/README.md`

## Template task contracts

- `tasks/01_TASK__SOURCE_AND_METHOD_MAP.task.md`
- `tasks/02_TASK__MATH_ASSUMPTION_AND_RETOOL_MAP.task.md`
- `tasks/03_TASK__RATCHET_FUEL_SELECTION_MATRIX.task.md`
- `tasks/04_TASK__PRO_THREAD_BOOT_AND_QUERY_PLAN.task.md`
- `tasks/05_TASK__INSTANT_AUDIT_BRIEF.task.md`
- `tasks/06_TASK__QUALITY_GATE__CITATIONS_AND_NO_SMOOTHING.task.md`

## Workflow

1. Pick one bounded topic lane only.
2. Fill:
   - `input/RESEARCH_TOPIC_BRIEF.md`
   - `input/RESEARCH_SEED_NOTES.md`
3. Confirm the pack will require:
   - one source-and-method map
   - one math-assumption/retool map
   - one ratchet-fuel selection matrix
   - one Pro-thread boot and query plan
   - one instant-audit brief
   - one quality gate report
4. Build the narrow boot using:
   - `python3 system_v3/tools/build_pro_boot_job_zip.py`
   - `--no-default-system-save`
   - explicit `--include-relpath` owner docs
5. Emit:
   - exact built job/dropin path
   - exact boot zip path
   - exact send/query text or follow-on boot plan
6. Hand the return to `pro-return-instant-audit`.

## Guardrails

- Do not include broad `system_v3/runs/`, `archive/`, `work/curated_zips/`, or transient mirrors by default.
- Do not launch without a concrete topic brief.
- Do not treat the returned research pack as doctrine.
- If the topic is too broad, split it before launch.

---
name: pro-return-instant-audit
description: Audit returned Pro or deep-research refinery outputs for the Codex Ratchet system. Use when a bounded external research pack has come back and the result needs fast controller-grade checking for citations, overclaim, ontology smuggling, process-vs-math confusion, omissions, and usable-now versus after-retool routing.
---

# Pro Return Instant Audit

Use this skill when an external research return exists and needs bounded audit before A2 ingestion.

## Core rules

- Returned research is not doctrine.
- Audit before A2 ingestion.
- Preserve disagreements and gaps; do not smooth them away.
- Keep process flow, mathematical primitives, and ontology/worldview separated.
- Force the `usable now / usable after retool / reject` split if the return blurred it.

## Owner surfaces

- `work/zip_subagents/ZIP_JOB__VARIANT__EXTERNAL_RESEARCH_RETOOL_REFINERY_v1.md`
- `work/zip_subagents/EXTERNAL_RESEARCH_CONTROLLER_BOOT_RECIPE__v1.md`
- `work/zip_job_templates/EXTERNAL_RESEARCH_RETOOL_REFINERY__BUNDLE_TEMPLATE_v1/tasks/05_TASK__INSTANT_AUDIT_BRIEF.task.md`
- `work/zip_job_templates/EXTERNAL_RESEARCH_RETOOL_REFINERY__BUNDLE_TEMPLATE_v1/tasks/06_TASK__QUALITY_GATE__CITATIONS_AND_NO_SMOOTHING.task.md`

## Audit targets

- citation quality
- overclaim
- ontology smuggling
- process-vs-math confusion
- major omitted adjacent lines
- missing or blurred `usable now / usable after retool / reject` split

## Workflow

1. Read the returned output set and the original topic brief.
2. Check whether the return actually produced:
   - source-and-method map
   - math-assumption/retool map
   - ratchet-fuel selection matrix
   - Pro-thread boot/query plan
   - instant-audit brief
   - quality gate report
3. Audit the content against the target categories above.
4. Emit one bounded audit result:
   - pass
   - pass with cautions
   - fail closed
5. Produce a short controller routing note:
   - safe for A2 reduction
   - hold for correction
   - rerun Pro with narrower or corrected boot

## Guardrails

- Do not promote the returned pack into active doctrine.
- Do not accept citation-free synthesis as if it were source-linked research.
- Do not let elegant summaries hide omitted major adjacent lines.
- If the return merged process and math into one bucket, flag it directly.
- If the return is weak, recommend correction or rerun, not smoothing.

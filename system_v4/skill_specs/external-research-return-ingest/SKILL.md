---
name: external-research-return-ingest
description: Normalize and route returned Pro or deep-research refinery packs for the Codex Ratchet system. Use when an external research lane has produced its output files and the return needs to be checked for completeness, handed through instant audit, and then routed into A2/A1 follow-on work without being treated as doctrine.
---

# External Research Return Ingest

Use this skill when a bounded external research lane has returned a completed or partial output set.

## Core rules

- Returned external research is refinery artifact, not doctrine.
- Do not bypass `pro-return-instant-audit`.
- Do not ingest incomplete output sets silently.
- Keep the process/mathematics/ontology split explicit.
- Route only audited returns into A2/A1 follow-on work.

## Owner surfaces

- `system_v4/skill_specs/pro-return-instant-audit/SKILL.md`
- `system_v4/skill_specs/a2-brain-refresh/SKILL.md`
- `system_v4/skill_specs/a1-from-a2-distillation/SKILL.md`
- `system_v4/skill_specs/a2-a1-memory-admission-guard/SKILL.md`
- `system_v4/skill_specs/brain-delta-consolidation/SKILL.md`
- `system_v3/a2_state/SKILL_STACK_APPLICATION__ENTROPY_CARNOT_SZILARD_EXTERNAL_LANE__v1.md`

## Expected return set

For the external research refinery variant, the return should include:

- source-and-method map
- math-assumption / retool map
- ratchet-fuel selection matrix
- Pro-thread boot and query plan
- instant-audit brief
- quality gate report

## Workflow

1. Locate the returned output set in the job/dropin output tree.
2. Check whether all expected outputs exist.
3. If incomplete:
   - mark the return incomplete
   - route to correction or rerun
   - stop there
4. If complete:
   - hand the return to `pro-return-instant-audit`
5. If the audit fails:
   - hold for correction
   - or rerun with narrower boot / better prompt
6. If the audit passes:
   - route to `a2-brain-refresh`
   - then `a1-from-a2-distillation`
   - then `a2-a1-memory-admission-guard`
   - then `brain-delta-consolidation`
7. Report:
   - completeness
   - audit result
   - safe/not-safe for A2 reduction
   - next controller step

## Guardrails

- Do not treat presence of files as evidence of quality.
- Do not let elegant output templates mask weak citation quality.
- Do not route directly into active owner surfaces without audit and memory guard.
- If the return merged usable-now and after-retool lines, flag it before any ingestion.

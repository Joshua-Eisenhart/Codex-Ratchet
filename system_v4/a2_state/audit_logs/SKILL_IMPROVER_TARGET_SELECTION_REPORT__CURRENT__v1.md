# Skill Improver Target Selection Report

- generated_utc: `2026-03-21T13:04:22Z`
- status: `ok`
- cluster_id: `SKILL_CLUSTER::a2-skill-truth-maintenance`
- slice_id: `a2-skill-improver-target-selector-operator`
- target_skill_id: `skill-improver-operator`
- readiness_gate_status: `bounded_ready_for_first_target`
- candidate_count: `2`
- recommended_first_target_class: `native maintenance Python skill with dedicated smoke, codex spec, and audit-only/propose-only behavior`
- do_not_promote: `True`

## Recommended Target
- skill_id: `a2-skill-improver-readiness-operator`
- source_path: `system_v4/skills/a2_skill_improver_readiness_operator.py`
- smoke_path: `system_v4/skills/test_a2_skill_improver_readiness_operator_smoke.py`
- score: `12`

## Candidate Targets
- `a2-skill-improver-readiness-operator`: score=12; source=system_v4/skills/a2_skill_improver_readiness_operator.py; smoke=system_v4/skills/test_a2_skill_improver_readiness_operator_smoke.py
- `a2-brain-surface-refresher`: score=10; source=system_v4/skills/a2_brain_surface_refresher.py; smoke=system_v4/skills/test_a2_brain_surface_refresher_smoke.py

## Recommended Actions
- Keep this slice audit-only; do not mutate any skill from this selection report.
- If a first target is chosen, keep skill-improver-operator behind its explicit allowlist + approval-token gate.
- Use the recommended smoke path as the first bounded proof surface rather than widening to general repo mutation.

## Packet Summary
- target_ready_for_first_class: `True`
- recommended_target_skill_id: `a2-skill-improver-readiness-operator`

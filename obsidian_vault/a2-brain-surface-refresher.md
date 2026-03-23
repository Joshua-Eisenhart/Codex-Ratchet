---
id: "SKILL::a2-brain-surface-refresher"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-brain-surface-refresher
**Node ID:** `SKILL::a2-brain-surface-refresher`

## Description
Audit-mode A2 brain surface refresher

## Properties
- **skill_type**: maintenance
- **source_type**: operator_module
- **source_path**: system_v4/skills/a2_brain_surface_refresher.py
- **status**: active
- **applicable_layers**: ["A2_HIGH_INTAKE", "A2_MID_REFINEMENT"]
- **applicable_trust_zones**: ["A2_HIGH_INTAKE", "A2_MID_REFINEMENT"]
- **applicable_graphs**: ["runtime", "control", "a2_high_intake_graph_v1"]
- **inputs**: ["repo_root", "task_signal", "changed_paths", "changed_tools", "new_run_evidence", "pending_a1_work", "report_path", "markdown_path", "packet_path"]
- **outputs**: ["brain_surface_refresh_report", "brain_surface_refresh_packet"]
- **adapters**: {"codex": "system_v4/skill_specs/a2-brain-surface-refresher/SKILL.md", "shell": "system_v4/skills/a2_brain_surface_refresher.py", "dispatch_binding": "python_module"}
- **related_skills**: ["a2-brain-refresh", "a2-tracked-work-operator", "graph-capability-auditor", "runtime-context-snapshot"]

## Outward Relations
- **RELATED_TO** → [[a2-brain-refresh]]
- **RELATED_TO** → [[a2-tracked-work-operator]]
- **RELATED_TO** → [[graph-capability-auditor]]
- **RELATED_TO** → [[runtime-context-snapshot]]
- **SKILL_OPERATES_ON** → [[a2_canonical_schemas]]
- **SKILL_OPERATES_ON** → [[a2_thread_boot_nine_hard_rules]]
- **MEMBER_OF** → [[A2 Skill Truth Maintenance]]

## Inward Relations
- [[a2-workshop-analysis-gate-operator]] → **RELATED_TO**
- [[outer-session-ledger]] → **RELATED_TO**
- [[outside-control-shell-operator]] → **RELATED_TO**
- [[a2-skill-improver-readiness-operator]] → **RELATED_TO**
- [[a2-skill-improver-target-selector-operator]] → **RELATED_TO**
- [[a2-skill-improver-dry-run-operator]] → **RELATED_TO**
- [[a2-lev-builder-placement-audit-operator]] → **RELATED_TO**
- [[a2-lev-builder-formalization-proposal-operator]] → **RELATED_TO**
- [[a2-lev-builder-formalization-skeleton-operator]] → **RELATED_TO**
- [[a2-lev-builder-post-skeleton-readiness-operator]] → **RELATED_TO**
- [[a2-lev-builder-post-skeleton-follow-on-selector-operator]] → **RELATED_TO**
- [[a2-lev-builder-post-skeleton-disposition-audit-operator]] → **RELATED_TO**
- [[a2-lev-builder-post-skeleton-future-lane-existence-audit-operator]] → **RELATED_TO**
- [[a2-evermem-backend-reachability-audit-operator]] → **RELATED_TO**
- [[a2-lev-autodev-loop-audit-operator]] → **RELATED_TO**
- [[a2-lev-architecture-fitness-operator]] → **RELATED_TO**
- [[a2-skill-improver-second-target-admission-audit-operator]] → **RELATED_TO**
- [[a2-context-spec-workflow-follow-on-selector-operator]] → **RELATED_TO**
- [[a2-append-safe-context-shell-audit-operator]] → **RELATED_TO**
- [[a2-context-spec-workflow-post-shell-selector-operator]] → **RELATED_TO**

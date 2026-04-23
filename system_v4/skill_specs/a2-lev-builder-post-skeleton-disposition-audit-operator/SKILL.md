---
skill_id: a2-lev-builder-post-skeleton-disposition-audit-operator
name: a2-lev-builder-post-skeleton-disposition-audit-operator
description: Audit-only post-skeleton disposition operator that decides whether the selected lev-builder unresolved branch should stay open, hold, or retire without widening into runtime claims.
skill_type: maintenance
source_type: repo_skill
applicable_layers: [A2_MID_REFINEMENT, A2_LOW_CONTROL]
applicable_graphs: [runtime, control, a2_mid_refinement_graph_v1]
inputs:
  - repo_root
  - selector_report_path
  - selector_packet_path
  - readiness_report_path
  - report_json_path
  - report_md_path
  - packet_path
outputs:
  - lev_builder_post_skeleton_disposition_audit_report
  - lev_builder_post_skeleton_disposition_audit_packet
related_skills:
  - a2-lev-builder-post-skeleton-follow-on-selector-operator
  - a2-lev-builder-post-skeleton-readiness-operator
  - a2-brain-surface-refresher
capabilities:
  can_write_repo: false
  can_only_propose: true
  reads_graph: true
tool_dependencies: []
provenance: "bounded post-skeleton disposition audit retooled from the lev-builder selector and readiness sequence"
adapters:
  codex: system_v4/skill_specs/a2-lev-builder-post-skeleton-disposition-audit-operator/SKILL.md
  shell: system_v4/skills/a2_lev_builder_post_skeleton_disposition_audit_operator.py
---

# A2 lev-builder Post-Skeleton Disposition Audit Operator

Use this skill when the selector has already chosen the unresolved post-skeleton
branch and we need one bounded answer about whether that branch should remain
open, hold, or retire.

## Purpose

- read the landed selector and readiness surfaces
- decide only whether the unresolved branch should stay open, hold, or retire
- emit one bounded report and one compact packet
- keep the output clearly non-migratory and non-runtime-live

## Execute Now

1. Read:
   - [A2_LEV_BUILDER_POST_SKELETON_FOLLOW_ON_SELECTOR_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_LEV_BUILDER_POST_SKELETON_FOLLOW_ON_SELECTOR_REPORT__CURRENT__v1.json)
   - [A2_LEV_BUILDER_POST_SKELETON_FOLLOW_ON_SELECTOR_PACKET__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_LEV_BUILDER_POST_SKELETON_FOLLOW_ON_SELECTOR_PACKET__CURRENT__v1.json)
   - [A2_LEV_BUILDER_POST_SKELETON_READINESS_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_LEV_BUILDER_POST_SKELETON_READINESS_REPORT__CURRENT__v1.json)
   - [lev-builder](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/lev-builder/SKILL.md)
   - [arch](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/arch/SKILL.md)
   - [work](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/work/SKILL.md)
2. Decide only whether the selected unresolved branch should remain open, hold, or retire.
3. Emit one report and one packet only.

## Default Outputs

- `system_v4/a2_state/audit_logs/A2_LEV_BUILDER_POST_SKELETON_DISPOSITION_AUDIT_REPORT__CURRENT__v1.json`
- `system_v4/a2_state/audit_logs/A2_LEV_BUILDER_POST_SKELETON_DISPOSITION_AUDIT_REPORT__CURRENT__v1.md`
- `system_v4/a2_state/audit_logs/A2_LEV_BUILDER_POST_SKELETON_DISPOSITION_AUDIT_PACKET__CURRENT__v1.json`

## Quality Gates

- Do not migrate files.
- Do not mutate registry or runner surfaces from this slice.
- Do not claim runtime-live status, runtime import, or imported ownership.
- Do not widen the audit into completeness, execution readiness, or patch application.
- Keep the branch disposition explicit, bounded, and repo-held.

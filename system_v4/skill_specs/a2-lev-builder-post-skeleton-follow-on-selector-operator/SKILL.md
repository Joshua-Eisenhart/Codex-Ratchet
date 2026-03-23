---
skill_id: a2-lev-builder-post-skeleton-follow-on-selector-operator
name: a2-lev-builder-post-skeleton-follow-on-selector-operator
description: Selector-only post-skeleton follow-on operator that keeps the lev-builder lane bounded without migration, runner, registry, or runtime-live claims.
skill_type: maintenance
source_type: repo_skill
applicable_layers: [A2_MID_REFINEMENT, A2_LOW_CONTROL]
applicable_graphs: [runtime, control, a2_mid_refinement_graph_v1]
inputs:
  - repo_root
  - readiness_report_path
  - readiness_packet_path
  - skeleton_report_path
  - skeleton_packet_path
  - report_json_path
  - report_md_path
  - packet_path
outputs:
  - lev_builder_post_skeleton_follow_on_selector_report
  - lev_builder_post_skeleton_follow_on_selector_packet
related_skills:
  - a2-lev-builder-post-skeleton-readiness-operator
  - a2-lev-builder-formalization-skeleton-operator
  - a2-lev-builder-placement-audit-operator
  - a2-brain-surface-refresher
capabilities:
  can_write_repo: false
  can_only_propose: true
  reads_graph: true
tool_dependencies: []
provenance: "bounded post-skeleton follow-on selector retooled from the lev-builder readiness and scaffold sequence"
adapters:
  codex: system_v4/skill_specs/a2-lev-builder-post-skeleton-follow-on-selector-operator/SKILL.md
  shell: system_v4/skills/a2_lev_builder_post_skeleton_follow_on_selector_operator.py
---

# A2 lev-builder Post-Skeleton Follow-On Selector Operator

Use this skill when the post-skeleton readiness slice has already admitted a
selector-only follow-on and we need one bounded choice about the next unresolved
branch.

## Purpose

- read the landed post-skeleton readiness and skeleton surfaces
- select the smallest honest follow-on branch
- emit one bounded report and one compact packet
- keep the output clearly non-migratory and non-runtime-live

## Execute Now

1. Read:
   - [A2_LEV_BUILDER_POST_SKELETON_READINESS_REPORT__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_LEV_BUILDER_POST_SKELETON_READINESS_REPORT__CURRENT__v1.json)
   - [A2_LEV_BUILDER_POST_SKELETON_READINESS_PACKET__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_LEV_BUILDER_POST_SKELETON_READINESS_PACKET__CURRENT__v1.json)
   - [A2_LEV_BUILDER_FORMALIZATION_SKELETON_REPORT__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_LEV_BUILDER_FORMALIZATION_SKELETON_REPORT__CURRENT__v1.json)
   - [A2_LEV_BUILDER_FORMALIZATION_SKELETON_PACKET__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_LEV_BUILDER_FORMALIZATION_SKELETON_PACKET__CURRENT__v1.json)
   - [lev-builder](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/lev-builder/SKILL.md)
   - [arch](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/arch/SKILL.md)
   - [work](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/work/SKILL.md)
2. Select only the bounded unresolved follow-on branch or hold at scaffold.
3. Emit one report and one packet only.

## Default Outputs

- `system_v4/a2_state/audit_logs/A2_LEV_BUILDER_POST_SKELETON_FOLLOW_ON_SELECTOR_REPORT__CURRENT__v1.json`
- `system_v4/a2_state/audit_logs/A2_LEV_BUILDER_POST_SKELETON_FOLLOW_ON_SELECTOR_REPORT__CURRENT__v1.md`
- `system_v4/a2_state/audit_logs/A2_LEV_BUILDER_POST_SKELETON_FOLLOW_ON_SELECTOR_PACKET__CURRENT__v1.json`

## Quality Gates

- Do not migrate files.
- Do not mutate registry or runner surfaces from this slice.
- Do not claim runtime-live status, runtime import, or imported ownership.
- Do not widen the selector into execution or patch application.
- Keep the follow-on choice explicit, bounded, and repo-held.

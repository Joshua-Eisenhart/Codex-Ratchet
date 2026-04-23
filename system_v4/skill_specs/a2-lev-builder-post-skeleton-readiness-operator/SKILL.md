---
skill_id: a2-lev-builder-post-skeleton-readiness-operator
name: a2-lev-builder-post-skeleton-readiness-operator
description: Audit-only readiness operator that confirms the lev-builder post-skeleton slice is bounded without migration, runtime-live, or imported-ownership claims.
skill_type: maintenance
source_type: repo_skill
applicable_layers: [A2_MID_REFINEMENT, A2_LOW_CONTROL]
applicable_graphs: [runtime, control, a2_mid_refinement_graph_v1]
inputs:
  - repo_root
  - skeleton_report_path
  - skeleton_packet_path
  - report_json_path
  - report_md_path
  - packet_path
outputs:
  - lev_builder_post_skeleton_readiness_report
  - lev_builder_post_skeleton_readiness_packet
related_skills:
  - a2-lev-builder-formalization-skeleton-operator
  - a2-lev-builder-formalization-proposal-operator
  - a2-lev-builder-placement-audit-operator
  - a2-brain-surface-refresher
capabilities:
  can_write_repo: false
  can_only_propose: true
  reads_graph: true
tool_dependencies: []
provenance: "lev-builder placement/proposal/skeleton sequence retooled into a bounded post-skeleton readiness slice"
adapters:
  codex: system_v4/skill_specs/a2-lev-builder-post-skeleton-readiness-operator/SKILL.md
  shell: system_v4/skills/a2_lev_builder_post_skeleton_readiness_operator.py
---

# A2 lev-builder Post-Skeleton Readiness Operator

Use this skill when the lev-builder placement, proposal, and skeleton slices
have landed and we need one bounded readiness check before any wider follow-on
work is considered.

## Purpose

- confirm the post-skeleton slice is still bounded and repo-held
- keep the lane audit-oriented instead of turning it into migration or runtime work
- emit one report and one packet only
- preserve the non-goals as explicit guardrails

## Execute Now

1. Read:
   - [A2_LEV_BUILDER_FORMALIZATION_SKELETON_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_LEV_BUILDER_FORMALIZATION_SKELETON_REPORT__CURRENT__v1.json)
   - [A2_LEV_BUILDER_FORMALIZATION_SKELETON_PACKET__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_LEV_BUILDER_FORMALIZATION_SKELETON_PACKET__CURRENT__v1.json)
   - [A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.json)
   - [GRAPH_CAPABILITY_AUDIT__2026_03_20__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/GRAPH_CAPABILITY_AUDIT__2026_03_20__v1.json)
   - [lev-builder](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/lev-builder/SKILL.md)
   - [arch](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/arch/SKILL.md)
   - [work](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/work/SKILL.md)
   - optional background only: [lev-plan](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/lev-plan/SKILL.md) and [stack](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/stack/SKILL.md)
2. Verify the bounded post-skeleton readiness surface only.
3. Keep the slice non-migratory, non-runtime-live, and non-promotional.

## Default Outputs

When no explicit paths are supplied, write:

- `system_v4/a2_state/audit_logs/A2_LEV_BUILDER_POST_SKELETON_READINESS_REPORT__CURRENT__v1.json`
- `system_v4/a2_state/audit_logs/A2_LEV_BUILDER_POST_SKELETON_READINESS_REPORT__CURRENT__v1.md`
- `system_v4/a2_state/audit_logs/A2_LEV_BUILDER_POST_SKELETON_READINESS_PACKET__CURRENT__v1.json`

## Quality Gates

- Do not claim migration permission, runtime-live status, formalization completion, or imported runtime ownership.
- Do not mutate files, registry, or runner surfaces from this slice.
- Do not widen the slice into build, promotion, or execution work.
- Keep the output explicit about what is bounded, ready, and still deferred.

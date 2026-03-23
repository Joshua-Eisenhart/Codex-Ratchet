---
skill_id: a2-lev-builder-formalization-skeleton-operator
name: a2-lev-builder-formalization-skeleton-operator
description: Prove the bounded lev-builder formalization scaffold bundle is landed after the proposal packet, without migration, registry, runner, or runtime-import claims.
skill_type: maintenance
source_type: repo_skill
applicable_layers: [A2_MID_REFINEMENT, A2_LOW_CONTROL]
applicable_graphs: [runtime, control, a2_mid_refinement_graph_v1]
inputs:
  - repo_root
  - proposal_report_path
  - proposal_packet_path
  - brain_refresh_report_path
  - graph_audit_path
outputs:
  - lev_builder_formalization_skeleton_report
  - lev_builder_formalization_skeleton_packet
related_skills:
  - a2-lev-builder-placement-audit-operator
  - a2-lev-builder-formalization-proposal-operator
  - a2-brain-surface-refresher
capabilities:
  can_write_repo: false
  can_only_propose: false
  reads_graph: true
tool_dependencies: []
provenance: "lev-os/agents lev-builder formalization proposal retooled into a bounded scaffold-proof slice"
adapters:
  codex: system_v4/skill_specs/a2-lev-builder-formalization-skeleton-operator/SKILL.md
  shell: system_v4/skills/a2_lev_builder_formalization_skeleton_operator.py
---

# A2 lev-builder Formalization Skeleton Operator

Use this skill when the formalization proposal packet has already landed and the scaffold bundle for the next bounded slice is now present on disk.

## Purpose

- prove the smallest honest scaffold bundle is landed
- preserve keep/adapt/mine/skip boundaries
- keep migration, runner, and runtime-import claims false
- emit one repo-held skeleton report and one compact packet

## Execute Now

1. Read:
   - [A2_LEV_BUILDER_FORMALIZATION_PROPOSAL_REPORT__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_LEV_BUILDER_FORMALIZATION_PROPOSAL_REPORT__CURRENT__v1.json)
   - [A2_LEV_BUILDER_FORMALIZATION_PROPOSAL_PACKET__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_LEV_BUILDER_FORMALIZATION_PROPOSAL_PACKET__CURRENT__v1.json)
   - [A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.json)
   - [GRAPH_CAPABILITY_AUDIT__2026_03_20__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/GRAPH_CAPABILITY_AUDIT__2026_03_20__v1.json)
   - [lev-builder](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/lev-builder/SKILL.md)
   - [arch](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/arch/SKILL.md)
   - [work](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/work/SKILL.md)
   - optional background only: [lev-plan](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/lev-plan/SKILL.md) and [stack](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/stack/SKILL.md)
2. Verify the bounded scaffold bundle is present:
   - `system_v4/skill_specs/a2-lev-builder-formalization-skeleton-operator/SKILL.md`
   - `system_v4/skills/a2_lev_builder_formalization_skeleton_operator.py`
   - `system_v4/skills/test_a2_lev_builder_formalization_skeleton_operator_smoke.py`
3. Keep the slice scaffold-only and non-migratory.
4. Emit one report and one packet only.

## Default Outputs

- `system_v4/a2_state/audit_logs/A2_LEV_BUILDER_FORMALIZATION_SKELETON_REPORT__CURRENT__v1.json`
- `system_v4/a2_state/audit_logs/A2_LEV_BUILDER_FORMALIZATION_SKELETON_REPORT__CURRENT__v1.md`
- `system_v4/a2_state/audit_logs/A2_LEV_BUILDER_FORMALIZATION_SKELETON_PACKET__CURRENT__v1.json`

## Quality Gates

- Do not migrate files.
- Do not generate or apply patches.
- Do not update registry or runner surfaces from inside this operator.
- Do not claim runtime import, production placement, formalization completion, or imported runtime ownership.
- Do not widen the slice into a migration or execution lane.
- Keep the scaffold bundle explicitly bounded, repo-held, and non-runtime-live.

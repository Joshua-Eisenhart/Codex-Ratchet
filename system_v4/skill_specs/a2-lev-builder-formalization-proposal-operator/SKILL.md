---
skill_id: a2-lev-builder-formalization-proposal-operator
name: a2-lev-builder-formalization-proposal-operator
description: Emit one bounded proposal-only repo-held formalization proposal for the lev-builder seam after the placement audit has landed, without migration or runtime claims.
skill_type: maintenance
source_type: repo_skill
applicable_layers: [A2_MID_REFINEMENT, A2_LOW_CONTROL]
applicable_graphs: [runtime, control, a2_mid_refinement_graph_v1]
inputs: [repo_root, placement_report_path, placement_packet_path, report_json_path, report_md_path, packet_path]
outputs: [lev_builder_formalization_proposal_report, lev_builder_formalization_proposal_packet]
related_skills: [a2-lev-builder-placement-audit-operator, a2-lev-agents-promotion-operator, a2-brain-surface-refresher]
capabilities:
  can_write_repo: false
  can_only_propose: true
  reads_graph: true
tool_dependencies: []
provenance: "lev-os/agents lev-builder placement audit retooled into a bounded proposal-only formalization follow-on slice"
adapters:
  codex: system_v4/skill_specs/a2-lev-builder-formalization-proposal-operator/SKILL.md
  shell: system_v4/skills/a2_lev_builder_formalization_proposal_operator.py
---

# A2 lev-builder Formalization Proposal Operator

Use this skill when the lev-builder placement audit has already landed and the
next step must stay proposal-only instead of widening into migration, runtime,
or imported implementation claims.

## Purpose

- read the landed lev-builder placement audit surfaces
- propose the smallest honest next formalization shape without claiming it is live
- keep `keep/adapt/mine/skip` boundaries explicit
- emit one repo-held proposal report and one compact packet

## Execute Now

1. Read:
   - [A2_LEV_BUILDER_PLACEMENT_AUDIT_REPORT__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_LEV_BUILDER_PLACEMENT_AUDIT_REPORT__CURRENT__v1.json)
   - [A2_LEV_BUILDER_PLACEMENT_AUDIT_PACKET__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_LEV_BUILDER_PLACEMENT_AUDIT_PACKET__CURRENT__v1.json)
   - [A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.json)
   - [lev-builder](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/lev-builder/SKILL.md)
   - [arch](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/arch/SKILL.md)
   - [work](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/work/SKILL.md)
   - optional background only: [lev-plan](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/lev-plan/SKILL.md) and [stack](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/stack/SKILL.md)
2. Keep the slice proposal-only.
3. Emit one report and one packet only.

## Default Outputs

When no explicit paths are supplied, write:

- `system_v4/a2_state/audit_logs/A2_LEV_BUILDER_FORMALIZATION_PROPOSAL_REPORT__CURRENT__v1.json`
- `system_v4/a2_state/audit_logs/A2_LEV_BUILDER_FORMALIZATION_PROPOSAL_REPORT__CURRENT__v1.md`
- `system_v4/a2_state/audit_logs/A2_LEV_BUILDER_FORMALIZATION_PROPOSAL_PACKET__CURRENT__v1.json`

## Quality Gates

- Do not migrate files.
- Do not generate or apply patches.
- Do not update registry or runner surfaces.
- Do not claim runtime import, production placement, or formalization completion.
- Do not claim prompt-stack control or `.lev/*` substrate import.
- Keep the follow-on explicitly proposal-side and nonoperative.

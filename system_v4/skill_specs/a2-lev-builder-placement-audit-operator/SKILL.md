---
skill_id: a2-lev-builder-placement-audit-operator
name: a2-lev-builder-placement-audit-operator
description: Emit one bounded repo-held placement/formalization audit for the lev-builder seam, without migrating files or claiming full Lev formalization import.
skill_type: maintenance
source_type: repo_skill
applicable_layers: [A2_MID_REFINEMENT, A2_LOW_CONTROL]
applicable_graphs: [runtime, control, a2_mid_refinement_graph_v1]
inputs: [repo_root, candidate, report_json_path, report_md_path, packet_path]
outputs: [lev_builder_placement_audit_report, lev_builder_placement_audit_packet]
related_skills: [a2-lev-agents-promotion-operator, a2-workshop-analysis-gate-operator, a2-brain-surface-refresher]
capabilities:
  can_write_repo: false
  can_only_propose: true
  reads_graph: true
tool_dependencies: []
provenance: "lev-os/agents lev-builder plus arch and work retooled into a bounded Ratchet placement/formalization audit slice"
adapters:
  codex: system_v4/skill_specs/a2-lev-builder-placement-audit-operator/SKILL.md
  shell: system_v4/skills/a2_lev_builder_placement_audit_operator.py
---

# A2 lev-builder Placement Audit Operator

Use this skill when the local `lev-os/agents` promotion report already points at
the lev formalization / placement cluster and we need one bounded audit over the
`lev-builder` seam before claiming any deeper imported implementation.

## Purpose

- read the current lev-os/agents promotion report and packet
 - audit the local `lev-builder` seam and its nearby helper refs
- emit one repo-held placement/formalization audit report and one packet
- keep non-goals explicit so this does not turn into migration or production placement

## Execute Now

1. Read:
   - [A2_LEV_AGENTS_PROMOTION_REPORT__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_LEV_AGENTS_PROMOTION_REPORT__CURRENT__v1.json)
   - [A2_LEV_AGENTS_PROMOTION_PACKET__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_LEV_AGENTS_PROMOTION_PACKET__CURRENT__v1.json)
   - [A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.json)
   - [lev-builder](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/lev-builder/SKILL.md)
   - [arch](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/arch/SKILL.md)
   - [work](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/work/SKILL.md)
   - optional background only: [lev-plan](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/lev-plan/SKILL.md) and [stack](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/stack/SKILL.md)
2. Keep the slice bounded to placement/formalization audit only.
3. Emit one report and one packet only.

## Quality Gates

- Do not mutate paths or generate graph plans.
- Do not migrate files.
- Do not generate or apply patches.
- Do not run tests, registry updates, git close-loop, or production placement actions.
- Do not claim prompt-stack control, `.lev/*` substrate import, or full Lev formalization import.

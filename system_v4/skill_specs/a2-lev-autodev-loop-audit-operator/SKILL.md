---
skill_id: a2-lev-autodev-loop-audit-operator
name: a2-lev-autodev-loop-audit-operator
description: Emit one bounded repo-held audit over the lev autodev execution/validation loop seam without claiming cron, heartbeat, `.lev`, or prompt-stack runtime ownership.
skill_type: maintenance
source_type: repo_skill
applicable_layers: [A2_MID_REFINEMENT, A2_LOW_CONTROL]
applicable_graphs: [runtime, control, a2_mid_refinement_graph_v1]
inputs: [repo_root, candidate, report_json_path, report_md_path, packet_path]
outputs: [lev_autodev_loop_audit_report, lev_autodev_loop_audit_packet]
related_skills: [a2-lev-agents-promotion-operator, a2-tracked-work-operator, a2-brain-surface-refresher]
capabilities:
  can_write_repo: false
  can_only_propose: true
  reads_graph: true
tool_dependencies: []
provenance: "lev-os/agents autodev-loop plus autodev-lev, with lev-plan and stack as background-only context, retooled into a bounded Ratchet execution/validation loop audit slice"
adapters:
  codex: system_v4/skill_specs/a2-lev-autodev-loop-audit-operator/SKILL.md
  shell: system_v4/skills/a2_lev_autodev_loop_audit_operator.py
---

# A2 lev Autodev Loop Audit Operator

Use this skill when the current lev-os/agents promotion report points at the
autodev execution/validation cluster and we need one bounded audit over the
loop seam before claiming any recurring execution or runtime import.

## Purpose

- read the current lev-os/agents promotion report and packet
- audit the local `autodev-loop` seam and its nearby runtime-coupled refs
- emit one repo-held report and one packet only
- keep non-goals explicit so this does not turn into cron, heartbeat, `.lev`,
  prompt-stack, git-sync, or service control

## Execute Now

1. Read:
   - [A2_LEV_AGENTS_PROMOTION_REPORT__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_LEV_AGENTS_PROMOTION_REPORT__CURRENT__v1.json)
   - [A2_LEV_AGENTS_PROMOTION_PACKET__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_LEV_AGENTS_PROMOTION_PACKET__CURRENT__v1.json)
   - [A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.json)
   - [autodev-loop](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/autodev-loop/SKILL.md)
   - [autodev-lev](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/autodev-lev/SKILL.md)
   - [autodev.ts](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/leviathan/plugins/core-sdlc/src/commands/autodev.ts)
   - background only: [lev-plan](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/lev-plan/SKILL.md), [stack](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/stack/SKILL.md), and [support README](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/leviathan/plugins/core-sdlc/support/README.md)
2. Keep the slice bounded to loop-shape / validation-boundary / runtime-coupling audit only.
3. Emit one report and one packet only.

## Quality Gates

- Do not schedule or run cron ticks.
- Do not claim heartbeat runtime continuity or `lev loop autodev` ownership.
- Do not claim `.lev/pm/*` or validation-gates substrate ownership.
- Do not claim prompt-stack runtime control.
- Do not run git sync, background service setup, or recurring autonomous execution.
- Do not claim that Ratchet now has a live autodev loop.

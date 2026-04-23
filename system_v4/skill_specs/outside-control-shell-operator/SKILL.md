---
skill_id: outside-control-shell-operator
name: outside-control-shell-operator
description: Emit one bounded repo-held pi-mono outside-session-host audit report and packet, without claiming runtime hosting, memory integration, or full pi-mono import.
skill_type: maintenance
source_type: repo_skill
applicable_layers: [A2_LOW_CONTROL, A2_MID_REFINEMENT]
applicable_graphs: [runtime, control, a2_low_control_graph_v1]
inputs: [repo, target_surface_path, report_json_path, report_md_path, packet_path]
outputs: [outside_session_host_report, outside_session_host_packet]
related_skills: [outer-session-ledger, a2-brain-surface-refresher, a2-workshop-analysis-gate-operator]
capabilities:
  can_write_repo: true
  can_only_propose: true
tool_dependencies: []
provenance: "pi-mono coding-agent session surfaces and mom workspace boundary retooled into a bounded Ratchet outside-session-host audit slice"
adapters:
  codex: system_v4/skill_specs/outside-control-shell-operator/SKILL.md
  shell: system_v4/skills/outside_control_shell_operator.py
---

# Outside Control Shell Operator

Use this skill when we want one honest repo-held audit of the `pi-mono`
outside control-shell/session-host seam without pretending the whole host stack
is ported or live inside Ratchet.

## Purpose

- inspect one local pi-mono session-host surface
- summarize the session header, entry/message counts, stop reasons, and shell clues
- keep mom as a boundary-only workspace model, not canonical control state
- emit one JSON report, one Markdown report, and one compact packet only

## Execute Now

1. Read:
   - [V4_IMPORTED_SKILL_CLUSTER_MAP__CURRENT.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/V4_IMPORTED_SKILL_CLUSTER_MAP__CURRENT.md)
   - [SYSTEM_SKILL_BUILD_PLAN.md](/home/ratchet/Desktop/Codex%20Ratchet/SYSTEM_SKILL_BUILD_PLAN.md)
   - [session.md](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/other/pi-mono/packages/coding-agent/docs/session.md)
   - [rpc.md](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/other/pi-mono/packages/coding-agent/docs/rpc.md)
   - [README.md](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/other/pi-mono/packages/mom/README.md)
2. Inspect the current target session surface. Default target:
   - `work/reference_repos/other/pi-mono/packages/coding-agent/test/fixtures/large-session.jsonl`
3. Emit one report and one compact packet only.

## Default Outputs

When no explicit path is supplied, write:

- `system_v4/a2_state/audit_logs/A2_PIMONO_OUTSIDE_SESSION_HOST_REPORT__CURRENT__v1.json`
- `system_v4/a2_state/audit_logs/A2_PIMONO_OUTSIDE_SESSION_HOST_REPORT__CURRENT__v1.md`
- `system_v4/a2_state/audit_logs/A2_PIMONO_OUTSIDE_SESSION_HOST_PACKET__CURRENT__v1.json`

## Quality Gates

- Do not claim full pi-mono integration or runtime hosting inside Ratchet.
- Do not claim memory integration, startup retrieval, or A2 replacement.
- Do not mutate pi-mono workspaces, session files, or canonical A2 state.
- Keep mom boundary-only and do not treat `context.jsonl` as canonical truth.

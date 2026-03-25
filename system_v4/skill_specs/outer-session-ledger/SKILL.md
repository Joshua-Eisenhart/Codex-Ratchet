---
skill_id: outer-session-ledger
name: outer-session-ledger
description: Emit one bounded repo-held outer-session continuity ledger from local session surfaces, without claiming FlowMind hosting, A2 replacement, or memory fusion.
skill_type: maintenance
source_type: repo_skill
applicable_layers: [A2_LOW_CONTROL, A2_MID_REFINEMENT]
applicable_graphs: [runtime, control, a2_low_control_graph_v1]
inputs: [repo, sessions_root, host_kind, state_path, events_path, report_json_path, report_md_path]
outputs: [outer_session_ledger_state, outer_session_ledger_report]
related_skills: [a2-brain-surface-refresher, a2-workshop-analysis-gate-operator, witness-evermem-sync]
capabilities:
  can_write_repo: true
  can_only_propose: true
tool_dependencies: []
provenance: "lev-os/leviathan session durability patterns retooled into a bounded Ratchet continuity ledger slice"
adapters:
  codex: system_v4/skill_specs/outer-session-ledger/SKILL.md
  shell: system_v4/skills/outer_session_ledger.py
---

# Outer Session Ledger

Use this skill when we want one honest repo-held continuity surface for an
outside or outside-shaped session host, without pretending the whole Leviathan
or FlowMind runtime is ported.

## Purpose

- observe local session continuity surfaces
- keep one current ledger state plus one append-only event trail
- emit one report about resumability, cursor position, receipts, and non-goals
- keep the first Leviathan-derived slice bounded to continuity witnessing

## Execute Now

1. Read:
   - [V4_IMPORTED_SKILL_CLUSTER_MAP__CURRENT.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/V4_IMPORTED_SKILL_CLUSTER_MAP__CURRENT.md)
   - [SYSTEM_SKILL_BUILD_PLAN.md](/home/ratchet/Desktop/Codex%20Ratchet/SYSTEM_SKILL_BUILD_PLAN.md)
   - [ratchet_prompt_stack.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills/ratchet_prompt_stack.py)
2. Inspect the current session surfaces under `system_v4/a2_state/stack_sessions` unless an explicit alternate root is supplied.
3. Emit:
   - one current ledger state
   - one append-only event observation
   - one current JSON report
   - one current Markdown report

## Default Outputs

When no explicit path is supplied, write:

- `system_v4/a2_state/OUTER_SESSION_LEDGER_STATE__CURRENT__v1.json`
- `system_v4/a2_state/OUTER_SESSION_LEDGER_EVENTS__APPEND_ONLY__v1.jsonl`
- `system_v4/a2_state/audit_logs/OUTER_SESSION_LEDGER_REPORT__CURRENT__v1.json`
- `system_v4/a2_state/audit_logs/OUTER_SESSION_LEDGER_REPORT__CURRENT__v1.md`

## Quality Gates

- Do not claim FlowMind runtime hosting inside Ratchet.
- Do not claim memory replacement or A2 replacement.
- Do not mutate canonical A2 or outside host state.
- Keep this slice observer-only and repo-held.

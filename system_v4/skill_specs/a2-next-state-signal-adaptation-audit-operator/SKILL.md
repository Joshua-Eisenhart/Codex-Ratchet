---
skill_id: a2-next-state-signal-adaptation-audit-operator
name: a2-next-state-signal-adaptation-audit-operator
description: Map the OpenClaw-RL paper and repo into a bounded Ratchet next-state / directive-correction audit slice without claiming the OpenClaw-RL training stack is ported.
skill_type: maintenance
source_type: repo_skill
applicable_layers: [A2_MID_REFINEMENT, B_ADJUDICATED]
applicable_graphs: [runtime, control, a2_mid_refinement_graph_v1]
inputs: [repo, report_path, markdown_path, packet_path]
outputs: [next_state_signal_adaptation_audit_report, next_state_signal_adaptation_audit_packet]
related_skills: [witness-recorder, runtime-state-kernel, bounded-improve-operator, a2-skill-improver-readiness-operator, a2-skill-improver-first-target-proof-operator]
capabilities:
  can_write_repo: true
  can_only_propose: true
tool_dependencies: []
provenance: "OpenClaw-RL (arXiv 2603.10165 + Gen-Verse/OpenClaw-RL) retooled into a bounded Ratchet next-state signal adaptation audit slice"
adapters:
  codex: system_v4/skill_specs/a2-next-state-signal-adaptation-audit-operator/SKILL.md
  shell: system_v4/skills/a2_next_state_signal_adaptation_audit_operator.py
---

# A2 Next-State Signal Adaptation Audit Operator

Use this skill when we want to process OpenClaw-RL as source material and make
one honest Ratchet-native slice from it without pretending we imported its RL
runtime.

## Purpose

- turn the paper plus repo into a durable corpus member
- map `next-state`, `directive correction`, and `async improvement` ideas onto existing Ratchet seams
- emit one repo-held report and packet for the current bounded mapping

## Execute Now

1. Read:
   - [work/external_refs/OPENCLAW_RL__REFERENCE_NOTE__2026_03_21__v1.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/work/external_refs/OPENCLAW_RL__REFERENCE_NOTE__2026_03_21__v1.md)
   - [SKILL_SOURCE_CORPUS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/SKILL_SOURCE_CORPUS.md)
   - [REPO_SKILL_INTEGRATION_TRACKER.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/REPO_SKILL_INTEGRATION_TRACKER.md)
   - [system_v4/V4_IMPORTED_SKILL_CLUSTER_MAP__CURRENT.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/V4_IMPORTED_SKILL_CLUSTER_MAP__CURRENT.md)
2. Verify the local mapping seams only:
   - `witness-recorder`
   - `runtime-state-kernel`
   - `bounded-improve-operator`
   - `a2-skill-improver-readiness-operator`
   - `a2-skill-improver-first-target-proof-operator`
3. Emit one report that says what to keep, what to adapt, what not to import, and what the next bounded follow-on would be.

## Default Outputs

When no explicit path is supplied, write:

- `system_v4/a2_state/audit_logs/A2_NEXT_STATE_SIGNAL_ADAPTATION_AUDIT_REPORT__CURRENT__v1.json`
- `system_v4/a2_state/audit_logs/A2_NEXT_STATE_SIGNAL_ADAPTATION_AUDIT_REPORT__CURRENT__v1.md`
- `system_v4/a2_state/audit_logs/A2_NEXT_STATE_SIGNAL_ADAPTATION_AUDIT_PACKET__CURRENT__v1.json`

## Quality Gates

- Do not claim OpenClaw runtime import.
- Do not claim online RL training is now live in Ratchet.
- Do not claim policy mutation from live user traffic.
- Keep the slice audit-only, proposal-only, and repo-held.

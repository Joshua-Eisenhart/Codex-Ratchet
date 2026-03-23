---
skill_id: a2-next-state-directive-signal-probe-operator
name: a2-next-state-directive-signal-probe-operator
description: Probe the live witness corpus for bounded next-state and directive-correction evidence without claiming live learning or mutation.
skill_type: maintenance
source_type: repo_skill
applicable_layers: [A2_MID_REFINEMENT, B_ADJUDICATED]
applicable_graphs: [runtime, control, a2_mid_refinement_graph_v1]
inputs: [repo, next_state_audit_path, witness_path, readiness_report_path, report_path, markdown_path, packet_path]
outputs: [next_state_directive_signal_probe_report, next_state_directive_signal_probe_packet]
related_skills: [a2-next-state-signal-adaptation-audit-operator, witness-recorder, runtime-state-kernel, a2-skill-improver-readiness-operator]
capabilities:
  can_write_repo: true
  can_only_propose: true
tool_dependencies: []
provenance: "OpenClaw-RL-derived bounded probe over Ratchet witness entries and skill-improver readiness surfaces"
adapters:
  codex: system_v4/skill_specs/a2-next-state-directive-signal-probe-operator/SKILL.md
  shell: system_v4/skills/a2_next_state_directive_signal_probe_operator.py
---

# A2 Next-State Directive Signal Probe Operator

Use this skill after the next-state-signal adaptation audit when we want one
honest answer to the question: do we currently have real next-state and
directive-correction evidence in the witness corpus, or are we still only
describing the idea?

## Purpose

- inspect the current witness corpus for actual post-action evidence
- separate evaluative signal from directive correction signal
- decide whether a later bounded improver-context bridge is even admissible

## Execute Now

1. Read:
   - [A2_NEXT_STATE_SIGNAL_ADAPTATION_AUDIT_REPORT__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_NEXT_STATE_SIGNAL_ADAPTATION_AUDIT_REPORT__CURRENT__v1.json)
   - [system_v4/a2_state/witness_corpus_v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/witness_corpus_v1.json)
   - [SKILL_IMPROVER_READINESS_REPORT__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/SKILL_IMPROVER_READINESS_REPORT__CURRENT__v1.json)
2. Count and classify witness entries only:
   - transition / next-state candidates
   - evaluative signals
   - directive-correction signals
3. Emit one repo-held report and packet with the bounded verdict.

## Default Outputs

When no explicit path is supplied, write:

- `system_v4/a2_state/audit_logs/A2_NEXT_STATE_DIRECTIVE_SIGNAL_PROBE_REPORT__CURRENT__v1.json`
- `system_v4/a2_state/audit_logs/A2_NEXT_STATE_DIRECTIVE_SIGNAL_PROBE_REPORT__CURRENT__v1.md`
- `system_v4/a2_state/audit_logs/A2_NEXT_STATE_DIRECTIVE_SIGNAL_PROBE_PACKET__CURRENT__v1.json`

## Quality Gates

- Do not mutate the witness corpus.
- Do not treat `intent` or `context` entries by themselves as post-action next-state proof.
- Do not widen this into an improver or live-learning claim unless the report earns it.
- Keep the slice audit-only, proposal-only, and repo-held.

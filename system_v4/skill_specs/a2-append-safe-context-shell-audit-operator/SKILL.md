---
skill_id: a2-append-safe-context-shell-audit-operator
name: a2-append-safe-context-shell-audit-operator
description: Audit-only append-safe context-shell slice for the context-spec-workflow-memory cluster that maps current standing A2 continuity surfaces, admitted write shapes, and anti-bloat fences
skill_type: maintenance
source_type: repo_skill
applicable_layers: [A2_MID_REFINEMENT, A2_LOW_CONTROL]
applicable_graphs: [runtime, control, a2_mid_refinement_graph_v1]
inputs: [repo_root, audit_scope, report_json_path, report_md_path, packet_path]
outputs: [a2_append_safe_context_shell_audit_report, a2_append_safe_context_shell_audit_packet]
related_skills: [a2-context-spec-workflow-follow-on-selector-operator, a2-context-spec-workflow-pattern-audit-operator, a2-brain-surface-refresher]
capabilities:
  can_write_repo: false
  can_only_propose: true
  reads_graph: true
tool_dependencies: []
provenance: "Ratchet-native append-safe continuity-shell audit derived from Context-Engineering, spec-kit, superpowers, and mem0 as source-family pressure only"
adapters:
  codex: system_v4/skill_specs/a2-append-safe-context-shell-audit-operator/SKILL.md
  shell: system_v4/skills/a2_append_safe_context_shell_audit_operator.py
---

# A2 Append Safe Context Shell Audit Operator

Use this skill when the selected `context-spec-workflow-memory` lane needs the
bounded append-safe context-shell follow-on slice.

## Purpose

- audit the standing continuity shell already used by Ratchet:
  - `INTENT_SUMMARY.md`
  - `A2_BRAIN_SLICE__v1.md`
  - `A2_KEY_CONTEXT_APPEND_LOG__v1.md`
  - `OPEN_UNRESOLVED__v1.md`
  - `A2_CONTROLLER_STATE_RECORD__CURRENT__v1.md`
- make the admitted write shapes explicit so continuity stays append-safe and
  low-bloat
- preserve explicit non-goals around canonical memory replacement, background
  session ownership, graph-substrate replacement, and service import

## Execute Now

1. Confirm the context/spec/workflow follow-on selector explicitly chose this slice.
2. Confirm the local source repos still exist.
3. Audit the current standing continuity shell surfaces and classify admitted
   write shapes.
4. Emit one repo-held report and one compact packet.

## Quality Gates

- No canonical `A2` / `A1` brain replacement claim.
- No new owner-surface family creation claim.
- No background workflow/session-manager ownership claim.
- No external memory platform or service bootstrap claim.
- No graph-substrate replacement claim.
- No selector widening by momentum.

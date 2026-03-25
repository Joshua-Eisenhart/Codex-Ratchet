---
skill_id: skill-improver-operator
name: skill-improver-operator
description: Validate and optionally commit a proposed target-skill update under explicit dry-run, test, and allowlist gates.
skill_type: operator
source_type: repo_skill
applicable_layers: [A2_MID_REFINEMENT, A2_LOW_CONTROL]
applicable_graphs: [runtime, a2_mid_refinement_graph_v1]
inputs: [target_skill_path, candidate_code, test_command, allow_write, approval_token, allowed_targets, recorder, context_packet, context_bridge_packet, bridge_packet, directive_topics, selected_witness_indices, context_notes]
outputs: [improved, detail, path, proposed_change, compile_ok, tests_state, score, write_permitted, dry_run, context_contract_status, context_summary]
related_skills: [a2-skill-improver-readiness-operator, autoresearch-operator, llm-council-operator]
capabilities:
  can_write_repo: true
  requires_human_gate: true
tool_dependencies: []
provenance: "Karpathy mutator-loop pattern retooled into a bounded Ratchet skill-validation and gated-commit operator"
adapters:
  codex: system_v4/skill_specs/skill-improver-operator/SKILL.md
  shell: system_v4/skills/skill_improver_operator.py
---

# Skill Improver Operator

Use this skill when a candidate update to one existing skill needs bounded
validation before any repo write is permitted.

## Purpose

- validate one proposed target-skill update
- require explicit dry-run/test/allowlist gates
- allow commit only when approval is explicit

## Execute Now

1. Read:
   - [SKILL_IMPROVER_READINESS_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/SKILL_IMPROVER_READINESS_REPORT__CURRENT__v1.json)
   - [a2-skill-improver-readiness-operator spec](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/skill_specs/a2-skill-improver-readiness-operator/SKILL.md)
2. Require:
   - `candidate_code`
   - bounded `test_command`
   - explicit `allow_write`
   - explicit `approval_token`
   - exact-path `allowed_targets`
3. Keep dry-run as the default.
4. Treat any `context_packet` / `bridge_packet` inputs as bounded first-target metadata only.

## Context Contract

- Optional context fields may be supplied for the current proven first-target class only:
  - `context_packet`
  - `context_bridge_packet`
  - `bridge_packet`
  - `directive_topics`
  - `selected_witness_indices`
  - `context_notes`
- This contract is metadata-only:
  - it may shape repo-held audit context
  - it must not change write permission, allowlist gates, compile gates, test gates, or target admissibility
- Do not treat this contract as permission for:
  - second-target admission
  - live learning
  - runtime import
  - graph backfill

## Quality Gates

- Do not invent mutations implicitly.
- Do not write to a target that is not exact-path allowlisted.
- Do not commit a candidate that fails `py_compile`.
- Do not commit a candidate when the selected test command fails.
- Do not treat this operator as permissionless self-mutation.
- Do not treat accepted context metadata as proof that a broader consumer lane is runtime-live.

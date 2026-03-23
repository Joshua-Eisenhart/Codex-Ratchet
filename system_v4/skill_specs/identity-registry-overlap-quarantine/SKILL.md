---
skill_id: identity-registry-overlap-quarantine
name: identity-registry-overlap-quarantine
description: Quarantine heuristic identity-overlap edges out of the live identity owner surface into a separate non-canonical suggestion surface, keeping the owner graph limited to canonical identity facts.
skill_type: correction
source_type: repo_skill
applicable_layers: [INDEX, A2_HIGH_INTAKE, A2_MID_REFINEMENT, A2_LOW_CONTROL, A1_JARGONED, A1_STRIPPED, A1_CARTRIDGE]
applicable_graphs: [concept, rosetta, dependency]
inputs: [identity_registry_v1]
outputs: [identity_registry_v1, identity_registry_overlap_suggestions_v1, identity_registry_overlap_quarantine_audit]
related_skills: [identity-registry-builder, graph-capability-auditor, nested-graph-layer-auditor]
capabilities:
  can_write_repo: true
  can_only_propose: false
tool_dependencies: []
provenance: "repo-grounded correction lane for quarantining lexical identity overlap out of the owner surface"
adapters:
  codex: system_v4/skill_specs/identity-registry-overlap-quarantine/SKILL.md
  gemini: system_v4/skill_specs/identity-registry-overlap-quarantine/SKILL.md
  shell: system_v4/skills/identity_registry_overlap_quarantine.py
---

# Identity Registry Overlap Quarantine

Use this skill when the live identity owner surface has accumulated lexical
overlap edges that are not strong enough to count as canonical identity facts.

## Purpose

- keep the identity owner surface limited to canonical identity facts
- move heuristic lexical overlap into a separate non-canonical suggestion surface
- prevent filename/package-token collisions from masquerading as identity proofs

## Execute Now

1. Load:
   - `system_v4/a2_state/graphs/identity_registry_v1.json`
2. Identify all `IDENTITY_OVERLAP` edges.
3. Rewrite the owner surface without those edges.
4. Emit:
   - `system_v4/a2_state/graphs/identity_registry_v1.json`
   - `system_v4/a2_state/graphs/identity_registry_overlap_suggestions_v1.json`
   - `system_v4/a2_state/audit_logs/IDENTITY_REGISTRY_OVERLAP_QUARANTINE_AUDIT__2026_03_20__v1.md`

## Quality Gates

- Do not claim lexical shared-token overlap is canonical identity.
- Do not delete identity nodes from the owner surface in this pass.
- Do not promote the suggestion surface to owner authority.
- If no `IDENTITY_OVERLAP` edges exist, write an audit that says so and make no semantic changes.

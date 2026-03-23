---
skill_id: skill-kernel-link-seeding-policy-audit
name: skill-kernel-link-seeding-policy-audit
description: Audit what evidence is insufficient versus sufficient for future SKILL to KERNEL_CONCEPT link seeding, so the skill island stays fail-closed until owner-bound concept identity exists.
skill_type: audit
source_type: repo_skill
applicable_layers: [SKILL_REGISTRY, A2_LOW_CONTROL, A2_MID_REFINEMENT]
applicable_graphs: [runtime, control, dependency]
inputs: [skill_registry_v1, system_graph_a2_refinery, control_graph_bridge_source_audit_report]
outputs: [skill_kernel_link_seeding_policy_audit_report, skill_kernel_link_seeding_policy_packet]
related_skills: [control-graph-bridge-source-auditor, survivor-kernel-bridge-backfill-audit, pyg-heterograph-projection-audit]
capabilities:
  can_write_repo: true
  can_only_propose: true
  reads_graph: true
tool_dependencies: []
provenance: "repo-grounded audit slice over what may and may not justify future skill-to-kernel seeding under current registry and graph truth"
adapters:
  codex: system_v4/skill_specs/skill-kernel-link-seeding-policy-audit/SKILL.md
  shell: system_v4/skills/skill_kernel_link_seeding_policy_audit.py
---

# Skill Kernel Link Seeding Policy Audit

Use this skill when the next bridge question is no longer "are skills still an
island?" but "what exact evidence would be strong enough to ever seed direct
`SKILL -> KERNEL_CONCEPT` links, and what must stay forbidden for now?"

## Purpose

- read the canonical skill registry, live graph, and current bridge-source audit
- measure whether skills carry any owner-bound kernel concept identity
- keep auto-seeding fail-closed under current metadata-only conditions
- define:
  - forbidden current seed evidence
  - minimally sufficient future evidence
  - current policy status

## Execute Now

1. Load:
   - `system_v4/a1_state/skill_registry_v1.json`
   - `system_v4/a2_state/graphs/system_graph_a2_refinery.json`
   - `system_v4/a2_state/audit_logs/CONTROL_GRAPH_BRIDGE_SOURCE_AUDIT__CURRENT__v1.json`
2. Keep the registry and canonical live graph as owner surfaces.
3. Measure:
   - current registry row keys
   - current skill-node property keys
   - current skill outgoing relation families
   - whether any owner-bound concept fields exist today
4. Emit one JSON report, one markdown note, and one compact packet under `system_v4/a2_state/audit_logs/`.

## Quality Gates

- Do not permit direct skill-to-kernel seeding from source path, tags, descriptions, applicable layers, related skills, or other operational metadata alone.
- Do not permit direct skill-to-kernel seeding from inferred `SKILL -> SKILL` edges.
- Do not treat free-text skill specs as owner-bound concept identity.
- Keep the result audit-only, proposal-only, and repo-held.

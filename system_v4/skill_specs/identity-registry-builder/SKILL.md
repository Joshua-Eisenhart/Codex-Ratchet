---
skill_id: identity-registry-builder
name: identity-registry-builder
description: Build the first additive identity-registry scaffold from the live refinery graph without pretending the 3+3 nested layer stores already exist.
skill_type: refinement
source_type: repo_skill
applicable_layers: [INDEX, A2_HIGH_INTAKE, A2_MID_REFINEMENT, A2_LOW_CONTROL, A1_JARGONED, A1_STRIPPED, A1_CARTRIDGE]
applicable_graphs: [concept, rosetta, dependency]
inputs: [system_graph_a2_refinery, promoted_subgraph, a1_graph_projection, rosetta_v2]
outputs: [identity_registry_v1, identity_bridge_contracts_v1, identity_registry_build_audit]
related_skills: [graph-capability-auditor, nested-graph-layer-auditor, ratchet-a2-a1]
capabilities:
  can_write_repo: true
  can_only_propose: false
tool_dependencies: []
provenance: "repo-grounded first nested-graph build unit"
adapters:
  codex: system_v4/skill_specs/identity-registry-builder/SKILL.md
  gemini: system_v4/skill_specs/identity-registry-builder/SKILL.md
  shell: system_v4/skills/identity_registry_builder.py
---

# Identity Registry Builder

Use this skill when the controller is ready to materialize the first additive
identity-registry scaffold for the intended nested graph stack.

## Purpose

- seed identities only from the live refinery graph
- preserve ambiguous cases instead of auto-merging them
- attach exact-id memberships from supported projection surfaces
- emit bridge contracts that say what is strong enough now and what is still weak
- prepare the next bounded layer pass without claiming the full nested stack exists

## Execute Now

1. Load:
   - `system_v4/a2_state/graphs/system_graph_a2_refinery.json`
   - `system_v4/a2_state/graphs/promoted_subgraph.json`
   - `system_v4/a1_state/A1_GRAPH_PROJECTION.json`
   - `system_v4/a1_state/rosetta_v2.json`
2. Derive `entity_id` conservatively, in this order:
   - `properties.source_concept_id`
   - single resolvable `lineage_refs` chain root
   - `DOC::<original_path>` for source documents
   - otherwise the node's own `id`
3. Record exact-id `surface_memberships` only.
4. Record `ROSETTA_MAP` / `STRIPPED_FROM` correspondences explicitly.
5. Keep `PACKAGED_FROM` as wrapper links, not canonical identity.
6. Keep unanchored Rosetta packets external.
7. Emit:
   - `system_v4/a2_state/graphs/identity_registry_v1.json`
   - `system_v4/a2_state/graphs/identity_bridge_contracts__v1.md`
   - `system_v4/a2_state/audit_logs/IDENTITY_REGISTRY_BUILD_AUDIT__2026_03_20__v1.md`

## Quality Gates

- Do not use name overlap, tag overlap, or heuristic cross-links as identity proof.
- Do not promote `nested_graph_v1.json` to authority.
- Do not claim downstream layer stores already exist.
- Keep ambiguous and unresolved cases explicit.

---
skill_id: a2-source-family-lane-selector-operator
name: a2-source-family-lane-selector-operator
description: Audit-only selector that recommends the next bounded non-lev source-family lane from current corpus and hold state
skill_type: maintenance
source_type: repo_skill
applicable_layers: [A2_MID_REFINEMENT, A2_LOW_CONTROL]
applicable_graphs: [runtime, control, a2_mid_refinement_graph_v1]
inputs: [repo_root, report_json_path, report_md_path, packet_path]
outputs: [a2_source_family_lane_selection_report, a2_source_family_lane_selection_packet]
related_skills: [a2-skill-source-intake-operator, a2-research-deliberation-operator, a2-lev-agents-promotion-operator]
capabilities:
  can_write_repo: false
  can_only_propose: true
  reads_graph: true
tool_dependencies: []
provenance: "Ratchet-native selector slice that recommends the next bounded non-lev source-family lane after current lev, next-state, graph, and EverMem holds"
adapters:
  codex: system_v4/skill_specs/a2-source-family-lane-selector-operator/SKILL.md
  shell: system_v4/skills/a2_source_family_lane_selector_operator.py
---

# A2 Source-Family Lane Selector Operator

Use this skill when the current repo has no open lev candidate, the held lanes
must stay held, and the system needs one explicit bounded recommendation for the
next non-lev source-family lane.

## Purpose

- read the current source corpus, tracker, build plan, and imported-cluster map
- respect the current controller holds instead of widening them by momentum
- recommend one next bounded source-family lane and one first slice id, or emit an explicit hold when none are honestly admissible
- emit one repo-held report and one compact packet

## Execute Now

1. Read:
   - [SKILL_SOURCE_CORPUS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/SKILL_SOURCE_CORPUS.md)
   - [REPO_SKILL_INTEGRATION_TRACKER.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/REPO_SKILL_INTEGRATION_TRACKER.md)
   - [SYSTEM_SKILL_BUILD_PLAN.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/SYSTEM_SKILL_BUILD_PLAN.md)
   - [system_v4/V4_IMPORTED_SKILL_CLUSTER_MAP__CURRENT.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/V4_IMPORTED_SKILL_CLUSTER_MAP__CURRENT.md)
   - current hold reports for lev, next-state, EverMem, and graph-sidecar work
2. Keep this slice audit-only.
3. Recommend one next lane and one fallback lane only if they stay bounded and source-grounded.

## Quality Gates

- Do not reopen lev by absence of a current candidate.
- Do not reinterpret held next-state, graph, or EverMem work as implicitly ready.
- Do not widen into runtime mutation, training, migration, or service bootstrap.
- Keep the output honest even if no next lane is currently admissible.

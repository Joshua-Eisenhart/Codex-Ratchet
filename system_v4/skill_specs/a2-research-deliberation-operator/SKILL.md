---
skill_id: a2-research-deliberation-operator
name: a2-research-deliberation-operator
description: Compose a bounded local research/deliberation cluster over the existing autoresearch and llm-council skills, without claiming the full lev-research or CDO stack is ported.
skill_type: maintenance
source_type: repo_skill
applicable_layers: [A2_MID_REFINEMENT, B_ADJUDICATED]
applicable_graphs: [runtime, control, a2_mid_refinement_graph_v1]
inputs: [question, state, generator, evaluator, candidates, report_path]
outputs: [deliberation_report]
related_skills: [autoresearch-operator, llm-council-operator, a2-tracked-work-operator]
capabilities:
  can_write_repo: true
  can_only_propose: false
tool_dependencies: []
provenance: "lev-os/agents lev-research + cdo retooled into a bounded Ratchet research/deliberation cluster slice"
adapters:
  codex: system_v4/skill_specs/a2-research-deliberation-operator/SKILL.md
  shell: system_v4/skills/a2_research_deliberation_operator.py
---

# A2 Research Deliberation Operator

Use this skill when we want the first honest `research / deliberation` cluster
slice to be real in `system_v4` without pretending the whole external research
stack is already ported.

## Purpose

- keep the first `lev-research` / `cdo` slice bounded and local
- compose existing Ratchet skills instead of only tracking them in docs
- emit one repo-held report for the current local research/deliberation route

## Execute Now

1. Read:
   - [V4_IMPORTED_SKILL_CLUSTER_MAP__CURRENT.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/V4_IMPORTED_SKILL_CLUSTER_MAP__CURRENT.md)
   - [SKILL_SOURCE_CORPUS.md](/home/ratchet/Desktop/Codex%20Ratchet/SKILL_SOURCE_CORPUS.md)
   - [SYSTEM_SKILL_BUILD_PLAN.md](/home/ratchet/Desktop/Codex%20Ratchet/SYSTEM_SKILL_BUILD_PLAN.md)
2. Use one of two bounded routes:
   - explicit candidates -> local council adjudication
   - seeded state + generator + evaluator -> local autoresearch, then council adjudication
3. Emit one report describing the route, candidates, accepted set, and non-goals.

## Default Outputs

When no explicit path is supplied, write:

- `system_v4/a2_state/audit_logs/A2_RESEARCH_DELIBERATION_REPORT__CURRENT__v1.json`
- `system_v4/a2_state/audit_logs/A2_RESEARCH_DELIBERATION_REPORT__CURRENT__v1.md`

## Quality Gates

- Do not call external search, timetravel, valyu, oracle, or web tools here.
- Do not import the persistent CDO team/workflow scaffolding.
- Do not claim the full research stack is live because this slice exists.
- Keep the first slice honest: local, bounded, and repo-held.

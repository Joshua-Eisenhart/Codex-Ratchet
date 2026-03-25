---
skill_id: a2-lev-agents-promotion-operator
name: a2-lev-agents-promotion-operator
description: Audit-only operator that ranks the next lev-os/agents cluster to promote into Ratchet-native form
skill_type: maintenance
source_type: repo_skill
applicable_layers: [A2_MID_REFINEMENT, A2_LOW_CONTROL]
applicable_graphs: [runtime, control, a2_mid_refinement_graph_v1]
inputs: [repo_root, report_json_path, report_md_path, packet_path]
outputs: [a2_lev_agents_promotion_report, a2_lev_agents_promotion_packet]
related_skills: [a2-skill-source-intake-operator, a2-tracked-work-operator, a2-workshop-analysis-gate-operator]
capabilities:
  can_write_repo: false
  reads_graph: true
tool_dependencies: []
provenance: "Ratchet-native audit slice over the local lev-os/agents corpus that recommends the next bounded imported cluster promotion"
adapters:
  codex: system_v4/skill_specs/a2-lev-agents-promotion-operator/SKILL.md
  shell: system_v4/skills/a2_lev_agents_promotion_operator.py
---

# A2 lev-os/agents Promotion Operator

Use this skill when the local `lev-os/agents` corpus is present and we need one
bounded repo-held recommendation for the next imported cluster to promote into
Ratchet-native form.

## Purpose

- read the local `lev-os/agents` curated and library corpora
- compare them against already-landed imported cluster slices
- recommend one next bounded lev-os/agents cluster
- emit one repo-held report and one compact packet

## Execute Now

1. Read:
   - [system_v4/V4_IMPORTED_SKILL_CLUSTER_MAP__CURRENT.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/V4_IMPORTED_SKILL_CLUSTER_MAP__CURRENT.md)
   - [SKILL_SOURCE_CORPUS.md](/home/ratchet/Desktop/Codex%20Ratchet/SKILL_SOURCE_CORPUS.md)
   - the local `lev-os/agents` curated corpus under [work/reference_repos/lev-os/agents/skills](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills)
2. Keep this slice audit-only.
3. Recommend one next cluster and one first bounded slice id.

## Quality Gates

- Do not claim the whole `lev-os/agents` corpus is imported.
- Do not widen into runtime integration from this slice alone.
- Keep the output explicit about `keep / adapt / mine / skip` style treatment.

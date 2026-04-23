---
skill_id: a2-lev-architecture-fitness-operator
name: a2-lev-architecture-fitness-operator
description: Emit one bounded repo-held audit over the lev architecture/fitness guidance seam without importing generic review authority, ADR/C4 broadness, migration, or runtime ownership.
skill_type: maintenance
source_type: repo_skill
applicable_layers: [A2_MID_REFINEMENT, A2_LOW_CONTROL]
applicable_graphs: [runtime, control, a2_mid_refinement_graph_v1]
inputs: [repo_root, candidate, report_json_path, report_md_path, packet_path]
outputs: [lev_architecture_fitness_report, lev_architecture_fitness_packet]
related_skills: [a2-lev-agents-promotion-operator, a2-lev-autodev-loop-audit-operator, a2-brain-surface-refresher]
capabilities:
  can_write_repo: false
  can_only_propose: true
  reads_graph: true
tool_dependencies: []
provenance: "lev-os/agents arch adapted for bounded quality-attribute/tradeoff/fitness guidance, with lev-builder mined only for placement/migration context"
adapters:
  codex: system_v4/skill_specs/a2-lev-architecture-fitness-operator/SKILL.md
  shell: system_v4/skills/a2_lev_architecture_fitness_operator.py
---

# A2 lev Architecture Fitness Operator

Use this skill when the current lev-os/agents promotion report points at the
architecture / fitness / review cluster and we need one bounded audit over
candidate Ratchet change guidance before claiming any broader architecture
review or migration behavior.

## Purpose

- read the current lev-os/agents promotion report and packet
- audit the local `arch` seam with `lev-builder` as background-only context
- emit one repo-held report and one packet only
- keep non-goals explicit so this does not turn into generic review authority,
  full ADR/C4 generation, migration, patching, or runtime ownership

## Execute Now

1. Read:
   - [A2_LEV_AGENTS_PROMOTION_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_LEV_AGENTS_PROMOTION_REPORT__CURRENT__v1.json)
   - [A2_LEV_AGENTS_PROMOTION_PACKET__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_LEV_AGENTS_PROMOTION_PACKET__CURRENT__v1.json)
   - [A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.json)
   - [arch](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/arch/SKILL.md)
   - [arch SYSTEM_PROMPT](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/arch/SYSTEM_PROMPT.md)
   - background only: [lev-builder](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/lev-builder/SKILL.md)
2. Keep the slice bounded to quality attributes, candidate approaches, tradeoffs, bounded fitness-function proposals, and review-trigger thresholds only.
3. Emit one report and one packet only.

## Quality Gates

- Do not import generic architecture-review authority.
- Do not emit full ADR or C4 artifacts as the required first-slice output.
- Do not claim PR verdict authority such as `APPROVE` or `REQUEST_CHANGES`.
- Do not claim patch, migration, registry, or commit ownership.
- Do not claim Leviathan builder/runtime ownership.
- Do not claim that Ratchet now has a live architecture-governance runtime.

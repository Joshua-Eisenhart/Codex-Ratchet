---
id: "SKILL::wiggle-lane-runner"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# wiggle-lane-runner
**Node ID:** `SKILL::wiggle-lane-runner`

## Description
Spawn parallel A1 narrative lanes with different biases, compare outputs, merge the strongest before B adjudication.

## Properties
- **skill_type**: agent
- **source_type**: repo_skill
- **source_path**: system_v4/skill_specs/wiggle-lane-runner/SKILL.md
- **status**: active
- **applicable_layers**: ["A1_JARGONED", "A1_STRIPPED", "A1_CARTRIDGE"]
- **applicable_trust_zones**: ["A1_JARGONED", "A1_STRIPPED", "A1_CARTRIDGE"]
- **applicable_graphs**: ["concept", "dependency", "rosetta"]
- **inputs**: ["candidate_ids", "graph_nodes", "lane_configs"]
- **outputs**: ["lane_results", "comparison_matrix", "merged_strategy_packet"]
- **adapters**: {"codex": "system_v4/skill_specs/wiggle-lane-runner/SKILL.md", "gemini": "system_v4/skill_specs/wiggle-lane-runner/SKILL.md", "shell": "system_v4/skills/wiggle_lane_runner.py"}
- **related_skills**: ["a1-brain", "ratchet-reduce", "ratchet-overseer", "graveyard-lawyer"]

## Outward Relations
- **RELATED_TO** → [[a1-brain]]
- **RELATED_TO** → [[ratchet-reduce]]
- **RELATED_TO** → [[ratchet-overseer]]
- **RELATED_TO** → [[graveyard-lawyer]]
- **SKILL_OPERATES_ON** → [[a1_branch_exploration_contract]]

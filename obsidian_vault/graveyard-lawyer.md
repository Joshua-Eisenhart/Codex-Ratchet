---
id: "SKILL::graveyard-lawyer"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# graveyard-lawyer
**Node ID:** `SKILL::graveyard-lawyer`

## Description
Re-argue rejected structures. Find bad kills, premature parking, conflation kills, or new evidence that justifies reopening.

## Properties
- **skill_type**: agent
- **source_type**: repo_skill
- **source_path**: system_v4/skill_specs/graveyard-lawyer/SKILL.md
- **status**: active
- **applicable_layers**: ["GRAVEYARD", "B_ADJUDICATED", "SIM_EVIDENCED"]
- **applicable_trust_zones**: ["GRAVEYARD", "B_ADJUDICATED", "SIM_EVIDENCED"]
- **applicable_graphs**: ["graveyard", "runtime", "dependency"]
- **inputs**: ["graveyard_records", "routing_state", "graph_nodes"]
- **outputs**: ["reopen_candidates", "reopen_arguments", "rescue_proposals"]
- **adapters**: {"codex": "system_v4/skill_specs/graveyard-lawyer/SKILL.md", "gemini": "system_v4/skill_specs/graveyard-lawyer/SKILL.md", "shell": "system_v4/skills/graveyard_lawyer.py"}
- **related_skills**: ["ratchet-verify", "ratchet-overseer", "b-kernel", "sim-engine"]

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
- **RELATED_TO** → [[ratchet-overseer]]
- **RELATED_TO** → [[b-kernel]]
- **RELATED_TO** → [[sim-engine]]
- **SKILL_OPERATES_ON** → [[elimination_over_truth]]
- **SKILL_OPERATES_ON** → [[deterministic_dual_replay]]

## Inward Relations
- [[ratchet-overseer]] → **RELATED_TO**
- [[wiggle-lane-runner]] → **RELATED_TO**

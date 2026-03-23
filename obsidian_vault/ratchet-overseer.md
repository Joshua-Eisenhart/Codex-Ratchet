---
id: "SKILL::ratchet-overseer"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# ratchet-overseer
**Node ID:** `SKILL::ratchet-overseer`

## Description
Monitor ratchet convergence — watch acceptance rates, SIM kill rates, attractor density, and alert on stall/drift.

## Properties
- **skill_type**: supervisor
- **source_type**: repo_skill
- **source_path**: system_v4/skill_specs/ratchet-overseer/SKILL.md
- **status**: active
- **applicable_layers**: ["B_ADJUDICATED", "SIM_EVIDENCED", "GRAVEYARD"]
- **applicable_trust_zones**: ["B_ADJUDICATED", "SIM_EVIDENCED", "GRAVEYARD"]
- **applicable_graphs**: ["runtime", "graveyard", "dependency"]
- **inputs**: ["batch_summaries", "invocation_log", "survivor_ledger", "graveyard", "sim_evidence"]
- **outputs**: ["convergence_report", "drift_alerts", "plateau_diagnosis"]
- **adapters**: {"codex": "system_v4/skill_specs/ratchet-overseer/SKILL.md", "gemini": "system_v4/skill_specs/ratchet-overseer/SKILL.md", "shell": "system_v4/skills/ratchet_overseer.py"}
- **related_skills**: ["ratchet-verify", "graveyard-lawyer", "run-real-ratchet"]

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
- **RELATED_TO** → [[graveyard-lawyer]]
- **RELATED_TO** → [[run-real-ratchet]]
- **SKILL_OPERATES_ON** → [[four_layer_trust_architecture]]
- **SKILL_OPERATES_ON** → [[FOUR_LAYER_TRUST_SEPARATION]]
- **SKILL_OPERATES_ON** → [[COUPLED_LADDER_RATCHET]]

## Inward Relations
- [[graph-capability-auditor]] → **RELATED_TO**
- [[graveyard-lawyer]] → **RELATED_TO**
- [[wiggle-lane-runner]] → **RELATED_TO**

---
id: "SKILL::differential-tester"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# differential-tester
**Node ID:** `SKILL::differential-tester`

## Description
Differential Tester

## Properties
- **skill_type**: verification
- **source_type**: python_module
- **source_path**: system_v4/skills/differential_tester.py
- **status**: active
- **applicable_layers**: ["SIM_EVIDENCED"]
- **applicable_trust_zones**: ["SIM_EVIDENCED"]
- **applicable_graphs**: []
- **inputs**: ["runtime_state", "candidates", "probes"]
- **outputs**: ["diff_test_result", "disagreements"]
- **adapters**: {"shell": "system_v4/skills/differential_tester.py"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
- **SKILL_OPERATES_ON** → [[deterministic_dual_replay]]
- **SKILL_OPERATES_ON** → [[DUAL_REPLAY_DETERMINISM_REQUIREMENT]]

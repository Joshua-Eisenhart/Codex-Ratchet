---
id: "SKILL::witness-recorder"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# witness-recorder
**Node ID:** `SKILL::witness-recorder`

## Description
Witness Recorder

## Properties
- **skill_type**: bridge
- **source_type**: python_module
- **source_path**: system_v4/skills/witness_recorder.py
- **status**: active
- **applicable_layers**: ["SIM_EVIDENCED"]
- **applicable_trust_zones**: ["SIM_EVIDENCED"]
- **applicable_graphs**: []
- **inputs**: ["witness"]
- **outputs**: ["witness_corpus"]
- **adapters**: {"shell": "system_v4/skills/witness_recorder.py"}
- **related_skills**: []

## Outward Relations
- **SKILL_OPERATES_ON** → [[coupled_structural_evidence_ladders]]
- **SKILL_OPERATES_ON** → [[TERM_RATCHET_THROUGH_EVIDENCE]]

## Inward Relations
- [[intent-control-surface-builder]] → **RELATED_TO**
- [[runtime-context-snapshot]] → **RELATED_TO**
- [[a2-next-state-signal-adaptation-audit-operator]] → **RELATED_TO**
- [[a2-next-state-directive-signal-probe-operator]] → **RELATED_TO**
- [[a2-next-state-improver-context-bridge-audit-operator]] → **RELATED_TO**

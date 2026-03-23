---
id: "SKILL::property-pressure-tester"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# property-pressure-tester
**Node ID:** `SKILL::property-pressure-tester`

## Description
Property Pressure Tester

## Properties
- **skill_type**: verification
- **source_type**: python_module
- **source_path**: system_v4/skills/property_pressure_tester.py
- **status**: active
- **applicable_layers**: ["SIM_EVIDENCED"]
- **applicable_trust_zones**: ["SIM_EVIDENCED"]
- **applicable_graphs**: []
- **inputs**: ["runtime_state", "invariants", "perturbations"]
- **outputs**: ["pressure_result", "witness"]
- **adapters**: {"shell": "system_v4/skills/property_pressure_tester.py"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
- **SKILL_OPERATES_ON** → [[coupled_structural_evidence_ladders]]

---
id: "SKILL::fep-regulation-operator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# fep-regulation-operator
**Node ID:** `SKILL::fep-regulation-operator`

## Description
FEP Regulation Operator

## Properties
- **skill_type**: refinement
- **source_type**: python_module
- **source_path**: system_v4/skills/fep_regulation_operator.py
- **status**: active
- **applicable_layers**: ["A2_MID_REFINEMENT"]
- **applicable_trust_zones**: ["A2_MID_REFINEMENT"]
- **applicable_graphs**: ["a2_mid_refinement_graph_v1"]
- **inputs**: ["runtime_state", "observation"]
- **outputs**: ["regulated_state", "regulation_result"]
- **adapters**: {"shell": "system_v4/skills/fep_regulation_operator.py"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
- **SKILL_OPERATES_ON** → [[ENTROPIC_MONISM_AND_ALLOWABLE_MATH]]

---
id: "SKILL::z3-cegis-refiner"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# z3-cegis-refiner
**Node ID:** `SKILL::z3-cegis-refiner`

## Description
Z3 CEGIS Refiner

## Properties
- **skill_type**: refinement
- **source_type**: python_module
- **source_path**: system_v4/skills/z3_cegis_refiner.py
- **status**: active
- **applicable_layers**: ["B_ADJUDICATED"]
- **applicable_trust_zones**: ["B_ADJUDICATED"]
- **applicable_graphs**: []
- **inputs**: ["runtime_state", "candidate"]
- **outputs**: ["candidate", "witness", "cegis_history"]
- **adapters**: {"shell": "system_v4/skills/z3_cegis_refiner.py"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
- **SKILL_OPERATES_ON** → [[constraint_ladder_contracts]]
- **SKILL_OPERATES_ON** → [[constraint_manifold_formal_derivation]]

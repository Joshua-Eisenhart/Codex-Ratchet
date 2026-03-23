---
id: "SKILL::z3-constraint-checker"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# z3-constraint-checker
**Node ID:** `SKILL::z3-constraint-checker`

## Description
Z3 Constraint Checker

## Properties
- **skill_type**: verification
- **source_type**: python_module
- **source_path**: system_v4/skills/z3_constraint_checker.py
- **status**: active
- **applicable_layers**: ["B_ADJUDICATED"]
- **applicable_trust_zones**: ["B_ADJUDICATED"]
- **applicable_graphs**: []
- **inputs**: ["runtime_state", "constraints"]
- **outputs**: ["constraint_result", "witness"]
- **adapters**: {"shell": "system_v4/skills/z3_constraint_checker.py"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
- **SKILL_OPERATES_ON** → [[constraint_ladder_contracts]]
- **SKILL_OPERATES_ON** → [[constraint_manifold_formal_derivation]]
- **SKILL_OPERATES_ON** → [[base_constraints_ledger_bc01_to_bc12]]
- **SKILL_OPERATES_ON** → [[root_constraints_f01_n01]]
- **SKILL_OPERATES_ON** → [[CONSTRAINT_MANIFOLD_FORMAL_DERIVATION]]
- **SKILL_OPERATES_ON** → [[ROOT_CONSTRAINTS_F01_N01]]
- **SKILL_OPERATES_ON** → [[BASE_CONSTRAINTS_LEDGER_BC01_BC12]]

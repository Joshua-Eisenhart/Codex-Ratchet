---
id: "A1_CARTRIDGE::AUTO_GO_ON_RULE"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# AUTO_GO_ON_RULE_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::AUTO_GO_ON_RULE`

## Description
Multi-lane adversarial examination envelope for AUTO_GO_ON_RULE

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: auto_go_on_rule is structurally necessary because: Auto go-on allowed only when: thread completed one bounded pass AND emitted explicit bounded continuation contract (NEXT
- **adversarial_negative**: If auto_go_on_rule is removed, the following breaks: dependency chain on auto_go_on, continuation, policy
- **success_condition**: SIM produces stable output when auto_go_on_rule is present
- **fail_condition**: SIM diverges or produces contradictory output without auto_go_on_rule
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[AUTO_GO_ON_RULE]]

## Inward Relations
- [[AUTO_GO_ON_RULE_COMPILED]] → **COMPILED_FROM**

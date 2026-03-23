---
id: "A1_CARTRIDGE::TEN_NEGATIVE_CLASSES"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# TEN_NEGATIVE_CLASSES_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::TEN_NEGATIVE_CLASSES`

## Description
Multi-lane adversarial examination envelope for TEN_NEGATIVE_CLASSES

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: ten_negative_classes is structurally necessary because: 10 mandatory negative classes: PRIMITIVE_EQUALS, CLASSICAL_TIME, PRIMITIVE_PROBABILITY, EUCLIDEAN_METRIC, COMMUTATIVE_AS
- **adversarial_negative**: If ten_negative_classes is removed, the following breaks: dependency chain on negatives, falsification, classical_residue
- **success_condition**: SIM produces stable output when ten_negative_classes is present
- **fail_condition**: SIM diverges or produces contradictory output without ten_negative_classes
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[TEN_NEGATIVE_CLASSES]]

## Inward Relations
- [[TEN_NEGATIVE_CLASSES_COMPILED]] → **COMPILED_FROM**

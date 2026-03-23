---
id: "A1_STRIPPED::A0_DETERMINISTIC_CANONICALIZATION"
type: "REFINED_CONCEPT"
layer: "A1_STRIPPED"
authority: "CROSS_VALIDATED"
---

# A0_DETERMINISTIC_CANONICALIZATION
**Node ID:** `A1_STRIPPED::A0_DETERMINISTIC_CANONICALIZATION`

## Description
A0 is the deterministic bridge from A1 strategy to B artifacts. Canonicalization pipeline: parse → drop forbidden fields (confidence, probability, embedding) → normalize types → sort keys → serialize

## Properties
- **dropped_jargon**: []
- **required_anchors**: ["UNVERIFIED"]

## Outward Relations
- **STRIPPED_FROM** → [[a0_deterministic_canonicalization]]
- **STRUCTURALLY_RELATED** → [[a0_deterministic_canonicalization]]

## Inward Relations
- [[a0_deterministic_canonicalization]] → **ROSETTA_MAP**
- [[A0_DETERMINISTIC_CANONICALIZATION_CARTRIDGE]] → **PACKAGED_FROM**

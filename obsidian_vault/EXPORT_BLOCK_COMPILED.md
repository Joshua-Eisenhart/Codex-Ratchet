---
id: "A0_COMPILED::EXPORT_BLOCK"
type: "EXECUTION_BLOCK"
layer: "A0_COMPILED"
authority: "CROSS_VALIDATED"
---

# EXPORT_BLOCK_COMPILED
**Node ID:** `A0_COMPILED::EXPORT_BLOCK`

## Description
Deterministic A0 compilation of EXPORT_BLOCK

## Properties
- **compiled_logic**: {
  "test_target": "SIM_SPEC",
  "assertions": [
    {
      "type": "POSITIVE_STEELMAN",
      "condition": "export_block is structurally necessary because: Archived Work File: BEGIN EXPORT_BLOCK v1"
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **COMPILED_FROM** → [[EXPORT_BLOCK_CARTRIDGE]]

## Inward Relations
- [[EXPORT_BLOCK_B_STATUS]] → **ADJUDICATED_FROM**

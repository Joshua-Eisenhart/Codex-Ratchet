---
id: "A1_CARTRIDGE::INDEX_TS"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# INDEX_TS_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::INDEX_TS`

## Description
Multi-lane adversarial examination envelope for INDEX_TS

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: index_ts is structurally necessary because: Unprocessed File Type (index.ts): /** | * DOOM Overlay Demo - Play DOOM as an overlay | *
- **adversarial_negative**: If index_ts is removed, the following breaks: dependency chain on system_file_scan
- **success_condition**: SIM produces stable output when index_ts is present
- **fail_condition**: SIM diverges or produces contradictory output without index_ts
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[INDEX_TS]]

## Inward Relations
- [[INDEX_TS_COMPILED]] → **COMPILED_FROM**

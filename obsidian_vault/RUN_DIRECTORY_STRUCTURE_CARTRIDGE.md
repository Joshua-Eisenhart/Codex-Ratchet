---
id: "A1_CARTRIDGE::RUN_DIRECTORY_STRUCTURE"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# RUN_DIRECTORY_STRUCTURE_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::RUN_DIRECTORY_STRUCTURE`

## Description
Multi-lane adversarial examination envelope for RUN_DIRECTORY_STRUCTURE

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: run_directory_structure is structurally necessary because: [AUDITED] Required dirs: b_reports/, sim/, tapes/, logs/, reports/, tuning/, zip_packets/, a1_inbox/. Optional: outbox/,
- **adversarial_negative**: If run_directory_structure is removed, the following breaks: none identified
- **success_condition**: SIM produces stable output when run_directory_structure is present
- **fail_condition**: SIM diverges or produces contradictory output without run_directory_structure
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[RUN_DIRECTORY_STRUCTURE]]

## Inward Relations
- [[RUN_DIRECTORY_STRUCTURE_COMPILED]] → **COMPILED_FROM**

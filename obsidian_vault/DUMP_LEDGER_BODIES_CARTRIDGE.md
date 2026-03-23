---
id: "A1_CARTRIDGE::DUMP_LEDGER_BODIES"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# DUMP_LEDGER_BODIES_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::DUMP_LEDGER_BODIES`

## Description
Multi-lane adversarial examination envelope for DUMP_LEDGER_BODIES

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: dump_ledger_bodies is structurally necessary because: Archived Work File: BEGIN DUMP_LEDGER_BODIES v1
- **adversarial_negative**: If dump_ledger_bodies is removed, the following breaks: dependency chain on work_archive, audit_tmp
- **success_condition**: SIM produces stable output when dump_ledger_bodies is present
- **fail_condition**: SIM diverges or produces contradictory output without dump_ledger_bodies
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[DUMP_LEDGER_BODIES]]

## Inward Relations
- [[DUMP_LEDGER_BODIES_COMPILED]] → **COMPILED_FROM**

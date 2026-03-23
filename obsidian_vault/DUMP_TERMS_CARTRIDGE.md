---
id: "A1_CARTRIDGE::DUMP_TERMS"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# DUMP_TERMS_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::DUMP_TERMS`

## Description
Multi-lane adversarial examination envelope for DUMP_TERMS

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: dump_terms is structurally necessary because: Archived Work File: BEGIN DUMP_TERMS v1
- **adversarial_negative**: If dump_terms is removed, the following breaks: dependency chain on work_archive, audit_tmp
- **success_condition**: SIM produces stable output when dump_terms is present
- **fail_condition**: SIM diverges or produces contradictory output without dump_terms
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[DUMP_TERMS]]

## Inward Relations
- [[DUMP_TERMS_COMPILED]] → **COMPILED_FROM**

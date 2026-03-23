---
id: "A1_CARTRIDGE::DIRECTED_EXTRACTION_ANSWERS"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# DIRECTED_EXTRACTION_ANSWERS_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::DIRECTED_EXTRACTION_ANSWERS`

## Description
Multi-lane adversarial examination envelope for DIRECTED_EXTRACTION_ANSWERS

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: directed_extraction_answers is structurally necessary because: Archived Work File: MODE: STATE_EXTRACTION_ONLY
- **adversarial_negative**: If directed_extraction_answers is removed, the following breaks: dependency chain on work_archive, audit_tmp
- **success_condition**: SIM produces stable output when directed_extraction_answers is present
- **fail_condition**: SIM diverges or produces contradictory output without directed_extraction_answers
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[DIRECTED_EXTRACTION_ANSWERS]]

## Inward Relations
- [[DIRECTED_EXTRACTION_ANSWERS_COMPILED]] → **COMPILED_FROM**

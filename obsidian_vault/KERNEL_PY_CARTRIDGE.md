---
id: "A1_CARTRIDGE::KERNEL_PY"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# KERNEL_PY_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::KERNEL_PY`

## Description
Multi-lane adversarial examination envelope for KERNEL_PY

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: kernel_py is structurally necessary because: Unprocessed File Type (kernel.py): import re | from dataclasses import dataclass | from containers import parse_export_b
- **adversarial_negative**: If kernel_py is removed, the following breaks: dependency chain on system_file_scan
- **success_condition**: SIM produces stable output when kernel_py is present
- **fail_condition**: SIM diverges or produces contradictory output without kernel_py
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[KERNEL_PY]]

## Inward Relations
- [[KERNEL_PY_COMPILED]] → **COMPILED_FROM**

---
id: "A1_CARTRIDGE::HASHES_SHA256"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# HASHES_SHA256_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::HASHES_SHA256`

## Description
Multi-lane adversarial examination envelope for HASHES_SHA256

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: hashes_sha256 is structurally necessary because: Unprocessed File Type (HASHES.sha256): 06ae8b8987f9d9bc79b89e4dae21f05e9ef77d72d3891a916dd0b0c787e4819b  EXPORT_BLOCK.tx
- **adversarial_negative**: If hashes_sha256 is removed, the following breaks: dependency chain on system_file_scan
- **success_condition**: SIM produces stable output when hashes_sha256 is present
- **fail_condition**: SIM diverges or produces contradictory output without hashes_sha256
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[HASHES_SHA256]]

## Inward Relations
- [[HASHES_SHA256_COMPILED]] → **COMPILED_FROM**

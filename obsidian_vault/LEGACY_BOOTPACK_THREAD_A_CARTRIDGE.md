---
id: "A1_CARTRIDGE::LEGACY_BOOTPACK_THREAD_A"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# LEGACY_BOOTPACK_THREAD_A_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::LEGACY_BOOTPACK_THREAD_A`

## Description
Multi-lane adversarial examination envelope for LEGACY_BOOTPACK_THREAD_A

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: legacy_bootpack_thread_a is structurally necessary because: 32KB legacy Thread A bootpack v2.60. Defines A1 meta/boundary thread behavior: nondeterministic control, LLM failure mod
- **adversarial_negative**: If legacy_bootpack_thread_a is removed, the following breaks: dependency chain on bootpack, thread_a, legacy
- **success_condition**: SIM produces stable output when legacy_bootpack_thread_a is present
- **fail_condition**: SIM diverges or produces contradictory output without legacy_bootpack_thread_a
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[LEGACY_BOOTPACK_THREAD_A]]

## Inward Relations
- [[LEGACY_BOOTPACK_THREAD_A_COMPILED]] → **COMPILED_FROM**

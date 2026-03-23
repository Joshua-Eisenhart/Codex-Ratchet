---
id: "A1_STRIPPED::A1_QUEUE_STATUS_SURFACE"
type: "REFINED_CONCEPT"
layer: "A1_STRIPPED"
authority: "CROSS_VALIDATED"
---

# A1_QUEUE_STATUS_SURFACE
**Node ID:** `A1_STRIPPED::A1_QUEUE_STATUS_SURFACE`

## Description
6 allowed queue statuses: NO_WORK, READY_FROM_NEW_A2_HANDOFF, READY_FROM_EXISTING_FUEL, READY_FROM_A2_PREBUILT_BATCH, BLOCKED_MISSING_BOOT, BLOCKED_MISSING_ARTIFACTS. Do not use vague labels like READ

## Properties
- **dropped_jargon**: []
- **required_anchors**: ["UNVERIFIED"]

## Outward Relations
- **STRIPPED_FROM** → [[a1_queue_status_surface]]

## Inward Relations
- [[a1_queue_status_surface]] → **ROSETTA_MAP**
- [[A1_QUEUE_STATUS_SURFACE_CARTRIDGE]] → **PACKAGED_FROM**
- [[v3_spec_32_a1_queue_status_surface__v1]] → **DEPENDS_ON**
- [[v3_tools_prepare_a1_queue_status_surfaces]] → **DEPENDS_ON**
- [[v3_runtime_test_prepare_a1_queue_status_surfac]] → **DEPENDS_ON**
- [[test_prepare_a1_queue_status_surfaces_py]] → **DEPENDS_ON**

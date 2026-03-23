---
id: "A2_3::SOURCE_MAP_PASS::controller_boot_check_before_dispatch::5ad042e81be2b2e3"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "DRAFT"
---

# controller_boot_check_before_dispatch
**Node ID:** `A2_3::SOURCE_MAP_PASS::controller_boot_check_before_dispatch::5ad042e81be2b2e3`

## Description
Before dispatching: confirm active A2 surfaces readable, intake ledger readable, current worker roles identifiable, no critical unresolved break blocking. Boot-check outputs: boot_ok, known_active_lanes, strongest_recent_outputs, weakest_lane, spawn_recommendation. Weak-lane correction order: verify weakness, identify failure class (shallow/packaging/contradiction/selector/stalled), prefer bounded correction over redundant lane.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[current]]
- **DEPENDS_ON** → [[verify]]
- **DEPENDS_ON** → [[packaging]]
- **DEPENDS_ON** → [[output]]
- **DEPENDS_ON** → [[worker]]
- **DEPENDS_ON** → [[weak_lane_correction]]

## Inward Relations
- [[27_MASTER_CONTROLLER_THREAD_PROCESS__v1.md]] → **SOURCE_MAP_PASS**
- [[a2_controller_dispatch_first]] → **RELATED_TO**
- [[a2_worker_dispatch_packets]] → **RELATED_TO**
- [[a2_controller_dispatch_first_rule]] → **RELATED_TO**

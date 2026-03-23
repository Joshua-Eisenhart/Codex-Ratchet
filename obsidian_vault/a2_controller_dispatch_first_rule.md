---
id: "A2_3::SOURCE_MAP_PASS::a2_controller_dispatch_first_rule::7d681bed6f3641b7"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "NONCANON"
---

# a2_controller_dispatch_first_rule
**Node ID:** `A2_3::SOURCE_MAP_PASS::a2_controller_dispatch_first_rule::7d681bed6f3641b7`

## Description
RQ-147: A2_CONTROLLER is dispatch-first. If bounded worker packet can express the work, controller must dispatch rather than absorb. Direct controller work limited to: weighted state refresh, queue evaluation, one bounded audit pass, launch/dispatch/closeout routing.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **RELATED_TO** → [[controller_boot_check_before_dispatch]]
- **RELATED_TO** → [[a2_worker_dispatch_packets]]

## Inward Relations
- [[07_A2_OPERATIONS_SPEC.md]] → **SOURCE_MAP_PASS**
- [[a2_controller_dispatch_first]] → **RELATED_TO**

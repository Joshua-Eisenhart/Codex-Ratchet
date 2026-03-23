---
id: "A2_3::SOURCE_MAP_PASS::master_controller_entropy_routing_role::93b49fd8a98c315b"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "DRAFT"
---

# master_controller_entropy_routing_role
**Node ID:** `A2_3::SOURCE_MAP_PASS::master_controller_entropy_routing_role::93b49fd8a98c315b`

## Description
Controller is entropy-routing and problem-routing role. Spawns workers when: entropy accumulates, ratchet plateaus, lane keeps failing, new large source drop, promotion queue piling. Does NOT spawn just because parallelism is available. 10 stable role labels (Controller Master, A2H Upgrade Docs, A2H Archived State, A2H Sims, A2H Refined Fuel Non-Sims, A2M Promotion Review, A2M Contradiction Reprocess, A1 Rosetta Bridge, A1 Cartridge Judge, A1 Strategy Audit).

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **RELATED_TO** → [[no_controller_refinery_drift]]
- **DEPENDS_ON** → [[worker]]

## Inward Relations
- [[27_MASTER_CONTROLLER_THREAD_PROCESS__v1.md]] → **SOURCE_MAP_PASS**

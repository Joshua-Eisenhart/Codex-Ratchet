---
id: "A2_3::SOURCE_MAP_PASS::auto_go_on_applicator_execution::8dff784738d29d42"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "DRAFT"
---

# auto_go_on_applicator_execution
**Node ID:** `A2_3::SOURCE_MAP_PASS::auto_go_on_applicator_execution::8dff784738d29d42`

## Description
8-step execution: class gate (A2_CONTROLLER->MANUAL_REVIEW), metadata gate, stop gate, bounded-step gate, block-case gate, ceiling gate (count>=1->MANUAL_REVIEW), role purity gate, final decision. 4 possible outputs: SEND_ONE_GO_ON, STOP_NOW, ROUTE_TO_CLOSEOUT, MANUAL_REVIEW_REQUIRED. If SEND_ONE_GO_ON, emit exactly "go on" with no added prose. Records THREAD_CLASS, DECISION, REASON, CONTINUATION_COUNT, AUTO_GO_ON_ALLOWED.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[output]]
- **EXCLUDES** → [[v3_spec_42_auto_go_on_applicator__v1]]

## Inward Relations
- [[42_AUTO_GO_ON_APPLICATOR__v1.md]] → **SOURCE_MAP_PASS**
- [[B_SURVIVOR_S045_SIM_SPEC]] → **ACCEPTED_FROM**
- [[B_PARKED_S047]] → **PARKED_FROM**
- [[B_PARKED_S048]] → **PARKED_FROM**

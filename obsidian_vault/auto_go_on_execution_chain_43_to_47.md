---
id: "A2_3::SOURCE_MAP_PASS::auto_go_on_execution_chain_43_to_47::853f3e249ff4eff8"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "DRAFT"
---

# auto_go_on_execution_chain_43_to_47
**Node ID:** `A2_3::SOURCE_MAP_PASS::auto_go_on_execution_chain_43_to_47::853f3e249ff4eff8`

## Description
5-spec auto go-on execution chain: (43) EXECUTION_PATH: full pipeline from thread return through applicator to sender/closeout. (44) SENDER_PACKET: exact packet shape sent after SEND_ONE_GO_ON decision. (45) RUNNER: first runnable control-loop that consumes thread result, applies rule, sends go-on or routes. (46) THREAD_RESULT_SHAPE: normalized JSON shape with THREAD_CLASS, NEXT_STEP, IF_ONE_MORE_PASS, ROLE_AND_SCOPE, WHAT_YOU_READ, WHAT_YOU_UPDATED. (47) CYCLE_PACKET: single invocation packet consumed by runner. Together form the complete auto-continuation machinery.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[packet]]

## Inward Relations
- [[43_AUTO_GO_ON_EXECUTION_PATH__v1.md]] → **SOURCE_MAP_PASS**
- [[B_SURVIVOR_S053_SIM_SPEC]] → **ACCEPTED_FROM**
- [[B_PARKED_S055]] → **PARKED_FROM**
- [[B_PARKED_S056]] → **PARKED_FROM**

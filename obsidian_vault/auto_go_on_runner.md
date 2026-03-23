---
id: "A2_3::SOURCE_MAP_PASS::auto_go_on_runner::f55e7dfd8e0dc587"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# auto_go_on_runner
**Node ID:** `A2_3::SOURCE_MAP_PASS::auto_go_on_runner::f55e7dfd8e0dc587`

## Description
The control-loop stage that captures a thread result, routes it through the auto-go-on applicator, and produces a sender packet if authorized.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **RELATED_TO** → [[mass_extraction_runner_skill]]
- **EXCLUDES** → [[v3_spec_45_auto_go_on_runner__v1]]
- **EXCLUDES** → [[v3_tools_auto_go_on_runner]]
- **EXCLUDES** → [[auto_go_on_runner_py]]
- **DEPENDS_ON** → [[packet]]

## Inward Relations
- [[45_AUTO_GO_ON_RUNNER__v1.md]] → **SOURCE_MAP_PASS**
- [[v3_spec_45_auto_go_on_runner__v1]] → **DEPENDS_ON**
- [[v3_tools_run_auto_go_on_cycle]] → **DEPENDS_ON**

---
id: "A2_3::SOURCE_MAP_PASS::first_parallel_codex_wave_packet::113185f74f5e0615"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "DRAFT"
---

# first_parallel_codex_wave_packet
**Node ID:** `A2_3::SOURCE_MAP_PASS::first_parallel_codex_wave_packet::113185f74f5e0615`

## Description
First concrete parallel launch: C0 (A2_CONTROLLER, maintain state, monitor W1) + W1 (A2_WORKER, A2_HIGH_REFINERY_PASS on exact RUN_NOW refinedfuel set: 4 BATCH entries for constraints_entropy/constraints term conflict/source map). W2 empty, A1 empty (NO_WORK). AUTO_GO_ON_ALLOWED=NO by default. Wave ends when W1 returns bounded result and controller records decision.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[constraints]]
- **DEPENDS_ON** → [[worker]]
- **EXCLUDES** → [[v3_spec_67_first_parallel_codex_wave_packet]]
- **EXCLUDES** → [[v3_spec_68_first_parallel_codex_wave_operat]]
- **EXCLUDES** → [[v3_spec_69_first_parallel_codex_wave_c0_eva]]
- **EXCLUDES** → [[v3_spec_70_first_parallel_codex_wave_launch]]
- **STRUCTURALLY_RELATED** → [[first_parallel_wave_operator_handoff_68_to_70]]

## Inward Relations
- [[67_FIRST_PARALLEL_CODEX_WAVE_PACKET__v1.md]] → **SOURCE_MAP_PASS**
- [[v3_spec_67_first_parallel_codex_wave_packet]] → **DEPENDS_ON**
- [[first_parallel_codex_wave_launch_handoff]] → **EXCLUDES**

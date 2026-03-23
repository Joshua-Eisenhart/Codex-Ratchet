---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_generate_density_matrix_packet::b3548a69b11a74c3"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_generate_density_matrix_packet
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_generate_density_matrix_packet::b3548a69b11a74c3`

## Description
generate_density_matrix_packet.py (10546B): #!/usr/bin/env python3 """ Generate a single A1_TO_A0_STRATEGY_ZIP packet that ratchets concrete QIT-aligned terms (e.g. density_matrix) without introducing FORMULA/equality primitives.  This is an A1-side artifact generator (high entropy), but it em

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[generator]]
- **DEPENDS_ON** → [[packet]]
- **STRUCTURALLY_RELATED** → [[v3_runtime_sim_density_matrix]]

## Inward Relations
- [[test_run_a1_autoratchet_cycle_audit.py]] → **SOURCE_MAP_PASS**
- [[generate_density_matrix_packet_py]] → **STRUCTURALLY_RELATED**
- [[sim_density_matrix_py]] → **EXCLUDES**

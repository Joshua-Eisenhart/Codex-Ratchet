---
id: "A2_3::SOURCE_MAP_PASS::control_plane_03_mutation_path_rules::160c20b5052f5efb"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# control_plane_03_mutation_path_rules
**Node ID:** `A2_3::SOURCE_MAP_PASS::control_plane_03_mutation_path_rules::160c20b5052f5efb`

## Description
03_MUTATION_PATH_RULES.md (995B):  # Mutation Path Rules  ## Single allowed mutation path Mutation to canonical state is permitted only via:  1) A1 emits: `A1_TO_A0_STRATEGY_ZIP` 2) A0 compiles deterministically into: `A0_TO_B_EXPORT_BATCH_ZIP` 3) B admits changes from the single `EXPORT_BLOCK vN` inside the ZIP  No other path may m

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[03_mutation_path_rules]]
- **DEPENDS_ON** → [[export_block]]
- **DEPENDS_ON** → [[changes]]
- **STRUCTURALLY_RELATED** → [[sysrepair_v2_03_mutation_path_rules]]
- **STRUCTURALLY_RELATED** → [[sysrepair_v3_03_mutation_path_rules]]
- **STRUCTURALLY_RELATED** → [[sysrepair_v4_03_mutation_path_rules]]
- **EXCLUDES** → [[single_mutation_path_rule]]
- **EXCLUDES** → [[single_mutation_path]]

## Inward Relations
- [[00_README.md]] → **SOURCE_MAP_PASS**
- [[03_mutation_path_rules]] → **STRUCTURALLY_RELATED**

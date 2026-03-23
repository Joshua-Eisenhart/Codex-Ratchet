TASK_ID: TSK_A1_CONSOLIDATION_PREPACK__MERGE_AND_ORDER
TASK_KIND: A1_CONSOLIDATION_PREPACK
TASK_MODE: DETERMINISTIC_ORDERING

INPUT_FILES:
- output/CONSOLIDATED_SOURCE_REGISTRY__A1_CONSOLIDATION_PREPACK__v1.md
- output/CONFLICT_AND_DEDUP_REPORT__A1_CONSOLIDATION_PREPACK__v1.md

OUTPUT_FILES:
- output/TERM_FAMILY_ORDERING_REPORT__A1_CONSOLIDATION_PREPACK__v1.md
- output/NEGATIVE_AND_RESCUE_MERGE_REPORT__A1_CONSOLIDATION_PREPACK__v1.md
- output/A1_STRATEGY_v1.json

INSTRUCTIONS:
- Merge worker outputs into one ordered strategy candidate.
- Preserve substrate-before-axis ordering.
- Preserve negative classes and rescue lineage with the correct families.
- Record all dropped, partitioned, or merged collisions explicitly.

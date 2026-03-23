TASK_ID: TSK_A1_CONSOLIDATION_PREPACK__INGEST_AND_VALIDATE
TASK_KIND: A1_CONSOLIDATION_PREPACK
TASK_MODE: FAIL_CLOSED

INPUT_FILES:
- input/*.zip
- input/*.json
- input/*.md

OUTPUT_FILES:
- output/CONSOLIDATED_SOURCE_REGISTRY__A1_CONSOLIDATION_PREPACK__v1.md
- output/CONFLICT_AND_DEDUP_REPORT__A1_CONSOLIDATION_PREPACK__v1.md

INSTRUCTIONS:
- Inventory all worker inputs.
- Record bundle/source ids and available family outputs.
- Reject malformed inputs or missing provenance.
- Do not silently coerce incompatible structures.

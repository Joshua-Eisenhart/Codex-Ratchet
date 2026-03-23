TASK_ID: TSK_A1_CONSOLIDATION_PREPACK__EMIT_AND_AUDIT
TASK_KIND: A1_CONSOLIDATION_PREPACK
TASK_MODE: FAIL_CLOSED

INPUT_FILES:
- output/TERM_FAMILY_ORDERING_REPORT__A1_CONSOLIDATION_PREPACK__v1.md
- output/NEGATIVE_AND_RESCUE_MERGE_REPORT__A1_CONSOLIDATION_PREPACK__v1.md
- output/A1_STRATEGY_v1.json

OUTPUT_FILES:
- output/TRANSPORT_READINESS_AND_FAIL_CLOSED_REPORT__A1_CONSOLIDATION_PREPACK__v1.md

INSTRUCTIONS:
- Verify that exactly one `A1_STRATEGY_v1.json` candidate was emitted.
- Verify no mutation containers are present.
- Verify unresolved target collisions, schema conflicts, or missing provenance cause FAIL.
- Report whether the output is ready for later `A1_TO_A0_STRATEGY_ZIP` packaging.

# Task 3: Bounded Retrieval Sidecar Ingestion Test
Model Recommendation: `Gemini 3 Flash`

MISSION:
Implement a LightRAG/HippoRAG ingestion test over a tiny, bounded slice of the provenance corpus to prove the integration works before scaling.

INSTRUCTIONS:
1. Examine `system_v4/skills/qit_retrieval_sidecar.py`.
2. Construct a bounded test function `test_bounded_ingestion()` that parses exactly two nodes from `full_stack_provenance_graph.json` (e.g., `core_docs/QIT_GRAPH_SCHEMA.md` and `core_docs/QIT_GRAPH_RUNTIME_MODEL.md`).
3. Embed and index them in the sidecar engine, gracefully stubbing out missing local LLM keys, marking them simply as `EMBED_PENDING` if needed.
4. Execute the sidecar script manually using Python to prove it initializes the retrieval pipeline safely without memory spiraling or quota errors.
5. Write your test output summary to `system_v4/a2_state/antigravity_prompt_batches/safe_pack/task3_results.md`.

# Task 1: Fix and Verify Multi-Repo Provenance Ingestion
Model Recommendation: `Gemini 3.1 Pro (High)`

MISSION:
Verify and harden the ingestion pipeline in `system_v4/skills/graph_intake/multi_repo_ingestor.py` so that it parses exact files specified in the `full_stack_ingestion_manifest.json` correctly without glob-bombing `.git` or `.venv` directories.

INSTRUCTIONS:
1. Examine `multi_repo_ingestor.py` and `full_stack_ingestion_manifest.json`.
2. Ensure the ingestion correctly resolves both explicit files and safe globs across `Codex Ratchet` and `Leviathan-Arbitrage`.
3. If `Leviathan-Arbitrage` paths are missing local checkouts, emit a placeholder node with `authority_class=evidence_returns` rather than crashing.
4. Run the ingestion explicitly: `./.venv_spec_graph/bin/python system_v4/skills/graph_intake/multi_repo_ingestor.py` and verify `system_v4/a2_state/graphs/full_stack_provenance_graph.json` contains valid data.
5. Create a clean validation summary file: `system_v4/a2_state/antigravity_prompt_batches/safe_pack/task1_results.md` detailing how many nodes of each authority class successfully mapped.

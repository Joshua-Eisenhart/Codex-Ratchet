# Codex Ratchet old-sim processing task — P07_duplicate_lineage_and_archive_candidates

Route: codex1
Repo: /Users/joshuaeisenhart/Codex-Ratchet
Work package JSON: system_v5/evidence/old_sim_processing/work_packages_20260608.json
Package id: P07_duplicate_lineage_and_archive_candidates

## Mission
Audit duplicate basenames, lineage hazards, and archive/delete candidates. Propose moves only; do not delete.

## Read first
- AGENTS.md
- system_v5/docs/CURRENT_DOCS_MAP.md
- system_v5/docs/LLM_CONTROLLER_CONTRACT.md
- system_v5/docs/LEGO_SIM_CONTRACT.md
- system_v5/docs/maintenance/old_sim_reuse_index_20260608.md
- system_v5/docs/maintenance/three_engine_source_claim_audit_20260608.md
- system_v5/docs/maintenance/sim_tool_library_coverage_20260608.md
- system_v5/evidence/old_sim_reuse_index_20260608.json
- system_v5/evidence/three_engine_source_claim_audit_20260608.json
- system_v5/evidence/sim_tool_library_coverage_20260608.json
- this package row list inside system_v5/evidence/old_sim_processing/work_packages_20260608.json

## Source-truth correction
- Do not trust `packages_used`, `aligned_packages_load_bearing`, or an envelope-validator pass by itself.
- For current three-engine envelopes, use `scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed`; use `--strict-source-backed` when deciding whether a declared package claim is clean enough to become future fuel.
- Treat the coverage audit as a gap signal: current JAX/PyTorch lanes are narrow unless they use full sim libraries such as `diffrax`, `dynamiqs`, `qutip`, `quimb`, `netket`, `toponetx`, `gudhi`, `torch_ga`, `torch_geometric`, `geomstats`, or `e3nn` in a claim-carrying way.

## Hard boundaries
- Do not delete files.
- Do not stage, commit, push, rebase, or git-clean.
- Do not rewrite shared result trees.
- Do not promote old results to canonical/admitted.
- Treat old docs/logs/results as mines for math objects, controls, negatives, tool recipes, and rebuild fuel.
- Worker prose is not evidence; write artifacts and include exact paths.

## Required output
1. Report: `system_v5/ops/old_sim_processing/reports/P07_duplicate_lineage_and_archive_candidates.md`
2. Action manifest: `system_v5/evidence/old_sim_processing/actions/P07_duplicate_lineage_and_archive_candidates_actions.json`

The action manifest must be JSON with:
```json
{
  "schema": "old_sim_action_manifest.v1",
  "package_id": "P07_duplicate_lineage_and_archive_candidates",
  "route": "codex1",
  "claim_ceiling": "classification/fuel extraction only; no deletion/promotion",
  "rows": [
    {
      "source_path": "...",
      "old_role": "...",
      "recommended_action": "keep_current|mine_into_fuel_bank|rebuild_as_micro_lego|consolidate_duplicate|archive_candidate|delete_candidate_after_replacement_verified|graveyard_keep_as_falsifier|needs_human_review",
      "safe_current_reuse": "...",
      "replacement_or_fuel_path": "... or null",
      "delete_or_archive_gate": "...",
      "required_validator": "...",
      "claim_ceiling": "...",
      "notes": "..."
    }
  ]
}
```

## Report contents
- What this package covered.
- Top reusable fuel extracted.
- Candidate micro-legos to rebuild under current tri-engine/rich-tool contracts.
- Negative controls / graveyard rows worth preserving.
- Duplicate/archive/delete candidates, but only as proposals.
- Open blockers and required validators.

## Closeout check
Run local JSON parsing on your action manifest and report exact command/output in the report. If you touched Python, run py_compile on touched Python files. Do not call the package done until report + action manifest exist.

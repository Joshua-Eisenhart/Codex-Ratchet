# Old Sim Consolidation Campaign — 2026-06-08

Status: launch plan + work-package manifest. This is not deletion authorization.

## Bottom line

The goal is good: thousands of old sims are too hard to use as-is. The safe version is not mass deletion first; it is: index -> package -> extract fuel -> rebuild/consolidate -> verify replacements -> archive/delete in a separate controller tranche.

## Non-negotiable gates

- Workers may classify, write reports, create action manifests, and propose replacements.
- Workers may not delete, stage, commit, push, rebase, or `git clean`.
- Deletion requires an exact action-manifest row plus replacement/fuel verification or explicit no-fuel duplicate justification.
- Current `three_engine_sim_result_v1` envelopes validate with `scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed`; old pass labels do not promote anything.
- For cleanup/fuel decisions, use `--strict-source-backed` or the source-claim audit to catch thin/decorative declared package claims.
- Old docs/logs/results are mines, not route authority.

## Work-package manifest

Full package JSON: `system_v5/evidence/old_sim_processing/work_packages_20260608.json`

## Package roster

| package | route | rows | expected report | expected action manifest |
|---|---|---:|---|---|
| `P00_controller_receipt_and_gates` | `controller` | 109 | `system_v5/ops/old_sim_processing/reports/P00_controller_receipt_and_gates.md` | `system_v5/evidence/old_sim_processing/actions/P00_controller_receipt_and_gates_actions.json` |
| `P01_active_tri_engine_envelopes` | `codex1` | 202 | `system_v5/ops/old_sim_processing/reports/P01_active_tri_engine_envelopes.md` | `system_v5/evidence/old_sim_processing/actions/P01_active_tri_engine_envelopes_actions.json` |
| `P02_foundation_carrier_geometry_donors` | `codex1` | 900 | `system_v5/ops/old_sim_processing/reports/P02_foundation_carrier_geometry_donors.md` | `system_v5/evidence/old_sim_processing/actions/P02_foundation_carrier_geometry_donors_actions.json` |
| `P03_qit_density_entropy_classical_baselines` | `codex2` | 900 | `system_v5/ops/old_sim_processing/reports/P03_qit_density_entropy_classical_baselines.md` | `system_v5/evidence/old_sim_processing/actions/P03_qit_density_entropy_classical_baselines_actions.json` |
| `P04_graph_topology_tool_recipes` | `codex1` | 700 | `system_v5/ops/old_sim_processing/reports/P04_graph_topology_tool_recipes.md` | `system_v5/evidence/old_sim_processing/actions/P04_graph_topology_tool_recipes_actions.json` |
| `P05_proof_symbolic_negative_controls` | `codex2` | 700 | `system_v5/ops/old_sim_processing/reports/P05_proof_symbolic_negative_controls.md` | `system_v5/evidence/old_sim_processing/actions/P05_proof_symbolic_negative_controls_actions.json` |
| `P06_bridge_axis_physics_graveyard` | `codex2` | 900 | `system_v5/ops/old_sim_processing/reports/P06_bridge_axis_physics_graveyard.md` | `system_v5/evidence/old_sim_processing/actions/P06_bridge_axis_physics_graveyard_actions.json` |
| `P07_duplicate_lineage_and_archive_candidates` | `codex1` | 793 | `system_v5/ops/old_sim_processing/reports/P07_duplicate_lineage_and_archive_candidates.md` | `system_v5/evidence/old_sim_processing/actions/P07_duplicate_lineage_and_archive_candidates_actions.json` |
| `P08_unclassified_and_workbench_triage` | `codex2` | 143 | `system_v5/ops/old_sim_processing/reports/P08_unclassified_and_workbench_triage.md` | `system_v5/evidence/old_sim_processing/actions/P08_unclassified_and_workbench_triage_actions.json` |

## Codex TUI launch shape

Use the generated prompt cards under `system_v5/ops/old_sim_processing/prompts/`.

Observed local CLI: `codex-cli 0.137.0`; on this CLI `-p` is `--profile`. The user-corrected route is Codex TUI `-p` lanes for codex1/codex2. Record the exact command/session in each receipt.

Example launch pattern, if the local profiles/sessions are available:

```text
codex -p codex1 <prompt text or pasted prompt card>
codex -p codex2 <prompt text or pasted prompt card>
```

Do not count a launched TUI as complete until its report and action manifest exist and parse.

## Current receipt status

- `P00_controller_receipt_and_gates`: controller report/action manifest exist and parse.
- `P01_active_tri_engine_envelopes`: Codex TUI `codex1` exited without required artifacts; Hermes wrote a controller-fallback report/action manifest from the package index. Parsed rows: `202`.
- `P03_qit_density_entropy_classical_baselines`: Codex TUI `codex2` exited with termination status before required artifacts; Hermes wrote a controller-fallback report/action manifest from the package index. Parsed rows: `900`.
- These fallback receipts are classification/fuel-extraction surfaces only. They do not promote old/current rows, do not authorize deletion/archive, and do not replace row-level source reruns.

## First wave recommendation

1. `P00_controller_receipt_and_gates` locally/Hermes first, to keep delete gates honest.
2. `P01_active_tri_engine_envelopes` on codex1, because current envelopes define the new standard.
3. `P02_foundation_carrier_geometry_donors` on codex1 and `P03_qit_density_entropy_classical_baselines` on codex2 in parallel.
4. Then `P04`/`P05` tool/proof packages, then bridge/graveyard/unclassified packages.

## Final cleanup tranche, later

After action manifests exist, the controller builds a reviewed archive/delete manifest, reruns affected validators/tests, then performs deletes/moves in a separate commit-sized tranche. No worker performs the final deletion.

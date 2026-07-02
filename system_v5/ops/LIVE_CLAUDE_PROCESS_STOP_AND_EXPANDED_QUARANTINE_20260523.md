# Live Claude Process Stop And Expanded Quarantine - 2026-05-23

Status: process-stop and quarantine expansion note. This is not scientific
evidence and does not approve any generated file.

Supersession note: this is a historical process-stop snapshot. For current
cleanup state, use `EXPANDED_QUARANTINE_FULL_INVENTORY_20260523.json`,
`EXPANDED_QUARANTINE_SURFACE_CLASSIFICATION_20260523.md`, and
`EXPANDED_QUARANTINE_ACTION_MANIFEST_20260523.json`. Counts below may be stale.

## Trigger

While auditing the formal/grok_sim boundary breach, the working tree changed
underfoot. `git status` expanded from the earlier boundary-contamination set to
hundreds of untracked files, including new docs, clean-rebuild sims, constraint
audit sims, external audit packets, and additional formal-scout probes.

An active Claude Code process was still running with auto permissions:

```text
pid 15386 / 15387
model claude-opus-4-7
--permission-mode auto
--allow-dangerously-skip-permissions
--resume dc5d30d6-e7dc-425c-9ffd-fe79ffe9ecba
```

The process was stopped with:

```text
kill 15387 15386
```

Follow-up process scan found no remaining matching `claude --output-format
stream-json` / `local-agent-mode` process.

Second stop update: after the first stop, both a Claude Code stream and a
standalone `codex resume` process restarted in the repo. They were stopped as
well. The refreshed inventory notes this restart and uses the post-second-stop
snapshot.

Final stop update: the Claude desktop app later respawned the same Claude Code
writer process, and a standalone `codex resume` process also reappeared. The
Claude app parent and the remaining Codex resume process were force-stopped
before the final cleanup snapshot. No matching writer process was observed in
the final process scan.

Third stop update: `codex resume` respawned again from a repo-rooted `zsh`
parent. The child and parent shell were both terminated so the resume loop would
not keep rewriting the workspace during cleanup.

Fourth stop update: Claude Code respawned again during the post-cleanup status
check. The live Claude child and wrapper PIDs were terminated before reporting
the final state.

## Snapshot After Stop

Fresh snapshot after stopping the live Claude process:

| Surface | Count / state |
|---|---:|
| tracked dirty files shown by `git status --untracked-files=no` | 12 |
| untracked files under `system_v5/docs`, `system_v5/ops`, `system_v5/evidence` | 624 |
| untracked `system_v5/ops/formal_scouts/sim_*.py` | 42 |
| files under `system_v5/ops` / `system_v5/docs` newer than 2026-05-23 08:45 | 679 |
| untracked files under new `system_levels`, `clean_rebuild`, `constraint_audit` surfaces | 124 |

Tracked dirty files after stop:

```text
M system_v5/docs/00_manifest.md
M system_v5/docs/CURRENT_DOCS_MAP.md
M system_v5/docs/FORMAL_SCOUT_READINESS_INDEX.md
M system_v5/docs/MULTIMODEL_PROPOSAL_SPLIT.md
M system_v5/docs/SIM_ESTATE_INTEGRATION_INDEX.md
M system_v5/evidence/formal_scout_readiness_index.json
M system_v5/evidence/sim_estate_integration_index.json
M system_v5/ops/formal_scouts/README.md
M system_v5/ops/formal_scouts/results/su2_unit_quaternion_hopf_holonomy_order_probe_results.json
M system_v5/ops/formal_scouts/sim_source_aligned_stack_completion_gap_classifier_probe.py
M system_v5/ops/formal_scouts/sim_two_root_constraint_flux_recovery_runtime_tensor_bridge_classifier_probe.py
M system_v5/ops/formal_scouts/sim_two_root_constraint_tensor_scaling_status_classifier_probe.py
```

## Expanded Quarantine Surfaces

The earlier quarantine manifest remains valid for the first mixed formal/grok
wave, but it is now incomplete. The second live-Claude wave also puts these
surfaces under quarantine until reviewed:

- `system_v5/docs/system_levels_20260523/`
- `system_v5/ops/clean_rebuild_20260523/`
- `system_v5/ops/constraint_audit_20260523/`
- `system_v5/ops/external_audits/axes_qit_engine_system_pack_r1_20260523/`
- `system_v5/ops/external_audits/foundation_constraint_packet_r8_20260523/`
- `system_v5/ops/external_audits/foundation_constraint_packet_r9_20260523/`
- `system_v5/ops/external_audits/foundation_constraint_packet_r10_20260523/`
- `system_v5/ops/external_audits/foundation_constraint_packet_r11_20260523/`
- `system_v5/ops/external_audits/foundation_constraint_packet_r12_20260523/`
- additional untracked formal-scout probes beyond the earlier 23-file
  section-connection / PEPS cluster.

## Interpretation Rule

Nothing generated during the live-Claude expansion should be treated as
validated formal progress.

The generated material may contain useful prompts, candidate targets, or cleanup
ideas, but it belongs in quarantine/advisory review until:

1. a stable file inventory is produced after all writer processes are stopped;
2. each surface is classified as `discard`, `archive_only`, `advisory_only`,
   `manual_doc_review`, or `independent_rerun_candidate`;
3. no result JSON, readiness index, or classifier consumes it as evidence;
4. formal and informal sims rerun independently under the cross-lane
   independence reset rule.

## Immediate Recovery Boundary

Do not run more formal scouts, regenerate indexes, or stage files until the
expanded quarantine is classified.

The next non-destructive step is a stable full inventory, not science.

# Codex Agent Role Cards

These are Codex-native role templates mined from the local Claude roster and repo contracts. They are not proof that a subagent ran. Count them only when a runtime returns a real worker receipt with role id, source paths, terminal status, and usable output.

Each role stays bounded. Builders do not audit themselves. The controller owns serial synthesis, shared result paths, queue writes, status labels, staging, and commits.

## `repo_state_archaeologist`

```yaml
role_id: repo_state_archaeologist
goal: Answer what is actually on disk before trusting summaries.
scope: Read authority files, target repo paths, result JSONs, and status surfaces needed for one bounded claim.
out_of_scope: Editing docs, registries, sims, queue files, or status labels.
read_first:
  - AGENTS.md
  - CODEX.md
  - system_v5/docs/LLM_CONTROLLER_CONTRACT.md
acceptance:
  - Every reported claim cites an on-disk path or JSON field.
  - Drift between docs, source, and result files is named explicitly.
  - Status language stays within exists, runs, passes local rerun, or canonical by process.
deliverable: Paths read, on-disk answer, drift pairs, unknowns, and highest supported status label.
receipt_fields:
  - role_id
  - paths_read
  - claims_checked
  - drift_pairs
  - unknowns
  - highest_status_label
closeout_check: If the controlling path was not read in this run, report partial_state_archaeology.
```

## `mechanical_gatekeeper`

```yaml
role_id: mechanical_gatekeeper
goal: Run contract and gate commands, then report exact pass or fail evidence.
scope: One target sim/result pair, its validator command, and its highest allowed status label.
out_of_scope: Fixing the sim, auditing semantic fabrication, staging git, or promoting registry rows.
read_first:
  - system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md
  - system_v5/docs/LLM_CONTROLLER_CONTRACT.md
  - target sim or result path
acceptance:
  - Exact command, exit code, stdout or JSON verdict, and result path are recorded.
  - Result freshness is checked against the source path when applicable.
  - The highest status label is bounded by the command actually run.
deliverable: Gate list, verdicts, highest label, blockers, and whether adversarial audit is warranted.
receipt_fields:
  - role_id
  - target_paths
  - commands
  - exit_codes
  - verdicts
  - highest_status_label
  - blockers
closeout_check: If no command ran, return blocked_no_mechanical_gate.
```

## `fabrication_auditor`

```yaml
role_id: fabrication_auditor
goal: Fresh-context adversarial audit for fabricated or self-certifying evidence.
scope: One sim family or one result/source pair.
out_of_scope: Authoring or repairing the artifact under audit, promotion, broad repo claims, or status edits.
read_first:
  - system_v5/docs/LLM_CONTROLLER_CONTRACT.md
  - system_v5/docs/LEGO_SIM_CONTRACT.md
  - target source and result path
acceptance:
  - Decorative solver/proof use is checked against source lines.
  - Hardcoded ablations, by-construction invariants, and unsupported load-bearing labels are tested or named.
  - The strongest falsifier and evidence path are reported.
deliverable: Audit receipt with found_fabrication, strongest falsifier, evidence paths, and aggregate verdict.
receipt_fields:
  - role_id
  - audited_paths
  - found_fabrication
  - strongest_falsifier
  - evidence_paths
  - verdict
closeout_check: If any engine reads another result file for parity, return invalid_cross_run_echo.
```

## `stage_gate_steward`

```yaml
role_id: stage_gate_steward
goal: Preserve process order and block narrative substitutions.
scope: One proposed move, its current stage, required parent receipts, and active blocker.
out_of_scope: Changing status docs, launching broad queues, writing proof claims, or editing shared results.
read_first:
  - system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md
  - system_v5/docs/LLM_CONTROLLER_CONTRACT.md
  - system_v5/docs/LEGO_SIM_CONTRACT.md
acceptance:
  - The proposed move is classified as admitted, blocked, or not evaluated.
  - The exact gate criterion and evidence path are named.
  - Tool, lego, coupling, bridge, axis, and runtime order are not collapsed.
deliverable: Gate decision with admitted or blocked status and exact evidence requirement.
receipt_fields:
  - role_id
  - proposed_move
  - current_stage
  - gate_criterion
  - evidence_path
  - decision
  - blocked_reason
closeout_check: If no gate criterion is named, return blocked_narrative_substitution.
```

## `pattern_porter`

```yaml
role_id: pattern_porter
goal: Convert useful Claude, Hermes, or legacy skill mechanics into minimal Codex artifacts.
scope: One source family, one accepted pattern, one target surface, and one minimal test.
out_of_scope: Importing external doctrine as authority, counting reference roles as executed workers, or changing broad authority docs.
read_first:
  - system_v5/codex_skills/codex-skill-agent-upgrader/SKILL.md
  - system_v5/codex_skills/codex-skill-agent-upgrader/references/source_family_matrix.md
  - AGENTS.md
acceptance:
  - Source family, authority status, target surface, and minimal test are recorded.
  - Accepted patterns cite the controlling Codex authority surface.
  - Rejected patterns name the import risk or missing validation.
deliverable: Pattern cards, edits made, tests run, rejected patterns, and residual gaps.
receipt_fields:
  - role_id
  - source_path
  - source_family
  - accepted_pattern
  - target_path
  - minimal_test
  - status
closeout_check: If the pattern lacks a target path or test, return reference_only.
```

## `builder_lane`

```yaml
role_id: builder_lane
goal: Write one bounded artifact such as a skill, script, probe, or prompt.
scope: One target path, one acceptance test, and one handoff to a separate audit role.
out_of_scope: Auditing its own output, staging git, changing shared queue/status files, or claiming promotion.
read_first:
  - AGENTS.md
  - CODEX.md
  - target path and nearest existing pattern
acceptance:
  - Only the assigned target path is edited unless the controller expands scope.
  - A focused local test or validator command runs.
  - Residual risk and needed audit role are named.
deliverable: Changed path, test command, residual risk, and handoff to audit role.
receipt_fields:
  - role_id
  - target_path
  - files_changed
  - test_command
  - test_exit_code
  - residual_risk
  - audit_handoff
closeout_check: If the lane self-audits, return blocked_builder_self_audit.
```

# Wizard Runtime Audit Triage - 2026-06-10

## Scope

Bounded hygiene triage for `scripts/wizard_v4_2_runtime_audit.py`.

Out of scope and untouched:

- `system_v6/sims/geo_nested_disintegration_v0`
- `system_v6/sims/geo_s10_g2_family_v0`
- `system_v6/sims/geo_s9_octonionic_hopf_stack_v0`
- legacy `system_v4/probes/sim_*.py` mass edits
- git staging or commits

## Captures

Raw initial audit:

- command: `python3 scripts/wizard_v4_2_runtime_audit.py > /tmp/wizard_runtime_audit_initial_raw.json`
- exit: `1`

Exact red-item triage:

- path: `/tmp/wizard_runtime_audit_triage.json`
- class counts:
  - stale-report: 8
  - v4-lint-debt: 2
  - already-superseded: 1
  - config/path-rot: 1

Post-regeneration audit:

- command: `python3 scripts/wizard_v4_2_runtime_audit.py > /tmp/wizard_runtime_audit_after_regen.json`
- exit: `1`

Post-regeneration audit with enough lint time for live counts:

- command: `python3 scripts/wizard_v4_2_runtime_audit.py --contract-lint-timeout-sec 15 > /tmp/wizard_runtime_audit_after_regen_lint15.json`
- exit: `1`

## Dispositions

### stale-report

Initial red items:

- `system_v5/ops/blocked_reason_breakdown.json`
- `system_v5/ops/c1_classification_proposals.json`
- `system_v5/ops/c4_divergence_log_proposals.json`
- `system_v5/ops/c6_loadbearing_report.json`
- `system_v5/ops/c6_loadbearing_decision_table.json`
- `system_v5/ops/proposal_apply_preview.json`
- `system_v5/ops/runner_taxonomy_unknowns.json`
- `system_v5/ops/never_run_cohorts.json`

Disposition: fixed mechanically by rerunning generators, not by hand-editing JSON.

Generators run:

- `python3 scripts/blocked_reason_decompose.py`
- `python3 scripts/c1_classification_proposer.py`
- `python3 scripts/c4_divergence_log_proposer.py`
- `python3 scripts/c6_classical_loadbearing_report.py`
- `python3 scripts/c6_loadbearing_decision_table.py`
- `python3 scripts/proposal_apply_preview.py`
- `python3 scripts/runner_taxonomy_unknowns_report.py`
- `python3 scripts/never_run_cohort_report.py`

Post-regeneration result: `checks.ops_reports_freshness.stale=false`.

### v4-lint-debt

Initial red items:

- `checks.contract_lint_summary`
- `checks.never_run_summary`

Disposition: classified only. No legacy v4 sim source was mass-edited.

The default runtime audit gives timeout fallback counts from `system_v5/ops/state/contract_lint_ratchet.json`:

- `violation_total=4360`
- `sims_with_violations=2574`

A bounded full lint run completed and gave current live counts:

- command: `python3 scripts/lint_sim_contract.py > /tmp/wizard_runtime_contract_lint_full.json`
- exit: `1`
- `checked=3809`
- `violation_total=1146`
- `sims_with_violations=838`
- top rules: `C1_classification_missing=551`, `C5_probe_stale=302`, `C2_manifest_missing=139`, `C3_depth_missing=84`, `C4_divergence_log_missing=68`, `C5_missing_probe=2`

`never_run_summary` remains red after regeneration:

- before: `never_run_total=3741`
- after: `never_run_total=3554`

This is not acceptable as green, but it is acceptable to leave red in this pass because the task explicitly barred mass-editing legacy v4 sims and only authorized mechanical hygiene.

### already-superseded

Initial red item:

- `sim_heartbeat.status=runner_idle_with_backlog`

Disposition: classified only. The two blocked rows have `blocked_reason=done_duplicate_conflict`, `exit_code=0`, and strict receipt validation output with `all_pass=true`; the blocker is queue-state cleanup/owner routing, not a fresh sim failure.

Blocked files inspected:

- `system_v4/probes/a2_state/queue/blocked/4d14e5d91810cb53.json.15171.Joshuas-MacBook-Pro.laneB_w1`
- `system_v4/probes/a2_state/queue/blocked/b4f6c870a79a2272.json.24452.Joshuas-MacBook-Pro.laneB_w1`

No queue mutation was performed in this bounded pass.

### config/path-rot

Post-regeneration red item:

- `checks.taxonomy_unknown_allowlist`

Current post-regeneration values:

- `unknown_count=43`
- `allowlisted_count=39`
- `drift=4`
- `review_by=2026-08-11`
- `review_due=false`

New not-allowlisted rows:

- `system_v4/probes/sim_differentialequations_capability.py`
- `system_v4/probes/sim_diffrax_capability.py`
- `system_v4/probes/sim_manifolds_capability.py`
- `system_v4/probes/sim_symbolics_capability.py`

Disposition: classified only. This is likely taxonomy/config drift around `*_capability.py` probes, but updating `system_v5/docs/RUNNER_TAXONOMY_UNKNOWN_ALLOWLIST.md` requires an owner reason, and changing classifier policy would be more than a mechanical path fix without owner decision.

## Remaining Red

After mechanical regeneration, runtime audit still exits `1`.

Remaining red:

- `checks.contract_lint_summary`: live lint still has `1146` violations across `838` sims when the timeout is raised to 15 seconds.
- `checks.never_run_summary`: `3554` probes still have no canonical result.
- `checks.taxonomy_unknown_allowlist`: four regenerated `*_capability.py` unknown rows are not allowlisted.
- `sim_heartbeat.status=runner_idle_with_backlog`: two blocked duplicate-conflict rows remain in the blocked queue.

Acceptable to leave from this pass:

- v4 lint debt and never-run debt, because the requested work was triage plus mechanical regeneration only.
- duplicate-conflict backlog, because queue mutation was not requested and the rows appear already superseded by done receipts.

Needs owner decision:

- Whether to add owner reasons for the four `*_capability.py` taxonomy unknowns or change runner taxonomy policy for capability probes.
- Whether to clean the two duplicate-conflict blocked rows from queue state.
- Whether to open a separate reviewed micro-batch for the remaining v4 contract lint debt.

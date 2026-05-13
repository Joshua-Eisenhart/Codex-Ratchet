# Codex Ratchet — common tasks
# Use codex-ratchet env (torch 2.11.0) — not homebrew python (torch 2.8.0)
PYTHON := /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3
PROBES := system_v4/probes
MPLCONFIGDIR := /tmp/codex-mpl
NUMBA_CACHE_DIR := /tmp/codex-numba

# Start the iMessage command interface
imessage:
	PYTHONUNBUFFERED=1 MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) -u imessage_bot.py

# Run a single sim by name (e.g. make sim NAME=sim_layer_triple_catalog)
sim:
	@test -n "$(NAME)" || (echo "NAME is required, e.g. make sim NAME=sim_layer_triple_catalog"; exit 2)
	@case "$(NAME)" in *..*|*/*|*\\*) echo "invalid NAME: $(NAME)"; exit 2;; esac
	@test -f "$(PROBES)/$(NAME).py" || (echo "missing sim: $(PROBES)/$(NAME).py"; exit 2)
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) scripts/direct_sim_semantic_guard.py --name "$(NAME)" --probes-dir "$(PROBES)"
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/cleanup_first_guard.py --context sim
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/$(NAME).py

# Run the tools load-bearing check
tools:
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/cleanup_first_guard.py --context tools
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/sim_tools_load_bearing.py

# Show untracked / modified sim files
status:
	@git status --short $(PROBES)/

# Scan for canonical result files with genuine test failures or schema gaps
audit:
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/audit_overclassification.py

# Fail-closed probe/result truth audit; stale canonical rows fail closed, non-canonical stale rows warn by default
truth-audit:
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/probe_truth_audit.py

# Standard terminology alias: source/result integrity verification
integrity-audit:
	$(MAKE) truth-audit

# Advisory audit for standalone torch-family migration metadata coverage
migration-audit:
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/migration_contract_audit.py

# Standard terminology alias: migration compliance report
migration-compliance-audit:
	$(MAKE) migration-audit

# Fail-closed structural migration-contract gate for extracted torch families
migration-audit-strict:
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/migration_contract_audit.py --strict

# Standard terminology alias: migration compliance gate
migration-compliance-gate:
	$(MAKE) migration-audit-strict

# Advisory repo hygiene audit: dirty worktree pressure, result placement, control dirs
repo-hygiene-audit:
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/repo_hygiene_audit.py

# Standard terminology alias: repository hygiene audit
repository-hygiene-audit:
	$(MAKE) repo-hygiene-audit

# Advisory runtime hygiene audit: interpreter, cache dirs, dependency floors
runtime-hygiene-audit:
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/runtime_hygiene_audit.py

# Standard terminology alias: runtime environment audit
runtime-environment-audit:
	$(MAKE) runtime-hygiene-audit

# Read-only audit for stale browser/computer-use helpers before non-browser sim runs
helper-process-audit:
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) scripts/helper_process_audit.py

# Fail closed when stale browser/computer-use helpers are present
helper-process-audit-strict:
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) scripts/helper_process_audit.py --strict

# Advisory audit for legacy executable/result filenames with claim-layer labels
semantic-naming-audit:
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) scripts/sim_name_claim_label_audit.py

# Fail-closed runner launch preflight for non-browser sim execution
runner-preflight:
	$(MAKE) helper-process-audit-strict
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) scripts/runner_queue_preflight.py
	bash -n system_v5/ops/sim_runner.sh
	bash -n scripts/overnight_two_runner.sh

# Dry-run the parallel queue-claim runner topology without executing sims
parallel-runner-dry:
	$(MAKE) runner-preflight
	bash scripts/overnight_two_runner.sh --minutes $(or $(MINUTES),1) --lane-a-parallel $(or $(LANE_A_PARALLEL),2) --lane-b-parallel $(or $(LANE_B_PARALLEL),4) --dry

# Run independent admitted queue claims in parallel worker pools
parallel-runner:
	@test -n "$(MINUTES)" || (echo "MINUTES is required, e.g. make parallel-runner MINUTES=30"; exit 2)
	$(MAKE) runner-preflight
	bash scripts/overnight_two_runner.sh --minutes $(MINUTES) --lane-a-parallel $(or $(LANE_A_PARALLEL),2) --lane-b-parallel $(or $(LANE_B_PARALLEL),4)

# Advisory audit for duplicate repo-local agent state dirs and Codex runtime homes
state-dir-ownership-audit:
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/state_dir_ownership_audit.py

# Advisory audit for registry-linked tool reporting coverage and manifest quality
lego-tool-reporting-audit:
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/lego_tool_reporting_audit.py

# Advisory dirty-source checkpoint plan for bounded source/config cleanup
source-dirty-checkpoint-plan:
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/source_dirty_checkpoint_plan.py

# Standard terminology alias: source checkpoint planning report
source-checkpoint-plan:
	$(MAKE) source-dirty-checkpoint-plan

# Advisory source-dirty lane manifest for the next executable checkpoint group
source-dirty-lane-manifest:
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/source_dirty_lane_manifest.py $(if $(GROUP_ID),--group-id $(GROUP_ID),) $(if $(ALLOW_DOCS),--allow-docs,)

# Standard terminology alias: source lane manifest
source-lane-manifest:
	$(MAKE) source-dirty-lane-manifest

# Advisory checkpoint packet for the currently selected source-dirty lane
source-dirty-checkpoint-packet:
	$(MAKE) source-dirty-lane-manifest $(if $(GROUP_ID),GROUP_ID=$(GROUP_ID),) $(if $(ALLOW_DOCS),ALLOW_DOCS=$(ALLOW_DOCS),)
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/source_dirty_checkpoint_packet.py $(if $(GROUP_ID),--group-id $(GROUP_ID),)

# Standard terminology alias: source checkpoint packet
source-checkpoint-packet:
	$(MAKE) source-dirty-checkpoint-packet

# Advisory stage plan for the currently selected source-dirty lane
source-dirty-stage-plan:
	$(MAKE) source-dirty-checkpoint-packet $(if $(GROUP_ID),GROUP_ID=$(GROUP_ID),) $(if $(ALLOW_DOCS),ALLOW_DOCS=$(ALLOW_DOCS),)
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/source_dirty_stage_plan.py

# Standard terminology alias: source stage plan
source-stage-plan:
	$(MAKE) source-dirty-stage-plan

# Advisory maintenance surface: truth + controller + migration + repo/runtime hygiene
system-hygiene-report:
	$(MAKE) align
	$(MAKE) migration-audit-strict
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/repo_hygiene_audit.py
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/runtime_hygiene_audit.py
	$(MAKE) semantic-naming-audit
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/state_dir_ownership_audit.py
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/lego_tool_reporting_audit.py
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/source_dirty_checkpoint_plan.py
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/source_dirty_lane_manifest.py
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/source_dirty_checkpoint_packet.py
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/source_dirty_stage_plan.py
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/system_hygiene_supervisor.py
	$(MAKE) truth-audit

# Standard terminology alias: maintenance status report
maintenance-report:
	$(MAKE) system-hygiene-report

# Fail closed unless the full hygiene surface is green
system-hygiene:
	$(MAKE) system-hygiene-report
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/system_hygiene_supervisor.py --strict

# Standard terminology alias: maintenance gate
maintenance-gate:
	$(MAKE) system-hygiene

# Backwards-compatible explicit strict alias
system-hygiene-strict:
	$(MAKE) system-hygiene

# Safe self-repair dry run for low-risk hygiene actions
system-hygiene-repair:
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/system_hygiene_repair.py

# Standard terminology alias: bounded remediation dry run
maintenance-remediation:
	$(MAKE) system-hygiene-repair

# Apply low-risk hygiene repair actions, then rebuild the advisory surface
system-hygiene-repair-apply:
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/system_hygiene_repair.py --apply
	$(MAKE) system-hygiene-report

# Standard terminology alias: bounded remediation apply
maintenance-remediation-apply:
	$(MAKE) system-hygiene-repair-apply

# Apply the opt-in quarantine for unique legacy secondary result JSONs, then rebuild the advisory surface
system-hygiene-repair-secondary-apply:
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/system_hygiene_repair.py --apply --include-secondary-unique
	$(MAKE) system-hygiene-report

# Standard terminology alias: opt-in legacy result remediation apply
maintenance-remediation-secondary-apply:
	$(MAKE) system-hygiene-repair-secondary-apply

# Build one machine-readable controller alignment report
align:
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/probe_truth_audit.py
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/controller_alignment_audit.py
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/probe_truth_audit.py
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/controller_alignment_audit.py

# Standard terminology alias: contract compliance report
contract-compliance-audit:
	$(MAKE) align

# Build alignment surfaces and fail closed if docs still drift
align-strict-docs:
	$(MAKE) align
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/controller_alignment_audit.py --require-docs-current

# Build alignment surfaces and fail closed unless the full controller contract is current
align-strict-contract:
	$(MAKE) align
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/controller_alignment_audit.py --require-current-contract

# Build one machine-readable lego-first backlog report
lego-audit:
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/lego_stack_audit.py

# Build one machine-readable lego -> coupling routing report
lego-coupling:
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/lego_coupling_candidates.py

# Build one machine-readable lego execution queue
lego-queue:
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/lego_batch_queue.py

# Build a non-promoting mass exploration manifest for every sim/micro-lego/lego
mass-lego-batch:
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) scripts/mass_lego_batch_manifest.py

# Bounded Wizard/autoresearch sim loop: broad exploration, strict admission, no runner launch by default
wizard-autoresearch-loop:
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) scripts/wizard_autoresearch_sim_loop.py --iterations $(or $(ITERATIONS),1) $(if $(RUN_TAG),--run-tag $(RUN_TAG),) $(if $(OUT_DIR),--out-dir $(OUT_DIR),) $(if $(OUT_DIR),--evidence-index-out $(OUT_DIR)/qit_engine_evidence_index.json,) $(if $(OPUS_AUDIT),--opus-audit,) $(if $(RUN_RUNNER),--run-runner,) $(if $(DRY_RUNNER),--dry-runner,) $(if $(RUNNER_MINUTES),--runner-minutes $(RUNNER_MINUTES),) $(if $(LANE_A_PARALLEL),--lane-a-parallel $(LANE_A_PARALLEL),) $(if $(LANE_B_PARALLEL),--lane-b-parallel $(LANE_B_PARALLEL),) $(if $(ATTEMPT_GEMINI),--attempt-gemini,) $(if $(INCLUDE_HAIKU),--include-haiku,) $(if $(SKIP_WIZARD_MATRIX),--skip-wizard-matrix,) $(if $(EXTERNAL_COUNCIL_RECEIPTS),--external-council-receipts $(EXTERNAL_COUNCIL_RECEIPTS),)

# One safe disposable smoke loop: preflight only, no model matrix, no repo evidence writes
wizard-autoresearch-loop-dry:
	$(MAKE) wizard-autoresearch-loop ITERATIONS=$(or $(ITERATIONS),1) RUN_TAG=$(or $(RUN_TAG),dry) OUT_DIR=$(or $(OUT_DIR),/tmp/codex_ratchet_wizard_autoresearch_dry) SKIP_WIZARD_MATRIX=1 RUN_RUNNER=1 DRY_RUNNER=1 RUNNER_MINUTES=$(or $(RUNNER_MINUTES),1) LANE_A_PARALLEL=$(or $(LANE_A_PARALLEL),2) LANE_B_PARALLEL=$(or $(LANE_B_PARALLEL),4)

# Rehearse strict QIT micro-admission in /tmp without writing canonical evidence
qit-admission-rehearsal:
	@test -n "$(BASENAME)" || (echo "BASENAME is required"; exit 2)
	@test -n "$(RESULT)" || (echo "RESULT is required"; exit 2)
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) scripts/qit_admission_rehearsal.py --basename $(BASENAME) --result $(RESULT) $(if $(SIM_PATH),--sim-path $(SIM_PATH),) $(if $(FUNCTION_SURFACE),--function-surface $(FUNCTION_SURFACE),) $(if $(OUT_DIR),--out-dir $(OUT_DIR),)

# Map sims to runner-facing execution classes without running them
runner-taxonomy-audit:
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) scripts/sim_runner_taxonomy_audit.py

# Validate one or more result JSON files as controller-admissible receipts
receipt-validate:
	@test -n "$(FILES)" || (echo "FILES is required, e.g. make receipt-validate FILES=system_v4/probes/a2_state/sim_results/example_results.json"; exit 2)
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) scripts/validate_receipt.py $(FILES)

# Strict receipt validation with scope ceiling fields required
receipt-validate-strict:
	@test -n "$(FILES)" || (echo "FILES is required, e.g. make receipt-validate-strict FILES=system_v4/probes/a2_state/sim_results/example_results.json"; exit 2)
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) scripts/validate_receipt.py --strict-scope $(FILES)

# Strict executable receipt validation with run-boundary fields required
receipt-validate-run-boundary:
	@test -n "$(FILES)" || (echo "FILES is required, e.g. make receipt-validate-run-boundary FILES=system_v4/probes/a2_state/sim_results/example_results.json"; exit 2)
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) scripts/validate_receipt.py --strict-scope --require-executable --require-run-boundary $(FILES)

# Reconcile queue DONE rows against result JSON evidence and ledger loopback
receipt-reconcile:
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) scripts/reconcile_state.py $(if $(BASENAME),--basename $(BASENAME),) $(if $(SINCE),--since $(SINCE),)

# Reconcile Tier A, second-wave, and Tier B queue DONE rows against receipts and ledger loopback
receipt-reconcile-all-c:
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) scripts/reconcile_state.py --queue-preset all-c $(if $(BASENAME),--basename $(BASENAME),) $(if $(SINCE),--since $(SINCE),)

# Strict reconciliation gate for a named row or bounded recent batch
receipt-reconcile-strict:
	@test -n "$(BASENAME)$(SINCE)" || (echo "BASENAME or SINCE is required for strict reconciliation"; exit 2)
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) scripts/reconcile_state.py --require-clean $(if $(BASENAME),--basename $(BASENAME),) $(if $(SINCE),--since $(SINCE),)

# Strict All-C reconciliation gate for Tier A, second-wave, and Tier B rows
receipt-reconcile-all-c-strict:
	@test -n "$(BASENAME)$(SINCE)" || (echo "BASENAME or SINCE is required for strict All-C reconciliation"; exit 2)
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) scripts/reconcile_state.py --queue-preset all-c --require-clean $(if $(BASENAME),--basename $(BASENAME),) $(if $(SINCE),--since $(SINCE),)

# Strict reconciliation with demotion/scope-ceiling fields required
receipt-reconcile-scope-strict:
	@test -n "$(BASENAME)$(SINCE)" || (echo "BASENAME or SINCE is required for strict scope reconciliation"; exit 2)
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) scripts/reconcile_state.py --require-clean --strict-scope $(if $(BASENAME),--basename $(BASENAME),) $(if $(SINCE),--since $(SINCE),)

# Strict All-C reconciliation with demotion/scope-ceiling fields required
receipt-reconcile-all-c-scope-strict:
	@test -n "$(BASENAME)$(SINCE)" || (echo "BASENAME or SINCE is required for strict All-C scope reconciliation"; exit 2)
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) scripts/reconcile_state.py --queue-preset all-c --require-clean --strict-scope $(if $(BASENAME),--basename $(BASENAME),) $(if $(SINCE),--since $(SINCE),)

# Strict reconciliation for executable run admission with claim ceilings and lego promotion boundaries required
receipt-reconcile-run-boundary-strict:
	@test -n "$(BASENAME)$(SINCE)" || (echo "BASENAME or SINCE is required for strict run-boundary reconciliation"; exit 2)
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) scripts/reconcile_state.py --require-clean --strict-scope --require-executable-receipt --require-run-boundary $(if $(BASENAME),--basename $(BASENAME),) $(if $(SINCE),--since $(SINCE),)

# Strict All-C reconciliation for executable run admission with claim ceilings and lego promotion boundaries required
receipt-reconcile-all-c-run-boundary-strict:
	@test -n "$(BASENAME)$(SINCE)" || (echo "BASENAME or SINCE is required for strict All-C run-boundary reconciliation"; exit 2)
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) scripts/reconcile_state.py --queue-preset all-c --require-clean --strict-scope --require-executable-receipt --require-run-boundary $(if $(BASENAME),--basename $(BASENAME),) $(if $(SINCE),--since $(SINCE),)

# Advisory opt-in: include blocked Tier D rows in addition to All-C
receipt-reconcile-all-c-with-tier-d:
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) scripts/reconcile_state.py --queue-preset all-c --include-blocked-tier-d $(if $(BASENAME),--basename $(BASENAME),) $(if $(SINCE),--since $(SINCE),)

# Report current sim stage-gate admissions
stage-gate:
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) scripts/stage_gate.py

# Check one stage-gate claim, e.g. make stage-gate-claim CLAIM=scientific_coupling
stage-gate-claim:
	@test -n "$(CLAIM)" || (echo "CLAIM is required, e.g. make stage-gate-claim CLAIM=tool_micro"; exit 2)
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) scripts/stage_gate.py --claim $(CLAIM)

# Extract the actual markdown lego registry into machine-readable JSON
lego-registry:
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/extract_actual_lego_registry.py

# Build the next normalization queue from the actual lego registry
lego-normalize:
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/actual_lego_normalization_queue.py

# Tail the iMessage bot log
imessage-log:
	tail -f /tmp/imessage_bot.log

# Telegram bot (set TELEGRAM_TOKEN env var first)
telegram:
	PYTHONUNBUFFERED=1 MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) -u telegram_bot.py >> /tmp/telegram_bot.log 2>&1

telegram-log:
	tail -f /tmp/telegram_bot.log

.PHONY: imessage imessage-log telegram telegram-log sim tools status audit truth-audit integrity-audit migration-audit migration-compliance-audit migration-audit-strict migration-compliance-gate repo-hygiene-audit repository-hygiene-audit runtime-hygiene-audit runtime-environment-audit helper-process-audit helper-process-audit-strict semantic-naming-audit runner-preflight state-dir-ownership-audit lego-tool-reporting-audit source-dirty-checkpoint-plan source-checkpoint-plan source-dirty-lane-manifest source-lane-manifest source-dirty-checkpoint-packet source-checkpoint-packet source-dirty-stage-plan source-stage-plan system-hygiene-report maintenance-report system-hygiene maintenance-gate system-hygiene-strict system-hygiene-repair maintenance-remediation system-hygiene-repair-apply maintenance-remediation-apply system-hygiene-repair-secondary-apply maintenance-remediation-secondary-apply align contract-compliance-audit align-strict-docs align-strict-contract lego-audit lego-coupling lego-queue mass-lego-batch runner-taxonomy-audit receipt-validate receipt-validate-strict receipt-validate-run-boundary receipt-reconcile receipt-reconcile-all-c receipt-reconcile-strict receipt-reconcile-all-c-strict receipt-reconcile-scope-strict receipt-reconcile-all-c-scope-strict receipt-reconcile-run-boundary-strict receipt-reconcile-all-c-run-boundary-strict receipt-reconcile-all-c-with-tier-d stage-gate stage-gate-claim lego-registry lego-normalize

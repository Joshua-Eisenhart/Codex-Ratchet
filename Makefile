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
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/$(NAME).py

# Run the tools load-bearing check
tools:
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
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/lego_tool_reporting_audit.py
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/source_dirty_checkpoint_plan.py
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/source_dirty_lane_manifest.py
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

.PHONY: imessage imessage-log telegram telegram-log sim tools status audit truth-audit integrity-audit migration-audit migration-compliance-audit migration-audit-strict migration-compliance-gate repo-hygiene-audit repository-hygiene-audit runtime-hygiene-audit runtime-environment-audit lego-tool-reporting-audit source-dirty-checkpoint-plan source-checkpoint-plan source-dirty-lane-manifest source-lane-manifest source-dirty-checkpoint-packet source-checkpoint-packet source-dirty-stage-plan source-stage-plan system-hygiene-report maintenance-report system-hygiene maintenance-gate system-hygiene-strict system-hygiene-repair maintenance-remediation system-hygiene-repair-apply maintenance-remediation-apply system-hygiene-repair-secondary-apply maintenance-remediation-secondary-apply align contract-compliance-audit align-strict-docs align-strict-contract lego-audit lego-coupling lego-queue lego-registry lego-normalize

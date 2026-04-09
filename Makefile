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

# Advisory audit for standalone torch-family migration metadata coverage
migration-audit:
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/migration_contract_audit.py

# Fail-closed structural migration-contract gate for extracted torch families
migration-audit-strict:
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/migration_contract_audit.py --strict

# Build one machine-readable controller alignment report
align:
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/probe_truth_audit.py
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/controller_alignment_audit.py
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/probe_truth_audit.py
	MPLCONFIGDIR=$(MPLCONFIGDIR) NUMBA_CACHE_DIR=$(NUMBA_CACHE_DIR) $(PYTHON) $(PROBES)/controller_alignment_audit.py

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

.PHONY: imessage imessage-log telegram telegram-log sim tools status audit truth-audit migration-audit migration-audit-strict align align-strict-docs align-strict-contract lego-audit lego-coupling lego-queue lego-registry lego-normalize

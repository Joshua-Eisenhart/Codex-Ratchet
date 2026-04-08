# Codex Ratchet — common tasks
PYTHON := /opt/homebrew/bin/python3
PROBES := system_v4/probes

# Start the iMessage command interface
imessage:
	$(PYTHON) imessage_bot.py

# Run a single sim by name (e.g. make sim NAME=sim_layer_triple_catalog)
sim:
	$(PYTHON) $(PROBES)/$(NAME).py

# Run the tools load-bearing check
tools:
	$(PYTHON) $(PROBES)/sim_tools_load_bearing.py

# Show untracked / modified sim files
status:
	@git status --short $(PROBES)/

.PHONY: imessage sim tools status

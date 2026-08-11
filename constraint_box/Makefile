.PHONY: help verify-install verify-wheel install-core install-control-plane install-test install-gates install-full test clean

PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
PYTHONPATH := $(CURDIR)/src:$(PYTHONPATH)

help:
	@echo "ConstraintBox build and verification targets:"
	@echo ""
	@echo "  make verify-install      Exercise the installed v9 core with this interpreter"
	@echo "  make verify-wheel WHEEL=/path/to/constraintbox.whl  Fresh-wheel v9 core smoke"
	@echo "  make install-core        Install the five-tool v9 core"
	@echo "  make install-control-plane  Install the bounded Pydantic/jsonschema profile"
	@echo "  make install-test        Install the test-only Hypothesis profile"
	@echo "  make install-gates       Compatibility alias for install-core"
	@echo "  make install-full        Compatibility alias for install-core + install-test"
	@echo "  make test                Run the test suite"
	@echo "  make clean               Remove build artifacts"

# Verify the distribution actually installed into the selected interpreter.
# Deliberately do not set PYTHONPATH: source-tree imports would hide wheel
# resource and console-entrypoint defects.
verify-install:
	@$(PYTHON) -m constraintbox doctor --json
	@$(PYTHON) -m constraintbox exercise --json
	@$(PIP) check

# A convenience wrapper only. The Python verifier itself is cross-platform;
# this Make target needs an explicit wheel rather than guessing among artifacts.
verify-wheel:
	@test -n "$(WHEEL)" || (echo "set WHEEL=/path/to/constraintbox.whl"; exit 2)
	@$(PYTHON) scripts/verify_wheel.py --wheel "$(WHEEL)"

# Install the supported profiles.  The canonical cross-platform interface is
# ``python -m pip``; this Makefile is a convenience only.
install-core:
	$(PIP) install -e .

install-control-plane:
	$(PIP) install -e '.[control-plane]'

install-test:
	$(PIP) install -e '.[test]'

# Historical target names are aliases, not nonexistent extras.
install-gates: install-core

install-full: install-core install-test

# Run pytest on the test suite with the current interpreter.
test:
	@PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest tests/ -v

# Clean up build artifacts.
clean:
	rm -rf build/ dist/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

.PHONY: help verify-install install-gates install-full test clean

PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
PYTHONPATH := $(CURDIR)/src:$(PYTHONPATH)

help:
	@echo "ConstraintBox build and verification targets:"
	@echo ""
	@echo "  make verify-install      Check all dependencies are installed and versions correct"
	@echo "  make install-gates       Install CB with gates extra (core tool dependencies)"
	@echo "  make install-full        Install CB with full extra (gates + test)"
	@echo "  make test                Run the test suite"
	@echo "  make clean               Remove build artifacts"

# Verify that all declared dependencies are installed at correct versions.
# Exit code 0 if OK, 1 if any required dependency missing or version mismatch.
verify-install:
	@PYTHONPATH=$(PYTHONPATH) $(PYTHON) scripts/verify_install.py

# Install CB with gates extra (includes all core tool dependencies).
install-gates:
	$(PIP) install -e .[gates]

# Install CB with full extra (gates + test dependencies).
install-full:
	$(PIP) install -e .[full]

# Run pytest on the test suite with the current interpreter.
test:
	@PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest tests/ -v

# Clean up build artifacts.
clean:
	rm -rf build/ dist/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

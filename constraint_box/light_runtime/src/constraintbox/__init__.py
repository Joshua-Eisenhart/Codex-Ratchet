"""CB Light-only runtime package.

This distribution intentionally exposes only the finite deterministic control
plane.  CB Heavy adapters and simulation engines remain outside this package;
their absence is tested from a fresh contained Light interpreter.
"""

__all__: list[str] = []

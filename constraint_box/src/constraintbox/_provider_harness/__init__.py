"""Lean, vendored provider boundary used by ConstraintBox's Mini-Lev loop.

This package intentionally contains only the receipt types, signing/notary,
provider adapters, runner, and deterministic provider gate used by
``constraintbox.agentrun``.  It does not include the parent Ratchet harness
orchestrator or controller adapters.

Determinism applies to receipt capture, signatures, and gate outcomes—not to
the untrusted model output supplied by a provider.
"""

from __future__ import annotations

__all__: list[str] = []

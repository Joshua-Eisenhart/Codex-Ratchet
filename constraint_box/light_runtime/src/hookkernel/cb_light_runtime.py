"""Single contained runtime identity for the CB Light control plane.

This is intentionally a literal path inside ``constraint_box``.  CB Light
must not inherit a shared Ratchet interpreter, a simulation environment, or a
provider-specific runtime merely because one happens to be installed there.
"""

from __future__ import annotations

import os
from pathlib import Path


def _contained_root() -> Path:
    """Locate the checkout-owned Light state without inheriting a Heavy path.

    A wheel installs the executable package into ``site-packages`` while the
    SQLite state, hook wiring, receipts, and finite proposal domain remain in
    the contained ``constraint_box`` checkout.  The explicit environment
    value wins; otherwise discover only a directory bearing the Light
    contract.  Falling back to the source location keeps source-tree hooks
    usable, but never guesses a shared Ratchet or sim-engine directory.
    """

    configured = os.environ.get("CB_LIGHT_ROOT")
    if configured:
        candidate = Path(configured).expanduser().resolve()
        if (candidate / "config/cb_light_contract_v1.json").is_file():
            return candidate
        raise RuntimeError(f"CB_LIGHT_ROOT is not a CB Light checkout: {candidate}")

    source_root = Path(__file__).resolve().parents[1]
    candidates = [Path.cwd().resolve(), *(Path.cwd().resolve().parents)]
    for candidate in candidates:
        for maybe_root in (candidate, candidate / "constraint_box"):
            if (maybe_root / "config/cb_light_contract_v1.json").is_file():
                return maybe_root
    return source_root


ROOT = _contained_root()
MANDATED_INTERPRETER = ROOT / ".venv" / "bin" / "python"


def normalized_declared_interpreter(value: str | Path) -> str:
    """Normalize a declared interpreter path without dereferencing symlinks.

    Virtual-environment ``bin/python`` launchers commonly resolve to the same
    host Python binary.  Controller identity is the declared environment path,
    not that shared underlying executable: dereferencing here would let a
    different environment masquerade as the contained CB Light runtime.
    """

    return os.path.normcase(
        os.path.normpath(os.path.abspath(os.path.expanduser(os.fspath(value))))
    )


def same_declared_interpreter(observed: str | Path, expected: str | Path) -> bool:
    """Return whether two paths name the same declared environment launcher."""

    return normalized_declared_interpreter(observed) == normalized_declared_interpreter(
        expected
    )

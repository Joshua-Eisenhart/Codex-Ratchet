#!/usr/bin/env python3
"""Builder/audit boundary marker for gcm_nesting_tower_le3q_v0."""

from __future__ import annotations

from pathlib import Path

from gcm_nesting_tower_le3q_v0_common import SIM_DIR


NO_BUILDER_AUDIT_VERDICT = True
NO_AUDIT_VERDICT_WRITTEN = True
FILE_DISJOINT_PACKET = True
AUDIT_PATH = SIM_DIR / "audit_verdict.md"


def boundary_ok() -> bool:
    if not AUDIT_PATH.exists():
        return True
    header = "\n".join(Path(AUDIT_PATH).read_text(encoding="utf-8").splitlines()[:40]).lower()
    return "independent" in header and "audit" in header


if __name__ == "__main__":
    raise SystemExit(0 if boundary_ok() else 1)

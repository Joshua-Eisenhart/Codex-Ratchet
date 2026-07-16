#!/usr/bin/env python3
"""Tombstone for the killed v0.4 L5 re-audit.

The original instrument is preserved at
``ratchet/archive/manifold_l5_reaudit_v0_4_killed.py`` for audit
reproduction.  It is intentionally not runnable from the current process
entry point because its positive candidates repeat the answer-key formula and
two ablation deltas are hardcoded.
"""

from __future__ import annotations

import sys


def main() -> int:
    print("KILLED_AS_SCIENTIFIC_EVIDENCE")
    print("read ratchet/runs/L5_REAUDIT_AUDIT_KILLED_NOTE.md")
    print("frozen reproduction only: ratchet/archive/manifold_l5_reaudit_v0_4_killed.py")
    return 2


if __name__ == "__main__":
    sys.exit(main())

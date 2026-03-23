#!/usr/bin/env python3
"""Backward-compatible wrapper for legacy strict real-loop entrypoint.

Canonical strict entrypoint:
- system_v3/tools/run_real_loop.py

Explicit recovery entrypoint:
- system_v3/tools/run_real_loop_recovery_cycle.py
"""

from __future__ import annotations

import sys

from run_real_loop import main


def _compatibility_recovery_bridge_warning(argv: list[str]) -> str | None:
    if "--allow-reconstructed-artifacts" not in argv:
        return None
    return (
        "MANUAL_REVIEW_REQUIRED: compatibility recovery path requested through run_real_loop_bridge_from_work.py; "
        "prefer system_v3/tools/run_real_loop_recovery_bridge_from_work.py."
    )


if __name__ == "__main__":
    warning = _compatibility_recovery_bridge_warning(list(sys.argv))
    if warning:
        print(warning, file=sys.stderr)
    raise SystemExit(main())

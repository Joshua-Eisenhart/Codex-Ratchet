#!/usr/bin/env python3
"""Backward-compatible wrapper for explicit recovery real-loop entrypoint.

Canonical recovery entrypoint:
- system_v3/tools/run_real_loop_recovery_cycle.py
"""

from run_real_loop_recovery_cycle import main


if __name__ == "__main__":
    raise SystemExit(main())

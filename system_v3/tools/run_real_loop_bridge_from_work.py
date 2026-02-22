#!/usr/bin/env python3
"""Backward-compatible wrapper for legacy script name.

Canonical entrypoint is system_v3/tools/run_real_loop.py.
"""

from run_real_loop import main


if __name__ == "__main__":
    raise SystemExit(main())

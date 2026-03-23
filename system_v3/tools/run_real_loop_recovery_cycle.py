#!/usr/bin/env python3
"""Dedicated recovery-mode entrypoint for run_real_loop.

This keeps the default strict runner separate from explicit recovery usage.
"""

from __future__ import annotations

import sys

from run_real_loop import main


def _inject_recovery_flag(argv: list[str]) -> list[str]:
    if "--allow-reconstructed-artifacts" in argv:
        return list(argv)
    return [*argv, "--allow-reconstructed-artifacts"]


def _inject_recovery_invocation_source(argv: list[str]) -> list[str]:
    if "--recovery-invocation-source" in argv:
        return list(argv)
    return [*argv, "--recovery-invocation-source", "dedicated_recovery_entrypoint"]


if __name__ == "__main__":
    sys.argv = _inject_recovery_invocation_source(_inject_recovery_flag(list(sys.argv)))
    raise SystemExit(main())

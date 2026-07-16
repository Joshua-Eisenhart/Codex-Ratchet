#!/usr/bin/env python3
"""Compatibility entry point for the order-open Ratchet v0.5 engine.

The current process lives in ``ratchet_engine.py``.  This name remains so
existing commands fail forward into mass candidate exploration plus gate-order
and gate-decomposition search instead of the fixed v0.4 gate list.
"""

from ratchet_engine import (  # noqa: F401
    SCHEMA_VERSION,
    main,
    run_packet,
    run_self_test,
    validate_run,
)


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build the LEAN state-fingerprinted 7Q GCM constraint carve packet."""

from __future__ import annotations

from gcm_constraint_carve_7q_v1_common import main

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
TOOL_MANIFEST = {
    "python_stdlib": {"tried": True, "used": True, "reason": "thin entrypoint dispatches to the LEAN 7Q packet builder"},
}
TOOL_INTEGRATION_DEPTH = {"python_stdlib": "supportive"}


if __name__ == "__main__":
    raise SystemExit(main())

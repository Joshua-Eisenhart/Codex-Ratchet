#!/usr/bin/env python3
"""HOSTILE CONTROL FIXTURE — class: timeout_hang.

A registry-style gate case that HANGS: infinite sleep loop, no output, never
exits. Models a tier2/tier3 registry gate whose cmd wedges (deadlocked solver,
stuck engine, network wait). If a verifier ever treats "no answer yet" as
"pass", this fixture catches it.

NEVER wire this into the real gate_registry.json. Run it only under
timeout_demo.py (5 s harness) — claim_verify's own run() would hold it for
the full 900 s before killing it.
"""

FIXTURE_MARKER = {
    "classification": "hostile_control_fixture",
    "promotion_allowed": False,
    "class": "timeout_hang",
}

import time

while True:
    time.sleep(1)  # no output, no exit — the gate simply never answers

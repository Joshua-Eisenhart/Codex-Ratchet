#!/usr/bin/env python3
"""Write the exact build_three_engine_envelope spec for this packet."""

from __future__ import annotations

import json

from s8_local_information_table_v0_common import PACKET, SIM_ID, rel, write_json
from s8_local_information_table_v0_envelope import SPEC, build_spec


def main() -> int:
    spec = build_spec()
    write_json(SPEC, spec)
    print(json.dumps({"ok": True, "spec_path": rel(PACKET / f"{SIM_ID}_envelope_spec.json")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

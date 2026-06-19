#!/usr/bin/env python3
"""Write the flip-controlled 3Q nested geometry-delta packet."""

from __future__ import annotations

import json

from gcm_nested_geometry_delta_3q_v0_common import RESULT_PATH, build_packet, rel


def main() -> int:
    packet = build_packet(write_result=True)
    print(
        json.dumps(
            {
                "ok": True,
                "result_path": rel(RESULT_PATH),
                "geometry_delta_stability_class": packet["geometry_delta_stability_class"],
                "main_delta_l1": packet["geometry_delta_from_free"]["main"]["delta_l1"],
                "alternate_pin_delta_l1": packet["flip_control_runs"]["alternate_registry_pin"]["delta_l1"],
                "alternate_probe_delta_l1": packet["flip_control_runs"]["alternate_probe_family"]["delta_l1"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

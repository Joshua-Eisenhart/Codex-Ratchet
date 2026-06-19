#!/usr/bin/env python3
"""Write only the gcm_qca_runner_2q_v1 envelope."""

from __future__ import annotations

import json

from gcm_qca_runner_2q_v1_common import ENVELOPE_PATH, build_envelope, rel, write_json


def main() -> None:
    envelope = build_envelope()
    write_json(ENVELOPE_PATH, envelope)
    print(json.dumps({"envelope_path": rel(ENVELOPE_PATH), "all_pass": envelope["all_pass"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

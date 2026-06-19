#!/usr/bin/env python3
"""Build the ECD.06 prediction-first inference core result."""

from __future__ import annotations

import json

import ecd06_prediction_first_inference_v0_common as common


def main() -> int:
    result = common.build_prediction_first_object()
    common.write_json(common.RESULT_PATH, result)
    print(json.dumps({"result_path": common.rel(common.RESULT_PATH), "all_pass": result["all_pass"]}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

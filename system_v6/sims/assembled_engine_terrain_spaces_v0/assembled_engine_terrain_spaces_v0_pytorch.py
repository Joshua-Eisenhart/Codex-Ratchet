#!/usr/bin/env python3
"""Scoped PyTorch lane wrapper for assembled_engine_terrain_spaces_v0."""

from __future__ import annotations

import json

import torch  # noqa: F401

import assembled_engine_terrain_spaces_v0_common as common


def main() -> int:
    payload = common.write_pytorch_result()
    print(json.dumps({"result_path": payload["result_path"], "all_pass": payload["all_pass"]}, indent=2, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())


#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _planner_tools_root() -> Path:
    return _repo_root() / "system_v3" / "runtime" / "bootpack_b_kernel_v1" / "tools"


def validate_family_slice_runtime_semantics(family_slice: dict[str, Any]) -> str:
    planner_tools_root = _planner_tools_root()
    if str(planner_tools_root) not in sys.path:
        sys.path.insert(0, str(planner_tools_root))
    from a1_adaptive_ratchet_planner import _validate_family_slice_semantics  # noqa: PLC0415

    _validate_family_slice_semantics(family_slice)
    return "jsonschema_plus_runtime_semantics"

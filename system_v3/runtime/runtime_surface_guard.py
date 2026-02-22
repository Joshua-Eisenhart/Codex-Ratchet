import os
from pathlib import Path


CANONICAL_RUNTIME_NAME = "bootpack_b_kernel_v1"
ALLOW_NONCANONICAL_ENV = "RATCHET_ALLOW_NONCANONICAL_RUNTIME"


def enforce_canonical_runtime(script_path: str) -> None:
    if os.environ.get(ALLOW_NONCANONICAL_ENV, "") == "1":
        return
    path = Path(script_path).resolve()
    parts = {part for part in path.parts}
    if CANONICAL_RUNTIME_NAME in parts:
        return
    raise SystemExit(
        f"non-canonical runtime surface blocked: {path}; "
        f"use {CANONICAL_RUNTIME_NAME} or set {ALLOW_NONCANONICAL_ENV}=1 for explicit override"
    )

"""Portable CPython runtime binding for the ConstraintBox controller.

CPython is a declared part of CB: it runs the controller, finite reference
algorithms, Mini-LevOS hooks, ledgers, and Python tool adapters.  The old
implementation treated one developer's CPython executable, Homebrew layout,
stdlib bytes, and machine architecture as the only legal product runtime.

This module instead binds the active interpreter to a controller-owned portable
profile registry.  The registry controls supported Python minors and core
library windows; an individual receipt records the local executable and module
origins that actually ran.  CB never activates another interpreter, runs an
installer, or silently accepts a fallback profile.
"""

from __future__ import annotations

import builtins
import fractions
import hashlib
import heapq
import itertools
import json
import marshal
import math
import os
import subprocess
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .intake import canonical_json
from .runtime_profiles import (
    DEFAULT_RUNTIME_PROFILE_REGISTRY,
    RuntimeProfileError,
    inspect_active_runtime,
    load_runtime_profile_registry,
)


# Kept as a compatibility alias for callers that previously imported the
# singleton policy path.  It now points to a portable profile registry, never
# to a developer-host binary/stdlib attestation.
DEFAULT_PYTHON_RUNTIME_POLICY = DEFAULT_RUNTIME_PROFILE_REGISTRY
_SHA256 = hashlib.sha256


class PythonRuntimeError(RuntimeError):
    """The active CPython runtime does not satisfy the core CB profile."""


@dataclass(frozen=True)
class PythonRuntimePolicy:
    """Small controller-facing view of the portable runtime registry."""

    policy_sha256: str
    profile_ids: tuple[str, ...]
    operation_ids: tuple[str, ...]
    claim_ceiling: str


_OPERATION_GETTERS: dict[str, Callable[[], object]] = {
    "builtins.all": lambda: builtins.all,
    "builtins.any": lambda: builtins.any,
    "builtins.len": lambda: builtins.len,
    "fractions.Fraction": lambda: fractions.Fraction,
    "hashlib.sha256": lambda: hashlib.sha256,
    "heapq.heappop": lambda: heapq.heappop,
    "heapq.heappush": lambda: heapq.heappush,
    "itertools.product": lambda: itertools.product,
    "json.dumps": lambda: json.dumps,
    "json.loads": lambda: json.loads,
    "math.prod": lambda: math.prod,
    "os.replace": lambda: os.replace,
    "subprocess.run": lambda: subprocess.run,
}

_EXPECTED_OPERATION_METADATA = {
    "builtins.all": ("builtins", "all", "all"),
    "builtins.any": ("builtins", "any", "any"),
    "builtins.len": ("builtins", "len", "len"),
    "fractions.Fraction": ("fractions", "Fraction", "Fraction"),
    "hashlib.sha256": ("_hashlib", "openssl_sha256", "openssl_sha256"),
    "heapq.heappop": ("_heapq", "heappop", "heappop"),
    "heapq.heappush": ("_heapq", "heappush", "heappush"),
    "itertools.product": ("itertools", "product", "product"),
    "json.dumps": ("json", "dumps", "dumps"),
    "json.loads": ("json", "loads", "loads"),
    "math.prod": ("math", "prod", "prod"),
    "os.replace": ("posix", "replace", "replace"),
    "subprocess.run": ("subprocess", "run", "run"),
}


def load_python_runtime_policy() -> PythonRuntimePolicy:
    """Load the controller-owned portable profile policy, not a host image."""

    try:
        registry = load_runtime_profile_registry()
    except RuntimeProfileError as exc:
        raise PythonRuntimeError(f"portable runtime policy unavailable: {exc}") from exc
    return PythonRuntimePolicy(
        policy_sha256=registry.registry_sha256,
        profile_ids=tuple(profile.profile_id for profile in registry.profiles),
        operation_ids=tuple(sorted(_OPERATION_GETTERS)),
        claim_ceiling=(
            "only that the active CPython runtime matched one declared portable "
            "ConstraintBox core profile and remained stable during this run; "
            "not host integrity, external sim-estate readiness, release, "
            "promotion, or scientific truth"
        ),
    )


def _operation_identity(operation_id: str) -> dict[str, Any]:
    getter = _OPERATION_GETTERS.get(operation_id)
    if getter is None:
        raise PythonRuntimeError(f"unknown Python operation registration: {operation_id}")
    observed = getter()
    code = getattr(observed, "__code__", None)
    code_sha256 = (
        _SHA256(marshal.dumps(code)).hexdigest()
        if isinstance(code, types.CodeType)
        else None
    )
    identity = {
        "module": getattr(observed, "__module__", None),
        "name": getattr(observed, "__name__", None),
        "qualname": getattr(observed, "__qualname__", None),
        "type": f"{type(observed).__module__}.{type(observed).__qualname__}",
        "code_sha256": code_sha256,
    }
    expected_module, expected_name, expected_qualname = _EXPECTED_OPERATION_METADATA[operation_id]
    if (
        identity["module"] != expected_module
        or identity["name"] != expected_name
        or identity["qualname"] != expected_qualname
    ):
        raise PythonRuntimeError(f"Python operation binding drift: {operation_id}")
    return identity


def _operation_witnesses() -> dict[str, Any]:
    product_rows = list(itertools.product((0, 1), repeat=2))
    heap = [3, 1]
    heapq.heapify(heap)
    heapq.heappush(heap, 2)
    heap_first = heapq.heappop(heap)
    encoded = json.dumps(
        {"b": 1, "a": 2},
        sort_keys=True,
        separators=(",", ":"),
    )
    decoded = json.loads(encoded)
    witnesses = {
        "builtins.all": all((True, True)),
        "builtins.any": any((False, True)),
        "builtins.len": len(product_rows) == 4,
        "fractions.Fraction": (
            fractions.Fraction(1, 3) + fractions.Fraction(2, 3)
            == fractions.Fraction(1, 1)
        ),
        "hashlib.sha256": (
            hashlib.sha256(b"constraintbox").hexdigest()
            == "61272c0a0be3411314c923dfc30b7abe9fba86701c18ecb954b7e5c9d67c9d5e"
        ),
        "heapq.heappop": heap_first == 1,
        "heapq.heappush": heap == [2, 3],
        "itertools.product": product_rows
        == [(0, 0), (0, 1), (1, 0), (1, 1)],
        "json.dumps": encoded == '{"a":2,"b":1}',
        "json.loads": decoded == {"a": 2, "b": 1},
        "math.prod": math.prod((2, 3, 5)) == 30,
        "os.replace": "binding_only",
        "subprocess.run": "binding_only",
    }
    if any(value is not True for value in witnesses.values() if value != "binding_only"):
        raise PythonRuntimeError("a bounded Python operation witness failed")
    return witnesses


def capture_python_runtime() -> dict[str, Any]:
    """Capture one active portable-profile runtime receipt.

    An active runtime that lacks a declared profile or a required core package
    is a fail-closed runtime error for a controller path.  The separate CLI
    runtime inspection command reports the same state without raising.
    """

    policy = load_python_runtime_policy()
    try:
        profile_receipt = inspect_active_runtime()
    except RuntimeProfileError as exc:
        raise PythonRuntimeError(f"runtime-profile inspection failed: {exc}") from exc
    if profile_receipt["state"] != "ELIGIBLE":
        raise PythonRuntimeError(
            "active core runtime is not eligible: "
            f"{profile_receipt['state']}/{profile_receipt['reason']}"
        )
    operations = {
        operation_id: _operation_identity(operation_id)
        for operation_id in policy.operation_ids
    }
    witnesses = _operation_witnesses()
    source_path = Path(__file__).resolve()
    try:
        source_sha256 = _SHA256(source_path.read_bytes()).hexdigest()
    except OSError as exc:
        raise PythonRuntimeError(f"runtime-binding source unavailable: {exc}") from exc
    body = {
        "schema": "constraintbox.python-runtime-receipt.v2",
        "policy_sha256": policy.policy_sha256,
        "profile_id": profile_receipt["profile_id"],
        "runtime_profile": profile_receipt,
        "operations": operations,
        "operation_witnesses": witnesses,
        "runtime_module_source_sha256": source_sha256,
        "claim_ceiling": policy.claim_ceiling,
        "promotion_allowed": False,
    }
    return {**body, "identity_sha256": _SHA256(canonical_json(body)).hexdigest()}


def verify_python_runtime_stable(
    before: dict[str, Any],
    after: dict[str, Any],
) -> None:
    """Fail when the selected runtime/profile binding changes during work."""

    if before != after:
        raise PythonRuntimeError("selected Python runtime identity changed during evaluation")


def python_runtime_policy_sha256() -> str:
    """Return the portable registry digest used in controller policy material."""

    return load_python_runtime_policy().policy_sha256

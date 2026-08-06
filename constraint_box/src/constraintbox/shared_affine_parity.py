"""Controller for one parameter-identical NumPy/JAX/PyTorch/Julia fixture."""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


SCHEMA = "constraintbox.shared-affine-density-parity.v1"
_ENGINES = ("numpy", "jax", "pytorch", "julia")
JULIA_BIN_ENV = "CONSTRAINTBOX_JULIA_BIN"
JULIA_PROJECT_ENV = "CONSTRAINTBOX_JULIA_PROJECT"


class SharedAffineParityError(ValueError):
    pass


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _strict_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise SharedAffineParityError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _json_object(text: str, label: str) -> dict[str, Any]:
    try:
        value = json.loads(text, object_pairs_hook=_strict_pairs)
    except json.JSONDecodeError as exc:
        raise SharedAffineParityError(f"{label} did not return JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise SharedAffineParityError(f"{label} did not return an object")
    return value


def _close(left: Any, right: Any, tolerance: float) -> bool:
    if isinstance(left, list):
        return isinstance(right, list) and len(left) == len(right) and all(
            _close(a, b, tolerance) for a, b in zip(left, right, strict=True)
        )
    return (
        isinstance(left, (int, float)) and not isinstance(left, bool)
        and isinstance(right, (int, float)) and not isinstance(right, bool)
        and math.isfinite(float(left)) and math.isfinite(float(right))
        and abs(float(left) - float(right)) <= tolerance
    )


def run_shared_affine_parity(*, run_root: Path) -> tuple[dict[str, Any], int]:
    if not run_root.is_absolute():
        raise SharedAffineParityError("run_root must be absolute")
    run_root.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[2]
    fixture = root / "fixtures" / "shared_affine_density_v1.json"
    lane = root / "workers" / "shared_affine_density_v1" / "python_lane.py"
    julia_lane = root / "workers" / "shared_affine_density_v1" / "julia_lane.jl"
    if not all(path.is_file() for path in (fixture, lane, julia_lane)):
        raise SharedAffineParityError("shared affine fixture sources are unavailable")
    julia_project_value = os.environ.get(JULIA_PROJECT_ENV)
    if not julia_project_value:
        raise SharedAffineParityError(
            f"{JULIA_PROJECT_ENV} must name the local Julia project containing the required packages"
        )
    julia_project = Path(julia_project_value).expanduser().resolve(strict=True)
    if not (julia_project / "Project.toml").is_file():
        raise SharedAffineParityError(
            f"{JULIA_PROJECT_ENV} must contain Project.toml: {julia_project}"
        )
    julia_bin_value = os.environ.get(JULIA_BIN_ENV, "julia")
    julia_bin = shutil.which(julia_bin_value)
    if julia_bin is None:
        raise SharedAffineParityError(
            f"{JULIA_BIN_ENV} does not resolve to an executable: {julia_bin_value}"
        )
    fixture_body = _json_object(fixture.read_text(encoding="utf-8"), "fixture")
    tolerance = fixture_body.get("tolerance")
    if not isinstance(tolerance, (int, float)) or isinstance(tolerance, bool) or tolerance <= 0:
        raise SharedAffineParityError("fixture tolerance must be positive")
    commands = {
        engine: [sys.executable, str(lane), "--engine", engine, "--fixture", str(fixture)]
        for engine in ("numpy", "jax", "pytorch")
    }
    commands["julia"] = [
        julia_bin,
        "--startup-file=no",
        f"--project={julia_project}",
        str(julia_lane),
        str(fixture),
    ]
    receipts: dict[str, dict[str, Any]] = {}
    errors: dict[str, str] = {}
    for engine in _ENGINES:
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        if engine == "julia":
            env["JULIA_LOAD_PATH"] = "@:@stdlib"
        completed = subprocess.run(commands[engine], text=True, capture_output=True, env=env, timeout=180)
        if completed.returncode != 0:
            errors[engine] = completed.stderr[-1000:]
            continue
        try:
            row = _json_object(completed.stdout, engine)
            if (
                row.get("schema") != "constraintbox.shared-affine-density-lane.v1"
                or row.get("engine") != engine
                or row.get("reads_peer_result") is not False
                or row.get("positive_case") is not True
                or row.get("wrong_time_control_caught") is not True
            ):
                raise SharedAffineParityError("lane contract mismatch")
            receipts[engine] = row
        except SharedAffineParityError as exc:
            errors[engine] = str(exc)
    comparisons: list[dict[str, Any]] = []
    for index, left_name in enumerate(_ENGINES):
        for right_name in _ENGINES[index + 1:]:
            if left_name not in receipts or right_name not in receipts:
                continue
            left, right = receipts[left_name], receipts[right_name]
            fields = {
                field: _close(left.get(field), right.get(field), float(tolerance))
                for field in ("state", "jacobian")
            }
            comparisons.append({"left": left_name, "right": right_name, "fields": fields, "consistent": all(fields.values())})
    state = "CONSISTENT" if len(receipts) == 4 and comparisons and all(row["consistent"] for row in comparisons) else "DIVERGENT"
    result = {
        "schema": SCHEMA,
        "state": state,
        "fixture": {"path": str(fixture), "sha256": _sha256(fixture)},
        "local_resource_bindings": {
            "julia_binary": str(Path(julia_bin).resolve()),
            "julia_project": str(julia_project),
        },
        "tolerance": float(tolerance),
        "receipts": receipts,
        "comparisons": comparisons,
        "errors": errors,
        "consistency_only": True,
        "release_allowed": False,
        "promotion_allowed": False,
        "claim_ceiling": "one independent execution of a shared finite affine fixture across NumPy, JAX, PyTorch, and Julia; numerical consistency only, not Canon, engine readiness, scientific proof, release, or promotion",
    }
    (run_root / "shared_affine_parity_receipt.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result, 0 if state == "CONSISTENT" else 1

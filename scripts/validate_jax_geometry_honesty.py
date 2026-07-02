#!/usr/bin/env python3
"""Fail JAX geometry receipts that lack a falsifying geometry control.

This is not a layer-completion or admission gate. It is a narrow anti-theater
check for the specific failure mode where a target invariant is true by
construction, while all controls perturb unrelated weights or policy fields.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


GAP = 1.0e-6
NATIVE_GEOMETRY_LOAD_BEARING = {"jax"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def negative_control_ok(control: Any) -> tuple[bool, str]:
    if not isinstance(control, dict):
        return False, "missing target_invariant_negative_control object"
    if not bool(control.get("pass")):
        return False, "target_invariant_negative_control.pass is not true"
    if not bool(control.get("control_failed_target_claim")):
        return False, "bad geometry did not fail the target claim"

    real_residual = float(control.get("real_residual", 0.0))
    control_residual = float(control.get("control_residual", 0.0))
    signal_delta = abs(float(control.get("control_signal_delta", 0.0)))
    signal_lost = abs(float(control.get("control_signal_lost", 0.0)))
    if real_residual > max(GAP, control_residual):
        return False, f"real residual {real_residual:.3g} exceeds allowed bound"
    if max(control_residual, signal_delta, signal_lost) <= GAP:
        return False, "control has no nonzero residual, signal delta, or signal loss"
    return True, "ok"


def audit_rows(path: Path, data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    rows = data.get("scale_results") or data.get("rows") or []
    if not rows:
        errors.append(f"{path}: no scale_results/rows to audit")
        return errors

    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"{path}: row {index} is not an object")
            continue
        controls = row.get("controls") if isinstance(row.get("controls"), dict) else {}
        negative = row.get("target_invariant_negative_control") or controls.get("target_invariant_negative_control")
        ok, reason = negative_control_ok(negative)
        if not ok:
            errors.append(f"{path}: row {index}: {reason}")
        erased = controls.get("target_invariant_erased")
        if isinstance(erased, dict) and erased.get("pass") is True:
            errors.append(f"{path}: row {index}: target_invariant_erased.pass=true is forbidden")
    return errors


def audit_tool_roles(path: Path, data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if "jax_native_geometry_" not in path.name:
        return errors
    depth = data.get("tool_integration_depth") or data.get("TOOL_INTEGRATION_DEPTH") or {}
    if not isinstance(depth, dict) or not depth:
        return [f"{path}: missing tool_integration_depth"]
    load_bearing = {name for name, role in depth.items() if role == "load_bearing"}
    if load_bearing != NATIVE_GEOMETRY_LOAD_BEARING:
        errors.append(
            f"{path}: native geometry load-bearing tools must be {sorted(NATIVE_GEOMETRY_LOAD_BEARING)}, got {sorted(load_bearing)}"
        )
    boundary = data.get("tool_role_boundary")
    if not isinstance(boundary, dict):
        errors.append(f"{path}: missing tool_role_boundary")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="JAX geometry result JSON files or directories")
    args = parser.parse_args()

    result_paths: list[Path] = []
    for item in args.paths:
        path = Path(item)
        if path.is_dir():
            result_paths.extend(sorted(path.glob("*.json")))
        else:
            result_paths.append(path)

    errors: list[str] = []
    audited = 0
    for path in result_paths:
        if not path.exists():
            errors.append(f"{path}: missing")
            continue
        data = load_json(path)
        if "jax_native_geometry_" not in path.name and "_full_network_subreceipt" not in path.name:
            continue
        audited += 1
        errors.extend(audit_rows(path, data))
        errors.extend(audit_tool_roles(path, data))

    report = {
        "audited": audited,
        "errors": errors,
        "ok": not errors,
        "claim_boundary": "Pass means JAX geometry receipts include a target-level negative control. It does not admit layers, G-structures, stacking, Axis0, flux, or final manifold claims.",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

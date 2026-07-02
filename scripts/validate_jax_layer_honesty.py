#!/usr/bin/env python3
"""Validate JAX layer receipts against execution and full-layer honesty gates.

The current JAX L0-L8 receipts are allowed to be bounded execution receipts.
They are not allowed to silently stand in for full individual manifold-layer
sims unless they carry the missing native carrier, scale, and falsifier fields.
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path
from typing import Any


GENERIC_SITE_LADDER = [8, 16, 32, 64]


def _load(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except Exception as exc:  # pragma: no cover - CLI guard
        raise SystemExit(f"{path}: cannot parse JSON: {exc}") from exc


def _contains_text(payload: Any, needle: str) -> bool:
    if isinstance(payload, str):
        return needle.lower() in payload.lower()
    if isinstance(payload, dict):
        return any(_contains_text(value, needle) for value in payload.values())
    if isinstance(payload, list):
        return any(_contains_text(value, needle) for value in payload)
    return False


def _path_args(args: list[str]) -> list[Path]:
    paths: list[Path] = []
    for arg in args:
        matches = [Path(match) for match in glob.glob(arg)]
        path = Path(arg)
        if path.is_dir():
            matches.extend(sorted(path.glob("*.json")))
        elif path.exists():
            matches.append(path)
        paths.extend(matches)
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(path)
    return unique


def _execution_floor_errors(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("classification") != "formal_scout":
        errors.append("classification is not formal_scout")
    if data.get("promotion_allowed") is not False:
        errors.append("promotion_allowed is not false")
    if data.get("all_pass") is not True:
        errors.append("all_pass is not true")
    if not data.get("TOOL_MANIFEST") and not data.get("tool_manifest"):
        errors.append("missing tool manifest")
    if not data.get("TOOL_INTEGRATION_DEPTH") and not data.get("tool_integration_depth"):
        errors.append("missing tool integration depth")
    if not _contains_text(data.get("claim_ceiling", data.get("claim_boundary", "")), "formal scout"):
        errors.append("claim boundary does not say formal scout")
    if not _contains_text(data, "promotion_allowed=false") and data.get("promotion_allowed") is not False:
        errors.append("missing explicit promotion lock")
    boundary = data.get("boundary") or {}
    if boundary.get("not_peps3d_or_full_layer_admission", {}).get("pass") is not True:
        errors.append("missing not_peps3d_or_full_layer_admission boundary")
    controls = data.get("controls") or {}
    for name in ("zero_signal_control", "scrambled_edge_control", "downstream_lock_control"):
        if controls.get(name, {}).get("pass") is not True:
            errors.append(f"missing or failing {name}")
    return errors


def _full_layer_blockers(data: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    scales = data.get("scales")
    if scales == GENERIC_SITE_LADDER:
        blockers.append("uses generic 8/16/32/64 site ladder, not native layer scale parameters")
    if not data.get("native_scale_parameters"):
        blockers.append("missing native_scale_parameters")
    carrier = " ".join(
        str(data.get(key, ""))
        for key in ("carrier_layer", "carrier_realization", "peps3d_embedding", "network_carrier")
    ).lower()
    if not any(token in carrier for token in ("peps3d", "peps", "mps", "spinor network", "spinor-network")):
        blockers.append("missing explicit PEPS/MPS/spinor-network carrier realization")
    if not data.get("layer_specific_negative_control"):
        blockers.append("missing layer_specific_negative_control")
    if not data.get("native_dynamics"):
        blockers.append("missing native_dynamics")
    if data.get("promotion_allowed") is not False:
        blockers.append("promotion_allowed is not false")
    if _contains_text(data.get("claim_ceiling", data.get("claim_boundary", "")), "formal scout only"):
        blockers.append("receipt self-declares formal scout only")
    boundary = data.get("boundary") or {}
    if boundary.get("not_peps3d_or_full_layer_admission", {}).get("pass") is True:
        blockers.append("receipt explicitly blocks PEPS3D/full layer admission")
    return blockers


def _audit(path: Path) -> dict[str, Any]:
    data = _load(path)
    floor_errors = _execution_floor_errors(data)
    blockers = _full_layer_blockers(data)
    return {
        "path": str(path),
        "layer_id": data.get("layer_id"),
        "layer_name": data.get("layer_name"),
        "execution_receipt_ok": not floor_errors,
        "execution_floor_errors": floor_errors,
        "full_layer_ready": not blockers,
        "full_layer_blockers": blockers,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", help="Result JSON paths, directories, or globs.")
    parser.add_argument(
        "--require-full",
        action="store_true",
        help="Exit nonzero unless each receipt satisfies the full individual layer sim gate.",
    )
    args = parser.parse_args()

    paths = _path_args(args.paths)
    if not paths:
        print(json.dumps({"ok": False, "errors": ["no input paths"]}, indent=2, sort_keys=True))
        return 2

    audits = [_audit(path) for path in paths]
    execution_errors = [
        {"path": row["path"], "errors": row["execution_floor_errors"]}
        for row in audits
        if not row["execution_receipt_ok"]
    ]
    full_blocked = [
        {"path": row["path"], "blockers": row["full_layer_blockers"]}
        for row in audits
        if not row["full_layer_ready"]
    ]
    ok = not execution_errors and (not args.require_full or not full_blocked)
    print(
        json.dumps(
            {
                "audited": len(audits),
                "execution_receipt_errors": execution_errors,
                "full_layer_blocked": full_blocked,
                "ok": ok,
                "require_full": args.require_full,
                "summary": [
                    {
                        "layer_id": row["layer_id"],
                        "layer_name": row["layer_name"],
                        "execution_receipt_ok": row["execution_receipt_ok"],
                        "full_layer_ready": row["full_layer_ready"],
                    }
                    for row in audits
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

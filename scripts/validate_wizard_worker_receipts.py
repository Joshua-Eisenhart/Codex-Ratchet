#!/usr/bin/env python3
"""Validate Wizard v4.2 worker receipt truth before topology counts are accepted."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED = {
    "schema",
    "wizard_version",
    "route",
    "parent_id",
    "pool",
    "launch_surface",
    "terminal_status",
    "artifact_path",
    "accepted_conclusion",
    "counts_toward_topology",
}

POOLS = {"codex-native", "claude-bridge", "gemini", "omx", "tmux", "tool"}
EXTERNAL_POOLS = {"claude-bridge", "gemini", "omx", "tmux"}
TERMINAL_STATUSES = {
    "completed",
    "failed",
    "timed_out",
    "blocked",
    "abandoned",
    "not_launched",
    "superseded",
}


def load_receipts(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text())
    if isinstance(data, dict) and "receipts" in data:
        data = data["receipts"]
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        raise ValueError(f"{path}: expected one receipt object, a list, or an object with receipts[]")
    return data


def present(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_receipt(receipt: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED - receipt.keys())
    if missing:
        errors.append(f"{label}: missing required fields: {', '.join(missing)}")

    if receipt.get("schema") != "wizard-v4.2-worker-receipt":
        errors.append(f"{label}: schema must be wizard-v4.2-worker-receipt")
    if receipt.get("wizard_version") != "v4.2":
        errors.append(f"{label}: wizard_version must be v4.2")
    if receipt.get("pool") not in POOLS:
        errors.append(f"{label}: pool must be one of {', '.join(sorted(POOLS))}")
    if receipt.get("terminal_status") not in TERMINAL_STATUSES:
        errors.append(f"{label}: terminal_status is not recognized")
    if not isinstance(receipt.get("counts_toward_topology"), bool):
        errors.append(f"{label}: counts_toward_topology must be boolean")

    for field in ("route", "parent_id", "launch_surface"):
        if field in receipt and not present(receipt[field]):
            errors.append(f"{label}: {field} must be non-empty")

    if receipt.get("pool") in EXTERNAL_POOLS and receipt.get("external_worker") is not True:
        errors.append(f"{label}: external pool receipts must set external_worker=true")

    if receipt.get("counts_toward_topology") is True:
        if receipt.get("terminal_status") != "completed":
            errors.append(f"{label}: topology-counted receipts must be completed")
        if not present(receipt.get("artifact_path")):
            errors.append(f"{label}: topology-counted receipts require artifact_path")
        if not present(receipt.get("accepted_conclusion")):
            errors.append(f"{label}: topology-counted receipts require accepted_conclusion")
        if receipt.get("pool") == "codex-native" and not present(receipt.get("child_id", "controller")):
            errors.append(f"{label}: codex-native topology receipts require child_id or controller marker")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipts", nargs="+", type=Path, help="JSON receipt file(s) to validate")
    args = parser.parse_args(argv)

    errors: list[str] = []
    count = 0
    for path in args.receipts:
        try:
            receipts = load_receipts(path)
        except Exception as exc:  # noqa: BLE001 - validator should report all user-facing load failures.
            errors.append(f"{path}: {exc}")
            continue
        for index, receipt in enumerate(receipts, start=1):
            count += 1
            errors.extend(validate_receipt(receipt, f"{path}#{index}"))

    if errors:
        print(json.dumps({"ok": False, "checked": count, "errors": errors}, indent=2))
        return 1
    print(json.dumps({"ok": True, "checked": count}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

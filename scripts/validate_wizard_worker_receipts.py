#!/usr/bin/env python3
"""Validate Wizard v4.2 worker receipt truth before topology counts are accepted."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import jsonschema


REQUIRED_ALWAYS = {
    "schema",
    "wizard_version",
    "route",
    "parent_id",
    "pool",
    "launch_surface",
    "terminal_status",
    "counts_toward_topology",
}
REQUIRED_WHEN_COUNTED = {"artifact_path", "accepted_conclusion"}

POOLS = {"codex-native", "claude-bridge", "gemini", "tmux", "tool"}
EXTERNAL_POOLS = {"claude-bridge", "gemini", "tmux"}
TERMINAL_STATUSES = {
    "completed",
    "failed",
    "timed_out",
    "blocked",
    "abandoned",
    "not_launched",
    "superseded",
}
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "system_v5/wizard/schemas/WIZARD_V4_2_WORKER_RECEIPT_SCHEMA.json"


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


def validate_receipt(receipt: dict[str, Any], label: str, *, require_artifacts: bool = False) -> list[str]:
    errors: list[str] = []
    try:
        schema = json.loads(SCHEMA_PATH.read_text())
        jsonschema.validate(receipt, schema)
    except jsonschema.ValidationError as exc:
        errors.append(f"{label}: schema validation failed: {exc.message}")
    except Exception as exc:  # noqa: BLE001 - keep validator failures user-facing.
        errors.append(f"{label}: could not load receipt schema: {exc}")

    missing = sorted(REQUIRED_ALWAYS - receipt.keys())
    if receipt.get("counts_toward_topology") is True:
        missing.extend(sorted(REQUIRED_WHEN_COUNTED - receipt.keys()))
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
    if receipt.get("pool") == "tool" and receipt.get("counts_toward_topology") is True:
        errors.append(f"{label}: tool receipts cannot count toward Wizard topology")

    if receipt.get("counts_toward_topology") is True:
        if receipt.get("terminal_status") != "completed":
            errors.append(f"{label}: topology-counted receipts must be completed")
        if not present(receipt.get("artifact_path")):
            errors.append(f"{label}: topology-counted receipts require artifact_path")
        if not present(receipt.get("accepted_conclusion")):
            errors.append(f"{label}: topology-counted receipts require accepted_conclusion")
        if receipt.get("pool") == "codex-native":
            has_child = present(receipt.get("child_id"))
            has_controller_marker = receipt.get("controller_marker") is True
            has_controller_justification = present(receipt.get("controller_marker_justification"))
            if not has_child and not has_controller_marker:
                errors.append(f"{label}: codex-native topology receipts require child_id or controller_marker=true")
            if has_controller_marker and not has_controller_justification:
                errors.append(f"{label}: controller_marker=true requires controller_marker_justification")
            if has_child and has_controller_marker:
                errors.append(f"{label}: controller_marker=true cannot be combined with child_id")

    if require_artifacts and present(receipt.get("artifact_path")):
        artifact = Path(str(receipt["artifact_path"])).expanduser()
        if not artifact.is_absolute():
            artifact = Path.cwd() / artifact
        if not artifact.exists():
            errors.append(f"{label}: artifact_path does not exist: {receipt['artifact_path']}")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipts", nargs="+", type=Path, help="JSON receipt file(s) to validate")
    parser.add_argument("--require-artifacts", action="store_true", help="Require non-empty artifact_path values to exist.")
    args = parser.parse_args(argv)

    errors: list[str] = []
    count = 0
    topology_keys: dict[tuple[str, str], str] = {}
    for path in args.receipts:
        try:
            receipts = load_receipts(path)
        except Exception as exc:  # noqa: BLE001 - validator should report all user-facing load failures.
            errors.append(f"{path}: {exc}")
            continue
        for index, receipt in enumerate(receipts, start=1):
            count += 1
            label = f"{path}#{index}"
            errors.extend(validate_receipt(receipt, label, require_artifacts=args.require_artifacts))
            if receipt.get("counts_toward_topology") is True:
                child_key = receipt.get("child_id") or ("controller" if receipt.get("controller_marker") is True else "")
                key = (str(receipt.get("parent_id", "")), str(child_key))
                if key in topology_keys:
                    errors.append(f"{label}: duplicate topology receipt for parent/child also seen at {topology_keys[key]}")
                else:
                    topology_keys[key] = label

    if errors:
        print(json.dumps({"ok": False, "checked": count, "errors": errors}, indent=2))
        return 1
    print(json.dumps({"ok": True, "checked": count}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Create a compact, source-bound index for one external-validation run."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


class ReceiptIndexError(ValueError):
    """Raised when a run receipt cannot be safely indexed."""


def _read_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReceiptIndexError(f"{label} is unreadable JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ReceiptIndexError(f"{label} must be a JSON object")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve_under(root: Path, value: object, *, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ReceiptIndexError(f"{label} must be a nonempty path string")
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = root / candidate
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise ReceiptIndexError(f"{label} is unavailable: {exc}") from exc
    if resolved != root and root not in resolved.parents:
        raise ReceiptIndexError(f"{label} escaped the declared run root")
    if not resolved.is_file():
        raise ReceiptIndexError(f"{label} must name a file")
    return resolved


def _directory_under(root: Path, value: object, *, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ReceiptIndexError(f"{label} must be a nonempty path string")
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = root / candidate
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise ReceiptIndexError(f"{label} is unavailable: {exc}") from exc
    if resolved != root and root not in resolved.parents:
        raise ReceiptIndexError(f"{label} escaped the declared run root")
    if not resolved.is_dir():
        raise ReceiptIndexError(f"{label} must name a directory")
    return resolved


def _markdown(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _api_text(receipt: dict[str, Any]) -> str:
    values: list[str] = []

    def collect(value: object, *, depth: int) -> None:
        if depth > 6:
            return
        if isinstance(value, dict):
            for key, nested in value.items():
                if key in {"exact_api", "exact_apis"}:
                    if isinstance(nested, str):
                        values.append(nested)
                    elif isinstance(nested, list):
                        values.extend(item for item in nested if isinstance(item, str))
                else:
                    collect(nested, depth=depth + 1)
        elif isinstance(value, list):
            for nested in value:
                collect(nested, depth=depth + 1)

    collect(receipt, depth=0)
    unique = list(dict.fromkeys(values))
    if len(unique) > 12:
        unique = unique[:12] + ["additional receipt-bound APIs"]
    return "; ".join(unique) or "receipt-specific witness"


def _write_new(path: Path, text: str) -> None:
    if path.exists():
        raise ReceiptIndexError("output must not already exist")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(text)


def build_index(*, run_root: Path) -> str:
    if not run_root.is_absolute():
        raise ReceiptIndexError("run_root must be absolute")
    try:
        root = run_root.resolve(strict=True)
    except OSError as exc:
        raise ReceiptIndexError(f"run_root is unavailable: {exc}") from exc
    if not root.is_dir():
        raise ReceiptIndexError("run_root must name a directory")

    aggregate_path = root / "external_validation_result.json"
    aggregate = _read_object(aggregate_path, label="external validation aggregate")
    components = aggregate.get("components")
    if not isinstance(components, dict):
        raise ReceiptIndexError("aggregate components must be an object")
    workload = components.get("integrated_workload")
    if not isinstance(workload, dict):
        raise ReceiptIndexError("aggregate integrated_workload component is missing")
    workload_artifact = workload.get("artifact")
    if not isinstance(workload_artifact, dict):
        raise ReceiptIndexError("integrated_workload artifact is missing")
    integrated_path = _resolve_under(
        root,
        workload_artifact.get("path"),
        label="integrated_workload artifact",
    )
    integrated = _read_object(integrated_path, label="integrated workload receipt")
    workload_root_value = workload.get("run_root")
    if workload_root_value is None:
        # r19 preceded the explicit nested-root receipt field.  Its runner
        # contract still fixed this name; retain the fallback only for that
        # known previous layout rather than searching the filesystem.
        workload_root_value = "01_integrated_workload"
    workload_root = _directory_under(
        root,
        workload_root_value,
        label="integrated_workload run root",
    )
    external_workload = integrated.get("external_workload")
    if not isinstance(external_workload, dict):
        raise ReceiptIndexError("integrated workload external_workload is missing")
    suite_artifact = external_workload.get("receipt")
    if not isinstance(suite_artifact, dict):
        raise ReceiptIndexError("capability suite artifact is missing")
    suite_path = _resolve_under(
        workload_root,
        suite_artifact.get("path"),
        label="capability suite artifact",
    )
    suite = _read_object(suite_path, label="capability suite receipt")
    suite_components = suite.get("components")
    if not isinstance(suite_components, list):
        raise ReceiptIndexError("capability suite components must be a list")

    lines = [
        "# ConstraintBox external validation index",
        "",
        "This is a receipt index, not a scientific, CR, portability, or release claim.",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Request | `{_markdown(aggregate.get('request_id'))}` |",
        f"| Aggregate disposition | `{_markdown(aggregate.get('disposition'))}` |",
        f"| Aggregate receipt SHA-256 | `{_sha256(aggregate_path)}` |",
        f"| Integrated receipt SHA-256 | `{_sha256(integrated_path)}` |",
        f"| Capability-suite SHA-256 | `{_sha256(suite_path)}` |",
        "",
        "## Controller stages",
        "",
        "| Stage | Disposition | Reason |",
        "|---|---|---|",
    ]
    stages = integrated.get("stages")
    if not isinstance(stages, list):
        raise ReceiptIndexError("integrated workload stages must be a list")
    for stage in stages:
        if not isinstance(stage, dict):
            raise ReceiptIndexError("integrated workload stage must be an object")
        lines.append(
            "| "
            + _markdown(stage.get("stage"))
            + " | `"
            + _markdown(stage.get("disposition"))
            + "` | "
            + _markdown(stage.get("reason"))
            + " |"
        )

    lines.extend(
        [
            "",
            "## External simulation profiles",
            "",
            "| Profile | State | Receipt result | Witness/API surface | Receipt SHA-256 | Independent replay |",
            "|---|---|---|---|---|---|",
        ]
    )
    for component in suite_components:
        if not isinstance(component, dict):
            raise ReceiptIndexError("capability component must be an object")
        capability_id = component.get("capability_id")
        result = component.get("result")
        if not isinstance(result, dict):
            raise ReceiptIndexError(f"{capability_id} result is missing")
        artifacts = result.get("artifacts")
        if not isinstance(artifacts, dict):
            raise ReceiptIndexError(f"{capability_id} artifacts are missing")
        receipt_path = _resolve_under(
            root,
            artifacts.get("capability_receipt"),
            label=f"{capability_id} capability receipt",
        )
        receipt = _read_object(receipt_path, label=f"{capability_id} capability receipt")
        replay = component.get("independent_replay_artifact")
        replay_text = _markdown(replay) if isinstance(replay, str) else "missing"
        lines.append(
            "| `"
            + _markdown(capability_id)
            + "` | `"
            + _markdown(component.get("state"))
            + "` | "
            + _markdown(receipt.get("reason"))
            + " | "
            + _markdown(_api_text(receipt))
            + " | `"
            + _sha256(receipt_path)
            + "` | `"
            + replay_text
            + "` |"
        )

    lev = components.get("leviathan_reference")
    if isinstance(lev, dict):
        lines.extend(
            [
                "",
                "## Optional live Lev comparison",
                "",
                "| Requested | Disposition | Reason | Artifact |",
                "|---|---|---|---|",
                "| "
                + _markdown(lev.get("requested"))
                + " | `"
                + _markdown(lev.get("disposition"))
                + "` | "
                + _markdown(lev.get("reason"))
                + " | "
                + _markdown((lev.get("artifact") or {}).get("path", "none"))
                + " |",
            ]
        )
    lines.extend(["", "Claim ceiling: " + _markdown(aggregate.get("claim_ceiling")), ""])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        text = build_index(run_root=args.run_root)
        output = args.output if args.output is not None else args.run_root / "external_validation_index.md"
        _write_new(output, text)
    except ReceiptIndexError as exc:
        parser.error(str(exc))
    print(str(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

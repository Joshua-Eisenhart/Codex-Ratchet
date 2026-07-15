#!/usr/bin/env python3
"""Deterministically validate Claude bridge routing, hashes, and non-gating scope."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from claude_bridge import (
    LAUNCH_CWD,
    PROVIDER,
    SCHEMA_ID,
    budget_summary,
    build_command,
    route_metadata,
    sha256_file,
)


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def validate_receipt(receipt: Any, *, verify_files: bool = True) -> list[str]:
    errors: list[str] = []
    if not isinstance(receipt, dict):
        return ["receipt must be a JSON object"]

    constants = {
        "schema": SCHEMA_ID,
        "provider": PROVIDER,
        "advisory_only": True,
        "gate_authority": False,
        "evidence_allowed": False,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "release_eligible": False,
        "official_launch_allowed": False,
        "scientific_claim_proven": False,
        "gate_decision": "not_applicable",
        "backend_model_truth_source": "output.modelUsage",
        "cwd": LAUNCH_CWD,
    }
    for key, expected in constants.items():
        if receipt.get(key) != expected:
            errors.append(f"{key} must equal {expected!r}")

    mode = receipt.get("execution_mode")
    if mode not in {"dry_run", "live"}:
        errors.append("execution_mode must be dry_run or live")

    route = receipt.get("route")
    if not isinstance(route, dict):
        errors.append("route must be an object")
    else:
        requested_model = route.get("requested_model")
        try:
            expected_route = route_metadata(requested_model)
        except (AttributeError, ValueError):
            errors.append("route.requested_model must be a non-empty string")
        else:
            if route != expected_route:
                errors.append("route does not match deterministic alias resolution")

    parsed = receipt.get("parsed")
    if not isinstance(parsed, dict):
        errors.append("parsed must be an object")
        parsed = {}
    models = parsed.get("models")
    if not isinstance(models, list) or not all(isinstance(item, str) for item in models):
        errors.append("parsed.models must be a string array")
        models = []
    model_usage = parsed.get("model_usage")
    if not isinstance(model_usage, dict):
        errors.append("parsed.model_usage must be an object copied from modelUsage")
        model_usage = {}
    if models != sorted(model_usage):
        errors.append("parsed.models must exactly equal sorted parsed.model_usage keys")
    if receipt.get("backend_models") != models:
        errors.append("backend_models must exactly mirror parsed modelUsage keys")

    budget = receipt.get("budget")
    if not isinstance(budget, dict):
        errors.append("budget must be an object")
    else:
        try:
            expected_budget = budget_summary(
                budget.get("requested_usd"), parsed.get("total_cost_usd")
            )
        except (TypeError, ValueError):
            errors.append("budget values are invalid")
        else:
            if budget != expected_budget:
                errors.append("budget summary does not match requested and observed cost")

    command = receipt.get("command")
    if not isinstance(command, list) or not all(isinstance(item, str) for item in command):
        errors.append("command must be a string array")
    elif isinstance(route, dict) and isinstance(budget, dict):
        fallback = receipt.get("fallback_route")
        fallback_model = ""
        if fallback is not None:
            if not isinstance(fallback, dict):
                errors.append("fallback_route must be null or an object")
            else:
                fallback_model = fallback.get("requested_model", "")
                try:
                    if fallback != route_metadata(fallback_model):
                        errors.append("fallback_route does not match deterministic alias resolution")
                except (AttributeError, ValueError):
                    errors.append("fallback_route requested model is invalid")
        try:
            expected_command = build_command(
                requested_model=route.get("requested_model", ""),
                budget=budget.get("requested_usd"),
                stream=receipt.get("stream"),
                tools=receipt.get("tools", ""),
                requested_cwd=receipt.get("requested_cwd", ""),
                effort=receipt.get("effort", ""),
                fallback_model=fallback_model,
            )
        except (TypeError, ValueError):
            errors.append("command inputs are invalid")
        else:
            if command != expected_command:
                errors.append("command does not match deterministic command construction")

    if not isinstance(receipt.get("provider_invoked"), bool):
        errors.append("provider_invoked must be boolean")
    if not isinstance(receipt.get("stream"), bool):
        errors.append("stream must be boolean")
    if not isinstance(receipt.get("timed_out"), bool):
        errors.append("timed_out must be boolean")
    timeout = receipt.get("timeout_sec")
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or timeout < 0:
        errors.append("timeout_sec must be non-negative")
    if not _is_int(receipt.get("wrapper_returncode")):
        errors.append("wrapper_returncode must be an integer")

    provider_returncode = receipt.get("provider_returncode")
    if mode == "dry_run":
        if receipt.get("provider_invoked") is not False:
            errors.append("dry_run must not invoke the provider")
        if provider_returncode is not None:
            errors.append("dry_run provider_returncode must be null")
        if receipt.get("timed_out") is not False:
            errors.append("dry_run cannot be timed_out")
        if parsed.get("dry_run") is not True:
            errors.append("dry_run parsed marker is missing")
        if receipt.get("wrapper_returncode") != 0:
            errors.append("dry_run wrapper_returncode must be zero")
    elif mode == "live":
        if receipt.get("provider_invoked") is not True:
            errors.append("live receipt must record provider_invoked true")
        if not _is_int(provider_returncode):
            errors.append("live provider_returncode must be an integer")
        else:
            if provider_returncode != 0:
                expected_wrapper_returncode = provider_returncode
            elif not parsed.get("parse_ok"):
                expected_wrapper_returncode = 3
            else:
                expected_wrapper_returncode = 0
            if receipt.get("wrapper_returncode") != expected_wrapper_returncode:
                errors.append("wrapper_returncode does not fail closed over provider and parse status")
        if receipt.get("timed_out") and provider_returncode != 124:
            errors.append("timed_out live receipt must use provider_returncode 124")

    for path_key, hash_key in (
        ("prompt_path", "prompt_sha256"),
        ("output_path", "output_sha256"),
    ):
        raw_path = receipt.get(path_key)
        expected_hash = receipt.get(hash_key)
        if not isinstance(raw_path, str) or not raw_path:
            errors.append(f"{path_key} must be a non-empty string")
            continue
        if not isinstance(expected_hash, str) or len(expected_hash) != 64:
            errors.append(f"{hash_key} must be a 64-character sha256")
            continue
        if verify_files:
            artifact = Path(raw_path)
            if not artifact.is_file():
                errors.append(f"{path_key} does not exist: {artifact}")
            elif sha256_file(artifact) != expected_hash:
                errors.append(f"{hash_key} does not match {path_key}")

    if mode == "dry_run" and verify_files:
        output_path = receipt.get("output_path")
        if isinstance(output_path, str) and Path(output_path).is_file():
            try:
                dry_output = json.loads(Path(output_path).read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"dry_run output must be valid JSON: {exc}")
            else:
                expected_dry_output = {
                    "kind": "claude_bridge_dry_run",
                    "provider_invoked": False,
                    "route": route,
                    "command": command,
                }
                if dry_output != expected_dry_output:
                    errors.append("dry_run output does not match receipt route and command")

    receipt_path = receipt.get("receipt_path")
    if not isinstance(receipt_path, str) or not receipt_path:
        errors.append("receipt_path must be a non-empty string")

    return errors


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--no-file-hashes", action="store_true", help="Validate structure only")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)]}, indent=2, sort_keys=True))
        return 2
    errors = validate_receipt(receipt, verify_files=not args.no_file_hashes)
    print(
        json.dumps(
            {
                "ok": not errors,
                "receipt": str(args.receipt),
                "errors": errors,
                "claim_ceiling": "receipt integrity and non-gating scope only",
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

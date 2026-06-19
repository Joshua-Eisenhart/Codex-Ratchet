#!/usr/bin/env python3
"""Validate formal-scout result receipts."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
RESULTS = ROOT / "results"


def pass_values(section: dict[str, Any]) -> list[bool]:
    values = []
    for row in section.values():
        if isinstance(row, dict) and "pass" in row:
            values.append(bool(row["pass"]))
    return values


def validate_formal_scout(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    positives = data.get("positive")
    graveyards = data.get("graveyard_companions")
    if not isinstance(positives, dict) or not positives:
        errors.append("positive section missing")
    if not isinstance(graveyards, dict) or not graveyards:
        errors.append("graveyard_companions section missing")
    boundary = data.get("boundary")
    if not isinstance(boundary, dict) or not boundary:
        errors.append("boundary section missing")
    if not data.get("why_not_v4_probes"):
        errors.append("why_not_v4_probes missing")
    nearby = data.get("nearby_variants")
    if not isinstance(nearby, dict) or not nearby.get("total"):
        errors.append("nearby_variants summary missing")
    elif nearby.get("passed") != nearby.get("total"):
        errors.append("nearby_variants did not all pass")
    if isinstance(positives, dict) and False in pass_values(positives):
        errors.append("one or more positive checks failed")
    if isinstance(graveyards, dict) and False in pass_values(graveyards):
        errors.append("one or more graveyard checks failed")
    if isinstance(boundary, dict) and False in pass_values(boundary):
        errors.append("one or more boundary checks failed")
    return errors


def validate_tool_capability(data: dict[str, Any]) -> list[str]:
    """Validate pre-admission tool-stack/lego-fit/consumer-gate receipts.

    These are intentionally not `formal_scout` results. They exist so the
    tool-stack and consumer gates can be simulated and tuned before the
    scientific ladder consumes them. The validator keeps their ceiling low while
    still checking that the receipt is operational rather than an import-only
    manifest or prose-only policy note.
    """
    errors: list[str] = []
    evidence_level = data.get("evidence_level")
    if evidence_level not in {"tool_capability", "tool_lego_fit", "consumer_gate"}:
        errors.append("evidence_level is not tool_capability/tool_lego_fit/consumer_gate")
    if data.get("formal_admission_allowed") is not False:
        errors.append("formal_admission_allowed is not false")
    if data.get("all_pass") is not True:
        errors.append("all_pass is not true")
    if evidence_level == "consumer_gate":
        positive = data.get("positive")
        negative = data.get("negative")
        boundary = data.get("boundary")
        if not isinstance(positive, dict) or not positive:
            errors.append("consumer_gate positive checks missing")
        elif False in pass_values(positive):
            errors.append("one or more consumer_gate positive checks failed")
        if not isinstance(negative, dict) or not negative:
            errors.append("consumer_gate negative checks missing")
        elif False in pass_values(negative):
            errors.append("one or more consumer_gate negative checks failed")
        if not isinstance(boundary, dict) or not boundary:
            errors.append("consumer_gate boundary checks missing")
        elif False in pass_values(boundary):
            errors.append("one or more consumer_gate boundary checks failed")
        if data.get("stage_movement_allowed") is not False:
            errors.append("stage_movement_allowed is not false")
        if data.get("stage4_unlock_allowed") is not False:
            errors.append("stage4_unlock_allowed is not false")
        allowed = data.get("allowed_next_uses") or data.get("eligible_consumers")
        if not isinstance(allowed, list) or not allowed:
            errors.append("consumer_gate allowed_next_uses/eligible_consumers missing")
        if not isinstance(data.get("blocked_downstream_consumers"), list) or not data.get("blocked_downstream_consumers"):
            errors.append("blocked_downstream_consumers missing")
        if not isinstance(data.get("receipt_schema_validation"), dict) or not data.get("receipt_schema_validation"):
            errors.append("receipt_schema_validation missing")
    else:
        summary = data.get("summary")
        if not isinstance(summary, dict):
            errors.append("summary missing")
        else:
            if summary.get("failed_or_blocked") not in ([], None):
                errors.append("failed_or_blocked is not empty")
            if summary.get("pass_count") != summary.get("probe_count"):
                errors.append("summary pass_count does not equal probe_count")
        tool_claims = data.get("tool_claim") or data.get("tool_claims")
        if not isinstance(tool_claims, dict) or not tool_claims:
            errors.append("tool_claim/tool_claims missing")
        else:
            required = {
                "tool",
                "api_surface",
                "observable",
                "positive",
                "negative",
                "boundary",
                "demotion_condition",
            }
            for name, claim in tool_claims.items():
                if not isinstance(claim, dict):
                    errors.append(f"tool claim {name} is not an object")
                    continue
                missing = sorted(field for field in required if not claim.get(field))
                if missing:
                    errors.append(f"tool claim {name} missing fields: {', '.join(missing)}")
        if not isinstance(data.get("engine_contract"), dict) or not data.get("engine_contract"):
            errors.append("engine_contract missing")
        if not isinstance(data.get("blocked_downstream_consumers"), list) or not data.get("blocked_downstream_consumers"):
            errors.append("blocked_downstream_consumers missing")
    if not data.get("source_path"):
        errors.append("source_path missing")
    if not data.get("source_sha256"):
        errors.append("source_sha256 missing")
    return errors


def validate(path: pathlib.Path) -> dict[str, Any]:
    data = json.loads(path.read_bytes().decode("utf-8"))
    errors = []
    classification = data.get("classification")
    if classification not in {"formal_scout", "scratch_diagnostic", "tool_lego_fit_probe"}:
        errors.append("classification is not formal_scout/scratch_diagnostic/tool_lego_fit_probe")
    if data.get("promotion_allowed") is not False:
        errors.append("promotion_allowed is not false")
    if not data.get("claim_ceiling"):
        errors.append("claim_ceiling missing")
    if "canonical" in str(data.get("claim_ceiling", "")).lower() and "does not admit" not in str(data.get("claim_ceiling", "")).lower():
        errors.append("claim_ceiling may overclaim")
    if classification == "formal_scout":
        errors.extend(validate_formal_scout(data))
    else:
        errors.extend(validate_tool_capability(data))
    if "rosetta_to_sim_contract" in data:
        errors.append("legacy rosetta_to_sim_contract key present")
    if data.get("blockers"):
        errors.append("blockers present")
    return {"path": str(path), "pass": not errors, "errors": errors}


def script_for_result(path: pathlib.Path) -> pathlib.Path:
    stem = path.name
    if not stem.endswith("_results.json"):
        raise ValueError(f"result name does not end with _results.json: {path}")
    return ROOT / f"sim_{stem.removesuffix('_results.json')}.py"


def tail_text(value: str | bytes | None, limit: int = 800) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")[-limit:]
    return value[-limit:]


def fresh_rerun(path: pathlib.Path, timeout_seconds: int) -> dict[str, Any]:
    script = script_for_result(path)
    if not script.exists():
        return {
            "result": str(path),
            "script": str(script),
            "pass": False,
            "errors": ["matching scout script missing"],
        }
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        proc = subprocess.run(
            [sys.executable, str(script)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            env=env,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "result": str(path),
            "script": str(script),
            "pass": False,
            "errors": [f"rerun timed out after {timeout_seconds}s"],
            "returncode": None,
            "stdout_tail": tail_text(exc.stdout),
            "stderr_tail": tail_text(exc.stderr),
        }
    errors = []
    if proc.returncode != 0:
        errors.append(f"rerun exited {proc.returncode}")
    if not path.exists():
        errors.append("expected result was not written")
    return {
        "result": str(path),
        "script": str(script),
        "pass": not errors,
        "errors": errors,
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-800:],
        "stderr_tail": proc.stderr[-800:],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=pathlib.Path)
    parser.add_argument(
        "--fresh-rerun",
        action="store_true",
        help="rerun matching scout scripts before validating result receipts",
    )
    parser.add_argument(
        "--fresh-rerun-timeout",
        type=int,
        default=120,
        help="timeout in seconds for each matching scout script rerun",
    )
    args = parser.parse_args()
    paths = args.paths or sorted(RESULTS.glob("*_results.json"))
    reruns = [fresh_rerun(path, args.fresh_rerun_timeout) for path in paths] if args.fresh_rerun else []
    rows = [validate(path) for path in paths]
    all_pass = all(row["pass"] for row in rows) and all(row["pass"] for row in reruns)
    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "fresh_rerun": args.fresh_rerun,
                "reruns": reruns,
                "results": rows,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

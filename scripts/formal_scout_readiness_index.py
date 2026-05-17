#!/usr/bin/env python3
"""Build a noncanonical readiness index for formal-scout receipts.

This index is a cleanup and routing surface only. It does not rerun, admit, or
promote formal scouts.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCOUT_ROOT = ROOT / "system_v5" / "ops" / "formal_scouts"
RESULTS = SCOUT_ROOT / "results"
README = SCOUT_ROOT / "README.md"
VALIDATOR = SCOUT_ROOT / "validate_formal_scout_results.py"
PROVIDER_VALIDATOR = SCOUT_ROOT / "validate_provider_receipts.py"
PROVIDER_RECEIPTS = SCOUT_ROOT / "provider_receipts"
OUT_JSON = ROOT / "system_v5" / "evidence" / "formal_scout_readiness_index.json"
OUT_MD = ROOT / "system_v5" / "docs" / "FORMAL_SCOUT_READINESS_INDEX.md"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_validator() -> Any:
    spec = importlib.util.spec_from_file_location("formal_scout_validator", VALIDATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load validator: {VALIDATOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_module(path: Path, module_name: str) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_json_error": str(exc)}
    return data if isinstance(data, dict) else {"_json_error": "result root is not an object"}


def key_style(data: dict[str, Any], upper_key: str, lower_key: str) -> str:
    has_upper = upper_key in data
    has_lower = lower_key in data
    if has_upper and has_lower:
        return "both"
    if has_upper:
        return "upper"
    if has_lower:
        return "lower"
    return "missing"


def result_stem(path: Path) -> str:
    return path.name.removesuffix("_results.json").removesuffix("_result.json")


def expected_script_for_result(path: Path) -> Path:
    stem = result_stem(path)
    if stem.startswith("sim_"):
        return SCOUT_ROOT / f"{stem}.py"
    return SCOUT_ROOT / f"sim_{stem}.py"


def alternate_script_for_result(path: Path) -> Path:
    stem = result_stem(path)
    if stem.startswith("sim_"):
        return SCOUT_ROOT / f"sim_{stem}.py"
    return expected_script_for_result(path)


def readme_result_paths() -> set[str]:
    if not README.exists():
        return set()
    text = README.read_text(encoding="utf-8", errors="replace")
    paths = set(re.findall(r"`(results/[^`]+?_results\.json)`", text))
    return {rel(SCOUT_ROOT / path) for path in paths}


def normalized_tool_depth(data: dict[str, Any]) -> dict[str, str]:
    raw = data.get("TOOL_INTEGRATION_DEPTH")
    if not isinstance(raw, dict):
        raw = data.get("tool_integration_depth")
    if not isinstance(raw, dict):
        return {}
    return {str(key).lower(): str(value).lower() for key, value in raw.items() if value is not None}


def backend_policy_violations(stem: str, tool_depth: dict[str, str]) -> list[str]:
    tokens = {token for token in stem.lower().replace("-", "_").split("_") if token}
    violations: list[str] = []
    if ("bridge" in tokens or "nonclassical" in tokens) and tool_depth.get("numpy") == "load_bearing":
        violations.append("load_bearing_numpy_in_bridge_or_nonclassical_named_scout")
    if "nonclassical" in tokens and tool_depth.get("pytorch") != "load_bearing":
        violations.append("nonclassical_missing_load_bearing_pytorch")
    return violations


def readiness_status(validation_pass: bool, source_exists: bool, errors: list[str]) -> str:
    if not source_exists:
        return "source_missing"
    if not validation_pass:
        return "validator_failed"
    if errors:
        return "needs_review"
    return "schema_ready"


def blockers_for(row: dict[str, Any]) -> list[str]:
    blockers = ["formal_scout_noncanonical", "fresh_rerun_not_performed"]
    if row["readiness_status"] != "schema_ready":
        blockers.append(row["readiness_status"])
    if not row["readme_indexed"]:
        blockers.append("readme_index_missing")
    if row["fresh_rerun_mapping_defect"]:
        blockers.append("fresh_rerun_mapping_defect")
    if row.get("fresh_rerun_dual_source_defect"):
        blockers.append("fresh_rerun_dual_source_defect")
    if row["classification"] != "formal_scout":
        blockers.append("classification_not_formal_scout")
    if row["promotion_allowed"] is not False:
        blockers.append("promotion_allowed_not_false")
    blockers.extend(row.get("backend_policy_violations") or [])
    return sorted(set(blockers))


def build_index() -> dict[str, Any]:
    validator = load_validator()
    readme_paths = readme_result_paths()
    result_paths = sorted(RESULTS.glob("*_results.json"))
    script_paths = sorted(SCOUT_ROOT.glob("sim_*.py"))
    script_set = {path.name for path in script_paths}
    result_stems = {result_stem(path) for path in result_paths}
    rows: list[dict[str, Any]] = []
    for path in result_paths:
        data = load_json(path)
        try:
            validation = validator.validate(path)
        except Exception as exc:
            validation = {"pass": False, "errors": [f"validator_exception:{exc}"]}
        expected_script = expected_script_for_result(path)
        alternate_script = alternate_script_for_result(path)
        expected_exists = expected_script.exists()
        alternate_exists = alternate_script.exists()
        source_exists = expected_exists or alternate_exists
        fresh_rerun_mapping_defect = bool(not expected_exists and alternate_exists)
        fresh_rerun_dual_source_defect = bool(expected_exists and alternate_exists and expected_script != alternate_script)
        errors = list(validation.get("errors") or [])
        stem = result_stem(path)
        tool_depth = normalized_tool_depth(data)
        row = {
            "result_path": rel(path),
            "stem": stem,
            "source_path": rel(expected_script if expected_exists else alternate_script) if source_exists else "",
            "validator_expected_source_path": rel(expected_script),
            "source_exists": source_exists,
            "fresh_rerun_mapping_defect": fresh_rerun_mapping_defect,
            "fresh_rerun_dual_source_defect": fresh_rerun_dual_source_defect,
            "readme_indexed": rel(path) in readme_paths,
            "validation_pass": bool(validation.get("pass")),
            "validation_errors": errors,
            "readiness_status": readiness_status(bool(validation.get("pass")), source_exists, errors),
            "classification": str(data.get("classification") or ""),
            "promotion_allowed": data.get("promotion_allowed"),
            "all_pass": data.get("all_pass"),
            "claim_ceiling_present": bool(data.get("claim_ceiling")),
            "claim_ceiling": str(data.get("claim_ceiling") or ""),
            "tool_manifest_key_style": key_style(data, "TOOL_MANIFEST", "tool_manifest"),
            "tool_depth_key_style": key_style(data, "TOOL_INTEGRATION_DEPTH", "tool_integration_depth"),
            "normalized_tool_depth": tool_depth,
            "backend_policy_violations": backend_policy_violations(stem, tool_depth),
            "public_status_label": "exists",
            "public_status_blockers": [
                "index_only_no_execution",
                "fresh_local_rerun_not_performed",
                "canonical_process_not_evaluated",
            ],
        }
        row["promotion_blockers"] = blockers_for(row)
        rows.append(row)

    source_without_result = []
    for script in script_paths:
        stem = script.name.removeprefix("sim_").removesuffix(".py")
        if stem not in result_stems and f"sim_{stem}" not in result_stems:
            source_without_result.append(rel(script))

    status_counts = Counter(row["readiness_status"] for row in rows)
    error_counts = Counter(error for row in rows for error in row["validation_errors"])
    blocker_counts = Counter(blocker for row in rows for blocker in row["promotion_blockers"])
    tool_manifest_key_style_counts = Counter(row["tool_manifest_key_style"] for row in rows)
    tool_depth_key_style_counts = Counter(row["tool_depth_key_style"] for row in rows)
    readme_missing = [row for row in rows if not row["readme_indexed"]]
    mapping_defects = [row for row in rows if row["fresh_rerun_mapping_defect"]]
    dual_source_defects = [row for row in rows if row["fresh_rerun_dual_source_defect"]]
    validator_failed = [row for row in rows if not row["validation_pass"]]
    source_missing = [row for row in rows if not row["source_exists"]]
    backend_policy_violations_rows = [row for row in rows if row["backend_policy_violations"]]
    provider_summary = provider_receipt_summary()
    return {
        "schema": "formal_scout_readiness_index.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "boundary": "readiness_index_only_not_rerun_not_admission_not_promotion",
        "summary": {
            "result_count": len(result_paths),
            "source_count": len(script_paths),
            "source_without_result_count": len(source_without_result),
            "validator_pass_count": sum(1 for row in rows if row["validation_pass"]),
            "validator_fail_count": len(validator_failed),
            "source_missing_count": len(source_missing),
            "readme_indexed_count": sum(1 for row in rows if row["readme_indexed"]),
            "readme_missing_count": len(readme_missing),
            "fresh_rerun_mapping_defect_count": len(mapping_defects),
            "fresh_rerun_dual_source_defect_count": len(dual_source_defects),
            "backend_policy_violation_count": len(backend_policy_violations_rows),
            "readiness_status_counts": dict(status_counts),
            "validation_error_counts": dict(error_counts),
            "promotion_blocker_counts": dict(blocker_counts),
            "tool_manifest_key_style_counts": dict(tool_manifest_key_style_counts),
            "tool_depth_key_style_counts": dict(tool_depth_key_style_counts),
            "provider_receipts": provider_summary["summary"],
        },
        "provider_receipt_failed_samples": provider_summary["failed_samples"],
        "source_without_result_samples": source_without_result[:100],
        "validator_failed_rows": validator_failed,
        "readme_missing_samples": readme_missing[:100],
        "fresh_rerun_mapping_defect_rows": mapping_defects,
        "fresh_rerun_dual_source_defect_rows": dual_source_defects,
        "backend_policy_violation_rows": backend_policy_violations_rows,
        "source_missing_rows": source_missing,
        "rows": rows,
    }


def provider_receipt_summary() -> dict[str, Any]:
    if not PROVIDER_RECEIPTS.exists() or not PROVIDER_VALIDATOR.exists():
        return {
            "summary": {
                "receipt_count": 0,
                "validator_available": PROVIDER_VALIDATOR.exists(),
                "validator_pass_count": 0,
                "validator_fail_count": 0,
            },
            "failed_samples": [],
        }
    validator = load_module(PROVIDER_VALIDATOR, "formal_scout_provider_validator")
    rows: list[dict[str, Any]] = []
    for path in sorted(PROVIDER_RECEIPTS.glob("*.json")):
        try:
            validation = validator.validate(path)
        except Exception as exc:
            validation = {"path": str(path), "pass": False, "errors": [f"validator_exception:{exc}"]}
        rows.append(
            {
                "path": rel(path),
                "validation_pass": bool(validation.get("pass")),
                "validation_errors": list(validation.get("errors") or []),
            }
        )
    failed = [row for row in rows if not row["validation_pass"]]
    error_counts = Counter(error for row in failed for error in row["validation_errors"])
    return {
        "summary": {
            "receipt_count": len(rows),
            "validator_available": True,
            "validator_pass_count": len(rows) - len(failed),
            "validator_fail_count": len(failed),
            "validation_error_counts": dict(error_counts),
        },
        "failed_samples": failed[:100],
    }


def write_markdown(index: dict[str, Any], path: Path) -> None:
    summary = index["summary"]
    lines = [
        "# Formal Scout Readiness Index",
        "",
        f"Generated: `{index['generated_at']}`",
        "",
        "Boundary: readiness index only. This does not rerun, admit, promote, or canonicalize formal scouts.",
        "",
        "## Summary",
        "",
        f"- Result receipts indexed: `{summary['result_count']}`",
        f"- Source harnesses indexed: `{summary['source_count']}`",
        f"- Source harnesses without result receipt: `{summary['source_without_result_count']}`",
        f"- Validator pass: `{summary['validator_pass_count']}`",
        f"- Validator fail: `{summary['validator_fail_count']}`",
        f"- README indexed receipts: `{summary['readme_indexed_count']}`",
        f"- README missing receipts: `{summary['readme_missing_count']}`",
        f"- Fresh-rerun mapping defects: `{summary['fresh_rerun_mapping_defect_count']}`",
        f"- Fresh-rerun dual-source defects: `{summary['fresh_rerun_dual_source_defect_count']}`",
        f"- Backend policy violations: `{summary['backend_policy_violation_count']}`",
        f"- Provider receipts indexed: `{summary['provider_receipts']['receipt_count']}`",
        f"- Provider receipt validator pass: `{summary['provider_receipts']['validator_pass_count']}`",
        f"- Provider receipt validator fail: `{summary['provider_receipts']['validator_fail_count']}`",
        "",
        "## Readiness Status Counts",
        "",
    ]
    for key, value in sorted(summary["readiness_status_counts"].items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{key}`: {value}")
    lines += ["", "## Validation Error Counts", ""]
    for key, value in sorted(summary["validation_error_counts"].items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{key}`: {value}")
    lines += ["", "## Promotion Blocker Counts", ""]
    for key, value in sorted(summary["promotion_blocker_counts"].items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{key}`: {value}")
    lines += ["", "## Tool Schema Key Styles", "", "### TOOL_MANIFEST", ""]
    for key, value in sorted(summary["tool_manifest_key_style_counts"].items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{key}`: {value}")
    lines += ["", "### TOOL_INTEGRATION_DEPTH", ""]
    for key, value in sorted(summary["tool_depth_key_style_counts"].items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{key}`: {value}")
    lines += ["", "## Provider Receipt Validation", ""]
    provider = summary["provider_receipts"]
    lines.append(f"- `pass`: {provider['validator_pass_count']}")
    lines.append(f"- `fail`: {provider['validator_fail_count']}")
    if provider.get("validation_error_counts"):
        lines += ["", "### Provider Error Counts", ""]
        for key, value in sorted(provider["validation_error_counts"].items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"- `{key}`: {value}")
    lines += [
        "",
        "## Validator Failed Rows",
        "",
        "| result | status | errors |",
        "| --- | --- | --- |",
    ]
    for row in index["validator_failed_rows"]:
        lines.append(
            "| `{result}` | `{status}` | {errors} |".format(
                result=row["result_path"],
                status=row["readiness_status"],
                errors=", ".join(row["validation_errors"]) or "-",
            )
        )
    lines += [
        "",
        "## Fresh-Rerun Mapping Defects",
        "",
        "| result | validator expected source | actual source |",
        "| --- | --- | --- |",
    ]
    if index["fresh_rerun_mapping_defect_rows"]:
        for row in index["fresh_rerun_mapping_defect_rows"]:
            lines.append(
                f"| `{row['result_path']}` | `{row['validator_expected_source_path']}` | `{row['source_path']}` |"
            )
    else:
        lines.append("| - | - | - |")
    lines += [
        "",
        "## Backend Policy Violations",
        "",
        "| result | source | violations |",
        "| --- | --- | --- |",
    ]
    if index["backend_policy_violation_rows"]:
        for row in index["backend_policy_violation_rows"]:
            lines.append(
                "| `{result}` | `{source}` | {violations} |".format(
                    result=row["result_path"],
                    source=row["source_path"] or "-",
                    violations=", ".join(row["backend_policy_violations"]) or "-",
                )
            )
    else:
        lines.append("| - | - | - |")
    lines += [
        "",
        "## README Missing Samples",
        "",
    ]
    if index["readme_missing_samples"]:
        for row in index["readme_missing_samples"][:50]:
            lines.append(f"- `{row['result_path']}`")
    else:
        lines.append("- none")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out", type=Path, default=OUT_JSON)
    parser.add_argument("--md-out", type=Path, default=OUT_MD)
    args = parser.parse_args()
    index = build_index()
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(index, indent=2), encoding="utf-8")
    write_markdown(index, args.md_out)
    summary = index["summary"]
    print(f"wrote {args.json_out}")
    print(f"wrote {args.md_out}")
    print(f"result_count={summary['result_count']}")
    print(f"validator_fail_count={summary['validator_fail_count']}")
    print(f"readme_missing_count={summary['readme_missing_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

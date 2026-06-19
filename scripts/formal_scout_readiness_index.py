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

from two_root_constraints import legacy_sections_all_pass


ROOT = Path(__file__).resolve().parents[1]
SCOUT_ROOT = ROOT / "system_v5" / "ops" / "formal_scouts"
RESULTS = SCOUT_ROOT / "results"
README = SCOUT_ROOT / "README.md"
VALIDATOR = SCOUT_ROOT / "validate_formal_scout_results.py"
PROVIDER_VALIDATOR = SCOUT_ROOT / "validate_provider_receipts.py"
PROVIDER_RECEIPTS = SCOUT_ROOT / "provider_receipts"
OUT_JSON = ROOT / "system_v5" / "evidence" / "formal_scout_readiness_index.json"
OUT_MD = ROOT / "system_v5" / "docs" / "FORMAL_SCOUT_READINESS_INDEX.md"
READINESS_DEBT_CLASSIFIER_RESULT = (
    "system_v5/ops/formal_scouts/results/formal_scout_readiness_debt_classification_probe_results.json"
)


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
        data = json.loads(path.read_bytes().decode("utf-8"))
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


def readme_declared_statuses() -> dict[str, str]:
    """Return explicit README readiness labels keyed by result path.

    Some README rows use prose in the readiness column. Only parse exact status
    labels so narrative descriptions do not become false status authority.
    """
    if not README.exists():
        return {}
    statuses = {"schema_ready", "validator_failed", "non_formal_boundary"}
    declared: dict[str, str] = {}
    for line in README.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith("| `sim_"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        result_match = re.fullmatch(r"`(results/[^`]+?_results\.json)`", cells[1])
        status_match = re.fullmatch(r"`([^`]+)`", cells[2])
        if result_match and status_match and status_match.group(1) in statuses:
            declared[rel(SCOUT_ROOT / result_match.group(1))] = status_match.group(1)
    return declared


def normalized_tool_depth(data: dict[str, Any]) -> dict[str, str]:
    raw = data.get("TOOL_INTEGRATION_DEPTH")
    if not isinstance(raw, dict):
        raw = data.get("tool_integration_depth")
    if not isinstance(raw, dict):
        return {}
    return {str(key).lower(): str(value).lower() for key, value in raw.items() if value is not None}


def all_pass_status(data: dict[str, Any]) -> tuple[bool | None, str]:
    for path in (
        ("all_pass",),
        ("summary", "all_pass"),
        ("summary", "all_passed"),
        ("positive", "all_pass"),
    ):
        cur: Any = data
        for key in path:
            if not isinstance(cur, dict) or key not in cur:
                cur = None
                break
            cur = cur[key]
        if isinstance(cur, bool):
            return cur, ".".join(path)
    if data.get("classification") == "formal_scout":
        return legacy_sections_all_pass(data), "derived_formal_scout_sections"
    return None, "missing"


def backend_policy_violations(stem: str, tool_depth: dict[str, str]) -> list[str]:
    tokens = {token for token in stem.lower().replace("-", "_").split("_") if token}
    violations: list[str] = []
    if "quarantine" in tokens or "baseline" in tokens or "legacy" in tokens:
        return violations
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


def validator_failure_classification(stem: str, row: dict[str, Any]) -> dict[str, str]:
    if row.get("validation_pass") or row.get("classification") != "formal_scout":
        return {"kind": "", "note": "", "resolution_surface": "", "handling": ""}
    if stem.startswith("engine_core_finite_boundary_"):
        return {
            "kind": "stale_noncovering_engine_core_finite_boundary_debt",
            "note": "finite-boundary quarantine receipt is red because the current target gate no longer clears the old EngineCore boundary",
            "resolution_surface": READINESS_DEBT_CLASSIFIER_RESULT,
            "handling": "preserve_red_nonclearance",
        }
    if stem == "grok_numpy_nonclassical_quarantine_audit_probe":
        return {
            "kind": "true_open_numpy_inventory_blocker",
            "note": "inventory/admission surfaces still contain NumPy-bearing nonclassical or bridge rows that require split, demotion, or source-native ports",
            "resolution_surface": READINESS_DEBT_CLASSIFIER_RESULT,
            "handling": "preserve_quarantine_or_split_legacy_classical_from_native_nonclassical",
        }
    if stem == "chiral_trajectory_persistent_homology_readout_feature_probe":
        return {
            "kind": "true_failed_readout_probe",
            "note": "persistence readout clears its own accuracy floor but loses to the raw-trajectory baseline and remains an open negative result",
            "resolution_surface": READINESS_DEBT_CLASSIFIER_RESULT,
            "handling": "preserve_negative_result_until_revised_design",
        }
    if stem in {
        "multiqubit_qit_reservoir_global_structure_probe",
        "multiqubit_qit_reservoir_grok_task_replication_probe",
        "xgi_hypergraph_multi_layer_coupling_centrality_probe",
    }:
        return {
            "kind": "overclaim_risk_failed_probe",
            "note": "positive controls or graveyards fail, so treating this as proof would overclaim the receipt",
            "resolution_surface": READINESS_DEBT_CLASSIFIER_RESULT,
            "handling": "preserve_failed_probe_or_rerun_revised_design",
        }
    return {
        "kind": "uncategorized_validator_failure",
        "note": "validator failure requires manual triage before it can be used as evidence",
        "resolution_surface": "",
        "handling": "manual_triage_required",
    }


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
    declared_readme_statuses = readme_declared_statuses()
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
        pass_value, pass_source = all_pass_status(data)
        row = {
            "result_path": rel(path),
            "stem": stem,
            "source_path": rel(expected_script if expected_exists else alternate_script) if source_exists else "",
            "validator_expected_source_path": rel(expected_script),
            "source_exists": source_exists,
            "fresh_rerun_mapping_defect": fresh_rerun_mapping_defect,
            "fresh_rerun_dual_source_defect": fresh_rerun_dual_source_defect,
            "readme_indexed": rel(path) in readme_paths,
            "readme_declared_status": declared_readme_statuses.get(rel(path)),
            "validation_pass": bool(validation.get("pass")),
            "validation_errors": errors,
            "readiness_status": readiness_status(bool(validation.get("pass")), source_exists, errors),
            "classification": str(data.get("classification") or ""),
            "promotion_allowed": data.get("promotion_allowed"),
            "raw_all_pass": data.get("all_pass"),
            "all_pass": pass_value,
            "derived_all_pass": pass_value,
            "all_pass_source": pass_source,
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
        if row["classification"] and row["classification"] != "formal_scout":
            row["readiness_status"] = "non_formal_boundary"
        row["readme_status_mismatch"] = bool(
            row["readme_declared_status"]
            and row["readme_declared_status"] != row["readiness_status"]
        )
        validator_failure = validator_failure_classification(stem, row)
        row["validator_failure_kind"] = validator_failure["kind"]
        row["validator_failure_note"] = validator_failure["note"]
        row["validator_failure_resolution_surface"] = validator_failure["resolution_surface"]
        row["validator_failure_handling"] = validator_failure["handling"]
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
    pass_source_counts = Counter(str(row["all_pass_source"]) for row in rows)
    tool_manifest_key_style_counts = Counter(row["tool_manifest_key_style"] for row in rows)
    tool_depth_key_style_counts = Counter(row["tool_depth_key_style"] for row in rows)
    validator_failure_kind_counts = Counter(
        row["validator_failure_kind"] for row in rows if row["validator_failure_kind"]
    )
    validator_failure_handling_counts = Counter(
        row["validator_failure_handling"] for row in rows if row["validator_failure_handling"]
    )
    readme_missing = [row for row in rows if not row["readme_indexed"]]
    readme_status_mismatches = [row for row in rows if row["readme_status_mismatch"]]
    mapping_defects = [row for row in rows if row["fresh_rerun_mapping_defect"]]
    dual_source_defects = [row for row in rows if row["fresh_rerun_dual_source_defect"]]
    validator_failed = [
        row for row in rows if not row["validation_pass"] and row["classification"] == "formal_scout"
    ]
    preserved_validator_failed = [
        row for row in validator_failed if str(row.get("validator_failure_handling", "")).startswith("preserve_")
    ]
    actionable_validator_failed = [
        row for row in validator_failed if row not in preserved_validator_failed
    ]
    non_formal_boundaries = [row for row in rows if row["classification"] and row["classification"] != "formal_scout"]
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
            "preserved_validator_fail_count": len(preserved_validator_failed),
            "actionable_validator_fail_count": len(actionable_validator_failed),
            "non_formal_boundary_count": len(non_formal_boundaries),
            "source_missing_count": len(source_missing),
            "readme_indexed_count": sum(1 for row in rows if row["readme_indexed"]),
            "readme_missing_count": len(readme_missing),
            "readme_status_mismatch_count": len(readme_status_mismatches),
            "fresh_rerun_mapping_defect_count": len(mapping_defects),
            "fresh_rerun_dual_source_defect_count": len(dual_source_defects),
            "backend_policy_violation_count": len(backend_policy_violations_rows),
            "readiness_status_counts": dict(status_counts),
            "validation_error_counts": dict(error_counts),
            "promotion_blocker_counts": dict(blocker_counts),
            "all_pass_source_counts": dict(pass_source_counts),
            "tool_manifest_key_style_counts": dict(tool_manifest_key_style_counts),
            "tool_depth_key_style_counts": dict(tool_depth_key_style_counts),
            "validator_failure_kind_counts": dict(validator_failure_kind_counts),
            "validator_failure_handling_counts": dict(validator_failure_handling_counts),
            "provider_receipts": provider_summary["summary"],
        },
        "provider_receipt_skipped_sidecar_samples": provider_summary["skipped_sidecar_samples"],
        "provider_receipt_failed_samples": provider_summary["failed_samples"],
        "provider_receipt_strict_live_failed_samples": provider_summary["strict_live_failed_samples"],
        "source_without_result_samples": source_without_result[:100],
        "validator_failed_rows": validator_failed,
        "preserved_validator_failed_rows": preserved_validator_failed,
        "actionable_validator_failed_rows": actionable_validator_failed,
        "non_formal_boundary_rows": non_formal_boundaries,
        "readme_missing_samples": readme_missing[:100],
        "readme_status_mismatch_rows": readme_status_mismatches,
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
                "validation_error_counts": {},
                "strict_live_validator_pass_count": 0,
                "strict_live_validator_fail_count": 0,
                "strict_live_validation_error_counts": {},
            },
            "skipped_sidecar_samples": [],
            "failed_samples": [],
            "strict_live_failed_samples": [],
        }
    validator = load_module(PROVIDER_VALIDATOR, "formal_scout_provider_validator")
    rows: list[dict[str, Any]] = []
    strict_rows: list[dict[str, Any]] = []
    all_paths = sorted(PROVIDER_RECEIPTS.glob("*.json"))
    skipped_sidecars = [
        {
            "path": rel(path),
            "reason": str(validator.sidecar_artifact_reason(path)),
        }
        for path in all_paths
        if str(validator.sidecar_artifact_reason(path))
    ]
    receipt_paths = validator.receipt_candidate_paths(PROVIDER_RECEIPTS)
    for path in receipt_paths:
        try:
            validation = validator.validate(path)
        except Exception as exc:
            validation = {"path": str(path), "pass": False, "errors": [f"validator_exception:{exc}"]}
        try:
            strict_validation = validator.validate(path, strict_live=True)
        except Exception as exc:
            strict_validation = {"path": str(path), "pass": False, "errors": [f"validator_exception:{exc}"]}
        rows.append(
            {
                "path": rel(path),
                "validation_pass": bool(validation.get("pass")),
                "validation_errors": list(validation.get("errors") or []),
            }
        )
        strict_rows.append(
            {
                "path": rel(path),
                "validation_pass": bool(strict_validation.get("pass")),
                "validation_errors": list(strict_validation.get("errors") or []),
            }
        )
    failed = [row for row in rows if not row["validation_pass"]]
    strict_failed = [row for row in strict_rows if not row["validation_pass"]]
    error_counts = Counter(error for row in failed for error in row["validation_errors"])
    strict_error_counts = Counter(error for row in strict_failed for error in row["validation_errors"])
    return {
        "summary": {
            "receipt_count": len(rows),
            "skipped_sidecar_count": len(skipped_sidecars),
            "validator_available": True,
            "validator_pass_count": len(rows) - len(failed),
            "validator_fail_count": len(failed),
            "validation_error_counts": dict(error_counts),
            "strict_live_validator_pass_count": len(strict_rows) - len(strict_failed),
            "strict_live_validator_fail_count": len(strict_failed),
            "strict_live_validation_error_counts": dict(strict_error_counts),
        },
        "skipped_sidecar_samples": skipped_sidecars[:100],
        "failed_samples": failed[:100],
        "strict_live_failed_samples": strict_failed[:100],
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
        f"- Formal-scout validator fail: `{summary['validator_fail_count']}`",
        f"- Preserved validator-red rows: `{summary['preserved_validator_fail_count']}`",
        f"- Actionable validator-red rows: `{summary['actionable_validator_fail_count']}`",
        f"- Non-formal boundary rows: `{summary['non_formal_boundary_count']}`",
        f"- README indexed receipts: `{summary['readme_indexed_count']}`",
        f"- README missing receipts: `{summary['readme_missing_count']}`",
        f"- README explicit-status mismatches: `{summary['readme_status_mismatch_count']}`",
        f"- Fresh-rerun mapping defects: `{summary['fresh_rerun_mapping_defect_count']}`",
        f"- Fresh-rerun dual-source defects: `{summary['fresh_rerun_dual_source_defect_count']}`",
        f"- Backend policy violations: `{summary['backend_policy_violation_count']}`",
        f"- Provider receipts indexed: `{summary['provider_receipts']['receipt_count']}`",
        f"- Provider JSON sidecars skipped: `{summary['provider_receipts'].get('skipped_sidecar_count', 0)}`",
        f"- Provider receipt validator pass: `{summary['provider_receipts']['validator_pass_count']}`",
        f"- Provider receipt validator fail: `{summary['provider_receipts']['validator_fail_count']}`",
        f"- Provider strict-live validator pass: `{summary['provider_receipts']['strict_live_validator_pass_count']}`",
        f"- Provider strict-live validator fail: `{summary['provider_receipts']['strict_live_validator_fail_count']}`",
        "",
        "## Readiness Status Counts",
        "",
    ]
    for key, value in sorted(summary["readiness_status_counts"].items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{key}`: {value}")
    lines += ["", "## Validation Error Counts", ""]
    for key, value in sorted(summary["validation_error_counts"].items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{key}`: {value}")
    lines += ["", "## Validator Failure Kind Counts", ""]
    if summary["validator_failure_kind_counts"]:
        for key, value in sorted(summary["validator_failure_kind_counts"].items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"- `{key}`: {value}")
    else:
        lines.append("- none")
    lines += ["", "## Validator Failure Handling Counts", ""]
    if summary["validator_failure_handling_counts"]:
        for key, value in sorted(summary["validator_failure_handling_counts"].items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"- `{key}`: {value}")
    else:
        lines.append("- none")
    lines += [
        "",
        "## Actionable vs Preserved Red Rows",
        "",
        f"- Preserved red rows: `{summary['preserved_validator_fail_count']}`",
        f"- Actionable red rows: `{summary['actionable_validator_fail_count']}`",
        "",
        "Preserved red rows are intentionally retained as negative, nonclearance, or overclaim-boundary evidence. They are not green proofs and not current readiness-repair debt. Actionable red rows require new repair, rerun, or manual triage before closeout.",
    ]
    lines += ["", "## Promotion Blocker Counts", ""]
    for key, value in sorted(summary["promotion_blocker_counts"].items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{key}`: {value}")
    lines += ["", "## Pass Source Counts", ""]
    for key, value in sorted(summary["all_pass_source_counts"].items(), key=lambda item: (-item[1], item[0])):
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
    lines.append("")
    lines.append("### Strict-Live Provider Provenance")
    lines.append("")
    lines.append("Normal provider validation is schema/proposal-boundary validation. Strict-live validation is the provenance check for completed live-provider receipts.")
    lines.append(f"- `pass`: {provider['strict_live_validator_pass_count']}")
    lines.append(f"- `fail`: {provider['strict_live_validator_fail_count']}")
    if provider.get("validation_error_counts"):
        lines += ["", "### Provider Error Counts", ""]
        for key, value in sorted(provider["validation_error_counts"].items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"- `{key}`: {value}")
    if provider.get("strict_live_validation_error_counts"):
        lines += ["", "### Strict-Live Provider Error Counts", ""]
        for key, value in sorted(provider["strict_live_validation_error_counts"].items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"- `{key}`: {value}")
    lines += [
        "",
        "## Validator Failed Rows",
        "",
        "| result | failure kind | handling | resolution surface | errors |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in index["validator_failed_rows"]:
        lines.append(
            "| `{result}` | `{kind}` | `{handling}` | `{resolution}` | {errors} |".format(
                result=row["result_path"],
                kind=row.get("validator_failure_kind") or "uncategorized_validator_failure",
                handling=row.get("validator_failure_handling") or "manual_triage_required",
                resolution=row.get("validator_failure_resolution_surface") or "-",
                errors=", ".join(row["validation_errors"]) or "-",
            )
        )
    lines += [
        "",
        "## Validator Failure Notes",
        "",
        "| kind | meaning |",
        "| --- | --- |",
    ]
    seen_notes = {}
    for row in index["validator_failed_rows"]:
        kind = row.get("validator_failure_kind") or "uncategorized_validator_failure"
        note = row.get("validator_failure_note") or "validator failure requires manual triage"
        seen_notes.setdefault(kind, note)
    for kind, note in sorted(seen_notes.items()):
        lines.append(f"| `{kind}` | {note} |")
    lines += [
        "",
        "## Non-Formal Boundary Rows",
        "",
        "| result | classification | blockers |",
        "| --- | --- | --- |",
    ]
    if index["non_formal_boundary_rows"]:
        for row in index["non_formal_boundary_rows"]:
            lines.append(
                "| `{result}` | `{classification}` | {blockers} |".format(
                    result=row["result_path"],
                    classification=row["classification"] or "-",
                    blockers=", ".join(row["promotion_blockers"]) or "-",
                )
            )
    else:
        lines.append("| - | - | - |")
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
    lines += [
        "",
        "## README Status Mismatches",
        "",
        "| result | README status | index status |",
        "| --- | --- | --- |",
    ]
    if index["readme_status_mismatch_rows"]:
        for row in index["readme_status_mismatch_rows"]:
            lines.append(
                f"| `{row['result_path']}` | `{row['readme_declared_status']}` | `{row['readiness_status']}` |"
            )
    else:
        lines.append("| - | - | - |")
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
    print(f"readme_status_mismatch_count={summary['readme_status_mismatch_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

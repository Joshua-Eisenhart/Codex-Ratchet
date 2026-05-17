#!/usr/bin/env python3
"""Shared validation helpers for sim/tool receipt admission.

The helpers are intentionally read-only and stdlib-only.  They validate the
controller-facing receipt facts that a runner DONE marker cannot prove alone:
result status, manifest/depth consistency, prior receipt existence, and scope
ceiling fields.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


VALID_CLASSIFICATIONS = {
    "canonical",
    "classical_baseline",
    "tool_lego_fit_probe",
    "supporting",
    "audit",
    "controller_audit",
}

VALID_DEPTHS = {
    "load_bearing",
    "supportive",
    None,
}

LEGACY_DEPTHS = {"decorative"}

STRICT_SCOPE_FIELDS = (
    "demotion_condition",
    "out_of_scope",
)

RUN_BOUNDARY_FIELDS = (
    "claim_ceiling",
    "next_lego_target",
    "promotion_condition",
    "blocked_until",
)

TOOL_ALIASES = {
    "np": "numpy",
    "numpy": "numpy",
    "torch": "pytorch",
    "pytorch": "pytorch",
    "z3": "z3",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def result_dir(root: Path | None = None) -> Path:
    base = root or repo_root()
    return base / "system_v4" / "probes" / "a2_state" / "sim_results"


def relpath(path: Path, root: Path | None = None) -> str:
    base = root or repo_root()
    try:
        return str(path.resolve().relative_to(base.resolve()))
    except ValueError:
        return str(path)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_tool_name(tool: str) -> str:
    normalized = str(tool).strip().lower().replace("-", "_")
    family = normalized.split(".", 1)[0]
    return TOOL_ALIASES.get(family, family)


def normalized_execution_kind(value: Any) -> str:
    normalized = str(value or "").strip().lower().replace("-", "_")
    if normalized in {
        "bridge",
        "qit_bridge",
        "nonclassical_bridge",
        "semiclassical",
        "semi_classical",
        "semiclassical_bridge",
        "semiclassical_szilard",
    }:
        return "bridge"
    if normalized == "nonclassical":
        return "nonclassical"
    if normalized == "classical":
        return "classical"
    return ""


def summary_all_pass(payload: dict[str, Any]) -> bool | None:
    summary = payload.get("summary")
    if isinstance(summary, dict):
        paired_counts = (
            ("tests_passed", "tests_total"),
            ("total_pass", "total_tests"),
            ("passed", "total"),
        )
        for passed_key, total_key in paired_counts:
            passed = summary.get(passed_key)
            total = summary.get(total_key)
            if isinstance(passed, int) and isinstance(total, int):
                if total <= 0:
                    return False
                return passed == total

        for key in ("all_pass", "all_passed"):
            value = summary.get(key)
            if isinstance(value, bool):
                return value

    for key in ("all_pass", "passed", "overall_pass"):
        value = payload.get(key)
        if isinstance(value, bool):
            return value

    return None


def failed_check_paths(
    obj: Any,
    path: str = "$",
    *,
    max_hits: int = 20,
    max_nodes: int = 5000,
    _state: dict[str, int] | None = None,
) -> list[str]:
    """Return paths where an explicit per-check pass flag is false."""
    state = _state if _state is not None else {"nodes": 0}
    if state["nodes"] >= max_nodes:
        return []
    state["nodes"] += 1
    hits: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if len(hits) >= max_hits or state["nodes"] >= max_nodes:
                break
            next_path = f"{path}.{key}"
            if key in {"pass", "passed"} and value is False:
                hits.append(next_path)
            else:
                hits.extend(
                    failed_check_paths(
                        value,
                        next_path,
                        max_hits=max_hits,
                        max_nodes=max_nodes,
                        _state=state,
                    )
                )
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            if len(hits) >= max_hits or state["nodes"] >= max_nodes:
                break
            hits.extend(
                failed_check_paths(
                    value,
                    f"{path}[{index}]",
                    max_hits=max_hits,
                    max_nodes=max_nodes,
                    _state=state,
                )
            )
    return hits[:max_hits]


def _finding(kind: str, severity: str, **fields: Any) -> dict[str, Any]:
    out = {"kind": kind, "severity": severity}
    out.update(fields)
    return out


def _prior_receipt_paths(value: Any) -> list[tuple[str | None, str]]:
    if isinstance(value, dict):
        return [(str(key), str(path)) for key, path in value.items()]
    if isinstance(value, list):
        return [(None, str(path)) for path in value]
    if isinstance(value, str) and value:
        return [(None, value)]
    return []


def _resolve_receipt_path(path_text: str, root: Path) -> Path | None:
    path = Path(path_text)
    if path.is_absolute():
        return path
    candidate = root / path
    if candidate.exists():
        return candidate
    if "/" not in path_text and not path_text.endswith("_results.json"):
        named = result_dir(root) / f"{path_text}_results.json"
        if named.exists():
            return named
    return candidate


def validate_result_payload(
    payload: Any,
    *,
    path: Path | None = None,
    root: Path | None = None,
    strict_scope: bool = False,
    require_executable: bool = False,
    require_run_boundary: bool = False,
) -> dict[str, Any]:
    """Validate one result JSON payload for receipt-admission use."""
    base = root or repo_root()
    facts: dict[str, Any] = {
        "result_json": relpath(path, base) if path else None,
        "name": None,
        "classification": None,
        "sim_execution_kind": None,
        "all_pass": None,
        "load_bearing_tools": [],
        "used_tools": [],
        "prior_receipts": [],
        "claim_ceiling": None,
        "next_lego_target": None,
        "promotion_condition": None,
        "blocked_until": None,
    }
    hard_findings: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    if not isinstance(payload, dict):
        hard_findings.append(
            _finding("non_object_result_json", "hard", actual_type=type(payload).__name__)
        )
        return {
            "facts": facts,
            "hard_findings": hard_findings,
            "warnings": warnings,
            "ok": False,
        }

    name = payload.get("name")
    facts["name"] = name
    if not isinstance(name, str) or not name.strip():
        hard_findings.append(_finding("missing_name", "hard"))

    classification = payload.get("classification")
    facts["classification"] = classification
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    execution_kind = normalized_execution_kind(
        payload.get("sim_execution_kind")
        or payload.get("SIM_EXECUTION_KIND")
        or summary.get("sim_execution_kind")
        or summary.get("SIM_EXECUTION_KIND")
    )
    facts["sim_execution_kind"] = execution_kind or None
    if classification not in VALID_CLASSIFICATIONS:
        hard_findings.append(
            _finding(
                "invalid_or_missing_classification",
                "hard",
                classification=classification,
                allowed=sorted(VALID_CLASSIFICATIONS),
            )
        )
    if require_executable and classification in {"supporting", "audit"}:
        hard_findings.append(
            _finding(
                "non_executable_receipt_classification",
                "hard",
                classification=classification,
            )
        )

    all_pass = summary_all_pass(payload)
    facts["all_pass"] = all_pass
    if all_pass is not True:
        hard_findings.append(
            _finding("result_not_all_pass", "hard", all_pass=all_pass)
        )

    manifest = payload.get("tool_manifest") or payload.get("TOOL_MANIFEST")
    depth = payload.get("tool_integration_depth") or payload.get("TOOL_INTEGRATION_DEPTH")

    if not isinstance(manifest, dict) or not manifest:
        hard_findings.append(_finding("missing_or_empty_tool_manifest", "hard"))
        manifest = {}

    if not isinstance(depth, dict) or not depth:
        hard_findings.append(_finding("missing_or_empty_tool_integration_depth", "hard"))
        depth = {}

    manifest_by_tool: dict[str, Any] = {}
    for raw_tool, entry in manifest.items():
        tool = str(raw_tool)
        if not isinstance(raw_tool, str):
            hard_findings.append(
                _finding(
                    "non_string_tool_manifest_key",
                    "hard",
                    tool=tool,
                    actual_type=type(raw_tool).__name__,
                )
            )
        if tool in manifest_by_tool:
            hard_findings.append(_finding("duplicate_tool_manifest_key", "hard", tool=tool))
            continue
        manifest_by_tool[tool] = entry

    depth_by_tool: dict[str, Any] = {}
    for raw_tool, level in depth.items():
        tool = str(raw_tool)
        if not isinstance(raw_tool, str):
            hard_findings.append(
                _finding(
                    "non_string_tool_integration_depth_key",
                    "hard",
                    tool=tool,
                    actual_type=type(raw_tool).__name__,
                )
            )
        if tool in depth_by_tool:
            hard_findings.append(
                _finding("duplicate_tool_integration_depth_key", "hard", tool=tool)
            )
            continue
        depth_by_tool[tool] = level

    for tool, entry in manifest_by_tool.items():
        if not isinstance(entry, dict):
            hard_findings.append(
                _finding("malformed_tool_manifest_entry", "hard", tool=str(tool))
            )
            continue

        tried = entry.get("tried")
        used = entry.get("used")
        reason = entry.get("reason")
        if used is True:
            facts["used_tools"].append(str(tool))
            if tried is not True:
                hard_findings.append(
                    _finding("used_tool_not_marked_tried", "hard", tool=str(tool))
                )
            if not isinstance(reason, str) or not reason.strip():
                hard_findings.append(
                    _finding("used_tool_missing_reason", "hard", tool=str(tool))
                )

    for tool, level in depth_by_tool.items():
        if tool not in manifest_by_tool:
            hard_findings.append(
                _finding("depth_tool_missing_manifest", "hard", tool=str(tool))
            )
        if level == "load_bearing":
            facts["load_bearing_tools"].append(str(tool))
        elif level not in VALID_DEPTHS:
            finding = _finding(
                "invalid_tool_integration_depth",
                "hard" if level not in LEGACY_DEPTHS else "warning",
                tool=str(tool),
                level=level,
                allowed=sorted(v for v in VALID_DEPTHS if v is not None) + ["None"],
            )
            if finding["severity"] == "hard":
                hard_findings.append(finding)
            else:
                warnings.append(finding)

    for tool in facts["used_tools"]:
        if tool not in depth_by_tool:
            hard_findings.append(
                _finding("used_tool_missing_integration_depth", "hard", tool=tool)
            )

    for tool in facts["load_bearing_tools"]:
        entry = manifest_by_tool.get(tool)
        if not isinstance(entry, dict) or entry.get("used") is not True:
            hard_findings.append(
                _finding("load_bearing_tool_not_used_in_manifest", "hard", tool=tool)
            )
        elif entry.get("tried") is not True:
            hard_findings.append(
                _finding("load_bearing_tool_not_tried_in_manifest", "hard", tool=tool)
            )

    load_bearing_canonical = {canonical_tool_name(tool) for tool in facts["load_bearing_tools"]}
    if execution_kind in {"bridge", "nonclassical"} and "numpy" in load_bearing_canonical:
        hard_findings.append(
            _finding(
                "numpy_load_bearing_blocked_for_bridge_or_nonclassical",
                "hard",
                sim_execution_kind=execution_kind,
            )
        )
    if execution_kind == "nonclassical" and "pytorch" not in load_bearing_canonical:
        hard_findings.append(
            _finding(
                "nonclassical_requires_load_bearing_pytorch",
                "hard",
                load_bearing_tools=sorted(load_bearing_canonical),
            )
        )

    if classification == "canonical":
        if not facts["load_bearing_tools"]:
            hard_findings.append(
                _finding("canonical_has_no_load_bearing_tool", "hard")
            )
        for section in ("positive", "negative", "boundary"):
            value = payload.get(section)
            if section not in payload:
                hard_findings.append(
                    _finding("canonical_missing_test_section", "hard", section=section)
                )
            elif _is_empty_test_section(value):
                hard_findings.append(
                    _finding("canonical_empty_test_section", "hard", section=section)
                )

        failed_paths = failed_check_paths(payload)
        if failed_paths:
            hard_findings.append(
                _finding(
                    "canonical_has_failed_checks",
                    "hard",
                    paths=failed_paths[:20],
                )
            )

    if classification == "classical_baseline":
        divergence = payload.get("divergence_log")
        if not isinstance(divergence, str) or not divergence.strip():
            hard_findings.append(
                _finding("classical_baseline_missing_divergence_log", "hard")
            )

    prior_value = payload.get("prior_function_receipts")
    prior_paths = _prior_receipt_paths(prior_value)
    for label, path_text in prior_paths:
        resolved = _resolve_receipt_path(path_text, base)
        prior_fact: dict[str, Any] = {
            "label": label,
            "declared": path_text,
            "path": relpath(resolved, base) if resolved else path_text,
            "exists": bool(resolved and resolved.exists()),
            "all_pass": None,
            "classification": None,
        }
        facts["prior_receipts"].append(prior_fact)
        if not resolved or not resolved.exists():
            hard_findings.append(
                _finding("missing_prior_function_receipt", "hard", prior=path_text)
            )
            continue
        try:
            prior_payload = load_json(resolved)
        except (OSError, json.JSONDecodeError) as exc:
            hard_findings.append(
                _finding(
                    "unreadable_prior_function_receipt",
                    "hard",
                    prior=relpath(resolved, base),
                    error=f"{exc.__class__.__name__}: {exc}",
                )
            )
            continue
        if isinstance(prior_payload, dict):
            prior_fact["all_pass"] = summary_all_pass(prior_payload)
            prior_fact["classification"] = prior_payload.get("classification")
            if prior_fact["all_pass"] is not True:
                hard_findings.append(
                    _finding(
                        "prior_function_receipt_not_all_pass",
                        "hard",
                        prior=relpath(resolved, base),
                    )
                )
            if prior_fact["classification"] != "canonical":
                hard_findings.append(
                    _finding(
                        "prior_function_receipt_not_canonical",
                        "hard",
                        prior=relpath(resolved, base),
                        classification=prior_fact["classification"],
                    )
                )
        else:
            hard_findings.append(
                _finding("prior_function_receipt_non_object", "hard", prior=path_text)
            )

    for key in STRICT_SCOPE_FIELDS:
        value = payload.get(key)
        missing = (
            not isinstance(value, list) or not value
            if key == "out_of_scope"
            else not isinstance(value, str) or not value.strip()
        )
        if missing:
            target = hard_findings if strict_scope else warnings
            target.append(_finding(f"missing_{key}", "hard" if strict_scope else "warning"))

    for key in RUN_BOUNDARY_FIELDS:
        value = payload.get(key)
        facts[key] = value if isinstance(value, str) else None
        missing = not isinstance(value, str) or not value.strip()
        if missing:
            target = hard_findings if require_run_boundary else warnings
            target.append(
                _finding(f"missing_{key}", "hard" if require_run_boundary else "warning")
            )

    return {
        "facts": facts,
        "hard_findings": hard_findings,
        "warnings": warnings,
        "ok": not hard_findings,
    }


def validate_result_path(
    path: Path,
    *,
    root: Path | None = None,
    strict_scope: bool = False,
    require_executable: bool = False,
    require_run_boundary: bool = False,
) -> dict[str, Any]:
    base = root or repo_root()
    try:
        payload = load_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "facts": {"result_json": relpath(path, base)},
            "hard_findings": [
                _finding(
                    "unreadable_result_json",
                    "hard",
                    error=f"{exc.__class__.__name__}: {exc}",
                )
            ],
            "warnings": [],
            "ok": False,
        }
    return validate_result_payload(
        payload,
        path=path,
        root=base,
        strict_scope=strict_scope,
        require_executable=require_executable,
        require_run_boundary=require_run_boundary,
    )


def _is_empty_test_section(value: Any) -> bool:
    if isinstance(value, dict):
        return len(value) == 0
    if isinstance(value, list):
        return len(value) == 0
    return True


def make_report(records: list[dict[str, Any]]) -> dict[str, Any]:
    hard_count = sum(len(record.get("hard_findings", [])) for record in records)
    warning_count = sum(len(record.get("warnings", [])) for record in records)
    return {
        "checked": len(records),
        "hard_finding_count": hard_count,
        "warning_count": warning_count,
        "all_pass": hard_count == 0,
        "records": records,
    }

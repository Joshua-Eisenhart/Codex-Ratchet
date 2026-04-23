#!/usr/bin/env python3
"""
Probe truth audit.

Fail-closed checks for result payload contradictions that should block controller
promotion, plus warning-grade checks for stale source/result drift.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "a2_state" / "sim_results"
OUT_PATH = RESULTS_DIR / "probe_truth_audit_results.json"
CONTROLLER_AUDIT_PATH = RESULTS_DIR / "controller_alignment_audit_results.json"
LIVE_ANCHOR_SPINE_PATH = RESULTS_DIR / "live_anchor_spine.json"
SOURCE_INDEX: dict[str, list[Path]] = {}
for source_path in sorted(ROOT.rglob("*.py")):
    SOURCE_INDEX.setdefault(source_path.name, []).append(source_path)


def matching_source_path(result_path: Path, payload: dict[str, Any]) -> Path | None:
    names = []
    payload_source = payload.get("source_file")
    if isinstance(payload_source, str) and payload_source:
        direct = Path(payload_source)
        if not direct.is_absolute():
            direct = ROOT / payload_source
        if direct.exists():
            return direct
    payload_name = payload.get("name")
    if isinstance(payload_name, str) and payload_name:
        names.append(payload_name)
    stem = result_path.name.removesuffix("_results.json")
    if stem not in names:
        names.append(stem)
    for name in names:
        for candidate_name in (f"sim_{name}.py", f"{name}.py"):
            matches = SOURCE_INDEX.get(candidate_name, [])
            if matches:
                return matches[0]
    return None


def summary_all_pass(payload: dict[str, Any]) -> bool | None:
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        return None
    for key in ("all_pass", "all_passed"):
        value = summary.get(key)
        if isinstance(value, bool):
            return value
    tests_passed = summary.get("tests_passed")
    tests_total = summary.get("tests_total")
    if isinstance(tests_passed, int) and isinstance(tests_total, int):
        return tests_passed == tests_total
    total_pass = summary.get("total_pass")
    total_tests = summary.get("total_tests")
    if isinstance(total_pass, int) and isinstance(total_tests, int):
        return total_pass == total_tests
    return None


def false_pass_paths(obj: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            next_path = f"{path}.{key}"
            if key == "pass" and value is False:
                hits.append(next_path)
            else:
                hits.extend(false_pass_paths(value, next_path))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            hits.extend(false_pass_paths(value, f"{path}[{idx}]"))
    return hits


def non_bool_pass_paths(obj: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            next_path = f"{path}.{key}"
            if (
                key == "pass"
                and value is not None
                and not isinstance(value, bool)
                and not isinstance(value, str)
                and not (isinstance(value, int) and path.endswith((".summary", ".totals")))
            ):
                hits.append(next_path)
            else:
                hits.extend(non_bool_pass_paths(value, next_path))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            hits.extend(non_bool_pass_paths(value, f"{path}[{idx}]"))
    return hits


def controller_sync_warning_findings(summary: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    if CONTROLLER_AUDIT_PATH.exists():
        try:
            controller = json.loads(CONTROLLER_AUDIT_PATH.read_text())
        except Exception as exc:  # noqa: BLE001
            findings.append({
                "kind": "controller_audit_unreadable",
                "result_json": CONTROLLER_AUDIT_PATH.name,
                "error": f"{exc.__class__.__name__}: {exc}",
            })
        else:
            embedded = controller.get("probe_truth_audit", {})
            if isinstance(embedded, dict):
                expected = {
                    "ok": summary.get("ok"),
                    "hard_finding_count": summary.get("hard_finding_count"),
                }
                actual = {
                    "ok": embedded.get("ok"),
                    "hard_finding_count": embedded.get("hard_finding_count"),
                }
                if actual != expected:
                    findings.append({
                        "kind": "controller_truth_snapshot_mismatch",
                        "result_json": CONTROLLER_AUDIT_PATH.name,
                        "expected": expected,
                        "actual": actual,
                    })

            if LIVE_ANCHOR_SPINE_PATH.exists():
                try:
                    spine = json.loads(LIVE_ANCHOR_SPINE_PATH.read_text())
                except Exception as exc:  # noqa: BLE001
                    findings.append({
                        "kind": "live_anchor_spine_unreadable",
                        "result_json": LIVE_ANCHOR_SPINE_PATH.name,
                        "error": f"{exc.__class__.__name__}: {exc}",
                    })
                else:
                    rows = spine.get("rows", [])
                    if isinstance(rows, list):
                        risky_entries = sum(
                            1 for row in rows
                            if isinstance(row, dict) and row.get("promotion_ready") is False
                        )
                        controller_risky = controller.get("summary", {}).get("trusted_spine_risky_entries")
                        if isinstance(controller_risky, int) and controller_risky != risky_entries:
                            findings.append({
                                "kind": "controller_live_spine_mismatch",
                                "result_json": CONTROLLER_AUDIT_PATH.name,
                                "expected_trusted_spine_risky_entries": risky_entries,
                                "actual_trusted_spine_risky_entries": controller_risky,
                            })

    return findings


def main() -> int:
    strict_stale = "--strict-stale" in sys.argv[1:]

    hard_findings: list[dict[str, Any]] = []
    warning_findings: list[dict[str, Any]] = []

    scanned = 0
    for result_path in sorted(RESULTS_DIR.glob("*_results.json")):
        scanned += 1
        try:
            payload = json.loads(result_path.read_text())
        except Exception as exc:  # noqa: BLE001
            hard_findings.append({
                "kind": "malformed_result_json",
                "result_json": result_path.name,
                "error": f"{exc.__class__.__name__}: {exc}",
            })
            continue
        if not isinstance(payload, dict):
            hard_findings.append({
                "kind": "non_object_result_json",
                "result_json": result_path.name,
                "type": type(payload).__name__,
            })
            continue
        classification = payload.get("classification")
        manifest = payload.get("tool_manifest")
        depth = payload.get("tool_integration_depth")

        if classification == "canonical":
            all_pass = summary_all_pass(payload)
            if all_pass is False:
                hard_findings.append({
                    "kind": "canonical_summary_false",
                    "result_json": result_path.name,
                })

            failed_paths = false_pass_paths(payload)
            if failed_paths:
                hard_findings.append({
                    "kind": "canonical_has_failed_checks",
                    "result_json": result_path.name,
                    "paths": failed_paths[:20],
                })

            weird_pass_paths = non_bool_pass_paths(payload)
            if weird_pass_paths:
                warning_findings.append({
                    "kind": "non_boolean_pass_fields",
                    "result_json": result_path.name,
                    "paths": weird_pass_paths[:20],
                })

        if isinstance(manifest, dict):
            for tool, info in manifest.items():
                if not isinstance(info, dict):
                    continue
                if info.get("used") is True and info.get("tried") is not True:
                    hard_findings.append({
                        "kind": "used_without_tried",
                        "result_json": result_path.name,
                        "tool": tool,
                    })

        if isinstance(depth, dict):
            for tool, integration in depth.items():
                if not isinstance(integration, str):
                    continue
                if "load" not in integration.lower():
                    continue
                info = manifest.get(tool, {}) if isinstance(manifest, dict) else {}
                if not isinstance(info, dict) or info.get("used") is not True:
                    hard_findings.append({
                        "kind": "load_bearing_without_used",
                        "result_json": result_path.name,
                        "tool": tool,
                        "depth": integration,
                    })

        source_path = matching_source_path(result_path, payload)
        if source_path is not None and source_path.stat().st_mtime > result_path.stat().st_mtime + 1:
            finding = {
                "kind": "stale_source_newer_than_result",
                "source": source_path.name,
                "result_json": result_path.name,
            }
            if strict_stale or classification == "canonical":
                hard_findings.append(finding)
            else:
                warning_findings.append(finding)

    summary = {
        "hard_finding_count": len(hard_findings),
        "warning_finding_count": len(warning_findings),
        "ok": len(hard_findings) == 0,
    }
    warning_findings.extend(controller_sync_warning_findings(summary))
    summary["warning_finding_count"] = len(warning_findings)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "strict_stale": strict_stale,
        "files_scanned": scanned,
        "summary": summary,
        "hard_findings": hard_findings,
        "warning_findings": warning_findings,
    }

    OUT_PATH.write_text(json.dumps(report, indent=2))

    print(f"Wrote {OUT_PATH}")
    print(f"files_scanned={scanned}")
    print(f"hard_finding_count={len(hard_findings)}")
    print(f"warning_finding_count={len(warning_findings)}")

    if hard_findings:
        print("PROBE TRUTH AUDIT FAILED")
        return 1

    print("PROBE TRUTH AUDIT PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Audit engine-lab visualizer wiring without browser automation."""

from __future__ import annotations

import json
import pathlib
import re
from typing import Any


CLASSIFICATION = "controller_audit"
classification = CLASSIFICATION
divergence_log = (
    "Controller audit for engine-lab visualizer receipt wiring. It verifies "
    "data globals, script tags, and no-promotion boundary language only; it "
    "does not execute browser rendering or promote QIT, GStack, axis, or engine claims."
)

LEGO_IDS = ["engine_lab_matrix", "visualizer_receipt_audit"]
PRIMARY_LEGO_IDS = ["engine_lab_matrix"]

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "loads JS-wrapped visualizer payloads"},
    "pathlib": {"tried": True, "used": True, "reason": "resolves repo-local visualizer/source paths"},
    "re": {"tried": True, "used": True, "reason": "extracts JS global assignments and script tags"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive", "re": "supportive"}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
ROOT = PROBE_DIR.parents[1]
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
VIS_DIR = ROOT / "visualizer"

REQUIRED_PAYLOADS = [
    {
        "path": VIS_DIR / "engine-lab-open-row-audit-data.js",
        "global": "ENGINE_LAB_OPEN_ROW_AUDIT_DATA",
        "required_summary_keys": ["audit_complete", "qit_or_axis_promotion_allowed"],
    },
    {
        "path": VIS_DIR / "engine-lab-next-work-queue-data.js",
        "global": "ENGINE_LAB_NEXT_WORK_QUEUE_DATA",
        "required_summary_keys": ["queue_complete", "active_uncovered_row_count", "qit_or_axis_promotion_allowed"],
    },
    {
        "path": VIS_DIR / "engine-lab-successor-coverage-data.js",
        "global": "ENGINE_LAB_SUCCESSOR_COVERAGE_DATA",
        "required_summary_keys": [
            "all_pass",
            "active_uncovered_row_count",
            "source_rows_preserved_negative",
            "schema_error_count",
            "qit_or_axis_promotion_allowed",
        ],
    },
    {
        "path": VIS_DIR / "szilard-open-row-consolidation-data.js",
        "global": "SZILARD_OPEN_ROW_CONSOLIDATION_DATA",
        "required_summary_keys": [
            "all_pass",
            "source_negative_count",
            "passing_successor_count",
            "fresh_source_count",
            "fresh_successor_count",
            "qit_or_axis_promotion_allowed",
        ],
    },
]

HTML_LOADERS = [
    VIS_DIR / "ratchet-visualizer.html",
    VIS_DIR / "engine-dual-stack.html",
]

REACT_PANEL = VIS_DIR / "rosetta_panel.jsx"
SIM_RECEIPT_PANEL = VIS_DIR / "iching_engine.jsx"


def read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_wrapped_payload(path: pathlib.Path, global_name: str) -> tuple[dict[str, Any] | None, str | None]:
    if not path.exists():
        return None, "missing_payload_file"
    text = read(path).strip()
    prefix = f"window.{global_name} = "
    if not text.startswith(prefix):
        return None, "missing_or_wrong_global_assignment"
    body = text[len(prefix) :]
    if body.endswith(";"):
        body = body[:-1]
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        return None, f"invalid_json_payload:{exc.msg}"
    if not isinstance(payload, dict):
        return None, "payload_not_object"
    return payload, None


def check_payload(entry: dict[str, Any]) -> dict[str, Any]:
    payload, error = load_wrapped_payload(entry["path"], entry["global"])
    summary = payload.get("summary", {}) if isinstance(payload, dict) else {}
    missing_summary_keys = [
        key for key in entry["required_summary_keys"] if not isinstance(summary, dict) or key not in summary
    ]
    rows = payload.get("rows") if isinstance(payload, dict) else None
    pass_check = error is None and not missing_summary_keys and isinstance(rows, list)
    return {
        "file": rel(entry["path"]),
        "global": entry["global"],
        "exists": entry["path"].exists(),
        "error": error,
        "missing_summary_keys": missing_summary_keys,
        "row_count": len(rows) if isinstance(rows, list) else None,
        "qit_or_axis_promotion_allowed": summary.get("qit_or_axis_promotion_allowed")
        if isinstance(summary, dict)
        else None,
        "pass": bool(pass_check),
    }


def check_loader(path: pathlib.Path) -> dict[str, Any]:
    text = read(path)
    script_srcs = re.findall(r"<script\b[^>]*\bsrc=[\"']([^\"']+)[\"'][^>]*>", text)
    script_names = {src.split("?", 1)[0].rsplit("/", 1)[-1] for src in script_srcs}
    missing_files = [entry["path"].name for entry in REQUIRED_PAYLOADS if entry["path"].name not in script_names]
    return {
        "file": str(path.relative_to(ROOT)),
        "missing_files": missing_files,
        "script_names": sorted(script_names),
        "pass": not missing_files,
    }


def check_react_panel() -> dict[str, Any]:
    text = read(REACT_PANEL)
    required_tokens = [
        "Engine Lab contract:",
        "ENGINE_LAB_OPEN_ROW_AUDIT_DATA",
        "ENGINE_LAB_NEXT_WORK_QUEUE_DATA",
        "ENGINE_LAB_SUCCESSOR_COVERAGE_DATA",
        "SZILARD_OPEN_ROW_CONSOLIDATION_DATA",
        "successor-layer coverage",
        "Szilard four-row consolidation",
        "source rows scientifically passing",
        "QIT/GStack/axis claims",
        "runtime engine",
    ]
    missing_tokens = [token for token in required_tokens if token not in text]
    direct_successor_all_pass_display = bool(
        re.search(r"engineLabSuccessorCoverage\s*&&.*summary\s*&&.*summary\.all_pass", text)
    )
    engine_lab_section = text[text.find("function EngineLabCoveragePanel") : text.find("function EngineRosettaWorkbench")]
    engine_lab_uses_admission_label = "source-backed" in engine_lab_section or "loaded/pass" in engine_lab_section
    balanced = {
        "paren": text.count("(") == text.count(")"),
        "brace": text.count("{") == text.count("}"),
        "bracket": text.count("[") == text.count("]"),
    }
    return {
        "file": str(REACT_PANEL.relative_to(ROOT)),
        "missing_tokens": missing_tokens,
        "direct_successor_all_pass_display": direct_successor_all_pass_display,
        "engine_lab_uses_admission_label": engine_lab_uses_admission_label,
        "balanced_delimiters": balanced,
        "pass": (
            not missing_tokens
            and not direct_successor_all_pass_display
            and not engine_lab_uses_admission_label
            and all(balanced.values())
        ),
    }


def check_sim_receipt_panel() -> dict[str, Any]:
    text = read(SIM_RECEIPT_PANEL)
    required_tokens = [
        "Engine lab open-row audit",
        "Engine lab next-work queue",
        "Engine lab successor coverage",
        "Szilard open-row consolidation",
        "successor-layer coverage only; source rows remain preserved-negative",
    ]
    missing_tokens = [token for token in required_tokens if token not in text]
    return {
        "file": str(SIM_RECEIPT_PANEL.relative_to(ROOT)),
        "missing_tokens": missing_tokens,
        "pass": not missing_tokens,
    }


def main() -> None:
    payload_checks = [check_payload(entry) for entry in REQUIRED_PAYLOADS]
    loader_checks = [check_loader(path) for path in HTML_LOADERS]
    react_panel_check = check_react_panel()
    sim_receipt_panel_check = check_sim_receipt_panel()
    positive = {
        "payload_globals_are_loadable": {
            "pass": all(row["pass"] for row in payload_checks),
            "payload_count": len(payload_checks),
        },
        "html_loaders_reference_payloads": {
            "pass": all(row["pass"] for row in loader_checks),
            "loader_count": len(loader_checks),
        },
        "react_panel_has_fail_closed_boundary": {
            "pass": react_panel_check["pass"],
        },
        "sim_receipt_index_lists_engine_lab_receipts": {
            "pass": sim_receipt_panel_check["pass"],
        },
    }
    negative = {
        "successor_all_pass_is_not_rendered_as_admission": {
            "pass": not react_panel_check["direct_successor_all_pass_display"],
        },
        "qit_gstack_axis_promotion_remains_closed": {
            "pass": all(row.get("qit_or_axis_promotion_allowed") is False for row in payload_checks),
            "payload_flags": {
                row["global"]: row.get("qit_or_axis_promotion_allowed") for row in payload_checks
            },
        },
    }
    all_pass = all(check["pass"] for check in positive.values()) and all(
        check["pass"] for check in negative.values()
    )
    result = {
        "name": "visualizer_engine_lab_receipt_audit",
        "classification": CLASSIFICATION,
        "sim_execution_kind": "controller_index",
        "controller_index_exempt": True,
        "controller_index_exemption_reason": (
            "This audit checks visualizer wiring and boundary text over existing "
            "receipt payloads; it does not create sim physics or admission claims."
        ),
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_files": {
            "visualizer_html": [str(path.relative_to(ROOT)) for path in HTML_LOADERS],
            "react_panel": str(REACT_PANEL.relative_to(ROOT)),
            "sim_receipt_panel": str(SIM_RECEIPT_PANEL.relative_to(ROOT)),
            "payloads": [str(entry["path"].relative_to(ROOT)) for entry in REQUIRED_PAYLOADS],
        },
        "positive": positive,
        "negative": negative,
        "summary": {
            "all_pass": bool(all_pass),
            "payload_count": len(payload_checks),
            "loader_count": len(loader_checks),
            "react_panel_boundary_pass": react_panel_check["pass"],
            "sim_receipt_index_pass": sim_receipt_panel_check["pass"],
            "qit_or_axis_promotion_allowed": False,
            "scope_note": divergence_log,
        },
        "payload_checks": payload_checks,
        "loader_checks": loader_checks,
        "react_panel_check": react_panel_check,
        "sim_receipt_panel_check": sim_receipt_panel_check,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULT_DIR / "visualizer_engine_lab_receipt_audit_results.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()

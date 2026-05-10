from __future__ import annotations

import importlib.util
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_PATH = REPO_ROOT / "system_v4" / "probes" / "sim_visualizer_engine_lab_receipt_audit.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("visualizer_engine_lab_receipt_audit", AUDIT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_engine_lab_visualizer_payload_globals_are_loadable() -> None:
    audit = _load_module()
    checks = [audit.check_payload(entry) for entry in audit.REQUIRED_PAYLOADS]

    assert all(check["pass"] for check in checks), checks


def test_engine_lab_visualizer_html_loaders_reference_payloads() -> None:
    audit = _load_module()
    checks = [audit.check_loader(path) for path in audit.HTML_LOADERS]

    assert all(check["pass"] for check in checks), checks
    assert all("engine-lab-successor-coverage-data.js" in check["script_names"] for check in checks)


def test_engine_lab_react_panel_preserves_no_promotion_boundary() -> None:
    audit = _load_module()
    check = audit.check_react_panel()

    assert check["pass"], check
    assert check["direct_successor_all_pass_display"] is False
    assert check["engine_lab_uses_admission_label"] is False


def test_engine_lab_sim_receipt_index_lists_receipts() -> None:
    audit = _load_module()
    check = audit.check_sim_receipt_panel()

    assert check["pass"], check


def test_payload_gate_fails_when_qit_promotion_flag_is_true(tmp_path: Path) -> None:
    audit = _load_module()
    payload = {
        "summary": {
            "all_pass": True,
            "active_uncovered_row_count": 0,
            "source_rows_preserved_negative": True,
            "schema_error_count": 0,
            "qit_or_axis_promotion_allowed": True,
        },
        "rows": [],
    }
    path = tmp_path / "engine-lab-successor-coverage-data.js"
    path.write_text("window.ENGINE_LAB_SUCCESSOR_COVERAGE_DATA = " + json.dumps(payload) + ";\n", encoding="utf-8")

    check = audit.check_payload(
        {
            "path": path,
            "global": "ENGINE_LAB_SUCCESSOR_COVERAGE_DATA",
            "required_summary_keys": [
                "all_pass",
                "active_uncovered_row_count",
                "source_rows_preserved_negative",
                "schema_error_count",
                "qit_or_axis_promotion_allowed",
            ],
        }
    )

    assert check["pass"] is True
    assert check["qit_or_axis_promotion_allowed"] is True
    assert not all(row.get("qit_or_axis_promotion_allowed") is False for row in [check])

import json
import runpy
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def run_python(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["python3", *args], cwd=ROOT, text=True, capture_output=True, check=False)


def test_worker_receipt_validator_accepts_counted_codex_receipt(tmp_path: Path) -> None:
    receipt = tmp_path / "receipt.json"
    receipt.write_text(
        json.dumps(
            {
                "schema": "wizard-v4.2-worker-receipt",
                "wizard_version": "v4.2",
                "route": "Decision",
                "parent_id": "parent-1",
                "child_id": "child-1",
                "pool": "codex-native",
                "launch_surface": "spawn_agent",
                "terminal_status": "completed",
                "artifact_path": "system_v5/wizard/receipts/example.json",
                "accepted_conclusion": "usable route result",
                "counts_toward_topology": True,
            }
        )
    )

    result = run_python("scripts/validate_wizard_worker_receipts.py", str(receipt))

    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["ok"] is True


def test_worker_receipt_validator_rejects_uncounted_external_blur(tmp_path: Path) -> None:
    receipt = tmp_path / "receipt.json"
    receipt.write_text(
        json.dumps(
            {
                "schema": "wizard-v4.2-worker-receipt",
                "wizard_version": "v4.2",
                "route": "Failure",
                "parent_id": "parent-2",
                "pool": "claude-bridge",
                "launch_surface": "claude task",
                "terminal_status": "completed",
                "artifact_path": "",
                "accepted_conclusion": "",
                "counts_toward_topology": True,
            }
        )
    )

    result = run_python("scripts/validate_wizard_worker_receipts.py", str(receipt))

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert any("external_worker=true" in error for error in payload["errors"])
    assert any("artifact_path" in error for error in payload["errors"])


def test_worker_receipt_validator_can_require_existing_artifacts(tmp_path: Path) -> None:
    receipt = tmp_path / "receipt.json"
    receipt.write_text(
        json.dumps(
            {
                "schema": "wizard-v4.2-worker-receipt",
                "wizard_version": "v4.2",
                "route": "Follow-Up",
                "parent_id": "parent-3",
                "child_id": "child-3",
                "pool": "tool",
                "launch_surface": "local command",
                "terminal_status": "completed",
                "artifact_path": "missing/receipt.json",
                "accepted_conclusion": "claimed result",
                "counts_toward_topology": True,
            }
        )
    )

    result = run_python("scripts/validate_wizard_worker_receipts.py", "--require-artifacts", str(receipt))

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert any("does not exist" in error for error in payload["errors"])


def test_worker_receipt_validator_rejects_codex_native_missing_child_id(tmp_path: Path) -> None:
    receipt = tmp_path / "receipt.json"
    receipt.write_text(
        json.dumps(
            {
                "schema": "wizard-v4.2-worker-receipt",
                "wizard_version": "v4.2",
                "route": "Decision",
                "parent_id": "parent-4",
                "pool": "codex-native",
                "launch_surface": "spawn_agent",
                "terminal_status": "completed",
                "artifact_path": "system_v5/wizard/receipts/example.json",
                "accepted_conclusion": "usable route result",
                "counts_toward_topology": True,
            }
        )
    )

    result = run_python("scripts/validate_wizard_worker_receipts.py", str(receipt))

    assert result.returncode == 1
    assert "child_id or controller_marker=true" in result.stdout


def test_worker_receipt_validator_rejects_tool_topology_count(tmp_path: Path) -> None:
    receipt = tmp_path / "receipt.json"
    receipt.write_text(
        json.dumps(
            {
                "schema": "wizard-v4.2-worker-receipt",
                "wizard_version": "v4.2",
                "route": "Tool Scout",
                "parent_id": "parent-5",
                "child_id": "tool-1",
                "pool": "tool",
                "launch_surface": "local command",
                "terminal_status": "completed",
                "artifact_path": "system_v5/wizard/receipts/tool.json",
                "accepted_conclusion": "tool check passed",
                "counts_toward_topology": True,
            }
        )
    )

    result = run_python("scripts/validate_wizard_worker_receipts.py", str(receipt))

    assert result.returncode == 1
    assert "tool receipts cannot count" in result.stdout


def test_worker_receipt_validator_rejects_duplicate_topology_pair(tmp_path: Path) -> None:
    receipt = tmp_path / "receipts.json"
    row = {
        "schema": "wizard-v4.2-worker-receipt",
        "wizard_version": "v4.2",
        "route": "Decision",
        "parent_id": "parent-6",
        "child_id": "child-6",
        "pool": "codex-native",
        "launch_surface": "spawn_agent",
        "terminal_status": "completed",
        "artifact_path": "system_v5/wizard/receipts/example.json",
        "accepted_conclusion": "usable route result",
        "counts_toward_topology": True,
    }
    receipt.write_text(json.dumps([row, row]))

    result = run_python("scripts/validate_wizard_worker_receipts.py", str(receipt))

    assert result.returncode == 1
    assert "duplicate topology receipt" in result.stdout


def test_runtime_audit_flags_live_v4_1_defaults() -> None:
    script = ROOT / "scripts/wizard_v4_2_runtime_audit.py"
    module_globals = runpy.run_path(str(script), run_name="wizard_v4_2_runtime_audit")

    findings = module_globals["scan_live_surfaces"]()

    assert findings == []


def test_runtime_audit_positive_detection_and_narrow_allow(tmp_path: Path) -> None:
    script = ROOT / "scripts/wizard_v4_2_runtime_audit.py"
    module_globals = runpy.run_path(str(script), run_name="wizard_v4_2_runtime_audit")
    drift_file = tmp_path / "drift.md"
    drift_file.write_text("Wizard v4.1 Max is the live default now.\n")
    scan = module_globals["scan_live_surfaces"]
    scan.__globals__["LIVE_SURFACES"] = [drift_file]
    scan.__globals__["LIVE_SURFACE_GLOBS"] = []

    findings = scan()

    assert findings
    assert findings[0]["code"] == "v4_1_live_default"


def test_runtime_audit_skip_preflight_is_not_ok() -> None:
    result = run_python("scripts/wizard_v4_2_runtime_audit.py", "--skip-preflight")

    assert result.returncode == 1
    assert json.loads(result.stdout)["skipped_preflight"] is True


def test_runtime_audit_rejects_empty_blocked_reason(tmp_path: Path) -> None:
    script = ROOT / "scripts/wizard_v4_2_runtime_audit.py"
    module_globals = runpy.run_path(str(script), run_name="wizard_v4_2_runtime_audit")
    base = tmp_path / "system_v5/ops/lego_scaling"
    base.mkdir(parents=True)
    (base / "empty_blocked.json").write_text("{}")

    heartbeat_status = module_globals["heartbeat_status"]
    heartbeat_status.__globals__["ROOT"] = tmp_path
    heartbeat = heartbeat_status({"lane_A": 0, "lane_B": 0, "lane_D": 0, "default": 0, "claimed": 0})

    assert heartbeat["status"] == "needs_next_micro_move_or_blocked_reason"

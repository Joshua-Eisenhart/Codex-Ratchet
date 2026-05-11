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


def test_runtime_audit_flags_live_v4_1_defaults() -> None:
    script = ROOT / "scripts/wizard_v4_2_runtime_audit.py"
    module_globals = runpy.run_path(str(script), run_name="wizard_v4_2_runtime_audit")

    findings = module_globals["scan_live_surfaces"]()

    assert findings == []

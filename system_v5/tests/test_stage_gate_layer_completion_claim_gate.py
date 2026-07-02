import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STAGE_GATE = ROOT / "scripts" / "stage_gate.py"


def write_open_stage_gate(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "active_stage": "coupling",
                "allow_default_queue_late_stage": True,
                "allow_tier_d_launch": True,
                "notes": ["test fixture only"],
            }
        ),
        encoding="utf-8",
    )


def run_stage_gate(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(STAGE_GATE), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_stage_gate_blocks_layer_completion_when_claim_gate_fails(tmp_path: Path) -> None:
    gate = tmp_path / "stage_gate.json"
    write_open_stage_gate(gate)
    claim = tmp_path / "claim.md"
    claim.write_text(
        "L2 Weyl spinor/chirality is fully simed and parent-complete.\n",
        encoding="utf-8",
    )

    result = run_stage_gate(
        "--stage-gate",
        str(gate),
        "--claim",
        "layer_completion",
        "--claim-file",
        str(claim),
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    requested = payload["requested_claim"]
    assert requested["allowed"] is False
    assert requested["layer_completion_claim_gate"]["ok"] is False


def test_stage_gate_blocks_axis0_when_claim_gate_fails(tmp_path: Path) -> None:
    gate = tmp_path / "stage_gate.json"
    write_open_stage_gate(gate)
    claim = tmp_path / "axis0_claim.md"
    claim.write_text(
        "Axis0 is unlocked from the current bounded scout receipts.\n",
        encoding="utf-8",
    )

    result = run_stage_gate(
        "--stage-gate",
        str(gate),
        "--claim",
        "axis0",
        "--claim-file",
        str(claim),
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    requested = payload["requested_claim"]
    assert requested["allowed"] is False
    assert requested["layer_completion_claim_gate"]["ok"] is False


def test_stage_gate_never_generically_admits_final_manifold(tmp_path: Path) -> None:
    gate = tmp_path / "stage_gate.json"
    write_open_stage_gate(gate)

    result = run_stage_gate("--stage-gate", str(gate), "--claim", "final_manifold")

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    requested = payload["requested_claim"]
    assert requested["allowed"] is False
    assert "claim-file" in requested["reason"]
    assert requested["layer_completion_claim_gate"]["status"] == "not_evaluated"


def test_stage_gate_marks_unrequested_sensitive_rows_not_evaluated_without_claim_file(
    tmp_path: Path,
) -> None:
    gate = tmp_path / "stage_gate.json"
    write_open_stage_gate(gate)

    result = run_stage_gate("--stage-gate", str(gate))

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    sensitive = payload["decisions"]["layer_completion"]
    assert sensitive["allowed"] is False
    assert sensitive["layer_completion_claim_gate"]["status"] == "not_evaluated"
    assert "ok" not in sensitive["layer_completion_claim_gate"]
    assert "claim gate failed" not in sensitive["reason"]


def test_stage_gate_still_blocks_bounded_sensitive_claim_after_claim_gate_passes(tmp_path: Path) -> None:
    gate = tmp_path / "stage_gate.json"
    write_open_stage_gate(gate)
    claim = tmp_path / "claim.md"
    claim.write_text(
        "L2 Weyl has bounded formal-scout coverage, not full layer completion.\n",
        encoding="utf-8",
    )

    result = run_stage_gate(
        "--stage-gate",
        str(gate),
        "--claim",
        "layer_completion",
        "--claim-file",
        str(claim),
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    requested = payload["requested_claim"]
    assert requested["allowed"] is False
    assert requested["layer_completion_claim_gate"]["ok"] is True
    assert "cannot admit" in requested["reason"]


def test_stage_gate_empty_sensitive_claim_file_keeps_claim_gate_failed(tmp_path: Path) -> None:
    gate = tmp_path / "stage_gate.json"
    write_open_stage_gate(gate)
    claim = tmp_path / "empty.md"
    claim.write_text("   \n", encoding="utf-8")

    result = run_stage_gate(
        "--stage-gate",
        str(gate),
        "--claim",
        "axis0",
        "--claim-file",
        str(claim),
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    requested = payload["requested_claim"]
    assert requested["allowed"] is False
    assert requested["layer_completion_claim_gate"]["ok"] is False
    assert "claim gate failed" in requested["reason"]

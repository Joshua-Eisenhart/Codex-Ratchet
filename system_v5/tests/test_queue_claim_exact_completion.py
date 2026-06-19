from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
QUEUE_CLAIM_PATH = REPO_ROOT / "scripts" / "queue_claim.py"


def _load_queue_claim_module():
    spec = importlib.util.spec_from_file_location("queue_claim_under_test", QUEUE_CLAIM_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.STRICT_WIZARD_QUEUE_ADMISSION = False
    module.CLAIM_REQUIRES_WIZARD_QUEUE_ADMISSION = False
    return module


def test_recovery_bypass_marker_must_be_valid(tmp_path: Path) -> None:
    marker = tmp_path / ".allow_admission_bypass_recovery"
    spec = importlib.util.spec_from_file_location("queue_claim_under_test_marker", QUEUE_CLAIM_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    module.STRICT_WIZARD_QUEUE_ADMISSION = True
    module.ALLOW_ADMISSION_BYPASS_RECOVERY = True
    module.ADMISSION_BYPASS_SENTINEL = marker

    marker.write_text("invalid json", encoding="utf-8")
    module.CLAIM_REQUIRES_WIZARD_QUEUE_ADMISSION = (
        module.STRICT_WIZARD_QUEUE_ADMISSION
        and not module._admission_bypass_marker_allows_recovery()
    )
    assert module.CLAIM_REQUIRES_WIZARD_QUEUE_ADMISSION is True

    marker.write_text(
        json.dumps(
            {
                "scope": "queue_claim",
                "enabled": True,
                "expires_at": 0,
            }
        ),
        encoding="utf-8",
    )
    module.CLAIM_REQUIRES_WIZARD_QUEUE_ADMISSION = (
        module.STRICT_WIZARD_QUEUE_ADMISSION
        and not module._admission_bypass_marker_allows_recovery()
    )
    assert module.CLAIM_REQUIRES_WIZARD_QUEUE_ADMISSION is True

    marker.write_text(
        json.dumps(
            {
                "scope": "queue_claim",
                "enabled": True,
                "expires_at": 9999999999,
            }
        ),
        encoding="utf-8",
    )
    module.CLAIM_REQUIRES_WIZARD_QUEUE_ADMISSION = (
        module.STRICT_WIZARD_QUEUE_ADMISSION
        and not module._admission_bypass_marker_allows_recovery()
    )
    assert module.CLAIM_REQUIRES_WIZARD_QUEUE_ADMISSION is False


def test_complete_uses_exact_claim_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_queue_claim_module()
    monkeypatch.setattr(module, "QUEUE_ROOT", tmp_path / "queue")

    module.enqueue("lane_A", "system_v4/probes/classical_baseline_first.py")
    module.enqueue("lane_A", "system_v4/probes/classical_baseline_second.py")

    first_claim = module.claim("lane_A", "laneA_w1")
    second_claim = module.claim("lane_A", "laneA_w1")

    first_payload = json.loads(Path(first_claim).read_text(encoding="utf-8"))
    second_payload = json.loads(Path(second_claim).read_text(encoding="utf-8"))

    done_path = module.complete(second_claim, 0, "/tmp/artifact-second.log")
    done_payload = json.loads(done_path.read_text(encoding="utf-8"))

    assert done_path.name == Path(second_claim).name
    assert done_payload["sim_path"] == second_payload["sim_path"]
    assert done_payload["artifact_path"] == "/tmp/artifact-second.log"
    assert Path(first_claim).exists(), f"stale claim for {first_payload['sim_path']} should remain untouched"


def test_complete_blocks_duplicate_done_records(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_queue_claim_module()
    monkeypatch.setattr(module, "QUEUE_ROOT", tmp_path / "queue")

    module.enqueue("lane_A", "system_v4/probes/classical_baseline_first.py")
    first_claim = module.claim("lane_A", "laneA_w1")
    assert first_claim is not None

    claimed_dir = tmp_path / "queue" / "claimed"
    claimed_dir.mkdir(parents=True, exist_ok=True)
    base = Path(first_claim).name.split(".json.")[0]
    duplicate_claim = claimed_dir / f"{base}.json.99999.test-host.dup-w1"
    duplicate_claim.write_text(Path(first_claim).read_text(encoding="utf-8"), encoding="utf-8")

    first_done = module.complete(first_claim, 0, "/tmp/artifact-first.log")

    done_dir = tmp_path / "queue" / "done"
    done_dir.mkdir(parents=True, exist_ok=True)
    (done_dir / f"{base}.json.11111.test-host.w2").write_text(
        first_done.read_text(encoding="utf-8"), encoding="utf-8"
    )
    done_count_before = len(list((tmp_path / "queue" / "done").glob("*.json.*")))
    second_blocked = module.complete(duplicate_claim, 0, "/tmp/artifact-second.log")

    assert first_done.parent.name == "done"
    assert second_blocked.parent.name == "blocked"

    blocked_payload = json.loads(Path(second_blocked).read_text(encoding="utf-8"))
    assert blocked_payload["blocked_reason"] == "done_duplicate_conflict"
    assert blocked_payload["artifact_path"] == "/tmp/artifact-second.log"

    done_count = len(list((tmp_path / "queue" / "done").glob("*.json.*")))
    blocked_count = len(list((tmp_path / "queue" / "blocked").glob("*.json*")))
    assert done_count == done_count_before
    assert blocked_count == 1


def test_resolve_claim_path_fails_closed_when_worker_is_ambiguous(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_queue_claim_module()
    monkeypatch.setattr(module, "QUEUE_ROOT", tmp_path / "queue")

    module.enqueue("lane_A", "system_v4/probes/classical_baseline_first.py")
    module.enqueue("lane_A", "system_v4/probes/classical_baseline_second.py")
    module.claim("lane_A", "laneA_w1")
    module.claim("lane_A", "laneA_w1")

    with pytest.raises(RuntimeError, match="ambiguous claimed item"):
        module._resolve_claim_path(claim_path=None, worker="laneA_w1")


def test_complete_blocks_nonzero_exit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_queue_claim_module()
    monkeypatch.setattr(module, "QUEUE_ROOT", tmp_path / "queue")

    module.enqueue("lane_A", "system_v4/probes/classical_baseline_bad.py")
    claim = module.claim("lane_A", "laneA_w1")

    blocked_path = module.complete(claim, 2, "/tmp/artifact-bad.log")
    blocked_payload = json.loads(blocked_path.read_text(encoding="utf-8"))

    assert blocked_path.parent.name == "blocked"
    assert blocked_payload["blocked_reason"] == "exit_code_2"
    assert Path(claim).exists() is False


def test_complete_require_receipt_blocks_failed_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_queue_claim_module()
    monkeypatch.setattr(module, "QUEUE_ROOT", tmp_path / "queue")
    monkeypatch.setattr(
        module,
        "_validate_receipt",
        lambda path: subprocess.CompletedProcess(["validate"], 1, "bad receipt", ""),
    )

    module.enqueue("lane_A", "system_v4/probes/classical_baseline_bad_receipt.py")
    claim = module.claim("lane_A", "laneA_w1")

    blocked_path = module.complete(claim, 0, "/tmp/artifact.log", require_receipt=True)
    blocked_payload = json.loads(blocked_path.read_text(encoding="utf-8"))

    assert blocked_path.parent.name == "blocked"
    assert blocked_payload["blocked_reason"] == "receipt_validation_failed"
    assert blocked_payload["receipt_validation_exit_code"] == 1


def test_complete_require_receipt_admits_successful_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_queue_claim_module()
    monkeypatch.setattr(module, "QUEUE_ROOT", tmp_path / "queue")
    monkeypatch.setattr(
        module,
        "_validate_receipt",
        lambda path: subprocess.CompletedProcess(["validate"], 0, '{"all_pass": true}', ""),
    )

    module.enqueue("lane_A", "system_v4/probes/classical_baseline_good_receipt.py")
    claim = module.claim("lane_A", "laneA_w1")

    done_path = module.complete(claim, 0, "/tmp/artifact.log", require_receipt=True)
    done_payload = json.loads(done_path.read_text(encoding="utf-8"))

    assert done_path.parent.name == "done"
    assert done_payload["receipt_admission"] == "strict_executable_run_boundary"


def test_complete_requires_claimed_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_queue_claim_module()
    monkeypatch.setattr(module, "QUEUE_ROOT", tmp_path / "queue")

    lane_dir = tmp_path / "queue" / "lane_A"
    lane_dir.mkdir(parents=True)
    unclaimed = lane_dir / "item.json"
    unclaimed.write_text('{"sim_path": "system_v4/probes/sim_unclaimed.py"}', encoding="utf-8")

    with pytest.raises(ValueError, match="queue/claimed"):
        module.complete(unclaimed, 0, "/tmp/artifact.log")

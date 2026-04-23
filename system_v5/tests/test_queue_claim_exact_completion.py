from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
QUEUE_CLAIM_PATH = REPO_ROOT / "scripts" / "queue_claim.py"


def _load_queue_claim_module():
    spec = importlib.util.spec_from_file_location("queue_claim_under_test", QUEUE_CLAIM_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_complete_uses_exact_claim_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_queue_claim_module()
    monkeypatch.setattr(module, "QUEUE_ROOT", tmp_path / "queue")

    module.enqueue("lane_A", "system_v4/probes/sim_first.py")
    module.enqueue("lane_A", "system_v4/probes/sim_second.py")

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


def test_resolve_claim_path_fails_closed_when_worker_is_ambiguous(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_queue_claim_module()
    monkeypatch.setattr(module, "QUEUE_ROOT", tmp_path / "queue")

    module.enqueue("lane_A", "system_v4/probes/sim_first.py")
    module.enqueue("lane_A", "system_v4/probes/sim_second.py")
    module.claim("lane_A", "laneA_w1")
    module.claim("lane_A", "laneA_w1")

    with pytest.raises(RuntimeError, match="ambiguous claimed item"):
        module._resolve_claim_path(claim_path=None, worker="laneA_w1")

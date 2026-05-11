import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BLOCKED_REASON = ROOT / "system_v5/ops/lego_scaling/blocked_coupling_prereq_refresh_20260511.json"


def queue_counts() -> dict[str, int]:
    result = subprocess.run(
        ["python3", "scripts/queue_claim.py", "counts"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(result.stdout)


def test_queue_is_either_moving_or_has_current_blocked_reason() -> None:
    counts = queue_counts()
    active = counts.get("lane_A", 0) > 0 or counts.get("lane_B", 0) > 0 or counts.get("claimed", 0) > 0

    assert active or BLOCKED_REASON.exists()
    if not active:
        data = json.loads(BLOCKED_REASON.read_text())
        assert data.get("kind") == "blocked_reason"
        assert data.get("blocked_candidates") or data.get("next_admissible_step") or data.get("recommended_next_move")

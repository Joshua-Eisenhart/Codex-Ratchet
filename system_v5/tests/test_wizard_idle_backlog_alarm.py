import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_runtime_audit_flags_idle_backlog() -> None:
    result = subprocess.run(
        ["python3", "scripts/wizard_v4_2_runtime_audit.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    data = json.loads(result.stdout)

    if data["queue_counts"].get("blocked", 0) > 0 and not any(
        data["queue_counts"].get(key, 0) for key in ("lane_A", "lane_B", "claimed")
    ):
        assert result.returncode == 1
        assert data["sim_heartbeat"]["status"] == "runner_idle_with_backlog"
        assert data["sim_heartbeat"]["dominant_blocked_reason"]["count"] > 0

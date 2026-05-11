import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "system_v4/probes/a2_state/sim_results/sim_runner_taxonomy_audit_results.json"


def test_runner_taxonomy_unknowns_are_named() -> None:
    result = subprocess.run(
        ["python3", "scripts/sim_runner_taxonomy_audit.py", "--strict"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert REPORT.exists(), result.stdout + result.stderr
    data = json.loads(REPORT.read_text())
    unknown_count = data["summary"]["unknown_count"]
    unknown_samples = data.get("unknown_samples") or []

    assert result.returncode == (1 if unknown_count else 0)
    assert len(unknown_samples) == unknown_count
    assert all(row.get("sim") and row.get("runner_class_reason") for row in unknown_samples)

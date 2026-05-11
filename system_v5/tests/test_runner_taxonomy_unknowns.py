import json
import subprocess
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "system_v4/probes/a2_state/sim_results/sim_runner_taxonomy_audit_results.json"
ALLOWLIST = ROOT / "system_v5/docs/RUNNER_TAXONOMY_UNKNOWN_ALLOWLIST.md"


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


def test_runner_taxonomy_unknowns_are_allowlisted_debt_with_review_date() -> None:
    subprocess.run(
        ["python3", "scripts/runner_taxonomy_unknowns_report.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    report = json.loads((ROOT / "system_v5/ops/runner_taxonomy_unknowns.json").read_text())
    text = ALLOWLIST.read_text()
    allowlisted = {
        line.strip()[3:-1]
        for line in text.splitlines()
        if line.strip().startswith("- `") and line.strip().endswith("`")
    }
    review_line = next(line for line in text.splitlines() if line.startswith("review_by:"))
    review_by = date.fromisoformat(review_line.split(":", 1)[1].strip())

    assert review_by >= date.today()
    for row in report["rows"]:
        assert row["sim"] in allowlisted

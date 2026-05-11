import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_runtime_audit_surfaces_ops_report_freshness() -> None:
    result = subprocess.run(
        ["python3", "scripts/wizard_v4_2_runtime_audit.py", "--skip-preflight", "--accept-skipped-preflight"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    payload = json.loads(result.stdout)

    assert "ops_reports_freshness" in payload["checks"]
    freshness = payload["checks"]["ops_reports_freshness"]
    assert freshness["reports"]
    assert any(report["path"] == "system_v5/ops/proposal_apply_preview.json" for report in freshness["reports"])


def test_proposal_apply_contract_names_owner_gate() -> None:
    text = (ROOT / "system_v5/docs/PROPOSAL_APPLY_CONTRACT.md").read_text()

    assert "owner review" in text
    assert "Dry-run reports" in text
    assert "Applied means" in text


def test_never_run_top_families_have_triage_rules() -> None:
    report = json.loads((ROOT / "system_v5/ops/never_run_cohorts.json").read_text())
    text = (ROOT / "system_v5/docs/NEVER_RUN_TRIAGE.md").read_text()
    top_families = list(report["family_counts"].keys())[:15]

    assert "review_required_before_queueing" in text
    for family in top_families:
        assert f"`{family}`" in text


def test_taxonomy_unknowns_are_allowlisted_by_path() -> None:
    report = json.loads((ROOT / "system_v5/ops/runner_taxonomy_unknowns.json").read_text())
    text = (ROOT / "system_v5/docs/RUNNER_TAXONOMY_UNKNOWN_ALLOWLIST.md").read_text()

    for row in report["rows"]:
        assert row["sim"] in text

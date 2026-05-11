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
    assert "contract_lint_summary" in payload["checks"]
    assert "never_run_summary" in payload["checks"]
    assert "taxonomy_unknown_allowlist" in payload["checks"]
    freshness = payload["checks"]["ops_reports_freshness"]
    assert freshness["ok"]
    assert freshness["source_file_count"] > 0
    assert freshness["newest_source_mtime"]
    assert freshness["reports"]
    assert any(report["path"] == "system_v5/ops/proposal_apply_preview.json" for report in freshness["reports"])
    assert payload["checks"]["contract_lint_summary"]["violation_total"] >= 0
    assert "never_run_total" in payload["checks"]["never_run_summary"]
    next_check = payload["sim_heartbeat"]["dominant_blocked_reason_next_check"]
    assert next_check is None or {
        "owner_surface",
        "next_check",
    }.issubset(next_check)


def test_contract_lint_debt_density_does_not_regress() -> None:
    result = subprocess.run(
        ["python3", "scripts/wizard_v4_2_runtime_audit.py", "--skip-preflight", "--accept-skipped-preflight"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    payload = json.loads(result.stdout)
    summary = payload["checks"]["contract_lint_summary"]
    ratchet = json.loads((ROOT / "system_v5/ops/state/contract_lint_ratchet.json").read_text())

    current_ratio = summary["violation_total"] / max(summary["sims_with_violations"], 1)
    allowed_ratio = ratchet["violations_per_sim_with_violations"]
    assert summary["violation_total"] <= ratchet["violation_total"]
    assert summary["sims_with_violations"] <= ratchet["sims_with_violations"]
    assert current_ratio <= allowed_ratio + 0.000001


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
    allowlisted = {
        line.strip()[3:-1]
        for line in text.splitlines()
        if line.strip().startswith("- `") and line.strip().endswith("`")
    }

    for row in report["rows"]:
        assert row["sim"] in allowlisted


def test_ops_debt_registers_are_linked_from_enforcement_rules() -> None:
    text = (ROOT / "system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md").read_text()

    assert "PROPOSAL_APPLY_CONTRACT.md" in text
    assert "NEVER_RUN_TRIAGE.md" in text
    assert "RUNNER_TAXONOMY_UNKNOWN_ALLOWLIST.md" in text

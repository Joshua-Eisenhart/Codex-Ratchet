import json
import subprocess
from copy import deepcopy
from datetime import datetime, timezone
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
    assert freshness["freshness_rule"]
    assert freshness["timestamp_source"] == "filesystem_mtime_utc"
    assert freshness["reports"]
    assert any(report["path"] == "system_v5/ops/proposal_apply_preview.json" for report in freshness["reports"])
    assert any(report["path"] == "system_v5/ops/c6_loadbearing_decision_table.json" for report in freshness["reports"])
    assert payload["checks"]["contract_lint_summary"]["violation_total"] >= 0
    assert payload["checks"]["contract_lint_summary"]["closeout_check"] == "python3 scripts/lint_sim_contract.py"
    assert "never_run_total" in payload["checks"]["never_run_summary"]
    assert payload["checks"]["never_run_summary"]["closeout_check"] == "python3 scripts/never_run_cohort_report.py"
    assert payload["checks"]["taxonomy_unknown_allowlist"]["closeout_check"] == "python3 scripts/runner_taxonomy_unknowns_report.py"
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


def test_contract_lint_ratchet_failure_path_is_exercised() -> None:
    ratchet = json.loads((ROOT / "system_v5/ops/state/contract_lint_ratchet.json").read_text())
    summary = {
        "violation_total": ratchet["violation_total"] + 1,
        "sims_with_violations": ratchet["sims_with_violations"],
    }
    current_ratio = summary["violation_total"] / max(summary["sims_with_violations"], 1)

    assert summary["violation_total"] > ratchet["violation_total"]
    assert current_ratio > ratchet["violations_per_sim_with_violations"]


def test_taxonomy_allowlist_review_date_failure_path_is_exercised() -> None:
    from scripts import wizard_v4_2_runtime_audit as audit

    stale_now = datetime(2026, 8, 12, tzinfo=timezone.utc)
    summary = audit.taxonomy_allowlist_summary(stale_now)

    assert summary["review_due"] is True
    assert summary["ok"] is False


def test_ops_report_freshness_failure_path_is_exercised() -> None:
    from scripts import wizard_v4_2_runtime_audit as audit

    report = audit.reports_freshness(datetime.now(timezone.utc))
    stale_report = deepcopy(report)
    stale_report["reports"][0]["stale_vs_newest_source"] = True
    stale_report["stale"] = any(item["stale_vs_newest_source"] for item in stale_report["reports"])
    stale_report["ok"] = not stale_report["stale"] and not stale_report["missing"] and not stale_report["source_missing"]

    assert stale_report["stale"] is True
    assert stale_report["ok"] is False


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


def test_c6_decision_table_is_review_only() -> None:
    subprocess.run(
        ["python3", "scripts/c6_loadbearing_decision_table.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    table = json.loads((ROOT / "system_v5/ops/c6_loadbearing_decision_table.json").read_text())

    assert table["schema"] == "c6_loadbearing_decision_table_v1"
    assert table["mode"] == "review_only_no_source_edits"
    assert table["source_report_row_counts"]["blocked_reason_breakdown"] > 0
    assert table["source_report_row_counts"]["c6_loadbearing_report"] >= 0
    assert table["blocked_c6_sim_count"] >= 0
    assert table["decision_row_count"] >= table["blocked_c6_sim_count"]
    if table["decision_row_count"] == 0:
        assert table["action_counts"] == {}
    else:
        assert table["action_counts"]
    assert table["action_counts"].get("owner_review_inconclusive", 0) >= 0
    for row in table["rows"]:
        assert row["owner_review_required"] is True
        assert row["source_edit_allowed"] is False
        assert row["candidate_action"]


def test_c6_decision_table_maps_known_buckets_explicitly() -> None:
    from scripts import c6_loadbearing_decision_table as decisions

    assert (
        decisions.candidate_action(
            {
                "bucket": "genuinely_load_bearing_so_promote_to_canonical_candidate",
                "result_path": "result.json",
            }
        )
        == "promote_to_canonical_candidate_after_owner_review"
    )
    assert (
        decisions.candidate_action({"bucket": "inconclusive_needs_owner", "result_path": None})
        == "owner_review_missing_result_before_edit"
    )
    assert (
        decisions.candidate_action({"bucket": "inconclusive_needs_owner", "result_path": "result.json"})
        == "owner_review_inconclusive"
    )
